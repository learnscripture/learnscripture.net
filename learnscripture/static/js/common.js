/*jslint browser: true, vars: true, plusplus: true */
/*globals $, jQuery, alert */
// Common functionality and requirements.

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

// From https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Object/keys
if (!Object.keys) {
  Object.keys = (function() {
    'use strict';
    var hasOwnProperty = Object.prototype.hasOwnProperty,
        hasDontEnumBug = !({ toString: null }).propertyIsEnumerable('toString'),
        dontEnums = [
          'toString',
          'toLocaleString',
          'valueOf',
          'hasOwnProperty',
          'isPrototypeOf',
          'propertyIsEnumerable',
          'constructor'
        ],
        dontEnumsLength = dontEnums.length;

    return function(obj) {
      if (typeof obj !== 'object' && (typeof obj !== 'function' || obj === null)) {
        throw new TypeError('Object.keys called on non-object');
      }

      var result = [], prop, i;

      for (prop in obj) {
        if (hasOwnProperty.call(obj, prop)) {
          result.push(prop);
        }
      }

      if (hasDontEnumBug) {
        for (i = 0; i < dontEnumsLength; i++) {
          if (hasOwnProperty.call(obj, dontEnums[i])) {
            result.push(dontEnums[i]);
          }
        }
      }
      return result;
    };
  }());
}


// Django CSRF requirements
$(document).ajaxSend(function (event, xhr, settings) {
    // due to CSRF_COOKIE_HTTPONLY, we get token from HTML, not cookie
    function getCsrfToken () {
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
        xhr.setRequestHeader("X-CSRFToken", getCsrfToken());
    }
});

var learnscripture = (function (learnscripture, $) {
    "use strict";
    var displaySimpleAjaxError = function (errorResponse) {
        var parts = errorResponse.responseText.split(/\n/);
        if (parts.length == 1) {
            return parts[0];
        } else {
            var errors = $.parseJSON(parts[1]);
            var retval = '';
            for (var key in errors) {
                retval = retval + errors[key];
            }
            return retval;
        }
    }

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
        indicateLoading();
        $('#id-ajax-errors').html('<span>' + text + '</span>');
    };

    var ajaxRetryFailed = function (jqXHR, textStatus, errorThrown) {
        $('#id-ajax-status').show();
        $('#id-ajax-loading').hide();
        $('#id-ajax-errors').html('<span>Data not saved. Please check internet connection</span>');
    };

    var indicateLoading = function () {
        $('#id-ajax-status').show();
        $('#id-ajax-loading').show();
    };

    var hideLoadingIndicator = function () {
        $('#id-ajax-status').hide();
        $('#id-ajax-loading').hide();
    };

    var ajaxRetrySucceeded = function () {
        $('#id-ajax-errors').html('');
    };

    var isTouchDevice = function () {
        return 'ontouchstart' in window;
    };

    var isAndroid = function () {
        return navigator.userAgent.toLowerCase().indexOf("android") > -1;
    };

    var deviceCanVibrate = function () {
        return (("vibrate" in navigator)
                || (window.androidlearnscripture &&
                    window.androidlearnscripture.vibrate));
    }

    var getLocation = function(href) {
        var l = document.createElement("a");
        l.href = href;
        return l;
    };

    // Export:
    learnscripture.handleFormValidationErrors = handleFormValidationErrors;
    learnscripture.displaySimpleAjaxError = displaySimpleAjaxError;
    learnscripture.ajaxFailed = ajaxFailed;
    learnscripture.ajaxRetryOptions = {tick: ajaxRetryTick,
                                       attempts: 11
                                      };
    learnscripture.ajaxRetryFailed = ajaxRetryFailed;
    learnscripture.ajaxRetrySucceeded = ajaxRetrySucceeded;
    learnscripture.isTouchDevice = isTouchDevice;
    learnscripture.isAndroid = isAndroid;
    learnscripture.deviceCanVibrate = deviceCanVibrate;
    learnscripture.indicateLoading = indicateLoading;
    learnscripture.hideLoadingIndicator = hideLoadingIndicator;
    learnscripture.getLocation = getLocation;
    return learnscripture;

}(learnscripture || {}, $));


// Use [[ and ]] for templates to avoid clash with Django templates
$.views.delimiters('[[', ']]');

$(document).ready(function () {
    // Dropdown in topbar
    $('.topbar').dropdown();

    if (learnscripture.isTouchDevice()) {
        // A bit hacky but works:
        $('#id_desktop_testing_method').parent().parent().hide();
    } else {
        $('#id_touchscreen_testing_method').parent().parent().hide();
    }

    if (!learnscripture.deviceCanVibrate()) {
        $('#id_enable_vibration').closest('ul').parent().hide();
    }

    // Scrolling of #id-ajax-status
    var TOPBAR_HEIGHT = 40;
    $(window).scroll(function (ev) {
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

    $(document).ajaxStop(function () {
        learnscripture.hideLoadingIndicator();
    });

});
