"""
------------------------
Common module
These are the common functions/logic that are related to the Fabric project that can be used in various modules in various scenarios.
------------------------
Coded by: Krishna Prasad K
© Jyothy Fabricare Services LTD.
------------------------
"""
from sqlalchemy import or_, case, text

from fabric import db
from fabric.modules.models import City, Branch, Area, PickupRequest, PickupReschedule, CustomerAddres
from fabric.settings.project_settings import OLD_DB, SERVER_DB, LOCAL_DB, ALERT_ENGINE_DB
from fabric.generic.classes import CallSP
from fabric.generic.loggers import error_logger, info_logger
import json
from flask import request


def validate_discount_code(discount_code, source, egrn, customer_code, branch_code, is_er_discount):
    """
    Function for validating a discount code by calling a stored procedure.
    @param discount_code: DiscountCode given to a user. eg: SAREESPA
    @param source: Whether the discount is applying at the time of 'pickup' or 'order'.
    @param egrn: EGRN of the order if any.
    @param customer_code: CustomerCode of the customer.
    @param branch_code: BranchCode of the customer.
    @param is_er_discount: Whether the DiscountCode is an EasyRewardz discount code or not.
    @return: result of the stored procedure as a dict or None if it fails to execute.
    """
    # Constructing the query string for the execution.

    if source == "order":
        # Here, the source is order. So EGRN need to be passed to the SP.
        query = f"EXEC {SERVER_DB}..validateDiscountCode @PROMOCODE='{discount_code}',@source='{source}',@CUSTOMERCODE='{customer_code}',@Branchcode='{branch_code}',@EGRNNo='{egrn}',@EasyDiscount='{is_er_discount}'"
    else:
        # source can also be pickup.
        query = f"EXEC {SERVER_DB}..validateDiscountCode @PROMOCODE='{discount_code}',@source='{source}',@CUSTOMERCODE='{customer_code}',@Branchcode='{branch_code}',@EasyDiscount='{is_er_discount}'"
    # Executing the stored procedure.
    result = CallSP(query).execute().fetchone()

    # convert DISCOUNTAMOUNT to int for logging
    result.update({'DISCOUNTAMOUNT': int(result['DISCOUNTAMOUNT'])})

    log_data = {
        'query of validate_discount_code ': query,
        'Result of validate_discount_code': result,
    }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))

    return result


def validate_coupon_code(coupon_code, customer_code, branch_code, source, egrn):
    """
    Function for validating the coupon code (compensation coupon, marketing coupon...etc.)
    @param coupon_code: CouponCode given to a customer (eg: 2000010821)
    @param customer_code: POS customer code.
    @param branch_code: branch code of the customer.
    @param source: If the order has already created and has EGRN, then source will be order; otherwise pickup.
    @param egrn: EGRN of the order.
    @return: result of the stored procedure as a dict or None if it fails to execute.
    """
    # Constructing the query.
    query = f"EXEC {SERVER_DB}.dbo.ValidatePromocodeforApp @CouponCode='{coupon_code}', @Customercode='{customer_code}',@isCode='1', @Branch='{branch_code}',@Source='{source}',@EGRNNO='{egrn}'"
    # Executing the stored procedure.
    result = CallSP(query).execute().fetchone()
    log_data = {
        'query of validate_coupon_code ': query,
        'Result of validate_coupon_code': result,
    }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))
    return result


# def check_open_pickups(address_id, customer_id):
#     """
#     Function for getting the current open pickups for a customer.
#     @param address_id: Address id.
#     @param customer_id: Customer id.
#     @return: If an existing pickup is present, return the dict result variable.
#     Otherwise dict variable with status False will be returned.
#     """

#     # If the pickup is rescheduled, then select reschedule's BranchCode, else BranchCode of
#     # the pickup request.
#     select_address_id = case([(PickupReschedule.CustAddressId == None, PickupRequest.CustAddressId), ],
#                              else_=PickupReschedule.CustAddressId).label("CustAddressId")

#     # Getting the open pickups from the DB.
#     open_pickups = db.session.query(PickupRequest.PickupRequestId, select_address_id,
#                                     CustomerAddres.CityCode).outerjoin(
#         PickupReschedule,
#         PickupRequest.PickupRequestId == PickupReschedule.PickupRequestId).join(CustomerAddres,
#                                                                                 CustomerAddres.CustAddressId == select_address_id).filter(
#         PickupRequest.CustomerId == customer_id,
#         or_(PickupRequest.PickupSource == 'Fabricare', PickupRequest.PickupSource == 'Adhoc'),
#         PickupRequest.IsCancelled == 0,
#         PickupRequest.PickupStatusId.in_(
#             (1, 2)), or_(PickupReschedule.IsDeleted == 0, PickupReschedule.IsDeleted == None)).all()

#     for open_pickup in open_pickups:
#         if open_pickup.CustAddressId == address_id:
#             # There's an open pickup found for the customer for
#             # the same address id.
#             return {'status': True, 'pickup_request_id': open_pickup.PickupRequestId}

