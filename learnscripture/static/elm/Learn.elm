module Learn exposing (..)

import Erl
import Dom
import Dict
import Html as H
import Html.Attributes as A
import Html.Events as E
import Http
import Json.Decode as JD
import Json.Decode.Pipeline as JDP
import Json.Encode as JE
import Maybe
import Navigation
import Process
import Random
import Random.List
import Regex as R
import Set
import String
import String.Interpolate exposing (interpolate)
import Task
import Time
import Window
import LearnPorts
import Native.StringUtils


{- Main -}


main : Program Flags Model Msg
main =
    H.programWithFlags
        { init = init
        , view = view
        , update = update
        , subscriptions = subscriptions
        }



{- Constants -}


{-| Strength == 0.6 corresponds to about 10 days learning.
-}
hardModeStrengthThreshold : Float
hardModeStrengthThreshold =
    0.6



{- Flags and external inputs -}


type alias Flags =
    { preferences : JD.Value
    , account : Maybe AccountData
    , isTouchDevice : Bool
    , csrfMiddlewareToken : String
    }


decodePreferences : JD.Value -> Preferences
decodePreferences prefsValue =
    case JD.decodeValue preferencesDecoder prefsValue of
        Ok prefs ->
            prefs

        Err err ->
            Debug.crash err


init : Flags -> ( Model, Cmd Msg )
init flags =
    ( { preferences = decodePreferences flags.preferences
      , user =
            case flags.account of
                Just ad ->
                    Account ad

                Nothing ->
                    GuestUser
      , isTouchDevice = flags.isTouchDevice
      , httpConfig =
            { csrfMiddlewareToken = flags.csrfMiddlewareToken
            }
      , learningSession = Loading
      , helpVisible = False
      , currentHttpCalls = Dict.empty
      , permanentFailHttpCalls = []
      , openDropdown = Nothing
      }
    , loadVerses
    )



{- Model -}


type alias Model =
    { preferences : Preferences
    , user : User
    , learningSession : LearningSession
    , isTouchDevice : Bool
    , httpConfig : HttpConfig
    , helpVisible : Bool
    , currentHttpCalls :
        Dict.Dict Int
            { call : TrackedHttpCall
            , attempts : Int
            }
    , permanentFailHttpCalls : List TrackedHttpCall
    , openDropdown : Maybe Dropdown
    }


type alias Preferences =
    { preferencesSetup : Bool
    , enableAnimations : Bool
    , enableSounds : Bool
    , enableVibration : Bool
    , desktopTestingMethod : TestingMethod
    , touchscreenTestingMethod : TestingMethod
    }


type alias HttpConfig =
    { csrfMiddlewareToken : String
    }


type TestingMethod
    = FullWords
    | FirstLetter
    | OnScreen


type User
    = GuestUser
    | Account AccountData


type alias AccountData =
    { username : String
    }


type LearningSession
    = Loading
    | VersesError Http.Error
    | Session SessionData


type alias SessionData =
    { verses : VerseStore
    , currentVerse : CurrentVerse
    }


type alias CurrentVerse =
    { verseStatus : VerseStatus
    , sessionLearningType : LearningType
    , currentStage : LearningStage
    , remainingStageTypes : List LearningStageType
    , seenStageTypes : List LearningStageType
    }


type alias LearnOrder =
    Int


type alias UvsId =
    Int


type alias Url =
    String


type alias VerseStore =
    { verseStatuses : List VerseStatus
    , learningType : LearningType
    , returnTo : Url
    , maxOrderVal : LearnOrder
    }


type alias VerseBatchBase a =
    { a
        | learningTypeRaw : Maybe LearningType
        , returnTo : Url
        , maxOrderValRaw : Maybe LearnOrder
    }


type alias VerseBatchRaw =
    VerseBatchBase
        { verseStatusesRaw : List VerseStatusRaw
        , versions : List Version
        , verseSets : List VerseSet
        }



-- VerseBatchRaw constructor does not get created for us so we make one here for
-- consistency


verseBatchRawCtr :
    Maybe LearningType
    -> String
    -> Maybe LearnOrder
    -> List VerseStatusRaw
    -> List Version
    -> List VerseSet
    -> VerseBatchRaw
verseBatchRawCtr l r m v1 v2 v3 =
    { learningTypeRaw = l
    , returnTo = r
    , maxOrderValRaw = m
    , verseStatusesRaw = v1
    , versions = v2
    , verseSets = v3
    }


type alias VerseBatch =
    VerseBatchBase
        { verseStatuses : List VerseStatus
        }


type alias WordSuggestion =
    String


type alias WordSuggestions =
    List String


type alias VerseSuggestions =
    List WordSuggestions


type alias VerseStatusBase a =
    { a
        | id : Int
        , strength : Float
        , localizedReference : String
        , needsTesting : Bool
        , textOrder : Int
        , suggestions : VerseSuggestions
        , scoringTextWords : List String
        , titleText : String
        , learnOrder : LearnOrder
    }


type alias VerseStatusRaw =
    VerseStatusBase
        { verseSetId : Maybe Int
        , versionSlug : String
        }



-- VerseStatusRaw constructor does not get created for us


verseStatusRawCtr :
    Int
    -> Float
    -> String
    -> Bool
    -> Int
    -> VerseSuggestions
    -> List String
    -> String
    -> Int
    -> Maybe Int
    -> String
    -> VerseStatusRaw
verseStatusRawCtr i s l n t s2 s3 t2 l2 v v2 =
    { id = i
    , strength = s
    , localizedReference = l
    , needsTesting = n
    , textOrder = t
    , suggestions = s2
    , scoringTextWords = s3
    , titleText = t2
    , learnOrder = l2
    , verseSetId = v
    , versionSlug = v2
    }


type alias VerseStatus =
    VerseStatusBase
        { verseSet : Maybe VerseSet
        , version : Version
        }


type alias VerseSet =
    { id : Int
    , setType : VerseSetType
    , name : String
    , getAbsoluteUrl : String
    }


type VerseSetType
    = Selection
    | Passage


type alias Version =
    { fullName : String
    , shortName : String
    , slug : String
    , url : String
    , textType : TextType
    }


type TextType
    = Bible
    | Catechism


type LearningType
    = Revision
    | Learning
    | Practice



{- View -}


type alias IconName =
    String


type LinkIconAlign
    = AlignLeft
    | AlignRight


type Dropdown
    = AjaxInfo
    | VerseOptionsMenu


dashboardUrl : String
dashboardUrl =
    "/dashboard/"


view : Model -> H.Html Msg
view model =
    H.div []
        [ topNav model
        , case model.learningSession of
            Loading ->
                loadingDiv

            VersesError err ->
                errorMessage ("The items to learn could not be loaded (error message: " ++ toString err ++ ".) Please check your internet connection!")

            Session sessionData ->
                viewCurrentVerse sessionData model
        ]


topNav : Model -> H.Html Msg
topNav model =
    H.nav [ A.class "topbar-new" ]
        [ H.div [ A.class "dashboard-link" ]
            [ link dashboardUrl "Dashboard" "icon-return" AlignLeft ]
        , H.div [ A.class "spacer" ]
            []
        , ajaxInfo model
        , H.div [ A.class "preferences-link" ]
            [ link "#" (userDisplayName model.user) "icon-preferences" AlignRight ]
        ]


ajaxInfo : Model -> H.Html Msg
ajaxInfo model =
    let
        currentHttpCalls =
            Dict.values model.currentHttpCalls

        httpCallsInProgress =
            currentHttpCalls |> List.isEmpty |> not

        retryingAttempts =
            currentHttpCalls |> List.map .attempts |> List.any (\a -> a > 1)

        failedHttpCalls =
            model.permanentFailHttpCalls

        retriesClass =
            if retryingAttempts then
                "ajax-retries"
            else
                ""

        failuresClass =
            if not <| List.isEmpty failedHttpCalls then
                "ajax-failures"
            else
                ""

        itemsToView =
            not <| List.isEmpty currentHttpCalls && List.isEmpty failedHttpCalls

        hideStatus =
            not itemsToView

        hiddenClass =
            if hideStatus then
                "hidden"
            else
                ""

        spinClass =
            if hideStatus then
                ""
            else if httpCallsInProgress then
                "icon-spin"
            else
                ""

        topClass =
            String.join " "
                [ retriesClass
                , failuresClass
                , hiddenClass
                ]

        dropdownOpen =
            dropdownIsOpen model AjaxInfo

        openClass =
            if dropdownOpen && itemsToView then
                " open"
            else
                ""
    in
        H.div [ A.class ("ajax-info nav-dropdown" ++ openClass) ]
            [ H.div
                ([ A.class ("nav-dropdown-heading " ++ topClass)
                 ]
                )
                [ H.a
                    ([ A.href "#"
                     , onClickSimply (ToggleDropdown AjaxInfo)
                     ]
                        ++ if hideStatus then
                            [ A.tabindex -1 ]
                           else
                            []
                    )
                    [ H.span [ A.class "nav-caption" ]
                        [ H.text "Working..." ]
                    , makeIcon ("icon-ajax-in-progress " ++ spinClass)
                    ]
                ]
            , if not itemsToView then
                emptyNode
              else
                H.ul
                    [ A.class "nav-dropdown-menu" ]
                    ((currentHttpCalls
                        |> List.map
                            (\{ call, attempts } ->
                                H.li
                                    [ A.class
                                        ("ajax-attempt"
                                            ++ (if attempts > 1 then
                                                    " ajax-retrying"
                                                else
                                                    ""
                                               )
                                        )
                                    ]
                                    [ H.text <|
                                        interpolate "Attempt {0} of {1} - {2}"
                                            [ toString attempts
                                            , toString maxHttpRetries
                                            , trackedHttpCallCaption call
                                            ]
                                    ]
                            )
                     )
                        ++ (failedHttpCalls
                                |> List.map
                                    (\call ->
                                        H.div [ A.class "ajax-failed" ]
                                            [ H.text <|
                                                interpolate "Failed - {0}"
                                                    [ trackedHttpCallCaption call ]
                                            ]
                                    )
                           )
                    )
            ]


userDisplayName : User -> String
userDisplayName u =
    case u of
        GuestUser ->
            "Guest"

        Account ad ->
            ad.username


loadingDiv : H.Html msg
loadingDiv =
    H.div [ A.id "id-loading-full" ] [ H.text "Loading" ]


viewCurrentVerse : SessionData -> Model -> H.Html Msg
viewCurrentVerse session model =
    let
        currentVerse =
            session.currentVerse

        previousVerse =
            if shouldShowPreviousVerse currentVerse.verseStatus then
                getPreviousVerse session.verses currentVerse.verseStatus
            else
                Nothing

        testingMethod =
            getTestingMethod model

        titleTextAttrs =
            if isTestingReference currentVerse.currentStage then
                [ A.class "blurry" ]
            else
                []

        hideWordBoundariesClass =
            "hide-word-boundaries"

        verseClasses =
            "current-verse "
                ++ case currentVerse.currentStage of
                    ReadForContext ->
                        "read-for-context"

                    Test _ _ ->
                        case testingMethod of
                            OnScreen ->
                                hideWordBoundariesClass

                            _ ->
                                if shouldUseHardTestingMode currentVerse then
                                    hideWordBoundariesClass
                                else
                                    ""

                    _ ->
                        ""

        verseOptionsMenuOpen =
            (dropdownIsOpen model VerseOptionsMenu)
    in
        H.div [ A.id "id-content-wrapper" ]
            ([ H.div [ A.id "id-verse-header" ]
                [ H.h2 titleTextAttrs
                    [ H.text currentVerse.verseStatus.titleText ]
                , viewVerseOptionsMenuButton verseOptionsMenuOpen
                ]
             , if verseOptionsMenuOpen then
                viewVerseOptionsMenu model currentVerse
               else
                emptyNode
             , H.div [ A.id typingBoxContainerId ]
                -- We make typing box a permanent fixture to avoid issues with
                -- losing focus and screen keyboards then disappearing.
                -- It comes before verse-wrapper to fix tab order without needing
                -- tabindex.
                [ typingBox currentVerse.currentStage testingMethod
                , case previousVerse of
                    Nothing ->
                        emptyNode

                    Just verse ->
                        H.div [ A.class "previous-verse-wrapper" ]
                            [ H.div [ A.class "previous-verse" ]
                                (versePartsToHtml ReadForContext <|
                                    partsForVerse verse ReadForContextStage testingMethod
                                )
                            ]
                , H.div [ A.class "current-verse-wrapper" ]
                    [ H.div [ A.class verseClasses ]
                        (versePartsToHtml currentVerse.currentStage <|
                            partsForVerse currentVerse.verseStatus (learningStageTypeForStage currentVerse.currentStage) testingMethod
                        )
                    ]
                , copyrightNotice currentVerse.verseStatus.version
                ]
             , actionButtons model currentVerse session.verses model.preferences
             , hintButton model currentVerse testingMethod
             , onScreenTestingButtons currentVerse testingMethod
             ]
                ++ (instructions currentVerse testingMethod model.helpVisible)
            )


