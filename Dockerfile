FROM alpine:3
LABEL org.opencontainers.image.source=github.com/savagemindz/tplink-powerstats
RUN addgroup -S powerstats && adduser -S powerstats -G powerstats

# hadolint ignore=DL3018
RUN apk add --no-cache python3 py3-pip

WORKDIR /tmp
COPY . .

# hadolint ignore=SC1091
RUN python3 -m venv /venv/py3 \
    && . /venv/py3/bin/activate \
    && pip install --no-cache-dir ./

EXPOSE 9101

USER powerstats
ENTRYPOINT ["/venv/py3/bin/python", "-m", "tplink_powerstats"]