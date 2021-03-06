#!/usr/bin/env python3

import os
import sys
import json
import argparse
import logging
import pickle
import plotly

from io import StringIO
from gillespy2.core import log
log_stream = StringIO()
for handler in log.handlers:
    if type(handler) is logging.StreamHandler:
        handler.stream = log_stream


from gillespy2 import Species, Parameter, Reaction, RateRule, Model, AssignmentRule, FunctionDefinition

import numpy
import gillespy2.core.gillespySolver
from gillespy2.core.events import EventAssignment, EventTrigger, Event
from gillespy2.core.gillespyError import ModelError, SolverError, DirectoryError, BuildError, ExecutionError
from gillespy2.solvers.numpy.basic_tau_leaping_solver import BasicTauLeapingSolver
from gillespy2.solvers.numpy.basic_tau_hybrid_solver import BasicTauHybridSolver
from gillespy2.solvers.cpp.variable_ssa_c_solver import VariableSSACSolver

import warnings
warnings.simplefilter("ignore")


user_dir = '/home/jovyan'


class GillesPy2Workflow():

    def __init__(self, wkfl_path, mdl_path, settings=None):
        self.wkfl_path = wkfl_path
        self.mdl_path = mdl_path
        if wkfl_path:
            self.settings = self.get_settings() if settings is None else settings
            self.mdl_file = mdl_path.split('/').pop()
            self.info_path = os.path.join(wkfl_path, 'info.json')
            self.log_path = os.path.join(wkfl_path, 'logs.txt')
            self.wkfl_mdl_path = os.path.join(wkfl_path, self.mdl_file)
            self.res_path = os.path.join(wkfl_path, 'results')
            wkfl_name_elements = wkfl_path.split('/').pop().split('.')[0].split('_')
            try:
                date, time = wkfl_name_elements[-2:]
                if date.isdigit() and time.isdigit():
                    self.wkfl_timestamp = '_'.join(["",date,time])
                else:
                    self.wkfl_timestamp = None
            except:
                self.wkfl_timestamp = None


    def get_settings(self):
        settings_path = os.path.join(self.wkfl_path, "settings.json")

        if os.path.exists(settings_path):
            with open(settings_path, "r") as settings_file:
                return json.load(settings_file)

        with open("/stochss/stochss_templates/workflowSettingsTemplate.json", "r") as template_file:
            settings_template = json.load(template_file)
        
        if os.path.exists(self.wkfl_mdl_path):
            with open(self.wkfl_mdl_path, "r") as mdl_file:
                mdl = json.load(mdl_file)
                try:
                    settings = {"simulationSettings":mdl['simulationSettings'],
                                "parameterSweepSettings":mdl['parameterSweepSettings'],
                                "resultsSettings":settings_template['resultsSettings']}
                    return settings
                except:
                    return settings_template
        else:
            return settings_template


    def save(self):
        settings_path = os.path.join(self.wkfl_path, "settings.json")
        with open(settings_path, "w") as settings_file:
            json.dump(self.settings, settings_file)


    def run_preview(self, gillespy2_model, stochss_model):
        with open("/stochss/stochss_templates/workflowSettingsTemplate.json", "r") as template_file:
            sim_settings = json.load(template_file)['simulationSettings']

        _results = run_solver(gillespy2_model, sim_settings, 5)
        results = _results[0]
        res_dict = dict(results)
        for k, v in res_dict.items():
            res_dict[k] = list(v)
        results = res_dict
        for key in results.keys():
            if not isinstance(results[key], list):
                # Assume it's an ndarray, use tolist()
                results[key] = results[key].tolist()
        results['data'] = stochss_model
        return results


    def run(self, gillespy2_model, verbose):
        sim_settings = self.settings['simulationSettings']
        trajectories = sim_settings['realizations']
        is_stochastic = not sim_settings['algorithm'] == "ODE"

        results = run_solver(gillespy2_model, sim_settings, 0)
        self.store_results(results)
        self.plot_results(results, trajectories, is_stochastic)


    def store_results(self, results):
        if not 'results' in os.listdir(path=self.wkfl_path):
            os.mkdir(self.res_path)
        # with open(os.path.join(self.res_path, 'results.p'), 'wb') as results_file:
        #     pickle.dump(results, results_file, protocol=pickle.HIGHEST_PROTOCOL)

        results.to_csv(path=self.res_path, nametag="results_csv", stamp=self.wkfl_timestamp)
        

    def plot_results(self, results, trajectories, is_stochastic):
        '''
        Create the set of result plots and write them to file in the results directory.

        Attributes
        ----------
        results : GillesPy2 ResultsEnsemble or GillesPy2 Results
            Results of a workflow run.
        results_path : str
            Path to the results directory.
        trajectories : int
            Number of trajectories for the workflow.
        is_stochastic : bool
            Was the workflow a stochastic simulation?.
        '''
        plots = {}
        
        if is_stochastic and trajectories > 1:
            stddevrange_plot = results.plotplotly_std_dev_range(return_plotly_figure=True)
            stddevrange_plot["config"] = {"responsive": True,}
            plots['stddevran'] = stddevrange_plot

            stddev_plot = results.stddev_ensemble().plotplotly(return_plotly_figure=True)
            stddev_plot["config"] = {"responsive": True,}
            plots['stddev'] = stddev_plot

            avg_plot = results.average_ensemble().plotplotly(return_plotly_figure=True)
            avg_plot["config"] = {"responsive": True,}
            plots['avg'] = avg_plot

        plot = results.plotplotly(return_plotly_figure=True)
        plot["config"] = {"responsive": True,}
        plots['trajectories'] = plot

        with open(os.path.join(self.res_path, 'plots.json'), 'w') as plots_file:
            json.dump(plots, plots_file, cls=plotly.utils.PlotlyJSONEncoder)


