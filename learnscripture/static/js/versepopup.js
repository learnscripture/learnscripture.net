var learnscripture = (function (learnscripture, $) {
    "use strict";
    var cancelLearningClick = function (ev) {
        ev.preventDefault();
        var $btn = $(this);
        var $form = $btn.closest('form');
        $.ajax({
            url: '/api/learnscripture/v1/cancellearningverse/?format=json',
            dataType: 'json',
            type: 'POST',
            data: {
                verse_status: JSON.stringify({
                    id: $form.find('input[name=verse_status_id]').val(),
                    reference: $form.find('input[name=verse_status_reference]').val()
                }, null, 2)
            },
            success: function () {
                $btn.closest('tr').remove();
            },
            error: learnscripture.ajaxFailed

        });
    }

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
                                $target.find('.cancel-learning-btn').bind('click', cancelLearningClick);
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
