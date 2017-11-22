
// For initial migration, use 'script-loader' for everything,
// as we fix things we can move over to something better.

// node_modules lib
require('expose-loader?jQuery!jquery');
require("jquery-ui/ui/widgets/sortable");
require('jsrender');
require('autosize');

// bundled libs
require('lib/jquery.ajaxretry');
require('script-loader!lib/d3.v3.min');  // for dashboard
require('script-loader!lib/cal-heatmap.min');  // for dashboard
require('bootstrap-dropdown');
require('bootstrap-tabs');
require('bootstrap-buttons');

// Ours
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

