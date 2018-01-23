module MemoryModelTests exposing (..)

import List
import Json.Decode as JD
import Expect exposing (Expectation)
import Fuzz
import Fuzz exposing (Fuzzer, int, list, string, float, floatRange, maybe)
import MemoryModel exposing (..)
import Native.TestData.MemoryModel
import String
import Test exposing (..)


strengthEstimateTestData : List (Maybe Float, Float, Maybe Float, Float)
strengthEstimateTestData =
    JD.decodeValue (JD.list (JD.list (JD.nullable JD.float))) Native.TestData.MemoryModel.strengthEstimateTestData
        |> \v -> case v of
                     Ok val ->
                         List.map (\item ->
                                       ( getAtUnsafe item 0
                                       , getAtUnsafe item 1
                                           |> (\mi -> case mi of
                                                         Nothing ->
                                                             Debug.crash "Item at index 1 must not be null"
                                                         Just i ->
                                                             i)
                                       , getAtUnsafe item 2
                                       , getAtUnsafe item 3
                                           |> (\mi -> case mi of
                                                         Nothing ->
                                                             Debug.crash "Item at index 3 must not be null"
                                                         Just i ->
                                                             i)
                                       )) val
                     Err msg ->
                         Debug.crash msg


getAtUnsafe : List a -> Int -> a
getAtUnsafe xs idx =
    List.drop idx xs
        |> List.head
        |> (\v -> case v of
                    Nothing ->
                        Debug.crash ("Missing item " ++ toString idx)
                    Just val ->
                        val)


aMemoryStrength : Fuzzer Float
aMemoryStrength =
    floatRange 0 bestStrength


aTestAccuracy : Fuzzer Float
aTestAccuracy =
    floatRange 0 1


anOldMemoryStrength : Fuzzer (Maybe Float)
anOldMemoryStrength =
    maybe aMemoryStrength


aTimeElapsed : Fuzzer (Maybe Float)
aTimeElapsed =
    Fuzz.map abs float |> maybe


epsilon : Float
epsilon =
    0.0000000001


almostEqual : Float -> Float -> Expectation
almostEqual x =
    Expect.within (Expect.Absolute epsilon) x


suite : Test
suite =
    describe "MemoryModel.elm"
        [ describe "strengthEstimate"
            ([ fuzz2 aMemoryStrength aTestAccuracy "zero time elapsed" <|
                \s a ->
                    strengthEstimate (Just s) a (Just 0)
                        |> Expect.atMost (s + epsilon)
             , fuzz3 anOldMemoryStrength aTestAccuracy aTimeElapsed "output range" <|
                \s a t ->
                    Expect.all
                        [ Expect.atLeast 0
                        , Expect.atMost bestStrength
                        ]
                        (strengthEstimate s a t)
             ]
                ++ List.map
                    (\( s, a, t, o ) ->
                        test ("output for " ++ toString s ++ ", " ++ toString a ++ ", " ++ toString t ++ " -> " ++ toString o)
                            (\_ ->
                                almostEqual o (strengthEstimate s a t)
                            )
                    )
                    strengthEstimateTestData
            )
        ]
