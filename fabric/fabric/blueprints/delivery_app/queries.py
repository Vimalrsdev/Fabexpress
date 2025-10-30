"""
DB SQL Alchemy queries can be written here...
"""
from sqlalchemy import case, and_, func, text, literal, or_, String, cast
from fabric import db
from fabric.modules.models import OrderGarment, PickupCancelReason, PickupRescheduleReason, PriceList, Order, Garment, \
    GarmentInstruction, OrderInstruction, Branch, Area, MSSWeeklyOff, DeliveryDateEstimator, City, CustomerAddres, \
    PickupRequest, PickupReschedule, PickupTimeSlot, DeliveryUser, Customer, Delivery, DeliveryReschedule, \
    DeliveryRequest, TravelLog, DeliveryUserBranch, BranchHoliday, DeliveryUserAttendance, DeliveryGarment, GarmentUOM, \
    Complaint, TransactionPaymentInfo, TransactionInfo
from fabric.generic.functions import get_current_date, send_sms_laundry
from fabric.settings.project_settings import SERVER_DB, LOCAL_DB, PAYMENT_LINK_API_KEY, CURRENT_ENV, ALERT_ENGINE_DB, \
    ICE_CUBES_SMS_API, ICE_CUBES_TRANSACTIONAL_SMS_API_KEY, ICE_CUBES_SENDER, invoice_generate_url, \
    invoice_link_shortening_url
from datetime import datetime, timedelta
import inspect
import fabric.modules.payment as payment_module
import json
from flask import request
from fabric.generic.loggers import error_logger, info_logger
from fabric.generic.classes import CallSP
import requests
import haversine as hs


def update_lat_long(lat, long, Custlat, Custlong, TRNNo, EGRN, BranchCode, UserId):
    
    distance = 0
    DuserDistance = ""
    StoreDistance = ""
    updated = False

    
    CustomerLocation = (Custlat, Custlong)
    DeliveryUserLocation = (lat, long)

    # Calculate customer-to-delivery distance
    if CustomerLocation and DeliveryUserLocation:
        distance = hs.haversine(CustomerLocation, DeliveryUserLocation)
        if distance >= 1:
            km_part = int(distance)
            meters_part = (distance - km_part) * 1000
            DuserDistance = f"{km_part} km {int(meters_part)} m"
        else:
            DuserDistance = f"{int(distance * 1000)} m"

    # Get Branch Location
    BranchLocationRow = db.session.execute(
        text("""SELECT Lat, Long, BranchName 
                FROM JFSL.dbo.Branchinfo 
                WHERE BranchCode = :BranchCode"""),
        {"BranchCode": BranchCode}
    ).fetchone()

    if BranchLocationRow:
        BranchLocation = (float(BranchLocationRow.Lat), float(BranchLocationRow.Long))
        BranchName = BranchLocationRow.BranchName

        # Calculate delivery-to-branch distance
        store_distance = hs.haversine(BranchLocation, DeliveryUserLocation)
        if store_distance >= 1:
            km_part = int(store_distance)
            meters_part = (store_distance - km_part) * 1000
            StoreDistance = f"{km_part} km {int(meters_part)} m"
        else:
            StoreDistance = f"{int(store_distance * 1000)} m"

    # Update DB
    db.session.execute(text("""
        UPDATE JFSL.DBO.FabdeliveryInfo 
        SET DUserId = :DUserId,
            DuserLat = :DuserLat,
            DuserLong = :DuserLong,
            CustLat = :CustLat,
            CustLong = :CustLong,
            Store_distance = :Store_distance,
            Distance = :Distance
        WHERE TRNNO = :TRNNo AND EGRNNo = :EGRN
    """), {
        "DUserId": UserId,
        "DuserLat": lat,
        "DuserLong": long,
        "CustLat": Custlat,
        "CustLong": Custlong,
        "Store_distance": StoreDistance,
        "Distance": DuserDistance,
        "TRNNo": TRNNo,
        "EGRN": EGRN
    })

    db.session.commit()
    updated = True

    return updated


# Edited by MMM
def get_customer_id_from_code(customer_code):
    """
    Function for returning customer id
    """
    customer_details = db.session.query(Customer.CustomerId).filter(
        Customer.CustomerCode == customer_code).one_or_none()

    return customer_details.CustomerId if customer_details is not None else None


def get_delivery_request_id_from_egrn(egrn):
    """
    Function for returning delivery request id by passing egrn
    """
    delivery_request_details = db.session.query(DeliveryRequest.DeliveryRequestId).join(Order,
                                                                                        Order.OrderId == DeliveryRequest.OrderId).filter(
        Order.EGRN == egrn, Order.IsDeleted == 0).one_or_none()

    return delivery_request_details.DeliveryRequestId if delivery_request_details is not None else None




def invoice_link_shortening(invoice_num):
    """
    Function for shortening Invoice URL
    """
    invoice_link = None
    try:
        # Generating invoice link through url for sending via SMS
        invoice_link = invoice_generate_url + invoice_num
        headers = {'Content-Type': 'application/json', 'api_key': PAYMENT_LINK_API_KEY}

        # url for shortening the invoice link for sending via SMS
        api_url = invoice_link_shortening_url
        # passing invoice_num in request body of url
        json_request = {'invoiceno': invoice_num}

        # Calling the API.
        response = requests.post(api_url, data=json.dumps(json_request), headers=headers)

        response = json.loads(response.text)
        log_data = {
            'response': response,
            'request': json_request
        }
        info_logger(f'Route: {api_url}').info(json.dumps(log_data))
        if response:
            # A valid response has been received.
            if response['status'] == "success":
                # Shortened Link generation is successful.
                invoice_link = response['url']
    except Exception as e:
        error_logger(f'Delivery Blueprint Queries: {inspect.stack()[0].function}()').error(e)

    return invoice_link

def invoice_generate(invoice_num):
    """
       Function for  Invoice report
    """
    invoice_url = None

    try:

        data = {
            "reportName": 'Invoice',
            "DocumentNo": invoice_num
        }
        data_string = json.dumps(data)
        headers = {'Content-Type': 'application/json', 'Content-Length': str(len(data_string))}

        # url for generate the report
        api_url = "http://192.168.202.4/GetMobileReports/api/GenerateReport"
        response = requests.post(api_url, data=data_string, headers=headers)

        response = json.loads(response.text)

        log_data = {
            'invoice_generate :': response
        }
        info_logger(f'Route: {request.path}').info(json.dumps(log_data))

        if response:
            # A valid response has been received.
            if response['status'] == "success":
                invoice_url = response['url']

    except Exception as e:
        error_logger(f'Delivery Blueprint Queries: {inspect.stack()[0].function}()').error(e)


    return invoice_url


def send_sms_via_ice_cube(mobile_num, message):
    """
    Function for sending SMS through ice cube
    """

    api_url = f'{ICE_CUBES_SMS_API}/?api_key={ICE_CUBES_TRANSACTIONAL_SMS_API_KEY}&method=sms&to={mobile_num}&sender={ICE_CUBES_SENDER}&message={message}'

    requests.get(api_url)


# def trigger_sms_after_pickup(alert_code, customer_id, booking_id, date_time_slot):
#     """
#     Function for send SMS via SP after adhoc pickup for future date
#     """
#     query = None
#     # Getting customer details from DB
#     customer_details = db.session.query(Customer.MobileNo, Customer.CustomerName).filter(
#         Customer.CustomerId == customer_id).one_or_none()

#     # Calling SP to send SMS
#     if alert_code == 'JFSL_GARMENT_PICKUP_FABRICSPA':
#         query = f"""EXEC {ALERT_ENGINE_DB}..ALERT_PROCESS @ALERT_CODE = '{alert_code}'
#                                              ,@EMAIL_ID = NULL
#                                              ,@MOBILE_NO = {customer_details.MobileNo}
#                                              ,@SUBJECT = NULL
#                                              ,@DISPATCH_FLAG = 'OFF'
#                                              ,@EMAIL_SENDER_ADD = NULL
#                                              ,@SMS_SENDER_ADD = NULL
#                                              ,@P1 = '{date_time_slot}'
#                                              ,@P2 = {booking_id}
#                                              ,@P3 = '1800-123-4664'
#                                              ,@P4 = 'FABRICSPA'
#                                              ,@P5 = {customer_details.CustomerName} ,@P6 =  'or Click here 
#                                              https://fabspa.in/app' ,@P7 = NULL ,@P8 = NULL ,@P9 = NULL ,@P10 = NULL 
#                                              ,@P11 = NULL ,@P12 = NULL ,@P13 = NULL ,@P14 = NULL ,@P15 = NULL , 
#                                              @P16 = NULL ,@P17 = NULL ,@P18 = NULL ,@P19 = NULL ,@P20 = NULL , 
#                                              @REC_ID = '0' """

#     # Calling SP to send whatsapp message
#     elif alert_code == 'pickup_scheduled':
#         query = f"""EXEC {ALERT_ENGINE_DB}..ALERT_PROCESS @ALERT_CODE = {'pickup_scheduled'}
#                                          ,@EMAIL_ID = NULL
#                                          ,@MOBILE_NO = {customer_details.MobileNo}
#                                          ,@SUBJECT = NULL
#                                          ,@DISPATCH_FLAG = 'OFF'
#                                          ,@EMAIL_SENDER_ADD = NULL
#                                          ,@SMS_SENDER_ADD = NULL
#                                          ,@P1 = {str(91) + customer_details.MobileNo}
#                                          ,@P2 = {customer_details.CustomerName}
#                                          ,@P3 = '{date_time_slot}'
#                                          ,@P4 = {booking_id} ,@P5 = NULL ,@P6 =  NULL ,@P7 = NULL ,@P8 = NULL ,@P9 = 
#                                          NULL ,@P10 = NULL ,@P11 = NULL ,@P12 = NULL ,@P13 = NULL ,@P14 = NULL ,
#                                          @P15 = NULL ,@P16 = NULL ,@P17 = NULL ,@P18 = NULL ,@P19 = NULL ,@P20 = NULL 
#                                          ,@REC_ID = '0' """

#     db.engine.execute(text(query).execution_options(autocommit=True))


def trigger_sms_after_pickup( alert_code,MobileNumber, CustomerName, BookingID, date_time_slot):
    """
    Function for send SMS via SP after adhoc pickup for future date
    """
    query = None
    # Getting customer details from DB
    

    # Calling SP to send SMS
    if alert_code == 'JFSL_GARMENT_PICKUP_FABRICSPA':


        # query = f"""EXEC {ALERT_ENGINE_DB}..ALERT_PROCESS @ALERT_CODE = '{alert_code}'
        #                                      ,@EMAIL_ID = NULL
        #                                      ,@MOBILE_NO = '{customer_details.MobileNo}'
        #                                      ,@SUBJECT = NULL
        #                                      ,@DISPATCH_FLAG = 'OFF'
        #                                      ,@EMAIL_SENDER_ADD = NULL
        #                                      ,@SMS_SENDER_ADD = NULL
        #                                      ,@P1 = '{date_time_slot}'
        #                                      ,@P2 = '{booking_id}'
        #                                      ,@P3 = '1800-123-4664'
        #                                      ,@P4 = 'FABRICSPA'
        #                                      ,@P5 = '{customer_details.CustomerName}' ,@P6 =  'or Click here 
        #                                      https://fabspa.in/app' ,@P7 = NULL ,@P8 = NULL ,@P9 = NULL ,@P10 = NULL 
        #                                      ,@P11 = NULL ,@P12 = NULL ,@P13 = NULL ,@P14 = NULL ,@P15 = NULL , 
        #                                      @P16 = NULL ,@P17 = NULL ,@P18 = NULL ,@P19 = NULL ,@P20 = NULL , 
        #                                      @REC_ID = '0' """
        query = f"""EXEC {ALERT_ENGINE_DB}..ALERT_PROCESS @ALERT_CODE = '{alert_code}', @EMAIL_ID = NULL, @MOBILE_NO = '{MobileNumber}', @SUBJECT = NULL, @DISPATCH_FLAG = 'OFF', @EMAIL_SENDER_ADD = NULL, @SMS_SENDER_ADD = NULL, @P1 = '{date_time_slot}', @P2 = '{BookingID}', @P3 = '1800-123-4664', @P4 = 'FABRICSPA', @P5 = '{CustomerName}', @P6 = 'or Click here https://fabspa.in/app', @P7 = NULL, @P8 = NULL, @P9 = NULL, @P10 = NULL, @P11 = NULL, @P12 = NULL, @P13 = NULL, @P14 = NULL, @P15 = NULL, @P16 = NULL, @P17 = NULL, @P18 = NULL, @P19 = NULL, @P20 = NULL, @REC_ID = '0';""".replace('\n', ' ')



        log_data = {
            'trigger_sms_after_pickupsms12 :': query
        }
        info_logger(f'Route: {request.path}').info(json.dumps(log_data))

    # Calling SP to send whatsapp message
    elif alert_code == 'pickup_scheduled':
        query = f"""EXEC {ALERT_ENGINE_DB}..ALERT_PROCESS @ALERT_CODE = {'pickup_scheduled'}
                                         ,@EMAIL_ID = NULL
                                         ,@MOBILE_NO = '{MobileNumber}'
                                         ,@SUBJECT = NULL
                                         ,@DISPATCH_FLAG = 'OFF'
                                         ,@EMAIL_SENDER_ADD = NULL
                                         ,@SMS_SENDER_ADD = NULL
                                         ,@P1 = '{str(91) + MobileNumber}'
                                         ,@P2 = '{CustomerName}'
                                         ,@P3 = '{date_time_slot}'
                                         ,@P4 = '{BookingID}' ,@P5 = NULL ,@P6 =  NULL ,@P7 = NULL ,@P8 = NULL ,@P9 = 
                                         NULL ,@P10 = NULL ,@P11 = NULL ,@P12 = NULL ,@P13 = NULL ,@P14 = NULL ,
                                         @P15 = NULL ,@P16 = NULL ,@P17 = NULL ,@P18 = NULL ,@P19 = NULL ,@P20 = NULL 
                                         ,@REC_ID = '0' """
        log_data = {
            'trigger_sms_after_pickupsms2 :': query
        }
        info_logger(f'Route: {request.path}').info(json.dumps(log_data))

    result_proxy = db.engine.execute(text(query).execution_options(autocommit=True))
    response = result_proxy.fetchall()
    response_data = [dict(row) for row in response]
    log_data = {
        'trigger_sms_after_pickupsms result  :': 'Success',
        'trigger_sms_after_pickupsms2':response_data
    }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))




