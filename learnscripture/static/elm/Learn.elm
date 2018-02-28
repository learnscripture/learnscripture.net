port module Learn exposing (..)

import Dict
import Dom
import Erl
import Html as H
import Html.Attributes as A
import Html.Events as E
import Html.Keyed
import Http
import ISO8601
import Json.Decode as JD
import Json.Decode.Pipeline as JDP
import Json.Encode as JE
import Maybe
import MemoryModel
import Native.Confirm
import Native.StringUtils
import Navigation
import Process
import Random
import Random.List
import Regex as R
import Set
import String
import StringInterpolate.Interpolate exposing (interpolate)
import Task
import Time
import Window
import Pivot


{- Main -}


main : Program Flags Model Msg
main =
    H.programWithFlags
        { init = init
        , view = view
        , update = update
        , subscriptions = subscriptions
        }



{- Ports -}


port updateTypingBox : UpdateTypingBoxData -> Cmd msg


port receivePreferences : (JD.Value -> msg) -> Sub msg


port vibrateDevice : Int -> Cmd msg


port beep : ( Float, Float ) -> Cmd msg


port helpTourHighlightElement : String -> Cmd msg



{- Constants -}


{-| Strength == 0.6 corresponds to about 10 days learning.
-}
hardModeStrengthThreshold : Float
hardModeStrengthThreshold =
    0.6



{- Flags and external inputs -}


type alias Flags =
    { preferences : JD.Value
    , autoSavedPreferences : JD.Value
    , account : Maybe AccountData
    , isTouchDevice : Bool
    , csrfMiddlewareToken : String
    , windowSize :
        { width : Int
        , height : Int
        }
    }


decodePreferences : JD.Value -> Preferences
decodePreferences prefsValue =
    case JD.decodeValue preferencesDecoder prefsValue of
        Ok prefs ->
            prefs

        Err err ->
            Debug.crash err


decodeAutoSavedPreferences : JD.Value -> AutoSavedPreferences
decodeAutoSavedPreferences prefsValue =
    case JD.decodeValue autoSavedPreferencesDecoder prefsValue of
        Ok prefs ->
            prefs

        Err err ->
            Debug.crash err


init : Flags -> ( Model, Cmd Msg )
init flags =
    let
        preferences =
            decodePreferences flags.preferences

        autoSavedPreferences =
            decodeAutoSavedPreferences flags.autoSavedPreferences

        windowSize =
            flags.windowSize
    in
        ( { preferences = preferences
          , autoSavedPreferences = autoSavedPreferences
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
          , previousVerseVisible = False
          , currentHttpCalls = Dict.empty
          , permanentFailHttpCalls = []
          , openDropdown = Nothing
          , pinnedMenus = setPinnedMenus autoSavedPreferences windowSize
          , sessionStats = Nothing
          , attemptingReturn = False
          , currentTime =
                ISO8601.fromTime 0
                -- Hard coding this to prefer reading, instead of storing in preferences
                -- etc., is a deliberate design decision to reduce the number of tests. If
                -- people want to prefer testing to reading, they have to select it in
                -- each passage testing session.
          , testOrReadPreference = PreferReading
          , windowSize = windowSize
          , helpTour = Nothing
          }
        , loadVerses True
        )


setPinnedMenus : AutoSavedPreferences -> { height : Int, width : Int } -> Set.Set String
setPinnedMenus prefs windowSize =
    [ if
        ((prefs.pinActionLogMenuLargeScreen
            && isScreenLargeEnoughForSidePanels windowSize
         )
            || (prefs.pinActionLogMenuSmallScreen
                    && (not <| isScreenLargeEnoughForSidePanels windowSize)
               )
        )
      then
        Just ActionLogsInfo
      else
        Nothing
    , if
        (prefs.pinVerseOptionsMenuLargeScreen
            && isScreenLargeEnoughForSidePanels windowSize
        )
      then
        Just VerseOptionsMenu
      else
        Nothing
    ]
        |> List.filterMap identity
        |> List.map toString
        |> Set.fromList



{- Model -}


type alias Model =
    { preferences : Preferences
    , autoSavedPreferences : AutoSavedPreferences
    , user : User
    , learningSession : LearningSession
    , isTouchDevice : Bool
    , httpConfig : HttpConfig
    , helpVisible : Bool
    , previousVerseVisible : Bool
    , currentHttpCalls :
        Dict.Dict CallId QueuedCall
    , permanentFailHttpCalls : List ( CallId, TrackedHttpCall )
    , openDropdown : Maybe Dropdown
    , pinnedMenus : Set.Set String
    , sessionStats : Maybe SessionStats
    , attemptingReturn : Bool
    , currentTime : ISO8601.Time
    , testOrReadPreference : TestOrReadPreference
    , windowSize :
        { height : Int
        , width : Int
        }
    , helpTour : Maybe HelpTour
    }


type alias Preferences =
    { preferencesSetup : Bool
    , enableAnimations : Bool
    , enableSounds : Bool
    , enableVibration : Bool
    , desktopTestingMethod : TestingMethod
    , touchscreenTestingMethod : TestingMethod
    }


type alias AutoSavedPreferences =
    { pinActionLogMenuLargeScreen : Bool
    , pinActionLogMenuSmallScreen : Bool
    , pinVerseOptionsMenuLargeScreen : Bool
    , seenHelpTour : Bool
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
    , actionLogStore : ActionLogStore
    }


type alias CurrentVerse =
    { verseStatus : VerseStatus
    , sessionLearningType : LearningType
    , currentStage : LearningStage
    , remainingStageTypes : List LearningStageType
    , seenStageTypes : List LearningStageType
    , recordedTestScore :
        Maybe
            { accuracy : Float
            , timestamp : ISO8601.Time
            }
    }


type alias ActionLogStore =
    { processed : Dict.Dict Int ActionLog
    , beingProcessed : Maybe ActionLog
    , toProcess : Dict.Dict Int ActionLog
    }


type alias LearnOrder =
    Int


type alias UvsId =
    Int


type alias Url =
    String


type TestOrReadPreference
    = PreferReading
    | PreferTests


type alias VerseStore =
    { verseStatuses : List VerseStatus
    , learningType : LearningType
    , returnTo : Url
    , maxOrderVal : LearnOrder
    , untestedOrderVals : List LearnOrder
    }


type alias VerseBatchBase a =
    { a
        | learningTypeRaw : Maybe LearningType
        , returnTo : Url
        , maxOrderValRaw : Maybe LearnOrder
        , untestedOrderVals : List LearnOrder
    }


type alias VerseBatchRaw =
    VerseBatchBase
        { verseStatusesRaw : List VerseStatusRaw
        , versions : List Version
        , verseSets : List VerseSet
        , sessionStats : Maybe SessionStats
        , actionLogs : Maybe (List ActionLog)
        }



-- VerseBatchRaw constructor does not get created for us so we make one here for
-- consistency


verseBatchRawCtr :
    Maybe LearningType
    -> String
    -> Maybe LearnOrder
    -> List LearnOrder
    -> List VerseStatusRaw
    -> List Version
    -> List VerseSet
    -> Maybe SessionStats
    -> Maybe (List ActionLog)
    -> VerseBatchRaw
verseBatchRawCtr l r m u v1 v2 v3 s a =
    { learningTypeRaw = l
    , returnTo = r
    , maxOrderValRaw = m
    , untestedOrderVals = u
    , verseStatusesRaw = v1
    , versions = v2
    , verseSets = v3
    , sessionStats = s
    , actionLogs = a
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
        , lastTested : Maybe ISO8601.Time
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
    -> Maybe ISO8601.Time
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
verseStatusRawCtr i s lt lr n t s2 s3 t2 l2 v v2 =
    { id = i
    , strength = s
    , lastTested = lt
    , localizedReference = lr
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
    , smartName : String
    , url : String
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


type alias ActionLog =
    { id : Int
    , points : Int
    , reason :
        ScoreReason
        -- created is technically a date, but in ISO format it is fine.
        -- we only use it for sorting and ISO dates sort chronologically.
    , created : String
    }


type ScoreReason
    = VerseTested
    | VerseReviewed
    | RevisionCompleted
    | PerfectTestBonus
    | VerseLearnt
    | EarnedAward


type alias SessionStats =
    { totalVersesTested : Int
    , newVersesStarted : Int
    }


currentSetType : CurrentVerse -> Maybe VerseSetType
currentSetType currentVerse =
    case currentVerse.verseStatus.verseSet of
        Nothing ->
            Nothing

        Just verseSet ->
            Just verseSet.setType


isPassageSet : CurrentVerse -> Bool
isPassageSet currentVerse =
    case currentSetType currentVerse of
        Nothing ->
            False

        Just Selection ->
            False

        Just Passage ->
            True



{- View -}


type alias IconName =
    String


type LinkIconAlign
    = AlignLeft
    | AlignRight


type Dropdown
    = AjaxInfo
    | ActionLogsInfo
    | VerseOptionsMenu


dashboardUrl : String
dashboardUrl =
    "/dashboard/"


view : Model -> H.Html Msg
view model =
    H.div (pinnedAttributes model)
        [ viewTopNav model
        , case model.learningSession of
            Loading ->
                loadingDiv

            VersesError err ->
                errorMessage ("The items to learn could not be loaded (error message: " ++ toString err ++ ".) Please check your internet connection!")

            Session sessionData ->
                viewCurrentVerse sessionData model
        , case model.helpTour of
            Nothing ->
                emptyNode

            Just helpTour ->
                viewHelpTour helpTour
        ]


viewTopNav : Model -> H.Html Msg
viewTopNav model =
    H.nav [ A.class "topbar-new" ]
        [ H.div [ A.class "nav-item return-link" ]
            [ navLink
                [ A.href "#"
                , onClickSimply (AttemptReturn { immediate = True, queued = False })
                ]
                (getReturnUrl model |> getReturnCaption)
                "icon-return"
                AlignLeft
            ]
        , sessionProgress model
        , viewActionLogs model
        , ajaxInfo model
        , viewSessionStats model
        , H.div [ A.class "nav-item preferences-link" ]
            [ navLink [ A.href "#" ] (userDisplayName model.user) "icon-preferences" AlignRight ]
        ]


pinnedAttributes : Model -> List (H.Attribute msg)
pinnedAttributes model =
    List.filterMap identity
        [ if menuIsPinned model ActionLogsInfo then
            Just (A.attribute "data-actionlogsinfo-pinned" "true")
          else
            Nothing
        , if menuIsPinned model VerseOptionsMenu then
            Just (A.attribute "data-verseoptionsmenu-pinned" "true")
          else
            Nothing
        ]


getReturnCaption : Url -> String
getReturnCaption url =
    if url == dashboardUrl then
        "Dashboard"
    else
        "Return"


sessionProgress : Model -> H.Html Msg
sessionProgress model =
    let
        render fraction caption numberCaption =
            H.div [ A.class "nav-item spacer session-progress" ]
                [ H.div [ A.class "progress-bar" ]
                    [ H.div
                        [ A.class "filled-bar"
                        , A.style [ ( "width", toString (fraction * 100) ++ "%" ) ]
                        ]
                        []
                    , H.div
                        [ A.class "progress-caption" ]
                        [ H.span [ A.class "nav-caption" ]
                            [ H.text caption ]
                        , H.text numberCaption
                        ]
                    ]
                ]
    in
        case getSessionProgressData model of
            NoProgress ->
                H.div [ A.class "nav-item spacer" ]
                    []

            VerseProgress fraction ->
                render fraction "" ""

            SessionProgress fraction total current ->
                render fraction
                    "Review: "
                    (interpolate "{0} / {1}"
                        [ current |> toString
                        , total |> toString
                        ]
                    )


ajaxInfo : Model -> H.Html Msg
ajaxInfo model =
    let
        currentHttpCalls =
            Dict.values model.currentHttpCalls

        httpCallsInProgress =
            currentHttpCalls |> List.filter (\{ attempts } -> attempts > 0) |> List.isEmpty |> not

        retryingAttempts =
            currentHttpCalls |> List.map .attempts |> List.any (\a -> a > 1)

        failedHttpCalls =
            model.permanentFailHttpCalls

        retriesClass =
            if retryingAttempts then
                Just "ajax-retries"
            else
                Nothing

        failuresClass =
            if not <| List.isEmpty failedHttpCalls then
                Just "ajax-failures"
            else
                Nothing

        itemsToView =
            not <| List.isEmpty currentHttpCalls && List.isEmpty failedHttpCalls

        hideStatus =
            not itemsToView

        hiddenClass =
            if hideStatus then
                Just "hidden"
            else
                Nothing

        topClasses =
            [ retriesClass
            , failuresClass
            , hiddenClass
            , Just "nav-item"
            ]
                |> List.filterMap identity

        spinClass =
            if hideStatus then
                ""
            else if httpCallsInProgress then
                "icon-spin"
            else
                ""

        dropdownOpen =
            dropdownIsOpen model AjaxInfo

        openClass =
            if dropdownOpen && itemsToView then
                "menu-open"
            else
                ""
    in
        H.div [ A.class ("ajax-info nav-dropdown " ++ openClass) ]
            [ H.div
                (dropdownHeadingAttributes AjaxInfo itemsToView topClasses)
                [ H.span [ A.class "nav-caption" ]
                    [ H.text "Working..." ]
                , makeIcon ("icon-ajax-in-progress " ++ spinClass) "Data transfer in progress"
                ]
            , if not itemsToView then
                emptyNode
              else
                H.ul
                    [ A.class ("nav-dropdown-menu " ++ openClass) ]
                    ((if not <| List.isEmpty failedHttpCalls then
                        [ H.li [ A.class "button-item" ]
                            [ H.button
                                [ A.class "btn"
                                , onClickSimply RetryFailedCalls
                                ]
                                [ H.text "Try to load/save data again" ]
                            ]
                        ]
                      else
                        []
                     )
                        ++ (failedHttpCalls
                                |> List.map
                                    (\( callId, call ) ->
                                        H.li [ A.class "ajax-failed" ]
                                            [ H.text <|
                                                interpolate "Failed - {0}"
                                                    [ trackedHttpCallCaption call ]
                                            ]
                                    )
                           )
                        ++ (currentHttpCalls
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
                                                if attempts == 0 then
                                                    interpolate "In queue - {0}"
                                                        [ trackedHttpCallCaption call ]
                                                else
                                                    interpolate "Attempt {0} of {1} - {2}"
                                                        [ toString attempts
                                                        , toString maxHttpRetries
                                                        , trackedHttpCallCaption call
                                                        ]
                                            ]
                                    )
                           )
                    )
            ]


