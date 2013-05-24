var learnscripture =
    (function (learnscripture, $) {
        "use strict";


        var setupCommentControls = function () {
            $('a.icon-comment').bind('click', function (ev) {
                var div = $(this).closest('.activityitem');
                $('#id-add-comment').appendTo(div).show();
            })

            $('#id-add-comment-btn').bind('click', function(ev) {
                // Find event id
                var div = $(this).closest('.activityitem');
                var eventId = div.data().eventId;
                $.ajax({url: '/api/learnscripture/v1/addcomment/?format=json',
                        dataType: 'json',
                        type: 'POST',
                        data: {
                            'event_id': eventId,
                            'message': $('#id-comment-box').val(),
                        },
                        success: function (data) {
                            // data contains new comment to add.
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
