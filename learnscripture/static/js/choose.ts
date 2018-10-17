import { quickFindAndHandleResults } from './quickfind';
import { setupNeedsPreferencesControls } from './preferences';
import { ajaxFailed } from './common';

var loadResults = function(results) {
    $('#id-quick-find-form .validation-error').remove();
    var d = $('.quickfind_search_results');
    d.html(results['html'])
    setupNeedsPreferencesControls(d);
};

var setupChooseControls = function() {
    $('#id_lookup').click(quickFindAndHandleResults(loadResults, false, "choose-individual"));

    $('#id-choose-individual').on('click', 'form.individual-choose input[name=add_to_queue]', function(ev) {
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
                var $btn = $form.find('input[name=add_to_queue]');
                $btn.val($btn.attr('data-added-caption')).prop('disabled', 'true');
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
