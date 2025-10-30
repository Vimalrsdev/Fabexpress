import json
from datetime import datetime, timedelta
from sqlalchemy import case, func, literal, text, or_, and_, desc, asc
import requests
from sqlalchemy import case, literal, or_, and_, func, cast, String
from fabric.generic.classes import CallSP
from fabric.modules.settings.project_settings import CURRENT_ENV
from fabric.settings.project_settings import SERVER_DB, ICE_CUBES_SMS_API, ICE_CUBES_TRANSACTIONAL_SMS_API_KEY, \
    ICE_CUBES_SENDER, ALERT_ENGINE_DB
from fabric import db
from fabric.generic.functions import get_today, get_current_date
from fabric.modules import common as common_module
from fabric.modules.models import StoreUserBranch, PickupRequest, CustomerAddres, PickupReschedule, PickupTimeSlot, \
    Customer, DeliveryUser, Order, DeliveryRequest, DeliveryReschedule, Delivery, StoreUser, Branch, \
    StoreUserAttendance, State, Area, City, DeliveryGarment, OrderGarment, CustomerTimeSlot, TransactionInfo, TravelLog
from sqlalchemy.orm import aliased
from fabric.generic.loggers import error_logger, info_logger
import requests

from flask import Blueprint, request, current_app, redirect, send_from_directory


# Edited by MMM
def send_sms_after_set_customer_preferred_day(customer_code, day):
    """
    Function for sending SMS after a successful delivery  using Ice Cubes Transactional SMS service.
    """
    # If anny day is selected change the day string
    day = "Any day in a week" if day == 'Any Day' else day

    # Getting customer details from DB
    # customer_details = db.session.query(Customer.CustomerName, Customer.MobileNo).filter(
    #     Customer.CustomerCode == customer_code, Customer.IsActive == 1, Customer.IsDeleted == 0, ).one_or_none()
    customer_details = db.session.execute(
    text(
        "SELECT ContactNo, FirstName FROM JFSL.dbo.CustomerInfo (nolock) WHERE CustomerCode = :CustomerCode"
    ),
    {"CustomerCode": customer_code}
    ).fetchone()

    if customer_details:
        ContactNo = customer_details[0]
        FirstName = customer_details[1]

    # Making a text to send via SMS
    message = f"Hi {FirstName}, Your future orders at fabricspa will be delivered on {day} as per " \
              f"your request. For any changes or query reach us on 18001234664 "

    if CURRENT_ENV == 'development':
        # Send SMS using Ice Cubes Transactional SMS service.
        api_url = f'{ICE_CUBES_SMS_API}/?api_key={ICE_CUBES_TRANSACTIONAL_SMS_API_KEY}&method=sms&to={ContactNo}&sender={ICE_CUBES_SENDER}&message={message}'
        requests.get(api_url)

    # SP Query for checking the the customer is subscribed for whatsapp notification
    query = f"EXEC {SERVER_DB}.dbo.[USP_CHECK_IF_OPTIN_FOR_WHATSAPP] @CUSTOMERCODE={customer_code}"

    result = CallSP(query).execute().fetchone()
    # If subscribed send whatsapp message
    if result['ISOPTIN']:
        # Calling Sp for sending whatsapp notification
        query = f"EXEC {ALERT_ENGINE_DB}..ALERT_PROCESS @ALERT_CODE = 'FUTURE_DELIVERY_WHATSAPP', @EMAIL_ID= NULL, " \
                f"@MOBILE_NO= {ContactNo}, @SUBJECT= NULL, @DISPATCH_FLAG= 'OFF', @EMAIL_SENDER_ADD= " \
                f"NULL, @SMS_SENDER_ADD= NULL, @P1= {ContactNo}, " \
                f"@P2= '{FirstName}', @P3= '{day}', @P4= '18001234664', @P5= NULL, @P6= NULL, " \
                f"@P7= NULL, @P8= NULL, @P9= NULL, @P10= NULL, @P11= NULL, @P12= NULL, @P13= NULL, @P14= NULL, " \
                f"@P15= NULL, @P16= NULL, @P17= NULL, @P18= NULL, @P19= NULL, @P20= NULL, @REC_ID= '0' "

        CallSP(query).execute()


def get_customer_preferred_delivery_from_db(filter_type, filter_by):
    """
    Api for getting details of customer from db if no data retrieved from sp
    """
    customer_data = None
    # Base query for getting the customer details
    base_query = db.session.query(Customer.CustomerId, Customer.CustomerCode, Customer.CustomerName,
                                  Customer.MobileNo).filter(Customer.IsActive == 1, Customer.IsDeleted == 0)

    # If filter type is CUSTOMER_CODE
    if filter_type == 'CUSTOMER_CODE':
        # Filter on the base of customer code
        customer_data = base_query.filter(Customer.CustomerCode == filter_by).all()

    # If filter type is MOBILE_NUMBER
    elif filter_type == 'MOBILE_NUMBER':
        # Filter on the base of mobile number
        customer_data = base_query.filter(Customer.MobileNo == filter_by).all()

    # Make customer data if none customer found
    customer_data = [] if customer_data is None else customer_data

    if len(customer_data) > 0:
        # Getting the first instance from the customer_data queryset according to index
        customer_data = customer_data[0]
        # Getting the customer address based on customer id
        customer_address = db.session.query(CustomerAddres.AddressLine1, CustomerAddres.AddressLine2,
                                            CustomerAddres.AddressLine3).filter(
            CustomerAddres.CustomerId == customer_data[0], CustomerAddres.IsDeleted == 0,
            CustomerAddres.IsActive == 1).all()

        delivery_address = ''
        permanent_address = ''
        index = 0
        # Looping the customer address
        for address in customer_address:
            # Assume the first row of customer address as delivery address
            if index == 0:
                delivery_address = address.AddressLine1 or "NA" + address.AddressLine2 or "NA" + address.AddressLine3 or "NA"
            # Assume the second row of customer address as permanent address
            elif index == 1:
                permanent_address = address.AddressLine1 or "NA" + address.AddressLine2 or "NA" + address.AddressLine3 or "NA"
            # Increment the value of index
            index += 1
        # Store the details from customer address and customer details to the result list
        result = [{
            "CUSTOMERCODE": customer_data[1], "NAME": customer_data[2], "CONTACTNO": customer_data[3],
            "DELIVERYADDRESS": delivery_address, "PERMANANTADDRESS": permanent_address, "CREATEDDATE": None,
            "CREATEDBY": None, "MODIFIEDDATE": None, "MODIFIEDBY": None, "ISLOCAL": True
        }]
    else:
        result = []

    return result


def get_customer_preferred_delivery(filter_type, filter_by):
    """
    Function for getting the details of customer preferred delivery date
    """
    query = None
    # If filter type is CUSTOMER_CODE
    if filter_type == 'CUSTOMER_CODE':
        # Calling Sp according with customer code
        query = f"EXEC {SERVER_DB}.dbo.[USP_GET_CUSTOMER_PREFERRED_DELIVERY_DAY] @CUSTOMERCODE={filter_by}"

    # If filter type is MOBILE_NUMBER
    elif filter_type == 'MOBILE_NUMBER':
        # Calling Sp according with mobile number
        query = f"EXEC {SERVER_DB}.dbo.[USP_GET_CUSTOMER_PREFERRED_DELIVERY_DAY] @CONTACTNO={filter_by}"

    # check if customer_code and mobile_number is none if none return all the result
    elif filter_type is None and filter_type is None:
        # Calling SP without parameters returns all data
        query = f"EXEC {SERVER_DB}.dbo.[USP_GET_CUSTOMER_PREFERRED_DELIVERY_DAY]"

    # Store result of sp to variable
    result = CallSP(query).execute().fetchall()

    if result is not None:
        for data in result:
            data['ISLOCAL'] = False

    # Make result none if no customer found
    result = [] if result is None else result

    return result


def set_customer_preferred_day(day, time_slot, customer_code, action, user_id):
    """
    Function for creating customer preferred delivery date of a delivery
    """
    # Getting store user name from DB
    store_user = db.session.query(StoreUser.UserName).filter(StoreUser.SUserId == user_id, StoreUser.IsActive == 1,
                                                             StoreUser.IsDeleted == 0).one_or_none()
    # passing the parameters to the SP
    query = f"EXEC {SERVER_DB}.dbo.[USP_UPDATE_CUSTOMER_PREFERRED_DELIVERY_DAY_FROM_FABXPRESS] @CUSTOMERCODE={customer_code}, @DAY='{day}', @ACTION='{action}', @UPDATEDBY='{store_user.UserName}', @DELIVERYTIMESLOT={time_slot}"

    # Store result of sp to variable
    result = CallSP(query).execute().fetchone()
    db.session.commit()

    return result['RESULT']


# Edited by MMM
def get_store_user_branches_uat(user_id, state_codes=None, city_codes=None, allow_inactive=True):
    """
    Function for getting the branch codes of store users.
    @param user_id:,
    @param state_codes: List of state codes.
    @param allow_inactive:
    @param city_codes: List of city codes.
    @return: list of branch codes associated with the user.
    If no branches are found, empty will be returned.
    """
    allow_inactive = True
    store_user_branches = []
    store_user = db.session.query(StoreUser).filter(StoreUser.SUserId == user_id).one_or_none()
    if store_user is not None:
        if store_user.IsAdmin:
            base_query = db.session.query(Branch.BranchCode).distinct(Branch.BranchCode)

            # If the state codes are given, state codes need to be considered.
            if state_codes:
                base_query = base_query.join(Area, Branch.AreaCode == Area.AreaCode).join(City,
                                                                                          Area.CityCode == City.CityCode).join(
                    State, City.StateCode == State.StateCode).filter(State.StateCode.in_(state_codes))

            # If the city codes are given, city codes need to be considered.
            if city_codes:
                if state_codes:
                    base_query = base_query.filter(City.CityCode.in_(city_codes))
                else:

                    base_query = base_query.join(Area, Branch.AreaCode == Area.AreaCode).join(City,
                                                                                              Area.CityCode == City.CityCode).filter(
                        City.CityCode.in_(city_codes))

            if allow_inactive:
                store_user_branches = base_query.filter(Branch.IsDeleted == 0).all()
            else:
                store_user_branches = base_query.filter(Branch.IsDeleted == 0,
                                                        Branch.IsActive == 1).all()

        else:
            # Store user is a normal store user/zonal in charge.
            # Getting the branches associated with the store user.
            base_query = db.session.query(StoreUserBranch.BranchCode)

            # If the state codes are given, state codes need to be considered.
            if state_codes:
                base_query = base_query.join(Branch, StoreUserBranch.BranchCode == Branch.BranchCode).join(Area,
                                                                                                           Branch.AreaCode == Area.AreaCode).join(
                    City,
                    Area.CityCode == City.CityCode).join(
                    State, City.StateCode == State.StateCode).filter(State.StateCode.in_(state_codes))

            # If the city codes are given, city codes need to be considered.
            if city_codes:
                if state_codes:
                    base_query = base_query.filter(City.CityCode.in_(city_codes))
                else:

                    base_query = base_query.join(Branch, StoreUserBranch.BranchCode == Branch.BranchCode).join(Area,
                                                                                                               Branch.AreaCode == Area.AreaCode).join(
                        City,
                        Area.CityCode == City.CityCode).filter(
                        City.CityCode.in_(city_codes))

            store_user_branches = base_query.filter(
                StoreUserBranch.SUserId == user_id, StoreUserBranch.IsDeleted == 0).all()

    # Populating the list of branch codes.
    branch_codes = [store_user_branch.BranchCode for store_user_branch in store_user_branches]

    return branch_codes

def get_store_user_branches(user_id, state_codes=None, city_codes=None, allow_inactive=True):
    """
    Function for getting the branch codes of store users.
    @param user_id:,
    @param state_codes: List of state codes.
    @param allow_inactive:
    @param city_codes: List of city codes.
    @return: list of branch codes associated with the user.
    If no branches are found, empty will be returned.
    """
    allow_inactive = True
    store_user_branches = []
    store_user = db.session.query(StoreUser).filter(StoreUser.SUserId == user_id).one_or_none()
    if store_user is None:
        return []

    branch_dtls = f"EXEC JFSL.dbo.SPFabStoreBranchInfo @store_user_id = '{user_id}'"

    result = CallSP(branch_dtls).execute().fetchall()
    branch_codes = [row['BranchCode'] for row in result]  # Corrected fetchall() usage

    return branch_codes



def get_completed_pickups(record_created_date, store_user_branches):
    """
    Function for retrieving the completed pickups.
    @param record_created_date: Saved date of the pickup.
    @param interval_start_date: 1-7 (in days).
    @param store_user_branches: List of associated branch codes. Return the result from these branches only.
    @return: Completed pickups (SQLA result).
    """

    # If the discount code is not applied, select NA.
    select_discount_code = case([(Order.DiscountCode == None, "NA"), ],
                                else_=Order.DiscountCode).label("DiscountCode")

    # If the coupon code is not applied, select NA.
    # select_coupon_code = case([(PickupRequest.CouponCode == None, "NA"), ],
    #                           else_=PickupRequest.CouponCode).label("CouponCode")
    select_coupon_code = case([(and_(Order.CouponCode != None, Order.CouponCode != ''), Order.CouponCode)],
                              else_='NA', ).label("CouponCode")

    # If the address line 2 is not present, then select NA.
    select_address_line_2 = case([(CustomerAddres.AddressLine2 == None, "NA"), ],
                                 else_=CustomerAddres.AddressLine2).label("AddressLine2")

    # If the address line 3 is not present, then select NA.
    select_address_line_3 = case([(CustomerAddres.AddressLine3 == None, "NA"), ],
                                 else_=CustomerAddres.AddressLine3).label("AddressLine3")

    # if interval_start_date is not None:
    #     # Here, a day interval is specified. So select the details from the start date and current date.
    #     interval_condition_check = and_(PickupRequest.CompletedDate < get_current_date(),
    #                                     PickupRequest.CompletedDate > interval_start_date)
    # else:
    #     # No interval day is specified.
    #     interval_condition_check = PickupRequest.CompletedDate < get_current_date()

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

    # If the Order Remarks is NULL, select NA.
    select_order_remarks = case([(Order.Remarks == None, "NA"), ],
                                else_=Order.Remarks).label("Remarks")

    # If the pickup is rescheduled, then select RescheduledDate, else select PickupDate.
    select_activity_date = case([(PickupReschedule.RescheduledDate == None, PickupRequest.PickupDate), ],
                                else_=PickupReschedule.RescheduledDate).label("ActivityDate")

    # Check if the activity is a walk in or D2D.
    select_activity_category = case([(Order.PickupRequestId == None, literal('Walk-In').label('ActivityCategory')), ],
                                    else_=literal('D2D').label('ActivityCategory')).label("ActivityCategory")

    # If a DisplayName found for a branch, then select DisplayName as the BranchName.
    select_branch_name = case(
        [(or_(Branch.DisplayName == None, Branch.DisplayName == ''), Branch.BranchName), ],
        else_=Branch.DisplayName).label("BranchName")

    select_delivery_charge = case([
        (Order.DeliveryCharge == None, "NA"),
        (Order.DeliveryCharge == 0, "YES"),
        (Order.DeliveryCharge == 1, "NO")
    ]).label("DeliveryCharge")

    # Total completed pickups for the branch.
    completed_pickups = db.session.query(literal('Pickup').label('ActivityType'),
                                         select_activity_category,
                                         select_activity_date,
                                         PickupRequest.BookingId, Order.OrderId, Order.EGRN,
                                         select_time_slot_from,
                                         select_time_slot_to,
                                         select_delivery_user_id,
                                         DeliveryUser.UserName.label('DeliveryUser'), Customer.CustomerId,
                                         Customer.CustomerCode,
                                         Customer.CustomerName,
                                         Customer.MobileNo,
                                         select_discount_code, select_coupon_code, CustomerAddres.AddressLine1,
                                         select_address_line_2, select_address_line_3,
                                         record_created_date, select_order_remarks, select_branch_code,
                                         select_branch_name, select_delivery_charge).join(Customer,
                                                                                          PickupRequest.CustomerId == Customer.CustomerId).outerjoin(
        PickupReschedule,
        PickupReschedule.PickupRequestId == PickupRequest.PickupRequestId).join(
        CustomerAddres, select_address_id == CustomerAddres.CustAddressId).join(
        DeliveryUser,
        select_delivery_user_id == DeliveryUser.DUserId).outerjoin(
        Order,
        Order.PickupRequestId == PickupRequest.PickupRequestId).join(Branch,
                                                                     select_branch_code == Branch.BranchCode).filter(
        or_(Order.IsDeleted == 0, Order.IsDeleted == None),
        PickupRequest.IsCancelled == 0, PickupRequest.PickupStatusId == 3,
        # interval_condition_check,
        select_branch_code.in_(store_user_branches),
        select_delivery_user_id != None, Order.OrderId != None,
        or_(PickupReschedule.IsDeleted == 0, PickupReschedule.IsDeleted == None)
    )

    return completed_pickups



