/*jslint browser: true, vars: true, plusplus: true */
/*globals $, jQuery, alert, confirm */
var learnscripture =
    (function (learnscripture, $) {
        "use strict";
        var preferences = null;
        var PREFERENCES_ID = '#id-preferences-form';

        var afterPreferencesSave = null;

        var setPreferences = function (prefs) {
            prefs.testingMethod = learnscripture.isTouchDevice() ? prefs.touchscreenTestingMethod : prefs.desktopTestingMethod;
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
            $(PREFERENCES_ID).show();
            window.location.hash = PREFERENCES_ID;
            $(document).bind('keyup.sidepanel', function (e) {
                if (e.which == 27) {
                    closePreferences();
                }
            });
        }

        var closePreferences = function () {
            $(PREFERENCES_ID).hide();
            // We need to remove the afterPreferencesSave callback so
            // that it doesn't get invoked if they press cancel and then
            // open the form manually later.
            afterPreferencesSave = null;

            $(document).unbind('keyup.sidepanel');
            if (window.location.hash.replace("#", "") != "") {
                window.history.back();
            }
        }

        var savePrefsClick = function (ev) {
            ev.preventDefault();
            $.ajax({url: '/api/learnscripture/v1/setpreferences/?format=json',
                    dataType: 'json',
                    type: 'POST',
                    data: $('#id-preferences-form form').serialize(),
                    success: function (data) {
                        // translate from Python attributes
                        data.defaultBibleVersion = data.default_bible_version;
                        data.desktopTestingMethod = data.desktop_testing_method;
                        data.touchscreenTestingMethod = data.touchscreen_testing_method;
                        data.enableAnimations = data.enable_animations;
                        data.enableSounds = data.enable_sounds;
                        data.enableVibration = data.enable_vibration;
                        data.interfaceTheme = data.interface_theme;
                        data.preferencesSetup = data.preferences_setup;

                        setPreferences(data);

                        // Take a reference now, because after hiding the panel
                        // afterPreferencesSave is set to null
                        var afterSaveCallback = afterPreferencesSave;

                        closePreferences();

                        if (afterSaveCallback !== null) {
                            afterSaveCallback();
                        }

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
                showPreferences();
            }
        };

        var setupPreferencesControls = function () {
            $("#id-preferences-form .close-bar").on("click", function (ev) {
                ev.preventDefault();
                closePreferences();
            });

            $(".preferences-link,a[href='/preferences/']").on('click', function (ev) {
                ev.preventDefault();
                showPreferences();
            });

            $('#id-preferences-save-btn').on('click', savePrefsClick);
            $('#id-preferences-cancel-btn').on('click', function (ev) {
                ev.preventDefault();
                closePreferences();
            });

            // Sidepanel:
            // * shouldn't submit form when user presses Enter
            // * should click the 'primary' button if they press Enter on last input
            $("div.sidepanel form input[type=\"text\"], " +
              "div.sidepanel form input[type=\"password\"]").keypress(function (ev) {
                  if ((ev.which && ev.which === 13) || (ev.keyCode && ev.keyCode === 13)) {
                      // Stop IE from submitting:
                      ev.preventDefault();

                      // Last input in list should cause submit
                      var input = $(ev.target);
                      var form = input.closest('form');
                      var lastInput = form.find('input[type="text"],input[type="password"]').last();
                      if (input.attr('id') === lastInput.attr('id')) {
                          form.closest('.sidepanel').find('.btn.default').first().click();
                      }
                  }
              });

            $(window).bind('hashchange', function (ev) {
                var oldLocation = learnscripture.getLocation(ev.originalEvent.oldURL);
                var newLocation = learnscripture.getLocation(ev.originalEvent.newURL);

                if (newLocation.hash.replace("#", "") == "") {
                    var div = $(oldLocation.hash);
                    if (div.length > 0 && div.hasClass('sidepanel')) {
                        closePreferences();
                    }
                }
            });


            $('#id_interface_theme').change(function (ev) {
                var theme = $(this).val();
                $('body').attr('class', theme);
                // Also need to load the webfont CSS
                var themeFontPairs = learnscripture.themeFonts;
                for (var i = 0; i < themeFontPairs.length; i++) {
                    if (themeFontPairs[i][0] == theme) {
                        var fonts = themeFontPairs[i][1];
                        for (var j = 0; j < fonts.length; j++) {
                            $('head').append('<link href="' + fonts[j] + '" rel="stylesheet" type="text/css" />');
                        }
                    }
                }
            });

            setupNeedsPreferencesControls($('body'));
        };

        var setupNeedsPreferencesControls = function (section) {
            section.find('.needs-preferences').on('click', needsPreferencesButtonClick);
        };

        // Public interface:
        learnscripture.setupPreferencesControls = setupPreferencesControls;
        learnscripture.setupNeedsPreferencesControls = setupNeedsPreferencesControls;
        learnscripture.setPreferences = setPreferences;
        learnscripture.getPreferences = getPreferences;
        learnscripture.showPreferences = showPreferences;

        return learnscripture;
    }(learnscripture || {}, $));

$(document).ready(function () {
    learnscripture.setupPreferencesControls();
    learnscripture.setPreferences($('#id-preferences-data').data());
    if (window.androidlearnscripture && window.androidlearnscripture.setEnablePreferencesMenu) {
        window.androidlearnscripture.setEnablePreferencesMenu();
    }
});
