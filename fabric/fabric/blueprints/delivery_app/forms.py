from wtforms import StringField, IntegerField, Field, FloatField, BooleanField
from wtforms.validators import InputRequired, Length, Optional, NumberRange
from .validators import validate_latitude, validate_longitude, validate_otp_types, validate_hanger_instruction_actions, \
    validate_sorting_method, validate_gender, validate_email, validate_payment_collection, validate_complaint_list, \
    validate_day_interval, validate_activities, validate_address_details, validate_photo_types, validate_rewash_complaint_list, validate_final_rewash_list
from flask_wtf import FlaskForm


class ListField(Field):
    """
    A custom WTF field for accepting array of data.
    """

    def process_formdata(self, valuelist):
        self.data = valuelist

class CheckOpenPickupsForm(FlaskForm):
    """
    WTF form class for validating the add_order_garment_photo API request.
    """

    class Meta:
        csrf = False

    CustomerCode = StringField('CustomerCode', validators=[InputRequired()])
    PickupDate = StringField('PickupDate', validators=[InputRequired()])
    BranchCode = StringField('BranchCode', validators=[InputRequired()])
    CustomerName = StringField('CustomerName', validators=[InputRequired()])
    MobileNumber = StringField('MobileNumber', validators=[InputRequired()])
# Edited by MMM
class CheckPaymentStatusForm(FlaskForm):
    """
    WTF form class for validating the add_order_garment_photo API request.
    """

    class Meta:
        csrf = False

    TRNNo = StringField('TRNNo', validators=[InputRequired()])


class SaleRequestForm(FlaskForm):
    """
    WTF form class for validating the add_order_garment_photo API request.
    """

    class Meta:
        csrf = False

    TRNNo = StringField('TRNNo', validators=[InputRequired()])
    force_pay = BooleanField('force_pay', validators=[Optional()], false_values=(False, 'false', 0, '0'))
    EGRN = StringField('TRNNo', validators=[InputRequired()])
    CustomerCode = StringField('CustomerCode', validators=[InputRequired()])


class DUserProPicForm(FlaskForm):
    """
    WTF form class for validating the add_order_garment_photo API request.
    """

    class Meta:
        csrf = False

    b64_image = StringField('b64_image', validators=[InputRequired()])


class RankForm(FlaskForm):
    """
    WTF form class for validating get_rank_list
    """

    class Meta:
        csrf = False

    sort_by = StringField('sort_by', validators=[InputRequired()])


class DarningForm(FlaskForm):
    """
    WTF form class for checking discount code is valid or not
    """

    class Meta:
        csrf = False

    order_garment_id = IntegerField('order_garment_id', validators=[InputRequired()])
    length = FloatField('length', validators=[Optional()])


class DuserAttendanceDeleteForm(FlaskForm):
    """
    WTF form class for validating set_d_user_daily_branch API request
    """

    class Meta:
        csrf = False

    d_user_id = IntegerField('d_user_id', validators=[InputRequired()])
    delete_d_user_branches = BooleanField('delete_d_user_branches', validators=[Optional()],
                                          false_values=(False, 'false', 0, '0'))


class DUserDailyBranchForm(FlaskForm):
    """
    WTF form class for validating set_d_user_daily_branch API request
    """

    class Meta:
        csrf = False

    branch_codes = ListField('branch_codes', validators=[Optional()])


class CheckDiscountCodeForm(FlaskForm):
    """
    WTF form class for checking discount code is valid or not
    """

    class Meta:
        csrf = False

    discount_code = StringField('discount_code', validators=[InputRequired()])
    branch_code = StringField('branch_code', validators=[InputRequired()])
    customer_code = StringField('customer_code', validators=[InputRequired()])


class PushNotificationForm(FlaskForm):
    """
    WTF form class for validating the clock_in API request.
    """

    class Meta:
        csrf = False

    page = IntegerField('page', validators=[InputRequired()])


class MakeReadReadNotificationForm(FlaskForm):
    """
    WTF form class for validating the make_read_notifications API request.
    """

    class Meta:
        csrf = False

    notification_id = IntegerField('notification_id', validators=[Optional()])
    is_read = BooleanField('is_read', validators=[Optional()], false_values=(False, 'false', 0, '0'))


class NotifyForm(FlaskForm):
    """
    Notify  form class for validating popup notification fields
    """

    class Meta:
        csrf = False

    d_userid = IntegerField('d_userid', validators=[InputRequired()])
    title = StringField('title', validators=[InputRequired()])
    message = StringField('message', validators=[InputRequired()])
    image_url = StringField('image_url', validators=[Optional()])


class LoginForm(FlaskForm):
    """
    WTF form class for validating the login API request.
    """

    class Meta:
        csrf = False

    mobile_number = StringField('mobile_number', validators=[InputRequired(), Length(min=10, max=10,
                                                                                     message="Minimum 10 characters are needed"), ])

    password = StringField('password', validators=[InputRequired()])
    force_login = BooleanField('force_login', validators=[Optional()], false_values=(False, 'false', 0, '0'))


class ClockInForm(FlaskForm):
    """
    WTF form class for validating the clock_in API request.
    """

    class Meta:
        csrf = False

    lat = FloatField('lat', validators=[Optional(), validate_latitude])
    long = FloatField('long', validators=[Optional(), validate_longitude])


class ClockOutForm(FlaskForm):
    """
    WTF form class for validating the clock_out API request.
    """

    class Meta:
        csrf = False

    lat = FloatField('lat', validators=[Optional(), validate_latitude])
    long = FloatField('long', validators=[Optional(), validate_longitude])


class HomeForm(FlaskForm):
    """
    WTF form class for validating the home API request.
    """

    class Meta:
        csrf = False

    branch_codes = ListField('branch_codes', validators=[Optional()])


# Edited by MMM
class FcmForm(FlaskForm):
    """
    FcmForm form class for validating fcm token
    """

    class Meta:
        csrf = False

    fcm_token = StringField('fcm_token', validators=[Optional()])
    app_version = StringField('app_version', validators=[Optional()])
    build_number = IntegerField('build_number', validators=[Optional()])

    # Edited by MMM


