""" Adyen payment processing. """
from __future__ import unicode_literals

from datetime import datetime
import logging
from urlparse import urljoin

from oscar.apps.payment.exceptions import TransactionDeclined
from oscar.core.loading import get_model
import requests

from ecommerce.core.url_utils import get_lms_url
from ecommerce.core.constants import ISO_8601_FORMAT
from ecommerce.extensions.order.constants import PaymentEventTypeName
from ecommerce.extensions.payment.exceptions import InvalidAdyenDecision
from ecommerce.extensions.payment.processors import BasePaymentProcessor
from ecommerce.extensions.payment.utils import minor_units

logger = logging.getLogger(__name__)

PaymentEvent = get_model('order', 'PaymentEvent')
PaymentEventType = get_model('order', 'PaymentEventType')
PaymentProcessorResponse = get_model('payment', 'PaymentProcessorResponse')
ProductClass = get_model('catalogue', 'ProductClass')
Source = get_model('payment', 'Source')
SourceType = get_model('payment', 'SourceType')


class Adyen(BasePaymentProcessor):
    """
    Adyen CSE Integration (June 2016)

    For reference, see https://docs.adyen.com/developers
    """

    NAME = 'adyen'

    def __init__(self):
        """
        Constructs a new instance of the Adyen processor.

        Raises:
            KeyError: If no settings configured for this payment processor
        """
        configuration = self.configuration
        self.web_service_username = configuration['web_service_username']
        self.web_service_password = configuration['web_service_password']
        self.merchant_account_code = configuration['merchant_account_code']
        self.cse_js_url = configuration['cse_js_url']
        self.payment_api_url = configuration['payment_api_url']

    @property
    def generation_time(self):
        return datetime.utcnow().strftime(ISO_8601_FORMAT)

    @property
    def receipt_page_url(self):
        return get_lms_url(self.configuration['receipt_path'])

    @property
    def cancel_page_url(self):
        return get_lms_url(self.configuration['cancel_path'])

    def get_transaction_parameters(self, basket, request=None):
        """
        Not implemented
        """
        pass

    def authorise(self, basket, encryptedCardJSON):
        """
        Send authorise API request to Adyen to authorize payment.
        """
        response = requests.post(
            urljoin(self.payment_api_url, 'authorise'),
            auth=(self.web_service_username, self.web_service_password),
            headers={
                'Content-Type': 'application/json'
            },
            json={
                'additionalData': {
                    'card.encrypted.json': encryptedCardJSON
                },
                'amount': {
                    'value': minor_units(basket.total_incl_tax, basket.currency),
                    'currency': basket.currency
                },
                'reference': basket.order_number,
                'merchantAccount': self.merchant_account_code
            }
        )

        return response.status_code, response.json()

    def handle_processor_response(self, response, basket=None):
        """
        Handle an authorise response from Adyen.

        This method does the following:
            1. Create PaymentEvents and Sources for successful payments.

        Arguments:
            response (dict): Dictionary of parameters received from the payment processor.

        Keyword Arguments:
            basket (Basket): Basket being purchased via the payment processor.

        Raises:
            UserCancelled: Indicates the user cancelled payment.
            TransactionDeclined: Indicates the payment was declined by the processor.
            GatewayError: Indicates a general error on the part of the processor.
            InvalidCyberSourceDecision: Indicates an unknown decision value.
                Known values are ACCEPT, CANCEL, DECLINE, ERROR.
            PartialAuthorizationError: Indicates only a portion of the requested amount was authorized.
        """

        # Raise an exception for payments that were not accepted. Consuming code should be responsible for handling
        # and logging the exception.
        result_code = response['resultCode'].lower()
        if result_code != 'authorised':
            error_code = response['errorCode']
            # exception = {
            #     'decline': TransactionDeclined,
            # }.get(result_code, InvalidAdyenDecision)

            raise TransactionDeclined

        # Create Source to track all transactions related to this processor and order
        source_type, __ = SourceType.objects.get_or_create(name=self.NAME)
        currency = basket.currency
        total = basket.total_incl_tax
        transaction_id = response['pspReference']

        source = Source(source_type=source_type,
                        currency=currency,
                        amount_allocated=total,
                        amount_debited=total,
                        reference=transaction_id)

        # Create PaymentEvent to track
        event_type, __ = PaymentEventType.objects.get_or_create(name=PaymentEventTypeName.PAID)
        event = PaymentEvent(event_type=event_type, amount=total, reference=transaction_id, processor_name=self.NAME)

        return source, event

    def issue_credit(self, source, amount, currency):
        pass