shouldShowPreviousVerse : VerseStatus -> Bool
shouldShowPreviousVerse verse =
    case verse.version.textType of
        Bible ->
            case verse.verseSet of
                Nothing ->
                    False

                Just verseSet ->
                    case verseSet.setType of
                        Selection ->
                            False

                        Passage ->
                            True

        Catechism ->
            False


viewVerseOptionsMenuButton : Bool -> H.Html Msg
viewVerseOptionsMenuButton menuOpen =
    H.div
        [ A.id "id-verse-options-menu-btn"
        , A.class
            (if menuOpen then
                "open"
             else
                "closed"
            )
        ]
        [ H.a
            [ A.href "#"
            , onClickSimply (ToggleDropdown VerseOptionsMenu)
            ]
            [ makeIcon "icon-verse-options-menu-btn" ]
        ]


viewVerseOptionsMenu : Model -> CurrentVerse -> H.Html Msg
viewVerseOptionsMenu model currentVerse =
    H.div [ A.id "id-verse-options-menu" ]
        [ H.ul []
            [ H.li []
                [ viewButton model
                    { enabled = Enabled
                    , default = NonDefault
                    , msg = NextVerse
                    , caption = "Skip this for now"
                    , id = "id-skip-verse"
                    , refocusTypingBox = True
                    }
                ]
            ]
        ]


dropdownIsOpen : Model -> Dropdown -> Bool
dropdownIsOpen model dropdown =
    case model.openDropdown of
        Just dropdown ->
            True

        _ ->
            False



{- word/sentence splitting and word buttons -}


type Part
    = WordPart Word
    | Space
    | ReferencePunct String
    | Linebreak


type alias Word =
    { type_ : WordType
    , index : WordIndex
    , text : String
    }


type WordType
    = BodyWord
    | ReferenceWord


type alias WordIndex =
    Int


partsForVerse : VerseStatus -> LearningStageType -> TestingMethod -> List Part
partsForVerse verse learningStageType testingMethod =
    (List.map2 verseWordToParts verse.scoringTextWords (listIndices verse.scoringTextWords)
        |> List.concat
    )
        ++ if
            (shouldShowReference verse
                && (not (isTestingStage learningStageType)
                        || (shouldTestReferenceForTestingMethod testingMethod)
                   )
            )
           then
            [ Linebreak ] ++ referenceToParts verse.localizedReference
           else
            []


wordsForVerse : VerseStatus -> LearningStageType -> TestingMethod -> List Word
wordsForVerse verseStatus learningStageType testingMethod =
    let
        parts =
            partsForVerse verseStatus learningStageType testingMethod
    in
        List.filterMap
            (\p ->
                case p of
                    WordPart w ->
                        Just w

                    _ ->
                        Nothing
            )
            parts


{-| Split word into Part objects.

 Only used for within verse body
 The initial sentence has already been split into words server side, and this
 function does not split off punctuation, but keeps it as part of the word.
-}
verseWordToParts : String -> WordIndex -> List Part
verseWordToParts w idx =
    let
        ( start, end ) =
            ( String.slice 0 -1 w, String.right 1 w )
    in
        if end == "\n" then
            [ WordPart
                { type_ = BodyWord
                , index = idx
                , text = start
                }
            , Linebreak
            ]
        else
            [ WordPart
                { type_ = BodyWord
                , index = idx
                , text = w
                }
            , Space
            ]


referenceToParts : String -> List Part
referenceToParts reference =
    let
        -- Javascript regexes: no Unicode support, no lookbehinds, and we want
        -- to keep the punctuation that we are splitting on - hence this is more
        -- complex than you might expect.
        splitter =
            R.regex "(?=[\\s:\\-])"

        punct =
            R.regex "^[\\s:\\-]"

        parts =
            reference
                |> R.split R.All splitter
                -- Split the initial punctuation into separate bits:
                |>
                    List.map
                        (\w ->
                            if R.contains punct w then
                                [ String.left 1 w, String.dropLeft 1 w ]
                            else
                                [ w ]
                        )
                |> List.concat
    in
        List.map2
            (\idx w ->
                if R.contains punct w then
                    ReferencePunct w
                else if String.trim w == "" then
                    Space
                else
                    WordPart
                        { type_ = ReferenceWord
                        , index = idx
                        , text = w
                        }
            )
            (List.range 0 (List.length parts))
            parts


versePartsToHtml : LearningStage -> List Part -> List (H.Html Msg)
versePartsToHtml stage parts =
    List.map
        (\p ->
            case p of
                WordPart word ->
                    wordButton word stage

                Space ->
                    H.text " "

                ReferencePunct w ->
                    H.span [ A.class "punct" ]
                        [ H.text w ]

                Linebreak ->
                    linebreak
        )
        parts


idPrefixForButton : WordType -> String
idPrefixForButton wt =
    case wt of
        BodyWord ->
            "id-word-"

        ReferenceWord ->
            "id-reference-part-"


idForButton : Word -> String
idForButton wd =
    idPrefixForButton wd.type_ ++ toString wd.index


wordButton : Word -> LearningStage -> H.Html Msg
wordButton word stage =
    let
        ( classesOuter, classesInner ) =
            wordButtonClasses word stage

        clickableButton =
            List.member clickableClass classesOuter

        id =
            case stage of
                Read ->
                    ""

                ReadForContext ->
                    ""

                _ ->
                    idForButton word
    in
        H.span
            ([ A.class <| String.join " " classesOuter
             ]
                ++ (if id /= "" then
                        [ A.id id ]
                    else
                        []
                   )
                ++ (if clickableButton then
                        [ onClickSimply <| WordButtonClicked <| getWordId word ]
                    else
                        []
                   )
            )
            [ H.span
                [ A.class <| String.join " " ([ "wordpart" ] ++ classesInner) ]
                (subWordParts word stage)
            ]


wordButtonClass : String
wordButtonClass =
    "word-button"


readingWordClass : String
readingWordClass =
    "reading-word"


clickableClass : String
clickableClass =
    "clickable"


wordButtonClasses : Word -> LearningStage -> ( List String, List String )
wordButtonClasses wd stage =
    let
        stageClasses =
            case stage of
                Read ->
                    [ wordButtonClass ]

                ReadForContext ->
                    [ readingWordClass ]

                Recall _ _ ->
                    [ wordButtonClass
                    , clickableClass
                    ]

                Test _ _ ->
                    [ wordButtonClass ]

        testStageClasses =
            case stage of
                Test _ tp ->
                    case getWordAttempt tp wd of
                        Nothing ->
                            case tp.currentWord of
                                TestFinished _ ->
                                    []

                                CurrentWord cw ->
                                    if cw.word == wd then
                                        [ "current" ]
                                    else
                                        []

                        Just attempt ->
                            if attempt.finished then
                                let
                                    allFailed =
                                        List.all isAttemptFailure attempt.checkResults

                                    noneFailed =
                                        List.all (isAttemptFailure >> not) attempt.checkResults

                                    lastWasHint =
                                        case List.head attempt.checkResults of
                                            Nothing ->
                                                False

                                            Just Hint ->
                                                True

                                            _ ->
                                                False
                                in
                                    if allFailed then
                                        [ "incorrect" ]
                                    else if lastWasHint then
                                        [ "hinted" ]
                                    else if noneFailed then
                                        [ "correct" ]
                                    else
                                        [ "partially-correct" ]
                            else
                                []

                _ ->
                    []

        inner =
            case stage of
                Test _ tp ->
                    case getWordAttempt tp wd of
                        Nothing ->
                            [ "hidden" ]

                        Just _ ->
                            []

                _ ->
                    []
    in
        ( stageClasses ++ testStageClasses, inner )


subWordParts : Word -> LearningStage -> List (H.Html msg)
subWordParts word stage =
    let
        -- Need to split into first letter and remaining letters, but the first
        -- letter part must include any initial punctuation.
        core =
            stripOuterPunctuation word.text
    in
        case String.indexes core word.text of
            -- This shouldn't happen, a word composed of just punctuation?
            [] ->
                [ H.text word.text ]

            coreIndex :: _ ->
                let
                    startChars =
                        coreIndex + 1

                    start =
                        String.left startChars word.text

                    end =
                        String.dropLeft startChars word.text

                    ( startIsHidden, endIsHidden ) =
                        case stage of
                            Recall def rp ->
                                let
                                    wordId =
                                        getWordId word

                                    hidden =
                                        Set.member wordId rp.hiddenWordIds

                                    manuallyShown =
                                        Set.member wordId rp.manuallyShownWordIds
                                in
                                    if manuallyShown then
                                        ( False, False )
                                    else
                                        case def.hideType of
                                            HideWordEnd ->
                                                ( False, hidden )

                                            HideFullWord ->
                                                ( hidden, True )

                            _ ->
                                ( False, False )

                    addHidden class isHidden =
                        class
                            ++ (if isHidden then
                                    " hidden"
                                else
                                    ""
                               )
                in
                    [ H.span
                        [ A.class <| addHidden "wordstart" startIsHidden ]
                        [ H.text start ]
                    , H.span
                        [ A.class <| addHidden "wordend" endIsHidden ]
                        [ H.text end ]
                    ]


copyrightNotice : Version -> H.Html msg
copyrightNotice version =
    let
        caption =
            version.shortName ++ " - " ++ version.fullName
    in
        H.div
            [ A.id "id-copyright-notice"
            ]
            (if version.url == "" then
                [ H.text caption ]
             else
                [ H.a
                    [ A.href version.url
                    , A.tabindex -1
                    , A.target "_blank"
                    ]
                    [ H.text caption ]
                ]
            )


typingBoxId : String
typingBoxId =
    "id-typing"


typingBoxContainerId : String
typingBoxContainerId =
    "id-verse-wrapper"


typingBox : LearningStage -> TestingMethod -> H.Html Msg
typingBox stage testingMethod =
    let
        ( value, inUse, incorrectInput ) =
            case stage of
                Test _ tp ->
                    let
                        ( lastCheckFailed, failedAttemptText ) =
                            case getCurrentWordAttempt tp of
                                Nothing ->
                                    ( False, Nothing )

                                Just attempt ->
                                    case attempt.checkResults of
                                        [] ->
                                            ( False, Nothing )

                                        r :: remainder ->
                                            case r of
                                                Failure text ->
                                                    ( True, Just text )

                                                _ ->
                                                    ( False, Nothing )

                        -- If the user has edited the text since they pressed
                        -- Space and had it checked, then remove the styling
                        -- that indicates failure, otherwise it is confusing.
                        currentTextEqualsFailedAttempt =
                            case failedAttemptText of
                                Nothing ->
                                    False

                                Just text ->
                                    (normalizeWordForTest tp.currentTypedText
                                        == normalizeWordForTest text
                                    )
                    in
                        ( tp.currentTypedText
                        , typingBoxInUse tp testingMethod
                        , lastCheckFailed && currentTextEqualsFailedAttempt
                        )

                _ ->
                    ( "", False, False )
    in
        H.input
            ([ A.id typingBoxId
             , A.value value
             , A.class
                (classForTypingBox inUse
                    ++ (if incorrectInput then
                            " incorrect"
                        else
                            ""
                       )
                )
             ]
                ++ if inUse then
                    [ E.onInput TypingBoxInput
                    , onEnter TypingBoxEnter
                    ]
                   else
                    []
            )
            []


typingBoxInUse : TestProgress -> TestingMethod -> Bool
typingBoxInUse testProgress testingMethod =
    let
        isCurrentWord =
            case testProgress.currentWord of
                TestFinished _ ->
                    False

                CurrentWord _ ->
                    True
    in
        isCurrentWord && testMethodUsesTextBox testingMethod



-- See learn_setup.js


classForTypingBox : Bool -> String
classForTypingBox inUse =
    if inUse then
        "toshow"
    else
        "tohide"


actionButtons : Model -> CurrentVerse -> VerseStore -> Preferences -> H.Html Msg
actionButtons model verse verseStore preferences =
    let
        buttons =
            buttonsForStage model verse verseStore preferences
    in
        case buttons of
            [] ->
                emptyNode

            _ ->
                H.div [ A.id "id-action-btns" ]
                    ((if List.length buttons == 1 then
                        -- empty element to take the left hand position,
                        -- pushing the one button to the right
                        [ emptySpan ]
                      else
                        []
                     )
                        ++ (List.map (viewButton model) buttons)
                    )


