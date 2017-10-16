/*jslint browser: true, vars: true, plusplus: true, maxerr: 1000 */
/*globals $, jQuery, alert, confirm, BIBLE_BOOK_INFO */
var learnscripture =
    (function (learnscripture, $) {
        "use strict";

        var MAX_VERSES_FOR_SINGLE_CHOICE = 4;

        var range = function (start, stop) {
            var foo = [], i;
            for (i = start; i < stop; i++) {
                foo.push(i);
            }
            return foo;
        };

        var isInPassageMode = function (form) {
            return form.find('select[name=chapter_end]').length > 0;
        };

        var bookChange = function (ev) {
            var form = $(this).closest('form');
            var book = $(ev.target).val();
            if (book === '' || book === null) {
                setChapterStartSelect(form, []);
            } else {
                setChapterStartSelect(form, range(1, BIBLE_BOOK_INFO[book]['chapter_count'] + 1));
                setQuickFind(form);
            }
        };

        var chapterStartChange = function (ev) {
            var form = $(this).closest('form');
            var book = getBook(form);
            var chapterStart = getChapterStart(form);
            if (chapterStart === null) {
                setChapterEndSelect(form, []);
                setVerseStartSelect(form, []);
            } else {
                setChapterEndSelect(form, range(chapterStart, BIBLE_BOOK_INFO[book]['chapter_count'] + 1));
                setVerseStartSelect(form, range(1, BIBLE_BOOK_INFO[book]['verse_counts'][chapterStart] + 1))
            }
            setQuickFind(form);

        };

        var chapterEndChange = function (ev) {
            var form = $(this).closest('form');
            var book = getBook(form);
            var chapterEnd = getChapterEnd(form);
            // chapterEnd doesn't have an empty option, so don't need to deal with that.
            setVerseEndSelect(form, range(1, BIBLE_BOOK_INFO[book]['verse_counts'][chapterEnd] + 1))
            setQuickFind(form);

        };

        var verseStartChange = function (ev) {
            var form = $(this).closest('form');
            var book = getBook(form);
            var verseStart = getVerseStart(form);
            var verseEnd = getVerseEnd(form);
            var chapterStart = getChapterStart(form);
            var chapterEnd = getChapterEnd(form);
            var passageMode = isInPassageMode(form);
            if (verseStart === null) {
                if (passageMode) {
                    setChapterEndSelect(form, [])
                }
                setVerseEndSelect(form, []);
            } else {
                if (passageMode && chapterEnd === null) {
                    setChapterEndSelect(form, range(chapterStart, BIBLE_BOOK_INFO[book]['chapter_count'] + 1));
                    setChapterEndSelectValue(form, chapterStart);
                    chapterEnd = chapterStart;
                }

                var lastVerse;
                if (passageMode) {
                    lastVerse = BIBLE_BOOK_INFO[book]['verse_counts'][chapterEnd];
                } else {
                    lastVerse = BIBLE_BOOK_INFO[book]['verse_counts'][chapterStart];
                    lastVerse = Math.min(lastVerse, verseStart - 1 + MAX_VERSES_FOR_SINGLE_CHOICE);
                }
                if (passageMode && chapterStart !== chapterEnd) {
                    setVerseEndSelect(form, range(1, lastVerse + 1));
                    if (verseEnd < lastVerse + 1) {
                        // restore
                        setVerseEndSelectValue(form, verseEnd);
                    }
                } else {
                    setVerseEndSelect(form, range(verseStart + 1, lastVerse + 1));
                    if (verseEnd >= verseStart + 1 &&
                        verseEnd < lastVerse + 1) {
                        // restore
                        setVerseEndSelectValue(form, verseEnd);
                    }
                }
            }
            setQuickFind(form);
        };

        var verseEndChange = function (ev) {
            var form = $(this).closest('form');
            setQuickFind(form);
        };

        var getBook = function (form) {
            return form.find('select[name=book]').val();
        };

        var getChapterStart = function (form) {
            return getSelectNumber(form, 'select[name=chapter_start]');
        };

        var getChapterEnd = function (form) {
            return getSelectNumber(form, 'select[name=chapter_end]');
        };

        var getVerseStart = function (form) {
            return getSelectNumber(form, 'select[name=verse_start]');
        };

        var getVerseEnd = function (form) {
            return getSelectNumber(form, 'select[name=verse_end]');
        };

        var getSelectNumber = function (form, selector) {
            var s = form.find(selector);
            if (s.length === 0) {
                return null;
            }
            var num = s.val();
            if (num === '' || num === null) {
                return null;
            } else {
                return parseInt(num, 10);
            }
        };

        var fillNumberSelect = function (select, numbers, addEmpty) {
            var i;
            if (select.length === 0) {
                return;
            }
            select.children().remove();
            if (numbers.length > 0) {
                if (addEmpty) {
                    select.append('<option value="">-</option>');
                }
                for (i = 0; i < numbers.length; i++) {
                    var n = numbers[i].toString();
                    select.append('<option value="' + n + '">' + n + '</option>');
                }
            }
        };

        var setChapterStartSelect = function (form, chapters) {
            fillNumberSelect(form.find('select[name=chapter_start]'), chapters, true);
            setChapterEndSelect(form, []);
            setVerseStartSelect(form, []);
        };

        var setChapterEndSelect = function (form, chapters) {
            fillNumberSelect(form.find('select[name=chapter_end]'), chapters, false);
        };

        var setChapterEndSelectValue = function (form, value) {
            form.find('select[name=chapter_end]').val(value);
        };

        var setVerseStartSelect = function (form, verses) {
            fillNumberSelect(form.find('select[name=verse_start]'), verses, true);
            setVerseEndSelect(form, []);
        };

        var setVerseEndSelect = function (form, verses) {
            fillNumberSelect(form.find('select[name=verse_end]'), verses, true);
        };

        var setVerseEndSelectValue = function (form, value) {
            form.find('select[name=verse_end]').val(value);
        };

        var setQuickFind = function (form) {
            var book = getBook(form);
            var chapterStart = getChapterStart(form);
            var chapterEnd = getChapterEnd(form);
            var verseStart = getVerseStart(form);
            var verseEnd = getVerseEnd(form);

            if (chapterStart != undefined && chapterEnd != undefined
                && chapterStart != chapterEnd
                && verseStart != undefined
                && verseEnd == undefined) {
                // This can't be turned into a reference
                return
            }

            if (chapterStart != undefined && chapterEnd != undefined
                && chapterStart != chapterEnd
                && verseStart == undefined
                && verseEnd == undefined) {
                // This can be turned into a meaningful reference,
                // but our backend can't handle it
                return;
            }

            var bookName = getBookName(book);
            var text = bookName + " ";
            if (chapterStart != undefined) {
                text = text + chapterStart.toString();
            }
            if (verseStart != undefined) {
                text = text + ":" + verseStart.toString();
            }
            if (chapterEnd != undefined && chapterEnd != chapterStart) {
                text = text + "-" + chapterEnd.toString();
                if (verseEnd != undefined) {
                    text = text + ":" + verseEnd.toString();
                }
            } else {
                if (verseEnd != undefined) {
                    text = text + "-" + verseEnd.toString();
                }
            }
            form.find('input[name=quick_find]').val(text);
        };

        var getBookName = function (internalBookName) {
            return $('select[name=book] option[value=' + internalBookName + ']').text();
        }

        var quickFindAndHandleResults = function (resultHandler, passageMode) {

            var handler = function (ev) {
                var form = $(ev.target).closest('form');
                ev.preventDefault();
                $.ajax({url: '/api/learnscripture/v1/versefind/?format=json',
                        dataType: 'json',
                        type: 'GET',
                        data: {
                            'quick_find': form.find('input[name=quick_find]').val(),
                            'version_slug': $('#id-version-select').val(),
                            'passage_mode': passageMode ? '1' : '0'
                        },
                        success: resultHandler,
                        error:  function (jqXHR, textStatus, errorThrown) {
                            if (jqXHR.status === 400) {
                                form.parent().find('.quickfind_search_results *').remove();
                                learnscripture.handleFormValidationErrors(form, '', jqXHR);
                            } else if (jqXHR.status === 500) {
                                form.parent().find('.quickfind_search_results').html('Your search terms were not understood.');
                            } else {
                                learnscripture.ajaxFailed(jqXHR, textStatus, errorThrown);
                            }
                        }
                       });
            };
            return handler;
        };


        var setupQuickFindControls = function () {
            $('form.quickfind select[name=book]').change(bookChange);
            $('form.quickfind select[name=chapter_start]').change(chapterStartChange);
            $('form.quickfind select[name=chapter_end]').change(chapterEndChange);
            $('form.quickfind select[name=verse_start]').change(verseStartChange);
            $('form.quickfind select[name=verse_end]').change(verseEndChange);
            $('form.quickfind input[name=quick_find]');
            $('form.quickfind input[type=text]').bind('keypress', function (ev){
                if (ev.keyCode === 13) {
                    ev.preventDefault();
                    $(this).closest('form').find('input[type=submit].primary:first').click();
                }
            });
        };

        // Exports:
        learnscripture.setupQuickFindControls = setupQuickFindControls;
        learnscripture.quickFindAndHandleResults = quickFindAndHandleResults;

        return learnscripture;

    }(learnscripture || {}, $));

$(document).ready(function () {
    learnscripture.setupQuickFindControls();
});
