ARG VNV_BASE_IMAGE=vnv_base
from ${VNV_BASE_IMAGE} as server

ARG SERVER_CONFIG=config


COPY ${SERVER_CONFIG} /serve-config
ENV VNV_CONFIG=${VNV_CONFIG}:/serve-config/.vnv-config.json
COPY ./launch.sh ./launch.sh

