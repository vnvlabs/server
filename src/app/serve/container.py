import threading
import uuid
from .common import Container

'''
TODO We can switch this out for one that launches containers on AWS? 
Will need to think about security on those containers -- maybe only 
allow incoming html from this ip ? + turn on authentication? 
Right now, we turn of authentication for those containers because they 
are not accessible through the outside world.. 
'''

from .local import DockerImplementation as ContainerImplementation
from .common import CommonImpl as Implementation


def set_container_status(container):
    if isinstance(container, list):
        for cont in container:
            set_container_status(cont)
    elif isinstance(container, Container):
        container.status_ = ContainerImplementation.status(container.id)
    return container


def list_available_resources(uname):
    return Implementation.resources(uname)


def list_user_containers(username):
    return set_container_status(Implementation.containers(username))


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


def add_money(username, amount):
    return Implementation.add_money(username, amount)


def get_account_balance(username):
    return Implementation.balance(username)


def add_new_image(username, name, desc, id):
    return Implementation.new_image(username, name, desc, id)


def remove_docker_image(username, image_id):
    return Implementation.remove_image(username, image_id)


def create_docker_container(uname, name, image, resource, image_desc):
    try:
        container_id = "vnv-" + uuid.uuid4().hex
        container = Implementation.new_container(uname, name, image, resource, image_desc, container_id)
        if container is not None:
            container = set_container_status(container)
            comm = "/vnv-gui/launch.sh "
            threading.Thread(target=ContainerImplementation.create_, args=[container, comm]).start()
    except:
        pass

def stop_docker_container(username, container_id):
    try:
        if mark_stopped(username, container_id):
            threading.Thread(target=ContainerImplementation.stop_, args=[container_id]).start()
    except:
        pass


def start_docker_container(username, container_id):
    try:
        mark_started(username, container_id)
        threading.Thread(target=ContainerImplementation.start_, args=[container_id]).start()
    except Exception as e:
        pass


def delete_docker_container(username, container_id):
    try:
        if remove_docker_container(username, container_id):
            threading.Thread(target=ContainerImplementation.delete_, args=[container_id]).start()
    except:
        pass


def create_docker_image(username, container_id, name, desc):
    try:
        new_image_id = "vnv-" + uuid.uuid4().hex
        image = add_new_image(username, name, desc, new_image_id)
        if Implementation.owns_container(username, container_id):
            threading.Thread(target=ContainerImplementation.snapshot_, args=[container_id, image]).start()
    except:
        pass


def delete_docker_image(username, image_id):
    try:
        if remove_docker_image(username, image_id):
            threading.Thread(target=ContainerImplementation.delete_image_, args=[image_id]).start()
    except:
        pass

def docker_container_ready(username, container_id):
    if Implementation.owns_container(username,container_id):
        return ContainerImplementation.ready_(container_id)


#### DONT LET A USER USER THIS FUNCTION
def __execute_command__(image, command):
    return ContainerImplementation.execute(image, command)

def image_exists(image):
    return ContainerImplementation.image_exists(image)


try:
    INITIALIZED_CONTAINERS
except:
    INITIALIZED_CONTAINERS = True

    for container in ContainerImplementation.list_containers():
        Implementation.new_container_(container)
    for image in ContainerImplementation.list_images():
        Implementation.new_image_(image)


    def monitor_containers():
        for container in ContainerImplementation.list_containers():
            if ContainerImplementation.status(container.id) == "running":
                Implementation.remove_money(container.user, container.price())


    def monitor_containers_forever():
        ev = threading.Event()
        while True:
            monitor_containers()
            ev.wait(60)


    threading.Thread(target=monitor_containers_forever).start()
