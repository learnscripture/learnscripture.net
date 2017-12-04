/*jslint browser: true, vars: true, plusplus: true, maxerr: 1000 */
/*globals alert, confirm */

// Learning and testing functionality for learnscripture.net

// Refer to learn.html for UI definition.
//
// = Main concepts =
//
// == Stages ==
//
// For a specific verse, there are various stages that might be stepped
// through. Often, the stage list is a single item (e.g. 'test'), but when
// learning it will be set ['read', 'recall1', ....]
//
// The stage list will be set by default on the basis of the current stage of
// the verse in the database. But further actions (e.g. 'More practice') can
// replace it.
//
// Various controls are specific to certain stages. These are controlled
// by giving them a 'stage-specific' class, and then, if they *always*
// appear for their stage, a 'stage-$NAME' class.
//
// showStageControls is responsible for toggling the visibility of these
// controls.
//
// Other controls only appear for certain stages under certain conditions,
// and these are simply marked 'stage-specific' and then made visible
// on an ad-hoc basis by code.
"use strict";

// Imports
import { ajaxRetrySucceeded, ajaxRetryOptions, ajaxRetryFailed, hideLoadingIndicator, indicateLoading, ajaxFailed } from './common';
import { doBeep, setUpAudio } from './sound';
import { getPreferences } from './preferences'
import { getAccountData } from './accounts';


// User prefs
var preferences = null;
var userAccountData = null;
var scoringEnabled = false;

// Controls
var inputBox = null;
var testingStatus = null;

// -- Constants and globals --
var WORD_TOGGLE_SHOW = 0;
var WORD_TOGGLE_HIDE_END = 1;
var WORD_TOGGLE_HIDE_ALL = 2;

var LOADING_QUEUE_BUFFER_SIZE = 3;

var scrollingTimeoutId = null;

// Defined in StageType:
var STAGE_TYPE_TEST = 'TEST';
var STAGE_TYPE_READ = 'READ';

// Defined in TestingMethod:
var TEST_FULL_WORDS = 'FULL_WORDS';
var TEST_FIRST_LETTER = 'FIRST_LETTER';
var TEST_ON_SCREEN = 'ON_SCREEN';

// Defined in VerseSetType
var SET_TYPE_SELECTION = 'SELECTION';
var SET_TYPE_PASSAGE = 'PASSAGE';


// Defined in LearningType:
var LEARNING_TYPE_PRACTICE = 'practice';

// Defined in TextType
var TEXT_TYPE_BIBLE = 'BIBLE';

// Thresholds for different testings modes:
// Strength == 0.6 corresponds to about 10 days learning.
var HARD_MODE_THRESHOLD = 0.6

// Defined in learnscripture.session
var VERSE_STATUS_BATCH_SIZE = 10;

// Initial state
var currentStage = null;
var currentStageIdx = null;
var currentStageList = null;

// tracking of words is done using a list
// of integers, where the value is the index
// into the div of the word.
var wordList = null;
var referenceList = null;

// Globals for recall stages:
var uncheckedWords = null;
var checkedWords = null;

// Globals for testings stages:
var testingMethodStrategy = null;
var testingMistakes = null;
var wordBoundariesHidden = null;
var practiceMode = null;

// Verse list
var versesToLearn = null; // eventually a dictionary of index:verse
var currentVerseIndex = null;
var minVerseIndex = null;
var maxVerseIndex = null;
var moreToLoad = true; // assume true initially.
var currentVerseStatus = null;

// Finish
var redirect_to = '/dashboard/';


// ======== Generic utilities =========

// === Randomising ===

var chooseN = function(aList, n) {
    aList = aList.slice(0);
    var i;
    var chosen = [];
    for (i = 0; i < n; i++) {
        if (aList.length === 0) {
            break;
        }
        var pos = Math.floor(Math.random() * aList.length);
        var item = aList[pos];
        aList.splice(pos, 1);
        chosen.push(item);
    }
    return chosen;
};

// === Sets ===

var setUnion = function(list1, list2) {
    var i, output = list1.slice(0);
    for (i = 0; i < list2.length; i++) {
        var item = list2[i];
        if (output.indexOf(item) === -1) {
            output.push(item);
        }
    }
    return output;
};

var setRemove = function(list1, list2) {
    // Return a new list which is a copy of list1 with the items
    // of list2 removed
    var i, output = list1.slice(0);
    for (i = 0; i < list2.length; i++) {
        var p = output.indexOf(list2[i]);
        if (p !== -1) {
            output.splice(p, 1);
        }
    }
    return output;
};

// === Maths ===

var approximatelyEqual = function(a, b, epsilon) {
    return Math.abs(Math.abs(a) - Math.abs(b)) <= epsilon;
};

// === HTML ===

var enableBtn = function(btn, state) {
    if (state) {
        btn.prop('disabled', false);
    } else {
        btn.prop('disabled', true);
    }
};

function escapeHtml(s) {
    if (!s) {
        return "";
    }
    s = s + "";
    return s.replace(/[\&"<>\\]/g, function(s) {
        switch (s) {
            case "&": return "&amp;";
            case "\\": return "\\\\";
            case '"': return '\"';
            case "<": return "&lt;";
            case ">": return "&gt;";
            default: return s;
        }
    });
}


// ========== Word toggling =============

// For speed in test mode, where we have to keep up with typing,
// we tag all the words with ids, and keep track of the current id
// and word number
var currentWordIndex = null;

var getWordAt = function(index) {
    return $('#id-word-' + index.toString());
};

var getWordNumber = function(word) {
    return $('.current-verse .word').index(word);
};

var isHidden = function(word) {
    return word.css('opacity') === '0';
};

var hideWord = function(word, options?) {
    if (preferences.enableAnimations) {
        if (options === undefined) {
            options = {
                duration: 300,
                queue: false
            };
        }
        word.animate({
            'opacity': '0'
        }, options);
    } else {
        word.css({
            'opacity': '0'
        });
    }
};

var showWord = function(word) {
    if (preferences.enableAnimations) {
        word.animate({
            'opacity': '1'
        }, {
                duration: 300,
                queue: false
            });
    } else {
        word.css({
            'opacity': '1'
        });
    }
};

var toggleWord = function(word) {
    var wordNumber = getWordNumber(word);

    var wordEnd = word.find('.wordend');
    var wordStart = word.find('.wordstart');
    var toggleMode = currentStage.toggleMode;
    if (toggleMode === WORD_TOGGLE_SHOW) {
        return;
    } else if (toggleMode === WORD_TOGGLE_HIDE_END) {
        if (isHidden(wordEnd)) {
            markRevealed(wordNumber);
            showWord(wordEnd);
        }
    } else if (toggleMode === WORD_TOGGLE_HIDE_ALL) {
        if (isHidden(wordStart)) {
            markRevealed(wordNumber);
            showWord(wordStart);
        } else if (isHidden(wordEnd)) {
            markRevealed(wordNumber);
            showWord(wordEnd);
        }
    }
};

// ========== Messages ===========

var flashMsg = function(elements, wordBox) {
    var pos = wordBox.position();
    elements.css({
        'top': (pos.top - elements.outerHeight()).toString() + "px",
        'left': pos.left.toString() + "px"
    }).show();

    if (preferences.enableAnimations) {
        elements.css({
            opacity: 1
        }).animate({
            opacity: 0
        }, {
                duration: 1000,
                queue: false
            });
    } else {
        elements.css({
            opacity: 1
        });
    }
};

var indicateSuccess = function() {
    var word = getWordAt(currentWordIndex);
    word.addClass('correct');
    flashMsg(testingStatus.attr({
        'class': 'correct'
    }).text("Correct!"), word);
};

