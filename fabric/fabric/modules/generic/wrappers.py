from functools import wraps
from flask import request, jsonify
from .functions import json_input


def json_wrapper(func):
    """
    Wrapping up the functions that deals with the JSON requests. If the JSON request is invalid, it
    instantly returned the fail response. If the json is valid, then proceed to the function and
    finally wraps the final_data dictionary in JSON format.
    :param func:
    :return: JSON object
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        json_request = json_input(request)
        if json_request.get('status') == 'failed':
            return jsonify(json_request)
        else:
            function = func(*args, **kwargs)
            return jsonify(function)

    return wrapper
