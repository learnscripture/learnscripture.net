
$(document).ready(function() {
    $('.accordion-heading').bind('click', function(e) {

        var $heading = $(this);
        var $accordion = $heading.closest('.accordion-container');
        var $item = $heading.closest('.accordion-item');

        if ($item.hasClass('expanded')) {
            $item.removeClass('expanded');
        } else {
            $accordion
                .find('.accordion-item').removeClass('expanded')

            $item.addClass('expanded');
        }
    });
});