#     # No open pickups have been found.
#     return {'status': False}
def check_open_pickups(address_id, customer_id):
    """
    Function for getting the current open pickups for a customer.
    @param address_id: Address id.
    @param customer_id: Customer id.
    @return: If an existing pickup is present, return the dict result variable.
    Otherwise dict variable with status False will be returned.
    """

    # If the pickup is rescheduled, then select reschedule's BranchCode, else BranchCode of
    # the pickup request.
    select_address_id = case([(PickupReschedule.CustAddressId == None, PickupRequest.CustAddressId), ],
                             else_=PickupReschedule.CustAddressId).label("CustAddressId")

    # Getting the open pickups from the DB.
    open_pickups = db.session.query(PickupRequest.PickupRequestId, select_address_id,
                                    CustomerAddres.CityCode).outerjoin(
        PickupReschedule,
        PickupRequest.PickupRequestId == PickupReschedule.PickupRequestId).join(CustomerAddres,
                                                                                CustomerAddres.CustAddressId == select_address_id).filter(
        PickupRequest.CustomerId == customer_id,
        or_(PickupRequest.PickupSource != 'Inbound Re',
            PickupRequest.PickupSource != 'Rewash',
            PickupRequest.PickupSource != 'Outbound R'),
        PickupRequest.IsCancelled == 0,
        PickupRequest.PickupStatusId.in_(
            (1, 2)), or_(PickupReschedule.IsDeleted == 0, PickupReschedule.IsDeleted == None)).all()
    pickups = []
    if len(open_pickups) > 1:
        for open_pickup in open_pickups:
            pickups.append(open_pickup.PickupRequestId)
        # open_pickups = {'pickups': pickups}
        log_data = {
            'multiple open pickups': pickups
        }
        info_logger(f'Route: {request.path}').info(json.dumps(log_data))
    for open_pickup in open_pickups:
        # if open_pickup.CustAddressId == address_id:
            # There's an open pickup found for the customer for
            # the same address id.
        return {'status': True, 'pickup_request_id': open_pickup.PickupRequestId}

    # No open pickups have been found.
    return {'status': False}


def get_city_from_branch_code(branch_code):
    """
    Function for getting the city and city code based on a branch code.
    @param branch_code:
    @return: City name and City code.
    """

    city_details = db.session.query(City.CityName, City.CityCode).join(Area, City.CityCode == Area.CityCode).join(
        Branch,
        Area.AreaCode == Branch.AreaCode).filter(
        Branch.BranchCode == branch_code).one_or_none()

    return city_details



def notify_pos_regarding_pickup_reschedule_or_cancel(pickup_request_id, booking_id, is_cancelled, is_rescheduled, is_cob):
    """
    If the pickup is cancelled/rescheduled from the App, inform the POS by calling the below SP.
    @param pickup_request_id: PickupRequestId of the pickup request.
    @param booking_id: BookingId of the pickup request.
    @param is_cancelled: 1 if the pickup is cancelled, else 0.
    @param is_rescheduled: 1 if the pickup is rescheduled, else 0.
    @return:
    """
    query = f"""EXEC {LOCAL_DB}.dbo.USP_UPDATE_CANCELLEDorRESCHEDULED_PICKUP_IN_FABRICARE @PICKUPREQUESTID={pickup_request_id},@ISCANCELLED={is_cancelled},@ISRESCHEDULE={is_rescheduled},@ISCOB={is_cob},@BOOKINGID={booking_id}"""

    # Executing the SP.
    db.engine.execute(text(query).execution_options(autocommit=True))
    log_data = {
        'cancel or reschedule pickup': query
    }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))


def send_out_for_activity_sms(alert_code, customer_name, mobile_number, booking_id, egrn):
    """
    Function for informing the POS to send the SMS while out for pickup/delivery happens in a day.
    @param alert_code: This can be either OUT_FOR_DELIVERY or OUT_FOR_PICKUP.
    @param customer_name: Name of the customer.
    @param mobile_number: Mobile number of the customer.
    @param booking_id: BookingId of the pickup.
    @param egrn: EGRN of the order.
    @return:
    """
    if alert_code == 'OUT_FOR_DELIVERY':
        # If the activity is delivery, order number will be EGRN.
        order_number = egrn
    else:
        # If the activity is pickup, order number will be BookingId.
        order_number = booking_id
    query = f"""EXEC {ALERT_ENGINE_DB}..ALERT_PROCESS @ALERT_CODE = '{alert_code}'
                                         ,@EMAIL_ID = NULL
                                         ,@MOBILE_NO = {mobile_number}
                                         ,@SUBJECT = NULL
                                         ,@DISPATCH_FLAG = 'OFF'
                                         ,@EMAIL_SENDER_ADD = NULL
                                         ,@SMS_SENDER_ADD = NULL
                                         ,@P1 = '{customer_name}'
                                         ,@P2 = {order_number}
                                         ,@P3 = '080-46644664'
                                         ,@P4 = NULL
                                         ,@P5 = NULL
                                         ,@P6 = NULL
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
                                         ,@REC_ID = '0'"""

    # Calling the SP.
    db.engine.execute(text(query).execution_options(autocommit=True))
    log_data = {
        'send_out_for_activity_sms': query
        }

    info_logger(f'Route: {request.path}').info(json.dumps(log_data))