def send_sms_after_activity(customer_id, delivery_request_id, date_or_egrn, activity_id_or_amount,
                            time_frame_or_invoice_no, activity):
    """
    Function for sending SMS after a successful delivery  using Ice Cubes Transactional SMS service.
    """
    # if activity is pickup activity_id will booking id , if delivery order_id
    # if pickup date_or_egrn will rescheduled date, if delivery egrn

    try:
        message = ''
        # Getting customer details from DB
        customer_details = db.session.query(Customer.CustomerName, Customer.MobileNo, Customer.MonthlyCustomer).filter(
            Customer.CustomerId == customer_id).one_or_none()

        if activity == 'DELIVERY':
            # Check if the garments are explicitly selected for delivery or not.
            delivery_garments_count = db.session.query(func.count(DeliveryGarment.DeliveryGarmentId)).filter(
                DeliveryGarment.DeliveryRequestId == delivery_request_id, DeliveryGarment.IsDeleted == 0).scalar()

            if delivery_garments_count == 0:
                # This is not a partial delivery. Get the count from the OrderGarments table itself.
                delivery_garments_count = db.session.query(func.count(OrderGarment.OrderGarmentId)).filter(
                    OrderGarment.OrderId == activity_id_or_amount, OrderGarment.GarmentStatusId == 11,
                    OrderGarment.IsDeleted == 0).scalar()

            if customer_details.MonthlyCustomer:
                # Making a text to send via SMS
                message = f"Hi {customer_details.CustomerName}, Your {str(delivery_garments_count)} garment(s) with order number {date_or_egrn} from fabricspa is delivered on {datetime.today().strftime('%d-%m-%Y')}. For any query reach us on 18001234664"

            else:
                txn_details = db.session.query(TransactionInfo.TransactionId,
                                               TransactionInfo.TotalPayableAmount).filter(
                    TransactionInfo.EGRNNo == date_or_egrn).first()

                if txn_details and txn_details.TransactionId is not None:

                    time_frame_or_invoice_no = db.session.query(TransactionPaymentInfo.InvoiceNo).filter(
                        TransactionPaymentInfo.TransactionId == txn_details.TransactionId).first()

                    if time_frame_or_invoice_no is not None and time_frame_or_invoice_no.InvoiceNo is not None:
                        invoice_link = invoice_link_shortening(time_frame_or_invoice_no.InvoiceNo)

                        message = f"Hi {customer_details.CustomerName}, payment of Rs.{str(txn_details.TotalPayableAmount)}/- for {str(delivery_garments_count)} garments against order No. {date_or_egrn} at fabricspa has been successful. Click here {invoice_link} to view your Invoice copy."

        if activity == 'RESCHEDULE_PICKUP':
            # Making text to send via SMS
            message = f"Hi {customer_details.CustomerName}, your pickup with booking ID {activity_id_or_amount}  is rescheduled for {date_or_egrn} {time_frame_or_invoice_no}. For any changes call 18001234664  / Click here https://fabspa.in/app to download the app."

        if activity == 'FUTURE_ADHOC':
            message = f"Hi {customer_details.CustomerName}, you have scheduled a pickup on {date_or_egrn} {time_frame_or_invoice_no} and your booking ID is {activity_id_or_amount}. For any changes, call 080-46644664  or Click here https://fabspa.in/app ."

        if message != "":
            send_sms_via_ice_cube(customer_details.MobileNo, message)

    except Exception as e:
        error_logger(f'Delivery Blueprint Queries: {inspect.stack()[0].function}()').error(e)


def add_hanger(order_id, order_garment_id):
    """
    Function for adding hanger instruction if there is default hanger presents
    """
    new_instruction = OrderInstruction(OrderId=order_id,
                                       OrderGarmentId=order_garment_id,
                                       InstructionId=12, IsDeleted=0
                                       )
    try:
        db.session.add(new_instruction)
        db.session.commit()
    except Exception as e:
        error_logger(f'Delivery Blueprint Queries: {inspect.stack()[0].function}()').error(e)


def check_monthly_customer(customer_code):
    """
    Function for checking whether the customer is monthly customer or not
    :param customer_code:
    :return:
    """
    # Getting details from DB
    customer = db.session.query(Customer.MonthlyCustomer).filter(Customer.CustomerCode == customer_code,
                                                                 Customer.IsDeleted == 0,
                                                                 Customer.IsActive == 1).one_or_none()

    return False if customer.MonthlyCustomer is None else customer.MonthlyCustomer


# def send_sms_email_when_settled(customer_code, egrn, amount, invoice_num):
#     """
#     Function for sending sms with invoice link
#     @param customer_code:
#     @param egrn:
#     @param amount:
#     @param invoice_num:
#     @return:
#     """
#     customer_details = db.session.query(Customer.EmailId, Customer.MobileNo, Customer.CustomerName).filter(
#         Customer.CustomerCode == customer_code).one_or_none()

#     # Shortened Link generation is successful.
#     invoice_link = invoice_link_shortening(invoice_num)
#     formatted_invoice_link = f'Click here {invoice_link} to view your Invoice copy.'

#     query = f"EXEC {ALERT_ENGINE_DB}..ALERT_PROCESS @ALERT_CODE = 'JFSL_DELIVERY_COMPLETED_FABRICSPA', @EMAIL_ID = '{customer_details.EmailId}', @MOBILE_NO = '{customer_details.MobileNo}', @SUBJECT = NULL, @DISPATCH_FLAG = 'OFF', @EMAIL_SENDER_ADD = NULL, @SMS_SENDER_ADD = 'FABSPA', @P1 = '{egrn}', @P2 = NULL, @P3 = '{customer_details.CustomerName}', @P4 = '080 46644664', @P5 = 'SERVICE', @P6 = '{amount}', @P7 = NULL, @P8 = '{amount}', @P9 = '{formatted_invoice_link}', @P10 = NULL, @P11 = NULL, @P12 = '{invoice_num}', @P13 = NULL, @P14 = NULL, @P15 = NULL, @P16 = NULL, @P17 = NULL, @P18 = NULL, @P19 = NULL, @P20 = NULL, @REC_ID = '0' "
#     # Executing SP
#     CallSP(query).execute()

def send_sms_email_when_settled_before_zero(customer_code, egrn, amount, invoice_num):
    """
    Function for sending sms with invoice link
    @param customer_code:
    @param egrn:
    @param amount:
    @param invoice_num:
    @return:
    """
    try:
        # invoice_generate_result = invoice_generate(invoice_num)
        # log_data = {
        #     'invoice_generate_result': 'invoice_generate_result'
        # }
        # info_logger(f'Route: {request.path}').info(json.dumps(log_data))

        amount_type = type(amount)
        log_data = {
            'amount_type': str(amount_type)

        }
        info_logger(f'Route: {request.path}').info(json.dumps(log_data))
        customer_details = db.session.query(Customer.EmailId, Customer.MobileNo, Customer.CustomerName).filter(
            Customer.CustomerCode == customer_code).one_or_none()
        log_data = {
            'sms_check': 'txt1',

        }
        info_logger(f'Route: {request.path}').info(json.dumps(log_data))

        # Shortened Link generation is successful.
        # invoice_link = invoice_link_shortening(invoice_num)
        # formatted_invoice_link = f'Click here {invoice_link} to view your Invoice copy.'
        formatted_invoice_link = None
        invoice_link = None

        sender = "FABSPA"
        if egrn is not None:
            query = f"EXEC CustomerApp.[dbo].[GetBrandName] @BranchCode='NULL', @EGRNNo={egrn}, @PickupRequestId=NULL"
            brand_details = CallSP(query).execute().fetchone()
            log_data = {
                'query of brand': query,
                'result of brand': brand_details if brand_details else "No results"
            }
            info_logger(f'Route: {request.path}').info(json.dumps(log_data))

            #brand_details["BrandDescription"] ="QUICLO"

            if brand_details and brand_details["BrandDescription"] != 'FABRICSPA':
                sender = "QUICLO"
                # Shortened Link generation is successful.
                payment_link = invoice_link_shortening(invoice_num)

                InvoiceNo = invoice_num
                sp_query = f"EXEC JFSL.dbo.GenerateUniqueCombination @longurl='{payment_link}', @Source='Fabxpress', @brand='{sender}', @DocumentType='Invoice', @DocumentNo='{InvoiceNo}'"
                log_data = {
                    'query of links': sp_query
                }
                info_logger(f'Route: {request.path}').info(json.dumps(log_data))
                sp_result = CallSP(sp_query).execute().fetchone()

                log_data = {
                    'query of link': sp_query,
                    'result of link': sp_result
                }
                info_logger(f'Route: {request.path}').info(json.dumps(log_data))

                if sp_result:
                    # payment_link = sp_result
                    invoice_link = sp_result.get('GeneratedCombination')
                    log_data = {
                        'payment_link': invoice_link,

                    }
                    info_logger(f'Route: {request.path}').info(json.dumps(log_data))
                formatted_invoice_link = f'Click here {invoice_link} to view your Invoice copy.'

            else:
                # Shortened Link generation is successful.
                invoice_link = invoice_link_shortening(invoice_num)
                formatted_invoice_link = f'Click here {invoice_link} to view your Invoice copy.'
                sender = "FABSPA"
        try:

            query = f"EXEC {ALERT_ENGINE_DB}..ALERT_PROCESS @ALERT_CODE = 'JFSL_DELIVERY_COMPLETED_FABRICSPA', @EMAIL_ID = '{customer_details.EmailId}', @MOBILE_NO = '{customer_details.MobileNo}', @SUBJECT = NULL, @DISPATCH_FLAG = 'OFF', @EMAIL_SENDER_ADD = NULL, @SMS_SENDER_ADD = 'FABSPA', @P1 = '{egrn}', @P2 = NULL, @P3 = '{customer_details.CustomerName}', @P4 = '080 46644664', @P5 = 'SERVICE', @P6 = '{amount}', @P7 = NULL, @P8 = '{amount}', @P9 = '{formatted_invoice_link}', @P10 = NULL, @P11 = NULL, @P12 = '{invoice_num}', @P13 = NULL, @P14 = NULL, @P15 = NULL, @P16 = NULL, @P17 = NULL, @P18 = NULL, @P19 = NULL, @P20 = NULL, @REC_ID = '0' "
            log_data = {
                'sms_invoice_sp :': query
            }
            info_logger(f'Route: {request.path}').info(json.dumps(log_data))
            # Executing SP
            result = CallSP(query).execute()
            # CallSP(query).execute()
            # result1 = result.fetchone()
            log_data = {
                'sms_invoice :': query,
                # 'response': result1 if result1 else 'No data returned from SP'
            }
            info_logger(f'Route: {request.path}').info(json.dumps(log_data))
        except Exception as e:
            error_logger(f'Route: {request.path}').error(e)

    except Exception as e:
        error_logger(f'Route: {request.path}').error(e)
        log_data = {
            'sms_invoiceExc :': query
        }
        info_logger(f'Route: {request.path}').info(json.dumps(log_data))

def send_sms_email_when_settled_live(customer_code, egrn, amount, invoice_num):
    """
    Function for sending SMS with invoice link.
    :param customer_code: str
    :param egrn: str
    :param amount: float
    :param invoice_num: str
    :return: None
    """
    e = None
    try:
        amount_type = type(amount)
        log_data = {
            'amount_type': str(amount_type)

        }
        info_logger(f'Route: {request.path}').info(json.dumps(log_data))

        # Fetch customer details
        customer_details = db.session.query(
            Customer.EmailId, Customer.MobileNo, Customer.CustomerName, Customer.CustomerId
        ).filter(
            Customer.CustomerCode == customer_code,
            Customer.IsDeleted == 0,
            Customer.IsActive == 1
        ).one_or_none()

        log_data = {
            'sms_check': 'txt1',

        }
        info_logger(f'Route: {request.path}').info(json.dumps(log_data))

        sender = "FABSPA"
        header = "fabricspa"
        formatted_invoice_link = None

        if egrn:
            # Fetch brand details
            if egrn is not None:
                query = f"EXEC CustomerApp.[dbo].[GetBrandName] @BranchCode='NULL', @EGRNNo={egrn}, @PickupRequestId=NULL"
                brand_details = CallSP(query).execute().fetchone()
                log_data = {
                    'query of brand': query,
                    'result of brand': brand_details if brand_details else "No results"
                }
                info_logger(f'Route: {request.path}').info(json.dumps(log_data))

                if brand_details and brand_details.get("BrandDescription") == "QUICLO":
                    sender = "QUICLO"
                    header = "Quiclo"
                    payment_link = invoice_link_shortening(invoice_num)

                    InvoiceNo = invoice_num
                    sp_query = f"EXEC JFSL.dbo.GenerateUniqueCombination @longurl='{payment_link}', @Source='Fabxpress', @brand='{sender}', @DocumentType='Invoice', @DocumentNo='{InvoiceNo}'"
                    log_data = {
                        'query of links': sp_query
                    }
                    info_logger(f'Route: {request.path}').info(json.dumps(log_data))
                    sp_result = CallSP(sp_query).execute().fetchone()

                    log_data = {
                        'query of link': sp_query,
                        'result of link': sp_result
                    }
                    info_logger(f'Route: {request.path}').info(json.dumps(log_data))

                    if sp_result:
                        # payment_link = sp_result
                        invoice_link = sp_result.get('GeneratedCombination')
                        log_data = {
                            'payment_link': invoice_link,

                        }
                        info_logger(f'Route: {request.path}').info(json.dumps(log_data))
                    formatted_invoice_link = f'Click here {invoice_link} to view your Invoice copy.'

                else:
                    # Shortened Link generation is successful.
                    invoice_link = invoice_link_shortening(invoice_num)
                    formatted_invoice_link = f'Click here {invoice_link} to view your Invoice copy.'
                    sender = "FABSPA"
                    header = "fabricspa"
                log_data = {
                    'sender': sender,
                }
                info_logger(f'Route: {request.path}').info(json.dumps(log_data))

                if amount == 0.0:

                    # message = f'Dear customer, your garment(s) against order no. {egrn} at {sender}  is settled successfully. click here {payment_link} to ' \
                    #         to view your Invoice copy.'
                    message = (
                        f"Dear customer, your garment(s) against order no. {egrn} at {header} is settled for the zero value."
                        f" Click here {invoice_link} to view your invoice copy."
                    )

                   

                    sms = send_sms_laundry(customer_details.MobileNo, message, customer_details.CustomerId, sender)

                    # if sms['result']:
                    #     if sms['result'].get('status') == "OK":
                    #         send_status = True
                else:

                    query = f"EXEC {ALERT_ENGINE_DB}..ALERT_PROCESS @ALERT_CODE = 'JFSL_DELIVERY_COMPLETED_FABRICSPA', @EMAIL_ID = '{customer_details.EmailId}', @MOBILE_NO = '{customer_details.MobileNo}', @SUBJECT = NULL, @DISPATCH_FLAG = 'OFF', @EMAIL_SENDER_ADD = NULL, @SMS_SENDER_ADD = '{sender}', @P1 = '{egrn}', @P2 = NULL, @P3 = '{customer_details.CustomerName}', @P4 = '080 46644664', @P5 = 'SERVICE', @P6 = '{amount}', @P7 = NULL, @P8 = '{amount}', @P9 = '{formatted_invoice_link}', @P10 = NULL, @P11 = NULL, @P12 = '{invoice_num}', @P13 = NULL, @P14 = NULL, @P15 = NULL, @P16 = NULL, @P17 = NULL, @P18 = NULL, @P19 = NULL, @P20 = NULL, @REC_ID = '0' "
                    # query = f"""EXEC JFSL..[ZeroValueSettlementSMSTrigger] @ALERT_CODE ='JFSL_DELIVERY_COMPLETED_FABRICSPA',@EMAIL_ID = '{customer_details.EmailId}',@MOBILE_NO ='{customer_details.MobileNo}' , @SUBJECT = NULL, @DISPATCH_FLAG ='OFF', @EMAIL_SENDER_ADD = NULL, @SMS_SENDER_ADD ='{sender}', @P1 = '{egrn}', @P2 = NULL, @P3 = '{customer_details.CustomerName}', @P4 = '080 46644664', @P5 = 'SERVICE', @P6 = NULL, @P7 = NULL, @P8 =NULL, @P9 = '{formatted_invoice_link}', @P10 = NULL, @P11 = NULL, @P12 = '{invoice_num}', @P13 = NULL, @P14 = NULL, @P15 = NULL, @P16 = NULL, @P17 = NULL, @P18 = NULL, @P19 = NULL, @P20 = NULL, @REC_ID  ='0' """
                    log_data = {
                        'sms_invoice_sp :': query
                    }
                    info_logger(f'Route: {request.path}').info(json.dumps(log_data))

                    try:
                        result = CallSP(query).execute().fetchall()

                        log_data = {
                            'sms_invoice :': query,
                            'response': result
                        }
                        info_logger(f'Route: {request.path}').info(json.dumps(log_data))
                    except Exception as e:
                        error_logger(f'Route: {request.path}').error(e)

    except Exception as e:
        error_logger(f'Route: {request.path}').error(e)

