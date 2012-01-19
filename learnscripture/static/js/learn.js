var learnscripture =
    (function(pub, $) {
         var WORD_TOGGLE_SHOW = 0;
         var WORD_TOGGLE_HIDE_END = 1;
         var WORD_TOGGLE_HIDE_ALL = 2;
         var TEST_FRACTION = 0.2;

         var stage = 'read';
         var wordList = null; // list of integers
         var untestedWords = null;
         var testedWords = null;

         var markupVerse = function() {
             var words = $('#verse').text().split(/ |\n/);
             wordList = $.map(words, function(word, i) {
                                  return i;
                              });
             var replace = $.map(words, function(word, i) {
                                     var start = word.slice(0,1);
                                     var end = word.slice(1);
                                     return ('<span class=\"word\">' +
                                             '<span class="wordstart">' + start +
                                             '</span><span class="wordend">' + end +
                                             '</span></span>');
                                     }).join(' ');
             $('#verse').html(replace);
             $('.word').click(function(ev) {
                 toggleWord($(this));
                 $('#id-typing').focus();
             });
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

         var moveSelection = function(word) {
             $('.word.selected').removeClass('selected');
             word.addClass('selected');
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

         var readStage = function() {
             showWord($('.wordstart, .wordend'));
         };

         var recall1Start = function() {
             untestedWords = wordList.slice(0);
             testedWords = [];
             recall1Continue();
         };

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

         var recall1Continue = function() {
             var i;
             if (untestedWords.length == 0) {
                 return false;
             }

             setProgress(stage, testedWords.length / wordList.length);
             // Pick some words to test from untestedWords
             var toTest = [];
             var candidates = untestedWords.slice(0);
             for (i=0; i < wordList.length * TEST_FRACTION; i++) {
                 if (candidates.length == 0) {
                     break;
                 }
                 var pos = Math.floor(Math.random()*candidates.length);
                 var item = candidates[pos];
                 toTest.push(item);
                 testedWords.push(item);
                 candidates.splice(pos,1);
                 untestedWords.splice(pos,1);
             }
             var selector = $.map(toTest, function(elem, idx) {
                                      return '.word:eq(' + elem.toString() + ')';
                                      }).join(', ');
             showWord($('.wordstart, .wordend'));
             hideWord($(selector).find('.wordend'));
             return true;
         };

         var recall2Start = function() {
             hideWord($('.wordstart, .wordend'));
         };

         var enableBtn = function(btn, state) {
             if (state) {
                 btn.removeAttr('disabled');
             } else {
                 btn.attr('disabled', 'disabled');
             }
         };

         var setStageState = function() { var stageInfo = stages[stage];
             enableBtn($('#id-next-btn'), stageInfo.next != null);
             enableBtn($('#id-back-btn'), stageInfo.previous != null);
             $('#id-instructions div').animate({opacity: 0}, {duration: 150,
             complete: function() { $('#id-instructions div').hide();
             $('#id-instructions .instructions-' +
             stage).show().animate({opacity: 1}, 150); }});
             moveSelection($('.word').first());
             $('#id-typing').val('').focus();
             $('th.currenttask').removeClass('currenttask');
             $('#id-progress-row-' + stage + ' th').addClass('currenttask');
             setProgress(stage, 0);
         };

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
             $('#id-progress-row-' + stage).show(300);
             setStageState();
         };

         var back = function(ev) {
             var thisStage = stages[stage];
             var previousStage = thisStage.previous;
             if (previousStage == null) {
                 return;
             }
             $('#id-progress-row-' + stage).hide();
             stage = previousStage;
             var stageInfo = stages[stage];
             stageInfo.setup();
             setStageState();
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

         var stages = {'read':    {setup: readStage,
                                   continueStage: function() { return false; },
                                   next: 'recall1',
                                   previous:  null,
                                   toggleMode: WORD_TOGGLE_SHOW},
                       'recall1': {setup: recall1Start,
                                   continueStage: recall1Continue,
                                   next: 'recall2',
                                   previous: 'read',
                                   toggleMode: WORD_TOGGLE_HIDE_END},
                       'recall2': {setup: recall2Start,
                                   next: null,
                                   previous: 'recall1',
                                   toggleMode: WORD_TOGGLE_HIDE_ALL}
                       };

         var start = function() {
             markupVerse();
             $('#id-next-btn').show().click(next);
             $('#id-back-btn').show().click(back);
             $('#id-typing').keydown(keypress);
             setStageState();
         };
         pub.start = start;
         return pub;

})(learnscripture || {}, $);


$(document).ready(function() {
    learnscripture.start();
});


