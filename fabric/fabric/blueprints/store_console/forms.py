from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, Field, PasswordField, BooleanField, FloatField
from wtforms.validators import InputRequired, Length, Optional
from .validators import validate_email, validate_admin, validate_branch_code_selection, \
    validate_delivery_user_selection, validate_pickup_request_for_cancel, validate_pickup_requests, \
    validate_delivery_requests, validate_day_interval, validate_store_user_selection, \
    validate_branch_code_selection_d_user_update_register


class ListField(Field):
    """
    A custom WTF field for accepting array of data.
    """

    def process_formdata(self, valuelist):
        self.data = valuelist


class DictField(Field):
    """
    A custom WTF field for accepting an object (like a Dict variable).
    """

    def process_formdata(self, valuelist):
        self.data = valuelist


# Edited by MMM
class RankForm(FlaskForm):
    """
    WTF form class for validating the get_rank_list API request.
    """

    class Meta:
        csrf = False

    city_code = StringField('city_code', validators=[InputRequired()])
    end_date = StringField('end_date', validators=[Optional()])
    report = BooleanField('report', validators=[Optional()], false_values=(False, 'false', 0, '0'))


class CustomerPreferredDayForm(FlaskForm):
    """
    WTF form class for validating the get_customer_preferred_delivery_day API request.
    """

    class Meta:
        csrf = False

    filter_type = StringField('filter_type', validators=[Optional()])
    filter_by = StringField('filter_by', validators=[Optional()])


class SetCustomerPrefferedDayForm(FlaskForm):
    """
    WTF form class for validating the set_customer_preferred_day API request.
    """

    class Meta:
        csrf = False

    day = StringField('filter_type', validators=[InputRequired()])
    customer_code = StringField('customer_code', validators=[InputRequired()])
    time_slot = IntegerField('time_slot', validators=[InputRequired()])
    action = StringField('action', validators=[InputRequired()])


class PushNotificationForm(FlaskForm):
    """
    WTF form class for validating the clock_in API request.
    """

    class Meta:
        csrf = False

    d_userid = IntegerField('d_userid', validators=[InputRequired()])
    page = IntegerField('page', validators=[InputRequired()])


class GetBranchesForm(FlaskForm):
    """
    WTF form class for validating get_branches api request
    """

    class Meta:
        csrf = False

    inactive_branches = BooleanField('Inactive_branches', validators=[Optional()],
                                     false_values=(False, 'false', 0, '0'))


class BranchInactiveForm(FlaskForm):
    """
    WTF form class for validating get_garments_details api request
    """

    class Meta:
        csrf = False

    branch_code = StringField('branch_code', validators=[InputRequired(), validate_branch_code_selection])


class DuserActivityForm(FlaskForm):
    """
    WTF form class for validating garment id
    """

    class Meta:
        csrf = False

    delivery_user_id = IntegerField('delivery_user_id', validators=[InputRequired()])


class GarmentDetailsForm(FlaskForm):
    """
    WTF form class for validating get_garments_details api request
    """

    class Meta:
        csrf = False

    branch_codes = ListField('branch_codes', validators=[InputRequired(), validate_branch_code_selection])


class AddHangerForm(FlaskForm):
    """
    WTF form class for validating garment id
    """

    class Meta:
        csrf = False

    data = ListField('data', validators=[InputRequired()])


# Edited by MMM
class LoginForm(FlaskForm):
    """
    WTF form class for validating the login API request.
    """

    class Meta:
        csrf = False

    mobile_number = StringField('mobile_number', validators=[InputRequired(), Length(min=10, max=10,
                                                                                     message="Minimum 10 characters are needed"), ])

    password = StringField('password', validators=[InputRequired()])