def send_reschedule_sms(alert_code, customer_name, mobile_number, egrn, garments_count, rescheduled_date):
    """
    API for triggering alert engine to send SMS when a delivery reschedule happen.
    @param alert_code: Alert code of the alert engine. Value will be DELIVERY_RESCHEDULE.
    @param customer_name: Customer name.
    @param mobile_number: Mobile number of the customer.
    @param egrn: EGRN of the order.
    @param garments_count: Total number of garments under this delivery requests.
    @param rescheduled_date: RescheduledDate of the delivery request.
    @return:
    """
    query = f"""EXEC {ALERT_ENGINE_DB}..ALERT_PROCESS @ALERT_CODE = '{alert_code}'
                                         ,@EMAIL_ID = NULL
                                         ,@MOBILE_NO = '{mobile_number}'
                                         ,@SUBJECT = NULL
                                         ,@DISPATCH_FLAG = 'OFF'
                                         ,@EMAIL_SENDER_ADD = NULL
                                         ,@SMS_SENDER_ADD = NULL
                                         ,@P1 = '{customer_name}'
                                         ,@P2 = {garments_count}
                                         ,@P3 = '{egrn}'
                                         ,@P4 = '{rescheduled_date}'
                                         ,@P5 = NULL
                                         ,@P6 = NULL
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
                                         ,@REC_ID = '0'"""

    # Calling the SP.
    db.engine.execute(text(query).execution_options(autocommit=True))

# def check_rewash_open_pickups(address_id, customer_id):
#     """
#     Function for getting the current open rewash pickups for a customer.
#     @param address_id: Address id.
#     @param customer_id: Customer id.
#     @return: If an existing pickup is present, return the dict result variable.
#     Otherwise dict variable with status False will be returned.
#     """

#     # If the pickup is rescheduled, then select reschedule's BranchCode, else BranchCode of
#     # the pickup request.
#     select_address_id = case([(PickupReschedule.CustAddressId == None, PickupRequest.CustAddressId), ],
#                              else_=PickupReschedule.CustAddressId).label("CustAddressId")

#     # Getting the open pickups from the DB.
#     open_pickups = db.session.query(PickupRequest.PickupRequestId, select_address_id,
#                                     CustomerAddres.CityCode).outerjoin(
#         PickupReschedule,
#         PickupRequest.PickupRequestId == PickupReschedule.PickupRequestId).join(CustomerAddres,
#                                                                                 CustomerAddres.CustAddressId == select_address_id).filter(
#         PickupRequest.CustomerId == customer_id,
#         PickupRequest.PickupSource == 'Rewash',
#         PickupRequest.IsCancelled == 0,
#         PickupRequest.PickupStatusId.in_(
#             (1, 2)), or_(PickupReschedule.IsDeleted == 0, PickupReschedule.IsDeleted == None)).all()

#     for open_pickup in open_pickups:
#         if open_pickup.CustAddressId == address_id:
#             # There's an open pickup found for the customer for
#             # the same address id.
#             return {'status': True, 'pickup_request_id': open_pickup.PickupRequestId}

#     # No open pickups have been found.
#     return {'status': False}

def check_rewash_open_pickups(address_id, customer_id):
    """
    Function for getting the current open rewash pickups for a customer.
    @param address_id: Address id.
    @param customer_id: Customer id.
    @return: If an existing pickup is present, return the dict result variable.
    Otherwise dict variable with status False will be returned.
    """

    # If the pickup is rescheduled, then select reschedule's BranchCode, else BranchCode of
    # the pickup request.
    select_address_id = case([(PickupReschedule.CustAddressId == None, PickupRequest.CustAddressId), ],
                             else_=PickupReschedule.CustAddressId).label("CustAddressId")

    # Getting the open pickups from the DB.
    open_pickups = db.session.query(PickupRequest.PickupRequestId, select_address_id,
                                    CustomerAddres.CityCode).outerjoin(
        PickupReschedule,
        PickupRequest.PickupRequestId == PickupReschedule.PickupRequestId).join(CustomerAddres,
                                                                                CustomerAddres.CustAddressId == select_address_id).filter(
        PickupRequest.CustomerId == customer_id,
        PickupRequest.PickupSource == 'Rewash',
        PickupRequest.IsCancelled == 0,
        PickupRequest.PickupStatusId.in_(
            (1, 2)), or_(PickupReschedule.IsDeleted == 0, PickupReschedule.IsDeleted == None)).all()
    pickups = []
    if len(open_pickups) > 1:
        for open_pickup in open_pickups:
            pickups.append(open_pickup.PickupRequestId)
        # open_pickups = {'pickups': pickups}
        log_data = {
            'multiple rewash open pickups': pickups
        }
        info_logger(f'Route: {request.path}').info(json.dumps(log_data))

    for open_pickup in open_pickups:
        return {'status': True, 'pickup_request_id': open_pickup.PickupRequestId}
        # if open_pickup.CustAddressId == address_id:
            # There's an open pickup found for the customer for
            # the same address id.
            

    # No open pickups have been found.
    return {'status': False}