var beep = function(frequency, length) {
    if (!preferences.enableSounds) {
        return;
    }
    doBeep(frequency, length);
};

var vibrate = function(length) {
    if (!preferences.enableVibration) {
        return;
    }
    if (!("vibrate" in navigator)) {
        return;
    }
    navigator.vibrate(length);
}

var indicateMistake = function(mistakes, maxMistakes) {
    var msg = "Try again! (" + mistakes.toString() + "/" + maxMistakes.toString() + ")";
    flashMsg(testingStatus.attr({
        'class': 'incorrect'
    }).text(msg),
        getWordAt(currentWordIndex));
    beep(330, 0.10);
    vibrate(25);
};

var indicateFail = function() {
    var word = getWordAt(currentWordIndex);
    word.addClass('incorrect');
    flashMsg(testingStatus.attr({
        'class': 'incorrect'
    }).text("Incorrect"), word);
    beep(220, 0.10);
    vibrate(50);
};

// ========== Actions completed =============

var trimVerseStatusDataForPostback = function(verseStatus) {
    // Clone the data:
    var d = JSON.parse(JSON.stringify(verseStatus));
    // Trim stuff we don't need:
    d.scoring_text_words = null;
    d.suggestions = null;
    return d;
};

var readingComplete = function(callbackAfter?) {
    $.ajax({
        url: '/api/learnscripture/v1/actioncomplete/?format=json',
        dataType: 'json',
        type: 'POST',
        data: {
            verse_status: JSON.stringify(trimVerseStatusDataForPostback(currentVerseStatus), null, 2),
            stage: STAGE_TYPE_READ
        },
        success: function() {
            ajaxRetrySucceeded();
            if (callbackAfter !== undefined) {
                callbackAfter();
            }
        },
        retry: ajaxRetryOptions,
        error: ajaxRetryFailed
    });
};

var testableWordCount = function() {
    if (testingMethodStrategy.testReference) {
        return wordList.length;
    } else {
        return wordList.length - referenceList.length;
    }
}

var testComplete = function() {
    testingMethodStrategy.testTearDown();

    var accuracy = 0;
    var mistakes = 0;
    $.each(testingMistakes, function(key, val) {
        mistakes += val;
    });
    accuracy = 1 - (mistakes / testableWordCount());
    accuracy = Math.max(0, accuracy);

    // Do some rounding  to avoid '99.9' and retain 3 s.f.
    accuracy = Math.round(accuracy * 1000) / 1000;

    var wasPracticeMode = isPracticeMode();
    $.ajax({
        url: '/api/learnscripture/v1/actioncomplete/?format=json',
        dataType: 'json',
        type: 'POST',
        data: {
            verse_status: JSON.stringify(trimVerseStatusDataForPostback(currentVerseStatus), null, 2),
            stage: STAGE_TYPE_TEST,
            accuracy: accuracy,
            practice: wasPracticeMode,
        },
        success: function(data) {
            ajaxRetrySucceeded();
            if (!wasPracticeMode) {
                loadStats();
                loadActionLogs();
            }
        },
        retry: ajaxRetryOptions,
        error: ajaxRetryFailed
    });

    var accuracyPercent = Math.floor(accuracy * 100);
    $('#id-accuracy').text(accuracyPercent.toString() + "%");
    var comment =
        accuracyPercent > 98 ? 'awesome!' :
            accuracyPercent > 95 ? 'excellent!' :
                accuracyPercent > 90 ? 'very good.' :
                    accuracyPercent > 80 ? 'good.' :
                        accuracyPercent > 50 ? 'OK.' :
                            accuracyPercent > 30 ? 'could do better!' :
                                "more practice needed!";

    $('#id-result-comment').text(comment);
    fadeVerseTitle(false);
    enableBtn($('#id-hint-btn'), false);

    completeStageGroup();
    showTestFinishedControls();

    if (accuracyPercent < 80) {
        // 'More practice' the default
        $('#id-next-verse-btn').removeClass('primary');
        $('#id-more-practice-btn').addClass('primary');

    } else {
        // 'More practice' available but not default
        $('#id-more-practice-btn').removeClass('primary');
        $('#id-next-verse-btn').addClass('primary');
    }

    $('#id-more-practice-btn').unbind().bind('click', function(ev) {
        if (accuracyPercent < 20) {
            currentStageList = chooseStageListForStrength(0);
        } else if (accuracyPercent < 70) {
            currentStageList = ['read', 'recall2', 'recall4', 'test'];
        } else {
            currentStageList = ['recall2', 'recall4', 'test'];
        }
        setPracticeMode(true);
        setUpStage(0);
    });
    bindDocKeyPress();
};

// =========== Stage handling ==========

var setProgress = function(stageIdx, fraction) {
    var progress = (stageIdx + fraction) / currentStageList.length * 100;
    var bar = $('#id-progress-bar');
    var oldVal = parseInt(bar.val().toString(), 10);
    if (preferences.enableAnimations &&
        !currentStage.testMode &&
        Math.abs(oldVal - progress) > 5 && // animation pointless
        !(oldVal > 99 && progress === 0) // new verse - animation confusing
    ) {
        bar.animate({
            value: progress,
            duration: 'fast'
        });
    } else {
        bar.val(progress);
    }
    bar.html(Math.floor(progress).toString() + "%");
};

var completeStageGroup = function() {
    currentStage = stageDefs['results'];
    currentStageList = [currentStage];
    currentStageIdx = 0;
    enableBtn($('#id-next-btn, #id-back-btn'), false);
};

var setStageControlBtns = function() {
    if (currentStageIdx == 0 && currentStageList.length == 1) {
        $('#id-next-btn, #id-back-btn').hide();
    } else {
        $('#id-next-btn, #id-back-btn').show();
        enableBtn($('#id-next-btn'), currentStageIdx < currentStageList.length - 1);
        enableBtn($('#id-back-btn'), currentStageIdx > 0);
    }
};

var fadeVerseTitle = function(fade) {
    $('#id-verse-title').toggleClass('blurry', fade);
};

var getStageSelector = function(stageName) {
    return '.stage-' + stageName;
}

var showStageControls = function(stageName) {
    var stageSelector = getStageSelector(stageName);
    // Hide everything that is stage specific, except stuff for this
    // stage.
    $('.stage-specific:not(' + stageSelector + ')').hide()
    $(stageSelector).show();
    // Once we've set things up, show the container.
    $('#id-bottom-controls .buttonbar').show();
}

var showTestFinishedControls = function() {
    // We can't just use showStageControls, because we want to leave the
    // instructions div alone, and only affect the id-bottom-controls
    // bit.
    var stageSelector = getStageSelector('test-finished');
    $('#id-bottom-controls .stage-specific:not(' + stageSelector + ')').hide();
    $('#id-bottom-controls ' + stageSelector).show();
};

var setUpStage = function(idx) {
    // set the globals
    var currentStageName = currentStageList[idx];
    currentStageIdx = idx;
    currentStage = stageDefs[currentStageName];

    // Common clearing, and stage specific setup
    $('.current-verse .correct, .current-verse .incorrect').removeClass('correct').removeClass('incorrect');
    $('#id-progress-summary').text("Stage " + (currentStageIdx + 1).toString() + "/" + currentStageList.length.toString());
    $('#id-points-target').html('');

    showStageControls(currentStageName)
    // reset current word
    currentWordIndex = 0;
    currentStage.setUp();
    setStageControlBtns();
    if (currentStage.testMode) {
        unbindDocKeyPress();
        // currentStage.setUp will call testingMethodStrategy.testSetUp()
    } else {
        bindDocKeyPress();
    }

    setProgress(currentStageIdx, 0);
};

