var learnscripture = (function (learnscripture, $) {
    "use strict";

    var groupListContent = null;

    var fetchGroupListContent = function () {
        if (groupListContent === null) {
            $.ajax({url: '/group-select-list/?format=json',
                    dataType: 'html',
                    type: 'GET',
                    async: false,
                    success: function(data) {
                        groupListContent = data;
                    }
                   });
        }
        return groupListContent;
    };

    var groupBtnClick = function (ev) {
        var val = $(ev.target).closest('div').find('input').val();
        var q = $.deparam(window.location.search.replace('?', ''));
        q['group'] = val;
        q['p'] = '1';
        window.location = window.location.pathname + '?' + $.param(q);
    };

    var setupLeaderboardControls = function () {
        $('#id-leaderboard-select-group-btn')
            .popover({
                title: function () { return "Select group"; },
                content: fetchGroupListContent,
                trigger: 'manual',
                placement: 'below',
                html: true,
            })
            .toggle(function (ev) {
                $(this).popover('show');
                $('.popover').find('input,label').bind('click', groupBtnClick);
            }, function (ev) {
                $(this).popover('hide');
            });
    };

    // Exports:
    learnscripture.setupLeaderboardControls = setupLeaderboardControls;

    return learnscripture;
}(learnscripture || {}, $));

$(document).ready(function () {
    if ($('#id-leaderboard-select-group-btn').length > 0) {
        learnscripture.setupLeaderboardControls();
    }
});
