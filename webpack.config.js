var path = require("path")
var webpack = require('webpack')
var BundleTracker = require('webpack-bundle-tracker')

module.exports = {
    context: __dirname,

    entry: {
        base: './learnscripture/static/js/base', // for base template
    },
    output: {
        path: path.resolve(__dirname, 'learnscripture/static/webpack_bundles'),
        filename: "[name]-[hash].js"
    },
    module: {
        rules: [
            {
                test: /\.css$/,
                use: [
                    'style-loader',
                    'css-loader'
                ]
            },
            {
                test: /\.less$/,
                use: [
                    'style-loader',
                    'css-loader',
                    'less-loader'
                ]
            }
        ]
    },
    plugins: [
        new BundleTracker({filename: './webpack-stats.json'}),
        new webpack.ProvidePlugin({
            $: "jquery",
            jQuery: "jquery",
            "window.jQuery": "jquery",
        })
    ],
    resolve: {
        modules: [
            "node_modules",
            path.resolve(__dirname, 'learnscripture/static/bootstrap/js'),
            path.resolve(__dirname, 'learnscripture/static/js'),
            path.resolve(__dirname, 'learnscripture/static/css'),
        ],
        alias: {
            "jquery": "jquery/src/jquery",
        }
    }
}
