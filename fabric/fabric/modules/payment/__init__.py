"""
------------------------
Payments module
Fabric's payment flow related logic & functions.
------------------------
Coded by: Krishna Prasad K
© Jyothy Fabricare Services LTD.
------------------------
"""
import math
from fabric.generic.classes import CallSP
from fabric.generic.functions import get_current_date
from fabric.generic.loggers import error_logger, info_logger
import requests
from fabric.settings.project_settings import SERVER_DB, CURRENT_ENV
from fabric import db
from fabric.modules.models import TransactionInfo, TransactionPaymentInfo, OrderGarment, Order, DeliveryGarment, \
    DeliveryRequest, Customer
from sqlalchemy import func, text
import fabric.modules.easyrewardz.queries as er_queries
import inspect
import fabric.modules.easyrewardz as er_module
from .queries import update_transaction_info_with_lp_details, insert_transaction_payment_info_with_coupon_details
from fabric.blueprints.delivery_app import queries as delivery_controller_queries
from fabric.generic.loggers import error_logger, info_logger
from flask import request
import json


def get_unsettled_orders(customer_code):
    """
    Function that calls the unsettled orders stored procedure and returns the result.
    @param customer_code: POS customer code.
    @return: List of unsettled orders of a customer.
    """
    query = f"EXEC {SERVER_DB}.dbo.[OrderListForGenerateInvoice] @CustomerCode='{customer_code}', @BrandCode='PCT0000001'"

    # Executing the SP and retrieving the result.
    unsettled_orders = CallSP(query).execute().fetchall()

    # Returning the result.
    return unsettled_orders


def get_unsettled_garments(customer_code, egrn):
    """
    Function that calls the unsettled garments stored procedure and returns the result.
    @param customer_code: POS customer code.
    @param egrn: EGRN of the order.
    @return: List of unsettled orders of a customer.
    """
    query = f"EXEC {SERVER_DB}.dbo.[GetGarmentListForGenerateInvoiceForMobileApp] @CustomerCode='{customer_code}', @BrandCode='PCT0000001',@egrn={egrn}"

    # Executing the SP and retrieving the result.
    unsettled_garments = CallSP(query).execute().fetchall()

    # Returning the result.
    return unsettled_garments


# Edited by MMM removing code bcz of trn is not used
def get_unsettled_garments_with_complaints(customer_code, egrn, pos_order_garment_ids):
    """
    Function that calls the unsettled garments(with complaints) stored procedure and returns the result.
    @param customer_code: POS customer code.
    @param egrn: EGRN of the order.
    @return: List of unsettled orders of a customer.
    """

    query = f"EXEC {SERVER_DB}.dbo.[GetGarmentListForGenerateInvoiceForMobileAppwithComplaintGarmentwise] @CustomerCode='{customer_code}', @BrandCode='PCT0000001',@egrn={egrn},@ordergarmentids='{','.join(map(str, pos_order_garment_ids))}'"

    # Executing the SP and retrieving the result.
    unsettled_garments = CallSP(query).execute().fetchall()
    # Returning the result.
    return unsettled_garments


# Edited by MMM removing code bcz of trn is not used


def get_unsettled_egrn_details(customer_code, egrn):
    """
    This function checks whether the EGRN is found in the unsettled orders SP or not. If the EGRN is found,
    then returns the details.
    @param given_egrn: EGRN provided as param.
    @param customer_code: POS customer code.
    @return: dict variable consists of amount to pay and list of egrn details.
    """
    # Getting the unsettled orders.
    unsettled_orders = get_unsettled_orders(customer_code)
    # Unsettled orders belongs to the given egrn.
    details = {}
    # Result variable.
    result = {'initial_amount': 0, 'details': details}
    if len(unsettled_orders) > 0:
        # Unsettled orders are present.
        # Checks if the given EGRN under this EGRN is present in the list or not.
        for unsettled_order in unsettled_orders:
            # Checking this EGRN is same as given EGRN, then get the order details.
            if unsettled_order['UNSETTLEDORDERNUMBER'] == egrn:
                result['details'] = unsettled_order
                result['initial_amount'] = unsettled_order['PAYABLEAMOUNT']
                break
    # Returning the result variable.
    return result


def get_unsettled_egrn_details_garment_wise(customer_code, egrn, pos_order_garment_ids):
    """
    This function checks whether the given garment ids found in the unsettled garments SP or not. If the garments are found,
    then returns the details.
    @param given_egrn: EGRN provided as param.
    @param customer_code: POS customer code.
    @param pos_order_garment_ids: List of POS order garment ids (Garments that are needed to be delivered - explicitly given).
    @return: dict variable consists of amount to pay and list of egrn details.
    """
    # Getting the unsettled orders.
    unsettled_garments = get_unsettled_garments(customer_code, egrn)

    customer_type = ''

    # Based on the customer type, selecting the unsettled order number.
    if len(unsettled_garments) > 0:
        customer_type = unsettled_garments[0]['CUSTOMERTYPE']

    if customer_type == "Monthly":
        unsettled_order_number = unsettled_garments[0]['UNSETTLEDORDERNUMBER']
    else:
        unsettled_order_number = egrn

    # Result variable.
    result = {
        'initial_amount': 0, 'order_garment_ids': '', 'details': {
            'UNSETTLEDORDERNUMBER': unsettled_order_number,
            'ORDERGARMENTID': '',
            'BASICAMOUNT': 0,
            'ROUNDOFF': 0,
            'FINALINVOICEAMOUNT': 0,
            'PAYABLEAMOUNT': 0,
            'GARMENTSCOUNT': len(pos_order_garment_ids),
            'PRODUCTBASICAMOUNT': 0,
            'PRODUCTROUNDOFF': 0,
            'PRODUCTINVOICEAMOUNT': 0
        }
    }

    if len(unsettled_garments) > 0:
        # Unsettled garments are present.
        # Checks if the given POS order garment Id under this EGRN is present in the list or not.
        for unsettled_garment in unsettled_garments:

            # Checking this POS Order garment id is same as given order_garment_id, then get the order details.
            if unsettled_garment['ORDERGARMENTID'] in pos_order_garment_ids:
                if unsettled_garment['CUSTOMERTYPE'].upper() == 'REGULAR':
                    result['initial_amount'] += unsettled_garment['PAYABLEAMOUNT']
                    result['details']['PAYABLEAMOUNT'] += unsettled_garment['PAYABLEAMOUNT']
                else:
                    # This is the monthly customer.
                    result['initial_amount'] = unsettled_garment['PAYABLEAMOUNT']
                    result['details']['PAYABLEAMOUNT'] = unsettled_garment['PAYABLEAMOUNT']
                # Below details are needed for table insertion.
                result['details']['BASICAMOUNT'] += float(unsettled_garment['BASICAMOUNT'])
                result['details']['ROUNDOFF'] += float(unsettled_garment['ROUNDOFF'])

                if unsettled_garment['CUSTOMERTYPE'].upper() == 'REGULAR':
                    result['details']['FINALINVOICEAMOUNT'] += float(unsettled_garment['FINALINVOICEAMOUNT'])
                else:
                    # This is the monthly customer.
                    result['details']['FINALINVOICEAMOUNT'] = float(unsettled_garment['FINALINVOICEAMOUNT'])

                result['details']['PRODUCTBASICAMOUNT'] += float(unsettled_garment['PRODUCTBASICAMOUNT'])
                result['details']['PRODUCTROUNDOFF'] += float(unsettled_garment['PRODUCTROUNDOFF'])
                result['details']['PRODUCTINVOICEAMOUNT'] += float(unsettled_garment['PRODUCTINVOICEAMOUNT'])

    result['order_garment_ids'] = ','.join(map(str, pos_order_garment_ids))
    result['details']['ORDERGARMENTID'] = ','.join(map(str, pos_order_garment_ids))

    if abs(result['details']['ROUNDOFF']) % 0.5 == 0:
        # Rounding the payable amount. Amount with .5 as decimal will be rounded off to higher number (ceiling).
        # in the old fashioned way.
        result['initial_amount'] = int(result['initial_amount'] + math.copysign(0.5, result['initial_amount']))
    else:
        # Rounding the payable amount.
        result['initial_amount'] = round(result['initial_amount'])

    # Returning the result variable.
    return result


