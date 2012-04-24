/*jslint browser: true, vars: true, plusplus: true */
/*globals $, jQuery, alert, confirm */
var learnscripture =
    (function (learnscripture, $) {
        "use strict";
        var preferences = null;

        var setPreferences = function (prefs) {
            preferences = prefs;
            // Notify listeners. Could pick any DOM element to trigger off as
            // long as listeners do the same. It makes sense to use
            // #id-preferences-data.
            $('#id-preferences-data').trigger('preferencesSet', preferences);
        };

        var getPreferences = function () {
            return preferences;
        };

        var showPreferences = function (ev) {
            $('#id-preferences-form').modal({backdrop: 'static', keyboard: true, show: true});
        };

        var afterPreferencesSave = null;

        var savePrefsClick = function (ev) {
            ev.preventDefault();
            $.ajax({url: '/api/learnscripture/v1/setpreferences/',
                    dataType: 'json',
                    type: 'POST',
                    data: $('#id-preferences-form form').serialize(),
                    success: function (data) {
                        // translate from Python attributes
                        data.defaultBibleVersion = data.default_bible_version;
                        data.testingMethod = data.testing_method;
                        data.enableAnimations = data.enable_animations;
                        data.interfaceTheme = data.interface_theme;
                        data.preferencesSetup = data.preferences_setup;

                        setPreferences(data);

                        if (afterPreferencesSave !== null) {
                            afterPreferencesSave();
                        }
                        // This must come after, because the afterPreferencesSave callback
                        // will be removed after the modal is hidden.
                        $('#id-preferences-form').modal('hide');
                    },
                    error: function(jqXHR, textStatus, errorThrown) {
                        if (jqXHR.status === 400) {
                            learnscripture.handleFormValidationErrors($('#id-preferences-form'), '', jqXHR);
                        } else {
                            learnscripture.ajaxFailed(jqXHR, textStatus, errorThrown);
                        }
                    }
                   });
        };

        var needsPreferencesButtonClick = function (ev) {
            var prefs = getPreferences();
            if (prefs === null || !prefs.preferencesSetup) {
                // Need to intercept, and first get user to set preferences.
                ev.preventDefault();

                // If they save their preferences correctly, then do the
                // click again. It will succeed this time
                afterPreferencesSave = function () {
                    $(ev.target).click();
                };

                // We need to remove the afterPreferencesSave callback so
                // that it doesn't get invoked if they press cancel and then
                // open the form manually later.
                $('#id-preferences-form').bind('hidden', function (ev) {
                    afterPreferencesSave = null;
                });

                showPreferences();
            }
        };

        var setupPreferencesControls = function () {
            $(".preferences-link,a[href='/preferences/']").click(function (ev) {
                ev.preventDefault();
                showPreferences();
            });

            $('#id-preferences-save-btn').click(savePrefsClick);
            $('#id-preferences-cancel-btn').click(function (ev) {
                ev.preventDefault();
                $('#id-preferences-form').modal('hide');
            });

            $('#id_interface_theme').change(function (ev) {
                $('body').attr('class', $(this).val());
            });

            setupNeedsPreferencesControls($('body'));
        };

        var setupNeedsPreferencesControls = function (section) {
            section.find('.needs-preferences').click(needsPreferencesButtonClick);
        };

        // Public interface:
        learnscripture.setupPreferencesControls = setupPreferencesControls;
        learnscripture.setupNeedsPreferencesControls = setupNeedsPreferencesControls;
        learnscripture.setPreferences = setPreferences;
        learnscripture.getPreferences = getPreferences;

        return learnscripture;
    }(learnscripture || {}, $));

$(document).ready(function () {
    learnscripture.setupPreferencesControls();
    learnscripture.setPreferences($('#id-preferences-data').data());
});
