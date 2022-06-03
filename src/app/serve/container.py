import threading
import uuid
from .resource import Resource, Image, Container
from .local import DockerImplementation as ContainerImplementation


ALL_RESOURCES = {
    "basic" : Resource("basic","Basic", "A Single CPU on the server", 2)
}



def set_container_status(container):
    if isinstance(container, list):
        for cont in container:
            set_container_status(cont)
    elif isinstance(container, Container):
        container.status_ = ContainerImplementation.status(container.id)
    return container


def get_volume_info(user):
    return ContainerImplementation.get_volume_info(user.uid)

def list_user_containers(uid):
    return set_container_status(ContainerImplementation.list_user_containers(uid))

def list_user_images(uid) -> list :
    return ContainerImplementation.list_user_images(uid)

def user_owns_image(image, uid):
    for im in list_user_images(uid):
        if im.id == image:
            return True
    return False

def pull_image(repo,tag=None, sync=False):
    if sync:
        ContainerImplementation.pull(repo,tag)
    else:
        threading.Thread(target=ContainerImplementation.pull, args=[repo, tag]).start()


def create_docker_container(uname, name, image, resource, image_desc):
    try:
        container_id = "vnv-" + uuid.uuid4().hex
        container = Container(container_id, uname, name,image,resource,image_desc)
        container = set_container_status(container)
        comm = "/vnv-gui/launch.sh "
        threading.Thread(target=ContainerImplementation.create_, args=[container, comm]).start()
    except Exception as e :
        pass

def stop_docker_container(uid, container_id):
    try:
        threading.Thread(target=ContainerImplementation.stop_, args=[container_id, uid]).start()
    except:
        pass


def start_docker_container(uid, container_id):
    try:
        threading.Thread(target=ContainerImplementation.start_, args=[container_id, uid]).start()
    except Exception as e:
        pass


def delete_docker_container(uid, container_id):
    try:
        threading.Thread(target=ContainerImplementation.delete_, args=[container_id, uid]).start()
    except:
        pass

def create_docker_image(uid, container_id, name, desc):
    try:
        new_image_id = "vnv-" + uuid.uuid4().hex
        image = Image(new_image_id,uid,name,desc,True)
        threading.Thread(target=ContainerImplementation.snapshot_, args=[container_id, image, uid]).start()
    except:
        pass

def delete_docker_image(uid, image_id):
    try:
       threading.Thread(target=ContainerImplementation.delete_image_, args=[image_id, uid]).start()
    except:
        pass

def docker_container_ready(uid, container_id):
    return ContainerImplementation.ready_(container_id, uid)


### DONT LET A USER USER THIS FUNCTION
def __execute_command__(image, command):
    return ContainerImplementation.execute(image, command)

def image_exists(image):
    return ContainerImplementation.image_exists(image)

def list_all_containers():
    return set_container_status(ContainerImplementation.list_containers())
