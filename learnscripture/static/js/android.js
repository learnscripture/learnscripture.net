$(document).ready(function () {
    "use strict";
    var CURRENT_ANDROID_APP_VERSION = 13;
    if (window.androidlearnscripture) {

        $('.page-header').after(
            '<div class="message-container"><div class="notice">This Android app is no longer supported. Please go to <a href="http://bit.do/learnscripture">learnscripture.net</a> in a normal browser (e.g. Firefox or Chrome) and log in for the best experience.</div></div>'
        );

        if (window.androidlearnscripture.showMenu) {
            $('.android-appmenu-link').on('click', function (ev) {
                ev.preventDefault();
                window.androidlearnscripture.showMenu();
            });
            $('.android-appmenu-link').closest('li').attr('style', '').show();
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
