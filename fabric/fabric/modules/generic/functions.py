import hashlib
import hmac
from datetime import datetime
from flask import current_app
from math import sin, cos, sqrt, atan2, radians
from fabric.modules.settings.project_settings import MSG91_SEND_OTP_API, MSG91_AUTH_KEY, MSG91_TEMPLATE_ID, \
    MSG91_MESSAGE_PARAM_1
import requests
import json
import xml.etree.ElementTree as ET
from copy import copy


def generate_final_data(status_code, custom_message=False, key=False):
    """
    Function to generate the final data dict that needs to be sent back to client.
    @param status_code: App specific status_code (string constants)
    @param custom_message: Custom string message
    @param key: specific key
    @return: generated final_data variable
    """
    if status_code == 'INVALID':
        final_data = {"status": "failed", "status_code": status_code, "message": "Invalid request"}

    elif status_code == 'UNAUTHORIZED':
        final_data = {"status": "failed", "status_code": status_code,
                      "message": "Unauthorized access."}

    elif status_code == 'FAILED':
        final_data = {"status": "failed", "status_code": status_code,
                      "message": "Network seems to be busy. Please try again after some time"}

    elif status_code == 'API_KEY_NOT_FOUND':
        final_data = {"status": "failed", "status_code": status_code, "message": "API Key is not provided"}

    elif status_code == 'INVALID_API_KEY':
        final_data = {"status": "failed", "status_code": status_code, "message": "Invalid API key"}

    elif status_code == 'ACCESS_KEY_NOT_FOUND':
        final_data = {"status": "failed", "status_code": status_code, "message": "Access key is not provided"}

    elif status_code == 'INVALID_ACCESS_KEY':
        final_data = {"status": "failed", "status_code": status_code, "message": "Invalid Access key"}

    elif status_code == 'CUSTOM_FAILED':
        final_data = {"status": "failed", "status_code": status_code, "message": custom_message}

    elif status_code == 'KEY_NOT_PROVIDED':
        final_data = {"status": "failed", "status_code": status_code, "message": f"The key '{key}' is not provided"}

    elif status_code == 'ERROR':
        final_data = {"status": "failed", "status_code": status_code, "message": "Please try again after some time"}

    elif status_code == 'FORM_ERROR':
        final_data = {"status": "failed", "status_code": status_code, "message": "Validation error"}


    elif status_code == 'DATA_SAVE_FAILED':
        final_data = {"status": "failed", "status_code": status_code, "message": "Failed to save the data"}

    elif status_code == 'DATA_UPDATE_FAILED':
        final_data = {"status": "failed", "status_code": status_code, "message": "Failed to update the data"}

    elif status_code == 'DATA_DELETE_FAILED':
        final_data = {"status": "failed", "status_code": status_code, "message": "Failed to delete the data"}

    elif status_code == 'SUCCESS':
        final_data = {"status": "success", "status_code": status_code, "message": "Success"}

    elif status_code == 'CUSTOM_SUCCESS':
        final_data = {"status": "success", "status_code": status_code,
                      "message": custom_message}
    elif status_code == 'DATA_FOUND':
        final_data = {"status": "success", "status_code": status_code, "message": "Data retrieved successfully"}

    elif status_code == 'DATA_NOT_FOUND':
        final_data = {"status": "success", "status_code": status_code, "message": "No data found"}

    elif status_code == 'DATA_SAVED':
        final_data = {"status": "success", "status_code": status_code, "message": "Data saved successfully"}

    elif status_code == 'DATA_UPDATED':
        final_data = {"status": "success", "status_code": status_code, "message": "Data updated successfully"}

    elif status_code == 'DATA_DELETED':
        final_data = {"status": "success", "status_code": status_code, "message": "Data deleted successfully"}

    else:
        final_data = {"status": "failed", "status_code": status_code, "message": "Invalid request"}
    return final_data


def get_current_date():
    """
    Generating the current Unix datetime
    :return:
    """
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return current_date


