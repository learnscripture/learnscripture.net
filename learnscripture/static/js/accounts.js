
var learnscripture = (function(learnscripture, $) {
    var signedInAccountData = null;

    var hideSignupLinks = function() {
        $('.signup-link, .signin-link').each(function(idx, elem) {
            var a = $(elem);
            a.hide();
            if (a.parent().find(":visible").length == 0) {
                a.parent().hide();
            }
        });

    };

    var setSignedIn = function(accountData) {
        hideSignupLinks();
        signedInAccountData = accountData;
        $('.holds-username').text(accountData.username);
    };

    var handleFormValidationErrors = function(form, formPrefix, errorResponse) {
        var errors = $.parseJSON(errorResponse.responseText.split(/\n/)[1]);
        form.find(".validation-error").remove();
        form.find(".error").removeClass("error");
        $.each(errors, function(key, val) {
            $.each(val, function(idx, msg) {
                var formElem = $('#id_' + formPrefix + "-" + key);
                var p = formElem.parent();
                if (p.find("ul").length == 0) {
                    p.append("<ul class='validation-error'></ul>");
                }
                p.find("ul").append($('<li class="help-inline"></li>').text(msg));
                p.parent().addClass("error");
                });
            });

    };

    var signupError = function(jqXHR, textStatus, errorThrown) {
        if (jqXHR.status == 400) {
            handleFormValidationErrors($('#id-signup-form'), 'signup', jqXHR);
        } else {
            learnscripture.handlerAjaxError(jqXHR, textStatus, errorThrown);
        }
    };

    var signupBtnClick = function(ev) {
        $.ajax({url: '/api/learnscripture/v1/signup/',
                dataType: 'json',
                type: 'POST',
                data: $('#id-signup-form form').serialize(),
                error: signupError,
                success: function(data) {
                    setSignedIn(data);
                    $('#id-signup-form').modal('hide');
                }
                });
    };

    var showSignup = function(ev) {
        ev.preventDefault();
        $('#id-signup-form').modal({backdrop:true, keyboard:true, show:true});
    };

    var signinError = function(jqXHR, textStatus, errorThrown) {
        if (jqXHR.status == 400) {
            handleFormValidationErrors($('#id-signin-form'), 'signin', jqXHR);
        } else {
            learnscripture.handlerAjaxError(jqXHR, textStatus, errorThrown);
        }
    };

    var signinBtnClick = function(ev) {
        $.ajax({url: '/api/learnscripture/v1/signin/',
                dataType: 'json',
                type: 'POST',
                data: $('#id-signin-form form').serialize(),
                error: signinError,
                success: function(data) {
                    setSignedIn(data);
                    $('#id-signin-form').modal('hide');
                }
                });
    };

    var showSignin = function(ev) {
        ev.preventDefault();
        $('#id-signin-form').modal({backdrop:true, keyboard:true, show:true});
    };

    var setupAccountControls = function(ev) {
        $('.signup-link').click(showSignup);
        $('#id-create-account-btn').click(signupBtnClick);
        $('#id-create-account-cancel-btn').click(function(ev) {
            $('#id-signup-form').modal('hide');
        });

        $('.signin-link').click(showSignin);
        $('#id-sign-in-btn').click(signinBtnClick);
        $('#id-sign-in-canncel-btn').click(function(ev) {
            $('#id-signin-form').modal('hide');
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
