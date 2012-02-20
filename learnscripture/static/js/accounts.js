
var learnscripture = (function(learnscripture, $) {
    var signedInAccountData = null;

    var hideSignUpLinks = function() {
        $('.dropdown-menu .signup-link, .dropdown-menu .login-link').each(function(idx, elem) {
            var a = $(elem);
            a.hide();
            if (a.parent().find(":visible").length == 0) {
                a.parent().hide();
            }
        });

    };

    var setSignedIn = function(accountData, signinType) {
        hideSignUpLinks();
        signedInAccountData = accountData;
        $('.holds-username').text(accountData.username);
        $('.guest-only').hide();

        if (signinType == 'logout') {
            // Need to refresh page
            window.location.reload();
        } else if (signinType == 'signup') {
            // If they are in the middle of reading/testing,
            // we don't want to force them back to the beginning.
            // However, on some pages we do want to force a refresh.
            if ($(".reload-after-signup").length > 0) {
                window.location.reload();
            }
        }
    };

    var signupError = function(jqXHR, textStatus, errorThrown) {
        if (jqXHR.status == 400) {
            learnscripture.handleFormValidationErrors($('#id-signup-form'), 'signup', jqXHR);
        } else {
            learnscripture.handlerAjaxError(jqXHR, textStatus, errorThrown);
        }
    };

    var signupBtnClick = function(ev) {
        ev.preventDefault();
        $.ajax({url: '/api/learnscripture/v1/signup/',
                dataType: 'json',
                type: 'POST',
                data: $('#id-signup-form form').serialize(),
                error: signupError,
                success: function(data) {
                    setSignedIn(data, 'signup');
                    $('#id-signup-form').modal('hide');
                }
                });
    };

    var showSignUp = function(ev) {
        ev.preventDefault();
        $('#id-signup-form').modal({backdrop:'static', keyboard:true, show:true});
        $('#id_signup-email').focus();
    };

    var loginBtnClick = function(ev) {
        // Chrome will only remember passwords if the login form is submitted in
        // the normal way.  Therefore we do synchronous XHR to check login
        // details (and actually log them in), then allow form submission to
        // continue if it is correct.
        $.ajax({url: '/api/learnscripture/v1/login/',
                dataType: 'json',
                async: false,
                type: 'POST',
                data: $('#id-login-form form').serialize(),
                error: function(jqXHR, textStatus, errorThrown) {
                    ev.preventDefault();
                    if (jqXHR.status == 400) {
                        learnscripture.handleFormValidationErrors($('#id-login-form'), 'login', jqXHR);
                    } else {
                        learnscripture.handlerAjaxError(jqXHR, textStatus, errorThrown);
                    }
                },
                success: function(data) {
                    // No ev.preventDefault, form will submit
                }
                });
    };

    var showLogIn = function(ev) {
        ev.preventDefault();
        $('#id-login-form').modal({backdrop:'static', keyboard:true, show:true});
        $('#id_login-email').focus();
    };


    var logoutBtnClick = function(ev) {
        $.ajax({url: '/api/learnscripture/v1/logout/',
                 dataType: 'json',
                 type: 'POST',
                 success: function(data) {
                     setSignedIn(data, 'logout');
                     $('#id-logout-form').modal('hide');
                 }
               });
        ev.preventDefault();
    };

    var showLogOut = function(ev) {
        ev.preventDefault();
        $('#id-logout-form').modal({backdrop:'static', keyboard:true, show:true});
    }

    var setupAccountControls = function(ev) {
        $('.signup-link').click(showSignUp);
        $('#id-create-account-btn').click(signupBtnClick);
        $('#id-create-account-cancel-btn').click(function(ev) {
            ev.preventDefault();
            $('#id-signup-form').modal('hide');
        });

        $('.login-link').click(showLogIn);
        $('#id-sign-in-btn').click(loginBtnClick);
        $('#id-sign-in-cancel-btn').click(function(ev) {
            ev.preventDefault();
            $('#id-login-form').modal('hide');
        });

        $('.logout-link').click(showLogOut);
        $('#id-logout-btn').click(logoutBtnClick);
        $('#id-logout-cancel-btn').click(function(ev) {
            ev.preventDefault();
            $('#id-logout-form').modal('hide');
        });
    };

    // Export:
    learnscripture.setupAccountControls = setupAccountControls;
    learnscripture.setSignedIn = setSignedIn;
    return learnscripture;
})(learnscripture || {}, $);

$(document).ready(function() {
                      learnscripture.setupAccountControls();
                  });