class _Model(Model):
    '''
    ##############################################################################
    Build a GillesPy2 model.
    ##############################################################################
    '''
    def __init__(self, name, species, parameters, reactions, events, rate_rules, 
                    assignment_rules, function_definitions, endSim, timeStep, volume):
        '''
        Initialize and empty model and add its components.

        Attributes
        ----------
        name : str
            Name of the model.
        species : list
            List of GillesPy2 species to be added to the model.
        parameters : list
            List of GillesPy2 parameters to be added to the model.
        reactions : list
            List of GillesPy2 reactions to be added to the model.
        events : list
            List of GillesPy2 events to be added to the model.
        rate_rules : list
            List of GillesPy2 rate rules to be added to the model.
        assignment_rules : list
            List of GillesPy2 assignment rules to be added to the model.
        function_definitions : list
            List of GillesPy2 function definitions to be added to the model.
        endSim : int
            Simulation duration of the model.
        timeStep : int
            Time unit until next sample.
        volume : int
            The volume of the system matters when converting to from population to
            concentration form. This will also set a parameter "vol" for use in
            custom (i.e. non-mass-action) propensity functions.
        '''
        Model.__init__(self, name=name, volume=volume)
        self.add_parameter(parameters)
        self.add_species(species)
        self.add_reaction(reactions)
        self.add_event(events)
        self.add_rate_rule(rate_rules)
        self.add_assignment_rule(assignment_rules)
        self.add_function_definition(function_definitions)
        numSteps = int(endSim / timeStep + 1)
        self.timespan(numpy.linspace(0,endSim,numSteps))


