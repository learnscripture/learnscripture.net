module Learn exposing (..)

import Dict
import Html as H
import Html.Attributes as A
import Html.Events as E
import Http
import Json.Decode as JD
import Json.Decode.Pipeline as JDP
import Maybe
import Navigation
import Regex as R
import Set
import String
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



{- Flags and external inputs -}


type alias Flags =
    { preferences : JD.Value
    , account : Maybe AccountData
    , isTouchDevice : Bool
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
      , learningSession = Loading
      }
    , loadVerses
    )



{- Model -}


type alias Model =
    { preferences : Preferences
    , user : User
    , learningSession : LearningSession
    , isTouchDevice : Bool
    }


type alias Preferences =
    { preferencesSetup : Bool
    , enableAnimations : Bool
    , enableSounds : Bool
    , enableVibration : Bool
    , desktopTestingMethod : TestingMethod
    , touchscreenTestingMethod : TestingMethod
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
    , currentStage : LearningStage
    , remainingStages : List LearningStage
    , seenStages : List LearningStage
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
    , seen : List UvsId
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


type alias Suggestions =
    List (List String)


type alias VerseStatusBase a =
    { a
        | id : Int
        , strength : Float
        , localizedReference : String
        , needsTesting : Bool
        , textOrder : Int
        , suggestions : Suggestions
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
    -> Suggestions
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


topNav : Model -> H.Html msg
topNav model =
    H.nav [ A.class "topbar" ]
        [ H.ul []
            [ H.li [ A.class "dashboard-link" ]
                [ link dashboardUrl "Dashboard" "return" AlignLeft ]
            , H.li [ A.class "preferences-link" ]
                [ link "#" (userDisplayName model.user) "preferences" AlignRight ]
            ]
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

        testingMethod =
            getTestingMethod model
    in
        H.div [ A.id "id-content-wrapper" ]
            [ H.h2 []
                [ H.text currentVerse.verseStatus.titleText ]
            , H.div [ A.id "id-verse-wrapper" ]
                [ H.div [ A.class "current-verse-wrapper" ]
                    [ H.div [ A.class "current-verse" ]
                        (versePartsToHtml currentVerse.currentStage <| partsForVerse currentVerse.verseStatus)
                    ]
                , copyrightNotice currentVerse.verseStatus.version
                ]
            , actionButtons currentVerse model.preferences
            , instructions currentVerse testingMethod
              -- We make typing box a permanent fixture to avoid issues with
              -- losing focus and screen keyboards then disappearing
            , typingBox currentVerse.currentStage testingMethod
            ]



{- View helpers - word/sentence splitting and word buttons -}


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


partsForVerse : VerseStatus -> List Part
partsForVerse verse =
    (List.map2 verseWordToParts verse.scoringTextWords (listIndices verse.scoringTextWords)
        |> List.concat
    )
        ++ if shouldShowReference verse then
            [ Linebreak ] ++ referenceToParts verse.localizedReference
           else
            []


wordsForVerse : VerseStatus -> List Word
wordsForVerse verseStatus =
    let
        parts =
            partsForVerse verseStatus
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



-- only used for within verse body
-- The initial sentence has already been split into words server side, and this
-- function does not split off punctuation, but keeps it as part of the word.


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


versePartsToHtml : LearningStage -> List Part -> List (H.Html msg)
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


wordButton : Word -> LearningStage -> H.Html msg
wordButton wd stage =
    let
        ( classesOuter, classesInner ) =
            wordButtonClasses wd stage
    in
        H.span
            [ A.class <| String.join " " classesOuter
            , A.id <| idForButton wd
            ]
            [ H.span
                [ A.class <| String.join " " ([ "wordpart" ] ++ classesInner) ]
                [ H.text wd.text ]
            ]


wordButtonClasses : Word -> LearningStage -> ( List String, List String )
wordButtonClasses wd stage =
    let
        outer1 =
            case wd.type_ of
                BodyWord ->
                    [ "word" ]

                ReferenceWord ->
                    [ "word", "reference" ]

        outer2 =
            case stage of
                TestStage tp ->
                    case getWordAttempt tp wd of
                        Nothing ->
                            []

                        Just attempt ->
                            if attempt.finished then
                                if List.all (\r -> r == Failure) attempt.checkResults then
                                    [ "incorrect" ]
                                else if List.all (\r -> r == Success) attempt.checkResults then
                                    [ "correct" ]
                                else
                                    [ "partially-correct" ]
                            else
                                []

                _ ->
                    []

        inner =
            case stage of
                TestStage tp ->
                    case getWordAttempt tp wd of
                        Nothing ->
                            [ "hidden" ]

                        Just _ ->
                            []

                _ ->
                    []
    in
        ( outer1 ++ outer2, inner )


copyrightNotice : Version -> H.Html msg
copyrightNotice version =
    let
        caption =
            version.shortName ++ " - " ++ version.fullName
    in
        H.div [ A.id "id-copyright-notice" ]
            (if version.url == "" then
                [ H.text caption ]
             else
                [ H.a [ A.href version.url ]
                    [ H.text caption ]
                ]
            )


typingBoxId : String
typingBoxId =
    "id-typing"


typingBox : LearningStage -> TestingMethod -> H.Html Msg
typingBox stage testingMethod =
    let
        ( value, inUse, lastCheckFailed ) =
            case stage of
                TestStage tp ->
                    let
                        lastCheckFailed =
                            case getCurrentWordAttempt tp of
                                Nothing ->
                                    False

                                Just attempt ->
                                    case attempt.checkResults of
                                        [] ->
                                            False

                                        r :: remainder ->
                                            r == Failure
                    in
                        ( tp.currentTypedText
                        , typingBoxInUse tp testingMethod
                        , lastCheckFailed
                        )

                _ ->
                    ( "", False, False )
    in
        H.input
            ([ A.id typingBoxId
             , A.value value
             , A.class
                (classForTypingBox inUse
                    ++ (if lastCheckFailed then
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
            case getCurrentWord testProgress of
                Nothing ->
                    False

                Just _ ->
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


actionButtons : CurrentVerse -> Preferences -> H.Html Msg
actionButtons verse preferences =
    H.div [ A.id "id-action-btns" ]
        (buttonsForStage verse preferences)


type ButtonEnabled
    = Enabled
    | Disabled


type ButtonDefault
    = Default
    | NonDefault


buttonsForStage : CurrentVerse -> Preferences -> List (H.Html Msg)
buttonsForStage verse preferences =
    let
        isRemainingStage =
            not <| List.isEmpty <| List.filter (not << isFinishedStage) verse.remainingStages

        isPreviousStage =
            not <| List.isEmpty verse.seenStages

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
            Read ->
                [ previousStageBtn previousEnabled NonDefault
                , nextStageBtn nextEnabled Default
                ]

            TestStage _ ->
                [ previousStageBtn previousEnabled NonDefault
                , nextStageBtn nextEnabled Default
                ]


getTestingMethod : Model -> TestingMethod
getTestingMethod model =
    if model.isTouchDevice then
        model.preferences.touchscreenTestingMethod
    else
        model.preferences.desktopTestingMethod


previousStageBtn : ButtonEnabled -> ButtonDefault -> H.Html Msg
previousStageBtn enabled default =
    button enabled default PreviousStage "Back"


nextStageBtn : ButtonEnabled -> ButtonDefault -> H.Html Msg
nextStageBtn enabled default =
    button enabled default NextStage "Next"


button : ButtonEnabled -> ButtonDefault -> msg -> String -> H.Html msg
button enabled default clickMsg text =
    let
        class =
            case enabled of
                Enabled ->
                    case default of
                        Default ->
                            "btn primary"

                        NonDefault ->
                            "btn"

                Disabled ->
                    "btn disabled"

        attributes =
            [ A.class class ]

        eventAttributes =
            case enabled of
                Enabled ->
                    [ E.onClick clickMsg ]
                        ++ (case default of
                                Default ->
                                    [ onEnter clickMsg ]

                                NonDefault ->
                                    []
                           )

                Disabled ->
                    []
    in
        H.button (attributes ++ eventAttributes)
            [ H.text text ]


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


instructions : CurrentVerse -> TestingMethod -> H.Html msg
instructions verse testingMethod =
    H.div [ A.id "id-instructions" ]
        (case verse.currentStage of
            Read ->
                [ bold "READ: "
                , H.text "Read the text through (preferably aloud), and click 'Next'."
                ]

            TestStage _ ->
                (case testingMethod of
                    FullWords ->
                        [ bold "TEST: "
                        , H.text
                            ("Testing time! Type the text, pressing space after each word."
                                ++ "(hint: don't sweat the spelling, we should be able to work it out)."
                            )
                        ]

                    FirstLetter ->
                        [ bold "TEST: "
                        , H.text "Testing time! Type the "
                        , bold "first letter"
                        , H.text " of each word."
                        ]

                    OnScreen ->
                        [ bold "TEST: "
                        , H.text "Testing time! For each word choose from the options below."
                        ]
                )
        )



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
makeIcon icon =
    H.i [ A.class ("icon-fw icon-" ++ icon) ] []


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
    = LoadVerses
    | VersesToLearn (Result Http.Error VerseBatchRaw)
    | NextStage
    | PreviousStage
    | TypingBoxInput String
    | TypingBoxEnter
    | WindowResize { width : Int, height : Int }
    | ReceivePreferences JD.Value


update : Msg -> Model -> ( Model, Cmd msg )
update msg model =
    case msg of
        LoadVerses ->
            ( model, Cmd.none )

        VersesToLearn (Ok verseBatchRaw) ->
            let
                maybeBatchSession =
                    normalizeVerseBatch verseBatchRaw |> verseBatchToSession

                newSession =
                    case model.learningSession of
                        Session origSession ->
                            case maybeBatchSession of
                                Nothing ->
                                    Just origSession

                                Just batchSession ->
                                    Just <| mergeSession origSession batchSession

                        _ ->
                            maybeBatchSession
            in
                case newSession of
                    Nothing ->
                        ( model, Navigation.load dashboardUrl )

                    Just ns ->
                        ( { model
                            | learningSession = Session ns
                          }
                        , Cmd.none
                        )

        VersesToLearn (Err errMsg) ->
            ( { model | learningSession = VersesError errMsg }, Cmd.none )

        NextStage ->
            moveToNextStage model

        PreviousStage ->
            moveToPreviousStage model

        TypingBoxInput input ->
            handleTypedInput model input

        TypingBoxEnter ->
            handleTypedEnter model

        WindowResize _ ->
            ( model, updateTypingBoxCommand model )

        ReceivePreferences prefsValue ->
            let
                newModel =
                    { model | preferences = decodePreferences prefsValue }
            in
                ( newModel, updateTypingBoxCommand newModel )



{- Update helpers -}


updateCurrentVerse : Model -> (CurrentVerse -> CurrentVerse) -> Model
updateCurrentVerse model updater =
    case model.learningSession of
        Session sessionData ->
            let
                newCurrentVerse =
                    updater sessionData.currentVerse

                newSessionData =
                    { sessionData
                        | currentVerse = newCurrentVerse
                    }
            in
                { model | learningSession = Session newSessionData }

        _ ->
            model


updateTestProgress : Model -> (TestProgress -> TestProgress) -> Model
updateTestProgress model updater =
    updateCurrentVerse model
        (\currentVerse ->
            case currentVerse.currentStage of
                TestStage tp ->
                    { currentVerse
                        | currentStage =
                            TestStage (updater tp)
                    }

                _ ->
                    currentVerse
        )


getCurrentTestProgress : Model -> Maybe TestProgress
getCurrentTestProgress model =
    case model.learningSession of
        Session sessionData ->
            case sessionData.currentVerse.currentStage of
                TestStage testProgress ->
                    Just testProgress

                _ ->
                    Nothing

        _ ->
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


verseBatchToSession : VerseBatch -> Maybe SessionData
verseBatchToSession batch =
    case List.head batch.verseStatuses of
        Nothing ->
            Nothing

        Just verse ->
            case batch.learningTypeRaw of
                Nothing ->
                    Nothing

                Just learningType ->
                    case batch.maxOrderValRaw of
                        Nothing ->
                            Nothing

                        Just maxOrderVal ->
                            let
                                ( firstStage, remainingStages ) =
                                    getStages learningType verse
                            in
                                Just
                                    { verses =
                                        { verseStatuses = batch.verseStatuses
                                        , learningType = learningType
                                        , returnTo = batch.returnTo
                                        , maxOrderVal = maxOrderVal
                                        , seen = []
                                        }
                                    , currentVerse =
                                        { verseStatus = verse
                                        , currentStage = firstStage
                                        , seenStages = []
                                        , remainingStages = remainingStages
                                        }
                                    }



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



{- Stages -}


type LearningStage
    = Read
    | TestStage TestProgress



-- AttemptRecord should really be:
---  Dict.Dict (WordType, WordIndex) Attempt
-- but Elm doesn't support that


type alias AttemptRecord =
    Dict.Dict ( String, WordIndex ) Attempt


type alias TestProgress =
    { attemptRecord : AttemptRecord
    , currentTypedText : String
    , words : List Word
    , currentWordIndex :
        Maybe WordIndex
        -- Nothing if finished
    }


type alias Attempt =
    { finished : Bool
    , checkResults : List CheckResult
    }


type CheckResult
    = Failure
    | Success


initialTestProgress : VerseStatus -> TestProgress
initialTestProgress verseStatus =
    { attemptRecord = Dict.empty
    , currentTypedText = ""
    , words = wordsForVerse verseStatus
    , currentWordIndex = Just 0
    }


getCurrentWord : TestProgress -> Maybe Word
getCurrentWord testProgress =
    case testProgress.currentWordIndex of
        Nothing ->
            Nothing

        Just i ->
            getAt testProgress.words i


getCurrentWordAttempt : TestProgress -> Maybe Attempt
getCurrentWordAttempt testProgress =
    case getCurrentWord testProgress of
        Nothing ->
            Nothing

        Just word ->
            getWordAttempt testProgress word


isFinishedStage : LearningStage -> Bool
isFinishedStage stage =
    case stage of
        TestStage tp ->
            case tp.currentWordIndex of
                Nothing ->
                    True

                Just _ ->
                    False

        _ ->
            False


isTestingStage : LearningStage -> Bool
isTestingStage stage =
    case stage of
        TestStage _ ->
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


getStages : LearningType -> VerseStatus -> ( LearningStage, List LearningStage )
getStages learningType verseStatus =
    case learningType of
        Learning ->
            ( Read
            , [ TestStage (initialTestProgress verseStatus)
              ]
            )

        Revision ->
            ( TestStage (initialTestProgress verseStatus)
            , []
            )

        Practice ->
            ( TestStage (initialTestProgress verseStatus)
            , []
            )


moveToNextStage : Model -> ( Model, Cmd msg )
moveToNextStage model =
    let
        newModel =
            updateCurrentVerse model
                (\currentVerse ->
                    let
                        remaining =
                            currentVerse.remainingStages
                    in
                        case remaining of
                            [] ->
                                currentVerse

                            stage :: stages ->
                                { currentVerse
                                    | seenStages = currentVerse.currentStage :: currentVerse.seenStages
                                    , currentStage = stage
                                    , remainingStages = stages
                                }
                )
    in
        ( newModel, updateTypingBoxCommand newModel )


moveToPreviousStage : Model -> ( Model, Cmd msg )
moveToPreviousStage model =
    let
        newModel =
            updateCurrentVerse model
                (\currentVerse ->
                    let
                        previous =
                            currentVerse.seenStages
                    in
                        case previous of
                            [] ->
                                currentVerse

                            stage :: stages ->
                                { currentVerse
                                    | seenStages = stages
                                    , currentStage = stage
                                    , remainingStages = currentVerse.currentStage :: currentVerse.remainingStages
                                }
                )
    in
        ( newModel, updateTypingBoxCommand newModel )


handleTypedInput : Model -> String -> ( Model, Cmd msg )
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


handleTypedEnter : Model -> ( Model, Cmd msg )
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
                    && (String.right 1 input
                            == " "
                            || String.right 1 input
                            == "\n"
                       )

            FirstLetter ->
                String.length trimmedText > 0

            OnScreen ->
                False


checkCurrentWordAndUpdate : Model -> String -> ( Model, Cmd msg )
checkCurrentWordAndUpdate model input =
    let
        testingMethod =
            getTestingMethod model

        newModel =
            updateCurrentVerse model
                (\currentVerse ->
                    case currentVerse.currentStage of
                        TestStage tp ->
                            case getCurrentWord tp of
                                Nothing ->
                                    currentVerse

                                Just currentWord ->
                                    let
                                        correct =
                                            checkWord currentWord input testingMethod
                                    in
                                        markWord correct currentWord tp currentVerse testingMethod

                        _ ->
                            currentVerse
                )
    in
        ( newModel
          -- The typing box might need moving, so do it in case:
        , updateTypingBoxCommand newModel
        )


checkWord : { a | text : String } -> String -> TestingMethod -> Bool
checkWord word input testingMethod =
    let
        wordN =
            normalizeWordForTest word.text

        inputN =
            normalizeWordForTest input
    in
        case testingMethod of
            FullWords ->
                if String.length wordN == 1 then
                    wordN == inputN
                else
                    ((String.left 1 wordN
                        == String.left 1 inputN
                     )
                        && (damerauLevenshteinDistance wordN inputN
                                < (ceiling ((toFloat <| String.length wordN) / 3.0))
                           )
                    )

            FirstLetter ->
                String.right 1 inputN == String.left 1 wordN

            OnScreen ->
                False


normalizeWordForTest : String -> String
normalizeWordForTest =
    String.trim >> stripPunctuation >> simplifyTurkish >> String.toLower


stripPunctuation : String -> String
stripPunctuation =
    R.replace R.All (R.regex "[\"'\\.,;!?:\\/#!$%\\^&\\*{}=\\-_`~()\\[\\]“”‘’—]") (\m -> "")


simplifyTurkish : String -> String
simplifyTurkish =
    translate "ÂâÇçĞğİıÖöŞşÜü" "AaCcGgIiOoSsUu"


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
                        \x -> x

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


initialAttempt : Attempt
initialAttempt =
    { finished = False
    , checkResults = []
    }


markWord : Bool -> Word -> TestProgress -> CurrentVerse -> TestingMethod -> CurrentVerse
markWord correct word testingProgress verse testingMethod =
    let
        attempt =
            case getWordAttempt testingProgress word of
                Nothing ->
                    initialAttempt

                Just a ->
                    a

        checkResults =
            (if correct then
                Success
             else
                Failure
            )
                :: attempt.checkResults

        shouldMoveOn =
            correct || List.length checkResults > allowedMistakesForTestingMethod testingMethod

        attempt2 =
            { attempt
                | checkResults = checkResults
                , finished = shouldMoveOn
            }

        newAttempts =
            updateWordAttempts testingProgress word attempt2

        nextWordIndex =
            if shouldMoveOn then
                case testingProgress.currentWordIndex of
                    Nothing ->
                        Nothing

                    Just i ->
                        let
                            nextI =
                                i + 1
                        in
                            case getAt testingProgress.words nextI of
                                Just nextWord ->
                                    if isReference nextWord.type_ && not (testReferenceForTestingMethod testingMethod) then
                                        Nothing
                                    else
                                        Just nextI

                                Nothing ->
                                    Nothing
            else
                testingProgress.currentWordIndex
    in
        { verse
            | currentStage =
                TestStage
                    { testingProgress
                        | attemptRecord = newAttempts
                        , currentWordIndex = nextWordIndex
                        , currentTypedText =
                            if shouldMoveOn then
                                ""
                            else
                                testingProgress.currentTypedText
                    }
        }


getWordAttempt : TestProgress -> Word -> Maybe Attempt
getWordAttempt testingProgress word =
    Dict.get ( toString word.type_, word.index ) testingProgress.attemptRecord


updateWordAttempts : TestProgress -> Word -> Attempt -> AttemptRecord
updateWordAttempts testingProgress word attempt =
    Dict.insert ( toString word.type_, word.index ) attempt testingProgress.attemptRecord


allowedMistakesForTestingMethod : TestingMethod -> number
allowedMistakesForTestingMethod testingMethod =
    case testingMethod of
        FullWords ->
            2

        FirstLetter ->
            1

        OnScreen ->
            0


testReferenceForTestingMethod : TestingMethod -> Bool
testReferenceForTestingMethod testingMethod =
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


updateTypingBoxCommand : Model -> Cmd msg
updateTypingBoxCommand model =
    case getCurrentTestProgress model of
        Just tp ->
            case getCurrentWord tp of
                Nothing ->
                    hideTypingBoxCommand

                Just w ->
                    LearnPorts.updateTypingBox
                        ( typingBoxId
                        , idForButton w
                        , classForTypingBox <| typingBoxInUse tp (getTestingMethod model)
                        )

        Nothing ->
            hideTypingBoxCommand


hideTypingBoxCommand : Cmd msg
hideTypingBoxCommand =
    LearnPorts.updateTypingBox ( typingBoxId, "", classForTypingBox False )



{- API calls -}


versesToLearnUrl : String
versesToLearnUrl =
    "/api/learnscripture/v1/versestolearn2/"


loadVerses : Cmd Msg
loadVerses =
    Http.send VersesToLearn (Http.get versesToLearnUrl verseBatchRawDecoder)



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



{- General utils -}


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
