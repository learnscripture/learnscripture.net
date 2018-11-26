/*jslint browser: true, vars: true, plusplus: true, maxerr: 1000 */
/*globals alert, confirm */
"use strict";

import { handleFormValidationErrors, ajaxFailed } from './common';
import { BIBLE_BOOK_INFO } from './bible_book_info';

var lastSetReference = null;

var range = function(start, stop) {
    var foo = [], i;
    for (i = start; i < stop; i++) {
        foo.push(i);
    }
    return foo;
};

var bookChange = function(ev) {
    var $form = $(this).closest('form');
    var book = $(ev.target).val();
    if (book === '' || book === null || typeof book !== "string") {
        setChapterStartSelect($form, []);
    } else {
        setChapterStartSelect($form, range(1, BIBLE_BOOK_INFO[book]['chapter_count'] + 1));
        setQuickFind($form);
    }
};

var chapterStartChange = function(ev) {
    var $form = $(this).closest('form');
    var book = getBook($form);
    var chapterStart = getChapterStart($form);
    if (chapterStart === null) {
        setChapterEndSelect($form, []);
        setVerseStartSelect($form, []);
    } else {
        setChapterEndSelect($form, range(chapterStart, BIBLE_BOOK_INFO[book]['chapter_count'] + 1));
        setVerseStartSelect($form, range(1, BIBLE_BOOK_INFO[book]['verse_counts'][chapterStart] + 1))
    }
    setQuickFind($form);

};

var chapterEndChange = function(ev) {
    var $form = $(this).closest('form');
    var book = getBook($form);
    var chapterEnd = getChapterEnd($form);
    // chapterEnd doesn't have an empty option, so don't need to deal with that.
    setVerseEndSelect($form, range(1, BIBLE_BOOK_INFO[book]['verse_counts'][chapterEnd] + 1))
    setQuickFind($form);

};

var verseStartChange = function(ev) {
    var $form = $(this).closest('form');
    var book = getBook($form);
    var verseStart = getVerseStart($form);
    var verseEnd = getVerseEnd($form);
    var chapterStart = getChapterStart($form);
    var chapterEnd = getChapterEnd($form);
    if (verseStart === null) {
        setChapterEndSelect($form, [])
        setVerseEndSelect($form, []);
    } else {
        if (chapterEnd === null) {
            setChapterEndSelect($form, range(chapterStart, BIBLE_BOOK_INFO[book]['chapter_count'] + 1));
            setChapterEndSelectValue($form, chapterStart);
            chapterEnd = chapterStart;
        }

        var lastVerse;
        lastVerse = BIBLE_BOOK_INFO[book]['verse_counts'][chapterEnd];
        if (chapterStart !== chapterEnd) {
            setVerseEndSelect($form, range(1, lastVerse + 1));
            if (verseEnd < lastVerse + 1) {
                // restore
                setVerseEndSelectValue($form, verseEnd);
            }
        } else {
            setVerseEndSelect($form, range(verseStart + 1, lastVerse + 1));
            if (verseEnd >= verseStart + 1 &&
                verseEnd < lastVerse + 1) {
                // restore
                setVerseEndSelectValue($form, verseEnd);
            }
        }
    }
    setQuickFind($form);
};

var verseEndChange = function(ev) {
    var $form = $(this).closest('form');
    setQuickFind($form);
};

var versionChange = function(ev) {
    var $form = $(this).closest('form');
    var langCode = $('#id-version-select option:selected').attr('lang');
    $form.find('select[name=book] option').each(function(idx, elem) {
        var $opt = $(elem);
        $opt.text($opt.attr('data-lang-' + langCode));
    });
    if (lastSetReference !== null) {
        if ($('input[name=quick_find]').val() == lastSetReference) {
            setQuickFind($form); // Might need to be updated due to language change
        }
    }
    languageChange();
}

var languageChange = function() {
    var langCode = $('#id-version-select option:selected').attr('lang');
    $('[data-lang-specific]').hide().filter('[lang=' + langCode + ']').show();
}

var getBook = function($form) {
    return $form.find('select[name=book]').val();
};

var getBookName = function(internalBookName) {
    return $('select[name=book] option[value=' + internalBookName + ']').text();
};

var getChapterStart = function($form) {
    return getSelectNumber($form, 'select[name=chapter_start]');
};

var getChapterEnd = function($form) {
    return getSelectNumber($form, 'select[name=chapter_end]');
};

var getVerseStart = function($form) {
    return getSelectNumber($form, 'select[name=verse_start]');
};

var getVerseEnd = function($form) {
    return getSelectNumber($form, 'select[name=verse_end]');
};

