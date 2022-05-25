

#Build the serve docker image.  
docker build -f asgard/docker/Dockerfile -t $2 --build-arg FROM_IMAGE=$1 . 





