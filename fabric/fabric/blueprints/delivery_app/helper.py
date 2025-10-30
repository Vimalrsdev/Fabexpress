"""
------------------------
The module consists helper functions that can be used by various modules in various scenarios.
------------------------
Coded by: Sivaprasad C
© Map My marketing LTD.
------------------------
"""
# import checksum generation utility
import json
import paytmchecksum
import inspect
from datetime import datetime, timedelta, date
import requests
from flask import request
from sqlalchemy import case, and_, func, literal, or_, String, cast
from fabric import db
from fabric.generic.classes import  CallSP
from fabric.generic.functions import get_current_date, get_today, generate_final_data
from fabric.modules.models import PickupReschedule, PickupRequest, CustomerAddres, Order, Customer, DeliveryUser, \
    PushNotification, DeliveryUserLogin, DeliveryUserBranch, Branch, DeliveryReschedule, DeliveryRequest, Delivery, \
    Area, DailyCompletedActivityCount, OrderInstruction, PriceList, City, Rankingcityinfo, DeliveryUserEDCDetail
from pyfcm import FCMNotification
from flask import current_app
from . import queries as delivery_controller_queries
from ...generic.classes import SerializeSQLAResult
from ...generic.loggers import error_logger
from fabric.generic.loggers import error_logger, info_logger
from ...settings.project_settings import sale_request_status_url
import calendar
import os
import firebase_admin
from firebase_admin import credentials, messaging


cred = credentials.Certificate(



)
firebase_admin.initialize_app(cred)



def send_push_notification_test(d_userid, activity, notification_img=None, source=None, sent_by=None):
    log_data = {'re-assign': '1'}
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))

    data = {}
    message_content = ''

    # Getting the activity counts to populate a string for sending via push notification
    d_user_branches = delivery_controller_queries.get_delivery_user_branches(d_userid, is_delivery=True)
    query = f"""EXEC JFSL.DBO.SPFabNotificationConsole @DUserID={d_userid}"""
    result = CallSP(query).execute().fetchall()
    total_pickup_count = result[0].get('PickUpCount')
    last_hour_pickup_count = result[0].get('Last1HrPickUpCount')
    total_delivery_count = result[0].get('DeliveryCount')
    last_hour_delivery_count = result[0].get('Last1HrDeliveryCount')
    log_data = {
        'result': result,
    }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))

    if not notification_img:
        notification_img = 'https://www.pinclipart.com/picdir/big/554-5546245_simple-character-and-a-hi-hi-sticker-for.png'

    data['image'] = notification_img

    # Getting the FCM token of the delivery user for sending push notification
    user_data = db.session.query(
        DeliveryUserLogin.FcmToken,
        DeliveryUser.UserName
    ).join(
        DeliveryUser, DeliveryUserLogin.DUserId == DeliveryUser.DUserId
    ).filter(
        DeliveryUserLogin.DUserId == d_userid,
        DeliveryUserLogin.FcmToken.isnot(None),
        DeliveryUserLogin.FcmToken != ''
    ).order_by(
        DeliveryUserLogin.DUserLoginId.desc()
    ).first()

    if user_data is None:
        return generate_final_data('CUSTOM_FAILED', 'FCM Token not available')

    if activity == 'DELIVERY':
        message_content = f"{user_data.UserName}, {last_hour_delivery_count} " \
                          f"Delivery(s) assigned to you.\n\nTotal Pending:\n" \
                          f"{total_delivery_count} Delivery(s)\n" \
                          f"{total_pickup_count} Pickup(s)"
    elif activity == 'PICKUP':
        message_content = f"{user_data.UserName}, {last_hour_pickup_count} Pickup(s)" \
                          f" assigned to you.\n\nTotal Pending:\n" \
                          f"{total_delivery_count} Delivery(s)\n" \
                          f"{total_pickup_count} Pickup(s)"

    message = messaging.Message(
        notification=messaging.Notification(
            title='Alert',
            body=message_content,
            image=notification_img,
        ),
        token=user_data.FcmToken,
        data=data
    )

    log_data = {'re-message': 'message', 'message_content': message_content}
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))

    try:
        response = messaging.send(message)
        new_push_notification = PushNotification(
            Message=message_content,
            DUserId=d_userid,
            IsRead=0,
            RecordCreatedDate=datetime.now(),
            RecordVersion=1,
            ImageUrl=notification_img,
            Source=source,
            SentBy=sent_by,
            IsActive=1,
            IsDeleted=0,
            Title='Alert'
        )
        db.session.add(new_push_notification)
        db.session.commit()
        log_data = {'re-message': response, 'new_push_notification': new_push_notification}
        info_logger(f'Route: {request.path}').info(json.dumps(log_data))
        return generate_final_data('SUCCESS')
    except firebase_admin._messaging_utils.SenderIdMismatchError as e:
        db.session.rollback()
        return generate_final_data('CUSTOM_FAILED', f'SenderId mismatch: {str(e)}')
    except Exception as e:
        db.session.rollback()
        return generate_final_data('CUSTOM_FAILED', f'Error sending notification: {str(e)}')


def check_paytm_payment_status(paytm_credentials, transaction_id, current_12_hr_time):
    """
    Func for checking the payment request is success or not
    """
    status = None
    try:
        checksum_body = {"paytmMid": paytm_credentials['MID'], "paytmTid": paytm_credentials['TID'],
                         "transactionDateTime": current_12_hr_time,
                         "merchantTransactionId": transaction_id
                         }
        checksum = checksum_generator(checksum_body, paytm_credentials['MerchantKey'])

        if checksum:
            headers = {
                'Content-Type': 'application/json'
            }
            body = {
                "head": {
                    "requestTimeStamp": current_12_hr_time, "channelId": "FAB", "checksum": checksum,
                    "version": "3.1"
                },
                "body": {
                    "paytmMid": paytm_credentials['MID'], "paytmTid": paytm_credentials['TID'],
                    "transactionDateTime": current_12_hr_time,
                    "merchantTransactionId": transaction_id
                }
            }

            response = requests.post(sale_request_status_url, data=json.dumps(body), headers=headers)
            response = json.loads(response.text)
            log_data = {
                'response': response

            }
            info_logger(f'Route: {request.path}').info(json.dumps(log_data))

            if response['body']['resultInfo']['resultStatus'] == "SUCCESS":

                status = "SUCCESS"

            else:
                status = "Payment not received"

        else:
            status = "Failed to generate checksum"

    except Exception as e:
        error_logger(f'Delivery helper: {inspect.stack()[0].function}()').error(e)

    log_data = {
        'status': status

    }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))

    return status


