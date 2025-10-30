import re
from flask import request
from sqlalchemy import or_, case
from wtforms import ValidationError
import inspect
from fabric import db
from fabric.blueprints.store_console.queries import get_store_user_branches
from fabric.generic.loggers import error_logger
from fabric.modules.models import StoreUser, DeliveryUser, PickupRequest, PickupReschedule, DeliveryRequest, Order, \
    DeliveryUserBranch, StoreUserBranch


def validate_email(form, field):
    """
    Checking the email is valid or not.
    @param form:
    @param field:
    @return: If validation fails, validator will return a validation error.
    """
    email = field.data
    regex = '^[A-Za-z0-9]+[\._]?[A-Za-z0-9]+[@]\w+[.]\w{2,3}$'
    email_regex = re.search(regex, email)
    if not email_regex:
        raise ValidationError('Please provide a valid email address.')


def validate_admin(form, field):
    """
    Checking whether the store user is admin or not.
    Only a store user admin have the privilege to add this field.
    @param form:
    @param field:
    @return: If validation fails, validator will return a validation error.
    """
    user_id = request.headers.get('user-id')
    admin = False
    # Checking whether the store user is admin or not.
    try:
        store_user = db.session.query(StoreUser).filter(StoreUser.SUserId == user_id).one_or_none()
        if store_user is not None:
            if store_user.IsAdmin == 1:
                admin = True
    except Exception as e:
        error_logger(f'Store Blueprint Validators: {inspect.stack()[0].function}()').error(e)

    if not admin:
        raise ValidationError('Can not add this field. Admin privilege required.')


def validate_branch_code_selection(form, field):
    """
    Checking whether the store user is admin or not.
    Only admin can choose any branch code. Non admin can only choose their own branch code.
    @param form:
    @param field:
    @return: If validation fails, validator will return a validation error.
    """
    branch_codes = field.data
    user_id = request.headers.get('user-id')
    valid_branch_code = False
    invalid_branch_codes = []
    # Checking whether the store user is admin or not.
    try:
        store_user = db.session.query(StoreUser).filter(StoreUser.SUserId == user_id).one_or_none()
        if store_user is not None:
            if store_user.IsAdmin == 1:
                valid_branch_code = True
            else:
                # Here, the store user is not an admin.
                # The non admin store user's branch code should be matched with the given branch code.
                # If they are not matching, then raise exception.

                # Getting the branch codes associated with the store user.
                store_user_branch_codes = get_store_user_branches(user_id)

                if type(branch_codes) == str:
                    # Only one branch code is given.
                    if branch_codes in store_user_branch_codes:
                        valid_branch_code = True
                    else:
                        # Store user have no privilege to access this branch code.
                        invalid_branch_codes.append(branch_codes)
                elif type(branch_codes) == list:
                    # Multiple branch codes are given.
                    flags = []
                    for branch_code in branch_codes:
                        if branch_code not in store_user_branch_codes:
                            # This branch code does not belong to this store user.
                            invalid_branch_codes.append(branch_code)
                            flags.append(False)
                        else:
                            flags.append(True)

                    # AND operation on flags. True if all flags are True. Otherwise, returns False.
                    valid_branch_code = all(flags)
    except Exception as e:
        error_logger(f'Store Blueprint Validators: {inspect.stack()[0].function}()').error(e)

    if not valid_branch_code:
        raise ValidationError(
            f"This store user does not have the privilege to choose this branch code(s): {','.join(map(str, invalid_branch_codes))}")


