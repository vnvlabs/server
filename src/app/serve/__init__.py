# -*- encoding: utf-8 -*-
import asyncio
import re
import threading
import uuid
from os import abort

import requests
import websocket
import websockets
from flask import Blueprint, render_template, current_app, request, make_response, jsonify, send_file, g, Response
from werkzeug.utils import redirect
import docker
from flask_sock import Sock

from app.serve.container import list_user_images, list_user_containers, create_docker_container, \
    delete_docker_container, pull_image, \
    delete_docker_image, start_docker_container, create_docker_image, stop_docker_container, list_all_containers, \
    docker_container_ready, user_owns_image, ALL_RESOURCES

from app.serve.container import list_all_containers
from app.serve.resource import Container, Image, Resource
from app.serve.users import db

docker_client = docker.from_env()

import socketio as sio

blueprint = Blueprint(
    'base',
    __name__,
    url_prefix='',
    template_folder='templates'
)

ALL_IMAGES = {}
DEFAULT_IMAGES = []
DEFAULT_RESOURCES = []
DATABASE_IMPL = None

def getDatabaseImpl():
    return DATABASE_IMPL


# Decorator to enforce saving g.user at end of function.
def modifies_user():
    def decorator_func(func):
        def wrapper_func(*args, **kwargs):
            # Invoke the wrapped function first
            retval = func(*args, **kwargs)
            # Now do something here with retval and/or action
            if g.user is not None:
                getDatabaseImpl().updateUser(g.user)
            return retval
        return wrapper_func
    return decorator_func


def createUser(username, passw, authCode, admin=False, resources=DEFAULT_RESOURCES, images=DEFAULT_IMAGES, override=False):

    if not override:
        if  not current_app.config["ALLOW_NEW_USERS"]:
            return "New User creation is not supported at this time."

        if current_app.config.get("REQUIRE_AUTH",True):
            if not getDatabaseImpl().validateAuthcode(authCode):
                return "Invalid Authorization Code"

        if len(username) < 3:
            return "Username is to short"

        if len(username) > 20:
            return "Username is to long"

        if not re.match("^[a-zA-Z0-9]+$", username):
            return "Username is invalid [a-zA-Z0-9] only"

    if getDatabaseImpl().getUser(username) is not None:
        return "Username is not available"

    return getDatabaseImpl().createUser(username,passw, resources=resources,images=images, admin=admin)

def getUser(username):
    return getDatabaseImpl().getUser(username)

def userExists(username):
    return getUser(username) is not None

def verify_cookie(cook):
    g.user = None
    try:
        if cook is not None:
            s = cook.split(":")

            u = getUser(s[0])
            if u is None:
                return False

            if u.validate_cookie(cook):
                g.user = u
                return True

        return False
    except:
        return False

def list_users():
    if g.user.admin:
        return getDatabaseImpl().list_users()
    return [g.user]

@blueprint.before_request
def check_valid_login():
    login_valid = verify_cookie(request.cookies.get("vnv-docker-login"))
    if request.endpoint and request.endpoint != "base.login" and 'static' not in request.endpoint and not login_valid:
        return render_template('login.html', next=request.url, newuser=0)


@blueprint.route("/admin")
def admin_panel():
    if g.user.admin:
        return render_template("admin.html", users=list_users(), error="")


@blueprint.route("/admin/new_or_reset", methods=["POST"])
def new_user_or_reset_password():
    if g.user.admin:
        uname = request.form["username"]
        passw = request.form["password"]

        if userExists(uname):
            u = getUser(uname)
            u.reset_password(passw)
            getDatabaseImpl().updateUser(u)
        else:
            ne=createUser(uname, passw, admin=False)
            if isinstance(ne,str):
                return render_template("admin.html", users=list_users(), error="ne")
        return make_response(redirect("/admin"), 302)
    return redirect("/", 302)


@blueprint.route('/', methods=["GET"])
def home():
    return proxy("")

def createAccount():

    if g.user is not None:
        return proxy("login")

    uname = request.form.get("username").lower()
    passw = request.form.get("password")
    auth = request.form.get("auth")

    ne = createUser(uname, passw, auth)
    if isinstance(ne,str):
        return render_template("login.html", newerror=ne, newuser=1)
    return redirect("/", 302)



