#! /usr/bin/bash

#---------------------------------------
### CASE INPUT - START
#---------------------------------------

export working_dir="path/to/the/working/directory"
export input_json_filename="input_json_filename.json"

### needed for the dictionary setup
###     leave these default, if you want
export openfoam_version="v2412"
export foamfile_version="2.0"

### options are --> "mm" or "m"
export geometry_length_unit="mm"

### syntax --> "x-coord, y-coord, z-coord"
export location_in_mesh="0.0, 0.0, 0.0"

export blockmesh_size=2

#---------------------------------------

### provide the path to your openfoam bashrc file
###     Typically located at - [openfoam installation directory]/etc/bashrc
export openfoam_bashrc_path="path/to/the/openfoam/bashrc/file"

### provide the path of the process automation script
snappyHex_case_generation_script="path/to/the/snappyHexMesh_from_stl.py/script"

### provide the of the python interpreter be it
###    from an installation or from a virtual environment
python="path/to/the/python/interpreter"

#---------------------------------------
### CASE INPUT - END
#---------------------------------------

log_file="$working_dir/log_generate_snappyHexMesh_case.txt"

if [[ -f "$log_file" ]]; then
    rm -f "$log_file"
fi

if [[ ! -f "$working_dir/$input_json_filename" ]]; then
    echo "The input json file \"$input_json_filename\" not found in the working directory."
    echo "Aborting ... ... ..."
    exit
fi

### run the automated process
$python "$snappyHex_case_generation_script" |& tee "$log_file"

#---------------------------------------


