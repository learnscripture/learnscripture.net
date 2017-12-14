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
    var typingBoxId = args[0];
    var wordButtonId = args[1];

    var attempts = 0
    var fixTypingBox = function () {
        if (attempts > 10) {
            return; // give up
        }
        var typingBox = document.getElementById(typingBoxId);
        var wordButton = document.getElementById(wordButtonId);
        if (typingBox === null || wordButton === null) {
            attempts += 1;
            callFixTypingBox();
        } else {
            if (typingBox.style.display == 'none') {
                return;
            }
            typingBox.focus();
            var rect = wordButton.getClientRects()[0];

            typingBox.style.top = rect.top.toString() + "px";
            typingBox.style.left = rect.left.toString() + "px";
            // Allow for border
            typingBox.style.height = (rect.height - 2 * 2).toString() + "px";
            // Allow for border and left padding
            typingBox.style.width = (rect.width - 2 * 2 - 4).toString() + "px";
        }
    };

    var callFixTypingBox = function () {
        window.setTimeout(fixTypingBox, 1)
    }

    callFixTypingBox();

});