def get_completed_deliveries(record_created_date, store_user_branches):
    """
    Function for retrieving the completed deliveries.
    @param record_created_date: Saved date of the delivery details.
    @param interval_start_date: 1-7 (in days).
    @param store_user_branches: List of associated branch codes. Return the result from these branches only.
    @return: completed deliveries (SQLA result).
    """

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

    # if interval_start_date is not None:
    #     # Here, an day interval is specified. So select the details from the start date and current date.
    #     interval_condition_check = and_(Delivery.RecordCreatedDate < get_current_date(),
    #                                     Delivery.RecordCreatedDate > interval_start_date)
    # else:
    #     # No interval day is specified.
    #     interval_condition_check = Delivery.RecordCreatedDate < get_current_date()
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

    # If the Delivery Remarks is NULL, select NA.
    select_delivery_remarks = case([(Delivery.Remarks == None, "NA"), ],
                                   else_=Delivery.Remarks).label("Remarks")

    # If the delivery is rescheduled, then select RescheduledDate, else select DeliveryDate.
    select_activity_date = case([(DeliveryReschedule.RescheduledDate == None, DeliveryRequest.DeliveryDate), ],
                                else_=DeliveryReschedule.RescheduledDate).label("ActivityDate")

    # Check if the activity is a walk in or D2D.
    select_activity_category = case([(Order.PickupRequestId == None, literal('Walk-In').label('ActivityCategory')), ],
                                    else_=literal('D2D').label('ActivityCategory')).label("ActivityCategory")

    # If a DisplayName found for a branch, then select DisplayName as the BranchName.
    select_branch_name = case(
        [(or_(Branch.DisplayName == None, Branch.DisplayName == ''), Branch.BranchName), ],
        else_=Branch.DisplayName).label("BranchName")
    select_delivery_charge = case([
        (Order.DeliveryCharge == None, "NA"),
        (Order.DeliveryCharge == 0, "YES"),
        (Order.DeliveryCharge == 1, "NO")
    ]).label("DeliveryCharge")

    completed_deliveries = db.session.query(literal('Delivery').label('ActivityType'),
                                            select_activity_category,
                                            select_activity_date,
                                            select_booking_id, Order.OrderId, Order.EGRN,
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
                                            select_address_line_2, select_address_line_3, record_created_date,
                                            select_delivery_remarks, Delivery.BranchCode, select_branch_name,
                                            select_delivery_charge
                                            ).select_from(Delivery).join(Customer,
                                                                         Delivery.CustomerId == Customer.CustomerId).outerjoin(
        DeliveryReschedule, DeliveryReschedule.DeliveryRequestId == Delivery.DeliveryRequestId).join(
        Order,
        Delivery.OrderId == Order.OrderId).join(
        CustomerAddres, Delivery.DeliveryAddressId == CustomerAddres.CustAddressId).join(
        DeliveryUser,
        Delivery.DUserId == DeliveryUser.DUserId).outerjoin(DeliveryRequest,
                                                            Delivery.DeliveryRequestId == DeliveryRequest.DeliveryRequestId).join(
        Branch, Delivery.BranchCode == Branch.BranchCode).filter(
        or_(Order.IsDeleted == 0, Order.IsDeleted == None),
        DeliveryRequest.WalkIn == 0,
        Delivery.DUserId != None, Delivery.BranchCode.in_(store_user_branches),
        Delivery.DeliveryId != None,
        # interval_condition_check,
        or_(DeliveryReschedule.IsDeleted == 0, DeliveryReschedule.IsDeleted == None))

    return completed_deliveries


##--no lat and long
def get_completed_pickups_fromdate_todateb4LatLong(record_created_date, formatted_from_date, formatted_to_date,
                                              store_user_branches):
    """
    Function for retrieving the completed pickups.
    @param formatted_to_date:
    @param formatted_from_date:
    @param record_created_date: Saved date of the pickup.
    @param store_user_branches: List of associated branch codes. Return the result from these branches only.
    @return: Completed pickups (SQLA result).
    """

    # If the discount code is not applied, select NA.
    select_discount_code = case([(Order.DiscountCode == None, "NA"), ],
                                else_=Order.DiscountCode).label("DiscountCode")

    # If the coupon code is not applied, select NA.
    # select_coupon_code = case([(PickupRequest.CouponCode == None, "NA"), ],
    #                           else_=PickupRequest.CouponCode).label("CouponCode")
    select_coupon_code = case([(and_(Order.CouponCode != None, Order.CouponCode != ''), Order.CouponCode)],
                              else_='NA', ).label("CouponCode")

    # If the address line 2 is not present, then select NA.
    select_address_line_2 = case([(CustomerAddres.AddressLine2 == None, "NA"), ],
                                 else_=CustomerAddres.AddressLine2).label("AddressLine2")

    # If the address line 3 is not present, then select NA.
    select_address_line_3 = case([(CustomerAddres.AddressLine3 == None, "NA"), ],
                                 else_=CustomerAddres.AddressLine3).label("AddressLine3")

    if formatted_from_date < formatted_to_date:
        # Here, a day interval is specified. So select the details from the from_date and to date.
        interval_condition_check = and_(PickupRequest.CompletedDate < formatted_to_date,
                                        PickupRequest.CompletedDate > formatted_from_date)


    elif formatted_from_date == formatted_to_date:
        f = datetime.strptime(formatted_to_date, "%Y-%m-%d %H:%M:%S")
        formatted_to_date = f + timedelta(1)
        interval_condition_check = and_(PickupRequest.CompletedDate >= formatted_from_date,
                                        PickupRequest.CompletedDate < formatted_to_date
                                        )

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

    # If the Order Remarks is NULL, select NA.
    select_order_remarks = case([(Order.Remarks == None, "NA"), ],
                                else_=Order.Remarks).label("Remarks")

    # If the pickup is rescheduled, then select RescheduledDate, else select PickupDate.
    # select_activity_date = case([(PickupReschedule.RescheduledDate == None, PickupRequest.PickupDate), ],
    #                             else_=PickupReschedule.RescheduledDate).label("ActivityDate")

    # Check if the activity is a walk in or D2D.
    select_activity_category = case([(Order.PickupRequestId == None, literal('Walk-In').label('ActivityCategory')), ],
                                    else_=literal('D2D').label('ActivityCategory')).label("ActivityCategory")

    # If a DisplayName found for a branch, then select DisplayName as the BranchName.
    select_branch_name = case(
        [(or_(Branch.DisplayName == None, Branch.DisplayName == ''), Branch.BranchName), ],
        else_=Branch.DisplayName).label("BranchName")

    select_payment_status_with_na = literal('NA')
    select_payment_status = select_payment_status_with_na.label('PaymentStatus')

    Delivered_pickup = literal("NA")
    Delivered_pickups = Delivered_pickup.label('DeliveredOn')
    amount_dtls = literal(0).label('Amount')
    payable = literal('NA').label('PaymentCollectedBy')

    # Total completed pickups for the branch.
    completed_pickups = db.session.query(literal('Pickup').label('ActivityType'),
                                         select_activity_category,
                                         PickupRequest.CompletedDate,
                                         PickupRequest.BookingId, Order.OrderId, Order.EGRN,
                                         select_time_slot_from,
                                         select_time_slot_to,
                                         select_delivery_user_id,
                                         DeliveryUser.UserName.label('DeliveryUser'), Customer.CustomerId,
                                         Customer.CustomerCode,
                                         Customer.CustomerName,
                                         Customer.MobileNo,
                                         select_discount_code, select_coupon_code, CustomerAddres.AddressLine1,
                                         select_address_line_2, select_address_line_3,
                                         record_created_date, select_order_remarks, select_branch_code,
                                         select_branch_name, literal('NO').label('Is OTP sent?'),
                                         amount_dtls, select_payment_status,
                                         Delivered_pickups, payable).join(Customer,
                                                                          PickupRequest.CustomerId == Customer.CustomerId).outerjoin(
        PickupReschedule,
        PickupReschedule.PickupRequestId == PickupRequest.PickupRequestId).join(
        CustomerAddres, select_address_id == CustomerAddres.CustAddressId).join(
        DeliveryUser,
        select_delivery_user_id == DeliveryUser.DUserId).outerjoin(
        Order,
        Order.PickupRequestId == PickupRequest.PickupRequestId).join(Branch,
                                                                     select_branch_code == Branch.BranchCode).filter(
        or_(Order.IsDeleted == 0, Order.IsDeleted == None),
        PickupRequest.IsCancelled == 0, PickupRequest.PickupStatusId == 3,
        interval_condition_check,
        select_branch_code.in_(store_user_branches),
        select_delivery_user_id != None, Order.OrderId != None, Delivery.PaymentStatus == 'Paid',
        or_(PickupReschedule.IsDeleted == 0, PickupReschedule.IsDeleted == None)
    )

    return completed_pickups

def get_completed_deliveries_fromdate_todateb4LatLong(record_created_date, formatted_from_date, formatted_to_date,
                                                 store_user_branches):
    """
    Function for retrieving the completed deliveries.
    @param record_created_date: Saved date of the delivery details.
    @param interval_start_date: 1-7 (in days).
    @param store_user_branches: List of associated branch codes. Return the result from these branches only.
    @return: completed deliveries (SQLA result).
    """
    print("hai")
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

    if formatted_from_date < formatted_to_date:
        # Here, an day interval is specified. So select the details from the start date and current date.
        interval_condition_check = and_(Delivery.RecordCreatedDate < formatted_to_date,
                                        Delivery.RecordCreatedDate > formatted_from_date)
    elif formatted_from_date == formatted_to_date:

        f = datetime.strptime(formatted_to_date, "%Y-%m-%d %H:%M:%S")
        formatted_to_date = f + timedelta(1)
        interval_condition_check = and_(
            Delivery.RecordCreatedDate >= formatted_from_date,
            Delivery.RecordCreatedDate <= formatted_to_date)

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

    # If the Delivery Remarks is NULL, select NA.
    select_delivery_remarks = case([(Delivery.Remarks == None, "NA"), ],
                                   else_=Delivery.Remarks).label("Remarks")

    # If the delivery is rescheduled, then select RescheduledDate, else select DeliveryDate.
    # select_activity_date = case([(DeliveryReschedule.RescheduledDate == None, DeliveryRequest.DeliveryDate), ],
    #                             else_=DeliveryReschedule.RescheduledDate).label("ActivityDate")

    # Check if the activity is a walk in or D2D.
    select_activity_category = case([(Order.PickupRequestId == None, literal('Walk-In').label('ActivityCategory')), ],
                                    else_=literal('D2D').label('ActivityCategory')).label("ActivityCategory")

    # If a DisplayName found for a branch, then select DisplayName as the BranchName.
    select_branch_name = case(
        [(or_(Branch.DisplayName == None, Branch.DisplayName == ''), Branch.BranchName), ],
        else_=Branch.DisplayName).label("BranchName")

    select_payment_status = case([(Delivery.PaymentFlag == 0, literal('Delivered-Paid'))],
                                 else_=literal('Paid')).label('PaymentStatus')

    otp_dtls = case([(Delivery.DeliveryWithoutOtp == 0, 'YES')], else_='NO').label('IsOTPSent')

    select_date = case([(TransactionInfo.PaymentCompletedOn.is_(None), "NA")],
                       else_=cast(TransactionInfo.PaymentCompletedOn, String)).label('CompletedDate')
    

    amount_dtls = case([(TransactionInfo.TotalPayableAmount.is_(None), 0)],
                       else_=TransactionInfo.TotalPayableAmount).label('Amount')
    # payable = case([(TransactionInfo.PaymentCollectedBY.is_(None), 'NA')],
    #                else_=TransactionInfo.PaymentCollectedBY).label('PaymentCollectedBY')
    payment_collected_by_case = case(
        [
            (TransactionInfo.PaymentSource == 'delivery', DeliveryUser.UserName)
        ],
        else_=TransactionInfo.PaymentSource
    ).label('PaymentCollectedBy')
    


    completed_deliveries = db.session.query(literal('Delivery').label('ActivityType'),
                                            select_activity_category,
                                            DeliveryRequest.CompletedDate.label('DeliveredOn'),
                                            select_booking_id, Order.OrderId, Order.EGRN,
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
                                            select_address_line_2, select_address_line_3, record_created_date,
                                            select_delivery_remarks, Delivery.BranchCode, select_branch_name, otp_dtls,
                                            amount_dtls, select_payment_status, select_date, payment_collected_by_case).select_from(
        Delivery).join(Customer,
                       Delivery.CustomerId == Customer.CustomerId).outerjoin(
        DeliveryReschedule, DeliveryReschedule.DeliveryRequestId == Delivery.DeliveryRequestId).join(
        Order,
        Delivery.OrderId == Order.OrderId).join(
        CustomerAddres, Delivery.DeliveryAddressId == CustomerAddres.CustAddressId).join(
        DeliveryUser,
        Delivery.DUserId == DeliveryUser.DUserId).outerjoin(DeliveryRequest,
                                                            Delivery.DeliveryRequestId == DeliveryRequest.DeliveryRequestId).join(
        Branch, Delivery.BranchCode == Branch.BranchCode).outerjoin(
        TransactionInfo, TransactionInfo.EGRNNo == Delivery.EGRN).filter(
        or_(Order.IsDeleted == 0, Order.IsDeleted == None),
        DeliveryRequest.WalkIn == 0,
        Delivery.DUserId != None, Delivery.BranchCode.in_(store_user_branches),
        Delivery.DeliveryId != None, Delivery.PaymentStatus == 'Paid',
        interval_condition_check,
        or_(DeliveryReschedule.IsDeleted == 0, DeliveryReschedule.IsDeleted == None))
    # print("end")
    # log_data = {
    #     'completed_deliveries :': completed_deliveries
    # }
    # info_logger(f'Route: {request.path}').info(json.dumps(log_data))

    return completed_deliveries


## ---no lat long

def get_completed_pickups_fromdate_todate_orginal(record_created_date, formatted_from_date, formatted_to_date,
                                              store_user_branches):
    """
    Function for retrieving the completed pickups.
    @param formatted_to_date:
    @param formatted_from_date:
    @param record_created_date: Saved date of the pickup.
    @param store_user_branches: List of associated branch codes. Return the result from these branches only.
    @return: Completed pickups (SQLA result).
    """

    # If the discount code is not applied, select NA.
    select_discount_code = case([(Order.DiscountCode == None, "NA"), ],
                                else_=Order.DiscountCode).label("DiscountCode")

    # If the coupon code is not applied, select NA.
    # select_coupon_code = case([(PickupRequest.CouponCode == None, "NA"), ],
    #                           else_=PickupRequest.CouponCode).label("CouponCode")
    select_coupon_code = case([(and_(Order.CouponCode != None, Order.CouponCode != ''), Order.CouponCode)],
                              else_='NA', ).label("CouponCode")

    # If the address line 2 is not present, then select NA.
    select_address_line_2 = case([(CustomerAddres.AddressLine2 == None, "NA"), ],
                                 else_=CustomerAddres.AddressLine2).label("AddressLine2")

    # If the address line 3 is not present, then select NA.
    select_address_line_3 = case([(CustomerAddres.AddressLine3 == None, "NA"), ],
                                 else_=CustomerAddres.AddressLine3).label("AddressLine3")

    if formatted_from_date < formatted_to_date:
        # Here, a day interval is specified. So select the details from the from_date and to date.
        interval_condition_check = and_(PickupRequest.CompletedDate < formatted_to_date,
                                        PickupRequest.CompletedDate > formatted_from_date)


    elif formatted_from_date == formatted_to_date:
        f = datetime.strptime(formatted_to_date, "%Y-%m-%d %H:%M:%S")
        formatted_to_date = f + timedelta(1)
        interval_condition_check = and_(PickupRequest.CompletedDate >= formatted_from_date,
                                        PickupRequest.CompletedDate < formatted_to_date
                                        )

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

    # If the Order Remarks is NULL, select NA.
    select_order_remarks = case([(Order.Remarks == None, "NA"), ],
                                else_=Order.Remarks).label("Remarks")

    # If the pickup is rescheduled, then select RescheduledDate, else select PickupDate.
    # select_activity_date = case([(PickupReschedule.RescheduledDate == None, PickupRequest.PickupDate), ],
    #                             else_=PickupReschedule.RescheduledDate).label("ActivityDate")

    # Check if the activity is a walk in or D2D.
    select_activity_category = case([(Order.PickupRequestId == None, literal('Walk-In').label('ActivityCategory')), ],
                                    else_=literal('D2D').label('ActivityCategory')).label("ActivityCategory")

    # If a DisplayName found for a branch, then select DisplayName as the BranchName.
    select_branch_name = case(
        [(or_(Branch.DisplayName == None, Branch.DisplayName == ''), Branch.BranchName), ],
        else_=Branch.DisplayName).label("BranchName")

    select_payment_status_with_na = literal('NA')
    select_payment_status = select_payment_status_with_na.label('PaymentStatus')

    Delivered_pickup = literal("NA")
    Delivered_pickups = Delivered_pickup.label('DeliveredOn')
    amount_dtls = literal(0).label('Amount')
    payable = literal('NA').label('PaymentCollectedBy')

    # Total completed pickups for the branch.
    completed_pickups = db.session.query(literal('Pickup').label('ActivityType'),
                                         select_activity_category,
                                         PickupRequest.CompletedDate,
                                         PickupRequest.BookingId, Order.OrderId, Order.EGRN,
                                         select_time_slot_from,
                                         select_time_slot_to,
                                         select_delivery_user_id,
                                         DeliveryUser.UserName.label('DeliveryUser'), Customer.CustomerId,
                                         Customer.CustomerCode,
                                         Customer.CustomerName,
                                         Customer.MobileNo,
                                         func.concat(CustomerAddres.Lat, ',', CustomerAddres.Long).label(
                                                'Customer Lat & Long'), func.concat(Branch.Lat, ',', Branch.Long).label('Store Lat & LONG'),
                                         func.concat(TravelLog.Lat, ',', TravelLog.Long).label('Pickup/Delivery Lat & Long'),
                                         select_discount_code, select_coupon_code, CustomerAddres.AddressLine1,
                                         select_address_line_2, select_address_line_3,
                                         record_created_date, select_order_remarks, select_branch_code,
                                         select_branch_name, literal('NO').label('Is OTP sent?'),
                                         amount_dtls, select_payment_status,
                                         Delivered_pickups, payable, (PickupRequest.distance).label('P-up/Del Location to Customer Distance'), (PickupRequest.store_distance).label(
                                             'P-up/Del Location to Store Distance')).join(Customer,
                                                                          PickupRequest.CustomerId == Customer.CustomerId).outerjoin(
        PickupReschedule,
        PickupReschedule.PickupRequestId == PickupRequest.PickupRequestId).join(
        CustomerAddres, select_address_id == CustomerAddres.CustAddressId).join(
        DeliveryUser,
        select_delivery_user_id == DeliveryUser.DUserId).outerjoin(
        Order, Order.PickupRequestId == PickupRequest.PickupRequestId).outerjoin(
        TravelLog, (TravelLog.OrderId == Order.OrderId) & (TravelLog.Activity == 'Pickup')).join(Branch, select_branch_code == Branch.BranchCode).filter(
        or_(Order.IsDeleted == 0, Order.IsDeleted == None),
        PickupRequest.IsCancelled == 0, PickupRequest.PickupStatusId == 3,
        interval_condition_check,
        select_branch_code.in_(store_user_branches),
        select_delivery_user_id != None, Order.OrderId != None,
        or_(PickupReschedule.IsDeleted == 0, PickupReschedule.IsDeleted == None)
    )

    return completed_pickups