class HomeForm(FlaskForm):
    """
    WTF form class for validating the home API request.
    """

    class Meta:
        csrf = False

    date = StringField('date', validators=[InputRequired()])
    branch_codes = ListField('branch_codes', validators=[Optional(), validate_branch_code_selection])
    state_codes = ListField('state_codes', validators=[Optional()])
    city_codes = ListField('city_codes', validators=[Optional()])
    delivery_user_id = IntegerField('delivery_user_id', validators=[Optional(), validate_delivery_user_selection])
    report = BooleanField('report', validators=[Optional()], false_values=(False, 'false', 0, '0'))


class GetPendingActivitiesForm(FlaskForm):
    """
    WTF form class for validating the get_pending_activities API request.
    """

    class Meta:
        csrf = False

    from_date = StringField('from_date', validators=[Optional()])
    to_date = StringField('to_date', validators=[Optional()])    
    filter_type = StringField('filter_type', validators=[Optional()])
    search = StringField('search', validators=[Optional()])
    page = IntegerField('page', validators=[Optional()])
    branch_codes = ListField('branch_codes', validators=[Optional(), validate_branch_code_selection])
    unassigned_only = BooleanField('unassigned_only', validators=[Optional()], false_values=(False, 'false', 0, '0'))
    late_only = BooleanField('late_only', validators=[Optional()], false_values=(False, 'false', 0, '0'))
    report = BooleanField('report', validators=[Optional()], false_values=(False, 'false', 0, '0'))

class GetDeliveredWithoutPaymentForm(FlaskForm):
    """
    WTF form class for validating the get_pending_activities API request.
    """

    class Meta:
        csrf = False

    from_date = StringField('from_date', validators=[Optional()])
    to_date = StringField('to_date', validators=[Optional()])
    # filter_type = StringField('filter_type', validators=[Optional()])
    # search = StringField('search', validators=[Optional()])
    # page = IntegerField('page', validators=[Optional()])
    branch_codes = ListField('branch_codes', validators=[Optional(), validate_branch_code_selection])
    # unassigned_only = BooleanField('unassigned_only', validators=[Optional()], false_values=(False, 'false', 0, '0'))
    # late_only = BooleanField('late_only', validators=[Optional()], false_values=(False, 'false', 0, '0'))
    # report = BooleanField('report', validators=[Optional()], false_values=(False, 'false', 0, '0'))

class GetAddressForm(FlaskForm):
    """
    WTF form class for validating the get_address API request.
    """

    class Meta:
        csrf = False

    customer_id = IntegerField('customer_id', validators=[InputRequired()])


class GetTimeSlotsForm(FlaskForm):
    """
    WTF form class for validating the get_time_slots API request.
    """

    class Meta:
        csrf = False

    branch_codes = ListField('branch_code', validators=[Optional(), validate_branch_code_selection])


# class CancelPickupForm(FlaskForm):
#     """
#     WTF form class for validating the cancel_pickup API request.
#     """

#     class Meta:
#         csrf = False

#     pickup_request_id = IntegerField('pickup_request_id',
#                                      validators=[InputRequired(), validate_pickup_request_for_cancel])
#     cancel_reason_id = IntegerField('cancel_reason_id', validators=[InputRequired()])
#     cancel_remarks = StringField('cancel_remarks', validators=[Optional()])

class CancelPickupForm(FlaskForm):
    """
    WTF form class for validating the cancel_pickup API request.
    """

    class Meta:
        csrf = False

    booking_id = IntegerField('booking_id',
                                     validators=[InputRequired(), validate_pickup_request_for_cancel])
    cancel_reason_id = IntegerField('cancel_reason_id', validators=[InputRequired()])
    cancel_remarks = StringField('cancel_remarks', validators=[Optional()])
    customer_name = StringField('cancel_remarks', validators=[Optional()])
    branch_code = ListField('branch_code', validators=[Optional(), validate_branch_code_selection])
    mobile_number = StringField('mobile_number', validators=[InputRequired()])