class ModelFactory():
    '''
    ##############################################################################
    Build the individual components of a model.
    ##############################################################################
    '''
    def __init__(self, data, is_ode):
        '''
        Initialize and build a GillesPy2 model.

        Attributes
        ----------
        data : dict
            A json representation of a model.
        '''
        
        name = data['name']
        timeStep = (data['modelSettings']['timeStep'])
        endSim = data['modelSettings']['endSim']
        volume = data['modelSettings']['volume']
        self.species = list(map(lambda s: self.build_specie(s, is_ode), data['species']))
        self.parameters = list(map(lambda p: self.build_parameter(p), data['parameters']))
        self.reactions = list(map(lambda r: self.build_reaction(r, self.parameters), data['reactions']))
        self.events = list(map(lambda e: self.build_event(e, self.species, self.parameters), data['eventsCollection']))
        rate_rules = list(filter(lambda rr: self.is_valid_rate_rule(rr), data['rules']))
        assignment_rules = list(filter(lambda rr: self.is_valid_assignment_rule(rr), data["rules"]))
        self.rate_rules = list(map(lambda rr: self.build_rate_rules(rr, self.species, self.parameters), rate_rules))
        self.assignment_rules = list(map(lambda ar: self.build_assignment_rules(ar, self.species, self.parameters), assignment_rules))
        self.function_definitions = list(map(lambda fd: self.build_function_definitions(fd), data['functionDefinitions']))
        self.model = _Model(name, self.species, self.parameters, self.reactions, self.events, self.rate_rules, 
             self.assignment_rules, self.function_definitions, endSim, timeStep, volume)

    def build_specie(self, args, is_ode):
        '''
        Build a GillesPy2 species.

        Atrributes
        ----------
        args : dict
            A json representation of a species.
        '''
        name = args['name'].strip()
        value = args['value']
        if not is_ode:
            mode = args['mode']
        else:
            mode = 'continuous'
        switch_tol = args['switchTol']
        if args['isSwitchTol']:
            switch_min = 0
        else:
            switch_min = args['switchMin']

        return Species(name=name, initial_value=value, mode=mode, switch_tol=switch_tol, switch_min=switch_min)
        
    def build_parameter(self, args):
        '''
        Build a GillesPy2 parameter.

        Attributes
        ----------
        args : dict
            A json representation of a parameter.
        '''
        name = args['name'].strip()
        expression = args['expression']
        return Parameter(name=name, expression=expression)

    def build_reaction(self, args, parameters):
        '''
        Build a GillesPy2 reaction.

        Attributes
        ----------
        args : dict
            A json representation of a reaction.
        parameters : list
            List of GillesPy2 parameters.
        '''
        if args['reactionType'] not in 'custom-propensity':
            rate = list(filter(lambda p: p.name == args['rate']['name'], parameters))[0]
            propensity = None
        else:
            rate = None
            propensity = args['propensity']
        R = Reaction(
            name=args['name'],
            reactants=self.build_stoich_species_dict(args['reactants']),
            products=self.build_stoich_species_dict(args['products']),
            rate=rate,
            propensity_function=propensity
        )
        return R


    def build_event(self, args, species, parameters):
        '''
        Build a GillesPy2 event.

        Attributes
        ----------
        args : dict
            A json representation of an event.
        species : list
            List of GillesPy2 species.
        parameter : list
            List of GillesPy2 parameters.
        '''
        name = args['name']
        if not args['delay'] == "":
            delay = args['delay']
        else:
            delay = None
        priority = args['priority']
        trigger_expression = args['triggerExpression']
        initial_value = args['initialValue']
        persistent = args['persistent']
        use_values_from_trigger_time = args['useValuesFromTriggerTime']

        trigger = EventTrigger(expression=trigger_expression, initial_value=initial_value, persistent=persistent)

        assignments = list(map(lambda a: self.build_event_assignment(a, self.species, self.parameters), args['eventAssignments']))

        return Event(name=name, delay=delay, assignments=assignments, priority=priority, trigger=trigger, use_values_from_trigger_time=use_values_from_trigger_time)


    def build_event_assignment(self, args, species, parameters):
        '''
        Build a GillesPy2 event assignment.

        Attributes
        ----------
        args : dict
            A json representation of an event assignment.
        species : list
            List of GillesPy2 species.
        parameter : list
            List of GillesPy2 parameters.
        '''
        expression = args['expression']
        variable = list(filter(lambda s: s.name == args['variable']['name'], species))
        if not len(variable):
            variable = list(filter(lambda p: p.name == args['variable']['name'], parameters))

        return EventAssignment(variable=variable[0], expression=expression)
        

    def is_valid_rate_rule(self, rr):
        if rr['type'] == "Rate Rule" and not rr['expression'] == "":
            return rr


    def is_valid_assignment_rule(self, rr):
        if rr['type'] == "Assignment Rule" and not rr['expression'] == "":
            return rr


    def build_rate_rules(self, args, species, parameters):
        '''
        Build a GillesPy2 rate rule.

        Attributes
        ----------
        args : dict
            A json representation of a rate rule.
        species : list
            List of GillesPy2 species.
        parameter : list
            List of GillesPy2 parameters.
        '''
        name = args['name'].strip()
        variable = list(filter(lambda s: s.name == args['variable']['name'], species))
        if not len(variable):
            variable = list(filter(lambda p: p.name == args['variable']['name'], parameters))
        expression = args['expression'].strip()
        return RateRule(name=name, variable=variable[0].name, formula=expression)


    def build_assignment_rules(self, args, species, parameters):
        '''
        Build a GillesPy2 assignment rule.

        Attributes
        ----------
        args : dict
            A json representation of an assignment rule.
        species : list
            List of GillesPy2 species.
        parameter : list
            List of GillesPy2 parameters.
        '''
        name = args['name'].strip()
        variable = list(filter(lambda s: s.name == args['variable']['name'], species))
        if not len(variable):
            variable = list(filter(lambda p: p.name == args['variable']['name'], parameters))
        expression = args['expression'].strip()
        return AssignmentRule(name=name, variable=variable[0].name, formula=expression)


    def build_stoich_species_dict(self, args):
        '''
        Build a dictionary of GillesPy2 stoich species

        Attributes
        ----------
        args : dict
            A json representation of a stoich species
        '''
        d = {}
        for stoich_specie in args:
            key = stoich_specie['specie']['name']
            value = stoich_specie['ratio']
            d[key] = value
        return d


    def build_function_definitions(self, args):
        '''
        Build a GillesPy2 function definition.

        Attributes
        ----------
        args : dict
            A json representation of a function definition.
        '''
        name = args['name']
        variables = args['variables'].split(', ')
        expression = args['expression']

        return FunctionDefinition(name=name, args=variables, function=expression)
        