# def send_sms_email_when_settled(customer_code, egrn, amount, invoice_num):
#     """
#     Function for sending SMS with invoice link.
#     :param customer_code: str
#     :param egrn: str
#     :param amount: float
#     :param invoice_num: str
#     :return: None
#     """
#     e = None
#     try:
#         amount_type = type(amount)
#         log_data = {
#             'amount_type': str(amount_type)

#         }
#         info_logger(f'Route: {request.path}').info(json.dumps(log_data))

#         # Fetch customer details
#         # customer_details = db.session.execute(
#         #     text(
#         #         "SELECT * FROM JFSL.dbo.CustomerInfo WHERE CustomerCode = :customer_code"),
#         #     {"CustomerCode": customer_code}
#         # ).fetchone()
#         log_data = {
#             'sms_check': customer_code,

#         }
#         info_logger(f'Route: {request.path}').info(json.dumps(log_data))

#         customer_details = db.session.execute(
#             text("SELECT * FROM JFSL.dbo.CustomerInfo WHERE CustomerCode = :customer_code"),
#             {"customer_code": customer_code}
#         ).fetchone()

#         log_data = {
#             'sms_check': 'test',

#         }
#         info_logger(f'Route: {request.path}').info(json.dumps(log_data))

#         log_data = {
#             'customer_detail_keys': list(customer_details.keys())

#         }
#         info_logger(f'Route: {request.path}').info(json.dumps(log_data))

#         sender = "FABSPA"
#         header = "fabricspa"
#         formatted_invoice_link = None

#         if egrn:
#             # Fetch brand details
#             if egrn is not None:
#                 query = f"EXEC CustomerApp.[dbo].[GetBrandName] @BranchCode='NULL', @EGRNNo={egrn}, @PickupRequestId=NULL"
#                 brand_details = CallSP(query).execute().fetchone()
#                 log_data = {
#                     'query of brand': query,
#                     'result of brand': brand_details if brand_details else "No results"
#                 }
#                 info_logger(f'Route: {request.path}').info(json.dumps(log_data))

#                 if brand_details and brand_details.get("BrandDescription") == "QUICLO":
#                     sender = "QUICLO"
#                     header = "Quiclo"
#                     payment_link = invoice_link_shortening(invoice_num)

#                     InvoiceNo = invoice_num
#                     sp_query = f"EXEC JFSL.dbo.GenerateUniqueCombination @longurl='{payment_link}', @Source='Fabxpress', @brand='{sender}', @DocumentType='Invoice', @DocumentNo='{InvoiceNo}'"
#                     log_data = {
#                         'query of links': sp_query
#                     }
#                     info_logger(f'Route: {request.path}').info(json.dumps(log_data))
#                     sp_result = CallSP(sp_query).execute().fetchone()

#                     log_data = {
#                         'query of link': sp_query,
#                         'result of link': sp_result
#                     }
#                     info_logger(f'Route: {request.path}').info(json.dumps(log_data))

#                     if sp_result:
#                         # payment_link = sp_result
#                         invoice_link = sp_result.get('GeneratedCombination')
#                         log_data = {
#                             'payment_link': invoice_link,

#                         }
#                         info_logger(f'Route: {request.path}').info(json.dumps(log_data))
#                     formatted_invoice_link = f'Click here {invoice_link} to view your Invoice copy.'

#                 else:
#                     # Shortened Link generation is successful.
#                     invoice_link = invoice_link_shortening(invoice_num)
#                     formatted_invoice_link = f'Click here {invoice_link} to view your Invoice copy.'
#                     sender = "FABSPA"
#                     header = "fabricspa"
#                 log_data = {
#                     'sender': sender,
#                 }
#                 info_logger(f'Route: {request.path}').info(json.dumps(log_data))

#                 if amount == 0.0:

#                     # message = f'Dear customer, your garment(s) against order no. {egrn} at {sender}  is settled successfully. click here {payment_link} to ' \
#                     #         to view your Invoice copy.'
#                     message = (
#                         f"Dear customer, your garment(s) against order no. {egrn} at {header} is settled for the zero value."
#                         f" Click here {invoice_link} to view your invoice copy."
#                     )

#                     log_data = {
#                         'customer_id': customer_details.CustomerCode
#                     }
#                     info_logger(f'Route: {request.path}').info(json.dumps(log_data))
#                     customer_details["CustomerCode"] = 0

#                     #sms = send_sms_laundry(customer_details.ContactNo, message, customer_details.CustomerCode, sender)
#                     sms = send_sms_laundry(customer_details["ContactNo"], message, customer_details["CustomerCode"], sender)

#                     # if sms['result']:
#                     #     if sms['result'].get('status') == "OK":
#                     #         send_status = True
#                 else:

#                     #query = f"EXEC {ALERT_ENGINE_DB}..ALERT_PROCESS @ALERT_CODE = 'JFSL_DELIVERY_COMPLETED_FABRICSPA', @EMAIL_ID = '{customer_details["EmailID1"]}', @MOBILE_NO = '{customer_details["ContactNo"]}', @SUBJECT = NULL, @DISPATCH_FLAG = 'OFF', @EMAIL_SENDER_ADD = NULL, @SMS_SENDER_ADD = '{sender}', @P1 = '{egrn}', @P2 = NULL, @P3 = '{customer_details["FirstName"]}', @P4 = '080 46644664', @P5 = 'SERVICE', @P6 = '{amount}', @P7 = NULL, @P8 = '{amount}', @P9 = '{formatted_invoice_link}', @P10 = NULL, @P11 = NULL, @P12 = '{invoice_num}', @P13 = NULL, @P14 = NULL, @P15 = NULL, @P16 = NULL, @P17 = NULL, @P18 = NULL, @P19 = NULL, @P20 = NULL, @REC_ID = '0' "
#                     # query = f"""EXEC JFSL..[ZeroValueSettlementSMSTrigger] @ALERT_CODE ='JFSL_DELIVERY_COMPLETED_FABRICSPA',@EMAIL_ID = '{customer_details.EmailId}',@MOBILE_NO ='{customer_details.MobileNo}' , @SUBJECT = NULL, @DISPATCH_FLAG ='OFF', @EMAIL_SENDER_ADD = NULL, @SMS_SENDER_ADD ='{sender}', @P1 = '{egrn}', @P2 = NULL, @P3 = '{customer_details.CustomerName}', @P4 = '080 46644664', @P5 = 'SERVICE', @P6 = NULL, @P7 = NULL, @P8 =NULL, @P9 = '{formatted_invoice_link}', @P10 = NULL, @P11 = NULL, @P12 = '{invoice_num}', @P13 = NULL, @P14 = NULL, @P15 = NULL, @P16 = NULL, @P17 = NULL, @P18 = NULL, @P19 = NULL, @P20 = NULL, @REC_ID  ='0' """
#                     #query = f"EXEC {ALERT_ENGINE_DB}..ALERT_PROCESS @ALERT_CODE = 'JFSL_DELIVERY_COMPLETED_FABRICSPA', @EMAIL_ID = '{customer_details.EmailId1}', @MOBILE_NO = '{customer_details.ContactNo}', @SUBJECT = NULL, @DISPATCH_FLAG = 'OFF', @EMAIL_SENDER_ADD = NULL, @SMS_SENDER_ADD = '{sender}', @P1 = '{egrn}', @P2 = NULL, @P3 = '{customer_details.FirstName}', @P4 = '080 46644664', @P5 = 'SERVICE', @P6 = '{amount}', @P7 = NULL, @P8 = '{amount}', @P9 = '{formatted_invoice_link}', @P10 = NULL, @P11 = NULL, @P12 = '{invoice_num}', @P13 = NULL, @P14 = NULL, @P15 = NULL, @P16 = NULL, @P17 = NULL, @P18 = NULL, @P19 = NULL, @P20 = NULL, @REC_ID = '0' "
#                     query = f"EXEC {ALERT_ENGINE_DB}..ALERT_PROCESS @ALERT_CODE = 'JFSL_DELIVERY_COMPLETED_FABRICSPA', @EMAIL_ID = '{customer_details['EmailID1']}', @MOBILE_NO = '{customer_details['ContactNo']}', @SUBJECT = NULL, @DISPATCH_FLAG = 'OFF', @EMAIL_SENDER_ADD = NULL, @SMS_SENDER_ADD = '{sender}', @P1 = '{egrn}', @P2 = NULL, @P3 = '{customer_details['FirstName']}', @P4 = '080 46644664', @P5 = 'SERVICE', @P6 = '{amount}', @P7 = NULL, @P8 = '{amount}', @P9 = '{formatted_invoice_link}', @P10 = NULL, @P11 = NULL, @P12 = '{invoice_num}', @P13 = NULL, @P14 = NULL, @P15 = NULL, @P16 = NULL, @P17 = NULL, @P18 = NULL, @P19 = NULL, @P20 = NULL, @REC_ID = '0'"

#                     log_data = {
#                         'sms_invoice_sp :': query
#                     }
#                     info_logger(f'Route: {request.path}').info(json.dumps(log_data))

#                     try:
#                         result = CallSP(query).execute().fetchall()

#                         log_data = {
#                             'sms_invoice :': query,
#                             'response': result
#                         }
#                         info_logger(f'Route: {request.path}').info(json.dumps(log_data))
#                     except Exception as e:
#                         error_logger(f'Route: {request.path}').error(e)

#     except Exception as e:
#         error_logger(f'Route: {request.path}').error(e)

def send_sms_email_when_settled(customer_code, egrn, amount, invoice_num,TRNNo):
    """
    Function for sending SMS with invoice link.
    :param customer_code: str
    :param egrn: str
    :param amount: float
    :param invoice_num: str
    :return: None
    """
    e = None
    try:
        amount_type = type(amount)
        log_data = {
            'amount_type': str(amount_type)

        }
        info_logger(f'Route: {request.path}').info(json.dumps(log_data))

        # Fetch customer details
        # customer_details = db.session.execute(
        #     text(
        #         "SELECT * FROM JFSL.dbo.CustomerInfo WHERE CustomerCode = :customer_code"),
        #     {"CustomerCode": customer_code}
        # ).fetchone()
        log_data = {
            'sms_check': customer_code,

        }
        info_logger(f'Route: {request.path}').info(json.dumps(log_data))

        customer_details = db.session.execute(
            text("SELECT * FROM JFSL.dbo.CustomerInfo WHERE CustomerCode = :customer_code"),
            {"customer_code": customer_code}
        ).fetchone()

        log_data = {
            'sms_check': 'test',

        }
        info_logger(f'Route: {request.path}').info(json.dumps(log_data))

        log_data = {
            'customer_detail_keys': list(customer_details.keys())

        }
        info_logger(f'Route: {request.path}').info(json.dumps(log_data))

        sender = "FABSPA"
        header = "fabricspa"
        formatted_invoice_link = None

        if egrn:
            # Fetch brand details
            if egrn is not None:
                query = f"EXEC CustomerApp.[dbo].[GetBrandName] @BranchCode='NULL', @EGRNNo={egrn}, @PickupRequestId=NULL"
                brand_details = CallSP(query).execute().fetchone()
                log_data = {
                    'query of brand': query,
                    'result of brand': brand_details if brand_details else "No results"
                }
                info_logger(f'Route: {request.path}').info(json.dumps(log_data))

                if brand_details and brand_details.get("BrandDescription") == "QUICLO":
                    sender = "QUICLO"
                    header = "Quiclo"
                    payment_link = invoice_link_shortening(invoice_num)

                    InvoiceNo = invoice_num
                    sp_query = f"EXEC JFSL.dbo.GenerateUniqueCombination @longurl='{payment_link}', @Source='Fabxpress', @brand='{sender}', @DocumentType='Invoice', @DocumentNo='{InvoiceNo}'"
                    log_data = {
                        'query of links': sp_query
                    }
                    info_logger(f'Route: {request.path}').info(json.dumps(log_data))
                    sp_result = CallSP(sp_query).execute().fetchone()

                    log_data = {
                        'query of link': sp_query,
                        'result of link': sp_result
                    }
                    info_logger(f'Route: {request.path}').info(json.dumps(log_data))

                    if sp_result:
                        # payment_link = sp_result
                        invoice_link = sp_result.get('GeneratedCombination')
                        log_data = {
                            'payment_link': invoice_link,

                        }
                        info_logger(f'Route: {request.path}').info(json.dumps(log_data))
                    formatted_invoice_link = f'Click here {invoice_link} to view your Invoice copy.'

                else:
                    # Shortened Link generation is successful.
                    invoice_link = invoice_link_shortening(invoice_num)
                    formatted_invoice_link = f'Click here {invoice_link} to view your Invoice copy.'
                    sender = "FABSPA"
                    header = "fabricspa"
                log_data = {
                    'sender': sender,
                }
                info_logger(f'Route: {request.path}').info(json.dumps(log_data))

                if amount == 0.0:

                    # message = f'Dear customer, your garment(s) against order no. {egrn} at {sender}  is settled successfully. click here {payment_link} to ' \
                    #         to view your Invoice copy.'
                    message = (
                        f"Dear customer, your garment(s) against order no. {egrn} at {header} is settled for the zero value."
                        f" Click here {invoice_link} to view your invoice copy."
                    )
                    customer_dict = dict(customer_details)

                    log_data = {
                        'customer_id': customer_dict["CustomerCode"]
                    }
                    info_logger(f'Route: {request.path}').info(json.dumps(log_data))
                    #customer_details["CustomerCode"] = 0
                    customer_dict["CustomerCode"] = 0

                    #sms = send_sms_laundry(customer_details.ContactNo, message, customer_details.CustomerCode, sender)
                    sms = send_sms_laundry(customer_details["ContactNo"], message, customer_dict["CustomerCode"], sender)

                    # if sms['result']:
                    #     if sms['result'].get('status') == "OK":
                    #         send_status = True
                else:

                    #query = f"EXEC {ALERT_ENGINE_DB}..ALERT_PROCESS @ALERT_CODE = 'JFSL_DELIVERY_COMPLETED_FABRICSPA', @EMAIL_ID = '{customer_details["EmailID1"]}', @MOBILE_NO = '{customer_details["ContactNo"]}', @SUBJECT = NULL, @DISPATCH_FLAG = 'OFF', @EMAIL_SENDER_ADD = NULL, @SMS_SENDER_ADD = '{sender}', @P1 = '{egrn}', @P2 = NULL, @P3 = '{customer_details["FirstName"]}', @P4 = '080 46644664', @P5 = 'SERVICE', @P6 = '{amount}', @P7 = NULL, @P8 = '{amount}', @P9 = '{formatted_invoice_link}', @P10 = NULL, @P11 = NULL, @P12 = '{invoice_num}', @P13 = NULL, @P14 = NULL, @P15 = NULL, @P16 = NULL, @P17 = NULL, @P18 = NULL, @P19 = NULL, @P20 = NULL, @REC_ID = '0' "
                    # query = f"""EXEC JFSL..[ZeroValueSettlementSMSTrigger] @ALERT_CODE ='JFSL_DELIVERY_COMPLETED_FABRICSPA',@EMAIL_ID = '{customer_details.EmailId}',@MOBILE_NO ='{customer_details.MobileNo}' , @SUBJECT = NULL, @DISPATCH_FLAG ='OFF', @EMAIL_SENDER_ADD = NULL, @SMS_SENDER_ADD ='{sender}', @P1 = '{egrn}', @P2 = NULL, @P3 = '{customer_details.CustomerName}', @P4 = '080 46644664', @P5 = 'SERVICE', @P6 = NULL, @P7 = NULL, @P8 =NULL, @P9 = '{formatted_invoice_link}', @P10 = NULL, @P11 = NULL, @P12 = '{invoice_num}', @P13 = NULL, @P14 = NULL, @P15 = NULL, @P16 = NULL, @P17 = NULL, @P18 = NULL, @P19 = NULL, @P20 = NULL, @REC_ID  ='0' """
                    #query = f"EXEC {ALERT_ENGINE_DB}..ALERT_PROCESS @ALERT_CODE = 'JFSL_DELIVERY_COMPLETED_FABRICSPA', @EMAIL_ID = '{customer_details.EmailId1}', @MOBILE_NO = '{customer_details.ContactNo}', @SUBJECT = NULL, @DISPATCH_FLAG = 'OFF', @EMAIL_SENDER_ADD = NULL, @SMS_SENDER_ADD = '{sender}', @P1 = '{egrn}', @P2 = NULL, @P3 = '{customer_details.FirstName}', @P4 = '080 46644664', @P5 = 'SERVICE', @P6 = '{amount}', @P7 = NULL, @P8 = '{amount}', @P9 = '{formatted_invoice_link}', @P10 = NULL, @P11 = NULL, @P12 = '{invoice_num}', @P13 = NULL, @P14 = NULL, @P15 = NULL, @P16 = NULL, @P17 = NULL, @P18 = NULL, @P19 = NULL, @P20 = NULL, @REC_ID = '0' "
                    query = f"EXEC {ALERT_ENGINE_DB}..ALERT_PROCESS @ALERT_CODE = 'JFSL_DELIVERY_COMPLETED_FABRICSPA', @EMAIL_ID = '{customer_details['EmailID1']}', @MOBILE_NO = '{customer_details['ContactNo']}', @SUBJECT = NULL, @DISPATCH_FLAG = 'OFF', @EMAIL_SENDER_ADD = NULL, @SMS_SENDER_ADD = '{sender}', @P1 = '{egrn}', @P2 = NULL, @P3 = '{customer_details['FirstName']}', @P4 = '080 46644664', @P5 = 'SERVICE', @P6 = '{amount}', @P7 = NULL, @P8 = '{amount}', @P9 = '{formatted_invoice_link}', @P10 = NULL, @P11 = NULL, @P12 = '{invoice_num}', @P13 = NULL, @P14 = NULL, @P15 = NULL, @P16 = NULL, @P17 = NULL, @P18 = NULL, @P19 = NULL, @P20 = NULL, @REC_ID = '0'"

                    log_data = {
                        'sms_invoice_sp :': query
                    }
                    info_logger(f'Route: {request.path}').info(json.dumps(log_data))

                    try:
                        result = CallSP(query).execute().fetchall()

                        log_data = {
                            'sms_invoice :': query,
                            'response': result
                        }
                        info_logger(f'Route: {request.path}').info(json.dumps(log_data))
                    except Exception as e:
                        error_logger(f'Route: {request.path}').error(e)
                # if  sender == "FABSPA" :
                if  sender == "FABSPA" and customer_details['IsOptIn'] == 1:
                    contact_no = customer_details['ContactNo']
                    contact_no = f"+91{contact_no}"
                    user_id = request.headers.get('user-id')
                    query = f""" EXEC JFSL.Dbo.SPPendingDeliveriesDetailedScreen @user_id = {user_id} ,@TRNNo = '{TRNNo}',@TRNNoBasisGarmentsCounts = {1}"""
                    DeliveryGarmentsCount = CallSP(query).execute().fetchone()
                    InvoicedGarments = DeliveryGarmentsCount.get('GarmentsCount')

                    query = f""" 
                      EXEC Alert_Engine..ALERT_PROCESS @ALERT_CODE = 'payment_successful' 

                         ,@EMAIL_ID = '{customer_details['EmailID1']}' 

                         ,@MOBILE_NO = '{customer_details['ContactNo']}' 

                         ,@SUBJECT = NULL 

                         ,@DISPATCH_FLAG = 'OFF' 

                         ,@EMAIL_SENDER_ADD = NULL 

                         ,@SMS_SENDER_ADD = NULL 

                         ,@P1 = '{contact_no}' 

                         ,@P2 = '{customer_details['FirstName']}' 

                         ,@P3 = {amount}    

                         ,@P4 = {InvoicedGarments}   

                         ,@P5 = '{egrn}' 

                         ,@P6 = '{invoice_link}'  

                         ,@P7 = NULL 

                         ,@P8 = NULL 

                         ,@P9 = NULL 

                         ,@P10 = NULL 

                         ,@P11 = NULL 

                         ,@P12 = NULL 

                         ,@P13 = NULL 

                         ,@P14 = NULL 

                         ,@P15 = NULL 

                         ,@P16 = NULL 

                         ,@P17 = NULL 

                         ,@P18 = NULL 

                         ,@P19 = NULL 

                         ,@P20 = NULL 

                         ,@REC_ID = '0' """

                    log_data = {
                            'wps :': query,
                           
                    }
                    info_logger(f'Route: {request.path}').info(json.dumps(log_data))
                    db.engine.execute(text(query).execution_options(autocommit=True))

    except Exception as e:
        error_logger(f'Route: {request.path}').error(e)

