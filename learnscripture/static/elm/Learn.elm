module Learn exposing (..)

import Dict
import Html as H
import Html.Attributes as A
import Http
import Json.Decode as JD
import Json.Decode.Pipeline as JDP
import Maybe


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
      , verseData = Loading
      }
    , loadVerses
    )



{- Model -}


type alias Model =
    { preferences : Preferences
    , user : User
    , verseData : VerseData
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


type VerseData
    = Loading
    | VersesError Http.Error
    | Verses VerseStore


type alias LearnOrder =
    Int


type alias UvsId =
    Int


type alias Url =
    String


type alias VerseStore =
    { verseStatuses : Dict.Dict LearnOrder VerseStatus
    , learningType : LearningType
    , returnTo : Url
    , maxOrderVal : LearnOrder
    , currentOrderVal : LearnOrder
    , seen : List UvsId
    }


type alias VerseBatchBase a =
    { a
        | learningType : LearningType
        , returnTo : Url
        , maxOrderVal : LearnOrder
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
    a
    -> b
    -> c
    -> d
    -> e
    -> f
    -> { learningType : a
       , maxOrderVal : c
       , returnTo : b
       , verseSets : f
       , verseStatusesRaw : d
       , versions : e
       }
verseBatchRawCtr l r m v1 v2 v3 =
    { learningType = l
    , returnTo = r
    , maxOrderVal = m
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


dashboardLink : String
dashboardLink =
    "/dashboard/"


view : Model -> H.Html msg
view model =
    H.div []
        [ topNav model
        , case model.verseData of
            Loading ->
                loadingDiv

            VersesError err ->
                errorMessage ("The items to learn could not be loaded (error message: " ++ toString err ++ ".) Please check your internet connection!")

            Verses vs ->
                showVerses vs model.preferences
        ]


loadingDiv : H.Html msg
loadingDiv =
    H.div [ A.id "id-loading-full" ] [ H.text "Loading" ]


errorMessage : String -> H.Html msg
errorMessage msg =
    H.div [ A.class "error" ] [ H.text msg ]


showVerses : VerseStore -> Preferences -> H.Html msg
showVerses verseStore preferences =
    H.div []
        [ H.text <| toString verseStore ]


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
                [ link dashboardLink "Dashboard" "return" AlignLeft ]
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
                batchStore =
                    normalizeVerseBatch verseBatchRaw |> verseBatchToStore

                newStore =
                    case model.verseData of
                        Verses verseStore ->
                            mergeStores verseStore batchStore

                        _ ->
                            batchStore
            in
                ( { model
                    | verseData = Verses newStore
                  }
                , Cmd.none
                )

        VersesToLearn (Err errMsg) ->
            ( { model | verseData = VersesError errMsg }, Cmd.none )



{- Update helpers -}


normalizeVerseBatch : VerseBatchRaw -> VerseBatch
normalizeVerseBatch vbr =
    { learningType = vbr.learningType
    , returnTo = vbr.returnTo
    , maxOrderVal = vbr.maxOrderVal
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


verseBatchToStore : VerseBatch -> VerseStore
verseBatchToStore batch =
    let
        batchDict =
            Dict.fromList (List.map (\vs -> ( vs.learnOrder, vs )) batch.verseStatuses)

        minOrderVal =
            case List.minimum <| List.map .learnOrder batch.verseStatuses of
                Nothing ->
                    0

                -- should never happen in practice
                Just m ->
                    m
    in
        { verseStatuses = batchDict
        , learningType = batch.learningType
        , returnTo = batch.returnTo
        , maxOrderVal = batch.maxOrderVal
        , currentOrderVal = minOrderVal
        , seen = []
        }


mergeStores : VerseStore -> VerseStore -> VerseStore
mergeStores initialVerseStore newVerseStore =
    { initialVerseStore
        | verseStatuses =
            Dict.union newVerseStore.verseStatuses initialVerseStore.verseStatuses
    }



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
        |> JDP.required "learning_type" learningTypeDecoder
        |> JDP.required "return_to" JD.string
        |> JDP.required "max_order_val" JD.int
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