class ActivityListForm(FlaskForm):
    """
    WTF form class for validating the get_activity_list API request.
    """

    class Meta:
        csrf = False

    branch_codes = ListField('branch_codes', validators=[Optional()])
    sorting_method = StringField('sorting_method', validators=[InputRequired(), validate_sorting_method])
    lat = FloatField('lat', validators=[Optional(), validate_latitude])
    long = FloatField('long', validators=[Optional(), validate_longitude])
    only_tomorrow = BooleanField('only_tomorrow', validators=[Optional()], false_values=(False, 'false', 0, '0'))
    all_branch = BooleanField('all_branch', validators=[Optional()], false_values=(False, 'false', 0, '0'))
    delivery_type = StringField('delivery_type', validators=[Optional()])
    payment_status = StringField('payment_status', validators=[Optional()])


# class CancelPickupForm(FlaskForm):
#     """
#     WTF form class for validating the cancel_pickup API request.
#     """

#     class Meta:
#         csrf = False

#     pickup_request_id = IntegerField('pickup_request_id', validators=[InputRequired()])
#     cancel_reason_id = IntegerField('cancel_reason_id', validators=[InputRequired()])
#     lat = FloatField('lat', validators=[Optional(), validate_latitude])
#     long = FloatField('long', validators=[Optional(), validate_longitude])

class CancelPickupForm(FlaskForm):
    """
    WTF form class for validating the cancel_pickup API request.
    """

    class Meta:
        csrf = False

    BookingId = IntegerField('BookingId', validators=[InputRequired()])
    POSId = IntegerField('POSId', validators=[InputRequired()])
    lat = FloatField('lat', validators=[Optional(), validate_latitude])
    long = FloatField('long', validators=[Optional(), validate_longitude])
    BranchCode = StringField('BranchCode', validators=[Optional()])
    CustomerName = StringField('CustomerName', validators=[InputRequired()])
    MobileNumber = StringField('MobileNumber', validators=[InputRequired()])
    Remarks = StringField('Remarks', validators=[Optional()])

class ReschedulePickupForm(FlaskForm):
    """
    WTF form class for validating the reschedule_pickup API request.
    """
    class Meta:
        csrf = False
    BookingId = IntegerField('BookingId', validators=[InputRequired()])
    POSId = IntegerField('POSId', validators=[Optional()])
    ReschuduleDate = StringField('ReschuduleDate', validators=[InputRequired()])
    BranchCode = StringField('BranchCode', validators=[Optional()])
    PickupTimeSlotId = IntegerField('PickupTimeSlotId', validators=[InputRequired()])
    lat = FloatField('lat', validators=[Optional(), validate_latitude])
    long = FloatField('long', validators=[Optional(), validate_longitude])
    ServiceTatId = IntegerField('ServiceTatId', validators=[Optional()])
    TimeSlotFrom = StringField('TimeSlotFrom', validators=[InputRequired()])
    TimeSlotTo = StringField('TimeSlotTo', validators=[InputRequired()])
    CustomerName = StringField('CustomerName', validators=[InputRequired()])
    MobileNumber = StringField('MobileNumber', validators=[InputRequired()])
    Remarks =  StringField('Remarks', validators=[Optional()])


# class ReschedulePickupForm(FlaskForm):
#     """
#     WTF form class for validating the reschedule_pickup API request.
#     """

#     class Meta:
#         csrf = False

#     pickup_request_id = IntegerField('pickup_request_id', validators=[InputRequired()])
#     reschedule_reason_id = IntegerField('cancel_reason_id', validators=[InputRequired()])
#     rescheduled_date = StringField('rescheduled_date', validators=[InputRequired()])
#     branch_code = StringField('branch_code', validators=[Optional()])
#     time_slot_id = IntegerField('time_slot_id', validators=[InputRequired()])
#     lat = FloatField('lat', validators=[Optional(), validate_latitude])
#     long = FloatField('long', validators=[Optional(), validate_longitude])
#     discount_code = StringField('discount_code', validators=[Optional()])
#     service_tat_id = IntegerField('service_tat_id', validators=[Optional()])


class RescheduleDeliveryForm(FlaskForm):
    """
    WTF form class for validating the reschedule_delivery API request.
    """

    class Meta:
        csrf = False

    CustomerCode = StringField('CustomerCode', validators=[InputRequired()])
    CustomerName = StringField('CustomerName', validators=[InputRequired()])
    MobileNo = StringField('CustomerName', validators=[InputRequired()])
    TimeSlotId = IntegerField('TimeSlotId', validators=[InputRequired()])
    TimeSlotFrom = StringField('CustomerName', validators=[InputRequired()])
    TimeSlotTo = StringField('CustomerName', validators=[InputRequired()])
    RescheduleDate = StringField('RescheduleDate', validators=[InputRequired()])
    RescheduleReasonId = IntegerField('TimeSlotId', validators=[InputRequired()])
    EGRN = StringField('EGRN', validators=[InputRequired()])
    BranchCode = StringField('BranchCode', validators=[InputRequired()])
    TRNNo = StringField('TRNNo', validators=[InputRequired()])


class GetPickupTimeslotsForm(FlaskForm):
    """
    WTF form class for validating the get_pickup_time_slots API request.
    """

    class Meta:
        csrf = False

    branch_code = StringField('branch_code', validators=[InputRequired()])
    today = BooleanField('today', validators=[Optional()], false_values=(False, 'false', 0, '0'))


class PendingPickupDetailsForm(FlaskForm):
    """
    WTF form class for validating the get_pending_pickup_details API request.
    """

    class Meta:
        csrf = False

    BookingId = StringField('BookingId', validators=[InputRequired()])


class GetGarmentsForm(FlaskForm):
    """
    WTF form class for validating the get_garments API request.
    """

    class Meta:
        csrf = False

    branch_code = StringField('branch_code', validators=[InputRequired()])
    service_tat_id = IntegerField('service_tat_id', validators=[InputRequired()])
    service_type_id = IntegerField('service_type_id', validators=[InputRequired()])


class GetOrderGarmentsForm(FlaskForm):
    """
    WTF form class for validating the get_order_garments API request.
    """

    class Meta:
        csrf = False

    BookingId = IntegerField('BookingId', validators=[InputRequired()])
    ServiceTatId = IntegerField('ServiceTatId', validators=[Optional()])


