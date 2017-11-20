
// For initial migration, use 'script-loader' for everything,
// as we fix things we can move over to something better.

// Lib
require('script-loader!lib/jquery-1.7.1.min');
require('script-loader!lib/jquery-ui-1.8.17.custom.min.js');
require('script-loader!lib/jsrender');
require('script-loader!lib/jquery.ajaxretry');
require('script-loader!lib/jquery.ba-bbq.min');
require('script-loader!lib/jquery.actual.min');
require('script-loader!lib/jquery.autosize');
require('script-loader!lib/d3.v3.min');  // for dashboard
require('script-loader!lib/cal-heatmap.min');  // for dashboard

// Twitter Bootstrap
require('script-loader!bootstrap-dropdown');
require('script-loader!bootstrap-tabs');
require('script-loader!bootstrap-buttons');

// Ours
require('script-loader!accounts');
require('script-loader!common');
require('script-loader!sound');
require('script-loader!notices');
require('script-loader!bible_book_info');
require('script-loader!quickfind');
require('script-loader!learn');
require('script-loader!accounts');
require('script-loader!choose');
require('script-loader!create');
require('script-loader!preferences');
require('script-loader!viewset');
require('script-loader!dashboard');
require('script-loader!versepopup');
require('script-loader!groups');
require('script-loader!comment');
require('script-loader!follow');

