var $ = require('jquery');
var bootstrap = require('bootstrap');
var _ = require('underscore');
var domReady = require('domready');
var Router = require('./router');
var app = require('ampersand-app');
var config = require('./config.js')(process.env.NODE_ENV);
app.config = config;
window.app = app;

import styles from './styles/styles.css';
import bootstrapStyles from './styles/bootstrap.css';

// Models
var Models = require('./models/models');
var Me = require('./models/me');
// Page container view
var MainView = require('./views/main');

app.extend({
  models: new Models(),
  router: new Router(),
  me: new Me(),
  
  init: function () {
    var self = this;
    this.me.fetch({
      success: function (model, response, options) {
        self.models.fetch();
        self.models.fetch();
        self.mainView = new MainView({
          el: document.body 
        });
        self.router.history.start({ pushState: true, root: '/hub/stochss' });
      },
      error: function (model, response, options) {
        alert("Fatal error: unable to retrieve username from API");
      }
    });
  },

  // This is a helper for navigating around the app.
  // this gets called by a global click handler that handles
  // all the <a> tags in the app.
  // it expects a url pathname for example: "/costello/settings"
  navigate: function (page) {
    var url = (page.charAt(0) == '/') ? page.slice(1) : page;
    this.router.history.navigate(url, {
      trigger: true
    });
  }
});

domReady(_.bind(app.init, app));