def get_paytm_credentials(d_user_id):
    """
    Func for getting paytm credentials such as merchant_id,  tid from DB
    """
    paytm_credentials = db.session.query(DeliveryUserEDCDetail.Tid,
                                         DeliveryUserEDCDetail.MerchantId,

                                         DeliveryUserEDCDetail.DeviceSerialNumber,
                                         DeliveryUserEDCDetail.MerchantKey).filter(
        DeliveryUserEDCDetail.DUserId == d_user_id, DeliveryUserEDCDetail.IsDeleted == 0).one_or_none()

    log_data = {
        'paytm_credentials': paytm_credentials
    }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))


    return {"MID": paytm_credentials.MerchantId, "TID": paytm_credentials.Tid,
            "SerialNumber": paytm_credentials.DeviceSerialNumber,
            "MerchantKey": paytm_credentials.MerchantKey} if paytm_credentials else None


def checksum_generator(checksum_body, merchant_key):
    """
    Function for generating and validating checksum
    """
    checksum = None

    try:
        # initialize JSON String
        # Generate checksum by parameters we have
        paytm_checksum = paytmchecksum.generateSignature(checksum_body, merchant_key)
        # Validating whether the checksum is valid or not
        is_valid_signature = paytmchecksum.verifySignature(checksum_body, merchant_key, paytm_checksum)

        checksum = paytm_checksum if is_valid_signature else None

    except Exception as e:
        error_logger(f'Delivery helper: {inspect.stack()[0].function}()').error(e)
    log_data = {
        'checksum': checksum
    }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))
    return checksum


def date_formatter(raw_date, date_only):
    """
    Function for converting date format retrieved through form
    """

    # Convert string date to datetime object.
    date_obj = datetime.strptime(raw_date, "%d-%m-%Y")
    if date_only:
        formatted_date = date_obj.strftime("%Y-%m-%d")
    else:
        # From the date object, convert the date to YYYY-MM-DD format.
        formatted_date = date_obj.strftime("%Y-%m-%d 00:00:00")

    return formatted_date


