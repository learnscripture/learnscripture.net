var webpack = require('webpack')
var BundleTracker = require('webpack-bundle-tracker')
var ExtractTextPlugin = require("extract-text-webpack-plugin");
const UglifyJsPlugin = require('uglifyjs-webpack-plugin')

var config = require('./webpack.config.base.js');

config.output.filename = "[name]-[hash].deploy.pack.js";

config.plugins = config.plugins.concat([
    new BundleTracker({filename: './webpack-stats.deploy.json'}),
    new ExtractTextPlugin("[name]-[hash].deploy.css"),
    new UglifyJsPlugin()
])

module.exports = config;
