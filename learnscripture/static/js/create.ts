import { ajaxFailed } from './common';
import { BIBLE_BOOK_INFO } from './bible_book_info';
import { quickFindAndHandleResults } from './quickfind';

var addVerse = function(verseData) {
    $('#id-verse-list tbody').append(
        $('#id_verse_list_selection_row_template').render({ 'verseData': verseData }));
    $('#id-verse-list table').show();
    $('#id-verse-list-empty-message').hide();
};

var addVerseClick = function(ev) {
    ev.preventDefault();
    var btn = $(ev.target);
    $.ajax({
        url: '/api/learnscripture/v1/versefind/?format=json',
        data: btn.closest('form').serialize(),
        dataType: 'json',
        success: function(results) {
            addVerse(results[0]);
            btn.closest('.actionset').remove();
        },
        error: ajaxFailed
    });
};

var previousPassageRef = null;

var addPassage = function(passageData) {
    $('#id-verse-list tbody tr').remove();
    $.each(passageData.verses, function(idx, verseData) {
        $('#id-verse-list tbody').append(
            $('#id_verse_list_passage_row_template').render({ 'verseData': verseData }));
    });
    $('#id-verse-list').show();
    var ref = passageData.localized_reference;
    var simplifiedRef = ref;
    var parsedRef = passageData.parsed_ref;
    if (parsedRef !== null) {
        if (parsedRef.start_chapter == parsedRef.end_chapter &&
            parsedRef.start_verse == 1 &&
            parsedRef.end_verse == BIBLE_BOOK_INFO[parsedRef.internal_book_name]['verse_counts'][parsedRef.start_chapter.toString()]) {
            // Whole chapter. Special case to make name nicer.
            simplifiedRef = parsedRef.book_name + " " + parsedRef.start_chapter.toString();
        }
    }
    var currentName = (<string>$('#id_name').val()).trim();
    if (currentName === "" || currentName === previousPassageRef) {
        $('#id_name').val(simplifiedRef);
    }
    previousPassageRef = simplifiedRef;
};

var deleteButtonClick = function(ev) {
    ev.preventDefault();
    $(ev.target).closest('tr').remove();
};

var selectionSaveBtnClick = function(ev) {
    ev.preventDefault();
    // Create hidden fields with all internal_references
    var refs = [];
    $('#id-verse-list tr[data-internal-reference]').each(function(idx, elem) {
        refs.push($(elem).attr('data-internal-reference'));
    });
    $('#id-internal-reference-list').val(refs.join('|'));
    $('#id-verse-set-form').submit();
};

var passageSaveBtnClick = function(ev) {
    ev.preventDefault();
    // Create hidden fields with all internal_references
    var refs = [];
    var breaks = [];
    $('#id-verse-list tbody tr[data-internal-reference]').each(function(idx, elem) {
        var $row = $(elem);
        var ref = $row.attr('data-internal-reference');
        refs.push(ref);
        if ($row.find('input').prop('checked')) {
            breaks.push(ref);
        }
    });
    $('#id-internal-reference-list').val(refs.join('|'));
    $('#id-break-list').val(breaks.join(','));
    // continue with submit
};

var selectionLoadResults = function(results) {
    $('#id-quick-find-form .validation-error').remove();
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

var passageLoadResults = function(results) {
    $('#id-quick-find-form .validation-error').remove();
    $('#id-duplicate-warning').html('');
    if (results.length > 0) {
        addPassage(results[0]);
        // If creating, not editing:
        if (window.location.pathname.match(/\/create-passage-set\//) != null) {
            var verses = results[0].verses;
            $.ajax({
                url: '/api/learnscripture/v1/checkduplicatepassageset/?format=json',
                data: {
                    start_reference: verses[0].localized_reference,
                    end_reference: verses[verses.length - 1].localized_reference
                },
                dataType: 'json',
                success: function(results) {
                    if (results.length > 0) {
                        var html = '<p>There are already some passage sets for this passage:</p>'
                        html = html +
                            '<ul>' +
                            $('#id-duplicate-warning-template').render(results) +
                            '</ul>';

                        $('#id-duplicate-warning').html(html);
                    }
                }
            })
        }
    }
};

var setupCreateVerseSetControls = function() {
    if ($('#id-verse-list tbody tr').length === 0) {
        $('#id-verse-list table').hide();
    } else {
        $('#id-verse-list-empty-message').hide();
    }
    $('#id-verse-list').on('click', '.icon-arrow-up, .icon-arrow-down',
        function(ev) {
            var row = $(this).parents("tr:first");
            if ($(this).is(".icon-arrow-up")) {
                row.insertBefore(row.prev());
            } else {
                row.insertAfter(row.next());
            }
        });
    $('#id-create-selection-set #id-verse-list tbody').sortable();
    $('#id-create-selection-set #id-verse-list tbody').on('click', '.icon-trash', deleteButtonClick);
    $('#id-create-selection-set #id-save-btn').click(selectionSaveBtnClick);

    $('#id-create-passage-set #id-save-btn').click(passageSaveBtnClick);

    $("#id-create-selection-set input[type=\"text\"], " +
        "#id-create-passage-set input[type=\"text\"]").keypress(function(ev) {
            if ((ev.which && ev.which === 13) || (ev.keyCode && ev.keyCode === 13)) {
                // Stop browsers from submitting:
                ev.preventDefault();
            }
        });
    $('#id_public').each(function(idx, elem) {
        var input = $(elem);
        if (input.prop('checked')) {
            input.prop('disabled', true);
        }
    });
    $('#id-create-selection-set #id_lookup').click(quickFindAndHandleResults(selectionLoadResults, false));
    $('#id-create-passage-set #id_lookup').click(quickFindAndHandleResults(passageLoadResults, true));

};

$(document).ready(function() {
    if ($('#id-create-selection-set, #id-create-passage-set').length > 0) {
        setupCreateVerseSetControls();
    }
});

