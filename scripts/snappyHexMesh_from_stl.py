"""
    Automation script for mesh generation using the "snappyHemxMesh" utility in OpenFOAM.
    
    - Reads the exported JSON file from the geometry generation process.
    - Generates the required directories and dictionaries to run the "snappyHemxMesh" utility.
    - Runs the mesh generation process.
    - Applies the geometry topology
"""

import os
import sys
import json
import subprocess
import shutil
import time


#---------------------------------------

def get_openfom_dictionary_header(
        openfoamVersion,
    ):
    ver = openfoamVersion
    headerString = ""
    headerString +=  "/*--------------------------------*- C++ -*----------------------------------*\\\n"
    headerString +=  "| =========                 |                                                 |\n"
    headerString +=  "| \\\\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |\n"
    headerString += f"|  \\\\    /   O peration     | Version:  {ver}                                 |\n"
    headerString +=  "|   \\\\  /    A nd           | Website:  www.openfoam.com                      |\n"
    headerString +=  "|    \\\\/     M anipulation  |                                                 |\n"
    headerString +=  "\\*---------------------------------------------------------------------------*/\n"
    return headerString


def get_foamfile_info(
        foamFileVersion,
        location,
        dictName,
    ):
    foamFileInfo = ""
    foamFileInfo += "FoamFile\n"
    foamFileInfo += "{\n"
    foamFileInfo += "    version     " + foamFileVersion + ";\n"
    foamFileInfo += "    format      ascii\n;"
    foamFileInfo += "    class       dictionary;\n"
    foamFileInfo += "    location    " + "\"" + location + "\";\n"
    foamFileInfo += "    object      " +  dictName + ";\n"
    foamFileInfo += "}\n"
    return foamFileInfo


def get_openfoam_dictionary_hline():
    return "// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //"



#---------------------------------------

def empty_populated_directory(
        dirName,
        excludeFileList,
    ):
    fileList = os.listdir(dirName)
    for excludeFile in excludeFileList:
        for index, filename in enumerate(fileList):
            if excludeFile in filename:
                fileList[index] = "NA"
    for filename in fileList:
        filePath = os.path.join(dirName, filename)
        if "NA" in filename:
            continue
        else:
            try:
                if os.path.isfile(filePath) or os.path.islink(filePath):
                    os.unlink(filePath)
                elif os.path.isdir(filePath):
                    shutil.rmtree(filePath)
            except Exception as e:
                str2print = "-"*40 + "\n"
                str2print += f"{'Directory' : <10}: {filePath}\n"
                str2print += f"{'Status' : <10}: {'Failed'}\n"
                str2print += f"{'Reason' : <10}: {e}\n"
                print(str2print)
    return


def populate_triSurface_directory(
        domainInfoDict,
        caseDir,
        triSurfaceDir,
    ):
    stlSourceDir = domainInfoDict["snappyhex-ready-stl-dir"]
    
    if os.path.exists(triSurfaceDir):
        shutil.rmtree(triSurfaceDir)
    os.system("mkdir -p " + triSurfaceDir)
    
    stlFileList = []
    stlFileList.append(domainInfoDict["combined-bc-stl-filename"])
    stlFileList.extend([v["bc-stl-file"] for k, v in domainInfoDict["bc-info"].items()])
    stlFileList.extend(list(domainInfoDict["block-info"].values()))
    
    str2print = "-"*40 + "\n"
    str2print += "STL file list :\n"
    str2print += " - " + "\n - ".join(stlFileList) + "\n"
    str2print += "-"*40 + "\n"
    str2print += "Copying required files to \"triSurface\" directory!\n"
    print(str2print)
    
    for stlFile in stlFileList:
        sourceFile = stlSourceDir + os.sep + stlFile 
        targetFile = triSurfaceDir + os.sep + stlFile 
        shutil.copy2(sourceFile, targetFile)
    return stlFileList


def create_snappyHex_case_directory(caseDir):
    dirList = [
            "0.org", 
            "constant",
            "system"
        ]
    for dir in dirList:
        os.system("mkdir -p " + caseDir + os.sep + dir)
    return


def initiate_snappyHex_case_directory(
        domainInfoDict,
        caseDir,
    ):
    excludeFileList = []
    
    if os.path.exists(caseDir):
        empty_populated_directory(
                caseDir,
                excludeFileList,
            )
    
    create_snappyHex_case_directory(caseDir)
    return


def prepareSTL(
        rPath,
        openfoamEnvSourceCommand
    ):
    str2print = "-"*40 + "\n"
    str2print += "Extracting edge features ...\n"
    print(str2print)
    # commandString = "/bin/bash"
    result = subprocess.run(
            openfoamEnvSourceCommand + " && " + "surfaceFeatureExtract > log_surfaceFeatureExtract.log",
            cwd = rPath,
            shell = True,
        )
    return


