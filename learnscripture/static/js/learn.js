var learnscripture =
    (function(pub, $) {
         var markupverse = function() {
             var words = $('.verse').text().split(/ |\n/);
             var replace = $.map(words, function(word, i) {
                                     var start = word.slice(0,1);
                                     var end = word.slice(1);
                                     return ('<span class=\"word\">' +
                                             '<span class="wordstart">' + start +
                                             '</span><span class="wordend">' + end +
                                             '</span></span>');
                                     }).join(' ');
             $('.verse').html(replace);
             $('.word').click(function(ev) {
                 var wordend = $(this).find('.wordend');
                 if (wordend.css('opacity') == '0') {
                     showWordEnd(wordend);
                 } else {
                     hideWordEnd(wordend);
                 }});
         };

         var hideWordEnd = function(wordend) {
             wordend.animate({'opacity': '0'}, 300);
         };

         var hideWordEnds = function(ev) {
             hideWordEnd($('.wordend'));
         };

         var showWordEnd = function(wordend) {
             wordend.animate({'opacity': '1'}, 300);
         };

         var showWordEnds = function(ev) {
             showWordEnd($('.wordend'));
         };

         var stage = 'read';

         var stages = {'read':    ['recall1', hideWordEnds, null,   null],
                       'recall1': [ null,     null,        'read',  showWordEnds]};

         var revealClicks = 0;

         var enableBtn = function(btn, state) {
             if (state) {
                 btn.removeAttr('disabled');
             } else {
                 btn.attr('disabled', 'disabled');
             }
         };

         var setStageState = function() {
             var stageinfo = stages[stage];
             enableBtn($('#id-next-btn'), stageinfo[0] != null);
             enableBtn($('#id-back-btn'), stageinfo[2] != null);
             $('#id-instructions div').animate({opacity: 0}, {duration: 300, complete: function() {
                 $('#id-instructions div').hide();
                 $('#id-instructions .instructions-' + stage).show().animate({opacity: 1}, 300);
             }});
         };

         var next = function(ev) {
             var stageinfo = stages[stage];
             stage = stageinfo[0];
             stageinfo[1]();
             setStageState();
         };

         var back = function(ev) {
             var stageinfo = stages[stage];
             stage = stageinfo[2];
             stageinfo[3]();
             setStageState();
         };

         var start = function() {
             markupverse();
             $('#id-next-btn').show().click(next);
             $('#id-back-btn').show().click(back);
             $('.word').first().addClass('selected');
         };
         pub.start = start;
         return pub;

})(learnscripture || {}, $);


$(document).ready(function() {
    learnscripture.start();
});


