var learnscripture =
    (function(learnscripture, $) {
        var MAX_VERSES_FOR_SINGLE_CHOICE = 4;

        var range = function(start, stop) {
            var foo = [];
            for (var i = start; i < stop; i++)
                foo.push(i);
            return foo;
        };

        var bookChange = function(ev) {
            var form = $(this).closest('form');
            var book = $(ev.target).val();
            if (book == '') {
                setChapterStartSelect(form, []);
            } else {
                setChapterStartSelect(form, range(1, BIBLE_BOOK_INFO[book]['chapter_count'] + 1));
                setQuickFind(form, book);
            }
        };

        var chapterStartChange = function(ev) {
            var form = $(this).closest('form');
            var book = getBook(form);
            var chapterStart = getChapterStart(form);
            if (chapterStart == null) {
                setVerseStartSelect(form, []);
                setQuickFind(form, book);
            } else {
                setVerseStartSelect(form, range(1, BIBLE_BOOK_INFO[book]['verse_counts'][chapterStart] + 1))
                setQuickFind(form, book, chapterStart);
            }

        };

        var verseStartChange = function(ev) {
            var form = $(this).closest('form');
            var book = getBook(form);
            var verseStart = getVerseStart(form);
            var chapterStart = getChapterStart(form);
            if (verseStart == null) {
                setVerseEndSelect(form, []);
                setQuickFind(form, book, chapterStart);
            } else {
                var lastVerse = BIBLE_BOOK_INFO[book]['verse_counts'][chapterStart];
                lastVerse = Math.min(lastVerse, verseStart -1 + MAX_VERSES_FOR_SINGLE_CHOICE);
                setVerseEndSelect(form, range(verseStart + 1, lastVerse + 1))
                setQuickFind(form, book, chapterStart, verseStart);
            }
        };

        var verseEndChange = function(ev) {
            var form = $(this).closest('form');
            var book = getBook(form);
            var chapterStart = getChapterStart(form);
            var verseStart = getVerseStart(form);
            var verseEnd = getVerseEnd(form);
            setQuickFind(form, book, chapterStart, verseStart, verseEnd);
        };


        var getBook = function(form) {
            return form.find('select[name=book]').val();
        };

        var getChapterStart = function(form) {
            return getSelectNumber(form, 'select[name=chapter_start]');
        };

        var getVerseStart = function(form) {
            return getSelectNumber(form, 'select[name=verse_start]');
        };

        var getVerseEnd = function(form) {
            return getSelectNumber(form, 'select[name=verse_end]');
        };

        var getSelectNumber = function(form, selector) {
            var num = form.find(selector).val();
            if (num == '') {
                return null;
            } else {
                return parseInt(num, 10)
            }
        };


        var fillNumberSelect = function(select, numbers) {
            select.children().remove();
            if (numbers.length > 0) {
                select.append('<option value="">-</option>');
                for (var i = 0; i < numbers.length; i++) {
                    var n = numbers[i].toString()
                    select.append('<option value="' + n + '">' + n + '</option>');
                }
            }
        };

        var setChapterStartSelect = function(form, chapters) {
            fillNumberSelect(form.find('select[name=chapter_start]'), chapters);
            setVerseStartSelect(form, []);
        };

        var setVerseStartSelect = function(form, verses) {
            fillNumberSelect(form.find('select[name=verse_start]'), verses);
            setVerseEndSelect(form, []);
        };

        var setVerseEndSelect = function(form, verses) {
            fillNumberSelect(form.find('select[name=verse_end]'), verses);
        };

        var setQuickFind = function(form, book, chapterStart, verseStart, verseEnd) {
            var text = book + " ";
            if (chapterStart != undefined) {
                text = text + chapterStart.toString();
            }
            if (verseStart != undefined) {
                text = text + ":" + verseStart.toString();
            }
            if (verseEnd != undefined) {
                text = text + "-" + verseEnd.toString();
            }
            form.find('input[name=quick_find]').val(text);
        };

        var setupQuickFindControls = function() {
            $('form.quickfind select[name=book]').change(bookChange);
            $('form.quickfind select[name=chapter_start]').change(chapterStartChange);
            $('form.quickfind select[name=verse_start]').change(verseStartChange);
            $('form.quickfind select[name=verse_end]').change(verseEndChange);
        };

        // Exports:
        learnscripture.setupQuickFindControls = setupQuickFindControls;

        return learnscripture;

    })(learnscripture || {}, $);

$(document).ready(function() {
    learnscripture.setupQuickFindControls();
});
