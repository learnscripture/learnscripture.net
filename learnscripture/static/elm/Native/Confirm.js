var _user$project$Native_Confirm = function () {
    var scheduler = _elm_lang$core$Native_Scheduler;

    function confirmTask(prompt, successValue, failValue) {
        return scheduler.nativeBinding(function (callback) {
            if (window.confirm(prompt)) {
                callback(scheduler.succeed(successValue));
            } else {
                callback(scheduler.fail(failValue));
            }
        });
    };

    return {
        confirmTask: F3(confirmTask),
    }
}()