# Edited by MMM removing code bcz of trn is not used
def get_unsettled_egrn_details_garment_wise_with_complaints(customer_code, egrn, pos_order_garment_ids):
    """
    This function checks whether the given garment ids found in the unsettled garments SP (Including complaints) or not.
    If the garments are found, then returns the details.
    @param given_egrn: EGRN provided as param.
    @param customer_code: POS customer code.
    @param pos_order_garment_ids: List of POS order garment ids (Garments that are needed to be delivered - explicitly given).
    @return: dict variable consists of amount to pay and list of egrn details.
    """
    # Getting the unsettled orders.
    unsettled_garments = get_unsettled_garments_with_complaints(customer_code, egrn, pos_order_garment_ids)

    customer_type = ''

    # Based on the customer type, selecting the unsettled order number.
    if len(unsettled_garments) > 0:
        customer_type = unsettled_garments[0]['CUSTOMERTYPE']

    if customer_type == "Monthly":
        unsettled_order_number = unsettled_garments[0]['UNSETTLEDORDERNUMBER']
    else:
        unsettled_order_number = egrn

    # Result variable.
    result = {
        'initial_amount': 0, 'order_garment_ids': '', 'details': {
            'UNSETTLEDORDERNUMBER': unsettled_order_number,
            'ORDERGARMENTID': '',
            'BASICAMOUNT': 0,
            'ROUNDOFF': 0,
            'FINALINVOICEAMOUNT': 0,
            'PAYABLEAMOUNT': 0,
            'GARMENTSCOUNT': len(pos_order_garment_ids),
            'PRODUCTBASICAMOUNT': 0,
            'PRODUCTROUNDOFF': 0,
            'PRODUCTINVOICEAMOUNT': 0,
            'BASICAMOUNTWIHTOUTTAX': 0
        }
    }

    if len(unsettled_garments) > 0:
        # Unsettled garments are present.
        # Checks if the given POS order garment Id under this EGRN is present in the list or not.
        for unsettled_garment in unsettled_garments:

            # Checking this POS Order garment id is same as given order_garment_id, then get the order details.
            if unsettled_garment['ORDERGARMENTID'] in pos_order_garment_ids:
                if unsettled_garment['CUSTOMERTYPE'].upper() == 'REGULAR':
                    result['initial_amount'] += unsettled_garment['PAYABLEAMOUNT']
                    result['details']['PAYABLEAMOUNT'] += unsettled_garment['PAYABLEAMOUNT']
                else:
                    # This is the monthly customer.
                    result['initial_amount'] = unsettled_garment['PAYABLEAMOUNT']
                    result['details']['PAYABLEAMOUNT'] = unsettled_garment['PAYABLEAMOUNT']
                # Below details are needed for table insertion.
                result['details']['BASICAMOUNT'] += float(unsettled_garment['BASICAMOUNT'])
                result['details']['ROUNDOFF'] += float(unsettled_garment['ROUNDOFF'])
                if unsettled_garment['CUSTOMERTYPE'].upper() == 'REGULAR':
                    result['details']['FINALINVOICEAMOUNT'] += float(unsettled_garment['FINALINVOICEAMOUNT'])
                else:
                    # This is the monthly customer.
                    result['details']['FINALINVOICEAMOUNT'] = float(unsettled_garment['FINALINVOICEAMOUNT'])
                result['details']['PRODUCTBASICAMOUNT'] += float(unsettled_garment['PRODUCTBASICAMOUNT'])
                result['details']['PRODUCTROUNDOFF'] += float(unsettled_garment['PRODUCTROUNDOFF'])
                result['details']['PRODUCTINVOICEAMOUNT'] += float(unsettled_garment['PRODUCTINVOICEAMOUNT'])
                result['details']['BASICAMOUNTWIHTOUTTAX'] += float(unsettled_garment['BASICAMOUNTWIHTOUTTAX'])

    result['order_garment_ids'] = ','.join(map(str, pos_order_garment_ids))
    result['details']['ORDERGARMENTID'] = ','.join(map(str, pos_order_garment_ids))

    if abs(result['details']['ROUNDOFF']) % 0.5 == 0:
        # Rounding the payable amount. Amount with .5 as decimal will be rounded off to higher number (ceiling).
        # in the old fashioned way.
        result['initial_amount'] = int(
            result['initial_amount'] + math.copysign(0.5, result['initial_amount']))
    else:
        # Rounding the payable amount.
        result['initial_amount'] = round(result['initial_amount'])
    # Returning the result variable.
    return result
    # Edited by MMM removing code bcz of trn is not used


def get_global_invoice_discount_details(egrn, order_garment_ids):
    """
    Function for checking whether the EGRN have global discount code attached to it or not.
    @param kwargs: Params can be either egrn or dcn.
    @param order_garment_ids POS order garment ids present in the current EGRN.
    @return: SP result.
    """

    query = f"EXEC {SERVER_DB}.dbo.[GetDiscountAmount] @ApplyOn=8,@EGRNNo='{egrn}',@InvoiceNo=NULL,@OrderGarmentIDs='{order_garment_ids}',@ForMobileApp=1,@PaymentSource='website'"

    # Executing the SP and retrieving the result.
    discount_details = CallSP(query).execute().fetchone()

    # Returning the result.
    return discount_details


