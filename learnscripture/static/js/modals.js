
// Functionality for all modals

$(document).ready(function() {
    // Modal forms:
    // * shouldn't submit when user presses Enter
    // * should click the 'primary' button if they press Enter on last input
    $("div.modal form input[type=\"text\"], " +
      "div.modal form input[type=\"password\"]").keypress(function (ev) {
          if ((ev.which && ev.which == 13) || (ev.keyCode && ev.keyCode == 13)) {
              // Stop IE from submitting:
              ev.preventDefault();

              // Last input in list should cause submit
              var input = $(ev.target);
              var form = input.closest('form');
              var lastInput = form.find('input[type="text"],input[type="password"]').last();
              if (input.attr('id') == lastInput.attr('id')) {
                  form.closest('.modal').find('.btn.default').first().click();
              }
          }
      });
    $('div.modal').bind('shown', function(ev) {
        var modal = $(this);
        // if we have a small screen, then .modal divs are set to have
        // 'position:absolute' instead of 'position:fixed' (using CSS media
        // queries), so that they can scroll.  But this means the modal can be
        // at the top of the screen, where it can't be seen if we are way down
        // the screen.  We move the modal, being careful not to move it off
        // bottom of screen.
        if (modal.css('position') == 'absolute') {
            var bestScrollTop;
            var modalMargin = 10;  // allow 10px margin top and bottom, see CSS
            var modalHeight = modal.height() + modalMargin * 2;
            if ($(window).height() > modalHeight) {
                // we have enough room for the whole modal
                bestScrollTop = $(window).scrollTop();
            } else {
                // not enough room for modal, so be careful not to put it so
                // that it would stick off the bottom of the page.
                bestScrollTop = Math.min($(window).scrollTop(),
                                         $(document).height() - modalHeight);
            }
            if (modal.position().top != bestScrollTop) {
                modal.css('top', (bestScrollTop + modalMargin).toString() + "px")
            }
        }


        // For narrow screens, use 'form-stacked'
        if (modal.width() < 500) {
            modal.find('form').addClass('form-stacked');
        }

    }).bind('hidden', function(ev) {
        var modal = $(this);
        // Remove any 'top' set above (for the case where browser window gets
        // resized and we switch between absolute and fixed positioning for the
        // modal).
        modal.css('top', '');

        // Remove the 'form-stacked' we added.
        modal.find('form').removeClass('form-stacked');
    });

});

