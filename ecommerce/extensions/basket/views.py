from __future__ import unicode_literals
import hashlib
import logging

from django.conf import settings
from django.http import HttpResponseBadRequest, HttpResponseRedirect
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from requests.exceptions import ConnectionError, Timeout
from oscar.apps.basket.views import *  # pylint: disable=wildcard-import, unused-wildcard-import
from edx_rest_api_client.client import EdxRestApiClient
from slumber.exceptions import SlumberBaseException

from ecommerce.coupons.views import get_voucher_from_code
from ecommerce.extensions.api.data import get_lms_footer
from ecommerce.extensions.basket.utils import get_certificate_type_display_value, prepare_basket
from ecommerce.extensions.payment.helpers import get_processor_class
from ecommerce.extensions.partner.shortcuts import get_partner_for_site
from ecommerce.extensions.voucher.utils import get_voucher_discount_info
from ecommerce.settings import get_lms_url

Benefit = get_model('offer', 'Benefit')
logger = logging.getLogger(__name__)
StockRecord = get_model('partner', 'StockRecord')


class BasketSingleItemView(View):
    """
    View that adds a single product to a user's basket.
    An additional coupon code can be supplied so the offer is applied to the basket.
    """
    def get(self, request):
        partner = get_partner_for_site(request)

        sku = request.GET.get('sku', None)
        code = request.GET.get('code', None)

        if not sku:
            return HttpResponseBadRequest(_('No SKU provided.'))

        if code:
            voucher, __ = get_voucher_from_code(code=code)
        else:
            voucher = None

        try:
            product = StockRecord.objects.get(partner=partner, partner_sku=sku).product
        except StockRecord.DoesNotExist:
            return HttpResponseBadRequest(_('SKU [{sku}] does not exist.'.format(sku=sku)))

        purchase_info = request.strategy.fetch_for_product(product)
        if not purchase_info.availability.is_available_to_buy:
            return HttpResponseBadRequest(_('Product [{product}] not available to buy.'.format(product=product.title)))

        prepare_basket(request, product, voucher)
        return HttpResponseRedirect(reverse('basket:summary'), status=303)
