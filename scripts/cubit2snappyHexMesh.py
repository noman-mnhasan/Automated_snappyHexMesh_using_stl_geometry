"""
    Automation script for Coreform/Cubit
    
    Imports geoemtry in STEP format and creates a set of STL files to 
    generate mesh using the "snappyHexMesh" mesh utility in OpenFOAM.
    
    Exports geometry information ito a JSON file as an input for the 
    mesh generation automation process/script.
"""


import os
import sys
import platform
import shutil
import json

import cubit

def list2string(pList, sep = ", "):
    return str(sep).join([str(x) for x in pList])


def export_pre_formatted_stl_files( \
        exportDir, \
        bcDict, \
        blockDict, \
        bcSurfaceList = [], \
    ):
    bcStlFileList = []
    blockStlFileList = []
    preFormatPostFix = "_pre_formatted"
    checkExportDir = os.path.exists(exportDir)
    
    print("External surface list : " + ", ".join([str(x) for x in bcSurfaceList]))
    
    if not checkExportDir:
        if platform.system().lower() == "windows":
            os.system("mkdir \"" + exportDir + "\"")
        elif platform.system().lower() == "linux":
            os.system("mkdir -p \"" + exportDir + "\"")
    else:
        shutil.rmtree(exportDir)
        if platform.system().lower() == "windows":
            os.system("mkdir \"" + exportDir + "\"")
        elif platform.system().lower() == "linux":
            os.system("mkdir -p \"" + exportDir + "\"")
    
    for bcName, bcData in bcDict.items():
        print("{0:20} : {1}".format(bcName, ", ".join([str(x) for x in bcData["surface-list"]])))
        if bool(bcData["surface-list"]):
            bcStlFilename = "bc_" + str(bcName) + preFormatPostFix + ".stl"
            bcStlFileList.append(bcStlFilename)
            cmd2cub = ""
            cmd2cub = "export stl ascii \"" + exportDir + os.sep + bcStlFilename + "\" surface " + list2string(bcData["surface-list"], sep = " ") + " mesh overwrite"
            print(cmd2cub)
            cubit.cmd(cmd2cub)
        else:
            continue
    
    for block, volumeList in blockDict.items():
        print("{0:20} : {1}".format(block, ", ".join([str(x) for x in volumeList])))
        surfaceList = []
        meshedSurfaceList = []
        if bool(volumeList):
            for volume in volumeList:
                surfaceList.extend(cubit.get_relatives("volume", volume, "surface"))
            print("Meshed surfaces in volume " + str(volume) + " : " + ", ".join([str(x) for x in surfaceList]))
            meshedSurfaceList = [x for x in surfaceList if cubit.is_meshed("surface", x) == True]
            blockStlFilename = "block_" + str(block) + preFormatPostFix + ".stl"
            blockStlFileList.append(blockStlFilename)
            cmd2cub = ""
            cmd2cub = "export stl ascii \"" + exportDir + os.sep + blockStlFilename + "\" surface " + list2string(meshedSurfaceList, sep = " ") + " mesh overwrite"
            print(cmd2cub)
            cubit.cmd(cmd2cub)
        else:
            continue
    
    if bool(bcSurfaceList):
        completeDomainStlFilename = "complete_domain" + ".stl"
        cmd2cub = ""
        cmd2cub = "export stl ascii \"" + exportDir + os.sep + completeDomainStlFilename + preFormatPostFix + "\"" + list2string(bcSurfaceList, sep = " ") + " mesh overwrite"
    else:
        print("Complete file for the domain is missing ...")
        return None, None, None, None
    
    return bcStlFileList, blockStlFileList, completeDomainStlFilename, preFormatPostFix


