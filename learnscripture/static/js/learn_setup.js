// For the moment, this is separated out from base.js to minimize breakage, but
// will be merged eventually.

// node_modules libs
import 'expose-loader?jQuery!jquery';
import 'jquery.ajaxretry';

// Ours
import './preferences';
import { isTouchDevice } from './common';
import { doBeep, setUpAudio } from './sound';

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


var fixTypingBox = function (attempts, args, afterDomUpdated) {
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


    if (args.expectedClass == "toshow") {
        // Fix size/position first, then make it visible.

        var correctPositioningComplete = false;
        if (wordButton != null) {
            // This always exists if typingBox does:
            var typingBoxContainer = document.getElementById(args.typingBoxContainerId);
            // By doing `position: absolute` on typingBox and `position: relative`
            // on typingBoxContainer, then the position of the typing box doesn't
            // need to be updated if typingBoxContainer itself moves up or down the page
            // e.g. things appearing above it.
            var wordRect = wordButton.getClientRects()[0];
            var containerRect = typingBoxContainer.getClientRects()[0];

            typingBox.style.top = (wordRect.top - containerRect.top).toString() + "px";
            typingBox.style.left = (wordRect.left - containerRect.left).toString() + "px";
            // Allow for border
            var styles = window.getComputedStyle(typingBox);
            var parsePx = function (p) {
                return parseInt(p.replace("px", ""), 10);
            }
            var borderWidth = parsePx(styles['border-left-width']);
            typingBox.style.height = (wordRect.height - 2 * borderWidth).toString() + "px";

            if (args.hardMode) {
                typingBox.style.width = "6em";
            } else {
                // Allow for border and left padding
                var paddingLeft = parsePx(styles['padding-left']);
                var paddingRight = parsePx(styles['padding-right']);
                typingBox.style.width = (wordRect.width - 2 * borderWidth - paddingLeft - paddingRight).toString() + "px";
            }
            correctPositioningComplete = true;
        } else {
            typingBox.style.top = "0px";
            typingBox.style.left = "-1000px";  // hide offscreen until we know correct position.
        }
        typingBox.style.display = "inline-block";
        if (args.refocus) {
            typingBox.focus();
        }

        if (!correctPositioningComplete || !afterDomUpdated) {
            tryAgain();
            return;
        }
    } else if (args.expectedClass == "tohide") {
        if (args.refocus) {
            typingBox.blur();
        }
        typingBox.style.display = 'none';
    }
};


app.ports.updateTypingBox.subscribe(function (args) {
    // Move the typing box to cover the word we are testing. This is much easier
    // than trying to get it to fit in the same space without disrupting the
    // layout at all. Doing this in Elm is really hard, so we do it in
    // Javascript. In addition, we need to handle it appearing and disappearing,
    // and not appearing before it has been put in the correct position.

    fixTypingBox(0, args, false);
});

// Elm's runtime appears to use setTimeout / requestAnimationFrame such that
// doing `focus()` from within it, even via ports, does not cause the on screen
// keyboard to be brought up in Firefox for Android when you press 'Next'
// buttons etc., even though it is possible using Javascript.
//
// See https://github.com/elm-lang/dom/issues/21
//
// So, we have this crazy workaround: for buttons that will should cause the
// typing box to be focuses, in Elm we signal this by putting a
// data-focus-typing-box-required attribute on the button. We also pass other
// required data using data-* attributes on the element. We then do a normal
// event handler which spots the click, and makes the typing box visible and
// focused. The `.focus()` call from this route causes Firefox for Android to
// make the keyboard appear, so that the user doesn't have to manually click it.
//
// Note that in Firefox for Android, the user still has to manually click to
// make the box appear for the first verse in a session, because the typing box
// appears without the user manually clicking on any button, and there doesn't
// seem to be any way to get Firefox to open the keyboard in this case.

$('body.learn-page').on('click', '[data-focus-typing-box-required]', function (ev) {
    var $button = $(ev.currentTarget);
    var args = { typingBoxId: $button.attr("data-focus-typingBoxId"),
                 typingBoxContainerId: $button.attr("data-focus-typingBoxContainerId"),
                 wordButtonId: $button.attr("data-focus-wordButtonId"),
                 expectedClass: $button.attr("data-focus-expectedClass"),
                 hardMode: $button.attr("data-focus-hardMode") == "true",
                 refocus: true,  // This mechanism is only used when refocus is true
               }
    fixTypingBox(0, args, false);

})

// Listen for changes to preferences. This signal is sent when the user changes
// preferences via the form (see preferences.ts), and we need to tell Elm about
// it.
$('#id-preferences-data').bind('preferencesSet', function(ev, prefs) {
    app.ports.receivePreferences.send(prefs);
});

app.ports.vibrateDevice.subscribe(function (length) {
    if (!("vibrate" in navigator)) {
        return;
    }
    navigator.vibrate(length);
});

app.ports.beep.subscribe(function (args) {
    var frequency = args[0],
        length = args[1];
    doBeep(frequency, length);
});

setUpAudio();



app.ports.flashActionLog.subscribe(function (id) {
    function flash(attempts) {
        if (attempts > 4) {
            return;
        }
        var $span = $("#" + id);
        // This function gets called before the DOM is updated, so we check for
        // that and defer until after a DOM update if the node doesn't exist
        // yet.
        if ($span.length == 0) {
            setTimeout(function() {
                flash(attempts + 1)
            }, 10)
            return;
        }
        $span.addClass("flash-action-log");
    }
    flash(0);
});