# class AddOrderGarmentsForm(FlaskForm):
#     """
#     WTF form class for validating the add_order_garments API request.
#     """

#     class Meta:
#         csrf = False

#     pickup_request_id = IntegerField('pickup_request_id', validators=[InputRequired()])
#     service_tat_id = IntegerField('service_tat_id', validators=[InputRequired()])
#     service_type_id = IntegerField('service_type_id', validators=[InputRequired()])
#     garments = ListField('garments', validators=[InputRequired()])
    
class AddOrderGarmentsForm(FlaskForm):
    """
    WTF form class for validating the add_order_garments API request.
    """
    class Meta:
        csrf = False

    BookingId = IntegerField('BookingId', validators=[InputRequired()])
    Garments = ListField('Garments', validators=[InputRequired()])
    service_tat_id = IntegerField('service_tat_id', validators=[InputRequired()])
    service_type_id = IntegerField('service_type_id', validators=[InputRequired()])

class RemoveOrderGarmentForm(FlaskForm):
    """
    WTF form class for validating the remove_order_garment API request.
    """

    class Meta:
        csrf = False

    OrderGarmentID = StringField('OrderGarmentID', validators=[InputRequired()])


class SaveOrderGarmentInstructionForm(FlaskForm):
    """
    WTF form class for validating the save_order_garment_instruction API request.
    """

    class Meta:
        csrf = False
        
    order_garment_id = StringField('order_garment_id', validators=[InputRequired()])
    instruction_id = IntegerField('instruction_id', validators=[InputRequired()])
    BookingID = IntegerField('BookingID', validators=[Optional()])


class SaveOrderGarmentIssueForm(FlaskForm):
    """
    WTF form class for validating the save_order_garment_issue API request.
    """

    class Meta:
        csrf = False
    order_garment_id = StringField('order_garment_id', validators=[InputRequired()])
    issue_id = IntegerField('issue_id', validators=[InputRequired()])
    BookingID = IntegerField('instruction_id', validators=[Optional()])


class AddOrderGarmentPhotoForm(FlaskForm):
    """
    WTF form class for validating the add_order_garment_photo API request.
    """

    class Meta:
        csrf = False

    BookingId = IntegerField('BookingId', validators=[Optional()])
    order_garment_id = StringField('order_garment_id', validators=[InputRequired()])
    b64_image = StringField('b64_image', validators=[InputRequired()])
    photo_type = StringField('photo_type', validators=[Optional(), validate_photo_types])
    photo_date = StringField('photo_date', validators=[Optional()])


class RemoveOrderGarmentPhotoForm(FlaskForm):
    """
    WTF form class for validating the remove_order_garment_photo API request.
    """

    class Meta:
        csrf = False

    photo_id = IntegerField('photo_id', validators=[InputRequired()])


class UpdateOrderGarmentServiceTypeForm(FlaskForm):
    """
    WTF form class for validating the update_order_garment_service_type API request.
    """

    class Meta:
        csrf = False

    order_garment_id = StringField('order_garment_id', validators=[InputRequired()])
    service_type_id = IntegerField('service_type_id', validators=[InputRequired()])


class UpdateHangerInstructionsForm(FlaskForm):
    """
    WTF form class for validating the update_hanger_instructions API request.
    """

    class Meta:
        csrf = False

    BookingId = IntegerField('BookingId', validators=[InputRequired()])
    garment_id = IntegerField('garment_id', validators=[InputRequired()])
    action = StringField('action', validators=[InputRequired(), validate_hanger_instruction_actions])


# class FinalizeOrderForm(FlaskForm):
#     """
#     WTF form class for validating the finalize_order API request.
#     """

#     class Meta:
#         csrf = False

#     order_id = IntegerField('order_id', validators=[InputRequired()])
#     discount_code = StringField('discount_code', validators=[Optional()])
#     coupon_code = StringField('coupon_code', validators=[Optional()])
#     remarks = StringField('remarks', validators=[Optional()])
#     lat = FloatField('lat', validators=[Optional(), validate_latitude])
#     long = FloatField('long', validators=[Optional(), validate_longitude])
#     delivery_charge = BooleanField('delivery_charge', validators=[Optional()])

class FinalizeOrderForm(FlaskForm):
    """
    WTF form class for validating the finalize_order API request.
    """

    class Meta:
        csrf = False
    DiscountCode = StringField('DiscountCode', validators=[Optional()])
    CouponCode = StringField('CouponCode', validators=[Optional()])
    remarks = StringField('remarks', validators=[Optional()])
    Duserlat = FloatField('Duserlat', validators=[InputRequired(), validate_latitude])
    Duserlong = FloatField('Duserlong', validators=[InputRequired(), validate_longitude])
    CustLat = FloatField('CustLat', validators=[InputRequired()])
    CustLong = FloatField('CustLong', validators=[InputRequired()])
    # CustLat = FloatField('CustLat', validators=[InputRequired(), validate_latitude])
    # CustLong = FloatField('CustLong', validators=[InputRequired(), validate_latitude])
    delivery_charge = BooleanField('delivery_charge', validators=[Optional()])
    PickupId = StringField('PickupID', validators=[Optional()])
    IsExistOrderID = IntegerField('IsExistOrderID', validators=[Optional()])
    BookingId = IntegerField('BookingId', validators=[Optional()])
    BranchCode = StringField('BranchCode', validators=[Optional()])
    CustomerCode = StringField('CustomerCode', validators=[Optional()])
    BasicAmount = FloatField('BasicAmount', validators=[Optional()])
    Garments = ListField('Garments', validators=[Optional()])
    CustAddressId = IntegerField('CustAddressId', validators=[Optional()])
    PickupDate = StringField('PickupDate', validators=[Optional()])
    GarmentCount = IntegerField('GarmentCount', validators=[Optional()])
    IsERCoupon = IntegerField('IsERCoupon', validators=[Optional()])
    ERRequestId = IntegerField('ERRequestId', validators=[Optional()])
    CodeFromER = StringField('CodeFromER', validators=[Optional()])
    ServiceTaxAmount = FloatField('ServiceTaxAmount', validators=[Optional()])
    EstimatedAmount = FloatField('EstimatedAmount', validators=[Optional()])
    OrderTypeId = IntegerField('OrderTypeId', validators=[Optional()])
    DiscountAmt = FloatField('DiscountAmt', validators=[Optional()])
    AddressType = StringField('AddressType', validators=[Optional()])




