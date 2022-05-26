#! ./virt/bin/python 
# -*- encoding: utf-8 -*-


from app import create_serve_app
import sys,json
import os
import shutil

from app.serve.container import __execute_command__, image_exists


class Config:
    DEBUG=False
    port = 5001
    DEFAULT_USERS= {"Admin" : {"password" : "Admin", "admin" : True}}
    THEIA_FORWARDS = []
    DOCKER_IMAGES = {}
    ALLOW_NEW_USERS = True
    AUTHORIZATION_CODES = ["Trial"]
    HOST = "0.0.0.0"
    WSPATH = f"ws://{HOST}:{port}/ws"
    HOSTCORS = f"http://localhost:{port}"

app_config = Config()

with open(sys.argv[1],'r') as c:
    co = json.load(c)
    for k,v in co.items():
        try:
            setattr(app_config, k, v)
        except Exception as e:
            print(e, "Could not configure option ", k, v)

# Delete any images that dont work
fkeys = [k for k in app_config.DOCKER_IMAGES.keys() if not image_exists(k)]
for k in fkeys:
    print("Image ", k, " could not be found")
    app_config.DOCKER_IMAGES.pop(k)

if len(app_config.DOCKER_IMAGES) == 0:
    print("At least one VnV Enabled docker image is required.")
    exit(32)

forwards=[]
pvforwards = __execute_command__(list(app_config.DOCKER_IMAGES.keys())[0], "ls /paraview/share/paraview-5.10/web/visualizer/www" ).split("\n")
for line in pvforwards:
    kk = line.replace("\t", " ")
    forwards = forwards + line.split(" ")
app_config.PARAVIEW_FORWARDS = [ a.strip() for a in forwards if len(a) > 0 and a != "index.html"]


forwards=[]
theiaforwards = __execute_command__(list(app_config.DOCKER_IMAGES.keys())[0], "ls /theia/lib" ).split("\n")
for line in theiaforwards:
       kk = line.replace("\t", " " )
       forwards = forwards + kk.split(" ")
app_config.THEIA_FORWARDS = [ a.strip() for a in forwards if len(a) > 0 and a != "index.html"]


if __name__ == "__main__":
    socketio, app = create_serve_app(app_config)
    socketio.run(app, use_reloader=False, host=app_config.HOST, port=app_config.port)
