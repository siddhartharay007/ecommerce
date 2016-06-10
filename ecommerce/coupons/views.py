from __future__ import unicode_literals

import csv
from decimal import Decimal
import logging

from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.utils.decorators import method_decorator
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _
from django.shortcuts import render
from django.utils import timezone
from django.views.generic import TemplateView, View
from opaque_keys.edx.keys import CourseKey
from oscar.core.loading import get_class, get_model

from ecommerce.core.url_utils import get_ecommerce_url
from ecommerce.core.views import StaffOnlyMixin
from ecommerce.extensions.api import exceptions
from ecommerce.extensions.analytics.utils import prepare_analytics_data
from ecommerce.extensions.api.constants import APIConstants as AC
from ecommerce.extensions.basket.utils import prepare_basket
from ecommerce.extensions.checkout.mixins import EdxOrderPlacementMixin
from ecommerce.extensions.offer.utils import format_benefit_value

Applicator = get_class('offer.utils', 'Applicator')
Basket = get_model('basket', 'Basket')
Benefit = get_model('offer', 'Benefit')
logger = logging.getLogger(__name__)
OrderLineVouchers = get_model('voucher', 'OrderLineVouchers')
Order = get_model('order', 'Order')
Product = get_model('catalogue', 'Product')
Selector = get_class('partner.strategy', 'Selector')
StockRecord = get_model('partner', 'StockRecord')
Voucher = get_model('voucher', 'Voucher')


def get_voucher_from_code(code):
    """
    Returns a voucher and product for a given code.

    Arguments:
        code (str): The code of a coupon voucher.

    Returns:
        voucher (Voucher): The Voucher for the passed code.
        product (Product): The Product associated with the Voucher.

    Raises:
        Voucher.DoesNotExist: When no vouchers with provided code exist.
        ProductNotFoundError: When no products are associated with the voucher.
    """
    voucher = Voucher.objects.get(code=code)
    products = voucher.offers.all()[0].benefit.range.all_products()

    if products:
        return voucher, products
    else:
        raise exceptions.ProductNotFoundError()


def voucher_is_valid(voucher, products, request):
    """
    Checks if the voucher is valid.

    Arguments:
        voucher (Voucher): The Voucher that is checked.
        products (list of Products): Products associated with the Voucher.
        request (Request): WSGI request.

    Returns:
        bool (bool): True if the voucher is valid, False otherwise.
        msg (str): Message in case the voucher is invalid.
    """

    if voucher is None:
        return False, _('Coupon does not exist')

    if not voucher.is_active():
        now = timezone.now()
        if voucher.start_datetime > now:
            return False, _('This coupon code is not yet valid.')
        elif voucher.end_datetime < now:  # pragma: no cover
            return False, _('This coupon code has expired.')

    # We want to display the offer page to all users, including anonymous.
    if request.user.is_authenticated():
        avail, msg = voucher.is_available_to_user(request.user)
        if not avail:
            voucher_msg = msg.replace('voucher', 'coupon')
            return False, voucher_msg

    for product in products:
        purchase_info = request.strategy.fetch_for_product(product)
        if not purchase_info.availability.is_available_to_buy:
            return False, _('Product [{product}] not available for purchase.'.format(product=product))

    # If the voucher's number of applications exceeds it's limit.
    offer = voucher.offers.first()
    if offer.get_max_applications(request.user) == 0:
        return False, _('This coupon code is no longer available.')

    return True, ''


def get_course_seat(product, query_results, benefit, request):
    course = next((result for result in query_results if result['key'] == product.course_id), None)
    if course:
        if benefit.range.catalog:
            stock_record = benefit.range.catalog.stock_records.get(product__id=product.id)
        else:
            stock_record = StockRecord.objects.get(product__id=product.id)
        course['verified'] = product.attr.certificate_type == 'verified'
        course['price'] = stock_record.price_excl_tax
        course['sku'] = stock_record.partner_sku
        course['benefit_value'] = format_benefit_value(benefit)
        course['org'] = CourseKey.from_string(course['key']).org
        course['start_date'] = datetime.strptime(course['start'], '%Y-%m-%dT%H:%M:%SZ')

        if benefit.type == 'Percentage':
            new_price = course['price'] - (course['price'] * (benefit.value / 100))
        else:
            new_price = course['price'] - benefit.value
            if new_price < 0:
                new_price = Decimal(0)

        course['new_price'] = "%.2f" % new_price
        course['analytics_data'] = prepare_analytics_data(request.user,
                                                          request.site.siteconfiguration.segment_key,
                                                          product.course_id)
    return course


class CouponAppView(StaffOnlyMixin, TemplateView):
    template_name = 'coupons/coupon_app.html'

    def get_context_data(self, **kwargs):
        context = super(CouponAppView, self).get_context_data(**kwargs)
        context['admin'] = 'coupon'
        return context


