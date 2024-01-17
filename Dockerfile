FROM python:3.11

COPY requirements.txt requirements.txt

RUN apt update\
    && apt install -y wkhtmltopdf\
    && pip install --no-cache-dir -U pip\
    && pip install --no-cache-dir -U -r requirements.txt\
    && rm -rf /root/.cache/pip\
    && rm -rf /vat/cache/apt\
    && rm requirements.txt

WORKDIR /app
COPY . .
CMD [ "python3", "main.py" ]
