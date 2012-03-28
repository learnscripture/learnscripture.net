var learnscripture =
    (function(learnscripture, $) {

        var setupSubscribeControls = function() {
            $('#id_currency_list input').change(function(ev) {
                var currency = $(ev.target).val();
                $('.price-form').hide();
                $('#id_prices_list input').each(function(idx, elem) {
                    var i = $(elem);
                    i.removeAttr('checked');
                    if (i.attr('id').match('^id_price_' + currency + '_') == null) {
                        i.closest('li').hide()
                    } else {
                        i.closest('li').show();
                        i.closest('div.clearfix').show();
                    }
                });
            });
            $('#id_prices_list input').change(function(ev) {
                var id = ev.target.id.replace("id_price_", "");
                $('.price-form').hide();
                $('#id_price_form_' + id).show()
            });

        };

        // === Exports ===

        learnscripture.setupSubscribeControls = setupSubscribeControls;
        return learnscripture;

    })(learnscripture || {}, $);

$(document).ready(function() {
    learnscripture.setupSubscribeControls();
});
