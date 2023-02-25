

// TODO setupNeedspreferencescontrols should be applied to quick find results

var setupChooseControls = function() {
    $('#id-choose-verseset').bind('accordion:expanded', function(ev) {
        // We want to not get in the way of mobile users who just want to browse
        // the list, rather than search. So we use setTimeout here because
        // on Firefox for Android at least, it means that the keyboard doesn't
        // get raised.
        window.setTimeout(function() {
            $('#id_query').focus();
        }, 0);
    });

    $('#id-choose-individual').bind('accordion:expanded', function(ev) {
        $('#id_quick_find').focus();
    });

    $('#id-choose-create-set-menu').bind('accordion:expanded', function(ev) {
        $(ev.target).find('.btn.primary')[0].focus();
    });


};

$(document).ready(function() {
    if ($('body.choose-page').length > 0) {
        setupChooseControls();
    }
});
