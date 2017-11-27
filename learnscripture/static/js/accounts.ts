import { ajaxFailed } from './common';


interface AccountData {
    username: string;
    id: string;
}
var signedInAccountData: AccountData | null = null;

var setAccountData = function(accountData: AccountData | null) {
    if (accountData !== null) {
        signedInAccountData = accountData;
        $('#id-account-data').trigger('accountDataSet', accountData);
    }
};

export const getAccountData = function() {
    return signedInAccountData;
};

var doLogout = function(ev: JQuery.Event) {
    ev.preventDefault();
    if (confirm("Are you sure you want to log out?")) {
        $.ajax({
            url: '/api/learnscripture/v1/logout/?format=json',
            dataType: 'json',
            type: 'POST',
            success: function(data) {
                // Need to refresh page, unless page indicates differently
                if ($('#url-after-logout').length > 0) {
                    window.location.href = $('#url-after-logout').text();
                } else {
                    window.location.reload();
                }
            },
            error: ajaxFailed
        });
    }
};

var needsAccountButtonClick = function(ev: JQuery.Event) {
    var account = getAccountData();
    if (account === null || account.username === "") {
        // first get user to create an account
        ev.preventDefault();
        window.location.href = '/signup/?next=' + encodeURIComponent(window.location.pathname);
    }
};

var setupAccountControls = function() {

    $('.logout-link').click(doLogout);

    // Attach this class to buttons that require an account, but might be
    // presented when the user isn't logged in. This functionality is used
    // to streamline some entry points where it makes sense to invite people
    // to create accounts.
    $('.needs-account').click(needsAccountButtonClick);

};


$(document).ready(function() {
    setupAccountControls();
    if ($('#id-account-data').length > 0) {
        setAccountData($('#id-account-data').data() as AccountData);
    } else {
        setAccountData(null);
    }
});