class ReschedulePickupForm(FlaskForm):
    """
    WTF form class for validating the reschedule_pickup API request.
    """

    class Meta:
        csrf = False

    BookingId = ListField('CustomerNames',
                                validators=[InputRequired()])
    reschedule_reason_id = IntegerField('cancel_reason_id', validators=[InputRequired()])
    rescheduled_date = StringField('rescheduled_date', validators=[Optional()])
    CustomerName = ListField('CustomerName', validators=[Optional()])
    MobileNo = ListField('MobileNo', validators=[Optional()])
    CustomerCode = ListField('CustomerCodes', validators=[Optional()])
    BranchCode = ListField('BranchCode', validators=[Optional()])
    time_slot_id = IntegerField('time_slot_id', validators=[Optional()])
    branch_code = StringField('branch_code', validators=[Optional(), validate_branch_code_selection])
    delivery_user_id = IntegerField('delivery_user_id', validators=[Optional(), validate_delivery_user_selection])
    remarks = StringField('remarks', validators=[Optional()])
    TimeSlotFrom = StringField('TimeSlotFrom', validators=[Optional()])
    TimeSlotTo = StringField('TimeSlotTo', validators=[Optional()])
    is_cob = IntegerField('is_cob', validators=[Optional()])
    is_reschedule = IntegerField('is_reschedule', validators=[Optional()])


class GetDeliveryUsersForm(FlaskForm):
    """
    WTF form class for validating the get_delivery_users API request.
    """

    class Meta:
        csrf = False

    # Edited my MM
    inactve = BooleanField('inactve', validators=[Optional()], false_values=(False, 'false', 0, '0'))
    branch = StringField('branch', validators=[Optional()])
    active = BooleanField('active', validators=[Optional()])
    # edited my MM
    branch_codes = ListField('branch_code', validators=[Optional(), validate_branch_code_selection])
    city_code = StringField('city_code', validators=[Optional()])
    report = BooleanField('report', validators=[Optional()], false_values=(False, 'false', 0, '0'))


class GetCompletedActivitiesForm(FlaskForm):
    """
    WTF form class for validating the get_completed_activities API request.
    """

    class Meta:
        csrf = False

    from_date = StringField('from_date', validators=[Optional()])
    to_date = StringField('to_date', validators=[Optional()])
    page = IntegerField('page', validators=[Optional()])
    filter_type = StringField('filter_type', validators=[Optional()])
    search = StringField('search', validators=[Optional()])
    branch_codes = ListField('branch_code', validators=[Optional(), validate_branch_code_selection])
    day_interval = IntegerField('day_interval', validators=[Optional(), validate_day_interval])
    report = BooleanField('report', validators=[Optional()], false_values=(False, 'false', 0, '0'))


class AssignPickupForm(FlaskForm):
    """
    WTF form class for validating the assign_pickup API request.
    """

    class Meta:
        csrf = False

    delivery_user_id = IntegerField('delivery_user_id', validators=[InputRequired(), validate_delivery_user_selection])
    # PickupDate = StringField('PickupDate', validators=[Optional()])
    BookingId = ListField('BookingId', validators=[Optional()])
    MobileNo = ListField('MobileNo', validators=[Optional()])
    CustomerName = ListField('CustomerName', validators=[Optional()])

class AssignDeliveryForm(FlaskForm):
    """
    WTF form class for validating the assign_delivery API request.
    """

    class Meta:
        csrf = False

    TRNNo = ListField('delivery_requests',
                                  validators=[InputRequired()])
    delivery_user_id = IntegerField('cancel_reason_id', validators=[InputRequired()])
    DeliveryDate = StringField('DeliveryDate', validators=[Optional()])
    EGRN = ListField('EGRN', validators=[Optional()])
    MobileNo = ListField('MobileNo', validators=[Optional()])
    CustomerName = ListField('CustomerName', validators=[Optional()])