// === Moving between stages and verses ===

// next stage within verse
var next = function(ev) {
    if (currentStage.continueStage()) {
        return;
    }
    if (currentStage.testMode) {
        testingMethodStrategy.testTearDown();
    }
    if (currentStageIdx < currentStageList.length - 1) {
        setUpStage(currentStageIdx + 1);
    }
};

var back = function(ev) {
    if (currentStageIdx == 0) {
        return;
    }
    if (currentStage.testMode) {
        testingMethodStrategy.testTearDown();
    }
    setUpStage(currentStageIdx - 1);
};

var nextVerse = function() {
    var doIt = function() {
        currentVerseIndex++;
        loadCurrentVerse();
        hideLoadingIndicator();
    };

    if (nextVersePossible()) {
        if (currentVerseIndex == maxVerseIndex) {
            // We got to the end, and the next batch didn't load in time. So
            // we have to load them and wait synchronously before we can
            // continue.
            indicateLoading();
            if ($.active) {
                // Still waiting for something to finish, probably.
                // loadVerses. We don't want to ask again in that
                // case, so just wait.
                window.setTimeout(nextVerse, 500);
            } else {
                loadVerses(doIt);
            }
        } else {
            doIt();
            // Potentially need to load more.
            // Need to do so before we are on the last one,
            // and also give some time for the data to arrive,
            // so we add a buffer.
            if (moreToLoad && maxVerseIndex - currentVerseIndex == LOADING_QUEUE_BUFFER_SIZE) {
                loadVerses();
            }
        }
    } else {
        finish();
    }
};

var nextVersePossible = function() {
    return (currentVerseIndex < maxVerseIndex) || moreToLoad;
};

var markReadAndNextVerse = function() {
    readingComplete(loadStats);
    nextVerse();
};


var finish = function() {
    var go = function() {
        window.location.href = redirect_to;
    };

    if ($.active) {
        indicateLoading();
        // Do the action when we've finished sending data
        $(document).ajaxStop(go);
    } else {
        go();
    }
};

var pressPrimaryButton = function() {
    var $btn = $('input.primary:visible:not([disabled])');
    $btn.click();
};

// =========== Different stages =========

// === Reading stage ===

var readStageStart = function() {
    hideWordBoundaries(false);
    showWord($('.current-verse .word *'));
};

var readStageContinue = function() {
    readingComplete();
    return false;
};

// === Read/recall stages ===
// recall type 1 - FullAndInitial
//    Some full words, some initial letters only

var makeFullAndInitialContinue = function(initialFraction) {
    // Factory function that generates a function for
    // FullAndInitial stage continue function

    var recallContinue = function() {
        if (uncheckedWords.length === 0) {
            return false;
        }
        setProgress(currentStageIdx, checkedWords.length / wordList.length);
        var wordsToCheck = getWordsToCheck(initialFraction);
        showWord($('.current-verse .word *'));
        hideWord(wordsToCheck.find('.wordend'));
        return true;
    };

    return recallContinue;
};

// recall type 2 - InitialAndMissing
//    Some initial words, some missing

var makeInitialAndMissingContinue = function(missingFraction) {
    // Factory function that generates a function for
    // InitialAndMissing stage continue function

    var recallContinue = function() {
        if (uncheckedWords.length === 0) {
            return false;
        }
        setProgress(currentStageIdx, checkedWords.length / wordList.length);
        var wordsToCheck = getWordsToCheck(missingFraction);
        hideWord($('.current-verse .wordend'));
        showWord($('.current-verse .wordstart'));
        hideWord(wordsToCheck.find('.wordstart'));
        return true;
    };

    return recallContinue;
};

var makeRecallStart = function(continueFunc) {
    // Factory function that returns a stage starter
    // function for recall stages
    return function() {
        hideWordBoundaries(false);
        uncheckedWords = wordList.slice(0);
        checkedWords = [];
        continueFunc();
    };

};

var getWordsToCheck = function(checkFraction) {
    // Moves checkFraction fraction of words from uncheckedWords to
    // checkedWords for the next test and return a jQuery objects for the
    // words that are to be checked.

    // Pick some words to test from uncheckedWords:
    var toCheck = [];
    var checkCount = Math.ceil(wordList.length * checkFraction);
    // Try to test the ones in uncheckedWords first.
    toCheck = chooseN(uncheckedWords, checkCount);
    if (toCheck.length < checkCount) {
        // But if these are fewer than the fraction we are
        // supposed to be testing, use others that
        // have already been tested.
        var reCheck = chooseN(checkedWords, checkCount - toCheck.length);
        toCheck = setUnion(reCheck, toCheck);
    }
    uncheckedWords = setRemove(uncheckedWords, toCheck);
    // NB this must come after the chooseN(checkedWords) above.
    checkedWords = setUnion(checkedWords, toCheck);
    var selector = $.map(toCheck, function(elem, idx) {
        return '.current-verse .word:eq(' + elem.toString() + ')';
    }).join(', ');
    return $(selector);
};

var markRevealed = function(wordNumber) {
    var p = checkedWords.indexOf(wordNumber);
    if (p !== -1) {
        checkedWords.splice(p, 1);
    }
    if (uncheckedWords.indexOf(wordNumber) === -1) {
        uncheckedWords.push(wordNumber);
    }
};

// === Testing stages ===

var resetTestingMistakes = function() {
    var i;
    testingMistakes = {};
    for (i = 0; i < wordList.length; i++) {
        testingMistakes[i] = 0;
    }
};

var getPointsTarget = function() {
    // Constants from scores/models.py
    var POINTS_PER_WORD = 20;
    // Duplication of logic in Account.award_action_points.  NB word
    // count excludes reference for this purpose, so we don't use
    // wordList.count
    return currentVerseStatus.wordCount * POINTS_PER_WORD;
};

var hideWordBoundaries = function(hard) {
    wordBoundariesHidden = hard;
    $('.current-verse').toggleClass('hide-word-boundaries', hard);
};

var areWordBoundariesHidden = function() {
    return wordBoundariesHidden;
};

var setPracticeMode = function(practice) {
    practiceMode = practice;
}

var isPracticeMode = function() {
    return practiceMode;
}

var testStart = function() {
    $('.current-verse .word *').stop(true, true);
    // Don't want to see a flash of words at the beginning,
    // so hide quickly
    hideWord($('.current-verse .word span'), {
        'duration': 0,
        queue: false
    });
    resetTestingMistakes();
    testingStatus.text('');
    if (!isPracticeMode()) {
        $('#id-points-target').html(' Points target: <b>' + getPointsTarget().toString() + '</b>');
    }
    if (testingMethodStrategy == null) {
        setTestingMethodStrategy(preferences);
    }
    testingMethodStrategy.testSetUp();

};

var testContinue = function() {
    return true;
};

// === Testing logic ===

// Abstract base class
var TestingStrategy = {
    testReference: true,
    allowHint: function() { return false; },
    conditionalShowReference: function() {
        var referenceSelector = '.current-verse .reference, .current-verse .colon';
        if (this.testReference) {
            $(referenceSelector).show();
        } else {
            $(referenceSelector).hide();
        }
    },
    methodSetUp: function() {  // function to run when method is chosen
        this.conditionalShowReference();
    },
    methodTearDown: function() { }, // function to run when another method is chosen
    testSetUp: function() { // function to run when a test is started
        this.conditionalShowReference();
    },
    testTearDown: function() { // function to run when a test is finished
        testingStatus.hide();
    },
    wordTestSetUp: function() { }, // function to run when a new word is being tested
    wordTestTearDown: function() { }, // function to run when a new word is finished tested
    nextWord: function() {
        this.wordTestTearDown();
        this.wordTestSetUp();
    },
    windowAdjust: function() { },
    scrollingAdjust: function() { }
};