var getSelectNumber = function($form, selector) {
    var s = $form.find(selector);
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

var fillNumberSelect = function(select, numbers, addEmpty) {
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

var setBookByName = function($form, languageCode, bookName) {
    var $bookSelect = $form.find("select[name=book]")
    $bookSelect.find("option").filter(function() {
        return $(this).attr('data-lang-' + languageCode) == bookName;
    }).prop('selected', true);
};

var setChapterStartSelect = function($form, chapters) {
    fillNumberSelect($form.find('select[name=chapter_start]'), chapters, true);
    setChapterEndSelect($form, []);
    setVerseStartSelect($form, []);
};

var setChapterStartSelectValue = function($form, value) {
    $form.find('select[name=chapter_start]').val(value);
};

var setChapterEndSelect = function($form, chapters) {
    fillNumberSelect($form.find('select[name=chapter_end]'), chapters, false);
};

var setChapterEndSelectValue = function($form, value) {
    $form.find('select[name=chapter_end]').val(value);
};

var setVerseStartSelect = function($form, verses) {
    fillNumberSelect($form.find('select[name=verse_start]'), verses, true);
    setVerseEndSelect($form, []);
};

var setVerseStartSelectValue = function($form, value) {
    $form.find('select[name=verse_start]').val(value);
};

var setVerseEndSelect = function($form, verses) {
    fillNumberSelect($form.find('select[name=verse_end]'), verses, true);
};

var setVerseEndSelectValue = function($form, value) {
    $form.find('select[name=verse_end]').val(value);
};

var setControlsFromParsedRef = function($form, parsedRef) {
    setBookByName($form, parsedRef.language_code, parsedRef.book_name);
    $form.find('select[name=book]').trigger('change')
    setChapterStartSelectValue($form, parsedRef.start_chapter.toString());
    $form.find('select[name=chapter_start]').trigger('change');
    setVerseStartSelectValue($form, parsedRef.start_verse.toString());
    $form.find('select[name=verse_start]').trigger('change');
    setChapterEndSelectValue($form, parsedRef.end_chapter.toString());
    $form.find('select[name=chapter_end]').trigger('change');
    setVerseEndSelectValue($form, parsedRef.end_verse.toString());
    $form.find('select[name=verse_end]').trigger('change');
}

var setQuickFind = function($form) {
    var text = getReferenceFromControls($form);
    $form.find('input[name=quick_find]').val(text);
    lastSetReference = text;
}

var getReferenceFromControls = function($form) {
    var book = getBook($form);
    var chapterStart = getChapterStart($form);
    var chapterEnd = getChapterEnd($form);
    var verseStart = getVerseStart($form);
    var verseEnd = getVerseEnd($form);

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
        if (verseEnd != undefined && (
            (chapterStart != chapterEnd) ||
            (verseStart != verseEnd))) {
            text = text + "-" + verseEnd.toString();
        }
    }
    return text;
};

export const quickFindAndHandleResults = function(resultHandler, passageMode, renderFor, $form: JQuery, showMore) {

    var handler = function(ev) {
        ev.preventDefault();
        var page = 0;
        if (showMore) {
            page = parseInt($(ev.target).attr('data-page'), 10);
        }
        $.ajax({
            url: '/api/learnscripture/v1/versefind/?format=json',
            dataType: 'json',
            type: 'GET',
            data: {
                'quick_find': $form.find('input[name=quick_find]').val(),
                'version_slug': $('#id-version-select').val(),
                'passage_mode': passageMode ? '1' : '0',
                'render_for': renderFor,
                'page': page.toString(),
            },
            success: function(results) {
                resultHandler(results);
                if (results.parsed_reference !== null) {
                    setControlsFromParsedRef($form, results.parsed_reference);
                }
            },
            error: function(jqXHR, textStatus, errorThrown) {
                if (jqXHR.status === 400) {
                    $form.parent().find('.quickfind_search_results *').remove();
                    handleFormValidationErrors($form, '', jqXHR);
                } else {
                    ajaxFailed(jqXHR, textStatus, errorThrown);
                }
            }
        });
    };
    return handler;
};


var setupQuickFindControls = function() {
    $('form.quickfind select[name=book]').change(bookChange);
    $('form.quickfind select[name=chapter_start]').change(chapterStartChange);
    $('form.quickfind select[name=chapter_end]').change(chapterEndChange);
    $('form.quickfind select[name=verse_start]').change(verseStartChange);
    $('form.quickfind select[name=verse_end]').change(verseEndChange);
    $('form.quickfind select[name=version]').change(versionChange);
    $('form.quickfind input[type=text]').bind('keypress', function(ev) {
        if (ev.keyCode === 13) {
            ev.preventDefault();
            $(this).closest('form').find('[type=submit].primary:first').click();
        }
    });
    languageChange();
};


$(document).ready(function() {
    setupQuickFindControls();
});