def extract_domain_stl_information(
        domainStlFile,
        triSurfaceDir,
    ):
    wspace = " "
    indentLength = 4
    indent = wspace * indentLength
    
    domainStlFilename = os.path.basename(domainStlFile)
    workingStlFile = triSurfaceDir + os.sep + domainStlFilename
    
    str2print = "-"*40 + "\n"
    str2print += "triSurfacedirectory path : " + triSurfaceDir + "\n"
    str2print += "Domain STL file          : " + domainStlFilename + "\n"
    print(str2print)
    
    with open(workingStlFile, "r") as rf:
        domainStlFileData = rf.readlines()
    
    vertexList = []
    
    for index, line in enumerate(domainStlFileData):
        if "vertex" in line:
            lineSegment = [x for x in line.split()]
            vertexList.append(
                    (
                        float(lineSegment[1]),
                        float(lineSegment[2]),
                        float(lineSegment[3]),
                    )
                )
    
    vextexXcoordinateList = [i[0] for i in vertexList]
    vextexYcoordinateList = [i[1] for i in vertexList]
    vextexZcoordinateList = [i[2] for i in vertexList]
    
    domainStlBound = {
            "x-min" : min(vextexXcoordinateList),
            "x-max" : max(vextexXcoordinateList),
            "y-min" : min(vextexYcoordinateList),
            "y-max" : max(vextexYcoordinateList),
            "z-min" : min(vextexZcoordinateList ),
            "z-max" : max(vextexZcoordinateList),
        }
            
    return domainStlBound


#---------------------------------------


def create_block_mesh_dict(
        openfoamVersion,
        foamFileVersion,
        location,
        blockMeshDictFile,
        domainStlBound,
        blockMeshCellSize,
        lengthUnit,
    ):
    openfaomHeaderString = get_openfom_dictionary_header(openfoamVersion)
    
    dictName = "blockMeshDict"
    foamFileInfo = get_foamfile_info(
            foamFileVersion,
            location,
            dictName,
        )
    
    domainExtend = {
        "x-range" : domainStlBound["x-max"] - domainStlBound["x-min"],
        "y-range" : domainStlBound["y-max"] - domainStlBound["y-min"],
        "z-range" : domainStlBound["z-max"] - domainStlBound["z-min"],
    }
    
    nodeSpacing = {
        "x" : int(domainExtend["x-range"] / blockMeshCellSize),
        "y" : int(domainExtend["y-range"] / blockMeshCellSize),
        "z" : int(domainExtend["z-range"] / blockMeshCellSize),
    }
    
    if lengthUnit == "mm":
        conversionFactor = 1.0
        
    elif lengthUnit == "cm":
        conversionFactor = 10.0
        
    elif lengthUnit == "m":
        conversionFactor = 1000.0
    
    tolerance = 10.0
    tolerance = tolerance / conversionFactor
    
    bBox = {
        "x-min" : domainStlBound["x-min"] - tolerance,
        "x-max" : domainStlBound["x-max"] + tolerance,
        "y-min" : domainStlBound["y-min"] - tolerance,
        "y-max" : domainStlBound["y-max"] + tolerance,
        "z-min" : domainStlBound["z-min"] - tolerance,
        "z-max" : domainStlBound["z-max"] + tolerance,
    }
    
    wspace = " "
    indent = wspace * 4
    str2write = ""
    str2write += openfaomHeaderString + "\n"
    str2write += foamFileInfo + "\n"
    str2write += get_openfoam_dictionary_hline() + "\n"
    str2write += "\n"
    str2write += "vertices\n"
    str2write += "(\n"
    str2write += indent + "(" + f"{bBox['x-min']} {bBox['y-min']} {bBox['z-min']}" + ")\n"
    str2write += indent + "(" + f"{bBox['x-max']} {bBox['y-min']} {bBox['z-min']}" + ")\n"
    str2write += indent + "(" + f"{bBox['x-max']} {bBox['y-max']} {bBox['z-min']}" + ")\n"
    str2write += indent + "(" + f"{bBox['x-min']} {bBox['y-max']} {bBox['z-min']}" + ")\n"
    str2write += indent + "(" + f"{bBox['x-min']} {bBox['y-min']} {bBox['z-max']}" + ")\n"
    str2write += indent + "(" + f"{bBox['x-max']} {bBox['y-min']} {bBox['z-max']}" + ")\n"
    str2write += indent + "(" + f"{bBox['x-max']} {bBox['y-max']} {bBox['z-max']}" + ")\n"
    str2write += indent + "(" + f"{bBox['x-min']} {bBox['y-max']} {bBox['z-max']}" + ")\n"
    str2write += ");\n"
    str2write += "\n"
    str2write += "blocks\n"
    str2write += "(\n"
    str2write += indent + "hex (0 1 2 3 4 5 6 7)" + " ("  + f"{nodeSpacing['x']} {nodeSpacing['y']} {nodeSpacing['z']}" + ") " + "simpleGrading (1 1 1 )\n"
    str2write += ");\n"
    str2write += "\n"
    str2write += "edges\n"
    str2write += "(\n"
    str2write += ");\n"
    str2write += "\n"
    str2write += "boundary\n"
    str2write += "(\n"
    str2write += ");\n"
    str2write += "\n"
    str2write += "mergePatchPairs\n"
    str2write += "(\n"
    str2write += ");\n"
    str2write += "\n"
    str2write += get_openfoam_dictionary_hline() + "\n"
    str2write += "// Comments/Notes\n"
    str2write += "// \n"
    str2write += "// \n"
    str2write += get_openfoam_dictionary_hline() + "\n"
    str2write += "\n"
    
    with open(blockMeshDictFile, "w") as wf:
        wf.write(str2write)
    return bBox


