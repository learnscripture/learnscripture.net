var learnscripture =
    (function(learnscripture, $) {

        var setupPreferencesControls = function() {
            $('#id_interface_theme').change(function(ev) {
                $('body').attr('class', $(this).val());
            });
        }

        // Public interface:
        learnscripture.setupPreferencesControls = setupPreferencesControls;

        return learnscripture;
    })(learnscripture || {}, $);

$(document).ready(function() {
    if ($('#id_default_bible_version').length > 0) {
        learnscripture.setupPreferencesControls();
    }
});
