/*jslint browser: true, vars: true, plusplus: true, maxerr: 1000 */
/*globals $, jQuery, alert, confirm */

// Functionality for all modals

$(document).ready(function () {
    // Modal forms:
    // * shouldn't submit when user presses Enter
    // * should click the 'primary' button if they press Enter on last input
    $("div.modal form input[type=\"text\"], " +
      "div.modal form input[type=\"password\"]").keypress(function (ev) {
          if ((ev.which && ev.which === 13) || (ev.keyCode && ev.keyCode === 13)) {
              // Stop IE from submitting:
              ev.preventDefault();

              // Last input in list should cause submit
              var input = $(ev.target);
              var form = input.closest('form');
              var lastInput = form.find('input[type="text"],input[type="password"]').last();
              if (input.attr('id') === lastInput.attr('id')) {
                  form.closest('.modal').find('.btn.default').first().click();
              }
          }
      });
});


var learnscripture = (function (learnscripture, $) {
    "use strict";
    var adjustModal = function (modal) {
        // if we have a small screen, then .modal divs are set to have
        // 'position:absolute' instead of 'position:fixed', so that they can
        // scroll.  But this means the modal can be at the top of the screen,
        // where it can't be seen if we are way down the screen.  We move the
        // modal, being careful not to move it off bottom of screen.

        var bestScrollTop;
        var modalMargin = 10;  // allow 10px margin top and bottom, see CSS
        var modalHeight = modal.height() + modalMargin * 2;

        if (modalHeight > $(window).height()) {
            modal.css({'position': 'absolute',
                       'top': modalMargin.toString() + 'px',
                       'margin-top': '0px'
                      });
            // not enough room for modal, so be careful not to put it so
            // that it would stick off the bottom of the page.
            bestScrollTop = Math.min($(window).scrollTop(),
                                     $(document).height() - modalHeight);

            if (modal.position().top !== bestScrollTop) {
                modal.css('top', (bestScrollTop + modalMargin).toString() + "px");
            }

        } else {
            // we have enough room for the whole modal, so we just
            // center it and make it fixed.
            modal.css({'position': 'fixed',
                       'top': '50%',
                       'margin-top': "-" + (modalHeight / 2).toString() + "px"
                      });
        }
    };

    var adjustVisibleModals = function () {
        $('div.modal:visible').each(function (idx, elem) {
            adjustModal($(elem));
        });
    };

    $('div.modal').bind('shown', function (ev) {
        var modal = $(this);
        adjustModal(modal);
    });


    $(window).bind('resize', function (ev) {
        adjustVisibleModals();
    });

    $(document).ready(adjustAllForms);

    // Export:
    learnscripture.adjustModal = adjustModal;
    return learnscripture;

}(learnscripture || {}, $));