class RegisterDeliveryUserForm(FlaskForm):
    """
    WTF form class for validating the register_delivery_user API request.
    """

    class Meta:
        csrf = False

    user_name = StringField('user_name', validators=[InputRequired()])
    mobile_number = StringField('mobile_number', validators=[InputRequired()])
    password = PasswordField('password', validators=[Optional()])
    email = StringField('email', validators=[Optional(), validate_email])
    branch_codes = ListField('branch_codes',
                             validators=[InputRequired(), validate_branch_code_selection_d_user_update_register])
    partial_payment_permission = BooleanField('partial_payment_permission', validators=[Optional()],
                                              false_values=(False, 'false', 0, '0'))
    device_details = DictField('device_details', validators=[Optional()])
    cancel_pickup_permission = BooleanField('cancel_pickup_permission', validators=[Optional()],
                                            false_values=(False, 'false', 0, '0'))
    reschedule_pickup_permission = BooleanField('reschedule_pickup_permission', validators=[Optional()],
                                                false_values=(False, 'false', 0, '0'))
    delivery_charge_permission = BooleanField('delivery_charge_permission', validators=[Optional()],
                                                false_values=(False, 'false', 0, '0'))
    Delivery_Without_OTP_permission = BooleanField('Delivery_Without_OTP_permission',validators=[Optional()],
                                                   false_values=(False,'false',0,'0'))
    deliver_without_payment_Permission = BooleanField('deliver_without_payment_Permission', validators=[Optional()],
                                                      false_values=(False, 'false', 0, '0'))

class UpdateDeliveryUserForm(FlaskForm):
    """
    WTF form class for validating the update_delivery_user API request.
    """

    class Meta:
        csrf = False

    delivery_user_id = IntegerField('delivery_user_id', validators=[InputRequired(), validate_delivery_user_selection])
    user_name = StringField('user_name', validators=[Optional()])
    password = PasswordField('password', validators=[Optional()])
    email = StringField('email', validators=[Optional(), validate_email])
    branch_codes = ListField('branch_codes', validators=[Optional()])
    partial_payment_permission = BooleanField('partial_payment_permission', validators=[Optional()],
                                              false_values=(False, 'false', 0, '0'))
    device_details = DictField('device_details', validators=[Optional()])
    user_has_device = BooleanField('user_has_device', validators=[Optional()],
                                   false_values=(False, 'false', 0, '0'))
    cancel_pickup_permission = BooleanField('cancel_pickup_permission', validators=[Optional()],
                                            false_values=(False, 'false', 0, '0'))
    reschedule_pickup_permission = BooleanField('reschedule_pickup_permission', validators=[Optional()],
                                                false_values=(False, 'false', 0, '0'))
    delivery_charge_permission = BooleanField('delivery_charge_permission', validators=[Optional()],
                                                false_values=(False, 'false', 0, '0'))
    Delivery_Without_OTP_permission = BooleanField('Delivery_Without_OTP_permission', validators=[Optional()],
                                                   false_values=(False, 'false', 0, '0'))
    deliver_without_payment_Permission = BooleanField('deliver_without_payment_Permission',validators=[Optional()],
                                           false_values=(False,'false',0,'0'))

class RegisterStoreUserForm(FlaskForm):
    """
    WTF form class for validating the register_store_user API request.
    """

    class Meta:
        csrf = False

    user_name = StringField('user_name', validators=[InputRequired()])
    mobile_number = StringField('mobile_number', validators=[InputRequired()])
    password = PasswordField('password', validators=[InputRequired()])
    email = StringField('email', validators=[InputRequired(), validate_email])
    branch_codes = ListField('branch_codes', validators=[InputRequired(), validate_branch_code_selection])
    is_zic = BooleanField('is_zic', validators=[Optional()], false_values=(False, 'false', 0, '0'))
    cancel_pickup_permission = BooleanField('cancel_pickup_permission', validators=[Optional()],
                                            false_values=(False, 'false', 0, '0'))
    reschedule_pickup_permission = BooleanField('reschedule_pickup_permission', validators=[Optional()],
                                                false_values=(False, 'false', 0, '0'))
    branch_changing_permission = BooleanField('branch_changing_permission', validators=[Optional()],
                                              false_values=(False, 'false', 0, '0'))
    product_screen_permission = BooleanField('product_screen_permission', validators=[Optional()],
                                              false_values=(False, 'false', 0, '0'))
    only_product_screen_permission = BooleanField('product_screen_permission', validators=[Optional()],
                                              false_values=(False, 'false', 0, '0'))
    screen_access = ListField('screen_access', validators=[Optional()])