def get_completed_deliveries_fromdate_todate(record_created_date, formatted_from_date, formatted_to_date,
                                                 store_user_branches):
    """
    Function for retrieving the completed deliveries.
    @param record_created_date: Saved date of the delivery details.
    @param interval_start_date: 1-7 (in days).
    @param store_user_branches: List of associated branch codes. Return the result from these branches only.
    @return: completed deliveries (SQLA result).
    """
    print("hai")
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

    if formatted_from_date < formatted_to_date:
        # Here, an day interval is specified. So select the details from the start date and current date.
        interval_condition_check = and_(Delivery.RecordCreatedDate < formatted_to_date,
                                        Delivery.RecordCreatedDate > formatted_from_date)
    elif formatted_from_date == formatted_to_date:

        f = datetime.strptime(formatted_to_date, "%Y-%m-%d %H:%M:%S")
        formatted_to_date = f + timedelta(1)
        interval_condition_check = and_(
            Delivery.RecordCreatedDate >= formatted_from_date,
            Delivery.RecordCreatedDate <= formatted_to_date)

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

    # If the Delivery Remarks is NULL, select NA.
    select_delivery_remarks = case([(Delivery.Remarks == None, "NA"), ],
                                   else_=Delivery.Remarks).label("Remarks")

    # If the delivery is rescheduled, then select RescheduledDate, else select DeliveryDate.
    # select_activity_date = case([(DeliveryReschedule.RescheduledDate == None, DeliveryRequest.DeliveryDate), ],
    #                             else_=DeliveryReschedule.RescheduledDate).label("ActivityDate")

    # Check if the activity is a walk in or D2D.
    select_activity_category = case([(Order.PickupRequestId == None, literal('Walk-In').label('ActivityCategory')), ],
                                    else_=literal('D2D').label('ActivityCategory')).label("ActivityCategory")

    # If a DisplayName found for a branch, then select DisplayName as the BranchName.
    select_branch_name = case(
        [(or_(Branch.DisplayName == None, Branch.DisplayName == ''), Branch.BranchName), ],
        else_=Branch.DisplayName).label("BranchName")

    select_payment_status = case([(Delivery.PaymentFlag == 0, literal('Delivered-Paid'))],
                                 else_=literal('Paid')).label('PaymentStatus')

    otp_dtls = case([(Delivery.DeliveryWithoutOtp == 0, 'YES')], else_='NO').label('IsOTPSent')

    select_date = case([(TransactionInfo.PaymentCompletedOn.is_(None), "NA")],
                       else_=cast(TransactionInfo.PaymentCompletedOn, String)).label('CompletedDate')
    

    amount_dtls = case([(TransactionInfo.TotalPayableAmount.is_(None), 0)],
                       else_=TransactionInfo.TotalPayableAmount).label('Amount')
    # payable = case([(TransactionInfo.PaymentCollectedBY.is_(None), 'NA')],
    #                else_=TransactionInfo.PaymentCollectedBY).label('PaymentCollectedBY')
    select_city_code = case(
        [(CustomerAddres.CityCode.is_(None), "NA")],
        else_=CustomerAddres.CityCode
    ).label("CityCode")

    select_city_name = case(
        [(City.CityName.is_(None), "NA")],
        else_=City.CityName
    ).label("CityName")
    
    select_state_name = case(
    [(State.StateName.is_(None), "NA")],  # Handle null StateName
        else_=State.StateName
    ).label("StateName")
    payment_collected_by_case = case(
        [
            (TransactionInfo.PaymentSource == 'delivery', DeliveryUser.UserName)
        ],
        else_=TransactionInfo.PaymentSource
    ).label('PaymentCollectedBy')

    trn_number = case([(DeliveryRequest.TRNNo == None, "NA")],
                         else_=DeliveryRequest.TRNNo).label("TRN Number")
    


    completed_deliveries = db.session.query(literal('Delivery').label('ActivityType'),
                                            select_activity_category,
                                            select_city_name,
                                            select_state_name,
                                            DeliveryRequest.CompletedDate.label('DeliveredOn'),
                                            select_booking_id, Order.OrderId, Order.EGRN,
                                            select_time_slot_from,
                                            select_time_slot_to,
                                            
                                    
                                            Delivery.DUserId,
                                            DeliveryUser.UserName.label('DeliveryUser'),
                                            Customer.CustomerId,
                                            Customer.CustomerCode,
                                            Customer.CustomerName,
                                            Customer.MobileNo,
                                            func.concat(CustomerAddres.Lat, ',', CustomerAddres.Long).label(
                                                'Customer Lat & Long'), func.concat(Branch.Lat, ',', Branch.Long).label('Store Lat & LONG'),
                                            func.concat(Delivery.Lat, ',', Delivery.Long).label('Pickup/Delivery Lat & Long'),
                                            select_discount_code, select_coupon_code,
                                            CustomerAddres.AddressLine1,
                                            select_address_line_2, select_address_line_3, record_created_date,
                                            select_delivery_remarks, Delivery.BranchCode, select_branch_name, otp_dtls,
                                            amount_dtls, trn_number, select_payment_status, select_date, payment_collected_by_case, (Delivery.distance).label('P-up/Del Location to Customer Distance'), (Delivery.store_distance).label('P-up/Del Location to Store Distance')).select_from(
        Delivery).join(Customer,
                       Delivery.CustomerId == Customer.CustomerId).outerjoin(
        DeliveryReschedule, DeliveryReschedule.DeliveryRequestId == Delivery.DeliveryRequestId).join(
        Order,
        Delivery.OrderId == Order.OrderId).join(
        CustomerAddres, Delivery.DeliveryAddressId == CustomerAddres.CustAddressId).outerjoin(
        City, CustomerAddres.CityCode == City.CityCode).outerjoin(
        State, City.StateCode == State.StateCode).join(
        DeliveryUser,
        Delivery.DUserId == DeliveryUser.DUserId).outerjoin(DeliveryRequest,
                                                            Delivery.DeliveryRequestId == DeliveryRequest.DeliveryRequestId).join(
        Branch, Delivery.BranchCode == Branch.BranchCode).outerjoin(
        TransactionInfo, TransactionInfo.EGRNNo == Delivery.EGRN).filter(
        or_(Order.IsDeleted == 0, Order.IsDeleted == None),
        DeliveryRequest.WalkIn == 0,
        Delivery.DUserId != None, Delivery.BranchCode.in_(store_user_branches),
        Delivery.DeliveryId != None, or_( Delivery.PaymentStatus == 'Paid',Delivery.PaymentStatus =='Partial - paid'),
        interval_condition_check,
        or_(DeliveryReschedule.IsDeleted == 0, DeliveryReschedule.IsDeleted == None))
    #print("end")
    # log_data = {
    #     'completed_deliveries :': completed_deliveries
    # }
    # info_logger(f'Route: {request.path}').info(json.dumps(log_data))

    return completed_deliveries

def get_completed_pickups_fromdate_todate(record_created_date, formatted_from_date, formatted_to_date,
                                      store_user_branches):
    """
    Function for retrieving the completed pickups.
    @param formatted_to_date:
    @param formatted_from_date:
    @param record_created_date: Saved date of the pickup.
    @param store_user_branches: List of associated branch codes. Return the result from these branches only.
    @return: Completed pickups (SQLA result).
    """

    # If the discount code is not applied, select NA.
    select_discount_code = case([(Order.DiscountCode == None, "NA"), ],
                                else_=Order.DiscountCode).label("DiscountCode")

    # If the coupon code is not applied, select NA.
    # select_coupon_code = case([(PickupRequest.CouponCode == None, "NA"), ],
    #                           else_=PickupRequest.CouponCode).label("CouponCode")
    select_coupon_code = case([(and_(Order.CouponCode != None, Order.CouponCode != ''), Order.CouponCode)],
                              else_='NA', ).label("CouponCode")

    # If the address line 2 is not present, then select NA.
    select_address_line_2 = case([(CustomerAddres.AddressLine2 == None, "NA"), ],
                                 else_=CustomerAddres.AddressLine2).label("AddressLine2")

    # If the address line 3 is not present, then select NA.
    select_address_line_3 = case([(CustomerAddres.AddressLine3 == None, "NA"), ],
                                 else_=CustomerAddres.AddressLine3).label("AddressLine3")

    if formatted_from_date < formatted_to_date:
        # Here, a day interval is specified. So select the details from the from_date and to date.
        interval_condition_check = and_(PickupRequest.CompletedDate < formatted_to_date,
                                        PickupRequest.CompletedDate > formatted_from_date)


    elif formatted_from_date == formatted_to_date:
        f = datetime.strptime(formatted_to_date, "%Y-%m-%d %H:%M:%S")
        formatted_to_date = f + timedelta(1)
        interval_condition_check = and_(PickupRequest.CompletedDate >= formatted_from_date,
                                        PickupRequest.CompletedDate < formatted_to_date
                                        )

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

    # If the Order Remarks is NULL, select NA.
    select_order_remarks = case([(Order.Remarks == None, "NA"), ],
                                else_=Order.Remarks).label("Remarks")

    # If the pickup is rescheduled, then select RescheduledDate, else select PickupDate.
    # select_activity_date = case([(PickupReschedule.RescheduledDate == None, PickupRequest.PickupDate), ],
    #                             else_=PickupReschedule.RescheduledDate).label("ActivityDate")

    # Check if the activity is a walk in or D2D.
    select_activity_category = case([(Order.PickupRequestId == None, literal('Walk-In').label('ActivityCategory')), ],
                                    else_=literal('D2D').label('ActivityCategory')).label("ActivityCategory")

    # If a DisplayName found for a branch, then select DisplayName as the BranchName.
    select_branch_name = case(
        [(or_(Branch.DisplayName == None, Branch.DisplayName == ''), Branch.BranchName), ],
        else_=Branch.DisplayName).label("BranchName")

    select_payment_status_with_na = literal('NA')
    select_payment_status = select_payment_status_with_na.label('PaymentStatus')

    select_city_code = case(
        [(CustomerAddres.CityCode.is_(None), "NA")],
        else_=CustomerAddres.CityCode
    ).label("CityCode")

    select_city_name = case(
        [(City.CityName.is_(None), "NA")],
        else_=City.CityName
    ).label("CityName")

    select_state_name = case(
    [(State.StateName.is_(None), "NA")],  # Handle null StateName
        else_=State.StateName
    ).label("StateName")

    Delivered_pickup = literal("NA")
    Delivered_pickups = Delivered_pickup.label('DeliveredOn')
    amount_dtls = literal(0).label('Amount')
    payable = literal('NA').label('PaymentCollectedBy')
    trn_number = literal('NA').label('TRN Number')

    # Total completed pickups for the branch.
    completed_pickups = db.session.query(literal('Pickup').label('ActivityType'),
                                         select_activity_category,
                                         select_city_name,
                                         select_state_name,
                                         PickupRequest.CompletedDate,
                                         PickupRequest.BookingId, Order.OrderId, Order.EGRN,
                                         select_time_slot_from,
                                         select_time_slot_to,
                                         
        
                                         select_delivery_user_id,
                                         DeliveryUser.UserName.label('DeliveryUser'), Customer.CustomerId,
                                         Customer.CustomerCode,
                                         Customer.CustomerName,
                                         Customer.MobileNo,
                                         func.concat(CustomerAddres.Lat, ',', CustomerAddres.Long).label(
                                             'Customer Lat & Long'),
                                         func.concat(PickupRequest.DuserLat, ',', PickupRequest.DuserLong).label('Pickup/Delivery Lat & Long'),
                                         func.concat(Branch.Lat, ',', Branch.Long).label('Store Lat & LONG'),
                                         select_discount_code, select_coupon_code, CustomerAddres.AddressLine1,
                                         select_address_line_2, select_address_line_3,
                                         record_created_date, select_order_remarks, select_branch_code,
                                         select_branch_name, literal('NO').label('Is OTP sent?'),
                                         amount_dtls, trn_number, select_payment_status,
                                         Delivered_pickups, payable,(PickupRequest.distance).label('P-up/Del Location to Customer Distance'),(PickupRequest.store_distance).label('P-up/Del Location to Store Distance')).join(Customer,
                                                                          PickupRequest.CustomerId == Customer.CustomerId).outerjoin(
        PickupReschedule,
        PickupReschedule.PickupRequestId == PickupRequest.PickupRequestId).join(
        CustomerAddres, select_address_id == CustomerAddres.CustAddressId).join(
        City, CustomerAddres.CityCode == City.CityCode).join(
        State,City.StateCode == State.StateCode).join(
        DeliveryUser,
        select_delivery_user_id == DeliveryUser.DUserId).outerjoin(
        Order,
        Order.PickupRequestId == PickupRequest.PickupRequestId).join(Branch,
                                                  select_branch_code == Branch.BranchCode).filter(
        or_(Order.IsDeleted == 0, Order.IsDeleted == None),
        PickupRequest.IsCancelled == 0, PickupRequest.PickupStatusId == 3,
        interval_condition_check,
        select_branch_code.in_(store_user_branches),
        select_delivery_user_id != None, Order.OrderId != None, Delivery.PaymentStatus == 'Paid',
        or_(PickupReschedule.IsDeleted == 0, PickupReschedule.IsDeleted == None)
    )

    return completed_pickups
