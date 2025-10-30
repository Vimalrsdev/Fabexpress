"""
------------------------
Fabric module
The Flask factory module for the Fabric project.
------------------------
Coded by: Krishna Prasad K
© Jyothy Fabricare Services LTD.
------------------------
"""

from flask import Flask, render_template, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from sqlalchemy.orm import DeclarativeBase

from fabric.settings.project_settings import CURRENT_ENV

# Define base model for SQLAlchemy 2.0
class Base(DeclarativeBase):
    pass

# Configure SQLAlchemy with the new base model
db = SQLAlchemy(model_class=Base)

login_manager = LoginManager()


def create_app():
    """
    Function to create a Flask application object.
    @return:
    """
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)

    if CURRENT_ENV == 'development':
        app.config.from_object('config.DevelopmentConfig')
    elif CURRENT_ENV == 'production':
        app.config.from_object('config.ProductionConfig')
    else:
        # default is development
        app.config.from_object('config.DevelopmentConfig')

    @app.route('/')
    def index():
        return redirect("https://jfsl.in", code=302)

    register_extensions(app)

    register_blueprints(app)

    register_error_handlers(app)

    return app


def register_extensions(app):
    """
    Function to register the Flask extensions
    @param app: Flask application object
    """
    db.init_app(app)

    login_manager.init_app(app)


def register_blueprints(app):
    """
    Function to register Flask blueprints
    @param app: Flask application object
    """
    from fabric.blueprints.web_app.controller import web_blueprint
    from fabric.blueprints.mobile_app.controller import mobile_blueprint
    from fabric.blueprints.delivery_app.controller import delivery_blueprint
    from fabric.blueprints.store_console.controller import store_console_blueprint
    from fabric.blueprints.api_routes.controller import api_routes_blueprint
    from fabric.blueprints.assets.controller import assets_routes_blueprint
    app.register_blueprint(web_blueprint)
    app.register_blueprint(mobile_blueprint)
    app.register_blueprint(delivery_blueprint)
    app.register_blueprint(store_console_blueprint)
    app.register_blueprint(api_routes_blueprint)
    app.register_blueprint(assets_routes_blueprint)


def register_error_handlers(app):
    """
    Function to register Flask error handlers.
    @param app: Flask application object
    """
    from fabric.generic.error_handlers import handle_401, handle_404, handle_405, handle_500

    app.register_error_handler(401, handle_401)
    app.register_error_handler(404, handle_404)
    app.register_error_handler(405, handle_405)
    # If the PROPAGATE_EXCEPTION is False, Flask will treat it as internal server error including exceptions.
    # The following method will only be called when PROPAGATE_EXCEPTION is False.
    # app.register_error_handler(500, handle_500)
    # If PROPAGATE_EXCEPTION is True, Flask will treat it as exception and call the following method
    # The following method will be called when PROPAGATE_EXCEPTION is True or False
    app.register_error_handler(Exception, handle_500)
