# Sistema de Agendamento de Serviços

Aplicação web para gerenciamento de agendamentos de serviços: cadastro de clientes, locais e tipos de atendimento, geração de grades de horários e controle de disponibilidade para novos agendamentos.

## Tecnologias

- **Backend**: Python 3.13 + Django 5 + Django REST Framework
- **Frontend**: React + TypeScript + Vite + Tailwind CSS
- **Banco de dados**: PostgreSQL (via Docker)
- **Testes**: pytest + pytest-django (59 testes automatizados no backend)

## Estrutura do projeto

```
.
├── docker-compose.yml     # Postgres + backend + frontend (stack completa)
├── backend/                # API Django REST Framework
│   ├── Dockerfile
│   ├── config/               # settings, urls
│   └── apps/
│       ├── core/                # comando de setup (criar_usuario_padrao)
│       ├── clientes/          # CRUD de clientes (com validação de CPF/CNPJ)
│       ├── locais/             # CRUD de locais
│       ├── tipos_atendimento/  # CRUD de tipos de atendimento
│       └── agendamentos/        # grade de horários, agendamentos, status, indicadores
└── frontend/               # SPA React
    ├── Dockerfile
    └── src/
        ├── api/               # chamadas HTTP + tipos
        ├── components/        # componentes reutilizáveis
        └── pages/             # telas da aplicação
```

## Como rodar o projeto

### Opção A — Tudo via Docker (recomendado, um único comando)

**Pré-requisito**: Docker.

Na raiz do projeto:

```bash
docker compose up --build
```

Isso sobe **os três serviços** (PostgreSQL, backend, frontend), já aplica as migrations e cria o usuário padrão de avaliação automaticamente. Não precisa instalar Python, Node, nem configurar nenhum `.env` — os containers já vêm com as variáveis necessárias.

- Frontend: `http://localhost:5173`
- API: `http://localhost:8000/api/`
- Login: usuário `admin`, senha `admin123`

Para parar: `Ctrl+C` ou, em outro terminal, `docker compose down` (adicione `-v` se quiser apagar também os dados do banco).

### Opção B — Backend e frontend manualmente

Útil para rodar os testes automatizados ou mexer no código com hot-reload fora de containers.

**Pré-requisitos**: Python 3.11+, Node.js 18+, Docker (só para o banco).

**1. Banco de dados**

```bash
docker compose up -d db
```

Sobe um PostgreSQL na porta **5434** do host (mapeada para não conflitar com instâncias locais de PostgreSQL que já usem as portas 5432/5433), com o banco `agendamento` e usuário/senha `agendamento`/`agendamento`.

> Se preferir usar um PostgreSQL já existente na sua máquina, ajuste `DATABASE_URL` no `.env` do backend em vez de subir o container.

**2. Backend**

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

**3. Rodando os testes do backend**

```bash
cd backend
python -m pytest apps/
```

**4. Frontend**

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
3. Em **Gerar Grade**, selecione o local, o intervalo de data/hora e a duração do atendimento — o sistema cria automaticamente a quantidade máxima de horários completos que cabem no intervalo. Marque "Gerar apenas em dias úteis" para pular sábados e domingos automaticamente.
4. Em **Novo Agendamento**, escolha local → data → horário disponível, o cliente e o tipo de atendimento.
5. Em **Agendamentos**, acompanhe a listagem com filtros, indicadores e altere o status de cada atendimento (Pendente → Realizado / Cancelado / Não compareceu).

## Decisões de projeto

O enunciado do teste deixa alguns comportamentos em aberto. As decisões tomadas, e o porquê, estão registradas aqui:

- **Cancelamento não libera o horário para reagendamento.** O enunciado não especifica esse comportamento; optou-se pela leitura literal do texto ("impedindo que seja utilizado novamente enquanto estiver indisponível") de forma permanente. Essa decisão também permite modelar o vínculo entre `Atendimento` e `HorarioAgendamento` como `OneToOneField`, garantindo no nível do banco que um horário nunca tenha mais de um atendimento.
- **Geração de grade com sobreposição é rejeitada por completo.** Se o intervalo informado colidir com horários já existentes no mesmo local, a API recusa a geração inteira (HTTP 400) em vez de criar apenas os horários não conflitantes.
- **Intervalo menor que a duração informada é tratado como erro.** Se o intervalo não comportar nenhum horário completo, a API retorna 400 em vez de "0 grades criadas com sucesso".
- **Atendimentos não são excluídos.** Não há endpoint de exclusão para atendimentos — permanecem armazenados independentemente do status, conforme exigido.
- **Cliente/Local/Tipo de Atendimento: soft delete na UI, hard delete continua disponível na API.** O enunciado aceita "exclusão **ou** desativação" para Cliente; optou-se por só expor a desativação (`ativo=false`) na interface — reversível, não perde histórico, e é a única ação de remoção que a listagem de agendamentos permanece consistente ao usar. O `DELETE` do DRF não foi desligado da API (`ModelViewSet` continua completo): quem quiser excluir de verdade um cadastro sem nenhum uso ainda pode, via API ou Admin; se houver atendimento vinculado, o `on_delete=PROTECT` recusa com um 400 legível (ver seção de exclusão de horários). Ou seja, os dois convivem por design — a UI só usa o caminho reversível.
- **Cancelado pode voltar a Pendente (se o horário ainda não passou); Realizado e Não Compareceu, nunca.** A diferença não é arbitrária: Realizado e Não Compareceu só são marcados **depois do fato** — registram algo que já aconteceu (ou não), então "desfazer" não tem correspondência com a realidade. Cancelado é diferente: normalmente é uma decisão tomada **com antecedência**, e essa decisão pode mudar — o cliente liga de volta dizendo que consegue ir, por exemplo. Por isso só Cancelado é reversível, e só enquanto o horário da grade ainda estiver no futuro (reabrir para um horário que já passou geraria um "pendente" para uma data que já era, o que não faz sentido).
- **Geração de grade em intervalos de vários dias respeita uma janela diária de expediente.** Se `início` e `fim` estiverem em dias diferentes (ex.: dia 17 às 08:00 até dia 21 às 18:00), o horário de cada um define o expediente diário (aqui, 08:00–18:00), repetido em todos os dias do intervalo — nunca é gerado horário fora dessa janela, mesmo que o intervalo bruto atravesse a madrugada. Se o horário de fim não for posterior ao de início dentro do dia, a API rejeita com 400.
- **Geração de grade tem opção de pular sábados e domingos** (`apenas_dias_uteis`, opcional). Não é um requisito do enunciado — é uma conveniência para quem não atende nesses dias, evitando ter que excluir manualmente pelo Admin depois.
- **A duração do Tipo de Atendimento é independente da duração da grade.** O enunciado apresenta os dois campos em seções separadas (cadastro do tipo vs. geração de grade) sem deixar claro se um deveria derivar do outro. Essa dúvida foi confirmada diretamente com o Janio (autor do teste): a duração do tipo de atendimento não deve ser considerada na geração/ocupação da grade — ela existe apenas como informação do cadastro, não é usada em nenhum cálculo. Um agendamento sempre ocupa **exatamente um horário da grade**, com a duração que a grade foi gerada — nunca a duração cadastrada no tipo. Exemplo prático: um "Tipo de Atendimento" cadastrado com 60 minutos de duração, usado numa grade gerada com slots de 30 minutos, ocupa um único slot de 30 minutos; o campo de 60 minutos do tipo não altera isso em nada, é só informativo. Implementar o contrário (o tipo "reservar" múltiplos slots ou redimensionar o horário) foi considerado e descartado por aumentar bastante a complexidade (ocupação de slots consecutivos, conflitos ao gerar grade com slots menores que algum tipo, etc.) sem que o enunciado pedisse isso.