class PickupDetails:
    """
    Class of functions for counting pickup  on various aspects and passing pickups list to activity in list api
    """

    def __init__(self, user_id, ):
        self.tomorrow = (datetime.today() + timedelta(1)).strftime("%Y-%m-%d 00:00:00")
        self.current_date_time = datetime.now()
        self.last_hour_time = datetime.now() - timedelta(hours=1, minutes=1)
        self.user_id = user_id

        # If the pickup is rescheduled, then select reschedule's DuserId, else DUserId of
        # the pickup request.
        self.select_delivery_user_id = case([(PickupReschedule.DUserId == None, PickupRequest.DUserId), ],
                                            else_=PickupReschedule.DUserId).label("DUserId")

        # If Pickup is rescheduled, then take the RescheduledDate as PickupDate,
        # else, return the original PickupDate.
        self.select_pickup_date = case([(PickupReschedule.PickupRequestId == None, PickupRequest.PickupDate), ],
                                       else_=PickupReschedule.RescheduledDate).label("PickupDate")

        # If the pickup is rescheduled, then select reschedule's BranchCode, else BranchCode of
        # the pickup request.
        self.select_branch_code = case([(PickupReschedule.BranchCode == None, PickupRequest.BranchCode), ],
                                       else_=PickupReschedule.BranchCode).label("BranchCode")

    def pickup_count_query(self, delivery_user_branches):
        """
        function includes basic query of pickup count
        """

        # Base query for calculating pickup counts
        pickups_base_query = db.session.query(func.count(PickupRequest.PickupRequestId)).outerjoin(PickupReschedule,
                                                                                                   PickupRequest.PickupRequestId == PickupReschedule.PickupRequestId).outerjoin(
            Order, Order.PickupRequestId == PickupRequest.PickupRequestId).filter(
            self.select_delivery_user_id == self.user_id, PickupRequest.IsCancelled == 0,
            self.select_branch_code.in_(delivery_user_branches),
            or_(PickupReschedule.IsDeleted == 0, PickupReschedule.IsDeleted == None),
            or_(Order.IsDeleted == 0, Order.IsDeleted == None, and_(PickupRequest.IsReopen == 1, Order.ReOpenStatus == None)))

        return pickups_base_query

    def current_pickup_count(self, delivery_user_branches):
        """
        Function for calculating current pickup count
        """
        # Getting base query from pickup_count_query func
        current_pickup_query = self.pickup_count_query(delivery_user_branches)
        # Current pickup count
        current_pickup_count = current_pickup_query.filter(PickupRequest.PickupStatusId.in_((1, 2)),
                                                           self.select_pickup_date <= get_current_date()).scalar()
        return current_pickup_count

    def current_completed_pickup_count(self, delivery_user_branches):
        """
        Function for calculating completed pickup count
        """
        # Getting base query from pickup_count_query func
        current_completed_pickup_query = self.pickup_count_query(delivery_user_branches)

        current_completed_pickup_count = current_completed_pickup_query.filter(PickupRequest.PickupStatusId == 3, and_(
            PickupRequest.CompletedDate >= get_today(), PickupRequest.CompletedDate <= self.tomorrow)).scalar()

        return current_completed_pickup_count

    def last_hour_pickup_count(self, delivery_user_branches):
        """
        Function for calculating last hour assigned pickup count
        """
        # If Pickup is rescheduled, then take the RescheduledDate as PickupDate, else, return the original PickupDate.
        select_pickup_time = case(
            [(PickupReschedule.PickupRequestId == None, PickupRequest.RecordLastUpdatedDate), ],
            else_=PickupReschedule.RecordLastUpdatedDate).label("PickupDate")

        # Getting base query from pickup_count_query func
        current_pickup_query = self.pickup_count_query(delivery_user_branches)

        count = current_pickup_query.filter(PickupRequest.PickupStatusId.in_((1, 2)),
                                            select_pickup_time >= self.last_hour_time).scalar()
        return count

    def get_pending_pickups(self, tomorrow, select_activity_date, select_time_slot_from, select_time_slot_to, lat, long,
                            delivery_user_branches):
        """
        Getting the total pending pickups for tomorrow.
        @param tomorrow: Tomorrow's date.
        @param select_activity_date PickupDate of the pickup request.
        @param select_time_slot_from: TimeSlotFrom field.
        @param select_time_slot_to: TimeSlotTo field.
        @param lat Lat value of the delivery user.
        @param long Long value of the delivery user.
        @param delivery_user_branches: Associated branches of delivery user.
        @return: SQL Alchemy ORM result.
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

        # If the OrderId is NOT present in the Orders table, return 0, else return the value.
        select_order_id = case([(Order.OrderId == None, 0), ], else_=Order.OrderId).label("OrderId")

        # If the CouponCode is present in the PickupRequest or the Orders table, select CouponCode.
        select_booking_id = case([(PickupRequest.BookingId != None, PickupRequest.BookingId), ], else_="NA").label(
            "BookingId")

        # If the pickup is rescheduled, then select reschedule's address id, else address id of
        # the pickup request.
        select_address_id = case([(PickupReschedule.CustAddressId == None, PickupRequest.CustAddressId), ],
                                 else_=PickupReschedule.CustAddressId).label("CustAddressId")

        select_time_slot_id = case([(PickupReschedule.PickupTimeSlotId == None, PickupRequest.PickupTimeSlotId), ],
                                 else_=PickupReschedule.PickupTimeSlotId).label("TimeSlotId")

        # Selecting the order type.
        select_order_type = case([(cast(PickupRequest.PickupSource, String).label('OrderType') == "Adhoc", "Normal"),
                                  (cast(PickupRequest.PickupSource, String).label('OrderType') == 'Fabricare', "Normal"),
                                  (cast(PickupRequest.PickupSource, String).label('OrderType') == 'Rewash', "Rewash"),
                                  (cast(PickupRequest.PickupSource, String).label('OrderType') == 'Inbound Re', "Rewash"),
                                  (cast(PickupRequest.PickupSource, String).label('OrderType') == 'Outbound R', "Rewash")],
                                 else_=literal('Normal').label('OrderType')).label("OrderType")

        # Calculating the distance in KM between the delivery user's lat and long to
        # the customer address' lat and long.
        distance_in_km = func.dbo.GetDistance(lat, long, CustomerAddres.Lat, CustomerAddres.Long).label('Distance')
        select_branch_name = case([(Branch.DisplayName == '', Branch.BranchName), ],
                                  else_=Branch.DisplayName).label("BranchName")

        # Total pending pickup requests for the branch.
        base_query = db.session.query(literal('Pickup').label('ActivityType'),
                                      PickupRequest.PickupRequestId.label('ActivityId'), select_booking_id,
                                      select_order_id, literal('NA').label('EGRN'),
                                      literal('NA').label('Type'),
                                      select_address_id,select_time_slot_id,
                                      select_order_type, select_activity_date, select_time_slot_from,
                                      select_time_slot_to, self.select_delivery_user_id,
                                      DeliveryUser.UserName.label('DeliveryUser'), Customer.CustomerCode,
                                      Customer.CustomerName, Customer.MobileNo, literal(False).label('MonthlyCustomer'),
                                      select_discount_code, select_coupon_code, CustomerAddres.AddressLine1,
                                      select_address_line_2, select_address_line_3, self.select_branch_code,
                                      CustomerAddres.Lat, CustomerAddres.Long, distance_in_km, case([(Branch.IsActive == 0, 'Inact - ' + select_branch_name)],
                                               else_=select_branch_name).label('BranchName')).join(Customer,
                                                                                                    PickupRequest.CustomerId == Customer.CustomerId).outerjoin(
            PickupReschedule, PickupReschedule.PickupRequestId == PickupRequest.PickupRequestId).join(CustomerAddres,
                                                                                                      select_address_id == CustomerAddres.CustAddressId).join(
            DeliveryUser, self.select_delivery_user_id == DeliveryUser.DUserId).outerjoin(Order,
                                                                                          Order.PickupRequestId == PickupRequest.PickupRequestId).outerjoin(Branch, Branch.BranchCode == self.select_branch_code)

        # Select all the details based on given branch code(s).
        pending_pickups = base_query.filter(self.select_branch_code.in_(delivery_user_branches))

        if tomorrow is not None:
            # tomorrow date is given. So select only for the tomorrow's records.
            pending_pickups = pending_pickups.filter(
                or_(Order.IsDeleted == 0, Order.IsDeleted == None, and_(PickupRequest.IsReopen == 1, Order.ReOpenStatus == None)),
                PickupRequest.IsCancelled == 0, PickupRequest.PickupStatusId.in_((1, 2)),
                select_activity_date == tomorrow,
                self.select_delivery_user_id == self.user_id,
                or_(PickupReschedule.IsDeleted == 0, PickupReschedule.IsDeleted == None))
        else:
            # Normal pending pickups up to current date.
            pending_pickups = pending_pickups.filter(
                or_(Order.IsDeleted == 0, Order.IsDeleted == None, and_(PickupRequest.IsReopen == 1, Order.ReOpenStatus == None)),
                PickupRequest.IsCancelled == 0, PickupRequest.PickupStatusId.in_((1, 2)),
                select_activity_date <= get_current_date(),
                self.select_delivery_user_id == self.user_id,
                or_(PickupReschedule.IsDeleted == 0, PickupReschedule.IsDeleted == None))

        return pending_pickups

    """_____________________________DELIVERY SECTION______________________________"""


class DeliveryDetails:
    """
    Class of functions for counting deliveries  on various aspects and passing delivery list to activity in list api
    """

    def __init__(self, user_id):
        self.tomorrow = (datetime.today() + timedelta(1)).strftime("%Y-%m-%d 00:00:00")
        self.current_date_time = datetime.now()
        self.last_hour_time = datetime.now() - timedelta(hours=1, minutes=1)
        self.user_id = user_id

        # If the delivery is rescheduled, then select RescheduledDate, else select DeliveryDate.
        self.select_delivery_date = case([(DeliveryReschedule.RescheduledDate == None, DeliveryRequest.DeliveryDate), ],
                                         else_=DeliveryReschedule.RescheduledDate).label("DeliveryDate")

        # If the delivery is rescheduled, then select reschedules DUserId, else DUserId of the delivery request.
        self.select_delivery_user_id = case([(DeliveryReschedule.DUserId == None, DeliveryRequest.DUserId), ],
                                            else_=DeliveryReschedule.DUserId).label("DUserId")

    def delivery_count_query(self, delivery_user_branches):
        """
        function includes basic query of delivery count
        """
        # Base query for calculating delivery count
        delivery_base_query = db.session.query(func.count(DeliveryRequest.DeliveryRequestId)).outerjoin(
            DeliveryReschedule, DeliveryReschedule.DeliveryRequestId == DeliveryRequest.DeliveryRequestId).outerjoin(
            Delivery, DeliveryRequest.DeliveryRequestId == Delivery.DeliveryRequestId).join(Order,
                                                                                            DeliveryRequest.OrderId == Order.OrderId).filter(
            self.select_delivery_user_id == self.user_id,
            or_(DeliveryReschedule.IsDeleted == 0, DeliveryReschedule.IsDeleted == None),
            DeliveryRequest.BranchCode.in_(delivery_user_branches))

        return delivery_base_query




    def current_delivery_count(self, delivery_user_branches):
        """
        Function for calculating current_delivery_count
        """
        # Getting base query from delivery_count_query func
        current_delivery_query = self.delivery_count_query(delivery_user_branches)

        current_delivery_count = current_delivery_query.filter(DeliveryRequest.IsDeleted == 0,
                                                               Delivery.DeliveryId == None,
                                                               or_(Order.IsDeleted == 0, Order.IsDeleted == None),
                                                               self.select_delivery_date <= get_current_date()).scalar()

        return current_delivery_count

    # def current_completed_delivery_count(self, delivery_user_branches):
    #     """
    #     Function for calculating current completed delivery count
    #     """
    #     # Getting base query from delivery_count_query func
    #     completed_delivery_query = self.delivery_count_query(delivery_user_branches)

    #     completed_delivery_count = completed_delivery_query.filter(Delivery.DeliveryId != None,
    #                                                                and_(DeliveryRequest.CompletedDate >= get_today(),
    #                                                                     DeliveryRequest.CompletedDate <= self.tomorrow)).scalar()

    #     return completed_delivery_count

    def current_completed_delivery_count(self, delivery_user_branches):
        """
        Function for calculating current completed delivery count
        """
        # Getting base query from delivery_count_query func
        completed_delivery_query = self.delivery_count_query(delivery_user_branches)
        
        from sqlalchemy import and_

        completed_delivery_count = completed_delivery_query.filter(
            Delivery.DeliveryId != None,
            and_(
                DeliveryRequest.CompletedDate >= get_today(),
                DeliveryRequest.CompletedDate <= self.tomorrow,
                DeliveryRequest.DeliveryRequestId.in_(
                    db.session.query(Delivery.DeliveryRequestId)
                    .filter(Delivery.PaymentStatus == 'Paid')
                )
            )
        ).scalar()

        return completed_delivery_count




    def last_hour_delivery_count(self, delivery_user_branches):
        """
        Function for calculating current completed delivery count
        """
        # If the delivery is rescheduled, then select RescheduledDate, else select DeliveryDate.
        select_delivery_time = case(
            [(DeliveryReschedule.RescheduledDate == None, DeliveryRequest.RecordLastUpdatedDate), ],
            else_=DeliveryReschedule.RecordLastUpdatedDate).label("DeliveryDate")

        # Getting base query from delivery_count_query func
        last_hour_delivery_query = self.delivery_count_query(delivery_user_branches)

        # Number of delivery requests in last hour
        last_hour_delivery_count = last_hour_delivery_query.filter(DeliveryRequest.IsDeleted == 0,
                                                                   Delivery.DeliveryId == None,
                                                                   select_delivery_time >= self.last_hour_time).scalar()

        return last_hour_delivery_count

    def get_pending_deliveries(self, tomorrow, select_activity_date, select_time_slot_from, select_time_slot_to, lat,
                               long, delivery_user_branches, delivery_type):
        """
        API  for getting the tomorrow's pending delivery activities for the user.
        @param tomorrow: Tomorrow's date.
        @param select_activity_date DeliveryDate of the delivery request.
        @param select_time_slot_from: TimeSlotFrom field.
        @param select_time_slot_to: TimeSlotTo field.
        @param lat Lat value of the delivery user.
        @param lat Long value of the delivery user.
        @param delivery_user_branches: Associated branches of delivery user.
        @return: SQL Alchemy ORM result.
        """
        # Total delivery requests for the branch.

        select_discount_code = case([(Order.DiscountCode != None, Order.DiscountCode), ], else_="NA").label(
            "DiscountCode")

        # If the CouponCode is present in the PickupRequest or the Orders table, select CouponCode.
        select_coupon_code = case([(Order.CouponCode != None, Order.CouponCode), ], else_="NA").label("CouponCode")

        # If the CouponCode is present in the PickupRequest or the Orders table, select CouponCode.
        select_booking_id = case([(DeliveryRequest.BookingId != None, DeliveryRequest.BookingId), ], else_="NA").label(
            "BookingId")

        # If the address line 2 is not present, then select NA.
        select_address_line_2 = case([(CustomerAddres.AddressLine2 == None, "NA"), ],
                                     else_=CustomerAddres.AddressLine2).label("AddressLine2")

        # If the address line 3 is not present, then select NA.
        select_address_line_3 = case([(CustomerAddres.AddressLine3 == None, "NA"), ],
                                     else_=CustomerAddres.AddressLine3).label("AddressLine3")

        # If the delivery is rescheduled, then select reschedule's address id, else address id of
        # the delivery request.
        select_address_id = case([(DeliveryReschedule.CustAddressId == None, DeliveryRequest.CustAddressId), ],
                                 else_=DeliveryReschedule.CustAddressId).label("CustAddressId")

        select_time_slot_id = case([(DeliveryReschedule.DeliveryTimeSlotId == None, DeliveryRequest.DeliveryTimeSlotId), ],
                                 else_=DeliveryReschedule.DeliveryTimeSlotId).label("TimeSlotId")

        # Calculating the distance in KM between the delivery user's lat and long to
        # the customer address' lat and long.
        distance_in_km = func.dbo.GetDistance(lat, long, CustomerAddres.Lat, CustomerAddres.Long).label('Distance')

        # Selecting the order type.
        select_order_type = case([(cast(Order.OrderTypeId, String).label('OrderType') == None, "Normal"),
                                  (cast(Order.OrderTypeId, String).label('OrderType') == 1, "Normal"),
                                  (cast(Order.OrderTypeId, String).label('OrderType') == 2, "Rewash"), ],
                                 else_=literal('NA').label('OrderType')).label("OrderType")

        select_delivery_type = case([(cast(DeliveryRequest.BookingId, String).label('Type') == None, "Walkin")],
                                     else_=literal('D2D').label('Type')).label("Type")

        #  Set MonthlyCustomer is false when MonthlyCustomer is Null or 0 else true
        select_monthly_customer = case(
            [(or_(Customer.MonthlyCustomer == None, Customer.MonthlyCustomer != 1), 'False'), ],
            else_=Customer.MonthlyCustomer).label("MonthlyCustomer")
        select_branch_name = case([(Branch.DisplayName == '', Branch.BranchName), ],
                                  else_=Branch.DisplayName).label("BranchName")

        base_query = db.session.query(literal('Delivery').label('ActivityType'),
                                      DeliveryRequest.DeliveryRequestId.label('ActivityId'), select_booking_id,
                                      Order.OrderId, Order.EGRN,
                                      select_delivery_type,
                                      select_address_id, select_time_slot_id,
                                      select_order_type, select_activity_date,
                                      select_time_slot_from, select_time_slot_to, self.select_delivery_user_id,
                                      DeliveryUser.UserName.label('DeliveryUser'), Customer.CustomerCode,
                                      Customer.CustomerName, Customer.MobileNo, select_monthly_customer,
                                      select_discount_code, select_coupon_code, CustomerAddres.AddressLine1,
                                      select_address_line_2, select_address_line_3, DeliveryRequest.BranchCode,
                                      CustomerAddres.Lat, CustomerAddres.Long, distance_in_km, select_branch_name).join(Customer,
                                                                                                    DeliveryRequest.CustomerId == Customer.CustomerId).outerjoin(
            DeliveryReschedule, DeliveryReschedule.DeliveryRequestId == DeliveryRequest.DeliveryRequestId).join(Order,
                                                                                                                DeliveryRequest.OrderId == Order.OrderId).join(
            CustomerAddres, select_address_id == CustomerAddres.CustAddressId).join(DeliveryUser,
                                                                                    self.select_delivery_user_id == DeliveryUser.DUserId).outerjoin(
            Delivery, Delivery.DeliveryRequestId == DeliveryRequest.DeliveryRequestId).outerjoin(Branch, Branch.BranchCode == DeliveryRequest.BranchCode)

        if delivery_type == 'd2d':

            # Select all the details based on given branch code(s).
            pending_deliveries = base_query.filter(DeliveryRequest.BranchCode.in_(delivery_user_branches),
                                                   or_(DeliveryRequest.WalkIn == 0, DeliveryRequest.WalkIn == None),
                                                   DeliveryRequest.BookingId != None)
        elif delivery_type == 'walkin':
            # Select all the details based on given branch code(s).
            pending_deliveries = base_query.filter(DeliveryRequest.BranchCode.in_(delivery_user_branches),
                                                   or_(DeliveryRequest.WalkIn == 0, DeliveryRequest.WalkIn == None, DeliveryRequest.WalkIn == 1),
                                                   DeliveryRequest.BookingId == None)
        else:
            # Select all the details based on given branch code(s).
            pending_deliveries = base_query.filter(DeliveryRequest.BranchCode.in_(delivery_user_branches),
                                                   or_(DeliveryRequest.WalkIn == 0, DeliveryRequest.WalkIn == None, DeliveryRequest.WalkIn == 1))


        if tomorrow is not None:
            # tomorrow date is given. So select only for the tomorrow's records.
            pending_deliveries = pending_deliveries.filter(
                or_(Order.IsDeleted == 0, Order.IsDeleted == None),
                self.select_delivery_user_id == self.user_id, DeliveryRequest.IsDeleted == 0,
                Delivery.DeliveryId == None, select_activity_date == tomorrow,
                or_(DeliveryReschedule.IsDeleted == 0, DeliveryReschedule.IsDeleted == None))
        else:
            # Normal pending pickups up to current date.
            pending_deliveries = pending_deliveries.filter(
                or_(Order.IsDeleted == 0, Order.IsDeleted == None),
                self.select_delivery_user_id == self.user_id, DeliveryRequest.IsDeleted == 0,
                Delivery.DeliveryId == None, select_activity_date <= get_current_date(),
                or_(DeliveryReschedule.IsDeleted == 0, DeliveryReschedule.IsDeleted == None))

        return pending_deliveries


