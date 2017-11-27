var BundleTracker = require('webpack-bundle-tracker')
var ExtractTextPlugin = require("extract-text-webpack-plugin");

var config = require('./webpack.config.base.js');

config.output.filename = "[name]-[hash].tests.pack.js";

config.plugins = config.plugins.concat([
    new BundleTracker({filename: './webpack-stats.tests.json'}),
    new ExtractTextPlugin("[name]-[hash].tests.css"),
])

module.exports = config;