@blueprint.route('/containers', methods=["GET"])
def container_management():
    ims = list_available_images(g.user)
    pims = [i for i in ims if i.private]
    return render_template("container.html",
                           balance=g.user.balance_str(),
                           resources=list_available_resources(g.user),
                           pimages=pims,
                           images=ims,
                           containers=list_user_containers(g.user.uid),
                           message=None,
                           stopped_id=None
                           )

@blueprint.route('/container/refresh', methods=["GET"])
def container_management_r():
     return container_management_content()

def list_available_resources(user):
   return [ ALL_RESOURCES[r] for r in user.resources ]

def list_available_images(user):
    return [ ALL_IMAGES[r] for r in user.images  ] + list_user_images(user.uid)

def container_management_content(message=None, stopped_id=None):

    ims = list_available_images(g.user)
    pims = [i for i in ims if i.private]
    return render_template("container_content.html",
                           balance=g.user.balance_str(),
                           resources=list_available_resources(g.user),
                           images=ims,
                           pimages=pims,
                           containers=list_user_containers(g.user.uid),
                           message=message,
                           stopped_id = stopped_id
                           )


@blueprint.route('/container/create', methods=["POST"])
def create_container():
    name = request.form.get("name")
    image = request.form.get("image")
    resource = request.form.get("resource")

    if g.user.has_resource(resource):

        if not image in g.user.images:
            if not user_owns_image(image,g.user.uid):
                return make_response("invalid container config", 400)

        desc = request.form.get("desc","No description available")
        create_docker_container(g.user.uid, name, image, ALL_RESOURCES[resource], desc )
        return make_response(redirect("/containers"),302)

    return make_response("invalid container config", 400)

@blueprint.route('/container/stop/<cid>', methods=["POST"])
def stop_container(cid):
    stop_docker_container(g.user.uid, cid)
    return container_management_content(None, cid)

@blueprint.route('/container/start/<cid>', methods=["POST"])
def start_container(cid):
    start_docker_container(g.user.uid, cid)
    return container_management_content()

@blueprint.route('/container/delete/<cid>', methods=["POST"])
def delete_container(cid):
    delete_docker_container(g.user.uid,cid)
    return container_management_content()

@blueprint.route('/container/connect/<cid>', methods=["GET"])
def connect_to_container(cid):
    start_docker_container(g.user.uid, cid)
    response = make_response(redirect("/"))
    response.set_cookie('vnv-docker-connect', cid)
    return response

@blueprint.route('/container/snapshot', methods=["POST"])
def create_image():
    cid = request.form.get("id")
    create_docker_image(g.user.uid, cid, request.form.get("name"), request.form.get("description"))
    return make_response(redirect("/containers"))


@blueprint.route('/container/delete_image/<cid>', methods=["POST"])
def delete_image(cid):
    delete_docker_image(g.user.uid, cid)
    return container_management_content()

@blueprint.route('/container/balance', methods=["GET"])
def account_balance():
    return make_response(str(g.user.balance),200)


@blueprint.route('/container/fund/<int:amount>', methods=["POST"])
def add_funds(amount):
    g.user.add_money(amount)
    getDatabaseImpl().updateUser(g.user)
    return make_response(str(g.user.balance),200)

@blueprint.route("/paraview/", methods=["POST"])
def paraview_o():
    return make_response(jsonify({"sessionURL" : current_app.config["WSPATH"]}),200)

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

    if "auth" in request.form:
        return createAccount()

    uname = request.form.get("username").lower()
    user = getUser(uname)
    if user is not None and user.check_password(request.form.get("password")):
        response = make_response(redirect("/containers"))
        response.set_cookie('vnv-docker-login', user.get_cookie())
        getDatabaseImpl().updateUser(user)
        return response

    return render_template("login.html", loginerror="Invalid Password", newuser=0)


