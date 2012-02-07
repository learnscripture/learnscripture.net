
$(document).ready(function() {
    // Avoid loading this unless we need it
    var prefs = $('#id-preferences-data').data();
    if (prefs.theme == 'bubblegum') {
        $('head').append("<link href='http://fonts.googleapis.com/css?family=Short+Stack' rel='stylesheet' type='text/css'>");
    }
});