def send_push_notification(d_userid, activity, notification_img, source=None, sent_by=None):
    """
    Function for sending push notification to the user whenever a delivery is rescheduled and scheduled
    """
    # if there is no image send only the click action else both
    data = {}
    message_content = ''

    # Getting the activity counts to populate a string for sending via push notification
    d_user_branches = delivery_controller_queries.get_delivery_user_branches(d_userid, is_delivery=True)

    total_pickup_count = PickupDetails(d_userid).current_pickup_count(d_user_branches)
    last_hour_pickup_count = PickupDetails(d_userid).last_hour_pickup_count(d_user_branches)

    total_delivery_count = DeliveryDetails(d_userid).current_delivery_count(d_user_branches)
    last_hour_delivery_count = DeliveryDetails(d_userid).last_hour_delivery_count(d_user_branches)

    notification_img = 'https://www.pinclipart.com/picdir/big/554-5546245_simple-character-and-a-hi-hi-sticker-for.png'

    if notification_img != '':
        data['image'] = notification_img
        data['click_action'] = 'FLUTTER_NOTIFICATION_CLICK'
    else:
        data['click_action'] = 'FLUTTER_NOTIFICATION_CLICK'

    # Getting the FCM key for sending push notification
    push_service = FCMNotification(api_key=current_app.config['FCM_KEY'])

    # Getting the fcm token of the delivery user for sending push notification
    user_data = db.session.query(DeliveryUserLogin.FcmToken, DeliveryUser.UserName).join(DeliveryUser,
                                                                                         DeliveryUserLogin.DUserId == DeliveryUser.DUserId).filter(
        DeliveryUserLogin.DUserId == d_userid,
        and_(DeliveryUserLogin.FcmToken != 'NULL', DeliveryUserLogin.FcmToken != '')).order_by(
        DeliveryUserLogin.DUserLoginId.desc()).first()

    if user_data is not None:

        if activity == 'DELIVERY':
            # Formatting the message for sending via push notification if delivery
            message_content = f"{user_data.UserName}, {last_hour_delivery_count} " \
                              f"Delivery(s) assigned to you. \n\n Total Pending: \n {total_delivery_count}" \
                              f" Delivery(s)\n {total_pickup_count} Pickup(s)"

        elif activity == 'PICKUP':
            # Formatting the message for sending via push notification if pickup
            message_content = f"{user_data.UserName}, {last_hour_pickup_count} Pickup(s)" \
                              f" assigned to you. \n\nTotal Pending: \n{total_delivery_count} " \
                              f" Delivery(s)\n{total_pickup_count}   Pickup(s) "
        # invoke push notification
        send_notification = push_service.notify_single_device(user_data.FcmToken,
                                                              message_title='Alert',
                                                              message_body=message_content, data_message=data)

        if send_notification['success']:
            # If notification send successfully save that details to table
            new_push_notification = PushNotification(
                Message=message_content,
                DUserId=d_userid,
                IsRead=0,
                RecordCreatedDate=get_current_date(),
                RecordVersion=1,
                ImageUrl=str(notification_img),
                Source=source,
                SentBy=sent_by,
                IsActive=1,
                IsDeleted=0,
                Title='Alert'
            )
            db.session.add(new_push_notification)
            db.session.commit()

            result = generate_final_data('SUCCESS')
        else:
            result = generate_final_data('CUSTOM_FAILED', 'Failed to send notification')
    else:
        result = generate_final_data('CUSTOM_FAILED', 'FCM Token not available')

    return result



