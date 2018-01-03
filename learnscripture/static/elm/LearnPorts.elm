port module LearnPorts exposing (..)

import Json.Decode as JD


port updateTypingBox :
    { typingBoxId : String
    , wordButtonId : String
    , expectedClass : String
    , hardMode : Bool
    }
    -> Cmd msg


port receivePreferences : (JD.Value -> msg) -> Sub msg


port vibrateDevice : Int -> Cmd msg