hintButton : Model -> CurrentVerse -> TestingMethod -> H.Html Msg
hintButton model currentVerse testingMethod =
    let
        hintDiv enabled total used =
            H.div [ A.id "id-hint-btn-container" ]
                [ viewButton model
                    { enabled = enabled
                    , default = NonDefault
                    , msg = UseHint
                    , caption =
                        "Use hint"
                            ++ interpolate " ({0}/{1})"
                                [ toString used
                                , toString total
                                ]
                    , id = "id-hint-btn"
                    , refocusTypingBox = True
                    }
                ]
    in
        case currentVerse.currentStage of
            Test _ testProgress ->
                case testProgress.currentWord of
                    TestFinished _ ->
                        emptyNode

                    CurrentWord w ->
                        let
                            hintsUsed =
                                (getHintsUsed testProgress)

                            totalHints =
                                allowedHints currentVerse testingMethod

                            hintsRemaining =
                                totalHints - hintsUsed
                        in
                            if totalHints == 0 then
                                emptyNode
                            else
                                hintDiv
                                    (if hintsRemaining > 0 then
                                        Enabled
                                     else
                                        Disabled
                                    )
                                    totalHints
                                    hintsUsed

            _ ->
                emptyNode


emptySpan : H.Html msg
emptySpan =
    H.span [] []


type alias Button =
    { enabled : ButtonEnabled
    , default : ButtonDefault
    , msg : Msg
    , caption : String
    , id : String
    , refocusTypingBox : Bool
    }


type ButtonEnabled
    = Enabled
    | Disabled


type ButtonDefault
    = Default
    | NonDefault


buttonsForStage : Model -> CurrentVerse -> VerseStore -> Preferences -> List Button
buttonsForStage model verse verseStore preferences =
    let
        multipleStages =
            (List.length verse.remainingStageTypes + List.length verse.seenStageTypes) > 0

        nextVerseButtonCaption =
            if moreVersesToLearn verseStore verse.verseStatus then
                "Next"
            else
                "Done"

        nextVerseEnabled =
            case getNextVerse verseStore verse.verseStatus of
                NextVerseData _ ->
                    Enabled

                NoMoreVerses ->
                    Enabled

                VerseNotInStore ->
                    if verseLoadInProgress model then
                        -- Don't trigger another verse load,
                        -- or a double 'next verse' message
                        Disabled
                    else
                        -- Pressing the button will trigger
                        -- the verse load.
                        Enabled

        testStageButtons tp =
            case tp.currentWord of
                TestFinished { accuracy } ->
                    let
                        defaultMorePractice =
                            accuracy < 0.8
                    in
                        [ { caption = "More practice"
                          , msg = MorePractice accuracy
                          , enabled = Enabled
                          , default =
                                if defaultMorePractice then
                                    Default
                                else
                                    NonDefault
                          , id = "id-more-practice"
                          , refocusTypingBox = True
                          }
                        , { caption = nextVerseButtonCaption
                          , msg = NextVerse
                          , enabled = nextVerseEnabled
                          , default =
                                if defaultMorePractice then
                                    NonDefault
                                else
                                    Default
                          , id = "id-next-btn"
                          , refocusTypingBox = True
                          }
                        ]

                CurrentWord _ ->
                    -- Never show previous/back button once we've reached test
                    -- because we might also have 'on screen buttons'
                    -- on the screen.
                    []
    in
        if multipleStages then
            let
                isRemainingStage =
                    not <| List.isEmpty verse.remainingStageTypes

                isPreviousStage =
                    not <| List.isEmpty verse.seenStageTypes

                nextEnabled =
                    if isRemainingStage then
                        Enabled
                    else
                        Disabled

                previousEnabled =
                    if isPreviousStage then
                        Enabled
                    else
                        Disabled
            in
                case verse.currentStage of
                    Test _ tp ->
                        testStageButtons tp

                    _ ->
                        [ { caption = "Back"
                          , msg = PreviousStage
                          , enabled = previousEnabled
                          , default = NonDefault
                          , id = "id-previous-btn"
                          , refocusTypingBox = False
                          }
                        , { caption = "Next"
                          , msg = NextStageOrSubStage
                          , enabled = nextEnabled
                          , default = Default
                          , id = "id-next-btn"
                          , refocusTypingBox = True
                          }
                        ]
        else
            case verse.currentStage of
                Test _ tp ->
                    testStageButtons tp

                _ ->
                    [ { caption = nextVerseButtonCaption
                      , msg = NextVerse
                      , enabled = nextVerseEnabled
                      , default = Default
                      , id = "id-next-btn"
                      , refocusTypingBox = True
                      }
                    ]


getTestingMethod : Model -> TestingMethod
getTestingMethod model =
    if model.isTouchDevice then
        model.preferences.touchscreenTestingMethod
    else
        model.preferences.desktopTestingMethod


viewButton : Model -> Button -> H.Html Msg
viewButton model button =
    let
        class =
            case button.enabled of
                Enabled ->
                    case button.default of
                        Default ->
                            "btn primary"

                        NonDefault ->
                            "btn"

                Disabled ->
                    "btn disabled"

        attributes =
            [ A.class class
            , A.id button.id
            ]

        eventAttributes =
            case button.enabled of
                Enabled ->
                    [ onClickSimply button.msg ]

                Disabled ->
                    []

        -- see learn_setup.js
        focusData =
            if button.refocusTypingBox then
                getTypingBoxFocusDataForMsg model button.msg True
            else
                Nothing

        focusAttributes =
            case focusData of
                Nothing ->
                    []

                Just data ->
                    if data.refocus then
                        [ A.attribute "data-focus-typing-box-required" ""
                        , A.attribute "data-focus-typingBoxId" data.typingBoxId
                        , A.attribute "data-focus-typingBoxContainerId" data.typingBoxContainerId
                        , A.attribute "data-focus-wordButtonId" data.wordButtonId
                        , A.attribute "data-focus-expectedClass" data.expectedClass
                        , A.attribute "data-focus-hardMode" (encodeBool data.hardMode)
                        ]
                    else
                        -- We only need this mechanism if we need a focus action,
                        -- resizing and moving the box is handled by updateTypingBoxCommand
                        []
    in
        H.button (attributes ++ eventAttributes ++ focusAttributes)
            [ H.text button.caption ]


{-| If the Msg will produce a change of state such that
the typing box will be present (and we therefore need to focus it),
return the data for focussing/moving the typing box, otherwise Nothing.

Pass True for refocus argument if we want to refocus, False otherwise.

See learn_setup.js for why this is necessary.
-}
getTypingBoxFocusDataForMsg : Model -> Msg -> Bool -> Maybe UpdateTypingBoxData
getTypingBoxFocusDataForMsg model msg refocus =
    let
        typingBoxUsed state =
            case getCurrentTestProgress state of
                Just tp ->
                    typingBoxInUse tp (getTestingMethod state)

                Nothing ->
                    False

        ( nextState, _ ) =
            update msg model

        typingBoxUsedAfterMsg =
            typingBoxUsed nextState
    in
        if typingBoxUsedAfterMsg then
            Just (getUpdateTypingBoxData nextState refocus)
        else
            Nothing


onScreenTestingButtons : CurrentVerse -> TestingMethod -> H.Html Msg
onScreenTestingButtons currentVerse testingMethod =
    case currentVerse.currentStage of
        Read ->
            emptyNode

        ReadForContext ->
            emptyNode

        Recall _ _ ->
            emptyNode

        Test _ tp ->
            case testingMethod of
                FullWords ->
                    emptyNode

                FirstLetter ->
                    emptyNode

                OnScreen ->
                    case tp.currentWord of
                        TestFinished _ ->
                            emptyNode

                        CurrentWord currentWord ->
                            let
                                words =
                                    getWordSuggestions currentVerse.verseStatus currentWord.word
                            in
                                H.div [ A.id "id-onscreen-test-container" ]
                                    (case words of
                                        [] ->
                                            [ H.div [ A.id "id-onscreen-not-available" ]
                                                [ H.text
                                                    ("On screen testing is not available for this verse in this version."
                                                        ++ " Sorry! Please choose another option in your "
                                                    )
                                                , preferencesLink
                                                ]
                                            ]

                                        _ ->
                                            [ H.div [ A.id "id-onscreen-test-options" ]
                                                (words
                                                    |> List.map
                                                        (\w ->
                                                            H.span
                                                                [ A.class "word-button"
                                                                , onClickSimply (OnScreenButtonClick w)
                                                                ]
                                                                [ H.text w ]
                                                        )
                                                )
                                            ]
                                    )


emptyNode : H.Html msg
emptyNode =
    H.text ""


onEnter : a -> H.Attribute a
onEnter msg =
    let
        isEnter code =
            if code == 13 then
                JD.succeed msg
            else
                JD.fail "not ENTER"
    in
        E.on "keydown" (JD.andThen isEnter E.keyCode)



{- View - help -}


preferencesLink : H.Html msg
preferencesLink =
    H.a
        [ A.class "preferences-link"
        , A.href "#"
        ]
        [ H.text "preferences" ]


instructions : CurrentVerse -> TestingMethod -> Bool -> List (H.Html Msg)
instructions verse testingMethod helpVisible =
    let
        commonHelp =
            [ [ H.text "You can finish your review or learning session at any time using the return button in the top left corner."
              ]
            , [ H.text "Keyboard navigation: use Tab and Shift-Tab to move focus between controls, and Enter to 'press' one. Focus is shown with a blue border."
              ]
            ]

        testingCommonHelp =
            [ [ H.text "You can change your testing method in your "
              , preferencesLink
              , H.text " at any time."
              ]
            ]

        buttonsHelp =
            [ [ H.text "The button for the most likely action is highlighted in colour and is focused by default."
              ]
            ]

        ( main, help ) =
            case verse.currentStage of
                Read ->
                    ( [ bold "READ: "
                      , H.text "Read the text through (preferably aloud), and click 'Next'."
                      ]
                    , commonHelp ++ buttonsHelp
                    )

                ReadForContext ->
                    ( [ bold "READ: "
                      , H.text "Read this verse to get the context and flow of the passage."
                      ]
                    , commonHelp ++ buttonsHelp
                    )

                Recall _ rp ->
                    ( [ bold "READ and RECALL: "
                      , H.text "Read the text through, filling in the gaps from your memory. Click a word to reveal it if you can't remember."
                      ]
                    , commonHelp ++ buttonsHelp
                    )

                Test _ tp ->
                    case tp.currentWord of
                        CurrentWord _ ->
                            case testingMethod of
                                FullWords ->
                                    ( [ bold "TEST: "
                                      , H.text "Testing time! Type the text, pressing space after each word."
                                      ]
                                    , commonHelp
                                        ++ testingCommonHelp
                                        ++ [ [ H.text "You don't need perfect spelling to get full marks."
                                             ]
                                           ]
                                    )

                                FirstLetter ->
                                    ( [ bold "TEST: "
                                      , H.text "Testing time! Type the "
                                      , bold "first letter"
                                      , H.text " of each word."
                                      ]
                                    , commonHelp ++ testingCommonHelp
                                    )

                                OnScreen ->
                                    ( [ bold "TEST: "
                                      , H.text "Testing time! For each word choose from the options shown."
                                      ]
                                    , commonHelp ++ testingCommonHelp
                                    )

                        TestFinished { accuracy } ->
                            ( [ bold "RESULTS: "
                              , H.text "You scored: "
                              , bold (toString (floor (accuracy * 100)) ++ "%")
                              , H.text (" - " ++ resultComment accuracy)
                              ]
                            , []
                            )
    in
        [ H.div [ A.id "id-instructions" ]
            main
        , H.div [ A.id "id-help" ]
            (case help of
                [] ->
                    []

                _ ->
                    [ H.h3 []
                        [ H.text "Help"
                        , if helpVisible then
                            (H.a
                                [ A.href "#"
                                , onClickSimply CollapseHelp
                                ]
                                [ makeIcon "icon-help-expanded" ]
                            )
                          else
                            (H.a
                                [ A.href "#"
                                , onClickSimply ExpandHelp
                                ]
                                [ makeIcon "icon-help-collapsed" ]
                            )
                        ]
                    ]
                        ++ (if helpVisible then
                                [ H.ul []
                                    (List.map (\i -> H.li [] i) help)
                                ]
                            else
                                []
                           )
            )
        ]