viewSessionStats : Model -> H.Html Msg
viewSessionStats model =
    case model.sessionStats of
        Nothing ->
            emptyNode

        Just stats ->
            H.div
                [ A.class "nav-item session-stats"
                , A.title "Todays stats - new items / items tested"
                ]
                [ H.span [ A.class "nav-caption" ]
                    [ H.text "Today: " ]
                , H.span
                    [ A.id "id-new-verses-started-count"
                    , A.title "Items started today"
                    ]
                    [ H.text <| interpolate " + {0} " [ toString stats.newVersesStarted ] ]
                , H.span
                    [ A.id "id-total-verses-tested-count"
                    , A.title "Total items tested today"
                    ]
                    [ H.text <| interpolate " ⟳ {0} " [ toString stats.totalVersesTested ] ]
                , makeIcon "icon-today-stats" "Stats for today"
                ]


viewActionLogs : Model -> H.Html Msg
viewActionLogs model =
    let
        ( totalPoints, latestLog, processedLogs ) =
            withSessionData model
                ( 0, Nothing, [] )
                (\sessionData ->
                    let
                        totalPoints =
                            sessionData.actionLogStore.processed
                                |> (\p ->
                                        -- We exclude 'beingProcessed' so that the total is
                                        -- updated after the animation.
                                        case sessionData.actionLogStore.beingProcessed of
                                            Just log ->
                                                Dict.remove log.id p

                                            Nothing ->
                                                p
                                   )
                                |> Dict.values
                                |> List.map .points
                                |> List.sum
                    in
                        ( totalPoints
                        , sessionData.actionLogStore.beingProcessed
                        , sessionData.actionLogStore.processed
                            |> Dict.values
                            |> List.sortBy .created
                            |> List.reverse
                        )
                )

        dropdownOpen =
            dropdownIsOpen model ActionLogsInfo

        menuPinned =
            menuIsPinned model ActionLogsInfo

        itemsToView =
            List.length processedLogs > 0

        openClass =
            if not menuPinned && (dropdownOpen && itemsToView) then
                "menu-open"
            else
                ""

        pinnedClass =
            if menuPinned then
                "menu-pinned"
            else
                ""

        openable =
            itemsToView && not menuPinned
    in
        H.div [ A.class ("action-logs nav-dropdown " ++ openClass ++ " " ++ pinnedClass) ]
            [ H.div
                (dropdownHeadingAttributes ActionLogsInfo openable [ "nav-item" ])
                [ H.span [ A.class "nav-caption" ]
                    [ H.text "Session points: " ]
                , H.span [ A.class "total-points" ]
                    [ H.text (toString totalPoints)
                    , case latestLog of
                        Nothing ->
                            emptyNode

                        Just log ->
                            H.span
                                [ A.class "latest-points flash-action-log"
                                , A.attribute "data-reason" (toString log.reason)
                                , A.id (idForLatestActionLogSpan log)
                                ]
                                [ H.text (signedNumberToString log.points) ]
                    ]
                , makeIcon "icon-points" "Points gained this session"
                ]
            , Html.Keyed.ul
                [ A.class ("nav-dropdown-menu menu-pinnable " ++ openClass ++ " " ++ pinnedClass) ]
                ([ ( "pin-button"
                   , pinButton ActionLogsInfo
                   )
                 ]
                    ++ (processedLogs
                            |> List.map
                                (\log ->
                                    ( toString log.id
                                    , H.li
                                        [ A.class "action-log-item"
                                        , A.attribute "data-reason" (toString log.reason)
                                        ]
                                        [ H.text <|
                                            interpolate "{0} - {1}"
                                                [ toString log.points
                                                , prettyReason log.reason
                                                ]
                                        ]
                                    )
                                )
                       )
                )
            ]


pinButton : Dropdown -> H.Html Msg
pinButton dropdown =
    H.button
        [ A.class "menu-pin"
        , A.title "Pin/unpin menu"
        , onClickSimply (TogglePinnableMenu dropdown)
        , A.tabindex -1
        ]
        [ makeIcon "icon-pin-menu" "Pin menu" ]


dropdownHeadingAttributes : Dropdown -> Bool -> List String -> List (H.Attribute Msg)
dropdownHeadingAttributes dropdown openable extraClasses =
    [ A.class <| "dropdown-heading " ++ String.join " " extraClasses ]
        ++ if openable then
            [ onClickSimply (ToggleDropdown dropdown)
            , onEnter (ToggleDropdown dropdown)
            , A.tabindex 0
            ]
           else
            [ A.tabindex -1 ]


prettyReason : ScoreReason -> String
prettyReason reason =
    case reason of
        VerseTested ->
            "initial test"

        VerseReviewed ->
            "review test"

        RevisionCompleted ->
            "revision completed"

        PerfectTestBonus ->
            "perfect score BONUS!"

        VerseLearnt ->
            "verse fully learnt BONUS!"

        EarnedAward ->
            "award bonus"


idForLatestActionLogSpan : { b | id : a } -> String
idForLatestActionLogSpan log =
    "id-latest-action-log-" ++ toString log.id


signedNumberToString : Int -> String
signedNumberToString number =
    if number > 0 then
        "+" ++ (toString number)
    else
        toString number


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

        verseScaledStrength =
            scaledStrength (currentVerseStrength currentVerse)

        verseStrengthPercent =
            floor (verseScaledStrength * 100)

        -- Clip width for the overlayed 'star' icon, rescaled to make it look as
        -- expected (trial and error)
        progressStarWidth =
            floor (verseScaledStrength * 65 + 15)

        verseOptionsMenuOpen =
            dropdownIsOpen model VerseOptionsMenu

        verseOptionsMenuPinned =
            menuIsPinned model VerseOptionsMenu

        verseOptionsMenuVisible =
            verseOptionsMenuOpen || verseOptionsMenuPinned
    in
        H.div [ A.id "id-content-wrapper" ]
            ([ H.div [ A.id "id-verse-header" ]
                [ H.h2 titleTextAttrs
                    [ H.text currentVerse.verseStatus.titleText ]
                , H.div [ A.class "spacer" ]
                    []
                , H.div [ A.id "id-verse-strength-icon" ]
                    -- Two stars, a full one on top of an outline, the full one clipped.
                    [ H.i [ A.class "icon-fw icon-star-o" ] []
                    , H.i
                        [ A.class "icon-fw icon-star"
                        , A.style
                            [ ( "clip-path"
                              , interpolate
                                    "inset(0px {0}% 0px 0px)"
                                    [ toString (100 - progressStarWidth) ]
                              )
                            ]
                        ]
                        []
                    ]
                , H.div
                    [ A.id "id-verse-strength-value"
                    , A.title "Memory strength for this verse"
                    ]
                    [ H.text (toString verseStrengthPercent ++ "%") ]
                , viewVerseOptionsMenuButton verseOptionsMenuOpen verseOptionsMenuPinned
                ]
             , if verseOptionsMenuVisible then
                viewVerseOptionsMenu model currentVerse
               else
                emptyNode
             , H.div [ A.id "id-verse-wrapper" ]
                [ case previousVerse of
                    Nothing ->
                        emptyNode

                    Just verse ->
                        H.div
                            [ A.class
                                ("previous-verse-wrapper"
                                    ++ (if not model.previousVerseVisible then
                                            " previous-verse-partial"
                                        else
                                            ""
                                       )
                                )
                            ]
                            [ H.div [ A.class "previous-verse" ]
                                (versePartsToHtml ReadForContext
                                    (partsForVerse verse ReadForContextStage testingMethod)
                                    verse.id
                                )
                            , H.a
                                [ A.href "#"
                                , onClickSimply TogglePreviousVerseVisible
                                , A.tabindex -1
                                ]
                                [ H.span [ A.id "id-toggle-show-previous-verse" ]
                                    [ makeIcon
                                        ("icon-show-previous-verse"
                                            ++ (if model.previousVerseVisible then
                                                    " expanded"
                                                else
                                                    ""
                                               )
                                        )
                                        "Toggle show all of previous verse"
                                    ]
                                ]
                            ]
                , H.div [ A.id typingBoxContainerId ]
                    -- We make typing box a permanent fixture to avoid issues
                    -- with losing focus and screen keyboards then disappearing.
                    -- It comes close to the verse itself to fix tab order
                    -- without needing tabindex.
                    [ typingBox currentVerse.currentStage testingMethod
                    , H.div [ A.class verseClasses ]
                        (versePartsToHtml currentVerse.currentStage
                            (partsForVerse currentVerse.verseStatus (learningStageTypeForStage currentVerse.currentStage) testingMethod)
                            currentVerse.verseStatus.id
                        )
                    ]
                , copyrightNotice currentVerse.verseStatus.version
                , verseSetLink currentVerse.verseStatus.verseSet
                , H.div [ A.style [ ( "clear", "both" ) ] ]
                    []
                ]
             , actionButtons model currentVerse session.verses model.preferences
             , hintButton model currentVerse testingMethod
             , onScreenTestingButtons currentVerse testingMethod
             ]
                ++ (instructions currentVerse testingMethod model.helpVisible)
            )


{-| see bibleverses/models.py scaled_strength
-}
scaledStrength : Float -> Float
scaledStrength rawStrength =
    min (rawStrength / MemoryModel.learnt) 1.0


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


viewVerseOptionsMenuButton : Bool -> Bool -> H.Html Msg
viewVerseOptionsMenuButton menuOpen menuPinned =
    H.div
        ((dropdownHeadingAttributes VerseOptionsMenu
            True
            (if menuOpen then
                [ "menu-open" ]
             else if menuPinned then
                [ "menu-pinned" ]
             else
                [ "menu-closed" ]
            )
         )
            ++ [ A.id "id-verse-options-menu-btn" ]
        )
        [ H.span []
            [ makeIcon "icon-verse-options-menu-btn" "verse options" ]
        ]


viewVerseOptionsMenu : Model -> CurrentVerse -> H.Html Msg
viewVerseOptionsMenu model currentVerse =
    let
        skipButton =
            { enabled = Enabled
            , default = NonDefault
            , msg = SkipVerse currentVerse.verseStatus
            , caption =
                case currentVerse.verseStatus.version.textType of
                    Bible ->
                        "Skip this verse for now"

                    Catechism ->
                        "Skip this question for now"
            , id = "id-skip-verse-btn"
            , refocusTypingBox = True
            }

        cancelLearningButton =
            { enabled = Enabled
            , default = NonDefault
            , msg = CancelLearning currentVerse.verseStatus
            , caption =
                case currentVerse.verseStatus.version.textType of
                    Bible ->
                        "Stop learning this verse"

                    Catechism ->
                        "Stop learning this question"
            , id = "id-cancel-learning-btn"
            , refocusTypingBox = True
            }

        resetProgressButton =
            { enabled = Enabled
            , default = NonDefault
            , msg = ResetProgress currentVerse.verseStatus False
            , caption = "Reset progress"
            , id = "id-reset-progress-btn"
            , refocusTypingBox = False
            }

        buttons =
            List.filterMap identity <|
                [ Just skipButton
                , if isPassageSet currentVerse then
                    Nothing
                  else
                    Just cancelLearningButton
                , Just resetProgressButton
                ]

        menuPinned =
            menuIsPinned model VerseOptionsMenu

        pinnedClass =
            if menuPinned then
                "menu-pinned"
            else
                ""
    in
        H.div [ A.id "id-verse-options-menu" ]
            [ H.ul [ A.class pinnedClass ]
                ([ pinButton VerseOptionsMenu
                 ]
                    ++ (if allowTestInsteadOfRead model then
                            [ H.li []
                                [ H.label []
                                    [ H.input
                                        ([ A.type_ "checkbox"
                                         , A.checked
                                            (case model.testOrReadPreference of
                                                PreferReading ->
                                                    False

                                                PreferTests ->
                                                    True
                                            )
                                         , onClickSimply TogglePreferTestsToReading
                                         ]
                                            ++ (getTypingBoxFocusDataForMsg model TogglePreferTestsToReading True
                                                    |> getFocusAttributes
                                               )
                                        )
                                        []
                                    , H.span []
                                        [ H.text "Test instead of read" ]
                                    ]
                                ]
                            ]
                        else
                            []
                       )
                    ++ (List.map
                            (\button ->
                                H.li []
                                    [ viewButton model button ]
                            )
                            buttons
                       )
                )
            ]


allowTestInsteadOfRead : Model -> Bool
allowTestInsteadOfRead model =
    withCurrentVerse model
        False
        (\currentVerse ->
            (isPassageSet currentVerse)
                && (not <| currentVerse.sessionLearningType == Practice)
                && (case model.learningSession of
                        Session sessionData ->
                            List.any (\vs -> not vs.needsTesting) sessionData.verses.verseStatuses

                        _ ->
                            False
                   )
        )


dropdownIsOpen : Model -> Dropdown -> Bool
dropdownIsOpen model dropdown =
    case model.openDropdown of
        Just d ->
            d == dropdown

        Nothing ->
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
        |> dropEndWhile (\p -> p == Linebreak)
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

        initialPunctOrSpace =
            R.regex "^[\\s:\\-]"

        parts =
            reference
                |> R.split R.All splitter
                -- Split the initial punct/space we found into separate bits:
                |>
                    List.map
                        (\w ->
                            if R.contains initialPunctOrSpace w then
                                [ String.left 1 w, String.dropLeft 1 w ]
                            else
                                [ w ]
                        )
                |> List.concat
    in
        List.map2
            (\idx w ->
                if String.trim w == "" then
                    Space
                else if R.contains initialPunctOrSpace w then
                    ReferencePunct w
                else
                    WordPart
                        { type_ = ReferenceWord
                        , index = idx
                        , text = w
                        }
            )
            (List.range 0 (List.length parts))
            parts


