"use strict";

var $ = require('jquery');
var common = require('common');


var cancelLearningVerseClick = function (ev) {
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
                version: { slug: $form.find('input[name=verse_status_version_slug]').val() },
                localized_reference: $form.find('input[name=verse_status_localized_reference]').val()
            }, null, 2)
        },
        success: function () {
            $btn.closest('tr').remove();
        },
        error: common.ajaxFailed

    });
};

var cancelLearningPassageClick = function (ev) {
    ev.preventDefault();
    var $btn = $(this);
    var $form = $btn.closest('form');
    var verseSetId = $form.find('input[name=verse_set_id]').val();
    var versionId = $form.find('input[name=version_id]').val();
    $.ajax({
        url: '/api/learnscripture/v1/cancellearningpassage/?format=json',
        dataType: 'json',
        type: 'POST',
        data: {
            verse_set_id: verseSetId,
            version_id: versionId
        },
        success: function () {
            $btn.closest('table').find('tr' +
                                       '[data-verse-set-id=' + verseSetId.toString() + ']' +
                                       '[data-version-id=' + versionId.toString() + ']'
                                      ).remove();
        },
        error: common.ajaxFailed
    });
};

var setupVersePopups = function () {
    $('.verse-popup-btn').click(
        function (ev) {
            ev.preventDefault();
            var $btn = $(this);
            if ($btn.data("popupopen") !== "yes") {
                $btn.data("popupopen", "yes")
                var ref = this.attributes['data-localized-reference'].value;
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
                            $target.find('.cancel-learning-verse-btn').bind('click', cancelLearningVerseClick);
                            $target.find('.cancel-learning-passage-btn').bind('click', cancelLearningPassageClick);
                        }
                       })
            } else {
                $btn.data("popupopen", "no")
                $btn.closest('td').find('.verse-options-container').remove();
            }
        });
};


$(document).ready(setupVersePopups);