def validate_branch_code_selection_d_user_update_register(form, field):
    """
    Checking whether the store user is admin or not.
    Only admin can choose any branch code. Non admin can only choose their own branch code.
    @param form:
    @param field:
    @return: If validation fails, validator will return a validation error.
    """
    branch_codes = field.data
    user_id = request.headers.get('user-id')
    valid_branch_code = False
    invalid_branch_codes = []
    # Checking whether the store user is admin or not.
    try:
        store_user = db.session.query(StoreUser).filter(StoreUser.SUserId == user_id).one_or_none()
        if store_user is not None:
            if store_user.IsAdmin == 1:
                valid_branch_code = True
            else:
                # Here, the store user is not an admin.
                # The non admin store user's branch code should be matched with the given branch code.
                # If they are not matching, then raise exception.

                # Getting the branch codes associated with the store user.
                store_user_branch_codes = get_store_user_branches(user_id)

                if type(branch_codes) == str:
                    # Only one branch code is given.
                    if branch_codes in store_user_branch_codes:
                        valid_branch_code = True
                    else:
                        # Store user have no privilege to access this branch code.
                        invalid_branch_codes.append(branch_codes)
                elif type(branch_codes) == list:
                    # Multiple branch codes are given.
                    flags = []
                    for branch_code in branch_codes:
                        if branch_code['BranchCode'] not in store_user_branch_codes:
                            # This branch code does not belong to this store user.
                            invalid_branch_codes.append(branch_code['BranchCode'])
                            flags.append(False)
                        else:
                            flags.append(True)

                    # AND operation on flags. True if all flags are True. Otherwise, returns False.
                    valid_branch_code = all(flags)
    except Exception as e:
        error_logger(f'Store Blueprint Validators: {inspect.stack()[0].function}()').error(e)

    if not valid_branch_code:
        raise ValidationError(
            f"This store user does not have the privilege to choose this branch code(s): {','.join(map(str, invalid_branch_codes))}")


def validate_delivery_user_selection(form, field):
    """
    Checking whether the store user is admin or not.
    Only admin can choose any delivery user. Non admin can only choose their own delivery users.
    @param form:
    @param field:
    @return: If validation fails, validator will return a validation error.
    """
    user_id = request.headers.get('user-id')
    delivery_user_id = field.data
    valid_delivery_user = False
    try:
        store_user = db.session.query(StoreUser).filter(StoreUser.SUserId == user_id).one_or_none()
        if store_user is not None:
            if store_user.IsAdmin:
                # The store user is admin. Admin can choose any delivery users.
                valid_delivery_user = True
            else:
                # Getting the branch codes associated with the store user.
                store_user_branch_codes = get_store_user_branches(user_id)

                # Store user is not admin. So this store user can only choose his own delivery users.
                delivery_user = db.session.query(DeliveryUser.DUserId).join(DeliveryUserBranch,
                                                                            DeliveryUserBranch.DUserId == DeliveryUser.DUserId).distinct(
                    DeliveryUser.DUserId).filter(
                    DeliveryUserBranch.BranchCode.in_(store_user_branch_codes),
                    DeliveryUser.DUserId == delivery_user_id).one_or_none()

                if delivery_user is not None:
                    # The store user can choose this delivery user.
                    valid_delivery_user = True

    except Exception as e:
        error_logger(f'Store Blueprint Validators: {inspect.stack()[0].function}()').error(e)

    if not valid_delivery_user:
        raise ValidationError('This store user does not have the privilege to choose this delivery user.')


def validate_store_user_selection(form, field):
    """
    Validating the selection of a store user.
    Only admin can choose any store user. Zonal in charge can only choose their own store users.
    Normal store users can not select others.
    @param form:
    @param field:
    @return: If validation fails, validator will return a validation error.
    """
    user_id = request.headers.get('user-id')
    store_user_id = field.data
    valid_store_user = False
    error_msg = ''
    try:
        if int(user_id) != store_user_id:
            store_user = db.session.query(StoreUser).filter(StoreUser.SUserId == user_id).one_or_none()
            if store_user is not None:
                if store_user.IsAdmin:
                    # The store user is admin. Admin can choose any store users.
                    valid_store_user = True
                else:
                    if store_user.IsZIC:
                        # Getting the branch codes associated with the store user.
                        store_user_branch_codes = get_store_user_branches(user_id)

                        # Store user is not admin but ZIC. So this store user can only choose his own store users.
                        store_user = db.session.query(StoreUser.SUserId).join(StoreUserBranch,
                                                                              StoreUserBranch.SUserId == StoreUser.SUserId).distinct(
                            StoreUser.SUserId).filter(
                            StoreUserBranch.BranchCode.in_(store_user_branch_codes),
                            StoreUser.SUserId == store_user_id, StoreUser.IsAdmin == 0).one_or_none()

                        if store_user is not None:
                            # The store user can choose this store user.
                            valid_store_user = True
        else:
            error_msg = 'You can not choose yourself. Please choose another store user.'

    except Exception as e:
        error_logger(f'Store Blueprint Validators: {inspect.stack()[0].function}()').error(e)

    if not valid_store_user:
        if error_msg:
            raise ValidationError(error_msg)
        else:
            raise ValidationError(f'This store user does not have the privilege to choose this store user.')


