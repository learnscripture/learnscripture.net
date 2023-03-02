const path = require("path")
var webpack = require('webpack')


const MiniCssExtractPlugin = require("mini-css-extract-plugin");
const BundleTracker = require('webpack-bundle-tracker')

// var elmSource = path.resolve(__dirname, './learnscripture/static/elm');

module.exports = (env) => {
    var mode = env.mode;
    if (mode != "development" && mode != "production") {
        throw new Error("mode must be passed using `--env mode=production` or `--env mode=development`")
    }
    var filenameSuffix = (mode == "development" ? "dev" : "deploy");

    return {
        mode: mode,
        context: __dirname,
        target: "web",
        entry: './learnscripture/static/js/index',
        output: {
            path: path.resolve(__dirname, 'learnscripture/static/webpack_bundles'),
            filename: "[name]-[fullhash]." + filenameSuffix + ".js",
            chunkFilename: "[name]-[fullhash]" + filenameSuffix + ".js"
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
            new MiniCssExtractPlugin({
                filename: '[name]-[fullhash].' + filenameSuffix + '.css',
                chunkFilename: "[name]-[fullhash].' + filenameSuffix + '.css",
            }),
            // This makes jQuery available to the various modules in our code that
            // use it, instead of importing it everywhere
            new webpack.ProvidePlugin({
                $: "jquery",
                jQuery: "jquery",
                "window.jQuery": "jquery",
                d3: "d3",
            }),
            //     htmx: "htmx.org",
            // })
            new BundleTracker({filename: './webpack-stats.' + filenameSuffix + '.json'}),
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
        //     ]
        // },
        // resolve: {
        //     alias: {
        //         "jquery": "jquery/src/jquery",
        //         "cal-heatmap$": "cal-heatmap/cal-heatmap.js",
        //     }
        // }
    };
}
