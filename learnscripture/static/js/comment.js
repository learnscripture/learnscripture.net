var learnscripture =
    (function (learnscripture, $) {
        "use strict";


        var setupCommentControls = function () {
            $('a.show-add-comment').bind('click', function (ev) {
                ev.preventDefault();
                var div = $(this).closest('.activityitem').find('.commentblock').show('fast');
                $('#id-add-comment').appendTo(div).show('fast');
                $('#id-comment-box').focus();
            })

            $('#id-add-comment-btn').bind('click', function(ev) {
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
                            // data contains new comment to add.
                            activityDiv.find('.commentlist').append(
                                $('#id-comment-template').render({'comment': data})
                            );

                            $('#id-comment-box').val('');
                            $('#id-add-comment').hide();
                        },
                        error: function (jqXHR, textStatus, errorThrown) {
                            if (jqXHR.status.toString()[0] == "4") {
                                alert(learnscripture.displaySimpleAjaxError(jqXHR));
                            } else {
                                return learnscripture.ajaxFailed(jqXHR, textStatus, errorThrown);
                            }
                        }
                       });
            });

            $('#id-cancel-comment-btn').bind('click', function (ev) {
                ev.preventDefault();
                $('#id-add-comment').hide();
                $('#id-comment-box').val('');
            });
        };

        // === Exports ===
        learnscripture.setupCommentControls = setupCommentControls;
        return learnscripture;
    }(learnscripture || {}, $));

$(document).ready(function () {
    learnscripture.setupCommentControls();
});
