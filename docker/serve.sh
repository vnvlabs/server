
#Command to SERVE THE DOCKER IMAGE
docker run --rm -it --network="host" -v /var/run/docker.sock:/var/run/docker.sock vnv_serve $1 
