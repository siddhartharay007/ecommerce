define([
        'jquery',
        'backbone',
        'backbone.super',
        'backbone.validation',
        'underscore',
        'underscore.string',
        'views/alert_view',
        'utils/utils',
    ],
    function ($,
              Backbone,
              BackboneSuper,
              BackboneValidation,
              _,
              _s,
              AlertView,
              Utils) {
        'use strict';

        var FormView = Backbone.View.extend({
            tagName: 'form',

            events: {
                'submit': 'submit'
            },

            initialize: function () {
                this.alertViews = [];

                // Enable validation
                Utils.bindValidation(this);
            },

            remove: function () {
                Backbone.Validation.unbind(this);

                this.clearAlerts();
                return this._super();
            },

            render: function () {
                // Avoid the need to create this jQuery object every time an alert has to be rendered.
                this.$alerts = this.$el.find('.alerts');
                return this;
            },

            /**
             * Renders alerts that will appear at the top of the page.
             *
             * @param {String} level - Severity of the alert. This should be one of success, info, warning, or danger.
             * @param {Sring} message - Message to display to the user.
             */
            renderAlert: function (level, message) {
                var view = new AlertView({level: level, title: gettext('Error!'), message: message});

                view.render();
                this.$alerts.append(view.el);
                this.alertViews.push(view);

                $('body').animate({
                    scrollTop: this.$alerts.offset().top
                }, 500);

                this.$alerts.focus();

                return this;
            },

            validateCourseID : function(){
                var self = this;
                var courseIdInput = self.$('input[name=id]');
                courseIdInput.focusout(function() {
                    var courseId = courseIdInput.val();
                    self.checkCourseAlreadyExist(courseId);
                });
            },
            /**
             * Validate the courseId input if it already exists
             */
            checkCourseAlreadyExist : function(courseId){
                var courseIDFound = false, _this = this, url = '/api/v2/courses/' + courseId,
                    redirected_url = '/courses/' + courseId,
                    html = '<a href="'+redirected_url+'"> Click here to view the existing course</a>',
                    message = gettext('A course with the specified ID already exists.' + html);

                $.ajax({
                    url: url,
                    method: 'get',
                    contentType: 'application/json',
                    async: false,
                    success: function (data) {
                        if(data.id === courseId) {
                            _this.clearAlerts();
                            _this.renderAlert('danger', message);
                            courseIDFound = true;
                        }
                    },
                    error: function (response) {
                        if (response.status === 404) {
                            _this.clearAlerts();
                        }
                    }
                });
                return courseIDFound;

            },
            /**
             * Remove all alerts currently on display.
             */
            clearAlerts: function () {
                _.each(this.alertViews, function (view) {
                    view.remove();
                });

                this.alertViews = [];

                return this;
            },

            /**
             * Navigate to a new page within the App.
             *
             * @param {String} fragment
             */
            goTo: function (fragment) {
                Backbone.history.navigate(fragment, {trigger: true});
            },

            /**
             * Callback to run on save success.
             */
            saveSuccess: function (model) {
                this.goTo(model.id);
            },

            /**
             * Submits the form data to the server.
             *
             * If client-side validation fails, data will NOT be submitted. Server-side errors will result in an
             * alert being rendered. If submission succeeds, the user will be redirected to the course detail page.
             *
             * @param e
             */
            submit: function (e) {
                var $buttons,
                    $submitButton,
                    btnDefaultText,
                    self = this,
                    courseId = $('input[name=id]').val(),
                    btnSavingContent = '<i class="fa fa-spinner fa-spin" aria-hidden="true"></i> ' +
                        gettext('Saving...');

                e.preventDefault();

                // Validate the input and display a message, if necessary.
                if (!this.model.isValid(true)) {
                    this.clearAlerts();
                    this.renderAlert('danger', gettext('You must complete all required fields.'));
                    return;
                }
                // Check if the courseID already exists.
                else if(courseId && !self.editing && self.checkCourseAlreadyExist(courseId)){
                    return;
                }

                $buttons = this.$el.find('.form-actions .btn');
                $submitButton = $buttons.filter('button[type=submit]');

                // Store the default button text, and replace it with the saving state content.
                btnDefaultText = $submitButton.text();
                $submitButton.html(btnSavingContent);

                // Disable all buttons by setting the attribute (for <button>) and class (for <a>)
                $buttons.attr('disabled', 'disabled').addClass('disabled');

                this.model.save({
                    complete: function () {
                        // Restore the button text
                        $submitButton.text(btnDefaultText);

                        // Re-enable the buttons
                        $buttons.removeAttr('disabled').removeClass('disabled');
                    },
                    success: this.saveSuccess.bind(this),
                    error: function (model, response) {
                        var message = gettext('An error occurred while saving the data.');

                        if (response.responseJSON && response.responseJSON.error) {
                            message = response.responseJSON.error;

                            // Log the error to the console for debugging purposes
                            console.error(message);
                        } else {
                            // Log the error to the console for debugging purposes
                            console.error(response.responseText);
                        }

                        self.clearAlerts();
                        self.renderAlert('danger', message);
                        self.$el.animate({scrollTop: 0}, 'slow');
                    }
                });

                return this;
            }
        });

        /**
         * Override Backbone.View.extend so that the child view inherits events.
         */
        FormView.extend = function (child) {
            var view = Backbone.View.extend.apply(this, arguments);
            view.prototype.events = _.extend({}, this.prototype.events, child.events);
            return view;
        };

        return FormView;
    }
);
