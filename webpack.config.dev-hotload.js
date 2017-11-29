var path = require("path")
var webpack = require('webpack')

var config = require('./webpack.config.dev.js');

Object.keys(config.entry).forEach(function(key) {
    var path = config.entry[key];
    config.entry[key] = [
        'webpack-dev-server/client?http://learnscripture.local:8080',
        'webpack/hot/only-dev-server',
        path
    ];
});

config.output.publicPath = 'http://learnscripture.local:8080/static/webpack_bundles/';

config.plugins = config.plugins.concat([
    new webpack.HotModuleReplacementPlugin(),
    new webpack.NoEmitOnErrorsPlugin()
]);

config.devServer = {
    headers: {
        "Access-Control-Allow-Origin": "*"
    },
    historyApiFallback: true,
    hot: true,
    host: "learnscripture.local",
    port: 8080,
    allowedHosts: [
        'learnscripture.local',
        'localhost'
    ]
};

module.exports = config;