@blueprint.route('/logout', methods=["GET"])
def logout():

    response = make_response(redirect("/containers"))

    if "superhard" in request.args:
        g.user.remove_all_cookies()
        getDatabaseImpl().updateUser(g.user)
        response.set_cookie('vnv-docker-login', "", expires=0)

    elif "hard" in request.args:
        g.user.remove_cookie(request.cookies.get("vnv-docker-login"))
        getDatabaseImpl().updateUser(g.user)
        response.set_cookie('vnv-docker-login', "", expires=0)

    response.set_cookie('vnv-docker-connect', "", expires=0)
    return response

def loading(count):
    if count == 0:
        return render_template("loading.html", count=count)
    else:
        return make_response(str(count + 1), 205)


@blueprint.route('/<path:path>', methods=["GET", "POST"])
def proxy(path):

    def ppath(port,path=""):
        return f'http://{current_app.config["HOST"]}:{port}{path}'

    containerId = request.cookies.get("vnv-docker-connect")
    if containerId is None:
        return redirect("/containers")

    container, theia, paraview = docker_container_ready(g.user.uid,containerId)

    count = int(request.args.get("count", "0"))

    if container is None:
        return loading(count)

    try:
        if path == "theia":
            return redirect("/?theia")

        if path == "theia" or (path == "" and "theia" in request.args):
            PROXIED_PATH = ppath(theia)

        elif path == "paraview" or (path == "" and "paraview" in request.args):
            return render_template("pvindex.html")
        elif path in current_app.config["THEIA_FORWARDS"]:
            PROXIED_PATH = ppath(theia,request.full_path)
        elif path in current_app.config["PARAVIEW_FORWARDS"]:
            PROXIED_PATH = ppath(paraview,request.full_path)
        else:
            PROXIED_PATH = ppath(container,request.full_path)

        if request.method == "GET":
            resp = requests.get(PROXIED_PATH)
            excluded_headers = ["content-encoding", "content-length", "transfer-encoding", "connection"]
            headers = [(name, value) for (name, value) in resp.raw.headers.items() if
                       name.lower() not in excluded_headers]
            response = Response(resp.content, resp.status_code, headers)
            return response

        elif request.method == "POST":
            try:
                request.is_json
            except Exception as e:
                print("What")

            if not request.is_json :
                resp = requests.post(PROXIED_PATH, data=request.form)
            else:
                resp = requests.post(PROXIED_PATH, json=request.get_json())

            excluded_headers = ["content-encoding", "content-length", "transfer-encoding", "connection"]
            headers = [(name, value) for (name, value) in resp.raw.headers.items() if
                       name.lower() not in excluded_headers]
            response = Response(resp.content, resp.status_code, headers)

            return response
        else:
            print("Unsupported Query sent to proxy")

    except Exception as e:
        return loading(count)

def start_container_monitoring():

    def monitor_containers():
        remove_money = {}
        for container in list_all_containers():
            if container.status() == "running":
                if container.user not in remove_money:
                    remove_money[container.user] = container.price()
                else:
                    remove_money[container.user] += container.price()

        getDatabaseImpl().update_money(remove_money)


    def monitor_containers_forever():
        ev = threading.Event()
        while True:
            monitor_containers()
            ev.wait(60)

    threading.Thread(target=monitor_containers_forever).start()


