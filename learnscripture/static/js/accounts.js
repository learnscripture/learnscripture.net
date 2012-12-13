/*jslint browser: true, vars: true */
/*globals $ */
var learnscripture = (function (learnscripture, $) {
    "use strict";
    var signedInAccountData = null;

    var afterCreateAccount = null;

    var hideSignUpLinks = function () {
        $('.dropdown-menu .signup-link, .dropdown-menu .login-link').each(function (idx, elem) {
            var a = $(elem);
            a.hide();
            if (a.parent().find(":visible").length === 0) {
                a.parent().hide();
            }
        });

    };

    var setAccountData = function (accountData) {
        signedInAccountData = accountData;

        $('#id-account-data').trigger('accountDataSet', accountData);
    };

    var getAccountData = function () {
        return signedInAccountData;
    };

    var setSignedIn = function (accountData, signinType) {
        hideSignUpLinks();
        setAccountData(accountData);
        $('.holds-username').text(accountData.username);
        $('.guest-only').hide();

        if (signinType === 'logout') {
            // Need to refresh page, unless page indicates differently
            if ($('#url-after-logout').length > 0) {
                window.location = $('#url-after-logout').text();
            } else {
                window.location.reload();
            }
        } else if (signinType === 'signup') {
            // If they are in the middle of reading/testing,
            // we don't want to force them back to the beginning.
            // However, on some pages we do want to force a refresh.
            if ($(".reload-after-signup").length > 0) {
                window.location.reload();
            }
        }
    };

    var signupError = function (jqXHR, textStatus, errorThrown) {
        if (jqXHR.status === 400) {
            learnscripture.handleFormValidationErrors($('#id-signup-form'), 'signup', jqXHR);
        } else {
            learnscripture.ajaxFailed(jqXHR, textStatus, errorThrown);
        }
    };

    var signupBtnClick = function (ev) {
        ev.preventDefault();
        $.ajax({url: '/api/learnscripture/v1/signup/?format=json',
                dataType: 'json',
                type: 'POST',
                data: $('#id-signup-form form').serialize(),
                error: signupError,
                success: function (data) {
                    // Translate from Python attributes where needed
                    setSignedIn(data, 'signup');
                    if (afterCreateAccount !== null) {
                        afterCreateAccount();
                    }
                    $('#id-signup-form').modal('hide');
                }
                });
    };

    var showSignUp = function () {
        $('#id-signup-form').modal({backdrop: 'static', keyboard: true, show: true});
        $('#id_signup-email').focus();
    };

    var logoutBtnClick = function (ev) {
        $.ajax({url: '/api/learnscripture/v1/logout/?format=json',
                dataType: 'json',
                type: 'POST',
                success: function (data) {
                    setSignedIn(data, 'logout');
                    $('#id-logout-form').modal('hide');
                },
                error: learnscripture.ajaxFailed
               });
        ev.preventDefault();
    };

    var showLogOut = function (ev) {
        ev.preventDefault();
        $('#id-logout-form').modal({backdrop: 'static', keyboard: true, show: true});
    };

    var needsAccountButtonClick = function (ev) {
        var account = getAccountData();
        if (account === null || account.username === "") {
            // first get user to create an account
            ev.preventDefault();

            // Setup function to run after creating account
            afterCreateAccount = function() {
                $(ev.target).click();
            }

            $('#id-signup-function').bind('hidden', function (ev) {
                afterCreateAccount = null;
            });

            showSignUp();
        }
    };

    var setupAccountControls = function (ev) {
        $('.signup-link').click(function (ev) {
            ev.preventDefault();
            showSignUp();
        });
        $('#id-create-account-btn').click(signupBtnClick);
        $('#id-create-account-cancel-btn').click(function (ev) {
            ev.preventDefault();
            $('#id-signup-form').modal('hide');
        });

        $('.logout-link').click(showLogOut);
        $('#id-logout-btn').click(logoutBtnClick);
        $('#id-logout-cancel-btn').click(function (ev) {
            ev.preventDefault();
            $('#id-logout-form').modal('hide');
        });

        // Attach this class to buttons that require an account, but might be
        // presented when the user isn't logged in. This functionality is used
        // to streamline some entry points where it makes sense to invite people
        // to create accounts.
        $('.needs-account').click(needsAccountButtonClick);

    };

    // Export:
    learnscripture.setupAccountControls = setupAccountControls;
    learnscripture.setAccountData = setAccountData;
    learnscripture.getAccountData = getAccountData;
    return learnscripture;
}(learnscripture || {}, $));

$(document).ready(function () {
    learnscripture.setupAccountControls();
    if ($('#id-account-data').length > 0) {
        learnscripture.setAccountData($('#id-account-data').data());
    } else {
        learnscripture.setAccountData(null);
    }
});
