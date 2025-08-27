FROM python:3.12

WORKDIR /app
COPY . .

RUN apt update\
    && apt install -y wkhtmltopdf\
    && apt install -y pipx \
    && pipx install poetry \
    && poetry install \
    && rm -rf /root/.cache \
    && rm -rf /var/cache/apt \


CMD [ "poetry", "run", "python3", "main.py" ]
