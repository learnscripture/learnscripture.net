// node_modules libs
import { UAParser } from 'ua-parser-js';

// Ours
import './preferences';
import { isTouchDevice } from './common';
import { doBeep, setUpAudio } from './sound';
import { getSavedCalls, storeSavedCalls } from './offlineutils';


import Elm from "../elm/Learn.elm";

if ($('body.learn-page').length > 0) {
    var preferencesNode = document.getElementById('id-preferences-data');
    var accountNode = document.getElementById('id-account-data');
    var accountName = accountNode == null ? "" : accountNode.attributes['data-username'].value;
    var savedCalls = getSavedCalls(accountName);

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
                "interfaceLanguage": preferencesNode.attributes['data-interface-language'].value,
                },
                "autoSavedPreferences": {
                    // These preferences are not manually set in the 'preferences' dialog,
                    // and therefore not part of the data sent in the receivePreferences subscription.
                    // It is then easiest to separate them out completely.
                    "pinActionLogMenuLargeScreen" : preferencesNode.attributes['data-pin-action-log-menu-large-screen'].value == "true",
                    "pinActionLogMenuSmallScreen" : preferencesNode.attributes['data-pin-action-log-menu-small-screen'].value == "true",
                    "pinVerseOptionsMenuLargeScreen" : preferencesNode.attributes['data-pin-verse-options-menu-large-screen'].value == "true",
                    "seenHelpTour": preferencesNode.attributes['data-seen-help-tour'].value == "true"
                },
                "account": accountNode == null ? null : {
                    "username": accountNode.attributes['data-username'].value,
                },
                "isTouchDevice": isTouchDevice(),
                "csrfMiddlewareToken": document.querySelector("[name=csrfmiddlewaretoken]").value,
                "windowSize": {
                    "width": $(window).width(),
                    "height": $(window).height()
                },
                "savedCalls": savedCalls
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
        if (attempts > 100) {
            return; // give up
        }

        var tryAgain = function () {
            window.requestAnimationFrame(function () {
                fixTypingBox(attempts + 1, args)
            })
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
                    typingBox.style.width = "7em";
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

    function getBrowserEngine() {
        var parser = new UAParser();
        return parser.getEngine().name;
    }

    app.ports.helpTourHighlightElement.subscribe(function (args) {
        var highlightSelector = args[0];
        var positionSelector = args[1];

        window.scrollTo(0, 0);
        $("#id-help-tour-highlight").remove();
        var animationDelay = 10;
        if (highlightSelector.indexOf(".menu-open") != -1) {
            animationDelay = 700; // allow time for opening animation
        }
        var highlightAnimation = function ($item) {
            var itemRect = $item.get(0).getBoundingClientRect();
            var itemCenter = {
                top: itemRect.top + itemRect.height / 2,
                left: itemRect.left + itemRect.width / 2
            };
            var shapeToElementRatio = 1;
            var shapeSize = {
                width: itemRect.width * shapeToElementRatio,
                height: itemRect.height * shapeToElementRatio
            };
            // SVG document is larger than shape, to give
            // room for the stroke of the shape.
            var svgDocToShapeRatio = 1.5;
            var svgDocSize = {
                width: shapeSize.width * svgDocToShapeRatio,
                height: shapeSize.height * svgDocToShapeRatio
            };
            var svgDocPosition = {
                top: itemCenter.top - svgDocSize.height / 2,
                left: itemCenter.left - svgDocSize.width / 2
            };
            var center = {
                x: svgDocSize.width / 2,
                y: svgDocSize.height / 2
            }
            var svgDoc =
                `<svg id="id-help-tour-highlight"
                xmlns="http://www.w3.org/2000/svg"
                xmlns:xlink="http://www.w3.org/1999/xlink"
                width="${svgDocSize.width}"
                height="${svgDocSize.height}"
                viewBox="0 0 ${svgDocSize.width} ${svgDocSize.height}"
                >
               <path d="M ${- shapeSize.width / 2 + center.x} ${0 + center.y}
                        L ${- shapeSize.width / 2 + center.x} ${- shapeSize.height / 4 + center.y}
                        Q ${- shapeSize.width / 2 + center.x} ${- shapeSize.height / 2 + center.y}
                          ${- shapeSize.width / 4 + center.x} ${- shapeSize.height / 2 + center.y}
                        L ${+ shapeSize.width / 4 + center.x} ${- shapeSize.height / 2 + center.y}
                        Q ${+ shapeSize.width / 2 + center.x} ${- shapeSize.height / 2 + center.y}
                          ${+ shapeSize.width / 2 + center.x} ${- shapeSize.height / 4 + center.y}
                        L ${+ shapeSize.width / 2 + center.x} ${+ shapeSize.height / 4 + center.y}
                        Q ${+ shapeSize.width / 2 + center.x} ${+ shapeSize.height / 2 + center.y}
                          ${+ shapeSize.width / 4 + center.x} ${+ shapeSize.height / 2 + center.y}
                        L ${- shapeSize.width / 4 + center.x} ${+ shapeSize.height / 2 + center.y}
                        Q ${- shapeSize.width / 2 + center.x} ${+ shapeSize.height / 2 + center.y}
                          ${- shapeSize.width / 2 + center.x} ${+ shapeSize.height / 4 + center.y}
                        L ${- shapeSize.width / 2 + center.x} ${0 + center.y}
                        "
                   fill="transparent"
                   stroke-width="2px">
             </svg>`;

            var $svgElem = $(svgDoc)
                .css({'top': asPx(svgDocPosition.top),
                      'left': asPx(svgDocPosition.left)});
            $("#id-help-tour-highlight").remove();
            $('body').append($svgElem);
            var $path = $('#id-help-tour-highlight path');
            var length = $path.get(0).getTotalLength();
            var engine = getBrowserEngine();
            if (engine == 'EdgeHTML' || engine == 'Trident') {
                // Edge (probably IE too) seems unable to animate stroke-dashoffset,
                // so the entire thing disappears. Therefore we disable the
                // animation by not setting 'stroke-dasharray'
            } else {
                $path.css({'stroke-dasharray': length.toString()+","+length.toString(),
                           'stroke-dashoffset': length.toString()})
            }
        }

        var adjustMessageBox = function($item) {
            var itemRect = $item.get(0).getBoundingClientRect();
            var helpMessage = $('#id-help-tour-message');
            var wrapper = $('#id-help-tour-wrapper');
            var helpMessageRect = helpMessage.get(0).getBoundingClientRect();
            var docWidth = $(document).width();
            var newMessageLeft = Math.min(itemRect.left,
                                          docWidth - helpMessageRect.width
                                         )
            if (wrapper.hasClass('help-tour-below')) {
                helpMessage.css({
                    'top': asPx(itemRect.top + itemRect.height + 20),
                    'left': asPx(newMessageLeft),
                    'bottom': 'auto'
                });
            }
        };

        window.requestAnimationFrame(function() {
            if (highlightSelector != "") {
                whenVisible(highlightSelector, 100, function($item) {
                    if (animationDelay > 0) {
                        window.setTimeout(highlightAnimation, animationDelay, $item);
                    } else {
                        highlightAnimation($item);
                    }
                })
            }
            if (positionSelector != "") {
                whenVisible(positionSelector, 100, function($item) {
                    if (animationDelay > 0) {
                        window.setTimeout(adjustMessageBox, animationDelay, $item);
                    } else {
                        adjustMessageBox($item);
                    }
                })
            }
        });

    });

    function whenVisible(selector, maxAttempts, action) {
        var $item = $(selector);
        if ($item.length > 0 && $item.is(":visible")) {
            action($item);
        } else {
            window.requestAnimationFrame(function() {
                whenVisible(selector, maxAttempts - 1, 0, action)
            });
        }
    }

    app.ports.saveCallsToLocalStorage.subscribe(function (args) {
        storeSavedCalls(args[0], args[1]);
    });
}