def make_payment(customer_code, egrn_details, branch_code, amount_to_pay, attached_coupons, attached_loyalty_points,
                 invoice_discount_details, collected, egrn_no, trn_amount_received, user_id, is_monthly_customer,
                 TRNNo):
    """
    Function for making payment for an EGRN.
    @param customer_code: CustomerCode of the customer.
    @param egrn_details: Unsettled order details of an EGRN.
    @param branch_code: Branch code where the order belongs to.
    @param amount_to_pay: Payable amount of the customer after deducting all the pre applied coupons/discounts/LPs..etc (if any).
    @param attached_coupons: Pre applied & applied compensation coupon details.
    @param attached_loyalty_points: Pre applied & applied loyalty points.
    @param invoice_discount_details: Pre applied invoice level discount details.
    @param collected: Amount collected from the customer.
    @return: Status of the settlement if the settlement is successfully completed, else return empty Dict variable.
    """
    # Generating the new payment id. Payment id will be the same for all the EGRN orders.
    new_payment_id = db.session.query(func.newid().label('Id')).one_or_none()
    payment_id = new_payment_id.Id
    # Logging the data in the request into log file.
    # Generating the new transaction_id.
    new_transaction_id = db.session.query(func.newid().label('Id')).one_or_none()
    transaction_id = new_transaction_id.Id

    ready_to_settle = False
    settled = {}
    attached_coupons_amount = 0
    attached_coupons_str = None
    full_lp_settlement = False
    # in case of coupon and discount code settlement
    # Check if the customer is monthly customer if TRUE permit insertion of data to TransactionPaymentInfo table

    egrn = egrn_details['details']['UNSETTLEDORDERNUMBER']

    basic_amount = round(egrn_details['details']['BASICAMOUNT'], 2)
    round_off = round(egrn_details['details']['ROUNDOFF'], 2)
    invoice_amount = egrn_details['details']['FINALINVOICEAMOUNT']
    revised_payable_amount = egrn_details['details']['PAYABLEAMOUNT']
    product_basic_amount = egrn_details['details']['PRODUCTBASICAMOUNT']
    product_round_off = egrn_details['details']['PRODUCTROUNDOFF']
    product_invoice_amount = egrn_details['details']['PRODUCTINVOICEAMOUNT']
    invoice_discount_code = None
    invoice_discount = None

    order_garment_ids = egrn_details['details']['ORDERGARMENTID']
    garments_count = egrn_details['details']['GARMENTSCOUNT']

    if invoice_discount_details:
        if float(invoice_discount_details['InvoiceDiscount']) != 0:
            # Global discount amount is present.
            basic_amount = invoice_discount_details['RevisedBasicAmount']
            round_off = invoice_discount_details['RevisedRoundOff']
            invoice_amount = invoice_discount_details['RevisedInvoiceAmount']
            revised_payable_amount = float(invoice_discount_details['RevisedPayableAmount'])
            product_basic_amount = float(invoice_discount_details['ProductBasicAmount'])
            product_round_off = float(invoice_discount_details['ProductRoundOff'])
            product_invoice_amount = float(invoice_discount_details['ProductInvoiceAmount'])
            invoice_discount_code = invoice_discount_details['InvoiceDiscountCode']
            invoice_discount = float(invoice_discount_details['InvoiceDiscount'])
    #         Edited by MMM
    # If amount received is YES take trnno from getGarementPaymentInfoDetails SP
    dcn_no = None
    trn_number = None

    if trn_amount_received.get('AmountReceived') == "YES":
        trn_number1 = trn_amount_received['trnno']

        dcn_no = delivery_controller_queries.get_payable_amount_via_sp(customer_code, TRNNo)

        if dcn_no is not None:
            trn_number2 = dcn_no['DCNO']

            if trn_number1 == trn_number2:
                trn_number = trn_number1
            else:

                trn_number = trn_number2 if trn_number2 else trn_number1
    else:
        # If amount received is NO take trnno from fabexpressOrderListForGenerateInvoice SP
        dcn_no = delivery_controller_queries.get_payable_amount_via_sp(customer_code, TRNNo)
        trn_number = dcn_no['DCNO']
    print("11trn_number", trn_number)

    if attached_coupons:
        # Attached coupons are found.
        coupons = []
        attached_coupons_amount = 0
        for attached_coupon in attached_coupons:
            coupons.append(attached_coupon['COUPONCODE'])
            attached_coupons_amount += float(attached_coupon['RedeemedAmount'])
        attached_coupons_str = ','.join(map(str, coupons))

    payment_from = None
    # appending cash_card_collection_list with CASH_COLLECTION and CARD_COLLECTION modes only
    cash_card_collection_list = [i for i in collected if
                                 i['mode'] == 'CASH_COLLECTION' or i['mode'] == 'CARD_COLLECTION' or i[
                                     'mode'] == 'PHONEPE']

    if len(cash_card_collection_list) == 3:
        payment_from = 'FABXPRESS'

    # Creating a new TransactionInfo object to insert.
    new_transaction_info = TransactionInfo(
        CustomerCode=customer_code,
        TransactionId=transaction_id,
        TransactionDate=get_current_date(),
        EGRNNo=egrn,
        DCNo=trn_number,
        FinalServiceAmount=invoice_amount,
        FinalProductAmount=product_invoice_amount,
        TotalPayableAmount=amount_to_pay,
        RoundOff=round_off,
        PaymentId=payment_id,
        PaymentSource='delivery',
        OrderGarmentIDs=order_garment_ids,
        UsedCompensationCoupons=attached_coupons_str,
        DiscountAmount=attached_coupons_amount,
        RevisedBasicAmount=basic_amount,
        RevisedRoundOff=round_off,
        RevisedInvoiceAmount=invoice_amount,
        ProductBasicAmount=product_basic_amount,
        ProductRoundOff=product_round_off,
        ProductInvoiceAmount=product_invoice_amount,
        RevisedPayableAmount=revised_payable_amount,
        InvoiceDiscountCode=invoice_discount_code,
        InvoiceDiscount=invoice_discount,
        GarmentsCount=garments_count,
        PaymentFrom=payment_from,
        PaymentCollectedBY=user_id,
        PaymentCompletedOn=get_current_date(),
        Gateway='PAYTMEDC' if collected and collected[0]['mode'] == 'PAYTMEDC' else None
    )
    try:

        db.session.add(new_transaction_info)
        db.session.commit()
        """
        ###
        Inserting into the TransactionPaymentInfo table logic.
        ###
        """
        # After inserting into the TransactionInfo, new row need to be inserted into the
        # TransactionPaymentInfo as well.

        # If the coupons are applied, amount_to_pay will be different to the initial EGRN amount.
        # If the whole payable amount can be paid by a coupon/invoice discount/LP, then amount_to_pay will be 0.
        # Hence in that case, no need for checking the collected amounts.
        redeemed_amount = 0
        if amount_to_pay > 0:
            """
            THE REMAINING AMOUNT NEEDS TO BE COLLECTED FROM THE CUSTOMER EXPLICITLY, ALONG WITH
            ANY COUPONS/LOYALTY POINTS (IF ANY).
            """

            # If the coupons are applied, inserting coupon data into TransactionPaymentInfo table.
            if attached_coupons:
                redeemed_amount = insert_transaction_payment_info_with_coupon_details(attached_coupons, transaction_id,
                                                                                      payment_id,
                                                                                      round_off, trn_number, egrn)

            # If any loyalty points are attached, insert the loyalty points information in the TransactionInfo table.
            if attached_loyalty_points:
                update_transaction_info_with_lp_details(new_transaction_info.Id, attached_loyalty_points)

            # If monthly customer no need for considering the collected amount
            if not is_monthly_customer:
                # If there are multiple payment modes are available, insert them into different rows in payment
                # gateway.
                for collection in collected:
                    # Splitting the payment modes based on given order amount and collected amount.

                    # If the remaining amount is already 0, so no need for looping the next
                    # payment method.
                    if amount_to_pay == 0:
                        break

                    if amount_to_pay > collection['amount']:
                        print("amount_to_pay", amount_to_pay)
                        print("collection['amount']", collection['amount'])
                        # Here, the collection amount is less than amount_to_pay.
                        # Which means, collection_amount can be fully used here.
                        collection_amount = float(collection['amount'])
                        # Remaining amount_to_pay.
                        amount_to_pay = amount_to_pay - collection['amount']

                        # The whole amount has been used for this payment mode.
                        collection['amount'] = 0
                    else:
                        # Collection amount is greater than the amount_to_pay.
                        collection_amount = float(amount_to_pay)

                        # Only a partial of the amount has been used for this order.
                        collection['amount'] = collection['amount'] - amount_to_pay

                        # No more remaining amount is there for that order.

                    # if redeemed_amount > 0:
                    #     collection_amount = max(0, amount_to_pay - redeemed_amount)
                    print("collection_amount",collection_amount)
                    if collection_amount > 0:
                        try:
                            # New TransactionPaymentInfo object.
                            new_transaction_payment_info = TransactionPaymentInfo(
                                PaymentId=payment_id,
                                CreatedOn=get_current_date(),
                                TransactionId=transaction_id,
                                PaymentMode=collection['mode'],
                                CardTransactionId=collection.get('transaction_id'),
                                PaymentAmount=collection_amount,
                                RoundOff=round_off,
                                BranchCode=branch_code
                            )

                            db.session.add(new_transaction_payment_info)
                            db.session.commit()

                            ready_to_settle = True
                        except Exception as e:
                            error_logger(f'Payment: {inspect.stack()[0].function}()').error(e)

            if is_monthly_customer:
                # Make ready_to_settle flag true
                ready_to_settle = True

        else:
            # If amount to pay is 0 make ready_to_settle True
            if amount_to_pay == 0:
                ready_to_settle = True
            """
            NO COLLECTION FROM THE CUSTOMER; THE WHOLE AMOUNT CAN BE REDEEMED BY EITHER COUPONS/LOYALTY POINTS.
            """
            # The whole amount can be paid via coupon/ER loyalty points.
            # Insert the coupon details into the TransactionPaymentInfo table.
            if attached_coupons:
                insert_transaction_payment_info_with_coupon_details(attached_coupons, transaction_id, payment_id,
                                                                    round_off, trn_number, egrn_no)
                ready_to_settle = True

            if attached_loyalty_points:
                # The whole amount can be redeemed by loyalty points.
                # Update the TransactionInfo table with the loyalty points details.
                update_transaction_info_with_lp_details(new_transaction_info.Id, attached_loyalty_points)
                ready_to_settle = True
                full_lp_settlement = True

            if invoice_discount_details:
                # TODO: Doubt - Can a whole order be redeemed by invoice discount?
                pass

            if redeemed_amount == amount_to_pay:
                ready_to_settle = True
        print("redeemed_amount", redeemed_amount)
        print("amount_to_pay", amount_to_pay)
        if ready_to_settle:
            # Calling the settlement procedure to settle the order.
            print("transaction_id", transaction_id)
            print("payment_id", payment_id)
            settlement = make_settlement(transaction_id, payment_id)
            if settlement is not None:

                if settlement.get('RESULT') == 'SUCCESS':
                    # Edited by Athira

                    # info_logger(f'Route: {request.path}').info(json.dumps(log_data))
                    if new_transaction_info.Gateway is not None:
                        try:

                            if collected[0]['mode'] == 'PAYTMEDC':
                                invoice_no = settlement.get('INVOICENO')
                                query = f"EXEC [BranchEmailForPayTMEDC] @TransactionId='{transaction_id}',@InvoiceNo='{invoice_no}'"
                                CallSP(query).execute()
                        except Exception as e:
                            error_logger(f'Route: {request.path}').error(e)

                    # Send sms only if AmountReceived is no means invoice already generated
                    if trn_amount_received['AmountReceived'] == "NO":
                        try:
                            # Send shortened invoice link as sms
                            delivery_controller_queries.send_sms_email_when_settled(customer_code, egrn,
                                                                                    dcn_no['PAYABLEAMOUNT'],
                                                                                    settlement.get('INVOICENO'),TRNNo)
                        except Exception as e:
                            error_logger(f'Route: {request.path}').error(e)

                    # Add entry to TransactionPaymentInfo only if not monthly customer
                    if not full_lp_settlement and not is_monthly_customer:
                        # This is not a full LP redeemed settlement.
                        try:
                            payment_info_details = db.session.query(TransactionPaymentInfo).filter(
                                TransactionPaymentInfo.PaymentId == payment_id,
                                TransactionPaymentInfo.TransactionId == transaction_id).all()
                            for payment_info_detail in payment_info_details:
                                payment_info_detail.InvoiceNo = settlement.get('INVOICENO')
                                payment_info_detail.Remarks = settlement.get('REMARKS')
                                db.session.commit()
                            # Populating the final result variable needs to be returned.
                            settled = {"Status": "Settled", "InvoiceNo": f"{settlement.get('INVOICENO')}"}
                        except Exception as e:
                            db.session.rollback()
                            error_logger(f'Payment: {inspect.stack()[0].function}()').error(e)
                    else:
                        # This is a full LP redeemed settlement. There won't be any payment info table entries.
                        # Populating the final result variable needs to be returned.
                        settled = {"Status": "Settled", "InvoiceNo": f"{settlement.get('INVOICENO')}"}

                    # After the settlement, need to perform some tasks
                    # such as confirming the use of ER coupon/loyalty points (if any), save sku calls..etc.
                    after_settlement(customer_code, egrn, settlement.get('INVOICENO'), amount_to_pay)
    except Exception as e:
        db.session.rollback()
        error_logger(f'Payment: {inspect.stack()[0].function}()').error(e)

    return settled


# def make_payment(customer_code, egrn_details, branch_code, amount_to_pay, attached_coupons, attached_loyalty_points,
#                  invoice_discount_details, collected, egrn_no, trn_amount_received,user_id):
#     """
#     Function for making payment for an EGRN.
#     @param customer_code: CustomerCode of the customer.
#     @param egrn_details: Unsettled order details of an EGRN.
#     @param branch_code: Branch code where the order belongs to.
#     @param amount_to_pay: Payable amount of the customer after deducting all the pre applied coupons/discounts/LPs..etc (if any).
#     @param attached_coupons: Pre applied & applied compensation coupon details.
#     @param attached_loyalty_points: Pre applied & applied loyalty points.
#     @param invoice_discount_details: Pre applied invoice level discount details.
#     @param collected: Amount collected from the customer.
#     @return: Status of the settlement if the settlement is successfully completed, else return empty Dict variable.
#     """
#     # Generating the new payment id. Payment id will be the same for all the EGRN orders.
#     new_payment_id = db.session.query(func.newid().label('Id')).one_or_none()
#     payment_id = new_payment_id.Id
#     # Logging the data in the request into log file.
#     # Generating the new transaction_id.
#     new_transaction_id = db.session.query(func.newid().label('Id')).one_or_none()
#     transaction_id = new_transaction_id.Id

#     ready_to_settle = False
#     settled = {}
#     attached_coupons_amount = 0
#     attached_coupons_str = None
#     full_lp_settlement = False
#     # in case of coupon and discount code settlement
#     # Check if the customer is monthly customer if TRUE permit insertion of data to TransactionPaymentInfo table
#     is_monthly_customer = delivery_controller_queries.check_monthly_customer(customer_code)

#     egrn = egrn_details['details']['UNSETTLEDORDERNUMBER']

#     basic_amount = round(egrn_details['details']['BASICAMOUNT'], 2)
#     round_off = round(egrn_details['details']['ROUNDOFF'], 2)
#     invoice_amount = egrn_details['details']['FINALINVOICEAMOUNT']
#     revised_payable_amount = egrn_details['details']['PAYABLEAMOUNT']
#     product_basic_amount = egrn_details['details']['PRODUCTBASICAMOUNT']
#     product_round_off = egrn_details['details']['PRODUCTROUNDOFF']
#     product_invoice_amount = egrn_details['details']['PRODUCTINVOICEAMOUNT']
#     invoice_discount_code = None
#     invoice_discount = None