def register(socketio, apps, config):

    for k,v in config.DOCKER_IMAGES.items():
        ALL_IMAGES[k] = Image(k,"N/A",v[0],v[1],False)
        DEFAULT_IMAGES.append(k)

    for k in config.DEFAULT_RESOURCES:
        DEFAULT_RESOURCES.append(k)


    global DATABASE_IMPL
    DATABASE_IMPL = db.Configure(config)

    for i in config.AUTHORIZATION_CODES:
        getDatabaseImpl().createAuthcode(i)

    apps.register_blueprint(blueprint)

    #Monitor the containers
    start_container_monitoring()

    #Register the default users.
    for k, v in config.DEFAULT_USERS.items():
        p = uuid.uuid4().hex[0:9]
        s = createUser(k, p, v.get("admin", False), override=True)
        if isinstance(s,str):
            print(s)
        else:
            print("Created user ",k, " with password ", p)

    # Pull all the docker images:


    #Forward all the socket connections.
    class SocketContainer:
        def __init__(self, pty, theia=False):
            self.pty = pty
            self.user = g.user.uid
            self.sock = None
            self.sid = request.sid
            self.theia = theia

        def connect(self):
            if self.sock is None:
                containerId = request.cookies.get("vnv-docker-connect")
                container, theia, paraview = docker_container_ready(g.user.uid, containerId)

                # If theia then set the docker theia port instead.
                container = theia if self.theia else container

                if container is not None:
                    self.sock = sio.Client()

                    self.sock.connect("http://localhost:" + container, namespaces=[f"/{self.pty}"])

                    @self.sock.on('*', namespace=f"/{self.pty}")
                    def catch_all(event, data):
                        try:
                            socketio.emit(event, data, namespace=f"/{self.pty}", to=self.sid)
                        except Exception as e:
                            print(e)

        def to_docker_container(self, event, data):
            self.connect()
            if self.sock is not None:
                count = 0
                while count < 5:
                    try:
                        self.sock.emit(event=event, data=data, namespace=f"/{self.pty}")
                        count = 100
                    except:
                        threading.Event().wait(1)
                        count += 1
            else:
                socketio.emit("Could not connect", namespace=f"/{self.pty}", to=self.sid)

    socks = {
        "pty": {},
        "pypty": {},
        "theia": {},
        "pv": {}
    }

    def a_check_valid_login():
        return verify_cookie(request.cookies.get("vnv-docker-login"))

        # Forward websocket to the paraview server.

    sock = Sock(apps)

    class WSockApp:
        def __init__(self, ip, ws):
            self.wsock = websocket.create_connection("ws://localhost:" + ip + "/ws")
            self.killed = False
            self.ws = ws

        def kill(self):
            self.killed = True

        def running(self):
            return not self.killed

        def send(self,mess):
            self.wsock.send(mess)

        def run(self):
            while not self.killed:
                mess = self.wsock.recv()
                self.ws.send(mess)

        def serve(self):
            threading.Thread(target=self.run).start()

    @sock.route("/ws")
    def echo(ws):
        if a_check_valid_login():
            containerId = request.cookies.get("vnv-docker-connect")
            container, theia, paraview = docker_container_ready(g.user.uid, containerId)
            wsock = WSockApp(paraview, ws)
            wsock.serve()
            while wsock.running():
                try:
                    greeting = ws.receive()
                    wsock.send(greeting)
                except Exception as e:
                    wsock.kill()

    def wrap(pty):

        @socketio.on(f"{pty}-input", namespace=f"/{pty}")
        def pty_input(data):
            if a_check_valid_login():
                if request.sid in socks[pty]:
                    socks[pty][request.sid].to_docker_container(f"{pty}-input", data)

        @socketio.on("resize", namespace=f"/{pty}")
        def pyresize(data):
            if a_check_valid_login():
                if request.sid in socks[pty]:
                    socks[pty][request.sid].to_docker_container(f"resize", data)

        @socketio.on("connect", namespace=f"/{pty}")
        def pyconnect():
            if a_check_valid_login() :
                try:
                    socks[pty][request.sid] = SocketContainer(pty)
                except Exception as e:
                    print(e)

        @socketio.on("disconnect", namespace=f"/{pty}")
        def pydisconnect():
            if a_check_valid_login():
                if request.sid in socks[pty]:
                    socks[pty].pop(request.sid)


    wrap("pty")
    wrap("pypty")

    @socketio.on("connect", namespace=f"/services")
    def theiaconnect(**kwargs):
        if a_check_valid_login():
            socks["theia"][request.sid] = SocketContainer("services", True)

    @socketio.on('message', namespace="/services")
    def catch_message(data, **kwargs):
        if a_check_valid_login():
            if g.user.uid in socks["theia"]:
                socks["theia"][request.sid].to_docker_container(f"message", data)

    @socketio.on('disconnect', namespace="/services")
    def abcatch_disconnect(**kwargs):
        if a_check_valid_login():
            if request.sid in socks["theia"]:
                socks["theia"].pop(request.sid)