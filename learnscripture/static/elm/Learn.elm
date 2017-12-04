module Learn exposing (..)

import Dict
import Http
import Html as H
import Html.Attributes as A
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
    , verseData : VerseDataStatus
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


type VerseDataStatus
    = Loading
    | VersesError
    | Verses (List Verse)


type alias Verse =
    { id : Int
    , strength : Float
    , verseSet : Maybe VerseSet
    , localizedReference : String
    , needsTesting : Bool
    , textOrder : Int
    , version : Version
    , suggestions : List (List String)
    , scoringTextWords : List String
    , titleText : String
    , learnOrder : Int
    , maxOrderVal : Int
    , learningType : LearningType
    , returnTo : String
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

            VersesError ->
                errorMessage "The items to learn could not be loaded. Please check your internet connection!"

            Verses vd ->
                showVerses vd model.preferences
        ]


loadingDiv : H.Html msg
loadingDiv =
    H.div [ A.id "id-loading-full" ] [ H.text "Loading" ]


errorMessage : String -> H.Html msg
errorMessage msg =
    H.div [ A.class "error" ] [ H.text msg ]


showVerses : List Verse -> Preferences -> H.Html msg
showVerses verses preferences =
    H.div []
        ((List.map (toString >> H.text >> \x -> H.div [] [ x ]) verses))


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
    | VersesToLearn (Result Http.Error (List Verse))


update : Msg -> Model -> ( Model, Cmd msg )
update msg model =
    case msg of
        LoadVerses ->
            ( model, Cmd.none )

        VersesToLearn (Ok verses) ->
            ( { model | verseData = Verses verses }, Cmd.none )

        VersesToLearn (Err _) ->
            ( { model | verseData = VersesError }, Cmd.none )


versesToLearnUrl : String
versesToLearnUrl =
    "/api/learnscripture/v1/versestolearn/"


loadVerses : Cmd Msg
loadVerses =
    Http.send VersesToLearn (Http.get versesToLearnUrl versesDecoder)



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


versesDecoder : JD.Decoder (List Verse)
versesDecoder =
    JD.list verseDecoder


nullOr : JD.Decoder a -> JD.Decoder (Maybe a)
nullOr decoder =
    JD.oneOf
        [ JD.null Nothing
        , JD.map Just decoder
        ]


verseDecoder : JD.Decoder Verse
verseDecoder =
    JDP.decode Verse
        |> JDP.required "id" JD.int
        |> JDP.required "strength" JD.float
        |> JDP.required "verse_set" (nullOr verseSetDecoder)
        |> JDP.required "localized_reference" JD.string
        |> JDP.required "needs_testing" JD.bool
        |> JDP.required "text_order" JD.int
        |> JDP.required "version" versionDecoder
        |> JDP.required "suggestions" (JD.list (JD.list (JD.string)))
        |> JDP.required "scoring_text_words" (JD.list (JD.string))
        |> JDP.required "title_text" JD.string
        |> JDP.required "learn_order" JD.int
        |> JDP.required "max_order_val" JD.int
        |> JDP.required "learning_type" learningTypeDecoder
        |> JDP.required "return_to" JD.string


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
        [ ( "REVISION", Revision)
        , ( "LEARNING", Learning)
        , ( "PRACTICE", Practice)
        ]
