import { ajaxFailed } from './common';


var cancelLearningVerseClick = function(ev) {
    ev.preventDefault();
    var $btn = $(this);
    var $form = $btn.closest('form');
    $.ajax({
        url: '/api/learnscripture/v1/cancellearningverse/?format=json',
        dataType: 'json',
        type: 'POST',
        data: {
            uvs_id: $form.find('input[name=verse_status_id]').val(),
            version_slug: $form.find('input[name=verse_status_version_slug]').val(),
            localized_reference: $form.find('input[name=verse_status_localized_reference]').val()
        },
        success: function() {
            $btn.closest('tbody').remove();
        },
        error: ajaxFailed

    });
};

var cancelLearningPassageClick = function(ev) {
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
        success: function() {
            $btn.closest('table').find('tbody' +
                '[data-verse-set-id=' + verseSetId.toString() + ']' +
                '[data-version-id=' + versionId.toString() + ']'
            ).remove();
        },
        error: ajaxFailed
    });
};

var setupVersePopups = function() {
    $('#id-user-verses-results').on('click', '.verse-popup-btn',
        function(ev) {
            ev.preventDefault();
            var $btn = $(this);
            if ($btn.closest("tbody").find(".verse-options-container").hasClass("hide")) {
                var ref = this.attributes['data-localized-reference'].value;
                var version = this.attributes['data-version'].value;
                var that = this;
                $.ajax({
                    url: '/verse-options/',
                    dataType: 'html',
                    type: 'GET',
                    data: {
                        'ref': ref,
                        'version_slug': version
                    },
                    success: function(html) {
                        var $target = $(that).closest('tbody').find(".verse-options-container");
                        $target.html(html).removeClass("hide")
                        $target.find('.cancel-learning-verse-btn').bind('click', cancelLearningVerseClick);
                        $target.find('.cancel-learning-passage-btn').bind('click', cancelLearningPassageClick);
                    }
                })
            } else {
                $btn.closest('tbody').find('.verse-options-container').addClass("hide");
            }
        });
};


$(document).ready(setupVersePopups);
