var path = require("path")
var webpack = require('webpack')
var ExtractTextPlugin = require("extract-text-webpack-plugin");


var elmSource = path.resolve(__dirname, './learnscripture/static/elm');

module.exports = {
    context: __dirname,

    entry: {
        base: './learnscripture/static/js/base.ts', // for base template
        learn: './learnscripture/static/js/learn_setup.js', // for learn page template
    },
    output: {
        path: path.resolve(__dirname, 'learnscripture/static/webpack_bundles'),
    },
    module: {
        noParse: /.elm$/,
        rules: [
            {
                test: /\.ts$/,
                use: 'ts-loader',
                exclude: /node_modules/
            },
            {
                test: require.resolve('jquery'),
                use: [{
                    loader: 'expose-loader',
                    options: 'jQuery'
                }]
            },
            {
                test: /\.elm$/,
                exclude: [/elm-stuff/, /node_modules/],
                use: {
                    loader: 'elm-webpack-loader',
                    options: {
                        cwd: elmSource,
                        verbose: true,
                        warn: true,
                        debug: false
                    }
                }
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
                        {
                            loader: "css-loader",
                            options: {
                                sourceMap: true
                            }
                        },
                        {
                            loader: "less-loader",
                            options: {
                                sourceMap: true
                            }
                        }
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
        extensions: ['.ts', '.js', '.elm'],
        modules: [
            "node_modules",
            path.resolve(__dirname, 'learnscripture/static/bootstrap/js'),
            path.resolve(__dirname, 'learnscripture/static/lib'),
            path.resolve(__dirname, 'learnscripture/static/js'),
            path.resolve(__dirname, 'learnscripture/static/css'),
        ],
        alias: {
            "jquery": "jquery/src/jquery",
            "cal-heatmap$": "cal-heatmap/cal-heatmap.js",
        }
    }
}