#     order_garment_ids = egrn_details['details']['ORDERGARMENTID']
#     garments_count = egrn_details['details']['GARMENTSCOUNT']

#     if invoice_discount_details:
#         if float(invoice_discount_details['InvoiceDiscount']) != 0:
#             # Global discount amount is present.
#             basic_amount = invoice_discount_details['RevisedBasicAmount']
#             round_off = invoice_discount_details['RevisedRoundOff']
#             invoice_amount = invoice_discount_details['RevisedInvoiceAmount']
#             revised_payable_amount = float(invoice_discount_details['RevisedPayableAmount'])
#             product_basic_amount = float(invoice_discount_details['ProductBasicAmount'])
#             product_round_off = float(invoice_discount_details['ProductRoundOff'])
#             product_invoice_amount = float(invoice_discount_details['ProductInvoiceAmount'])
#             invoice_discount_code = invoice_discount_details['InvoiceDiscountCode']
#             invoice_discount = float(invoice_discount_details['InvoiceDiscount'])
#     #         Edited by MMM
#     # If amount received is YES take trnno from getGarementPaymentInfoDetails SP
#     dcn_no = None
#     trn_number = None
#     # if trn_amount_received['AmountReceived'] == "YES":

#     #     trn_number = trn_amount_received['trnno']
#     # else:
#     #     # If amount received is NO take trnno from fabexpressOrderListForGenerateInvoice SP
#     #     dcn_no = delivery_controller_queries.get_payable_amount_via_sp(customer_code, egrn_no)
#     #     trn_number = dcn_no['DCNO']
#     #         Edited by MMM
#     if trn_amount_received.get('AmountReceived') == "YES":
#         trn_number1 = trn_amount_received['trnno']

#         dcn_no = delivery_controller_queries.get_payable_amount_via_sp(customer_code, egrn_no)
#         if dcn_no is not None:
#             trn_number2 = dcn_no['DCNO']

#             if trn_number1 == trn_number2:
#                 trn_number = trn_number1
#             else:

#                 trn_number = trn_number2 if trn_number2 else trn_number1
#     else:
#         # If amount received is NO take trnno from fabexpressOrderListForGenerateInvoice SP
#         dcn_no = delivery_controller_queries.get_payable_amount_via_sp(customer_code, egrn_no)
#         trn_number = dcn_no['DCNO']

#     if attached_coupons:
#         # Attached coupons are found.
#         coupons = []
#         attached_coupons_amount = 0
#         for attached_coupon in attached_coupons:
#             coupons.append(attached_coupon['COUPONCODE'])
#             attached_coupons_amount += float(attached_coupon['RedeemedAmount'])
#         attached_coupons_str = ','.join(map(str, coupons))

#     payment_from = None
#     # appending cash_card_collection_list with CASH_COLLECTION and CARD_COLLECTION modes only
#     cash_card_collection_list = [i for i in collected if
#                                  i['mode'] == 'CASH_COLLECTION' or i['mode'] == 'CARD_COLLECTION' or i['mode'] == 'PHONEPE']


#     if len(cash_card_collection_list) == 3:
#         payment_from = 'FABXPRESS'

#     # Creating a new TransactionInfo object to insert.
#     new_transaction_info = TransactionInfo(
#         CustomerCode=customer_code,
#         TransactionId=transaction_id,
#         TransactionDate=get_current_date(),
#         EGRNNo=egrn,
#         DCNo=trn_number,
#         FinalServiceAmount=invoice_amount,
#         FinalProductAmount=product_invoice_amount,
#         TotalPayableAmount=amount_to_pay,
#         RoundOff=round_off,
#         PaymentId=payment_id,
#         PaymentSource='delivery',
#         OrderGarmentIDs=order_garment_ids,
#         UsedCompensationCoupons=attached_coupons_str,
#         DiscountAmount=attached_coupons_amount,
#         RevisedBasicAmount=basic_amount,
#         RevisedRoundOff=round_off,
#         RevisedInvoiceAmount=invoice_amount,
#         ProductBasicAmount=product_basic_amount,
#         ProductRoundOff=product_round_off,
#         ProductInvoiceAmount=product_invoice_amount,
#         RevisedPayableAmount=revised_payable_amount,
#         InvoiceDiscountCode=invoice_discount_code,
#         InvoiceDiscount=invoice_discount,
#         GarmentsCount=garments_count,
#         PaymentFrom=payment_from,
#         PaymentCollectedBY=user_id,
#         PaymentCompletedOn=get_current_date(),
#         Gateway='PAYTMEDC' if collected and collected[0]['mode'] == 'PAYTMEDC' else None
#     )

#     try:
#         db.session.add(new_transaction_info)
#         db.session.commit()
#         """
#         ###
#         Inserting into the TransactionPaymentInfo table logic.
#         ###
#         """
#         # After inserting into the TransactionInfo, new row need to be inserted into the
#         # TransactionPaymentInfo as well.

#         # If the coupons are applied, amount_to_pay will be different to the initial EGRN amount.
#         # If the whole payable amount can be paid by a coupon/invoice discount/LP, then amount_to_pay will be 0.
#         # Hence in that case, no need for checking the collected amounts.

#         if amount_to_pay > 0:
#             """
#             THE REMAINING AMOUNT NEEDS TO BE COLLECTED FROM THE CUSTOMER EXPLICITLY, ALONG WITH
#             ANY COUPONS/LOYALTY POINTS (IF ANY).
#             """

#             # If the coupons are applied, inserting coupon data into TransactionPaymentInfo table.
#             if attached_coupons:
#                 insert_transaction_payment_info_with_coupon_details(attached_coupons, transaction_id, payment_id,
#                                                                     round_off, trn_number, egrn_no)

#             # If any loyalty points are attached, insert the loyalty points information in the TransactionInfo table.
#             if attached_loyalty_points:
#                 update_transaction_info_with_lp_details(new_transaction_info.Id, attached_loyalty_points)

#             # If monthly customer no need for considering the collected amount
#             if not is_monthly_customer:
#                 # If there are multiple payment modes are available, insert them into different rows in payment
#                 # gateway.
#                 for collection in collected:
#                     # Splitting the payment modes based on given order amount and collected amount.

#                     # If the remaining amount is already 0, so no need for looping the next
#                     # payment method.
#                     if amount_to_pay == 0:
#                         break

#                     if amount_to_pay > collection['amount']:
#                         # Here, the collection amount is less than amount_to_pay.
#                         # Which means, collection_amount can be fully used here.
#                         collection_amount = float(collection['amount'])
#                         # Remaining amount_to_pay.
#                         amount_to_pay = amount_to_pay - collection['amount']

#                         # The whole amount has been used for this payment mode.
#                         collection['amount'] = 0

#                     else:
#                         # Collection amount is greater than the amount_to_pay.
#                         collection_amount = float(amount_to_pay)

#                         # Only a partial of the amount has been used for this order.
#                         collection['amount'] = collection['amount'] - amount_to_pay

#                         # No more remaining amount is there for that order.
#                         amount_to_pay = 0

#                     if collection_amount > 0:
#                         try:
#                             # New TransactionPaymentInfo object.
#                             new_transaction_payment_info = TransactionPaymentInfo(
#                                 PaymentId=payment_id,
#                                 CreatedOn=get_current_date(),
#                                 TransactionId=transaction_id,
#                                 PaymentMode=collection['mode'],
#                                 CardTransactionId=collection.get('transaction_id'),
#                                 PaymentAmount=collection_amount,
#                                 RoundOff=round_off,
#                                 BranchCode=branch_code
#                             )

#                             db.session.add(new_transaction_payment_info)
#                             db.session.commit()

#                             ready_to_settle = True
#                         except Exception as e:
#                             error_logger(f'Payment: {inspect.stack()[0].function}()').error(e)

#             if is_monthly_customer:
#                 # Make ready_to_settle flag true
#                 ready_to_settle = True

#         else:
#             # If amount to pay is 0 make ready_to_settle True
#             if amount_to_pay == 0:
#                 ready_to_settle = True
#             """
#             NO COLLECTION FROM THE CUSTOMER; THE WHOLE AMOUNT CAN BE REDEEMED BY EITHER COUPONS/LOYALTY POINTS.
#             """
#             # The whole amount can be paid via coupon/ER loyalty points.
#             # Insert the coupon details into the TransactionPaymentInfo table.
#             if attached_coupons:
#                 insert_transaction_payment_info_with_coupon_details(attached_coupons, transaction_id, payment_id,
#                                                                     round_off, trn_number, egrn_no)
#                 ready_to_settle = True

#             if attached_loyalty_points:
#                 0# The whole amount can be redeemed by loyalty points.
#                 # Update the TransactionInfo table with the loyalty points details.
#                 update_transaction_info_with_lp_details(new_transaction_info.Id, attached_loyalty_points)
#                 ready_to_settle = True
#                 full_lp_settlement = True

#             if invoice_discount_details:
#                 # TODO: Doubt - Can a whole order be redeemed by invoice discount?
#                 pass

#         if ready_to_settle:
#             # Calling the settlement procedure to settle the order.
#             settlement = make_settlement(transaction_id, payment_id)
#             if settlement is not None:

#                 if settlement.get('RESULT') == 'SUCCESS':
#                     # Edited by Athira

#                     # info_logger(f'Route: {request.path}').info(json.dumps(log_data))
#                     if new_transaction_info.Gateway is not None:
#                         try:

