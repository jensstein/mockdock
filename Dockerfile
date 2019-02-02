FROM alpine

RUN apk add --update python3 gcc python3-dev musl-dev libffi-dev openssl-dev

RUN mkdir /home/mockdock
WORKDIR /home/mockdock

COPY src src
COPY setup.py setup.py
COPY Pipfile Pipfile
COPY Pipfile.lock Pipfile.lock
COPY start.sh start.sh

RUN python3 -m venv ENV && \
	source ENV/bin/activate && \
	pip install -U pip && \
	pip install -e .

LABEL CONFIG_PATH path to config file [optional]
LABEL CONFIG_DATA path to config data [optional]
LABEL TLS_CERTIFICATE path to tls certificate [optional]
LABEL TLS_CERTIFICATE_KEY path to tls certificate key [optional]
LABEL EXTRA_PORTS list of extra ports that need to be opened, ex. [8080, 8088] [optional]

CMD ["./start.sh"]