// Base class for keyboard methods
var KeyboardTestingStrategy = Object.create(TestingStrategy);
$.extend(KeyboardTestingStrategy, {

    testSetUp: function() {
        Object.getPrototypeOf(KeyboardTestingStrategy).testSetUp.call(this);
        // After an certain point, we make things a bit harder by not
        // showing the widths of words.
        hideWordBoundaries(currentVerseStatus.strength > HARD_MODE_THRESHOLD);
        $('#id-keyboard-test-bar').show();
        this.wordTestSetUp();
        this.hintsShown = 0;
        if (currentStageList.length == 1) {
            enableBtn($('#id-hint-btn').show(), true);
        } else {
            // Don't show hints button if we just reviewed the verse.
            $('#id-hint-btn').hide();
        }
    },

    testTearDown: function() {
        Object.getPrototypeOf(KeyboardTestingStrategy).testTearDown.call(this);
        // For Safari, it seems we need to blur inputBox before we hide it
        // or hide #id-keyboard-test-bar, otherwise it retains focus, which
        // means that docKeyPress doesn't work.
        inputBox.blur().hide();
        $('#id-keyboard-test-bar').hide();
    },

    wordTestSetUp: function() {
        this.adjustTypingBox();
        inputBox.show().val('').focus();
    },

    windowAdjust: function() {
        this.adjustTypingBox();
    },

    checkCurrentWord: function() {
        var wordIdx = currentWordIndex;
        var word = getWordAt(wordIdx);
        var wordStr = normalizeWordForTest(word.text());
        var typed = normalizeWordForTest(inputBox.val());

        if (this.matchWord(wordStr, typed)) {
            indicateSuccess();
            moveOn();
        } else {
            var mistakeVal = 1 / this.testMaxAttempts;
            testingMistakes[wordIdx] += mistakeVal;
            if (approximatelyEqual(testingMistakes[wordIdx], 1.0, 0.001) ||
                testingMistakes[wordIdx] > 1) // can happen if switched test method in middle
            {
                indicateFail();
                moveOn();
            } else {
                indicateMistake(Math.round(testingMistakes[wordIdx] / mistakeVal),
                    this.testMaxAttempts);
            }
        }
    },

    adjustTypingBox: function() {
        var wordBox = getWordAt(currentWordIndex);
        var pos = wordBox.position();
        var width;
        $('#id-keyboard-test-bar').css({
            left: pos.left.toString() + "px",
            top: pos.top.toString() + "px"
        });
        if (areWordBoundariesHidden()) {
            width = "6em";
        } else {
            width = (wordBox.outerWidth() - 4).toString() + "px";
        }
        // 4 = 2 * size of #id-typing border
        inputBox.css({
            height: (wordBox.outerHeight() - 4).toString() + "px",
            width: width
        })
        // Trigger numeric keyboard:
        // <input pattern="[0-9]*" inputmode="numeric">
        if (wordBox.hasClass('number')) {
            inputBox.attr('pattern', '[0-9]*');
            inputBox.attr('inputmode', 'numeric');
        } else {
            inputBox.removeAttr('pattern');
            inputBox.removeAttr('inputmode');
        }
    },

    showFullWordHint: function() {
        // show full word hint, and move on.
        var word = getWordAt(currentWordIndex);
        var wordStr = stripPunctuation(word.text());
        inputBox.val(wordStr);
        moveOn();
        testingStatus.hide();
    },

    allowHint: function() {
        return this.hintsShown < this.getMaxHints();
    },

    getMaxHints: function() {
        // For very short verses, allow fewer hints e.g.  2 or 3 word
        // verses should get just 1 hint.
        return Math.min(Math.floor(currentVerseStatus.wordCount / 2), this.maxHintsToShow);
    },

    hintFinished: function() {
        inputBox.focus();
        this.hintsShown++;
        if (this.hintsShown >= this.getMaxHints()) {
            enableBtn($('#id-hint-btn'), false);
        }
    }
});


// Full word keyboard testing

var FullWordTestingStrategy = Object.create(KeyboardTestingStrategy);
$.extend(FullWordTestingStrategy, {
    testMaxAttempts: 3,
    maxHintsToShow: 4,

    methodSetUp: function() {
        Object.getPrototypeOf(FullWordTestingStrategy).methodSetUp.call(this);
        $('.test-method-keyboard-full-word').show();
    },

    methodTearDown: function() {
        this.testTearDown();
        $('.test-method-keyboard-full-word').hide();
    },

    shouldCheckWord: function(textSoFar, wordSeparatorEntered) {
        return wordSeparatorEntered;
    },

    matchWord: function(target, typed) {
        // inputs are already lowercased with punctuation stripped
        if (typed === "") {
            return false;
        }
        // for 1 letter words, don't allow any mistakes
        if (target.length === 1) {
            return typed === target;
        }
        // After that, allow N/3 mistakes, rounded up.
        return damerauLevenshteinDistance(target, typed) <= Math.ceil(target.length / 3);
    },

    getHint: function() {
        var word = getWordAt(currentWordIndex);
        var wordStr = stripPunctuation(word.text()); // don't use normalizeWordForTest, we want case
        var typed = normalizeWordForTest(inputBox.val());

        if (typed == "" || typed.slice(0, 1) != wordStr.toLowerCase().slice(0, 1)) {
            // Nothing or incorrect letter typed: show first letter hint
            inputBox.val(wordStr.slice(0, 1));
        } else {
            this.showFullWordHint();
        }

        this.hintFinished();
    }
});


// First letter keyboard testing
var FirstLetterTestingStrategy = Object.create(KeyboardTestingStrategy);

$.extend(FirstLetterTestingStrategy, {
    testMaxAttempts: 2, // stricter than full word because it is easier
    maxHintsToShow: 3,

    methodSetUp: function() {
        Object.getPrototypeOf(FirstLetterTestingStrategy).methodSetUp.call(this);
        $('.test-method-keyboard-first-letter').show();
    },

    methodTearDown: function() {
        this.testTearDown();
        $('.test-method-keyboard-first-letter').hide();
    },

    shouldCheckWord: function(textSoFar, wordSeparatorEntered) {
        return textSoFar.length > 0;
    },

    matchWord: function(target, typed) {
        var lastCharTyped = typed.slice(-1);
        return (lastCharTyped === target.slice(0, 1));
    },

    getHint: function() {
        this.showFullWordHint();
        this.hintFinished();
    }
});

// On screen testing

var OnScreenTestingStrategy = Object.create(TestingStrategy);

