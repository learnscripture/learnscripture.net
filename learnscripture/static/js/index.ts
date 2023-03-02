/// <reference path="../typings/jquery-extra.d.ts" />


// node_modules libs

import "jquery-ui/ui/widgets/sortable";
import 'autosize';
import 'htmx.org';

// Ours

// We put javascript for (almost) all pages in the base template, with maximum
// expiry set up. This results in a bigger initial hit, but much better
// performance after that since the client only needs to ask for one js file (due
// to bundling) and never needs to request any js again.

import './common';
import './accordion';
import './accounts';
import './sound';
import './notices';
import './bible_book_info';
import './quickfind';
import './preferences';
import './choose';
import './create';
import './viewset';
import './dashboard';
import './versepopup';
import './groups';
import './comment';
import './sw_setup';
import './learn_setup';

// CSS/Less
import 'base.less';
