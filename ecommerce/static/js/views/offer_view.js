define([
        'jquery',
        'backbone',
        'underscore',
        'underscore.string',
        'moment',
        'text!templates/_offer_course_list.html'
    ],
    function ($,
              Backbone,
              _,
              _s,
              moment,
              OfferCourseListTemplate) {

        'use strict';

        return Backbone.View.extend({
            template: _.template(OfferCourseListTemplate),

            initialize: function (options) {
                this.code = options.code;
                this.listenTo(this.collection, 'update', this.refreshData);
            },

            refreshData: function () {
                this.hideVerifiedCertificate();
                this.isEnrollmentCode =
                    this.collection.models[0].get('benefit').type === 'Percentage' &&
                    Math.round(this.collection.models[0].get('benefit').value) === 100;

                _.each(this.collection.models, this.formatValues, this);

                this.render();
            },

            formatValues: function (course) {
                this.setNewPrice(course);
                this.formatBenefitValue(course);
                this.formatDate(course);
            },

            formatDate: function (course) {
                course.set({
                    course_start_date: moment(course.get('course_start_date')).format('MMM DD, YYYY'),
                    voucher_end_date: moment(course.get('voucher_end_date')).format('MMM DD, YYYY')
                });
            },

            setNewPrice: function (course) {
                var benefit = course.get('benefit'),
                    new_price,
                    price = parseInt(course.get('stockrecords').price_excl_tax);

                if (benefit.type === 'Percentage') {
                    new_price = price - (price * (benefit.value / 100));
                } else {
                    new_price = price - benefit.value;
                    if (new_price < 0) { new_price = 0; }
                }

                course.get('stockrecords').price_excl_tax = Math.round(price);
                course.set({ new_price: Math.round(new_price) });
            },

            formatBenefitValue: function (course) {
                var benefit = course.get('benefit'),
                    benefit_value = Math.round(benefit.value);
                if (benefit.type === 'Percentage') {
                    benefit_value = benefit_value + '%';
                } else {
                    benefit_value = benefit_value + '$';
                }

                course.set({benefit_value: benefit_value});
            },

            hideVerifiedCertificate: function () {
                var notVerified = this.collection.models.some(this.checkVerified);
                if (notVerified) { $('.verified-info').hide(); }
            },

            checkVerified: function (course) {
                return (course.get('seat_type') !== 'verified');
            },

            render: function () {
                this.$el.html(
                    this.template({
                        courses: this.collection.models,
                        code: this.code,
                        isEnrollmentCode: this.isEnrollmentCode
                    })
                );
                return this;
            }
        });
    }
);