# def validate_pickup_request_for_cancel(form, field):
#     """
#     Checking whether the store user is admin or not.
#     Only admin can choose any pickup request for cancelling. Non admin can only choose their own branch's
#     pickup requests for cancelling.
#     @param form:
#     @param field:
#     @return: If validation fails, validator will return a validation error.
#     """
#     user_id = request.headers.get('user-id')
#     pickup_request_id = field.data
#     valid_pickup_request = False
#     try:
#         store_user = db.session.query(StoreUser).filter(StoreUser.SUserId == user_id).one_or_none()
#         if store_user is not None:
#             if store_user.IsAdmin:
#                 # The store user is admin. Admin can choose any pickup request.
#                 valid_pickup_request = True
#             else:

#                 # Getting the branch codes associated with the store user.
#                 store_user_branch_codes = get_store_user_branches(user_id)

#                 # If the pickup is rescheduled, then select pickup reschedule's BranchCode,
#                 # else select pickup request's BranchCode.
#                 existing_branch_code = case([(PickupReschedule.PickupRequestId == None, PickupRequest.BranchCode), ],
#                                             else_=PickupReschedule.BranchCode).label("BranchCode")

#                 # Store user is not admin. So this store user can only choose his own pickup requests.
#                 pickup_request = db.session.query(PickupRequest).outerjoin(PickupReschedule,
#                                                                            PickupRequest.PickupRequestId == PickupReschedule.PickupRequestId).filter(
#                     existing_branch_code.in_(store_user_branch_codes),
#                     PickupRequest.PickupRequestId == pickup_request_id,
#                     or_(PickupReschedule.IsDeleted == 0, PickupReschedule.IsDeleted == None)).one_or_none()

#                 if pickup_request is not None:
#                     # The store user can choose this pickup request.
#                     valid_pickup_request = True

#     except Exception as e:
#         error_logger(f'Store Blueprint Validators: {inspect.stack()[0].function}()').error(e)

#     if not valid_pickup_request:
#         raise ValidationError('This store user does not have the privilege to choose this pickup request.')

def validate_pickup_request_for_cancel(form, field):
    """
    Checking whether the store user is admin or not.
    Only admin can choose any pickup request for cancelling. Non admin can only choose their own branch's
    pickup requests for cancelling.
    @param form:
    @param field:
    @return: If validation fails, validator will return a validation error.
    """
    user_id = request.headers.get('user-id')
    branch_code = field.data
    valid_pickup_request = False
    try:
        store_user = db.session.query(StoreUser).filter(StoreUser.SUserId == user_id).one_or_none()
        print(store_user)
        if store_user is not None:
            print("hello")
            if store_user.IsAdmin:
                print("test")
                # The store user is admin. Admin can choose any pickup request.
                valid_pickup_request = True
            else:
                print("hjk")

                # Getting the branch codes associated with the store user.
                store_user_branch_codes = get_store_user_branches(user_id)

                # Validate if the user has access to cancel this pickup request
                if branch_code in store_user_branch_codes:
                    valid_pickup_request = True

    except Exception as e:
        error_logger(f'Store Blueprint Validators: {inspect.stack()[0].function}()').error(e)

    if not valid_pickup_request:
        raise ValidationError('This store user does not have the privilege to choose this pickup request.')