class UpdateStoreUserForm(FlaskForm):
    """
    WTF form class for validating the update_store_user API request.
    """

    class Meta:
        csrf = False

    store_user_id = IntegerField('store_user_id', validators=[InputRequired()])
    user_name = StringField('user_name', validators=[Optional()])
    password = PasswordField('password', validators=[Optional()])
    email = StringField('email', validators=[Optional(), validate_email])
    branch_codes = ListField('branch_codes', validators=[Optional(), validate_branch_code_selection])
    cancel_pickup_permission = BooleanField('cancel_pickup_permission', validators=[Optional()],
                                            false_values=(False, 'false', 0, '0'))
    reschedule_pickup_permission = BooleanField('reschedule_pickup_permission', validators=[Optional()],
                                                false_values=(False, 'false', 0, '0'))
    branch_changing_permission = BooleanField('branch_changing_permission', validators=[Optional()],
                                              false_values=(False, 'false', 0, '0'))
    product_screen_permission = BooleanField('product_screen_permission', validators=[Optional()],
                                              false_values=(False, 'false', 0, '0'))
    only_product_screen_permission = BooleanField('product_screen_permission', validators=[Optional()],
                                              false_values=(False, 'false', 0, '0'))
    screen_access = ListField('screen_access', validators=[Optional()])


class RescheduleDeliveryForm(FlaskForm):
    """
    WTF form class for validating the reschedule_delivery API request.
    """

    class Meta:
        csrf = False

    TRNNo = ListField('delivery_requests',
                                  validators=[InputRequired()])
    reschedule_reason_id = IntegerField('cancel_reason_id', validators=[InputRequired()])
    rescheduled_date = StringField('rescheduled_date', validators=[InputRequired()])
    time_slot_id = IntegerField('time_slot_id', validators=[InputRequired()])
    delivery_user_id = IntegerField('delivery_user_id', validators=[Optional()])
    CustomerName = ListField('CustomerName', validators=[Optional()])
    remarks = StringField('remarks', validators=[Optional()])
    MobileNo = ListField('MobileNo', validators=[Optional()])
    EGRN = ListField('EGRN', validators=[Optional()])
    TimeSlotFrom = StringField('TimeSlotFrom', validators=[Optional()])
    TimeSlotTo = StringField('TimeSlotTo', validators=[Optional()])
    BranchCode = StringField('BranchCode', validators=[Optional()])
    CustomerCode = ListField('CustomerCode', validators=[Optional()])


class RemoveStoreUserForm(FlaskForm):
    """
    WTF form class for validating the remove_store_user API request.
    """

    class Meta:
        csrf = False

    store_user_id = IntegerField('store_user_id', validators=[InputRequired(), validate_store_user_selection])


class RemoveDeliveryUserForm(FlaskForm):
    """
    WTF form class for validating the remove_delivery_user API request.
    """

    class Meta:
        csrf = False

    delivery_user_id = IntegerField('delivery_user_id', validators=[InputRequired(), validate_delivery_user_selection])


class UpdateBranchForm(FlaskForm):
    """
    WTF form class for validating the update_branch API request.
    """

    class Meta:
        csrf = False

    branch_code = StringField('branch_code', validators=[InputRequired(), validate_admin])
    branch_name = StringField('branch_name', validators=[Optional(), validate_delivery_user_selection])
    holiday = StringField("holiday", validators=[Optional()])


class GetBranchHolidaysForm(FlaskForm):
    """
    WTF form class for validating the get_branch_holidays API request.
    """

    class Meta:
        csrf = False

    branch_codes = ListField('branch_codes', validators=[InputRequired(), validate_branch_code_selection])