def send_test_push_notification(d_userid, title, message, image_url):
    """
    Function for sending test push notifications to delivery users
    """
    # if there is no image send only the click action else both
    data = {}

    if image_url != '':
        data['image'] = image_url
        data['click_action'] = 'FLUTTER_NOTIFICATION_CLICK'
    else:
        data['click_action'] = 'FLUTTER_NOTIFICATION_CLICK'

    # Getting the FCM key for sending push notification
    push_service = FCMNotification(api_key=current_app.config['FCM_KEY'])

    # Getting the fcm token of the delivery user for sending push notification
    user_data = db.session.query(DeliveryUserLogin.FcmToken).filter(DeliveryUserLogin.DUserId == d_userid,
                                                                    and_(DeliveryUserLogin.FcmToken != 'NULL',
                                                                         DeliveryUserLogin.FcmToken != '')).order_by(
        DeliveryUserLogin.DUserLoginId.desc()).first()

    if user_data is not None:
        # invoke push notification
        send_notification = push_service.notify_single_device(user_data.FcmToken, message_title=title,
                                                              message_body=message, data_message=data)

        if send_notification['success']:
            # If notification send successfully save that details to table
            new_push_notification = PushNotification(
                Message=message,
                DUserId=d_userid,
                IsRead=0,
                RecordCreatedDate=get_current_date(),
                RecordVersion=1,
                ImageUrl=str(image_url),
                Source='API_CALL',
                SentBy=None,
                IsActive=1,
                IsDeleted=0,
                Title=title
            )
            db.session.add(new_push_notification)
            db.session.commit()

            result = generate_final_data('SUCCESS')
        else:
            result = generate_final_data('CUSTOM_FAILED', 'Failed to send notification')
    else:
        result = generate_final_data('CUSTOM_FAILED', 'FCM Token not available')

    return result


