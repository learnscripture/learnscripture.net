// For the moment, this is separated out from base.js to minimize breakage, but
// will be merged eventually.

// node_modules libs
import 'expose-loader?jQuery!jquery';
import 'jquery.ajaxretry';

// Ours
import './preferences';
import { isTouchDevice } from './common';

// CSS/Less
import 'learn.less';

import Elm from "../elm/Learn";
var preferencesNode = document.getElementById('id-preferences-data');
var accountNode = document.getElementById('id-account-data');
var app =
    Elm.Learn.embed(
        document.getElementById('elm-main'),
        {
            "preferences": {
                "preferencesSetup": preferencesNode.attributes['data-preferences-setup'].value == "true",
                "enableAnimations": preferencesNode.attributes['data-enable-animations'].value == "true",
                "enableSounds": preferencesNode.attributes['data-enable-sounds'].value == "true",
                "enableVibration": preferencesNode.attributes['data-enable-vibration'].value == "true",
                "desktopTestingMethod": preferencesNode.attributes['data-desktop-testing-method'].value,
                "touchscreenTestingMethod": preferencesNode.attributes['data-touchscreen-testing-method'].value,
            },
            "account": accountNode == null ? null : {
                "username": accountNode.attributes['data-username'].value,
            },
            "isTouchDevice": isTouchDevice(),
            "csrfMiddlewareToken": document.querySelector("[name=csrfmiddlewaretoken]").value
        });


var fixTypingBox = function (attempts, args) {
    if (attempts > 3) {
        return; // give up
    }

    var tryAgain = function () {
        window.setTimeout(function () {
            fixTypingBox(attempts + 1, args)
        }, 10)
    }

    var typingBox = document.getElementById(args.typingBoxId);
    if (typingBox === null) {
        if (args.expectedClass == "tohide") {
            // Don't need to hide something that doesn't exist yet, and the
            // typing box is hidden by default.
            return;
        } else {
            tryAgain();
            return;
        }
    }

    var wordButton = args.wordButtonId == "" ? null : document.getElementById(args.wordButtonId);

    // Have we been called before the DOM was updated?
    var classes = typingBox.className.trim().split(/ /);
    var domUpdated = classes.indexOf(args.expectedClass) >= 0;

    if (args.expectedClass == "toshow") {
        // Fix size/position first, then make it visible.

        var correctPositioningComplete = false;
        if (wordButton != null) {
            var rect = wordButton.getClientRects()[0];
            var doc = document.documentElement;
            var scrollTop = (window.pageYOffset || doc.scrollTop)
            var scrollLeft = (window.pageXOffset || doc.scrollLeft)

            typingBox.style.top = (rect.top + scrollTop).toString() + "px";
            typingBox.style.left = (rect.left + scrollLeft).toString() + "px";
            // Allow for border
            var styles = window.getComputedStyle(typingBox);
            var parsePx = function (p) {
                return parseInt(p.replace("px", ""), 10);
            }
            var borderWidth = parsePx(styles['border-left-width']);
            typingBox.style.height = (rect.height - 2 * borderWidth).toString() + "px";

            if (args.hardMode) {
                typingBox.style.width = "6em";
            } else {
                // Allow for border and left padding
                var paddingLeft = parsePx(styles['padding-left']);
                var paddingRight = parsePx(styles['padding-right']);
                typingBox.style.width = (rect.width - 2 * borderWidth - paddingLeft - paddingRight).toString() + "px";
            }
            correctPositioningComplete = true;
        } else {
            typingBox.style.top = "0px";
            typingBox.style.left = "0px";
        }
        typingBox.style.display = "inline-block";
        typingBox.focus();

        if (!correctPositioningComplete || !domUpdated) {
            tryAgain();
            return;
        }
    } else if (args.expectedClass == "tohide") {
        typingBox.blur();
        typingBox.style.display = 'none';
    }
};


app.ports.updateTypingBox.subscribe(function (args) {
    // Move the typing box to cover the word we are testing. This is much easier
    // than trying to get it to fit in the same space without disrupting the
    // layout at all. Doing this in Elm is really hard, so we do it in
    // Javascript. In addition, we need to handle it appearing and disappearing,
    // and not appearing before it has been put in the correct position.

    fixTypingBox(0, args);
});

// Elm's runtime appears to use setTimeout / requestAnimationFrame such that
// doing `focus()` from within it, even via ports, does not cause the on screen
// keyboard to be brought up in Firefox for Android when you press 'Next'
// buttons etc., even though it is possible.
//
// See https://github.com/elm-lang/dom/issues/21
//
// So, we have this crazy workaround: for buttons that will cause the typing box
// to appear, and therefore require a focus event, in Elm we signal this using
// data-focus-typing-box-required. We also pass other required data using data-*
// attributes on the element. We then do a normal event handler which spots the
// click, and makes the typing box visible and focused. The `.focus()` call from
// this route causes Firefox for Android to make the keyboard appear, so that
// the user doesn't have to manually click it.
//
// Note that in Firefox for Android, the user still has to manually click to
// make the box appear for the first verse in a session, because the typing box
// appears without the user manually clicking on any button, and there doesn't
// seem to be any way to get Firefox to open the keyboard in this case.

$('body.learn-page').on('click', '[data-focus-typing-box-required]', function (ev) {
    var $button = $(ev.currentTarget);
    var args = { typingBoxId: $button.attr("data-focus-typingBoxId"),
                 wordButtonId: $button.attr("data-focus-wordButtonId"),
                 expectedClass: $button.attr("data-focus-expectedClass"),
                 hardMode: $button.attr("data-focus-hardMode") == "true"
               }
    fixTypingBox(0, args);

})

// Listen for changes to preferences. This signal is sent when the user changes
// preferences via the form (see preferences.ts), and we need to tell Elm about
// it.
$('#id-preferences-data').bind('preferencesSet', function(ev, prefs) {
    app.ports.receivePreferences.send(prefs);
});
