# Automation : From Geoemtry to SnappyHexMesh setup - using STL files
Process automation for converting any geoemtry with its surfaces meshed and generating mesh using snappyHexMesh.

The geoemtry automation process is built based on [Coreform Cubit](https://coreform.com/coreform-cubit/). To use this process, the simulation geometry/domain needs to be created as well as the surface mesh needs to ge created already. Once, prerequisites are done, the scriptes included in this repository can be used to create and save the the necessary stl files and geometry information. These geometry files and information is later used for creating the dictionaries needed for the snappyHexMesh process.

<br>

### Repository Contents

```
Repository
    |---- process_input_template/
    |         |---- cubit2snappyHex_input_case_template.py
    |         |---- snappyHexMesh_from_stl_input_template.sh
    |---- scripts/
    |         |---- cubit2snappyHexMesh.py
    |         |---- snappyHexMesh_from_stl.py
    |---- test_cases/
              |---- geometry/
              |---- snappyHex_case/

```

<br>

### Process Overview

The automation process workflow is outlined below - 

1. Geometry Generation (cubit2snappyHexMesh.py)
    1. Imports the working file.
    2. Creates **shared tolopogy**.
    3. Creates surface mesh (tet mesh).
    4. Creates STL files representing the boundaries and zones.
    5. Clean up the created STL files.
    6. Merges STL files to create seperate STL files that represents the complete geometry.
    7. Create a json file containing necessary information necessary for the snappyHexMesh process.
2. Mesh generation (snappyHexMesh_from_stl.py)
    1. Setup an OpenFOAM case directory for the snappyHexMesh process.
    2. Copy necessary files (described in the case inpu file) necessary for the process
    3. Creates all the dictionaries needed to run the snappyHexMesh process.
    4. Runs the process - 
        1. Runs ```blockMesh``` to create the background mesh.
        2. Runs ```snappyHexMesh``` to generate the desired mesh.
        3. Runs ```topoSet``` to define zones in the mesh.


<br>

### How to Use?

Follow these steps to use this tools.

1. Download the repository or the required files
2. Keep the source code seperate from the working files
    1. Create seperate directories for working session
    2. Copy the **input template** needed for the session/work. There are two seperate input template files in this repository for **[1]** STL file generation, **[2]**
 mesh generation using the STL files.
    3. Rename and update the template input files as needed for the working case/session.
    4. Run the processes.


<br>

**To run the automated geoemtry/STL file creation process** - 

1. Add all necessary information in the input file (python).
2. Open Coreform/Cubit.
3. Go to ```Tools```.
4. Go to ```Play Journal File```.
5. Select ```Python Files``` from file type.
6. Select the process input file - this will execute the automation process.


<br>

<u>Here is a preview of the input file for geometry/STL file generation process</u>

```python

#---------------------------------------
### Case/Session Input
#---------------------------------------
caseName = "case_name"

scriptLocation = "path/to/the/cubit2snappyHexMesh/script"
scriptName = "cubit2snappyHexMesh.py"

stlExportSubDirName = "export_pre_formatted_stl"

#---------------------------------------
### Geometry Input
#       input geometry file can be either
#       a cub file or a step/stp file
#---------------------------------------
workingDir = r"path/to/working/directory"
inputGeometry = "input_geometry_file.ext"

meshSize = 1.0

#---------------------------------------
### Boundary Condition Input
#---------------------------------------

bcDict = {}
bcDict["bc_1"] = { 
    "type" : "inlet", 
    "surface-list" : [], 
}
bcDict["bc_2"] = { 
    "type" : "outlet", 
    "surface-list" : [], 
}
bcDict["bc_3"] = { 
    "type" : "wall", 
    "surface-list" : [], 
}

#---------------------------------------
### Zone Input
#---------------------------------------

blockDict = {}
blockDict["zone_1"] = []
blockDict["zone_2"] = []
blockDict["zone_3"] = []

#---------------------------------------
### Default Input
#---------------------------------------

mergeAllSolidTogether = True
mergeAllBcStlTogether = True

exportDir = workingDir + os.sep + stlExportSubDirName

#---------------------------------------
### RUN SCRIPT
#---------------------------------------

scriptPath = scriptLocation + os.sep + scriptName

with open(scriptPath, "rb") as source_file:
    code = compile(source_file.read(), scriptPath, "exec")
    exec(code, globals()) 

#---------------------------------------

```


<br>

**To run the automated snappyHexMesh generation process** - 

1. Add all necessary information in the input file (.sh).
2. Make sure to 
    1. Set the automation script path
    2. Path of the python interpreter
3. Run the process input script - **make sure** the script is executable.


<br>

<u>Here is a preview of the input file for snappyHexMesh generation process</u>

```bash

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

```