versePartsToHtml : LearningStage -> List Part -> UvsId -> List (H.Html Msg)
versePartsToHtml stage parts uvsId =
    List.map
        (\p ->
            case p of
                WordPart word ->
                    wordButton word stage uvsId

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


idForButton : Word -> UvsId -> String
idForButton wd uvsId =
    idPrefixForButton wd.type_ ++ toString uvsId ++ "-" ++ toString wd.index


wordButton : Word -> LearningStage -> UvsId -> H.Html Msg
wordButton word stage uvsId =
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
                    idForButton word uvsId
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


verseSetLink : Maybe VerseSet -> H.Html msg
verseSetLink verseSet =
    case verseSet of
        Nothing ->
            emptyNode

        Just vs ->
            H.div
                [ A.id "id-verse-set-link"
                ]
                [ H.a
                    [ A.href vs.url
                    , A.tabindex -1
                    , A.target "_blank"
                    ]
                    [ H.text vs.smartName ]
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
    "id-current-verse-wrapper"


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
               -- We experimented with making the type switch to "number" for
               -- verse reference chapter/verse, in order to activate a numeric on
               -- screen keyboard - see changeset e9b3664ccf48 and f3d144d3283d
               --
               -- However, this worked badly:
               -- * On Chrome for Android sometimes the onscreen keyboard disappears
               --   when we change the input type, don't know why.
               -- * It makes the keyboard a moving target when it switches from
               --   normal to numeric. This slows you down and causes
               --   mistakes, which is more annoying than the alternative.
               --
               -- So we stick with just "text"
             , A.type_ "text"
             , A.value value
             , A.autocomplete False
             , A.attribute "autocorrect" "off"
             , A.attribute "autocapitalize" "off"
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
                        ++ (buttons
                                |> List.map
                                    (\b ->
                                        H.span []
                                            [ viewButton model b
                                            , if b.subCaption == "" then
                                                emptyNode
                                              else
                                                H.span [ A.class "btn-sub-caption" ]
                                                    [ H.text b.subCaption ]
                                            ]
                                    )
                           )
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


type alias ButtonBase a =
    { a
        | enabled : ButtonEnabled
        , default : ButtonDefault
        , msg : Msg
        , caption : String
        , id : String
        , refocusTypingBox : Bool
    }


type alias Button =
    ButtonBase {}


type alias StageButton =
    ButtonBase
        { subCaption : String
        }


type ButtonEnabled
    = Enabled
    | Disabled


type ButtonDefault
    = Default
    | NonDefault


buttonsForStage : Model -> CurrentVerse -> VerseStore -> Preferences -> List StageButton
buttonsForStage model verse verseStore preferences =
    let
        multipleStages =
            (List.length verse.remainingStageTypes + List.length verse.seenStageTypes) > 0

        nextVerseButtonCaption =
            "OK"

        practiceButtonCaption =
            if verse.sessionLearningType == Practice then
                -- Clearer, and we will only have two buttons so will have more
                -- room for a longer caption.
                "Practice again"
            else
                "Practice"

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

        nextTestDue =
            calculateNextTestDue verse

        nextVerseSubCaption =
            case nextTestDue of
                Nothing ->
                    ""

                Just t ->
                    friendlyTimeUntil t

        -- To keep things aligned, we only put subCaption on
        -- MorePractice button if there is also one on NextVerse button
        morePracticeSubCaption =
            if nextVerseSubCaption == "" then
                ""
            else
                "Now"

        reviewSoonerButton =
            case nextTestDue of
                Nothing ->
                    Nothing

                Just testDueAfter ->
                    let
                        reviewAfter =
                            case testDueAfter of
                                NeverDue ->
                                    oneYear

                                DueAfter t ->
                                    t / 2
                    in
                        Just
                            { caption = "See sooner"
                            , subCaption = friendlyTimeUntil (DueAfter reviewAfter)
                            , msg = ReviewSooner verse.verseStatus reviewAfter
                            , enabled = Enabled
                            , default = NonDefault
                            , id = "id-review-sooner"
                            , refocusTypingBox = True
                            }

        testStageButtons tp =
            case tp.currentWord of
                TestFinished { accuracy } ->
                    let
                        defaultMorePractice =
                            accuracy < 0.8
                    in
                        [ Just
                            { caption = practiceButtonCaption
                            , subCaption = morePracticeSubCaption
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
                        , reviewSoonerButton
                        , Just
                            { caption = nextVerseButtonCaption
                            , subCaption = nextVerseSubCaption
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
                            |> List.filterMap identity

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
                          , subCaption = ""
                          , msg = PreviousStage
                          , enabled = previousEnabled
                          , default = NonDefault
                          , id = "id-previous-btn"
                          , refocusTypingBox = False
                          }
                        , { caption = "Next"
                          , subCaption = ""
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
                      , subCaption = ""
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


{-| renders button, complete with attributes for refocusing text box if necessary
-}
viewButton : Model -> ButtonBase a -> H.Html Msg
viewButton model button =
    let
        -- see learn_setup.js
        focusAttributes =
            case button.enabled of
                Enabled ->
                    if button.refocusTypingBox then
                        getTypingBoxFocusDataForMsg model button.msg True |> getFocusAttributes
                    else
                        []

                Disabled ->
                    []
    in
        viewButton_ button focusAttributes


{-| renders button, for case when we don't need to do any refocussing stuff
-}
viewButtonSimple : ButtonBase a -> H.Html Msg
viewButtonSimple button =
    viewButton_ button []


viewButton_ : ButtonBase a -> List (H.Attribute Msg) -> H.Html Msg
viewButton_ button extraAttributes =
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
    in
        H.button (attributes ++ eventAttributes ++ extraAttributes)
            [ H.text button.caption ]


getFocusAttributes : Maybe UpdateTypingBoxData -> List (H.Attribute Msg)
getFocusAttributes focusData =
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
            [ [ H.a
                    [ A.href "#"
                    , onClickSimply StartHelpTour
                    ]
                    [ H.text "Take the help tour." ]
              ]
            , [ H.text "You can finish your review or learning session at any time using the return button in the top left corner."
              ]
            , [ H.text "Keyboard navigation (for physical keyboards, not touchscreens): use Tab and Shift-Tab to move focus between controls, and Enter to 'press' one. Focus is shown with a blue border."
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

                Test testType tp ->
                    let
                        practiseNote =
                            if isPracticeTest verse testType then
                                [ H.br [] []
                                , H.b [] [ H.text "PRACTICE" ]
                                , H.text " test, scores are not counted."
                                ]
                            else
                                [ emptyNode ]
                    in
                        case tp.currentWord of
                            CurrentWord _ ->
                                case testingMethod of
                                    FullWords ->
                                        ( [ bold "TEST: "
                                          , H.text "Testing time! Type the text, pressing space after each word."
                                          ]
                                            ++ practiseNote
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
                                            ++ practiseNote
                                        , commonHelp ++ testingCommonHelp
                                        )

                                    OnScreen ->
                                        ( [ bold "TEST: "
                                          , H.text "Testing time! For each word choose from the options shown."
                                          ]
                                            ++ practiseNote
                                        , commonHelp ++ testingCommonHelp
                                        )

                            TestFinished { accuracy } ->
                                ( [ bold "RESULTS: "
                                  , H.text "You scored: "
                                  , bold (toString (floor (accuracy * 100)) ++ "%")
                                  , H.text (" - " ++ resultComment accuracy)
                                  ]
                                , commonHelp
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
                        , H.a
                            [ A.href "#"
                            , onClickSimply ToggleHelp
                            ]
                            [ makeIcon
                                ("icon-help-toggle"
                                    ++ (if helpVisible then
                                            " expanded"
                                        else
                                            ""
                                       )
                                )
                                "toggle help"
                            ]
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



{- View - help tour -}


viewHelpTour : HelpTour -> H.Html Msg
viewHelpTour (HelpTour helpTour) =
    let
        buttons =
            helpTourButtons helpTour
    in
        H.div
            [ A.id "id-help-tour-wrapper"
            , A.class (Pivot.getC helpTour.steps).class
            ]
            [ H.div [ A.id "id-help-tour-content" ]
                [ H.div [ A.id "id-help-tour-message" ]
                    (Pivot.getC helpTour.steps).html
                , H.div [ A.id "id-help-tour-controls" ]
                    (buttons
                        |> List.map
                            (\b ->
                                H.span []
                                    [ viewButtonSimple b ]
                            )
                    )
                ]
            ]


helpTourButtons : HelpTourData -> List Button
helpTourButtons helpTour =
    [ { caption = "Exit tour"
      , msg = FinishHelpTour
      , id = "id-help-tour-finish-btn"
      , enabled = Enabled
      , default = NonDefault
      , refocusTypingBox = False
      }
    , { caption = "Previous"
      , msg = PreviousHelpTourStep
      , id = "id-help-tour-previous-step-btn"
      , enabled =
            if Pivot.hasL helpTour.steps then
                Enabled
            else
                Disabled
      , default = NonDefault
      , refocusTypingBox = False
      }
    , { caption =
            if Pivot.hasR helpTour.steps then
                "Next"
            else
                "Finish"
      , msg = NextHelpTourStep
      , id = "id-help-tour-next-step-btn"
      , enabled = Enabled
      , default = Default
      , refocusTypingBox = False
      }
    ]



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


makeIcon : String -> String -> H.Html msg
makeIcon iconClass titleText =
    H.i
        [ A.class ("icon-fw " ++ iconClass)
        , A.title titleText
        ]
        []


navLink : List (H.Attribute Msg) -> String -> IconName -> LinkIconAlign -> H.Html Msg
navLink attrs caption icon iconAlign =
    let
        iconH =
            makeIcon icon caption

        captionH =
            H.span [ A.class "nav-caption" ] [ H.text (" " ++ caption ++ " ") ]

        combinedH =
            case iconAlign of
                AlignLeft ->
                    [ iconH, captionH ]

                AlignRight ->
                    [ captionH, iconH ]
    in
        H.a attrs combinedH



{- Update -}


type Msg
    = VersesToLearn CallId (Result Http.Error VerseBatchRaw)
    | AttemptReturn
        { immediate : Bool
        , queued : Bool
        }
    | NextStageOrSubStage
    | PreviousStage
    | NextVerse
    | SkipVerse VerseStatus
    | CancelLearning VerseStatus
    | ResetProgress VerseStatus Bool
    | ReviewSooner VerseStatus Float
    | SetHiddenWords (Set.Set WordId)
    | WordButtonClicked WordId
    | TypingBoxInput String
    | TypingBoxEnter
    | OnScreenButtonClick String
    | UseHint
    | TrackHttpCall TrackedHttpCall
    | MakeHttpCall CallId
    | RetryFailedCalls
    | RecordActionCompleteReturned CallId (Result Http.Error ())
    | EmptyResponseTrackedHttpCallReturned CallId (Result Http.Error ())
    | EmptyResponseReturned (Result Http.Error ())
    | ActionLogsLoaded (Result Http.Error (List ActionLog))
    | ProcessNewActionLogs
    | SessionStatsLoaded (Result Http.Error SessionStats)
    | MorePractice Float
    | ToggleHelp
    | TogglePreviousVerseVisible
    | ToggleDropdown Dropdown
    | TogglePinnableMenu Dropdown
    | TogglePreferTestsToReading
    | NavigateTo Url
    | WindowResize { width : Int, height : Int }
    | ReceivePreferences JD.Value
    | ReattemptFocus String Int
    | GetTime Time.Time
    | StartHelpTour
    | FinishHelpTour
    | NextHelpTourStep
    | PreviousHelpTourStep
    | Noop


type ActionCompleteType
    = TestAction


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    case model.helpTour of
        Nothing ->
            updateMain msg model

        Just (HelpTour helpTour) ->
            updateHelpTour msg model helpTour


updateMain : Msg -> Model -> ( Model, Cmd Msg )
updateMain msg model =
    case msg of
        VersesToLearn callId result ->
            handleRetries handleVersesToLearn model callId result

        AttemptReturn options ->
            attemptReturn model options

        NextStageOrSubStage ->
            moveToNextStageOrSubStage model

        PreviousStage ->
            moveToPreviousStage model

        NextVerse ->
            moveToNextVerse model

        SkipVerse verseStatus ->
            moveToNextVerse model
                |> addCommands [ recordSkipVerse verseStatus ]

        CancelLearning verseStatus ->
            moveToNextVerse model
                |> addCommands [ recordCancelLearning verseStatus ]

        ResetProgress verseStatus confirmed ->
            handleResetProgress model verseStatus confirmed

        ReviewSooner verseStatus reviewAfter ->
            moveToNextVerse model
                |> addCommands [ recordReviewSooner verseStatus reviewAfter ]

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

        RetryFailedCalls ->
            retryFailedCalls model

        -- This is used for calls that return no data that we need to process
        EmptyResponseTrackedHttpCallReturned callId result ->
            handleRetries (\model result -> ( model, Cmd.none )) model callId result

        EmptyResponseReturned result ->
            ( model, Cmd.none )

        RecordActionCompleteReturned callId result ->
            handleRetries handleRecordActionCompleteReturned model callId result

        ActionLogsLoaded result ->
            handleActionLogs model result

        ProcessNewActionLogs ->
            processNewActionLogs model

        SessionStatsLoaded result ->
            handleSessionStatsLoaded model result

        MorePractice accuracy ->
            startMorePractice model accuracy

        ToggleHelp ->
            ( { model | helpVisible = not model.helpVisible }, Cmd.none )

        TogglePreviousVerseVisible ->
            ( { model | previousVerseVisible = not model.previousVerseVisible }, Cmd.none )

        ToggleDropdown dropdown ->
            ( toggleDropdown model dropdown
            , Cmd.none
            )

        TogglePinnableMenu menu ->
            togglePinnableMenu model menu

        TogglePreferTestsToReading ->
            togglePreferTestsToReading model

        NavigateTo url ->
            ( model
            , Navigation.load url
            )

        WindowResize size ->
            -- Can cause reflow of words and change of sizes of everything,
            -- therefore need to reposition (but not change focus)
            ( { model
                | windowSize = size
                , pinnedMenus = setPinnedMenus model.autoSavedPreferences size
              }
            , updateTypingBoxCommand model False
            )

        ReceivePreferences prefsValue ->
            let
                newModel =
                    { model | preferences = decodePreferences prefsValue }
            in
                -- Might have switched to/from method that requires typing box
                ( newModel, updateTypingBoxCommand newModel False )

        ReattemptFocus id remainingAttempts ->
            ( model, Task.attempt (handleFocusResult id remainingAttempts) (Dom.focus id) )

        GetTime time ->
            ( { model
                | currentTime = ISO8601.fromTime time
              }
            , Cmd.none
            )

        StartHelpTour ->
            startHelpTour model

        FinishHelpTour ->
            finishHelpTour model

        NextHelpTourStep ->
            nextHelpTourStep model

        PreviousHelpTourStep ->
            previousHelpTourStep model

        Noop ->
            ( model, Cmd.none )



{- Update helpers -}


{-| Add a list of Cmds to a (Model, Cmd) pair
-}
addCommands : List (Cmd Msg) -> ( Model, Cmd Msg ) -> ( Model, Cmd Msg )
addCommands cmds ( model, cmd ) =
    model ! (cmd :: cmds)


{-| Add a list of commands produced by producer function to a (Model, Cmd) pair,
   threading the new model into the producer.
-}
addCommandsM : (Model -> List (Cmd Msg)) -> ( Model, Cmd Msg ) -> ( Model, Cmd Msg )
addCommandsM producer ( model, cmd ) =
    let
        newCommands =
            producer model
    in
        addCommands newCommands ( model, cmd )


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


updateSessionDataPlus : Model -> a -> (SessionData -> ( SessionData, a )) -> ( Model, a )
updateSessionDataPlus model defaultRetval updater =
    withSessionData model
        ( model, defaultRetval )
        (\sessionData ->
            let
                ( newSessionData, retval ) =
                    updater sessionData
            in
                ( { model | learningSession = Session newSessionData }
                , retval
                )
        )


updateSessionData : Model -> (SessionData -> SessionData) -> Model
updateSessionData model updater =
    let
        ( newModel, _ ) =
            updateSessionDataPlus model () (\s -> ( updater s, () ))
    in
        newModel


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
    updateSessionDataPlus model
        defaultRetval
        (\sessionData ->
            let
                ( newCurrentVerse, retval ) =
                    updater sessionData.currentVerse

                newSessionData =
                    { sessionData
                        | currentVerse = newCurrentVerse
                    }
            in
                ( newSessionData
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



{- Update functions -}


attemptReturn : Model -> { immediate : Bool, queued : Bool } -> ( Model, Cmd Msg )
attemptReturn model { immediate, queued } =
    let
        returnUrl =
            getReturnUrl model

        callsInProgress =
            not <| Dict.isEmpty model.currentHttpCalls

        failedCalls =
            not <| List.isEmpty model.permanentFailHttpCalls

        returnCmd =
            Navigation.load returnUrl

        -- returnMsg needed when using in conjunction with confirm
        returnMsg =
            NavigateTo returnUrl

        doReturn =
            ( model
            , returnCmd
            )

        noop =
            ( model
            , Cmd.none
            )

        doRetry =
            if model.attemptingReturn && not queued then
                -- Don't add another queue
                noop
            else
                ( { model
                    | attemptingReturn = True
                  }
                , AttemptReturn
                    { immediate = immediate
                    , queued = True
                    }
                    |> delay (1 * Time.second)
                )

        openAjaxDropdownCmd =
            if not <| dropdownIsOpen model AjaxInfo then
                ToggleDropdown AjaxInfo
            else
                Noop

        cancelledAttemptingReturn =
            { model
                | attemptingReturn = False
            }

        doFailedCallsPrompt =
            ( cancelledAttemptingReturn
            , confirm
                ("There is data that failed to save. If you go away from this page, "
                    ++ "the data will be lost. Do you want to continue?"
                )
                returnMsg
                openAjaxDropdownCmd
            )

        doCallsInProgressPrompt =
            ( cancelledAttemptingReturn
            , confirm
                ("Data is still being saved.  If you go away from this page, "
                    ++ "the data will be lost. Do you want to continue?"
                )
                returnMsg
                openAjaxDropdownCmd
            )
    in
        if not callsInProgress && not failedCalls then
            doReturn
        else if callsInProgress then
            if immediate then
                doCallsInProgressPrompt
            else
                -- keep trying until done, don't prompt
                doRetry
        else if immediate || not queued then
            doFailedCallsPrompt
        else
            ( setDropdownOpen AjaxInfo model
            , Cmd.none
            )


normalizeVerseBatch : VerseBatchRaw -> ( VerseBatch, Maybe SessionStats, Maybe (List ActionLog) )
normalizeVerseBatch vbr =
    ( { learningTypeRaw = vbr.learningTypeRaw
      , returnTo = vbr.returnTo
      , maxOrderValRaw = vbr.maxOrderValRaw
      , untestedOrderVals = vbr.untestedOrderVals
      , verseStatuses = normalizeVerseStatuses vbr
      }
    , vbr.sessionStats
    , vbr.actionLogs
    )


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
                , lastTested = vs.lastTested
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


verseBatchToSession : VerseBatch -> Maybe (List ActionLog) -> TestOrReadPreference -> ( Maybe SessionData, Cmd Msg )
verseBatchToSession batch actionLogs testOrReadPreference =
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
                                    setupCurrentVerse verse learningType testOrReadPreference

                                actionLogStore =
                                    case actionLogs of
                                        Nothing ->
                                            { processed = Dict.empty
                                            , toProcess = Dict.empty
                                            , beingProcessed = Nothing
                                            }

                                        Just logs ->
                                            { processed = actionLogListToDict logs
                                            , toProcess = Dict.empty
                                            , beingProcessed = Maybe.Nothing
                                            }
                            in
                                ( Just
                                    { verses =
                                        { verseStatuses = batch.verseStatuses
                                        , learningType = learningType
                                        , returnTo = batch.returnTo
                                        , maxOrderVal = maxOrderVal
                                        , untestedOrderVals = batch.untestedOrderVals
                                        }
                                    , currentVerse = newCurrentVerse
                                    , actionLogStore = actionLogStore
                                    }
                                , cmd
                                )



-- Merge in new verses. The only things which actually needs updating are:
-- * 'verseStatuses' - the verse store,
-- the rest will be the same, or the current model will be
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


flashActionLogDuration : Float
flashActionLogDuration =
    Time.second * 0.6


processNewActionLogs : Model -> ( Model, Cmd Msg )
processNewActionLogs model =
    updateSessionDataPlus model
        Cmd.none
        (\sessionData ->
            case sessionData.actionLogStore.beingProcessed of
                Just log ->
                    -- We are in the middle of processing one.
                    let
                        oldStore =
                            sessionData.actionLogStore

                        newSessionData =
                            { sessionData
                                | actionLogStore =
                                    { oldStore
                                        | beingProcessed = Nothing
                                    }
                            }
                    in
                        ( newSessionData
                        , delay (flashActionLogDuration / 2 + Time.second * 0.1) ProcessNewActionLogs
                        )

                Nothing ->
                    case Dict.toList sessionData.actionLogStore.toProcess |> List.sortBy (Tuple.second >> .created) of
                        [] ->
                            ( sessionData, Cmd.none )

                        ( k, log ) :: rest ->
                            let
                                oldStore =
                                    sessionData.actionLogStore

                                newSessionData =
                                    { sessionData
                                        | actionLogStore =
                                            { oldStore
                                              -- We put into 'processed' immediately so that it appears in
                                              -- the list at the same time as the  latest points animation is
                                              -- happening
                                                | processed = Dict.insert log.id log <| oldStore.processed
                                                , beingProcessed = Just log
                                                , toProcess = Dict.remove log.id oldStore.toProcess
                                            }
                                    }
                            in
                                ( newSessionData
                                , delay (flashActionLogDuration / 2) ProcessNewActionLogs
                                )
        )



{- Dropdowns -}


toggleDropdown : Model -> Dropdown -> Model
toggleDropdown model dropdown =
    let
        newOpenDropdown =
            case model.openDropdown of
                Just d ->
                    if d == dropdown then
                        -- close already open dropdown
                        Nothing
                    else
                        Just dropdown

                Nothing ->
                    Just dropdown
    in
        { model | openDropdown = newOpenDropdown }


closeDropdowns : Model -> Model
closeDropdowns model =
    { model | openDropdown = Nothing }


setDropdownOpen : Dropdown -> Model -> Model
setDropdownOpen dropdown model =
    { model | openDropdown = Just dropdown }


closeDropdownIfOpen : Dropdown -> Model -> Model
closeDropdownIfOpen dropdown model =
    if model.openDropdown == Just dropdown then
        { model | openDropdown = Nothing }
    else
        model


togglePinnableMenu : Model -> Dropdown -> ( Model, Cmd Msg )
togglePinnableMenu model dropdown =
    let
        wasPinned =
            menuIsPinned model dropdown

        isPinned =
            not wasPinned

        newModel1 =
            if isPinned then
                { model
                    | pinnedMenus = Set.insert (toString dropdown) model.pinnedMenus
                }
                    |> closeDropdownIfOpen dropdown
            else
                { model
                    | pinnedMenus = Set.remove (toString dropdown) model.pinnedMenus
                }
                    |> setDropdownOpen dropdown

        oldPreferences =
            model.autoSavedPreferences

        newPreferences =
            if dropdown == ActionLogsInfo then
                if isScreenLargeEnoughForSidePanels newModel1.windowSize then
                    { oldPreferences
                        | pinActionLogMenuLargeScreen = isPinned
                    }
                else
                    { oldPreferences
                        | pinActionLogMenuSmallScreen = isPinned
                    }
            else if dropdown == VerseOptionsMenu then
                if isScreenLargeEnoughForSidePanels newModel1.windowSize then
                    { oldPreferences
                        | pinVerseOptionsMenuLargeScreen = isPinned
                    }
                else
                    oldPreferences
            else
                oldPreferences

        newModel2 =
            { newModel1
                | autoSavedPreferences = newPreferences
            }
    in
        ( newModel2
        , saveAutoSavedPreferences newPreferences newModel2.httpConfig
        )


menuIsPinned : Model -> Dropdown -> Bool
menuIsPinned model dropdown =
    Set.member (toString dropdown) model.pinnedMenus



{- Other updates -}


togglePreferTestsToReading : Model -> ( Model, Cmd Msg )
togglePreferTestsToReading model =
    let
        newModel1 =
            { model
                | testOrReadPreference =
                    case model.testOrReadPreference of
                        PreferReading ->
                            PreferTests

                        PreferTests ->
                            PreferReading
            }
                |> closeDropdowns

        ( newModel2, cmd ) =
            updateCurrentVersePlus newModel1
                Cmd.none
                (\currentVerse ->
                    let
                        learningType =
                            case newModel1.learningSession of
                                Session sessionData ->
                                    sessionData.verses.learningType

                                _ ->
                                    -- Will not ever happen in reality
                                    Practice

                        testType =
                            case currentVerse.currentStage of
                                Test t _ ->
                                    t

                                _ ->
                                    FirstTest

                        ( newStageType, _ ) =
                            getStages learningType testType currentVerse.verseStatus newModel1.testOrReadPreference
                    in
                        -- we take care not to reset a test if the toggle button
                        -- doesn't make a difference to the current stage.
                        -- Otherwise we do need to call setupCurrentVerse to
                        -- initialise the test stage.
                        if (newStageType /= learningStageTypeForStage currentVerse.currentStage) then
                            setupCurrentVerse currentVerse.verseStatus learningType newModel1.testOrReadPreference
                        else
                            ( currentVerse, Cmd.none )
                )
                |> addCommandsM
                    (\m ->
                        [ stageOrVerseChangeCommands m True ]
                    )
    in
        ( newModel2
        , cmd
        )



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


setupCurrentVerse : VerseStatus -> LearningType -> TestOrReadPreference -> ( CurrentVerse, Cmd Msg )
setupCurrentVerse verse learningType testOrReadPreference =
    let
        ( firstStageType, remainingStageTypes ) =
            getStages learningType FirstTest verse testOrReadPreference

        ( newCurrentStage, cmd ) =
            initializeStage firstStageType verse
    in
        ( { verseStatus = verse
          , sessionLearningType = learningType
          , currentStage = newCurrentStage
          , seenStageTypes = []
          , remainingStageTypes = remainingStageTypes
          , recordedTestScore = Nothing
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
    recallStageWordCount verseStatus == Set.size recallProgress.passedWordIds


recallStageWordsFinishedCount : RecallProgress -> Int
recallStageWordsFinishedCount recallProgress =
    Set.size recallProgress.passedWordIds


recallStageWordCount : VerseStatus -> Int
recallStageWordCount verseStatus =
    List.length (recallWords verseStatus)


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


getStages : LearningType -> TestType -> VerseStatus -> TestOrReadPreference -> ( LearningStageType, List LearningStageType )
getStages learningType testType verseStatus testOrReadPreference =
    let
        getNonPracticeStages vs =
            if vs.needsTesting || testOrReadPreference == PreferTests then
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


type ProgressData
    = NoProgress
    | VerseProgress Float
    | SessionProgress Float Int Int


getSessionProgressData : Model -> ProgressData
getSessionProgressData model =
    withSessionData model
        NoProgress
        (\sessionData ->
            -- For 'Learning' sessions as opposed to 'Review', we might have
            -- lots of new individual items, and we don't expect the user to get
            -- through them all. Therefore the progress bar should be only the
            -- current verse. For revision/practice sessions, we can display a
            -- progress bar that includes everything in the session. However,
            -- for passage sets in 'learning' phase, we will have a mixture of
            -- review and learning. Almost always the 'learning' items will be
            -- at the end. So we just exclude learning items from the review
            -- count and switch to 'learn' mode when we come across learning
            -- items.
            let
                currentVerse =
                    sessionData.currentVerse

                -- Progress within a verse i.e. stages
                totalStageCount =
                    -- 1 for currentStage
                    1
                        + List.length currentVerse.seenStageTypes
                        + List.length currentVerse.remainingStageTypes

                stagesFinished =
                    List.length currentVerse.seenStageTypes

                -- Fractional progress within a stage
                stageProgress =
                    case currentVerse.currentStage of
                        -- For 'Read' and 'ReadForContext' we don't know how far
                        -- they have read until they press 'Next'. We could
                        -- choose [0..1]. If we choose less than 1, and the last
                        -- verse in the session has only a reading stage, then
                        -- the progress bar is less 100% when we are finally
                        -- done, which seems strange, so we prefer '1'. However,
                        -- if we choose 1 always, then if there are Read
                        -- followed by Recall stages, then we want the 'Next'
                        -- button to advance the progress bar, so for that
                        -- case we choose < 1.
                        Read ->
                            if totalStageCount == 1 then
                                1
                            else
                                0.5

                        ReadForContext ->
                            1

                        Recall rd rp ->
                            toFloat (recallStageWordsFinishedCount rp)
                                / toFloat (recallStageWordCount currentVerse.verseStatus)

                        Test td tp ->
                            case tp.currentWord of
                                TestFinished _ ->
                                    1

                                CurrentWord cw ->
                                    let
                                        wordCount =
                                            getCurrentTestWordList currentVerse (getTestingMethod model)
                                                |> List.length
                                    in
                                        toFloat cw.overallIndex / toFloat wordCount

                -- Fractional progress within verse
                verseProgress =
                    (toFloat stagesFinished + stageProgress) / toFloat totalStageCount

                isUntestedItem =
                    List.member currentVerse.verseStatus.learnOrder sessionData.verses.untestedOrderVals
            in
                if isUntestedItem then
                    VerseProgress verseProgress
                else
                    let
                        -- Progress within batch.
                        verseStore =
                            sessionData.verses

                        untestedOrderVals =
                            verseStore.untestedOrderVals

                        -- learnOrder is zero indexed, so when learnOrder == 0,
                        -- and e.g. maxOrderVal == 0, we have 1 item total, and
                        -- 0 finished items.
                        totalReviewVerses =
                            verseStore.maxOrderVal + 1 - (List.length untestedOrderVals)

                        reviewVersesFinished =
                            currentVerse.verseStatus.learnOrder
                                -- We also need to account for any untested
                                -- items we have already passed (can happen
                                -- sometimes when learning a passage).
                                -
                                    (untestedOrderVals
                                        |> List.filter
                                            (\v ->
                                                (v < currentVerse.verseStatus.learnOrder)
                                            )
                                        |> List.length
                                    )

                        overallProgress =
                            (toFloat reviewVersesFinished + verseProgress) / toFloat totalReviewVerses

                        currentVerseNumber =
                            reviewVersesFinished + 1
                    in
                        SessionProgress overallProgress totalReviewVerses currentVerseNumber
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
                newCurrentVerse
                    ! [ finishCmd
                      , initCmd
                      ]
        )
        |> addCommandsM (\newModel -> [ stageOrVerseChangeCommands newModel True ])


moveToPreviousStage : Model -> ( Model, Cmd Msg )
moveToPreviousStage model =
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
        |> addCommandsM
            (\newModel ->
                -- Do *not* include focus change here, since they are already
                -- focussing the 'back' button and we don't want to change that
                [ stageOrVerseChangeCommands newModel False ]
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
                        ( setDropdownOpen AjaxInfo model
                        , sendMsg (AttemptReturn { immediate = False, queued = False })
                        )

                    VerseNotInStore ->
                        if not (verseLoadInProgress model) then
                            loadVersesImmediate model False
                        else
                            ( model
                            , Cmd.none
                            )

                    NextVerseData verse ->
                        let
                            ( newModel1, cmd ) =
                                updateCurrentVersePlus model
                                    Cmd.none
                                    (\cv -> setupCurrentVerse verse sessionData.verses.learningType model.testOrReadPreference)

                            loadingQueueBufferSize =
                                3

                            moreVersesToLoad =
                                not <| allVersesLoaded verseStore

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
                                    loadVersesImmediate newModel1 False
                                else
                                    ( newModel1, Cmd.none )

                            newModel3 =
                                closeDropdowns newModel2
                        in
                            ( newModel3
                            , Cmd.batch
                                [ cmd
                                , loadMoreCommand
                                , stageOrVerseChangeCommands newModel3 True
                                ]
                            )

        _ ->
            ( model
            , Cmd.none
            )


getReturnUrl : Model -> Url
getReturnUrl model =
    withSessionData model
        dashboardUrl
        (\sessionData ->
            let
                url =
                    sessionData.verses.returnTo
            in
                case url of
                    "" ->
                        dashboardUrl

                    _ ->
                        url
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


allVersesLoaded : VerseStore -> Bool
allVersesLoaded verseStore =
    case List.maximum <| List.map .learnOrder <| verseStore.verseStatuses of
        Nothing ->
            True

        Just max ->
            max >= verseStore.maxOrderVal


handleResetProgress : Model -> VerseStatus -> Bool -> ( Model, Cmd Msg )
handleResetProgress model verseStatus confirmed =
    if confirmed then
        let
            newVerseStatus =
                verseStatusResetProgress verseStatus

            newModel1 =
                closeDropdowns model
        in
            updateCurrentVersePlus newModel1
                Cmd.none
                (\currentVerse ->
                    setupCurrentVerse newVerseStatus Learning model.testOrReadPreference
                )
                |> addCommandsM
                    (\m ->
                        [ stageOrVerseChangeCommands m True
                        , recordResetProgress verseStatus
                        ]
                    )
    else
        ( model
        , confirm "This will reset your progress on this item to zero. Continue?"
            (ResetProgress verseStatus True)
            Noop
        )


{-| Resets a VerseStatus to how it is at the very beginning, as per
reset_progress server side

-}
verseStatusResetProgress : VerseStatus -> VerseStatus
verseStatusResetProgress verseStatus =
    { verseStatus
        | strength = 0
        , lastTested = Nothing
        , needsTesting = True
    }


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
        oldTypedText =
            case getCurrentTestProgress model of
                Nothing ->
                    ""

                Just tp ->
                    tp.currentTypedText

        newModel1 =
            updateTestProgress model
                (\tp ->
                    { tp | currentTypedText = String.trimRight input }
                )

        testingMethod =
            getTestingMethod newModel1

        ( newModel2, cmd ) =
            if shouldCheckTypedWord testingMethod oldTypedText input then
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
                oldTypedText =
                    tp.currentTypedText

                currentTypedText =
                    oldTypedText ++ "\n"

                testingMethod =
                    getTestingMethod model

                ( newModel, cmd ) =
                    if shouldCheckTypedWord testingMethod oldTypedText currentTypedText then
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
    updateCurrentVersePlus model
        Cmd.none
        (\currentVerse ->
            withCurrentTestWord currentVerse
                ( currentVerse, Cmd.none )
                (\testType testProgress currentWord ->
                    markWord Hint currentWord.word testProgress testType currentVerse (getTestingMethod model) model.preferences model.currentTime
                )
        )
        |> addCommandsM
            (\m ->
                -- markWord may have moved us to next verse.
                [ stageOrVerseChangeCommands m True ]
            )


shouldCheckTypedWord : TestingMethod -> String -> String -> Bool
shouldCheckTypedWord testingMethod oldText input =
    let
        oldTrimmedText =
            oldText |> normalizeWordForTest

        trimmedText =
            input |> normalizeWordForTest
    in
        case testingMethod of
            FullWords ->
                -- TODO - allow ':' '.' etc in verse references
                (String.length trimmedText > 0)
                    && ((String.right 1 input == " ")
                            || (String.right 1 input == "\n")
                       )

            FirstLetter ->
                (String.length trimmedText > 0)
                    && -- Don't check again if they typed punctuation etc.
                       (oldTrimmedText /= trimmedText)
                    && -- Don't check again if they pressed delete or backspace
                       (String.length trimmedText > String.length oldTrimmedText)
                    && -- predictive keyboards can send multiple events if words are chosen,
                       -- and the second event will usually have a trailing whitespace.
                       -- We don't want to respond to this at all, otherwise a mispressed
                       -- button causes multiple failures.
                       (String.right 1 input /= " ")

            --
            OnScreen ->
                False


checkCurrentWordAndUpdate : Model -> String -> ( Model, Cmd Msg )
checkCurrentWordAndUpdate model input =
    let
        testingMethod =
            getTestingMethod model
    in
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
                            markWord checkResult currentWord.word testProgress testType currentVerse testingMethod model.preferences model.currentTime
                    )
            )
            |> addCommandsM
                (\m ->
                    [ stageOrVerseChangeCommands m True ]
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
    "[\"'\\.,;!?:\\/#!$%\\^&\\*{}=\\-_`~()\\[\\]“”‘’—–…<>]"


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


markWord : CheckResult -> Word -> TestProgress -> TestType -> CurrentVerse -> TestingMethod -> Preferences -> ISO8601.Time -> ( CurrentVerse, Cmd Msg )
markWord checkResult word testProgress testType verse testingMethod preferences currentTime =
    let
        currentWord =
            testProgress.currentWord

        attempt =
            getWordAttemptWithInitial testProgress word testingMethod

        newCheckResults =
            checkResult :: attempt.checkResults

        allowedMistakes =
            allowedMistakesForTestingMethod testingMethod

        failedCount =
            newCheckResults
                |> List.filter isAttemptFailure
                |> List.length

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
                            failedCount > allowedMistakes
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

        newTestProgress1 =
            { testProgress
                | attemptRecords = newAttempts
                , currentTypedText = newTypedText
            }

        nextCurrentWord =
            if shouldMoveOn then
                getNextCurrentWord verse newTestProgress1 testingMethod
            else
                currentWord

        newTestProgress2 =
            { newTestProgress1
                | currentWord = nextCurrentWord
            }

        newCurrentVerse1 =
            { verse
                | currentStage =
                    Test testType newTestProgress2
            }

        movedOn =
            shouldMoveOn && currentWord /= nextCurrentWord

        ( newCurrentVerse2, actionCompleteCommand ) =
            if movedOn then
                case nextCurrentWord of
                    TestFinished { accuracy } ->
                        ( if not <| isPracticeTest verse testType then
                            { newCurrentVerse1
                                | recordedTestScore =
                                    Just
                                        { accuracy = accuracy
                                        , timestamp = currentTime
                                        }
                            }
                          else
                            newCurrentVerse1
                        , recordTestComplete newCurrentVerse1 accuracy testType
                        )

                    _ ->
                        ( newCurrentVerse1
                        , Cmd.none
                        )
            else
                ( newCurrentVerse1
                , Cmd.none
                )

        ( vibrateCommand, beepCommand ) =
            if isAttemptFailure checkResult then
                if shouldMoveOn then
                    -- final failure
                    ( vibrateDevice 50, beep ( 290.0, 1 ) )
                else
                    -- mistake only
                    ( vibrateDevice 25, beep ( 330.0, 1 ) )
            else
                ( Cmd.none, Cmd.none )
    in
        ( newCurrentVerse2
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


getNextCurrentWord : CurrentVerse -> TestProgress -> TestingMethod -> CurrentTestWord
getNextCurrentWord verse testProgress testingMethod =
    let
        currentTestWordList =
            getCurrentTestWordList verse testingMethod

        testAccuracy =
            getTestResult testProgress
    in
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
    , value : String
    }


updateTypingBoxCommand : Model -> Bool -> Cmd msg
updateTypingBoxCommand model refocus =
    updateTypingBox (getUpdateTypingBoxData model refocus)


getUpdateTypingBoxData : Model -> Bool -> UpdateTypingBoxData
getUpdateTypingBoxData model refocus =
    case getCurrentVerse model of
        Just currentVerse ->
            case getCurrentTestProgress model of
                Just tp ->
                    case tp.currentWord of
                        TestFinished _ ->
                            hideTypingBoxData

                        CurrentWord cw ->
                            { typingBoxId = typingBoxId
                            , typingBoxContainerId = typingBoxContainerId
                            , wordButtonId = idForButton cw.word currentVerse.verseStatus.id
                            , expectedClass = classForTypingBox <| typingBoxInUse tp (getTestingMethod model)
                            , hardMode = shouldUseHardTestingMode currentVerse
                            , refocus = refocus
                            , value = tp.currentTypedText
                            }

                Nothing ->
                    hideTypingBoxData

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
    , value = ""
    }


focusDefaultButton : Model -> Cmd Msg
focusDefaultButton model =
    withSessionData model
        Cmd.none
        (\sessionData ->
            let
                downcastButton b =
                    { default = b.default
                    , id = b.id
                    }

                buttons =
                    case model.helpTour of
                        Nothing ->
                            buttonsForStage model sessionData.currentVerse sessionData.verses model.preferences |> List.map downcastButton

                        Just (HelpTour helpTour) ->
                            helpTourButtons helpTour |> List.map downcastButton

                defaultButtons =
                    List.filter (\b -> b.default == Default) buttons

                shouldFocusTypingBox =
                    if model.helpTour == Nothing then
                        case getCurrentTestProgress model of
                            Just tp ->
                                typingBoxInUse tp (getTestingMethod model)

                            Nothing ->
                                False
                    else
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
                        -- appearing in the DOM yet. In addition, there is some
                        -- issue with Firefox which means that if you are in a
                        -- test, and press space at the end of the last word,
                        -- the word is checked, the the 'OK' button appears (as
                        -- default), the DOM focus happens and then Firefox
                        -- thinks that space was pressed with that button
                        -- default, and 'presses' that button. We have found
                        -- this can be fixed by inserting a small, non-zero
                        -- delay using Process.sleep
                        Task.attempt (handleFocusResult id 5)
                            (Process.sleep 100
                                |> Task.andThen (\_ -> Dom.focus id)
                            )
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
    in
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
            |> addCommandsM
                (\m ->
                    [ stageOrVerseChangeCommands m True ]
                )


type TestDueAfter
    = NeverDue
    | DueAfter Float


oneYear : number
oneYear =
    365 * 24 * oneHour


oneHour : number
oneHour =
    60 * 60 * 1000


{-| If a test has been done, returns the time in milliseconds (from the last test)
    that the next test will be due.

-}
calculateNextTestDue : CurrentVerse -> Maybe TestDueAfter
calculateNextTestDue currentVerse =
    let
        verseStatus =
            currentVerse.verseStatus
    in
        case currentVerse.recordedTestScore of
            Nothing ->
                Nothing

            Just recordedTest ->
                -- logic here correponds to Identity.record_verse_action server side
                let
                    newStrength =
                        calculateNewVerseStrength verseStatus recordedTest
                in
                    if newStrength >= MemoryModel.learnt then
                        Just NeverDue
                    else
                        -- MemoryModel works in seconds, we are in milliseconds, so
                        -- convert here:
                        Just (DueAfter (1000 * MemoryModel.nextTestDueAfter newStrength))


calculateNewVerseStrength : VerseStatus -> { accuracy : Float, timestamp : ISO8601.Time } -> Float
calculateNewVerseStrength verseStatus { accuracy, timestamp } =
    let
        timeElapsed =
            case verseStatus.lastTested of
                Nothing ->
                    Nothing

                Just lt ->
                    -- MemoryModel works in seconds, not milliseconds
                    Just ((ISO8601.diff timestamp lt) / 1000)
    in
        MemoryModel.strengthEstimate verseStatus.strength accuracy timeElapsed


currentVerseStrength : CurrentVerse -> Float
currentVerseStrength currentVerse =
    case currentVerse.recordedTestScore of
        Nothing ->
            currentVerse.verseStatus.strength

        Just recordedTest ->
            calculateNewVerseStrength currentVerse.verseStatus recordedTest


friendlyTimeUntil : TestDueAfter -> String
friendlyTimeUntil testdue =
    case testdue of
        NeverDue ->
            "Fully learnt"

        DueAfter time ->
            let
                seconds =
                    time / 1000

                hours =
                    seconds / 3600

                rHours =
                    round hours

                days =
                    hours / 24

                rDays =
                    round days

                weeks =
                    days / 7

                rWeeks =
                    round weeks

                months =
                    days / 30

                rMonths =
                    round months
            in
                if hours < 1 then
                    "< 1 hour"
                else if rHours == 1 then
                    "1 hour"
                else if rHours < 24 then
                    interpolate "{0} hours" [ toString rHours ]
                else if rDays == 1 then
                    "1 day"
                else if rDays < 7 then
                    interpolate "{0} days" [ toString rDays ]
                else if rWeeks == 1 then
                    "1 week"
                else if rWeeks < 8 then
                    interpolate "{0} weeks" [ toString rWeeks ]
                else if rMonths == 1 then
                    "1 month"
                else
                    interpolate "{0} months" [ toString rMonths ]



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
    | RecordSkipVerse VerseStatus
    | RecordCancelLearning VerseStatus
    | RecordResetProgress VerseStatus
    | RecordReviewSooner VerseStatus Float
    | LoadVerses Bool


type alias QueuedCall =
    { call : TrackedHttpCall
    , attempts : Int
    }


maxHttpRetries : number
maxHttpRetries =
    6


trackedHttpCallCaption : TrackedHttpCall -> String
trackedHttpCallCaption call =
    case call of
        RecordTestComplete currentVerse _ testType ->
            if isPracticeTest currentVerse testType then
                interpolate "Marking done - {0}" [ currentVerse.verseStatus.localizedReference ]
            else
                interpolate "Saving score - {0}" [ currentVerse.verseStatus.localizedReference ]

        RecordReadComplete currentVerse ->
            interpolate "Recording read - {0}" [ currentVerse.verseStatus.localizedReference ]

        RecordSkipVerse verseStatus ->
            interpolate "Recording skipped item {0}" [ verseStatus.localizedReference ]

        RecordCancelLearning verseStatus ->
            interpolate "Recording cancelled item {0}" [ verseStatus.localizedReference ]

        RecordResetProgress verseStatus ->
            interpolate "Resetting progress for {0}" [ verseStatus.localizedReference ]

        RecordReviewSooner verseStatus _ ->
            interpolate "Marking {0} for reviewing sooner" [ verseStatus.localizedReference ]

        LoadVerses _ ->
            "Loading items for learning..."


type alias CallId =
    Int


{-| Start a tracked call, first registering
it and then triggering its execution.

-}
startTrackedCall : Model -> TrackedHttpCall -> ( Model, Cmd Msg )
startTrackedCall model trackedCall =
    triggerQueuedCalls (addTrackedCall model trackedCall)


{-| For a given TrackedHttpCall object, return a command that triggers
the HTTP call to be started.

Technically this doesn't need to return a Cmd Msg (we could just update the
model directly in all places that use this function), but rewiring from
`Http.send` to using `TrackedHttpCall` is much easier if we use a `Cmd Msg` and
this utility.

There can be race conditions that occur due to routing these message through
another `update` loop, instead of updating the model directly. Mostly for our
purposes these don't matter, but where they might we sometimes bypass this
mechanism and update the model directly e.g. loadVersesImmediate vs loadVerses
-}
sendStartTrackedCallMsg : TrackedHttpCall -> Cmd Msg
sendStartTrackedCallMsg trackedCall =
    sendMsg <| TrackHttpCall trackedCall


{-| Start an HTTP call if appropriate.

There are dependencies between some API calls for correct functioning. For
example, reviewsooner should come after actioncomplete for a given verse. Also,
since we add timestamps server side, not client side, the data is kept in better
more logical shape if we strictly order API calls to be sent in the order that
the user actually triggered them.

-}
triggerQueuedCalls : Model -> ( Model, Cmd Msg )
triggerQueuedCalls model =
    let
        noop =
            ( model
            , Cmd.none
            )
    in
        if queueBlocked model then
            -- We wait until the user has pressed the 'Retry' button and the
            -- previous calls all succeed before we try subsequently ordered
            -- ones.
            noop
        else
            case getOrderedQueuedCalls model of
                [] ->
                    noop

                ( callId, queuedCall ) :: _ ->
                    makeHttpCall model callId


{-| Gets any unsent calls in the order they should be sent.
-}
getOrderedQueuedCalls : Model -> List ( CallId, QueuedCall )
getOrderedQueuedCalls model =
    Dict.toList model.currentHttpCalls
        |> List.filter (\( callId, { call, attempts } ) -> attempts == 0)
        |> List.sortBy Tuple.first


queueBlocked : Model -> Bool
queueBlocked model =
    let
        failedCalls =
            not <| List.isEmpty model.permanentFailHttpCalls

        callsInProgress =
            Dict.values model.currentHttpCalls
                |> List.filter (\{ attempts } -> attempts > 0)
                |> List.isEmpty
                |> not
    in
        (failedCalls || callsInProgress)


{-| The motivation for having 'MakeHttpCall' and 'makeHttpCall' separate from
'startTrackedCall' is that when we retry, we want to add a delay. It seems
easier to just use the `delay` helper and send another message than to convert
`Http.send` calls into Task.Tasks in order to insert Process.sleep tasks etc.
(at least, I couldn't figure out the type problems caused by trying to work with
Tasks instead of Cmd Msg).

-}
makeHttpCall : Model -> CallId -> ( Model, Cmd Msg )
makeHttpCall model callId =
    case Dict.get callId model.currentHttpCalls of
        Nothing ->
            ( model, Cmd.none )

        Just { call, attempts } ->
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

                cmd =
                    case call of
                        RecordTestComplete currentVerse accuracy testType ->
                            callRecordTestComplete model.httpConfig callId currentVerse accuracy testType

                        RecordReadComplete currentVerse ->
                            callRecordReadComplete model.httpConfig callId currentVerse

                        RecordSkipVerse verseStatus ->
                            callRecordSkipVerse model.httpConfig callId verseStatus

                        RecordCancelLearning verseStatus ->
                            callRecordCancelLearning model.httpConfig callId verseStatus

                        RecordResetProgress verseStatus ->
                            callRecordResetProgress model.httpConfig callId verseStatus

                        RecordReviewSooner verseStatus reviewAfter ->
                            callRecordReviewSooner model.httpConfig callId verseStatus reviewAfter

                        LoadVerses initialPageLoad ->
                            callLoadVerses model.httpConfig callId model initialPageLoad
            in
                ( newModel, cmd )


addTrackedCall : Model -> TrackedHttpCall -> Model
addTrackedCall model trackedCall =
    let
        -- We need to give the call an order so that it executes after all
        -- current (or failed) calls.
        usedCallIds =
            (Dict.keys model.currentHttpCalls) ++ (List.map Tuple.first model.permanentFailHttpCalls)

        callId =
            1 + (usedCallIds |> List.maximum |> Maybe.withDefault 0)
    in
        addOrderedTrackedCall model callId trackedCall


addOrderedTrackedCall : Model -> CallId -> TrackedHttpCall -> Model
addOrderedTrackedCall model callId trackedCall =
    { model
        | currentHttpCalls = Dict.insert callId { call = trackedCall, attempts = 0 } model.currentHttpCalls
    }


{-| Given an `update` like function of type `Model -> a -> ( Model, Cmd Msg)`,
a model, a CallId and a Http result, handles the retries for the call, and
executes the update function.

-}
handleRetries : (Model -> a -> ( Model, Cmd Msg )) -> Model -> CallId -> Result.Result Http.Error a -> ( Model, Cmd Msg )
handleRetries updateFunction model callId result =
    case result of
        Ok v ->
            let
                ( newModel1, cmd1 ) =
                    updateFunction (markCallFinished model callId) v

                ( newModel2, cmd2 ) =
                    triggerQueuedCalls newModel1
            in
                ( newModel2
                , Cmd.batch
                    [ cmd1
                    , cmd2
                    ]
                )

        Err err ->
            case err of
                Http.BadUrl _ ->
                    ( markPermanentFailCall model callId
                    , Cmd.none
                    )

                _ ->
                    -- Other errors could all be temporary in theory, so we try again.
                    let
                        -- TODO save error message
                        _ =
                            Debug.log "HTTP call failed" err
                    in
                        markFailAndRetry model callId


markCallFinished : Model -> CallId -> Model
markCallFinished model callId =
    let
        newModel1 =
            { model
                | currentHttpCalls = Dict.remove callId model.currentHttpCalls
            }

        newModel2 =
            if
                dropdownIsOpen model AjaxInfo
                    && List.isEmpty newModel1.permanentFailHttpCalls
                    && Dict.isEmpty newModel1.currentHttpCalls
            then
                closeDropdowns newModel1
            else
                newModel1
    in
        newModel2


markPermanentFailCall : Model -> CallId -> Model
markPermanentFailCall model callId =
    case Dict.get callId model.currentHttpCalls of
        Nothing ->
            model

        Just { call } ->
            { model
                | currentHttpCalls = Dict.remove callId model.currentHttpCalls
                , permanentFailHttpCalls = ( callId, call ) :: model.permanentFailHttpCalls
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
                ( model
                , delay
                    (Time.second * (2 ^ attempts |> toFloat))
                    (MakeHttpCall callId)
                )


retryFailedCalls : Model -> ( Model, Cmd Msg )
retryFailedCalls model =
    let
        failedCalls =
            model.permanentFailHttpCalls

        newModel1 =
            { model
                | permanentFailHttpCalls = []
            }

        newModel2 =
            List.foldl
                (\( callId, call ) m ->
                    addOrderedTrackedCall m callId call
                )
                newModel1
                failedCalls
    in
        triggerQueuedCalls newModel2


delay : Time.Time -> msg -> Cmd msg
delay time msg =
    Process.sleep time
        |> Task.perform (\_ -> msg)


verseLoadInProgress : Model -> Bool
verseLoadInProgress model =
    Dict.values model.currentHttpCalls |> List.any (\{ call } -> isLoadVersesCall call)


verseLoadFailed : Model -> Bool
verseLoadFailed model =
    model.permanentFailHttpCalls |> List.map Tuple.second |> List.any isLoadVersesCall


isLoadVersesCall : TrackedHttpCall -> Bool
isLoadVersesCall call =
    case call of
        LoadVerses _ ->
            True

        _ ->
            False



{- Details of actual API calls start here -}
{- versestolearn2 API -}


versesToLearnUrl : String
versesToLearnUrl =
    "/api/learnscripture/v1/versestolearn2/"


{-| Trigger verse load via a Cmd
-}
loadVerses : Bool -> Cmd Msg
loadVerses initialPageLoad =
    sendStartTrackedCallMsg (LoadVerses initialPageLoad)


{-| Trigger verse load immediately

More robust than loadVerses, useful when we
have access to the full model
-}
loadVersesImmediate : Model -> Bool -> ( Model, Cmd Msg )
loadVersesImmediate model initialPageLoad =
    startTrackedCall model (LoadVerses initialPageLoad)


callLoadVerses : HttpConfig -> CallId -> Model -> Bool -> Cmd Msg
callLoadVerses httpConfig callId model initialPageLoad =
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
                |> Erl.addQuery "initial_page_load" (encodeBool initialPageLoad)
                |> Erl.toString
    in
        Http.send (VersesToLearn callId) (myHttpGet url verseBatchRawDecoder)


handleVersesToLearn : Model -> VerseBatchRaw -> ( Model, Cmd Msg )
handleVersesToLearn model verseBatchRaw =
    let
        ( verseBatch, sessionStats, actionLogs ) =
            normalizeVerseBatch verseBatchRaw

        ( maybeBatchSession, sessionCmd ) =
            verseBatchToSession verseBatch actionLogs model.testOrReadPreference

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
                    newModel1 =
                        { model
                            | learningSession = Session ns
                        }

                    newModel2 =
                        case sessionStats of
                            Nothing ->
                                newModel1

                            Just s ->
                                { newModel1
                                    | sessionStats = sessionStats
                                }

                    loadMoreCommand =
                        if allVersesLoaded ns.verses || verseLoadInProgress model then
                            Cmd.none
                        else
                            case ns.currentVerse.verseStatus.verseSet of
                                Nothing ->
                                    Cmd.none

                                Just vs ->
                                    -- For passages, we eagerly load the rest of
                                    -- the verses, because it is more imporant
                                    -- for the user not to get interrupted in
                                    -- reviewing the set if their internet
                                    -- connection gets interrupted. However,
                                    -- some verse sets are really large (more
                                    -- than 1 chapter), so disable this
                                    -- behaviour for them. All chapters are less
                                    -- than 90 verses (except Psalm 119)
                                    if vs.setType == Passage && ns.verses.maxOrderVal < 90 then
                                        loadVerses False
                                    else
                                        Cmd.none

                in
                    newModel2
                        ! [ sessionCmd
                          , if previousSessionEmpty then
                                stageOrVerseChangeCommands newModel2 True
                            else
                                Cmd.none
                          , if previousSessionEmpty && actionLogs == Nothing then
                                loadActionLogs newModel2
                            else
                                Cmd.none
                          , if previousSessionEmpty && sessionStats == Nothing then
                                loadSessionStats
                            else
                                Cmd.none
                          , loadMoreCommand
                          , if previousSessionEmpty && not newModel2.autoSavedPreferences.seenHelpTour then
                                delay 500 StartHelpTour
                            else
                                Cmd.none
                          ]



{- actioncomplete API -}
-- For both test complete and reading complete


actionCompleteUrl : String
actionCompleteUrl =
    "/api/learnscripture/v1/actioncomplete/"


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
                    (encodeBool <| isPracticeTest currentVerse testType)
                ]
    in
        Http.send (RecordActionCompleteReturned callId)
            (myHttpPost httpConfig
                actionCompleteUrl
                body
                emptyDecoder
            )


isPracticeTest : CurrentVerse -> TestType -> Bool
isPracticeTest currentVerse testType =
    (currentVerse.sessionLearningType == Practice)
        || (testType == MorePracticeTest)


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


handleRecordActionCompleteReturned : Model -> () -> ( Model, Cmd Msg )
handleRecordActionCompleteReturned model () =
    model
        ! [ loadActionLogs model
          , loadSessionStats
          ]



{- skipverse -}


skipVerseUrl : String
skipVerseUrl =
    "/api/learnscripture/v1/skipverse/"


recordSkipVerse : VerseStatus -> Cmd Msg
recordSkipVerse verseStatus =
    sendStartTrackedCallMsg (RecordSkipVerse verseStatus)


callRecordSkipVerse : HttpConfig -> CallId -> VerseStatus -> Cmd Msg
callRecordSkipVerse httpConfig callId verseStatus =
    let
        body =
            Http.multipartBody
                [ Http.stringPart "uvs_id" (toString verseStatus.id)
                ]
    in
        Http.send (EmptyResponseTrackedHttpCallReturned callId)
            (myHttpPost httpConfig
                skipVerseUrl
                body
                emptyDecoder
            )



{- cancellearningverse API -}


cancelLearningUrl : String
cancelLearningUrl =
    "/api/learnscripture/v1/cancellearningverse/"


recordCancelLearning : VerseStatus -> Cmd Msg
recordCancelLearning verseStatus =
    sendStartTrackedCallMsg (RecordCancelLearning verseStatus)


callRecordCancelLearning : HttpConfig -> CallId -> VerseStatus -> Cmd Msg
callRecordCancelLearning httpConfig callId verseStatus =
    let
        body =
            Http.multipartBody
                [ Http.stringPart "uvs_id" (toString verseStatus.id)
                , Http.stringPart "localized_reference" verseStatus.localizedReference
                , Http.stringPart "version_slug" verseStatus.version.slug
                ]
    in
        Http.send (EmptyResponseTrackedHttpCallReturned callId)
            (myHttpPost httpConfig
                cancelLearningUrl
                body
                emptyDecoder
            )



{- resetprogress API -}


resetProgressUrl : String
resetProgressUrl =
    "/api/learnscripture/v1/resetprogress/"


recordResetProgress : VerseStatus -> Cmd Msg
recordResetProgress verseStatus =
    sendStartTrackedCallMsg (RecordResetProgress verseStatus)


callRecordResetProgress : HttpConfig -> CallId -> VerseStatus -> Cmd Msg
callRecordResetProgress httpConfig callId verseStatus =
    let
        body =
            Http.multipartBody
                [ Http.stringPart "localized_reference" verseStatus.localizedReference
                , Http.stringPart "version_slug" verseStatus.version.slug
                ]
    in
        Http.send (EmptyResponseTrackedHttpCallReturned callId)
            (myHttpPost httpConfig
                resetProgressUrl
                body
                emptyDecoder
            )



{- reviewSooner API -}


reviewSoonerUrl : String
reviewSoonerUrl =
    "/api/learnscripture/v1/reviewsooner/"


recordReviewSooner : VerseStatus -> Float -> Cmd Msg
recordReviewSooner verseStatus reviewAfter =
    sendStartTrackedCallMsg (RecordReviewSooner verseStatus reviewAfter)


callRecordReviewSooner : HttpConfig -> CallId -> VerseStatus -> Float -> Cmd Msg
callRecordReviewSooner httpConfig callId verseStatus reviewAfter =
    let
        body =
            Http.multipartBody
                [ Http.stringPart "localized_reference" verseStatus.localizedReference
                , Http.stringPart "version_slug" verseStatus.version.slug
                , Http.stringPart "review_after" (reviewAfter / 1000 |> round |> toString)
                ]
    in
        Http.send (EmptyResponseTrackedHttpCallReturned callId)
            (myHttpPost httpConfig
                reviewSoonerUrl
                body
                emptyDecoder
            )



{- actionlogs -}


loadActionLogsUrl : String
loadActionLogsUrl =
    "/api/learnscripture/v1/actionlogs/"


loadActionLogs : Model -> Cmd Msg
loadActionLogs model =
    if scoringEnabled model then
        -- No need for tracking, this is unimportant
        let
            url =
                Erl.parse loadActionLogsUrl
                    |> Erl.addQuery "highest_id_seen"
                        (withSessionData model
                            0
                            (\sessionData ->
                                Dict.union sessionData.actionLogStore.processed sessionData.actionLogStore.toProcess
                                    |> Dict.keys
                                    |> List.maximum
                                    |> Maybe.withDefault 0
                            )
                            |> toString
                        )
                    |> Erl.toString
        in
            Http.send ActionLogsLoaded (myHttpGet url actionLogsDecoder)
    else
        Cmd.none


scoringEnabled : Model -> Bool
scoringEnabled model =
    case model.user of
        GuestUser ->
            False

        Account _ ->
            True


handleActionLogs : Model -> Result Http.Error (List ActionLog) -> ( Model, Cmd Msg )
handleActionLogs model result =
    case result of
        Err msg ->
            let
                _ =
                    Debug.log "Error loading logs" msg
            in
                ( model, Cmd.none )

        Ok actionLogs ->
            updateSessionDataPlus model
                Cmd.none
                (\sessionData ->
                    let
                        oldStore =
                            sessionData.actionLogStore

                        receivedActionLogDict =
                            actionLogListToDict actionLogs

                        unprocessedActionLogs =
                            Dict.diff receivedActionLogDict oldStore.processed

                        newToProcessLogs =
                            Dict.union oldStore.toProcess unprocessedActionLogs

                        newSessionData =
                            { sessionData
                                | actionLogStore =
                                    { oldStore
                                        | toProcess = newToProcessLogs
                                    }
                            }
                    in
                        ( newSessionData
                        , if Dict.isEmpty newToProcessLogs then
                            Cmd.none
                          else
                            sendMsg ProcessNewActionLogs
                        )
                )


actionLogListToDict : List ActionLog -> Dict.Dict Int ActionLog
actionLogListToDict actionLogs =
    Dict.fromList <| List.map (\log -> ( log.id, log )) actionLogs



{- sessionstats -}


loadSessionStatsUrl : String
loadSessionStatsUrl =
    "/api/learnscripture/v1/sessionstats/"


loadSessionStats : Cmd Msg
loadSessionStats =
    Http.send SessionStatsLoaded (myHttpGet loadSessionStatsUrl sessionStatsDecoder)


handleSessionStatsLoaded : Model -> Result Http.Error SessionStats -> ( Model, Cmd Msg )
handleSessionStatsLoaded model result =
    let
        newModel =
            case result of
                Ok stats ->
                    { model
                        | sessionStats = Just stats
                    }

                Err msg ->
                    -- Don't really case about this error condition, informational only
                    let
                        _ =
                            Debug.log "sessionStats error" msg
                    in
                        model
    in
        ( newModel
        , Cmd.none
        )



{- savemiscpreferences -}


saveMiscPreferencesUrl : String
saveMiscPreferencesUrl =
    "/api/learnscripture/v1/savemiscpreferences/"


saveAutoSavedPreferences : AutoSavedPreferences -> HttpConfig -> Cmd Msg
saveAutoSavedPreferences preferences httpConfig =
    let
        body =
            Http.multipartBody
                [ Http.stringPart "pin_action_log_menu_large_screen" (preferences.pinActionLogMenuLargeScreen |> encodeBool)
                , Http.stringPart "pin_action_log_menu_small_screen" (preferences.pinActionLogMenuSmallScreen |> encodeBool)
                , Http.stringPart "pin_verse_options_menu_large_screen" (preferences.pinVerseOptionsMenuLargeScreen |> encodeBool)
                , Http.stringPart "seen_help_tour" (preferences.seenHelpTour |> encodeBool)
                ]
    in
        Http.send EmptyResponseReturned
            (myHttpPost httpConfig
                saveMiscPreferencesUrl
                body
                emptyDecoder
            )



{- HTTP utilities -}


sendMsg : msg -> Cmd msg
sendMsg msg =
    Task.succeed msg |> Task.perform identity


encodeBool : Bool -> String
encodeBool =
    JE.bool >> JE.encode 0


encodeFloat : Float -> String
encodeFloat =
    JE.float >> JE.encode 0


myHttpGet : String -> JD.Decoder a -> Http.Request a
myHttpGet url decoder =
    Http.request
        { method = "GET"
        , headers =
            [ Http.header "X-Requested-With" "XMLHttpRequest"
            ]
        , url = url
        , body = Http.emptyBody
        , expect = Http.expectJson decoder
        , timeout = Nothing
        , withCredentials = False
        }


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
        , expect =
            Http.expectJson decoder
            -- All our POSTs involve sending and receiving very little data, by
            -- design. Delays greater than 30s are always going to be due to network
            -- issues that mean the request is not going to get there. By aborting
            -- early we get to try again sooner.
        , timeout = Just (Time.second * 30)
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



{- Help tour -}
-- When displaying the help tour, we save a copy of the old model, so that we
-- can adjust the model used for displaying in order to make certain UI elements
-- visible that would not otherwise be visible.
-- We also need to adjust the update function, so that:
--
-- 1) certain messages (e.g. normal button clicks) are ignored
--
-- 2) other messages (responses to AJAX requests) get forwarded
--    to the saved model, otherwise those messages would be lost.


type HelpTour
    = HelpTour HelpTourData


type alias HelpTourData =
    { savedModel : Model
    , savedModelInitialSnapshot : Model
    , steps : Pivot.Pivot HelpTourStep
    }


type alias HelpTourStep =
    { html : List (H.Html Msg)
    , class : String
    , selector : Maybe String
    , adapter : Model -> Model
    }


initialTourSteps : Pivot.Pivot HelpTourStep
initialTourSteps =
    let
        fakeHttpCalls =
            (\model ->
                withCurrentVerse model
                    model
                    (\currentVerse ->
                        { model
                            | currentHttpCalls =
                                Dict.fromList
                                    [ ( 0
                                      , { call = RecordTestComplete currentVerse 0.9 FirstTest
                                        , attempts = 2
                                        }
                                      )
                                    ]
                        }
                    )
            )

        fakeFailedHttpCalls =
            (\model ->
                withCurrentVerse model
                    model
                    (\currentVerse ->
                        { model
                            | permanentFailHttpCalls =
                                [ ( 0, RecordTestComplete currentVerse 0.9 FirstTest ) ]
                        }
                    )
            )

        fakeFinishedTest =
            (\model ->
                withSessionData model
                    model
                    (\sessionData ->
                        let
                            currentVerse =
                                sessionData.currentVerse

                            currentTestWordList =
                                getCurrentTestWordList currentVerse FullWords

                            testProgress =
                                { attemptRecords =
                                    Dict.fromList
                                        (List.map
                                            (\w ->
                                                ( getWordId w
                                                , { finished = True
                                                  , checkResults = [ Success ]
                                                  , allowedMistakes = 2
                                                  }
                                                )
                                            )
                                            currentTestWordList
                                        )
                                , currentTypedText = ""
                                , currentWord = TestFinished { accuracy = 1.0 }
                                }

                            newCurrentVerse =
                                { currentVerse
                                    | currentStage =
                                        Test FirstTest testProgress
                                    , recordedTestScore =
                                        Just
                                            { accuracy = 1
                                            , timestamp = model.currentTime
                                            }
                                }

                            newSessionData =
                                { sessionData
                                    | currentVerse = newCurrentVerse
                                }
                        in
                            { model
                                | learningSession = Session newSessionData
                            }
                    )
            )

        show x =
            [ H.p []
                [ H.text x
                ]
            ]

        first =
            { html = show "Hello! This guided tour will take you around the learning page interface."
            , class = "help-tour-welcome"
            , selector = Nothing
            , adapter = identity
            }

        rest =
            [ { html = show "Use the link in the top left corner to go back to the dashboard at any time."
              , class = "help-tour-dashboard"
              , selector = Just ".nav-item.return-link"
              , adapter = identity
              }
            , { html = show "This bar shows your progress in learning a verse for the first time, or your total progress in a review session."
              , class = "help-tour-session-progress"
              , selector = Just ".nav-item.session-progress"
              , adapter = identity
              }
            , { html = show "The total points you've earned in the current batch of verses are displayed here."
              , class = "help-tour-total-points"
              , selector = Just "nav .action-logs .nav-item"
              , adapter = identity
              }
            , { html = show "You can tap/click this menu header to show more detail."
              , class = "help-tour-action-logs"
              , selector = Just "nav .action-logs .nav-dropdown-menu.menu-open"
              , adapter = setDropdownOpen ActionLogsInfo
              }
            , { html = show "You can also pin this menu to the side (large screens) or the top (small screens) to have it permanently visible."
              , class = "help-tour-pin-action-logs"
              , selector = Just "nav .action-logs .menu-pin"
              , adapter = setDropdownOpen ActionLogsInfo
              }
            , { html = show "Tap the menu header again to close it."
              , class = "help-tour-action-logs-closed"
              , selector = Just "nav .action-logs .nav-item"
              , adapter = identity
              }
            , { html = show "If there is a problem saving your data, it will be displayed here. Tap the menu header for more info."
              , class = "help-tour-ajax-info"
              , selector = Just "nav .ajax-info"
              , adapter = fakeHttpCalls >> (setDropdownOpen AjaxInfo)
              }
            , { html = show "If your internet connection cuts out completely, don't worry - you can carry on working and then try to save data again when your internet connection comes back."
              , class = "help-tour-ajax-info-failures"
              , selector = Just "nav .ajax-info .menu-open .button-item"
              , adapter = fakeFailedHttpCalls >> (setDropdownOpen AjaxInfo)
              }
            , { html = show "This shows the number of new verses you have started today. If you are new to LearnScripture, it can be important to pace yourself. Why not try to learn one new verse each day?"
              , class = "help-tour-new-verses-started"
              , selector = Just "#id-new-verses-started-count"
              , adapter = identity
              }
            , { html = show "Here is the number of verses you've been tested on today."
              , class = "help-tour-new-verses-started"
              , selector = Just "#id-total-verses-tested-count"
              , adapter = identity
              }
            , { html = show "You can change your preferences at any point from here."
              , class = "help-tour-preferences"
              , selector = Just "nav .preferences-link"
              , adapter = identity
              }
            , { html = show "The approximate memory strength of each verse you are learning is displayed here."
              , class = "help-tour-verse-strength"
              , selector = Just "#id-verse-strength-value"
              , adapter = identity
              }
            , { html = show "At each stage, you are prompted with instructions to guide you through the learning and review process."
              , class = "help-tour-instructions"
              , selector = Just "#id-instructions"
              , adapter = identity
              }
            , { html = show "This menu shows additional options for the current verse."
              , class = "help-tour-verse-options-menu"
              , selector = Just "#id-verse-options-menu-btn"
              , adapter = setDropdownOpen VerseOptionsMenu
              }
            , { html = show "When you have finished a test, your test score is used to estimate your memory strength for a verse and schedule the next review. Underneath each button is a caption indicating approximately when you will next see the verse again if you choose that option."
              , class = "help-tour-test-finished-buttons"
              , selector = Just "#id-action-btns"
              , adapter = fakeFinishedTest
              }
            , { html = show "That's all for now - thanks for taking the tour! You can take it again at any point (see the 'Help' section)."
              , class = "help-tour-finish"
              , selector = Nothing
              , adapter = identity
              }
            ]
    in
        Pivot.fromCons first rest


startHelpTour : Model -> ( Model, Cmd Msg )
startHelpTour model =
    case model.helpTour of
        Nothing ->
            let
                initialHelpTourState =
                    { savedModel = model
                    , savedModelInitialSnapshot = model
                    , steps = initialTourSteps
                    }
            in
                doHelpTourStep initialHelpTourState True
                    |> addCommands [ updateTypingBox hideTypingBoxData ]

        Just helpTour ->
            -- Do not start the help tour twice
            ( model
            , Cmd.none
            )


doHelpTourStep : HelpTourData -> Bool -> ( Model, Cmd Msg )
doHelpTourStep helpTour focusDefault =
    let
        currentStep =
            Pivot.getC helpTour.steps

        adapter =
            adjustModelForHelpTour >> currentStep.adapter

        -- .savedModel can change underneath us, e.g. score logs received, so we
        -- use a snapshot that doesn't change.
        adaptedModel =
            adapter helpTour.savedModelInitialSnapshot

        finalModel =
            { adaptedModel
                | helpTour =
                    Just (HelpTour helpTour)
            }
    in
        ( finalModel
        , Cmd.batch
            [ if focusDefault then
                focusDefaultButton finalModel
              else
                Cmd.none
            , helpTourCommandForStep currentStep
            ]
        )


helpTourCommandForStep : HelpTourStep -> Cmd Msg
helpTourCommandForStep step =
    case step.selector of
        Nothing ->
            helpTourHighlightElement ""

        Just s ->
            helpTourHighlightElement s


finishHelpTour : Model -> ( Model, Cmd Msg )
finishHelpTour model =
    case model.helpTour of
        Nothing ->
            -- tour can't have been started
            ( model
            , Cmd.none
            )

        Just (HelpTour helpTour) ->
            let
                newModel1 =
                    helpTour.savedModel

                prefs =
                    newModel1.autoSavedPreferences

                newPrefs =
                    { prefs
                        | seenHelpTour = True
                    }

                newModel2 =
                    { newModel1
                        | autoSavedPreferences = newPrefs
                    }
            in
                ( newModel2
                , Cmd.batch
                    [ stageOrVerseChangeCommands newModel2 True
                    , saveAutoSavedPreferences newPrefs newModel2.httpConfig
                    , helpTourHighlightElement ""
                    ]
                )


nextHelpTourStep : Model -> ( Model, Cmd Msg )
nextHelpTourStep model =
    case model.helpTour of
        Nothing ->
            ( model
            , Cmd.none
            )

        Just (HelpTour helpTour) ->
            case Pivot.goR helpTour.steps of
                Nothing ->
                    finishHelpTour model

                Just newSteps ->
                    let
                        newHelpTour =
                            { helpTour
                                | steps = newSteps
                            }
                    in
                        doHelpTourStep newHelpTour True


previousHelpTourStep : Model -> ( Model, Cmd Msg )
previousHelpTourStep model =
    case model.helpTour of
        Nothing ->
            ( model
            , Cmd.none
            )

        Just (HelpTour helpTour) ->
            case Pivot.goL helpTour.steps of
                Nothing ->
                    ( model
                    , Cmd.none
                    )

                Just newSteps ->
                    let
                        newHelpTour =
                            { helpTour
                                | steps = newSteps
                            }
                    in
                        -- don't change focus in this case, keep it on 'Previous' button
                        doHelpTourStep newHelpTour False


{-| Adjust the existing model to make it better suited
for the purposes of a help tour.

As much as possible we use the user's actually data, rather than displaying data
that relates to a made up user. However, we also make adjustments to ensure we
don't have unnecessary distractions, and have a sensible base starting point for
the UI features we want to show.

The help tour is normally shown for new users on their first verse,
so in most cases the things we change simply put things to how they would be
anyway for such a user.

-}
adjustModelForHelpTour : Model -> Model
adjustModelForHelpTour model =
    let
        newAutoSavedPreferences =
            -- we hide all the pinned menus, which is the default
            -- anyway, so we can open the drop down menus and indicate
            -- the pinning icons.
            { pinActionLogMenuSmallScreen = False
            , pinActionLogMenuLargeScreen = False
            , pinVerseOptionsMenuLargeScreen = False
            , seenHelpTour = True
            }
    in
        { model
            | openDropdown = Nothing
            , attemptingReturn = False
            , autoSavedPreferences = newAutoSavedPreferences
            , pinnedMenus = setPinnedMenus newAutoSavedPreferences model.windowSize
            , learningSession =
                let
                    -- this example status is not fully used in most cases, because
                    -- usually (always?) there is a current session with its own
                    -- current verse, and the text/reference from that is used
                    -- instead.
                    exampleVerseStatus =
                        { id = 0
                        , strength = 0
                        , lastTested = Nothing
                        , localizedReference = "John 3:16"
                        , needsTesting = True
                        , textOrder = 1
                        , suggestions = []
                        , titleText = "John 3:16"
                        , scoringTextWords = [ "For", "this", "is", "the", "way", "God", "loved", "the", "world:", "He", "gave", "his", "one", "and", "only", "Son,", "so", "that", "everyone", "who", "believes", "in", "him", "will", "not", "perish", "but", "have", "eternal", "life." ]
                        , learnOrder = 0
                        , verseSet = Nothing
                        , version =
                            { fullName = "New English Translation"
                            , shortName = "NET"
                            , url = "http://bible.org/"
                            , slug = "NET"
                            , textType = Bible
                            }
                        }

                    exampleActionLog =
                        { id = 0
                        , points = 200
                        , reason = VerseTested
                        , created = "2018-02-26T06:34:12.923Z"
                        }

                    exampleActionLogStore =
                        { processed = Dict.fromList [ ( 0, exampleActionLog ) ]
                        , beingProcessed = Nothing
                        , toProcess = Dict.empty
                        }

                    origLearningSession =
                        model.learningSession

                    ( verseStatus, actionLogStore ) =
                        case origLearningSession of
                            Loading ->
                                ( exampleVerseStatus, exampleActionLogStore )

                            VersesError _ ->
                                ( exampleVerseStatus, exampleActionLogStore )

                            Session sessionData ->
                                let
                                    userVerseStatus =
                                        sessionData.currentVerse.verseStatus

                                    userActionLogStore =
                                        sessionData.actionLogStore

                                    combinedVerseStatus =
                                        { exampleVerseStatus
                                            | localizedReference = userVerseStatus.localizedReference
                                            , titleText = userVerseStatus.titleText
                                            , scoringTextWords = userVerseStatus.scoringTextWords
                                            , strength = userVerseStatus.strength
                                        }
                                in
                                    ( combinedVerseStatus
                                    , if Dict.size userActionLogStore.processed == 0 then
                                        exampleActionLogStore
                                      else
                                        { exampleActionLogStore
                                            | processed = userActionLogStore.processed
                                        }
                                    )

                    -- To display testing stage right at beginning, we pass this
                    -- verseStatus to setupCurrentVerse. But then we change back
                    -- to the one that shows the users actual strength for that
                    -- verse, to avoid confusion.
                    zeroStrengthVerseStatus =
                        { verseStatus
                            | strength = 0
                        }

                    ( currentVerse1, _ ) =
                        setupCurrentVerse zeroStrengthVerseStatus Learning PreferReading

                    currentVerse2 =
                        { currentVerse1
                            | verseStatus = verseStatus
                        }

                    sessionData =
                        { verses =
                            { verseStatuses = [ verseStatus ]
                            , learningType = Learning
                            , returnTo = ""
                            , maxOrderVal = 0
                            , untestedOrderVals = [ 0 ]
                            }
                        , currentVerse = currentVerse2
                        , actionLogStore = actionLogStore
                        }
                in
                    Session sessionData
            , currentHttpCalls = Dict.empty
            , permanentFailHttpCalls = []
        }


{-| When help tour is active, we have a fake model in place, and the
user's real data helpTour.savedModel. To handle any confusion
between these, we have a separate update function for this case.

In some cases (e.g. data received back from AJAX calls), we need
to ensure the message gets propagated to the real model.
In some cases (e.g. buttons pressed), we want to drop the message
entirely, blocking the user from interacting with the fake model
and doing AJAX calls from it etc.
In some cases (e.g. window resize), both the fake and the real
model should be updated.

-}
updateHelpTour : Msg -> Model -> HelpTourData -> ( Model, Cmd Msg )
updateHelpTour msg model helpTour =
    let
        ignoreIt =
            ( model, Cmd.none )

        forwardToMain msg =
            updateMain msg model

        forwardToSavedModel msg =
            let
                savedModel =
                    helpTour.savedModel

                ( newSavedModel, cmd ) =
                    updateMain msg savedModel

                newHelpTour =
                    { helpTour
                        | savedModel = newSavedModel
                    }

                newFullModel =
                    { model
                        | helpTour = Just (HelpTour newHelpTour)
                    }
            in
                ( newFullModel, cmd )

        forwardToBoth msg =
            let
                ( fullModel1, cmd1 ) =
                    forwardToSavedModel msg

                ( fullModel2, cmd2 ) =
                    updateMain msg fullModel1
            in
                ( fullModel2
                , Cmd.batch
                    [ cmd1
                    , cmd2
                    ]
                )

        ignoreSideEffects ( newModel, cmd ) =
            ( newModel, Cmd.none )
    in
        case msg of
            VersesToLearn _ _ ->
                forwardToSavedModel msg

            AttemptReturn _ ->
                ignoreIt

            NextStageOrSubStage ->
                ignoreIt

            PreviousStage ->
                ignoreIt

            NextVerse ->
                ignoreIt

            SkipVerse _ ->
                ignoreIt

            CancelLearning _ ->
                ignoreIt

            ResetProgress _ _ ->
                ignoreIt

            ReviewSooner _ _ ->
                ignoreIt

            SetHiddenWords _ ->
                ignoreIt

            WordButtonClicked _ ->
                ignoreIt

            TypingBoxInput _ ->
                ignoreIt

            TypingBoxEnter ->
                ignoreIt

            OnScreenButtonClick _ ->
                ignoreIt

            UseHint ->
                ignoreIt

            -- We allow calls to continue retrying - the user may have
            -- started AJAX and then started the help tour.
            TrackHttpCall _ ->
                forwardToSavedModel msg

            MakeHttpCall _ ->
                forwardToSavedModel msg

            RetryFailedCalls ->
                forwardToSavedModel msg

            EmptyResponseTrackedHttpCallReturned _ _ ->
                forwardToSavedModel msg

            EmptyResponseReturned _ ->
                forwardToSavedModel msg

            RecordActionCompleteReturned _ _ ->
                forwardToSavedModel msg

            ActionLogsLoaded _ ->
                forwardToSavedModel msg

            ProcessNewActionLogs ->
                forwardToSavedModel msg

            SessionStatsLoaded _ ->
                forwardToSavedModel msg

            MorePractice _ ->
                ignoreIt

            ToggleHelp ->
                ignoreIt

            TogglePreviousVerseVisible ->
                ignoreIt

            ToggleDropdown _ ->
                ignoreIt

            TogglePinnableMenu _ ->
                ignoreIt

            TogglePreferTestsToReading ->
                ignoreIt

            NavigateTo _ ->
                ignoreIt

            WindowResize _ ->
                -- Need both models to be updated, but ignore side effects and
                -- then add our own back.
                forwardToBoth msg
                    |> ignoreSideEffects
                    |> addCommands [ helpTourCommandForStep (Pivot.getC helpTour.steps) ]

            ReceivePreferences _ ->
                forwardToSavedModel msg

            ReattemptFocus id remainingAttempts ->
                forwardToMain msg

            GetTime time ->
                forwardToBoth msg

            StartHelpTour ->
                ignoreIt

            FinishHelpTour ->
                forwardToMain msg

            NextHelpTourStep ->
                forwardToMain msg

            PreviousHelpTourStep ->
                forwardToMain msg

            Noop ->
                ignoreIt



{- Subscriptions -}


subscriptions : Model -> Sub Msg
subscriptions model =
    Sub.batch
        [ Window.resizes WindowResize
        , receivePreferences ReceivePreferences
        , Time.every
            -- We need a rough time, so have low update period.
            -- But want it to initialize very quickly, so
            -- we never use the dummy '0' value
            (if ISO8601.toTime model.currentTime == 0 then
                1 * Time.millisecond
             else
                10 * Time.second
            )
            GetTime
        ]



{- Decoders and encoders -}


preferencesDecoder : JD.Decoder Preferences
preferencesDecoder =
    JDP.decode Preferences
        |> JDP.required "preferencesSetup" JD.bool
        |> JDP.required "enableAnimations" JD.bool
        |> JDP.required "enableSounds" JD.bool
        |> JDP.required "enableVibration" JD.bool
        |> JDP.required "desktopTestingMethod" testingMethodDecoder
        |> JDP.required "touchscreenTestingMethod" testingMethodDecoder


autoSavedPreferencesDecoder : JD.Decoder AutoSavedPreferences
autoSavedPreferencesDecoder =
    JDP.decode AutoSavedPreferences
        |> JDP.required "pinActionLogMenuLargeScreen" JD.bool
        |> JDP.required "pinActionLogMenuSmallScreen" JD.bool
        |> JDP.required "pinVerseOptionsMenuLargeScreen" JD.bool
        |> JDP.required "seenHelpTour" JD.bool


testingMethodDecoder : JD.Decoder TestingMethod
testingMethodDecoder =
    stringEnumDecoder
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
        |> JDP.required "untested_order_vals" (JD.list JD.int)
        |> JDP.required "verse_statuses" (JD.list verseStatusRawDecoder)
        |> JDP.required "versions" (JD.list versionDecoder)
        |> JDP.required "verse_sets" (JD.list verseSetDecoder)
        |> JDP.optional "session_stats" (sessionStatsDecoder |> JD.map Just) Nothing
        |> JDP.optional "action_logs" (actionLogsDecoder |> JD.map Just) Nothing


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
        |> JDP.required "last_tested" (nullOr iso8601decoder)
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
        |> JDP.required "smart_name" JD.string
        |> JDP.required "url" JD.string


verseSetTypeDecoder : JD.Decoder VerseSetType
verseSetTypeDecoder =
    stringEnumDecoder
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


actionLogDecoder : JD.Decoder ActionLog
actionLogDecoder =
    JDP.decode ActionLog
        |> JDP.required "id" JD.int
        |> JDP.required "points" JD.int
        |> JDP.required "reason" scoreReasonDecodor
        |> JDP.required "created" JD.string


actionLogsDecoder : JD.Decoder (List ActionLog)
actionLogsDecoder =
    JD.list actionLogDecoder


enumDecoder : List ( comparable, a ) -> JD.Decoder comparable -> JD.Decoder a
enumDecoder items valDecoder =
    let
        d =
            Dict.fromList items
    in
        valDecoder
            |> JD.andThen
                (\val ->
                    case (Dict.get val d) of
                        Just v ->
                            JD.succeed v

                        Nothing ->
                            JD.fail <| "Unknown enum value: " ++ toString val
                )


iso8601decoder : JD.Decoder ISO8601.Time
iso8601decoder =
    JD.string
        |> JD.andThen
            (\val ->
                case ISO8601.fromString val of
                    Ok d ->
                        JD.succeed d

                    Err msg ->
                        JD.fail msg
            )


stringEnumDecoder : List ( String, a ) -> JD.Decoder a
stringEnumDecoder items =
    enumDecoder items JD.string


intEnumDecoder : List ( Int, a ) -> JD.Decoder a
intEnumDecoder items =
    enumDecoder items JD.int


textTypeDecoder : JD.Decoder TextType
textTypeDecoder =
    stringEnumDecoder
        [ ( "BIBLE", Bible )
        , ( "CATECHISM", Catechism )
        ]


learningTypeDecoder : JD.Decoder LearningType
learningTypeDecoder =
    stringEnumDecoder
        [ ( "REVISION", Revision )
        , ( "LEARNING", Learning )
        , ( "PRACTICE", Practice )
        ]


scoreReasonDecodor : JD.Decoder ScoreReason
scoreReasonDecodor =
    intEnumDecoder
        [ ( 0, VerseTested )
        , ( 1, VerseReviewed )
        , ( 2, RevisionCompleted )
        , ( 3, PerfectTestBonus )
        , ( 4, VerseLearnt )
        , ( 5, EarnedAward )
        ]


sessionStatsDecoder : JD.Decoder SessionStats
sessionStatsDecoder =
    JD.field "stats"
        (JDP.decode SessionStats
            |> JDP.required "total_verses_tested" JD.int
            |> JDP.required "new_verses_started" JD.int
        )


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


{-| See also learn.less media query
-}
isScreenLargeEnoughForSidePanels : { width : Int, height : Int } -> Bool
isScreenLargeEnoughForSidePanels windowSize =
    windowSize.width >= 385 + 860


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


dropWhile : (a -> Bool) -> List a -> List a
dropWhile func list =
    case list of
        [] ->
            []

        x :: xs ->
            if func x then
                dropWhile func xs
            else
                list


dropEndWhile : (a -> Bool) -> List a -> List a
dropEndWhile func =
    List.reverse
        >> dropWhile func
        >> List.reverse


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



{- Custom tasks -}


confirmTask : String -> b -> a -> Task.Task a b
confirmTask =
    Native.Confirm.confirm


runConfirm : Task.Task Msg Msg -> Cmd Msg
runConfirm task =
    Task.attempt
        (\result ->
            case result of
                Ok success ->
                    success

                Err fail ->
                    fail
        )
        task


{-| Provided with a prompt, a success Msg and a failure Msg, use standard
window.confirm to decide which to run and run it.

-}
confirm : String -> Msg -> Msg -> Cmd Msg
confirm prompt success fail =
    confirmTask prompt success fail |> runConfirm
