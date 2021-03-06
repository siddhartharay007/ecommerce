define([], function(){
    'use strict';

    var enrollmentCodeVoucher = {
        'id': 1,
        'name': 'Test Enrollment Code',
        'code': 'XP54BC4M',
        'redeem_url': 'http://localhost:8002/coupons/offer/?code=XP54BC4M',
        'usage': 'Single use',
        'start_datetime': '2015-01-01T00:00:00Z',
        'end_datetime': '3500-01-01T00:00:00Z',
        'num_basket_additions': 0,
        'num_orders': 0,
        'total_discount': '0.00',
        'date_created': '2015-12-23',
        'offers': [
            1
        ],
        'is_available_to_user': [
            true,
            ''
        ],
        'benefit': [
            'Percentage',
            100.0
        ]
    },
    lastEditData = [
        'user',
        '2016-01-15T07:26:22.926Z'
    ],
    percentageDiscountCodeVoucher = {
        'id': 1,
        'name': 'Test Discount Code',
        'code': 'TST1234',
        'redeem_url': 'http://localhost:8002/coupons/offer/?code=TST1234',
        'usage': 'Single use',
        'start_datetime': '2015-01-01T00:00:00Z',
        'end_datetime': '3500-01-01T00:00:00Z',
        'num_basket_additions': 0,
        'num_orders': 0,
        'total_discount': '0.00',
        'date_created': '2015-12-23',
        'offers': [
            1
        ],
        'is_available_to_user': [
            true,
            ''
        ],
        'benefit': [
            'Percentage',
            50.0
        ]
    },
    valueDiscountCodeVoucher = {
        'id': 1,
        'name': 'Test Discount Code',
        'code': 'TST1234',
        'redeem_url': 'http://localhost:8002/coupons/offer/?code=TST1234',
        'usage': 'Once per customer',
        'start_datetime': '2015-01-01T00:00:00Z',
        'end_datetime': '3500-01-01T00:00:00Z',
        'num_basket_additions': 0,
        'num_orders': 0,
        'total_discount': '0.00',
        'date_created': '2015-12-23',
        'offers': [
            1
        ],
        'is_available_to_user': [
            true,
            ''
        ],
        'benefit': [
            'Absolute',
            12.0
        ]
    },
    verifiedSeat = {
        id: 9,
        url: 'http://ecommerce.local:8002/api/v2/products/9/',
        structure: 'child',
        product_class: 'Seat',
        title: 'Seat in edX Demonstration Course with verified certificate (and ID verification)',
        price: '15.00',
        expires: '2020-01-01T00:00:00Z',
        attribute_values: [
            {
                name: 'certificate_type',
                value: 'verified'
            },
            {
                name: 'course_key',
                value: 'course-v1:edX+DemoX+Demo_Course'
            },
            {
                name: 'id_verification_required',
                value: true
            }
        ],
        is_available_to_buy: true
    },
    courseData = {
        id: 'course-v1:edX+DemoX+Demo_Course',
        name: 'Demo Course',
        type: 'verified',
        products: [
            {
                id: 3,
                product_class: 'Seat',
                structure: 'child',
                expires: null,
                attribute_values: [
                    {
                        name: 'certificate_type',
                        value: 'verified'
                    }
                ],
                is_available_to_buy: true,
                stockrecords: [
                    {
                        id: 2,
                        product: 3,
                        partner: 1
                    }
                ]
            },
            {
                id: 2,
                product_class: 'Seat',
                structure: 'child',
                expires: null,
                attribute_values: [
                    {
                        name: 'certificate_type',
                        value: 'honor'
                    }
                ],
                stockrecords: [
                    {
                        id: 1,
                        product: 2,
                        partner: 1
                    }
                ]
            }
        ]
    },
    discountCodeCouponData = {
        'id': 11,
        'title': 'Test Discount Code',
        'coupon_type': 'Discount code',
        'last_edited': lastEditData,
        'seats': [verifiedSeat],
        'client': 'Client Name',
        'price': '100.00',
        'categories': [
            {
                'id': 4,
                'name': 'TESTCAT'
            }
        ],
        'vouchers': [percentageDiscountCodeVoucher]
    },
    discountCodeCouponModelData = {
        title: 'Test Discount',
        coupon_type: 'Discount code',
        client: 'test_client',
        start_date: '2015-01-01T00:00:00Z',
        end_date: '2016-01-01T00:00:00Z',
        stock_record_ids: [1],
        code: 'TESTCODE',
        voucher_type: 'Single use',
        benefit_type: 'Percentage',
        benefit_value: 25,
        course_id: 'a/b/c',
        seat_type: 'verified',
        course: verifiedSeat,
        price: 100,
        category: 4
    },
    enrollmentCodeCouponData = {
        'id': 10,
        'title': 'Test Enrollment Code',
        'code_type': 'Enrollment code',
        'last_edited': lastEditData,
        'seats': [verifiedSeat],
        'client': 'Client Name',
        'categories': [
            {
                'id': 4,
                'name': 'TESTCAT'
            }
        ],
        'price': '100.00',
        'vouchers': [enrollmentCodeVoucher]
    },
    enrollmentCodeCouponModelData = {
        title: 'Test Enrollment',
        coupon_type: 'Enrollment code',
        client: 'test_client',
        start_date: '2015-01-01T00:00:00Z',
        end_date: '2016-01-01T00:00:00Z',
        stock_record_ids: [1],
        voucher_type: 'Single use',
        price: 100,
        course_id: 'a/b/c',
        seat_type: 'verified',
        course: verifiedSeat
    },
    couponAPIResponseData = {
        count: 1,
        next: null,
        previous: null,
        results: [
            {
                id: 4,
                url: 'http://localhost:8002/api/v2/coupons/4/',
                structure: 'standalone',
                product_class: 'Coupon',
                title: 'Coupon',
                price: '100.00',
                expires: null,
                attribute_values: [
                    {
                        name: 'Coupon vouchers',
                        value: [enrollmentCodeCouponData]
                    }
                ],
                is_available_to_buy: true,
                stockrecords: []
            }
        ]
    };

    return {
        'couponAPIResponseData': couponAPIResponseData,
        'courseData': courseData,
        'discountCodeCouponData': discountCodeCouponData,
        'discountCodeCouponModelData': discountCodeCouponModelData,
        'enrollmentCodeCouponData': enrollmentCodeCouponData,
        'enrollmentCodeCouponModelData': enrollmentCodeCouponModelData,
        'enrollmentCodeVoucher': enrollmentCodeVoucher,
        'lastEditData': lastEditData,
        'percentageDiscountCodeVoucher': percentageDiscountCodeVoucher,
        'valueDiscountCodeVoucher': valueDiscountCodeVoucher,
        'verifiedSeat': verifiedSeat
    };
});
