define([
        'jquery',
        'underscore',
        'models/offer_model',
        'views/offer_view',
        'collections/offer_collection'
    ],
    function ($,
              _,
              OfferModel,
              OfferView,
              OfferCollection) {
        'use strict';

        describe('offer view', function () {
            var view,
                collection,
                code,
                course = new OfferModel({
                    benefit: {
                        type: 'Percentage',
                        value: 100
                    },
                    stockrecords: {
                        id: 2,
                        product: 3,
                        partner: 1,
                        partner_sku: '8CF08E5',
                        price_currency: 'USD',
                        price_excl_tax: '100.00'
                    },
                    image_url: 'img/src/url',
                    seat_type: 'Not verified',
                    organization: 'edX',
                    title: 'edX Demonstration Course',
                    course_start_date: '2013-02-05T05:00:00Z',
                    id: 'course-v1:edX+DemoX+Demo_Course',
                    voucher_end_date: '2016-07-29T00:00:00Z'
                }),
                course2 = new OfferModel({
                    benefit: {
                        type: 'Not percentage',
                        value: 20
                    },
                    stockrecords: {
                        id: 2,
                        product: 3,
                        partner: 1,
                        partner_sku: '8CF08E5',
                        price_currency: 'USD',
                        price_excl_tax: '100.00'
                    },
                    image_url: 'img/src/url2',
                    seat_type: 'verified',
                    organization: 'edX',
                    title: 'edX Demonstration Course',
                    course_start_date: '2013-02-05T05:00:00Z',
                    id: 'course-v1:edX+DemoX+Demo_Courseewewe',
                    voucher_end_date: '2016-07-29T00:00:00Z'
                });

            beforeEach(function () {
                collection = new OfferCollection();
                code = 'ABCDE';
                collection.add([ course, course2 ]);
                view = new OfferView({code: code, collection: collection}).render();
            });

            it('should hide the verified certificate info', function () {
                expect(view.$el.find('.verified-info:hidden')).toBeTruthy();
            });

            it('should call functions when formatValues called with course', function () {
                spyOn(view, 'setNewPrice');
                spyOn(view, 'formatBenefitValue');
                spyOn(view, 'formatDate');
                view.formatValues(course);
                expect(view.setNewPrice).toHaveBeenCalledWith(course);
                expect(view.formatBenefitValue).toHaveBeenCalledWith(course);
                expect(view.formatDate).toHaveBeenCalledWith(course);
            });

            it('should call functions when refreshData called', function () {
                spyOn(view, 'hideVerifiedCertificate');
                spyOn(_, 'each');
                spyOn(view, 'render');
                view.refreshData();
                expect(view.hideVerifiedCertificate).toHaveBeenCalled();
                expect(_.each).toHaveBeenCalledWith(view.collection.models, view.formatValues, view);
                expect(view.render).toHaveBeenCalled();
            });

            it('should format dates when formatDate called', function () {
                view.formatDate(view.collection.models[0]);
                expect(view.collection.models[0].get('course_start_date')).toBe('Feb 05, 2013');
                expect(view.collection.models[0].get('voucher_end_date')).toBe('Jul 29, 2016');
            });

            it('should format dates when formatDate called', function () {
                view.formatDate(view.collection.models[0]);
                expect(view.collection.models[0].get('course_start_date')).toBe('Feb 05, 2013');
                expect(view.collection.models[0].get('voucher_end_date')).toBe('Jul 29, 2016');
            });

            it('should set new price when setNewPrice called', function () {
                view.setNewPrice(view.collection.models[0]);
                expect(view.collection.models[0].get('new_price')).toBe(0);
                view.setNewPrice(view.collection.models[1]);
                expect(view.collection.models[1].get('new_price')).toBe(80);
            });

            it('should set benefit value when formatBenefitValue called', function () {
                view.formatBenefitValue(view.collection.models[0]);
                expect(view.collection.models[0].get('benefit_value')).toBe('100%');
                view.formatBenefitValue(view.collection.models[1]);
                expect(view.collection.models[1].get('benefit_value')).toBe('20$');
            });

            it('should return is seat type verified when checkVerified called', function () {
                expect(view.checkVerified(view.collection.models[0])).toBeTruthy();
                expect(view.checkVerified(view.collection.models[1])).toBeFalsy();
            });

            it('should set isEnrollmentCode when refreshData called', function () {
                view.refreshData();
                expect(view.isEnrollmentCode).toBeTruthy();
            });

        });
    }
);