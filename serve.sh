
#Command to build and run the docker image. 

./docker.sh vnv_env vnv_serve
docker run --rm -it --network="host" -v /var/run/docker.sock:/var/run/docker.sock vnv_serve $1
