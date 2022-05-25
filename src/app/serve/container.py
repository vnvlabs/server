import base64
import json
import threading
import uuid

import docker
from docker.errors import NotFound
from flask import g, current_app
from .common import benc, Container

'''
TODO We can switch this out for one that launches containers on AWS? 
Will need to think about security on those containers -- maybe only 
allow incoming html from this ip ? + turn on authentication? 
Right now, we turn of authentication for those containers because they 
are not accessible through the outside world.. 
'''

from .local import DockerImplementation as Implementation

def set_container_status(container):
    if isinstance(container,list):
        for cont in container:
            set_container_status(cont)
    elif isinstance(container,Container):
        container.status_ = Implementation.status(container.id)
    return container

def get_user_volume_name(username):
    Implementation.get_user_volume_name(username)

def list_available_resources(uname):
    return Implementation.resources(uname)

def list_user_containers(username):
    return set_container_status(Implementation.containers(username))


def add_new_container(username, containerName, image, resource, desc, id):
    return set_container_status(Implementation.new_container(username, containerName, image, resource, desc, id))

def remove_docker_container(username, container_id):
    return Implementation.remove_container(username, container_id)

def mark_stopped(username, container_id):
    return Implementation.mark_stopped(username, container_id)

def mark_started(username, container_id):
    return Implementation.mark_started(username, container_id)

def list_all_images(username):
    return Implementation.images(username, all=True)

def list_user_images(username):
    return Implementation.images(username, all=False)

def execute_command(image, command):
    return Implementation.execute(image, command)

def image_exists(image):
    return Implementation.image_exists(image)

def add_new_image(username, name, desc, id):
    return Implementation.new_image(username, name, desc, id)

def remove_docker_image(username, image_id):
    return Implementation.remove_image(username, image_id)

def docker_container_ready(container_id):
    return Implementation.ready_(container_id)

def create_docker_container(uname, name, image, resource, image_desc):
    try:
        container_id = "vnv-" + uuid.uuid4().hex
        container = add_new_container(uname, name, image, resource, image_desc, container_id)
        comm = "/vnv-gui/launch.sh "
        volumes = {Implementation.get_user_volume_name(container.user): {'bind': '/container', 'mode': 'rw'}}
        threading.Thread(target=Implementation.create_, args=[container, comm, volumes]).start()
    except:
        pass

def stop_docker_container(username, container_id):
    try:
        mark_stopped(username, container_id)
        threading.Thread(target=Implementation.stop_, args=[container_id]).start()
    except:
        pass

def start_docker_container(username, container_id):
    try:
        mark_started(username,container_id)
        threading.Thread(target=Implementation.start_, args=[container_id]).start()
    except Exception as e :
        print("SSSSSSSSSSSSSSS" + str(e) )


def delete_docker_container(username, container_id):
    try:
        threading.Thread(target=Implementation.delete_, args=[container_id]).start()
        remove_docker_container(username, container_id)
    except:
        pass


def create_docker_image(username, container_id, name, desc):
    try:
        new_image_id = "vnv-" + uuid.uuid4().hex
        image = add_new_image(username, name, desc, new_image_id)
        threading.Thread(target=Implementation.snapshot_, args=[container_id, image]).start()

    except:
        pass

def delete_docker_image(username, image_id):
    try:
        threading.Thread(target=Implementation.delete_image_, args=[image_id]).start()
        remove_docker_image(username, image_id)
    except:
        pass

def add_money(username, amount):
    return Implementation.add_money(username, amount)

def get_account_balance(username):
    return Implementation.balance(username)


try:
    INITIALIZED_CONTAINERS
except:
    INITIALIZED_CONTAINERS = True

    for container in Implementation.list_containers():
        Implementation.new_container_(container)
    for image in Implementation.list_images():
        Implementation.new_image_(image)

    def monitor_containers():
        for container in Implementation.list_containers():
            if Implementation.status(container.id) == "running":
                Implementation.remove_money(container.user, container.price())

    def monitor_containers_forever():
        ev = threading.Event()
        while True:
            monitor_containers()
            ev.wait(60)

    threading.Thread(target=monitor_containers_forever).start()
