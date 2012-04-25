var learnscripture = (function (learnscripture, $) {
    "use strict";
    var setupVersePopups = function () {
        $('.verse-popup-ref')
            .popover({
                title: function () {
                    return this.attributes['data-reference'].value +
                        " (" + this.attributes['data-version'].value + ")";
                },
                content: function () {
                    var ref = this.attributes['data-reference'].value;
                    var version = this.attributes['data-version'].value;
                    var content;
                    $.ajax({url: '/api/learnscripture/v1/versefind/',
                            dataType: 'json',
                            type: 'GET',
                            async: false,
                            data: {
                                'quick_find': ref,
                                'version_slug': version
                            },
                            success: function(results) {
                                content = results[0].text
                            }
                           });
                    return content;
                },
                trigger: 'manual',
            })
            .bind('mouseenter', function(ev) { $(this).popover('show');})
            .bind('mouseleave', function(ev) { $(this).popover('hide');})
            .bind('focus', function(ev) { $(this).popover('show');})
            .bind('blur', function(ev) { $(this).popover('hide');})
        ;
    };
    // Exports
    learnscripture.setupVersePopups = setupVersePopups;

    return learnscripture;
}(learnscripture || {}, $));


$(document).ready(learnscripture.setupVersePopups);