class SaveOrderReviewForm(FlaskForm):
    """
    WTF form class for validating the save_order_review API request.
    """

    class Meta:
        csrf = False

    BookingID = StringField('BookingID', validators=[InputRequired()])
    rating = IntegerField('rating', validators=[InputRequired(),
                                                NumberRange(min=1, max=5, message="Rating must be between 1 and 5.")])
    review_reason_id = IntegerField('review_reason_id', validators=[Optional()])
    remarks = StringField('remarks', validators=[Optional()])

class SaveDeliveryReviewForm(FlaskForm):
    """
    WTF form class for validating the save_order_review API request.
    """

    class Meta:
        csrf = False

    TRNNo = StringField('TRNNo', validators=[InputRequired()])
    rating = IntegerField('rating', validators=[InputRequired(),
                                                NumberRange(min=1, max=5, message="Rating must be between 1 and 5.")])
    review_reason_id = IntegerField('review_reason_id', validators=[Optional()])
    remarks = StringField('remarks', validators=[Optional()])


class PendingDeliveryDetailsForm(FlaskForm):
    """
    WTF form class for validating the get_pending_delivery_details API request.
    """

    class Meta:
        csrf = False

    TRNNo = StringField('TRNNo', validators=[InputRequired()])
    BranchCode = StringField('BranchCode', validators=[InputRequired()])


class GetDeliveryGarmentsForm(FlaskForm):
    """
    WTF form class for validating the get_delivery_garments API request.
    """

    class Meta:
        csrf = False
    TRNNo = StringField('TRNNo', validators=[InputRequired()])
    EGRN = StringField('EGRN', validators=[InputRequired()])


class GetGarmentDetailsForm(FlaskForm):
    """
    WTF form class for validating the get_garment_details API request.
    """

    class Meta:
        csrf = False

    order_garment_id = StringField('order_garment_id', validators=[InputRequired()])


class SaveGPSCordsForm(FlaskForm):
    """
    WTF form class for validating the save_gps_cords API request.
    """

    class Meta:
        csrf = False

    address_id = IntegerField('address_id', validators=[InputRequired()])
    lat = FloatField('lat', validators=[InputRequired(), validate_latitude])
    long = FloatField('long', validators=[InputRequired(), validate_longitude])


class UpdateCustomerAddressForm(FlaskForm):
    """
    WTF form class for validating the update_customer_address API request.
    """

    class Meta:
        csrf = False

    address_id = IntegerField('address_id', validators=[Optional()])
    address_line_1 = StringField('address_line_1', validators=[InputRequired()])
    address_line_2 = StringField('address_line_2', validators=[Optional()])
    address_line_3 = StringField('address_line_3', validators=[Optional()])
    landmark = StringField('landmark', validators=[Optional()])
    pincode = IntegerField('pincode', validators=[Optional()])
    lat = FloatField('lat', validators=[InputRequired(), validate_latitude])
    long = FloatField('long', validators=[InputRequired(), validate_longitude])
    delivery_user_branch_code = StringField('delivery_user_branch_code', validators=[Optional()])
    mobile_number = StringField('mobile_number', validators=[Optional()])
    customer_type = StringField('customer_type', validators=[Optional()])
    address_name = StringField('address_name', validators=[Optional()])
    geo_location = StringField('geo_location', validators=[Optional()])
    delivery_request_id = IntegerField('delivery_request_id', validators=[Optional()])
    BookingId = IntegerField('BookingId', validators=[Optional()])
    AddressType = StringField('address_type', validators=[Optional()])
    CustomerCode = StringField('CustomerCode', validators=[Optional()])
    TRNNo = StringField('TRNNo', validators=[Optional()])


class ValidateDiscountCodeForm(FlaskForm):
    """
    WTF form class for validating the validate_discount_code API request.
    """

    class Meta:
        csrf = False

    BookingId = IntegerField('BookingId', validators=[InputRequired()])
    discount_code = StringField('discount_code', validators=[Optional()])
    CustomerCode = StringField('CustomerCode', validators=[Optional()])
    BranchCode = StringField('BranchCode', validators=[Optional()])
    source = StringField('source', validators=[Optional()])


class ValidateCouponCodeForm(FlaskForm):
    """
    WTF form class for validating the validate_coupon_code API request.
    """

    class Meta:
        csrf = False

    coupon_code = StringField('coupon_code', validators=[Optional()])
    BookingId = IntegerField('BookingId', validators=[Optional()])
    BranchCode = StringField('branch_code', validators=[Optional()])
    CustomerCode = StringField('customer_code', validators=[Optional()])
    source = StringField('source', validators=[Optional()])


class SendOTPForm(FlaskForm):
    """
    WTF form class for validating the send_otp API request.
    """

    class Meta:
        csrf = False

    mobile_number = StringField('mobile_number', validators=[InputRequired(), Length(min=10, max=10,
                                                                                     message="Minimum 10 characters are needed"), ])
    otp_type = StringField('otp_type', validators=[Optional(), validate_otp_types])

    person = StringField('person', validators=[Optional()])

    otp = IntegerField('otp', validators=[Optional()])

    branch_code = StringField('branch_code', validators=[Optional()])
    TRNNo = StringField('TRNNo', validators=[Optional()])
    IsAlterNumber = BooleanField('IsAlterNumber', validators=[Optional()])


class VerifyOTPForm(FlaskForm):
    """
    WTF form class for validating the verify_otp API request.
    """

    class Meta:
        csrf = False

    mobile_number = StringField('mobile_number', validators=[InputRequired(), Length(min=10, max=10,
                                                                                     message="Minimum 10 characters are needed"), ])
    otp = IntegerField('otp', validators=[InputRequired()])
    otp_verify = BooleanField('otp_verify', validators=[Optional()], false_values=(False, 'false', 0, '0'))

