const path = require('path');
const HtmlWebpackPlugin = require('html-webpack-plugin');

module.exports = {
  mode: 'development',
  entry: {
    home: './client/pages/home.js',
    browser: './client/pages/file-browser.js',
    editor: './client/pages/model-editor.js',
    workflowSelection: './client/pages/workflow-selection.js',
    workflowEditor: './client/pages/workflow-manager.js',
  },
  output: {
    filename: '[name].bundle.js',
    path: path.resolve(__dirname, "dist")
  },
  devtool: 'inline-source-map',
  plugins: [
    new HtmlWebpackPlugin({
      title: 'StochSS | Home',
      filename: 'stochss-home.html',
      template: 'handlers/page_templates/page_template.pug',
      name: 'home',
      inject: false
    }),
    new HtmlWebpackPlugin({
      title: 'StochSS | Model Browser',
      filename: 'stochss-file-browser.html',
      template: 'handlers/page_templates/page_template.pug',
      name: 'browser',
      inject: false
    }),
    new HtmlWebpackPlugin({
      title: 'StochSS | Model Editor',
      filename: 'stochss-model-editor.html',
      template: 'handlers/page_templates/page_template.pug',
      name: 'editor',
      inject: false
    }),
    new HtmlWebpackPlugin({
      title: 'StochSS | Workflow Selection',
      filename: 'stochss-workflow-selection.html',
      template: 'handlers/page_templates/page_template.pug',
      name: 'workflowSelection',
      inject: false
    }),
    new HtmlWebpackPlugin({
      title: 'StochSS | Workflow Editor',
      filename: 'stochss-workflow-manager.html',
      template: 'handlers/page_templates/page_template.pug',
      name: 'workflowEditor',
      inject: false
    }),
  ],
  optimization: {
    splitChunks: {
      cacheGroups: {
        commons: {
          name: 'common',
          chunks: 'initial',
          minChunks: 2
        }
      }
    }
  },
  module: {
    rules: [
      {
        test: /\.pug$/,
        use: [ 'pug-loader' ]
      },
      {
        test: /\.css$/,
        use: [
          'style-loader',
          'css-loader'
        ]
      },
      {
        test: /\.(png|svg|jpg|gif)$/,
        use: [
          'file-loader' 
        ]
      }
    ]
  }
}