def get_today():
    """
    Generating today date in Unix datetime
    @return:
    """
    today = datetime.today().strftime("%Y-%m-%d 00:00:00")
    return today


def json_input(request):
    """
    Function to extract json from the request
    @param request: HTTP request
    @return:json
    """
    try:
        data = request.json
        return data
    except Exception as e:
        data = generate_final_data('INVALID')
        return data


def generate_hash(string_val, length=False):
    """
    Function to generate a secret hash
    @param length: Length of the final hash value. Optional value.
    @param string_val: string that needs to be hashed
    @return: hashed value
    """

    hash = hmac.new(bytes(current_app.config["SECRET_KEY"], 'utf-8'), string_val.encode('utf-8'),
                    hashlib.sha256).hexdigest()
    if length:
        # If the specific length is given, return that much character length hash value.
        hash = hash[:length]
    return hash


def populate_errors(errors):
    """
    Method for populating errors from WTF forms
    @param errors: Flask-WTF form errors object
    @return: Final list of errors
    """
    final = []
    for key, values in errors.items():
        final.append({'field': key, 'errors': values})
    return final


def calculate_distance(source_lat, source_long, dest_lat, dest_long):
    """
    Calculating the aerial distance between two GPS coordinates in latitude and longitude.
    @rtype: object Flat value in KMs.
    @param source_lat: Latitude value of the source GPS coordinate.
    @param source_long: Longitude value of the source GPS coordinate.
    @param dest_lat: Latitude value of the destination GPS coordinate.
    @param dest_long: Longitude value of the destination GPS coordinate.
    """
    # approximate radius of earth in km
    R = 6371.0

    lat1 = radians(source_lat)
    lon1 = radians(source_long)

    lat2 = radians(dest_lat)
    lon2 = radians(dest_long)

    long_diff = lon2 - lon1
    lat_diff = lat2 - lat1

    a = sin(lat_diff / 2) ** 2 + cos(lat1) * cos(lat2) * sin(long_diff / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    # Distance in KM
    distance = R * c

    return distance


def send_otp(mobile_number, otp):
    """
    A function for sending an OTP using MSG91's OTP service.
    @return:
    """
    # Constructing the API url for the MSG91's OTP service.
    api_url = f'{MSG91_SEND_OTP_API}?authkey={MSG91_AUTH_KEY}&template_id={MSG91_TEMPLATE_ID}&extra_param=%7B%22{MSG91_MESSAGE_PARAM_1}%22%3A%22{otp}%22%7D&mobile=+91{mobile_number}&otp={otp}'
    api_response = requests.get(api_url)
    # Converting the string response to dict
    result = json.loads(api_response.text)
    return result


def verify_otp(mobile_number, otp):
    """
    A function for verifying the OTP with the MSG91 OTP service.
    @param mobile_number:
    @param otp:
    @return:
    """
    api_url = f'{MSG91_SEND_OTP_API}/verify?mobile=+91{mobile_number}&otp={otp}&authkey={MSG91_AUTH_KEY}'
    api_response = requests.post(api_url)
    # Converting the string response to dict
    result = json.loads(api_response.text)
    return result


def read_xml_string(xml_string):
    """
    A function for reading the xml string and converts them into a dict variable.
    @param xml_string: XML string
    @return: XML data in a dict format.
    """
    parent = ET.fromstring(xml_string)
    dict_var = xml_to_dict(parent)
    return dict_var


def xml_to_dict(r, root=True):
    """
    A function that helps to generate a dict from a XML string.
    @param r: Element
    @param root: Flag
    @return: XML data in dict format.
    """
    if root:
        return {r.tag: xml_to_dict(r, False)}
    d = copy(r.attrib)
    if r.text:
        d["_text"] = r.text
    for x in r.findall("./*"):
        if x.tag not in d:
            d[x.tag] = []
        d[x.tag].append(xml_to_dict(x, False))
    return d
