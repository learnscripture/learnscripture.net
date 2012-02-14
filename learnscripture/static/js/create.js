var learnscripture =
    (function(learnscripture, $) {

        var addVerse = function(verseData) {
            var newrow = $('<tr><td></td><td></td><td><i class="icon-move"></i></td><td><a href="#"><i class="icon-trash"></i></a></td></tr>').find('td:first-child').text(verseData.reference).end().find('td:nth-child(2)').text(verseData.text).end();
            $('#id-selection-verse-list tbody').append(newrow);
            $('#id-selection-verse-list').show();
            $('#id-selection-verse-message *').remove();
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
                            $('#id-selection-verse-message').html(msg);
                        }
                    }
                   });
        }

        var deleteButtonClick = function(ev) {
            ev.preventDefault();
            $(ev.target).closest('tr').remove();
        }

        var selectionSaveBtnClick = function(ev) {
            // Create hidden fields with all references
            var refs = []
            $('#id-selection-verse-list td:first-child').each(function(idx, elem) {
                refs.push($(elem).text());
            });
            $('#id-reference-list').val(refs.join('|'));
            // continue with submit
        }

        var setupCreateVerseSetControls = function() {
            if ($('#id-selection-verse-list tbody tr').length == 0) {
                $('#id-selection-verse-list').hide();
            }
            $('#id-selection-verse-list tbody').sortable();
            $('#id-selection-verse-list tbody').disableSelection();
            $('#id-selection-verse-list tbody').on('click', 'a', deleteButtonClick);
            $('#id-add-verse-btn').click(addVerseClick);
            $('#id-selection-save-btn').click(selectionSaveBtnClick);

            $("#id-tab-selection input[type=\"text\"], " +
              "#id-tab passage input[type=\"text\"]").keypress(function (ev) {
              if ((ev.which && ev.which == 13) || (ev.keyCode && ev.keyCode == 13)) {
                  // Stop browsers from submitting:
                  ev.preventDefault();
              }
              });

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
