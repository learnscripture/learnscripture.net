var path = require("path")
var webpack = require('webpack')
var ExtractTextPlugin = require("extract-text-webpack-plugin");


module.exports = {
    context: __dirname,

    entry: {
        base: './learnscripture/static/js/base', // for base template
    },
    output: {
        path: path.resolve(__dirname, 'learnscripture/static/webpack_bundles'),
    },
    module: {
        rules: [
            {
                test: require.resolve('jquery'),
                use: [{
                    loader: 'expose-loader',
                    options: 'jQuery'
                }]
            },
            {
                test: /\.css$/,
                use: ExtractTextPlugin.extract({
                    fallback: "style-loader",
                    use: "css-loader"
                })
            },
            {
                test: /\.less$/,
                use: ExtractTextPlugin.extract({
                    fallback: "style-loader",
                    use: [
                        "css-loader",
                        "less-loader",
                    ]
                })
            }
        ]
    },
    plugins: [
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
