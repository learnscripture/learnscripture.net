
export const storeSavedCalls = function(calls, userName) {
    if (window.localStorage !== undefined) {
        window.localStorage.setItem("learnscripture_Learn_savedCalls_" + userName, JSON.stringify(calls))
    }
}

export const getSavedCalls = function(userName) {
    var savedCalls = [];
    if (window.localStorage !== undefined) {
        var savedCallsJSON = window.localStorage.getItem("learnscripture_Learn_savedCalls_" + userName);
        if (!savedCallsJSON) {
            savedCallsJSON = window.localStorage.getItem("learnscripture_Learn_savedCalls"); // compat
        }
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
