import json

import docker

from src.app.serve.resource import benc, Container, bdec, Image


class DockerImplementation:
    docker_client = docker.from_env()

    @classmethod
    def execute(cls, image, command):
        return cls.docker_client.containers.run(image, command, remove=True).decode('ascii')

    @classmethod
    def image_exists(cls, img):
        try:
            cls.docker_client.images.get(img)
            return True
        except:
            return False

    @classmethod
    def get_container(cls,container_id):
        c = cls.docker_client.containers.get(container_id)
        if c is not None:
            co = Container.from_json(json.loads(c.labels["vnv-container-info"]))
            co.status_ = c.status
            return co,c
        return None

    @classmethod
    def status(cls, container_id):
        try:
            return cls.docker_client.containers.get(container_id).status
        except:
            return "invalid"

    @classmethod
    def create_volume(cls, username):
        volname = "vnv-volume-"+username
        try:
            cls.docker_client.volumes.get(volname)
        except:
            cls.docker_client.volumes.create(volname)
        return volname

    @classmethod
    def create_(cls, container, comm):

        try:
            labels = {"vnv-container-info": container.to_json()}
            volumes = { cls.create_volume(container.user): {'bind': '/data', 'mode': 'rw'}}

            cls.docker_client.containers.run(container.image, volumes=volumes, command=comm, labels=labels,
                                             ports={5001: None, 3000: None, 9000: None}, name=container.id, detach=True)

        except Exception as e:
            return None

    @classmethod
    def stop_(cls, container_id, username):
        cont,c  = cls.get_container(container_id)
        if cont is not None and cont.user == username:
            c.stop(timeout=0)

    @classmethod
    def start_(cls, container_id, username):
        cont, c = cls.get_container(container_id)
        if cont is not None and cont.user == username:
            c.start()

    @classmethod
    def delete_(cls, container_id, username):
        cont, c = cls.get_container(container_id)
        if cont is not None and cont.user == username:
            c.stop(timeout=0)
            c.remove(force=True, v=False)

    @classmethod
    def delete_image_(cls, image_id,username):
        img = cls.get_image(image_id)
        if img is not None and img.user == username:
            cls.docker_client.images.remove(image_id)

    @classmethod
    def snapshot_(cls, container_id, image, username):
        cont, c = cls.get_container(container_id)
        if cont is not None and cont.user == username:
            newlabel = 'LABEL vnv-image-info="' + benc(image.to_json()) + '"\nLABEL vnv-container-info=""'
            c.commit(image.id, changes=newlabel)

    @classmethod
    def ready_(cls, container_id, username):

        cont, c = cls.get_container(container_id)
        if cont is not None and cont.user == username:
            try:
                return c.ports['5001/tcp'][0]["HostPort"], c.ports['3000/tcp'][0]["HostPort"], c.ports["9000/tcp"][0]["HostPort"]
            except:
                pass

        return None, None, None

    @classmethod
    def list_containers(cls):
        docker_containers = cls.docker_client.containers.list(all=True, filters={"label": "vnv-container-info"})
        containers = []
        for container in docker_containers:
            inf = json.loads(container.labels["vnv-container-info"])
            containers.append(Container.from_json(inf))
        return containers

    @classmethod
    def list_user_containers(cls, username):
       return [ c for c in cls.list_containers() if c.user == username ]

    @classmethod
    def list_user_images(cls, username):
       return [ c for c in cls.list_images() if c.user == username ]

    @classmethod
    def get_image(cls, image_id):
        image = cls.docker_client.images.get(image_id)
        b64 = image.labels["vnv-image-info"]
        inf = json.loads(bdec(b64))
        return Image.from_json(inf)

    @classmethod
    def list_images(cls):
        docker_images = cls.docker_client.images.list(all=True, filters={"label": "vnv-image-info"})
        images = []
        for image in docker_images:
            b64 = image.labels["vnv-image-info"]
            inf = json.loads(bdec(b64))
            images.append(Image.from_json(inf))
        return images

