import base64
import json
import time


def benc(msg):
    message_bytes = msg.encode('ascii')
    base64_bytes = base64.b64encode(message_bytes)
    return base64_bytes.decode('ascii')

def bdec(msg):
    base64_bytes = msg.encode('ascii')
    message_bytes = base64.b64decode(base64_bytes)
    return message_bytes.decode('ascii')


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

    def to_json1(self):
        return {
            "i": self.id,
            "u": self.user,
            "n": self.name,
            "im": self.image,
            "d": self.desc,
        }

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


