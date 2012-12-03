var learnscripture = (function (learnscripture, $) {
    "use strict";
    var setupVersePopups = function () {
        $('.verse-popup-btn')
            .popover({
                title: function () {
                    return this.attributes['data-title'].value +
                        " (" + this.attributes['data-version'].value + ")";
                },
                content: function () {
                    var ref = this.attributes['data-reference'].value;
                    var version = this.attributes['data-version'].value;
                    var content;
                    $.ajax({url: '/verse-options/',
                            dataType: 'html',
                            type: 'GET',
                            async: false,
                            data: {
                                'ref': ref,
                                'version_slug': version
                            },
                            success: function(html) {
                                content = html;
                            }
                           });
                    return content;
                },
                html: true,
                trigger: 'manual'
            })
            .toggle(
                function(ev) { $(this).button('toggle').popover('show');},
                function(ev) { $(this).button('toggle').popover('hide');}
            );
    };
    // Exports
    learnscripture.setupVersePopups = setupVersePopups;

    return learnscripture;
}(learnscripture || {}, $));


$(document).ready(learnscripture.setupVersePopups);
