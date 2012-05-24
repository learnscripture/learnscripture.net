var learnscripture = (function (learnscripture, $) {
    "use strict";

    var setOpenBtnState = function () {
        if (!$('#id_public').attr('checked')) {
            $('#id_open').removeAttr('checked').attr('disabled', 'disabled');
        } else {
            $('#id_open').removeAttr('disabled');
        }
    }

    var setupGroupControls = function () {
        setOpenBtnState();
        var publicBtn = $('#id_public');
        publicBtn.bind('change', setOpenBtnState);
        if (publicBtn.attr('checked')) {
            publicBtn.attr('disabled', 'disabled');
        }
    };

    // Exports:
    learnscripture.setupGroupControls = setupGroupControls;

    return learnscripture;
}(learnscripture || {}, $));

$(document).ready(function () {
    if ($('#id-form-edit-group').length > 0) {
        learnscripture.setupGroupControls();
    }
});
