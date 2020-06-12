FROM python:3.8.3-alpine AS builder

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /usr/src/app
COPY . .

RUN apk add --no-cache gcc python3-dev musl-dev
RUN python3 ./setup bdist_wheel -d build

FROM python:3.8.3-alpine
COPY --from=builder /usr/src/app/build/httpcheck-*-py3-none-any.whl /usr/local/src/
RUN apk add --no-cache py3-psycopg2

RUN python3 -m pip install /usr/local/src/httpcheck-1.0-py3-none-any.whl