def wtsp_notify_on_delivery_reschedule(customer_id, rescheduled_date, egrn):
    """
    Function for notifying the customer when the delivery is rescheduled@P7
    @return:
    """
    # Getting customer details from DB
    customer_details = db.session.query(Customer.IsWhatsAppSubscribed, Customer.MobileNo, Customer.EmailId,
                                        Customer.CustomerName).filter(Customer.CustomerId == customer_id).one_or_none()

    # Checking if customer is subscribes for whatsapp message if yes execute SP
    if customer_details.IsWhatsAppSubscribed:
        query = f"EXEC {ALERT_ENGINE_DB}..ALERT_PROCESS @ALERT_CODE = 'DELIVERY_RESCHEDULE_WHATSAPP',@EMAIL_ID = '{customer_details.EmailId}', @MOBILE_NO = '{customer_details.MobileNo}', @SUBJECT = 'Delivery Is rescheduled', @DISPATCH_FLAG = 'OFF', @EMAIL_SENDER_ADD = 'NULL', @SMS_SENDER_ADD = 'NULL', @P1 = '{customer_details.MobileNo}', @P2 = '{customer_details.CustomerName}', @P3 = '3', @P4 = '{egrn}', @P5 = '{rescheduled_date}', @P6 = '1800-123-4664', @P7 = 'FEEDBACK@FABRICSPA.COM', @P8 = 'NULL', @P9 = 'NULL', @P10 = 'NULL', @P11 = 'NULL', @P12 = 'NULL', @P13 = 'NULL', @P14 = 'NULL', @P15 = 'NULL', @P16 = 'NULL', @P17 = 'NULL', @P18 = 'NULL', @P19 = 'NULL', @P20 = 'NULL', @REC_ID = '0' "
        CallSP(query).execute()

        log_data = {
            'query wtsp_notify_on_delivery_reschedule :': query,
        }
        info_logger(f'Route: {request.path}').info(json.dumps(log_data))


def get_trno_toexpire_paylinlk(trno):
    """
    Function to prevent expiring payment link
    @param trno: trno is the Dcno retrived from get_payable_amount_via_sp
    @return:
    """
    query = f"EXEC {SERVER_DB}.dbo.fabriccarepaymentlink @TRNno='{trno}' "
    CallSP(query).execute()
    log_data = {
        'query get_trno_toexpire_paylinlk :': query,
    }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))


def get_payable_amount_via_sp(customer_code, TRNNo):
    """
    For getting the payable amount through a SP
    @param customer_code: customer_code
    @param order_egrn:
    @return: payable amount
    """
    query = f"EXEC {SERVER_DB}.dbo.SPFabexpressOrderGenerateInvoiceCustApp @customercode='{customer_code}',@TRNNo='{TRNNo}'" 
            

    result = CallSP(query).execute().fetchall()

    log_data = {
        'query of get_payable_amount_via_sp ....... :': query,
        'result of get_payable_amount_via_sp ......... :': result,
    }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))

    for i in result:
        # Populating a dictionary of results from SP
        payable_details = {'DCNO': i['DCNO'], 'ORDERDATE': i['ORDERDATE'], 'PAYABLEAMOUNT': i['PAYABLEAMOUNT'], 'DELIVERYCHARGE': i['DeliveryCharge'], 'IsPreAppliedCoupon': i['IsPreAppliedCoupon']}

        return payable_details


# Edited by MMM
def get_order_garments(order_id, service_tat_id=None):
    """
    For getting all the garments under an order_id.
    @param order_id: 
    @param service_tat_id: 
    @return: List of order garments under a particular Order Id.
    """
    # If the garment can be measured in Sq.ft then return 1, else 0.
    sft_flag = case([(GarmentUOM.UOMName == "SFT", 1), ],
                    else_=0).label("IsSFT")

    query = db.session.query(Garment.GarmentName, OrderGarment.OrderGarmentId, OrderGarment.OrderId,
                             OrderGarment.GarmentId, OrderGarment.ServiceTatId,
                             OrderGarment.ServiceTypeId, GarmentUOM.UOMName, sft_flag, OrderGarment.Length,
                             OrderGarment.Width).join(Garment, OrderGarment.GarmentId == Garment.GarmentId).join(
        GarmentUOM, Garment.UOMId == GarmentUOM.UOMId)

    if service_tat_id is None:
        garment_details = query.filter(
            OrderGarment.OrderId == order_id, OrderGarment.IsDeleted == 0)
    else:
        garment_details = query.filter(
            OrderGarment.OrderId == order_id, OrderGarment.ServiceTatId == service_tat_id,
            OrderGarment.IsDeleted == 0)
    garment_details = garment_details.order_by(OrderGarment.GarmentId.asc()).all()

    return garment_details


def get_pickup_cancel_and_reschedule_reasons():
    """
    For getting predefined pickup reschedule/cancel reasons.
    @return: Dict of reasons.
    """
    cancel_reasons = db.session.query(PickupCancelReason.CancelReason, PickupCancelReason.POSId).filter(
        PickupCancelReason.IsDeleted == 0).all()
    reschedule_reasons = db.session.query(PickupRescheduleReason.RescheduleReason,
                                          PickupRescheduleReason.POSId).filter(
        PickupRescheduleReason.IsDeleted == 0,PickupRescheduleReason.RescheduleReason != 'Change of Branch').all()
    reasons = {'cancel_reasons': cancel_reasons, 'reschedule_reasons': reschedule_reasons}
    return reasons


def get_price_for_garment(garment_id, service_tat_id, service_type_id, branch_code):
    """
    Getting price of a particular garment.
    @param garment_id: GarmentId of that garment.
    @param service_tat_id: ServiceTatId of that garment.
    @param service_type_id: ServiceTypeId of that garment.
    @param branch_code: BranchCode of that order.
    @return: SQL Alchemy ORM result.
    """
    price = db.session.query(PriceList.Price).filter(
        PriceList.GarmentId == garment_id,
        PriceList.ServiceTypeId == service_type_id,
        PriceList.ServiceTatId == service_tat_id,
        PriceList.BranchCode == branch_code,
        PriceList.IsDeleted == 0).one_or_none()
    return price


def update_basic_amount(order_id):
    """
    A function for updating the BasicAmount and ServiceTaxAmount in the Orders table.
    @param order_id:
    @param branch_code:
    """
    log_data = {
        'update_basic_amount': 'query'
    }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))
    try:
        # Getting the sum of order garment amount from the DB.
        basic_order_amount = db.session.query(func.sum(OrderGarment.BasicAmount).label('Sum')).filter(
            OrderGarment.OrderId == order_id, OrderGarment.IsDeleted == 0).one_or_none()
        log_data = {
            'update_basic_amount1': 'query'
        }
        info_logger(f'Route: {request.path}').info(json.dumps(log_data))

        basic_amount = 0 if basic_order_amount.Sum is None else float(basic_order_amount.Sum)

        log_data = {
            'update_basic_amount2': basic_amount
        }
        info_logger(f'Route: {request.path}').info(json.dumps(log_data))

        # Initially discount amount is 0.
        discount_amount = 0

        # Calculating the service tax amount.
        service_tax_amount = (basic_amount - discount_amount) * (18 / 100)

        # Updating the BasicAmount and ServiceTaxAmount in the Orders table.
        try:
            order = db.session.query(Order).filter(Order.OrderId == order_id, Order.IsDeleted == 0).one()
            # Updating the BasicAmount and ServiceTaxAmount
            order.BasicAmount = basic_amount
            order.ServiceTaxAmount = service_tax_amount
            order.RecordLastUpdatedDate = get_current_date()
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            error_logger(f'Delivery Blueprint Queries: {inspect.stack()[0].function}()').error(e)
    except Exception as e:
        error_logger(f'Delivery Blueprint Queries: {inspect.stack()[0].function}()').error(e)


def get_hanger_instruction_id():
    """
    A function to get the hanger instruction id from the GarmentInstructions table.
    @return: instruction id or None if no result is found.
    """
    hanger_instruction_id = None
    try:
        # Getting the hanger instruction id from the DB.
        hanger_instruction = db.session.query(GarmentInstruction.InstructionId).filter(
            GarmentInstruction.InstructionDescription == 'Hanger', GarmentInstruction.IsDeleted == 0).one_or_none()
        hanger_instruction_id = hanger_instruction.InstructionId
    except Exception as e:
        error_logger(f'Delivery Blueprint Queries: {inspect.stack()[0].function}()').error(e)

    return hanger_instruction_id


def get_hanger_instruction_of_order_garment(order_id, order_garment_id, hanger_instruction_id):
    """
    A function to get the hanger instruction of a order garment.
    If no hanger instruction is present, function will return None.
    @return: hanger instruction result or None if no result is found.
    """
    instruction = None
    try:
        instruction = db.session.query(OrderInstruction).filter(OrderInstruction.OrderId == order_id,
                                                                OrderInstruction.OrderGarmentId ==
                                                                order_garment_id,
                                                                OrderInstruction.InstructionId == hanger_instruction_id,
                                                                OrderInstruction.IsDeleted == 0).one_or_none()
    except Exception as e:
        error_logger(f'Delivery Blueprint Queries: {inspect.stack()[0].function}()').error(e)

    return instruction


def get_essential_details_from_dbranchcode(branch_code):
    """
    A function for getting the essential details (Pincode, AreaCode and CityCode) from the delivery user's branch code.
    @param branch_code:
    @return: SQL Alchemy ORM result.
    """
    essential_details = None
    try:
        essential_details = db.session.query(Branch.BranchCode, Branch.Pincode, Branch.AreaCode,
                                             Area.CityCode).join(Area, Branch.AreaCode == Area.AreaCode).filter(
            Branch.BranchCode == branch_code).one_or_none()
    except Exception as e:
        error_logger(f'Delivery Blueprint Queries: {inspect.stack()[0].function}()').error(e)

    return essential_details


def get_essential_details_from_pincode(pin_code):
    """
        A function for getting the essential details (Pincode, AreaCode and CityCode) from the pin code.
        @param pin_code:
        @return: SQL Alchemy ORM result.
        """
    essential_details = None
    try:
        essential_details = db.session.query(Branch.BranchCode, Branch.Pincode, Branch.AreaCode,
                                             Area.CityCode).join(Area, Branch.AreaCode == Area.AreaCode).filter(
            Branch.Pincode == pin_code).one_or_none()
    except Exception as e:
        error_logger(f'Delivery Blueprint Queries: {inspect.stack()[0].function}()').error(e)

    return essential_details


