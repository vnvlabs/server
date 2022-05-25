import json

import docker

from .common import CommonImpl, Container, bdec, Image, benc


class DockerImplementation(CommonImpl):
    docker_client = docker.from_env()

    @classmethod
    def execute(cls, image, command):
        return cls.docker_client.containers.run(image, command, remove=True).decode('ascii')

    @classmethod
    def image_exists(cls, img):
        return cls.docker_client.images.get(img) is not None

    @classmethod
    def status(cls, container_id):
        try:
            return cls.docker_client.containers.get(container_id).status
        except:
            return "invalid"

    @classmethod
    def create_(cls, container, comm, volumes):

        try:
            labels = {"vnv-container-info": container.to_json()}
            cls.docker_client.containers.run(container.image, volumes=volumes, command=comm, labels=labels,
                                             ports={5001: None, 3000: None, 9000: None}, name=container.id, detach=True)

        except Exception as e:
            return None

    @classmethod
    def stop_(cls, container_id):
        c = cls.docker_client.containers.get(container_id)
        c.stop()

    @classmethod
    def start_(cls, container_id):
        c = cls.docker_client.containers.get(container_id)
        c.start()

    @classmethod
    def delete_(cls, container_id):
        c = cls.docker_client.containers.get(container_id)
        c.stop()
        c.remove(force=True, v=False)

    @classmethod
    def delete_image_(cls, image_id):
        c = cls.docker_client.images.remove(image_id)

    @classmethod
    def snapshot_(cls, container_id, image):
        newlabel = 'LABEL vnv-image-info="' + benc(image.to_json()) + '"\nLABEL vnv-container-info=""'
        c = cls.docker_client.containers.get(container_id)
        i = c.commit(image.id, changes=newlabel)

    @classmethod
    def ready_(cls, container_id):

        try:
            c = cls.docker_client.containers.get(container_id)
            return c.ports['5001/tcp'][0]["HostPort"], c.ports['3000/tcp'][0]["HostPort"], c.ports["9000/tcp"][0][
                "HostPort"]
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
    def list_images(cls):
        docker_images = cls.docker_client.images.list(all=True, filters={"label": "vnv-image-info"})
        images = []
        for image in docker_images:
            b64 = image.labels["vnv-image-info"]
            inf = json.loads(bdec(b64))
            images.append(Image.from_json(inf))
        return images

