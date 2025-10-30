"""
------------------------
EasyRewardz queries
The module deals with calling of DB queries/stored procedures regarding EasyRewardz integration.
------------------------
Coded by: Krishna Prasad K
© Jyothy Fabricare Services LTD.
------------------------
"""

from fabric.settings.project_settings import SERVER_DB
from fabric.generic.classes import CallSP


def get_lp_from_egrn(egrn):
    """
    Getting the loyalty points details from an EGRN
    @param egrn:
    @return: SP result.
    """
    query = f"EXEC {SERVER_DB}.dbo.getAppliedAndAvailLP_MOBILE @EGRNNO='{egrn}',@DCNO=''"
    result = CallSP(query).execute().fetchone()
    return result


def get_er_coupon_data_for_confirmation(egrn, invoice_number=None):
    """
    After the settlement of the order, call this SP to get the current status of the ER coupon in this
    order (if any) - Useful or calling the use coupon API.
    @param egrn EGRN of the order.
    @param invoice_number - Invoice number of the order.
    @return:SP result.
    """
    if invoice_number is not None:
        query = f"EXEC {SERVER_DB}.dbo.GetAttachedERCouponData_Mobile @EGRNNo='{egrn}',@InvoiceNo='{invoice_number}'"
    else:
        query = f"EXEC {SERVER_DB}.dbo.GetAttachedERCouponData_Mobile @EGRNNo='{egrn}'"

    result = CallSP(query).execute().fetchone()
    return result


def get_er_lp_data_for_confirmation(egrn, invoice_number=None):
    """
    After the settlement of the order, call this SP to get the current status of the er loyalty points in this
    order (if any).
    @param egrn EGRN of the order.
    @param invoice_number Invoice number of the order.
    @return: SP result.
    """
    if invoice_number is not None:
        query = f"EXEC {SERVER_DB}.dbo.GetAttachedERLoyaltyData_Mobile @EGRNNo='{egrn}',@InvoiceNo='{invoice_number}'"
    else:
        query = f"EXEC {SERVER_DB}.dbo.GetAttachedERLoyaltyData_Mobile @EGRNNo='{egrn}'"

    result = CallSP(query).execute().fetchone()
    return result


def get_attached_er_sku_details(egrn, invoice_number=None):
    """
    Function for getting the details for calling the Save SKU API (After the settlement of the order).
    @param egrn: EGRN of the order.
    @param invoice_number: Invoice number of the order.
    @return: SP result.
    """
    if invoice_number is not None:
        query = f"EXEC {SERVER_DB}.dbo.GetAttachedERInvoiceSKUData_Mobile @EGRNNo='{egrn}',@InvoiceNo='{invoice_number}'"
    else:
        query = f"EXEC {SERVER_DB}.dbo.GetAttachedERInvoiceSKUData_Mobile @EGRNNo='{egrn}'"

    result = CallSP(query).execute().fetchall()
    return result


def get_tax_details_for_save_sku(invoice_number):
    """
    Getting the tax details based on Invoice number. This will return Tax, SGST,CGST,IGST values.
    @param invoice_number: Invoice number of the order.
    @return: SP result.
    """
    query = f"EXEC {SERVER_DB}.dbo.ERGETDATAFORSAVESKU_APP @INVOICENO='{invoice_number}'"
    result = CallSP(query).execute().fetchone()
    return result
