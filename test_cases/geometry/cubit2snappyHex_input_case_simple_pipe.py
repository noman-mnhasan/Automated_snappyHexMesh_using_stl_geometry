

import os

#---------------------------------------
### Case/Session Input
#---------------------------------------
caseName = "test_tube"

scriptLocation = r"path/to/the/cubit2snappyHexMesh/script"
scriptName = "cubit2snappyHexMesh.py"

stlExportSubDirName = "export_pre_formatted_stl"


#---------------------------------------
### Geometry Input
#       input geometry file can be either
#       a cub file or a step/stp file
#---------------------------------------
workingDir = r"path/to/working/directory"
inputGeometry = "simple_pipe.stp"

### Size of the surface mesh
meshSize = 1.0

#---------------------------------------
### Boundary Condition Input
#---------------------------------------
bcDict = {}
bcDict["inlet"] = { \
    "type" : "inlet", \
    "surface-list" : [4], \
}
bcDict["outlet"] = { \
    "type" : "outlet", \
    "surface-list" : [8], \
}
bcDict["wall"] = { \
    "type" : "wall", \
    "surface-list" : [1, 3, 5, 7, 9, 11], \
}


#---------------------------------------
### Zone Input
#---------------------------------------
blockDict = {}
blockDict["entry"] = [1]
blockDict["middle"] = [3]
blockDict["exit"] = [2]


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






