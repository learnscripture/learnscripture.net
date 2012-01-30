
var learnscripture = (function(learnscripture, $) {
    var signedInAccountData = null;

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

    var wireSignup = function(ev) {
        $('.signup-link').click(showSignup);
        $('#id-create-account-btn').click(signupBtnClick);
        $('#id-create-account-cancel-btn').click(function(ev) {
            $('#id-signup-form').modal('hide');
        });
    };

    // Export:
    learnscripture.wireSignup = wireSignup;
    learnscripture.setSignedIn = setSignedIn;
    return learnscripture;
})(learnscripture || {}, $);

$(document).ready(function() {
                      learnscripture.wireSignup();
                  });
