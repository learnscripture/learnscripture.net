var learnscripture =
    (function(learnscripture, $) {

        var addVerse = function(verseData) {
            var newrow = $('<tr><td></td><td></td></tr>').find('td:first-child').text(verseData.reference).end().find('td:last-child').text(verseData.text).end();
            $('#id-verse-list tbody').append(newrow);
            $('#id-verse-list').show();
            $('#id-verse-message *').remove();
        }

        var addVerseClick = function(ev) {
            ev.preventDefault();
            $.ajax({url: '/api/learnscripture/v1/getverseforselection/',
                    // This is the wrong form, but it includes the form we want,
                    // and otherwise we can't get this to work
                    data: $('#id-selection-verse-set-form').serialize(),
                    dataType: 'json',
                    success: addVerse,
                    error: function(jqXHR, textStatus, errorThrown) {
                        var errors = learnscripture.handleFormValidationErrors($('#id-selection-verse-selector'),
                                                                               'selection', jqXHR);
                        if (errors['__all__']) {
                            var msg = $('<div class="alert-message warning"></div>')
                            msg.text(errors['__all__']);
                            $('#id-verse-message').html(msg);
                        }
                    }
                   });
        }

        var selectionSaveBtnClick = function(ev) {
            // Create hidden fields with all references
            var refs = []
            $('#id-verse-list td:first-child').each(function(idx, elem) {
                refs.push($(elem).text());
            });
            $('#id-reference-list').val(refs.join('|'));
            // continue with submit
        }

        var setupCreateVerseSetControls = function() {
            if ($('#id-verse-list tbody tr').length == 0) {
                $('#id-verse-list').hide();
            }
            $('#id-add-verse-btn').click(addVerseClick);
            $('#id-selection-save-btn').click(selectionSaveBtnClick);
        };

        // Public interface:
        learnscripture.setupCreateVerseSetControls = setupCreateVerseSetControls;

        return learnscripture;
    })(learnscripture || {}, $);

$(document).ready(function() {
    if ($('#id-add-verse-btn').length > 0) {
        learnscripture.setupCreateVerseSetControls();
    }
});