def create_control_dictionary(
        openfoamVersion,
        foamFileVersion,
        location,
        controlDictFile,
    ):
    openfaomHeaderString = get_openfom_dictionary_header(openfoamVersion)
    
    dictName = "controlDict"
    foamFileInfo = get_foamfile_info(
            foamFileVersion,
            location,
            dictName,
        )
    
    wspace = " "
    indent = wspace * 4
    str2write = ""
    str2write += openfaomHeaderString + "\n"
    str2write += foamFileInfo + "\n"
    str2write += get_openfoam_dictionary_hline() + "\n"
    str2write += "\n"
    str2write += "application          simpleFoam;\n"
    str2write += "startTime            0;\n"
    str2write += "stopAt               endTime;\n"
    str2write += "endTime              15000;\n"
    str2write += "deltaT               1;\n"
    str2write += "writeControl         timeStep;\n"
    str2write += "writeInterval        5000;\n"
    str2write += "purgeWrite           2;\n"
    str2write += "writeFormat          binary;\n"
    str2write += "writePrecision       15;\n"
    str2write += "writeCompression     off;\n"
    str2write += "timeFormat           general;\n"
    str2write += "timePrecision        8;\n"
    str2write += "runTimeModifiable    false;\n"
    str2write += "\n"
    str2write += get_openfoam_dictionary_hline() + "\n"
    str2write += "// Comments/Notes\n"
    str2write += "// \n"
    str2write += "// \n"
    str2write += get_openfoam_dictionary_hline() + "\n"
    str2write += "\n"
    
    with open(controlDictFile, "w") as wf:
        wf.write(str2write)
    return


def create_surface_feature_extract_dictionary(
        openfoamVersion,
        foamFileVersion,
        location,
        surfaceFeatureExtractDictFile,
        stlFileList,
    ):
    openfaomHeaderString = get_openfom_dictionary_header(openfoamVersion)
    
    dictName = "surfaceFeatureExtractDict"
    foamFileInfo = get_foamfile_info(
            foamFileVersion,
            location,
            dictName,
        )
    
    wspace = " "
    indent = wspace * 4
    str2write = ""
    str2write += openfaomHeaderString + "\n"
    str2write += foamFileInfo + "\n"
    str2write += get_openfoam_dictionary_hline() + "\n"
    str2write += "\n"
    for stlFilename in stlFileList:
        str2write += stlFilename + "\n"
        str2write += "{\n"
        str2write += indent + "extractionMethod            extractFromSurface;\n"
        str2write += indent + "extractFromSurfaceCoeffs\n"
        str2write += indent + "{\n"
        str2write += indent + indent + "includedAngle    150;\n"
        str2write += indent + "}\n"
        str2write += indent
        str2write += indent + "subsetFeature\n"
        str2write += indent + "{\n"
        str2write += indent + indent + "nonManifoldEdges    yes;\n"
        str2write += indent + indent + "openEdges           yes;\n"
        str2write += indent + "}\n"
        str2write += indent
        str2write += indent + "trimFeature\n"
        str2write += indent + "{\n"
        str2write += indent + indent + "minElem    0;\n"
        str2write += indent + indent + "minLen     0;\n"
        str2write += indent + "}\n"
        str2write += indent
        str2write += indent + "writeObj        yes;\n"
        str2write += "}\n"
        str2write += "\n"
    str2write +=  "\n"
    str2write += get_openfoam_dictionary_hline() + "\n"
    str2write += "// Comments/Notes\n"
    str2write += "// \n"
    str2write += "// \n"
    str2write += get_openfoam_dictionary_hline() + "\n"
    str2write += "\n"
    
    with open(surfaceFeatureExtractDictFile, "w") as wf:
        wf.write(str2write)
    return