def recalculate_service_tax(order_id):
    """
    Function for recalculating the service tax.
    @param order_id:
    @return:
    """
    try:
        order_details = db.session.query(Order).filter(Order.OrderId == order_id, Order.IsDeleted == 0).one_or_none()

        if order_details is not None:
            basic_amount = float(order_details.BasicAmount)
            discount_amount = float(order_details.Discount)
            # Calculating the service tax amount.
            service_tax_amount = (basic_amount - discount_amount) * (18 / 100)

            try:
                order_details.ServiceTaxAmount = service_tax_amount
                order_details.RecordLastUpdatedDate = get_current_date()
                db.session.commit()
            except Exception as e:
                error_logger(f'Delivery Blueprint Queries: {inspect.stack()[0].function}()').error(e)
    except Exception as e:
        error_logger(f'Delivery Blueprint Queries: {inspect.stack()[0].function}()').error(e)


def divide_discount_to_garments(order_id, discount_amount):
    """
    Function for giving the order garments a share of discount amount.
    Eg: if discount is 100 and garments count is 5, each garment have 20 as discount.
    @return:
    """
    try:
        # Getting the order garment details
        garment_details = db.session.query(OrderGarment).filter(OrderGarment.OrderId == order_id,
                                                                OrderGarment.IsDeleted == 0).all()

        # Getting the total number of active order garments.
        garments_count = db.session.query(func.count(OrderGarment.OrderGarmentId)).filter(
            OrderGarment.OrderId == order_id,
            OrderGarment.IsDeleted == 0).scalar()

        # Calculating the discount amount for each order garment.
        discount_for_a_garment = discount_amount / garments_count

        # Recalculating the service tax of the order garment based on the discount amount.
        service_tax_amount = (OrderGarment.BasicAmount - discount_for_a_garment) * 18 / 100

        try:
            # Saving each garment the discount code.
            for garment in garment_details:
                garment.Discount = discount_for_a_garment
                garment.ServiceTaxAmount = service_tax_amount
                db.session.commit()
        except Exception as e:
            error_logger(f'Delivery Blueprint Queries: {inspect.stack()[0].function}()').error(e)
    except Exception as e:
        error_logger(f'Delivery Blueprint Queries: {inspect.stack()[0].function}()').error(e)


def notify_pos_about_discount(egrn, discount_code):
    """
    Function to call a SP that will notify the POS that the discount amount changes (discount code has been applied from our side.)
    @param egrn: EGRN of the order.
    @param discount_code: Discount code that is applied. eg: SAREESPA.
    @return:
    """
    try:
        query = f"EXEC {SERVER_DB}.dbo.App_UpdateDiscount  @egrn='{egrn}',@DisPromocode='{discount_code}'"
        db.engine.execute(text(query).execution_options(autocommit=True))
        log_data = {
            'App_UpdateDiscount': query
        }
        info_logger(f'Route: {request.path}').info(json.dumps(log_data))
    except Exception as e:
        error_logger(f'Delivery Blueprint Queries: {inspect.stack()[0].function}()').error(e)




def notify_pos_about_coupon(egrn, coupon_code):
    """
    Function to call a SP that will notify the POS that the coupon amount changes (coupon code has been applied from our side.)
    @param egrn: EGRN of the order.
    @param coupon_code: Coupon code that is applied. eg: A compensation coupon.
    @return:
    """
    try:
        query = f"EXEC {SERVER_DB}.dbo.App_UpdateCouponinFabricare @egrn='{egrn}',@CouponCode='{coupon_code}'"
        db.engine.execute(text(query).execution_options(autocommit=True))
    except Exception as e:
        error_logger(f'Delivery Blueprint Queries: {inspect.stack()[0].function}()').error(e)


def notify_pos_about_er_coupon(egrn, discount_code, er_request_id, code_from_er):
    """
    Function to call a SP that will notify the POS that the ER coupon amount changes (ER coupon code has been applied from our side.)
    @param egrn: EGRN of the order.
    @param coupon_code: Coupon code that is applied. eg: A compensation coupon.
    @return:
    """
    try:
        query = f"EXEC {SERVER_DB}.dbo.App_UpdateERCouponCodeinFabricare @egrn='{egrn}',@DisPromocode='{discount_code}',@ERRequestID='{er_request_id}',@ERCouponCode='{code_from_er}'"
        db.engine.execute(text(query).execution_options(autocommit=True))
    except Exception as e:
        error_logger(f'Delivery Blueprint Queries: {inspect.stack()[0].function}()').error(e)


def get_est_delivery_date(order_garment_id):
    """
    Query to find out the estimated delivery date of a garment.
    @param order_garment_id:
    @return: Delivery date in date format.
    """
    # Initially, the current date will be the delivery date.
    est_delivery_date = datetime.today().strftime("%Y-%m-%d 00:00:00")
    est_delivery_date = datetime.strptime(est_delivery_date, "%Y-%m-%d 00:00:00")
    try:
        garment_details = db.session.query(OrderGarment.GarmentId, OrderGarment.ServiceTatId,
                                           OrderGarment.ServiceTypeId, Order.BranchCode).join(Order,
                                                                                              OrderGarment.OrderId == Order.OrderId).filter(
            OrderGarment.OrderGarmentId == order_garment_id, OrderGarment.IsDeleted == 0).one_or_none()

        address_essentials = db.session.query(City.StateCode, OrderGarment.OrderGarmentId,
                                              CustomerAddres.CityCode).join(
            Order,
            OrderGarment.OrderId == Order.OrderId).join(
            CustomerAddres, Order.DeliveryAddressId == CustomerAddres.CustAddressId).join(City,
                                                                                          City.CityCode == CustomerAddres.CityCode).filter(
            OrderGarment.OrderGarmentId == order_garment_id).one_or_none()

        if garment_details is not None:
            garment_id = garment_details.GarmentId
            service_tat_id = garment_details.ServiceTatId
            service_type_id = garment_details.ServiceTypeId
            state_code = address_essentials.StateCode

            branch_code = garment_details.BranchCode

            # Getting the basic day required for service from the DB.
            try:
                delivery_estimator = db.session.query(DeliveryDateEstimator).filter(
                    DeliveryDateEstimator.GarmentId == garment_id,
                    DeliveryDateEstimator.ServiceTypeId == service_type_id,
                    DeliveryDateEstimator.ServiceTatId == service_tat_id,
                    DeliveryDateEstimator.BranchCode == branch_code, DeliveryDateEstimator.IsDeleted == 0).one_or_none()
                log_data = {
                    'delivery_estimator': delivery_estimator.Time,
                }
                info_logger(f'Route: {request.path}').info(json.dumps(log_data))
                if delivery_estimator is not None:
                    # Number of days needed to service.
                    days_require = delivery_estimator.Time
                    # Initial estimated delivery date
                    # Here, Time is the number of days that needed, plus the next day will be
                    # the delivery date.#TODO doubt?
                    est_delivery_date = est_delivery_date + timedelta(days_require)
                    # Days that garment need to take to service this garment.
                    service_days = []
                    day = 1
                    # Appending the days needed to complete the service of garment.
                    while day <= days_require:
                        date = datetime.today() + timedelta(day)
                        service_day = date.strftime('%A')
                        service_days.append(service_day)
                        day += 1

                    days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Friday", "Saturday"]

                    # Getting the MSSWeeklyOff date number from the DB.
                    # If the MSS has an holiday in the service days, one more extra day need to be
                    # added to the delivery date.
                    mss_weekly_off = db.session.query(MSSWeeklyOff).filter(
                        MSSWeeklyOff.StateCode == state_code).one_or_none()
                    if mss_weekly_off is not None:
                        # An MSS weekly off present for that State.
                        weekly_off_number = mss_weekly_off.WeeklyOff
                        weekly_off_day = days[weekly_off_number]

                        if weekly_off_day in service_days:
                            # Here, need to add one more day to the DeliveryDate.
                            # Because the MSS weekly off falls within the service day(s).
                            est_delivery_date = est_delivery_date + timedelta(1)
                            extra_service_day = est_delivery_date.strftime('%A')
                            # Adding  the extra day to the service_days
                            service_days.append(extra_service_day)
                            days_require += 1

                    # Checking whether the delivery date is a weekly off for Branch
                    branch_details = db.session.query(Branch.WeeklyOffDays).filter(
                        Branch.BranchCode == branch_code).one_or_none()

                    if branch_details is not None:
                        if branch_details.WeeklyOffDays is not None:
                            branch_weekly_off_days = ["No holiday", "Sunday", "Monday", "Tuesday", "Wednesday",
                                                      "Friday",
                                                      "Saturday"]

                            branch_weekly_off_day = branch_weekly_off_days[branch_details.WeeklyOffDays]

                            # Check whether the weekly off day in service days or not
                            if branch_weekly_off_day in service_days:
                                # Branch weekly off day is present in the service days.
                                # So the next day will be the delivery date.
                                est_delivery_date = est_delivery_date + timedelta(1)
                                extra_service_day = est_delivery_date.strftime('%A')
                                # Adding  the extra day to the service_days
                                service_days.append(extra_service_day)
                                days_require += 1

            except Exception as e:
                error_logger(f'Delivery Blueprint Queries: {inspect.stack()[0].function}()').error(e)
    except Exception as e:
        error_logger(f'Delivery Blueprint Queries: {inspect.stack()[0].function}()').error(e)
    log_data = {
        'est_delivery_date': str(est_delivery_date)
    }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))
    return est_delivery_date


def update_est_delivery_date(order_garment_id, est_delivery_date):
    """
    Query function for updating the EstDeliveryDate value in the OrderGarments table.
    @param order_garment_id:
    @param est_delivery_date:
    @return:
    """

    try:
        order_garment_details = db.session.query(OrderGarment).filter(
            OrderGarment.OrderGarmentId == order_garment_id).one_or_none()
        log_data = {
            'order_garment_id': order_garment_details.OrderGarmentId,
            'est_delivery_date': str(est_delivery_date),
        }
        info_logger(f'Route: {request.path}').info(json.dumps(log_data))
        if order_garment_details is not None:
            order_garment_details.EstDeliveryDate = est_delivery_date
            order_garment_details.RecordLastUpdatedDate = get_current_date()
            db.session.commit()
            log_data = {
                'order_garment_details id ': order_garment_details.OrderGarmentId,
                'est_delivery_date': str(est_delivery_date),
            }
            info_logger(f'Route: {request.path}').info(json.dumps(log_data))
    except Exception as e:
        db.session.rollback()
        error_logger(f'Delivery Blueprint Queries: {inspect.stack()[0].function}()').error(e)


def set_max_est_delivery_date(order_id):
    """
    Query function to update the EstDeliveryDate of the order, which is the max(EstDeliveryDate)
    of the order garments.
    @param order_id:
    @return:
    """
    try:
        max_date = db.session.query(func.max(OrderGarment.EstDeliveryDate).label('EstDeliveryDate')).filter(
            OrderGarment.OrderId == order_id).one_or_none()
        if max_date is not None:
            order_details = db.session.query(Order).filter(Order.OrderId == order_id,
                                                           Order.IsDeleted == 0).one_or_none()
            if order_details is not None:
                order_details.EstDeliveryDate = max_date.EstDeliveryDate
                order_details.RecordLastUpdatedDate = get_current_date()
                db.session.commit()
    except Exception as e:
        error_logger(f'Delivery Blueprint Queries: {inspect.stack()[0].function}()').error(e)


# Edited by MMM
def get_delivery_branch_of_all(store_user_branches, branch_name, all_users):
    '''
    To get details of delivery user in the aspect of filtering with branch name and
    including inactive users also
    '''
    delivery_users = []
    query = db.session.query(DeliveryUser.DUserId, DeliveryUser.UserName,
                             DeliveryUser.MobileNo,
                             DeliveryUser.EmailId, DeliveryUser.IsActive,
                             DeliveryUser.PartialPaymentPermission).distinct(
        DeliveryUser.UserName,
        DeliveryUser.MobileNo,
        DeliveryUser.EmailId, DeliveryUser.IsActive, DeliveryUser.PartialPaymentPermission).join(
        DeliveryUserBranch,
        DeliveryUserBranch.DUserId == DeliveryUser.DUserId, )

    if branch_name is None:
        print("branch")
        delivery_users = query.filter(
            DeliveryUserBranch.BranchCode.in_(store_user_branches)).all()

    if branch_name is not None:
        delivery_users = query.filter(
            DeliveryUserBranch.BranchCode.in_(store_user_branches), DeliveryUserBranch.BranchCode == branch_name).all()

    if branch_name is not None and all_users is False:
        print("here")
        delivery_users = query.filter(
            DeliveryUserBranch.BranchCode.in_(store_user_branches), DeliveryUserBranch.BranchCode == branch_name,
                                                                    DeliveryUserBranch.IsDeleted == 0)

    return delivery_users


# Edited by MMM

def get_delivery_user_branchname(user_id):
    """
    Function for getting the branch names of delivery users.
    @param user_id:
    @return: list of branch names associated with the user.
    If no branche names are found, empty will be returned.
    """

    # Getting the branch names associated with the delivery user.
    delivery_user_branches = db.session.query(DeliveryUserBranch).join(Branch).filter(
        DeliveryUserBranch.DUserId == user_id, DeliveryUserBranch.IsDeleted == 0).all()

    # Populating the list of branch names.
    branch_names = [delivery_user_branch.Branch.DisplayName for delivery_user_branch in delivery_user_branches]

    return branch_names


# def update_customer_address_in_pos(customer_details, address_details):
#     """
#     Function for updating the POS when a address is updated.
#     @return:
#     """
#     if customer_details['CustomerCode'] is not None:
#         # Here, a customer code is present.
#         gender = 1 if customer_details['Gender'] == 'M' else 2
#         dob = '' if customer_details['DateOfBirth'] is None else customer_details['DateOfBirth']
#         address_line_1 = '' if address_details['AddressLine1'] is None else address_details['AddressLine1'].replace("'",
#                                                                                                                     r"'''")
#         address_line_2 = '' if address_details['AddressLine2'] is None else address_details['AddressLine2'].replace("'",
#                                                                                                                     r"''")
#         address_line_3 = '' if address_details['AddressLine3'] is None else address_details['AddressLine3'].replace("'",
#                                                                                                                     r"''")

#         if address_details['AddressName'] == 'Address 1' or address_details['AddressName'] == 'DeliveryAddress':
#             # Updating the delivery address in the POS.
#             query = f"EXEC {SERVER_DB}.dbo.UPDATEFABRICARECUSTOMERDATA @CUSTOMERCODE='{customer_details['CustomerCode']}',@DOB='{dob}',@EMAIL='{customer_details['EmailId']}',@PROFESSION='{customer_details['Occupation']}',@GENDER='{gender}',@AddressLines1='{address_line_1} {address_line_2} {address_line_3}',@CityCode1='{address_details['CityCode']}',@AreaCode1='{address_details['AreaCode']}',@AddressLines2='',@CityCode2='',@AreaCode2='',@IsAddress2Deleted=0"
#             update_address = f"EXEC {SERVER_DB}.dbo.UpdateCustomerAppAddress @CUSTOMERCODE='{customer_details['CustomerCode']}',@DOB='{dob}',@EMAIL='{customer_details['EmailId']}',@PROFESSION='{customer_details['Occupation']}',@GENDER='{gender}',@AddressLines1='{address_line_1} {address_line_2} {address_line_3}',@CityCode1='{address_details['CityCode']}',@AreaCode1='{address_details['AreaCode']}',@AddressLines2='',@CityCode2='',@AreaCode2='',@IsAddress2Deleted=0 ,@addressname = 'Address 1'"

