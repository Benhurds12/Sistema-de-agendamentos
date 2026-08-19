FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# migrate + usuario padrao rodam a cada start; ambos sao idempotentes (nao
# fazem nada se ja tiverem sido aplicados/criados antes).
CMD ["sh", "-c", "python manage.py migrate && python manage.py criar_usuario_padrao && python manage.py runserver 0.0.0.0:8000"]
