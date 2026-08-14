
var setupNoticesControls = function() {

    // Turn broadcast data into links:
    $('.notice .broadcast').each(function(index, elem) {
        var $elem = $(elem);
        var d = $elem.data();
        var loc = document.location;
        var urlStart = loc.protocol + '//' + loc.host;
        var link = urlStart + d['link'];
        link += ((link.indexOf('?') == -1) ? "?" : "&");
        link += "from=" + d['accountUsername'];

        var caption = d['caption'];

        // Twitter
        var twUrl = 'https://twitter.com/share' +
            '?url=' + encodeURIComponent(link) +
            '&text=' + encodeURIComponent(caption) +
            '&hashtags=LearnScripture';

        $elem.find('a[data-twitter-link]').attr('href', twUrl);
    });

};


$(document).ready(function() {
    setupNoticesControls();
});
