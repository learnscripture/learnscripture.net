module Learn exposing (..)

import Html as H
import Html.Attributes as A


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
          , verseData = Loading
          }
        , Cmd.none
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
    | Verses VerseData


type alias VerseData =
    List String



-- TODO
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

            Verses vd ->
                H.text "TODO"
        ]


loadingDiv : H.Html msg
loadingDiv =
    H.div [ A.id "id-loading-full" ] [ H.text "Loading" ]


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