#                             if collected[0]['mode'] == 'PAYTMEDC':
#                                 invoice_no = settlement.get('INVOICENO')
#                                 query = f"EXEC [BranchEmailForPayTMEDC] @TransactionId='{transaction_id}',@InvoiceNo='{invoice_no}'"
#                                 CallSP(query).execute()
#                         except Exception as e:
#                             error_logger(f'Route: {request.path}').error(e)

#                     # Send sms only if AmountReceived is no means invoice already generated
#                     if trn_amount_received['AmountReceived'] == "NO":
#                         try:
#                             # Send shortened invoice link as sms
#                             delivery_controller_queries.send_sms_email_when_settled(customer_code, egrn,
#                                                                                     dcn_no['PAYABLEAMOUNT'],
#                                                                                     settlement.get('INVOICENO'))
#                         except Exception as e:
#                             error_logger(f'Route: {request.path}').error(e)

#                     # Add entry to TransactionPaymentInfo only if not monthly customer
#                     if not full_lp_settlement and not is_monthly_customer:
#                         # This is not a full LP redeemed settlement.
#                         try:
#                             payment_info_details = db.session.query(TransactionPaymentInfo).filter(
#                                 TransactionPaymentInfo.PaymentId == payment_id,
#                                 TransactionPaymentInfo.TransactionId == transaction_id).all()
#                             for payment_info_detail in payment_info_details:
#                                 payment_info_detail.InvoiceNo = settlement.get('INVOICENO')
#                                 payment_info_detail.Remarks = settlement.get('REMARKS')
#                                 db.session.commit()
#                             # Populating the final result variable needs to be returned.
#                             settled = {"Status": "Settled", "InvoiceNo": f"{settlement.get('INVOICENO')}"}
#                         except Exception as e:
#                             db.session.rollback()
#                             error_logger(f'Payment: {inspect.stack()[0].function}()').error(e)
#                     else:
#                         # This is a full LP redeemed settlement. There won't be any payment info table entries.
#                         # Populating the final result variable needs to be returned.
#                         settled = {"Status": "Settled", "InvoiceNo": f"{settlement.get('INVOICENO')}"}

#                     # After the settlement, need to perform some tasks
#                     # such as confirming the use of ER coupon/loyalty points (if any), save sku calls..etc.
#                     after_settlement(customer_code, egrn, settlement.get('INVOICENO'), amount_to_pay)
#     except Exception as e:
#         db.session.rollback()
#         error_logger(f'Payment: {inspect.stack()[0].function}()').error(e)

#     return settled


#     # TODO temporary  code change for checking the url for settlement is working or not
# def make_settlement(transaction_id, payment_id):
#     """
#     Function for calling the settlement stored procedure for settling an order.
#     @param transaction_id:
#     @param payment_id:
#     @return: SP result.
#     """
#     if CURRENT_ENV == 'development':
#         url = "https://uat.jfsl.in/settlement/api/settlement"
#     else:
#         url = "https://live.jfsl.in/FabXpress_Settlement/api/settlement"
#     response = requests.post(url,
#                              json={'TransactionID': transaction_id, 'PaymentID': payment_id})
#     result = json.loads(response.json())
#     result = result[0]
#     settlement = {"RESULT": result['RESULT'], "INVOICENO": result['INVOICENO'], "REMARKS": result['REMARKS']}
#     log_data = {
#         'result of settlement sp': settlement,
#         'result from api': json.loads(response.json()),
#     }
#     info_logger(f'Route: {request.path}').info(json.dumps(log_data))
#     return settlement
#     # TODO temporary  code change for checking the url for settlement is working or not


def make_settlement(transaction_id, payment_id):
    """
    Function for calling the settlement stored procedure for settling an order.
    @param transaction_id:
    @param payment_id:
    @return: SP result.
    """
    query = f"EXEC {SERVER_DB}.dbo.[INVOICEANDSETTLEMENTFORMOBILEAPPCustomerAPPDB] @TransactionId='{transaction_id}',@PAYMENTID='{payment_id}'"
    log_data = {
        'query of settlement :': query,

    }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))
    settlement = CallSP(query).execute().fetchone()
    db.session.commit()

    log_data = {
        'query of settlement :': query,
        'result of settlement :': settlement,
    }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))

    return settlement


def after_settlement(customer_code, egrn, invoice_number, amount):
    """
    Function for performing different tasks after making a payment settlement.
    @param customer_code: POS customer code.
    @param egrn: EGRN of the order.
    @param invoice_number: Invoice number generated after the settlement.
    @param amount: Amount settled in the order.
    @return:
    """

    # Use ER coupon call.
    er_module.use_er_coupon(egrn, invoice_number, amount)

    # Getting the LP details after the settlement to confirm the LP redemption.
    er_lp_data = er_module.queries.get_er_lp_data_for_confirmation(egrn, invoice_number)

    if er_lp_data:
        if er_lp_data['ISLASTInvoice'] == 'YES':
            if er_lp_data['IsAppliedinOrder'] == 1:
                er_transaction_code = er_lp_data['TransactionCode']
                # This is the last invoice of this particular order.
                if er_lp_data['INVLoyaltypoints'] == er_lp_data['OLoyaltypoints']:
                    # Calling the confirm ER loyalty points API.
                    er_module.confirm_er_loyalty_points(customer_code, er_transaction_code, invoice_number, amount)

                else:
                    # Unblocking the loyalty points.
                    er_module.unblock_er_loyalty_points(customer_code, er_lp_data['TransactionCode'],
                                                        er_lp_data['BranchCode'])

                    # Blocking it again.
                    er_module.block_er_loyalty_points(customer_code, er_transaction_code,
                                                      er_lp_data['INVLoyaltypoints'], amount, egrn)

                    # Confirming the loyalty points.
                    er_module.confirm_er_loyalty_points(customer_code, er_transaction_code, invoice_number, amount)

            else:
                er_transaction_code = er_lp_data['TransactionCode']
                # Confirming the loyalty points.
                er_module.confirm_er_loyalty_points(customer_code, er_transaction_code, invoice_number, amount)

    # Calling the EasyRewardz' Save SKU API.
    er_module.save_sku_details(egrn, invoice_number, amount)


def deduct_pre_applied_coupons_and_discounts(egrn, initial_amount, order_garment_ids):
    """
    Getting the final amount that customer needs to pay after deducting the pre applied coupons/discounts/loyalty points..etc.
    @param egrn: EGRN of the order.
    @param initial_amount: Initial amount gained from the unsettled store procedure.
    @param order_garment_ids POS order garment Ids present in the current EGRN.
    @return: Final amount that customer needs to pay.
    """
    amount_to_pay = initial_amount
    pre_applied_coupons = []
    invoice_discount_details = {}
    lp_details = {}
    lp_in_rupees = 0
    total_discount_in_rs = 0

    # First, check for the invoice level discount/global level discount that is applied or not.
    global_invoice_discount_details = get_global_invoice_discount_details(egrn, order_garment_ids)

    if float(global_invoice_discount_details['InvoiceDiscount']) != 0:
        # Here, a global invoice discount is present.
        amount_to_pay = float(global_invoice_discount_details['RevisedPayableAmount'])
        invoice_discount_details = global_invoice_discount_details
        # Adding the pre applied global level discount amount to the total discount variable.
        total_discount_in_rs += float(global_invoice_discount_details['InvoiceDiscount'])

    # Check if the compensation coupons are attached to this order or not.
    available_coupons = get_available_coupon_codes(egrn)

    if available_coupons:
        for coupon in available_coupons:
            if coupon['ATTACHEDATEGRNLEVEL'] == 1:
                # This coupon is attached from POS.
                # Deduct the amount from the amount_to_pay.
                amount_to_pay -= float(coupon['DISCOUNTAMOUNT'])
                # Adding the pre applied compensation coupon discount amount to the total discount variable.
                total_discount_in_rs += float(coupon['DISCOUNTAMOUNT'])
                coupon['RedeemedAmount'] = float(coupon['DISCOUNTAMOUNT'])
                pre_applied_coupons.append(coupon)

    # Check if any loyalty points are pre applied with this egrn or not.
    lp_from_egrn = er_queries.get_lp_from_egrn(egrn)
    if lp_from_egrn:
        if lp_from_egrn['IsAlreadyApplied'] == 1 and lp_from_egrn['IsappliedFromOrder']:
            # Loyalty points are pre applied.
            if lp_from_egrn['SelfAttached'] > 0:
                attached_lp = lp_from_egrn['SelfAttached']
            else:
                attached_lp = lp_from_egrn['RemainingPoints']
            lp_details = lp_from_egrn
            lp_in_rupees = attached_lp * lp_from_egrn['OILoyaltyPointsRate']
            lp_details['lp_in_rupees'] = float(lp_in_rupees)
            # Adding the pre applied loyalty point discount amount to the total discount variable.
            total_discount_in_rs += float(lp_in_rupees)
            lp_details['lp_applied'] = attached_lp
            lp_details['er_transaction_code'] = f'T{egrn}'

    # Deducting the loyalty points from the amount (if any).
    amount_to_pay -= float(lp_in_rupees)

    if amount_to_pay < 0:
        # In real world, this scenario won't be exists. Suppose if
        # such case arises, log the details. This is an unexpected scenario.
        info_logger(f'Payment: {inspect.stack()[0].function}()').info(
            f"UNEXPECTED. After applying pre-applied coupons, amount became less than 0. EGRN# {egrn}")

    # Returning the final amount to pay after deducting
    # all the pre applied coupons/discounts/loyalty points.
    # This amount needs to be paid by the customer himself/herself.

    result = {'amount_to_pay': amount_to_pay, 'total_discount': total_discount_in_rs,
              'pre_applied_coupons': pre_applied_coupons,
              'invoice_discount_details': invoice_discount_details, 'pre_applied_lp_details': lp_details}
    return result


