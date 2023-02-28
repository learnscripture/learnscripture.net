const path = require("path")
var webpack = require('webpack')
const MiniCssExtractPlugin = require("mini-css-extract-plugin");


// var elmSource = path.resolve(__dirname, './learnscripture/static/elm');


module.exports = {
    context: __dirname,
    target: "web",
    entry: './learnscripture/static/js/index',
    output: {
        path: path.resolve(__dirname, 'learnscripture/static/webpack_bundles'),
        filename: "[name]-[hash].js",
        chunkFilename: "[name]-[hash].js"
    },
    module: {
        rules: [
            {
                test: /\.tsx?$/,
                use: 'ts-loader',
                exclude: /node_modules/,
            },
            {
                test: /\.css$/i,
                use: [MiniCssExtractPlugin.loader, "css-loader"],
            },
            {
                test: /\.less$/i,
                use: [
                    {
                        loader: MiniCssExtractPlugin.loader,
                    },
                    {
                        loader: "css-loader",
                        options: {
                            url: false,  // Don't attempt to parse url() in CSS
                        }
                    },
                    {
                        loader: "less-loader",
                        options: {
                            sourceMap: true,
                        }
                    }
                ],
            },
            {
                // https://github.com/d3/d3/wiki#supported-environments

                // "If you are using a bundler, make sure your bundler is
                // configured to consume the modules entry point in the
                // package.json. See webpack’s resolve.mainFields, for example."

                test: require.resolve("d3"),
                resolve: {
                    mainFields: ['module']
                }
            },
            // {
            //     // Make $ and jQuery available everywhere, including at console
            //     test: require.resolve("jquery"),
            //     loader: "expose-loader",
            //     options: {
            //         exposes: ["$", "jQuery"],
            //     },
            // },
        ],
    },
    resolve: {
        extensions: ['.tsx', '.ts', '.js'],
        modules: [
            "node_modules",
            path.resolve(__dirname, 'learnscripture/static/lib'),
            path.resolve(__dirname, 'learnscripture/static/js'),
            path.resolve(__dirname, 'learnscripture/static/css'),
        ],
        alias: {
            "jquery": "jquery/src/jquery",
        }
    },
    plugins: [
        new MiniCssExtractPlugin({filename: '[name]-[hash].css',
                                  chunkFilename: "[name]-[hash].css"}),
        // This makes jQuery available to the various modules in our code that
        // use it, instead of importing it everywhere
        new webpack.ProvidePlugin({
            $: "jquery",
            jQuery: "jquery",
            "window.jQuery": "jquery",
            d3: "d3",
        })
        //     htmx: "htmx.org",
        // })
    ],

    // module: {
    //     noParse: /.elm$/,
    //     rules: [
    //         {
    //             test: /\.ts$/,
    //             use: 'ts-loader',
    //             exclude: /node_modules/
    //         },
    //         {
    //             test: require.resolve('jquery'),
    //             use: [{
    //                 loader: 'expose-loader',
    //                 options: 'jQuery'
    //             }]
    //         },
    //         {
    //             test: /\.elm$/,
    //             exclude: [/elm-stuff/, /node_modules/],
    //             use: {
    //                 loader: 'elm-webpack-loader',
    //                 options: {
    //                     cwd: elmSource,
    //                     verbose: true,
    //                     warn: true,
    //                     debug: false
    //                 }
    //             }
    //         },
    //         {
    //             test: /\.css$/,
    //             use: ExtractTextPlugin.extract({
    //                 fallback: "style-loader",
    //                 use: "css-loader"
    //             })
    //         },
    //         {
    //             test: /\.less$/,
    //             use: ExtractTextPlugin.extract({
    //                 fallback: "style-loader",
    //                 use: [
    //                     {
    //                         loader: "css-loader",
    //                         options: {
    //                             sourceMap: true
    //                         }
    //                     },
    //                     {
    //                         loader: "less-loader",
    //                         options: {
    //                             sourceMap: true
    //                         }
    //                     }
    //                 ]
    //             })
    //         }
    //     ]
    // },
    // resolve: {
    //     extensions: ['.ts', '.js', '.elm'],
    //     modules: [
    //         "node_modules",
    //         path.resolve(__dirname, 'learnscripture/static/lib'),
    //         path.resolve(__dirname, 'learnscripture/static/js'),
    //         path.resolve(__dirname, 'learnscripture/static/css'),
    //     ],
    //     alias: {
    //         "jquery": "jquery/src/jquery",
    //         "cal-heatmap$": "cal-heatmap/cal-heatmap.js",
    //     }
    // }
}
