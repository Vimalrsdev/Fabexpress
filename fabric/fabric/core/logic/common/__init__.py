"""
These are the common functions/logic that are related to the Fabric project.
These functions can be accessed by delivery app/customer app/store web console..etc.
"""
from fabric.modules.settings.project_settings import LOCAL_DB, SERVER_DB
from fabric.modules.generic.classes import CallSP


def validate_discount_code(discount_code, source, egrn, customer_code, branch_code, is_er_discount):
    """
    Function for validating a discount code by calling a stored procedure.
    @param discount_code: DiscountCode given to a user. eg: SAREESPA
    @param source: Whether the discount is applying at the time of 'pickup' or 'order'.
    @param egrn: EGRN of the order if any.
    @param customer_code: CustomerCode of the customer.
    @param branch_code: BranchCode of the customer.
    @param is_er_discount: Whether the DiscountCode is an EasyRewardz discount code or not.
    @return: result of the stored procedure as a dict or None if it fails to execute.
    """
    # Constructing the query string for the execution.

    if source == "order":
        # Here, the source is order. So EGRN need to be passed to the SP.
        query = f"EXEC {SERVER_DB}..validateDiscountCode @PROMOCODE='{discount_code}',@source='{source}',@CUSTOMERCODE='{customer_code}',@Branchcode='{branch_code}',@EGRNNo='{egrn}'"
    else:
        # source can also be pickup.
        query = f"EXEC {SERVER_DB}..validateDiscountCode @PROMOCODE='{discount_code}',@source='{source}',@CUSTOMERCODE='{customer_code}',@Branchcode='{branch_code}',@EasyDiscount='{is_er_discount}'"

    # Executing the stored procedure.
    result = CallSP(query).execute().fetchone()
    return result


def validate_coupon_code(coupon_code, customer_code, branch_code, source, egrn):
    """
    Function for validating the coupon code (compensation coupon, marketing coupon...etc.)
    @param coupon_code: CouponCode given to a customer (eg: 2000010821)
    @param customer_code: POS customer code.
    @param branch_code: branch code of the customer.
    @param source: If the order has already created and has EGRN, then source will be order; otherwise pickup.
    @param egrn: EGRN of the order.
    @return:
    """
    # Constructing the query.
    query = f"EXEC {SERVER_DB}.dbo.ValidatePromocodeforApp @CouponCode='{coupon_code}', @Customercode='{customer_code}',@isCode='1', @Branch='{branch_code}',@Source='{source}',@EGRNNO='{egrn}'"

    # Executing the stored procedure.
    result = CallSP(query).execute().fetchone()
    return result
