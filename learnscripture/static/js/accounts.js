
var learnscripture = (function(learnscripture, $) {
    var signedInAccountData = null;

    var hideSignUpLinks = function() {
        $('.signup-link, .login-link').each(function(idx, elem) {
            var a = $(elem);
            a.hide();
            if (a.parent().find(":visible").length == 0) {
                a.parent().hide();
            }
        });

    };

    var setSignedIn = function(accountData, identityChange) {
        hideSignUpLinks();
        signedInAccountData = accountData;
        $('.holds-username').text(accountData.username);
        $('.guest-only').hide();

        if (identityChange) {
            // Almost every page needs to be refreshed if we
            // have just logged in, because the identity will have
            // changed. So we redirect to the dashboard.
            window.location = '/dashboard/';
        }
    };

    var handleFormValidationErrors = function(form, formPrefix, errorResponse) {
        var errors = $.parseJSON(errorResponse.responseText.split(/\n/)[1]);
        form.find(".validation-error").remove();
        form.find(".error").removeClass("error");
        $.each(errors, function(key, val) {
            $.each(val, function(idx, msg) {
                if (key == '__all__') { return; }
                var formElem = $('#id_' + formPrefix + "-" + key);
                var p = formElem.parent();
                if (p.find("ul").length == 0) {
                    p.append("<ul class='validation-error'></ul>");
                }
                p.find("ul").append($('<li class="help-inline"></li>').text(msg));
                p.parent().addClass("error");
                });
            });
        return errors; // In cases other people want to use it

    };

    var signupError = function(jqXHR, textStatus, errorThrown) {
        if (jqXHR.status == 400) {
            handleFormValidationErrors($('#id-signup-form'), 'signup', jqXHR);
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
                    setSignedIn(data, false);
                    $('#id-signup-form').modal('hide');
                }
                });
    };

    var showSignUp = function(ev) {
        ev.preventDefault();
        $('#id-signup-form').modal({backdrop:'static', keyboard:true, show:true});
        $('#id_signup-email').focus();
    };

    var loginError = function(jqXHR, textStatus, errorThrown) {
        if (jqXHR.status == 400) {
            handleFormValidationErrors($('#id-login-form'), 'login', jqXHR);
        } else {
            learnscripture.handlerAjaxError(jqXHR, textStatus, errorThrown);
        }
    };

    var loginBtnClick = function(ev) {
        ev.preventDefault();
        $.ajax({url: '/api/learnscripture/v1/login/',
                dataType: 'json',
                type: 'POST',
                data: $('#id-login-form form').serialize(),
                error: loginError,
                success: function(data) {
                    setSignedIn(data, true);
                    $('#id-login-form').modal('hide');
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
                     setSignedIn(data, true);
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


        $("#id-login-form form input[type=\"text\"], " +
          "#id-login-form form input[type=\"password\"], " +
          "#id-signup-form form input[type=\"text\"], " +
          "#id-signup-form form input[type=\"password\"]").keypress(function (ev) {

              if ((ev.which && ev.which == 13) || (ev.keyCode && ev.keyCode == 13)) {
                  // Stop IE from submitting:
                  ev.preventDefault();

                  // Last input in list should cause submit
                  var input = $(ev.target);
                  var form = input.closest('form');
                  var lastInput = form.find('input[type="text"],input[type="password"]').last();
                  if (input.attr('id') == lastInput.attr('id')) {
                      form.closest('.modal').find('a.btn.default').first().click();
                  }
              }
          });
    };

    // Export:
    learnscripture.setupAccountControls = setupAccountControls;
    learnscripture.handleFormValidationErrors = handleFormValidationErrors;
    learnscripture.setSignedIn = setSignedIn;
    return learnscripture;
})(learnscripture || {}, $);

$(document).ready(function() {
                      learnscripture.setupAccountControls();
                  });
