// Common functionality and requirements.
import 'jsrender';
import 'jquery-pjax';


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
// * for essential things (e.g. POST requests that save test scores to server)
//   use:
//       retry: ajaxRetryOptions,
//       error: ajaxRetryFailed,
//       success: ajaxRetrySucceeded
//       (or call ajaxRetrySucceeded at beginning of success callback)
export const ajaxFailed = function(jqXHR, textStatus, errorThrown) {

    alert(`The server could not be contacted or an error occurred (${jqXHR.responseText}). Please try again.`);
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

    // Scrolling of #id-ajax-status
    // var TOPBAR_HEIGHT = 36;
    // $(window).scroll(function(ev) {
    //     // We want ajax div to stay underneath the topbar.
    //     // topbar can be either fixed or absolute depending on screen size.

    //     // TODO - rework

    //     var $tb = $('.topbar');
    //     var $aj = $('#id-ajax-status');
    //     var height;
    //     if ($tb.css('position') == 'fixed') {
    //         height = TOPBAR_HEIGHT;
    //     } else {
    //         // static
    //         height = Math.max(0, TOPBAR_HEIGHT - window.scrollY);
    //     }
    //     var heightString = height.toString() + "px";
    //     if ($aj.css('top') != heightString) {
    //         $aj.css('top', heightString);
    //     }
    // });

    $(document).ajaxStop(function() {
        hideLoadingIndicator();
    });

    // PJAX
    $('form[data-pjax-results-container]').each(function(idx, elem) {

        var $form = $(elem);
        var containerSelector = $form.attr("data-pjax-results-container");
        $form.on('submit', function(ev) {
            ev.preventDefault();
            $.pjax.submit(ev, {
                container: containerSelector,
                scrollTo: false
            });
        });

        $form.find("input").on('change', function(ev) {
            $form.submit();
        })

        if ($.support.pjax) {
            var $staticParent = $(containerSelector);
            var moreResultsContainer = $form.attr("data-pjax-more-results-container");
            if (moreResultsContainer != null && moreResultsContainer != "") {
                // Use 'on' binding on $staticParent because this is an element
                // that doesn't get replaced, while its children can be.
                $staticParent.on('click', moreResultsContainer + ' a[data-pjax]', function(ev) {
                    var $moreResults = $staticParent.find(moreResultsContainer);
                    // We always want to eliminate the old 'more results' container,
                    // replacing it with the results, after we've loaded them. We
                    // will also have a new 'more results' container, nested inside
                    // the old one, which we mustn't remove.

                    // TODO this probable has race conditions if multiple PJAX
                    // requests are running at once.
                    $(document).one('pjax:success', function() {
                        $moreResults.find("> :first-child").unwrap();
                    })
                    // Constraints for PJAX "show more":
                    // - we want bots to be able to browse everything on the site
                    //   using "load more" links, whether they execute Javascript or
                    //   not.
                    // - we want to avoid the server having to generate huge pages
                    // - we want to avoid normal users seeing partial pages.

                    // This means:
                    // - 'from_item' parameter - should only generate the next bit, not a whole page
                    // - users shouldn't see URLs with 'from' bit, so they won't share them.
                    //   This means 'push: false'
                    // - bots should be told `noindex, follow` for these pages
                    $.pjax.click(ev, {
                        container: moreResultsContainer,
                        push: false,
                        scrollTo: false
                    });
                });

            }
        }
    });

});

$.pjax.defaults.timeout = 3000
