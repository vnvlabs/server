from app.serve.users.user import User


class InMemoryUserManagement:

    def __init__(self, config):
        self.users = {}
        self.authcodes = set()

    def valid_auth_code(self, code: str) -> bool:
        return code in self.auth_codes

    def create_authcode(self, code: str):
        self.authcodes.add(code)

    def delete_authcode(self, code: str):
        if code in self.authcodes:
            self.authcodes.remove(code)

    def get_user(self, username: str) -> User:
        return self.users.get(username)

    def create_user(self, user: User):
        self.users[user.username.lower()] = user
        return user

    def delete_user(self, username: str):
        if username in self.users:
            self.users.pop(username)

    def update_user(self, user: User):
        self.users[user.username] = user

    def list_users(self) -> list:
        return list(self.users.values())

    def update_money(self, amounts):
        for k,v in amounts.items():
            u = self.get_user(k)
            if u is not None:
                u.remove_money(v)
