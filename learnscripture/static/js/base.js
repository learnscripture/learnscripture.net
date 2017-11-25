
// node_modules libs

// this seems to be the only way to get select2 lib to see window.jQuery,
// configuring in webpack.config does not seem to work.
import 'expose-loader?jQuery!jquery';
import "jquery-ui/ui/widgets/sortable";
import 'jsrender';
import 'autosize';

// bundled libs
import 'lib/jquery.ajaxretry';
import 'bootstrap-dropdown';
import 'bootstrap-tabs';
import 'bootstrap-buttons';

// Ours

// We put javascript for (almost) all pages in the base template, with maximum
// expiry set up. This results in a bigger initial hit, but much better
// performace after that since the client only needs to ask for one js file (due
// to bundling) and never needs to request any js again.

import './common';
import './accounts';
import './sound';
import './notices';
import './bible_book_info';
import './quickfind';
import './learn';
import './preferences';
import './choose';
import './create';
import './viewset';
import './dashboard';
import './versepopup';
import './groups';
import './comment';
import './follow';

// CSS/Less
import 'learnscripture.less';
