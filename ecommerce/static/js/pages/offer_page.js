define([
        'routers/offer_router',
        'views/offer_view',
        'pages/page',
        'collections/offer_collection',
        'models/offer_model'
    ],
    function (OfferRouter,
              OfferView,
              Page,
              OfferCollection) {
        'use strict';

        return Page.extend({
            title: gettext('Redeem'),

            initialize: function (options) {
                this.collection = new OfferCollection();
                this.collection.fetch({
                    data: {code: options.code},
                    processData: true
                });
                this.view = new OfferView({code: options.code, collection: this.collection});
                this.render();
            }
        });
    }
);
