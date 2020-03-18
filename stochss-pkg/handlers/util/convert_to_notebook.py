#!/usr/bin/env python3
import sys
import ast
import json
import nbformat
import argparse
from nbformat import v4 as nbf
from os import path

from .rename import get_unique_file_name
from .generate_notebook_cells import generate_imports_cell, generate_model_cell, generate_run_cell


user_dir = '/home/jovyan'


def convert_to_notebook(_model_path):

    model_path = path.join(user_dir,_model_path)
    file = model_path.split('/').pop()
    name = file.split('.')[0].replace('-', '_')
    dest_path = model_path.split(file)[0]
    
    # Collect .mdl Data
    try:
        with open(model_path, 'r') as json_file:
            # json_data = ast.literal_eval(json_file.read())
            json_data = json.loads(json_file.read())
    except Exception as e:
        print('Could not read file: ' + e)

    # Create new notebook
    cells = []
    # Create Markdown Cell with name
    cells.append(nbf.new_markdown_cell('# {0}'.format(name)))
    # Create imports cell
    cells.append(nbf.new_code_cell(generate_imports_cell(json_data)))
    # Create Model Cell
    cells.append(nbf.new_code_cell(generate_model_cell(json_data, name)))
    # Instantiate Model Cell
    cells.append(nbf.new_code_cell('model = {0}()'.format(name)))
    # Model Run Cell
    cells.append(nbf.new_code_cell(generate_run_cell(json_data)))
    # Plotting Cell
    cells.append(nbf.new_code_cell('results.plotplotly()'))

    # Append cells to worksheet
    nb = nbf.new_notebook(cells=cells)

    # Open and write to file
    dest_file = get_unique_file_name('{}.ipynb'.format(name), dest_path)[0]
    with open(dest_file, 'w') as f:
        nbformat.write(nb, f, version=4)
    f.close()

    print('{0} successfully created'.format(dest_file))

    return dest_file