class CreateAdhocPickupForm(FlaskForm):
    """
    WTF form class for validating the create_adhoc_pickup_request API request.
    """
    class Meta:
        csrf = False
    MobileNumber = StringField('MobileNumber', validators=[InputRequired(), Length(min=10, max=10,
                                                                                     message="Minimum 10 characters are needed"), ])
    PickupDate = StringField('PickupDate', validators=[InputRequired()])
    BranchCode = StringField('BranchCode', validators=[InputRequired()])
    CustomerCode = StringField('CustomerCode', validators=[Optional()])
    PickupTimeSlotId = IntegerField('PickupTimeSlotId', validators=[InputRequired()])
    ServiceTatId = IntegerField('ServiceTatId', validators=[InputRequired()])
    Lattitude = FloatField('Lattitude', validators=[InputRequired(), validate_latitude])
    Longitude = FloatField('Longitude', validators=[InputRequired(), validate_longitude])
    GeoLocation = StringField('GeoLocation', validators=[Optional()])
    TimeSlotFrom = StringField('TimeSlotFrom', validators=[Optional()])
    TimeSlotTo = StringField('TimeSlotTo', validators=[Optional()])
    Adhoccoupon = StringField('Adhoccoupon', validators=[Optional()])
    PinCode = IntegerField('PinCode', validators=[Optional()])
    DiscountCode = StringField('DiscountCode', validators=[Optional()])
    AddressType = StringField('AddressType', validators=[Optional()])
    ValidateDiscountCode = StringField('ValidateDiscountCode', validators=[Optional()])
    AddressLine1 = StringField('AddressLine1', validators=[Optional()])
    AddressLine2 = StringField('AddressLine2', validators=[Optional()])
    AddressLine3 = StringField('AddressLine3', validators=[Optional()])
    AddressName = StringField('AddressName', validators=[Optional()])
    CustomerName = StringField('CustomerName', validators=[Optional()])
    service_type_id = IntegerField('service_type_id', validators=[Optional()])

# class CreateAdhocPickupForm(FlaskForm):
#     """
#     WTF form class for validating the create_adhoc_pickup_request API request.
#     """

#     class Meta:
#         csrf = False

#     mobile_number = StringField('mobile_number', validators=[InputRequired(), Length(min=10, max=10,
#                                                                                      message="Minimum 10 characters are needed"), ])
#     address_id = IntegerField('address_id', validators=[InputRequired()])
#     pickup_date = StringField('pickup_date', validators=[InputRequired()])
#     branch_code = StringField('branch_code', validators=[InputRequired()])
#     time_slot_id = IntegerField('time_slot_id', validators=[InputRequired()])
#     #     Edited by MMM
#     discount_code = StringField('discount_code', validators=[Optional()])
#     #     Edited by MMM
#     #     Edited by Athira
#     service_tat_id = IntegerField('service_tat_id', validators=[InputRequired()])
#     lat = FloatField('lat', validators=[InputRequired(), validate_latitude])
#     long = FloatField('long', validators=[InputRequired(), validate_longitude])
#     geo_location = StringField('geo_location', validators=[Optional()])


class AddAddressForm(FlaskForm):
    """
    WTF form class for validating the add_address API request.
    """

    class Meta:
        csrf = False

    CustomerCode = StringField('CustomerCode', validators=[InputRequired()])
    address_line_1 = StringField('address_line_1', validators=[InputRequired()])
    address_line_2 = StringField('address_line_2', validators=[Optional()])
    address_line_3 = StringField('address_line_3', validators=[Optional()])
    landmark = StringField('landmark', validators=[Optional()])
    address_type = StringField('address_type', validators=[Optional()])
    pincode = IntegerField('pincode', validators=[Optional()])
    lat = FloatField('lat', validators=[InputRequired(), validate_latitude])
    long = FloatField('long', validators=[InputRequired(), validate_longitude])
    delivery_user_branch_code = StringField('delivery_user_branch_code', validators=[Optional()])
    mobile_number = StringField('mobile_number', validators=[Optional()])
    customer_type = StringField('customer_type', validators=[Optional()])
    address_name = StringField('address_name', validators=[Optional()])
    geo_location = StringField('geo_location', validators=[Optional()])
    BookingID = StringField('BookingID', validators=[Optional()])
    TRNNo = StringField('TRNNo', validators=[Optional()])


class CheckCustomerForm(FlaskForm):
    """
    WTF form class for validating the check_customer API request.
    """

    class Meta:
        csrf = False

    mobile_number = StringField('mobile_number', validators=[InputRequired(), Length(min=10, max=10,
                                                                                     message="Minimum 10 characters are needed"), ])
    # Edited by MMM
    branch_code = StringField('branch_code', validators=[Optional()])
    # Edited by MMM


class SaveCustomerForm(FlaskForm):
    """
    WTF form class for validating the save_customer API request.
    """

    class Meta:
        csrf = False

    mobile_number = StringField('mobile_number', validators=[InputRequired(), Length(min=10, max=10,
                                                                                     message="Minimum 10 characters are needed"), ])

    customer_name = StringField('customer_name', validators=[InputRequired(), Length(min=2)])
    customer_code = StringField('customer_code', validators=[Optional()])
    email = StringField('email', validators=[Optional()])
    gender = StringField('gender', validators=[InputRequired(), validate_gender])
    delivery_user_branch_code = StringField('delivery_user_branch_code', validators=[InputRequired()])
    address_details = ListField('address', validators=[InputRequired(), validate_address_details])


class GetCouponCodesForm(FlaskForm):
    """
    WTF form class for validating the get_coupon_codes API request.
    """

    class Meta:
        csrf = False

    EGRN = StringField('EGRN', validators=[InputRequired()])





class CheckOrderPaymentStatusForm(FlaskForm):
    """
    WTF form class for validating the check_order_payment_status API request.
    """

    class Meta:
        csrf = False

    TRNNo = StringField('TRNNo', validators=[InputRequired()])
    EGRN = StringField('EGRN', validators=[InputRequired()])
    QrId = StringField('QrId', validators=[Optional()])

class AddComplaintForm1(FlaskForm):
    """
    WTF form class for validating the add_complaint API request.
    """

    class Meta:
        csrf = False

    CustomerCode = StringField('CustomerCode', validators=[InputRequired()])
    EGRN = StringField('EGRN', validators=[InputRequired()])
    complaint_garment_list = ListField('complaint_garment_list', validators=[InputRequired(), validate_complaint_list])
    BranchCode = StringField('BranchCode', validators=[InputRequired()])
    TRNNo = StringField('TRNNo', validators=[Optional()])
    TagNo = ListField('TagNo', validators=[Optional()])
    CustomerName = StringField('CustomerName', validators=[Optional()])
    MobileNo = StringField('MobileNo', validators=[Optional()])
    Duserlat = FloatField('Duserlat', validators=[Optional()])
    Duserlong = FloatField('Duserlong', validators=[Optional()])
    CustLat = FloatField('CustLat', validators=[Optional()])
    CustLong = FloatField('CustLong', validators=[Optional()])