def get_available_coupon_codes(egrn):
    """
    Function for calling the GetPromocodeData stored procedure.
    Getting the attached coupons for a EGRN.
    @param egrn:
    @return: SP result.
    """

    OrderID = db.session.execute(
            text(
                "SELECT  OrderID FROM JFSL_UAT.dbo.OrderInfo (nolock) WHERE EGRNNO = :egrn"),
            {"egrn": egrn}
        ).fetchone()
    OrderID = OrderID[0]
    FinalAmount = db.session.execute(
            text(
                "SELECT FinalAmount  FROM JFSL_UAT.dbo.InvoIceInfo (nolock) WHERE OrderID = :OrderID"),
            {"OrderID": OrderID}
        ).fetchone()
    FinalAmount = FinalAmount[0]
    query = f"EXEC {SERVER_DB}.dbo.GetPromocodeData @EGRNNo='{egrn}',@MultipleDCEGRN=0,@EstimatedInvoiceAmount={FinalAmount}"
    print(query)
    result = CallSP(query).execute().fetchall()

    return result


def get_coupon_details(coupon_code, egrn):
    """
    Function for fetching a compensation coupon details from available coupons list.
    @param coupon_code: Compensation coupon/marketing coupon.
    @param egrn: EGRN of that coupon belongs to.
    @return: Dict variable if result is found, else None.
    """

    # Getting the available coupons for that EGRN.
    coupons = get_available_coupon_codes(egrn)
    selected_coupon_details = None
    # Getting the matching EGRN details from the coupons list.
    for coupon in coupons:
        if coupon['COUPONCODE'] == coupon_code:
            # Found the given coupon code details.
            selected_coupon_details = coupon
            break
    return selected_coupon_details


def apply_coupons(amount_to_pay, coupons, egrn):
    """
    Function for applying the coupons.
    @param amount_to_pay: Amount to be paid by the customer.
    @param coupons: Coupons that need to be applied.
    @param egrn: List of available coupons for the particular EGRN.
    @return: Result in a Dict format.
    """
    applied_coupons = []
    # Edited by MMM
    amount_to_pay_after_coupon = amount_to_pay
    for coupon in coupons:
        coupon_details = get_coupon_details(coupon, egrn)
        if coupon_details is not None:
            # A Valid coupon details is found.
            # Check whether the coupon deduction exceeds the amount to pay or not.
            amount_to_pay_after_coupon -= float(coupon_details['DISCOUNTAMOUNT'])
            if amount_to_pay_after_coupon < 0:
                # The coupon can be fully redeemed.
                coupon_details['RedeemedAmount'] = amount_to_pay
                applied_coupons.append(coupon_details)
                amount_to_pay = 0
                break
            else:
                coupon_details['RedeemedAmount'] = float(coupon_details['DISCOUNTAMOUNT'])
                applied_coupons.append(coupon_details)
                amount_to_pay = amount_to_pay_after_coupon

    result = {'amount_to_pay': amount_to_pay, 'applied_coupons': applied_coupons}
    return result
    # Edited by MMM


def get_lp(customer_code, egrn):
    """
    Function for getting the ER loyalty points.
    @param customer_code:
    @param egrn
    @return: Available loyalty points for the customer.
    """
    loyalty_points = {}
    # Getting the LP based on EGRN.
    lp_from_egrn = er_module.queries.get_lp_from_egrn(egrn)

    # Get the LP from the ER API itself.
    lp_from_er = er_module.get_available_er_lp(customer_code)

    if lp_from_egrn['IsAlreadyApplied'] == 0 and lp_from_egrn['SelfAttached'] == 0:
        # Consider the LP from the API itself.
        loyalty_points['IsAlreadyApplied'] = 0
        loyalty_points['IsappliedFromOrder'] = 0
        loyalty_points['RemainingPoints'] = lp_from_er['available_points']
        loyalty_points['OILoyaltyPointsRate'] = lp_from_er['point_rate']
    elif lp_from_egrn['SelfAttached'] > 1:
        # LP is attached to the EGRN.
        loyalty_points['IsAlreadyApplied'] = 0
        loyalty_points['IsappliedFromOrder'] = 0
        loyalty_points['RemainingPoints'] = lp_from_er['SelfAttached']

    else:
        lp_from_egrn['OILoyaltyPointsRate'] = float(lp_from_egrn['OILoyaltyPointsRate'])
        loyalty_points = lp_from_egrn

    return loyalty_points


def apply_lp(customer_code, egrn, amount_to_pay):
    """
    Function for manually applying the loyalty points for an order.
    @param customer_code:
    @param egrn:
    @param amount_to_pay: Amount to be paid by the customer.
    @return: Result in dict form - containing the applied LP details.
    """
    available_lp = get_lp(customer_code, egrn)
    applied_lp = {}
    if available_lp:
        if available_lp['IsAlreadyApplied'] == 0 and available_lp['IsappliedFromOrder'] == 0:
            # The LP is not pre applied.

            # Converting the amount_to_pay in loyalty points.
            amount_to_pay_in_lp = amount_to_pay * available_lp['OILoyaltyPointsRate']

            if available_lp['RemainingPoints'] > amount_to_pay_in_lp:
                # The whole amount can be redeemed by loyalty points.
                lp_applied = amount_to_pay_in_lp
                remaining_lp = available_lp['RemainingPoints'] - amount_to_pay_in_lp
                amount_to_pay = 0
            else:
                # The whole amount can not be redeemed fully by the loyalty points.
                lp_applied = available_lp['RemainingPoints']
                # No remaining LP will be available.
                remaining_lp = 0
                amount_to_pay = amount_to_pay - (available_lp['RemainingPoints'] * available_lp['OILoyaltyPointsRate'])

            er_transaction_code = f'T{egrn}'

            applied_lp['lp_applied'] = lp_applied
            applied_lp['lp_in_rupees'] = lp_applied * available_lp['OILoyaltyPointsRate']
            applied_lp['OILoyaltyPointsRate'] = available_lp['OILoyaltyPointsRate']
            applied_lp['RemainingPoints'] = remaining_lp
            applied_lp['er_transaction_code'] = er_transaction_code

            # Blocking the loyalty points.
            er_module.block_er_loyalty_points(customer_code, er_transaction_code, lp_applied,
                                              amount_to_pay, egrn)

    result = {'amount_to_pay': amount_to_pay, 'applied_lp': applied_lp}
    return result


# def create_trn(order_id, delivery_request_id, egrn_details, attached_coupons,
#                attached_loyalty_points,
#                invoice_discount_details, collected, after_pre_applied, partial_payment, collected_amount,
#                amount_to_pay, branch_code):
#     """
#     Function for creating the TRN.
#     Here, the customer is not paying the full amount instead partial - raise a complaint against this order and
#     generate a TRN against this order. (No settlement happens here).
#     @param order_id: CustomerCode of the customer.
#     @param delivery_request_id: Delivery request id of the order.
#     @param egrn_details: Unsettled EGRN details.
#     @param attached_coupons: Applied coupons.
#     @param attached_loyalty_points: Applied loyalty points.
#     @param invoice_discount_details: Global invoice discount details.
#     @param collected: Collected amount details from the customer directly.
#     @param after_pre_applied: Pre applied details (coupons, loyalty points, invoice level discount..etc.)
#     @param partial_payment: Whether this is a partial payment or not.
#     @param collected_amount: Amount collected from the customer.
#     @param amount_to_pay: Actual amount needs to pay by the customer.
#     @return:
#     """
#     # Status flag of the TRN creation process.
#     trn_creation = False

#     # Getting the order details.
#     order_details = db.session.query(Order.OrderId, Order.EGRN, Order.OrderCode, Order.BranchCode,
#                                      Customer.CustomerCode, Customer.MobileNo).join(
#         Customer, Order.CustomerId == Customer.CustomerId).filter(Order.IsDeleted == 0,
#                                                                   Order.OrderId == order_id).one_or_none()

#     # Getting the delivery request details.
#     delivery_request_details = db.session.query(DeliveryRequest).filter(DeliveryRequest.IsDeleted == 0,
#                                                                         DeliveryRequest.DeliveryRequestId == delivery_request_id).one_or_none()

#     if order_details is not None and delivery_request_details is not None:
#         # Order details and delivery request details are found.
#         if delivery_request_details.IsPartial:
#             # This is a partial garment delivery.
#             # Getting the delivery garments.
#             delivery_garments = db.session.query(DeliveryGarment).filter(
#                 DeliveryGarment.DeliveryRequestId == delivery_request_id, DeliveryGarment.IsDeleted == 0).all()

#             # Populating a list of POS order garment Ids based on the delivery garments.
#             pos_order_garment_ids = [garment.POSOrderGarmentId for garment in delivery_garments]

#         else:
#             # The order is not a partial garments delivery.
#             # Get all the garments from the OrderGarments table.
#             delivery_garments = db.session.query(
#                 OrderGarment).filter(
#                 OrderGarment.OrderId == order_id,
#                 OrderGarment.GarmentStatusId == 10,
#                 OrderGarment.IsDeleted == 0).all()

#             # Populating a list of POS order garment Ids based on the delivery garments.
#             pos_order_garment_ids = [garment.POSOrderGarmentId for garment in delivery_garments]

#         # Populating the comma separated string of POS order garment ids.
#         pos_order_garment_ids_string = ','.join(map(str, pos_order_garment_ids))

#         # Check if the order garments already have a TRN or not. If the order garments have TRN,
#         # those garments will be skipped for TRN creation.
#         non_trn_garments = []
#         garments_with_trn_details = get_garments_with_trn_status(order_details.EGRN, pos_order_garment_ids_string)

