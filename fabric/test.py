# @delivery_blueprint.route('/reschedule_pickup', methods=["POST"])
# # @authenticate('delivery_user')
# def reschedule_pickup():
#     """
#     API for rescheduling a pickup request.
#     """
#     reschedule_form = ReschedulePickupForm()
#     is_rescheduled = False
#     user_id = request.headers.get('user-id')
#
#     # mobileno1 = db.session.query(DeliveryUser.MobileNo).filter(DeliveryUser.DUserId == user_id).one_or_none()
#     # print(mobileno1)
#     # mobileno2 = mobileno1[0]  # Accessing the first element of the tuple
#     # mobileno = '"' + str(mobileno2) + '"'  # Convert to string and enclose in double quotes
#     # print("mobileno",mobileno)
#     if reschedule_form.validate_on_submit():
#         pickup_request_id = reschedule_form.pickup_request_id.data
#
#         modified_name = db.session.query(DeliveryUser.UserName).filter(DeliveryUser.DUserId == user_id).one_or_none()
#         # username = db.session.query(DeliveryUser.UserName).filter(DeliveryUser.DUserId == user_id).one_or_none()
#         #
#         # bookingid = db.session.query(Order.BookingId).filter(Order.PickupRequestId == pickup_request_id)
#         reschedule_reason_id = reschedule_form.reschedule_reason_id.data
#         rescheduled_date = reschedule_form.rescheduled_date.data
#         discount_code = None if reschedule_form.discount_code.data == '' else reschedule_form.discount_code.data
#         # rescheduled_date will be DD-MM-YYYY format. Need to convert into YYYY-MM-DD format.
#         # Here, first convert the string date to date object in expected form. Here, the string date will be
#         # in dd-mm-yyyy form.
#         rescheduled_date_obj = datetime.strptime(rescheduled_date, "%d-%m-%Y")
#         # From the date object, convert the date to YYYY-MM-DD format.
#         formatted_rescheduled_date = rescheduled_date_obj.strftime("%Y-%m-%d %H:%M:%S")
#         time_slot_id = reschedule_form.time_slot_id.data
#         branch_code = None if reschedule_form.branch_code.data == '' else reschedule_form.branch_code.data
#         lat = None if reschedule_form.lat.data == '' else reschedule_form.lat.data
#         long = None if reschedule_form.long.data == '' else reschedule_form.long.data
#         # Temporary change to update service_tat_id only if it is passed
#         service_tat_id = reschedule_form.service_tat_id.data
#         error_msg = ''
#         pickup_time_slot = None
#
#
#
#         try:
#             # Getting the pickup request table details. No orders should be present for this pickup request.
#             pickup_request_details = db.session.query(PickupRequest).outerjoin(Order,
#                                                                                PickupRequest.PickupRequestId == Order.PickupRequestId).filter(
#                 PickupRequest.PickupRequestId == pickup_request_id, or_(Order.OrderId == None, PickupRequest.IsReopen == 1, Order.EGRN == None)).one_or_none()
#
#             if pickup_request_details is not None:
#                 # Check whether the pickup is already rescheduled or not.
#                 # If the pickup request is already rescheduled, no further reschedules are allowed.
#                 pickup_reschedule = db.session.query(PickupReschedule).filter(
#                     PickupReschedule.PickupRequestId == pickup_request_id,
#                     PickupReschedule.IsDeleted == 0).one_or_none()
#
#                 if pickup_reschedule is None:
#
#                     # Check if the given date is a branch holiday or not.
#                     if branch_code is None:
#                         # No branch code is provided.
#                         reschedule_branch_code = pickup_request_details.BranchCode
#                     else:
#                         # Branch code is given.
#                         reschedule_branch_code = branch_code
#
#                     # Check if the given date is a branch holiday or not.
#                     holiday = delivery_controller_queries.check_branch_holiday(rescheduled_date,
#                                                                                reschedule_branch_code)
#                     if not holiday:
#                         # The given date is not a branch holiday.
#
#                         # Checking whether the given time slot id is belong to this branch or not.
#                         pickup_time_slot = db.session.query(PickupTimeSlot.TimeSlotFrom,
#                                                             PickupTimeSlot.TimeSlotTo).filter(
#                             PickupTimeSlot.PickupTimeSlotId == time_slot_id,
#                             PickupTimeSlot.BranchCode == reschedule_branch_code,
#                             or_(PickupTimeSlot.VisibilityFlag == 1, PickupTimeSlot.DefaultFlag == 1)).one_or_none()
#
#                         if pickup_time_slot is not None:
#
#                             # Setting up the new PickupReschedule object.
#                             new_reschedule = PickupReschedule(PickupRequestId=pickup_request_id,
#                                                               RescheduleReasonId=reschedule_reason_id,
#                                                               RescheduledDate=formatted_rescheduled_date,
#                                                               PickupTimeSlotId=time_slot_id,
#                                                               TimeSlotFrom=pickup_time_slot.TimeSlotFrom,
#                                                               TimeSlotTo=pickup_time_slot.TimeSlotTo,
#                                                               BranchCode=reschedule_branch_code,
#                                                               DUserId=user_id,
#                                                               CustAddressId=pickup_request_details.CustAddressId,
#                                                               RescheduledDeliveryUser=user_id,
#                                                               Lat=lat,
#                                                               Long=long,
#                                                               RescheduledBy=modified_name[0]
#                                                               )
#                             db.session.add(new_reschedule)
#                             db.session.commit()
#
#                             # Updating the RecordLastUpdatedDate in the pickup request table.
#                             pickup_request_details.RecordLastUpdatedDate = get_current_date()
#                             db.session.commit()
#
#                             is_rescheduled = True
#
#                             if pickup_request_details.BookingId is not None:
#                                 # Informing the POS about the pickup reschedule.
#                                 common_module.notify_pos_regarding_pickup_reschedule_or_cancel(
#                                     pickup_request_id,
#                                     pickup_request_details.BookingId, 0, 1, 0)
#                         else:
#                             error_msg = 'This time slot does not belongs to this branch.'
#                     else:
#                         # It is a branch holiday. Reschedule on this day is not allowed.
#                         error_msg = 'This is a branch holiday. Please choose another date.'
#                 else:
#
#                     # Check if the given date is a branch holiday or not.
#                     if branch_code is None:
#                         # No branch code is provided.
#                         reschedule_branch_code = pickup_reschedule.BranchCode
#                     else:
#                         # Branch co
#                         # de is given.
#                         reschedule_branch_code = branch_code
#
#                     # Check if the given date is a branch holiday or not.
#                     holiday = delivery_controller_queries.check_branch_holiday(rescheduled_date,
#                                                                                reschedule_branch_code)
#
#                     if not holiday:
#                         # The given date is not a branch holiday. So reschedule can be performed.
#
#                         # Pickup reschedule is already present. Delete the row and insert again.
#
#                         # Checking whether the given time slot id is belong to this branch or not.
#                         pickup_time_slot = db.session.query(PickupTimeSlot.TimeSlotFrom,
#                                                             PickupTimeSlot.TimeSlotTo).filter(
#                             PickupTimeSlot.PickupTimeSlotId == time_slot_id,
#                             PickupTimeSlot.BranchCode == reschedule_branch_code,
#                             or_(PickupTimeSlot.VisibilityFlag == 1, PickupTimeSlot.DefaultFlag == 1)).one_or_none()
#
#                         if pickup_time_slot is not None:
#                             pickup_reschedule.IsDeleted = 1
#                             pickup_reschedule.CancelledDate = get_current_date()
#                             db.session.commit()
#
#                             # After making the previous reschedule delete,
#                             # create a new entry in the PickupReschedules table.
#                             new_reschedule = PickupReschedule(PickupRequestId=pickup_request_id,
#                                                               RescheduleReasonId=reschedule_reason_id,
#                                                               RescheduledDate=formatted_rescheduled_date,
#                                                               PickupTimeSlotId=time_slot_id,
#                                                               TimeSlotFrom=pickup_time_slot.TimeSlotFrom,
#                                                               TimeSlotTo=pickup_time_slot.TimeSlotTo,
#                                                               BranchCode=reschedule_branch_code,
#                                                               DUserId=user_id,
#                                                               CustAddressId=pickup_reschedule.CustAddressId,
#                                                               RescheduledDeliveryUser=user_id,
#                                                               Lat=lat,
#                                                               Long=long,
#                                                               RescheduledBy=modified_name[0]
#                                                               )
#
#                             db.session.add(new_reschedule)
#                             db.session.commit()
#
#                             # Updating the RecordLastUpdatedDate in the pickup request table.
#                             pickup_request_details.RecordLastUpdatedDate = get_current_date()
#
#                             if service_tat_id:
#                                 pickup_request_details.ServiceTatId = service_tat_id
#
#                             db.session.commit()
#
#                             is_rescheduled = True
#
#                             if pickup_request_details.BookingId is not None:
#                                 # Informing the POS about the pickup reschedule.
#                                 common_module.notify_pos_regarding_pickup_reschedule_or_cancel(
#                                     pickup_request_id,
#                                     pickup_request_details.BookingId, 0, 1, 0)
#                         else:
#                             error_msg = 'This time slot does not belongs to this branch.'
#
#                     else:
#                         # It is a branch holiday. Reschedule on this day is not allowed.
#                         error_msg = 'This is a branch holiday. Please choose another date.'
#
#         except Exception as e:
#             db.session.rollback()
#             error_logger(f'Route: {request.path}').error(e)
#
#         if is_rescheduled:
#
#             # https://appuat.fabricspa.com/fabricspauat/Mobile_Controller/send_promotional_notification
#
#
#             # Getting Pickup details from DB
#             pickup_details = db.session.query(PickupRequest.CustomerId, PickupRequest.BookingId).filter(
#                 PickupRequest.PickupRequestId == pickup_request_id).one_or_none()
#
#             booking_id = 'NA' if pickup_details.BookingId is None else pickup_details.BookingId
#
#             time_slot = SerializeSQLAResult(pickup_time_slot).serialize_one()
#             # Formatting time slots to send via SMS
#             formatted_time_slot = f"{str(time_slot['TimeSlotFrom'])} to {str(time_slot['TimeSlotTo'])}"
#
#             # function for sending SMS via ice cubes
#             # delivery_controller_queries.send_sms_after_activity(pickup_details.CustomerId, None,
#             #                                                     rescheduled_date_obj.strftime("%d-%m-%Y"), booking_id,
#             #                                                     formatted_time_slot, 'RESCHEDULE_PICKUP')
#             # update PickupRequest details if discount code given
#             #
#             # headers = [{"key": "Content-Type", "value": "application/json"},
#             #             {"key": "api_key", "value": "c3bbd214b7f7439f60fa36ba"}]
#
#
#             # headers = {'Content-Type': 'application/json', 'api_key': "c3bbd214b7f7439f60fa36ba"}
#             #
#             # api_url = 'https://appuat.fabricspa.com/fabricspauat/Mobile_Controller/send_promotional_notification'
#             #
#             # message=f"Hi{username}, your pickup with booking ID {bookingid} is rescheduled for {rescheduled_date}.For any changes call 080-46644664 / Click here https://fabspa.in/app to download the app."
#             #
#             # json_request = {"mobile_number":mobileno,"message":message}
#             # print(json_request)
#             # Calling the API.
#             # response = requests.post(api_url, data=json.dumps(json_request), headers=headers)
#             # print(response,'response')
#
#             if discount_code is not None:
#                 try:
#                     er_discount_code = None
#                     db_discount_code = discount_code
#
#                     # Get PickupRequest details from DB
#                     pickup_details = db.session.query(PickupRequest).filter(
#                         PickupRequest.PickupRequestId == pickup_request_id).one_or_none()
#
#                     # Get Customer details from DB
#                     customer_details = db.session.query(Customer.CustomerCode).filter(
#                         Customer.CustomerId == pickup_details.CustomerId).one_or_none()
#
#                     # Checking whether the discount code is er discount code or not
#                     er_validation = er_module.validate_er_coupon(customer_details.CustomerCode,
#                                                                  pickup_details.BranchCode, discount_code)
#                     is_er_coupon = 0
#                     # validation will takes place only if there is no DiscountCode is already applied.
#                     if er_validation['status']:
#                         er_discount_code = discount_code
#                         # The original POS discount code is the discount_code coming from the ER response.
#                         discount_code = er_validation['discount_code']
#                         is_er_coupon = 1
#                     # Validating the discount code.
#                     validation = common_module.validate_discount_code(discount_code, 'pickup', None,
#                                                                       customer_details.CustomerCode,
#                                                                       pickup_details.BranchCode, is_er_coupon)
#
#                     if validation['ISVALID']:
#                         # Update PickupRequest table
#                         pickup_details.AdhocDiscount = db_discount_code
#                         pickup_details.IsERCoupon = is_er_coupon
#                         pickup_details.CodeFromER = er_discount_code
#                         db.session.commit()
#
#                 except Exception as e:
#                     error_logger(f'Route: {request.path}').error(e)
#
#             final_data = generate_final_data('DATA_UPDATED')
#         else:
#             if error_msg:
#                 final_data = generate_final_data('CUSTOM_FAILED', error_msg)
#             else:
#                 final_data = generate_final_data('DATA_UPDATE_FAILED')
#     else:
#         # Form validation error.
#         final_data = generate_final_data('FORM_ERROR')
#         final_data['errors'] = populate_errors(reschedule_form.errors)
#
#     return final_data
#