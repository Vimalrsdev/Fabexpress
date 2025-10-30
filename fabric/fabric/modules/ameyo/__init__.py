"""
------------------------
Ameyo module
The module deals with the integration of the Ameyo ticketing service.
(third-party library)
------------------------
Coded by: Krishna Prasad K
© Jyothy Fabricare Services LTD.
------------------------
"""

import requests
import json
import inspect

from fabric import db
from fabric.blueprints.delivery_app.queries import get_est_delivery_date, update_est_delivery_date, \
    set_max_est_delivery_date
from fabric.generic.classes import CallSP
from fabric.generic.functions import get_current_date, get_today
from fabric.generic.loggers import error_logger, info_logger
from fabric.modules.models import Order, OrderGarment, Complaint, CustomerAddres, State, City, PickupRequest, \
    PickupTimeSlot, OrderInstruction, Customer, FabPickupTimeSlots
from fabric.settings.project_settings import LOCAL_DB, SERVER_DB
from sqlalchemy import text
from flask import request
from fabric.generic.classes import SerializeSQLAResult


def add_complaint(CustomerName,MobileNo,CustomerCode, ameyo_customer_id, egrn, allowed_complaint_garment_list,BranchCode):

    """
    Function for generating a complaint for an order garment.
    First call the Ameyo API then create a complaint with CRM.
    @param allowed_complaint_garment_list: List of garments with the complaint details that has no previous complaints available.
    @param customer_details:
    @param ameyo_customer_id:
    @param egrn
    @return: Dict variable consisting of status and comments.
    """

    complaint_created = False
    comments = []

    # Calling the Ameyo API to create a ticket.
    ticket = create_ticket(egrn,CustomerCode, CustomerName,MobileNo,BranchCode ,ameyo_customer_id )

    if ticket is not None:
        # Received the response the API.
        if ticket['ticketId']:
            # Successfully generated a ticket id.
            # Saving the complaint details into Complaints table.

            # Each garment have to have each entries in the complaints table.
            for complaint_garment in allowed_complaint_garment_list:
                already_complaint = db.session.query(Complaint).filter(Complaint.TagId == complaint_garment['TagNo']).one_or_none()

                if already_complaint is None:

                    query = f"""EXEC JFSL_UAT.Dbo.[SPFabComplaintsInsertUpdate] 
                                @CustomerCode = '{CustomerCode}',
                                @BranchCode = '{BranchCode}',
                                @complaint_type = '{allowed_complaint_garment_list[0].get('complaint_type')}',
                                @EGRN = '{egrn}',
                                @TagId = '{allowed_complaint_garment_list[0].get('TagNo')}',
                                @complaint_remarks = '{allowed_complaint_garment_list[0].get('complaint_remarks')}'
                                ,@IsUpdate = {0},
                                @AmeyoTicketId = {ticket.get('ticketId')},
                                 @JFSLTicketId = '{ticket.get('customId')}',
                                @TicketSubject = '{ticket.get('subject')}',
                                @AmeyoTicketSourceType = '{ticket.get('sourceType')}',
                                @QueueId = {ticket.get('queueId')},
                                @CampaignId =  {ticket.get('campaignId')},
                                @AssignedUserId =  {ticket.get('assignedUserId')},
                                @AmeyoTicketStatus = {ticket.get('externalState')}
                                
                                """

                    execute_with_commit(text(query))

                else:
                    try:
                        already_complaint.AmeyoTicketId = ticket.get('ticketId')
                        already_complaint.JFSLTicketId = ticket.get('customId')
                        already_complaint.TicketSubject = ticket.get('subject')
                        already_complaint.AmeyoTicketSourceType = ticket.get('sourceType')
                        already_complaint.ComplaintDate = get_current_date()
                        already_complaint.ComplaintType = complaint_garment.get('complaint_type')
                        already_complaint.ComplaintDesc = complaint_garment.get('complaint_remarks')
                        already_complaint.RecordLastUpdatedDate = get_current_date()
                        # update the garment complaint in the DB.
                        db.session.commit()
                    except Exception as e:
                        error_logger(f'Ameyo: {inspect.stack()[0].function}()').error(e)

            # After adding generating the complaint, inform POS's CRM about the complaint.
            try:
                query = f"EXEC {LOCAL_DB}.dbo.usp_CREATE_CRM_COMPLAINT_FROM_MOBILE_APP @AMEYOTICKETID_FOR_CRM_COMPLAINT='{ticket.get('ticketId')}'"
                print(query)
                complaint_created = True
                execute_with_commit(text(query))
            except Exception as e:
                error_logger(f'Route: {request.path}').error(e)

            print(complaint_created)
        else:
            comments.append('Failed to generate Ameyo Ticket Id.')
    else:
        comments.append('Failed to get the response from Ameyo.')

    if complaint_created:
        # At least one complaint is generated.
        return {'status': True, 'comments': comments}
    else:
        return {'status': False, 'comments': comments}


