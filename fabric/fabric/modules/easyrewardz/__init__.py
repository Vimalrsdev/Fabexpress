"""
------------------------
EasyRewardz module
The module deals with the integration of the EasyRewardz.
(third-party library)
------------------------
Coded by: Krishna Prasad K
© Jyothy Fabricare Services LTD.
------------------------
"""

import requests
from fabric.generic.functions import read_xml_string
from fabric.settings.project_settings import ER_CONFIG, redeem_er_coupon_url, unblock_er_coupon_url
from datetime import datetime
import xml.etree.ElementTree as ET
from . import queries as queries
from fabric.generic.loggers import er_logger
import fabric.modules.payment as payment_module


def get_er_token():
    """
    API for generating an EasyRewardz token.
    @return: ER API token in a string format else None.

    # URL for the get_token API
    api_url = "http://lpaaswebapi.easyrewardz.com/api/GenerateSecurityToken"

    # XML request body
    xml_request = f""<Request>
                <UserName>{ER_CONFIG['ER_USERNAME']}</UserName>
                <UserPassword>{ER_CONFIG['ER_PASSWORD']}</UserPassword>
                <DevId>{ER_CONFIG['ER_DEV_ID']}</DevId>
                <AppId>{ER_CONFIG['ER_APP_ID']}</AppId>
                <ProgramCode>{ER_CONFIG['ER_PROGRAM_CODE']}</ProgramCode>
            </Request>""

    # Logging the API request.
    log_er_request('get_er_token', xml_request)

    headers = {'Content-Type': 'application/xml'}
    response = requests.post(api_url, data=xml_request, headers=headers)

    # Generating a XML tree element from the response
    xml_response = ET.fromstring(response.text)

    # Logging the API response.
    log_er_response('get_er_token', xml_response)

    # Getting the SecurityToken
    token = xml_response.find('SecurityToken')
    if token is not None:
        # ER token is found and successfully parsed.
        token = token.text
    return token """
    return "123456"


def validate_er_coupon(customer_code, branch_code, er_coupon):
    """
    API for validating a discount code with EasyRewardz.
    @param customer_code: POS customer code.
    @param branch_code: Branch code of the customer.
    @param er_coupon: ER coupon code that needs to be validated.
    @return: Result in a Dict format.
    """
    # Result variable.
    valid_coupon = {'status': False, 'discount_code': None}

    # Generating the ER token.
    token = get_er_token()

    # Since EasyRewardz have no direct validation method,
    # first block the ER coupon and then unblock it.

    # Calling the redeem coupon API for blocking the coupon.
    block = block_er_coupon(customer_code, branch_code, er_coupon, token)
    if block['er_request_id'] and block['pos_discount_code']:
        # Successfully blocked the coupon. Now unblock the coupon with the request id.
        unblock = unblock_er_coupon(block['er_request_id'], er_coupon, token)
        if unblock:
            # Successfully unblocked as well.
            valid_coupon['status'] = True
            valid_coupon['discount_code'] = block['pos_discount_code']
            valid_coupon['er_request_id'] = block['er_request_id']

    return valid_coupon


"------------------------------------ APIs related to the EasyRewardz coupon ------------------------------"


