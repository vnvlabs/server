import pymongo

from app.serve.users.user import User


class MongoUserManagement:

    def __init__(self, mongo_config):

        self.url = mongo_config.get("url",'mongodb://localhost:27017/')
        self.dbname = mongo_config.get("db","vnv-serve")

        self.client = pymongo.MongoClient(self.url, serverSelectionTimeoutMS=2000)

        if mongo_config.get("drop",False):
            self.client.drop_database(self.dbname)

        self.db = self.client[self.dbname]

        if not self.collection_exists("users"):
            self.db.create_collection("users")

        if not self.collection_exists("codes"):
            self.db.create_collection("codes")

        self.users = self.db.get_collection("users")
        self.codes = self.db.get_collection("codes")

    def collection_exists(self,name):
        return name in self.db.list_collection_names()

    def valid_auth_code(self, code: str) -> bool:
        return self.codes.find_one(filter={"value":code}) is not None

    def create_authcode(self, code: str):
        self.codes.insert_one({"value" : code})

    def delete_authcode(self, code: str):
        self.codes.delete_one(filter={"value":code})

    def get_user(self, username: str) -> User:
        u = self.users.find_one(filter={"username": username})
        if u is not None:
            return User.fromjson(u)
        return None

    def create_user(self, user: User):
        u = self.get_user(user.username)
        if u is None:
            self.users.insert_one(user.tojson())
        return u

    def delete_user(self, username: str):
        self.users.delete_one(filter={"username":username})

    def update_user(self, user: User):
        self.users.replace_one(filter={"username":user.username}, replacement=user.tojson())

    #TODO Paginate
    def list_users(self) -> list:
        return [User.fromjson(j) for j in self.users.find()]

    #TODO Bulk operation
    def update_money(self, amounts):
        for k,v in amounts.items():
            u = self.get_user(k)
            if u is not None:
                u.remove_money(v)
                self.update_user(u)
