"use strict";
import $ from 'jquery';
import ajaxFailed from './common';


var setupFollowingControls = function () {
    $('#id-follow-btn').bind('click', function (ev) {
        ev.preventDefault();
        var accountId = $(this).data().accountId;
        $.ajax({url: '/api/learnscripture/v1/follow/?format=json',
                dataType: 'json',
                type: 'POST',
                data: {'account_id': accountId},
                success: function (data) {
                    $('.is-following').show();
                    $('.is-not-following').hide();
                },
                error: common.ajaxFailed
               });
    });
    $('#id-unfollow-btn').bind('click', function (ev) {
        ev.preventDefault();
        var accountId = $(this).data().accountId;
        $.ajax({url: '/api/learnscripture/v1/unfollow/?format=json',
                dataType: 'json',
                type: 'POST',
                data: {'account_id': accountId},
                success: function (data) {
                    $('.is-following').hide();
                    $('.is-not-following').show();
                },
                error: common.ajaxFailed
               });
    });
}

$(document).ready(function () {
    setupFollowingControls();
});
