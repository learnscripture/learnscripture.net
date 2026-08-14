module LearnTests exposing (..)

import Dict
import Expect exposing (Expectation)
import Fuzz exposing (Fuzzer, int, list, string)
import Learn exposing (..)
import Test exposing (..)


suite : Test
suite =
    describe "Learn.elm"
        [ describe "stripOuterPunctuation"
            [ test "removes outer punctuation" <|
                \_ ->
                    Expect.equal "hello" (stripOuterPunctuation "—--“hello!”")
            , test "removes spanish outer punctuation" <|
                \_ ->
                    Expect.equal "hola" (stripOuterPunctuation "¡hola!")
            , test "removes leading plus" <|
                \_ ->
                    Expect.equal "Therefore" (stripOuterPunctuation "+‘Therefore")
            , test "doesn't remove inner punctuation" <|
                \_ ->
                    Expect.equal "some-thing" (stripOuterPunctuation "…some-thing?")
            , fuzz string "is idempotent" <|
                \s -> Expect.equal (stripOuterPunctuation s) (stripOuterPunctuation (stripOuterPunctuation s))
            ]
        , describe "normalizeWordForSuggestion"
            [ test "handles upper case accented characters" <|
                \_ ->
                    -- "Él" and "el" are different words, and may both be
                    -- present in the prompt_list. So it's important the
                    -- disctinction is preserved.
                    Expect.equal "él" (normalizeWordForSuggestion "Él")
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
        , describe "getTestResult"
            [ test "single item" <|
                \_ ->
                    Expect.equal 1.0
                        (getTestResult
                            (makeDummyTestProgress
                                [ { checkResults = [ Success ]
                                  , allowedMistakes = 0
                                  }
                                ]
                            )
                        )
            , test "single item 50%" <|
                \_ ->
                    Expect.equal 0.5
                        (getTestResult
                            (makeDummyTestProgress
                                [ { checkResults =
                                        [ Learn.Failure "foo"
                                        , Success
                                        ]
                                  , allowedMistakes = 1
                                  }
                                ]
                            )
                        )
            , test "single item fail" <|
                \_ ->
                    Expect.equal 0
                        (getTestResult
                            (makeDummyTestProgress
                                [ { checkResults =
                                        [ Learn.Failure "foo"
                                        , Learn.Failure "bar"
                                        ]
                                  , allowedMistakes = 1
                                  }
                                ]
                            )
                        )
            , test "three items overall 50%" <|
                \_ ->
                    Expect.equal 0.5
                        (getTestResult
                            (makeDummyTestProgress
                                [ { checkResults =
                                        [ Learn.Failure "foo"
                                        , Success
                                        ]
                                  , allowedMistakes = 1
                                  }
                                , { checkResults = [ Success ]
                                  , allowedMistakes = 1
                                  }
                                , { checkResults =
                                        [ Learn.Failure "foo"
                                        , Learn.Failure "bar"
                                        ]
                                  , allowedMistakes = 1
                                  }
                                ]
                            )
                        )
            ]
        , describe "referenceToParts"
            [ test "simple reference" <|
                \_ ->
                    Expect.equal
                        [ WordPart
                            { type_ = ReferenceWord
                            , index = 0
                            , text = "Mark"
                            }
                        , Space
                        , WordPart
                            { type_ = ReferenceWord
                            , index = 2
                            , text = "16"
                            }
                        , ReferencePunct ":"
                        , WordPart
                            { type_ = ReferenceWord
                            , index = 4
                            , text = "25"
                            }
                        ]
                        (referenceToParts "Mark 16:25")
            , test "numbered book name" <|
                \_ ->
                    Expect.equal
                        [ WordPart
                            { type_ = ReferenceWord
                            , index = 0
                            , text = "1"
                            }
                        , Space
                        , WordPart
                            { type_ = ReferenceWord
                            , index = 2
                            , text = "John"
                            }
                        , Space
                        , WordPart
                            { type_ = ReferenceWord
                            , index = 4
                            , text = "2"
                            }
                        , ReferencePunct ":"
                        , WordPart
                            { type_ = ReferenceWord
                            , index = 6
                            , text = "3"
                            }
                        ]
                        (referenceToParts "1 John 2:3")
            , test "verse range" <|
                \_ ->
                    Expect.equal
                        [ WordPart
                            { type_ = ReferenceWord
                            , index = 0
                            , text = "John"
                            }
                        , Space
                        , WordPart
                            { type_ = ReferenceWord
                            , index = 2
                            , text = "2"
                            }
                        , ReferencePunct ":"
                        , WordPart
                            { type_ = ReferenceWord
                            , index = 4
                            , text = "8"
                            }
                        , ReferencePunct "-"
                        , WordPart
                            { type_ = ReferenceWord
                            , index = 6
                            , text = "11"
                            }
                        ]
                        (referenceToParts "John 2:8-11")
            , test "Turkish 1" <|
                \_ ->
                    Expect.equal
                        [ WordPart
                            { type_ = ReferenceWord
                            , index = 0
                            , text = "Mısır'dan"
                            }
                        , Space
                        , WordPart
                            { type_ = ReferenceWord
                            , index = 2
                            , text = "Çıkış"
                            }
                        , Space
                        , WordPart
                            { type_ = ReferenceWord
                            , index = 4
                            , text = "1"
                            }
                        , ReferencePunct ":"
                        , WordPart
                            { type_ = ReferenceWord
                            , index = 6
                            , text = "2"
                            }
                        ]
                        (referenceToParts "Mısır'dan Çıkış 1:2")
            , test "Turkish 2" <|
                \_ ->
                    Expect.equal
                        [ WordPart
                            { type_ = ReferenceWord
                            , index = 0
                            , text = "1."
                            }
                        , Space
                        , WordPart
                            { type_ = ReferenceWord
                            , index = 2
                            , text = "Samuel"
                            }
                        , Space
                        , WordPart
                            { type_ = ReferenceWord
                            , index = 4
                            , text = "3"
                            }
                        , ReferencePunct ":"
                        , WordPart
                            { type_ = ReferenceWord
                            , index = 6
                            , text = "4"
                            }
                        ]
                        (referenceToParts "1. Samuel 3:4")
            ]
        ]


makeDummyTestProgress : List { c | allowedMistakes : Int, checkResults : List CheckResult } -> TestProgress
makeDummyTestProgress partial =
    { attemptRecords =
        List.map2
            (\{ checkResults, allowedMistakes } idx ->
                ( ( "BodyWord", idx )
                , { finished = True
                  , checkResults = checkResults
                  , allowedMistakes = allowedMistakes
                  }
                )
            )
            partial
            (List.range 0 (List.length partial))
            |> Dict.fromList
    , currentTypedText = ""
    , currentWord = dummyCurrentWord
    }


dummyCurrentWord : CurrentTestWord
dummyCurrentWord =
    CurrentWord
        { word =
            { type_ = BodyWord
            , index = 0
            , text = ""
            }
        , overallIndex = 0
        }
