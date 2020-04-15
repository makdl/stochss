#!/usr/bin/env python3

import json
import nbformat
from nbformat import v4 as nbf
from os import path
from .rename import get_unique_file_name
from json.decoder import JSONDecodeError
from .stochss_errors import ModelNotFoundError, ModelNotJSONFormatError, JSONFileNotModelError

# imports for modal notebook
from .generate_notebook_cells import generate_imports_cell, generate_model_cell, generate_run_cell
# imports for model inference workflow

def convert_to_mdl_inference_nb(model_path):
    user_dir = "/home/jovyan"

    full_path = path.join(user_dir,model_path)
    file = full_path.split('/').pop()
    name = file.split('.')[0].replace('-', '_')
    dest_path = model_path.split(file)[0]
    
    # Collect .mdl Data
    try:
        with open(full_path, 'r') as json_file:
            json_data = json.load(json_file)
    except FileNotFoundError as err:
        raise ModelNotFoundError('Could not find model file: ' + str(err))
    except JSONDecodeError as err:
        raise ModelNotJSONFormatError("The model is not JSON decodable: "+str(err))

    # Create new notebook
    cells = []
    # Create Markdown Cell with name
    cells.append(nbf.new_markdown_cell('# {0}'.format(name)))
    try:
        # Create imports cell
        cells.append(nbf.new_code_cell(generate_imports_cell(json_data)))
        # Create Model Cell
        cells.append(nbf.new_code_cell(generate_model_cell(json_data, name)))
        # Instantiate Model Cell
        cells.append(nbf.new_code_cell('model = {0}()'.format(name)))
        # Create simulator cell
        cells.append(nbf.new_code_cell(generate_mdl_inf_simulator_cell()))
    except KeyError as err:
        raise JSONFileNotModelError("The JSON file is not formatted as a StochSS model "+str(err))

    # Append cells to worksheet
    nb = nbf.new_notebook(cells=cells)

    # Open and write to file
    dest_file = get_unique_file_name('{}2dParamSweep.ipynb'.format(name), dest_path)[0]
    with open(dest_file, 'w') as f:
        nbformat.write(nb, f, version=4)
    f.close()

    return dest_file.replace(user_dir+'/', "")