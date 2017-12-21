port module LearnPorts exposing (..)

import Json.Decode as JD

port updateTypingBox : (String, String, String, Bool) -> Cmd msg

port receivePreferences : (JD.Value -> msg) -> Sub msg
