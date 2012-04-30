var learnscripture = (function (learnscripture, $) {
    "use strict";

    var setupNoticesControls = function () {
        $('.notice a.close').click(function(ev) {
            ev.preventDefault();
            var a = $(this);
            var n = a.closest('div.notice');
            n.animate({height: '0px', opacity: '0'},
                      function() {
                          var msgdiv = n.closest('.message-container');
                          if (msgdiv.find('div.notice').length == 1) {
                              // Must be the only notice
                              msgdiv.remove();
                          } else {
                              n.remove();
                          }
                      });
            var id = this.attributes['data-notice-id'].value;
            $.ajax({url: '/api/learnscripture/v1/deletenotice/',
                    dataType: 'json',
                    type: 'POST',
                    data: {'id': id}
                   });
        });

    };

    // Exports:
    learnscripture.setupNoticesControls = setupNoticesControls;


    return learnscripture;

}(learnscripture || {}, $));

$(document).ready(function () {
    learnscripture.setupNoticesControls();
});