#         else:
#             # Updating the permanent address in the POS.
#             query = f"EXEC {SERVER_DB}.dbo.UPDATEFABRICARECUSTOMERDATA @CUSTOMERCODE='{customer_details['CustomerCode']}',@DOB='{dob}',@EMAIL='{customer_details['EmailId']}',@PROFESSION='{customer_details['Occupation']}',@GENDER='{gender}',@AddressLines1='',@CityCode1='',@AreaCode1='',@AddressLines2='{address_line_1} {address_line_2} {address_line_3}',@CityCode2='{address_details['CityCode']}',@AreaCode2='{address_details['AreaCode']}',@IsAddress2Deleted=0"
#             update_address = f"EXEC {SERVER_DB}.dbo.UpdateCustomerAppAddress @CUSTOMERCODE='{customer_details['CustomerCode']}',@DOB='{dob}',@EMAIL='{customer_details['EmailId']}',@PROFESSION='{customer_details['Occupation']}',@GENDER='{gender}',@AddressLines1='',@CityCode1='',@AreaCode1='',@AddressLines2='{address_line_1} {address_line_2} {address_line_3}',@CityCode2='{address_details['CityCode']}',@AreaCode2='{address_details['AreaCode']}',@IsAddress2Deleted=0 ,@addressname = 'Address 2'"


#         try:
#             db.engine.execute(text(query).execution_options(autocommit=True))
#             db.engine.execute(text(update_address).execution_options(autocommit=True))

#             log_data = {
#                 'query Updating the delivery address in the POS :': query,
#                 'query Updating the delivery address in the webapp :': update_address
#             }
#             info_logger(f'Route: {request.path}').info(json.dumps(log_data))
#         except Exception as e:
#             error_logger(f'Delivery Blueprint Queries: {inspect.stack()[0].function}()').error(e)
def update_customer_address_in_pos(customer_details, address_details):
    """
    Function for updating the POS when a address is updated.
    @return:
    """
    if customer_details['CustomerCode'] is not None:
        # Here, a customer code is present.
        gender = 1 if customer_details['Gender'] == 'M' else 2
        #dob__date_obj = customer_details['DateOfBirth'].strftime("%Y-%m-%d")
        #dob = '' if customer_details['DateOfBirth'] is None else customer_details['DateOfBirth']        
        #dob = '' if customer_details['DateOfBirth'] is None else dob__date_obj
        dob = '' if customer_details['DateOfBirth'] is None else customer_details['DateOfBirth']

        
        address_line_1 = '' if address_details['AddressLine1'] is None else address_details['AddressLine1'].replace("'",
                                                                                                                    r"'''")
        address_line_2 = '' if address_details['AddressLine2'] is None else address_details['AddressLine2'].replace("'",
                                                                                                                    r"''")
        address_line_3 = '' if address_details['AddressLine3'] is None else address_details['AddressLine3'].replace("'",
                                                                                                                    r"''")

        if address_details['AddressName'] == 'Address 1' or address_details['AddressName'] == 'DeliveryAddress':
            # Updating the delivery address in the POS.
            query = f"EXEC {SERVER_DB}.dbo.UPDATEFABRICARECUSTOMERDATA @CUSTOMERCODE='{customer_details['CustomerCode']}',@DOB='{dob}',@EMAIL='{customer_details['EmailId']}',@PROFESSION='{customer_details['Occupation']}',@GENDER='{gender}',@flatno1='{address_line_1}',@AddressLines1='{address_line_2} {address_line_3}',@CityCode1='{address_details['CityCode']}',@AreaCode1='{address_details['AreaCode']}',@flatno2= NULL,@AddressLines2='',@CityCode2='',@AreaCode2='',@IsAddress2Deleted=0,@lat1 ='{address_details['Lat']}',@long1 ='{address_details['Long']}',@lat2 ='',@long2 ='',@GeoLocality1 ='{address_details['GeoLocality']}',@GeoLocality2 =NULL, @geoPinCode1={address_details['Pincode']}, @geoPinCode2=NULL, @ActiveBranch = {address_details['BranchCode']}"
            update_address = f"EXEC {SERVER_DB}.dbo.UpdateCustomerAppAddress @CUSTOMERCODE='{customer_details['CustomerCode']}',@DOB='{dob}',@EMAIL='{customer_details['EmailId']}',@PROFESSION='{customer_details['Occupation']}',@GENDER='{gender}',@AddressLines1='{address_line_2} {address_line_3}',@CityCode1='{address_details['CityCode']}',@AreaCode1='{address_details['AreaCode']}',@AddressLines2='',@CityCode2='',@AreaCode2='',@IsAddress2Deleted=0 ,@addressname = 'Address 1',@lat1 ='{address_details['Lat']}',@long1 ='{address_details['Long']}',@lat2 ='',@long2 ='',"\
                            f"@geolocality1='{address_details['GeoLocality']}',@geolocality2=NULL,@addresslineforAdd1='{address_line_1}'," \
                            f"@addresslineforAdd2 = NULL, @geoPinCode1={address_details['Pincode']}, @geoPinCode2=NULL"

            # query = f"EXEC {SERVER_DB}.dbo.UPDATEFABRICARECUSTOMERDATAFromFabexpress " \
            #                  f"@CUSTOMERCODE='{customer_details['CustomerCode']}',@flatno1 ='{address_line_1}',@AddressLines1='{address_line_2},{address_line_3}', " \
            #                  f"@CityCode1='{address_details['CityCode']}',@AreaCode1={address_details['AreaCode']}, " \
            #                  f"@pincode1={address_details['Pincode']}," \
            #                  f"@flatno2 = NULL,@AddressLines2=NULL,@CityCode2=NULL," \
            #                  f"@AreaCode2=NULL, @pincode2 = NULL, " \
            #                  f"@IsAddress2Deleted =NULL,@lat1 ='{address_details['Lat']}',@long1 ='{address_details['Long']}',@lat2 ='',@long2 ='',@GeoLocality1 = '{address_details['GeoLocality']}',@GeoLocality2 = NULL"
        else:
            # Updating the permanent address in the POS.
            query = f"EXEC {SERVER_DB}.dbo.UPDATEFABRICARECUSTOMERDATA @CUSTOMERCODE='{customer_details['CustomerCode']}',@DOB='{dob}',@EMAIL='{customer_details['EmailId']}',@PROFESSION='{customer_details['Occupation']}',@GENDER='{gender}',@flatno1=NULL,@AddressLines1='',@CityCode1='',@AreaCode1='',@flatno2='{address_line_1}',@AddressLines2='{address_line_2} {address_line_3}',@CityCode2='{address_details['CityCode']}',@AreaCode2='{address_details['AreaCode']}',@IsAddress2Deleted=0,@lat1 ='',@long1 ='',@lat2 ='{address_details['Lat']}',@long2 ='{address_details['Long']}',@GeoLocality1 = NULL,@GeoLocality2 ='{address_details['GeoLocality']}', @geoPinCode1=NULL, @geoPinCode2={address_details['Pincode']}, @ActiveBranch = {address_details['BranchCode']}"
            update_address = f"EXEC {SERVER_DB}.dbo.UpdateCustomerAppAddress @CUSTOMERCODE='{customer_details['CustomerCode']}',@DOB='{dob}',@EMAIL='{customer_details['EmailId']}',@PROFESSION='{customer_details['Occupation']}',@GENDER='{gender}',@AddressLines1='',@CityCode1='',@AreaCode1='',@AddressLines2='{address_line_2} {address_line_3}',@CityCode2='{address_details['CityCode']}',@AreaCode2='{address_details['AreaCode']}',@IsAddress2Deleted=0 ,@addressname = 'Address 2',@lat1 ='',@long1 ='',@lat2 ='{address_details['Lat']}',@long2 ='{address_details['Long']}',"\
                            f"@geolocality1=NULL,@geolocality2= '{address_details['GeoLocality']}',@addresslineforAdd1=NULL," \
                            f"@addresslineforAdd2 = '{address_line_1}', @geoPinCode1=NULL, @geoPinCode2={address_details['Pincode']}"
            # query = f"EXEC {SERVER_DB}.dbo.UPDATEFABRICARECUSTOMERDATAFromFabexpress " \
            #                  f"@CUSTOMERCODE='{customer_details['CustomerCode']}',@flatno1 = NULL,@AddressLines1=NULL, " \
            #                  f"@CityCode1=NULL,@AreaCode1=NULL, " \
            #                  f"@pincode1=NULL," \
            #                  f"@flatno2 ='{address_line_1}',@AddressLines2='{address_line_2},{address_line_3}'," \
            #                  f"@CityCode2='{address_details['CityCode']}'," \
            #                  f"@AreaCode2={address_details['AreaCode']}, @pincode2 = {address_details['Pincode']}, " \
            #                  f"@IsAddress2Deleted =NULL,@lat1 ='',@long1 ='',@lat2 ='{address_details['Lat']}',@long2 ='{address_details['Long']}',@GeoLocality1 = NULL,@GeoLocality2 = '{address_details['GeoLocality']}'"
        update_lat_long = f"EXEC {SERVER_DB}.dbo.USP_latlonglogs @AddressName='{address_details['AddressName']}',@Lat={address_details['Lat']},@Long={address_details['Long']},@bookingid=NULL," \
                              f"@CustomerCode={customer_details['CustomerCode']},@branchcode={address_details['BranchCode']}, @source " \
                              f"='FabExpress', @userid={0}"
        db.engine.execute(text(update_lat_long).execution_options(autocommit=True))
        try:
            db.engine.execute(text(query).execution_options(autocommit=True))
            db.engine.execute(text(update_address).execution_options(autocommit=True))
            

            log_data = {
                'query Updating the delivery address in the POS :': query,
                'query Updating the delivery address in the webapp :': update_address,
                'Updating the lat and long  :': update_lat_long
            }
            info_logger(f'Route: {request.path}').info(json.dumps(log_data))
        except Exception as e:
            error_logger(f'Delivery Blueprint Queries: {inspect.stack()[0].function}()').error(e)


def get_completed_pickups(interval_start_date, delivery_user_branches, user_id):
    """
    Function to get the completed pickups of the delivery user.
    @param interval_start_date: Initial date.
    @param delivery_user_branches: Branches associated with the delivery user.
    @param user_id: Delivery user id.
    @return: completed pickups SQLA result object.
    """
    # If the discount code is not applied, select NA.
    select_discount_code = case([(PickupRequest.DiscountCode == None, "NA"), ],
                                else_=PickupRequest.DiscountCode).label("DiscountCode")

    # If the coupon code is not applied, select NA.
    select_coupon_code = case([(PickupRequest.CouponCode == None, "NA"), ],
                              else_=PickupRequest.CouponCode).label("CouponCode")

    # If the address line 2 is not present, then select NA.
    select_address_line_2 = case([(CustomerAddres.AddressLine2 == None, "NA"), ],
                                 else_=CustomerAddres.AddressLine2).label("AddressLine2")

    # If the address line 3 is not present, then select NA.
    select_address_line_3 = case([(CustomerAddres.AddressLine3 == None, "NA"), ],
                                 else_=CustomerAddres.AddressLine3).label("AddressLine3")

    if interval_start_date is not None:
        # Here, an day interval is specified. So select the details from the start date and current date.
        interval_condition_check = and_(PickupRequest.CompletedDate < get_current_date(),
                                        PickupRequest.CompletedDate > interval_start_date)
    else:
        # No interval day is specified.
        interval_condition_check = PickupRequest.CompletedDate < get_current_date()

    # If the pickup is rescheduled, then select RescheduledDate, else select PickupDate.
    select_activity_date = case([(PickupReschedule.RescheduledDate == None, PickupRequest.PickupDate), ],
                                else_=PickupReschedule.RescheduledDate).label("ActivityDate")

    # If the pickup is rescheduled, then select reschedule's BranchCode, else BranchCode of
    # the pickup request.
    select_branch_code = case([(PickupReschedule.BranchCode == None, PickupRequest.BranchCode), ],
                              else_=PickupReschedule.BranchCode).label("BranchCode")

    # If the pickup is rescheduled, then select reschedule's DUserId, else DUserId of
    # the pickup request.
    select_delivery_user_id = case([(PickupReschedule.DUserId == None, PickupRequest.DUserId), ],
                                   else_=PickupReschedule.DUserId).label("DUserId")

    # If the pickup is rescheduled, then select reschedule's address id, else address id of
    # the pickup request.
    select_address_id = case([(PickupReschedule.CustAddressId == None, PickupRequest.CustAddressId), ],
                             else_=PickupReschedule.CustAddressId).label("CustAddressId")

    # If the pickup is rescheduled, then select reschedule's time slot from, else time slot from of
    # the pickup request.
    select_time_slot_from = case([(PickupReschedule.TimeSlotFrom == None, PickupRequest.TimeSlotFrom), ],
                                 else_=PickupReschedule.TimeSlotFrom).label("TimeSlotFrom")

    # If the pickup is rescheduled, then select reschedule's time slot to, else time slot to of
    # the pickup request.
    select_time_slot_to = case([(PickupReschedule.TimeSlotTo == None, PickupRequest.TimeSlotTo), ],
                               else_=PickupReschedule.TimeSlotTo).label("TimeSlotTo")

    select_order_type = case([(cast(PickupRequest.PickupSource, String).label('OrderType') == "Adhoc", "Normal"),
                              (cast(PickupRequest.PickupSource, String).label('OrderType') == 'Fabricare', "Normal"),
                              (cast(PickupRequest.PickupSource, String).label('OrderType') == 'Rewash', "Rewash"), ],
                             else_=literal('NA').label('OrderType')).label("OrderType")

    record_created_date = PickupRequest.RecordCreatedDate
    select_id = case([(PickupRequest.PickupRequestId != None, PickupRequest.PickupRequestId), ], else_="NA").label(
        "Id")

    # Total completed pickups for the branch.
    completed_pickups = db.session.query(literal('Pickup').label('ActivityType'),
                                         literal('NA').label('Type'),
                                         select_activity_date,select_order_type,
                                         PickupRequest.PickupRequestId.label('ActivityId'),
                                         select_id,
                                         PickupRequest.BookingId, Order.EGRN,
                                         select_time_slot_from,
                                         select_time_slot_to,
                                         select_delivery_user_id,
                                         DeliveryUser.UserName.label('DeliveryUser'), Customer.CustomerId,
                                         Customer.CustomerCode,
                                         Customer.CustomerName,
                                         Customer.MobileNo,
                                         select_discount_code, select_coupon_code, CustomerAddres.AddressLine1,
                                         select_address_line_2, select_address_line_3,
                                         record_created_date).join(Customer,
                                                                   PickupRequest.CustomerId == Customer.CustomerId).outerjoin(
        PickupReschedule,
        PickupReschedule.PickupRequestId == PickupRequest.PickupRequestId).join(
        CustomerAddres, select_address_id == CustomerAddres.CustAddressId).join(
        DeliveryUser,
        select_delivery_user_id == DeliveryUser.DUserId).outerjoin(
        Order,
        Order.PickupRequestId == PickupRequest.PickupRequestId).filter(
        PickupRequest.IsCancelled == 0, PickupRequest.PickupStatusId == 3,
        interval_condition_check,
        select_branch_code.in_(delivery_user_branches),
        select_delivery_user_id == user_id, Order.OrderId != None,
        or_(PickupReschedule.IsDeleted == 0, PickupReschedule.IsDeleted == None),
        or_(Order.IsDeleted == 0, Order.IsDeleted == None)
    )

    return completed_pickups


