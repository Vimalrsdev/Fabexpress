"""
------------------------
Payment queries
The module deals with calling of commonly used functions of the Payment module.
------------------------
Coded by: Krishna Prasad K
© Jyothy Fabricare Services LTD.
------------------------
"""
from sqlalchemy import text

from fabric import db
from fabric.generic.classes import CallSP
from fabric.generic.functions import get_current_date
from fabric.modules.models import TransactionInfo, TransactionPaymentInfo, PartialCollection
from fabric.settings.project_settings import SERVER_DB


def update_transaction_info_with_lp_details(new_transaction_info_id, attached_loyalty_points):
    """
    Function for updating the TransactionInfo table with the after the loyalty points applied.
    @param new_transaction_info_id: New TransactionInfo table's Id.
    @param attached_loyalty_points: Dict variable consisting of the attached loyalty points.
    @return:
    """
    # Updating the TransactionInfo table about the loyalty points attached.
    transaction_info_details = db.session.query(TransactionInfo).filter(
        TransactionInfo.Id == new_transaction_info_id).one_or_none()

    if transaction_info_details is not None:
        # Updating the TransactionInfo table with the loyalty points details.
        transaction_info_details.Loyaltypoints = attached_loyalty_points['lp_applied']
        transaction_info_details.LoyaltyPointsRate = attached_loyalty_points['OILoyaltyPointsRate']
        transaction_info_details.LoyaltyPointsAmount = attached_loyalty_points['lp_in_rupees']
        transaction_info_details.AvailableLoyaltyPoints = attached_loyalty_points['RemainingPoints']
        transaction_info_details.ERTransactionCode = attached_loyalty_points['er_transaction_code']
        db.session.commit()


def insert_transaction_payment_info_with_coupon_details(attached_coupons, transaction_id, payment_id, round_off, trn_number, egrn):
    """
    Inserting the TransactionPaymentInfo table with the applied compensation/marketing coupon details.
    @param attached_coupons: List of compensation coupon details.
    @param transaction_id: TransactionId of the TransactionPaymentInfo table.
    @param payment_id: PaymentId of the TransactionPaymentInfo table.
    @param round_off: Round off amount.
    :param trn_number:
    @return:
    """
    redeemed_amount = 0
    if attached_coupons:
        for attached_coupon in attached_coupons:
            redeemed_amount = attached_coupon['RedeemedAmount']
            if attached_coupon['ATTACHEDATEGRNLEVEL'] == 1:
                query = f"EXEC {SERVER_DB}.dbo.USP_GET_PREAPPLIED_COUPON_AMOUNT @COUPONCODE='{attached_coupon['COUPONCODE']}', @TRNNO={trn_number}, @EGRN={egrn}"
                result = CallSP(query).execute().fetchall()
                redeemed_amount = result[0].get('AMOUNT')
            new_transaction_payment_info = TransactionPaymentInfo(
                PaymentId=payment_id,
                CreatedOn=get_current_date(),
                TransactionId=transaction_id,
                PaymentMode='COUPON',
                CouponCode=attached_coupon['COUPONCODE'],
                PaymentAmount=redeemed_amount,
                RoundOff=round_off
            )
            db.session.add(new_transaction_payment_info)
            db.session.commit()
    return redeemed_amount

def get_customer_details_from_egrn(egrn):
    """
    Function for calling a SP that will returns the customer details from an EGRN.
    @param egrn: EGRN of the order.
    @return: SP result.
    """
    query = f"EXEC {SERVER_DB}.dbo.GetCustomerDataForPaymentCompletion @NO='{egrn}'"
    result = CallSP(query).execute().fetchone()
    return result


def save_payment_details_into_pos(payment_mode, amount, invoice_id, coupon_code):
    """
    Function for saving the payment details based on the payment modes(cash,card and coupon) into
    POS.
    @param payment_mode: Cash,Card or Coupon.
    @param amount: Amount paid via payment_mode
    @param invoice_id: Newly generated invoice id.
    @param coupon_code: Applied compensation coupon code.
    @return:
    """
    query = f"""EXEC {SERVER_DB}.dbo.CDC_InsertIntoInvoicePaymentForMonthySettleForMobileApp
            @InvoiceNo='{invoice_id.Id}',
            @PaymentMode='{payment_mode}',
            @Amount={amount},@ChequeNo='',
            @ChequeDate =null,
            @BankName='',
            @BranchName='',
            @CardNo='',
            @TransationNo='',
            @CouponCode='{coupon_code}',
            @Remark='',
            @AmountReconcile=0.00,
            @Status=0,
            @CreatedBy=1973,
            @MobileNo='',
            @RaiseComplain=1
            """
    # Calling the SP.
    execute_with_commit(text(query))


def save_partial_payment_details(delivery_request_id, order_id, egrn, payment_mode, amount):
    """
    Function for saving the partial collection details into the PartialCollections table.
    @param delivery_request_id: DeliveryRequestId of the delivery request.
    @param order_id: OrderId of the order.
    @param egrn: EGRN of the order.
    @param payment_mode: PaymentMode of the transaction.
    @param amount: Amount collected.
    @return:
    """
    # Constructing a new PartialCollection object.
    new_partial_collection = PartialCollection(
        DeliveryRequestId=delivery_request_id,
        OrderId=order_id,
        EGRN=egrn,
        PaymentMode=payment_mode,
        CollectedAmount=amount,
        RecordCreatedDate=get_current_date(),
        RecordLastUpdatedDate=get_current_date()
    )
    db.session.add(new_partial_collection)
    # Saving the details into the table.
    db.session.commit()
