# -*- encoding: utf-8 -*-

import os
import uuid

from app import create_serve_app

import sys


class Config:
    DEBUG = True
    LOCAL = False
    basedir = os.path.abspath(os.path.dirname(__file__))
    passw = sys.argv[2] if len(sys.argv) > 2 else "password"
    auth = False
    port = 5001
    DEFAULT_DATA_PREFIX = "../build/"
    DOCKER_IMAGE = "vnv_serve"


app_config = Config()

app_config.DEBUG = False
socketio, app = create_serve_app(app_config)
socketio.run(app, use_reloader=False, host="0.0.0.0", port=app_config.port)