resultComment : Float -> String
resultComment accuracy =
    let
        pairs =
            [ ( 0.98, "awesome!" )
            , ( 0.95, "excellent!" )
            , ( 0.9, "very good." )
            , ( 0.8, "good." )
            , ( 0.5, "OK." )
            , ( 0.3, "could do better!" )
            ]

        fallback =
            "more practice needed!"
    in
        case List.head <| List.filter (\( p, c ) -> accuracy > p) pairs of
            Nothing ->
                fallback

            Just ( p, c ) ->
                c



{- View - testing logic -}


shouldShowReference : VerseStatus -> Bool
shouldShowReference verse =
    case verse.version.textType of
        Bible ->
            case verse.verseSet of
                Nothing ->
                    True

                Just verseSet ->
                    case verseSet.setType of
                        Selection ->
                            True

                        Passage ->
                            False

        Catechism ->
            False



{- View helpers and generic utils -}


bold : String -> H.Html msg
bold text =
    H.b [] [ H.text text ]


linebreak : H.Html msg
linebreak =
    H.br [] []


errorMessage : String -> H.Html msg
errorMessage msg =
    H.div [ A.class "error" ] [ H.text msg ]


makeIcon : String -> H.Html msg
makeIcon iconClass =
    H.i [ A.class ("icon-fw " ++ iconClass) ] []


link : String -> String -> IconName -> LinkIconAlign -> H.Html msg
link href caption icon iconAlign =
    let
        iconH =
            makeIcon icon

        captionH =
            H.span [ A.class "nav-caption" ] [ H.text (" " ++ caption ++ " ") ]

        combinedH =
            case iconAlign of
                AlignLeft ->
                    [ iconH, captionH ]

                AlignRight ->
                    [ captionH, iconH ]
    in
        H.a [ A.href href ] combinedH



{- Update -}


type Msg
    = VersesToLearn CallId (Result Http.Error VerseBatchRaw)
    | NextStageOrSubStage
    | PreviousStage
    | NextVerse
    | SetHiddenWords (Set.Set WordId)
    | WordButtonClicked WordId
    | TypingBoxInput String
    | TypingBoxEnter
    | OnScreenButtonClick String
    | UseHint
    | TrackHttpCall TrackedHttpCall
    | MakeHttpCall CallId
    | RecordActionCompleteReturned CallId (Result Http.Error ())
    | MorePractice Float
    | ExpandHelp
    | CollapseHelp
    | ToggleDropdown Dropdown
    | NavigateToWhenDone String
    | WindowResize { width : Int, height : Int }
    | ReceivePreferences JD.Value
    | ReattemptFocus String Int
    | Noop


type ActionCompleteType
    = TestAction


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    case msg of
        VersesToLearn callId result ->
            handleRetries handleVersesToLearn model callId result

        NextStageOrSubStage ->
            moveToNextStageOrSubStage model

        PreviousStage ->
            moveToPreviousStage model

        NextVerse ->
            moveToNextVerse model

        SetHiddenWords hiddenWordIds ->
            ( setHiddenWords model hiddenWordIds
            , Cmd.none
            )

        WordButtonClicked wordId ->
            handleWordButtonClicked model wordId

        TypingBoxInput input ->
            handleTypedInput model input

        TypingBoxEnter ->
            handleTypedEnter model

        OnScreenButtonClick text ->
            handleOnScreenButtonClick model text

        UseHint ->
            handleUseHint model

        TrackHttpCall trackedCall ->
            startTrackedCall model trackedCall

        MakeHttpCall callId ->
            makeHttpCall model callId

        RecordActionCompleteReturned callId result ->
            handleRetries handleRecordActionCompleteReturned model callId result

        MorePractice accuracy ->
            startMorePractice model accuracy

        ExpandHelp ->
            ( { model | helpVisible = True }, Cmd.none )

        CollapseHelp ->
            ( { model | helpVisible = False }, Cmd.none )

        ToggleDropdown dropdown ->
            ( toggleDropdown model dropdown
            , Cmd.none
            )

        NavigateToWhenDone url ->
            -- TODO - if there is a permanent error, we need to show that.
            if Dict.isEmpty model.currentHttpCalls then
                ( model
                , Navigation.load url
                )
            else
                ( model
                  -- keep trying until done
                , NavigateToWhenDone url |> delay (1 * Time.second)
                )

        WindowResize _ ->
            -- Can cause reflow of words and change of sizes of everything,
            -- therefore need to reposition (but not change focus)
            ( model, updateTypingBoxCommand model False )

        ReceivePreferences prefsValue ->
            let
                newModel =
                    { model | preferences = decodePreferences prefsValue }
            in
                -- Might have switched to/from method that requires typing box
                ( newModel, updateTypingBoxCommand newModel False )

        ReattemptFocus id remainingAttempts ->
            ( model, Task.attempt (handleFocusResult id remainingAttempts) (Dom.focus id) )

        Noop ->
            ( model, Cmd.none )



{- Update helpers -}


withSessionData : Model -> a -> (SessionData -> a) -> a
withSessionData model default func =
    case model.learningSession of
        Session sessionData ->
            func sessionData

        _ ->
            default


withCurrentVerse : Model -> a -> (CurrentVerse -> a) -> a
withCurrentVerse model default func =
    withSessionData model
        default
        (\sessionData -> func sessionData.currentVerse)


withCurrentTestWord : CurrentVerse -> a -> (TestType -> TestProgress -> CurrentWordData -> a) -> a
withCurrentTestWord currentVerse default func =
    case currentVerse.currentStage of
        Test testType testProgress ->
            case testProgress.currentWord of
                TestFinished _ ->
                    default

                CurrentWord currentWord ->
                    func testType testProgress currentWord

        _ ->
            default


updateCurrentVerse : Model -> (CurrentVerse -> CurrentVerse) -> Model
updateCurrentVerse model updater =
    let
        ( newModel, _ ) =
            updateCurrentVersePlus model () (\c -> ( updater c, () ))
    in
        newModel


updateCurrentStage : Model -> (LearningStage -> LearningStage) -> Model
updateCurrentStage model updater =
    updateCurrentVerse model
        (\currentVerse ->
            { currentVerse
                | currentStage = updater currentVerse.currentStage
            }
        )


updateCurrentVersePlus : Model -> a -> (CurrentVerse -> ( CurrentVerse, a )) -> ( Model, a )
updateCurrentVersePlus model defaultRetval updater =
    withSessionData model
        ( model, defaultRetval )
        (\sessionData ->
            let
                ( newCurrentVerse, retval ) =
                    updater sessionData.currentVerse

                newSessionData =
                    { sessionData
                        | currentVerse = newCurrentVerse
                    }
            in
                ( { model | learningSession = Session newSessionData }
                , retval
                )
        )


updateTestProgress : Model -> (TestProgress -> TestProgress) -> Model
updateTestProgress model updater =
    updateCurrentStage model
        (\currentStage ->
            case currentStage of
                Test t tp ->
                    Test t (updater tp)

                _ ->
                    currentStage
        )


updateRecallProcess : Model -> (RecallProgress -> RecallProgress) -> Model
updateRecallProcess model updater =
    updateCurrentStage model
        (\currentStage ->
            case currentStage of
                Recall def rp ->
                    Recall def (updater rp)

                _ ->
                    currentStage
        )


getCurrentVerse : Model -> Maybe CurrentVerse
getCurrentVerse model =
    case model.learningSession of
        Session sessionData ->
            Just sessionData.currentVerse

        _ ->
            Nothing


getCurrentTestProgress : Model -> Maybe TestProgress
getCurrentTestProgress model =
    case getCurrentVerse model of
        Just currentVerse ->
            case currentVerse.currentStage of
                Test _ testProgress ->
                    Just testProgress

                _ ->
                    Nothing

        Nothing ->
            Nothing


normalizeVerseBatch : VerseBatchRaw -> VerseBatch
normalizeVerseBatch vbr =
    { learningTypeRaw = vbr.learningTypeRaw
    , returnTo = vbr.returnTo
    , maxOrderValRaw = vbr.maxOrderValRaw
    , verseStatuses = normalizeVerseStatuses vbr
    }


normalizeVerseStatuses : VerseBatchRaw -> List VerseStatus
normalizeVerseStatuses vrb =
    let
        versionDict =
            vrb.versions |> List.map (\v -> ( v.slug, v )) |> Dict.fromList

        verseSetDict =
            vrb.verseSets |> List.map (\v -> ( v.id, v )) |> Dict.fromList
    in
        List.map
            (\vs ->
                { id = vs.id
                , strength = vs.strength
                , localizedReference = vs.localizedReference
                , needsTesting = vs.needsTesting
                , textOrder = vs.textOrder
                , suggestions = vs.suggestions
                , scoringTextWords = vs.scoringTextWords
                , titleText = vs.titleText
                , learnOrder = vs.learnOrder
                , verseSet =
                    case vs.verseSetId of
                        Nothing ->
                            Nothing

                        Just verseSetId ->
                            Just
                                (Dict.get verseSetId verseSetDict
                                    |> (\maybeVs ->
                                            case maybeVs of
                                                Nothing ->
                                                    Debug.crash <| "VerseSet info " ++ toString verseSetId ++ " missing"

                                                Just vs ->
                                                    vs
                                       )
                                )
                , version =
                    Dict.get vs.versionSlug versionDict
                        |> (\maybeV ->
                                case maybeV of
                                    Nothing ->
                                        Debug.crash <| "Version info " ++ vs.versionSlug ++ " missing"

                                    Just v ->
                                        v
                           )
                }
            )
            vrb.verseStatusesRaw


verseBatchToSession : VerseBatch -> ( Maybe SessionData, Cmd Msg )
verseBatchToSession batch =
    case List.head batch.verseStatuses of
        Nothing ->
            ( Nothing, Cmd.none )

        Just verse ->
            case batch.learningTypeRaw of
                Nothing ->
                    ( Nothing, Cmd.none )

                Just learningType ->
                    case batch.maxOrderValRaw of
                        Nothing ->
                            ( Nothing, Cmd.none )

                        Just maxOrderVal ->
                            let
                                ( newCurrentVerse, cmd ) =
                                    setupCurrentVerse verse learningType
                            in
                                ( Just
                                    { verses =
                                        { verseStatuses = batch.verseStatuses
                                        , learningType = learningType
                                        , returnTo = batch.returnTo
                                        , maxOrderVal = maxOrderVal
                                        }
                                    , currentVerse = newCurrentVerse
                                    }
                                , cmd
                                )



-- Merge in new verses. The only thing which actually needs updating is the
-- verse store, the rest will be the same, or the current model will be
-- more recent.


mergeSession : SessionData -> SessionData -> SessionData
mergeSession initialSession newBatchSession =
    let
        initialVerses =
            initialSession.verses
    in
        { initialSession
            | verses =
                { initialVerses
                    | verseStatuses =
                        (initialVerses.verseStatuses
                            ++ newBatchSession.verses.verseStatuses
                        )
                            |> dedupeBy .learnOrder
                }
        }


stageOrVerseChangeCommands : Model -> Bool -> Cmd Msg
stageOrVerseChangeCommands model changeFocus =
    Cmd.batch
        ([ updateTypingBoxCommand model changeFocus
         ]
            ++ if changeFocus then
                [ focusDefaultButton model ]
               else
                []
        )



{- Dropdowns -}


toggleDropdown : Model -> Dropdown -> Model
toggleDropdown model dropdown =
    let
        newOpenDropdown =
            case model.openDropdown of
                Just dropdown ->
                    Nothing

                -- close already open dropdown
                _ ->
                    Just dropdown
    in
        { model | openDropdown = newOpenDropdown }


closeDropdowns : Model -> Model
closeDropdowns model =
    { model | openDropdown = Nothing }



{- Stages -}


{-| Representation of a learning stage that can be used
-}
type LearningStageType
    = ReadStage
    | ReadForContextStage
    | RecallStage RecallDef
    | TestStage TestType


type TestType
    = FirstTest
    | MorePracticeTest


type alias RecallDef =
    { fraction : Float
    , hideType : HideType
    }


type HideType
    = HideWordEnd
    | HideFullWord


{-| Representation of a stage that is in progress
-}
type LearningStage
    = Read
    | ReadForContext
    | Recall RecallDef RecallProgress
    | Test TestType TestProgress


{-| We really want WordType, but it is not comparable
    it https://github.com/elm-lang/elm-compiler/issues/774
    so use `toString` on it and this alias:
-}
type alias WordTypeString =
    String


type alias WordId =
    ( WordTypeString, WordIndex )


type alias RecallProgress =
    { hiddenWordIds : Set.Set WordId
    , passedWordIds : Set.Set WordId
    , manuallyShownWordIds : Set.Set WordId
    }


type alias AttemptRecords =
    Dict.Dict WordId Attempt


type alias TestProgress =
    { attemptRecords : AttemptRecords
    , currentTypedText : String
    , currentWord : CurrentTestWord
    }