def create_ticket(egrn,CustomerCode, CustomerName,MobileNo, BranchCode, ameyo_customer_id):
    """
    Function for calling the Ameyo API for creating a ticket.
    @param customer_name: 
    @param mobile_number: 
    @param customer_code: 
    @param ameyo_customer_id: Ameyo customer id
    @param egrn:
    @return: Ameyo API response.
    """

    body = {'subject': f'Complaint Related to EGRN: {egrn}', 'messageText': 'test complaint..',
            'priority': 'LOW', 'externalState': 'COMPLAINT','sourceType': 'CUSTOMER_PORTAL',
            'queueId': '71',
            'customerInfo': {'name': f'{CustomerName}', 'phone1': f'{MobileNo}', 'custom_id': f'{CustomerCode}'},
            'customerId': f'{ameyo_customer_id}', 'customFields': {'d306-5ef767f6-cf-0': 'crm_portal'}}


    # URL for raising a complaint API.
    api_url = "https://jfslcall.fabricspa.com:8443/ameyorestapi/tickets"

    headers = {'Content-Type': 'application/json', 'Authorization': 'fecace70bf6ea0c4'}

    response = requests.post(api_url, data=json.dumps(body), headers=headers)

    # Response in dict
    response = json.loads(response.text)
    log_data = {
        'rewash_response': response,
        'body': body

    }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))
    return response


def get_ameyo_customer_id(MobileNumber):
    """
    Function for getting the ameyo customer code. If no ameyo customer code has been found,
    then the complaint can not be raised.
    @param mobile_number:
    @return: True if the ameyo customer id is found, else False.
    """

    query = f"EXEC GetAmeyoCustomerId @MobileNumber='{MobileNumber}'"
    ameyo_customer_id = CallSP(query).execute().fetchone()
    return_data = None
    if ameyo_customer_id.get('AmeyoCustomerId') is not None:
        if ameyo_customer_id['AmeyoCustomerId'] != 'NA':
            # A valid Ameyo customer Id has been found.
            return_data = ameyo_customer_id['AmeyoCustomerId']
    return return_data


def check_complaint_garment(tag_id,EGRN):
    """
    Function to check whether a particular tag no has complaint or not. (if any)
    @param tag_id: TagId of the garment.
    @return: A dict variable contains complaint flag and rewash count (if any).
    """
    result = {'Complaint': False, 'RewashCount': 0}
    try:

        query = f"EXEC JFSL_UAT.[dbo].[SPFabGetRewashOrCRMComplaintCountBasedOnEGRN] '{EGRN}'"
        complaint_history = CallSP(query).execute().fetchall()

        if len(complaint_history) > 0:
            # Complaint history found.
            for complaint in complaint_history:
                if complaint['TAGNO'] == tag_id:
                    # A match found.
                    result['Complaint'] = True
                    result['RewashCount'] = complaint['REWASHCOUNT']
        else:
            # No complaints found for this Tag Id.
            result = {'Complaint': False, 'RewashCount': 0}
    except Exception as e:
        error_logger(f'Ameyo: {inspect.stack()[0].function}()').error(e)

    return result


def get_complaints_from_egrn(egrn):
    """
    Getting the complaints based on given EGRN.
    @param egrn:
    @return: SP result
    """
    query = f" EXEC JFSL_UAT.Dbo.SPFabGetRewashOrCRMComplaintCountBasedOnEGRN @EGRN ='{egrn}'"
    print(query)
    complaint_history = CallSP(query).execute().fetchall()
    return complaint_history

