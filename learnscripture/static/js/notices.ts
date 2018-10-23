
var setupNoticesControls = function() {
    $('.notice a.close').click(function(ev) {
        ev.preventDefault();
        var a = $(this);
        var n = a.closest('div.notice');
        n.animate({ height: '0px', opacity: '0' },
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
        $.ajax({
            url: '/api/learnscripture/v1/deletenotice/?format=json',
            dataType: 'json',
            type: 'POST',
            data: { 'id': id }
        });
    });

    // Turn broadcast data into links:
    $('.notice .broadcast').each(function(index, elem) {
        var $elem = $(elem);
        var d = $elem.data();
        var loc = document.location;
        var urlStart = loc.protocol + '//' + loc.host;
        var redirectUri = loc.toString();
        var link = urlStart + d['link'];
        link += ((link.indexOf('?') == -1) ? "?" : "&");
        link += "from=" + d['accountUsername'];

        var caption = d['caption'];

        // Facebook
        var fbUrl = 'https://www.facebook.com/dialog/feed?app_id=175882602545382' +
            '&link=' + encodeURIComponent(link) +
            '&redirect_uri=' + encodeURIComponent(redirectUri) +
            '&caption=' + encodeURIComponent(caption) +
            '&picture=' + encodeURIComponent(urlStart + d['picture']);

        // Twitter
        var twUrl = 'https://twitter.com/share' +
            '?url=' + encodeURIComponent(link) +
            '&text=' + encodeURIComponent(caption) +
            '&hashtags=LearnScripture';

        $elem.find('a[data-facebook-link]').attr('href', fbUrl);
        $elem.find('a[data-twitter-link]').attr('href', twUrl);
    });

};


$(document).ready(function() {
    setupNoticesControls();
});
