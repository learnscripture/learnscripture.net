/*jslint browser: true, vars: true, plusplus: true, maxerr: 1000 */
/*globals $, jQuery, alert, confirm */

// Learning and testing functionality for learnscripture.net

var learnscripture =
    (function (learnscripture, $) {
        "use strict";
        // User prefs
        var preferences = null;

        var isLearningPage = null;

        // Controls
        var inputBox = null;
        var testingStatus = null;

        // -- Constants and globals --
        var WORD_TOGGLE_SHOW = 0;
        var WORD_TOGGLE_HIDE_END = 1;
        var WORD_TOGGLE_HIDE_ALL = 2;


        // Defined in StageType:
        var STAGE_TYPE_TEST = 'TEST';
        var STAGE_TYPE_READ = 'READ';

        // Defined in TestingMethod:
        var TEST_FULL_WORDS = 0;
        var TEST_FIRST_LETTER = 1;

        // Defined in VerseSetType
        var SET_TYPE_SELECTION = 1;
        var SET_TYPE_PASSAGE = 2;

        // Defined in MemoryStage:
        var MEMORY_STAGE_TESTED = 3;

        var INITIAL_STRENGTH_FACTOR = 0.1;

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
        var untestedWords = null;
        var testedWords = null;

        var testingMistakes = null;
        var hardMode = null;

        // Score logs
        var waitingForScoreLogs = false;

        // Verse list
        var versesToLearn = null; // eventually a dictionary of index:verse
        var currentVerseIndex = null;
        var minVerseIndex = null;
        var maxVerseIndex = null;
        var currentVerseStatus = null;

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


        // === Events ===

        var alphanumeric = function (ev) {
            return ((!ev.ctrlKey && !ev.altKey && (
                (ev.which >= 65 && ev.which <= 90) ||
                    (ev.which >= 48 && ev.which <= 57)
            )));
        };


        // ========== Word toggling and selection =============

        // For speed in test mode, where we have to keep up with typing,
        // we tag all the words with ids, and keep track of the selected id
        // and word number
        var selectedWordIndex = null;

        var moveSelection = function (pos) {
            if (pos === selectedWordIndex) {
                return;
            }
            if (selectedWordIndex !== null) {
                getWordAt(selectedWordIndex).removeClass('selected');
            }
            selectedWordIndex = pos;
            getWordAt(selectedWordIndex).addClass('selected');
        };

        var getWordAt = function (index) {
            return $('#id-word-' + index.toString());
        };

        var getWordNumber = function (word) {
            return $('.current-verse .word').index(word);
        };

        var moveSelectionRelative = function (distance) {
            var i = selectedWordIndex;
            var pos = Math.min(Math.max(0, i + distance),
                               wordList.length - 1);
            moveSelection(pos);
        };

        var isHidden = function (word) {
            return word.css('opacity') === '0';
        };

        var hideWord = function (word, options) {
            if (preferences.enableAnimations) {
                if (options === undefined) {
                    options = {duration: 300, queue: false};
                }
                word.animate({'opacity': '0'}, options);
            } else {
                word.css({'opacity': '0'});
            }
        };

        var showWord = function (word) {
            if (preferences.enableAnimations) {
                word.animate({'opacity': '1'}, {duration: 300, queue: false});
            } else {
                word.css({'opacity': '1'});
            }
        };

        var toggleWord = function (word) {
            var wordNumber = getWordNumber(word);
            moveSelection(wordNumber);

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
            elements.css({'top': (pos.top + wordBox.outerHeight() + 4).toString() + "px",
                          'left': pos.left.toString() + "px"}).show();

            if (preferences.enableAnimations) {
                elements.css({opacity: 1}).animate({opacity: 0},
                                                   {duration: 1000, queue: false});
            } else {
                elements.css({opacity: 1});
            }
        };

        var indicateSuccess = function () {
            var word = getWordAt(selectedWordIndex);
            word.addClass('correct').removeClass('selected');
            flashMsg(testingStatus.attr({'class': 'correct'}).text("Correct!"), word);
        };

        var indicateMistake = function (mistakes, maxMistakes) {
            var msg = "Try again! (" + mistakes.toString() + "/" + maxMistakes.toString() + ")";
            flashMsg(testingStatus.attr({'class': 'incorrect'}).text(msg),
                     getWordAt(selectedWordIndex));
        };

        var indicateFail = function () {
            var word = getWordAt(selectedWordIndex);
            word.addClass('incorrect').removeClass('selected');
            flashMsg(testingStatus.attr({'class': 'incorrect'}).text("Incorrect"), word);
        };

        // ========== Actions completed =============

        var readingComplete = function (callbackAfter) {
            $.ajax({url: '/api/learnscripture/v1/actioncomplete/',
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

        var testComplete = function () {
            var accuracy = 0;
            var mistakes = 0;
            $.each(testingMistakes, function (key, val) {
                mistakes += val;
            });
            accuracy = 1 - (mistakes / wordList.length);
            accuracy = Math.max(0, accuracy);

            // Do some rounding  to avoid '99.9' and retain 3 s.f.
            accuracy = Math.round(accuracy * 1000) / 1000;

            $.ajax({url: '/api/learnscripture/v1/actioncomplete/',
                    dataType: 'json',
                    type: 'POST',
                    data: {
                        verse_status: JSON.stringify(currentVerseStatus, null, 2),
                        stage: STAGE_TYPE_TEST,
                        accuracy: accuracy
                    },
                    success: function(data) {
                        learnscripture.ajaxRetrySucceeded();
                        loadStats();
                        loadScoreLogs();
                    },
                    retry: learnscripture.ajaxRetryOptions,
                    error: learnscripture.ajaxRetryFailed
                   });

            var accuracyPercent = Math.floor(accuracy * 100).toString();
            $('#id-accuracy').text(accuracyPercent + "%");
            var comment =
                accuracyPercent > 95 ? 'awesome!' :
                accuracyPercent > 90 ? 'excellent!' :
                accuracyPercent > 80 ? 'very good.' :
                accuracyPercent > 70 ? 'good.' :
                accuracyPercent > 50 ? 'OK.' :
                accuracyPercent > 30 ? 'could do better!' :
                "more practice needed!";

            $('#id-result-comment').text(comment);
            fadeVerseTitle(false);

            completeStageGroup();

            if (accuracyPercent < 85) {
                $('#id-more-practice-btn').show();

                if (accuracyPercent < 60) {
                    // 'More practice' the default
                    $('#id-more-practice-btn').addClass('primary');
                    $('#id-result-suggestion').text("We recommend a bit a more practice " +
                                                    "with this before continuing");
                    $('#id-next-verse-btn').removeClass('primary');

                } else {
                    // 'More practice' available but not default
                    $('#id-more-practice-btn').removeClass('primary');
                    $('#id-result-suggestion').text("");
                    $('#id-next-verse-btn').addClass('primary');
                }

                $('#id-more-practice-btn').unbind().click(function () {
                    if (accuracyPercent < 10) {
                        currentStageList = chooseStageListForStrength(0);
                    } else if (accuracyPercent < 30) {
                        currentStageList = ['read', 'recall2', 'recall4', 'test'];
                    } else {
                        currentStageList = ['recall2', 'recall4', 'test'];
                    }
                    setupStage(0);
                });
            } else {
                $('#id-result-suggestion').text("");
                $('#id-more-practice-btn').removeClass('primary').hide();
                $('#id-next-verse-btn').addClass('primary');
            }

            inputBox.blur();
            $('#id-test-bar').hide();
            testingStatus.hide();
            bindDocKeyPress();
            showInstructions("results");
        };

        // =========== Stage handling ==========

        var setProgress = function (stageIdx, fraction) {
            var progress = (stageIdx + fraction)/currentStageList.length * 100;
            var bar = $('#id-progress-bar');
            var oldVal = parseInt(bar.val(), 10);
            if (preferences.enableAnimations &&
                !currentStage.testMode &&
                Math.abs(oldVal - progress) > 5 && // animation pointless
                !(oldVal > 99 && progress === 0) // new verse - animation confusing
               ) {
                bar.animate({value: progress,
                             duration: 'fast'});
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
            setNextPreviousBtns();
        };

        var showInstructions = function (stageName) {
            $('#id-instructions > div').css({opacity: 0});
            $('#id-instructions > div').hide();
            $('#id-instructions .instructions-' + stageName).show().css({opacity: 1});
        };

        var setNextPreviousBtns = function () {
            enableBtn($('#id-next-btn'), currentStageIdx < currentStageList.length - 1);
            enableBtn($('#id-back-btn'), currentStageIdx > 0);
        };

        var fadeVerseTitle = function (fade) {
            $('#id-verse-title').toggleClass('blurry', fade);
        };

        var setupStage = function (idx) {
            // set the globals
            var currentStageName = currentStageList[idx];
            currentStageIdx = idx;
            currentStage = stageDefs[currentStageName];

            // Common clearing, and stage specific setup
            $('.current-verse .correct, .current-verse .incorrect').removeClass('correct').removeClass('incorrect');
            $('#id-progress-summary').text("Stage " + (currentStageIdx + 1).toString() + "/" + currentStageList.length.toString());
            $('#id-points-target').html('');
            currentStage.setup();
            setNextPreviousBtns();
            if (currentStage.testMode) {
                unbindDocKeyPress();
                $('#id-test-bar').show();
                inputBox.focus();
            } else {
                inputBox.blur();
                $('#id-test-bar').hide();
                bindDocKeyPress();
            }

            showInstructions(currentStageName);
            // reset selected word
            moveSelection(0);
            adjustTypingBox();

            setProgress(currentStageIdx, 0);
        };

        // === Moving between stages and verses ===

        // next stage within verse
        var next = function (ev) {
            if (currentStage.continueStage()) {
                return;
            }
            if (currentStageIdx < currentStageList.length - 1) {
                setupStage(currentStageIdx + 1);
            }
        };

        var back = function (ev) {
            if (currentStageIdx == 0) {
                return;
            }
            setupStage(currentStageIdx - 1);
        };

        var nextVerse = function () {
            if (nextVersePossible()) {
                currentVerseIndex++;
                loadCurrentVerse();
            } else {
                finish();
            }
        };

        var nextVersePossible = function () {
            return (currentVerseIndex < maxVerseIndex);
        };

        var markReadAndNextVerse = function () {

            if (!nextVersePossible()) {
                // May need to do some waiting for score logs to appear if in
                // revision mode.
                waitingForScoreLogs = true;
            }
            readingComplete(function () {
                loadStats();
                if (waitingForScoreLogs) {
                    loadScoreLogs();
                }
            });
            nextVerse();
        };


        var finish = function (depth) {
            // depth is infinite recursion protection
            if (depth === undefined) {
                depth = 0;
            }
            var go = function () {
                window.location = '/dashboard/';
            };

            // Don't do redirect if we are waiting for score logs to show.
            // But don't wait forever.
            if (waitingForScoreLogs && depth < 2) {
                setTimeout(function () { finish(depth + 1); }, 1500);
                return;
            }

            if ($.active) {
                $('body').ajaxStop(go);
            } else {
                go();
            }
        };

        var pressPrimaryButton = function () {
            $('input.primary:visible:not([disabled])').click();
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
                moveSelection(0);
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
                moveSelection(0);
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
            var POINTS_PER_WORD = 10;
            // Duplication of logic in Account.award_action_points.  NB word
            // count excludes reference for this purpose, so we don't use
            // wordList.count
            var wordCount = stripPunctuation(currentVerseStatus.text.trim()).split(/\W/).length;
            var points = wordCount * POINTS_PER_WORD;
            return points;
        };

        var adjustTypingBox = function () {
            var wordBox = getWordAt(selectedWordIndex);
            var pos = wordBox.position();
            var width;
            $('#id-test-bar').css({left: pos.left.toString() + "px",
                                   top: pos.top.toString() + "px",
                                  });
            if (isHardMode()) {
                width = "6em";
            } else {
                width = (wordBox.outerWidth() - 4).toString() + "px";
            }
            // 4 = 2 * size of #id-typing border
            inputBox.css({height: (wordBox.outerHeight() - 4).toString() + "px",
                          width: width});

        };

        var setHardMode = function (hard) {
            hardMode = hard;
            $('.current-verse').toggleClass('hard-mode', hard);
        };

        var isHardMode = function () {
            return hardMode;
        };

        var testStart = function () {
            $('.current-verse .word *').stop(true, true);
            // Don't want to see a flash of words at the beginning,
            // so hide quickly
            hideWord($('.current-verse .word span'), {'duration': 0, queue: false});
            resetTestingMistakes();
            testingStatus.text('');
            // After an certain point, we make things a bit harder.
            // Strength == 0.6 corresponds to about 10 days learning.
            setHardMode(currentVerseStatus.strength > 0.6);
            $('#id-points-target').html(' Points target: <b>' + getPointsTarget().toString() + '</b>');
        };

        var testContinue = function () {
            return true;
        };


        // === Testing logic ===

        var stripPunctuation = function (str) {
            return str.replace(/["'\.,;!?:\/#!$%\^&\*{}=\-_`~()]/g, "");
        };

        var matchWord = function (target, typed) {
            // inputs are already lowercased with punctuation stripped
            if (preferences.testingMethod === TEST_FULL_WORDS) {
                if (typed === "") { return false; }
                // for 1 letter words, don't allow any mistakes
                if (target.length === 1) {
                    return typed === target;
                }
                // After that, allow N/3 mistakes, rounded up.
                return damerauLevenshteinDistance(target, typed) <= Math.ceil(target.length / 3);
            } else {
                // TEST_FIRST_LETTER
                return (typed === target.slice(0, 1));
            }
        };

        var checkCurrentWord = function () {
            var wordIdx = selectedWordIndex;
            var word = getWordAt(wordIdx);
            var wordStr = stripPunctuation(word.text().toLowerCase());
            var typed = stripPunctuation(inputBox.val().toLowerCase());
            var moveOn = function () {
                showWord(word.find('*'));
                inputBox.val('');
                setProgress(currentStageIdx, (wordIdx + 1) / wordList.length);
                if (wordIdx + 1 === wordList.length) {
                    testComplete();
                } else {
                    moveSelectionRelative(1);
                    adjustTypingBox();
                    var isReference = getWordAt(selectedWordIndex).hasClass('reference');
                    if (isReference) {
                        fadeVerseTitle(true);
                    }

                }
            };
            if (matchWord(wordStr, typed)) {
                indicateSuccess();
                moveOn();
            } else {
                // For first letter testing, we are stricter because it is easier.
                var testMaxAttempts = (preferences.testingMethod === TEST_FIRST_LETTER
                                       ? 2
                                       : 3);
                var mistakeVal = 1 / testMaxAttempts;
                testingMistakes[wordIdx] += mistakeVal;
                if (approximatelyEqual(testingMistakes[wordIdx], 1.0, 0.001)
                    || testingMistakes[wordIdx] > 1) // can happen if switched test method in middle
                {
                    indicateFail();
                    moveOn();
                } else {
                    indicateMistake(Math.round(testingMistakes[wordIdx] / mistakeVal),
                                    testMaxAttempts);
                }
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
        // setup: Function to do stage specific setup
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

        var stageDefs = {'read': {setup: readStageStart,
                                  continueStage: readStageContinue,
                                  caption: 'Read',
                                  testMode: false,
                                  toggleMode: WORD_TOGGLE_SHOW},
                         'recall1': {setup: recall1Start,
                                     continueStage: recall1Continue,
                                     caption: 'Recall 1 - 50% initial',
                                     testMode: false,
                                     toggleMode: WORD_TOGGLE_HIDE_END},
                         'recall2': {setup: recall2Start,
                                     continueStage: recall2Continue,
                                     caption: 'Recall 2 - 100% initial',
                                     testMode: false,
                                     toggleMode: WORD_TOGGLE_HIDE_END},
                         'recall3': {setup: recall3Start,
                                     continueStage: recall3Continue,
                                     caption: 'Recall 3 - 33% missing',
                                     testMode: false,
                                     toggleMode: WORD_TOGGLE_HIDE_ALL},
                         'recall4': {setup: recall4Start,
                                     continueStage: recall4Continue,
                                     caption: 'Recall 4 - 66% missing',
                                     testMode: false,
                                     toggleMode: WORD_TOGGLE_HIDE_ALL},
                         'test': {setup: testStart,
                                  continueStage: testContinue,
                                  caption: 'Test',
                                  testMode: true,
                                  toggleMode: null},
                         'results': {setup: function () {},
                                     continueStage: function () { return true; },
                                     caption: 'Results',
                                     testMode: false,
                                     toggleMode: null},
                         'readForContext': {setup: function () {},
                                            continueStage: function () { return true; },
                                            caption: 'Read',
                                            testMode: false,
                                            toggleMode: null},
                         'readAnyway': {setup: function () {},
                                        continueStage: function () { return true; },
                                        caption: 'Read',
                                        testMode: false,
                                        toggleMode: null}
                        };

        // === Handling stage lists ===


        var setupStageList = function (verseData) {
            var strength = 0;
            if (verseData.strength != null) {
                strength = verseData.strength;
            }
            if (verseData.needs_testing) {
                currentStageList = chooseStageListForStrength(strength);
            } else {
                if (isPassageType(verseData)) {
                    currentStageList = ['readForContext'];
                } else {
                    // This can happen if the user chooses a verse set to learn
                    // and they already know the verses in it.
                    currentStageList = ['readAnyway'];
                }
            }
            setupStage(0);
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
            $.ajax({url: url,
                    dataType: 'json',
                    type: 'GET',
                    success: function (data) {
                        // This function can be called when we have already
                        // loaded the verses e.g. if the user changed the
                        // version.  Also, once some verses have been
                        // read/learnt, they will be missing.

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
                        if (callbackAfter !== undefined) {
                            callbackAfter();
                        }
                    },
                    error: learnscripture.ajaxFailed
                   });
        };


        var loadCurrentVerse = function () {
            var oldVerseStatus = currentVerseStatus;
            currentVerseStatus = versesToLearn[currentVerseIndex];
            var verse = currentVerseStatus;
            var moveOld = (oldVerseStatus !== null &&
                           isPassageType(oldVerseStatus) &&
                           // Need to cope with possibility of a gap
                           // in the passage, caused by slim_passage_for_revising()
                           (currentVerseStatus.bible_verse_number === oldVerseStatus.bible_verse_number + 1))
            if (moveOld) {
                moveOldWords();
            } else {
                $('.current-verse').children().remove();
            }

            $('.current-verse').hide(); // Hide until set up
            $('#id-verse-title').text(currentVerseStatus.reference);
            $('#id-version-select').val(verse.version.slug);
            // convert newlines to divs
            var text = verse.text;
            markupVerse(text,
                        verse.verse_set === null ||
                        verse.verse_set === undefined ||
                        verse.verse_set.set_type === SET_TYPE_SELECTION
                        ? verse.reference
                        : null);
            $('#id-loading').hide();
            $('#id-controls').show();
            if (moveOld) {
                scrollOutPreviousVerse();
                $('.current-verse').show();
            } else {
                $('.previous-verse').remove();
                $('.current-verse').show();
            }
            setupStageList(verse);
            $('.selection-set-only').toggle(!isPassageType(currentVerseStatus));

            var nextBtns = $('#id-next-verse-btn, #id-context-next-verse-btn, #id-read-anyway-vext-verse-btn');
            var finishBtn = $('#id-finish-btn');
            if (nextVersePossible()) {
                nextBtns.val('Next');
                finishBtn.show();
            } else {
                nextBtns.val('Done');
                finishBtn.hide();
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

            // First fix the height
            if (preferences.enableAnimations) {
                $('.previous-verse').css({'height': $('.previous-verse').height().toString() + 'px'});
            }

            // Now make the other words disappear
            $.each(words, function (offset, elems) {
                if (offset.toString() !== maxOffset.toString()) {
                    $(elems).remove();
                }
            });
            $('.previous-verse br').remove();

            // Now shrink the area
            var wordHeight = $('.previous-verse .word, .previous-verse .testedword').css('line-height');
            if (preferences.enableAnimations) {
                inputBox.hide();
                $('.previous-verse')
                    .css({display: 'table-cell'})
                    .animate({height: wordHeight},
                             {duration: 500,
                              complete: function () {
                                  inputBox.show().focus();
                                  adjustTypingBox()
                              }
                              });
            }
            $('.previous-verse .word, .previous-verse .testedword')
                .removeClass('word').addClass('testedword')
                .find('span')
                .removeClass('wordstart').removeClass('wordend');
        };

        var markupVerse = function (text, reference) {
            // First split lines into divs.
            $.each(text.split(/\n/), function (idx, line) {
                if (line.trim() !== '') {
                    $('.current-verse').append('<div class="line">' +
                                               line + '</div>');
                }
            });
            // Then split up into words
            var wordClass = currentVerseStatus.needs_testing ? 'word' : 'testedword';
            var wordGroups = [];

            $('.current-verse .line').each(function (idx, elem) {
                wordGroups.push($(elem).text().trim().split(/ |\n/));
            });
            wordList = [];
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
            if (currentVerseStatus.needs_testing && reference !== null) {
                parts = reference.split(/\b/);
                replace = [];
                $.each(parts, function(j, word) {
                    if (word.trim() == "") {
                        return;
                    }
                    if (word == ":" || word == "-") {
                        replace.push('<span class="colon">' + word + '</span>');
                        return;
                    }
                    replace.push(makeNormalWord(word, "word reference"));
                    wordList.push(wordNumber);
                    wordNumber++;
                });
                $('.current-verse').append('<br/>' + replace.join(' '));

            }

            $('.current-verse .word').click(function (ev) {
                if (!currentStage.testMode) {
                    toggleWord($(this));
                }
            });
        };

        // ========== Stats/scores loading ==========

        var loadStats = function () {
            $.ajax({url: '/api/learnscripture/v1/sessionstats/?format=json&r=' +
                    Math.floor(Math.random() * 1000000000).toString(),
                    dataType: 'json',
                    type: 'GET',
                    success: function (data) {
                        $('#id-stats-block').html(data.stats_html);
                    }});
        };

        var loadScoreLogs = function () {
            if ($('#id-points-enabled').length === 0) {
                waitingForScoreLogs = false;
                return;
            }
            $.ajax({url: '/api/learnscripture/v1/scorelogs/?format=json&r=' +
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
                    waitingForScoreLogs = false;
                    return;
                }
                var scoreLog = scoreLogs[0];
                var doRest = function () { addScoreLog(scoreLogs.slice(1))};
                var divId = 'id-score-log-' + scoreLog.id.toString();
                if ($('#' + divId).length === 0) {
                    // Put new ones at top
                    var newSL = $('<div id="' + divId +
                                  '" class="score-log score-log-type-' + scoreLog.reason + '"' +
                                  '>' + scoreLog.points + '</div>');
                    // Need some tricks to get height of new element without
                    // showing.
                    newSL.css({'position': 'absolute', 'visibility': 'hidden', 'display': 'block',
                               'width': container.width().toString() + "px"});
                    container.prepend(newSL);
                    var h = newSL.height();
                    newSL.removeAttr('style');

                    newSL.css({opacity: 0,
                               height: 0});
                    var newProps = {opacity: 1,
                                    height: h.toString() + "px"};
                    if (preferences.enableAnimations) {
                        newSL.animate(newProps,
                                      {duration: 300,
                                       complete: doRest}
                                     );
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
            if (ev.which === 27) {
                // ESC
                ev.preventDefault();
                inputBox.val('');
                return;
            }
            if (ev.which === 32 || ev.which === 13) {
                ev.preventDefault();
                if (currentStage.testMode) {
                    if (preferences.testingMethod === TEST_FULL_WORDS) {
                        checkCurrentWord();
                    }
                }
                return;
            }
            // Any character
            if (currentStage.testMode && preferences.testingMethod === TEST_FIRST_LETTER) {
                if (alphanumeric(ev)) {
                    ev.preventDefault();
                    // Put it there ourselves, so it is ready for checkCurrentWord()
                    inputBox.val(String.fromCharCode(ev.which));
                    checkCurrentWord();
                }
            }

        };

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
            case 98: // 'b'
                back();
                return;
            case 110: // 'n'
                next();
                return;
            case 106: // 'j'
                moveSelectionRelative(-1);
                return;
            case 107: // 'k'
                moveSelectionRelative(1);
                return;
            case 32: // Space
                ev.preventDefault(); // Many devices scroll on space bar
                toggleWord(getWordAt(selectedWordIndex));
                return;
            case 13: // Enter
                if (tagName === 'a') {
                    return;
                }
                pressPrimaryButton();
                break;
            }
        };

        var versionSelectChanged = function (ev) {
            $.ajax({url: '/api/learnscripture/v1/changeversion/',
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
            $.ajax({url: '/api/learnscripture/v1/skipverse/',
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
            $.ajax({url: '/api/learnscripture/v1/cancellearningverse/',
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

        var finishBtnClick = function (ev) {
            // Skip to end, which skips everything in between
            var verse = versesToLearn[maxVerseIndex];
            $.ajax({url: '/api/learnscripture/v1/skipverse/',
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
        var setupLearningControls = function () {
            isLearningPage = ($('#id-verse-wrapper').length > 0);
            if (!isLearningPage) {
                return;
            }

            receivePreferences(learnscripture.getPreferences());
            // Listen for changes to preferences.
            $('#id-preferences-data').bind('preferencesSet', function (ev, prefs) {
                receivePreferences(prefs);
            });

            inputBox = $('#id-typing');
            inputBox.keydown(inputKeyDown);
            testingStatus = $('#id-testing-status');
            $('#id-next-btn').show().click(next);
            $('#id-back-btn').show().click(back);
            $('#id-next-verse-btn').click(nextVerse);
            $('#id-context-next-verse-btn, #id-read-anyway-next-verse-btn').click(markReadAndNextVerse);
            $('#id-version-select').change(versionSelectChanged);
            $('#id-help-btn').click(function (ev) {
                if (preferences.enableAnimations) {
                    $('#id-help').toggle('fast');
                } else {
                    $('#id-help').toggle();
                }
                $('#id-help-btn').button('toggle');
            });
            $('#id-skip-verse-btn').click(skipVerse);
            $('#id-cancel-learning-btn').click(cancelLearning);
            $('#id-finish-btn').click(finishBtnClick);
            $(window).resize(function () {
                if (currentStage !== null &&
                    currentStage.testMode) {
                    adjustTypingBox();
                }
            });
            if (typeof operamini !== "undefined") {
                // Opera Mini is a thin client browser and doesn't support
                // responding to key presses. It does, however, support
                // input onchange events, which fires when the user preses 'Done'
                inputBox.change(function (ev) {
                    ev.preventDefault();
                    checkCurrentWord();
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
            if (preferences.testingMethod === TEST_FIRST_LETTER) {
                $('.test-full').hide();
                $('.test-first-letter').show();
            } else {
                $('.test-full').show();
                $('.test-first-letter').hide();
            }
        };


        // === Exports ===

        learnscripture.setupLearningControls = setupLearningControls;
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
    learnscripture.setupLearningControls();
});
