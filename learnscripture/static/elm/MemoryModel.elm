module MemoryModel exposing (alpha, bestStrength, deltaSIdeal, exponent, initialStrengthFactor, learned, minTimeBetweenTests, nextTestDueAfter, oneYear, strength, strengthEstimate, time, verseTests)

-- See Python code accounts.memorymodel, and sync all changes
-- Note that Python code works in seconds, and so does this.


strength : Float -> Float
strength t =
    1.0 - (e ^ (-1 * alpha * (t ^ exponent)))


time : Float -> Float
time s =
    ((-1 * logBase e (1.0 - s)) / alpha) ^ (1.0 / exponent)


verseTests : number
verseTests =
    20


learned : Float
learned =
    0.8


bestStrength : Float
bestStrength =
    0.999


initialStrengthFactor : Float
initialStrengthFactor =
    deltaSIdeal


oneYear : Float
oneYear =
    365 * 24 * 3600 * 1.0


alpha : Float
alpha =
    -1.0 * logBase e (1.0 - learned) / (oneYear ^ exponent)


deltaSIdeal : Float
deltaSIdeal =
    learned / verseTests


{-| Calculates a strength estimate,
given the previous strength, the test accuracy, and the time
elapsed in _seconds_
-}
strengthEstimate : Float -> Float -> Maybe Float -> Float
strengthEstimate oldStrength testAccuracy timeElapsedM =
    let
        testStrength =
            testAccuracy ^ 2.0

        initialStrengthEstimate =
            initialStrengthFactor * testStrength
    in
    case timeElapsedM of
        Nothing ->
            initialStrengthEstimate

        Just timeElapsed ->
            if testStrength < oldStrength then
                testStrength

            else if oldStrength == 1.0 then
                bestStrength

            else
                let
                    s1 =
                        oldStrength

                    t1 =
                        time s1

                    t2 =
                        t1 + timeElapsed

                    s2 =
                        strength t2

                    deltaSmax =
                        min (s2 - s1) deltaSIdeal

                    deltaSactual =
                        deltaSmax * (testStrength - oldStrength) / (1.0 - oldStrength)

                    newStrength =
                        oldStrength + deltaSactual
                in
                min bestStrength newStrength


minTimeBetweenTests : number
minTimeBetweenTests =
    3600



{- Time delay in *seconds* from the test to the next test due -}


nextTestDueAfter : Float -> Float
nextTestDueAfter strength =
    let
        t0 =
            time strength

        t1 =
            time (min (strength + deltaSIdeal) bestStrength)
    in
    max (t1 - t0) minTimeBetweenTests


exponent : Float
exponent =
    0.25
