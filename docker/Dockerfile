ARG VNV_BASE_IMAGE=vnv_base
from ${VNV_BASE_IMAGE} 

#Install mongodb -- Should be able to move this to the vnv_env image. 
RUN wget -qO - https://www.mongodb.org/static/pgp/server-5.0.asc | apt-key add -
RUN echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu bionic/mongodb-org/5.0 multiverse" | tee /etc/apt/sources.list.d/mongodb-org-5.0.list
RUN apt-get update && apt-get install -y mongodb-server


COPY config /serve-config
COPY ./launch.sh ./launch.sh


#Tell VNV About our configuration file by appending it to the environment.
ENV VNV_CONFIG=${VNV_CONFIG}:/serve-config/.vnv-config.json