class CouponOfferView(TemplateView):
    template_name = 'coupons/offer.html'

    def get_context_data(self, **kwargs):
        code = self.request.GET.get('code', None)
        if code is not None:
            try:
                voucher, products = get_voucher_from_code(code=code)
            except Voucher.DoesNotExist:
                return {
                    'error': _('Coupon does not exist'),
                }
            except exceptions.ProductNotFoundError:
                return {
                    'error': _('The voucher is not applicable to your current basket.'),
                }
            valid_voucher, msg = voucher_is_valid(voucher, products, self.request)
            if valid_voucher:
                return {
                    'valid_voucher': valid_voucher,
                }

            return {
                'error': msg,
            }
        return {
            'error': _('This coupon code is invalid.'),
        }

    def get(self, request, *args, **kwargs):
        """Get method for coupon redemption page."""
        return super(CouponOfferView, self).get(request, *args, **kwargs)


class CouponRedeemView(EdxOrderPlacementMixin, View):
    @method_decorator(login_required)
    def get(self, request):
        """
        Looks up the passed code and adds the matching product to a basket,
        then applies the voucher and if the basket total is FREE places the order and
        enrolls the user in the course.
        """
        template_name = 'coupons/offer.html'
        code = request.GET.get('code')
        sku = request.GET.get('sku')

        if not code:
            return render(request, template_name, {'error': _('Code not provided.')})
        if not sku:
            return render(request, template_name, {'error': _('SKU not provided.')})

        try:
            voucher = Voucher.objects.get(code=code)
        except Voucher.DoesNotExist:
            msg = 'No voucher found with code {code}'.format(code=code)
            return render(request, template_name, {'error': _(msg)})

        try:
            product = StockRecord.objects.get(partner_sku=sku).product
        except StockRecord.DoesNotExist:
            return render(request, template_name, {'error': _('The product does not exist.')})

        valid_voucher, msg = voucher_is_valid(voucher, [product], request)
        if not valid_voucher:
            return render(request, template_name, {'error': msg})

        basket = prepare_basket(request, product, voucher)
        if basket.total_excl_tax == AC.FREE:
            self.place_free_order(basket)
        else:
            return HttpResponseRedirect(reverse('basket:summary'))

        return HttpResponseRedirect(request.site.siteconfiguration.student_dashboard_url)


class EnrollmentCodeCsvView(View):
    """ Download enrollment code CSV file view. """

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(EnrollmentCodeCsvView, self).dispatch(*args, **kwargs)

    def get(self, request, number):
        """
        Creates a CSV for the order. The structure of the CSV looks like this:

           > Order Number:,EDX-100001

           > Seat in Demo with verified certificate (and ID verification)
           > Code,Redemption URL
           > J4HDI5OAUGCSUJJ3,ecommerce.server?code=J4HDI5OAUGCSUJJ3
           > OZCRR6WXLWGAFWZR,ecommerce.server?code=OZCRR6WXLWGAFWZR
           > 6KPYL6IO6Y3XL7SI,ecommerce.server?code=6KPYL6IO6Y3XL7SI
           > NPIJWIKNLRURYVU2,ecommerce.server?code=NPIJWIKNLRURYVU2
           > 6SZULKPZQYACAODC,ecommerce.server?code=6SZULKPZQYACAODC
           >

        Args:
            request (Request): The GET request
            number (str): Number of the order

        Returns:
            HttpResponse

        Raises:
            Http404: When an order number for a non-existing order is passed.
            PermissionDenied: When a user tries to download a CSV for an order that he did not make.

        """
        try:
            order = Order.objects.get(number=number)
        except Order.DoesNotExist:
            raise Http404('Order not found.')

        if request.user != order.user and not request.user.is_staff:
            raise PermissionDenied

        file_name = 'Enrollment code CSV order num {}'.format(order.number)
        file_name = '{filename}.csv'.format(filename=slugify(file_name))

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename={filename}'.format(filename=file_name)

        redeem_url = get_ecommerce_url(reverse('coupons:offer'))
        voucher_field_names = ('Code', 'Redemption URL')
        voucher_writer = csv.DictWriter(response, fieldnames=voucher_field_names)

        writer = csv.writer(response)
        writer.writerow(('Order Number:', order.number))
        writer.writerow([])

        order_line_vouchers = OrderLineVouchers.objects.filter(line__order=order)
        for order_line_voucher in order_line_vouchers:
            writer.writerow([order_line_voucher.line.product.title])
            voucher_writer.writeheader()

            for voucher in order_line_voucher.vouchers.all():
                voucher_writer.writerow({
                    voucher_field_names[0]: voucher.code,
                    voucher_field_names[1]: '{url}?code={code}'.format(url=redeem_url, code=voucher.code)
                })
            writer.writerow([])
        return response
