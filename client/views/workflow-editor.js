var _ = require('underscore');
var $ = require('jquery');
var tests = require('../views/tests');
//views
var View = require('ampersand-view');
var InputView = require('./input');
var SimSettingsView = require('./simulation-settings');
var ParamSweepSettingsView = require('./parameter-sweep-settings');
var WorkflowStateButtonsView = require('./workflow-state-buttons');
//models
var Model = require('../models/model');
//templates
var template = require('../templates/includes/workflowEditor.pug');

let modelNotFoundHtml = (title, message) => {
  return `
    <div id="duplicateWorkflowModal" class="modal" tabindex="-1" role="dialog">
      <div class="modal-dialog" role="document">
        <div class="modal-content info">
          <div class="modal-header">
            <h5 class="modal-title"> ${title} </h5>
            <button type="button" class="close" data-dismiss="modal" aria-label="Close">
              <span aria-hidden="true">&times;</span>
            </button>
          </div>
          <div class="modal-body">
            <p> ${message} </p>
            <p> Please correct the model path and press enter to reset the workflow. </p>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary box-shadow" data-dismiss="modal">Close</button>
          </div>
        </div>
      </div>
    </div>
  `
}

module.exports = View.extend({
  template: template,
  events: {
    'change [data-hook=model-name-container]' : 'updateWorkflowEditor',
  },
  initialize: function (attrs, options) {
    var self = this;
    $(document).on('hidden.bs.modal', function (e) {
      $(self.queryByHook("model-name-container")).find('input').focus();
    });
    View.prototype.initialize.apply(this, arguments);
    this.type = attrs.type;
    this.settingsViews = {};
    var directory = attrs.directory
    var modelFile = directory.split('/').pop();
    var name = modelFile.split('.')[0];
    var isSpatial = modelFile.split('.').pop().startsWith('s');
    this.model = new Model({
      name: name,
      directory: directory,
      is_spatial: isSpatial,
      isPreview: false,
      for: "wkfl",
    });
    this.model.fetch({
      json: true,
      success: function (model, response, options) {
        self.renderSubviews();
      },
      error: function (model, response, options) {
        self.modelNotFound(response.body)
      }
    });
  },
  update: function (e) {
  },
  updateValid: function (e) {
  },
  updateWorkflowEditor: function (e) {
    let self = this;
    this.model.fetch({
      json: true,
      success: function (model, response, options) {
        self.renderSubviews();
      },
      error: function (model, response, options) {
        self.modelNotFound(response.body)
      }
    });
  },
  renderSubviews: function() {
    this.renderModelPathInputView(false)
    //initialize the settings views and add it to the dictionary of settings views
    this.settingsViews.gillespy = new SimSettingsView({
      parent: this,
      model: this.model.simulationSettings,
    });
    this.settingsViews.parameterSweep = new ParamSweepSettingsView({
      parent: this,
      model: this.model.parameterSweepSettings,
    });
    var workflowStateButtons = new WorkflowStateButtonsView({
      model: this.model
    });
    this.registerRenderSubview(this.settingsViews['gillespy'], 'sim-settings-container');
    if(this.type === "parameterSweep"){
      var species = this.model.species;
      var parameters = this.model.parameters;
      var parameterOne = this.model.parameterSweepSettings.parameterOne
      var parameterTwo = this.model.parameterSweepSettings.parameterTwo
      var speciesOfInterest = this.model.parameterSweepSettings.speciesOfInterest
      var p1Exists = parameters.filter(function (param) { if(parameterOne.compID && parameterOne.compID === param.compID) return param}).length
      var p2Exists = parameters.filter(function (param) { if(parameterTwo.compID && parameterTwo.compID === param.compID) return param}).length
      var speciesOfInterestExists = species.filter(function (specie) { if(speciesOfInterest.compID && speciesOfInterest.compID === specie.compID) return species}).length
      if(!parameterOne.name || !p1Exists){
        this.model.parameterSweepSettings.parameterOne = parameters.at(0)
        var val = eval(this.model.parameterSweepSettings.parameterOne.expression)
        this.model.parameterSweepSettings.p1Min = val * 0.5
        this.model.parameterSweepSettings.p1Max = val * 1.5
      }
      if(parameters.at(1) && (!parameterTwo.name || !p2Exists)) {
        this.model.parameterSweepSettings.parameterTwo = parameters.at(1)
        var val = eval(this.model.parameterSweepSettings.parameterTwo.expression)
        this.model.parameterSweepSettings.p2Min = val * 0.5
        this.model.parameterSweepSettings.p2Max = val * 1.5
      }
      if(!this.model.parameterSweepSettings.speciesOfInterest.name || !speciesOfInterestExists){
        this.model.parameterSweepSettings.speciesOfInterest = species.at(0)
      }
      this.registerRenderSubview(this.settingsViews['parameterSweep'], 'param-sweep-settings-container');
    }
    this.registerRenderSubview(workflowStateButtons, 'workflow-state-buttons-container');
    this.parent.trajectories = this.model.simulationSettings.realizations
    this.parent.species = this.model.species
    this.parent.speciesOfInterest = this.model.parameterSweepSettings.speciesOfInterest
  },
  modelNotFound: function (error) {
    let title = error.Reason
    let message = error.Message
    console.log(title, message)
    let modal = $(modelNotFoundHtml(title, message)).modal()
    this.renderModelPathInputView(true)
    $(this.queryByHook("model-name-container")).find('input').prop('autofocus', true)
  },
  renderModelPathInputView: function (mdlNotFound) {
    if(this.modelPathInput){
      this.modelPathInput.remove()
    }
    this.modelPathInput = new InputView({
      parent: this,
      required: true,
      name: 'name',
      label: 'Model Path: ',
      tests: "",
      modelKey: 'directory',
      valueType: 'string',
      value: this.model.directory,
    });
    this.registerRenderSubview(this.modelPathInput, "model-name-container");
  },
  registerRenderSubview: function (view, hook) {
    this.registerSubview(view);
    this.renderSubview(view, this.queryByHook(hook));
  },
  collapseContainer: function () {
    $(this.queryByHook("workflow-editor-container")).collapse();
  },
});