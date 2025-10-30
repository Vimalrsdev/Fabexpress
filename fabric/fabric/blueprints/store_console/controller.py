f"""
------------------------
STORE WEB CONSOLE CONTROLLER
The Flask blueprint module consisting of set of functions/APIs that are used by the store person's web console.
------------------------
Created on May 20, 2020.
Coded by: Krishna Prasad K
© Jyothy Fabricare Services LTD.
------------------------
"""
import os
from datetime import datetime, timedelta, date
import uuid
import jwt
import json
from sqlalchemy.orm import aliased
import base64
import random
import requests

from flask import Blueprint, request, current_app, redirect, send_from_directory
# Edited by MMM
from sqlalchemy.orm.exc import MultipleResultsFound
from sqlalchemy import case, func, literal, text, or_, and_, desc, asc
# Edited by MMM
from flask_cors import CORS
from fabric.generic.classes import SerializeSQLAResult, CallSP, TravelDistanceCalculator, GenerateReport
from fabric import db
from fabric.modules.models import StoreUser, StoreUserLogin, PickupRequest, Order, DeliveryRequest, Delivery, \
    DeliveryUser, Branch, CustomerAddres, PickupReschedule, PickupTimeSlot, PickupRescheduleReason, \
    PickupCancelReason, DeliveryReschedule, DeliveryUserBranch, StoreUserBranch, OrderReview, OrderReviewReason, \
    DeliveryReview, DeliveryReviewReason, DeliveryUserLogin, BranchHoliday, DeliveryUserGPSLog, TransactionInfo, \
    TransactionPaymentInfo, StoreUserAttendance, OrderGarment, DeliveryGarment, Customer, GarmentStatusCode, Garment, \
    ServiceType, ServiceTat, DeliveryUserAttendance, TravelLog, Area, City, MessageLog, State, \
    MessageTemplate, PickupStatusCode, OrderStatusCode, GarmentCategory, GarmentUOM, PriceList, PushNotification, \
    CustomerTimeSlot, DeliveryUserDailyBranch, Rankingcityinfo, DeliveryUserEDCDetail, FabPickupTimeSlots, \
    PickupInstructions, CancellationReason,Screens,UserScreenAccess
from fabric.generic.functions import get_current_date, generate_final_data, populate_errors, \
    generate_hash, get_today, day_difference
from fabric.blueprints.delivery_app.helper import send_push_notification, rank_list, send_push_notification_test
from fabric.generic.loggers import error_logger
from fabric.middlewares.auth_guard import api_key_required, authenticate
from .forms import LoginForm, HomeForm, GetPendingActivitiesForm, GetAddressForm, GetTimeSlotsForm, CancelPickupForm, \
    ReschedulePickupForm, AssignPickupForm, GetDeliveryUsersForm, GetCompletedActivitiesForm, AssignDeliveryForm, \
    RegisterDeliveryUserForm, UpdateDeliveryUserForm, RegisterStoreUserForm, UpdateStoreUserForm, \
    RescheduleDeliveryForm, RemoveStoreUserForm, RemoveDeliveryUserForm, UpdateBranchForm, GetBranchHolidaysForm, \
    GetDeliveryUserGpsLogsForm, GetCollectedAmounts, GetEGRNsForPartialDeliveryForm, CreateDeliveryRequest, \
    GetGarmentsForPartialDeliveryForm, GetAttendanceLogsForm, EnableStoreUserForm, EnableDeliveryUserForm, \
    GetWalkInOrdersForm, GetOrderDetailsForm, AttendanceReportForm, MessageLogsReport, AddHangerForm, \
    GarmentDetailsForm, DuserActivityForm, BranchInactiveForm, GetBranchesForm, PushNotificationForm, \
    CustomerPreferredDayForm, SetCustomerPrefferedDayForm, RankForm, \
    GetCompletedActivitiesReportForm, GetCancelledPickupsForm, GetFabricareStoreUserBranchForm, \
    GetDeliveredWithoutPaymentForm, \
    GetPickupInstructions, AddIconsForm, DeleteIconForm, GetBranchForm, Cancel_Restriction_PickupForm, Cancel_Reason_PickupForm
from fabric.settings.project_settings import SERVER_DB
from . import queries as store_controller_queries
from fabric.blueprints.delivery_app import queries as delivery_controller_queries
from fabric.modules import common as common_module
# Importing the payment module library.
import fabric.modules.payment as payment_module
from fabric.generic.loggers import error_logger, info_logger
from sqlalchemy.orm import sessionmaker

store_console_blueprint = Blueprint("store_console", __name__, url_prefix='/store_console')

# Adding the CORS extension to avoid the CORS problem on this blueprint routes.
CORS(store_console_blueprint)


@store_console_blueprint.route('/')
def index():
    # Redirects to the JFSL website.
    return redirect("https://jfsl.in", code=302)



@store_console_blueprint.route('/console_refresh', methods=["POST"])
# @authenticate('store_user')
def console_refresh():
    """
    API for getting all the store branches.
    @return:
    """
    updated = False
    try:
        query = f""" EXEC JFSL.DBO.SpFabRefreshButtonConsole"""
        db.engine.execute(text(query).execution_options(autocommit=True))
        updated = True
    except Exception as e:
        error_logger(f'Route: {request.path}').error(e)

    if updated:
        final_data = generate_final_data('DATA_UPDATED')
    else:
        final_data = generate_final_data('DATA_UPDATE_FAILED')
    return final_data



# Edited by MMM
@store_console_blueprint.route('/get_ranking_cities', methods=["GET"])
@authenticate('store_user')
def get_ranking_cities():
    """
    API for getting all ranking cities
    """
    user_id = request.headers.get('user-id')
    # Getting the branch codes associated with the store user.
    store_user_branch_codes = store_controller_queries.get_store_user_branches(user_id)
    # Getting RankingCity, RankingCityName code from DB
    ranking_cities = db.session.query(Rankingcityinfo.RankingCity, Rankingcityinfo.RankingCityName).distinct(
        Rankingcityinfo.RankingCity).join(Area, Area.CityCode == Rankingcityinfo.CityCode).join(Branch,
                                                                                                Branch.AreaCode == Area.AreaCode).filter(
        Branch.BranchCode.in_(store_user_branch_codes)).all()

    ranking_cities = SerializeSQLAResult(ranking_cities).serialize()

    if ranking_cities:
        final_data = generate_final_data('DATA_FOUND')
        final_data['result'] = ranking_cities
    else:
        final_data = generate_final_data('DATA_NOT_FOUND')

    return final_data


@store_console_blueprint.route('/get_rank_list', methods=["POST"])
@authenticate('store_user')
def get_rank_list():
    """
    API for getting rank list based on city code
    """

    form = RankForm()
    if form.validate_on_submit():
        city_code = form.city_code.data
        report = form.report.data
        end_date = None if form.end_date.data == '' else form.end_date.data

        # Get monthly rank list detail's of delivery and pickup
        monthly_rank_lists = rank_list(None, "Month", [city_code], True, end_date, report)
        # Get daily rank list detail's of delivery and pickup
        today_rank_lists = rank_list(None, "Today", [city_code], True, end_date, report)

        if report:

            extra_sheets = [{'MonthlyPickupRankList': monthly_rank_lists['PickupRankList']},
                            {'MonthlyDeliveryRankList': monthly_rank_lists['DeliveryRankList']},
                            {'TodayPickupRankList': today_rank_lists['PickupRankList']},
                            {'TodayDeliveryRankList': today_rank_lists['DeliveryRankList']}]
            # Removing dicts in extra_sheets with empty list
            extra_sheets = [sheet for sheet in extra_sheets if next(iter((sheet.items())))[1]]

            if extra_sheets:

                report_link = GenerateReport(None, 'RankReport', True, extra_sheets).generate().get()

                if report_link is not None:
                    final_data = generate_final_data('DATA_FOUND')
                    final_data['result'] = report_link
                else:
                    # Failed to generate the file.
                    final_data = generate_final_data('FILE_NOT_FOUND')
            else:
                final_data = generate_final_data('DATA_NOT_FOUND')

        else:
            # Deleting unused key and values
            del monthly_rank_lists['MyRank'], monthly_rank_lists['DeliveryRankList']
            del today_rank_lists['MyRank'], today_rank_lists['DeliveryRankList']

            if len(monthly_rank_lists) > 0 and len(today_rank_lists) > 0:
                result = {
                    "Month": monthly_rank_lists['PickupRankList'],
                    "Today": today_rank_lists['PickupRankList']
                }

                final_data = generate_final_data('DATA_FOUND')
                final_data['result'] = result
            else:
                final_data = generate_final_data('DATA_NOT_FOUND')
    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(form.errors)

    return final_data


# @store_console_blueprint.route('/get_customer_preferred_delivery_time_slots', methods=["GET"])
# @authenticate('store_user')
# def get_customer_preferred_delivery_time_slots():
#     """
#     APi for getting customer preferred time slots
#     """
#     # Getting all the time slots form DB
#     time_slots = db.session.query(CustomerTimeSlot.TimeSlotId.label('PickupTimeSlotId'), CustomerTimeSlot.TimeSlotFrom,
#                                   CustomerTimeSlot.TimeSlotTo).filter(CustomerTimeSlot.IsDeleted == 0,
#                                                                       CustomerTimeSlot.IsActive == 1).all()

#     final_data = generate_final_data('DATA_FOUND')
#     final_data['result'] = SerializeSQLAResult(time_slots).serialize()

#     return final_data

@store_console_blueprint.route('/get_customer_preferred_delivery_time_slots', methods=["GET"])
# @authenticate('store_user')
def get_customer_preferred_delivery_time_slots():
    """
    APi for getting customer preferred time slots
    """
    # Getting all the time slots form DB
    time_slots = f""" EXEC JFSL.dbo.SPTimeSlotFabriccareCustApp @Branch_code =''"""
    time_slots = CallSP(time_slots).execute().fetchall()

    final_data = generate_final_data('DATA_FOUND')
    final_data['result'] = time_slots

    return final_data


@store_console_blueprint.route('/set_customer_preferred_day', methods=["POST"])
@authenticate('store_user')
def set_customer_preferred_day():
    """
    APi for updating customer preferred time slots and day
    """
    set_customer_preferred_day_form = SetCustomerPrefferedDayForm()
    if set_customer_preferred_day_form.validate_on_submit():
        day = set_customer_preferred_day_form.day.data
        time_slot = set_customer_preferred_day_form.time_slot.data
        customer_code = set_customer_preferred_day_form.customer_code.data
        action = set_customer_preferred_day_form.action.data

        user_id = request.headers.get('user-id')
        # Calling SP to create preferred date for the delivery of a customer
        result = store_controller_queries.set_customer_preferred_day(day, time_slot, customer_code, action, user_id)

        if result == 'UPDATED':

            # sp called in reschedule delivery for report
            time_slots = db.session.query(CustomerTimeSlot.TimeSlot).filter(
                CustomerTimeSlot.TimeSlotId == time_slot).one_or_none()
            slot = time_slots.TimeSlot
            query = f"EXEC {SERVER_DB}.dbo.SPFabFetchtimeslotForApp @SP_Type='2', @Egrno=null, @Customercode='{customer_code}', " \
                    f"@Timeslot='{slot}', @Datedt=null, @Days='{day}',@modifiedby='FabExpress',@branchcode=null"
            db.engine.execute(text(query).execution_options(autocommit=True))
            log_data = {
                'delivery reschedule': query
            }
            info_logger(f'Route: {request.path}').info(json.dumps(log_data))
            # Calling function to send SMS after setting customer preferred day
            store_controller_queries.send_sms_after_set_customer_preferred_day(customer_code, day)
            final_data = generate_final_data('DATA_SAVED')
        else:
            final_data = generate_final_data('DATA_SAVE_FAILED')

    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(set_customer_preferred_day_form.errors)

    return final_data


@store_console_blueprint.route('/get_customer_preferred_delivery_day', methods=["POST"])
@authenticate('store_user')
def get_customer_preferred_delivery_day():
    """
    Api for retrieving customer preferred delivery day
    """
    customer_preferred_day_form = CustomerPreferredDayForm()
    if customer_preferred_day_form.validate_on_submit():
        filter_type = None if customer_preferred_day_form.filter_type.data == '' else customer_preferred_day_form.filter_type.data
        filter_by = None if customer_preferred_day_form.filter_by.data == '' else customer_preferred_day_form.filter_by.data

        # Calling SP for getting result
        result = store_controller_queries.get_customer_preferred_delivery(filter_type, filter_by)
        time_slots = f""" EXEC JFSL.dbo.SPTimeSlotFabriccareCustApp @Branch_code =''"""
        time_slots = CallSP(time_slots).execute().fetchall()
        # Store the time slot id's to  a list
        data = []
        for time_slot in result:
            # If TIMESLOT exists in the time_slot dict
            if time_slot.get('TIMESLOT'):
                timeslot_id = time_slot['TIMESLOT']  

               
                slot_info = next((slot for slot in time_slots if slot['PickupTimeSlotId'] == timeslot_id), None)

                if slot_info:
                    TimeSlotFrom = slot_info.get('TimeSlotFrom')
                    TimeSlotTo = slot_info.get('TimeSlotTo')
                    time_slot['TIMESLOTNAME'] = f"{TimeSlotFrom} TO {TimeSlotTo}"

            # Append the modified time_slot to the data list
            data.append(time_slot)

        if len(data) == 0 and filter_type is not None and filter_by is not None:
            # Getting customer details from Db
            data = store_controller_queries.get_customer_preferred_delivery_from_db(filter_type, filter_by)

        if filter_type is None and filter_by is None and len(data) == 0:
            final_data = generate_final_data('DATA_NOT_FOUND')
        else:
            if len(data) > 0:
                final_data = generate_final_data('DATA_FOUND')
                final_data['result'] = data
            else:
                final_data = generate_final_data('CUSTOM_FAILED', 'No user found for given input')
    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(customer_preferred_day_form.errors)

    return final_data


@store_console_blueprint.route('/get_push_notifications', methods=["POST"])
@authenticate('store_user')
def get_push_notifications():
    """
    Api for retrieving all push notifications belongs to the corresponding delivery user
    :return: Paginated result
    """
    # Define number of rows in a page
    per_page = 5
    push_notification_form = PushNotificationForm()
    if push_notification_form.validate_on_submit():
        d_userid = push_notification_form.d_userid.data
        page = push_notification_form.page.data
        # Getting the push notification details from db
        notifications = db.session.query(PushNotification.PushNotificationId, PushNotification.DUserId,
                                         PushNotification.ImageUrl, PushNotification.Source, PushNotification.SentBy,
                                         PushNotification.Message, PushNotification.RecordCreatedDate,
                                         PushNotification.IsRead, PushNotification.ReadTime).filter(
            PushNotification.DUserId == d_userid).order_by(
            PushNotification.RecordCreatedDate.asc()).paginate(page, per_page, error_out=False)

        # store the details from db to a list for serializing
        notification_list = [document for document in notifications.items]

        if len(notification_list) > 0:
            final_data = generate_final_data('DATA_FOUND')
            final_data['result'] = SerializeSQLAResult(notification_list).serialize(full_date_fields=['ReadTime'])
        else:
            final_data = generate_final_data('DATA_NOT_FOUND')

    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(push_notification_form.errors)

    return final_data


@store_console_blueprint.route('/make_branch_inactive', methods=["POST"])
@authenticate('store_user')
def make_branch_inactive():
    """
    Api for making the branch inactive if active and vice versa
    :return:
    """
    branch_inactive_form = BranchInactiveForm()
    store_usr_id = request.headers.get('user-id')
    if branch_inactive_form.validate_on_submit():
        branch_code = branch_inactive_form.branch_code.data
        # Getting the branch details for updating
        branch = db.session.query(Branch).filter(Branch.BranchCode == branch_code, Branch.IsDeleted == 0).one_or_none()
        store_user = db.session.query(StoreUser).filter(StoreUser.SUserId == store_usr_id).one_or_none()
        store_usr_name = store_user.UserName

        if branch.IsActive is True:
            # Updating branch inactive
            branch.IsActive = False
            db.session.commit()
            #  For setting as Inactive
            inactive_query = f"exec {SERVER_DB}.dbo.UpdateBranchStatusInFabricare @branchcode={branch_code},@active=0, @name={store_usr_name}"
            db.engine.execute(text(inactive_query).execution_options(autocommit=True))
            log_data = {
                'branch inactive': inactive_query
            }
            info_logger(f'Route: {request.path}').info(json.dumps(log_data))
            final_data = generate_final_data('CUSTOM_SUCCESS', 'Successfully Make the branch inactive')
        else:
            # Updating branch active
            branch.IsActive = True
            db.session.commit()
            #  -- For setting as active
            active_query = f"exec {SERVER_DB}.dbo.UpdateBranchStatusInFabricare @branchcode={branch_code},@active=1,@name={store_usr_name}"
            db.engine.execute(text(active_query).execution_options(autocommit=True))
            log_data = {
                'branch inactive': active_query
            }
            info_logger(f'Route: {request.path}').info(json.dumps(log_data))

            final_data = generate_final_data('CUSTOM_SUCCESS', 'Successfully Make the branch active')

    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(branch_inactive_form.errors)

    return final_data


@store_console_blueprint.route('/duser_activity_log', methods=["POST"])
@authenticate('store_user')
def duser_activity_log():
    """
    Api for getting activities of the delivery user for the current day
    :return:
    """
    duser_activity_form = DuserActivityForm()
    if duser_activity_form.validate_on_submit():
        delivery_user_id = duser_activity_form.delivery_user_id.data
        # Adding a day to the current date
        next_date = (datetime.today() + timedelta(1))
        # Formatting the added date
        formatted_next_date = next_date.strftime("%Y-%m-%d 00:00:00")
        # Getting the clock in details from DB
        clockin_time = db.session.query(DeliveryUserAttendance.ClockInTime.label('ActivityTime'),
                                        literal('Clocked in').label('Activity'),
                                        DeliveryUserAttendance.ClockInLat.label('Lat'),
                                        DeliveryUserAttendance.ClockInLong.label('Long')).filter(
            DeliveryUserAttendance.DUserId == delivery_user_id,
            DeliveryUserAttendance.RecordCreatedDate.between(get_today(), formatted_next_date)).one_or_none()

        if clockin_time and clockin_time.ActivityTime:
            # Get gps logs from travel logs1
            completed_activities = db.session.query(TravelLog.RecordCreatedDate.label('ActivityTime'),
                                                    TravelLog.Activity, TravelLog.Lat, TravelLog.Long).filter(
                TravelLog.DUserId == delivery_user_id,
                TravelLog.RecordCreatedDate.between(get_today(), formatted_next_date)).order_by(
                TravelLog.RecordCreatedDate.asc()).all()

            # Insert clockin_time to completed_activities
            completed_activities.insert(0, clockin_time)
            # Get the clocked out time from DB
            clock_out_time = db.session.query(DeliveryUserAttendance.ClockOutTime.label('ActivityTime'),
                                              literal('Clocked out').label('Activity'),
                                              DeliveryUserAttendance.ClockOutLat.label('Lat'),
                                              DeliveryUserAttendance.ClockOutLong.label('Long')).filter(
                DeliveryUserAttendance.DUserId == delivery_user_id,
                DeliveryUserAttendance.RecordCreatedDate.between(get_today(), formatted_next_date)).one_or_none()

            if clock_out_time and clock_out_time.ActivityTime:
                # Appending to the completed_activities list
                completed_activities.append(clock_out_time)

            logs_details = SerializeSQLAResult(completed_activities).serialize(full_date_fields=['ActivityTime'])

            final_data = generate_final_data('DATA_FOUND')
            final_data['result'] = logs_details

        else:
            # if not clocked in the delivery user so no gps logs available
            final_data = generate_final_data('CUSTOM_FAILED', 'Delivery user not clocked in')

    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(duser_activity_form.errors)

    return final_data


@store_console_blueprint.route('/get_garments', methods=["GET"])
@authenticate('store_user')
def get_garments():
    """
    Api for getting all the garments
    @return: all garments
    """
    # Getting all garment details from DB
    garments = db.session.query(Garment.GarmentId, Garment.GarmentName, Garment.Description,
                                GarmentCategory.CategoryName, GarmentUOM.UOMName
                                , Garment.GarmentIcon, Garment.GarmentPreference, Garment.IsActive,
                                Garment.IsDeleted).join(GarmentCategory,
                                                        Garment.CategoryId == GarmentCategory.CategoryId).join(
        GarmentUOM, Garment.UOMId == GarmentUOM.UOMId).all()

    garments = SerializeSQLAResult(garments).serialize()
    final_data = generate_final_data('DATA_FOUND')
    final_data['result'] = garments

    return final_data


# @store_console_blueprint.route('/get_garments_details', methods=["POST"])
# @authenticate('store_user')
# def get_garments_details():
#     """
#     Api for getting all the garment details based on Branch code
#     @return: all garments
#     """
#     garment_form = GarmentDetailsForm()
#     if garment_form.validate_on_submit():
#         branch_codes = garment_form.branch_codes.data
#         # Select branch name if display name is none
#         select_branch_name = case(
#             [(or_(Branch.DisplayName == None, Branch.DisplayName == ''), Branch.BranchName), ],
#             else_=Branch.DisplayName).label("BranchName")

#         # Get garment details from DB
#         garments = db.session.query(GarmentUOM.UOMName, select_branch_name, ServiceTat.ServiceTatName,
#                                     Garment.GarmentId, Garment.GarmentName, ServiceType.ServiceTypeName,
#                                     Garment.Description, GarmentCategory.CategoryName, Garment.GarmentIcon,
#                                     Garment.GarmentPreference, Garment.IsActive, Garment.IsDeleted,
#                                     PriceList.BranchCode, Area.AreaName, City.CityName, State.StateName,
#                                     PriceList.IsHanger, PriceList.Id).join(PriceList,
#                                                                            Garment.GarmentId == PriceList.GarmentId).join(
#             GarmentUOM, Garment.UOMId == GarmentUOM.UOMId).join(GarmentCategory,
#                                                                 Garment.CategoryId == GarmentCategory.CategoryId).join(
#             Branch, PriceList.BranchCode == Branch.BranchCode).join(Area, Branch.AreaCode == Area.AreaCode).join(
#             ServiceType, PriceList.ServiceTypeId == ServiceType.ServiceTypeId).join(City,
#                                                                                     Area.CityCode == City.CityCode).join(
#             State, City.StateCode == State.StateCode).join(ServiceTat,
#                                                            PriceList.ServiceTatId == ServiceTat.ServiceTatId).filter(
#             PriceList.IsActive == 1, PriceList.IsDeleted == 0, PriceList.BranchCode.in_(branch_codes),
#             PriceList.ServiceTypeId.in_([1, 2, 10])).order_by(PriceList.Id.asc()).all()

#         garments = SerializeSQLAResult(garments).serialize()
#         final_data = generate_final_data('DATA_FOUND')
#         final_data['result'] = garments
#     else:
#         # Form validation error.
#         final_data = generate_final_data('FORM_ERROR')
#         final_data['errors'] = populate_errors(garment_form.errors)

#     return final_data

@store_console_blueprint.route('/get_garments_details', methods=["POST"])
# @authenticate('store_user')
def get_garments_details():
    """
    Api for getting all the garment details based on Branch code
    @return: all garments
    """
    garment_form = GarmentDetailsForm()
    if garment_form.validate_on_submit():
        branch_codes = garment_form.branch_codes.data
        # Select branch name if display name is none
        query = f""" EXEC JFSL.DBO.SPFabGarmentsListConsole @BRANCHCODE = '{branch_codes[0]}'"""
        garments = CallSP(query).execute().fetchall()
        final_data = generate_final_data('DATA_FOUND')
        final_data['result'] = garments
    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(garment_form.errors)

    return final_data


@store_console_blueprint.route('/add_hanger', methods=["POST"])
@authenticate('store_user')
def add_hanger():
    """
    Api for adding default hanger to a list of garment
    @return:
    """
    hanger_form = AddHangerForm()
    if hanger_form.validate_on_submit():
        data = hanger_form.data.data
        final_data = ''
        for obj in data:
            # Get garment detail of corresponding price_list id
            garments = db.session.query(PriceList).filter(PriceList.Id == obj['price_list_id']).one_or_none()

            if garments:
                # Updating is_hanger in the given list of price_list id's
                garments.IsHanger = obj['is_selected']
                db.session.commit()
                final_data = generate_final_data('DATA_UPDATED')
            else:
                final_data = generate_final_data('DATA_UPDATE_FAILED')
    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(hanger_form.errors)

    return final_data


# Edited by MMM
@store_console_blueprint.route('/loginOld', methods=["POST"])
@api_key_required
def loginOld():
    """
    Login API for the store admin users.
    @return: Final response contains the access key (if validation successful) or failed message
    """
    login_form = LoginForm()
    if login_form.validate_on_submit():
        mobile_number = login_form.mobile_number.data
        password = login_form.password.data
        # Generating the password hash to compare with the DB data
        hashed_password = generate_hash(password, 50)
        try:
            # Getting the store user details from the DB.
            store_user = db.session.query(StoreUser.SUserId, StoreUser.UserName, StoreUser.EmailId,
                                          StoreUser.IsAdmin, StoreUser.IsZIC).filter(
                StoreUser.MobileNo == mobile_number,
                StoreUser.Password == hashed_password, StoreUser.IsDeleted == 0).one_or_none()
            # Edited by MMM
            select_branch_name = case(
                [(or_(Branch.DisplayName == None, Branch.DisplayName == ''), Branch.BranchName), ],
                else_=Branch.DisplayName).label("BranchName")
            if store_user.IsAdmin:
                s_user_branches = db.session.query(StoreUserBranch.BranchCode, select_branch_name).join(Branch,
                                                                                                        Branch.IsActive == 1).filter(
                    StoreUserBranch.IsDeleted == 0, StoreUserBranch.BranchCode == Branch.BranchCode).all()
            else:
                s_user_branches = db.session.query(StoreUserBranch.BranchCode, select_branch_name).join(Branch,
                                                                                                        Branch.IsActive == 1).filter(
                    StoreUserBranch.SUserId == store_user.SUserId,
                    StoreUserBranch.IsDeleted == 0, StoreUserBranch.BranchCode == Branch.BranchCode).all()
            store_user_branches = SerializeSQLAResult(s_user_branches).serialize()
            # Edited by MMM
            if store_user is not None:

                # If the store user is found then add login details into StoreUserLogin table.
                access_key = jwt.encode({'id': str(uuid.uuid1())},
                                        current_app.config['JWT_SECRET_KEY'] + str(store_user.SUserId),
                                        algorithm='HS256')

                # Setting up user_agent dict for saving the basic client device details.
                user_agent = {'browser': request.user_agent.browser, 'language': request.user_agent.language,
                              'platform': request.user_agent.platform,
                              'string': request.user_agent.string,
                              'version': request.user_agent.version,
                              'ip_addr': request.remote_addr
                              }

                # Setting up the device type based on user agent's platform.
                ua_platform = user_agent['platform'] if user_agent['platform'] is not None else ''
                if ua_platform.lower() in ('iphone', 'android'):
                    device_type = 'M'
                elif ua_platform.lower() in ('windows', 'linux'):
                    device_type = 'C'
                else:
                    device_type = 'O'

                new_store_user_login = StoreUserLogin(SUserId=store_user.SUserId,
                                                      LoginTime=get_current_date(),
                                                      AuthKey=access_key.decode('utf-8'),
                                                      AuthKeyExpiry=0,
                                                      LastAccessTime=get_current_date(),
                                                      IsActive=1,
                                                      DeviceType=device_type,
                                                      DeviceIP=user_agent['ip_addr'],
                                                      Browser=user_agent['browser'],
                                                      Platform=user_agent['platform'],
                                                      Language=user_agent['language'],
                                                      UAString=user_agent['string'],
                                                      UAVersion=user_agent['version'],
                                                      RecordCreatedDate=get_current_date(),
                                                      RecordVersion=0
                                                      )
                try:
                    db.session.add(new_store_user_login)
                    db.session.commit()
                    final_data = generate_final_data("DATA_SAVED")
                    result = {
                        'AccessKey': access_key.decode('utf-8'), 'UserId': store_user.SUserId,
                        'Name': store_user.UserName,
                        'Email': store_user.EmailId,
                        'Admin': store_user.IsAdmin,
                        'ZIC': store_user.IsZIC,
                        'Branches': store_user_branches,
                    }
                    final_data['result'] = result
                except Exception as e:
                    db.session.rollback()
                    error_logger(f'Route: {request.path}').error(e)
                    final_data = generate_final_data('DATA_SAVE_FAILED')
            else:
                # If the store user is not found, generate the error.
                final_data = generate_final_data('DATA_NOT_FOUND')
        except Exception as e:
            # Any DB error is occurred.
            error_logger(f'Route: {request.path}').error(e)
            final_data = generate_final_data('FAILED')

    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(login_form.errors)

    return final_data


@store_console_blueprint.route('/login', methods=["POST"])
@api_key_required
def login():
    """
    Login API for the store admin users.
    @return: Final response contains the access key (if validation successful) or failed message
    """
    login_form = LoginForm()
    if login_form.validate_on_submit():
        mobile_number = login_form.mobile_number.data
        password = login_form.password.data
        # Generating the password hash to compare with the DB data
        hashed_password = generate_hash(password, 50)
        try:
            # Getting the store user details from the DB.
            store_user = db.session.query(StoreUser.SUserId, StoreUser.UserName, StoreUser.EmailId,
                                          StoreUser.IsAdmin, StoreUser.IsZIC,StoreUser.ProductScreenPermission).filter(
                StoreUser.MobileNo == mobile_number,
                StoreUser.Password == hashed_password, StoreUser.IsDeleted == 0).one_or_none()
            # Edited by MMM
            select_branch_name = case(
                [(or_(Branch.DisplayName == None, Branch.DisplayName == ''), Branch.BranchName), ],
                else_=Branch.DisplayName).label("BranchName")
            if store_user.IsAdmin:
                s_user_branches = db.session.query(StoreUserBranch.BranchCode, select_branch_name).join(Branch,
                                                                                                        Branch.IsActive == 1).filter(
                    StoreUserBranch.IsDeleted == 0, StoreUserBranch.BranchCode == Branch.BranchCode).all()
            else:
                s_user_branches = db.session.query(StoreUserBranch.BranchCode, select_branch_name).join(Branch,
                                                                                                        Branch.IsActive == 1).filter(
                    StoreUserBranch.SUserId == store_user.SUserId,
                    StoreUserBranch.IsDeleted == 0, StoreUserBranch.BranchCode == Branch.BranchCode).all()
            store_user_branches = SerializeSQLAResult(s_user_branches).serialize()
            # Edited by MMM
            if store_user is not None:

                # If the store user is found then add login details into StoreUserLogin table.
                access_key = jwt.encode({'id': str(uuid.uuid1())},
                                        current_app.config['JWT_SECRET_KEY'] + str(store_user.SUserId),
                                        algorithm='HS256')
                log_data = {
                    'access_key': access_key
                }
                info_logger(f'Route: {request.path}').info(json.dumps(log_data))

                # Setting up user_agent dict for saving the basic client device details.
                user_agent = {'browser': request.user_agent.browser, 'language': request.user_agent.language,
                              'platform': request.user_agent.platform,
                              'string': request.user_agent.string,
                              'version': request.user_agent.version,
                              'ip_addr': request.remote_addr
                              }

                # Setting up the device type based on user agent's platform.
                ua_platform = user_agent['platform'] if user_agent['platform'] is not None else ''
                if ua_platform.lower() in ('iphone', 'android'):
                    device_type = 'M'
                elif ua_platform.lower() in ('windows', 'linux'):
                    device_type = 'C'
                else:
                    device_type = 'O'

                new_store_user_login = StoreUserLogin(SUserId=store_user.SUserId,
                                                      LoginTime=get_current_date(),
                                                      # AuthKey=access_key.decode('utf-8'),
                                                      AuthKey=access_key,
                                                      AuthKeyExpiry=0,
                                                      LastAccessTime=get_current_date(),
                                                      IsActive=1,
                                                      DeviceType=device_type,
                                                      DeviceIP=user_agent['ip_addr'],
                                                      Browser=user_agent['browser'],
                                                      Platform=user_agent['platform'],
                                                      Language=user_agent['language'],
                                                      UAString=user_agent['string'],
                                                      UAVersion=user_agent['version'],
                                                      RecordCreatedDate=get_current_date(),
                                                      RecordVersion=0
                                                      )
                try:
                    db.session.add(new_store_user_login)
                    db.session.commit()
                    screen_access = db.session.execute(text("""
                        SELECT S.ScreenName,S.ScreenId
                        FROM Screens S
                        LEFT JOIN UserScreenAccess Ua ON Ua.UserId = :user_id
                        CROSS APPLY STRING_SPLIT(Ua.ScreenId, ',') AS split
                        WHERE S.ScreenId = TRY_CAST(split.value AS INT)
                    """), {"user_id": store_user.SUserId}).fetchall()

                    screen_access = SerializeSQLAResult(screen_access).serialize()
                    final_data = generate_final_data("DATA_SAVED")
                    result = {
                        # 'AccessKey': access_key.decode('utf-8'), 'UserId': store_user.SUserId,
                        'AccessKey': access_key, 'UserId': store_user.SUserId,
                        'Name': store_user.UserName,
                        'Email': store_user.EmailId,
                        'Admin': store_user.IsAdmin,
                        'ZIC': store_user.IsZIC,
                        'Branches': store_user_branches,
                        'ProductPermission':store_user.ProductScreenPermission,
                        "screen_access":screen_access,
                    }
                    final_data['result'] = result
                except Exception as e:
                    db.session.rollback()
                    error_logger(f'Route: {request.path}').error(e)
                    final_data = generate_final_data('DATA_SAVE_FAILED')
            else:
                # If the store user is not found, generate the error.
                final_data = generate_final_data('DATA_NOT_FOUND')
        except Exception as e:
            # Any DB error is occurred.
            error_logger(f'Route: {request.path}').error(e)
            final_data = generate_final_data('FAILED')

    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(login_form.errors)

    return final_data


# @store_console_blueprint.route('/essential_data', methods=["GET"])
# @authenticate('store_user')
# def essential_data(inactive=0):
#     """
#     API for getting the essential data about the store user.
#     @return:
#     """
#     user_id = request.headers.get('user-id')
#     inactive = request.args.get('inactive')
#     inactive = True

#     states = []
#     cities = []
#     branches = []

#     # Getting the branch codes associated with the store user.
#     store_user_branch_codes = store_controller_queries.get_store_user_branches(user_id, allow_inactive=inactive)
#     # Getting the states, cities and branches belongs to the store user.
#     try:
#         states = store_controller_queries.get_states(store_user_branch_codes)
#         cities = store_controller_queries.get_cities(store_user_branch_codes)
#         branches = store_controller_queries.get_branches_with_all_details(store_user_branch_codes, inactive)
#     except Exception as e:
#         error_logger(f'Route: {request.path}').error(e)
#     if states and cities and branches:
#         final_data = generate_final_data('DATA_FOUND')
#         result = {
#             'States': SerializeSQLAResult(states).serialize(),
#             'Cities': SerializeSQLAResult(cities).serialize(),
#             'Branches': SerializeSQLAResult(branches).serialize(),

#         }
#         final_data['result'] = result
#     else:
#         final_data = generate_final_data('DATA_NOT_FOUND')

#     return final_data

@store_console_blueprint.route('/essential_data', methods=["GET"])
# @authenticate('store_user')
def essential_data(inactive=0):
    """
    API for getting the essential data about the store user.
    @return:
    """
    user_id = request.headers.get('user-id')
    states = []
    cities = []
    branches = []

    try:
        query = f"""EXEC JFSL.DBO.SPFabStoreBranchInfo @store_user_id = {user_id}"""
        branches_data = CallSP(query).execute().fetchall()

        for branch in branches_data:
            branch_info = {
                'BranchCode': branch['BranchCode'],
                'BranchName': branch['BranchName'],
                'BranchAddress': branch['BranchAddress'],
                'StateCode': branch['StateCode'],
                'StateName': branch['StateName'],
                'CityCode': branch['CityCode'],
                'CityName': branch['CityName']
            }
            branches.append(branch_info)

            state_info = {
                'StateCode': branch['StateCode'],
                'StateName': branch['StateName']
            }
            states.append(state_info)

            city_info = {
                'CityCode': branch['CityCode'],
                'CityName': branch['CityName']
            }
            cities.append(city_info)
    except Exception as e:
        error_logger(f'Route: {request.path}').error(e)
    if states and cities and branches:
        final_data = generate_final_data('DATA_FOUND')
        result = {
            'States': states,
            'Cities': cities,
            'Branches': branches,

        }
        final_data['result'] = result
    else:
        final_data = generate_final_data('DATA_NOT_FOUND')

    return final_data

@store_console_blueprint.route('/logout', methods=["POST"])
@authenticate('store_user')
def logout():
    """
    Logout API for the store users.
    @return: If the validations are successful, make the access token expire
    by changing the values(AuthKeyExpiry, IsActive) in the StoreUserLogin table.
    """
    result = False
    try:
        user_id = request.headers.get('user_id')
        access_key = request.headers.get('access_key')
        login_data = db.session.query(StoreUserLogin).filter(StoreUserLogin.SUserId == user_id,
                                                             StoreUserLogin.AuthKey == access_key,
                                                             StoreUserLogin.AuthKeyExpiry == 0).one_or_none()
        if login_data is not None:
            login_data.AuthKeyExpiry = 1
            login_data.IsActive = 0
            db.session.commit()
            result = True

    except Exception as e:
        db.session.rollback()
        error_logger(f'Route: {request.path}').error(e)

    if result:
        final_data = generate_final_data('SUCCESS')
    else:
        final_data = generate_final_data('FAILED')

    return final_data


@store_console_blueprint.route('/alerts', methods=["GET"])
@authenticate('store_user')
def alerts():
    """
    API for getting the latest alerts from the server (If any).
    @return:
    """
    attendance = None
    user_id = request.headers.get('user-id')
    try:
        # Checking for today's attendance.
        attendance = store_controller_queries.attendance_for_today(user_id)
    except Exception as e:
        error_logger(f'Route: {request.path}').error(e)
    if attendance is not None:
        final_data = generate_final_data('DATA_FOUND')
        result = {'Attendance': SerializeSQLAResult(attendance).serialize_one(), 'AppVersionRequired': None}
        final_data['result'] = result
    else:
        # Since AppVersionRequired will always present, this case is also a DATA_FOUND case.
        final_data = generate_final_data('DATA_FOUND')
        result = {'AppVersionRequired': None}
        final_data['result'] = result
    return final_data


@store_console_blueprint.route('/clock_in', methods=["POST"])
@authenticate('store_user')
def clock_in():
    """
    API for marking the clock in time of the store user.
    @return:
    """
    user_id = request.headers.get('user-id')
    today = datetime.today().strftime("%Y-%m-%d")
    clocked_in = False
    error_msg = ''
    try:
        # Checking for today's attendance.
        attendance_record_of_today = store_controller_queries.attendance_for_today(user_id)
        if attendance_record_of_today is None:
            # No previous clock in record found for today.
            new_clock_in = StoreUserAttendance(
                SUserId=user_id,
                Date=today,
                ClockInTime=get_current_date(),
                RecordCreatedDate=get_current_date()
            )
            # Saving the clock in details for the day.
            db.session.add(new_clock_in)
            db.session.commit()
            clocked_in = True

        else:
            # Already a record is found.
            error_msg = "You've already clocked in for today!"
    except Exception as e:
        db.session.rollback()
        error_logger(f'Route: {request.path}').error(e)

    if clocked_in:
        final_data = generate_final_data('DATA_SAVED')
    else:
        if error_msg:
            final_data = generate_final_data('CUSTOM_FAILED', error_msg)
        else:
            final_data = generate_final_data('DATA_SAVE_FAILED')

    return final_data


@store_console_blueprint.route('/clock_out', methods=["POST"])
@authenticate('store_user')
def clock_out():
    """
    API for marking the clock out time of the store user.
    @return:
    """
    user_id = request.headers.get('user-id')
    today = datetime.today().strftime("%Y-%m-%d")
    clocked_out = False
    error_msg = ''
    try:
        # Checking for today's attendance.
        attendance_record_of_today = db.session.query(StoreUserAttendance).filter(
            StoreUserAttendance.SUserId == user_id,
            StoreUserAttendance.Date == today,
            StoreUserAttendance.IsDeleted == 0).one_or_none()
        if attendance_record_of_today is not None:
            # A attendance record found for today.
            if attendance_record_of_today.ClockOutTime is None:
                # No previous clock out time saved for today.
                attendance_record_of_today.ClockOutTime = get_current_date()
                attendance_record_of_today.RecordLastUpdatedDate = get_current_date()
                # Updating the attendance with the clock out time.
                db.session.commit()
                clocked_out = True
            else:
                # ClockOut time is already present for the day.
                error_msg = "You've already clocked out for today!"
        else:
            # No previous record has been found for today.
            error_msg = "No attendance found for today!"
    except Exception as e:
        db.session.rollback()
        error_logger(f'Route: {request.path}').error(e)

    if clocked_out:
        final_data = generate_final_data('DATA_UPDATED')
    else:
        if error_msg:
            final_data = generate_final_data('CUSTOM_FAILED', error_msg)
        else:
            final_data = generate_final_data('DATA_UPDATE_FAILED')

    return final_data


# @store_console_blueprint.route('/home', methods=["POST"])
# @authenticate('store_user')
# def home():
#     """
#     API for getting the home screen data.
#     @return:
#     """
#     home_form = HomeForm()
#     if home_form.validate_on_submit():
#         date = home_form.date.data
#         # Convert string date to datetime object.
#         date_obj = datetime.strptime(date, "%d-%m-%Y")
#         # From the date object, convert the date to YYYY-MM-DD format.
#         formatted_date = date_obj.strftime("%Y-%m-%d %H:%M:%S")
#         next_date = (date_obj + timedelta(1)).strftime("%Y-%m-%d 00:00:00")
#         branch_codes = home_form.branch_codes.data
#         state_codes = home_form.state_codes.data
#         city_codes = home_form.city_codes.data
#         delivery_user_id = home_form.delivery_user_id.data
#         report = home_form.report.data
#         user_id = request.headers.get('user-id')
#         home_data = {}
#         adhoc_pickup_revenue = 0
#         try:
#             if not branch_codes:
#                 # Getting the branches associated with the user.
#                 store_user_branches = store_controller_queries.get_store_user_branches(user_id, state_codes, city_codes)
#             else:
#                 # Branch codes are given.
#                 store_user_branches = branch_codes

#             if delivery_user_id is not None:
#                 # Delivery user id is given.
#                 delivery_users = [delivery_user_id]
#                 # Getting the delivery user attendance.
#                 delivery_user_attendance = db.session.query(DeliveryUserAttendance.Date,
#                                                             DeliveryUserAttendance.ClockInTime,
#                                                             DeliveryUserAttendance.ClockOutTime,
#                                                             DeliveryUserAttendance.ClockInLat,
#                                                             DeliveryUserAttendance.ClockInLong,
#                                                             DeliveryUserAttendance.ClockOutLat,
#                                                             DeliveryUserAttendance.ClockOutLong).filter(
#                     DeliveryUserAttendance.Date == formatted_date,
#                     DeliveryUserAttendance.DUserId == delivery_user_id).one_or_none()

#                 # Getting the travelled distance of the day.
#                 today = get_today()
#                 tomorrow = (datetime.today() + timedelta(1)).strftime("%Y-%m-%d 00:00:00")
#                 travel_logs = db.session.query(TravelLog).filter(TravelLog.DUserId == delivery_user_id,
#                                                                  TravelLog.RecordCreatedDate >= today,
#                                                                  TravelLog.RecordCreatedDate < tomorrow).all()

#                 # Calculating the total travel distance from the travel logs.
#                 travelled_distance = TravelDistanceCalculator().loop(travel_logs).distance()

#                 delivery_user_attendance = SerializeSQLAResult(delivery_user_attendance).serialize_one()
#                 delivery_user_attendance['TravelledDistance'] = travelled_distance
#             else:
#                 # No particular delivery users are given. so take this from store user branches.
#                 selected_delivery_users = db.session.query(DeliveryUser.DUserId).distinct(DeliveryUser.DUserId).join(
#                     DeliveryUserBranch, DeliveryUser.DUserId == DeliveryUserBranch.DUserId).filter(
#                     DeliveryUser.IsDeleted == 0, DeliveryUserBranch.BranchCode.in_(store_user_branches)).all()

#                 delivery_users = [delivery_user.DUserId for delivery_user in selected_delivery_users]

#                 delivery_user_attendance = {}

#             "---------------------------------------ADHOC PICKUPS STATS--------------------------------"
#             # If the pickup is rescheduled, then select RescheduledDate, else select PickupDate.
#             # select_pickup_date = case([(PickupReschedule.RescheduledDate == None, PickupRequest.PickupDate), ],
#             #                           else_=PickupReschedule.RescheduledDate).label("PickupDate")

#             # If the pickup is rescheduled, then select reschedule's BranchCode, else BranchCode of
#             # the pickup request.
#             # select_branch_code = case([(PickupReschedule.BranchCode == None, PickupRequest.BranchCode), ],
#             #                           else_=PickupReschedule.BranchCode).label("BranchCode")

#             # If the pickup is rescheduled, then select reschedule's DUserId, else DUserId of
#             # the pickup request.
#             # select_delivery_user_id_for_pickup = case([(PickupReschedule.DUserId == None, PickupRequest.DUserId), ],
#             #                                           else_=PickupReschedule.DUserId).label("DUserId")
#             # Total adhoc pickup request count.
#             # adhoc_pickups_count = db.session.query(func.count(PickupRequest.PickupRequestId)).outerjoin(
#             #     PickupReschedule,
#             #     PickupRequest.PickupRequestId == PickupReschedule.PickupRequestId).filter(
#             #     PickupRequest.PickupSource == 'Adhoc', PickupRequest.IsCancelled == 0,
#             #     select_pickup_date == formatted_date, select_branch_code.in_(store_user_branches),
#             #     PickupRequest.BookingId != None,
#             #     select_delivery_user_id_for_pickup.in_(delivery_users),
#             #     or_(PickupReschedule.IsDeleted == 0, PickupReschedule.IsDeleted == None)).scalar()

#             # adding single quotes to the next date
#             str_nxt_date = f"'{next_date}'"
#             # adding single quotes to the formatted date
#             str_date = f"'{formatted_date}'"
#             # Removing the list brackets for passing to raw sql
#             d_user_ids = str(delivery_users)[1:-1]
#             str_duser_ids = 'NULL' if d_user_ids == '' else d_user_ids
#             # Removing the list brackets for passing to raw sql
#             s_user_brnchs = str(store_user_branches)[1:-1]
#             str_store_user_branches = 'NULL' if s_user_brnchs == '' else s_user_brnchs
#             # Total adhoc pickup request count.
#             query = "SELECT count([PickupRequests].[PickupRequestId]) AS count_1 FROM [PickupRequests] LEFT OUTER JOIN [PickupReschedules] ON [PickupRequests].[PickupRequestId] = [PickupReschedules].[PickupRequestId] WHERE [PickupRequests].[PickupSource] = 'Adhoc' AND [PickupRequests].[IsCancelled] = 0 AND CASE WHEN ([PickupReschedules].[RescheduledDate] IS NULL) THEN [PickupRequests].[PickupDate] ELSE [PickupReschedules].[RescheduledDate] END = (%s) AND CASE WHEN ([PickupReschedules].[BranchCode] IS NULL) THEN [PickupRequests].[BranchCode] ELSE [PickupReschedules].[BranchCode] END IN (%s) AND [PickupRequests].[BookingId] IS NOT NULL AND CASE WHEN ([PickupReschedules].[DUserId] IS NULL) THEN [PickupRequests].[DUserId] ELSE [PickupReschedules].[DUserId] END IN (%s) AND ([PickupReschedules].[IsDeleted] = 0 OR [PickupReschedules].[IsDeleted] IS NULL)" % (
#                 str_date, str_store_user_branches, str_duser_ids)
#             query_result = db.engine.execute(query)
#             adhoc_pickups_count = query_result.first()[0]
#             # If the delivery is rescheduled, then select reschedule's DUserId, else DUserId of
#             # the delivery request.
#             # select_delivery_user_id = case(
#             #     [(DeliveryReschedule.DUserId == None, DeliveryRequest.DUserId), ],
#             #     else_=DeliveryReschedule.DUserId).label("DUserId")

#             # Calculating the total sum of service taxes.
#             # adhoc_pickup_service_tax = db.session.query(func.sum(Order.ServiceTaxAmount)).outerjoin(
#             #     PickupRequest, Order.PickupRequestId == PickupRequest.PickupRequestId).outerjoin(
#             #     PickupReschedule,
#             #     PickupRequest.PickupRequestId == PickupReschedule.PickupRequestId).filter(
#             #     PickupRequest.PickupSource == 'Adhoc', PickupRequest.IsCancelled == 0,
#             #     select_pickup_date == formatted_date, select_branch_code.in_(store_user_branches),
#             #     PickupRequest.BookingId != None,
#             #     select_delivery_user_id_for_pickup.in_(delivery_users),
#             #     or_(PickupReschedule.IsDeleted == 0, PickupReschedule.IsDeleted == None)).scalar()

#             # Calculating the total sum of service taxes.
#             query = "SELECT sum([Orders].[ServiceTaxAmount]) AS sum_1 FROM [Orders] LEFT OUTER JOIN [PickupRequests] ON [Orders].[PickupRequestId] = [PickupRequests].[PickupRequestId] LEFT OUTER JOIN [PickupReschedules] ON [PickupRequests].[PickupRequestId] = [PickupReschedules].[PickupRequestId] WHERE [PickupRequests].[PickupSource] = 'Adhoc' AND [PickupRequests].[IsCancelled] = 0 AND CASE WHEN ([PickupReschedules].[RescheduledDate] IS NULL) THEN [PickupRequests].[PickupDate] ELSE [PickupReschedules].[RescheduledDate] END = (%s) AND CASE WHEN ([PickupReschedules].[BranchCode] IS NULL) THEN [PickupRequests].[BranchCode] ELSE [PickupReschedules].[BranchCode] END IN (%s) AND [PickupRequests].[BookingId] IS NOT NULL AND CASE WHEN ([PickupReschedules].[DUserId] IS NULL) THEN [PickupRequests].[DUserId] ELSE [PickupReschedules].[DUserId] END IN (%s) AND ([PickupReschedules].[IsDeleted] = 0 OR [PickupReschedules].[IsDeleted] IS NULL)" % (
#                 str_date, str_store_user_branches, str_duser_ids)
#             query_result = db.engine.execute(query)
#             adhoc_pickup_service_tax = query_result.first()[0]

#             # Calculating the total sum of service taxes.
#             # adhoc_pickup_discount = db.session.query(func.sum(Order.Discount)).outerjoin(
#             #     PickupRequest, Order.PickupRequestId == PickupRequest.PickupRequestId).outerjoin(
#             #     PickupReschedule,
#             #     PickupRequest.PickupRequestId == PickupReschedule.PickupRequestId).filter(
#             #     PickupRequest.PickupSource == 'Adhoc', PickupRequest.IsCancelled == 0,
#             #     select_pickup_date == formatted_date, select_branch_code.in_(store_user_branches),
#             #     PickupRequest.BookingId != None,
#             #     select_delivery_user_id_for_pickup.in_(delivery_users),
#             #     or_(PickupReschedule.IsDeleted == 0, PickupReschedule.IsDeleted == None)).scalar()

#             # Calculating the total sum of basic amounts.
#             query = "SELECT sum([Orders].[Discount]) AS sum_1 FROM [Orders] LEFT OUTER JOIN [PickupRequests] ON [Orders].[PickupRequestId] = [PickupRequests].[PickupRequestId] LEFT OUTER JOIN [PickupReschedules] ON [PickupRequests].[PickupRequestId] = [PickupReschedules].[PickupRequestId] WHERE [PickupRequests].[PickupSource] = 'Adhoc' AND [PickupRequests].[IsCancelled] = 0 AND CASE WHEN ([PickupReschedules].[RescheduledDate] IS NULL) THEN [PickupRequests].[PickupDate] ELSE [PickupReschedules].[RescheduledDate] END = (%s) AND CASE WHEN ([PickupReschedules].[BranchCode] IS NULL) THEN [PickupRequests].[BranchCode] ELSE [PickupReschedules].[BranchCode] END IN (%s) AND [PickupRequests].[BookingId] IS NOT NULL AND CASE WHEN ([PickupReschedules].[DUserId] IS NULL) THEN [PickupRequests].[DUserId] ELSE [PickupReschedules].[DUserId] END IN (%s) AND ([PickupReschedules].[IsDeleted] = 0 OR [PickupReschedules].[IsDeleted] IS NULL)" % (
#                 str_date, str_store_user_branches, str_duser_ids)
#             query_result = db.engine.execute(query)
#             adhoc_pickup_discount = query_result.first()[0]
#             # Calculating the total sum of basic amounts.
#             # adhoc_pickup_basic_amount = db.session.query(func.sum(Order.BasicAmount)).outerjoin(
#             #     PickupRequest, Order.PickupRequestId == PickupRequest.PickupRequestId).outerjoin(
#             #     PickupReschedule,
#             #     PickupRequest.PickupRequestId == PickupReschedule.PickupRequestId).filter(
#             #     PickupRequest.PickupSource == 'Adhoc', PickupRequest.IsCancelled == 0,
#             #     select_pickup_date == formatted_date, select_branch_code.in_(store_user_branches),
#             #     PickupRequest.BookingId != None,
#             #     select_delivery_user_id_for_pickup.in_(delivery_users),
#             #     or_(PickupReschedule.IsDeleted == 0, PickupReschedule.IsDeleted == None)).scalar()

#             # Calculating the total sum of basic amounts.
#             query = "SELECT sum([Orders].[BasicAmount]) AS sum_1 FROM [Orders] LEFT OUTER JOIN [PickupRequests] ON [Orders].[PickupRequestId] = [PickupRequests].[PickupRequestId] LEFT OUTER JOIN [PickupReschedules] ON [PickupRequests].[PickupRequestId] = [PickupReschedules].[PickupRequestId] WHERE [PickupRequests].[PickupSource] = 'Adhoc' AND [PickupRequests].[IsCancelled] = 0 AND CASE WHEN ([PickupReschedules].[RescheduledDate] IS NULL) THEN [PickupRequests].[PickupDate] ELSE [PickupReschedules].[RescheduledDate] END = (%s) AND CASE WHEN ([PickupReschedules].[BranchCode] IS NULL) THEN [PickupRequests].[BranchCode] ELSE [PickupReschedules].[BranchCode] END IN (%s) AND [PickupRequests].[BookingId] IS NOT NULL AND CASE WHEN ([PickupReschedules].[DUserId] IS NULL) THEN [PickupRequests].[DUserId] ELSE [PickupReschedules].[DUserId] END IN (%s) AND ([PickupReschedules].[IsDeleted] = 0 OR [PickupReschedules].[IsDeleted] IS NULL)" % (
#                 str_date, str_store_user_branches, str_duser_ids)
#             query_result = db.engine.execute(query)
#             adhoc_pickup_basic_amount = query_result.first()[0]

#             adhoc_pickup_basic_amount = 0 if adhoc_pickup_basic_amount is None else adhoc_pickup_basic_amount

#             adhoc_pickup_service_tax = 0 if adhoc_pickup_service_tax is None else adhoc_pickup_service_tax

#             adhoc_pickup_discount = 0 if adhoc_pickup_discount is None else adhoc_pickup_discount

#             # Getting the adhoc pickup revenue (Estimated order amount from adhoc pickups).
#             adhoc_pickup_revenue = (adhoc_pickup_basic_amount - adhoc_pickup_discount) + adhoc_pickup_service_tax

#             "---------------------------------------ON TIME & LATE STATS--------------------------------"

#             pickup_stat = store_controller_queries.on_time_and_late_pickups_count(formatted_date, next_date,
#                                                                                   store_user_branches, delivery_users)
#             delivery_stat = store_controller_queries.on_time_and_late_deliveries_count(formatted_date, next_date,
#                                                                                        store_user_branches,
#                                                                                        delivery_users)

#             "---------------------------------------COLLECTION STATS--------------------------------"

#             # If the delivery is rescheduled, then select reschedule's DUserId, else DUserId of
#             # the delivery request.
#             # select_delivery_user_id = case(
#             #     [(DeliveryReschedule.DUserId == None, DeliveryRequest.DUserId), ],
#             #     else_=DeliveryReschedule.DUserId).label("DUserId")

#             # Base query for finding the cumulative sum of the collected amount.
#             # total_collection = db.session.query(
#             #     func.sum(TransactionPaymentInfo.PaymentAmount).label('TotalCollected')
#             # ).join(TransactionInfo, and_(
#             #     TransactionInfo.TransactionId == TransactionPaymentInfo.TransactionId,
#             #     TransactionInfo.PaymentId == TransactionPaymentInfo.PaymentId)).join(Order,
#             #                                                                          TransactionInfo.EGRNNo == Order.EGRN).join(
#             #     DeliveryRequest, Order.OrderId == DeliveryRequest.OrderId).outerjoin(DeliveryReschedule,
#             #                                                                          DeliveryRequest.DeliveryRequestId == DeliveryReschedule.DeliveryRequestId).filter(
#             #
#             #     DeliveryRequest.IsDeleted == 0,
#             #     Order.IsDeleted == 0,
#             #     Order.BranchCode.in_(store_user_branches),
#             #
#             #     or_(DeliveryReschedule.IsDeleted == 0, DeliveryReschedule.IsDeleted == None),
#             #     TransactionPaymentInfo.InvoiceNo != None, select_delivery_user_id.in_(delivery_users),
#             #     Order.OrderTypeId == 1,
#             #     and_(formatted_date < TransactionPaymentInfo.CreatedOn,
#             #          next_date > TransactionPaymentInfo.CreatedOn))

#             # Getting the cash collection.
#             # total_cash_collection = total_collection.filter(
#             #     TransactionPaymentInfo.PaymentMode.in_(['CASH_COLLECTION'])).scalar()

#             # Getting the cash collection.
#             query = "SELECT sum([TransactionPaymentInfo].[PaymentAmount]) AS [TotalCollected] FROM [TransactionPaymentInfo] JOIN [TransactionInfo] ON [TransactionInfo].[TransactionId] = [TransactionPaymentInfo].[TransactionId] AND [TransactionInfo].[PaymentId] = [TransactionPaymentInfo].[PaymentId] JOIN [Orders] ON [TransactionInfo].[EGRNNo] = [Orders].[EGRN] JOIN [DeliveryRequests] ON [Orders].[OrderId] = [DeliveryRequests].[OrderId] LEFT OUTER JOIN [DeliveryReschedules] ON [DeliveryRequests].[DeliveryRequestId] = [DeliveryReschedules].[DeliveryRequestId] WHERE [DeliveryRequests].[IsDeleted] = 0 AND [Orders].[IsDeleted] = 0 AND [Orders].[BranchCode] IN (%s) AND ([DeliveryReschedules].[IsDeleted] = 0 OR [DeliveryReschedules].[IsDeleted] IS NULL) AND [TransactionPaymentInfo].[InvoiceNo] IS NOT NULL AND CASE WHEN ([DeliveryReschedules].[DUserId] IS NULL) THEN [DeliveryRequests].[DUserId] ELSE [DeliveryReschedules].[DUserId] END IN (%s) AND [Orders].[OrderTypeId] = 1 AND [TransactionPaymentInfo].[CreatedOn] > (%s) AND [TransactionPaymentInfo].[CreatedOn] < (%s) AND [TransactionPaymentInfo].[PaymentMode] IN ('CASH_COLLECTION')" % (
#                 str_store_user_branches, str_duser_ids, str_date, str_nxt_date)
#             query_result = db.engine.execute(query)
#             total_cash_collection = query_result.first()[0]

#             total_cash_collection = 0 if total_cash_collection is None else total_cash_collection

#             # Getting the card collection.
#             # total_card_collection = total_collection.filter(
#             #     TransactionPaymentInfo.PaymentMode.in_(['CARD_COLLECTION'])).scalar()

#             # Getting the card collection.
#             query = "SELECT sum([TransactionPaymentInfo].[PaymentAmount]) AS [TotalCollected] FROM [TransactionPaymentInfo] JOIN [TransactionInfo] ON [TransactionInfo].[TransactionId] = [TransactionPaymentInfo].[TransactionId] AND [TransactionInfo].[PaymentId] = [TransactionPaymentInfo].[PaymentId] JOIN [Orders] ON [TransactionInfo].[EGRNNo] = [Orders].[EGRN] JOIN [DeliveryRequests] ON [Orders].[OrderId] = [DeliveryRequests].[OrderId] LEFT OUTER JOIN [DeliveryReschedules] ON [DeliveryRequests].[DeliveryRequestId] = [DeliveryReschedules].[DeliveryRequestId] WHERE [DeliveryRequests].[IsDeleted] = 0 AND [Orders].[IsDeleted] = 0 AND [Orders].[BranchCode] IN (%s) AND ([DeliveryReschedules].[IsDeleted] = 0 OR [DeliveryReschedules].[IsDeleted] IS NULL) AND [TransactionPaymentInfo].[InvoiceNo] IS NOT NULL AND CASE WHEN ([DeliveryReschedules].[DUserId] IS NULL) THEN [DeliveryRequests].[DUserId] ELSE [DeliveryReschedules].[DUserId] END IN (%s) AND [Orders].[OrderTypeId] = 1 AND [TransactionPaymentInfo].[CreatedOn] > (%s) AND [TransactionPaymentInfo].[CreatedOn] < (%s) AND [TransactionPaymentInfo].[PaymentMode] IN ('CARD_COLLECTION')" % (
#                 str_store_user_branches, str_duser_ids, str_date, str_nxt_date)
#             query_result = db.engine.execute(query)
#             total_card_collection = query_result.first()[0]

#             total_card_collection = 0 if total_card_collection is None else total_card_collection

#             # Getting the online payment collection (All the payment modes except .CASH_COLLECTION,
#             # CARD_COLLECTION and COUPON.
#             # total_online_payment_collection = total_collection.filter(
#             #     TransactionPaymentInfo.PaymentMode.notin_(
#             #         ['CASH_COLLECTION', 'CARD_COLLECTION', 'COUPON', 'coupon'])).scalar()

#             # Getting the online payment collection (All the payment modes except .CASH_COLLECTION,
#             # CARD_COLLECTION and COUPON.
#             query = "SELECT sum([TransactionPaymentInfo].[PaymentAmount]) AS [TotalCollected] FROM [TransactionPaymentInfo] JOIN [TransactionInfo] ON [TransactionInfo].[TransactionId] = [TransactionPaymentInfo].[TransactionId] AND [TransactionInfo].[PaymentId] = [TransactionPaymentInfo].[PaymentId] JOIN [Orders] ON [TransactionInfo].[EGRNNo] = [Orders].[EGRN] JOIN [DeliveryRequests] ON [Orders].[OrderId] = [DeliveryRequests].[OrderId] LEFT OUTER JOIN [DeliveryReschedules] ON [DeliveryRequests].[DeliveryRequestId] = [DeliveryReschedules].[DeliveryRequestId] WHERE [DeliveryRequests].[IsDeleted] = 0 AND [Orders].[IsDeleted] = 0 AND [Orders].[BranchCode] IN (%s) AND ([DeliveryReschedules].[IsDeleted] = 0 OR [DeliveryReschedules].[IsDeleted] IS NULL) AND [TransactionPaymentInfo].[InvoiceNo] IS NOT NULL AND CASE WHEN ([DeliveryReschedules].[DUserId] IS NULL) THEN [DeliveryRequests].[DUserId] ELSE [DeliveryReschedules].[DUserId] END IN (%s) AND [Orders].[OrderTypeId] = 1 AND [TransactionPaymentInfo].[CreatedOn] > (%s) AND [TransactionPaymentInfo].[CreatedOn] < (%s) AND [TransactionPaymentInfo].[PaymentMode] NOT IN ('CASH_COLLECTION', 'CARD_COLLECTION', 'COUPON', 'coupon')" % (
#                 str_store_user_branches, str_duser_ids, str_date, str_nxt_date)
#             query_result = db.engine.execute(query)
#             total_online_payment_collection = query_result.first()[0]

#             total_online_payment_collection = 0 if total_online_payment_collection is None else total_online_payment_collection
#             # Calculating the partial amounts.
#             # total_partial_payment_collection = db.session.query(
#             #     func.sum(PartialCollection.CollectedAmount).label('TotalCollected')).join(DeliveryRequest,
#             #                                                                               PartialCollection.DeliveryRequestId == DeliveryRequest.DeliveryRequestId).join(
#             #     Order, DeliveryRequest.OrderId == Order.OrderId).outerjoin(DeliveryReschedule,
#             #                                                                DeliveryRequest.DeliveryRequestId == DeliveryReschedule.DeliveryRequestId).filter(
#             #     DeliveryRequest.IsDeleted == 0,
#             #     Order.IsDeleted == 0,
#             #     Order.OrderTypeId == 1,
#             #     Order.BranchCode.in_(store_user_branches),
#             #     or_(DeliveryReschedule.IsDeleted == 0, DeliveryReschedule.IsDeleted == None),
#             #     select_delivery_user_id.in_(delivery_users),
#             #     and_(formatted_date < PartialCollection.RecordCreatedDate,
#             #          next_date > PartialCollection.RecordCreatedDate)
#             # )

#             # Getting the partial cash collection.
#             # total_partial_cash_collection = total_partial_payment_collection.filter(
#             #     PartialCollection.PaymentMode.in_(['CASH_COLLECTION'])).scalar()

#             # Getting the partial cash collection.
#             query = "SELECT sum([PartialCollections].[CollectedAmount]) AS [TotalCollected] FROM [PartialCollections] JOIN [DeliveryRequests] ON [PartialCollections].[DeliveryRequestId] = [DeliveryRequests].[DeliveryRequestId] JOIN [Orders] ON [DeliveryRequests].[OrderId] = [Orders].[OrderId] LEFT OUTER JOIN [DeliveryReschedules] ON [DeliveryRequests].[DeliveryRequestId] = [DeliveryReschedules].[DeliveryRequestId] WHERE [DeliveryRequests].[IsDeleted] = 0 AND [Orders].[IsDeleted] = 0 AND [Orders].[OrderTypeId] = 1 AND [Orders].[BranchCode] IN (%s) AND ([DeliveryReschedules].[IsDeleted] = 0 OR [DeliveryReschedules].[IsDeleted] IS NULL) AND CASE WHEN ([DeliveryReschedules].[DUserId] IS NULL) THEN [DeliveryRequests].[DUserId] ELSE [DeliveryReschedules].[DUserId] END IN (%s) AND [PartialCollections].[RecordCreatedDate] > (%s) AND [PartialCollections].[RecordCreatedDate] < (%s) AND [PartialCollections].[PaymentMode] IN ('CASH_COLLECTION')" % (
#                 str_store_user_branches, str_duser_ids, str_date, str_nxt_date)
#             query_result = db.engine.execute(query)
#             total_partial_cash_collection = query_result.first()[0]

#             if total_partial_cash_collection is not None:
#                 # Adding the partial amount to the cash collections.
#                 total_cash_collection += total_partial_cash_collection

#             # Getting the partial cash collection.
#             # total_partial_card_collection = total_partial_payment_collection.filter(
#             #     PartialCollection.PaymentMode.in_(['CARD_COLLECTION'])).scalar()

#             # Getting the partial card collection.
#             query = "SELECT sum([PartialCollections].[CollectedAmount]) AS [TotalCollected] FROM [PartialCollections] JOIN [DeliveryRequests] ON [PartialCollections].[DeliveryRequestId] = [DeliveryRequests].[DeliveryRequestId] JOIN [Orders] ON [DeliveryRequests].[OrderId] = [Orders].[OrderId] LEFT OUTER JOIN [DeliveryReschedules] ON [DeliveryRequests].[DeliveryRequestId] = [DeliveryReschedules].[DeliveryRequestId] WHERE [DeliveryRequests].[IsDeleted] = 0 AND [Orders].[IsDeleted] = 0 AND [Orders].[OrderTypeId] = 1 AND [Orders].[BranchCode] IN (%s) AND ([DeliveryReschedules].[IsDeleted] = 0 OR [DeliveryReschedules].[IsDeleted] IS NULL) AND CASE WHEN ([DeliveryReschedules].[DUserId] IS NULL) THEN [DeliveryRequests].[DUserId] ELSE [DeliveryReschedules].[DUserId] END IN (%s) AND [PartialCollections].[RecordCreatedDate] > (%s) AND [PartialCollections].[RecordCreatedDate] < (%s) AND [PartialCollections].[PaymentMode] IN ('CARD_COLLECTION')" % (
#                 str_store_user_branches, str_duser_ids, str_date, str_nxt_date)
#             query_result = db.engine.execute(query)
#             total_partial_card_collection = query_result.first()[0]

#             if total_partial_card_collection is not None:
#                 # Adding the partial amount to the card collections.
#                 total_card_collection += total_partial_card_collection

#             "---------------------------------------PENDING PICKUPS STATS--------------------------------"

#             # Getting the count of branch code's pickup requests where their status code is either pickup requested
#             # and confirmed and not created any orders
#             # pending_pickups_base_query = db.session.query(func.count(PickupRequest.PickupRequestId)).outerjoin(Order,
#             #                                                                                                    Order.PickupRequestId == PickupRequest.PickupRequestId).outerjoin(
#             #     PickupReschedule,
#             #     PickupReschedule.PickupRequestId == PickupRequest.PickupRequestId)

#             # If the pickup is rescheduled, then select RescheduledDate, else select PickupDate.
#             # select_pickup_date = case([(PickupReschedule.RescheduledDate == None, PickupRequest.PickupDate), ],
#             #                           else_=PickupReschedule.RescheduledDate).label("PickupDate")

#             # If the pickup is rescheduled, then select reschedule's BranchCode, else BranchCode of
#             # the pickup request.
#             # select_branch_code = case([(PickupReschedule.BranchCode == None, PickupRequest.BranchCode), ],
#             #                           else_=PickupReschedule.BranchCode).label("BranchCode")

#             # If the pickup is rescheduled, then select reschedule's DUserId, else DUserId of
#             # the pickup request.
#             select_delivery_user_id_for_pickup = case([(PickupReschedule.DUserId == None, PickupRequest.DUserId), ],
#                                                       else_=PickupReschedule.DUserId).label("DUserId")

#             # Total count of pending pickup requests under that branch code.
#             # pending_pickups_count = pending_pickups_base_query.filter(
#             #     PickupRequest.IsCancelled == 0, PickupRequest.PickupStatusId.in_((1, 2)),
#             #     select_pickup_date == formatted_date, select_branch_code.in_(store_user_branches),
#             #     select_delivery_user_id_for_pickup.in_(delivery_users),
#             #     Order.OrderId == None, PickupRequest.BookingId != None,
#             #     or_(PickupReschedule.IsDeleted == 0, PickupReschedule.IsDeleted == None)).scalar()

#             # Total count of pending pickup requests under that branch code.
#             query = "SELECT count([PickupRequests].[PickupRequestId]) AS count_1 FROM [PickupRequests] LEFT OUTER JOIN [Orders] ON [Orders].[PickupRequestId] = [PickupRequests].[PickupRequestId] LEFT OUTER JOIN [PickupReschedules] ON [PickupReschedules].[PickupRequestId] = [PickupRequests].[PickupRequestId] WHERE [PickupRequests].[IsCancelled] = 0 AND [PickupRequests].[PickupStatusId] IN (1, 2) AND CASE WHEN ([PickupReschedules].[RescheduledDate] IS NULL) THEN [PickupRequests].[PickupDate] ELSE [PickupReschedules].[RescheduledDate] END = (%s) AND CASE WHEN ([PickupReschedules].[BranchCode] IS NULL) THEN [PickupRequests].[BranchCode] ELSE [PickupReschedules].[BranchCode] END IN (%s) AND CASE WHEN ([PickupReschedules].[DUserId] IS NULL) THEN [PickupRequests].[DUserId] ELSE [PickupReschedules].[DUserId] END IN (%s) AND [Orders].[OrderId] IS NULL AND [PickupRequests].[BookingId] IS NOT NULL AND ([PickupReschedules].[IsDeleted] = 0 OR [PickupReschedules].[IsDeleted] IS NULL)" % (
#                 str_date, str_store_user_branches, str_duser_ids)
#             query_result = db.engine.execute(query)
#             pending_pickups_count = query_result.first()[0]

#             # Total count of unassigned pending pickup requests under that branch code.
#             # unassigned_pending_pickups_count = pending_pickups_base_query.filter(
#             #     PickupRequest.IsCancelled == 0, PickupRequest.PickupStatusId.in_((1, 2)),
#             #     select_pickup_date == formatted_date, select_branch_code.in_(store_user_branches),
#             #     select_delivery_user_id_for_pickup == None,
#             #     Order.EGRN == None, PickupRequest.BookingId != None,
#             #     or_(PickupReschedule.IsDeleted == 0, PickupReschedule.IsDeleted == None)).scalar()

#             # Total count of unassigned pending pickup requests under that branch code.
#             query = "SELECT count([PickupRequests].[PickupRequestId]) AS count_1 FROM [PickupRequests] LEFT OUTER JOIN [Orders] ON [Orders].[PickupRequestId] = [PickupRequests].[PickupRequestId] LEFT OUTER JOIN [PickupReschedules] ON [PickupReschedules].[PickupRequestId] = [PickupRequests].[PickupRequestId] WHERE [PickupRequests].[IsCancelled] = 0 AND [PickupRequests].[PickupStatusId] IN (1, 2) AND CASE WHEN ([PickupReschedules].[RescheduledDate] IS NULL) THEN [PickupRequests].[PickupDate] ELSE [PickupReschedules].[RescheduledDate] END = (%s) AND CASE WHEN ([PickupReschedules].[BranchCode] IS NULL) THEN [PickupRequests].[BranchCode] ELSE [PickupReschedules].[BranchCode] END IN (%s) AND CASE WHEN ([PickupReschedules].[DUserId] IS NULL) THEN [PickupRequests].[DUserId] ELSE [PickupReschedules].[DUserId] END IS NULL AND [Orders].[EGRN] IS NULL AND [PickupRequests].[BookingId] IS NOT NULL AND ([PickupReschedules].[IsDeleted] = 0 OR [PickupReschedules].[IsDeleted] IS NULL)" % (
#                 str_date, str_store_user_branches)
#             query_result = db.engine.execute(query)
#             unassigned_pending_pickups_count = query_result.first()[0]

#             # Total count of delayed pending pickups requests under that branch code.
#             # delayed_pending_pickups_count = pending_pickups_base_query.filter(
#             #     PickupRequest.IsCancelled == 0, PickupRequest.PickupStatusId.in_((1, 2)),
#             #     select_delivery_user_id_for_pickup.in_(delivery_users),
#             #     select_pickup_date < formatted_date, select_branch_code.in_(store_user_branches),
#             #     Order.EGRN == None, PickupRequest.BookingId != None,
#             #     or_(PickupReschedule.IsDeleted == 0, PickupReschedule.IsDeleted == None)) .scalar()

#             # Total count of delayed pending pickups requests under that branch code.
#             query = "SELECT count([PickupRequests].[PickupRequestId]) AS count_1 FROM [PickupRequests] LEFT OUTER JOIN [Orders] ON [Orders].[PickupRequestId] = [PickupRequests].[PickupRequestId] LEFT OUTER JOIN [PickupReschedules] ON [PickupReschedules].[PickupRequestId] = [PickupRequests].[PickupRequestId] WHERE [PickupRequests].[IsCancelled] = 0 AND [PickupRequests].[PickupStatusId] IN (1, 2) AND CASE WHEN ([PickupReschedules].[DUserId] IS NULL) THEN [PickupRequests].[DUserId] ELSE [PickupReschedules].[DUserId] END IN (%s) AND CASE WHEN ([PickupReschedules].[RescheduledDate] IS NULL) THEN [PickupRequests].[PickupDate] ELSE [PickupReschedules].[RescheduledDate] END < (%s) AND CASE WHEN ([PickupReschedules].[BranchCode] IS NULL) THEN [PickupRequests].[BranchCode] ELSE [PickupReschedules].[BranchCode] END IN (%s) AND [Orders].[EGRN] IS NULL AND [PickupRequests].[BookingId] IS NOT NULL AND ([PickupReschedules].[IsDeleted] = 0 OR [PickupReschedules].[IsDeleted] IS NULL)" % (
#                 str_duser_ids, str_date, str_store_user_branches)
#             query_result = db.engine.execute(query)
#             delayed_pending_pickups_count = query_result.first()[0]

#             "---------------------------------------PENDING DELIVERY STATS--------------------------------"

#             # If the delivery is rescheduled, then select RescheduledDate, else select DeliveryDate.
#             # select_delivery_date = case([(DeliveryReschedule.RescheduledDate == None, DeliveryRequest.DeliveryDate), ],
#             #                             else_=DeliveryReschedule.RescheduledDate).label("DeliveryDate")

#             # Here, the delivery date must be within the given date and next day.
#             # date_condition_check = and_(select_delivery_date < next_date,
#             #                             select_delivery_date >= formatted_date)

#             # If the delivery is rescheduled, then select reschedule's DUserId, else DUserId of
#             # the delivery request.
#             # select_delivery_user_id_for_delivery = case(
#             #     [(DeliveryReschedule.DUserId == None, DeliveryRequest.DUserId), ],
#             #     else_=DeliveryReschedule.DUserId).label("DUserId")

#             # Delivery request base query.
#             # pending_delivery_base_query = db.session.query(func.count(DeliveryRequest.DeliveryRequestId)).outerjoin(
#             #     Delivery, Delivery.DeliveryRequestId == DeliveryRequest.DeliveryRequestId).outerjoin(DeliveryReschedule,
#             #                                                                                          DeliveryReschedule.DeliveryRequestId == DeliveryRequest.DeliveryRequestId)

#             # Total count of pending delivery requests under that branch code.
#             # pending_deliveries_count = pending_delivery_base_query.filter(
#             #     Delivery.DeliveryId == None, select_delivery_user_id_for_delivery.in_(delivery_users),
#             #     DeliveryRequest.BranchCode.in_(store_user_branches), date_condition_check,
#             #     DeliveryRequest.IsDeleted == 0,
#             #     or_(DeliveryReschedule.IsDeleted == 0, DeliveryReschedule.IsDeleted == None)).scalar()

#             # Total count of pending delivery requests under that branch code.
#             query = "SELECT count([DeliveryRequests].[DeliveryRequestId]) AS count_1 FROM [DeliveryRequests] LEFT OUTER JOIN [Deliveries] ON [Deliveries].[DeliveryRequestId] = [DeliveryRequests].[DeliveryRequestId] LEFT OUTER JOIN [DeliveryReschedules] ON [DeliveryReschedules].[DeliveryRequestId] = [DeliveryRequests].[DeliveryRequestId] WHERE [Deliveries].[DeliveryId] IS NULL AND CASE WHEN ([DeliveryReschedules].[DUserId] IS NULL) THEN [DeliveryRequests].[DUserId] ELSE [DeliveryReschedules].[DUserId] END IN (%s) AND [DeliveryRequests].[BranchCode] IN (%s) AND CASE WHEN ([DeliveryReschedules].[RescheduledDate] IS NULL) THEN [DeliveryRequests].[DeliveryDate] ELSE [DeliveryReschedules].[RescheduledDate] END < (%s) AND CASE WHEN ([DeliveryReschedules].[RescheduledDate] IS NULL) THEN [DeliveryRequests].[DeliveryDate] ELSE [DeliveryReschedules].[RescheduledDate] END >= (%s) AND [DeliveryRequests].[IsDeleted] = 0 AND ([DeliveryReschedules].[IsDeleted] = 0 OR [DeliveryReschedules].[IsDeleted] IS NULL)" % (
#                 str_duser_ids, str_store_user_branches, str_nxt_date, str_date)
#             query_result = db.engine.execute(query)
#             pending_deliveries_count = query_result.first()[0]

#             # Total count of unassigned pending delivery requests under that branch code.
#             # unassigned_pending_delivery_count = pending_delivery_base_query.filter(
#             #     Delivery.DeliveryId == None, select_delivery_user_id_for_delivery == None,
#             #     DeliveryRequest.BranchCode.in_(store_user_branches), date_condition_check,
#             #     DeliveryRequest.IsDeleted == 0,
#             #     or_(DeliveryReschedule.IsDeleted == 0, DeliveryReschedule.IsDeleted == None)).scalar()

#             # Total count of unassigned pending delivery requests under that branch code.
#             query = "SELECT count([DeliveryRequests].[DeliveryRequestId]) AS count_1 FROM [DeliveryRequests] LEFT OUTER JOIN [Deliveries] ON [Deliveries].[DeliveryRequestId] = [DeliveryRequests].[DeliveryRequestId] LEFT OUTER JOIN [DeliveryReschedules] ON [DeliveryReschedules].[DeliveryRequestId] = [DeliveryRequests].[DeliveryRequestId] WHERE [Deliveries].[DeliveryId] IS NULL AND CASE WHEN ([DeliveryReschedules].[DUserId] IS NULL) THEN [DeliveryRequests].[DUserId] ELSE [DeliveryReschedules].[DUserId] END IS NULL AND [DeliveryRequests].[BranchCode] IN (%s) AND CASE WHEN ([DeliveryReschedules].[RescheduledDate] IS NULL) THEN [DeliveryRequests].[DeliveryDate] ELSE [DeliveryReschedules].[RescheduledDate] END < (%s) AND CASE WHEN ([DeliveryReschedules].[RescheduledDate] IS NULL) THEN [DeliveryRequests].[DeliveryDate] ELSE [DeliveryReschedules].[RescheduledDate] END >= (%s) AND [DeliveryRequests].[IsDeleted] = 0 AND ([DeliveryReschedules].[IsDeleted] = 0 OR [DeliveryReschedules].[IsDeleted] IS NULL)" % (
#                 str_store_user_branches, str_nxt_date, str_date)
#             query_result = db.engine.execute(query)
#             unassigned_pending_delivery_count = query_result.first()[0]

#             # Total count of delayed pending delivery requests under that branch code.
#             # delayed_pending_delivery_count = pending_delivery_base_query.filter(
#             #     Delivery.DeliveryId == None, select_delivery_user_id_for_delivery.in_(delivery_users),
#             #     DeliveryRequest.BranchCode.in_(store_user_branches), select_delivery_date < formatted_date,
#             #     DeliveryRequest.IsDeleted == 0,
#             #     or_(DeliveryReschedule.IsDeleted == 0, DeliveryReschedule.IsDeleted == None)).scalar()

#             # Total count of delayed pending delivery requests under that branch code.
#             query = "SELECT count([DeliveryRequests].[DeliveryRequestId]) AS count_1 FROM [DeliveryRequests] LEFT OUTER JOIN [Deliveries] ON [Deliveries].[DeliveryRequestId] = [DeliveryRequests].[DeliveryRequestId] LEFT OUTER JOIN [DeliveryReschedules] ON [DeliveryReschedules].[DeliveryRequestId] = [DeliveryRequests].[DeliveryRequestId] WHERE [Deliveries].[DeliveryId] IS NULL AND CASE WHEN ([DeliveryReschedules].[DUserId] IS NULL) THEN [DeliveryRequests].[DUserId] ELSE [DeliveryReschedules].[DUserId] END IN (%s) AND [DeliveryRequests].[BranchCode] IN (%s) AND CASE WHEN ([DeliveryReschedules].[RescheduledDate] IS NULL) THEN [DeliveryRequests].[DeliveryDate] ELSE [DeliveryReschedules].[RescheduledDate] END < (%s) AND [DeliveryRequests].[IsDeleted] = 0 AND ([DeliveryReschedules].[IsDeleted] = 0 OR [DeliveryReschedules].[IsDeleted] IS NULL)" % (
#                 str_duser_ids, str_store_user_branches, str_date)
#             query_result = db.engine.execute(query)
#             delayed_pending_delivery_count = query_result.first()[0]

#             "---------------------------------------COMPLETED ACTIVITY STATS--------------------------------"

#             # Here, the pickup completed date must be within the given date and next day.
#             # date_condition_check = and_(PickupRequest.RecordLastUpdatedDate < next_date,
#             #                             PickupRequest.RecordLastUpdatedDate > formatted_date)

#             # PickupStatusId 3 means pickup is completed.
#             # completed_pickup_count = db.session.query(func.count(PickupRequest.PickupRequestId)).outerjoin(
#             #     PickupReschedule, PickupReschedule.PickupRequestId == PickupRequest.PickupRequestId).filter(
#             #     PickupRequest.IsCancelled == 0, select_delivery_user_id_for_pickup.in_(delivery_users),
#             #     select_branch_code.in_(store_user_branches), PickupRequest.PickupStatusId == 3,
#             #     date_condition_check,
#             #     or_(PickupReschedule.IsDeleted == 0, PickupReschedule.IsDeleted == None)).scalar()

#             # Completed pickup count, PickupStatusId 3 means pickup is completed.
#             query = "SELECT count([PickupRequests].[PickupRequestId]) AS count_1 FROM [PickupRequests] LEFT OUTER JOIN [PickupReschedules] ON [PickupReschedules].[PickupRequestId] = [PickupRequests].[PickupRequestId] WHERE [PickupRequests].[IsCancelled] = 0 AND CASE WHEN ([PickupReschedules].[DUserId] IS NULL) THEN [PickupRequests].[DUserId] ELSE [PickupReschedules].[DUserId] END IN (%s) AND CASE WHEN ([PickupReschedules].[BranchCode] IS NULL) THEN [PickupRequests].[BranchCode] ELSE [PickupReschedules].[BranchCode] END IN (%s) AND [PickupRequests].[PickupStatusId] = 3 AND [PickupRequests].[RecordLastUpdatedDate] < (%s) AND [PickupRequests].[RecordLastUpdatedDate] > (%s) AND ([PickupReschedules].[IsDeleted] = 0 OR [PickupReschedules].[IsDeleted] IS NULL)" % (
#                 str_duser_ids, str_store_user_branches, str_nxt_date, str_date)
#             query_result = db.engine.execute(query)
#             completed_pickup_count = query_result.first()[0]

#             # Here, the delivery created must be within the given date and next day.
#             # date_condition_check = and_(Delivery.RecordLastUpdatedDate < next_date,
#             #                             Delivery.RecordLastUpdatedDate > formatted_date)

#             # Delivery request must have an corresponding entry in Deliveries table
#             # in order to consider it as delivered.
#             # completed_delivery_count = db.session.query(func.count(Delivery.DeliveryId)).filter(
#             #     Delivery.BranchCode.in_(store_user_branches), Delivery.DUserId.in_(delivery_users),
#             #     date_condition_check).scalar()

#             # Delivery request must have an corresponding entry in Deliveries table
#             # in order to consider it as delivered.
#             query = "SELECT count([Deliveries].[DeliveryId]) AS count_1 FROM [Deliveries] WHERE [Deliveries].[BranchCode] IN (%s) AND [Deliveries].[DUserId] IN (%s) AND [Deliveries].[RecordLastUpdatedDate] < (%s) AND [Deliveries].[RecordLastUpdatedDate] > (%s)" % (
#                 str_store_user_branches, str_duser_ids, str_nxt_date, str_date)
#             query_result = db.engine.execute(query)
#             completed_delivery_count = query_result.first()[0]

#             "---------------------------------------CANCELLED PICKUP STATS--------------------------------"

#             # Here, the pickup cancelled date must be within the given date and next day.
#             # date_condition_check = and_(PickupRequest.CancelledDate < next_date,
#             #                             PickupRequest.CancelledDate > formatted_date)

#             # PickupStatusId 4 means pickup is cancelled.
#             # cancelled_pickup_count = db.session.query(func.count(PickupRequest.PickupRequestId)).outerjoin(
#             #     PickupReschedule, PickupReschedule.PickupRequestId == PickupRequest.PickupRequestId).filter(
#             #     PickupRequest.IsCancelled == 1,
#             #     select_branch_code.in_(store_user_branches), select_delivery_user_id_for_pickup.in_(delivery_users),
#             #     PickupRequest.PickupStatusId == 4,
#             #     date_condition_check,
#             #     or_(PickupReschedule.IsDeleted == 0, PickupReschedule.IsDeleted == None)).scalar()

#             # PickupStatusId 4 means pickup is cancelled.
#             query = "SELECT count([PickupRequests].[PickupRequestId]) AS count_1 FROM [PickupRequests] LEFT OUTER JOIN [PickupReschedules] ON [PickupReschedules].[PickupRequestId] = [PickupRequests].[PickupRequestId] WHERE [PickupRequests].[IsCancelled] = 1 AND CASE WHEN ([PickupReschedules].[BranchCode] IS NULL) THEN [PickupRequests].[BranchCode] ELSE [PickupReschedules].[BranchCode] END IN (%s) AND CASE WHEN ([PickupReschedules].[DUserId] IS NULL) THEN [PickupRequests].[DUserId] ELSE [PickupReschedules].[DUserId] END IN (%s) AND [PickupRequests].[PickupStatusId] = 4 AND [PickupRequests].[CancelledDate] < (%s) AND [PickupRequests].[CancelledDate] > (%s) AND ([PickupReschedules].[IsDeleted] = 0 OR [PickupReschedules].[IsDeleted] IS NULL)" % (
#                 str_store_user_branches, str_duser_ids, str_nxt_date, str_date)
#             query_result = db.engine.execute(query)
#             cancelled_pickup_count = query_result.first()[0]

#             "---------------------------------------COMPLETED ACTIVITY LOGS--------------------------------"

#             # Generating the top 10 activity logs.
#             # Completed pickup request logs.
#             created_date = PickupRequest.RecordCreatedDate.label('Date')

#             # If the pickup is rescheduled, then select reschedule's BranchCode, else BranchCode of
#             # the pickup request.
#             select_branch_code = case([(PickupReschedule.BranchCode == None, PickupRequest.BranchCode), ],
#                                       else_=PickupReschedule.BranchCode).label("BranchCode")

#             # Here, the record created date must be within the given date and next day.
#             date_condition_check = and_(created_date < next_date, created_date > formatted_date)

#             date_diff = func.datediff(text('minute'), created_date, get_current_date())

#             pickup_request_logs = db.session.query(literal('PickupRequest').label("ActivityType"),
#                                                    PickupRequest.BookingId.label("ActivityId"), select_branch_code,
#                                                    select_delivery_user_id_for_pickup, DeliveryUser.UserName,
#                                                    created_date, date_diff.label('Diff')).outerjoin(PickupReschedule,
#                                                                                                     PickupReschedule.PickupRequestId == PickupRequest.PickupRequestId).join(
#                 DeliveryUser, select_delivery_user_id_for_pickup == DeliveryUser.DUserId).filter(
#                 select_branch_code.in_(store_user_branches), select_delivery_user_id_for_pickup.in_(delivery_users),
#                 PickupRequest.PickupStatusId.in_((1, 2)),
#                 or_(PickupReschedule.IsDeleted == 0, PickupReschedule.IsDeleted == None), date_condition_check)

#             # Completed pickup logs
#             # Here, the record created date must be within the given date and next day.
#             pickup_logs = db.session.query(literal('Pickup').label("ActivityType"),
#                                            PickupRequest.BookingId.label("ActivityId"), select_branch_code,
#                                            select_delivery_user_id_for_pickup, DeliveryUser.UserName, created_date,
#                                            date_diff.label('Diff')).outerjoin(PickupReschedule,
#                                                                               PickupReschedule.PickupRequestId == PickupRequest.PickupRequestId).join(
#                 DeliveryUser, select_delivery_user_id_for_pickup == DeliveryUser.DUserId).filter(
#                 select_branch_code.in_(store_user_branches), PickupRequest.PickupStatusId == 3,
#                                                              PickupRequest.BookingId != None,
#                 select_delivery_user_id_for_pickup.in_(delivery_users),
#                 or_(PickupReschedule.IsDeleted == 0, PickupReschedule.IsDeleted == None), date_condition_check)

#             # Completed delivery logs
#             created_date = Delivery.RecordCreatedDate.label('Date')

#             # Here, the record created date must be within the given date and next day.
#             date_condition_check = and_(created_date < next_date, created_date > formatted_date)

#             date_diff = func.datediff(text('minute'), created_date, get_current_date())
#             delivery_logs = db.session.query(literal('Delivery').label("ActivityType"),
#                                              Delivery.EGRN.label("ActivityId"), Delivery.BranchCode, Delivery.DUserId,
#                                              DeliveryUser.UserName, created_date, date_diff.label('Diff')).join(
#                 DeliveryUser, Delivery.DUserId == DeliveryUser.DUserId).filter(
#                 Delivery.BranchCode.in_(store_user_branches), Delivery.DUserId.in_(delivery_users),
#                 Delivery.BookingId != None, date_condition_check)

#             logs = pickup_request_logs.union(pickup_logs).union(delivery_logs).order_by(created_date.desc()).limit(
#                 10).all()

#             log_desc = []
#             for log in logs:
#                 result = {"desc": "", "time": ""}

#                 # Check if the minute difference is greater than an hour/day or not.
#                 minute_difference = log.Diff

#                 if minute_difference > 1440:
#                     # 1440 is the minutes in a day. So difference is greater than a day.
#                     # So convert it to days.
#                     time_diff = minute_difference / 1440
#                     measure = 'days'
#                 elif 60 < minute_difference < 1440:
#                     # Convert to hours
#                     time_diff = minute_difference / 60
#                     measure = 'hours'
#                 else:
#                     # Here, the time difference is less than 60
#                     time_diff = minute_difference
#                     measure = 'minutes'

#                 if log.ActivityType == 'PickupRequest':
#                     # This log is an pickup request activity.
#                     desc = f"A new pickup request (#BookingId {log.ActivityId} for Branch code {log.BranchCode})"
#                     time_desc = f"{round(time_diff)} {measure} ago."
#                 elif log.ActivityType == 'Pickup':
#                     # This log is an completed pickup activity.
#                     desc = f"{log.UserName} picked up the request (#BookingId {log.ActivityId} for Branch code {log.BranchCode})"
#                     time_desc = f"{round(time_diff)} {measure} ago."
#                 elif log.ActivityType == 'Delivery':
#                     # This log is an completed delivery activity.
#                     desc = f"{log.UserName} delivered the order (#EGRN {log.ActivityId} for Branch code {log.BranchCode})"
#                     time_desc = f"{round(time_diff)} {measure} ago."
#                 else:
#                     desc = ""
#                     time_desc = ""

#                 result["desc"] = desc
#                 result["time"] = time_desc

#                 log_desc.append(result)

#             home_data = {
#                 'Pickups': {
#                     'Completed': {
#                         'Count': completed_pickup_count,
#                         'HelpText': 'These are the number of pickups completed on the given date.'
#                     },
#                     'Pending': {
#                         'Count': pending_pickups_count + delayed_pending_pickups_count,
#                         'HelpText': 'These are the number of pickups that are pending for the given date (Including delayed).'
#                     },
#                     'Unassigned': {
#                         'Count': unassigned_pending_pickups_count,
#                         'HelpText': 'These are the number of unassigned pickups to date.'
#                     },
#                     'Cancelled': {
#                         'Count': cancelled_pickup_count,
#                         'HelpText': 'These are the number of pickups cancelled on the given date.'
#                     },
#                     # Delayed could be delayed pending and delayed completed
#                     'Delayed': {
#                         'Count': pickup_stat['late'] + delayed_pending_pickups_count,
#                         'HelpText': 'These are the number of pickups completed as delayed & pickups pending as delayed on the given date.'
#                     },
#                     'OnTime': {
#                         'Count': pickup_stat['on_time'],
#                         'HelpText': 'These are the number of pickups made on time on the given date.'
#                     },
#                     'Late': {
#                         'Count': pickup_stat['late'],
#                         'HelpText': 'These are the number of pickups completed as delayed on the given date.'
#                     },
#                     'Total': {
#                         'Count': cancelled_pickup_count + completed_pickup_count + (
#                                 pending_pickups_count + delayed_pending_pickups_count),
#                         'HelpText': 'The total sum of completed + cancelled + pending '
#                                     'based on the given date.'
#                     },

#                 },
#                 'Delivery': {
#                     'Completed': {
#                         'Count': completed_delivery_count,
#                         'HelpText': 'These are the number of deliveries completed on the given date.'
#                     },
#                     'Pending': {
#                         'Count': pending_deliveries_count + delayed_pending_delivery_count,
#                         'HelpText': 'These are the number of deliveries that are pending for the given date (Including delayed).'
#                     },
#                     'Unassigned': {
#                         'Count': unassigned_pending_delivery_count,
#                         'HelpText': 'These are the number of unassigned deliveries to date.'
#                     },
#                     'Delayed': {
#                         'Count': delivery_stat['late'] + delayed_pending_delivery_count,
#                         'HelpText': 'These are the number of deliveries completed as delayed & deliveries pending as delayed on the given date.'
#                     },
#                     'OnTime': {
#                         'Count': delivery_stat['on_time'],
#                         'HelpText': 'These are the number of deliveries made on time on the given date.'
#                     },
#                     'Late': {
#                         'Count': delivery_stat['late'],
#                         'HelpText': 'These are the number of deliveries made late on the given date.'
#                     },
#                     'Total': {
#                         'Count': completed_delivery_count + pending_deliveries_count + delayed_pending_delivery_count,
#                         'HelpText': 'The total sum of pending + completed '
#                                     'based on the given date.'
#                     }
#                 },
#                 'AdhocPickupsCount': adhoc_pickups_count,
#                 'AdhocPickupsRevenue': round(float(adhoc_pickup_revenue)),
#                 'AmountCollection': {
#                     'CashCollection': float(total_cash_collection),
#                     'CardCollection': float(total_card_collection),
#                     'OnlinePayment': float(total_online_payment_collection)
#                 },
#                 'ActivityLogs': log_desc,
#                 'DeliveryUserAttendance': delivery_user_attendance
#             }

#         except Exception as e:
#             error_logger(f'Route: {request.path}').error(e)
#         if home_data:
#             # Edited by MMM
#             final_data = generate_final_data('DATA_FOUND')
#             if report:
#                 # Report flag is included in the request. So generate the file and send the file back.
#                 report_data = [
#                     {
#                         'PickupsCompleted': home_data['Pickups']['Completed']['Count'],
#                         'PickupsUnassigned': home_data['Pickups']['Unassigned']['Count'],
#                         'PickupsPending': home_data['Pickups']['Pending']['Count'],
#                         'PickupsCancelled': home_data['Pickups']['Cancelled']['Count'],
#                         'PickupsTotal': home_data['Pickups']['Total']['Count'],
#                         'DeliveriesCompleted': home_data['Delivery']['Completed']['Count'],
#                         'DeliveriesUnassigned': home_data['Delivery']['Unassigned']['Count'],
#                         'DeliveriesPending': home_data['Delivery']['Pending']['Count'],
#                         'DeliveriesTotal': home_data['Delivery']['Total']['Count'],
#                         'AdhocPickupsCount': home_data['AdhocPickupsCount'],
#                         'AdhocPickupsRevenue': home_data['AdhocPickupsRevenue'],
#                         'CashCollection': home_data['AmountCollection']['CashCollection'],
#                         'CardCollection': home_data['AmountCollection']['CardCollection'],
#                         'OnlinePayment': home_data['AmountCollection']['OnlinePayment']
#                     }
#                 ]
#                 report_link = GenerateReport(report_data, 'dashboard').generate().get()
#                 if report_link is not None:
#                     final_data['result'] = report_link
#                 else:
#                     # Failed to generate the file.
#                     final_data = generate_final_data('FILE_NOT_FOUND')
#             else:
#                 final_data['result'] = home_data
#             # Edited by MMM
#         else:
#             final_data = generate_final_data('DATA_NOT_FOUND')
#     else:
#         # Form validation error.
#         final_data = generate_final_data('FORM_ERROR')
#         final_data['errors'] = populate_errors(home_form.errors)

#     return final_data

from datetime import datetime, timedelta
@store_console_blueprint.route('/home', methods=["POST"])
# @authenticate('store_user')
def home_():
    """
    API for getting the home screen data.
    @return:
    """
    home_form = HomeForm()
    if home_form.validate_on_submit():
        date = home_form.date.data
        log_data = {
             'home_form': home_form.data
            }
        info_logger(f'Route: {request.path}').info(json.dumps(log_data))
        # Convert string date to datetime object.
        date_obj = datetime.strptime(date, "%d-%m-%Y")
        # From the date object, convert the date to YYYY-MM-DD format.
        formatted_date = date_obj.strftime("%Y-%m-%d %H:%M:%S")
        next_date = (date_obj + timedelta(1)).strftime("%Y-%m-%d 00:00:00")
        branch_codes = home_form.branch_codes.data
        state_codes = home_form.state_codes.data
        city_codes = home_form.city_codes.data
        delivery_user_id = home_form.delivery_user_id.data
        report = home_form.report.data
        user_id = request.headers.get('user-id')
        home_data = {}
        branches = []
        state = []
        delivery_user_attendance = []
        adhoc_pickup_revenue = 0
        try:
            state_codes = ','.join(filter(None, city_codes)) if city_codes else ''
            city_codes = ','.join(filter(None, state_codes)) if state_codes else ''
            if not branch_codes:
                # Getting the branches associated with the user.
                query = f"""EXEC JFSL.DBO.SPFabStoreBranchInfo @store_user_id='{user_id}'"""
                store_user_branches = CallSP(query).execute().fetchall()
                for branch in store_user_branches:
                    branches.append(branch.get('BranchCode'))

                store_user_branches = ','.join(branches)
            else:
                # Branch codes are given.
                store_user_branches = ','.join(branch_codes)
                delivery_user_attendance = {}

            query = f""" EXEC JFSL.DBO.SPFabConsoleDashboard @Actiontype = 'AdhocPickups',@userid = {user_id},@date = '{formatted_date}'
                    ,@state_codes  = '{state_codes}',@city_codes  = '{city_codes}',@branch_codes = '{store_user_branches}'"""
            log_data = {
             'query': query
            }
            info_logger(f'Route: {request.path}').info(json.dumps(log_data))
            adhoc_pickups = CallSP(query).execute().fetchall()
          

            query = f""" EXEC JFSL.DBO.SPFabConsoleDashboard @Actiontype = 'Pickup',@userid = {user_id},@date = '{formatted_date}' 
                    ,@state_codes  = '{state_codes}',@city_codes  = '{city_codes}',@branch_codes = '{store_user_branches}'"""
            log_data = {
             'query': query
            }
            info_logger(f'Route: {request.path}').info(json.dumps(log_data))

            Pickup = CallSP(query).execute().fetchall()
            
            pickup_stat = {item['Category']: item['Count'] or 0 for item in Pickup}

            query = f""" EXEC JFSL.DBO.SPFabConsoleDashboard @Actiontype = 'Delivery',@userid = {user_id},@date = '{formatted_date}' 
                        ,@state_codes  = '{state_codes}',@city_codes  = '{city_codes}',@branch_codes = '{store_user_branches}'"""
            log_data = {
             'query': query
            }
            info_logger(f'Route: {request.path}').info(json.dumps(log_data))
            Delivery = CallSP(query).execute().fetchall()
           
            Delivery_stat = {item['Category']: item['Count'] or 0 for item in Delivery}

            query = f""" EXEC JFSL.DBO.SPFabConsoleDashboard @Actiontype = 'Activitylog',@userid = {user_id},@date = '{formatted_date}' 
                                                        ,@state_codes  = '{state_codes}',@city_codes  = '{city_codes}',@branch_codes = '{store_user_branches}'"""

            log_data = {
             'query': query
            }
            info_logger(f'Route: {request.path}').info(json.dumps(log_data))
            ActivityLogs = CallSP(query).execute().fetchall()
           
            log_desc = []

            # Current date to calculate time difference
            current_date = datetime.now()
            if delivery_user_id is not None:
                # Delivery user id is given.
                delivery_users = [delivery_user_id]
                # Getting the delivery user attendance.
                delivery_user_attendance = db.session.query(DeliveryUserAttendance.Date,
                                                            DeliveryUserAttendance.ClockInTime,
                                                            DeliveryUserAttendance.ClockOutTime,
                                                            DeliveryUserAttendance.ClockInLat,
                                                            DeliveryUserAttendance.ClockInLong,
                                                            DeliveryUserAttendance.ClockOutLat,
                                                            DeliveryUserAttendance.ClockOutLong).filter(
                    DeliveryUserAttendance.Date == formatted_date,
                    DeliveryUserAttendance.DUserId == delivery_user_id).one_or_none()
                delivery_user_attendance = SerializeSQLAResult(delivery_user_attendance).serialize_one()


              


                # today = datetime.today().strftime("%Y-%m-%d 00:00:00")
                # tomorrow = (datetime.today() + timedelta(days=1)).strftime("%Y-%m-%d 00:00:00")
            log_data = {
            'home_form': "home_form"
            }
            info_logger(f'Route: {request.path}').info(json.dumps(log_data))
            try:
                for log in ActivityLogs:

                    travel_logs = db.session.execute(
                            text(
                        "SELECT * FROM JFSL.dbo.FABTravelLogs "
                        "WHERE DUserId = :delivery_user_id "
                        "AND RecordCreatedDate BETWEEN :today AND :tomorrow"
                            ),
                    {"delivery_user_id": delivery_user_id, "today": formatted_date, "tomorrow": next_date}
                    ).fetchall()
                    travelled_distance = TravelDistanceCalculator().loop(travel_logs).distance()
                    delivery_user_attendance['TravelledDistance'] = travelled_distance
                    log_data = {
                    'home_form': "home_form"
                    }
                    info_logger(f'Route: {request.path}').info(json.dumps(log_data))
                for log in ActivityLogs:
                    result = {"desc": "", "time": ""}

                    # Parse RecordCreatedDate to calculate time difference
                    record_date = datetime.strptime(log["RecordCreatedDate"], "%d-%m-%Y")
                    time_diff_minutes = (current_date - record_date).total_seconds() / 60

                    # Determine the time format
                    if time_diff_minutes > 1440:
                        # More than a day
                        time_diff = time_diff_minutes / 1440
                        measure = "days"
                    elif time_diff_minutes > 60:
                        # More than an hour
                        time_diff = time_diff_minutes / 60
                        measure = "hours"
                    else:
                        # Less than an hour
                        time_diff = time_diff_minutes
                        measure = "minutes"

                    # Generate description based on Activity Type
                    if log["Activity"] == "Pickup":
                        desc = f"Order #{log['OrderId']} picked up by User ID {log['DUserId']}."
                    elif log["Activity"] == "Delivery":
                        desc = f"Order #{log['OrderId']} delivered by User ID {log['DUserId']}."
                    elif log["Activity"] == "PickupRequest":
                        desc = f"A new pickup request (#OrderId {log['OrderId']}) for User ID {log['DUserId']}."
                    else:
                        desc = "Unknown activity."

                    # Format time description
                    time_desc = f"{round(time_diff)} {measure} ago."

                    # Prepare final result
                    result["desc"] = desc
                    result["time"] = time_desc

                    log_desc.append(result)
            except Exception as e:
                error_logger(f'Route: {request.path}').error(e)

            home_data = {

                'Pickups': {
                    'Completed': {
                        'Count': pickup_stat.get('Completed', 0),
                        'HelpText': 'These are the number of pickups completed on the given date.'
                    },
                    'Pending': {
                        'Count': pickup_stat.get('Pending', 0) + pickup_stat.get('DelayedPending', 0),
                        'HelpText': 'These are the number of pickups that are pending for the given date (Including delayed).'
                    },
                    'Unassigned': {
                        'Count': pickup_stat.get('Unassigned', 0),
                        'HelpText': 'These are the number of unassigned pickups to date.'
                    },
                    'Cancelled': {
                        'Count': pickup_stat.get('Cancelled', 0),
                        'HelpText': 'These are the number of pickups cancelled on the given date.'
                    },
                    'Delayed': {
                        'Count': pickup_stat.get('Late', 0) + pickup_stat.get('DelayedPending', 0),
                        'HelpText': 'These are the number of pickups completed as delayed & pickups pending as delayed on the given date.'
                    },
                    'OnTime': {
                        'Count': pickup_stat.get('OnTime', 0),
                        'HelpText': 'These are the number of pickups made on time on the given date.'
                    },
                    'Late': {
                        'Count': pickup_stat.get('Late', 0),
                        'HelpText': 'These are the number of pickups completed as delayed on the given date.'
                    },
                    'Total': {
                        'Count': pickup_stat.get('Cancelled', 0) + pickup_stat.get('Completed', 0) +
                                 (pickup_stat.get('Pending', 0) + pickup_stat.get('DelayedPending', 0)),
                        'HelpText': 'The total sum of completed + cancelled + pending based on the given date.'
                    }
                },
                'Delivery': {
                    'Completed': {
                        'Count': Delivery_stat.get('Completed', 0),
                        'HelpText': 'These are the number of deliveries completed on the given date.'
                    },
                    'Pending': {
                        'Count': Delivery_stat.get('Pending', 0),
                        'HelpText': 'These are the number of deliveries that are pending for the given date (Including delayed).'
                    },
                    'Unassigned': {
                        'Count': Delivery_stat.get('Unassigned', 0),
                        'HelpText': 'These are the number of unassigned deliveries to date.'
                    },
                    'Delayed': {
                        'Count': Delivery_stat.get('Delayed', 0),
                        'HelpText': 'These are the number of deliveries completed as delayed & deliveries pending as delayed on the given date.'
                    },
                    'OnTime': {
                        'Count': Delivery_stat.get('OnTime', 0),
                        'HelpText': 'These are the number of deliveries made on time on the given date.'
                    },
                    'Late': {
                        'Count': Delivery_stat.get('Late', 0),
                        'HelpText': 'These are the number of deliveries made late on the given date.'
                    },
                    'Total': {
                        'Count': Delivery_stat.get('Completed', 0) + Delivery_stat.get('Pending', 0) + Delivery_stat.get('Delayed', 0),
                        'HelpText': 'The total sum of pending + completed '
                                    'based on the given date.'
                    }
                },
                'AdhocPickupsCount':adhoc_pickups[0].get('AdhocPickupsCount'),
                'AdhocPickupsRevenue': adhoc_pickups[0].get('AdhocPickupsRevenue'),
                'AmountCollection': {
                    'CashCollection': float(adhoc_pickups[0].get('CashCollection')),
                    'CardCollection': float(adhoc_pickups[0].get('CardCollection')),
                    'OnlinePayment': float(adhoc_pickups[0].get('OnlinePayment')),
                },
                'ActivityLogs': log_desc,
                'DeliveryUserAttendance': delivery_user_attendance
            }

        except Exception as e:
            error_logger(f'Route: {request.path}').error(e)
        if home_data:
            # Edited by MMM
            final_data = generate_final_data('DATA_FOUND')
            if report:
                # Report flag is included in the request. So generate the file and send the file back.
                report_data = [
                    {
                        'PickupsCompleted': home_data['Pickups']['Completed']['Count'],
                        'PickupsUnassigned': home_data['Pickups']['Unassigned']['Count'],
                        'PickupsPending': home_data['Pickups']['Pending']['Count'],
                        'PickupsCancelled': home_data['Pickups']['Cancelled']['Count'],
                        'PickupsTotal': home_data['Pickups']['Total']['Count'],
                        'DeliveriesCompleted': home_data['Delivery']['Completed']['Count'],
                        'DeliveriesUnassigned': home_data['Delivery']['Unassigned']['Count'],
                        'DeliveriesPending': home_data['Delivery']['Pending']['Count'],
                        'DeliveriesTotal': home_data['Delivery']['Total']['Count'],
                        'AdhocPickupsCount': home_data['AdhocPickupsCount'],
                        'AdhocPickupsRevenue': home_data['AdhocPickupsRevenue'],
                        'CashCollection': home_data['AmountCollection']['CashCollection'],
                        'CardCollection': home_data['AmountCollection']['CardCollection'],
                        'OnlinePayment': home_data['AmountCollection']['OnlinePayment']
                    }
                ]
                report_link = GenerateReport(report_data, 'dashboard').generate().get()
                if report_link is not None:
                    final_data['result'] = report_link
                else:
                    # Failed to generate the file.
                    final_data = generate_final_data('FILE_NOT_FOUND')
            else:
                final_data['result'] = home_data
            # Edited by MMM
        else:
            final_data = generate_final_data('DATA_NOT_FOUND')
    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(home_form.errors)

    log_data = {
             'final_data': final_data
            }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))
    return final_data


@store_console_blueprint.route('/get_pending_activities', methods=["POST"])
@authenticate('store_user')
def get_pending_activities():
    """
    API for getting the pending activities in a branch.
    @return:
    """
    pending_activities_form = GetPendingActivitiesForm()
    if pending_activities_form.validate_on_submit():
        unassigned_only = pending_activities_form.unassigned_only.data
        branch_codes = pending_activities_form.branch_codes.data
        late_only = pending_activities_form.late_only.data
        report = pending_activities_form.report.data
        pending_activities = []
        user_id = request.headers.get('user-id')
        try:
            if not branch_codes:
                # Getting the branches associated with the user.
                # Edited by MMM
                store_user_branches = store_controller_queries.get_store_user_branches(user_id)
                store_user_all_branches = store_controller_queries.get_store_user_branches(user_id, None, None, True)
            else:
                store_user_branches = branch_codes
                store_user_all_branches = branch_codes

            # If the pickup is rescheduled, then select RescheduledDate, else select PickupDate.
            select_activity_date = case([(PickupReschedule.RescheduledDate == None, PickupRequest.PickupDate), ],
                                        else_=PickupReschedule.RescheduledDate).label("ActivityDate")

            # Getting the pending pickups for that branch code.
            pending_pickups = store_controller_queries.get_pending_pickups(select_activity_date, unassigned_only,
                                                                           late_only,
                                                                           store_user_branches)

            # If the delivery is rescheduled, then select RescheduledDate, else select DeliveryDate.
            select_activity_date = case([(DeliveryReschedule.RescheduledDate == None, DeliveryRequest.DeliveryDate), ],
                                        else_=DeliveryReschedule.RescheduledDate).label("ActivityDate")

            # Getting the pending deliveries for that branch code.
            pending_deliveries = store_controller_queries.get_pending_deliveries(select_activity_date, unassigned_only,
                                                                                 late_only,
                                                                                 store_user_all_branches)

            # Populating the final activity list by combining both pending_pickups and
            # pending_deliveries by union.
            pending_activities = pending_pickups.union(pending_deliveries).order_by(select_activity_date.asc()
                                                                                    ).all()

        except Exception as e:
            error_logger(f'Route: {request.path}').error(e)

        if pending_activities is not None:
            # Serializing the activity list.
            pending_activities = SerializeSQLAResult(pending_activities).serialize()
            if len(pending_activities) > 0:
                # Now for each activity, retrieve service tats and service types belongs
                # to that pickup request Id

                for activity in pending_activities:

                    # If the ActivityDate is less than current date, mention this order as LATE
                    activity_date = activity['ActivityDate']
                    # Convert string date to datetime object.
                    activity_date_obj = datetime.strptime(activity_date, "%d-%m-%Y")
                    # From the date object, convert the date to YYYY-MM-DD format.
                    formatted_activity_date = activity_date_obj.strftime("%Y-%m-%d %H:%M:%S")

                    try:
                        # Getting only the deliveries to add the CustomerPreferredDate, CustomerPreferredTimeSlot
                        if activity['ActivityType'] == 'Delivery':
                            # If CustomerPreferredTimeSlot in DeliveryReschedule then select it, Else select from
                            # DeliveryRequest
                            select_time_slot = case([(DeliveryReschedule.CustomerPreferredTimeSlot == None,
                                                      DeliveryRequest.CustomerPreferredTimeSlot), ],
                                                    else_=DeliveryReschedule.CustomerPreferredTimeSlot).label(
                                "TimeSlot")
                            # If DeliveryRequestId in DeliveryReschedule is none then select DeliveryRequestId from
                            # DeliveryRequest
                            select_delivery_id = case([(DeliveryReschedule.DeliveryRequestId == None,
                                                        DeliveryRequest.DeliveryRequestId), ],
                                                      else_=DeliveryReschedule.DeliveryRequestId).label(
                                "TimeSlot")
                            # Getting delivery details from DB
                            cus_prefer_date = db.session.query(DeliveryRequest.DeliveryRequestId,
                                                               DeliveryRequest.CustomerPreferredDate,
                                                               CustomerTimeSlot.TimeSlot,
                                                               select_time_slot,
                                                               CustomerTimeSlot.TimeSlotFrom,
                                                               CustomerTimeSlot.TimeSlotTo).outerjoin(
                                DeliveryReschedule,
                                DeliveryRequest.DeliveryRequestId == DeliveryReschedule.DeliveryRequestId).outerjoin(
                                CustomerTimeSlot,
                                DeliveryReschedule.CustomerPreferredTimeSlot == CustomerTimeSlot.TimeSlotId or DeliveryRequest.CustomerPreferredTimeSlot == CustomerTimeSlot.TimeSlotId).filter(
                                select_delivery_id == activity['ActivityId'],
                                # select_time_slot == CustomerTimeSlot.TimeSlotId,
                                DeliveryRequest.IsDeleted == 0, or_(DeliveryReschedule.IsDeleted == 0,
                                                                    DeliveryReschedule.IsDeleted == None)).one_or_none()
                            if cus_prefer_date is not None:
                                activity['IsPreferredDateAfter'] = False
                                activity['CustomerPreferredDate'] = None

                                if cus_prefer_date.CustomerPreferredDate is not None:
                                    # Insert CustomerPreferredDate to the result of delivery requests
                                    activity['CustomerPreferredDate'] = cus_prefer_date.CustomerPreferredDate.strftime(
                                        "%d-%m-%Y")

                                    # Format CustomerPreferredDate
                                    formatted_cus_prefer_date = cus_prefer_date.CustomerPreferredDate.strftime(
                                        "%Y-%m-%d %H:%M:%S")
                                    # Pass IsPreferredDateAfter as true if CustomerPreferredDate is greater then today
                                    if formatted_cus_prefer_date > get_today():
                                        activity['IsPreferredDateAfter'] = True

                                if cus_prefer_date.TimeSlot is not None:
                                    time_slots = SerializeSQLAResult(cus_prefer_date).serialize_one()
                                    # Update TimeSlotFrom and TimeSlotTo in looped activity with entry in
                                    # CustomerTimeSlot table
                                    cus_prefer_timeslot = db.session.query(CustomerTimeSlot.TimeSlotFrom,
                                                                           CustomerTimeSlot.TimeSlotTo).filter(
                                        CustomerTimeSlot.TimeSlotId == time_slots['TimeSlot']
                                    ).one_or_none()
                                    cus_prefer_timeslot = SerializeSQLAResult(cus_prefer_timeslot).serialize_one()
                                    activity.update({'TimeSlotFrom': cus_prefer_timeslot['TimeSlotFrom'],
                                                     'TimeSlotTo': cus_prefer_timeslot['TimeSlotTo']})
                            else:
                                # Update TimeSlotFrom and TimeSlotTo in looped activity as NUll
                                activity.update({'TimeSlotFrom': 'NULL', 'TimeSlotTo': 'NULL'})

                    except Exception as e:
                        pass

                    try:
                        duser = False
                        if activity['AssignType'] == "Manual":
                            if activity['ActivityType'] == "Delivery":
                                activity_id = activity['ActivityId']
                                try:
                                    store_user = db.session.query(DeliveryReschedule.AssignedStoreUser,
                                                                  DeliveryReschedule.RescheduledStoreUser,
                                                                  DeliveryReschedule.DUserId).filter(
                                        DeliveryReschedule.DeliveryRequestId == activity_id,
                                        DeliveryReschedule.IsDeleted == 0).one_or_none()

                                    if store_user is not None:
                                        if store_user.RescheduledStoreUser is None and store_user.AssignedStoreUser is None:
                                            select_store_user = DeliveryUser.UserName.label("AssignedStoreUser")
                                            store_user = db.session.query(select_store_user).filter(
                                                DeliveryUser.DUserId == store_user.DUserId).one_or_none()
                                            duser = True
                                    else:

                                        store_user = db.session.query(DeliveryRequest.AssignedStoreUser).filter(
                                            DeliveryRequest.DeliveryRequestId == activity_id,
                                            DeliveryRequest.IsDeleted == 0).one_or_none()
                                    if duser:
                                        activity[
                                            'AssignedStoreUser'] = store_user.AssignedStoreUser + " - Delivery User"

                                        select_assigned_date = DeliveryReschedule.RecordLastUpdatedDate.label(
                                            "AssignedDate")
                                        assigned_user_data = db.session.query(select_assigned_date, DeliveryReschedule
                                                                              ).filter(
                                            DeliveryReschedule.DeliveryRequestId == activity_id,
                                            DeliveryReschedule.IsDeleted == 0).all()
                                    else:
                                        select_store_user = StoreUser.UserName.label("AssignedStoreUser")
                                        if store_user.AssignedStoreUser is None:
                                            store_user_name = db.session.query(select_store_user).filter(
                                                StoreUser.SUserId == store_user.RescheduledStoreUser).one_or_none()
                                            select_assigned_date = DeliveryReschedule.RecordLastUpdatedDate.label(
                                                "AssignedDate")
                                            assigned_user_data = db.session.query(select_assigned_date,
                                                                                  DeliveryReschedule
                                                                                  ).filter(
                                                DeliveryReschedule.DeliveryRequestId == activity_id,
                                                DeliveryReschedule.IsDeleted == 0).all()
                                            activity['AssignedStoreUser'] = store_user_name.AssignedStoreUser
                                        else:
                                            store_user_name = db.session.query(select_store_user).filter(
                                                StoreUser.SUserId == store_user.AssignedStoreUser).one_or_none()
                                            select_assigned_date = DeliveryRequest.RecordLastUpdatedDate.label(
                                                "AssignedDate")
                                            assigned_user_data = db.session.query(select_assigned_date, DeliveryRequest
                                                                                  ).filter(
                                                DeliveryRequest.DeliveryRequestId == activity_id,
                                                DeliveryRequest.IsDeleted == 0).all()
                                            activity['AssignedStoreUser'] = store_user_name.AssignedStoreUser
                                except Exception as e:
                                    error_logger(f'Route: {request.path}').error(e)

                                try:
                                    assigned_user_data = SerializeSQLAResult(assigned_user_data).serialize(
                                        full_date_fields=['AssignedDate'])
                                    if assigned_user_data is not None:
                                        for assigned_data in assigned_user_data:
                                            activity['AssignedDate'] = assigned_data['AssignedDate']
                                except Exception as e:
                                    error_logger(f'Route: {request.path}').error(e)
                            if activity['ActivityType'] == 'Pickup':
                                activity_id = activity['ActivityId']
                                store_user = db.session.query(PickupReschedule.AssignedStoreUser,
                                                              PickupReschedule.RescheduledStoreUser,
                                                              PickupReschedule.RescheduledDeliveryUser).filter(
                                    PickupReschedule.PickupRequestId == activity_id,
                                    PickupReschedule.IsDeleted == 0).one_or_none()
                                if store_user is not None:

                                    if store_user.RescheduledStoreUser is None and store_user.AssignedStoreUser is None:
                                        select_store_user = DeliveryUser.UserName.label("AssignedStoreUser")
                                        store_user = db.session.query(select_store_user).filter(
                                            DeliveryUser.DUserId == store_user.RescheduledDeliveryUser).one_or_none()
                                        duser = True
                                else:
                                    store_user = db.session.query(PickupRequest.AssignedStoreUser).filter(
                                        PickupRequest.PickupRequestId == activity_id).one_or_none()
                                if duser:
                                    activity['AssignedStoreUser'] = store_user.AssignedStoreUser + " - Delivery User"
                                    select_assigned_date = PickupReschedule.RecordLastUpdatedDate.label(
                                        "AssignedDate")
                                    assigned_user_data = db.session.query(select_assigned_date, PickupReschedule
                                                                          ).filter(
                                        PickupReschedule.PickupRequestId == activity_id,
                                        PickupReschedule.IsDeleted == 0).all()
                                else:
                                    select_store_user = StoreUser.UserName.label("AssignedStoreUser")
                                    if store_user.AssignedStoreUser is None:
                                        store_user_name = db.session.query(select_store_user).filter(
                                            StoreUser.SUserId == store_user.RescheduledStoreUser).one_or_none()
                                        select_assigned_date = PickupReschedule.RecordLastUpdatedDate.label(
                                            "AssignedDate")
                                        assigned_user_data = db.session.query(select_assigned_date, PickupReschedule
                                                                              ).filter(
                                            PickupReschedule.PickupRequestId == activity_id,
                                            PickupReschedule.IsDeleted == 0).all()
                                        activity['AssignedStoreUser'] = store_user_name.AssignedStoreUser
                                    else:
                                        store_user_name = db.session.query(select_store_user).filter(
                                            StoreUser.SUserId == store_user.AssignedStoreUser).one_or_none()
                                        select_assigned_date = PickupRequest.RecordLastUpdatedDate.label("AssignedDate")
                                        assigned_user_data = db.session.query(select_assigned_date, PickupReschedule
                                                                              ).filter(
                                            PickupRequest.PickupRequestId == activity_id).all()
                                        activity['AssignedStoreUser'] = store_user_name.AssignedStoreUser

                                try:

                                    assigned_user_data = SerializeSQLAResult(assigned_user_data).serialize(
                                        full_date_fields=['AssignedDate'])
                                    if assigned_user_data is not None:
                                        for assigned_data in assigned_user_data:
                                            activity['AssignedDate'] = assigned_data['AssignedDate']

                                except Exception as e:
                                    error_logger(f'Route: {request.path}').error(e)
                        else:
                            if activity['ActivityType'] == "Delivery":
                                activity_id = activity['ActivityId']
                                select_assigned_date = DeliveryRequest.RecordCreatedDate.label(
                                    "AssignedDate")
                                assigned_user_data = db.session.query(select_assigned_date, DeliveryRequest
                                                                      ).filter(
                                    DeliveryRequest.DeliveryRequestId == activity_id,
                                    DeliveryRequest.IsDeleted == 0).all()
                                assigned_user_data = SerializeSQLAResult(assigned_user_data).serialize(
                                    full_date_fields=['AssignedDate'])
                                if assigned_user_data is not None:
                                    for assigned_data in assigned_user_data:
                                        activity['AssignedDate'] = assigned_data['AssignedDate']
                            if activity['ActivityType'] == "Pickup":
                                activity_id = activity['ActivityId']
                                select_assigned_date = PickupRequest.RecordCreatedDate.label(
                                    "AssignedDate")
                                assigned_user_data = db.session.query(select_assigned_date, PickupRequest
                                                                      ).filter(
                                    PickupRequest.PickupRequestId == activity_id,
                                ).all()
                                assigned_user_data = SerializeSQLAResult(assigned_user_data).serialize(
                                    full_date_fields=['AssignedDate'])
                                if assigned_user_data is not None:
                                    for assigned_data in assigned_user_data:
                                        activity['AssignedDate'] = assigned_data['AssignedDate']
                    except Exception as e:
                        error_logger(f'Route: {request.path}').error(e)

                    # If the activity is late than today, add a late flag.
                    if formatted_activity_date < get_today():
                        activity['IsLate'] = 1
                    else:
                        activity['IsLate'] = 0

        if pending_activities:
            final_data = generate_final_data('DATA_FOUND')
            if report:
                # Report flag is included in the request. So generate the file and send the file back.
                report_link = GenerateReport(pending_activities, 'pending').generate().get()
                if report_link is not None:
                    final_data['result'] = report_link
                else:
                    # Failed to generate the file.
                    final_data = generate_final_data('FILE_NOT_FOUND')
            else:
                final_data['result'] = pending_activities
        else:
            final_data = generate_final_data('DATA_NOT_FOUND')
    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(pending_activities_form.errors)

    return final_data


@store_console_blueprint.route('/get_completed_activities', methods=["POST"])
@authenticate('store_user')
def get_completed_activities():
    """
    API for getting the pending activities in a branch.
    @return:
    """
    completed_activities_form = GetCompletedActivitiesForm()
    if completed_activities_form.validate_on_submit():
        day_interval = completed_activities_form.day_interval.data
        branch_codes = completed_activities_form.branch_codes.data
        report = completed_activities_form.report.data
        interval_start_date = None
        user_id = request.headers.get('user-id')
        if day_interval is not None:
            interval_start_date = (datetime.today() - timedelta(day_interval)).strftime("%Y-%m-%d %H:%M:%S")
        completed_activities = []
        try:

            if not branch_codes:
                # Getting the branches associated with the user.
                # Edited by MMM
                store_user_branches = store_controller_queries.get_store_user_branches(user_id, None, None, True)
            else:
                # Branch code(s) are given.
                store_user_branches = branch_codes

            record_created_date = PickupRequest.RecordCreatedDate

            # Getting the completed pickups.
            completed_pickups = store_controller_queries.get_completed_pickups(record_created_date,
                                                                               interval_start_date,
                                                                               store_user_branches)

            record_created_date = Delivery.RecordCreatedDate

            # Getting the completed deliveries.
            completed_deliveries = store_controller_queries.get_completed_deliveries(record_created_date,
                                                                                     interval_start_date,
                                                                                     store_user_branches)

            # Populating the completed activities by combining both completed pickups and completed deliveries.
            completed_activities = completed_pickups.union(completed_deliveries).order_by(
                record_created_date.desc()).all()

        except Exception as e:
            error_logger(f'Route: {request.path}').error(e)

        completed_activities = SerializeSQLAResult(completed_activities).serialize()
        for completed_activity in completed_activities:

            if completed_activity['ActivityType'] == "Pickup":

                # Select Remarks if not NULL, else select NA.
                select_remarks = case([(OrderReview.Remarks == None, "NA"), ],
                                      else_=OrderReview.Remarks).label("Remarks")

                # Retrieving the OrderReviews & star ratings while created during the pickup.
                order_reviews = db.session.query(OrderReview.StarRating, OrderReviewReason.ReviewReason,
                                                 select_remarks).outerjoin(OrderReviewReason,
                                                                           OrderReview.OrderReviewReasonId == OrderReviewReason.OrderReviewReasonId).filter(
                    OrderReview.OrderId == completed_activity['OrderId']).one_or_none()

                if order_reviews is not None:
                    completed_activity['Review'] = SerializeSQLAResult(order_reviews).serialize_one()
                else:
                    completed_activity['Review'] = {}

            elif completed_activity['ActivityType'] == "Delivery":

                # Select Remarks if not NULL, else select NA.
                select_remarks = case([(DeliveryReview.Remarks == None, "NA"), ],
                                      else_=DeliveryReview.Remarks).label("Remarks")

                # Retrieving the DeliveryReviews & star ratings while created during the delivery.
                delivery_reviews = db.session.query(DeliveryReview.StarRating, DeliveryReviewReason.ReviewReason,
                                                    select_remarks).outerjoin(DeliveryReviewReason,
                                                                              DeliveryReview.DeliveryReviewReasonId == DeliveryReviewReason.DeliveryReviewReasonId).filter(
                    DeliveryReview.OrderId == completed_activity['OrderId']).one_or_none()

                if delivery_reviews is not None:
                    completed_activity['Review'] = SerializeSQLAResult(delivery_reviews).serialize_one()
                else:
                    completed_activity['Review'] = {}

        if completed_activities:
            final_data = generate_final_data('DATA_FOUND')
            if report:
                # Report flag is included in the request. So generate the file and send the file back.
                report_link = GenerateReport(completed_activities, 'completed').generate().get()
                if report_link is not None:
                    final_data['result'] = report_link
                else:
                    # Failed to generate the file.
                    final_data = generate_final_data('FILE_NOT_FOUND')
            else:
                final_data['result'] = completed_activities
        else:
            final_data = generate_final_data('DATA_NOT_FOUND')
    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(completed_activities_form.errors)

    return final_data


@store_console_blueprint.route('/get_address', methods=["POST"])
@authenticate('store_user')
def get_address():
    """
    API for getting the customer's addresses.
    @return:
    """
    address_form = GetAddressForm()
    if address_form.validate_on_submit():
        customer_id = address_form.customer_id.data
        address = []
        try:
            # Select AddressLine2 if not NULL, else select NA.
            select_address_line_2 = case([(CustomerAddres.AddressLine2 == None, "NA"), ],
                                         else_=CustomerAddres.AddressLine2).label("AddressLine2")

            # Select AddressLine3 if not NULL, else select NA.
            select_address_line_3 = case([(CustomerAddres.AddressLine3 == None, "NA"), ],
                                         else_=CustomerAddres.AddressLine3).label("AddressLine3")

            # Select Landmark if not NULL, else select NA.
            select_landmark = case([(CustomerAddres.Landmark == None, "NA"), ],
                                   else_=CustomerAddres.Landmark).label("Landmark")

            # Selecting the customer address from the DB.
            address = db.session.query(CustomerAddres.CustAddressId, CustomerAddres.AddressLine1, select_address_line_2,
                                       select_address_line_3, select_landmark, CustomerAddres.Pincode).filter(
                CustomerAddres.CustomerId == customer_id, CustomerAddres.IsDeleted == 0).all()
        except Exception as e:
            error_logger(f'Route: {request.path}').error(e)

        if address:
            final_data = generate_final_data('DATA_FOUND')
            final_data['result'] = SerializeSQLAResult(address).serialize()
        else:
            final_data = generate_final_data('DATA_NOT_FOUND')
    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(address_form.errors)

    return final_data


# @store_console_blueprint.route('/get_time_slots', methods=["POST"])
# @authenticate('store_user')
# def get_time_slots():
#     """
#     API for getting the available pickup time slots for a branch code.
#     @return:
#     """
#     time_slots_form = GetTimeSlotsForm()
#     if time_slots_form.validate_on_submit():
#         branch_codes = time_slots_form.branch_codes.data
#         time_slots = []
#         user_id = request.headers.get('user-id')
#         try:

#             if not branch_codes:
#                 # Getting the branches associated with the user.
#                 store_user_branches = store_controller_queries.get_store_user_branches(user_id)
#             else:
#                 # Branch codes are given.
#                 store_user_branches = branch_codes

#             # Getting the time slots from the DB.
#             time_slots = db.session.query(PickupTimeSlot.PickupTimeSlotId, PickupTimeSlot.TimeSlotFrom,
#                                           PickupTimeSlot.TimeSlotTo).filter(
#                 PickupTimeSlot.BranchCode.in_(store_user_branches),
#                 PickupTimeSlot.IsDeleted == 0,
#                 or_(PickupTimeSlot.VisibilityFlag == 1,
#                     PickupTimeSlot.DefaultFlag == 0)).order_by(PickupTimeSlot.TimeSlotFrom).all()
#         except Exception as e:
#             error_logger(f'Route: {request.path}').error(e)

#         if time_slots:
#             final_data = generate_final_data('DATA_FOUND')
#             final_data['result'] = SerializeSQLAResult(time_slots).serialize()
#         else:
#             final_data = generate_final_data('DATA_NOT_FOUND')

#     else:
#         # Form validation error.
#         final_data = generate_final_data('FORM_ERROR')
#         final_data['errors'] = populate_errors(time_slots_form.errors)

#     return final_data

@store_console_blueprint.route('/get_time_slots', methods=["POST"])
@authenticate('store_user')
def get_time_slots():
    """
    API for getting the available pickup time slots for a branch code.
    @return:
    """
    time_slots_form = GetTimeSlotsForm()
    if time_slots_form.validate_on_submit():
        branch_codes = time_slots_form.branch_codes.data
        time_slots = []
        user_id = request.headers.get('user-id')
        try:

            if not branch_codes:
                # Getting the branches associated with the user.
                store_user_branches = store_controller_queries.get_store_user_branches(user_id)
            else:
                # Branch codes are given.
                store_user_branches = branch_codes

            # Getting the time slots from the DB.
            time_slots = f""" EXEC JFSL.dbo.SPTimeSlotFabriccareCustApp @Branch_code =''"""
            time_slots = CallSP(time_slots).execute().fetchall()
        except Exception as e:
            error_logger(f'Route: {request.path}').error(e)

        if time_slots:
            final_data = generate_final_data('DATA_FOUND')
            final_data['result'] = time_slots
        else:
            final_data = generate_final_data('DATA_NOT_FOUND')

    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(time_slots_form.errors)

    return final_data


# @store_console_blueprint.route('/get_time_slots', methods=["POST"])
# @authenticate('store_user')
# def get_time_slots():
#     """
#     API for getting the available pickup time slots for a branch code.
#     @return:
#     """
#     time_slots_form = GetTimeSlotsForm()
#     if time_slots_form.validate_on_submit():
#         branch_codes = time_slots_form.branch_codes.data
#         time_slots = []
#         user_id = request.headers.get('user-id')
#         try:

#             if not branch_codes:
#                 # Getting the branches associated with the user.
#                 store_user_branches = store_controller_queries.get_store_user_branches(user_id)
#             else:
#                 # Branch codes are given.
#                 store_user_branches = branch_codes

#             # Getting the time slots from the DB.
#             time_slots = db.session.query(FabPickupTimeSlots.PickupTimeSlotId,
#                                           FabPickupTimeSlots.TimeSlotFrom,
#                                           FabPickupTimeSlots.TimeSlotTo).filter(
#                 FabPickupTimeSlots.IsActive == 1, FabPickupTimeSlots.IsDeleted == 0, 
#                 FabPickupTimeSlots.PickupTimeSlotId != 5, FabPickupTimeSlots.PickupTimeSlotId != 6).all()
#             # time_slots = db.session.query(PickupTimeSlot.PickupTimeSlotId, PickupTimeSlot.TimeSlotFrom,
#             #                               PickupTimeSlot.TimeSlotTo).filter(
#             #     PickupTimeSlot.BranchCode.in_(store_user_branches),
#             #     PickupTimeSlot.IsDeleted == 0,
#             #     or_(PickupTimeSlot.VisibilityFlag == 1,
#             #         PickupTimeSlot.DefaultFlag == 1)).all()
#         except Exception as e:
#             error_logger(f'Route: {request.path}').error(e)

#         if time_slots:
#             final_data = generate_final_data('DATA_FOUND')
#             final_data['result'] = SerializeSQLAResult(time_slots).serialize()
#         else:
#             final_data = generate_final_data('DATA_NOT_FOUND')

#     else:
#         # Form validation error.
#         final_data = generate_final_data('FORM_ERROR')
#         final_data['errors'] = populate_errors(time_slots_form.errors)

#     return final_data

@store_console_blueprint.route('/get_reschedule_reasons', methods=["GET"])
@authenticate('store_user')
def get_reschedule_reasons():
    """
    API for getting the pickup reschedule reasons.
    @return:
    """
    reschedule_reasons = []
    try:
        # Getting the reschedule reasons from the DB.
        reschedule_reasons = db.session.query(PickupRescheduleReason.RescheduleReason,
                                              PickupRescheduleReason.RescheduleReasonId).filter(
            PickupRescheduleReason.IsDeleted == 0).all()
    except Exception as e:
        error_logger(f'Route: {request.path}').error(e)

    if reschedule_reasons:
        final_data = generate_final_data('DATA_FOUND')
        final_data['result'] = SerializeSQLAResult(reschedule_reasons).serialize()
    else:
        final_data = generate_final_data('DATA_NOT_FOUND')

    return final_data


@store_console_blueprint.route('/get_cancel_reasons', methods=["GET"])
@authenticate('store_user')
def get_cancel_reasons():
    """
    API for getting the pickup cancel reasons.
    @return:
    """
    cancel_reasons = []
    try:
        # Getting the cancel reasons from the DB.
        cancel_reasons = db.session.query(PickupCancelReason.CancelReason,
                                          PickupCancelReason.CancelReasonId).filter(
            PickupCancelReason.IsDeleted == 0).all()
    except Exception as e:
        error_logger(f'Route: {request.path}').error(e)

    if cancel_reasons:
        final_data = generate_final_data('DATA_FOUND')
        final_data['result'] = SerializeSQLAResult(cancel_reasons).serialize()
    else:
        final_data = generate_final_data('DATA_NOT_FOUND')

    return final_data


# Edited by MM
@store_console_blueprint.route('/delivery_users_report', methods=["POST"])
@authenticate('store_user')
def delivery_users_report():
    """
    Api for getting report based on inactive users and filter by branch
    """
    delivery_users_form = GetDeliveryUsersForm()
    if delivery_users_form.validate_on_submit():
        branch_codes = delivery_users_form.branch_codes.data
        report = delivery_users_form.report.data
        all_usr = delivery_users_form.inactve.data
        branch = None if delivery_users_form.branch.data == '' else delivery_users_form.branch.data
        delivery_users = []
        user_id = request.headers.get('user-id')
        try:
            # Getting the delivery user details from the DB.

            # Based on the store user, delivery users will be returned. If the store user is the admin,
            # All delivery users will be returned. Else, only related branch's delivery users will be returned.
            store_user = db.session.query(StoreUser).filter(StoreUser.SUserId == user_id).one_or_none()

            if store_user is not None:
                store_user_branches = store_controller_queries.get_store_user_branches(user_id)

                # To get all delivery users.
                if all_usr is True:
                    delivery_users = delivery_controller_queries.get_delivery_branch_of_all(store_user_branches,
                                                                                            branch_name=None,
                                                                                            all_users=True)

                # To get all delivery users on the basis of branch
                if branch is not None and all_usr is True:
                    delivery_users = delivery_controller_queries.get_delivery_branch_of_all(store_user_branches, branch,
                                                                                            all_users=True)

                # To get active delivery users on the basis of  branch number
                if branch is not None and all_usr is False:
                    delivery_users = delivery_controller_queries.get_delivery_branch_of_all(store_user_branches, branch,
                                                                                            all_users=False)

            delivery_users = SerializeSQLAResult(delivery_users).serialize()

            # Getting the branch codes of delivery users.
            for delivery_user in delivery_users:
                delivery_user['BranchCodes'] = delivery_controller_queries.get_delivery_user_branches(
                    delivery_user['DUserId'])
                delivery_user['BranchNames'] = delivery_controller_queries.get_delivery_user_branchname(
                    delivery_user['DUserId'])
        except Exception as e:
            error_logger(f'Route: {request.path}').error(e)

        if delivery_users:
            final_data = generate_final_data('DATA_FOUND')
            if report:
                # Report flag is included in the request. So generate the file and send the file back.
                report_link = GenerateReport(delivery_users, 'delivery_users').generate().get()
                if report_link is not None:
                    final_data['result'] = report_link
                else:
                    # Failed to generate the file.
                    final_data = generate_final_data('FILE_NOT_FOUND')
            else:
                final_data['result'] = delivery_users
        else:
            final_data = generate_final_data('DATA_NOT_FOUND')
    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(delivery_users_form.errors)
    return final_data


@store_console_blueprint.route('/get_delivery_users', methods=["POST"])
# @authenticate('store_user')
def get_delivery_users():
    """
    API for getting the delivery users based on BranchCode.
    @return:
    """
    delivery_users_form = GetDeliveryUsersForm()
    if delivery_users_form.validate_on_submit():
        branch_codes = delivery_users_form.branch_codes.data
        report = delivery_users_form.report.data
        # Edited by MMM
        active = False if delivery_users_form.active.data == '' else delivery_users_form.active.data
        # Edited by MMM
        city_code = None if delivery_users_form.city_code.data == '' else delivery_users_form.city_code.data
        delivery_users = []
        branch_codes_list = []
        user_id = request.headers.get('user-id')
        try:
            # Getting the delivery user details from the DB.

            # Based on the store user, delivery users will be returned. If the store user is the admin,
            # All delivery users will be returned. Else, only related branch's delivery users will be returned.
            store_user = db.session.query(StoreUser).filter(StoreUser.SUserId == user_id).one_or_none()

            if store_user is not None:
                # Store user found.
                if not branch_codes:
                    # Getting the branches associated with the user.
                    store_user_branches = store_controller_queries.get_store_user_branches(user_id)
                else:
                    # Branch codes are given.
                    store_user_branches = branch_codes

                # Getting the branch codes based on city code if provided.
                if city_code is not None:
                    # Getting all the branch codes that under the given city.
                    branch_codes = db.session.query(Branch.BranchCode).join(Area,
                                                                            Branch.AreaCode == Area.AreaCode).join(City,
                                                                                                                   City.CityCode == Area.CityCode).filter(
                        City.CityCode == city_code, Branch.IsDeleted == 0).all()

                    branch_codes_list = [branch_code.BranchCode for branch_code in branch_codes]

                    # Populating a list of branch codes that are under this store user and in the given city.
                    branch_codes_in_the_city = [branch_code for branch_code in branch_codes_list if
                                                branch_code in store_user_branches]

                    # If the city code is given, choose only the branch code that are in the given city.
                    # Even if the store user has other delivery users outside the city.
                    store_user_branches = branch_codes_in_the_city

                # Store user can only get the delivery users
                # belongs to his/her branch.
             
                store_user_created_by = aliased(StoreUser)
                store_user_modified_by = aliased(StoreUser)
                base_query = db.session.query(DeliveryUser.DUserId, DeliveryUser.UserName, DeliveryUser.MobileNo,
                                              DeliveryUser.EmailId, DeliveryUser.IsActive,
                                              DeliveryUser.PartialPaymentPermission,
                                              DeliveryUser.CancellPickupPermission,
                                              DeliveryUser.ReschedulePickupPermission,
                                              DeliveryUser.DeliveryChargePermission,
                                              DeliveryUser.DeliveryWithoutOTPPermission,
                                              DeliveryUser.DeliverWithoutPaymentPermission,
                                              func.coalesce(DeliveryUser.ModifiedBy, DeliveryUser.AddedBy),
                                              store_user_modified_by.UserName.label('ModifiedBy'),
                                              store_user_created_by.UserName.label('CreatedBy'),
                                              DeliveryUser.RecordLastUpdatedDate.label('ModifiedDate'),
                                              DeliveryUser.RecordCreatedDate.label('CreatedDate')).join(
                    store_user_modified_by,
                    store_user_modified_by.SUserId == DeliveryUser.ModifiedBy, isouter=True
                ).join(
                    store_user_created_by,
                    store_user_created_by.SUserId == DeliveryUser.AddedBy, isouter=True
                ).distinct(
                    DeliveryUser.UserName,
                    DeliveryUser.MobileNo,
                    DeliveryUser.EmailId,
                    DeliveryUser.IsActive,
                    DeliveryUser.PartialPaymentPermission,
                    DeliveryUser.CancellPickupPermission,
                    DeliveryUser.ReschedulePickupPermission,
                    DeliveryUser.DeliveryChargePermission,
                    DeliveryUser.DeliveryWithoutOTPPermission,
                    DeliveryUser.DeliverWithoutPaymentPermission
                )
                # base_query = base_query.join(DeliveryUserBranch,
                #                              DeliveryUserBranch.DUserId == DeliveryUser.DUserId).filter(
                #     DeliveryUserBranch.BranchCode.in_(store_user_branches))
                # Edited By Athira
                # show all delivery user to ADMIN
           
                if store_user.UserName == 'ADMIN':
                    if not branch_codes:
                        base_query = base_query.join(DeliveryUserBranch,
                                                     DeliveryUserBranch.DUserId == DeliveryUser.DUserId)
                    else:
                        base_query = base_query.join(DeliveryUserBranch,
                                                     DeliveryUserBranch.DUserId == DeliveryUser.DUserId).filter(
                            DeliveryUserBranch.BranchCode.in_(store_user_branches), DeliveryUserBranch.IsDeleted == 0)
                else:
                    base_query = base_query.join(DeliveryUserBranch,
                                                     DeliveryUserBranch.DUserId == DeliveryUser.DUserId).filter(
                            DeliveryUserBranch.BranchCode.in_(store_user_branches), DeliveryUserBranch.IsDeleted == 0)

                # Edited by MMM
                # To sort out active users
                if active:
                    delivery_users = base_query.filter(DeliveryUser.IsActive == 1)
                else:
                    delivery_users = base_query.all()
                # Edited by MMM

            delivery_users = SerializeSQLAResult(delivery_users).serialize(
                full_date_fields=['ModifiedDate', 'CreatedDate'])

            # Select branch name if display name is none
            select_branch_name = case(
                [(or_(Branch.DisplayName == None, Branch.DisplayName == ''), Branch.BranchName), ],
                else_=Branch.DisplayName).label("BranchName")

            # Select case for converting the value to false if the result is none
            select_is_default_branch = case([(DeliveryUserBranch.IsDefaultBranch == None, False), ],
                                            else_=DeliveryUserBranch.IsDefaultBranch).label("IsDefaultBranch")
            log_data = {
                'before for loop': "before for loop"
                    }
            info_logger(f'Route: {request.path}').info(json.dumps(log_data))

            for delivery_user in delivery_users:
                # Getting DeliveryUserBranch details
                branch_base_query = db.session.query(DeliveryUserBranch.BranchCode,
                                                     case([(Branch.IsActive == 0, 'Inact - ' + select_branch_name)],
                                                          else_=select_branch_name).label('BranchName'),
                                                     select_is_default_branch).join(Branch,
                                                                                    DeliveryUserBranch.BranchCode == Branch.BranchCode).filter(
                    DeliveryUserBranch.DUserId == delivery_user['DUserId'], DeliveryUserBranch.IsDeleted == 0,
                )

                # Getting all branch codes except default branch of the corresponding delivery user
                optional_branches = branch_base_query.filter().all()
                # Getting all default branch codes of the corresponding delivery user
                default_branches = branch_base_query.filter(DeliveryUserBranch.IsDefaultBranch == 1).all()

                tomorrow = (datetime.today() + timedelta(1)).strftime("%Y-%m-%d 00:00:00")
                # Getting selected_branches from DeliveryUserDailyBranch table within the date
                selected_branches = db.session.query(select_branch_name).distinct(
                    DeliveryUserDailyBranch.BranchCode).join(DeliveryUserDailyBranch,
                                                             DeliveryUserDailyBranch.BranchCode == Branch.BranchCode).filter(
                    DeliveryUserDailyBranch.DUserId == delivery_user['DUserId'], DeliveryUserDailyBranch.IsActive == 1,
                    DeliveryUserDailyBranch.IsDeleted == 0,
                    DeliveryUserDailyBranch.RecordCreatedDate.between(get_today(), tomorrow)).all()

                device_details = db.session.query(DeliveryUserEDCDetail.MerchantId,
                                                  DeliveryUserEDCDetail.DeviceSerialNumber,
                                                  DeliveryUserEDCDetail.Tid, DeliveryUserEDCDetail.MerchantKey).filter(
                    DeliveryUserEDCDetail.DUserId == delivery_user['DUserId'],
                    DeliveryUserEDCDetail.IsDeleted == 0).one_or_none()

                serialized_device_details = SerializeSQLAResult(
                    device_details).serialize_one() if device_details else None

                delivery_user['BranchCodes'] = SerializeSQLAResult(optional_branches).serialize()

                delivery_user['OptionalBranches'] = [branch.BranchName for branch in optional_branches if
                                                     branch.IsDefaultBranch == False]

                delivery_user['DefaultBranches'] = [branch.BranchName for branch in default_branches]

                delivery_user['SelectedBranches'] = [branch.BranchName for branch in selected_branches]

                delivery_user['DeviceDetails'] = serialized_device_details
                
                date = datetime.today().date()
                clockedin = db.session.query(DeliveryUserAttendance.DUserId).filter(
                    DeliveryUserAttendance.Date == date,DeliveryUserAttendance.IsDeleted == 0,
                    DeliveryUserAttendance.DUserId == delivery_user['DUserId']
                ).one_or_none()
                delivery_user['ClockedIn'] = 1 if clockedin is not None else 0

               
        except Exception as e:
            error_logger(f'Route: {request.path}').error(e)

        if delivery_users:
            final_data = generate_final_data('DATA_FOUND')
            if report:
                # Report flag is included in the request. So generate the file and send the file back.
                report_link = GenerateReport(delivery_users, 'delivery_users').generate().get()
                if report_link is not None:
                    final_data['result'] = report_link
                else:
                    # Failed to generate the file.
                    final_data = generate_final_data('FILE_NOT_FOUND')
            else:
                final_data['result'] = delivery_users
        else:
            final_data = generate_final_data('DATA_NOT_FOUND')
    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(delivery_users_form.errors)

    return final_data


# @store_console_blueprint.route('/get_delivery_users', methods=["POST"])
# # @authenticate('store_user')
# def get_delivery_users():

# @store_console_blueprint.route('/get_branches', methods=["POST"])
# @authenticate('store_user')
# def get_branches():
#     """
#     API for getting the store branches.
#     @return:
#     """
#     inactive_branch_form = GetBranchesForm()
#     if inactive_branch_form.validate_on_submit():
#         inactive_branches = inactive_branch_form.inactive_branches.data
        

#         branches = []
#         user_id = request.headers.get('user-id')
#         try:
#             store_user = db.session.query(StoreUser).filter(StoreUser.SUserId == user_id).one_or_none()
#             # Branch codes of corresponding store users
#             store_user_branch_codes = store_controller_queries.get_store_user_branches(user_id)
#             # If a DisplayName found for a branch, then select DisplayName as the BranchName.
#             select_branch_name = case(
#                 [(or_(Branch.DisplayName == None, Branch.DisplayName == ''), Branch.BranchName), ],
#                 else_=Branch.DisplayName).label("BranchName")
#             base_query = db.session.query(Branch.BranchCode,
#                                           case([(Branch.IsActive == 0, 'Inact - ' + select_branch_name)],
#                                                else_=select_branch_name).label('BranchName'), Branch.BranchAddress,
#                                           Branch.IsActive).filter(
#                 Branch.IsDeleted == 0)
#             # if inactive_branches:
#             #     branch_list = base_query
#             # else:
#             #     branch_list = base_query.filter(Branch.IsActive == 1)
#             if store_user is not None:
#                 if store_user.IsAdmin == 1:
#                     # Getting the current active branch details from the DB.
#                     branches = base_query.all()
#                 else:
#                     # Getting the current active branch details from the DB.
#                     branches = base_query.filter(Branch.BranchCode.in_(store_user_branch_codes)).all()
#         except Exception as e:
#             error_logger(f'Route: {request.path}').error(e)

#         if branches:
#             final_data = generate_final_data('DATA_FOUND')
#             final_data['result'] = SerializeSQLAResult(branches).serialize()
#         else:
#             final_data = generate_final_data('DATA_NOT_FOUND')
  

#     return final_data

@store_console_blueprint.route('/get_branches', methods=["POST"])
# @authenticate('store_user')
def get_branches_():
    """
    API for getting the store branches.
    @return:
    """
    inactive_branch_form = GetBranchesForm()
    if inactive_branch_form.validate_on_submit():
        inactive_branches = inactive_branch_form.inactive_branches.data

        branches = []
        user_id = request.headers.get('user-id')
        try:
            query = f""" EXEC JFSL.DBO.SPFabStoreBranchInfo @store_user_id = {user_id}"""
            branches = CallSP(query).execute().fetchall()
        except Exception as e:
            error_logger(f'Route: {request.path}').error(e)

        if branches:
            final_data = generate_final_data('DATA_FOUND')
            final_data['result'] = branches
        else:
            final_data = generate_final_data('DATA_NOT_FOUND')

    return final_data

# @store_console_blueprint.route('/get_all_branches', methods=["GET"])
# @authenticate('store_user')
# def get_all_branches():
#     """
#     API for getting all the store branches.
#     @return:
#     """
#     branches = []
#     try:
#         # If a DisplayName found for a branch, then select DisplayName as the BranchName.
#         select_branch_name = case(
#             [(or_(Branch.DisplayName == None, Branch.DisplayName == ''), Branch.BranchName), ],
#             else_=Branch.DisplayName).label("BranchName")

#         # Getting the all active branches.
#         branches = db.session.query(Branch.BranchCode, select_branch_name, Branch.BranchAddress).filter(
#             Branch.IsActive == 1).all()

#     except Exception as e:
#         error_logger(f'Route: {request.path}').error(e)

#     if branches:
#         final_data = generate_final_data('DATA_FOUND')
#         final_data['result'] = SerializeSQLAResult(branches).serialize()
#     else:
#         final_data = generate_final_data('DATA_NOT_FOUND')

#     return final_data

@store_console_blueprint.route('/get_all_branches', methods=["GET"])
# @authenticate('store_user')
def get_all_branches_():
    """
    API for getting all the store branches.
    @return:
    """

    try:
        query = f""" EXEC JFSL.DBO.SPFabStoreBranchInfo @store_user_id = {1}"""
        branches = CallSP(query).execute().fetchall()
    except Exception as e:
        error_logger(f'Route: {request.path}').error(e)

    if branches:
        final_data = generate_final_data('DATA_FOUND')
        final_data['result'] = branches
    else:
        final_data = generate_final_data('DATA_NOT_FOUND')

    return final_data

@store_console_blueprint.route('/assign_pickup', methods=["POST"])
# @authenticate('store_user')
def assign_pickup():
    """
    API for assigning the delivery user to a pickup request.
    @return:
    """
    assign_pickup_form = AssignPickupForm()
    user_id = request.headers.get('user-id')
    if assign_pickup_form.validate_on_submit():
        BookingIds = assign_pickup_form.BookingId.data
        delivery_user_id = assign_pickup_form.delivery_user_id.data
        MobileNos = assign_pickup_form.MobileNo.data
        CustomerNames= assign_pickup_form.CustomerName.data
        PickupDate = get_current_date()
        assigned = False
        error_msg = ''
        notify = False
        sms_triggered = False
        try:
            # Iterate through all TRNNo values and perform assignment
            print(BookingIds)
            for i in range(len(BookingIds)):

                BookingId = BookingIds[i]
                MobileNo = MobileNos[i]
                CustomerName = CustomerNames[i]
                query = f""" EXEC JFSL.Dbo.SPFabAssignPickupDeliveryUpdate @BookingId = {BookingId}, @store_user_id = {user_id},  @delivery_user_id = {delivery_user_id}"""
                log_data = {
                "query": query
                    }
                info_logger(f'Route: {request.path}').info(json.dumps(log_data))
                db.engine.execute(text(query).execution_options(autocommit=True))
                assigned = True
                notify = True
                if  PickupDate == get_today():
                    store_controller_queries.trigger_out_for_activity_sms('OUT_FOR_PICKUP',
                                                                          MobileNo,
                                                                          BookingId,
                                                                          CustomerName,
                                                                          )

        except Exception as e:
            error_logger(f'Route: {request.path}').error(e)
        if assigned:
            final_data = generate_final_data('DATA_UPDATED')
            if notify:
                # Invoke push notification
                send_push_notification_test(delivery_user_id, 'PICKUP', None, "JFSLSTORE", user_id)
        else:
            if error_msg:
                final_data = generate_final_data('CUSTOM_FAILED', error_msg)
            else:
                final_data = generate_final_data('DATA_UPDATE_FAILED')
    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(assign_pickup_form.errors)

    return final_data


@store_console_blueprint.route('/assign_delivery', methods=["POST"])
# @authenticate('store_user')
def assign_delivery():
    """
    API for assigning the delivery user to a delivery request.
    @return: JSON response with status.
    """
    assign_delivery_form = AssignDeliveryForm()
    user_id = request.headers.get('user-id')

    if assign_delivery_form.validate_on_submit():
        log_data = {
                "assign_delivery_form": assign_delivery_form.data
                    }
        info_logger(f'Route: {request.path}').info(json.dumps(log_data))
        # Extract data from the form
        delivery_user_id = assign_delivery_form.delivery_user_id.data
        TRNNo_list = assign_delivery_form.TRNNo.data
        # DeliveryDate_list = assign_delivery_form.DeliveryDate.data
        TRNNo_list = [trnno for trnno in TRNNo_list if trnno is not None]
        MobileNo_list = assign_delivery_form.MobileNo.data
        CustomerName_list = assign_delivery_form.CustomerName.data
        EGRN_list = assign_delivery_form.EGRN.data
        delivery_date = get_current_date()

        assigned = False
        notify = False
        sms_triggered = False

        
        try:
            # Validate if all lists have the same length
            if not (len(TRNNo_list)  == len(MobileNo_list) == len(CustomerName_list) == len(
                    EGRN_list)):
                raise ValueError("Please Try Again")

            # Iterate through all TRNNo values and perform assignment
            for i in range(len(TRNNo_list)):
                trnno = TRNNo_list[i]
                # delivery_date = DeliveryDate_list[i]
                mobile_no = MobileNo_list[i]
                customer_name = CustomerName_list[i]
                egrn = EGRN_list[i]

              
                query = f""" EXEC JFSL.Dbo.SPFabAssignPickupDeliveryUpdate @TRNNo = {trnno}, @store_user_id = {user_id},  @delivery_user_id = {delivery_user_id}"""
                log_data = {
                "query": query
                    }
                info_logger(f'Route: {request.path}').info(json.dumps(log_data))
                db.engine.execute(text(query).execution_options(autocommit=True))
               

                if isinstance(delivery_date, str):
                    delivery_date = datetime.strptime(delivery_date, "%Y-%m-%d %H:%M:%S")

                # Check if DeliveryDate is today or earlier for notification
                if delivery_date <= datetime.now():
                    notify = True
                BookingId = None
                CustomerName = customer_name
                # Trigger SMS if the delivery date is today and time is past 9 AM
                if delivery_date.date() == datetime.now().date():
                    current_time = datetime.now().time()
                    alert_time = datetime.strptime('09:00:00', '%H:%M:%S').time()
                    
                    # if current_time >= alert_time:
                    #     store_controller_queries.trigger_out_for_activity_sms(
                    #         'OUT_FOR_DELIVERY',
                    #         mobile_no,
                    #         BookingId,
                    #         CustomerName,
                    #     egrn)
                    #     sms_triggered = True

            assigned = True

        except ValueError as ve:
            error_msg = f"Validation error: {str(ve)}"
            print(error_msg)

        except Exception as e:
            error_logger(f'Route: {request.path}').error(str(e))
            error_msg = f"Error while assigning delivery: {str(e)}"

        # Generate final response
        if assigned:
            final_data = generate_final_data('DATA_UPDATED')

            # Send push notification if required
            if notify:
                send_push_notification_test(delivery_user_id, 'DELIVERY', None, "JFSLSTORE", user_id)

            # Log SMS status
            if sms_triggered:
                print("SMS triggered successfully for today's deliveries.")
        else:
            if error_msg:
                final_data = generate_final_data('CUSTOM_FAILED', error_msg)
            else:
                final_data = generate_final_data('DATA_UPDATE_FAILED')

    else:
        # Handle form validation errors
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(assign_delivery_form.errors)

    return final_data

# @store_console_blueprint.route('/assign_delivery', methods=["POST"])
# @authenticate('store_user')
# def assign_delivery():
#     """
#     API for assigning the delivery user to a delivery request.
#     @return:
#     """
#     assign_delivery_form = AssignDeliveryForm()
#     user_id = request.headers.get('user-id')
#     if assign_delivery_form.validate_on_submit():
#         delivery_user_id = assign_delivery_form.delivery_user_id.data
#         TRNNo = assign_delivery_form.TRNNo.data
#         DeliveryDate = assign_delivery_form.DeliveryDate.data
        
#         MobileNo = assign_delivery_form.MobileNo.data
#         CustomerName = assign_delivery_form.CustomerName.data
#         EGRN = assign_delivery_form.EGRN.data
#         assigned = False
#         error_msg = ''
#         notify = False
#         egrn = EGRN
#         BookingId = None
#         try:
#             # Getting the delivery user details.
#             if DeliveryDate:
#                 DeliveryDate = datetime.strptime(DeliveryDate, "%d-%m-%Y")
#             else:
#                 DeliveryDate = get_today()
#             # Getting the pickup request details from the DB.
#             for trnno in TRNNo:
#                 query = f""" EXEC JFSL_UAT.Dbo.SPFabAssignPickupDeliveryUpdate  @TRNNo = '{trnno}', @store_user_id = {user_id},  @delivery_user_id = {delivery_user_id}"""
#                 db.engine.execute(text(query).execution_options(autocommit=True))
#                 log_data = {
#                     'query': query
#                     }
#                 info_logger(f'Route: {request.path}').info(json.dumps(log_data))
#                 assigned = True

#                 # Invoke push notification if the delivery is scheduled for today or lesser
#                 if DeliveryDate.strftime("%Y-%m-%d %H:%M:%S") <= get_today():
#                     notify = True

#                 if  DeliveryDate == get_today():
#                     # Check if the delivery date is today.
#                     # If the delivery date is today, and current time is past 9'o clock,
#                     # needs to trigger the alert engine SP to send the SMS for delivery.

#                     store_controller_queries.trigger_out_for_activity_sms('OUT_FOR_DELIVERY',
#                                                                           MobileNo,
#                                                                           BookingId ,
#                                                                           CustomerName,
#                                                                           egrn
#                                                                           )

#         except Exception as e:
#             error_logger(f'Route: {request.path}').error(e)

#         if assigned:
#             final_data = generate_final_data('DATA_UPDATED')
#             if notify:
#                 # Invoke push notification
#                 send_push_notification_test(delivery_user_id, 'DELIVERY', None, "JFSLSTORE", user_id)
#         else:
#             if error_msg:
#                 final_data = generate_final_data('CUSTOM_FAILED', error_msg)
#             else:
#                 final_data = generate_final_data('DATA_UPDATE_FAILED')
#     else:
#         # Form validation error.
#         final_data = generate_final_data('FORM_ERROR')
#         final_data['errors'] = populate_errors(assign_delivery_form.errors)

#     return final_data

# @store_console_blueprint.route('/assign_delivery', methods=["POST"])
# @authenticate('store_user')
# def assign_delivery():
#     """
#     API for assigning the delivery user to a delivery request.
#     @return: JSON response with status.
#     """
#     assign_delivery_form = AssignDeliveryForm()
#     user_id = request.headers.get('user-id')

#     if assign_delivery_form.validate_on_submit():
#         # Extract data from the form
#         delivery_user_id = assign_delivery_form.delivery_user_id.data
#         TRNNo_list = assign_delivery_form.TRNNo.data
#         DeliveryDate_list = assign_delivery_form.DeliveryDate.data
#         MobileNo_list = assign_delivery_form.MobileNo.data
#         CustomerName_list = assign_delivery_form.CustomerName.data
#         EGRN_list = assign_delivery_form.EGRN.data

#         assigned = False
#         error_msg = ''
#         notify = False
#         sms_triggered = False

#         try:
#             # Validate if all lists have the same length
#             # if not (len(TRNNo_list) == len(DeliveryDate_list) == len(MobileNo_list) == len(CustomerName_list) == len(
#             #         EGRN_list)):
#             #     raise ValueError("Mismatch in the length of input lists")

#             # Iterate through all TRNNo values and perform assignment
#             for i in range(len(TRNNo_list)):
#                 trnno = TRNNo_list[i]
#                 delivery_date = DeliveryDate_list
#                 mobile_no = MobileNo_list[i]
#                 customer_name = CustomerName_list[i]

#                 # Call the stored procedure for each TRNNo
#                 query = text("""EXEC JFSL_UAT.Dbo.SPFabAssignPickupDeliveryUpdate  
#                                 @TRNNo = :trnno, 
#                                 @store_user_id = :user_id,  
#                                 @delivery_user_id = :delivery_user_id""")

#                 db.engine.execute(query.execution_options(autocommit=True),
#                                   trnno=trnno,
#                                   user_id=user_id,
#                                   delivery_user_id=delivery_user_id)

#                 # Convert DeliveryDate to datetime if it's a string
#                 if isinstance(delivery_date, str):
#                     delivery_date = datetime.strptime(delivery_date, "%Y-%m-%d %H:%M:%S")

#                 # Check if DeliveryDate is today or earlier for notification
#                 if delivery_date <= datetime.now():
#                     notify = True
#                 BookingId=None
#                 CustomerName=customer_name
#                 # Trigger SMS if the delivery date is today and time is past 9 AM
#                 if delivery_date.date() == datetime.now().date():
#                     current_time = datetime.now().time()
#                     alert_time = datetime.strptime('09:00:00', '%H:%M:%S').time()

#                     if current_time >= alert_time:
#                         store_controller_queries.trigger_out_for_activity_sms(
#                             'OUT_FOR_DELIVERY',
#                             mobile_no,
#                             BookingId,
#                             CustomerName
#                         )
#                         sms_triggered = True

#             assigned = True

#         except ValueError as ve:
#             error_msg = f"Validation error: {str(ve)}"
#             print(error_msg)

#         except Exception as e:
#             error_logger(f'Route: {request.path}').error(str(e))
#             error_msg = f"Error while assigning delivery: {str(e)}"

#         # Generate final response
#         if assigned:
#             final_data = generate_final_data('DATA_UPDATED')

#             # Send push notification if required
#             if notify:
#                 send_push_notification_test(delivery_user_id, 'DELIVERY', None, "JFSLSTORE", user_id)

#             # Log SMS status
#             if sms_triggered:
#                 print("SMS triggered successfully for today's deliveries.")
#         else:
#             if error_msg:
#                 final_data = generate_final_data('CUSTOM_FAILED', error_msg)
#             else:
#                 final_data = generate_final_data('DATA_UPDATE_FAILED')

#     else:
#         # Handle form validation errors
#         final_data = generate_final_data('FORM_ERROR')
#         final_data['errors'] = populate_errors(assign_delivery_form.errors)

#     return final_data

@store_console_blueprint.route('/assign_delivered_unpaid', methods=["POST"])
# @authenticate('store_user')
def assign_delivered_unpaid():
    """
    API for assigning the delivery user to a delivery request.
    @return:
    """
    assign_delivery_form = AssignDeliveryForm()
    log_data = {
        'assign_delivery_form': assign_delivery_form.data
                    }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))
    user_id = request.headers.get('user-id')
    if assign_delivery_form.validate_on_submit():
        # Extract data from the form
        delivery_user_id = assign_delivery_form.delivery_user_id.data
        TRNNo_list = assign_delivery_form.TRNNo.data
        # DeliveryDate_list = assign_delivery_form.DeliveryDate.data
        # TRNNo_list = [trnno for trnno in TRNNo_list if trnno is not None]
        MobileNo_list = assign_delivery_form.MobileNo.data
        CustomerName_list = assign_delivery_form.CustomerName.data
        EGRN_list = assign_delivery_form.EGRN.data
        delivery_date = get_current_date()

        assigned = False
        error_msg = ''
        notify = False
        sms_triggered = False

        try:
            # Validate if all lists have the same length
            if not (len(TRNNo_list) == len(MobileNo_list) == len(CustomerName_list) == len(
                    EGRN_list)):
                raise ValueError("Please Try again")

            # Iterate through all TRNNo values and perform assignment
            for i in range(len(TRNNo_list)):
                trnno = TRNNo_list[i]
                # delivery_date = DeliveryDate_list[i]
                mobile_no = MobileNo_list[i]
                customer_name = CustomerName_list[i]
                egrn = EGRN_list[i]

                query = f""" EXEC JFSL.Dbo.SPFabAssignPickupDeliveryUpdate  @TRNNo = '{trnno}', @store_user_id = {user_id},  @delivery_user_id = {delivery_user_id}"""
                db.engine.execute(text(query).execution_options(autocommit=True))
           
            assigned = True

        except Exception as e:
            error_logger(f'Route: {request.path}').error(e)

        if assigned:
            final_data = generate_final_data('DATA_UPDATED')
            if notify:
                # Invoke push notification
                send_push_notification_test(delivery_user_id, 'DELIVERY', None, "JFSLSTORE", user_id)
        else:
            if error_msg:
                final_data = generate_final_data('CUSTOM_FAILED', error_msg)
            else:
                final_data = generate_final_data('DATA_UPDATE_FAILED')
    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(assign_delivery_form.errors)

    return final_data


# @store_console_blueprint.route('/register_delivery_user', methods=["POST"])
# @authenticate('store_user')
# def register_delivery_user():
#     """
#     API for registering an delivery user.
#     @return:
#     """
#     register_delivery_user_form = RegisterDeliveryUserForm()
#     if register_delivery_user_form.validate_on_submit():
#         user_name = register_delivery_user_form.user_name.data
#         mobile_number = register_delivery_user_form.mobile_number.data
#         email = None if register_delivery_user_form.email.data == '' else register_delivery_user_form.email.data
#         password = register_delivery_user_form.password.data
#         branch_codes = register_delivery_user_form.branch_codes.data
#         partial_payment_permission = register_delivery_user_form.partial_payment_permission.data
#         device_details = register_delivery_user_form.device_details.data
#         cancel_pickup_permission = register_delivery_user_form.cancel_pickup_permission.data
#         reschedule_pickup_permission = register_delivery_user_form.reschedule_pickup_permission.data
#         # Generating the hashed password.
#         hashed_password = generate_hash(password, 50)
#         pos_user_id = None
#         pos_username = None
#         user_id = request.headers.get('user-id')
#         registered = False
#         error_msg = ''
#         try:
#             # Checking whether the delivery user is already present in the DB or not.
#             delivery_user = db.session.query(DeliveryUser).filter(DeliveryUser.MobileNo == mobile_number,
#                                                                   DeliveryUser.IsDeleted == 0).one_or_none()
#             if delivery_user is None:

#                 # If a DisplayName found for a branch, then select DisplayName as the BranchName.
#                 select_branch_name = case(
#                     [(or_(Branch.DisplayName is None, Branch.DisplayName == ''), Branch.BranchName), ],
#                     else_=Branch.DisplayName).label("BranchName")

#                 # List for populating branch name's  already opted as default branch, for making error message while trying
#                 # to assign the same
#                 branch_name_list = []
#                 # List for populating Delivery user's who already opted same default branch as default branch for
#                 # making error message while trying to assign the same
#                 d_user_list = []

#                 for branch_code in branch_codes:
#                     # Getting details to format a string to display as error message
#                     is_default_branch = db.session.query(DeliveryUserBranch.BranchCode, select_branch_name,
#                                                          DeliveryUser.UserName).join(Branch,
#                                                                                      Branch.BranchCode == DeliveryUserBranch.BranchCode).join(
#                         DeliveryUser, DeliveryUser.DUserId == DeliveryUserBranch.DUserId).filter(
#                         DeliveryUserBranch.BranchCode == branch_code['BranchCode'], DeliveryUserBranch.IsDeleted == 0,
#                         DeliveryUserBranch.IsDefaultBranch == True,
#                         DeliveryUserBranch.IsDefaultBranch == branch_code['IsDefaultBranch']).one_or_none()

#                     if is_default_branch is not None:
#                         # Appending the branch name to branch_name_list
#                         branch_name_list.append(is_default_branch.BranchName)
#                         # Appending the branch name to d_user_list
#                         d_user_list.append(is_default_branch.UserName)

#                 if len(branch_name_list) == 0:

#                     # No previous records found. Proceed to register the delivery user.
#                     new_delivery_user = DeliveryUser(
#                         UserName=user_name,
#                         MobileNo=mobile_number,
#                         Password=hashed_password,
#                         EmailId=email,
#                         AddedBy=user_id,
#                         PartialPaymentPermission=partial_payment_permission,
#                         CancellPickupPermission=cancel_pickup_permission,
#                         ReschedulePickupPermission=reschedule_pickup_permission,
#                         RegisteredDate=get_current_date(),
#                         RecordCreatedDate=get_current_date(),
#                         RecordLastUpdatedDate=get_current_date(),
#                     )

#                     # Adding new delivery user.
#                     db.session.add(new_delivery_user)
#                     db.session.commit()

#                     # Add the branches to the delivery user.
#                     for branch_code in branch_codes:
#                         # Getting the POS username of the delivery user based on branch code.
#                         query = f"EXEC {SERVER_DB}..GetDeliveryUserBranchwise @branchcode = '{branch_code['BranchCode']}'"
#                         result = CallSP(query).execute().fetchone()
#                         if result:
#                             pos_user_id = result.get('UserID')
#                             pos_username = result.get('Username')
#                         new_delivery_user_branch_code = DeliveryUserBranch(
#                             DUserId=new_delivery_user.DUserId,
#                             POSUserId=pos_user_id,
#                             POSUsername=pos_username,
#                             BranchCode=branch_code['BranchCode'],
#                             AddedBy=user_id,
#                             RecordCreatedDate=get_current_date(),
#                             RecordLastUpdatedDate=get_current_date(),
#                             IsDefaultBranch=branch_code['IsDefaultBranch']
#                         )
#                         db.session.add(new_delivery_user_branch_code)

#                     if device_details[0]:
#                         new_device_details = DeliveryUserEDCDetail(
#                             DUserId=new_delivery_user.DUserId,
#                             Tid=device_details[0]['t_id'],
#                             MerchantId=device_details[0]['m_id'],
#                             IsDeleted=0,
#                             DeviceSerialNumber=device_details[0]['s_no'],
#                             MerchantKey=device_details[0]['merchant_key']
#                         )
#                         db.session.add(new_device_details)
#                     db.session.commit()
#                     registered = True
#                 else:
#                     # Removing list brackets
#                     branches_names = ','.join(map(str, branch_name_list))
#                     d_users = ','.join(map(str, d_user_list))
#                     # Making a string of error message
#                     error_msg = f"{branches_names} branche(s) are already assigned for the  delivery user(s) {d_users}"
#             else:
#                 error_msg = 'This delivery user is already registered.'

#         except Exception as e:
#             db.session.rollback()
#             error_logger(f'Route: {request.path}').error(e)

#         if registered:
#             final_data = generate_final_data('DATA_SAVED')
#         else:
#             if error_msg:
#                 final_data = generate_final_data('CUSTOM_FAILED', error_msg)
#             else:
#                 final_data = generate_final_data('DATA_SAVE_FAILED')

#     else:
#         # Form validation error.
#         final_data = generate_final_data('FORM_ERROR')
#         final_data['errors'] = populate_errors(register_delivery_user_form.errors)

#     return final_data

@store_console_blueprint.route('/register_delivery_user', methods=["POST"])
@authenticate('store_user')
def register_delivery_user():
    """
    API for registering an delivery user.
    @return:
    """
    register_delivery_user_form = RegisterDeliveryUserForm()
    if register_delivery_user_form.validate_on_submit():
        user_name = register_delivery_user_form.user_name.data
        mobile_number = register_delivery_user_form.mobile_number.data
        email = None if register_delivery_user_form.email.data == '' else register_delivery_user_form.email.data
        # password = register_delivery_user_form.password.data
        password = None if register_delivery_user_form.password.data == '' else register_delivery_user_form.password.data

        branch_codes = register_delivery_user_form.branch_codes.data
        partial_payment_permission = register_delivery_user_form.partial_payment_permission.data
        device_details = register_delivery_user_form.device_details.data
        cancel_pickup_permission = register_delivery_user_form.cancel_pickup_permission.data
        reschedule_pickup_permission = register_delivery_user_form.reschedule_pickup_permission.data
        delivery_charge_permission = register_delivery_user_form.delivery_charge_permission.data

        Delivery_Without_OTP_permission = register_delivery_user_form.Delivery_Without_OTP_permission.data
        deliver_without_payment_Permission = register_delivery_user_form.deliver_without_payment_Permission.data

        # Generating the hashed password.
        # hashed_password = generate_hash(password, 50)
        pos_user_id = None
        pos_username = None
        user_id = request.headers.get('user-id')
        registered = False
        error_msg = ''
        mobile_number = str(mobile_number)
        try:
            # Checking whether the delivery user is already present in the DB or not.
            delivery_user = db.session.query(DeliveryUser).filter(DeliveryUser.MobileNo == mobile_number).all()
            if len(delivery_user) == 0:

                # If a DisplayName found for a branch, then select DisplayName as the BranchName.
                select_branch_name = case(
                    [(or_(Branch.DisplayName is None, Branch.DisplayName == ''), Branch.BranchName), ],
                    else_=Branch.DisplayName).label("BranchName")

                # List for populating branch name's  already opted as default branch, for making error message while trying
                # to assign the same
                branch_name_list = []
                # List for populating Delivery user's who already opted same default branch as default branch for
                # making error message while trying to assign the same
                d_user_list = []

                for branch_code in branch_codes:
                    # Getting details to format a string to display as error message
                    is_default_branch = db.session.query(DeliveryUserBranch.BranchCode, select_branch_name,
                                                         DeliveryUser.UserName).join(Branch,
                                                                                     Branch.BranchCode == DeliveryUserBranch.BranchCode).join(
                        DeliveryUser, DeliveryUser.DUserId == DeliveryUserBranch.DUserId).filter(
                        DeliveryUserBranch.BranchCode == branch_code['BranchCode'], DeliveryUserBranch.IsDeleted == 0,
                        DeliveryUserBranch.IsDefaultBranch == True,
                        DeliveryUserBranch.IsDefaultBranch == branch_code['IsDefaultBranch']).one_or_none()

                    if is_default_branch is not None:
                        # Appending the branch name to branch_name_list
                        branch_name_list.append(is_default_branch.BranchName)
                        # Appending the branch name to d_user_list
                        d_user_list.append(is_default_branch.UserName)

                if len(branch_name_list) == 0:
                    isdeliverycharge = 1 if delivery_charge_permission == True else 0
                    # No previous records found. Proceed to register the delivery user.
                    new_delivery_user = DeliveryUser(
                        UserName=user_name,
                        MobileNo=mobile_number,
                        Password=password,
                        EmailId=email,
                        AddedBy=user_id,
                        PartialPaymentPermission=partial_payment_permission,
                        CancellPickupPermission=cancel_pickup_permission,
                        ReschedulePickupPermission=reschedule_pickup_permission,
                        RegisteredDate=get_current_date(),
                        RecordCreatedDate=get_current_date(),
                        DeliveryChargePermission=isdeliverycharge,
                        DeliveryWithoutOTPPermission=Delivery_Without_OTP_permission,
                        DeliverWithoutPaymentPermission=deliver_without_payment_Permission
                        # RecordLastUpdatedDate=get_current_date(),
                    )

                    # Adding new delivery user.
                    db.session.add(new_delivery_user)
                    db.session.commit()

                    # Add the branches to the delivery user.
                    for branch_code in branch_codes:
                        # Getting the POS username of the delivery user based on branch code.
                        query = f"EXEC {SERVER_DB}..GetDeliveryUserBranchwise @branchcode = '{branch_code['BranchCode']}'"
                        result = CallSP(query).execute().fetchone()
                        if result:
                            pos_user_id = result.get('UserID')
                            pos_username = result.get('Username')
                        new_delivery_user_branch_code = DeliveryUserBranch(
                            DUserId=new_delivery_user.DUserId,
                            POSUserId=pos_user_id,
                            POSUsername=pos_username,
                            BranchCode=branch_code['BranchCode'],
                            AddedBy=user_id,
                            RecordCreatedDate=get_current_date(),
                            RecordLastUpdatedDate=get_current_date(),
                            IsDefaultBranch=branch_code['IsDefaultBranch']
                        )
                        db.session.add(new_delivery_user_branch_code)

                    if device_details[0]:
                        new_device_details = DeliveryUserEDCDetail(
                            DUserId=new_delivery_user.DUserId,
                            Tid=device_details[0]['t_id'],
                            MerchantId=device_details[0]['m_id'],
                            IsDeleted=0,
                            DeviceSerialNumber=device_details[0]['s_no'],
                            MerchantKey=device_details[0]['merchant_key']
                        )
                        db.session.add(new_device_details)
                    db.session.commit()
                    registered = True
                else:
                    # Removing list brackets
                    branches_names = ','.join(map(str, branch_name_list))
                    d_users = ','.join(map(str, d_user_list))
                    # Making a string of error message
                    error_msg = f"{branches_names} branche(s) are already assigned for the  delivery user(s) {d_users}"
            else:
                error_msg = 'This delivery user is already registered.'

        except Exception as e:
            db.session.rollback()
            error_logger(f'Route: {request.path}').error(e)

        if registered:
            final_data = generate_final_data('DATA_SAVED')
        else:
            if error_msg:
                final_data = generate_final_data('CUSTOM_FAILED', error_msg)
            else:
                final_data = generate_final_data('DATA_SAVE_FAILED')

    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(register_delivery_user_form.errors)

    return final_data


@store_console_blueprint.route('/update_delivery_user_live', methods=["PUT"])
@authenticate('store_user')
def update_delivery_user_live():
    """
    API for updating an existing delivery user.
    @return:
    """
    update_delivery_user_form = UpdateDeliveryUserForm()
    if update_delivery_user_form.validate_on_submit():
        delivery_user_id = update_delivery_user_form.delivery_user_id.data
        user_name = None if update_delivery_user_form.user_name.data == '' else update_delivery_user_form.user_name.data
        email = None if update_delivery_user_form.email.data == '' else update_delivery_user_form.email.data
        password = None if update_delivery_user_form.password.data == '' else update_delivery_user_form.password.data
        branch_codes = update_delivery_user_form.branch_codes.data
        partial_payment_permission = update_delivery_user_form.partial_payment_permission.data
        device_details = update_delivery_user_form.device_details.data
        user_has_device = True if update_delivery_user_form.user_has_device.data else False
        cancel_pickup_permission = update_delivery_user_form.cancel_pickup_permission.data
        reschedule_pickup_permission = update_delivery_user_form.reschedule_pickup_permission.data
        delivery_charge_permission = update_delivery_user_form.delivery_charge_permission.data
        Delivery_Without_OTP_permission = update_delivery_user_form.Delivery_Without_OTP_permission.data
        deliver_without_payment_Permission = update_delivery_user_form.deliver_without_payment_Permission.data
        user_id = request.headers.get('user-id')
        # Generating the hashed password.
        if password is not None:
            hashed_password = generate_hash(password, 50)
        else:
            hashed_password = None
        updated = False
        error_msg = ''
        # List for populating branch name's  already opted as default branch, for making error message while trying
        # to assign the same
        branch_name_list = []
        # List for populating Delivery user's who already opted same default branch as default branch for
        # making error message while trying to assign the same
        d_user_list = []
        try:
            # Checking whether the delivery user is already present in the DB or not.
            delivery_user = db.session.query(DeliveryUser).filter(
                DeliveryUser.DUserId == delivery_user_id).one_or_none()

            if delivery_user is not None:
                # Delivery user is present.
                # Updating the details.
                if user_name is not None:
                    delivery_user.UserName = user_name

                if password is not None:
                    delivery_user.Password = hashed_password
                if email is not None:
                    delivery_user.EmailId = email

                delivery_user.PartialPaymentPermission = partial_payment_permission
                delivery_user.CancellPickupPermission = cancel_pickup_permission
                delivery_user.ReschedulePickupPermission = reschedule_pickup_permission
                delivery_user.DeliveryChargePermission = delivery_charge_permission
                delivery_user.DeliveryWithoutOTPPermission = Delivery_Without_OTP_permission
                delivery_user.DeliverWithoutPaymentPermission = deliver_without_payment_Permission
                delivery_user.ModifiedBy = user_id
                delivery_user.RecordLastUpdatedDate = get_current_date()
                db.session.commit()

                if branch_codes:
                    # Getting the branch codes associated with the delivery user.
                    delivery_user_branch_codes = delivery_controller_queries.get_delivery_user_branches(
                        delivery_user_id)

                    # Getting the existing delivery user's branch code that are not in
                    # the given branch_codes list and delete them.
                    other_existing_user_branch_codes = db.session.query(DeliveryUserBranch).filter(
                        DeliveryUserBranch.BranchCode.notin_([branch['BranchCode'] for branch in branch_codes]),
                        DeliveryUserBranch.DUserId == delivery_user_id, DeliveryUserBranch.IsDeleted == 0).all()

                    if other_existing_user_branch_codes:
                        for existing_user_branch_code in other_existing_user_branch_codes:
                            existing_user_branch_code.IsDeleted = 1
                            existing_user_branch_code.RecordLastUpdatedDate = get_current_date()
                            db.session.commit()

                    # If a DisplayName found for a branch, then select DisplayName as the BranchName.
                    select_branch_name = case(
                        [(or_(Branch.DisplayName is None, Branch.DisplayName == ''), Branch.BranchName), ],
                        else_=Branch.DisplayName).label("BranchName")

                    # Add the branches to the delivery user.
                    for branch_code in branch_codes:
                        # getting DeliveryUserBranch details from DB
                        default_branches = db.session.query(DeliveryUserBranch.IsDefaultBranch,
                                                            select_branch_name, DeliveryUserBranch.DUserId,
                                                            DeliveryUser.UserName).join(
                            Branch, DeliveryUserBranch.BranchCode == Branch.BranchCode).join(DeliveryUser,
                                                                                             DeliveryUserBranch.DUserId == DeliveryUser.DUserId).filter(
                            DeliveryUserBranch.BranchCode == branch_code['BranchCode'],
                            DeliveryUserBranch.IsDeleted == 0, DeliveryUserBranch.IsDefaultBranch == True,
                            DeliveryUserBranch.DUserId == delivery_user_id).one_or_none()

                        # If the branch code is already IsDefaultBranch, append it to the branch_list
                        if default_branches is not None and default_branches.IsDefaultBranch is True and branch_code[
                            'IsDefaultBranch'] == True and default_branches.DUserId != delivery_user_id:
                            # Appending the branch name to branch_name_list
                            branch_name_list.append(default_branches.BranchName)
                            # Appending the branch name to d_user_list
                            d_user_list.append(default_branches.UserName)

                        if branch_code['BranchCode'] not in delivery_user_branch_codes:
                            # This branch_code is not present in the table. So insert a new record.
                            new_delivery_user_branch_code = DeliveryUserBranch(
                                DUserId=delivery_user_id,
                                BranchCode=branch_code['BranchCode'],
                                AddedBy=user_id,
                                RecordCreatedDate=get_current_date(),
                                IsDefaultBranch=branch_code['IsDefaultBranch']
                            )
                            db.session.add(new_delivery_user_branch_code)
                        else:
                            # Getting DeliveryUserBranch details
                            d_user_branch = db.session.query(DeliveryUserBranch).filter(
                                DeliveryUserBranch.DUserId == delivery_user_id, DeliveryUserBranch.IsDeleted == 0,
                                DeliveryUserBranch.BranchCode == branch_code['BranchCode']).one_or_none()

                            # Updating DeliveryUserBranch table
                            d_user_branch.IsDefaultBranch = branch_code['IsDefaultBranch']

                existing_device_details = db.session.query(DeliveryUserEDCDetail).filter(
                    DeliveryUserEDCDetail.DUserId == delivery_user_id,
                    DeliveryUserEDCDetail.IsDeleted == 0).one_or_none()

                if not user_has_device and existing_device_details:
                    existing_device_details.IsDeleted = 1

                if device_details[0]:

                    if existing_device_details:
                        existing_device_details.IsDeleted = 1

                    new_device_details = DeliveryUserEDCDetail(
                        DUserId=delivery_user_id,
                        Tid=device_details[0]['t_id'],
                        MerchantId=device_details[0]['m_id'],
                        IsDeleted=0,
                        DeviceSerialNumber=device_details[0]['s_no'],
                        MerchantKey=device_details[0]['merchant_key']
                    )
                    db.session.add(new_device_details)

                updated = True
            else:
                error_msg = 'Delivery user not found.'

        except Exception as e:
            db.session.rollback()
            error_logger(f'Route: {request.path}').error(e)
        # Checking is there any branches with IsDefaultBranch
        if len(branch_name_list) > 0:
            db.session.rollback()
            # Removing list brackets
            branches_names = ','.join(map(str, branch_name_list))
            d_users = ','.join(map(str, d_user_list))

            # Making a string of error message
            error_msg = f"{branches_names} branche(s) are already assigned for the  delivery user(s) {d_users}"
            final_data = generate_final_data('CUSTOM_FAILED', error_msg)

        elif updated:
            db.session.commit()
            final_data = generate_final_data('DATA_UPDATED')
        else:
            if error_msg:
                final_data = generate_final_data('CUSTOM_FAILED', error_msg)
            else:
                final_data = generate_final_data('DATA_UPDATE_FAILED')

    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(update_delivery_user_form.errors)

    return final_data

@store_console_blueprint.route('/update_delivery_user_uat', methods=["PUT"])
@authenticate('store_user')
def update_delivery_user_uat():
    """
    API for updating an existing delivery user.
    @return:
    """
    update_delivery_user_form = UpdateDeliveryUserForm()
    if update_delivery_user_form.validate_on_submit():
        delivery_user_id = update_delivery_user_form.delivery_user_id.data
        user_name = None if update_delivery_user_form.user_name.data == '' else update_delivery_user_form.user_name.data
        email = None if update_delivery_user_form.email.data == '' else update_delivery_user_form.email.data
        password = None if update_delivery_user_form.password.data == '' else update_delivery_user_form.password.data
        branch_codes = update_delivery_user_form.branch_codes.data
        partial_payment_permission = update_delivery_user_form.partial_payment_permission.data
        device_details = update_delivery_user_form.device_details.data
        user_has_device = True if update_delivery_user_form.user_has_device.data else False
        cancel_pickup_permission = update_delivery_user_form.cancel_pickup_permission.data
        reschedule_pickup_permission = update_delivery_user_form.reschedule_pickup_permission.data
        delivery_charge_permission = update_delivery_user_form.delivery_charge_permission.data
        Delivery_Without_OTP_permission = update_delivery_user_form.Delivery_Without_OTP_permission.data
        deliver_without_payment_Permission = update_delivery_user_form.deliver_without_payment_Permission.data
        user_id = request.headers.get('user-id')
        # Generating the hashed password.
        if password is not None:
            hashed_password = generate_hash(password, 50)
        else:
            hashed_password = None
        updated = False
        error_msg = ''
        # List for populating branch name's  already opted as default branch, for making error message while trying
        # to assign the same
        branch_name_list = []
        # List for populating Delivery user's who already opted same default branch as default branch for
        # making error message while trying to assign the same
        d_user_list = []
        try:
            # Checking whether the delivery user is already present in the DB or not.
            delivery_user = db.session.query(DeliveryUser).filter(
                DeliveryUser.DUserId == delivery_user_id).one_or_none()

            if delivery_user is not None:
                # Delivery user is present.
                # Updating the details.
                if user_name is not None:
                    delivery_user.UserName = user_name

                if password is not None:
                    delivery_user.Password = hashed_password
                if email is not None:
                    delivery_user.EmailId = email

                delivery_user.PartialPaymentPermission = partial_payment_permission
                delivery_user.CancellPickupPermission = cancel_pickup_permission
                delivery_user.ReschedulePickupPermission = reschedule_pickup_permission
                delivery_user.DeliveryChargePermission = delivery_charge_permission
                delivery_user.DeliveryWithoutOTPPermission = Delivery_Without_OTP_permission
                delivery_user.DeliverWithoutPaymentPermission = deliver_without_payment_Permission
                delivery_user.ModifiedBy = user_id
                delivery_user.RecordLastUpdatedDate = get_current_date()
                db.session.commit()

                if branch_codes:
                    # Getting the branch codes associated with the delivery user.
                    delivery_user_branch_codes = delivery_controller_queries.get_delivery_user_branches(
                        delivery_user_id)

                    # Getting the existing delivery user's branch code that are not in
                    # the given branch_codes list and delete them.
                    other_existing_user_branch_codes = db.session.query(DeliveryUserBranch).filter(
                        DeliveryUserBranch.BranchCode.notin_([branch['BranchCode'] for branch in branch_codes]),
                        DeliveryUserBranch.DUserId == delivery_user_id, DeliveryUserBranch.IsDeleted == 0).all()

                    if other_existing_user_branch_codes:
                        for existing_user_branch_code in other_existing_user_branch_codes:
                            existing_user_branch_code.IsDeleted = 1
                            existing_user_branch_code.RecordLastUpdatedDate = get_current_date()
                            db.session.commit()

                    # If a DisplayName found for a branch, then select DisplayName as the BranchName.
                    select_branch_name = case(
                        [(or_(Branch.DisplayName is None, Branch.DisplayName == ''), Branch.BranchName), ],
                        else_=Branch.DisplayName).label("BranchName")

                    # Add the branches to the delivery user.
                    for branch_code in branch_codes:
                        # getting DeliveryUserBranch details from DB
                        default_branches = db.session.query(DeliveryUserBranch.IsDefaultBranch,
                                                            select_branch_name, DeliveryUserBranch.DUserId,
                                                            DeliveryUser.UserName).join(
                            Branch, DeliveryUserBranch.BranchCode == Branch.BranchCode).join(DeliveryUser,
                                                                                             DeliveryUserBranch.DUserId == DeliveryUser.DUserId).filter(
                            DeliveryUserBranch.BranchCode == branch_code['BranchCode'],
                            DeliveryUserBranch.IsDeleted == 0, DeliveryUserBranch.IsDefaultBranch == True,
                            DeliveryUserBranch.DUserId == delivery_user_id).one_or_none()

                        # If the branch code is already IsDefaultBranch, append it to the branch_list
                        if default_branches is not None and default_branches.IsDefaultBranch is True and branch_code[
                            'IsDefaultBranch'] == True and default_branches.DUserId != delivery_user_id:
                            # Appending the branch name to branch_name_list
                            branch_name_list.append(default_branches.BranchName)
                            # Appending the branch name to d_user_list
                            d_user_list.append(default_branches.UserName)

                        if branch_code['BranchCode'] not in delivery_user_branch_codes:
                            # This branch_code is not present in the table. So insert a new record.
                            new_delivery_user_branch_code = DeliveryUserBranch(
                                DUserId=delivery_user_id,
                                BranchCode=branch_code['BranchCode'],
                                AddedBy=user_id,
                                RecordCreatedDate=get_current_date(),
                                IsDefaultBranch=branch_code['IsDefaultBranch']
                            )
                            db.session.add(new_delivery_user_branch_code)
                        else:
                            # Getting DeliveryUserBranch details
                            d_user_branch = db.session.query(DeliveryUserBranch).filter(
                                DeliveryUserBranch.DUserId == delivery_user_id, DeliveryUserBranch.IsDeleted == 0,
                                DeliveryUserBranch.BranchCode == branch_code['BranchCode']).one_or_none()

                            # Updating DeliveryUserBranch table
                            d_user_branch.IsDefaultBranch = branch_code['IsDefaultBranch']

                existing_device_details = db.session.query(DeliveryUserEDCDetail).filter(
                    DeliveryUserEDCDetail.DUserId == delivery_user_id,
                    DeliveryUserEDCDetail.IsDeleted == 0).one_or_none()

                if not user_has_device and existing_device_details:
                    existing_device_details.IsDeleted = 1

                if device_details[0]:

                    if existing_device_details:
                        existing_device_details.IsDeleted = 1

                    new_device_details = DeliveryUserEDCDetail(
                        DUserId=delivery_user_id,
                        Tid=device_details[0]['t_id'],
                        MerchantId=device_details[0]['m_id'],
                        IsDeleted=0,
                        DeviceSerialNumber=device_details[0]['s_no'],
                        MerchantKey=device_details[0]['merchant_key']
                    )
                    db.session.add(new_device_details)

                updated = True
            else:
                error_msg = 'Delivery user not found.'

        except Exception as e:
            db.session.rollback()
            error_logger(f'Route: {request.path}').error(e)
        # Checking is there any branches with IsDefaultBranch
        if len(branch_name_list) > 0:
            db.session.rollback()
            # Removing list brackets
            branches_names = ','.join(map(str, branch_name_list))
            d_users = ','.join(map(str, d_user_list))

            # Making a string of error message
            error_msg = f"{branches_names} branche(s) are already assigned for the  delivery user(s) {d_users}"
            final_data = generate_final_data('CUSTOM_FAILED', error_msg)

        elif updated:
            db.session.commit()
            final_data = generate_final_data('DATA_UPDATED')
        else:
            if error_msg:
                final_data = generate_final_data('CUSTOM_FAILED', error_msg)
            else:
                final_data = generate_final_data('DATA_UPDATE_FAILED')

    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(update_delivery_user_form.errors)

    return final_data

@store_console_blueprint.route('/update_delivery_user', methods=["PUT"])
#@authenticate('store_user')
def update_delivery_user():
    """
    API for updating an existing delivery user.
    @return:
    """
    update_delivery_user_form = UpdateDeliveryUserForm()
    if update_delivery_user_form.validate_on_submit():
        delivery_user_id = update_delivery_user_form.delivery_user_id.data
        user_name = None if update_delivery_user_form.user_name.data == '' else update_delivery_user_form.user_name.data
        email = None if update_delivery_user_form.email.data == '' else update_delivery_user_form.email.data
        password = None if update_delivery_user_form.password.data == '' else update_delivery_user_form.password.data
        branch_codes = update_delivery_user_form.branch_codes.data
        partial_payment_permission = update_delivery_user_form.partial_payment_permission.data
        device_details = update_delivery_user_form.device_details.data
        user_has_device = True if update_delivery_user_form.user_has_device.data else False
        cancel_pickup_permission = update_delivery_user_form.cancel_pickup_permission.data
        reschedule_pickup_permission = update_delivery_user_form.reschedule_pickup_permission.data
        delivery_charge_permission = update_delivery_user_form.delivery_charge_permission.data
        Delivery_Without_OTP_permission = update_delivery_user_form.Delivery_Without_OTP_permission.data
        deliver_without_payment_Permission = update_delivery_user_form.deliver_without_payment_Permission.data
        user_id = request.headers.get('user-id')
        # Generating the hashed password.
        if password is not None:
            hashed_password = generate_hash(password, 50)
        else:
            hashed_password = None
        updated = False
        error_msg = ''
        # List for populating branch name's  already opted as default branch, for making error message while trying
        # to assign the same
        branch_name_list = []
        # List for populating Delivery user's who already opted same default branch as default branch for
        # making error message while trying to assign the same
        d_user_list = []
        try:
            # Checking whether the delivery user is already present in the DB or not.
            delivery_user = db.session.query(DeliveryUser).filter(
                DeliveryUser.DUserId == delivery_user_id).one_or_none()

            if delivery_user is not None:
                # Delivery user is present.
                # Updating the details.
                if user_name is not None:
                    delivery_user.UserName = user_name

                if password is not None:
                    delivery_user.Password = hashed_password
                if email is not None:
                    delivery_user.EmailId = email

                delivery_user.PartialPaymentPermission = partial_payment_permission
                delivery_user.CancellPickupPermission = cancel_pickup_permission
                delivery_user.ReschedulePickupPermission = reschedule_pickup_permission
                delivery_user.DeliveryChargePermission = delivery_charge_permission
                delivery_user.DeliveryWithoutOTPPermission = Delivery_Without_OTP_permission
                delivery_user.DeliverWithoutPaymentPermission = deliver_without_payment_Permission
                delivery_user.ModifiedBy = user_id
                delivery_user.RecordLastUpdatedDate = get_current_date()
                db.session.commit()

                if branch_codes:
                    # Getting the branch codes associated with the delivery user.
                    delivery_user_branch_codes = delivery_controller_queries.get_delivery_user_branches(
                        delivery_user_id)

                    # Getting the existing delivery user's branch code that are not in
                    # the given branch_codes list and delete them.
                    other_existing_user_branch_codes = db.session.query(DeliveryUserBranch).filter(
                        DeliveryUserBranch.BranchCode.notin_([branch['BranchCode'] for branch in branch_codes]),
                        DeliveryUserBranch.DUserId == delivery_user_id, DeliveryUserBranch.IsDeleted == 0).all()

                    if other_existing_user_branch_codes:
                        for existing_user_branch_code in other_existing_user_branch_codes:
                            existing_user_branch_code.IsDeleted = 1
                            existing_user_branch_code.RecordLastUpdatedDate = get_current_date()
                            db.session.commit()

                    # If a DisplayName found for a branch, then select DisplayName as the BranchName.
                    select_branch_name = case(
                        [(or_(Branch.DisplayName is None, Branch.DisplayName == ''), Branch.BranchName), ],
                        else_=Branch.DisplayName).label("BranchName")

                    if branch_codes:
                        # Checking if any branch has IsDefaultBranch=True already assigned to another user
                        for branch_code in branch_codes:
                            if branch_code['IsDefaultBranch']:
                                existing_default_branch_user = db.session.query(DeliveryUserBranch).join(
                                    DeliveryUser).filter(
                                    DeliveryUserBranch.BranchCode == branch_code['BranchCode'],
                                    DeliveryUserBranch.IsDefaultBranch == True,
                                    DeliveryUserBranch.IsDeleted == 0,
                                    DeliveryUser.DUserId != delivery_user_id).one_or_none()

                                if existing_default_branch_user:
                                    db.session.rollback()
                                    # Return error if default branch is already assigned
                                    error_msg = f"Default branch access is already given to another delivery user"
                                    final_data = generate_final_data('CUSTOM_FAILED', error_msg)
                                    return final_data
                        delivery_user_branch_codes = delivery_controller_queries.get_delivery_user_branches(
                            delivery_user_id)
                        for branch_code in branch_codes:
                            # Handle branch assignments
                            if branch_code['BranchCode'] not in delivery_user_branch_codes:
                                # This branch_code is not present in the table. So insert a new record.
                                new_delivery_user_branch_code = DeliveryUserBranch(
                                    DUserId=delivery_user_id,
                                    BranchCode=branch_code['BranchCode'],
                                    AddedBy=user_id,
                                    RecordCreatedDate=get_current_date(),
                                    IsDefaultBranch=branch_code['IsDefaultBranch']
                                )
                                db.session.add(new_delivery_user_branch_code)
                            else:
                                # Getting DeliveryUserBranch details
                                d_user_branch = db.session.query(DeliveryUserBranch).filter(
                                    DeliveryUserBranch.DUserId == delivery_user_id, DeliveryUserBranch.IsDeleted == 0,
                                    DeliveryUserBranch.BranchCode == branch_code['BranchCode']).one_or_none()

                                # Updating DeliveryUserBranch table
                                d_user_branch.IsDefaultBranch = branch_code['IsDefaultBranch']

                existing_device_details = db.session.query(DeliveryUserEDCDetail).filter(
                    DeliveryUserEDCDetail.DUserId == delivery_user_id,
                    DeliveryUserEDCDetail.IsDeleted == 0).one_or_none()

                if not user_has_device and existing_device_details:
                    existing_device_details.IsDeleted = 1

                if device_details[0]:

                    if existing_device_details:
                        existing_device_details.IsDeleted = 1

                    new_device_details = DeliveryUserEDCDetail(
                        DUserId=delivery_user_id,
                        Tid=device_details[0]['t_id'],
                        MerchantId=device_details[0]['m_id'],
                        IsDeleted=0,
                        DeviceSerialNumber=device_details[0]['s_no'],
                        MerchantKey=device_details[0]['merchant_key']
                    )
                    db.session.add(new_device_details)

                updated = True
            else:
                error_msg = 'Delivery user not found.'

        except Exception as e:
            db.session.rollback()
            error_logger(f'Route: {request.path}').error(e)
        # Checking is there any branches with IsDefaultBranch
        if len(branch_name_list) > 0:
            db.session.rollback()
            # Removing list brackets
            branches_names = ','.join(map(str, branch_name_list))
            d_users = ','.join(map(str, d_user_list))

            # Making a string of error message
            error_msg = f"{branches_names} branche(s) are already assigned for the  delivery user(s) {d_users}"
            final_data = generate_final_data('CUSTOM_FAILED', error_msg)

        elif updated:
            db.session.commit()
            final_data = generate_final_data('DATA_UPDATED')
        else:
            if error_msg:
                final_data = generate_final_data('CUSTOM_FAILED', error_msg)
            else:
                final_data = generate_final_data('DATA_UPDATE_FAILED')

    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(update_delivery_user_form.errors)

    return final_data

# @store_console_blueprint.route('/update_delivery_user', methods=["PUT"])
# # @authenticate('store_user')
# def update_delivery_user():
#     """
#     API for updating an existing delivery user.
#     @return:
#     """
#     update_delivery_user_form = UpdateDeliveryUserForm()
#     if update_delivery_user_form.validate_on_submit():
#         delivery_user_id = update_delivery_user_form.delivery_user_id.data
#         user_name = None if update_delivery_user_form.user_name.data == '' else update_delivery_user_form.user_name.data
#         email = None if update_delivery_user_form.email.data == '' else update_delivery_user_form.email.data
#         password = None if update_delivery_user_form.password.data == '' else update_delivery_user_form.password.data
#         branch_codes = update_delivery_user_form.branch_codes.data
#         partial_payment_permission = update_delivery_user_form.partial_payment_permission.data
#         device_details = update_delivery_user_form.device_details.data
#         user_has_device = True if update_delivery_user_form.user_has_device.data else False
#         cancel_pickup_permission = update_delivery_user_form.cancel_pickup_permission.data
#         reschedule_pickup_permission = update_delivery_user_form.reschedule_pickup_permission.data
#         delivery_charge_permission = update_delivery_user_form.delivery_charge_permission.data
#         Delivery_Without_OTP_permission = update_delivery_user_form.Delivery_Without_OTP_permission.data
#         deliver_without_payment_Permission = update_delivery_user_form.deliver_without_payment_Permission.data
#         user_id = request.headers.get('user-id')
#         # Generating the hashed password.
#         if password is not None:
#             hashed_password = generate_hash(password, 50)
#         else:
#             hashed_password = None
#         updated = False
#         error_msg = ''
#         # List for populating branch name's  already opted as default branch, for making error message while trying
#         # to assign the same
#         branch_name_list = []
#         # List for populating Delivery user's who already opted same default branch as default branch for
#         # making error message while trying to assign the same
#         d_user_list = []
#         try:
#             # Checking whether the delivery user is already present in the DB or not.
#             delivery_user = db.session.query(DeliveryUser).filter(
#                 DeliveryUser.DUserId == delivery_user_id).one_or_none()

#             if delivery_user is not None:
#                 # Delivery user is present.
#                 # Updating the details.
#                 if user_name is not None:
#                     delivery_user.UserName = user_name

#                 if password is not None:
#                     delivery_user.Password = hashed_password
#                 if email is not None:
#                     delivery_user.EmailId = email

#                 delivery_user.PartialPaymentPermission = partial_payment_permission
#                 delivery_user.CancellPickupPermission = cancel_pickup_permission
#                 delivery_user.ReschedulePickupPermission = reschedule_pickup_permission
#                 delivery_user.DeliveryChargePermission = delivery_charge_permission
#                 delivery_user.DeliveryWithoutOTPPermission = Delivery_Without_OTP_permission
#                 delivery_user.DeliverWithoutPaymentPermission = deliver_without_payment_Permission
#                 delivery_user.ModifiedBy = user_id
#                 delivery_user.RecordLastUpdatedDate = get_current_date()
#                 db.session.commit()

#                 if branch_codes:
#                     # Getting the branch codes associated with the delivery user.
#                     delivery_user_branch_codes = delivery_controller_queries.get_delivery_user_branches(
#                         delivery_user_id)

#                     # Getting the existing delivery user's branch code that are not in
#                     # the given branch_codes list and delete them.
#                     other_existing_user_branch_codes = db.session.query(DeliveryUserBranch).filter(
#                         DeliveryUserBranch.BranchCode.notin_([branch['BranchCode'] for branch in branch_codes]),
#                         DeliveryUserBranch.DUserId == delivery_user_id, DeliveryUserBranch.IsDeleted == 0).all()

#                     if other_existing_user_branch_codes:
#                         for existing_user_branch_code in other_existing_user_branch_codes:
#                             existing_user_branch_code.IsDeleted = 1
#                             existing_user_branch_code.RecordLastUpdatedDate = get_current_date()
#                             db.session.commit()

#                     # If a DisplayName found for a branch, then select DisplayName as the BranchName.
#                     select_branch_name = case(
#                         [(or_(Branch.DisplayName is None, Branch.DisplayName == ''), Branch.BranchName), ],
#                         else_=Branch.DisplayName).label("BranchName")

#                     # Add the branches to the delivery user.
#                     for branch_code in branch_codes:
#                         if branch_code['IsDefaultBranch'] is True:
#                             print(branch_code)
#                             # Check if this BranchCode is already marked as default for any other user
#                             conflict = db.session.query(DeliveryUserBranch, DeliveryUser).join(
#                                 DeliveryUser,
#                                 DeliveryUserBranch.DUserId == DeliveryUser.DUserId
#                             ).filter(
#                                 DeliveryUserBranch.BranchCode == branch_code['BranchCode'],
#                                 DeliveryUserBranch.IsDefaultBranch == True,
#                                 DeliveryUserBranch.IsDeleted == 0,
#                                 DeliveryUserBranch.DUserId != delivery_user_id  # Exclude current user
#                             ).one_or_none()
#                             if conflict:
#                                 db.session.rollback()
#                                 error_msg = f"The branch {branch_code['BranchCode']} is already assigned as default to another delivery user."
#                                 return generate_final_data('DATA_UPDATE_FAILED', error_msg)
#                             else:
#                                 # getting DeliveryUserBranch details from DB
#                                 default_branches = db.session.query(DeliveryUserBranch.IsDefaultBranch,
#                                                                     select_branch_name, DeliveryUserBranch.DUserId,
#                                                                     DeliveryUser.UserName).join(
#                                     Branch, DeliveryUserBranch.BranchCode == Branch.BranchCode).join(DeliveryUser,
#                                                                                                      DeliveryUserBranch.DUserId == DeliveryUser.DUserId).filter(
#                                     DeliveryUserBranch.BranchCode == branch_code['BranchCode'],
#                                     DeliveryUserBranch.IsDeleted == 0, DeliveryUserBranch.IsDefaultBranch == True,
#                                     DeliveryUserBranch.DUserId == delivery_user_id).one_or_none()

#                                 # If the branch code is already IsDefaultBranch, append it to the branch_list
#                                 if default_branches is not None and default_branches.IsDefaultBranch is True and \
#                                         branch_code[
#                                             'IsDefaultBranch'] == True and default_branches.DUserId != delivery_user_id:
#                                     # Appending the branch name to branch_name_list
#                                     branch_name_list.append(default_branches.BranchName)
#                                     # Appending the branch name to d_user_list
#                                     d_user_list.append(default_branches.UserName)

#                                 if branch_code['BranchCode'] not in delivery_user_branch_codes:
#                                     # This branch_code is not present in the table. So insert a new record.
#                                     new_delivery_user_branch_code = DeliveryUserBranch(
#                                         DUserId=delivery_user_id,
#                                         BranchCode=branch_code['BranchCode'],
#                                         AddedBy=user_id,
#                                         RecordCreatedDate=get_current_date(),
#                                         IsDefaultBranch=branch_code['IsDefaultBranch']
#                                     )
#                                     db.session.add(new_delivery_user_branch_code)
#                                 else:
#                                     # Getting DeliveryUserBranch details
#                                     d_user_branch = db.session.query(DeliveryUserBranch).filter(
#                                         DeliveryUserBranch.DUserId == delivery_user_id,
#                                         DeliveryUserBranch.IsDeleted == 0,
#                                         DeliveryUserBranch.BranchCode == branch_code['BranchCode']).one_or_none()

#                                     # Updating DeliveryUserBranch table
#                                     d_user_branch.IsDefaultBranch = branch_code['IsDefaultBranch']

#                         existing_device_details = db.session.query(DeliveryUserEDCDetail).filter(
#                             DeliveryUserEDCDetail.DUserId == delivery_user_id,
#                             DeliveryUserEDCDetail.IsDeleted == 0).one_or_none()

#                         if not user_has_device and existing_device_details:
#                             existing_device_details.IsDeleted = 1

#                         if device_details[0]:

#                             if existing_device_details:
#                                 existing_device_details.IsDeleted = 1

#                             new_device_details = DeliveryUserEDCDetail(
#                                 DUserId=delivery_user_id,
#                                 Tid=device_details[0]['t_id'],
#                                 MerchantId=device_details[0]['m_id'],
#                                 IsDeleted=0,
#                                 DeviceSerialNumber=device_details[0]['s_no'],
#                                 MerchantKey=device_details[0]['merchant_key']
#                             )
#                             db.session.add(new_device_details)

#                         updated = True
#             else:
#                 error_msg = 'Delivery user not found.'

#         except Exception as e:
#             db.session.rollback()
#             error_logger(f'Route: {request.path}').error(e)
#         # Checking is there any branches with IsDefaultBranch
#         if len(branch_name_list) > 0:
#             db.session.rollback()
#             # Removing list brackets
#             branches_names = ','.join(map(str, branch_name_list))
#             d_users = ','.join(map(str, d_user_list))

#             # Making a string of error message
#             error_msg = f"{branches_names} branche(s) are already assigned for the  delivery user(s) {d_users}"
#             final_data = generate_final_data('CUSTOM_FAILED', error_msg)

#         elif updated:
#             db.session.commit()
#             final_data = generate_final_data('DATA_UPDATED')
#         else:
#             if error_msg:
#                 final_data = generate_final_data('CUSTOM_FAILED', error_msg)
#             else:
#                 final_data = generate_final_data('DATA_UPDATE_FAILED')

#     else:
#         # Form validation error.
#         final_data = generate_final_data('FORM_ERROR')
#         final_data['errors'] = populate_errors(update_delivery_user_form.errors)

#     return final_data





@store_console_blueprint.route('/register_store_user', methods=["POST"])
@authenticate('store_user')
def register_store_user():
    """
    API for registering an delivery user.
    @return:
    """
    register_store_user_form = RegisterStoreUserForm()
    if register_store_user_form.validate_on_submit():
        user_name = register_store_user_form.user_name.data
        mobile_number = register_store_user_form.mobile_number.data
        email = register_store_user_form.email.data
        password = register_store_user_form.password.data
        branch_codes = register_store_user_form.branch_codes.data
        is_zic = register_store_user_form.is_zic.data
        cancel_pickup_permission = register_store_user_form.cancel_pickup_permission.data
        reschedule_pickup_permission = register_store_user_form.reschedule_pickup_permission.data
        branch_changing_permission = register_store_user_form.branch_changing_permission.data
        product_screen_permission = register_store_user_form.product_screen_permission.data
        only_product_screen_permission = register_store_user_form.only_product_screen_permission.data
        screen_access = register_store_user_form.screen_access.data

        # Generating the hashed password.
        user_id = request.headers.get('user-id')
        hashed_password = generate_hash(password, 50)
        registered = False
        proceed_to_register = False
        error_msg = ''
        try:
            CreatedBy = db.session.query(StoreUser.UserName).filter(
                StoreUser.SUserId == user_id).one_or_none()
            CreatedBy = CreatedBy[0]

            if not is_zic:
                # This is not a zonal in charge. Normal store user.

                # Normal store user must have only one branch code.
                if len(branch_codes) == 1:

                    # Checking whether the store user is already present in the DB or not.
                    # existing_store_user_records = db.session.query(StoreUser.SUserId,
                    #                                                StoreUserBranch.BranchCode).distinct(
                    #     StoreUserBranch.BranchCode).outerjoin(
                    #     StoreUserBranch,
                    #     StoreUserBranch.SUserId == StoreUser.SUserId).filter(or_(
                    #     StoreUser.MobileNo == mobile_number,
                    #     StoreUserBranch.BranchCode.in_(branch_codes), StoreUserBranch.IsDeleted == 0),
                    #     StoreUser.IsZIC == 0,
                    #     StoreUser.IsAdmin == 0).all()
                    # Edited by MMM
                    existing_store_user_records = db.session.query(StoreUser.SUserId,
                                                                   StoreUserBranch.BranchCode).distinct(
                        StoreUserBranch.BranchCode).outerjoin(
                        StoreUserBranch,
                        StoreUserBranch.SUserId == StoreUser.SUserId).filter(StoreUser.MobileNo == mobile_number,
                                                                             StoreUserBranch.IsDeleted == 0).all()
                    # Edited by MMM
                    if not existing_store_user_records:
                        # No store user found.
                        proceed_to_register = True
                    else:
                        error_msg = 'This store user is already registered.'
                else:
                    # Multiple branch codes given.
                    error_msg = 'Multiple branch codes are not allowed for a normal store user.'

            else:
                # This is a zonal in charge.
                existing_store_user_records = db.session.query(StoreUser).filter(
                    StoreUser.MobileNo == mobile_number).one_or_none()

                if existing_store_user_records is None:
                    # No previous users are found.
                    proceed_to_register = True
                else:
                    error_msg = 'This store user is already registered.'

            if proceed_to_register:

                # No previous records found. Proceed to register the store user.
                new_store_user = StoreUser(
                    UserName=user_name,
                    MobileNo=mobile_number,
                    Password=hashed_password,
                    EmailId=email,
                    IsZIC=is_zic,
                    RegisteredDate=get_current_date(),
                    RecordCreatedDate=get_current_date(),
                    # RecordLastUpdatedDate=get_current_date(),
                    CancellPickupPermission=cancel_pickup_permission,
                    ReschedulePickupPermission=reschedule_pickup_permission,
                    BranchChangePermission=branch_changing_permission,
                    ProductScreenPermission=product_screen_permission,

                    OnlyProductScreenAccess = only_product_screen_permission,
                    AddedBy = CreatedBy
                )

                # Adding new store user.
                db.session.add(new_store_user)
                db.session.commit()

                # Add the branches to the store user.
                for branch_code in branch_codes:
                    new_store_user_branch_code = StoreUserBranch(
                        SUserId=new_store_user.SUserId,
                        BranchCode=branch_code,
                        RecordCreatedDate=get_current_date(),
                        RecordLastUpdatedDate=get_current_date()
                    )
                    db.session.add(new_store_user_branch_code)
                    db.session.commit()

                registered = True

        except Exception as e:
            db.session.rollback()
            error_logger(f'Route: {request.path}').error(e)

        if registered:
            final_data = generate_final_data('DATA_SAVED')
        else:
            if error_msg:
                final_data = generate_final_data('CUSTOM_FAILED', error_msg)
            else:
                final_data = generate_final_data('DATA_SAVE_FAILED')

    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(register_store_user_form.errors)

    return final_data


@store_console_blueprint.route('/update_store_user', methods=["PUT"])
@authenticate('store_user')
def update_store_user():
    """
    API for updating an existing store user.
    @return:
    """
    update_store_user_form = UpdateStoreUserForm()
    if update_store_user_form.validate_on_submit():
        store_user_id = update_store_user_form.store_user_id.data
        user_name = None if update_store_user_form.user_name.data == '' else update_store_user_form.user_name.data
        email = None if update_store_user_form.email.data == '' else update_store_user_form.email.data
        password = None if update_store_user_form.password.data == '' else update_store_user_form.password.data
        branch_codes = update_store_user_form.branch_codes.data
        cancel_pickup_permission = update_store_user_form.cancel_pickup_permission.data
        reschedule_pickup_permission = update_store_user_form.reschedule_pickup_permission.data
        branch_changing_permission = update_store_user_form.branch_changing_permission.data
        product_screen_permission = update_store_user_form.product_screen_permission.data
        only_product_screen_permission = update_store_user_form.only_product_screen_permission.data
        screen_access = update_store_user_form.screen_access.data
        user_id = request.headers.get('user-id')
        updated = False
        error_msg = ''
        try:
            # Checking whether the store user is already present in the DB or not.
            store_user = db.session.query(StoreUser).filter(
                StoreUser.SUserId == store_user_id).one_or_none()
            if store_user is not None:
                # Store user is present.
                if store_user.IsAdmin == 0:

                    if user_name is None:
                        user_name = store_user.UserName

                    if email is None:
                        email = store_user.EmailId

                    if password is None:
                        # No new password provided.
                        password = store_user.Password
                    else:
                        # Generating the hashed password.
                        password = generate_hash(password, 50)

                    # Updating the details.
                    store_user.CancellPickupPermission = cancel_pickup_permission
                    store_user.ReschedulePickupPermission = reschedule_pickup_permission
                    store_user.BranchChangePermission = branch_changing_permission
                    store_user.UserName = user_name
                    store_user.EmailId = email
                    store_user.Password = password
                    store_user.ModifiedBy = user_id
                    store_user.OnlyProductScreenAccess = only_product_screen_permission
                    store_user.ProductScreenPermission = product_screen_permission
                    store_user.RecordLastUpdatedDate = get_current_date()
                    db.session.commit()

                    if branch_codes:
                        # Getting the branch codes associated with the store user.
                        store_user_branch_codes = store_controller_queries.get_store_user_branches(store_user_id)

                        # Getting the existing store user's branch code that are not in
                        # the given branch_codes list and delete them.
                        other_existing_user_branch_codes = db.session.query(StoreUserBranch).filter(
                            StoreUserBranch.BranchCode.notin_(branch_codes),
                            StoreUserBranch.SUserId == store_user_id, StoreUserBranch.IsDeleted == 0).all()
                        if other_existing_user_branch_codes:
                            for existing_user_branch_code in other_existing_user_branch_codes:
                                existing_user_branch_code.IsDeleted = 1
                                existing_user_branch_code.RecordLastUpdatedDate = get_current_date()
                                db.session.commit()

                        # Add the branches to the store user.
                        for branch_code in branch_codes:
                            if branch_code not in store_user_branch_codes:
                                # This branch_code is not present in the table. So insert a new record.
                                new_store_user_branch_code = StoreUserBranch(
                                    SUserId=store_user_id,
                                    BranchCode=branch_code,
                                    RecordCreatedDate=get_current_date()
                                )
                                db.session.add(new_store_user_branch_code)
                                db.session.commit()

                    updated = True
                    if updated:
                        branches = ','.join(branch_codes)
                        # update branch code to fabricare
                        # query = f"EXEC {SERVER_DB}.dbo.UpdateUserBranchinFabricare @branches='{branches}',@username='{user_name}'"
                        # db.engine.execute(text(query).execution_options(autocommit=True))
                else:
                    error_msg = 'Can not update the admin.'
            else:
                error_msg = 'Store user not found.'

        except Exception as e:
            db.session.rollback()
            error_logger(f'Route: {request.path}').error(e)

        if updated:
            final_data = generate_final_data('DATA_UPDATED')
        else:
            if error_msg:
                final_data = generate_final_data('CUSTOM_FAILED', error_msg)
            else:
                final_data = generate_final_data('DATA_UPDATE_FAILED')

    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(update_store_user_form.errors)

    return final_data


# @store_console_blueprint.route('/reschedule_delivery', methods=["POST"])
# #@authenticate('store_user')
# def reschedule_delivery():
#     """
#     API for rescheduling a delivery request.
#     @return:
#     """
#     reschedule_form = RescheduleDeliveryForm()
#     user_id = request.headers.get('user-id')
#     modified_name = db.session.query(StoreUser.UserName).filter(StoreUser.SUserId == user_id).one_or_none()
#     if reschedule_form.validate_on_submit():
#         delivery_requests = reschedule_form.delivery_requests.data
#         reschedule_reason_id = reschedule_form.reschedule_reason_id.data
#         rescheduled_date = reschedule_form.rescheduled_date.data
#         # rescheduled_date will be DD-MM-YYYY format. Need to convert into YYYY-MM-DD format.
#         # Here, first convert the string date to date object in expected form. Here, the string date will be
#         # in dd-mm-yyyy form.
#         rescheduled_date_obj = datetime.strptime(rescheduled_date, "%d-%m-%Y")
#         # From the date object, convert the date to YYYY-MM-DD format.
#         formatted_rescheduled_date = rescheduled_date_obj.strftime("%Y-%m-%d %H:%M:%S")
#         time_slot_id = reschedule_form.time_slot_id.data
#         delivery_user_id = None if reschedule_form.delivery_user_id.data == '' else reschedule_form.delivery_user_id.data
#         # address_id = None if reschedule_form.address_id.data == '' else reschedule_form.address_id.data
#         remarks = None if reschedule_form.remarks.data == '' else reschedule_form.remarks.data
#         valid_delivery_user = False
#         valid_time_slot = False
#         delivery_time_slot = None
#         clocked_in_check = False
#         error_msg = ''
#         is_rescheduled = False
#         first_time_assign = False
#         # Edited By MMM

#         if db.session.query(DeliveryUser).filter(DeliveryUser.IsActive == 1, DeliveryUser.DUserId == delivery_user_id). \
#                 one_or_none():
#             # Edited By MMM
#             try:

#                 for delivery_request_id in delivery_requests:
#                     # Getting the delivery request table details. No completed delivery should be present
#                     # for this delivery request.

#                     delivery_request_details = db.session.query(DeliveryRequest).outerjoin(Delivery,
#                                                                                            Delivery.DeliveryRequestId == DeliveryRequest.DeliveryRequestId).filter(
#                         DeliveryRequest.DeliveryRequestId == delivery_request_id, DeliveryRequest.IsDeleted == 0,
#                         Delivery.DeliveryId == None).one_or_none()

#                     if delivery_request_details is not None:
#                         # Edited by MMM
#                         base_query = db.session.query(DeliveryReschedule).filter(
#                             DeliveryReschedule.DeliveryRequestId == delivery_request_id,
#                             DeliveryReschedule.IsDeleted == 0)
#                         try:
#                             # If the delivery user is present in the request, check the delivery user's branch code
#                             # Check whether the delivery is already rescheduled or not.
#                             # If the delivery request is already rescheduled, no further reschedules are allowed.
#                             delivery_reschedule = base_query.one_or_none()
#                         except MultipleResultsFound:
#                             delivery_reschedule = base_query.order_by(desc(DeliveryReschedule.RecordCreatedDate)).all()
#                             duplicate_ids = [i.Id for i in delivery_reschedule]
#                             deleted_id_list = duplicate_ids.remove(max(duplicate_ids))
#                             for i in duplicate_ids:
#                                 delivery_reschedule = base_query.filter(DeliveryReschedule.Id == i).one_or_none()
#                                 delivery_reschedule.IsDeleted = 1
#                                 db.session.commit()
#                         delivery_reschedule = base_query.one_or_none()
#                         # Edited by MMM
#                         # If the delivery user is present in the request, check the delivery user's branch code

#                         # Check whether the delivery is already rescheduled or not.
#                         # If the delivery request is already rescheduled, no further reschedules are allowed.
#                         # delivery_reschedule = db.session.query(DeliveryReschedule).filter(
#                         #     DeliveryReschedule.DeliveryRequestId == delivery_request_id,
#                         #     DeliveryReschedule.IsDeleted == 0).one_or_none()

#                         if delivery_reschedule is None:
#                             # No previous reschedule details are available.
#                             if delivery_request_details.DUserId is None:
#                                 # No previous delivery user has been assigned to this activity.
#                                 first_time_assign = True

#                             # Check if the given date is a branch holiday or not.
#                             holiday = delivery_controller_queries.check_branch_holiday(rescheduled_date,
#                                                                                        delivery_request_details.BranchCode)

#                             if not holiday:
#                                 # The given date is a not a branch holiday. Reschedule can be performed.

#                                 # Checking the delivery user can be assigned to this reschedule or not.
#                                 if delivery_user_id is None:
#                                     # No delivery user is provided. Here, the delivery user is the original delivery user.
#                                     delivery_user_id = delivery_request_details.DUserId

#                                 delivery_user = db.session.query(DeliveryUser).filter(
#                                     DeliveryUser.DUserId == delivery_user_id).one_or_none()

#                                 log_data = {
#                                     'Duser Id 1:':delivery_user_id
#                                 }
#                                 info_logger(f'Route: {request.path}').info(json.dumps(log_data))

#                                 if delivery_user_id is not None:

#                                     # If the rescheduled date is today, check if the
#                                     # if the delivery user is clocked in for today
#                                     if formatted_rescheduled_date == get_today():
#                                         # Check whether the delivery user is clocked in or not.
#                                         delivery_user_attendance = db.session.query(
#                                             DeliveryUserAttendance.ClockInTime).filter(
#                                             DeliveryUserAttendance.Date == get_today(),
#                                             DeliveryUserAttendance.DUserId == delivery_user_id).one_or_none()

#                                         if delivery_user_attendance is not None:
#                                             clocked_in_check = True
#                                         else:
#                                             # Delivery user has not clocked in yet for the day.
#                                             pass
#                                     else:
#                                         # This is a future date. Clocked in restriction can not be enforced here.
#                                         clocked_in_check = True

#                                     if clocked_in_check:
#                                         # Getting the branch codes associated with the delivery user.
#                                         delivery_user_branch_codes = delivery_controller_queries.get_delivery_user_branches(
#                                             delivery_user.DUserId, True)
#                                         # The given delivery user must belong
#                                         # to the delivery request's branch code.
#                                         if delivery_request_details.BranchCode in delivery_user_branch_codes:
#                                             # The delivery user can be assigned.
#                                             valid_delivery_user = True

#                                             # Checking whether the given time slot id is belong to this branch or not.
#                                             # delivery_time_slot = db.session.query(PickupTimeSlot.TimeSlotFrom,
#                                             #                                       PickupTimeSlot.TimeSlotTo).filter(
#                                             #     PickupTimeSlot.PickupTimeSlotId == time_slot_id,
#                                             #     PickupTimeSlot.BranchCode == delivery_request_details.BranchCode,
#                                             #     or_(PickupTimeSlot.VisibilityFlag == 1,
#                                             #         PickupTimeSlot.DefaultFlag == 1)).one_or_none()
#                                             # Checking whether the given time slot id is belong to this branch or not.
#                                             # Getting the matching time slot from CustomerTimeSlot table
#                                             delivery_time_slot = db.session.query(CustomerTimeSlot.TimeSlotFrom,
#                                                                                   CustomerTimeSlot.TimeSlotTo).filter(
#                                                 CustomerTimeSlot.TimeSlotId == time_slot_id,
#                                                 CustomerTimeSlot.IsDeleted == 0,
#                                                 CustomerTimeSlot.IsActive == 1).one_or_none()

#                                             if delivery_time_slot is not None:
#                                                 valid_time_slot = True
#                                     else:
#                                         error_msg = "Delivery user has not clocked in for the day."

#                                 else:
#                                     error_msg = 'No delivery user found.'

#                                 if valid_delivery_user and valid_time_slot:

#                                     # If the optional fields are None, fill up with the existing details.

#                                     # if address_id is None:
#                                     address_id = delivery_request_details.CustAddressId

#                                     if delivery_user_id is None:
#                                         delivery_user_id = delivery_request_details.DUserId

#                                     # Setting up the new DeliveryReschedule object.
#                                     new_reschedule = DeliveryReschedule(DeliveryRequestId=delivery_request_id,
#                                                                         RescheduleReasonId=reschedule_reason_id,
#                                                                         RescheduledDate=formatted_rescheduled_date,
#                                                                         # DeliveryTimeSlotId=time_slot_id,
#                                                                         # Insert DeliveryTimeSlotId in deliveryrequest table
#                                                                         DeliveryTimeSlotId=delivery_request_details.DeliveryTimeSlotId,
#                                                                         TimeSlotFrom=delivery_time_slot.TimeSlotFrom,
#                                                                         TimeSlotTo=delivery_time_slot.TimeSlotTo,
#                                                                         CustAddressId=address_id,
#                                                                         RescheduleRemarks=remarks,
#                                                                         RescheduledStoreUser=user_id,
#                                                                         CustomerPreferredTimeSlot=time_slot_id,
#                                                                         RescheduledBy=modified_name[0]
#                                                                         )
#                                     db.session.add(new_reschedule)
#                                     if formatted_rescheduled_date > get_today():
#                                         new_reschedule.DUserId = None
#                                         delivery_request_details.DUserId = None
#                                     else:
#                                         new_reschedule.DUserId = delivery_user_id
#                                     db.session.commit()

#                                     # Updating the RecordLastUpdatedDate in the delivery request table.
#                                     delivery_request_details.RecordLastUpdatedDate = get_current_date()

#                                     delivery_request_details.ReschuduleStatus = 1
#                                     delivery_request_details.ReschuduleDate =  formatted_rescheduled_date
#                                     delivery_request_details.ReschuduleBy = user_id
#                                     delivery_request_details.DUserId = delivery_user_id
#                                     delivery_request_details.ReschuduleAddressId = address_id
#                                     delivery_request_details.ReschuduleModifiedDate = get_current_date()
#                                     delivery_request_details.ReschuduleTimeSlotId = time_slot_id

#                                     delivery_time_slot = db.session.query(CustomerTimeSlot.TimeSlotFrom,
#                                                                                   CustomerTimeSlot.TimeSlotTo).filter(
#                                                 CustomerTimeSlot.TimeSlotId == time_slot_id,
#                                                 CustomerTimeSlot.IsDeleted == 0,
#                                                 CustomerTimeSlot.IsActive == 1).one_or_none()
#                                     if delivery_time_slot is not None:
#                                         valid_time_slot = True
#                                         delivery_request_details.ReschuduleTimeSlotFrom = (delivery_time_slot.TimeSlotFrom).strftime('%H:%M:%S')
#                                         delivery_request_details.ReschuduleTimeSlotTo = (delivery_time_slot.TimeSlotTo).strftime('%H:%M:%S')
#                                     else:
#                                         error_msg = "Invalid Time Slot."                                              
#                                     # delivery_request_details.ReschuduleTimeSlotFrom = delivery_time_slot.time_slot_from
#                                     # delivery_request_details.ReschuduleTimeSlotTo = delivery_time_slot.time_slot_to

#                                     if delivery_request_details.WalkIn == 1:
#                                         # Making this flag 0. Then only it'll appear in the activity list/store console's
#                                         # pending activities.
#                                         delivery_request_details.WalkIn = 0
#                                     db.session.commit()

#                                     # Updating the address change in the Orders table.
#                                     order_details = db.session.query(Order).filter(
#                                         Order.OrderId == delivery_request_details.OrderId,
#                                         Order.IsDeleted == 0).one_or_none()

#                                     if order_details is not None:
#                                         order_details.DeliveryAddressId = address_id
#                                         order_details.RecordLastUpdatedDate = get_current_date()
#                                         db.session.commit()

#                                     is_rescheduled = True
#                                     if first_time_assign and formatted_rescheduled_date == get_today():
#                                         # Check if the delivery date is today.
#                                         # If the delivery date is today, and current time is past 9'o clock,
#                                         # needs to trigger the alert engine SP to send the SMS for delivery.
#                                         order_details = db.session.query(Order.EGRN).filter(
#                                             Order.OrderId == delivery_request_details.OrderId).one_or_none()
#                                         if order_details is not None:
#                                             store_controller_queries.trigger_out_for_activity_sms('OUT_FOR_DELIVERY',
#                                                                                                   delivery_request_details.CustomerId,
#                                                                                                   None,
#                                                                                                   order_details.EGRN)
#                                     else:
#                                         if formatted_rescheduled_date != get_today():
#                                             # If the rescheduled date is not current date, then trigger DELIVERY_RESCHEDULE
#                                             # SMS via alert engine.
#                                             store_controller_queries.trigger_delivery_reschedule_sms(
#                                                 'DELIVERY_RESCHEDULE',
#                                                 delivery_request_details.CustomerId,
#                                                 delivery_request_details.DeliveryRequestId,
#                                                 order_details.EGRN,
#                                                 rescheduled_date)

#                                 else:
#                                     log_data = {
#                                         'Duser Id 2:':delivery_user_id
#                                     }
#                                     info_logger(f'Route: {request.path}').info(json.dumps(log_data))
#                                     if not valid_delivery_user:
#                                         error_msg = "No delivery user found."
#                                     elif not error_msg:
#                                         error_msg = 'This delivery user/time slot does not belong to this branch.'
#                             else:
#                                 error_msg = 'This is a branch holiday. Please choose another date.'

#                         else:
#                             # Delivery reschedule is already present.

#                             # Check if the given date is a branch holiday or not.
#                             holiday = delivery_controller_queries.check_branch_holiday(rescheduled_date,
#                                                                                        delivery_request_details.BranchCode)
#                             log_data = {
#                                 'Duser Id :':'testtt'
#                             }
#                             info_logger(f'Route: {request.path}').info(json.dumps(log_data))
#                             if not holiday:
#                                 # The given date is not a branch holiday. So reschedule can be performed.

#                                 # Checking the delivery user can be assigned to this reschedule or not.
#                                 if delivery_user_id is None:
#                                     # No delivery user is provided. Here, the delivery user is the rescheduled delivery user.
#                                     delivery_user_id = delivery_reschedule.DUserId

#                                 if delivery_user_id is not None:
#                                     delivery_user = db.session.query(DeliveryUser).filter(
#                                         DeliveryUser.DUserId == delivery_user_id).one_or_none()
#                                     if delivery_user is not None:

#                                         # If the rescheduled date is today, check if the
#                                         # if the delivery user is clocked in for today
#                                         if formatted_rescheduled_date == get_today():
#                                             # Check whether the delivery user is clocked in or not.
#                                             delivery_user_attendance = db.session.query(
#                                                 DeliveryUserAttendance.ClockInTime).filter(
#                                                 DeliveryUserAttendance.Date == get_today(),
#                                                 DeliveryUserAttendance.DUserId == delivery_user_id).one_or_none()
#                                             if delivery_user_attendance is not None:
#                                                 clocked_in_check = True
#                                             else:
#                                                 # Delivery user has not clocked in yet for the day.
#                                                 pass
#                                         else:
#                                             # This is a future date. Clocked in restriction can not be enforced here.
#                                             clocked_in_check = True

#                                         if clocked_in_check:
#                                             # Getting the branch codes associated with the delivery user.
#                                             delivery_user_branch_codes = delivery_controller_queries.get_delivery_user_branches(
#                                                 delivery_user.DUserId, True)

#                                             # The given delivery user must belong
#                                             # to the delivery requests's branch code.
#                                             if delivery_request_details.BranchCode in delivery_user_branch_codes:
#                                                 # The delivery user can be assigned.
#                                                 valid_delivery_user = True

#                                             # Checking whether the given time slot id is belong to this branch or not.
#                                             # delivery_time_slot = db.session.query(PickupTimeSlot.TimeSlotFrom,
#                                             #                                       PickupTimeSlot.TimeSlotTo).filter(
#                                             #     PickupTimeSlot.PickupTimeSlotId == time_slot_id,
#                                             #     PickupTimeSlot.BranchCode == delivery_request_details.BranchCode,
#                                             #     or_(PickupTimeSlot.VisibilityFlag == 1,
#                                             #         PickupTimeSlot.DefaultFlag == 1)).one_or_none()
#                                             # Getting the matching time slot from CustomerTimeSlot table
#                                             delivery_time_slot = db.session.query(CustomerTimeSlot.TimeSlotFrom,
#                                                                                   CustomerTimeSlot.TimeSlotTo).filter(
#                                                 CustomerTimeSlot.TimeSlotId == time_slot_id,
#                                                 CustomerTimeSlot.IsDeleted == 0,
#                                                 CustomerTimeSlot.IsActive == 1).one_or_none()

#                                             if delivery_time_slot is not None:
#                                                 valid_time_slot = True
#                                         else:
#                                             error_msg = "Delivery user has not clocked in for the day."
#                                 else:
#                                     # No delivery user change.
#                                     valid_delivery_user = True

#                                 if valid_delivery_user and valid_time_slot:
#                                     # If the optional fields are None, fill up with the existing details.

#                                     # if address_id is None:
#                                     address_id = delivery_reschedule.CustAddressId

#                                     if delivery_user_id is None:
#                                         delivery_user_id = delivery_reschedule.DUserId

#                                     # Delete the row and insert again.
#                                     delivery_reschedule.IsDeleted = 1
#                                     delivery_reschedule.CancelledDate = get_current_date()
#                                     db.session.commit()

#                                     # After making the previous reschedule delete, create a new entry in
#                                     # the DeliveryReschedule table.
#                                     new_reschedule = DeliveryReschedule(DeliveryRequestId=delivery_request_id,
#                                                                         RescheduleReasonId=reschedule_reason_id,
#                                                                         RescheduledDate=formatted_rescheduled_date,
#                                                                         # DeliveryTimeSlotId=time_slot_id,
#                                                                         # Insert DeliveryTimeSlotId in deliveryrequest table
#                                                                         DeliveryTimeSlotId=delivery_request_details.DeliveryTimeSlotId,
#                                                                         TimeSlotFrom=delivery_time_slot.TimeSlotFrom,
#                                                                         TimeSlotTo=delivery_time_slot.TimeSlotTo,
#                                                                         CustAddressId=address_id,
#                                                                         RescheduleRemarks=remarks,
#                                                                         RescheduledStoreUser=user_id,
#                                                                         CustomerPreferredTimeSlot=time_slot_id,
#                                                                         RescheduledBy=modified_name[0]
#                                                                         )

#                                     db.session.add(new_reschedule)
#                                     if formatted_rescheduled_date > get_today():
#                                         new_reschedule.DUserId = None
#                                         delivery_request_details.DUserId = None
#                                     else:
#                                         new_reschedule.DUserId = delivery_user_id
#                                     db.session.commit()
#                                     log_data = {
#                                         'Duser Id :':'testtt22'
#                                     }
#                                     info_logger(f'Route: {request.path}').info(json.dumps(log_data))
#                                     # Updating the RecordLastUpdatedDate in the delivery request table.
#                                     delivery_request_details.RecordLastUpdatedDate = get_current_date()

#                                     delivery_request_details.ReschuduleStatus = 1
#                                     delivery_request_details.ReschuduleDate =  formatted_rescheduled_date
#                                     delivery_request_details.ReschuduleBy = user_id
#                                     delivery_request_details.DUserId = delivery_user_id
#                                     delivery_request_details.ReschuduleAddressId = address_id
#                                     delivery_request_details.ReschuduleModifiedDate = get_current_date()
#                                     delivery_request_details.ReschuduleTimeSlotId = time_slot_id

#                                     delivery_time_slot = db.session.query(CustomerTimeSlot.TimeSlotFrom,
#                                                                                   CustomerTimeSlot.TimeSlotTo).filter(
#                                                 CustomerTimeSlot.TimeSlotId == time_slot_id,
#                                                 CustomerTimeSlot.IsDeleted == 0,
#                                                 CustomerTimeSlot.IsActive == 1).one_or_none()
#                                     if delivery_time_slot is not None:
#                                         valid_time_slot = True
#                                         delivery_request_details.ReschuduleTimeSlotFrom = (delivery_time_slot.TimeSlotFrom).strftime('%H:%M:%S')
#                                         delivery_request_details.ReschuduleTimeSlotTo = (delivery_time_slot.TimeSlotTo).strftime('%H:%M:%S')
#                                     else:
#                                         error_msg = "Invalid Time Slot."

#                                     # delivery_request_details.ReschuduleTimeSlotFrom = time_slot_from
#                                     # delivery_request_details.ReschuduleTimeSlotTo = time_slot_to

#                                     if delivery_request_details.WalkIn == 1:
#                                         # Making this flag 0. Then only it'll appear in the activity list/store console's
#                                         # pending activities.
#                                         delivery_request_details.WalkIn = 0
#                                     db.session.commit()

#                                     # Updating the address change in the Orders table.
#                                     order_details = db.session.query(Order).filter(
#                                         Order.OrderId == delivery_request_details.OrderId,
#                                         Order.IsDeleted == 0).one_or_none()

#                                     if order_details is not None:
#                                         order_details.DeliveryAddressId = address_id
#                                         order_details.RecordLastUpdatedDate = get_current_date()
#                                         db.session.commit()

#                                     is_rescheduled = True
#                                     if formatted_rescheduled_date != get_today():
#                                         # If the rescheduled date is not current date, then trigger DELIVERY_RESCHEDULE
#                                         # SMS via alert engine.
#                                         store_controller_queries.trigger_delivery_reschedule_sms('DELIVERY_RESCHEDULE',
#                                                                                                  delivery_request_details.CustomerId,
#                                                                                                  delivery_request_details.DeliveryRequestId,
#                                                                                                  order_details.EGRN,
#                                                                                                  rescheduled_date)
#                                 else:
#                                     if not valid_delivery_user:
#                                         error_msg = "No delivery user found."
#                                     elif not error_msg:
#                                         error_msg = 'This delivery user/time slot does not belong to this branch.'
#                             else:
#                                 error_msg = 'This is a branch holiday. Please choose another date.'

#                     # If any error_msg are found, break from the loop.
#                     if error_msg:
#                         break

#             except Exception as e:
#                 error_logger(f'Route: {request.path}').error(e)

#             if is_rescheduled:
#                 final_data = generate_final_data('DATA_UPDATED')
#                 customer_code = db.session.query(Customer).filter(
#                     Customer.CustomerId == delivery_request_details.CustomerId).one_or_none()
#                 original_date = datetime.strptime(rescheduled_date, "%d-%m-%Y")
#                 formatted_rescheduled_date = original_date.strftime("%Y-%m-%d")
#                 time_slot = db.session.query(CustomerTimeSlot.TimeSlotFrom,
#                                              CustomerTimeSlot.TimeSlotTo,
#                                              CustomerTimeSlot.TimeSlot).filter(CustomerTimeSlot.TimeSlotId == time_slot_id,
#                     CustomerTimeSlot.IsDeleted == 0,
#                     CustomerTimeSlot.IsActive == 1).one_or_none()
#                 time_slot = time_slot.TimeSlot
#                 query = f"EXEC JFSL_UAT..FetchtimeslotForApp @SP_Type='1',@Egrno='{order_details.EGRN}'," \
#                         f"@Customercode='{customer_code.CustomerCode}',@Timeslot='{time_slot}',@Datedt='{formatted_rescheduled_date}'," \
#                         f"@Days=null,@modifiedby='FabExpress',@branchcode='{delivery_request_details.BranchCode}'"
#                 db.engine.execute(text(query).execution_options(autocommit=True))
#                 log_data = {
#                     'query of reschedule delivery': query
#                 }
#                 info_logger(f'Route: {request.path}').info(json.dumps(log_data))
#                 # Invoke push notification if the delivery is scheduled for today or lesser
#                 if formatted_rescheduled_date <= get_today():
#                     send_push_notification(delivery_user_id, 'DELIVERY', None, "JFSLSTORE", user_id)
#             else:
#                 if error_msg:
#                     final_data = generate_final_data('CUSTOM_FAILED', error_msg)
#                 else:
#                     final_data = generate_final_data('DATA_UPDATE_FAILED')
#         else:
#             final_data = generate_final_data('CUSTOM_FAILED', 'Delivery user is inactive')
#     else:
#         # Form validation error.
#         final_data = generate_final_data('FORM_ERROR')
#         final_data['errors'] = populate_errors(reschedule_form.errors)
#     return final_data


@store_console_blueprint.route('/reschedule_delivery', methods=["POST"])
# @authenticate('store_user')
def reschedule_delivery():
    """
    API for rescheduling a delivery request.
    @return:
    """
    reschedule_form = RescheduleDeliveryForm()
    user_id = request.headers.get('user-id')
    if reschedule_form.validate_on_submit():
        TRNNos  = reschedule_form.TRNNo.data
        reschedule_reason_id = reschedule_form.reschedule_reason_id.data
        CustomerNames = reschedule_form.CustomerName.data
        MobileNos = reschedule_form.MobileNo.data
        EGRNs = reschedule_form.EGRN.data
        rescheduled_date = reschedule_form.rescheduled_date.data
        rescheduled_date_obj = datetime.strptime(rescheduled_date, "%d-%m-%Y")
        current_time = datetime.now().time()
        final_datetime = datetime.combine(rescheduled_date_obj.date(), current_time)
        formatted_rescheduled_date = final_datetime.strftime("%Y-%m-%d %H:%M:%S")
        formatted_rescheduled_date1 = rescheduled_date_obj.strftime("%Y-%m-%d %H:%M:%S")
        time_slot_id = reschedule_form.time_slot_id.data
        delivery_user_id = None if reschedule_form.delivery_user_id.data == '' else reschedule_form.delivery_user_id.data
        remarks = None if reschedule_form.remarks.data == '' else reschedule_form.remarks.data
        TimeSlotFrom = None if reschedule_form.TimeSlotFrom.data == '' else reschedule_form.TimeSlotFrom.data
        TimeSlotTo = None if reschedule_form.TimeSlotTo.data == '' else reschedule_form.TimeSlotTo.data
        BranchCode = None if reschedule_form.BranchCode.data == '' else reschedule_form.BranchCode.data
        CustomerCodes = None if reschedule_form.CustomerCode.data == '' else reschedule_form.CustomerCode.data
        error_msg = ''
        is_rescheduled = False
        first_time_assign = False
        booking_id = None
        # Edited By MMM

        try:
            for i in range(len(TRNNos)):
                TRNNo = TRNNos[i]
                MobileNo = MobileNos[i]
                CustomerName = CustomerNames[i]
                egrn = EGRNs[i]

                query = f""" EXEC JFSL.Dbo.[SPFabDeliveryRescheduleUpdate] @DuserId = {delivery_user_id}, @TRNNo = '{TRNNo}',@TimeSlotId = {time_slot_id}      
                        ,@TimeSlotFrom = '{TimeSlotFrom}',@TimeSlotTo = '{TimeSlotTo}' ,@ReschuduleDate = '{formatted_rescheduled_date}',@RescheduleReasonId = {reschedule_reason_id}
                        ,@StoreUserID = {user_id}"""

                log_data = {
                    'query:':query
                         }
                info_logger(f'Route: {request.path}').info(json.dumps(log_data))
                db.engine.execute(text(query).execution_options(autocommit=True))
                is_rescheduled = True

                store_controller_queries.trigger_out_for_activity_sms('OUT_FOR_DELIVERY',
                                                                      CustomerName,booking_id,
                                                                       MobileNo,  egrn)
                                                                      
                                                                     
                                                                     

                if formatted_rescheduled_date != get_today():
                    store_controller_queries.trigger_delivery_reschedule_sms(
                        'DELIVERY_RESCHEDULE',MobileNo,TRNNo,
                        egrn,rescheduled_date,
                        CustomerName, user_id)
                         
                        

        except Exception as e:
            error_logger(f'Route: {request.path}').error(e)

        if is_rescheduled:
            time_slot = f"{TimeSlotFrom} to {TimeSlotTo}"
            final_data = generate_final_data('DATA_UPDATED')
            # query = f"EXEC JFSL..FetchtimeslotForApp @SP_Type='1',@Egrno='{EGRN}'," \
            #             f"@Customercode='{CustomerCode}',@Timeslot='{time_slot}',@Datedt='{formatted_rescheduled_date}'," \
            #             f"@Days=null,@modifiedby='FabExpress',@branchcode='{BranchCode}'"
            # db.engine.execute(text(query).execution_options(autocommit=True))

            if formatted_rescheduled_date1 <= get_today():
                log_data = {
                'send_push_notification_test:':"send_push_notification_test"
                     }
                info_logger(f'Route: {request.path}').info(json.dumps(log_data))
                send_push_notification_test(delivery_user_id, 'DELIVERY', None, "JFSLSTORE", user_id)
            else:
                if error_msg:
                    final_data = generate_final_data('CUSTOM_FAILED', error_msg)
                
        else:
            final_data = generate_final_data('CUSTOM_FAILED', 'Delivery user is inactive')
    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(reschedule_form.errors)
    log_data = {
                'final_data:':final_data
                     }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))
    return final_data

# @store_console_blueprint.route('/get_store_users', methods=["GET"])
# @store_console_blueprint.route('/get_store_users/<report>', methods=["GET"])
# @authenticate('store_user')
# def get_store_users(report=False):
#     """
#     API for getting store users.
#     @return:
#     """
#     user_id = request.headers.get('user-id')
#     store_users = []
#     try:
#         # Getting the delivery user details from the DB.

#         # If the store user is admin, then return all the store users, otherwise, return only the
#         # store user based on given user id.
#         store_user = db.session.query(StoreUser.SUserId, StoreUser.UserName, StoreUser.MobileNo, StoreUser.EmailId,
#                                       StoreUser.IsAdmin, StoreUser.IsZIC, StoreUser.IsActive,
#                                       StoreUser.ReschedulePickupPermission,
#                                       StoreUser.CancellPickupPermission, StoreUser.BranchChangePermission,
#                                       StoreUser.ModifiedBy,StoreUser.RecordCreatedDate.label('CreatedOn'),StoreUser.AddedBy.label('CreatedBy'),
#                                       StoreUser.RecordLastUpdatedDate.label("ModifiedDate")).filter(
#             StoreUser.SUserId == user_id).one_or_none()

#         if store_user is not None:
#             if store_user.IsAdmin == 1:
#                 # The store user is admin, so select all other users.
#                 store_users = db.session.query(StoreUser.SUserId, StoreUser.UserName, StoreUser.MobileNo,
#                                                StoreUser.EmailId, StoreUser.IsZIC, StoreUser.IsActive,
#                                                StoreUser.ReschedulePickupPermission,
#                                                StoreUser.CancellPickupPermission, StoreUser.BranchChangePermission,
#                                                StoreUser.ModifiedBy,StoreUser.RecordCreatedDate.label('CreatedOn'),StoreUser.AddedBy.label('CreatedBy'),
#                                                StoreUser.RecordLastUpdatedDate.label("ModifiedDate")
#                                                ).filter(
#                     StoreUser.IsAdmin == 0).order_by(
#                     desc(StoreUser.RecordCreatedDate)
#                 ).all()
#             else:
#                 # Store user is not an admin. So select the store user details only.
#                 store_users.append(store_user)

#             store_users = SerializeSQLAResult(store_users).serialize()
#             select_branch_name = case(
#                 [(or_(Branch.DisplayName is None, Branch.DisplayName == ''), Branch.BranchName), ],
#                 else_=Branch.DisplayName)
#             # Getting the branch codes of store users.
#             for store_user in store_users:
#                 if store_user["ModifiedBy"] is not None:
#                     modified_by = db.session.query(StoreUser.UserName).filter \
#                         (StoreUser.SUserId == store_user["ModifiedBy"]).one_or_none()
#                     store_user["ModifiedBy"] = modified_by.UserName
#                 else:
#                     store_user["ModifiedBy"] = " "
#                 branch_codes = store_controller_queries.get_store_user_branches(store_user['SUserId'])
#                 # Edited by Athira
#                 # branch_codes = db.session.query(Branch).filter(Branch.BranchCode.in_(branch_codes), Branch.IsActive==1).all()
#                 branch_codes = db.session.query(Branch).filter(Branch.BranchCode.in_(branch_codes)).all()

#                 branch_codes = [store_user_branch.BranchCode for store_user_branch in branch_codes]
#                 # Edited by MMM
#                 store_user['BranchCodes'] = branch_codes
#                 branch_names = db.session.query(case([(Branch.IsActive == 0, 'Inact - ' + select_branch_name)],
#                                                      else_=select_branch_name).label('BranchName')).filter(
#                     Branch.BranchCode.in_(branch_codes)).all()
#                 joined_branch_names = [', '.join(map(str, x)) for x in branch_names]
#                 store_user['BranchNames'] = joined_branch_names
#                 # Edited by MMM
#     except Exception as e:
#         error_logger(f'Route: {request.path}').error(e)

#     if store_users:
#         final_data = generate_final_data('DATA_FOUND')
#         if report:
#             # Report flag is included in the request. So generate the file and send the file back.
#             report_link = GenerateReport(store_users, 'store_users').generate().get()
#             if report_link is not None:
#                 final_data['result'] = report_link
#             else:
#                 # Failed to generate the file.
#                 final_data = generate_final_data('FILE_NOT_FOUND')
#         else:
#             final_data['result'] = store_users
#     else:
#         final_data = generate_final_data('DATA_NOT_FOUND')

#     return final_data

@store_console_blueprint.route('/get_store_users', methods=["GET"])
@store_console_blueprint.route('/get_store_users/<report>', methods=["GET"])
@authenticate('store_user')
def get_store_users(report=False):
    """
    API for getting store users.
    @return:
    """
    user_id = request.headers.get('user-id')
    store_users = []
    try:
        # Getting the delivery user details from the DB.

        # If the store user is admin, then return all the store users, otherwise, return only the
        # store user based on given user id.

        store_user = db.session.query(StoreUser.SUserId, StoreUser.UserName, StoreUser.MobileNo, StoreUser.EmailId,
                                      StoreUser.IsAdmin, StoreUser.IsZIC, StoreUser.IsActive,
                                      StoreUser.ReschedulePickupPermission,
                                      StoreUser.CancellPickupPermission, StoreUser.BranchChangePermission,
                                      StoreUser.ModifiedBy, StoreUser.ProductScreenPermission,
                                      StoreUser.RecordLastUpdatedDate.label("ModifiedDate")).filter(
            StoreUser.SUserId == user_id).one_or_none()
        # store_user = db.session.query(StoreUser.SUserId, StoreUser.UserName, StoreUser.MobileNo, StoreUser.EmailId,
        #                               StoreUser.IsAdmin, StoreUser.IsZIC, StoreUser.IsActive,
        #                               StoreUser.ReschedulePickupPermission,
        #                               StoreUser.CancellPickupPermission, StoreUser.BranchChangePermission,
        #                               StoreUser.ModifiedBy, StoreUser.ProductScreenPermission,StoreUser.RecordCreatedDate.label('CreatedOn'),StoreUser.AddedBy.label('CreatedBy'),
        #                               StoreUser.RecordLastUpdatedDate.label("ModifiedDate")).filter(
        #     StoreUser.SUserId == user_id).one_or_none()

        if store_user is not None:
            if store_user.IsAdmin == 1:
                # The store user is admin, so select all other users.
                store_users = db.session.query(StoreUser.SUserId, StoreUser.UserName, StoreUser.MobileNo,
                                               StoreUser.EmailId, StoreUser.IsZIC, StoreUser.IsActive,
                                               StoreUser.ReschedulePickupPermission,
                                               StoreUser.CancellPickupPermission, StoreUser.BranchChangePermission,
                                               StoreUser.ModifiedBy, StoreUser.ProductScreenPermission,
                                               StoreUser.RecordLastUpdatedDate.label("ModifiedDate")
                                               ).filter(
                    StoreUser.IsAdmin == 0).all()


                # store_users = db.session.query(StoreUser.SUserId, StoreUser.UserName, StoreUser.MobileNo,
                #                                StoreUser.EmailId, StoreUser.IsZIC, StoreUser.IsActive,
                #                                StoreUser.ReschedulePickupPermission,
                #                                StoreUser.CancellPickupPermission, StoreUser.BranchChangePermission,
                #                                StoreUser.ModifiedBy,StoreUser.ProductScreenPermission,StoreUser.RecordCreatedDate.label('CreatedOn'),StoreUser.AddedBy.label('CreatedBy'),
                #                                StoreUser.RecordLastUpdatedDate.label("ModifiedDate")
                #                                ).filter(
                #     StoreUser.IsAdmin == 0).order_by(
                #     desc(StoreUser.RecordCreatedDate)
                # ).all()
            else:
                # Store user is not an admin. So select the store user details only.
                store_users.append(store_user)

            #store_users = SerializeSQLAResult(store_users).serialize()
            store_users = SerializeSQLAResult(store_users).serialize(full_date_fields=['ModifiedDate'])
            select_branch_name = case(
                [(or_(Branch.DisplayName is None, Branch.DisplayName == ''), Branch.BranchName), ],
                else_=Branch.DisplayName)
            # Getting the branch codes of store users.
            for store_user in store_users:
                if store_user["ModifiedBy"] is not None:
                    modified_by = db.session.query(StoreUser.UserName).filter \
                        (StoreUser.SUserId == store_user["ModifiedBy"]).one_or_none()
                    store_user["ModifiedBy"] = modified_by.UserName
                else:
                    store_user["ModifiedBy"] = " "
                branch_codes = store_controller_queries.get_store_user_branches(store_user['SUserId'])
                # Edited by Athira
                # branch_codes = db.session.query(Branch).filter(Branch.BranchCode.in_(branch_codes), Branch.IsActive==1).all()
                branch_codes = db.session.query(Branch).filter(Branch.BranchCode.in_(branch_codes)).all()

                branch_codes = [store_user_branch.BranchCode for store_user_branch in branch_codes]
                # Edited by MMM
                store_user['BranchCodes'] = branch_codes
                branch_names = db.session.query(case([(Branch.IsActive == 0, 'Inact - ' + select_branch_name)],
                                                     else_=select_branch_name).label('BranchName')).filter(
                    Branch.BranchCode.in_(branch_codes)).all()
                joined_branch_names = [', '.join(map(str, x)) for x in branch_names]
                store_user['BranchNames'] = joined_branch_names
                # Edited by MMM

                screen_access = db.session.execute(text("""
                    SELECT S.ScreenName,S.ScreenId
                    FROM Screens S
                    LEFT JOIN UserScreenAccess Ua ON Ua.UserId = :user_id
                    CROSS APPLY STRING_SPLIT(Ua.ScreenId, ',') AS split
                    WHERE S.ScreenId = TRY_CAST(split.value AS INT)
                """), {"user_id": store_user['SUserId']}).fetchall()

                screen_access = SerializeSQLAResult(screen_access).serialize()
                store_user['StoreAcess'] = screen_access
    except Exception as e:
        error_logger(f'Route: {request.path}').error(e)

    if store_users:
        final_data = generate_final_data('DATA_FOUND')
        if report:
            # Report flag is included in the request. So generate the file and send the file back.
            report_link = GenerateReport(store_users, 'store_users').generate().get()
            if report_link is not None:
                final_data['result'] = report_link
            else:
                # Failed to generate the file.
                final_data = generate_final_data('FILE_NOT_FOUND')
        else:
            final_data['result'] = store_users
    else:
        final_data = generate_final_data('DATA_NOT_FOUND')

    return final_data



@store_console_blueprint.route('/remove_store_user', methods=["DELETE"])
@authenticate('store_user')
def remove_store_user():
    """
    API for removing a store user.
    @return:
    """
    remove_store_user_form = RemoveStoreUserForm()
    if remove_store_user_form.validate_on_submit():
        store_user_id = remove_store_user_form.store_user_id.data
        branches_deleted = False
        user_deleted = False
        tokens_deleted = False
        try:
            # First, making the branch code(s) of that store user disable.
            store_branch_codes = db.session.query(StoreUserBranch).filter(StoreUserBranch.SUserId == store_user_id,
                                                                          StoreUserBranch.IsDeleted == 0).all()
            # if store_branch_codes:
            #     for branch in store_branch_codes:
            #         branch.IsDeleted = 1
            #         branch.RecordLastUpdatedDate = get_current_date()
            #         db.session.commit()
            #         branches_deleted = True
            # else:
            #     # No branches are associated with this store user.
            #     branches_deleted = True

            # After deleting the branches, remove the store user login tokens.
            store_user_tokens = db.session.query(StoreUserLogin).filter(StoreUserLogin.SUserId == store_user_id,
                                                                        StoreUserLogin.IsActive == 1,
                                                                        StoreUserLogin.AuthKeyExpiry == 0).all()

            # Revoking the access token generated for that user.
            if store_user_tokens:
                for store_user_token in store_user_tokens:
                    store_user_token.AuthKeyExpiry = 1
                    store_user_token.IsActive = 0
                    store_user_token.RecordLastUpdatedDate = get_current_date()
                    db.session.commit()
                    tokens_deleted = True
            else:
                # No tokens are generated for this store user.
                tokens_deleted = True

            # Finally remove the store user.
            store_user = db.session.query(StoreUser).filter(StoreUser.SUserId == store_user_id,
                                                            StoreUser.IsDeleted == 0).one_or_none()
            if store_user is not None:
                store_user.IsActive = 0
                store_user.IsDeleted = 1
                store_user.RecordLastUpdatedDate = get_current_date()
                db.session.commit()
                user_deleted = True
        except Exception as e:
            error_logger(f'Route: {request.path}').error(e)

        # branches_deleted and 

        if tokens_deleted and user_deleted:
            final_data = generate_final_data('DATA_DELETED')
        else:
            final_data = generate_final_data('DATA_DELETE_FAILED')
    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(remove_store_user_form.errors)
    return final_data


@store_console_blueprint.route('/remove_delivery_user', methods=["DELETE"])
@authenticate('store_user')
def remove_delivery_user():
    """
    API for removing a delivery user.
    @return:
    """
    remove_delivery_user_form = RemoveDeliveryUserForm()
    user_id = request.headers.get('user-id')
    if remove_delivery_user_form.validate_on_submit():
        delivery_user_id = remove_delivery_user_form.delivery_user_id.data
        branches_deleted = False
        user_deleted = False
        tokens_deleted = False
        error_msg = ''
        try:
            # Getting the branch codes associated with the delivery user.
            delivery_user_branch_codes = delivery_controller_queries.get_delivery_user_branches(delivery_user_id)

            # Before removing the customer, ensuring that the delivery person has no pending
            # assigned activities.

            # If the pickup is rescheduled, then select RescheduledDate, else select PickupDate.
            select_activity_date = case([(PickupReschedule.RescheduledDate == None, PickupRequest.PickupDate), ],
                                        else_=PickupReschedule.RescheduledDate).label("ActivityDate")

            # Getting the assigned pickup activities of a delivery user.
            assigned_pickups = store_controller_queries.get_delivery_user_assigned_pickups(select_activity_date,
                                                                                           delivery_user_branch_codes,
                                                                                           delivery_user_id)

            # If the delivery is rescheduled, then select RescheduledDate, else select DeliveryDate.
            select_activity_date = case([(DeliveryReschedule.RescheduledDate == None, DeliveryRequest.DeliveryDate), ],
                                        else_=DeliveryReschedule.RescheduledDate).label("ActivityDate")

            # Getting the assigned delivery activities of a delivery user.
            assigned_deliveries = store_controller_queries.get_delivery_user_assigned_deliveries(select_activity_date,
                                                                                                 delivery_user_branch_codes,
                                                                                                 delivery_user_id)
            assigned_activities = assigned_pickups.union(assigned_deliveries).all()

            if len(assigned_activities) > 0:
                # This user has pending activities to their name. So the store user can not remove this delivery user
                # Unless all the assigned activities are removed manually from the store console.
                error_msg = 'Unable to remove this delivery user. Some activities are currently assigned to this user. ' \
                            'Please remove this user from the activities and try again later.'

            else:
                # The delivery user has no pending activities. The user can be removed.
                # First, making the branch code(s) of that delivery user disable.
                # not remove branches - inactive the users and immediately changes active back to users.(requirement by chitra - 14/02/2023 )
                # delivery_user_branch_codes = db.session.query(DeliveryUserBranch).filter(
                #     DeliveryUserBranch.DUserId == delivery_user_id,
                #     DeliveryUserBranch.IsDeleted == 0).all()
                # if delivery_user_branch_codes:
                #     for branch in delivery_user_branch_codes:
                #         branch.IsDeleted = 1
                #         branch.RecordLastUpdatedDate = get_current_date()
                #         db.session.commit()
                #         branches_deleted = True
                # else:
                #     # No branches are found for this delivery user.
                #     branches_deleted = True

                # After deleting the branches, remove the delivery user login tokens.
                delivery_user_tokens = db.session.query(DeliveryUserLogin).filter(
                    DeliveryUserLogin.DUserId == delivery_user_id,
                    DeliveryUserLogin.IsActive == 1,
                    DeliveryUserLogin.AuthKeyExpiry == 0).all()

                # Revoking the access token generated for that user.
                if delivery_user_tokens:
                    for delivery_user_token in delivery_user_tokens:
                        delivery_user_token.AuthKeyExpiry = 1
                        delivery_user_token.IsActive = 0
                        delivery_user_token.RecordLastUpdatedDate = get_current_date()
                        db.session.commit()
                        tokens_deleted = True
                else:
                    # No access tokens are found for this user.
                    tokens_deleted = True

                # Finally remove the delivery user.
                delivery_user = db.session.query(DeliveryUser).filter(DeliveryUser.DUserId == delivery_user_id,
                                                                      DeliveryUser.IsDeleted == 0).one_or_none()
                if delivery_user is not None:
                    delivery_user.IsActive = 0
                    delivery_user.IsDeleted = 1
                    delivery_user.RemovedBy = user_id
                    delivery_user.RecordLastUpdatedDate = get_current_date()
                    db.session.commit()
                    user_deleted = True
        except Exception as e:
            error_logger(f'Route: {request.path}').error(e)

        # if branches_deleted and tokens_deleted and user_deleted:
        if tokens_deleted and user_deleted:
            # Delivery user's branches, token and account has been removed.
            final_data = generate_final_data('DATA_DELETED')
        else:
            if error_msg:
                final_data = generate_final_data('CUSTOM_FAILED', error_msg)
            else:
                final_data = generate_final_data('DATA_DELETE_FAILED')
    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(remove_delivery_user_form.errors)
    return final_data


@store_console_blueprint.route('/update_branch', methods=["PUT"])
@authenticate('store_user')
def update_branch():
    """
    API for updating the a branch's display name and holiday list.
    @return:
    """
    update_branch_form = UpdateBranchForm()
    if update_branch_form.validate_on_submit():
        branch_code = update_branch_form.branch_code.data
        branch_name = update_branch_form.branch_name.data
        holiday = update_branch_form.holiday.data
        formatted_holiday_date = None
        if holiday:
            holiday_date_obj = datetime.strptime(holiday, "%d-%m-%Y")
            # From the date object, convert the date to YYYY-MM-DD format.
            formatted_holiday_date = holiday_date_obj.strftime("%Y-%m-%d 00:00:00")
        updated = False
        try:
            # Updating the DisplayName of the branch code.
            branch = db.session.query(Branch).filter(Branch.BranchCode == branch_code, Branch.IsActive == 1,
                                                     Branch.IsDeleted == 0).one_or_none()

            if branch is not None:
                # Branch details are found. Updating the DisplayName of the branch.
                branch.DisplayName = branch_name
                branch.RecordLastUpdatedDate = get_current_date()
                db.session.commit()
                updated = True

            if holiday:
                # A holiday is given.
                # Check if the holiday is present in the DB or not. If yes, update the record.
                # If no, add the new holiday.
                branch_holiday = db.session.query(BranchHoliday).filter(
                    BranchHoliday.BranchCode == branch_code, BranchHoliday.HolidayDate == formatted_holiday_date,
                    BranchHoliday.IsActive == 1, BranchHoliday.IsDeleted == 0).one_or_none()

                if branch_holiday is not None:
                    # A record is found. Delete the record.
                    branch_holiday.IsActive = 0
                    branch_holiday.IsDeleted = 1
                    branch_holiday.RecordLastUpdatedDate = get_current_date()
                    db.session.commit()
                    updated = True
                else:
                    # No record found for this holiday.
                    new_holiday = BranchHoliday(
                        BranchCode=branch_code,
                        HolidayDate=formatted_holiday_date,
                        RecordCreatedDate=get_current_date()
                    )
                    db.session.add(new_holiday)
                    db.session.commit()
                    updated = True

        except Exception as e:
            db.session.rollback()
            error_logger(f'Route: {request.path}').error(e)

        if updated:
            final_data = generate_final_data('DATA_UPDATED')
        else:
            final_data = generate_final_data('DATA_UPDATE_FAILED')

    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(update_branch_form.errors)
    return final_data


@store_console_blueprint.route('/get_branch_holidays', methods=["POST"])
@authenticate('store_user')
def get_branch_holidays():
    """
    API for getting the list of branch holidays
    @return:
    """
    holiday_form = GetBranchHolidaysForm()
    if holiday_form.validate_on_submit():
        branch_codes = holiday_form.branch_codes.data
        try:
            # If a DisplayName found for a branch, then select DisplayName as the BranchName.
            # select_branch_name = case(
            #     [(or_(Branch.DisplayName == None, Branch.DisplayName == ''), Branch.BranchName), ],
            #     else_=Branch.DisplayName).label("BranchName")
            select_branch_name = case(
                [(or_(Branch.DisplayName == None, Branch.DisplayName == '', Branch.IsActive == True),
                  case([(Branch.IsActive == True, Branch.BranchName)], else_='Inact - ' + Branch.BranchName)), ],
                else_='Inact-' + Branch.DisplayName
            ).label("BranchName")
            select_weekly_off_days = case(
                [
                    (Branch.WeeklyOffDays == 1, 'Sunday'),
                    (Branch.WeeklyOffDays == 2, 'Monday'),
                    (Branch.WeeklyOffDays == 3, 'Tuesday'),
                    (Branch.WeeklyOffDays == 4, 'Wednesday'),
                    (Branch.WeeklyOffDays == 5, 'Friday'),
                    (Branch.WeeklyOffDays == 6, 'Saturday')
                ]).label("WeeklyOffDay")
            holiday_list = []
            if len(branch_codes) > 0:
                for branch in branch_codes:
                    branch_obj = db.session.query(select_branch_name, select_weekly_off_days, Branch.BranchCode,
                                                  Branch.IsActive).filter(Branch.BranchCode == branch).all()
                    holidays = db.session.query(BranchHoliday.HolidayDate).filter(BranchHoliday.BranchCode == branch,
                                                                                  BranchHoliday.IsActive == 1).distinct(
                        BranchHoliday.HolidayDate).all()
                    holidays = [i.HolidayDate.strftime("%d-%m-%Y") for i in holidays]
                    branch_dict = {"BranchName": branch_obj[0][0],
                                   "WeeklyOffDay": "NA" if branch_obj[0][1] is None else branch_obj[0][1],
                                   "IsActive": branch_obj[0][3], "BranchCode": branch_obj[0][2],
                                   "Holidays": holidays}
                    holiday_list.append(branch_dict)
        except Exception as e:
            error_logger(f'Route: {request.path}').error(e)

        if holiday_list:
            final_data = generate_final_data('DATA_FOUND')
            final_data['result'] = holiday_list
        else:
            final_data = generate_final_data('DATA_NOT_FOUND')
    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(holiday_form.errors)
    return final_data


@store_console_blueprint.route('/get_delivery_user_gps_logs', methods=["POST"])
@authenticate('store_user')
def get_delivery_user_gps_logs():
    """
    API for getting the log of the delivery user's GPS location history.
    @return:
    """

    gps_logs_form = GetDeliveryUserGpsLogsForm()
    if gps_logs_form.validate_on_submit():
        branch_codes = gps_logs_form.branch_codes.data
        delivery_user_id = None if gps_logs_form.delivery_user_id.data == "" else gps_logs_form.delivery_user_id.data
        state_codes = gps_logs_form.state_codes.data
        city_codes = gps_logs_form.city_codes.data
        user_id = request.headers.get('user-id')
        logs = []
        day_interval = gps_logs_form.day_interval.data
        interval_start_date = None
        if day_interval is not None:
            interval_start_date = (datetime.today() - timedelta(day_interval)).strftime("%Y-%m-%d %H:%M:%S")
        try:
            if not branch_codes:
                # Getting the branches associated with the user.
                store_user_branches = store_controller_queries.get_store_user_branches(user_id, state_codes, city_codes)
            else:
                # Branch codes are given.
                store_user_branches = branch_codes
            # Edited by MMM
            delivery_users = []
            if delivery_user_id:
                delivery_users.append(delivery_user_id)
            else:
                # Edited by MMM
                # No particular delivery users are given. so take this from store user branches.
                selected_delivery_users = db.session.query(DeliveryUser.DUserId).distinct(DeliveryUser.DUserId).join(
                    DeliveryUserBranch,
                    DeliveryUser.DUserId == DeliveryUserBranch.DUserId).filter(
                    DeliveryUser.IsDeleted == 0, DeliveryUserBranch.BranchCode.in_(store_user_branches)).all()
                delivery_users = [delivery_user.DUserId for delivery_user in selected_delivery_users]

            if interval_start_date is not None:
                # Here, an day interval is specified. So select the details from the start date and current date.
                interval_condition_check = and_(DeliveryUserGPSLog.RecordCreatedDate < get_current_date(),
                                                DeliveryUserGPSLog.RecordCreatedDate > interval_start_date)
            else:
                # No interval day is specified.
                interval_condition_check = DeliveryUserGPSLog.RecordCreatedDate < get_current_date()

            for delivery_user in delivery_users:
                # Getting the latest log id of a delivery user.
                latest_log_id = db.session.query(DeliveryUserGPSLog.Id).filter(
                    DeliveryUserGPSLog.DUserId == delivery_user).order_by(
                    DeliveryUserGPSLog.RecordCreatedDate.desc()).first()
                if latest_log_id is not None:
                    # Getting the log details - including the name and lat & long co-ordinates.
                    log = db.session.query(DeliveryUser.DUserId,
                                           DeliveryUser.UserName,
                                           DeliveryUserGPSLog.Lat,
                                           DeliveryUserGPSLog.Long,
                                           DeliveryUserGPSLog.RecordCreatedDate).join(DeliveryUser,
                                                                                      DeliveryUserGPSLog.DUserId == DeliveryUser.DUserId).filter(
                        DeliveryUserGPSLog.Id == latest_log_id.Id, interval_condition_check).one_or_none()
                    logs.append(log)
        except Exception as e:
            error_logger(f'Route: {request.path}').error(e)
        if logs:
            final_data = generate_final_data('DATA_FOUND')
            logs = SerializeSQLAResult(logs).serialize(full_date_fields=['RecordCreatedDate'])
            print(logs)
            for log in logs:
                # Getting the delivery user branches.
                branch_codes = delivery_controller_queries.get_delivery_user_branches(log['DUserId'])
                log['BranchCodes'] = branch_codes
            final_data['result'] = logs
        else:
            final_data = generate_final_data('DATA_NOT_FOUND')
    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(gps_logs_form.errors)
    return final_data


@store_console_blueprint.route('/get_collected_amounts', methods=["POST"])
@authenticate('store_user')
def get_collected_amounts():
    """
    API for getting the amount collected by delivery user.
    @return:
    """
    collected_form = GetCollectedAmounts()

    if collected_form.validate_on_submit():
        delivery_user_id = collected_form.delivery_user_id.data
        branch_codes = collected_form.branch_codes.data
        date = collected_form.date.data
        user_id = request.headers.get('user-id')
        formatted_date = None
        tomorrow = None
        if date:
            date_obj = datetime.strptime(date, "%d-%m-%Y")
            # From the date object, convert the date to YYYY-MM-DD format.
            formatted_date = date_obj.strftime("%Y-%m-%d 00:00:00")

            tomorrow = (date_obj + timedelta(1)).strftime("%Y-%m-%d 00:00:00")

        collection_details = []
        try:
            if not branch_codes:
                # Getting the branches associated with the user.
                store_user_branches = store_controller_queries.get_store_user_branches(user_id)
            else:
                store_user_branches = branch_codes

            # If CouponCode is NULL, select "NA", otherwise select CouponCode.
            select_coupon_code = case([(TransactionPaymentInfo.CouponCode == None, "NA"), ],
                                      else_=TransactionPaymentInfo.CouponCode).label("CouponCode")

            # If CardTransactionId is NULL, select "NA", otherwise select CardTransactionId.
            select_card_transaction_id = case([(TransactionPaymentInfo.CardTransactionId == None, "NA"), ],
                                              else_=TransactionPaymentInfo.CardTransactionId).label("CardTransactionId")

            # Getting the collection details.
            collection_details = db.session.query(Delivery.EGRN, Delivery.DUserId, TransactionPaymentInfo.PaymentMode,
                                                  select_card_transaction_id,
                                                  select_coupon_code,
                                                  TransactionPaymentInfo.PaymentAmount).join(TransactionInfo,
                                                                                             Delivery.EGRN == TransactionInfo.EGRNNo).join(
                TransactionPaymentInfo,
                and_(
                    TransactionInfo.TransactionId == TransactionPaymentInfo.TransactionId,
                    TransactionInfo.PaymentId == TransactionPaymentInfo.PaymentId)).filter(
                Delivery.DUserId == delivery_user_id, Delivery.BranchCode.in_(store_user_branches),
                TransactionPaymentInfo.InvoiceNo != None,
                and_(formatted_date < Delivery.RecordCreatedDate, tomorrow > Delivery.RecordCreatedDate)).all()

        except Exception as e:
            error_logger(f'Route: {request.path}').error(e)

        if collection_details:
            final_data = generate_final_data('DATA_FOUND')
            final_data['result'] = SerializeSQLAResult(collection_details).serialize()
        else:
            final_data = generate_final_data('DATA_NOT_FOUND')

    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(collected_form.errors)
    return final_data


@store_console_blueprint.route('/get_egrns_for_partial_delivery', methods=["POST"])
@authenticate('store_user')
def get_egrns_for_partial_delivery():
    """
    API for getting the orders that have at least one ready for delivery garments and not all.
    @return:
    """
    partial_delivery_form = GetEGRNsForPartialDeliveryForm()
    if partial_delivery_form.validate_on_submit():
        branch_codes = partial_delivery_form.branch_codes.data
        user_id = request.headers.get('user-id')
        orders_for_partial_delivery = []
        try:
            # Based on the store user, orders for delivery will be returned. If the store user is the admin,
            # All the orders will be returned (If those has at least one ready for delivery garment).
            # Else, only related branch's
            # ready for delivery will be returned.
            store_user = db.session.query(StoreUser).filter(StoreUser.SUserId == user_id).one_or_none()

            if store_user is not None:
                # Store user found.
                if not branch_codes:
                    # Getting the branches associated with the user.
                    store_user_branches = store_controller_queries.get_store_user_branches(user_id)
                else:
                    # Branch codes are given.
                    store_user_branches = branch_codes

                # If a DisplayName found for a branch, then select DisplayName as the BranchName.
                select_branch_name = case(
                    [(or_(Branch.DisplayName == None, Branch.DisplayName == ''), Branch.BranchName), ],
                    else_=Branch.DisplayName).label("BranchName")

                branch_codes_str = "','".join(map(str, store_user_branches))
                branch_codes_str = f"'{branch_codes_str}'"

                # Preparing the query.
                sql = text(f"""select distinct(Orders.OrderId), Orders.EGRN, Orders.BranchCode, Branches.DisplayName,
                Customers.CustomerId,
                Customers.CustomerCode,
                Customers.CustomerName,
                Customers.MobileNo,
                oI.TotalGarments
                ,count(OrderGarments.tagid) as readyfordelivery
        
                from Orders join OrderGarments on Orders.OrderId=OrderGarments.OrderId
                
                join {SERVER_DB}..OrderInfo OI on oi.EGRNNO=orders.EGRN
                
                left outer join DeliveryRequests on Orders.OrderId = DeliveryRequests.OrderId
                
                join Customers on Orders.CustomerId = Customers.CustomerId
                
                join Branches on Orders.BranchCode = Branches.BranchCode
                
                where
                
                OrderGarments.GarmentStatusId in (10) and
                Orders.BranchCode in ({branch_codes_str}) and
                Orders.IsDeleted =0 and  
                DeliveryRequests.DeliveryRequestId is NULL
                
                 Group by
                
                Orders.OrderId, Orders.EGRN, Orders.BranchCode, Branches.DisplayName,
                Customers.CustomerId,
                Customers.CustomerCode,
                Customers.CustomerName,               
                Customers.MobileNo,                
                oI.TotalGarments
                Having oI.TotalGarments<>count(OrderGarments.tagid)""")

                # Executing the query.
                orders_for_partial_delivery = db.engine.execute(sql).fetchall()

        except Exception as e:
            error_logger(f'Route: {request.path}').error(e)

        if len(orders_for_partial_delivery) > 0:
            final_data = generate_final_data('DATA_FOUND')
            final_data['result'] = SerializeSQLAResult(orders_for_partial_delivery).serialize()
        else:
            final_data = generate_final_data('DATA_NOT_FOUND')
    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(partial_delivery_form.errors)
    return final_data


@store_console_blueprint.route('/get_garments_for_partial_delivery', methods=["POST"])
@authenticate('store_user')
def get_garments_for_partial_delivery():
    """
    Getting the Garment details from a order id (Must have at least one ready for delivery garments.
    (Not all)
    @return:
    """
    garments_for_partial_delivery_form = GetGarmentsForPartialDeliveryForm()
    if garments_for_partial_delivery_form.validate_on_submit():
        order_id = garments_for_partial_delivery_form.order_id.data
        order_garments = []
        try:
            # If TagId is NOT present in the OrderGarments table, return "NA", else return the value.
            select_tag_id = case([(OrderGarment.TagId == None, "NA"), ],
                                 else_=OrderGarment.TagId).label("TagId")

            # If GarmentBrand is NOT present in the OrderGarments table, return "NA", else return the value.
            select_garment_brand = case([(OrderGarment.GarmentBrand == None, "NA"), ],
                                        else_=OrderGarment.GarmentBrand).label("GarmentBrand")

            # If GarmentColour is NOT present in the OrderGarments table, return "NA", else return the value.
            select_garment_colour = case([(OrderGarment.GarmentColour == None, "NA"), ],
                                         else_=OrderGarment.GarmentColour).label("GarmentColour")

            # If GarmentSize is NOT present in the OrderGarments table, return "NA", else return the value.
            select_garment_size = case([(OrderGarment.GarmentSize == None, "NA"), ],
                                       else_=OrderGarment.GarmentSize).label("GarmentSize")

            # Only ready for delivery garments needs to be allowed for partial delivery.
            # Those garments can be selected by checkbox. So based on the order garment status,
            # determining whether the order garment needs to be enabled/disabled for the checkbox.
            checkbox_flag = case(
                [(OrderGarment.GarmentStatusId == 10, literal(1).label("Checkbox")), ],
                else_=literal(0).label("Checkbox")).label("Checkbox")

            # Getting the order garments from order id.
            order_garments = db.session.query(OrderGarment.OrderGarmentId, OrderGarment.POSOrderGarmentId,
                                              select_tag_id, select_garment_brand, select_garment_colour,
                                              select_garment_size, GarmentStatusCode.StatusCode, checkbox_flag,
                                              Garment.GarmentName, ServiceType.ServiceTypeName,
                                              ServiceType.ServiceDescription,
                                              ServiceTat.ServiceTatName
                                              ).join(
                Garment, OrderGarment.GarmentId == Garment.GarmentId).join(ServiceType,
                                                                           OrderGarment.ServiceTypeId == ServiceType.ServiceTypeId).join(
                ServiceTat, OrderGarment.ServiceTatId == ServiceTat.ServiceTatId).join(
                GarmentStatusCode,
                OrderGarment.GarmentStatusId == GarmentStatusCode.GarmentStatusId).filter(
                OrderGarment.OrderId == order_id,
                OrderGarment.IsDeleted == 0).all()

        except Exception as e:
            error_logger(f'Route: {request.path}').error(e)

        if order_garments:
            final_data = generate_final_data('DATA_FOUND')
            final_data['result'] = SerializeSQLAResult(order_garments).serialize()
        else:
            final_data = generate_final_data('DATA_NOT_FOUND')

    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(garments_for_partial_delivery_form.errors)

    return final_data


@store_console_blueprint.route('/create_delivery_request', methods=["POST"])
@authenticate('store_user')
def create_delivery_request():
    """
    API for creating a delivery request by passing the ready for delivery garments.
    @return:
    """
    create_delivery_request_form = CreateDeliveryRequest()
    user_id = request.headers.get('user-id')
    if create_delivery_request_form.validate_on_submit():
        order_garments = create_delivery_request_form.order_garments.data
        order_id = create_delivery_request_form.order_id.data
        address_id = create_delivery_request_form.address_id.data
        time_slot_id = None if create_delivery_request_form.time_slot_id.data == '' else create_delivery_request_form.time_slot_id.data
        delivery_user_id = None if create_delivery_request_form.delivery_user_id.data == '' else create_delivery_request_form.delivery_user_id.data
        delivery_date = None if create_delivery_request_form.delivery_date.data == '' else create_delivery_request_form.delivery_date.data
        #  Edited by MMM
        # Check if delivery user is active
        if db.session.query(DeliveryUser).filter(DeliveryUser.IsActive == 1,
                                                 DeliveryUser.DUserId == delivery_user_id).one_or_none():
            #  Edited by MMM
            if delivery_date is not None:
                delivery_date_obj = datetime.strptime(delivery_date, "%d-%m-%Y")
                # From the date object, convert the date to YYYY-MM-DD format.
                formatted_delivery_date = delivery_date_obj.strftime("%Y-%m-%d %H:%M:%S")
            else:
                # No delivery date is explicitly given. So today is the delivery date.
                formatted_delivery_date = get_today()

            garments_added = False
            delivery_request_created = False
            is_partial = False
            error_msg = ''
            try:
                # Getting the order details from the DB.
                order_details = db.session.query(Order).filter(Order.OrderId == order_id,
                                                               Order.IsDeleted == 0).one_or_none()

                if order_details is not None:

                    # Getting the total garments count for that order.
                    garments_count = db.session.query(func.count(OrderGarment.OrderGarmentId)).filter(
                        OrderGarment.OrderId == order_id, OrderGarment.IsDeleted == 0).scalar()

                    # Selecting the TimeSlotId - If the pickup is rescheduled, select the time slot id
                    # from the PickupReschedules table.
                    # Otherwise, select it from the PickupRequests table.
                    select_time_slot_id = case(
                        [(PickupReschedule.PickupTimeSlotId == None, PickupRequest.PickupTimeSlotId), ],
                        else_=PickupReschedule.PickupTimeSlotId).label("PickupTimeSlotId")

                    # If the pickup is rescheduled, then select reschedule's time slot from, else time slot from of
                    # the pickup request.
                    select_time_slot_from = case(
                        [(PickupReschedule.TimeSlotFrom == None, PickupRequest.TimeSlotFrom), ],
                        else_=PickupReschedule.TimeSlotFrom).label("TimeSlotFrom")

                    # If the pickup is rescheduled, then select reschedule's time slot to, else time slot to of
                    # the pickup request.
                    select_time_slot_to = case([(PickupReschedule.TimeSlotTo == None, PickupRequest.TimeSlotTo), ],
                                               else_=PickupReschedule.TimeSlotTo).label("TimeSlotTo")

                    if time_slot_id is None:
                        # No time slot is given. So select the time slot fromt the orders itself.
                        time_slot_details = db.session.query(Order.OrderId, select_time_slot_id, select_time_slot_from,
                                                             select_time_slot_to).join(PickupRequest,
                                                                                       Order.PickupRequestId == PickupRequest.PickupRequestId).outerjoin(
                            PickupReschedule, PickupRequest.PickupRequestId == PickupReschedule.PickupRequestId).filter(
                            Order.OrderId == order_id, Order.IsDeleted == 0, PickupRequest.IsCancelled == 0,
                            or_(PickupReschedule.IsDeleted == 0, PickupReschedule.IsDeleted == None)).one_or_none()
                    else:
                        # TimeSlot is given.
                        time_slot_details = db.session.query(PickupTimeSlot.TimeSlotFrom, PickupTimeSlot.TimeSlotTo,
                                                             PickupTimeSlot.PickupTimeSlotId).filter(
                            PickupTimeSlot.PickupTimeSlotId == time_slot_id).one_or_none()

                    if time_slot_details is not None:
                        delivery_time_slot_id = time_slot_details.PickupTimeSlotId
                        time_slot_from = time_slot_details.TimeSlotFrom
                        time_slot_to = time_slot_details.TimeSlotTo
                    else:
                        delivery_time_slot_id = None
                        time_slot_from = None
                        time_slot_to = None

                    if garments_count > len(order_garments):
                        # Total garments in the order and garments selected for the delivery
                        # are not equal. It should be less than order garments.
                        is_partial = True

                    if is_partial:
                        # Only partial garments are selected for delivery request creation. So go ahead.
                        # Checking whether a delivery request found for this order or not (not delivered).
                        existing_delivery_request = db.session.query(DeliveryRequest).outerjoin(Delivery,
                                                                                                DeliveryRequest.DeliveryRequestId == Delivery.DeliveryRequestId).filter(
                            DeliveryRequest.OrderId == order_id, DeliveryRequest.IsDeleted == 0,
                            Delivery.DeliveryId == None).one_or_none()

                        if existing_delivery_request is not None:
                            # An existing open delivery request is present in the table.
                            # Delete the request and delete the order garments inside it.
                            existing_delivery_request.IsDeleted = 1
                            existing_delivery_request.RecordLastUpdatedDate = get_current_date()
                            existing_delivery_request.CancelledStoreUser = user_id
                            existing_delivery_request.CancelledDate = get_current_date()
                            db.session.commit()

                            # Deleting the order garments under this delivery request.
                            delivery_garments = db.session.query(DeliveryGarment).filter(
                                DeliveryGarment.OrderId == order_id,
                                DeliveryGarment.DeliveryRequestId == existing_delivery_request.DeliveryRequestId,
                                DeliveryGarment.IsDeleted == 0).all()

                            for delivery_garment in delivery_garments:
                                # Looping over the delivery garments and marking them as deleted.
                                delivery_garment.IsDeleted = 1
                                delivery_garment.RecordLastUpdatedDate = get_current_date()
                                db.session.commit()
                        else:
                            # No existing delivery request is found for this order.
                            pass

                        if delivery_date is not None:
                            # If the delivery_date is explicitly given, check if the given date is a
                            # holiday for the branch or not.
                            holiday = delivery_controller_queries.check_branch_holiday(delivery_date,
                                                                                       order_details.BranchCode)
                        else:
                            # No delivery date is given. Today will be a working day so, no need for checking holiday.
                            holiday = False

                        if not holiday:
                            # Creating a new delivery request.
                            new_delivery_request = DeliveryRequest(
                                CustomerId=order_details.CustomerId,
                                BranchCode=order_details.BranchCode,
                                DeliveryDate=formatted_delivery_date,
                                DeliveryTimeSlotId=delivery_time_slot_id,
                                TimeSlotFrom=time_slot_from,
                                TimeSlotTo=time_slot_to,
                                CustAddressId=address_id,
                                BookingId=order_details.BookingId,
                                OrderId=order_details.OrderId,
                                IsPartial=is_partial,
                                DUserId=delivery_user_id,
                                CreatedStoreUser=user_id,
                                RecordCreatedDate=get_current_date()
                            )
                            db.session.add(new_delivery_request)
                            db.session.commit()
                            # A delivery request for this order has been successfully created.
                            delivery_request_created = True

                            # After creating the delivery request, insert the selected garments for
                            # delivery.
                            for order_garment_id in order_garments:
                                # Looping over the selected garments and select the essential
                                # details.
                                garment_details = db.session.query(OrderGarment.POSOrderGarmentId,
                                                                   OrderGarment.OrderId).filter(
                                    OrderGarment.OrderGarmentId == order_garment_id,
                                    OrderGarment.IsDeleted == 0).one_or_none()

                                if garment_details is not None:
                                    # Garment details are found. Insert the data into DeliveryGarments table.
                                    new_delivery_garment = DeliveryGarment(
                                        OrderGarmentId=order_garment_id,
                                        POSOrderGarmentId=garment_details.POSOrderGarmentId,
                                        OrderId=order_id,
                                        DeliveryRequestId=new_delivery_request.DeliveryRequestId,
                                        RecordCreatedDate=get_current_date(),
                                        RecordLastUpdatedDate=get_current_date()
                                    )
                                    db.session.add(new_delivery_garment)
                                    db.session.commit()
                                    # Garments have also been added.
                                    garments_added = True

                        else:
                            error_msg = 'Please choose another date. Given date is a branch holiday.'

                    else:
                        error_msg = 'This is not a partial delivery.'

                else:
                    error_msg = 'No order details are found.'

            except Exception as e:
                error_logger(f'Route: {request.path}').error(e)

            if garments_added and delivery_request_created:
                # Invoke push notification
                send_push_notification_test(delivery_user_id, 'DELIVERY', None, "JFSLSTORE", user_id)

                final_data = generate_final_data('DATA_SAVED')
            else:
                if error_msg:
                    final_data = generate_final_data('CUSTOM_FAILED', error_msg)
                else:
                    final_data = generate_final_data('DATA_NOT_SAVED')
        else:
            final_data = generate_final_data('CUSTOM_FAILED', 'Delivery user is inactive')
    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(create_delivery_request_form.errors)
    return final_data


@store_console_blueprint.route('/get_attendance_logs', methods=["POST"])
@authenticate('store_user')
def get_attendance_logs():
    """
    API for getting the attendance logs of a delivery user.
    @return:
    """
    attendance_form = GetAttendanceLogsForm()
    if attendance_form.validate_on_submit():
        delivery_user_id = attendance_form.delivery_user_id.data
        start_date = attendance_form.start_date.data
        end_date = attendance_form.end_date.data
        error_msg = ''
        attendance_logs = []
        # The difference between the dates should be less than two months.
        if day_difference(start_date, end_date) <= 60:
            # Convert string date to datetime object.
            start_date_obj = datetime.strptime(start_date, "%d-%m-%Y")
            # From the date object, convert the date to YYYY-MM-DD format.
            formatted_start_date_obj = start_date_obj.strftime("%Y-%m-%d %H:%M:%S")

            # Convert string date to datetime object.
            end_date_obj = datetime.strptime(end_date, "%d-%m-%Y")
            # From the date object, convert the date to YYYY-MM-DD format.
            formatted_end_date_obj = end_date_obj.strftime("%Y-%m-%d %H:%M:%S")
            try:
                attendance_logs = db.session.query(DeliveryUserAttendance.Date, DeliveryUserAttendance.ClockInTime,
                                                   DeliveryUserAttendance.ClockOutTime,
                                                   DeliveryUserAttendance.ClockInLat,
                                                   DeliveryUserAttendance.ClockInLong,
                                                   DeliveryUserAttendance.ClockOutLat,
                                                   DeliveryUserAttendance.ClockOutLong
                                                   ).filter(DeliveryUserAttendance.DUserId == delivery_user_id,
                                                            DeliveryUserAttendance
                                                            .IsDeleted == 0,
                                                            and_(DeliveryUserAttendance.Date > formatted_start_date_obj,
                                                                 DeliveryUserAttendance.Date < formatted_end_date_obj)).all()
            except Exception as e:
                error_logger(f'Route: {request.path}').error(e)
        else:
            error_msg = 'Please choose the dates within two months apart.'

        if attendance_logs:
            final_data = generate_final_data('DATA_FOUND')
            final_data['result'] = SerializeSQLAResult(attendance_logs).serialize()
        else:
            if error_msg:
                final_data = generate_final_data('CUSTOM_FAILED', error_msg)
            else:
                final_data = generate_final_data('DATA_NOT_FOUND')
    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(attendance_form.errors)

    return final_data


@store_console_blueprint.route('/enable_store_user', methods=["PUT"])
@authenticate('store_user')
def enable_store_user():
    """
    API for enabling the in active store user.
    @return:
    """
    form = EnableStoreUserForm()
    if form.validate_on_submit():
        store_user_id = form.store_user_id.data
        enabled = False
        try:
            # Getting the store user details.
            store_user = db.session.query(StoreUser).filter(StoreUser.SUserId == store_user_id,
                                                            StoreUser.IsDeleted == 1).one_or_none()

            if store_user is not None:
                # Store user details found. So enable the store user.
                store_user.IsActive = 1
                store_user.IsDeleted = 0
                db.session.commit()
                enabled = True
        except Exception as e:
            error_logger(f'Route: {request.path}').error(e)

        if enabled:
            final_data = generate_final_data('DATA_SAVED')
        else:
            final_data = generate_final_data('DATA_SAVE_FAILED')
    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(form.errors)

    return final_data


@store_console_blueprint.route('/enable_delivery_user', methods=["PUT"])
@authenticate('store_user')
def enable_delivery_user():
    """
    API for enabling a inactive delivery user.
    @return:
    """
    form = EnableDeliveryUserForm()
    if form.validate_on_submit():
        delivery_user_id = form.delivery_user_id.data
        enabled = False
        try:
            # Getting the delivery user details.
            delivery_user = db.session.query(DeliveryUser).filter(DeliveryUser.DUserId == delivery_user_id,
                                                                  DeliveryUser.IsDeleted == 1).one_or_none()

            if delivery_user is not None:
                # Delivery user details found. So enable the delivery user.
                delivery_user.IsActive = 1
                delivery_user.IsDeleted = 0
                db.session.commit()
                enabled = True
        except Exception as e:
            error_logger(f'Route: {request.path}').error(e)

        if enabled:
            final_data = generate_final_data('DATA_SAVED')
        else:
            final_data = generate_final_data('DATA_SAVE_FAILED')
    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(form.errors)

    return final_data


@store_console_blueprint.route('/get_walk_in_orders', methods=["POST"])
@authenticate('store_user')
def get_walk_in_orders():
    """
    API for getting the walk in orders.
    @return:
    """
    form = GetWalkInOrdersForm()
    user_id = request.headers.get('user-id')
    if form.validate_on_submit():
        branch_codes = form.branch_codes.data
        report = form.report.data
        walk_in_orders = []
        try:
            if not branch_codes:
                # Getting the branches associated with the user.
                # Edited by MMM
                store_user_branches = store_controller_queries.get_store_user_branches(user_id, None, None, True)
            else:
                # Branch codes are given.
                store_user_branches = branch_codes

            # Select AddressLine2 if not NULL, else select NA.
            select_address_line_2 = case([(CustomerAddres.AddressLine2 == None, "NA"), ],
                                         else_=CustomerAddres.AddressLine2).label("AddressLine2")

            # Select AddressLine3 if not NULL, else select NA.
            select_address_line_3 = case([(CustomerAddres.AddressLine3 == None, "NA"), ],
                                         else_=CustomerAddres.AddressLine3).label("AddressLine3")

            # If the delivery is rescheduled, then select RescheduledDate, else select DeliveryDate.
            select_delivery_date = case([(DeliveryReschedule.RescheduledDate == None, DeliveryRequest.DeliveryDate), ],
                                        else_=DeliveryReschedule.RescheduledDate).label("DeliveryDate")

            # If a DisplayName found for a branch, then select DisplayName as the BranchName.
            select_branch_name = case(
                [(or_(Branch.DisplayName == None, Branch.DisplayName == ''), Branch.BranchName), ],
                else_=Branch.DisplayName).label("BranchName")

            walk_in_orders = db.session.query(DeliveryRequest.DeliveryRequestId, Order.OrderId, Order.BranchCode,
                                              select_branch_name,
                                              select_delivery_date,
                                              CustomerAddres.AddressName, CustomerAddres.AddressLine1,
                                              select_address_line_2, select_address_line_3, Order.EGRN,
                                              Customer.CustomerName, Customer.MobileNo,
                                              DeliveryRequest.CustomerPreferredDate,
                                              DeliveryRequest.CustomerPreferredTimeSlot
                                              ).select_from(DeliveryRequest).join(
                Order,
                DeliveryRequest.OrderId == Order.OrderId).join(
                CustomerAddres, DeliveryRequest.CustAddressId == CustomerAddres.CustAddressId).join(Customer,
                                                                                                    Order.CustomerId == Customer.CustomerId).outerjoin(
                DeliveryReschedule,
                DeliveryRequest.DeliveryRequestId == DeliveryReschedule.DeliveryRequestId).outerjoin(
                Delivery,
                DeliveryRequest.DeliveryRequestId == Delivery.DeliveryRequestId).join(Branch,
                                                                                      Order.BranchCode == Branch.BranchCode).filter(
                DeliveryRequest.IsDeleted == 0,
                DeliveryRequest.WalkIn == 1,
                Order.PickupRequestId == None,
                Order.BranchCode.in_(store_user_branches), Order.IsDeleted == 0,
                or_(DeliveryReschedule.IsDeleted == 0,
                    DeliveryReschedule.IsDeleted == None),
                Delivery.DeliveryId == None).all()

            # Serializing for looping and adding CustomerPreferredDate and IsPreferredDateAfter flag
            walk_in_orders = SerializeSQLAResult(walk_in_orders).serialize()
            # Looping serialized Deliveries
            for delivery_id in walk_in_orders:

                if delivery_id['CustomerPreferredDate'] is not None:
                    # If the delivery have customer preferred date add it ti the raw
                    cus_preferred_date = delivery_id['CustomerPreferredDate']
                    # Formatting today for comparing
                    formatted_today = datetime.today().strftime("%d-%m-%Y")

                    if cus_preferred_date > formatted_today:
                        # If customer preferred day is bigger than today make IsPreferredDateAfter True
                        delivery_id['IsPreferredDateAfter'] = True
                    else:
                        delivery_id['IsPreferredDateAfter'] = False

                else:
                    # Send IsPreferredDateAfter, CustomerPreferredDate as None and False
                    delivery_id['IsPreferredDateAfter'] = False
                    delivery_id['CustomerPreferredDate'] = None

        except Exception as e:
            error_logger(f'Route: {request.path}').error(e)

        if walk_in_orders:
            final_data = generate_final_data('DATA_FOUND')

            if report:
                # Report flag is included in the request. So generate the file and send the file back.
                report_link = GenerateReport(walk_in_orders, 'walkin').generate().get()
                if report_link is not None:
                    final_data['result'] = report_link
                else:
                    # Failed to generate the file.
                    final_data = generate_final_data('FILE_NOT_FOUND')
            else:
                final_data['result'] = walk_in_orders
        else:
            final_data = generate_final_data('DATA_NOT_FOUND')
    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(form.errors)

    return final_data

# @store_console_blueprint.route('/get_order_details', methods=["POST"])
# # @authenticate('store_user')
# def get_order_details():
#     """
#     API for getting the order details.
#     @return:
#     """
#     form = GetOrderDetailsForm()
#     log_data = {
#         'form': form.data,

#     }
#     info_logger(f'Route: {request.path}').info(json.dumps(log_data))
#     if form.validate_on_submit():
#         order_id = form.order_id.data
#         delivery_request_id = form.delivery_request_id.data
#         activity_type = form.activity_type.data
#         order_details = None
#         order_garments = []
#         total_garments = 0
#         payment_status = 'NA'
#         payment_details = []
#         pickup_or_delivery = None
#         delivery_charge = 0
#         apply_delivery_charge = False
#         TotalAmount = 0
#         order_garment = []
#         PaymentStatus = ""
#         try:
#             # Selecting the order category. i.e. Walk In or D2D.
#             select_order_category = case([(Order.PickupRequestId == None, "Walk-In"), ],
#                                          else_="D2D").label("OrderCategory")

#             # If the BookingId is NOT present in the PickupRequest table, return NA, else return the 
# 
# 
# 
# 
# 
# value.
#             select_booking_id = case([(Order.BookingId == None, "NA"), ],
#                                      else_=Order.BookingId).label("BookingId")

#             # If the DiscountCode is present in the PickupRequest or the Orders table, select DiscountCode.
#             select_discount_code = case([

#                 (PickupRequest.DiscountCode != None, PickupRequest.DiscountCode),
#                 (Order.DiscountCode != None, Order.DiscountCode),
#             ], else_="NA").label("DiscountCode")

#             select_delivery_charge = case([
#                 (Order.DeliveryChargeFlag == None, "NA"),
#                 (Order.DeliveryChargeFlag == 0, "NO"),
#                 (Order.DeliveryChargeFlag == 1, "YES")
#             ]).label("DeliveryCharge")

#             # Getting the order details from the DB.
#             order_details = db.session.query(Order.OrderId, Order.EGRN, select_booking_id, select_order_category,
#                                              Order.BasicAmount, Order.Discount,
#                                              Order.ServiceTaxAmount,
#                                              Customer.CustomerName,
#                                              Customer.MobileNo, Customer.EmailId, select_discount_code,
#                                              select_delivery_charge).join(Customer,
#                                                                           Order.CustomerId == Customer.CustomerId).outerjoin(
#                 PickupRequest, Order.PickupRequestId == PickupRequest.PickupRequestId).filter(
#                 Order.OrderId == order_id, Order.IsDeleted == 0).one_or_none()

#             if order_details is not None:

#                 # Getting the total number of garments in that order.
#                 # total_garments = db.session.query(func.count(OrderGarment.OrderGarmentId)).filter(
#                 #     OrderGarment.OrderId == order_id, OrderGarment.IsDeleted == 0).scalar()

#                 if activity_type == 'Pickup':
#                     total_garments = db.session.query(func.count(OrderGarment.OrderGarmentId)).filter(
#                         OrderGarment.OrderId == order_id, OrderGarment.IsDeleted == 0).scalar()

#                 else:
#                     total_garments = db.session.query(func.count(DeliveryGarment.OrderGarmentId)).filter(
#                         DeliveryGarment.DeliveryRequestId == delivery_request_id,
#                         DeliveryGarment.IsDeleted == 0).scalar()

#                 # Getting the garment details from the OrderGarment table.
#                 # Getting the order garments from order id.
#                 # If TagId is NOT present in the OrderGarments table, return "NA", else return the value.
#                 select_tag_id = case([(OrderGarment.TagId == None, "NA"), ],
#                                      else_=OrderGarment.TagId).label("TagId")

#                 # If GarmentBrand is NOT present in the OrderGarments table, return "NA", else return the value.
#                 select_garment_brand = case([(OrderGarment.GarmentBrand == None, "NA"), ],
#                                             else_=OrderGarment.GarmentBrand).label("GarmentBrand")

#                 # If GarmentColour is NOT present in the OrderGarments table, return "NA", else return the value.
#                 select_garment_colour = case([(OrderGarment.GarmentColour == None, "NA"), ],
#                                              else_=OrderGarment.GarmentColour).label("GarmentColour")

#                 # If GarmentSize is NOT present in the OrderGarments table, return "NA", else return the value.
#                 select_garment_size = case([(OrderGarment.GarmentSize == None, "NA"), ],
#                                            else_=OrderGarment.GarmentSize).label("GarmentSize")

#                 # getting the pos_order_garments_id from ordergarment table or delivery garmet table based on pickup or delivery

#                 if activity_type == 'Pickup':
#                     # log_data = {
#                     # 'pos_order_garments_id11':activity_type

#                     # }
#                     # info_logger(f'Route: {request.path}').info(json.dumps(log_data))
#                     pos_order_garments_id = [
#                         garment.POSOrderGarmentId for garment in db.session.query(OrderGarment.POSOrderGarmentId)
#                         .filter(OrderGarment.OrderId == order_id, OrderGarment.IsDeleted == 0).all()
#                     ]

#                 else:
#                     pos_order_garments_id = [
#                         garment.POSOrderGarmentId for garment in db.session.query(DeliveryGarment.POSOrderGarmentId)
#                         .filter(DeliveryGarment.DeliveryRequestId == delivery_request_id,
#                                 DeliveryGarment.IsDeleted == 0).all()
#                     ]
#                     # pos_order_garments_id = db.session.query(DeliveryGarment.POSOrderGarmentId).filter(
#                     #     DeliveryGarment.DeliveryRequestId == delivery_request_id,
#                     #             DeliveryGarment.IsDeleted == 0).first()

                    
#                 # pos_order_garments_id =pos_order_garments_id[0]
#                 # pos_order_garments_id =str(pos_order_garments_id)
#                 log_data = {
#                         'pos_order_garments_id11': pos_order_garments_id,

#                     }
#                 info_logger(f'Route: {request.path}').info(json.dumps(log_data))


#                 order_garments = db.session.query(OrderGarment.OrderGarmentId, OrderGarment.POSOrderGarmentId,
#                                                   select_tag_id, select_garment_brand, select_garment_colour,
#                                                   select_garment_size, GarmentStatusCode.StatusCode,
#                                                   Garment.GarmentName, ServiceType.ServiceTypeName,
#                                                   ServiceType.ServiceDescription,
#                                                   ServiceTat.ServiceTatName
#                                                   ).join(
#                     Garment, OrderGarment.GarmentId == Garment.GarmentId).join(ServiceType,
#                                                                                OrderGarment.ServiceTypeId == ServiceType.ServiceTypeId).join(
#                     ServiceTat, OrderGarment.ServiceTatId == ServiceTat.ServiceTatId).join(
#                     GarmentStatusCode,
#                     OrderGarment.GarmentStatusId == GarmentStatusCode.GarmentStatusId).filter(
#                     OrderGarment.POSOrderGarmentId.in_(pos_order_garments_id),
#                     OrderGarment.IsDeleted == 0).all()
#                 log_data = {
#                     'order_garments': order_garments,

#                 }
#                 info_logger(f'Route: {request.path}').info(json.dumps(log_data))

#                 order_garments = SerializeSQLAResult(order_garments).serialize()

#                 if pos_order_garments_id:
#                     basic_amounts = db.session.query(
#                         OrderGarment.BasicAmount
#                     ).filter(
#                         OrderGarment.POSOrderGarmentId.in_(pos_order_garments_id),
#                         OrderGarment.IsDeleted == 0
#                     ).all()

#                     # Extract the BasicAmount values into a list
#                     basic_amounts_list = [float(amount[0]) for amount in basic_amounts]
#                     # Calculate the total
#                     TotalBasicAmount = sum(basic_amounts_list)

#                     ServiceTaxAmount = db.session.query(OrderGarment.ServiceTaxAmount).filter(
#                         OrderGarment.POSOrderGarmentId.in_(pos_order_garments_id),
#                         OrderGarment.IsDeleted == 0).all()

#                     service_tax_amount_list = [float(amount[0]) for amount in ServiceTaxAmount]

#                     TotalServiceTaxAmount = sum(service_tax_amount_list)

#                     Discount = db.session.query(OrderGarment.Discount).filter(
#                         OrderGarment.POSOrderGarmentId.in_(pos_order_garments_id),
#                         OrderGarment.IsDeleted == 0).all()

#                     discount_list = [float(amount[0]) for amount in Discount]

#                     TotalDisCount = sum(discount_list)

#                     # Log the results
#                     log_data = {
#                         'TotalBasicAmount': TotalBasicAmount,
#                         'BasicAmounts': basic_amounts_list,
#                         'service_tax_amount_list': service_tax_amount_list,
#                         'discount_list': discount_list,
#                         'TotalDisCount': TotalDisCount,
#                         'TotalServiceTaxAmount': TotalServiceTaxAmount

#                     }

#                     info_logger(f'Route: {request.path}').info(json.dumps(log_data))

#                     GarmentAmount = (TotalBasicAmount - TotalDisCount) + TotalServiceTaxAmount

#                     # Calculate the total amount
#                     # TotalAmount = TotalBasicAmount + TotalServiceTaxAmount - TotalDiscount
#                     # TotalAmount = TotalBasicAmount 

#                 if len(order_garments) > 0:
#                     # Getting the payment status of each garment.
#                     # pos_order_garment_ids = [order_garment['POSOrderGarmentId'] for order_garment in order_garments]
#                     # Concatenating the order garment ids.
#                     pos_order_garments_ids = [
#                         garment.POSOrderGarmentId for garment in db.session.query(OrderGarment.POSOrderGarmentId)
#                         .filter(OrderGarment.OrderId == order_id).all()
#                     ]
#                     log_data = {
#                         'order_garments': pos_order_garments_ids,

#                     }
#                     info_logger(f'Route: {request.path}').info(json.dumps(log_data))
#                     pos_order_garment_ids = ','.join(map(str, pos_order_garments_ids))
#                     log_data = {
#                         'order_garments': pos_order_garments_ids,

#                     }
#                     info_logger(f'Route: {request.path}').info(json.dumps(log_data))
#                     # pickup_or_delivery = db.session.query(DeliveryRequest).filter(
#                     #     DeliveryRequest.OrderId == order_details.OrderId).one_or_none()
#                     pickup_or_delivery = db.session.query(DeliveryRequest).filter(
#                         DeliveryRequest.OrderId == order_details.OrderId).all()

#                     if pickup_or_delivery:

#                         payment_status = payment_module.get_garments_payment_status(order_details.EGRN,
#                                                                                     pos_order_garment_ids)

#                         log_data = {

#                             'payment_status': payment_status,
#                             "pos_order_garment_ids": pos_order_garment_ids
#                         }
#                         info_logger(f'Route: {request.path}').info(json.dumps(log_data))
#                         # checking the order is a partial order or not
#                         partial_order = db.session.query(DeliveryRequest.IsPartial).filter(
#                             DeliveryRequest.DeliveryRequestId == delivery_request_id).scalar()

#                         # checking the delivery is completed or not
#                         delivery_details = db.session.query(Delivery.PartialStatus).filter(
#                             Delivery.DeliveryRequestId == delivery_request_id).scalar()

#                         if partial_order == 0:
#                             # assigning the payment satus for normal order
#                             if payment_status["Status"] == "Fully Paid":
#                                 PaymentStatus = "Fully Paid"
#                             else:
#                                 PaymentStatus = "UnPaid"

#                         else:
#                             if delivery_details is None:
#                                 # delivery_request_count = db.session.query(
#                                 #         func.count(DeliveryRequest.DeliveryRequestId)
#                                 #     ).filter(
#                                 #         DeliveryRequest.DeliveryRequestId == delivery_request_id,
#                                 #         DeliveryRequest.IsDeleted == 0
#                                 #     ).scalar()
#                                 # if payment_status["Status"] == "Fully Paid" and delivery_request_count == 1:
#                                 #     PaymentStatus = "Partially paid"
#                                 if payment_status["Status"] == "Fully Paid":
#                                     PaymentStatus = "Fully Paid"
#                                 elif payment_status["Status"] == "Partially paid":
#                                     PaymentStatus = "Partially paid"
#                                 else:
#                                     PaymentStatus = "Partially Unpaid"
#                             else:
#                                 partial_details = db.session.query(Delivery.PartialStatus).filter(
#                                     Delivery.DeliveryRequestId == delivery_request_id).scalar()
#                                 if partial_details is not None:

#                                     if partial_details == 3:
#                                         query = f"EXEC {SERVER_DB}.dbo.SpTotalGarmentCount @EGRNNO='{order_details.EGRN}'"
#                                         result = CallSP(query).execute().fetchone()
#                                         TotalGarmentCount = result['TotalGarmentCounts']
#                                         # fetching the count of garments in the delivery garment tabel 
#                                         DeliveryCount = db.session.query(
#                                             func.count(DeliveryGarment.OrderGarmentId)
#                                         ).filter(
#                                             DeliveryGarment.OrderId == order_id,
#                                             DeliveryGarment.IsDeleted == 0
#                                         ).scalar()
#                                         log_data = {
#                                             'result': result,
#                                             'TotalGarmentCount': TotalGarmentCount,
#                                             'DeliveryCount': DeliveryCount
#                                         }
#                                         info_logger(f'Route: {request.path}').info(json.dumps(log_data))

#                                         if TotalGarmentCount == DeliveryCount:
#                                             # fetching the latest delivery deliveryrequestid
#                                             last_delivery_request = db.session.query(
#                                                 DeliveryGarment.DeliveryRequestId).filter(
#                                                 DeliveryGarment.OrderId == order_id,
#                                                 DeliveryGarment.IsDeleted == 0).order_by(
#                                                 DeliveryGarment.RecordCreatedDate.desc()).first()

#                                             if last_delivery_request:
#                                                 last_delivery_request = last_delivery_request[0]
#                                                 last_delivery_request = int(last_delivery_request)
#                                                 # Checking if the last delivery request matches the current delivery request ID

#                                                 if last_delivery_request == delivery_request_id:
#                                                     log_data = {
#                                                         "last_delivery_request": last_delivery_request,
#                                                         "delivery_request_id": delivery_request_id
#                                                     }
#                                                     info_logger(f'Route: {request.path}').info(json.dumps(log_data))

#                                                     PaymentStatus = 'Fully Paid'
#                                                 else:
#                                                     PaymentStatus = 'Partially Paid'
#                                         else:
#                                             PaymentStatus = 'Partially Paid'


#                                     elif partial_details == 1:
#                                         PaymentStatus = 'Fully Paid'
#                                     elif partial_details == 2:
#                                         PaidStatus = db.session.query(Delivery.Activity_Status).filter(
#                                             Delivery.DeliveryRequestId == delivery_request_id).scalar()
#                                         if PaidStatus == 2:
#                                             # fetching the total garments count of the order
#                                             query = f"EXEC {SERVER_DB}.dbo.SpTotalGarmentCount @EGRNNO='{order_details.EGRN}'"
#                                             result = CallSP(query).execute().fetchone()
#                                             TotalGarmentCount = result['TotalGarmentCounts']
#                                             # fetching the count of garments in the delivery garment tabel 
#                                             DeliveryCount = db.session.query(
#                                                 func.count(DeliveryGarment.OrderGarmentId)
#                                             ).filter(
#                                                 DeliveryGarment.OrderId == order_id,
#                                                 DeliveryGarment.IsDeleted == 0
#                                             ).scalar()

#                                             if TotalGarmentCount == DeliveryCount:
#                                                 # fetching the latest delivery deliveryrequestid
#                                                 last_delivery_request = db.session.query(
#                                                     DeliveryGarment.DeliveryRequestId).filter(
#                                                     DeliveryGarment.OrderId == order_id,
#                                                     DeliveryGarment.IsDeleted == 0).order_by(
#                                                     DeliveryGarment.RecordCreatedDate.desc()).first()
#                                                 if last_delivery_request:
#                                                     last_delivery_request = last_delivery_request[0]
#                                                     # Checking if the last delivery request matches the current delivery request ID
#                                                     if last_delivery_request == delivery_request_id:

#                                                         PaymentStatus = 'Fully Paid'
#                                                     else:
#                                                         PaymentStatus = 'Partially Paid'
#                                             else:
#                                                 PaymentStatus = 'Partially Paid'
#                                         else:
#                                             PaymentStatus = 'Un paid'

#                         # # Calling the SP to get the payment details.
#                         # query = f"EXEC {SERVER_DB}.dbo.getGarementPaymentInfoDetails @egrnno='{order_details.EGRN}',@ORDERGARMENTID='{pos_order_garment_ids}'"
#                         # garment_payment_details = CallSP(query).execute().fetchall()

#                         # log_data = {
#                         #         'query':query,
#                         #         'garment_payment_details :': garment_payment_details,

#                         #         'payment_status':payment_status
#                         #     }
#                         # info_logger(f'Route: {request.path}').info(json.dumps(log_data))

#                         # # Getting the payment status of each garment.
#                         # for order_garment in order_garments:
#                         #     for garment_payment_detail in garment_payment_details:
#                         #         if order_garment['POSOrderGarmentId'] == garment_payment_detail['ordergarmentid']:
#                         #             if garment_payment_detail['AmountReceived'] == "YES":
#                         #                 order_garment['PaymentStatus'] = "Fully Paid"
#                         #             else:
#                         #                 order_garment['PaymentStatus'] = "Unpaid"
#                         #             break
#                         # if order_garment['PaymentStatus'] =="Unpaid":
#                         #     order_garment['PaymentStatus'] = "Unpaid"

#                         # else:
#                         #     partial_details = db.session.query(Delivery.PartialStatus).filter(
#                         #         Delivery.DeliveryRequestId == delivery_request_id ).scalar()
#                         #     if partial_details is not None:

#                         #         if partial_details == 3:
#                         #             order_garment['PaymentStatus'] = 'Partially Paid'
#                         #         elif partial_details == 1:
#                         #             order_garment['PaymentStatus'] = 'Fully Paid'

#                         # partial_order = db.session.query(DeliveryRequest.IsPartial).filter(
#                         #     DeliveryRequest.DeliveryRequestId == delivery_request_id).scalar()

#                         # if partial_order == 1:
#                         #     pos_order_garments_id = [
#                         #     garment.POSOrderGarmentId for garment in db.session.query(DeliveryGarment.POSOrderGarmentId)
#                         #     .filter(DeliveryGarment.DeliveryRequestId == delivery_request_id,DeliveryGarment.IsDeleted == 0).all()
#                         #     ]
#                         #     pos_order_garment_ids = ','.join(map(str, pos_order_garments_ids))

#                         #     payment_status = payment_module.get_garments_payment_status(order_details.EGRN,
#                         #                                                                 pos_order_garment_ids)

#                         #     if payment_status['Status'] == "Unpaid":
#                         #         order_garment['PaymentStatus'] ="Partially Unpaid"

#                         # log_data = {

#                         #        'partial_order':partial_order,
#                         #         'order_garment[PaymentStatus]':order_garment['PaymentStatus']
#                         #     }
#                         # info_logger(f'Route: {request.path}').info(json.dumps(log_data))

#                         # # Getting the payment details from the tables.
#                         if payment_status['Status'] == "Fully Paid" or payment_status['Status'] == "Partially paid":
#                             # Payment is either fully paid or partially paid.
#                             # payment_details = db.session.query(
#                             #     TransactionPaymentInfo.PaymentMode,
#                             #     TransactionPaymentInfo.PaymentAmount,
#                             #     TransactionPaymentInfo.CreatedOn.label('PaymentDate'),
#                             #     TransactionPaymentInfo.InvoiceNo.label('InvoiceNumber')
#                             # ).join(TransactionInfo, and_(
#                             #     TransactionInfo.TransactionId == TransactionPaymentInfo.TransactionId,
#                             #     TransactionInfo.PaymentId == TransactionPaymentInfo.PaymentId)).join(Order,
#                             #                                                                          TransactionInfo.EGRNNo == Order.EGRN).filter(
#                             #     Order.OrderId == order_id,
#                             #     TransactionPaymentInfo.InvoiceNo != None).all()
#                             trn_no = db.session.query(DeliveryRequest.TRNNo).filter(
#                                 DeliveryRequest.DeliveryRequestId == delivery_request_id).one_or_none()
#                             if trn_no is not None:
#                                 trn_no = trn_no[0]

#                             payment_details = db.session.query(
#                                 TransactionPaymentInfo.PaymentMode,
#                                 TransactionPaymentInfo.PaymentAmount,
#                                 TransactionPaymentInfo.CreatedOn.label('PaymentDate'),
#                                 TransactionPaymentInfo.InvoiceNo.label('InvoiceNumber')
#                             ).join(TransactionInfo, and_(
#                                 TransactionInfo.TransactionId == TransactionPaymentInfo.TransactionId,
#                                 TransactionInfo.PaymentId == TransactionPaymentInfo.PaymentId)).join(DeliveryRequest,
#                                                                                                      TransactionInfo.DCNo == DeliveryRequest.TRNNo).filter(
#                                 DeliveryRequest.TRNNo == trn_no,
#                                 TransactionPaymentInfo.InvoiceNo != None).distinct(
#                                 TransactionPaymentInfo.PaymentMode,
#                                 TransactionPaymentInfo.PaymentAmount,
#                                 TransactionPaymentInfo.CreatedOn,
#                                 TransactionPaymentInfo.InvoiceNo
#                             ).all()

#         except Exception as e:
#             error_logger(f'Route: {request.path}').error(e)

#         delivery_status = db.session.query(Delivery.DeliveryRequestId).filter(Delivery.OrderId == order_id).order_by(
#             Delivery.RecordCreatedDate.desc()).first()

#         log_data = {
#             'delivery_status': delivery_status,
#         }
#         info_logger(f'Route: {request.path}').info(json.dumps(log_data))

#         if delivery_status:
#             delivery_status = delivery_status[0]

#         if delivery_status == delivery_request_id:
#             apply_delivery_charge = True
#         delivery_charge = db.session.query(Order.DeliveryCharge).filter(Order.OrderId == order_id).scalar()

#         if delivery_charge is None:
#             delivery_charge = 0

#         log_data = {

#             'delivery_charge': delivery_charge,
#             'apply_delivery_charge': apply_delivery_charge,

#         }
#         info_logger(f'Route: {request.path}').info(json.dumps(log_data))

#         if order_details:
#             final_data = generate_final_data('DATA_FOUND')
#             final_data['result'] = SerializeSQLAResult(order_details).serialize_one()

#             if final_data['result']['BasicAmount'] is None:
#                 basic_amount = 0
#             else:
#                 basic_amount = final_data['result']['BasicAmount']

#             if final_data['result']['Discount'] is None:
#                 discount = 0
#             else:
#                 discount = final_data['result']['Discount']

#             if final_data['result']['ServiceTaxAmount'] is None:
#                 service_tax = 0
#             else:
#                 service_tax = final_data['result']['ServiceTaxAmount']

#             final_data['result']['OrderValueold'] = (basic_amount - discount) + service_tax

#             if delivery_status is None or apply_delivery_charge:
#                 payment_amounts = GarmentAmount + delivery_charge
#             else:
#                 payment_amounts = GarmentAmount

#             final_data['result']['OrderValue'] = payment_amounts

#             final_data['result']['GarmentsCount'] = total_garments
#             final_data['result']['Garments'] = order_garments
#             final_data['result']['PaymentStatus'] = PaymentStatus

#             # if isinstance(order_garment, dict):  # Ensure it's a dictionary
#             #     final_data['result']['PaymentStatus'] = order_garment.get('PaymentStatus', 'NA')
#             # else:
#             #     final_data['result']['PaymentStatus'] = 'NA' 
#             if pickup_or_delivery is not None:

#                 final_data['result']['PaymentDetails'] = SerializeSQLAResult(payment_details).serialize(
#                     full_date_fields=['PaymentDate'])
#             else:
#                 final_data['result']['PaymentDetails'] = []
#         else:
#             final_data = generate_final_data('DATA_NOT_FOUND')
#     else:
#         # Form validation error.
#         final_data = generate_final_data('FORM_ERROR')
#         final_data['errors'] = populate_errors(form.errors)

#     return final_data

@store_console_blueprint.route('/get_order_details', methods=["POST"])
# @authenticate('store_user')
def get_order_details():
    """
    API for getting the order details.
    @return:
    """
    form = GetOrderDetailsForm()

    if form.validate_on_submit():
        BookingId = form.BookingId.data
        TRNNo = form.TRNNo.data
        activity_type = form.activity_type.data
        order_details = None

        try:
            if activity_type == "Pickup":
                
                query = f""" EXEC JFSL.DBO.SPFabCompletedPickUpJson @BookingID ={BookingId}"""
                order_details = CallSP(query).execute().fetchall()
            else:
                query = f""" EXEC JFSL.DBO.SPFabCompletedDeliveryJson @TRNNo = '{TRNNo}'"""
                order_details = CallSP(query).execute().fetchall()
            log_data = {
                    'query': query,
                    "order_details":order_details
                }
            info_logger(f'Route: {request.path}').info(json.dumps(log_data))
        except Exception as e:
            error_logger(f'Route: {request.path}').error(e)
        if order_details:
            order_data = order_details[0]
            garments_json = order_data.get("Garments", "[]")
            garments_data = json.loads(garments_json)
            garments_list = json.loads(garments_data) if isinstance(garments_data, str) else garments_data
            payment_data = order_data["PaymentDetails"]
            payment_list = json.loads(payment_data) if isinstance(payment_data, str) else payment_data

            order_data["Garments"] = garments_list
            order_data["PaymentDetails"] = payment_list

            # Prepare final response
            final_data = generate_final_data('DATA_FOUND')
            final_data['result'] = order_details[0]
        else:
            final_data = generate_final_data('DATA_NOT_FOUND')

    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(form.errors)

    return final_data





@store_console_blueprint.route('/get_report/<filename>', methods=["GET"])
def get_report(filename):
    """
    API for getting the Excel reports.
    @param filename: Excel report name (without file extension.)
    @return: Returns the file if it exists, otherwise, error msg.
    """
    root_dir = os.path.dirname(current_app.instance_path)
    target_file = f'{root_dir}/reports/{filename}.xlsx'
    file_exists = os.path.exists(target_file)
    if file_exists:
        return send_from_directory(directory=f'{root_dir}/reports', filename=f'{filename}.xlsx', as_attachment=True)
    else:
        final_data = generate_final_data('FILE_NOT_FOUND')
        return final_data


@store_console_blueprint.route('/attendance_report', methods=["POST"])
@authenticate('store_user')
def attendance_report():
    """
    API for generating the attendance report for the delivery users.
    @return:
    """
    attendance_report_form = AttendanceReportForm()
    if attendance_report_form.validate_on_submit():
        date = attendance_report_form.date.data
        # Convert string date to datetime object.
        date_obj = datetime.strptime(date, "%d-%m-%Y")
        # From the date object, convert the date to YYYY-MM-DD format.
        formatted_date = date_obj.strftime("%Y-%m-%d %H:%M:%S")
        attendance_data = None
        # Edited by MMM
        end_date = attendance_report_form.end_date.data
        # Convert string date to datetime object.
        end_date_obj = datetime.strptime(end_date, "%d-%m-%Y")
        # From the date object, convert the date to YYYY-MM-DD format.
        formatted_end_date_obj = end_date_obj.strftime("%Y-%m-%d %H:%M:%S")
        user_id = request.headers.get('user-id')
        error_msg = ''
        # Edited by MMM
        try:
            # Getting the branch code belong to the store user
            # Edited by MMM
            store_user_branch_codes = store_controller_queries.get_store_user_branches(user_id)
            delivery_users = db.session.query(DeliveryUser.DUserId).join(
                DeliveryUserBranch,
                DeliveryUserBranch.DUserId == DeliveryUser.DUserId, ).filter(
                DeliveryUserBranch.BranchCode.in_(store_user_branch_codes), DeliveryUserBranch.IsDeleted == 0,
                                                                            DeliveryUser.IsActive == 1).all()
            # Populate a list of duserid's according to the store user
            delivery_users = [i.DUserId for i in delivery_users]
            if len(delivery_users) > 0:
                # Select Yes if the user has been clocked out, else select No.
                is_clocked_out = case(
                    [(DeliveryUserAttendance.ClockOutTime == None, literal('No').label("ClockedOut")), ],
                    else_=literal("Yes").label("ClockedOut")).label("ClockedOut")

                # Selecting the row number.
                row_number = func.row_number().over(
                    order_by=asc(DeliveryUserAttendance.ClockInTime)).label(
                    'SerialNumber')
                # Getting the data from the DB.
                attendance_data = db.session.query(row_number, DeliveryUserAttendance.DUserId, DeliveryUser.UserName,
                                                   DeliveryUser.MobileNo, DeliveryUser.EmailId,
                                                   DeliveryUserAttendance.Date,
                                                   DeliveryUserAttendance.ClockInTime,
                                                   DeliveryUserAttendance.ClockOutTime, is_clocked_out).join(
                    DeliveryUser,
                    DeliveryUserAttendance.DUserId == DeliveryUser.DUserId).filter(
                    DeliveryUserAttendance.DUserId.in_(delivery_users),
                    and_(DeliveryUserAttendance.Date >= formatted_date,
                         DeliveryUserAttendance.Date <= formatted_end_date_obj)).all()
            else:
                error_msg = 'No delivery users associated with the store user'
                # Edited by MMM
        except Exception as e:
            error_logger(f'Route: {request.path}').error(e)
        # Serializing the result object.
        attendance_data = SerializeSQLAResult(attendance_data).serialize()
        # Getting the associated branches from the DB.
        for data in attendance_data:
            # If a DisplayName found for a branch, then select DisplayName as the BranchName.
            select_branch_name = case(
                [(or_(Branch.DisplayName == None, Branch.DisplayName == ''), Branch.BranchName), ],
                else_=Branch.DisplayName).label("BranchName")

            # Getting the associated branches of a delivery user.
            branch_base_query = db.session.query(DeliveryUserBranch.BranchCode, select_branch_name).join(Branch,
                                                                                                         DeliveryUserBranch.BranchCode == Branch.BranchCode).filter(
                Branch.IsDeleted == 0, DeliveryUserBranch.IsDeleted == 0,
                DeliveryUserBranch.DUserId == data['DUserId'])

            associate_branches = branch_base_query.all()
            # Getting all  branches with IsDefaultBranch false from DB
            optional_branches = branch_base_query.filter(
                or_(DeliveryUserBranch.IsDefaultBranch == 0, DeliveryUserBranch.IsDefaultBranch == None)).all()

            # Getting branch code from DB
            default_branches = db.session.query(DeliveryUserBranch.BranchCode, select_branch_name).join(Branch,
                                                                                                        DeliveryUserBranch.BranchCode == Branch.BranchCode).filter(
                DeliveryUserBranch.IsDefaultBranch == True, DeliveryUserBranch.IsDeleted == 0,
                DeliveryUserBranch.DUserId == data['DUserId'], Branch.IsDeleted == 0).all()

            # Format Date from dict
            looped_date = datetime.strptime(data['Date'], '%d-%m-%Y')
            # Add a day to the formatted date
            added_next_date = looped_date + timedelta(1)
            # Getting selected branches on that day from DB
            selected_branches = db.session.query(select_branch_name).distinct(
                DeliveryUserDailyBranch.BranchCode).join(DeliveryUserDailyBranch,
                                                         DeliveryUserDailyBranch.BranchCode == Branch.BranchCode).filter(
                DeliveryUserDailyBranch.DUserId == data['DUserId'],
                DeliveryUserDailyBranch.RecordCreatedDate.between(
                    looped_date, added_next_date)).all()

            # List of branch codes.
            branch_codes = [branch.BranchCode for branch in associate_branches]

            # Getting the state(s) names based on branch code.
            states = store_controller_queries.get_states(branch_codes)
            state_names = [state.StateName for state in states]
            state_names_string = ','.join(map(str, state_names))
            data['States'] = state_names_string

            # Getting the city(s) names based on branch code.
            cities = store_controller_queries.get_cities(branch_codes)
            city_names = [city.CityName for city in cities]
            city_names_string = ','.join(map(str, city_names))
            data['Cities'] = city_names_string

            # List of optional branch names.
            branch_names = [branch.BranchName for branch in optional_branches]
            branch_names_string = ','.join(map(str, branch_names))
            data['OptionalBranches'] = branch_names_string

            # Populating a list of BranchName's
            default_branches_list = [branch.BranchName for branch in default_branches]
            default_branch_names_string = ','.join(map(str, default_branches_list))
            data['DefaultBranches'] = default_branch_names_string

            # Populating a list of selected branch codes on the corresponding day
            selected_branches_list = [branch.BranchName for branch in selected_branches]
            selected_branch_name_string = ','.join(map(str, selected_branches_list))
            data['SelectedBranches'] = selected_branch_name_string

        # if attendance_data is not None:
        if len(attendance_data) > 0:
            final_data = generate_final_data('DATA_FOUND')
            # Report flag is included in the request. So generate the file and send the file back.
            report_link = GenerateReport(attendance_data, 'attendance').generate().get()
            if report_link is not None:
                final_data['result'] = report_link
            else:
                # Failed to generate the file.
                final_data = generate_final_data('FILE_NOT_FOUND')
        elif error_msg:
            final_data = generate_final_data('CUSTOM_FAILED', error_msg)
        else:
            final_data = generate_final_data('DATA_NOT_FOUND')
    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(attendance_report_form.errors)

    return final_data


# @store_console_blueprint.route('/message_logs_report', methods=["POST"])
# @authenticate('store_user')
# def message_logs_report():
#     """
#     API for generating the reports based the data in the MessageLogs table.
#     @return:
#     """
#     # per_page = 2

#     message_log_report_form = MessageLogsReport()
#     if message_log_report_form.validate_on_submit():
#         # page = message_log_report_form.page.data

#         # from_date = message_log_report_form.from_date.data
#         day_interval = message_log_report_form.day_interval.data
#         report = message_log_report_form.report.data
#         d_userid = None if message_log_report_form.delivery_user_id.data == '' else message_log_report_form.delivery_user_id.data
#         # Convert string date to datetime object.
#         # from_date_obj = datetime.strptime(from_date, "%d-%m-%Y")
#         # # From the date object, convert the date to YYYY-MM-DD format.
#         # formatted_from_date = from_date_obj.strftime("%Y-%m-%d %H:%M:%S")
#         #
#         # to_date = message_log_report_form.to_date.data
#         # # Convert string date to datetime object.
#         # to_date_obj = datetime.strptime(to_date, "%d-%m-%Y")
#         # # From the date object, convert the date to YYYY-MM-DD format.
#         # formatted_to_date = to_date_obj.strftime("%Y-%m-%d %H:%M:%S")
#         message_logs = None
#         if day_interval is not None:
#             interval_start_date = (datetime.today() - timedelta(day_interval)).strftime("%Y-%m-%d %H:%M:%S")

#             try:
#                 # Edited by MMM
#                 if d_userid:
#                     # Getting the details from the DB related to the delivery user.
#                     message_logs = db.session.query(MessageLog.DUserId, MessageLog.CustomerCode.label('Customer ID'),
#                                                     MessageLog.MobileNo.label('Customer Contact Number'),
#                                                     DeliveryUser.UserName.label('Delivery User name'),
#                                                     DeliveryUser.MobileNo.label('Delivery User Contact Number'),
#                                                     MessageLog.PickupRequestId, MessageLog.DeliveryRequestId,
#                                                     MessageTemplate.MessageContent.label('SMSContent'),
#                                                     MessageLog.RecordCreatedDate.label('Sent Date and Time'),
#                                                     MessageLog.Lat,
#                                                     MessageLog.Long).join(DeliveryUser,
#                                                                           MessageLog.DUserId == DeliveryUser.DUserId).join(
#                         MessageTemplate, MessageLog.MessageTemplateId == MessageTemplate.Id).filter(
#                         and_(MessageLog.RecordCreatedDate > interval_start_date,
#                              MessageLog.RecordCreatedDate < get_current_date(), MessageLog.DUserId == d_userid),
#                     ).all()
#                     # paginate(page, per_page, error_out=False)

#                 else:
#                     # Getting the details from the DB.
#                     message_logs = db.session.query(MessageLog.DUserId, MessageLog.CustomerCode.label('Customer ID'),
#                                                     MessageLog.MobileNo.label('Customer Contact Number'),
#                                                     DeliveryUser.UserName.label('Delivery User name'),
#                                                     DeliveryUser.MobileNo.label('Delivery User Contact Number'),
#                                                     MessageLog.PickupRequestId, MessageLog.DeliveryRequestId,
#                                                     MessageTemplate.MessageContent.label('SMSContent'),
#                                                     MessageLog.RecordCreatedDate.label('Sent Date and Time'),
#                                                     MessageLog.Lat,
#                                                     MessageLog.Long).join(DeliveryUser,
#                                                                           MessageLog.DUserId == DeliveryUser.DUserId).join(
#                         MessageTemplate, MessageLog.MessageTemplateId == MessageTemplate.Id).filter(
#                         and_(MessageLog.RecordCreatedDate > interval_start_date,
#                              MessageLog.RecordCreatedDate < get_current_date())
#                     ).all()


#             except Exception as e:
#                 error_logger(f'Route: {request.path}').error(e)
#         else:
#             try:
#                 # Edited by MMM
#                 if d_userid:
#                     # Getting the details from the DB related to the delivery user.
#                     message_logs = db.session.query(MessageLog.DUserId, MessageLog.CustomerCode.label('Customer ID'),
#                                                     MessageLog.MobileNo.label('Customer Contact Number'),
#                                                     DeliveryUser.UserName.label('Delivery User name'),
#                                                     DeliveryUser.MobileNo.label('Delivery User Contact Number'),
#                                                     MessageLog.PickupRequestId, MessageLog.DeliveryRequestId,
#                                                     MessageTemplate.MessageContent.label('SMSContent'),
#                                                     MessageLog.RecordCreatedDate.label('Sent Date and Time'),
#                                                     MessageLog.Lat,
#                                                     MessageLog.Long).join(DeliveryUser,
#                                                                           MessageLog.DUserId == DeliveryUser.DUserId).join(
#                         MessageTemplate, MessageLog.MessageTemplateId == MessageTemplate.Id).filter(
#                         MessageLog.DUserId == d_userid).all()
#                     # paginate(page, per_page, error_out=False)

#                 else:
#                     # Getting the details from the DB.
#                     message_logs = db.session.query(MessageLog.DUserId, MessageLog.CustomerCode.label('Customer ID'),
#                                                     MessageLog.MobileNo.label('Customer Contact Number'),
#                                                     DeliveryUser.UserName.label('Delivery User name'),
#                                                     DeliveryUser.MobileNo.label('Delivery User Contact Number'),
#                                                     MessageLog.PickupRequestId, MessageLog.DeliveryRequestId,
#                                                     MessageTemplate.MessageContent.label('SMSContent'),
#                                                     MessageLog.RecordCreatedDate.label('Sent Date and Time'),
#                                                     MessageLog.Lat,
#                                                     MessageLog.Long).join(DeliveryUser,
#                                                                           MessageLog.DUserId == DeliveryUser.DUserId).join(
#                         MessageTemplate, MessageLog.MessageTemplateId == MessageTemplate.Id).all()


#             except Exception as e:
#                 error_logger(f'Route: {request.path}').error(e)

#         message_list = SerializeSQLAResult(message_logs).serialize(full_date_fields=['Sent Date and Time'])
#         for message_log in message_list:
#             if message_log['PickupRequestId'] is not None:
#                 # This is a pickup activity.

#                 # If the pickup is rescheduled, then select reschedule's BranchCode, else BranchCode of
#                 # the pickup request.
#                 select_branch_code = case([(PickupReschedule.BranchCode == None, PickupRequest.BranchCode), ],
#                                           else_=PickupReschedule.BranchCode).label("BranchCode")

#                 # If a DisplayName found for a branch, then select DisplayName as the BranchName.
#                 select_branch_name = case(
#                     [(or_(Branch.DisplayName == None, Branch.DisplayName == ''), Branch.BranchName), ],
#                     else_=Branch.DisplayName).label("BranchName")

#                 # Selecting the EGRN from the Orders table.
#                 select_egrn = case([(Order.EGRN == None, "NA"), ],
#                                    else_=Order.EGRN).label("EGRN")

#                 # If the pickup is rescheduled, then select RescheduledDate, else select PickupDate.
#                 select_activity_date = case(
#                     [(PickupReschedule.RescheduledDate == None, PickupRequest.PickupDate), ],
#                     else_=PickupReschedule.RescheduledDate).label("ActivityDate")

#                 # Selecting the pickup details from the DB.
#                 pickup_request_details = db.session.query(PickupRequest.PickupRequestId, PickupRequest.AssignedDate,
#                                                           literal('Pickup').label('Pickup/Delivery'),
#                                                           select_activity_date.label('Pickup/Delivery Date'),
#                                                           PickupRequest.BookingId,
#                                                           PickupStatusCode.StatusCode.label('Status'),
#                                                           select_egrn,
#                                                           select_branch_code,
#                                                           select_branch_name.label('Branch'),
#                                                           City.CityName.label('City'),
#                                                           State.StateName.label('State')).join(PickupStatusCode,
#                                                                                                PickupRequest.PickupStatusId == PickupStatusCode.PickupStatusId).outerjoin(
#                     Order, Order.PickupRequestId == PickupRequest.PickupRequestId).outerjoin(
#                     PickupReschedule, PickupRequest.PickupRequestId == PickupReschedule.PickupRequestId).join(
#                     Branch,
#                     select_branch_code == Branch.BranchCode).join(
#                     Area, Branch.AreaCode == Area.AreaCode).join(City, Area.CityCode == City.CityCode).join(State,
#                                                                                                             City.StateCode == State.StateCode).filter(
#                     PickupRequest.PickupRequestId == message_log['PickupRequestId'],
#                     or_(PickupReschedule.IsDeleted == 0, PickupReschedule.IsDeleted == None)).all()
#                 # PickupRequest.IsCancelled == 0, Order.IsDeleted == 0).all()

#                 if pickup_request_details and pickup_request_details[0] is not None:

#                     # Serializing the pickup request details.
#                     pickup_request_details = SerializeSQLAResult(pickup_request_details).serialize()
#                     pickup_request_details = pickup_request_details[0]

#                     # Number of times the message sent for this particular activity.
#                     number_of_times = db.session.query(func.count(MessageLog.Id)).filter(
#                         MessageLog.PickupRequestId == message_log['PickupRequestId']).scalar()

#                     message_log['NumberOfTimes'] = number_of_times

#                     # If the ActivityDate is less than current date, mention this order as Delay
#                     activity_date = pickup_request_details.get('Pickup/Delivery Date')
#                     # Convert string date to datetime object.
#                     activity_date_obj = datetime.strptime(activity_date, "%d-%m-%Y")
#                     # From the date object, convert the date to YYYY-MM-DD format.
#                     formatted_activity_date = activity_date_obj.strftime("%Y-%m-%d %H:%M:%S")

#                     # If the activity is late than today, add a late flag.
#                     if formatted_activity_date < get_today():
#                         message_log['Delayed'] = "Yes"
#                     else:
#                         message_log['Delayed'] = "No"

#                     # Looping through the keys and values of pickup_request_details dictionary and add them
#                     # into message_log dictionary.
#                     for key, value in zip(list(pickup_request_details.keys()),
#                                           list(pickup_request_details.values())):
#                         message_log[key] = value

#             elif message_log['DeliveryRequestId'] is not None:
#                 # This is a delivery activity.

#                 # If the delivery is rescheduled, then select RescheduledDate, else select DeliveryDate.
#                 select_activity_date = case(
#                     [(DeliveryReschedule.RescheduledDate == None, DeliveryRequest.DeliveryDate), ],
#                     else_=DeliveryReschedule.RescheduledDate).label("ActivityDate")

#                 # If a DisplayName found for a branch, then select DisplayName as the BranchName.
#                 select_branch_name = case(
#                     [(or_(Branch.DisplayName == None, Branch.DisplayName == ''), Branch.BranchName), ],
#                     else_=Branch.DisplayName).label("BranchName")

#                 # Getting the delivery request details from the DB.
#                 delivery_request_details = db.session.query(DeliveryRequest.DeliveryRequestId,
#                                                             DeliveryRequest.AssignedDate,
#                                                             literal('Delivery').label('Pickup/Delivery'),
#                                                             select_activity_date.label('Pickup/Delivery Date'),
#                                                             Order.BookingId,
#                                                             OrderStatusCode.StatusCode.label('Status'),
#                                                             Order.EGRN,
#                                                             Order.BranchCode,
#                                                             select_branch_name.label('Branch'),
#                                                             City.CityName.label('City'),
#                                                             State.StateName.label('State')).outerjoin(
#                     DeliveryReschedule,
#                     DeliveryReschedule.DeliveryRequestId == DeliveryRequest.DeliveryRequestId).join(
#                     Order,
#                     DeliveryRequest.OrderId == Order.OrderId).join(
#                     OrderStatusCode, Order.OrderStatusId == OrderStatusCode.OrderStatusId).outerjoin(Branch,
#                                                                                                      Order.BranchCode == Branch.BranchCode).outerjoin(
#                     Area, Branch.AreaCode == Area.AreaCode).outerjoin(City, Area.CityCode == City.CityCode).outerjoin(
#                     State,
#                     City.StateCode == State.StateCode).filter(
#                     DeliveryRequest.DeliveryRequestId == message_log['DeliveryRequestId'],
#                     Order.IsDeleted == 0,
#                     or_(DeliveryReschedule.IsDeleted == 0, DeliveryReschedule.IsDeleted == None),
#                 ).one_or_none()
#                 #     DeliveryRequest.IsDeleted == 0, Order.IsDeleted == 0,
#                 #     or_(DeliveryReschedule.IsDeleted == 0, DeliveryReschedule.IsDeleted == None),
#                 # ).one_or_none()

#                 if delivery_request_details is not None:
#                     # Serializing the delivery request details.
#                     delivery_request_details = SerializeSQLAResult(delivery_request_details).serialize_one()

#                     # Number of times the message sent for this particular activity.
#                     number_of_times = db.session.query(func.count(MessageLog.Id)).filter(
#                         MessageLog.DeliveryRequestId == message_log['DeliveryRequestId']).scalar()

#                     message_log['NumberOfTimes'] = number_of_times

#                     # If the ActivityDate is less than current date, mention this order as Delay
#                     activity_date = delivery_request_details.get('Pickup/Delivery Date')
#                     # Convert string date to datetime object.
#                     activity_date_obj = datetime.strptime(activity_date, "%d-%m-%Y")
#                     # From the date object, convert the date to YYYY-MM-DD format.
#                     formatted_activity_date = activity_date_obj.strftime("%Y-%m-%d %H:%M:%S")

#                     # If the activity is late than today, add a late flag.
#                     if formatted_activity_date < get_today():
#                         message_log['Delayed'] = "Yes"
#                     else:
#                         message_log['Delayed'] = "No"

#                     # Looping through the keys and values of delivery_request_details dictionary and add them
#                     # into message_log dictionary.
#                     for key, value in zip(list(delivery_request_details.keys()),
#                                           list(delivery_request_details.values())):
#                         message_log[key] = value

#         if message_list:
#             final_data = generate_final_data('DATA_FOUND')
#             # Removing some unwanted fields in the result.
#             for message_log in message_list:
#                 message_log.pop('DUserId')
#                 message_log.pop('DeliveryRequestId')
#                 message_log.pop('PickupRequestId')
#             # Edited by MMM
#             if report:
#                 # Report flag is included in the request. So generate the file and send the file back.
#                 report_link = GenerateReport(message_logs, 'message_logs').generate().get()
#                 if report_link is not None:
#                     final_data['result'] = report_link
#                 else:
#                     # Failed to generate the file.
#                     final_data = generate_final_data('FILE_NOT_FOUND')
#             else:
#                 final_data = generate_final_data('DATA_FOUND')
#                 final_data['result'] = message_list
#                 # Edited by MMM
#         else:
#             final_data = generate_final_data('DATA_NOT_FOUND')
#     else:
#         # Form validation error.
#         final_data = generate_final_data('FORM_ERROR')
#         final_data['errors'] = populate_errors(message_log_report_form.errors)

#     return final_data

@store_console_blueprint.route('/message_logs_report', methods=["POST"])
# @authenticate('store_user')
def message_logs_report():
    """
    API for generating the reports based the data in the MessageLogs table.
    @return:
    """
    # per_page = 2

    message_log_report_form = MessageLogsReport()
    if message_log_report_form.validate_on_submit():
        # page = message_log_report_form.page.data

        # from_date = message_log_report_form.from_date.data
        day_interval = message_log_report_form.day_interval.data
        report = message_log_report_form.report.data
        d_userid = None if message_log_report_form.delivery_user_id.data == '' else message_log_report_form.delivery_user_id.data
        interval_start_date = (datetime.today() - timedelta(day_interval)).strftime("%Y-%m-%d %H:%M:%S")
        query = f""" EXEC JFSL.DBO.SPFabMassageLogs @interval_start_date = '{interval_start_date}',@DUserID={d_userid}"""
        message_list = CallSP(query).execute().fetchall()
        if message_list:
            final_data = generate_final_data('DATA_FOUND')
            # Removing some unwanted fields in the result.
            for message_log in message_list:
                message_log.pop('DUserId')
                message_log.pop('DeliveryRequestId')
                message_log.pop('PickupRequestId')
            # Edited by MMM
            if report:
                # Report flag is included in the request. So generate the file and send the file back.
                report_link = GenerateReport(message_list, 'message_list').generate().get()
                if report_link is not None:
                    final_data['result'] = report_link
                else:
                    # Failed to generate the file.
                    final_data = generate_final_data('FILE_NOT_FOUND')
            else:
                final_data = generate_final_data('DATA_FOUND')
                final_data['result'] = message_list
                # Edited by MMM
        else:
            final_data = generate_final_data('DATA_NOT_FOUND')
    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(message_log_report_form.errors)

    return final_data

@store_console_blueprint.route('/get_completed_activity_report_date_wise', methods=["POST"])
# @authenticate('store_user')
def get_completed_activity_report_date_wise():
    """
    API for getting the pending activities in a branch.
    @return:
    """
    completed_activities_form = GetCompletedActivitiesReportForm()
    if completed_activities_form.validate_on_submit():
        user_id = request.headers.get('user-id')
        from_date = completed_activities_form.from_date.data
        to_date = completed_activities_form.to_date.data
        #completed_activities = []
        # log_data = {
        #     'PickupsReport :': 'Test'
        # }
        # info_logger(f'Route: {request.path}').info(json.dumps(log_data))
        try:
            formatted_from_date = datetime.strptime(from_date, "%d-%m-%Y")
            # From the date object, convert the date to YYYY-MM-DD format.
            formatted_from_date = formatted_from_date.strftime("%Y-%m-%d %H:%M:%S")
            formatted_to_date = datetime.strptime(to_date, "%d-%m-%Y")

            formatted_to_date = formatted_to_date.strftime("%Y-%m-%d %H:%M:%S")

            store_user_branches = store_controller_queries.get_store_user_branches(user_id, None, None, True)
            #branch_data = ','.join(store_user_branches) if store_user_branches else 'NULL'
            branches = ','.join(store_user_branches)
            try:
                #query = f"Exec CustomerApp.[dbo].[CompletedActivityReportNew] @fromdate={formatted_to_date}, @todate={formatted_to_date}, @branch={branch_data}"
                #query = f"Exec CustomerApp.[dbo].[CompletedActivityReportNew] @fromdate='{formatted_from_date}', @todate='{formatted_to_date}'"
                
                query = f"Exec JFSL.[dbo].[SPFabCompletedActivityReportConsole ] @fromdate='{formatted_from_date}', @todate='{formatted_to_date}', @branch='{branches}'"

                log_data = {
                    'query': query
                }
                info_logger(f'Route: {request.path}').info(json.dumps(log_data))
                result = CallSP(query).execute().fetchall()
                log_data = {
                    'query succ11': result
                }
                info_logger(f'Route: {request.path}').info(json.dumps(log_data))
                if result:
                    log_data = {
                        'query succ': 'query'
                    }
                    info_logger(f'Route: {request.path}').info(json.dumps(log_data))
                    final_data = generate_final_data('DATA_FOUND')
                    #final_data['result'] = result
                    report_link = GenerateReport(result,
                                                 'completed').generate().get()
                    if report_link is not None:
                        final_data['result'] = report_link
                    else:
                        # Failed to generate the file.
                        final_data = generate_final_data('FILE_NOT_FOUND')
                else:
                    log_data = {
                        'query succ11': 'Else'
                    }
                    info_logger(f'Route: {request.path}').info(json.dumps(log_data))
                    final_data = generate_final_data('DATA_NOT_FOUND')

            except Exception as e:
                error_logger(f'Route: {request.path}').error(e)
                final_data = generate_final_data('ERROR')
        except Exception as e:
            error_logger(f'Route: {request.path}').error(e)

    return final_data


@store_console_blueprint.route('/get_completed_activity_report_date_wise_live', methods=["POST"])
# @authenticate('store_user')
def get_completed_activity_report_date_wise_live():
    """
    API for getting the pending activities in a branch.
    @return:
    """
    completed_activities_form = GetCompletedActivitiesReportForm()
    if completed_activities_form.validate_on_submit():
        user_id = request.headers.get('user-id')
        from_date = completed_activities_form.from_date.data
        to_date = completed_activities_form.to_date.data
        completed_activities = []
        # log_data = {
        #     'PickupsReport :': 'Test'
        # }
        # info_logger(f'Route: {request.path}').info(json.dumps(log_data))
        try:
            formatted_from_date = datetime.strptime(from_date, "%d-%m-%Y")
            # From the date object, convert the date to YYYY-MM-DD format.
            formatted_from_date = formatted_from_date.strftime("%Y-%m-%d %H:%M:%S")
            formatted_to_date = datetime.strptime(to_date, "%d-%m-%Y")

            formatted_to_date = formatted_to_date.strftime("%Y-%m-%d %H:%M:%S")

            store_user_branches = store_controller_queries.get_store_user_branches(user_id, None, None, True)

            record_created_date = PickupRequest.RecordCreatedDate
            # Getting the completed pickups.
            # log_data = {
            #     'PickupsReport :': 'B4Test Nw'
            # }
            # info_logger(f'Route: {request.path}').info(json.dumps(log_data))
            completed_pickups = store_controller_queries.get_completed_pickups_fromdate_todate(record_created_date,
                                                                                               formatted_from_date,
                                                                                               formatted_to_date,
                                                                                               store_user_branches)

            record_created_date = Delivery.RecordCreatedDate

            log_data = {
                'PickupsReport :': 'completed_pickups'
            }
            info_logger(f'Route: {request.path}').info(json.dumps(log_data))

            # Getting the completed deliveries.
            completed_deliveries = store_controller_queries.get_completed_deliveries_fromdate_todate(
                record_created_date,
                formatted_from_date, formatted_to_date,
                store_user_branches)
            log_data = {
                'deliveryreport 2 :': 'deliveryreport 1'
            }
            info_logger(f'Route: {request.path}').info(json.dumps(log_data))
            try:

                # Populating the completed activities by combining both completed pickups and completed deliveries.
                completed_activities = completed_pickups.union(completed_deliveries).order_by(
                    record_created_date.desc()).all()
                log_data = {
                    'deliveryreport 2 :': 'deliveryreport'
                }
                info_logger(f'Route: {request.path}').info(json.dumps(log_data))
            except Exception as e:
                error_logger(f'Route: {request.path}').error(e)
                log_data = {
                    'deliveryreport 22 :': 'deliveryreport 3'
                }
                info_logger(f'Route: {request.path}').info(json.dumps(log_data))

        except Exception as e:
            error_logger(f'Route: {request.path}').error(e)

        completed_activities = SerializeSQLAResult(completed_activities).serialize()
        serialized_activities_without_record_created_date = [
            {k: v for k, v in activity.items() if k != 'RecordCreatedDate'} for activity in completed_activities
        ]
        for completed_activity in completed_activities:

            if completed_activity['ActivityType'] == "Pickup":
                # log_data = {
                #     'deliveryreport11 :': completed_activity['OrderId']
                # }
                # info_logger(f'Route: {request.path}').info(json.dumps(log_data))

                # Select Remarks if not NULL, else select NA.
                select_remarks = case([(OrderReview.Remarks == None, "NA"), ],
                                      else_=OrderReview.Remarks).label("Remarks")

                # Retrieving the OrderReviews & star ratings while created during the pickup.
                order_reviews = db.session.query(OrderReview.StarRating, OrderReviewReason.ReviewReason,
                                                 select_remarks).outerjoin(OrderReviewReason,
                                                                           OrderReview.OrderReviewReasonId == OrderReviewReason.OrderReviewReasonId).filter(
                    OrderReview.OrderId == completed_activity['OrderId']).first()

                # .one_or_none()

                if order_reviews is not None:
                    completed_activity['Review'] = SerializeSQLAResult(order_reviews).serialize_one()
                else:
                    completed_activity['Review'] = {}

            elif completed_activity['ActivityType'] == "Delivery":

                # Select Remarks if not NULL, else select NA.
                select_remarks = case([(DeliveryReview.Remarks == None, "NA"), ],
                                      else_=DeliveryReview.Remarks).label("Remarks")

                # Retrieving the DeliveryReviews & star ratings while created during the delivery.
                delivery_reviews = db.session.query(DeliveryReview.StarRating, DeliveryReviewReason.ReviewReason,
                                                    select_remarks).outerjoin(DeliveryReviewReason,
                                                                              DeliveryReview.DeliveryReviewReasonId == DeliveryReviewReason.DeliveryReviewReasonId).filter(
                    DeliveryReview.OrderId == completed_activity['OrderId']).first()

                if delivery_reviews is not None:
                    completed_activity['Review'] = SerializeSQLAResult(delivery_reviews).serialize_one()
                else:
                    completed_activity['Review'] = {}

        if completed_activities:
            final_data = generate_final_data('DATA_FOUND')

            # Report flag is included in the request. So generate the file and send the file back.
            report_link = GenerateReport(serialized_activities_without_record_created_date,
                                         'completed').generate().get()
            if report_link is not None:
                final_data['result'] = report_link
            else:
                # Failed to generate the file.
                final_data = generate_final_data('FILE_NOT_FOUND')
        else:
            final_data = generate_final_data('DATA_NOT_FOUND')
    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(completed_activities_form.errors)

    return final_data


# @store_console_blueprint.route('/get_cancelled_pickups', methods=["POST"])
# # @authenticate('store_user')
# def get_cancelled_pickups():
#     cancelled_pickups_form = GetCancelledPickupsForm()
#     if cancelled_pickups_form.validate_on_submit():
#         day_interval = cancelled_pickups_form.day_interval.data
#         branch_codes = cancelled_pickups_form.branch_codes.data
#         report = cancelled_pickups_form.report.data
#         interval_start_date = None
#         user_id = request.headers.get('user-id')
#         if day_interval is not None:
#             interval_start_date = (datetime.today() - timedelta(day_interval)).strftime("%Y-%m-%d %H:%M:%S")
#         try:

#             if not branch_codes:
#                 # Getting the branches associated with the user.
#                 # Edited by MMM
#                 store_user_branches = store_controller_queries.get_store_user_branches(user_id, None, None, True)
#             else:
#                 # Branch code(s) are given.
#                 store_user_branches = branch_codes
#             if interval_start_date is not None:
#                 # Here, a day interval is specified. So select the details from the start date and current date.
#                 interval_condition_check = and_(PickupRequest.CancelledDate < get_current_date(),
#                                                 PickupRequest.CancelledDate > interval_start_date)
#             else:
#                 # No interval day is specified.
#                 interval_condition_check = PickupRequest.CancelledDate < get_current_date()
#             select_branch_name = case(
#                 [(or_(Branch.DisplayName == None, Branch.DisplayName == ''), Branch.BranchName), ],
#                 else_=Branch.DisplayName).label("BranchName")
#             cancelled_pickups = db.session.query(PickupRequest.PickupRequestId, PickupRequest.BookingId,
#                                                  PickupRequest.RecordCreatedDate, select_branch_name,
#                                                  Customer.CustomerName,
#                                                  PickupCancelReason.CancelReason, PickupRequest.CancelRemarks,
#                                                  PickupRequest.BranchCode, PickupRequest.CancelledDate).join(Branch,
#                                                                                                              PickupRequest.BranchCode == Branch.BranchCode
#                                                                                                              ).join(
#                 Customer, PickupRequest.CustomerId == Customer.CustomerId).join(
#                 PickupCancelReason, PickupRequest.CancelReasonId == PickupCancelReason.CancelReasonId
#             ).filter(PickupRequest.PickupStatusId == 4,
#                      PickupRequest.IsCancelled == 1, PickupRequest.BranchCode.in_(store_user_branches),
#                      interval_condition_check).all()
#             # or_(PickupRequest.CancelledDeliveryUser != None, PickupRequest.CancelledStoreUser != None),
#             #         PickupRequest.CancelledBy == None,

#         except Exception as e:
#             error_logger(f'Route: {request.path}').error(e)
#         cancelled_pickups = SerializeSQLAResult(cancelled_pickups).serialize(full_date_fields=['CancelledDate'])
#         if cancelled_pickups:
#             try:
#                 for pickups in cancelled_pickups:
#                     pickup_id = pickups['PickupRequestId']
#                     message_logs = db.session.query(MessageLog.DUserId, DeliveryUser.UserName,
#                                                     MessageLog.DeliveryRequestId,
#                                                     MessageTemplate.MessageContent.label('SMSContent'),
#                                                     MessageLog.RecordCreatedDate.label('SmsSentDate')).join(
#                         DeliveryUser,
#                         MessageLog.DUserId == DeliveryUser.DUserId).join(
#                         MessageTemplate, MessageLog.MessageTemplateId == MessageTemplate.Id).filter(
#                         MessageLog.DeliveryRequestId == pickup_id).order_by(
#                         MessageLog.RecordCreatedDate.desc()).first()
#                     if message_logs is not None:
#                         pickups['SmsSentBy'] = message_logs.UserName
#                         pickups['SMSContent'] = message_logs.SMSContent
#                         pickups['SmsSentDate'] = message_logs.SmsSentDate
#                     else:
#                         pickups['SmsSentBy'] = "NA"
#                         pickups['SMSContent'] = "NA"
#                         pickups['SmsSentDate'] = "NA"
#                     pickup_details = db.session.query(PickupRequest).filter(
#                         PickupRequest.PickupRequestId == pickup_id).one_or_none()
#                     if pickup_details.CancelledBy is not None:
#                         pickups["CancelledBy"] = pickup_details.CancelledBy
#                     elif pickup_details.CancelledStoreUser is not None:
#                         store_user = db.session.query(StoreUser).filter(
#                             StoreUser.SUserId == pickup_details.CancelledStoreUser).one_or_none()
#                         pickups["CancelledBy"] = store_user.UserName + " - StoreUser "
#                     elif pickup_details.CancelledDeliveryUser is not None:
#                         delivery_user = db.session.query(DeliveryUser).filter(
#                             DeliveryUser.DUserId == pickup_details.CancelledDeliveryUser).one_or_none()
#                         pickups["CancelledBy"] = delivery_user.UserName + " - DeliveryUser "
#                     else:
#                         pass
#                         # pickups["CancelledBy"] = "Fabricare"
#             except Exception as e:
#                 error_logger(f'Route: {request.path}').error(e)
#         if cancelled_pickups:
#             final_data = generate_final_data('DATA_FOUND')
#             if report:
#                 # Report flag is included in the request. So generate the file and send the file back.
#                 report_link = GenerateReport(cancelled_pickups, 'completed').generate().get()
#                 if report_link is not None:
#                     final_data['result'] = report_link
#                 else:
#                     # Failed to generate the file.
#                     final_data = generate_final_data('FILE_NOT_FOUND')
#             else:
#                 final_data['result'] = cancelled_pickups
#         else:
#             final_data = generate_final_data('DATA_NOT_FOUND')
#     else:
#         # Form validation error.
#         final_data = generate_final_data('FORM_ERROR')
#         final_data['errors'] = populate_errors(cancelled_pickups_form.errors)

#     return final_data

@store_console_blueprint.route('/get_cancelled_pickups', methods=["POST"])
# @authenticate('store_user')
def get_cancelled_pickups():
    cancelled_pickups_form = GetCancelledPickupsForm()
    if cancelled_pickups_form.validate_on_submit():
        day_interval = cancelled_pickups_form.day_interval.data
        branch_codes = cancelled_pickups_form.branch_codes.data
        report = cancelled_pickups_form.report.data
        interval_start_date = None
        user_id = request.headers.get('user-id')
        cancelled_activities = None
        if day_interval is not None:
            interval_start_date = (datetime.today() - timedelta(day_interval)).strftime("%Y-%m-%d %H:%M:%S")
        try:

            if not branch_codes:
                # Getting the branches associated with the user.
                # Edited by MMM
                store_user_branches = store_controller_queries.get_store_user_branches(user_id)
                store_user_all_branches = store_controller_queries.get_store_user_branches(user_id, None, None, True)
                
            else:
                # Branch code(s) are given.
                #store_user_branches = branch_codes
                store_user_branches = branch_codes
                store_user_all_branches = branch_codes
            if not branch_codes:
                # branches = ''
                branches = ','.join(store_user_all_branches)
                #print(branches)
            else:
                branches = ','.join(store_user_branches)
                #print(branches)
            if interval_start_date is not None:
                # Here, a day interval is specified. So select the details from the start date and current date.
                # interval_condition_check = and_(PickupRequest.CancelledDate < get_current_date(),
                #                                 PickupRequest.CancelledDate > interval_start_date)
                to_date = get_current_date()
                from_date = interval_start_date
            else:
                from_date = ''
                to_date = ''
            cancelled_activities_query = f"EXEC JFSL.dbo.SPFabCancelledPickupActivity @fromdate='{from_date}', @todate='{to_date}', @BranchCode = '{branches}'"
            log_data = {
                'PendingMobileAppActivity qry :': cancelled_activities_query
            }
            info_logger(f'Route: {request.path}').info(json.dumps(log_data))

            cancelled_activities = CallSP(cancelled_activities_query).execute().fetchall()
                # No interval day is specified.
            #     interval_condition_check = PickupRequest.CancelledDate < get_current_date()
            # select_branch_name = case(
            #     [(or_(Branch.DisplayName == None, Branch.DisplayName == ''), Branch.BranchName), ],
            #     else_=Branch.DisplayName).label("BranchName")
            # cancelled_pickups = db.session.query(PickupRequest.PickupRequestId, PickupRequest.BookingId,
            #                                      PickupRequest.RecordCreatedDate, select_branch_name,
            #                                      Customer.CustomerName, PickupRequest.PickupSource,
            #                                      PickupCancelReason.CancelReason, PickupRequest.CancelRemarks,
            #                                      PickupRequest.BranchCode, PickupRequest.CancelledDate).join(Branch,
            #                                                                                                  PickupRequest.BranchCode == Branch.BranchCode
            #                                                                                                  ).join(
            #     Customer, PickupRequest.CustomerId == Customer.CustomerId).join(
            #     PickupCancelReason, PickupRequest.CancelReasonId == PickupCancelReason.CancelReasonId
            # ).filter(PickupRequest.PickupStatusId == 4,
            #          PickupRequest.IsCancelled == 1, PickupRequest.BranchCode.in_(store_user_branches),
            #          interval_condition_check).all()

            

        except Exception as e:
            error_logger(f'Route: {request.path}').error(e)
        # cancelled_pickups = SerializeSQLAResult(cancelled_pickups).serialize(
        #     full_date_fields=['CancelledDate', 'RecordCreatedDate'])
        #if cancelled_pickups:
            # try:
            #     for pickups in cancelled_pickups:
            #         pickup_id = pickups['PickupRequestId']
            #         message_logs = db.session.query(MessageLog.DUserId, DeliveryUser.UserName,
            #                                         MessageLog.DeliveryRequestId,
            #                                         MessageTemplate.MessageContent.label('SMSContent'),
            #                                         MessageLog.RecordCreatedDate.label('SmsSentDate')).join(
            #             DeliveryUser,
            #             MessageLog.DUserId == DeliveryUser.DUserId).join(
            #             MessageTemplate, MessageLog.MessageTemplateId == MessageTemplate.Id).filter(
            #             MessageLog.DeliveryRequestId == pickup_id).order_by(
            #             MessageLog.RecordCreatedDate.desc()).first()
            #         if message_logs is not None:
            #             pickups['SmsSentBy'] = message_logs.UserName
            #             pickups['SMSContent'] = message_logs.SMSContent
            #             pickups['SmsSentDate'] = message_logs.SmsSentDate
            #         else:
            #             pickups['SmsSentBy'] = "NA"
            #             pickups['SMSContent'] = "NA"
            #             pickups['SmsSentDate'] = "NA"
            #         pickup_details = db.session.query(PickupRequest).filter(
            #             PickupRequest.PickupRequestId == pickup_id).one_or_none()
            #         if pickup_details.CancelledBy is not None:
            #             pickups["CancelledBy"] = pickup_details.CancelledBy
            #         elif pickup_details.CancelledStoreUser is not None:
            #             store_user = db.session.query(StoreUser).filter(
            #                 StoreUser.SUserId == pickup_details.CancelledStoreUser).one_or_none()
            #             pickups["CancelledBy"] = store_user.UserName + " - StoreUser "
            #         elif pickup_details.CancelledDeliveryUser is not None:
            #             delivery_user = db.session.query(DeliveryUser).filter(
            #                 DeliveryUser.DUserId == pickup_details.CancelledDeliveryUser).one_or_none()
            #             pickups["CancelledBy"] = delivery_user.UserName + " - DeliveryUser "
            #         else:
            #             pass
            #             # pickups["CancelledBy"] = "Fabricare"
            # except Exception as e:
            #     error_logger(f'Route: {request.path}').error(e)
        if cancelled_activities:
           
            final_data = generate_final_data('DATA_FOUND')
            final_data['result'] = cancelled_activities
            if report:
                # Report flag is included in the request. So generate the file and send the file back.
                report_link = GenerateReport(cancelled_activities, 'completed').generate().get()
                if report_link is not None:
                    final_data['result'] = report_link
                else:
                    # Failed to generate the file.
                    final_data = generate_final_data('FILE_NOT_FOUND')
            else:
                final_data['result'] = cancelled_activities
        else:
            final_data = generate_final_data('DATA_NOT_FOUND')
    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(cancelled_pickups_form.errors)

    return final_data


# @store_console_blueprint.route('/cancel_or_reschedule_permission', methods=["GET"])
# @authenticate('store_user')
# def cancel_or_reschedule_permission():
#     user_id = request.headers.get('user-id')
#     error_msg = None
#     store_user = db.session.query(StoreUser.CancellPickupPermission, StoreUser.ReschedulePickupPermission,
#                                   StoreUser.BranchChangePermission).filter(
#         StoreUser.SUserId == user_id).one_or_none()
#     if store_user is not None:
#         final_data = generate_final_data('SUCCESS')
#         final_data['result'] = {'reschedule_permission': store_user.ReschedulePickupPermission,
#                                 'cancel_permission': store_user.CancellPickupPermission,
#                                 'branch_changing_permission': store_user.BranchChangePermission}
#     else:
#         error_msg = ''
#         final_data = generate_final_data('CUSTOM_FAILED', error_msg)
#     return final_data

@store_console_blueprint.route('/cancel_or_reschedule_permission', methods=["GET"])
@authenticate('store_user')
def cancel_or_reschedule_permission():
    user_id = request.headers.get('user-id')
    error_msg = None
    store_user = db.session.query(StoreUser.CancellPickupPermission, StoreUser.ReschedulePickupPermission,
                                  StoreUser.BranchChangePermission, StoreUser.ProductScreenPermission,StoreUser.OnlyProductScreenAccess,StoreUser.IsZIC,StoreUser.IsAdmin).filter(
        StoreUser.SUserId == user_id).one_or_none()

    if store_user.IsAdmin is True:
        IsZic = True
    else:
        IsZic = store_user.IsZIC

  
    screen_access = db.session.execute(text("""
        SELECT S.ScreenName,S.ScreenId
        FROM Screens S
        LEFT JOIN UserScreenAccess Ua ON Ua.UserId = :user_id
        CROSS APPLY STRING_SPLIT(Ua.ScreenId, ',') AS split
        WHERE S.ScreenId = TRY_CAST(split.value AS INT)
    """), {"user_id": user_id}).fetchall()

    screen_access = SerializeSQLAResult(screen_access).serialize()

    

    log_data = {
     'store_user': store_user,
     "IsZic":IsZic,

    }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))

    if store_user is not None:
        final_data = generate_final_data('SUCCESS')
        final_data['result'] = {'reschedule_permission': store_user.ReschedulePickupPermission,
                                'cancel_permission': store_user.CancellPickupPermission,
                                'branch_changing_permission': store_user.BranchChangePermission,
                                'product_screen_permission': store_user.ProductScreenPermission, 
                                "only_product_screen_permission" :store_user.OnlyProductScreenAccess,"screen_access":screen_access, 
                                "zonal_permission":IsZic}
    else:
        error_msg = ''
        final_data = generate_final_data('CUSTOM_FAILED', error_msg)
    return final_data


@store_console_blueprint.route('/get_paginated_walk_in_orders', methods=["POST"])
# @authenticate('store_user')
def get_paginated_walk_in_orders():
    """
    API for getting the walk in orders.
    @return:
    """
    form = GetWalkInOrdersForm()
    user_id = request.headers.get('user-id')
    if form.validate_on_submit():
        branch_codes = form.branch_codes.data
        from_date = None if form.from_date.data == '' else form.from_date.data
        to_date = None if form.to_date.data == '' else form.to_date.data
        search = '' if form.search.data == '' else form.search.data
        page = form.page.data
        report = form.report.data
        walk_in_orders = []
        per_page = 50
        try:
            if from_date is not None:
                start_date_obj = datetime.strptime(from_date, "%d-%m-%Y")
                from_date = start_date_obj.strftime("%Y-%m-%d %H:%M:%S")
                end_date_obj = datetime.strptime(to_date, "%d-%m-%Y")
                to_date = end_date_obj.strftime("%Y-%m-%d %H:%M:%S")
            else:
                from_date = (datetime.today() - timedelta(15)).strftime("%Y-%m-%d %H:%M:%S")
                to_date = get_current_date()
            if not branch_codes:
                # Getting the branches associated with the user.
                # Edited by MMM
                query = f""" EXEC JFSL.Dbo.SPFabStoreBranchInfo @store_user_id = {user_id}"""
                store_user_branches = CallSP(query).execute().fetchall()
                if isinstance(store_user_branches, list):
                    for branch in store_user_branches:
                        if isinstance(branch, dict) and 'BranchCode' in branch:
                            branch_codes.append(branch['BranchCode'])

            else:
                # Branch codes are given.
                branch_codes = branch_codes
            store_user_branches = ','.join(branch_codes)
            # Select AddressLine2 if not NULL, else select NA.
            query = f""" EXEC JFSL.Dbo.[SPFabWalkINActivity] @store_user_branches  = '{store_user_branches}',
                        @Search = '{search}',@fromdate = '{from_date}', @todate = '{to_date}' """
           
            log_data = {
                'query qry :': query
            }
            info_logger(f'Route: {request.path}').info(json.dumps(log_data))
            walk_in_orders = CallSP(query).execute().fetchall()
            walk_in_orders = walk_in_orders.paginate(page, per_page, error_out=False)
            if walk_in_orders is not None:
                walk_in_orders = [document for document in walk_in_orders.items]
                # Serializing for looping and adding CustomerPreferredDate and IsPreferredDateAfter flag
                walk_in_orders = SerializeSQLAResult(walk_in_orders).serialize()
                # Looping serialized Deliveries
                for delivery_id in walk_in_orders:

                    if delivery_id['CustomerPreferredDate'] is not None:
                        # If the delivery have customer preferred date add it ti the raw
                        cus_preferred_date = delivery_id['CustomerPreferredDate']
                        # Formatting today for comparing
                        formatted_today = datetime.today().strftime("%d-%m-%Y")

                        if cus_preferred_date > formatted_today:
                            # If customer preferred day is bigger than today make IsPreferredDateAfter True
                            delivery_id['IsPreferredDateAfter'] = True
                        else:
                            delivery_id['IsPreferredDateAfter'] = False

                    else:
                        # Send IsPreferredDateAfter, CustomerPreferredDate as None and False
                        delivery_id['IsPreferredDateAfter'] = False
                        delivery_id['CustomerPreferredDate'] = None

        except Exception as e:
            error_logger(f'Route: {request.path}').error(e)

        if walk_in_orders:
            final_data = generate_final_data('DATA_FOUND')

            if report:
                # Report flag is included in the request. So generate the file and send the file back.
                report_link = GenerateReport(walk_in_orders, 'walkin').generate().get()
                if report_link is not None:
                    final_data['result'] = report_link
                else:
                    # Failed to generate the file.
                    final_data = generate_final_data('FILE_NOT_FOUND')
            else:
                final_data['result'] = walk_in_orders
        else:
            final_data = generate_final_data('DATA_NOT_FOUND')
    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(form.errors)

    return final_data

    # ********** OLD CODE *************

@store_console_blueprint.route('/get_fabricare_store_users', methods=["GET"])
@authenticate('store_user')
def get_fabricare_store_users():
    query = f"EXEC {SERVER_DB}.dbo.GetFabricareUsers"
    store_users = CallSP(query).execute().fetchall()
    # store_user_list = [users['name'] for users in store_users]
    if len(store_users) > 0:
        final_data = generate_final_data('DATA_FOUND')
        final_data['result'] = store_users
    else:
        final_data = generate_final_data('DATA_NOT_FOUND')

    return final_data


@store_console_blueprint.route('/get_fabricare_store_user_branches', methods=["POST"])
@authenticate('store_user')
def get_fabricare_store_user_branches():
    store_user_name_form = GetFabricareStoreUserBranchForm()
    if store_user_name_form.validate_on_submit():
        user_name = store_user_name_form.user_name.data
        query = f"EXEC {SERVER_DB}.dbo.GetFabricareUserBranches @username='{user_name}'"
        branches = CallSP(query).execute().fetchall()
        final_data = generate_final_data('DATA_FOUND')
        final_data['result'] = branches
    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(store_user_name_form.errors)
    return final_data


# Delivery Flow Enhancements Code Changes Laji Start -11-feb-2024

# 10-feb-2024 Laji
# @store_console_blueprint.route('/get_Delivered_without_Payment', methods=["POST"])
# # @authenticate('store_user')
# def get_Delivered_without_Payment():
#     """
#         API for getting the pending activities in a branch.
#         @return:
#         """
#     delivered_without_Payment_form = GetDeliveredWithoutPaymentForm()

#     if delivered_without_Payment_form.validate_on_submit():
#         from_date = None if delivered_without_Payment_form.from_date.data == '' else delivered_without_Payment_form.from_date.data
#         to_date = None if delivered_without_Payment_form.to_date.data == '' else delivered_without_Payment_form.to_date.data
#         # unassigned_only = pending_activities_form.unassigned_only.data
#         branch_codes = delivered_without_Payment_form.branch_codes.data
#         # late_only = pending_activities_form.late_only.data
#         # report = pending_activities_form.report.data
#         delivered_without_Payment = []
#         user_id = request.headers.get('user-id')
#         empty_date = False
#         per_page = 50
#         # if from_date is not None:
#         #     start_date_obj = datetime.strptime(from_date, "%Y-%m-%d")
#         #     from_date = start_date_obj.strftime("%Y-%m-%d %H:%M:%S")
#         #     end_date_obj = datetime.strptime(to_date, "%Y-%m-%d")
#         #     to_date = (end_date_obj + timedelta(1)).strftime("%Y-%m-%d %H:%M:%S")
#         #     # to_date = end_date_obj.strftime("%Y-%m-%d %H:%M:%S")
#         # else:
#         #     # pass
#         #     from_date = (datetime.today() - timedelta(8)).strftime("%Y-%m-%d %H:%M:%S")
#         #     to_date = get_current_date()
#         # log_data = {
#         #     'from_date inv': from_date
#         # }
#         # info_logger(f'Route: {request.path}').info(json.dumps(log_data))
        
#         # if from_date ='Invalid date':
#         #     from_date = None
#         # if to_date ='Invalid date':
#         #     to_date = None

#         if from_date is not None:
#             start_date_obj = datetime.strptime(from_date, "%d-%m-%Y")
#             from_date = start_date_obj.strftime("%Y-%m-%d %H:%M:%S")
#             print(from_date)
#             end_date_obj = datetime.strptime(to_date, "%d-%m-%Y")
#             to_date = (end_date_obj + timedelta(1)).strftime("%Y-%m-%d %H:%M:%S")

#             # formatted_from_date = formatted_from_date.strftime("%Y-%m-%d %H:%M:%S")
#             # formatted_to_date = datetime.strptime(to_date, "%d-%m-%Y")

#             # formatted_to_date = formatted_to_date.strftime("%Y-%m-%d %H:%M:%S")
#         else:
#             from_date = (datetime.today() - timedelta(8)).strftime("%Y-%m-%d %H:%M:%S")
#             to_date = get_current_date()
#             empty_date = True

#         try:
#             if not branch_codes:
#                 # Getting the branches associated with the user.
#                 # Edited by MMM
#                 store_user_branches = store_controller_queries.get_store_user_branches(user_id)
#                 store_user_all_branches = store_controller_queries.get_store_user_branches(user_id, None, None, True)
#             else:
#                 store_user_branches = branch_codes
#                 store_user_all_branches = branch_codes
#             # print(store_user_branches)
#             branches = ','.join(store_user_branches)
#             # branch_list = ', '.join('?' for _ store_user_branches)
#             branch_list = "','".join(map(str, store_user_branches))
#             branch_list = f"'{branch_list}'"
#             result = ''
#             # log_data = {
#             #         'branch_list': branch_list
#             # }
#             # info_logger(f'Route: {request.path}').info(json.dumps(log_data))
#             try:
#                 if empty_date:
#                     qry = text(f"""
#                                 SELECT CASE WHEN O.PickupRequestId IS NULL THEN 'Walk-In' ELSE 'D2D' END AS ActivityCategory,
#                                 D.EGRN,
#                                 D.DeliveryDate AS DeliveredDate,
#                                 D.PaymentStatus AS PaymentStatus,
#                                 U.UserName AS DeliveredBy,
#                                 C.CustomerCode,
#                                 C.CustomerName,
#                                 C.MobileNo,
#                                 B.BranchName AS BranchName,
#                                 CASE WHEN D.DeliveryWithoutOTP = 1 THEN    'NO'  ELSE 'YES'end AS IsOTPSent,
#                                 D.PayableAmount AS PayableValue,
#                                 D.DeliveryDate AS DeliveredOn,
#                                 D.Reasons,
#                                 CASE WHEN REQ.TRNNO IS NULL THEN 'NA' ELSE REQ.TRNNO END AS TRNNO
#                             FROM  CustomerApp.[dbo].Deliveries D
#                             LEFT JOIN  DeliveryRequests REQ ON D.DeliveryRequestId = REQ.DeliveryRequestId
#                             LEFT JOIN DeliveryReschedules RSH ON D.DeliveryRequestId = RSH.DeliveryRequestId
#                             LEFT JOIN  DeliveryUsers U ON D.DUserId = U.DUserId
#                             LEFT JOIN Customers C ON D.CustomerId = C.CustomerId
#                             LEFT JOIN CustomerAddress ADDR ON D.DeliveryAddressId = ADDR.CustAddressId
#                             LEFT JOIN Branches B ON D.BranchCode = B.BranchCode
#                             LEFT JOIN Orders O ON D.OrderId = O.OrderId
#                             WHERE D.PaymentStatus ='Un-Paid' AND D.BranchCode IN ({branch_list})
#                         """)
#                     # AND D.BranchCode IN ({branch_list})
#                     log_data = {
#                         'unPaid-qry11': 'qry'
#                     }
#                     info_logger(f'Route: {request.path}').info(json.dumps(log_data))
#                 else:
#                     qry = text(f"""
#                                 SELECT CASE WHEN O.PickupRequestId IS NULL THEN 'Walk-In' ELSE 'D2D' END AS ActivityCategory,
#                                 D.EGRN,
#                                 D.DeliveryDate AS DeliveredDate,
#                                 D.PaymentStatus AS PaymentStatus,
#                                 U.UserName AS DeliveredBy,
#                                 C.CustomerCode,
#                                 C.CustomerName,
#                                 C.MobileNo,
#                                 B.BranchName AS BranchName,
#                                 CASE WHEN D.DeliveryWithoutOTP = 1 THEN    'NO'  ELSE 'YES'end AS IsOTPSent,
#                                 D.PayableAmount AS PayableValue,
#                                 D.DeliveryDate AS DeliveredOn,
#                                 D.Reasons,
#                                 CASE WHEN REQ.TRNNO IS NULL THEN 'NA' ELSE REQ.TRNNO END AS TRNNO
#                             FROM  CustomerApp.[dbo].Deliveries D
#                             LEFT JOIN  DeliveryRequests REQ ON D.DeliveryRequestId = REQ.DeliveryRequestId
#                             LEFT JOIN DeliveryReschedules RSH ON D.DeliveryRequestId = RSH.DeliveryRequestId
#                             LEFT JOIN  DeliveryUsers U ON D.DUserId = U.DUserId
#                             LEFT JOIN Customers C ON D.CustomerId = C.CustomerId
#                             LEFT JOIN CustomerAddress ADDR ON D.DeliveryAddressId = ADDR.CustAddressId
#                             LEFT JOIN Branches B ON D.BranchCode = B.BranchCode
#                             LEFT JOIN Orders O ON D.OrderId = O.OrderId
#                             WHERE D.PaymentStatus ='Un-Paid' AND D.BranchCode IN ({branch_list}) AND D.DeliveryDate >= '{from_date}' AND D.DeliveryDate <= '{to_date}'
#                         """)
#                     # AND D.BranchCode IN ({branch_list})
#                     log_data = {
#                         'unPaid-qry11': 'qry'

#                     }
#                     info_logger(f'Route: {request.path}').info(json.dumps(log_data))
#                 # query_text = qry.text
#                 test = db.engine.execute(qry).fetchall()

#                 result = SerializeSQLAResult(test).serialize()
#             except Exception as e:
#                 print(e)
#         except Exception as e:
#             print(e)
#         if result:

#             final_data = generate_final_data('SUCCESS')
#             final_data["result"] = result
#             # print(result)

#         else:
#             final_data = generate_final_data('DATA_NOT_FOUND')
#         return final_data

#     else:
#         # Form validation error.
#         final_data = generate_final_data('FORM_ERROR')
#         final_data['errors'] = populate_errors(delivered_without_Payment_form.errors)

#     return final_data

@store_console_blueprint.route('/get_Delivered_without_Payment', methods=["POST"])
# @authenticate('store_user')
def get_Delivered_without_Payment():
    """
        API for getting the pending activities in a branch.
        @return:
        """
    delivered_without_Payment_form = GetDeliveredWithoutPaymentForm()

    if delivered_without_Payment_form.validate_on_submit():
        from_date = None if delivered_without_Payment_form.from_date.data == '' else delivered_without_Payment_form.from_date.data
        to_date = None if delivered_without_Payment_form.to_date.data == '' else delivered_without_Payment_form.to_date.data
        # unassigned_only = pending_activities_form.unassigned_only.data
        branch_codes = delivered_without_Payment_form.branch_codes.data
        # late_only = pending_activities_form.late_only.data
        # report = pending_activities_form.report.data
        delivered_without_Payment = []
        user_id = request.headers.get('user-id')
        empty_date = False
        per_page = 50
        search = ''
        page=''

        # if from_date is not None:
        #     start_date_obj = datetime.strptime(from_date, "%Y-%m-%d")
        #     from_date = start_date_obj.strftime("%Y-%m-%d %H:%M:%S")
        #     end_date_obj = datetime.strptime(to_date, "%Y-%m-%d")
        #     to_date = (end_date_obj + timedelta(1)).strftime("%Y-%m-%d %H:%M:%S")
        #     # to_date = end_date_obj.strftime("%Y-%m-%d %H:%M:%S")
        # else:
        #     # pass
        #     from_date = (datetime.today() - timedelta(8)).strftime("%Y-%m-%d %H:%M:%S")
        #     to_date = get_current_date()
        # log_data = {
        #     'from_date inv': from_date
        # }
        # info_logger(f'Route: {request.path}').info(json.dumps(log_data))

        # if from_date ='Invalid date':
        #     from_date = None
        # if to_date ='Invalid date':
        #     to_date = None

        if from_date is not None:
            start_date_obj = datetime.strptime(from_date, "%d-%m-%Y")
            from_date = start_date_obj.strftime("%Y-%m-%d %H:%M:%S")
            print(from_date)
            end_date_obj = datetime.strptime(to_date, "%d-%m-%Y")
            to_date = (end_date_obj + timedelta(1)).strftime("%Y-%m-%d %H:%M:%S")

            # formatted_from_date = formatted_from_date.strftime("%Y-%m-%d %H:%M:%S")
            # formatted_to_date = datetime.strptime(to_date, "%d-%m-%Y")

            # formatted_to_date = formatted_to_date.strftime("%Y-%m-%d %H:%M:%S")
        else:
            from_date = (datetime.today() - timedelta(8)).strftime("%Y-%m-%d %H:%M:%S")
            to_date = get_current_date()
            empty_date = True

        try:
            if not branch_codes:
                # Getting the branches associated with the user.
                # Edited by MMM
                store_user_branches = store_controller_queries.get_store_user_branches(user_id)
                store_user_all_branches = store_controller_queries.get_store_user_branches(user_id, None, None, True)
            else:
                store_user_branches = branch_codes
                store_user_all_branches = branch_codes
            # print(store_user_branches)
            branches = ','.join(store_user_branches)
            # branch_list = ', '.join('?' for _ store_user_branches)
            branch_list = "','".join(map(str, store_user_branches))
            branch_list = f"'{branch_list}'"
            result = ''

            # log_data = {
            #         'branch_list': branch_list
            # }
            # info_logger(f'Route: {request.path}').info(json.dumps(log_data))
            try:
                if empty_date:
                    #print("hello")

                    delivered_unpaid_query = f"EXEC JFSL.dbo.SPFabGetDeliveredWithoutPayment @page='',@search='',@filter_type='',@branch_codes = '{branches}'"

                    # AND D.BranchCode IN ({branch_list})
                    log_data = {
                        'unPaid-qry11': 'qry'
                    }
                    info_logger(f'Route: {request.path}').info(json.dumps(log_data))
                else:
                    delivered_unpaid_query = f"EXEC JFSL.dbo.SPFabGetDeliveredWithoutPayment @page='',@search='',@filter_type='',@fromdate='{from_date}',@todate='{to_date}',@branch_codes = '{branches}'"

                log_data = {
                    'unPaid-qry11': delivered_unpaid_query

                }
                info_logger(f'Route: {request.path}').info(json.dumps(log_data))
                delivered_unpaid = CallSP(delivered_unpaid_query).execute().fetchall()
                # query_text = qry.text
                # test = db.engine.execute(delivered_unpaid_query).fetchall()
                #
                # result = SerializeSQLAResult(test).serialize()
            except Exception as e:
                print(e)
        except Exception as e:
            print(e)
        if delivered_unpaid:

            final_data = generate_final_data('SUCCESS')
            final_data["result"] = delivered_unpaid
            # print(result)

        else:
            final_data = generate_final_data('DATA_NOT_FOUND')
        return final_data

    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(delivered_without_Payment_form.errors)

    return final_data


@store_console_blueprint.route('/get_Delivered_without_PaymentSP', methods=["POST"])
# @authenticate('store_user')
def get_Delivered_without_PaymentSP():
    """
        API for getting the pending activities in a branch.
        @return:
        """
    delivered_without_Payment_form = GetDeliveredWithoutPaymentForm()

    if delivered_without_Payment_form.validate_on_submit():
        from_date = None if delivered_without_Payment_form.from_date.data == '' else delivered_without_Payment_form.from_date.data
        to_date = None if delivered_without_Payment_form.to_date.data == '' else delivered_without_Payment_form.to_date.data
        # unassigned_only = pending_activities_form.unassigned_only.data
        branch_codes = delivered_without_Payment_form.branch_codes.data
        # late_only = pending_activities_form.late_only.data
        # report = pending_activities_form.report.data
        delivered_without_Payment = []
        user_id = request.headers.get('user-id')

        per_page = 50
        if from_date is not None:
            start_date_obj = datetime.strptime(from_date, "%d-%m-%Y")
            from_date = start_date_obj.strftime("%Y-%m-%d %H:%M:%S")
            print(from_date)
            end_date_obj = datetime.strptime(to_date, "%d-%m-%Y")
            to_date = (end_date_obj + timedelta(1)).strftime("%Y-%m-%d %H:%M:%S")
            print(to_date)
        else:
            from_date = (datetime.today() - timedelta(8)).strftime("%Y-%m-%d %H:%M:%S")
            to_date = get_current_date()

        # if from_date is not None:
        #     start_date_obj = datetime.strptime(from_date, "%Y-%m-%d")
        #     from_date = start_date_obj.strftime("%Y-%m-%d %H:%M:%S")
        #     end_date_obj = datetime.strptime(to_date, "%Y-%m-%d")
        #     to_date = (end_date_obj + timedelta(1)).strftime("%Y-%m-%d %H:%M:%S")
        #     # to_date = end_date_obj.strftime("%Y-%m-%d %H:%M:%S")
        # else:
        #     # pass
        #     from_date = (datetime.today() - timedelta(8)).strftime("%Y-%m-%d %H:%M:%S")
        #     to_date = get_current_date()

        try:
            if not branch_codes:
                # Getting the branches associated with the user.
                # Edited by MMM
                store_user_branches = store_controller_queries.get_store_user_branches(user_id)
                store_user_all_branches = store_controller_queries.get_store_user_branches(user_id, None, None, True)
            else:
                store_user_branches = branch_codes
                store_user_all_branches = branch_codes
            # print(store_user_branches)
            branches = ','.join(store_user_branches)
            # branch_list = ', '.join('?' for _ store_user_branches)
            branch_list = "','".join(map(str, store_user_branches))
            branch_list = f"'{branch_list}'"
            result = ''
            try:
                qry = f"EXEC CustomerApp.dbo.PendingActivity @fromdate='{from_date}',@todate='{to_date}',@branch = '{branches}',@activitytype='Delivered-UnPaid',@Status_type = 'PENDING'"

                log_data = {
                    'Pending_pickupSP qry :': qry
                    # 'Pending_pickupSP qry :' 'HIII'
                }
                info_logger(f'Route: {request.path}').info(json.dumps(log_data))

                result = CallSP(qry).execute().fetchall()

                db.session.commit()

                # test = db.engine.execute(qry).fetchall()

                # result = SerializeSQLAResult(test).serialize()


            except Exception as e:
                print(e)
        except Exception as e:
            print(e)
        if result:

            final_data = generate_final_data('SUCCESS')
            final_data["result"] = result
            # print(result)

        else:
            final_data = generate_final_data('DATA_NOT_FOUND')
        return final_data

    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(delivered_without_Payment_form.errors)

    return final_data


#  11-feb-2024 Laji





# @store_console_blueprint.route('/get_pending_delivered_Unpaid_report_date_wise', methods=["POST"])
# # @authenticate('store_user')
# def get_pending_delivered_Unpaid_report_date_wise():
#     """
#     API for getting the pending activities in a branch.
#     @return:
#     """
#     completed_activities_form = GetCompletedActivitiesReportForm()
#     if completed_activities_form.validate_on_submit():
#         user_id = request.headers.get('user-id')
#         from_date = completed_activities_form.from_date.data
#         to_date = completed_activities_form.to_date.data
#         completed_activities = []
#         try:
#             formatted_from_date = datetime.strptime(from_date, "%d-%m-%Y")
#             # From the date object, convert the date to YYYY-MM-DD format.
#             formatted_from_date = formatted_from_date.strftime("%Y-%m-%d %H:%M:%S")
#             formatted_to_date = datetime.strptime(to_date, "%d-%m-%Y")

#             formatted_to_date = formatted_to_date.strftime("%Y-%m-%d %H:%M:%S")

#             store_user_branches = store_controller_queries.get_store_user_branches(user_id, None, None, True)

#             # print(store_user_branches,formatted_to_date,formatted_from_date)
#             record_created_date = Delivery.RecordCreatedDate

#             result = ''
#             try:
#                 # branch_list = ', '.join('?' for _ in store_user_branches)
#                 branch_list = "','".join(map(str, store_user_branches))
#                 branch_list = f"'{branch_list}'"
#                 log_data = {
#                     'branch_list :': branch_list
#                 }
#                 info_logger(f'Route: {request.path}').info(json.dumps(log_data))
#                 qry = text(
#                     f"""SELECT
#                                     CASE WHEN O.PickupRequestId IS NULL THEN 'Walk-In' ELSE 'D2D' END AS ActivityCategory,
#                                     D.EGRN,
#                                     D.DeliveryDate AS DeliveredDate,
#                                     D.PaymentStatus AS PaymentStatus,
#                                     '9:00 AM' as TimeSlotFrom,
#                                     '7:00 PM' AS TimeSlotTo,
#                                     U.UserName AS DeliveredBy,
#                                     C.CustomerCode,
#                                     C.CustomerName,
#                                     C.MobileNo,
#                                     COALESCE(O.DiscountCode, 'NA') AS DiscountCode,
#                                     COALESCE(O.CouponCode, 'NA') AS CouponCode,
#                                     COALESCE(ADDR.AddressLine1, 'NA') AS AddressLine1,
#                                     COALESCE(ADDR.AddressLine2, 'NA') AS AddressLine2,
#                                     COALESCE(ADDR.AddressLine3, 'NA') AS AddressLine3,
#                                     D.BranchCode,
#                                     B.BranchName AS BranchName,
#                                     RV.StarRating,
#                                     RVR.ReviewReason,
#                                     COALESCE(RV.Remarks, 'NA') AS ReviewRemarks,
#                                     CASE WHEN D.DeliveryWithoutOTP = 'False' THEN 'YES' ELSE 'NO'   END AS 'IsOTPSent',
#                                     --(O.BasicAmount - O.Discount +O.ServiceTaxAmount) AS PayableValue,
#                                     D.PayableAmount AS PayableValue,
#                                     D.DeliveryDate AS DeliveredOn,
#                                     COALESCE(REQ.TRNNO, 'NA') AS 'TRN Number',
#                                     CASE 
#                                     WHEN (cmp.CRMComplaintId != '' and cmp.CRMComplaintId is not null) AND (D.Reasons IS NOT NULL and D.Reasons != '')  AND (D.RecordLastUpdatedDate < cmp.ComplaintDate)  THEN cmp.CRMComplaintId
#                                     WHEN (cmp.CRMComplaintId != '' and cmp.CRMComplaintId is not null)  AND (D.Reasons = '' or D.Reasons is null) THEN cmp.CRMComplaintId
#                                     ELSE ''  
#                                 END AS 'Complaint No',
#                                 CASE 
#                                     WHEN (cmp.CRMComplaintId != '' and cmp.CRMComplaintId is not null) AND (D.Reasons IS NOT NULL AND D.Reasons != '') AND (D.RecordLastUpdatedDate < cmp.ComplaintDate)  THEN cmp.ComplaintType 
#                                      WHEN (cmp.CRMComplaintId != '' and cmp.CRMComplaintId is not null) AND (D.Reasons IS NOT NULL AND D.Reasons != '' AND D.RecordLastUpdatedDate > cmp.ComplaintDate) THEN D.Reasons
#                                     WHEN (D.Reasons != '' and D.Reasons is not null) AND (cmp.CRMComplaintId = '' or cmp.CRMComplaintId is null) THEN  D.Reasons
#                                      WHEN (D.Reasons = '' OR D.Reasons is null) AND (cmp.CRMComplaintId != '' and cmp.CRMComplaintId is not null) THEN  cmp.ComplaintType 
#                                     ELSE '' 
#                                 END AS 'Reasons'
#                                 FROM
#                                     CustomerApp.[dbo].Deliveries D
#                                 LEFT JOIN
#                                     DeliveryRequests REQ ON D.DeliveryRequestId = REQ.DeliveryRequestId
#                                 LEFT JOIN
#                                     DeliveryReschedules RSH ON D.DeliveryRequestId = RSH.DeliveryRequestId  AND RSH.IsDeleted = 0
#                                 LEFT JOIN
#                                     DeliveryUsers U ON D.DUserId = U.DUserId
#                                 LEFT JOIN
#                                     Customers C ON D.CustomerId = C.CustomerId
#                                 LEFT JOIN
#                                     CustomerAddress ADDR ON D.DeliveryAddressId = ADDR.CustAddressId
#                                 LEFT JOIN
#                                     Branches B ON D.BranchCode = B.BranchCode
#                                 LEFT JOIN
#                                     Orders O ON D.OrderId = O.OrderId
#                                 LEFT JOIN
#                                     DeliveryReviews RV ON D.OrderId = RV.OrderId
#                                 LEFT JOIN
#                                     DeliveryReviewReasons RVR ON RV.DeliveryReviewReasonId = RVR.DeliveryReviewReasonId
#                                 LEFT JOIN
#                                     Complaints CMP ON D.EGRN = CMP.EGRN
#                                 WHERE
#                                     (O.IsDeleted = 0)
#                                     AND REQ.WalkIn = 0
#                                     AND D.DUserId IS NOT NULL
#                                     AND D.DeliveryId IS NOT NULL
#                                     AND D.PaymentStatus != 'Paid'
#                                     AND D.BranchCode IN ({branch_list}) AND D.DeliveryDate >= '{formatted_from_date}' AND D.DeliveryDate <= '{formatted_to_date}'                         
#                                  """)

#                 # AND      D.BranchCode   IN(store_user_branches) AND D.DeliveryDate >= formatted_from_date AND D.DeliveryDate <= formatted_to_date
#                 # print(qry)
#                 test = db.engine.execute(qry).fetchall()
#                 result = SerializeSQLAResult(test).serialize()
#                 json_response = json.dumps(result)
#             except Exception as e:
#                 print(e)

#         except Exception as e:
#             error_logger(f'Route: {request.path}').error(e)

#         # completed_activities = SerializeSQLAResult(completed_activities).serialize()
#         completed_activities = result

#         if completed_activities:
#             final_data = generate_final_data('DATA_FOUND')

#             # Report flag is included in the request. So generate the file and send the file back.
#             report_link = GenerateReport(completed_activities, 'Delivered Un-Paid').generate().get()
#             if report_link is not None:
#                 final_data['result'] = report_link
#             else:
#                 # Failed to generate the file.
#                 final_data = generate_final_data('FILE_NOT_FOUND')
#         else:
#             final_data = generate_final_data('DATA_NOT_FOUND')
#     else:
#         # Form validation error.
#         final_data = generate_final_data('FORM_ERROR')
#         final_data['errors'] = populate_errors(completed_activities_form.errors)

#     return final_data

#     # Delivery Flow Enhancements Laji END
@store_console_blueprint.route('/get_pending_delivered_Unpaid_report_date_wise', methods=["POST"])
# @authenticate('store_user')
def get_pending_delivered_Unpaid_report_date_wise():
    """
    API for getting the pending activities in a branch.
    @return:
    """
    completed_activities_form = GetCompletedActivitiesReportForm()
    if completed_activities_form.validate_on_submit():
        user_id = request.headers.get('user-id')
        from_date = completed_activities_form.from_date.data
        to_date = completed_activities_form.to_date.data
        completed_activities = []
        try:
            formatted_from_date = datetime.strptime(from_date, "%d-%m-%Y")
            # From the date object, convert the date to YYYY-MM-DD format.
            formatted_from_date = formatted_from_date.strftime("%Y-%m-%d %H:%M:%S")
            formatted_to_date = datetime.strptime(to_date, "%d-%m-%Y")

            formatted_to_date = formatted_to_date.strftime("%Y-%m-%d %H:%M:%S")

            store_user_branches = store_controller_queries.get_store_user_branches(user_id, None, None, True)


            result = ''
            try:
                # branch_list = ', '.join('?' for _ in store_user_branches)
                branch_list = ','.join(map(str, store_user_branches))

                query = f""" EXEC JFSL.Dbo.SPDeliveredUnpaidReportConsole @BrachCode = '{branch_list}',@FromDate = '{formatted_from_date}',@Todate='{formatted_to_date}'"""
                #print(query)
                log_data = {
                    'unpaid_reportSP qry :': query
                }
                info_logger(f'Route: {request.path}').info(json.dumps(log_data))
                result = CallSP(query).execute().fetchall()


                json_response = json.dumps(result)
            except Exception as e:
                print(e)

        except Exception as e:
            error_logger(f'Route: {request.path}').error(e)

        # completed_activities = SerializeSQLAResult(completed_activities).serialize()
        completed_activities = result

        if completed_activities:
            final_data = generate_final_data('DATA_FOUND')

            # Report flag is included in the request. So generate the file and send the file back.
            report_link = GenerateReport(completed_activities, 'Delivered Un-Paid').generate().get()
            if report_link is not None:
                final_data['result'] = report_link
            else:
                # Failed to generate the file.
                final_data = generate_final_data('FILE_NOT_FOUND')
        else:
            final_data = generate_final_data('DATA_NOT_FOUND')
    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(completed_activities_form.errors)

    return final_data


# MarchEnhancement 06-AUG-2024 START

@store_console_blueprint.route('/delete_pickup_instruction_icons', methods=["POST"])
def DeletePickupInstructionIcon():
    deleteiconform = DeleteIconForm()

    if deleteiconform.validate_on_submit():
        PickupInstructionid = deleteiconform.PickupinstructionsId.data
        PickupInstruction = db.session.query(PickupInstructions).filter(
            PickupInstructions.PickupinstructionsId == PickupInstructionid).first()

        if PickupInstruction:
            PickupInstruction.PickupinstructionsImage = None
            db.session.commit()

            final_data = generate_final_data('DATA_FOUND')
            final_data['result'] = 'Icon Deleted Successfully'
        else:
            final_data = generate_final_data('FORM_ERROR')
            final_data['errors'] = 'Pickup Instruction not found'
    else:
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = deleteiconform.errors

    return final_data


from flask import send_file


@store_console_blueprint.route('/get_image/<photo_file>', methods=["GET"])
def get_image(photo_file):
    """
    API for getting Audit Complaint images based on image name
    """
    print(photo_file)

    root_dir = os.path.dirname(current_app.instance_path)

    try:
        # Getting the image data from the DB.
        instruction = db.session.query(PickupInstructions).filter(
            PickupInstructions.PickupinstructionsImage == photo_file).one_or_none()
        print(instruction)
    except Exception as e:
        error_logger(f'Route: {request.path}').error(e)

    if instruction:
        # Construct the target file path
        target_file = os.path.join(root_dir, 'uploads', str(instruction.PickupinstructionsId), f'{photo_file}')

        if os.path.exists(target_file):
            log_data = {'root_dir': target_file}
            info_logger(f'Route: {request.path}').info(json.dumps(log_data))
            return send_file(target_file, mimetype='image/jpeg')
        else:
            final_data = generate_final_data('FILE_NOT_FOUND')
            return final_data
    else:
        final_data = generate_final_data('FILE_NOT_FOUND')
        return final_data


@store_console_blueprint.route('/get_pickup_instructions', methods=["POST"])
# @authenticate('store_user')
def get_pickup_instructions():
    GetPickupInstructions_form = GetPickupInstructions()

    if GetPickupInstructions_form.validate_on_submit():
        user_id = request.headers.get('user-id')
        search = GetPickupInstructions_form.search.data
        root_dir = os.path.dirname(current_app.instance_path)

        if search:
            search_filter = or_(
                PickupInstructions.PickupinstructionsId.like(f"%{search}%"),
                PickupInstructions.PickupInstructionDescription.like(f"%{search}%"),
                PickupInstructions.Pickupinstructions.like(f"%{search}%")
            )

            pickupinstructions = db.session.query(
                PickupInstructions.PickupinstructionsId,
                PickupInstructions.PickupInstructionDescription.label('Pickupinstructions'),
                PickupInstructions.Category,
                PickupInstructions.Pickupinstructions.label('PickupInstructionDescription'),
                PickupInstructions.PickupinstructionsImage
            ).filter(search_filter).all()
        else:
            pickupinstructions = db.session.query(
                PickupInstructions.PickupinstructionsId,
                PickupInstructions.PickupInstructionDescription.label('Pickupinstructions'),
                PickupInstructions.Category,
                PickupInstructions.Pickupinstructions.label('PickupInstructionDescription'),
                PickupInstructions.PickupinstructionsImage
            ).all()

        serialized_pickupinstructions = SerializeSQLAResult(pickupinstructions).serialize()
        for instruction in serialized_pickupinstructions:
            image_path = instruction.get('PickupinstructionsImage')
            if image_path:
                # instruction['PickupinstructionsImageURL'] = f'{request.host_url}static/uploads/{instruction["PickupinstructionsId"]}/{os.path.basename(image_path)}'
                # image_url='file://15.207.234.46/c$/jfsl_cloud/dev/fabric/'
                # instruction[
                #     'PickupinstructionsImageURL'] = f"{image_url}uploads/{instruction['PickupinstructionsId']}/{os.path.basename(image_path)}"
                image_url = 'https://api.jfsl.in/store_console/get_image/'
                instruction['PickupinstructionsImageURL'] = f"{image_url}{os.path.basename(image_path)}"

        if serialized_pickupinstructions:
            final_data = generate_final_data('DATA_FOUND')
            final_data['result'] = serialized_pickupinstructions
        else:
            final_data = generate_final_data('DATA_NOT_FOUND')

        # if serialized_pickupinstructions:
        #     final_data = generate_final_data('DATA_FOUND')
        #     final_data['result'] = serialized_pickupinstructions
        # else:
        #     final_data = generate_final_data('DATA_NOT_FOUND')
    else:
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(GetPickupInstructions_form.errors)

    return final_data


@store_console_blueprint.route('/add_pickup_instruction_icons', methods=["POST"])
# @authenticate('store_user')
def add_pickup_instruction_icons():
    add_icon_form = AddIconsForm()
    if add_icon_form.validate_on_submit():
        try:
            uploaded = False
            result = False
            pickup_instructions_id = add_icon_form.PickupinstructionsId.data
            PickupinstructionsImage = add_icon_form.PickupinstructionsImage.data
            instruction = db.session.query(PickupInstructions).filter_by(
                PickupinstructionsId=pickup_instructions_id).one_or_none()

            if instruction:
                # Decode the base64 image
                # image_data = base64.b64decode(PickupinstructionsImage.replace('data:image/jpeg;base64,', ''))
                if PickupinstructionsImage.startswith('data:image/jpeg;base64,'):
                    image_data = base64.b64decode(PickupinstructionsImage.replace('data:image/jpeg;base64,', ''))
                elif PickupinstructionsImage.startswith('data:image/png;base64,'):
                    image_data = base64.b64decode(PickupinstructionsImage.replace('data:image/png;base64,', ''))
                else:
                    pass

                # Generate a random value for the file name
                random_val = random.randint(0, 9999)
                filename = f'{pickup_instructions_id}_{random_val}'

                # Determine the upload folder path
                root_dir = os.path.dirname(current_app.instance_path)
                # root_dir = 'https://uatapi.jfsl.in/store_console/'

                # uploads_folder = os.path.join(root_dir, 'static/uploads', str(pickup_instructions_id))
                uploads_folder = os.path.join(root_dir, 'uploads', str(pickup_instructions_id))

                # Create the folder if it doesn't exist
                os.makedirs(uploads_folder, exist_ok=True)

                if instruction.PickupinstructionsImage:
                    # existing_image_path = instruction.PickupinstructionsImage
                    existing_image_path = os.path.join(uploads_folder, instruction.PickupinstructionsImage)
                    if os.path.exists(existing_image_path):
                        os.remove(existing_image_path)

                # Save the image file
                target_file = os.path.join(uploads_folder, filename)
                with open(target_file, 'wb') as f:
                    f.write(image_data)
                    uploaded = True

                if uploaded:
                    if pickup_instructions_id is not None:
                        instruction_img = db.session.query(PickupInstructions).filter_by(
                            PickupinstructionsId=pickup_instructions_id).one_or_none()

                        # Store the full path or a relative path
                        instruction_img.PickupinstructionsImage = filename

                        db.session.commit()
                        result = True

                if result:
                    final_data = generate_final_data('DATA_SAVED')
                    final_data['result'] = {
                        'GarmentImage': 'https://api.jfsl.in/store_console/get_image/' + filename,
                        'PickupinstructionsId': pickup_instructions_id
                    }
                else:
                    final_data = generate_final_data('DATA_SAVE_FAILED')

            else:
                final_data = generate_final_data('DATA_SAVE_FAILED')

        except Exception as e:
            db.session.rollback()
            error_logger(f'Route: {request.path}').error(e)
            final_data = generate_final_data('DATA_SAVE_FAILED')

    else:
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(add_icon_form.errors)

    return final_data


# @store_console_blueprint.route('/reschedule_pickup', methods=["POST"])
# # @authenticate('store_user')
# def reschedule_pickup():
#     """
#     API for rescheduling a pickup request.
#     """
#     reschedule_form = ReschedulePickupForm()
#     is_rescheduled = False
#     user_id = request.headers.get('user-id')
#     modified_name = db.session.query(StoreUser.UserName).filter(StoreUser.SUserId == user_id).one_or_none()
#     if reschedule_form.validate_on_submit():
#         pickup_requests = reschedule_form.pickup_requests.data
#         reschedule_reason_id = reschedule_form.reschedule_reason_id.data
#         rescheduled_date = None if reschedule_form.rescheduled_date.data == '' else reschedule_form.rescheduled_date.data
#         message = False
#         if rescheduled_date is not None:
#             message = True
#             # rescheduled_date will be DD-MM-YYYY format. Need to convert into YYYY-MM-DD format.
#             # Here, first convert the string date to date object in expected form. Here, the string date will be
#             # in dd-mm-yyyy form.
#             rescheduled_date_obj = datetime.strptime(rescheduled_date, "%d-%m-%Y")
#             # From the date object, convert the date to YYYY-MM-DD format.
#             formatted_rescheduled_date = rescheduled_date_obj.strftime("%Y-%m-%d %H:%M:%S")
#         time_slot_id = None if reschedule_form.time_slot_id.data == '' else reschedule_form.time_slot_id.data

#         # Optional fields.
#         branch_code = None if reschedule_form.branch_code.data == '' else reschedule_form.branch_code.data
#         delivery_user_id = None if reschedule_form.delivery_user_id.data == '' else reschedule_form.delivery_user_id.data
#         # address_id = None if reschedule_form.address_id.data == '' else reschedule_form.address_id.data
#         remarks = None if reschedule_form.remarks.data == '' else reschedule_form.remarks.data
#         time_slot_from = reschedule_form.time_slot_from.data
#         time_slot_to = reschedule_form.time_slot_to.data
#         is_cob = reschedule_form.is_cob.data
#         is_reschedule = reschedule_form.is_reschedule.data
#         valid_delivery_user = False
#         valid_time_slot = False
#         pickup_time_slot = None
#         clocked_in_check = False
#         first_time_assign = False
#         error_msg = ''
#         # Edited By MMM
#         # Check if delivery user is active
#         try:
#             get_updated_jfsl_data_query = f"Exec {SERVER_DB}.dbo.SP_MiscIssuesCorrectionForCustomerAppDB"
#             db.engine.execute(text(get_updated_jfsl_data_query).execution_options(autocommit=True))

#             log_data = {
#                 'get_updated_jfsl_data_query :': get_updated_jfsl_data_query
#             }
#             info_logger(f'Route: {request.path}').info(json.dumps(log_data))
#         except Exception as e:
#             print(e)
#         if db.session.query(DeliveryUser).filter(DeliveryUser.IsActive == 1, DeliveryUser.DUserId == delivery_user_id). \
#                 one_or_none():
#             # Edited By MMM
#             try:
#                 for pickup_request_id in pickup_requests:
#                     # Getting the pickup request table details. No orders should be present for this pickup request.
#                     pickup_request_details = db.session.query(PickupRequest).outerjoin(Order,
#                                                                                        Order.PickupRequestId == PickupRequest.PickupRequestId).filter(
#                         PickupRequest.PickupRequestId == pickup_request_id,
#                         or_(Order.OrderId == None, Order.IsDeleted == 1)).one_or_none()

#                     if pickup_request_details is not None:
#                         # If the delivery user is present in the request, check the delivery user's branch code

#                         # Check whether the pickup is already rescheduled or not.
#                         # If the pickup request is already rescheduled, no further reschedules are allowed.
#                         pickup_reschedule = db.session.query(PickupReschedule).filter(
#                             PickupReschedule.PickupRequestId == pickup_request_id,
#                             PickupReschedule.IsDeleted == 0).one_or_none()

#                         if pickup_reschedule is None:
#                             if rescheduled_date is None:
#                                 rescheduled_date = pickup_request_details.PickupDate

#                                 input_date = datetime.strptime(str(rescheduled_date), "%Y-%m-%d")
#                                 rescheduled_date = input_date.strftime("%d-%m-%Y")
#                                 rescheduled_date_obj = datetime.strptime(rescheduled_date, "%d-%m-%Y")
#                                 # From the date object, convert the date to YYYY-MM-DD format.
#                                 formatted_rescheduled_date = rescheduled_date_obj.strftime("%Y-%m-%d %H:%M:%S")
#                             # No previous reschedule details are available.
#                             if pickup_request_details.DUserId is None:
#                                 # No previous delivery user has been assigned to this activity.
#                                 first_time_assign = True

#                             # Check if the given date is a branch holiday or not.
#                             if branch_code is None:
#                                 # No branch code is provided.
#                                 reschedule_branch_code = pickup_request_details.BranchCode
#                             else:
#                                 # Branch code is given.
#                                 reschedule_branch_code = branch_code

#                             holiday = delivery_controller_queries.check_branch_holiday(rescheduled_date,
#                                                                                        reschedule_branch_code)

#                             if not holiday:
#                                 # The given date is not a branch holiday. So allow the reschedule.

#                                 # Checking the delivery user can be assigned to this reschedule or not.
#                                 if delivery_user_id is None:
#                                     # No delivery user is provided. Here, the delivery user is the original delivery user.
#                                     delivery_user_id = pickup_request_details.DUserId

#                                 delivery_user = db.session.query(DeliveryUser).filter(
#                                     DeliveryUser.DUserId == delivery_user_id).one_or_none()

#                                 if delivery_user is not None:

#                                     # If the rescheduled date is today, check if the
#                                     # if the delivery user is clocked in for today
#                                     if formatted_rescheduled_date == get_today():

#                                         # Check whether the delivery user is clocked in or not.
#                                         delivery_user_attendance = db.session.query(
#                                             DeliveryUserAttendance.ClockInTime).filter(
#                                             DeliveryUserAttendance.Date == get_today(),
#                                             DeliveryUserAttendance.DUserId == delivery_user_id).one_or_none()

#                                         if delivery_user_attendance is not None:
#                                             clocked_in_check = True
#                                         else:
#                                             # Delivery user has not clocked in yet for the day.
#                                             pass
#                                     else:
#                                         # This is a future date. Clocked in restriction can not be enforced here.
#                                         clocked_in_check = True

#                                     if clocked_in_check:
#                                         # Getting the branch codes associated with the delivery user.
#                                         delivery_user_branch_codes = delivery_controller_queries.get_delivery_user_branches(
#                                             delivery_user.DUserId)

#                                         # Checking whether the branch code is provided or not.
#                                         if branch_code is not None:
#                                             # Here, a branch code is provided. The given branch code must be belong
#                                             # to the delivery user.

#                                             if branch_code in delivery_user_branch_codes:
#                                                 # The delivery user can be assigned.
#                                                 valid_delivery_user = True

#                                             # Checking whether the given time slot id is belong to this branch or not.
#                                             pickup_time_slot = db.session.query(PickupTimeSlot.PickupTimeSlotId).filter(
#                                                 and_(PickupTimeSlot.TimeSlotFrom == time_slot_from,
#                                                      PickupTimeSlot.TimeSlotTo == time_slot_to),
#                                                 PickupTimeSlot.BranchCode == branch_code,
#                                                 PickupTimeSlot.IsDeleted == 0,
#                                                 or_(PickupTimeSlot.VisibilityFlag == 1,
#                                                     PickupTimeSlot.DefaultFlag == 1)).one_or_none()

#                                             if pickup_time_slot is not None:
#                                                 valid_time_slot = True
#                                                 time_slot_id = pickup_time_slot.PickupTimeSlotId
#                                             else:
#                                                 valid_time_slot = True
#                                                 time_slot_id = pickup_request_details.PickupTimeSlotId


#                                         else:
#                                             # No branch code is given. So the given delivery user must belong
#                                             # to the pickup request's branch code.

#                                             if pickup_request_details.BranchCode in delivery_user_branch_codes:
#                                                 # The delivery user can be assigned.
#                                                 valid_delivery_user = True

#                                                 # Checking whether the given time slot id is belong to this branch or not.
#                                                 pickup_time_slot = db.session.query(
#                                                     PickupTimeSlot.PickupTimeSlotId).filter(
#                                                     and_(PickupTimeSlot.TimeSlotFrom == time_slot_from,
#                                                          PickupTimeSlot.TimeSlotTo == time_slot_to),
#                                                     PickupTimeSlot.BranchCode == pickup_request_details.BranchCode,
#                                                     PickupTimeSlot.IsDeleted == 0,
#                                                     or_(PickupTimeSlot.VisibilityFlag == 1,
#                                                         PickupTimeSlot.DefaultFlag == 1)).one_or_none()
#                                                 if pickup_time_slot is not None:
#                                                     valid_time_slot = True
#                                                     time_slot_id = pickup_time_slot.PickupTimeSlotId
#                                                 else:
#                                                     valid_time_slot = True
#                                                     time_slot_id = pickup_request_details.PickupTimeSlotId

#                                     else:
#                                         error_msg = "Delivery user is not clocked in for the day."

#                                 else:
#                                     error_msg = 'No delivery user found.'

#                                 if valid_delivery_user and valid_time_slot:

#                                     # If the optional fields are None, fill up with the existing details.
#                                     if branch_code is None:
#                                         branch_code = pickup_request_details.BranchCode

#                                     # if address_id is None:
#                                     address_id = pickup_request_details.CustAddressId

#                                     if delivery_user_id is None:
#                                         delivery_user_id = pickup_request_details.DUserId

#                                     # Setting up the new PickupReschedule object.
#                                     new_reschedule = PickupReschedule(PickupRequestId=pickup_request_id,
#                                                                       RescheduleReasonId=reschedule_reason_id,
#                                                                       RescheduledDate=formatted_rescheduled_date,
#                                                                       PickupTimeSlotId=time_slot_id,
#                                                                       TimeSlotFrom=time_slot_from,
#                                                                       TimeSlotTo=time_slot_to,
#                                                                       BranchCode=branch_code,
#                                                                       CustAddressId=address_id,
#                                                                       RescheduleRemarks=remarks,
#                                                                       RescheduledStoreUser=user_id,
#                                                                       RescheduledBy=modified_name[0]
#                                                                       )
#                                     db.session.add(new_reschedule)
#                                     if formatted_rescheduled_date == get_today():
#                                         new_reschedule.DUserId = delivery_user_id
#                                     else:
#                                         pickup_request_details.DUserId = None
#                                     db.session.commit()

#                                     # Updating the RecordLastUpdatedDate in the pickup request table.
#                                     pickup_request_details.RecordLastUpdatedDate = get_current_date()
#                                     # Updating the reschedule flag in the PickupRequests table.
#                                     pickup_request_details.IsRescheduled = 1

#                                     pickup_request_details.ReschuduleStatus = 1
#                                     pickup_request_details.ReschuduleDate = formatted_rescheduled_date
#                                     pickup_request_details.ReschuduleBy = delivery_user_id
#                                     pickup_request_details.ReschuduleAddressId = address_id
#                                     pickup_request_details.ReschuduleModifiedDate = get_current_date()
#                                     pickup_request_details.ReschuduleTimeSlotId = time_slot_id
#                                     pickup_request_details.ReschuduleTimeSlotFrom = time_slot_from
#                                     pickup_request_details.ReschuduleTimeSlotTo = time_slot_to
#                                     pickup_request_details.DUserId = delivery_user_id
#                                     db.session.commit()

#                                     is_rescheduled = True
#                                     customer_id = db.session.query(PickupRequest.CustomerId).filter(
#                                         PickupRequest.PickupRequestId == pickup_request_id).first()
#                                     if customer_id is not None:
#                                         customer_id = customer_id[0]

#                                     customer_name = db.session.query(Customer.CustomerName).filter(
#                                         Customer.CustomerId == customer_id).first()
#                                     if customer_name:
#                                         customer_name = customer_name[0]
#                                         print(customer_name)
#                                     mobile_number = db.session.query(Customer.MobileNo).filter(
#                                         Customer.CustomerId == customer_id).first()
#                                     if mobile_number:
#                                         mobile_number = mobile_number[0]
#                                         print(mobile_number)
#                                     booking_id = db.session.query(PickupRequest.BookingId).filter(
#                                         PickupRequest.PickupRequestId == pickup_request_id).first()
#                                     if booking_id is not None:
#                                         booking_id = booking_id[0]
#                                     log_data = {
#                                         'json_request reschedule pickup1': 'testt',

#                                     }
#                                     info_logger(f'Route: {request.path}').info(json.dumps(log_data))
#                                     formated_date = formatted_rescheduled_date

#                                     formatted_rescheduled_date = datetime.strptime(formated_date, "%Y-%m-%d %H:%M:%S")

#                                     date = formatted_rescheduled_date.strftime("%d-%m-%Y ")

#                                     timeslot_from = time_slot_from

#                                     # timeslotfrom = timeslot_from.strftime("%H:%M:%S")

#                                     # timeslot_from = datetime.strptime(timeslotfrom, "%H:%M:%S")
#                                     # timeslot_from = timeslot_from.strftime("%I:%M %p")

#                                     timeslot_to = time_slot_to
#                                     # timeslot_to = timeslot_to.strftime("%H:%M:%S")
#                                     # timeslotto = datetime.strptime(timeslot_to, "%H:%M:%S")
#                                     # timeslot_to = timeslotto.strftime("%I:%M %p")

#                                     formatted_rescheduled_date = datetime.strptime(formated_date, "%Y-%m-%d %H:%M:%S")
#                                     date = formatted_rescheduled_date.strftime("%d-%m-%Y")

#                                     # Convert time_slot_from and time_slot_to to datetime objects
#                                     timeslot_from = datetime.strptime(time_slot_from, "%H:%M:%S")
#                                     timeslot_from = timeslot_from.strftime("%I:%M %p")

#                                     timeslot_to = datetime.strptime(time_slot_to, "%H:%M:%S")
#                                     timeslot_to = timeslot_to.strftime("%I:%M %p")

#                                     message = f" Dear {customer_name}, your pickup with booking ID {booking_id} is rescheduled to {date} between {timeslot_from} to {timeslot_to}."

#                                     headers = {'Content-Type': 'application/json',
#                                                'api_key': "c3bbd214b7f7439f60fa36ba"}

#                                     # Based on the environment, API URL will be changed.

#                                     api_url = 'https://apps.fabricspa.com/Mobile_Controller/send_promotional_notification'

#                                     json_request = {"mobile_number": str(mobile_number), "message": message,
#                                                     "screen": "active_pickup",
#                                                     "image_url": "",'source': 'Fabxpress'}
#                                     query = f"EXEC CustomerApp.[dbo].[GetBrandName] @BranchCode='{branch_code}', @EGRNNo=NULL, @PickupRequestId=NULL"
#                                     brand_details = CallSP(query).execute().fetchone()
#                                     log_data = {
#                                                 'query of brand': query,
#                                                 'result of brand': brand_details,
#                                                 'json_request reschedule pickup': json_request

#                                             }
#                                     info_logger(f'Route: {request.path}').info(json.dumps(log_data))

#                                     if brand_details["BrandDescription"] == 'FABRICSPA':
#                                         # Calling the API.
#                                         response = requests.post(api_url, data=json.dumps(json_request), headers=headers)

                                   

#                                     if first_time_assign and formatted_rescheduled_date <= get_today():
#                                         # Check if the rescheduled pickup date is today.
#                                         # If the pickup rescheduled date is today, and current time is past 9'o clock,
#                                         # needs to trigger the alert engine SP to send the SMS for pickup.
#                                         if reschedule_reason_id != 9 or message == True:
#                                             store_controller_queries.trigger_out_for_activity_sms(
#                                                 'OUT_FOR_PICKUP',
#                                                 pickup_request_details.CustomerId,
#                                                 pickup_request_details.BookingId, None)

#                                     if pickup_request_details.BookingId is not None:
#                                         # Informing the POS about the pickup rescheduling.
#                                         common_module.notify_pos_regarding_pickup_reschedule_or_cancel(
#                                             pickup_request_id,
#                                             pickup_request_details.BookingId, 0, is_reschedule, is_cob)
#                                 else:
#                                     if not error_msg:
#                                         error_msg = 'This delivery user/time slot does not belong to this branch.'
#                             else:
#                                 error_msg = 'This is a branch holiday. Please choose another date.'
#                         else:
#                             if rescheduled_date is None:
#                                 rescheduled_date = pickup_reschedule.RescheduledDate

#                                 input_date = datetime.strptime(str(rescheduled_date), "%Y-%m-%d")
#                                 rescheduled_date = input_date.strftime("%d-%m-%Y")
#                                 rescheduled_date_obj = datetime.strptime(rescheduled_date, "%d-%m-%Y")
#                                 # From the date object, convert the date to YYYY-MM-DD format.
#                                 formatted_rescheduled_date = rescheduled_date_obj.strftime("%Y-%m-%d %H:%M:%S")
#                             # Pickup reschedule is already present.

#                             # Check if the given date is a branch holiday or not.
#                             if branch_code is None:
#                                 # No branch code is provided.
#                                 reschedule_branch_code = pickup_reschedule.BranchCode
#                             else:
#                                 # Branch code is given.
#                                 reschedule_branch_code = branch_code

#                             # Check if the given date is a branch holiday or not.
#                             holiday = delivery_controller_queries.check_branch_holiday(rescheduled_date,
#                                                                                        reschedule_branch_code)
#                             if not holiday:
#                                 # The given date is not a branch holiday. So allow to reschedule.

#                                 # Checking the delivery user can be assigned to this reschedule or not.
#                                 if delivery_user_id is None:
#                                     # No delivery user is provided. Here, the delivery user is the rescheduled delivery user.
#                                     delivery_user_id = pickup_reschedule.DUserId

#                                 if delivery_user_id is not None:
#                                     delivery_user = db.session.query(DeliveryUser).filter(
#                                         DeliveryUser.DUserId == delivery_user_id).one_or_none()

#                                     if delivery_user is not None:

#                                         # If the rescheduled date is today, check if the
#                                         # if the delivery user is clocked in for today
#                                         if formatted_rescheduled_date == get_today():

#                                             # Check whether the delivery user is clocked in or not.
#                                             delivery_user_attendance = db.session.query(
#                                                 DeliveryUserAttendance.ClockInTime).filter(
#                                                 DeliveryUserAttendance.Date == get_today(),
#                                                 DeliveryUserAttendance.DUserId == delivery_user_id).one_or_none()

#                                             if delivery_user_attendance is not None:
#                                                 clocked_in_check = True
#                                             else:
#                                                 # Delivery user has not clocked in yet for the day.
#                                                 pass
#                                         else:
#                                             # This is a future date. Clocked in restriction can not be enforced here.
#                                             clocked_in_check = True
#                                         if clocked_in_check:
#                                             # Checking whether the branch code is provided or not.
#                                             # Getting the branch codes associated with the delivery user.
#                                             delivery_user_branch_codes = delivery_controller_queries.get_delivery_user_branches(
#                                                 delivery_user.DUserId)

#                                             if branch_code is not None:
#                                                 # Here, a branch code is provided. The given branch code must be belong
#                                                 # to the delivery user.

#                                                 if branch_code in delivery_user_branch_codes:
#                                                     # The delivery user can be assigned.
#                                                     valid_delivery_user = True

#                                                 # Checking whether the given time slot id is belong to this branch or not.
#                                                 pickup_time_slot = db.session.query(
#                                                     PickupTimeSlot.PickupTimeSlotId).filter(
#                                                     and_(PickupTimeSlot.TimeSlotFrom == time_slot_from,
#                                                          PickupTimeSlot.TimeSlotTo == time_slot_to),
#                                                     PickupTimeSlot.BranchCode == branch_code,
#                                                     PickupTimeSlot.IsDeleted == 0,
#                                                     or_(PickupTimeSlot.VisibilityFlag == 1,
#                                                         PickupTimeSlot.DefaultFlag == 1)).one_or_none()

#                                                 if pickup_time_slot is not None:
#                                                     valid_time_slot = True
#                                                     time_slot_id = pickup_time_slot.PickupTimeSlotId
#                                                 else:
#                                                     valid_time_slot = True
#                                                     time_slot_id = pickup_reschedule.PickupTimeSlotId

#                                             else:
#                                                 # No branch code is given. So the given delivery user must belong
#                                                 # to the reschedule pickup request's branch code.
#                                                 if pickup_reschedule.BranchCode in delivery_user_branch_codes:
#                                                     # The delivery user can be assigned.
#                                                     valid_delivery_user = True

#                                                 # # Checking whether the given time slot id is belong to this branch or not.
#                                                 pickup_time_slot = db.session.query(
#                                                     PickupTimeSlot.PickupTimeSlotId).filter(
#                                                     and_(PickupTimeSlot.TimeSlotFrom == time_slot_from,
#                                                          PickupTimeSlot.TimeSlotTo == time_slot_to),
#                                                     PickupTimeSlot.BranchCode == pickup_reschedule.BranchCode,
#                                                     PickupTimeSlot.IsDeleted == 0,
#                                                     or_(PickupTimeSlot.VisibilityFlag == 1,
#                                                         PickupTimeSlot.DefaultFlag == 1)).one_or_none()
#                                                 if pickup_time_slot is not None:
#                                                     valid_time_slot = True
#                                                     time_slot_id = pickup_time_slot.PickupTimeSlotId

#                                                 else:
#                                                     valid_time_slot = True
#                                                     time_slot_id = pickup_reschedule.PickupTimeSlotId
#                                         else:
#                                             error_msg = "Delivery user has not clocked in for the day."
#                                     else:
#                                         error_msg = "Delivery user is not found."
#                                 else:
#                                     error_msg = "Delivery user is not found."

#                                 if valid_delivery_user and valid_time_slot:
#                                     # If the optional fields are None, fill up with the existing details.
#                                     if branch_code is None:
#                                         branch_code = pickup_reschedule.BranchCode

#                                     # if address_id is None:
#                                     address_id = pickup_reschedule.CustAddressId

#                                     if delivery_user_id is None:
#                                         delivery_user_id = pickup_reschedule.DUserId

#                                     # Delete the row and insert again.
#                                     pickup_reschedule.IsDeleted = 1
#                                     pickup_reschedule.CancelledDate = get_current_date()
#                                     db.session.commit()

#                                     # After making the previous reschedule delete, create a new entry in
#                                     # the PickupReschedules table.
#                                     new_reschedule = PickupReschedule(PickupRequestId=pickup_request_id,
#                                                                       RescheduleReasonId=reschedule_reason_id,
#                                                                       RescheduledDate=formatted_rescheduled_date,
#                                                                       PickupTimeSlotId=time_slot_id,
#                                                                       TimeSlotFrom=time_slot_from,
#                                                                       TimeSlotTo=time_slot_to,
#                                                                       BranchCode=branch_code,
#                                                                       CustAddressId=address_id,
#                                                                       RescheduleRemarks=remarks,
#                                                                       RescheduledStoreUser=user_id,
#                                                                       RescheduledBy=modified_name[0]
#                                                                       )

#                                     db.session.add(new_reschedule)
#                                     if formatted_rescheduled_date <= get_today():
#                                         new_reschedule.DUserId = delivery_user_id
#                                     else:
#                                         pickup_request_details.DUserId = None
#                                     db.session.commit()

#                                     # Updating the RecordLastUpdatedDate in the pickup request table.
#                                     pickup_request_details.RecordLastUpdatedDate = get_current_date()
#                                     # Updating the reschedule flag in the PickupRequests table.
#                                     pickup_request_details.IsRescheduled = 1

#                                     pickup_request_details.ReschuduleStatus = 1
#                                     pickup_request_details.ReschuduleDate = formatted_rescheduled_date
#                                     pickup_request_details.ReschuduleBy = delivery_user_id
#                                     pickup_request_details.ReschuduleAddressId = address_id
#                                     pickup_request_details.ReschuduleModifiedDate = get_current_date()
#                                     pickup_request_details.ReschuduleTimeSlotId = time_slot_id
#                                     pickup_request_details.ReschuduleTimeSlotFrom = time_slot_from
#                                     pickup_request_details.ReschuduleTimeSlotTo = time_slot_to
#                                     pickup_request_details.DUserId = delivery_user_id
#                                     db.session.commit()

#                                     is_rescheduled = True

#                                     log_data = {
#                                         'json_request reschedule pickup2': 'testt2',

#                                     }
#                                     info_logger(f'Route: {request.path}').info(json.dumps(log_data))

#                                     customer_id = db.session.query(PickupRequest.CustomerId).filter(
#                                         PickupRequest.PickupRequestId == pickup_request_id).first()
#                                     if customer_id is not None:
#                                         customer_id = customer_id[0]

#                                     customer_name = db.session.query(Customer.CustomerName).filter(
#                                         Customer.CustomerId == customer_id).first()
#                                     if customer_name:
#                                         customer_name = customer_name[0]
#                                         print(customer_name)
#                                     mobile_number = db.session.query(Customer.MobileNo).filter(
#                                         Customer.CustomerId == customer_id).first()
#                                     if mobile_number:
#                                         mobile_number = mobile_number[0]
#                                         print(mobile_number)
#                                     booking_id = db.session.query(PickupRequest.BookingId).filter(
#                                         PickupRequest.PickupRequestId == pickup_request_id).first()
#                                     if booking_id is not None:
#                                         booking_id = booking_id[0]

#                                     formated_date = formatted_rescheduled_date
#                                     timeslot_from = time_slot_from
#                                     timeslot_to = time_slot_to

#                                     # formatted_rescheduled_date = datetime.strptime(formated_date, "%Y-%m-%d %H:%M:%S")

#                                     # date = formatted_rescheduled_date.strftime("%d-%m-%Y ")

#                                     # timeslotfrom = timeslot_from.strftime("%H:%M:%S")

#                                     # timeslot_from = datetime.strptime(timeslotfrom, "%H:%M:%S")
#                                     # timeslot_from = timeslot_from.strftime("%I:%M %p")

#                                     # timeslot_to = timeslot_to.strftime("%H:%M:%S")
#                                     # timeslotto = datetime.strptime(timeslot_to, "%H:%M:%S")
#                                     # timeslot_to = timeslotto.strftime("%I:%M %p")
#                                     formatted_rescheduled_date = datetime.strptime(formated_date, "%Y-%m-%d %H:%M:%S")
#                                     date = formatted_rescheduled_date.strftime("%d-%m-%Y")

#                                     # Convert time_slot_from and time_slot_to to datetime objects
#                                     timeslot_from = datetime.strptime(time_slot_from, "%H:%M:%S")
#                                     timeslot_from = timeslot_from.strftime("%I:%M %p")

#                                     timeslot_to = datetime.strptime(time_slot_to, "%H:%M:%S")
#                                     timeslot_to = timeslot_to.strftime("%I:%M %p")

#                                     message = f" Dear {customer_name}, your pickup with booking ID {booking_id} is rescheduled to {date} between {timeslot_from} to {timeslot_to}."

#                                     headers = {'Content-Type': 'application/json',
#                                                'api_key': "c3bbd214b7f7439f60fa36ba"}

#                                     # Based on the environment, API URL will be changed.

#                                     api_url = 'https://apps.fabricspa.com/Mobile_Controller/send_promotional_notification'

#                                     json_request = {"mobile_number": str(mobile_number), "message": message,
#                                                     "screen": "active_pickup",
#                                                     "image_url": "",'source': 'Fabxpress'}
#                                     query = f"EXEC CustomerApp.[dbo].[GetBrandName] @BranchCode='{branch_code}', @EGRNNo=NULL, @PickupRequestId=NULL"
#                                     brand_details = CallSP(query).execute().fetchone()
#                                     log_data = {
#                                                 'query of brand': query,
#                                                 'result of brand': brand_details,
#                                                 'json_request reschedule pickup': json_request

#                                             }
#                                     info_logger(f'Route: {request.path}').info(json.dumps(log_data))

#                                     if brand_details["BrandDescription"] == 'FABRICSPA':

#                                         # Calling the API.
#                                         response = requests.post(api_url, data=json.dumps(json_request), headers=headers)

                                   

#                                 if pickup_request_details.BookingId is not None:
#                                     # Informing the POS about the pickup rescheduling.
#                                     common_module.notify_pos_regarding_pickup_reschedule_or_cancel(
#                                         pickup_request_id,
#                                         pickup_request_details.BookingId, 0, is_reschedule, is_cob)
#                                 else:
#                                     if not error_msg:
#                                         error_msg = 'This delivery user/time slot does not belong to this branch.'
#                             else:
#                                 error_msg = 'This is a branch holiday. Please choose another date.'

#                     # If any error_msg are found, break from the loop.
#                     if error_msg:
#                         break

#             except Exception as e:
#                 db.session.rollback()
#                 error_logger(f'Route: {request.path}').error(e)

#             if is_rescheduled:
#                 final_data = generate_final_data('DATA_UPDATED')

#                 formatted_rescheduled_date_str = formatted_rescheduled_date.strftime("%Y-%m-%d %H:%M:%S")
#                 # Invoke push notification if the delivery is scheduled for today or lesser
#                 formatted_rescheduled_date = datetime.strptime(formatted_rescheduled_date_str, "%Y-%m-%d %H:%M:%S")

#                 current_date_str = datetime.now()
#                 # today_date_obj = datetime.strptime(current_date_str, "%Y-%m-%d %H:%M:%S")
#                 if formatted_rescheduled_date <= current_date_str:
#                     send_push_notification_test(delivery_user_id, 'PICKUP', None, "JFSLSTORE", user_id)
#             else:
#                 if error_msg:
#                     final_data = generate_final_data('CUSTOM_FAILED', error_msg)
#                 else:
#                     final_data = generate_final_data('DATA_UPDATE_FAILED')
#         else:
#             final_data = generate_final_data('CUSTOM_FAILED', 'Delivery user is inactive')
#     else:
#         # Form validation error.
#         final_data = generate_final_data('FORM_ERROR')
#         final_data['errors'] = populate_errors(reschedule_form.errors)

#     return final_data
@store_console_blueprint.route('/reschedule_pickup', methods=["POST"])
# @authenticate('store_user')
def reschedule_pickup_():
    """
    API for rescheduling a pickup request.
    """
    reschedule_form = ReschedulePickupForm()
    user_id = request.headers.get('user-id')
    if reschedule_form.validate_on_submit():
        BookingIds = reschedule_form.BookingId.data
        reschedule_reason_id = reschedule_form.reschedule_reason_id.data
        rescheduled_date = '' if reschedule_form.rescheduled_date.data == '' else reschedule_form.rescheduled_date.data
        CustomerNames = reschedule_form.CustomerName.data
        MobileNos = reschedule_form.MobileNo.data
        time_slot_id = reschedule_form.time_slot_id.data
        delivery_user_id = '' if reschedule_form.delivery_user_id.data == '' else reschedule_form.delivery_user_id.data
        remarks = '' if reschedule_form.remarks.data == '' else reschedule_form.remarks.data
        TimeSlotFrom ='' if reschedule_form.TimeSlotFrom.data == '' else reschedule_form.TimeSlotFrom.data
        TimeSlotTo = '' if reschedule_form.TimeSlotTo.data == '' else reschedule_form.TimeSlotTo.data
        BranchCode = '' if reschedule_form.BranchCode.data == '' else reschedule_form.BranchCode.data
        CustomerCodes = '' if reschedule_form.CustomerCode.data == '' else reschedule_form.CustomerCode.data
        is_cob = reschedule_form.is_cob.data
        formatted_rescheduled_date = None
       
        rescheduled_date_obj = datetime.strptime(rescheduled_date, "%d-%m-%Y")
        formatted_rescheduled_date = rescheduled_date_obj.strftime("%Y-%m-%d %H:%M:%S")
        
        is_rescheduled = False
        log_data = {
                    'reschedule_form': reschedule_form.data,
                   
                }
        info_logger(f'Route: {request.path}').info(json.dumps(log_data))

        try:
            for i in range(len(BookingIds)):
                BookingId = BookingIds[i]
                MobileNo = MobileNos[i]
                CustomerName = CustomerNames[i]
                query = f""" EXEC JFSL.Dbo.[SPPickupRescheduleUpdateCustApp] @DuserId = {delivery_user_id}, @BookingID ={BookingId},@BranchCode ='{BranchCode[0]}'   
                            ,@PickupTimeSlotId = {time_slot_id},@TimeSlotFrom = '{TimeSlotFrom}',@TimeSlotTo = '{TimeSlotTo}'      
                            ,@ReschuduleDate = '{formatted_rescheduled_date}' ,@ReschuduleReasonID ={reschedule_reason_id}, @RescheduleRemarks = '{remarks}'
                            ,@StoreUserID  = '{user_id}',@ISCOB={is_cob}"""
                log_data = {
                    'query': query,
                   
                }
                info_logger(f'Route: {request.path}').info(json.dumps(log_data))
                db.engine.execute(text(query).execution_options(autocommit=True))
                is_rescheduled = True
                message = f" Dear {CustomerName}, your pickup with booking ID {BookingId} is rescheduled to {rescheduled_date} between {TimeSlotFrom} to {TimeSlotTo}."
                print(message)
                headers = {'Content-Type': 'application/json',
                           'api_key': "c3bbd214b7f7439f60fa36ba"}
                api_url = 'https://apps.fabricspa.com/Mobile_Controller/send_promotional_notification'

                json_request = {"mobile_number": str(MobileNo), "message": message,
                                "screen": "active_pickup",
                                "image_url": "", 'source': 'fabxpress'}
                query = f"EXEC CustomerApp.[dbo].[GetBrandName] @BranchCode='{BranchCode[0]}', @EGRNNo=NULL, @PickupRequestId=NULL"
                brand_details = CallSP(query).execute().fetchone()
                log_data = {
                    'query of brand': query,
                    'result of brand': brand_details
                }
                info_logger(f'Route: {request.path}').info(json.dumps(log_data))

                if brand_details["BrandDescription"] == 'FABRICSPA':
                    # Calling the API.
                    response = requests.post(api_url, data=json.dumps(json_request),
                                             headers=headers)

                rescheduled_date_obj = datetime.strptime(rescheduled_date, "%d-%m-%Y")
                if rescheduled_date_obj <= datetime.now():
                    if reschedule_reason_id != 9:
                        booking_id = BookingId
                        store_controller_queries.trigger_out_for_activity_sms(
                            'OUT_FOR_PICKUP',
                            CustomerName,
                            booking_id,MobileNo,None)

                    send_push_notification_test(delivery_user_id, 'PICKUP', None, "JFSLSTORE", user_id)
        except Exception as e:
            error_logger(f'Route: {request.path}').error(e)
        if is_rescheduled:
            final_data = generate_final_data('DATA_UPDATED')
            current_date_str = datetime.now()

        else:
            final_data = generate_final_data('DATA_UPDATE_FAILED')
    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(reschedule_form.errors)
    return final_data


# @store_console_blueprint.route('/cancel_pickup_uat', methods=["POST"])
# @authenticate('store_user')
# def cancel_pickup_uat():
#     """
#     API for cancelling a pickup request.
#     @return:
#     """
#     cancel_form = CancelPickupForm()

#     log_data = {
#         'cancel_form': cancel_form.data

#     }
#     info_logger(f'Route: {request.path}').info(json.dumps(log_data))

#     is_cancelled = False
#     user_id = request.headers.get('user-id')
#     if cancel_form.validate_on_submit():
#         pickup_request_id = cancel_form.pickup_request_id.data
#         cancel_reason_id = cancel_form.cancel_reason_id.data
#         cancel_remarks = cancel_form.cancel_remarks.data
#         try:
#             # Getting the pickup request details
#             pickup_request = db.session.query(PickupRequest).outerjoin(Order,
#                                                                        Order.PickupRequestId == PickupRequest.PickupRequestId).filter(
#                 PickupRequest.PickupRequestId == pickup_request_id, PickupRequest.IsCancelled == 0,
#                 or_(Order.OrderId == None, Order.IsDeleted == 1)).one_or_none()

#             if pickup_request is not None:
#                 # Updating the IsCancelled and CancelReasonId in the PickupRequest table.
#                 pickup_request.IsCancelled = 1
#                 # Status 4 is for the cancelled ones.
#                 pickup_request.PickupStatusId = 4
#                 pickup_request.CancelReasonId = cancel_reason_id
#                 pickup_request.CancelledDate = get_current_date()
#                 pickup_request.CancelledStoreUser = user_id
#                 pickup_request.RecordLastUpdatedDate = get_current_date()
#                 pickup_request.CancelRemarks = cancel_remarks
#                 db.session.commit()
#                 is_cancelled = True

#                 log_data = {
#                     'cancel_form': "cancel_form.data"

#                 }
#                 info_logger(f'Route: {request.path}').info(json.dumps(log_data))

#                 booking_id = db.session.query(PickupRequest.BookingId).filter(
#                     PickupRequest.PickupRequestId == pickup_request_id).first()
#                 if booking_id is not None:
#                     booking_id = booking_id[0]

#                 customer_id = db.session.query(PickupRequest.CustomerId).filter(
#                     PickupRequest.PickupRequestId == pickup_request_id).first()
#                 if customer_id is not None:
#                     customer_id = customer_id[0]

#                 customer_name = db.session.query(Customer.CustomerName).filter(
#                     Customer.CustomerId == customer_id).first()
#                 if customer_name:
#                     customer_name = customer_name[0]
#                     print(customer_name)
#                 mobile_number = db.session.query(Customer.MobileNo).filter(
#                     Customer.CustomerId == customer_id).first()
#                 if mobile_number:
#                     mobile_number = mobile_number[0]
#                     print(mobile_number)

#                 # message = f"Dear {customer_name}, your scheduled pickup for {pickup_request.CancelledDate}under booking ID {booking_id} has been cancelled. To reschedule go to MY ORDERS and follow the steps."
#                 message = f"Dear {customer_name} We regret to inform you that your booking with ID {booking_id} has been cancelled.Please feel free to reschedule your pickup.We are always here to assist you."

#                 headers = {'Content-Type': 'application/json', 'api_key': "c3bbd214b7f7439f60fa36ba"}

#                 # Based on the environment, API URL will be changed.

#                 api_url = 'https://apps.fabricspa.com/Mobile_Controller/send_promotional_notification'

#                 # api_url = 'https://app-staging.fabricspa.com/jfsl/api/generate_payment_link'

#                 json_request = {"mobile_number": str(mobile_number), "message": message, "screen": "cancelled_pickup",
#                                 "image_url": "",'source': 'Fabxpress'}

#                 branch_code = db.session.query(PickupRequest.BranchCode).filter(
#                     PickupRequest.PickupRequestId == pickup_request_id).first()
               
#                 if branch_code:
#                     branch_code = branch_code[0]

#                 query = f"EXEC CustomerApp.[dbo].[GetBrandName] @BranchCode='{branch_code}', @EGRNNo=NULL, @PickupRequestId=NULL"
#                 brand_details = CallSP(query).execute().fetchone()
#                 log_data = {
#                             'query of brand': query,
#                             'result of brand': brand_details,
#                             'json_request':json_request
#                         }
#                 info_logger(f'Route: {request.path}').info(json.dumps(log_data))

#                 if brand_details["BrandDescription"] == 'FABRICSPA':

#                     # Calling the API.
#                     response = requests.post(api_url, data=json.dumps(json_request), headers=headers)
                

#                 if pickup_request.BookingId is not None:
#                     # Informing the POS about the pickup cancellation.
#                     common_module.notify_pos_regarding_pickup_reschedule_or_cancel(
#                         pickup_request_id,
#                         pickup_request.BookingId, 1, 0, 0)
#         except Exception as e:
#             db.session.rollback()
#             error_logger(f'Route: {request.path}').error(e)

#         if is_cancelled:
#             final_data = generate_final_data('DATA_DELETED')
#         else:
#             final_data = generate_final_data('DATA_DELETE_FAILED')
#     else:
#         # Form validation error.
#         final_data = generate_final_data('FORM_ERROR')
#         final_data['errors'] = populate_errors(cancel_form.errors)
#     log_data = {
#         'final_data': final_data
#     }
#     info_logger(f'Route: {request.path}').info(json.dumps(log_data))

#     return final_data

@store_console_blueprint.route('/cancel_pickup', methods=["POST"])
#@authenticate('store_user')
def cancel_pickup():
    """
    API for cancelling a pickup request.
    @return:
    """
    cancel_form = CancelPickupForm()

    log_data = {
        'cancel_form': cancel_form.data

    }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))

    is_cancelled = False
    user_id = request.headers.get('user-id')
    if cancel_form.validate_on_submit():
        booking_id = cancel_form.booking_id.data
        cancel_reason_id = cancel_form.cancel_reason_id.data
        cancel_remarks = cancel_form.cancel_remarks.data
        branch_code = cancel_form.branch_code.data
        customer_name = cancel_form.customer_name.data
        mobile_number = cancel_form.mobile_number.data
        pickup_source_dtls = None
        try:
            # Getting the pickup request details
            # pickup_request = db.session.query(PickupRequest).outerjoin(Order,
            #                                                            Order.PickupRequestId == PickupRequest.PickupRequestId).filter(
            #     PickupRequest.PickupRequestId == pickup_request_id, PickupRequest.IsCancelled == 0,
            #     or_(Order.OrderId == None, Order.IsDeleted == 1)).one_or_none()

            if booking_id is not None:
                log_data = {
                    'test': 'brand'
                }
                info_logger(f'Route: {request.path}').info(json.dumps(log_data))
                # pickup_source_dtls = db.session.query(PickupRequest).filter(
                #     PickupRequest.PickupRequestId == pickup_request.PickupRequestId,
                #     PickupRequest.PickupSource.in_(['Outbound', 'Inbound', 'Direct schedule', 'App Leads', 'Direct Sch'])
                # ).one_or_none()

                pending_pickups_query = f"EXEC CustomerApp.[dbo].[PickupCancelRestrictUsers] @bookingid='{booking_id}'"
                log_data = {
                    'pickup :': pending_pickups_query
                }
                info_logger(f'Route: {request.path}').info(json.dumps(log_data))

                result = CallSP(pending_pickups_query).execute().fetchone()

                log_data = {
                    'pickups :': result
                }
                info_logger(f'Route: {request.path}').info(json.dumps(log_data))
                pickup_source_dtls = result.get("IsExist", 0) if result else 0

                log_data = {
                    'test1': 'brand'
                }
                info_logger(f'Route: {request.path}').info(json.dumps(log_data))
                if pickup_source_dtls == 1:
                    log_data = {
                        'test2': 'brand'
                    }
                    info_logger(f'Route: {request.path}').info(json.dumps(log_data))

                    return generate_final_data('CUSTOM_FAIL')
                else:
                    cancel_pickups_query = f"EXEC JFSL.[dbo].[SPPickupCancelledUpdateCustApp] @DuserId = {user_id}, @IsCancelled = 1,  @BookingID = {booking_id}, @CancelReasonID = {cancel_reason_id}, @CancelRemarks = '{cancel_remarks}', @StoreUserID = {user_id}"
                    db.engine.execute(text(cancel_pickups_query).execution_options(autocommit=True))
                    log_data = {
                        'cancel or reschedule pickup': cancel_pickups_query
                    }
                    info_logger(f'Route: {request.path}').info(json.dumps(log_data))

                    is_cancelled = True

                    log_data = {
                        'cancel_form': "cancel_form.data"

                    }
                    info_logger(f'Route: {request.path}').info(json.dumps(log_data))


                    if customer_name is not None:
                        customer_name = customer_name

                    if mobile_number:
                        mobile_number = mobile_number
                        # print(mobile_number)

                    # message = f"Dear {customer_name}, your scheduled pickup for {pickup_request.CancelledDate}under booking ID {booking_id} has been cancelled. To reschedule go to MY ORDERS and follow the steps."
                    message = f"Dear {customer_name} We regret to inform you that your booking with ID {booking_id} has been cancelled.Please feel free to reschedule your pickup.We are always here to assist you."

                    headers = {'Content-Type': 'application/json', 'api_key': "c3bbd214b7f7439f60fa36ba"}

                    # Based on the environment, API URL will be changed.

                    api_url = 'https://intapps.fabricspa.com/jfsl/api/generate_payment_link'

                    # api_url = 'https://app-staging.fabricspa.com/jfsl/api/generate_payment_link'

                    json_request = {"mobile_number": str(mobile_number), "message": message,
                                    "screen": "cancelled_pickup",
                                    "image_url": "", 'source': 'Fabxpress'}

                    if branch_code:
                        branch_code = branch_code

                    query = f"EXEC CustomerApp.[dbo].[GetBrandName] @BranchCode='{branch_code}', @EGRNNo=NULL, @PickupRequestId=NULL"
                    brand_details = CallSP(query).execute().fetchone()
                    log_data = {
                        'query of brand': query,
                        'result of brand': brand_details,
                        'json_request': json_request
                    }
                    info_logger(f'Route: {request.path}').info(json.dumps(log_data))

                    if brand_details["BrandDescription"] == 'FABRICSPA':
                        # Calling the API.
                        response = requests.post(api_url, data=json.dumps(json_request), headers=headers)



        except Exception as e:
            db.session.rollback()
            error_logger(f'Route: {request.path}').error(e)

        if is_cancelled:
            final_data = generate_final_data('DATA_DELETED')
        else:
            if pickup_source_dtls == 1:
                log_data = {
                    'test5': 'brand'
                }
                info_logger(f'Route: {request.path}').info(json.dumps(log_data))
                final_data = generate_final_data('CUSTOM_FAIL')
            else:
                final_data = generate_final_data('DATA_DELETE_FAILED')
    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(cancel_form.errors)
    log_data = {
        'final_data': final_data
    }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))

    return final_data


@store_console_blueprint.route('/get_paginated_pending_activitie', methods=["POST"])
# @authenticate('store_user')
def get_paginated_pending_activitie():
    """
        API for getting the pending activities in a branch.
        @return:
        """
    pending_activities_form = GetPendingActivitiesForm()
    if pending_activities_form.validate_on_submit():
        from_date = None if pending_activities_form.from_date.data == '' else pending_activities_form.from_date.data
        to_date = None if pending_activities_form.to_date.data == '' else pending_activities_form.to_date.data
        unassigned_only = pending_activities_form.unassigned_only.data
        branch_codes = pending_activities_form.branch_codes.data
        late_only = pending_activities_form.late_only.data
        report = pending_activities_form.report.data
        pending_activities = []
        user_id = request.headers.get('user-id')
        page = pending_activities_form.page.data
        filter_type = None if pending_activities_form.filter_type.data == '' else pending_activities_form.filter_type.data
        search = None if pending_activities_form.search.data == '' else pending_activities_form.search.data
        per_page = 50
        empty_date = 0
        if from_date is not None:
            start_date_obj = datetime.strptime(from_date, "%Y-%m-%d")
            from_date = start_date_obj.strftime("%Y-%m-%d %H:%M:%S")
            end_date_obj = datetime.strptime(to_date, "%Y-%m-%d")
            to_date = (end_date_obj + timedelta(1)).strftime("%Y-%m-%d %H:%M:%S")
            # to_date = end_date_obj.strftime("%Y-%m-%d %H:%M:%S")
        else:
            # pass
            # from_date = (datetime.today() - timedelta(8)).strftime("%Y-%m-%d %H:%M:%S")
            from_date = (datetime.today() - timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
            to_date = get_current_date()
            empty_date = 1
        try:
            if not branch_codes:
                # Getting the branches associated with the user.
                # Edited by MMM
                store_user_branches = store_controller_queries.get_store_user_branches(user_id)
                store_user_all_branches = store_controller_queries.get_store_user_branches(user_id, None, None, True)
            else:
                store_user_branches = branch_codes
                store_user_all_branches = branch_codes
            # print(store_user_branches)
            if not branch_codes:
                # branches = ''
                branches = ','.join(store_user_all_branches)
            else:
                branches = ','.join(store_user_branches)

            try:
                log_data = {
                    'BRANCHES :': branches
                }
                info_logger(f'Route: {request.path}').info(json.dumps(log_data))
                # @activitytype='Pickup'
                if unassigned_only:
                    status_type = 'UN-ASSIGNED'
                    if (filter_type == None):
                        if empty_date == 1:
                            pending_pickups_query = f"EXEC CustomerApp.dbo.PendingActivity @branch = '{branches}',@activitytype='',@Status_type = '{status_type}'"
                        else:
                            pending_pickups_query = f"EXEC CustomerApp.dbo.PendingActivity @fromdate='{from_date}',@todate='{to_date}',@branch = '{branches}',@activitytype='',@Status_type = '{status_type}'"
                    else:
                        if empty_date == 1:
                            pending_pickups_query = f"EXEC CustomerApp.dbo.PendingActivity @branch = '{branches}',@activitytype='{filter_type}',@Status_type = '{status_type}'"
                        else:
                            pending_pickups_query = f"EXEC CustomerApp.dbo.PendingActivity @fromdate='{from_date}',@todate='{to_date}',@branch = '{branches}',@activitytype='{filter_type}',@Status_type = '{status_type}'"
                else:
                    status_type = 'PENDING'
                    if (filter_type == None):
                        if empty_date == 1:
                            pending_pickups_query = f"EXEC CustomerApp.dbo.PendingActivity @branch = '{branches}',@activitytype='',@Status_type = '{status_type}'"
                        else:
                            pending_pickups_query = f"EXEC CustomerApp.dbo.PendingActivity @fromdate='{from_date}',@todate='{to_date}',@branch = '{branches}',@activitytype='',@Status_type = '{status_type}'"
                    else:
                        if empty_date == 1:
                            pending_pickups_query = f"EXEC CustomerApp.dbo.PendingActivity @branch = '{branches}',@activitytype='{filter_type}',@Status_type = '{status_type}'"
                        else:
                            pending_pickups_query = f"EXEC CustomerApp.dbo.PendingActivity @fromdate='{from_date}',@todate='{to_date}',@branch = '{branches}',@activitytype='{filter_type}',@Status_type = '{status_type}'"
                    # CustomerApp.[dbo].[PendingActivity] @ fromdate = '2023-11-01',@todate='2024-01-19',@branch =''
                    # print(pending_pickups_query)
                if (late_only):
                    status_type = 'DELAYED'
                    if (filter_type == None):
                        pending_pickups_query = f"EXEC CustomerApp.dbo.PendingActivity @fromdate='{from_date}',@todate='{to_date}',@branch = '{branches}',@activitytype='',@Status_type = '{status_type}'"
                    else:
                        pending_pickups_query = f"EXEC CustomerApp.dbo.PendingActivity @fromdate='{from_date}',@todate='{to_date}',@branch = '{branches}',@activitytype='{filter_type}',@Status_type = '{status_type}'"

                log_data = {
                    'Pending_pickupSP qry :': pending_pickups_query
                    # 'Pending_pickupSP qry :' 'HIII'
                }
                info_logger(f'Route: {request.path}').info(json.dumps(log_data))

                pending_activities = CallSP(pending_pickups_query).execute().fetchall_by_date()
                # pending_activities = CallSP(pending_pickups_query).execute().fetchall()

                # print(pending_activities)
                # log_data = {
                #     'Pending_pickupSP result :': pending_activities
                # }
                # info_logger(f'Route: {request.path}').info(json.dumps(log_data))

                # print(pending_activities)
                db.session.commit()
            except Exception as e:
                print(e)
        except Exception as e:
            print(e)
        if pending_activities:
            final_data = generate_final_data('DATA_FOUND')
            if report:
                # Report flag is included in the request. So generate the file and send the file back.
                report_link = GenerateReport(pending_activities, 'pending').generate().get()
                if report_link is not None:
                    final_data['result'] = report_link
                else:
                    # Failed to generate the file.
                    final_data = generate_final_data('FILE_NOT_FOUND')
            else:
                final_data['result'] = pending_activities
        else:
            final_data = generate_final_data('DATA_NOT_FOUND')
    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(pending_activities_form.errors)

    return final_data

@store_console_blueprint.route('/get_paginated_pending_activities', methods=["POST"])
# @authenticate('store_user')
def get_paginated_pending_activities():
    """
        API for getting the pending activities in a branch.
        @return:
        """
    pending_activities_form = GetPendingActivitiesForm()
    if pending_activities_form.validate_on_submit():
        from_date = None if pending_activities_form.from_date.data == '' else pending_activities_form.from_date.data
        to_date = None if pending_activities_form.to_date.data == '' else pending_activities_form.to_date.data
        unassigned_only = pending_activities_form.unassigned_only.data
        branch_codes = pending_activities_form.branch_codes.data
        late_only = pending_activities_form.late_only.data
        report = pending_activities_form.report.data
        pending_activities = []
        user_id = request.headers.get('user-id')
        page = pending_activities_form.page.data
        filter_type = None if pending_activities_form.filter_type.data == '' else pending_activities_form.filter_type.data
        search = None if pending_activities_form.search.data == '' else pending_activities_form.search.data
        per_page = 50
        empty_date = 0
        if from_date is not None:
            start_date_obj = datetime.strptime(from_date, "%Y-%m-%d")
            from_date = start_date_obj.strftime("%Y-%m-%d %H:%M:%S")
            end_date_obj = datetime.strptime(to_date, "%Y-%m-%d")
            to_date = (end_date_obj + timedelta(1)).strftime("%Y-%m-%d %H:%M:%S")
            # to_date = end_date_obj.strftime("%Y-%m-%d %H:%M:%S")
        else:
            # pass
            # from_date = (datetime.today() - timedelta(8)).strftime("%Y-%m-%d %H:%M:%S")
            from_date = (datetime.today() - timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
            to_date = get_current_date()
            empty_date = 1
        try:
            if not branch_codes:
                # Getting the branches associated with the user.
                # Edited by MMM
                store_user_branches = store_controller_queries.get_store_user_branches(user_id)
                store_user_all_branches = store_controller_queries.get_store_user_branches(user_id, None, None, True)
            else:
                store_user_branches = branch_codes
                store_user_all_branches = branch_codes
            # print(store_user_branches)
            if not branch_codes:
                # branches = ''
                branches = ','.join(store_user_all_branches)
            else:
                branches = ','.join(store_user_branches)

            try:
                log_data = {
                    'BRANCHES :': branches
                }
                info_logger(f'Route: {request.path}').info(json.dumps(log_data))
                # @activitytype='Pickup'
                if unassigned_only:
                    status_type = 'UN-ASSIGNED'
                    if (filter_type == None):
                        if empty_date == 1:
                            pending_pickups_query = f"EXEC JFSL.dbo.SPFabUnAssiginedActivity @branch = '{branches}',@activitytype='',@Status_type = '{status_type}'"
                        else:
                            pending_pickups_query = f"EXEC JFSL.dbo.SPFabUnAssiginedActivity @fromdate='{from_date}',@todate='{to_date}',@branch = '{branches}',@activitytype='',@Status_type = '{status_type}'"
                    else:
                        if empty_date == 1:
                            pending_pickups_query = f"EXEC JFSL.dbo.SPFabUnAssiginedActivity @branch = '{branches}',@activitytype='{filter_type}',@Status_type = '{status_type}'"
                        else:
                            pending_pickups_query = f"EXEC JFSL.dbo.SPFabUnAssiginedActivity @fromdate='{from_date}',@todate='{to_date}',@branch = '{branches}',@activitytype='{filter_type}',@Status_type = '{status_type}'"
                else:
                    status_type = 'PENDING'
                    if (filter_type == None):
                        if empty_date == 1:
                            pending_pickups_query = f"EXEC JFSL.dbo.SPFabPendingActivity @branch = '{branches}',@activitytype='',@Status_type = '{status_type}'"
                        else:
                            pending_pickups_query = f"EXEC JFSL.dbo.SPFabPendingActivity @fromdate='{from_date}',@todate='{to_date}',@branch = '{branches}',@activitytype='',@Status_type = '{status_type}'"
                    else:
                        if empty_date == 1:
                            pending_pickups_query = f"EXEC JFSL.dbo.SPFabPendingActivity @branch = '{branches}',@activitytype='{filter_type}',@Status_type = '{status_type}'"
                        else:
                            pending_pickups_query = f"EXEC JFSL.dbo.SPFabPendingActivity @fromdate='{from_date}',@todate='{to_date}',@branch = '{branches}',@activitytype='{filter_type}',@Status_type = '{status_type}'"
                    # CustomerApp.[dbo].[PendingActivity] @ fromdate = '2023-11-01',@todate='2024-01-19',@branch =''
                    # print(pending_pickups_query)
                if (late_only):
                    status_type = 'DELAYED'
                    if (filter_type == None):
                        pending_pickups_query = f"EXEC JFSL.dbo.SPFabDelayedActivity @fromdate='{from_date}',@todate='{to_date}',@branch = '{branches}',@activitytype='',@Status_type = '{status_type}'"
                    else:
                        pending_pickups_query = f"EXEC JFSL.dbo.SPFabDelayedActivity @fromdate='{from_date}',@todate='{to_date}',@branch = '{branches}',@activitytype='{filter_type}',@Status_type = '{status_type}'"

                log_data = {
                    'Pending_pickupSP qry :': pending_pickups_query
                    # 'Pending_pickupSP qry :' 'HIII'
                }
                info_logger(f'Route: {request.path}').info(json.dumps(log_data))

                pending_activities = CallSP(pending_pickups_query).execute().fetchall_by_date()
                # pending_activities = CallSP(pending_pickups_query).execute().fetchall()

                # print(pending_activities)
                # log_data = {
                #     'Pending_pickupSP result :': pending_activities
                # }
                # info_logger(f'Route: {request.path}').info(json.dumps(log_data))

                # print(pending_activities)
                db.session.commit()
            except Exception as e:
                print(e)
        except Exception as e:
            print(e)
        if pending_activities:
            final_data = generate_final_data('DATA_FOUND')
            if report:
                # Report flag is included in the request. So generate the file and send the file back.
                report_link = GenerateReport(pending_activities, 'pending').generate().get()
                if report_link is not None:
                    final_data['result'] = report_link
                else:
                    # Failed to generate the file.
                    final_data = generate_final_data('FILE_NOT_FOUND')
            else:
                final_data['result'] = pending_activities
        else:
            final_data = generate_final_data('DATA_NOT_FOUND')
    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(pending_activities_form.errors)

    return final_data




@store_console_blueprint.route('/get_paginated_completed_activities', methods=["POST"])
# @authenticate('store_user')#originel
def get_paginated_completed_activities():
    """
    API for getting the pending activities in a branch.
    @return:
    """
    completed_activities_form = GetCompletedActivitiesForm()
    if completed_activities_form.validate_on_submit():
        from_date = None if completed_activities_form.from_date.data == '' else completed_activities_form.from_date.data
        to_date = None if completed_activities_form.to_date.data == '' else completed_activities_form.to_date.data
        branch_codes = completed_activities_form.branch_codes.data
        report = completed_activities_form.report.data
        # completed_only = completed_activities_form.completed_only.data
        page = completed_activities_form.page.data
        filter_type = None if completed_activities_form.filter_type.data == '' else completed_activities_form.filter_type.data
        search = None if completed_activities_form.search.data == '' else completed_activities_form.search.data
        per_page = 50
        user_id = request.headers.get('user-id')
        completed_activities = []

        if from_date is not None:
            start_date_obj = datetime.strptime(from_date, "%d-%m-%Y")
            from_date = start_date_obj.strftime("%Y-%m-%d %H:%M:%S")
            print(from_date)
            end_date_obj = datetime.strptime(to_date, "%d-%m-%Y")
            to_date = (end_date_obj + timedelta(1)).strftime("%Y-%m-%d %H:%M:%S")
            print(to_date)
        else:
            from_date = (datetime.today() - timedelta(8)).strftime("%Y-%m-%d %H:%M:%S")
            to_date = get_current_date()
        try:
            if not branch_codes:
                # Getting the branches associated with the user.
                # Edited by MMM
                store_user_branches = store_controller_queries.get_store_user_branches(user_id, None, None, True)
            else:
                # Branch code(s) are given.
                store_user_branches = branch_codes
            branches = ','.join(store_user_branches)
            log_data = {
                'BRANCHES :': branches
            }
            info_logger(f'Route: {request.path}').info(json.dumps(log_data))
            status_type = 'COMPLETED'
            if (filter_type == None):
                completed_activities_query = f"EXEC JFSL.dbo.SPFabCompletedActivity @fromdate='{from_date}', @todate='{to_date}', @branch = '{branches}',@activitytype='',@Status_type = '{status_type}'"
            else:
                completed_activities_query = f"EXEC JFSL.dbo.SPFabCompletedActivity @fromdate='{from_date}', @todate='{to_date}', @branch = '{branches}',@activitytype='{filter_type}',@Status_type = '{status_type}'"
            completed_activities = CallSP(completed_activities_query).execute().fetchall()
            db.session.commit()
            # print(pending_activities)
            log_data = {
                'completed_query :': completed_activities_query
                # "completed_activities": completed_activities
            }
            info_logger(f'Route: {request.path}').info(json.dumps(log_data))

            # print(pending_activities)




        except Exception as e:
            error_logger(f'Route: {request.path}').error(e)

        if completed_activities:
            final_data = generate_final_data('DATA_FOUND')
            if report:
                # Report flag is included in the request. So generate the file and send the file back.
                report_link = GenerateReport(completed_activities, 'completed').generate().get()
                if report_link is not None:
                    final_data['result'] = report_link
                else:
                    # Failed to generate the file.
                    final_data = generate_final_data('FILE_NOT_FOUND')
            else:
                final_data['result'] = completed_activities
        else:
            final_data = generate_final_data('DATA_NOT_FOUND')
    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(completed_activities_form.errors)

    return final_data

@store_console_blueprint.route('/get_branch', methods=["POST"])
#@authenticate('store_user')
def get_branch():
    """
    API for getting the store branches using the stored procedure.
    @return:
    """
    get_branches_form = GetBranchForm()
    if get_branches_form.validate_on_submit():
        latpoint = get_branches_form.latpoint.data
        longpoint = get_branches_form.longpoint.data
        radius = 2.00
        distance_unit = 12
        type_return = 1
        final_data = generate_final_data('ERROR')
        log_data = {
                'get_branches_form': get_branches_form.data
            }
        info_logger(f'Route: {request.path}').info(json.dumps(log_data))

        try:
            query = f"Exec JFSL.[dbo].[FetchingPartnersUsingCordinatesForApp] @Latpoint={latpoint}, @Longpoint={longpoint}, @Radius={radius}, @DistanceUnit={distance_unit}, @TypeReturn={type_return}"
            log_data = {
                'query': query
            }
            info_logger(f'Route: {request.path}').info(json.dumps(log_data))
            branches = CallSP(query).execute().fetchall()
            log_data = {
                'query succ11': branches
            }
            info_logger(f'Route: {request.path}').info(json.dumps(log_data))
            if branches:
                log_data = {
                    'query succ': 'query'
                }
                info_logger(f'Route: {request.path}').info(json.dumps(log_data))
                final_data = generate_final_data('DATA_FOUND')
                final_data['result'] = [dict(branch) for branch in branches]  
            else:
                log_data = {
                    'query succ11': 'Else'
                }
                info_logger(f'Route: {request.path}').info(json.dumps(log_data))
                final_data = generate_final_data('DATA_NOT_FOUND')

        except Exception as e:
            error_logger(f'Route: {request.path}').error(e)
            final_data = generate_final_data('ERROR')

    return final_data

@store_console_blueprint.route('/cancel_pickup_restriction', methods=["POST"])
# @authenticate('store_user')
def cancel_pickup_restriction():
    """
    API for cancelling a pickup request.
    @return:
    """
    cancel_form = Cancel_Restriction_PickupForm()

    log_data = {
        'cancel_form': cancel_form.data

    }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))
    print("hello")

    user_id = request.headers.get('user-id')
    if cancel_form.validate_on_submit():
        BookingId = cancel_form.pickup_request_id.data
        try:

            if BookingId is not None:
                log_data = {
                    'test': 'brand'
                }
                info_logger(f'Route: {request.path}').info(json.dumps(log_data))

                #pickup_source = pickup_request.BookingId if pickup_request else None
                pending_pickups_query = f"EXEC CustomerApp.[dbo].[PickupCancelRestrictUsers] @bookingid='{BookingId}'"
                log_data = {
                    'pickup :': pending_pickups_query
                }
                info_logger(f'Route: {request.path}').info(json.dumps(log_data))

                result = CallSP(pending_pickups_query).execute().fetchone()

                log_data = {
                    'pickups :': result
                }
                info_logger(f'Route: {request.path}').info(json.dumps(log_data))
                if result:

                    final_data = generate_final_data('DATA_FOUND')
                    final_data['result'] = result
                else:
                    final_data = generate_final_data('DATA_NOT_FOUND')



        except Exception as e:
            db.session.rollback()
            error_logger(f'Route: {request.path}').error(e)


    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(cancel_form.errors)
    log_data = {
        'final_data': final_data
    }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))

    return final_data

@store_console_blueprint.route('/cancel_pickup_reason', methods=["POST"])
# @authenticate('store_user')
def cancel_pickup_reason():
    """
    API for cancelling a pickup request.
    @return:
    """
    cancel_form = Cancel_Reason_PickupForm()

    log_data = {
        'cancel_form': cancel_form.data

    }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))

    user_id = request.headers.get('user-id')
    if cancel_form.validate_on_submit():
        BookingId = cancel_form.pickup_request_id.data
        cancel_reason = cancel_form.cancel_reason.data


        try:


            if BookingId is not None:
                existing_reason = db.session.query(CancellationReason).filter(
                    and_(
                        CancellationReason.Store_User_Id == user_id,
                        CancellationReason.BookingId == BookingId
                    )
                ).first()

                if existing_reason:
                    existing_reason.Reason = cancel_reason
                    existing_reason.RecordLastUpdatedDate = get_current_date()
                    db.session.commit()
                    is_added = True
                else:

                    new_cancel = CancellationReason(
                        BookingId=BookingId,
                        RecordCreatedDate=get_current_date(),
                        RecordLastUpdatedDate=get_current_date(),
                        Reason=cancel_reason,
                        Store_User_Id=user_id
                    )
                    db.session.add(new_cancel)
                    db.session.commit()
                    is_added = True

                if is_added:

                    final_data = generate_final_data('DATA_SAVED')
                else:
                    final_data = generate_final_data('DATA_SAVE_FAILED')




        except Exception as e:
            db.session.rollback()
            error_logger(f'Route: {request.path}').error(e)


    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(cancel_form.errors)
    log_data = {
        'final_data': final_data
    }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))

    return final_data


@store_console_blueprint.route('/get_screens', methods=["GET"])
# @authenticate('store_user')
def get_screens():
    try:
        query = db.session.execute(text("""
            SELECT * from Screens""")).fetchall()
        result = SerializeSQLAResult(query).serialize()

        if result:
            final_data = generate_final_data('DATA_FOUND')
            final_data['result'] = result
        else:
            final_data = generate_final_data('DATA_NOT_FOUND')

    except Exception as e:
        error_logger(f'Route: {request.path}').error(e)
        final_data = generate_final_data('ERROR')
    return final_data

