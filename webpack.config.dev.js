var BundleTracker = require('webpack-bundle-tracker')
var ExtractTextPlugin = require("extract-text-webpack-plugin");

var config = require('./webpack.config.base.js');

config.output.filename = "[name]-[hash].dev.pack.js";

config.plugins = config.plugins.concat([
    new BundleTracker({filename: './webpack-stats.dev.json'}),
    new ExtractTextPlugin("[name]-[hash].dev.css"),
])

config.devtool = 'source-map';

module.exports = config;
