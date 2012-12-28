/*jslint browser: true, vars: true */
/*globals $ */
var learnscripture = (function (learnscripture, $) {
    "use strict";
    var signedInAccountData = null;

    var setAccountData = function (accountData) {
        signedInAccountData = accountData;

        $('#id-account-data').trigger('accountDataSet', accountData);
    };

    var getAccountData = function () {
        return signedInAccountData;
    };

    var doLogout = function (ev) {
        ev.preventDefault();
        if (confirm("Are you sure you want to log out?")) {
            $.ajax({url: '/api/learnscripture/v1/logout/?format=json',
                    dataType: 'json',
                    type: 'POST',
                    success: function (data) {
                        // Need to refresh page, unless page indicates differently
                        if ($('#url-after-logout').length > 0) {
                            window.location = $('#url-after-logout').text();
                        } else {
                            window.location.reload();
                        }
                    },
                    error: learnscripture.ajaxFailed
                   });
        }
    };

    var needsAccountButtonClick = function (ev) {
        var account = getAccountData();
        if (account === null || account.username === "") {
            // first get user to create an account
            ev.preventDefault();
            window.location = '/signup/?next=' + encodeURIComponent(window.location.pathname);
        }
    };

    var setupAccountControls = function (ev) {

        $('.logout-link').click(doLogout);

        // Attach this class to buttons that require an account, but might be
        // presented when the user isn't logged in. This functionality is used
        // to streamline some entry points where it makes sense to invite people
        // to create accounts.
        $('.needs-account').click(needsAccountButtonClick);

    };

    // Export:
    learnscripture.setupAccountControls = setupAccountControls;
    learnscripture.setAccountData = setAccountData;
    learnscripture.getAccountData = getAccountData;
    return learnscripture;
}(learnscripture || {}, $));

$(document).ready(function () {
    learnscripture.setupAccountControls();
    if ($('#id-account-data').length > 0) {
        learnscripture.setAccountData($('#id-account-data').data());
    } else {
        learnscripture.setAccountData(null);
    }
});