def rewash(order_details, rewash_garment_list):
    """
    Function to rewash the garments.
    @param order_details:
    @param rewash_garment_list:
    @return: True if successfully rewashed, False if not.
    """
    rewashed = False
    time_slot_id = None
    time_slot_from = None
    time_slot_to = None
    permit_to_rewash = True

    # Getting the time slot details.
    if order_details.PickupRequestId is not None:
        # This is a normal order, not a walk in.
        # Select the time slots from this pickup request row.
        pickup_request_details = db.session.query(PickupRequest).filter(
            PickupRequest.PickupRequestId == order_details.PickupRequestId).one_or_none()
        if pickup_request_details is not None:
            time_slot_id = pickup_request_details.PickupTimeSlotId
            time_slot_from = pickup_request_details.TimeSlotFrom
            time_slot_to = pickup_request_details.TimeSlotTo
    else:
        # This is a walk in order. So no pickup request id will be present.
        # Getting the time slots from the pickup requests table.
        time_slot = db.session.query(PickupTimeSlot).filter(PickupTimeSlot.BranchCode == order_details.BranchCode,
                                                            PickupTimeSlot.DefaultFlag == 1, PickupTimeSlot.IsActive == 1).one_or_none()

        if time_slot is not None:
            time_slot_id = time_slot.PickupTimeSlotId
            time_slot_from = time_slot.TimeSlotFrom
            time_slot_to = time_slot.TimeSlotTo
    if order_details.DeliveryAddressId is not None:
        address_id = order_details.DeliveryAddressId
    else:
        address = db.session.query(DeliveryRequest).filter(DeliveryRequest.OrderId == order_details.OrderId).one_or_none()
        address_id = address.CustAddressId

    # Setting up the new PickupRequest object.
    new_pickup_request = PickupRequest(
        CustomerId=order_details.CustomerId,
        PickupDate=get_today(),
        BranchCode=order_details.BranchCode,
        PickupTimeSlotId=time_slot_id,
        TimeSlotFrom=time_slot_from,
        TimeSlotTo=time_slot_to,
        CustAddressId=address_id,
        PickupSource='Rewash',
        PickupStatusId=2,
        DUserId=order_details.DUserId,
        RecordCreatedDate=get_current_date(),
        RecordLastUpdatedDate=get_current_date()
    )

    # Saving the new pickup request.
    db.session.add(new_pickup_request)
    db.session.commit()

    # After creating the pickup request data, generate BookingId.
    query = f"EXEC {LOCAL_DB}.dbo.[USP_INSERT_ADHOC_PICKUP_FROM_MOBILEAPP_TO_FABRICARE] @PickUprequestId={new_pickup_request.PickupRequestId}"
    execute_with_commit(text(query))

    # Getting the BookingId. If BookingId is not generated,rewash order can't be created.
    booking_id = db.session.query(PickupRequest.BookingId).filter(
        PickupRequest.PickupRequestId == new_pickup_request.PickupRequestId).one_or_none()
    if booking_id is not None:
        if booking_id.BookingId is not None:
            booking_id = booking_id.BookingId
    else:
        # BookingId is not generated.
        permit_to_rewash = False

    if permit_to_rewash:
        address_id = None
        if order_details.PickupAddressId is None:
            # This will be a walk-in order. In case of a walk in order, select the address 1
            # of the customer.
            customer_address = db.session.query(CustomerAddres.CustAddressId).filter(
                CustomerAddres.CustomerId == order_details.CustomerId, CustomerAddres.AddressName == 'Address 1').limit(
                1).one_or_none()

            if customer_address is not None:
                # A valid first address is found for the customer.
                address_id = customer_address.CustAddressId
            else:
                # No valid first address found for the customer. Rewash can not be performed.
                info_logger(f'Rewash - No valid first address found for the customer (Id: {order_details.CustomerId}).')
                return False

        else:
            address_id = order_details.PickupAddressId

        # Creating a new re wash order.
        # Basic, discount and tax amounts will be 0.
        new_rewash_order = Order(
            OrderCode=order_details.OrderCode,
            EGRN=None,
            CustomerId=order_details.CustomerId,
            BranchCode=order_details.BranchCode,
            PickupRequestId=new_pickup_request.PickupRequestId,
            BookingId=booking_id,
            PickupAddressId=address_id,
            DeliveryAddressId=address_id,
            PickupDate=get_today(),
            DUserId=order_details.DUserId,
            Remarks=order_details.Remarks,
            # DiscountCode=order_details.DiscountCode,
            DiscountCode=None,
            CouponCode=order_details.CouponCode,
            LoyalityPoints=order_details.LoyalityPoints,
            # Rewash type.
            OrderTypeId=2,
            OrderDate=get_current_date(),
            EstDeliveryDate=None,
            BasicAmount=0,
            Discount=0,
            ServiceTaxAmount=0,
            OrderAmount=0,
            OrderStatusId=1
        )

        # Adding the new rewash order into the DB.
        db.session.add(new_rewash_order)
        db.session.commit()

        new_order_id = new_rewash_order.OrderId

        # Marking the pickup request as 3, i.e. completed.
        pickup_request = db.session.query(PickupRequest).filter(
            PickupRequest.PickupRequestId == new_pickup_request.PickupRequestId).one_or_none()
        if pickup_request is not None:
            pickup_request.PickupStatusId = 3
            db.session.commit()

        # After creating the rewash order, create a new order garment for each rewash garments.
        for rewash_garment in rewash_garment_list:

            order_garment_details = db.session.query(OrderGarment).filter(
                OrderGarment.OrderGarmentId == rewash_garment['order_garment_id']).one_or_none()

            if order_details is not None:
                # Same garment needs to be inserted again as a new order garment.
                # Basic, discount and tax amounts will be 0.
                new_order_garment = OrderGarment(
                    OrderId=new_order_id,
                    GarmentId=order_garment_details.GarmentId,
                    ServiceTypeId=order_garment_details.ServiceTypeId,
                    ServiceTatId=order_garment_details.ServiceTatId,
                    TagId=None,
                    GarmentStatusId=1,
                    GarmentBrand=order_garment_details.GarmentBrand,
                    GarmentColour=order_garment_details.GarmentColour,
                    GarmentSize=order_garment_details.GarmentSize,
                    QCStatus=None,
                    CRMComplaintId=order_garment_details.CRMComplaintId,
                    BasicAmount=0,
                    Discount=0,
                    ServiceTaxAmount=0,
                    EstDeliveryDate=None
                )

                # Adding the garment into the DB.
                db.session.add(new_order_garment)
                db.session.commit()

                # After adding the garment id, calculate the EstDeliveryDate value and update it.
                est_delivery = get_est_delivery_date(new_order_garment.OrderGarmentId)

                # Updating the EstDeliveryDate in the OrderGarments table.
                update_est_delivery_date(new_order_garment.OrderGarmentId, est_delivery)

                # Updating the EstDeliveryDate of the Orders table.
                set_max_est_delivery_date(new_order_id)

        # Generating an EGRN for the new rewash order.
        query = f"EXEC {SERVER_DB}.dbo.App_OrderCreation_Detail @branchcode='{order_details.BranchCode}',@orderid={new_order_id}"
        egrn = CallSP(query).execute().fetchone()
        if egrn:
            egrn = egrn['EGRN']
            # Updating the order with the EGRN.
            try:
                # Saving the order with the newly generated EGRN.
                new_order_details = db.session.query(Order).filter(
                    Order.OrderId == new_order_id).one_or_none()
                if new_order_details is not None:
                    # Saving the EGRN to the rewash order.
                    new_order_details.EGRN = egrn
                    db.session.commit()
                    rewashed = True
            except Exception as e:
                db.session.rollback()
                error_logger(f'Ameyo: {inspect.stack()[0].function}()').error(e)

    return rewashed


