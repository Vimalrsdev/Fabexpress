# EasyRewardz library module
import requests
from fabric.modules.generic.functions import read_xml_string
from fabric.modules.settings.project_settings import ER_CONFIG
from datetime import datetime
import xml.etree.ElementTree as ET


def get_er_token():
    """
    API for generating an EasyRewardz token.
    @return: Result in dict format.
    """
    # URL for the get_token API
    api_url = "http://lpaaswebapi.easyrewardz.com/api/GenerateSecurityToken"

    # XML request body
    xml = """<Request>
                <UserName>PrestigeClub</UserName>
                <UserPassword>PrestigeClub123</UserPassword>
                <DevId>363da8b2-398b-4eda-b2f0-cb0f637986a2</DevId>
                <AppId>f6e8a14d-49e0-452c-8fe4-9f4e8a3c6bee</AppId>
                <ProgramCode>prestigeclub</ProgramCode>
            </Request>"""

    headers = {'Content-Type': 'application/xml'}
    response = requests.post(api_url, data=xml, headers=headers)

    # Generating a XML tree element from the response
    xml_response = ET.fromstring(response.text)

    # Getting the SecurityToken
    token = xml_response.find('SecurityToken')
    if token is not None:
        # ER token is found and successfully parsed.
        token = token.text
    return token


def validate_er_coupon(customer_code, branch_code, er_coupon):
    """
    API for validating a discount code with EasyRewardz.
    @param customer_code: POS customer code.
    @param branch_code: Branch code of the customer.
    @param er_coupon: ER coupon code that needs to be validated.
    @return:
    """
    # Since EasyRewardz have no direct validation method,
    # first block the ER coupon and then unblock it.

    # Generating the ER token.
    token = get_er_token()

    # Calling the redeem coupon API for blocking the coupon.
    block = block_er_coupon(customer_code, branch_code, er_coupon, token)

    if block['er_request_id'] and block['pos_discount_code']:
        # Successfully blocked the coupon. Now unblock the coupon with the request id.
        unblock_er_coupon(block['er_request_id'], er_coupon, token)


def block_er_coupon(customer_code, branch_code, er_coupon, token=None):
    """
    Function for calling the EasyRewardz block API i.e. RedeemCoupon API.
    This API will block an ER coupon.
    @param token: ER token
    @param customer_code: POS customer code.
    @param branch_code: Branch code of the customer.
    @param er_coupon: ER coupon code needs to be blocked.
    @return:
    """

    # Getting the ER token if no token is passed over.
    if token is None:
        token = get_er_token()
    today = datetime.today().strftime("%d %b %Y")

    # URL for the redeem coupon API
    api_url = 'http://lpaaswebapi.easyrewardz.com/api/RedeemCoupon'

    # XML request body
    xml = f"""<Request> 
        <SecurityToken>{token}</SecurityToken>
        <MemberID>{customer_code}</MemberID>
        <Date>{today}</Date>
        <StoreCode>{branch_code}</StoreCode>
        <PayableAmount>100</PayableAmount>
        <UserName>{ER_CONFIG['ER_API_USER']}</UserName>
        <CouponCode>{er_coupon}</CouponCode>
        <CountryCode>91</CountryCode>
        </Request>"""

    headers = {'Content-Type': 'application/xml'}
    response = requests.post(api_url, data=xml, headers=headers)

    # Generating a XML tree element from the response
    xml_response = ET.fromstring(response.text)

    if int(xml_response.find('ReturnCode').text) == 0:
        # Here, ER coupon has been successfully blocked.
        # In return, they'll send us a POS discount code and request ID.
        pos_discount_code = xml_response.find('POSPromo')
        # For each redeem coupon API, there'll be a corresponding ER request id.
        er_request_id = xml_response.find('RequestID')
    else:
        # Failed response. Failed to block the coupon (Invalid coupon, any other errors...etc).
        pos_discount_code = None
        er_request_id = None

    result = {'pos_discount_code': pos_discount_code, 'er_request_id': er_request_id}
    return result


def unblock_er_coupon(request_id, er_coupon, token=None):
    """
    Function for calling EasyRewardz unblock coupon API.
    After blocking the coupon, ER coupon can be unblocked based on the request id.
    @param request_id: The ID returned by ER upon the block coupon (Redeem coupon) API call.
    @param er_coupon: EasyRewardz coupon code needs to be unblocked.
    @param token: ER token.
    @return:
    """
    # Getting the ER token if no token is passed over.
    if token is None:
        token = get_er_token()

    # URL for the unblock coupon API
    api_url = "http://lpaaswebapi.easyrewardz.com/api/UnBlockCoupon"

    # XML request body
    xml = f"""<Request>
    <RequestID>{request_id}</RequestID>
    <CouponCode>{er_coupon}</CouponCode>
    <UserName>{ER_CONFIG['ER_API_USER']}</UserName>
    <SecurityToken>{token}</SecurityToken>
    </Request>"""

    headers = {'Content-Type': 'application/xml'}
    response = requests.post(api_url, data=xml, headers=headers)


def get_available_er_lp(customer_code):
    """
    Function for calling the EasyRewardz AvailablePoints API. Which returns the available loyalty points for a customer.
    @param customer_code:
    @return:
    """
    # Getting the ER token
    token = get_er_token()

    # URL for the unblock coupon API
    api_url = "http://lpaaswebapi.easyrewardz.com/api/CustomerAvailablePoints"

    # XML request body
    xml = f"""<Request>
            <EasyId>{customer_code}</EasyId>
            <SecurityToken>{token}</SecurityToken>
            <CountryCode>91</CountryCode>
            </Request>"""

    headers = {'Content-Type': 'application/xml'}
    response = requests.post(api_url, data=xml, headers=headers)

    # Generating a XML tree element from the response
    xml_response = ET.fromstring(response.text)

    if int(xml_response.find('ReturnCode').text) == 0:
        # Successfully retrieved the result.
        available_points = int(xml_response.find('AvailablePoints').text)
        point_value = float(xml_response.find('PointValue').text)
        point_rate = float(xml_response.find('PointRate').text)
    else:
        # Failed to get the response.
        available_points = None
        point_value = None
        point_rate = None

    result = {'available_points': available_points, 'point_value': point_value, 'point_rate': point_rate}
    return result
