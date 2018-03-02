
export const storeSavedCalls = function(calls) {
    if (window.localStorage !== undefined) {
        window.localStorage.setItem("learnscripture_Learn_savedCalls", JSON.stringify(calls))
    }
}

export const getSavedCalls = function() {
    var savedCalls = [];
    if (window.localStorage !== undefined) {
        var savedCallsJSON = window.localStorage.getItem("learnscripture_Learn_savedCalls");
        if (!savedCallsJSON) {
            savedCalls = [];
        } else {
            try {
                savedCalls = JSON.parse(savedCallsJSON);
            } catch (e) {
                savedCalls = [];
            }
        }
    }
    return savedCalls;
}
