from __future__ import unicode_literals

import logging

from django.http import HttpResponseBadRequest, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from requests.exceptions import ConnectionError, Timeout
from opaque_keys.edx.keys import CourseKey
from oscar.apps.basket.views import *  # pylint: disable=wildcard-import, unused-wildcard-import
from edx_rest_api_client.client import EdxRestApiClient
from slumber.exceptions import SlumberBaseException

from ecommerce.core.constants import ENROLLMENT_CODE_PRODUCT_CLASS_NAME, SEAT_PRODUCT_CLASS_NAME
from ecommerce.core.url_utils import get_lms_url, get_lms_enrollment_base_api_url
from ecommerce.coupons.views import get_voucher_from_code
from ecommerce.courses.utils import get_course_info_from_course_catalog, mode_for_seat
from ecommerce.extensions.analytics.utils import prepare_analytics_data
from ecommerce.extensions.basket.utils import get_certificate_type_display_value, prepare_basket, get_basket_switch_data
from ecommerce.extensions.offer.utils import format_benefit_value
from ecommerce.extensions.partner.shortcuts import get_partner_for_site

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
            course_key = product.attr.course_key

            api = EdxRestApiClient(
                get_lms_enrollment_base_api_url(),
                oauth_access_token=request.user.access_token,
                append_slash=False
            )
            logger.debug(
                'Getting enrollment information for [%s] in [%s].',
                request.user.username,
                course_key
            )
            status = api.enrollment(','.join([request.user.username, course_key])).get()
            username = request.user.username
            seat_type = mode_for_seat(product)
            if status and status.get('mode') == seat_type and status.get('is_active'):
                logger.warning(
                    'User [%s] attempted to repurchase the [%s] seat of course [%s]',
                    username,
                    seat_type,
                    course_key
                )
                return HttpResponseBadRequest(_('You are already enrolled in {course}.').format(
                    course=product.course.name))
        except StockRecord.DoesNotExist:
            return HttpResponseBadRequest(_('SKU [{sku}] does not exist.').format(sku=sku))
        except (ConnectionError, SlumberBaseException, Timeout) as ex:
            logger.exception(
                'Failed to retrieve enrollment details for [%s] in course [%s], Because of [%s]',
                request.user.username,
                course_key,
                ex,
            )
            return HttpResponseBadRequest(_('An error occurred while retrieving enrollment details. Please try again.'))
        purchase_info = request.strategy.fetch_for_product(product)
        if not purchase_info.availability.is_available_to_buy:
            return HttpResponseBadRequest(_('Product [{product}] not available to buy.').format(product=product.title))

        prepare_basket(request, product, voucher)
        return HttpResponseRedirect(reverse('basket:summary'), status=303)


class BasketSummaryView(BasketView):
    """
    Display basket contents and checkout/payment options.
    """
    def _determine_seat_type(self, product):
        """
        Return the seat type based on the product class
        """
        seat_type = None
        if product.get_product_class().name == SEAT_PRODUCT_CLASS_NAME:
            seat_type = get_certificate_type_display_value(product.attr.certificate_type)
        elif product.get_product_class().name == ENROLLMENT_CODE_PRODUCT_CLASS_NAME:
            seat_type = get_certificate_type_display_value(product.attr.seat_type)
        return seat_type

    def get_context_data(self, **kwargs):
        context = super(BasketSummaryView, self).get_context_data(**kwargs)
        formset = context.get('formset', [])
        lines = context.get('line_list', [])
        lines_data = []
        is_verification_required = is_bulk_purchase = False
        switch_link_text = partner_sku = ''

        for line in lines:
            course_key = CourseKey.from_string(line.product.attr.course_key)
            course_name = None
            image_url = None
            short_description = None
            try:
                course = get_course_info_from_course_catalog(self.request.site, course_key)
                image_url = get_lms_url(course['image']['src'])
                short_description = course['short_description']
                course_name = course['title']
            except (ConnectionError, SlumberBaseException, Timeout):
                logger.exception('Failed to retrieve data from Course API for course [%s].', course_key)

            # Set to true if any course in basket has bulk purchase scenario
            if line.product.get_product_class().name == ENROLLMENT_CODE_PRODUCT_CLASS_NAME:
                is_bulk_purchase = True
                # Iterate on message storage so all messages are marked as read
                list(messages.get_messages(self.request))

            # Get variables for alternative basket view
            switch_link_text, partner_sku = get_basket_switch_data(line.product)

            if line.has_discount:
                benefit = self.request.basket.applied_offers().values()[0].benefit
                benefit_value = format_benefit_value(benefit)
            else:
                benefit_value = None

            lines_data.append({
                'seat_type': self._determine_seat_type(line.product),
                'course_name': course_name,
                'course_key': course_key,
                'image_url': image_url,
                'course_short_description': short_description,
                'benefit_value': benefit_value,
                'enrollment_code': line.product.get_product_class().name == ENROLLMENT_CODE_PRODUCT_CLASS_NAME,
                'line': line,
            })

            context.update({
                'analytics_data': prepare_analytics_data(
                    self.request.user,
                    self.request.site.siteconfiguration.segment_key,
                    unicode(course_key)
                ),
            })

            # Check product attributes to determine if ID verification is required for this basket
            try:
                is_verification_required = is_verification_required or line.product.attr.id_verification_required
            except AttributeError:
                pass

        context.update({
            'free_basket': context['order_total'].incl_tax == 0,
            'payment_processors': self.request.site.siteconfiguration.get_payment_processors(),
            'homepage_url': get_lms_url(''),
            'formset_lines_data': zip(formset, lines_data),
            'is_verification_required': is_verification_required,
            'min_seat_quantity': 1,
            'is_bulk_purchase': is_bulk_purchase,
            'switch_link_text': switch_link_text,
            'partner_sku': partner_sku,
        })

        return context