import uuid
import haversine as hs

def rewash(user_id, rewash_garment_list, TRNNo, TagNo, Duserlat, Duserlong, CustLat,CustLong ,BranchCode):
    """
    Function to rewash the garments.
    @param order_details:
    @param rewash_garment_list:
    @return: True if successfully rewashed, False if not.
    """
    booking_id = None
    rewashed = False
    GarmentAdded = False
    permit_to_rewash = False

    query = f""" EXEC JFSL.Dbo.SPPendingDeliveriesDetailedScreen @user_id = {user_id} ,@TRNNo = '{TRNNo}',@PendingDeliveriesScreen = {1}"""
    order_detail = CallSP(query).execute().fetchall()
    log = {
        "query": query,
        "order_detail": order_detail
    }
    info_logger(f'Route: {request.path}').info(json.dumps(log))
    order_detail = order_detail[0]

    # Getting the time slot details.
    query = f"""EXEC JFSL.DBO.SPPickupInfoInsertValidationCustApp @BranchCode ='{order_detail.get('BranchCode')}',@CustomerCode ='{order_detail.get('CustomerCode')}',@PickupDate = '{get_today()}' """
    result = CallSP(query).execute().fetchone()
    log = {
        "result": result,
        "result": order_detail.get('BranchCode'),
        "CustomerCode": order_detail.get('CustomerCode')
    }
    info_logger(f'Route: {request.path}').info(json.dumps(log))
    # result = result[0]

    if result.get("Message") == "Success":
        log = {

            "result": result.get("Message")
        }
        info_logger(f'Route: {request.path}').info(json.dumps(log))

        DeliveryFlat = ''
        DeliveryAddress = ''
        PermanentFlat = ''
        PermanantAddress = ''
        LattitudePer = 0.0
        LongitudePer = 0.0
        Lattitude = 0.0
        Longitude = 0.0

        if order_detail.get('AddressType') == 'delivery':
            DeliveryFlat = order_detail.get('AddressLine1')
            DeliveryAddress = order_detail.get('AddressLine2')
            Lattitude = order_detail.get('Lat')
            Longitude = order_detail.get('Long')
        else:
            PermanentFlat = order_detail.get('AddressLine1')
            PermanantAddress = order_detail.get('AddressLine2')
            LattitudePer = order_detail.get('Lat')
            LongitudePer = order_detail.get('Long')

        unicode1 = uuid.uuid4()
        TimeSlotFrom = '9:00 AM'
        TimeSlotTo = '11:00 AM'
        query = f"""
                EXEC JFSL.Dbo.SPPickupInfoInsertCustApp
                @GUID_Value = '{unicode1}',
                @DUserID = {user_id},
                @BranchCode = '{order_detail.get('BranchCode')}',
                @CustomerCode = '{order_detail.get('CustomerCode')}',
                @DeliveryFlat = '{DeliveryFlat}',
                @PermanentFlat = '{PermanentFlat}',
                @DeliveryAddress = '{DeliveryAddress}',
                @PermanantAddress = '{PermanantAddress}',
                @Lattitude = '{Lattitude}',
                @LattitudePer = '{LattitudePer}',
                @Longitude = '{Longitude}',
                @LongitudePer = '{LongitudePer}',
                @PinCode = {0},
                @PermanantPinCode = '{0}',
                @PickupTimeSlotId = '{0}',
                @PickupDate = '{get_today()}',
                @PickupSource = {'Rewash'},
                @TimeSlotFrom = '{TimeSlotFrom}',
                @TimeSlotTo = '{TimeSlotTo}',
                @ServiceTatId = {1},
                @ValidateCouponCode = {"null"},
                @ValidateDiscountCode = {"null"},
                @CodeFromER = {'null'},
                @ISERCoupon = {"null"},
                @ERRequestID ={"null"},
                @GeoLocation = '{order_detail.get('GeoLocation')}'
                        """
        log = {
            "query": query,
        }
        info_logger(f'Route: {request.path}').info(json.dumps(log))

        execute_with_commit(text(query))
        permit_to_rewash = True

        # Getting the BookingId. If BookingId is not generated,rewash order can't be created.

        booking_id = db.session.execute(
            text(
                "SELECT BookingID  FROM JFSL.dbo.PickupInfo (nolock) WHERE PickupID = :unicode"),
            {"unicode": unicode1}
        ).fetchone()

        booking_id = booking_id[0]
        log = {
            "booking_id": booking_id,

        }
        info_logger(f'Route: {request.path}').info(json.dumps(log))
        if booking_id:
            permit_to_rewash = True



    else:
        booking_id = result.get("BookingID")
        permit_to_rewash = True
    log = {
        "permit_to": permit_to_rewash,
    }
    info_logger(f'Route: {request.path}').info(json.dumps(log))
    if permit_to_rewash:

        for garment in rewash_garment_list:
            TagNo = garment['TagNo']
            query = f""" EXEC JFSL.Dbo.SPFabComplaintResolutionCheck @TagNo = '{TagNo}' """
            log = {
                "query": query,

            }
            info_logger(f'Route: {request.path}').info(json.dumps(log))
            result = CallSP(query).execute().fetchall()

            result = result[0]

            garment['BookingID'] = booking_id
            garment['OldOrderGarmentID'] = garment['order_garment_id']
            garment['OrderGarmentID'] = uuid.uuid4()
            garment['ServiceTypeId'] = result.get('ServiceTypeId')
            garment['ServiceTatId'] = result.get('ServiceTatId')
            garment['GarmentId'] = result.get('GarmentID')
            garment['GarmentName'] = result.get('GarmentName')
            garment['OrderInstructionIDs'] = None
            garment['GarmentCount'] = 1
            garment['price_list_id'] = 0
            garment['price'] = 0
            garment['UOMID'] = 0
            garment['OrderIssueIDs'] = None
            garment['isChanged'] = None
            garment['OrderIssueIDs'] = None
            garment['CRMComplaintId'] = result.get('CRMComplaintId')
            garment['OrderTypeId'] = 2

            db.session.execute(text("""
                                      INSERT INTO JFSL.Dbo.FabTempOrderGarments ( OrderGarmentID,   BookingID,OrderTypeId,  GarmentCount,   ServiceTatId,   ServiceTypeId,  GarmentId,GarmentName,  Price,  PriceListId,    UOMID,  CRMComplaintId, OrderInstructionIDs,    IsChanged, OrderIssueIDs,OldOrderGarmentID) 
                                      VALUES (:OrderGarmentID,:BookingID,:OrderTypeId,:GarmentCount,  :ServiceTatId, :ServiceTypeId,:GarmentId,:GarmentName, :price, :price_list_id, :UOMID,:CRMComplaintId,:OrderInstructionIDs, :isChanged, :OrderIssueIDs,:OldOrderGarmentID)

                                  """), garment)

            db.session.commit()
            GarmentAdded = True
            log = {
                "GarmentAdded": GarmentAdded,

            }
            info_logger(f'Route: {request.path}').info(json.dumps(log))

        if GarmentAdded:
            DuserDistance = 0.0
            StoreDistance = 0.0
            CustomerLocation = (CustLat, CustLong)
            DeliveryUserLocation = (Duserlat, Duserlong)

            # Calculate distance between delivery user and customer
            DuserDistance = hs.haversine(CustomerLocation, DeliveryUserLocation)
            if DuserDistance >= 1:
                km_part = int(DuserDistance)
                meters_part = (DuserDistance - km_part) * 1000
                DuserDistance = f"{km_part} km {int(meters_part)} m"
            else:
                DuserDistance = f"{int(DuserDistance * 1000)} m"

            # Get branch info and calculate distance
            BranchLocation = db.session.execute(
                text("SELECT Lat, Long, BranchName FROM JFSL_UAT.dbo.Branchinfo WHERE BranchCode = :BranchCode"),
                {"BranchCode": BranchCode}
            ).fetchone()



            branch_coords = (float(BranchLocation.Lat), float(BranchLocation.Long))
            StoreDistance = hs.haversine(branch_coords, DeliveryUserLocation)
            if StoreDistance >= 1:
                km_part = int(StoreDistance)
                meters_part = (StoreDistance - km_part) * 1000
                StoreDistance = f"{km_part} km {int(meters_part)} m"
            else:
                StoreDistance = f"{int(StoreDistance * 1000)} m"

            tag_counts = sum(1 for item in rewash_garment_list if 'TagNo' in item)
            query = f""" JFSL.Dbo.SPFabOldEGRNRewashOrderGarmentsInsert @PickupID ='{unicode1}',@DUserID ={user_id},@BookingID = {booking_id},@BranchCode = '{order_detail.get('BranchCode')}'                
                                                ,@CustomerCode = '{order_detail.get('CustomerCode')}',@OrderType = {2},@RewashReason = '' ,@OLDEGRNNo = '{order_detail.get('EGRN')}',@Remarks = ''                         
                                                ,@DuserDistance = {0.0} ,@AssignedStoreUser = '{1}',@StoreDistance = {StoreDistance} , @Distance = {DuserDistance},@DuserLat = {Duserlat} ,@DuserLong = {Duserlong},@GarmentsCount={tag_counts}"""

            log = {
                "query": query,

            }
            info_logger(f'Route: {request.path}').info(json.dumps(log))
            execute_with_commit(text(query))

            rewashed = True

    return rewashed


