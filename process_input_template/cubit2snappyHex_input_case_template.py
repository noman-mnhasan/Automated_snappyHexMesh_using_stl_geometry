

import os

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

### Size of the surface mesh
meshSize = 1.0

 
### The backslashes ( \ ) at the end of lines are as a safeguard if the 
### python version for the running Cubit session is 2.x.
#---------------------------------------
### Boundary Condition Input
#---------------------------------------
bcDict = {}
bcDict["bc_1"] = { \
    "type" : "inlet", \
    "surface-list" : [], \
}
bcDict["bc_2"] = { \
    "type" : "outlet", \
    "surface-list" : [], \
}
bcDict["bc_3"] = { \
    "type" : "wall", \
    "surface-list" : [], \
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
    exec(code, globals()) # Executes in the current module's global scope

#---------------------------------------






