$(document).ready(function () {
    "use strict";
    var CURRENT_ANDROID_APP_VERSION = 10;
    if (window.androidlearnscripture) {
        if (window.androidlearnscripture.getVersionCode == undefined ||
            window.androidlearnscripture.getVersionCode() < CURRENT_ANDROID_APP_VERSION) {
            $('.page-header').after(
                '<div class="message-container"><div class="notice">Please <a href="https://play.google.com/store/apps/details?id=net.learnscripture.webviewapp">upgrade</a> to the most recent version of the Android app for the best experience.</div></div>'
            );
        }

        var receiveAccountData = function (accountData) {
            if (accountData && !accountData.hasInstalledAndroidApp) {
                // According to recorded data, the user hasn't installed the Android
                // app. But they have now, or we wouldn't have reached this code.
                // So we update.
                $.ajax({url: '/api/learnscripture/v1/androidappinstalled/?format=json',
                        dataType: 'json',
                        type: 'POST',
                        data: {},
                       });
            }
        };

        receiveAccountData(learnscripture.getAccountData());
        $('#id-account-data').bind('accountDataSet', function (ev, accountData) {
            receiveAccountData(accountData);
        });

        if (window.androidlearnscripture.setUrlForSharing) {
            var rl = $("#id_referral_link");
            var url;
            if (rl.length > 0) {
                url = rl.attr('href');
                if (!url.match(/^http/)) {
                    url = window.location.protocol + "//" + window.location.hostname + "/" + url;
                }
                window.androidlearnscripture.setUrlForSharing(url);
            }
        }
    }
});
