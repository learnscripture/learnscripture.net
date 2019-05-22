import { ajaxFailed } from './common';
import { BIBLE_BOOK_INFO } from './bible_book_info';
import { quickFindAndHandleResults } from './quickfind';

var addVerse = function(verseHtml) {
    $('#id-verse-list tbody').append(verseHtml);
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
            addVerse(results['html']);
            btn.closest('.actionset').remove();
        },
        error: ajaxFailed
    });
};

var previousPassageRef = null;

var addPassage = function(results) {
    $('#id-verse-list tbody tr').remove();
    $('#id-verse-list tbody').html(results['html']);
    $('#id-verse-list, #id-verse-list table').show();
    var simplifiedRef = results.canonical_reference;
    var parsedRef = results.parsed_reference;
    if (parsedRef.start_chapter == parsedRef.end_chapter &&
        parsedRef.start_verse == 1 &&
        parsedRef.end_verse == BIBLE_BOOK_INFO[parsedRef.internal_book_name]['verse_counts'][parsedRef.start_chapter.toString()]) {
        // Whole chapter. Special case to make name nicer.
        simplifiedRef = parsedRef.book_name + " " + parsedRef.start_chapter.toString();
    }
    var currentName = (<string>$('#id_name').val()).trim();
    if (currentName === "" || currentName === previousPassageRef) {
        $('#id_name').val(simplifiedRef);
        $('#id_language_code').val(parsedRef.language_code);
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
    $('#id-verse-set-form').submit();
};

var selectionLoadResults = function(results) {
    $('#id-quick-find-form .validation-error').remove();
    var d = $('.quickfind_search_results');
    d.html(results['html']);
    d.find('[type=submit]').click(addVerseClick);
};

var selectionLoadMoreResults = function(results) {
    var d = $('.quickfind_search_results .more-results-container');
    d.html(results['html']);
    d.find('[type=submit]').click(addVerseClick);
    d.children().unwrap();
};

var passageLoadResults = function(results) {
    $('#id-quick-find-form .validation-error').remove();
    $('#id-duplicate-warning').html('');
    addPassage(results);
    // If creating, not editing:
    if (window.location.pathname.match(/\/create-passage-set\//) != null) {
        if (results['duplicate_check_html']) {
            $('#id-duplicate-warning').html(results['duplicate_check_html']);
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
    var $quickFindForm = $('form.quickfind');

    $('#id-create-selection-set #id_lookup').click(quickFindAndHandleResults(selectionLoadResults, false, "create-selection-set", $quickFindForm, false));
    $('.quickfind_search_results').on(
        'click', 'a[data-quick-find-show-more]',
        quickFindAndHandleResults(selectionLoadMoreResults, false, "create-selection-set", $quickFindForm, true));

    $('#id-create-passage-set #id_lookup').click(quickFindAndHandleResults(passageLoadResults, true, "create-passage-row", $quickFindForm, false));

    var $initialRef = $('[name="initial_localized_reference"]');
    if ($initialRef.length > 0 && $initialRef.val() != "") {
        $('#id_quick_find').val($initialRef.val());
        $('#id-create-passage-set #id_lookup').trigger('click');
    }

};

$(document).ready(function() {
    if ($('#id-create-selection-set, #id-create-passage-set').length > 0) {
        setupCreateVerseSetControls();
    }
});

