var learnscripture =
    (function(pub, $) {
         // -- Constants and globals --
         var WORD_TOGGLE_SHOW = 0;
         var WORD_TOGGLE_HIDE_END = 1;
         var WORD_TOGGLE_HIDE_ALL = 2;

         var stage = 'read';
         var wordList = null; // list of integers
         var untestedWords = null;
         var testedWords = null;

         // word toggling and selection

         var moveSelection = function(word) {
             $('.word.selected').removeClass('selected');
             word.addClass('selected');
         };

         var moveSelectionRelative = function(distance) {
             var i = $('.word').index($('.word.selected'));
             var pos = Math.min(Math.max(0, i + distance),
                                $('.word').length - 1);
             var word = $('.word').get(pos);
             if (word != null) {
                 moveSelection($(word));
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
             var wordNumber = $('.word').index(word);

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


         // ---- Stages ----

         // -- reading stage --
         var readStage = function() {
             showWord($('.wordstart, .wordend'));
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
                 showWord($('.wordstart, .wordend'));
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
                 untestedWords = wordList.slice(0);
                 testedWords = [];
                 continueFunc();
             };

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
             var testCount = Math.floor(wordList.length * testFraction);
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

         var setStageState = function() { var stageInfo = stages[stage];
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
             $('#id-typing').val('').focus();

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
             var stageInfo = stages[stage];
             stageInfo.setup();
             setStageState();
         };

         var back = function(ev) {
             var thisStage = stages[stage];
             var previousStage = thisStage.previous;
             if (previousStage == null) {
                 return;
             }
             $('#id-progress-row-' + stage).remove();
             stage = previousStage;
             var stageInfo = stages[stage];
             stageInfo.setup();
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
                 $('#id-typing').val('');
                 return;
             }
             if (ev.which == 13) {
                 ev.preventDefault();
                 toggleWord($('.word.selected'));
                 return;
             }
             if (ev.which == 37) {
                 ev.preventDefault();
                 moveSelectionRelative(-1);
                 return;
             }
             if (ev.which == 39 || ev.which == 32) {
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
         };

         // Stages definition

         // Full and initial
         var recall1Continue = makeFullAndInitialContinue(0.25);
         var recall1Start = makeRecallStart(recall1Continue);

         var recall2Continue = makeFullAndInitialContinue(0.5);
         var recall2Start = makeRecallStart(recall2Continue);

         var recall3Continue = makeFullAndInitialContinue(0.75);
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
                                   caption: 'Recall 1 - 25% initial',
                                   toggleMode: WORD_TOGGLE_HIDE_END},
                       'recall2': {setup: recall2Start,
                                   continueStage: recall2Continue,
                                   next: 'recall3',
                                   previous: 'recall1',
                                   caption: 'Recall 2 - 50% initial',
                                   toggleMode: WORD_TOGGLE_HIDE_END},
                       'recall3': {setup: recall3Start,
                                   continueStage: recall3Continue,
                                   next: 'recall4',
                                   previous: 'recall2',
                                   caption: 'Recall 3 - 75% initial',
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
                                   next: null,
                                   previous: 'recall5',
                                   caption: 'Recall 6 - 100% missing',
                                   toggleMode: WORD_TOGGLE_HIDE_ALL}
                       };


         // setup and wiring

         var start = function() {
             markupVerse();
             $('#id-next-btn').show().click(next);
             $('#id-back-btn').show().click(back);
             $('#id-typing').keydown(keypress);
             setStageState();
         };

         var markupVerse = function() {
             var wordGroups = [];

             $('#verse .line').each(function(idx, elem) {
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
             $('#verse').html(replacement.join('<br/>'));
             $('.word').click(function(ev) {
                 toggleWord($(this));
                 $('#id-typing').focus();
             });
         };

         pub.start = start;
         return pub;

})(learnscripture || {}, $);


$(document).ready(function() {
    learnscripture.start();
});


