const path = require("path")
var webpack = require('webpack')


const MiniCssExtractPlugin = require("mini-css-extract-plugin");
const BundleTracker = require('webpack-bundle-tracker')

var elmSource = path.resolve(__dirname, './learnscripture/static/elm');

module.exports = (env) => {
    var mode = env.mode
    if (mode != "development" && mode != "production" && mode != "tests") {
        throw new Error("mode must be passed using `--env mode=production|development|tests`")
    }
    var filenameSuffix = (mode == "development" ? "dev" : (mode == "tests" ? "tests" : "deploy"));

    return {
        mode: (mode == "tests" ? "development" : mode),
        context: __dirname,
        target: "web",
        entry: {
            main: './learnscripture/static/js/index',
            stats: './learnscripture/static/js/stats',
        },
        output: {
            path: path.resolve(__dirname, 'learnscripture/static/webpack_bundles'),
            filename: "[name]-[fullhash]." + filenameSuffix + ".js",
            chunkFilename: "[name]-[fullhash]" + filenameSuffix + ".js"
        },
        module: {
            noParse: /.elm$/,
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
                    test: /\.elm$/,
                    exclude: [/elm-stuff/, /node_modules/],
                    use: {
                        loader: 'elm-webpack-loader',
                        options: {
                            cwd: elmSource,
                            verbose: true,
                            warn: true,
                            debug: mode == "development"
                        }
                    }
                },
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
            }),
            new BundleTracker({filename: './webpack-stats.' + filenameSuffix + '.json'}),
        ],
    };
}
