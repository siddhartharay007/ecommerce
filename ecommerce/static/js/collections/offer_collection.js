define([
        'backbone',
        'models/offer_model'
    ],
    function (Backbone,
              OfferModel) {
        'use strict';

        return Backbone.Collection.extend({
            model: OfferModel,
            url: '/api/v2/vouchers/offers/',
            parse: function (response) {
                return response.offers;
            }
        });
    }
);
