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



app.ports.updateTypingBox.subscribe(function (args) {
    // Move the typing box to cover the word we are testing. This is much easier
    // than trying to get it to fit in the same space without disrupting the
    // layout at all. Doing this in Elm is really hard, so we do it in Javascript.
    // In addition, we need to handle it appearing and disappearing, and not appearing
    // before it has been put in the correct position.

    // Also note that this subscribe function can get called before Elm has
    // updated the actual DOM, so handling this correctly is tricky.
    var typingBoxId = args[0];
    var wordButtonId = args[1];
    var expectedClass = args[2];
    var hardMode = args[3];

    var attempts = 0;
    var fixTypingBox = function () {
        if (attempts > 10) {
            return; // give up
        }

        var tryAgain = function () {
            attempts += 1;
            callFixTypingBox(attempts * 10);
        }

        var typingBox = document.getElementById(typingBoxId);
        if (typingBox === null) {
            tryAgain();
            return;
        }

        var wordButton = wordButtonId == "" ? null : document.getElementById(wordButtonId);

        if (wordButtonId != "" && wordButtonId == null) {
            tryAgain();
            return;
        }

        var classes = typingBox.className.trim().split(/ /);
        if (classes.indexOf(expectedClass) < 0) {
            // We have been called before the DOM was updated.
            tryAgain();
            return;
        }

        if (expectedClass == "toshow") {
            // Fix size/position first, then make it visible.
            var rect = wordButton.getClientRects()[0];
            typingBox.style.top = rect.top.toString() + "px";
            typingBox.style.left = rect.left.toString() + "px";
            // Allow for border
            var styles = window.getComputedStyle(typingBox);
            var parsePx = function (p) {
                return parseInt(p.replace("px", ""), 10);
            }
            var borderWidth = parsePx(styles['border-left-width']);
            typingBox.style.height = (rect.height - 2 * borderWidth).toString() + "px";

            if (hardMode) {
                typingBox.style.width = "6em";
            } else {
                // Allow for border and left padding
                var paddingLeft = parsePx(styles['padding-left']);
                var paddingRight = parsePx(styles['padding-right']);
                typingBox.style.width = (rect.width - 2 * borderWidth - paddingLeft - paddingRight).toString() + "px";
            }
            typingBox.style.display = "inline";
            typingBox.focus();
        } else if (expectedClass == "tohide") {
            typingBox.blur();
            typingBox.style.display = "none";
        }
    };

    var callFixTypingBox = function (delay) {
        window.setTimeout(fixTypingBox, delay)
    }

    callFixTypingBox(1);

});

// Listen for changes to preferences. This signal is sent when the user changes
// preferences via the form (see preferences.ts), and we need to tell Elm about
// it.
$('#id-preferences-data').bind('preferencesSet', function(ev, prefs) {
    app.ports.receivePreferences.send(prefs);
});