def first_3_activity_dict(raw_list, count_type):
    """
    Func for getting first 3 ranked users delete others
    """
    if len(raw_list) > 3:
        try:
            # getting last index of DUser rank data with third rank
            first_rank_last_index = [index for index, k in enumerate(raw_list) if k['rank'] == 3]

            if first_rank_last_index:
                first_rank_last_index = first_rank_last_index[-1]

                # Delete rank data after rank 3
                del raw_list[first_rank_last_index + 1:]
            # Removing delivery user rank data with delivery count 0
            raw_list = [obj for obj in raw_list if obj[count_type] != 0]

        except Exception as e:
            error_logger(f'Delivery helper: {inspect.stack()[0].function}()').error(e)

    return raw_list


def get_city_rank_list(city_code_list, sort_by, date_range):
    """
    Function for getting rank list of the given rank city
    """

    # Getting first day of the current month
    month_first_day = datetime.today().replace(day=1).strftime("%Y-%m-%d")
    today = date.today()
    activities = None
    # Base query for calculating activity count for a selected period
    activity_base_query = db.session.query(DailyCompletedActivityCount.Id, DailyCompletedActivityCount.DUserId,
                                           DeliveryUser.DUserImage, DeliveryUser.UserName,
                                           DailyCompletedActivityCount.DeliveryCount,
                                           DailyCompletedActivityCount.PickupCount,
                                           DailyCompletedActivityCount.PickupRevenue,
                                           DailyCompletedActivityCount.DeliveryRevenue).join(DeliveryUser,
                                                                                             DailyCompletedActivityCount.DUserId == DeliveryUser.DUserId).filter(
        DeliveryUser.IsDeleted == 0, DailyCompletedActivityCount.IsDeleted == 0,
        DailyCompletedActivityCount.CityCode.in_(city_code_list))

    if date_range:
        if date_range == "TopRank":
            # If current date is first day of month take rank list of previous month else rank list of previous day
            if today.day == 1:
                # Getting current month count
                if today.month == 1:
                    # Getting first day of previous month
                    month_first_day = datetime.today().replace(day=1, month=12, year=int(
                        int(datetime.now().strftime("%Y")) - 1)).strftime("%Y-%m-%d")
                else:
                    # Getting first day of previous month
                    month_first_day = datetime.today().replace(day=1, month=int(
                        int(datetime.now().strftime("%m")) - 1)).strftime("%Y-%m-%d")
                # Convert month first day to date format
                date_formatted_month_first_day = datetime.strptime(month_first_day, "%Y-%m-%d")
                # Getting last day of previous month
                month_last_date = calendar.monthrange(date_formatted_month_first_day.year,
                                                      date_formatted_month_first_day.month)[1]
                # assign last day of previous month as var today
                today = datetime.strptime(month_first_day, "%Y-%m-%d").replace(day=month_last_date).strftime("%Y-%m-%d")
                sort_by = "Month"

            else:
                sort_by = "Today"
                # Assign yesterday as today
                today = (datetime.today() - timedelta(1)).strftime("%Y-%m-%d")

        else:
            today = date_formatter(date_range, True)
            # getting 1 st day of selected month
            month_first_day = datetime.strptime(today, "%Y-%m-%d").replace(day=1).strftime("%Y-%m-%d")

    if sort_by == "Today":
        # Getting delivery & pickup counts DB belongs to the delivery user's same city code of today
        activities = activity_base_query.filter(DailyCompletedActivityCount.CompletedDate == today).all()

    elif sort_by == "Month":
        # Getting delivery & pickup counts DB belongs to the delivery user's same city code of the last month
        activities = activity_base_query.filter(
            DailyCompletedActivityCount.CompletedDate.between(month_first_day, today)).all()

    activities = SerializeSQLAResult(activities).serialize()

    return activities