def get_models(full_path, name):
    try:
        with open(full_path, "r") as model_file:
            stochss_model = json.loads(model_file.read())
            stochss_model['name'] = name
            is_ode = stochss_model['defaultMode'] == "continuous"
    except FileNotFoundError as error:
        print(str(error))
        log.critical("Failed to find the model file: {0}".format(error))

    try:
        _model = ModelFactory(stochss_model, is_ode) # build GillesPy2 model
        gillespy2_model = _model.model
    except Exception as error:
        print(str(error))
        log.error(str(error))
        gillespy2_model = None

    return gillespy2_model, stochss_model


def run_model(model_path):
    '''
    Run the model and return a preview of the results from the first trajectory.
    Model runs will timeout after 5 seconds if the model hasn't completed.
    Logs are logged to a stream object.

    Attributes
    ----------
    model_path : str
        Path to the model file.
    '''
    gillespy2_model, stochss_model = get_models(model_path, model_path.split('/').pop().split('.')[0])
    workflow = GillesPy2Workflow(None, model_path)
    results = workflow.run_preview(gillespy2_model, stochss_model)
    return results


def run_solver(model, data, run_timeout, is_ssa=False, solver=None, rate1=None, rate2=None):
    '''
    Choose the solver based on the algorithm and is_stochastic.

    Attributes
    ----------
    model : GillesPy2 Model
        Model to be run.
    data : dict
        Simulation settings to use for the run.
    run_timeout : int
        Number of seconds until the simulation times out.
    '''
    # print("Selecting the algorithm")
    algorithm = "V-SSA" if is_ssa else data['algorithm']
    if data['isAutomatic']:
        return chooseForMe(model, run_timeout, is_ssa, solver, rate1, rate2)
    if(algorithm == "ODE"):
        return basicODESolver(model, data, run_timeout)
    if(algorithm == "SSA"):
        return ssaSolver(model, data, run_timeout)
    if(algorithm == "V-SSA"):
        return v_ssa_solver(model, data, run_timeout, solver, rate1, rate2)
    if(algorithm == "Tau-Leaping"):
        return basicTauLeapingSolver(model, data, run_timeout)
    if(algorithm == "Hybrid-Tau-Leaping"):
        return basicTauHybridSolver(model, data, run_timeout)


def chooseForMe(model, run_timeout, is_ssa, solver, rate1, rate2):
    print("running choose for me")
    if solver is None:
        solver = model.get_best_solver(precompile=False)

    kwargs = {"solver":solver, "timeout":run_timeout}

    variables = {} if rate1 is None else {rate1[0]:rate1[1]}
    if rate2 is not None:
        variables[rate2[0]] = rate2[1]

    if solver.name == "VariableSSACSolver":
        kwargs["variables"] = variables

    results = model.run(**kwargs)
    return results


