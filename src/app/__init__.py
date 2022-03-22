# -*- encoding: utf-8 -*-

from flask import Flask,render_template

from flask_socketio import SocketIO


def configure_error_handlers(app):
    @app.errorhandler(404)
    def fourohfour(e):
        return render_template('page-404.html'), 404

    @app.errorhandler(403)
    def fourohthree(e):
        return render_template('page-403.html'), 403

    @app.errorhandler(500)
    def fivehundred(e):
        return render_template('page-500.html'), 500


def create_serve_app(config):
    import app.serve

    app = Flask(__name__, static_folder="static")
    app.config.from_object(config)
    socketio = SocketIO(app)
    serve.register(socketio, app, config)

    return socketio, app
