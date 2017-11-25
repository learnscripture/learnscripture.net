var BundleTracker = require('webpack-bundle-tracker')

var config = require('./webpack.config.base.js');

config.output.filename = "[name]-[hash].tests.js";

config.plugins = config.plugins.concat([
    new BundleTracker({filename: './webpack-stats.tests.json'})
])

module.exports = config;
