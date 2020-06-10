FROM python:3.8.3-alpine

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /usr/src/app
COPY . .

RUN apk add --no-cache postgresql-dev gcc python3-dev musl-dev && python3 -m pip install -e .[test]
