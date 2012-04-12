
// Common functionality and requirements.
// See also some things at end e.g. modals.js

if (String.prototype.trim == undefined) {
    // Before ECMAscript 5 (e.g. Android 1.6, older IE versions)
    String.prototype.trim=function(){return this.replace(/^\s\s*/, '').replace(/\s\s*$/, '');};
}

// IE8 and earlier need this
if (Array.prototype.indexOf == undefined) {
    Array.prototype.indexOf = function(obj, start) {
        for (var i = (start || 0), j = this.length; i < j; i++) {
            if (this[i] === obj) { return i; }
        }
        return -1;
    };
}


// Django CSRF requirements
$(document).ajaxSend(function(event, xhr, settings) {
    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie != '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = jQuery.trim(cookies[i]);
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) == (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    function sameOrigin(url) {
        // url could be relative or scheme relative or absolute
        var host = document.location.host; // host + port
        var protocol = document.location.protocol;
        var sr_origin = '//' + host;
        var origin = protocol + sr_origin;
        // Allow absolute or scheme relative URLs to same origin
        return (url == origin || url.slice(0, origin.length + 1) == origin + '/') ||
            (url == sr_origin || url.slice(0, sr_origin.length + 1) == sr_origin + '/') ||
            // or any other URL that isn't scheme relative or absolute i.e relative.
            !(/^(\/\/|http:|https:).*/.test(url));
    }
    function safeMethod(method) {
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    }

    if (!safeMethod(settings.type) && sameOrigin(settings.url)) {
        xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
    }
});

var learnscripture = (function(learnscripture, $) {

    var handleFormValidationErrors = function(form, formPrefix, errorResponse) {
        var errors = $.parseJSON(errorResponse.responseText.split(/\n/)[1]);
        var prefix = '';
        if (formPrefix.length > 0) {
            prefix = formPrefix + "-"; // To matche Django form prefices
        }
        form.find(".validation-error").remove();
        form.find(".error").removeClass("error");
        $.each(errors, function(key, val) {
            $.each(val, function(idx, msg) {
                var p;
                if (key == '__all__') {
                    p = $('#id_' + prefix + 'form_all_errors')
                } else {
                    var formElem = $('#id_' + prefix + key);
                    p = formElem.parent();
                }
                if (p.find("ul.validation-error").length == 0) {
                    p.append("<ul class='validation-error'></ul>");
                }
                p.find("ul.validation-error").append($('<li class="help-inline"></li>').text(msg));
                p.parent().addClass("error");
                });
            });
        return errors; // In cases other people want to use it

    };

    // TODO - implement retrying and a queue and UI for manual retrying. Also
    // handle case of user being logged out.
    var handleAjaxError = function(jqXHR, textStatus, errorThrown) {
        console.log("AJAX error: %s, %s, %o", textStatus, errorThrown, jqXHR);
    };

    var ajaxRetryTick = function(info) {
        var text = "Data not saved. Retrying "
            + info.failures.toString() + " of "
            + (info.attempts - 1).toString() + // -1 because we are want to display '1 of 10' the first time we get an error.
            "...";
        $('#id-ajax-errors').html('<span>' + text + '</span>');
    };

    var ajaxRetryFailed = function(jqXHR, textStatus, errorThrown) {
        $('#id-ajax-errors').html('<span>Data not saved. Please check internet connection</span>');
    };

    var ajaxRetrySucceeded = function() {
        $('#id-ajax-errors').html('');
    };


    // Export:
    learnscripture.handleFormValidationErrors = handleFormValidationErrors;
    learnscripture.handleAjaxError = handleAjaxError;
    learnscripture.ajaxRetryOptions = {tick: ajaxRetryTick,
                                       attempts: 11
                                      };
    learnscripture.ajaxRetryFailed = ajaxRetryFailed;
    learnscripture.ajaxRetrySucceeded = ajaxRetrySucceeded;
    return learnscripture;

})(learnscripture || {}, $);


// Use [[ and ]] for templates to avoid clash with Django templates
$.views.delimiters('[[', ']]');

// Dropdown in topbar
$(document).ready(function() {
    $('.topbar').dropdown();
});