type alias Attempt =
    { finished : Bool
    , checkResults : List CheckResult
    , allowedMistakes : Int
    }


type CheckResult
    = Failure String
    | Hint
    | Success


learningStageTypeForStage : LearningStage -> LearningStageType
learningStageTypeForStage s =
    case s of
        Read ->
            ReadStage

        ReadForContext ->
            ReadForContextStage

        Recall def _ ->
            RecallStage def

        Test t _ ->
            TestStage t


setupCurrentVerse : VerseStatus -> LearningType -> ( CurrentVerse, Cmd Msg )
setupCurrentVerse verse learningType =
    let
        ( firstStageType, remainingStageTypes ) =
            getStages learningType FirstTest verse

        ( newCurrentStage, cmd ) =
            initializeStage firstStageType verse
    in
        ( { verseStatus = verse
          , sessionLearningType = learningType
          , currentStage = newCurrentStage
          , seenStageTypes = []
          , remainingStageTypes = remainingStageTypes
          }
        , cmd
        )


initializeStage : LearningStageType -> VerseStatus -> ( LearningStage, Cmd Msg )
initializeStage stageType verseStatus =
    case stageType of
        ReadStage ->
            ( Read, Cmd.none )

        ReadForContextStage ->
            ( ReadForContext, Cmd.none )

        RecallStage def ->
            let
                rp =
                    initialRecallProgress
            in
                ( Recall def rp
                , hideRandomWords verseStatus def rp
                )

        TestStage t ->
            ( Test t (initialTestProgress verseStatus), Cmd.none )


initialRecallProgress : RecallProgress
initialRecallProgress =
    { hiddenWordIds = Set.empty
    , passedWordIds = Set.empty
    , manuallyShownWordIds = Set.empty
    }


initialTestProgress : VerseStatus -> TestProgress
initialTestProgress verseStatus =
    { attemptRecords = Dict.empty
    , currentTypedText = ""
    , currentWord =
        CurrentWord
            { overallIndex = 0
            , word =
                -- Passing 'FullWords' here is a bit of a hack, but
                -- works fine when we are only getting the first word.
                -- and saves passing testingMethod around everywhere
                case getAt (wordsForVerse verseStatus (TestStage FirstTest) FullWords) 0 of
                    Nothing ->
                        Debug.crash ("Should be at least one word in verse " ++ verseStatus.localizedReference)

                    Just w ->
                        w
            }
    }


finishStage : CurrentVerse -> LearningStage -> Cmd Msg
finishStage currentVerse learningStage =
    case learningStage of
        Read ->
            recordReadComplete currentVerse

        ReadForContext ->
            recordReadComplete currentVerse

        Recall _ _ ->
            Cmd.none

        Test _ _ ->
            -- commands for finishing test phase are done via
            -- checkCurrentWordAndUpdate/markWord
            Cmd.none


{-| Returns a command that picks words to hide.

The fraction to hide is based on RecallDef.
We try to hide ones that haven't been hidden before i.e. ones not
in `passedWordIds`
-}
hideRandomWords : VerseStatus -> RecallDef -> RecallProgress -> Cmd Msg
hideRandomWords verseStatus recallDef recallProgress =
    let
        words =
            recallWords verseStatus

        wordIds =
            List.map getWordId words |> Set.fromList

        -- The number of words we want to hide:
        neededWordCount =
            recallDef.fraction * (toFloat <| Set.size wordIds) |> ceiling

        unpassedWordIds =
            Set.diff wordIds recallProgress.passedWordIds

        unpassedWordCount =
            Set.size unpassedWordIds

        generator =
            if neededWordCount >= unpassedWordCount then
                -- We need all the unpassed ones, and possibly some more
                hiddenWordsGenerator unpassedWordIds recallProgress.passedWordIds (neededWordCount - unpassedWordCount)
            else
                -- pick from the the unpassed ones.
                hiddenWordsGenerator Set.empty unpassedWordIds neededWordCount
    in
        Random.generate SetHiddenWords generator


recallWords : VerseStatus -> List Word
recallWords verseStatuses =
    -- the values passed to RecallStage here don't matter, we pass in random values.
    -- FullWords passed to ensure we get all words, rather
    -- than OnScreen which doesn't return reference (hack)
    wordsForVerse verseStatuses
        (RecallStage
            { fraction = 0
            , hideType = HideFullWord
            }
        )
        FullWords


{-| Given some WordIds we definitely want to choose,
    a Set of potentials and a number to choose from the potentials,
    returns a Random.Generator that will return a matching
    Set
-}
hiddenWordsGenerator : Set.Set WordId -> Set.Set WordId -> Int -> Random.Generator (Set.Set WordId)
hiddenWordsGenerator wantedWordIds possibleWordIds numberWanted =
    chooseN numberWanted (Set.toList possibleWordIds) |> Random.map (\choices -> Set.fromList choices |> Set.union wantedWordIds)


recallStageFinished : VerseStatus -> RecallProgress -> Bool
recallStageFinished verseStatus recallProgress =
    List.length (recallWords verseStatus) == Set.size recallProgress.passedWordIds


type alias CurrentWordData =
    { word :
        Word
        -- overallIndex is the position in list returned by wordsForVerse, which can include references
    , overallIndex : Int
    }


type CurrentTestWord
    = TestFinished { accuracy : Float }
    | CurrentWord CurrentWordData


getCurrentWordAttempt : TestProgress -> Maybe Attempt
getCurrentWordAttempt testProgress =
    case testProgress.currentWord of
        TestFinished _ ->
            Nothing

        CurrentWord w ->
            getWordAttempt testProgress w.word


isTestingStage : LearningStageType -> Bool
isTestingStage stage =
    case stage of
        TestStage _ ->
            True

        _ ->
            False


isTestingReference : LearningStage -> Bool
isTestingReference stage =
    case stage of
        Test _ tp ->
            case tp.currentWord of
                TestFinished _ ->
                    False

                CurrentWord cw ->
                    cw.word.type_ == ReferenceWord

        _ ->
            False


getTestResult : TestProgress -> Float
getTestResult testProgress =
    let
        attempts =
            List.filter .finished <| List.map Tuple.second <| Dict.toList testProgress.attemptRecords

        wordAccuracies =
            List.map
                (\attempt ->
                    -- if, for example, 2 mistakes are allowed, then
                    -- total 3 attempts possible:
                    -- 0 mistakes = 100% accurate
                    -- 1 mistake = 66%
                    -- 2 mistakes = 33%
                    -- 3 mistakes = 0
                    let
                        mistakes =
                            List.length <| List.filter isAttemptFailure attempt.checkResults

                        allowedAttempts =
                            attempt.allowedMistakes + 1
                    in
                        1.0 - ((toFloat <| min mistakes allowedAttempts) / (toFloat allowedAttempts))
                )
                attempts
    in
        case List.length wordAccuracies of
            0 ->
                1.0

            l ->
                -- Do some rounding to avoid 0.999 and retain 3 s.f.
                (toFloat (round (List.sum wordAccuracies / (toFloat l) * 1000)) / 1000)


getHintsUsed : TestProgress -> Int
getHintsUsed testProgress =
    testProgress.attemptRecords
        |> Dict.toList
        |> List.map (Tuple.second >> .checkResults)
        |> List.concat
        |> List.filter isAttemptHint
        |> List.length


isAttemptFailure : CheckResult -> Bool
isAttemptFailure r =
    case r of
        Failure _ ->
            True

        _ ->
            False


isAttemptHint : CheckResult -> Bool
isAttemptHint r =
    case r of
        Hint ->
            True

        _ ->
            False


testMethodUsesTextBox : TestingMethod -> Bool
testMethodUsesTextBox testingMethod =
    case testingMethod of
        FullWords ->
            True

        FirstLetter ->
            True

        OnScreen ->
            False


getStages : LearningType -> TestType -> VerseStatus -> ( LearningStageType, List LearningStageType )
getStages learningType testType verseStatus =
    let
        getNonPracticeStages vs =
            if vs.needsTesting then
                getStagesByStrength vs.strength testType
            else
                ( ReadForContextStage
                , []
                )
    in
        case learningType of
            Learning ->
                getNonPracticeStages verseStatus

            Revision ->
                getNonPracticeStages verseStatus

            Practice ->
                ( TestStage testType
                , []
                )


recallStage1 : LearningStageType
recallStage1 =
    RecallStage
        { fraction = 0.5
        , hideType = HideWordEnd
        }


recallStage2 : LearningStageType
recallStage2 =
    RecallStage
        { fraction = 1
        , hideType = HideWordEnd
        }


recallStage3 : LearningStageType
recallStage3 =
    RecallStage
        { fraction = 0.34
        , hideType = HideFullWord
        }


recallStage4 : LearningStageType
recallStage4 =
    RecallStage
        { fraction = 0.67
        , hideType = HideFullWord
        }


getStagesByStrength : Float -> TestType -> ( LearningStageType, List LearningStageType )
getStagesByStrength strength testType =
    if strength < 0.02 then
        ( ReadStage
        , [ recallStage1
          , recallStage2
          , recallStage3
          , recallStage4
          , TestStage testType
          ]
        )
    else if strength < 0.07 then
        -- e.g. first test was 70% or less, this is second test
        ( ReadStage
        , [ recallStage2
          , TestStage testType
          ]
        )
    else
        ( TestStage testType
        , []
        )


moveToNextStageOrSubStage : Model -> ( Model, Cmd Msg )
moveToNextStageOrSubStage model =
    let
        nextSubStage =
            withCurrentVerse model
                Nothing
                (\currentVerse ->
                    moveToNextSubStage currentVerse.verseStatus currentVerse.currentStage
                )
    in
        case nextSubStage of
            Nothing ->
                moveToNextStage model

            Just ( newStage, cmd ) ->
                updateCurrentVersePlus model
                    Cmd.none
                    (\currentVerse ->
                        ( { currentVerse
                            | currentStage = newStage
                          }
                        , cmd
                        )
                    )


moveToNextSubStage : VerseStatus -> LearningStage -> Maybe ( LearningStage, Cmd Msg )
moveToNextSubStage verseStatus stage =
    case stage of
        Recall def rp ->
            let
                -- Anything hidden is now regarded as 'passed'
                newRecallProgress =
                    { rp
                        | passedWordIds = Set.union rp.passedWordIds rp.hiddenWordIds
                    }
            in
                if recallStageFinished verseStatus newRecallProgress then
                    Nothing
                else
                    Just <|
                        ( Recall def newRecallProgress
                        , hideRandomWords verseStatus def newRecallProgress
                        )

        _ ->
            Nothing


moveToNextStage : Model -> ( Model, Cmd Msg )
moveToNextStage model =
    let
        ( newModel, cmd ) =
            updateCurrentVersePlus model
                Cmd.none
                (\currentVerse ->
                    let
                        finishCmd =
                            finishStage currentVerse currentVerse.currentStage

                        remaining =
                            currentVerse.remainingStageTypes

                        ( newCurrentVerse, initCmd ) =
                            case remaining of
                                [] ->
                                    ( currentVerse, Cmd.none )

                                stage :: stages ->
                                    let
                                        ( newCurrentStage, initCmd ) =
                                            initializeStage stage currentVerse.verseStatus
                                    in
                                        ( { currentVerse
                                            | seenStageTypes = (learningStageTypeForStage currentVerse.currentStage) :: currentVerse.seenStageTypes
                                            , currentStage = newCurrentStage
                                            , remainingStageTypes = stages
                                          }
                                        , initCmd
                                        )
                    in
                        ( newCurrentVerse
                        , Cmd.batch
                            [ finishCmd
                            , initCmd
                            ]
                        )
                )
    in
        ( newModel
        , Cmd.batch
            [ cmd
            , stageOrVerseChangeCommands newModel True
            ]
        )


moveToPreviousStage : Model -> ( Model, Cmd Msg )
moveToPreviousStage model =
    let
        ( newModel, cmd ) =
            updateCurrentVersePlus model
                Cmd.none
                (\currentVerse ->
                    let
                        previous =
                            currentVerse.seenStageTypes
                    in
                        case previous of
                            [] ->
                                ( currentVerse, Cmd.none )

                            stage :: stages ->
                                let
                                    ( newCurrentStage, cmd ) =
                                        initializeStage stage currentVerse.verseStatus
                                in
                                    ( { currentVerse
                                        | seenStageTypes = stages
                                        , currentStage = newCurrentStage
                                        , remainingStageTypes = (learningStageTypeForStage currentVerse.currentStage) :: currentVerse.remainingStageTypes
                                      }
                                    , cmd
                                    )
                )
    in
        ( newModel
        , Cmd.batch
            [ cmd
              -- Do *not* include focus change here, since
              -- they are already focussing the 'back' button and we don't
              -- want to change that
            , stageOrVerseChangeCommands newModel False
            ]
        )