def get_completed_deliveries(interval_start_date, delivery_user_branches, user_id):
    """
    Function to get the completed deliveries of the delivery user.
    @param interval_start_date: Initial date.
    @param delivery_user_branches: Branches associated with the delivery user.
    @param user_id: Delivery user id.
    @return: SQL Alchemy ORM result.
    """
    # Total completed deliveries for the branch.

    select_discount_code = case([
        (Order.DiscountCode != None, Order.DiscountCode),
    ], else_="NA").label("DiscountCode")

    # If the CouponCode is present in the PickupRequest or the Orders table, select CouponCode.
    select_coupon_code = case([
        (Order.CouponCode != None, Order.CouponCode),
    ], else_="NA").label("CouponCode")

    # If the address line 2 is not present, then select NA.
    select_address_line_2 = case([(CustomerAddres.AddressLine2 == None, "NA"), ],
                                 else_=CustomerAddres.AddressLine2).label("AddressLine2")

    # If the address line 3 is not present, then select NA.
    select_address_line_3 = case([(CustomerAddres.AddressLine3 == None, "NA"), ],
                                 else_=CustomerAddres.AddressLine3).label("AddressLine3")

    if interval_start_date is not None:
        # Here, an day interval is specified. So select the details from the start date and current date.
        interval_condition_check = and_(Delivery.RecordCreatedDate < get_current_date(),
                                        Delivery.RecordCreatedDate > interval_start_date)
    else:
        # No interval day is specified.
        interval_condition_check = Delivery.RecordCreatedDate < get_current_date()

    # If the BookingId is present in the Deliveries table, select BookingId.
    select_booking_id = case([
        (Delivery.BookingId != None, Delivery.BookingId),
    ], else_="NA").label("BookingId")

    # If the delivery is rescheduled, then select reschedule's time slot from, else time slot from of
    # the delivery request.
    select_time_slot_from = case([(DeliveryReschedule.TimeSlotFrom == None, DeliveryRequest.TimeSlotFrom), ],
                                 else_=DeliveryReschedule.TimeSlotFrom).label("TimeSlotFrom")

    # If the delivery is rescheduled, then select reschedule's time slot to, else time slot to of
    # the delivery request.
    select_time_slot_to = case([(DeliveryReschedule.TimeSlotTo == None, DeliveryRequest.TimeSlotTo), ],
                               else_=DeliveryReschedule.TimeSlotTo).label("TimeSlotTo")

    record_created_date = Delivery.RecordCreatedDate

    # If the delivery is rescheduled, then select RescheduledDate, else select DeliveryDate.
    select_activity_date = case([(DeliveryReschedule.RescheduledDate == None, DeliveryRequest.DeliveryDate), ],
                                else_=DeliveryReschedule.RescheduledDate).label("ActivityDate")

    select_order_type = case([(cast(Order.OrderTypeId, String).label('OrderType') == None, "Normal"),
                              (cast(Order.OrderTypeId, String).label('OrderType') == 1, "Normal"),
                              (cast(Order.OrderTypeId, String).label('OrderType') == 2, "Rewash"), ],
                             else_=literal('NA').label('OrderType')).label("OrderType")
    select_delivery_type = case([(cast(DeliveryRequest.BookingId, String).label('Type') == None, "Walkin")],
                                else_=literal('D2D').label('Type')).label("Type")
    select_id = case([(Delivery.DeliveryRequestId != None, Delivery.DeliveryRequestId), ], else_="NA").label(
        "Id")

    completed_deliveries = db.session.query(literal('Delivery').label('ActivityType'),
                                            select_delivery_type,
                                            select_activity_date,select_order_type,
                                            Delivery.DeliveryId.label('ActivityId'),
                                            select_id,
                                            select_booking_id, Delivery.EGRN,
                                            select_time_slot_from,
                                            select_time_slot_to,
                                            Delivery.DUserId,
                                            DeliveryUser.UserName.label('DeliveryUser'),
                                            Customer.CustomerId,
                                            Customer.CustomerCode,
                                            Customer.CustomerName,
                                            Customer.MobileNo,
                                            select_discount_code, select_coupon_code,
                                            CustomerAddres.AddressLine1,
                                            select_address_line_2, select_address_line_3, record_created_date
                                            ).select_from(Delivery).join(Customer,
                                                                         Delivery.CustomerId == Customer.CustomerId).outerjoin(
        DeliveryReschedule, DeliveryReschedule.DeliveryRequestId == Delivery.DeliveryRequestId).join(
        Order,
        Delivery.OrderId == Order.OrderId).join(
        CustomerAddres, Delivery.DeliveryAddressId == CustomerAddres.CustAddressId).join(
        DeliveryUser,
        Delivery.DUserId == DeliveryUser.DUserId).outerjoin(DeliveryRequest,
                                                            Delivery.DeliveryRequestId == DeliveryRequest.DeliveryRequestId).filter(
        Delivery.DUserId == user_id, Delivery.BranchCode.in_(delivery_user_branches),
        Delivery.DeliveryId != None,
        interval_condition_check,
        or_(DeliveryReschedule.IsDeleted == 0, DeliveryReschedule.IsDeleted == None),
        or_(Order.IsDeleted == 0, Order.IsDeleted == None)
    )

    return completed_deliveries


# def get_pending_pickups(tomorrow, select_activity_date, select_time_slot_from, select_time_slot_to, lat, long,
#                         delivery_user_branches, user_id):
#     """
#     Getting the total pending pickups for tomorrow.
#     @param tomorrow: Tomorrow's date.
#     @param select_activity_date PickupDate of the pickup request.
#     @param select_time_slot_from: TimeSlotFrom field.
#     @param select_time_slot_to: TimeSlotTo field.
#     @param lat Lat value of the delivery user.
#     @param long Long value of the delivery user.
#     @param delivery_user_branches: Associated branches of delivery user.
#     @param user_id: Delivery user id.
#     @return: SQL Alchemy ORM result.
#     """
#     # If the discount code is not applied, select NA.
#     select_discount_code = case([(PickupRequest.DiscountCode == None, "NA"), ],
#                                 else_=PickupRequest.DiscountCode).label("DiscountCode")
#
#     # If the coupon code is not applied, select NA.
#     select_coupon_code = case([(PickupRequest.CouponCode == None, "NA"), ],
#                               else_=PickupRequest.CouponCode).label("CouponCode")
#
#     # If the address line 2 is not present, then select NA.
#     select_address_line_2 = case([(CustomerAddres.AddressLine2 == None, "NA"), ],
#                                  else_=CustomerAddres.AddressLine2).label("AddressLine2")
#
#     # If the address line 3 is not present, then select NA.
#     select_address_line_3 = case([(CustomerAddres.AddressLine3 == None, "NA"), ],
#                                  else_=CustomerAddres.AddressLine3).label("AddressLine3")
#
#     # If the pickup is rescheduled, then select reschedule's BranchCode, else BranchCode of
#     # the pickup request.
#     select_branch_code = case([(PickupReschedule.BranchCode == None, PickupRequest.BranchCode), ],
#                               else_=PickupReschedule.BranchCode).label("BranchCode")
#
#     # If the OrderId is NOT present in the Orders table, return 0, else return the value.
#     select_order_id = case([(Order.OrderId == None, 0), ],
#                            else_=Order.OrderId).label("OrderId")
#
#     # If the CouponCode is present in the PickupRequest or the Orders table, select CouponCode.
#     select_booking_id = case([
#         (PickupRequest.BookingId != None, PickupRequest.BookingId),
#     ], else_="NA").label("BookingId")
#
#     # If the pickup is rescheduled, then select reschedule's DUserId, else DUserId of
#     # the pickup request.
#     select_delivery_user_id = case([(PickupReschedule.DUserId == None, PickupRequest.DUserId), ],
#                                    else_=PickupReschedule.DUserId).label("DUserId")
#
#     # If the pickup is rescheduled, then select reschedule's address id, else address id of
#     # the pickup request.
#     select_address_id = case([(PickupReschedule.CustAddressId == None, PickupRequest.CustAddressId), ],
#                              else_=PickupReschedule.CustAddressId).label("CustAddressId")
#
#     # Calculating the distance in KM between the delivery user's lat and long to
#     # the customer address' lat and long.
#     distance_in_km = func.dbo.GetDistance(lat, long, CustomerAddres.Lat,
#                                           CustomerAddres.Long).label('Distance')
#
#     # Total pending pickup requests for the branch.
#     base_query = db.session.query(literal('Pickup').label('ActivityType'),
#                                   PickupRequest.PickupRequestId.label('ActivityId'),
#                                   select_booking_id, select_order_id, literal('NA').label('EGRN'),
#                                   literal('Normal').label('OrderType'),
#                                   select_activity_date,
#                                   select_time_slot_from,
#                                   select_time_slot_to,
#                                   select_delivery_user_id,
#                                   DeliveryUser.UserName.label('DeliveryUser'), Customer.CustomerCode,
#                                   Customer.CustomerName,
#                                   Customer.MobileNo, literal(False).label('MonthlyCustomer'),
#                                   select_discount_code, select_coupon_code, CustomerAddres.AddressLine1,
#                                   select_address_line_2, select_address_line_3, select_branch_code,
#                                   CustomerAddres.Lat, CustomerAddres.Long, distance_in_km
#                                   ).join(
#         Customer,
#         PickupRequest.CustomerId == Customer.CustomerId).outerjoin(
#         PickupReschedule,
#         PickupReschedule.PickupRequestId == PickupRequest.PickupRequestId).join(
#         CustomerAddres, select_address_id == CustomerAddres.CustAddressId).join(
#         DeliveryUser,
#         select_delivery_user_id == DeliveryUser.DUserId)\
#         # .outerjoin(Order, Order.PickupRequestId == PickupRequest.PickupRequestId)
#
#     # Select all the details based on given branch code(s).
#     pending_pickups = base_query.filter(select_branch_code.in_(delivery_user_branches))
#
#     if tomorrow is not None:
#         # tomorrow date is given. So select only for the tomorrow's records.
#         pending_pickups = pending_pickups.filter(
#             or_(Order.IsDeleted == 0, Order.IsDeleted == None),
#             PickupRequest.IsCancelled == 0, PickupRequest.PickupStatusId.in_((1, 2)),
#             select_activity_date == tomorrow,
#             select_delivery_user_id == user_id,
#             or_(PickupReschedule.IsDeleted == 0, PickupReschedule.IsDeleted == None),
#
#         )
#     else:
#         # Normal pending pickups up to current date.
#         pending_pickups = pending_pickups.filter(
#             # or_(Order.IsDeleted == 0, Order.IsDeleted == None),
#             PickupRequest.IsCancelled == 0, PickupRequest.PickupStatusId.in_((1, 2)),
#             select_activity_date <= get_current_date(),
#             select_delivery_user_id == user_id,
#             or_(PickupReschedule.IsDeleted == 0, PickupReschedule.IsDeleted == None)
#
#         )
#
#     return pending_pickups


# def get_pending_deliveries(tomorrow, select_activity_date, select_time_slot_from, select_time_slot_to, lat, long,
#                            delivery_user_branches, user_id):
#     """
#     API  for getting the tomorrow's pending delivery activities for the user.
#     @param tomorrow: Tomorrow's date.
#     @param select_activity_date DeliveryDate of the delivery request.
#     @param select_time_slot_from: TimeSlotFrom field.
#     @param select_time_slot_to: TimeSlotTo field.
#     @param lat Lat value of the delivery user.
#     @param lat Long value of the delivery user.
#     @param delivery_user_branches: Associated branches of delivery user.
#     @param user_id: Delivery user id.
#     @return: SQL Alchemy ORM result.
#     """
#     # Total delivery requests for the branch.
#
#     select_discount_code = case([
#         (Order.DiscountCode != None, Order.DiscountCode),
#     ], else_="NA").label("DiscountCode")
#
#     # If the CouponCode is present in the PickupRequest or the Orders table, select CouponCode.
#     select_coupon_code = case([
#         (Order.CouponCode != None, Order.CouponCode),
#     ], else_="NA").label("CouponCode")
#
#     # If the CouponCode is present in the PickupRequest or the Orders table, select CouponCode.
#     select_booking_id = case([
#         (DeliveryRequest.BookingId != None, DeliveryRequest.BookingId),
#     ], else_="NA").label("BookingId")
#
#     # If the address line 2 is not present, then select NA.
#     select_address_line_2 = case([(CustomerAddres.AddressLine2 == None, "NA"), ],
#                                  else_=CustomerAddres.AddressLine2).label("AddressLine2")
#
#     # If the address line 3 is not present, then select NA.
#     select_address_line_3 = case([(CustomerAddres.AddressLine3 == None, "NA"), ],
#                                  else_=CustomerAddres.AddressLine3).label("AddressLine3")
#
#     # If the delivery is rescheduled, then select reschedule's DUserId, else DUserId of
#     # the delivery request.
#     select_delivery_user_id = case(
#         [(DeliveryReschedule.DUserId == None, DeliveryRequest.DUserId), ],
#         else_=DeliveryReschedule.DUserId).label("DUserId")
#
#     # If the delivery is rescheduled, then select reschedule's address id, else address id of
#     # the delivery request.
#     select_address_id = case(
#         [(DeliveryReschedule.CustAddressId == None, DeliveryRequest.CustAddressId), ],
#         else_=DeliveryReschedule.CustAddressId).label("CustAddressId")
#
#     # Calculating the distance in KM between the delivery user's lat and long to
#     # the customer address' lat and long.
#     distance_in_km = func.dbo.GetDistance(lat, long, CustomerAddres.Lat,
#                                           CustomerAddres.Long).label('Distance')
#
#     # Selecting the order type.
#     select_order_type = case([
#         (cast(Order.OrderTypeId, String).label('OrderType') == None, "Normal"),
#         (cast(Order.OrderTypeId, String).label('OrderType') == 1, "Normal"),
#         (cast(Order.OrderTypeId, String).label('OrderType') == 2, "Rewash"),
#     ],
#         else_=literal('NA').label('OrderType')).label("OrderType")
#
#     #  Set MonthlyCustomer is false when MonthlyCustomer is Null or 0 else true
#     select_monthly_customer = case(
#         [(or_(Customer.MonthlyCustomer == None, Customer.MonthlyCustomer != 1), 'False'), ],
#         else_=Customer.MonthlyCustomer).label("MonthlyCustomer")
#
#     base_query = db.session.query(literal('Delivery').label('ActivityType'),
#                                   DeliveryRequest.DeliveryRequestId.label('ActivityId'),
#                                   select_booking_id, Order.OrderId, Order.EGRN,
#                                   select_order_type,
#                                   select_activity_date,
#                                   select_time_slot_from,
#                                   select_time_slot_to,
#                                   select_delivery_user_id, DeliveryUser.UserName.label('DeliveryUser'),
#                                   Customer.CustomerCode,
#                                   Customer.CustomerName,
#                                   Customer.MobileNo, select_monthly_customer,
#                                   select_discount_code, select_coupon_code, CustomerAddres.AddressLine1,
#                                   select_address_line_2, select_address_line_3, DeliveryRequest.BranchCode,
#                                   CustomerAddres.Lat, CustomerAddres.Long, distance_in_km
#                                   ).join(Customer,
#                                          DeliveryRequest.CustomerId == Customer.CustomerId).outerjoin(
#         DeliveryReschedule, DeliveryReschedule.DeliveryRequestId == DeliveryRequest.DeliveryRequestId).join(
#         Order,
#         DeliveryRequest.OrderId == Order.OrderId).join(
#         CustomerAddres, select_address_id == CustomerAddres.CustAddressId).join(
#         DeliveryUser,
#         select_delivery_user_id == DeliveryUser.DUserId).outerjoin(Delivery,
#                                                                    Delivery.DeliveryRequestId == DeliveryRequest.DeliveryRequestId)
#
#     # Select all the details based on given branch code(s).
#     pending_deliveries = base_query.filter(DeliveryRequest.BranchCode.in_(delivery_user_branches),
#                                            or_(DeliveryRequest.WalkIn == 0, DeliveryRequest.WalkIn == None))
#
#     if tomorrow is not None:
#         # tomorrow date is given. So select only for the tomorrow's records.
#         pending_deliveries = pending_deliveries.filter(
#             or_(Order.IsDeleted == 0, Order.IsDeleted == None),
#             select_delivery_user_id == user_id, DeliveryRequest.IsDeleted == 0,
#             Delivery.DeliveryId == None, select_activity_date == tomorrow,
#             or_(DeliveryReschedule.IsDeleted == 0, DeliveryReschedule.IsDeleted == None),
#
#         )
#     else:
#         # Normal pending pickups up to current date.
#         pending_deliveries = pending_deliveries.filter(
#             or_(Order.IsDeleted == 0, Order.IsDeleted == None),
#             select_delivery_user_id == user_id, DeliveryRequest.IsDeleted == 0,
#             Delivery.DeliveryId == None, select_activity_date <= get_current_date(),
#             or_(DeliveryReschedule.IsDeleted == 0, DeliveryReschedule.IsDeleted == None),
#
#         )
#
#     return pending_deliveries


