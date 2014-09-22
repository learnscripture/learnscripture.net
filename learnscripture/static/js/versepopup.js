var learnscripture = (function (learnscripture, $) {
    "use strict";
    var setupVersePopups = function () {
        $('.verse-popup-btn')
            .toggle(
                function (ev) {
                    var ref = this.attributes['data-reference'].value;
                    var version = this.attributes['data-version'].value;
                    var that = this;
                    $.ajax({url: '/verse-options/',
                            dataType: 'html',
                            type: 'GET',
                            data: {
                                'ref': ref,
                                'version_slug': version
                            },
                            success: function(html) {
                                var $target = $(that).closest('td')
                                $target.append('<div class="verse-options-container">' + html + '</div>');
                            }
                           });
                },
                function (ev) {
                    $(this).closest('td').find('.verse-options-container').remove();
                });
    };
    // Exports
    learnscripture.setupVersePopups = setupVersePopups;

    return learnscripture;
}(learnscripture || {}, $));


$(document).ready(learnscripture.setupVersePopups);
