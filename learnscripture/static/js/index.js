
// For initial migration, use 'script-loader' for everything,
// as we fix things we can move over to something better.

// Lib
import exec from 'script-loader!lib/jquery-1.7.1.min';
import exec from 'script-loader!lib/json2';
import exec from 'script-loader!lib/jquery-ui-1.8.17.custom.min.js';
import exec from 'script-loader!lib/jsrender';
import exec from 'script-loader!lib/jquery.ajaxretry';
import exec from 'script-loader!lib/jquery.ba-bbq.min';
import exec from 'script-loader!lib/jquery.actual.min';
import exec from 'script-loader!lib/jquery.autosize';
import exec from 'script-loader!lib/d3.v3.min';  // for dashboard
import exec from 'script-loader!lib/cal-heatmap.min';  // for dashboard

// Twitter Bootstrap
import exec from 'script-loader!bootstrap-dropdown';
import exec from 'script-loader!bootstrap-tabs';
import exec from 'script-loader!bootstrap-buttons';

// Ours
import exec from 'script-loader!accounts';
import exec from 'script-loader!common';
import exec from 'script-loader!sound';
import exec from 'script-loader!notices';
import exec from 'script-loader!bible_book_info';
import exec from 'script-loader!quickfind';
import exec from 'script-loader!learn';
import exec from 'script-loader!accounts';
import exec from 'script-loader!choose';
import exec from 'script-loader!create';
import exec from 'script-loader!preferences';
import exec from 'script-loader!viewset';
import exec from 'script-loader!dashboard';
import exec from 'script-loader!versepopup';
import exec from 'script-loader!groups';
import exec from 'script-loader!comment';
import exec from 'script-loader!follow';

