"use strict";
var $ = require('jquery');

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

$(document).ready(function () {
    if ($('#id-form-edit-group').length > 0) {
        setupGroupControls();
    }
});
