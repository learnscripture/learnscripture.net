
// Common functionality and requirements.
// See also some things at end e.g. modals.js

if (String.prototype.trim == undefined) {
    // Before ECMAscript 5 (e.g. Android 1.6, older IE versions)
    String.prototype.trim=function(){return this.replace(/^\s\s*/, '').replace(/\s\s*$/, '');};
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
                if (key == '__all__') { return; }
                var formElem = $('#id_' + prefix + key);
                var p = formElem.parent();
                if (p.find("ul.validation-error").length == 0) {
                    p.append("<ul class='validation-error'></ul>");
                }
                p.find("ul.validation-error").append($('<li class="help-inline"></li>').text(msg));
                p.parent().addClass("error");
                });
            });
        return errors; // In cases other people want to use it

    };
    // Export:
    learnscripture.handleFormValidationErrors = handleFormValidationErrors;
    return learnscripture;

})(learnscripture || {}, $);


// Dropdown in topbar
$(document).ready(function() {
    $('.topbar').dropdown();
});
