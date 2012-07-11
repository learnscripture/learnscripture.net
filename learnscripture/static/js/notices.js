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
            $.ajax({url: '/api/learnscripture/v1/deletenotice/?format=json',
                    dataType: 'json',
                    type: 'POST',
                    data: {'id': id}
                   });
        });

        // Turn broadcast data into links:
        $('.notice .broadcast').prepend("&nbsp;&nbsp; Tell people: ");
        $('.notice .broadcast .facebook').each(function (index, elem) {
            var j = $(elem);
            var d = j.data();
            var loc = document.location;
            var urlStart = loc.protocol + '//' + loc.host;
            var redirectUri = loc.toString();
            var caption = "I just earned badge " + d['awardName'];
            var fbUrl = 'http://www.facebook.com/dialog/feed?app_id=175882602545382' +
                '&link=' + encodeURIComponent(urlStart + d['fbLink']) +
                '&redirect_uri=' + encodeURIComponent(redirectUri) +
                '&caption=' + encodeURIComponent(caption) +
                '&picture=' + encodeURIComponent(urlStart + d['fbPicture']);
            var html = '<a href="' + fbUrl + '">Facebook</a>';
            j.html(html);
        });

    };

    // Exports:
    learnscripture.setupNoticesControls = setupNoticesControls;


    return learnscripture;

}(learnscripture || {}, $));

$(document).ready(function () {
    learnscripture.setupNoticesControls();
});
