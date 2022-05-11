import threading

import docker
from docker.errors import NotFound
from flask import g

'''
TODO We can switch this out for one that launches containers on AWS? 
Will need to think about security on those containers -- maybe only 
allow incoming html from this ip ? + turn on authentication? 
Right now, we turn of authentication for those containers because they 
are not accessible through the outside world.. 
'''
docker_client = docker.from_env()



def docker_container_ready():

    try:
        c = docker_client.containers.get("vnv-" + g.user)
        return c.ports['5001/tcp'][0]["HostPort"], c.ports['3000/tcp'][0]["HostPort"], c.ports["9000/tcp"][0]["HostPort"]

    except:
        pass

    print("Looking for docker container for ", g.user)

    return None,None,None


def launch_docker_container(uname, password, DOCKER_IMAGE_NAME="vnv_serve:latest"):
    '''
        TODO: Add a wsgi lock across all wsgi workers. We can use named locks based on 
        the uname to get better performance across users (no need to lock for all users while
        starting the docker container for one user. 
    '''

    try:
        container = docker_client.containers.get("vnv-" + uname)
        container.start()


    except NotFound as e:
        #Container not found for user -- so create one.
        try:
            comm = "./launch.sh " + uname

            try:
                volume = docker_client.volumes.get("vnv-" + uname)
            except Exception as e:
                volume = docker_client.volumes.create("vnv-"+uname)

            volumes = {'vnv-'+uname : {'bind': '/container', 'mode': 'rw'} }
            container = docker_client.containers.run("vnv_serve:latest", volumes=volumes, command=comm, ports={5001:None, 3000:None, 9000:None}, name="vnv-" + uname, detach=True)
    
        except Exception as e:
            print(e)
            return None

def stop_(uname):
    c = docker_client.containers.get("vnv-" + uname)
    c.stop()

def stop_docker_container():
    try:
        c = g.user
        threading.Thread(target=stop_, args=[c]).start()
    except:
        pass
    print("Killing docker container for " ,g.user)
