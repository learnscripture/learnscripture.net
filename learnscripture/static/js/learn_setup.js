// node_modules libs

//import 'expose-loader?jQuery!jquery';


// CSS/Less
import 'learnscripture.less';

import Elm from "../elm/Main";
Elm.Main.embed(document.getElementById('elm-main'));
