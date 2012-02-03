// Learning and testing functionality for learnscripture.net

var learnscripture =
    (function(learnscripture, $) {
        // Controls
        var inputBox = null;

        // -- Constants and globals --
        var WORD_TOGGLE_SHOW = 0;
        var WORD_TOGGLE_HIDE_END = 1;
        var WORD_TOGGLE_HIDE_ALL = 2;

        var TEST_TYPE_FULL = 'TEST_TYPE_FULL';
        var TEST_TYPE_QUICK = 'TEST_TYPE_QUICK';

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

        var moveSelection = function(word) {
            $('.word.selected').removeClass('selected');
            word.addClass('selected');
        };

        var getSelectedWordIndex = function() {
            return $('.word').index($('.word.selected'));
        };

        var getWordCount = function() {
            return $('.word').length;
        };

        var getWordAt = function(index) {
            return $($('.word').get(index));
        };

        var getWordNumber = function(word) {
            return $('.word').index(word);
        };

        var moveSelectionRelative = function(distance) {
            var i = getSelectedWordIndex();
            var pos = Math.min(Math.max(0, i + distance),
                               getWordCount() - 1);
            var word = getWordAt(pos);
            if (word.length != 0) {
                moveSelection(word);
            }
        };

        var isHidden = function(word) {
            return word.css('opacity') == '0';
        };

        var hideWord = function(word, options) {
            if (options == undefined) {
                options = {duration: 300, queue: false};
            }
            word.animate({'opacity': '0'}, options);
        };

        var showWord = function(word) {
            word.animate({'opacity': '1'}, {duration: 300, queue: false});
        };

        var toggleWord = function(word) {
            moveSelection(word);
            var wordNumber = getWordNumber(word);

            var wordEnd = word.find('.wordend');
            var wordStart = word.find('.wordstart');
            var toggleMode = currentStage.toggleMode;
            if (toggleMode == WORD_TOGGLE_SHOW) {
                return;
            } else if (toggleMode == WORD_TOGGLE_HIDE_END) {
                if (isHidden(wordEnd)) {
                    markRevealed(wordNumber);
                    showWord(wordEnd);
                } else {
                    hideWord(wordEnd);
                }
            } else if (toggleMode == WORD_TOGGLE_HIDE_ALL) {
                if (isHidden(wordStart)) {
                    markRevealed(wordNumber);
                    showWord(wordStart);
                } else if (isHidden(wordEnd)) {
                    markRevealed(wordNumber);
                    showWord(wordEnd);
                } else {
                    hideWord(wordStart);
                    hideWord(wordEnd);
                }
            }
        };

        var flashMsg = function(elements) {
            elements.css({opacity:1}).animate({opacity: 0},
                                              {duration: 1000, queue: false});
        };

        var indicateSuccess = function() {
            var word = getWordAt(getSelectedWordIndex());
            word.addClass('correct');
            flashMsg($('#id-testing-status').attr({'class': 'correct'}).text("Correct!"));
        };

        var indicateMistake = function(mistakes, maxMistakes) {
            var msg = "Try again! (" + mistakes.toString() + " out of " + maxMistakes.toString() + ")";
            flashMsg($('#id-testing-status').attr({'class': 'incorrect'}).text(msg));
        };

        var indicateFail = function() {
            var word = getWordAt(getSelectedWordIndex());
            word.addClass('incorrect');
            flashMsg($('#id-testing-status').attr({'class': 'incorrect'}).text("Incorrect"));
        };

        var stripPunctuation = function(str) {
            return str.replace(/["'\.,;!?:\/#!$%\^&\*{}=\-_`~()]/g,"");
        };

        var matchWord = function(target, typed) {
            // inputs are already lowercased with punctuation stripped
            if (currentStage.testType == TEST_TYPE_FULL) {
                if (typed == "") return false;
                // for 1 letter words, don't allow any mistakes
                if (target.length == 1) {
                    return typed == target;
                }
                // After that, allow N/3 mistakes, rounded up.
                return levenshteinDistance(target, typed) <= Math.ceil(target.length / 3);
            } else {
                // TEST_TYPE_QUICK:
                return (typed == target.slice(0, 1));
            }
        };

        var testComplete = function() {
            var score = 0;
            var mistakes = 0;
            $.each(testingMistakes, function(key, val) {
                mistakes += val;
            });
            score = 1 - (mistakes / (currentStage.testMaxAttempts * wordList.length));
            $.ajax({url: '/api/learnscripture/v1/actioncomplete/',
                    dataType: 'json',
                    type: 'POST',
                    data: {
                        user_verse_status_id: currentVerseStatus.id,
                        stage: currentStage.testType,
                        score: score
                    }});
            $('#id-score').text(Math.floor(score * 100).toString() + "%");
            completeStageGroup();
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
            var wordIdx = getSelectedWordIndex();
            var word = getWordAt(wordIdx);
            var wordStr = stripPunctuation(word.text().toLowerCase());
            var typed = stripPunctuation(inputBox.val().toLowerCase());
            var moveOn = function() {
                showWord(word.find('*'));
                inputBox.val('');
                setProgress(currentStageIdx, (wordIdx + 1)/ wordList.length);
                if (getSelectedWordIndex() + 1 == getWordCount()) {
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
            showWord($('.word *'));
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
                moveSelection($('.word').first());
                var testWords = getTestWords(initialFraction);
                showWord($('.word *'));
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
                moveSelection($('.word').first());
                var testWords = getTestWords(missingFraction);
                hideWord($('.wordend'));
                showWord($('.wordstart'));
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

        var testFullStart = function() {
            // Don't want to see a flash of words at the beginning,
            // so hide quickly
            hideWord($('.word span'), {'duration': 0, queue:false});
            resetTestingMistakes();
        };

        var testFullContinue = function() {
            return true;
        };

        var testQuickStart = testFullStart;
        var testQuickContinue = testFullContinue;

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
                return '.word:eq(' + elem.toString() + ')';
            }).join(', ');
            return $(selector);
        };

        var showInstructions = function(stageName) {
            // Fade out old instructions, fade in the new
            $('#id-instructions div').animate(
                {opacity: 0},
                {duration: 150,
                 queue: false,
                 complete: function() {
                     $('#id-instructions div').hide();
                     $('#id-instructions .instructions-' + stageName).show().animate({opacity: 1}, 150); }});
        };

        var setNextPreviousBtns = function() {
            enableBtn($('#id-next-btn'), currentStageIdx < currentStageList.length - 1);
            enableBtn($('#id-back-btn'), currentStageIdx > 0);
        };

        var isScrolledIntoView = function(div) {
            var docViewTop = $(window).scrollTop();
            var docViewBottom = docViewTop + $(window).height();

            var elemTop = div.offset().top;
            var elemBottom = elemTop + div.height();

            return ((elemBottom >= docViewTop) && (elemTop <= docViewBottom)
                    && (elemBottom <= docViewBottom) &&  (elemTop >= docViewTop) );
        };

        var focusTypingInputCarefully = function() {
            var instructions = $('#id-instructions');
            inputBox.focus();
            // If the instructions are out of view, and they were visible
            // before we focussed, move back.
            setTimeout(function() {
                if (!isScrolledIntoView(instructions)) {
                    var pos = instructions.position().top;
                    var topbar = $('.topbar');
                    if (topbar.css('position') == 'fixed') {
                        // If the topbar is position:fixed, we need to take into account
                        // its height.
                        pos -= topbar.height();
                    }
                    $('body').scrollTop(pos);
                };
            }, 1000);
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
                         'testFull': {setup: testFullStart,
                                      continueStage: testFullContinue,
                                      caption: 'Full test',
                                      testMode: true,
                                      testType: TEST_TYPE_FULL,
                                      testMaxAttempts: 3,
                                      toggleMode: null},
                         'testQuick': {setup: testQuickStart,
                                       continueStage: testQuickContinue,
                                       caption: 'Quick test',
                                       testMode: true,
                                       testType: TEST_TYPE_QUICK,
                                       testMaxAttempts: 2,
                                       toggleMode: null},
                         'results': {setup: function() {},
                                     continueStage: function() { return true;},
                                     caption: 'Results',
                                     testMode: false,
                                     toggleMode: null}
                        };


        var progressRowId = function(stageIdx) {
            return 'id-progress-row-' + (currentStageIdx + spentStagesCount).toString();
        };

        var setupStage = function(idx) {
            // set the globals
            var currentStageName = currentStageList[idx];
            currentStageIdx = idx;
            currentStage = stageDefs[currentStageName];

            // Common clearing, and stage specific setup
            $('#id-verse .correct, #id-verse .incorrect').removeClass('correct').removeClass('incorrect');
            $('#id-progress-summary').text("Stage " + (currentStageIdx + 1).toString() + "/" + currentStageList.length.toString());
            currentStage.setup();
            setNextPreviousBtns();

            showInstructions(currentStageName);
            // reset selected word
            moveSelection($('.word').first());
            inputBox.val('').focus();

            // Create progress bar for this stage.
            var pRowId = progressRowId(currentStageIdx);
            if (!document.getElementById(pRowId)) {
                var progressRow = $(
                    '<tr id="' + pRowId + '" style="display:none;">' +
                        '<th>' + currentStage.caption + '</th>' +
                        '<td><progress value="0" max="100">0%</progress>' +
                        '</td></tr>');
                $('.progress table').prepend(progressRow);
                progressRow.show('200');

            }
            setProgress(currentStageIdx, 0);
            $('th.currenttask').removeClass('currenttask');
            $('#' + pRowId + ' th').addClass('currenttask');
        };

        // -- Moving between stages --

        var next = function(ev) {
            inputBox.val('').focus();
            if (currentStage.continueStage()) {
                return;
            }
            if (currentStageIdx < currentStageList.length - 1) {
                setProgress(currentStageIdx, 1);
                setupStage(currentStageIdx + 1);
            }
        };

        var back = function(ev) {
            inputBox.val('').focus();
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

        var keypress = function(ev) {
            if (ev.ctrlKey && ev.which == 37) {
                // Ctrl-Left
                ev.preventDefault();
                back();
                return;
            }
            if (ev.ctrlKey && ev.which == 39) {
                // Ctrl-Right
                ev.preventDefault();
                next();
                return;
            }
            if (ev.which == 27) {
                // ESC
                ev.preventDefault();
                inputBox.val('');
                return;
            }
            if (ev.which == 13) {
                // Enter
                ev.preventDefault();
                toggleWord($('.word.selected'));
                return;
            }
            if (!currentStage.testMode) {
                if (ev.which == 37) {
                    // Left
                    ev.preventDefault();
                    moveSelectionRelative(-1);
                    return;
                }
                if (ev.which == 39) {
                    // Right
                    ev.preventDefault();
                    moveSelectionRelative(1);
                    return;
                }
            }
            if (ev.which == 32) {
                ev.preventDefault();
                if (currentStage.testMode) {
                    if (currentStage.testType == TEST_TYPE_FULL) {
                        checkCurrentWord();
                    }
                } else {
                    moveSelectionRelative(1);
                }
            }
            // Any character in TEST_TYPE_QUICK
            if (currentStage.testMode && currentStage.testType == TEST_TYPE_QUICK) {
                if (alphanumeric(ev)) {
                    ev.preventDefault()
                    // Put it there ourselves, so it is ready for checkCurrentWord()
                    inputBox.val(String.fromCharCode(ev.which));
                    checkCurrentWord();
                }
            }

            // Fall through for all other keys
            if (!currentStage.testMode) {
                // do not allow other typing, since it confuses user to be able
                // to type. We are conservative in what we catch, to avoid
                // catching tab and function keys etc.
                if (alphanumeric(ev)) {
                    ev.preventDefault();
                }
            }

        };
        var versionSelectChanged = function(ev) {
            $.ajax({url: '/api/learnscripture/v1/changeversion/',
                    dataType: 'json',
                    type: 'POST',
                    data: {
                        reference: currentVerseStatus.reference,
                        version_slug: $('#id-version-select').val(),
                        verse_set_id: currentVerseStatus.verse_choice.verse_set != undefined
                            ? currentVerseStatus.verse_choice.verse_set.id
                            : null,
                        user_verse_status_id: currentVerseStatus.id
                    },
                    success: function() {
                        nextVerse();
                    },
                    error: handlerAjaxError
                   });
        };

        // setup and wiring
        var start = function() {
            inputBox = $('#id-typing');
            inputBox.keydown(keypress);
            $('#id-next-btn').show().click(next);
            $('#id-back-btn').show().click(back);
            $('#id-next-verse-btn').click(nextVerse);
            $('#id-version-select').change(versionSelectChanged);
            nextVerse();
        };

        var nextVerse = function() {
            $('.progress table tr').remove();
            loadVerse();
        };

        var chooseStageListForStrength = function(strength) {
            // This function is tuned to give read/recall stages only for the
            // early stages, or when the verse has been completely forgotten.
            // Although it doesn't use it, it's tuned to the value of
            // INITIAL_STRENGTH_FACTOR
            if (strength < 0.02) {
                // either first test, or first test after initial test score
                // of 20% or less. Do everything:
                return ['read', 'recall1', 'recall2', 'recall3', 'recall4', 'testFull'];
            }
            if (strength < 0.07) {
                // e.g. first test was 70% or less, this is second test
                return ['recall2', 'testFull']
            }
            if (strength < 0.4) {
                return ['testFull'];
            }
            // Choice between testQuick and testFull
            var choices = ['testFull', 'testQuick'];
            if (strength < 0.5) {
                // 50% chance
                return [choices[Math.floor(Math.random() * choices.length)]]
            }
            // 1 in 5 chance of testFull
            return [choices[Math.min(1, Math.floor(Math.random() * choices.length * 5))]]
        }

        var setupStageList = function(verseData) {
            var strength = 0;
            if (verseData.strength != null) {
                strength = verseData.strength;
            }
            currentStageList = chooseStageListForStrength(strength);
            setupStage(0);
        }

        var loadVerse = function() {
            $.ajax({url: '/api/learnscripture/v1/nextverse/?format=json',
                    dataType: 'json',
                    success: function(data) {
                        currentVerseStatus = data;
                        $('#id-verse-wrapper').hide(); // Hide until set up
                        $('#id-verse-title').text(data.reference);
                        // convert newlines to divs
                        var text = data.text + '\n' + data.reference;
                        $.each(text.split(/\n/), function(idx, line) {
                            if (line.trim() != '') {
                                $('#id-verse').append('<div class="line">' +
                                                      line + '</div>');
                            }
                        });
                        var versionText = "Version: " + data.version.full_name +
                            " (" + data.version.short_name + ")";
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
                        $('#id-verse-wrapper').show();

                        focusTypingInputCarefully();
                    },
                    error: function(jqXHR, textStatus, errorThrown) {
                        if (jqXHR.status == 404) {
                            $('#id-loading').hide();
                            $('#id-controls').hide();
                            $('#id-no-verse-queue').show(300);
                        } else {
                            handlerAjaxError(jqXHR, textStatus, errorThrown);
                        }
                    }
                   });
        };

        var markupVerse = function() {
            var wordGroups = [];

            $('#id-verse .line').each(function(idx, elem) {
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
                $.each(group, function(j, word) {
                    wordList.push(wordNumber);
                    wordNumber++;
                });
                var replace = $.map(group, function(word, j) {
                    var start = word.match(/\W*./)[0];
                    var end = word.slice(start.length);
                    return ('<span class=\"word\">' +
                            '<span class="wordstart">' + start +
                            '</span><span class="wordend">' + end +
                            '</span></span>');
                }).join(' ');
                replacement.push(replace);
            }
            $('#id-verse').html(replacement.join('<br/>'));
            $('.word').click(function(ev) {
                if (!currentStage.testMode) {
                    toggleWord($(this));
                }
                inputBox.focus();
            });
        };

        // TODO - implement retrying and a queue and UI for manual
        // retrying.
        // Also handle case of user being logged out.
        var handlerAjaxError = function(jqXHR, textStatus, errorThrown) {
            console.log("AJAX error: %s, %s, %o", textStatus, errorThrown, jqXHR);
        };

        learnscripture.handlerAjaxError = handlerAjaxError;
        learnscripture.start = start;
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

$(document).ajaxSend(function(event, xhr, settings) {
    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie != '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = jQuery.trim(cookies[i]);
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) == (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    function sameOrigin(url) {
        // url could be relative or scheme relative or absolute
        var host = document.location.host; // host + port
        var protocol = document.location.protocol;
        var sr_origin = '//' + host;
        var origin = protocol + sr_origin;
        // Allow absolute or scheme relative URLs to same origin
        return (url == origin || url.slice(0, origin.length + 1) == origin + '/') ||
            (url == sr_origin || url.slice(0, sr_origin.length + 1) == sr_origin + '/') ||
            // or any other URL that isn't scheme relative or absolute i.e relative.
            !(/^(\/\/|http:|https:).*/.test(url));
    }
    function safeMethod(method) {
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    }

    if (!safeMethod(settings.type) && sameOrigin(settings.url)) {
        xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
    }
});

$(document).ready(function() {
    if ($('#id-verse').length > 0) {
        learnscripture.start();
    }
    $('.topbar').dropdown();
});
