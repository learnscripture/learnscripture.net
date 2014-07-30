/*jslint browser: true, vars: true, plusplus: true, maxerr: 1000 */
/*globals $, jQuery, alert, confirm */

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


var learnscripture = (function (learnscripture, $) {
    "use strict";
    // User prefs
    var preferences = null;
    var userAccountData = null;
    var scoringEnabled = false;

    var isLearningPage = null;

    // Controls
    var inputBox = null;
    var testingStatus = null;

    // -- Constants and globals --
    var WORD_TOGGLE_SHOW = 0;
    var WORD_TOGGLE_HIDE_END = 1;
    var WORD_TOGGLE_HIDE_ALL = 2;

    var scrollingTimeoutId = null;
    var fastEventName = 'ontouchstart' in window ? 'touchstart' : 'mousedown';

    // Defined in StageType:
    var STAGE_TYPE_TEST = 'TEST';
    var STAGE_TYPE_READ = 'READ';

    // Defined in TestingMethod:
    var TEST_FULL_WORDS = 0;
    var TEST_FIRST_LETTER = 1;
    var TEST_ON_SCREEN = 2;

    // Defined in VerseSetType
    var SET_TYPE_SELECTION = 1;
    var SET_TYPE_PASSAGE = 2;

    // Defined in MemoryStage:
    var MEMORY_STAGE_TESTED = 3;

    // Defined in LearningType:
    var LEARNING_TYPE_PRACTICE = 'practice';

    // Defined in TextType
    var TEXT_TYPE_BIBLE = 1;
    var TEXT_TYPE_CATECHISM = 2;

    var INITIAL_STRENGTH_FACTOR = 0.1;

    // Thresholds for different testings modes:
    // Strength == 0.6 corresponds to about 10 days learning.
    var HARD_MODE_THRESHOLD = 0.6

    // Defined in learnscripture.session
    var VERSE_STATUS_BATCH_SIZE = 10;

    // Initial state
    var currentStage = null;
    var currentStageIdx = null;
    var currentStageList = null;

    // this is changed only when a whole
    // set of stages is completed
    var spentStagesCount = 0;

    // tracking of words is done using a list
    // of integers, where the value is the index
    // into the div of the word.
    var wordList = null;
    var referenceList = null;
    var untestedWords = null;
    var testedWords = null;

    var testingMethodStrategy = null;
    var testingMistakes = null;
    var hardMode = null;
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

    var chooseN = function (aList, n) {
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

    var setUnion = function (list1, list2) {
        var i, output = list1.slice(0);
        for (i = 0; i < list2.length; i++) {
            var item = list2[i];
            if (output.indexOf(item) === -1) {
                output.push(item);
            }
        }
        return output;
    };

    var setRemove = function (list1, list2) {
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

    var approximatelyEqual = function (a, b, epsilon) {
        return Math.abs(Math.abs(a) - Math.abs(b)) <= epsilon;
    };

    // === HTML ===

    var enableBtn = function (btn, state) {
        if (state) {
            btn.removeAttr('disabled');
        } else {
            btn.attr('disabled', 'disabled');
        }
    };

    function escapeHtml(s) {
	if (!s) {
	    return "";
	}
	s = s + "";
	return s.replace(/[\&"<>\\]/g, function(s) {
	    switch(s) {
	    case "&": return "&amp;";
	    case "\\": return "\\\\";
	    case '"': return '\"';
	    case "<": return "&lt;";
	    case ">": return "&gt;";
	    default: return s;
	    }
	});
    }

    // === Events ===

    var alphanumeric = function (ev) {
        return ((!ev.ctrlKey && !ev.altKey && (
            (ev.which >= 65 && ev.which <= 90) ||
            (ev.which >= 48 && ev.which <= 57)
        )));
    };


    // ========== Word toggling =============

    // For speed in test mode, where we have to keep up with typing,
    // we tag all the words with ids, and keep track of the current id
    // and word number
    var currentWordIndex = null;

    var getWordAt = function (index) {
        return $('#id-word-' + index.toString());
    };

    var getWordNumber = function (word) {
        return $('.current-verse .word').index(word);
    };

    var isHidden = function (word) {
        return word.css('opacity') === '0';
    };

    var hideWord = function (word, options) {
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

    var showWord = function (word) {
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

    var toggleWord = function (word) {
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

    var flashMsg = function (elements, wordBox) {
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

    var indicateSuccess = function () {
        var word = getWordAt(currentWordIndex);
        word.addClass('correct');
        flashMsg(testingStatus.attr({
            'class': 'correct'
        }).text("Correct!"), word);
    };

    var beep = function (frequency, length) {
        if (!preferences.enableSounds) {
            return;
        }
        learnscripture.doBeep(frequency, length);
    };

    var indicateMistake = function (mistakes, maxMistakes) {
        var msg = "Try again! (" + mistakes.toString() + "/" + maxMistakes.toString() + ")";
        flashMsg(testingStatus.attr({
                'class': 'incorrect'
            }).text(msg),
            getWordAt(currentWordIndex));
        beep(330, 0.10);
    };

    var indicateFail = function () {
        var word = getWordAt(currentWordIndex);
        word.addClass('incorrect');
        flashMsg(testingStatus.attr({
            'class': 'incorrect'
        }).text("Incorrect"), word);
        beep(220, 0.10);
    };

    // ========== Actions completed =============

    var readingComplete = function (callbackAfter) {
        $.ajax({
            url: '/api/learnscripture/v1/actioncomplete/?format=json',
            dataType: 'json',
            type: 'POST',
            data: {
                verse_status: JSON.stringify(currentVerseStatus, null, 2),
                stage: STAGE_TYPE_READ
            },
            success: function () {
                learnscripture.ajaxRetrySucceeded();
                if (callbackAfter !== undefined) {
                    callbackAfter();
                }
            },
            retry: learnscripture.ajaxRetryOptions,
            error: learnscripture.ajaxRetryFailed
        });
    };

    var testableWordCount = function () {
        if (testingMethodStrategy.testReference) {
            return wordList.length;
        } else {
            return wordList.length - referenceList.length;
        }
    }

    var testComplete = function () {
        testingMethodStrategy.testTearDown();

        var accuracy = 0;
        var mistakes = 0;
        $.each(testingMistakes, function (key, val) {
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
                verse_status: JSON.stringify(currentVerseStatus, null, 2),
                stage: STAGE_TYPE_TEST,
                accuracy: accuracy,
                practice: wasPracticeMode,
            },
            success: function (data) {
                learnscripture.ajaxRetrySucceeded();
                if (!wasPracticeMode) {
                    loadStats();
                    loadScoreLogs();
                }
            },
            retry: learnscripture.ajaxRetryOptions,
            error: learnscripture.ajaxRetryFailed
        });

        var accuracyPercent = Math.floor(accuracy * 100).toString();
        $('#id-accuracy').text(accuracyPercent + "%");
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

        if (nextVersePossible()) {
            $('#id-finish-btn').show();
        } else {
            $('#id-finish-btn').hide();
        }

        if (accuracyPercent < 90) {
            $('#id-more-practice-btn').show();

            if (accuracyPercent < 80) {
                // 'More practice' the default
                $('#id-more-practice-btn').addClass('primary');
                $('#id-next-verse-btn').removeClass('primary');

            } else {
                // 'More practice' available but not default
                $('#id-more-practice-btn').removeClass('primary');
                $('#id-next-verse-btn').addClass('primary');
            }

            fastEventBind($('#id-more-practice-btn').unbind(), function (ev) {
                if (accuracyPercent < 10) {
                    currentStageList = chooseStageListForStrength(0);
                } else if (accuracyPercent < 30) {
                    currentStageList = ['read', 'recall2', 'recall4', 'test'];
                } else {
                    currentStageList = ['recall2', 'recall4', 'test'];
                }
                setUpStage(0);
            });
        } else {
            $('#id-more-practice-btn').removeClass('primary').hide();
            $('#id-next-verse-btn').addClass('primary');
        }
        testingStatus.hide();
        bindDocKeyPress();
    };

    // =========== Stage handling ==========

    var setProgress = function (stageIdx, fraction) {
        var progress = (stageIdx + fraction) / currentStageList.length * 100;
        var bar = $('#id-progress-bar');
        var oldVal = parseInt(bar.val(), 10);
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

    var completeStageGroup = function () {
        spentStagesCount += currentStageList.length;
        currentStage = stageDefs['results'];
        currentStageList = [currentStage];
        currentStageIdx = 0;
        enableBtn($('#id-next-btn, #id-back-btn'), false);
    };

    var setStageControlBtns = function () {
        if (currentStageIdx == 0 && currentStageList.length == 1) {
            $('#id-next-btn, #id-back-btn').hide();
        } else {
            $('#id-next-btn, #id-back-btn').show();
            enableBtn($('#id-next-btn'), currentStageIdx < currentStageList.length - 1);
            enableBtn($('#id-back-btn'), currentStageIdx > 0);
        }
    };

    var fadeVerseTitle = function (fade) {
        $('#id-verse-title').toggleClass('blurry', fade);
    };

    var getStageSelector = function (stageName) {
        return '.stage-' + stageName;
    }

    var forceRedrawBottomControls = function () {
        // This hack is needed for Chrome 30, possibly others
        var n = $('#id-bottom-controls').get(0);
        n.style.webkitTransform = '';
        window.setTimeout(function () {
            n.style.webkitTransform = 'scale(1)';
        }, 0);
    }

    var showStageControls = function (stageName) {
        var stageSelector = getStageSelector(stageName);
        // Hide everything that is stage specific, except stuff for this
        // stage.
        $('.stage-specific:not(' + stageSelector + ')').hide()
        $(stageSelector).show();
        // Once we've set things up, show the container.
        $('#id-bottom-controls .buttonbar').show();
        forceRedrawBottomControls();
    }

    var showTestFinishedControls = function () {
        // We can't just use showStageControls, because we want to leave the
        // instructions div alone, and only affect the id-bottom-controls
        // bit.
        var stageSelector = getStageSelector('test-finished');
        $('#id-bottom-controls .stage-specific:not(' + stageSelector + ')').hide();
        $('#id-bottom-controls ' + stageSelector).show();
        forceRedrawBottomControls();
    };

    var setUpStage = function (idx) {
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
            // currentStage.setUp will call testingMethod.testSetUp()
        } else {
            if (testingMethodStrategy != null) {
                testingMethodStrategy.testTearDown();
            }
            bindDocKeyPress();
        }

        setProgress(currentStageIdx, 0);
    };

    // === Moving between stages and verses ===

    // next stage within verse
    var next = function (ev) {
        if (currentStage.continueStage()) {
            return;
        }
        if (currentStageIdx < currentStageList.length - 1) {
            setUpStage(currentStageIdx + 1);
        }
    };

    var back = function (ev) {
        if (currentStageIdx == 0) {
            return;
        }
        setUpStage(currentStageIdx - 1);
    };

    var nextVerse = function () {
        if (nextVersePossible()) {
            currentVerseIndex++;
            loadCurrentVerse();
            // Potentially need to load more.
            // Need to do so before we are on the last one,
            // and also give some time for the data to arrive,
            // so we add a buffer of 2.
            if (moreToLoad && maxVerseIndex - currentVerseIndex == 2) {
                loadVerses();
            }
        } else {
            finish();
        }
    };

    var nextVersePossible = function () {
        return (currentVerseIndex < maxVerseIndex);
    };

    var markReadAndNextVerse = function () {
        readingComplete(loadStats);
        nextVerse();
    };


    var finish = function () {
        var go = function () {
            window.location = redirect_to;
        };

        if ($.active) {
            $('body').ajaxStop(go);
        } else {
            go();
        }
    };

    var pressPrimaryButton = function () {
        var $btn = $('input.primary:visible:not([disabled])');
        if ($btn.hasClass('fastevent')) {
            $btn.trigger(fastEventName);
        } else {
            $btn.click();
        }
    };

    // =========== Different stages =========

    // === Reading stage ===

    var readStageStart = function () {
        setHardMode(false);
        showWord($('.current-verse .word *'));
    };

    var readStageContinue = function () {
        readingComplete();
        return false;
    };

    // === Read/recall stages ===
    // recall type 1 - FullAndInitial
    //    Some full words, some initial letters only

    var makeFullAndInitialContinue = function (initialFraction) {
        // Factory function that generates a function for
        // FullAndInitial stage continue function

        var recallContinue = function () {
            if (untestedWords.length === 0) {
                return false;
            }
            setProgress(currentStageIdx, testedWords.length / wordList.length);
            var testWords = getTestWords(initialFraction);
            showWord($('.current-verse .word *'));
            hideWord(testWords.find('.wordend'));
            return true;
        };

        return recallContinue;
    };

    // recall type 2 - InitialAndMissing
    //    Some initial words, some missing

    var makeInitialAndMissingContinue = function (missingFraction) {
        // Factory function that generates a function for
        // InitialAndMissing stage continue function

        var recallContinue = function () {
            if (untestedWords.length === 0) {
                return false;
            }
            setProgress(currentStageIdx, testedWords.length / wordList.length);
            var testWords = getTestWords(missingFraction);
            hideWord($('.current-verse .wordend'));
            showWord($('.current-verse .wordstart'));
            hideWord(testWords.find('.wordstart'));
            return true;
        };

        return recallContinue;
    };

    var makeRecallStart = function (continueFunc) {
        // Factory function that returns a stage starter
        // function for recall stages
        return function () {
            setHardMode(false);
            untestedWords = wordList.slice(0);
            testedWords = [];
            continueFunc();
        };

    };

    var getTestWords = function (testFraction) {
        // Moves testFraction fraction of words from
        // untestedWords for next test, for the next test
        // and return a jQuery objects for the words
        // that are to be tested.
        // Pick some words to test from untestedWords
        var i;
        var toTest = [];
        var testCount = Math.ceil(wordList.length * testFraction);
        // Try to test the ones in untestedWords first.
        toTest = chooseN(untestedWords, testCount);
        if (toTest.length < testCount) {
            // But if these are fewer than the fraction we are
            // supposed to be testing, use others that
            // have already been tested.
            var reTest = chooseN(testedWords, testCount - toTest.length);
            toTest = setUnion(reTest, toTest);
        }
        untestedWords = setRemove(untestedWords, toTest);
        // NB this must come after the chooseN(testedWords) above.
        testedWords = setUnion(testedWords, toTest);
        var selector = $.map(toTest, function (elem, idx) {
            return '.current-verse .word:eq(' + elem.toString() + ')';
        }).join(', ');
        return $(selector);
    };

    var markRevealed = function (wordNumber) {
        var p = testedWords.indexOf(wordNumber);
        if (p !== -1) {
            testedWords.splice(p, 1);
        }
        if (untestedWords.indexOf(wordNumber) === -1) {
            untestedWords.push(wordNumber);
        }
    };

    // === Testing stages ===

    var resetTestingMistakes = function () {
        var i;
        testingMistakes = {};
        for (i = 0; i < wordList.length; i++) {
            testingMistakes[i] = 0;
        }
    };

    var getPointsTarget = function () {
        // Constants from scores/models.py
        var POINTS_PER_WORD = 20;
        // Duplication of logic in Account.award_action_points.  NB word
        // count excludes reference for this purpose, so we don't use
        // wordList.count
        return currentVerseStatus.wordCount * POINTS_PER_WORD;
    };

    var setHardMode = function (hard) {
        hardMode = hard;
        $('.current-verse').toggleClass('hard-mode', hard);
    };

    var isHardMode = function () {
        return hardMode;
    };

    var setPracticeMode = function (practice) {
        practiceMode = practice;
    }

    var isPracticeMode = function () {
        return practiceMode;
    }

    var testStart = function () {
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
        testingMethodStrategy.testSetUp();

    };

    var testContinue = function () {
        return true;
    };

    // === Testing logic ===

    // Abstract base class
    var TestingStrategy = {
        testReference: true,
        conditionalShowReference: function () {
            var referenceSelector = '.current-verse .reference, .current-verse .colon';
            if (this.testReference) {
                $(referenceSelector).show();
            } else {
                $(referenceSelector).hide();
            }
        },
        methodSetUp: function () {  // function to run when method is chosen
            this.conditionalShowReference();
        },
        methodTearDown: function () {}, // function to run when another method is chosen
        testSetUp: function () { // function to run when a test is started
            this.conditionalShowReference();
        },
        testTearDown: function () {}, // function to run when a test is finished
        wordTestSetUp: function () {}, // function to run when a new word is being tested
        wordTestTearDown: function () {}, // function to run when a new word is finished tested
        nextWord: function () {
            this.wordTestTearDown();
            this.wordTestSetUp();
        },
        windowAdjust: function () {},
        scrollingAdjust: function () {}
    };

    // Base class for keyboard methods
    var KeyboardTestingStrategy = Object.create(TestingStrategy);
    $.extend(KeyboardTestingStrategy, {

        testSetUp: function () {
            Object.getPrototypeOf(KeyboardTestingStrategy).testSetUp.call(this);
            // After an certain point, we make things a bit harder by not
            // showing the widths of words.
            setHardMode(currentVerseStatus.strength > HARD_MODE_THRESHOLD);
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

        testTearDown: function () {
            $('#id-keyboard-test-bar').hide();
            this.wordTestTearDown();
        },

        wordTestSetUp: function () {
            this.adjustTypingBox();
            inputBox.show().val('').focus();
            this.forceShowKeyboard();
        },

        wordTestTearDown: function () {
            inputBox.blur().hide();
        },

        windowAdjust: function () {
            this.adjustTypingBox();
        },

        checkCurrentWord: function () {
            var wordIdx = currentWordIndex;
            var word = getWordAt(wordIdx);
            var wordStr = normaliseWordForTest(word.text());
            var typed = normaliseWordForTest(inputBox.val());

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
                        this.forceShowKeyboard();
                    }
            }
        },

        adjustTypingBox: function () {
            var wordBox = getWordAt(currentWordIndex);
            var pos = wordBox.position();
            var width;
            $('#id-keyboard-test-bar').css({
                left: pos.left.toString() + "px",
                top: pos.top.toString() + "px"
            });
            if (isHardMode()) {
                width = "6em";
            } else {
                width = (wordBox.outerWidth() - 4).toString() + "px";
            }
            // 4 = 2 * size of #id-typing border
            inputBox.css({
                height: (wordBox.outerHeight() - 4).toString() + "px",
                width: width
            })
        },

        forceShowKeyboard: function () {
            // Attempt to force keyboard to be shown. This is needed in case
            // android app user pressed 'Enter' instead of 'space'
            if (window.androidlearnscripture &&
                window.androidlearnscripture.showKeyboard) {
                inputBox.focus();
                window.androidlearnscripture.showKeyboard();
            }

        },

        showFullWordHint: function () {
            // show full word hint, and move on.
            var word = getWordAt(currentWordIndex);
            var wordStr = stripPunctuation(word.text());
            inputBox.val(wordStr);
            moveOn();
            testingStatus.hide();
        },

        hintFinished: function () {
            inputBox.focus();
            this.hintsShown++;
            // For very short verses, allow fewer hints e.g.  2 or 3 word
            // verses should get just 1 hint.
            var maxHints = Math.min(Math.floor(currentVerseStatus.wordCount / 2), this.maxHintsToShow);
            if (this.hintsShown >= this.maxHintsToShow) {
                enableBtn($('#id-hint-btn'), false);
            }
        }
    });


    // Full word keyboard testing

    var FullWordTestingStrategy = Object.create(KeyboardTestingStrategy);
    $.extend(FullWordTestingStrategy, {
        testMaxAttempts: 3,
        maxHintsToShow: 4,

        methodSetUp: function () {
            Object.getPrototypeOf(FullWordTestingStrategy).methodSetUp.call(this);
            $('.test-method-keyboard-full-word').show();
        },

        methodTearDown: function () {
            this.testTearDown();
            $('.test-method-keyboard-full-word').hide();
        },

        shouldCheckWord: function(ev, isSpace) {
            return isSpace;
        },

        matchWord: function (target, typed) {
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

        getHint: function () {
            var word = getWordAt(currentWordIndex);
            var wordStr = stripPunctuation(word.text()); // don't use normaliseWordForTest, we want case
            var typed = normaliseWordForTest(inputBox.val());

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

        methodSetUp: function () {
            Object.getPrototypeOf(FirstLetterTestingStrategy).methodSetUp.call(this);
            $('.test-method-keyboard-first-letter').show();
        },

        methodTearDown: function () {
            this.testTearDown();
            $('.test-method-keyboard-first-letter').hide();
        },

        shouldCheckWord: function (ev, isSpace) {
            if (isSpace) {
                // compat for Android on Chrome, which doesn't fire the
                // event for first letter in box, but will get here if
                // you press one letter and then space
                return true;
            }
            return alphanumeric(ev);
        },

        matchWord: function (target, typed) {
            return (typed === target.slice(0, 1));
        },

        getHint: function () {
            this.showFullWordHint();
            this.hintFinished();
        }
    });

    // On screen testing

    var OnScreenTestingStrategy = Object.create(TestingStrategy);

    $.extend(OnScreenTestingStrategy, {
        testReference: false,

        methodSetUp: function () {
            Object.getPrototypeOf(OnScreenTestingStrategy).methodSetUp.call(this);
            $('.test-method-onscreen').show();
        },

        methodTearDown: function () {
            this.testTearDown();
            $('.test-method-onscreen').hide();
        },

        testSetUp: function () {
            Object.getPrototypeOf(OnScreenTestingStrategy).testSetUp.call(this);
            setHardMode(true);
            $('#id-onscreen-test-container').show();
            this.wordTestSetUp();
            this.ensureTestDivVisible();
            $('#id-hint-btn').hide();
        },

        testTearDown: function () {
            $('#id-onscreen-test-container').hide();
            this.removeTestDivFix();
            this.wordTestTearDown();
        },

        wordTestSetUp: function () {
            this.removeCurrentWordMarker();
            var $w = getWordAt(currentWordIndex);
            $w.addClass('current-word');
            var $c = $('#id-onscreen-test-container');
            $c.hide(); // for speed.

            var suggestions = currentVerseStatus.suggestion_pairs[currentWordIndex];
            if (suggestions == undefined) {
                $c.html('On screen testing is not available for this verse in this version. Sorry!');
                $c.show();
                return;
            }

            // suggestions is an array of (word, frequency) pairs,
            // normalised so that maximum frequency is 1.0
            // Make bag according to frequency.
            var bag = [];
            for (var i = 0; i < suggestions.length; i++) {
                var suggestion = suggestions[i];
                for (var j = 0; j < suggestion[1] * 100; j++) {
                    bag.push(suggestion[0]);
                }
            }
            // Pick N unique items
            var chosen = [];
            var CHOICE_COUNT = 10;
            var correctWord = normaliseWordForTest($w.text());
            chosen.push(correctWord);
            while (chosen.length < CHOICE_COUNT && bag.length > 0) {
                var pos = Math.floor(Math.random() * bag.length);
                var choice = normaliseWordForTest(bag[pos]);
                if (chosen.indexOf(choice) === -1) {
                    chosen.push(choice);
                }
                bag = setRemove(bag, [choice]);
            }
            chosen.sort();

            var html = '';
            for (var i = 0; i < chosen.length; i++) {
                html += '<span class="word">' + escapeHtml(chosen[i]) + '</span>';
            }
            $c.html(html);
            fastEventBind($c.find('.word'),
                          this.handleButtonClick);
            $c.show();
        },

        wordTestTearDown: function () {
            this.removeCurrentWordMarker();
        },

        removeCurrentWordMarker: function () {
            $('.current-verse .current-word').removeClass('current-word');
        },

        handleButtonClick: function (ev) {
            ev.preventDefault();
            var $btn = $(ev.target);
            if (normaliseWordForTest($btn.text()) ===
                normaliseWordForTest(getWordAt(currentWordIndex).text())) {
                indicateSuccess();
            } else {
                testingMistakes[currentWordIndex] = 1;
                indicateFail();
            }
            moveOn();
        },

        windowAdjust: function () {
            this.removeTestDivFix();
            this.ensureTestDivVisible();
        },

        scrollingAdjust: function() {
            this.ensureTestDivVisible();
        },

        ensureTestDivVisible: function () {
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

        removeTestDivFix: function () {
            $('#id-onscreen-test-container').removeClass('make-fixed');
        }

    })

    // -----------------------

    var normaliseWordForTest = function (str) {
        return stripPunctuation(str.trim().toLowerCase());
    }

    var stripPunctuation = function (str) {
        return str.replace(/["'\.,;!?:\/#!$%\^&\*{}=\-_`~()]/g, "");
    };

    var moveOn = function () {
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
            setUp: function () {},
            continueStage: function () {
                return true;
            },
            caption: 'Results',
            testMode: false,
            toggleMode: null
        },
        'readForContext': {
            setUp: function () {},
            continueStage: function () {
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


    var setUpStageList = function (verseData) {
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

    var chooseStageListForStrength = function (strength) {
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

    var loadVerses = function (callbackAfter) {
        var url = '/api/learnscripture/v1/versestolearn/?format=json&r=' + Math.floor(Math.random() * 1000000000).toString();
        $.ajax({
            url: url,
            dataType: 'json',
            type: 'GET',
            success: function (data) {
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
                }
                if (data.length < VERSE_STATUS_BATCH_SIZE) {
                    // It would only be less if versestolearn has run out of
                    // things to send. So we don't need to try again.
                    moreToLoad = false;
                }
                if (callbackAfter !== undefined) {
                    callbackAfter();
                }
            },
            error: learnscripture.ajaxFailed
        });
    };


    var normaliseLearningType = function (verseData) {
        if (verseData.learning_type != LEARNING_TYPE_PRACTICE && !verseData.needs_testing && !isPassageType(verseData)) {
            // This can happen if the user chooses a verse set to learn
            // and they already know the verses in it.
            verseData.learning_type = LEARNING_TYPE_PRACTICE;
        }
    };

    var loadCurrentVerse = function () {
        var oldVerseStatus = currentVerseStatus;
        currentVerseStatus = versesToLearn[currentVerseIndex];
        var verseStatus = currentVerseStatus;

        verseStatus.showReference = (
            verseStatus.version.text_type == TEXT_TYPE_BIBLE ? (verseStatus.verse_set === null ||
                verseStatus.verse_set === undefined ||
                verseStatus.verse_set.set_type === SET_TYPE_SELECTION) : false)

        verseStatus.wordCount = verseStatus.scoring_text_words.length;
        normaliseLearningType(verseStatus);
        var moveOld = (oldVerseStatus !== null &&
            isPassageType(oldVerseStatus) &&
            // Need to cope with possibility of a gap
            // in the passage, caused by slim_passage_for_revising()
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
        if (verseStatus.version.text_type == TEXT_TYPE_BIBLE) {
            $('#id-version-select').show().val(verseStatus.version.slug);
        } else {
            $('#id-version-select').hide();
        }
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

        var nextBtns = $('#id-next-verse-btn, #id-context-next-verse-btn, #id-read-anyway-vext-verse-btn');
        if (nextVersePossible()) {
            nextBtns.val('Next');
        } else {
            nextBtns.val('Done');
        }
        if (verseStatus.return_to) {
            redirect_to = verseStatus.return_to;
        }
    };

    var isPassageType = function (verseData) {
        return (verseData &&
            verseData.verse_set &&
            verseData.verse_set.set_type === SET_TYPE_PASSAGE);
    };

    var moveOldWords = function () {
        $('.previous-verse-wrapper').remove();
        $('.current-verse').removeClass('current-verse').addClass('previous-verse');
        $('.current-verse-wrapper').removeClass('current-verse-wrapper')
            .addClass('previous-verse-wrapper')
            .after('<div class="current-verse-wrapper"><div class="current-verse"></div></div>');
        $('.previous-verse .word, .previous-verse .testedword').each(function (idx, elem) {
            $(elem).removeAttr('id');
        });
    };

    var scrollOutPreviousVerse = function () {
        // Animating this is tricky to do cleanly, since we'd need to using
        // continuation style to pass in the remainder of the calling function
        // to pass to an animate({complete:}) callback.

        var words = {}; // offset:node list of word spans
        var maxOffset = null;
        $('.previous-verse .word, .previous-verse .testedword').each(function (idx, elem) {
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
        $.each(words, function (offset, elems) {
            if (offset.toString() !== maxOffset.toString()) {
                $(elems).remove();
            }
        });
        $('.previous-verse br').remove();

        // Now shrink the area
        var wordHeight = $('.previous-verse .word, .previous-verse .testedword').css('line-height');
        $('.previous-verse .word, .previous-verse .testedword')
            .removeClass('word').addClass('testedword')
            .find('span')
            .removeClass('wordstart').removeClass('wordend');
    };

    var markupVerse = function (verseStatus) {
        // We join words back together, so that we can split on \n
        // which is useful for poetry
        var text = verseStatus.scoring_text_words.join(" ")
        var reference = (verseStatus.showReference ? verseStatus.reference : null);
        // First split lines into divs.
        $.each(text.split(/\n/), function (idx, line) {
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

        $('.current-verse .line').each(function (idx, elem) {
            wordGroups.push($(elem).text().trim().split(/ |\n/));
        });
        wordList = [];
        referenceList = [];
        var replacement = [];
        var wordNumber = 0;
        var i, parts, replace;


        var makeNormalWord = function (word, wordClass) {
            var start = word.match(/\W*./)[0];
            var end = word.slice(start.length);
            return ('<span id="id-word-' + wordNumber.toString() +
                '" class=\"' + wordClass + '\">' +
                '<span class="wordstart">' + start +
                '</span><span class="wordend">' + end +
                '</span></span>');

        };

        for (i = 0; i < wordGroups.length; i++) {
            var group = wordGroups[i];
            group = $.map(group, function (word, j) {
                if (stripPunctuation(word) === "") {
                    return null;
                } else {
                    return word;
                }
            });
            replace = [];
            $.each(group, function (j, word) {
                replace.push(makeNormalWord(word, wordClass));
                wordList.push(wordNumber);
                wordNumber++;
            });
            replacement.push(replace.join(' '));
        }

        $('.current-verse').html(replacement.join('<br/>'));

        // Add reference
        if (doTest && reference !== null) {
            parts = reference.split(/\b/);
            replace = [];
            $.each(parts, function (j, word) {
                if (word.trim() == "") {
                    return;
                }
                if (word == ":" || word == "-") {
                    replace.push('<span class="colon">' + word + '</span>');
                    return;
                }
                replace.push(makeNormalWord(word, "word reference"));
                wordList.push(wordNumber);
                referenceList.push(wordNumber);
                wordNumber++;
            });
            $('.current-verse').append('<br/>' + replace.join(' '));

        }

        $('.current-verse .word').bind('tap click', function (ev) {
            if (!currentStage.testMode) {
                toggleWord($(this));
            }
        });
    };

    // ========== Stats/scores loading ==========

    var loadStats = function () {
        $.ajax({
            url: '/api/learnscripture/v1/sessionstats/?format=json&r=' +
                Math.floor(Math.random() * 1000000000).toString(),
            dataType: 'json',
            type: 'GET',
            success: function (data) {
                $('#id-stats-block').html(data.stats_html);
            }
        });
    };

    var loadScoreLogs = function () {
        if (!scoringEnabled) {
            return;
        }
        $.ajax({
            url: '/api/learnscripture/v1/scorelogs/?format=json&r=' +
                Math.floor(Math.random() * 1000000000).toString(),
            dataType: 'json',
            type: 'GET',
            success: handleScoreLogs
        });
    };

    var handleScoreLogs = function (scoreLogs) {
        var container = $('#id-points-block');
        var addScoreLog = function (scoreLogs) {
            // This is defined recursively to get the animation to work
            // nicely for multiple score logs appearing one after the other.
            if (scoreLogs.length === 0) {
                return;
            }
            var scoreLog = scoreLogs[0];
            var doRest = function () {
                addScoreLog(scoreLogs.slice(1))
            };
            var divId = 'id-score-log-' + scoreLog.id.toString();
            if ($('#' + divId).length === 0) {
                // Put new ones at top
                var newSL = $('<div id="' + divId +
                    '" class="score-log score-log-type-' + scoreLog.reason + '"' +
                    '>' + scoreLog.points + '</div>');
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
        addScoreLog(scoreLogs);
    };

    // =========== Event handlers ==========

    // We need to be careful with docKeyPress:
    // - it must be disabled when modals are active
    // - it must be disabled when test mode is active,
    //   to avoid handling of 'b' and 'n' etc, and
    //   to avoid double handling of 'Enter' key press
    //
    // Unbind docKeyPress may also help with performance
    // on handhelds which can be laggy when typing

    var docKeyPressBound = false;

    var bindDocKeyPress = function () {
        if (!docKeyPressBound && !currentStage.testMode) {
            $(document).bind('keypress', docKeyPress);
            docKeyPressBound = true;
        }
    };
    var unbindDocKeyPress = function () {
        if (docKeyPressBound) {
            $(document).unbind('keypress');
            docKeyPressBound = false;
        }
    };

    var inputKeyDown = function (ev) {
        var characterInserted = false;
        var textSoFar = inputBox.val();
        var textSoFarTrimmed = textSoFar.trim();
        if (ev.which == 229) {
            // keyboard composition code sent by Chrome on Android, which is
            // totally useless. The only upside is that, apart from the
            // first character in the text box, the keydown event gets sent
            // *after* the character has already appeared in the text
            // box. This means we can get the character just typed.
            if (textSoFar.length > 0) {
                var character = textSoFar.substr(textSoFar.length - 1, 1);
                // overwrite ev.which
                ev.which = character.charCodeAt(0);
                characterInserted = true;
            }
        }

        if (ev.which === 27) {
            // ESC
            ev.preventDefault();
            inputBox.val('');
            return;
        }

        if ((textSoFarTrimmed.length > 0) && // if only whitespace entered, don't trigger test
            (
                ev.which === 32 || // space
                ev.which === 13 || // enter
                (ev.which == 186 // colon, at least for US/UK
                    // allowed if in reference
                    && getWordAt(currentWordIndex).hasClass("reference")
                )
            )
        ) {
            ev.preventDefault();
            if (currentStage.testMode && testingMethodStrategy.shouldCheckWord(ev, true)) {
                testingMethodStrategy.checkCurrentWord();
            }
            return;
        } else {
            // Any other character
            if (currentStage.testMode && testingMethodStrategy.shouldCheckWord(ev, false)) {
                ev.preventDefault();
                if (!characterInserted) {
                    // Put it there ourselves, so it is ready for checkCurrentWord()
                    inputBox.val(String.fromCharCode(ev.which));
                }
                testingMethodStrategy.checkCurrentWord();
            }
        }

    };

    var inputFocused = function (ev) {
        if (window.androidlearnscripture &&
            window.androidlearnscripture.registerInputFocused) {
            window.androidlearnscripture.registerInputFocused();
        }
    }

    var docKeyPress = function (ev) {
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

    var versionSelectChanged = function (ev) {
        $.ajax({
            url: '/api/learnscripture/v1/changeversion/?format=json',
            dataType: 'json',
            type: 'POST',
            data: {
                verse_status: JSON.stringify(currentVerseStatus, null, 2),
                new_version_slug: $('#id-version-select').val()
            },
            success: function () {
                // We pretend there is no 'old verse' if we changed
                // version, to avoid the complications with moving the
                // old verse.
                currentVerseStatus = null;
                // Any number of verses could have changed (if it was
                // part of a passage), so we must reload everything.
                loadVerses(loadCurrentVerse);
            },
            error: learnscripture.ajaxFailed
        });
    };

    var skipVerse = function (ev) {
        ev.preventDefault();
        $.ajax({
            url: '/api/learnscripture/v1/skipverse/?format=json',
            dataType: 'json',
            type: 'POST',
            data: {
                verse_status: JSON.stringify(currentVerseStatus, null, 2)
            },
            success: learnscripture.ajaxRetrySucceeded,
            retry: learnscripture.ajaxRetryOptions,
            error: learnscripture.ajaxRetryFailed
        });
        nextVerse();
    };

    var cancelLearning = function (ev) {
        ev.preventDefault();
        $.ajax({
            url: '/api/learnscripture/v1/cancellearningverse/?format=json',
            dataType: 'json',
            type: 'POST',
            data: {
                verse_status: JSON.stringify(currentVerseStatus, null, 2)
            },
            success: learnscripture.ajaxRetrySucceeded,
            retry: learnscripture.ajaxRetryOptions,
            error: learnscripture.ajaxRetryFailed
        });
        nextVerse();
    };

    var resetProgress = function (ev) {
        ev.preventDefault();
        if (confirm("This will reset your progress on this item to the zero. " +
            "Continue?")) {
            $.ajax({
                url: '/api/learnscripture/v1/resetprogress/?format=json',
                dataType: 'json',
                type: 'POST',
                data: {
                    verse_status: JSON.stringify(currentVerseStatus, null, 2)
                },
                success: learnscripture.ajaxRetrySucceeded,
                retry: learnscripture.ajaxRetryOptions,
                error: learnscripture.ajaxRetryFailed
            });
            currentVerseStatus.strength = 0;
            currentVerseStatus.needs_testing = true;
            currentVerseStatus = null;
            loadCurrentVerse();
        }
    }

    var finishBtnClick = function (ev) {
        // Skip to end, which skips everything in between
        var verse = versesToLearn[maxVerseIndex];
        $.ajax({
            url: '/api/learnscripture/v1/skipverse/?format=json',
            dataType: 'json',
            type: 'POST',
            data: {
                verse_status: JSON.stringify(verse, null, 2)
            },
            success: learnscripture.ajaxRetrySucceeded,
            retry: learnscripture.ajaxRetryOptions,
            error: learnscripture.ajaxRetryFailed
        });
        finish();
    };

    // === Setup and wiring ===
    var fastEventBind = function ($elem, callback) {
        $elem.addClass('fastevent').bind(fastEventName, callback);
        return $elem;
    };

    var setUpLearningControls = function () {
        isLearningPage = ($('#id-verse-wrapper').length > 0);
        if (!isLearningPage) {
            return;
        }
        learnscripture.setUpAudio();
        receivePreferences(learnscripture.getPreferences());
        receiveAccountData(learnscripture.getAccountData());

        // Listen for changes to preferences.
        $('#id-preferences-data').bind('preferencesSet', function (ev, prefs) {
            receivePreferences(prefs);
        });

        $('#id-account-data').bind('accountDataSet', function (ev, accountData) {
            receiveAccountData(accountData);
        });

        inputBox = $('#id-typing');
        inputBox.on('focus', inputFocused);
        // Chrome on Android does not fire onkeypress, only keyup and keydown.
        // It also fires onchange only after pressing 'Enter' and closing
        // the on-screen keyboard.
        inputBox.bind('keydown', inputKeyDown);
        testingStatus = $('#id-testing-status');
        fastEventBind($('#id-next-btn'), next).show();
        fastEventBind($('#id-back-btn'), back).show();
        fastEventBind($('#id-hint-btn'), function (ev) {
            ev.preventDefault();
            testingMethodStrategy.getHint();
        });
        fastEventBind($('#id-next-verse-btn'), nextVerse);
        fastEventBind($('#id-context-next-verse-btn'), markReadAndNextVerse);
        $('#id-version-select').change(versionSelectChanged);
        fastEventBind($('#id-help-btn'), function (ev) {
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
        fastEventBind($('#id-finish-btn'), finishBtnClick);
        $(window).resize(function () {
            if (currentStage !== null &&
                currentStage.testMode) {
                testingMethodStrategy.windowAdjust();
            }
        });
        $(window).bind('scroll', function () {
            if (currentStage !== null &&
                currentStage.testMode) {
                // Run callback if stopped scrolling for 500ms
                if (scrollingTimeoutId !== null) {
                    window.clearTimeout(scrollingTimeoutId);
                }
                scrollingTimeoutId = window.setTimeout(function () {
                    testingMethodStrategy.scrollingAdjust();
                }, 500);
            }
        });
        if (typeof operamini !== "undefined") {
            // Opera Mini is a thin client browser and doesn't support
            // responding to key presses. It does, however, support
            // input onchange events, which fires when the user preses 'Done'
            inputBox.change(function (ev) {
                ev.preventDefault();
                testingMethodStrategy.checkCurrentWord();
                inputBox.focus();
            });
        }
        $('.verse-dropdown').dropdown();
        loadVerses(function () {
            if (maxVerseIndex === null) {
                $('#id-loading').hide();
                $('#id-controls').hide();
                $('#id-no-verse-queue').show();
            } else {
                currentVerseIndex = minVerseIndex;
                loadCurrentVerse();
                loadStats();
                loadScoreLogs();
            }
        });

        // For performance on handhelds especially, we disable docKeyPress
        // handling when a modal is active.

        $('div.modal').bind('shown', function (ev) {
            unbindDocKeyPress();
        }).bind('hidden', function (ev) {
            bindDocKeyPress();
        });


    };

    var receivePreferences = function (prefs) {
        if (prefs === null) {
            // If preferences have not yet been loaded
            return;
        }
        preferences = prefs;
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

    var receiveAccountData = function (accountData) {
        userAccountData = accountData;
        scoringEnabled = (userAccountData !== null);
        if (scoringEnabled) {
            $('#id-points-block *').remove();
        }
    };


    // === Exports ===

    learnscripture.setUpLearningControls = setUpLearningControls;
    return learnscripture;

}(learnscripture || {}, $));

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

$(document).ready(function () {
    learnscripture.setUpLearningControls();
});
