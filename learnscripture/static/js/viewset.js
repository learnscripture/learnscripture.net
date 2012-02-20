// Javascript for the view-set page

$(document).ready(function() {
    // TODO - better way to locate the 'verse-set' pages that mustn't clash with
    // 'learn' page.
    if (document.location.pathname.match(/\/verse-set/) != null) {
        $('#id-version-select').change(function(ev) {
            $(ev.target).closest('form').submit();
        });
    }
});

