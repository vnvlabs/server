

#Build the serve docker image.  
docker build -f docker/Dockerfile -t $2 --build-arg FROM_IMAGE=$1 .







