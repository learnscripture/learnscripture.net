module Main exposing (..)

import Html exposing (div, button, text, programWithFlags)


{- Main -}


main : Program Flags Model Msg
main =
    programWithFlags
        { init = init
        , view = view
        , update = update
        , subscriptions = subscriptions
        }



{- Flags and external inputs -}


type alias Flags =
    { preferences : JsPreferences
    , account : Maybe AccountData
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
    let
        p =
            flags.preferences

        a =
            flags.account
    in
        ( { preferences =
                { preferencesSetup = p.preferencesSetup
                , enableAnimations = p.enableAnimations
                , enableSounds = p.enableSounds
                , enableVibration = p.enableVibration
                , desktopTestingMethod = testingMethodFromString p.desktopTestingMethod
                , touchscreenTestingMethod = testingMethodFromString p.touchscreenTestingMethod
                }
          , user =
                case a of
                    Just ad ->
                        Account ad

                    Nothing ->
                        GuestUser
          }
        , Cmd.none
        )



{- Model -}


type alias Model =
    { preferences : Preferences
    , user : User
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



{- View -}


view : Model -> Html.Html msg
view model =
    div []
        [ div [] [ text ("Hello " ++ userDisplayName model.user ++ "! How are you?") ]
        , div [] [ text ("preferencesSetup: " ++ toString model.preferences.preferencesSetup) ]
        , div [] [ text ("enableVibration: " ++ toString model.preferences.enableVibration) ]
        , div [] [ text ("enableAnimations: " ++ toString model.preferences.enableAnimations) ]
        , div [] [ text ("desktopTestingMethod: " ++ toString model.preferences.desktopTestingMethod) ]
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
    = None


update : Msg -> a -> ( a, Cmd msg )
update msg model =
    case msg of
        None ->
            ( model, Cmd.none )



{- Subscriptions -}


subscriptions : a -> Sub msg
subscriptions model =
    Sub.none
