import { quickFindAndHandleResults } from './quickfind';
import { setupNeedsPreferencesControls } from './preferences';
import { ajaxFailed } from './common';

var loadResults = function(results) {
    $('#id-quick-find-form .validation-error').remove();
    var d = $('.quickfind_search_results');
    d.html(results['html'])
    setupNeedsPreferencesControls(d);
};

var loadMoreResults = function(results) {
    var d = $('.quickfind_search_results .more-results-container');
    d.html(results['html'])
    setupNeedsPreferencesControls(d);
    // d might contain a further '.more-results-container'
    // which should be the target of the next 'show more',
    // rather than d itself.
    d.children().unwrap();
}

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

    var $quickFindForm = $('#id-choose-individual form.quickfind');
    $('#id_lookup').click(quickFindAndHandleResults(loadResults, false, "choose-individual", $quickFindForm, false));
    $('.quickfind_search_results').on(
        'click', 'a[data-quick-find-show-more]',
        quickFindAndHandleResults(loadMoreResults, false, "choose-individual", $quickFindForm, true))

    $('#id-choose-individual').on('click', 'form.individual-choose [name=add_to_queue]', function(ev) {
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
                var $btn = $form.find('[name=add_to_queue]');
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