def create_fvSchemes_dictionary(
        openfoamVersion,
        foamFileVersion,
        location,
        fvSchemesFile,
    ):
    openfaomHeaderString = get_openfom_dictionary_header(openfoamVersion)
    
    dictName = "fvSchemes"
    foamFileInfo = get_foamfile_info(
            foamFileVersion,
            location,
            dictName,
        )
    
    wspace = " "
    indent = wspace * 2
    str2write = ""
    str2write += openfaomHeaderString + "\n"
    str2write += foamFileInfo + "\n"
    str2write += get_openfoam_dictionary_hline() + "\n"
    str2write += "\n"
    str2write += "ddtSchemes\n"
    str2write += "{\n"
    str2write += "}\n"
    str2write += "\n"
    str2write += "gradSchemes\n"
    str2write += "{\n"
    str2write += "}\n"
    str2write += "\n"
    str2write += "divSchemes\n"
    str2write += "{\n"
    str2write += "}\n"
    str2write += "\n"
    str2write += "laplacianSchemes\n"
    str2write += "{\n"
    str2write += "}\n"
    str2write += "\n"
    str2write += "interpolationSchemes\n"
    str2write += "{\n"
    str2write += "}\n"
    str2write += "\n"
    str2write += "snGradSchemes\n"
    str2write += "{\n"
    str2write += "}\n"
    str2write += "\n"
    str2write += "/*\n"
    str2write += "\n"
    str2write += "wallDist\n"
    str2write += "{\n"
    str2write += "}\n"
    str2write += "\n"
    str2write += "geometry\n"
    str2write += "{\n"
    str2write += (1 * indent) + "type         highAspectRatio;\n"
    str2write += (1 * indent) + "minAspect    10;\n"
    str2write += (1 * indent) + "maxAspect    100;\n"
    str2write += (1 * indent) + "\n"
    str2write += "}\n"
    str2write += "\n"
    str2write += "*/\n"
    str2write += "\n"
    str2write += "\n"
    str2write += get_openfoam_dictionary_hline() + "\n"
    str2write += "// Comments/Notes\n"
    str2write += "// \n"
    str2write += "// \n"
    str2write += get_openfoam_dictionary_hline() + "\n"
    str2write += "\n"
    
    with open(fvSchemesFile, "w") as wf:
        wf.write(str2write)
    return


def create_fvSolution_dictionary(
        openfoamVersion,
        foamFileVersion,
        location,
        fvSolutionFile,
    ):
    openfaomHeaderString = get_openfom_dictionary_header(openfoamVersion)
    
    dictName = "fvSolution"
    foamFileInfo = get_foamfile_info(
            foamFileVersion,
            location,
            dictName,
        )
    
    wspace = " "
    indent = wspace * 2
    str2write = ""
    str2write += openfaomHeaderString + "\n"
    str2write += foamFileInfo + "\n"
    str2write += get_openfoam_dictionary_hline() + "\n"
    str2write += "\n"
    str2write += "solvers\n"
    str2write += "{\n"
    str2write += "}\n"
    str2write += "\n"
    str2write += "\n"
    str2write += "\n"
    str2write += get_openfoam_dictionary_hline() + "\n"
    str2write += "// Comments/Notes\n"
    str2write += "// \n"
    str2write += "// \n"
    str2write += get_openfoam_dictionary_hline() + "\n"
    str2write += "\n"
    
    with open(fvSolutionFile, "w") as wf:
        wf.write(str2write)
    return