moveToNextVerse : Model -> ( Model, Cmd Msg )
moveToNextVerse model =
    case model.learningSession of
        Session sessionData ->
            let
                verseStore =
                    sessionData.verses

                currentVerseStatus =
                    sessionData.currentVerse.verseStatus
            in
                case getNextVerse verseStore currentVerseStatus of
                    NoMoreVerses ->
                        ( model
                        , sendMsg <| NavigateToWhenDone sessionData.verses.returnTo
                        )

                    VerseNotInStore ->
                        if not (verseLoadInProgress model) then
                            loadVersesImmediate model
                        else
                            ( model
                            , Cmd.none
                            )

                    NextVerseData verse ->
                        let
                            ( newModel1, cmd ) =
                                updateCurrentVersePlus model
                                    Cmd.none
                                    (\cv -> setupCurrentVerse verse sessionData.verses.learningType)

                            loadingQueueBufferSize =
                                3

                            moreVersesToLoad =
                                case List.maximum <| List.map .learnOrder <| verseStore.verseStatuses of
                                    Nothing ->
                                        False

                                    Just max ->
                                        max < verseStore.maxOrderVal

                            ( newModel2, loadMoreCommand ) =
                                if
                                    moreVersesToLoad
                                        && ((getFollowingVersesInStore verseStore currentVerseStatus
                                                |> List.length
                                            )
                                                <= loadingQueueBufferSize
                                           )
                                        && (not <| verseLoadInProgress model)
                                then
                                    loadVersesImmediate newModel1
                                else
                                    ( newModel1, Cmd.none )

                            newModel3 =
                                closeDropdowns newModel2
                        in
                            ( newModel3
                            , Cmd.batch
                                [ cmd
                                , loadMoreCommand
                                , stageOrVerseChangeCommands newModel2 True
                                ]
                            )

        _ ->
            ( model
            , Cmd.none
            )


type NextVerse
    = NoMoreVerses
    | VerseNotInStore
    | NextVerseData VerseStatus


getNextVerse : VerseStore -> VerseStatus -> NextVerse
getNextVerse verseStore verseStatus =
    let
        nextVerseInStore =
            getFollowingVersesInStore verseStore verseStatus
                |> List.sortBy .learnOrder
                |> List.head
    in
        case nextVerseInStore of
            Just verseStatus ->
                NextVerseData verseStatus

            Nothing ->
                if moreVersesToLearn verseStore verseStatus then
                    VerseNotInStore
                else
                    NoMoreVerses


getPreviousVerse : VerseStore -> VerseStatus -> Maybe VerseStatus
getPreviousVerse verseStore verseStatus =
    let
        previousVerseInStore =
            getPreviousVersesInStore verseStore verseStatus
                |> List.sortBy (\v -> -v.learnOrder)
                |> List.head
    in
        case previousVerseInStore of
            Nothing ->
                Nothing

            Just previousVerseStatus ->
                if previousVerseStatus.textOrder == verseStatus.textOrder - 1 then
                    Just previousVerseStatus
                else
                    Nothing


getFollowingVersesInStore : VerseStore -> VerseStatus -> List VerseStatus
getFollowingVersesInStore verseStore verseStatus =
    verseStore.verseStatuses
        |> List.filter (\v -> v.learnOrder > verseStatus.learnOrder)


getPreviousVersesInStore : VerseStore -> VerseStatus -> List VerseStatus
getPreviousVersesInStore verseStore verseStatus =
    verseStore.verseStatuses
        |> List.filter (\v -> v.learnOrder < verseStatus.learnOrder)


moreVersesToLearn : VerseStore -> VerseStatus -> Bool
moreVersesToLearn verseStore currentVerse =
    currentVerse.learnOrder < verseStore.maxOrderVal


setHiddenWords : Model -> Set.Set WordId -> Model
setHiddenWords model hiddenWordIds =
    updateRecallProcess model
        (\recallProgress ->
            { recallProgress
                | hiddenWordIds = hiddenWordIds
                , manuallyShownWordIds = Set.empty
            }
        )


handleWordButtonClicked : Model -> WordId -> ( Model, Cmd Msg )
handleWordButtonClicked model wordId =
    ( updateRecallProcess model
        (\recallProgress ->
            { recallProgress
              -- reveal the word:
                | hiddenWordIds =
                    Set.remove wordId recallProgress.hiddenWordIds
                    -- if the user had to press the button to reveal it, we consider
                    -- it no longer 'passed'
                , passedWordIds =
                    Set.remove wordId recallProgress.passedWordIds
                , manuallyShownWordIds =
                    Set.insert wordId recallProgress.manuallyShownWordIds
            }
        )
    , focusDefaultButton model
    )


handleTypedInput : Model -> String -> ( Model, Cmd Msg )
handleTypedInput model input =
    let
        newModel1 =
            updateTestProgress model
                (\tp ->
                    { tp | currentTypedText = String.trimRight input }
                )

        testingMethod =
            getTestingMethod newModel1

        ( newModel2, cmd ) =
            if shouldCheckTypedWord testingMethod input then
                checkCurrentWordAndUpdate newModel1 input
            else
                ( newModel1, Cmd.none )
    in
        ( newModel2, cmd )


handleTypedEnter : Model -> ( Model, Cmd Msg )
handleTypedEnter model =
    case getCurrentTestProgress model of
        Nothing ->
            ( model, Cmd.none )

        Just tp ->
            let
                currentTypedText =
                    tp.currentTypedText

                testingMethod =
                    getTestingMethod model

                ( newModel, cmd ) =
                    if shouldCheckTypedWord testingMethod (currentTypedText ++ "\n") then
                        checkCurrentWordAndUpdate model currentTypedText
                    else
                        ( model, Cmd.none )
            in
                ( newModel, cmd )


handleOnScreenButtonClick : Model -> String -> ( Model, Cmd Msg )
handleOnScreenButtonClick model buttonText =
    checkCurrentWordAndUpdate model buttonText


handleUseHint : Model -> ( Model, Cmd Msg )
handleUseHint model =
    let
        ( newModel, cmd ) =
            updateCurrentVersePlus model
                Cmd.none
                (\currentVerse ->
                    withCurrentTestWord currentVerse
                        ( currentVerse, Cmd.none )
                        (\testType testProgress currentWord ->
                            markWord Hint currentWord.word testProgress testType currentVerse (getTestingMethod model) model.preferences
                        )
                )
    in
        ( newModel
        , Cmd.batch
            -- markWord may have moved us to next verse.
            [ stageOrVerseChangeCommands newModel True
            , cmd
            ]
        )


shouldCheckTypedWord : TestingMethod -> String -> Bool
shouldCheckTypedWord testingMethod input =
    let
        trimmedText =
            String.trim input
    in
        case testingMethod of
            FullWords ->
                -- TODO - allow ':' '.' etc in verse references
                String.length trimmedText
                    > 0
                    && ((String.right 1 input == " ")
                            || (String.right 1 input == "\n")
                       )

            FirstLetter ->
                String.length trimmedText > 0

            OnScreen ->
                False


checkCurrentWordAndUpdate : Model -> String -> ( Model, Cmd Msg )
checkCurrentWordAndUpdate model input =
    let
        testingMethod =
            getTestingMethod model

        ( newModel, cmd ) =
            updateCurrentVersePlus model
                Cmd.none
                (\currentVerse ->
                    withCurrentTestWord currentVerse
                        ( currentVerse, Cmd.none )
                        (\testType testProgress currentWord ->
                            let
                                correct =
                                    checkWord currentWord.word.text input testingMethod

                                checkResult =
                                    (if correct then
                                        Success
                                     else
                                        Failure input
                                    )
                            in
                                markWord checkResult currentWord.word testProgress testType currentVerse testingMethod model.preferences
                        )
                )
    in
        ( newModel
        , Cmd.batch
            [ stageOrVerseChangeCommands newModel True
            , cmd
            ]
        )


checkWord : String -> String -> TestingMethod -> Bool
checkWord word input testingMethod =
    let
        wordN =
            normalizeWordForTest word

        inputN =
            normalizeWordForTest input
    in
        case testingMethod of
            FullWords ->
                if String.length wordN <= 2 then
                    wordN == inputN
                else
                    ((String.left 1 wordN
                        == String.left 1 inputN
                     )
                        && (damerauLevenshteinDistance wordN inputN
                                <= (ceiling ((toFloat <| String.length wordN) / 4.0))
                           )
                    )

            FirstLetter ->
                String.right 1 inputN == String.left 1 wordN

            OnScreen ->
                normalizeWordForSuggestion word == input


normalizeWordForTest : String -> String
normalizeWordForTest =
    String.trim >> stripPunctuation >> simplifyTurkish >> String.toLower


normalizeWordForSuggestion : String -> String
normalizeWordForSuggestion =
    String.trim >> stripOuterPunctuation >> String.toLower


punctuationRegex : String
punctuationRegex =
    "[\"'\\.,;!?:\\/#!$%\\^&\\*{}=\\-_`~()\\[\\]“”‘’—]"


stripPunctuation : String -> String
stripPunctuation =
    regexRemoveAll punctuationRegex


stripOuterPunctuation : String -> String
stripOuterPunctuation =
    regexRemoveAll ("^" ++ punctuationRegex ++ "+")
        >> regexRemoveAll (punctuationRegex ++ "+$")


regexRemoveAll : String -> String -> String
regexRemoveAll regex =
    R.replace R.All (R.regex regex) (\m -> "")


simplifyTurkish : String -> String
simplifyTurkish =
    translate "ÂâÇçĞğİıÖöŞşÜü" "AaCcGgIiOoSsUu"


markWord : CheckResult -> Word -> TestProgress -> TestType -> CurrentVerse -> TestingMethod -> Preferences -> ( CurrentVerse, Cmd Msg )
markWord checkResult word testProgress testType verse testingMethod preferences =
    let
        attempt =
            getWordAttemptWithInitial testProgress word testingMethod

        newCheckResults =
            checkResult :: attempt.checkResults

        allowedMistakes =
            allowedMistakesForTestingMethod testingMethod

        ( shouldMoveOn, newTypedText ) =
            case checkResult of
                Success ->
                    ( True, "" )

                Hint ->
                    let
                        previousHintCountForWord =
                            attempt.checkResults |> List.filter isAttemptHint |> List.length

                        singleLetterWord =
                            (normalizeWordForTest word.text |> String.length) == 1

                        firstLetterTestingMethod =
                            case testingMethod of
                                FirstLetter ->
                                    True

                                _ ->
                                    False
                    in
                        if singleLetterWord || previousHintCountForWord > 0 || firstLetterTestingMethod then
                            -- full word hint, move to next word
                            ( True, "" )
                        else
                            -- single letter hint
                            ( False, word.text |> stripPunctuation |> String.left 1 )

                Failure _ ->
                    let
                        finalFailure =
                            (newCheckResults |> List.filter isAttemptFailure |> List.length) > allowedMistakes
                    in
                        ( finalFailure
                        , if finalFailure then
                            ""
                          else
                            testProgress.currentTypedText
                        )

        attempt2 =
            { attempt
                | checkResults = newCheckResults
                , finished = shouldMoveOn
                , allowedMistakes = allowedMistakes
            }

        newAttempts =
            updateWordAttempts testProgress word attempt2

        currentTestWordList =
            getCurrentTestWordList verse testingMethod

        newTestProgress1 =
            { testProgress
                | attemptRecords = newAttempts
                , currentTypedText = newTypedText
            }

        testAccuracy =
            getTestResult newTestProgress1

        nextCurrentWord =
            if shouldMoveOn then
                case testProgress.currentWord of
                    TestFinished r ->
                        TestFinished r

                    CurrentWord cw ->
                        let
                            nextI =
                                cw.overallIndex + 1
                        in
                            case getAt currentTestWordList nextI of
                                Just nextWord ->
                                    if isReference nextWord.type_ && not (shouldTestReferenceForTestingMethod testingMethod) then
                                        TestFinished { accuracy = testAccuracy }
                                    else
                                        CurrentWord
                                            { word = nextWord
                                            , overallIndex = nextI
                                            }

                                Nothing ->
                                    TestFinished { accuracy = testAccuracy }
            else
                testProgress.currentWord

        newTestProgress2 =
            { newTestProgress1
                | currentWord = nextCurrentWord
            }

        newCurrentVerse =
            { verse
                | currentStage =
                    Test testType newTestProgress2
            }

        actionCompleteCommand =
            if
                (shouldMoveOn
                    && (case nextCurrentWord of
                            TestFinished _ ->
                                True

                            _ ->
                                False
                       )
                    && (testProgress.currentWord /= nextCurrentWord)
                )
            then
                recordTestComplete newCurrentVerse testAccuracy testType
            else
                Cmd.none

        ( vibrateCommand, beepCommand ) =
            if isAttemptFailure checkResult then
                if shouldMoveOn then
                    -- final failure
                    ( LearnPorts.vibrateDevice 50, LearnPorts.beep ( 220.0, 0.2 ) )
                else
                    -- mistake only
                    ( LearnPorts.vibrateDevice 25, LearnPorts.beep ( 330.0, 0.15 ) )
            else
                ( Cmd.none, Cmd.none )
    in
        ( newCurrentVerse
        , Cmd.batch
            [ actionCompleteCommand
            , if preferences.enableVibration then
                vibrateCommand
              else
                Cmd.none
            , if preferences.enableSounds then
                beepCommand
              else
                Cmd.none
            ]
        )


