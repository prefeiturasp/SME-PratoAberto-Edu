FROM python:3.6-alpine3.8

COPY . /code/
WORKDIR /code

RUN set -ex && \
    apk add --no-cache --virtual=.goss-dependencies curl ca-certificates && \
    apk update && apk add --no-cache tzdata libpq && \
    apk update && apk add --no-cache \
      --virtual=.build-dependencies \
      gcc \
      musl-dev \
      python3-dev && \
    python -m pip --no-cache install -U pip && \
    python -m pip --no-cache install -r requirements.txt && \
    cp /usr/share/zoneinfo/America/Sao_Paulo /etc/localtime &&\
    echo "America/Sao_Paulo" > /etc/timezone &&\
    apk del --purge .build-dependencies .goss-dependencies

CMD chown root:root /etc/crontabs/root && /usr/sbin/crond -f