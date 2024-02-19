FROM python:3.12-slim

WORKDIR /usr/src/app

COPY requirements.txt ./

RUN pip install -r requirements.txt

ENV HOSTS node1.example.com node1.example.com node1.example.com

COPY . .

ENTRYPOINT ["python", "./main.py"]