def get_completed_deliveries_fromdate_todateStaging(record_created_date, formatted_from_date, formatted_to_date,
                                             store_user_branches):
    """
    Function for retrieving the completed deliveries.
    @param record_created_date: Saved date of the delivery details.
    @param interval_start_date: 1-7 (in days).
    @param store_user_branches: List of associated branch codes. Return the result from these branches only.
    @return: completed deliveries (SQLA result).
    """
    print("hai")
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

    if formatted_from_date < formatted_to_date:
        # Here, an day interval is specified. So select the details from the start date and current date.
        interval_condition_check = and_(Delivery.RecordCreatedDate < formatted_to_date,
                                        Delivery.RecordCreatedDate > formatted_from_date)
    elif formatted_from_date == formatted_to_date:

        f = datetime.strptime(formatted_to_date, "%Y-%m-%d %H:%M:%S")
        formatted_to_date = f + timedelta(1)
        interval_condition_check = and_(
            Delivery.RecordCreatedDate >= formatted_from_date,
            Delivery.RecordCreatedDate <= formatted_to_date)

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

    # If the Delivery Remarks is NULL, select NA.
    select_delivery_remarks = case([(Delivery.Remarks == None, "NA"), ],
                                   else_=Delivery.Remarks).label("Remarks")

    # If the delivery is rescheduled, then select RescheduledDate, else select DeliveryDate.
    # select_activity_date = case([(DeliveryReschedule.RescheduledDate == None, DeliveryRequest.DeliveryDate), ],
    #                             else_=DeliveryReschedule.RescheduledDate).label("ActivityDate")

    # Check if the activity is a walk in or D2D.
    select_activity_category = case([(Order.PickupRequestId == None, literal('Walk-In').label('ActivityCategory')), ],
                                    else_=literal('D2D').label('ActivityCategory')).label("ActivityCategory")

    # If a DisplayName found for a branch, then select DisplayName as the BranchName.
    select_branch_name = case(
        [(or_(Branch.DisplayName == None, Branch.DisplayName == ''), Branch.BranchName), ],
        else_=Branch.DisplayName).label("BranchName")

    select_payment_status = case([(Delivery.PaymentFlag == 0, literal('Delivered-Paid'))],
                                 else_=literal('Paid')).label('PaymentStatus')

    otp_dtls = case([(Delivery.DeliveryWithoutOtp == 0, 'YES')], else_='NO').label('IsOTPSent')

    select_date = case([(TransactionInfo.PaymentCompletedOn.is_(None), "NA")],
                       else_=cast(TransactionInfo.PaymentCompletedOn, String)).label('CompletedDate')

    amount_dtls = case([(TransactionInfo.TotalPayableAmount.is_(None), 0)],
                       else_=TransactionInfo.TotalPayableAmount).label('Amount')
    # payable = case([(TransactionInfo.PaymentCollectedBY.is_(None), 'NA')],
    #                else_=TransactionInfo.PaymentCollectedBY).label('PaymentCollectedBY')
    payment_collected_by_case = case(
        [
            (TransactionInfo.PaymentSource == 'delivery', DeliveryUser.UserName)
        ],
        else_=TransactionInfo.PaymentSource
    ).label('PaymentCollectedBy')
    completed_deliveries = db.session.query(literal('Delivery').label('ActivityType'),
                                            select_activity_category,
                                            DeliveryRequest.CompletedDate.label('DeliveredOn'),
                                            select_booking_id, Order.OrderId, Order.EGRN,
                                            select_time_slot_from,
                                            select_time_slot_to,
                                            Delivery.DUserId,
                                            DeliveryUser.UserName.label('DeliveryUser'),
                                            Customer.CustomerId,
                                            Customer.CustomerCode,
                                            Customer.CustomerName,
                                            func.concat(CustomerAddres.Lat, ',', CustomerAddres.Long).label(
                                                'Customer Lat & Long'),
                                            Customer.MobileNo, func.concat(Delivery.Lat, ',', Delivery.Long).label('Pickup/Delivery Lat & Long'),
                                            func.concat(Branch.Lat, ',', Branch.Long).label('Store Lat & LONG'),
                                            select_discount_code, select_coupon_code,
                                            CustomerAddres.AddressLine1,
                                            select_address_line_2, select_address_line_3, record_created_date,
                                            select_delivery_remarks, Delivery.BranchCode, select_branch_name, otp_dtls,
                                            amount_dtls, select_payment_status, select_date,
                                            payment_collected_by_case,(Delivery.distance).label('P-up/Del Location to Customer Distance'),(Delivery.store_distance).label('P-up/Del Location to Store Distance')).select_from(
        Delivery).join(Customer,
                       Delivery.CustomerId == Customer.CustomerId).outerjoin(
        DeliveryReschedule, DeliveryReschedule.DeliveryRequestId == Delivery.DeliveryRequestId).join(
        Order,
        Delivery.OrderId == Order.OrderId).join(
        CustomerAddres, Delivery.DeliveryAddressId == CustomerAddres.CustAddressId).join(
        DeliveryUser,
        Delivery.DUserId == DeliveryUser.DUserId).outerjoin(DeliveryRequest,
                                                            Delivery.DeliveryRequestId == DeliveryRequest.DeliveryRequestId).join(
        Branch, Delivery.BranchCode == Branch.BranchCode).outerjoin(
        TransactionInfo, TransactionInfo.EGRNNo == Delivery.EGRN).filter(
        or_(Order.IsDeleted == 0, Order.IsDeleted == None),
        DeliveryRequest.WalkIn == 0,
        Delivery.DUserId != None, Delivery.BranchCode.in_(store_user_branches),
        Delivery.DeliveryId != None, Delivery.PaymentStatus == 'Paid',
        interval_condition_check,
        or_(DeliveryReschedule.IsDeleted == 0, DeliveryReschedule.IsDeleted == None))

    return completed_deliveries



def attendance_for_today(user_id):
    """
    Getting the attendance details for today.
    @param user_id: Store user id.
    @return: StoreUserAttendance record.
    """
    today = datetime.today().strftime("%Y-%m-%d")
    attendance_record_of_today = db.session.query(StoreUserAttendance.Date,
                                                  StoreUserAttendance.ClockInTime,
                                                  StoreUserAttendance.ClockOutTime).filter(
        StoreUserAttendance.SUserId == user_id,
        StoreUserAttendance.Date == today,
        StoreUserAttendance.IsDeleted == 0).one_or_none()
    return attendance_record_of_today


def get_states(branch_codes):
    """
    Function for getting the states from a given branch codes.
    @param branch_codes:
    @return: SQLA result.
    """
    states = db.session.query(State.StateName, State.StateCode).distinct(State.StateName, State.StateCode).join(City,
                                                                                                                City.StateCode == State.StateCode).join(
        Area,
        City.CityCode == Area.CityCode).join(
        Branch, Area.AreaCode == Branch.AreaCode).filter(Branch.BranchCode.in_(branch_codes),
                                                         Branch.IsActive == 1).all()

    return states


def get_cities(branch_codes):
    """
    Function for getting the cities from given branch codes.
    @param branch_codes:
    @return: SQLA result.
    """
    cities = db.session.query(City.CityName, City.CityCode).distinct(City.CityName, City.CityCode).join(Area,
                                                                                                        City.CityCode == Area.CityCode).join(
        Branch, Area.AreaCode == Branch.AreaCode).filter(Branch.BranchCode.in_(branch_codes),
                                                         Branch.IsActive == 1).all()

    return cities


def get_branches(branch_codes):
    """
    Function for getting the branch code, and branch name from the given branch codes.
    @param branch_codes:
    @return: SQLA result.
    """

    # If a DisplayName found for a branch, then select DisplayName as the BranchName.
    select_branch_name = case(
        [(or_(Branch.DisplayName == None, Branch.DisplayName == ''), Branch.BranchName), ],
        else_=Branch.DisplayName).label("BranchName")

    branches = stores = db.session.query(select_branch_name, Branch.BranchCode).filter(
        Branch.BranchCode.in_(branch_codes), Branch.IsActive == 1).all()

    return branches


def get_branches_with_all_details(branch_codes, inactive):
    """
    Function for getting the branches with the city and state information.
    @param branch_codes:
    @return: SQLA result of branch details with city and state information.
    """

    # If a DisplayName found for a branch, then select DisplayName as the BranchName.
    select_branch_name = case(
        [(or_(Branch.DisplayName == None, Branch.DisplayName == ''), Branch.BranchName), ],
        else_=Branch.DisplayName).label("BranchName")

    branches = db.session.query(
        case([(Branch.IsActive == 0, 'Inact - ' + select_branch_name)], else_=select_branch_name).label('BranchName'),
        Branch.BranchCode, City.CityName, City.CityCode,
        State.StateName, State.StateCode).join(Area,
                                               Branch.AreaCode == Area.AreaCode).join(
        City, Area.CityCode == City.CityCode).join(State, City.StateCode == State.StateCode).filter(
        Branch.BranchCode.in_(branch_codes))
    if inactive:
        branches = branches.all()
    else:
        branches = branches.filter(Branch.IsActive == 1).all()

    return branches


def on_time_and_late_pickups_count(date, next_date, branch_codes, delivery_users):
    """
    Function for counting on time pickups and late pickups.
    (Based on PickupRequest's CompletedDate and PickupTimeSlot's TimeSlotFrom and TimeSlotTo.
    @param date: Given date (unix format).
    @param next_date: Next date of the given date (unix format).
    @param branch_codes: Store user's branch codes (given).
    @param delivery_users: List of delivery user ids.
    @return: Dict variable consisting of on time pickups and late pickups count.
    """

    # If the pickup is rescheduled, then select reschedule's time slot from, else time slot from of
    # the pickup request.
    select_time_slot_from = case([(PickupReschedule.TimeSlotFrom == None, PickupRequest.TimeSlotFrom), ],
                                 else_=PickupReschedule.TimeSlotFrom).label("TimeSlotFrom")

    # If the pickup is rescheduled, then select reschedule's time slot to, else time slot to of
    # the pickup request.
    select_time_slot_to = case([(PickupReschedule.TimeSlotTo == None, PickupRequest.TimeSlotTo), ],
                               else_=PickupReschedule.TimeSlotTo).label("TimeSlotTo")

    # If the pickup is rescheduled, then select RescheduledDate, else select PickupDate.
    select_pickup_date = case([(PickupReschedule.RescheduledDate == None, PickupRequest.PickupDate), ],
                              else_=PickupReschedule.RescheduledDate).label("PickupDate")

    completed_pickups = db.session.query(Order.OrderId, PickupRequest.PickupRequestId, PickupRequest.CompletedDate,
                                         Order.RecordCreatedDate,
                                         select_pickup_date, select_time_slot_from,
                                         select_time_slot_to).join(PickupRequest,
                                                                   Order.PickupRequestId == PickupRequest.PickupRequestId).outerjoin(
        PickupReschedule, PickupReschedule.PickupRequestId == PickupRequest.PickupRequestId).filter(
        PickupRequest.IsCancelled == 0, Order.DUserId.in_(delivery_users),
        Order.BranchCode.in_(branch_codes), PickupRequest.PickupStatusId == 3,
        and_(PickupRequest.CompletedDate > date, PickupRequest.CompletedDate < next_date),
        or_(PickupReschedule.IsDeleted == 0, PickupReschedule.IsDeleted == None)).all()

    on_time_pickups = 0
    late_pickups = 0

    # Iterating over the Orders details of the day and calculating the on time pickups and late pickups.
    for order in completed_pickups:
        if order.TimeSlotFrom is not None and order.TimeSlotTo is not None:
            completed_date = order.CompletedDate.strftime("%Y-%m-%d 00:00:00")
            pickup_date = order.PickupDate.strftime("%Y-%m-%d 00:00:00")

            if pickup_date == completed_date:
                # The pickup happened on the scheduled date.
                created_on = order.CompletedDate.strftime('%H:%M:%S')
                time_slot_start = order.TimeSlotFrom.strftime('%H:%M:%S')
                time_slot_end = order.TimeSlotTo.strftime('%H:%M:%S')

                # Checking whether the order created within the correct time slot or not.
                if time_slot_start < created_on < time_slot_end:
                    # Order created on time. So this is a on time pickup.
                    on_time_pickups += 1
                else:
                    # Order created late. So this is a late pickup.
                    late_pickups += 1
            else:
                # Pickup has happened not on the scheduled date. So this is late anyway.
                late_pickups += 1

    # Final dict variable that needs to be returned.
    data = {'on_time': on_time_pickups, 'late': late_pickups}

    return data


def on_time_and_late_deliveries_count(date, next_date, branch_codes, delivery_users):
    """
    Function for counting on time deliveries and late deliveries.
    (Based on Deliveries's RecordCreatedDate and PickupTimeSlot's TimeSlotFrom and TimeSlotTo.
    @param date: Given date in unix format (string).
    @param next_date: The next date in unix format (string).
    @param branch_codes: Store user's branch codes (given).
    @param delivery_users: List of delivery user ids.
    @return: Dict variable consisting of on time deliveries and late deliveries count.
    """

    # If the delivery is rescheduled, then select reschedule's time slot from, else time slot from of
    # the delivery request.
    select_time_slot_from = case([(DeliveryReschedule.TimeSlotFrom == None, DeliveryRequest.TimeSlotFrom), ],
                                 else_=DeliveryReschedule.TimeSlotFrom).label("TimeSlotFrom")

    # If the delivery is rescheduled, then select reschedule's time slot to, else time slot to of
    # the delivery request.
    select_time_slot_to = case([(DeliveryReschedule.TimeSlotTo == None, DeliveryRequest.TimeSlotTo), ],
                               else_=DeliveryReschedule.TimeSlotTo).label("TimeSlotTo")

    # If the delivery is rescheduled, then select RescheduledDate, else select DeliveryDate.
    select_delivery_date = case([(DeliveryReschedule.RescheduledDate == None, DeliveryRequest.DeliveryDate), ],
                                else_=DeliveryReschedule.RescheduledDate).label("DeliveryDate")

    # Getting the deliveries data of the day.
    deliveries_of_the_day = db.session.query(Delivery.DeliveryId, DeliveryRequest.DeliveryRequestId,
                                             Delivery.RecordCreatedDate,
                                             select_delivery_date, select_time_slot_from,
                                             select_time_slot_to).join(DeliveryRequest,
                                                                       Delivery.DeliveryRequestId == DeliveryRequest.DeliveryRequestId).outerjoin(
        DeliveryReschedule,
        DeliveryReschedule.DeliveryRequestId == DeliveryRequest.DeliveryRequestId).filter(
        DeliveryRequest.WalkIn == 0,
        Delivery.BranchCode.in_(branch_codes), Delivery.DUserId.in_(delivery_users),
        or_(DeliveryReschedule.IsDeleted == 0, DeliveryReschedule.IsDeleted == None),
        and_(Delivery.RecordCreatedDate > date, Delivery.RecordCreatedDate < next_date)).all()

    on_time_deliveries = 0
    late_deliveries = 0

    # Iterating over the Deliveries details of the day and calculating the on time deliveries and late deliveries.
    for delivery in deliveries_of_the_day:
        if delivery.TimeSlotFrom is not None and delivery.TimeSlotTo is not None:
            actual_delivery_date = delivery.RecordCreatedDate.strftime("%Y-%m-%d 00:00:00")
            delivery_date = delivery.DeliveryDate.strftime("%Y-%m-%d 00:00:00")

            if delivery_date == actual_delivery_date:
                # The delivery happened on the scheduled date.
                created_on = delivery.RecordCreatedDate.strftime('%H:%M:%S')
                time_slot_start = delivery.TimeSlotFrom.strftime('%H:%M:%S')
                time_slot_end = delivery.TimeSlotTo.strftime('%H:%M:%S')

                # Checking whether the delivery created within the correct time slot or not.
                if time_slot_start < created_on < time_slot_end:
                    # Delivery created on time. So this is a on time delivery.
                    on_time_deliveries += 1
                else:
                    # Delivery created late. So this is a late delivery.
                    late_deliveries += 1
            else:
                # Delivery has happened not on the scheduled date. So this is late anyway.
                late_deliveries += 1
    # Final dict variable that needs to be returned.
    data = {'on_time': on_time_deliveries, 'late': late_deliveries}

    return data


def trigger_out_for_activity_sms(alert_code, CustomerName, booking_id, MobileNo ,egrn):
    """
    If the pickup date is today, and current time is past 9'o clock,
    needs to trigger the alert engine SP to send the SMS for pickup.
    @param alert_code: Alert code of the alert engine. This could be OUT_FOR_PICKUP/OUT_FOR_DELIVERY.
    @param customer_id: CustomerId in the Customers table.
    @param booking_id: BookingId of the pickup request.
    @param egrn: EGRN of the order.
    @return:
    """

    # Getting hour from current time
    current_time = datetime.now().hour

    if current_time > 9:
        # Current time is past 9 AM. So needs to trigger the SMS.
        
        common_module.send_out_for_activity_sms(alert_code,
                                                    CustomerName,
                                                    MobileNo,
                                                    booking_id, egrn)


# def trigger_delivery_reschedule_sms(alert_code, customer_id, delivery_request_id, egrn, rescheduled_date):
#     """
#     If the delivery request is rescheduled for a future date, this SMS should be triggered.
#     @param alert_code: Alert code of the alert engine. This could be DELIVERY_RESCHEDULE.
#     @param customer_id: CustomerId in the Customers table.
#     @param delivery_request_id: DeliveryRequestId of the DeliveryRequests table.
#     @param egrn: EGRN of the order.
#     @param rescheduled_date: Rescheduled date in DD-MM-YYYY format.
#     @return:
#     """
#     # Getting the customer details.
#     customer_details = db.session.query(Customer.CustomerName,
#                                         Customer.MobileNo).filter(
#         Customer.CustomerId == customer_id).one_or_none()

#     # Delivery Request details.
#     delivery_request = db.session.query(DeliveryRequest.OrderId, DeliveryRequest.IsPartial).filter(
#         DeliveryRequest.DeliveryRequestId == delivery_request_id).one_or_none()

