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
                        $('#id_prices_list_container').show();
                    }
                });
            });
            $('#id_prices_list input').change(function(ev) {
                var id = ev.target.id.replace("id_price_", "");
                $('.price-form').hide();
                $('#id_price_form_' + id).show();
                $('#id_cant_afford_form').toggle(id.match('cant_afford') != null);
            });
        };

        // === Exports ===

        learnscripture.setupSubscribeControls = setupSubscribeControls;
        return learnscripture;

    })(learnscripture || {}, $);

$(document).ready(function() {
    learnscripture.setupSubscribeControls();
});