class GetDeliveryUserGpsLogsForm(FlaskForm):
    """
    WTF form class for validating the get_delivery_user_gps_logs API request.
    """

    class Meta:
        csrf = False

    # Edited by MMM
    delivery_user_id = IntegerField('delivery_user_id', validators=[Optional()])
    # Edited by MMM
    branch_codes = ListField('branch_codes', validators=[Optional(), validate_branch_code_selection])
    state_codes = ListField('state_codes', validators=[Optional()])
    city_codes = ListField('city_codes', validators=[Optional()])
    day_interval = IntegerField('day_interval', validators=[Optional(), validate_day_interval])


class GetCollectedAmounts(FlaskForm):
    """
    WTF form class for validating the get_collected_amounts API request.
    """

    class Meta:
        csrf = False

    delivery_user_id = IntegerField('delivery_user_id', validators=[InputRequired(), validate_delivery_user_selection])
    date = StringField('date', validators=[InputRequired()])
    branch_codes = ListField('branch_codes', validators=[Optional(), validate_branch_code_selection])


class GetEGRNsForPartialDeliveryForm(FlaskForm):
    """
    WTF form class for validating the get_egrns_for_partial_delivery API request.
    """

    class Meta:
        csrf = False

    branch_codes = ListField('branch_code', validators=[Optional(), validate_branch_code_selection])


class GetGarmentsForPartialDeliveryForm(FlaskForm):
    """
    WTF form class for validating the get_garments_for_partial_delivery API request.
    """

    class Meta:
        csrf = False

    order_id = IntegerField('order_id', validators=[InputRequired()])


class CreateDeliveryRequest(FlaskForm):
    """
    WTF form class for validating the create_delivery_request API request.
    """

    class Meta:
        csrf = False

    order_id = IntegerField('order_id', validators=[InputRequired()])
    order_garments = ListField('order_garments', validators=[InputRequired()])
    address_id = IntegerField('address_id', validators=[InputRequired()])
    delivery_date = StringField('delivery_date', validators=[Optional()])
    delivery_user_id = IntegerField('delivery_user_id', validators=[Optional(), validate_delivery_user_selection])
    time_slot_id = IntegerField('time_slot_id', validators=[Optional()])


class GetAttendanceLogsForm(FlaskForm):
    """
    WTF form class for validating the get_attendance_logs API request.
    """

    class Meta:
        csrf = False

    delivery_user_id = IntegerField('delivery_user_id', validators=[InputRequired()])
    start_date = StringField('start_date', validators=[InputRequired()])
    end_date = StringField('end_date', validators=[InputRequired()])


class EnableStoreUserForm(FlaskForm):
    """
    WTF form class for validating the enable_store_user API request.
    """

    class Meta:
        csrf = False

    store_user_id = IntegerField('store_user_id', validators=[InputRequired(), validate_store_user_selection])


class EnableDeliveryUserForm(FlaskForm):
    """
    WTF form class for validating the enable_delivery_user API request.
    """

    class Meta:
        csrf = False

    delivery_user_id = IntegerField('delivery_user_id', validators=[InputRequired(), validate_delivery_user_selection])


class GetWalkInOrdersForm(FlaskForm):
    """
    WTF form class for validating the get_walk_in_orders API request.
    """

    class Meta:
        csrf = False

    from_date = StringField('from_date', validators=[Optional()])
    to_date = StringField('to_date', validators=[Optional()])
    page = IntegerField('page', validators=[Optional()])
    search = StringField('search', validators=[Optional()])
    branch_codes = ListField('branch_codes', validators=[Optional(), validate_branch_code_selection])
    report = BooleanField('report', validators=[Optional()], false_values=(False, 'false', 0, '0'))


class GetOrderDetailsForm(FlaskForm):
    """
    WTF form class for validating the get_order_details API request.
    """

    class Meta:
        csrf = False

    BookingId = StringField('BookingId', validators=[Optional()])
    TRNNo = StringField('TRNNo', validators=[Optional()])
    activity_type = StringField('activity_type', validators=[Optional()])


