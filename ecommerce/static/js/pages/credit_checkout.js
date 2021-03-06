define([
        'jquery',
        'backbone',
        'views/payment_button_view',
        'utils/utils',
        'utils/analytics_utils',
        'views/provider_selection_view',
        'pages/page'
    ],
    function ($,
              Backbone,
              PaymentButtonView,
              Utils,
              AnalyticsUtils,
              ProviderSelectionView,
              Page) {
        'use strict';

        return Page.extend({

            initialize: function () {
                var providerSelectionView = new ProviderSelectionView({el: '.provider-details'}),
                    paymentButtonView = new PaymentButtonView({el: '#payment-buttons'});

                this.listenTo(providerSelectionView, 'productSelected', function (data) {
                    paymentButtonView.setSku(data.sku);

                    // Update the display of the checkout total.
                    this.$el.find('.total-price span').text(data.price);
                });

                // Render the payment buttons first, since the rendering of the provider selection will
                // select the first available product.
                paymentButtonView.render();
                providerSelectionView.render();

                AnalyticsUtils.analyticsSetUp();
            }
        });
    }
);
