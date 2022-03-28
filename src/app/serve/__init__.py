# -*- encoding: utf-8 -*-
import uuid
from os import abort

import requests
import websocket
from flask import Blueprint, render_template, current_app, request, make_response, jsonify, send_file, g, Response
from werkzeug.utils import redirect
from werkzeug.security import generate_password_hash, check_password_hash
from app.serve.container import launch_docker_container, docker_container_ready, stop_docker_container
import docker

docker_client = docker.from_env()
import socketio as sio

blueprint = Blueprint(
    'base',
    __name__,
    url_prefix='',
    template_folder='templates'
)

def init_users():
  if len(users) == 0:
    adminCount = 0
    try:
        for k,v in current_app.config["DEFAULT_USERS"].items():
            createUser(k, generate_password_hash(v["password"]), v.get("admin", False))
            if v.get("admin", False):
                adminCount += 1
    except:
        print("USER CONFIGURATION ERROR -- CHECK YOUR DEFAULT USERS AND TRY AGAIN")
        abort()
    if len(users) == 0:
        print("NO DEFAULT USER FOUND -- CHECK YOUR DEFAULT USERS AND TRY AGAIN")
        abort()
    if adminCount == 0:
        print("NO ADMIN USERS FOUND -- You wont be able to configure users ")

users = {
}

def getUser(username):
    init_users()
    return users.get(username,None)

def createUser(username, passw, admin=False):
    users[username] = { "Password" : passw, "Admin" : admin } 

def userExists(username):
    init_users()
    return username in users


def GET_COOKIE_TOKEN(username):
    
    if not userExists(username):
        return None

    cook = getUser(username).get("Cookie")
    if cook is None:
        uid = uuid.uuid4().hex
        getUser(username)["Cookie"] = uid
        return username + ":" + uid
    else:
        return username + ":" + cook


def verify_cookie(cook):
    g.user = None
    try:
        if cook is not None:
            s = cook.split(":")
           
            u = getUser(s[0])
            if u is None:
                return False
            elif u["Cookie"] == s[1]:
                g.user = s[0]
                return True
        return False
    except:
        return False

@blueprint.before_request
def check_valid_login():
    login_valid = verify_cookie(request.cookies.get("vnv-docker-login"))
    if request.endpoint and request.endpoint != "base.login" and 'static' not in request.endpoint and not login_valid:
        return render_template('login.html', next=request.url)


@blueprint.route("/admin")
def admin_panel():
    if getUser(g.user)["Admin"]:
        return render_template("admin.html", users=users, error="")


@blueprint.route("/admin/new_or_reset", methods=["POST"])
def new_user_or_reset_password():
    if getUser(g.user)["Admin"]:
        uname = request.form["username"]
        passw = request.form["password"]
        
        if userExists(uname):
            u = getUser(uname)
            u["Password"] = generate_password_hash(passw)
        else:
            createUser(uname, generate_password_hash(passw))

        return make_response(redirect("/admin"), 302)

    return redirect("/", 302)


@blueprint.route('/', methods=["GET"])
def home():
    return proxy("")


@blueprint.route('/login', methods=["POST"])
def login():
    # If the user is logged in, then we forward the login
    # request to the proxy. There is no need for double
    # security, so this should not happen (authentication should
    # be turned off in the docker container -- all authentication
    # is done here based on the FACT that the containers are running on
    # localhost and are not accessible to the outside world.
    if g.user is not None:
        return proxy("login")

    uname = request.form.get("username")
    
    if userExists(uname) and  check_password_hash(getUser(uname)["Password"], request.form.get("password")):
        launch_docker_container(uname, request.form.get("password"), current_app.config["DOCKER_IMAGE"])
        response = make_response(redirect("/"))
        response.set_cookie('vnv-docker-login', GET_COOKIE_TOKEN(uname))
        return response

    return render_template("login.html", error=True)


@blueprint.route('/logout', methods=["GET"])
def logout():
    # We do not proxy logout requests -- We just log the user out and stop
    # there container. This is nice as it means the logout button in the container
    # works (make sure?)
    getUser(g.user).pop("Cookie")
    stop_docker_container()
    response = make_response(redirect("/"))
    response.set_cookie('vnv-docker-login', "", expires=0)
    response.set_cookie('vnv-container-login', "", expires=0)
    return response


def loading(count):
    if count == 0:
        return render_template("loading.html", count=count)
    else:
        return make_response(str(count + 1), 205)


@blueprint.route('/<path:path>', methods=["GET", "POST"])
def proxy(path):
    container = docker_container_ready()
    count = int(request.args.get("count", "0"))

    if container is not None:
        try:
            requests.get("http://localhost:" + container + "/")
        except:
            return loading(count)
    else:
        return loading(count)

    PROXIED_PATH = "http://localhost:" + container + request.full_path
    if request.method == "GET":
        resp = requests.get(PROXIED_PATH)
        excluded_headers = ["content-encoding", "content-length", "transfer-encoding", "connection"]
        headers = [(name, value) for (name, value) in resp.raw.headers.items() if name.lower() not in excluded_headers]
        response = Response(resp.content, resp.status_code, headers)
        return response

    elif request.method == "POST":
        if request.get_json() is None:
            resp = requests.post(PROXIED_PATH, data=request.form)
        else:
            resp = requests.post(PROXIED_PATH, json=request.get_json())

        excluded_headers = ["content-encoding", "content-length", "transfer-encoding", "connection"]
        headers = [(name, value) for (name, value) in resp.raw.headers.items() if name.lower() not in excluded_headers]
        response = Response(resp.content, resp.status_code, headers)

        return response


def register(socketio, apps, config):
        

    apps.register_blueprint(blueprint)

    class SocketContainer:
        def __init__(self, pty):
            self.pty = pty
            self.user = g.user
            self.sid = request.sid
            self.sock = None

        def connect(self):
            if self.sock is None:
                self.container = docker_container_ready()
                if container is not None:
                    self.sock = sio.Client()
                    self.sock.connect("http://localhost:" + self.container, namespaces=[f"/{self.pty}"])

                    @self.sock.on('*', namespace=f"/{self.pty}")
                    def catch_all(event, data):
                        try:
                            print("GGG ", data, self)

                            socketio.emit(event, data, namespace=f"/{self.pty}", to=self.sid)
                        except Exception as e:
                            print(e)

        def to_docker_container(self, event, data, namespace):
            self.connect()
            print("HHH ", data)
            if self.sock is not None:
                self.sock.emit(event=event, data=data, namespace=f"/{self.pty}")
            else:
                socketio.emit("Could not connect", namespace=f"/{self.pty}", to=self.sid)

    socks = {
        "pty": {},
        "pypty": {}
    }

    def a_check_valid_login():
        check_valid_login()
        return g.user

    def wrap(pty):

        @socketio.on(f"{pty}-input", namespace=f"/{pty}")
        def pty_input(data):
            if a_check_valid_login() is not None:
                if g.user in socks[pty]:
                    socks[pty][g.user].to_docker_container(f"{pty}-input", data, namespace=f"/{pty}")

        @socketio.on("resize", namespace=f"/{pty}")
        def pyresize(data):
            if a_check_valid_login() is not None:
                if g.user in socks[pty]:
                    socks[pty][g.user].to_docker_container(f"resize", data, namespace=f"/{pty}")

        @socketio.on("connect", namespace=f"/{pty}")
        def pyconnect():
            if a_check_valid_login() is not None:
                try:
                    socks[pty][g.user] = SocketContainer(pty)
                except Exception as e:
                    print(e)

    wrap("pty")
    wrap("pypty")