def create_snappyHexMesh_dictionary(
        openfoamVersion,
        foamFileVersion,
        location,
        snappyHexMeshDictFile,
        domainInfoDict,
        loactionInMesh,
    ):
    openfaomHeaderString = get_openfom_dictionary_header(openfoamVersion)
    
    dictName = "snappyHexMeshDict"
    foamFileInfo = get_foamfile_info(
            foamFileVersion,
            location,
            dictName,
        )
    
    domainStlFilename = domainInfoDict["combined-bc-stl-filename"]
    bcList = list(domainInfoDict["bc-info"].keys())
    
    wspace = " "
    indent = wspace * 2
    str2write = ""
    str2write += openfaomHeaderString + "\n"
    str2write += foamFileInfo + "\n"
    str2write += get_openfoam_dictionary_hline() + "\n"
    str2write += "castellatedMesh    true;\n"
    str2write += "snap               true;\n"
    str2write += "addLayers          false;\n"
    str2write += "\n"
    str2write += "geometry\n"
    str2write += "{\n"
    str2write += (1 * indent) + domainStlFilename + "\n"
    str2write += (1 * indent) + "{\n"
    str2write += (2 * indent) + "type    triSurfaceMesh;\n"
    str2write += (2 * indent) + "name    domain;\n"
    str2write += (2 * indent) + "regions\n"
    str2write += (2 * indent) + "{\n"
    
    maxKeyLength = max([len(x) for x in bcList])
    for bc in bcList:
        str2write += (3 * indent) + f"{bc:{maxKeyLength + 4}} {{ name {bc}; }}\n"
        
    str2write += (2 * indent) + "}\n"
    str2write += (1 * indent) + "}\n"
    str2write += "\n"
    str2write += (1 * indent) + "/*\n"
    str2write += (1 * indent) + "refinementBox1\n"
    str2write += (1 * indent) + "{\n"
    str2write += (2 * indent) + "type searchableBox;\n"
    str2write += (2 * indent) + "min (x-min, y-min, z-min);\n"
    str2write += (2 * indent) + "max (x-max, y-max, z-max);\n"
    str2write += (1 * indent) + "}\n"
    str2write += (1 * indent) + "*/\n"
    str2write += (1 * indent) + "/*\n"
    str2write += (1 * indent) + "refinementBox2\n"
    str2write += (1 * indent) + "{\n"
    str2write += (2 * indent) + "type searchableBox;\n"
    str2write += (2 * indent) + "min (x-min, y-min, z-min);\n"
    str2write += (2 * indent) + "max (x-max, y-max, z-max);\n"
    str2write += (1 * indent) + "}\n"
    str2write += (1 * indent) + "*/\n"
    str2write += "};\n"
    str2write += "\n"
    str2write += "\n"
    str2write += "castellatedMeshControls\n"
    str2write += "{\n"
    str2write += (1 * indent) + "maxLocalCells                 3000000;\n"
    str2write += (1 * indent) + "maxGlobalCells                25000000;\n"
    str2write += (1 * indent) + "minRefinementCells            0;\n"
    str2write += (1 * indent) + "nCellsBetweenLevels           3;\n"
    str2write += (1 * indent) + "maxLoadUnbalance              0.1;\n"
    str2write += (1 * indent) + "allowFreeStandingZoneFaces    true;\n"
    str2write += (1 * indent) + "gapLevelIncrement             2;\n"
    str2write += (1 * indent) + "resolveFeatureAngle           20;\n"
    str2write += (1 * indent) + "\n"
    str2write += "\n"
    str2write += (1 * indent) + "features\n"
    str2write += (1 * indent) + "(\n"
    str2write += (2 * indent) + "{\n"
    str2write += (3 * indent) + "file     \"" + domainStlFilename.replace(".stl", ".eMesh") + "\";\n"
    str2write += (3 * indent) + "level    0;\n"
    str2write += (2 * indent) + "}\n"
    str2write += (1 * indent) + ");\n"
    str2write += "\n"
    str2write += (1 * indent) + "refinementSurfaces\n"
    str2write += (1 * indent) + "{\n"
    str2write += (2 * indent) + "domain\n"
    str2write += (2 * indent) + "{\n"
    str2write += (3 * indent) + "level             (0 0);\n"
    # str2write += (3 * indent) + "curvatureLevel    (5 0 7 -1);\n"
    str2write += (3 * indent) + "regions\n"
    str2write += (3 * indent) + "{\n"
    
    for bc in bcList:
        str2write += (4 * indent) + f"{bc:{maxKeyLength + 4}} {{ level (3 3); patchInfo {{ type {bc}; }} }}\n"
    
    str2write += (3 * indent) + "}\n"
    str2write += (2 * indent) + "}\n"
    str2write += (1 * indent) + "}\n"
    str2write += "\n"
    # str2write += (1 * indent) + "/*\n"
    str2write += (1 * indent) + "refinementRegions\n"
    str2write += (1 * indent) + "{\n"
    str2write += (2 * indent) + "// refinementBox1 { mode inside;    levels((1E15 2)); }\n"
    str2write += (2 * indent) + "// refinementBox2 { mode inside;    levels((1E15 2)); }\n"
    str2write += (1 * indent) + "}\n"
    # str2write += (1 * indent) + "*/\n"
    str2write += "\n"
    str2write += (1 * indent) + "locationInMesh (" + str(loactionInMesh[0]) + " " + str(loactionInMesh[1]) + " " + str(loactionInMesh[2]) + ");\n"
    str2write += "}\n"
    str2write += "\n"
    str2write += "snapControls\n"
    str2write += "{\n"
    str2write += (1 * indent) + "tolerance                 4;\n"
    str2write += (1 * indent) + "implicitFeatureSnap       false;\n"
    str2write += (1 * indent) + "explicitFeatureSnap       true;\n"
    str2write += (1 * indent) + "multiRegionFeatureSnap    false;\n"
    str2write += (1 * indent) + "detectNearSurfaceSnap     true;\n"
    str2write += (1 * indent) + "nSmoothPatch              5;\n"
    str2write += (1 * indent) + "nSolveIter                100;\n"
    str2write += (1 * indent) + "nRelaxIter                5;\n"
    str2write += (1 * indent) + "nFeatureSnapIter          20;\n"
    str2write += (1 * indent) + "nSmoothInternal           20;\n"
    str2write += "}\n"
    str2write += "\n"
    str2write += "addLayersControls\n"
    str2write += "{\n"
    str2write += "}\n"
    str2write += "\n"
    str2write += "meshQualityControls\n"
    str2write += "{\n"
    str2write += (1 * indent) + "minVol                 1e-20;\n"
    str2write += (1 * indent) + "minTetQuality          1e-16;\n"
    str2write += (1 * indent) + "minArea                1e-20;\n"
    str2write += (1 * indent) + "minTwist               0.05;\n"
    str2write += (1 * indent) + "minDeterminant         0.01;\n"
    str2write += (1 * indent) + "minFaceWeight          0.02;\n"
    str2write += (1 * indent) + "minVolRatio            0.01;\n"
    str2write += (1 * indent) + "minTriangleTwist       -1;\n"
    str2write += (1 * indent) + "minFlatness            0.5;\n"
    str2write += (1 * indent) + "maxNonOrtho            65;\n"
    str2write += (1 * indent) + "maxBoundarySkewness    4;\n"
    str2write += (1 * indent) + "maxInternalSkewness    1;\n"
    str2write += (1 * indent) + "maxConcave             80;\n"
    str2write += (1 * indent) + "nSmoothScale           4;\n"
    str2write += (1 * indent) + "errorReduction         0.75;\n"
    str2write += (1 * indent) + "relaxed\n"
    str2write += (1 * indent) + "{\n"
    str2write += (2 * indent) + "maxNonOrtho            75;\n"
    str2write += (2 * indent) + "maxInternalSkewness    8;\n"
    str2write += (1 * indent) + "}\n"
    str2write += "}\n"
    str2write += "\n"
    str2write += "mergeTolerance        1e-6;\n"
    str2write += "debug                 0;\n"
    str2write += "\n"
    str2write += get_openfoam_dictionary_hline() + "\n"
    str2write += "// Comments/Notes\n"
    str2write += "// \n"
    str2write += "// \n"
    str2write += get_openfoam_dictionary_hline() + "\n"
    str2write += "\n"
    
    with open(snappyHexMeshDictFile, "w") as wf:
        wf.write(str2write)
    return


