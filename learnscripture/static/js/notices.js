var learnscripture = (function (learnscripture, $) {
    "use strict";

    var setupNoticesControls = function () {
        $('.notice a').click(function(ev) {
            var n = $(this);
            n.closest('div.notice').
                animate({height: '0px', opacity: '0'},
                        function() { $(this).remove(); });
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
