
import Html exposing (beginnerProgram, div, button, text)
import Html.Events exposing (onClick)


main =
  beginnerProgram { model = 0, view = view, update = update }


view model = div [] [ text "Hello world!" ]


type Msg = None


update msg model =
  case msg of
    None ->
      model