#     if delivery_request.IsPartial == 1:
#         # Check if the garments are explicitly selected for delivery or not.
#         delivery_garments_count = db.session.query(func.count(DeliveryGarment.DeliveryGarmentId)).filter(
#             DeliveryGarment.DeliveryRequestId == delivery_request_id, DeliveryGarment.IsDeleted == 0).scalar()

#     else:
#         # This is not a partial delivery. Get the count from the OrderGarments table itself.
#         delivery_garments_count = db.session.query(
#             func.count(OrderGarment.OrderGarmentId)).filter(
#             OrderGarment.OrderId == delivery_request.OrderId,
#             OrderGarment.GarmentStatusId == 10,
#             OrderGarment.IsDeleted == 0).scalar()

#     if customer_details is not None and delivery_garments_count > 0:
#         # Triggering the DELIVERY_RESCHEDULE alert code.
#         common_module.send_reschedule_sms(alert_code,
#                                           customer_details.CustomerName,
#                                           customer_details.MobileNo,
#                                           egrn, delivery_garments_count, get_current_date())

def trigger_delivery_reschedule_sms(alert_code, MobileNo,TRNNo, egrn, RescheduleDate, CustomerName ,user_id):
    """
    If the delivery request is rescheduled for a future date, this SMS should be triggered.
    @param alert_code: Alert code of the alert engine. This could be DELIVERY_RESCHEDULE.
    @param customer_id: CustomerId in the Customers table.
    @param delivery_request_id: DeliveryRequestId of the DeliveryRequests table.
    @param egrn: EGRN of the order.
    @param rescheduled_date: Rescheduled date in DD-MM-YYYY format.
    @return:
    """
    query = f""" EXEC JFSL.Dbo.SPPendingDeliveriesDetailedScreen @user_id = {user_id} ,@TRNNo = '{TRNNo}',@TRNNoBasisGarmentsCounts = {1}"""
    DeliveryGarmentsCount = CallSP(query).execute().fetchone()
    log_data = {
                    'query:':query
                         }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))
    garments_count = DeliveryGarmentsCount.get('GarmentsCount')
    common_module.send_reschedule_sms(alert_code,
                                          CustomerName,
                                          MobileNo,
                                          egrn, RescheduleDate, garments_count)


def get_delivery_user_assigned_pickups(select_activity_date, delivery_user_branches, user_id):
    """
    Function for getting the assigned pickup requests for a delivery user.
    @param select_activity_date PickupDate of the pickup request.
    @param delivery_user_branches: Associated branches of delivery user.
    @param user_id: Delivery user id.
    @return: SQL Alchemy ORM result.
    """
    # If the pickup is rescheduled, then select reschedule's BranchCode, else BranchCode of
    # the pickup request.
    select_branch_code = case([(PickupReschedule.BranchCode == None, PickupRequest.BranchCode), ],
                              else_=PickupReschedule.BranchCode).label("BranchCode")

    # If the CouponCode is present in the PickupRequest or the Orders table, select CouponCode.
    select_booking_id = case([
        (PickupRequest.BookingId != None, PickupRequest.BookingId),
    ], else_="NA").label("BookingId")

    # If the pickup is rescheduled, then select reschedule's DUserId, else DUserId of
    # the pickup request.
    select_delivery_user_id = case([(PickupReschedule.DUserId == None, PickupRequest.DUserId), ],
                                   else_=PickupReschedule.DUserId).label("DUserId")

    # If the pickup is rescheduled, then select reschedule's address id, else address id of
    # the pickup request.
    select_address_id = case([(PickupReschedule.CustAddressId == None, PickupRequest.CustAddressId), ],
                             else_=PickupReschedule.CustAddressId).label("CustAddressId")

    # Total pending pickup requests for the branch.
    base_query = db.session.query(literal('Pickup').label('ActivityType'),
                                  PickupRequest.PickupRequestId.label('ActivityId'),
                                  select_booking_id
                                  ).join(
        Customer,
        PickupRequest.CustomerId == Customer.CustomerId).outerjoin(
        PickupReschedule,
        PickupReschedule.PickupRequestId == PickupRequest.PickupRequestId).join(
        CustomerAddres, select_address_id == CustomerAddres.CustAddressId).join(
        DeliveryUser,
        select_delivery_user_id == DeliveryUser.DUserId).outerjoin(
        Order,
        Order.PickupRequestId == PickupRequest.PickupRequestId)

    # Select all the details based on given branch code(s).
    pending_pickups = base_query.filter(select_branch_code.in_(delivery_user_branches))

    # Normal pending pickups up to current date.
    pending_pickups = pending_pickups.filter(
        or_(Order.IsDeleted == 0, Order.IsDeleted == None),
        PickupRequest.IsCancelled == 0, PickupRequest.PickupStatusId.in_((1, 2)),
        select_activity_date <= get_current_date(),
        select_delivery_user_id == user_id,
        or_(PickupReschedule.IsDeleted == 0, PickupReschedule.IsDeleted == None)

    )

    return pending_pickups


def get_delivery_user_assigned_deliveries(select_activity_date, delivery_user_branches, user_id):
    """
    Function for getting the assigned delivery requests for a delivery user.
    @param select_activity_date DeliveryDate of the delivery request.
    @param delivery_user_branches: Associated branches of delivery user.
    @param user_id: Delivery user id.
    @return: SQL Alchemy ORM result.
    """
    # If the CouponCode is present in the PickupRequest or the Orders table, select CouponCode.
    select_booking_id = case([
        (DeliveryRequest.BookingId != None, DeliveryRequest.BookingId),
    ], else_="NA").label("BookingId")

    # If the delivery is rescheduled, then select reschedule's DUserId, else DUserId of
    # the delivery request.
    select_delivery_user_id = case(
        [(DeliveryReschedule.DUserId == None, DeliveryRequest.DUserId), ],
        else_=DeliveryReschedule.DUserId).label("DUserId")

    # If the delivery is rescheduled, then select reschedule's address id, else address id of
    # the delivery request.
    select_address_id = case(
        [(DeliveryReschedule.CustAddressId == None, DeliveryRequest.CustAddressId), ],
        else_=DeliveryReschedule.CustAddressId).label("CustAddressId")

    base_query = db.session.query(literal('Delivery').label('ActivityType'),
                                  DeliveryRequest.DeliveryRequestId.label('ActivityId'),
                                  select_booking_id
                                  ).join(Customer,
                                         DeliveryRequest.CustomerId == Customer.CustomerId).outerjoin(
        DeliveryReschedule, DeliveryReschedule.DeliveryRequestId == DeliveryRequest.DeliveryRequestId).join(
        Order,
        DeliveryRequest.OrderId == Order.OrderId).join(
        CustomerAddres, select_address_id == CustomerAddres.CustAddressId).join(
        DeliveryUser,
        select_delivery_user_id == DeliveryUser.DUserId).outerjoin(Delivery,
                                                                   Delivery.DeliveryRequestId == DeliveryRequest.DeliveryRequestId)

    # Select all the details based on given branch code(s).
    pending_deliveries = base_query.filter(DeliveryRequest.BranchCode.in_(delivery_user_branches),
                                           or_(DeliveryRequest.WalkIn == 0, DeliveryRequest.WalkIn == None))

    # Normal pending pickups up to current date.
    pending_deliveries = pending_deliveries.filter(
        or_(Order.IsDeleted == 0, Order.IsDeleted == None),
        select_delivery_user_id == user_id, DeliveryRequest.IsDeleted == 0,
        Delivery.DeliveryId == None, select_activity_date <= get_current_date(),
        or_(DeliveryReschedule.IsDeleted == 0, DeliveryReschedule.IsDeleted == None),

    )

    return pending_deliveries


def get_paginated_completed_pickups(record_created_date, from_date, to_date, store_user_branches):
    """
    Function for retrieving the completed pickups.
    @param record_created_date: Saved date of the pickup.
    @param interval_start_date: 1-7 (in days).
    @param store_user_branches: List of associated branch codes. Return the result from these branches only.
    @return: Completed pickups (SQLA result).
    """

    # If the discount code is not applied, select NA.
    select_discount_code = case([(Order.DiscountCode == None, "NA"), ],
                                else_=Order.DiscountCode).label("DiscountCode")

    # If the coupon code is not applied, select NA.
    # select_coupon_code = case([(PickupRequest.CouponCode == None, "NA"), ],
    #                           else_=PickupRequest.CouponCode).label("CouponCode")
    select_coupon_code = case([(and_(Order.CouponCode != None, Order.CouponCode != ''), Order.CouponCode)],
                              else_='NA', ).label("CouponCode")

    # If the address line 2 is not present, then select NA.
    select_address_line_2 = case([(CustomerAddres.AddressLine2 == None, "NA"), ],
                                 else_=CustomerAddres.AddressLine2).label("AddressLine2")

    # If the address line 3 is not present, then select NA.
    select_address_line_3 = case([(CustomerAddres.AddressLine3 == None, "NA"), ],
                                 else_=CustomerAddres.AddressLine3).label("AddressLine3")

    # Here, a day interval is specified. So select the details from the start date and current date.
    interval_condition_check = and_(PickupRequest.CompletedDate < to_date,
                                    PickupRequest.CompletedDate > from_date)

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

    # If the Order Remarks is NULL, select NA.
    select_order_remarks = case([(Order.Remarks == None, "NA"), ],
                                else_=Order.Remarks).label("Remarks")

    # If the pickup is rescheduled, then select RescheduledDate, else select PickupDate.
    select_activity_date = case([(PickupReschedule.RescheduledDate == None, PickupRequest.PickupDate), ],
                                else_=PickupReschedule.RescheduledDate).label("ActivityDate")

    # Check if the activity is a walk in or D2D.
    select_activity_category = case([(Order.PickupRequestId == None, literal('Walk-In').label('ActivityCategory')), ],
                                    else_=literal('D2D').label('ActivityCategory')).label("ActivityCategory")

    # If a DisplayName found for a branch, then select DisplayName as the BranchName.
    select_branch_name = case(
        [(or_(Branch.DisplayName == None, Branch.DisplayName == ''), Branch.BranchName), ],
        else_=Branch.DisplayName).label("BranchName")
    select_delivery_charge = case([
        (Order.DeliveryCharge == None, "NA"),
        (Order.DeliveryCharge == 0, "YES"),
        (Order.DeliveryCharge == 1, "NO")
    ]).label("DeliveryCharge")
    select_payment_status_with_na = literal('NA')
    select_payment_status = select_payment_status_with_na.label('PaymentStatus')
    Delivered_pickup = literal("NA")
    Delivered_pickups = Delivered_pickup.label('DeliveredOn')

    # Total completed pickups for the branch.
    completed_pickups = db.session.query(literal('Pickup').label('ActivityType'),
                                         select_activity_category, select_payment_status,
                                         literal('NA').label('IsOTPSent'),
                                         select_activity_date,
                                         PickupRequest.BookingId, Order.OrderId, Order.EGRN,
                                         select_time_slot_from,
                                         select_time_slot_to,
                                         select_delivery_user_id,
                                         DeliveryUser.UserName.label('DeliveryUser'), Customer.CustomerId,
                                         Customer.CustomerCode,
                                         Customer.CustomerName,
                                         Customer.MobileNo,
                                         select_discount_code, select_coupon_code, CustomerAddres.AddressLine1,
                                         select_address_line_2, select_address_line_3,
                                         record_created_date, select_order_remarks, select_branch_code,
                                         select_branch_name, select_delivery_charge,
                                         DeliveryUser.UserName.label('PaymentCollectedBy'), Delivered_pickups).join(
        Customer,
        PickupRequest.CustomerId == Customer.CustomerId).outerjoin(
        PickupReschedule,
        PickupReschedule.PickupRequestId == PickupRequest.PickupRequestId).join(
        CustomerAddres, select_address_id == CustomerAddres.CustAddressId).join(
        DeliveryUser,
        select_delivery_user_id == DeliveryUser.DUserId).outerjoin(
        Order,
        Order.PickupRequestId == PickupRequest.PickupRequestId).join(Branch,
                                                                     select_branch_code == Branch.BranchCode).filter(
        or_(Order.IsDeleted == 0, Order.IsDeleted == None),
        PickupRequest.IsCancelled == 0, PickupRequest.PickupStatusId == 3,
        select_branch_code.in_(store_user_branches),
        select_delivery_user_id != None, Order.OrderId != None,
        or_(PickupReschedule.IsDeleted == 0, PickupReschedule.IsDeleted == None), interval_condition_check
    )
    return completed_pickups


def get_paginated_completed_pickupstest(record_created_date, from_date, to_date, store_user_branches):
    """
    Function for retrieving the completed pickups.
    @param record_created_date: Saved date of the pickup.
    @param interval_start_date: 1-7 (in days).
    @param store_user_branches: List of associated branch codes. Return the result from these branches only.
    @return: Completed pickups (SQLA result).
    """

    # If the discount code is not applied, select NA.
    select_discount_code = case([(Order.DiscountCode == None, "NA"), ],
                                else_=Order.DiscountCode).label("DiscountCode")

    # If the coupon code is not applied, select NA.
    # select_coupon_code = case([(PickupRequest.CouponCode == None, "NA"), ],
    #                           else_=PickupRequest.CouponCode).label("CouponCode")
    select_coupon_code = case([(and_(Order.CouponCode != None, Order.CouponCode != ''), Order.CouponCode)],
                              else_='NA', ).label("CouponCode")

    # If the address line 2 is not present, then select NA.
    select_address_line_2 = case([(CustomerAddres.AddressLine2 == None, "NA"), ],
                                 else_=CustomerAddres.AddressLine2).label("AddressLine2")

    # If the address line 3 is not present, then select NA.
    select_address_line_3 = case([(CustomerAddres.AddressLine3 == None, "NA"), ],
                                 else_=CustomerAddres.AddressLine3).label("AddressLine3")

    # Here, a day interval is specified. So select the details from the start date and current date.
    interval_condition_check = and_(PickupRequest.CompletedDate < to_date,
                                    PickupRequest.CompletedDate > from_date)

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

    # If the Order Remarks is NULL, select NA.
    select_order_remarks = case([(Order.Remarks == None, "NA"), ],
                                else_=Order.Remarks).label("Remarks")

    # If the pickup is rescheduled, then select RescheduledDate, else select PickupDate.
    select_activity_date = case([(PickupReschedule.RescheduledDate == None, PickupRequest.PickupDate), ],
                                else_=PickupReschedule.RescheduledDate).label("ActivityDate")

    # Check if the activity is a walk in or D2D.
    select_activity_category = case([(Order.PickupRequestId == None, literal('Walk-In').label('ActivityCategory')), ],
                                    else_=literal('D2D').label('ActivityCategory')).label("ActivityCategory")

    # If a DisplayName found for a branch, then select DisplayName as the BranchName.
    select_branch_name = case(
        [(or_(Branch.DisplayName == None, Branch.DisplayName == ''), Branch.BranchName), ],
        else_=Branch.DisplayName).label("BranchName")
    select_delivery_charge = case([
        (Order.DeliveryCharge == None, "NA"),
        (Order.DeliveryCharge == 0, "YES"),
        (Order.DeliveryCharge == 1, "NO")
    ]).label("DeliveryCharge")
    select_payment_status_with_na = literal('NA')
    select_payment_status = select_payment_status_with_na.label('PaymentStatus')

    # Total completed pickups for the branch.
    completed_pickups = db.session.query(literal('Pickup').label('ActivityType'),
                                         select_activity_category, select_payment_status,
                                         literal('NA').label('IsOTPSent'),
                                         select_activity_date,
                                         PickupRequest.BookingId, Order.OrderId, Order.EGRN,
                                         select_time_slot_from,
                                         select_time_slot_to,
                                         select_delivery_user_id,
                                         DeliveryUser.UserName.label('DeliveryUser'), Customer.CustomerId,
                                         Customer.CustomerCode,
                                         Customer.CustomerName,
                                         Customer.MobileNo,
                                         select_discount_code, select_coupon_code, CustomerAddres.AddressLine1,
                                         select_address_line_2, select_address_line_3,
                                         record_created_date, select_order_remarks, select_branch_code,
                                         select_branch_name, select_delivery_charge).join(Customer,
                                                                                          PickupRequest.CustomerId == Customer.CustomerId).outerjoin(
        PickupReschedule,
        PickupReschedule.PickupRequestId == PickupRequest.PickupRequestId).join(
        CustomerAddres, select_address_id == CustomerAddres.CustAddressId).join(
        DeliveryUser,
        select_delivery_user_id == DeliveryUser.DUserId).outerjoin(
        Order,
        Order.PickupRequestId == PickupRequest.PickupRequestId).join(Branch,
                                                                     select_branch_code == Branch.BranchCode).filter(
        or_(Order.IsDeleted == 0, Order.IsDeleted == None),
        PickupRequest.IsCancelled == 0, PickupRequest.PickupStatusId == 3,
        select_branch_code.in_(store_user_branches),
        select_delivery_user_id != None, Order.OrderId != None,
        or_(PickupReschedule.IsDeleted == 0, PickupReschedule.IsDeleted == None), interval_condition_check
    )
    return completed_pickups


