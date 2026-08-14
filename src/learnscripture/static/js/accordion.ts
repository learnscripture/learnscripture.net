
$(document).ready(function() {
    $('.accordion-heading').bind('click', function(e) {

        var $heading = $(this);
        var $accordion = $heading.closest('.accordion-container');
        var $item = $heading.closest('.accordion-item');

        if ($item.hasClass('expanded')) {
            $item.removeClass('expanded');
            $item.trigger('accordion:collapsed');
        } else {
            $accordion
                .find('.accordion-item').each(function(idx, elem) {
                    var $elem = $(elem);
                    if ($elem.hasClass('expanded')) {
                        $elem.removeClass('expanded').trigger('accordion-collapsed');
                    }
                });
            $item.addClass('expanded');
            $item.trigger('accordion:expanded');
        }
    });
});
