var _user$project$Native_Confirm = function () {
    var scheduler = _elm_lang$core$Native_Scheduler;

    function confirm_(prompt, successValue, failValue) {
        return scheduler.nativeBinding(function (callback) {
            if (window.confirm(prompt)) {
                callback(scheduler.succeed(successValue));
            } else {
                callback(scheduler.fail(failValue));
            }
        });
    };

    return {
        confirm: F3(confirm_),
    }
}()