def remove_surface_definition_from_stl_file( \
        fileSourcePath, \
        fileTargetPath, \
        preFormatPostFix, \
        mergeAllSolidTogether = True, \
    ):
    wspace = " "
    indent = wspace*4
    baseFilename = os.path.basename(fileSourcePath)
    with open(fileSourcePath, "r") as stlf:
        readStlData = stlf.readlines()
        
    stripString = preFormatPostFix + ".stl"
    stripLength = len(stripString)
    StlDefiniationName = ""
    StlDefiniationName = baseFilename[ : (-1 * stripLength)]
    StlDefiniationName = StlDefiniationName.split("_")[1]
    print("\n")
    
    str2print = "-"*40 + "\n"
    str2print += "[*] Source filename : " + "\n"
    str2print += baseFilename + "\n"
    str2print += "" + "\n"
    str2print += "[*] Target filename : " + "\n"
    str2print += os.path.basename(fileTargetPath) + "\n"
    str2print += "" + "\n"
    str2print += "[*] STL solid definition name : " + "\n"
    str2print += StlDefiniationName + "\n"
    str2print += "" + "\n"
    print(str2print)
    
    solidDefinitionStartList = []
    solidDefinitionEndList = []
    solidNameList = []
    
    nSolid = 0
    searchStringStart = "solid "
    searchStringStartLen = len(searchStringStart)
    searchStringEnd = "endsolid "
    searchStringEndLen = len(searchStringEnd)
    
    for index, line in enumerate(readStlData):
        if line[ : searchStringStartLen] == searchStringStart:
            solidDefinitionStartList.append(index)
            nSolid += 1
            solidNameList.append(line.replace(searchStringStart, ""))
        elif line[ : searchStringEndLen] == searchStringEnd:
            solidDefinitionEndList.append(index)
    solidNameListStr = ""
    for solidName in solidNameList:
        solidNameListStr += str(solidName.rstrip("\n")) + ", "
    ### Removing the last entry of the newline ("\n")
    solidNameListStr = solidNameListStr.strip("\n")
    
    str2print = ""
    str2print += "-"*40 + "\n"
    str2print += "Number of \"Solid\" definition : " + str(nSolid) + "\n"
    str2print += "Names of \"Solid\" definition : " + "\n" + indent + solidNameListStr.replace(", ", "\n" + indent) + "\n"
    str2print += "" + "\n"
    print(str2print)
    
    solidDefinitionTotal = []
    for i in range(nSolid):
        solidDefinition = None
        start = solidDefinitionStartList[i]
        end = solidDefinitionEndList[i] + 1
        
        if mergeAllSolidTogether:
            solidDefinition = readStlData[(start + 1) : (end - 1)]
        else:
            solidDefinition = readStlData[start : end]
        solidDefinitionTotal.extend(solidDefinition)
        
        if mergeAllSolidTogether:
            solidDefinitionTotal.insert(0, ("solid " + StlDefiniationName + "\n"))
            solidDefinitionTotal.append("endsolid " + StlDefiniationName + "\n")
    
    
        solidDefinitionTotalStr = "".join([x for x in solidDefinitionTotal])
        
        with open(fileTargetPath, "w") as tf:
            tf.write(solidDefinitionTotalStr)
    
    return solidDefinitionTotal


