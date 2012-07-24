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
                    data.scoringEnabled = data.scoring_enabled;
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


    var loginEndpoint = '/login/';

    var setLoginEndpoint = function (url) {
        loginEndpoint = url;
    }

    var getLoginEndpoint = function (url) {
        return loginEndpoint;
    }

    var setLoginRedirectToSelf = function () {
        setLoginEndpoint('/login/?next=' + encodeURIComponent(window.location.pathname + window.location.search));
    }

    var loginBtnClick = function (ev) {
        ev.preventDefault();
        // Chrome will only remember passwords if the login form is submitted in
        // the normal way.  Therefore we do synchronous XHR to check login
        // details (and actually log them in), then do form submission to
        // continue if it is correct.
        // This form is 'shared' between login and forgot password, so ensure
        // form action is correct.
        if ($(".reload-after-login").length > 0) {
            setLoginRedirectToSelf();
        }

        $('#id-login-form form').attr('action', getLoginEndpoint());

        $.ajax({url: '/api/learnscripture/v1/login/?format=json',
                dataType: 'json',
                async: false,
                type: 'POST',
                data: $('#id-login-form form').serialize(),
                error: function (jqXHR, textStatus, errorThrown) {
                    ev.preventDefault();
                    if (jqXHR.status === 400) {
                        learnscripture.handleFormValidationErrors($('#id-login-form'), 'login', jqXHR);
                    } else {
                        learnscripture.ajaxFailed(jqXHR, textStatus, errorThrown);
                    }
                },
                success: function (data) {
                    $('#id-login-form form').get(0).submit();
                }
                });
    };

    var forgotPasswordClick = function (ev) {
        ev.preventDefault();
        // This form is 'shared' between login and forgot password, so ensure
        // form action is correct.
        $('#id-login-form form').attr('action', '/password-reset/');

        $.ajax({url: '/api/learnscripture/v1/resetpassword/?format=json',
                dataType: 'json',
                async: false,
                type: 'POST',
                data: $('#id-login-form form').serialize(),
                error: function (jqXHR, textStatus, errorThrown) {
                    ev.preventDefault();
                    if (jqXHR.status === 400) {
                        learnscripture.handleFormValidationErrors($('#id-login-form'), 'login', jqXHR);
                    } else {
                        learnscripture.ajaxFailed(jqXHR, textStatus, errorThrown);
                    }
                },
                success: function (data) {
                    $('#id-login-form form').get(0).submit();
                }
                });
    };

    var showLogIn = function (ev) {
        if (ev !== undefined) {
            ev.preventDefault();
        }
        $('#id-login-form').modal({backdrop: 'static', keyboard: true, show: true});
        $('#id_login-email').focus();
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

        $('.login-link').click(showLogIn);
        $('#id-sign-in-btn').click(loginBtnClick);
        $('#id-sign-in-cancel-btn').click(function (ev) {
            ev.preventDefault();
            $('#id-login-form').modal('hide');
        });

        $('#id-forgot-password-btn').click(forgotPasswordClick);

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
    learnscripture.showLogIn = showLogIn;
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