Em geral, na dúvida entre uma solução simples e uma mais "completa" mas não pedida pelo enunciado, optou-se pela simples (ver também: cancelamento não libera horário, sobreposição de grade rejeitada por completo em vez de parcial) — e, como no caso acima, pontos genuinamente ambíguos foram esclarecidos diretamente com o Janio em vez de resolvidos por suposição. Fica a mesma recomendação para qualquer novo item da lista de melhorias futuras: alinhar o comportamento esperado com o cliente antes de implementar, em vez de assumir.

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

## Excluindo horários gerados por engano (feriado, fim de semana etc.)

A API não expõe exclusão de horários da grade (só geração e consulta), mas isso é possível pelo **Django Admin** (`http://localhost:8000/admin/`, login com o superusuário). Em "Horarios de agendamento": use o filtro por data (`date_hierarchy`) para navegar até o dia desejado, selecione os horários e exclua em lote. Horários que já possuem um atendimento vinculado **não podem ser excluídos** (o Admin recusa automaticamente, protegendo o histórico).

## Autenticação

A API é protegida por autenticação JWT (`djangorestframework-simplejwt`), implementada como funcionalidade adicional (opcional segundo o enunciado).

```
POST   /api/auth/token/           # login: {"username": "...", "password": "..."} -> {access, refresh}
POST   /api/auth/token/refresh/   # renova o access token: {"refresh": "..."} -> {access}
```

O frontend anexa o `access token` automaticamente em toda requisição e, se ele expirar (401), tenta renová-lo uma vez com o `refresh token` antes de redirecionar para a tela de login.

**Login para avaliação**: usuário `admin`, senha `admin123` (criado pelo comando `python manage.py criar_usuario_padrao`, ver seção de instalação). Essa credencial é conhecida de propósito — o comando só executa com `DEBUG=True` e nunca deveria ser usado em um ambiente real de produção.

### Criando outros usuários

Não existe cadastro público (autocadastro pela interface web) — usuários só podem ser criados por quem já tem acesso ao terminal ou ao Admin:

- **Superusuário** (acessa a API e o Django Admin): `python manage.py createsuperuser` (pede usuário/senha interativamente).
- **Usuário comum** (só acessa a API/frontend, sem entrar no Admin):
  ```bash
  python manage.py shell -c "from django.contrib.auth import get_user_model; get_user_model().objects.create_user(username='fulano', password='senha123')"
  ```
- **Pelo Django Admin** (se já estiver logado como superusuário): `Autenticação e Autorização` → `Users` → `ADD USER +`.

Rodando via Docker, prefixe qualquer um desses comandos com `docker compose exec backend` (ex.: `docker compose exec backend python manage.py createsuperuser`), e o container precisa estar em execução (`docker compose up -d`).

## Testes automatizados

O backend possui 82 testes automatizados (pytest) cobrindo: CRUDs de cadastro (incluindo edição), geração de grade (quantidade de slots, validações, sobreposição), consulta de disponibilidade, criação de agendamento (incluindo proteção contra concorrência), transições de status (incluindo reabertura de cancelamento) e filtros/ordenação/indicadores da listagem.

## Melhorias futuras (fora do escopo desta entrega)

Pontos identificados durante o desenvolvimento que melhorariam a experiência, mas que optamos por não incluir nesta entrega — exigem mais esforço de implementação do que os ajustes já feitos, e não são requisitos do enunciado.

### Visualização em grade (semanal/mensal)

Hoje a disponibilidade é consultada em formato de lista (data → horários daquele dia, um de cada vez). Uma visão em **grade semanal** — linhas por horário do dia, colunas por dia da semana, células coloridas por status — daria uma leitura muito mais rápida da ocupação de um local.

