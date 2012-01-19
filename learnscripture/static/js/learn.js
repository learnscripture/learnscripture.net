var learnscripture =
    (function(pub, $) {
         var WORD_TOGGLE_SHOW = 0;
         var WORD_TOGGLE_HIDE_END = 1;
         var WORD_TOGGLE_HIDE_ALL = 2;

         var markupverse = function() {
             var words = $('#verse').text().split(/ |\n/);
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
             var wordEnd = word.find('.wordend');
             var wordStart = word.find('.wordstart');
             var toggleMode = stages[stage].toggleMode;
             if (toggleMode == WORD_TOGGLE_SHOW) {
                 return;
             } else if (toggleMode == WORD_TOGGLE_HIDE_END) {
                 if (isHidden(wordEnd)) {
                     showWord(wordEnd);
                 } else {
                     hideWord(wordEnd);
                 }
             } else if (toggleMode == WORD_TOGGLE_HIDE_ALL) {
                 if (isHidden(wordStart)) {
                     showWord(wordStart);
                 } else if (isHidden(wordEnd)) {
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

         var testedWords = [];

         var recall1Stage = function() {
             hideWord($('.wordend'));
             showWord($('.wordstart'));
         };

         var recall2Stage = function() {
             hideWord($('.wordstart, .wordend'));
         };

         var stage = 'read';

         // stages: {name: [setupFunc, next stage, previous stage, word toggle mode]
         //
         var stages = {'read':    {setup: readStage,
                                   next: 'recall1',
                                   previous:  null,
                                   toggleMode: WORD_TOGGLE_SHOW},
                       'recall1': {setup: recall1Stage,
                                   next: 'recall2',
                                   previous: 'read',
                                   toggleMode: WORD_TOGGLE_HIDE_END},
                       'recall2': {setup: recall2Stage,
                                   next: null,
                                   previous: 'recall1',
                                   toggleMode: WORD_TOGGLE_HIDE_ALL}
                       };

         var revealClicks = 0;

         var enableBtn = function(btn, state) {
             if (state) {
                 btn.removeAttr('disabled');
             } else {
                 btn.attr('disabled', 'disabled');
             }
         };

         var setStageState = function() {
             var stageInfo = stages[stage];
             enableBtn($('#id-next-btn'), stageInfo.next != null);
             enableBtn($('#id-back-btn'), stageInfo.previous != null);
             $('#id-instructions div').animate({opacity: 0}, {duration: 300, complete: function() {
                 $('#id-instructions div').hide();
                 $('#id-instructions .instructions-' + stage).show().animate({opacity: 1}, 300);
             }});
             moveSelection($('.word').first());
             $('#id-typing').val('').focus();
         };

         var next = function(ev) {
             var thisStage = stages[stage];
             stage = thisStage.next;
             var nextStage = stages[stage];
             nextStage.setup();
             setStageState();
         };

         var back = function(ev) {
             var thisStage = stages[stage];
             stage = thisStage.previous;
             var previousStage = stages[stage];
             previousStage.setup();
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
             if (ev.which == 20) {
                 ev.preventDefault();
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
         };

         var start = function() {
             markupverse();
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


