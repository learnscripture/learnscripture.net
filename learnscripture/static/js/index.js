
// node_modules libs
require('expose-loader?jQuery!jquery');
require("jquery-ui/ui/widgets/sortable");
require('jsrender');
require('autosize');

// bundled libs
require('lib/jquery.ajaxretry');
require('bootstrap-dropdown');
require('bootstrap-tabs');
require('bootstrap-buttons');

// Ours

// We put javascript for (almost) all pages in the base template, with maximum
// expiry set up. This results in a bigger initial hit, but much better
// performace after that since the client only needs to ask for one js file (due
// to bundling) and never needs to request any js again.

require('common');
require('accounts');
require('sound');
require('notices');
require('bible_book_info');
require('quickfind');
require('learn');
require('preferences');
require('choose');
require('create');
require('viewset');
require('dashboard');
require('versepopup');
require('groups');
require('comment');
require('follow');

// CSS/Less
require('learnscripture.less');
