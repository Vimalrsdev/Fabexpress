"""
------------------------
API CONTROLLER
The Flask blueprint Module that handles the API routes console page.
------------------------
Created on June 25, 2020.
Coded by: Krishna Prasad K
© Jyothy Fabricare Services LTD.
------------------------
"""

"""
Importing the built-in modules/third party libraries.
"""
from flask import Blueprint, request, render_template, redirect, url_for, jsonify
from flask_login import current_user, login_user, logout_user, login_required
from sqlalchemy import func

"""
Importing the project modules.
"""
from .forms import LoginForm
from .user_manager import *
from .models import APIRoutesUser, APIRoute
from fabric import db
from fabric.generic.functions import generate_hash
from fabric.generic.loggers import error_logger

# instance of API routes blueprint
api_routes_blueprint = Blueprint("api_routes", __name__, url_prefix='/routes', template_folder='templates',
                                 static_folder='static')


@api_routes_blueprint.route('/login', methods=["GET", "POST"])
def login():
    """
    login API for the routes admin console.
    @return:
    """
    # List of variables that can be accessed in the template.
    data = {'title': "Fabric APIs login", 'page': 'login'}

    form = LoginForm()
    if request.method == "GET":

        if current_user.is_authenticated:

            return redirect(url_for('api_routes.api_list'))
        else:
            return render_template("login.html", data=data, form=form)
    else:

        if form.validate_on_submit():
            username = form.username.data
            password = form.password.data
            hashed_password = generate_hash(password, 50)

            try:
                admin = db.session.query(APIRoutesUser).filter(APIRoutesUser.Username == username,
                                                               APIRoutesUser.Password == hashed_password).one_or_none()

                if admin is not None:
                    login_user(admin)
                    return redirect(url_for('api_routes.api_list'))
            except Exception as e:
                error_logger().error(e)

        else:
            pass

        return render_template("login.html", data=data, form=form)


@api_routes_blueprint.route('/logout', methods=["GET"])
@login_required
def logout():
    """
    logout API for the routes admin console.
    @return:
    """
    logout_user()
    return redirect(url_for('api_routes.login'))


@api_routes_blueprint.route('/', methods=["GET"])
@login_required
def api_list():
    """
    Home page of the routes console.
    @return: A page that shows the list of APIs available with its count, categorized.
    """
    # List of variables that can be accessed in the template.
    data = {'title': "Fabric APIs", 'delivery_apis_count': 0, 'store_console_apis_count': 0,
            'customer_app_apis_count': 0,
            'assets_apis_count': 0}

    try:
        # Number of APIs available in the delivery blueprint.
        delivery_apis_count = db.session.query(func.count(APIRoute.Id)).filter(APIRoute.APIGroup == "Delivery",
                                                                               APIRoute.IsCompleted == 1).scalar()

        # Number of APIs available in the assets blueprint.
        assets_apis_count = db.session.query(func.count(APIRoute.Id)).filter(APIRoute.APIGroup == "Assets",
                                                                             APIRoute.IsCompleted == 1).scalar()

        # Number of APIs available in the store console blueprint.
        store_console_apis_count = db.session.query(func.count(APIRoute.Id)).filter(APIRoute.APIGroup == "StoreConsole",
                                                                                    APIRoute.IsCompleted == 1).scalar()

        # Setting up the variable that needs to be passed to the view template.
        data['delivery_apis_count'] = delivery_apis_count
        data['assets_apis_count'] = assets_apis_count
        data['store_console_apis_count'] = store_console_apis_count
        data['customer_app_apis_count'] = 0

    except Exception as e:
        error_logger().error(e)

    return render_template("api_list.html", data=data)


@api_routes_blueprint.route('/delivery', methods=["GET"])
@login_required
def delivery():
    """
    Delivery APIs page.
    @return: A page that shows the list of APIs available in
    the delivery controller.
    """
    # List of variables that can be accessed in the template.
    data = {"title": "Delivery APIs", "page": "Delivery", "base_url": "http://api.jfslcloud.in/delivery"}
    api_routes = []

    try:
        # Getting the API routes available for the delivery.
        api_routes = db.session.query(APIRoute).filter(APIRoute.APIGroup == "Delivery", APIRoute.IsCompleted == 1).all()
    except Exception as e:
        error_logger().error(e)

    return render_template("delivery_apis.html", data=data, routes=api_routes)


@api_routes_blueprint.route('/assets', methods=["GET"])
@login_required
def assets():
    """
    Assets APIs page.
    @return: A page that shows the list of APIs available in
    the assets controller.
    """
    # List of variables that can be accessed in the template.
    data = {"title": "Assets APIs", "page": "Assets", "base_url": "http://api.jfslcloud.in/assets"}
    api_routes = []

    try:
        # Getting the API routes available for the assets.
        api_routes = db.session.query(APIRoute).filter(APIRoute.APIGroup == "Assets", APIRoute.IsCompleted == 1).all()
    except Exception as e:
        error_logger().error(e)

    return render_template("assets_apis.html", data=data, routes=api_routes)


@api_routes_blueprint.route('/store', methods=["GET"])
@login_required
def store():
    """
    Store web console APIs page.
    @return: A page that shows the list of APIs available in
    the store web console controller.
    """
    # List of variables that can be accessed in the template.
    data = {"title": "Store Web Console APIs", "page": "Store Web Console",
            "base_url": "http://api.jfslcloud.in/store_console"}
    api_routes = []

    try:
        # Getting the API routes available for the assets.
        api_routes = db.session.query(APIRoute).filter(APIRoute.APIGroup == "StoreConsole",
                                                       APIRoute.IsCompleted == 1).all()
    except Exception as e:
        error_logger().error(e)

    return render_template("store_console_apis.html", data=data, routes=api_routes)
