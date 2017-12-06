// Common functionality and requirements.
import 'jsrender';
import 'bootstrap-dropdown';


// Django CSRF requirements
$(document).ajaxSend(function(event, xhr, settings) {
    // due to CSRF_COOKIE_HTTPONLY, we get token from HTML, not cookie
    function getCsrfToken() {
        return $('[name=csrfmiddlewaretoken]').val();
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
        var token = getCsrfToken();
        xhr.responseJSON;
        if ((typeof token == "string") && token != "") {
            xhr.setRequestHeader("X-CSRFToken", token);
        }
    }
});

export const displaySimpleAjaxError = function(errorResponse) {
    var errors = errorResponse.responseJSON;
    var retval = '';
    for (var key in errors) {
        retval = retval + errors[key];
    }
    return retval;
}

export const handleFormValidationErrors = function(form, formPrefix, errorResponse) {
    var errors = errorResponse.responseJSON;
    var prefix = '';
    if (formPrefix.length > 0) {
        prefix = formPrefix + "-"; // To matche Django form prefices
    }
    form.find(".validation-error").remove();
    form.find(".error").removeClass("error");
    $.each(errors, function(key, val) {
        $.each(val, function(idx, msg) {
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
export const ajaxFailed = function(jqXHR, textStatus, errorThrown) {
    alert("The server could not be contacted. Please try again.");
    console.log("AJAX error: %s, %s, %o", textStatus, errorThrown, jqXHR);
};

var ajaxRetryTick = function(info) {
    var text = "Data not saved. Retrying "
        + info.failures.toString() + " of "
        + (info.attempts - 1).toString() + // -1 because we are want to display '1 of 10' the first time we get an error.
        "...";
    indicateLoading();
    $('#id-ajax-errors').html('<span>' + text + '</span>');
};

export const ajaxRetryOptions = {
    tick: ajaxRetryTick,
    attempts: 11
};

export const ajaxRetryFailed = function(jqXHR, textStatus, errorThrown) {
    $('#id-ajax-status').show();
    $('#id-ajax-loading').hide();
    $('#id-ajax-errors').html('<span>Data not saved. Please check internet connection</span>');
};

export const indicateLoading = function() {
    $('#id-ajax-status').show();
    $('#id-ajax-loading').show();
};

export const hideLoadingIndicator = function() {
    $('#id-ajax-status').hide();
    $('#id-ajax-loading').hide();
};

export const ajaxRetrySucceeded = function() {
    $('#id-ajax-errors').html('');
};

export const isTouchDevice = function() {
    return 'ontouchstart' in window;
};

export const isAndroid = function() {
    return navigator.userAgent.toLowerCase().indexOf("android") > -1;
};

var deviceCanVibrate = function() {
    return ("vibrate" in navigator);
}

export const getLocation = function(href) {
    var l = document.createElement("a");
    l.href = href;
    return l;
};


// Use [[ and ]] for templates to avoid clash with Django templates
$.views.settings.delimiters('[[', ']]');

$(document).ready(function() {
    // Dropdown in topbar
    $('.topbar').dropdown();

    if (isTouchDevice()) {
        // A bit hacky but works:
        $('#id_desktop_testing_method').parent().parent().hide();
    } else {
        $('#id_touchscreen_testing_method').parent().parent().hide();
    }

    if (!deviceCanVibrate()) {
        $('#id_enable_vibration').closest('ul').parent().hide();
    }

    // Scrolling of #id-ajax-status
    var TOPBAR_HEIGHT = 40;
    $(window).scroll(function(ev) {
        // We want ajax div to stay underneath the topbar.
        // topbar can be either fixed or absolute depending on screen size.
        var $tb = $('.topbar');
        var $aj = $('#id-ajax-status');
        var height;
        if ($tb.css('position') == 'fixed') {
            height = TOPBAR_HEIGHT;
        } else {
            // static
            height = Math.max(0, TOPBAR_HEIGHT - window.scrollY);
        }
        var heightString = height.toString() + "px";
        if ($aj.css('top') != heightString) {
            $aj.css('top', heightString);
        }
    });

    $(document).ajaxStop(function() {
        hideLoadingIndicator();
    });

});