def calculate_ranks(actual_list, count_category, revenue_category):
    """
    Function for making rank of delivery users same if same activity count and same revenue
    """
    rank, previous_revenue, previous_count = 1, -1, -1

    for index, data in enumerate(actual_list):
        if previous_count != -1 and previous_revenue != -1:
            if previous_count == data[count_category]:
                if previous_revenue == data[revenue_category]:
                    data["rank"] = rank
                else:
                    rank = index + 1
                    data["rank"] = rank
            else:
                rank = index + 1
                data["rank"] = rank
        else:
            data["rank"] = rank

        previous_revenue = data[revenue_category]
        previous_count = data[count_category]

    return actual_list


def find_rank_by_revenue(raw_list, activity_type):
    """
    func to calculate rank if multiple users with same delivery count take revenue as ranking parameter ,
    if same revenue split rank to both
    """
    index = 0
    loop_index = -1
    result_list = []
    user_id = request.headers.get('user-id')
    count_category = 'PickupCount' if activity_type == 'Pickup' else 'DeliveryCount'

    for item in raw_list:
        loop_index += 1
        if loop_index >= index:
            current_count = item[count_category]
            # Getting users with same activity count
            same_count_users = [list_item for list_item in raw_list if list_item[count_category] == current_count]
            # Sorting rank list by revenue earned
            same_count_users.sort(key=lambda obj: obj['Revenue'], reverse=True)
            result_list.extend(same_count_users)
            index += len(same_count_users)

    result_list = calculate_ranks(result_list, count_category, 'Revenue')
    # Getting index of current delivery users activity details
    d_user_activity_index = next((index for index, item in enumerate(result_list) if item["DUserId"] == int(user_id)),
                                 None)
    if d_user_activity_index:
        # Extracting activity data of the corresponding delivery user
        d_user_activity_data = result_list[d_user_activity_index]

        # Index where the first delivery user match same delivery count & revenue of the current user
        first_same_occurrence_index = next((index for index, item in enumerate(result_list) if
                                            item[count_category] == d_user_activity_data[count_category] and item[
                                                'Revenue'] == d_user_activity_data['Revenue']), None)

        if d_user_activity_index != first_same_occurrence_index:
            # Swapping data of current user and user whose activity count and revenue matches with current user
            result_list[first_same_occurrence_index], result_list[d_user_activity_index] = result_list[
                                                                                               d_user_activity_index], \
                                                                                           result_list[
                                                                                               first_same_occurrence_index]

    return result_list


