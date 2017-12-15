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
            "isTouchDevice": isTouchDevice()
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

        if (typingBox.className != expectedClass) {
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
            typingBox.style.height = (rect.height - 2 * 2).toString() + "px";
            // Allow for border and left padding
            typingBox.style.width = (rect.width - 2 * 2 - 4).toString() + "px";
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