def save_travel_log(activity, user_id, order_id, delivery_id, lat, long):
    """
    Function for saving the travel log of the delivery user.
    @param activity: Pickup/Order
    @param user_id: Delivery User's Id.
    @param order_id:
    @param delivery_id:
    @param lat: Latitude value of the current GPS position.
    @param long: Longitude value of the current GPS position.
    @return:
    """
    # New travel log object.
    new_travel_log = TravelLog(
        Activity=activity,
        DUserId=user_id,
        OrderId=order_id,
        DeliveryId=delivery_id,
        Lat=lat,
        Long=long,
        RecordCreatedDate=get_current_date(),
        RecordLastUpdatedDate=get_current_date()
    )

    # Saving the travel log into the DB.
    db.session.add(new_travel_log)
    db.session.commit()


def get_delivery_user_branches(user_id, is_delivery=False):
    """
    Function for getting the branch codes of delivery users.
    @param user_id:
    @param is_delivery:
    @return: list of branch codes associated with the user.
    If no branches are found, empty will be returned.
    """

    # Getting the branches associated with the delivery user.
    base_query = db.session.query(DeliveryUserBranch.BranchCode).join(Branch,
                                                                      DeliveryUserBranch.BranchCode == Branch.BranchCode).filter(
        DeliveryUserBranch.DUserId == user_id, DeliveryUserBranch.IsDeleted == 0)
    if is_delivery:
        delivery_user_branches = base_query.all()
    else:
        # delivery_user_branches = base_query.filter(Branch.IsActive == 1).all()
        delivery_user_branches = base_query.all()
    # Populating the list of branch codes.
    branch_codes = [delivery_user_branch.BranchCode for delivery_user_branch in delivery_user_branches]

    return branch_codes


def get_delivery_user_branches_count(user_id):
    """
    Function for getting the branch codes of delivery users.
    @param user_id:
    @param is_delivery:
    @return: list of branch codes associated with the user.
    If no branches are found, empty will be returned.
    """

    # Getting the branches associated with the delivery user.
    branch_count = db.session.query(func.count(DeliveryUserBranch.BranchCode)).join(Branch,
                                                                                    DeliveryUserBranch.BranchCode == Branch.BranchCode).filter(
        DeliveryUserBranch.DUserId == user_id, DeliveryUserBranch.IsDeleted == 0, Branch.IsActive == 1).scalar()

    return branch_count


def get_delivery_user_branch_names(user_id):
    """
    Function for getting the branch names of delivery users.
    @param user_id:
    @return: list of branch codes associated with the user.
    If no branches are found, empty will be returned.
    """

    # Select display name if it exists else BranchName
    select_branch_name = case([(or_(Branch.DisplayName == None, Branch.DisplayName == ''), Branch.BranchName), ],
                              else_=Branch.DisplayName).label("BranchName")
    # Getting the branches associated with the delivery user.
    delivery_user_branches = db.session.query(DeliveryUserBranch.BranchCode, select_branch_name).join(Branch,
                                                                                                      DeliveryUserBranch.BranchCode == Branch.BranchCode).filter(
        DeliveryUserBranch.DUserId == user_id, DeliveryUserBranch.IsDeleted == 0, Branch.IsActive == 1).all()

    # Populating the list of branch codes.
    branch_names = [delivery_user_branch.BranchName for delivery_user_branch in delivery_user_branches]

    return branch_names


def check_branch_holiday(activity_date, branch_code):
    """
    Checking whether the activity date (pickup date, rescheduled pickup date, rescheduled delivery date..etc)
    is a branch holiday or not. If the date is a branch holiday, activity can not be performed.
    @param activity_date: Date in string format (d-m-Y)
    @param branch_code:
    @return: True if the date is a branch holiday, False if it is not a branch holiday.
    """
    # Check for branch holidays.
    branch_holidays = db.session.query(BranchHoliday.HolidayDate).filter(BranchHoliday.BranchCode == branch_code,
                                                                         BranchHoliday.IsActive == 1).all()
    holidays = []
    if branch_holidays:
        for branch_holiday in branch_holidays:
            holidays.append(branch_holiday.HolidayDate.strftime("%d-%m-%Y"))

    if activity_date in holidays:
        # It is a holiday. No need for further checks.
        return True

    formatted_date = datetime.strptime(activity_date, "%d-%m-%Y")
    formatted_day = formatted_date.strftime('%A')

    # Checking whether the delivery date is a weekly off for Branch
    branch_details = db.session.query(Branch).filter(
        Branch.BranchCode == branch_code).one_or_none()

    if branch_details is not None:
        if branch_details.WeeklyOffDays is not None:
            branch_weekly_off_days = ["No holiday", "Sunday", "Monday", "Tuesday", "Wednesday", "Friday",
                                      "Saturday"]

            branch_weekly_off_day = branch_weekly_off_days[branch_details.WeeklyOffDays]
            if branch_weekly_off_day == formatted_day:
                # This is a branch weekly off day.
                return True

    return False


def attendance_for_today(user_id):
    """
    Getting the attendance details for today.
    @param user_id: Delivery user id.
    @return: DeliveryUserAttendance record.
    """
    today = datetime.today().strftime("%Y-%m-%d")
    attendance_record_of_today = db.session.query(DeliveryUserAttendance.Date,
                                                  DeliveryUserAttendance.ClockInTime, DeliveryUserAttendance.ClockInLat,
                                                  DeliveryUserAttendance.ClockInLong,
                                                  DeliveryUserAttendance.ClockOutTime,
                                                  DeliveryUserAttendance.ClockOutLat,
                                                  DeliveryUserAttendance.ClockOutLong).filter(
        DeliveryUserAttendance.DUserId == user_id,
        DeliveryUserAttendance.Date == today,
        DeliveryUserAttendance.IsDeleted == 0).one_or_none()
    return attendance_record_of_today


# def get_essential_data_for_payment(delivery_request_id, order_id):
#     """
#     Function for getting the essential details for the payment.
#     @param delivery_request_id:
#     @param order_id:
#     @return: essential details in a dict format.
#     """
#     essential_details = {}
#     # Getting the essential delivery request details from the DB.
#     essentials = db.session.query(DeliveryRequest.OrderId, DeliveryRequest.IsPartial, Order.EGRN, Order.BranchCode,
#                                   Customer.CustomerCode).join(Order,
#                                                               DeliveryRequest.OrderId == Order.OrderId).join(
#         Customer,
#         Order.CustomerId == Customer.CustomerId).filter(
#         DeliveryRequest.DeliveryRequestId == delivery_request_id, DeliveryRequest.OrderId == order_id,
#         DeliveryRequest.IsDeleted == 0, Order.IsDeleted == 0).one_or_none()

#     if essentials is not None:
#         customer_code = essentials.CustomerCode
#         egrn = essentials.EGRN
#         branch_code = essentials.BranchCode

#         if not essentials.IsPartial:
#             # This is not a partial delivery. All the garments under this order are ready to be delivered.
#             garments_for_delivery = db.session.query(OrderGarment.POSOrderGarmentId
#                                                      ).filter(
#                 OrderGarment.OrderId == order_id, OrderGarment.IsDeleted == 0).all()

#             # Populating the list of POS order garment ids.
#             pos_order_garment_ids = [garment.POSOrderGarmentId for garment in garments_for_delivery]
#         else:
#             # Only some garments are selected for the delivery. Only those garments' price need to be considered
#             # here.

#             # Delivery garments explicitly specified. Not all garments in this order are selected for delivery.
#             garments_for_delivery = db.session.query(DeliveryGarment.POSOrderGarmentId
#                                                      ).filter(
#                 DeliveryGarment.DeliveryRequestId == delivery_request_id, DeliveryGarment.IsDeleted == 0).all()

#             # Populating the list of POS order garment ids.
#             pos_order_garment_ids = [garment.POSOrderGarmentId for garment in garments_for_delivery]

#         allowed_pos_order_garment_ids = []
#         # Discarding the order garment ids that have TRN generated.
#         trn_details = payment_module.get_garments_with_trn_status(egrn, ','.join(map(str, pos_order_garment_ids)))
#         # Populating a dict of result from trn_details
#         trn_amount_received = {'AmountReceived': trn_details[0]['AmountReceived'], 'trnno': trn_details[0]['trnno'],
#                                'Amount': trn_details[0]['Amount']}

#         for pos_order_garment_id in pos_order_garment_ids:
#             for trn_detail in trn_details:
#                 if pos_order_garment_id == trn_detail['ordergarmentid'] and trn_detail['TRNGenerated'] == "NO":
#                     # This order garment id has no TRN generated.
#                     allowed_pos_order_garment_ids.append(pos_order_garment_id)

#         egrn_details = payment_module.get_unsettled_egrn_details_garment_wise_with_complaints(customer_code,
#                                                                                               egrn,
#                                                                                               allowed_pos_order_garment_ids)

#         essential_details = {'egrn': egrn, 'customer_code': customer_code, 'egrn_details': egrn_details,
#                              'pos_order_garment_ids': allowed_pos_order_garment_ids, 'branch_code': branch_code,
#                              'trn_amount_received': trn_amount_received}

#     return essential_details

def get_essential_data_for_payment(egrn, TRNNo, customer_code):
    """
    Function for getting the essential details for the payment.
    @param delivery_request_id:
    @param order_id:
    @return: essential details in a dict format.
    """
    essential_details = {}
    # Getting the essential delivery request details from the DB.


    allowed_pos_order_garment_ids = []
    # Discarding the order garment ids that have TRN generated.
    trn_details = payment_module.get_garments_with_trn_status(TRNNo)
    # Populating a dict of result from trn_details
    print(trn_details)
    trn_amount_received = {'AmountReceived': trn_details[0]['AmountReceived'], 'trnno': trn_details[0]['trnno'],
                           'Amount': trn_details[0]['Amount']}
    pos_order_garment_ids = []

    for order_garment_ids in trn_details:
        pos_order_garment_ids.append(order_garment_ids['ordergarmentid'])

    print(pos_order_garment_ids)

    for pos_order_garment_id in pos_order_garment_ids:
        for trn_detail in trn_details:
            if pos_order_garment_id == trn_detail['ordergarmentid'] and trn_detail['TRNGenerated'] == "NO":
                # This order garment id has no TRN generated.
                allowed_pos_order_garment_ids.append(pos_order_garment_id)
    print(allowed_pos_order_garment_ids)

    egrn_details = payment_module.get_unsettled_egrn_details_garment_wise_with_complaints(customer_code,
                                                                                          egrn,
                                                                                          allowed_pos_order_garment_ids)

    essential_details = {'egrn_details': egrn_details,
                         'pos_order_garment_ids': allowed_pos_order_garment_ids,
                         'trn_amount_received': trn_amount_received}
    print(essential_details)
    return essential_details


def count_order_garments_complaints(order_id):
    """
    Function for checking if there's any complaint in any of the order garments or not.
    If complaints are found in any of the garments, payment can not be made for this order.
    @param order_id: Order id of the order.
    @return: Number of complaints (garments that have complaint) under this order.
    """

    number_of_complaints = 0
    order_details = db.session.query(Order.EGRN).filter(Order.OrderId == order_id).one_or_none()
    if order_details is not None:
        if order_details.EGRN is not None:
            number_of_complaints = db.session.query(Complaint.CRMComplaintId).filter(
                Complaint.EGRN == order_details.EGRN).all()
            number_of_complaints = len(number_of_complaints)
    return number_of_complaints


def count_order_garments_open_complaints(order_id):
    """
    Function for checking if there's any open complaint in any of the order garments or not.
    If complaints are found in any of the garments, payment can not be made for this order.
    @param order_id: Order id of the order.
    @return: Number of complaints (garments that have complaint) under this order.
    """

    number_of_complaints = 0
    order_details = db.session.query(Order.EGRN).filter(Order.OrderId == order_id).one_or_none()
    if order_details is not None:
        if order_details.EGRN is not None:
            number_of_complaints = db.session.query(Complaint.CRMComplaintId).filter(
                Complaint.EGRN == order_details.EGRN, Complaint.CRMComplaintStatus == 'Active').all()
            number_of_complaints = len(number_of_complaints)
    return number_of_complaints


def get_customer_type(customer_code):
    """
    Function for checking the customer type. i.e. Regular or Monthly.
    @param customer_code:
    @return: SQLA result.
    """
    customer_type_query = f"EXEC {LOCAL_DB}..GetCustomerType @CustomerCode='{customer_code}'"
    customer_type = CallSP(customer_type_query).execute().fetchone()
    return customer_type

# def invoice_generate(invoice_num):
#     """
#        Function for  Invoice report
#     """
#     invoice_url = None

#     try:

#         data = {
#             "reportName": 'Invoice',
#             "DocumentNo": invoice_num
#         }
#         data_string = json.dumps(data)
#         headers = {'Content-Type': 'application/json', 'Content-Length': str(len(data_string))}

#         # url for generate the report
#         api_url = "http://192.168.202.4/GetMobileReports/api/GenerateReport"
#         response = requests.post(api_url, data=data_string, headers=headers)

#         response = json.loads(response.text)
#         if response:
#             # A valid response has been received.
#             if response['status'] == "success":
#                 invoice_url = response['url']

#     except Exception as e:
#         error_logger(f'Delivery Blueprint Queries: {inspect.stack()[0].function}()').error(e)

#     return invoice_url


def get_payable_amount_via_sp_trn(CustomerCode, EGRN, TRNNo):
    """
    For getting the payable amount through a SP
    @param customer_code: customer_code
    @param order_egrn:
    @return: payable amount
    """
    query = f"EXEC JFSL.[dbo].[SPFabexpressOrderGenerateInvoiceCustApp] @TRNNo = '{TRNNo}' , @CustomerCode = '{CustomerCode}'"
    log_data = {
        'query of get_payable_amount_via_sp ....... :': query,
       
    }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))

    result = CallSP(query).execute().fetchall()

    log_data = {
        'query of get_payable_amount_via_sp ....... :': query,
        'result of get_payable_amount_via_sp ......... :': result,
    }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))

    for i in result:
        if i['DCNO'] == TRNNo:
            # Populating a dictionary of results from SP
            payable_details = {'DCNO': i['DCNO'], 'ORDERDATE': i['ORDERDATE'], 'PAYABLEAMOUNT': i['PAYABLEAMOUNT'], 'DELIVERYCHARGE': i['DeliveryCharge'], 'IsPreAppliedCoupon': i['IsPreAppliedCoupon']}

            return payable_details
    return {}