def rank_list(is_d_user, sort_by, user_id_or_city_code, is_for_console=False, date_range=False, is_report=False):
    """
    Function for finding rank list of all active delivery users of the same city code of delivery user
    """

    delivery_rank_list = []
    pickup_rank_list = []
    ordered_delivery_rank_list = []
    ordered_pickup_rank_list = []

    try:
        if is_for_console:
            activities = get_city_rank_list(user_id_or_city_code, sort_by, date_range)
        else:

            # Getting delivery user branches of corresponding delivery user
            d_user_branches = delivery_controller_queries.get_delivery_user_branches(user_id_or_city_code)
            # Getting city code from DB
            city_code = db.session.query(Rankingcityinfo.RankingCity).distinct(Rankingcityinfo.RankingCity).join(Area,
                                                                                                                 Area.CityCode == Rankingcityinfo.CityCode).join(
                Branch, Branch.AreaCode == Area.AreaCode).filter(Branch.BranchCode.in_(d_user_branches)).all()
            # Populating a list of CityCode's
            city_code_list = [obj.RankingCity for obj in city_code]
            # log_data = {
            #     'city_code_list': city_code_list
            # }
            # info_logger(f'Route: {request.path}').info(json.dumps(log_data))
            activities = get_city_rank_list(city_code_list, sort_by, date_range)
        # Removing duplicates from Delivery user id
        delivery_users = set(obj['DUserId'] for obj in activities)

        for d_user in delivery_users:
            d_user_activity = []

            for index, obj2 in enumerate(activities):

                if obj2['DUserId'] == d_user:
                    d_user_activity.append(obj2)

                if index + 1 == len(activities):

                    delivery_count, pickup_count, delivery_revenue, pickup_revenue = 0, 0, 0, 0

                    for activity in d_user_activity:
                        delivery_count += activity['DeliveryCount']
                        pickup_count += activity['PickupCount']
                        pickup_revenue += 0 if activity['PickupRevenue'] is None else round(activity['PickupRevenue'])
                        delivery_revenue += 0 if activity['DeliveryRevenue'] is None else round(
                            activity['DeliveryRevenue'])

                    delivery_rank_list.append(
                        {"DeliveryUserName": d_user_activity[0]['UserName'], "DUserId": d_user_activity[0]['DUserId'],
                         "DeliveryCount": delivery_count, "FileName": d_user_activity[0]['DUserImage'],
                         "Revenue": delivery_revenue})

                    pickup_rank_list.append(
                        {"DeliveryUserName": d_user_activity[0]['UserName'], "DUserId": d_user_activity[0]['DUserId'],
                         "PickupCount": pickup_count, "FileName": d_user_activity[0]['DUserImage'],
                         "Revenue": pickup_revenue})

    except Exception as e:
        error_logger(f'Delivery helper: {inspect.stack()[0].function}()').error(e)

    my_rank_dict = {}
    delivery_rank_list_with_0 = []
    final_delivery_rank_list = []
    pickup_rank_list_with_0 = []
    final_pickup_rank_list = []
    result = {}
    store_rank_list = []

    try:
        # Append to delivery_rank_list_without_0 if delivery count is not 0 else append to delivery_rank_list_with_0
        [final_delivery_rank_list.append(i) if i['DeliveryCount'] != 0 else delivery_rank_list_with_0.append(i) for
         i in delivery_rank_list]
        # Sort delivery_rank_list_with_0 by DeliveryUserName
        delivery_rank_list_with_0.sort(key=lambda obj: obj['DeliveryUserName'].casefold())
        # Sorting the delivery_rank_list_without_0 based on DeliveryCount
        final_delivery_rank_list.sort(key=lambda obj: obj['DeliveryCount'], reverse=True)
        # Extend the delivery_rank_list_without_0 with delivery_rank_list_with_0
        final_delivery_rank_list.extend(delivery_rank_list_with_0)

        # Append to pickup_rank_list_without_0 if delivery count is not 0 else append to pickup_rank_list_with_0
        [final_pickup_rank_list.append(i) if i['PickupCount'] != 0 else pickup_rank_list_with_0.append(i) for i in
         pickup_rank_list]
        # Sort pickup_rank_list_with_0 by DeliveryUserName
        pickup_rank_list_with_0.sort(key=lambda obj: obj['DeliveryUserName'].casefold())
        # Sorting the pickup_rank_list_without_0 based on PickupCount
        final_pickup_rank_list.sort(key=lambda obj: obj['PickupCount'], reverse=True)
        # Extend the pickup_rank_list_without_0 with pickup_rank_list_with_0
        final_pickup_rank_list.extend(pickup_rank_list_with_0)
        # Calling func to calculate rank if multiple users with same delivery count take revenue as ranking parameter ,
        # if same revenue split rank to both
        final_delivery_rank_list = find_rank_by_revenue(final_delivery_rank_list, 'Delivery')
        final_pickup_rank_list = find_rank_by_revenue(final_pickup_rank_list, 'Pickup')

        # Looping delivery_list & pickup_list concurrently to insert rank to delivery user
        # If a specific delivery user rank is to be calculated
        if is_d_user:
            # If a specific delivery user rank is to be calculated
            ordered_delivery_rank_list = [
                {"DeliveryCount": delivery_data['DeliveryCount'], "DeliveryRank": delivery_data['rank'],
                 "Revenue": delivery_data['Revenue']} for delivery_data in final_delivery_rank_list if
                user_id_or_city_code == delivery_data['DUserId']]

            ordered_pickup_rank_list = [{"PickupCount": pickup_data['PickupCount'], "PickupRank": pickup_data['rank'],
                                         "Revenue": pickup_data['Revenue']} for pickup_data in
                                        final_pickup_rank_list if user_id_or_city_code == pickup_data['DUserId']]

        else:
            if is_report is False:
                ordered_delivery_rank_list = list(final_delivery_rank_list)

                ordered_pickup_rank_list = list(final_pickup_rank_list)

                if is_for_console is False and user_id_or_city_code:
                    # Getting current user rank details
                    pickup_my_rank_list = [
                        {"DUserId": pickup['DUserId'], "DeliveryUserName": pickup['DeliveryUserName'],
                         "PickupCount": pickup['PickupCount'], "PickupRank": pickup['rank'],
                         "FileName": pickup['FileName'], "PickupRevenue": pickup['Revenue'], } for pickup in
                        final_pickup_rank_list if user_id_or_city_code == pickup['DUserId']]

                    delivery_my_rank_list = [
                        {"DeliveryCount": delivery_data['DeliveryCount'], "DeliveryRank": delivery_data['rank'],
                         "DeliveryRevenue": delivery_data['Revenue']} for delivery_data in
                        final_delivery_rank_list if user_id_or_city_code == delivery_data['DUserId']]
                    # Joining dictionaries inside pickup_my_rank_list & delivery_my_rank_list
                    my_rank_dict = {**pickup_my_rank_list[0], **delivery_my_rank_list[0]}

            else:
                # Remove FileName while generating report in console
                for delivery_data, pickup_data in zip(final_delivery_rank_list, final_pickup_rank_list):
                    del delivery_data['FileName'], pickup_data['FileName']

                ordered_delivery_rank_list = list(final_delivery_rank_list)
                ordered_pickup_rank_list = list(final_pickup_rank_list)

        if is_for_console and is_report is False:

            for pickup_d_user in ordered_pickup_rank_list:
                # Appending store_rank_list if d user id matches
                next(store_rank_list.append({"DUserName": obj['DeliveryUserName'],
                                             "DUserBranches": delivery_controller_queries.get_delivery_user_branch_names(
                                                 obj['DUserId']), "PickupCount": pickup_d_user['PickupCount'],
                                             "PickupRank": pickup_d_user['rank'],
                                             "PickupRevenue": pickup_d_user['Revenue'],
                                             "DeliveryCount": obj['DeliveryCount'],
                                             "DeliveryRevenue": obj['Revenue'], "DeliveryRank": obj['rank']})
                     for obj in ordered_delivery_rank_list if obj["DUserId"] == pickup_d_user['DUserId'])

            # Clearing list
            ordered_pickup_rank_list.clear()
            # Store list values of store_rank_list to ordered_pickup_rank_list
            ordered_pickup_rank_list = list(store_rank_list)

    except Exception as e:
        error_logger(f'Delivery helper: {inspect.stack()[0].function}()').error(e)
    # Adding pickup_rank_list & delivery_rank_list to result
    result['PickupRankList'] = ordered_pickup_rank_list
    result['DeliveryRankList'] = ordered_delivery_rank_list
    result['MyRank'] = my_rank_dict

    return result


def add_instruction(order_id, order_garment_id, instruction_id):
    """
    Function for adding instruction to a garment
    """
    try:

        new_instruction = OrderInstruction(OrderId=order_id, OrderGarmentId=order_garment_id,
                                           InstructionId=instruction_id, IsDeleted=0)
        db.session.add(new_instruction)
        db.session.commit()

    except Exception as e:
        db.session.rollback()
        error_logger(f'Delivery helper: {inspect.stack()[0].function}()').error(e)


def get_garment_price(garment_id, serv_type_id, serv_tat_id, branch_code):
    """
    Function for getting garment price from DB
    """
    # Getting garment price from DB
    price = db.session.query(PriceList.Price, PriceList.Id).filter(PriceList.GarmentId == garment_id,
                                                                   PriceList.ServiceTypeId == serv_type_id,
                                                                   PriceList.ServiceTatId == serv_tat_id,
                                                                   PriceList.BranchCode == branch_code,
                                                                   PriceList.IsActive == 1,
                                                                   PriceList.IsDeleted == 0).one_or_none()
    return price
