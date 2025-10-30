"""
------------------------
DELIVERY CONTROLLER
A module consisting of set of functions/APIs that are used by the delivery/logistics app.


The Flask blueprint module consisting of set of functions/APIs that are used by the delivery/logistics app.
------------------------
Created on May 20, 2020.
Coded by: Krishna Prasad K
© Jyothy Fabricare Services LTD.
------------------------
"""
import inspect
import requests
from flask import Blueprint, request, current_app, send_file, redirect
import json
from decimal import Decimal
from datetime import datetime, timedelta, date
from sqlalchemy import func, or_, case, cast, String, and_, text, literal, extract, desc
import jwt
import uuid
import base64
from sqlalchemy import desc
import openpyxl
import haversine as hs

import os
import random
import requests
from fabric import db
from sqlalchemy.orm.exc import MultipleResultsFound
from werkzeug.utils import secure_filename
# Importing authentication middleware.
from fabric.middlewares.auth_guard import api_key_required, authenticate
# Importing the generally used functions module.
from fabric.generic.functions import json_input, generate_final_data, populate_errors, generate_hash, \
    get_current_date, get_today, send_sms, login_send_sms, get_greeting_text,send_sms_laundry
from .helper import PickupDetails, send_push_notification, send_test_push_notification, DeliveryDetails, rank_list, \
    add_instruction, get_garment_price, checksum_generator, get_paytm_credentials, check_paytm_payment_status, \
    first_3_activity_dict

# Importing the WTF form classes used by this controller.
from .forms import LoginForm, HomeForm, ActivityListForm, PendingPickupDetailsForm, GetOrderGarmentsForm, \
    AddOrderGarmentsForm, AddOrderGarmentPhotoForm, RemoveOrderGarmentForm, CancelPickupForm, ReschedulePickupForm, \
    SaveOrderGarmentInstructionForm, SaveOrderGarmentIssueForm, RemoveOrderGarmentPhotoForm, GetPickupTimeslotsForm, \
    UpdateOrderGarmentServiceTypeForm, UpdateHangerInstructionsForm, SaveOrderReviewForm, PendingDeliveryDetailsForm, \
    GetDeliveryGarmentsForm, GetGarmentDetailsForm, SaveGPSCordsForm, UpdateCustomerAddressForm, \
    ValidateDiscountCodeForm, SendOTPForm, VerifyOTPForm, CreateAdhocPickupForm, CheckCustomerForm, \
    SaveCustomerForm, AddAddressForm, FinalizeOrderForm, ValidateCouponCodeForm, GetCouponCodesForm, GetGarmentsForm, \
    SaveDeliveryReviewForm, CheckOrderPaymentStatusForm, AddComplaintForm, MakePaymentForm, MakeDelivery, \
    GetOrderGarmentsPriceForm, GetCompletedActivitiesForm, GetLPForm, SaveGPSPosition, ClockInForm, ClockOutForm, \
    SendPaymentLinkForm, SendWaitingSMSForm, RescheduleDeliveryForm, CalculatePayableAmountForm, SaveRemarksForm, \
    GetAvailableServiceTypesForm, UpdateGarmentMeasurementForm, FcmForm, NotifyForm, UpdateBranchForm, \
    PushNotificationForm, MakeReadReadNotificationForm, CheckDiscountCodeForm, DUserDailyBranchForm, DarningForm, \
    CancelorReschedulePermissionForm, OpenPickupsForm, \
    DuserAttendanceDeleteForm, RankForm, DUserProPicForm, SaleRequestForm, CheckPaymentStatusForm, GetServiceTatForm, \
    GetRecentOrdersForm, GetTagDetailsForm, ReopenComplaintForm, GarmentDetailsForm, FutureDateRewashForm, \
    AdhocRewashForm, FinalizeRewashForm, TagDetailsForm, VasDetailsForm, \
    CheckOutStandingLimitForm, GetPickupInstructionsForm, SmsForm,  CheckOpenPickupsForm,AddComplaintForm1,GenaretRazorPayQRCode,SendPaymentLinkForms

# Importing the core model classes used by this controller.
from fabric.modules.models import DeliveryUser, DeliveryUserLogin, PickupRequest, Order, Customer, \
    CustomerAddres, PickupTimeSlot, ServiceTat, ServiceType, \
    Garment, GarmentCategory, GarmentUOM, BranchSeviceTat, OrderGarment, \
    PriceList, OrderPhoto, OrderInstruction, GarmentInstruction, GarmentIssue, OrderIssue, PickupReschedule, \
    OrderStatusCode, OrderReview, OrderReviewReason, OTP, DeliveryRequest, \
    QCInfo, DeliveryReviewReason, DeliveryReview, Delivery, ComplaintType, \
    TransactionInfo, TransactionPaymentInfo, DeliveryReschedule, TravelLog, DeliveryUserGPSLog, DeliveryUserAttendance, \
    DeliveryGarment, DeliveryUserBranch, Branch, MessageTemplate, PickupRescheduleReason, Complaint, PartialCollection, \
    MessageLog, PushNotification, CustomerTimeSlot, DeliveryUserDailyBranch, DailyCompletedActivityCount, \
    PaytmEDCTransaction, DeliveryDateEstimator, GarmentStatusCode, City, State, FabPickupTimeSlots, ReasonTemplates,RazorpayPayments

# Importing the common module library.
import fabric.modules.common as common_module

# Importing the payment module library.
import fabric.modules.payment as payment_module

# Importing the Ameyo ticketing service module library.
import fabric.modules.ameyo as ameyo_module

# Importing the EasyRewardz module library.
import fabric.modules.easyrewardz as er_module

# Importing the generally used classes module.
from fabric.generic.classes import SerializeSQLAResult, CallSP, TravelDistanceCalculator

# Importing the loggers module.
from fabric.generic.loggers import error_logger, info_logger

# Importing the queries that are needed to execute on more than one occasions by this controller.
from . import queries as delivery_controller_queries

# Importing the project settings.
from fabric.settings.project_settings import LOCAL_DB, SERVER_DB, CURRENT_ENV, PAYMENT_LINK_API_KEY, OLD_DB, channel_id, \
    sale_request_url, sale_request_status_url, CRM

# Importing functions from store_console queries
from fabric.blueprints.store_console import queries as store_controller_queries

# instance of delivery app blueprint
delivery_blueprint = Blueprint("delivery", __name__, url_prefix='/delivery', template_folder='templates',
                               static_folder='static')


@delivery_blueprint.route('/')
def index():
    """
    Index route.
    @return:
    """
    # Redirects to the JFSL website.
    return redirect("https://jfsl.in", code=302)


# # Edited by MMM
# @delivery_blueprint.route('/initiate_payment_request', methods=["POST"])
# # @authenticate('delivery_user')
# def initiate_payment_request():
#     form = SaleRequestForm()
#     if form.validate_on_submit():
#         order_id = form.order_id.data
#         force_pay = True if form.force_pay.data else False
#         initiate_sale_request = False
#         sale_request_completed = False
#         # Change order id to pass to pos device (Need min 8 alpha numeric chars)
#         edc_order_id = f"{order_id}FBX{datetime.now().strftime('%d%H%M%S')}"

#         user_id = request.headers.get('user-id')
#         current_12_hr_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

#         response = None
#         error_msg = None

#         paytm_credentials = get_paytm_credentials(user_id)

#         if paytm_credentials is None:
#             return generate_final_data('CUSTOM_FAILED', "Could not find PAYTM EDC device linked to your account")

#         edc_transaction_base_query = db.session.query(PaytmEDCTransaction).filter(
#             PaytmEDCTransaction.OrderId == order_id, PaytmEDCTransaction.IsDeleted == 0)

#         edc_transaction = edc_transaction_base_query.filter(
#             PaytmEDCTransaction.PaymentStatus == 'Success').one_or_none()

#         if edc_transaction:
#             return generate_final_data('CUSTOM_FAILED', "Payment already received for this order")

#         edc_transaction = edc_transaction_base_query.filter(
#             PaytmEDCTransaction.PaymentStatus == 'Pending').one_or_none()

#         if edc_transaction:
#             paytm_status = check_paytm_payment_status(paytm_credentials, edc_transaction.MerchantTransactionId,
#                                                       current_12_hr_time)

#             if paytm_status == "SUCCESS":
#                 edc_transaction.PaymentStatus = "Success"
#                 db.session.commit()
#                 return generate_final_data('CUSTOM_FAILED', "Payment already received")

#         if edc_transaction is None or force_pay:
#             initiate_sale_request = True

#         if initiate_sale_request:

#             try:

#                 order_details = db.session.query(Order.EGRN, Customer.CustomerCode).join(Customer,
#                                                                                          Order.CustomerId == Customer.CustomerId).filter(
#                     Order.IsDeleted == 0, Order.OrderId == order_id).one_or_none()

#                 # Retrieving the payable amount through SP
#                 amount = delivery_controller_queries.get_payable_amount_via_sp(order_details.CustomerCode,
#                                                                                order_details.EGRN)

#                 if amount:

#                     payable_amount = str(round(amount['PAYABLEAMOUNT'] * 100))

#                     checksum_body = {"paytmTid": paytm_credentials['TID'], "transactionDateTime": current_12_hr_time,
#                                      "transactionAmount": payable_amount,
#                                      "merchantTransactionId": edc_order_id,
#                                      "paytmMid": paytm_credentials['MID'].strip()}

#                     checksum = checksum_generator(checksum_body, paytm_credentials['MerchantKey'])

#                     log_data = {
#                         'checksum_body': checksum_body,
#                         'checksum': checksum
#                     }
#                     info_logger(f'Route: {request.path}').info(json.dumps(log_data))

#                     if checksum:
#                         headers = {
#                             'Content-Type': 'application/json'
#                         }
#                         body = {
#                             "head": {
#                                 "version": "3.1", "requestTimeStamp": current_12_hr_time, "channelId": channel_id,
#                                 "checksum": checksum
#                             },
#                             "body": {
#                                 "paytmMid": paytm_credentials['MID'].strip(), "paytmTid": paytm_credentials['TID'],
#                                 "transactionDateTime": current_12_hr_time, "merchantTransactionId": edc_order_id,
#                                 "transactionAmount": payable_amount
#                             }
#                         }
#                         log_data = {
#                             'body': body
#                         }
#                         info_logger(f'Route: {request.path}').info(json.dumps(log_data))

#                         response = requests.post(sale_request_url, data=json.dumps(body), headers=headers)
#                         response = json.loads(response.text)
#                         log_data = {
#                             'response': response
#                         }
#                         info_logger(f'Route: {request.path}').info(json.dumps(log_data))

#                         if response['body']['resultInfo']['resultStatus'] == 'ACCEPTED_SUCCESS':

#                             log_data = {
#                                 'init if': "init if"
#                             }
#                             info_logger(f'Route: {request.path}').info(json.dumps(log_data))

#                             edc_transaction = db.session.query(PaytmEDCTransaction).filter(
#                                 PaytmEDCTransaction.OrderId == order_id, PaytmEDCTransaction.PaymentStatus == 'Pending',
#                                 PaytmEDCTransaction.IsDeleted == 0).one_or_none()

#                             if edc_transaction:
#                                 edc_transaction.IsDeleted = 1
#                                 edc_transaction.PaymentStatus = "Cancelled"

#                             new_paytm_transaction = PaytmEDCTransaction(
#                                 OrderId=order_id, PaymentStatus="Pending", MerchantTransactionId=edc_order_id,
#                                 IsDeleted=0, RecordCreatedDate=get_current_date())
#                             db.session.add(new_paytm_transaction)
#                             db.session.commit()
#                             sale_request_completed = True

#                     else:
#                         log_data = {
#                             'init8': 'init8'
#                         }
#                         info_logger(f'Route: {request.path}').info(json.dumps(log_data))
#                         error_msg = "Failed to generate checksum"
#                 else:
#                     error_msg = "Payable amount not found"

#             except Exception as e:
#                 error_logger(f'Route: {request.path}').error(e)

#         else:
#             error_msg = "Payment request already exists"

#         if error_msg is None:
#             if sale_request_completed:
#                 final_data = generate_final_data('SUCCESS')
#                 final_data['SerialNumber'] = paytm_credentials['SerialNumber']
#             else:
#                 if response:
#                     final_data = generate_final_data('CUSTOM_FAILED', response['body']['resultInfo']['resultMsg'])
#                 else:
#                     final_data = generate_final_data('CUSTOM_FAILED', "Maximum retries Exceeded please try again after"
#                                                                       " some time")

#         else:
#             final_data = generate_final_data('CUSTOM_FAILED', error_msg)

#     else:
#         # Form validation error.
#         final_data = generate_final_data('FORM_ERROR')
#         final_data['errors'] = populate_errors(form.errors)

#     log_data = {
#         'final_data': final_data,
#         "error_msg": error_msg
#     }
#     info_logger(f'Route: {request.path}').info(json.dumps(log_data))

#     return final_data

@delivery_blueprint.route('/initiate_payment_request', methods=["POST"])
# @authenticate('delivery_user')
def initiate_payment_request():
    form = SaleRequestForm()
    if form.validate_on_submit():
        TRNNo = form.TRNNo.data
        EGRN =  form.EGRN.data
        CustomerCode = form.CustomerCode.data
        force_pay = True if form.force_pay.data else False
        initiate_sale_request = False
        sale_request_completed = False
        # Change order id to pass to pos device (Need min 8 alpha numeric chars)
        edc_order_id = f"{TRNNo}FBX{datetime.now().strftime('%d%H%M%S')}"

        user_id = request.headers.get('user-id')
        current_12_hr_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        PaymentStatus = "Pending"

        response = None
        error_msg = None

        paytm_credentials = get_paytm_credentials(user_id)

        if paytm_credentials is None:
            return generate_final_data('CUSTOM_FAILED', "Could not find PAYTM EDC device linked to your account")

        edc_transaction = db.session.execute(
            text("""
                        SELECT PaymentStatus
                        FROM JFSL.dbo.FAbPaytmEDCTransactions WITH (NOLOCK)
                        WHERE PaymentStatus = 'Success' AND TRNNo = :TRNNo
                    """),
            {"TRNNo": TRNNo}
        ).fetchone()

        if edc_transaction:
            return generate_final_data('CUSTOM_FAILED', "Payment already received for this order")

        edc_transaction = db.session.execute(
            text("""
                SELECT PaymentStatus, MerchantTransactionId
                FROM JFSL.dbo.FAbPaytmEDCTransactions WITH (NOLOCK)
                WHERE PaymentStatus = 'Pending' AND TRNNo = :TRNNo
            """),
            {"TRNNo": TRNNo}
        ).fetchone()

        if edc_transaction:
            paytm_status = check_paytm_payment_status(paytm_credentials, edc_transaction.MerchantTransactionId,
                                                      current_12_hr_time)

            if paytm_status == "SUCCESS":
                edc_transaction = db.session.execute(
                    text("""
                        UPDATE JFSL.dbo.FAbPaytmEDCTransactions
                        SET PaymentStatus = 'Success'
                        WHERE PaymentStatus = 'Pending' AND TRNNo = :TRNNo
                    """),
                    {"TRNNo": TRNNo}
                )

                db.session.commit()
                return generate_final_data('CUSTOM_FAILED', "Payment already received")

        if edc_transaction is None or force_pay:
            initiate_sale_request = True

        if initiate_sale_request:

            try:

                # Retrieving the payable amount through SP
                amount = delivery_controller_queries.get_payable_amount_via_sp(CustomerCode,
                                                                               TRNNo)

                if amount:

                    payable_amount = str(round(amount['PAYABLEAMOUNT'] * 100))

                    checksum_body = {"paytmTid": paytm_credentials['TID'], "transactionDateTime": current_12_hr_time,
                                     "transactionAmount": payable_amount,
                                     "merchantTransactionId": edc_order_id,
                                     "paytmMid": paytm_credentials['MID'].strip()}

                    checksum = checksum_generator(checksum_body, paytm_credentials['MerchantKey'])

                    log_data = {
                        'checksum_body': checksum_body,
                        'checksum': checksum
                    }
                    info_logger(f'Route: {request.path}').info(json.dumps(log_data))

                    if checksum:
                        headers = {
                            'Content-Type': 'application/json'
                        }
                        body = {
                            "head": {
                                "version": "3.1", "requestTimeStamp": current_12_hr_time, "channelId": channel_id,
                                "checksum": checksum
                            },
                            "body": {
                                "paytmMid": paytm_credentials['MID'].strip(), "paytmTid": paytm_credentials['TID'],
                                "transactionDateTime": current_12_hr_time, "merchantTransactionId": edc_order_id,
                                "transactionAmount": payable_amount
                            }
                        }
                        log_data = {
                            'body': body
                        }
                        info_logger(f'Route: {request.path}').info(json.dumps(log_data))

                        response = requests.post(sale_request_url, data=json.dumps(body), headers=headers)
                        response = json.loads(response.text)
                        log_data = {
                            'response': response
                        }
                        info_logger(f'Route: {request.path}').info(json.dumps(log_data))

                        if response['body']['resultInfo']['resultStatus'] == 'ACCEPTED_SUCCESS':

                            log_data = {
                                'init if': "init if"
                            }
                            info_logger(f'Route: {request.path}').info(json.dumps(log_data))
                            edc_transaction = db.session.execute(
                                    text("""
                                        SELECT PaymentStatus
                                        FROM JFSL.dbo.FAbPaytmEDCTransactions WITH (NOLOCK)
                                        WHERE PaymentStatus = 'Pending' AND TRNNo = :TRNNo
                                    """),
                                    {"TRNNo": TRNNo}
                            ).fetchone()


                            db.session.execute(text("""
                                INSERT INTO JFSL.Dbo.FAbPaytmEDCTransactions 
                                (TRNNo, PaymentStatus, MerchantTransactionId, IsDeleted, RecordCreatedDate)
                                VALUES (:TRNNo, :PaymentStatus, :edc_order_id, :IsDeleted, :RecordCreatedDate)
                            """), {
                                "TRNNo": TRNNo,
                                "PaymentStatus": PaymentStatus,
                                "edc_order_id": edc_order_id,
                                "IsDeleted": 0,
                                "RecordCreatedDate": get_current_date()
                            })
                            db.session.commit()
                            sale_request_completed = True

                    else:
                        log_data = {
                            'init8': 'init8'
                        }
                        info_logger(f'Route: {request.path}').info(json.dumps(log_data))
                        error_msg = "Failed to generate checksum"
                else:
                    error_msg = "Payable amount not found"

            except Exception as e:
                error_logger(f'Route: {request.path}').error(e)

        else:
            error_msg = "Payment request already exists"

        if error_msg is None:
            if sale_request_completed:
                final_data = generate_final_data('SUCCESS')
                final_data['SerialNumber'] = paytm_credentials['SerialNumber']
            else:
                if response:
                    final_data = generate_final_data('CUSTOM_FAILED', response['body']['resultInfo']['resultMsg'])
                else:
                    final_data = generate_final_data('CUSTOM_FAILED', "Maximum retries Exceeded please try again after"
                                                                      " some time")

        else:
            final_data = generate_final_data('CUSTOM_FAILED', error_msg)

    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(form.errors)

    log_data = {
        'final_data': final_data,
        "error_msg": error_msg
    }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))

    return final_data


# @delivery_blueprint.route('/check_payment_status', methods=["POST"])
# @authenticate('delivery_user')
# def check_payment_status():
#     """
#     API for checking the status of a sale request
#     """
#     form = CheckPaymentStatusForm()
#     if form.validate_on_submit():
#         order_id = form.order_id.data

#         final_data = {}
#         error_msg = None
#         is_payment_success = False
#         user_id = request.headers.get('user-id')
#         current_12_hr_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

#         paytm_credentials = get_paytm_credentials(user_id)

#         log_data = {
#             'form': form.data
#         }
#         info_logger(f'Route: {request.path}').info(json.dumps(log_data))

#         if paytm_credentials is None:
#             return generate_final_data('CUSTOM_FAILED', "Could not find PAYTM EDC device linked to your account")

#         previous_order = db.session.query(PaytmEDCTransaction).filter(
#             PaytmEDCTransaction.OrderId == order_id, PaytmEDCTransaction.IsDeleted == 0,
#             PaytmEDCTransaction.PaymentStatus == 'Pending').one_or_none()

#         if previous_order:
#             payment_status = check_paytm_payment_status(paytm_credentials, previous_order.MerchantTransactionId,
#                                                         current_12_hr_time)

#             if payment_status == "SUCCESS":

#                 previous_order.PaymentStatus = "Success"
#                 db.session.commit()
#                 is_payment_success = True

#             else:
#                 error_msg = payment_status

#         if is_payment_success:
#             final_data = generate_final_data('SUCCESS')
#         elif error_msg:
#             final_data = generate_final_data('CUSTOM_FAILED', error_msg)
#     else:
#         # Form validation error.
#         final_data = generate_final_data('FORM_ERROR')
#         final_data['errors'] = populate_errors(form.errors)
#     log_data = {
#         'final_data': final_data
#     }
#     info_logger(f'Route: {request.path}').info(json.dumps(log_data))

#     return final_data

@delivery_blueprint.route('/check_payment_status', methods=["POST"])
# @authenticate('delivery_user')
def check_payment_status():
    """
    API for checking the status of a sale request
    """
    form = CheckPaymentStatusForm()
    if form.validate_on_submit():
        TRNNo = form.TRNNo.data

        final_data = {}
        error_msg = None
        is_payment_success = False
        user_id = request.headers.get('user-id')
        current_12_hr_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        paytm_credentials = get_paytm_credentials(user_id)

        log_data = {
            'form': form.data
        }
        info_logger(f'Route: {request.path}').info(json.dumps(log_data))

        if paytm_credentials is None:
            return generate_final_data('CUSTOM_FAILED', "Could not find PAYTM EDC device linked to your account")

        # previous_order = db.session.query(PaytmEDCTransaction).filter(
        #     PaytmEDCTransaction.TRNNo == TRNNo, PaytmEDCTransaction.IsDeleted == 0,
        #     PaytmEDCTransaction.PaymentStatus == 'Pending').one_or_none()
        previous_order = db.session.execute(
            text("""
                SELECT PaymentStatus, MerchantTransactionId
                FROM JFSL.dbo.FAbPaytmEDCTransactions WITH (NOLOCK)
                WHERE PaymentStatus = 'Pending' AND TRNNo = :TRNNo
                Order BY ID DESC
            """),
            {"TRNNo": TRNNo}
        ).fetchone()

        if previous_order:
            payment_status = check_paytm_payment_status(paytm_credentials, previous_order.MerchantTransactionId,
                                                        current_12_hr_time)

            if payment_status == "SUCCESS":

                edc_transaction = db.session.execute(
                    text("""
                        UPDATE JFSL.dbo.FAbPaytmEDCTransactions
                        SET PaymentStatus = 'Success'
                        WHERE PaymentStatus = 'Pending' AND TRNNo = :TRNNo
                    """),
                    {"TRNNo": TRNNo}
                )

                db.session.commit()
                is_payment_success = True

            else:
                error_msg = payment_status
        else:

            previous_order = db.session.execute(
            text("""
                SELECT PaymentStatus, MerchantTransactionId
                FROM JFSL.dbo.FAbPaytmEDCTransactions WITH (NOLOCK)
                WHERE PaymentStatus = 'Success' AND TRNNo = :TRNNo
                Order BY ID DESC
            """),
            {"TRNNo": TRNNo}
            ).fetchone()
            if previous_order:
                is_payment_success = True

        if is_payment_success:
            final_data = generate_final_data('SUCCESS')
        elif error_msg:
            final_data = generate_final_data('CUSTOM_FAILED', error_msg)
    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(form.errors)
        
    log_data = {
        'final_data': final_data
    }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))

    return final_data


@delivery_blueprint.route('/set_d_user_pro_pic', methods=["POST"])
@authenticate('delivery_user')
def set_d_user_pro_pic():
    """
    API for adding  profile picture to delivery user.
    """

    form = DUserProPicForm()
    if form.validate_on_submit():

        b64_image = form.b64_image.data

        # Setting up the uploaded flag. If the image is successfully uploaded this will be set to True.
        uploaded = False
        result = False
        filename = ""

        try:
            # Removing the MIME type description from the string.
            purified_string = base64.b64decode(b64_image.replace('data:image/png;base64,', ''))

            user_id = request.headers.get('user-id')

            # Root directory of the project.
            root_dir = os.path.dirname(current_app.instance_path)
            # Folder to which the image in  uploaded
            uploads_folder = f'{root_dir}/uploads/delivery_user_profile_images'
            # If the folder doesn't exist, create the folder.
            if not os.path.exists(uploads_folder):
                os.makedirs(uploads_folder)
            # Create a name for the image
            filename = f'IMG_{user_id}_0'

            d_user = db.session.query(DeliveryUser).filter(DeliveryUser.DUserId == user_id).one_or_none()

            if d_user is not None and d_user.DUserImage is not None:
                filename = d_user.DUserImage

                image_with_path = uploads_folder + '/' + f"{filename}.jpg"
                # Removing image if there is already an image
                if os.path.isfile(image_with_path):
                    os.remove(image_with_path)

                # Finding the index with last  _ occurrence
                last_index = filename.rfind('_')
                # image_num means, the number of time's image is uploaded
                # Each time an image is uploaded the image_num is incremented with 1
                image_num = int(filename[last_index + 1:])
                # Setting up the photo file name
                filename = f'IMG_{user_id}_{image_num + 1}'

            # Target file link
            target_file = f'{uploads_folder}/{filename}.jpg'

            with open(target_file, 'wb') as f:
                f.write(purified_string)
                uploaded = True

            if uploaded:
                # File successfully saved into the folder. Now save the date into DeliveryUser table.
                try:
                    d_user.DUserImage = f'{filename}'
                    db.session.commit()
                    # The data is inserted into DB.
                    result = True

                except Exception as e:
                    db.session.rollback()
                    error_logger(f'Route: {request.path}').error(e)

        except Exception as e:
            error_logger(f'Route: {request.path}').error(e)

        if result:
            final_data = generate_final_data('DATA_SAVED')
            final_data['file_name'] = filename
        else:
            final_data = generate_final_data('DATA_SAVE_FAILED')

    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(form.errors)

    return final_data


@delivery_blueprint.route('/get_d_user_pro_pic/<photo_file>', methods=["GET"])
# @authenticate('delivery_user')
def get_d_user_pro_pic(photo_file):
    """
    API for getting Delivery user images based on image name
    """

    root_dir = os.path.dirname(current_app.instance_path)
    # Loading the data from the DB.
    image_data = None
    try:
        # Getting the image data from the DB.
        image_data = db.session.query(DeliveryUser.DUserImage).filter(
            DeliveryUser.DUserImage == photo_file).one_or_none()
    except Exception as e:
        error_logger(f'Route: {request.path}').error(e)

    if image_data:
        # Here a image data is found. So return the image file.
        target_file = f'{root_dir}/uploads/delivery_user_profile_images/{photo_file}.jpg'
        return send_file(target_file, mimetype='image/jpg')
    else:
        # No file found for that particular image.
        final_data = generate_final_data('FILE_NOT_FOUND')

        return final_data


# @delivery_blueprint.route('/get_top_users_rank', methods=["POST"])
# # @authenticate('delivery_user')
# def get_top_users_rank():
#     """
#     API for Top 3 ranked delivery user activity details if there are more than 3 user's with
#     rank 1 display all, other ways display only first 3 ones
#     """
#     # Getting user-id from header
#     user_id = int(request.headers.get('user-id'))
#     # Today rank list
#     rank_data = rank_list(None, "Today", user_id, None, "TopRank")
#     # Delete MyRank instance
#     del rank_data['MyRank']

#     final_pickup_data = first_3_activity_dict(rank_data['PickupRankList'], 'PickupCount')
#     final_delivery_data = first_3_activity_dict(rank_data['DeliveryRankList'], 'DeliveryCount')

#     is_mtd = True if date.today().day == 1 else False

#     final_data = generate_final_data('DATA_FOUND')
#     final_data['result'] = {"PickupRankList": final_pickup_data, "DeliveryRankList": final_delivery_data,
#                             "IsMtd": is_mtd}

#     return final_data

@delivery_blueprint.route('/get_top_users_rank', methods=["POST"])
def get_current_user_rank_():
    """
    API for returning rank of delivery user based on completed pickup and delivery count taken by delivery user
    """
    # Getting user-id from header
    user_id = int(request.headers.get('user-id'))

    # Query for yesterday's pickup and delivery data
    query = """EXEC JFSL.DBO.SPFabGetLeaderBoardData @FilterFlag = 'Yesterday', @deliverytype = 'Pickup'"""
    Yesterday_Pickup = CallSP(query).execute().fetchall()

    query = """EXEC JFSL.DBO.SPFabGetLeaderBoardData @FilterFlag = 'Yesterday', @deliverytype = 'Delivery'"""
    Yesterday_Delivery = CallSP(query).execute().fetchall()

    # Generate final data if pickup or delivery data exists
    if Yesterday_Pickup or Yesterday_Delivery:
        def format_rank_data(data, is_pickup=True):
            """Format data to match expected response format."""
            result = []
            for item in data:
                result.append({
                    "DeliveryUserName": item.get('DeliveryUserName', ''),
                    "DUserId": item.get('DUserId', 0),
                    "PickupCount" if is_pickup else "DeliveryCount": item.get('Count', 0),
                    "FileName": f"IMG_{item.get('DUserId', 0)}_{item.get('Rank', 0)}",
                    "Revenue": item.get('Revenue', 0),
                    "rank": item.get('rank', 0)
                })
            return result

        # Build the response
        result = {
            "PickupRankList": format_rank_data(Yesterday_Pickup, is_pickup=True),
            "DeliveryRankList": format_rank_data(Yesterday_Delivery, is_pickup=False),
            "IsMtd": False
        }

        # Generate data with 'DATA_FOUND'
        final_data = generate_final_data('DATA_FOUND')
        final_data['result'] = result
    else:
        # Generate data with 'DATA_NOT_FOUND'
        final_data = generate_final_data('DATA_NOT_FOUND')
        final_data['result'] = {
            "PickupRankList": [],
            "DeliveryRankList": [],
            "IsMtd": False
        }

    return final_data


# @delivery_blueprint.route('/get_current_user_rank', methods=["POST"])
# @authenticate('delivery_user')
# def get_current_user_rank():
#     """
#     Api for returning rank of delivery user based on completed pickup and delivery count taken by delivery user
#     """

#     # Getting user-id from header
#     user_id = int(request.headers.get('user-id'))
#     # Today rank list
#     today_rank = rank_list(True, "Today", user_id)
#     # Month rank list
#     month_rank = rank_list(True, "Month", user_id)

#     if today_rank and month_rank:
#         result = {'TodayRank': {"PickupRankList": today_rank['PickupRankList'][0] if today_rank['PickupRankList'] else {
#             "PickupCount": 0, "PickupRank": 0}, "DeliveryRankList": today_rank['DeliveryRankList'][0] if today_rank[
#             'DeliveryRankList'] else {"DeliveryCount": 0, "DeliveryRank": 0}},

#                   'MonthRank': {"PickupRankList": month_rank['PickupRankList'][0] if month_rank['PickupRankList'] else {
#                       "PickupCount": 0, "PickupRank": 0}, "DeliveryRankList": month_rank['DeliveryRankList'][0] if
#                   month_rank['DeliveryRankList'] else {"DeliveryCount": 0, "DeliveryRank": 0}}}

#         final_data = generate_final_data('DATA_FOUND')

    #     final_data['result'] = result
    # else:
    #     final_data = generate_final_data('DATA_NOT_FOUND')

    # return final_data

# @delivery_blueprint.route('/get_current_user_rank', methods=["POST"])
# def get_current_user_rank():
#     """
#     API for returning rank of delivery user based on completed pickup and delivery count taken by delivery user
#     """

#     # Getting user-id from header
#     user_id = int(request.headers.get('user-id'))

#     # Query for yesterday's pickup and delivery data
#     query = f"""EXEC JFSL.DBO.SPFabGetLeaderBoardData @FilterFlag = 'Today', @deliverytype = 'Pickup', @DuserId = {user_id}"""
#     Yesterday_Pickup = CallSP(query).execute().fetchall()

#     query = f"""EXEC JFSL.DBO.SPFabGetLeaderBoardData @FilterFlag = 'Today', @deliverytype = 'Delivery', @DuserId = {user_id}"""
#     Yesterday_Delivery = CallSP(query).execute().fetchall()

#     # Query for monthly pickup and delivery data
#     query = f"""EXEC JFSL.DBO.SPFabGetLeaderBoardData @FilterFlag = 'Month', @deliverytype = 'Pickup' , @DuserId = {user_id}"""
#     Month_Pickup = CallSP(query).execute().fetchall()

#     query = f"""EXEC JFSL.DBO.SPFabGetLeaderBoardData @FilterFlag = 'Month', @deliverytype = 'Delivery' , @DuserId = {user_id}"""
#     Month_Delivery = CallSP(query).execute().fetchall()

#     # Helper function to get top record or default values
#     def get_top_rank(data, is_pickup=True):
#         """Return top rank data or default values."""
#         if data:
#             item = data[0]
#             return {
#                 "PickupCount" if is_pickup else "DeliveryCount": item.get('Count', 0),
#                 "PickupRank" if is_pickup else "DeliveryRank": item.get('rank', 0),
#                 "Revenue": item.get('Revenue', 0)
#             }
#         else:
#             return {
#                 "PickupCount" if is_pickup else "DeliveryCount": 0,
#                 "PickupRank" if is_pickup else "DeliveryRank": 0,
#                 "Revenue": 0
#             }

#     result = {
#         "MonthRank": {
#             "PickupRankList": get_top_rank(Month_Pickup, is_pickup=True),
#             "DeliveryRankList": get_top_rank(Month_Delivery, is_pickup=False)
#         },
#         "TodayRank": {
#             "PickupRankList": get_top_rank(Yesterday_Pickup, is_pickup=True),
#             "DeliveryRankList": get_top_rank(Yesterday_Delivery, is_pickup=False)
#         }
#     }

#     # Prepare the final response
#     if result['MonthRank']['PickupRankList']['PickupCount'] or result['MonthRank']['DeliveryRankList']['DeliveryCount']:
#         final_data = generate_final_data('DATA_FOUND')
#         final_data['result'] = result
#     else:
#         final_data = generate_final_data('DATA_NOT_FOUND')

#     return final_data

@delivery_blueprint.route('/get_current_user_rank', methods=["POST"])
def get_current_user_rank():
    """
    API for returning rank of delivery user based on completed pickup and delivery count taken by delivery user
    """

    # Getting user-id from header
    user_id = int(request.headers.get('user-id'))

    # Query for yesterday's pickup and delivery data
    query = f"""EXEC JFSL.DBO.SPFabGetLeaderBoardData @FilterFlag = 'Today', @deliverytype = 'Pickup', @DuserId = {user_id}"""
    Yesterday_Pickup = CallSP(query).execute().fetchall()

    query = f"""EXEC JFSL.DBO.SPFabGetLeaderBoardData @FilterFlag = 'Today', @deliverytype = 'Delivery', @DuserId = {user_id}"""
    Yesterday_Delivery = CallSP(query).execute().fetchall()

    # Query for monthly pickup and delivery data
    query = f"""EXEC JFSL.DBO.SPFabGetLeaderBoardData @FilterFlag = 'Month', @deliverytype = 'Pickup' , @DuserId = {user_id}"""
    Month_Pickup = CallSP(query).execute().fetchall()

    query = f"""EXEC JFSL.DBO.SPFabGetLeaderBoardData @FilterFlag = 'Month', @deliverytype = 'Delivery' , @DuserId = {user_id}"""
    Month_Delivery = CallSP(query).execute().fetchall()

    # Helper function to get top record or default values
    def get_top_rank(data, is_pickup=True):
        """Return top rank data or default values, handling null columns."""
        if data and isinstance(data, list):
            item = data[0]
            count = item.get('Count')
            rank = item.get('rank')
            revenue = item.get('Revenue')

            if count is None and rank is None and revenue is None:
                return {
                    "PickupCount" if is_pickup else "DeliveryCount": 0,
                    "PickupRank" if is_pickup else "DeliveryRank": 0,
                    "Revenue": 0
                }

            return {
                "PickupCount" if is_pickup else "DeliveryCount": count or 0,
                "PickupRank" if is_pickup else "DeliveryRank": rank or 0,
                "Revenue": revenue or 0
            }

        # Empty data fallback
        return {
            "PickupCount" if is_pickup else "DeliveryCount": 0,
            "PickupRank" if is_pickup else "DeliveryRank": 0,
            "Revenue": 0
        }

    result = {
        "MonthRank": {
            "PickupRankList": get_top_rank(Month_Pickup, is_pickup=True),
            "DeliveryRankList": get_top_rank(Month_Delivery, is_pickup=False)
        },
        "TodayRank": {
            "PickupRankList": get_top_rank(Yesterday_Pickup, is_pickup=True),
            "DeliveryRankList": get_top_rank(Yesterday_Delivery, is_pickup=False)
        }
    }

    # # Prepare the final response
    # if (
    #     result['MonthRank']['PickupRankList']['PickupCount'] > 0 or
    #     result['MonthRank']['DeliveryRankList']['DeliveryCount'] > 0
    # ):
    if result:
        final_data = generate_final_data('DATA_FOUND')
        final_data['result'] = result
    else:
        final_data = generate_final_data('DATA_NOT_FOUND')

    return final_data




# @delivery_blueprint.route('/get_rank_list', methods=["POST"])
# # @authenticate('delivery_user')
# def get_rank_list():
#     """
#     Api for returning sorted rank list based on completed pickup and delivery count taken by delivery users
#     """

#     # Function for getting DeliveryRankList & PickupRankList of delivery users
#     rank_form = RankForm()
#     if rank_form.validate_on_submit():
#         sort_by = rank_form.sort_by.data

#         # Getting user-id from header
#         user_id = int(request.headers.get('user-id'))
#         rank_lists = rank_list(None, sort_by, user_id)
#         log_data = {
#             'user_id': user_id
#         }
#         info_logger(f'Route: {request.path}').info(json.dumps(log_data))

#         if rank_lists:

#             final_data = generate_final_data('DATA_FOUND')
#             final_data['DeliveryCount'] = rank_lists['DeliveryRankList']
#             final_data['PickupCount'] = rank_lists['PickupRankList']
#             final_data['MyRank'] = rank_lists['MyRank']
#         else:
#             final_data = generate_final_data('DATA_NOT_FOUND')

#     else:
#         # Form validation error.
#         final_data = generate_final_data('FORM_ERROR')
#         final_data['errors'] = populate_errors(rank_form.errors)

#     return final_data

@delivery_blueprint.route('/get_rank_list', methods=["POST"])
# @authenticate('delivery_user')
def get_rank_list():
    """
    Api for returning sorted rank list based on completed pickup and delivery count taken by delivery users
    """
    # Function for getting DeliveryRankList & PickupRankList of delivery users
    rank_form = RankForm()

    # Helper function to rename 'Count' field
    def rename_count_field(data, new_key):
        for item in data:
            if 'Count' in item:
                item[new_key] = item.pop('Count')
        return data

    if rank_form.validate_on_submit():
        sort_by = rank_form.sort_by.data
        user_id = int(request.headers.get('user-id'))

        if sort_by == 'Today':
            query = f"""EXEC JFSL.DBO.SPFabGetLeaderBoardData @FilterFlag = 'Today', @deliverytype = 'Pickup', @Duserid = {user_id}"""
            pickup_my_rank_list = CallSP(query).execute().fetchall()

            query = f"""EXEC JFSL.DBO.SPFabGetLeaderBoardData @FilterFlag = 'Today', @deliverytype = 'Delivery', @Duserid = {user_id}"""
            delivery_my_rank_list = CallSP(query).execute().fetchall()

            query = f"""EXEC JFSL.DBO.SPFabGetLeaderBoardData @FilterFlag = 'Today', @deliverytype = 'Pickup'"""
            Pickup_rank_lists = CallSP(query).execute().fetchall()

            query = f"""EXEC JFSL.DBO.SPFabGetLeaderBoardData @FilterFlag = 'Today', @deliverytype = 'Delivery'"""
            Delivery_rank_lists = CallSP(query).execute().fetchall()

        else:
            query = f"""EXEC JFSL.DBO.SPFabGetLeaderBoardData @FilterFlag = 'Month', @deliverytype = 'Pickup', @Duserid = {user_id}"""
            pickup_my_rank_list = CallSP(query).execute().fetchall()

            query = f"""EXEC JFSL.DBO.SPFabGetLeaderBoardData @FilterFlag = 'Month', @deliverytype = 'Delivery', @Duserid = {user_id}"""
            delivery_my_rank_list = CallSP(query).execute().fetchall()

            query = f"""EXEC JFSL.DBO.SPFabGetLeaderBoardData @FilterFlag = 'Month', @deliverytype = 'Pickup'"""
            Pickup_rank_lists = CallSP(query).execute().fetchall()

            query = f"""EXEC JFSL.DBO.SPFabGetLeaderBoardData @FilterFlag = 'Month', @deliverytype = 'Delivery'"""
            Delivery_rank_lists = CallSP(query).execute().fetchall()

        if Pickup_rank_lists or Delivery_rank_lists:
            final_data = generate_final_data('DATA_FOUND')

            # Rename Count to PickupCount and DeliveryCount
            final_data['DeliveryCount'] = rename_count_field(Delivery_rank_lists, 'DeliveryCount')
            final_data['PickupCount'] = rename_count_field(Pickup_rank_lists, 'PickupCount')

            # Rename Count in MyRank
            if pickup_my_rank_list and delivery_my_rank_list:
                pickup_data = pickup_my_rank_list[0]
                delivery_data = delivery_my_rank_list[0]

                # Merge and format the data
                # final_data['MyRank'] = {
                #     "DUserId": pickup_data["DUserId"],
                #     "DeliveryUserName": pickup_data["DeliveryUserName"],
                #     "PickupCount": pickup_data["Count"],
                #     "PickupRank": pickup_data["rank"],
                #     # "FileName": pickup_data["FileName"],
                #     "PickupRevenue": pickup_data["Revenue"],
                #     "DeliveryCount": delivery_data["Count"],
                #     "DeliveryRank": delivery_data["rank"],
                #     "DeliveryRevenue": delivery_data["Revenue"]
                # }
                final_data['MyRank'] = {
                        "DUserId": pickup_data.get("DUserId", 0),
                        "DeliveryUserName": pickup_data.get("DeliveryUserName", ""),
                        "PickupCount": pickup_data.get("Count", 0),
                        "PickupRank": pickup_data.get("rank", 0),
                        # "FileName": pickup_data.get("FileName", ""),
                        "PickupRevenue": pickup_data.get("Revenue", 0),
                        "DeliveryCount": delivery_data.get("Count", 0),
                        "DeliveryRank": delivery_data.get("rank", 0),
                        "DeliveryRevenue": delivery_data.get("Revenue", 0)
                    }


            elif pickup_my_rank_list:
                pickup_data = pickup_my_rank_list[0]

                # final_data['MyRank'] = {
                #     "DUserId": pickup_data["DUserId"],
                #     "DeliveryUserName": pickup_data["DeliveryUserName"],
                #     "PickupCount": pickup_data["Count"],
                #     "PickupRank": pickup_data["rank"],
                #     # "FileName": pickup_data["FileName"],
                #     "PickupRevenue": pickup_data["Revenue"],
                #     "DeliveryCount": 0,
                #     "DeliveryRank": 0,
                #     "DeliveryRevenue": 0
                # }
                final_data['MyRank'] = {
                    "DUserId": pickup_data.get("DUserId", 0),
                    "DeliveryUserName": pickup_data.get("DeliveryUserName", ""),
                    "PickupCount": pickup_data.get("Count", 0),
                    "PickupRank": pickup_data.get("rank", 0),
                    # "FileName": pickup_data.get("FileName", ""),
                    "PickupRevenue": pickup_data.get("Revenue", 0),
                    "DeliveryCount": 0,
                    "DeliveryRank": 0,
                    "DeliveryRevenue": 0
                }


            elif delivery_my_rank_list:
                delivery_data = delivery_my_rank_list[0]

                # final_data['MyRank'] = {
                #     "DUserId": delivery_data["DUserId"],
                #     "DeliveryUserName": delivery_data["DeliveryUserName"],
                #     "PickupCount": 0,
                #     "PickupRank": 0,
                #     "FileName": "",
                #     "PickupRevenue": 0,
                #     "DeliveryCount": delivery_data["Count"],
                #     "DeliveryRank": delivery_data["rank"],
                #     "DeliveryRevenue": delivery_data["Revenue"]
                # }
                final_data['MyRank'] = {
                    "DUserId": delivery_data.get("DUserId", 0),
                    "DeliveryUserName": delivery_data.get("DeliveryUserName", ""),
                    "PickupCount": 0,
                    "PickupRank": 0,
                    "FileName": "",
                    "PickupRevenue": 0,
                    "DeliveryCount": delivery_data.get("Count", 0),
                    "DeliveryRank": delivery_data.get("rank", 0),
                    "DeliveryRevenue": delivery_data.get("Revenue", 0)
                }


            else:
                final_data['MyRank'] = {
                    "DUserId": 0,
                    "DeliveryUserName": "",
                    "PickupCount": 0,
                    "PickupRank": 0,
                    "FileName": "",
                    "PickupRevenue": 0,
                    "DeliveryCount": 0,
                    "DeliveryRank": 0,
                    "DeliveryRevenue": 0
                }

        else:
            final_data = generate_final_data('DATA_NOT_FOUND')

    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(rank_form.errors)

    return final_data

@delivery_blueprint.route('/delete_d_user_attendance', methods=["POST"])
# @authenticate('delivery_user')
def delete_d_user_attendance():
    form = DuserAttendanceDeleteForm()
    if form.validate_on_submit():
        d_user_id = form.d_user_id.data
        delete_d_user_branches = form.delete_d_user_branches.data
        updated = False

        try:
            d_user_attendance = db.session.query(DeliveryUserAttendance).filter_by(DUserId=d_user_id).order_by(
                DeliveryUserAttendance.RecordCreatedDate.desc()).first()
            db.session.delete(d_user_attendance)

            if delete_d_user_branches:
                daily_d_user_branches = db.session.query(DeliveryUserDailyBranch).filter(
                    DeliveryUserDailyBranch.DUserId == d_user_id, DeliveryUserDailyBranch.IsActive == 1,
                    DeliveryUserDailyBranch.IsDeleted == 0,
                    DeliveryUserDailyBranch.RecordCreatedDate.between(get_today(), (
                            datetime.today() + timedelta(1)).strftime("%Y-%m-%d 00:00:00"))).all()

                for obj in daily_d_user_branches:
                    db.session.delete(obj)

            db.session.commit()
            updated = True
        except Exception as e:
            db.session.rollback()
            error_logger(f'Route: {request.path}').error(e)

        if updated:
            final_data = generate_final_data('SUCCESS')
        else:
            final_data = generate_final_data('DATA_SAVE_FAILED')
    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(form.errors)

    return final_data


@delivery_blueprint.route('/update_darning_instruction', methods=["POST"])
@authenticate('delivery_user')
def update_darning_instruction():
    darning_form = DarningForm()
    if darning_form.validate_on_submit():
        order_garment_id = darning_form.order_garment_id.data
        length = darning_form.length.data

        # Get OrderGarment details from DB
        order_garment_details = db.session.query(OrderGarment).filter(
            OrderGarment.OrderGarmentId == order_garment_id).one_or_none()

        # Getting  OrderInstruction details from DB
        garment_instruction = db.session.query(OrderInstruction).filter(OrderInstruction.InstructionId == 16,
                                                                        OrderInstruction.IsDeleted == 0,
                                                                        OrderInstruction.OrderGarmentId == order_garment_id).one_or_none()
        # Getting BranchCode from Order table
        order_details = db.session.query(Order.BranchCode).filter(Order.OrderId == order_garment_details.OrderId,
                                                                  Order.IsDeleted == 0).one_or_none()
        # Calling get_garment_price func to Get darning garment price from DB
        garment_price = get_garment_price(order_garment_details.GarmentId, 7, order_garment_details.ServiceTatId,
                                          order_details.BranchCode)
        # Calculating total darning amount for the garment
        darning_amount = length * float(garment_price.Price)

        db_order_garment_basic_amount = float(order_garment_details.BasicAmount)
        db_instruction_darning_amount = 0.0 if garment_instruction.DarningGarmentAmount == None else float(
            garment_instruction.DarningGarmentAmount)
        # Subtract DarningGarmentAmount in OrderInstruction table from basic amount in OrderGarment table
        subtracted_order_garment_basic_amount = db_order_garment_basic_amount - db_instruction_darning_amount

        if garment_instruction is not None:
            # Update OrderInstruction, OrderGarment table if the garment length is not zero
            if length != 0.0:
                # Update after subtracting basic amount from the existing OrderInstruction daring amount and add darning
                # amount
                order_garment_details.BasicAmount = subtracted_order_garment_basic_amount + darning_amount
                order_garment_details.ServiceTaxAmount = (subtracted_order_garment_basic_amount + darning_amount) \
                                                         * 18 / 100

                # Updating OrderInstruction of corresponding OrderGarmentId
                garment_instruction.DarningGarmentLength = length
                garment_instruction.DarningGarmentAmount = darning_amount
                order_garment_details.DarningGarmentLength = length

            else:
                # Change delete flag if darning is unselected and update the basic amount with actual amount of garment
                garment_instruction.RecordLastUpdatedDate = get_current_date()
                order_garment_details.BasicAmount = subtracted_order_garment_basic_amount
                order_garment_details.ServiceTaxAmount = subtracted_order_garment_basic_amount * 18 / 100
                garment_instruction.DarningGarmentLength = 0.0
                garment_instruction.DarningGarmentAmount = 0.0
                order_garment_details.DarningGarmentLength = 0.0

            db.session.commit()
            # Updating basic amount in orders table
            delivery_controller_queries.update_basic_amount(order_garment_details.OrderId)

            final_data = generate_final_data('DATA_UPDATED')

        else:
            final_data = generate_final_data('DATA_NOT_FOUND')

    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(darning_form.errors)

    return final_data


@delivery_blueprint.route('/set_d_user_daily_branch', methods=["POST"])
@authenticate('delivery_user')
def set_d_user_daily_branch():
    d_user_daily_branch_form = DUserDailyBranchForm()
    if d_user_daily_branch_form.validate_on_submit():
        branch_codes = d_user_daily_branch_form.branch_codes.data
        d_userid = request.headers.get('user-id')

        #  Get DeliveryUserDailyBranch from DB
        duser_daily_branch_details = db.session.query(DeliveryUserDailyBranch).filter(
            DeliveryUserDailyBranch.DUserId == d_userid, DeliveryUserDailyBranch.IsActive == 1).all()
        try:
            if duser_daily_branch_details is not None:

                for obj in duser_daily_branch_details:
                    # Updating DeliveryUserDailyBranch entry of the delivery user
                    obj.IsActive = 0
                    obj.IsDeleted = 1
                    obj.RecordLastUpdatedDate = get_current_date()
                    db.session.commit()
            try:

                for branch_code in branch_codes:
                    # Add new entry to DeliveryUserDailyBranch table
                    new_duser_daily_branch_details = DeliveryUserDailyBranch(BranchCode=branch_code, DUserId=d_userid,
                                                                             IsDeleted=0, IsActive=1,
                                                                             RecordCreatedDate=get_current_date(),
                                                                             RecordLastUpdatedDate=get_current_date())
                    db.session.add(new_duser_daily_branch_details)
                db.session.commit()
                # Getting default branch details from DeliveryUserBranch table in DB
                default_branches = db.session.query(DeliveryUserBranch.BranchCode,
                                                    DeliveryUserBranch.IsDefaultBranch).filter(
                    DeliveryUserBranch.DUserId == d_userid, DeliveryUserBranch.IsDeleted == 0,
                    DeliveryUserBranch.IsDefaultBranch == True).all()

                for branch_code in default_branches:
                    # Inserting new row to DeliveryUserDailyBranch table
                    new_delivery_user_daily_branch = DeliveryUserDailyBranch(DUserId=d_userid,
                                                                             BranchCode=branch_code[0],
                                                                             IsDeleted=0, IsActive=1,
                                                                             RecordCreatedDate=get_current_date(),
                                                                             RecordLastUpdatedDate=get_current_date(),
                                                                             IsDefault=branch_code[1])
                    # Saving the default branch details to DeliveryUserDailyBranch table for the day.
                    db.session.add(new_delivery_user_daily_branch)
                    db.session.commit()


            except Exception as e:
                error_logger(f'Route: {request.path}').error(e)
        except Exception as e:
            error_logger(f'Route: {request.path}').error(e)

        final_data = generate_final_data('DATA_SAVED')

    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(d_user_daily_branch_form.errors)

    return final_data


@delivery_blueprint.route('/check_discount_code', methods=["POST"])
@authenticate('delivery_user')
def check_discount_code():
    """
    API for checking  the discount code is valid or not.
    """
    check_discount_code_form = CheckDiscountCodeForm()
    log_data = {
        'check_discount_code_form': check_discount_code_form.data
    }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))
    if check_discount_code_form.validate_on_submit():
        discount_code = check_discount_code_form.discount_code.data
        branch_code = check_discount_code_form.branch_code.data
        customer_code = check_discount_code_form.customer_code.data

        source = 'pickup'
        # Result flag
        result = None

        try:
            # First, validate with the EasyRewardz to check whether the discount code is an ER coupon code or not.
            er_validation = er_module.validate_er_coupon(customer_code, branch_code, discount_code)
            log_data = {
            'er_validation': er_validation
                }
            info_logger(f'Route: {request.path}').info(json.dumps(log_data))

            # validation will takes place only if there is no DiscountCode is already applied.
            is_er_coupon = 0

            if er_validation['status']:
                # The original POS discount code is the discount_code coming from the ER response.
                discount_code = er_validation['discount_code']
                is_er_coupon = 1

            # Validating the discount code.
            validation = common_module.validate_discount_code(discount_code, source, None, customer_code, branch_code,
                                                              is_er_coupon)
            log_data = {
            'validation': validation
                }
            info_logger(f'Route: {request.path}').info(json.dumps(log_data))
            if validation['ISVALID']:
                # Store Details from discount validation
                response_code = validation['ISVALID']
                response_message = validation['RESULT']
                app_remarks = validation['DISCOUNTCODE']
                Remarks =  validation['AppRemark']
                response_discount_amount = float(validation['DISCOUNTAMOUNT'])
                # Making a new dict from discount validation results
                result = {'IsValid': response_code, 'Message': response_message,
                          'Discount': response_discount_amount, 'AppRemarks': app_remarks, "Remarks":Remarks}

        except Exception as e:
            error_logger(f'Route: {request.path}').error(e)

        if result is not None:
            final_data = generate_final_data('SUCCESS')
            final_data['result'] = result
        else:
            final_data = generate_final_data('CUSTOM_FAILED', 'Invalid Discount Code')

    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(check_discount_code_form.errors)
    log_data = {
        'final_data': final_data
    }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))
    return final_data


# @delivery_blueprint.route('/get_customer_preferred_time_slots', methods=["GET"])
# @authenticate('delivery_user')
# def get_customer_preferred_time_slots():
#     """
#     APi for getting customer preferred time slots
#     """
#     # Getting all the time slots form DB
#     time_slots = db.session.query(CustomerTimeSlot.TimeSlotId.label('PickupTimeSlotId'), CustomerTimeSlot.TimeSlotFrom,
#                                   CustomerTimeSlot.TimeSlotTo).filter(CustomerTimeSlot.IsDeleted == 0,
#                                                                       CustomerTimeSlot.IsActive == 1).all()

#     final_data = generate_final_data('DATA_FOUND')
#     # Store time_slots to a dict
#     result = {'TimeSlots': SerializeSQLAResult(time_slots).serialize()}
#     final_data['result'] = result

#     return final_data

@delivery_blueprint.route('/get_customer_preferred_time_slots', methods=["GET"])
@authenticate('delivery_user')
def get_customer_preferred_time_slots():
    """
    APi for getting customer preferred time slots
    """
    # Getting all the time slots form DB
    time_slots = f""" EXEC JFSL.dbo.SPTimeSlotFabriccareCustApp @Branch_code =''"""
    time_slots = CallSP(time_slots).execute().fetchall()

    final_data = generate_final_data('DATA_FOUND')
    # Store time_slots to a dict
    result = {'TimeSlots': time_slots}
    final_data['result'] = result

    return final_data


@delivery_blueprint.route('/get_push_notifications', methods=["POST"])
@authenticate('delivery_user')
def get_push_notifications():
    """
    Api for retrieving all push notifications belongs to the corresponding delivery user
    :return: Paginated result
    """
    # Define number ofr rows in a page
    per_page = 5
    push_notification_form = PushNotificationForm()
    if push_notification_form.validate_on_submit():
        page = push_notification_form.page.data
        d_userid = request.headers.get('user-id')

        # Getting the push notification details from db
        notifications = db.session.query(PushNotification.PushNotificationId, PushNotification.DUserId,
                                         PushNotification.ImageUrl, PushNotification.Source, PushNotification.SentBy,
                                         PushNotification.Message, PushNotification.RecordCreatedDate,
                                         PushNotification.IsRead, PushNotification.ReadTime,
                                         PushNotification.Title).filter(PushNotification.DUserId == d_userid).order_by(
            PushNotification.RecordCreatedDate.desc()).paginate(page, per_page, error_out=False)
        # store the details from db to a list for serializing
        notification_list = [document for document in notifications.items]
        if notification_list:
            final_data = generate_final_data('SUCCESS')
            final_data['result'] = SerializeSQLAResult(notification_list).serialize(
                full_date_fields=['ReadTime', 'RecordCreatedDate'])
        else:
            final_data = generate_final_data('DATA_NOT_FOUND')

    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(push_notification_form.errors)

    return final_data


@delivery_blueprint.route('/make_read_notification', methods=["POST"])
@authenticate('delivery_user')
def make_read_notification():
    """
    Api for marking the notification as read
    :return:
    """
    makeread_notificationform = MakeReadReadNotificationForm()
    if makeread_notificationform.validate_on_submit():
        notification_id = makeread_notificationform.notification_id.data
        is_read = False if makeread_notificationform.is_read.data == '' else makeread_notificationform.notification_id.data
        # Getting the corresponding row for updating the is read status
        notification = db.session.query(PushNotification).filter(
            PushNotification.PushNotificationId == notification_id).one_or_none()
        # Updating PushNotification columns
        notification.IsRead = is_read
        notification.ReadTime = get_current_date()
        db.session.commit()

        final_data = generate_final_data('SUCCESS')
    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(makeread_notificationform.errors)

    return final_data


@delivery_blueprint.route('/send_individual_notification', methods=["POST"])
@api_key_required
def send_individual_notification():
    """
    Api for sending individual push notifications
    @return: Notify if fcm token and user is active
    """
    notify_form = NotifyForm()
    if notify_form.validate_on_submit():
        d_userid = notify_form.d_userid.data
        title = notify_form.title.data
        message = notify_form.message.data
        image_url = notify_form.image_url.data

        if len(image_url) < 4000:
            # Getting the fcm token for sending push notification
            final_data = send_test_push_notification(d_userid, title, message, image_url)
        else:
            final_data = generate_final_data('CUSTOM_FAILED', 'IMAGE LENGTH IS TOO LONG')
    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(notify_form.errors)

    return final_data


@delivery_blueprint.route('/save_fcm_token_app_version', methods=["POST"])
# @authenticate('delivery_user')
def save_fcm_token_app_version():
    """
    used to store fcm token,app version,build number
    @return:
    """
    fcm_form = FcmForm()
    if fcm_form.validate_on_submit():
        fcm_token = fcm_form.fcm_token.data
        app_version = fcm_form.app_version.data
        build_number = fcm_form.build_number.data
        user_id = request.headers.get('user-id')

        fcm_token_changed = False
        app_version_changed = False
        build_number_changed = False
        updated = False
        # Getting DeliveryUserLogin details from DB
        active_session = db.session.query(DeliveryUserLogin).filter(DeliveryUserLogin.DUserId == user_id,
                                                                    DeliveryUserLogin.AuthKeyExpiry == 0,
                                                                    DeliveryUserLogin.IsActive == 1).one_or_none()
        if active_session is not None:
            # Getting the FCM token
            try:
                # Updating DeliveryUserLogin row
                if active_session.FcmToken != fcm_token:
                    fcm_token_changed = True
                    active_session.FcmToken = fcm_token

                if active_session.AppVersion != app_version:
                    app_version_changed = True
                    active_session.AppVersion = app_version

                if active_session.BuildNumber != build_number:
                    build_number_changed = True
                    active_session.BuildNumber = build_number

                if fcm_token_changed or app_version_changed or build_number_changed:
                    db.session.commit()
                    updated = True

            except Exception as e:
                # Any DB error is occurred.
                error_logger(f'Route: {request.path}').error(e)
        if updated:
            final_data = generate_final_data('DATA_UPDATED')
        else:
            final_data = generate_final_data('DATA_UPDATE_FAILED')
    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(fcm_form.errors)

    return final_data


@delivery_blueprint.route('/get_branches', methods=["GET"])
# @authenticate('delivery_user')
def get_branches():
    user_id = request.headers.get('user-id')

   # fetchig the delivery users branches from sp using the delivery user id
    query =f"EXEC JFSL.Dbo.SPGetDeliveryUserbranchMappingCustApp @Duserid='{user_id}'"
    delivery_user_branches = CallSP(query).execute().fetchall()
    
    final_data = generate_final_data('DATA_FOUND')
    # Inserting serialized delivery_user_branches to a dict
    result = {
        'Branches': delivery_user_branches
    }
    final_data['result'] = result

    return final_data


@delivery_blueprint.route('/loginLive', methods=["POST"])
@api_key_required
def loginLive():
    """
    Login API for the delivery users.
    @return: Final response contains the access key (if validation successful) or failed message
    """
    json_request = json_input(request)
    # Logging the data in the request into log file.
    info_logger(f'Route: {request.path}').info(json.dumps(json_request))
    if json_request.get('status') == 'failed':
        return json_request, 500
    login_form = LoginForm()
    if login_form.validate_on_submit():
        mobile_number = login_form.mobile_number.data
        password = login_form.password.data
        force_login = login_form.force_login.data
        permit_login = False
        # Generating the password hash to compare with the DB data
        hashed_password = generate_hash(password, 50)
        try:
            # Getting the delivery user details from the DB.
            delivery_user = db.session.query(DeliveryUser.DUserId, DeliveryUser.UserName, DeliveryUser.EmailId,
                                             DeliveryUser.DUserImage).filter(DeliveryUser.MobileNo == mobile_number,
                                                                             DeliveryUser.Password == hashed_password,
                                                                             DeliveryUser.IsDeleted == 0).one_or_none()
            if delivery_user is not None:
                # Checking if there's any active access token is generated or not.
                # If there's an active access token is present, deny the login request.
                access_tokens = db.session.query(DeliveryUserLogin).filter(
                    DeliveryUserLogin.DUserId == delivery_user.DUserId, DeliveryUserLogin.IsActive == 1,
                    DeliveryUserLogin.AuthKeyExpiry == 0).all()
                if len(access_tokens) == 0:
                    permit_login = True
                else:
                    # Active tokens found.
                    if force_login:
                        # Forcefully login. Making all currently active access tokens inactive.
                        for access_token in access_tokens:
                            # Making the access token expire.
                            access_token.IsActive = 0
                            access_token.AuthKeyExpiry = 1
                            db.session.commit()
                        # Made all active tokens expired.
                        permit_login = True

                if permit_login:
                    # If a DisplayName found for a branch, then select DisplayName as the BranchName.
                    select_branch_name = case(
                        [(or_(Branch.DisplayName == None, Branch.DisplayName == ''), Branch.BranchName), ],
                        else_=Branch.DisplayName).label("BranchName")

                    # Select case for converting the value to false if the result is none
                    select_is_default_branch = case([(DeliveryUserBranch.IsDefaultBranch == None, False), ],
                                                    else_=DeliveryUserBranch.IsDefaultBranch).label("IsDefaultBranch")

                    # Getting the branches associated with the delivery user.
                    base_query = db.session.query(DeliveryUserBranch.DUserId, DeliveryUserBranch.BranchCode,
                                                  select_branch_name, select_is_default_branch).join(Branch,
                                                                                                     DeliveryUserBranch.BranchCode == Branch.BranchCode).filter(
                        DeliveryUserBranch.DUserId == delivery_user.DUserId, DeliveryUserBranch.IsDeleted == 0,
                        Branch.IsDeleted == 0)

                    # Getting active delivery user branches if there is no branch with delivery this list is taken
                    all_duser_branches = base_query.filter(Branch.IsActive == 1)

                    # Getting inactive branches
                    inactive_branches = base_query.filter(Branch.IsActive == 0).all()

                    # Populating a list of inactive branches
                    inactive_branch_list = [i.BranchCode for i in inactive_branches]

                    if len(inactive_branch_list) > 0:
                        # if DUserId found in DeliveryReschedule table take it else take from DeliveryRequest table
                        select_delivery_user_id = case(
                            [(DeliveryReschedule.DUserId == None, DeliveryRequest.DUserId), ],
                            else_=DeliveryReschedule.DUserId).label("DUserId")

                        # Getting inactive branch details which have delivery
                        inactive_branch_with_delivery = db.session.query(select_delivery_user_id, Branch.BranchCode,
                                                                         select_branch_name,
                                                                         select_is_default_branch).distinct(
                            Branch.BranchCode, Branch.BranchName).outerjoin(Branch,
                                                                            DeliveryRequest.BranchCode == Branch.BranchCode).join(
                            Customer, DeliveryRequest.CustomerId == Customer.CustomerId).join(DeliveryUserBranch,
                                                                                              DeliveryUserBranch.BranchCode == DeliveryRequest.BranchCode).outerjoin(
                            DeliveryReschedule,
                            DeliveryReschedule.DeliveryRequestId == DeliveryRequest.DeliveryRequestId).join(Order,
                                                                                                            DeliveryRequest.OrderId == Order.OrderId).join(
                            DeliveryUser, select_delivery_user_id == DeliveryUser.DUserId).outerjoin(Delivery,
                                                                                                     Delivery.DeliveryRequestId == DeliveryRequest.DeliveryRequestId).filter(
                            select_delivery_user_id == delivery_user.DUserId,
                            DeliveryRequest.BranchCode.in_(inactive_branch_list),
                            or_(DeliveryRequest.WalkIn == 0, DeliveryRequest.WalkIn == None),
                            or_(Order.IsDeleted == 0, Order.IsDeleted == None), DeliveryRequest.IsDeleted == 0,
                            Delivery.DeliveryId == None,
                            or_(DeliveryReschedule.IsDeleted == 0, DeliveryReschedule.IsDeleted == None),
                            DeliveryUserBranch.IsDeleted == 0, DeliveryUserBranch.DUserId == delivery_user.DUserId)

                        if inactive_branch_with_delivery:
                            # Join branch with delivery to the branch details
                            all_duser_branches = all_duser_branches.union(inactive_branch_with_delivery)

                    all_duser_branches = SerializeSQLAResult(all_duser_branches).serialize()
                    # Removing DUserId from list
                    [i.pop('DUserId') for i in all_duser_branches]

                    # Getting selected branch details from Db within date range
                    daily_d_user_branches = db.session.query(DeliveryUserDailyBranch.BranchCode, select_branch_name,
                                                             select_is_default_branch).join(DeliveryUserBranch,
                                                                                            DeliveryUserBranch.BranchCode == DeliveryUserDailyBranch.BranchCode).join(
                        Branch, Branch.BranchCode == DeliveryUserDailyBranch.BranchCode).filter(
                        and_(DeliveryUserBranch.DUserId == delivery_user.DUserId,
                             DeliveryUserDailyBranch.DUserId == delivery_user.DUserId),
                        DeliveryUserDailyBranch.IsActive == 1, DeliveryUserDailyBranch.IsDeleted == 0,
                        DeliveryUserBranch.IsDeleted == 0,
                        DeliveryUserDailyBranch.RecordCreatedDate.between(get_today(),
                                                                          (datetime.today() + timedelta(1)).strftime(
                                                                              "%Y-%m-%d 00:00:00"))).all()

                    selected_branches = SerializeSQLAResult(daily_d_user_branches).serialize()

                    # If the delivery user is found then add login details into DeliveryUserLogin table.
                    access_key = jwt.encode({'id': str(uuid.uuid1())},
                                            current_app.config['JWT_SECRET_KEY'] + str(delivery_user.DUserId),
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

                    new_delivery_user_login = DeliveryUserLogin(DUserId=delivery_user.DUserId,
                                                                LoginTime=get_current_date(),
                                                                AuthKey=access_key.decode('utf-8'), AuthKeyExpiry=0,
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
                        db.session.add(new_delivery_user_login)
                        db.session.commit()
                        final_data = generate_final_data("DATA_SAVED")
                        result = {'AccessKey': access_key.decode('utf-8'),
                                  'UserId': delivery_user.DUserId,
                                  'Name': delivery_user.UserName,
                                  'Email': delivery_user.EmailId,
                                  "FileName": delivery_user.DUserImage,
                                  'BranchCodes': all_duser_branches,
                                  'SelectedBranches': selected_branches
                                  }
                        final_data['result'] = result
                    except Exception as e:
                        db.session.rollback()
                        error_logger(f'Route: {request.path}').error(e)
                        final_data = generate_final_data('DATA_SAVE_FAILED')
                else:
                    # Active access tokens are found for this delivery user. So prevent
                    # the delivery user from logging in.
                    final_data = generate_final_data('CUSTOM_FAILED',
                                                     'Another active access token found. Failed to login.')
            else:
                # If the delivery user is not found, generate the error.
                final_data = generate_final_data('DATA_NOT_FOUND')
        except Exception as e:
            # Any DB error is occurred.
            error_logger(f'Route: {request.path}').error(e)
            final_data = generate_final_data('FAILED')

    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(login_form.errors)
    log_data = {
        'final_data': final_data
    }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))

    return final_data


@delivery_blueprint.route('/login', methods=["POST"])
@api_key_required
def login():
    """
    Login API for the delivery users.
    @return: Final response contains the access key (if validation successful) or failed message
    """
    json_request = json_input(request)
    # Logging the data in the request into log file.
    info_logger(f'Route: {request.path}').info(json.dumps(json_request))
    if json_request.get('status') == 'failed':
        return json_request, 500
    login_form = LoginForm()
    if login_form.validate_on_submit():
        mobile_number = login_form.mobile_number.data
        password = login_form.password.data
        force_login = login_form.force_login.data
        permit_login = False
        # Generating the password hash to compare with the DB data
        hashed_password = generate_hash(password, 50)
        try:
            # Getting the delivery user details from the DB.
            delivery_user = db.session.query(DeliveryUser.DUserId, DeliveryUser.UserName, DeliveryUser.EmailId,
                                             DeliveryUser.DUserImage).filter(DeliveryUser.MobileNo == mobile_number,
                                                                             DeliveryUser.Password == hashed_password,
                                                                             DeliveryUser.IsDeleted == 0).one_or_none()
            if delivery_user is not None:
                # Checking if there's any active access token is generated or not.
                # If there's an active access token is present, deny the login request.
                access_tokens = db.session.query(DeliveryUserLogin).filter(
                    DeliveryUserLogin.DUserId == delivery_user.DUserId, DeliveryUserLogin.IsActive == 1,
                    DeliveryUserLogin.AuthKeyExpiry == 0).all()
                if len(access_tokens) == 0:
                    permit_login = True
                else:
                    # Active tokens found.
                    if force_login:
                        # Forcefully login. Making all currently active access tokens inactive.
                        for access_token in access_tokens:
                            # Making the access token expire.
                            access_token.IsActive = 0
                            access_token.AuthKeyExpiry = 1
                            db.session.commit()
                        # Made all active tokens expired.
                        permit_login = True

                if permit_login:
                    # If a DisplayName found for a branch, then select DisplayName as the BranchName.
                    select_branch_name = case(
                        [(or_(Branch.DisplayName == None, Branch.DisplayName == ''), Branch.BranchName), ],
                        else_=Branch.DisplayName).label("BranchName")

                    # Select case for converting the value to false if the result is none
                    select_is_default_branch = case([(DeliveryUserBranch.IsDefaultBranch == None, False), ],
                                                    else_=DeliveryUserBranch.IsDefaultBranch).label("IsDefaultBranch")

                    # Getting the branches associated with the delivery user.
                    base_query = db.session.query(DeliveryUserBranch.DUserId, DeliveryUserBranch.BranchCode,
                                                  select_branch_name, select_is_default_branch).join(Branch,
                                                                                                     DeliveryUserBranch.BranchCode == Branch.BranchCode).filter(
                        DeliveryUserBranch.DUserId == delivery_user.DUserId, DeliveryUserBranch.IsDeleted == 0,
                        Branch.IsDeleted == 0)

                    # Getting active delivery user branches if there is no branch with delivery this list is taken
                    all_duser_branches = base_query.filter(Branch.IsActive == 1)

                    # Getting inactive branches
                    inactive_branches = base_query.filter(Branch.IsActive == 0).all()

                    # Populating a list of inactive branches
                    inactive_branch_list = [i.BranchCode for i in inactive_branches]

                    if len(inactive_branch_list) > 0:
                        # if DUserId found in DeliveryReschedule table take it else take from DeliveryRequest table
                        select_delivery_user_id = case(
                            [(DeliveryReschedule.DUserId == None, DeliveryRequest.DUserId), ],
                            else_=DeliveryReschedule.DUserId).label("DUserId")

                        # Getting inactive branch details which have delivery
                        inactive_branch_with_delivery = db.session.query(select_delivery_user_id, Branch.BranchCode,
                                                                         select_branch_name,
                                                                         select_is_default_branch).distinct(
                            Branch.BranchCode, Branch.BranchName).outerjoin(Branch,
                                                                            DeliveryRequest.BranchCode == Branch.BranchCode).join(
                            Customer, DeliveryRequest.CustomerId == Customer.CustomerId).join(DeliveryUserBranch,
                                                                                              DeliveryUserBranch.BranchCode == DeliveryRequest.BranchCode).outerjoin(
                            DeliveryReschedule,
                            DeliveryReschedule.DeliveryRequestId == DeliveryRequest.DeliveryRequestId).join(Order,
                                                                                                            DeliveryRequest.OrderId == Order.OrderId).join(
                            DeliveryUser, select_delivery_user_id == DeliveryUser.DUserId).outerjoin(Delivery,
                                                                                                     Delivery.DeliveryRequestId == DeliveryRequest.DeliveryRequestId).filter(
                            select_delivery_user_id == delivery_user.DUserId,
                            DeliveryRequest.BranchCode.in_(inactive_branch_list),
                            or_(DeliveryRequest.WalkIn == 0, DeliveryRequest.WalkIn == None),
                            or_(Order.IsDeleted == 0, Order.IsDeleted == None), DeliveryRequest.IsDeleted == 0,
                            Delivery.DeliveryId == None,
                            or_(DeliveryReschedule.IsDeleted == 0, DeliveryReschedule.IsDeleted == None),
                            DeliveryUserBranch.IsDeleted == 0, DeliveryUserBranch.DUserId == delivery_user.DUserId)

                        if inactive_branch_with_delivery:
                            # Join branch with delivery to the branch details
                            all_duser_branches = all_duser_branches.union(inactive_branch_with_delivery)

                    all_duser_branches = SerializeSQLAResult(all_duser_branches).serialize()
                    # Removing DUserId from list
                    [i.pop('DUserId') for i in all_duser_branches]

                    # Getting selected branch details from Db within date range
                    daily_d_user_branches = db.session.query(DeliveryUserDailyBranch.BranchCode, select_branch_name,
                                                             select_is_default_branch).join(DeliveryUserBranch,
                                                                                            DeliveryUserBranch.BranchCode == DeliveryUserDailyBranch.BranchCode).join(
                        Branch, Branch.BranchCode == DeliveryUserDailyBranch.BranchCode).filter(
                        and_(DeliveryUserBranch.DUserId == delivery_user.DUserId,
                             DeliveryUserDailyBranch.DUserId == delivery_user.DUserId),
                        DeliveryUserDailyBranch.IsActive == 1, DeliveryUserDailyBranch.IsDeleted == 0,
                        DeliveryUserBranch.IsDeleted == 0,
                        DeliveryUserDailyBranch.RecordCreatedDate.between(get_today(),
                                                                          (datetime.today() + timedelta(1)).strftime(
                                                                              "%Y-%m-%d 00:00:00"))).all()

                    selected_branches = SerializeSQLAResult(daily_d_user_branches).serialize()

                    # If the delivery user is found then add login details into DeliveryUserLogin table.
                    access_key = jwt.encode({'id': str(uuid.uuid1())},
                                            current_app.config['JWT_SECRET_KEY'] + str(delivery_user.DUserId),
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

                    new_delivery_user_login = DeliveryUserLogin(DUserId=delivery_user.DUserId,
                                                                LoginTime=get_current_date(),
                                                                AuthKey=access_key.decode('utf-8'), AuthKeyExpiry=0,
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
                        db.session.add(new_delivery_user_login)
                        db.session.commit()
                        final_data = generate_final_data("DATA_SAVED")
                        result = {'AccessKey': access_key.decode('utf-8'),
                                  'UserId': delivery_user.DUserId,
                                  'Name': delivery_user.UserName,
                                  'Email': delivery_user.EmailId,
                                  "FileName": delivery_user.DUserImage,
                                  'BranchCodes': all_duser_branches,
                                  'SelectedBranches': selected_branches
                                  }
                        final_data['result'] = result
                    except Exception as e:
                        db.session.rollback()
                        error_logger(f'Route: {request.path}').error(e)
                        final_data = generate_final_data('DATA_SAVE_FAILED')
                else:
                    # Active access tokens are found for this delivery user. So prevent
                    # the delivery user from logging in.
                    final_data = generate_final_data('CUSTOM_FAILED',
                                                     'Another active access token found. Failed to login.')
            else:
                # If the delivery user is not found, generate the error.
                final_data = generate_final_data('DATA_NOT_FOUND')
        except Exception as e:
            # Any DB error is occurred.
            error_logger(f'Route: {request.path}').error(e)
            final_data = generate_final_data('FAILED')

    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(login_form.errors)
    log_data = {
        'final_data': final_data
    }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))

    return final_data


@delivery_blueprint.route('/logout', methods=["POST"])
@authenticate('delivery_user')
def logout():
    """
    Logout API for the delivery users.
    @return: If the validations are successful, make the access token expire
    by changing the values(AuthKeyExpiry, IsActive) in the DeliveryUserLogin table.
    """
    result = False
    try:
        user_id = request.headers.get('user_id')
        access_key = request.headers.get('access_key')
        login_data = db.session.query(DeliveryUserLogin).filter(DeliveryUserLogin.DUserId == user_id,
                                                                DeliveryUserLogin.AuthKey == access_key,
                                                                DeliveryUserLogin.AuthKeyExpiry == 0).one_or_none()
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


@delivery_blueprint.route('/alerts', methods=["GET"])
@authenticate('delivery_user')
def alerts():
    """
    API for getting the latest alerts from the server (If any).
    @return:
    """
    attendance = None
    user_id = request.headers.get('user-id')
    try:
        # Checking for today's attendance.
        attendance = delivery_controller_queries.attendance_for_today(user_id)
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


@delivery_blueprint.route('/clock_in', methods=["POST"])
@authenticate('delivery_user')
def clock_in():
    """
    API for marking the clock in time of the delivery user.
    @return:
    """
    clock_in_form = ClockInForm()
    log_data = {
                'clock_in_form:': clock_in_form.data
            }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))
    if clock_in_form.validate_on_submit():
        user_id = request.headers.get('user-id')
        today = datetime.today().strftime("%Y-%m-%d")
        lat = None if clock_in_form.lat.data == '' else clock_in_form.lat.data
        long = None if clock_in_form.long.data == '' else clock_in_form.long.data
        clocked_in = False
        error_msg = ''
        # Minus a day to the current date
        previous_day = (datetime.today() - timedelta(1))
        # Formatting the previous date
        formatted_previous_day = previous_day.strftime("%Y-%m-%d 00:00:00")

        try:
            # Checking for today's attendance.
            attendance_record_of_today = delivery_controller_queries.attendance_for_today(user_id)
            if attendance_record_of_today is None:
                # No previous clock in record found for today.
                new_clock_in = DeliveryUserAttendance(
                    DUserId=user_id,
                    Date=today,
                    ClockInTime=get_current_date(),
                    ClockInLat=lat,
                    ClockInLong=long,
                    RecordCreatedDate=get_current_date()
                )
                # Saving the clock in details for the day.
                db.session.add(new_clock_in)
                db.session.commit()

                #  Get DeliveryUserDailyBranch from DB
                duser_daily_branch_details = db.session.query(DeliveryUserDailyBranch).filter(
                    DeliveryUserDailyBranch.DUserId == user_id, DeliveryUserDailyBranch.IsActive == 1).all()

                if duser_daily_branch_details is not None:

                    for obj in duser_daily_branch_details:
                        # Updating DeliveryUserDailyBranch entry of the delivery user
                        obj.IsActive = 0
                        obj.IsDeleted = 1
                        obj.RecordLastUpdatedDate = get_current_date()

                # Getting default branch details from DeliveryUserBranch table in DB
                default_branches = db.session.query(DeliveryUserBranch.BranchCode,
                                                    DeliveryUserBranch.IsDefaultBranch).filter(
                    DeliveryUserBranch.DUserId == user_id, DeliveryUserBranch.IsDeleted == 0,
                    DeliveryUserBranch.IsDefaultBranch == True).all()

                for branch_code in default_branches:
                    # Inserting new row to DeliveryUserDailyBranch table
                    new_delivery_user_daily_branch = DeliveryUserDailyBranch(DUserId=user_id,
                                                                             BranchCode=branch_code[0],
                                                                             IsDeleted=0, IsActive=1,
                                                                             RecordCreatedDate=get_current_date(),
                                                                             RecordLastUpdatedDate=get_current_date(),
                                                                             IsDefault=branch_code[1])
                    # Saving the default branch details to DeliveryUserDailyBranch table for the day.
                    db.session.add(new_delivery_user_daily_branch)
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
    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(clock_in_form.errors)
    log_data = {
                'final_data:': final_data
            }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))
    return final_data


@delivery_blueprint.route('/clock_out', methods=["POST"])
@authenticate('delivery_user')
def clock_out():
    """
    API for marking the clock out time of the delivery user.
    @return:
    """
    clock_out_form = ClockOutForm()
    if clock_out_form.validate_on_submit():
        user_id = request.headers.get('user-id')
        lat = None if clock_out_form.lat.data == '' else clock_out_form.lat.data
        long = None if clock_out_form.long.data == '' else clock_out_form.long.data
        today = datetime.today().strftime("%Y-%m-%d")
        clocked_out = False
        error_msg = ''
        try:
            # Checking for today's attendance.
            attendance_record_of_today = db.session.query(DeliveryUserAttendance).filter(
                DeliveryUserAttendance.DUserId == user_id,
                DeliveryUserAttendance.Date == today,
                DeliveryUserAttendance.IsDeleted == 0).one_or_none()
            if attendance_record_of_today is not None:
                # A attendance record found for today.
                if attendance_record_of_today.ClockOutTime is None:
                    # No previous clock out time saved for today.
                    attendance_record_of_today.ClockOutLat = lat
                    attendance_record_of_today.ClockOutLong = long
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
    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(clock_out_form.errors)

    return final_data





@delivery_blueprint.route('/home', methods=["POST"])
# @authenticate('delivery_user')
def home():
    """
    API for getting the home screen data.
    @return:
    """

    home_form = HomeForm()

    if home_form.validate_on_submit():
        user_id = request.headers.get('user-id')
        total_pickup_requests = 0
        pickups_completed = 0
        total_delivery_requests = 0
        delivery_completed = 0
        cash_collected = 0
        card_collected = 0
        online_payment_collected = 0
        travelled_distance = 0.0
        branch_codes = home_form.branch_codes.data
        today = get_today()
        tomorrow = (datetime.today() + timedelta(1)).strftime("%Y-%m-%d 00:00:00")
        payment_modes = []
        log_data = {
                'home_form:': home_form.data
            }
        info_logger(f'Route: {request.path}').info(json.dumps(log_data))

        try:

            if not branch_codes:
                # Getting the branches associated with the user.
                delivery_user_branches = delivery_controller_queries.get_delivery_user_branches(user_id)

            else:
                # Branch codes are given.
                delivery_user_branches = branch_codes
            payment_modes = []

            for branch in delivery_user_branches:
                query = f"EXEC {SERVER_DB}..GetPaymentMode @branchcode={branch}"
                result = CallSP(query).execute().fetchall()
                payment_modes.append(result)
            payment_m = []
            for payment in payment_modes:
                for payment in payment:
                    p = payment['PaymentMode']
                    payment_m.append(p)
            payment_mode = set(payment_m)
            payment_mode = list(payment_mode)
            payment_mode.append('PaytmEDC') if get_paytm_credentials(user_id) else payment_mode

            pickups_completed = PickupDetails(user_id).current_completed_pickup_count(delivery_user_branches)

            # total_pickup_requests = PickupDetails(user_id).current_pickup_count(delivery_user_branches)
            branches = ','.join(branch_codes)

            travel_logs = db.session.query(TravelLog).filter(TravelLog.DUserId == user_id,
                                                             TravelLog.RecordCreatedDate >= today,
                                                             TravelLog.RecordCreatedDate <= tomorrow).all()

            # Calculating the total travel distance from the travel logs.
            travelled_distance = TravelDistanceCalculator().loop(travel_logs).distance()


        except Exception as e:
            error_logger(f'Route: {request.path}').error(e)

        # Checking for today's attendance.
        attendance_record_of_today = db.session.query(DeliveryUserAttendance).filter(
            DeliveryUserAttendance.DUserId == user_id,
            DeliveryUserAttendance.Date == today,
            DeliveryUserAttendance.IsDeleted == 0).one_or_none()

        if attendance_record_of_today is not None:
            clock_in_status = True
        else:
            clock_in_status = False
        branches = ','.join(branch_codes)

        total_pickup = 0
        total_delivery = 0
        completed_pickups = 0
        pending_pickups = 0
        pending_delivery = 0
        completed_delivery = 0
        no_of_orders = 0
        pending_collection = 0
        no_of_customers = 0
        cash_collection = 0
        card_collection = 0
        online_payment = 0

        sp_result = None
        try:

            sp_query = f"EXEC JFSL.[dbo].[SPFabDashBoard] @deliveryuserId= '{user_id}',@branch='{branches}'"
            log_data = {
                'sp_query:': sp_query
            }
            info_logger(f'Route: {request.path}').info(json.dumps(log_data))
            
            sp_result = CallSP(sp_query).execute().fetchall()
            
            db.session.commit()

            pending_pickups = sp_result[0]['PendingPickups']
            completed_pickups = sp_result[0]['CompletedPickups']
            total_pickup = sp_result[0]['TotalPickups']  # Assuming count is the first column in the result
            total_delivery = sp_result[0]['TotalDeliveries']

            pending_delivery = sp_result[0]['PendingDelivery']
            completed_delivery = sp_result[0]['CompletedDeliveries']
            no_of_orders = sp_result[0]['noOfOrders']
            pending_collection = sp_result[0]['pendingForCollection']
            no_of_customers = sp_result[0]['noOfCustomers']
            cash_collection = sp_result[0]['CashCollection']
            card_collection = sp_result[0]['CardCollection']
            online_payment = sp_result[0]['OnlinePayment']
        except Exception as e:
            error_logger(f'Route: {request.path}').error(e)

    
        
        if sp_result is not None:

            final_data = generate_final_data('DATA_FOUND')
            msg = "We've got something new for you! To continue enjoying the latest features and improvements, please update your app to the latest version."
            result = {'PendingPickups': pending_pickups,
                      'CompletedPickups': completed_pickups,
                      'TotalPickups': total_pickup,
                      'PendingDelivery': pending_delivery,
                      'CompletedDeliveries': completed_delivery,
                      'TotalDeliveries': total_delivery, 'CashCollection': cash_collection,
                      'noOfOrders': no_of_orders,
                      'pendingForCollection': pending_collection,
                      'noOfCustomers': no_of_customers,
                      'CardCollection': card_collection, 'OnlinePayment': online_payment,
                      'TotalTravelled': travelled_distance,
                      'ClockInStatus': clock_in_status,
                      'PaymentMode': payment_mode,
                      'MinVersion': 83,
                      'IosVersion': 83,
                      'IsForce': True,
                      'ForceUpdateMsg': msg
                      }
            final_data['result'] = result
            

        else:
            final_data = generate_final_data('DATA_NOT_FOUND')
    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(home_form.errors)
        
    log_data = {
                'final_data:': final_data
            }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))
    return final_data


@delivery_blueprint.route('/get_activity_listB4SP', methods=["POST"])
@authenticate('delivery_user')
def get_activity_listB4SP():
    """
    API for getting the list of pickup requests that need to be picked up by the pickup/delivery user.
    """
    activity_list_form = ActivityListForm()

    if activity_list_form.validate_on_submit():
        user_id = request.headers.get('user-id')
        activity_list = []
        branch_codes = activity_list_form.branch_codes.data
        sorting_method = activity_list_form.sorting_method.data
        # lat and long are optional. If no data provided, NULL will be passed to the stored procedure.
        lat = None if activity_list_form.lat.data == '' else activity_list_form.lat.data
        long = None if activity_list_form.long.data == '' else activity_list_form.long.data
        delivery_type = None if activity_list_form.delivery_type.data == '' else activity_list_form.delivery_type.data

        only_tomorrow = activity_list_form.only_tomorrow.data

        if only_tomorrow:
            # If only_tomorrow param present in the request, return only tomorrow's activities.
            tomorrow = (datetime.today() + timedelta(1)).strftime("%Y-%m-%d 00:00:00")
        else:
            tomorrow = None

        try:

            if not branch_codes:
                # Getting the branches associated with the user.
                delivery_user_branches = delivery_controller_queries.get_delivery_user_branches(user_id)
            else:
                # Branch codes are given.
                delivery_user_branches = branch_codes

            # Calculating the distance in KM between the delivery user's lat and long to
            # the customer address' lat and long.
            distance_in_km = func.dbo.GetDistance(lat, long, CustomerAddres.Lat,
                                                  CustomerAddres.Long).label('Distance')

            # If the pickup is rescheduled, then select RescheduledDate, else select PickupDate.
            select_activity_date = case([(PickupReschedule.RescheduledDate == None, PickupRequest.PickupDate), ],
                                        else_=PickupReschedule.RescheduledDate).label("ActivityDate")

            # If the pickup is rescheduled, then select reschedule's time slot from, else time slot from of
            # the pickup request.
            select_time_slot_from = case([(PickupReschedule.TimeSlotFrom == None, PickupRequest.TimeSlotFrom), ],
                                         else_=PickupReschedule.TimeSlotFrom).label("TimeSlotFrom")

            # If the pickup is rescheduled, then select reschedule's time slot to, else time slot to of
            # the pickup request.
            select_time_slot_to = case([(PickupReschedule.TimeSlotTo == None, PickupRequest.TimeSlotTo), ],
                                       else_=PickupReschedule.TimeSlotTo).label("TimeSlotTo")

            # Getting the pending pickup requests.
            # pending_pickups = delivery_controller_queries.get_pending_pickups(tomorrow,
            #                                                                   select_activity_date,
            #                                                                   select_time_slot_from,
            #                                                                   select_time_slot_to, lat,
            #                                                                   long,
            #                                                                   delivery_user_branches, user_id)

            pending_pickups = PickupDetails(user_id).get_pending_pickups(tomorrow, select_activity_date,
                                                                         select_time_slot_from, select_time_slot_to,
                                                                         lat, long, delivery_user_branches)
            # If the delivery is rescheduled, then select RescheduledDate, else select DeliveryDate.
            select_activity_date = case([(DeliveryReschedule.RescheduledDate == None, DeliveryRequest.DeliveryDate), ],
                                        else_=DeliveryReschedule.RescheduledDate).label("ActivityDate")

            # If the delivery is rescheduled, then select reschedule's time slot from, else time slot from of
            # the pickup request.
            select_time_slot_from = case([(DeliveryReschedule.TimeSlotFrom == None, DeliveryRequest.TimeSlotFrom), ],
                                         else_=DeliveryReschedule.TimeSlotFrom).label("TimeSlotFrom")

            # If the delivery is rescheduled, then select reschedule's time slot to, else time slot to of
            # the pickup request.
            select_time_slot_to = case([(DeliveryReschedule.TimeSlotTo == None, DeliveryRequest.TimeSlotTo), ],
                                       else_=DeliveryReschedule.TimeSlotTo).label("TimeSlotTo")

            # Getting the pending delivery requests.
            # pending_deliveries = delivery_controller_queries.get_pending_deliveries(tomorrow,
            #                                                                         select_activity_date,
            #                                                                         select_time_slot_from,
            #                                                                         select_time_slot_to,
            #                                                                         lat, long,
            #                                                                         delivery_user_branches, user_id)
            pending_deliveries = DeliveryDetails(user_id).get_pending_deliveries(tomorrow, select_activity_date,
                                                                                 select_time_slot_from,
                                                                                 select_time_slot_to, lat, long,
                                                                                 delivery_user_branches, delivery_type)

            if sorting_method == 'TIME_SLOT':
                # Sorting based on Activity Date, TimeSlotFrom and TimeSlotTo
                activity_list = pending_pickups.union(pending_deliveries).order_by(select_activity_date.asc(),
                                                                                   select_time_slot_from.asc(),
                                                                                   select_time_slot_to.asc(),
                                                                                   ).all()
            elif sorting_method == 'NEAR_ME':
                # Sorting the activity list based on nearest distance from the delivery user.
                activity_list = pending_pickups.union(pending_deliveries).order_by(distance_in_km.asc()).all()
            elif sorting_method == 'BOTH':
                # Sorting the activity list based on Activity Date, TimeSlotFrom, TimeSlotTo
                # and nearest distance from the delivery user.
                activity_list = pending_pickups.union(pending_deliveries).order_by(select_activity_date.asc(),
                                                                                   select_time_slot_from.asc(),
                                                                                   select_time_slot_to.asc(),
                                                                                   distance_in_km.asc()).all()
            else:
                # Default sorting based on Activity Date, TimeSlotFrom and TimeSlotTo
                activity_list = pending_pickups.union(pending_deliveries).order_by(
                    select_activity_date.asc(),
                    select_time_slot_from.asc(),
                    select_time_slot_to.asc()).all()

        except Exception as e:
            error_logger(f'Route: {request.path}').error(e)

        if activity_list is not None:
            # Serializing the activity list.
            activity_list = SerializeSQLAResult(activity_list).serialize()
            if len(activity_list) > 0:
                # Now for each activity, retrieve service tats and service types belongs
                # to that pickup request Id

                for activity in activity_list:

                    # If the ActivityDate is less than current date, mention this order as LATE
                    activity_date = activity['ActivityDate']
                    # Convert string date to datetime object.
                    activity_date_obj = datetime.strptime(activity_date, "%d-%m-%Y")
                    # From the date object, convert the date to YYYY-MM-DD format.
                    formatted_activity_date = activity_date_obj.strftime("%Y-%m-%d %H:%M:%S")
                    try:
                        # If delivery replace  customer preferred time slot to
                        if activity['ActivityType'] == 'Delivery':
                            # If CustomerPreferredTimeSlot in DeliveryReschedule then select it, Else select from
                            # DeliveryRequest
                            select_time_slot = case(
                                [(DeliveryReschedule.CustomerPreferredTimeSlot == None,
                                  DeliveryRequest.CustomerPreferredTimeSlot), ],
                                else_=DeliveryReschedule.CustomerPreferredTimeSlot).label("TimeSlot")
                            # If DeliveryRequestId in DeliveryReschedule is none then select DeliveryRequestId from
                            # DeliveryRequest
                            select_delivery_id = case([(DeliveryReschedule.DeliveryRequestId == None,
                                                        DeliveryRequest.DeliveryRequestId), ],
                                                      else_=DeliveryReschedule.DeliveryRequestId).label(
                                "ActivityId")
                            # Getting delivery details from DB
                            cus_prefer_date = db.session.query(DeliveryRequest.DeliveryRequestId,
                                                               DeliveryRequest.CustomerPreferredDate,
                                                               select_time_slot).join(
                                DeliveryReschedule,
                                DeliveryRequest.DeliveryRequestId == DeliveryReschedule.DeliveryRequestId).outerjoin(
                                CustomerTimeSlot,
                                DeliveryReschedule.CustomerPreferredTimeSlot == CustomerTimeSlot.TimeSlotId or DeliveryRequest.CustomerPreferredTimeSlot == CustomerTimeSlot.TimeSlotId).filter(
                                select_delivery_id == activity['ActivityId'],
                                DeliveryRequest.IsDeleted == 0, or_(DeliveryReschedule.IsDeleted == 0,
                                                                    DeliveryReschedule.IsDeleted == None)).one_or_none()

                            if cus_prefer_date is not None:

                                if cus_prefer_date.TimeSlot is not None:
                                    # Getting the serialized value of TimeSlotFrom from DB
                                    time_slot_from = SerializeSQLAResult(
                                        db.session.query(CustomerTimeSlot.TimeSlotFrom).filter(
                                            CustomerTimeSlot.TimeSlotId == cus_prefer_date.TimeSlot,
                                            CustomerTimeSlot.IsActive == 1).one_or_none()).serialize_one()

                                    # Getting the serialized value of TimeSlotTo from DB
                                    time_slot_to = SerializeSQLAResult(
                                        db.session.query(CustomerTimeSlot.TimeSlotTo).filter(
                                            CustomerTimeSlot.TimeSlotId == cus_prefer_date.TimeSlot,
                                            CustomerTimeSlot.IsActive == 1).one_or_none()).serialize_one()

                                    # Update TimeSlotFrom and TimeSlotTo in looped activity with entry in
                                    # CustomerTimeSlot table
                                    activity.update({'TimeSlotFrom': time_slot_from['TimeSlotFrom'],
                                                     'TimeSlotTo': time_slot_to['TimeSlotTo']})
                            else:
                                delivery_time_slot = SerializeSQLAResult(db.session.query(CustomerTimeSlot.TimeSlotFrom,
                                                                                          CustomerTimeSlot.TimeSlotTo).outerjoin(
                                    DeliveryRequest,
                                    CustomerTimeSlot.TimeSlotId == DeliveryRequest.CustomerPreferredTimeSlot
                                ).filter(
                                    CustomerTimeSlot.IsDeleted == 0,
                                    CustomerTimeSlot.IsActive == 1, DeliveryRequest.DeliveryRequestId == activity[
                                        'ActivityId']).one_or_none()).serialize_one()
                                if delivery_time_slot is not None:
                                    activity.update({'TimeSlotFrom': delivery_time_slot['TimeSlotFrom'],
                                                     'TimeSlotTo': delivery_time_slot['TimeSlotTo']})
                                else:
                                    # Update TimeSlotFrom and TimeSlotTo in looped activity as NUll
                                    activity.update({'TimeSlotFrom': 'NULL', 'TimeSlotTo': 'NULL'})

                    except Exception as e:
                        error_logger(f'Route: {request.path}').error(e)

                    # If the activity is late than today, add a late flag.
                    if formatted_activity_date < get_today():
                        activity['IsLate'] = 1
                    else:
                        activity['IsLate'] = 0
                    # Edited by MMM
                # Adding a day to the current date
                next_date = (datetime.today() + timedelta(1))
                # Formatting the added date
                formatted_next_date = next_date.strftime("%Y-%m-%d 00:00:00")
                # Getting travel log details from DB
                completed_activities = db.session.query(TravelLog.OrderId,
                                                        TravelLog.RecordCreatedDate.label('ActivityTime'),
                                                        TravelLog.Activity, TravelLog.Lat, TravelLog.Long).filter(
                    TravelLog.DUserId == user_id,
                    TravelLog.RecordCreatedDate.between(get_today(), formatted_next_date)).order_by(
                    TravelLog.RecordCreatedDate.asc()).all()
                logs_details = SerializeSQLAResult(completed_activities).serialize(full_date_fields=['ActivityTime'])

                # Edited by MMM

                final_data = generate_final_data('DATA_FOUND')
                final_data['result'] = activity_list
                final_data['CompletedActivities'] = logs_details

            else:
                final_data = generate_final_data('DATA_NOT_FOUND')

        else:
            final_data = generate_final_data('DATA_NOT_FOUND')
    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(activity_list_form.errors)

    return final_data


# @delivery_blueprint.route('/get_activity_list', methods=["POST"])
# # @authenticate('store_user')
# def get_activity_list():
#     """
#         API for getting the pending activities in a branch.
#         @return:
#         """
#     activity_list_form = ActivityListForm()
#     if activity_list_form.validate_on_submit():
#         user_id = request.headers.get('user-id')
#         activity_list = []
#         branch_codes = activity_list_form.branch_codes.data

#         sorting_method = activity_list_form.sorting_method.data
#         # lat and long are optional. If no data provided, NULL will be passed to the stored procedure.
#         lat = None if activity_list_form.lat.data == '' else activity_list_form.lat.data
#         long = None if activity_list_form.long.data == '' else activity_list_form.long.data
#         delivery_type = None if activity_list_form.delivery_type.data == '' else activity_list_form.delivery_type.data

#         only_tomorrow = activity_list_form.only_tomorrow.data

#         if only_tomorrow:
#             # If only_tomorrow param present in the request, return only tomorrow's activities.
#             tomorrow = (datetime.today() + timedelta(1)).strftime("%Y-%m-%d 00:00:00")
#             is_tommorrow = 1
#         else:
#             tomorrow = None
#             is_tommorrow = 0

#         try:
#             if not branch_codes:
#                 # Getting the branches associated with the user.
#                 delivery_user_branches = delivery_controller_queries.get_delivery_user_branches(user_id)
#             else:
#                 # Branch codes are given.
#                 delivery_user_branches = branch_codes
#             branches = ','.join(delivery_user_branches)
#             # Calculating the distance in KM between the delivery user's lat and long to
#             # the customer address' lat and long.
#             distance_in_km = func.dbo.GetDistance(lat, long, CustomerAddres.Lat,
#                                                   CustomerAddres.Long).label('Distance')
#             try:
#                 # @activitytype='ALL'
#                 # pending_pickups_query = f"EXEC CustomerApp.[dbo].[PendingMobileAppActivity] @Status_type= 'PENDING',@Activitytype=''"

#                 pending_pickups_query = f"EXEC CustomerApp.[dbo].[PendingMobileAppActivity] @DeliveryUsername= '{user_id}',@Branch='{branches}',@SortingMethod='{sorting_method}',@Status_type='PENDING',@Activitytype='',@IsTommorrow='{is_tommorrow}'"

#                 log_data = {
#                     'activity_list_form  :': activity_list_form.data
#                 }
#                 info_logger(f'Route: {request.path}').info(json.dumps(log_data))

#                 pending_activities = CallSP(pending_pickups_query).execute().fetchall()
#                 db.session.commit()
#             except Exception as e:
#                 print(e)

#             if pending_activities:
#                 # Adding a day to the current date
#                 next_date = (datetime.today() + timedelta(1))
#                 # Formatting the added date
#                 formatted_next_date = next_date.strftime("%Y-%m-%d 00:00:00")
#                 # Getting travel log details from DB
#                 completed_activities = db.session.query(TravelLog.OrderId,
#                                                         TravelLog.RecordCreatedDate.label('ActivityTime'),
#                                                         TravelLog.Activity, TravelLog.Lat, TravelLog.Long).filter(
#                     TravelLog.DUserId == user_id,
#                     TravelLog.RecordCreatedDate.between(get_today(), formatted_next_date)).order_by(
#                     TravelLog.RecordCreatedDate.asc()).all()
#                 logs_details = SerializeSQLAResult(completed_activities).serialize(full_date_fields=['ActivityTime'])

#                 final_data = generate_final_data('DATA_FOUND')
#                 final_data['result'] = pending_activities
#                 final_data['CompletedActivities'] = logs_details
#             else:
#                 final_data = generate_final_data('DATA_NOT_FOUND')

#         except Exception as e:
#             error_logger(f'Route: {request.path}').error(e)

#     else:
#         # Form validation error.
#         final_data = generate_final_data('FORM_ERROR')
#         final_data['errors'] = populate_errors(activity_list_form.errors)
#     return final_data

@delivery_blueprint.route('/get_activity_list', methods=["POST"])
# @authenticate('store_user')
def get_pickup_list_():
    """
        API for getting the pending activities in a branch.
        @return:
        """
    activity_list_form = ActivityListForm()
    if activity_list_form.validate_on_submit():
        user_id = request.headers.get('user-id')
        branch_codes = activity_list_form.branch_codes.data
        sorting_method = activity_list_form.sorting_method.data
        only_tomorrow = activity_list_form.only_tomorrow.data
        pending_activities = None
        today = get_today()
        next_date = (datetime.today() + timedelta(1))
        # Formatting the added date
        formatted_next_date = next_date.strftime("%Y-%m-%d 00:00:00")
        log_data = {
                    'activity_list_form:': activity_list_form.data
                        }
        info_logger(f'Route: {request.path}').info(json.dumps(log_data))
        if only_tomorrow:
            is_tommorrow = 1
          
        else:
            is_tommorrow = 0
        try:
            if not branch_codes:
                branch_codes = []
                query = f"EXEC JFSL.Dbo.SPGetDeliveryUserbranchMappingCustApp @Duserid='{user_id}'"
                delivery_user_branches = CallSP(query).execute().fetchall()
                if isinstance(delivery_user_branches, list):
                    for branch in delivery_user_branches:
                        if isinstance(branch, dict) and 'BranchCode' in branch:
                            branch_codes.append(branch['BranchCode'])
            else:
                # Branch codes are given.
                branch_codes = branch_codes
            branch_codes = ','.join(branch_codes)
            try:
                pending_pickups_query = f"""EXEC JFSL.[dbo].[SPFabPendingMobileAppActivity] @DeliveryUsername= '{user_id}',@Branch='{branch_codes}',@SortingMethod='{sorting_method}',@Status_type='PENDING',@Activitytype='',@IsTommorrow={is_tommorrow}"""

                log_data = {
                'pending_pickups_query qry :': pending_pickups_query,
                
                }
                info_logger(f'Route: {request.path}').info(json.dumps(log_data))
                pending_activities = CallSP(pending_pickups_query).execute().fetchall()
                for pending in pending_activities:
                    pending["ActivityId"] = pending.pop("ActivityID", None)

            except Exception as e:
                print(e)
            CompletedActivities = db.session.execute(
                text(
                    "SELECT DuserLat, DuserLong, BookingID,CompletedDate As ActivityTime FROM JFSL.dbo.FabPickupInfo WHERE CompletedBy = :user_id AND CompletedDate Between :today AND :next_date  ORDER BY CompletedDate DESC"),
                {"user_id": user_id,"today":today,"next_date":next_date}
            ).fetchall()
            if pending_activities:
                final_data = generate_final_data('DATA_FOUND')
                final_data['result'] = pending_activities
                final_data['pickup_instructions'] = ['day_delivery']
                final_data["CompletedActivities"] = SerializeSQLAResult(CompletedActivities).serialize(full_date_fields=['ActivityTime'])
            else:
                final_data = generate_final_data('DATA_NOT_FOUND')
        except Exception as e:
            error_logger(f'Route: {request.path}').error(e)
    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(activity_list_form.errors)
    return final_data


@delivery_blueprint.route('/get_pickup_cancel_reschedule_reasons', methods=["GET"])
@authenticate('delivery_user')
def get_pickup_cancel_reschedule_reasons():
    """
    API for getting the cancel & reschedule reasons from the DB.
    @return: Final result containing the order cancel and reschedule reasons
    """
    reasons = {}
    cancel_reasons = []
    reschedule_reasons = []
    try:
        # Getting the reasons from the DB.
        reasons = delivery_controller_queries.get_pickup_cancel_and_reschedule_reasons()
        cancel_reasons = reasons['cancel_reasons']
        reschedule_reasons = reasons['reschedule_reasons']

    except Exception as e:
        error_logger(f'Route: {request.path}').error(e)

    if len(cancel_reasons) > 0 or len(reschedule_reasons) > 0:
        # Any of the reasons set is must.
        reasons['cancel_reasons'] = SerializeSQLAResult(cancel_reasons).serialize()
        reasons['reschedule_reasons'] = SerializeSQLAResult(reschedule_reasons).serialize()

        final_data = generate_final_data('DATA_FOUND')
        final_data['result'] = reasons
    else:
        final_data = generate_final_data('DATA_NOT_FOUND')
    log_data = {
        'final_data:': final_data
    }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))

    return final_data


# @delivery_blueprint.route('/reschedule_delivery', methods=["POST"])
# # @authenticate('delivery_user')
# def reschedule_delivery():
#     """
#     API for rescheduling a delivery request.
#     """
#     reschedule_form = RescheduleDeliveryForm()
#     log_data = {
#         'reschedule_form:': reschedule_form.data
#     }
#     info_logger(f'Route: {request.path}').info(json.dumps(log_data))
#     is_rescheduled = False
#     if reschedule_form.validate_on_submit():
#         DUserId = request.headers.get('user-id')
#         delivery_request_id = reschedule_form.delivery_request_id.data
#         reschedule_reason_id = reschedule_form.reschedule_reason_id.data
#         rescheduled_date = reschedule_form.rescheduled_date.data
#         # rescheduled_date will be DD-MM-YYYY format. Need to convert into YYYY-MM-DD format.
#         # Here, first convert the string date to date object in expected form. Here, the string date will be
#         # in dd-mm-yyyy form.
#         rescheduled_date_obj = datetime.strptime(rescheduled_date, "%d-%m-%Y")
#         # From the date object, convert the date to YYYY-MM-DD format.
#         formatted_rescheduled_date = rescheduled_date_obj.strftime("%Y-%m-%d %H:%M:%S")
#         time_slot_id = reschedule_form.time_slot_id.data
#         lat = None if reschedule_form.lat.data == '' else reschedule_form.lat.data
#         long = None if reschedule_form.long.data == '' else reschedule_form.long.data
#         error_msg = ''
#         try:

#             # Getting the delivery request table details. No delivery details should be present
#             # for this delivery request.
#             delivery_request_details = db.session.query(DeliveryRequest).outerjoin(Delivery,
#                                                                                    DeliveryRequest.DeliveryRequestId == Delivery.DeliveryRequestId).filter(
#                 DeliveryRequest.DeliveryRequestId == delivery_request_id, DeliveryRequest.IsDeleted == 0,
#                 Delivery.DeliveryId == None).one_or_none()

#             log_data = {
#                 'DUserId': DUserId
#             }
#             info_logger(f'Route: {request.path}').info(json.dumps(log_data))
#             # Edited by MMM
#             order_details = db.session.query(Order).filter(
#                 Order.OrderId == delivery_request_details.OrderId,
#                 Order.IsDeleted == 0).one_or_none()
#             # Edited by MMM
#             log_data = {
#                 'delivery reschedule': 'test00'
#             }
#             info_logger(f'Route: {request.path}').info(json.dumps(log_data))
#             if delivery_request_details is not None:
#                 # Edited by MMM
#                 base_query = db.session.query(DeliveryReschedule).filter(
#                     DeliveryReschedule.DeliveryRequestId == delivery_request_id,
#                     DeliveryReschedule.IsDeleted == 0)
#                 try:
#                     # If the delivery user is present in the request, check the delivery user's branch code
#                     # Check whether the delivery is already rescheduled or not.
#                     # If the delivery request is already rescheduled, no further reschedules are allowed.
#                     delivery_reschedule = base_query.one_or_none()
#                 except MultipleResultsFound:
#                     delivery_reschedule = base_query.order_by(desc(DeliveryReschedule.RecordCreatedDate)).all()
#                     duplicate_ids = [i.Id for i in delivery_reschedule]
#                     deleted_id_list = duplicate_ids.remove(max(duplicate_ids))
#                     for i in duplicate_ids:
#                         delivery_reschedule = base_query.filter(DeliveryReschedule.Id == i).one_or_none()
#                         delivery_reschedule.IsDeleted = 1
#                         db.session.commit()
#                 # Check whether the delivery is already rescheduled or not.
#                 # If the delivery request is already rescheduled, no further reschedules are allowed.
#                 delivery_reschedule = base_query.one_or_none()
#                 # Edited by MMM
#                 # Check whether the delivery is already rescheduled or not.
#                 # If the delivery request is already rescheduled, no further reschedules are allowed.
#                 # delivery_reschedule = db.session.query(DeliveryReschedule).filter(
#                 #     DeliveryReschedule.DeliveryRequestId == delivery_request_id,
#                 #     DeliveryReschedule.IsDeleted == 0).one_or_none()

#                 if delivery_reschedule is None:

#                     # Check if the given date is a branch holiday or not.
#                     holiday = delivery_controller_queries.check_branch_holiday(rescheduled_date,
#                                                                                delivery_request_details.BranchCode)
#                     if not holiday:
#                         # The given date is not a branch holiday.

#                         # Checking whether the given time slot id is belong to this branch or not.
#                         # pickup_time_slot = db.session.query(PickupTimeSlot.TimeSlotFrom,
#                         #                                     PickupTimeSlot.TimeSlotTo).filter(
#                         #     PickupTimeSlot.PickupTimeSlotId == time_slot_id,
#                         #     PickupTimeSlot.BranchCode == delivery_request_details.BranchCode,
#                         #     or_(PickupTimeSlot.VisibilityFlag == 1,
#                         #         PickupTimeSlot.DefaultFlag == 1)).one_or_none()
#                         # Get timeslots from db
#                         pickup_time_slot = db.session.query(CustomerTimeSlot.TimeSlotFrom,
#                                                             CustomerTimeSlot.TimeSlotTo).filter(
#                             CustomerTimeSlot.TimeSlotId == time_slot_id, CustomerTimeSlot.IsDeleted == 0).one_or_none()

#                         if pickup_time_slot is not None:

#                             # Setting up the new PickupReschedule object.
#                             new_reschedule = DeliveryReschedule(DeliveryRequestId=delivery_request_id,
#                                                                 RescheduleReasonId=reschedule_reason_id,
#                                                                 RescheduledDate=formatted_rescheduled_date,
#                                                                 DeliveryTimeSlotId=delivery_request_details.DeliveryTimeSlotId,
#                                                                 TimeSlotFrom=pickup_time_slot.TimeSlotFrom,
#                                                                 TimeSlotTo=pickup_time_slot.TimeSlotTo,
#                                                                 DUserId=delivery_request_details.DUserId,
#                                                                 CustAddressId=delivery_request_details.CustAddressId,
#                                                                 Lat=lat,
#                                                                 Long=long,
#                                                                 CustomerPreferredTimeSlot=time_slot_id
#                                                                 )
#                             db.session.add(new_reschedule)
#                             db.session.commit()

#                             # Updating the RecordLastUpdatedDate in the delivery request table.
#                             delivery_request_details.RecordLastUpdatedDate = get_current_date()

#                             delivery_request_details.ReschuduleStatus = 1
#                             delivery_request_details.ReschuduleDate = formatted_rescheduled_date
#                             delivery_request_details.ReschuduleBy = DUserId
#                             delivery_request_details.DUserId = delivery_reschedule.DUserId
#                             delivery_request_details.ReschuduleAddressId = delivery_request_details.CustAddressId
#                             delivery_request_details.ReschuduleModifiedDate = get_current_date()
#                             delivery_request_details.ReschuduleTimeSlotId = time_slot_id

#                             # delivery_request_details.ReschuduleTimeSlotFrom = pickup_time_slot.TimeSlotFrom
#                             # delivery_request_details.ReschuduleTimeSlotTo = pickup_time_slot.TimeSlotTo
#                             pickup_time_slot = db.session.query(CustomerTimeSlot.TimeSlotFrom,
#                                                                 CustomerTimeSlot.TimeSlotTo).filter(
#                                 CustomerTimeSlot.TimeSlotId == time_slot_id, CustomerTimeSlot.IsDeleted == 0
#                             ).one_or_none()

#                             if pickup_time_slot is not None:
#                                 delivery_request_details.ReschuduleTimeSlotFrom = pickup_time_slot.TimeSlotFrom
#                                 delivery_request_details.ReschuduleTimeSlotTo = pickup_time_slot.TimeSlotTo
#                             else:
#                                 error_msg = "Invalid Time Slot."

#                             db.session.commit()
#                             # SMS via alert engine.
#                             store_controller_queries.trigger_delivery_reschedule_sms('DELIVERY_RESCHEDULE',
#                                                                                      delivery_request_details.
#                                                                                      CustomerId,
#                                                                                      delivery_request_details.
#                                                                                      DeliveryRequestId,
#                                                                                      order_details.EGRN,
#                                                                                      rescheduled_date)

#                             is_rescheduled = True
#                             # sends Whatsapp notification if the subscribed for whatsapp notification
#                             delivery_controller_queries.wtsp_notify_on_delivery_reschedule(
#                                 delivery_request_details.CustomerId, formatted_rescheduled_date, order_details.EGRN)
#                             # Edited by MMM
#                         else:
#                             error_msg = 'This time slot does not belongs to this branch.'
#                     else:
#                         # It is a branch holiday. Reschedule on this day is not allowed.
#                         error_msg = 'This is a branch holiday. Please choose another date.'
#                 else:
#                     # Check if the given date is a branch holiday or not.
#                     holiday = delivery_controller_queries.check_branch_holiday(rescheduled_date,
#                                                                                delivery_request_details.BranchCode)

#                     if not holiday:
#                         # The given date is not a branch holiday. So reschedule can be performed.

#                         # Delivery reschedule is already present. Delete the row and insert again.

#                         # Checking whether the given time slot id is belong to this branch or not.
#                         # Get timeslots from db
#                         pickup_time_slot = db.session.query(CustomerTimeSlot.TimeSlotFrom,
#                                                             CustomerTimeSlot.TimeSlotTo).filter(
#                             CustomerTimeSlot.TimeSlotId == time_slot_id, CustomerTimeSlot.IsDeleted == 0
#                         ).one_or_none()

#                         if pickup_time_slot is not None:
#                             delivery_reschedule.IsDeleted = 1
#                             db.session.commit()

#                             # After making the previous reschedule delete,
#                             # create a new entry in the DeliveryReschedule table.
#                             new_reschedule = DeliveryReschedule(DeliveryRequestId=delivery_request_id,
#                                                                 RescheduleReasonId=reschedule_reason_id,
#                                                                 RescheduledDate=formatted_rescheduled_date,
#                                                                 DeliveryTimeSlotId=delivery_request_details.DeliveryTimeSlotId,
#                                                                 TimeSlotFrom=pickup_time_slot.TimeSlotFrom,
#                                                                 TimeSlotTo=pickup_time_slot.TimeSlotTo,
#                                                                 DUserId=delivery_reschedule.DUserId,
#                                                                 CustAddressId=delivery_reschedule.CustAddressId,
#                                                                 Lat=lat,
#                                                                 Long=long,
#                                                                 CustomerPreferredTimeSlot=time_slot_id
#                                                                 )

#                             db.session.add(new_reschedule)
#                             db.session.commit()

#                             # Updating the RecordLastUpdatedDate in the delivery request table.
#                             delivery_request_details.RecordLastUpdatedDate = get_current_date()

#                             delivery_request_details.ReschuduleStatus = 1
#                             delivery_request_details.ReschuduleDate = formatted_rescheduled_date
#                             delivery_request_details.ReschuduleBy = DUserId
#                             delivery_request_details.DUserId = delivery_reschedule.DUserId
#                             delivery_request_details.ReschuduleAddressId = delivery_reschedule.CustAddressId
#                             delivery_request_details.ReschuduleModifiedDate = get_current_date()
#                             delivery_request_details.ReschuduleTimeSlotId = time_slot_id

#                             pickup_time_slot = db.session.query(CustomerTimeSlot.TimeSlotFrom,
#                                                                 CustomerTimeSlot.TimeSlotTo).filter(
#                                 CustomerTimeSlot.TimeSlotId == time_slot_id, CustomerTimeSlot.IsDeleted == 0
#                             ).one_or_none()

#                             if pickup_time_slot is not None:
#                                 delivery_request_details.ReschuduleTimeSlotFrom = pickup_time_slot.TimeSlotFrom
#                                 delivery_request_details.ReschuduleTimeSlotTo = pickup_time_slot.TimeSlotTo
#                             else:
#                                 error_msg = "Invalid Time Slot."

#                             db.session.commit()
#                             # SMS via alert engine.
#                             store_controller_queries.trigger_delivery_reschedule_sms('DELIVERY_RESCHEDULE',
#                                                                                      delivery_request_details.
#                                                                                      CustomerId,
#                                                                                      delivery_request_details.
#                                                                                      DeliveryRequestId,
#                                                                                      order_details.EGRN,
#                                                                                      rescheduled_date)

#                             is_rescheduled = True
#                             # Edited by MMM
#                             # sends Whatsapp notification if the subscribed for whatsapp notification
#                             delivery_controller_queries.wtsp_notify_on_delivery_reschedule(
#                                 delivery_request_details.CustomerId, formatted_rescheduled_date, order_details.EGRN)
#                         # Edited by MMM

#                         else:
#                             error_msg = 'This time slot does not belongs to this branch.'

#                     else:
#                         # It is a branch holiday. Reschedule on this day is not allowed.
#                         error_msg = 'This is a branch holiday. Please choose another date.'

#         except Exception as e:
#             db.session.rollback()
#             error_logger(f'Route: {request.path}').error(e)

#         if is_rescheduled:
#             final_data = generate_final_data('DATA_UPDATED')
#             customer_details = db.session.query(Customer).filter(
#                 Customer.CustomerId == delivery_request_details.CustomerId).one_or_none()

#             customer_code = customer_details.CustomerCode
#             time_slot = db.session.query(CustomerTimeSlot.TimeSlotFrom,
#                                          CustomerTimeSlot.TimeSlotTo,
#                                          CustomerTimeSlot.TimeSlot).filter(
#                 CustomerTimeSlot.TimeSlotId == time_slot_id,
#                 CustomerTimeSlot.IsDeleted == 0,
#                 CustomerTimeSlot.IsActive == 1).one_or_none()
#             time_slot = time_slot.TimeSlot
#             original_date = datetime.strptime(rescheduled_date, "%d-%m-%Y")
#             formatted_rescheduled_date = original_date.strftime("%Y-%m-%d")
#             query = f"EXEC {SERVER_DB}.dbo.FetchtimeslotForApp @SP_Type='1', @Egrno='{order_details.EGRN}', @Customercode='{customer_code}', " \
#                     f"@Timeslot='{time_slot}',@Datedt='{formatted_rescheduled_date}', @Days=null, @modifiedby='FabExpress'," \
#                     f"@branchcode='{delivery_request_details.BranchCode}'"
#             db.engine.execute(text(query).execution_options(autocommit=True))
#             log_data = {
#                 'delivery reschedule': query
#             }
#             info_logger(f'Route: {request.path}').info(json.dumps(log_data))

#         else:
#             if error_msg:
#                 final_data = generate_final_data('CUSTOM_FAILED', error_msg)
#             else:
#                 final_data = generate_final_data('DATA_UPDATE_FAILED')
#     else:
#         # Form validation error.
#         final_data = generate_final_data('FORM_ERROR')
#         final_data['errors'] = populate_errors(reschedule_form.errors)

#     return final_data

@delivery_blueprint.route('/reschedule_delivery', methods=["POST"])
# @authenticate('delivery_user')
def reschedule_delivery():
    """
    API for rescheduling a delivery request.
    """
    reschedule_form = RescheduleDeliveryForm()
    log_data = {
        'reschedule_form:': reschedule_form.data
    }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))
   
    if reschedule_form.validate_on_submit():
        user_id = request.headers.get('user-id')
        CustomerCode = reschedule_form.CustomerCode.data
        CustomerName = reschedule_form.CustomerName.data
        MobileNo = reschedule_form.MobileNo.data
        TimeSlotId = reschedule_form.TimeSlotId.data
        TimeSlotFrom = reschedule_form.TimeSlotFrom.data
        TimeSlotTo = reschedule_form.TimeSlotTo.data
        RescheduleDate = reschedule_form.RescheduleDate.data
        rescheduled_date_obj = datetime.strptime(RescheduleDate, "%d-%m-%Y")
        current_time = datetime.now().time()
        final_datetime = datetime.combine(rescheduled_date_obj.date(), current_time)
        formatted_rescheduled_date1 = final_datetime.strftime("%Y-%m-%d %H:%M:%S")
        RescheduleReasonId = reschedule_form.RescheduleReasonId.data
        EGRN = reschedule_form.EGRN.data
        BranchCode = reschedule_form.BranchCode.data
        TRNNo = reschedule_form.TRNNo.data
        is_rescheduled = False
        rescheduled_date_obj = datetime.strptime(RescheduleDate, "%d-%m-%Y")
        # From the date object, convert the date to YYYY-MM-DD format.
        formatted_rescheduled_date = rescheduled_date_obj.strftime("%Y-%m-%d %H:%M:%S")
     

        error_msg = ''
        try:
            query = f""" EXEC JFSL.DBo.[SPFabDeliveryRescheduleUpdate] @DuserId = {user_id}, @TRNNo = '{TRNNo}',@TimeSlotId = {TimeSlotId} 
                    ,@TimeSlotFrom = '{TimeSlotFrom}',@TimeSlotTo = '{TimeSlotTo}',@ReschuduleDate = '{formatted_rescheduled_date1}',@RescheduleReasonId = {RescheduleReasonId}"""
            
            log_data = {
            'query:': query
                }
            info_logger(f'Route: {request.path}').info(json.dumps(log_data))
            db.engine.execute(text(query).execution_options(autocommit=True))
            is_rescheduled = True

            # SMS via alert engine.
            store_controller_queries.trigger_delivery_reschedule_sms('DELIVERY_RESCHEDULE',
                                                                    TRNNo,
                                                                     MobileNo,TRNNo,
                                                                     EGRN,
                                                                     RescheduleDate,user_id)


            # Edited by MMM
            # sends Whatsapp notification if the subscribed for whatsapp notification
            delivery_controller_queries.wtsp_notify_on_delivery_reschedule(
                CustomerName, RescheduleDate, MobileNo, CustomerCode,EGRN)

        except Exception as e:
            db.session.rollback()
            error_logger(f'Route: {request.path}').error(e)

        if is_rescheduled:
            final_data = generate_final_data('DATA_UPDATED')

            time_slot =  f"{TimeSlotFrom} TO {TimeSlotTo}"
            query = f"EXEC {SERVER_DB}.dbo.SPFabFetchtimeslotForApp @SP_Type='1', @Egrno='{EGRN}', @Customercode='{CustomerCode}', " \
                    f"@Timeslot='{time_slot}',@Datedt='{formatted_rescheduled_date}', @Days=null, @modifiedby='FabExpress'," \
                    f"@branchcode='{BranchCode}'"
            db.engine.execute(text(query).execution_options(autocommit=True))
            log_data = {
                'delivery reschedule': query
            }
            info_logger(f'Route: {request.path}').info(json.dumps(log_data))
             

        else:
            if error_msg:
                final_data = generate_final_data('CUSTOM_FAILED', error_msg)
            else:
                final_data = generate_final_data('DATA_UPDATE_FAILED')
    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(reschedule_form.errors)
    log_data = {
        'final_data:': final_data
    }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))

    return final_data

@delivery_blueprint.route('/get_pickup_time_slots', methods=["POST"])
# @authenticate('delivery_user')
def get_pickup_time_slots_revamping():
    """
    API for getting the time slots for a particular branch code.
    @return:
    """
    time_slots_form = GetPickupTimeslotsForm()
    if time_slots_form.validate_on_submit():
        branch_code = time_slots_form.branch_code.data
        time_slots = None
        try:
            # Getting the time slots from the SP
            query = f"EXEC JFSL.dbo.SPTimeSlotFabriccareCustApp @Branch_code ='{branch_code}'"
            time_slots= CallSP(query).execute().fetchall()

        except Exception as e:
            error_logger(f'Route: {request.path}').error(e)

        if time_slots:
            final_data = generate_final_data('DATA_FOUND')
            result = {'TimeSlots':time_slots}
            final_data['result'] = result
        else:
            final_data = generate_final_data('DATA_NOT_FOUND')
    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(time_slots_form.errors)

    log_data = {
        'query of time_slots': final_data,
        'branch_code': branch_code
    }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))
    return final_data

@delivery_blueprint.route('/get_garments', methods=["POST"])
# @authenticate('delivery_user')
def get_garments():
    """
    API to get all the garments with their order of preference and icon (if any).
    """
    garments_form = GetGarmentsForm()
    if garments_form.validate_on_submit():

        branch_code = garments_form.branch_code.data
        # branch_code = 'BRN0000313'
        service_tat_id = garments_form.service_tat_id.data
        service_type_id = garments_form.service_type_id.data
        garment_list = []
        try:
            
            
            query = f" EXEC JFSL.dbo.SPFabGarmentsPriceDisplay  @BRANCHCODE ='{branch_code}', @ServiceTatId = '{service_tat_id}', @ServiceTypeId = '{service_type_id}'"
            garment_list = CallSP(query).execute().fetchall()
            log_data = {
                "query":query,
            }
            info_logger(f'Route: {request.path}').info(json.dumps(log_data))
            for garments in garment_list:
                garments['GarmentIcon'] = "NA"

        except Exception as e:
            error_logger(f'Route: {request.path}').error(e)

        if garment_list:
            final_data = generate_final_data('DATA_FOUND')
            # Making garment_list JSON serializable.
            final_data['result'] = garment_list
        else:
            final_data = generate_final_data('DATA_NOT_FOUND')
    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(garments_form.errors)
    log_data = {
                "final_data":final_data,
            }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))
    return final_data

@delivery_blueprint.route('/get_garments_', methods=["POST"])
# @authenticate('delivery_user')
def get_garments_():
    """
    API to get all the garments with their order of preference and icon (if any).
    """
    garments_form = GetGarmentsForm()
    if garments_form.validate_on_submit():
        garment_list = []
        branch_code = garments_form.branch_code.data
        service_tat_id = garments_form.service_tat_id.data
        service_type_id = garments_form.service_type_id.data
        try:
            # 'CASE WHEN' equivalent in SQLAlchemy ORM. Select "NA" (Because the column type is varchar)
            # if the GarmentIcon is NULL, else select the column value.
            select_garment_icon = case([(Garment.GarmentIcon == None, "NA"), ],
                                       else_=Garment.GarmentIcon).label("GarmentIcon")

            # If the GarmentPreference is explicitly given, data will be selected in ascending manner,
            # if not, i.e. GarmentPreference is NULL, select it last.
            order_by_condition_check = case([(Garment.GarmentPreference == None, 999), ],
                                            else_=Garment.GarmentPreference).label("GarmentPreference")

            garment_list = db.session.query(Garment.GarmentId, Garment.GarmentName, GarmentCategory.CategoryName,
                                            GarmentUOM.UOMName, select_garment_icon, Garment.GarmentPreference,
                                            PriceList.Price, PriceList.Id.label('PriceListId')).join(
                GarmentCategory, Garment.CategoryId == GarmentCategory.CategoryId).join(GarmentUOM,
                                                                                        Garment.UOMId == GarmentUOM.UOMId).join(
                PriceList, Garment.GarmentId == PriceList.GarmentId).join(DeliveryDateEstimator,
                                                                          Garment.GarmentId == DeliveryDateEstimator.GarmentId).filter(
                Garment.IsActive == 1, PriceList.IsDeleted == 0, PriceList.IsActive == 1,
                PriceList.ServiceTatId == service_tat_id, DeliveryDateEstimator.Time != 0,
                PriceList.ServiceTypeId == service_type_id, PriceList.BranchCode == branch_code,
                PriceList.Price != 0, DeliveryDateEstimator.IsDeleted == 0,
                DeliveryDateEstimator.ServiceTatId == service_tat_id,
                DeliveryDateEstimator.ServiceTypeId == service_type_id,
                DeliveryDateEstimator.BranchCode == branch_code).order_by(order_by_condition_check).all() 
            
            log_data = {
               
                'service_type_id': service_type_id,
                'service_tat_id': service_tat_id,
                'branch_code': branch_code  
               
            }
            info_logger(f'Route: {request.path}').info(json.dumps(log_data))


        except Exception as e:
            error_logger(f'Route: {request.path}').error(e)

        if len(garment_list) > 0:
            final_data = generate_final_data('DATA_FOUND')
            # Making garment_list JSON serializable.
            final_data['result'] = SerializeSQLAResult(garment_list).serialize()
        else:
            final_data = generate_final_data('DATA_NOT_FOUND')
    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(garments_form.errors)

    return final_data

@delivery_blueprint.route('/get_order_garments', methods=["POST"])
# @authenticate('delivery_user')
def get_order_garments_():
    """
    API to get the garments and its details added to a particular order
    """
    order_garments_form = GetOrderGarmentsForm()
    log_data = {
               
                'order_garments_form': order_garments_form.data
            }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))
    if order_garments_form.validate_on_submit():
        BookingID = order_garments_form.BookingId.data
        # Service tat id is optional. If not service tat id is present, all the garments under
        # that order id is considered.
        ServiceTatId = '' if order_garments_form.ServiceTatId.data == None else order_garments_form.ServiceTatId.data
        order_garments = {}

        garment_details = []
        order_details = None
        try:
            query = f""" EXEC JFSL.Dbo.SPDisplayTempOrderGarmentsCustApp @BookingID = {BookingID} , @ActionType = {1} , @ServiceTatId = '{ServiceTatId}'"""
            print(query)
            overview = CallSP(query).execute().fetchall()
            query = f""" EXEC JFSL.Dbo.SPDisplayTempOrderGarmentsCustApp @BookingID = {BookingID} , @ActionType = {6}  , @ServiceTatId = '{ServiceTatId}'"""
            order_type = CallSP(query).execute().fetchone()

            if ServiceTatId == '':
                OrderGarmentIDs = db.session.execute(
                    text(
                        "SELECT OrderGarmentID FROM JFSL.dbo.FabTempOrderGarments (nolock) WHERE BookingID = :BookingID "),
                    {"BookingID": BookingID}
                ).fetchall()

            else:

                OrderGarmentIDs = db.session.execute(
                    text(
                        "SELECT OrderGarmentID FROM JFSL.dbo.FabTempOrderGarments (nolock) WHERE BookingID = :BookingID AND ServiceTatId = :ServiceTatId"),
                    {"BookingID": BookingID, "ServiceTatId": ServiceTatId}
                ).fetchall()
            OrderGarmentIDs = SerializeSQLAResult(OrderGarmentIDs).serialize()


            garment_details = []  # Ensure this list is defined

            for order in OrderGarmentIDs:
                OrderGarmentID = order.get('OrderGarmentID')

                query = f""" EXEC JFSL.Dbo.SPDisplayTempOrderGarmentsCustApp @BookingID = {BookingID}, @OrderGarmentID = '{OrderGarmentID}', @ActionType = {2} , @ServiceTatId = '{ServiceTatId}'"""
                log = {
                "query": query
                    }
                info_logger(f'Route: {request.path}').info(json.dumps(log))
                garment_info = CallSP(query).execute().fetchall()
               

                for g in garment_info:
                    garment_data = {
                        "GarmentName": g["GarmentName"],
                        "OrderGarmentId": g["OrderGarmentID"],
                        "OrderId": g["BookingID"],
                        "GarmentId": g["GarmentId"],
                        "ServiceTatId": g["ServiceTatId"],
                        "ServiceTypeId": g["ServiceTypeId"],
                        "UOMName": g["UOMName"],
                        "IsSFT": g["IsSFT"],
                        "Length": g["Length"],
                        "Width": g["Width"],
                        "GarmentPrice": g["GarmentPrice"],
                        "PriceListId": g["PriceListId"],
                        "UOMID":g["UOMID"]
                    }

                    # Fetch instructions
                    query = f""" EXEC JFSL.Dbo.SPDisplayTempOrderGarmentsCustApp @BookingID = {BookingID}, @OrderGarmentID = '{OrderGarmentID}', @ActionType = {3} , @ServiceTatId = '{ServiceTatId}'"""
                    instructions = CallSP(query).execute().fetchall()
                    print("instructions", instructions)
                    garment_data["Instructions"] = [
                        {
                            "InstructionID": i["InstructionID"],
                            "OrderGarmentId": i["OrderGarmentID"],
                            "Instruction": i["Instruction"],
                            "Description": i["Description"],
                            "InstructionIcon": i["InstructionIcon"],
                            "DarningGarmentLength": i["DarningGarmentLength"],
                            
                        }
                        for i in instructions if i
                    ]

                    # Fetch issues
                    query = f""" EXEC JFSL.Dbo.SPDisplayTempOrderGarmentsCustApp @BookingID = {BookingID}, @OrderGarmentID = '{OrderGarmentID}', @ActionType = {4} , @ServiceTatId = '{ServiceTatId}'"""
                    issues = CallSP(query).execute().fetchall()
                    print("query", query)
                    garment_data["Issues"] = [
                        {
                            "IssueID": i["IssueID"],
                            "OrderGarmentId": i["OrderGarmentID"],
                            "IssueName": i["IssueName"],
                            "IssueDescription": i["IssueDescription"],
                            "IssueIcon": i["IssueIcon"],
                            "DarningGarmentLength": i["DarningGarmentLength"],
                          
                        }
                        for i in issues if i
                    ]

                    # Fetch photos
                    query = f""" EXEC JFSL.Dbo.SPDisplayTempOrderGarmentsCustApp @BookingID = {BookingID}, @OrderGarmentID = '{OrderGarmentID}', @ActionType = {5} , @ServiceTatId = '{ServiceTatId}'"""
                    photos = CallSP(query).execute().fetchall()
                    print("query", query)
                    garment_data["Photos"] = [
                        {
                            "OrderPhotoId": p["OrderPhotoId"],
                            "OrderGarmentId": p["OrderGarmentID"],
                            "GarmentImage": p["GarmentImage"],
                            "RecordCreatedDate": p["RecordCreatedDate"]
                        }
                        for p in photos if p
                    ]

                    garment_details.append(garment_data)

        except Exception as e:
            print(f"Error: {e}")

        if len(overview) > 0 and len(garment_details) > 0:
            final_data = generate_final_data('DATA_FOUND')
            order_garments['overview'] = overview

            order_garments['garment_details'] = garment_details
            # Adding the order type in the result.
            order_garments['order_type'] = order_type.get('order_type')
            final_data['result'] = order_garments
        else:
             final_data = generate_final_data('DATA_NOT_FOUND')
    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(order_garments_form.errors)
    log_data = {
               
                'final_data': final_data
            }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))
    return final_data

# @delivery_blueprint.route('/get_order_garments', methods=["POST"])
#  # @authenticate('delivery_user')
# def get_order_garments_n():
#     """
#     API to get the garments and their details added to a particular order.
#     """
#     order_garments_form = GetOrderGarmentsForm()

#     # Validate form data
#     if order_garments_form.validate_on_submit():
#         BookingID = order_garments_form.BookingId.data
#         ServiceTatId = order_garments_form.ServiceTatId.data or ''  # Default to empty string if None

#         try:
#             # Using parameterized query for security
#             query = f"""EXEC JFSL_UAT.Dbo.SPFabDisplayTempOrderGarmentsJson @BookingID = {BookingID}, @ServiceTatId = {ServiceTatId}"""
#             print(query)
#             garment_details = CallSP(query).execute().fetchall()


#             if garment_details and len(garment_details) > 0:
#                 garment_details_data = garment_details[0].get('result') if isinstance(garment_details[0],
#                                                                                       dict) else None
#                 overview = garment_details[0].get('overview') if isinstance(garment_details[0],
#                                                                                       dict) else None

#                 if garment_details_data:
#                     # Convert stringified JSON into actual JSON for garment_details

#                     garment_list = safe_json_loads(garment_details_data) or []
#                     overview = safe_json_loads(overview) or []
#                     print(overview)

#                     overview_list = []
#                     garment_detail_list = []


#                     for item in garment_list:
#                         # Decode 'garment_details' if it's a stringified JSON
#                         garment_details_raw = item.get('garment_details', "[]")

#                         garment_details = safe_json_loads(garment_details_raw) or []  # Decode garment details
#                         overview_list.extend(overview)
#                         garment_detail_list.extend(garment_details)

#                     final_data = generate_final_data('DATA_FOUND')
#                     final_data['result'] = {
#                         "overview": overview,
#                         "garment_details": garment_detail_list,
#                         "order_type": garment_list[0].get('order_type', None)
#                     }
#                 else:
#                     final_data = generate_final_data('DATA_NOT_FOUND')
#             else:
#                 final_data = generate_final_data('DATA_NOT_FOUND')

#         except Exception as e:
#             error_logger(f'Route: {request.path}').error(str(e))
#             final_data = generate_final_data('ERROR')
#             final_data['message'] = str(e)
#     else:
#         # Form validation error
#         final_data = generate_final_data('FORM_ERROR')
#         final_data['errors'] = populate_errors(order_garments_form.errors)

#     return final_data



@delivery_blueprint.route('/add_order_garments_', methods=["POST"])
# @authenticate('delivery_user')
def add_order_garments_():
    """
    API to add garments to a particular order.
    """
    add_order_garments_form = AddOrderGarmentsForm()
    if add_order_garments_form.validate_on_submit():
        BookingID = add_order_garments_form.BookingId.data
        Garments = add_order_garments_form.Garments.data
        service_tat_id = add_order_garments_form.service_tat_id.data
        service_type_id = add_order_garments_form.service_type_id.data
        log_data = {
                "add_order_garments": add_order_garments_form.data
        }
        info_logger(f'Route: {request.path}').info(json.dumps(log_data))
        is_added = False

        try:
            for garment in Garments:
                garment['BookingID'] = BookingID
                garment['service_tat_id'] = service_tat_id
                garment['service_type_id'] = service_type_id
                garment['OrderGarmentID'] = uuid.uuid4()
                garment['OrderInstructionIDs'] = None
                garment['OrderIssueIDs'] = None
              
                
                db.session.execute(text("""
                               INSERT INTO JFSL.Dbo.FabTempOrderGarments ( OrderGarmentID,  BookingID, OrderTypeId, GarmentCount,   ServiceTatId,   ServiceTypeId,  GarmentId, GarmentName,  Price,  PriceListId, UOMID,UOMName, CRMComplaintId, OrderInstructionIDs, OrderIssueIDs,  IsChanged) 
                               VALUES (:OrderGarmentID,:BookingID, :OrderTypeId, :GarmentCount,  :service_tat_id, :service_type_id,:garment_id, :GarmentName, :price, :price_list_id, :UOMID,:UOMNAME,:CRMComplaintId,:OrderInstructionIDs, :OrderIssueIDs, :isChanged)

                           """), garment)

            db.session.commit()
            is_added = True
        except Exception as e:
            error_logger(f'Route: {request.path}').error(e)
        if is_added:
            final_data = generate_final_data('DATA_SAVED')
        else:
            final_data = generate_final_data('DATA_SAVE_FAILED')

    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(add_order_garments_form.errors)
    log_data = {
        "final_data": final_data
    }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))
    return final_data

@delivery_blueprint.route('/add_order_garments', methods=["POST"])
# @authenticate('delivery_user')
def add_order_garments():
    """
    API to add garments to a particular order.
    """
    add_order_garments_form = AddOrderGarmentsForm()
    if add_order_garments_form.validate_on_submit():
        BookingID = add_order_garments_form.BookingId.data
        Garments = add_order_garments_form.Garments.data
        service_tat_id = add_order_garments_form.service_tat_id.data
        service_type_id = add_order_garments_form.service_type_id.data
        log_data = {
                "add_order_garments": add_order_garments_form.data
        }
        info_logger(f'Route: {request.path}').info(json.dumps(log_data))
        is_added = False

        try:
            json_data = json.dumps({
                "BookingId": BookingID,
                "Garments": Garments,
                "service_tat_id": service_tat_id,
                "service_type_id": service_type_id
            })
            query = f"""EXEC JFSL.DBO.SPFabTempOrderGarmentsInsert @json = '{json_data}'"""
            log_data = {
                "query": query
                }
            info_logger(f'Route: {request.path}').info(json.dumps(log_data))
            db.engine.execute(text(query).execution_options(autocommit=True))
            is_added = True
        except Exception as e:
            error_logger(f'Route: {request.path}').error(e)
        if is_added:
            final_data = generate_final_data('DATA_SAVED')
        else:
            final_data = generate_final_data('DATA_SAVE_FAILED')

    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(add_order_garments_form.errors)
    log_data = {
        "final_data": final_data
    }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))
    return final_data


# @delivery_blueprint.route('/remove_order_garment', methods=["DELETE"])
# @authenticate('delivery_user')
# def remove_order_garment():
#     """
#     API for removing a particular order garment.
#     """
#     remove_garment_form = RemoveOrderGarmentForm()
#     if remove_garment_form.validate_on_submit():
#         order_garment_id = remove_garment_form.order_garment_id.data
#         garment_to_remove = None
#         is_garment_removed = False
#         is_garment_photos_removed = False
#         try:
#             # Getting the garment details from the DB.
#             garment_to_remove = db.session.query(OrderGarment).filter(
#                 OrderGarment.OrderGarmentId == order_garment_id, OrderGarment.IsDeleted == 0).one()
#         except Exception as e:
#             error_logger(f'Route: {request.path}').error(e)

#         if garment_to_remove is not None:
#             # A garment data is found. Update the IsDeleted to 1.
#             try:
#                 garment_to_remove.IsDeleted = 1
#                 garment_to_remove.RecordLastUpdatedDate = get_current_date()
#                 db.session.commit()
#                 is_garment_removed = True

#                 # Recalculating the BasicAmount and ServiceTaxAmount in the Orders table.
#                 try:
#                     order_details = db.session.query(OrderGarment.OrderId).join(Order,
#                                                                                 OrderGarment.OrderId == Order.OrderId).filter(
#                         OrderGarment.OrderGarmentId == order_garment_id, Order.IsDeleted == 0).one()

#                     order_id = order_details.OrderId
#                     delivery_controller_queries.update_basic_amount(order_id)
#                 except Exception as e:
#                     error_logger(f'Route: {request.path}').error(e)
#             except Exception as e:
#                 db.session.rollback()
#                 error_logger(f'Route: {request.path}').error(e)

#         if is_garment_removed:
#             final_data = generate_final_data('DATA_DELETED')
#         else:
#             final_data = generate_final_data('DATA_DELETE_FAILED')

#     else:
#         # Form validation error.
#         final_data = generate_final_data('FORM_ERROR')
#         final_data['errors'] = populate_errors(remove_garment_form.errors)
#     return final_data

@delivery_blueprint.route('/remove_order_garment', methods=["POST"])
# @authenticate('delivery_user')
def remove_order_garment():
    """
    API for removing a particular order garment.
    """
    remove_garment_form = RemoveOrderGarmentForm()
    log_data = {
        "remove_garment_form": remove_garment_form.data
    }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))
    if remove_garment_form.validate_on_submit():
        OrderGarmentID = remove_garment_form.OrderGarmentID.data
        Removed = False
        print(remove_garment_form.data)
        try:
            query = f""" EXEC JFSL.Dbo.[SPDeleteTempOrderGarmentsCustApp]  @OrderGarmentID = '{OrderGarmentID}'"""
            
            db.engine.execute(text(query).execution_options(autocommit=True))
            Removed = True

        except Exception as e:
            error_logger(f'Route: {request.path}').error(e)
        if Removed :
            final_data = generate_final_data('DATA_DELETED')
        else:
            final_data = generate_final_data('DATA_DELETE_FAILED')
    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(remove_garment_form.errors)
    return final_data


@delivery_blueprint.route('/save_order_garment_instruction', methods=["POST"])
# @authenticate('delivery_user')
def save_order_garment_instruction():
    """
    API for saving an instruction (value added service) for a order garment.
    If the instruction is already there, remove the instruction by updating the instruction.w
    If the instruction is new, then save the instruction.
    """
    garment_instruction_form = SaveOrderGarmentInstructionForm()
    if garment_instruction_form.validate_on_submit():

        is_saved = False
        action_performed = ''
        instructions = []
        BookingID = garment_instruction_form.BookingID.data
        OrderGarmentID = garment_instruction_form.order_garment_id.data
        InstructionID = garment_instruction_form.instruction_id.data
        Remove = False
        Add = False
        try:
            ExistingInstructIon = db.session.execute(
                text(
                    "SELECT OrderInstructionIDs FROM JFSL.dbo.FabTempOrderGarments WHERE OrderGarmentID = :order_garment_id"
                ),
                {"order_garment_id": OrderGarmentID},
            )
            ExistingInstructIon = SerializeSQLAResult(ExistingInstructIon).serialize()
         

            if ExistingInstructIon:
                ExistingInstructIon = ExistingInstructIon[0]

                if ExistingInstructIon.get("OrderInstructionIDs"):
                    instructions = list(
                        map(str, ExistingInstructIon["OrderInstructionIDs"].split(",")))
                else:
                    instructions = []

                if str(InstructionID) in instructions:
                    instructions.remove(str(InstructionID))
            
                    Remove = True
                else:
                    instructions.append(str(InstructionID))
                    Add = True

            else:
                instructions = [str(InstructionID)]
                Add = True

            print(instructions)

            instructions = ",".join(instructions)
            print(instructions)

            db.session.execute(
                text(
                    "UPDATE JFSL.dbo.FabTempOrderGarments SET OrderInstructionIDs = :instructions WHERE OrderGarmentID = :order_garment_id"
                ),
                {"order_garment_id": OrderGarmentID, "instructions": instructions},
            )

            db.session.commit()

            action_performed = "added" if Add else "removed"
            is_saved = True

        except Exception as e:
            error_logger(f"Route: {request.path}").error(e)

        if is_saved :
            final_data = generate_final_data('CUSTOM_SUCCESS',
                                                 f'Instruction {action_performed} on this order garment.')
        else:
            final_data = generate_final_data('DATA_SAVE_FAILED', 'Failed to save the instruction.')

    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(garment_instruction_form.errors)

    return final_data


@delivery_blueprint.route('/save_order_garment_issue', methods=["POST"])
# @authenticate('delivery_user')
def save_order_garment_issue_():
    """
    API for saving an issue (QC Issues) for a order garment.
    If the issue is already there, remove the issue by updating the issue.
    If the issue is new, then save the issue.
    """
    garment_issue_form = SaveOrderGarmentIssueForm()
    action_performed = ''
    if garment_issue_form.validate_on_submit():
        OrderGarmentID = garment_issue_form.order_garment_id.data
        IssueID = garment_issue_form.issue_id.data
        BookingID = garment_issue_form.BookingID.data
        is_saved = False
        Remove = False
        Add = False
        try:

            ExistingIssues = db.session.execute(
                text(
                    "SELECT OrderIssueIDs FROM  JFSL.dbo.FabTempOrderGarments WHERE OrderGarmentID = :order_garment_id"
                ),
                {"order_garment_id": OrderGarmentID},
            )

            ExistingIssues = SerializeSQLAResult(ExistingIssues).serialize()
            print(ExistingIssues)

            if ExistingIssues:
                ExistingIssues = ExistingIssues[0]

                if ExistingIssues.get("OrderIssueIDs"):
                    issues = list(
                        map(str, ExistingIssues["OrderIssueIDs"].split(",")))
                else:
                    issues = []

                if str(IssueID) in issues:
                    issues.remove(str(IssueID))

                    Remove = True

                else:
                    issues.append(str(IssueID))
                    Add = True

            else:
                issues = [str(IssueID)]
                Add = True

            print(issues)
            issues = ",".join(issues)
            print(issues)
            db.session.execute(
                text(
                    "UPDATE JFSL.dbo.FabTempOrderGarments SET OrderIssueIDs = :issues WHERE OrderGarmentID = :order_garment_id"),
                {"order_garment_id": OrderGarmentID,"issues":issues}
            )
            db.session.commit()
            action_performed = "added" if Add else "removed"
            is_saved = True
        except Exception as e:
            db.session.rollback()
            error_logger(f'Route: {request.path}').error(e)

        if is_saved:
            final_data = generate_final_data('CUSTOM_SUCCESS', f'Issue {action_performed} on this order garment.')
        else:
            final_data = generate_final_data('DATA_SAVE_FAILED')

    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(garment_issue_form.errors)

    return final_data


@delivery_blueprint.route('/get_instructions_and_issues', methods=["GET"])
# @authenticate('delivery_user')
def get_instructions_and_issues_():
    """
    API for retrieving garment instructions from GarmentInstructions and issues from GarmentIssues tables.
    """
    garment_instructions = []
    garment_issues = []
    try:
        garment_instructions = db.session.execute(
            text(
                "SELECT InstructionID, Instruction, Description  FROM JFSL.dbo.InstructionsInfo WHERE Category = 4")
        ).fetchall()
        garment_instructions = SerializeSQLAResult(garment_instructions).serialize()
        for row in garment_instructions:
            row["InstructionIcon"] = "NA"

        garment_issues = db.session.execute(
            text(
                "SELECT IssueId, IssueName, IssueDescription, IssueIcon  FROM JFSL.dbo.FabGarmentIssueInfo")
            ).fetchall()
        garment_issues = SerializeSQLAResult(garment_issues).serialize()
        for row in garment_issues:
            row["IssueIcon"] = "NA"

    except Exception as e:
        error_logger(f'Route: {request.path}').error(e)

    if len(garment_instructions) > 0 and len(garment_issues) > 0:
        final_data = generate_final_data('DATA_FOUND')
        instructions_and_issues = {'Instructions': garment_instructions ,
                                   'Issues': garment_issues }
        final_data['result'] = instructions_and_issues
    else:
        final_data = generate_final_data('DATA_NOT_FOUND')

    return final_data

# @delivery_blueprint.route('/get_instructions_and_issues', methods=["GET"])
# # @authenticate('delivery_user')
# def get_instructions_and_issues():
#     """
#     API for retrieving garment instructions from GarmentInstructions and issues from GarmentIssues tables.
#     """
#     garment_instructions = []
#     garment_issues = []
#     try:
#         # If garment icon is NULL, then select "NA".
#         select_garment_icon = case([(GarmentInstruction.InstructionIcon == None, "NA"), ],
#                                    else_=GarmentInstruction.InstructionIcon).label("InstructionIcon")

#         # If instruction icon is NULL, then select "NA".
#         select_issue_icon = case([(GarmentIssue.IssueIcon == None, "NA"), ],
#                                  else_=GarmentIssue.IssueIcon).label("IssueIcon")

#         # Getting the garment instructions from the DB.
#         garment_instructions = db.session.query(GarmentInstruction.InstructionId, GarmentInstruction.InstructionName,
#                                                 GarmentInstruction.InstructionDescription,
#                                                 select_garment_icon).all()
#         # Getting the garment issues from the DB.
#         garment_issues = db.session.query(GarmentIssue.IssueId, GarmentIssue.IssueName, GarmentIssue.IssueDescription,
#                                           select_issue_icon).all()

#     except Exception as e:
#         error_logger(f'Route: {request.path}').error(e)

#     if len(garment_instructions) > 0 and len(garment_issues) > 0:
#         final_data = generate_final_data('DATA_FOUND')
#         instructions_and_issues = {'Instructions': SerializeSQLAResult(garment_instructions).serialize(),
#                                    'Issues': SerializeSQLAResult(garment_issues).serialize()}
#         final_data['result'] = instructions_and_issues
#     else:
#         final_data = generate_final_data('DATA_NOT_FOUND')

#     return final_data


# @delivery_blueprint.route('/add_order_garment_photo', methods=["POST"])
# @authenticate('delivery_user')
# def add_order_garment_photo():
#     """
#     API for adding a photo to the order garment.
#     @return: Result message with the file name of the uploaded image file.
#     """
#     add_photo_form = AddOrderGarmentPhotoForm()
#     order_photo_id = 0
#     order_photo_date = None
#     if add_photo_form.validate_on_submit():
#         # Setting up the uploaded flag. If the image is successfully uploaded this will be set to True.
#         uploaded = False
#         # Setting up the result flag. If the photo data saved into DB is successful, this will be set as True
#         result = False
#         b64_image = add_photo_form.b64_image.data
#         order_id = add_photo_form.order_id.data
#         order_garment_id = add_photo_form.order_garment_id.data
#         photo_date = add_photo_form.photo_date.data
#         photo_type = None if add_photo_form.photo_type.data == '' else add_photo_form.photo_type.data
#         # Default photo type values.
#         is_normal = 1
#         is_qc = 0
#         is_vas = 0
#         if photo_type == 'QC':
#             is_normal = 0
#             is_qc = 1
#         if photo_type == 'VAS':
#             is_normal = 0
#             is_vas = 1

#         # Removing the MIME type description from the string.
#         purified_string = base64.b64decode(b64_image.replace('data:image/png;base64,', ''))

#         # A random value from 0 to 9999.
#         random_val = random.randint(0, 9999)

#         # Setting up the photo file name
#         filename = f'{order_garment_id}_{random_val}'

#         # Root directory of the project.
#         root_dir = os.path.dirname(current_app.instance_path)

#         uploads_folder = f'{root_dir}/uploads/order_garments/{order_id}'

#         # If the folder doesn't exist, create the folder.
#         if not os.path.exists(uploads_folder):
#             os.makedirs(uploads_folder)

#         # Target file link
#         target_file = f'{uploads_folder}/{filename}.jpg'

#         with open(target_file, 'wb') as f:
#             f.write(purified_string)
#             uploaded = True

#         if uploaded:
#             # File successfully saved into the folder. Now save the date into OrderPhotos table.
#             try:
#                 # Edited By Athira
#                 if photo_date:
#                     photo_date_obj = datetime.strptime(photo_date, "%d-%m-%Y")
#                     formatted_photo_date = photo_date_obj.strftime("%Y-%m-%d %H:%M:%S")
#                     new_order_photo = OrderPhoto(OrderId=order_id, OrderGarmentId=order_garment_id,
#                                                  GarmentImage=f'{filename}', IsQC=is_qc, IsVAS=is_vas,
#                                                  IsNormal=is_normal,
#                                                  RecordCreatedDate=formatted_photo_date)
#                 else:
#                     new_order_photo = OrderPhoto(OrderId=order_id, OrderGarmentId=order_garment_id,
#                                                  GarmentImage=f'{filename}', IsQC=is_qc, IsVAS=is_vas,
#                                                  IsNormal=is_normal)

#                 db.session.add(new_order_photo)
#                 db.session.commit()
#                 # The data is inserted into DB.
#                 result = True
#                 order_photo_id = new_order_photo.OrderPhotoId
#                 order_photo_date = new_order_photo.RecordCreatedDate
#             except Exception as e:
#                 db.session.rollback()
#                 error_logger(f'Route: {request.path}').error(e)

#         if result:
#             final_data = generate_final_data('DATA_SAVED')
#             image_uploaded = {'GarmentImage': f'{filename}', 'OrderPhotoId': order_photo_id,
#                               'RecordCreatedDate': order_photo_date}
#             final_data['result'] = image_uploaded
#         else:
#             final_data = generate_final_data('DATA_SAVE_FAILED')

#     else:
#         # Form validation error.
#         final_data = generate_final_data('FORM_ERROR')
#         final_data['errors'] = populate_errors(add_photo_form.errors)

#     return final_data

@delivery_blueprint.route('/add_order_garment_photo', methods=["POST"])
# @authenticate('delivery_user')
def add_order_garment_photo():
    """
    API for adding a photo to the order garment.
    @return: Result message with the file name of the uploaded image file.
    """
    add_photo_form = AddOrderGarmentPhotoForm()
    log_data = {
        'add_photo_form': add_photo_form.data
    }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))
    order_photo_id = 0
    order_photo_date = None
    if add_photo_form.validate_on_submit():
        # Setting up the uploaded flag. If the image is successfully uploaded this will be set to True.
        uploaded = False
        # Setting up the result flag. If the photo data saved into DB is successful, this will be set as True
        result = False
        b64_image = add_photo_form.b64_image.data
        BookingID = add_photo_form.BookingId.data
        order_garment_id = add_photo_form.order_garment_id.data
        photo_date = add_photo_form.photo_date.data
        photo_type = None if add_photo_form.photo_type.data == '' else add_photo_form.photo_type.data
        # Default photo type values.
        is_normal = 1
        is_qc = 0
        is_vas = 0
        if photo_type == 'QC':
            is_normal = 0
            is_qc = 1
        if photo_type == 'VAS':
            is_normal = 0
            is_vas = 1

        # Removing the MIME type description from the string.
        purified_string = base64.b64decode(b64_image.replace('data:image/png;base64,', ''))

        # A random value from 0 to 9999.
        random_val = random.randint(0, 9999)

        # Setting up the photo file name
        filename = f'{order_garment_id}_{random_val}'

        # Root directory of the project.
        root_dir = os.path.dirname(current_app.instance_path)

        uploads_folder = f'{root_dir}/uploads/order_garments/{order_garment_id}'

        # If the folder doesn't exist, create the folder.
        if not os.path.exists(uploads_folder):
            os.makedirs(uploads_folder)

        # Target file link
        target_file = f'{uploads_folder}/{filename}.jpg'

        with open(target_file, 'wb') as f:
            f.write(purified_string)
            uploaded = True

        if uploaded:
            # File successfully saved into the folder. Now save the date into OrderPhotos table.
            try:
                if photo_date:
                    #photo_date_obj = datetime.strptime(photo_date, "%d-%m-%Y")
                    photo_date_obj = datetime.strptime(photo_date, "%Y-%m-%d - %H:%M")
                    formatted_photo_date = photo_date_obj.strftime("%Y-%m-%d %H:%M:%S")
                else:
                    formatted_photo_date = get_current_date()

                new_order_photo = db.session.execute(text("""
                        INSERT INTO JFSL.Dbo.fabOrderPhotos 
                            (BookingID, OrderGarmentId, GarmentImage, IsQC, IsVAS, IsNormal, IsDeleted, RecordCreatedDate, RecordLastUpdatedDate) 
                        OUTPUT INSERTED.OrderPhotoId, INSERTED.RecordCreatedDate
                        VALUES (:BookingID, :order_garment_id, :filename, :is_qc, :is_vas, :is_normal, 0, :formatted_photo_date, :formatted_photo_date)
                    """), {
                    "BookingID": BookingID,
                    "order_garment_id": order_garment_id,
                    "filename": filename,
                    "is_qc": is_qc,
                    "is_vas": is_vas,
                    "is_normal": is_normal,
                    "formatted_photo_date": formatted_photo_date
                })

                

                row = new_order_photo.fetchone()
                if row:
                    order_photo_id = row[0]
                    order_photo_date = row[1]
                    result = True
                else:
                    result = False
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                error_logger(f'Route: {request.path}').error(e)
        
        if result:
            final_data = generate_final_data('DATA_SAVED')
            image_uploaded = {'GarmentImage': f'{filename}', 'OrderPhotoId': order_photo_id,
                              'RecordCreatedDate': order_photo_date}
            final_data['result'] = image_uploaded
        else:
            final_data = generate_final_data('DATA_SAVE_FAILED')

    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(add_photo_form.errors)

    
    return final_data



# @delivery_blueprint.route('/remove_order_garment_photo', methods=["DELETE"])
# @authenticate('delivery_user')
# def remove_order_garment_photo():
#     """
#     API for deleting an order garment photo.
#     @return:
#     """
#     remove_photo_form = RemoveOrderGarmentPhotoForm()
#     is_removed = False
#     if remove_photo_form.validate_on_submit():
#         photo_id = remove_photo_form.photo_id.data
#         try:
#             # Getting the garment photo details from the DB.
#             photo = db.session.query(OrderPhoto).filter(OrderPhoto.OrderPhotoId == photo_id,
#                                                         OrderPhoto.IsDeleted == 0).one_or_none()
#             if photo is not None:
#                 try:
#                     photo.IsDeleted = 1
#                     photo.RecordLastUpdateDate = get_current_date()
#                     db.session.commit()
#                     is_removed = True
#                 except Exception as e:
#                     error_logger(f'Route: {request.path}').error(e)
#         except Exception as e:
#             error_logger(f'Route: {request.path}').error(e)

#         if is_removed:
#             final_data = generate_final_data('DATA_SAVED')
#         else:
#             final_data = generate_final_data('DATA_SAVE_FAILED')
#     else:
#         # Form validation error.
#         final_data = generate_final_data('FORM_ERROR')
#         final_data['errors'] = populate_errors(remove_photo_form.errors)

#     return final_data

@delivery_blueprint.route('/remove_order_garment_photo', methods=["POST"])
# @authenticate('delivery_user')
def remove_order_garment_photo():
    """
    API for deleting an order garment photo.
    @return:
    """
    remove_photo_form = RemoveOrderGarmentPhotoForm()
    is_removed = False
    if remove_photo_form.validate_on_submit():
        photo_id = remove_photo_form.photo_id.data
        try:
            # Getting the garment photo details from the DB.

            db.session.execute(
                text(
                    "DELETE FROM JFSL.dbo.FabOrderPhotos WHERE OrderPhotoId = :photo_id "
                ),
                {"photo_id": photo_id},
            )
            db.session.commit()
            is_removed = True

        except Exception as e:
            error_logger(f'Route: {request.path}').error(e)

        if is_removed:
            final_data = generate_final_data('DATA_SAVED')
        else:
            final_data = generate_final_data('DATA_SAVE_FAILED')
    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(remove_photo_form.errors)

    return final_data


# @delivery_blueprint.route('/get_order_garment_photo/<photo_file>', methods=["GET"])
# @authenticate('delivery_user')
# def get_order_garment_photo(photo_file):
#     """
#     API for showing a particular order garment photo from the URL param string.
#     @param photo_file: The file name of the order garment photo.
#     @return: Will return the file if it is a valid order garment photo, else failed message will be returned.
#     """
#     root_dir = os.path.dirname(current_app.instance_path)
#     # Loading the data from the DB.
#     image_data = None
#     try:
#         # Getting the image data from the DB.
#         image_data = db.session.query(OrderPhoto.OrderId).filter(OrderPhoto.GarmentImage == photo_file,
#                                                                  OrderPhoto.IsDeleted == 0).one()
#     except Exception as e:
#         error_logger(f'Route: {request.path}').error(e)

#     if image_data is not None:
#         # Here a image data is found. So return the image file.
#         image_data_dict = SerializeSQLAResult(image_data).serialize_one()
#         order_id = image_data_dict['OrderId']
#         target_file = f'{root_dir}/uploads/order_garments/{order_id}/{photo_file}.jpg'
#         return send_file(target_file, mimetype='image/jpg')
#     else:
#         # No file found for that particular image.
#         final_data = generate_final_data('FILE_NOT_FOUND')
#         return final_data

@delivery_blueprint.route('/get_order_garment_photo/<photo_file>', methods=["GET"])
# @authenticate('delivery_user')
def get_order_garment_photo(photo_file):
    """
    API for showing a particular order garment photo from the URL param string.
    @param photo_file: The file name of the order garment photo.
    @return: Will return the file if it is a valid order garment photo, else failed message will be returned.
    """
    root_dir = os.path.dirname(current_app.instance_path)
    # Loading the data from the DB.
    image_data = None
    try:
        
        image_data = db.session.execute(
            text(
                "SELECT OrderGarmentId  FROM JFSL.dbo.FabOrderPhotos (nolock) WHERE GarmentImage = :photo_file "),
            {"photo_file": photo_file}
        ).fetchone()
    except Exception as e:
        error_logger(f'Route: {request.path}').error(e)

    if image_data is not None:
        # Here a image data is found. So return the image file.
        image_data_dict = SerializeSQLAResult(image_data).serialize_one()
        OrderGarmentId = image_data_dict['OrderGarmentId']
        target_file = f'{root_dir}/uploads/order_garments/{OrderGarmentId}/{photo_file}.jpg'
        return send_file(target_file, mimetype='image/jpg')
    else:
        # No file found for that particular image.
        final_data = generate_final_data('FILE_NOT_FOUND')
        return final_data


# @delivery_blueprint.route('/update_order_garment_service_type', methods=["PUT"])
# @authenticate('delivery_user')
# def update_order_garment_service_type():
#     """
#     API for updating the service type of a particular order garment.
#     @return:
#     """
#     service_type_form = UpdateOrderGarmentServiceTypeForm()
#     if service_type_form.validate_on_submit():
#         log_data = {
#         'service_type_form': service_type_form.data,
#             }
#         info_logger(f'Route: {request.path}').info(json.dumps(log_data))
#         order_garment_id = service_type_form.order_garment_id.data
#         service_type_id = service_type_form.service_type_id.data
#         update = False
#         error_msg = None
#         try:
#             # Getting the order garment details
#             order_garment_details = db.session.query(OrderGarment).filter(
#                 OrderGarment.OrderGarmentId == order_garment_id).one()

#             if order_garment_details.ServiceTypeId != service_type_id:
#                 # Updating the order garment details with the given service type id
#                 order_garment_details.ServiceTypeId = service_type_id
#                 db.session.commit()
#                 # If the pickup is rescheduled, then select reschedule's BranchCode, else BranchCode of the pickup
#                 # request.
#                 select_branch_code = case([(PickupReschedule.BranchCode == None, PickupRequest.BranchCode), ],
#                                           else_=PickupReschedule.BranchCode).label("BranchCode")

#                 pickup_details = db.session.query(PickupRequest.PickupRequestId, select_branch_code).outerjoin(
#                     PickupReschedule, PickupReschedule.PickupRequestId == PickupRequest.PickupRequestId).join(Order,
#                                                                                                               PickupRequest.PickupRequestId == Order.PickupRequestId).filter(
#                     Order.OrderId == order_garment_details.OrderId,
#                     or_(PickupReschedule.IsDeleted == 0, PickupReschedule.IsDeleted == None)).one_or_none()

#                 if pickup_details:

#                     # Calculating the garment price.
#                     basic_garment_amount = delivery_controller_queries.get_price_for_garment(
#                         order_garment_details.GarmentId, order_garment_details.ServiceTatId,
#                         service_type_id, pickup_details.BranchCode)

#                     # If failed to get the price, set it to 0.0
#                     if basic_garment_amount is None:
#                         basic_garment_amount = 0.0
#                     else:
#                         basic_garment_amount = float(basic_garment_amount.Price)

#                     # ServiceTax amount of the order garment
#                     service_tax_amount = basic_garment_amount * 18 / 100
#                     order_garment_details.BasicAmount = basic_garment_amount
#                     order_garment_details.ServiceTaxAmount = service_tax_amount

#                     delivery_controller_queries.update_basic_amount(order_garment_details.OrderId)
#                     update = True
#                 else:
#                     error_msg = "Order is cancelled due to inactivity"
#             else:
#                 # Updating the order garment details with the given service type id
#                 order_garment_details.ServiceTypeId = service_type_id
#                 db.session.commit()
#                 update = True

#         except Exception as e:
#             db.session.rollback()

#         if update and error_msg is None:
#             final_data = generate_final_data('DATA_UPDATED')
#         else:
#             if error_msg:
#                 final_data = generate_final_data('CUSTOM_FAILED', error_msg)
#             else:
#                 final_data = generate_final_data('DATA_UPDATE_FAILED')

#     else:
#         # Form validation error.
#         final_data = generate_final_data('FORM_ERROR')
#         final_data['errors'] = populate_errors(service_type_form.errors)
    # log_data = {
    #     'final_data': final_data
    #         }
    #     info_logger(f'Route: {request.path}').info(json.dumps(log_data))
#     return final_data

@delivery_blueprint.route('/update_order_garment_service_type', methods=["PUT"])
@authenticate('delivery_user')
def update_order_garment_service_type():
    """
    API for updating the service type of a particular order garment.
    @return:
    """
    service_type_form = UpdateOrderGarmentServiceTypeForm()
    if service_type_form.validate_on_submit():
        order_garment_id = service_type_form.order_garment_id.data
        service_type_id = service_type_form.service_type_id.data
        update = False
        error_msg = None
        try:
            query = f""" EXEC JFSL.DBO.SPFabTempOrderGarmentsUpdate @OrderGarmentID = '{order_garment_id}' , @ServiceTypeId={service_type_id}"""
            log_data = {
            'query': query
            }
            info_logger(f'Route: {request.path}').info(json.dumps(log_data))
            db.engine.execute(text(query).execution_options(autocommit=True))
            update = True
        except Exception as e:
            db.session.rollback()

        if update and error_msg is None:
            final_data = generate_final_data('DATA_UPDATED')
        else:
            if error_msg:
                final_data = generate_final_data('CUSTOM_FAILED', error_msg)
            else:
                final_data = generate_final_data('DATA_UPDATE_FAILED')

    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(service_type_form.errors)
    return final_data


# @delivery_blueprint.route('/update_hanger_instructions', methods=["PUT"])
# @authenticate('delivery_user')
# def update_hanger_instructions():
#     """
#     API for applying/removing hanger instruction to/from order garments.
#     @return:
#     """
#     hanger_form = UpdateHangerInstructionsForm()
#     if hanger_form.validate_on_submit():
#         order_id = hanger_form.order_id.data
#         garment_id = hanger_form.garment_id.data
#         action = hanger_form.action.data
#         result = False
#         # Getting all the order garment ids belongs to that order.
#         try:
#             order_garment_ids = db.session.query(OrderGarment.OrderGarmentId).filter(OrderGarment.OrderId == order_id,
#                                                                                      OrderGarment.GarmentId == garment_id,
#                                                                                      OrderGarment.IsDeleted == 0).all()

#             # Getting the hanger instruction id from the DB.
#             hanger_instruction_id = delivery_controller_queries.get_hanger_instruction_id()

#             # For each garment ids, insert hanger instruction into the OrderInstructions table.
#             for order_garment_id in order_garment_ids:
#                 # Getting the hanger instruction for that particular order garment.
#                 # If the hanger instruction is already added, then skip it.
#                 # If the order garment has no hanger instruction, then add it.
#                 instruction = delivery_controller_queries.get_hanger_instruction_of_order_garment(order_id,
#                                                                                                   order_garment_id.OrderGarmentId,
#                                                                                                   hanger_instruction_id)

#                 if action == "ADD":
#                     # Here, the hanger instruction need to be applied to all
#                     # order garments.
#                     if instruction is None:
#                         # No hanger instruction is already present.
#                         # So add hanger instruction.
#                         try:
#                             new_instruction = OrderInstruction(OrderId=order_id,
#                                                                OrderGarmentId=order_garment_id.OrderGarmentId,
#                                                                InstructionId=hanger_instruction_id, IsDeleted=0)
#                             db.session.add(new_instruction)
#                             db.session.commit()
#                             result = True
#                         except Exception as e:
#                             db.session.rollback()
#                             error_logger(f'Route: {request.path}').error(e)
#                 elif action == "REMOVE":
#                     # Here, the hanger instruction needs to be removed from
#                     # all the order garments if any.
#                     if instruction is not None:
#                         # Already a hanger instruction exists. So remove it.
#                         try:
#                             instruction.IsDeleted = 1
#                             db.session.commit()
#                             result = True
#                         except Exception as e:
#                             db.session.rollback()
#                 else:
#                     pass

#         except Exception as e:
#             error_logger(f'Route: {request.path}').error(e)

#         if result:
#             # The hanger instruction successfully added/removed.
#             final_data = generate_final_data('DATA_UPDATED')
#         else:
#             # Failed to add/remove the hanger instruction.
#             final_data = generate_final_data('DATA_UPDATE_FAILED')

#     else:
#         # Form validation error.
#         final_data = generate_final_data('FORM_ERROR')
#         final_data['errors'] = populate_errors(hanger_form.errors)

#     return final_data

@delivery_blueprint.route('/update_hanger_instructions', methods=["POST"])
# @authenticate('delivery_user')
def update_hanger_instructions():
    """
    API for applying/removing hanger instruction to/from order garments.
    @return:
    """
    hanger_form = UpdateHangerInstructionsForm()
    if hanger_form.validate_on_submit():
        BookingId = hanger_form.BookingId.data
        garment_id = hanger_form.garment_id.data
        action = hanger_form.action.data

        try:
            order_garment_ids = db.session.execute(
                text(
                    "SELECT OrderGarmentId FROM JFSL.dbo.FabTempOrderGarments (nolock) WHERE BookingID = :BookingID AND GarmentId = :garment_id"),
                {"BookingID": BookingId, "garment_id": garment_id}
            ).fetchall()

            order_garment_ids = [row[0] for row in order_garment_ids]
            print(order_garment_ids)
            hanger_instruction = db.session.execute(
                text("SELECT InstructionID FROM JFSL.dbo.InstructionsInfo (nolock) WHERE Description = :Hanger"),
                {"Hanger": "Hanger"}
            ).scalar()


            hanger_instruction = str(hanger_instruction) 

            for order_garment_id in order_garment_ids:
                instruction = db.session.execute(
                    text(
                        "SELECT OrderInstructionIDs FROM JFSL.dbo.FabTempOrderGarments (nolock) WHERE OrderGarmentId = :order_garment_id AND GarmentId = :garment_id"),
                    {"order_garment_id": order_garment_id, "garment_id": garment_id}
                ).fetchone()

                existing_instruction = instruction[0] if instruction else ""
                print(existing_instruction)
                instructions = existing_instruction.split(",") if existing_instruction else []
                print(hanger_instruction)

                if action == "ADD":
                    if hanger_instruction not in instructions:
                        instructions.append(hanger_instruction)
                else:
                    if hanger_instruction in instructions:
                        instructions.remove(hanger_instruction)

                updated_instructions = ",".join(instructions)
                print(updated_instructions)

                db.session.execute(
                    text(
                        "UPDATE JFSL.dbo.FabTempOrderGarments SET OrderInstructionIDs = :instructions WHERE OrderGarmentID = :order_garment_id AND GarmentId = :garment_id"),
                    {"order_garment_id": order_garment_id, "instructions": updated_instructions,
                     "garment_id": garment_id}
                )

            db.session.commit()
            result = True

        except Exception as e:
            db.session.rollback()
            print(f"Error: {e}")

        except Exception as e:
            error_logger(f'Route: {request.path}').error(e)

        if result:
            # The hanger instruction successfully added/removed.
            final_data = generate_final_data('DATA_UPDATED')
        else:
            # Failed to add/remove the hanger instruction.
            final_data = generate_final_data('DATA_UPDATE_FAILED')

    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(hanger_form.errors)

    return final_data

@delivery_blueprint.route('/finalize_order1', methods=["POST"])
@authenticate('delivery_user')
def finalize_order1():
    """
    API for finalizing the order. EGRN generation will take place. Discount Code calculation will also be taking place.
    @return:
    """

    finalize_form = FinalizeOrderForm()
    log_data = {
        'finalize_form': finalize_form.data,
    }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))
    if finalize_form.validate_on_submit():
        order_id = finalize_form.order_id.data
        given_discount_code = None if finalize_form.discount_code.data == '' else finalize_form.discount_code.data
        given_coupon_code = None if finalize_form.coupon_code.data == '' else finalize_form.coupon_code.data
        remarks = None if finalize_form.remarks.data == '' else finalize_form.remarks.data
        egrn_generated = False
        lat = None if finalize_form.lat.data == '' else finalize_form.lat.data
        long = None if finalize_form.long.data == '' else finalize_form.long.data
        delivery_charge = finalize_form.delivery_charge.data
        user_id = request.headers.get('user-id')
        pickup_request = None
        invalid_discount_code_msg = ''
        error_msg = ""
        in_location = ""
        distance = None
        store_distance = None

        # Logging the data in the request into log file.
        log_data = {
            'order_id': order_id,
            'given_discount_code': given_discount_code,
            'given_coupon_code': given_coupon_code,
            'remarks': remarks,
        }
        info_logger(f'Route: {request.path}').info(json.dumps(log_data))

        # Getting the order details from the DB.
        try:
            # Updating the pickup request status code to Pickup Completed.
            try:
                # Getting the pickup request id from the Orders table.
                pickup_request_id = db.session.query(Order.PickupRequestId).filter(
                    Order.OrderId == order_id, Order.IsDeleted == 0).one_or_none()
                log_data = {
                    'pickup_request_id from order table': pickup_request_id.PickupRequestId,
                }
                info_logger(f'Route: {request.path}').info(json.dumps(log_data))
                # Logging the data in the request into log file.

                if pickup_request_id is not None:

                    # Updating the status code.
                    try:
                        # Getting the pickup request details by giving the pickup request id.
                        pickup_request = db.session.query(PickupRequest).filter(
                            PickupRequest.PickupRequestId == pickup_request_id.PickupRequestId).one_or_none()
                        log_data = {
                            'pickup_request details from PickupRequest table': pickup_request.PickupRequestId,
                        }
                        info_logger(f'Route: {request.path}').info(json.dumps(log_data))
                        if pickup_request is not None and pickup_request.PickupStatusId != 3:
                            # If Pickup is rescheduled, then take the RescheduledDate as PickupDate,
                            # else, return the original PickupDate.
                            select_pickup_date = case(
                                [(PickupReschedule.PickupRequestId == None, PickupRequest.PickupDate), ],
                                else_=PickupReschedule.RescheduledDate).label("PickupDate")
                            if pickup_request.DiscountCode is not None:
                                given_discount_code = pickup_request.DiscountCode

                            # Getting the pickup date from the pickup request.
                            pickup_date_details = db.session.query(select_pickup_date).outerjoin(PickupReschedule,
                                                                                                 PickupReschedule.PickupRequestId == PickupRequest.PickupRequestId).filter(
                                PickupRequest.PickupRequestId == pickup_request.PickupRequestId,
                                PickupRequest.IsCancelled == 0,
                                or_(PickupReschedule.IsDeleted == 0, PickupReschedule.IsDeleted == None)).one_or_none()

                            if pickup_request.PickupSource == 'Adhoc' and pickup_date_details.PickupDate.strftime(
                                    "%Y-%m-%d 00:00:00") <= get_today() and pickup_request.BookingId == None:
                                # If this is a adhoc pickup and if it is scheduled for today, generate Booking Id.
                                # Generating the BookingId in realtime.
                                query = f"EXEC {LOCAL_DB}.dbo.[USP_INSERT_ADHOC_PICKUP_FROM_MOBILEAPP_TO_FABRICARE] @PickUprequestId={pickup_request.PickupRequestId}"
                                db.engine.execute(text(query).execution_options(autocommit=True))

                                log_data = {
                                    'INSERT_ADHOC_PICKUP_FROM_MOBILEAPP_TO_FABRICARE': query
                                }
                                info_logger(f'Route: {request.path}').info(json.dumps(log_data))
                        else:
                            error_msg = "Pickup already completed"

                    except Exception as e:
                        db.session.rollback()
                        error_logger(f'Route: {request.path}').error(e)
            except Exception as e:
                error_logger(f'Route: {request.path}').error(e)

            order_details = db.session.query(Order).filter(Order.OrderId == order_id, Order.EGRN == None,
                                                           Order.IsDeleted == 0).one_or_none()

            order_details.DeliveryCharge = delivery_charge
            order_details.DeliveryChargeFlag = delivery_charge
            db.session.commit()
        
            branch_active_or_not = db.session.query(Branch.IsActive).filter(
                Branch.BranchCode == order_details.BranchCode,
                Branch.IsDeleted == 0, Branch.IsActive == 1).one_or_none()
            if branch_active_or_not is not None:

                customer_id = order_details.CustomerId

                customer_details = db.session.query(Customer).filter(
                    Customer.CustomerId == order_details.CustomerId).one_or_none()

                # If the customer has no CustomerCode, then EGRN generation can't be made.
                # Getting the CustomerCode from the customers table.
                if customer_details is not None:
                    customer_code = customer_details.CustomerCode
                else:
                    customer_code = None

                if customer_code is None or customer_code == '':
                    # No customer code found.
                    # Execute a SP to generate Customer code in realtime.
                    query = f"EXEC {LOCAL_DB}..USP_Adhoc_PickUp_Customer_Registration @MobileNo='{customer_details.MobileNo}', @userId={customer_id}"
                    result = CallSP(query).execute().fetchone()
                    new_customer_code = None
                    if result:
                        if result['Result'] == "Success":
                            # Here, the customer code is successfully generated
                            new_customer_code = result["CustomerCode"]
                            customer_details.CustomerCode = new_customer_code
                            try:
                                # Newly created customer code need to be saved in the DB.
                                db.session.commit()
                            except Exception as e:
                                db.session.rollback()
                                error_logger(f'Route: {request.path}').error(e)
                    # Newly generated customer code.
                    customer_code = new_customer_code

                # Getting the BookingId. If BookingId is not generated, finalizing
                # the pickup can not be performed.
                booking_id = db.session.query(PickupRequest.BookingId).filter(
                    PickupRequest.PickupRequestId == pickup_request.PickupRequestId).one_or_none()
                log_data = {
                    'booking_id from PickupRequest table': booking_id.BookingId,
                    'order_details from orders table': order_details.OrderId,
                }
                info_logger(f'Route: {request.path}').info(json.dumps(log_data))
                if booking_id.BookingId is not None:
                    if order_details is not None and pickup_request is not None:
                        if order_details.EGRN == None:
                            # Valid order details found.
                            # Saving the order remarks.
                            order_details.Remarks = remarks
                            # Saving the lat and long values.
                            order_details.Lat = lat
                            order_details.Long = long
                            db.session.commit()

                            branch_code = order_details.BranchCode
                            already_applied_discount_code = order_details.DiscountCode
                            already_applied_coupon_code = order_details.CouponCode

                            if already_applied_discount_code:
                                # Already a discount code is present in the Orders table.
                                discount_code = already_applied_discount_code
                            else:
                                # No discount code is present from the orders table. So take the discount code from the request.
                                discount_code = given_discount_code

                            if already_applied_coupon_code:
                                # Already a coupon code is present in the Orders table.
                                coupon_code = already_applied_coupon_code
                            else:
                                coupon_code = given_coupon_code

                            # Updating the EstDeliveryDate of the Orders table.
                            delivery_controller_queries.set_max_est_delivery_date(order_id)

                            if customer_code:
                                # Generating an EGRN for the order if a valid customer code is present.
                                query = f"EXEC {SERVER_DB}.dbo.App_OrderCreation_Detail @branchcode='{branch_code}',@orderid={order_id}"
                                egrn = CallSP(query).execute().fetchone()
                                log_data = {
                                    'egrn from SP': egrn,
                                    'query for generating egrn': query,
                                }
                                info_logger(f'Route: {request.path}').info(json.dumps(log_data))
                                if egrn:
                                    egrn = egrn['EGRN']
                                    # to complete delivery only if there is no egrn generated
                                    # else:
                                    #     egrn_generated = True
                                    # to complete delivery only if there is no egrn generated

                                    # Updating the order with the EGRN.
                                    try:

                                        pickup_request_id = db.session.query(Order.PickupRequestId).filter(
                                            Order.OrderId == order_id, Order.IsDeleted == 0).scalar()

                                        # Logging the data in the request into log file.

                                        customer_address_id = db.session.query(PickupRequest.CustAddressId).filter(
                                            PickupRequest.PickupRequestId == pickup_request_id).scalar()
                                        customer_location = db.session.query(CustomerAddres.Lat,
                                                                             CustomerAddres.Long).filter(
                                            CustomerAddres.CustAddressId == customer_address_id).one_or_none()

                                        delivery_user_loaction = (lat, long)
                                        distance = hs.haversine(customer_location, delivery_user_loaction)
                                        if distance is not None:
                                            if distance >= 1:
                                                km_part = int(distance)  # Integer part in kilometers
                                                meters_part = (distance - km_part) * 1000  # Convert fractional kilometers to meters
                                                distance_display = f"{km_part} km {int(meters_part)} m"
                                            else:
                                                # If the distance is less than 1 km, convert it to meters
                                                distance_meters = distance * 1000
                                                distance_display = f"{int(distance_meters)} m"
                                            if distance <= 0.1:
                                                in_location = "YES"
                                            else:
                                                in_location = "NO"

                                        branchcode = db.session.query(PickupRequest.BranchCode).filter(
                                            PickupRequest.PickupRequestId == pickup_request_id).scalar()

                                        branch_location = db.session.query(Branch.Lat, Branch.Long).filter(
                                            Branch.BranchCode == branchcode).one_or_none()

                                        if branch_location:
                                            store_distance = hs.haversine(branch_location, delivery_user_loaction)
                                            if store_distance >= 1:
                                                km_part = int(store_distance)  # Integer part in kilometers
                                                meters_part = (store_distance - km_part) * 1000  # Convert fractional kilometers to meters
                                                distance_dis = f"{km_part} km {int(meters_part)} m"
                                            else:
                                                # If the distance is less than 1 km, convert it to meters
                                                distance_meters = store_distance * 1000
                                                distance_dis = f"{int(distance_meters)} m"

                                        # Saving the order with the newly generated EGRN.
                                        order_details.EGRN = egrn
                                        pickup_request.RecordLastUpdatedDate = get_current_date()
                                        # 3 is the status for Pickup Completed.
                                        pickup_request.PickupStatusId = 3
                                        pickup_request.CompletedDate = get_current_date()
                                        pickup_request.CompletedBy = user_id
                                        pickup_request.IsReopen = 0
                                        pickup_request.inlocation = in_location
                                        pickup_request.distance = distance_display
                                        pickup_request.store_distance = distance_dis

                                        db.session.commit()
                                        egrn_generated = True
                                        log_data = {
                                            'pickup status': 3,
                                            'egrn_generated': True,
                                        }
                                        info_logger(f'Route: {request.path}').info(json.dumps(log_data))
                                    except Exception as e:
                                        db.session.rollback()
                                        error_logger(f'Route: {request.path}').error(e)

                                    if egrn_generated:
                                        # Checking if the DiscountCode is applied or not.
                                        if discount_code is not None:
                                            # Here, a discount code is applied. Calculations can be done here.

                                            # First, validate with the EasyRewardz to check whether the discount code is an
                                            # ER coupon code or not.
                                            er_validation = er_module.validate_er_coupon(customer_code, branch_code,
                                                                                         discount_code)

                                            is_er_coupon = 0
                                            code_from_er = None
                                            er_request_id = None
                                            log_data = {
                                                'er_validation ': er_validation,
                                            }
                                            info_logger(f'Route: {request.path}').info(json.dumps(log_data))
                                            if er_validation['status']:
                                                # Here, the discount_code is the code from ER.
                                                code_from_er = discount_code
                                                # The original POS discount code is the discount_code coming from the ER response.
                                                discount_code = er_validation['discount_code']
                                                is_er_coupon = 1
                                                er_request_id = er_validation['er_request_id']
                                            elif pickup_request.IsERCoupon == 1:
                                                # Here, the discount_code is the code from ER saved in pickup request table.
                                                code_from_er = pickup_request.CodeFromER
                                                # The original POS discount code is the discount_code coming from the ER response saved in pickup request table.
                                                discount_code = pickup_request.DiscountCode
                                                is_er_coupon = 1
                                                er_request_id = pickup_request.ERRequestId

                                            validation = common_module.validate_discount_code(discount_code, 'order',
                                                                                              egrn,
                                                                                              customer_code,
                                                                                              branch_code, is_er_coupon)
                                            if validation:
                                                # if validation['ISVALID'] == 1:
                                                try:
                                                    # Updating the Orders table with the Discount value.
                                                    order_details.DiscountCode = discount_code
                                                    order_details.Discount = validation['DISCOUNTAMOUNT']
                                                    order_details.CodeFromER = code_from_er
                                                    order_details.IsERCoupon = is_er_coupon
                                                    order_details.ERRequestId = er_request_id
                                                    db.session.commit()

                                                except Exception as e:
                                                    error_logger(f'Route: {request.path}').error(e)

                                                # Recalculating the service tax amount.
                                                delivery_controller_queries.recalculate_service_tax(order_id)

                                                # Updating the discount value in order garments table.
                                                delivery_controller_queries.divide_discount_to_garments(order_id,
                                                                                                        validation[
                                                                                                            'DISCOUNTAMOUNT'])

                                                if is_er_coupon == 1:
                                                    # Notifying the POS that a ER coupon has been applied.
                                                    delivery_controller_queries.notify_pos_about_er_coupon(egrn,
                                                                                                           discount_code,
                                                                                                           er_request_id,
                                                                                                           code_from_er)
                                                else:
                                                    # Notifying the POS that a discount has been applied.
                                                    delivery_controller_queries.notify_pos_about_discount(egrn,
                                                                                                          discount_code)

                                                # else:
                                                #     invalid_discount_code_msg = 'Discount criteria does not match, edit ' \
                                                #                                 'or apply a new code from fabricare. '

                                        if coupon_code is not None:
                                            # Coupon code is applied. Now validate the coupon code.
                                            validation = common_module.validate_coupon_code(coupon_code, customer_code,
                                                                                            branch_code,
                                                                                            'order', egrn)

                                            if validation:
                                                if validation['message'] == "Valid Promocode":
                                                    # Coupon code is valid.
                                                    # Saving the coupon code into the DB.
                                                    try:
                                                        order_details.CouponCode = coupon_code
                                                        db.session.commit()

                                                        delivery_controller_queries.notify_pos_about_coupon(egrn,
                                                                                                            coupon_code)

                                                    except Exception as e:
                                                        error_logger(f'Route: {request.path}').error(e)
                        else:
                            # EGRN is already generated.
                            egrn_generated = True
                if egrn_generated:
                    if delivery_charge:
                        delivery_charge = 1
                    else:
                        delivery_charge = 0
                    delivery_charge_applied = (
                        f"EXEC {SERVER_DB}.dbo.ComputeDeliveryChargeforFabexpress @EGRN='{egrn}',"
                        f"@ENABLEORDISABLE={1}")
                    db.engine.execute(text(delivery_charge_applied).execution_options(autocommit=True))
                    log_data = {
                        'delivery_charge_applied': delivery_charge_applied
                    }
                    info_logger(f'Route: {request.path}').info(json.dumps(log_data))
                    update_customer_outstanding = f"EXEC {SERVER_DB}.dbo.UpdateCustomer_Outstanding_Unsettled_Data " \
                                                  f"@customercode ='{customer_code}'"
                    db.engine.execute(text(update_customer_outstanding).execution_options(autocommit=True))
                    # If the GPS co-ordinates are provided, save the GPS position into the TravelLogs table.
                    if lat is not None and long is not None:
                        delivery_controller_queries.save_travel_log('Pickup', user_id, order_id, None, lat, long)

                pickup_request_id = db.session.query(Order.PickupRequestId).filter(
                    Order.OrderId == order_id).one_or_none()
                order_ids = db.session.query(Order.OrderId, Order.ReOpenStatus).filter(
                    Order.PickupRequestId == pickup_request_id.PickupRequestId
                ).all()
                order_ids = SerializeSQLAResult(order_ids).serialize()

                for order in order_ids:
                    if order['OrderId'] == order_id:
                        pass
                    else:
                        reopen_status = db.session.query(Order).filter(
                            Order.OrderId == order['OrderId']).one_or_none()
                        reopen_status.ReOpenStatus = 1
                        db.session.commit()
            else:
                error_msg = "You cannot create an order branch as the is “Inactivated”"
        except Exception as e:
            error_logger(f'Route: {request.path}').error(e)

        if egrn_generated and error_msg == "":
            final_data = generate_final_data('DATA_SAVED')
            if invalid_discount_code_msg != '':
                final_data['message'] = invalid_discount_code_msg
        else:
            final_data = generate_final_data('CUSTOM_FAILED', error_msg)

    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(finalize_form.errors)

    return final_data

@delivery_blueprint.route('/finalize_order', methods=["POST"])
# @authenticate('delivery_user')
def finalize_order():
    """
    API for finalizing the order. EGRN generation will take place. Discount Code calculation will also be taking place.
    @return:
    """
    finalize_form = FinalizeOrderForm()

    if finalize_form.validate_on_submit():
        DiscountCode = '' if finalize_form.DiscountCode.data in ('', 'NA') else finalize_form.DiscountCode.data
        CouponCode = '' if finalize_form.CouponCode.data in ('', 'NA') else finalize_form.CouponCode.data
       
       
        Remarks = '' if finalize_form.remarks.data == '' else clean_address_field(finalize_form.remarks.data)
        DuserLat = 0.0 if finalize_form.Duserlat.data == '' else finalize_form.Duserlat.data
        DuserLong = 0.0 if finalize_form.Duserlong.data == '' else finalize_form.Duserlong.data
        DeliveryCharge = finalize_form.delivery_charge.data
        ServiceTaxAmount = finalize_form.ServiceTaxAmount.data
        EstimatedAmount = finalize_form.EstimatedAmount.data
        DUserId = request.headers.get('user-id')
        PickupID = finalize_form.PickupId.data
        IsExistOrderID = finalize_form.IsExistOrderID.data
        BookingID = finalize_form.BookingId.data
        BranchCode = finalize_form.BranchCode.data
        CustomerCode = finalize_form.CustomerCode.data
        BasicAmount = 0.0 if finalize_form.BasicAmount.data == '' else finalize_form.BasicAmount.data
        Garments = finalize_form.Garments.data
        CustAddressId = finalize_form.CustAddressId.data
        PickupDate = finalize_form.PickupDate.data
        GarmentCount = finalize_form.GarmentCount.data
        OrderTypeId  = finalize_form.OrderTypeId.data
        CustLat = finalize_form.CustLat.data
        CustLong = finalize_form.CustLong.data
        IsERCoupon = finalize_form.IsERCoupon.data
        ERRequestId = finalize_form.ERRequestId.data
        CodeFromER = finalize_form.CodeFromER.data
        AddressType = finalize_form.AddressType.data
        DuserDistance = 0.0
        StoreDistance = 0.0
        trigger_mail = False
        result = None
        BranchName = None
        EGRN = None
     
    
        DiscountAmount = 0.0
        ValidCouponCode = None
        Success = False
        log_data = {
                "finalize_form":finalize_form.data,
                
                    }
        info_logger(f'Route: {request.path}').info(json.dumps(log_data))

        print(finalize_form.data)
        try:
            DuserLocation = (DuserLat, DuserLong)
            CustLocation = (CustLat, CustLong)
            Distance = hs.haversine(DuserLocation, CustLocation)
            if Distance is not None:
                if Distance >= 1:
                    if Distance >= 10:
                        trigger_mail = True
                    km_part = int(Distance)  # Integer part in kilometers
                    meters_part = (Distance - km_part) * 1000  # Convert fractional kilometers to meters
                    DuserDistance = f"{km_part} km {int(meters_part)} m"
                else:
                    # If the distance is less than 1 km, convert it to meters
                    distance_meters = Distance * 1000
                    DuserDistance = f"{int(distance_meters)} m"

            BranchLocation = db.session.execute(
                text(
                    "SELECT Lat, Long,BranchName FROM JFSL.dbo.Branchinfo WHERE BranchCode = :BranchCode"),
                {"BranchCode": BranchCode}
            ).fetchone()
            BranchName = BranchLocation.BranchName

            if BranchLocation is not None:
                BranchLocation = (
                    float(BranchLocation.Lat), float(BranchLocation.Long))

                store_distance = hs.haversine(BranchLocation, DuserLocation)
                if store_distance >= 1:
                    if store_distance >= 10:
                        trigger_mail = True
                    km_part = int(store_distance)  # Integer part in kilometers
                    meters_part = (store_distance - km_part) * 1000  # Convert fractional kilometers to meters
                    StoreDistance = f"{km_part} km {int(meters_part)} m"
                else:
                    # If the distance is less than 1 km, convert it to meters
                    distance_meters = store_distance * 1000
                    StoreDistance = f"{int(distance_meters)} m"
        except Exception as e:
            error_logger(f'Route: {request.path}').error(e)
        try:

            query = f"""
                        EXEC JFSL.Dbo.SPOrderGarmentsInsertCustApp
                            @PickupID = '{PickupID}',
                          
                            @DUserID = {DUserId},
                            @BookingID = {BookingID},
                            @BranchCode = '{BranchCode}',
                            @CustomerCode = '{CustomerCode}',
                            @GarmentsCount = {GarmentCount},
                            @BasicAmount = {BasicAmount},
                            @Remarks = '{Remarks}',
                            @DuserDistance = '{DuserDistance}',
                            @AssignedStoreUser = {'NULL'},
                            @StoreDistance = '{StoreDistance}',
                            @Distance = '{DuserDistance}',
                            @DuserLat = '{DuserLat}',
                            @DuserLong = '{DuserLong}',
                            @ServiceTaxAmount = {ServiceTaxAmount},
                            @EstimatedAmount = {EstimatedAmount},
                            @OrderType = {OrderTypeId},
                            @AddressType = '{AddressType}'

                    """
            log_data = {
                        'query': query
                    }
            info_logger(f'Route: {request.path}').info(json.dumps(log_data))

            db.engine.execute(text(query).execution_options(autocommit=True))

            print("query")
            EGRN = db.session.execute(
                text(
                    "SELECT EGRNNO  FROM JFSL.dbo.OrderInfo (nolock) WHERE PickupID = :PickupID"),
                {"PickupID": PickupID}
            ).fetchone()
            EGRN = EGRN[0]
            print(EGRN)
            if EGRN:
                Success = True
                if len(CouponCode) > 0 or  len(DiscountCode) > 0 :
                    query = f""" EXEC JFSL.Dbo.SPFabERCoupanCodeValidation @ActualDiscCode ='{DiscountCode}'"""
                    result = CallSP(query).execute().fetchone()
                    if result.get('Message') == 'Success':
                        CodeFromER = DiscountCode
                        IsERCoupon = 1
                        ERRequestId = 1
                        
                    else:
                        CodeFromER = ''
                        IsERCoupon = 0
                        ERRequestId = 0
                    query = f"""  EXEC JFSL.Dbo.SPFabOrderGarmentsDiscountUpdate @EGRN = '{EGRN}',@Branchcode = '{BranchCode}',@CUSTOMERCODE = '{CustomerCode}',@PROMOCODE = '{DiscountCode}'
                                ,@GarmentsCount = '{GarmentCount}',@CouponCode = '{CouponCode}',@CodeFromER = '{CodeFromER}',@IsERCoupon = {IsERCoupon}, @ERRequestId={ERRequestId}"""

                    log_data = {
                        'query': query
                    }
                    info_logger(f'Route: {request.path}').info(json.dumps(log_data))
                    db.engine.execute(text(query).execution_options(autocommit=True))
        except Exception as e:
            error_logger(f'Route: {request.path}').error(e)
        try:
            if Success and trigger_mail:
                if trigger_mail:
                    customer_name = db.session.execute(
                        text(
                            "SELECT FirstName FROM JFSL.dbo.CustomerInfo WHERE CustomerCode = :CustomerCode"),
                        {"CustomerCode": CustomerCode}
                    ).fetchone()
                    delivery_user_name = db.session.query(DeliveryUser.UserName).filter(
                        DeliveryUser.DUserId == DUserId, DeliveryUser.IsActive == 1,
                        DeliveryUser.IsDeleted == 0).scalar()
                    current_day = get_current_date()
                    workbook = openpyxl.Workbook()
                    worksheet = workbook.active
                    field_name_mapping = {
                        BranchCode: "Branch Code",
                        BranchName: "Branch Name",
                        "Pickup": "Activity Type",
                        current_day: "Completed Date",
                        BookingID: "Booking Id",
                        customer_name: "Customer Name",
                        delivery_user_name: "Delivery User Name",
                        DuserDistance: "P-up/Del Location to Customer Distance",
                        StoreDistance: "P-up/Del Location to Store Distance"
                    }
                    # Columns to include
                    column_names = [BranchCode, BranchName, "Pickup", current_day,
                                    BookingID, customer_name, delivery_user_name, DuserDistance,
                                    StoreDistance]

                    # Headers for the Excel file
                    headers = [field_name_mapping.get(col, col) for col in column_names]
                    worksheet.append(headers)

                    # data_row = [branchcode, current_day, booking_id,customer_id,customer_name,delivery_user_name,distance_display,distance_dis,egrn]
                    data_row = [str(BranchCode), str(BranchName), "Pickup", str(current_day),
                                str(BookingID),
                                str(customer_name), str(delivery_user_name), str(DuserDistance),
                                str(StoreDistance)]
                    worksheet.append(data_row)

                    row_index = 2
                    col_index = 2

                    # Save the file
                    file_name = "report.xlsx"
                    file_path = 'C:\\jfsl_cloud\\dev\\fabexpress_distance_report\\report.xlsx'
                    workbook.save(file_path)

                    # query = f"EXEC JFSL.[dbo].[SendCommanEmailFabXpress] @FilePath='{file_name}', @EmailTo='jfsl.mdm@jyothy.com', @EmailCC='laji.saju@mapmymarketing.com', @Subject='Pickup/Delivery Distance more than 10 KM', @Body='Please find the attached report'"

                    # log_data = {
                    #     'query': query
                    # }
                    # info_logger(f'Route: {request.path}').info(json.dumps(log_data))
                    # # result = CallSP(query).execute().fetchall()
                    # db.engine.execute(text(query).execution_options(autocommit=True))

        except Exception as e:
            error_logger(f'Route: {request.path}').error(e)
        
        if EGRN:
            query = f"EXEC JFSL.dbo.[SPOrderBookingSMSCustApp] @egrnno ='{EGRN}'"
            log_data = {
                'query': query,
            }
            info_logger(f'Route: {request.path}').info(json.dumps(log_data))
            db.engine.execute(text(query).execution_options(autocommit=True))

            final_data = generate_final_data('DATA_SAVED')
            try:
                db.session.execute(text("""
                                            INSERT INTO JFSL.Dbo.FABTravelLogs 
                                            (Activity,  DUserId,    BookingID,  TRNNo,  Lat,    Long,   IsDeleted,  RecordCreatedDate,  RecordLastUpdatedDate) 
            
                                            VALUES (:Activity,  :DUserId,   :BookingID, :TRNNo, :Lat,   :Long,  :IsDeleted, :RecordCreatedDate, :RecordCreatedDate)
                                            """), {
                        "Activity": "Pickup",
                        "DUserId": DUserId,
                        "BookingID": BookingID,
                        "TRNNo": '',
                        "Lat": DuserLat,
                        "Long": DuserLong,
                        "Remarks": Remarks,
                        "IsDeleted": 0,
                        "RecordCreatedDate": get_current_date()
                    })
                db.session.commit()
            except Exception as e:
                error_logger(f'Route: {request.path}').error(e)
            
        else:
            custom_message = "Failed to Create Order Please Contact MDM"
            final_data = generate_final_data('CUSTOM_FAILED',custom_message)

    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(finalize_form.errors)
    log_data = {
        'final_data': final_data,
    }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))

    return final_data



@delivery_blueprint.route('/get_order_review_reasons', methods=["GET"])
# @authenticate('delivery_user')
def get_order_review_reasons_():
    """
    API for getting the predefined order review reasons from the DB.
    @return:
    """
    review_reasons = []
    try:

        review_reasons = db.session.execute(
            text(
                "SELECT OrderReviewReasonId, ReviewReason FROM JFSL.dbo.FabOrderReviewReasons Where IsDeleted = 0")

        ).fetchall()
        print(review_reasons)
    except Exception as e:
        error_logger(f'Route: {request.path}').error(e)

    if review_reasons:
        final_data = generate_final_data('DATA_FOUND')
        final_data['result'] = SerializeSQLAResult(review_reasons).serialize()
    else:
        final_data = generate_final_data('DATA_NOT_FOUND')

    return final_data

@delivery_blueprint.route('/save_order_review', methods=["POST"])
# @authenticate('delivery_user')
def save_order_review():
    """
    API for saving an order review after picking up the garments.
    @return:
    """
    review_form = SaveOrderReviewForm()
    log = {
            "save_order_review": review_form.data
        }
    info_logger(f'Route: {request.path}').info(json.dumps(log))
    if review_form.validate_on_submit():
        BookingID = review_form.BookingID.data
        rating = review_form.rating.data
        review_reason_id = review_form.review_reason_id.data
        # Remarks will be NULL if no remarks are provided in the request.
        remarks = review_form.remarks.data if review_form.remarks.data != '' else None
        user_id = request.headers.get('user-id')
        picked_up = False
        is_already_picked_up = False
        try:
            order_review = db.session.execute(
                text(
                    "SELECT * FROM JFSL.dbo.FabOrderReviews Where BookingID = BookingID"),
                {"BookingID":BookingID}

            ).fetchall()

            if order_review is not None:
             
                db.session.execute(text("""
                        INSERT INTO JFSL.Dbo.FabOrderReviews 
                        (BookingID, OrderReviewReasonId,    StarRating, Remarks,    DUserId,    IsDeleted,  RecordCreatedDate,  RecordLastUpdatedDate) 
                                        
                        VALUES (:BookingID, :OrderReviewReasonId, :StarRating, :Remarks, :DUserId, :IsDeleted, :RecordCreatedDate, :RecordCreatedDate)
                        """), {
                    "BookingID": BookingID,
                    "OrderReviewReasonId": review_reason_id,
                    "StarRating": rating,
                    "Remarks": remarks,
                    "DUserId": user_id,
                    "IsDeleted": 0,
                    "RecordCreatedDate": get_current_date()
                })
                db.session.commit()
                picked_up = True
            
            else:
                is_already_picked_up = True

        except Exception as e:
            db.session.rollback()
            error_logger(f'Route: {request.path}').error(e)

        if picked_up:
            # Review saved and marked this order as picked up.
            final_data = generate_final_data('DATA_SAVED')
        else:
            if is_already_picked_up:
                # Ther order has already been picked up.
                final_data = generate_final_data('CUSTOM_FAILED', 'The order has already been picked up.')
            else:
                # Failed to save the review and mark this one as picked up.
                final_data = generate_final_data('DATA_NOT_SAVED')

    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(review_form.errors)
    log = {
            "final_data": final_data
        }
    info_logger(f'Route: {request.path}').info(json.dumps(log))

    return final_data



@delivery_blueprint.route('/get_pending_delivery_details', methods=["POST"])
# @authenticate('delivery_user')
def get_pending_delivery_details():
    """
    API for getting the details of a order details that need to be delivered. i.e. ready for delivery order.
    @return:
    """
    delivery_details_form = PendingDeliveryDetailsForm()

    if delivery_details_form.validate_on_submit():
        log = {
                "delivery_details_form": delivery_details_form.data
            }
        info_logger(f'Route: {request.path}').info(json.dumps(log))
        TRNNo = delivery_details_form.TRNNo.data
        BranchCode = delivery_details_form.BranchCode.data
        payment_mode = []
        user_id = request.headers.get('user-id')
        delivery_garments_count = 0

        # try:
        query = f""" EXEC JFSL.Dbo.SPPendingDeliveriesDetailedScreen @user_id = {user_id} ,@TRNNo = '{TRNNo}',@PendingDeliveriesScreen = {1}"""
        order_detail = CallSP(query).execute().fetchall()
        for i, row in enumerate(order_detail):
            row_dict = dict(row)
            
            lat = row_dict.get('Lat')
            long = row_dict.get('Long')

            row_dict['Lat'] = lat if lat and lat > 0.0 else None
            row_dict['Long'] = long if long and long > 0.0 else None

            order_detail[i] = row_dict
       
        EGRN = order_detail[0]["EGRN"]
        CustomerCode = order_detail[0]["CustomerCode"]
      
        query = f""" EXEC JFSL.Dbo.SPPendingDeliveriesDetailedScreen @user_id = {user_id} ,@TRNNo = '{TRNNo}',@TRNNoBasisGarmentsCounts = {1}"""
        DeliveryGarmentsCount= CallSP(query).execute().fetchone()


        query = f""" EXEC JFSL.Dbo.SPPendingDeliveriesDetailedScreen @user_id = {user_id} ,@TRNNo = '{TRNNo}', @CRMComplaintCounts = {1}"""
        ComplaintGarmentsCount = CallSP(query).execute().fetchone()

        query = f""" EXEC JFSL.Dbo.SPPendingDeliveriesDetailedScreen @user_id = {user_id} ,@TRNNo = '{TRNNo}' , @DeliveryUserEDCDetails ={1}"""
        UserHasDevice = CallSP(query).execute().fetchall()
      

        query = f""" EXEC JFSL.Dbo.SPPendingDeliveriesDetailedScreen @user_id = {user_id} ,@TRNNo = '{TRNNo}', @NotServedGarmentsCount = {1}"""
        NotServedGarmentsCount = CallSP(query).execute().fetchone()

        query = f"EXEC {SERVER_DB}..GetPaymentMode @branchcode='{BranchCode}'"
        payment_modes = CallSP(query).execute().fetchall()
        query = f"EXEC {SERVER_DB}.dbo.SpTotalGarmentCount @EGRNNO='{EGRN}'"
       
        TotalGarmentsCount = CallSP(query).execute().fetchone()
        


        delivered_status = db.session.execute(
            text(
                "SELECT PaymentStatus  FROM JFSL.dbo.FabDeliveryInfo (nolock) WHERE TRNNo = :TRNNo AND PaymentStatus =:PaymentStatus AND CompletedBy is not NULL"),
            {"TRNNo": TRNNo, "PaymentStatus":"Un-paid"}
        ).fetchone()
        print(delivered_status)
        if TotalGarmentsCount.get('TotalGarmentCounts') == DeliveryGarmentsCount.get('GarmentsCount'):
            delivery_status = "Full Delivery"
        else:
            delivery_status = "Partial Delivery"

        for payment in payment_modes:
            payment_mode.append(payment['PaymentMode'])
        payment_mode.append("PaytmEDC")
        # for payment in payment_modes:
            # # mode = payment['PaymentMode'].replace(" ", "") 
            # payment_mode.append(payment)
        if order_detail is not None:
            final_data = generate_final_data('DATA_FOUND')
            order_detail = order_detail[0]
            order_detail['OrderId'] = 0
            # order_detail['TotalGarmentsCount'] = TotalGarmentsCount.get('TotalGarmentCounts')
            order_detail['TotalGarmentsCount'] = DeliveryGarmentsCount.get('GarmentsCount')
            order_detail['DeliveryGarmentsCount'] = DeliveryGarmentsCount.get('GarmentsCount')
            order_detail['NotServedGarmentsCount'] = NotServedGarmentsCount.get('GarmentsCount')
            order_detail['DeliveryStatus'] = delivery_status
            order_detail['ComplaintGarmentsCount'] = ComplaintGarmentsCount.get('CRMComplaintCounts')
            order_detail['garmetsDelivered'] = DeliveryGarmentsCount.get('GarmentsCount')
            if TotalGarmentsCount.get('TotalGarmentCounts') == NotServedGarmentsCount.get('GarmentsCount'):
                order_detail['GarmentsType'] = 'Not served'
            else:
                order_detail['GarmentsType'] = 'served'

            payable_amount = 0
            pre_applied_coupons = []
            pre_applied_lp = {}

            payment_status = payment_module.get_garments_payment_status(EGRN, TRNNo)
            #
            amount = delivery_controller_queries.get_payable_amount_via_sp_trn(CustomerCode, EGRN, TRNNo)

            reasons = db.session.execute(
                text(
                    "SELECT ReasonValue  FROM JFSL.dbo.FAbReasonTemplates (nolock) WHERE IsDeleted = 0"),

            ).fetchall()
            query = f""" JFSL.Dbo.SPFabDeliveryPaymentStatus @EGRNNO = '{EGRN}',@TRNNo = '{TRNNo}'"""
            PaymentStatus = CallSP(query).execute().fetchone()

            if amount:
                if amount.get('IsPreAppliedCoupon') in [1, True]:
                    egrn = EGRN
                    result = payment_module.get_available_coupon_codes(egrn)
                    print(result)
                    discount_amount = result[0]['DISCOUNTAMOUNT'] if result and isinstance(result, list) and 'DISCOUNTAMOUNT' in result[0] else 0
                    order_detail['PreAppliedCoupons'] = result

                    # Ensure no negative payable amount
                    payable_amount = amount['PAYABLEAMOUNT'] - discount_amount
                    order_detail['PayableAmount'] = payable_amount if payable_amount > 0 else 0

                    order_detail['DeliveryCharge'] = amount['DELIVERYCHARGE']
                else:
                    order_detail['PayableAmount'] = amount['PAYABLEAMOUNT']
                    order_detail['DeliveryCharge'] = amount['DELIVERYCHARGE']
                    order_detail['PreAppliedCoupons'] = []
            else:
                order_detail['PayableAmount'] = 0
                order_detail['DeliveryCharge'] = 0.0
                order_detail['PreAppliedCoupons'] = []


            AlterNumber = db.session.execute(text(
                    """SELECT MobileNumber, IsAlterNumber FROM OTPS WHERE TRNNo = :TRNNo"""
                ), {"TRNNo": TRNNo}).fetchone()

            if AlterNumber:
                order_detail['IsAlterNumber'] = AlterNumber['IsAlterNumber']
                order_detail['MobileNumber'] = AlterNumber['MobileNumber']
            else:
                order_detail['IsAlterNumber'] = None
                order_detail['MobileNumber'] = None
            if order_detail.get('MonthlyCustomer') is True:

                order_detail['PayableAmount'] = payment_status['FinalAmount']

           
            order_detail['PaymentStatus'] = PaymentStatus.get('PaymentStatus')

            # coupon_code = order_detail.get('CouponCode')
            # order_detail['PreAppliedCoupons'] = [] if coupon_code is None or coupon_code == 'NA' else [coupon_code]


            order_detail['PreAppliedLP'] = pre_applied_lp

        
            order_detail['IsMonthlyCustomerDelivery'] = False if order_detail.get(
                'MonthlyCustomer') is None else order_detail.get('MonthlyCustomer')
            order_detail['UserHasDevice'] = True if get_paytm_credentials(user_id) else False
            # log = {
            #     "get_paytm_credentials": get_paytm_credentials
            # }
            # info_logger(f'Route: {request.path}').info(json.dumps(log))

            order_detail['PaymentMode'] = payment_mode
            order_detail['Reasons'] = [reason[0] for reason in reasons]
            order_detail['skip_otp'] = "Are you sure to deliver the garments without OTP?"

            order_detail['skip_payment1'] = "You are delivering the garment(s)"
            order_detail['skip_payment2'] = "without collecting the amount."
            order_detail['skip_payment3'] = "Do you want to continue?"
            order_detail['skip_complaint'] = "Do you wish to raise the complaints?"

            final_data['result'] = order_detail
        else:
            final_data = generate_final_data('DATA_NOT_FOUND')

    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(delivery_details_form.errors)
    log = {
                "final_data": final_data
            }
    info_logger(f'Route: {request.path}').info(json.dumps(log))
    return final_data

# @delivery_blueprint.route('/get_delivery_garments', methods=["POST"])
# # @authenticate('delivery_user')
# def get_delivery_garments():
#     """
#     API for getting the garments for the delivery.
#     @return:
#     """
#     delivery_garments_form = GetDeliveryGarmentsForm()
#     if delivery_garments_form.validate_on_submit():
#         order_id = delivery_garments_form.order_id.data
#         delivery_request_id = delivery_garments_form.delivery_request_id.data
#         delivery_garments = []
#         order_details = None
#         try:
            # log = {
            #     "time": 'time1'
            # }
            # info_logger(f'Route: {request.path}').info(json.dumps(log))
#             order_details = db.session.query(Order).filter(Order.OrderId == order_id,
#                                                            Order.IsDeleted == 0).one_or_none()
#             # If TagId is NOT present in the OrderGarments table, return "NA", else return the value.
#             select_tag_id = case([(OrderGarment.TagId == None, "NA"), ],
#                                  else_=OrderGarment.TagId).label("TagId")

#             # If JFSLTicketId is NOT present in the Complaints table, return "NA", else return the value.
#             select_jfsl_ticket_id = case([(Complaint.JFSLTicketId == None, "NA"), ],
#                                          else_=Complaint.JFSLTicketId).label("JFSLTicketId")

#             # If CRMComplaintStatus is NOT present in the Complaints table, return "NA", else return the value.
#             select_crm_complaint_status = case([(Complaint.CRMComplaintStatus == None, "NA"), ],
#                                                else_=Complaint.CRMComplaintStatus).label("CRMComplaintStatus")

#             # Selecting CRM Complaint Id.
#             select_complaint_id = case([(OrderGarment.CRMComplaintId == None, 0), ],
#                                        else_=OrderGarment.CRMComplaintId).label("CRMComplaintId")

#             # Selecting the string values for the QCStatus.
#             select_qc_status = case([
#                 (cast(QCInfo.Status, String).label('QCStatus') == None, "NA"),
#                 (cast(QCInfo.Status, String).label('QCStatus') == 1, "Not Served"),
#                 (cast(QCInfo.Status, String).label('QCStatus') == 2, "Approved"),
#                 (cast(QCInfo.Status, String).label('QCStatus') == 3, "QCPending"),
#             ],
#                 else_=cast(QCInfo.Status, String)).label("QCStatus")

#             # Selecting the latest QCInfo row from the QCInfo table.
#             latest_qc_id = db.session.query(QCInfo.QCID).filter(
#                 QCInfo.POSOrderGarmentID == OrderGarment.POSOrderGarmentId).order_by(
#                 QCInfo.PostedDateTime.desc()).limit(
#                 1).correlate(OrderGarment).as_scalar()

#             # Selecting the TagId in the Complaints table in related to the TagId of the
#             # OrderGarments table.
#             select_tag_id_from_complaints = db.session.query(Complaint.TagId).filter(
#                 Complaint.TagId == OrderGarment.TagId).order_by(Complaint.RecordCreatedDate.desc()).limit(
#                 1).correlate(OrderGarment).as_scalar()

#             # Getting DeliveryRequest details from DB
#             delivery_details = db.session.query(DeliveryRequest.IsPartial).filter(
#                 DeliveryRequest.DeliveryRequestId == delivery_request_id).one_or_none()

#             # Getting the delivery garments count from DB
#             delivery_garments_count = db.session.query(func.count(DeliveryGarment.DeliveryGarmentId)).filter(
#                 DeliveryGarment.DeliveryRequestId == delivery_request_id, DeliveryGarment.IsDeleted == 0).scalar()

#             # Base query for checking the delivery is partial
#             base_query = db.session.query(OrderGarment.OrderGarmentId, Garment.GarmentName, select_tag_id,
#                                           ServiceTat.ServiceTatName, ServiceType.ServiceTypeName, select_qc_status,
#                                           select_complaint_id, select_jfsl_ticket_id, select_crm_complaint_status,
#                                           literal(0).label('Complaint'), literal(0).label('RewashCount')).join(Garment,
#                                                                                                                OrderGarment.GarmentId == Garment.GarmentId).join(
#                 Order, OrderGarment.OrderId == Order.OrderId).join(ServiceTat,
#                                                                    OrderGarment.ServiceTatId == ServiceTat.ServiceTatId).join(
#                 ServiceType, OrderGarment.ServiceTypeId == ServiceType.ServiceTypeId).outerjoin(QCInfo,
#                                                                                                 QCInfo.QCID == latest_qc_id).outerjoin(
#                 Complaint, Complaint.TagId == select_tag_id_from_complaints).filter(OrderGarment.OrderId == order_id,
#                                                                                     OrderGarment.GarmentStatusId == 10,
#                                                                                     OrderGarment.IsDeleted == 0)

#             # If partial delivery take garments for delivery in DeliveryGarment table and garments count should be have
#             if delivery_details.IsPartial and delivery_garments_count != 0:

#                 # Get OrderGarmentId from DeliveryGarment table
#                 order_garment_ids = db.session.query(DeliveryGarment.OrderGarmentId).filter(
#                     DeliveryGarment.DeliveryRequestId == delivery_request_id).all()

#                 # Populating a list of OrderGarmentId's
#                 order_garment_id_list = [ordergarmentid.OrderGarmentId for ordergarmentid in order_garment_ids]

#                 # Getting the garments for the delivery.
#                 delivery_garments = base_query.filter(OrderGarment.OrderGarmentId.in_(order_garment_id_list)).all()
#             else:
#                 # Getting the garments for the delivery.
#                 delivery_garments = base_query.all()

#             delivery_garments = SerializeSQLAResult(delivery_garments).serialize()

#             order_details = db.session.query(Order.OrderId, Order.EGRN, Order.OrderTypeId).filter(
#                 Order.OrderId == order_id, Order.IsDeleted == 0).one_or_none()
#             log = {
#                 "time": 'time2'
#             }
#             info_logger(f'Route: {request.path}').info(json.dumps(log))

#             complaint_history = []
#             if order_details is not None:
#                 query = f"EXEC {LOCAL_DB}.[dbo].[USP_GET_REWASH_or_CRM_COMPLAINT_COUNT_BASED_ON_EGRN] '{order_details.EGRN}'"
#                 complaint_history = CallSP(query).execute().fetchall()
#                 log = {
#                     "complaint_history": query
#                 }
#                 info_logger(f'Route: {request.path}').info(json.dumps(log))

#             for complaint in complaint_history:
#                 result = {'Complaint': False, 'RewashCount': 0}
#                 # Complaint history found.
#                 for delivery_garment in delivery_garments:
#                     if complaint['TAGNO'] == delivery_garment['TagId']:
#                         # A match found.
#                         delivery_garment['Complaint'] = 1
#                         delivery_garment['RewashCount'] = result['RewashCount']
#                         break

#         except Exception as e:
#             error_logger(f'Route: {request.path}').error(e)

#         if len(delivery_garments) > 0:
#             # Garments found.
#             final_data = generate_final_data('DATA_FOUND')
#             if order_details is not None:
#                 result = {'delivery_garments': delivery_garments, 'order_type': order_details.OrderTypeId}
#             else:
#                 result = {'delivery_garments': delivery_garments}
#             final_data['result'] = result
#         else:
#             # No garments for delivery.
#             final_data = generate_final_data('DATA_NOT_FOUND')
#         log = {
#             "time": 'time3'
#         }
#         info_logger(f'Route: {request.path}').info(json.dumps(log))
#         # log={
#         #     "latest_qc_id":latest_qc_id
#         #     # "select_complaint_id":select_complaint_id,
#         #     # "select_crm_complaint_status":select_crm_complaint_status,
#         #     # "select_jfsl_ticket_id":select_jfsl_ticket_id,
#         #     # "select_tag_id":select_tag_id
#         # }
#         # info_logger(f'Route: {request.path}').info(json.dumps(log))
#     else:
#         # Form validation error.
#         final_data = generate_final_data('FORM_ERROR')
#         final_data['errors'] = populate_errors(delivery_garments_form.errors)

#     return final_data

@delivery_blueprint.route('/get_delivery_garments', methods=["POST"])
# @authenticate('delivery_user')
def get_delivery_garments_():
    """
    API for getting the garments for the delivery.
    @return:
    """
    delivery_garments_form = GetDeliveryGarmentsForm()
    if delivery_garments_form.validate_on_submit():
        TRNNo = delivery_garments_form.TRNNo.data
        EGRN = delivery_garments_form.EGRN.data
        delivery_garments = []
        order_detail = []
        order_details = None
        try:
            query = f""" EXEC JFSL.Dbo.SPFabGetDeliveryGarments @TRNNo ='{TRNNo}'"""
            order_details = CallSP(query).execute().fetchall()
            # order_details = order_details[0]

            log = {
            "order_details": order_details,
            "query" :query
                }
            info_logger(f'Route: {request.path}').info(json.dumps(log))
            
            complaint_history = []
            if order_details is not None:
                query = f"EXEC JFSL.Dbo.SPFabGetRewashOrCRMComplaintCountBasedOnEGRN @EGRN ='{EGRN}'"
                complaint_history = CallSP(query).execute().fetchall()
                log = {
                "complaint_history": complaint_history,
                "query" :query
                    }
                info_logger(f'Route: {request.path}').info(json.dumps(log))
               
            if complaint_history:
                for complaint in complaint_history:
                    result = {'Complaint': False, 'RewashCount': 0}
                    # Complaint history found.
                    for delivery_garment in order_details:
                        if complaint['TAGNO'] == delivery_garment['TagId']:
                            # A match found.
                            delivery_garment['Complaint'] = 1
                            delivery_garment['RewashCount'] = result['RewashCount']
                            break

        except Exception as e:
            error_logger(f'Route: {request.path}').error(e)

        if order_details:
            # Garments found.
            final_data = generate_final_data('DATA_FOUND')
            if order_details is not None:
                result = {'delivery_garments': order_details, 'order_type': order_details[0].get('OrderType')}
            else:
                result = {'delivery_garments': order_details}
            final_data['result'] = result
        else:
            # No garments for delivery.
            final_data = generate_final_data('DATA_NOT_FOUND')
       

    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(delivery_garments_form.errors)
    log = {
            "final_data": final_data
        }
    info_logger(f'Route: {request.path}').info(json.dumps(log))

    return final_data

# @delivery_blueprint.route('/get_order_garment_details', methods=["POST"])
# @authenticate('delivery_user')
# def get_order_garment_details():
#     """
#     API for getting the details of a particular order garment.
#     @return:
#     """
#     garment_details_form = GetGarmentDetailsForm()
#     if garment_details_form.validate_on_submit():
#         order_garment_id = garment_details_form.order_garment_id.data
#         garment_details = None
#         price = 0.0
#         garment_instructions = []
#         garment_issues = []
#         photos = []
#         fabcliq_details = []
#         qc_details = []
#         complaint = 0
#         rewash_count = 0
#         try:
#             # If TagId is NOT present in the OrderGarments table, return "NA", else return the value.
#             select_tag_id = case([(OrderGarment.TagId == None, "NA"), ],
#                                  else_=OrderGarment.TagId).label("TagId")

#             # If GarmentColour is NOT present in the OrderGarments table, return "NA", else return the value.
#             select_garment_colour = case([(OrderGarment.GarmentColour == None, "NA"), ],
#                                          else_=OrderGarment.GarmentColour).label("GarmentColour")

#             # If GarmentBrand is NOT present in the OrderGarments table, return "NA", else return the value.
#             select_garment_brand = case([(OrderGarment.GarmentBrand == None, "NA"), ],
#                                         else_=OrderGarment.GarmentBrand).label("GarmentBrand")

#             # If JFSLTicketId is NOT present in the Complaints table, return "NA", else return the value.
#             select_jfsl_ticket_id = case([(Complaint.JFSLTicketId == None, "NA"), ],
#                                          else_=Complaint.JFSLTicketId).label("JFSLTicketId")

#             # If CRMComplaintStatus is NOT present in the Complaints table, return "NA", else return the value.
#             select_crm_complaint_status = case([(Complaint.CRMComplaintStatus == None, "NA"), ],
#                                                else_=Complaint.CRMComplaintStatus).label("CRMComplaintStatus")

#             # Selecting CRM Complaint Id.
#             select_complaint_id = case([(OrderGarment.CRMComplaintId == None, 0), ],
#                                        else_=OrderGarment.CRMComplaintId).label("CRMComplaintId")
#             # Select garment length.
#             select_length = case([(OrderGarment.Length == None, 0), ],
#                                  else_=OrderGarment.Length).label("Length")
#             # Select garment length.
#             select_width = case([(OrderGarment.Width == None, 0), ],
#                                 else_=OrderGarment.Width).label("Width")
#             # Select garment length.
#             select_sqft = case([(OrderGarment.Sqft == None, 0), ],
#                                else_=OrderGarment.Sqft).label("Sqft")

#             # Selecting the string values for the QCStatus.
#             select_qc_status = case([
#                 (cast(OrderGarment.QCStatus, String).label('QCStatus') == None, "NA"),
#                 (cast(OrderGarment.QCStatus, String).label('QCStatus') == 1, "Not Served"),
#                 (cast(OrderGarment.QCStatus, String).label('QCStatus') == 2, "Approved"),
#                 (cast(OrderGarment.QCStatus, String).label('QCStatus') == 3, "QCPending"),
#             ],
#                 else_=cast(OrderGarment.QCStatus, String)).label("QCStatus")

#             # Selecting the TagId in the Complaints table in related to the TagId of the
#             # OrderGarments table.
#             select_tag_id_from_complaints = db.session.query(Complaint.TagId).filter(
#                 Complaint.TagId == OrderGarment.TagId).order_by(Complaint.RecordCreatedDate.desc()).limit(
#                 1).correlate(OrderGarment).as_scalar()

#             # Getting the garment details from the DB.
#             garment_details = db.session.query(Garment.GarmentName, OrderGarment.POSOrderGarmentId,
#                                                OrderGarment.GarmentId, OrderGarment.ServiceTatId,
#                                                OrderGarment.ServiceTypeId, select_tag_id, select_garment_colour,
#                                                select_length, select_width, select_sqft,
#                                                select_garment_brand, select_qc_status, Order.BranchCode, Order.EGRN,
#                                                Order.OrderTypeId, Order.OrderId, Order.CustomerId,
#                                                select_complaint_id, select_jfsl_ticket_id,
#                                                select_crm_complaint_status).join(
#                 Garment,
#                 OrderGarment.GarmentId == Garment.GarmentId).outerjoin(
#                 Complaint,
#                 Complaint.TagId == select_tag_id_from_complaints).filter(
#                 OrderGarment.OrderGarmentId == order_garment_id).join(Order,
#                                                                       OrderGarment.OrderId == Order.OrderId).one_or_none()

#             if garment_details is not None:
#                 # Getting the garment price from the DB.
#                 price = delivery_controller_queries.get_price_for_garment(garment_details.GarmentId,
#                                                                           garment_details.ServiceTatId,
#                                                                           garment_details.ServiceTypeId,
#                                                                           garment_details.BranchCode)
#                 price = SerializeSQLAResult(price).serialize_one()['Price']
#                 # If the delivery is rewash the amount of each garment should be zero
#                 if garment_details.OrderTypeId == 2:
#                     price = 0.0
#                 # Getting the garment instructions based on order garment id.
#                 garment_instructions = db.session.query(OrderInstruction.OrderInstructionId,
#                                                         GarmentInstruction.InstructionName,
#                                                         GarmentInstruction.InstructionDescription).join(
#                     GarmentInstruction, OrderInstruction.InstructionId == GarmentInstruction.InstructionId).filter(
#                     OrderInstruction.OrderGarmentId == order_garment_id, OrderInstruction.IsDeleted == 0).all()

#                 # Getting the garment issues based on order garment id.

#                 garment_issues = db.session.query(OrderIssue.OrderIssueId,
#                                                   GarmentIssue.IssueName,
#                                                   GarmentIssue.IssueDescription).join(
#                     GarmentIssue,
#                     OrderIssue.IssueId == GarmentIssue.IssueId).filter(
#                     OrderIssue.OrderGarmentId == order_garment_id, OrderIssue.IsDeleted == 0).all()

#                 # Getting the garment photos based on order garment id.

#                 photos = db.session.query(OrderPhoto.GarmentImage, OrderPhoto.OrderPhotoId, OrderPhoto.IsNormal,
#                                           OrderPhoto.IsQC, OrderPhoto.IsVAS, OrderPhoto.RecordCreatedDate).filter(
#                     OrderPhoto.OrderGarmentId == order_garment_id, OrderPhoto.IsDeleted == 0).all()

#                 # Getting the QC details of the garment.

#                 # If Image1 is NOT present in the QCInfo table, return "NA", else return the value.
#                 select_image_1 = case([(QCInfo.Image1 == None, "NA"), (QCInfo.Image1 == "", "NA"), ],
#                                       else_=QCInfo.Image1).label("Image1")

#                 # If Image2 is NOT present in the QCInfo table, return "NA", else return the value.
#                 select_image_2 = case([(QCInfo.Image2 == None, "NA"), (QCInfo.Image2 == "", "NA"), ],
#                                       else_=QCInfo.Image2).label("Image2")

#                 # If Image3 is NOT present in the QCInfo table, return "NA", else return the value.
#                 select_image_3 = case([(QCInfo.Image3 == None, "NA"), (QCInfo.Image3 == "", "NA"), ],
#                                       else_=QCInfo.Image3).label("Image3")

#                 # Selecting the string values for the QCStatus.
#                 select_qc_status = case([
#                     (cast(QCInfo.Status, String).label('QCStatus') == None, "NA"),
#                     (cast(QCInfo.Status, String).label('QCStatus') == 1, "Not Served"),
#                     (cast(QCInfo.Status, String).label('QCStatus') == 2, "Approved"),
#                     (cast(QCInfo.Status, String).label('QCStatus') == 3, "QCPending"),
#                 ],
#                     else_=cast(QCInfo.Status, String)).label("QCStatus")

#                 qc_details = db.session.query(select_qc_status, QCInfo.Remark, QCInfo.RecordCreatedDate,
#                                               QCInfo.Remark,
#                                               select_image_1, select_image_2,
#                                               select_image_3).filter(
#                     QCInfo.POSOrderGarmentID == garment_details.POSOrderGarmentId, QCInfo.IsActive == 1).all()

#                 # Getting the complaint history of the garment.
#                 garment_complaint = ameyo_module.check_complaint_garment(garment_details.TagId)

#                 complaint = 0 if not garment_complaint['Complaint'] else 1
#                 rewash_count = garment_complaint['RewashCount']
#                 # Calling SP for getting the images based on egrn
#                 query = f"EXEC {OLD_DB}.dbo.USP_GET_IMAGES_BASED_ON_EGRN @EGRNNo='{garment_details.EGRN}' "
#                 fabcliq_details = CallSP(query).execute().fetchall()

#                 qc_image_query = f"EXEC {OLD_DB}.dbo.USP_GET_IMAGES_BASED_ON_TAG @TagNo='{garment_details.TagId}'"
#                 # qc_image_query = f"EXEC Mobile_JFSL_UAT.dbo.USP_GET_IMAGES_BASED_ON_TAG @TagNo='{'SPEC00000006779'}'"
#                 qc_images = CallSP(qc_image_query).execute().fetchall_by_date()
#                 alternate_keys = ['TagId', 'Photo', 'ImageCategory', 'RecordCreatedDate']
#                 qc_image_list = []
#                 for i in qc_images:
#                     final_dict = dict(zip(alternate_keys, list(i.values())))
#                     qc_image_list.append(final_dict)

#         except Exception as e:
#             error_logger(f'Route: {request.path}').error(e)

#         if garment_details is not None:

#             final_data = generate_final_data('DATA_FOUND')
#             garment_details = SerializeSQLAResult(garment_details).serialize_one()
#             garment_details['Price'] = price
#             garment_details['Instructions'] = SerializeSQLAResult(garment_instructions).serialize()
#             garment_details['Issues'] = SerializeSQLAResult(garment_issues).serialize()
#             garment_details['Photos'] = SerializeSQLAResult(photos).serialize(
#                 full_date_fields=['RecordCreatedDate'])
#             garment_details['QC'] = SerializeSQLAResult(qc_details).serialize(full_date_fields=['RecordCreatedDate'])
#             garment_details['Fabcliq'] = fabcliq_details
#             garment_details['QcPhotos'] = qc_image_list
#             garment_details['Complaint'] = complaint
#             garment_details['RewashCount'] = rewash_count
#             final_data['result'] = garment_details
#         else:
#             final_data = generate_final_data('DATA_NOT_FOUND')
#     else:
#         # Form validation error.
#         final_data = generate_final_data('FORM_ERROR')
#         final_data['errors'] = populate_errors(garment_details_form.errors)

#     return final_data

@delivery_blueprint.route('/get_order_garment_details', methods=["POST"])
# @authenticate('delivery_user')
def get_order_garment_details():
    """
    API for getting the details of a particular order garment.
    @return:
    """
    garment_details_form = GetGarmentDetailsForm()
    if garment_details_form.validate_on_submit():
        OrderGarmentID = garment_details_form.order_garment_id.data
        garment_details = None
        price = 0.0
        garment_instructions = []
        garment_issues = []
        photos = []
        fabcliq_details = []
        qc_image_list = []
        qc_details = []
        complaint = 0
        rewash_count = 0
        log = {
            "garment_details_form": garment_details_form.data
        }
        info_logger(f'Route: {request.path}').info(json.dumps(log))
        try:
            query = f"""EXEC JFSL.Dbo.SPFabGetDeliveryGarments @OrderGarmentID = '{OrderGarmentID}'"""
            print(query)
            garment_details = CallSP(query).execute().fetchall()
            print(garment_details)
            if garment_details is not None:
                # Getting the garment price from the DB.
                price = garment_details[0].get('Price')
                garment_details[0]['Price'] = int(price)
                print(price)
                EGRN = garment_details[0].get('EGRN')
                TagId = garment_details[0].get('TagId')
                # If the delivery is rewash the amount of each garment should be zero
                if garment_details[0].get('OrderTypeId') == 2:
                    price = 0.0

                # Loop through garment details
                for garment in garment_details:
                    # Create instruction dictionary
                    garment_instructions.append({
                        'OrderInstructionId': garment['OrderInstructionId'],
                        'InstructionName': garment['InstructionName'],
                        'InstructionDescription': garment['InstructionDescription']
                    })

                    # Create issue dictionary
                    garment_issues.append({
                        'OrderIssueId': garment['IssueId'],
                        'IssueName': garment['IssueName'],
                        'IssueDescription': garment['IssueDescription']
                    })

                    # Create photo dictionary
                    photos.append({
                        'GarmentImage': garment['GarmentImage'],
                        'OrderPhotoId': garment['OrderPhotoId'],
                        'IsNormal': garment['IsNormal'],
                        'IsQC': garment['IsQC'],
                        'IsVAS': garment['IsVAS'],
                        'RecordCreatedDate': garment['OrderPhotoCreatedDate']
                    })

                    qc_details.append({
                        "Status":garment['QCStatus'],
                        "Image1": garment['Image1'],
                        "Image2": garment['Image2'],
                        "Image3": garment['Image3'],
                        "Image3": garment['Image3'],
                        "Remark": garment['Remark'],
                        "RecordCreatedDate": garment['QCRecordCreatedDate']
                    })


                               # Getting the complaint history of the garment.
                tag_id = TagId
                garment_complaint = ameyo_module.check_complaint_garment(tag_id,EGRN)

                complaint = 0 if not garment_complaint['Complaint'] else 1
                log = {
                 "garment_complaint": garment_complaint
                    }
                info_logger(f'Route: {request.path}').info(json.dumps(log))
                rewash_count = garment_complaint['RewashCount']
                # Calling SP for getting the images based on egrn


                qc_image_query = f"EXEC {OLD_DB}.dbo.USP_GET_IMAGES_BASED_ON_TAG @TagNo='{TagId}'"
                # qc_image_query = f"EXEC Mobile_JFSL_UAT.dbo.USP_GET_IMAGES_BASED_ON_TAG @TagNo='{'SPEC00000006779'}'"
                qc_images = CallSP(qc_image_query).execute().fetchall_by_date()
                alternate_keys = ['TagId', 'Photo', 'ImageCategory', 'RecordCreatedDate']

                for i in qc_images:
                    final_dict = dict(zip(alternate_keys, list(i.values())))
                    qc_image_list.append(final_dict)

        except Exception as e:
            error_logger(f'Route: {request.path}').error(e)

        if garment_details is not None:

            final_data = generate_final_data('DATA_FOUND')
            garment_details = garment_details
            garment_details[0]['Price'] = int(price)
            garment_details[0]['Instructions'] = garment_instructions
            garment_details[0]['Issues'] = garment_issues
            garment_details[0]['Photos'] = photos

            garment_details[0]['QC'] = qc_details
            garment_details[0]['Fabcliq'] = []
            garment_details[0]['QcPhotos'] = qc_image_list
            garment_details[0]['Complaint'] = complaint
            garment_details[0]['RewashCount'] = rewash_count
            final_data['result'] = garment_details[0]
        else:
            final_data = generate_final_data('DATA_NOT_FOUND')
    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(garment_details_form.errors)
    log = {
        "final_data": final_data
        }
    info_logger(f'Route: {request.path}').info(json.dumps(log))

    return final_data


@delivery_blueprint.route('/save_gps_cords', methods=["POST"])
@authenticate('delivery_user')
def save_gps_cords():
    """
    API for saving the GPS co-ordinates of a customer's address.
    @return:
    """
    gps_cords_form = SaveGPSCordsForm()
    if gps_cords_form.validate_on_submit():
        address_id = gps_cords_form.address_id.data
        lat = gps_cords_form.lat.data
        long = gps_cords_form.long.data
        is_saved = False
        try:
            # Getting the address from the DB.
            address = db.session.query(CustomerAddres).filter(CustomerAddres.CustAddressId == address_id).one_or_none()
            if address is not None:
                # Updating it's GPS co-ordinates.
                try:
                    address.Lat = lat
                    address.Long = long
                    address.RecordLastUpdatedDate = get_current_date()
                    db.session.commit()
                    is_saved = True
                except Exception as e:
                    db.session.rollback()
                    error_logger(f'Route: {request.path}').error(e)
        except Exception as e:
            error_logger(f'Route: {request.path}').error(e)

        if is_saved:
            final_data = generate_final_data('DATA_SAVED')
        else:
            final_data = generate_final_data('DATA_SAVE_FAILED')
    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(gps_cords_form.errors)

    return final_data


# @delivery_blueprint.route('/update_customer_address', methods=["PUT"])
# @authenticate('delivery_user')
# def update_customer_address():
#     """
#     API for updating the customer's address.
#     @return:
#     """
#     update_address_form = UpdateCustomerAddressForm()
#     if update_address_form.validate_on_submit():
#         address_id = update_address_form.address_id.data
#         address_line_1 = update_address_form.address_line_1.data
#         address_line_2 = update_address_form.address_line_2.data if update_address_form.address_line_2.data != '' else None
#         address_line_3 = update_address_form.address_line_3.data if update_address_form.address_line_3.data != '' else None
#         landmark = update_address_form.landmark.data if update_address_form.landmark.data != '' else None
#         pincode = update_address_form.pincode.data if update_address_form.pincode.data != '' else None
#         delivery_user_branch_code = None if update_address_form.delivery_user_branch_code.data == '' else update_address_form.delivery_user_branch_code.data
#         address_name = update_address_form.address_name.data
#         customer_type = update_address_form.customer_type.data
#         mobile_number = update_address_form.mobile_number.data
#         lat = update_address_form.lat.data
#         long = update_address_form.long.data
#         # Result flag variable
#         address_updated = False
#         address = None
#         customer_details = None
#         area_code = None
#         city_code = None
#         essential_details = None
#         try:
#             # Checking POS or DB is to be updated
#             if customer_type != "POS":
#                 # Getting the customer address from the DB.
#                 address = db.session.query(CustomerAddres).filter(
#                     CustomerAddres.CustAddressId == address_id).one_or_none()
#                 if pincode is not None:
#                     # Pin code is provided. So selecting the essential data from the pin code itself.
#                     essential_details = delivery_controller_queries.get_essential_details_from_pincode(pincode)
#                 else:
#                     # Pin code is not provided. So selecting the essential data from the delivery user's
#                     # branch itself (if provided).
#                     if delivery_user_branch_code is not None:
#                         essential_details = delivery_controller_queries.get_essential_details_from_dbranchcode(
#                             delivery_user_branch_code)

#                 if essential_details is not None:
#                     # Essential details are found based on given pin code/delivery user's branch code.
#                     area_code = essential_details.AreaCode
#                     pincode = essential_details.Pincode
#                     city_code = essential_details.CityCode

#                 if address is not None:
#                     try:
#                         # Updating the customer address.
#                         address.AddressLine1 = address_line_1
#                         address.AddressLine2 = address_line_2
#                         address.AddressLine3 = address_line_3
#                         address.Landmark = landmark
#                         address.Lat = lat
#                         address.Long = long
#                         if pincode is not None:
#                             address.Pincode = pincode
#                         if area_code is not None:
#                             address.AreaCode = area_code
#                         if city_code is not None:
#                             address.CityCode = city_code
#                         address.RecordLastUpdatedDate = get_current_date()
#                         db.session.commit()
#                         address_updated = True

#                         customer_details = db.session.query(Customer.CustomerCode, Customer.Gender, Customer.EmailId,
#                                                             Customer.DateOfBirth, Customer.Occupation).filter(
#                             Customer.CustomerId == address.CustomerId).one_or_none()

#                         customer_details = SerializeSQLAResult(customer_details).serialize_one()
#                         address = {'AddressLine1': address.AddressLine1, 'AddressLine2': address.AddressLine2,
#                                    'AddressLine3': address.AddressLine3, 'AddressName': address.AddressName,
#                                    'CityCode': address.CityCode, 'AreaCode': address.AreaCode}

#                     except Exception as e:
#                         db.session.rollback()
#                         error_logger(f'Route: {request.path}').error(e)

#             else:

#                 query = f"EXEC {SERVER_DB}.dbo.GetCustomerDetails @mobileNo='{mobile_number}'"
#                 customer_details_in_pos = CallSP(query).execute().fetchone()
#                 # Customer exists in the POS DB and not CustomerApp DB.
#                 customer_details = {"CustomerCode": customer_details_in_pos['CustomerCode'],
#                                     "BranchCode": customer_details_in_pos['BranchCode'],
#                                     "EmailId": customer_details_in_pos['Email'],
#                                     "MobileNo": customer_details_in_pos['ContactNo'],
#                                     "CustomerName": customer_details_in_pos['CustomerName'], 'Occupation': '',
#                                     "Gender": customer_details_in_pos['Gender'][0],
#                                     'DateOfBirth': customer_details_in_pos['DOB']}

#                 # Populating the address fields.
#                 address = {"AddressLine1": address_line_1, "AddressLine2": address_line_2,
#                            "AddressLine3": address_line_3,
#                            "AreaCode": area_code, "Pincode": pincode, "CityCode": city_code,
#                            'AddressName': address_name}
#                 address_updated = True

#         except Exception as e:
#             error_logger(f'Route: {request.path}').error(e)

#         if address_updated:
#             # If the address is updated, then need to update in POS as well.
#             if customer_details:
#                 delivery_controller_queries.update_customer_address_in_pos(customer_details, address)
#         if address_updated:
#             final_data = generate_final_data('DATA_UPDATED')
#         else:
#             final_data = generate_final_data('DATA_UPDATE_FAILED')
#     else:
#         # Form validation error.
#         final_data = generate_final_data('FORM_ERROR')
#         final_data['errors'] = populate_errors(update_address_form.errors)

#     return final_data

import re
from sqlalchemy.sql import text




import re

def clean_address_field(address):
    if not address:
        return ''
    address = address.replace("'", "")  # Remove single quotes
    # Remove unwanted special characters between word characters (not digits, commas, dots)
    address = re.sub(r"(?<=\w)[^\w\s,\.](?=\w)", "", address)
    return address.strip()




@delivery_blueprint.route('/update_customer_address_live', methods=["POST"])
# @authenticate('delivery_user')
def update_customer_address_live():
    """
    API for updating the customer's address.
    @return:
    """
    update_address_form = UpdateCustomerAddressForm()
    log_data = {
        "update_address_form":update_address_form.data
    }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))
    if update_address_form.validate_on_submit():

        address_line_1 = clean_address_field(update_address_form.address_line_1.data)
        address_line_2 = clean_address_field(update_address_form.address_line_2.data if update_address_form.address_line_2.data != '' else '')
        address_line_3 = clean_address_field(update_address_form.address_line_3.data if update_address_form.address_line_3.data != '' else '')
        landmark = clean_address_field(update_address_form.landmark.data if update_address_form.landmark.data != '' else '')
        pincode = update_address_form.pincode.data if update_address_form.pincode.data != '' else ''
        delivery_user_branch_code = '' if update_address_form.delivery_user_branch_code.data == '' else update_address_form.delivery_user_branch_code.data
        address_name = update_address_form.address_name.data
        address_type = update_address_form.AddressType.data
        CustomerCode = update_address_form.CustomerCode.data
        customer_type = update_address_form.customer_type.data
        mobile_number = update_address_form.mobile_number.data
        lat = update_address_form.lat.data
        long = update_address_form.long.data
        geo_location = clean_address_field(update_address_form.geo_location.data)
        TRNNo = '' if update_address_form.TRNNo.data in ('NA', '') else update_address_form.TRNNo.data

        BookingID = '' if update_address_form.BookingId.data in ('0', '',0) else update_address_form.BookingId.data

        

        log_data = {
                "update_address_form":update_address_form.data
            }
        info_logger(f'Route: {request.path}').info(json.dumps(log_data))
        # Result flag variable
        address_updated = False

        try:
           
            query =f""" EXEC JFSL.Dbo.[SPUpdateCustomerInfoCustApp] @CustomerCode ='{CustomerCode}',@address_line_1 = '{address_line_1}', @address_line_2 = '{address_line_2}'
                    ,@address_line_3 = '{address_line_3}' , @landmark ='{landmark}', @pincode ='{pincode}',@delivery_user_branch_code ='{delivery_user_branch_code}',@address_name ='{address_type}'
                    ,@mobile_number ='{mobile_number}' ,@lat ='{lat}' ,@long ='{long}',@geo_location = '{geo_location}',@TRNNO = '{TRNNo}',@BookingID = '{BookingID}'"""
            db.engine.execute(text(query).execution_options(autocommit=True))
            address_updated = True
            log_data = {
                "query":query
            }
            info_logger(f'Route: {request.path}').info(json.dumps(log_data))
        except Exception as e:
            error_logger(f'Route: {request.path}').error(e)

        if address_updated:
            final_data = generate_final_data('DATA_UPDATED')
        else:
            final_data = generate_final_data('DATA_UPDATE_FAILED')
    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(update_address_form.errors)
    log_data = {
        "final_data":final_data
    }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))

    return final_data


@delivery_blueprint.route('/update_customer_address', methods=["POST"])
# @authenticate('delivery_user')
def update_customer_address():
    """
    API for updating the customer's address.
    @return:
    """
    update_address_form = UpdateCustomerAddressForm()
    log_data = {
        "update_address_form":update_address_form.data
    }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))
    if update_address_form.validate_on_submit():

        address_line_1 = update_address_form.address_line_1.data
        address_line_2 = update_address_form.address_line_2.data if update_address_form.address_line_2.data != '' else None
        address_line_3 = update_address_form.address_line_3.data if update_address_form.address_line_3.data != '' else None
        landmark = update_address_form.landmark.data if update_address_form.landmark.data != '' else None
        pincode = update_address_form.pincode.data if update_address_form.pincode.data != '' else None
        delivery_user_branch_code = None if update_address_form.delivery_user_branch_code.data == '' else update_address_form.delivery_user_branch_code.data
        address_name = update_address_form.address_name.data
        address_type = update_address_form.AddressType.data
        CustomerCode = update_address_form.CustomerCode.data
        customer_type = update_address_form.customer_type.data
        mobile_number = update_address_form.mobile_number.data
        lat = update_address_form.lat.data
        long = update_address_form.long.data
        geo_location = update_address_form.geo_location.data 
        TRNNo = update_address_form.TRNNo.data if update_address_form.TRNNo.data != '' else ''
        BookingID = update_address_form.BookingId.data if update_address_form.BookingId.data != '' else ''
        #address_line_2 = f"{address_line_2} {address_line_3}"
        

        log_data = {
                "update_address_form":update_address_form.data
            }
        info_logger(f'Route: {request.path}').info(json.dumps(log_data))
        # Result flag variable
        address_updated = False

        try:
           
            # query =f""" EXEC JFSL_UAT.Dbo.[SPUpdateCustomerInfoCustApp] @CustomerCode ='{CustomerCode}',@address_line_1 = '{address_line_1}', @address_line_2 = '{address_line_2}'
            #         ,@address_line_3 = '{address_line_3}' , @landmark ='{landmark}', @pincode ='{pincode}',@delivery_user_branch_code ='{delivery_user_branch_code}',@address_name ='{address_type}'
            #         ,@mobile_number ='{mobile_number}' ,@lat ='{lat}' ,@long ='{long}',@geo_location = '{geo_location}',@TRNNO = '{TRNNo}',@BookingID = '{BookingID}'"""
            # db.engine.execute(text(query).execution_options(autocommit=True))

            query = text("""
                EXEC JFSL.Dbo.SPUpdateCustomerInfoCustApp 
                    @CustomerCode = :CustomerCode,
                    @address_line_1 = :address_line_1,
                    @address_line_2 = :address_line_2,
                    @address_line_3 = :address_line_3,
                    @landmark = :landmark,
                    @pincode = :pincode,
                    @delivery_user_branch_code = :delivery_user_branch_code,
                    @address_name = :address_type,
                    @mobile_number = :mobile_number,
                    @lat = :lat,
                    @long = :long,
                    @geo_location = :geo_location,
                    @TRNNO = :TRNNo,
                    @BookingID = :BookingID
            """)

            params = {
                "CustomerCode": CustomerCode,
                "address_line_1": address_line_1,
                "address_line_2": address_line_2,
                "address_line_3": address_line_3,
                "landmark": landmark,
                "pincode": pincode,
                "delivery_user_branch_code": delivery_user_branch_code,
                "address_type": address_type,
                "mobile_number": mobile_number,
                "lat": lat,
                "long": long,
                "geo_location": geo_location,
                "TRNNo": TRNNo,
                "BookingID": BookingID
            }

            db.engine.execute(query.execution_options(autocommit=True), params)

            #address_updated = True

            address_updated = True
            log_data = {
                "query":str(query),
                "parameter_values": params
            }
            info_logger(f'Route: {request.path}').info(json.dumps(log_data))
        except Exception as e:
            error_logger(f'Route: {request.path}').error(e)

        if address_updated:
            final_data = generate_final_data('DATA_UPDATED')
        else:
            final_data = generate_final_data('DATA_UPDATE_FAILED')
    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(update_address_form.errors)
    log_data = {
        "final_data":final_data
    }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))

    return final_data





@delivery_blueprint.route('/validate_discount_code', methods=["POST"])
# @authenticate('delivery_user')
def validate_discount_code():
    """
    API for validating the discount code.
    If the pickup request has already picked up (has a corresponding order with EGRN),
    discount code validation is still allowed.
    """
    validate_discount_form = ValidateDiscountCodeForm()
    info_logger(f'Route: {request.path}').info(json.dumps({
        "validate_discount_form": validate_discount_form.data
    }))

    if not validate_discount_form.validate_on_submit():
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(validate_discount_form.errors)
        info_logger(f'Route: {request.path}').info(json.dumps({"final_data": final_data}))
        return final_data

    BookingID = validate_discount_form.BookingId.data
    discount_code = validate_discount_form.discount_code.data
    branch_code = validate_discount_form.BranchCode.data
    customer_code = validate_discount_form.CustomerCode.data
    source = validate_discount_form.source.data
    result = None
    already_applied_discount_code = None
    is_already_applied = False
    db_discount_code = discount_code
    is_er_coupon = 0
    er_discount_code = None

    try:
        if discount_code == '' and source == "FabXpress":
            # Clear the discount
            result = {
                'IsValid': 1,
                'Message': 'DISCOUNT CODE CLEARED',
                'Discount': 0.0,
                'AppRemarks': 'Discount code cleared',
                "Remarks": 'Discount code cleared'
            }

            db.session.execute(
                text("""
                    UPDATE JFSL.dbo.PickupInfo 
                    SET ERCouponCode = '', IsERCoupon = '', ERRequestID = '', DiscountCode = ''
                    WHERE BookingID = :BookingID
                """),
                {"BookingID": BookingID}
            )
            db.session.commit()

        elif discount_code == '' and source != "FabXpress":
            result = {
                'IsValid': 1,
                'Message': "DISCOUNT CODE IS FROM FABRICARE AND IT CAN NOT BE CLEARED",
                'Discount': 0.0,
                'AppRemarks': "Discount code is from fabricare and it can't be cleared",
                "Remarks": "Discount code is from fabricare and it can't be cleared",
            }

        else:
            source = 'pickup'  
            
            if not already_applied_discount_code:
                validation = common_module.validate_discount_code(
                    discount_code, source, None, customer_code, branch_code, is_er_coupon
                )
                log_data = {

                        "validation1": validation
                            }
                info_logger(f'Route: {request.path}').info(json.dumps(log_data))
             
                if validation.get('ISVALID'):
                    DiscountCode = validation.get('DISCOUNTCODE')
                    response_code = validation.get('ISVALID')
                    response_message = validation.get('RESULT')
                    app_remarks = validation.get('AppRemark')
                    Remarks= validation.get('AppRemark')
                    response_discount_amount = float(validation.get('DISCOUNTAMOUNT', 0.0))

                    result = {
                        'IsValid': response_code,
                        'Message': response_message,
                        'Discount': response_discount_amount,
                        'AppRemarks': DiscountCode,
                        "Remarks":Remarks

                    }

                    query = f"""EXEC JFSL.Dbo.SPFabERCoupanCodeValidation @ActualDiscCode = '{discount_code}'"""
                  
                    result_from_erp = CallSP(query).execute().fetchone()
                    log_data = {

                    "result_from_erp": result_from_erp
                        }
                    info_logger(f'Route: {request.path}').info(json.dumps(log_data))
                    if result_from_erp and result_from_erp.get('Message') == 'Success':
                        CodeFromER = discount_code
                        IsERCoupon = 1
                        ERRequestID = 1
                    else:
                        CodeFromER = ''
                        IsERCoupon = 0
                        ERRequestID = 0
                    try:
                        db.session.execute(
                            text("""
                                UPDATE JFSL.dbo.PickupInfo 
                                SET ERCouponCode = :CodeFromER,
                                    IsERCoupon = :IsERCoupon,
                                    ERRequestID = :ERRequestID,
                                    DiscountCode = :DiscountCode
                                WHERE BookingID = :BookingID
                            """),
                            {
                                "CodeFromER": CodeFromER,
                                "IsERCoupon": IsERCoupon,
                                "ERRequestID": ERRequestID,
                                "DiscountCode": DiscountCode,
                                "BookingID": BookingID
                            }
                        )
                        db.session.commit()
                    except Exception as e:
                        db.session.rollback()
                        error_logger(f'Route: {request.path}').error(f'DB Update Error: {str(e)}')

                else:
                    result = None
            else:
                is_already_applied = True

    except Exception as e:
        error_logger(f'Route: {request.path}').error(f'Unhandled Exception: {str(e)}')

    if result is not None:
        final_data = generate_final_data('SUCCESS')
        final_data['result'] = result
    else:
        if is_already_applied:
            final_data = generate_final_data('CUSTOM_FAILED', 'Discount code is already applied.')
        else:
            final_data = generate_final_data('CUSTOM_FAILED', 'Invalid Discount Code')

    info_logger(f'Route: {request.path}').info(json.dumps({"final_data": final_data}))
    return final_data





# @delivery_blueprint.route('/validate_coupon_code', methods=["POST"])
# @authenticate('delivery_user')
# def validate_coupon_code_():
#     """
#     API for validating the coupon code. (Compensation coupons, marketing coupons...etc)
#     If the pickup request has already picked up, i.e. has a corresponding order that has an EGRN,
#     coupon code calculation can also be performed.
#     @return:
#     """
#     validate_coupon_form = ValidateCouponCodeForm()
#     if validate_coupon_form.validate_on_submit():

#         coupon_code = validate_coupon_form.coupon_code.data
#         BookingID = validate_coupon_form.BookingId.data
#         branch_code = validate_coupon_form.BranchCode.data
#         customer_code = validate_coupon_form.CustomerCode.data
#         source = validate_coupon_form.source.data
#         # Result flag
#         result = None
#         is_already_applied = False
#         selected_coupon_details = {}
#         egrn = None
#         try:
#             # If the coupon code is cleared clear adhoc coupon code
#             pickup_details = db.session.execute(
#                 text(
#                     "SELECT * FROM JFSL_UAT.dbo.PickupInfo (nolock) WHERE BookingID = :BookingID"
#                 ),
#                 {"BookingID": BookingID}
#             ).fetchone()
#             if coupon_code == '' and source == "FabXpress":
#                 result = {'IsValid': 1, 'Message': 'Coupon code is cleared'}
#             elif coupon_code == '' and pickup_details is not None and source != "FabXpress":
#                 result = {'IsValid': 1, 'Message': "Coupon code is from Fabricare and it can not be cleared",
#                           'Discount': 0.0, 'AppRemarks': "Coupon code is from fabricare and it can't be cleared"}
#             else:
#                 source = 'pickup'

#                 # Validating the discount code.
#                 validation = common_module.validate_coupon_code(coupon_code, customer_code,
#                                                                 branch_code, source, egrn)
#                 if validation:
#                     # Successfully executed the SP and populated the result.

#                     if validation['message'] == "Valid Promocode":
#                         coupon_valid = 1
#                     else:
#                         coupon_valid = 0

#                     if selected_coupon_details:
#                         result = {'IsValid': coupon_valid, 'Message': validation['message'],
#                                   'Amount': selected_coupon_details['DISCOUNTAMOUNT']}
#                     else:
#                         result = {'IsValid': coupon_valid, 'Message': validation['message']}

#                 else:
#                     # Already a DiscountCode is applied in the PickupRequest table or Orders table.
#                     is_already_applied = True

#         except Exception as e:
#             error_logger(f'Route: {request.path}').error(e)

#         if result is not None:
#             final_data = generate_final_data('SUCCESS')
#             final_data['result'] = result
#         else:
#             if is_already_applied:
#                 final_data = generate_final_data('CUSTOM_FAILED', f'A coupon code is already applied.')
#             else:
#                 final_data = generate_final_data('FAILED')
#     else:
#         # Form validation error.
#         final_data = generate_final_data('FORM_ERROR')
#         final_data['errors'] = populate_errors(validate_coupon_form.errors)
#     return final_data

@delivery_blueprint.route('/validate_coupon_code', methods=["POST"])
@authenticate('delivery_user')
def validate_coupon_code_():
    """
    API for validating the coupon code. (Compensation coupons, marketing coupons...etc)
    If the pickup request has already picked up, i.e. has a corresponding order that has an EGRN,
    coupon code calculation can also be performed.
    @return:
    """
    validate_coupon_form = ValidateCouponCodeForm()
    if validate_coupon_form.validate_on_submit():

        log_data = {
            "validate_coupon_form": validate_coupon_form.data
                    }
        info_logger(f'Route: {request.path}').info(json.dumps(log_data))
        coupon_code = validate_coupon_form.coupon_code.data
        BookingID = validate_coupon_form.BookingId.data
        branch_code = validate_coupon_form.BranchCode.data
        customer_code = validate_coupon_form.CustomerCode.data
        # Result flag
        result = None
        is_already_applied = False
        selected_coupon_details = {}
        try:
            # If the coupon code is cleared clear adhoc coupon code
            PickupTypeId = db.session.execute(
                text(
                    "SELECT PickupTypeId FROM JFSL.dbo.PickupInfo (nolock) WHERE BookingID = :BookingID"
                ),
                {"BookingID": BookingID}
            ).fetchone()
            PickupTypeId = PickupTypeId[0]
            if coupon_code == '' and PickupTypeId == 16:
                db.session.execute(
                    text("""
                        UPDATE JFSL.dbo.PickupInfo 
                        SET CouponCode = ''
                        WHERE BookingID = :BookingID
                                """),
                    {"BookingID": BookingID}
                )
                db.session.commit()
                result = {'IsValid': 1, 'Message': 'Coupon code is cleared'}
            if coupon_code == '' and PickupTypeId !=16:
                result = {'IsValid': 1, 'Message': "Coupon code is from Fabricare and it can not be cleared",
                          'Discount': 0.0, 'AppRemarks': "Coupon code is from fabricare and it can't be cleared"}
            else:
                source = 'pickup'
                egrn = None
                # Validating the discount code.
                validation = common_module.validate_coupon_code(coupon_code, customer_code,
                                                                branch_code, source,egrn )
                log_data = {
                    "validation": validation
                    }
                info_logger(f'Route: {request.path}').info(json.dumps(log_data))
                if validation:
                    # Successfully executed the SP and populated the result.
                  
                    if validation['message'] == "Valid Promocode":
                        coupon_valid = 1
                        db.session.execute(
                            text("""
                                UPDATE JFSL.dbo.PickupInfo 
                                SET CouponCode = :CouponCode
                                WHERE BookingID = :BookingID
                                            """),
                            {"BookingID": BookingID,"CouponCode":coupon_code}

                        )
                        db.session.commit()
                    else:
                        coupon_valid = 0

                    if selected_coupon_details:
                        result = {'IsValid': coupon_valid, 'Message': validation['message'],
                                  'Amount': selected_coupon_details['DISCOUNTAMOUNT']}
                    else:
                        result = {'IsValid': coupon_valid, 'Message': validation['message']}

                else:
                    # Already a DiscountCode is applied in the PickupRequest table or Orders table.
                    is_already_applied = True

        except Exception as e:
            error_logger(f'Route: {request.path}').error(e)

        if result is not None:
            final_data = generate_final_data('SUCCESS')
            final_data['result'] = result
        else:
            if is_already_applied:
                final_data = generate_final_data('CUSTOM_FAILED', f'A coupon code is already applied.')
            else:
                final_data = generate_final_data('FAILED')
    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(validate_coupon_form.errors)
    log_data = {
        "final_data": final_data
                    }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))
    return final_data

@delivery_blueprint.route('/send_otp', methods=["POST"])
# @authenticate('delivery_user')
def send_otp():
    """
    API for sending an OTP to a mobile number.
    @return:
    """
    send_otp_form = SendOTPForm()
    if send_otp_form.validate_on_submit():
        log_data = {
                'send_otp_form': send_otp_form.data,
               
            }
        info_logger(f'Route: {request.path}').info(json.dumps(log_data))

        MobileNumber = send_otp_form.mobile_number.data
        TRNNo = send_otp_form.TRNNo.data if send_otp_form.TRNNo.data != '' else None
        IsAlterNumber = send_otp_form.IsAlterNumber.data if send_otp_form.IsAlterNumber.data != '' else None
        otp_type = send_otp_form.otp_type.data
        person = send_otp_form.person.data if send_otp_form.person.data != '' else None
        # Generating an OTP (A random value from 1000 to 9999).
        otp = random.randint(1000, 9999)
        # Result flag
        send_status = False
        user_id = request.headers.get('user-id')
        sender = "FABSPA"
        branch_code = send_otp_form.branch_code.data
        brand = None

        duser_branch = db.session.query(DeliveryUserBranch.BranchCode).filter(
                DeliveryUserBranch.DUserId == user_id,DeliveryUserBranch.IsDeleted == 0).first()
            
        duser_branch = duser_branch[0]

        # for getting the delivery user brand calling this sp

        query = f"EXEC CustomerApp.[dbo].[GetBrandName] @BranchCode='{duser_branch}', @EGRNNo=NULL, @PickupRequestId=NULL"
        brand_details = CallSP(query).execute().fetchone()
        brand = brand_details["BrandDescription"]
        log_data = {
            'query of brand': query
        }
        info_logger(f'Route: {request.path}').info(json.dumps(log_data))


        if otp_type == 'DELIVERY' and branch_code:
            query = f"EXEC CustomerApp.[dbo].[GetBrandName] @BranchCode='{branch_code}', @EGRNNo=NULL, @PickupRequestId=NULL"
            brand_details = CallSP(query).execute().fetchone()
            log_data = {
                'query of brand': query,
                'result of brand': brand_details
            }
            info_logger(f'Route: {request.path}').info(json.dumps(log_data))
            if brand_details and brand_details["BrandDescription"] == 'QUICLO':
                sender="QUICLO"
                #otp_message =  f" Delivery confirmation code {otp} from Quiclo.Thank you for choosing us. For help call us 08068322433"
                otp_message = f" Delivery confirmation code {otp} from Quiclo. Thank you for choosing us. For help call us 08068322433"

            else:
                otp_message = f"Delivery confirmation code {otp} from fabricspa. Thank you for choosing us. For help call us 18001234664."
                # otp_message = f"Delivery confirmation code {otp} from fabricspa." \
                #           "Thank you for choosing us. For help call us 18001234664."

        else:
            # otp_message = f"Your OTP is {otp}. Thank you for choosing Fabricspa - India's finest Dry cleaning and " \
            #               f"Laundry service. For any help please call 4664 4664. "
            # otp_message = f"Your OTP code is: {otp}. Thank you for choosing fabricspa - India's finest dry cleaning and " \
            #               f"laundry service. For any help please call 18001234664."
            if brand == 'FABRICSPA':
                sender = "FABSPA"
                otp_message = f"Your OTP code is: {otp}. Thank you for choosing fabricspa - India's finest dry cleaning and " \
                          f"laundry service. For any help please call 18001234664."
            else:
                sender = "QUICLO"
                otp_message =f"Your OTP code is: {otp}. Thank you for choosing Quiclo - The Premium Dry cleaning and " \
                         f"Laundry service. For any help please call 08068322433"

            #otp_message = f"{otp} your one time password (OTP) to Proceed on FabXpress App & it is valid only for 30 seconds."

        if CURRENT_ENV == 'development1':
            send_status = True
        else:
            log_data = {
                "otp77 ": 'otp77'
            }
            info_logger(f'Route: {request.path}').info(json.dumps(log_data))
            send = send_sms(MobileNumber, otp_message,'',sender)
            log_data = {
                "otpSend88 ": otp_message
            }
            info_logger(f'Route: {request.path}').info(json.dumps(log_data))
            if send['result'] is not None:
                if send['result']['status'] == 'OK':
                    send_status = True
                    # Saving the details into the OTP table.
                    log_data = {
                        "otpSend99 ": otp
                    }
                    info_logger(f'Route: {request.path}').info(json.dumps(log_data))
                    try:
                        new_otp = OTP(OTP=otp, MobileNumber=MobileNumber, Type=otp_type, Person=person,
                                      IsVerified=0,
                                      SMSLog=send['log_id'],
                                      RecordCreatedDate=get_current_date(),
                                      TRNNo = TRNNo ,IsAlterNumber = IsAlterNumber
                                      )
                        db.session.add(new_otp)
                        db.session.commit()
                    except Exception as e:
                        error_logger(f'Route: {request.path}').error(e)

        if send_status:
            # Successfully sent the OTP.
            final_data = generate_final_data('SUCCESS')
        else:
            # Failed to send the OTP.
            final_data = generate_final_data('FAILED')

    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(send_otp_form.errors)
    log_data = {
                
                'final_data': final_data
            }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))

    return final_data


# @delivery_blueprint.route('verify_otp_lastold', methods=["POST"])
# @authenticate('delivery_user')
# def verify_otp_lastold():
#     """
#     API for verifying the OTP.
#     @return:
#     """
#     verify_otp_form = VerifyOTPForm()
#     if verify_otp_form.validate_on_submit():
#         mobile_number = verify_otp_form.mobile_number.data
#         otp = verify_otp_form.otp.data
#         # Result flag.
#         verified = False
#         error_msg = ''

#         # Checking the current environment, if the env is development, no need to verify OTP.
#         if CURRENT_ENV == 'development':
#             verified = True
#         else:
#             otp_details = db.session.query(OTP).filter(OTP.MobileNumber == mobile_number
#                                                        ).order_by(
#                 OTP.RecordCreatedDate.desc()).first()
#             if otp_details is not None:
#                 if otp == otp_details.OTP:
#                     now = datetime.strptime(get_current_date(), "%Y-%m-%d %H:%M:%S")
#                     seconds = abs((now - otp_details.RecordCreatedDate)).seconds
#                     # The difference between the OTP created date and current date must be
#                     # less than 1000 seconds.
#                     if seconds < 1000:
#                         # Mark this OTP log as verified.
#                         otp_details.IsVerified = 1
#                         db.session.commit()
#                         verified = True
#                     else:
#                         # OTP created more than 3 minutes ago.
#                         error_msg = 'This OTP has been expired.'
#                 else:
#                     # Another non verified OTP record has been found.
#                     error_msg = 'This OTP has been expired.'
#             else:
#                 # OTP record has not found in the DB.
#                 error_msg = 'Invalid OTP.'
#         if verified:
#             final_data = generate_final_data('SUCCESS')
#         else:
#             # OTP is not verified. Return the failed message.
#             final_data = generate_final_data('CUSTOM_FAILED', f'Failed to verify. {error_msg}')

#     else:
#         # Form validation error.
#         final_data = generate_final_data('FORM_ERROR')
#         final_data['errors'] = populate_errors(verify_otp_form.errors)

#     return final_data

@delivery_blueprint.route('verify_otp', methods=["POST"])
#@authenticate('delivery_user')
def verify_otp():
    """
    API for verifying the OTP.
    @return:
    """
    verify_otp_form = VerifyOTPForm()
    if verify_otp_form.validate_on_submit():
        mobile_number = verify_otp_form.mobile_number.data
        otp = verify_otp_form.otp.data
        otp_verify = verify_otp_form.otp_verify.data
        # Result flag.
        verified = False
        error_msg = ''
        IsOtpVerified = False

        log_data = {
            "verify_otp_form ": verify_otp_form.data
        }
        info_logger(f'Route: {request.path}').info(json.dumps(log_data))

        # Checking the current environment, if the env is development, no need to verify OTP.
        if CURRENT_ENV == 'development':
            verified = True
        else:
            otp_details = db.session.query(OTP).filter(OTP.MobileNumber == mobile_number
                                                       ).order_by(
                OTP.RecordCreatedDate.desc()).first()
            if otp_details is not None:
                if otp == otp_details.OTP:
                    now = datetime.strptime(get_current_date(), "%Y-%m-%d %H:%M:%S")
                    seconds = abs((now - otp_details.RecordCreatedDate)).seconds
                    # The difference between the OTP created date and current date must be
                    # less than 1000 seconds.
                    if seconds < 300:
                        # Mark this OTP log as verified.
                        otp_details.IsVerified = 1
                        db.session.commit()
                        verified = True
                    else:
                        # OTP created more than 3 minutes ago.
                        error_msg = 'This OTP has been expired.'
                else:
                    # Another non verified OTP record has been found.
                    error_msg = 'Invalid OTP .'
            else:
                # OTP record has not found in the DB.
                error_msg = 'Invalid OTP.'
        if verified and otp_verify:
            customercode = db.session.execute(
                text(
                    "SELECT CustomerCode  FROM JFSL.dbo.CustomerInfo (nolock) WHERE ContactNo = :mobile_number"),
                {"mobile_number": mobile_number}
            ).fetchone()
            customercode = customercode[0]
         
            IsOtpVerified = True
            query = f"Exec CustomerApp..SPCoustomerOTPVarified @MobileNumber = '{mobile_number}' , @CustomerCode = '{customercode}' , @IsOtpVerified = '{IsOtpVerified}'"
            result = CallSP(query).execute().fetchone()
            db.session.commit()
            log_data = {
                'query': query
            }
            info_logger(f'Route: {request.path}').info(json.dumps(log_data))
            log_data = {
                'query2': result
            }

            info_logger(f'Route: {request.path}').info(json.dumps(log_data))
        if verified:
            final_data = generate_final_data('SUCCESS')
        else:
            # OTP is not verified. Return the failed message.
            final_data = generate_final_data('CUSTOM_FAILED', f'Failed to verify. {error_msg}')

    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(verify_otp_form.errors)

    return final_data



# @delivery_blueprint.route('/check_customer_lastold', methods=["POST"])
# # @authenticate('delivery_user')
# def check_customer_lastold():
#     """
#     API for checking whether the customer is already registered or not.
#     @return:
#     """
#     check_customer_form = CheckCustomerForm()
#     if check_customer_form.validate_on_submit():
#         mobile_number = check_customer_form.mobile_number.data
#         branch_code = check_customer_form.branch_code.data
#         user_id = request.headers.get('user-id')
#         # Result flag.
#         is_existing = False
#         customer_details = None
#         is_customer_code_on_local = False
#         customer_address_details = []

#         # Edited By MMM
#         # if db.session.query(DeliveryUser, Branch).filter(DeliveryUser.IsActive == 1, DeliveryUser.DUserId == user_id,
#         #                                                  Branch.BranchCode == branch_code,
#         #                                                  Branch.IsActive == 1).one_or_none():

#         if db.session.query(DeliveryUser).filter(DeliveryUser.IsActive == 1, DeliveryUser.DUserId == user_id,
#                                                  DeliveryUser.IsDeleted == 0).one_or_none():
#             # log_data = {
#             #     "customer_address_details_query ":'Success2'  
#             # }  
#             # info_logger(f'Route: {request.path}').info(json.dumps(log_data))

#             customer_dtls = db.session.query(Customer).filter(
#                 or_(Customer.MobileNo == mobile_number, Customer.AlternateNo == mobile_number),
#                 Customer.IsActive == 1, Customer.IsDeleted == 0
#             ).one_or_none()

#             if customer_dtls is not None:
#                 customer_id = customer_dtls.CustomerId

#                 if customer_dtls.CustomerCode is None:
#                     query = f"EXEC {LOCAL_DB}..USP_Adhoc_PickUp_Customer_Registration @MobileNo='{customer_dtls.MobileNo}', @userId={customer_id}"
#                     result = CallSP(query).execute().fetchone()
#                     log_data = {
#                         "customer_code ": query,
#                         "customer_code_result ": result,

#                     }
#                     info_logger(f'Route: {request.path}').info(json.dumps(log_data))
#                     # customer_dtls.CustomerCode = result.CustomerCode
#                     customer_dtls.CustomerCode = result['CustomerCode']
#                     db.session.commit()
#             else:
#                 pass

#             customer_details_query = db.session.query(Customer.CustomerId, Customer.CustomerCode, Customer.MobileNo,
#                                                       Customer.EmailId, Customer.BranchCode, Customer.CustomerName,
#                                                       Customer.Gender)

#             customer_address_details_query = db.session.query(CustomerAddres.CustAddressId, CustomerAddres.AddressLine1,
#                                                               CustomerAddres.AddressLine2, CustomerAddres.AddressLine3,
#                                                               CustomerAddres.AreaCode,
#                                                               CustomerAddres.CityCode, CustomerAddres.Pincode,
#                                                               CustomerAddres.AddressName, CustomerAddres.Lat,
#                                                               CustomerAddres.Long)

#             # log_data = {
#             #                 "customer_address_details_query ":customer_address_details_query  
#             #             }  

#             # info_logger(f'Route: {request.path}').info(json.dumps(log_data))
#             try:
#                 # Checking whether the user registered with CustomerApp DB or not.
#                 customer_details = customer_details_query.filter(
#                     or_(Customer.MobileNo == mobile_number, Customer.AlternateNo == mobile_number),
#                     Customer.IsActive == 1, Customer.IsDeleted == 0).one_or_none()

#                 log_data = {
#                     "customer_address_details_query ": 'Success'
#                 }
#                 info_logger(f'Route: {request.path}').info(json.dumps(log_data))

#                 if customer_details is not None:
#                     # Getting the address details.
#                     customer_address_details = customer_address_details_query.join(
#                         Customer,
#                         CustomerAddres.CustomerId == Customer.CustomerId).filter(
#                         CustomerAddres.CustomerId == customer_details.CustomerId, CustomerAddres.IsActive == 1,
#                         CustomerAddres.IsDeleted == 0).order_by(
#                         CustomerAddres.AddressName.asc()).all()
#                 if customer_details is None:
#                     # No customer has been found. Check for the POS if the customer data exists or not.
#                     try:
#                         query = f"EXEC {SERVER_DB}.dbo.GetCustomerDetails @mobileNo='{mobile_number}'"
#                         customer_details_in_pos = CallSP(query).execute().fetchone()
#                         # log_data = {
#                         #     "Customer_address": query,
#                         #     "customer_details_in_pos":customer_details_in_pos
#                         # }       
#                         # info_logger(f'Route: {request.path}').info(json.dumps(log_data))
#                         if customer_details_in_pos:
#                             if customer_details_in_pos['Status'] == 'Existing':
#                                 # Edited by MMM
#                                 customer_code = customer_details_in_pos['CustomerCode']
#                                 if db.session.query(Customer).filter(Customer.CustomerCode == customer_code,
#                                                                      Customer.IsActive == 1).distinct(
#                                     Customer.CustomerCode).one_or_none():
#                                     # Checking whether the user registered with CustomerApp DB or not.
#                                     customer_details = customer_details_query.filter(
#                                         Customer.CustomerCode == customer_code,

#                                         Customer.IsActive == 1).one_or_none()
#                                     alternate_customer_no = db.session.query(Customer).filter(
#                                         Customer.CustomerCode == customer_code,
#                                         Customer.IsActive == 1).one_or_none()
#                                     alternate_customer_no.AlternateNo = customer_details_in_pos['Alternateno']
#                                     db.session.commit()

#                                     # Getting the address details.
#                                     customer_address_details = customer_address_details_query.join(
#                                         Customer,
#                                         CustomerAddres.CustomerId == Customer.CustomerId).filter(
#                                         Customer.CustomerCode == customer_code,
#                                         CustomerAddres.IsActive == 1, CustomerAddres.IsDeleted == 0).order_by(
#                                         CustomerAddres.AddressName.asc()).all()
#                                     is_customer_code_on_local = True
#                                 else:
#                                     # Customer exists in the POS DB and not CustomerApp DB.
#                                     customer_details = {"CustomerCode": customer_details_in_pos['CustomerCode'],
#                                                         "BranchCode": customer_details_in_pos['BranchCode'],
#                                                         "EmailId": customer_details_in_pos['Email'],
#                                                         "MobileNo": customer_details_in_pos['ContactNo'],
#                                                         "CustomerName": customer_details_in_pos['CustomerName'],
#                                                         "Gender": customer_details_in_pos['Gender'][0], "From": "POS"}

#                                     # Populating the address fields.
#                                     permanent_address = customer_details_in_pos['PermenentAddress']
#                                     permanent_address = permanent_address.replace(" ", "")
#                                     if permanent_address == '':
#                                         if customer_details_in_pos['lat1'] is not None:
#                                             Lat = float(customer_details_in_pos['lat1'])
#                                             Long = float(customer_details_in_pos['long1'])
#                                         else:
#                                             Lat = customer_details_in_pos['lat1']
#                                             Long = customer_details_in_pos['long1']
#                                         customer_address_details = [
#                                             {"AddressLine1": customer_details_in_pos['DeliveryAddress'],
#                                              "AddressLine2": "NA", "AddressLine3": "NA",
#                                              "AreaCode": customer_details_in_pos['DeliveryAreaCode'],
#                                              "Pincode": customer_details_in_pos['DeliveryPinCode'],
#                                              "CityCode": customer_details_in_pos['DeliveryCityCode'],
#                                              "Lat": Lat,
#                                              "Long": Long,
#                                              "CustAddressId": 0,
#                                              "AddressType": "DeliveryAddress"}]
#                                     else:
#                                         if customer_details_in_pos['lat1'] is not None:
#                                             Lat = float(customer_details_in_pos['lat1'])
#                                             Long = float(customer_details_in_pos['long1'])
#                                         else:
#                                             Lat = customer_details_in_pos['lat1']
#                                             Long = customer_details_in_pos['long1']
#                                         if customer_details_in_pos['lat2'] is not None:
#                                             Lat2 = float(customer_details_in_pos['lat2'])
#                                             Long2 = float(customer_details_in_pos['long2'])
#                                         else:
#                                             Lat2 = customer_details_in_pos['lat2']
#                                             Long2 = customer_details_in_pos['long2']
#                                         customer_address_details = [
#                                             {"AddressLine1": customer_details_in_pos['DeliveryAddress'],
#                                              "AddressLine2": "NA", "AddressLine3": "NA",
#                                              "AreaCode": customer_details_in_pos['DeliveryAreaCode'],
#                                              "Pincode": customer_details_in_pos['DeliveryPinCode'],
#                                              "Lat": Lat,
#                                              "Long": Long,
#                                              "CityCode": customer_details_in_pos['DeliveryCityCode'],
#                                              "CustAddressId": 0,
#                                              "AddressType": "DeliveryAddress"},
#                                             {"AddressLine1": customer_details_in_pos['PermenentAddress'],
#                                              "AddressLine2": "NA", "AddressLine3": "NA",
#                                              "AreaCode": customer_details_in_pos['PermenentAreaCode'],
#                                              "Pincode": customer_details_in_pos['PermenentPinCode'],
#                                              "Lat": Lat2,
#                                              "Long": Long2,
#                                              "CityCode": customer_details_in_pos['PermenentCityCode'],
#                                              "CustAddressId": 0,
#                                              "AddressType": "PermenentAddress"}
#                                         ]
#                                     is_existing = True
#                     except Exception as e:
#                         error_logger(f'Route: {request.path}').error(e)
#                 else:
#                     is_existing = True
#                 if is_existing or is_customer_code_on_local:
#                     customer_details = SerializeSQLAResult(customer_details).serialize_one()
#                     customer_details['From'] = 'LOCAL'
#                     customer_address_details = SerializeSQLAResult(customer_address_details).serialize()
#             except Exception as e:
#                 error_logger(f'Route: {request.path}').error(e)

#             if is_existing or is_customer_code_on_local:
#                 result = {'CustomerDetails': customer_details, 'AddressDetails': customer_address_details}
#                 final_data = generate_final_data('DATA_FOUND')
#                 final_data['result'] = result
#             else:
#                 final_data = generate_final_data('DATA_NOT_FOUND')
#         else:
#             final_data = generate_final_data('CUSTOM_FAILED', 'Inactive Store or user')

#     else:
#         # Form validation error.
#         final_data = generate_final_data('FORM_ERROR')
#         final_data['errors'] = populate_errors(check_customer_form.errors)

#     return final_data


@delivery_blueprint.route('/check_customer', methods=["POST"])
# @authenticate('delivery_user')
def check_customer():
    """
    API for checking whether the customer is already registered or not.
    @return:
    """
    check_customer_form = CheckCustomerForm()
    if check_customer_form.validate_on_submit():
        mobile_number = check_customer_form.mobile_number.data
        branch_code = check_customer_form.branch_code.data
        user_id = request.headers.get('user-id')
        customer_details1 = None
        AddressDetails = None
        result = None
        log_data = {
            
            'check_customer_form': check_customer_form.data
        }
        info_logger(f'Route: {request.path}').info(json.dumps(log_data))
        query = f"EXEC JFSL.Dbo.SPGetCustomerDetailsCustApp @ContactNo = '{mobile_number}',@ActionType='{1}'"
        
        customer_details = CallSP(query).execute().fetchall()
        log_data = {
            
            'customer_details': customer_details
        }
        info_logger(f'Route: {request.path}').info(json.dumps(log_data))
        if customer_details:
            customer_details1 = customer_details[0]
        query = f"""EXEC JFSL.Dbo.SPGetCustomerDetailsCustApp  @ContactNo ={mobile_number}"""
        
        AddressDetails = CallSP(query).execute().fetchall()
        # for address in AddressDetails:
        #     address["PinCode"] = str(address['PinCode'])
        for i, address in enumerate(AddressDetails):
            address = dict(address)  # Ensure it's a dictionary (if not already)

            # Convert PinCode to string
            address["PinCode"] = str(address.get('PinCode', ''))

            # Convert Lat and Long to float safely
            try:
                lat = float(address.get('Lat', 0.0))
            except (TypeError, ValueError):
                lat = 0.0

            try:
                long = float(address.get('Long', 0.0))
            except (TypeError, ValueError):
                long = 0.0

            # Set None if lat/long is not valid
            address['Lat'] = lat if lat > 0.0 else None
            address['Long'] = long if long > 0.0 else None

            AddressDetails[i] = address
        if len(AddressDetails) == 1:
            AddressDetails[0]["CustAddressId"] = 0
        log_data = {
            
            'AddressDetails': AddressDetails
        }
        info_logger(f'Route: {request.path}').info(json.dumps(log_data))

        if customer_details1 is not None:

            result = {'CustomerDetails': customer_details1,"AddressDetails":AddressDetails}

        if result:
            final_data = generate_final_data('DATA_FOUND')
            final_data['result'] = result
        # final_data['is_verified'] = customer_details_in_pos["IsOTPVerified"]
        else:
            final_data = generate_final_data('DATA_NOT_FOUND')
    else:
    # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(check_customer_form.errors)
    log_data = {
            
            'final_data': final_data
        }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))
    return final_data

@delivery_blueprint.route('/save_customer', methods=["POST"])
# @authenticate('delivery_user')
def save_customer():
    save_customer_form = SaveCustomerForm()
    # Removed duplicate initialization

    if save_customer_form.validate_on_submit():
        log_data = {
                    'save_customer_form:': save_customer_form.data,
                
                }
        info_logger(f'Route: {request.path}').info(json.dumps(log_data))
        MobileNumber = save_customer_form.mobile_number.data
        CustomerName = save_customer_form.customer_name.data
        Email = save_customer_form.email.data
        Gender = save_customer_form.gender.data
        DeliveryUserBranchCode = save_customer_form.delivery_user_branch_code.data
        AddressDetails = save_customer_form.address_details.data
        AddressDetails = AddressDetails[0]
        Saved = False
        CustomerCode = None

        try:
            # Check if mobile number already exists
            result = db.session.execute(
                text("SELECT CustomerCode FROM JFSL.dbo.CustomerInfo (nolock) "
                     "WHERE ContactNo = :MobileNumber"),
                {"MobileNumber": MobileNumber}
            ).fetchone()

            if result:
                CustomerCode = result[0]
                Saved = False
                final_data = generate_final_data('EMAIL_EXIST')
                final_data["message"] = f"Mobile Number already Exists"
                return final_data  
            log_data = {
                    'CustomerCode1:': CustomerCode,
                
                }
            info_logger(f'Route: {request.path}').info(json.dumps(log_data))

            # Check email only if mobile not found
            if Email and Email.strip():
                log_data = {
                    'Email:': Email,
                
                }
                info_logger(f'Route: {request.path}').info(json.dumps(log_data))
                CustomerCode = db.session.execute(
                    text(
                        "SELECT CustomerCode FROM JFSL.dbo.CustomerInfo (nolock) "
                        "WHERE EmailID1 = :Email OR EmailID2 = :Email"
                    ),
                    {"Email": Email}
                ).fetchone()

                if CustomerCode:
                    CustomerCode = CustomerCode[0]
                else:
                    CustomerCode = None

                log_data = {'CustomerCode:': CustomerCode}
                info_logger(f'Route: {request.path}').info(json.dumps(log_data))
            log_data = {
                    'CustomerCode:': CustomerCode,
                
                }
            info_logger(f'Route: {request.path}').info(json.dumps(log_data))

            if CustomerCode is None:
                # Insert new customer record
                Email_sql = 'NULL' if not Email or Email.strip() == '' else f"'{Email}'"

                query = f""" 
                    EXEC JFSL.Dbo.SPCustomerInfoInsertCustApp 
                    @mobile_number ='{MobileNumber}',
                    @customer_name ='{CustomerName}',
                    @email ={Email_sql},      
                    @gender ='{Gender}', 
                    @delivery_user_branch_code ='{DeliveryUserBranchCode}', 
                    @DeliveryAddress ='{AddressDetails.get('address_line_2')}',
                    @PermanantAddress = NULL,  
                    @lat ='{AddressDetails.get('lat')}',
                    @long ='{AddressDetails.get('long')}',
                    @geolocation ='{AddressDetails.get('geolocation')}',
                    @Pincode ='{AddressDetails.get('Pincode')}',
                    @DOB = NULL,
                    @flatno1 = '{AddressDetails.get('address_line_1')}',
                    @flatno2 = NULL, 
                    @IsWhatsAppSubscribed = NULL
                """

                log_data = {'query:': query}
                info_logger(f'Route: {request.path}').info(json.dumps(log_data))
                db.engine.execute(text(query).execution_options(autocommit=True))
                Saved = True

        except Exception as e:
            error_logger(f'Route: {request.path}').error(e)

        print(Saved)

        if Saved:
            CustomerCode = db.session.execute(
                text(
                    "SELECT CustomerCode  FROM JFSL.dbo.CustomerInfo (nolock) "
                    "WHERE ContactNo = :MobileNumber"
                ),
                {"MobileNumber": MobileNumber}
            ).fetchone()
            CustomerCode = CustomerCode[0]

            query = f"""EXEC JFSL.Dbo.SPCustomerInfoInsertSMSCustApp 
                        @NewCutomerCode = '{CustomerCode}'"""
            print(query)
            db.engine.execute(text(query).execution_options(autocommit=True))

            final_data = generate_final_data('DATA_SAVED')
            final_data['result'] = {
                'CustomerCode': CustomerCode,
                'MobileNumber': MobileNumber
            }
            print(final_data)

        if not Saved:
            final_data = generate_final_data('EMAIL_EXIST')
            final_data["message"] = f" The Email ID is already linked to this Customer ID {CustomerCode}."

    else:
        # Form validation error
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(save_customer_form.errors)
    log_data = {'final_data:': final_data}
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))

    return final_data



# @delivery_blueprint.route('/add_address', methods=["POST"])
# @authenticate('delivery_user')
# def add_address():
#     """
#     API for adding an address.
#     @return:
#     """
#     add_address_form = AddAddressForm()
#     if add_address_form.validate_on_submit():
#         customer_id = add_address_form.customer_id.data
#         address_line_1 = add_address_form.address_line_1.data
#         address_line_2 = add_address_form.address_line_2.data if add_address_form.address_line_2.data != '' else None
#         address_line_3 = add_address_form.address_line_3.data if add_address_form.address_line_3.data != '' else None
#         landmark = add_address_form.landmark.data if add_address_form.landmark.data != '' else None
#         delivery_user_branch_code = add_address_form.delivery_user_branch_code.data
#         lat = add_address_form.lat.data
#         long = add_address_form.long.data
        # log_data = {
        #     'lat frontEnd :': lat,
        #     'long frontEnd :': long
        # }
        # info_logger(f'Route: {request.path}').info(json.dumps(log_data))

#         geo_location = add_address_form.geo_location.data if add_address_form.geo_location.data != '' else None
#         pincode = add_address_form.pincode.data if add_address_form.pincode.data != '' else None
#         is_added = False
#         error_msg = None
#         try:
#             count = db.session.query(func.count(CustomerAddres.CustomerId)).filter(
#                 CustomerAddres.CustomerId == customer_id, CustomerAddres.IsDeleted == 0).scalar()
#             address_name = f'Address {count + 1}'
#             # Getting the essential details from the DB.
#             essential_details = delivery_controller_queries.get_essential_details_from_dbranchcode(
#                 delivery_user_branch_code)
#             if pincode is None:
#                 pincode = essential_details.Pincode
#             customer_code = db.session.query(Customer.CustomerCode).filter(
#                 Customer.CustomerId == customer_id).one_or_none()
#             if count < 2:
#                 if essential_details is not None:
#                     log_data = {
#                         'lat to table :': lat,
#                         'long to table :': long
#                     }
#                     info_logger(f'Route: {request.path}').info(json.dumps(log_data))
#                     # Adding the address into the table.
#                     new_customer_address = CustomerAddres(
#                         CustomerId=customer_id,
#                         AddressName=address_name,
#                         AddressLine1=address_line_1,
#                         AddressLine2=address_line_2,
#                         AddressLine3=address_line_3,
#                         Landmark=landmark,
#                         Pincode=pincode,
#                         AreaCode=essential_details.AreaCode,
#                         CityCode=essential_details.CityCode,
#                         Lat=lat,
#                         Long=long,
#                         IsActive=1,
#                         RecordCreatedDate=get_current_date(),
#                         RecordLastUpdatedDate=get_current_date(),
#                         GeoLocation=geo_location
#                     )

#                     try:
#                         db.session.add(new_customer_address)
#                         db.session.commit()
#                         # Successfully addded the address.
#                         is_added = True
#                     except Exception as e:
#                         error_logger(f'Route: {request.path}').error(e)
#                     # query = f"EXEC {SERVER_DB}.dbo.UPDATEFABRICARECUSTOMERDATAFromFabexpress " \
#                     #         f"@CUSTOMERCODE='{customer_code.CustomerCode}',@AddressLines1='{address_line_1},{address_line_2},{address_line_3}', " \
#                     #         f"@CityCode1='{essential_details.CityCode}',@AreaCode1={essential_details.AreaCode}, " \
#                     #         f"@pincode1={essential_details.Pincode}," \
#                     #         f"@AddressLines2=NULL,@CityCode2=NULL," \
#                     #         f"@AreaCode2=NULL, @pincode2 = NULL, " \
#                     #         f"@IsAddress2Deleted =NULL "
#                     # db.engine.execute(text(query).execution_options(autocommit=True))
#                     if address_name == 'Address 1':
#                         query = f"EXEC {SERVER_DB}.dbo.UPDATEFABRICARECUSTOMERDATA @CUSTOMERCODE='{customer_code.CustomerCode}',@DOB='',@EMAIL='',@PROFESSION='',@GENDER='',@flatno1='{address_line_1}',@AddressLines1='{address_line_2} {address_line_3}',@CityCode1='{essential_details.CityCode}',@AreaCode1='{essential_details.AreaCode}',@flatno2= NULL,@AddressLines2='',@CityCode2='',@AreaCode2='',@IsAddress2Deleted=0,@lat1 ='{lat}',@long1 ='{long}',@lat2 ='',@long2 ='',@GeoLocality1 ='{geo_location}',@GeoLocality2 =NULL, @geoPinCode1={pincode}, @geoPinCode2=NULL, @ActiveBranch={delivery_user_branch_code}"
#                         update_address = f"EXEC {SERVER_DB}.dbo.UpdateCustomerAppAddress @CUSTOMERCODE='{customer_code.CustomerCode}',@DOB='',@EMAIL='',@PROFESSION='',@GENDER='',@AddressLines1='{address_line_2} {address_line_3}',@CityCode1='{essential_details.CityCode}',@AreaCode1='{essential_details.AreaCode}',@AddressLines2='',@CityCode2='',@AreaCode2='',@IsAddress2Deleted=0 ,@addressname = 'Address 1',@lat1 ='{lat}',@long1 ='{long}',@lat2 ='',@long2 =''," \
#                                          f"@geolocality1='{geo_location}',@geolocality2=NULL,@addresslineforAdd1='{address_line_1}'," \
#                                          f"@addresslineforAdd2 = NULL, @geoPinCode1={pincode}, @geoPinCode2=NULL"
#                     else:
#                         query = f"EXEC {SERVER_DB}.dbo.UPDATEFABRICARECUSTOMERDATA @CUSTOMERCODE='{customer_code.CustomerCode}',@DOB='',@EMAIL='',@PROFESSION='',@GENDER='',@flatno1=NULL,@AddressLines1='',@CityCode1='',@AreaCode1='',@flatno2='{address_line_1}',@AddressLines2='{address_line_2} {address_line_3}',@CityCode2='{essential_details.CityCode}',@AreaCode2='{essential_details.AreaCode}',@IsAddress2Deleted=0,@lat1 ='',@long1 ='',@lat2 ='{lat}',@long2 ='{long}',@GeoLocality1 = NULL,@GeoLocality2 ='{geo_location}', @geoPinCode1=NULL, @geoPinCode2={pincode}, @ActiveBranch={delivery_user_branch_code}"
#                         update_address = f"EXEC {SERVER_DB}.dbo.UpdateCustomerAppAddress @CUSTOMERCODE='{customer_code.CustomerCode}',@DOB='',@EMAIL='',@PROFESSION='',@GENDER='',@AddressLines1='',@CityCode1='',@AreaCode1='',@AddressLines2='{address_line_2} {address_line_3}',@CityCode2='{essential_details.CityCode}',@AreaCode2='{essential_details.AreaCode}',@IsAddress2Deleted=0 ,@addressname = 'Address 2',@lat1 ='',@long1 ='',@lat2 ='{lat}',@long2 ='{long}'," \
#                                          f"@geolocality1=NULL,@geolocality2= '{geo_location}',@addresslineforAdd1=NULL," \
#                                          f"@addresslineforAdd2 = '{address_line_1}', @geoPinCode1=NULL, @geoPinCode2={pincode}"

#                     update_lat_long = f"EXEC {SERVER_DB}.dbo.USP_latlonglogs @AddressName='{address_name}',@Lat={lat},@Long={long},@bookingid=NULL," \
#                                       f"@CustomerCode={customer_code.CustomerCode},@branchcode=NULL, @source " \
#                                       f"='FabExpress',  @userid={0}"
#                     db.engine.execute(text(update_lat_long).execution_options(autocommit=True))
#                     try:
#                         db.engine.execute(text(query).execution_options(autocommit=True))
#                         db.engine.execute(text(update_address).execution_options(autocommit=True))

#                         log_data = {
#                             'query Updating the delivery address in the POS :': query,
#                             'query Updating the delivery address in the webapp :': update_address,
#                             'Updating the lat and long  :': update_lat_long
#                         }
#                         info_logger(f'Route: {request.path}').info(json.dumps(log_data))
#                     except Exception as e:
#                         error_logger(f'Delivery Blueprint Queries: {inspect.stack()[0].function}()').error(e)
#             else:
#                 error_msg = 'You can only add two addresses'
#         except Exception as e:
#             error_logger(f'Route: {request.path}').error(e)

#         if is_added:
#             final_data = generate_final_data('DATA_SAVED')
#         elif error_msg is not None:
#             final_data = generate_final_data('CUSTOM_FAILED', error_msg)
#         else:
#             final_data = generate_final_data('DATA_SAVE_FAILED')
#     else:
#         # Form validation error.
#         final_data = generate_final_data('FORM_ERROR')
#         final_data['errors'] = populate_errors(add_address_form.errors)

#     return final_data

@delivery_blueprint.route('/add_address', methods=["POST"])
# @authenticate('delivery_user')
def add_address():
    """
    API for adding an address.
    @return:
    """
    add_address_form = AddAddressForm()
    log_data = {
        'add_address_form:': add_address_form.data,
                
                }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))
    if add_address_form.validate_on_submit():
        address_line_1 = clean_address_field(add_address_form.address_line_1.data)
        address_line_2 = clean_address_field(add_address_form.address_line_2.data if add_address_form.address_line_2.data != '' else '')
        address_line_3 = clean_address_field(add_address_form.address_line_3.data if add_address_form.address_line_3.data != '' else '')
        landmark = clean_address_field(add_address_form.landmark.data if add_address_form.landmark.data != '' else '')
        pincode = add_address_form.pincode.data if add_address_form.pincode.data != '' else ''
        delivery_user_branch_code = None if add_address_form.delivery_user_branch_code.data == '' else add_address_form.delivery_user_branch_code.data
        address_name = add_address_form.address_name.data
        address_type = add_address_form.address_type.data
        CustomerCode = add_address_form.CustomerCode.data
        customer_type = add_address_form.customer_type.data
        mobile_number = add_address_form.mobile_number.data
        lat = add_address_form.lat.data
        long = add_address_form.long.data
        geo_location = clean_address_field(add_address_form.geo_location.data if add_address_form.geo_location.data != '' else '')
       


        # Result flag variable
        is_added = False
       

        try:
            

            query = f""" EXEC JFSL.Dbo.[SPUpdateCustomerInfoCustApp] @CustomerCode ='{CustomerCode}',@address_line_1 = '{address_line_1}', @address_line_2 = '{address_line_2}'
                            ,@address_line_3 = '{address_line_3}' , @landmark ='{landmark}', @pincode ={pincode},@delivery_user_branch_code ='{delivery_user_branch_code}',@address_name ='{address_type}'
                            ,@mobile_number ='{mobile_number}' ,@lat  ={lat} ,@long ={long},@geo_location = '{geo_location}'"""
            
            log_data = {
                'query:': query
                
                }
            info_logger(f'Route: {request.path}').info(json.dumps(log_data))
            db.engine.execute(text(query).execution_options(autocommit=True))
            is_added = True
        except Exception as e:
            error_logger(f'Route: {request.path}').error(e)

        if is_added:
            final_data = generate_final_data('DATA_SAVED')
        
        else:
            final_data = generate_final_data('DATA_SAVE_FAILED')
    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(add_address_form.errors)
    log_data = {
        'final_data:': final_data
                
                }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))

    return final_data



# @delivery_blueprint.route('/get_coupon_codes', methods=["POST"])
# #@authenticate('delivery_user')
# def get_coupon_codes():
#     """
#     API for getting coupon codes for an EGRN.
#     @return:
#     """
#     coupon_codes_form = GetCouponCodesForm()
#     if coupon_codes_form.validate_on_submit():
#         egrn = coupon_codes_form.EGRN.data
#         result = None
#         # Getting the EGRN of the order.
#         try:

#             result = payment_module.get_available_coupon_codes(egrn)
#         except Exception as e:
#             error_logger(f'Route: {request.path}').error(e)

#         # if result is not None and len(result) > 0:
#         #     # Result is found from the SP.
#         #     final_data = generate_final_data('DATA_FOUND')
#         #     final_data['result'] = result
#         if result:
#             final_data = generate_final_data('DATA_FOUND')
#             final_data['result'] = list(result) if not isinstance(result, list) else result
#         else:
#             final_data = generate_final_data('DATA_NOT_FOUND')
#     else:
#         # Form validation error.
#         final_data = generate_final_data('FORM_ERROR')
#         final_data['errors'] = populate_errors(coupon_codes_form.errors)
#     log_data = {
#         'final_data:': final_data
                
#                 }
#     info_logger(f'Route: {request.path}').info(json.dumps(log_data))
#     return final_data

@delivery_blueprint.route('/get_coupon_codes', methods=["POST"])
#@authenticate('delivery_user')
def get_coupon_codes():
    """
    API for getting coupon codes for an EGRN.
    @return:
    """
    coupon_codes_form = GetCouponCodesForm()
    if coupon_codes_form.validate_on_submit():
        egrn = coupon_codes_form.EGRN.data
        result = None
        # Getting the EGRN of the order.
        try:

            result = payment_module.get_available_coupon_codes(egrn)
        except Exception as e:
            error_logger(f'Route: {request.path}').error(e)

        # if result is not None and len(result) > 0:
        #     # Result is found from the SP.
        #     final_data = generate_final_data('DATA_FOUND')
        #     final_data['result'] = result
        if any(result):
            final_data = generate_final_data('DATA_FOUND')
            final_data['result'] = list(result) if not isinstance(result, list) else result
        else:
            final_data = generate_final_data('DATA_NOT_FOUND')
    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(coupon_codes_form.errors)
    log_data = {
        'final_data:': final_data
                
                }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))
    return final_data


@delivery_blueprint.route('/get_delivery_review_reasons', methods=["GET"])
@authenticate('delivery_user')
def get_delivery_review_reasons():
    """
    API for getting the predefined delivery review reasons from the DB.
    @return:
    """
    review_reasons = []
    try:
        review_reasons = db.session.execute(
            text(
                "SELECT DeliveryReviewReasonId , ReviewReason FROM JFSL.dbo.FabDeliveryReviewReasons Where IsDeleted = 0"),

        ).fetchall()
    except Exception as e:
        error_logger(f'Route: {request.path}').error(e)

    if len(review_reasons) > 0:
        final_data = generate_final_data('DATA_FOUND')
        final_data['result'] = SerializeSQLAResult(review_reasons).serialize()
    else:
        final_data = generate_final_data('DATA_NOT_FOUND')

    return final_data

@delivery_blueprint.route('/save_delivery_review', methods=["POST"])
# @authenticate('delivery_user')
def save_delivery_review():
    """
    API for saving an order review after picking up the garments.
    @return:
    """
    review_form = SaveDeliveryReviewForm()
    if review_form.validate_on_submit():
        TRNNo = review_form.TRNNo.data
        rating = review_form.rating.data
        review_reason_id = review_form.review_reason_id.data
        # Remarks will be NULL if no remarks are provided in the request.
        remarks = review_form.remarks.data if review_form.remarks.data != '' else None
        user_id = request.headers.get('user-id')
        saved = False
        is_already_delivered = False
        try:
            # Checking whether the review is already saved or not. If the review is already saved, then skip it.

            order_review = db.session.execute(
                text(
                    "SELECT * FROM JFSL.dbo.FabDeliveryReviews Where TRNNo = :TRNNo"),
                {"TRNNo": TRNNo}

            ).fetchall()
            order_review = SerializeSQLAResult(order_review).serialize()
           
            if len(order_review) == 0:
                print(order_review)
                # No existing reviews present for this order id. So save the new review to the table.

                db.session.execute(text("""
                        INSERT INTO JFSL.Dbo.FabDeliveryReviews 
                        (TRNNo, DeliveryReviewReasonId, StarRating, Remarks, DUserId,   IsDeleted,  RecordCreatedDate,  RecordLastUpdatedDate) 

                        VALUES (:TRNNo, :DeliveryReviewReasonId,    :StarRating,    :Remarks,   :DUserId,   :IsDeleted, :RecordCreatedDate, :RecordCreatedDate)
                        """), {
                    "TRNNo": TRNNo,
                    "DeliveryReviewReasonId": review_reason_id,
                    "StarRating": rating,
                    "Remarks": remarks,
                    "DUserId": user_id,
                    "IsDeleted": 0,
                    "RecordCreatedDate": get_current_date()
                })
                db.session.commit()
                saved = True

            else:
                # The order has a pickup review; which means this already has been picked up.
                is_already_delivered = True


        except Exception as e:
            db.session.rollback()
            error_logger(f'Route: {request.path}').error(e)

        if saved:
            # Review saved and marked this order as delivered.
            final_data = generate_final_data('DATA_SAVED')
        else:
            if is_already_delivered:
                # The order has already been delivered.
                final_data = generate_final_data('CUSTOM_FAILED', 'The order has already been delivered.')
            else:
                # Failed to save the review and mark this one as delivered.
                final_data = generate_final_data('DATA_NOT_SAVED')

    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(review_form.errors)
    log_data = {
            
         "final_data": final_data,
         "review_form": review_form.data
                            }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))

    return final_data


@delivery_blueprint.route('/check_order_payment_status', methods=["POST"])
# @authenticate('delivery_user')
def check_order_payment_status():
    """
    API for checking payment status of the given delivery request id.
    @return:
    """
    payment_status_form = CheckOrderPaymentStatusForm()
    if payment_status_form.validate_on_submit():
        log_data = {

        "payment_status_form": payment_status_form.data
            }
        info_logger(f'Route: {request.path}').info(json.dumps(log_data))
        TRNNo = payment_status_form.TRNNo.data
        EGRN = payment_status_form.EGRN.data
        payment_status = 'NA'
        user_id = request.headers.get('user_id')
        QrId = '' if payment_status_form.QrId.data == '' else payment_status_form.QrId.data
        try:
            if QrId != '':

                api_url = f'https://api.razorpay.com/v1/payments/qr_codes/{QrId}'
              

                auth = (
                    os.getenv('RazorPayLiveUserName'),
                    os.getenv('RazorPayLivePassword')
                )

                headers = {
                    'Content-Type': 'application/json'
                }

                
                response = requests.get(api_url, headers=headers, auth=auth)
                response.raise_for_status()
                response_data = response.json()
                log_data = {
                            "response_data":response_data
                            
                                }
                info_logger(f'Route: {request.path}').info(json.dumps(log_data))

                if response_data.get('payment_amount') == response_data.get('payments_amount_received'):

                    final_data = generate_final_data('DATA_FOUND')
                    result = {'PaymentStatus': 'Paid'}
                    final_data['result'] = result
                else:
                    final_data = generate_final_data('DATA_NOT_FOUND')
            else:


                 # Getting the payment status.
                payment_status = payment_module.get_garments_payment_status(EGRN, TRNNo)

                if payment_status['Status'] == 'Unpaid':
                    payment_status['Status'] = 'Delivered Unpaid'

                if payment_status['Status'] == 'Fully Paid' or payment_status['Status'] =="Partially paid":
                    log_data = {
                            'payment_status': payment_status['Status'],
                            "payment_status_form":payment_status_form.data
                                }
                    info_logger(f'Route: {request.path}').info(json.dumps(log_data))

                    payment_dtls = db.session.query(TransactionInfo).filter(
                        TransactionInfo.DCNo == TRNNo,
                        TransactionInfo.PaymentSource == 'PaymentLink').one_or_none()
                    if payment_dtls:
                        payment_dtls.PaymentCollectedBY = user_id
                        payment_dtls.PaymentCompletedOn = get_current_date()
                        db.session.commit()
                        cust_details = db.session.execute(
                            text("SELECT CustomerCode FROM JFSL.dbo.FabDeliveryInfo WHERE TRNNo = :TRNNo"),
                            {"TRNNo": TRNNo}
                        ).fetchone()

                        log_data = {
                            'sms_check': 'test',

                        }
                        info_logger(f'Route: {request.path}').info(json.dumps(log_data))

                        if cust_details:
                            log_data = {
                                'customer_detail_keys': list(cust_details.keys())
                            }
                            customer_code = cust_details['CustomerCode']  # or cust_details.CustomerCode
                        else:
                            log_data = {
                                'customer_detail_keys': 'No result returned'
                            }
                            customer_code = None

                        # Fetch payment details
                        payment_details = db.session.query(TransactionInfo).filter(
                            TransactionInfo.DCNo == TRNNo,
                            TransactionInfo.PaymentFrom.in_(['Billdesk', 'Fabricspa'])
                        ).order_by(TransactionInfo.TransactionDate.desc()).first()

                        if payment_details:

                            # Fetch transaction ID and payment ID
                            transaction_id_result = db.session.query(
                                TransactionInfo.TransactionId).filter(
                                TransactionInfo.DCNo == TRNNo
                            ).order_by(TransactionInfo.TransactionDate.desc()).first()

                            payment_id_result = db.session.query(TransactionInfo.PaymentId).filter(
                                TransactionInfo.DCNo == TRNNo
                            ).order_by(TransactionInfo.TransactionDate.desc()).first()

                            transaction_id = transaction_id_result[
                                0] if transaction_id_result else None
                            payment_id = payment_id_result[0] if payment_id_result else None

                            if transaction_id is not None and payment_id is not None:
                                amount = db.session.query(TransactionPaymentInfo.PaymentAmount).filter(
                                    TransactionPaymentInfo.TransactionId == transaction_id).order_by(
                                    TransactionPaymentInfo.CreatedOn.desc()).first()
                                amount = amount[0]

                                # invoice_num = db.session.query(TransactionPaymentInfo.InvoiceNo).filter(
                                #     TransactionPaymentInfo.TransactionId == transaction_id).order_by(TransactionPaymentInfo.CreatedOn.desc()).first()
                                invoice_num = db.session.query(TransactionPaymentInfo.InvoiceNo).filter(
                                    and_(
                                        TransactionPaymentInfo.TransactionId == transaction_id,
                                        TransactionPaymentInfo.InvoiceNo.isnot(None)
                                    )
                                ).order_by(TransactionPaymentInfo.CreatedOn.desc()).first()

                                invoice_num = invoice_num[0]
                                try:
                                    delivery_controller_queries.send_sms_email_when_settled(
                                        customer_code, EGRN,
                                        amount,
                                        invoice_num,TRNNo)
                                except Exception as e:
                                    error_logger(f'Route: {request.path}').error(e)
                                    log_data = {
                                        'sms_Excption': 'Error :ALERT_PROCESS @ALERT_CODE = JFSL_DELIVERY_COMPLETED_FABRICSPA',
                                        'exception_message': str(e)
                                    }
                                    info_logger(f'Route: {request.path}').info(json.dumps(log_data))

            
                    result = {'PaymentStatus': payment_status['Status']}

        except Exception as e:
            error_logger(f'Route: {request.path}').error(e)

        
        final_data = generate_final_data('DATA_FOUND')
        final_data['result'] = result
    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(payment_status_form.errors)
    log_data = {
            'final_data': final_data 
                }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))
    return final_data



# @delivery_blueprint.route('/check_order_payment_status', methods=["POST"])
# # @authenticate('delivery_user')
# def check_order_payment_status():
#     """
#     API for checking payment status of the given delivery request id.
#     @return:
#     """
#     payment_status_form = CheckOrderPaymentStatusForm()
#     if payment_status_form.validate_on_submit():
#         log_data = {

#         "payment_status_form": payment_status_form.data
#             }
#         info_logger(f'Route: {request.path}').info(json.dumps(log_data))
#         TRNNo = payment_status_form.TRNNo.data
#         EGRN = payment_status_form.EGRN.data
#         payment_status = 'NA'
#         user_id = request.headers.get('user_id')
#         try:

#             # Getting the payment status.
#             payment_status = payment_module.get_garments_payment_status(EGRN, TRNNo)

#             if payment_status['Status'] == 'Unpaid':
#                 payment_status['Status'] = 'Delivered Unpaid'

#             if payment_status['Status'] == 'Fully Paid' or payment_status['Status'] =="Partially paid":
#                 log_data = {
#                         'payment_status': payment_status['Status'],
#                         "payment_status_form":payment_status_form.data
#                             }
#                 info_logger(f'Route: {request.path}').info(json.dumps(log_data))

#                 payment_dtls = db.session.query(TransactionInfo).filter(
#                     TransactionInfo.DCNo == TRNNo,
#                     TransactionInfo.PaymentSource == 'PaymentLink').one_or_none()
#                 if payment_dtls:
#                     payment_dtls.PaymentCollectedBY = user_id
#                     payment_dtls.PaymentCompletedOn = get_current_date()
#                     db.session.commit()
#                     cust_details = db.session.execute(
#                         text("SELECT CustomerCode FROM JFSL.dbo.FabDeliveryInfo WHERE TRNNo = :TRNNo"),
#                         {"TRNNo": TRNNo}
#                     ).fetchone()

#                     log_data = {
#                         'sms_check': 'test',

#                     }
#                     info_logger(f'Route: {request.path}').info(json.dumps(log_data))

#                     if cust_details:
#                         log_data = {
#                             'customer_detail_keys': list(cust_details.keys())
#                         }
#                         customer_code = cust_details['CustomerCode']  # or cust_details.CustomerCode
#                     else:
#                         log_data = {
#                             'customer_detail_keys': 'No result returned'
#                         }
#                         customer_code = None

#                     # Fetch payment details
#                     payment_details = db.session.query(TransactionInfo).filter(
#                         TransactionInfo.DCNo == TRNNo,
#                         TransactionInfo.PaymentFrom.in_(['Billdesk', 'Fabricspa'])
#                     ).order_by(TransactionInfo.TransactionDate.desc()).first()

#                     if payment_details:

#                         # Fetch transaction ID and payment ID
#                         transaction_id_result = db.session.query(
#                             TransactionInfo.TransactionId).filter(
#                             TransactionInfo.DCNo == TRNNo
#                         ).order_by(TransactionInfo.TransactionDate.desc()).first()

#                         payment_id_result = db.session.query(TransactionInfo.PaymentId).filter(
#                             TransactionInfo.DCNo == TRNNo
#                         ).order_by(TransactionInfo.TransactionDate.desc()).first()

#                         transaction_id = transaction_id_result[
#                             0] if transaction_id_result else None
#                         payment_id = payment_id_result[0] if payment_id_result else None

#                         if transaction_id is not None and payment_id is not None:
#                             amount = db.session.query(TransactionPaymentInfo.PaymentAmount).filter(
#                                 TransactionPaymentInfo.TransactionId == transaction_id).order_by(
#                                 TransactionPaymentInfo.CreatedOn.desc()).first()
#                             amount = amount[0]

#                             # invoice_num = db.session.query(TransactionPaymentInfo.InvoiceNo).filter(
#                             #     TransactionPaymentInfo.TransactionId == transaction_id).order_by(TransactionPaymentInfo.CreatedOn.desc()).first()
#                             invoice_num = db.session.query(TransactionPaymentInfo.InvoiceNo).filter(
#                                 and_(
#                                     TransactionPaymentInfo.TransactionId == transaction_id,
#                                     TransactionPaymentInfo.InvoiceNo.isnot(None)
#                                 )
#                             ).order_by(TransactionPaymentInfo.CreatedOn.desc()).first()

#                             invoice_num = invoice_num[0]
#                             try:
#                                 delivery_controller_queries.send_sms_email_when_settled(
#                                     customer_code, EGRN,
#                                     amount,
#                                     invoice_num, TRNNo)
#                             except Exception as e:
#                                 error_logger(f'Route: {request.path}').error(e)
#                             log_data = {
#                                 'sms_Excption': 'Error :ALERT_PROCESS @ALERT_CODE = JFSL_DELIVERY_COMPLETED_FABRICSPA',
#                                 'exception_message': str(e)
#                             }
#                             info_logger(f'Route: {request.path}').info(json.dumps(log_data))
#             else:
#                 pass


#         except Exception as e:
#             error_logger(f'Route: {request.path}').error(e)

#         result = {'PaymentStatus': payment_status['Status']}
#         final_data = generate_final_data('DATA_FOUND')
#         final_data['result'] = result
#     else:
#         # Form validation error.
#         final_data = generate_final_data('FORM_ERROR')
#         final_data['errors'] = populate_errors(payment_status_form.errors)
#     log_data = {
#             'final_data': final_data 
#                 }
#     info_logger(f'Route: {request.path}').info(json.dumps(log_data))
#     return final_data

# @delivery_blueprint.route('/get_complaint_types', methods=["GET"])
# @authenticate('delivery_user')
# def get_complaint_types():
#     """
#     API for getting the complaint types that can be passed to the Ameyo ticketing service.
#     @return:
#     """
#     result = []
#     try:
#         # Getting the departments from the DB.
#         departments = db.session.query(ComplaintType.DeptName).distinct(ComplaintType.DeptName).filter(
#             ComplaintType.IsDeleted == 0).all()

#         for department in departments:
#             # Looping through the departments.
#             dep = {'Department': department.DeptName, 'ComplaintTypes': []}
#             result.append(dep)

#         # Looping through the result dict variable, find the complaint types that belongs to the dict.
#         for department in result:
#             # Department name
#             dept_name = department['Department']
#             try:
#                 # Fetching all the complaint types related to this department.
#                 complaint_types = db.session.query(ComplaintType.ComplaintTypeName).filter(
#                     ComplaintType.DeptName == dept_name, ComplaintType.IsDeleted == 0).all()

#                 department_complaint_types = []

#                 # Looping through the complaint types and append them into the department_complaint_types variable.
#                 for complaint_type in complaint_types:
#                     department_complaint_types.append(complaint_type.ComplaintTypeName)

#                 # List of complaint types belongs to this department.
#                 department['ComplaintTypes'] = department_complaint_types

#             except Exception as e:
#                 error_logger(f'Route: {request.path}').error(e)

#     except Exception as e:
#         error_logger(f'Route: {request.path}').error(e)

#     if len(result) > 0:
#         # Complaint types found.
#         final_data = generate_final_data('DATA_FOUND')
#         final_data['result'] = result
#     else:
#         # No complaint types are found.
#         final_data = generate_final_data('DATA_NOT_FOUND')

#     return final_data

@delivery_blueprint.route('/get_complaint_types', methods=["GET"])
# @authenticate('delivery_user')
def get_complaint_types():
    """
    API for getting the complaint types that can be passed to the Ameyo ticketing service.
    @return:
    """
    result = []
    try:

        query = f""" EXEC JFSL.Dbo. SPFabComplaintTypesCustApp"""
        departments = CallSP(query).execute().fetchall()
        print(departments)

        for department in departments:
            # Looping through the departments.
            dep = {'Department': department.get('DeptName'), 'ComplaintTypes': []}
            result.append(dep)
        print(result)

        # Looping through the result dict variable, find the complaint types that belongs to the dict.
        for department in result:
            # Department name
            dept_name = department['Department']
            try:
                # Fetching all the complaint types related to this department.
                query = f""" EXEC JFSL.Dbo. SPFabComplaintTypesCustApp @DeptName = '{dept_name}'"""
                complaint_types = CallSP(query).execute().fetchall()
                department_complaint_types = []

                # Looping through the complaint types and append them into the department_complaint_types variable.
                for complaint_type in complaint_types:
                    department_complaint_types.append(complaint_type.get('ComplaintTypeName'))

                # List of complaint types belongs to this department.
                department['ComplaintTypes'] = department_complaint_types

            except Exception as e:
                error_logger(f'Route: {request.path}').error(e)

    except Exception as e:
        error_logger(f'Route: {request.path}').error(e)

    if len(result) > 0:
        # Complaint types found.
        final_data = generate_final_data('DATA_FOUND')
        final_data['result'] = result
    else:
        # No complaint types are found.
        final_data = generate_final_data('DATA_NOT_FOUND')

    return final_data


# @delivery_blueprint.route('/complaint_or_rewash', methods=["POST"])
# @authenticate('delivery_user')
# def complaint_or_rewash():
#     """
#     API for adding a complaint  to the Ameyo ticketing service. Rewash is also possible here.
#     If the garment has already a complaint, then the complaint can not update/delete.
#     If the garment is more than 180 days old, then complaints cannot be added.
#     @return:
#     """

#     complaint_form = AddComplaintForm()
#     if complaint_form.validate_on_submit():
#         customer_id = complaint_form.customer_id.data
#         order_id = complaint_form.order_id.data
#         complaint_garment_list = complaint_form.complaint_garment_list.data
#         allowed_complaint_garment_list = []
#         allowed_rewash_garments = []
#         complaint_created = False
#         rewashed = False
#         comments = []
#         try:
#             # Getting the customer details
#             customer_details = db.session.query(Customer.CustomerId, Customer.CustomerCode, Customer.CustomerName,
#                                                 Customer.MobileNo, Customer.BranchCode).filter(
#                 Customer.CustomerId == customer_id).one_or_none()
#             if customer_details is not None:
#                 ameyo_customer_id = ameyo_module.get_ameyo_customer_id(customer_details.MobileNo)
#                 if ameyo_customer_id:
#                     # A valid ameyo customer id is found.

#                     # Getting the order details
#                     order_details = db.session.query(Order).filter(
#                         Order.OrderId == order_id, Order.IsDeleted == 0).one_or_none()

#                     if order_details is not None:

#                         # Getting the complaints of the EGRN (if any)
#                         complaints = ameyo_module.get_complaints_from_egrn(order_details.EGRN)

#                         # Looping all the list of garments and filtering the garments
#                         # which has no previous complaint history.
#                         for garment_complaint in complaint_garment_list:

#                             # Default permit flag for each garment set to True.
#                             permit_to_complaint = True

#                             # Default permit flag for each rewash garment.
#                             if garment_complaint['department_complaint'] == 'Rewash':
#                                 permit_to_rewash = True
#                             else:
#                                 permit_to_rewash = False

#                             # Getting the tag id from the OrderGarments table.
#                             # The garment should not have any QC issues.
#                             tag_id_detail = db.session.query(OrderGarment.TagId).filter(
#                                 OrderGarment.OrderGarmentId == garment_complaint['order_garment_id'],
#                                 OrderGarment.OrderId == order_id,
#                                 OrderGarment.IsDeleted == 0,
#                                 or_(OrderGarment.QCStatus == None, OrderGarment.QCStatus == 2)).one_or_none()

#                             if tag_id_detail is not None:
#                                 # Successfully retrieved the details.
#                                 if tag_id_detail.TagId is not None:
#                                     # TagId is not a NULL value.
#                                     for complaint in complaints:
#                                         if complaint['TAGNO'] == tag_id_detail.TagId:
#                                             # This garment has a complaint. So no further complaints can be generated.
#                                             permit_to_complaint = False

#                                             # Checking whether the garment is already rewashed or not.
#                                             if garment_complaint['department_complaint'] == 'Rewash' and 0 < complaint[
#                                                 'REWASHCOUNT'] < 2:
#                                                 permit_to_rewash = True
#                                             else:
#                                                 # Here, the garment has either has a complaint or has exceeded
#                                                 # the rewash limit.
#                                                 if garment_complaint['department_complaint'] == 'Rewash' and complaint[
#                                                     'REWASHCOUNT'] >= 2:
#                                                     comments.append(
#                                                         'The garment can not be rewashed. Exceeded the rewash limit.')
#                                                 else:
#                                                     # Another complaint has been found.
#                                                     if garment_complaint['department_complaint'] == 'Rewash' and \
#                                                             complaint['REWASHCOUNT'] == 0:
#                                                         comments.append('This garment can not be rewashed. '
#                                                                         'Another complaint has been found for this garment.')
#                                                 permit_to_rewash = False
#                                             break
#                                     if permit_to_complaint:
#                                         # No previous complaints found.
#                                         garment_complaint['tag_id'] = tag_id_detail.TagId
#                                         allowed_complaint_garment_list.append(garment_complaint)
#                                     else:
#                                         # A complaint has been found for this garment.
#                                         comments.append(
#                                             f"A previous complaint found for "
#                                             f"order garment id {garment_complaint['order_garment_id']}."
#                                         )

#                                     if permit_to_rewash:
#                                         # This garment can be rewashed.
#                                         allowed_rewash_garments.append(garment_complaint)
#                                     else:
#                                         if garment_complaint['department_complaint'] == 'Rewash':
#                                             # A complaint has been found for this garment.
#                                             comments.append(
#                                                 f"This garment can not be rewashed. "
#                                                 f" Order garment id {garment_complaint['order_garment_id']}."
#                                             )
#                             else:
#                                 # No garment details are found.
#                                 comments.append(
#                                     f"No valid garment details found for "
#                                     f"order garment id {garment_complaint['order_garment_id']}.")

#                         # allowed_complaint_garment_list will contain the garments that are allowed to make
#                         # a complaint.
#                         if len(allowed_complaint_garment_list) > 0:

#                             # Generating a complaint for this garment(s).
#                             create_complaint = ameyo_module.add_complaint(customer_details, ameyo_customer_id,
#                                                                           order_details.EGRN,
#                                                                           allowed_complaint_garment_list)

#                             if create_complaint['status']:
#                                 # Complaints are created.
#                                 complaint_created = True
#                                 comments = create_complaint['comments']
#                             else:
#                                 # Failed to create any complaint.
#                                 comments = create_complaint['comments']

#                         # allowed_rewash_garments will contain the garments that are
#                         # allowed to make a rewash
#                         if len(allowed_rewash_garments) > 0:
#                             rewash = ameyo_module.rewash(order_details, allowed_rewash_garments)

#                             if rewash:
#                                 # Successfully rewashed the garments.
#                                 rewashed = True
#                     else:
#                         comments.append('No order details found')
#                 else:
#                     comments.append('No ameyo customer id found')
#         except Exception as e:
#             error_logger(f'Route: {request.path}').error(e)

#         if complaint_created:
#             final_data = generate_final_data('DATA_SAVED')
#             if comments:
#                 final_data['comments'] = comments
#         else:
#             if rewashed:
#                 final_data = generate_final_data('DATA_SAVED')
#             else:
#                 final_data = generate_final_data('DATA_SAVE_FAILED')

#             if comments:
#                 final_data['comments'] = comments
#     else:
#         # Form validation error.
#         final_data = generate_final_data('FORM_ERROR')
#         final_data['errors'] = populate_errors(complaint_form.errors)
#     return final_data


@delivery_blueprint.route('/complaint_or_rewash', methods=["POST"])
# @authenticate('delivery_user')
def complaint_or_rewash():
    """
    API for adding a complaint  to the Ameyo ticketing service. Rewash is also possible here.
    If the garment has already a complaint, then the complaint can not update/delete.
    If the garment is more than 180 days old, then complaints cannot be added.
    @return:
    """
    complaint_form = AddComplaintForm1()
    if complaint_form.validate_on_submit():
        log = {
            "test_form": complaint_form.data
                    }
        info_logger(f'Route: {request.path}').info(json.dumps(log))
        CustomerCode = complaint_form.CustomerCode.data
        TRNNo = complaint_form.TRNNo.data
        EGRN = complaint_form.EGRN.data
        TagNo =  complaint_form.TagNo.data
        CustomerName = complaint_form.CustomerName.data
        BranchCode = complaint_form.BranchCode.data
        MobileNo = complaint_form.MobileNo.data
        complaint_garment_list = complaint_form.complaint_garment_list.data
        Duserlat = complaint_form.Duserlat.data
        Duserlong = complaint_form.Duserlong.data
        CustLat = complaint_form.CustLat.data
        CustLong = complaint_form.CustLong.data
        allowed_complaint_garment_list = []
        allowed_rewash_garments = []
        user_id = request.headers.get('user_id')
        complaint_created = False
        rewashed = False
        comments = []
        try:
            # Getting the customer details
            ameyo_customer_id = ameyo_module.get_ameyo_customer_id(MobileNo)
            if ameyo_customer_id:
                complaints = ameyo_module.get_complaints_from_egrn(EGRN)
                print(complaints)
                for garment_complaint in complaint_garment_list:
                            # Default permit flag for each garment set to True.
                    permit_to_complaint = True

                            # Default permit flag for each rewash garment.
                    
                    if garment_complaint['department_complaint'] == 'Rewash':
                        permit_to_rewash = True
                    

                    else:
                        permit_to_rewash = False
                    log = {
                        "permit_to_rewash": permit_to_rewash
                    }
                    info_logger(f'Route: {request.path}').info(json.dumps(log))
                    for complaint in complaints:
                       
                        if complaint['TAGNO'] == garment_complaint['TagNo']:

                            permit_to_complaint = False

                            if garment_complaint['department_complaint'] == 'Rewash' and 0 < complaint[
                                        'REWASHCOUNT'] < 2:
                                permit_to_rewash = True
                            else:

                                if garment_complaint['department_complaint'] == 'Rewash' and complaint[
                                                    'REWASHCOUNT'] >= 2:
                                    comments.append(
                                                        'The garment can not be rewashed. Exceeded the rewash limit.')
                                else:
                                                    # Another complaint has been found.
                                    if garment_complaint['department_complaint'] == 'Rewash' and \
                                                            complaint['REWASHCOUNT'] == 0:
                                        comments.append('This garment can not be rewashed. '
                                                                        'Another complaint has been found for this garment.')
                                permit_to_rewash = False
                            break
                    if permit_to_complaint:
                                         # No previous complaints found.
                        garment_complaint['TagNo'] = garment_complaint['TagNo']
                        allowed_complaint_garment_list.append(garment_complaint)

                    else:
                                        # A complaint has been found for this garment.
                        comments.append(
                                            f"A previous complaint found for "
                                            f"order garment id {garment_complaint['order_garment_id']}."
                                )

                    if permit_to_rewash:
                                        # This garment can be rewashed.
                        allowed_rewash_garments.append(garment_complaint)
                    else:
                        if garment_complaint['department_complaint'] == 'Rewash':
                                            # A complaint has been found for this garment.
                                comments.append(
                                                f"This garment can not be rewashed. "
                                                f" Order garment id {garment_complaint['order_garment_id']}."
                                )

                    # allowed_complaint_garment_list will contain the garments that are allowed to make
                        # a complaint.

                if len(allowed_complaint_garment_list) > 0:

                            # Generating a complaint for this garment(s).
                    egrn = EGRN
                    create_complaint = ameyo_module.add_complaint(CustomerName,MobileNo, CustomerCode ,ameyo_customer_id,
                                                                         egrn,
                                                                          allowed_complaint_garment_list ,BranchCode)


                    if create_complaint['status']:
                                # Complaints are created.
                        complaint_created = True
                        comments = create_complaint['comments']
                    else:
                                # Failed to create any complaint.
                        comments = create_complaint['comments']

                        # allowed_rewash_garments will contain the garments that are
                        # allowed to make a rewash
                if len(allowed_rewash_garments) > 0:
                    log = {
                        "allowed_rewash_garments": allowed_rewash_garments
                    }
                    info_logger(f'Route: {request.path}').info(json.dumps(log))
                    rewash = ameyo_module.rewash(user_id, allowed_rewash_garments, TRNNo,TagNo, Duserlat, Duserlong, CustLat,CustLong ,BranchCode)
                    if rewash:
                        rewashed = True
                    else:
                        pass
                        # comments.append('No order details found')
            else:
                comments.append('No ameyo customer id found')
        except Exception as e:
            error_logger(f'Route: {request.path}').error(e)
        log = {
            "complaint_created": complaint_created,
            "rewashed":rewashed
                    }
        info_logger(f'Route: {request.path}').info(json.dumps(log))

        if complaint_created or rewashed:
            status_code = 'DATA_SAVED'
        else:
            status_code = 'DATA_SAVE_FAILED'

        if status_code == 'DATA_SAVED':
            final_data = {
                "status": "success",
                "status_code": status_code,
                "message": "Data saved successfully"
            }
        elif status_code == 'DATA_SAVE_FAILED':
            final_data = {
                "status": "failed",
                "status_code": status_code,
                "message": "Failed to save the data"
            }

        if comments:
            final_data['comments'] = comments
    else:
            # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(complaint_form.errors)

    log_data = {
        'final_data': final_data
        }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))

    return final_data


@delivery_blueprint.route('/check_permission', methods=["GET"])
@authenticate('delivery_user')
def check_permission():
    """
    Logout API for the delivery users.
    @return: If the validations are successful, make the access token expire
    by changing the values(AuthKeyExpiry, IsActive) in the DeliveryUserLogin table.
    """
    final_data = generate_final_data('FAILED')
    try:
        user_id = request.headers.get('user_id')
        delivery_user_permission = db.session.query(
            DeliveryUser.PartialPaymentPermission).filter(
            DeliveryUser.DUserId == user_id).one_or_none()
        if delivery_user_permission is not None:
            if delivery_user_permission.PartialPaymentPermission:
                final_data = generate_final_data('SUCCESS')
            else:
                final_data = generate_final_data('FAILED')
        else:
            final_data = generate_final_data('FAILED')
        print(final_data)
    except Exception as e:
        db.session.rollback()
        error_logger(f'Route: {request.path}').error(e)

    return final_data


@delivery_blueprint.route('/make_payment_before', methods=["POST"])
# @authenticate('delivery_user')
def make_payment_before():
    """
    API for making the payment and settling the order.
    @return:
    """
    payment_form = MakePaymentForm()

    log_data = {

        "payment_form": payment_form.data
    }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))

    if payment_form.validate_on_submit():
        order_id = payment_form.order_id.data
        delivery_request_id = payment_form.delivery_request_id.data
        collected = payment_form.collected.data
        trn = payment_form.trn.data
        coupons = payment_form.coupons.data
        lp = payment_form.lp.data
        user_id = request.headers.get('user-id')
        error_msg = ''
        collected_amount = 0
        settlement = False
        attached_coupons = []
        ready_to_make_payment = False
        trn_creation = False
        is_monthly_customer = False

        # Looping through the amount collection and calculate the total collected amount in various payment modes.
        for collection in collected:
            collected_amount += collection['amount']

        # Getting the EGRN and the customer code details.
        try:
            essential_details = delivery_controller_queries.get_essential_data_for_payment(delivery_request_id,
                                                                                           order_id)

            if essential_details:
                # Edited by MMM
                egrn = essential_details['egrn']
                customer_code = essential_details['customer_code']
                egrn_details = essential_details['egrn_details']
                branch_code = essential_details['branch_code']
                trn_amount_received = essential_details['trn_amount_received']
                after_pre_applied = payment_module.deduct_pre_applied_coupons_and_discounts(egrn,
                                                                                            egrn_details[
                                                                                                'initial_amount'],
                                                                                            egrn_details[
                                                                                                'details'][
                                                                                                'ORDERGARMENTID'])

                # amount_to_pay will be the initial EGRN amount (Before any calculations).
                # Getting the payment details.
                # Edited by MMM
                # Retrieving the payable amount through SP
                payable_details = delivery_controller_queries.get_payable_amount_via_sp(customer_code, egrn)
                # amount_to_pay = payable_details['PAYABLEAMOUNT']
                if payable_details:
                    amount_to_pay = payable_details['PAYABLEAMOUNT']
                else:
                    amount_to_pay = 0
                new_customer_code = None

                invoice_discount_details = []

                attached_loyalty_points = {}

                # Passing the EGRN to check whether any pre-applied discounts/coupons/LPs
                # are attached to it or not.

                if amount_to_pay > 0 or after_pre_applied['pre_applied_coupons']:
                    if coupons:
                        # Coupons have been given in the request.
                        after_applied = payment_module.apply_coupons(amount_to_pay, coupons, egrn)

                        if after_applied['applied_coupons']:
                            # Coupon(s) have successfully applied.
                            if after_pre_applied['pre_applied_coupons']:
                                # Merging both applied coupons and pre-applied coupons.
                                attached_coupons = [*after_pre_applied['pre_applied_coupons'],
                                                    *after_applied['applied_coupons']]
                            else:
                                # No pre-applied coupons found. Only applied coupons are attached.
                                attached_coupons = after_applied['applied_coupons']

                            amount_to_pay = after_applied['amount_to_pay']
                    else:
                        if after_pre_applied['pre_applied_coupons']:
                            attached_coupons = after_pre_applied['pre_applied_coupons']

                    # After considering all the pre-applieds, update the amount_to_pay variable.
                    # amount_to_pay = after_pre_applied['amount_to_pay']
                    #
                    # # Getting the pre applied invoice level discount details (if any).
                    # invoice_discount_details = after_pre_applied['invoice_discount_details']
                    #
                    # # Getting the pre applied loyalty points details (if any).
                    # attached_loyalty_points = after_pre_applied['pre_applied_lp_details']

                    # if amount_to_pay > 0:
                    # Customer needs to pay from himself/herself.
                    # if coupons:
                    #     # Coupons have been given in the request.
                    #     after_applied = payment_module.apply_coupons(amount_to_pay, coupons, egrn)
                    #
                    #     if after_applied['applied_coupons']:
                    #         # Coupon(s) have successfully applied.
                    #         if after_pre_applied['pre_applied_coupons']:
                    #             # Merging both applied coupons and pre-applied coupons.
                    #             attached_coupons = [*after_pre_applied['pre_applied_coupons'],
                    #                                 *after_applied['applied_coupons']]
                    #         else:
                    #             # No pre-applied coupons found. Only applied coupons are attached.
                    #             attached_coupons = after_applied['applied_coupons']
                    #
                    #         amount_to_pay = after_applied['amount_to_pay']
                    #     else:
                    #         # No valid coupon details are found for the given coupons.
                    #         info_logger(f'Route: {request.path}').info(
                    #             f"No valid coupon details are found for the given coupons - {','.join(map(str, coupons))}.")
                    # else:
                    #     # No coupons have been given.
                    #
                    #     # If no pre-applied coupons are found, attached_coupons
                    #     # will be an empty list.
                    #     if after_pre_applied['pre_applied_coupons']:
                    #         attached_coupons = after_pre_applied['pre_applied_coupons']
                    #
                    # # After checking the coupons, LP will be checked. Here, amount_to_pay must not be 0.
                    # if lp and amount_to_pay > 0:
                    #     # LP is manually applied. If the LP is applied manually,
                    #     # there should not be a pre applied LP.
                    #     # If a pre applied LP is present, then lp redemption is not allowed.
                    #     if not attached_loyalty_points:
                    #         # No pre applied LPs are applied to this order before.
                    #         # So manual LP redemption is possible.
                    #         applied_lp = payment_module.apply_lp(customer_code, egrn, amount_to_pay)
                    #
                    #         if applied_lp:
                    #             # Manually applied the loyalty points.
                    #             attached_loyalty_points = applied_lp['applied_lp']
                    #             amount_to_pay = applied_lp['amount_to_pay']
                    #
                    #     else:
                    #         error_msg = 'Can not apply LP again. Already a pre applied LP is present.'

                    # Calling function for checking  monthly customer
                    monthly_customer = delivery_controller_queries.check_monthly_customer(customer_code)
                    # After considering the coupons,LP, collected amount can also be considered.
                    # If monthly customer no need for checking collected amount
                    if collected_amount != amount_to_pay and monthly_customer is False:
                        log_data = {
                            "entry1": "1"
                        }
                        info_logger(f'Route: {request.path}').info(json.dumps(log_data))

                        garment_complaints = delivery_controller_queries.count_order_garments_open_complaints(
                            order_id)
                        if garment_complaints == 0:
                            if trn:
                                if collected_amount < amount_to_pay:
                                    # Checking whether this delivery user has permission or not to make
                                    # partial payments.
                                    delivery_user_permission = db.session.query(
                                        DeliveryUser.PartialPaymentPermission).filter(
                                        DeliveryUser.DUserId == user_id).one_or_none()
                                    if delivery_user_permission is not None:
                                        if delivery_user_permission.PartialPaymentPermission:
                                            # This delivery user has the permission to make partial payments.
                                            partial_payment = True
                                            trn_creation = payment_module.create_trn(order_id, delivery_request_id,
                                                                                     egrn_details,
                                                                                     attached_coupons,
                                                                                     attached_loyalty_points,
                                                                                     invoice_discount_details,
                                                                                     collected,
                                                                                     after_pre_applied,
                                                                                     partial_payment,
                                                                                     collected_amount,
                                                                                     amount_to_pay, branch_code)
                                        else:
                                            error_msg = 'This delivery user has no permission to make partial ' \
                                                        'payments. '
                                    else:
                                        error_msg = 'Delivery user details not found.'
                                else:
                                    error_msg = 'Collected amount is more than the actual payable amount.'
                            else:
                                error_msg = 'Amounts are not matching.'
                        else:
                            error_msg = 'Amounts are not matching and no active complaints present'

                    else:
                        # Collected amount is matching with the amount_to_pay.
                        ready_to_make_payment = True

                else:
                    ready_to_make_payment = True

                log_data = {
                    'entry2': 'going to settlement',
                    'ready_to_make_payment....': ready_to_make_payment

                }
                info_logger(f'Route: {request.path}').info(json.dumps(log_data))

                if ready_to_make_payment:
                    log_data = {
                        'entry2': 'going to settlement11',
                        'ready_to_make_payment....': ready_to_make_payment,
                        'amount_to_pay....': amount_to_pay,
                        "essential_details": essential_details
                    }
                    info_logger(f'Route: {request.path}').info(json.dumps(log_data))
                    # Checking whether the garments under this order has a complaint or not.
                    # requested by ravi sir to go to make payment even though the garment complaint exists

                    # garment_complaints = delivery_controller_queries.count_order_garments_open_complaints(order_id)
                    # if garment_complaints == 0:
                    # No complaints have been found for any garments in this order.
                    # Proceed to mak        e the payment.
                    # result_pay = delivery_controller_queries.get_payable_amount_via_sp(customer_code, egrn_details)

                    monthly_customer = delivery_controller_queries.check_monthly_customer(customer_code)
                    if monthly_customer:
                        is_monthly_customer = True

                    settlement = payment_module.make_payment(customer_code, egrn_details, branch_code, amount_to_pay,
                                                             attached_coupons, attached_loyalty_points,
                                                             invoice_discount_details, collected, egrn,
                                                             trn_amount_received, user_id)

                else:
                    # A complaint has been found for one of the order garments. So Create TRN instead of settlement.
                    partial_payment = False
                    trn_creation = payment_module.create_trn(order_id, delivery_request_id, egrn_details,
                                                             attached_coupons,
                                                             attached_loyalty_points,
                                                             invoice_discount_details, collected,
                                                             after_pre_applied, partial_payment, collected_amount,
                                                             amount_to_pay, branch_code)

        except Exception as e:
            error_logger(f'Route: {request.path}').error(e)

        log_data = {

            'settlement': settlement,
            'trn_creation': trn_creation,
            "is_monthly_customer": is_monthly_customer
        }
        info_logger(f'Route: {request.path}').info(json.dumps(log_data))
        # Commneted by Manju to avoid rewash issues
        if settlement or trn_creation or is_monthly_customer:
            final_data = generate_final_data('DATA_SAVED')
            final_data['result'] = settlement
        else:
            if error_msg != '':
                final_data = generate_final_data('CUSTOM_FAILED', error_msg)
            else:
                final_data = generate_final_data('DATA_SAVE_FAILED')

    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(payment_form.errors)
    log_data = {
        'final_data': final_data

    }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))

    return final_data

# @delivery_blueprint.route('/make_payment', methods=["POST"])
# # @authenticate('delivery_user')
# def make_payment():
#     """
#     API for making the payment and settling the order.
#     @return:
#     """
#     payment_form = MakePaymentForm()

#     log_data = {

#         "payment_form": payment_form.data
#     }
#     info_logger(f'Route: {request.path}').info(json.dumps(log_data))

#     if payment_form.validate_on_submit():
#         order_id = payment_form.order_id.data
#         delivery_request_id = payment_form.delivery_request_id.data
#         collected = payment_form.collected.data
#         trn = payment_form.trn.data
#         coupons = payment_form.coupons.data
#         lp = payment_form.lp.data
#         user_id = request.headers.get('user-id')
#         error_msg = ''
#         collected_amount = 0
#         settlement = False
#         attached_coupons = []
#         ready_to_make_payment = False
#         trn_creation = False
#         is_monthly_customer = False
#         IsSettled = None

#         # Fetching the trn number from db based on delivery request id
#         TRNNumber = db.session.query(DeliveryRequest.TRNNo).filter(
#             DeliveryRequest.DeliveryRequestId == delivery_request_id).one_or_none()

#         TRNNumber = TRNNumber[0]

#         query = f" EXEC JFSL.[dbo].SpIsSettledInvoice @TRNNO ='{TRNNumber}'"

#         result = CallSP(query).execute().fetchall()
#         log_data = {
#             "query": query,
#             "result": result
#         }
#         info_logger(f'Route: {request.path}').info(json.dumps(log_data))

#         if result and result[0].get('IsSettled') is False:
#             # Looping through the amount collection and calculate the total collected amount in various payment modes.
#             for collection in collected:
#                 collected_amount += collection['amount']

#             # Getting the EGRN and the customer code details.
#             try:
#                 essential_details = delivery_controller_queries.get_essential_data_for_payment(delivery_request_id,
#                                                                                                order_id)

#                 if essential_details:
#                     # Edited by MMM
#                     egrn = essential_details['egrn']
#                     customer_code = essential_details['customer_code']
#                     egrn_details = essential_details['egrn_details']
#                     branch_code = essential_details['branch_code']
#                     trn_amount_received = essential_details['trn_amount_received']
#                     after_pre_applied = payment_module.deduct_pre_applied_coupons_and_discounts(egrn,
#                                                                                                 egrn_details[
#                                                                                                     'initial_amount'],
#                                                                                                 egrn_details[
#                                                                                                     'details'][
#                                                                                                     'ORDERGARMENTID'])

#                     # amount_to_pay will be the initial EGRN amount (Before any calculations).
#                     # Getting the payment details.
#                     # Edited by MMM
#                     # Retrieving the payable amount through SP
#                     payable_details = delivery_controller_queries.get_payable_amount_via_sp(customer_code, egrn)
#                     # amount_to_pay = payable_details['PAYABLEAMOUNT']
#                     if payable_details:
#                         amount_to_pay = payable_details['PAYABLEAMOUNT']
#                     else:
#                         amount_to_pay = 0
#                     new_customer_code = None

#                     invoice_discount_details = []

#                     attached_loyalty_points = {}

#                     # Passing the EGRN to check whether any pre-applied discounts/coupons/LPs
#                     # are attached to it or not.

#                     if amount_to_pay > 0 or after_pre_applied['pre_applied_coupons']:
#                         if coupons:
#                             # Coupons have been given in the request.
#                             after_applied = payment_module.apply_coupons(amount_to_pay, coupons, egrn)

#                             if after_applied['applied_coupons']:
#                                 # Coupon(s) have successfully applied.
#                                 if after_pre_applied['pre_applied_coupons']:
#                                     # Merging both applied coupons and pre-applied coupons.
#                                     attached_coupons = [*after_pre_applied['pre_applied_coupons'],
#                                                         *after_applied['applied_coupons']]
#                                 else:
#                                     # No pre-applied coupons found. Only applied coupons are attached.
#                                     attached_coupons = after_applied['applied_coupons']

#                                 amount_to_pay = after_applied['amount_to_pay']
#                         else:
#                             if after_pre_applied['pre_applied_coupons']:
#                                 attached_coupons = after_pre_applied['pre_applied_coupons']

#                         # Calling function for checking  monthly customer
#                         monthly_customer = delivery_controller_queries.check_monthly_customer(customer_code)
#                         # After considering the coupons,LP, collected amount can also be considered.
#                         # If monthly customer no need for checking collected amount
#                         if collected_amount != amount_to_pay and monthly_customer is False:
#                             log_data = {
#                                 "entry1": "1"
#                             }
#                             info_logger(f'Route: {request.path}').info(json.dumps(log_data))

#                             garment_complaints = delivery_controller_queries.count_order_garments_open_complaints(
#                                 order_id)
#                             if garment_complaints == 0:
#                                 if trn:
#                                     if collected_amount < amount_to_pay:
#                                         # Checking whether this delivery user has permission or not to make
#                                         # partial payments.
#                                         delivery_user_permission = db.session.query(
#                                             DeliveryUser.PartialPaymentPermission).filter(
#                                             DeliveryUser.DUserId == user_id).one_or_none()
#                                         if delivery_user_permission is not None:
#                                             if delivery_user_permission.PartialPaymentPermission:
#                                                 # This delivery user has the permission to make partial payments.
#                                                 partial_payment = True
#                                                 trn_creation = payment_module.create_trn(order_id, delivery_request_id,
#                                                                                          egrn_details,
#                                                                                          attached_coupons,
#                                                                                          attached_loyalty_points,
#                                                                                          invoice_discount_details,
#                                                                                          collected,
#                                                                                          after_pre_applied,
#                                                                                          partial_payment,
#                                                                                          collected_amount,
#                                                                                          amount_to_pay, branch_code)
#                                             else:
#                                                 error_msg = 'This delivery user has no permission to make partial ' \
#                                                             'payments. '
#                                         else:
#                                             error_msg = 'Delivery user details not found.'
#                                     else:
#                                         error_msg = 'Collected amount is more than the actual payable amount.'
#                                 else:
#                                     error_msg = 'Amounts are not matching.'
#                             else:
#                                 error_msg = 'Amounts are not matching and no active complaints present'

#                         else:
#                             # Collected amount is matching with the amount_to_pay.
#                             ready_to_make_payment = True

#                     else:
#                         ready_to_make_payment = True

#                     log_data = {
#                         'entry2': 'going to settlement',
#                         'ready_to_make_payment....': ready_to_make_payment

#                     }
#                     info_logger(f'Route: {request.path}').info(json.dumps(log_data))

#                     if ready_to_make_payment:
#                         log_data = {
#                             'entry2': 'going to settlement11',
#                             'ready_to_make_payment....': ready_to_make_payment,
#                             'amount_to_pay....': amount_to_pay,
#                             "essential_details": essential_details
#                         }
#                         info_logger(f'Route: {request.path}').info(json.dumps(log_data))
#                         # Checking whether the garments under this order has a complaint or not.
#                         # requested by ravi sir to go to make payment even though the garment complaint exists

#                         # garment_complaints = delivery_controller_queries.count_order_garments_open_complaints(order_id)
#                         # if garment_complaints == 0:
#                         # No complaints have been found for any garments in this order.
#                         # Proceed to mak        e the payment.
#                         # result_pay = delivery_controller_queries.get_payable_amount_via_sp(customer_code, egrn_details)

#                         monthly_customer = delivery_controller_queries.check_monthly_customer(customer_code)
#                         if monthly_customer:
#                             is_monthly_customer = True

#                         settlement = payment_module.make_payment(customer_code, egrn_details, branch_code,
#                                                                  amount_to_pay,
#                                                                  attached_coupons, attached_loyalty_points,
#                                                                  invoice_discount_details, collected, egrn,
#                                                                  trn_amount_received, user_id)

#                     else:
#                         # A complaint has been found for one of the order garments. So Create TRN instead of settlement.
#                         partial_payment = False
#                         trn_creation = payment_module.create_trn(order_id, delivery_request_id, egrn_details,
#                                                                  attached_coupons,
#                                                                  attached_loyalty_points,
#                                                                  invoice_discount_details, collected,
#                                                                  after_pre_applied, partial_payment, collected_amount,
#                                                                  amount_to_pay, branch_code)

#             except Exception as e:
#                 error_logger(f'Route: {request.path}').error(e)

#             log_data = {

#                 'settlement': settlement,
#                 'trn_creation': trn_creation,
#                 "is_monthly_customer": is_monthly_customer
#             }
#             info_logger(f'Route: {request.path}').info(json.dumps(log_data))
#             # Commneted by Manju to avoid rewash issues
#             if settlement or trn_creation or is_monthly_customer:
#                 final_data = generate_final_data('DATA_SAVED')
#                 final_data['result'] = settlement
#             else:
#                 if error_msg != '':
#                     final_data = generate_final_data('CUSTOM_FAILED', error_msg)
#                 else:
#                     final_data = generate_final_data('DATA_SAVE_FAILED')

#         else:
#             final_data = generate_final_data('DATA_ALREADY_SAVED')
#     else:
#         # Form validation error.
#         final_data = generate_final_data('FORM_ERROR')
#         final_data['errors'] = populate_errors(payment_form.errors)
#     log_data = {
#         'final_data': final_data

#     }
#     info_logger(f'Route: {request.path}').info(json.dumps(log_data))

#     return final_data

@delivery_blueprint.route('/make_payment', methods=["POST"])
# @authenticate('delivery_user')
def make_payment():
    """
    API for making the payment and settling the order.
    @return:
    """
    payment_form = MakePaymentForm()

    if payment_form.validate_on_submit():
        log_data = {

            "payment_form": payment_form.data
                            }
        info_logger(f'Route: {request.path}').info(json.dumps(log_data))

        collected = payment_form.collected.data
        trn = payment_form.trn.data
        TRNNo = payment_form.TRNNo.data
        egrn = payment_form.EGRN.data
        customer_code = payment_form.CustomerCode.data
        branch_code = payment_form.BranchCode.data
        coupons = payment_form.coupons.data
        lp = payment_form.lp.data
        MobileNo = payment_form.MobileNo.data
        OrderId = payment_form.OrderID.data
        is_monthly_customer = payment_form.MonthlyCustomer.data
        user_id = request.headers.get('user-id')
        error_msg = ''
        collected_amount = 0
        settlement = False
        attached_coupons = []
        ready_to_make_payment = False
        trn_creation = False
     
        IsSettled = None
        query = f" EXEC JFSL.[dbo].SpIsSettledInvoice @TRNNO ='{TRNNo}'"

        result = CallSP(query).execute().fetchall()
        print(result)

        if result and result[0].get('IsSettled') is False:
            # Looping through the amount collection and calculate the total collected amount in various payment modes.
            for collection in collected:
                collected_amount += collection['amount']

            # Getting the EGRN and the customer code details.
            try:
                essential_details = delivery_controller_queries.get_essential_data_for_payment(egrn,
                                                                                               TRNNo, customer_code)

                if essential_details:
                    # Edited by MMM
                    egrn_details = essential_details['egrn_details']

                    trn_amount_received = essential_details['trn_amount_received']
                    payable_details = delivery_controller_queries.get_payable_amount_via_sp(customer_code, TRNNo)
                    after_pre_applied = payment_module.deduct_pre_applied_coupons_and_discounts(egrn,
                                                                                                # egrn_details[
                                                                                                #     'initial_amount'],
                                                                                                payable_details['PAYABLEAMOUNT'],
                                                                                                egrn_details[
                                                                                                    'details'][
                                                                                                    'ORDERGARMENTID'])


                    payable_details = delivery_controller_queries.get_payable_amount_via_sp(customer_code, TRNNo)
                    log_data = {
                        "payable_details": payable_details
                            }
                    info_logger(f'Route: {request.path}').info(json.dumps(log_data))
                    if payable_details:
                        if payable_details.get('IsPreAppliedCoupon') in [1, True]:
                            result = payment_module.get_available_coupon_codes(egrn)
                           
                            discount_amount = result[0]['DISCOUNTAMOUNT'] if result and isinstance(result, list) and 'DISCOUNTAMOUNT' in result[0] else 0

                            # Ensure amount_to_pay is not negative
                            amount_to_pay = payable_details['PAYABLEAMOUNT'] - discount_amount
                            amount_to_pay = amount_to_pay if amount_to_pay > 0 else 0
                        else:
                            amount_to_pay = payable_details['PAYABLEAMOUNT']
                    else:
                        amount_to_pay = 0

                    log_data = {
                        "amount_to_pay": amount_to_pay
                            }
                    info_logger(f'Route: {request.path}').info(json.dumps(log_data))
                    # amount_to_pay = payable_details['PAYABLEAMOUNT']
                    # if payable_details:
                    #     amount_to_pay = payable_details['PAYABLEAMOUNT']
                    # else:
                    #     amount_to_pay = 0
                    new_customer_code = None

                    invoice_discount_details = []

                    attached_loyalty_points = {}

                    # Passing the EGRN to check whether any pre-applied discounts/coupons/LPs
                    # are attached to it or not.

                    if amount_to_pay > 0 or after_pre_applied['pre_applied_coupons']:
                        if coupons:
                            # Coupons have been given in the request.
                            after_applied = payment_module.apply_coupons(amount_to_pay, coupons, egrn)

                            if after_applied['applied_coupons']:
                                # Coupon(s) have successfully applied.
                                if after_pre_applied['pre_applied_coupons']:
                                    # Merging both applied coupons and pre-applied coupons.
                                    attached_coupons = [*after_pre_applied['pre_applied_coupons'],
                                                        *after_applied['applied_coupons']]
                                else:
                                    # No pre-applied coupons found. Only applied coupons are attached.
                                    attached_coupons = after_applied['applied_coupons']

                                amount_to_pay = after_applied['amount_to_pay']
                        else:
                            if after_pre_applied['pre_applied_coupons']:
                                attached_coupons = after_pre_applied['pre_applied_coupons']
                        log_data = {
                                "amount_to_pay": amount_to_pay
                            }
                        info_logger(f'Route: {request.path}').info(json.dumps(log_data))

              
                        if collected_amount != amount_to_pay and is_monthly_customer is False:
                            log_data = {
                                "is_monthly_customer": is_monthly_customer
                            }
                            info_logger(f'Route: {request.path}').info(json.dumps(log_data))


                            query = f""" EXEC JFSL.Dbo.SPPendingDeliveriesDetailedScreen @user_id = {user_id} ,@TRNNo = '{TRNNo}', @CRMComplaintCounts = {1}"""
                            garment_complaints = CallSP(query).execute().fetchone()
                            garment_complaints = garment_complaints.get('CRMComplaintCounts')
                            log_data = {
                                "garment_complaints": garment_complaints
                                                }
                            info_logger(f'Route: {request.path}').info(json.dumps(log_data))

                            if garment_complaints == 0:
                                if trn:
                                    if collected_amount < amount_to_pay:
                                        # Checking whether this delivery user has permission or not to make
                                        # partial payments.
                                        delivery_user_permission = db.session.query(
                                            DeliveryUser.PartialPaymentPermission).filter(
                                            DeliveryUser.DUserId == user_id).one_or_none()
                                        if delivery_user_permission is not None:
                                            log_data = {
                                                    "delivery_user_permission": delivery_user_permission
                                                }
                                            info_logger(f'Route: {request.path}').info(json.dumps(log_data))
                                            if delivery_user_permission.PartialPaymentPermission:
                                                # This delivery user has the permission to make partial payments.
                                                partial_payment = True
                                                log_data = {
                                                    "partial_payment": partial_payment
                                                }
                                                info_logger(f'Route: {request.path}').info(json.dumps(log_data))
                                                trn_creation = payment_module.create_trn(TRNNo,
                                                                                         egrn,
                                                                                         customer_code,
                                                                                         egrn_details,
                                                                                         attached_coupons,
                                                                                         attached_loyalty_points,
                                                                                         invoice_discount_details,
                                                                                         collected,
                                                                                         after_pre_applied,
                                                                                         partial_payment,
                                                                                         collected_amount,
                                                                                         amount_to_pay,
                                                                                         branch_code, OrderId,MobileNo )
                              
                                            else:
                                                error_msg = 'This delivery user has no permission to make partial ' \
                                                            'payments. '
                                        else:
                                            error_msg = 'Delivery user details not found.'
                                    else:
                                
                                        error_msg = 'Collected amount is more than the actual payable amount.'
                                else:
                                    error_msg = 'Amounts are not matching.'
                            else:
                                error_msg = 'Amounts are not matching and no active complaints present'

                        else:
                            # Collected amount is matching with the amount_to_pay.
                            ready_to_make_payment = True

                    else:
                        ready_to_make_payment = True

                    log_data = {
                        'entry2': 'going to settlement',
                        "error_msg":error_msg,
                        'ready_to_make_payment....': ready_to_make_payment

                    }
                    info_logger(f'Route: {request.path}').info(json.dumps(log_data))

                    if ready_to_make_payment:
                        log_data = {
                            'entry2': 'going to settlement11',
                            'ready_to_make_payment....': ready_to_make_payment,
                            'amount_to_pay....': amount_to_pay,
                            "essential_details": essential_details
                        }
                        info_logger(f'Route: {request.path}').info(json.dumps(log_data))

                        

                        settlement = payment_module.make_payment(customer_code, egrn_details, branch_code,
                                                                 amount_to_pay,
                                                                 attached_coupons, attached_loyalty_points,
                                                                 invoice_discount_details, collected, egrn,
                                                                 trn_amount_received, user_id, is_monthly_customer ,TRNNo)


                        print("settlement",settlement)
                    else:
                        # A complaint has been found for one of the order garments. So Create TRN instead of settlement.
                        partial_payment = False
                        trn_creation = payment_module.create_trn(TRNNo,
                                                                 egrn,
                                                                 customer_code,
                                                                 egrn_details,
                                                                 attached_coupons,
                                                                 attached_loyalty_points,
                                                                 invoice_discount_details,
                                                                 collected,
                                                                 after_pre_applied,
                                                                 partial_payment,
                                                                 collected_amount,
                                                                 amount_to_pay,
                                                                 branch_code, OrderId,MobileNo )

            except Exception as e:
                error_logger(f'Route: {request.path}').error(e)

            log_data = {

                'settlement': settlement,
                'trn_creation': trn_creation,
                "is_monthly_customer": is_monthly_customer
            }
            info_logger(f'Route: {request.path}').info(json.dumps(log_data))
            # Commneted by Manju to avoid rewash issues
            if settlement or trn_creation or is_monthly_customer:
                final_data = generate_final_data('DATA_SAVED')
                final_data['result'] = settlement
                try:
                    log_data = {
                        'collect': collected

                    }
                    info_logger(f'Route: {request.path}').info(json.dumps(log_data))
                    #if collected[0].get('mode') == 'RAZORPAY':
                    if collected and isinstance(collected[0], dict) and collected[0].get('mode', '').upper() == 'RAZORPAY':

                        log_data = {
                            'collected1': 'test1'

                        }
                        info_logger(f'Route: {request.path}').info(json.dumps(log_data))
                        #update payment status in fabdeliveryinfo table 
                        # PaymentCollectedByName = db.session.query(DeliveryUser.UserName).filter(DeliveryUser.DUserId == user_id).one_or_none()
                        # PaymentCollectedByName = PaymentCollectedByName[0]
                        log_data = {
                            "user_id": user_id
                        }
                        info_logger(f'Route: {request.path}').info(json.dumps(log_data))
                        result = db.session.query(DeliveryUser.UserName).filter(
                            DeliveryUser.DUserId == user_id
                        ).one_or_none()

                        log_data = {
                            "query_result": str(result)
                            
                        }
                        if result is None:
                            raise ValueError(f"No DeliveryUser found with id {user_id}")
                        PaymentCollectedByName = result[0] if isinstance(result, tuple) else result
                        log_data = {
                            'collected1': PaymentCollectedByName

                        }
                        info_logger(f'Route: {request.path}').info(json.dumps(log_data))

                        update = db.session.execute(text("""
                                UPDATE JFSL.DBO.FabDeliveryInfo
                                SET PaymentCollectedBy = :user_id,
                                    PaymentCollectedByName = :PaymentCollectedByName,
                                    PaymentStatus = 'Paid',
                                    Activity_Status = 2,
                                    PaymentCollectedDate = :PaymentCollectedDate
                                WHERE TRNNo = :TRNNo
                        """), {
                                "user_id": user_id,
                                "PaymentCollectedByName": PaymentCollectedByName,
                                "PaymentCollectedDate": get_current_date(),
                                "TRNNo": TRNNo
                        })
                        info_logger("Update FabDeliveryInfo").info(f"Rows affected: {update.rowcount}, TRNNo={TRNNo}")

                        UpdateRazorPayQRCode = db.session.execute(text("""
                            UPDATE Customerapp..RazorpayPayments
                            SET IsExpired = 1,
                                IsDeleted = 1,
                                IsSettled = 1,
                                PaymentStatus = 'Paid'
                            WHERE TRNNo = :TRNNo
                        """), {"TRNNo": TRNNo})
                        info_logger("Update RazorpayPayments").info(f"Rows affected: {UpdateRazorPayQRCode.rowcount}, TRNNo={TRNNo}")

                        db.session.commit()
                        

                    else:
                        pass
                except Exception as e:
                    db.session.rollback()
                    error_logger("Update error").error(str(e))
                try:
                    #expiring existing payment link if any payment link active
                    expire_existing_payment_link = text("""
                                UPDATE Mobile_JFSL.Dbo.TransactionInfo
                                SET is_active = 0, Is_Delete = 1
                                WHERE (EGRNNo = :egrn AND DCNo = :trn)
                                 
                            """)

                    db.session.execute(expire_existing_payment_link, {"egrn": egrn, "trn": TRNNo})

                    db.session.commit()
                except Exception as e:
                    error_logger(f'Route: {request.path}').error(e)
            else:
                
                custom_message = "Payment Failed Please Try again..."
                final_data = generate_final_data('DATA_SAVE_FAILED',custom_message)

        else:
            final_data = generate_final_data('DATA_ALREADY_SAVED')
    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(payment_form.errors)
    log_data = {
        'final_data': final_data

    }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))

    return final_data

@delivery_blueprint.route('/get_order_garments_price', methods=["POST"])
# @authenticate('delivery_user')
def get_order_garments_price():
    """
    API for grouping order garments based on service tat and count.
    @return:
    """
    garments_price_form = GetOrderGarmentsPriceForm()
    if garments_price_form.validate_on_submit():
        BookingId = garments_price_form.BookingId.data
        actual_garment_split_up = None

        try:
            query = f""" JFSL.DBO.SPFabTempOrderGarmentWisePriceDtls @BookingID={BookingId}"""
            result = CallSP(query).execute().fetchall()

        except Exception as e:
            error_logger(f'Route: {request.path}').error(e)

        if len(result) > 0:
            final_data = generate_final_data('DATA_FOUND')
            final_data['result'] = result
        else:
            final_data = generate_final_data('DATA_NOT_FOUND')
    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(garments_price_form.errors)

    return final_data


# @delivery_blueprint.route('/get_order_garments_price', methods=["POST"])
# @authenticate('delivery_user')
# def get_order_garments_price():
#     """
#     API for grouping order garments based on service tat and count.
#     @return:
#     """
#     garments_price_form = GetOrderGarmentsPriceForm()
#     if garments_price_form.validate_on_submit():
#         order_id = garments_price_form.order_id.data
#         actual_garment_split_up = None

#         try:
#             # Getting the details from the DB.
#             split_up = db.session.query(Garment.GarmentName, ServiceTat.ServiceTatName.label('Service'),
#                                         func.count(OrderGarment.OrderGarmentId).label('Count'),
#                                         func.sum(OrderGarment.BasicAmount + OrderGarment.ServiceTaxAmount).label(
#                                             'Total'),

#                                         ).join(Garment, OrderGarment.GarmentId == Garment.GarmentId).join(ServiceTat,
#                                                                                                           OrderGarment.ServiceTatId == ServiceTat.ServiceTatId).filter(
#                 OrderGarment.OrderId == order_id, OrderGarment.IsDeleted == 0).group_by(OrderGarment.GarmentId,
#                                                                                         Garment.GarmentName,
#                                                                                         ServiceTat.ServiceTatName
#                                                                                         ).all()

#             actual_garment_split_up = SerializeSQLAResult(split_up).serialize()
#             # Getting garments count with darning from DB
#             darning_details = db.session.query(Garment.GarmentName, ServiceTat.ServiceTatName.label('Service'),
#                                                func.count(OrderGarment.OrderGarmentId).label('DarningCount'),
#                                                func.sum(OrderGarment.BasicAmount + OrderGarment.ServiceTaxAmount).label(
#                                                    'Total'), ).join(Garment,
#                                                                     OrderGarment.GarmentId == Garment.GarmentId).join(
#                 ServiceTat,
#                 OrderGarment.ServiceTatId == ServiceTat.ServiceTatId).join(OrderInstruction,
#                                                                            OrderGarment.OrderGarmentId == OrderInstruction.OrderGarmentId).filter(
#                 OrderGarment.OrderId == order_id, OrderGarment.IsDeleted == 0, OrderInstruction.IsDeleted == 0,
#                 OrderInstruction.InstructionId == 16).group_by(OrderGarment.GarmentId,
#                                                                Garment.GarmentName,
#                                                                ServiceTat.ServiceTatName
#                                                                ).all()

#             darning_details_dict = SerializeSQLAResult(darning_details).serialize()
#             # Proceed only if there is garments with darning VAS
#             if len(darning_details_dict) > 0:

#                 for obj1, obj2 in zip(darning_details_dict, actual_garment_split_up):
#                     # Checking garments with same value in both dict and having darning count in
#                     # darning_details_dict
#                     if obj2.get('GarmentName') == obj1.get('GarmentName') and obj2.get('Service') == obj1.get(
#                             'Service') and obj1.get('DarningCount') > 0:
#                         # Add darning count to actual_garment_split_up dict
#                         obj2['DarningCount'] = obj1.get('DarningCount')

#         except Exception as e:
#             error_logger(f'Route: {request.path}').error(e)

#         if len(actual_garment_split_up) > 0:
#             final_data = generate_final_data('DATA_FOUND')
#             final_data['result'] = actual_garment_split_up
#         else:
#             final_data = generate_final_data('DATA_NOT_FOUND')
#     else:
#         # Form validation error.
#         final_data = generate_final_data('FORM_ERROR')
#         final_data['errors'] = populate_errors(garments_price_form.errors)

#     return final_data


# @delivery_blueprint.route('/get_completed_activities', methods=["POST"])
# # @authenticate('delivery_user')
# def get_completed_activities():
#     """
#     API for getting the completed activities in a branch of a user.
#     @return:
#     """
#     completed_activities_form = GetCompletedActivitiesForm()
#     if completed_activities_form.validate_on_submit():
#         branch_codes = completed_activities_form.branch_codes.data
#         day_interval = completed_activities_form.day_interval.data
#         completed_only = completed_activities_form.completed_only.data
#         filter_type = None if completed_activities_form.filter_type.data == '' else completed_activities_form.filter_type.data
#         user_id = request.headers.get('user-id')
#         interval_start_date = None
#         if day_interval is not None:
#             from_date = (datetime.today() - timedelta(day_interval)).strftime("%Y-%m-%d %H:%M:%S")
#             # print(from_date)
#             to_date = get_current_date()
#             # print(to_date)

#         completed_activities = []
#         try:

#             if not branch_codes:
#                 # Getting the branches associated with the user.
#                 delivery_user_branches = delivery_controller_queries.get_delivery_user_branches(user_id)
#             else:
#                 # Branch codes are given.
#                 delivery_user_branches = branch_codes
#             branches = ','.join(delivery_user_branches)
#             log_data = {
#                 'BRANCHES :': branches
#             }
#             info_logger(f'Route: {request.path}').info(json.dumps(log_data))
#             if completed_only:
#                 status_type = 'COMPLETED'
#                 if (filter_type == None):
#                     # completed_activities_query = f"EXEC CustomerApp.dbo.PendingActivity @fromdate='{from_date}', @todate='{to_date}', @branch = '{branches}',@activitytype='',@Status_type = '{status_type}'"
#                     # completed_activities_query = f"EXEC CustomerApp.dbo.CompletedMobileActivity @fromdate='{from_date}', @todate='{to_date}', @branch = '{branches}',@activitytype='',@Status_type = '{status_type}'"
#                     completed_activities_query = f"EXEC CustomerApp.dbo.CompletedMobileActivity @DeliveryUsername= '{user_id}', @fromdate='{from_date}', @todate='{to_date}', @branch = '{branches}',@activitytype='',@Status_type = '{status_type}'"
#                 else:
#                     completed_activities_query = f"EXEC CustomerApp.dbo.CompletedMobileActivity @DeliveryUsername= '{user_id}', @fromdate='{from_date}', @todate='{to_date}', @branch = '{branches}',@activitytype='{filter_type}',@Status_type = '{status_type}'"
#                 completed_activities = CallSP(completed_activities_query).execute().fetchall()
#                 # print(pending_activities)
#                 log_data = {
#                     'completed_results :': completed_activities,
#                     'completed_qry :': completed_activities_query
#                 }
#                 info_logger(f'Route: {request.path}').info(json.dumps(log_data))

#                 # print(pending_activities)
#                 db.session.commit()
#             else:
#                 pass

#         except Exception as e:
#             error_logger(f'Route: {request.path}').error(e)
#         if completed_activities is not None:
#             final_data = generate_final_data('DATA_FOUND')
#             final_data['result'] = completed_activities


#         else:
#             final_data = generate_final_data('DATA_NOT_FOUND')
#     else:
#         # Form validation error.
#         final_data = generate_final_data('FORM_ERROR')
#         final_data['errors'] = populate_errors(completed_activities_form.errors)

#     return final_data


@delivery_blueprint.route('/get_completed_activities', methods=["POST"])
# @authenticate('delivery_user')
def get_completed_activities():
    """
    API for getting the completed activities in a branch of a user.
    @return:
    """
    completed_activities_form = GetCompletedActivitiesForm()
    if completed_activities_form.validate_on_submit():
        branch_codes = completed_activities_form.branch_codes.data
        day_interval = completed_activities_form.day_interval.data
        completed_only = completed_activities_form.completed_only.data
        filter_type = None if completed_activities_form.filter_type.data == '' else completed_activities_form.filter_type.data
        user_id = request.headers.get('user-id')
        interval_start_date = None
        if day_interval is not None:
            from_date = (datetime.today() - timedelta(day_interval)).strftime("%Y-%m-%d %H:%M:%S")
            # print(from_date)
            to_date = get_current_date()
            # print(to_date)

        completed_activities = []
        try:

            if not branch_codes:
                branch_codes = []
                query = f"EXEC JFSL.Dbo.SPGetDeliveryUserbranchMappingCustApp @Duserid='{user_id}'"
                delivery_user_branches = CallSP(query).execute().fetchall()

                if isinstance(delivery_user_branches, list):
                    for branch in delivery_user_branches:
                        if isinstance(branch, dict) and 'BranchCode' in branch:
                            branch_codes.append(branch['BranchCode'])
            else:
                # Branch codes are given.
                branch_codes = branch_codes
            branch_codes = ','.join(branch_codes)
            if completed_only:
                status_type = 'COMPLETED'
                if (filter_type == None):
                    completed_activities_query = f"EXEC JFSL.Dbo.SPFabCompletedMobileActivity @DeliveryUsername= '{user_id}', @fromdate='{from_date}', @todate='{to_date}', @branch = '{branch_codes}',@activitytype='',@Status_type = '{status_type}'"
                else:
                    completed_activities_query = f"EXEC JFSL.dbo.SPFabCompletedMobileActivity @DeliveryUsername= '{user_id}', @fromdate='{from_date}', @todate='{to_date}', @branch = '{branch_codes}',@activitytype='{filter_type}',@Status_type = '{status_type}'"
                completed_activities = CallSP(completed_activities_query).execute().fetchall()
                # print(pending_activities)
                log_data = {

                    'completed_qry :': completed_activities_query,
                    "completed_activities_form":completed_activities_form.data,
                 
                }
                info_logger(f'Route: {request.path}').info(json.dumps(log_data))

                # print(pending_activities)
                db.session.commit()
            else:
                pass

        except Exception as e:
            error_logger(f'Route: {request.path}').error(e)
        if completed_activities is not None:
            final_data = generate_final_data('DATA_FOUND')
            final_data['result'] = completed_activities


        else:
            final_data = generate_final_data('DATA_NOT_FOUND')
    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(completed_activities_form.errors)

    return final_data



@delivery_blueprint.route('/log_gps_position', methods=["POST"])
# @authenticate('delivery_user')
def log_gps_position():
    """
    API for saving the GPS position of the delivery user.
    @return:
    """
    save_position_form = SaveGPSPosition()
    if save_position_form.validate_on_submit():
        lat = save_position_form.lat.data
        long = save_position_form.long.data
        user_id = request.headers.get('user-id')
        saved = False
        try:
            # Saving the current GPS position.
            new_gps_position = DeliveryUserGPSLog(
                DUserId=user_id,
                Lat=lat,
                Long=long,
                RecordCreatedDate=get_current_date()
            )
            db.session.add(new_gps_position)
            db.session.commit()
            saved = True

        except Exception as e:
            error_logger(f'Route: {request.path}').error(e)
        notification_count = db.session.query(func.count(PushNotification.PushNotificationId)).filter(
            PushNotification.DUserId == user_id, PushNotification.IsRead == 0).scalar()
        if saved:
            final_data = generate_final_data('DATA_SAVED')
            final_data['PushNotificationCount'] = notification_count
        else:
            final_data = generate_final_data('DATA_SAVE_FAILED')
    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(save_position_form.errors)
    return final_data


# @delivery_blueprint.route('/send_payment_link', methods=["POST"])
# @authenticate('delivery_user')
# def send_payment_link():
#     """
#     Function to prevent expiring payment link,
#     API for sending the payment link to the customer.
#     @return:
#     """
#     payment_link_form = SendPaymentLinkForm()
#     if payment_link_form.validate_on_submit():
#         order_id = payment_link_form.order_id.data
#         mobile_number = payment_link_form.mobile_number.data
#         send_status = False
#         payment_link = ''
#         sender = "FABSPA"
#         head = "Fabricspa"
#         try:
#             # Getting the EGRN details from the DB.
#             # egrn_details = db.session.query(Order.EGRN).filter(Order.OrderId == order_id,
#             #                                                    Order.IsDeleted == 0).one_or_none()
#             # Edited by MMM
#             egrn_details = db.session.query(Order.EGRN, Customer.CustomerCode, Customer.CustomerId).join(Customer,
#                                                                                                          Customer.CustomerId == Order.CustomerId).filter(
#                 Order.OrderId == order_id, Order.IsDeleted == 0).one_or_none()
#             # Edited by MMM
#             if egrn_details is not None:
#                 customer_code = egrn_details.CustomerCode
#                 order_egrn = egrn_details.EGRN

#                 amount_dtls = delivery_controller_queries.get_payable_amount_via_sp(
#                     customer_code,
#                     order_egrn)
#                 if amount_dtls and 'PAYABLEAMOUNT' in amount_dtls:
#                     amount = amount_dtls['PAYABLEAMOUNT']
#                 else:
#                     amount = 0  # Or handle the error


#                 headers = {'Content-Type': 'application/json', 'api_key': PAYMENT_LINK_API_KEY}

#                 # Based on the environment, API URL will be changed.
#                 if CURRENT_ENV == 'development':
#                     api_url = 'https://appuat.fabricspa.com/UAT/jfsl/api/generate_payment_link'
#                 else:
#                     #api_url = 'https://intapps.fabricspa.com/jfsl/api/generate_payment_link'
#                     api_url = 'https://intapps.fabricspa.com/jfsl/api/generate_payment_link'

#                 # json_request = {'egrn': egrn_details.EGRN}
#                 json_request = {'egrn': egrn_details.EGRN, 'source_from': 'Fabxpress'}

#                 # Calling the API.
#                 response = requests.post(api_url, data=json.dumps(json_request), headers=headers)

#                 response = json.loads(response.text)
#                 if response:
#                     # A valid response has been received.
#                     if response['status'] == "success":
#                         # Link generation is successful.
#                         payment_link = response['url']

#                     query = f"EXEC CustomerApp.[dbo].[GetBrandName] @BranchCode='NULL', @EGRNNo={order_egrn}, @PickupRequestId=NULL"
#                     brand_details = CallSP(query).execute().fetchone()
#                     log_data = {
#                         'query of brand': query,
#                         'result of brand': brand_details if brand_details else "No results"
#                     }
#                     info_logger(f'Route: {request.path}').info(json.dumps(log_data))
#                     if brand_details and brand_details["BrandDescription"] != 'FABRICSPA':
#                         sender = brand_details["BrandDescription"]
#                         # print(sender)
#                         head = "QUICLO"
#                         sp_query = f"EXEC JFSL.dbo.GenerateUniqueCombination @longurl='{payment_link}', @Source='FabxpressPaymentLink', @brand='{sender}', @DocumentType='EGRN', @DocumentNo='{order_egrn}'"
#                         log_data = {
#                             'query of links': sp_query
#                         }
#                         info_logger(f'Route: {request.path}').info(json.dumps(log_data))
#                         sp_result = CallSP(sp_query).execute().fetchone()

#                         log_data = {
#                             'query of link': sp_query,
#                             'result of link': sp_result 
#                         }
#                         info_logger(f'Route: {request.path}').info(json.dumps(log_data))

#                         if sp_result:
#                             # payment_link = sp_result
#                             payment_link =  sp_result.get('GeneratedCombination')
#                             log_data = {
#                             'payment_link': payment_link,
                        
#                             }
#                             info_logger(f'Route: {request.path}').info(json.dumps(log_data))
#                     else:
#                         pass



#                     if payment_link:
#                         message = f'{head} has now made the payment process easier, click here {payment_link} to ' \
#                                   f'complete the payment of Rs {amount}/- from anywhere you are.'
#                         sms = send_sms(mobile_number, message, egrn_details.CustomerId, sender)
#                         log_data = {
#                             'customer_id': egrn_details.CustomerId
#                         }
#                         info_logger(f'Route: {request.path}').info(json.dumps(log_data))

#                         if sms['result']:
#                             if sms['result'].get('status') == "OK":
#                                 send_status = True

#                                 # Edited by MMM
#                                 trn_no = delivery_controller_queries.get_payable_amount_via_sp(
#                                     egrn_details.CustomerCode, egrn_details.EGRN)
#                                 delivery_controller_queries.get_trno_toexpire_paylinlk(trn_no['DCNO'])
#                                 # Edited by MMM

#         except Exception as e:
#             error_logger(f'Route: {request.path}').error(e)

#         if send_status:
#             final_data = generate_final_data('SUCCESS')
#             final_data['result'] = payment_link
#         else:
#             final_data = generate_final_data('FAILED')

#     else:
#         # Form validation error.
#         final_data = generate_final_data('FORM_ERROR')
#         final_data['errors'] = populate_errors(payment_link_form.errors)
#     log_data = {
#         'final_data': final_data
#                             }
#     info_logger(f'Route: {request.path}').info(json.dumps(log_data))
#     return final_data

@delivery_blueprint.route('/send_payment_link', methods=["POST"])
# @authenticate('delivery_user')
def send_payment_link():
    """
    Function to prevent expiring payment link,
    API for sending the payment link to the customer.
    @return:
    """
    payment_link_form = SendPaymentLinkForms()
    if payment_link_form.validate_on_submit():
        CustomerCode = payment_link_form.CustomerCode.data
        TRNNo = payment_link_form.TRNNo.data
        EGRN = payment_link_form.EGRN.data
        MobileNumber = payment_link_form.MobileNumber.data
        send_status = False
        payment_link = ''
        sender = "FABSPA"
        head = "Fabricspa"
        CouponCode = ""
        try:
            egrn = EGRN
            result = payment_module.get_available_coupon_codes(egrn)
            amount_dtls = delivery_controller_queries.get_payable_amount_via_sp(
                CustomerCode,
                TRNNo)
            if amount_dtls and 'PAYABLEAMOUNT' in amount_dtls:
                PayableAmount = amount_dtls['PAYABLEAMOUNT']
                coupon_details = db.session.execute(
                    text("SELECT Couponcode FROM JFSL.dbo.OrderInfo WHERE EGRNNo = :egrn"),
                    {"egrn": egrn}
                ).fetchone()
                if coupon_details is not None:
                    expected_coupon_code = coupon_details[0]
                    all_coupons = payment_module.get_available_coupon_codes(egrn)

                    # Filter only the coupon that matches the one in OrderInfo
                    if isinstance(all_coupons, list):
                        matching_coupons = [
                            coupon for coupon in all_coupons 
                            if str(coupon.get("COUPONCODE")) == str(expected_coupon_code)
                        ]
                        if matching_coupons:
                            discount_amount = matching_coupons[0].get('DISCOUNTAMOUNT', 0)
                            CouponCode = matching_coupons[0].get('COUPONCODE', '')
                            amount = PayableAmount - discount_amount
                        else:
                            amount = PayableAmount
                            CouponCode = ""


                else:
                    amount = PayableAmount
                    CouponCode = ""
            user_info = db.session.execute(
                            text("SELECT DUserId FROM JFSL.dbo.FabDeliveryInfo WHERE EGRNNo = :egrn"),
                            {"egrn": EGRN}
                        ).fetchone()
            DUserId = user_info[0] if user_info and user_info[0] else None

            

            headers = {'Content-Type': 'application/json', 'api_key': PAYMENT_LINK_API_KEY}

            # Based on the environment, API URL will be changed.
            if CURRENT_ENV == 'development':
                api_url = 'https://appuat.fabricspa.com/UAT/jfsl/api/generate_payment_link'
            else:
                api_url = 'https://intapps.fabricspa.com/jfsl/api/generate_payment_link'
                #api_url = 'https://app-staging.fabricspa.com/jfsl/api/generate_payment_link'

            # json_request = {'egrn': egrn_details.EGRN}
            json_request = {'egrn': EGRN, 'source_from': 'Fabxpress' ,"coupons_attached_to_order":[CouponCode]}

            if DUserId:
                json_request['duserid'] = str(DUserId)


            # Calling the API.
            response = requests.post(api_url, data=json.dumps(json_request), headers=headers)
            response = json.loads(response.text)
            log_data = {
                        'response': response,
                        "json_request":json_request
                       
                    }
            info_logger(f'Route: {request.path}').info(json.dumps(log_data))

            if response:
                log_data = {
                        'response': "sp_query",
                       
                    }
                info_logger(f'Route: {request.path}').info(json.dumps(log_data))
                # A valid response has been received.
                if response['status'] == "success":
                    # Link generation is successful.
                    payment_link = response['url']

                query = f"EXEC CustomerApp.[dbo].[GetBrandName] @BranchCode='NULL', @EGRNNo={EGRN}, @PickupRequestId=NULL"
                brand_details = CallSP(query).execute().fetchone()

                if brand_details and brand_details["BrandDescription"] != 'FABRICSPA':
                    sender = brand_details["BrandDescription"]
                    # print(sender)
                    head = "QUICLO"
                    sp_query = f"EXEC JFSL.dbo.GenerateUniqueCombination @longurl='{payment_link}', @Source='FabxpressPaymentLink', @brand='{sender}', @DocumentType='EGRN', @DocumentNo='{EGRN}'"
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
                        payment_link = sp_result.get('GeneratedCombination')
                      
                        log_data = {
                            'payment_link': payment_link,

                        }
                        info_logger(f'Route: {request.path}').info(json.dumps(log_data))
                else:
                    pass

                if payment_link:
                    message = f'{head} has now made the payment process easier, click here {payment_link} to ' \
                              f'complete the payment of Rs {amount}/- from anywhere you are.'
                    sms = send_sms(MobileNumber, message,'', sender)


                    if sms['result']:
                        if sms['result'].get('status') == "OK":
                            send_status = True

                            # Edited by MMM
                            trn_no = delivery_controller_queries.get_payable_amount_via_sp(
                                CustomerCode, TRNNo)
                            delivery_controller_queries.get_trno_toexpire_paylinlk(trn_no['DCNO'])
                            # Edited by MMM

        except Exception as e:
            error_logger(f'Route: {request.path}').error(e)

        if send_status:
            final_data = generate_final_data('SUCCESS')
            final_data['result'] = payment_link
        else:
            final_data = generate_final_data('FAILED')

    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(payment_link_form.errors)
    log_data = {
        'final_data': final_data
    }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))
    return final_data

@delivery_blueprint.route('/send_payment_linklive', methods=["POST"])
@authenticate('delivery_user')
def send_payment_linklive():
    """
    Function to prevent expiring payment link,
    API for sending the payment link to the customer.
    @return:
    """
    payment_link_form = SendPaymentLinkForm()
    if payment_link_form.validate_on_submit():
        order_id = payment_link_form.order_id.data
        mobile_number = payment_link_form.mobile_number.data
        send_status = False
        payment_link = ''
        sender = "FABSPA"
        try:
            # Getting the EGRN details from the DB.
            # egrn_details = db.session.query(Order.EGRN).filter(Order.OrderId == order_id,
            #                                                    Order.IsDeleted == 0).one_or_none()
            # Edited by MMM
            egrn_details = db.session.query(Order.EGRN, Customer.CustomerCode, Customer.CustomerId).join(Customer,
                                                                                                         Customer.CustomerId == Order.CustomerId).filter(
                Order.OrderId == order_id, Order.IsDeleted == 0).one_or_none()
            # Edited by MMM
            if egrn_details is not None:
                customer_code = egrn_details.CustomerCode
                order_egrn = egrn_details.EGRN

                amount_dtls = delivery_controller_queries.get_payable_amount_via_sp(
                    customer_code,
                    order_egrn)
                if amount_dtls and 'PAYABLEAMOUNT' in amount_dtls:
                    amount = amount_dtls['PAYABLEAMOUNT']
                else:
                    amount = 0  # Or handle the error

                headers = {'Content-Type': 'application/json', 'api_key': PAYMENT_LINK_API_KEY}

                # Based on the environment, API URL will be changed.

                if CURRENT_ENV == 'development':
                    api_url = 'https://appuat.fabricspa.com/UAT/jfsl/api/generate_payment_link'
                else:
                    api_url = 'https://intapps.fabricspa.com/jfsl/api/generate_payment_link'
                    # api_url = 'https://app-staging.fabricspa.com/jfsl/api/generate_payment_link'

                # json_request = {'egrn': egrn_details.EGRN}
                json_request = {'egrn': egrn_details.EGRN, 'source_from': 'Fabxpress'}

                # Calling the API.
                response = requests.post(api_url, data=json.dumps(json_request), headers=headers)

                response = json.loads(response.text)
                if response:
                    # A valid response has been received.
                    if response['status'] == "success":
                        # Link generation is successful.
                        payment_link = response['url']
                        query = f"EXEC CustomerApp.[dbo].[GetBrandName] @BranchCode='NULL', @EGRNNo={order_egrn}, @PickupRequestId=NULL"
                        brand_details = CallSP(query).execute().fetchone()
                        log_data = {
                            'query of brand': query,
                            'result of brand': brand_details if brand_details else "No results"
                        }
                        info_logger(f'Route: {request.path}').info(json.dumps(log_data))
                        if brand_details and brand_details["BrandDescription"] == 'QUICLO':
                            sender = "QUICLO"
                           
                            message = f'Quiclo has now made the payment process easier, click here {payment_link} to ' \
                                      f'complete the payment of Rs {amount}/- from anywhere you are.'
                        else:

                            # Now sending the SMS to the mobile number.
                            message = f'Fabricspa has now made the payment process easier, click here {payment_link} to ' \
                                      f'complete the payment of Rs {amount}/- from anywhere you are.'
                        sms = send_sms(mobile_number, message, egrn_details.CustomerId,sender)
                        log_data = {
                            'customer_id': egrn_details.CustomerId
                        }
                        info_logger(f'Route: {request.path}').info(json.dumps(log_data))

                        if sms['result']:
                            if sms['result'].get('status') == "OK":
                                send_status = True

                                # Edited by MMM
                                trn_no = delivery_controller_queries.get_payable_amount_via_sp(
                                    egrn_details.CustomerCode, egrn_details.EGRN)
                                delivery_controller_queries.get_trno_toexpire_paylinlk(trn_no['DCNO'])
                                # Edited by MMM

        except Exception as e:
            error_logger(f'Route: {request.path}').error(e)

        if send_status:
            final_data = generate_final_data('SUCCESS')
            final_data['result'] = payment_link
        else:
            final_data = generate_final_data('FAILED')

    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(payment_link_form.errors)
    return final_data



@delivery_blueprint.route('/send_payment_linkold', methods=["POST"])
@authenticate('delivery_user')
def send_payment_linkold():
    """
    Function to prevent expiring payment link,
    API for sending the payment link to the customer.
    @return:
    """
    payment_link_form = SendPaymentLinkForm()
    if payment_link_form.validate_on_submit():
        order_id = payment_link_form.order_id.data
        mobile_number = payment_link_form.mobile_number.data
        send_status = False
        payment_link = ''
        try:
            # Getting the EGRN details from the DB.
            # egrn_details = db.session.query(Order.EGRN).filter(Order.OrderId == order_id,
            #                                                    Order.IsDeleted == 0).one_or_none()
            # Edited by MMM
            egrn_details = db.session.query(Order.EGRN, Customer.CustomerCode, Customer.CustomerId).join(Customer,
                                                                                                         Customer.CustomerId == Order.CustomerId).filter(
                Order.OrderId == order_id, Order.IsDeleted == 0).one_or_none()
            # Edited by MMM
            if egrn_details is not None:

                headers = {'Content-Type': 'application/json', 'api_key': PAYMENT_LINK_API_KEY}

                # Based on the environment, API URL will be changed.
                if CURRENT_ENV == 'development':
                    api_url = 'https://appuat.fabricspa.com/UAT/jfsl/api/generate_payment_link'
                else:
                    api_url = 'https://intapps.fabricspa.com/jfsl/api/generate_payment_link'
                    # api_url = 'https://app-staging.fabricspa.com/jfsl/api/generate_payment_link'

                # json_request = {'egrn': egrn_details.EGRN}
                json_request = {'egrn': egrn_details.EGRN, 'source_from': 'Fabxpress'}

                # Calling the API.
                response = requests.post(api_url, data=json.dumps(json_request), headers=headers)

                response = json.loads(response.text)
                if response:
                    # A valid response has been received.
                    if response['status'] == "success":
                        # Link generation is successful.
                        payment_link = response['url']
                        # Now sending the SMS to the mobile number.
                        message = f'Fabricspa has now made the payment process easier, click here {payment_link} and ' \
                                  f'complete the payment from anywhere you are. For query call 18001234664. '
                        sms = send_sms(mobile_number, message, egrn_details.CustomerId)
                        log_data = {
                            'customer_id': egrn_details.CustomerId
                        }
                        info_logger(f'Route: {request.path}').info(json.dumps(log_data))

                        if sms['result']:
                            if sms['result'].get('status') == "OK":
                                send_status = True

                                # Edited by MMM
                                trn_no = delivery_controller_queries.get_payable_amount_via_sp(
                                    egrn_details.CustomerCode, egrn_details.EGRN)
                                delivery_controller_queries.get_trno_toexpire_paylinlk(trn_no['DCNO'])
                                # Edited by MMM

        except Exception as e:
            error_logger(f'Route: {request.path}').error(e)

        if send_status:
            final_data = generate_final_data('SUCCESS')
            final_data['result'] = payment_link
        else:
            final_data = generate_final_data('FAILED')

    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(payment_link_form.errors)
    return final_data


@delivery_blueprint.route('/send_waiting_sms', methods=["POST"])
# @authenticate('delivery_user')
def send_waiting_sms():
    """
    API for sending SMS to customer notifying that the delivery user is waiting
    for the customer at the location for pickup/delivery.
    @return:
    """
    waiting_sms_form = SendWaitingSMSForm()
    if waiting_sms_form.validate_on_submit():
        mobile_number = waiting_sms_form.mobile_number.data
        sms_template_id = waiting_sms_form.sms_template_id.data
        lat = None if waiting_sms_form.lat.data == '' else waiting_sms_form.lat.data
        long = None if waiting_sms_form.long.data == '' else waiting_sms_form.long.data
        customer_code = None if waiting_sms_form.customer_code.data == '' else waiting_sms_form.customer_code.data
       
        activity_type = None if waiting_sms_form.activity_type.data == '' else waiting_sms_form.activity_type.data
        #TRNNo = '' if waiting_sms_form.TRNNo.data == '' else waiting_sms_form.TRNNo.data
        TRNNo = None if waiting_sms_form.TRNNo.data in ('', 'NA') else waiting_sms_form.TRNNo.data
        BookingId = None if waiting_sms_form.BookingIDString.data in ('', 'NA') else waiting_sms_form.BookingIDString.data
        #BookingId = None if waiting_sms_form.BookingIDString.data == '' else waiting_sms_form.BookingIDString.data
        branch_code = None if waiting_sms_form.branch_code.data == '' else waiting_sms_form.branch_code.data
        user_id = request.headers.get('user-id')
        send_status = False
        message = None
        pickup_request_id = None
        delivery_request_id = None
        sender = ""
        # branch_code = "SPEC000001"
       
        query = f"EXEC CustomerApp.[dbo].[GetBrandName] @BranchCode='{branch_code}', @EGRNNo=NULL, @PickupRequestId=NULL"
        brand_details = CallSP(query).execute().fetchone()
        log_data = {
                "activity_type":activity_type,
                'query of brand': query,
                'result of brand': brand_details,
                'branch_code':branch_code,
                "waiting_sms_form":waiting_sms_form.data
            }
        info_logger(f'Route: {request.path}').info(json.dumps(log_data))

        if brand_details["BrandDescription"] == 'QUICLO':
            sender = 'QUICLO'
        else:
            sender = 'FABSPA'

        try:
            message = db.session.query(MessageTemplate.MessageContent).filter(MessageTemplate.Id == sms_template_id,
                                                                              MessageTemplate.IsDeleted == 0).one_or_none()

            if message is not None:
                # Sending the SMS to the customer.
                # if CURRENT_ENV == 'production':
                #     sms = send_sms(mobile_number, message.MessageContent, '')

                # else:
                #     sms = {'result': {'status': "OK"}}
                sms = send_sms_laundry(mobile_number, message.MessageContent, '',sender)

                if sms['result']:
                    if sms['result'].get('status') == "OK":
                        # SMS have been sent successfully.
                        send_status = True

                        db.session.execute(text("""
                            INSERT INTO JFSL.Dbo.FabMessageLogs (
                                CustomerCode, DUserId, BookingID, TRNNo, MessageTemplateId, MobileNo, Lat, Long, RecordCreatedDate, RecordLastUpdatedDate, RecordVersion
                            )
                            VALUES (
                                :customer_code, :user_id, :BookingId, :TRNNo, :sms_template_id, :mobile_number, :lat, :long, GETDATE(), GETDATE(), 0
                            )
                        """), {
                            "customer_code": customer_code,
                            "user_id": user_id,
                            "BookingId": BookingId,
                            "TRNNo": TRNNo,
                            "sms_template_id": sms_template_id,
                            "mobile_number": mobile_number,
                            "lat": lat,
                            "long": long
                        })

                        db.session.commit()

        except Exception as e:
            db.session.rollback()
            error_logger(f'Route: {request.path}').error(e)

        if send_status:
            final_data = generate_final_data('SUCCESS')
        else:
            final_data = generate_final_data('FAILED')
    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(waiting_sms_form.errors)
    return final_data


@delivery_blueprint.route('/get_lp', methods=["POST"])
@authenticate('delivery_user')
def get_lp():
    """
    API for getting the loyalty points of a customer based on EGRN.
    @return:
    """
    lp_form = GetLPForm()
    if lp_form.validate_on_submit():

        customer_code = lp_form.customer_code.data
        egrn = lp_form.egrn.data

        # Getting the loyalty points based on a customer code.
        loyalty_points = payment_module.get_lp(customer_code, egrn)

        if loyalty_points:
            final_data = generate_final_data('DATA_FOUND')
            final_data['result'] = loyalty_points
        else:
            final_data = generate_final_data('NO_DATA_FOUND')

    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(lp_form.errors)

    return final_data


@delivery_blueprint.route('/sms_templates_quiclo', methods=["POST"])
# @authenticate('delivery_user')
def sms_templates_quiclo():
    """
    API for getting the predefined SMS templates.
    @return:
    """
    sms_form = SmsForm()
    log_data = {
        "sms ": sms_form.data
    }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))

    if sms_form.validate_on_submit():
        branch_code = sms_form.branch_code.data
        templates = []
        brand = None
        query = f"EXEC CustomerApp.[dbo].[GetBrandName] @BranchCode='{branch_code}', @EGRNNo=NULL, @PickupRequestId=NULL"
        brand_details = CallSP(query).execute().fetchone()
        brand = brand_details["BrandDescription"]
        try:
            # Getting the message templates from the DB.
            templates = db.session.query(MessageTemplate.Id, MessageTemplate.Title, MessageTemplate.MessageContent,MessageTemplate.Brand).filter(
                MessageTemplate.IsDeleted == 0,MessageTemplate.Brand == brand).all()
        except Exception as e:
            error_logger(f'Route: {request.path}').   error(e)

        if templates:
            final_data = generate_final_data('DATA_FOUND')
            final_data['result'] = SerializeSQLAResult(templates).serialize()
        else:
            final_data = generate_final_data('DATA_NOT_FOUND')
    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(sms_form.errors)
    log_data = {
        "sms ": final_data
    }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))
    return final_data

@delivery_blueprint.route('/sms_templates', methods=["GET"])
@authenticate('delivery_user')
def sms_templates():
    """
    API for getting the predefined SMS templates.
    @return:
    """
    templates = []
    try:
        # Getting the message templates from the DB.
        templates = db.session.query(MessageTemplate.Id, MessageTemplate.Title, MessageTemplate.MessageContent).filter(
            MessageTemplate.IsDeleted == 0).all()
    except Exception as e:
        error_logger(f'Route: {request.path}').error(e)

    if templates:
        final_data = generate_final_data('DATA_FOUND')
        final_data['result'] = SerializeSQLAResult(templates).serialize()
    else:
        final_data = generate_final_data('DATA_NOT_FOUND')
    
    return final_data


@delivery_blueprint.route('/calculate_payable_amount', methods=["POST"])
@authenticate('delivery_user')
def calculate_payable_amount():
    """
    API for calculating the payment amount after applying the coupon code, LP..etc.
    @return:
    """
    calculate_form = CalculatePayableAmountForm()
    if calculate_form.validate_on_submit():
        order_id = calculate_form.order_id.data
        coupons = calculate_form.coupons.data
        lp = calculate_form.lp.data
        delivery_request_id = calculate_form.delivery_request_id.data
        payable_amount = 0
        applied_coupons = []
        error_msg = ''
        result = False
        lp_applied = False
        try:
            # Getting the essential delivery request details from the DB.
            essentials = delivery_controller_queries.get_essential_data_for_payment(delivery_request_id, order_id)
            if essentials:
                if essentials['egrn_details']['initial_amount'] > 0:
                    # Getting the payable amount of the order after considering the pre applied
                    # coupons/lp/discount..etc.
                    # Calculating the payable amount after considering any
                    # pre applied coupons/invoice discount/LPs...etc.
                    egrn = essentials['egrn']
                    initial_amount = essentials['egrn_details']['initial_amount']
                    pos_order_garment_ids = essentials['pos_order_garment_ids']
                    customer_code = essentials['customer_code']
                    after_pre_applied = payment_module.deduct_pre_applied_coupons_and_discounts(egrn, initial_amount,
                                                                                                pos_order_garment_ids)
                    if after_pre_applied['amount_to_pay'] > 0:
                        payable_amount = after_pre_applied['amount_to_pay']
                        if coupons:
                            # Compensation coupons are provided in the request.
                            for coupon in coupons:
                                coupon_details = payment_module.get_coupon_details(coupon, egrn)
                                if payable_amount - float(coupon_details['DISCOUNTAMOUNT']) >= 0:
                                    # The coupon amount is less than the payable amount. So deduct the coupon
                                    # amount from the payable amount to get the new coupon amount.
                                    payable_amount -= float(coupon_details['DISCOUNTAMOUNT'])
                                    applied_coupons.append(coupon_details)
                                else:
                                    # Coupon can be cover the whole amount.
                                    payable_amount = 0
                                    applied_coupons.append(coupon_details)
                                    break

                        if payable_amount > 0:
                            # After considering the coupons, if LP is need to apply, considering
                            # redeeming the loyalty points too.
                            if lp:
                                # Getting the LP based on EGRN.
                                lp_from_egrn = er_module.queries.get_lp_from_egrn(egrn)

                                if lp_from_egrn['IsAlreadyApplied'] == 0 and lp_from_egrn['SelfAttached'] == 0:
                                    # Consider the LP from the API itself.
                                    lp_from_er = er_module.get_available_er_lp(customer_code)
                                    available_points = lp_from_er['available_points']
                                    point_rate = lp_from_er['point_rate']

                                    if payable_amount - (available_points * point_rate) > 0:
                                        payable_amount -= float(available_points * point_rate)
                                        lp_applied = True
                                    else:
                                        # The payable amount can be redeemed fully via loyalty points.
                                        payable_amount = 0
                                        lp_applied = True
                                else:
                                    # Loyalty points is already applied. Can not apply anymore.
                                    error_msg = 'Loyalty points is already applied.'
                        result = True
                    else:
                        error_msg = 'The order can fully be redeemed by pre applied coupons,LPs..etc.'
                else:
                    error_msg = 'The order is either settled or has a complaint.'
            else:
                error_msg = 'Failed to get any essential data.'

        except Exception as e:
            error_logger(f'Route: {request.path}').error(e)

        if result:
            final_data = generate_final_data('DATA_FOUND')
            result = {
                'PayableAmount': payable_amount,
                'AppliedCoupons': applied_coupons,
                'LPApplied': lp_applied
            }
            final_data['result'] = result
        else:
            if error_msg:
                final_data = generate_final_data('CUSTOM_FAILED', error_msg)
            else:
                final_data = generate_final_data('DATA_SAVE_FAILED')
    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(calculate_form.errors)

    return final_data


@delivery_blueprint.route('/save_remarks', methods=["POST"])
@authenticate('delivery_user')
def save_remarks():
    """
    API for saving the remarks while creating a adhoc pickup.
    @return:
    """
    save_remarks_form = SaveRemarksForm()
    if save_remarks_form.validate_on_submit():
        pickup_request_id = save_remarks_form.pickup_request_id.data
        remarks = save_remarks_form.remarks.data
        saved = False
        try:
            # Getting the pickup request details.
            pickup_request = db.session.query(PickupRequest).filter(PickupRequest.PickupRequestId == pickup_request_id,
                                                                    PickupRequest.IsCancelled == 0).one_or_none()

            if pickup_request is not None:
                # A pickup request is found. Saving the Remarks into the PickupRequests table.
                pickup_request.Remarks = remarks
                db.session.commit()
                saved = True
        except Exception as e:
            error_logger(f'Route: {request.path}').error(e)

        if saved:
            final_data = generate_final_data('DATA_SAVED')
        else:
            final_data = generate_final_data('DATA_NOT_SAVED')
    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(save_remarks_form.errors)

    return final_data


@delivery_blueprint.route('/get_available_service_types', methods=["POST"])
# @authenticate('delivery_user')
def get_available_service_types():
    """
    API for getting the available service types based on garment id and branch code.
    @return:
    """
    service_types_form = GetAvailableServiceTypesForm()
    if service_types_form.validate_on_submit():
        service_types = []
        try:
            query = f" EXEC JFSL.dbo.SPServiceTypesCustApp"
            service_types = CallSP(query).execute().fetchall()

        except Exception as e:
            error_logger(f'Route: {request.path}').error(e)

        if service_types:
            final_data = generate_final_data('DATA_FOUND')
            final_data['result'] = service_types
        else:
            final_data = generate_final_data('DATA_NOT_FOUND')
    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(service_types_form.errors)

    return final_data



@delivery_blueprint.route('/update_garment_measurement', methods=["PUT"])
@authenticate('delivery_user')
def update_garment_measurement():
    """
    If the garment has sq.ft as the measurement, length and width of the
    order garment can be updated.
    @return:
    """
    measurement_form = UpdateGarmentMeasurementForm()
    log_data = {
    "measurement_form": measurement_form.data
                    }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))
    if measurement_form.validate_on_submit():
        order_garment_id = measurement_form.order_garment_id.data
        length = measurement_form.length.data
        width = measurement_form.width.data
        updated = False
        print(length)
        print(width)
        try:
            sq_ft = length * width
            db.session.execute(
                text("""
                   UPDATE JFSL.dbo.FABTemporderGarments 
                   SET Length = :length,
                   Width = :width,
                   Sqft = :sq_ft
                   WHERE OrderGarmentID = :order_garment_id
                            """),
                {"order_garment_id": order_garment_id, "sq_ft": sq_ft,"width":width,"length":length}
            )
            db.session.commit()

            updated = True
        except Exception as e:
            error_logger(f'Route: {request.path}').error(e)

        if updated:
            final_data = generate_final_data('DATA_UPDATED')
        else:
            final_data = generate_final_data('DATA_NOT_FOUND')
    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(measurement_form.errors)
    log_data = {
    "final_data": final_data
                    }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))
    return final_data



@delivery_blueprint.route('/get_service_tat_id', methods=["POST"])
# @authenticate('delivery_user')
def get_service_tat_id():
    get_service_tat_form = GetServiceTatForm()

    result = False
    if get_service_tat_form.validate_on_submit():
        branch_code = get_service_tat_form.branch_code.data
        service_tat = []
        try:

            # Select service tat icon if available, else select "NA".
            query = f""" EXEC JFSL.DBO.SPBranchServiceTatsCustApp @BRANCHCODE= '{branch_code}'"""

            service_tat = CallSP(query).execute().fetchall()
            print(service_tat)
            if service_tat is not None:
                service_tat = [
                    {
                        "ServiceTatId": item["ServiceTatId"],
                        "ServiceTatName": item["ServiceTatName"],
                        "ServiceTatIcon": item["ServiceTatName"].lower()
                    }
                    for item in service_tat
                ]
                result = True


        except Exception as e:
            error_logger(f'Route: {request.path}').error(e)

        if result:
            final_data = generate_final_data('DATA_FOUND')
            final_data['result'] = service_tat
        else:
            final_data = generate_final_data('DATA_NOT_FOUND')
    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(get_service_tat_form.errors)
    return final_data




@delivery_blueprint.route('/get_tag_details_beforevalidation', methods=["POST"])
# @authenticate('delivery_user')
def get_tag_details_beforevalidation():
    get_tag_details_form = GetTagDetailsForm()
    if get_tag_details_form.validate_on_submit():
        tag_id = get_tag_details_form.tag_id.data
        mobile_number = get_tag_details_form.mobile_number.data
        branch_code = get_tag_details_form.branch_code.data
        # EGRN = get_tag_details_form.EGRN.data
        error_msg = None
        order_garments = []
        complaint_id = 0
        complaint_type = "NA"
        complaint_status = "NA"
        ameyo_ticket_id = "NA"
        assigned_dept = "NA"
        rewash_status = False
        complaint_details = None
        crm_complaint_status = False
        start_date = datetime.today() - timedelta(days=90)

        try:

            query = f"EXEC {SERVER_DB}.dbo.GetGarmentStatus @tagno = {tag_id}"
            tag_status = CallSP(query).execute().fetchone()
            log_data = {
                        'tag_status': tag_status
                                        }
            info_logger(f'Route: {request.path}').info(json.dumps(log_data))
            if tag_status['Status'] == 'Invoiced & Delivered' or tag_status['Status'] == 'Transfer in at CDC':

                query = f"EXEC {SERVER_DB}.dbo.USP_CheckTagTypeForRewash @tagno={tag_id}"
                normal_tag = CallSP(query).execute().fetchone()
                log_data = {
                        'normal_tag': normal_tag
                                        }
                info_logger(f'Route: {request.path}').info(json.dumps(log_data))
                if normal_tag['Tag Type'] == 'Normal_Tag':

                    ameyo_customer_id = ameyo_module.get_ameyo_customer_id(mobile_number)
                    if ameyo_customer_id:
                        

                        query = f""" EXEC JFSL.Dbo.SPFabComplaintResolutionCheck @TagNo = {tag_id}"""
                        complaint_details = CallSP(query).execute().fetchall()
                        log_data = {
                        'complaint_details': complaint_details
                                        }
                        info_logger(f'Route: {request.path}').info(json.dumps(log_data))
                        EGRN = complaint_details[0].get('OLDEGRN', "NA")
                        garment_complaint = ameyo_module.check_complaint_garment(tag_id, EGRN)
                        print(garment_complaint)
                        complaint = 0 if not garment_complaint['Complaint'] else 1
                        rewash_count = garment_complaint['RewashCount']


                        if complaint_details is not None:
                            complaint_id = complaint_details[0].get('Id')

                            if complaint_details and complaint_details[0].get('ComplaintType'):
                                complaint_type = complaint_details[0]['ComplaintType']
                            else:
                                complaint_type = "NA"
                            # Check if complaint_details is a list and has at least one record
                            if complaint_details and isinstance(complaint_details, list) and len(complaint_details) > 0:
                                ameyo_ticket_id = complaint_details[0].get('JFSLTicketId', "NA") or "NA"
                                complaint_status = complaint_details[0].get('CrmComplaintStatus', "NA")
                                if complaint_status == '0':
                                    complaint_status = 'NA'
                            else:
                                ameyo_ticket_id = "NA"
                                complaint_status = "NA"

                            # Check if complaint_details is a list with at least one record
                            # Check if complaint_details is a list with at least one record
                            if complaint_details and isinstance(complaint_details, list) and len(complaint_details) > 0:
                                assigned_dept = complaint_details[0].get('AssignedDept', "NA") or "NA"
                                assigned_user_id = complaint_details[0].get('AssignedUserId')

                                if assigned_dept == 'OPERATIONS' and assigned_user_id is not None:
                                    assigned_dept = 'CRMOPERATIONS'
                            else:
                                assigned_dept = "NA"

                            if complaint == 1:
                                crm_complaint_status = True
                                print(crm_complaint_status)
                                if rewash_count != 0:
                                    rewash_status = ameyo_module.active_or_not(
                                        complaint_details[0].get('CRMComplaintId'))
                                # SP for complaint is closed as Compensation complaint or not
                                query = f"EXEC {CRM}.dbo.USP_Complaint_Resolution_Check @AMEYO_TKT_ID='{complaint_details[0].get('AmeyoTicketId')}' "
                                compensation = CallSP(query).execute().fetchone()

                                if compensation['Compensation Complaint'] == 'NO':

                                    crm_complaint_status = complaint_details[0].get('CrmComplaintStatus')
                                    if crm_complaint_status in ['NA', None, '']:
                                        crm_complaint_status = False
                                    else:
                                        crm_complaint_status = True

                                else:
                                    complaint_status = 'Compensation complaint'
                            else:
                                crm_complaint_status = False


                    else:
                        error_msg = 'No ameyo customer id found'

                else:
                    error_msg = "It's a rewash order tag no. Kindly enter normal order tag details"

            else:
                if tag_status['Status'] == 'Garment not found':
                    error_msg = 'Please enter a valid tag no'
                else:
                    error_msg = 'Rewash cannot be created, as selected garments are still in process.'

        except Exception as e:
            error_logger(f'Route: {request.path}').error(e)
        if complaint_details:
            final_data = generate_final_data('DATA_FOUND')
            result = [{

                'complaintId': complaint_id,
                'ComplaintStatus': complaint_status,
                'CrmComplaintStatus': crm_complaint_status,
                'ComplaintType': complaint_type,
                'AmeyoTicketID': ameyo_ticket_id,
                'OrderGarmentId': complaint_details[0].get('OrderGarmentId', "NA"),
                'POSOrderGarmentId': complaint_details[0].get('OrderGarmentId', "NA"),
                'GarmentBrand': complaint_details[0].get('GarmentBrand', "NA"),
                'GarmentColour': complaint_details[0].get('GarmentColour', "NA"),
                'GarmentSize': complaint_details[0].get('GarmentSize', "NA"),
                'GarmentName': complaint_details[0].get('GarmentName', "NA"),
                'ServiceTypeName': complaint_details[0].get('ServiceTypeName', "NA"),
                'ServiceDescription': complaint_details[0].get('ServiceDescription', "NA"),
                'ServiceTatName': complaint_details[0].get('ServiceTatName', "NA"),
                'EGRN': complaint_details[0].get('OLDEGRN', "NA"),
                'TRNNo': complaint_details[0].get('TRNNo', "NA"),
                'TagNo': complaint_details[0].get('TagId', "NA"),
                'CustomerCode': complaint_details[0].get('CustomerCode', "NA"),
                'QCStatus': complaint_details[0].get('QCStatus', "NA"),
                'StatusCode': complaint_details[0].get('StatusCode', "NA"),
                'RewashStatus': rewash_status,
                'RewashCount': rewash_count,
                'BranchCode': complaint_details[0].get('BranchCode', "NA"),
                'AssignedDept': assigned_dept
            }]
            final_data['result'] = result

        else:
            if error_msg is not None:
                final_data = generate_final_data('CUSTOM_FAILED', error_msg)
            else:
                final_data = generate_final_data('DATA_NOT_FOUND')
    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(get_tag_details_form.errors)
    return final_data

@delivery_blueprint.route('/get_tag_details', methods=["POST"])
# @authenticate('delivery_user')
def get_tag_details__():
    get_tag_details_form = GetTagDetailsForm()
    if get_tag_details_form.validate_on_submit():
        tag_id = get_tag_details_form.tag_id.data
        mobile_number = get_tag_details_form.mobile_number.data
        branch_code = get_tag_details_form.branch_code.data
        # EGRN = get_tag_details_form.EGRN.data
        error_msg = None
        order_garments = []
        complaint_id = 0
        complaint_type = "NA"
        complaint_status = "NA"
        ameyo_ticket_id = "NA"
        assigned_dept = "NA"
        rewash_status = False
        complaint_details = None
        crm_complaint_status = False
        start_date = datetime.today() - timedelta(days=90)

        try:

            query = f"EXEC {SERVER_DB}.dbo.GetGarmentStatus @tagno = {tag_id}"
            tag_status = CallSP(query).execute().fetchone()
            log_data = {
                'tag_status': tag_status
            }
            info_logger(f'Route: {request.path}').info(json.dumps(log_data))
            if tag_status['Status'] == 'Invoiced & Delivered' or tag_status['Status'] == 'Transfer in at CDC':

                query = f"EXEC {SERVER_DB}.dbo.USP_CheckTagTypeForRewash @tagno={tag_id}"
                normal_tag = CallSP(query).execute().fetchone()
                log_data = {
                    'normal_tag': normal_tag
                }
                info_logger(f'Route: {request.path}').info(json.dumps(log_data))
                if normal_tag['Tag Type'] == 'Normal_Tag':
                    query = f""" EXEC JFSL.Dbo.SPFabRewashTagScanValidation @ContactNo= '{mobile_number}' ,@TagNo = '{tag_id}'"""
                    result = CallSP(query).execute().fetchone()
                    log_data = {
                        'validation_details': result
                    }
                    info_logger(f'Route: {request.path}').info(json.dumps(log_data))
                    #if result and result.get('Message') == 'success':
                    if result and result.get('Message') == 'success':
                        ameyo_customer_id = ameyo_module.get_ameyo_customer_id(mobile_number)
                        if ameyo_customer_id:

                            query = f""" EXEC JFSL.Dbo.SPFabComplaintResolutionCheck @TagNo = {tag_id}"""
                            complaint_details = CallSP(query).execute().fetchall()
                            log_data = {
                                'complaint_details': complaint_details
                            }
                            info_logger(f'Route: {request.path}').info(json.dumps(log_data))
                            EGRN = complaint_details[0].get('OLDEGRN', "NA")
                            garment_complaint = ameyo_module.check_complaint_garment(tag_id, EGRN)
                            print(garment_complaint)
                            complaint = 0 if not garment_complaint['Complaint'] else 1
                            rewash_count = garment_complaint['RewashCount']

                            if complaint_details is not None:
                                complaint_id = complaint_details[0].get('Id')

                                if complaint_details and complaint_details[0].get('ComplaintType'):
                                    complaint_type = complaint_details[0]['ComplaintType']
                                else:
                                    complaint_type = "NA"
                                # Check if complaint_details is a list and has at least one record
                                if complaint_details and isinstance(complaint_details, list) and len(
                                        complaint_details) > 0:
                                    ameyo_ticket_id = complaint_details[0].get('JFSLTicketId', "NA") or "NA"
                                    complaint_status = complaint_details[0].get('CrmComplaintStatus', "NA")
                                    if complaint_status == '0':
                                        complaint_status = 'NA'
                                else:
                                    ameyo_ticket_id = "NA"
                                    complaint_status = "NA"

                                # Check if complaint_details is a list with at least one record
                                # Check if complaint_details is a list with at least one record
                                if complaint_details and isinstance(complaint_details, list) and len(
                                        complaint_details) > 0:
                                    assigned_dept = complaint_details[0].get('AssignedDept', "NA") or "NA"
                                    assigned_user_id = complaint_details[0].get('AssignedUserId')

                                    if assigned_dept == 'OPERATIONS' and assigned_user_id is not None:
                                        assigned_dept = 'CRMOPERATIONS'
                                else:
                                    assigned_dept = "NA"

                                if complaint == 1:
                                    crm_complaint_status = True
                                    print(crm_complaint_status)
                                    if rewash_count != 0:
                                        rewash_status = ameyo_module.active_or_not(
                                            complaint_details[0].get('CRMComplaintId'))
                                    # SP for complaint is closed as Compensation complaint or not
                                    query = f"EXEC {CRM}.dbo.USP_Complaint_Resolution_Check @AMEYO_TKT_ID='{complaint_details[0].get('AmeyoTicketId')}' "
                                    compensation = CallSP(query).execute().fetchone()

                                    if compensation['Compensation Complaint'] == 'NO':

                                        crm_complaint_status = complaint_details[0].get('CrmComplaintStatus')
                                        if crm_complaint_status in ['NA', None, '']:
                                            crm_complaint_status = False
                                        else:
                                            crm_complaint_status = True

                                    else:
                                        complaint_status = 'Compensation complaint'
                                else:
                                    crm_complaint_status = False


                        else:
                            error_msg = 'No ameyo customer id found'
                    else:
                        error_msg = 'Tag No. is not matching with mobile number'

                else:
                    error_msg = "It's a rewash order tag no. Kindly enter normal order tag details"

            else:
                if tag_status['Status'] == 'Garment not found':
                    error_msg = 'Please enter a valid tag no'
                elif tag_status['Status'] == 'Invoiced & Pending Delivery':
                    error_msg = 'Garment is still not delivered'
                else:
                    error_msg = 'Rewash cannot be created, as selected garments are still in process.'

        except Exception as e:
            error_logger(f'Route: {request.path}').error(e)
        if complaint_details:
            final_data = generate_final_data('DATA_FOUND')
            result = [{

                'complaintId': complaint_id,
                'ComplaintStatus': complaint_status,
                'CrmComplaintStatus': crm_complaint_status,
                'ComplaintType': complaint_type,
                'AmeyoTicketID': ameyo_ticket_id,
                'OrderGarmentId': complaint_details[0].get('OrderGarmentId', "NA"),
                'POSOrderGarmentId': complaint_details[0].get('OrderGarmentId', "NA"),
                'GarmentBrand': complaint_details[0].get('GarmentBrand', "NA"),
                'GarmentColour': complaint_details[0].get('GarmentColour', "NA"),
                'GarmentSize': complaint_details[0].get('GarmentSize', "NA"),
                'GarmentName': complaint_details[0].get('GarmentName', "NA"),
                'ServiceTypeName': complaint_details[0].get('ServiceTypeName', "NA"),
                'ServiceDescription': complaint_details[0].get('ServiceDescription', "NA"),
                'ServiceTatName': complaint_details[0].get('ServiceTatName', "NA"),
                'EGRN': complaint_details[0].get('OLDEGRN', "NA"),
                'TRNNo': complaint_details[0].get('TRNNo', "NA"),
                'TagNo': complaint_details[0].get('TagId', "NA"),
                'CustomerCode': complaint_details[0].get('CustomerCode', "NA"),
                'QCStatus': complaint_details[0].get('QCStatus', "NA"),
                'StatusCode': complaint_details[0].get('StatusCode', "NA"),
                'RewashStatus': rewash_status,
                'RewashCount': rewash_count,
                'BranchCode': complaint_details[0].get('BranchCode', "NA"),
                'AssignedDept': assigned_dept
            }]
            final_data['result'] = result

        else:
            if error_msg is not None:
                final_data = generate_final_data('CUSTOM_FAILED', error_msg)
            else:
                final_data = generate_final_data('DATA_NOT_FOUND')
    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(get_tag_details_form.errors)
    return final_data


@delivery_blueprint.route('/get_recent_orders', methods=["POST"])
# @authenticate('delivery_user')
def get_recent_orders():
    get_recent_orders_form = GetRecentOrdersForm()
    log_data = {
        'get_recent_orders_form': get_recent_orders_form.data
                                        }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))
    if get_recent_orders_form.validate_on_submit():
        result = False
        orders = []
        error_msg = None
        MobileNo = get_recent_orders_form.MobileNo.data

        CustomerCode = get_recent_orders_form.CustomerCode.data
        try:

            # if customer is not None:
            ameyo_customer_id = ameyo_module.get_ameyo_customer_id(MobileNo)
            if ameyo_customer_id:
                query = f"""EXEC JFSL.Dbo.SPPendingDeliveriesDetailedScreen @CustomerCode = '{CustomerCode}', @ForRewashOrderDisplay=1"""
                log_data = {
                'query': query
                                        }
                info_logger(f'Route: {request.path}').info(json.dumps(log_data))
                orders = CallSP(query).execute().fetchall()
                if orders is not None:
                    result = True
                    orders = SerializeSQLAResult(orders).serialize()

            else:
                error_msg = 'Ameyo customer id not found'
            # else:
            #     error_msg = 'customer not found'
        except Exception as e:
            error_logger(f'Route: {request.path}').error(e)

        if result:
            final_data = generate_final_data('DATA_FOUND')
            final_data['result'] = orders
        else:
            if error_msg is not None:

                final_data = generate_final_data('CUSTOM_FAILED', error_msg)
            else:
                final_data = generate_final_data('DATA_NOT_FOUND')
    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(get_recent_orders_form.errors)
    log_data = {
        'final_data': final_data
                                        }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))
    return final_data


@delivery_blueprint.route('/registration', methods=["POST"])
# @authenticate('delivery_user')
def registration():
    final_data = generate_final_data('DATA_FOUND')
    result = {"is_visibility": 0}
    final_data['result'] = result
    return final_data


@delivery_blueprint.route('/reopen_complaint', methods=["POST"])
@authenticate('delivery_user')
def reopen_complaint():
    reopen_complaint_form = ReopenComplaintForm()
    if reopen_complaint_form.validate_on_submit():
        tag_id = reopen_complaint_form.tag_id.data
        remarks = reopen_complaint_form.remarks.data

        updated = False

        try:
            complaint_status = db.session.query(Complaint).filter(
                Complaint.TagId == tag_id,
                Complaint.IsDeleted == 0).order_by(Complaint.RecordCreatedDate.desc()).limit(
                1).one_or_none()
            if complaint_status.CRMComplaintStatus == 'Closed':
                try:
                    complaint_status.CRMComplaintStatus = "Active"
                    complaint_status.ComplaintDesc = remarks
                    complaint_status.RecordLastUpdatedDate = get_current_date()
                    db.session.commit()
                    query = f"EXEC {CRM}.dbo.usp_Update_CRM_COMPLAINT_Status @AMEYOTICKETID_FOR_CRM_COMPLAINT='{complaint_status.AmeyoTicketId}'"
                    db.engine.execute(text(query).execution_options(autocommit=True))
                except Exception as e:
                    error_logger(f'Route: {request.path}').error(e)
                updated = True
        except Exception as e:
            error_logger(f'Route: {request.path}').error(e)

        if updated:
            final_data = generate_final_data('DATA_UPDATED')
        else:
            final_data = generate_final_data('CUSTOM_FAILED')
    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(reopen_complaint_form.errors)
    return final_data

@delivery_blueprint.route('/garment_details', methods=["POST"])
# @authenticate('delivery_user')
def garment_details_():
    garment_details_form = GarmentDetailsForm()
    log_data = {
        'garment_details_form': garment_details_form.data
    }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))
    if garment_details_form.validate_on_submit():
        TagNo = garment_details_form.TagNo.data
        EGRN = garment_details_form.EGRN.data
        TRNNo = garment_details_form.TRNNo.data

        # Initialize default values
        garment_detail = []

        try:
            for tag_id in TagNo:
                # Fetch garment complaint details
                garment_complaint = ameyo_module.check_complaint_garment(tag_id, EGRN)


                complaint = 1 if garment_complaint['Complaint'] else 0
                rewash_count = garment_complaint['RewashCount']

                # Execute stored procedure for complaint details
                try:
                    query = f"EXEC JFSL.Dbo.SPFabComplaintResolutionCheck @TagNo = '{tag_id}'"
                    
                    complaint_details = CallSP(query).execute().fetchall()
                    log_data = {
                    'query': query,
                    "complaint_details":complaint_details
                        }
                    info_logger(f'Route: {request.path}').info(json.dumps(log_data))

                except Exception as e:
                    error_logger(f'Route: {request.path}').error(e)
                    continue

                # Set default values
                complaint_id = 0
                complaint_type = "NA"
                complaint_status = "NA"
                crm_complaint_status = False
                ameyo_ticket_id = "NA"
                assigned_dept = "NA"
                rewash_status = False

                if complaint_details and isinstance(complaint_details, list) and len(complaint_details) > 0:
                    
                    complaint_id = complaint_details[0].get('CRMComplaintId', 0)
                    complaint_type = complaint_details[0].get('ComplaintType', "NA")
                    ameyo_ticket_id = complaint_details[0].get('JFSLTicketId', "NA") or "NA"
                    complaint_status = complaint_details[0].get('CrmComplaintStatus', "NA")
                    if complaint_status == '0':
                        complaint_status = 'NA'
                    assigned_dept = complaint_details[0].get('AssignedDept', "NA") or "NA"
                    assigned_user_id = complaint_details[0].get('AssignedUserId')

                    # Adjust assigned department if needed
                    if assigned_dept == 'OPERATIONS' and assigned_user_id is not None:
                        assigned_dept = 'CRMOPERATIONS'

                    # Check for rewash status if the complaint exists
                    if complaint == 1:
                        crm_complaint_status = True
                        if rewash_count != 0:
                            rewash_status = ameyo_module.active_or_not(complaint_details[0].get('CRMComplaintId'))

                        # Check if the complaint is marked as compensation
                        query = f"EXEC {CRM}.dbo.USP_Complaint_Resolution_Check @AMEYO_TKT_ID='{complaint_details[0].get('AmeyoTicketId')}'"
                        compensation = CallSP(query).execute().fetchone()
                        log_data = {
                        'query': query,
                        "compensation":compensation
                        }
                        info_logger(f'Route: {request.path}').info(json.dumps(log_data))

                        if compensation and compensation.get('Compensation Complaint') == 'NO':
                            crm_complaint_status = complaint_details[0].get('CRMComplaintStatus')
                            if crm_complaint_status in ['NA', None, '']:
                                crm_complaint_status = False
                            else:
                                crm_complaint_status = crm_complaint_status
                        else:
                            complaint_status = 'Compensation complaint'
                    else:
                        crm_complaint_status = False

                # Process complaint details and build the response
                for order in complaint_details:
                    order['RewashCount'] = rewash_count or 0
                    order['RewashStatus'] = rewash_status or False
                    order['ComplaintStatus'] = complaint_status or "NA"
                    order['ComplaintId'] = complaint_id or 0
                    order['ComplaintType'] = complaint_type or "NA"
                    order['CrmComplaintStatus'] = crm_complaint_status
                    order['AmeyoTicketId'] = ameyo_ticket_id or "NA"
                    order['AssignedDept'] = assigned_dept or "NA"

                    # Append each updated order to garment_detail
                    if order not in garment_detail:
                        garment_detail.append(order)

        except Exception as e:
            error_logger(f'Route: {request.path}').error(e)

        # Return final response based on data
        if garment_detail:
            final_data = generate_final_data('DATA_FOUND')
            final_data['result'] = garment_detail
        else:
            final_data = generate_final_data('DATA_NOT_FOUND')

    else:
        # Form validation error
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(garment_details_form.errors)
    log_data = {
        'final_data': final_data
    }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))

    return final_data

#     return final_data

@delivery_blueprint.route('/rewash', methods=["POST"])
# @authenticate('delivery_user')
def rewash():
    complaint_form = AdhocRewashForm()
    log_data = {
        'ReqBody_rewashNew': complaint_form.data
    }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))
    if complaint_form.validate_on_submit():

        BookingID = None if complaint_form.BookingID.data == '' else complaint_form.BookingID.data

        rewashed = False
        user_id = request.headers.get('user-id')
        complaint_garment_list = complaint_form.complaint_garment_list.data
        error_msg = None
        TRNNo = None
        ExistingOrderGarmentID = complaint_garment_list[0].get('OrderGarmentID')
        OLDEGRN = complaint_form.OLDEGRN.data
        print(OLDEGRN)
        OrderGarmentIDs = []  # To keep track of inserted IDs
        rewash_orders = []  # To collect rewash data for the response

        try:
            for garment in complaint_garment_list:
                existing = db.session.execute(
                    text("""
                        SELECT 1 FROM JFSL.Dbo.FabTempOrderGarments (NOLOCK)
                        WHERE OldOrderGarmentID = :OrderGarmentID
                    """),
                    {'OrderGarmentID': garment['OrderGarmentID']}
                ).fetchone()

                if existing:
                    # Fetch the already inserted new OrderGarmentID from FabTempOrderGarments
                    existing_order = db.session.execute(
                        text("""
                            SELECT OrderGarmentID FROM JFSL.Dbo.FabTempOrderGarments (NOLOCK)
                            WHERE OldOrderGarmentID = :OrderGarmentID
                        """),
                        {'OrderGarmentID': garment['OrderGarmentID']}
                    ).fetchone()

                    if existing_order:
                        OrderGarmentID = existing_order[0]
                        OrderGarmentIDs.append(OrderGarmentID)
                        rewash_orders.append({
                            "new_garment_id": OrderGarmentID,
                            "old_garment_id": garment['OrderGarmentID'],
                            "complaint_status": garment.get('CRMComplaintStatus', "NA"),
                            "complaint_id": garment.get('CRMComplaintId'),
                        })

                    continue  # Skip insertion

                garment['BookingID'] = BookingID
                garment['OldOrderGarmentID'] = garment['OrderGarmentID']
                garment['OrderGarmentID'] = uuid.uuid4()
                garment['OrderInstructionIDs'] = None
                garment['GarmentCount'] = 1
                garment['price_list_id'] = 0
                garment['price'] = 0
                garment['UOMID'] = 0
                garment['OrderIssueIDs'] = None
                garment['isChanged'] = None
                garment['OrderTypeId'] = 2

                db.session.execute(text("""
                    INSERT INTO JFSL.Dbo.FabTempOrderGarments (
                        OrderGarmentID, BookingID, OrderTypeId, GarmentCount,
                        ServiceTatId, ServiceTypeId, GarmentId, GarmentName,
                        Price, PriceListId, UOMID, CRMComplaintId,
                        OrderInstructionIDs, IsChanged, OrderIssueIDs, OldOrderGarmentID
                    ) VALUES (
                        :OrderGarmentID, :BookingID, :OrderTypeId, :GarmentCount,
                        :ServiceTatId, :ServiceTypeId, :GarmentID, :GarmentName,
                        :price, :price_list_id, :UOMID, :CRMComplaintId,
                        :OrderInstructionIDs, :isChanged, :OrderIssueIDs, :OldOrderGarmentID
                    )
                """), garment)

                OrderGarmentID = garment['OrderGarmentID']
                OrderGarmentIDs.append(OrderGarmentID)

                rewash_orders.append({
                    "new_garment_id": OrderGarmentID,
                    "old_garment_id": garment['OldOrderGarmentID'],
                    "complaint_status": garment.get('CRMComplaintStatus', "NA"),
                    "complaint_id": garment.get('CRMComplaintId'),
                })

            db.session.commit()
            rewashed = True

            TRNNoRow = db.session.execute(
                text("SELECT TRNNo FROM JFSL.dbo.Fabdeliveryinfo (NOLOCK) WHERE EGRNNo = :OLDEGRN"),
                {"OLDEGRN": OLDEGRN}
            ).fetchone()
            TRNNo = TRNNoRow[0] if TRNNoRow else None

        except Exception as e:
            error_logger(f'Route: {request.path}').error(e)
        if rewashed:
            final_data = generate_final_data('DATA_SAVED')
            print(OrderGarmentID)
            final_data['new_order_id'] = OrderGarmentID

            rewash_order = {"new_garment_id": OrderGarmentID,
                            "old_garment_id": ExistingOrderGarmentID,
                            "complaint_status": complaint_garment_list[0].get('CRMComplaintStatus', "NA"),
                            "complaint_id": complaint_garment_list[0].get('CRMComplaintId'), "TRNNo": TRNNo}

            final_data['final_rewash'] = [rewash_order]
        else:
            if error_msg is not None:
                final_data = generate_final_data('CUSTOM_FAILED', error_msg)
            else:
                final_data = generate_final_data('DATA_SAVE_FAILED')
    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(complaint_form.errors)
    return final_data




@delivery_blueprint.route('/finalize_rewash', methods=["POST"])
# @authenticate('delivery_user')
def finalize_rewash():
    finalize_rewash_form = FinalizeRewashForm()
    if finalize_rewash_form.validate_on_submit():
        BookingId = finalize_rewash_form.BookingId.data
        log_data = {
            'finalize_rewash_form': finalize_rewash_form.data
        }
        info_logger(f'Route: {request.path}').info(json.dumps(log_data))
        user_id = request.headers.get('user-id')
        final_rewash_list = finalize_rewash_form.final_rewash_list.data
        egrn = finalize_rewash_form.EGRN.data
        rewashed = False
        lat = 0.0 if finalize_rewash_form.lat.data == '' else finalize_rewash_form.lat.data
        long = 0.0 if finalize_rewash_form.long.data == '' else finalize_rewash_form.long.data
        StoreDistance = 0.0
        DuserDistance = 0.0
        try:
            query = f"""EXEC  JFSL.dbo.SpGetPendingPickupCustApp @BookingId={BookingId}"""
            log_data = {
            'query': query
            }
            info_logger(f'Route: {request.path}').info(json.dumps(log_data))

            result = CallSP(query).execute().fetchone()
            # log_data = {
            # 'query_s': result
            # }
            # info_logger(f'Route: {request.path}').info(json.dumps(log_data))
            CustomerCode = result.get('CustomerCode')
            # MobileNo = result.get('MobileNo')
            BranchCode = result.get('BranchCode')
            CustLat = float(result.get('Lat', 0))
            CustLong = float(result.get('Long', 0))
            PickupID = result.get('PickupID')
            CustomerName = result.get('CustomerName')
            MobileNo = db.session.execute(
                    text(
                        "SELECT ContactNo  FROM JFSL.dbo.CustomerInfo (nolock) WHERE CustomerCode = :CustomerCode"),
                    {"CustomerCode": CustomerCode}
                ).fetchone()
            MobileNo = MobileNo[0]

            for rewash_list in final_rewash_list:
                AmeyoTicketId = rewash_list['AmeyoTicketId']
                ComplaintId = rewash_list['ComplaintID']
                crm_complaint_id = ameyo_module.rewash_complaint(egrn,CustomerCode, CustomerName,MobileNo, BranchCode,AmeyoTicketId ,ComplaintId)


            customer_location = (CustLat, CustLong)
            delivery_user_loaction = (lat, long)
            distance = hs.haversine(customer_location, delivery_user_loaction)
            if distance is not None:
                if distance >= 1:
                    km_part = int(distance)
                    meters_part = (distance - km_part) * 1000
                    DuserDistance = f"{km_part} km {int(meters_part)} m"
                else:
                    distance_meters = distance * 1000
                    DuserDistance = f"{int(distance_meters)} m"

            BranchLocation = db.session.execute(
                text(
                    "SELECT Lat, Long,BranchName FROM JFSL.dbo.Branchinfo WHERE BranchCode = :BranchCode"),
                {"BranchCode": BranchCode}
            ).fetchone()

            if BranchLocation is not None:
                branch_location = (
                    float(BranchLocation.Lat), float(BranchLocation.Long))

                store_distance = hs.haversine(branch_location, delivery_user_loaction)
                if store_distance >= 1:
                    km_part = int(store_distance)
                    meters_part = (
                                              store_distance - km_part) * 1000
                    StoreDistance = f"{km_part} km {int(meters_part)} m"
                else:
                    # If the distance is less than 1 km, convert it to meters
                    distance_meters = store_distance * 1000
                    StoreDistance = f"{int(distance_meters)} m"

            GarmentsCount = db.session.execute(
                text("""
                    SELECT COUNT(*) 
                    FROM JFSL.dbo.FabTempOrderGarments WITH (NOLOCK) 
                    WHERE BookingID = :BookingId
                """),
                {"BookingId": BookingId}
            ).fetchone()
            Count = GarmentsCount[0] if GarmentsCount else 0

            query = f""" JFSL.Dbo.SPFabOldEGRNRewashOrderGarmentsInsert @PickupID ='{PickupID}',@DUserID ={user_id},@BookingID = {BookingId},@BranchCode = '{BranchCode}'                
                            ,@CustomerCode = '{CustomerCode}',@OrderType = {2},@RewashReason = '' ,@OLDEGRNNo = '{egrn}',@Remarks = ''                         
                            ,@DuserDistance = '{DuserDistance}' ,@AssignedStoreUser = '{1}',@StoreDistance = '{StoreDistance}' , @Distance = '{DuserDistance}',@DuserLat = {lat} ,@DuserLong = {long},@GarmentsCount={Count}"""

            log_data = {
                'SP-update-complaintId': query
            }
            info_logger(f'Route: {request.path}').info(json.dumps(log_data))
            rewashed = True
            db.engine.execute(text(query).execution_options(autocommit=True))
            

        except Exception as e:
            error_logger(f'Route: {request.path}').error(e)
        if rewashed:
            final_data = generate_final_data('DATA_SAVED')
            try:
                db.session.execute(text("""
                                        INSERT INTO JFSL.Dbo.FABTravelLogs 
                                        (Activity,  DUserId,    BookingID,  TRNNo,  Lat,    Long,   IsDeleted,  RecordCreatedDate,  RecordLastUpdatedDate) 
        
                                        VALUES (:Activity,  :DUserId,   :BookingID, :TRNNo, :Lat,   :Long,  :IsDeleted, :RecordCreatedDate, :RecordCreatedDate)
                                        """), {
                    "Activity": "Pickup",
                    "DUserId": user_id,
                    "BookingID": BookingId,
                    "TRNNo": '',
                    "Lat": lat,
                    "Long": long,
                    "Remarks": '',
                    "IsDeleted": 0,
                    "RecordCreatedDate": get_current_date()
                })
                db.session.commit()
            except Exception as e:
                error_logger(f'Route: {request.path}').error(e)
        else:
            final_data = generate_final_data('DATA_SAVE_FAILED')
    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(finalize_rewash_form.errors)
    log_data = {
                'final_data': final_data
            }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))
    return final_data

@delivery_blueprint.route('/get_selected_garment_details', methods=["POST"])
# @authenticate('delivery_user')
def get_selected_garment_details():
    tag_details_form = TagDetailsForm()
    log_data = {
                'tag_details_form': tag_details_form.data
            }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))
    if tag_details_form.validate_on_submit():
        tag_id = tag_details_form.tag_id.data
        tag_id = [*set(tag_id)]  # Remove duplicate tag IDs if any

        all_garments = []

        for tag in tag_id:
            query = f"""EXEC JFSL.Dbo.SPFabComplaintResolutionCheck @TagNo = '{tag}'"""
            log_data = {
                'query': query
            }
            info_logger(f'Route: {request.path}').info(json.dumps(log_data))
            garments = CallSP(query).execute().fetchall()

            if garments:
                for garment in garments:
                    garment_dict = dict(garment)

                    # Get CrmComplaintStatus value
                    crm_status = str(garment_dict.get('CrmComplaintStatus', '0'))

                    # Add 'ComplaintStatus' logic
                    garment_dict['ComplaintStatus'] = 'NA' if crm_status == '0' else crm_status

                    # Add 'CRMComplaintStatus' as boolean
                    garment_dict['CRMComplaintStatus'] = False if crm_status == '0' else True

                    all_garments.append(garment_dict)

        # Remove duplicate entries based on all fields
        all_garments = [dict(t) for t in {tuple(d.items()) for d in all_garments}]

        if all_garments:
            final_data = generate_final_data('DATA_FOUND')
            final_data['result'] = all_garments
        else:
            final_data = generate_final_data('DATA_NOT_FOUND')
    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(tag_details_form.errors)

    return final_data

@delivery_blueprint.route('/get_selected_vas', methods=["POST"])
@authenticate('delivery_user')
def get_selected_vas():
    vas_details_form = VasDetailsForm()
    if vas_details_form.validate_on_submit():
        order_id = vas_details_form.order_id.data
        order_garment_id = vas_details_form.order_garment_id.data
        log_data = {
                'vas_details_form': vas_details_form.data
                    }
        info_logger(f'Route: {request.path}').info(json.dumps(log_data))
        vas_details = []
        try:

            query = f""" EXEC JFSL.Dbo.SPDisplayTempOrderGarmentsCustApp @BookingID = '', @OrderGarmentID = '{order_garment_id}', @ActionType = {3} , @ServiceTatId = ''"""
            vas_details = CallSP(query).execute().fetchall()
            vas_details = [
                {
                    "InstructionId": i["InstructionID"],
                    "OrderGarmentId": i["OrderGarmentID"],
                    "Instruction": i["Instruction"],
                    "InstructionDescription": i["Description"],
                    "InstructionIcon": i["InstructionIcon"],
                }
                for i in vas_details if i
            ]
        except Exception as e:
            error_logger(f'Route: {request.path}').error(e)
        if vas_details:
            final_data = generate_final_data('DATA_SAVED')

            final_data['result'] = vas_details
        else:
            final_data = generate_final_data('DATA_NOT_FOUND')
            final_data['result'] = vas_details
    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(VasDetailsForm.errors)
    log_data = {
                'final_data': final_data
                    }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))
    return final_data


@delivery_blueprint.route('/raise_complaint', methods=["POST"])
# @authenticate('delivery_user')
def raise_complaint():
    complaint_form = AddComplaintForm()
    if complaint_form.validate_on_submit():
        log_data = {
                'complaint_form': complaint_form.data
                    }
        info_logger(f'Route: {request.path}').info(json.dumps(log_data))
        CustomerCode = complaint_form.CustomerCode.data
        EGRN = complaint_form.EGRN.data
        complaint_garment_list = complaint_form.complaint_garment_list.data
        BranchCode = complaint_form.BranchCode.data
        complaint = False

        try:
            for complaints in complaint_garment_list:
                complaint_remarks = re.sub(r"(?<=\w)[^\w\s,\.](?=\w)", "", complaints['complaint_remarks'].replace("'", "")).strip()

                query = f""" EXEC JFSL.Dbo.[SPFabComplaintsInsertUpdate] @CustomerCode = '{CustomerCode}',@BranchCode = '{BranchCode}',@complaint_type = '{complaints['complaint_type']}'      
                ,@EGRN = '{EGRN}',@TagId = '{complaints['TagNo']}',@complaint_remarks='{complaint_remarks}'"""
                
                log_data = {
                'query': query
                    }
                info_logger(f'Route: {request.path}').info(json.dumps(log_data))
                db.engine.execute(text(query).execution_options(autocommit=True))
                complaint = True

        except Exception as e:
            error_logger(f'Route: {request.path}').error(e)
        if complaint:
            final_data = generate_final_data('DATA_SAVED')
        else:
            final_data = generate_final_data('DATA_NOT_FOUND')
    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(complaint_form.errors)
    log_data = {
                'final_data': final_data
                    }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))
    return final_data



# @delivery_blueprint.route('/raise_complaint', methods=["POST"])
# # @authenticate('delivery_user')
# def raise_complaint():
#     complaint_form = AddComplaintForm()
#     if complaint_form.validate_on_submit():
#         log_data = {
#             'complaint_form11': complaint_form.data
#         }
#         info_logger(f'Route: {request.path}').info(json.dumps(log_data))

#         CustomerCode = complaint_form.CustomerCode.data
#         EGRN = complaint_form.EGRN.data
#         complaint_garment_list = complaint_form.complaint_garment_list.data
#         BranchCode = complaint_form.BranchCode.data
#         complaint = False

#         try:
#             for complaints in complaint_garment_list:
#                 query = text("""
#                     EXEC JFSL.Dbo.SPFabComplaintsInsertUpdate 
#                         @CustomerCode = :CustomerCode,
#                         @BranchCode = :BranchCode,
#                         @complaint_type = :complaint_type,
#                         @EGRN = :EGRN,
#                         @TagId = :TagId,
#                         @complaint_remarks = :complaint_remarks
#                 """).execution_options(autocommit=True)

#                 params = {
#                     'CustomerCode': CustomerCode,
#                     'BranchCode': BranchCode,
#                     'complaint_type': complaints['complaint_type'],
#                     'EGRN': EGRN,
#                     'TagId': complaints['TagNo'],
#                     'complaint_remarks': re.sub(r"(?<=\w)[^\w\s,\.](?=\w)", "", complaints['complaint_remarks'].replace("'", "")).strip()

#                 }

#                 log_data = {
#                     'executing_query': 'SPFabComplaintsInsertUpdate',
#                     'params': params
#                 }
#                 info_logger(f'Route: {request.path}').info(json.dumps(log_data))

#                 db.session.execute(query, params)
#                 complaint = True

#         except Exception as e:
#             error_logger(f'Route: {request.path}').error(str(e))
#             complaint = False

#         if complaint:
#             final_data = generate_final_data('DATA_SAVED')
#         else:
#             final_data = generate_final_data('DATA_NOT_FOUND')
#     else:
#         final_data = generate_final_data('FORM_ERROR')
#         final_data['errors'] = populate_errors(complaint_form.errors)

#     log_data = {
#         'final_data': final_data
#     }
#     info_logger(f'Route: {request.path}').info(json.dumps(log_data))
#     return final_data



@delivery_blueprint.route('/get_pickup_listB4SP', methods=["POST"])
@authenticate('delivery_user')
def get_pickup_listB4SP():
    """
    API for getting the list of pickup requests that need to be picked up by the pickup/delivery user.
    """
    activity_list_form = ActivityListForm()

    if activity_list_form.validate_on_submit():
        user_id = request.headers.get('user-id')
        activity_list = []
        branch_codes = activity_list_form.branch_codes.data
        sorting_method = activity_list_form.sorting_method.data
        # lat and long are optional. If no data provided, NULL will be passed to the stored procedure.
        lat = None if activity_list_form.lat.data == '' else activity_list_form.lat.data
        long = None if activity_list_form.long.data == '' else activity_list_form.long.data

        only_tomorrow = activity_list_form.only_tomorrow.data

        if only_tomorrow:
            # If only_tomorrow param present in the request, return only tomorrow's activities.
            tomorrow = (datetime.today() + timedelta(1)).strftime("%Y-%m-%d 00:00:00")
        else:
            tomorrow = None

        try:

            if not branch_codes:
                # Getting the branches associated with the user.
                delivery_user_branches = delivery_controller_queries.get_delivery_user_branches(user_id)
            else:
                # Branch codes are given.
                delivery_user_branches = branch_codes

            # Calculating the distance in KM between the delivery user's lat and long to
            # the customer address' lat and long.
            distance_in_km = func.dbo.GetDistance(lat, long, CustomerAddres.Lat,
                                                  CustomerAddres.Long).label('Distance')

            # If the pickup is rescheduled, then select RescheduledDate, else select PickupDate.
            select_activity_date = case([(PickupReschedule.RescheduledDate == None, PickupRequest.PickupDate), ],
                                        else_=PickupReschedule.RescheduledDate).label("ActivityDate")

            # If the pickup is rescheduled, then select reschedule's time slot from, else time slot from of
            # the pickup request.
            select_time_slot_from = case([(PickupReschedule.TimeSlotFrom == None, PickupRequest.TimeSlotFrom), ],
                                         else_=PickupReschedule.TimeSlotFrom).label("TimeSlotFrom")

            # If the pickup is rescheduled, then select reschedule's time slot to, else time slot to of
            # the pickup request.
            select_time_slot_to = case([(PickupReschedule.TimeSlotTo == None, PickupRequest.TimeSlotTo), ],
                                       else_=PickupReschedule.TimeSlotTo).label("TimeSlotTo")

            # Getting the pending pickup requests.

            pending_pickups = PickupDetails(user_id).get_pending_pickups(tomorrow, select_activity_date,
                                                                         select_time_slot_from, select_time_slot_to,
                                                                         lat, long, delivery_user_branches)

            if sorting_method == 'TIME_SLOT':
                # Sorting based on Activity Date, TimeSlotFrom and TimeSlotTo
                activity_list = pending_pickups.order_by(select_activity_date.asc(),
                                                         select_time_slot_from.asc(),
                                                         select_time_slot_to.asc(),
                                                         ).all()
            elif sorting_method == 'NEAR_ME':
                # Sorting the activity list based on nearest distance from the delivery user.
                activity_list = pending_pickups.order_by(distance_in_km.asc()).all()
            elif sorting_method == 'BOTH':
                # Sorting the activity list based on Activity Date, TimeSlotFrom, TimeSlotTo
                # and nearest distance from the delivery user.
                activity_list = pending_pickups.order_by(select_activity_date.asc(),
                                                         select_time_slot_from.asc(),
                                                         select_time_slot_to.asc(),
                                                         distance_in_km.asc()).all()
            else:
                # Default sorting based on Activity Date, TimeSlotFrom and TimeSlotTo
                activity_list = pending_pickups.order_by(
                    select_activity_date.asc(),
                    select_time_slot_from.asc(),
                    select_time_slot_to.asc()).all()

        except Exception as e:
            error_logger(f'Route: {request.path}').error(e)

        if activity_list is not None:
            # Serializing the activity list.
            activity_list = SerializeSQLAResult(activity_list).serialize()
            if len(activity_list) > 0:
                # Now for each activity, retrieve service tats and service types belongs
                # to that pickup request Id

                for activity in activity_list:

                    # If the ActivityDate is less than current date, mention this order as LATE
                    activity_date = activity['ActivityDate']
                    # Convert string date to datetime object.
                    activity_date_obj = datetime.strptime(activity_date, "%d-%m-%Y")
                    # From the date object, convert the date to YYYY-MM-DD format.
                    formatted_activity_date = activity_date_obj.strftime("%Y-%m-%d %H:%M:%S")
                    # If the activity is late than today, add a late flag.
                    if formatted_activity_date < get_today():
                        activity['IsLate'] = 1
                    else:
                        activity['IsLate'] = 0
                    # Edited by MMM
                # Adding a day to the current date
                next_date = (datetime.today() + timedelta(1))
                # Formatting the added date
                formatted_next_date = next_date.strftime("%Y-%m-%d 00:00:00")
                # Getting travel log details from DB
                completed_activities = db.session.query(TravelLog.OrderId,
                                                        TravelLog.RecordCreatedDate.label('ActivityTime'),
                                                        TravelLog.Activity, TravelLog.Lat, TravelLog.Long).filter(
                    TravelLog.DUserId == user_id,
                    TravelLog.RecordCreatedDate.between(get_today(), formatted_next_date)).order_by(
                    TravelLog.RecordCreatedDate.asc()).all()
                logs_details = SerializeSQLAResult(completed_activities).serialize(full_date_fields=['ActivityTime'])

                # Edited by MMM

                final_data = generate_final_data('DATA_FOUND')
                final_data['result'] = activity_list
                final_data['CompletedActivities'] = logs_details

            else:
                final_data = generate_final_data('DATA_NOT_FOUND')

        else:
            final_data = generate_final_data('DATA_NOT_FOUND')
    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(activity_list_form.errors)

    return final_data


@delivery_blueprint.route('/get_delivery_list', methods=["POST"])
# @authenticate('store_user')
def get_delivery_list():
    """
        API for getting the pending activities in a branch.
        @return:
        """
    activity_list_form = ActivityListForm()
    if activity_list_form.validate_on_submit():
        user_id = request.headers.get('user-id')
        activity_list = []
        branch_codes = activity_list_form.branch_codes.data
        sorting_method = activity_list_form.sorting_method.data
        # lat and long are optional. If no data provided, NULL will be passed to the stored procedure.
        lat = None if activity_list_form.lat.data == '' else activity_list_form.lat.data
        long = None if activity_list_form.long.data == '' else activity_list_form.long.data
        delivery_type = None if activity_list_form.delivery_type.data == '' else activity_list_form.delivery_type.data
        payment_status = None if activity_list_form.payment_status.data == '' else activity_list_form.payment_status.data
        only_tomorrow = activity_list_form.only_tomorrow.data
        today = get_today()
        next_date = (datetime.today() + timedelta(1))
        if only_tomorrow:
            is_tommorrow = 1
           
        else:
            is_tommorrow = 0

        if not branch_codes:
            branch_codes = []
            query = f"EXEC JFSL.Dbo.SPGetDeliveryUserbranchMappingCustApp @Duserid='{user_id}'"
            delivery_user_branches = CallSP(query).execute().fetchall()

            if isinstance(delivery_user_branches, list):
                for branch in delivery_user_branches:
                    if isinstance(branch, dict) and 'BranchCode' in branch:
                        branch_codes.append(branch['BranchCode'])
        else:
            # Branch codes are given.
            branch_codes = branch_codes
        branch_codes = ','.join(branch_codes)
        delivery_count = 0
        print(payment_status)
        try:
            if (payment_status == 'Un-Paid'):
                Activitytype = "Delivered-Unpaid"
            else:
                Activitytype = "Deliveries"
            pending_delivery_query = f"EXEC JFSL.Dbo.[SPFabPendingMobileAppActivity] @DeliveryUsername= '{user_id}',@Branch='{branch_codes}',@SortingMethod='{sorting_method}',@delivery_type='{delivery_type}',@Status_type='PENDING',@Activitytype='{Activitytype}',@IsTommorrow={is_tommorrow}"
            print(pending_delivery_query)
            log_data = {
                'PendingMobileAppActivity qry :': pending_delivery_query,
                'activity_list_form': activity_list_form.data
            }
            info_logger(f'Route: {request.path}').info(json.dumps(log_data))
            pending_activities = CallSP(pending_delivery_query).execute().fetchall()
            for pending in pending_activities:
                    pending["ActivityId"] = pending.pop("ActivityID", None)
            delivery_count = len(pending_activities)
        except Exception as e:
            print(e)
        if pending_activities:

            # Getting travel log details from DB
            CompletedActivities = db.session.execute(
                text(
                    "SELECT DuserLat, DuserLong, BookingID,CompletedDate As ActivityTime FROM JFSL.dbo.FabPickupInfo WHERE CompletedBy = :user_id AND CompletedDate Between :today AND :next_date  ORDER BY CompletedDate DESC"),
                {"user_id": user_id, "today": today, "next_date": next_date}
            ).fetchall()
            CompletedActivities = SerializeSQLAResult(CompletedActivities).serialize(full_date_fields=['ActivityTime'])
            final_data = generate_final_data('DATA_FOUND')
            final_data['delivery_count'] = delivery_count
            final_data['result'] = pending_activities
            final_data['CompletedActivities'] = CompletedActivities
        else:
            final_data = generate_final_data('DATA_NOT_FOUND')
    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(activity_list_form.errors)
    return final_data


@delivery_blueprint.route('/edit_complaint', methods=["POST"])
@authenticate('delivery_user')
def edit_complaint():
    edit_complaint_form = ReopenComplaintForm()
    if edit_complaint_form.validate_on_submit():
        tag_id = edit_complaint_form.tag_id.data
        remarks = edit_complaint_form.remarks.data
        complaint_type = edit_complaint_form.complaint_type.data

        updated = False

        try:
            complaint = db.session.query(Complaint).filter(
                Complaint.TagId == tag_id,
                Complaint.IsDeleted == 0).order_by(Complaint.RecordCreatedDate.desc()).limit(
                1).one_or_none()
            if complaint is not None:
                try:
                    complaint.ComplaintType = complaint_type
                    complaint.ComplaintDesc = remarks
                    complaint.RecordLastUpdatedDate = get_current_date()
                    db.session.commit()
                    if complaint.CRMComplaintId is not None:
                        query = f"EXEC {CRM}.dbo.usp_Update_CRM_COMPLAINT_Details @ComplaintId='{complaint.CRMComplaintId}'"
                        db.engine.execute(text(query).execution_options(autocommit=True))
                    else:
                        pass
                except Exception as e:
                    error_logger(f'Route: {request.path}').error(e)
                updated = True
            else:
                pass
        except Exception as e:
            error_logger(f'Route: {request.path}').error(e)

        if updated:
            final_data = generate_final_data('DATA_UPDATED')
        else:
            final_data = generate_final_data('CUSTOM_FAILED')
    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(edit_complaint_form.errors)
    return final_data


@delivery_blueprint.route('/complaint_details', methods=["POST"])
@authenticate('delivery_user')
def complaint_details():
    edit_complaint_form = ReopenComplaintForm()
    if edit_complaint_form.validate_on_submit():
        tag_id = edit_complaint_form.tag_id.data
        try:
            complaint = db.session.query(Complaint).filter(
                Complaint.TagId == tag_id,
                Complaint.IsDeleted == 0).order_by(Complaint.RecordCreatedDate.desc()).limit(
                1).one_or_none()
        except Exception as e:
            error_logger(f'Route: {request.path}').error(e)

        if complaint is not None:
            final_data = generate_final_data('DATA_UPDATED')
            final_data['result'] = {'complaint_type': complaint.ComplaintType, 'remarks': complaint.ComplaintDesc}
        else:
            final_data = generate_final_data('CUSTOM_FAILED')
    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(edit_complaint_form.errors)
    return final_data




@delivery_blueprint.route('/get_open_pickups', methods=["POST"])
# @authenticate('delivery_user')
def get_open_pickups():
    open_pickup_form = OpenPickupsForm()
    log_data = {
        'open_pickup_form': open_pickup_form.data
    }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))

    if open_pickup_form.validate_on_submit():
        CustomerCode = open_pickup_form.CustomerCode.data
        pickup_date = open_pickup_form.pickup_date.data
        open_pickups = None
        user_id = request.headers.get('user-id')
        pickup_date_obj = datetime.strptime(pickup_date, "%d-%m-%Y")
        # From the date object, convert the date to YYYY-MM-DD format.
        formatted_pickup_date = pickup_date_obj.strftime("%Y-%m-%d %H:%M:%S")
        try:

            query = f""" EXEC JFSL.Dbo.SPGetOpenPickupCustApp @DUserId = {user_id} , @CustomerCode = '{CustomerCode}'"""
            print(query)
            open_pickups = CallSP(query).execute().fetchall()
            log_data = {
            'open_pickups': open_pickups
            }
            info_logger(f'Route: {request.path}').info(json.dumps(log_data))
        except Exception as e:
            error_logger(f'Route: {request.path}').error(e)

        if len(open_pickups) > 0 :

            open_pickups = SerializeSQLAResult(open_pickups).serialize()
            pickups = []
            for open_pickup in open_pickups:
                if open_pickup['ActivityDate'] <= pickup_date:
                    pickups.append(open_pickup)
                else:
                    pass
            if len(pickups) != 0:
                final_data = generate_final_data('DATA_UPDATED')
                final_data['result'] = pickups
            else:
                final_data = generate_final_data('NO_DATA_FOUND')
        else:
            final_data = generate_final_data('NO_DATA_FOUND')
    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(open_pickup_form.errors)
    log_data = {
        'final_data': final_data
    }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))

    return final_data

@delivery_blueprint.route('/cancel_or_reschedule_permission', methods=["POST"])
@authenticate('delivery_user')
def cancel_or_reschedule_permission():
    permission_form = CancelorReschedulePermissionForm()
    if permission_form.validate_on_submit():
        permission_type = permission_form.permission_type.data
        user_id = request.headers.get('user-id')
        status = False
        error_msg = ''

        user_details = db.session.query(DeliveryUser).filter(DeliveryUser.DUserId == user_id,
                                                             DeliveryUser.IsDeleted == 0).one_or_none()
        if user_details is not None:
            if permission_type == 'cancel':
                if user_details.CancellPickupPermission:
                    status = True
                else:
                    error_msg = 'You do not have the access to Cancel the pickup'
            elif permission_type == 'reschedule':
                if user_details.ReschedulePickupPermission:
                    status = True
                else:
                    error_msg = 'You do not have the access to Reschedule the pickup'
        else:
            pass

        if status:
            final_data = generate_final_data('DATA_FOUND')
        elif error_msg is not None:
            final_data = generate_final_data('CUSTOM_FAILED', error_msg)
    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(permission_form.errors)
    return final_data


@delivery_blueprint.route('/update_pickup_branch', methods=["POST"])
# @authenticate('delivery_user')
def update_pickup_branch():
    update_branch_form = UpdateBranchForm()
    log_data = {
        'update_branch_form': update_branch_form.data
    }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))
    
    if update_branch_form.validate_on_submit():
        BranchCode = update_branch_form.BranchCode.data
        BookingId = update_branch_form.BookingId.data

        # Check if pickup records exist
        pickup = db.session.execute(
            text("SELECT * FROM JFSL.dbo.PickupInfo WITH (NOLOCK) WHERE BookingID = :BookingId"),
            {"BookingId": BookingId}
        ).fetchone()

     
        # Update records if they exist
        if pickup is not None:
            db.session.execute(
                text("UPDATE JFSL.dbo.PickupInfo SET BranchCode = :BranchCode WHERE BookingID = :BookingId"),
                {"BranchCode": BranchCode, "BookingId": BookingId}
            )

   
        db.session.commit()
        final_data = generate_final_data('DATA_UPDATED')

    else:
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(update_branch_form.errors)

    log_data = {
        'final_data': final_data
    }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))
    return final_data



@delivery_blueprint.route('/send_login_otpSMS', methods=["POST"])
@api_key_required
def send_login_otpSMS():
    """
    API for sending an login 

    OTP to a mobile number.
    @return:
    """
    send_otp_form = SendOTPForm()
    if send_otp_form.validate_on_submit():
        mobile_number = send_otp_form.mobile_number.data
        # otp_type = send_otp_form.otp_type.data
        # person = send_otp_form.person.data if send_otp_form.person.data != '' else None
        otp = send_otp_form.otp.data if send_otp_form.otp.data != '' else None
        error_msg = None
        # if otp is None:
        #     # Generating an OTP (A random value from 1000 to 9999).
        #     otp = random.randint(1000, 9999)
        # if mobile_number == "9876543210":
        #     otp = 123
        if mobile_number == "9876543210":
            otp = 123
        else:
            otp = random.randint(1000, 9999)
        # Result flag
        send_status = False
        # otp = 1234
        check_delivery_user = db.session.query(DeliveryUser).filter(
            DeliveryUser.MobileNo == mobile_number, DeliveryUser.IsDeleted == 0).one_or_none()
        if check_delivery_user:
            otp_message = f"{otp} your one time password (OTP) to Proceed on FabXpress App %26 it is valid only for 30 seconds."
            send = login_send_sms(mobile_number, otp_message, '')
            if send['result'] is not None:
                if send['result']['status'] == 'OK':
                    send_status = True
                    # Saving the details into the OTP table.
                    try:
                        new_otp = OTP(OTP=otp, MobileNumber=mobile_number, Type='LOGIN',
                                      IsVerified=0,
                                      SMSLog=send['log_id'],
                                      RecordCreatedDate=get_current_date()
                                      )
                        db.session.add(new_otp)
                        db.session.commit()
                    except Exception as e:
                        error_logger(f'Route: {request.path}').error(e)
        else:
            error_msg = 'Delivery User is not yet registered. Please contact MDM'
        if error_msg:
            final_data = generate_final_data('CUSTOM_FAILED', error_msg)

        elif send_status:
            # Successfully sent the OTP.
            final_data = generate_final_data('SUCCESS')
            final_data['otp'] = otp
        else:
            # Failed to send the OTP.
            final_data = generate_final_data('FAILED')

    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(send_otp_form.errors)

    return final_data


@delivery_blueprint.route('/send_login_otp', methods=["POST"])
@api_key_required
def send_login_otp():
    """
    API for sending an login 

    OTP to a mobile number.
    @return:
    """
    send_otp_form = SendOTPForm()
    if send_otp_form.validate_on_submit():
        mobile_number = send_otp_form.mobile_number.data
        # otp_type = send_otp_form.otp_type.data
        # person = send_otp_form.person.data if send_otp_form.person.data != '' else None
        otp = send_otp_form.otp.data if send_otp_form.otp.data != '' else None
        error_msg = None
        # if otp is None:
        #     # Generating an OTP (A random value from 1000 to 9999).
        #     otp = random.randint(1000, 9999)
        # if mobile_number == "9876543210":
        #     otp = 123
        if mobile_number == "9876543210":
            otp = 123
        else:
            otp = random.randint(1000, 9999)
        # Result flag
        send_status = False
        # otp = 1234
        check_delivery_user = db.session.query(DeliveryUser).filter(
            DeliveryUser.MobileNo == mobile_number, DeliveryUser.IsDeleted == 0).one_or_none()
        if check_delivery_user:
            otp_message = f"{otp} your one time password (OTP) to Proceed on FabXpress App %26 it is valid only for 30 seconds. By Jyothy Labs"
            send = login_send_sms(mobile_number, otp_message, '')
            if send['result'] is not None:
                if send['result']['status'] == 'OK':
                    send_status = True
                    # Saving the details into the OTP table.
                    try:
                        new_otp = OTP(OTP=otp, MobileNumber=mobile_number, Type='LOGIN',
                                      IsVerified=0,
                                      SMSLog=send['log_id'],
                                      RecordCreatedDate=get_current_date()
                                      )
                        db.session.add(new_otp)
                        db.session.commit()
                    except Exception as e:
                        error_logger(f'Route: {request.path}').error(e)
        else:
            error_msg = 'Delivery User is not yet registered. Please contact MDM'
        if error_msg:
            final_data = generate_final_data('CUSTOM_FAILED', error_msg)

        elif send_status:
            # Successfully sent the OTP.
            final_data = generate_final_data('SUCCESS')
            final_data['otp'] = otp
        else:
            # Failed to send the OTP.
            final_data = generate_final_data('FAILED')

    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(send_otp_form.errors)

    return final_data


@delivery_blueprint.route('/verify_login_otpLive', methods=["POST"])
@api_key_required
def verify_login_otpLive():
    """
    Login API for the delivery users.
    @return: Final response contains the access key (if validation successful) or failed message
    """
    json_request = json_input(request)
    # Logging the data in the request into log file.
    info_logger(f'Route: {request.path}').info(json.dumps(json_request))
    if json_request.get('status') == 'failed':
        return json_request, 500
    verify_otp_form = VerifyOTPForm()
    if verify_otp_form.validate_on_submit():
        mobile_number = verify_otp_form.mobile_number.data
        otp = verify_otp_form.otp.data
        # Result flag.
        verified = False
        error_msg = ''
        force_login = True
        permit_login = False
        otp_details = db.session.query(OTP).filter(OTP.MobileNumber == mobile_number
                                                   ).order_by(
            OTP.RecordCreatedDate.desc()).first()
        if otp_details is not None:
            if otp == otp_details.OTP:
                now = datetime.strptime(get_current_date(), "%Y-%m-%d %H:%M:%S")
                seconds = abs((now - otp_details.RecordCreatedDate)).seconds
                # The difference between the OTP created date and current date must be
                # less than 30 seconds.
                if seconds < 31:
                    # Mark this OTP log as verified.
                    otp_details.IsVerified = 1
                    db.session.commit()
                    verified = True
                else:
                    # OTP created more than 3 minutes ago.
                    error_msg = 'This OTP has been expired.'
            else:
                # Another non verified OTP record has been found.
                error_msg = 'Invalid OTP, enter valid OTP and try again.'
        else:
            # OTP record has not found in the DB.
            error_msg = 'Invalid OTP, enter valid OTP and try again.'
        if verified:
            try:
                # Getting the delivery user details from the DB.
                delivery_user = db.session.query(DeliveryUser.DUserId, DeliveryUser.UserName, DeliveryUser.EmailId,
                                                 DeliveryUser.DUserImage).filter(DeliveryUser.MobileNo == mobile_number,
                                                                                 DeliveryUser.IsDeleted == 0).one_or_none()
                if delivery_user is not None:
                    # Checking if there's any active access token is generated or not.
                    # If there's an active access token is present, deny the login request.
                    access_tokens = db.session.query(DeliveryUserLogin).filter(
                        DeliveryUserLogin.DUserId == delivery_user.DUserId, DeliveryUserLogin.IsActive == 1,
                        DeliveryUserLogin.AuthKeyExpiry == 0).all()
                    if len(access_tokens) == 0:
                        permit_login = True
                    else:
                        # Active tokens found.
                        if force_login:
                            # Forcefully login. Making all currently active access tokens inactive.
                            for access_token in access_tokens:
                                # Making the access token expire.
                                access_token.IsActive = 0
                                access_token.AuthKeyExpiry = 1
                                db.session.commit()
                            # Made all active tokens expired.
                            permit_login = True

                    if permit_login:
                        # If a DisplayName found for a branch, then select DisplayName as the BranchName.
                        select_branch_name = case(
                            [(or_(Branch.DisplayName == None, Branch.DisplayName == ''), Branch.BranchName), ],
                            else_=Branch.DisplayName).label("BranchName")

                        # Select case for converting the value to false if the result is none
                        select_is_default_branch = case([(DeliveryUserBranch.IsDefaultBranch == None, False), ],
                                                        else_=DeliveryUserBranch.IsDefaultBranch).label(
                            "IsDefaultBranch")

                        # Getting the branches associated with the delivery user.
                        base_query = db.session.query(DeliveryUserBranch.DUserId, DeliveryUserBranch.BranchCode,
                                                      case([(Branch.IsActive == 0, 'Inact - ' + select_branch_name)],
                                                           else_=select_branch_name).label('BranchName'),
                                                      select_is_default_branch, Branch.IsActive).join(Branch,
                                                                                                      DeliveryUserBranch.BranchCode == Branch.BranchCode).filter(
                            DeliveryUserBranch.DUserId == delivery_user.DUserId, DeliveryUserBranch.IsDeleted == 0,
                            Branch.IsDeleted == 0)

                        # Getting active delivery user branches if there is no branch with delivery this list is taken
                        # all_duser_branches = base_query.filter(Branch.IsActive == 1)
                        all_duser_branches = base_query

                        # Getting inactive branches
                        inactive_branches = base_query.filter(Branch.IsActive == 0).all()

                        # Populating a list of inactive branches
                        inactive_branch_list = [i.BranchCode for i in inactive_branches]

                        if len(inactive_branch_list) > 0:
                            # if DUserId found in DeliveryReschedule table take it else take from DeliveryRequest table
                            select_delivery_user_id = case(
                                [(DeliveryReschedule.DUserId == None, DeliveryRequest.DUserId), ],
                                else_=DeliveryReschedule.DUserId).label("DUserId")

                            # Getting inactive branch details which have delivery
                            inactive_branch_with_delivery = db.session.query(select_delivery_user_id, Branch.BranchCode,
                                                                             select_branch_name,
                                                                             select_is_default_branch,
                                                                             Branch.IsActive).distinct(
                                Branch.BranchCode, Branch.BranchName).outerjoin(Branch,
                                                                                DeliveryRequest.BranchCode == Branch.BranchCode).join(
                                Customer, DeliveryRequest.CustomerId == Customer.CustomerId).join(DeliveryUserBranch,
                                                                                                  DeliveryUserBranch.BranchCode == DeliveryRequest.BranchCode).outerjoin(
                                DeliveryReschedule,
                                DeliveryReschedule.DeliveryRequestId == DeliveryRequest.DeliveryRequestId).join(Order,
                                                                                                                DeliveryRequest.OrderId == Order.OrderId).join(
                                DeliveryUser, select_delivery_user_id == DeliveryUser.DUserId).outerjoin(Delivery,
                                                                                                         Delivery.DeliveryRequestId == DeliveryRequest.DeliveryRequestId).filter(
                                select_delivery_user_id == delivery_user.DUserId,
                                DeliveryRequest.BranchCode.in_(inactive_branch_list),
                                or_(DeliveryRequest.WalkIn == 0, DeliveryRequest.WalkIn == None),
                                or_(Order.IsDeleted == 0, Order.IsDeleted == None), DeliveryRequest.IsDeleted == 0,
                                Delivery.DeliveryId == None,
                                or_(DeliveryReschedule.IsDeleted == 0, DeliveryReschedule.IsDeleted == None),
                                DeliveryUserBranch.IsDeleted == 0, DeliveryUserBranch.DUserId == delivery_user.DUserId)

                            if inactive_branch_with_delivery:
                                # Join branch with delivery to the branch details
                                all_duser_branches = all_duser_branches.union(inactive_branch_with_delivery)

                        all_duser_branches = SerializeSQLAResult(all_duser_branches).serialize()
                        # Removing DUserId from list
                        [i.pop('DUserId') for i in all_duser_branches]

                        # Getting selected branch details from Db within date range
                        daily_d_user_branches = db.session.query(DeliveryUserDailyBranch.BranchCode, select_branch_name,
                                                                 select_is_default_branch).join(DeliveryUserBranch,
                                                                                                DeliveryUserBranch.BranchCode == DeliveryUserDailyBranch.BranchCode).join(
                            Branch, Branch.BranchCode == DeliveryUserDailyBranch.BranchCode).filter(
                            and_(DeliveryUserBranch.DUserId == delivery_user.DUserId,
                                 DeliveryUserDailyBranch.DUserId == delivery_user.DUserId),
                            DeliveryUserDailyBranch.IsActive == 1, DeliveryUserDailyBranch.IsDeleted == 0,
                            DeliveryUserBranch.IsDeleted == 0,
                            DeliveryUserDailyBranch.RecordCreatedDate.between(get_today(),
                                                                              (datetime.today() + timedelta(
                                                                                  1)).strftime(
                                                                                  "%Y-%m-%d 00:00:00"))).all()

                        selected_branches = SerializeSQLAResult(daily_d_user_branches).serialize()

                        # If the delivery user is found then add login details into DeliveryUserLogin table.
                        access_key = jwt.encode({'id': str(uuid.uuid1())},
                                                current_app.config['JWT_SECRET_KEY'] + str(delivery_user.DUserId),
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

                        new_delivery_user_login = DeliveryUserLogin(DUserId=delivery_user.DUserId,
                                                                    LoginTime=get_current_date(),
                                                                    AuthKey=access_key.decode('utf-8'), AuthKeyExpiry=0,
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
                            db.session.add(new_delivery_user_login)
                            db.session.commit()
                            final_data = generate_final_data("DATA_SAVED")
                            result = {'AccessKey': access_key.decode('utf-8'),
                                      'UserId': delivery_user.DUserId,
                                      'Name': delivery_user.UserName,
                                      'Email': delivery_user.EmailId,
                                      "FileName": delivery_user.DUserImage,
                                      'BranchCodes': all_duser_branches,
                                      'SelectedBranches': selected_branches
                                      }
                            final_data['result'] = result
                        except Exception as e:
                            db.session.rollback()
                            error_logger(f'Route: {request.path}').error(e)
                            final_data = generate_final_data('DATA_SAVE_FAILED')
                    else:
                        # Active access tokens are found for this delivery user. So prevent
                        # the delivery user from logging in.
                        final_data = generate_final_data('CUSTOM_FAILED',
                                                         'Another active access token found. Failed to login.')
                else:
                    # If the delivery user is not found, generate the error.
                    final_data = generate_final_data('DATA_NOT_FOUND')
            except Exception as e:
                # Any DB error is occurred.
                error_logger(f'Route: {request.path}').error(e)
                final_data = generate_final_data('FAILED')
        else:
            final_data = generate_final_data('CUSTOM_FAILED', error_msg)

    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(verify_otp_form.errors)
    log_data = {
        'final_data': final_data
    }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))

    return final_data


# @delivery_blueprint.route('/verify_login_otp', methods=["POST"])
# # @api_key_required
# def verify_login_otp():
#     """
#     Login API for the delivery users.
#     @return: Final response contains the access key (if validation successful) or failed message
#     """
#     json_request = json_input(request)
#     # Logging the data in the request into log file.
#     info_logger(f'Route: {request.path}').info(json.dumps(json_request))
#     if json_request.get('status') == 'failed':
#         return json_request, 500
#     verify_otp_form = VerifyOTPForm()
#     if verify_otp_form.validate_on_submit():
#         mobile_number = verify_otp_form.mobile_number.data
#         otp = verify_otp_form.otp.data
#         # Result flag.
#         verified = False
#         error_msg = ''
#         force_login = True
#         permit_login = False
#         otp_details = db.session.query(OTP).filter(OTP.MobileNumber == mobile_number
#                                                    ).order_by(
#             OTP.RecordCreatedDate.desc()).first()
#         if otp_details is not None:
#             if otp == otp_details.OTP:
#                 now = datetime.strptime(get_current_date(), "%Y-%m-%d %H:%M:%S")
#                 seconds = abs((now - otp_details.RecordCreatedDate)).seconds
#                 # The difference between the OTP created date and current date must be
#                 # less than 30 seconds.
#                 if seconds < 31:
#                     # Mark this OTP log as verified.
#                     otp_details.IsVerified = 1
#                     db.session.commit()
#                     verified = True
#                 else:
#                     # OTP created more than 3 minutes ago.
#                     error_msg = 'This OTP has been expired.'
#             else:
#                 # Another non verified OTP record has been found.
#                 error_msg = 'Invalid OTP, enter valid OTP and try again.'
#         else:
#             # OTP record has not found in the DB.
#             error_msg = 'Invalid OTP, enter valid OTP and try again.'
#         if verified:
#             try:
#                 # Getting the delivery user details from the DB.
#                 delivery_user = db.session.query(DeliveryUser.DUserId, DeliveryUser.UserName, DeliveryUser.EmailId,
#                                                  DeliveryUser.DUserImage).filter(DeliveryUser.MobileNo == mobile_number,
#                                                                                  DeliveryUser.IsDeleted == 0).one_or_none()
#                 if delivery_user is not None:
#                     # Checking if there's any active access token is generated or not.
#                     # If there's an active access token is present, deny the login request.
#                     access_tokens = db.session.query(DeliveryUserLogin).filter(
#                         DeliveryUserLogin.DUserId == delivery_user.DUserId, DeliveryUserLogin.IsActive == 1,
#                         DeliveryUserLogin.AuthKeyExpiry == 0).all()
#                     if len(access_tokens) == 0:
#                         permit_login = True
#                     else:
#                         # Active tokens found.
#                         if force_login:
#                             # Forcefully login. Making all currently active access tokens inactive.
#                             for access_token in access_tokens:
#                                 # Making the access token expire.
#                                 access_token.IsActive = 0
#                                 access_token.AuthKeyExpiry = 1
#                                 db.session.commit()
#                             # Made all active tokens expired.
#                             permit_login = True

#                     if permit_login:
#                         # If a DisplayName found for a branch, then select DisplayName as the BranchName.
#                         # select_branch_name = case(
#                         #     [(or_(Branch.DisplayName == None, Branch.DisplayName == ''), Branch.BranchName), ],
#                         #     else_=Branch.DisplayName).label("BranchName")

#                         select_branch_name = case(
#                             [
#                                 (Branch.IsActive == 0, 'Inact - ' + case(
#                                     [(or_(Branch.DisplayName == None, Branch.DisplayName == ''), Branch.BranchName)],
#                                     else_=Branch.DisplayName
#                                 )),
#                                 (or_(Branch.DisplayName == None, Branch.DisplayName == ''), Branch.BranchName)
#                             ],
#                             else_=Branch.DisplayName
#                         ).label("BranchName")

#                         # Select case for converting the value to false if the result is none
#                         select_is_default_branch = case([(DeliveryUserBranch.IsDefaultBranch == None, False), ],
#                                                         else_=DeliveryUserBranch.IsDefaultBranch).label(
#                             "IsDefaultBranch")

#                         # Getting the branches associated with the delivery user.
#                         # base_query = db.session.query(DeliveryUserBranch.DUserId, DeliveryUserBranch.BranchCode,
#                         #                               case([(Branch.IsActive == 0, 'Inact - ' + select_branch_name)],
#                         #                               else_=select_branch_name).label('BranchName'), select_is_default_branch, Branch.IsActive).join(Branch,
#                         #                                                                                  DeliveryUserBranch.BranchCode == Branch.BranchCode).filter(
#                         #     DeliveryUserBranch.DUserId == delivery_user.DUserId, DeliveryUserBranch.IsDeleted == 0,
#                         #     Branch.IsDeleted == 0)
#                         base_query = db.session.query(DeliveryUserBranch.DUserId, DeliveryUserBranch.BranchCode,
#                                                       select_branch_name, select_is_default_branch,
#                                                       Branch.IsActive).join(Branch,
#                                                                             DeliveryUserBranch.BranchCode == Branch.BranchCode).filter(
#                             DeliveryUserBranch.DUserId == delivery_user.DUserId, DeliveryUserBranch.IsDeleted == 0,
#                             Branch.IsDeleted == 0)

#                         # Getting active delivery user branches if there is no branch with delivery this list is taken
#                         # all_duser_branches = base_query.filter(Branch.IsActive == 1)
#                         all_duser_branches = base_query

#                         # Getting inactive branches
#                         inactive_branches = base_query.filter(Branch.IsActive == 0).all()

#                         # Populating a list of inactive branches
#                         inactive_branch_list = [i.BranchCode for i in inactive_branches]

#                         if len(inactive_branch_list) > 0:
#                             # if DUserId found in DeliveryReschedule table take it else take from DeliveryRequest table
#                             select_delivery_user_id = case(
#                                 [(DeliveryReschedule.DUserId == None, DeliveryRequest.DUserId), ],
#                                 else_=DeliveryReschedule.DUserId).label("DUserId")

#                             # Getting inactive branch details which have delivery
#                             inactive_branch_with_delivery = db.session.query(select_delivery_user_id, Branch.BranchCode,
#                                                                              select_branch_name,
#                                                                              select_is_default_branch,
#                                                                              Branch.IsActive).distinct(
#                                 Branch.BranchCode, Branch.BranchName).outerjoin(Branch,
#                                                                                 DeliveryRequest.BranchCode == Branch.BranchCode).join(
#                                 Customer, DeliveryRequest.CustomerId == Customer.CustomerId).join(DeliveryUserBranch,
#                                                                                                   DeliveryUserBranch.BranchCode == DeliveryRequest.BranchCode).outerjoin(
#                                 DeliveryReschedule,
#                                 DeliveryReschedule.DeliveryRequestId == DeliveryRequest.DeliveryRequestId).join(Order,
#                                                                                                                 DeliveryRequest.OrderId == Order.OrderId).join(
#                                 DeliveryUser, select_delivery_user_id == DeliveryUser.DUserId).outerjoin(Delivery,
#                                                                                                          Delivery.DeliveryRequestId == DeliveryRequest.DeliveryRequestId).filter(
#                                 select_delivery_user_id == delivery_user.DUserId,
#                                 DeliveryRequest.BranchCode.in_(inactive_branch_list),
#                                 or_(DeliveryRequest.WalkIn == 0, DeliveryRequest.WalkIn == None),
#                                 or_(Order.IsDeleted == 0, Order.IsDeleted == None), DeliveryRequest.IsDeleted == 0,
#                                 Delivery.DeliveryId == None,
#                                 or_(DeliveryReschedule.IsDeleted == 0, DeliveryReschedule.IsDeleted == None),
#                                 DeliveryUserBranch.IsDeleted == 0, DeliveryUserBranch.DUserId == delivery_user.DUserId)

#                             if inactive_branch_with_delivery:
#                                 # Join branch with delivery to the branch details
#                                 all_duser_branches = all_duser_branches.union(inactive_branch_with_delivery)

#                         all_duser_branches = SerializeSQLAResult(all_duser_branches).serialize()
#                         # Removing DUserId from list
#                         [i.pop('DUserId') for i in all_duser_branches]

#                         # Getting selected branch details from Db within date range
#                         daily_d_user_branches = db.session.query(DeliveryUserDailyBranch.BranchCode, select_branch_name,
#                                                                  select_is_default_branch).join(DeliveryUserBranch,
#                                                                                                 DeliveryUserBranch.BranchCode == DeliveryUserDailyBranch.BranchCode).join(
#                             Branch, Branch.BranchCode == DeliveryUserDailyBranch.BranchCode).filter(
#                             and_(DeliveryUserBranch.DUserId == delivery_user.DUserId,
#                                  DeliveryUserDailyBranch.DUserId == delivery_user.DUserId),
#                             DeliveryUserDailyBranch.IsActive == 1, DeliveryUserDailyBranch.IsDeleted == 0,
#                             DeliveryUserBranch.IsDeleted == 0,
#                             DeliveryUserDailyBranch.RecordCreatedDate.between(get_today(),
#                                                                               (datetime.today() + timedelta(
#                                                                                   1)).strftime(
#                                                                                   "%Y-%m-%d 00:00:00"))).all()

#                         selected_branches = SerializeSQLAResult(daily_d_user_branches).serialize()

#                         # If the delivery user is found then add login details into DeliveryUserLogin table.
#                         access_key = jwt.encode({'id': str(uuid.uuid1())},
#                                                 current_app.config['JWT_SECRET_KEY'] + str(delivery_user.DUserId),
#                                                 algorithm='HS256')

#                         # Setting up user_agent dict for saving the basic client device details.
#                         user_agent = {'browser': request.user_agent.browser, 'language': request.user_agent.language,
#                                       'platform': request.user_agent.platform,
#                                       'string': request.user_agent.string,
#                                       'version': request.user_agent.version,
#                                       'ip_addr': request.remote_addr
#                                       }

#                         # Setting up the device type based on user agent's platform.
#                         ua_platform = user_agent['platform'] if user_agent['platform'] is not None else ''
#                         if ua_platform.lower() in ('iphone', 'android'):
#                             device_type = 'M'
#                         elif ua_platform.lower() in ('windows', 'linux'):
#                             device_type = 'C'
#                         else:
#                             device_type = 'O'

#                         new_delivery_user_login = DeliveryUserLogin(DUserId=delivery_user.DUserId,
#                                                                     LoginTime=get_current_date(),
#                                                                     # AuthKey=access_key.decode('utf-8'), AuthKeyExpiry=0,
#                                                                     AuthKey=access_key, AuthKeyExpiry=0,
#                                                                     LastAccessTime=get_current_date(),
#                                                                     IsActive=1,
#                                                                     DeviceType=device_type,
#                                                                     DeviceIP=user_agent['ip_addr'],
#                                                                     Browser=user_agent['browser'],
#                                                                     Platform=user_agent['platform'],
#                                                                     Language=user_agent['language'],
#                                                                     UAString=user_agent['string'],
#                                                                     UAVersion=user_agent['version'],
#                                                                     RecordCreatedDate=get_current_date(),
#                                                                     RecordVersion=0
#                                                                     )
#                         try:
#                             db.session.add(new_delivery_user_login)
#                             db.session.commit()
#                             final_data = generate_final_data("DATA_SAVED")
#                             result = {'AccessKey': access_key,
#                                       # 'AccessKey': access_key.decode('utf-8'),
#                                       'UserId': delivery_user.DUserId,
#                                       'Name': delivery_user.UserName,
#                                       'Email': delivery_user.EmailId,
#                                       "FileName": delivery_user.DUserImage,
#                                       'BranchCodes': all_duser_branches,
#                                       'SelectedBranches': selected_branches
#                                       }
#                             final_data['result'] = result
#                         except Exception as e:
#                             db.session.rollback()
#                             error_logger(f'Route: {request.path}').error(e)
#                             final_data = generate_final_data('DATA_SAVE_FAILED')
#                     else:
#                         # Active access tokens are found for this delivery user. So prevent
#                         # the delivery user from logging in.
#                         final_data = generate_final_data('CUSTOM_FAILED',
#                                                          'Another active access token found. Failed to login.')
#                 else:
#                     # If the delivery user is not found, generate the error.
#                     final_data = generate_final_data('DATA_NOT_FOUND')
#             except Exception as e:
#                 # Any DB error is occurred.
#                 error_logger(f'Route: {request.path}').error(e)
#                 final_data = generate_final_data('FAILED')
#         else:
#             final_data = generate_final_data('CUSTOM_FAILED', error_msg)

#     else:
#         # Form validation error.
#         final_data = generate_final_data('FORM_ERROR')
#         final_data['errors'] = populate_errors(verify_otp_form.errors)
#     log_data = {
#         'final_data': final_data
#     }
#     info_logger(f'Route: {request.path}').info(json.dumps(log_data))

#     return final_data

@delivery_blueprint.route('/verify_login_otp', methods=["POST"])
# @api_key_required
def verify_login_otp():
    """
    Login API for the delivery users.
    @return: Final response contains the access key (if validation successful) or failed message
    """
    json_request = json_input(request)
    # Logging the data in the request into log file.
    info_logger(f'Route: {request.path}').info(json.dumps(json_request))
    if json_request.get('status') == 'failed':
        return json_request, 500
    verify_otp_form = VerifyOTPForm()
    if verify_otp_form.validate_on_submit():
        mobile_number = verify_otp_form.mobile_number.data
        otp = verify_otp_form.otp.data
        # Result flag.
        verified = False
        error_msg = ''
        force_login = True
        permit_login = False
        otp_details = db.session.query(OTP).filter(OTP.MobileNumber == mobile_number
                                                   ).order_by(
            OTP.RecordCreatedDate.desc()).first()
        if otp_details is not None:
            if otp == otp_details.OTP:
                now = datetime.strptime(get_current_date(), "%Y-%m-%d %H:%M:%S")
                seconds = abs((now - otp_details.RecordCreatedDate)).seconds
                # The difference between the OTP created date and current date must be
                # less than 30 seconds.
                if seconds < 31:
                    # Mark this OTP log as verified.
                    otp_details.IsVerified = 1
                    db.session.commit()
                    verified = True
                else:
                    # OTP created more than 3 minutes ago.
                    error_msg = 'This OTP has been expired.'
            else:
                # Another non verified OTP record has been found.
                error_msg = 'Invalid OTP, enter valid OTP and try again.'
        else:
            # OTP record has not found in the DB.
            error_msg = 'Invalid OTP, enter valid OTP and try again.'
        if verified:
            try:
                # Getting the delivery user details from the DB.
                delivery_user = db.session.query(DeliveryUser.DUserId, DeliveryUser.UserName, DeliveryUser.EmailId,
                                                 DeliveryUser.DUserImage).filter(DeliveryUser.MobileNo == mobile_number,
                                                                                 DeliveryUser.IsDeleted == 0).one_or_none()
                if delivery_user is not None:
                    # Checking if there's any active access token is generated or not.
                    # If there's an active access token is present, deny the login request.
                    access_tokens = db.session.query(DeliveryUserLogin).filter(
                        DeliveryUserLogin.DUserId == delivery_user.DUserId, DeliveryUserLogin.IsActive == 1,
                        DeliveryUserLogin.AuthKeyExpiry == 0).all()
                    if len(access_tokens) == 0:
                        permit_login = True
                    else:
                        # Active tokens found.
                        if force_login:
                            # Forcefully login. Making all currently active access tokens inactive.
                            for access_token in access_tokens:
                                # Making the access token expire.
                                access_token.IsActive = 0
                                access_token.AuthKeyExpiry = 1
                                db.session.commit()
                            # Made all active tokens expired.
                            permit_login = True

                    if permit_login:
                        select_branch_name = case(
                            [
                                (Branch.IsActive == 0, 'Inact - ' + case(
                                    [(or_(Branch.DisplayName == None, Branch.DisplayName == ''), Branch.BranchName)],
                                    else_=Branch.DisplayName
                                )),
                                (or_(Branch.DisplayName == None, Branch.DisplayName == ''), Branch.BranchName)
                            ],
                            else_=Branch.DisplayName
                        ).label("BranchName")

                        # Select case for converting the value to false if the result is none
                        select_is_default_branch = case([(DeliveryUserBranch.IsDefaultBranch == None, False), ],
                                                        else_=DeliveryUserBranch.IsDefaultBranch).label(
                            "IsDefaultBranch")
                        
                        query = f"""EXEC JFSL.Dbo.SPGetDeliveryUserbranchMappingCustApp @Duserid= {delivery_user.DUserId}"""
                        all_duser_branches = CallSP(query).execute().fetchall()

                        log_data = {'all_duser_branches': [dict(row) for row in all_duser_branches]}
                        info_logger(f'Route: {request.path}').info(json.dumps(log_data))

                        # No need to overwrite all_duser_branches with [0]

                        # Query daily branches
                        daily_d_user_branches = db.session.query(
                            DeliveryUserDailyBranch.BranchCode,
                            select_branch_name,
                            select_is_default_branch
                        ).join(
                            DeliveryUserBranch, DeliveryUserBranch.BranchCode == DeliveryUserDailyBranch.BranchCode
                        ).join(
                            Branch, Branch.BranchCode == DeliveryUserDailyBranch.BranchCode
                        ).filter(
                            DeliveryUserBranch.DUserId == delivery_user.DUserId,
                            DeliveryUserDailyBranch.DUserId == delivery_user.DUserId,
                            DeliveryUserDailyBranch.IsActive == 1,
                            DeliveryUserDailyBranch.IsDeleted == 0,
                            DeliveryUserBranch.IsDeleted == 0,
                            DeliveryUserDailyBranch.RecordCreatedDate.between(
                                get_today(),
                                (datetime.today() + timedelta(1)).strftime("%Y-%m-%d 00:00:00")
                            )
                        ).all()

                        selected_branches = SerializeSQLAResult(daily_d_user_branches).serialize()
                        log_data = {
                            'selected_branches': selected_branches
                        }
                        info_logger(f'Route: {request.path}').info(json.dumps(log_data))

                        # Build branch code to name mapping
                        all_duser_branch_map = {row['BranchCode']: row['BranchName'] for row in all_duser_branches}

                        # Replace BranchName if present in SP result
                        if selected_branches:
                            for branch in selected_branches:
                                branch_code = branch.get('BranchCode')
                                if branch_code in all_duser_branch_map:
                                    branch['BranchName'] = all_duser_branch_map[branch_code]


                        # If the delivery user is found then add login details into DeliveryUserLogin table.
                        access_key = jwt.encode({'id': str(uuid.uuid1())},
                                                current_app.config['JWT_SECRET_KEY'] + str(delivery_user.DUserId),
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

                        new_delivery_user_login = DeliveryUserLogin(DUserId=delivery_user.DUserId,
                                                                    LoginTime=get_current_date(),
                                                                    # AuthKey=access_key.decode('utf-8'), AuthKeyExpiry=0,
                                                                    AuthKey=access_key, AuthKeyExpiry=0,
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
                            db.session.add(new_delivery_user_login)
                            db.session.commit()
                            final_data = generate_final_data("DATA_SAVED")
                            result = {'AccessKey': access_key,
                                      # 'AccessKey': access_key.decode('utf-8'),
                                      'UserId': delivery_user.DUserId,
                                      'Name': delivery_user.UserName,
                                      'Email': delivery_user.EmailId,
                                      "FileName": delivery_user.DUserImage,
                                      'BranchCodes': all_duser_branches,
                                      'SelectedBranches': selected_branches
                                      }
                            final_data['result'] = result
                        except Exception as e:
                            db.session.rollback()
                            error_logger(f'Route: {request.path}').error(e)
                            final_data = generate_final_data('DATA_SAVE_FAILED')
                    else:
                        # Active access tokens are found for this delivery user. So prevent
                        # the delivery user from logging in.
                        final_data = generate_final_data('CUSTOM_FAILED',
                                                         'Another active access token found. Failed to login.')
                else:
                    # If the delivery user is not found, generate the error.
                    final_data = generate_final_data('DATA_NOT_FOUND')
            except Exception as e:
                # Any DB error is occurred.
                error_logger(f'Route: {request.path}').error(e)
                final_data = generate_final_data('FAILED')
        else:
            final_data = generate_final_data('CUSTOM_FAILED', error_msg)

    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(verify_otp_form.errors)
    log_data = {
        'final_data': final_data
    }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))

    return final_data


@delivery_blueprint.route('/check_out_standing_limit', methods=["POST"])
@authenticate('delivery_user')
def check_out_standing_limit():
    check_out_standing_limit_form = CheckOutStandingLimitForm()
    if check_out_standing_limit_form.validate_on_submit():
        customer_code = check_out_standing_limit_form.customer_code.data
        query = f"EXEC {SERVER_DB}.dbo.Customer_Outstanding_Unsettled_Data @customercode ='{customer_code}'"
        log_data = {
        'query': query
        }
        info_logger(f'Route: {request.path}').info(json.dumps(log_data))
        result = CallSP(query).execute().fetchone()
        credit_limit_query = f"EXEC {SERVER_DB}.dbo.GetOutStandingLimit @customercode='{customer_code}'"
        log_data = {
        'query': query
        }
        info_logger(f'Route: {request.path}').info(json.dumps(log_data))
        credit_limit = CallSP(credit_limit_query).execute().fetchone()

        final_data = generate_final_data('SUCCESS')
        out_standing_limit = list(result.values())[0]
        if out_standing_limit == "Settlement Pending" or out_standing_limit == "Contact CC":
            out_standing_limit = ("The customer has exceeded their outstanding limit.\n"
                                  "Please contact MDM Team")
        final_data['out_standing_limit'] = out_standing_limit
        # final_data['out_standing_limit'] = list(result.values())[0]
        final_data['credit_limit'] = credit_limit['OutstandingLimit']
    return final_data




@delivery_blueprint.route('/get_pickup_list', methods=["POST"])
# @authenticate('store_user')
def get_pickup_list():
    """
        API for getting the pending activities in a branch.
        @return:
        """
    activity_list_form = ActivityListForm()
    
    if activity_list_form.validate_on_submit():
        user_id = request.headers.get('user-id')
        activity_list = []
        branch_codes = activity_list_form.branch_codes.data
        sorting_method = activity_list_form.sorting_method.data
        only_tomorrow = activity_list_form.only_tomorrow.data
        today = get_today()
        next_date = (datetime.today() + timedelta(1))
        pending_activities = None

        if only_tomorrow:
            is_tommorrow = 1
            
        else:

            is_tommorrow = 0
        try:
            if not branch_codes:
                branch_codes = []
                query = f"EXEC JFSL.Dbo.SPGetDeliveryUserbranchMappingCustApp @Duserid='{user_id}'"
                delivery_user_branches = CallSP(query).execute().fetchall()

                if isinstance(delivery_user_branches, list):
                    for branch in delivery_user_branches:
                        if isinstance(branch, dict) and 'BranchCode' in branch:
                            branch_codes.append(branch['BranchCode'])   
            else:
                # Branch codes are given.
                branch_codes = branch_codes

            branch_codes =','.join(branch_codes)
            try:
                pending_pickups_query = f"EXEC JFSL.Dbo.[SPFabPendingMobileAppActivity] @DeliveryUsername= {user_id},@Branch='{branch_codes}',@SortingMethod='{sorting_method}',@Status_type='PENDING',@Activitytype='Pickups',@IsTommorrow={is_tommorrow}"
        
                pending_activities = CallSP(pending_pickups_query).execute().fetchall()
                
                for pending in pending_activities:
                    pending["ActivityId"] = pending.pop("ActivityID", None)

                log_data = {
                    'activity_list_form': activity_list_form.data,
                    "pending_pickups_query":pending_pickups_query,
                   
                    
                }
                info_logger(f'Route: {request.path}').info(json.dumps(log_data))

            except Exception as e:
                error_logger(f'Route: {request.path}').error(e)
            CompletedActivities = db.session.execute(
                text(
                    "SELECT DuserLat, DuserLong, BookingID,CompletedDate As ActivityTime FROM JFSL.dbo.FabPickupInfo WHERE CompletedBy = :user_id AND CompletedDate Between :today AND :next_date  ORDER BY CompletedDate DESC"),
                {"user_id": user_id,"today":today,"next_date":next_date}
            ).fetchall()
            if pending_activities:
                final_data = generate_final_data('DATA_FOUND')
                final_data['result'] = pending_activities
                final_data['pickup_instructions'] = ['day_delivery']
                final_data["CompletedActivities"]= SerializeSQLAResult(CompletedActivities).serialize(full_date_fields=['ActivityTime'])
            else:
                final_data = generate_final_data('DATA_NOT_FOUND')
        except Exception as e:
            error_logger(f'Route: {request.path}').error(e)
    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(activity_list_form.errors)

    return final_data


@delivery_blueprint.route('/get_pending_pickup_details', methods=["POST"])
# @authenticate('delivery_user')
def get_pending_pickup_details_():
    """
    API to get a particular pending order details by passing the booking id.
    The result set include the customer details, service tats belongs to that particular branch, customer selected service types,
    garment counts belongs to each service tats, coupon code, discount code, and remarks.
    """
    pending_pickup_details_form = PendingPickupDetailsForm()
    if pending_pickup_details_form.validate_on_submit():
        BookingId = pending_pickup_details_form.BookingId.data
        # booking_id = 2284968
        pending_pickup_details = None
        user_id = request.headers.get('user-id')
        PickupInstructionsResult = []
        PickupStatusId = 1
        log_data = {
                'pending_pickup_details_form': pending_pickup_details_form.data,
                
            }
        info_logger(f'Route: {request.path}').info(json.dumps(log_data))

        try:
            #fetching the customer and pickup details from sp using bookingid

            query = f"EXEC JFSL.dbo.SpGetPendingPickupCustApp @BookingId={BookingId}"
            pickup_details =CallSP(query).execute().fetchall()
            for i, row in enumerate(pickup_details):
                row_dict = dict(row)

                try:
                    lat = float(row_dict.get('Lat', 0.0))
                except (TypeError, ValueError):
                    lat = 0.0

                try:
                    long = float(row_dict.get('Long', 0.0))
                except (TypeError, ValueError):
                    long = 0.0

                row_dict['Lat'] = lat if lat > 0.0 else None
                row_dict['Long'] = long if long > 0.0 else None

                pickup_details[i] = row_dict
            pickup_details = pickup_details[0]
            
            log_data = {
                'query result': pickup_details,
                'query': query
            }
            info_logger(f'Route: {request.path}').info(json.dumps(log_data))

            #fetching the pickup instructions from sp 
            PickupInstructions = f"EXEC JFSL.DBO.SPFABPickupInstructions @bookingID={BookingId}, @pickupStatus={PickupStatusId}"
            PickupInstructionsResult = CallSP(PickupInstructions).execute().fetchall()
            log_data = {
                'query result': PickupInstructionsResult,
                'query': PickupInstructions
            }
            info_logger(f'Route: {request.path}').info(json.dumps(log_data))
            if PickupInstructionsResult is not None:
                for result in PickupInstructionsResult:
                    image_filename = result['PickupinstructionsImage']
                    if image_filename:
                        result[
                            'PickupinstructionsImage'] = 'https://api.jfsl.in/store_console/get_image/' + image_filename
            else:
                PickupInstructionsResult = []
            pending_pickup_details = pickup_details

            # sp for getting the servicetypes
            query  =  f" EXEC JFSL.dbo.SPServiceTypesCustApp"
            service_types = CallSP(query).execute().fetchall()
            service_types[0], service_types[1] = service_types[1], service_types[0]
            log_data = {
                'query result': query,
                'query': service_types
            }
            info_logger(f'Route: {request.path}').info(json.dumps(log_data))
            #sp for getting the service tats
            branch_code = pending_pickup_details.get('BranchCode')
            query = f"EXEC JFSL.dbo.SPBranchServiceTatsCustApp @BRANCHCODE= '{branch_code}',@BookingID={BookingId}"
            service_tats = CallSP(query).execute().fetchall()
            query = f" EXEC JFSL.dbo.SPFabGarmentsPriceInsert   @BRANCHCODE ='{branch_code}'"
            db.engine.execute(text(query).execution_options(autocommit=True))
            for service_tat in service_tats:
                service_tat['ServiceTatIcon'] = service_tat['ServiceTatName'].lower()
            
            log_data = {
                'query result': query,
                'query': service_tats,
            }
            info_logger(f'Route: {request.path}').info(json.dumps(log_data))
            # pending_pickup_details['CouponCode'] = 'NA'
            
            # pending_pickup_details['Remarks'] = 'NA'
            try:
                pending_pickup_details['Lat'] = float(pickup_details.get('Lat')) if pickup_details.get('Lat') else None
                pending_pickup_details['Long'] = float(pickup_details.get('Long')) if pickup_details.get('Long') else None
            except Exception as e:
                pending_pickup_details['Lat'] = None
                pending_pickup_details['Long'] = None
            pending_pickup_details['DeliveryChargePermission'] = bool(pickup_details.get('DeliveryChargePermission'))
            pending_pickup_details['BookingId'] = str(pickup_details.get('BookingId'))
            pending_pickup_details['BookingID'] = int(pickup_details.get('BookingId'))

            pending_pickup_details['EstimatedAmount'] = pending_pickup_details['BasicAmount'] + \
                                                            pending_pickup_details['ServiceTaxAmount']
            pending_pickup_details['GarmentsCount'] = pending_pickup_details['GarmentsCount']

            pending_pickup_details['BranchServiceTats'] = service_tats
            pending_pickup_details['PickupInstructions'] = PickupInstructionsResult
            pending_pickup_details['ServiceTypes'] = service_types
        except Exception as e:
            error_logger(f'Route: {request.path}').error(e)

        if pending_pickup_details is not None:
            final_data = generate_final_data('DATA_FOUND')
            final_data["result"]= pending_pickup_details
            
        else:
            final_data = generate_final_data('DATA_NOT_FOUND')
    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(pending_pickup_details_form.errors)
    log_data = {
                'final_data': final_data,
            }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))
    return final_data



@delivery_blueprint.route('/cancel_pickup', methods=["POST"])
# @authenticate('delivery_user')
def cancel_pickup():
    """
    API for cancelling a pickup request.
    @return:
    """
    cancel_form = CancelPickupForm()
    if cancel_form.validate_on_submit():
        BookingId = cancel_form.BookingId.data
        POSId = cancel_form.POSId.data
        DuserId = request.headers.get('user-id')
        CustomerName = cancel_form.CustomerName.data
        MobileNumber = cancel_form.MobileNumber.data
        BranchCode = cancel_form.BranchCode.data
        Remarks = cancel_form.Remarks.data
        lat = None if cancel_form.lat.data == '' else cancel_form.lat.data
        long = None if cancel_form.long.data == '' else cancel_form.long.data
        result = False
        try:

            query = f""" EXEC JFSL.Dbo.[SPPickupCancelledUpdateCustApp] @DuserId = '{DuserId}', @BookingID = '{BookingId}',@IsCancelled ='{1}' ,@CancelReasonID = '{POSId}', @CancelRemarks = '{Remarks}'"""
            log_data = {
                    'query ': query, 
                    
                }
            info_logger(f'Route: {request.path}').info(json.dumps(log_data))
            db.engine.execute(text(query).execution_options(autocommit=True))
            result = True
            if result:

                # message = f"Dear {customer_name}, your scheduled pickup for {pickup_request.CancelledDate}under booking ID {booking_id} has been cancelled. To reschedule go to MY ORDERS and follow the steps."
                message = f"Dear {CustomerName} We regret to inform you that your booking with ID {BookingId} has been cancelled.Please feel free to reschedule your pickup.We are always here to assist you."

                headers = {'Content-Type': 'application/json', 'api_key': "c3bbd214b7f7439f60fa36ba"}

                # Based on the environment, API URL will be changed.
                if CURRENT_ENV == 'development':
                    api_url = 'https://apps.fabricspa.com/Mobile_Controller/send_promotional_notification'
                else:
                    api_url = 'https://apps.fabricspa.com/Mobile_Controller/send_promotional_notification'
                    # api_url = 'https://app-staging.fabricspa.com/jfsl/api/generate_payment_link'

                json_request = {"mobile_number": str(MobileNumber), "message": message, "screen": "cancelled_pickup",
                                "image_url": "", 'source': 'Fabxpress'}

                query = f"EXEC CustomerApp.[dbo].[GetBrandName] @BranchCode='{BranchCode}', @EGRNNo=NULL, @PickupRequestId=NULL"
                brand_details = CallSP(query).execute().fetchone()
                log_data = {
                    'query of brand': query, 
                    'result of brand': brand_details,
                    'json_request cancel pickup:': json_request,
                }
                info_logger(f'Route: {request.path}').info(json.dumps(log_data))

                if brand_details["BrandDescription"] == 'FABRICSPA':
                    # Calling the API.
                    response = requests.post(api_url, data=json.dumps(json_request), headers=headers)

        except Exception as e:

            error_logger(f'Route: {request.path}').error(e)

        if result:
            final_data = generate_final_data('DATA_DELETED')
        else:
            final_data = generate_final_data('DATA_DELETE_FAILED')
    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(cancel_form.errors)

    return final_data


@delivery_blueprint.route('/reschedule_pickup', methods=["POST"])
# @authenticate('delivery_user')
def reschedule_pickup():
    """
    API for rescheduling a pickup request.
    """
    reschedule_form = ReschedulePickupForm()

    if reschedule_form.validate_on_submit():
        BookingID = reschedule_form.BookingId.data
        POSId = reschedule_form.POSId.data
        ReschuduleDate = reschedule_form.ReschuduleDate.data
        PickupTimeSlotId = reschedule_form.PickupTimeSlotId.data
        BranchCode = None if reschedule_form.BranchCode.data == '' else reschedule_form.BranchCode.data
        lat = None if reschedule_form.lat.data == '' else reschedule_form.lat.data
        long = None if reschedule_form.long.data == '' else reschedule_form.long.data
        ServiceTatId = reschedule_form.ServiceTatId.data
        TimeSlotFrom = reschedule_form.TimeSlotFrom.data
        TimeSlotTo = reschedule_form.TimeSlotTo.data
        Remarks = reschedule_form.Remarks.data
        CustomerName = reschedule_form.CustomerName.data
        MobileNumber = reschedule_form.MobileNumber.data
        DuserId = request.headers.get('user-id')
        error_msg = ''
        result = False
        try:
            rescheduled_date_obj = datetime.strptime(ReschuduleDate, "%d-%m-%Y")
            # From the date object, convert the date to YYYY-MM-DD format.
            formatted_rescheduled_date = rescheduled_date_obj.strftime("%Y-%m-%d %H:%M:%S")

            query =f"""EXEC  JFSL.Dbo.[SPPickupRescheduleUpdateCustApp] @DuserId = '{DuserId}',@BookingID = '{BookingID}',
            @BranchCode = '{BranchCode}',@PickupTimeSlotId = '{PickupTimeSlotId}',@TimeSlotFrom = '{TimeSlotFrom}',@TimeSlotTo = '{TimeSlotTo}',
            @ReschuduleDate ='{formatted_rescheduled_date}',@ReschuduleReasonID = '{POSId}',@RescheduleRemarks = '{Remarks}',@ISCOB = 1 """
            log_data = {
                    'query ': query,
                   "reschedule_form":reschedule_form.data
                }
            info_logger(f'Route: {request.path}').info(json.dumps(log_data))
            
            db.engine.execute(text(query).execution_options(autocommit=True))
            result = True
            if result:
                message = f" Dear {CustomerName}, your pickup with booking ID {BookingID} is rescheduled to {ReschuduleDate} between {TimeSlotFrom} to {TimeSlotTo}."

                headers = {'Content-Type': 'application/json', 'api_key': "c3bbd214b7f7439f60fa36ba"}

                # Based on the environment, API URL will be changed.
                if CURRENT_ENV == 'development':
                    api_url = 'https://apps.fabricspa.com/Mobile_Controller/send_promotional_notification'
                else:
                    api_url = 'https://apps.fabricspa.com/Mobile_Controller/send_promotional_notification'

                json_request = {"mobile_number": str(MobileNumber), "message": message,
                                "screen": "active_pickup",
                                "image_url": "", 'source': 'Fabxpress'}

                query = f"EXEC CustomerApp.[dbo].[GetBrandName] @BranchCode='{BranchCode}', @EGRNNo=NULL, @PickupRequestId=NULL"
                brand_details = CallSP(query).execute().fetchone()
                log_data = {
                    'query of brand': query,
                    'result of brand': brand_details,
                    'json_request reschedule pickup': json_request
                }
                info_logger(f'Route: {request.path}').info(json.dumps(log_data))
                if brand_details["BrandDescription"] == 'FABRICSPA':
                    log_data = {
                   
                    'response': "response"
                        }
                    info_logger(f'Route: {request.path}').info(json.dumps(log_data))
                    # Calling the API.
                    response = requests.post(api_url, data=json.dumps(json_request), headers=headers)
                   

        except Exception as e:
            error_logger(f'Route: {request.path}').error(e)
        if result:
            final_data = generate_final_data('DATA_UPDATED')
            BranchCode = db.session.execute(
                text(
                    "SELECT BranchCode FROM JFSL.dbo.pickupinfo WHERE BookingID = :BookingID"),
                {"BookingID": BookingID}
            ).fetchone()
            BranchCode = BranchCode[0]
            BranchName = db.session.execute(
                text(
                    "SELECT BranchName FROM JFSL.dbo.Branchinfo WHERE BranchCode = :BranchCode"),
                {"BranchCode": BranchCode}
            ).fetchone()
            BranchName = BranchName[0]
            final_data['BranchName'] = BranchName 
            final_data['BranchCode'] = BranchCode 
        else:
            if error_msg:
                final_data = generate_final_data('CUSTOM_FAILED', error_msg)
            else:
                final_data = generate_final_data('DATA_UPDATE_FAILED')
    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(reschedule_form.errors)
    log_data = {
                   
        'final_data': final_data
                        }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))
    return final_data






@delivery_blueprint.route('/make_delivery', methods=["POST"])
# @authenticate('delivery_user')#after implementing sms triggering
def make_delivery():
    """
    API to mark the order as delivered.
    @return:
    """
    delivery_form = MakeDelivery()
    log_data = {
        'delivery_form': delivery_form.data
    }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))

    if delivery_form.validate_on_submit():
        TRNNo = delivery_form.TRNNo.data
        EGRN = delivery_form.EGRN.data
        DeliveryWithoutOtp = delivery_form.DeliveryWithoutOtp.data
        DeliverWithoutPayment = delivery_form.DeliverWithoutPayment.data
        lat = 0.0 if delivery_form.lat.data == '' else delivery_form.lat.data
        long = 0.0 if delivery_form.long.data == '' else delivery_form.long.data
        Custlat = 0.0 if delivery_form.CustLat.data == '' else delivery_form.CustLat.data
        Custlong = 0.0 if delivery_form.CustLong.data == '' else delivery_form.CustLong.data
        ReasonList = None if delivery_form.ReasonList.data == '' else delivery_form.ReasonList.data
        CustomerName = delivery_form.CustomerName.data
        MobileNumber = delivery_form.MobileNumber.data
        CustomerCode = delivery_form.CustomerCode.data
        BranchCode = delivery_form.BranchCode.data
        BookingId = delivery_form.BookingId.data
        Remarks = delivery_form.Remarks.data
        user_id = request.headers.get('user-id')
        reasons_str = ','.join(ReasonList)
        delivered = False
        error_msg = ''
        already_delivered = None
        proceed_to_delivery = False
        delivery_request = None
        order_details = None
        Status = None
        activity_status = 0
        in_location = ''
        distance = 0
        DuserDistance = 0
        StoreDistance = 0
        distance_dis = 0
        garment_counts = False
        partial_status = None
        trigger_mail = False
        payment_link = ''
        sender = "FABSPA"
        head = "Fabricspa"

        # Checking whether the order is already delivered or not.
        try:
            delivered_status = db.session.execute(
                text(
                    "SELECT PaymentStatus  FROM JFSL.dbo.FabDeliveryInfo (nolock) WHERE TRNNo = :TRNNo AND PaymentStatus =:PaymentStatus AND CompletedBy IS NOT NULL"),
                {"TRNNo": TRNNo, "PaymentStatus": "Paid"}
            ).fetchone()

            print("delivered_status",delivered_status)
            if delivered_status is not None:
                delivered = True
        except Exception as e:
            error_logger(f'Route: {request.path}').error(e)

        if delivered_status is None:
            # Checking whether the order id is present in the delivery request table or not.
            try:
                already_delivered_withoutpayment = db.session.execute(
                    text(
                        "SELECT *  FROM JFSL.dbo.FabDeliveryInfo (nolock) WHERE TRNNo = :TRNNo AND CompletedByName  is not NULL "),
                    {"TRNNo": TRNNo}
                ).fetchone()
               
              

                if already_delivered_withoutpayment is not None :

                    payment_status = payment_module.get_garments_payment_status(EGRN,
                                                                                TRNNo)

                    if payment_status['Status'] == 'Fully Paid':
                        # Amount has been received for this delivery request.
                        Status = 'Paid'
                        activity_status = 2
                        proceed_to_delivery = True

                    if payment_status['Status'] == 'Unpaid':
                        # Amount has been received for this delivery request.
                        Status = 'Un-paid'
                        activity_status = 1
                        proceed_to_delivery = True

                    if payment_status['Status'] == 'Partially paid':
                        # Amount has been received for this delivery request.
                        Status = 'Partial - paid'
                        activity_status = 3
                        proceed_to_delivery = True

                    if proceed_to_delivery:

                        query = f"""EXEC JFSL.DBO.SPFabDeliveryInfoUpdate @TRNNo ='{TRNNo}',@DeliveryDate = '{get_current_date()}',@DUserId = {user_id},@PaymentStatus = '{Status}',@Activity_Status = {activity_status}"""
                        log_data = {
                                'query': query
                                }
                        info_logger(f'Route: {request.path}').info(json.dumps(log_data))
                        db.engine.execute(text(query).execution_options(autocommit=True))
                        delivered = True
                    else:
                        pass
                else:

                    payable_amount = delivery_controller_queries.get_payable_amount_via_sp(CustomerCode,
                                                                                           TRNNo)

                    query = f"EXEC JFSL.[dbo].SPPendingDeliveriesDetailedScreen @user_id = {user_id} ,@TRNNo = '{TRNNo}', @SettledPaymentAmount={1}"

                    result = CallSP(query).execute().fetchone()

                    if result:
                        amount = result.get('FinalAmount')
                    else:
                        amount = 0

                    try:
                        CustomerLocation = (Custlat, Custlong)
                       
                        DeliveryUserLoaction = (lat, long)
                       
                        if CustomerLocation and DeliveryUserLoaction:
                            distance = hs.haversine(CustomerLocation, DeliveryUserLoaction)
                            print(distance)
                            if distance >= 1:
                                if distance >= 10:
                                    trigger_mail = True
                                km_part = int(distance)
                                meters_part = (
                                                          distance - km_part) * 1000
                                DuserDistance = f"{km_part} km {int(meters_part)} m"
                            else:
                                distance_meters = distance * 1000
                                DuserDistance = f"{int(distance_meters)} m"
                            print("DuserDistance", DuserDistance)
                        BranchLocation = db.session.execute(
                            text(
                                "SELECT Lat, Long,BranchName FROM JFSL.dbo.Branchinfo WHERE BranchCode = :BranchCode"),
                            {"BranchCode": BranchCode}
                        ).fetchone()
                        BranchName = BranchLocation.BranchName
                        print("BranchLocation", BranchLocation)
                        BranchLocation = (
                            float(BranchLocation.Lat), float(BranchLocation.Long))
                        if BranchLocation:
                            store_distance = hs.haversine(BranchLocation, DeliveryUserLoaction)
                            if store_distance >= 1:
                                if store_distance >= 10:
                                    trigger_mail = True
                                km_part = int(store_distance)
                                meters_part = (
                                                      store_distance - km_part) * 1000
                                StoreDistance = f"{km_part} km {int(meters_part)} m"
                            else:
                                distance_meters = store_distance * 1000
                                StoreDistance = f"{int(distance_meters)} m"
                            print("StoreDistance", StoreDistance)
                        excluded_branches = {"BRN0001049", "BRN0001160", "SPEC000001", "BRN0001192",
                                             "BRN0001195", "BRN0001196"}
                    except Exception as e:
                        pass
                    if trigger_mail and BranchCode not in excluded_branches:

                        delivery_user_name = db.session.query(DeliveryUser.UserName).filter(
                            DeliveryUser.DUserId == user_id, DeliveryUser.IsActive == 1,
                            DeliveryUser.IsDeleted == 0).scalar()

                        egrn = EGRN
                        current_day = get_current_date()
                        workbook = openpyxl.Workbook()
                        worksheet = workbook.active
                        field_name_mapping = {
                            BranchCode: "Branch Code",
                            BranchName: "Branch Name",
                            "Delivery": "Activity Type",
                            current_day: "Completed Date",
                            BookingId: "Booking Id",
                            CustomerName: "Customer Name",
                            delivery_user_name: "Delivery User Name",
                            DuserDistance: "P-up/Del Location to Customer Distance",
                            StoreDistance: "P-up/Del Location to Store Distance",
                            EGRN: " EGRN"
                        }
                        # print(field_name_mapping)

                        # Columns to include
                        column_names = [BranchCode, BranchName, "Delivery", current_day, BookingId,
                                        CustomerName, delivery_user_name, DuserDistance, StoreDistance, EGRN]

                        # Headers for the Excel file
                        headers = [field_name_mapping.get(col, col) for col in column_names]
                        worksheet.append(headers)

                        # data_row = [branchcode, current_day, booking_id,customer_id,customer_name,delivery_user_name,distance_display,distance_dis,egrn]
                        data_row = [str(BranchCode), BranchName, "Delivery", str(current_day), str(BookingId),
                                    str(CustomerName), str(delivery_user_name), str(StoreDistance),
                                    str(DuserDistance), str(egrn)]
                        worksheet.append(data_row)

                        # Save the file
                        file_name = "report_delivery.xlsx"
                        #file_path = ' C:\\Users\\HP\\fabric\\report_delivery.xlsx'

                        file_path = os.path.join(r"C:\Apache24\htdocs\jfsl\uploads", file_name)

                        # file_path = r"C:\\Apache24\\htdocs\\jfsl\\uploads\\output.xlsx"
                        workbook.save(file_path)
                        # query = f"EXEC JFSL.[dbo].[SendCommanEmailFabXpress] @FilePath='{file_name}', @EmailTo='jfsl.mdm@jyothy.com', @EmailCC='jyothy.support@mapmymarketing.ai;rahul.shettigar@jyothy.com;abhinav.ambasta@jyothy.com', @Subject='Pickup/Delivery Distance more than 10 KM', @Body='Please find the attached report'"

                        # db.engine.execute(text(query).execution_options(autocommit=True))

                    # Edited by MMM
                    # Checking the status of the selected order garments and amount to pay .
                    payment_status = payment_module.get_garments_payment_status(EGRN,
                                                                                TRNNo)
                    if payment_status['Status'] == 'Fully Paid':
                        # Amount has been received for this delivery request.
                        Status = 'Paid'
                        activity_status = 2
                        proceed_to_delivery = True

                    if payment_status['Status'] == 'Unpaid':
                        # Amount has been received for this delivery request.
                        Status = 'Un-paid'
                        activity_status = 1
                        proceed_to_delivery = True

                    if payment_status['Status'] == 'Partially paid':
                        # Amount has been received for this delivery request.
                        Status = 'Partial - paid'
                        activity_status = 3
                        proceed_to_delivery = True

                    if proceed_to_delivery:
                        try:
                            query = f""" EXEC JFSL.[dbo].SPFabDeliveryInfoUpdate 
                                        @DeliveryDate = '{get_current_date()}' ,@DUserId ={user_id}, @DuserLat = {lat},
                                        @DuserLong = {long},@CustLat = {Custlat},@CustLong = {Custlong},@DeliveryWithoutOtp = {DeliveryWithoutOtp},
                                        @PaymentStatus = '{Status}',@Activity_Status = {activity_status},@DeliverWithoutPayment = {DeliverWithoutPayment},@Reasons ='{reasons_str}',
                                       @PayableAmount = {amount}, 
                                        @distance = '{DuserDistance}' ,@store_distance = '{StoreDistance}',@TRNNo = '{TRNNo}'"""
                            log_data = {
                                'query': query
                                }
                            info_logger(f'Route: {request.path}').info(json.dumps(log_data))
                            db.engine.execute(text(query).execution_options(autocommit=True))
                            delivered = True
                            query = f""" EXEC JFSL.Dbo.SPPendingDeliveriesDetailedScreen @user_id = {user_id} ,@TRNNo = '{TRNNo}',@TRNNoBasisGarmentsCounts = {1}"""
                            DeliveryGarmentsCount = CallSP(query).execute().fetchone()
                            GarmentCount = DeliveryGarmentsCount.get('GarmentsCount')
                            message = f" Dear {CustomerName}, payment of Rs.{amount}/- for {GarmentCount}  garment(s) against order number {EGRN} at Fabricspa has been successfully processed. Click to view the invoice copy."
                            # message=f"Hi {customer_name}, payment of Rs.{amount}/- for {delivery_garments_count} garments against order No. {order_details.EGRN} at fabricspa has been successful. Go to MY ORDERS to view your Invoice copy."
                            # message  =f" Dear {customer_name},your order No {order_details.EGRN} for {delivery_garments_count} garments booked on {booking_date} and your estimated order amount would be Rs {amount}/-. You can track your order status in the App. "
                            headers = {'Content-Type': 'application/json',
                                       'api_key': "c3bbd214b7f7439f60fa36ba"}

                            if CURRENT_ENV == 'development':
                                api_url = 'https://apps.fabricspa.com/Mobile_Controller/send_promotional_notification'
                            else:
                                api_url = 'https://apps.fabricspa.com/Mobile_Controller/send_promotional_notification'
                                # api_url = 'https://app-staging.fabricspa.com/jfsl/api/generate_payment_link'

                            json_request = {"mobile_number": str(MobileNumber), "message": message,
                                            "screen": "completed_order", "image_url": "", 'source': 'Fabxpress'}

                            query = f"EXEC CustomerApp.[dbo].[GetBrandName] @BranchCode='{BranchCode}', @EGRNNo=NULL, @PickupRequestId=NULL"
                            brand_details = CallSP(query).execute().fetchone()

                            if brand_details["BrandDescription"] == 'FABRICSPA':
                                if payment_status['Status'] == 'Fully Paid':
                                    # Calling the API.
                                    response = requests.post(api_url, data=json.dumps(json_request),
                                                             headers=headers)

                            if payment_status['Status'] == 'Fully Paid':

                                # Fetch payment details
                                payment_dtls = db.session.query(TransactionInfo).filter(
                                    TransactionInfo.EGRNNo == EGRN,
                                    TransactionInfo.PaymentFrom.in_(['Billdesk', 'Fabricspa'])
                                ).order_by(TransactionInfo.TransactionDate.desc()).first()

                                if payment_dtls:

                                    # Fetch transaction ID and payment ID
                                    transaction_id_result = db.session.query(
                                        TransactionInfo.TransactionId).filter(
                                        TransactionInfo.DCNo == TRNNo
                                    ).order_by(TransactionInfo.TransactionDate.desc()).first()

                                    payment_id_result = db.session.query(TransactionInfo.PaymentId).filter(
                                        TransactionInfo.DCNo == TRNNo
                                    ).order_by(TransactionInfo.TransactionDate.desc()).first()

                                    transaction_id = transaction_id_result[
                                        0] if transaction_id_result else None
                                    payment_id = payment_id_result[0] if payment_id_result else None

                                    if transaction_id is not None and payment_id is not None:
                                        amount = db.session.query(TransactionPaymentInfo.PaymentAmount).filter(
                                            TransactionPaymentInfo.TransactionId == transaction_id).order_by(
                                            TransactionPaymentInfo.CreatedOn.desc()).first()
                                        amount = amount[0]

                                        invoice_num = db.session.query(TransactionPaymentInfo.InvoiceNo).filter(
                                            and_(
                                                TransactionPaymentInfo.TransactionId == transaction_id,
                                                TransactionPaymentInfo.InvoiceNo.isnot(None)
                                            )
                                        ).order_by(TransactionPaymentInfo.CreatedOn.desc()).first()

                                        invoice_num = invoice_num[0]
                                        customer_code = CustomerCode
                                        egrn = EGRN
                                        delivery_controller_queries.send_sms_email_when_settled(
                                            customer_code, egrn,
                                            amount,
                                            invoice_num,TRNNo)
                                else:
                                    pass
                            #if payment_status['Status'] == 'Un-paid':
                            if payment_status['Status'] == 'Unpaid':
                                log_data = {
                                    'delivery_form': 'sms_test'
                                }
                                info_logger(f'Route: {request.path}').info(json.dumps(log_data))

                                amount_dtls = delivery_controller_queries.get_payable_amount_via_sp(
                                    CustomerCode,
                                    TRNNo)
                                amount = amount_dtls['PAYABLEAMOUNT']
                                log_data = {
                                    'amount': amount
                                }
                                info_logger(f'Route: {request.path}').info(json.dumps(log_data))

                                query = f""" EXEC JFSL.Dbo.SPPendingDeliveriesDetailedScreen @user_id = {user_id} ,@TRNNo = '{TRNNo}',@TRNNoBasisGarmentsCounts = {1}"""
                                log_data = {
                                    'test1': 'test1'
                                }
                                info_logger(f'Route: {request.path}').info(json.dumps(log_data))

                                DeliveryGarmentsCount = CallSP(query).execute().fetchone()
                                log_data = {
                                    'query1': query
                                }
                                info_logger(f'Route: {request.path}').info(json.dumps(log_data))

                                query = f"EXEC CustomerApp.[dbo].[GetBrandName] @BranchCode='NULL', @EGRNNo={EGRN}, @PickupRequestId=NULL"
                                brand_details = CallSP(query).execute().fetchone()

                                if brand_details and brand_details["BrandDescription"] != 'FABRICSPA':

                                    RequestBody = {
                                        "TRNNo": TRNNo,
                                        "EGRN": EGRN,
                                        "CustomerCode": CustomerCode,
                                        "DeliveryWithoutOtp":DeliveryWithoutOtp,
                                        "DeliverWithoutPayment": DeliverWithoutPayment,
                                        "COUNT": DeliveryGarmentsCount.get('GarmentsCount'),
                                        "lat ": lat ,
                                        "long":long,
                                        "Custlat": Custlat,
                                        "Custlong":Custlong,
                                        "ReasonList": ReasonList,
                                        "CustomerName":CustomerName,
                                        "CustomerCode":CustomerCode,
                                        "BranchCode": BranchCode,
                                        "Remarks": Remarks,
                                        "UserId": user_id,
                                        "MobileNumber":MobileNumber
                                    }

                                    log_data = {
                                        'RequestBody': RequestBody
                                    }
                                    info_logger(f'Route: {request.path}').info(json.dumps(log_data))

                                    headers = {
                                        'Content-Type': 'application/json',
                                        "user-id": str(user_id)
                                    }

                                    with current_app.test_request_context(
                                            '/delivery/send_payment_link1',
                                            method='POST',
                                            json=RequestBody,
                                            headers=headers
                                    ):
                                        response = send_payment_link1()
                                        response_data = response

                                    log_data = {
                                        'response_data': response_data
                                    }
                                    info_logger(f'Route: {request.path}').info(json.dumps(log_data))

                                    if response_data.get('status') == 'success':
                                            # Link generation is successful.
                                            payment_link = response_data.get('result')

                                            query = f"EXEC {LOCAL_DB}.dbo.DeliveredPaymentPendingSMSTrigger @Amount='{str(amount)}',@Link='{payment_link}',@MobileNo='{str(MobileNumber)}',@EGRNNo='{EGRN}'"
                                            db.engine.execute(text(query).execution_options(autocommit=True))
                                            log_data = {
                                                'sms_query': query
                                            }
                                            info_logger(f'Route: {request.path}').info(json.dumps(log_data))

                                    else:
                                        pass
                                else:
                                    payment_link = 'https://fabspa.in/payments'

                                    query = f"EXEC {LOCAL_DB}.dbo.DeliveredPaymentPendingSMSTrigger @Amount='{str(amount)}',@Link='{payment_link}',@MobileNo='{str(MobileNumber)}',@EGRNNo='{EGRN}'"
                                    db.engine.execute(text(query).execution_options(autocommit=True))
                                    log_data = {
                                        'sms_query1': query
                                    }
                                    info_logger(f'Route: {request.path}').info(json.dumps(log_data))


                            else:
                                pass


                                    
                            

                        except Exception as e:
                            db.session.rollback()
                            error_logger(f'Route: {request.path}').error(e)

            except Exception as e:
                error_logger(f'Route: {request.path}').error(e)

        else:
            # error_msg = 'The order is already delivered.'
            delivered = True

        if delivered:
            final_data = generate_final_data('DATA_SAVED')

            try:
                db.session.execute(text("""
                                            INSERT INTO JFSL.Dbo.FABTravelLogs 
                                            (Activity,  DUserId,    BookingID,  TRNNo,  Lat,    Long,   IsDeleted,  RecordCreatedDate,  RecordLastUpdatedDate) 
            
                                            VALUES (:Activity,  :DUserId,   :BookingID, :TRNNo, :Lat,   :Long,  :IsDeleted, :RecordCreatedDate, :RecordCreatedDate)
                                            """), {
                        "Activity": "Delivery",
                        "DUserId": user_id,
                        "BookingID": BookingId,
                        "TRNNo": TRNNo,
                        "Lat": lat,
                        "Long": long,
                        "Remarks": Remarks,
                        "IsDeleted": 0,
                        "RecordCreatedDate": get_current_date()
                    })
                db.session.commit()
            except Exception as e:
                error_logger(f'Route: {request.path}').error(e)
        else:
            if error_msg:
                final_data = generate_final_data('CUSTOM_FAILED', error_msg)
            else:
                final_data = generate_final_data('DATA_SAVE_FAILED')
    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(delivery_form.errors)
    log_data = {
        'final_data': final_data
    }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))

    return final_data


@delivery_blueprint.route('/check_open_pickups', methods=["POST"])
# @authenticate('delivery_user')
def check_open_pickups():
    """
    API for checking payment status of the given delivery request id.
    @return:
    """
    check_open_pickups_form = CheckOpenPickupsForm()
    if check_open_pickups_form.validate_on_submit():
        CustomerCode = check_open_pickups_form.CustomerCode.data
        PickupDate = check_open_pickups_form.PickupDate.data
        BranchCode = check_open_pickups_form.BranchCode.data
        CustomerName = None if check_open_pickups_form.CustomerName.data == '' else check_open_pickups_form.CustomerName.data
        MobileNumber = None if check_open_pickups_form.MobileNumber.data == '' else check_open_pickups_form.MobileNumber.data

        FormattedPickupDate = datetime.strptime(PickupDate, "%d-%m-%Y")
        FormattedPickupDate = FormattedPickupDate.strftime("%Y-%m-%d %H:%M:%S")
        RescheduleTimeSlotFrom = None
        RescheduleTimeSlotTo = None
        RescheduleTimeSlotID = 0
        BookingID = None
        Message = None
        PickupBranchCode = None
        PickupBranchName = None
        ExistingPickupDate = None


        user_id = request.headers.get('user_id')
        try:
            query = f""" JFSL.DBO.SPPickupInfoInsertValidationCustApp @BranchCode ='{BranchCode}',@CustomerCode ='{CustomerCode}',@PickupDate = '{FormattedPickupDate}'"""
            result = CallSP(query).execute().fetchall()
            log_data = {
            'query': query
                }
            info_logger(f'Route: {request.path}').info(json.dumps(log_data))

            result = result[0]
            BookingID = result.get('BookingID')
            Message = result.get('Message')
            RescheduleTimeSlotFrom = result.get('ExistingTimeSlotFrom')
            RescheduleTimeSlotTo = result.get('ExistingTimeSlotTo')
            RescheduleTimeSlotID = result.get('ExistingTimeSlotID')
            PickupType = result.get('PickupType')
            ExistingPickupDate = result.get('ExistingPickupDate')
            PickupBranchCode = result.get('PickupBranchCode')
            BranchName = db.session.execute(
                    text(
                        "SELECT BranchName FROM JFSL.dbo.Branchinfo WHERE BranchCode = :BranchCode"),
                    {"BranchCode": PickupBranchCode}
                ).scalar()
            if BranchName:
                PickupBranchName = BranchName
            if ExistingPickupDate:
                if isinstance(ExistingPickupDate, str):
                    # Try parsing string into datetime
                    try:
                        ExistingPickupDate = datetime.strptime(ExistingPickupDate, "%Y-%m-%d %H:%M:%S.%f")
                    except ValueError:
                        ExistingPickupDate = datetime.strptime(ExistingPickupDate, "%Y-%m-%d %H:%M:%S")
                # Now it's guaranteed to be datetime
                ExistingPickupDate = ExistingPickupDate.strftime("%d-%m-%Y")
            


        except Exception as e:
            error_logger(f'Route: {request.path}').error(e)

        # final_data = generate_final_data('DATA_FOUND')
        # final_data['result'] = result

        if Message == 'Success':
            final_data = generate_final_data('DATA_AVAILABLE',Message)
            result = {'Message': Message}
            final_data['result'] = result

        else:
            final_data = generate_final_data('DATA_AVAILABLE',Message)
            result = {
                "BookingID":BookingID,
                "Message": Message,
                "RescheduleTimeSlotID": RescheduleTimeSlotID,
                "RescheduleTimeSlotFrom": RescheduleTimeSlotFrom,
                "RescheduleTimeSlotTo": RescheduleTimeSlotTo,
                "ReschedulePickupDate": PickupDate,
                "POSId": 6,
                "CustomerName": CustomerName,
                "MobileNumber": MobileNumber,
                "PickupType":PickupType,
                "PickupBranchName":PickupBranchName,
                "PickupBranchCode":PickupBranchCode,
                "ExistingPickupDate":ExistingPickupDate
            }
            final_data['result'] = result

    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(check_open_pickups_form.errors)
    log_data = {
            'final_data': final_data
                }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))
    return final_data


@delivery_blueprint.route('/create_adhoc_pickup_request', methods=["POST"])
# @authenticate('delivery_user')
def create_adhoc_pickup_request():
    """
    API for creating a pickup request at the time of Ad-hoc pickup.
    @return:
    """

    adhoc_form = CreateAdhocPickupForm()
    if adhoc_form.validate_on_submit():
        CustomerName = '' if adhoc_form.CustomerName.data == '' else adhoc_form.CustomerName.data
        MobileNumber = '' if adhoc_form.MobileNumber.data == '' else adhoc_form.MobileNumber.data
        PickupDate = '' if adhoc_form.PickupDate.data == '' else adhoc_form.PickupDate.data
        BranchCode = '' if adhoc_form.BranchCode.data == '' else adhoc_form.BranchCode.data
        CustomerCode = '' if adhoc_form.CustomerCode.data == '' else adhoc_form.CustomerCode.data
        PickupTimeSlotId = adhoc_form.PickupTimeSlotId.data
        ServiceTatId = adhoc_form.ServiceTatId.data
        TimeSlotFrom = '' if adhoc_form.TimeSlotFrom.data == '' else adhoc_form.TimeSlotFrom.data
        TimeSlotTo = '' if adhoc_form.TimeSlotTo.data == '' else adhoc_form.TimeSlotTo.data
        Adhoccoupon = '' if adhoc_form.Adhoccoupon.data == '' else adhoc_form.Adhoccoupon.data
        AddressLine1 = '' if adhoc_form.AddressLine1.data == '' else clean_address_field(adhoc_form.AddressLine1.data)
        AddressLine2 = '' if adhoc_form.AddressLine2.data == '' else clean_address_field(adhoc_form.AddressLine2.data)
        AddressLine3 = '' if adhoc_form.AddressLine3.data == '' else clean_address_field(adhoc_form.AddressLine3.data)
        AddressName = '' if adhoc_form.AddressName.data == '' else clean_address_field(adhoc_form.AddressName.data)
        Lattitude = '' if adhoc_form.Lattitude.data == '' else adhoc_form.Lattitude.data
        Longitude = '' if adhoc_form.Longitude.data == '' else adhoc_form.Longitude.data
        GeoLocation = '' if adhoc_form.GeoLocation.data == '' else adhoc_form.GeoLocation.data
        PinCode = 0 if adhoc_form.PinCode.data == '' else adhoc_form.PinCode.data

        DiscountCode = '' if adhoc_form.DiscountCode.data in ('', 'NA') else adhoc_form.DiscountCode.data
        AddressType = '' if adhoc_form.AddressType.data == '' else adhoc_form.AddressType.data

        ValidateDiscountCode = '' if adhoc_form.ValidateDiscountCode.data in ('', 'NA') else adhoc_form.ValidateDiscountCode.data
        service_type_id = 2 if adhoc_form.service_type_id.data == '' else adhoc_form.service_type_id.data
        DUserID = request.headers.get('user-id')
        DUserID = int(DUserID)
        log_data = {
                    'adhoc_form ': adhoc_form.data,
                   
                }
        info_logger(f'Route: {request.path}').info(json.dumps(log_data))

        PickupSource = 'Adhoc'
        DeliveryFlat = ''
        DeliveryAddress = ''
        PermanentFlat = ''
        PermanantAddress = ''
        LattitudePer = ''
        LongitudePer = ''
        BookingID = None
        Message = None
        Created = False
        RescheduleTimeSlotFrom = None
        RescheduleTimeSlotTo = None
        RescheduleTimeSlotID = 0
        ExistingPickupDate = None

        pickup_date_obj = datetime.strptime(PickupDate, "%d-%m-%Y")
        # From the date object, convert the date to YYYY-MM-DD format.
        formatted_pickup_date = pickup_date_obj.strftime("%Y-%m-%d %H:%M:%S")
        if AddressType == 'delivery':
            DeliveryFlat = AddressLine1
            DeliveryAddress = AddressLine2
            PermanantPinCode = 0

        else:
            PermanentFlat = AddressLine1
            PermanantAddress = AddressLine2
            LattitudePer = Lattitude
            LongitudePer = Longitude
            PermanantPinCode = PinCode
            PinCode = 0
        try:
            query = f""" EXEC JFSL.Dbo.SPPickupInfoInsertValidationCustApp @BranchCode ='{BranchCode}',@CustomerCode ='{CustomerCode}',@PickupDate = '{formatted_pickup_date}'"""
            result = CallSP(query).execute().fetchall()
            log_data = {
                    'query ': query,
                    'result': result
                }
            info_logger(f'Route: {request.path}').info(json.dumps(log_data))
            result = result[0]
            BookingID = result.get('BookingID')
            Message = result.get('Message')
            RescheduleTimeSlotFrom = result.get('ExistingTimeSlotFrom')
            RescheduleTimeSlotTo = result.get('ExistingTimeSlotTo')
            RescheduleTimeSlotID = result.get('ExistingTimeSlotID')
            RescheduledServiceTypeId = result.get('RescheduledServiceTypeId')
            ExistingPickupDate = result.get('ExistingPickupDate')
            if ExistingPickupDate:
                ExistingPickupDate = datetime.strptime(ExistingPickupDate, "%Y-%m-%d %H:%M:%S.%f")
                ExistingPickupDate = ExistingPickupDate.strftime("%d-%m-%Y")
           

            if result.get("Message") == "Success":
                query = f""" EXEC JFSL.Dbo.SPFabERCoupanCodeValidation @ActualDiscCode ='{DiscountCode}'"""
                result = CallSP(query).execute().fetchone()
                if result.get('Message') == 'Success':
                    CodeFromER = DiscountCode
                    IsERCoupon = 1
                    ERRequestId = 1
                    
                else:
                    CodeFromER = ''
                    IsERCoupon = 0
                    ERRequestId = 0
               
                unicode = uuid.uuid4()
                query = f"""

                        EXEC JFSL.Dbo.SPPickupInfoInsertCustApp
                            @GUID_Value = '{unicode}',
                            @DUserID = '{DUserID}',
                            @BranchCode = '{BranchCode}',
                            @CustomerCode = '{CustomerCode}',
                            @DeliveryFlat = '{DeliveryFlat}',
                            @PermanentFlat = '{PermanentFlat}',
                            @DeliveryAddress = '{DeliveryAddress}',
                            @PermanantAddress = '{PermanantAddress}',
                            @Lattitude = '{Lattitude}',
                            @LattitudePer = '{LattitudePer}',
                            @Longitude = '{Longitude}',
                            @LongitudePer = '{LongitudePer}',
                            @PinCode = '{PinCode}',
                            @PermanantPinCode = '{PermanantPinCode}',
                            @PickupTimeSlotId = '{PickupTimeSlotId}',
                            @PickupDate = '{formatted_pickup_date}',
                            @PickupSource = '{PickupSource}',
                            @TimeSlotFrom = '{TimeSlotFrom}',
                            @TimeSlotTo = '{TimeSlotTo}',
                            @ServiceTatId = {ServiceTatId},
                            @ValidateCouponCode = {'null'},
                            @ValidateDiscountCode = '{ValidateDiscountCode}',
                            @CodeFromER = '{CodeFromER}',
                            @ISERCoupon = {IsERCoupon},
                            @ERRequestID ={ERRequestId},
                            @GeoLocation = '{GeoLocation}',
                            @washtype = {service_type_id}
                           
                """
                log_data = {
                    'query ': query,
                    
                }
                info_logger(f'Route: {request.path}').info(json.dumps(log_data))
                db.engine.execute(text(query).execution_options(autocommit=True))
                Created = True
                print(Created)
                BookingID = db.session.execute(
                    text(
                        "SELECT BookingID  FROM JFSL.dbo.PickupInfo (nolock) WHERE PickupID = :unicode"),
                    {"unicode": unicode}
                ).fetchone()
                BookingID = BookingID[0]
                print(BookingID)
            if formatted_pickup_date != get_today and BookingID and Created:

                message = f"Dear {CustomerName} your pickup at fabricspa has been confirmed with booking ID {BookingID} and it is scheduled for {PickupDate} between {TimeSlotFrom} to {TimeSlotTo}."

                headers = {'Content-Type': 'application/json',
                           'api_key': "c3bbd214b7f7439f60fa36ba"}

                # Based on the environment, API URL will be changed.
                if CURRENT_ENV == 'development':

                    api_url = 'https://apps.fabricspa.com/Mobile_Controller/send_promotional_notification'
                else:
                    api_url = 'https://apps.fabricspa.com/Mobile_Controller/send_promotional_notification'
                json_request = {"mobile_number": str(MobileNumber), "message": message,
                                "screen": "active_pickup",
                                "image_url": "", 'source': 'Fabxpress'}

                query = f"EXEC CustomerApp.[dbo].[GetBrandName] @BranchCode='{BranchCode}', @EGRNNo=NULL, @PickupRequestId=NULL"
                brand_details = CallSP(query).execute().fetchone()
                log_data = {
                    'query of brand': query,
                    'json_request':json_request,
                    'result of brand': brand_details
                }
                info_logger(f'Route: {request.path}').info(json.dumps(log_data))
                print(query)

                if brand_details["BrandDescription"] == 'FABRICSPA':
                    response = requests.post(api_url, data=json.dumps(json_request),
                                             headers=headers)
            pickup_date_only = pickup_date_obj.date()
            today = datetime.today().date()
            if BookingID and Created and pickup_date_only != today:

                formatted_date_time_slot = f"{PickupDate} {TimeSlotFrom} to {TimeSlotTo} "
                # function for sending SMS by Calling SP
                delivery_controller_queries.trigger_sms_after_pickup(
                    'JFSL_GARMENT_PICKUP_FABRICSPA', MobileNumber, CustomerName,
                    BookingID, formatted_date_time_slot)

                query = f"EXEC {SERVER_DB}.dbo.GetWhatsappOptinDetails @customercode='{CustomerCode}'"
                whatsapp_opt_or_not = CallSP(query).execute().fetchall()
                log_data = {
                    'whatsapp_opt_or_not :': query
                }
                info_logger(f'Route: {request.path}').info(json.dumps(log_data))
                if whatsapp_opt_or_not["WhatsAppOptin"] == 'YES':
                    # function for sending whats app message by Calling SP
                    delivery_controller_queries.trigger_sms_after_pickup(
                        'pickup_scheduled', MobileNumber, CustomerName,
                        BookingID, formatted_date_time_slot)
                else:
                    # function for sending SMS by Calling SP
                    delivery_controller_queries.trigger_sms_after_pickup(
                        'JFSL_GARMENT_PICKUP_FABRICSPA', MobileNumber, CustomerName,
                        BookingID, formatted_date_time_slot)

        except Exception as e:
            error_logger(f'Route: {request.path}').error(e)

        if BookingID and Created:
            final_data = generate_final_data('DATA_SAVED')
            result = {'BookingID': BookingID,'BookingId': BookingID }
            final_data['result'] = result

        else:
            final_data = generate_final_data('CUSTOM_FAILED',Message)
            result = {
                'BookingID': BookingID,
                'BookingId': BookingID,
                "Message": Message,
                "RescheduleTimeSlotID": RescheduleTimeSlotID,
                "RescheduleTimeSlotFrom": RescheduleTimeSlotFrom,
                "RescheduleTimeSlotTo": RescheduleTimeSlotTo,
                "ReschedulePickupDate": PickupDate,
                "CustomerName": CustomerName,
                "MobileNumber": MobileNumber,
                "POSId": 6,
                "RescheduledServiceTypeId":RescheduledServiceTypeId,
                "ExistingPickupDate":ExistingPickupDate
            }
            final_data['result'] = result

    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(adhoc_form.errors)
    log_data = {
        'final_data ': final_data,
                
                }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))

    return final_data


# @delivery_blueprint.route('/future_date_rewash', methods=["POST"])
# @authenticate('delivery_user')
# def future_date_rewash():
#     future_date_rewash_form = FutureDateRewashForm()
#     if future_date_rewash_form.validate_on_submit():
#         mobile_number = future_date_rewash_form.mobile_number.data
#         address_id = future_date_rewash_form.address_id.data
#         rewash_date = future_date_rewash_form.rewash_date.data
#         branch_code = future_date_rewash_form.branch_code.data
#         time_slot_id = future_date_rewash_form.time_slot_id.data
#         rewash_date_obj = datetime.strptime(rewash_date, "%d-%m-%Y")
#         # From the date object, convert the date to YYYY-MM-DD format.
#         formated_rewash_date = rewash_date_obj.strftime("%Y-%m-%d %H:%M:%S")
#         result = False
#         user_id = request.headers.get('user-id')
#         error_msg = ''
#         existing_pickup_request_details = {}
#         same_date = False
#         log_data = {
#             'json_request rewash:': 'test',

#         }
#         info_logger(f'Route: {request.path}').info(json.dumps(log_data))

#         try:
#             # Getting the customer details from the DB.
#             customer_details = db.session.query(Customer.CustomerId, Customer.CustomerCode, Customer.BranchCode).filter(
#                 or_(Customer.MobileNo == mobile_number, Customer.AlternateNo == mobile_number),
#                 Customer.IsDeleted == 0).one_or_none()
#             if customer_details is not None:
#                 ameyo_customer_id = ameyo_module.get_ameyo_customer_id(mobile_number)
#                 if ameyo_customer_id:
#                     address_details = db.session.query(CustomerAddres.CustAddressId).filter(
#                         CustomerAddres.CustomerId == customer_details.CustomerId,
#                         CustomerAddres.CustAddressId == address_id).one_or_none()
#                     if address_details is not None:
#                         open_pickups = common_module.check_rewash_open_pickups(address_id,
#                                                                                customer_details.CustomerId)

#                         if not open_pickups['status']:
#                             if formated_rewash_date != get_today():

#                                 holiday = delivery_controller_queries.check_branch_holiday(rewash_date,
#                                                                                            branch_code)
#                                 if not holiday:
#                                     # The pickup date is not a branch holiday.
#                                     # Getting the time slot details from PickupTimeSlots

#                                     time_slot = db.session.query(PickupTimeSlot.PickupTimeSlotId,
#                                                                  PickupTimeSlot.TimeSlotFrom,
#                                                                  PickupTimeSlot.TimeSlotTo).filter(
#                                         PickupTimeSlot.BranchCode == branch_code,
#                                         PickupTimeSlot.PickupTimeSlotId == time_slot_id,
#                                         PickupTimeSlot.VisibilityFlag == 1,
#                                         PickupTimeSlot.IsActive == 1
#                                     ).first()
#                                     # time_slot = db.session.query(FabPickupTimeSlots.PickupTimeSlotId,
#                                     #                          FabPickupTimeSlots.TimeSlotFrom,
#                                     #                          FabPickupTimeSlots.TimeSlotTo).filter(
#                                     # FabPickupTimeSlots.PickupTimeSlotId == pickup_time_slot_id,
#                                     # FabPickupTimeSlots.IsActive == 1, FabPickupTimeSlots.IsDeleted == 0
#                                     # ).first()

#                                     if time_slot is None:
#                                         # No time slot present, so try with DefaultFlag.
#                                         time_slot = db.session.query(PickupTimeSlot.PickupTimeSlotId,
#                                                                      PickupTimeSlot.TimeSlotFrom,
#                                                                      PickupTimeSlot.TimeSlotTo).filter(
#                                             PickupTimeSlot.BranchCode == branch_code,
#                                             PickupTimeSlot.DefaultFlag == 1,
#                                             PickupTimeSlot.IsActive == 1
#                                         ).first()
#                                     if time_slot:
#                                         # Now creating a pickup request.
#                                         # Setting up the related variables.
#                                         customer_id = customer_details.CustomerId

#                                         time_slot_id = time_slot.PickupTimeSlotId
#                                         time_slot_from = time_slot.TimeSlotFrom
#                                         time_slot_to = time_slot.TimeSlotTo
#                                         address_id = address_details.CustAddressId
#                                         # Here, the pickup source will be 'Adhoc'.
#                                         pickup_source = 'Rewash'
#                                         status_id = 1
#                                         try:
#                                             # Setting up the new PickupRequest object.
#                                             # if formated_rewash_date != get_today():
#                                             new_pickup_request = PickupRequest(
#                                                 CustomerId=customer_id,
#                                                 PickupDate=formated_rewash_date,
#                                                 BranchCode=branch_code,
#                                                 PickupTimeSlotId=time_slot_id,
#                                                 TimeSlotFrom=time_slot_from,
#                                                 TimeSlotTo=time_slot_to,
#                                                 CustAddressId=address_id,
#                                                 PickupSource=pickup_source,
#                                                 PickupStatusId=status_id,
#                                                 DUserId=user_id,
#                                                 RecordCreatedDate=get_current_date(),
#                                                 RecordLastUpdatedDate=get_current_date(),

#                                             )

#                                             # Saving the new pickup request.
#                                             db.session.add(new_pickup_request)
#                                             db.session.commit()
#                                             new_pickup_request_id = new_pickup_request.PickupRequestId
#                                             pickup_details = db.session.query(PickupRequest.BookingId,
#                                                                               PickupRequest.CustomerId).filter(
#                                                 PickupRequest.PickupRequestId == new_pickup_request_id).one_or_none()

#                                             # Getting Booking id from  PickupRequest table
#                                             # booking_id = db.session.query(PickupRequest.BookingId
#                                             #                                  ).filter(
#                                             #     PickupRequest.PickupRequestId == new_pickup_request_id).first()
#                                             # booking_id = pickup_details.BookingId

#                                             # log_data = {
#                                             #     'bookingids :': pickup_details
#                                             # }
#                                             # info_logger(f'Route: {request.path}').info(json.dumps(log_data))

#                                             # if booking_id:
#                                             #     booking_id = booking_id[0]






#                                         except Exception as e:
#                                             error_logger(f'Route: {request.path}').error(e)
#                                         # if formated_rewash_date != get_today():
#                                         # Generating the BookingId in realtime.
#                                         query = f"EXEC {LOCAL_DB}.dbo.[USP_INSERT_ADHOC_PICKUP_FROM_MOBILEAPP_TO_FABRICARE] @PickUprequestId={new_pickup_request.PickupRequestId}"
#                                         db.engine.execute(text(query).execution_options(autocommit=True))
#                                         result = True
#                                         log_data = {
#                                             'reschedule pickup': query
#                                         }
#                                         info_logger(f'Route: {request.path}').info(json.dumps(log_data))
#                                         new_pickup_request_id = new_pickup_request.PickupRequestId
#                                         booking_id = db.session.query(PickupRequest.BookingId
#                                                                       ).filter(
#                                             PickupRequest.PickupRequestId == new_pickup_request_id).first()
#                                         booking_id = booking_id
#                                         if booking_id:
#                                             booking_id = booking_id[0]

#                                         log_data = {
#                                             'bookingids :': booking_id
#                                         }
#                                         info_logger(f'Route: {request.path}').info(json.dumps(log_data))
#                                         customer_name = db.session.query(Customer.CustomerName).filter(
#                                             Customer.CustomerId == customer_id).first()
#                                         if customer_name:
#                                             customer_name = customer_name[0]

#                                         formated_date = formated_rewash_date

#                                         formatted_rescheduled_date = datetime.strptime(formated_date,
#                                                                                        "%Y-%m-%d %H:%M:%S")

#                                         date = formatted_rescheduled_date.strftime("%d-%m-%Y")

#                                         timeslot_from = time_slot_from

#                                         timeslotfrom = timeslot_from.strftime("%H:%M:%S")

#                                         timeslot_from = datetime.strptime(timeslotfrom, "%H:%M:%S")
#                                         timeslot_from = timeslot_from.strftime("%I:%M %p")

#                                         timeslot_to = time_slot_to
#                                         timeslot_to = timeslot_to.strftime("%H:%M:%S")
#                                         timeslotto = datetime.strptime(timeslot_to, "%H:%M:%S")
#                                         timeslot_to = timeslotto.strftime("%I:%M %p")
#                                         message = f"Dear {customer_name} your pickup at fabricspa has been confirmed with booking ID {booking_id} and it is scheduled for {date} between {timeslot_from} to {timeslot_to}."
#                                         # message = f"Hi {customer_name}, you have scheduled a pickup on {formatted_pickup_date} {time_slot_from} to {time_slot_to} and your booking ID is {pickup_details.BookingId}. For any changes go to MY ORDERS and follow the steps."

#                                         headers = {'Content-Type': 'application/json',
#                                                    'api_key': "c3bbd214b7f7439f60fa36ba"}

#                                         # Based on the environment, API URL will be changed.
#                                         if CURRENT_ENV == 'development':
#                                             api_url = 'https://apps.fabricspa.com/Mobile_Controller/send_promotional_notification'
#                                         else:
#                                             api_url = 'https://apps.fabricspa.com/Mobile_Controller/send_promotional_notification'
#                                             # api_url = 'https://app-staging.fabricspa.com/jfsl/api/generate_payment_link'

#                                         json_request = {"mobile_number": str(mobile_number), "message": message,
#                                                         "screen": "active_pickup",
#                                                         "image_url": "",'source': 'Fabxpress'}
#                                         query = f"EXEC CustomerApp.[dbo].[GetBrandName] @BranchCode='{branch_code}', @EGRNNo=NULL, @PickupRequestId=NULL"
#                                         brand_details = CallSP(query).execute().fetchone()
#                                         log_data = {
#                                                     'query of brand': query,
#                                                     'result of brand': brand_details,
#                                                     'json_request rewash:': json_request,
#                                                 }
#                                         info_logger(f'Route: {request.path}').info(json.dumps(log_data))
#                                         if brand_details["BrandDescription"] == 'FABRICSPA':

#                                             # Calling the API.
#                                             if formated_rewash_date != get_today():
#                                                 response = requests.post(api_url, data=json.dumps(json_request),
#                                                                          headers=headers)
                                           



#                                 else:
#                                     error_msg = 'Please choose another date. This is a branch holiday.'
#                             else:
#                                 same_date = True
#                         else:
#                             # The existing pickup is needed to be rescheduled to the given date.
#                             # Irrespective of the assigned delivery user.
#                             # Here, the current delivery user can reschedule the pickup even if the existing open
#                             # pickup is assigned to somebody else. Return the pickup request id based on BookingId.
#                             # If the pickup is rescheduled, then select RescheduledDate, else select PickupDate.
#                             select_activity_date = case(
#                                 [(PickupReschedule.RescheduledDate == None, PickupRequest.PickupDate), ],
#                                 else_=PickupReschedule.RescheduledDate).label("ActivityDate")

#                             select_pickup_address = case(
#                                 [(PickupReschedule.CustAddressId == None, PickupRequest.CustAddressId), ],
#                                 else_=PickupReschedule.CustAddressId).label("CustAddressId")

#                             pickup_request_details = db.session.query(PickupRequest.PickupRequestId,
#                                                                       PickupRequest.PickupTimeSlotId,
#                                                                       select_activity_date,
#                                                                       select_pickup_address).outerjoin(PickupReschedule,
#                                                                                                        PickupRequest.PickupRequestId == PickupReschedule.PickupRequestId).filter(
#                                 PickupRequest.PickupRequestId == open_pickups['pickup_request_id'],
#                                 or_(PickupReschedule.IsDeleted == 0, PickupReschedule.IsDeleted == None)).one_or_none()

#                             if pickup_request_details is not None:
#                                 # Existing pickup request's details found.
#                                 prevent_schedule = False
#                                 if pickup_request_details.ActivityDate.strftime(
#                                         "%Y-%m-%d %H:%M:%S") == formated_rewash_date:
#                                     if pickup_request_details.CustAddressId == address_id:
#                                         # Trying to create an adhoc pickup for the same day as open pickup date and
#                                         # for the same address. This is not possible.
#                                         prevent_schedule = True

#                                 if not prevent_schedule:
#                                     # The new adhoc pickup is NOT scheduled for the same as existing pickup
#                                     # for the same address.
#                                     reschedule_reason = db.session.query(PickupRescheduleReason).filter(
#                                         PickupRescheduleReason.RescheduleReason == 'Customer Postponed',
#                                         PickupRescheduleReason.IsDeleted == 0).one_or_none()
#                                     if reschedule_reason is not None:
#                                         # Found the reason id for postponing.
#                                         reschedule_reason_id = reschedule_reason.RescheduleReasonId
#                                         # Generating the dict that needs to be returned in the result.
#                                         existing_pickup_request_details = {
#                                             'PickupRequestId': pickup_request_details.PickupRequestId,
#                                             'PickupTimeSlotId': pickup_request_details.PickupTimeSlotId,
#                                             'RescheduleReasonId': reschedule_reason_id
#                                         }
#                                     else:
#                                         error_msg = 'Failed to get the reschedule reason.'
#                                 else:
#                                     error_msg = 'The customer has an open pickup for the same day and for the same ' \
#                                                 'address. '
#                                     existing_pickup_request_details = {
#                                         'PickupRequestId': pickup_request_details.PickupRequestId,
#                                         'PickupTimeSlotId': pickup_request_details.PickupTimeSlotId,
#                                         'PickupDate': pickup_request_details.ActivityDate.strftime("%d-%m-%Y")
#                                     }

#                             else:
#                                 error_msg = 'No existing pickup request details are found in the system.'

#                         if error_msg == '':
#                             error_msg = 'Sorry, this customer has an existing pickup. Action can not be performed.'
#                         # else:
#                         #     error_msg = 'The customer has an open rewash pickup for the same day and for the same ' \
#                         #                 'address'
#                     else:
#                         error_msg = 'Customer address are not available.'

#                 else:
#                     error_msg = 'Ameyo customer id not found'
#             else:
#                 error_msg = 'customer not found'

#         except Exception as e:
#             error_logger(f'Route: {request.path}').error(e)
#         if result:
#             final_data = generate_final_data('DATA_SAVED')
#             result = {'PickupRequestId': new_pickup_request_id}
#             final_data['result'] = result

#         else:
#             if same_date:
#                 final_data = generate_final_data('DATA_SAVED')
#             elif error_msg:
#                 final_data = generate_final_data('CUSTOM_FAILED', error_msg)
#                 if existing_pickup_request_details:
#                     final_data['result'] = existing_pickup_request_details
#             else:
#                 final_data = generate_final_data('DATA_SAVE_FAILED')

#     else:
#         # Form validation error.
#         final_data = generate_final_data('FORM_ERROR')
#         final_data['errors'] = populate_errors(future_date_rewash_form.errors)
#     return final_data

@delivery_blueprint.route('/future_date_rewash', methods=["POST"])
# @authenticate('delivery_user')
def future_date_rewash():
    future_date_rewash_form = FutureDateRewashForm()
    if future_date_rewash_form.validate_on_submit():
        log_data = {
            'future_date_rewash_form ': future_date_rewash_form.data,
                       
                    }
        info_logger(f'Route: {request.path}').info(json.dumps(log_data))
        CustomerName = '' if future_date_rewash_form.CustomerName.data == '' else future_date_rewash_form.CustomerName.data
        MobileNumber = '' if future_date_rewash_form.MobileNumber.data == '' else future_date_rewash_form.MobileNumber.data
        RewashDate = '' if future_date_rewash_form.PickupDate.data == '' else future_date_rewash_form.PickupDate.data
        BranchCode = '' if future_date_rewash_form.BranchCode.data == '' else future_date_rewash_form.BranchCode.data
        CustomerCode = '' if future_date_rewash_form.CustomerCode.data == '' else future_date_rewash_form.CustomerCode.data
        PickupTimeSlotId = future_date_rewash_form.PickupTimeSlotId.data
        TimeSlotFrom = '' if future_date_rewash_form.TimeSlotFrom.data == '' else future_date_rewash_form.TimeSlotFrom.data
        TimeSlotTo = '' if future_date_rewash_form.TimeSlotTo.data == '' else future_date_rewash_form.TimeSlotTo.data
        AddressLine1 = '' if future_date_rewash_form.AddressLine1.data == '' else future_date_rewash_form.AddressLine1.data
        AddressLine2 = '' if future_date_rewash_form.AddressLine2.data == '' else future_date_rewash_form.AddressLine2.data
        AddressLine3 = '' if future_date_rewash_form.AddressLine3.data == '' else future_date_rewash_form.AddressLine3.data
        AddressName = '' if future_date_rewash_form.AddressName.data == '' else future_date_rewash_form.AddressName.data
        Lattitude = 0.0 if future_date_rewash_form.Lattitude.data == '' else future_date_rewash_form.Lattitude.data
        Longitude = 0.0 if future_date_rewash_form.Longitude.data == '' else future_date_rewash_form.Longitude.data
        GeoLocation = '' if future_date_rewash_form.GeoLocation.data == '' else future_date_rewash_form.GeoLocation.data
        PinCode = 0 if future_date_rewash_form.PinCode.data == '' else future_date_rewash_form.PinCode.data
        AddressType = '' if future_date_rewash_form.AddressType.data == '' else future_date_rewash_form.AddressType.data
        DUserID = request.headers.get('user-id')
        rewash_date_obj = datetime.strptime(RewashDate, "%d-%m-%Y")
        # From the date object, convert the date to YYYY-MM-DD format.
        formated_rewash_date = rewash_date_obj.strftime("%Y-%m-%d %H:%M:%S")
        DeliveryFlat = ''
        DeliveryAddress = ''
        PermanentFlat = ''
        PermanantAddress = ''
        LattitudePer = 0.0
        LongitudePer = 0.0
        BookingID = None
        Message = None
        Created = False
        RescheduleTimeSlotFrom = ''
        RescheduleTimeSlotTo = ''
        RescheduleTimeSlotID = 0
        RescheduledServiceTypeId = 0
        result = False
        error_msg = ''

        if AddressType == 'delivery':
            DeliveryFlat = AddressLine1
            DeliveryAddress = AddressLine2
            PermanantPinCode = 0

        else:
            PermanentFlat = AddressLine1
            PermanantAddress = AddressLine2
            LattitudePer = Lattitude
            LongitudePer = Longitude
            PermanantPinCode = PinCode
            PinCode = 0
        try:
            ameyo_customer_id = ameyo_module.get_ameyo_customer_id(MobileNumber)
       
            if ameyo_customer_id is not None:
                query = f""" JFSL.DBO.SPPickupInfoInsertValidationCustApp @BranchCode ='{BranchCode}',@CustomerCode ='{CustomerCode}',@PickupDate = '{formated_rewash_date}' """
                result = CallSP(query).execute().fetchall()
                result = result[0]
                log_data = {
                        'query ': query,
                       
                    }
                info_logger(f'Route: {request.path}').info(json.dumps(log_data))
                BookingID = result.get('BookingID')
                Message = result.get('Message')
                RescheduleTimeSlotFrom = result.get('ExistingTimeSlotFrom')
                RescheduleTimeSlotTo = result.get('ExistingTimeSlotTo')
                RescheduleTimeSlotID = result.get('ExistingTimeSlotID')
                RescheduledServiceTypeId = result.get('RescheduledServiceTypeId')
                print(result)

                if result.get("Message") == "Success":
                    print("result")
                    unicode = uuid.uuid4()
                   
                    query = f"""
                            EXEC JFSL.Dbo.SPPickupInfoInsertCustApp
                            @GUID_Value = '{unicode}',
                            @DUserID = {DUserID},
                            @BranchCode = '{BranchCode}',
                            @CustomerCode = '{CustomerCode}',
                            @DeliveryFlat = '{DeliveryFlat}',
                            @PermanentFlat = '{PermanentFlat}',
                            @DeliveryAddress = '{DeliveryAddress}',
                            @PermanantAddress = '{PermanantAddress}',
                            @Lattitude = '{Lattitude}',
                            @LattitudePer = '{LattitudePer}',
                            @Longitude = '{Longitude}',
                            @LongitudePer = '{LongitudePer}',
                            @PinCode = {PinCode},
                            @PermanantPinCode = '{PermanantPinCode}',
                            @PickupTimeSlotId = '{PickupTimeSlotId}',
                            @PickupDate = '{formated_rewash_date}',
                            @PickupSource = {'Rewash'},
                            @TimeSlotFrom = '{TimeSlotFrom}',
                            @TimeSlotTo = '{TimeSlotTo}',
                            @ServiceTatId = {"null"},
                            @ValidateCouponCode = {"null"},
                            @ValidateDiscountCode = {"null"},
                            @CodeFromER = {'null'},
                            @ISERCoupon = {"null"},
                            @ERRequestID ={"null"},
                            @GeoLocation = '{GeoLocation}'
                    """
                    log_data = {
                        'query ': query,
                       
                    }
                    info_logger(f'Route: {request.path}').info(json.dumps(log_data))

                    db.engine.execute(text(query).execution_options(autocommit=True))
                    Created = True

                    BookingID = db.session.execute(
                        text(
                            "SELECT BookingID  FROM JFSL.dbo.PickupInfo (nolock) WHERE PickupID = :unicode"),
                        {"unicode": unicode}
                    ).fetchone()
                    BookingID = BookingID[0]
                    print(BookingID)


                    message = f"Dear {CustomerName} your pickup at fabricspa has been confirmed with booking ID {BookingID} and it is scheduled for {RewashDate} between {TimeSlotFrom} to {TimeSlotTo}."
                    # message = f"Hi {customer_name}, you have scheduled a pickup on {formatted_pickup_date} {time_slot_from} to {time_slot_to} and your booking ID is {pickup_details.BookingId}. For any changes go to MY ORDERS and follow the steps."

                    headers = {'Content-Type': 'application/json',
                               'api_key': "c3bbd214b7f7439f60fa36ba"}

                    # Based on the environment, API URL will be changed.
                    if CURRENT_ENV == 'development':
                        api_url = 'https://apps.fabricspa.com/Mobile_Controller/send_promotional_notification'
                    else:
                        api_url = 'https://apps.fabricspa.com/Mobile_Controller/send_promotional_notification'
                        # api_url = 'https://app-staging.fabricspa.com/jfsl/api/generate_payment_link'

                    json_request = {"mobile_number": str(MobileNumber), "message": message,
                                    "screen": "active_pickup",
                                    "image_url": "", 'source': 'Fabxpress'}
                    query = f"EXEC CustomerApp.[dbo].[GetBrandName] @BranchCode='{BranchCode}', @EGRNNo=NULL, @PickupRequestId=NULL"
                    brand_details = CallSP(query).execute().fetchone()
                    log_data = {
                        'query of brand': query,
                        'result of brand': brand_details,
                        'json_request rewash:': json_request,
                    }
                    info_logger(f'Route: {request.path}').info(json.dumps(log_data))
                    if brand_details["BrandDescription"] == 'FABRICSPA':

                        # Calling the API.
                        if formated_rewash_date != get_today():
                            response = requests.post(api_url, data=json.dumps(json_request),
                                                     headers=headers)

            else:
                Message ='Ameyo customer id not found'


        except Exception as e:
            error_logger(f'Route: {request.path}').error(e)
        if BookingID and Created:
            final_data = generate_final_data('DATA_SAVED')
            result = {'BookingID': BookingID ,"CustomerCode": CustomerCode}
            final_data['result'] = result

        else:
            log_data = {
                        'Message': Message,
                        
                    }
            info_logger(f'Route: {request.path}').info(json.dumps(log_data))
            final_data = generate_final_data('CUSTOM_FAILED', Message)
            result = {
                'BookingID': BookingID,
                "Message": Message,
                "RescheduleTimeSlotID": RescheduleTimeSlotID,
                "RescheduleTimeSlotFrom": RescheduleTimeSlotFrom,
                "RescheduleTimeSlotTo": RescheduleTimeSlotTo,
                "ReschedulePickupDate": RewashDate,
                "CustomerName": CustomerName,
                "MobileNumber": MobileNumber,
                "POSId": 6,
                "CustomerCode": CustomerCode,
                "RescheduledServiceTypeId":RescheduledServiceTypeId
            }
            final_data['result'] = result
    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(future_date_rewash_form.errors)
    log_data = {
        'final_data': final_data,       
                    }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))
    return final_data


@delivery_blueprint.route('/get_pickup_instructions', methods=["POST"])
# @authenticate('delivery_user')
def GetPickupInstructions():
    get_pickup_instructions_form = GetPickupInstructionsForm()
    if get_pickup_instructions_form.validate_on_submit():
        BookingId = get_pickup_instructions_form.BookingId.data

        if BookingId :
          
            PickupInstructions = f"EXEC JFSL.DBO.SPFABPickupInstructions @bookingID={BookingId}, @pickupStatus={1}"

            PickupInstructionsResult = CallSP(PickupInstructions).execute().fetchall()

            # PickipInstructionsResult = SerializeSQLAResult(PickipInstructionsResult).serialize()
            log_data = {
                'query result': PickupInstructionsResult,
                'query': PickupInstructions
            }
            info_logger(f'Route: {request.path}').info(json.dumps(log_data))

            for result in PickupInstructionsResult:
                image_filename = result['PickupinstructionsImage']
                if image_filename:
                    result['PickupinstructionsImage'] = 'https://api.jfsl.in/store_console/get_image/' + image_filename

            final_data = generate_final_data('SUCCESS')
            final_data['PickupInstructions'] = PickupInstructionsResult

        else:
            final_data = generate_final_data('CUSTOM_FAILED', error_msg)
    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(get_pickup_instructions_form.errors)
    return final_data


@delivery_blueprint.route('/generate_qr_code', methods=["POST"])
# @authenticate('delivery_user')
def GenrateQRCode():
    GenarateQRCodeForm = GenaretRazorPayQRCode()
    if GenarateQRCodeForm.validate_on_submit():
        log_data = {
                'GenarateQRCodeForm': GenarateQRCodeForm.data,
               
            }
        info_logger(f'Route: {request.path}').info(json.dumps(log_data))
        TRNNo = GenarateQRCodeForm.TRNNo.data
        EGRN = GenarateQRCodeForm.EGRN.data
        DeliveryWithoutOtp = GenarateQRCodeForm.DeliveryWithoutOtp.data
        DeliverWithoutPayment = GenarateQRCodeForm.DeliverWithoutPayment.data
        lat = 0.0 if GenarateQRCodeForm.lat.data == '' else GenarateQRCodeForm.lat.data
        long = 0.0 if GenarateQRCodeForm.long.data == '' else GenarateQRCodeForm.long.data
        Custlat = 0.0 if GenarateQRCodeForm.CustLat.data == '' else GenarateQRCodeForm.CustLat.data
        Custlong = 0.0 if GenarateQRCodeForm.CustLong.data == '' else GenarateQRCodeForm.CustLong.data
        ReasonList = None if GenarateQRCodeForm.ReasonList.data == '' else GenarateQRCodeForm.ReasonList.data
        CustomerName = GenarateQRCodeForm.CustomerName.data
        MobileNumber = GenarateQRCodeForm.MobileNumber.data
        CustomerCode = GenarateQRCodeForm.CustomerCode.data
        BranchCode = GenarateQRCodeForm.BranchCode.data
        BookingId = GenarateQRCodeForm.BookingId.data
        Remarks = GenarateQRCodeForm.Remarks.data
        user_id = request.headers.get('user-id')
        reasons_str = ','.join(ReasonList)
        Amount = GenarateQRCodeForm.Amount.data
        UserId = request.headers.get('user-id')
        CouponCode = GenarateQRCodeForm.CouponCode.data
        error_msg = 'Failed to generate Qr code please choose another payment mode'
        auth = (os.getenv('RazorPayLiveUserName').strip(), os.getenv('RazorPayLivePassword').strip())
        delivered = False
        error_msg = ''
        already_delivered = None
        proceed_to_delivery = False
        delivery_request = None
        order_details = None
        Status = None
        activity_status = 0
        in_location = ''
        distance = 0
        DuserDistance = 0
        StoreDistance = 0
        distance_dis = 0
        garment_counts = False
        partial_status = None
        trigger_mail = False
        updated = False

        NotDelivered = db.session.execute(text(""" SELECT DuserLat, DuserLong from JFSL.Dbo.FabdeliveryInfo where TRNNO = :TRNNo and DuserLat =0   AND DuserLong = 0

            """),{"TRNNo":TRNNo}).fetchone()
        if NotDelivered:
            updated  = delivery_controller_queries.update_lat_long(lat,long,Custlat,Custlong,TRNNo,EGRN,BranchCode,UserId)

        else:
            updated = True

        IsExistingQrCode = db.session.query(RazorpayPayments.QrCode).filter(
            RazorpayPayments.TRNNo == TRNNo,
            RazorpayPayments.IsExpired == 0,
            RazorpayPayments.IsDeleted == 0
        ).order_by(
            RazorpayPayments.RecordCreatedDate.desc()
        ).first()
      
        if IsExistingQrCode:
            ExistingQrCode = IsExistingQrCode[0]
            api_url = f"https://api.razorpay.com/v1/payments/qr_codes/{ExistingQrCode}/close"
            headers = {'Content-Type': 'application/json'}
            response = requests.post(api_url, headers=headers, auth=auth)
            response.raise_for_status()
            response_data = response.json()
            log_data = {
                'response_data': response_data,
                "api_url":api_url
               
            }
            info_logger(f'Route: {request.path}').info(json.dumps(log_data))

            if response_data.get('status') == 'closed':
               
                db.session.execute(text(""" 

                    UPDATE RazorpayPayments SET IsExpired = 1, IsDeleted = 1 WHERE TRNNo = :TRNNo
                    """),{"TRNNo":TRNNo})
                db.session.commit()
        if CouponCode :
            CouponCode = CouponCode[0]
        else:
            CouponCode = ''

        result = db.session.execute(
            text("""
                SELECT CustomerCode 
                FROM JFSL.DBO.FabdeliveryInfo 
                WHERE TRNNo = :TRNNo
            """),
            {"TRNNo": TRNNo}
        ).scalar()   # directly gives single value

        CustomerCode = result if result else None

        # Fetch CustomerName
        if CustomerCode:
            CustomerName = db.session.execute(
                text("""
                    SELECT FirstName 
                    FROM JFSL.DBO.CustomerInfo 
                    WHERE CustomerCode = :CustomerCode
                """),
                {"CustomerCode": CustomerCode}
            ).scalar()
        else:
            CustomerName = None

        RequestBody = {
            "type": "upi_qr",
            "name": "QR_1",
            "usage": "single_use",
            "fixed_amount": True,
            "payment_amount": Amount*100,
            "description": "UPI Payment",
            "notes": {
                "notes_key_1": "",
                "notes_key_2": "",
                "notes_key_3": CustomerCode,
                "notes_key_4": EGRN,
                "notes_key_5": "FABEXPRESS",
                "notes_key_6": MobileNumber,
                "notes_key_7": CustomerName,
               
                 "user-id":UserId,
                 "TRNNo": TRNNo,
            }
        }
        api_url = 'https://api.razorpay.com/v1/payments/qr_codes'

       
        headers = {
            'Content-Type': 'application/json'
        }
        response = requests.post(api_url, data=json.dumps(RequestBody), headers=headers, auth=auth)
       
        response_data = response.json()
        log_data = {
            "api_url":api_url,
            "RequestBody":RequestBody,

                'response_data': response_data
               
            }
        info_logger(f'Route: {request.path}').info(json.dumps(log_data))
      
        if response_data.get('id') and updated :
            final_data = generate_final_data('SUCCESS')
            final_data['result'] = response_data
            

            try:
                NewTransaction = RazorpayPayments(TRNNo=TRNNo, UserId=UserId, PaymentMode='Fabexpress QR CODE', Amount=Amount,
                              RecordCreatedDate= get_current_date(),
                              IsExpired = 0,
                              IsDeleted= 0,PaymentStatus = 'Pending',
                                                  EGRN = EGRN, MobileNumber = MobileNumber,IsSettled= 0,QrCode = response_data.get('id'),
                                                  QrLink = response_data.get('image_url'),CouponCode = CouponCode

                              )
                db.session.add(NewTransaction)
                db.session.commit()
            except Exception as e:
                error_logger(f'Route: {request.path}').error(e)

        else:
            final_data = generate_final_data('CUSTOM_FAILED', error_msg)
    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(GenarateQRCodeForm.errors)
    log_data = {
                'final_data': final_data,
               
            }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))
    return final_data


@delivery_blueprint.route('/send_payment_link_new', methods=["POST"])
# @authenticate('delivery_user')
def send_payment_link_new():
    """
    Function to prevent expiring payment link,
    API for sending the payment link to the customer.
    @return:
    """
    payment_link_form = SendPaymentLinkForm()
    if payment_link_form.validate_on_submit():
        CustomerCode = payment_link_form.CustomerCode.data
        TRNNo = payment_link_form.TRNNo.data
        COUNT = payment_link_form.COUNT.data
        EGRN = payment_link_form.EGRN.data
        MobileNumber = payment_link_form.MobileNumber.data

        DeliveryWithoutOtp = payment_link_form.DeliveryWithoutOtp.data
        DeliverWithoutPayment = payment_link_form.DeliverWithoutPayment.data
        lat = 0.0 if payment_link_form.lat.data == '' else payment_link_form.lat.data
        long = 0.0 if payment_link_form.long.data == '' else payment_link_form.long.data
        Custlat = 0.0 if payment_link_form.CustLat.data == '' else payment_link_form.CustLat.data
        Custlong = 0.0 if payment_link_form.CustLong.data == '' else payment_link_form.CustLong.data
        ReasonList = None if payment_link_form.ReasonList.data == '' else payment_link_form.ReasonList.data
        CustomerName = payment_link_form.CustomerName.data
        CustomerCode = payment_link_form.CustomerCode.data
        BranchCode = payment_link_form.BranchCode.data
        BookingId = payment_link_form.BookingId.data
        Remarks = payment_link_form.Remarks.data
        user_id = request.headers.get('user-id')
        UserId = request.headers.get('user-id')
        reasons_str = ','.join(ReasonList)
        amount = 0
        discount_amount = 0

        send_status = False
        payment_link = ''
        sender = "FABSPA"
        head = "Fabricspa"
        is_success = False
        error_msg = ''
        CouponCode = None
        updated = False
        #amount = 0.0
        try:
            query = f" EXEC JFSL.[dbo].SpIsSettledInvoice @TRNNO ='{TRNNo}'"

            result = CallSP(query).execute().fetchall()
            print(result)

            if result and result[0].get('IsSettled') is False:
                NotDelivered = db.session.execute(text(""" SELECT DuserLat, DuserLong from JFSL.Dbo.FabdeliveryInfo where TRNNO = :TRNNo and DuserLat =0   AND DuserLong = 0

                """),{"TRNNo":TRNNo}).fetchone()
                if NotDelivered:
                    updated  = delivery_controller_queries.update_lat_long(lat,long,Custlat,Custlong,TRNNo,EGRN,BranchCode,UserId)

                else:
                    updated = True

                egrn = EGRN
                result = payment_module.get_available_coupon_codes(egrn)
                amount_dtls = delivery_controller_queries.get_payable_amount_via_sp(
                    CustomerCode,
                    TRNNo)
                if amount_dtls and 'PAYABLEAMOUNT' in amount_dtls:
                    PayableAmount = amount_dtls['PAYABLEAMOUNT']
                    log_data = {
                        'amount': PayableAmount,

                    }
                    info_logger(f'Route: {request.path}').info(json.dumps(log_data))
                    coupon_details = db.session.execute(
                        text("SELECT Couponcode FROM JFSL.dbo.OrderInfo WHERE EGRNNo = :egrn"),
                        {"egrn": egrn}
                    ).fetchone()
                    #if coupon_details is not None:
                    if coupon_details and coupon_details[0]:
                        log_data = {
                                  
                            'test4' : "test"

                        }
                        info_logger(f'Route: {request.path}').info(json.dumps(log_data))
                        expected_coupon_code = coupon_details[0]
                        all_coupons = payment_module.get_available_coupon_codes(egrn)

                        # Filter only the coupon that matches the one in OrderInfo
                        if isinstance(all_coupons, list):
                            matching_coupons = [
                                coupon for coupon in all_coupons
                                if str(coupon.get("COUPONCODE")) == str(expected_coupon_code)
                            ]
                            if matching_coupons:
                                discount_amount = matching_coupons[0].get('DISCOUNTAMOUNT', 0)
                                CouponCode = matching_coupons[0].get('COUPONCODE', '')
                                amount = PayableAmount - discount_amount
                                log_data = {
                                  
                                    'test1' : "test"

                                }
                                info_logger(f'Route: {request.path}').info(json.dumps(log_data))
                            else:
                                amount = PayableAmount
                                log_data = {
                                    
                                    'test2' : "test"

                                }
                                info_logger(f'Route: {request.path}').info(json.dumps(log_data))
                                CouponCode = ""


                    else:
      
                        amount = PayableAmount
                       
                        CouponCode = ""

                user_info = db.session.execute(
                    text("SELECT DUserId FROM JFSL.dbo.FabDeliveryInfo WHERE EGRNNo = :egrn"),
                    {"egrn": EGRN}
                ).fetchone()
                log_data = {
                                    
                    'test3' : user_info[0] if user_info else None

                }
                info_logger(f'Route: {request.path}').info(json.dumps(log_data))

                DUserId = user_info[0] if user_info and user_info[0] else None
                # Generating the new payment id. Payment id will be the same for all the EGRN orders.
                new_payment_id = db.session.query(func.newid().label('Id')).one_or_none()
                payment_id = new_payment_id.Id
                # Logging the data in the request into log file.
                # Generating the new transaction_id.
                new_transaction_id = db.session.query(func.newid().label('Id')).one_or_none()
                transaction_id = new_transaction_id.Id
                log_data = {
                                    
                    'test4' : "test"

                }
                info_logger(f'Route: {request.path}').info(json.dumps(log_data))

                try:
                    db.session.query(TransactionInfo).filter(
                        (TransactionInfo.EGRNNo == EGRN) | 
                        (TransactionInfo.DCNo == TRNNo)
                    ).delete(synchronize_session=False)
                    db.session.commit()
                except Exception as e:
                    db.session.rollback()
                    error_logger(f'Route: {request.path}').error(f'Error deleting existing TransactionInfo: {str(e)}')

                # Creating a new TransactionInfo object to insert.
                new_transaction_info = TransactionInfo(
                    CustomerCode=CustomerCode,
                    TransactionId=transaction_id,
                    TransactionDate=get_current_date(),
                    EGRNNo=EGRN,
                    DCNo=TRNNo,
                    FinalServiceAmount=amount,
                    FinalProductAmount=None,
                    TotalPayableAmount=amount,
                    RoundOff=None,
                    PaymentId=payment_id,
                    PaymentSource='Razorpay PaymentLink',
                    OrderGarmentIDs=None,
                    UsedCompensationCoupons=None,
                    DiscountAmount=discount_amount,
                    RevisedBasicAmount=None,
                    RevisedRoundOff=None,
                    RevisedInvoiceAmount=None,
                    ProductBasicAmount=None,
                    ProductRoundOff=None,
                    ProductInvoiceAmount=None,
                    RevisedPayableAmount=None,
                    InvoiceDiscountCode=None,
                    InvoiceDiscount=None,
                    GarmentsCount=COUNT,
                    PaymentFrom=None,
                    PaymentCollectedBY=DUserId,
                    Gateway=None,
                    CouponCode=CouponCode
                )

                # db.session.add(new_transaction_info)
                # db.session.commit()
                try:
                    db.session.add(new_transaction_info)
                    db.session.commit()
                except Exception as e:
                    db.session.rollback()
                    error_logger(f'Route: {request.path}').error(f'Error inserting TransactionInfo: {str(e)}')


                is_success = True
                if is_success:

                    try:
                        
                        select_sql = text("""
                            SELECT * FROM Mobile_JFSL.Dbo.TransactionInfo
                            WHERE EGRNNo = :egrn OR DCNo = :trn
                        """)
                        result = db.session.execute(select_sql, {"egrn": EGRN, "trn": TRNNo}).fetchall()

                        if result:

                            
                            update_sql = text("""
                                UPDATE Mobile_JFSL.Dbo.TransactionInfo
                                SET is_active = 0, Is_Delete = 1
                                WHERE (EGRNNo = :egrn AND DCNo = :trn)
                                 
                            """)

                            db.session.execute(update_sql, {"egrn": EGRN, "trn": TRNNo})

                            db.session.commit()

                    except Exception as e:
                        db.session.rollback()
                        error_logger(f'Route: {request.path}').error(f'Error updating IsActive in TransactionInfo: {str(e)}')


                    db.session.execute(text(""" 
                        INSERT INTO Mobile_JFSL.Dbo.TransactionInfo 
                        (
                            CustomerCode, TransactionId, TransactionDate, EGRNNo, DCNo,
                            FinalServiceAmount, FinalProductAmount, TotalPayableAmount, RoundOff,
                            Status, PaymentId, PaymentSource, OrderGarmentIDs, Gateway,
                            Loyaltypoints, LoyaltyPointsRate, LoyaltyPointsAmount, AvailableLoyaltyPoints,
                            ERTransactionCode, InvoiceNo, DiscountAmount,
                            RevisedBasicAmount, RevisedRoundOff, RevisedInvoiceAmount,
                            ProductBasicAmount, ProductRoundOff, ProductInvoiceAmount, RevisedPayableAmount,
                            InvoiceDiscountCode, InvoiceDiscount, GarmentsCount,
                            SourceFrom, is_active, PaymentLinkSentBy,
                           

                            ServiceCharge, ServiceSGST, ServiceCGST, ServiceGST,
                            ProductCharge, ProductSGST, ProductCGST, ProductGST,
                            TransactionCarryBagId, UsedCompensationCoupons,
                            ConsoleVerify, ManualVerify, VerifiedBy, VerificationDate
                        ) 
                        VALUES (
                            :CustomerCode, :TransactionId, :TransactionDate, :EGRNNo, :DCNo,
                            :FinalServiceAmount, :FinalProductAmount, :TotalPayableAmount, :RoundOff,
                            :Status, :PaymentId, :PaymentSource, :OrderGarmentIDs, :Gateway,
                            :Loyaltypoints, :LoyaltyPointsRate, :LoyaltyPointsAmount, :AvailableLoyaltyPoints,
                            :ERTransactionCode, :InvoiceNo, :DiscountAmount,
                            :RevisedBasicAmount, :RevisedRoundOff, :RevisedInvoiceAmount,
                            :ProductBasicAmount, :ProductRoundOff, :ProductInvoiceAmount, :RevisedPayableAmount,
                            :InvoiceDiscountCode, :InvoiceDiscount, :GarmentsCount,
                            :SourceFrom, :is_active, :PaymentLinkSentBy,
                            

                            :ServiceCharge, :ServiceSGST, :ServiceCGST, :ServiceGST,
                            :ProductCharge, :ProductSGST, :ProductCGST, :ProductGST,
                            :TransactionCarryBagId, :UsedCompensationCoupons,
                            :ConsoleVerify, :ManualVerify, :VerifiedBy, :VerificationDate
                        )
                    """), {
                        "CustomerCode": CustomerCode,
                        "TransactionId": transaction_id,
                        "TransactionDate": get_current_date(),
                        "EGRNNo": EGRN,
                        "DCNo": TRNNo,

                        "FinalServiceAmount": amount,
                        "FinalProductAmount": None,
                        "TotalPayableAmount": amount,
                        "RoundOff": None,


                        "Status": 0,
                        "PaymentId": payment_id,
                        "PaymentSource": 'Razorpay PaymentLink',
                        "OrderGarmentIDs": None,
                        "Gateway": None,

                        "Loyaltypoints": None,
                        "LoyaltyPointsRate": None,
                        "LoyaltyPointsAmount": None,
                        "AvailableLoyaltyPoints": None,

                        "ERTransactionCode": None,
                        "InvoiceNo": None,
                        
                        "DiscountAmount": discount_amount,

                        "RevisedBasicAmount": None,
                        "RevisedRoundOff": None,
                        "RevisedInvoiceAmount": None,

                        "ProductBasicAmount": None,
                        "ProductRoundOff": None,
                        "ProductInvoiceAmount": None,
                        "RevisedPayableAmount": None,

                        "InvoiceDiscountCode": None,
                        "InvoiceDiscount": None,
                        "GarmentsCount": COUNT,

                        "SourceFrom": "Fabexpress",
                        "is_active": 1,
                        "PaymentLinkSentBy": DUserId,


                        "ServiceCharge": None,
                        "ServiceSGST": None,
                        "ServiceCGST": None,
                        "ServiceGST": None,

                        "ProductCharge": None,
                        "ProductSGST": None,
                        "ProductCGST": None,
                        "ProductGST": None,

                        "TransactionCarryBagId": None, 
                        "UsedCompensationCoupons":CouponCode ,

                        "ConsoleVerify": None,
                        "ManualVerify": None,
                        "VerifiedBy": None,
                        "VerificationDate": None
                    })
                    db.session.commit()

                
                headers = {
                    'accept': '*/*'
                }

                #api_url = 'https://uat.jfsl.in/Razorpay_API/ShortLink/Link'
                api_url = 'https://live.jfsl.in/Razorpay_API/ShortLink/Link'


                params = {
                    # "TransactionId": transaction_id
                    "TransactionId":payment_id
                }

                try:
                    response = requests.get(api_url, headers=headers, params=params)
                    response_json = response.json()
                except Exception as e:
                    response_json = {"status": "error", "message": str(e)}

                log_data = {
                    'response': response_json,
                    'api_url': api_url,
                    'full_api_url': response.url
                }
                info_logger(f'Route: {request.path}').info(json.dumps(log_data))

                if response_json:
                    payment_link = response_json.get('short_url')
                    log_data = {
                    'payment_link': payment_link,
                    
                    }
                    info_logger(f'Route: {request.path}').info(json.dumps(log_data))
                else:
                    api_url = "https://fabspa.in/sui/get_link"
                    payload = json.dumps({
                        "url": f"http://3.109.116.65:88/{payment_id}"
                    })

                    headers = {
                        'Content-Type': 'application/json',
                        'api_key': 'asdasHWod3(&22XK:Ji2))2j653&'
                    }
                    response = requests.request("POST", api_url, headers=headers, data=payload)
                    response_json = response.json()
                    if response_json:
                        payment_link = response_json.get('short_url')
                        log_data = {
                            'response': response_json,
                            'api_url': api_url,
                            'full_api_url': response.url,
                            'payment_link':payment_link
                        }
                        info_logger(f'Route: {request.path}').info(json.dumps(log_data))


                query = f"EXEC CustomerApp.[dbo].[GetBrandName] @BranchCode='NULL', @EGRNNo={EGRN}, @PickupRequestId=NULL"
                brand_details = CallSP(query).execute().fetchone()


                if brand_details and brand_details["BrandDescription"] != 'FABRICSPA':
                    sender = brand_details["BrandDescription"]
                    # print(sender)
                    head = "QUICLO"
                    sp_query = f"EXEC JFSL.dbo.GenerateUniqueCombination @longurl='{payment_link}', @Source='FabxpressPaymentLink', @brand='{sender}', @DocumentType='EGRN', @DocumentNo='{EGRN}'"
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
                        payment_link = sp_result.get('GeneratedCombination')

                        log_data = {
                            'payment_link': payment_link,

                        }
                        info_logger(f'Route: {request.path}').info(json.dumps(log_data))
                else:
                    pass
                log_data = {
                        'payment_link': payment_link,
                        
                    }
                info_logger(f'Route: {request.path}').info(json.dumps(log_data))

                if payment_link:
                    message = f'{head} has now made the payment process easier, click here {payment_link} to ' \
                              f'complete the payment of Rs {amount}/- from anywhere you are.'
                    sms = send_sms(MobileNumber, message, '', sender)

                    if sms['result']:
                        if sms['result'].get('status') == "OK":
                            send_status = True
                    else:
                        error_msg = 'Failed to send payment link please contact adminstrator'

            else:
                error_msg = 'Payment has already been received for this order'
                #error_msg = 'Payment is already received for this order'
                

                
                # success_msg = 'Payment is already received for this order'
                # final_data = generate_final_data('SUCCESS', success_msg)

        except Exception as e:
            error_logger(f'Route: {request.path}').error(e)

        

        if send_status or updated:
            final_data = generate_final_data('SUCCESS')
            final_data['result'] = payment_link
        
        else:
            final_data = generate_final_data('FAILED',error_msg)

    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(payment_link_form.errors)
    log_data = {
        'final_data': final_data
    }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))
    return final_data

@delivery_blueprint.route('/send_payment_link1', methods=["POST"])
# @authenticate('delivery_user')
def send_payment_link1():
    """
    Function to prevent expiring payment link,
    API for sending the payment link to the customer.
    @return:
    """
    payment_link_form = SendPaymentLinkForm()
    if payment_link_form.validate_on_submit():
        CustomerCode = payment_link_form.CustomerCode.data
        TRNNo = payment_link_form.TRNNo.data
        COUNT = payment_link_form.COUNT.data
        EGRN = payment_link_form.EGRN.data
        MobileNumber = payment_link_form.MobileNumber.data

        DeliveryWithoutOtp = payment_link_form.DeliveryWithoutOtp.data
        DeliverWithoutPayment = payment_link_form.DeliverWithoutPayment.data
        lat = 0.0 if payment_link_form.lat.data == '' else payment_link_form.lat.data
        long = 0.0 if payment_link_form.long.data == '' else payment_link_form.long.data
        Custlat = 0.0 if payment_link_form.CustLat.data == '' else payment_link_form.CustLat.data
        Custlong = 0.0 if payment_link_form.CustLong.data == '' else payment_link_form.CustLong.data
        ReasonList = None if payment_link_form.ReasonList.data == '' else payment_link_form.ReasonList.data
        CustomerName = payment_link_form.CustomerName.data
        CustomerCode = payment_link_form.CustomerCode.data
        BranchCode = payment_link_form.BranchCode.data
        BookingId = payment_link_form.BookingId.data
        Remarks = payment_link_form.Remarks.data
        user_id = request.headers.get('user-id')
        UserId = request.headers.get('user-id')
        reasons_str = ','.join(ReasonList)
        amount = 0
        discount_amount = 0

        send_status = False
        payment_link = ''
        sender = "FABSPA"
        head = "Fabricspa"
        is_success = False
        error_msg = ''
        CouponCode = None
        #amount = 0.0
        try:
            query = f" EXEC JFSL.[dbo].SpIsSettledInvoice @TRNNO ='{TRNNo}'"

            result = CallSP(query).execute().fetchall()
            print(result)

            if result and result[0].get('IsSettled') is False:
                NotDelivered = db.session.execute(text(""" SELECT DuserLat, DuserLong from JFSL.Dbo.FabdeliveryInfo where TRNNO = :TRNNo and DuserLat =0   AND DuserLong = 0

                """),{"TRNNo":TRNNo}).fetchone()
                if NotDelivered:
                    updated  = delivery_controller_queries.update_lat_long(lat,long,Custlat,Custlong,TRNNo,EGRN,BranchCode,UserId)

                else:
                    updated = True

                egrn = EGRN
                result = payment_module.get_available_coupon_codes(egrn)
                amount_dtls = delivery_controller_queries.get_payable_amount_via_sp(
                    CustomerCode,
                    TRNNo)
                if amount_dtls and 'PAYABLEAMOUNT' in amount_dtls:
                    PayableAmount = amount_dtls['PAYABLEAMOUNT']
                    log_data = {
                        'amount': PayableAmount,

                    }
                    info_logger(f'Route: {request.path}').info(json.dumps(log_data))
                    coupon_details = db.session.execute(
                        text("SELECT Couponcode FROM JFSL.dbo.OrderInfo WHERE EGRNNo = :egrn"),
                        {"egrn": egrn}
                    ).fetchone()
                    #if coupon_details is not None:
                    if coupon_details and coupon_details[0]:
                        log_data = {
                                  
                            'test4' : "test"

                        }
                        info_logger(f'Route: {request.path}').info(json.dumps(log_data))
                        expected_coupon_code = coupon_details[0]
                        all_coupons = payment_module.get_available_coupon_codes(egrn)

                        # Filter only the coupon that matches the one in OrderInfo
                        if isinstance(all_coupons, list):
                            matching_coupons = [
                                coupon for coupon in all_coupons
                                if str(coupon.get("COUPONCODE")) == str(expected_coupon_code)
                            ]
                            if matching_coupons:
                                discount_amount = matching_coupons[0].get('DISCOUNTAMOUNT', 0)
                                CouponCode = matching_coupons[0].get('COUPONCODE', '')
                                amount = PayableAmount - discount_amount
                                log_data = {
                                  
                                    'test1' : "test"

                                }
                                info_logger(f'Route: {request.path}').info(json.dumps(log_data))
                            else:
                                amount = PayableAmount
                                log_data = {
                                    
                                    'test2' : "test"

                                }
                                info_logger(f'Route: {request.path}').info(json.dumps(log_data))
                                CouponCode = ""


                    else:
      
                        amount = PayableAmount
                       
                        CouponCode = ""

                user_info = db.session.execute(
                    text("SELECT DUserId FROM JFSL.dbo.FabDeliveryInfo WHERE EGRNNo = :egrn"),
                    {"egrn": EGRN}
                ).fetchone()
                DUserId = user_info[0] if user_info and user_info[0] else None
                # Generating the new payment id. Payment id will be the same for all the EGRN orders.
                new_payment_id = db.session.query(func.newid().label('Id')).one_or_none()
                payment_id = new_payment_id.Id
                # Logging the data in the request into log file.
                # Generating the new transaction_id.
                new_transaction_id = db.session.query(func.newid().label('Id')).one_or_none()
                transaction_id = new_transaction_id.Id

                try:
                    db.session.query(TransactionInfo).filter(
                        (TransactionInfo.EGRNNo == EGRN) | 
                        (TransactionInfo.DCNo == TRNNo)
                    ).delete(synchronize_session=False)
                    db.session.commit()
                except Exception as e:
                    db.session.rollback()
                    error_logger(f'Route: {request.path}').error(f'Error deleting existing TransactionInfo: {str(e)}')

                # Creating a new TransactionInfo object to insert.
                new_transaction_info = TransactionInfo(
                    CustomerCode=CustomerCode,
                    TransactionId=transaction_id,
                    TransactionDate=get_current_date(),
                    EGRNNo=EGRN,
                    DCNo=TRNNo,
                    FinalServiceAmount=amount,
                    FinalProductAmount=None,
                    TotalPayableAmount=amount,
                    RoundOff=None,
                    PaymentId=payment_id,
                    PaymentSource='Razorpay PaymentLink',
                    OrderGarmentIDs=None,
                    UsedCompensationCoupons=None,
                    DiscountAmount=discount_amount,
                    RevisedBasicAmount=None,
                    RevisedRoundOff=None,
                    RevisedInvoiceAmount=None,
                    ProductBasicAmount=None,
                    ProductRoundOff=None,
                    ProductInvoiceAmount=None,
                    RevisedPayableAmount=None,
                    InvoiceDiscountCode=None,
                    InvoiceDiscount=None,
                    GarmentsCount=COUNT,
                    PaymentFrom=None,
                    PaymentCollectedBY=DUserId,
                    Gateway=None,
                    CouponCode=CouponCode
                )

                # db.session.add(new_transaction_info)
                # db.session.commit()
                try:
                    db.session.add(new_transaction_info)
                    db.session.commit()
                except Exception as e:
                    db.session.rollback()
                    error_logger(f'Route: {request.path}').error(f'Error inserting TransactionInfo: {str(e)}')


                is_success = True
                if is_success:

                    try:
                        
                        select_sql = text("""
                            SELECT * FROM Mobile_JFSL.Dbo.TransactionInfo
                            WHERE EGRNNo = :egrn OR DCNo = :trn
                        """)
                        result = db.session.execute(select_sql, {"egrn": EGRN, "trn": TRNNo}).fetchall()

                        if result:

                            
                            update_sql = text("""
                                UPDATE Mobile_JFSL.Dbo.TransactionInfo
                                SET is_active = 0, Is_Delete = 1
                                WHERE (EGRNNo = :egrn AND DCNo = :trn)
                                 
                            """)

                            db.session.execute(update_sql, {"egrn": EGRN, "trn": TRNNo})

                            db.session.commit()

                    except Exception as e:
                        db.session.rollback()
                        error_logger(f'Route: {request.path}').error(f'Error updating IsActive in TransactionInfo: {str(e)}')


                    db.session.execute(text(""" 
                        INSERT INTO Mobile_JFSL.Dbo.TransactionInfo 
                        (
                            CustomerCode, TransactionId, TransactionDate, EGRNNo, DCNo,
                            FinalServiceAmount, FinalProductAmount, TotalPayableAmount, RoundOff,
                            Status, PaymentId, PaymentSource, OrderGarmentIDs, Gateway,
                            Loyaltypoints, LoyaltyPointsRate, LoyaltyPointsAmount, AvailableLoyaltyPoints,
                            ERTransactionCode, InvoiceNo, DiscountAmount,
                            RevisedBasicAmount, RevisedRoundOff, RevisedInvoiceAmount,
                            ProductBasicAmount, ProductRoundOff, ProductInvoiceAmount, RevisedPayableAmount,
                            InvoiceDiscountCode, InvoiceDiscount, GarmentsCount,
                            SourceFrom, is_active, PaymentLinkSentBy,
                           

                            ServiceCharge, ServiceSGST, ServiceCGST, ServiceGST,
                            ProductCharge, ProductSGST, ProductCGST, ProductGST,
                            TransactionCarryBagId, UsedCompensationCoupons,
                            ConsoleVerify, ManualVerify, VerifiedBy, VerificationDate
                        ) 
                        VALUES (
                            :CustomerCode, :TransactionId, :TransactionDate, :EGRNNo, :DCNo,
                            :FinalServiceAmount, :FinalProductAmount, :TotalPayableAmount, :RoundOff,
                            :Status, :PaymentId, :PaymentSource, :OrderGarmentIDs, :Gateway,
                            :Loyaltypoints, :LoyaltyPointsRate, :LoyaltyPointsAmount, :AvailableLoyaltyPoints,
                            :ERTransactionCode, :InvoiceNo, :DiscountAmount,
                            :RevisedBasicAmount, :RevisedRoundOff, :RevisedInvoiceAmount,
                            :ProductBasicAmount, :ProductRoundOff, :ProductInvoiceAmount, :RevisedPayableAmount,
                            :InvoiceDiscountCode, :InvoiceDiscount, :GarmentsCount,
                            :SourceFrom, :is_active, :PaymentLinkSentBy,
                            

                            :ServiceCharge, :ServiceSGST, :ServiceCGST, :ServiceGST,
                            :ProductCharge, :ProductSGST, :ProductCGST, :ProductGST,
                            :TransactionCarryBagId, :UsedCompensationCoupons,
                            :ConsoleVerify, :ManualVerify, :VerifiedBy, :VerificationDate
                        )
                    """), {
                        "CustomerCode": CustomerCode,
                        "TransactionId": transaction_id,
                        "TransactionDate": get_current_date(),
                        "EGRNNo": EGRN,
                        "DCNo": TRNNo,

                        "FinalServiceAmount": amount,
                        "FinalProductAmount": None,
                        "TotalPayableAmount": amount,
                        "RoundOff": None,


                        "Status": 0,
                        "PaymentId": payment_id,
                        "PaymentSource": 'Razorpay PaymentLink',
                        "OrderGarmentIDs": None,
                        "Gateway": None,

                        "Loyaltypoints": None,
                        "LoyaltyPointsRate": None,
                        "LoyaltyPointsAmount": None,
                        "AvailableLoyaltyPoints": None,

                        "ERTransactionCode": None,
                        "InvoiceNo": None,
                        
                        "DiscountAmount": discount_amount,

                        "RevisedBasicAmount": None,
                        "RevisedRoundOff": None,
                        "RevisedInvoiceAmount": None,

                        "ProductBasicAmount": None,
                        "ProductRoundOff": None,
                        "ProductInvoiceAmount": None,
                        "RevisedPayableAmount": None,

                        "InvoiceDiscountCode": None,
                        "InvoiceDiscount": None,
                        "GarmentsCount": COUNT,

                        "SourceFrom": "Fabexpress",
                        "is_active": 1,
                        "PaymentLinkSentBy": DUserId,


                        "ServiceCharge": None,
                        "ServiceSGST": None,
                        "ServiceCGST": None,
                        "ServiceGST": None,

                        "ProductCharge": None,
                        "ProductSGST": None,
                        "ProductCGST": None,
                        "ProductGST": None,

                        "TransactionCarryBagId": None, 
                        "UsedCompensationCoupons":CouponCode ,

                        "ConsoleVerify": None,
                        "ManualVerify": None,
                        "VerifiedBy": None,
                        "VerificationDate": None
                    })
                    db.session.commit()


                headers = {
                    'accept': '*/*'
                }

                #api_url = 'https://uat.jfsl.in/Razorpay_API/ShortLink/Link'
                api_url = 'https://live.jfsl.in/Razorpay_API/ShortLink/Link'


                params = {
                    # "TransactionId": transaction_id
                    "TransactionId":payment_id
                }

                try:
                    response = requests.get(api_url, headers=headers, params=params)
                    response_json = response.json()
                except Exception as e:
                    response_json = {"status": "error", "message": str(e)}

                log_data = {
                    'response': response_json,
                    'api_url': api_url,
                    'full_api_url': response.url
                }
                info_logger(f'Route: {request.path}').info(json.dumps(log_data))

                if response_json:
                    payment_link = response_json.get('short_url')
                    log_data = {
                    'payment_link': payment_link,
                    
                    }
                    info_logger(f'Route: {request.path}').info(json.dumps(log_data))
                else:
                    api_url = "https://fabspa.in/sui/get_link"
                    payload = json.dumps({
                        "url": f"http://3.109.116.65:88/{payment_id}"
                    })

                    headers = {
                        'Content-Type': 'application/json',
                        'api_key': 'asdasHWod3(&22XK:Ji2))2j653&'
                    }
                    response = requests.request("POST", api_url, headers=headers, data=payload)
                    response_json = response.json()
                    if response_json:
                        payment_link = response_json.get('short_url')
                        log_data = {
                            'response': response_json,
                            'api_url': api_url,
                            'full_api_url': response.url,
                            'payment_link':payment_link
                        }
                        info_logger(f'Route: {request.path}').info(json.dumps(log_data))

                

                query = f"EXEC CustomerApp.[dbo].[GetBrandName] @BranchCode='NULL', @EGRNNo={EGRN}, @PickupRequestId=NULL"
                brand_details = CallSP(query).execute().fetchone()


                if brand_details and brand_details["BrandDescription"] != 'FABRICSPA':
                    sender = brand_details["BrandDescription"]
                    # print(sender)
                    head = "QUICLO"
                    sp_query = f"EXEC JFSL.dbo.GenerateUniqueCombination @longurl='{payment_link}', @Source='FabxpressPaymentLink', @brand='{sender}', @DocumentType='EGRN', @DocumentNo='{EGRN}'"
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
                        payment_link = sp_result.get('GeneratedCombination')

                        log_data = {
                            'payment_link': payment_link,

                        }
                        info_logger(f'Route: {request.path}').info(json.dumps(log_data))
                else:
                    pass
                # log_data = {
                #         'payment_link': payment_link,
                        
                #     }
                # info_logger(f'Route: {request.path}').info(json.dumps(log_data))

                # if payment_link:
                #     message = f'{head} has now made the payment process easier, click here {payment_link} to ' \
                #               f'complete the payment of Rs {amount}/- from anywhere you are.'
                #     sms = send_sms(MobileNumber, message, '', sender)

                #     if sms['result']:
                #         if sms['result'].get('status') == "OK":
                #             send_status = True
                #     else:
                #         error_msg = 'Failed to send payment link please contact adminstrator'

            else:
                error_msg = 'Payment has already been received for this order'
                #error_msg = 'Payment is already received for this order'
                

                
                # success_msg = 'Payment is already received for this order'
                # final_data = generate_final_data('SUCCESS', success_msg)

        except Exception as e:
            error_logger(f'Route: {request.path}').error(e)

        

        if send_status or updated:
            final_data = generate_final_data('SUCCESS')
            final_data['result'] = payment_link
        
        else:
            final_data = generate_final_data('FAILED',error_msg)

    else:
        # Form validation error.
        final_data = generate_final_data('FORM_ERROR')
        final_data['errors'] = populate_errors(payment_link_form.errors)
    log_data = {
        'final_data': final_data
    }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))
    return final_data
