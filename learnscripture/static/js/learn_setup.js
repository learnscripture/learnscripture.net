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
                "pinActionLogMenuLargeScreen" : preferencesNode.attributes['data-pin-action-log-menu-large-screen'].value == "true",
                "pinActionLogMenuSmallScreen" : preferencesNode.attributes['data-pin-action-log-menu-small-screen'].value == "true",
                "pinVerseOptionsMenuLargeScreen" : preferencesNode.attributes['data-pin-verse-options-menu-large-screen'].value == "true",
            },
            "account": accountNode == null ? null : {
                "username": accountNode.attributes['data-username'].value,
            },
            "isTouchDevice": isTouchDevice(),
            "csrfMiddlewareToken": document.querySelector("[name=csrfmiddlewaretoken]").value
        });


// We want the typing box to be in the same place and be the same size that the
// word would be. To know the width of a piece of text, the only way is to
// measure the width of the DOM element. In addition, we are much less likely to
// disrupt the layout if we simply cover the word with the typing box using
// absolute positioning, rather than putting it inside the verse HTML at the
// right point. So we need to move the typing box into position and adjust its
// size after the layout has been done. This is obviously hard in Elm, so it is
// done using a port. We also need to handle focus (see below).

var parsePx = function (p) {
    return parseInt(p.replace("px", ""), 10);
}

var asPx = function (n) {
    return n.toString() + "px";
}

var fixTypingBox = function (attempts, args) {
    if (attempts > 10) {
        return; // give up
    }

    var tryAgain = function () {
        window.setTimeout(function () {
            fixTypingBox(attempts + 1, args)
        }, 10 + attempts * 20)
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
        // to avoid seeing the previous typed text in next word word position,
        // make sure we blank it before moving/making visible. This does seem to
        // be necessary on some computers e.g. Safari on MacBook.
        if (args.value === "" && typingBox.value !== "") {
            typingBox.value = "";
        }

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
            var typingBoxStyles = window.getComputedStyle(typingBox);
            var wordButtonStyles = window.getComputedStyle(wordButton);

            // typingBox position may need to account for difference in border
            // widths and padding (see .hide-word-boundaries) if we want typed
            // text to line up exactly with underlying word text.
            var typingBoxLeft = wordRect.left - containerRect.left
                - parsePx(typingBoxStyles['border-left-width'])
                + parsePx(wordButtonStyles['border-left-width'])
                - parsePx(typingBoxStyles['padding-left'])
                + parsePx(wordButtonStyles['padding-left']);

            var typingBoxTop = (wordRect.top - containerRect.top);
            typingBox.style.top =  asPx(typingBoxTop)
            typingBox.style.left = asPx(typingBoxLeft)
            var borderWidth = parsePx(typingBoxStyles['border-left-width']);
            typingBox.style.height = asPx(wordRect.height - 2 * borderWidth)

            if (args.hardMode) {
                // Don't give away the word length, which would be a clue.
                typingBox.style.width = "6em";
            } else {
                // Allow for border and left padding
                var paddingLeft = parsePx(typingBoxStyles['padding-left']);
                var paddingRight = parsePx(typingBoxStyles['padding-right']);
                typingBox.style.width = asPx(wordRect.width - 2 * borderWidth - paddingLeft - paddingRight)
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

        if (!correctPositioningComplete) {
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
    fixTypingBox(0, args);
});

// Elm's runtime appears to use setTimeout / requestAnimationFrame such that
// doing `focus()` from within it, even via ports, does not cause the on screen
// keyboard to be brought up in Firefox for Android when you press 'Next'
// buttons etc., even though it is possible using plain Javascript.
//
// See https://github.com/elm-lang/dom/issues/21
//
// So, we have this crazy workaround: for buttons that will cause the typing box
// to be focused, in Elm we signal this by putting a
// data-focus-typing-box-required attribute on the button. We also pass other
// required data using data-* attributes on the element. We then do a normal
// VanillaJS event handler (below) which spots the click, and makes the typing
// box visible and focused. The `.focus()` call from this route causes Firefox
// for Android to make the keyboard appear, so that the user doesn't have to
// manually click it.
//
// Note that in Firefox for Android, the user may still habe to manually click
// to make the box appear for the first verse in a session, because the typing
// box appears without the user manually clicking on any button, and there
// doesn't seem to be any way to get Firefox to open the keyboard in this case.

$('body.learn-page').on('click', '[data-focus-typing-box-required]', function (ev) {
    var $button = $(ev.currentTarget);
    var args = { typingBoxId: $button.attr("data-focus-typingBoxId"),
                 typingBoxContainerId: $button.attr("data-focus-typingBoxContainerId"),
                 wordButtonId: $button.attr("data-focus-wordButtonId"),
                 expectedClass: $button.attr("data-focus-expectedClass"),
                 hardMode: $button.attr("data-focus-hardMode") == "true",
                 refocus: true,  // This mechanism is only used when refocus is true
               }
    fixTypingBox(0, args);

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