def create_toposet_dictionary(
        openfoamVersion,
        foamFileVersion,
        domainInfoDict,
        location,
        topoSetDictFile,
        caseDir,
    ):
    openfaomHeaderString = get_openfom_dictionary_header(openfoamVersion)
    
    dictName = "topoSetDict"
    foamFileInfo = get_foamfile_info(
            foamFileVersion,
            location,
            dictName,
        )
    
    blockList = list(domainInfoDict["block-info"].keys())
    
    wspace = " "
    indent = wspace * 2
    str2write = ""
    str2write += openfaomHeaderString + "\n"
    str2write += foamFileInfo + "\n"
    str2write += get_openfoam_dictionary_hline() + "\n"
    
    for block in blockList:
        blockVarName = block + "STL"
        blockStlPath = "\"" + caseDir + os.sep + "constant" + os.sep + "triSurface" + os.sep + "block_" + block + ".stl" + "\";\n"
        str2write += f"{blockVarName}{indent}{blockStlPath}" + "\n"
    
    str2write += "\n"
    str2write += "// [    surface --> cell    ]\n"
    str2write += "\n"
    str2write += "actions\n"
    str2write += "(\n"
    
    for block in blockList:
        str2write += (1 * indent) + "//==== Zone : " + block + " ====//\n"
        str2write += (1 * indent) + "{\n"
        str2write += (2 * indent) + "name      " + block + "_cellSet;\n"
        str2write += (2 * indent) + "type      cellSet;\n"
        str2write += (2 * indent) + "action    new;\n"
        str2write += (2 * indent) + "source    surfaceToCell;\n"
        str2write += (2 * indent) + "sourceInfo\n"
        str2write += (2 * indent) + "{\n"
        str2write += (3 * indent) + "file                     $" + block + "STL;\n"
        str2write += (3 * indent) + "useSurfaceOrientation    true;\n"
        str2write += (3 * indent) + "outsidePoints            ();\n"
        str2write += (3 * indent) + "includeCut               false;\n"
        str2write += (3 * indent) + "includeInside            true;\n"
        str2write += (3 * indent) + "includeOutside           false;\n"
        str2write += (3 * indent) + "nearDistance             -1;\n"
        str2write += (3 * indent) + "curvature                -1;\n"
        str2write += (2 * indent) + "}\n"
        str2write += (1 * indent) + "}\n"
        str2write += "\n"
    
    str2write += ");\n"
    str2write += "\n"
    str2write += "\n"
    str2write += "\n"
    str2write += get_openfoam_dictionary_hline() + "\n"
    str2write += "// Comments/Notes\n"
    str2write += "// \n"
    str2write += "// \n"
    str2write += get_openfoam_dictionary_hline() + "\n"
    str2write += "\n"
    
    with open(topoSetDictFile, "w") as wf:
        wf.write(str2write)
    return


