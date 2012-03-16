var learnscripture =
    (function(learnscripture, $) {
        var lookupVerse = function(ev) {
            ev.preventDefault();
            $.ajax({url: '/api/learnscripture/v1/versefind/',
                    dataType: 'json',
                    type: 'GET',
                    data: {
                        'quick_find': $(ev.target).closest('form').find('input[name=quick_find]').val(),
                        'version_slug': $('#id-version-select').val()
                    },
                    success: loadResults,
                    error:  function(jqXHR, textStatus, errorThrown) {
                        if (jqXHR.status == 400) {
                            $('#id_individual_search_results *').remove();
                            learnscripture.handleFormValidationErrors($('#id-verse-find-form'), '', jqXHR);
                        } else {
                            learnscripture.handlerAjaxError(jqXHR, textStatus, errorThrown);
                        }
                    }
                   });
        };

        var loadResults = function(results) {
            $('#id-verse-find-form .validation-error').remove();
            var d = $('#id_individual_search_results');
            if (results.length > 0) {
                var html = '';
                if (results.length > 10) {
                    html = html + "<p>The first 10 results matching your search are below:</p>";
                }
                html = html + $('#id_search_result_template').render(results);
                d.html(html);
                learnscripture.setupNeedsPreferencesControls(d);
            } else {
                d.html("<p><span class='error'>No verses were found matching your search</span></p>");
            }
        };

        var setupChooseControls = function() {
            $('#id_lookup').click(lookupVerse);
        };

        // Exports:
        learnscripture.setupChooseControls = setupChooseControls;

        return learnscripture;

    })(learnscripture || {}, $);

$(document).ready(function() {
    learnscripture.setupChooseControls();
});
