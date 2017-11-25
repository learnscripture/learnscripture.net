"use strict";
import $ from 'jquery';

var setOpenBtnState = function () {
    if (!$('#id_public').prop('checked')) {
        $('#id_open').prop('checked', false).prop('disabled', true);
    } else {
        $('#id_open').prop('disabled', false);
    }
}

var setupGroupControls = function () {
    setOpenBtnState();
    var publicBtn = $('#id_public');
    publicBtn.bind('change', setOpenBtnState);
    if (publicBtn.prop('checked')) {
        publicBtn.prop('disabled', true);
    }
};

$(document).ready(function () {
    if ($('#id-form-edit-group').length > 0) {
        setupGroupControls();
    }
});