# def get_paginated_completed_pickups(record_created_date, from_date, to_date, store_user_branches):
#     """
#     Function for retrieving the completed pickups.local
#     @param record_created_date: Saved date of the pickup.
#     @param interval_start_date: 1-7 (in days).
#     @param store_user_branches: List of associated branch codes. Return the result from these branches only.
#     @return: Completed pickups (SQLA result).
#     """

#     # If the discount code is not applied, select NA.
#     select_discount_code = case([(Order.DiscountCode == None, "NA"), ],
#                                 else_=Order.DiscountCode).label("DiscountCode")

#     # If the coupon code is not applied, select NA.
#     # select_coupon_code = case([(PickupRequest.CouponCode == None, "NA"), ],
#     #                           else_=PickupRequest.CouponCode).label("CouponCode")
#     select_coupon_code = case([(and_(Order.CouponCode != None, Order.CouponCode != ''), Order.CouponCode)],
#                               else_='NA', ).label("CouponCode")

#     # If the address line 2 is not present, then select NA.
#     select_address_line_2 = case([(CustomerAddres.AddressLine2 == None, "NA"), ],
#                                  else_=CustomerAddres.AddressLine2).label("AddressLine2")

#     # If the address line 3 is not present, then select NA.
#     select_address_line_3 = case([(CustomerAddres.AddressLine3 == None, "NA"), ],
#                                  else_=CustomerAddres.AddressLine3).label("AddressLine3")

#     # Here, a day interval is specified. So select the details from the start date and current date.
#     interval_condition_check = and_(PickupRequest.CompletedDate < to_date,
#                                     PickupRequest.CompletedDate > from_date)

#     # If the pickup is rescheduled, then select reschedule's BranchCode, else BranchCode of
#     # the pickup request.
#     select_branch_code = case([(PickupReschedule.BranchCode == None, PickupRequest.BranchCode), ],
#                               else_=PickupReschedule.BranchCode).label("BranchCode")

#     # If the pickup is rescheduled, then select reschedule's DUserId, else DUserId of
#     # the pickup request.
#     select_delivery_user_id = case([(PickupReschedule.DUserId == None, PickupRequest.DUserId), ],
#                                    else_=PickupReschedule.DUserId).label("DUserId")

#     # If the pickup is rescheduled, then select reschedule's address id, else address id of
#     # the pickup request.
#     select_address_id = case([(PickupReschedule.CustAddressId == None, PickupRequest.CustAddressId), ],
#                              else_=PickupReschedule.CustAddressId).label("CustAddressId")

#     # If the pickup is rescheduled, then select reschedule's time slot from, else time slot from of
#     # the pickup request.
#     select_time_slot_from = case([(PickupReschedule.TimeSlotFrom == None, PickupRequest.TimeSlotFrom), ],
#                                  else_=PickupReschedule.TimeSlotFrom).label("TimeSlotFrom")

#     # If the pickup is rescheduled, then select reschedule's time slot to, else time slot to of
#     # the pickup request.
#     select_time_slot_to = case([(PickupReschedule.TimeSlotTo == None, PickupRequest.TimeSlotTo), ],
#                                else_=PickupReschedule.TimeSlotTo).label("TimeSlotTo")

#     # If the Order Remarks is NULL, select NA.
#     select_order_remarks = case([(Order.Remarks == None, "NA"), ],
#                                 else_=Order.Remarks).label("Remarks")

#     # If the pickup is rescheduled, then select RescheduledDate, else select PickupDate.
#     select_activity_date = case([(PickupReschedule.RescheduledDate == None, PickupRequest.PickupDate), ],
#                                 else_=PickupReschedule.RescheduledDate).label("ActivityDate")

#     # Check if the activity is a walk in or D2D.
#     select_activity_category = case([(Order.PickupRequestId == None, literal('Walk-In').label('ActivityCategory')), ],
#                                     else_=literal('D2D').label('ActivityCategory')).label("ActivityCategory")

#     # If a DisplayName found for a branch, then select DisplayName as the BranchName.
#     select_branch_name = case(
#         [(or_(Branch.DisplayName == None, Branch.DisplayName == ''), Branch.BranchName), ],
#         else_=Branch.DisplayName).label("BranchName")
#     select_delivery_charge = case([
#         (Order.DeliveryCharge == None, "NA"),
#         (Order.DeliveryCharge == 0, "YES"),
#         (Order.DeliveryCharge == 1, "NO")
#     ]).label("DeliveryCharge")

#     select_payment_status_with_na = literal('NA')
#     select_payment_status = select_payment_status_with_na.label('PaymentStatus')

#     Delivered_pickup = literal("NA")
#     Delivered_pickups = Delivered_pickup.label('DeliveredOn')
#     #Delivered_pickups = cast(Delivered_pickup, String).label('DeliveredOn')

#     # PaymentCollected = literal('NA')
#     # collected_payment_id = PaymentCollected.label('PaymentCollectedBy_id')
#     # Payment = literal('NA')
#     # collected_payment = Payment.label('PaymentCollectedBY')

#     # PaymentCollectedBy_ids = case([(PickupReschedule.DUserId == None, PickupRequest.DUserId), ],
#     #                                else_=PickupReschedule.DUserId).label("PaymentCollectedBy_id")

#     # Total completed pickups for the branch.
#     completed_pickups = db.session.query(literal('Pickup').label('ActivityType'),
#                                          select_activity_category,
#                                          select_payment_status, literal('NA').label('IsOTPSent'),
#                                          select_activity_date,
#                                          PickupRequest.BookingId, Order.OrderId, Order.EGRN,
#                                          select_time_slot_from,
#                                          select_time_slot_to,
#                                          select_delivery_user_id,
#                                          DeliveryUser.UserName.label('DeliveryUser'), Customer.CustomerId,
#                                          Customer.CustomerCode,
#                                          Customer.CustomerName,
#                                          Customer.MobileNo,
#                                          select_discount_code, select_coupon_code, CustomerAddres.AddressLine1,
#                                          select_address_line_2, select_address_line_3,
#                                          record_created_date, select_order_remarks, select_branch_code,
#                                          select_branch_name, select_delivery_charge,DeliveryUser.UserName.label('PaymentCollectedBY'),Delivered_pickups).join(Customer,
#                                                                                           PickupRequest.CustomerId == Customer.CustomerId).outerjoin(
#         PickupReschedule,
#         PickupReschedule.PickupRequestId == PickupRequest.PickupRequestId).join(
#         CustomerAddres, select_address_id == CustomerAddres.CustAddressId).join(
#         DeliveryUser,
#         select_delivery_user_id == DeliveryUser.DUserId).outerjoin(
#         Order,
#         Order.PickupRequestId == PickupRequest.PickupRequestId).join(Branch,
#                                                                      select_branch_code == Branch.BranchCode).filter(
#         or_(Order.IsDeleted == 0, Order.IsDeleted == None),
#         PickupRequest.IsCancelled == 0, PickupRequest.PickupStatusId == 3,
#         select_branch_code.in_(store_user_branches),
#         select_delivery_user_id != None, Order.OrderId != None,
#         or_(PickupReschedule.IsDeleted == 0, PickupReschedule.IsDeleted == None), interval_condition_check
#     )
#     return completed_pickups


def get_paginated_completed_deliveries(record_created_date, from_date, to_date, store_user_branches):
    """
    Function for retrieving the completed deliveries.
    @param record_created_date: Saved date of the delivery details.
    @param interval_start_date: 1-7 (in days).
    @param store_user_branches: List of associated branch codes. Return the result from these branches only.
    @return: completed deliveries (SQLA result).
    """

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

    # Here, an day interval is specified. So select the details from the start date and current date.
    interval_condition_check = and_(Delivery.RecordCreatedDate < to_date,
                                    Delivery.RecordCreatedDate > from_date)

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

    # If the Delivery Remarks is NULL, select NA.
    select_delivery_remarks = case([(Delivery.Remarks == None, "NA"), ],
                                   else_=Delivery.Remarks).label("Remarks")

    # If the delivery is rescheduled, then select RescheduledDate, else select DeliveryDate.
    select_activity_date = case([(DeliveryReschedule.RescheduledDate == None, DeliveryRequest.DeliveryDate), ],
                                else_=DeliveryReschedule.RescheduledDate).label("ActivityDate")

    # Check if the activity is a walk in or D2D.
    select_activity_category = case([(Order.PickupRequestId == None, literal('Walk-In').label('ActivityCategory')), ],
                                    else_=literal('D2D').label('ActivityCategory')).label("ActivityCategory")

    # If a DisplayName found for a branch, then select DisplayName as the BranchName.
    select_branch_name = case(
        [(or_(Branch.DisplayName == None, Branch.DisplayName == ''), Branch.BranchName), ],
        else_=Branch.DisplayName).label("BranchName")
    select_delivery_charge = case([
        (Order.DeliveryCharge == None, "NA"),
        (Order.DeliveryCharge == 0, "YES"),
        (Order.DeliveryCharge == 1, "NO")
    ]).label("DeliveryCharge")

    select_payment_status = case([(Delivery.PaymentFlag == 0, literal('Delivery-Unpaid'))],
                                 else_=literal('Paid')).label('PaymentStatus')
    # otp_dtls = case([(Delivery.DeliveryWithoutOtp == 1, literal('NO'))],
    #                 else_=literal('YES')).label('IsOTPSent')
    otp_dtls = case([(Delivery.DeliveryWithoutOtp == 0, 'YES')], else_='NO').label('IsOTPSent')
    select_date = case([(TransactionInfo.PaymentCompletedOn.is_(None), "NA")],
                       else_=cast(TransactionInfo.PaymentCompletedOn, String)).label('DeliveredOn')

    completed_deliveries = db.session.query(literal('Delivery').label('ActivityType'),
                                            select_activity_category, select_payment_status, otp_dtls,
                                            select_activity_date,
                                            select_booking_id, Order.OrderId, Order.EGRN,
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
                                            select_address_line_2, select_address_line_3, record_created_date,
                                            select_delivery_remarks, Delivery.BranchCode, select_branch_name,
                                            select_delivery_charge, DeliveryUser.UserName.label('PaymentCollectedBy'),
                                            select_date).select_from(Delivery).join(Customer,
                                                                                    Delivery.CustomerId == Customer.CustomerId).outerjoin(
        DeliveryReschedule, DeliveryReschedule.DeliveryRequestId == Delivery.DeliveryRequestId).join(
        Order,
        Delivery.OrderId == Order.OrderId).join(
        CustomerAddres, Delivery.DeliveryAddressId == CustomerAddres.CustAddressId).join(
        DeliveryUser,
        Delivery.DUserId == DeliveryUser.DUserId).outerjoin(DeliveryRequest,
                                                            Delivery.DeliveryRequestId == DeliveryRequest.DeliveryRequestId).join(
        Branch, Delivery.BranchCode == Branch.BranchCode).outerjoin(
        TransactionInfo, TransactionInfo.EGRNNo == Delivery.EGRN).filter(
        or_(Order.IsDeleted == 0, Order.IsDeleted == None),
        DeliveryRequest.WalkIn == 0,
        Delivery.DUserId != None, Delivery.BranchCode.in_(store_user_branches),
        Delivery.DeliveryId != None, Delivery.PaymentStatus == 'Paid',
        # interval_condition_check,
        or_(DeliveryReschedule.IsDeleted == 0, DeliveryReschedule.IsDeleted == None), interval_condition_check)

    return completed_deliveries


def get_paginated_completed_deliveriestest(record_created_date, from_date, to_date, store_user_branches):
    """
    Function for retrieving the completed deliveries.
    @param record_created_date: Saved date of the delivery details.
    @param interval_start_date: 1-7 (in days).
    @param store_user_branches: List of associated branch codes. Return the result from these branches only.
    @return: completed deliveries (SQLA result).
    """

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

    # Here, an day interval is specified. So select the details from the start date and current date.
    interval_condition_check = and_(Delivery.RecordCreatedDate < to_date,
                                    Delivery.RecordCreatedDate > from_date)

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

    # If the Delivery Remarks is NULL, select NA.
    select_delivery_remarks = case([(Delivery.Remarks == None, "NA"), ],
                                   else_=Delivery.Remarks).label("Remarks")

    # If the delivery is rescheduled, then select RescheduledDate, else select DeliveryDate.
    select_activity_date = case([(DeliveryReschedule.RescheduledDate == None, DeliveryRequest.DeliveryDate), ],
                                else_=DeliveryReschedule.RescheduledDate).label("ActivityDate")

    # Check if the activity is a walk in or D2D.
    select_activity_category = case([(Order.PickupRequestId == None, literal('Walk-In').label('ActivityCategory')), ],
                                    else_=literal('D2D').label('ActivityCategory')).label("ActivityCategory")

    # If a DisplayName found for a branch, then select DisplayName as the BranchName.
    select_branch_name = case(
        [(or_(Branch.DisplayName == None, Branch.DisplayName == ''), Branch.BranchName), ],
        else_=Branch.DisplayName).label("BranchName")
    select_delivery_charge = case([
        (Order.DeliveryCharge == None, "NA"),
        (Order.DeliveryCharge == 0, "YES"),
        (Order.DeliveryCharge == 1, "NO")
    ]).label("DeliveryCharge")

    select_payment_status = case([(Delivery.PaymentFlag == 0, literal('Delivery-Unpaid'))],
                                 else_=literal('Paid')).label('PaymentStatus')
    # otp_dtls = case([(Delivery.DeliveryWithoutOtp == 1, literal('NO'))],
    #                 else_=literal('YES')).label('IsOTPSent')
    otp_dtls = case([(Delivery.DeliveryWithoutOtp == 1, 'YES')], else_='NO').label('IsOTPSent')

    completed_deliveries = db.session.query(literal('Delivery').label('ActivityType'),
                                            select_activity_category, select_payment_status, otp_dtls,
                                            select_activity_date,
                                            select_booking_id, Order.OrderId, Order.EGRN,
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
                                            select_address_line_2, select_address_line_3, record_created_date,
                                            select_delivery_remarks, Delivery.BranchCode, select_branch_name,
                                            select_delivery_charge
                                            ).select_from(Delivery).join(Customer,
                                                                         Delivery.CustomerId == Customer.CustomerId).outerjoin(
        DeliveryReschedule, DeliveryReschedule.DeliveryRequestId == Delivery.DeliveryRequestId).join(
        Order,
        Delivery.OrderId == Order.OrderId).join(
        CustomerAddres, Delivery.DeliveryAddressId == CustomerAddres.CustAddressId).join(
        DeliveryUser,
        Delivery.DUserId == DeliveryUser.DUserId).outerjoin(DeliveryRequest,
                                                            Delivery.DeliveryRequestId == DeliveryRequest.DeliveryRequestId).join(
        Branch, Delivery.BranchCode == Branch.BranchCode).filter(
        or_(Order.IsDeleted == 0, Order.IsDeleted == None),
        DeliveryRequest.WalkIn == 0,
        Delivery.DUserId != None, Delivery.BranchCode.in_(store_user_branches),
        Delivery.DeliveryId != None, Delivery.PaymentStatus == 'Paid',
        # interval_condition_check,
        or_(DeliveryReschedule.IsDeleted == 0, DeliveryReschedule.IsDeleted == None), interval_condition_check)

    return completed_deliveries


# def get_paginated_completed_deliveries(record_created_date, from_date, to_date, store_user_branches):
#     """
#     Function for retrieving the completed deliveries.local
#     @param record_created_date: Saved date of the delivery details.
#     @param interval_start_date: 1-7 (in days).
#     @param store_user_branches: List of associated branch codes. Return the result from these branches only.
#     @return: completed deliveries (SQLA result).
#     """

#     select_discount_code = case([
#         (Order.DiscountCode != None, Order.DiscountCode),
#     ], else_="NA").label("DiscountCode")

#     # If the CouponCode is present in the PickupRequest or the Orders table, select CouponCode.
#     select_coupon_code = case([
#         (Order.CouponCode != None, Order.CouponCode),
#     ], else_="NA").label("CouponCode")

#     # If the address line 2 is not present, then select NA.
#     select_address_line_2 = case([(CustomerAddres.AddressLine2 == None, "NA"), ],
#                                  else_=CustomerAddres.AddressLine2).label("AddressLine2")

#     # If the address line 3 is not present, then select NA.
#     select_address_line_3 = case([(CustomerAddres.AddressLine3 == None, "NA"), ],
#                                  else_=CustomerAddres.AddressLine3).label("AddressLine3")

#     # Here, an day interval is specified. So select the details from the start date and current date.
#     interval_condition_check = and_(Delivery.RecordCreatedDate < to_date,
#                                     Delivery.RecordCreatedDate > from_date)

#     # If the BookingId is present in the Deliveries table, select BookingId.
#     select_booking_id = case([
#         (Delivery.BookingId != None, Delivery.BookingId),
#     ], else_="NA").label("BookingId")