#         for garment in garments_with_trn_details:
#             # Loop over the selected garments and check if the garment has an existing TRN or not.
#             for pos_order_garment_id in pos_order_garment_ids:
#                 if pos_order_garment_id == garment['ordergarmentid'] and garment['TRNGenerated'] == "NO":
#                     # This garment has no existing TRN. So this garment can be selected for
#                     # TRN generation.
#                     non_trn_garments.append(pos_order_garment_id)

#         # After considering the existing TRNs, populate the new POS order garment id string
#         # to create the new TRN. (Avoid the garments that has already an existing TRN).
#         pos_order_garment_ids_string = ','.join(map(str, non_trn_garments))

#         # Generating the new invoice id.
#         new_invoice_id = db.session.query(func.newid().label('Id')).one_or_none()

#         # Getting the TRN.
#         if CURRENT_ENV == 'development':
#             trn = db.session.query(func.JFSL_UAT.dbo.FINDID('TRNNo', 'SPEC000001').label('TRN')).one_or_none()
#         else:
#             trn = db.session.query(func.JFSL.dbo.FINDID('TRNNo', branch_code).label('TRN')).one_or_none()

#         # Check if the loyalty points is attached to it or not.
#         if attached_loyalty_points:
#             # Loyalty points attached.
#             lp_applied = attached_loyalty_points['lp_applied']
#             lp_applied_sp_param = f"@LOYALTYPOINTS={lp_applied}"
#             lp_in_rupees = attached_loyalty_points['lp_in_rupees']
#         else:
#             lp_applied = None
#             lp_applied_sp_param = "@LOYALTYPOINTS=null"
#             lp_in_rupees = 0

#         # Getting the available points for the customer.
#         available_lp = er_module.get_available_er_lp(order_details.CustomerCode)
#         total_discount_amount = after_pre_applied['total_discount']
#         service_tax = (egrn_details['details']['BASICAMOUNT'] - total_discount_amount) * 18 / 100

#         # Calling SP for TRN CREATION.
#         query = f"""EXEC {SERVER_DB}.dbo.InvoiceCalculation_DeliveryNote @invoiceid='{new_invoice_id.Id}',
#         @TRNNO={trn.TRN},@Orderid='{order_details.OrderCode}',
#         @BASIC={egrn_details['details']['BASICAMOUNTWIHTOUTTAX']},
#         @DISCOUNT={total_discount_amount},@TAX={service_tax},@INVOICESTATUS=6,
#         @BRANCHCODE='{order_details.BranchCode}',
#         @ROUNDOFF={round(round(egrn_details['details']['BASICAMOUNTWIHTOUTTAX'] + service_tax) - (egrn_details['details']['BASICAMOUNTWIHTOUTTAX'] + service_tax), 2)},
#         @MISDISCOUNT =0,
#         @CREATEDBY=1973,@REMARKS='',
#         @ORDERGARMENTIDS='{pos_order_garment_ids_string}',
#         @DCNO=null,{lp_applied_sp_param},
#         @LOYALTYPOINTSAMOUNT=0,@LOYALTYPOINTSRATE={available_lp['point_rate']},
#         @AVAILABLELOYALTYPOINTS={available_lp['available_points']}"""

#         # Calling the SP.
#         execute_with_commit(text(query))

#         # Based on the payment modes, save the payment details into the POS.
#         if attached_coupons:
#             # Saving the compensation coupons payment details into POS.
#             payment_mode = 'coupon'
#             for attached_coupon in attached_coupons:
#                 coupon_code = attached_coupon['COUPONCODE']
#                 redeemed_amount = attached_coupon['RedeemedAmount']
#                 queries.save_payment_details_into_pos(payment_mode, redeemed_amount, new_invoice_id, coupon_code)
#         for collection in collected:
#             if collection['mode'] == 'CASH_COLLECTION':
#                 # Saving the  cash payment details into the POS.
#                 payment_mode = 'Cash'
#                 queries.save_payment_details_into_pos(payment_mode, collection['amount'], new_invoice_id, '')
#                 # Saving the partial collection details into the table.
#                 queries.save_partial_payment_details(delivery_request_id, order_id, order_details.EGRN,
#                                                      collection['mode'], collection['amount'])
#             elif collection['mode'] == 'CARD_COLLECTION':
#                 # Saving the  card payment details into the POS.
#                 payment_mode = 'Card'
#                 queries.save_payment_details_into_pos(payment_mode, collection['amount'], new_invoice_id, '')
#                 # Saving the partial collection details into the table.
#                 queries.save_partial_payment_details(delivery_request_id, order_id, order_details.EGRN,
#                                                      collection['mode'], collection['amount'])

#             elif collection['mode'] == 'PHONEPE':
#                 # Saving the  phone pay payment details into the POS.
#                 payment_mode = 'Phonepe'
#                 queries.save_payment_details_into_pos(payment_mode, collection['amount'], new_invoice_id, '')
#                 # Saving the partial collection details into the table.
#                 queries.save_partial_payment_details(delivery_request_id, order_id, order_details.EGRN,
#                                                      collection['mode'], collection['amount'])


#             else:
#                 payment_mode = 'NA'

#         # Set the flag as True.
#         trn_creation = True

#         if trn_creation and partial_payment:
#             # After the successful TRN creation, SMS needs to be sent to customer.
#             # Triggering the SMS via alert engine.
#             query = f"""EXEC alert_Engine..ALERT_PROCESS @ALERT_CODE = 'PARTIAL_PAYMENT'
#                                              ,@EMAIL_ID = NULL
#                                              ,@MOBILE_NO = '{order_details.MobileNo}'
#                                              ,@SUBJECT = NULL
#                                              ,@DISPATCH_FLAG = 'OFF'
#                                              ,@EMAIL_SENDER_ADD = NULL
#                                              ,@SMS_SENDER_ADD = NULL
#                                              ,@P1 = {float(collected_amount)}
#                                              ,@P2 = {amount_to_pay}
#                                              ,@P3 = '{order_details.EGRN}'
#                                              ,@P4 = null
#                                              ,@P5 = NULL
#                                              ,@P6 = NULL
#                                              ,@P7 = NULL
#                                              ,@P8 = NULL
#                                              ,@P9 = NULL
#                                              ,@P10 = NULL
#                                              ,@P11 = NULL
#                                              ,@P12 = NULL
#                                              ,@P13 = NULL
#                                              ,@P14 = NULL
#                                              ,@P15 = NULL
#                                              ,@P16 = NULL
#                                              ,@P17 = NULL
#                                              ,@P18 = NULL
#                                              ,@P19 = NULL
#                                              ,@P20 = NULL
#                                              ,@REC_ID = '0'"""
#             execute_with_commit(text(query))
#             log_data = {
#                 'SMS': query
#             }
#             info_logger(f'Route: {request.path}').info(json.dumps(log_data))
#     return trn_creation