def adhoc_rewash(complaint_garment_list, user_id, time_slot_id, address_id, branch_code, customer_id, booking_id, pickup_request_id, lat, longitude, geo_location):
    """
    Function to rewash the garments.
    @param complaint_garment_list:
    @param user_id:
    @param time_slot_id:
    @param branch_code:
    @param customer_id:
    @param address_id
    @param booking_id
    @return: True if successfully rewashed, False if not.
    """
    final_rewash = []
    time_slot = db.session.query(PickupTimeSlot.PickupTimeSlotId,
                                     PickupTimeSlot.TimeSlotFrom,
                                     PickupTimeSlot.TimeSlotTo).filter(
            PickupTimeSlot.BranchCode == branch_code,
            PickupTimeSlot.DefaultFlag == 1,
            PickupTimeSlot.IsActive == 1
        ).first()

    if time_slot is None:
        # No time slot present, so try with DefaultFlag.
        time_slot = db.session.query(PickupTimeSlot.PickupTimeSlotId,
                                     PickupTimeSlot.TimeSlotFrom,
                                     PickupTimeSlot.TimeSlotTo).filter(
            PickupTimeSlot.BranchCode == branch_code,
            PickupTimeSlot.DefaultFlag == 1,
            PickupTimeSlot.IsActive == 1
        ).first()

    permit_to_rewash = True
    if booking_id is None:
        # pickup_request_details = db.session.query(PickupRequest).filter(PickupRequest.PickupRequestId == pickup_request_id).one_or_none()
        # if pickup_request_details.BookingId is not None:
        if pickup_request_id is None:
            # # Setting up the new PickupRequest object.
            new_pickup_request = PickupRequest(
                CustomerId=customer_id,
                PickupDate=get_today(),
                BranchCode=branch_code,
                PickupTimeSlotId=time_slot.PickupTimeSlotId,
                TimeSlotFrom=time_slot.TimeSlotFrom,
                TimeSlotTo=time_slot.TimeSlotTo,
                CustAddressId=address_id,
                PickupSource='Rewash',
                PickupStatusId=2,
                DUserId=user_id,
                RecordCreatedDate=get_current_date(),
                RecordLastUpdatedDate=get_current_date(),
                Lat=lat,
                Long=longitude,
                GeoLocation=geo_location
            #     CompletedDate=get_today(),
            #     CompletedBy = user_id
            )
            # # Saving the new pickup request.
            db.session.add(new_pickup_request)
            db.session.commit()
            # pickup_request_details.RecordLastUpdatedDate = get_current_date()
            # # pickup_request_details.PickupStatusId = 2
            # db.session.commit()

            # After creating the pickup request data, generate BookingId.
            # query = f"EXEC {LOCAL_DB}.dbo.[USP_INSERT_ADHOC_PICKUP_FROM_MOBILEAPP_TO_FABRICARE] @PickUprequestId={new_pickup_request.PickupRequestId}"
            # execute_with_commit(text(query))
            # Getting the BookingId. If BookingId is not generated,rewash order can't be created.
            pickup_details = db.session.query(PickupRequest).filter(
                PickupRequest.PickupRequestId == new_pickup_request.PickupRequestId).one_or_none()
            pickup_request_id = new_pickup_request.PickupRequestId
        else:
            # query = f"EXEC {LOCAL_DB}.dbo.[USP_INSERT_ADHOC_PICKUP_FROM_MOBILEAPP_TO_FABRICARE] @PickUprequestId={pickup_request_id}"
            # execute_with_commit(text(query))
            pickup_details = db.session.query(PickupRequest).filter(
                PickupRequest.PickupRequestId == pickup_request_id).one_or_none()

    else:
        pickup_details = db.session.query(PickupRequest).filter(PickupRequest.BookingId == booking_id).one_or_none()
        # pickup_details.RecordLastUpdatedDate = get_current_date()
        # pickup_details.PickupStatusId = 2
        # pickup_details.CompletedDate = get_today()
        # pickup_details.CompletedBy = user_id
        # db.session.commit()
        pickup_request_id = pickup_details.PickupRequestId
    if pickup_details is not None:
        permit_to_rewash = True
        # if pickup_details.BookingId is not None:
        #     booking_id = pickup_details.BookingId
    else:
        # BookingId is not generated.
        permit_to_rewash = False

    if permit_to_rewash:
        order_details = db.session.query(Order).filter(Order.PickupRequestId == pickup_request_id, Order.IsDeleted == 0).one_or_none()
        if order_details is None:
            new_rewash_order = Order(
                # OrderCode=order_details.OrderCode,
                EGRN=None,
                CustomerId=customer_id,
                BranchCode=branch_code,
                PickupRequestId=pickup_request_id,
                # BookingId=booking_id,
                PickupAddressId=address_id,
                DeliveryAddressId=address_id,
                PickupDate=get_today(),
                DUserId=user_id,
                # Rewash type.
                OrderTypeId=2,
                OrderDate=get_current_date(),
                EstDeliveryDate=None,
                BasicAmount=0,
                Discount=0,
                ServiceTaxAmount=0,
                OrderAmount=0,
                OrderStatusId=1
            )
            # Adding the new rewash order into the DB.
            db.session.add(new_rewash_order)
            db.session.commit()

            new_order_id = new_rewash_order.OrderId
        else:
            new_order_id = order_details.OrderId

            order_garments = db.session.query(OrderGarment.OrderGarmentId).filter(OrderGarment.OrderId == new_order_id).all()
            if order_garments is not None:
                order_garments = SerializeSQLAResult(order_garments).serialize()
                log_data = {
                    'already present garments': order_garments
                    }
                info_logger(f'Route: {request.path}').info(json.dumps(log_data))
                for garments in order_garments:
                    order_garment_id = garments['OrderGarmentId']
                    order_garment = db.session.query(OrderGarment).filter(OrderGarment.OrderGarmentId == order_garment_id).one_or_none()
                    order_garment.IsDeleted = 1
                    db.session.commit()
            else:
                pass

        # Marking the pickup request as 3, i.e. completed.
        pickup_request = db.session.query(PickupRequest).filter(
            PickupRequest.PickupRequestId == pickup_request_id).one_or_none()
        if pickup_request is not None:
            pickup_request.PickupStatusId = 2
            pickup_request.RecordLastUpdatedDate = get_current_date()
            db.session.commit()

        # After creating the rewash order, create a new order garment for each rewash garments.
        for rewash_garment in complaint_garment_list:
            new_rewash_details = {}
            order_garment_details = db.session.query(OrderGarment).filter(
                OrderGarment.OrderGarmentId == rewash_garment['order_garment_id']).one_or_none()
            if order_garment_details is not None:

                new_order_garment = OrderGarment(
                    OrderId=new_order_id,
                    GarmentId=order_garment_details.GarmentId,
                    ServiceTypeId=order_garment_details.ServiceTypeId,
                    ServiceTatId=order_garment_details.ServiceTatId,
                    TagId=None,
                    GarmentStatusId=1,
                    GarmentBrand=order_garment_details.GarmentBrand,
                    GarmentColour=order_garment_details.GarmentColour,
                    GarmentSize=order_garment_details.GarmentSize,
                    QCStatus=None,
                    # CRMComplaintId=crm_complaint_id,
                    BasicAmount=0,
                    Discount=0,
                    ServiceTaxAmount=0,
                    EstDeliveryDate=None
                )
                # Adding the garment into the DB.
                db.session.add(new_order_garment)
                db.session.commit()

                new_rewash_details['new_garment_id'] = new_order_garment.OrderGarmentId
                new_rewash_details['old_garment_id'] = rewash_garment['order_garment_id']
                new_rewash_details['complaint_status'] = rewash_garment['crm_complaint_status']
                new_rewash_details['complaint_id'] = rewash_garment['complaint_id']
                final_rewash.append(new_rewash_details)
                vas_details = db.session.query(OrderInstruction).filter(
                    OrderInstruction.OrderId == order_garment_details.OrderId,
                    OrderInstruction.OrderGarmentId == order_garment_details.OrderGarmentId).all()
                if vas_details is not None:
                    for vas in vas_details:
                        new_instruction = OrderInstruction(OrderId=new_order_id,
                                                           OrderGarmentId=new_order_garment.OrderGarmentId,
                                                           InstructionId=vas.InstructionId, IsDeleted=0)
                        db.session.add(new_instruction)
                        db.session.commit()

                # After adding the garment id, calculate the EstDeliveryDate value and update it.
                est_delivery = get_est_delivery_date(new_order_garment.OrderGarmentId)

                # Updating the EstDeliveryDate in the OrderGarments table.
                update_est_delivery_date(new_order_garment.OrderGarmentId, est_delivery)

                # Updating the EstDeliveryDate of the Orders table.
                set_max_est_delivery_date(new_order_id)

    return {"new_order_id": new_order_id, "final_rewash": final_rewash}