class AddComplaintForm(FlaskForm):
    """
    WTF form class for validating the add_complaint API request.
    """

    class Meta:
        csrf = False

    CustomerCode = StringField('CustomerCode', validators=[InputRequired()])
    EGRN = StringField('EGRN', validators=[InputRequired()])
    complaint_garment_list = ListField('complaint_garment_list', validators=[InputRequired(), validate_complaint_list])
    BranchCode = StringField('BranchCode', validators=[InputRequired()])
    TRNNo = StringField('TRNNo', validators=[Optional()])
    TagNo = ListField('TagNo', validators=[Optional()])
    CustomerName = StringField('CustomerName', validators=[Optional()])
    MobileNo = StringField('MobileNo', validators=[Optional()])
    Duserlat = FloatField('Duserlat', validators=[Optional()])
    Duserlong = FloatField('Duserlong', validators=[Optional()])
    CustLat = FloatField('CustLat', validators=[Optional()])
    CustLong = FloatField('CustLong', validators=[Optional()])


class MakePaymentForm(FlaskForm):
    """
    WTF form class for validating the make_payment API request.
    """

    class Meta:
        csrf = False

    OrderID = StringField('OrderID', validators=[InputRequired()])
    MonthlyCustomer = BooleanField('MonthlyCustomer', validators=[Optional()], false_values=(False, 'false', 0, '0'))
    TRNNo = StringField('TRNNo', validators=[InputRequired()])
    EGRN = StringField('EGRN', validators=[InputRequired()])
    CustomerCode = StringField('CustomerCode', validators=[InputRequired()])
    BranchCode = StringField('CustomerCode', validators=[InputRequired()])
    MobileNo = StringField('MobileNo', validators=[InputRequired()])
    collected = ListField('collected', validators=[Optional(), validate_payment_collection])
    coupons = ListField('coupons', validators=[Optional()])
    lp = BooleanField('lp', validators=[Optional()], false_values=(False, 'false', 0, '0'))
    trn = BooleanField('trn', validators=[Optional()], false_values=(False, 'false', 0, '0'))


class MakeDelivery(FlaskForm):
    """
    WTF form class for validating the make_delivery API request.
    """

    class Meta:
        csrf = False

    lat = FloatField('lat', validators=[Optional(), validate_latitude])
    long = FloatField('long', validators=[Optional(), validate_longitude])
    DeliveryWithoutOtp = BooleanField('DeliveryWithoutOtp', validators=[Optional()], false_values=(False, 'false', 0, '0'))
    DeliverWithoutPayment = BooleanField('DeliverWithoutPayment', validators=[Optional()], false_values=(False, 'false', 0, '0'))
    ReasonList = ListField('ReasonList', validators=[Optional()])
    TRNNo = StringField('TRNNo', validators=[Optional()])
    EGRN = StringField('EGRN', validators=[Optional()])
    CustLat = FloatField('CustLat', validators=[Optional(), validate_latitude])
    CustLong = FloatField('CustLong', validators=[Optional(), validate_latitude])
    CustomerName = StringField('CustomerName', validators=[Optional()])
    MobileNumber = StringField('MobileNumber', validators=[Optional()])
    CustomerCode = StringField('CustomerCode', validators=[Optional()])
    BranchCode = StringField('BranchCode', validators=[Optional()])
    BookingId = IntegerField('BookingId', validators=[Optional()])
    Remarks = StringField('Remarks', validators=[Optional()])

    # delivery_request_id = IntegerField('delivery_request_id', validators=[InputRequired()])
    # lat = FloatField('lat', validators=[Optional(), validate_latitude])
    # long = FloatField('long', validators=[Optional(), validate_longitude])
    # DeliveryWithoutOtp = BooleanField('DeliveryWithoutOtp', validators=[Optional()], false_values=(False, 'false', 0, '0'))
    # DeliverWithoutPayment = BooleanField('DeliverWithoutPayment', validators=[Optional()], false_values=(False, 'false', 0, '0'))
    # ReasonList = ListField('ReasonList', validators=[Optional()])


class RewashGarmentForm(FlaskForm):
    """
    WTF form class for validating the rewash_garment API request.
    """

    class Meta:
        csrf = False

    order_garment_id = IntegerField('order_garment_id', validators=[InputRequired()])


class GetOrderGarmentsPriceForm(FlaskForm):
    """
    WTF form class for validating the get_order_garments_price API request.
    """

    class Meta:
        csrf = False

    BookingId = IntegerField('BookingId', validators=[InputRequired()])


class GetCompletedActivitiesForm(FlaskForm):
    """
    WTF form class for validating the get_completed_activities API request.
    """

    class Meta:
        csrf = False

    branch_codes = ListField('branch_codes', validators=[Optional()])
    day_interval = IntegerField('day_interval', validators=[Optional(), validate_day_interval])
    filter_type = StringField('filter_type', validators=[Optional()])
    completed_only = BooleanField('unassigned_only', validators=[Optional()], false_values=(False, 'false', 0, '0'))


class GetLPForm(FlaskForm):
    """
    WTF form class for validating the get_lp API request.
    """

    class Meta:
        csrf = False

    customer_code = StringField('customer_code', validators=[InputRequired()])
    egrn = StringField('egrn', validators=[InputRequired()])


class SaveGPSPosition(FlaskForm):
    """
    WTF form class for validating the save_gps_position API request.
    """

    class Meta:
        csrf = False

    lat = FloatField('lat', validators=[InputRequired(), validate_latitude])
    long = FloatField('long', validators=[InputRequired(), validate_longitude])


