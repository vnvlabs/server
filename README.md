# vnv-serve

Simple Flask Reverse Proxy that acts as the front end for the vnv docker image. The reverse proxy creates a container for each user when they login and then acts as a middle man between the user and their container. 



## To Run -- 

./run.sh base-docker-image

where base-docker-image is a docker image built on top of the vnv_base docker image.



## Off label
  
   Technically, this thing will lock with any docker image containing a launch.sh script 
   in the root directory. 
   
   The python script launches the docker container using the command ./launch.sh USERNAME
   and then forwards the user to http://localhost:5001/ in the browser. 


