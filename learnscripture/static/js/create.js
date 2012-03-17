var learnscripture =
    (function(learnscripture, $) {

        var addVerse = function(verseData) {
            var newrow = $('<tr><td></td><td></td><td><i class="icon-arrow-up"></i></td><td><i class="icon-arrow-down"></i></td><td><i class="icon-trash"></i></td></tr>').find('td:first-child').text(verseData.reference).end().find('td:nth-child(2)').text(verseData.text).end();
            $('#id-selection-verse-list tbody').append(newrow);
            $('#id-selection-verse-list').show();
        }

        var addVerseClick = function(ev) {
            ev.preventDefault();
            var btn = $(ev.target);
            $.ajax({url: '/api/learnscripture/v1/versefind/',
                    data: btn.closest('form').serialize(),
                    dataType: 'json',
                    success: function(results) {
                        addVerse(results[0]);
                        btn.closest('.actionset').remove();
                    }
                   });
        };

        var previousPassageRef = null;

        var addPassage = function(passageData) {
            $('#id-passage-verse-list tbody tr').remove();
            $.each(passageData.verse_list, function(idx, verseData) {
                var newrow = $('<tr><td><input type="checkbox" /></td><td></td><td></td></tr>').find('td:nth-child(2)').text(verseData.reference).end().find('td:nth-child(3)').text(verseData.text).end();
                $('#id-passage-verse-list tbody').append(newrow);
            });
            $('#id-passage-verse-list').show();
            $('#id-passage-verse-message *').remove();
            var ref = passageData.reference;
            var currentName = $('#id_passage-name').val().trim();
            if (currentName == "" || currentName == previousPassageRef) {
                $('#id_passage-name').val(ref);
            }
            previousPassageRef = ref;
        }

        var lookupPassageClick = function(ev) {
            ev.preventDefault();
            $.ajax({url: '/api/learnscripture/v1/getpassage/',
                    // This is the wrong form, but it includes the form we want,
                    // and otherwise we can't get this to work
                    data: $('#id-passage-verse-set-form').serialize(),
                    dataType: 'json',
                    success: addPassage,
                    error: function(jqXHR, textStatus, errorThrown) {
                        // TODO - handle other errors apart from validation
                        var errors = learnscripture.handleFormValidationErrors($('#id-passage-verse-selector'),
                                                                               'passage', jqXHR);
                        if (errors['__all__']) {
                            var msg = $('<div class="alert-message warning"></div>')
                            msg.text(errors['__all__'].join(' '));
                            $('#id-passage-verse-message').html(msg);
                        }
                    }
                   });
        };

        var deleteButtonClick = function(ev) {
            ev.preventDefault();
            $(ev.target).closest('tr').remove();
        };

        var selectionSaveBtnClick = function(ev) {
            // Create hidden fields with all references
            var refs = [];
            $('#id-selection-verse-list td:first-child').each(function(idx, elem) {
                refs.push($(elem).text());
            });
            $('#id-selection-reference-list').val(refs.join('|'));
            $('#id-selection-verse-set-form').submit();
        };

        var passageSaveBtnClick =  function(ev) {
            // Create hidden fields with all references
            var refs = [];
            var breaks = [];
            $('#id-passage-verse-list tbody tr').each(function(idx, elem) {
                var row = $(elem);
                var ref = $(row.find('td').get(1)).text();
                refs.push(ref);
                if (row.find('input').attr('checked') == 'checked') {
                    breaks.push(ref.split(" ").slice(-1)[0]);
                }
            });
            $('#id-passage-reference-list').val(refs.join('|'));
            $('#id-passage-break-list').val(breaks.join(','));
            // continue with submit
        };

        var loadResults = function(results) {
            $('#id-verse-find-form .validation-error').remove();
            var d = $('.quickfind_search_results');
            if (results.length > 0) {
                var html = '';
                if (results.length > 10) {
                    html = html + "<p>The first 10 results matching your search are below:</p>";
                }
                html = html + $('#id_create_selection_result_template').render(results);
                d.html(html);
                d.find('input[type=submit]').click(addVerseClick);
            } else {
                d.html("<p><span class='error'>No verses were found matching your search</span></p>");
            }
        };

        var setupCreateVerseSetControls = function() {
            if ($('#id-selection-verse-list tbody tr').length == 0) {
                $('#id-selection-verse-list').hide();
            }
            if ($('#id-passage-verse-list tbody tr').length == 0) {
                $('#id-passage-verse-list').hide();
            }
            $('#id-selection-verse-list').on('click', 'i.icon-arrow-up,i.icon-arrow-down',
                function(ev) {
                    var row = $(this).parents("tr:first");
                    if ($(this).is(".icon-arrow-up")) {
                        row.insertBefore(row.prev());
                    } else {
                        row.insertAfter(row.next());
                    }
                });
            $('#id-selection-verse-list tbody').sortable();
            $('#id-selection-verse-list tbody').disableSelection();
            $('#id-selection-verse-list tbody').on('click', '.icon-trash', deleteButtonClick);
            $('#id-add-verse-btn').click(addVerseClick);
            $('#id-selection-save-btn').click(selectionSaveBtnClick);

            $('#id-lookup-passage-btn').click(lookupPassageClick);
            $('#id-passage-save-btn').click(passageSaveBtnClick);

            $("#id-tab-selection input[type=\"text\"], " +
              "#id-tab passage input[type=\"text\"]").keypress(function (ev) {
              if ((ev.which && ev.which == 13) || (ev.keyCode && ev.keyCode == 13)) {
                  // Stop browsers from submitting:
                  ev.preventDefault();
              }
              });
            $('#id_selection-public, #id_passage-public').each(function(idx, elem) {
                var input = $(elem);
                if (input.attr('checked')) {
                    input.attr('disabled', 'disabled');
                }
            });
            $('#id_lookup').click(learnscripture.quickFindAndHandleResults(loadResults));

        };

        // Public interface:
        learnscripture.setupCreateVerseSetControls = setupCreateVerseSetControls;

        return learnscripture;
    })(learnscripture || {}, $);

$(document).ready(function() {
    if ($('#id-selection-verse-set-form, #id-passage-verse-set-form').length > 0) {
        learnscripture.setupCreateVerseSetControls();
    }
});
