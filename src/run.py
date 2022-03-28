# -*- encoding: utf-8 -*-


from app import create_serve_app
import sys,json

class Config:
    DEBUG=False
    port = 5001
    DOCKER_IMAGE = "vnv_serve"
    DEFAULT_USERS= {"Admin" : {"password" : "Admin", "admin" : True}}


app_config = Config()

with open(sys.argv[1],'r') as c:
    co = json.load(c)
    for k,v in co.items():
        try:
            app_config[k] = v
        except:
            print("Could not configure option ", k, v)
socketio, app = create_serve_app(app_config)
socketio.run(app, use_reloader=False, host="0.0.0.0", port=app_config.port)