def rewash_complaint(egrn,CustomerCode, CustomerName,MobileNo, BranchCode ,AmeyoTicketId):
    complaint_status = False

    ameyo_customer_id = get_ameyo_customer_id(MobileNo)
    if ameyo_customer_id:
        # Calling the Ameyo API to create a ticket.
        ticket = create_ticket(CustomerName, MobileNo,
                               CustomerCode,
                               ameyo_customer_id, egrn)
        print(ticket)
        if ticket is not None:
            # Received the response the API.
            if ticket['ticketId']:
                try:
                    AmeyoTicketId = ticket.get('ticketId')
                    JFSLTicketId = ticket['customId']
                    TicketSubject = ticket['subject']
                    AmeyoTicketSourceType = ticket['sourceType']
                    AmeyoTicketStatus = ticket['externalState']
                    CampaignId = ticket['campaignId']
                    QueueId = ticket['queueId']
                    AssignedUserId = ticket['assignedUserId']
                    try:
                        query = f"""EXEC JFSL_UAT.Dbo.EXEC SPFabExistsComplaintsUpdate @AmeyoTicketId ='{AmeyoTicketId}' ,@JFSLTicketId ='{JFSLTicketId}' ,@TicketSubject ='{TicketSubject}'  
                            ,@AmeyoTicketSourceType ='{AmeyoTicketSourceType}' ,@AmeyoTicketStatus ='{AmeyoTicketStatus}' ,@CampaignId ='{CampaignId}' ,@QueueId ='{QueueId}', @AssignedUserId ='{AssignedUserId}'
                            ,@TagId=''"""
                        execute_with_commit(text(query))
                    except Exception as e:
                        error_logger(f'Ameyo: {inspect.stack()[0].function}()').error(e)
                except Exception as e:
                    error_logger(f'Ameyo: {inspect.stack()[0].function}()').error(e)

            query = f"EXEC {LOCAL_DB}.dbo.usp_CREATE_CRM_COMPLAINT_FROM_MOBILE_APP " \
                    f"@AMEYOTICKETID_FOR_CRM_COMPLAINT='{ticket['ticketId']}' "

            execute_with_commit(text(query))
    else:
        query = f"EXEC {LOCAL_DB}.dbo.usp_CREATE_CRM_COMPLAINT_FROM_MOBILE_APP " \
                f"@AMEYOTICKETID_FOR_CRM_COMPLAINT='{AmeyoTicketId}'"
        log_data = {
            'SP-update-complaintId': query
        }
        info_logger(f'Route: {request.path}').info(json.dumps(log_data))
        execute_with_commit(text(query))


    return True

