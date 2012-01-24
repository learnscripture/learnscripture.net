// Learning and testing functionality for learnscripture.net

var learnscripture =
    (function(pub, $) {
         // Controls
         var inputBox = null;

         // -- Constants and globals --
         var WORD_TOGGLE_SHOW = 0;
         var WORD_TOGGLE_HIDE_END = 1;
         var WORD_TOGGLE_HIDE_ALL = 2;
         var TESTING_MAX_ATTEMPTS = 3;

         // Initial state
         var stage = 'read';

         // tracking of words is done using a list
         // of integers, where the value is the index
         // into the div of the word.
         var wordList = null;
         var untestedWords = null;
         var testedWords = null;

         var testMode = false;
         var testingMistakes = {};

         // word toggling and selection

         var moveSelection = function(word) {
             $('.word.selected').removeClass('selected');
             word.addClass('selected');
         };

         var getSelectedWordIndex = function() {
             return $('.word').index($('.word.selected'));
         };

         var getWordCount = function() {
             return $('.word').length;
         };

         var getWordAt = function(index) {
             return $($('.word').get(index));
         };

         var getWordNumber = function(word) {
             return $('.word').index(word);
         };

         var moveSelectionRelative = function(distance) {
             var i = getSelectedWordIndex();
             var pos = Math.min(Math.max(0, i + distance),
                                getWordCount() - 1);
             var word = getWordAt(pos);
             if (word.length != 0) {
                 moveSelection(word);
             }
         };

         var isHidden = function(word) {
             return word.css('opacity') == '0';
         };

         var hideWord = function(word) {
             word.animate({'opacity': '0'}, 300);
         };

         var showWord = function(word) {
             word.animate({'opacity': '1'}, 300);
         };

         var toggleWord = function(word) {
             moveSelection(word);
             var wordNumber = getWordNumber(word);

             var wordEnd = word.find('.wordend');
             var wordStart = word.find('.wordstart');
             var toggleMode = stages[stage].toggleMode;
             if (toggleMode == WORD_TOGGLE_SHOW) {
                 return;
             } else if (toggleMode == WORD_TOGGLE_HIDE_END) {
                 if (isHidden(wordEnd)) {
                     markRevealed(wordNumber);
                     showWord(wordEnd);
                 } else {
                     hideWord(wordEnd);
                 }
             } else if (toggleMode == WORD_TOGGLE_HIDE_ALL) {
                 if (isHidden(wordStart)) {
                     markRevealed(wordNumber);
                     showWord(wordStart);
                 } else if (isHidden(wordEnd)) {
                     markRevealed(wordNumber);
                     showWord(wordEnd);
                 } else {
                     hideWord(wordStart);
                     hideWord(wordEnd);
                 }
             }
         };

         var flashMsg = function(elements) {
             elements.css({opacity:1}).animate({opacity: 0},
                                               {duration: 1000, queue: false});
         };

         var indicateSuccess = function() {
             var word = getWordAt(getSelectedWordIndex());
             word.addClass('correct');
             flashMsg($('#id-testing-status').attr({'class': 'correct'}).text("Correct!"));
         };

         var indicateMistake = function(mistakes, maxMistakes) {
             var msg = "Try again! (" + mistakes.toString() + " out of " + maxMistakes.toString() + ")";
             flashMsg($('#id-testing-status').attr({'class': 'incorrect'}).text(msg));
         };

         var indicateFail = function() {
             var word = getWordAt(getSelectedWordIndex());
             word.addClass('incorrect');
             flashMsg($('#id-testing-status').attr({'class': 'incorrect'}).text("Incorrect"));
         };

         var stripPunctuation = function(str) {
             return str.replace(/[\.,;!?:\/#!$%\^&\*{}=\-_`~()]/g,"");
         };

         var matchWord = function(target, typed) {
             typed = stripPunctuation(typed);
             if (typed == "") return false;
             // for 1 letter words, don't allow any mistakes
             if (target.length == 1) {
                 return typed == target;
             }
             // After that, allow N/3 mistakes, rounded up.
             return levenshteinDistance(target, typed) <= Math.ceil(target.length / 3);
         };

         var checkCurrentWord = function() {
             var wordIdx = getSelectedWordIndex();
             var word = getWordAt(wordIdx);
             var wordStr = stripPunctuation(word.text().toLowerCase());
             var typed = inputBox.val().toLowerCase();
             var moveOn = function() {
                 showWord(word.find('*'));
                 inputBox.val('');
                 moveSelectionRelative(1);
                 setProgress(stage, wordIdx / wordList.length);
             };
             if (matchWord(wordStr, typed)) {
                 indicateSuccess();
                 moveOn();
             } else {
                 testingMistakes[wordIdx] += 1;
                 if (testingMistakes[wordIdx] == TESTING_MAX_ATTEMPTS) {
                     indicateFail();
                     moveOn();
                 } else {
                     indicateMistake(testingMistakes[wordIdx], TESTING_MAX_ATTEMPTS);
                 }
             }
         };

         // ---- Stages ----

         // -- reading stage --
         var readStage = function() {
             showWord($('.word *'));
             testMode = false;
         };

         // recall type 1 - FullAndInitial
         //    Some full words, some initial letters only

         var makeFullAndInitialContinue = function(initialFraction) {
             // Factory function that generates a function for
             // FullAndInitial stage continue function

             var recallContinue = function() {
                 if (untestedWords.length == 0) {
                     return false;
                 }
                 setProgress(stage, testedWords.length / wordList.length);
                 moveSelection($('.word').first());
                 var testWords = getTestWords(initialFraction);
                 showWord($('.word *'));
                 hideWord(testWords.find('.wordend'));
                 return true;
             };

             return recallContinue;
         };

         // recall type 2 - InitialAndMissing
         //    Some initial words, some missing

         var makeInitialAndMissingContinue = function(missingFraction) {
             // Factory function that generates a function for
             // InitialAndMissing stage continue function

             var recallContinue = function() {
                 if (untestedWords.length == 0) {
                     return false;
                 }
                 setProgress(stage, testedWords.length / wordList.length);
                 moveSelection($('.word').first());
                 var testWords = getTestWords(missingFraction);
                 hideWord($('.wordend'));
                 showWord($('.wordstart'));
                 hideWord(testWords.find('.wordstart'));
                 return true;
             };

             return recallContinue;
         };

         var makeRecallStart = function(continueFunc) {
             // Factory function that returns a stage starter
             // function for recall stages
             return function() {
                 testMode = false;
                 untestedWords = wordList.slice(0);
                 testedWords = [];
                 continueFunc();
             };

         };

         // Testing stages

         var resetTestingMistakes = function() {
             for (var i = 0; i < wordList.length; i++) {
                 testingMistakes[i] = 0;
             }
         };

         var testFullStart = function() {
             hideWord($('.word span'));
             resetTestingMistakes();
             testMode = true;
         };

         var testFullContinue = function() {
             return true;
         };

         // Utilities for stages
         var setProgress = function(stage, fraction) {
             $('#id-progress-row-' + stage + ' progress').val(fraction * 100);
         };

         var markRevealed = function(wordNumber) {
             var p = testedWords.indexOf(wordNumber);
             if (p != -1) {
                 testedWords.splice(p, 1);
             }
             if (untestedWords.indexOf(wordNumber) == -1) {
                 untestedWords.push(wordNumber);
             }
         };

         var chooseN = function(aList, n) {
             aList = aList.slice(0);
             var i;
             var chosen = [];
             for(i = 0; i < n; i++) {
                 if (aList.length == 0) {
                     break;
                 }
                 var pos = Math.floor(Math.random()*aList.length);
                 var item = aList[pos];
                 aList.splice(pos, 1);
                 chosen.push(item);
             }
             return chosen;
         };

         var setUnion = function(list1, list2) {
             var output = list1.slice(0);
             for (var i = 0; i < list2.length; i++) {
                 var item = list2[i];
                 if (output.indexOf(item) == -1) {
                     output.push(item);
                 }
             }
             return output;
         };

         var setRemove = function(list1, list2) {
             // Return a new list which is a copy of list1 with the items
             // of list2 removed
             var output = list1.slice(0);
             for (var i = 0; i < list2.length; i++) {
                 var p = output.indexOf(list2[i]);
                 if (p != -1) {
                     output.splice(p, 1);
                 }
             }
             return output;
         };

         var getTestWords = function(testFraction) {
             // Moves testFraction fraction of words from
             // untestedWords for next test, for the next test
             // and return a jQuery objects for the words
             // that are to be tested.
             // Pick some words to test from untestedWords
             var i;
             var toTest = [];
             var testCount = Math.ceil(wordList.length * testFraction);
             // Try to test the ones in untestedWords first.
             toTest = chooseN(untestedWords, testCount);
             if (toTest.length < testCount) {
                 // But if these are fewer than the fraction we are
                 // supposed to be testing, use others that
                 // have already been tested.
                 var reTest = chooseN(testedWords, testCount - toTest.length);
                 toTest = setUnion(reTest, toTest);
             }
             untestedWords = setRemove(untestedWords, toTest);
             // NB this must come after the chooseN(testedWords) above.
             testedWords = setUnion(testedWords, toTest);
             var selector = $.map(toTest, function(elem, idx) {
                                      return '.word:eq(' + elem.toString() + ')';
                                      }).join(', ');
             return $(selector);
         };

         var setStageState = function() {
             // Common clearing, and stage specific setup
             $('#id-verse .correct, #id-verse .incorrect').removeClass('correct').removeClass('incorrect');
             var stageInfo = stages[stage];
             stageInfo.setup();
             enableBtn($('#id-next-btn'), stageInfo.next != null);
             enableBtn($('#id-back-btn'), stageInfo.previous != null);
             // Fade out old instructions, fade in the new
             $('#id-instructions div').animate(
                 {opacity: 0},
                 {duration: 150,
                  complete: function() {
                      $('#id-instructions div').hide();
                      $('#id-instructions .instructions-' + stage).show().animate({opacity: 1}, 150); }});
             // reset selected word
             moveSelection($('.word').first());
             inputBox.val('').focus();

             // Create progress bar for this stage.
             var progressRowId = 'id-progress-row-' + stage;
             if (!document.getElementById(progressRowId)) {
                 var progressRow = (
                     '<tr id="id-progress-row-' + stage + '">' +
                     '<th>' + stageInfo.caption + '</th>' +
                     '<td><progress value="0" max="100">0%</progress>' +
                     '</td></tr>');
                 $('.progress table').prepend(progressRow);

             }
             setProgress(stage, 0);
             $('th.currenttask').removeClass('currenttask');
             $('#' + progressRowId + ' th').addClass('currenttask');
         };

         // -- Moving between stages --

         var next = function(ev) {
             inputBox.val('').focus();
             var thisStage = stages[stage];
             if (thisStage.continueStage()) {
                 return;
             }
             var nextStage = thisStage.next;
             if (nextStage == null) {
                 return;
             }
             setProgress(stage, 1);
             stage = nextStage;
             setStageState();
         };

         var back = function(ev) {
             inputBox.val('').focus();
             var thisStage = stages[stage];
             var previousStage = thisStage.previous;
             if (previousStage == null) {
                 return;
             }
             $('#id-progress-row-' + stage).remove();
             stage = previousStage;
             setStageState();
         };

         var enableBtn = function(btn, state) {
             if (state) {
                 btn.removeAttr('disabled');
             } else {
                 btn.attr('disabled', 'disabled');
             }
         };

         // -- event handlers --

         var keypress = function(ev) {
             if (ev.ctrlKey && ev.which == 37) {
                 ev.preventDefault();
                 back();
                 return;
             }
             if (ev.ctrlKey && ev.which == 39) {
                 ev.preventDefault();
                 next();
                 return;
             }
             if (ev.which == 27) {
                 ev.preventDefault();
                 inputBox.val('');
                 return;
             }
             if (ev.which == 13) {
                 ev.preventDefault();
                 toggleWord($('.word.selected'));
                 return;
             }
             if (!testMode) {
                 if (ev.which == 37) {
                     ev.preventDefault();
                     moveSelectionRelative(-1);
                     return;
                 }
                 if (ev.which == 39) {
                     ev.preventDefault();
                     moveSelectionRelative(1);
                     return;
                 }
                 if (ev.which == 38) {
                     ev.preventDefault();
                     moveSelectionRelative(-1000);
                     return;
                 }
                 if (ev.which == 40) {
                     ev.preventDefault();
                     moveSelectionRelative(1000);
                     return;
                 }
             }
             if (ev.which == 32) {
                 ev.preventDefault();
                 if (testMode) {
                     checkCurrentWord();
                 } else {
                     moveSelectionRelative(1);
                 }
             }

         };

         // Stages definition

         // Full and initial
         var recall1Continue = makeFullAndInitialContinue(0.33);
         var recall1Start = makeRecallStart(recall1Continue);

         var recall2Continue = makeFullAndInitialContinue(0.66);
         var recall2Start = makeRecallStart(recall2Continue);

         var recall3Continue = makeFullAndInitialContinue(1);
         var recall3Start = makeRecallStart(recall3Continue);

         // initial and missing
         var recall4Continue = makeInitialAndMissingContinue(0.33);
         var recall4Start = makeRecallStart(recall4Continue);

         var recall5Continue = makeInitialAndMissingContinue(0.66);
         var recall5Start = makeRecallStart(recall5Continue);

         var recall6Continue = makeInitialAndMissingContinue(1);
         var recall6Start = makeRecallStart(recall6Continue);


         var stages = {'read':    {setup: readStage,
                                   continueStage: function() { return false; },
                                   next: 'recall1',
                                   previous:  null,
                                   caption: 'Read',
                                   toggleMode: WORD_TOGGLE_SHOW},
                       'recall1': {setup: recall1Start,
                                   continueStage: recall1Continue,
                                   next: 'recall2',
                                   previous: 'read',
                                   caption: 'Recall 1 - 33% initial',
                                   toggleMode: WORD_TOGGLE_HIDE_END},
                       'recall2': {setup: recall2Start,
                                   continueStage: recall2Continue,
                                   next: 'recall3',
                                   previous: 'recall1',
                                   caption: 'Recall 2 - 66% initial',
                                   toggleMode: WORD_TOGGLE_HIDE_END},
                       'recall3': {setup: recall3Start,
                                   continueStage: recall3Continue,
                                   next: 'recall4',
                                   previous: 'recall2',
                                   caption: 'Recall 3 - 100% initial',
                                   toggleMode: WORD_TOGGLE_HIDE_END},
                       'recall4': {setup: recall4Start,
                                   continueStage: recall4Continue,
                                   next: 'recall5',
                                   previous: 'recall3',
                                   caption: 'Recall 4 - 33% missing',
                                   toggleMode: WORD_TOGGLE_HIDE_ALL},
                       'recall5': {setup: recall5Start,
                                   continueStage: recall5Continue,
                                   next: 'recall6',
                                   previous: 'recall4',
                                   caption: 'Recall 5 - 66% missing',
                                   toggleMode: WORD_TOGGLE_HIDE_ALL},
                       'recall6': {setup: recall6Start,
                                   continueStage: recall6Continue,
                                   next: 'testFull',
                                   previous: 'recall5',
                                   caption: 'Recall 6 - 100% missing',
                                   toggleMode: WORD_TOGGLE_HIDE_ALL},
                       'testFull': {setup: testFullStart,
                                    continueStage: testFullContinue,
                                    next: null,
                                    previous: 'recall6',
                                    caption: 'Full test',
                                    toggleMode: null}
                       };


         // setup and wiring

         var start = function() {
             inputBox = $('#id-typing');
             $('#id-next-btn').show().click(next);
             $('#id-back-btn').show().click(back);
             inputBox.keydown(keypress);
             setStageState();

             loadVerse();
         };

         var loadVerse = function() {
             $.ajax({url: '/api/learnscripture/v1/nextverse/?format=json',
                     dataType: 'json',
                     success: function(data) {
                         $('#id-verse-title').text(data.verse_reference);
                         // convert newlines to divs
                         var text = data.verse_text + '\n' + data.verse_reference;
                         $.each(text.split(/\n/), function(idx, line) {
                                    if (line.trim() != '') {
                                        $('#id-verse').append('<div class="line">' +
                                                             line + '</div>');
                                    }
                                });
                         markupVerse();

                         $('#id-loading').hide();
                         $('#id-controls').show();
                     }});
         };

         var markupVerse = function() {
             var wordGroups = [];

             $('#id-verse .line').each(function(idx, elem) {
                                                   wordGroups.push($(elem).text().trim().split(/ |\n/));
                                           });
             wordList = [];
             var replacement = [];
             var wordNumber = 0;
             for(var i = 0; i < wordGroups.length; i++) {
                 var group = wordGroups[i];
                 $.each(group, function(j, word) {
                            wordList.push(wordNumber);
                            wordNumber++;
                        });
                 var replace = $.map(group, function(word, j) {
                                         var start = word.slice(0,1);
                                         var end = word.slice(1);
                                         return ('<span class=\"word\">' +
                                                 '<span class="wordstart">' + start +
                                                 '</span><span class="wordend">' + end +
                                                 '</span></span>');
                                         }).join(' ');
                 replacement.push(replace);
             }
             $('#id-verse').html(replacement.join('<br/>'));
             $('.word').click(function(ev) {
                 if (!testMode) {
                     toggleWord($(this));
                 }
                 inputBox.focus();
             });
         };

         pub.start = start;
         return pub;

})(learnscripture || {}, $);



/*

Copyright (c) 2006. All Rights reserved.
If you use this script, please email me and let me know, thanks!

Andrew Hedges
andrew (at) hedges (dot) name

If you want to hire me to write JavaScript for you, see my resume.
http://andrew.hedges.name/resume/

*/

// calculate the Levenshtein distance between a and b
var levenshteinDistance = function(a, b) {
    var cost;

    var m = a.length;
    var n = b.length;

    // make sure a.length >= b.length to use O(min(n,m)) space, whatever that is
    if (m < n) {
        var c=a;a=b;b=c;
        var o=m;m=n;n=o;
    }

    var r = new Array();
    r[0] = new Array();
    for (var c = 0; c < n+1; c++) {
        r[0][c] = c;
    }

    for (var i = 1; i < m+1; i++) {
        r[i] = new Array();
        r[i][0] = i;
        for (var j = 1; j < n+1; j++) {
            cost = (a.charAt(i-1) == b.charAt(j-1))? 0: 1;
            r[i][j] = min3(r[i-1][j]+1,r[i][j-1]+1,r[i-1][j-1]+cost);
        }
    }

    return r[m][n];
};

// return the smallest of the three values passed in
var min3 = function(x,y,z) {
	if (x < y && x < z) return x;
	if (y < x && y < z) return y;
	return z;
};


$(document).ready(function() {
    learnscripture.start();
});