def setup_snappyHexMesh_case(
        openfoamVersion,
        foamFileVersion,
        domainInfoDict,
        caseSystemPath,
        stlFileList,
        domainStlBound,
        blockMeshCellSize,
        loactionInMesh,
        lengthUnit,
    ):
    
    location = "system"
    blockMeshDictFile = caseSystemPath + os.sep + "blockMeshDict"
    bBox = create_block_mesh_dict(
            openfoamVersion,
            foamFileVersion,
            location,
            blockMeshDictFile,
            domainStlBound,
            blockMeshCellSize,
            lengthUnit,
        )
    
    location = "system"
    controlDictFile = caseSystemPath + os.sep + "controlDict"
    create_control_dictionary(
            openfoamVersion,
            foamFileVersion,
            location,
            controlDictFile,
        )
    
    location = "system"
    surfaceFeatureExtractDictFile = caseSystemPath + os.sep + "surfaceFeatureExtractDict"
    create_surface_feature_extract_dictionary(
            openfoamVersion,
            foamFileVersion,
            location,
            surfaceFeatureExtractDictFile,
            stlFileList,
        )
    
    ### CASE/system/fvSchemes
    
    location = "system"
    fvSchemesFile = caseSystemPath + os.sep + "fvSchemes"
    create_fvSchemes_dictionary(
            openfoamVersion,
            foamFileVersion,
            location,
            fvSchemesFile,
        )
    
    
    ### CASE/system/fvSolution
    
    location = "system"
    fvSolutionFile = caseSystemPath + os.sep + "fvSolution"
    create_fvSolution_dictionary(
            openfoamVersion,
            foamFileVersion,
            location,
            fvSolutionFile,
        )
    
    
    
    location = "system"
    snappyHexMeshDictFile = caseSystemPath + os.sep + "snappyHexMeshDict"
    create_snappyHexMesh_dictionary(
            openfoamVersion,
            foamFileVersion,
            location,
            snappyHexMeshDictFile,
            domainInfoDict,
            loactionInMesh,
        )
    return


#---------------------------------------
#    MAIN FUNCTION
#---------------------------------------

