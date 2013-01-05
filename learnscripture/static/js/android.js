$(document).ready(function () {
    "use strict";
    var CURRENT_ANDROID_APP_VERSION = 11;
    if (window.androidlearnscripture &&
        (window.androidlearnscripture.getVersionCode == undefined ||
         window.androidlearnscripture.getVersionCode() < CURRENT_ANDROID_APP_VERSION)) {
        $('.page-header').after(
            '<div class="message-container"><div class="notice">Please <a href="https://play.google.com/store/apps/details?id=net.learnscripture.webviewapp">upgrade</a> to the most recent version of the Android app for the best experience.</div></div>'
        );
    }
});
