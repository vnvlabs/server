import uuid

from werkzeug.security import generate_password_hash, check_password_hash

class User:

    def __init__(self, username, password, admin=False, cookies=[], balance=1000, hashPassword=True, resources=[], images=[], **kwargs):
        self.username = username.lower()
        self.password = generate_password_hash(password) if hashPassword else password
        self.admin = admin
        self.cookies = cookies
        self.balance = balance
        self.resources = resources
        self.images = images


    def tojson(self):
        return {"username":self.username,
                "password":self.password,
                "admin":self.admin,
                "cookies":self.cookies,
                "balance":self.balance,
                "resources": self.resources,
                "images" : self.images
                }

    @classmethod
    def fromjson(cls,j):
        return User(**j, hashPassword=False)


    def check_password(self, password):
        return check_password_hash(self.password,password)

    def validate_cookie(self, cookie):
        return cookie in self.cookies

    def get_cookie(self):
        uid = self.username + ":" + uuid.uuid4().hex
        self.cookies.append(uid)
        return uid

    def remove_cookie(self, cookie):
        self.cookies.remove(cookie)

    def remove_all_cookies(self):
        self.cookies = []

    def reset_password(self, password, hashPassword=True):
        self.password = generate_password_hash(password) if hashPassword else password

    def add_money(self, add):
        self.balance += add

    def remove_money(self,amount):
        self.balance -= amount

    def add_resource(self, resource:str):
        if not self.has_resource(resource):
            self.resources.append(resource)

    def remove_resource(self, resource):
        self.resources.remove(resource)

    def has_resource(self, resource):
        return resource in self.resources

    def add_image(self, image:str):
        if not self.has_image(image):
            self.images.append(image)

    def remove_image(self, image):
        self.images.remove(image)

    def has_image(self, image):
        return image in self.images

