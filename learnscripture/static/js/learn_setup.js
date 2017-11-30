// node_modules libs

//import 'expose-loader?jQuery!jquery';


// CSS/Less
import 'learn.less';

import Elm from "../elm/Learn";
Elm.Main.embed(document.getElementById('elm-main'));