#     # If the delivery is rescheduled, then select reschedule's time slot from, else time slot from of
#     # the delivery request.
#     select_time_slot_from = case([(DeliveryReschedule.TimeSlotFrom == None, DeliveryRequest.TimeSlotFrom), ],
#                                  else_=DeliveryReschedule.TimeSlotFrom).label("TimeSlotFrom")

#     # If the delivery is rescheduled, then select reschedule's time slot to, else time slot to of
#     # the delivery request.
#     select_time_slot_to = case([(DeliveryReschedule.TimeSlotTo == None, DeliveryRequest.TimeSlotTo), ],
#                                else_=DeliveryReschedule.TimeSlotTo).label("TimeSlotTo")

#     # If the Delivery Remarks is NULL, select NA.
#     select_delivery_remarks = case([(Delivery.Remarks == None, "NA"), ],
#                                    else_=Delivery.Remarks).label("Remarks")

#     # If the delivery is rescheduled, then select RescheduledDate, else select DeliveryDate.
#     select_activity_date = case([(DeliveryReschedule.RescheduledDate == None, DeliveryRequest.DeliveryDate), ],
#                                 else_=DeliveryReschedule.RescheduledDate).label("ActivityDate")

#     # Check if the activity is a walk in or D2D.
#     select_activity_category = case([(Order.PickupRequestId == None, literal('Walk-In').label('ActivityCategory')), ],
#                                     else_=literal('D2D').label('ActivityCategory')).label("ActivityCategory")

#     # If a DisplayName found for a branch, then select DisplayName as the BranchName.
#     select_branch_name = case(
#         [(or_(Branch.DisplayName == None, Branch.DisplayName == ''), Branch.BranchName), ],
#         else_=Branch.DisplayName).label("BranchName")
#     select_delivery_charge = case([
#         (Order.DeliveryCharge == None, "NA"),
#         (Order.DeliveryCharge == 0, "YES"),
#         (Order.DeliveryCharge == 1, "NO")
#     ]).label("DeliveryCharge")

#     select_payment_status = case([(Delivery.PaymentFlag == 0, literal('Delivery-Unpaid'))],
#                                  else_=literal('Paid')).label('PaymentStatus')
#     # otp_dtls = case([(Delivery.DeliveryWithoutOtp == 1, literal('NO'))],
#     #                 else_=literal('YES')).label('IsOTPSent')
#     # otp_dtls = case([(Delivery.DeliveryWithoutOtp == 1, 0)], else_=1).label('IsOTPSent')
#     otp_dtls = case([(Delivery.DeliveryWithoutOtp == 1, 'YES')], else_='NO').label('IsOTPSent')
#     # select_date = case([(TransactionInfo.PaymentCompletedOn.is_(None), None)],
#     #                    else_=TransactionInfo.PaymentCompletedOn).label('DeliveredOn')


#     # Assuming TransactionInfo.PaymentCompletedOn is a DateTime field
#     # select_date = case([(TransactionInfo.PaymentCompletedOn.is_(None), "NA")],
#     #                    else_=cast(TransactionInfo.PaymentCompletedOn, String)).label('DeliveredOn')
#     select_date = case([(TransactionInfo.PaymentCompletedOn.is_(None), "NA")],
#                        else_=cast(TransactionInfo.PaymentCompletedOn, String)).label('DeliveredOn')

#     completed_deliveries = db.session.query(literal('Delivery').label('ActivityType'),
#                                             select_activity_category, select_payment_status, otp_dtls,
#                                             select_activity_date,
#                                             select_booking_id, Order.OrderId, Order.EGRN,
#                                             select_time_slot_from,
#                                             select_time_slot_to,
#                                             Delivery.DUserId,
#                                             DeliveryUser.UserName.label('DeliveryUser'),
#                                             Customer.CustomerId,
#                                             Customer.CustomerCode,
#                                             Customer.CustomerName,
#                                             Customer.MobileNo,
#                                             select_discount_code, select_coupon_code,
#                                             CustomerAddres.AddressLine1,
#                                             select_address_line_2, select_address_line_3, record_created_date,
#                                             select_delivery_remarks, Delivery.BranchCode, select_branch_name,
#                                             select_delivery_charge,DeliveryUser.UserName.label('PaymentCollectedBy'),select_date
#                                             ).select_from(Delivery).join(Customer,
#                                                                          Delivery.CustomerId == Customer.CustomerId).outerjoin(
#         DeliveryReschedule, DeliveryReschedule.DeliveryRequestId == Delivery.DeliveryRequestId).join(
#         Order,
#         Delivery.OrderId == Order.OrderId).join(
#         CustomerAddres, Delivery.DeliveryAddressId == CustomerAddres.CustAddressId).join(
#         DeliveryUser,
#         Delivery.DUserId == DeliveryUser.DUserId).outerjoin(DeliveryRequest,
#                                                             Delivery.DeliveryRequestId == DeliveryRequest.DeliveryRequestId).join(
#         Branch, Delivery.BranchCode == Branch.BranchCode).outerjoin(
#         TransactionInfo, TransactionInfo.EGRNNo == Delivery.EGRN).filter(
#         or_(Order.IsDeleted == 0, Order.IsDeleted == None),
#         DeliveryRequest.WalkIn == 0,
#         Delivery.DUserId != None, Delivery.BranchCode.in_(store_user_branches),
#         Delivery.DeliveryId != None, Delivery.PaymentStatus == 'Paid',
#         or_(DeliveryReschedule.IsDeleted == 0, DeliveryReschedule.IsDeleted == None), interval_condition_check)

#     return completed_deliveries


def global_search_get_pending_pickups(select_activity_date, unassigned_only, late_only, store_user_branches):
    """
    Getting the pending pickups for the branch_code
    @param select_activity_date: Selection of PickupDate based on Pickup request/Pickup reschedule.
    @param unassigned_only: If it is True, only assigned activities will be returned.
    Else the unassigned pickups will be returned.
    @param late_only: Will return only late activities.
    @param store_user_branches: List of associated branch codes. Return the result from these branches only.
    @return: pending pickups (SQLA result).
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

    # If the pickup is rescheduled, then select reschedule's BranchCode, else BranchCode of
    # the pickup request.
    select_branch_code = case([(PickupReschedule.BranchCode == None, PickupRequest.BranchCode), ],
                              else_=PickupReschedule.BranchCode).label("BranchCode")

    # Selecting the BookingId from the table. If not found, return NA.
    select_booking_id = case([(PickupRequest.BookingId == None, "NA"), ],
                             else_=PickupRequest.BookingId).label("BookingId")

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

    # If the delivery is rescheduled, then select reschedule's time slot id, else time slot id of
    # the pickup request.
    select_time_slot_id = case([(PickupReschedule.PickupTimeSlotId == None, PickupRequest.PickupTimeSlotId), ],
                               else_=PickupReschedule.PickupTimeSlotId).label("TimeSlotId")

    # Select OrderId.
    select_order_id = case([(Order.OrderId == None, 0), ],
                           else_=Order.OrderId).label("OrderId")

    # Check if the activity is a walk in or D2D. Pending pickup will always be D2D.
    select_activity_category = literal('D2D').label('ActivityCategory')

    # If a DisplayName found for a branch, then select DisplayName as the BranchName.
    select_branch_name = case(
        [(or_(Branch.DisplayName == None, Branch.DisplayName == ''), Branch.BranchName), ],
        else_=Branch.DisplayName).label("BranchName")

    select_modified_by = case([(PickupReschedule.RescheduledBy == None, "NA"), ],
                              else_=PickupReschedule.RescheduledBy).label("ModifiedBy")

    # select_modified_date = case([(PickupReschedule.RescheduledDate == None, PickupRequest.RecordLastUpdatedDate), ],
    #                           else_=PickupReschedule.RecordLastUpdatedDate).label("ModifiedDate")
    select_modified_date = PickupReschedule.RecordLastUpdatedDate.label("ModifiedDate")

    select_assign_type = case([(and_(PickupReschedule.AssignedStoreUser == None,
                                     PickupReschedule.RescheduledStoreUser == None,
                                     PickupRequest.AssignedStoreUser == None),
                                literal('Auto').label('AssignType')), ],
                              else_=literal('Manual').label('AssignType')).label("AssignType")
    original_branch = aliased(Branch)
    select_original_branch_name = case(
        [(or_(original_branch.DisplayName == None, original_branch.DisplayName == ''), original_branch.BranchName), ],
        else_=original_branch.DisplayName).label("OriginalBranchName")

    # Total pending pickup requests for the branch.
    base_query = db.session.query(literal('Pickup').label('ActivityType'),
                                  PickupRequest.PickupRequestId.label('ActivityId'),
                                  select_activity_category,
                                  select_booking_id, select_order_id, literal('NA').label('EGRN'), select_activity_date,
                                  select_time_slot_id,
                                  select_time_slot_from,
                                  select_time_slot_to,
                                  select_delivery_user_id,
                                  DeliveryUser.UserName.label('DeliveryUser'), Customer.CustomerId,
                                  Customer.CustomerCode,
                                  Customer.CustomerName,
                                  Customer.MobileNo,
                                  select_discount_code, select_coupon_code, CustomerAddres.CustAddressId,
                                  CustomerAddres.AddressLine1,
                                  select_address_line_2, select_address_line_3, select_branch_code,
                                  case([(Branch.IsActive == 0, 'Inact - ' + select_original_branch_name)],
                                       else_=select_original_branch_name).label('OriginalBranchName'),
                                  case([(Branch.IsActive == 0, 'Inact - ' + select_branch_name)],
                                       else_=select_branch_name).label('BranchName'), select_assign_type,
                                  select_modified_by, select_modified_date).join(
        original_branch,
        original_branch.BranchCode == PickupRequest.BranchCode, isouter=True
    ).join(
        Customer,
        PickupRequest.CustomerId == Customer.CustomerId).outerjoin(
        PickupReschedule,
        PickupReschedule.PickupRequestId == PickupRequest.PickupRequestId).join(
        CustomerAddres, select_address_id == CustomerAddres.CustAddressId).join(Branch,
                                                                                select_branch_code == Branch.BranchCode).outerjoin(
        DeliveryUser,
        select_delivery_user_id == DeliveryUser.DUserId).outerjoin(
        Order,
        Order.PickupRequestId == PickupRequest.PickupRequestId)

    if unassigned_only:
        # Only getting the unassigned pending pickup requests. i.e. delivery user is unassigned
        # to the pickup request.
        pending_pickups = base_query.filter(
            or_(Order.IsDeleted == 0, Order.IsDeleted == None,
                and_(PickupRequest.IsReopen == 1, Order.ReOpenStatus == None)),
            PickupRequest.BookingId != None,
            PickupRequest.IsCancelled == 0, PickupRequest.PickupStatusId.in_((1, 2)),
            select_branch_code.in_(store_user_branches),
            select_delivery_user_id == None,
            # Order.OrderId == None,
            or_(PickupReschedule.IsDeleted == 0, PickupReschedule.IsDeleted == None))

    else:
        # Getting only assigned pickup requests.
        pending_pickups = base_query.filter(
            or_(Order.IsDeleted == 0, Order.IsDeleted == None,
                and_(PickupRequest.IsReopen == 1, Order.ReOpenStatus == None)),
            PickupRequest.BookingId != None,
            PickupRequest.IsCancelled == 0, PickupRequest.PickupStatusId.in_((1, 2)),
            select_branch_code.in_(store_user_branches),
            select_delivery_user_id != None,
            # Order.OrderId == None,
            or_(PickupReschedule.IsDeleted == 0, PickupReschedule.IsDeleted == None))

    if late_only:
        # If late_only flag is given in the request, return only late pickup requests.
        pending_pickups = pending_pickups.filter(select_activity_date < get_today())

    return pending_pickups


def global_search_get_pending_deliveries(select_activity_date, unassigned_only, late_only, store_user_branches):
    """
    Function to retrieve the pending delivery requests for a branch.
    @param late_only:
    @param select_activity_date Selection of DeliveryDate based on Delivery request/Delivery reschedule.
    @param unassigned_only: True if only need to return Assigned deliveries.
    Return non assigned deliveries if it is False.
    @param: late_only: Will return only late deliveries.
    @param store_user_branches: List of associated branch codes. Return the result from these branches only.
    @return: Pending deliveries (SQLA result).
    """

    select_discount_code = case([
        (Order.DiscountCode != None, Order.DiscountCode),
    ], else_="NA").label("DiscountCode")

    # If the CouponCode is present in the PickupRequest or the Orders table, select CouponCode.
    select_coupon_code = case([
        (Order.CouponCode != None, Order.CouponCode),
    ], else_="NA").label("CouponCode")

    # If the CouponCode is present in the PickupRequest or the Orders table, select CouponCode.
    select_booking_id = case([
        (DeliveryRequest.BookingId != None, DeliveryRequest.BookingId),
    ], else_="NA").label("BookingId")

    # If the address line 2 is not present, then select NA.
    select_address_line_2 = case([(CustomerAddres.AddressLine2 == None, "NA"), ],
                                 else_=CustomerAddres.AddressLine2).label("AddressLine2")

    # If the address line 3 is not present, then select NA.
    select_address_line_3 = case([(CustomerAddres.AddressLine3 == None, "NA"), ],
                                 else_=CustomerAddres.AddressLine3).label("AddressLine3")

    # If the delivery is rescheduled, then select reschedule's DUserId, else DUserId of
    # the delivery request.
    select_delivery_user_id = case(
        [(DeliveryReschedule.DUserId == None, DeliveryRequest.DUserId), ],
        else_=DeliveryReschedule.DUserId).label("DUserId")
    # select_delivery_user_id = case(
    #     [(and_(DeliveryReschedule.DUserId == None, DeliveryReschedule.IsDeleted == 1), DeliveryRequest.DUserId), ],
    #     else_=DeliveryReschedule.DUserId).label("DUserId")
    # If the delivery is rescheduled, then select reschedule's address id, else address id of
    # the delivery request.
    select_address_id = case(
        [(DeliveryReschedule.CustAddressId == None, DeliveryRequest.CustAddressId), ],
        else_=DeliveryReschedule.CustAddressId).label("CustAddressId")

    # If the delivery is rescheduled, then select reschedule's time slot from, else time slot from of
    # the pickup request.
    select_time_slot_from = case([(DeliveryReschedule.TimeSlotFrom == None, DeliveryRequest.TimeSlotFrom), ],
                                 else_=DeliveryReschedule.TimeSlotFrom).label("TimeSlotFrom")

    # If the delivery is rescheduled, then select reschedule's time slot to, else time slot to of
    # the pickup request.
    select_time_slot_to = case([(DeliveryReschedule.TimeSlotTo == None, DeliveryRequest.TimeSlotTo), ],
                               else_=DeliveryReschedule.TimeSlotTo).label("TimeSlotTo")

    # If the delivery is rescheduled, then select reschedule's time slot id, else time slot id of
    # the pickup request.
    select_time_slot_id = case([(DeliveryReschedule.DeliveryTimeSlotId == None, DeliveryRequest.DeliveryTimeSlotId), ],
                               else_=DeliveryReschedule.DeliveryTimeSlotId).label("TimeSlotId")

    # Check if the activity is a walk in or D2D.
    select_activity_category = case([(Order.PickupRequestId == None, literal('Walk-In').label('ActivityCategory')), ],
                                    else_=literal('D2D').label('ActivityCategory')).label("ActivityCategory")

    select_modified_by = case([(DeliveryReschedule.RescheduledBy == None, "NA"), ],
                              else_=DeliveryReschedule.RescheduledBy).label("ModifiedBy")

    # select_modified_date = case([(DeliveryReschedule.RescheduledDate == None, DeliveryRequest.RecordLastUpdatedDate), ],
    #                             else_=DeliveryReschedule.RecordLastUpdatedDate).label("ModifiedDate")
    select_modified_date = DeliveryReschedule.RecordLastUpdatedDate.label("ModifiedDate")

    # If a DisplayName found for a branch, then select DisplayName as the BranchName.
    select_branch_name = case(
        [(or_(Branch.DisplayName == None, Branch.DisplayName == ''), Branch.BranchName), ],
        else_=Branch.DisplayName).label("OriginalBranchName")
    select_assign_type = case([(and_(DeliveryReschedule.AssignedStoreUser == None,
                                     DeliveryReschedule.RescheduledStoreUser == None,
                                     DeliveryRequest.AssignedStoreUser == None),
                                literal('Auto').label('AssignType')), ],
                              else_=literal('Manual').label('AssignType')).label("AssignType")

    base_query = db.session.query(literal('Delivery').label('ActivityType'),
                                  DeliveryRequest.DeliveryRequestId.label('ActivityId'),
                                  select_activity_category,
                                  select_booking_id, Order.OrderId, Order.EGRN,
                                  select_activity_date,
                                  select_time_slot_id,
                                  select_time_slot_from,
                                  select_time_slot_to,
                                  select_delivery_user_id,
                                  DeliveryUser.UserName.label('DeliveryUser'),
                                  Customer.CustomerId,
                                  Customer.CustomerCode,
                                  Customer.CustomerName,
                                  Customer.MobileNo,
                                  select_discount_code, select_coupon_code,
                                  CustomerAddres.CustAddressId, CustomerAddres.AddressLine1,
                                  select_address_line_2, select_address_line_3,

                                  DeliveryRequest.BranchCode,
                                  # literal(' ').label('BranchName'),

                                  case([(Branch.IsActive == 0, 'Inact - ' + select_branch_name)],
                                       else_=select_branch_name).label('OriginalBranchName'),
                                  case([(Branch.IsActive == 0, 'Inact - ' + select_branch_name)],
                                       else_=select_branch_name).label('BranchName'),
                                  select_assign_type, select_modified_by, select_modified_date
                                  ).join(Customer,
                                         DeliveryRequest.CustomerId == Customer.CustomerId).outerjoin(
        DeliveryReschedule, DeliveryReschedule.DeliveryRequestId == DeliveryRequest.DeliveryRequestId).join(
        Order,
        DeliveryRequest.OrderId == Order.OrderId).join(
        CustomerAddres, select_address_id == CustomerAddres.CustAddressId).join(Branch,
                                                                                DeliveryRequest.BranchCode == Branch.BranchCode).outerjoin(
        DeliveryUser,
        select_delivery_user_id == DeliveryUser.DUserId).outerjoin(Delivery,
                                                                   Delivery.DeliveryRequestId == DeliveryRequest.DeliveryRequestId)

    # Omitting walk in orders.
    base_query = base_query.filter(DeliveryRequest.WalkIn == 0)

    if unassigned_only:
        # Only selects the delivery requests without delivery user.
        pending_deliveries = base_query.filter(
            or_(Order.IsDeleted == 0, Order.IsDeleted == None),
            select_delivery_user_id == None, DeliveryRequest.BranchCode.in_(store_user_branches),
            DeliveryRequest.IsDeleted == 0,
            Delivery.DeliveryId == None,
            or_(DeliveryReschedule.IsDeleted == 0, DeliveryReschedule.IsDeleted == None))
    else:

        # Getting assigned delivery requests.
        pending_deliveries = base_query.filter(
            or_(Order.IsDeleted == 0, Order.IsDeleted == None),
            DeliveryRequest.BranchCode.in_(store_user_branches),
            DeliveryRequest.IsDeleted == 0,
            select_delivery_user_id != None,
            Delivery.DeliveryId == None,
            or_(DeliveryReschedule.IsDeleted == 0, DeliveryReschedule.IsDeleted == None))

    if late_only:
        # If late_only flag is given in the request, return only late delivery requests.
        pending_deliveries = pending_deliveries.filter(select_activity_date < get_today())
    return pending_deliveries


def get_pending_pickups(select_activity_date, unassigned_only, late_only, store_user_branches, from_date, to_date):
    """
    Getting the pending pickups for the branch_code
    @param select_activity_date: Selection of PickupDate based on Pickup request/Pickup reschedule.
    @param unassigned_only: If it is True, only assigned activities will be returned.
    Else the unassigned pickups will be returned.
    @param late_only: Will return only late activities.
    @param store_user_branches: List of associated branch codes. Return the result from these branches only.
    @return: pending pickups (SQLA result).
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

    # If the pickup is rescheduled, then select reschedule's BranchCode, else BranchCode of
    # the pickup request.
    select_branch_code = case([(PickupReschedule.BranchCode == None, PickupRequest.BranchCode), ],
                              else_=PickupReschedule.BranchCode).label("BranchCode")

    # Selecting the BookingId from the table. If not found, return NA.
    select_booking_id = case([(PickupRequest.BookingId == None, "NA"), ],
                             else_=PickupRequest.BookingId).label("BookingId")

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

    # If the delivery is rescheduled, then select reschedule's time slot id, else time slot id of
    # the pickup request.
    select_time_slot_id = case([(PickupReschedule.PickupTimeSlotId == None, PickupRequest.PickupTimeSlotId), ],
                               else_=PickupReschedule.PickupTimeSlotId).label("TimeSlotId")

    # Select OrderId.
    select_order_id = case([(Order.OrderId == None, 0), ],
                           else_=Order.OrderId).label("OrderId")

    # Check if the activity is a walk in or D2D. Pending pickup will always be D2D.
    select_activity_category = literal('D2D').label('ActivityCategory')

    # If a DisplayName found for a branch, then select DisplayName as the BranchName.
    select_branch_name = case(
        [(or_(Branch.DisplayName == None, Branch.DisplayName == ''), Branch.BranchName), ],
        else_=Branch.DisplayName).label("BranchName")

    select_assign_type = case([(and_(PickupReschedule.AssignedStoreUser == None,
                                     PickupReschedule.RescheduledStoreUser == None,
                                     PickupRequest.AssignedStoreUser == None),
                                literal('Auto').label('AssignType')), ],
                              else_=literal('Manual').label('AssignType')).label("AssignType")
    select_modified_by = case([(PickupReschedule.RescheduledBy == None, "NA"), ],
                              else_=PickupReschedule.RescheduledBy).label("ModifiedBy")
    # select_modified_date = case([(PickupReschedule.RescheduledDate == None, PickupRequest.RecordLastUpdatedDate), ],
    #                             else_=PickupReschedule.RecordLastUpdatedDate).label("ModifiedDate")
    select_modified_date = PickupReschedule.RecordLastUpdatedDate.label("ModifiedDate")

    interval_condition_check = and_(PickupRequest.RecordCreatedDate < to_date,
                                    PickupRequest.RecordCreatedDate > from_date)
    original_branch = aliased(Branch)
    select_original_branch_name = case(
        [(or_(original_branch.DisplayName == None, original_branch.DisplayName == ''), original_branch.BranchName), ],
        else_=original_branch.DisplayName).label("OriginalBranchName")
    # Total pending pickup requests for the branch.
    base_query = db.session.query(literal('Pickup').label('ActivityType'),
                                  PickupRequest.PickupRequestId.label('ActivityId'),
                                  select_activity_category,
                                  select_booking_id, select_order_id, literal('NA').label('EGRN'), select_activity_date,
                                  select_time_slot_id,
                                  select_time_slot_from,
                                  select_time_slot_to,
                                  select_delivery_user_id,
                                  DeliveryUser.UserName.label('DeliveryUser'), Customer.CustomerId,
                                  Customer.CustomerCode,
                                  Customer.CustomerName,
                                  Customer.MobileNo,
                                  select_discount_code, select_coupon_code, CustomerAddres.CustAddressId,
                                  CustomerAddres.AddressLine1,
                                  select_address_line_2, select_address_line_3, select_branch_code,
                                  case([(Branch.IsActive == 0, 'Inact - ' + select_original_branch_name)],
                                       else_=select_original_branch_name).label('OriginalBranchName'),
                                  case([(Branch.IsActive == 0, 'Inact - ' + select_branch_name)],
                                       else_=select_branch_name).label('BranchName'), select_assign_type,
                                  select_modified_by,
                                  select_modified_date).join(
        original_branch,
        original_branch.BranchCode == PickupRequest.BranchCode, isouter=True
    ).join(
        Customer,
        PickupRequest.CustomerId == Customer.CustomerId).outerjoin(
        PickupReschedule,
        PickupReschedule.PickupRequestId == PickupRequest.PickupRequestId).join(
        CustomerAddres, select_address_id == CustomerAddres.CustAddressId).join(Branch,
                                                                                select_branch_code == Branch.BranchCode).outerjoin(
        DeliveryUser,
        select_delivery_user_id == DeliveryUser.DUserId).outerjoin(
        Order,
        Order.PickupRequestId == PickupRequest.PickupRequestId)
    if unassigned_only:
        # Only getting the unassigned pending pickup requests. i.e. delivery user is unassigned
        # to the pickup request.
        pending_pickups = base_query.filter(
            or_(Order.IsDeleted == 0, Order.IsDeleted == None,
                and_(PickupRequest.IsReopen == 1, Order.ReOpenStatus == None)),
            PickupRequest.BookingId != None,
            PickupRequest.IsCancelled == 0, PickupRequest.PickupStatusId.in_((1, 2)),
            select_branch_code.in_(store_user_branches),
            select_delivery_user_id == None, interval_condition_check,
            # Order.OrderId == None,
            or_(PickupReschedule.IsDeleted == 0, PickupReschedule.IsDeleted == None))

    else:
        # Getting only assigned pickup requests.
        pending_pickups = base_query.filter(
            or_(Order.IsDeleted == 0, Order.IsDeleted == None,
                and_(PickupRequest.IsReopen == 1, Order.ReOpenStatus == None)),
            PickupRequest.BookingId != None,
            PickupRequest.IsCancelled == 0, PickupRequest.PickupStatusId.in_((1, 2)),
            select_branch_code.in_(store_user_branches),
            select_delivery_user_id != None, interval_condition_check,
            # Order.OrderId == None,
            or_(PickupReschedule.IsDeleted == 0, PickupReschedule.IsDeleted == None))

    if late_only:
        # If late_only flag is given in the request, return only late pickup requests.
        pending_pickups = pending_pickups.filter(select_activity_date < get_today(), interval_condition_check)

    return pending_pickups