class SendPaymentLinkForms(FlaskForm):
    """
    WTF form class for validating the send_payment_link API request.
    """

    class Meta:
        csrf = False

    EGRN = StringField('EGRN', validators=[InputRequired()])
    TRNNo = StringField('TRNNo', validators=[InputRequired()])
    CustomerCode = StringField('CustomerCode', validators=[InputRequired()])
    MobileNumber = StringField('MobileNumber', validators=[InputRequired(), Length(min=10, max=10,
                                                                                     message="Minimum 10 characters are needed"), ])

class SendPaymentLinkForm(FlaskForm):
    """
    WTF form class for validating the send_payment_link API request.
    """

    class Meta:
        csrf = False

    lat = FloatField('lat', validators=[Optional(), validate_latitude])
    long = FloatField('long', validators=[Optional(), validate_longitude])
    DeliveryWithoutOtp = BooleanField('DeliveryWithoutOtp', validators=[Optional()], false_values=(False, 'false', 0, '0'))
    DeliverWithoutPayment = BooleanField('DeliverWithoutPayment', validators=[Optional()], false_values=(False, 'false', 0, '0'))
    ReasonList = ListField('ReasonList', validators=[Optional()])
    CustLat = FloatField('CustLat', validators=[Optional(), validate_latitude])
    CustLong = FloatField('CustLong', validators=[Optional(), validate_latitude])
    CustomerName = StringField('CustomerName', validators=[Optional()])
 
    BranchCode = StringField('BranchCode', validators=[Optional()])
    BookingId = IntegerField('BookingId', validators=[Optional()])
    Remarks = StringField('Remarks', validators=[Optional()])

    EGRN = StringField('EGRN', validators=[InputRequired()])
    TRNNo = StringField('TRNNo', validators=[InputRequired()])
    CustomerCode = StringField('CustomerCode', validators=[InputRequired()])
    COUNT = StringField('COUNT', validators=[Optional()])
    MobileNumber = StringField('MobileNumber', validators=[InputRequired(), Length(min=10, max=10,
                                                                                     message="Minimum 10 characters are needed"), ])


class SendWaitingSMSForm(FlaskForm):
    """
    WTF form class for validating the send_waiting_sms API request.
    """

    class Meta:
        csrf = False

    mobile_number = StringField('mobile_number', validators=[InputRequired(), Length(min=10, max=10,
                                                                                     message="Minimum 10 characters are needed"), ])
    sms_template_id = IntegerField('sms_template_id', validators=[InputRequired()])
    lat = FloatField('lat', validators=[Optional(), validate_latitude])
    long = FloatField('long', validators=[Optional(), validate_longitude])
    customer_code = StringField('customer_code', validators=[Optional()])
    BookingIDString = StringField('BookingIDString', validators=[Optional()])
    activity_type = StringField('activity_type', validators=[Optional(), validate_activities])
    branch_code = StringField('branch_code', validators=[Optional()])
    TRNNo = StringField('branch_code', validators=[Optional()])



class CalculatePayableAmountForm(FlaskForm):
    """
    WTF form class for validating the calculate_payable_amount API request.
    """

    class Meta:
        csrf = False

    delivery_request_id = IntegerField('delivery_request_id', validators=[InputRequired()])
    order_id = IntegerField('order_id', validators=[InputRequired()])
    coupons = ListField('coupons', validators=[Optional()])
    lp = BooleanField('lp', validators=[Optional()], false_values=(False, 'false', 0, '0'))


class SaveRemarksForm(FlaskForm):
    """
    WTF form class for validating the save_remarks API request.
    """

    class Meta:
        csrf = False

    pickup_request_id = IntegerField('pickup_request_id', validators=[InputRequired()])
    remarks = StringField('remarks', validators=[InputRequired()])


class GetAvailableServiceTypesForm(FlaskForm):
    """
    WTF form class for validating the get_available_service_types API request.
    """

    class Meta:
        csrf = False

    branch_code = StringField('branch_code', validators=[Optional()])
    garment_id = IntegerField('garment_id', validators=[Optional()])


class UpdateGarmentMeasurementForm(FlaskForm):
    """
    WTF form class for validating the update_garment_measurement API request.
    """

    class Meta:
        csrf = False

    order_garment_id = StringField('order_garment_id', validators=[InputRequired()])
    length = FloatField('length', validators=[InputRequired()])
    width = FloatField('width', validators=[InputRequired()])


class GetServiceTatForm(FlaskForm):
    """
    WTF form class for validating the get_service_tat_id API request.
    """

    class Meta:
        csrf = False

    branch_code = StringField('branch_code', validators=[InputRequired()])


class GetTagDetailsForm(FlaskForm):
    """
    WTF form class for validating the get_tag_details API request.
    """

    class Meta:
        csrf = False

    tag_id = StringField('tag_id', validators=[InputRequired()])
    mobile_number = StringField('mobile_number', validators=[InputRequired()])
    branch_code = StringField('branch_code', validators=[InputRequired()])
    # EGRN = StringField('EGRN', validators=[InputRequired()])


class GetRecentOrdersForm(FlaskForm):
    """
    WTF form class for validating the get_recent_orders API request.
    """

    class Meta:
        csrf = False

    MobileNo = StringField('MobileNo', validators=[InputRequired()])
    CustomerCode = StringField('CustomerCode', validators=[InputRequired()])

class ReopenComplaintForm(FlaskForm):
    """
    WTF form class for validating the reopen_complaint API request.
    """

    class Meta:
        csrf = False

    tag_id = StringField('tag_id', validators=[InputRequired()])
    remarks = StringField('remarks', validators=[Optional()])
    complaint_type = StringField('complaint_type', validators=[Optional()])

class GarmentDetailsForm(FlaskForm):
    """
    WTF form class for validating the garment_details API request.
    """

    class Meta:
        csrf = False

    TagNo = ListField('TagNo', validators=[InputRequired()])
    EGRN = StringField('EGRN', validators=[Optional()])
    TRNNo = StringField('TRNNo', validators=[Optional()])

class AdhocRewashForm(FlaskForm):
    """
    WTF form class for validating the rewash API request.
    """

    class Meta:
        csrf = False

    # ServiceTypeId = StringField('customer_id', validators=[InputRequired()])
    # ServiceTatId = IntegerField('time_slot_id', validators=[InputRequired()])
    OLDEGRN = StringField('OLDEGRN', validators=[Optional()])
    BookingID = StringField('booking_id', validators=[Optional()])
    complaint_garment_list = ListField('complaint_garment_list',
                                       validators=[InputRequired()])
    # OrderGarmentID = StringField('OrderGarmentID', validators=[InputRequired()])