def basicODESolver(model, data, run_timeout):
    '''
    Run the model with the GillesPy2 BasicODESolver.

    Attributes
    ----------
    model : GillesPy2 Model
        Model to be run.
    data : dict
        Simulation settings to use for the run.
    run_timeout : int
        Number of seconds until the simulation times out.
    '''
    # print("running ode solver")
    results = model.run(
        solver = BasicTauHybridSolver,
        timeout = run_timeout,
        integrator_options = { 'atol' : data['absoluteTol'], 'rtol' : data['relativeTol']}
    )
    return results


def ssaSolver(model, data, run_timeout):
    '''
    Run the model with the best GillesPy2 SSASolver.

    Attributes
    ----------
    model : GillesPy2 Model
        Model to be run.
    data : dict
        Simulation settings to use for the run.
    run_timeout : int
        Number of seconds until the simulation times out.
    '''
    print("running ssa solver")
    seed = data['seed']
    if(seed == -1):
        seed = None
    results = model.run(
        timeout = run_timeout,
        number_of_trajectories = data['realizations'],
        seed = seed
    )
    return results


def v_ssa_solver(model, data, run_timeout, solver, rate1, rate2):
    seed = data['seed']
    if seed == -1:
        seed = None
    variables = {rate1[0]:rate1[1]}
    if rate2 is not None:
        variables[rate2[0]] = rate2[1]
    results = model.run(
        solver = solver,
        timeout = run_timeout,
        number_of_trajectories = data['realizations'],
        seed = seed,
        variables = variables
    )
    return results


def basicTauLeapingSolver(model, data, run_timeout):
    '''
    Run the model with the GillesPy2 BasicTauLeapingSolver.
    
    Attributes
    ----------
    model : GillesPy2 Model
        Model to be run.
    data : dict
        Simulation settings to use for the run.
    run_timeout : int
        Number of seconds until the simulation times out.
    '''
    # print("running tau leaping solver")
    seed = data['seed']
    if(seed == -1):
        seed = None
    results = model.run(
        solver = BasicTauLeapingSolver,
        timeout = run_timeout,
        number_of_trajectories = data['realizations'],
        seed = seed,
        tau_tol = data['tauTol']
    )
    return results


def basicTauHybridSolver(model, data, run_timeout):
    '''
    Run the model with the GillesPy2 BasicTauHybridSolver.
    
    Attributes
    ----------
    model : GillesPy2 Model
        Model to be run.
    data : dict
        Simulation settings to use for the run.
    run_timeout : int
        Number of seconds until the simulation times out.
    '''
    # print("running hybrid solver")
    seed = data['seed']
    if(seed == -1):
        seed = None
    results = model.run(
        solver = BasicTauHybridSolver,
        timeout = run_timeout,
        number_of_trajectories = data['realizations'],
        seed = seed,
        tau_tol = data['tauTol'],
        integrator_options = { 'atol' : data['absoluteTol'], 'rtol' : data['relativeTol']}
    )
    return results


def get_parsed_args():
    '''
    Initializes an argpaser to document this script and returns a dict of
    the arguments that were passed to the script from the command line.

    Attributes
    ----------

    '''
    parser = argparse.ArgumentParser(description="Run a preview of a model. Prints the results of the first trajectory after 5s.")
    parser.add_argument('model_path', help="The path from the user directory to the model.")
    parser.add_argument('outfile', help="The temp file used to hold the results.")
    parser.add_argument('-s', '--start', action="store_true", help="Start a model preview run.")
    parser.add_argument('-r', '--read', action="store_true", help="Check for model preview results.")
    args = parser.parse_args()
    if not (args.start or args.read):
        parser.error("No action requested, please add -s (start) or -r (read).")
    return args


if __name__ == "__main__":
    args = get_parsed_args()
    model_path = os.path.join(user_dir, args.model_path)
    outfile = os.path.join(user_dir, ".{0}".format(args.outfile))
    if not args.read:
        resp = {"timeout":False}
        try:
            results = run_model(model_path)
            resp["results"] = results
            logs = log_stream.getvalue()
            if 'GillesPy2 simulation exceeded timeout.' in logs:
                resp['timeout'] = True
        except ModelError as error:
            resp['errors'] = str(error)
        with open(outfile, "w") as fd:
            json.dump(resp, fd)
        open(outfile + ".done", "w").close()
    else:
        if os.path.exists(outfile + ".done"):
            with open(outfile, "r") as fd:
                print(fd.read())
            os.remove(outfile)
            os.remove(outfile + ".done")
    log_stream.close()


