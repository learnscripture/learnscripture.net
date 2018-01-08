port module LearnPorts exposing (..)

import Json.Decode as JD


port updateTypingBox :
    { typingBoxId : String
    , typingBoxContainerId : String
    , wordButtonId : String
    , expectedClass : String
    , hardMode : Bool
    , refocus : Bool
    }
    -> Cmd msg


port receivePreferences : (JD.Value -> msg) -> Sub msg


port vibrateDevice : Int -> Cmd msg


port beep : (Float, Float) -> Cmd msg