class AttendanceReportForm(FlaskForm):
    """
    WTF form class for validating the attendance_report API request.
    """

    class Meta:
        csrf = False

    date = StringField('date', validators=[InputRequired()])
    # Edited by MMM
    end_date = StringField('end_date', validators=[InputRequired()])
    is_log = BooleanField('is_log', validators=[Optional()], false_values=(False, 'false', 0, '0'))
    # Edited by MMM


class MessageLogsReport(FlaskForm):
    """
    WTF form class for validating the message_logs_report API request.
    """

    class Meta:
        csrf = False

    # from_date = StringField('from_date', validators=[InputRequired()])
    # to_date = StringField('to_date', validators=[InputRequired()])
    day_interval = IntegerField('day_interval', validators=[Optional()])
    # Edited By MMM
    delivery_user_id = IntegerField('delivery_user_id', validators=[Optional()])
    report = BooleanField('report', validators=[Optional()], false_values=(False, 'false', 0, '0'))
    # Edited By MMM
    # page = IntegerField('page', validators=[InputRequired()])


class GetCompletedActivitiesReportForm(FlaskForm):
    """
    WTF form class for validating the get_completed_activities API request.
    """

    class Meta:
        csrf = False

    branch_codes = ListField('branch_code', validators=[Optional(), validate_branch_code_selection])

    report = BooleanField('report', validators=[Optional()], false_values=(False, 'false', 0, '0'))
    from_date = StringField('from_date', validators=[InputRequired()])
    to_date = StringField('to_date', validators=[InputRequired()])


class GetCancelledPickupsForm(FlaskForm):
    """
    WTF form class for validating the get_completed_activities API request.
    """

    class Meta:
        csrf = False

    branch_codes = ListField('branch_code', validators=[Optional(), validate_branch_code_selection])
    day_interval = IntegerField('day_interval', validators=[Optional(), validate_day_interval])
    report = BooleanField('report', validators=[Optional()], false_values=(False, 'false', 0, '0'))


class GetFabricareStoreUserBranchForm(FlaskForm):
    """
    WTF form class for validating the get_fabricare_store_user_branches API request.
    """
    class Meta:
        csrf = False

    user_name = StringField('user_name', validators=[InputRequired()])

class GetPickupInstructions(FlaskForm):
    class Meta:
        csrf = False
    search = StringField('search', validators=[Optional()])

class AddIconsForm(FlaskForm):
    class Meta:
        csrf = False

    PickupinstructionsId = IntegerField('PickupinstructionsId', validators=[InputRequired()])
    PickupinstructionsImage = StringField('PickupinstructionsImage', validators=[Optional()])


class DeleteIconForm(FlaskForm):
    class Meta:
        csrf = False

    PickupinstructionsId = IntegerField('PickupinstructionsId', validators=[InputRequired()])

class GetBranchForm(FlaskForm):
    """
    WTF form class for validating get_branches API request.
    """

    class Meta:
        csrf = False

    latpoint = FloatField('Latitude', validators=[InputRequired()])
    longpoint = FloatField('Longitude', validators=[InputRequired()])

class Cancel_Restriction_PickupForm(FlaskForm):
    """
    WTF form class for validating the cancel_pickup API request.
    """

    class Meta:
        csrf = False

    # pickup_request_id = IntegerField('pickuprequest_id',
    #                                  validators=[InputRequired(), validate_pickup_request_for_cancel])
    pickup_request_id = StringField('pickup_request_id',
                                     validators=[InputRequired()])

class Cancel_Reason_PickupForm(FlaskForm):
    """
    WTF form class for validating the cancel_pickup API request.
    """

    class Meta:
        csrf = False


    # pickup_request_id = IntegerField('pickuprequest_id',
    #                                  validators=[InputRequired(), validate_pickup_request_for_cancel])
    pickup_request_id = StringField('pickup_request_id',
                             validators=[InputRequired()])
    cancel_reason = StringField('cancel_reason', validators=[Optional()])