// Common functionality and requirements.
import htmx = require('htmx.org');


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
        prefix = formPrefix + "-"; // To match Django form prefices
    }
    form.find(".validation-error").remove();
    form.find(".error").removeClass("error");
    $.each(errors, function(key, val) {
        $.each(val, function(idx, msg) {
            var p;
            if (key === '__all__') {
                p = $('#id_' + prefix + 'form_all_errors');
            } else {
                var formElem = $('#id_' + prefix + <string>key);
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

// AJAX utilities, for use with `$.ajax`
//
// * if the user needs immediate feedback if the ajax failed,
//   and we don't expect it to fail normally,
//   use `error: ajaxFailed`
// * if there are some expected fail conditions due to user
//   error, write custom `error` that calls `ajaxFailed` after
//   handling known user error cases.
// * for non-essential things (e.g. GET requests for score logs)
//   just silently fail
export const ajaxFailed = function(jqXHR, textStatus, errorThrown) {
    alert($('#id-i18n-site-ajax-failed').text() + "\n " + jqXHR.responseText);
    console.log("AJAX error: %s, %s, %o", textStatus, errorThrown, jqXHR);
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


$(document).ready(function() {
    // Dropdown in topbar
    if ($('.base-page').length > 0) {
        var closeDropdowns = function() {
            $('.nav-dropdown').removeClass('menu-open');
        }
        $('html').bind('click', closeDropdowns)
        $('.dropdown-heading').bind('click', (ev) => {
            ev.stopPropagation();
            var $menu = $(ev.target).closest('.nav-dropdown');
            $menu.toggleClass("menu-open");
        });
        $('.dropdown-heading a').bind('click', (ev) => {
            ev.preventDefault();
        })
    }

    if (isTouchDevice()) {
        // A bit hacky but works:
        $('#id_desktop_testing_method').parent().parent().hide();
    } else {
        $('#id_touchscreen_testing_method').parent().parent().hide();
    }

    if (!deviceCanVibrate()) {
        $('#id_enable_vibration').closest('ul').parent().hide();
    }

    // HTMX
    document.querySelectorAll('form[hx-target][data-trigger-on-input-change]').forEach((form, idx) => {
        form.querySelectorAll('input, select').forEach((input, idx) => {
            input.addEventListener("change", (ev) => {
                htmx.trigger(form, 'submit', null);
            }, true);
        });
    });

    window.addEventListener('beforeunload', function(ev) {
        $('#id-unloader').addClass('shown');
    });
});
