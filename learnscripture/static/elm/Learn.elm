module Learn exposing (..)

import Dict
import Html as H
import Html.Attributes as A
import Http
import Json.Decode as JD
import Json.Decode.Pipeline as JDP
import Maybe
import Navigation
import Regex as R
import Set


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
    }


init : Flags -> ( Model, Cmd Msg )
init flags =
    ( { preferences =
            case JD.decodeValue preferencesDecoder flags.preferences of
                Ok prefs ->
                    prefs

                Err err ->
                    Debug.crash err
      , user =
            case flags.account of
                Just ad ->
                    Account ad

                Nothing ->
                    GuestUser
      , learningSession = Loading
      }
    , loadVerses
    )



{- Model -}


type alias Model =
    { preferences : Preferences
    , user : User
    , learningSession : LearningSession
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


type LearningStage
    = Read
    | Test
    | TestFinished
    | PracticeStage
    | PracticeFinished


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


view : Model -> H.Html msg
view model =
    H.div []
        [ topNav model
        , case model.learningSession of
            Loading ->
                loadingDiv

            VersesError err ->
                errorMessage ("The items to learn could not be loaded (error message: " ++ toString err ++ ".) Please check your internet connection!")

            Session vs ->
                viewCurrentVerse vs model.preferences
        ]


loadingDiv : H.Html msg
loadingDiv =
    H.div [ A.id "id-loading-full" ] [ H.text "Loading" ]


errorMessage : String -> H.Html msg
errorMessage msg =
    H.div [ A.class "error" ] [ H.text msg ]


viewCurrentVerse : SessionData -> Preferences -> H.Html msg
viewCurrentVerse session preferences =
    let
        currentVerse =
            session.currentVerse
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
            ]


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


linebreak : H.Html msg
linebreak =
    H.br [] []


numberItems : List a -> List Int
numberItems l =
    List.range 0 (List.length l)


partsForVerse : VerseStatus -> List Part
partsForVerse verse =
    (List.map2 verseWordToParts verse.scoringTextWords (numberItems verse.scoringTextWords)
        |> List.concat
    )
        ++ if showReference verse then
            [ Linebreak ] ++ referenceToParts verse.localizedReference
           else
            []


type alias Index =
    Int


type Part
    = VerseWord Index String
    | ReferenceWord Index String
    | Space
    | Punct String
      -- only used for references
    | Linebreak



-- only used for within verse body
-- The initial sentence has already been split into words server side, and this
-- function does not split off punctuation, but keeps it as part of the word.


verseWordToParts : String -> Index -> List Part
verseWordToParts w idx =
    let
        ( start, end ) =
            ( String.slice 0 -1 w, String.right 1 w )
    in
        if end == "\n" then
            [ VerseWord idx start
            , Linebreak
            ]
        else
            [ VerseWord idx w
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
                    Punct w
                else if String.trim w == "" then
                    Space
                else
                    ReferenceWord idx w
            )
            (List.range 0 (List.length parts))
            parts


showReference :
    { c
        | verseSet : Maybe { a | setType : VerseSetType }
        , version : { b | textType : TextType }
    }
    -> Bool
showReference verse =
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


versePartsToHtml : LearningStage -> List Part -> List (H.Html msg)
versePartsToHtml stage parts =
    List.map
        (\p ->
            case p of
                VerseWord idx w ->
                    wordButton VerseWordButton stage idx w

                ReferenceWord idx w ->
                    wordButton ReferenceWordButton stage idx w

                Space ->
                    H.text " "

                Punct w ->
                    H.span [ A.class "punct" ]
                        [ H.text w ]

                Linebreak ->
                    linebreak
        )
        parts


type WordButtonType
    = VerseWordButton
    | ReferenceWordButton


idPrefixForButton : WordButtonType -> String
idPrefixForButton wbt =
    case wbt of
        VerseWordButton ->
            "id-word-"

        ReferenceWordButton ->
            "id-reference-part-"


idForButton : WordButtonType -> Index -> String
idForButton wbt idx =
    idPrefixForButton wbt ++ toString idx


wordButton : WordButtonType -> LearningStage -> Index -> String -> H.Html msg
wordButton wbt stage idx text =
    H.span
        [ A.class <|
            case wbt of
                VerseWordButton ->
                    "word"

                ReferenceWordButton ->
                    "word reference"
        , A.id <| idForButton wbt idx
        ]
        [ H.text text ]


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



{- Update -}


type Msg
    = LoadVerses
    | VersesToLearn (Result Http.Error VerseBatchRaw)


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



{- Update helpers -}


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


getStages : LearningType -> VerseStatus -> ( LearningStage, List LearningStage )
getStages learningType verseStatus =
    case learningType of
        Learning ->
            ( Read, [ Test, TestFinished ] )

        Revision ->
            ( Test, [ TestFinished ] )

        Practice ->
            ( PracticeStage, [ PracticeFinished ] )



{- API calls -}


versesToLearnUrl : String
versesToLearnUrl =
    "/api/learnscripture/v1/versestolearn2/"


loadVerses : Cmd Msg
loadVerses =
    Http.send VersesToLearn (Http.get versesToLearnUrl verseBatchRawDecoder)



{- Subscriptions -}


subscriptions : a -> Sub msg
subscriptions model =
    Sub.none



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
