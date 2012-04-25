/*jslint browser: true, vars: true, plusplus: true */
/*globals $, jQuery, alert */
var learnscripture =
    (function (learnscripture, $) {
        "use strict";
        var addVerse = function (verseData) {
            var newrow = $('<tr><td></td><td></td><td><span class="icon-arrow-up icon-replace" title="move up">up</span></td><td><span class="icon-arrow-down icon-replace" title="move down">down</span></td><td><span class="icon-trash icon-replace" title="remove">remove</span></td></tr>').find('td:first-child').text(verseData.reference).end().find('td:nth-child(2)').text(verseData.text).end();
            $('#id-verse-list tbody').append(newrow);
            $('#id-verse-list').show();
        };

        var addVerseClick = function (ev) {
            ev.preventDefault();
            var btn = $(ev.target);
            $.ajax({url: '/api/learnscripture/v1/versefind/',
                    data: btn.closest('form').serialize(),
                    dataType: 'json',
                    success: function (results) {
                        addVerse(results[0]);
                        btn.closest('.actionset').remove();
                    },
                    error: learnscripture.ajaxFailed
                   });
        };

        var previousPassageRef = null;

        var addPassage = function (passageData) {
            $('#id-verse-list tbody tr').remove();
            $.each(passageData.verses, function (idx, verseData) {
                var newrow = $('<tr><td><input type="checkbox" /></td><td></td><td></td></tr>').find('td:nth-child(2)').text(verseData.reference).end().find('td:nth-child(3)').text(verseData.text).end();
                $('#id-verse-list tbody').append(newrow);
            });
            $('#id-verse-list').show();
            var ref = passageData.reference;
            var currentName = $('#id_name').val().trim();
            if (currentName === "" || currentName === previousPassageRef) {
                $('#id_name').val(ref);
            }
            previousPassageRef = ref;
        };

        var deleteButtonClick = function (ev) {
            ev.preventDefault();
            $(ev.target).closest('tr').remove();
        };

        var selectionSaveBtnClick = function (ev) {
            // Create hidden fields with all references
            var refs = [];
            $('#id-verse-list td:first-child').each(function (idx, elem) {
                refs.push($(elem).text());
            });
            $('#id-reference-list').val(refs.join('|'));
            $('#id-verse-set-form').submit();
        };

        var passageSaveBtnClick = function (ev) {
            // Create hidden fields with all references
            var refs = [];
            var breaks = [];
            $('#id-verse-list tbody tr').each(function (idx, elem) {
                var row = $(elem);
                var ref = $(row.find('td').get(1)).text();
                refs.push(ref);
                if (row.find('input').attr('checked') === 'checked') {
                    breaks.push(ref.split(" ").slice(-1)[0]);
                }
            });
            $('#id-reference-list').val(refs.join('|'));
            $('#id-break-list').val(breaks.join(','));
            // continue with submit
        };

        var selectionLoadResults = function (results) {
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

        var passageLoadResults = function (results) {
            $('#id-quick-find-form .validation-error').remove();
            $('#id-duplicate-warning').html('');
            if (results.length > 0) {
                addPassage(results[0]);
                // If creating, not editing:
                if (window.location.pathname.match(/\/create-passage-set\//) != null) {
                    var verses = results[0].verses;
                    $.ajax({url: '/api/learnscripture/v1/checkduplicatepassageset/',
                            data: {
                                bible_verse_number_start: verses[0].bible_verse_number,
                                bible_verse_number_end: verses[verses.length-1].bible_verse_number
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

        var setupCreateVerseSetControls = function () {
            if ($('#id-verse-list tbody tr').length === 0) {
                $('#id-verse-list').hide();
            }
            $('#id-verse-list').on('click', '.icon-arrow-up, .icon-arrow-down',
                function (ev) {
                    var row = $(this).parents("tr:first");
                    if ($(this).is(".icon-arrow-up")) {
                        row.insertBefore(row.prev());
                    } else {
                        row.insertAfter(row.next());
                    }
                });
            $('#id-create-selection-set #id-verse-list tbody').sortable();
            $('#id-create-selection-set #id-verse-list tbody').disableSelection();
            $('#id-create-selection-set #id-verse-list tbody').on('click', '.icon-trash', deleteButtonClick);
            $('#id-create-selection-set #id-save-btn').click(selectionSaveBtnClick);

            $('#id-create-passage-set #id-save-btn').click(passageSaveBtnClick);

            $("#id-create-selection-set input[type=\"text\"], " +
              "#id-create-passage-set input[type=\"text\"]").keypress(function (ev) {
                  if ((ev.which && ev.which === 13) || (ev.keyCode && ev.keyCode === 13)) {
                  // Stop browsers from submitting:
                  ev.preventDefault();
              }
              });
            $('#id_public').each(function (idx, elem) {
                var input = $(elem);
                if (input.attr('checked')) {
                    input.attr('disabled', 'disabled');
                }
            });
            $('#id-create-selection-set #id_lookup').click(learnscripture.quickFindAndHandleResults(selectionLoadResults, false));
            $('#id-create-passage-set #id_lookup').click(learnscripture.quickFindAndHandleResults(passageLoadResults, true));

        };

        // Public interface:
        learnscripture.setupCreateVerseSetControls = setupCreateVerseSetControls;

        return learnscripture;
    }(learnscripture || {}, $));

$(document).ready(function () {
    if ($('#id-create-selection-set, #id-create-passage-set').length > 0) {
        learnscripture.setupCreateVerseSetControls();
    }
});
