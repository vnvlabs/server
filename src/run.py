# -*- encoding: utf-8 -*-


from app import create_serve_app
import sys,json
import os
import shutil

class Config:
    DEBUG=False
    port = 5001
    DOCKER_IMAGE = "vnv_serve"
    DEFAULT_USERS= {"Admin" : {"password" : "Admin", "admin" : True}}
    

app_config = Config()

with open(sys.argv[1],'r') as c:
    co = json.load(c)
    print(co)
    for k,v in co.items():

        try:
            setattr(app_config, k, v)
        except Exception as e:
            print(e, "Could not configure option ", k, v)


try: 
    shutil.copy(os.path.join(os.getcwd(),app_config.LOGO), "./src/app/static/assets/images/logo-dark.png")
except Exception as e:
    print(e)

try: 
    shutil.copy(os.path.join(os.getcwd(),app_config.ICON), "./src/app/static/assets/images/favicon.ico")
except Exception as e:
    print(e)


socketio, app = create_serve_app(app_config)
socketio.run(app, use_reloader=False, host="0.0.0.0", port=app_config.port)
