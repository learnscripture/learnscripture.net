module LearnTests exposing (..)

import Expect exposing (Expectation)
import Fuzz exposing (Fuzzer, int, list, string)
import Test exposing (..)
import Learn exposing (..)


suite : Test
suite =
    describe "Learn.elm"
        [ describe "stripOuterPunctuation"
            [ test "removes outer punctuation" <|
                \_ ->
                    Expect.equal "hello" (stripOuterPunctuation "—--“hello!”")
            , test "doesn't remove inner punctuation" <|
                \_ ->
                    Expect.equal "some-thing" (stripOuterPunctuation "…some-thing?")
            , fuzz string "is idempotent" <|
                \s -> Expect.equal (stripOuterPunctuation s) (stripOuterPunctuation (stripOuterPunctuation s))

            ]
        , describe "checkWord"
            [ test "ignores whitespace" <|
                  \_ ->
                  Expect.equal True (checkWord "hello" "   hello    " FullWords)
            , test "ignores punctuation" <|
                  \_ ->
                  Expect.equal True (checkWord "“hello," "hello!!!???" FullWords)
            , test "False for different short words" <|
                  \_ ->
                  Expect.equal False (checkWord "a" "b" FullWords)
            , test "True if close enough" <|
                  \_ ->
                  Expect.equal True (checkWord "hello" "hellp" FullWords)
            , test "False if not close enough" <|
                  \_ ->
                  Expect.equal False (checkWord "hello" "shell" FullWords)
            , test "allows more mistakes for longer words" <|
                  \_ ->
                  Expect.equal True (checkWord "happenstance" "hapenstans" FullWords)
            ]
        ]