def get_pending_deliveries(select_activity_date, unassigned_only, late_only, store_user_branches, from_date, to_date):
    """
    Function to retrieve the pending delivery requests for a branch.
    @param late_only:
    @param select_activity_date Selection of DeliveryDate based on Delivery request/Delivery reschedule.
    @param unassigned_only: True if only need to return Assigned deliveries.
    Return non assigned deliveries if it is False.
    @param: late_only: Will return only late deliveries.
    @param store_user_branches: List of associated branch codes. Return the result from these branches only.
    @return: Pending deliveries (SQLA result).
    """

    select_discount_code = case([
        (Order.DiscountCode != None, Order.DiscountCode),
    ], else_="NA").label("DiscountCode")

    # If the CouponCode is present in the PickupRequest or the Orders table, select CouponCode.
    select_coupon_code = case([
        (Order.CouponCode != None, Order.CouponCode),
    ], else_="NA").label("CouponCode")

    # If the CouponCode is present in the PickupRequest or the Orders table, select CouponCode.
    select_booking_id = case([
        (DeliveryRequest.BookingId != None, DeliveryRequest.BookingId),
    ], else_="NA").label("BookingId")

    # If the address line 2 is not present, then select NA.
    select_address_line_2 = case([(CustomerAddres.AddressLine2 == None, "NA"), ],
                                 else_=CustomerAddres.AddressLine2).label("AddressLine2")

    # If the address line 3 is not present, then select NA.
    select_address_line_3 = case([(CustomerAddres.AddressLine3 == None, "NA"), ],
                                 else_=CustomerAddres.AddressLine3).label("AddressLine3")

    # If the delivery is rescheduled, then select reschedule's DUserId, else DUserId of
    # the delivery request.
    select_delivery_user_id = case(
        [(DeliveryReschedule.DUserId == None, DeliveryRequest.DUserId), ],
        else_=DeliveryReschedule.DUserId).label("DUserId")
    # select_delivery_user_id = case(
    #     [(and_(DeliveryReschedule.DUserId == None, DeliveryReschedule.IsDeleted == 1), DeliveryRequest.DUserId), ],
    #     else_=DeliveryReschedule.DUserId).label("DUserId")
    # If the delivery is rescheduled, then select reschedule's address id, else address id of
    # the delivery request.
    select_address_id = case(
        [(DeliveryReschedule.CustAddressId == None, DeliveryRequest.CustAddressId), ],
        else_=DeliveryReschedule.CustAddressId).label("CustAddressId")

    # If the delivery is rescheduled, then select reschedule's time slot from, else time slot from of
    # the pickup request.
    select_time_slot_from = case([(DeliveryReschedule.TimeSlotFrom == None, DeliveryRequest.TimeSlotFrom), ],
                                 else_=DeliveryReschedule.TimeSlotFrom).label("TimeSlotFrom")

    # If the delivery is rescheduled, then select reschedule's time slot to, else time slot to of
    # the pickup request.
    select_time_slot_to = case([(DeliveryReschedule.TimeSlotTo == None, DeliveryRequest.TimeSlotTo), ],
                               else_=DeliveryReschedule.TimeSlotTo).label("TimeSlotTo")

    # If the delivery is rescheduled, then select reschedule's time slot id, else time slot id of
    # the pickup request.
    select_time_slot_id = case([(DeliveryReschedule.DeliveryTimeSlotId == None, DeliveryRequest.DeliveryTimeSlotId), ],
                               else_=DeliveryReschedule.DeliveryTimeSlotId).label("TimeSlotId")

    # Check if the activity is a walk in or D2D.
    select_activity_category = case([(Order.PickupRequestId == None, literal('Walk-In').label('ActivityCategory')), ],
                                    else_=literal('D2D').label('ActivityCategory')).label("ActivityCategory")
    select_modified_by = case([(DeliveryReschedule.RescheduledBy == None, "NA"), ],
                              else_=DeliveryReschedule.RescheduledBy).label("ModifiedBy")
    # select_modified_date = case([(DeliveryReschedule.RescheduledDate == None, DeliveryRequest.RecordLastUpdatedDate), ],
    #                             else_=DeliveryReschedule.RecordLastUpdatedDate).label("ModifiedDate")
    select_modified_date = DeliveryReschedule.RecordLastUpdatedDate.label("ModifiedDate")

    # If a DisplayName found for a branch, then select DisplayName as the BranchName.
    select_branch_name = case(
        [(or_(Branch.DisplayName == None, Branch.DisplayName == ''), Branch.BranchName), ],
        else_=Branch.DisplayName).label("OriginalBranchName")
    select_assign_type = case([(and_(DeliveryReschedule.AssignedStoreUser == None,
                                     DeliveryReschedule.RescheduledStoreUser == None,
                                     DeliveryRequest.AssignedStoreUser == None),
                                literal('Auto').label('AssignType')), ],
                              else_=literal('Manual').label('AssignType')).label("AssignType")

    interval_condition_check = and_(DeliveryRequest.RecordCreatedDate < to_date,
                                    DeliveryRequest.RecordCreatedDate > from_date)

    base_query = db.session.query(literal('Delivery').label('ActivityType'),
                                  DeliveryRequest.DeliveryRequestId.label('ActivityId'),
                                  select_activity_category,
                                  select_booking_id, Order.OrderId, Order.EGRN,
                                  select_activity_date,
                                  select_time_slot_id,
                                  select_time_slot_from,
                                  select_time_slot_to,
                                  select_delivery_user_id,
                                  DeliveryUser.UserName.label('DeliveryUser'),
                                  Customer.CustomerId,
                                  Customer.CustomerCode,
                                  Customer.CustomerName,
                                  Customer.MobileNo,
                                  select_discount_code, select_coupon_code,
                                  CustomerAddres.CustAddressId, CustomerAddres.AddressLine1,
                                  select_address_line_2, select_address_line_3,
                                  DeliveryRequest.BranchCode,
                                  case([(Branch.IsActive == 0, 'Inact - ' + select_branch_name)],
                                       else_=select_branch_name).label('OriginalBranchName'),
                                  literal(' ').label('BranchName'),
                                  select_assign_type, select_modified_by, select_modified_date
                                  ).join(Customer,
                                         DeliveryRequest.CustomerId == Customer.CustomerId).outerjoin(
        DeliveryReschedule, DeliveryReschedule.DeliveryRequestId == DeliveryRequest.DeliveryRequestId).join(
        Order,
        DeliveryRequest.OrderId == Order.OrderId).join(
        CustomerAddres, select_address_id == CustomerAddres.CustAddressId).join(Branch,
                                                                                DeliveryRequest.BranchCode == Branch.BranchCode).outerjoin(
        DeliveryUser,
        select_delivery_user_id == DeliveryUser.DUserId).outerjoin(Delivery,
                                                                   Delivery.DeliveryRequestId == DeliveryRequest.DeliveryRequestId)

    # Omitting walk in orders.
    base_query = base_query.filter(DeliveryRequest.WalkIn == 0)

    if unassigned_only:
        # Only selects the delivery requests without delivery user.
        pending_deliveries = base_query.filter(
            or_(Order.IsDeleted == 0, Order.IsDeleted == None),
            select_delivery_user_id == None, DeliveryRequest.BranchCode.in_(store_user_branches),
            DeliveryRequest.IsDeleted == 0,
            Delivery.DeliveryId == None, interval_condition_check,
            or_(DeliveryReschedule.IsDeleted == 0, DeliveryReschedule.IsDeleted == None))
    else:

        # Getting assigned delivery requests.
        pending_deliveries = base_query.filter(
            or_(Order.IsDeleted == 0, Order.IsDeleted == None),
            DeliveryRequest.BranchCode.in_(store_user_branches),
            DeliveryRequest.IsDeleted == 0,
            select_delivery_user_id != None,
            Delivery.DeliveryId == None, interval_condition_check,
            or_(DeliveryReschedule.IsDeleted == 0, DeliveryReschedule.IsDeleted == None))

    if late_only:
        # If late_only flag is given in the request, return only late delivery requests.
        pending_deliveries = pending_deliveries.filter(select_activity_date < get_today(), interval_condition_check)
    return pending_deliveries
