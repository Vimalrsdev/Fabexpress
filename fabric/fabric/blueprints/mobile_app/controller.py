"""
------------------------
MOBILE APP CONTROLLER
The Flask blueprint module consisting of set of functions/APIs that are used by the customer's mobile app.
------------------------
Created on May 20, 2020.
Coded by: Krishna Prasad K
© Jyothy Fabricare Services LTD.
------------------------
"""

"""
Importing the built-in modules/third party libraries.
"""
from flask import Blueprint, redirect

# instance of mobile app blueprint
mobile_blueprint = Blueprint("mobile", __name__, url_prefix='/mobile')


@mobile_blueprint.route('/')
def index():
    # Redirects to the JFSL website.
    return redirect("https://jfsl.in", code=302)
