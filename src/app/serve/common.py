import base64
import json
import time
import uuid
from flask import current_app


class Container:
    def __init__(self,id, user, name,image,resource,desc):
        self.id = id
        self.user = user
        self.name = name
        self.image = image
        self.stopped = False
        self.ltime = time.time()


        if not isinstance(resource,Resource):
            raise Exception("NOT RESOURCE")

        self.resource = resource
        self.desc = desc
        self.status_ = "undefined"

    def to_json(self):
        return json.dumps({
            "i" : self.id,
            "u": self.user,
            "n" : self.name,
            "im" : self.image,
            "re" : self.resource.to_json(),
            "d" : self.desc,
        })

    def stop(self):
        self.stopped = True

    def start(self):
        self.stopped = False
        self.ltime = time.time()

    def status(self):
        # If invalid but pretty new, then just wait
        if self.status_ == "invalid" and time.time() - self.ltime < 10:
            return "starting"

         # If exited, return that
        if self.status_ == "exited":
            return self.status_

        # If stopped but not exited, return stopping.
        if self.stopped:
            return "stopping"

        return self.status_

    def price(self):
        return self.resource.price

    @staticmethod
    def from_json(j):
        return Container(j["i"],j["u"],j["n"],j["im"],Resource.from_json(j["re"]),j["d"])


class Image:
    def __init__(self, id, user, name, desc, private=False):
        self.id = id
        self.name = name
        self.description = desc
        self.private = private
        self.user = user

    def to_json(self):
       return json.dumps({
        "i": self.id,
        "n": self.name,
        "d": self.description,
        "u": self.user,
        "p": self.private
        })

    @staticmethod
    def from_json(j):
        return Image(j["i"], j["u"], j["n"], j["d"], j["p"])


class Resource:
    def __init__(self, id, name, desc, price):
        self.id = id
        self.name = name
        self.description = desc
        self.price = price

    @staticmethod
    def from_json(j):
        return Resource(j["i"],j["n"],j["d"],j['p'])

    def to_json(self):
        return { "i" : self.id, "n" : self.name, "d" : self.description, "p" : self.price}

class CommonImpl:
    DEFAULT_IMAGES = []
    RESOURCES = {"basic": Resource("basic", "Basic", "Docker container will run on the webserver", 2)}
    CONTAINER_MAP = {}

    @classmethod
    def init_user(cls, username):
        if username not in cls.CONTAINER_MAP:
            cls.CONTAINER_MAP[username] = {"account": 10000, "containers": {}, "images": {},
                                           "volume": "vnv-" + uuid.uuid4().hex}
            cls.docker_client.volumes.create(cls.CONTAINER_MAP[username]["volume"])

    @classmethod
    def init_default_images(cls):
        if len(cls.DEFAULT_IMAGES) == 0:
            a = current_app.config["DOCKER_IMAGES"]
            for k, v in a.items():
                cls.DEFAULT_IMAGES.append(Image(k, "global", v[0], v[1], private=False))

    @classmethod
    def resources(cls, username):
        return list(cls.RESOURCES.values())

    @classmethod
    def images(cls,username, all=False):
        cls.init_default_images()
        cls.init_user(username)
        uimages = list(cls.CONTAINER_MAP.get(username).get("images").values())
        if all:
            uimages += cls.DEFAULT_IMAGES

        return uimages

    @classmethod
    def get_resource(cls,resource):
        if not isinstance(resource, Resource):
            resource = cls.RESOURCES.get(resource, cls.RESOURCES["basic"])
        return resource

    @classmethod
    def new_container(cls,username, containerName, image, resource, desc, id):
        resource = cls.get_resource(resource)
        cls.init_user(username)
        cls.CONTAINER_MAP[username]["containers"][id] = Container(id, username, containerName,image,resource,desc)
        return cls.CONTAINER_MAP[username]["containers"][id]

    @classmethod
    def new_container_(cls,container):
        cls.init_user(container.user)
        cls.CONTAINER_MAP[container.user]["containers"][container.id] = container
        return container

    @classmethod
    def mark_stopped(cls, username, container_id):
        cls.init_user(username)
        if container_id in cls.CONTAINER_MAP[username]["containers"]:
            cls.CONTAINER_MAP[username]["containers"][container_id].stop()

    @classmethod
    def mark_started(cls, username, container_id):
        cls.init_user(username)
        if container_id in cls.CONTAINER_MAP[username]["containers"]:
            cls.CONTAINER_MAP[username]["containers"][container_id].start()


    @classmethod
    def new_image(cls, username, name, desc, id):
        cls.init_user(username)
        cls.CONTAINER_MAP[username]["images"][id] = Image(id, username, name, desc, private=True)
        return cls.CONTAINER_MAP[username]["images"][id]

    @classmethod
    def new_image_(cls,image):
        cls.init_user(image.user)
        cls.CONTAINER_MAP[image.user]["images"][image.id] = image
        return image

    @classmethod
    def remove_container(cls,username, container_id):
        cls.init_user(username)
        if container_id in cls.CONTAINER_MAP[username]["containers"]:
            cls.CONTAINER_MAP[username]["containers"].pop(container_id)

    @classmethod
    def remove_image(cls, username, image_id):
        cls.init_user(username)
        if image_id in cls.CONTAINER_MAP[username]["images"]:
            cls.CONTAINER_MAP[username]["images"].pop(image_id)

    @classmethod
    def containers(cls,username):
        cls.init_user(username)
        return list(cls.CONTAINER_MAP.get(username).get("containers").values())

    @classmethod
    def get_user_volume_name(cls,username):
        cls.init_user(username)
        cls.CONTAINER_MAP.get(username).get("volume")

    @classmethod
    def add_money(cls, username, amount):
        cls.init_user(username)
        cls.CONTAINER_MAP[username]["account"] += amount;
        return cls.CONTAINER_MAP[username]["account"]

    @classmethod
    def remove_money(cls, username, amount):
        cls.init_user(username)
        cls.CONTAINER_MAP[username]["account"] -= amount;
        return cls.CONTAINER_MAP[username]["account"]

    @classmethod
    def balance(cls, username):
        cls.init_user(username)
        return cls.CONTAINER_MAP[username]["account"]


def benc(msg):
    message_bytes = msg.encode('ascii')
    base64_bytes = base64.b64encode(message_bytes)
    return base64_bytes.decode('ascii')

def bdec(msg):
    base64_bytes = msg.encode('ascii')
    message_bytes = base64.b64decode(base64_bytes)
    return message_bytes.decode('ascii')