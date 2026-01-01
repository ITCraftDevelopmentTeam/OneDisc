FROM python:3.12-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        wkhtmltopdf \
        curl \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /var/cache/apt

# 安装 Poetry
ENV POETRY_HOME="/opt/poetry"
ENV PATH="$POETRY_HOME/bin:$PATH"
RUN curl -sSL https://install.python-poetry.org | python3 - \
    && poetry config virtualenvs.create false

# 复制依赖文件
COPY pyproject.toml poetry.lock* ./

# 安装 Python 依赖
RUN poetry install --only main --no-interaction --no-ansi

# 复制应用代码
COPY . .

# 运行应用
CMD ["python3", "main.py"]
