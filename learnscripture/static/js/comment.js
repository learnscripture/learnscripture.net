"use strict";
import $ from 'jquery';
import autosize from 'autosize';
import { ajaxFailed, displaySimpleAjaxError } from './common';


var setupCommentControls = function () {
    var showAddComment = function(div) {
        var commentBlock = div.find('.commentblock').show();
        var locator = commentBlock.find('.commentboxlocator');
        $('#id-add-comment').appendTo(locator).show();
        $('#id-comment-box').focus();
    }

    if ($('.activityitem').length == 1) {
        showAddComment($('.activityitem'));
    }

    $('a.show-add-comment').bind('click', function (ev) {
        ev.preventDefault();
        var div = $(this).closest('.activityitem,.groupcomments');
        showAddComment(div);
    })

    var postCommentClick = function(ev) {
        ev.preventDefault();
        var data = {
            'message': $('#id-comment-box').val(),
        }
        // Find event id
        var commentListDiv = null;
        var activityDiv = $(this).closest('.activityitem');
        if (activityDiv.length > 0) {
            data['event_id'] = activityDiv.data().eventId;
            commentListDiv = activityDiv.find('.commentlist')
        }
        // or group id
        var groupDiv = $(this).closest('.groupcomments');
        if (groupDiv.length > 0) {
            data['group_id'] = groupDiv.data().groupId;
            commentListDiv = groupDiv.find('.commentlist')
        }
        // Get position of comment box relative to comment list
        var position = ($("#id-comment-box").add(commentListDiv).index(commentListDiv) == 0 ?
                        'bottom' : 'top');

        $.ajax({url: '/api/learnscripture/v1/addcomment/?format=json',
                dataType: 'json',
                type: 'POST',
                data: data,
                success: function (data) {
                    setTimeout(bindPostCommentClick, 500);
                    // data contains new comment to add.
                    var newItem = $('#id-comment-template').render({'comment': data});
                    if (position == 'top') {
                        commentListDiv.prepend(newItem);
                    } else {
                        commentListDiv.append(newItem);
                    }

                    $('#id-comment-box').val('');
                    $('#id-add-comment').hide();
                },
                error: function (jqXHR, textStatus, errorThrown) {
                    setTimeout(bindPostCommentClick, 500);
                    if (jqXHR.status.toString()[0] == "4") {
                        alert(displaySimpleAjaxError(jqXHR));
                    } else {
                        return ajaxFailed(jqXHR, textStatus, errorThrown);
                    }
                }
               });
    };

    var bindPostCommentClick = function () {
        $('#id-add-comment-btn').one('click', postCommentClick);
    }
    bindPostCommentClick();

    $('#id-cancel-comment-btn').bind('click', function (ev) {
        ev.preventDefault();
        $('#id-add-comment').hide();
        $('#id-comment-box').val('');
    });

    $('.moderate-comment').bind('click', function (ev) {
        ev.preventDefault();
        if (window.confirm("Remove this comment?")) {
            var commentDiv = $(this).closest('.comment');
            var commentId = commentDiv.data().commentId;
            $.ajax({url: '/api/learnscripture/v1/hidecomment/?format=json',
                    dataType: 'json',
                    type: 'POST',
                    data: {
                        'comment_id': commentId,
                    },
                    success: function (data) {
                        commentDiv.remove();
                    },
                    error: ajaxFailed
                   });
        }
    });

    autosize($('#id-comment-box'));
};

$(document).ready(function () {
    setupCommentControls();
});
