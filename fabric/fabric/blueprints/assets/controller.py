"""
------------------------
ASSETS CONTROLLER
The Flask blueprint module consisting of set of functions/APIs that deals with the sharing of static files
used by the customer's app/delivery app.
------------------------
Created on August 10, 2020.
Coded by: Krishna Prasad K
© Jyothy Fabricare Services LTD.
------------------------
"""

"""
Importing the built-in modules/third party libraries.
"""
import os
from flask import Blueprint, current_app, send_file, redirect

"""
Importing the project modules.
"""
from fabric.generic.functions import generate_final_data
from fabric.middlewares.auth_guard import asset_auth

# instance of assets blueprint
assets_routes_blueprint = Blueprint("assets", __name__, url_prefix='/assets', template_folder='templates',
                                    static_folder='static')


@assets_routes_blueprint.route('/', methods=["GET"])
def index():
    """
    Assets blueprint index route.
    @return:
    """
    # Redirects to the JFSL website.
    return redirect("https://jfsl.in", code=302)


@assets_routes_blueprint.route('/get/<file_type>/<detail>/<file_name>', methods=["GET"])
@asset_auth
def get(file_type, detail, file_name):
    """
    API for retrieving an asset/file.
    @param file_type: This can be icon,img,pdf...etc.
    @param detail: For eg: This can be garment, instruction, issue (All have icons assets).
    @param file_name: file name saved in the DB.
    @return: returns the asset if the asset is found, else return the FILE_NOT_FOUND error message.
    """
    if file_type == 'icon':
        if detail == 'garment':
            asset = read_icon('garments', file_name)
            if asset is not None:
                return send_file(asset, mimetype='image/svg+xml')
        elif detail == 'service_tat':
            asset = read_icon('service_tats', file_name)
            if asset is not None:
                return send_file(asset, mimetype='image/svg+xml')
        elif detail == 'service_type':
            asset = read_icon('service_types', file_name)
            if asset is not None:
                return send_file(asset, mimetype='image/svg+xml')
        elif detail == 'vas':
            asset = read_icon('vas', file_name)
            if asset is not None:
                return send_file(asset, mimetype='image/svg+xml')
        elif detail == 'issue':
            asset = read_icon('issues', file_name)
            if asset is not None:
                return send_file(asset, mimetype='image/svg+xml')

    final_data = generate_final_data('FILE_NOT_FOUND')
    return final_data


def read_icon(directory, file_name):
    """
    Reading the icon file from a given path.
    @param directory: directory of that icon file. Eg: garments.
    @param file_name: file name of that file.
    @return: target file path if file is a valid file, else return None.
    """
    root_dir = os.path.dirname(current_app.instance_path)
    target_file = f'{root_dir}/static/assets/icons/{directory}/{file_name}.svg'
    file_exists = os.path.exists(target_file)
    if file_exists:
        return target_file
    else:
        return None


def read_image(file_name):
    """
    Reading image files from a given path.
    @param file_name: image file name.
    @return: target file path if file is a valid file, else return None.
    """
    pass


def read_pdf(file_name):
    """
    Reading PDF files from a given path.
    @param file_name: PDF file name.
    @return: target file path if file is a valid file, else return None.
    """
    pass
