from flask import Blueprint

# instance of web console blueprint
web_console_blueprint = Blueprint("web_console", __name__, url_prefix='/web_console')


@web_console_blueprint.route('/')
def index():
    return "Web console route"
