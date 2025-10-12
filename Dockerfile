FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip && \
    pip install --no-cache-dir --no-deps -r requirements.txt && \
    pip install --no-cache-dir spacy
RUN spacy download en_core_web_sm

COPY . .

RUN chmod -R 777 ./
