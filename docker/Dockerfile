
ARG FROM_IMAGE=vnv_env
FROM ${FROM_IMAGE}:latest
COPY . /serve

WORKDIR /serve
RUN virtualenv --python=python3 virt && virt/bin/pip install -r requirements.txt
ENTRYPOINT ["docker/run.sh"]
CMD ["/serve/config/config.json"]
