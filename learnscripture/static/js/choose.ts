import { quickFindAndHandleResults } from './quickfind';
import { setupNeedsPreferencesControls } from './preferences';
import { ajaxFailed } from './common';

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
        setupNeedsPreferencesControls(d);
    } else {
        d.html("<p><span class='error'>No verses were found matching your search</span></p>");
    }
};

var setupChooseControls = function() {
    $('#id_lookup').click(quickFindAndHandleResults(loadResults, false));

    $('#id-tab-individual').on('click', 'form.individual-choose input[name=add_to_queue]', function(ev) {
        ev.preventDefault();
        var $form = $(ev.currentTarget).parent('form');
        var localized_reference = $form.find('input[name=localized_reference]').val();
        var version_slug = $form.find('input[name=version_slug]').val();
        console.log(localized_reference, version_slug);
        $.ajax({
            url: '/api/learnscripture/v1/addversetoqueue/?format=json',
            dataType: 'json',
            type: 'POST',
            data: {
                localized_reference: localized_reference,
                version_slug: version_slug
            },
            success: function() {
                $form.find('input[name=add_to_queue]').val('Added!').prop('disabled', 'true');
            },
            error: ajaxFailed
        });
    });
};

$(document).ready(function() {
    if ($('body.choose-page').length > 0) {
        setupChooseControls();
    }
});
