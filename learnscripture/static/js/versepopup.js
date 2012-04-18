var learnscripture = (function (learnscripture, $) {
    "use strict";
    var setupVersePopups = function () {
        $('.verse-popup-ref').popover(
            {
                title: function () {
                    return this.dataset.reference + " (" + this.dataset.version + ")";
                },
                content: function () {
                    var ref = this.dataset.reference;
                    var version = this.dataset.version;
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
                }
            });
    };
    // Exports
    learnscripture.setupVersePopups = setupVersePopups;

    return learnscripture;
}(learnscripture || {}, $));


$(document).ready(learnscripture.setupVersePopups);