$.extend(OnScreenTestingStrategy, {
    testReference: false,

    methodSetUp: function() {
        Object.getPrototypeOf(OnScreenTestingStrategy).methodSetUp.call(this);
        $('.test-method-onscreen').show();
    },

    methodTearDown: function() {
        this.testTearDown();
        $('.test-method-onscreen').hide();
    },

    testSetUp: function() {
        Object.getPrototypeOf(OnScreenTestingStrategy).testSetUp.call(this);
        hideWordBoundaries(true);
        $('#id-onscreen-test-container').show();
        this.wordTestSetUp();
        this.ensureTestDivVisible();
        $('#id-hint-btn').hide();
    },

    testTearDown: function() {
        Object.getPrototypeOf(OnScreenTestingStrategy).testTearDown.call(this);
        $('#id-onscreen-test-container').hide();
        this.removeTestDivFix();
        this.wordTestTearDown();
    },

    wordTestSetUp: function() {
        this.removeCurrentWordMarker();
        var $w = getWordAt(currentWordIndex);
        $w.addClass('current-word');
        var $c = $('#id-onscreen-test-container');
        var $wl = $c.find('#id-onscreen-test-options');
        $c.hide(); // for speed.

        var suggestions = currentVerseStatus.suggestions[currentWordIndex];
        if (suggestions == undefined) {
            $('#id-onscreen-not-available').show();
            $c.show();
            return;
        } else {
            $('#id-onscreen-not-available').hide();
        }
        var chosen = [];
        var correctWord = $w.text();
        chosen.push(normalizeWordForSuggestion(correctWord));
        for (var i = 0; i < suggestions.length; i++) {
            chosen.push(normalizeWordForSuggestion(suggestions[i]));
        }
        chosen.sort();

        var html = '';
        for (var i = 0; i < chosen.length; i++) {
            html += '<span class="word">' + escapeHtml(chosen[i]) + '</span>';
        }
        $wl.html(html);
        var that = this;
        $wl.find('.word').bind('click', function(ev) {
            that.handleButtonClick(ev);
        });
        $c.show();
    },

    wordTestTearDown: function() {
        this.removeCurrentWordMarker();
    },

    removeCurrentWordMarker: function() {
        $('.current-verse .current-word').removeClass('current-word');
    },

    handleButtonClick: function(ev) {
        ev.preventDefault();
        var $btn = $(ev.target);
        var chosenWord = normalizeWordForTest($btn.text());
        var correctWord = normalizeWordForTest(getWordAt(currentWordIndex).text());
        if (chosenWord === correctWord) {
            indicateSuccess();
        } else {
            testingMistakes[currentWordIndex] = 1;
            indicateFail();
        }
        moveOn();
    },

    windowAdjust: function() {
        this.removeTestDivFix();
        this.ensureTestDivVisible();
    },

    scrollingAdjust: function() {
        this.ensureTestDivVisible();
    },

    ensureTestDivVisible: function() {
        // For long verses, we want buttons to be displayed as absolute
        // so they don't have to scroll off screen.
        var $c = $('#id-onscreen-test-container');
        if (!$c.hasClass('make-fixed')) {
            var $win = $(window);
            if ($c.offset().top + $c.outerHeight() > $win.height() - $win.scrollTop()) {
                $c.addClass('make-fixed');
            }
        }
        // There isn't an easy way to undo this - we would need
        // to calculate whether #id-onscreen-test-container would be
        // visible if it were not fixed, which is hard.
    },

    removeTestDivFix: function() {
        $('#id-onscreen-test-container').removeClass('make-fixed');
    }

})

// -----------------------
var normalizeWordForTest = function(str) {
    return simplifyTurkish(stripPunctuation(str.trim())).toLowerCase();
}

var simplifyTurkish = function(str) {
    // People normally type Turkish without attention for correct dots etc.
    // so we tolerate that.
    return (str
        .replace(/Â/g, "A")
        .replace(/â/g, "a")
        .replace(/Ç/g, "C")
        .replace(/ç/g, "c")
        .replace(/Ğ/g, "G")
        .replace(/ğ/g, "g")
        .replace(/İ/g, "I")
        .replace(/ı/g, "i")
        .replace(/Ö/g, "O")
        .replace(/ö/g, "o")
        .replace(/Ş/g, "S")
        .replace(/ş/g, "s")
        .replace(/Ü/g, "U")
        .replace(/ü/g, "u"))
};

var normalizeWordForSuggestion = function(str) {
    return stripOuterPunctuation(str.trim().toLowerCase());
}

