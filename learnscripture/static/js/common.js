/*jslint browser: true, vars: true, plusplus: true */
/*globals $, jQuery, alert */
// Common functionality and requirements.
// See also some things at end e.g. modals.js

if (String.prototype.trim === undefined) {
    // Before ECMAscript 5 (e.g. Android 1.6, older IE versions)
    String.prototype.trim = function () { return this.replace(/^\s\s*/, '').replace(/\s\s*$/, ''); };
}

// IE8 and earlier need this
if (Array.prototype.indexOf === undefined) {
    Array.prototype.indexOf = function (obj, start) {
        var i, j;
        for (i = (start || 0), j = this.length; i < j; i++) {
            if (this[i] === obj) { return i; }
        }
        return -1;
    };
}


// Django CSRF requirements
$(document).ajaxSend(function (event, xhr, settings) {
    function getCookie(name) {
        var cookieValue = null, i;
        if (document.cookie && document.cookie != '') {
            var cookies = document.cookie.split(';');
            for (i = 0; i < cookies.length; i++) {
                var cookie = jQuery.trim(cookies[i]);
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
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
        return (url === origin || url.slice(0, origin.length + 1) === origin + '/') ||
            (url === sr_origin || url.slice(0, sr_origin.length + 1) === sr_origin + '/') ||
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

var learnscripture = (function (learnscripture, $) {
    "use strict";
    var handleFormValidationErrors = function (form, formPrefix, errorResponse) {
        var errors = $.parseJSON(errorResponse.responseText.split(/\n/)[1]);
        var prefix = '';
        if (formPrefix.length > 0) {
            prefix = formPrefix + "-"; // To matche Django form prefices
        }
        form.find(".validation-error").remove();
        form.find(".error").removeClass("error");
        $.each(errors, function (key, val) {
            $.each(val, function (idx, msg) {
                var p;
                if (key === '__all__') {
                    p = $('#id_' + prefix + 'form_all_errors');
                } else {
                    var formElem = $('#id_' + prefix + key);
                    p = formElem.parent();
                }
                if (p.find("ul.validation-error").length === 0) {
                    p.append("<ul class='validation-error'></ul>");
                }
                p.find("ul.validation-error").append($('<li class="help-inline"></li>').text(msg));
                p.parent().addClass("error");
            });
        });

        // form validation may have changed size of modal
        var modal = form.closest('div.modal');
        if (modal.length > 0) {
            learnscripture.adjustModal(modal);
        }

        return errors; // In cases other people want to use it

    };

    // * if the user needs immediate feedback if the ajax failed,
    //   use ajaxFailed
    // * for non-essential things (e.g. GET requests for score logs)
    //   just silently fail
    // * for essential things (e.g. POST requests that save test scores to server)
    //   use:
    //       retry: ajaxRetryOptions,
    //       error: ajaxRetryFailed,
    //       success: ajaxRetrySucceeded
    //       (or call ajaxRetrySucceeded at beginning of success callback)
    var ajaxFailed = function (jqXHR, textStatus, errorThrown) {
        alert("The server could not be contacted. Please try again.");
        console.log("AJAX error: %s, %s, %o", textStatus, errorThrown, jqXHR);
    };

    var ajaxRetryTick = function (info) {
        var text = "Data not saved. Retrying "
            + info.failures.toString() + " of "
            + (info.attempts - 1).toString() + // -1 because we are want to display '1 of 10' the first time we get an error.
            "...";
        $('#id-ajax-errors').html('<span>' + text + '</span>');
    };

    var ajaxRetryFailed = function (jqXHR, textStatus, errorThrown) {
        $('#id-ajax-errors').html('<span>Data not saved. Please check internet connection</span>');
    };

    var ajaxRetrySucceeded = function () {
        $('#id-ajax-errors').html('');
    };


    // Export:
    learnscripture.handleFormValidationErrors = handleFormValidationErrors;
    learnscripture.ajaxFailed = ajaxFailed;
    learnscripture.ajaxRetryOptions = {tick: ajaxRetryTick,
                                       attempts: 11
                                      };
    learnscripture.ajaxRetryFailed = ajaxRetryFailed;
    learnscripture.ajaxRetrySucceeded = ajaxRetrySucceeded;
    return learnscripture;

}(learnscripture || {}, $));


// Use [[ and ]] for templates to avoid clash with Django templates
$.views.delimiters('[[', ']]');

$(document).ready(function () {
    // Dropdown in topbar
    $('.topbar').dropdown();
});
