"""Ecommerce API constants."""


class APIDictionaryKeys(object):
    """Dictionary keys used repeatedly in the ecommerce API."""
    BASKET_ID = u'id'
    BENEFIT_TYPE = u'benefit_type'
    BENEFIT_VALUE = u'benefit_value'
    CATEGORY_IDS = u'category_ids'
    CHECKOUT = u'checkout'
    CLIENT = u'client'
    CODE = u'code'
    COUPON_ID = u'coupon_id'
    END_DATE = u'end_date'
    NOTE = u'note'
    ORDER = u'order'
    ORDER_NUMBER = u'number'
    ORDER_TOTAL = u'total'
    PAYMENT_DATA = u'payment_data'
    PAYMENT_FORM_DATA = u'payment_form_data'
    PAYMENT_PAGE_URL = u'payment_page_url'
    PAYMENT_PROCESSOR_NAME = u'payment_processor_name'
    PRICE = u'price'
    PRODUCTS = u'products'
    QUANTITY = u'quantity'
    SHIPPING_CHARGE = u'shipping_charge'
    SHIPPING_METHOD = u'shipping_method'
    START_DATE = u'start_date'
    STOCK_RECORD_IDS = u'stock_record_ids'
    SKU = u'sku'
    TITLE = u'title'
    VOUCHER_TYPE = u'voucher_type'


class APIConstants(object):
    """Constants used throughout the ecommerce API."""
    FREE = 0
    KEYS = APIDictionaryKeys()
    UPDATEABLE_VOUCHER_FIELDS = [
        {
            'request_data_key': KEYS.END_DATE,
            'attribute': 'end_datetime'
        },
        {
            'request_data_key': KEYS.START_DATE,
            'attribute': 'start_datetime'
        },
        {
            'request_data_key': KEYS.TITLE,
            'attribute': 'name'
        }
    ]
