# Sistema de Agendamento de Serviços

Aplicação web para gerenciamento de agendamentos de serviços: cadastro de clientes, locais e tipos de atendimento, geração de grades de horários e controle de disponibilidade para novos agendamentos.

## Tecnologias

- **Backend**: Python 3.13 + Django 5 + Django REST Framework
- **Frontend**: React + TypeScript + Vite + Tailwind CSS
- **Banco de dados**: PostgreSQL (via Docker)
- **Testes**: pytest + pytest-django (51 testes automatizados no backend)

## Estrutura do projeto

```
.
├── docker-compose.yml     # PostgreSQL
├── backend/                # API Django REST Framework
│   ├── config/               # settings, urls
│   └── apps/
│       ├── core/                # comando de setup (criar_usuario_padrao)
│       ├── clientes/          # CRUD de clientes (com validação de CPF/CNPJ)
│       ├── locais/             # CRUD de locais
│       ├── tipos_atendimento/  # CRUD de tipos de atendimento
│       └── agendamentos/        # grade de horários, agendamentos, status, indicadores
└── frontend/               # SPA React
    └── src/
        ├── api/               # chamadas HTTP + tipos
        ├── components/        # componentes reutilizáveis
        └── pages/             # telas da aplicação
```

## Pré-requisitos

- Python 3.11+
- Node.js 18+
- Docker (para o PostgreSQL) — ou uma instância PostgreSQL local própria

## Como rodar o projeto

### 1. Banco de dados (PostgreSQL via Docker)

Na raiz do projeto:

```bash
docker compose up -d db
```

Isso sobe um PostgreSQL na porta **5434** do host (mapeada para não conflitar com instâncias locais de PostgreSQL que já usem as portas 5432/5433), com o banco `agendamento` e usuário/senha `agendamento`/`agendamento`.

> Se preferir usar um PostgreSQL já existente na sua máquina, basta ajustar `DATABASE_URL` no `.env` do backend (passo abaixo) em vez de subir o container.

### 2. Backend

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate

pip install -r requirements.txt

# Copie o arquivo de variaveis de ambiente e ajuste se necessario
cp .env.example .env

python manage.py migrate

# Cria o usuario padrao de avaliacao (usuario: admin / senha: admin123)
# Nao faz nada se o usuario ja existir; so funciona com DEBUG=True.
python manage.py criar_usuario_padrao

python manage.py runserver
```

A API sobe em `http://localhost:8000`. As rotas ficam sob `http://localhost:8000/api/`.

> Se preferir criar seu próprio usuário em vez de usar o padrão, use `python manage.py createsuperuser`.

Variáveis de ambiente relevantes (`backend/.env`):

| Variável | Descrição |
|---|---|
| `SECRET_KEY` | Chave secreta do Django |
| `DEBUG` | `True` em desenvolvimento |
| `DATABASE_URL` | String de conexão do PostgreSQL |
| `CORS_ALLOWED_ORIGINS` | Origens liberadas para chamar a API (o frontend em `localhost:5173`) |

### 3. Rodando os testes do backend

```bash
cd backend
python -m pytest apps/
```

### 4. Frontend

Em outro terminal:

```bash
cd frontend
npm install

# Copie o arquivo de variaveis de ambiente e ajuste se necessario
cp .env.example .env

npm run dev
```

A aplicação sobe em `http://localhost:5173`.

Variável de ambiente relevante (`frontend/.env`):

| Variável | Descrição |
|---|---|
| `VITE_API_URL` | URL base da API (padrão: `http://localhost:8000/api`) |

## Fluxo de uso

1. Acesse `http://localhost:5173` e faça login com o usuário padrão: **`admin`** / **`admin123`** (criado no passo anterior via `criar_usuario_padrao`).
2. Cadastre ao menos um **Cliente**, um **Local** e um **Tipo de Atendimento**.
3. Em **Gerar Grade**, selecione o local, o intervalo de data/hora e a duração do atendimento — o sistema cria automaticamente a quantidade máxima de horários completos que cabem no intervalo.
4. Em **Novo Agendamento**, escolha local → data → horário disponível, o cliente e o tipo de atendimento.
5. Em **Agendamentos**, acompanhe a listagem com filtros, indicadores e altere o status de cada atendimento (Pendente → Realizado / Cancelado / Não compareceu).

## Decisões de projeto

O enunciado do teste deixa alguns comportamentos em aberto. As decisões tomadas, e o porquê, estão registradas aqui:

- **Cancelamento não libera o horário para reagendamento.** O enunciado não especifica esse comportamento; optou-se pela leitura literal do texto ("impedindo que seja utilizado novamente enquanto estiver indisponível") de forma permanente. Essa decisão também permite modelar o vínculo entre `Atendimento` e `HorarioAgendamento` como `OneToOneField`, garantindo no nível do banco que um horário nunca tenha mais de um atendimento.
- **Geração de grade com sobreposição é rejeitada por completo.** Se o intervalo informado colidir com horários já existentes no mesmo local, a API recusa a geração inteira (HTTP 400) em vez de criar apenas os horários não conflitantes.
- **Intervalo menor que a duração informada é tratado como erro.** Se o intervalo não comportar nenhum horário completo, a API retorna 400 em vez de "0 grades criadas com sucesso".
- **Atendimentos não são excluídos.** Não há endpoint de exclusão para atendimentos — permanecem armazenados independentemente do status, conforme exigido.

## Principais endpoints da API

```
POST   /api/clientes/                          GET/PUT/PATCH/DELETE /api/clientes/{id}/
POST   /api/locais/                             GET/PUT/PATCH/DELETE /api/locais/{id}/
POST   /api/tipos-atendimento/                  GET/PUT/PATCH/DELETE /api/tipos-atendimento/{id}/

POST   /api/horarios/gerar-grade/
GET    /api/horarios/datas-disponiveis/?local=
GET    /api/horarios/horarios-disponiveis/?local=&data=

GET    /api/atendimentos/?status=&local=&tipo=&cliente_nome=
POST   /api/atendimentos/
PATCH  /api/atendimentos/{id}/status/
GET    /api/atendimentos/indicadores/?status=&local=&tipo=&cliente_nome=
```

## Autenticação

A API é protegida por autenticação JWT (`djangorestframework-simplejwt`), implementada como funcionalidade adicional (opcional segundo o enunciado).

```
POST   /api/auth/token/           # login: {"username": "...", "password": "..."} -> {access, refresh}
POST   /api/auth/token/refresh/   # renova o access token: {"refresh": "..."} -> {access}
```

O frontend anexa o `access token` automaticamente em toda requisição e, se ele expirar (401), tenta renová-lo uma vez com o `refresh token` antes de redirecionar para a tela de login.

**Login para avaliação**: usuário `admin`, senha `admin123` (criado pelo comando `python manage.py criar_usuario_padrao`, ver seção de instalação). Essa credencial é conhecida de propósito — o comando só executa com `DEBUG=True` e nunca deveria ser usado em um ambiente real de produção. Para criar um usuário próprio em vez do padrão, use `python manage.py createsuperuser`.

## Testes automatizados

O backend possui 51 testes automatizados (pytest) cobrindo: CRUDs de cadastro, geração de grade (quantidade de slots, validações, sobreposição), consulta de disponibilidade, criação de agendamento (incluindo proteção contra concorrência), transições de status e filtros/indicadores da listagem.
