var _ = require('underscore');
//models
var Event = require('./event');
//collections
var Collection = require('ampersand-collection');

module.exports = Collection.extend({
  model: Event,
  addEvent: function () {
    var id = this.parent.getDefaultID();
    var name = this.getDefaultName();
    var event = this.add({
      compID: id,
      name: name,
      annotation: "",
      delay: "",
      priority: "0",
      triggerExpression: "",
      initialValue: false,
      persistent: false,
      useValuesFromTriggerTime: false,
    });
    event.eventAssignments.addEventAssignment()
    return event
  },
  getDefaultName: function () {
    var i = this.length + 1;
    name = 'e' + i;
    var names = this.map(function (event) { return event.name; });
    while(_.contains(names, name)){
      i += 1;
      name = 'e' + i;
    }
    return name;
  },
  removeEvent: function (event) {
    this.remove(event);
  },
});