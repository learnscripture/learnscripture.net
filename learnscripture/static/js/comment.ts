import autosize = require('autosize');
import { ajaxFailed, displaySimpleAjaxError } from './common';


var setupCommentControls = function() {

    var showAddComment = function(div) {
        var $commentBlock = div.find('.commentblock').show();
        if ($commentBlock.find(".comment-box").length > 0) {
            return; // We've already got one
        }
        var $locator = $commentBlock.find('.commentboxlocator');

        $locator.append($('#id-add-comment').html());

        var $commentBoxDiv = $locator.find('.comment-box-wrapper');
        var $commentBox = $locator.find('.comment-box');

        autosize($commentBox);
        $commentBox.focus();

        bindPostCommentClick($locator, $commentBoxDiv, $commentBox);

        $locator.find('.cancel-comment-btn').bind('click', function(ev) {
            ev.preventDefault();
            $commentBoxDiv.remove();
        });
    }

    var bindPostCommentClick = function($locator, $commentBoxDiv, $commentBox) {
        var postCommentClick = function(ev) {
            ev.preventDefault();
            var data = {};
            var $commentListDiv = null;

            // Find event id
            var activityDiv = $(ev.target).closest('.activityitem');
            if (activityDiv.length > 0) {
                data['event_id'] = activityDiv.attr("data-event-id");
                $commentListDiv = activityDiv.find('.commentblock')
            }
            // or group id
            var groupDiv = $(ev.target).closest('.groupcomments');
            if (groupDiv.length > 0) {
                data['group_id'] = groupDiv.attr("data-group-id");
                $commentListDiv = groupDiv.find('.commentblock')
            }

            data['message'] = $commentBox.val();

            var position = $commentListDiv.attr("data-new-comments-position")

            $.ajax({
                url: '/api/learnscripture/v1/addcomment/?format=json',
                dataType: 'json',
                type: 'POST',
                data: data,
                success: function(returnedData) {
                    // returnedData contains new comment to add.
                    var newItem = returnedData['html'];
                    $commentBoxDiv.remove();
                    if (position == 'top') {
                        $commentListDiv.prepend(newItem);
                        $locator.prependTo($locator.parent());
                    } else {
                        $commentListDiv.append(newItem);
                        $locator.appendTo($locator.parent());
                    }

                },
                error: function(jqXHR, textStatus, errorThrown) {
                    setTimeout(bindPostCommentClick, 500, $commentBoxDiv);
                    if (jqXHR.status.toString()[0] == "4") {
                        alert(displaySimpleAjaxError(jqXHR));
                    } else {
                        return ajaxFailed(jqXHR, textStatus, errorThrown);
                    }
                }
            });
        };
        $commentBoxDiv.find('.add-comment-btn').on('click', postCommentClick);
    }

    if ($('.activityitem').length == 1) {
        showAddComment($('.activityitem'));
    }

    $('body').on('click', 'a.show-add-comment', function(ev) {
        ev.preventDefault();
        var div = $(this).closest('.activityitem,.groupcomments');
        showAddComment(div);
    })

    $('body').on('click', '.moderate-comment', function(ev) {
        ev.preventDefault();
        if (window.confirm("Remove this comment?")) {
            var commentDiv = $(this).closest('.comment');
            var commentId = commentDiv.data().commentId;
            $.ajax({
                url: '/api/learnscripture/v1/hidecomment/?format=json',
                dataType: 'json',
                type: 'POST',
                data: {
                    'comment_id': commentId,
                },
                success: function(data) {
                    commentDiv.remove();
                },
                error: ajaxFailed
            });
        }
    });

};

$(document).ready(function() {
    setupCommentControls();
});
