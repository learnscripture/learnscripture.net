var learnscripture =
    (function(learnscripture, $) {

        var setupSubscribeControls = function() {
            $('#id_currency_list input').click(function(ev) {
                var currency = $(ev.target).val();
                $('#id_prices_list input').each(function(idx, elem) {
                    var i = $(elem);
                    if (i.attr('id').match('^id_price_' + currency + '_') == null) {
                        i.closest('li').hide()
                    } else {
                        i.closest('li').show();
                    }
                });

            });

        };

        // === Exports ===

        learnscripture.setupSubscribeControls = setupSubscribeControls;
        return learnscripture;

    })(learnscripture || {}, $);

$(document).ready(function() {
    learnscripture.setupSubscribeControls();
});