def snappyHexMesh_from_stl(
        openfoamVersion,
        foamFileVersion,
        openFoamBashrcPath,
        workingDir,
        snappyHexInfoFile,
        blockMeshCellSize,
        loactionInMesh,
        lengthUnit,
    ):
    openfoamEnvSourceCommand = ". " + openFoamBashrcPath
    snappyHexSetupDirname = "snappyHexMesh_caseDir"
    caseDir = workingDir + os.sep + snappyHexSetupDirname
    caseSystemPath = caseDir + os.sep + "system"          
    
    with open(snappyHexInfoFile, "r") as shif:
        domainInfoDict = json.load(shif)
        print("\n" + "-"*40)
        print("snappyHexMesh process input loaded!")
    
    ### Clean old log files
    subprocess.run(
            "rm -f " + "*.log",
            cwd = workingDir, 
            shell = True
        )
    
    ### Clean old snappyHex case directory
    subprocess.run(
            "rm -fr " + caseDir,
            cwd = workingDir, 
            shell = True
        )
    
    initiate_snappyHex_case_directory(
            domainInfoDict,
            caseDir,
        )
    
    triSurfaceDir = caseDir + os.sep + "constant" + os.sep + "triSurface"
    stlFileList = populate_triSurface_directory(
            domainInfoDict,
            caseDir,
            triSurfaceDir,
        )
    
    domainStlFile = domainInfoDict["snappyhex-ready-stl-dir"] + os.sep + domainInfoDict["combined-bc-stl-filename"]
    domainStlBound = extract_domain_stl_information(
            domainStlFile,
            triSurfaceDir,
        )
    
    setup_snappyHexMesh_case(
            openfoamVersion,
            foamFileVersion,
            domainInfoDict,
            caseSystemPath,
            stlFileList,
            domainStlBound,
            blockMeshCellSize,
            loactionInMesh,
            lengthUnit,
        )
    
    prepareSTL(
            caseDir,
            openfoamEnvSourceCommand,
        )
    
    location = "system"
    topoSetDictFile = caseSystemPath + os.sep + "topoSetDict"
    create_toposet_dictionary(
            openfoamVersion,
            foamFileVersion,
            domainInfoDict,
            location,
            topoSetDictFile,
            caseDir,
        )
    
    ### RUN - blockMesh
    print("\n")
    print("-"*40)
    print("Running \"blockMesh\" ... ... ...")
    blockMeshStartTime = time.time()
    result = subprocess.run(
            openfoamEnvSourceCommand + " && " + "blockMesh > log_blockMesh.log",
            cwd = caseDir,
            shell = True,
        )
    blockMeshFinishTime = time.time()
    
    ### RUN - snappyHexMesh
    print("\n")
    print("-"*40)
    print("Running \"snappyHexMesh\" ... ... ...")
    snappyHexMeshStartTime = time.time()
    result = subprocess.run(
            openfoamEnvSourceCommand + " && " + "snappyHexMesh > log_snappyHexMesh.log",
            cwd = caseDir,
            shell = True,
        )
    snappyHexMeshFinishTime = time.time()
    
    ### RUN - topoSet
    print("\n")
    print("-"*40)
    print("Running \"topoSet\" ... ... ...")
    topoSetStartTime = time.time()
    result = subprocess.run(
            openfoamEnvSourceCommand + " && " + "topoSet > log_topoSet.log",
            cwd = caseDir,
            shell = True,
        )
    topoSetFinishTime = time.time()
    
    
    str2print =  "\n\n" + "-"*40 + "\n"
    str2print += "Execution time \n"
    str2print += "-"*40 + "\n"
    str2print += f"blockMesh     : {blockMeshFinishTime - blockMeshStartTime : >10.4} [sec]\n"
    str2print += f"snappyHexMesh : {snappyHexMeshFinishTime - snappyHexMeshStartTime : >10.4} [sec]\n"
    str2print += f"topotSet      : {topoSetFinishTime - topoSetStartTime : >10.4} [sec]\n"
    str2print += "\n"
    str2print += "-"*40 + "\n"
    str2print += "\n"
    str2print += "Process complete !!!"
    print(str2print)
    
    return

#---------------------------------------

if __name__ == "__main__":
#     workingDir = ""
#     openfoamVersion = "v2412"
#     foamFileVersion = "2.0"
#     openFoamBashrcPath = ""
#     lengthUnit = "mm"
#     blockMeshCellSize = 2
#     loactionInMesh = (0.0, 0.0, 0.0)
#     snappyHexInfoFilename = "snappyHexInfo.json"
#     snappyHexInfoFile = workingDir+ os.sep + snappyHexInfoFilename 
    wspace = ""
    workingDir = os.environ["working_dir"]
    openfoamVersion = os.environ["openfoam_version"]
    foamFileVersion = os.environ["foamfile_version"]
    openFoamBashrcPath = os.environ["openfoam_bashrc_path"]
    lengthUnit = os.environ["geometry_length_unit"]
    blockMeshCellSize = float(os.environ["blockmesh_size"])
    loactionInMeshStr = os.environ["location_in_mesh"]
    loactionInMesh = [float(x) for x in loactionInMeshStr.replace(wspace, "").split(",")]
    snappyHexInfoFilename = os.environ["input_json_filename"]
    snappyHexInfoFile = workingDir+ os.sep + snappyHexInfoFilename 
    
    print("-"*40)
    print("Location in mesh --> " + str(loactionInMesh))
    
    snappyHexMesh_from_stl(
            openfoamVersion, 
            foamFileVersion,
            openFoamBashrcPath,
            workingDir,
            snappyHexInfoFile,
            blockMeshCellSize,
            loactionInMesh,
            lengthUnit,
        )
#---------------------------------------