def block_er_coupon(customer_code, branch_code, er_coupon, token=None):
    """
    Function for calling the EasyRewardz block API i.e. RedeemCoupon API.
    This API will block an ER coupon.
    @param token: ER token
    @param customer_code: POS customer code.
    @param branch_code: Branch code of the customer.
    @param er_coupon: ER coupon code needs to be blocked.
    @return: Result in a Dict format.
    """

    # Getting the ER token if no token is passed over.
    if token is None:
        token = get_er_token()
    today = datetime.today().strftime("%d %b %Y")

    # URL for the redeem coupon API
    api_url = redeem_er_coupon_url

    # XML request body
    xml_request = f"""<Request> 
        <SecurityToken>{token}</SecurityToken>
        <MemberID>{customer_code}</MemberID>
        <Date>{today}</Date>
        <StoreCode>{branch_code}</StoreCode>
        <PayableAmount>100</PayableAmount>
        <UserName>{ER_CONFIG['ER_API_USER']}</UserName>
        <CouponCode>{er_coupon}</CouponCode>
        <CountryCode>91</CountryCode>
        </Request>"""

    # Logging the API request.
    log_er_request('block_er_coupon', xml_request)

    headers = {'Content-Type': 'application/xml'}
    response = requests.post(api_url, data=xml_request, headers=headers)

    # Generating a XML tree element from the response
    xml_response = ET.fromstring(response.text)

    # Logging the API response.
    log_er_response('block_er_coupon', xml_response)

    if int(xml_response.find('ReturnCode').text) == 0:
        # Here, ER coupon has been successfully blocked.
        # In return, they'll send us a POS discount code and request ID.
        pos_discount_code = xml_response.find('POSPromo').text
        # For each redeem coupon API, there'll be a corresponding ER request id.
        er_request_id = xml_response.find('RequestID').text
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
    @return: True if ER coupon is successfully unblocked, False if not.
    """
    # Getting the ER token if no token is passed over.
    if token is None:
        token = get_er_token()

    # URL for the unblock coupon API
    # api_url = "http://lpaaswebapi.easyrewardz.com/api/UnBlockCoupon"
    api_url = unblock_er_coupon_url

    # XML request body
    xml_request = f"""<Request>
    <RequestID>{request_id}</RequestID>
    <CouponCode>{er_coupon}</CouponCode>
    <UserName>{ER_CONFIG['ER_API_USER']}</UserName>
    <SecurityToken>{token}</SecurityToken>
    </Request>"""

    # Logging the API request.
    log_er_request('unblock_er_coupon', xml_request)

    headers = {'Content-Type': 'application/xml'}
    response = requests.post(api_url, data=xml_request, headers=headers)

    # Generating a XML tree element from the response
    xml_response = ET.fromstring(response.text)

    # Logging the API response.
    log_er_response('unblock_er_coupon', xml_response)

    if int(xml_response.find('ReturnCode').text) == 0:
        # Here, ER coupon has successfully unblocked.
        return True
    else:
        # Failed to unblock the ER coupon code.
        return False


def use_er_coupon(egrn, invoice_number, amount):
    """
    Calling the ER API for finalizing the usage of a ER coupon after completing the
    payment and settlement.
    @param egrn: EGRN of the order.
    @param invoice_number: Invoice number generated of the order.
    @param amount: Amount of the order.
    @return:
    ""
    # Checking whether the EGRN has an ER coupon attached to it or not.
    er_coupon_details = queries.get_er_coupon_data_for_confirmation(egrn)
    if er_coupon_details['ISLASTInvoice'] == 'YES':
        if er_coupon_details['Discount'] == 0:
            if er_coupon_details['ERRequestID'] and er_coupon_details['ERCouponCode']:
                unblock_er_coupon(er_coupon_details['ERRequestID'], er_coupon_details['ERCouponCode'])

        else:
            if er_coupon_details['ERRequestID'] and er_coupon_details['ERCouponCode']:
                # A ER coupon code is attached to this EGRN. So call the ER api to redeem it.
                token = get_er_token()

                # URL for the use coupon API
                api_url = "http://lpaaswebapi.easyrewardz.com/api/UseCoupon"

                # XML request body
                xml_request = f""<Request>
                    <RequestID>"{er_coupon_details['ERRequestID']}</RequestID>
                    <CouponCode>{er_coupon_details['ERCouponCode']}</CouponCode>
                    <BillNo>{invoice_number}</BillNo>
                    <Discount>{er_coupon_details['Discount']}</Discount>
                    <OTP></OTP>
                    <TotalPaidAmount>{amount}</TotalPaidAmount>
                    <UserName>{ER_CONFIG['ER_API_USER']}</UserName>
                    <SecurityToken>{token}</SecurityToken>
                    <CountryCode></CountryCode>
                    </Request>""

                # Logging the API request.
                log_er_request('use_er_coupon', xml_request)

                headers = {'Content-Type': 'application/xml'}
                # Calling the API.
                response = requests.post(api_url, data=xml_request, headers=headers)

                # Generating a XML tree element from the response
                xml_response = ET.fromstring(response.text)

                # Logging the API response.
                log_er_response('use_er_coupon', xml_response) """


"------------------------------------ APIs related to the EasyRewardz loyalty points ------------------------------"


def get_available_er_lp(customer_code):
    """
    Function for calling the EasyRewardz AvailablePoints API. Which returns the available loyalty points for a customer.
    @param customer_code:
    @return: Result in a Dict format.

    # Getting the ER token
    token = get_er_token()

    # URL for the unblock coupon API
    api_url = "http://lpaaswebapi.easyrewardz.com/api/CustomerAvailablePoints"

    # XML request body
    xml_request = f""<Request>
            <EasyId>{customer_code}</EasyId>
            <SecurityToken>{token}</SecurityToken>
            <CountryCode>91</CountryCode>
            </Request>""

    # Logging the API request.
    log_er_request('get_available_er_lp', xml_request)

    headers = {'Content-Type': 'application/xml'}
    response = requests.post(api_url, data=xml_request, headers=headers)

    # Generating a XML tree element from the response
    xml_response = ET.fromstring(response.text)

    # Logging the API response.
    log_er_response('get_available_er_lp', xml_response)

    if int(xml_response.find('ReturnCode').text) == 0:
        # Successfully retrieved the result.
        available_points = int(xml_response.find('AvailablePoints').text)
        point_value = float(xml_response.find('PointValue').text)
        point_rate = float(xml_response.find('PointRate').text)
    else:
        # Failed scenario. Eg: Member ID does not exist case in EasyRewardz.
        available_points = 0
        point_value = 0
        point_rate = 0

    result = {'available_points': available_points, 'point_value': point_value, 'point_rate': point_rate}
    return result """
    return True


def block_er_loyalty_points(customer_code, transaction_code, easy_points, amount, egrn):
    """
    API for blocking the EasyRewardz loyalty points.
    @param customer_code: POS customer code.
    @param transaction_code: ER transaction code.
    @param easy_points:
    @param amount: Amount of the transaction.
    @param egrn:
    @return:

    # Getting the ER token
    token = get_er_token()

    today = datetime.today().strftime("%d %b %Y")

    # URL for the block loyalty points API.
    api_url = "http://lpaaswebapi.easyrewardz.com/api/CheckForEasyPointsRedemption"

    # XML request body
    xml_request = f""<Request>
            <SecurityToken>{token}</SecurityToken>
            <StoreCode>{ER_CONFIG['ER_STORE_CODE']}</StoreCode>
            <UserName>{ER_CONFIG['ER_API_USER']}</UserName>
            <EasyId>{customer_code}</EasyId>
            <TransactionCode>{transaction_code}</TransactionCode>
            <EasyPoints>{easy_points}</EasyPoints>
            <TransactionDescription></TransactionDescription>
            <RedemptionDate>{today}</RedemptionDate>
            <Amount>{amount}</Amount>
            <RedemptionType>PD</RedemptionType>
            <ActivityCode>RED01</ActivityCode>
            <CountryCode>91</CountryCode>
            </Request>""

    # Logging the API request.
    log_er_request('block_er_loyalty_points', xml_request)

    headers = {'Content-Type': 'application/xml'}
    # Calling the API.
    response = requests.post(api_url, data=xml_request, headers=headers)

    # Generating a XML tree element from the response
    xml_response = ET.fromstring(response.text)

    # Logging the API response.
    log_er_response('block_er_loyalty_points', xml_response) """


def unblock_er_loyalty_points(customer_code, transaction_code, branch_code):
    """
    API for unblocking ER loyalty points.
    @param customer_code: POS customer code.
    @param transaction_code: ER transaction code.
    @param branch_code: BranchCode.
    @return:

    # Getting the ER token
    token = get_er_token()

    today = datetime.today().strftime("%d %b %Y")

    # URL for the unblock coupon API.
    api_url = "http://lpaaswebapi.easyrewardz.com/api/ReleaseRedemptionPoints"

    # XML request body
    xml_request = f""<Request>
            <SecurityToken>{token}</SecurityToken>
            <StoreCode>{branch_code}</StoreCode>
          <UserName>{ER_CONFIG['ER_API_USER']}</UserName>
          <EasyId>{customer_code}</EasyId>
          <TransactionCode>{transaction_code}</TransactionCode>
          <TransactionDate>{today}</TransactionDate>
          <CountryCode>91</CountryCode>
            </Request>""

    # Logging the API request.
    log_er_request('unblock_er_loyalty_points', xml_request)

    headers = {'Content-Type': 'application/xml'}
    # Calling the API.
    response = requests.post(api_url, data=xml_request, headers=headers)

    # Generating a XML tree element from the response
    xml_response = ET.fromstring(response.text)

    # Logging the API response.
    log_er_response('unblock_er_loyalty_points', xml_response) """


def confirm_er_loyalty_points(customer_code, transaction_code, invoice_number, amount):
    """
    API for confirming the finalizing the redemption of the ER loyalty points.
    @param customer_code: POS customer code.
    @param transaction_code: ER transaction code.
    @param invoice_number: Invoice number generated after the settlement.
    @param amount: Amount of the transaction.
    @return:

    # Getting the ER token
    token = get_er_token()

    # API URL for the confirming the loyalty points redemption.
    api_url = "http://lpaaswebapi.easyrewardz.com/api/ConfirmEasyPointsRedemption"

    # XML request body
    xml_request = f""
            <Request>
              <SecurityToken>{token}</SecurityToken>
              <RedemptionCode></RedemptionCode>
              <UserName>{ER_CONFIG['ER_API_USER']}</UserName>
              <EasyId>{customer_code}</EasyId>
              <TransactionCode>{transaction_code}</TransactionCode>
              <EOSSAmount>0</EOSSAmount>
              <NONEOSSAmount>0</NONEOSSAmount>
              <NetAmount>0</NetAmount>
              <NewTransactionCode>{invoice_number}</NewTransactionCode>
              <CountryCode>91</CountryCode>
            </Request>""

    # Logging the API request.
    log_er_request('confirm_er_loyalty_points', xml_request)

    headers = {'Content-Type': 'application/xml'}

    # Calling the API.
    response = requests.post(api_url, data=xml_request, headers=headers)

    # Generating a XML tree element from the response
    xml_response = ET.fromstring(response.text)

    # Logging the API response.
    log_er_response('confirm_er_loyalty_points', xml_response) """


def save_sku_details(egrn, invoice_number, grand_total, gateway=None):
    """
    Function for calling “SaveSKUBillDetails” API after successful invoice settlement based on LOYALTY POINT
    from mobile app/web app in order to change invoice data sharing process from 6 hours interval to real time.
    @param egrn: EGRN of the order.
    @param invoice_number: Invoice number generated after settling the order.
    @param grand_total: Amount paid by the customer on this order.
    @param gateway: Payment gateway (if any).
    @return:

    # Getting the ER token
    token = get_er_token()

    today = datetime.today().strftime("%d %b %Y")

    # API URL for the confirming the loyalty points redemption.
    api_url = "http://lpaaswebapi.easyrewardz.com/api/SaveSKUBillDetails"

    # Getting the details required for calling this API.
    er_invoice_sku_details = queries.get_attached_er_sku_details(egrn, invoice_number)

    # Getting the customer details from the egrn.
    customer_details = payment_module.queries.get_customer_details_from_egrn(egrn)

    if customer_details:
        branch_code = customer_details['BRANCHCODE']
        customer_code = customer_details['CUSTOMERCODE']

        # XML request body
        xml_request = f""
                    <Request>
                      <SecurityToken>{token}</SecurityToken>
                      <StoreCode>{branch_code}</StoreCode>
                      <TransactionDate>{today}</TransactionDate>
                      <BillNo>{invoice_number}</BillNo>
                      <EasyId>{customer_code}</EasyId>
                      <UserName>{ER_CONFIG['ER_API_USER']}</UserName>
                      <Channel></Channel>
                      <CustomerType></CustomerType>
                      <BillValue>{grand_total}</BillValue>
                      <PrimaryOrderNumber></PrimaryOrderNumber>
                      <PointsRedeemed></PointsRedeemed>
                      <PointsValueRedeemed></PointsValueRedeemed>
                      <AllowPointIssuance></AllowPointIssuance>
                      <IssuanceOnRedemption></IssuanceOnRedemption>
                      <SKUOfferCode></SKUOfferCode>
                      <CountryCode>91</CountryCode>
                      <TransactionItems>""

        for sku_detail in er_invoice_sku_details:
            # Looping through the essential details for SKU api and creating the TransactionItem(s) that will
            # append to the request body.
            total_price = sku_detail['Amount'] + sku_detail['ServiceTax']
            if sku_detail['MiscDiscount'] is None:
                # No miscellaneous discounts are applied.
                misc_discount = 0
            else:
                # miscellaneous discounts are applied.
                misc_discount = sku_detail['MiscDiscount']
            billed_price = total_price - sku_detail['Discount'] - misc_discount

            # Concatenating the TransactionItem scope to the XML request string.
            xml_request += f""<TransactionItem>
                      <ItemType>s</ItemType>
                      <ItemQty>1</ItemQty>
                      <Unit>{round(sku_detail['Amount'], 2)}"</Unit>
                      <ItemDiscount>{round((misc_discount + sku_detail['Discount']), 2)}</ItemDiscount>
                      <ItemTax>{round(sku_detail['ServiceTax'], 2)}</ItemTax>
                      <TotalPrice>{round(total_price, 2)}</TotalPrice>
                      <BilledPrice>{round(billed_price, 2)}</BilledPrice>
                      <Department>D1</Department>
                      <Category>C1</Category>
                      <Group>G1</Group>
                      <ItemId>{sku_detail['GarmentID']}</ItemId>
                    </TransactionItem>
                    ""
        # Closing the TransactionItems scope and starting the PaymentMode scope.
        xml_request += "</TransactionItems><PaymentMode>"

        # Default is zaakpay
        tender_code = '9mobikwik'

        # Based on the gateway, tender_code will be populated.
        if gateway is not None:
            if gateway.lower() == 'paytm':
                tender_code = '7paytm'
            elif gateway.lower() == 'zaakpay':
                tender_code = '9mobikwik'

        tenders = []
        if er_invoice_sku_details[0]['LoyaltyPointsAmount'] != 0 and er_invoice_sku_details[0][
            'LoyaltyPointsAmount'] != None:
            # Some loyalty points have been applied on this order.
            if er_invoice_sku_details[0]['FinalInvoiceAmount'] == er_invoice_sku_details[0]['LoyaltyPointsAmount']:
                # The order is fully settled with the loyalty points.
                tender_dict = {'tender_code': 'Point', 'tender_value': er_invoice_sku_details[0]['Loyaltypoints']}
                tenders.append(tender_dict)
            else:
                # The order is settled with in some loyalty points and in some other way..
                # eg: payment gateway, coupon..etc.
                tender_dict = {'tender_code': 'Point', 'tender_value': er_invoice_sku_details[0]['Loyaltypoints']}
                tenders.append(tender_dict)

                tender_dict = {'tender_code': tender_code,
                               'tender_value': er_invoice_sku_details[0]['FinalInvoiceAmount'] -
                                               er_invoice_sku_details[0][
                                                   'LoyaltyPointsAmount']}
                tenders.append(tender_dict)

        else:
            # This order is not settled with any loyalty points.
            tender_dict = {'tender_code': tender_code,
                           'tender_value': er_invoice_sku_details[0]['FinalInvoiceAmount']}

            tenders.append(tender_dict)

        tenders_str = ''
        # Looping through the tenders and construct the tender XML-like string.
        for tender in tenders:
            tenders_str += f""
                <TenderItem>
                    <TenderCode>{tender['tender_code']}</TenderCode>
                    <TenderID></TenderID>
                    <TenderValue>{tender['tender_value']}</TenderValue>
                </TenderItem>""

        # Concatenating the tender xml string to the xml_request.
        xml_request += tenders_str
        # Closing the PaymentMode scope and starting the Request scope.
        xml_request += "</PaymentMode><Request>"

        # Logging the API request.
        log_er_request('save_sku_details', xml_request)

        headers = {'Content-Type': 'application/xml'}

        # Calling the API.
        response = requests.post(api_url, data=xml_request, headers=headers)

        # Generating a XML tree element from the response
        xml_response = ET.fromstring(response.text)

        # Logging the API response.
        log_er_response('save_sku_details', xml_response) """


def log_er_request(function_name, xml_request):
    """
    Function for saving the log of ER API requests.
    @param function_name:
    @param xml_request:
    @return:
    """
    er_logger(f'Request for {function_name}').info(xml_request)


def log_er_response(function_name, xml_response):
    """
    Function for saving the log of ER API responses.
    @param function_name:
    @param xml_response:
    @return:
    """
    er_logger(f'Response for {function_name}').info(ET.tostring(xml_response, encoding='unicode'))
