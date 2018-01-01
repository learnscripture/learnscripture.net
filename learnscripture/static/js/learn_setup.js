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

    var attempts = 0;

    var callFixTypingBox = function (delay,
                                     typingBoxId, wordButtonId, expectedClass, hardMode) {
        window.setTimeout(function () {
            fixTypingBox(typingBoxId, wordButtonId, expectedClass, hardMode)
        }, delay)
    };

    var fixTypingBox = function (typingBoxId, wordButtonId, expectedClass, hardMode) {
        if (attempts > 10) {
            return; // give up
        }

        var tryAgain = function () {
            attempts += 1;
            callFixTypingBox(attempts * 10, typingBoxId, wordButtonId, expectedClass, hardMode);
        }

        var typingBox = document.getElementById(typingBoxId);
        if (typingBox === null) {
            if (expectedClass == "tohide") {
                // Don't need to hide something that doesn't exist yet, and the
                // typing box is hidden by default.
                return;
            } else {
                tryAgain();
                return;
            }
        }

        var wordButton = wordButtonId == "" ? null : document.getElementById(wordButtonId);

        // Have we been called before the DOM was updated?
        var classes = typingBox.className.trim().split(/ /);
        var domUpdated = classes.indexOf(expectedClass) >= 0;

        // We really need to wait for the DOM to be updated before
        // we move/show/focus the typing box, especially when it first appears
        // (otherwise, `wordButton` won't exist in the DOM, and we won't
        // know where to move the typing box to).
        //
        // However, we want the `.focus()` call to cause onscreen keyboard to
        // automatically appear. This only works if we do this operation
        // directly within an event handler, not via a `setTimeout` call (at
        // least with Firefox for Android).
        //
        // So, we have to show and focus the box even before the DOM is updated
        // in some cases, and then run this routine again (using setTimeout) to
        // move the typing box into the right place.

        if (expectedClass == "toshow") {
            // Fix size/position first, then make it visible.

            var correctPositioningComplete = false;
            if (wordButton != null) {
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
                correctPositioningComplete = true;
            } else {
                insertCss("body.learn-page #id-typing { " +
                          "   top: 0px;" +
                          "   left: 0px;" +
                          "}");
            }
            insertCss("body.learn-page #id-typing { " +
                      "   display: inline-block;" +
                      "}")
            typingBox.focus();

            if (!correctPositioningComplete || !domUpdated) {
                tryAgain();
                return;
            }
        } else if (expectedClass == "tohide") {
            typingBox.blur();
            insertCss("body.learn-page #id-typing { " +
                      "   display: none;" +
                      "}")
        }
    };

    // insertCss - changes need to be done perhaps via CSS rules to avoid
    // modifying the DOM before Elm has. (TODO - really?)
    var insertCss = function (code) {
        var style = document.createElement('style');
        style.type = 'text/css';

        if (style.styleSheet) {
            // IE
            style.styleSheet.cssText = code;
        } else {
            // Other browsers
            style.innerHTML = code;
        }
        document.getElementsByTagName("head")[0].appendChild(style);
    };


    fixTypingBox(args[0], args[1], args[2], args[3]);

});

// Listen for changes to preferences. This signal is sent when the user changes
// preferences via the form (see preferences.ts), and we need to tell Elm about
// it.
$('#id-preferences-data').bind('preferencesSet', function(ev, prefs) {
    app.ports.receivePreferences.send(prefs);
});
