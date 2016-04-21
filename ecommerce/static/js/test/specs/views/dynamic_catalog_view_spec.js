define([
        'jquery',
        'underscore',
        'views/dynamic_catalog_view'
    ],
    function ($,
              _,
              DynamicCatalogView) {
        'use strict';

        describe('dynamic catalog view', function () {
            var view;

            beforeEach(function () {
                view = new DynamicCatalogView({creating_editing: true});
                view.render();
            });

            it('should call preview catalog if preview button was clicked', function () {
                spyOn(view, 'previewCatalog');
                view.delegateEvents();
                view.$el.find('[name=preview_catalog]').trigger('click');
                expect(view.previewCatalog).toHaveBeenCalled();
            });

            it('should call get help with catalog if help button was clicked', function () {
                spyOn(view, 'getHelpWithCatalog');
                view.delegateEvents();
                view.$el.find('[name=catalog_help]').trigger('click');
                expect(view.getHelpWithCatalog).toHaveBeenCalled();
            });
        });
    }
);
