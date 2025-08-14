FROM python:3.13-alpine

RUN apk add --no-cache curl

WORKDIR /app

COPY server.py /app/server.py

EXPOSE 8000

CMD [ "python", "/app/server.py" ]