def format_exported_stl_file( \
        bcStlFileList, \
        blockStlFileList, \
        completeDomainStlFilename, \
        preFormatPostFix, \
        exportDir, \
        snappyHexReadyStlFileDirPath, \
        mergeAllSolidTogether = True, \
        mergeAllBcStlTogether = True, \
    ):
    stlDataAsList = []
    stlDataAsListTotal = []
    formattedBcStlList = []
    formattedBlockStlList = []
    combinedBcStlFilename = "combinedBcStl" + ".stl"
    combinedBlockStlFilename = "combinedBlockStl" + ".stl"
    
    if not os.path.exists(snappyHexReadyStlFileDirPath):
        if platform.system().lower() == "windows":
            os.system("mkdir \"" + snappyHexReadyStlFileDirPath + "\"")
        elif platform.system().lower() == "linux":
            os.system("mkdir -p \"" + snappyHexReadyStlFileDirPath + "\"")
    else:
        shutil.rmtree(snappyHexReadyStlFileDirPath)
        if platform.system().lower() == "windows":
            os.system("mkdir \"" + snappyHexReadyStlFileDirPath + "\"")
        elif platform.system().lower() == "linux":
            os.system("mkdir -p \"" + snappyHexReadyStlFileDirPath + "\"")
    
    for filename in bcStlFileList:
        stripString = preFormatPostFix + ".stl"
        stripLength = len(stripString)
        baseFilename = ""
        baseFilename = filename[ : (-1 * stripLength)]
        baseFilename += ".stl"
        print("\n")
        print(filename)
        print(baseFilename)
        formattedBcStlList.append(baseFilename)
        fileSourcePath = exportDir + os.sep + filename
        fileTargetPath = snappyHexReadyStlFileDirPath + os.sep + baseFilename
        
        stlDataAsList = remove_surface_definition_from_stl_file( \
                                fileSourcePath, \
                                fileTargetPath, \
                                preFormatPostFix, \
                                mergeAllSolidTogether, \
                            )
    
    for filename in blockStlFileList:
        stripString = preFormatPostFix + ".stl"
        stripLength = len(stripString)
        baseFilename = ""
        baseFilename = filename[ : (-1 * stripLength)]
        baseFilename += ".stl"
        print("\n")
        print(filename)
        print(baseFilename)
        formattedBlockStlList.append(baseFilename)
        fileSourcePath = exportDir + os.sep + filename
        fileTargetPath = snappyHexReadyStlFileDirPath + os.sep + baseFilename
        
        stlDataAsList = remove_surface_definition_from_stl_file( \
                                fileSourcePath, \
                                fileTargetPath, \
                                preFormatPostFix, \
                                mergeAllSolidTogether, \
                            )
        stlDataAsListTotal.extend(stlDataAsList)
    
    completeDomainStlFilename = completeDomainStlFilename.rstrip(preFormatPostFix + ".stl")
    completeDomainStlFilename += ".stl"
    if mergeAllBcStlTogether:
        str2print = "\n"
        str2print += "Merging all STL files which represent BCs" + "\n"
        str2print += "-----------------------------------------" + "\n"
        print(str2print)
        
        os.chdir(snappyHexReadyStlFileDirPath)
        
        if platform.system().lower() == "windows":
            os.system("type " + list2string(formattedBcStlList, sep = " ") + " > " + combinedBcStlFilename)
            os.system("type " + list2string(formattedBlockStlList, sep = " ") + " > " + combinedBlockStlFilename)
        elif platform.system().lower() == "linux":
            os.system("cat " + list2string(formattedBcStlList, sep = " ") + " > " + combinedBcStlFilename)
            os.system("cat " + list2string(formattedBlockStlList, sep = " ") + " > " + combinedBlockStlFilename)
        
        os.chdir(workingDir)
        
    return ( \
            formattedBcStlList, \
            formattedBlockStlList, \
            combinedBcStlFilename, \
            combinedBlockStlFilename, \
        )

def write_crash_report( \
        workingDir, \
        reportString, \
    ):
    crashFile = workingDir + os.sep + "crash_report.txt"
    
    with open(crashFile, "w") as crf:
        crf.write(reportString)
    return



#---------------------------------------
### PROCESS CONTROL
#---------------------------------------

"""
    The backslashes ( \ ) at the end of lines are as a safeguard if the 
    python version for the running Cubit session is 2.x.
    
    cmd2cub = ""    --> setting the command string to empty string just in case

"""

#--------------------------------------- 

removeFileList = [ \
    workingDir + os.sep + "snappyHexInfo.json", \
    workingDir + os.sep + "crash_report.txt", \
]

for item in removeFileList:
    if os.path.exists(item):
        os.remove(item)

#---------------------------------------
fileExtension = inputGeometry.split(".")[-1]

reportString = ""
checkInputDict = {}

checkInputDict["file-extension"] = True
if fileExtension.lower() == "cub":
    cmd2cub = ""
    cmd2cub = "open \"" + workingDir + os.sep + inputGeometry + "\""
    cubit.cmd(cmd2cub)
    cubit.cmd("view iso")
elif fileExtension.lower() == "stp" or fileExtension.lower == "step":
    cmd2cub = ""
    cmd2cub = "import step \"" + workingDir + os.sep + inputGeometry + "\" heal"
    cubit.cmd(cmd2cub)
    cubit.cmd("view iso")
else:
    checkInputDict["file-extension"] = False
    reportString += "The geometry extension found --> \"" + fileExtension + "\"" + "\n"
    reportString += "Supported extensions are" + "\n"
    reportString += " - cub (cubit)" + "\n"
    reportString += " - step/step" + "\n"
    reportString += "" + "\n"
    
#---------------------------------------   

bcSurfaceList = []
checkInputDict["bc"] = True

for bc in bcDict.keys():
    bcSurfaceList.extend(
            list(bcDict[bc]["surface-list"])
        )

allExternalSurfaceList = [x for x in list(cubit.get_entities("surface")) if cubit.is_merged("surface", x) != True]

