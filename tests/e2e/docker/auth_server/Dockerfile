FROM python:3.14-alpine

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apk add --no-cache curl

WORKDIR /app

COPY server.py /app/server.py

EXPOSE 8000

CMD [ "python", "/app/server.py" ]