def same_order_complaint(single_ameyo_orders, customer_id):
    complaint_status = False
    customer_details = db.session.query(Customer.CustomerId, Customer.CustomerCode,
                                        Customer.CustomerName,
                                        Customer.MobileNo, Customer.BranchCode).filter(
        Customer.CustomerId == customer_id).one_or_none()
    ameyo_customer_id = get_ameyo_customer_id(customer_details.MobileNo)
    if ameyo_customer_id:

        for single_order in single_ameyo_orders:

            egrn = db.session.query(Order.EGRN, Order.OrderId).filter(
                Order.OrderId == single_order['order_id']
            ).one_or_none()
            ticket = create_ticket(customer_details.CustomerName, customer_details.MobileNo,
                                   customer_details.CustomerCode,
                                   ameyo_customer_id, egrn.EGRN)
            if ticket is not None:
                # Received the response the API.
                if ticket['ticketId']:
                    complaint_status = True
                    for complaint_id in single_order["complaint_id"]:
                        try:
                            complaint_details = db.session.query(Complaint).filter(
                                Complaint.Id == complaint_id).one_or_none()

                            complaint_details.AmeyoTicketId = ticket['ticketId']
                            complaint_details.JFSLTicketId = ticket['customId']
                            complaint_details.TicketSubject = ticket['subject']
                            complaint_details.AmeyoTicketSourceType = ticket['sourceType']
                            complaint_details.AmeyoTicketStatus = ticket['externalState']
                            complaint_details.CampaignId = ticket['campaignId']
                            complaint_details.QueueId = ticket['queueId']
                            complaint_details.AssignedUserId = ticket['assignedUserId']
                            try:
                                # Inserting the new garment complaint in the DB.
                                db.session.commit()
                            except Exception as e:
                                error_logger(f'Ameyo: {inspect.stack()[0].function}()').error(e)
                        except Exception as e:
                            error_logger(f'Ameyo: {inspect.stack()[0].function}()').error(e)

                    query = f"EXEC {LOCAL_DB}.dbo.usp_CREATE_CRM_COMPLAINT_FROM_MOBILE_APP " \
                            f"@AMEYOTICKETID_FOR_CRM_COMPLAINT='{ticket['ticketId']}' "
                    execute_with_commit(text(query))
                    log_data = {
                        'same_order_ameyo': query,
                    }
                    info_logger(f'Route: {request.path}').info(json.dumps(log_data))
    return complaint_status

def active_or_not(complaint_id):
    rewash_status = True
    query = f"EXEC {SERVER_DB}.dbo.GetRewashOrderstatus @ComplaintID='{complaint_id}'"
    order_status = CallSP(query).execute().fetchall()
    if order_status is not None:
        for status in order_status:
            if status['OrderStatus'] == 'Active' and status['GarmentStatus'] != 'Transfer in at CDC':
                rewash_status = True
                break
            elif status['OrderStatus'] == 'cancelled' or status['OrderStatus'] == 'Completed' or status['GarmentStatus'] == 'Transfer in at CDC':
                rewash_status = False
    return rewash_status