getCurrentTestWordList : CurrentVerse -> TestingMethod -> List Word
getCurrentTestWordList currentVerse testingMethod =
    wordsForVerse currentVerse.verseStatus (learningStageTypeForStage currentVerse.currentStage) testingMethod


getWordAttempt : TestProgress -> Word -> Maybe Attempt
getWordAttempt testProgress word =
    Dict.get (getWordId word) testProgress.attemptRecords


getWordAttemptWithInitial : TestProgress -> Word -> TestingMethod -> Attempt
getWordAttemptWithInitial testProgress word testingMethod =
    case getWordAttempt testProgress word of
        Nothing ->
            { finished = False
            , checkResults = []
            , allowedMistakes = allowedMistakesForTestingMethod testingMethod
            }

        Just a ->
            a


getWordId : Word -> WordId
getWordId word =
    ( toString word.type_, word.index )


updateWordAttempts : TestProgress -> Word -> Attempt -> AttemptRecords
updateWordAttempts testProgress word attempt =
    Dict.insert ( toString word.type_, word.index ) attempt testProgress.attemptRecords


allowedMistakesForTestingMethod : TestingMethod -> number
allowedMistakesForTestingMethod testingMethod =
    case testingMethod of
        FullWords ->
            2

        FirstLetter ->
            1

        OnScreen ->
            0


allowedHints : CurrentVerse -> TestingMethod -> Int
allowedHints currentVerse testingMethod =
    let
        wordCount =
            currentVerse.verseStatus.scoringTextWords |> List.length |> toFloat

        -- Very short verses should get few hints
        -- For FirstLetter testing method, a hint is always
        -- the entire word, so give fewer hints still
    in
        case testingMethod of
            FullWords ->
                -- 1 to 3 word verses - 1 hint, 4 to 6 - 2 etc.
                -- maximum 4
                min (wordCount / 3 |> floor) 4

            FirstLetter ->
                -- 1 to 5 word verses - 1 hint, 6 to 10 - 2 etc.
                -- maximum 3
                min (wordCount / 5 |> floor) 3

            OnScreen ->
                0


shouldTestReferenceForTestingMethod : TestingMethod -> Bool
shouldTestReferenceForTestingMethod testingMethod =
    case testingMethod of
        FullWords ->
            True

        FirstLetter ->
            True

        OnScreen ->
            False


isReference : WordType -> Bool
isReference wordType =
    case wordType of
        BodyWord ->
            False

        ReferenceWord ->
            True


shouldUseHardTestingMode : CurrentVerse -> Bool
shouldUseHardTestingMode currentVerse =
    currentVerse.verseStatus.strength > hardModeStrengthThreshold


type alias UpdateTypingBoxData =
    { typingBoxId : String
    , typingBoxContainerId : String
    , wordButtonId : String
    , expectedClass : String
    , hardMode : Bool
    , refocus : Bool
    }


updateTypingBoxCommand : Model -> Bool -> Cmd msg
updateTypingBoxCommand model refocus =
    LearnPorts.updateTypingBox (getUpdateTypingBoxData model refocus)


getUpdateTypingBoxData : Model -> Bool -> UpdateTypingBoxData
getUpdateTypingBoxData model refocus =
    case getCurrentTestProgress model of
        Just tp ->
            case tp.currentWord of
                TestFinished _ ->
                    hideTypingBoxData

                CurrentWord cw ->
                    { typingBoxId = typingBoxId
                    , typingBoxContainerId = typingBoxContainerId
                    , wordButtonId = idForButton cw.word
                    , expectedClass = classForTypingBox <| typingBoxInUse tp (getTestingMethod model)
                    , hardMode =
                        case getCurrentVerse model of
                            Nothing ->
                                False

                            Just currentVerse ->
                                shouldUseHardTestingMode currentVerse
                    , refocus = refocus
                    }

        Nothing ->
            hideTypingBoxData


hideTypingBoxData : UpdateTypingBoxData
hideTypingBoxData =
    { typingBoxId = typingBoxId
    , typingBoxContainerId = typingBoxContainerId
    , wordButtonId = ""
    , expectedClass = classForTypingBox False
    , hardMode = False
    , refocus = True
    }


focusDefaultButton : Model -> Cmd Msg
focusDefaultButton model =
    withSessionData model
        Cmd.none
        (\sessionData ->
            let
                buttons =
                    buttonsForStage model sessionData.currentVerse sessionData.verses model.preferences

                defaultButtons =
                    List.filter (\b -> b.default == Default) buttons

                shouldFocusTypingBox =
                    case getCurrentTestProgress model of
                        Just tp ->
                            typingBoxInUse tp (getTestingMethod model)

                        Nothing ->
                            False

                idToFocus =
                    if shouldFocusTypingBox then
                        -- This will be done by updateTypingBox
                        Nothing
                    else
                        case defaultButtons of
                            [] ->
                                Nothing

                            b :: rest ->
                                Just b.id
            in
                case idToFocus of
                    Nothing ->
                        Cmd.none

                    Just id ->
                        -- Dom.focus can fail if the control doesn't exist yet.
                        -- Not sure if this is really possible, but we
                        -- re-attempt focus for the case of the control not
                        -- appearing in the DOM yet.
                        Task.attempt (handleFocusResult id 5) (Dom.focus id)
        )


handleFocusResult : String -> Int -> (Result error value -> Msg)
handleFocusResult id remainingAttempts =
    if remainingAttempts <= 0 then
        always Noop
    else
        (\r ->
            let
                _ =
                    Debug.log ("Dom.focus failed - id " ++ id)
            in
                case r of
                    Ok _ ->
                        Noop

                    Err _ ->
                        ReattemptFocus id (remainingAttempts - 1)
        )


getWordSuggestions : VerseStatus -> Word -> WordSuggestions
getWordSuggestions verseStatus word =
    case word.type_ of
        BodyWord ->
            let
                l =
                    getAt verseStatus.suggestions word.index
            in
                case l of
                    Nothing ->
                        []

                    Just l ->
                        List.sort <| List.map normalizeWordForSuggestion (word.text :: l)

        ReferenceWord ->
            []


startMorePractice : Model -> Float -> ( Model, Cmd Msg )
startMorePractice model accuracy =
    let
        testType =
            MorePracticeTest

        ( firstStageType, remainingStageTypes ) =
            if accuracy < 0.5 then
                -- 0.5 is quite low, treat as if starting afresh
                getStagesByStrength 0 testType
            else if accuracy < 0.8 then
                ( ReadStage
                , [ recallStage2
                  , recallStage4
                  , TestStage testType
                  ]
                )
            else
                ( recallStage2
                , [ recallStage4
                  , TestStage testType
                  ]
                )

        ( newModel, cmd ) =
            updateCurrentVersePlus model
                Cmd.none
                (\currentVerse ->
                    let
                        ( newCurrentStage, cmd ) =
                            initializeStage firstStageType currentVerse.verseStatus
                    in
                        ( { currentVerse
                            | currentStage = newCurrentStage
                            , seenStageTypes = []
                            , remainingStageTypes = remainingStageTypes
                          }
                        , cmd
                        )
                )
    in
        ( newModel
        , Cmd.batch
            [ stageOrVerseChangeCommands newModel True
            , cmd
            ]
        )



{- API calls -}
{- For some calls, we need to:

   - Keep track of the fact that the call is in progress
   - Retry if necessary
   - Avoid leaving the page if the call (or retries) are in progress.

   So the data needed for these calls is stored on the model, along with
   info about attempts etc.


-}


type TrackedHttpCall
    = RecordTestComplete CurrentVerse Float TestType
    | RecordReadComplete CurrentVerse
    | LoadVerses


maxHttpRetries : number
maxHttpRetries =
    6


trackedHttpCallCaption : TrackedHttpCall -> String
trackedHttpCallCaption call =
    case call of
        RecordTestComplete currentVerse _ _ ->
            interpolate "Saving score - {0}" [ currentVerse.verseStatus.localizedReference ]

        RecordReadComplete currentVerse ->
            interpolate "Recording read - {0}" [ currentVerse.verseStatus.localizedReference ]

        LoadVerses ->
            "Loading items for learning..."


type alias CallId =
    Int


{-| Start a tracked call, first registering
it and then triggering its execution.

-}
startTrackedCall : Model -> TrackedHttpCall -> ( Model, Cmd Msg )
startTrackedCall model trackedCall =
    let
        ( newModel, callId ) =
            addTrackedCall model trackedCall

        cmd =
            sendMsg <| MakeHttpCall callId
    in
        ( newModel, cmd )


{-| For a given TrackedHttpCall object, return a command that triggers
the HTTP call to be started.

Technically this doesn't need to return a Cmd Msg (we could just update the
model directly in all places that use this function), but rewiring from
`Http.send` to using `TrackedHttpCall` is much easier if we use a `Cmd Msg` and
this utility
-}
sendStartTrackedCallMsg : TrackedHttpCall -> Cmd Msg
sendStartTrackedCallMsg trackedCall =
    sendMsg <| TrackHttpCall trackedCall


{-| The motivation for having 'MakeHttpCall' and 'makeHttpCall' separate from
'startTrackedCall' is that when we retry, we want to add a delay. It seems
easier to just use the `delay` helper and send another message than to convert
`Http.send` calls into Task.Tasks in order to insert Process.sleep tasks etc.
(at least, I couldn't figure out the type problems caused by trying to work with
Tasks instead of Cmd Msg).

-}
makeHttpCall : Model -> CallId -> ( Model, Cmd Msg )
makeHttpCall model callId =
    let
        cmd =
            case Dict.get callId model.currentHttpCalls of
                Nothing ->
                    Cmd.none

                Just { call } ->
                    case call of
                        RecordTestComplete currentVerse accuracy testType ->
                            callRecordTestComplete model.httpConfig callId currentVerse accuracy testType

                        RecordReadComplete currentVerse ->
                            callRecordReadComplete model.httpConfig callId currentVerse

                        LoadVerses ->
                            callLoadVerses model.httpConfig callId model
    in
        ( model, cmd )


addTrackedCall : Model -> TrackedHttpCall -> ( Model, CallId )
addTrackedCall model trackedCall =
    let
        callId =
            case Dict.keys model.currentHttpCalls |> List.reverse |> List.head of
                Nothing ->
                    1

                Just i ->
                    i + 1

        newCurrentCalls =
            Dict.insert callId { call = trackedCall, attempts = 1 } model.currentHttpCalls
    in
        ( { model
            | currentHttpCalls = newCurrentCalls
          }
        , callId
        )


markCallFinished : Model -> CallId -> Model
markCallFinished model callId =
    { model
        | currentHttpCalls = Dict.remove callId model.currentHttpCalls
    }


markPermanentFailCall : Model -> CallId -> Model
markPermanentFailCall model callId =
    case Dict.get callId model.currentHttpCalls of
        Nothing ->
            model

        Just { call } ->
            { model
                | currentHttpCalls = Dict.remove callId model.currentHttpCalls
                , permanentFailHttpCalls = call :: model.permanentFailHttpCalls
            }


markFailAndRetry : Model -> CallId -> ( Model, Cmd Msg )
markFailAndRetry model callId =
    case Dict.get callId model.currentHttpCalls of
        Nothing ->
            ( model, Cmd.none )

        Just { call, attempts } ->
            if attempts == maxHttpRetries then
                ( markPermanentFailCall model callId
                , Cmd.none
                )
            else
                let
                    newModel =
                        { model
                            | currentHttpCalls =
                                Dict.insert callId
                                    { call = call
                                    , attempts = attempts + 1
                                    }
                                    model.currentHttpCalls
                        }

                    delayTask =
                        Process.sleep (Time.second * (2 ^ attempts |> toFloat))
                in
                    ( newModel
                    , delay
                        (Time.second * (2 ^ attempts |> toFloat))
                        (MakeHttpCall callId)
                    )