def create_trn(TRNNo, egrn, customer_code, egrn_details, attached_coupons,
               attached_loyalty_points,
               invoice_discount_details, collected, after_pre_applied, partial_payment, collected_amount,
               amount_to_pay, branch_code, OrderId, MobileNo):
    """
    Function for creating the TRN.
    Here, the customer is not paying the full amount instead partial - raise a complaint against this order and
    generate a TRN against this order. (No settlement happens here).
    @param order_id: CustomerCode of the customer.
    @param delivery_request_id: Delivery request id of the order.
    @param egrn_details: Unsettled EGRN details.
    @param attached_coupons: Applied coupons.
    @param attached_loyalty_points: Applied loyalty points.
    @param invoice_discount_details: Global invoice discount details.
    @param collected: Collected amount details from the customer directly.
    @param after_pre_applied: Pre applied details (coupons, loyalty points, invoice level discount..etc.)
    @param partial_payment: Whether this is a partial payment or not.
    @param collected_amount: Amount collected from the customer.
    @param amount_to_pay: Actual amount needs to pay by the customer.
    @return:
    """
    # Status flag of the TRN creation process.
    trn_creation = False
    query = f"EXEC {SERVER_DB}.dbo.SPFabGetGarementPaymentInfoDetails @TRNNo='{TRNNo}'"

    trn_details = CallSP(query).execute().fetchall()
    pos_order_garment_ids = []
    for order_garment_ids in trn_details:
        pos_order_garment_ids.append(order_garment_ids['ordergarmentid'])

    # Check if the order garments already have a TRN or not. If the order garments have TRN,
    # those garments will be skipped for TRN creation.
    non_trn_garments = []
    garments_with_trn_details = get_garments_with_trn_status(TRNNo)

    for garment in garments_with_trn_details:
        # Loop over the selected garments and check if the garment has an existing TRN or not.
        for pos_order_garment_id in pos_order_garment_ids:
            if pos_order_garment_id == garment['ordergarmentid'] and garment['TRNGenerated'] == "NO":
                # This garment has no existing TRN. So this garment can be selected for
                # TRN generation.
                non_trn_garments.append(pos_order_garment_id)

    # After considering the existing TRNs, populate the new POS order garment id string
    # to create the new TRN. (Avoid the garments that has already an existing TRN).
    pos_order_garment_ids_string = ','.join(map(str, non_trn_garments))

    # Generating the new invoice id.
    new_invoice_id = db.session.query(func.newid().label('Id')).one_or_none()

    # Getting the TRN.
    if CURRENT_ENV == 'development':
        trn = db.session.query(func.JFSL_UAT.dbo.FINDID('TRNNo', 'SPEC000001').label('TRN')).one_or_none()
    else:
        trn = db.session.query(func.JFSL.dbo.FINDID('TRNNo', branch_code).label('TRN')).one_or_none()

    # Check if the loyalty points is attached to it or not.
    if attached_loyalty_points:
        # Loyalty points attached.
        lp_applied = attached_loyalty_points['lp_applied']
        lp_applied_sp_param = f"@LOYALTYPOINTS={lp_applied}"
        lp_in_rupees = attached_loyalty_points['lp_in_rupees']
    else:
        lp_applied = None
        lp_applied_sp_param = "@LOYALTYPOINTS=null"
        lp_in_rupees = 0

    # Getting the available points for the customer.
    available_lp = er_module.get_available_er_lp(customer_code)
    total_discount_amount = after_pre_applied['total_discount']
    service_tax = (egrn_details['details']['BASICAMOUNT'] - total_discount_amount) * 18 / 100

    # Calling SP for TRN CREATION.
    query = f"""EXEC {SERVER_DB}.dbo.InvoiceCalculation_DeliveryNote @invoiceid='{new_invoice_id.Id}',
    @TRNNO={TRNNo},@Orderid='{OrderId}',
    @BASIC={egrn_details['details']['BASICAMOUNTWIHTOUTTAX']}, 
    @DISCOUNT={total_discount_amount},@TAX={service_tax},@INVOICESTATUS=6,
    @BRANCHCODE='{branch_code}',
    @ROUNDOFF={round(round(egrn_details['details']['BASICAMOUNTWIHTOUTTAX'] + service_tax) - (egrn_details['details']['BASICAMOUNTWIHTOUTTAX'] + service_tax), 2)},
    @MISDISCOUNT =0,
    @CREATEDBY=1973,@REMARKS='',
    @ORDERGARMENTIDS='{pos_order_garment_ids_string}',
    @DCNO=null,{lp_applied_sp_param},
    @LOYALTYPOINTSAMOUNT=0,@LOYALTYPOINTSRATE={available_lp['point_rate']},
    @AVAILABLELOYALTYPOINTS={available_lp['available_points']}"""

    # Calling the SP.
    execute_with_commit(text(query))

    # Based on the payment modes, save the payment details into the POS.
    if attached_coupons:
        # Saving the compensation coupons payment details into POS.
        payment_mode = 'coupon'
        for attached_coupon in attached_coupons:
            coupon_code = attached_coupon['COUPONCODE']
            redeemed_amount = attached_coupon['RedeemedAmount']
            queries.save_payment_details_into_pos(payment_mode, redeemed_amount, new_invoice_id, coupon_code)
    for collection in collected:
        if collection['mode'] == 'CASH_COLLECTION':
            # Saving the  cash payment details into the POS.
            payment_mode = 'Cash'
            queries.save_payment_details_into_pos(payment_mode, collection['amount'], new_invoice_id, '')
            # Saving the partial collection details into the table.
            # queries.save_partial_payment_details(delivery_request_id, order_id, order_details.EGRN,
            #                                      collection['mode'], collection['amount'])
        elif collection['mode'] == 'CARD_COLLECTION':
            # Saving the  card payment details into the POS.
            payment_mode = 'Card'
            queries.save_payment_details_into_pos(payment_mode, collection['amount'], new_invoice_id, '')
            # Saving the partial collection details into the table.
            # queries.save_partial_payment_details(delivery_request_id, order_id, order_details.EGRN,
            #                                      collection['mode'], collection['amount'])

        elif collection['mode'] == 'PHONEPE':
            # Saving the  phone pay payment details into the POS.
            payment_mode = 'Phonepe'
            queries.save_payment_details_into_pos(payment_mode, collection['amount'], new_invoice_id, '')
            # Saving the partial collection details into the table.
            # queries.save_partial_payment_details(delivery_request_id, order_id, order_details.EGRN,
            #                                      collection['mode'], collection['amount'])
        else:
            payment_mode = 'NA'

        # Set the flag as True.
        trn_creation = True

        if trn_creation and partial_payment:
            # After the successful TRN creation, SMS needs to be sent to customer.
            # Triggering the SMS via alert engine.
            query = f"""EXEC alert_Engine..ALERT_PROCESS @ALERT_CODE = 'PARTIAL_PAYMENT'
                                             ,@EMAIL_ID = NULL
                                             ,@MOBILE_NO = '{MobileNo}'
                                             ,@SUBJECT = NULL
                                             ,@DISPATCH_FLAG = 'OFF'
                                             ,@EMAIL_SENDER_ADD = NULL
                                             ,@SMS_SENDER_ADD = NULL
                                             ,@P1 = {float(collected_amount)}
                                             ,@P2 = {amount_to_pay}
                                             ,@P3 = '{egrn}'
                                             ,@P4 = null
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
            execute_with_commit(text(query))
            log_data = {
                'SMS': query
            }
            info_logger(f'Route: {request.path}').info(json.dumps(log_data))
    return trn_creation


# def get_garments_payment_status(egrn, pos_order_garments_ids):
#     """
#     Function for calling the getGarementPaymentInfoDetails SP - for checking
#     the payment status of the garments.
#     @param egrn: EGRN of the order.
#     @param pos_order_garments_ids: POS order garment ids.
#     @return: Status (String).
#     """
#     query = f"EXEC {SERVER_DB}.dbo.getGarementPaymentInfoDetails @egrnno='{egrn}',@ORDERGARMENTID='{pos_order_garments_ids}'"
#     result = CallSP(query).execute().fetchall()

#     log_data = {
#         'query of get_garments_payment_status': query,
#         'result of get_garments_payment_status sp': result
#     }
#     info_logger(f'Route: {request.path}').info(json.dumps(log_data))
#     received = []
#     not_received = []
#     for garment_payment_status in result:
#         if garment_payment_status['AmountReceived'] == "YES":
#             received.append(True)
#             # elif garment_payment_status['TRNGenerated'] == "YES":
#             # received.append(True)
#         else:
#             not_received.append(False)
#     if received and not_received:
#         payment_status = "Partially paid"
#     elif received and not not_received:
#         payment_status = "Paid"
#     else:
#         payment_status = "Unpaid"
#     # Populating a list of payment details
#     data = {"Status": payment_status, "FinalAmount": result[0]['FinalAmount']}


#     return data

def get_garments_payment_status_old(EGRN, TRNNo):
    """
    Function for calling the getGarementPaymentInfoDetails SP - for checking
    the payment status of the garments.
    @param egrn: EGRN of the order.
    @param pos_order_garments_ids: POS order garment ids.
    @return: Status (String).
    """
    query = f"EXEC {SERVER_DB}.dbo.SPFabGetGarementPaymentInfoDetails @TRNNo='{TRNNo}'"
    result = CallSP(query).execute().fetchall()

    log_data = {
        'query of get_garments_payment_status': query,
        'result of get_garments_payment_status sp': result
    }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))
    received = []
    not_received = []
    for garment_payment_status in result:
        if garment_payment_status['AmountReceived'] == "YES":
            received.append(True)
            # elif garment_payment_status['TRNGenerated'] == "YES":
            # received.append(True)
        else:
            not_received.append(False)
    if received and not_received:
        payment_status = "Partially paid"
        print(payment_status)
    elif received and not not_received:
        payment_status = "Paid"
        print(payment_status)
    else:
        payment_status = "Unpaid"
        # print(payment_status)
        # print("haii")
    # Populating a list of payment details
    data = {"Status": payment_status, "FinalAmount": result[0]['FinalAmount']}

    return data


def get_garments_payment_status(EGRN, TRNNo):
    """
    Function for calling the getGarementPaymentInfoDetails SP - for checking
    the payment status of the garments.
    @param egrn: EGRN of the order.
    @param pos_order_garments_ids: POS order garment ids.
    @return: Status (String).


    """

    log_data = {
        'query of get_garments_payment_status egrn': EGRN,
        'result of get_garments_payment_status pos_order_garments_ids': TRNNo
    }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))
    query = f"EXEC {SERVER_DB}.dbo.SPFabGetGarementPaymentInfoDetails @TRNNo='{TRNNo}'"
    result = CallSP(query).execute().fetchall()

    log_data = {
        'query of get_garments_payment_status': query,
        'result of get_garments_payment_status sp': result
    }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))
    received = []
    not_received = []
    for garment_payment_status in result:
        if garment_payment_status['AmountReceived'] == "YES":
            received.append(True)
            # elif garment_payment_status['TRNGenerated'] == "YES":
            # received.append(True)
        else:
            not_received.append(False)
    if received and not_received:
        payment_status = "Partially paid"
        print(payment_status)
    elif received and not not_received:

        # orderid = db.session.query(Order.OrderId).filter(Order.EGRN == egrn, Order.IsDeleted == 0).one_or_none()
        # #print(orderid)
        # orderid_dtls = orderid.OrderId
        # #print(orderid_dtls)
        # if orderid is not None:
        #     partial_check = db.session.query(DeliveryRequest.IsPartial).filter(DeliveryRequest.OrderId == orderid_dtls,
        #                                                                        DeliveryRequest.IsDeleted == 0).one_or_none()
        #     if partial_check is not None:

        #         if partial_check == 0:
        #             payment_status = "Fully Paid"
        #             print(payment_status)
        #         else:
        #             payment_status = "Partially Paid"
        #     else:
        #         pass
        # else:
        #     pass

        payment_status = "Fully Paid"
        print(payment_status)
    else:
        payment_status = "Unpaid"
        # print(payment_status)
        # print("haii")
    # Populating a list of payment details
    data = {"Status": payment_status, "FinalAmount": result[0]['FinalAmount']}

    return data


def get_garments_with_trn_status(TRNNo):
    """
    Function for calling the getGarementPaymentInfoDetails SP - for checking
    the payment status of the garments.
    @param egrn: EGRN of the order.
    @param pos_order_garments_ids: POS order garment ids.
    @return: SP result.
    """
    query = f"EXEC {SERVER_DB}.dbo.SPFabGetGarementPaymentInfoDetails @TRNNo='{TRNNo}'"

    result = CallSP(query).execute().fetchall()

    log_data = {
        'get_garments_with_trn_status :': query,
        'get_garments_with_trn_status result:': result
    }
    info_logger(f'Route: {request.path}').info(json.dumps(log_data))

    return result
