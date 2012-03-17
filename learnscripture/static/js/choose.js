var learnscripture =
    (function(learnscripture, $) {

        var loadResults = function(results) {
            $('#id-quick-find-form .validation-error').remove();
            var d = $('.quickfind_search_results');
            if (results.length > 0) {
                var html = '';
                if (results.length > 10) {
                    html = html + "<p>The first 10 results matching your search are below:</p>";
                }
                html = html + $('#id_individual_choose_result_template').render(results);
                d.html(html);
                learnscripture.setupNeedsPreferencesControls(d);
            } else {
                d.html("<p><span class='error'>No verses were found matching your search</span></p>");
            }
        };

        var setupChooseControls = function() {
            $('#id_lookup').click(learnscripture.quickFindAndHandleResults(loadResults, false));
        };

        // Exports:
        learnscripture.setupChooseControls = setupChooseControls;

        return learnscripture;

    })(learnscripture || {}, $);

$(document).ready(function() {
    if ($('#id-tab-individual').length > 0) {
        learnscripture.setupChooseControls();
    }
});
