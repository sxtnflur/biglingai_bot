FROM python:3.12

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app
COPY . /app

RUN pip install -U git+https://github.com/PrithivirajDamodaran/Gramformer.git
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

RUN chmod -R 777 ./