```
Semana de 18/08 a 24/08 — Local: Unidade Central

         Seg 18    Ter 19    Qua 20    Qui 21    Sex 22    Sáb 23    Dom 24
08:00   [ LIVRE ] [OCUPADO] [ LIVRE ] [ LIVRE ] [OCUPADO]     —         —
08:30   [OCUPADO] [ LIVRE ] [ LIVRE ] [CANCEL.] [ LIVRE ]     —         —
09:00   [ LIVRE ] [ LIVRE ] [OCUPADO] [ LIVRE ] [ LIVRE ]     —         —
09:30   [ LIVRE ] [OCUPADO] [ LIVRE ] [ LIVRE ] [ LIVRE ]     —         —
  ...

Legenda:  LIVRE = disponível   OCUPADO = agendado (pendente/realizado)
          CANCEL. = cancelado (horário não reaproveitado)   — = fora do expediente / fim de semana
```

- **Semana**: viável com o nível de detalhe acima (hora a hora), reaproveitando os endpoints de disponibilidade já existentes (uma consulta por dia, ou um novo endpoint de intervalo).
- **Mês**: nesse nível de detalhe fica visualmente poluído; funcionaria melhor como um calendário resumido, com um contador de horários livres/ocupados por dia (parecido com o que `datas-disponiveis` já retorna), sem tentar mostrar cada horário individual.
- **Posicionamento sugerido**: como complemento visual dentro da própria tela de **Gerar Grade** (mostrando o que já existe para o local antes/depois de gerar), não anexado a outras telas — o grid precisa de largura própria para não ficar espremido ao lado do menu.

### Paginação nas listagens

As listagens (`/api/clientes/`, `/api/locais/`, `/api/atendimentos/` etc.) hoje retornam todos os registros de uma vez. O Django REST Framework já oferece paginação pronta (`PageNumberPagination`), mas adotá-la muda o formato de resposta de todos os endpoints de listagem (de array direto para um envelope com `count`/`next`/`previous`/`results`), exigindo ajustes tanto nos testes do backend quanto na camada de API do frontend. Não é necessário no volume de dados de um teste técnico, mas seria o próximo passo natural em caso de crescimento real da base.

### Remover horários livres de um dia (feriados)

A geração de grade hoje só sabe pular fins de semana (`apenas_dias_uteis`); um feriado que cai em dia útil (ex.: um feriado nacional gerado meses à frente numa grade multi-dia) continua gerando horários normalmente, porque o sistema não tem uma lista de feriados. Duas formas de tratar isso, sem se sobrepor:

- **Prevenção, na geração:** cadastrar uma lista de feriados (fixos ou parametrizáveis) e fazer `gerar_grade` pular esses dias automaticamente, do mesmo jeito que já pula fins de semana com `apenas_dias_uteis`. Resolve o problema na origem, mas exige manter essa lista atualizada (e feriados municipais variam por local).
- **Correção, depois de já gerado:** uma ação "excluir horários livres de um dia" (por local + data), que remove em lote só os horários `disponivel=True` sem atendimento vinculado. Horários que já têm atendimento vinculado (qualquer status) **não podem ser excluídos** — o `on_delete=PROTECT` já impede isso no banco — e a ação devolveria a lista de quem está com agendamento naquele dia, para o atendente cancelar manualmente e avisar o cliente. Cancelamento em massa automático não é uma boa ideia aqui: avisar o cliente é uma decisão humana, não deveria ser uma ação de sistema disparada sem contato prévio.

A segunda opção é mais valiosa a curto prazo (cobre feriados não previstos, feriados municipais, e qualquer outro motivo de bloqueio pontual de agenda), e já existe um caminho manual equivalente hoje via Django Admin (ver seção "Excluindo horários gerados por engano" acima) — a diferença seria expor isso como uma ação de API + UI dedicada, com a lista de agendamentos vinculados retornada na resposta, em vez de depender do Admin e conferir manualmente quais horários recusaram a exclusão.