delay : Time.Time -> msg -> Cmd msg
delay time msg =
    Process.sleep time
        |> Task.perform (\_ -> msg)


verseLoadInProgress : Model -> Bool
verseLoadInProgress model =
    Dict.values model.currentHttpCalls |> List.any (\{ call } -> call == LoadVerses)


verseLoadFailed : Model -> Bool
verseLoadFailed model =
    model.permanentFailHttpCalls |> List.any (\c -> c == LoadVerses)


versesToLearnUrl : String
versesToLearnUrl =
    "/api/learnscripture/v1/versestolearn2/"


actionCompleteUrl : String
actionCompleteUrl =
    "/api/learnscripture/v1/actioncomplete/"


{-| Trigger verse load via a Cmd
-}
loadVerses : Cmd Msg
loadVerses =
    sendStartTrackedCallMsg LoadVerses


{-| Trigger verse load immediately

More robust than loadVerses, useful when we
have access to the full model
-}
loadVersesImmediate : Model -> ( Model, Cmd Msg )
loadVersesImmediate model =
    startTrackedCall model LoadVerses


callLoadVerses : HttpConfig -> CallId -> Model -> Cmd Msg
callLoadVerses httpConfig callId model =
    let
        verseStatuses =
            case model.learningSession of
                Session sessionData ->
                    sessionData.verses.verseStatuses

                _ ->
                    []

        url =
            Erl.parse versesToLearnUrl
                |> Erl.addQuery "format" "json"
                |> Erl.addQuery "seen"
                    (verseStatuses
                        |> List.map (.id >> toString)
                        |> String.join ","
                    )
                |> Erl.toString
    in
        Http.send (VersesToLearn callId) (Http.get url verseBatchRawDecoder)


recordTestComplete : CurrentVerse -> Float -> TestType -> Cmd Msg
recordTestComplete currentVerse accuracy testType =
    sendStartTrackedCallMsg (RecordTestComplete currentVerse accuracy testType)


callRecordTestComplete : HttpConfig -> CallId -> CurrentVerse -> Float -> TestType -> Cmd Msg
callRecordTestComplete httpConfig callId currentVerse accuracy testType =
    let
        verseStatus =
            currentVerse.verseStatus

        body =
            Http.multipartBody
                [ Http.stringPart "uvs_id" (toString verseStatus.id)
                , Http.stringPart "uvs_needs_testing" (encodeBool <| verseStatus.needsTesting)
                , Http.stringPart "stage" stageTypeTest
                , Http.stringPart "accuracy" (encodeFloat accuracy)
                , Http.stringPart "practice"
                    (encodeBool <|
                        (currentVerse.sessionLearningType == Practice)
                            || (testType == MorePracticeTest)
                    )
                ]
    in
        Http.send (RecordActionCompleteReturned callId)
            (myHttpPost httpConfig
                actionCompleteUrl
                body
                emptyDecoder
            )


recordReadComplete : CurrentVerse -> Cmd Msg
recordReadComplete currentVerse =
    sendStartTrackedCallMsg (RecordReadComplete currentVerse)


callRecordReadComplete : HttpConfig -> CallId -> CurrentVerse -> Cmd Msg
callRecordReadComplete httpConfig callId currentVerse =
    let
        verseStatus =
            currentVerse.verseStatus

        body =
            Http.multipartBody
                [ Http.stringPart "uvs_id" (toString verseStatus.id)
                , Http.stringPart "uvs_needs_testing" (encodeBool <| verseStatus.needsTesting)
                , Http.stringPart "stage" stageTypeRead
                ]
    in
        Http.send (RecordActionCompleteReturned callId)
            (myHttpPost httpConfig
                actionCompleteUrl
                body
                emptyDecoder
            )


{-| Given an `update` like function of type `Model -> a -> ( Model, Cmd Msg)`,
a model, a CallId and a Http result, handles the retries for the call, and
executes the update function.

-}
handleRetries : (Model -> a -> ( Model, Cmd Msg )) -> Model -> CallId -> Result.Result Http.Error a -> ( Model, Cmd Msg )
handleRetries continuation model callId result =
    case result of
        Ok v ->
            let
                newModel1 =
                    markCallFinished model callId

                ( newModel2, cmd ) =
                    continuation newModel1 v
            in
                ( newModel2, cmd )

        Err err ->
            case err of
                Http.BadUrl _ ->
                    ( markPermanentFailCall model callId
                    , Cmd.none
                    )

                _ ->
                    -- Others could all be temporary in theory, so we try again.
                    -- TODO save error message
                    markFailAndRetry model callId


handleVersesToLearn : Model -> VerseBatchRaw -> ( Model, Cmd Msg )
handleVersesToLearn model verseBatchRaw =
    let
        ( maybeBatchSession, sessionCmd ) =
            normalizeVerseBatch verseBatchRaw |> verseBatchToSession

        ( newSession, previousSessionEmpty ) =
            case model.learningSession of
                Session origSession ->
                    case maybeBatchSession of
                        Nothing ->
                            ( Just origSession, False )

                        Just batchSession ->
                            ( Just <| mergeSession origSession batchSession, False )

                _ ->
                    ( maybeBatchSession, True )
    in
        case newSession of
            Nothing ->
                ( model, Navigation.load dashboardUrl )

            Just ns ->
                let
                    newModel =
                        { model
                            | learningSession = Session ns
                        }
                in
                    ( newModel
                    , Cmd.batch
                        [ sessionCmd
                        , if previousSessionEmpty then
                            stageOrVerseChangeCommands newModel True
                          else
                            Cmd.none
                        ]
                    )


handleRecordActionCompleteReturned : Model -> () -> ( Model, Cmd Msg )
handleRecordActionCompleteReturned model () =
    ( model
      -- TODO - load score logs
    , Cmd.none
    )


sendMsg : msg -> Cmd msg
sendMsg msg =
    Task.succeed msg |> Task.perform identity


encodeBool : Bool -> String
encodeBool =
    JE.bool >> JE.encode 0


encodeFloat : Float -> String
encodeFloat =
    JE.float >> JE.encode 0


myHttpPost : HttpConfig -> String -> Http.Body -> JD.Decoder a -> Http.Request a
myHttpPost config url body decoder =
    Http.request
        { method = "POST"
        , headers =
            [ Http.header "X-CSRFToken" config.csrfMiddlewareToken
            , Http.header "X-Requested-With" "XMLHttpRequest"
            ]
        , url = url
        , body = body
        , expect = Http.expectJson decoder
        , timeout = Nothing
        , withCredentials = False
        }



-- The following constants are defined in StageType.
-- Can probably clean this up if we define
-- LearningStage as a pure enum and rework this.


stageTypeTest : String
stageTypeTest =
    "TEST"


stageTypeRead : String
stageTypeRead =
    "READ"



{- Subscriptions -}


subscriptions : a -> Sub Msg
subscriptions model =
    Sub.batch
        [ Window.resizes WindowResize
        , LearnPorts.receivePreferences ReceivePreferences
        ]



{- Decoder and encoders -}


preferencesDecoder : JD.Decoder Preferences
preferencesDecoder =
    JDP.decode Preferences
        |> JDP.required "preferencesSetup" JD.bool
        |> JDP.required "enableAnimations" JD.bool
        |> JDP.required "enableSounds" JD.bool
        |> JDP.required "enableVibration" JD.bool
        |> JDP.required "desktopTestingMethod" testingMethodDecoder
        |> JDP.required "touchscreenTestingMethod" testingMethodDecoder


testingMethodDecoder : JD.Decoder TestingMethod
testingMethodDecoder =
    enumDecoder
        [ ( "FULL_WORDS", FullWords )
        , ( "FIRST_LETTER", FirstLetter )
        , ( "ON_SCREEN", OnScreen )
        ]


verseBatchRawDecoder : JD.Decoder VerseBatchRaw
verseBatchRawDecoder =
    JDP.decode verseBatchRawCtr
        |> JDP.required "learning_type" (nullOr learningTypeDecoder)
        |> JDP.required "return_to" JD.string
        |> JDP.required "max_order_val" (nullOr JD.int)
        |> JDP.required "verse_statuses" (JD.list verseStatusRawDecoder)
        |> JDP.required "versions" (JD.list versionDecoder)
        |> JDP.required "verse_sets" (JD.list verseSetDecoder)


nullOr : JD.Decoder a -> JD.Decoder (Maybe a)
nullOr decoder =
    JD.oneOf
        [ JD.null Nothing
        , JD.map Just decoder
        ]


verseStatusRawDecoder : JD.Decoder VerseStatusRaw
verseStatusRawDecoder =
    JDP.decode verseStatusRawCtr
        |> JDP.required "id" JD.int
        |> JDP.required "strength" JD.float
        |> JDP.required "localized_reference" JD.string
        |> JDP.required "needs_testing" JD.bool
        |> JDP.required "text_order" JD.int
        |> JDP.required "suggestions" (JD.list (JD.list (JD.string)))
        |> JDP.required "scoring_text_words" (JD.list (JD.string))
        |> JDP.required "title_text" JD.string
        |> JDP.required "learn_order" JD.int
        |> JDP.required "verse_set_id" (nullOr JD.int)
        |> JDP.required "version_slug" JD.string


verseSetDecoder : JD.Decoder VerseSet
verseSetDecoder =
    JDP.decode VerseSet
        |> JDP.required "id" JD.int
        |> JDP.required "set_type" verseSetTypeDecoder
        |> JDP.required "name" JD.string
        |> JDP.required "get_absolute_url" JD.string


verseSetTypeDecoder : JD.Decoder VerseSetType
verseSetTypeDecoder =
    enumDecoder
        [ ( "SELECTION", Selection )
        , ( "PASSAGE", Passage )
        ]


versionDecoder : JD.Decoder Version
versionDecoder =
    JDP.decode Version
        |> JDP.required "full_name" JD.string
        |> JDP.required "short_name" JD.string
        |> JDP.required "slug" JD.string
        |> JDP.required "url" JD.string
        |> JDP.required "text_type" textTypeDecoder


enumDecoder : List ( String, a ) -> JD.Decoder a
enumDecoder items =
    let
        d =
            Dict.fromList items
    in
        JD.string
            |> JD.andThen
                (\str ->
                    case (Dict.get str d) of
                        Just v ->
                            JD.succeed v

                        Nothing ->
                            JD.fail <| "Unknown enum value: " ++ str
                )


textTypeDecoder : JD.Decoder TextType
textTypeDecoder =
    enumDecoder
        [ ( "BIBLE", Bible )
        , ( "CATECHISM", Catechism )
        ]


learningTypeDecoder : JD.Decoder LearningType
learningTypeDecoder =
    enumDecoder
        [ ( "REVISION", Revision )
        , ( "LEARNING", Learning )
        , ( "PRACTICE", Practice )
        ]


emptyDecoder : JD.Decoder ()
emptyDecoder =
    JD.succeed ()



{- General utils -}


onClickSimply : msg -> H.Attribute msg
onClickSimply msg =
    E.onWithOptions
        "click"
        { stopPropagation = False
        , preventDefault = True
        }
        (JD.succeed msg)


dedupeBy : (a -> comparable) -> List a -> List a
dedupeBy keyFunc list =
    let
        helper =
            \keyFunc list existing ->
                case list of
                    [] ->
                        []

                    first :: rest ->
                        let
                            key =
                                keyFunc first
                        in
                            if Set.member key existing then
                                helper keyFunc rest existing
                            else
                                first :: helper keyFunc rest (Set.insert key existing)
    in
        helper keyFunc list Set.empty


listIndices : List a -> List Int
listIndices l =
    List.range 0 (List.length l)


getAt : List a -> Int -> Maybe a
getAt xs idx =
    List.head <| List.drop idx xs


damerauLevenshteinDistance : String -> String -> Int
damerauLevenshteinDistance =
    Native.StringUtils.damerauLevenshteinDistance


chooseN : Int -> List a -> Random.Generator (List a)
chooseN n items =
    Random.List.shuffle items |> Random.map (\items -> List.take n items)


zip : List a -> List b -> List ( a, b )
zip =
    List.map2 (,)


translate : String -> String -> String -> String
translate fromStr toStr target =
    let
        allPairs =
            zip (String.toList fromStr) (String.toList toStr)

        makeMapper =
            \pairs ->
                case pairs of
                    [] ->
                        identity

                    ( c1, c2 ) :: rest ->
                        (\c ->
                            if c == c1 then
                                c2
                            else
                                makeMapper rest c
                        )

        mapper =
            makeMapper allPairs
    in
        String.map mapper target