// NB Javascript regex character classes like \W \w etc. don't handle
// unicode, such as Turkish characters, so we are better off building lists
// of non-letter-like characters.
var stripPunctuation = function(str) {
    return str.replace(/["'\.,;!?:\/#!$%\^&\*{}=\-_`~()\[\]“”‘’—]/g, "");
};

var stripOuterPunctuation = function(str) {
    return str.replace(/^["'\.,;!?:\/#!$%\^&\*{}=\-_`~()\[\]“”‘’—]+/g, "")
        .replace(/["'\.,;!?:\/#!$%\^&\*{}=\-_`~()\[\]“”‘’—]+$/g, "");
}

var moveOn = function() {
    var wordIdx = currentWordIndex;
    var word = getWordAt(wordIdx);
    showWord(word.find('*'));
    setProgress(currentStageIdx, (wordIdx + 1) / testableWordCount());
    if (wordIdx + 1 === testableWordCount()) {
        testComplete();
    } else {
        currentWordIndex++;
        var isReference = getWordAt(currentWordIndex).hasClass('reference');
        if (isReference) {
            fadeVerseTitle(true);
        }
        testingMethodStrategy.nextWord();
    }
};

// === Stages definition ===

// Full and initial
var recall1Continue = makeFullAndInitialContinue(0.50);
var recall1Start = makeRecallStart(recall1Continue);

var recall2Continue = makeFullAndInitialContinue(1);
var recall2Start = makeRecallStart(recall2Continue);

// initial and missing
var recall3Continue = makeInitialAndMissingContinue(0.33);
var recall3Start = makeRecallStart(recall3Continue);

var recall4Continue = makeInitialAndMissingContinue(0.66);
var recall4Start = makeRecallStart(recall4Continue);

// Each stage definition contains:
//
// setUp: Function to do stage specific setup
//
// continueStage: function that is run when
//  the user clicks 'Next' and moves the stage on.
//  It returns true if the stage should be continued.
//  false is the stage is over.
//
// caption: currently unused
//
// testMode: boolean that is true if in testing
//
// toggleMode: contstant defining how clicking on words should react

var stageDefs = {
    'read': {
        setUp: readStageStart,
        continueStage: readStageContinue,
        caption: 'Read',
        testMode: false,
        toggleMode: WORD_TOGGLE_SHOW
    },
    'recall1': {
        setUp: recall1Start,
        continueStage: recall1Continue,
        caption: 'Recall 1 - 50% initial',
        testMode: false,
        toggleMode: WORD_TOGGLE_HIDE_END
    },
    'recall2': {
        setUp: recall2Start,
        continueStage: recall2Continue,
        caption: 'Recall 2 - 100% initial',
        testMode: false,
        toggleMode: WORD_TOGGLE_HIDE_END
    },
    'recall3': {
        setUp: recall3Start,
        continueStage: recall3Continue,
        caption: 'Recall 3 - 33% missing',
        testMode: false,
        toggleMode: WORD_TOGGLE_HIDE_ALL
    },
    'recall4': {
        setUp: recall4Start,
        continueStage: recall4Continue,
        caption: 'Recall 4 - 66% missing',
        testMode: false,
        toggleMode: WORD_TOGGLE_HIDE_ALL
    },
    'test': {
        setUp: testStart,
        continueStage: testContinue,
        caption: 'Test',
        testMode: true,
        toggleMode: null
    },
    'results': {
        setUp: function() { },
        continueStage: function() {
            return true;
        },
        caption: 'Results',
        testMode: false,
        toggleMode: null
    },
    'readForContext': {
        setUp: function() { },
        continueStage: function() {
            return true;
        },
        caption: 'Read',
        testMode: false,
        toggleMode: null
    },
    'practice': {
        setUp: testStart,
        continueStage: testContinue,
        caption: 'Practice',
        testMode: true,
        toggleMode: null
    }
};

// === Handling stage lists ===


var setUpStageList = function(verseData) {
    var strength = 0;
    if (verseData.strength != null) {
        strength = verseData.strength;
    }
    if (verseData.learning_type == LEARNING_TYPE_PRACTICE) {
        currentStageList = ['practice'];
        setPracticeMode(true);
    } else {
        if (verseData.needs_testing) {
            currentStageList = chooseStageListForStrength(strength);
            setPracticeMode(false);
        } else {
            currentStageList = ['readForContext'];
        }
    }
    setUpStage(0);
};

var chooseStageListForStrength = function(strength) {
    // This function is tuned to give read/recall stages only for the
    // early stages, or when the verse has been completely forgotten.
    // Although it doesn't use it, it's tuned to the value of
    // INITIAL_STRENGTH_FACTOR.
    // The other constants are picked by looking at the
    // output of accounts.memorymodel.test_run()
    if (strength < 0.02) {
        // either first test, or first test after initial test accuracy
        // of 20% or less. Do everything:
        return ['read', 'recall1', 'recall2', 'recall3', 'recall4', 'test'];
    } else if (strength < 0.07) {
        // e.g. first test was 70% or less, this is second test
        return ['recall2', 'test'];
    } else {
        return ['test'];
    }
};


// ========= Handling verse loading =======

var getSeenVerseIds = function() {
    if (versesToLearn == null) {
        return []
    }
    var keys = Object.keys(versesToLearn);
    var ids = [];
    for (var i = 0; i < keys.length; i++) {
        ids.push(versesToLearn[keys[i]].id);
    }
    return ids;
};

var loadVerses = function(callbackAfter?) {
    var url = '/api/learnscripture/v1/versestolearn/';
    $.ajax({
        url: url,
        data: {
            format: 'json',
            seen: getSeenVerseIds().join(","),
            r: Math.floor(Math.random() * 1000000000).toString() // IE cache breaker
        },
        dataType: 'json',
        type: 'GET',
        success: function(data) {
            // This function can be called when we have already
            // loaded the verses e.g. if the user changed the
            // version.  Also, once some verses have been
            // read/learnt, they will be missing from the incoming
            // data. Also, the underlying versestolearn handler batches
            // data to avoid sending too much over the network,
            // so multiple calls to loadVerses will be need to
            // get all the data.

            // We use the 'learn_order' as an index to work out
            // which verse we are on, and to merge the incoming
            // verses with any existing.
            var i;
            if (versesToLearn === null) {
                versesToLearn = {};
            }
            moreToLoad = true;

            for (i = 0; i < data.length; i++) {
                var verse = data[i];
                versesToLearn[verse.learn_order] = verse;
                if (maxVerseIndex === null ||
                    verse.learn_order > maxVerseIndex) {
                    maxVerseIndex = verse.learn_order;
                }
                if (minVerseIndex === null ||
                    verse.learn_order < minVerseIndex) {
                    minVerseIndex = verse.learn_order;
                }
                if (verse.max_order_val != undefined && verse.learn_order == verse.max_order_val) {
                    moreToLoad = false;
                }
            }
            // TODO - this is backwards compat for sessions that don't have
            // verse.max_order_val attribute
            if (data.length < VERSE_STATUS_BATCH_SIZE) {
                // It would only be less if versestolearn has run out of
                // things to send. So we don't need to try again.
                moreToLoad = false;
            }
            if (callbackAfter !== undefined) {
                callbackAfter();
            }
        },
        error: ajaxFailed
    });
};


var normalizeLearningType = function(verseData) {
    if (verseData.learning_type != LEARNING_TYPE_PRACTICE && !verseData.needs_testing && !isPassageType(verseData)) {
        // This can happen if the user chooses a verse set to learn
        // and they already know the verses in it.
        verseData.learning_type = LEARNING_TYPE_PRACTICE;
    }
};

var loadCurrentVerse = function() {
    var oldVerseStatus = currentVerseStatus;
    currentVerseStatus = versesToLearn[currentVerseIndex];
    var verseStatus = currentVerseStatus;

    verseStatus.showReference = (
        verseStatus.version.text_type == TEXT_TYPE_BIBLE ? (verseStatus.verse_set === null ||
            verseStatus.verse_set === undefined ||
            verseStatus.verse_set.set_type === SET_TYPE_SELECTION) : false)

    verseStatus.wordCount = verseStatus.scoring_text_words.length;
    normalizeLearningType(verseStatus);
    var moveOld = (oldVerseStatus !== null &&
        isPassageType(oldVerseStatus) &&
        // Need to cope with possibility of a gap
        // in the passage, caused by slim_passage_for_reviewing()
        (verseStatus.text_order === oldVerseStatus.text_order + 1))
    if (moveOld) {
        moveOldWords();
    } else {
        $('.current-verse').children().remove();
    }

    if (verseStatus.verse_set &&
        verseStatus.verse_set.get_absolute_url) {
        $('#id-verse-set-info')
            .find('a')
            .text(verseStatus.verse_set.name)
            .attr('href', verseStatus.verse_set.get_absolute_url)
            .end()
            .show();
    } else {
        $('#id-verse-set-info').hide();
    }

    $('.current-verse').hide(); // Hide until set up
    $('#id-verse-title').text(verseStatus.title_text);

    var version = verseStatus.version;
    var copyrightNotice = escapeHtml(version.short_name + " - " + version.full_name);
    if (version.url != "") {
        copyrightNotice = '<a href="' + escapeHtml(version.url) + '">' + copyrightNotice + '</a>';
    }
    $('#id-copyright-notice').html(copyrightNotice);

    // convert newlines to divs
    markupVerse(verseStatus);
    $('#id-loading').hide();
    $('#id-controls').show();
    if (moveOld) {
        scrollOutPreviousVerse();
        $('.current-verse').show();
    } else {
        $('.previous-verse').remove();
        $('.current-verse').show();
    }
    setUpStageList(verseStatus);
    $('.selection-set-only').toggle(!isPassageType(verseStatus));

    var nextBtns = $('#id-next-verse-btn, #id-context-next-verse-btn');
    if (nextVersePossible()) {
        nextBtns.val('Next');
    } else {
        nextBtns.val('Done');
    }
    if (verseStatus.return_to) {
        redirect_to = verseStatus.return_to;
    }
};

var isPassageType = function(verseData) {
    return (verseData &&
        verseData.verse_set &&
        verseData.verse_set.set_type === SET_TYPE_PASSAGE);
};

var moveOldWords = function() {
    $('.previous-verse-wrapper').remove();
    $('.current-verse').removeClass('current-verse').addClass('previous-verse');
    $('.current-verse-wrapper').removeClass('current-verse-wrapper')
        .addClass('previous-verse-wrapper')
        .after('<div class="current-verse-wrapper"><div class="current-verse"></div></div>');
    $('.previous-verse .word, .previous-verse .testedword').each(function(idx, elem) {
        $(elem).removeAttr('id');
    });
};

var scrollOutPreviousVerse = function() {
    // Animating this is tricky to do cleanly, since we'd need to using
    // continuation style to pass in the remainder of the calling function
    // to pass to an animate({complete:}) callback.

    var words = {}; // offset:node list of word spans
    var maxOffset = null;
    $('.previous-verse .word, .previous-verse .testedword').each(function(idx, elem) {
        var offset = $(elem).offset().top;
        if (maxOffset === null || offset > maxOffset) {
            maxOffset = offset;
        }
        // Build up elements for the words in groups
        if (words[offset] === undefined) {
            words[offset] = [];
        }
        words[offset].push(elem);
    });

    // Now make the other words disappear
    for (var offset in words) {
        if (words.hasOwnProperty(offset)) {
            var elems = words[offset];
            if (offset.toString() !== maxOffset.toString()) {
                $(elems).remove();
            }
        }
    }
    $('.previous-verse br').remove();

    // Now shrink the area
    $('.previous-verse .word, .previous-verse .testedword')
        .removeClass('word').addClass('testedword')
        .find('span')
        .removeClass('wordstart').removeClass('wordend');
};

var markupVerse = function(verseStatus) {
    // We join words back together, so that we can split on \n
    // which is useful for poetry
    var text = verseStatus.scoring_text_words.join(" ")
    var reference = (verseStatus.showReference ? verseStatus.localized_reference : null);

    // Word splitting here needs to match with the way
    // that bibleverses.suggestions splits words up.

    // First split lines into divs.
    $.each(text.split(/\n/), function(idx, line) {
        if (line.trim() !== '') {
            $('.current-verse').append('<div class="line">' +
                line + '</div>');
        }
    });
    var doTest = (verseStatus.needs_testing ||
        verseStatus.learning_type == LEARNING_TYPE_PRACTICE)
    // Then split up into words
    var wordClass = doTest ? 'word' : 'testedword';
    var wordGroups = [];

    $('.current-verse .line').each(function(idx, elem) {
        wordGroups.push($(elem).text().trim().split(/ |\n/));
    });
    wordList = [];
    referenceList = [];
    var replacement = [];
    var wordNumber = 0;
    var i, parts, replace;


    var makeNormalWord = function(word, wordClass) {
        var core = stripOuterPunctuation(word);
        var start = word.slice(0, word.indexOf(core[0]) + 1);
        var end = word.slice(start.length);
        return ('<span id="id-word-' + wordNumber.toString() +
            '" class=\"' + wordClass + '\">' +
            '<span class="wordstart">' + start +
            '</span><span class="wordend">' + end +
            '</span></span>');

    };

    for (i = 0; i < wordGroups.length; i++) {
        var group = wordGroups[i];
        group = $.map(group, function(word, j) {
            if (stripPunctuation(word) === "") {
                return null;
            } else {
                return word;
            }
        });
        replace = [];
        $.each(group, function(j, word) {
            replace.push(makeNormalWord(word, wordClass));
            wordList.push(wordNumber);
            wordNumber++;
        });
        replacement.push(replace.join(' '));
    }

    $('.current-verse').html(replacement.join('<br/>'));

    // Add reference
    if (doTest && reference !== null) {
        // Javascript regexes: no Unicode support, no lookbehinds, and we want to keep the punctuation
        // that we are splitting on.
        parts = [].concat.apply([], reference.split(/(?=[\s:\-])/).map(w => w.match(/^[\s:\-]/) ? [w[0], w.slice(1)] : [w]));
        replace = [];

        $.each(parts, function(j, word) {
            word = word.trim()
            if (word == "") {
                return;
            }
            if (word == ":" || word == "-") {
                replace.push('<span class="colon">' + word + '</span>');
                return;
            }
            var classes = "word reference"
            if (word.match(/\d+/)) {
                classes += " number";
            }
            replace.push(makeNormalWord(word, classes));
            wordList.push(wordNumber);
            referenceList.push(wordNumber);
            wordNumber++;
        });
        $('.current-verse').append('<br/>' + replace.join(' '));

    }

    $('.current-verse .word').bind('click', function(ev) {
        if (!currentStage.testMode) {
            toggleWord($(this));
        }
    });
};

// ========== Stats/scores loading ==========

var loadStats = function() {
    $.ajax({
        url: '/api/learnscripture/v1/sessionstats/?format=json&r=' +
            Math.floor(Math.random() * 1000000000).toString(),
        dataType: 'json',
        type: 'GET',
        success: function(data) {
            $('#id-stats-block').html(data.stats_html);
        }
    });
};

var loadActionLogs = function() {
    if (!scoringEnabled) {
        return;
    }
    $.ajax({
        url: '/api/learnscripture/v1/actionlogs/?format=json&r=' +
            Math.floor(Math.random() * 1000000000).toString(),
        dataType: 'json',
        type: 'GET',
        success: handleActionLogs
    });
};

var handleActionLogs = function(actionLogs) {
    var container = $('#id-points-block');
    var addActionLog = function(actionLogs) {
        // This is defined recursively to get the animation to work
        // nicely for multiple score logs appearing one after the other.
        if (actionLogs.length === 0) {
            return;
        }
        var actionLog = actionLogs[0];
        var doRest = function() {
            addActionLog(actionLogs.slice(1))
        };
        var divId = 'id-action-log-' + actionLog.id.toString();
        if ($('#' + divId).length === 0) {
            // Put new ones at top
            var newSL = $('<div id="' + divId +
                '" class="action-log action-log-type-' + actionLog.reason + '"' +
                '>' + actionLog.points + '</div>');
            // Need some tricks to get height of new element without
            // showing.
            newSL.css({
                'position': 'absolute',
                'visibility': 'hidden',
                'display': 'block',
                'width': container.width().toString() + "px"
            });
            container.prepend(newSL);
            var h = newSL.height();
            newSL.removeAttr('style');

            newSL.css({
                opacity: 0,
                height: 0
            });
            var newProps = {
                opacity: 1,
                height: h.toString() + "px"
            };
            if (preferences.enableAnimations) {
                newSL.animate(newProps, {
                    duration: 300,
                    complete: doRest
                });
            } else {
                newSL.css(newProps);
                doRest();
            }
        } else {
            doRest();
        }
    };
    addActionLog(actionLogs);
};

// =========== Event handlers ==========

// We need to be careful with docKeyPress:
// - it must be disabled when test mode is active,
//   to avoid handling of 'b' and 'n' etc, and
//   to avoid double handling of 'Enter' key press
//
// Unbind docKeyPress may also help with performance
// on handhelds which can be laggy when typing

var docKeyPressBound = false;

var bindDocKeyPress = function() {
    if (!docKeyPressBound && !currentStage.testMode) {
        $(document).bind('keypress', docKeyPress);
        docKeyPressBound = true;
    }
};
var unbindDocKeyPress = function() {
    if (docKeyPressBound) {
        $(document).unbind('keypress');
        docKeyPressBound = false;
    }
};

var inputBoxKeyDown = function(ev) {
    if (ev.which === 27) {
        // ESC
        ev.preventDefault();
        inputBox.val('');
        return;
    }
    var textSoFar = inputBox.val();
    var textSoFarTrimmed = textSoFar.trim();

    if ((textSoFarTrimmed.length > 0) && // if only whitespace entered, don't trigger test
        ((ev.which === 32 || ev.key === " ") ||
            (ev.which === 13 || ev.key === "Enter"))) {
        ev.preventDefault();
        if (currentStage.testMode) {
            testingMethodStrategy.checkCurrentWord();
        }
        return;
    }
    // All other characters dealt with using inputBoxInput
};

var inputBoxInput = function(ev) {
    var textSoFar = inputBox.val();
    var textSoFarTrimmed = textSoFar.trim();
    var isWordSeparator = false
    if (textSoFarTrimmed.length > 0 && textSoFar.slice(-1) == " ") {
        isWordSeparator = true;
    } else {
        var lastChar = textSoFarTrimmed.length == 0 ? "" : textSoFarTrimmed.slice(-1);
        var isInReference = getWordAt(currentWordIndex).hasClass("reference");
        if (isInReference && (lastChar == ":" || lastChar == "-")) {
            isWordSeparator = true;
        }
    }
    if (currentStage.testMode && testingMethodStrategy.shouldCheckWord(textSoFarTrimmed, isWordSeparator)) {
        testingMethodStrategy.checkCurrentWord();
    }

};

var docKeyPress = function(ev) {
    var tagName = ev.target.tagName.toLowerCase();
    if (tagName === 'input' ||
        tagName === 'select' ||
        tagName === 'textarea') {
        return;
    }
    // Some android phones will bring up box for searching or something
    // on almost any key press. But we don't want to disable other
    // keyboard shortcuts on desktop browsers.
    if (!ev.altKey && !ev.ctrlKey && !ev.metaKey &&
        !(ev.which >= 112 && ev.which <= 123) && // F1 - F12
        !(ev.which === 0) // special characters
    ) {
        ev.preventDefault();
    }
    switch (ev.which) {
        case 13: // Enter
            if (tagName === 'a') {
                return;
            }
            pressPrimaryButton();
            break;
    }
};

var skipVerse = function(ev) {
    ev.preventDefault();
    $.ajax({
        url: '/api/learnscripture/v1/skipverse/?format=json',
        dataType: 'json',
        type: 'POST',
        data: {
            verse_status: JSON.stringify(currentVerseStatus, null, 2)
        },
        success: ajaxRetrySucceeded,
        retry: ajaxRetryOptions,
        error: ajaxRetryFailed
    });
    if (testingMethodStrategy != null) {
        testingMethodStrategy.testTearDown();
    }
    nextVerse();
};

var cancelLearning = function(ev) {
    ev.preventDefault();
    $.ajax({
        url: '/api/learnscripture/v1/cancellearningverse/?format=json',
        dataType: 'json',
        type: 'POST',
        data: {
            verse_status: JSON.stringify(currentVerseStatus, null, 2)
        },
        success: ajaxRetrySucceeded,
        retry: ajaxRetryOptions,
        error: ajaxRetryFailed
    });
    nextVerse();
};

var resetProgress = function(ev) {
    ev.preventDefault();
    if (confirm("This will reset your progress on this item to zero. " +
        "Continue?")) {
        $.ajax({
            url: '/api/learnscripture/v1/resetprogress/?format=json',
            dataType: 'json',
            type: 'POST',
            data: {
                verse_status: JSON.stringify(currentVerseStatus, null, 2)
            },
            success: ajaxRetrySucceeded,
            retry: ajaxRetryOptions,
            error: ajaxRetryFailed
        });
        currentVerseStatus.strength = 0;
        currentVerseStatus.needs_testing = true;
        currentVerseStatus = null;
        loadCurrentVerse();
    }
}


// === Setup and wiring ===

var setUpLearningControls = function() {
    setUpAudio();
    receivePreferences(getPreferences());
    receiveAccountData(getAccountData());

    // Listen for changes to preferences.
    $('#id-preferences-data').bind('preferencesSet', function(ev, prefs) {
        receivePreferences(prefs);
    });

    $('#id-account-data').bind('accountDataSet', function(ev, accountData) {
        receiveAccountData(accountData);
    });

    inputBox = $('#id-typing');
    // Chrome on Android does not fire onkeypress, only keyup and keydown.
    // It also fires onchange only after pressing 'Enter' and closing
    // the on-screen keyboard.
    // Firefox (at least on desktop) doesn't show anything helpful
    // in ev.which with keyup, only keydown.
    // Some browsers on Linux are screwy when it comes to composed
    // characters.
    // So, we do as much as possible with 'input', and 'keydown'
    // just for detecting enter
    inputBox.bind('input', inputBoxInput);
    inputBox.bind('keydown', inputBoxKeyDown);
    testingStatus = $('#id-testing-status');
    $('#id-next-btn').bind('click', next).show();
    $('#id-back-btn').bind('click', back).show();
    $('#id-next-verse-btn').bind('click', nextVerse);
    $('#id-context-next-verse-btn').bind('click', markReadAndNextVerse);

    $('#id-hint-btn').bind('click', function(ev) {
        ev.preventDefault();
        // Just disabling the button doesn't seem to be enough to stop event
        // handler firing on iOS
        if (testingMethodStrategy.allowHint()) {
            testingMethodStrategy.getHint();
        }
    });
    $('#id-help-btn').bind('click', function(ev) {
        if (preferences.enableAnimations) {
            $('#id-help').toggle('fast');
        } else {
            $('#id-help').toggle();
        }
        $('#id-help-btn').button('toggle');
    });
    $('#id-skip-verse-btn').bind("click", skipVerse);
    $('#id-cancel-learning-btn').bind("click", cancelLearning);
    $('#id-reset-progress-btn').bind("click", resetProgress);
    $(window).resize(function() {
        if (currentStage !== null &&
            currentStage.testMode) {
            testingMethodStrategy.windowAdjust();
        }
    });
    $(window).bind('scroll', function() {
        if (currentStage !== null &&
            currentStage.testMode) {
            // Run callback if stopped scrolling for 500ms
            if (scrollingTimeoutId !== null) {
                window.clearTimeout(scrollingTimeoutId);
            }
            scrollingTimeoutId = window.setTimeout(function() {
                testingMethodStrategy.scrollingAdjust();
            }, 500);
        }
    });
    $('.verse-dropdown').dropdown();
    loadVerses(function() {
        if (maxVerseIndex === null) {
            $('#id-loading').hide();
            $('#id-controls').hide();
            $('#id-no-verse-queue').show();
        } else {
            currentVerseIndex = minVerseIndex;
            loadCurrentVerse();
            loadStats();
            loadActionLogs();
        }
    });

};

var receivePreferences = function(prefs) {
    if (prefs === null) {
        // If preferences have not yet been loaded
        return;
    }
    preferences = prefs;
    setTestingMethodStrategy(preferences);
};

var setTestingMethodStrategy = function(preferences) {
    if (testingMethodStrategy != null) {
        testingMethodStrategy.methodTearDown();
    }
    if (preferences.testingMethod === TEST_FULL_WORDS) {
        testingMethodStrategy = FullWordTestingStrategy;
    } else if (preferences.testingMethod === TEST_FIRST_LETTER) {
        testingMethodStrategy = FirstLetterTestingStrategy;
    } else if (preferences.testingMethod === TEST_ON_SCREEN) {
        testingMethodStrategy = OnScreenTestingStrategy;
    }
    testingMethodStrategy.methodSetUp();
    if (currentStage != null && currentStage.testMode) {
        testingMethodStrategy.testSetUp();
    }
};

var receiveAccountData = function(accountData) {
    userAccountData = accountData;
    scoringEnabled = (userAccountData !== null);
    if (scoringEnabled) {
        $('#id-points-block *').remove();
    }
};


function damerauLevenshteinDistance(a, b) {
    var INF = a.length + b.length;
    var i, j, d, i1, j1;
    var H = [];
    // Make matrix of dimensions a.length + 2, b.length + 2
    for (i = 0; i < a.length + 2; i++) {
        H.push(new Array(b.length + 2));
    }
    // Fill matrix
    H[0][0] = INF;
    for (i = 0; i <= a.length; ++i) {
        H[i + 1][1] = i;
        H[i + 1][0] = INF;
    }
    for (j = 0; j <= b.length; ++j) {
        H[1][j + 1] = j;
        H[0][j + 1] = INF;
    }
    var DA = {};
    for (d = 0; d < (a + b).length; d++) {
        DA[(a + b)[d]] = 0;
    }
    for (i = 1; i <= a.length; ++i) {
        var DB = 0;
        for (j = 1; j <= b.length; ++j) {
            i1 = DA[b[j - 1]];
            j1 = DB;
            d = ((a[i - 1] === b[j - 1]) ? 0 : 1);
            if (d === 0) {
                DB = j;
            }
            H[i + 1][j + 1] = Math.min(H[i][j] + d,
                H[i + 1][j] + 1,
                H[i][j + 1] + 1,
                H[i1][j1] + (i - i1 - 1) + 1 + (j - j1 - 1));
        }
        DA[a[i - 1]] = i;
    }
    return H[a.length + 1][b.length + 1];
}

$(document).ready(function() {
    if ($('#id-verse-wrapper').length > 0) {
        setUpLearningControls();
    }
});