def validate_pickup_requests(form, field):
    """
    Checking whether the store user is admin or not.
    Only admin can choose any pickup request for cancelling. Non admin can only choose their own branch's
    pickup requests for cancelling.
    @param form:
    @param field:
    @return: If validation fails, validator will return a validation error.
    """
    user_id = request.headers.get('user-id')
    pickup_requests = field.data
    valid_pickup_request = False
    try:
        store_user = db.session.query(StoreUser).filter(StoreUser.SUserId == user_id).one_or_none()
        if store_user is not None:
            if store_user.IsAdmin:
                # The store user is admin. Admin can choose any pickup request.
                valid_pickup_request = True
            else:

                # Getting the branch codes associated with the store user.
                store_user_branch_codes = get_store_user_branches(user_id)

                for pickup_request_id in pickup_requests:
                    # Looping through the given pickup requests.

                    # If the pickup is rescheduled, then select pickup reschedule's BranchCode,
                    # else select pickup request's BranchCode.
                    existing_branch_code = case(
                        [(PickupReschedule.PickupRequestId == None, PickupRequest.BranchCode), ],
                        else_=PickupReschedule.BranchCode).label("BranchCode")

                    # Store user is not admin. So this store user can only choose his own pickup requests.
                    pickup_request = db.session.query(PickupRequest).outerjoin(PickupReschedule,
                                                                               PickupRequest.PickupRequestId == PickupReschedule.PickupRequestId).filter(
                        existing_branch_code.in_(store_user_branch_codes),
                        PickupRequest.PickupRequestId == pickup_request_id,
                        or_(PickupReschedule.IsDeleted == 0, PickupReschedule.IsDeleted == None)).one_or_none()

                    if pickup_request is not None:
                        # The store user can choose this pickup request.
                        valid_pickup_request = True
                    else:
                        valid_pickup_request = False
                        break

    except Exception as e:
        error_logger(f'Store Blueprint Validators: {inspect.stack()[0].function}()').error(e)

    if not valid_pickup_request:
        raise ValidationError('This store user does not have the privilege to choose this pickup request.')


def validate_delivery_requests(form, field):
    """
    Checking whether the store user is admin or not.
    Only admin can choose any delivery request for rescheduling. Non admin can only choose their own branch's
    delivery requests for rescheduling.
    @param form:
    @param field:
    @return: If validation fails, validator will return a validation error.
    """
    user_id = request.headers.get('user-id')
    delivery_requests = field.data
    valid_delivery_request = False
    try:
        store_user = db.session.query(StoreUser).filter(StoreUser.SUserId == user_id).one_or_none()
        if store_user is not None:
            if store_user.IsAdmin:
                # The store user is admin. Admin can choose any delivery request.
                valid_delivery_request = True
            else:
                # Getting the branch codes associated with the store user.
                store_user_branch_codes = get_store_user_branches(user_id)

                for delivery_request_id in delivery_requests:
                    # Looping through the delivery request ids and validating each other.

                    # Store user is not admin. So this store user can only choose his own delivery requests.
                    delivery_request = db.session.query(DeliveryRequest).join(Order,
                                                                              DeliveryRequest.OrderId == Order.OrderId).filter(
                        Order.BranchCode.in_(store_user_branch_codes),
                        DeliveryRequest.DeliveryRequestId == delivery_request_id).one_or_none()

                    if delivery_request is not None:
                        # The store user can choose this delivery request.
                        valid_delivery_request = True
                    else:
                        valid_delivery_request = False
                        break

    except Exception as e:
        error_logger(f'Store Blueprint Validators: {inspect.stack()[0].function}()').error(e)

    if not valid_delivery_request:
        raise ValidationError('This store user does not have the privilege to choose this delivery request.')


def validate_day_interval(form, field):
    """
    Validating the given day is less than 7 or not. (A week or not).
    @param form:
    @param field:
    @return: If validation fails, validator will return a validation error.
    """
    day_interval = field.data
    if day_interval > 7:
        raise ValidationError('Up to 7 days are permissible.')
