port module LearnPorts exposing (..)

import Json.Decode as JD

port updateTypingBox : (String, String, String) -> Cmd msg

port receivePreferences : (JD.Value -> msg) -> Sub msg