if len(allExternalSurfaceList) != len(bcSurfaceList):
    checkInputDict["bc"] = False
    reportString += "The number of external (no-shared/merged) surface present in the geometry does not match with the user input" + "\n"
    reportString += "User provided number of bc surfaces --> " + list2string(bcSurfaceList) + "\n"
    reportString += "Calculated number of bc surfaces    --> " + list2string(allExternalSurfaceList) + "\n"
    reportString += "" + "\n"
    reportString += "Check the input file " + "\n"
    reportString += " - Check if all the boundary conditions are added" + "\n"
    reportString += " - Check if any surface got missed in the surface list for any boundary condition." + "\n"
    reportString += "" + "\n"

#--------------------------------------- 

zoneVolumeList = []
checkInputDict["zone"] = True

for block in blockDict.keys():
    zoneVolumeList.extend(
            list(blockDict[block])
        )

allVolumeList = cubit.get_entities("volume")

if len(allVolumeList) != len(zoneVolumeList):
    checkInputDict["zone"] = False
    reportString += "The number of volumes present in the geometry does not match with the user input" + "\n"
    reportString += "User provided number of volumes (from block) --> " + list2string(zoneVolumeList) + "\n"
    reportString += "Calculated number of volumes                 --> " + list2string(allVolumeList) + "\n"
    reportString += "" + "\n"
    reportString += "Check the input file " + "\n"
    reportString += " - Check if all the zones/blocks are added" + "\n"
    reportString += " - Check if any volume got missed in the volume list for any zone/block." + "\n"
    reportString += "" + "\n"

#--------------------------------------- 

### EXIT if check fails ###

if False in checkInputDict.values():
    write_crash_report( \
            workingDir, \
            reportString, \
        )

#--------------------------------------- 

wspace = " "
indent = wspace*4

#--------------------------------------- 

### Merge all entities
cubit.cmd("merge all")

### Create surface mesh
cubit.cmd("surface all size " + str(meshSize))
cubit.cmd("set trimesher coarse off")
cubit.cmd("surface all scheme trimesh")
cubit.cmd("mesh surface all")

#--------------------------------------- 

( \
    bcStlFileList, \
    blockStlFileList, \
    completeDomainStlFilename, \
    preFormatPostFix, \
) = export_pre_formatted_stl_files( \
        exportDir, \
        bcDict, \
        blockDict, \
        bcSurfaceList, \
    )

snappyHexReadyStlFileDir = "snappyHexMesh_ready_stl_files"

resultDict = {}
resultDict["snappyhex-ready-stl-dir"] = exportDir.rstrip(os.sep) + os.sep + snappyHexReadyStlFileDir

( \
    formattedBcStlList, \
    formattedBlockStlList, \
    combinedBcStlFilename, \
    combinedBlockStlFilename, \
) = format_exported_stl_file( \
    bcStlFileList, \
    blockStlFileList, \
    completeDomainStlFilename, \
    preFormatPostFix, \
    exportDir, \
    resultDict["snappyhex-ready-stl-dir"], \
    mergeAllSolidTogether, \
    mergeAllBcStlTogether, \
)

bcInfoDict = {}
blockInfoDict = {}

for bcName, bcData in bcDict.items():
    bcInfoDict[bcName] = {
        "bc-stl-file" : "bc_" + bcName + ".stl",
        "type" : bcData["type"]
    }

for block, volumeList in blockDict.items():
    blockInfoDict[block] = "block_" + block + ".stl"

resultDict = {}
resultDict["snappyhex-ready-stl-dir"] = exportDir.rstrip(os.sep) + os.sep + snappyHexReadyStlFileDir
resultDict["bc-info"] = bcInfoDict
resultDict["bc-stl-file-list"] = formattedBcStlList
resultDict["block-info"] = blockInfoDict
resultDict["block-stl-file-list"] = formattedBlockStlList
resultDict["combined-bc-stl-filename"] = combinedBcStlFilename
resultDict["combined-block-stl-filename"] = combinedBlockStlFilename
# resultDict[""] = ""

snappyHexInfoFilename = "snappyHexInfo.json"
snappyHexInfoFile = workingDir + os.sep + snappyHexInfoFilename

with open(snappyHexInfoFile, "w") as ojf:
    json.dump(resultDict, ojf, indent = indent)

#---------------------------------------


