var learnscripture =
    (function (learnscripture, $) {
        "use strict";


        var setupCommentControls = function () {
            var showAddComment = function(div) {
                var commentBlock = div.find('.commentblock').show('fast');
                $('#id-add-comment').appendTo(commentBlock).show('fast');
                $('#id-comment-box').focus();
            }

            if ($('.activityitem').length == 1) {
                showAddComment($('.activityitem'));
            }

            $('a.show-add-comment').bind('click', function (ev) {
                ev.preventDefault();
                var div = $(this).closest('.activityitem');
                showAddComment(div);
            })

            var postCommentClick = function(ev) {
                ev.preventDefault();
                // Find event id
                var activityDiv = $(this).closest('.activityitem');
                var eventId = activityDiv.data().eventId;
                $.ajax({url: '/api/learnscripture/v1/addcomment/?format=json',
                        dataType: 'json',
                        type: 'POST',
                        data: {
                            'event_id': eventId,
                            'message': $('#id-comment-box').val(),
                        },
                        success: function (data) {
                            setTimeout(bindPostCommentClick, 500);
                            // data contains new comment to add.
                            activityDiv.find('.commentlist').append(
                                $('#id-comment-template').render({'comment': data})
                            );

                            $('#id-comment-box').val('');
                            $('#id-add-comment').hide();
                        },
                        error: function (jqXHR, textStatus, errorThrown) {
                            setTimeout(bindPostCommentClick, 500);
                            if (jqXHR.status.toString()[0] == "4") {
                                alert(learnscripture.displaySimpleAjaxError(jqXHR));
                            } else {
                                return learnscripture.ajaxFailed(jqXHR, textStatus, errorThrown);
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
                if (window.confirm("Hide this comment?")) {
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
                            error: learnscripture.ajaxFailed
                           });
                }
            });

            $('#id-comment-box').autosize();
        };

        // === Exports ===
        learnscripture.setupCommentControls = setupCommentControls;
        return learnscripture;
    }(learnscripture || {}, $));

$(document).ready(function () {
    learnscripture.setupCommentControls();
});
