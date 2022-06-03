from app.serve.users.memory import InMemoryUserManagement
from app.serve.users.mongo import MongoUserManagement
from app.serve.users.user import User


class DBImpl:

    def __init__(self, impl):
        self.impl = impl

    def createAuthcode(self, authcode):
        self.impl.create_authcode(authcode)

    def deleteAuthcode(self, authcode):
        self.impl.delete_authcode(authcode)

    def validateAuthcode(self, authcode):
        return self.impl.valid_auth_code(authcode)

    def createUser(self, username, raw_password, resources, images, admin=False) -> User:
        return self.impl.create_user(User(username, raw_password, admin, resources=resources, images=images))

    def getUser(self, username) -> User:
        return self.impl.get_user(username)

    def deleteUser(self, username):
        self.impl.delete_user(username)

    def updateUser(self, user: User):
        self.impl.update_user(user)

    def list_users(self):
        return self.impl.list_users()

    def update_money(self, amounts):
        return self.impl.update_money(amounts)


def Configure(config) -> DBImpl:
    try:
        return DBImpl(MongoUserManagement(config.MONGO_CONFIG))
    except Exception as e:
        print("Could not connect to the mongo server -- launching with in memory db instead ", e)
    return DBImpl(InMemoryUserManagement(config))
