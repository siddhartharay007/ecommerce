define(['jquery',
        'backbone',
        'collections/course_collection',
        'text!templates/dynamic_catalog_buttons.html'
    ],
    function ($,
              Backbone,
              Courses,
              DynamicCatalogButtons) {
        'use strict';

        return Backbone.View.extend({
            template: _.template(DynamicCatalogButtons),

            events: {
                'click [name=preview_catalog]': 'previewCatalog',
                'click [name=catalog_help]': 'getHelpWithCatalog',
            },

            initialize: function (options) {
                this.creating_editing = options.creating_editing || false;
                this.query = options.query;
                this.seat_types = options.seat_types;

                this.courses = new Courses();

                this._super();
            },

            getRowData: function (course) {
                return {
                    id: course.get('id'),
                    name: course.get('name'),
                    type: course.get('type')
                };
            },

            previewCatalog: function (event) {
                // TODO:
                // Make an AJAX call to the API endpoint that will process dynamic catalog query
                event.preventDefault();
                this.courses.fetch();

                Backbone.ajax({
                    context: this,
                    type: 'GET',
                    url: window.location.origin + '/api/v2/catalogs/preview/',
                    data: {
                        query : this.query
                    },
                    success: function(data) {
                        var course_keys = _.pluck(data.results, 'key'),
                            course_data = this.filterCourses(course_keys, this.seat_types);

                        this.$el.find('#coursesTable').DataTable({
                            autoWidth: false,
                            destroy: true,
                            info: true,
                            paging: true,
                            ordering: false,
                            searching: false,
                            columns: [
                                {
                                    title: gettext('Course ID'),
                                    data: 'id'
                                },
                                {
                                    title: gettext('Course name'),
                                    data: 'name'
                                },
                                {
                                    title: gettext('Seat type'),
                                    data: 'type'
                                }
                            ],
                            data: course_data.map(this.getRowData, this)
                        });
                    },
                    error: function(){
                        alert('error');
                    }
                });
            },

            getHelpWithCatalog: function (event) {
                var url = 'https://stage-edx-discovery.edx.org/';
                event.preventDefault();

                window.open(url, '_blank');
            },

            filterCourses: function (course_keys, seat_types) {
                return _.filter(this.courses.models, function(course) {
                    return (_.contains(course_keys, course.get('id')) && _.contains(seat_types, course.get('type')));
                });
            },

            render: function () {
                this.$el.html(this.template({'creating_editing': this.creating_editing}));
                return this;
            }
        });
    });