class FinalizeRewashForm(FlaskForm):
    """
    WTF form class for validating the finalize_rewash API request.
    """

    class Meta:
        csrf = False

    BookingId = StringField('BookingId', validators=[InputRequired()])

    # AmeyoTicketId = StringField('AmeyoTicketId', validators=[InputRequired()])
    GarmentsCount = StringField('GarmentsCount', validators=[Optional()])

    EGRN = StringField('EGRN', validators=[Optional()])
    final_rewash_list =  ListField('complaint_garment_list',
                                       validators=[InputRequired()])

    lat = FloatField('lat', validators=[Optional(), validate_latitude])
    long = FloatField('long', validators=[Optional(), validate_longitude])


class TagDetailsForm(FlaskForm):
    """
    WTF form class for validating the garment_details API request.
    """

    class Meta:
        csrf = False

    tag_id = ListField('tag_id', validators=[InputRequired()])

class VasDetailsForm(FlaskForm):
    """
    WTF form class for validating the get_selected_vas API request.
    """

    class Meta:
        csrf = False

    order_id = StringField('order_id', validators=[Optional()])
    order_garment_id = StringField('order_garment_id', validators=[InputRequired()])

class FutureDateRewashForm(FlaskForm):
    """
    WTF form class for validating the future_date_rewash API request.
    """

    class Meta:
        csrf = False

    
    MobileNumber = StringField('MobileNumber', validators=[InputRequired(), Length(min=10, max=10,
                                                                                   message="Minimum 10 characters are needed"), ])
    PickupDate = StringField('PickupDate', validators=[InputRequired()])
    BranchCode = StringField('BranchCode', validators=[InputRequired()])
    CustomerCode = StringField('CustomerCode', validators=[Optional()])
    PickupTimeSlotId = IntegerField('PickupTimeSlotId', validators=[InputRequired()])
    ServiceTatId = IntegerField('ServiceTatId', validators=[Optional()])
    Lattitude = FloatField('Lattitude', validators=[InputRequired(), validate_latitude])
    Longitude = FloatField('Longitude', validators=[InputRequired(), validate_longitude])
    GeoLocation = StringField('GeoLocation', validators=[Optional()])
    TimeSlotFrom = StringField('TimeSlotFrom', validators=[Optional()])
    TimeSlotTo = StringField('TimeSlotTo', validators=[Optional()])
    Adhoccoupon = StringField('Adhoccoupon', validators=[Optional()])
    PinCode = IntegerField('PinCode', validators=[Optional()])
    DiscountCode = StringField('DiscountCode', validators=[Optional()])
    AddressType = StringField('AddressType', validators=[Optional()])
    ValidateDiscountCode = StringField('ValidateDiscountCode', validators=[Optional()])
    AddressLine1 = StringField('AddressLine1', validators=[Optional()])
    AddressLine2 = StringField('AddressLine2', validators=[Optional()])
    AddressLine3 = StringField('AddressLine3', validators=[Optional()])
    AddressName = StringField('AddressName', validators=[Optional()])
    CustomerName = StringField('CustomerName', validators=[Optional()])

class CancelorReschedulePermissionForm(FlaskForm):
    """
    WTF form class for validating the CancelorReschedulePermissionForm API request.
    """

    class Meta:
        csrf = False

    permission_type = StringField("permission_type", validators=[InputRequired()])

class OpenPickupsForm(FlaskForm):
    """
    WTF form class for validating the get_open_pickups API request.
    """

    class Meta:
        csrf = False

    CustomerCode = StringField("CustomerCode", validators=[InputRequired()])
    pickup_date = StringField('pickup_date', validators=[InputRequired()])

class UpdateBranchForm(FlaskForm):
    """
    WTF form class for validating the updatebranchcode API request.
    """ 

    class Meta:
        csrf = False

    BranchCode = StringField('BranchCode', validators=[InputRequired()])
    BookingId = IntegerField('BookingId', validators=[InputRequired()])

class CheckOutStandingLimitForm(FlaskForm):
    """
    WTF form class for validating the check_out_standing_limit API request.
    """

    class Meta:
        csrf = False

    customer_code = StringField('customer_code', validators=[InputRequired()])


class GetPickupInstructionsForm(FlaskForm):

    class Meta:
        csrf = False

    BookingId = IntegerField('BookingId', validators=[InputRequired()])

class SmsForm(FlaskForm):
    """
    WTF form class for validating the validate_coupon_code API request.
    """

    class Meta:
        csrf = False
    branch_code = StringField('branch_code', validators=[Optional()])

class GenaretRazorPayQRCode(FlaskForm):
    class Meta:
        csrf = False

    TRNNo = StringField('TRNNo', validators=[InputRequired()])
    EGRN = StringField('EGRN', validators=[InputRequired()])
    Amount = FloatField('Amount', validators=[InputRequired()])
    MobileNumber = StringField('MobileNumber', validators=[InputRequired()])
    CouponCode = ListField('CouponCode',validators = [Optional()])
    lat = FloatField('lat', validators=[Optional(), validate_latitude])
    long = FloatField('long', validators=[Optional(), validate_longitude])
    DeliveryWithoutOtp = BooleanField('DeliveryWithoutOtp', validators=[Optional()], false_values=(False, 'false', 0, '0'))
    DeliverWithoutPayment = BooleanField('DeliverWithoutPayment', validators=[Optional()], false_values=(False, 'false', 0, '0'))
    ReasonList = ListField('ReasonList', validators=[Optional()])
    TRNNo = StringField('TRNNo', validators=[Optional()])
    EGRN = StringField('EGRN', validators=[Optional()])
    CustLat = FloatField('CustLat', validators=[Optional(), validate_latitude])
    CustLong = FloatField('CustLong', validators=[Optional(), validate_latitude])
    CustomerName = StringField('CustomerName', validators=[Optional()])
    CustomerCode = StringField('CustomerCode', validators=[Optional()])
    BranchCode = StringField('BranchCode', validators=[Optional()])
    BookingId = IntegerField('BookingId', validators=[Optional()])
    Remarks = StringField('Remarks', validators=[Optional()])