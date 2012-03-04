
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
});

