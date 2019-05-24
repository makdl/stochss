var View = require('ampersand-view');
var _ = require('underscore');

var template = require('../templates/includes/modelListing.pug');

module.exports = View.extend({
  template: template,
  initialize: function () {
    this.model.version_open_tag = this.model.latest_version;
  },
  events: {
    "change [data-hook='version-select']": "selectVersion"
  },
  bindings: {
    'model.name' : '[data-hook~=name]',
    'model.public' : {
      type: function (el, value, previousValue) {
        var text = value ? 'Yes' : 'No';
        el.innerHTML = text;
      },
      hook: 'public',
    },
    'model.id' : {
      type: function (el, value, previousValue) {
        el.href = '/models/edit/' + value
      },
      hook: 'edit-link',
    },
    'model.version_open_tag': {
      type: function (el, value, previousValue) {
        el.value = String(value);
        var options = this.queryAll('option');
        var self = this;
        options.forEach(function(option) {
          option.selected = parseInt(option.value) === value;
        });
      },
      hook: 'version-select'
    }
  },
  selectVersion: function (e) {
    this.model.version_open_tag = parseInt(e.target.value);
  }

});