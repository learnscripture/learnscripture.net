// Learning and testing functionality for learnscripture.net

var learnscripture =
    (function(learnscripture, $) {
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

        var currentVerseStatus = null;

        // word toggling and selection

        // For speed in test mode, where we have to keep up with typing,
        // we tag all the words with ids, and keep track of the selected id
        // and word number
        var selectedWordIndex = null;

        var moveSelection = function(pos) {
            if (pos == selectedWordIndex) {
                return;
            }
            if (selectedWordIndex != null) {
                getWordAt(selectedWordIndex).removeClass('selected');
            }
            selectedWordIndex = pos;
            getWordAt(selectedWordIndex).addClass('selected');
        };

        var getWordAt = function(index) {
            return $('#id-word-' + index.toString());
        };

        var getWordNumber = function(word) {
            return $('.current-verse .word').index(word);
        };

        var moveSelectionRelative = function(distance) {
            var i = selectedWordIndex;
            var pos = Math.min(Math.max(0, i + distance),
                               wordList.length - 1);
            moveSelection(pos);
        };

        var isHidden = function(word) {
            return word.css('opacity') == '0';
        };

        var hideWord = function(word, options) {
            if (preferences.enableAnimations) {
                if (options == undefined) {
                    options = {duration: 300, queue: false};
                }
                word.animate({'opacity': '0'}, options);
            } else {
                word.css({'opacity':'0'});
            }
        };

        var showWord = function(word) {
            if (preferences.enableAnimations) {
                word.animate({'opacity': '1'}, {duration: 300, queue: false});
            } else {
                word.css({'opacity': '1'});
            }
        };

        var toggleWord = function(word) {
            var wordNumber = getWordNumber(word);
            moveSelection(wordNumber);

            var wordEnd = word.find('.wordend');
            var wordStart = word.find('.wordstart');
            var toggleMode = currentStage.toggleMode;
            if (toggleMode == WORD_TOGGLE_SHOW) {
                return;
            } else if (toggleMode == WORD_TOGGLE_HIDE_END) {
                if (isHidden(wordEnd)) {
                    markRevealed(wordNumber);
                    showWord(wordEnd);
                }
            } else if (toggleMode == WORD_TOGGLE_HIDE_ALL) {
                if (isHidden(wordStart)) {
                    markRevealed(wordNumber);
                    showWord(wordStart);
                } else if (isHidden(wordEnd)) {
                    markRevealed(wordNumber);
                    showWord(wordEnd);
                }
            }
        };

        var flashMsg = function(elements) {
            if (preferences.enableAnimations) {
                elements.css({opacity:1}).animate({opacity: 0},
                                                  {duration: 1000, queue: false});
            } else {
                elements.css({opacity:1});
            }
        };

        var indicateSuccess = function() {
            var word = getWordAt(selectedWordIndex);
            word.addClass('correct');
            flashMsg(testingStatus.attr({'class': 'correct'}).text("Correct!"));
        };

        var indicateMistake = function(mistakes, maxMistakes) {
            var msg = "Try again! (" + mistakes.toString() + "/" + maxMistakes.toString() + ")";
            flashMsg(testingStatus.attr({'class': 'incorrect'}).text(msg));
        };

        var indicateFail = function() {
            var word = getWordAt(selectedWordIndex);
            word.addClass('incorrect');
            flashMsg(testingStatus.attr({'class': 'incorrect'}).text("Incorrect"));
        };

        var stripPunctuation = function(str) {
            return str.replace(/["'\.,;!?:\/#!$%\^&\*{}=\-_`~()]/g,"");
        };

        var matchWord = function(target, typed) {
            // inputs are already lowercased with punctuation stripped
            if (preferences.testingMethod == TEST_FULL_WORDS) {
                if (typed == "") return false;
                // for 1 letter words, don't allow any mistakes
                if (target.length == 1) {
                    return typed == target;
                }
                // After that, allow N/3 mistakes, rounded up.
                return levenshteinDistance(target, typed) <= Math.ceil(target.length / 3);
            } else {
                // TEST_FIRST_LETTER
                return (typed == target.slice(0, 1));
            }
        };

        var readingComplete = function(callbackAfter) {
            $.ajax({url: '/api/learnscripture/v1/actioncomplete/',
                    dataType: 'json',
                    type: 'POST',
                    data: {
                        verse_status: JSON.stringify(currentVerseStatus, null, 2),
                        stage: STAGE_TYPE_READ,
                    },
                    success: function() {
                        callbackAfter();
                    }
                   });
        }

        var testComplete = function() {
            var accuracy = 0;
            var mistakes = 0;
            $.each(testingMistakes, function(key, val) {
                mistakes += val;
            });
            accuracy = 1 - (mistakes / (currentStage.testMaxAttempts * wordList.length));
            $.ajax({url: '/api/learnscripture/v1/actioncomplete/',
                    dataType: 'json',
                    type: 'POST',
                    data: {
                        verse_status: JSON.stringify(currentVerseStatus, null, 2),
                        stage: STAGE_TYPE_TEST,
                        accuracy: accuracy
                    }});
            var accuracyPercent = Math.floor(accuracy * 100).toString()
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
            completeStageGroup();
            if (accuracyPercent < 60) {
                $('#id-result-suggestion').text("We recommend a bit a more practice " +
                                                "with this before continuing");
                $('#id-more-practice-btn').addClass('primary').show();
                $('#id-next-verse-btn').removeClass('primary');
                $('#id-more-practice-btn').unbind().click(function() {
                    if (accuracyPercent < 10) {
                        currentStageList = chooseStageListForStrength(0);
                    } else if (accuracyPercent < 30) {
                        currentStageList = ['read', 'recall2', 'recall4', 'testFull'];
                    } else {
                        currentStageList = ['recall2', 'recall4', 'testFull'];
                    }
                    setupStage(0);
                });
            } else {
                $('#id-result-suggestion').text("");
                $('#id-more-practice-btn').removeClass('primary').hide();
                $('#id-next-verse-btn').addClass('primary');
            }


            showInstructions("results");
        };

        var completeStageGroup = function() {
            spentStagesCount += currentStageList.length;
            currentStage = stageDefs['results'];
            currentStageList = [currentStage];
            currentStageIdx = 0;
            setNextPreviousBtns();
        };

        var checkCurrentWord = function() {
            var wordIdx = selectedWordIndex;
            var word = getWordAt(wordIdx);
            var wordStr = stripPunctuation(word.text().toLowerCase());
            var typed = stripPunctuation(inputBox.val().toLowerCase());
            var moveOn = function() {
                showWord(word.find('*'));
                inputBox.val('');
                setProgress(currentStageIdx, (wordIdx + 1)/ wordList.length);
                if (wordIdx + 1 == wordList.length) {
                    testComplete();
                } else {
                    moveSelectionRelative(1);
                }
            };
            if (matchWord(wordStr, typed)) {
                indicateSuccess();
                moveOn();
            } else {
                testingMistakes[wordIdx] += 1;
                if (testingMistakes[wordIdx] == currentStage.testMaxAttempts) {
                    indicateFail();
                    moveOn();
                } else {
                    indicateMistake(testingMistakes[wordIdx], currentStage.testMaxAttempts);
                }
            }
        };

        // ---- Stages ----

        // -- reading stage --
        var readStage = function() {
            showWord($('.current-verse .word *'));
        };

        // recall type 1 - FullAndInitial
        //    Some full words, some initial letters only

        var makeFullAndInitialContinue = function(initialFraction) {
            // Factory function that generates a function for
            // FullAndInitial stage continue function

            var recallContinue = function() {
                if (untestedWords.length == 0) {
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

        var makeInitialAndMissingContinue = function(missingFraction) {
            // Factory function that generates a function for
            // InitialAndMissing stage continue function

            var recallContinue = function() {
                if (untestedWords.length == 0) {
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

        var makeRecallStart = function(continueFunc) {
            // Factory function that returns a stage starter
            // function for recall stages
            return function() {
                untestedWords = wordList.slice(0);
                testedWords = [];
                continueFunc();
            };

        };

        // Testing stages

        var resetTestingMistakes = function() {
            testingMistakes = {};
            for (var i = 0; i < wordList.length; i++) {
                testingMistakes[i] = 0;
            }
        };

        var testStart = function() {
            // Don't want to see a flash of words at the beginning,
            // so hide quickly
            hideWord($('.current-verse .word span'), {'duration': 0, queue:false});
            resetTestingMistakes();
            testingStatus.text('');
        };

        var testContinue = function() {
            return true;
        };

        // Utilities for stages
        var setProgress = function(stageIdx, fraction) {
            $('#' + progressRowId(stageIdx) + ' progress').val(fraction * 100);
        };

        var markRevealed = function(wordNumber) {
            var p = testedWords.indexOf(wordNumber);
            if (p != -1) {
                testedWords.splice(p, 1);
            }
            if (untestedWords.indexOf(wordNumber) == -1) {
                untestedWords.push(wordNumber);
            }
        };

        var chooseN = function(aList, n) {
            aList = aList.slice(0);
            var i;
            var chosen = [];
            for(i = 0; i < n; i++) {
                if (aList.length == 0) {
                    break;
                }
                var pos = Math.floor(Math.random()*aList.length);
                var item = aList[pos];
                aList.splice(pos, 1);
                chosen.push(item);
            }
            return chosen;
        };

        var setUnion = function(list1, list2) {
            var output = list1.slice(0);
            for (var i = 0; i < list2.length; i++) {
                var item = list2[i];
                if (output.indexOf(item) == -1) {
                    output.push(item);
                }
            }
            return output;
        };

        var setRemove = function(list1, list2) {
            // Return a new list which is a copy of list1 with the items
            // of list2 removed
            var output = list1.slice(0);
            for (var i = 0; i < list2.length; i++) {
                var p = output.indexOf(list2[i]);
                if (p != -1) {
                    output.splice(p, 1);
                }
            }
            return output;
        };

        var getTestWords = function(testFraction) {
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
            var selector = $.map(toTest, function(elem, idx) {
                return '.current-verse .word:eq(' + elem.toString() + ')';
            }).join(', ');
            return $(selector);
        };

        var showInstructions = function(stageName) {
            if (preferences.enableAnimations) {
                // Fade out old instructions, fade in the new
                $('#id-instructions div').animate(
                    {opacity: 0},
                    {duration: 150,
                     queue: false,
                     complete: function() {
                         $('#id-instructions div').hide();
                         $('#id-instructions .instructions-' + stageName).show().animate({opacity: 1}, 150); }});
            } else {
                $('#id-instructions div').css({opacity: 0});
                $('#id-instructions div').hide();
                $('#id-instructions .instructions-' + stageName).show().css({opacity: 1});
            }
        };

        var setNextPreviousBtns = function() {
            enableBtn($('#id-next-btn'), currentStageIdx < currentStageList.length - 1);
            enableBtn($('#id-back-btn'), currentStageIdx > 0);
        };

        // Stages definition

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
        // caption: Caption to put next to the progress bar
        //
        // testMode: boolean that is true if in testing
        //
        // toggleMode: contstant defining how clicking on words should react

        var stageDefs = {'read': {setup: readStage,
                                  continueStage: function() { return false; },
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
                         'testFull': {setup: testStart,
                                      continueStage: testContinue,
                                      caption: 'Test',
                                      testMode: true,
                                      testMaxAttempts: 3,
                                      toggleMode: null},
                         // We use a separate stage for this for the sake of
                         // showing the right instructions and having a
                         // different testMaxAttempts
                         'testFirstLetter': {setup: testStart,
                                             continueStage: testContinue,
                                             caption: 'Test',
                                             testMode: true,
                                             testMaxAttempts: 2,
                                             toggleMode: null},
                         'results': {setup: function() {},
                                     continueStage: function() { return true;},
                                     caption: 'Results',
                                     testMode: false,
                                     toggleMode: null},
                         'readForContext': {setup: function() {},
                                            continueStage: function() { return true;},
                                            caption: 'Read',
                                            testMode: false,
                                            toggleMode: null}
                        };


        var progressRowId = function(stageIdx) {
            return 'id-progress-row-' + (currentStageIdx + spentStagesCount).toString();
        };

        var setupStage = function(idx) {
            // set the globals
            var currentStageName = currentStageList[idx];
            if (preferences.testingMethod == TEST_FIRST_LETTER &&
                currentStageName == 'testFull') {
                currentStageName = 'testFirstLetter';
            }
            currentStageIdx = idx;
            currentStage = stageDefs[currentStageName];

            // Common clearing, and stage specific setup
            $('.current-verse .correct, .current-verse .incorrect').removeClass('correct').removeClass('incorrect');
            $('#id-progress-summary').text("Stage " + (currentStageIdx + 1).toString() + "/" + currentStageList.length.toString());
            currentStage.setup();
            setNextPreviousBtns();
            if (currentStage.testMode) {
                $('#id-test-bar').show();
                inputBox.focus();
            } else {
                inputBox.blur();
                $('#id-test-bar').hide();
            }

            showInstructions(currentStageName);
            // reset selected word
            moveSelection(0);

            // Create progress bar for this stage.
            var pRowId = progressRowId(currentStageIdx);
            if (!document.getElementById(pRowId)) {
                var progressRow = $(
                    '<tr id="' + pRowId + '" style="display:none;">' +
                        '<th>' + currentStage.caption + '</th>' +
                        '<td><progress value="0" max="100">0%</progress>' +
                        '</td></tr>');
                $('.progress table').prepend(progressRow);
                if (preferences.enableAnimations) {
                    progressRow.show('200');
                } else {
                    progressRow.show();
                }

            }
            setProgress(currentStageIdx, 0);
            $('th.currenttask').removeClass('currenttask');
            $('#' + pRowId + ' th').addClass('currenttask');
        };

        // -- Moving between stages --

        var next = function(ev) {
            if (currentStage.continueStage()) {
                return;
            }
            if (currentStageIdx < currentStageList.length - 1) {
                setProgress(currentStageIdx, 1);
                setupStage(currentStageIdx + 1);
            }
        };

        var back = function(ev) {
            if (currentStageIdx == 0) {
                return;
            }
            $('#' + progressRowId(currentStageIdx)).remove();
            setupStage(currentStageIdx - 1);
        };

        var enableBtn = function(btn, state) {
            if (state) {
                btn.removeAttr('disabled');
            } else {
                btn.attr('disabled', 'disabled');
            }
        };

        // -- event handlers --
        var alphanumeric = function(ev) {
            return ((!ev.ctrlKey && !ev.altKey && (
                (ev.which >= 65 && ev.which <= 90) ||
                    (ev.which >= 48 && ev.which <= 57)
            )));
        }

        var inputKeyDown = function(ev) {
            if (ev.which == 27) {
                // ESC
                ev.preventDefault();
                inputBox.val('');
                return;
            }
            if (ev.which == 32) {
                ev.preventDefault();
                if (currentStage.testMode) {
                    if (preferences.testingMethod == TEST_FULL_WORDS) {
                        checkCurrentWord();
                    }
                }
            }
            if (ev.which == 13) {
                pressPrimaryButton();
            }
            // Any character
            if (currentStage.testMode && preferences.testingMethod == TEST_FIRST_LETTER) {
                if (alphanumeric(ev)) {
                    ev.preventDefault()
                    // Put it there ourselves, so it is ready for checkCurrentWord()
                    inputBox.val(String.fromCharCode(ev.which));
                    checkCurrentWord();
                }
            }

        };

        var pressPrimaryButton = function() {
            $('input.primary:visible:not([disabled])').click();
        };

        var docKeyPress = function(ev) {
            if (currentStage.testMode) {
                return;
            }
            var tagName = ev.target.tagName.toLowerCase();
            if (tagName == 'input' ||
                tagName == 'select' ||
                tagName == 'textarea') {
                return;
            }
            // Some android phones will bring up box for searching or something on almost
            // any key press, and many devices will scroll on space bar:
            ev.preventDefault();
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
                toggleWord(getWordAt(selectedWordIndex));
                return;
            case 13: // Enter
                if (tagName == 'a') {
                    return;
                }
                pressPrimaryButton();
            }
        };

        var versionSelectChanged = function(ev) {
            $.ajax({url: '/api/learnscripture/v1/changeversion/',
                    dataType: 'json',
                    type: 'POST',
                    data: {
                        verse_status: JSON.stringify(currentVerseStatus, null, 2),
                        new_version_slug: $('#id-version-select').val()
                    },
                    success: function() {
                        // We pretend there is no 'old verse' if we changed
                        // version, to avoid the complications with moving the
                        // old verse.
                        currentVerseStatus = null;
                        nextVerse();
                    },
                    error: handlerAjaxError
                   });
        };

        var bindDocKeyPress = function() {
            if (isLearningPage) {
                $(document).bind('keypress', docKeyPress);
            }
        }
        var unbindDocKeyPress = function() {
            if (isLearningPage) {
                $(document).unbind('keypress');
            }
        }

        var nextVerse = function() {
            $('.progress table tr').remove();
            loadVerse();
        };

        var markReadAndNextVerse = function() {
            readingComplete(nextVerse);
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
                return ['read', 'recall1', 'recall2', 'recall3', 'recall4', 'testFull'];
            } else if (strength < 0.07) {
                // e.g. first test was 70% or less, this is second test
                return ['recall2', 'testFull'];
            } else {
                return ['testFull'];
            }
        };

        var setupStageList = function(verseData) {
            var strength = 0;
            if (verseData.strength != null) {
                strength = verseData.strength;
            }
            if (verseData.needs_testing) {
                currentStageList = chooseStageListForStrength(strength);
            } else {
                currentStageList = ['readForContext'];
            }
            setupStage(0);
        };

        var scrollOutPreviousVerse = function() {
            var words = {}; // offset:node list of word spans
            var maxOffset = null;
            $('.previous-verse .word, .previous-verse .testedword').each(function(idx, elem) {
                var offset = $(elem).offset().top;
                if (maxOffset == null || offset > maxOffset) {
                    maxOffset = offset;
                }
                // Build up elements for the words in groups
                if (words[offset] == undefined) {
                    words[offset] = [];
                }
                words[offset].push(elem);
            });

            // First fix the height
            if (preferences.enableAnimations) {
                $('.previous-verse').css({'height': $('.previous-verse').height().toString()});
            }

            // Now make the other words disappear
            $.each(words, function(offset, elems) {
                if (offset != maxOffset) {
                        $(elems).remove();
                }
            });
            $('.previous-verse br').remove();

            // Now shrink the area
            var wordHeight = $('.previous-verse .word, .previous-verse .testedword').css('line-height');
            if (preferences.enableAnimations) {
                $('.previous-verse')
                    .css({display: 'table-cell'})
                    .animate({height: wordHeight},
                             {duration: 500});
            }
            $('.previous-verse .word, .previous-verse .testedword')
                .removeClass('word').addClass('testedword')
                .find('span')
                .removeClass('wordstart').removeClass('wordend');
        }

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

        var isPassageType = function(verseData) {
            return (verseData &&
                    verseData.verse_choice.verse_set &&
                    verseData.verse_choice.verse_set.set_type ==
                    SET_TYPE_PASSAGE)
        };


        var loadVerse = function() {
            $.ajax({url: '/api/learnscripture/v1/nextverse/?format=json&r=' +
                    Math.floor(Math.random()*1000000000).toString(),
                    dataType: 'json',
                    type: 'GET',
                    success: function(data) {
                        var oldVerseStatus = currentVerseStatus;
                        currentVerseStatus = data;
                        if (isPassageType(oldVerseStatus)) {
                            moveOldWords();
                        } else {
                            $('.current-verse').children().remove();
                        }
                        $('.current-verse').hide(); // Hide until set up
                        $('#id-verse-title').text(data.reference);
                        // convert newlines to divs
                        var text = data.text;
                        if (data.verse_choice.verse_set == null ||
                            data.verse_choice.verse_set.set_type == SET_TYPE_SELECTION) {
                            text = text + '\n' + data.reference;
                        }
                        $.each(text.split(/\n/), function(idx, line) {
                            if (line.trim() != '') {
                                $('.current-verse').append('<div class="line">' +
                                                      line + '</div>');
                            }
                        });
                        var versionText = "Version: " + data.version.full_name +
                            " (" + data.version.short_name + ") |";
                        $('#id-version-name').text(versionText);

                        if (data.version.url != "") {
                            var url = data.version.url.replace('%s', encodeURI(data.reference)).replace('%20', '+');
                            $('#id-browse-link').show().find('a').attr('href', url);
                        } else {
                            $('#id-browse-link').hide();
                        }
                        $('#id-version-select').val(data.version.slug);
                        markupVerse();
                        $('#id-loading').hide();
                        $('#id-controls').show();
                        setupStageList(data);

                        if (isPassageType(oldVerseStatus)) {
                            scrollOutPreviousVerse();
                            $('.current-verse').show();
                        } else {
                            $('.previous-verse').remove()
                            $('.current-verse').show();
                        }

                    },
                    error: function(jqXHR, textStatus, errorThrown) {
                        if (jqXHR.status == 404) {
                            $('#id-loading').hide();
                            $('#id-controls').hide();
                            $('#id-no-verse-queue').show();
                        } else {
                            handlerAjaxError(jqXHR, textStatus, errorThrown);
                        }
                    }
                   });
        };

        var markupVerse = function() {
            var wordClass = currentVerseStatus.needs_testing ? 'word' : 'testedword';
            var wordGroups = [];

            $('.current-verse .line').each(function(idx, elem) {
                wordGroups.push($(elem).text().trim().split(/ |\n/));
            });
            wordList = [];
            var replacement = [];
            var wordNumber = 0;
            for(var i = 0; i < wordGroups.length; i++) {
                var group = wordGroups[i];
                group = $.map(group, function(word, j) {
                    if (stripPunctuation(word) == "") {
                        return null;
                    } else {
                        return word;
                    }
                });
                var replace = [];
                $.each(group, function(j, word) {
                    var start = word.match(/\W*./)[0];
                    var end = word.slice(start.length);
                    replace.push ('<span id="id-word-' + wordNumber.toString() +
                                  '" class=\"' + wordClass + '\">' +
                                  '<span class="wordstart">' + start +
                                  '</span><span class="wordend">' + end +
                                  '</span></span>');
                    wordList.push(wordNumber);
                    wordNumber++;

                });
                replacement.push(replace.join(' '));
            }
            $('.current-verse').html(replacement.join('<br/>'));
            $('.current-verse .word').click(function(ev) {
                if (!currentStage.testMode) {
                    toggleWord($(this));
                }
            });
        };

        // TODO - implement retrying and a queue and UI for manual
        // retrying.
        // Also handle case of user being logged out.
        var handlerAjaxError = function(jqXHR, textStatus, errorThrown) {
            console.log("AJAX error: %s, %s, %o", textStatus, errorThrown, jqXHR);
        };



        // setup and wiring
        var setupLearningControls = function(prefs) {
            isLearningPage = ($('#id-verse-wrapper').length > 0);
            if (!isLearningPage) {
                return;
            }

            preferences = learnscripture.getPreferences();
            // Listen for changes to preferences
            $('#id-preferences-data').bind('preferencesSet', function(ev, prefs) {
                console.log('preferences received:');
                console.log(prefs);
                preferences = prefs;
            });

            inputBox = $('#id-typing');
            inputBox.keydown(inputKeyDown);
            testingStatus = $('#id-testing-status');
            bindDocKeyPress();
            $('#id-next-btn').show().click(next);
            $('#id-back-btn').show().click(back);
            $('#id-next-verse-btn').click(nextVerse);
            $('#id-context-next-verse-btn').click(markReadAndNextVerse);
            $('#id-version-select').change(versionSelectChanged);
            $('#id-help-btn').click(function(ev) {
                if (preferences.enableAnimations) {
                    $('#id-help').toggle('fast');
                } else {
                    $('#id-help').toggle();
                }
                $('#id-help-btn').button('toggle');
            });
            nextVerse();
        };

        learnscripture.handlerAjaxError = handlerAjaxError;
        learnscripture.setupLearningControls = setupLearningControls;
        learnscripture.unbindDocKeyPress = unbindDocKeyPress;
        learnscripture.bindDocKeyPress = bindDocKeyPress;
        return learnscripture;

    })(learnscripture || {}, $);



/*

  Copyright (c) 2006. All Rights reserved.
  If you use this script, please email me and let me know, thanks!

  Andrew Hedges
  andrew (at) hedges (dot) name

  If you want to hire me to write JavaScript for you, see my resume.
  http://andrew.hedges.name/resume/

*/

// calculate the Levenshtein distance between a and b
var levenshteinDistance = function(a, b) {
    var cost;

    var m = a.length;
    var n = b.length;

    // make sure a.length >= b.length to use O(min(n,m)) space, whatever that is
    if (m < n) {
        var c=a;a=b;b=c;
        var o=m;m=n;n=o;
    }

    var r = new Array();
    r[0] = new Array();
    for (var c = 0; c < n+1; c++) {
        r[0][c] = c;
    }

    for (var i = 1; i < m+1; i++) {
        r[i] = new Array();
        r[i][0] = i;
        for (var j = 1; j < n+1; j++) {
            cost = (a.charAt(i-1) == b.charAt(j-1))? 0: 1;
            r[i][j] = min3(r[i-1][j]+1,r[i][j-1]+1,r[i-1][j-1]+cost);
        }
    }

    return r[m][n];
};

// return the smallest of the three values passed in
var min3 = function(x,y,z) {
    if (x < y && x < z) return x;
    if (y < x && y < z) return y;
    return z;
};

$(document).ready(function() {
    learnscripture.setupLearningControls();
});
