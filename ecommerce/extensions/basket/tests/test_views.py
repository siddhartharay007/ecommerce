import datetime

from django.core.urlresolvers import reverse
import httpretty
from oscar.core.loading import get_class, get_model
import pytz

from ecommerce.courses.tests.factories import CourseFactory
from ecommerce.extensions.test.factories import create_coupon
from ecommerce.tests.factories import StockRecordFactory
from ecommerce.tests.mixins import LmsApiMockMixin
from ecommerce.tests.testcases import TestCase

Basket = get_model('basket', 'Basket')
Benefit = get_model('offer', 'Benefit')
Catalog = get_model('catalogue', 'Catalog')
Selector = get_class('partner.strategy', 'Selector')
StockRecord = get_model('partner', 'StockRecord')

COUPON_CODE = 'COUPONTEST'


class BasketSingleItemViewTests(LmsApiMockMixin, TestCase):
    """ BasketSingleItemView view tests. """
    path = reverse('basket:single-item')

    def setUp(self):
        super(BasketSingleItemViewTests, self).setUp()
        self.user = self.create_user()
        self.client.login(username=self.user.username, password=self.password)

        course = CourseFactory()
        course.create_or_update_seat('verified', True, 50, self.partner)
        product = course.create_or_update_seat('verified', False, 0, self.partner)
        self.stock_record = StockRecordFactory(product=product, partner=self.partner)
        self.catalog = Catalog.objects.create(partner=self.partner)
        self.catalog.stock_records.add(self.stock_record)

    def test_login_required(self):
        """ The view should redirect to login page if the user is not logged in. """
        self.client.logout()
        response = self.client.get(self.path)
        testserver_login_url = self.get_full_url(reverse('login'))
        expected_url = '{path}?next={basket_path}'.format(path=testserver_login_url, basket_path=self.path)
        self.assertRedirects(response, expected_url, target_status_code=302)

    def test_missing_sku(self):
        """ The view should return HTTP 400 if no SKU is provided. """
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content, 'No SKU provided.')

    def test_missing_product(self):
        """ The view should return HTTP 400 if SKU has no associated product. """
        sku = 'NONEXISTING'
        expected_content = 'SKU [{}] does not exist.'.format(sku)
        url = '{path}?sku={sku}'.format(path=self.path, sku=sku)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content, expected_content)

    def test_unavailable_product(self):
        """ The view should return HTTP 400 if the product is not available for purchase. """
        product = self.stock_record.product
        product.expires = pytz.utc.localize(datetime.datetime.min)
        product.save()
        self.assertFalse(Selector().strategy().fetch_for_product(product).availability.is_available_to_buy)

        expected_content = 'Product [{}] not available to buy.'.format(product.title)
        url = '{path}?sku={sku}'.format(path=self.path, sku=self.stock_record.partner_sku)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content, expected_content)

    @httpretty.activate
    def test_redirect_to_basket_summary(self):
        """
        Verify the view redirects to the basket summary page, and that the user's basket is prepared for checkout.
        """
        create_coupon(catalog=self.catalog, code=COUPON_CODE, benefit_value=5)

        self.mock_footer_api_response()
        self.mock_course_api_response()
        url = '{path}?sku={sku}&code={code}'.format(path=self.path, sku=self.stock_record.partner_sku,
            code=COUPON_CODE)
        response = self.client.get(url)
        expected_url = self.get_full_url(reverse('basket:summary'))
        self.assertRedirects(response, expected_url, status_code=303)

        basket = Basket.objects.get(owner=self.user, site=self.site)
        self.assertEqual(basket.status, Basket.OPEN)
        self.assertEqual(basket.lines.count(), 1)
        self.assertTrue(basket.contains_a_voucher)
        self.assertEqual(basket.lines.first().product, self.stock_record.product)
