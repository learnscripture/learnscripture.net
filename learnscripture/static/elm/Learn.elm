module Main exposing (..)

import Html exposing (div, button, text, programWithFlags)


{- Flags and external inputs -}

type alias Flags =
    { preferences : JsPreferences
    }


type alias JsPreferences =
    { preferencesSetup : Bool
    , enableAnimations : Bool
    , enableSounds : Bool
    , enableVibration : Bool
    , desktopTestingMethod : String
    , touchscreenTestingMethod : String
    }

testingMethodFromString : String -> TestingMethod
testingMethodFromString x =
    case x of
        "FULL_WORDS" ->
            FullWords

        "FIRST_LETTER" ->
            FirstLetter

        "ON_SCREEN" ->
            OnScreen

        x ->
            Debug.crash ("Uknown testing method " ++ x)


init : Flags -> ( Model, Cmd Msg )
init flags =
    let p = flags.preferences
    in ( { preferences = { preferencesSetup = p.preferencesSetup
                         , enableAnimations = p.enableAnimations
                         , enableSounds = p.enableSounds
                         , enableVibration = p.enableVibration
                         , desktopTestingMethod = testingMethodFromString p.desktopTestingMethod
                         , touchscreenTestingMethod = testingMethodFromString p.touchscreenTestingMethod
                         }
         }, Cmd.none)

{- Model -}

type alias Model =
    { preferences : Preferences
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



main : Program Flags Model Msg
main =
    programWithFlags
        { init = init
        , view = view
        , update = update
        , subscriptions = subscriptions
        }


view : Model -> Html.Html msg
view model =
    div []
        [ div [] [ text "Hello world! How are you?" ]
        , div [] [ text ("preferencesSetup: " ++ toString model.preferences.preferencesSetup) ]
        , div [] [ text ("enableVibration: " ++ toString model.preferences.enableVibration) ]
        , div [] [ text ("enableAnimations: " ++ toString model.preferences.enableAnimations) ]
        , div [] [ text ("desktopTestingMethod: " ++ toString model.preferences.desktopTestingMethod) ]
        ]


subscriptions : a -> Sub msg
subscriptions model =
    Sub.none


type Msg
    = None


update : Msg -> a -> ( a, Cmd msg )
update msg model =
    case msg of
        None ->
            ( model, Cmd.none )
