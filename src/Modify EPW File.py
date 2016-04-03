"""
This script accepts an epw file and creates a new one by modifying according to the HOY input.
The HOY input accepts a list values numbers between 1 to 8760. Hours of the year corresponding to those numbers
will be kept intact in the new epw file, while for the rest of the hours the values of Diffuse Horizontal Radiation and
Direct Normal Radiation will be set to zero.
    
    Args:
        _epwFile: File path of the epw file.
        _newEpwName_: Optional name for the new, modified epw file.
        _HOY: List of hours for which the radiation values are to be included in the modified epw file.
    Returns:
        readMe!: ...
        modEpwFile: The file path for the modified epw file. This file can be used like a normal epw file.
"""
import Grasshopper.Kernel as gh
import scriptcontext as sc
import shutil

ghenv.Component.Name = "Modify EPW File"
ghenv.Component.NickName = "modifyEpw"
ghenv.Component.Message = "VER 0.0.1\n02_Apr_2016"
ghenv.Component.Category = "PSUAE"
ghenv.Component.SubCategory = "Utilities"

if not sc.sticky.has_key('ladybug_release'):
        print "You should first let the Ladybug fly..."
        w = gh.GH_RuntimeMessageLevel.Warning
        ghenv.Component.AddRuntimeMessage(w, "You should first let the Ladybug fly...")


import os,sys

if _HOY and _epwFile:
    
    hourcount = 0
    if not _newEpwName_:
        oldName = os.path.splitext(_epwFile)[0]
        _newEpwName_ = oldName+"_Modified"+".epw"
    else:
        if not _newEpwName_.lower().endswith(".epw"):
            _newEpwName_ = os.path.splitext(_newEpwName_)[0]+".epw"
        if not os.path.isabs(_newEpwName_):
            oldEpwPath = os.path.split(_epwFile)[0]
            _newEpwName_ = os.path.join(oldEpwPath,_newEpwName_)
    
    if len(_HOY) ==1:
        _HOY = _HOY[0]

        if os.path.exists(_HOY):
            with open(_HOY) as hourListFile:
                hourData = hourListFile.read().strip()
        else:
            hourData = _HOY
            
        if "," in hourData:
            _HOY = hourData.split(",")
        else:
            _HOY = hourData.split()
        

    _HOY = map(int,_HOY) #Keep this one !

    with open(_epwFile) as epw,open(_newEpwName_,'w') as epwmod:
        for ids,lines in enumerate(epw):
            try:
               year = float(lines.split(',')[0]) #throw exception in case of text string.
               hourcount = hourcount + 1
               if _HOY and hourcount in _HOY:
                   epwmod.write(lines)
               elif _HOY :
                   linesplit = lines.split(',')
                   print(linesplit[14:16])
                   linesplit[14],linesplit[15]="0","0"
                   lines = ",".join(linesplit)
                   epwmod.write(lines)
               else:
                   epwmod.write(lines)    
               
            except ValueError:
                if not ids:
                    lines = lines.split(',')
                    lines[1] = lines[1]+'Modified'

                    #Remove existing folder if it exists.
                    possibleFolderPath = " ".join(lines[1:4])
                    possibleFolderPath = possibleFolderPath.replace(" ","_")
                    ladybugFolder = sc.sticky['Ladybug_DefaultFolder']
                    existingEpwFolder = os.path.join(ladybugFolder,possibleFolderPath)
                    if os.path.exists(existingEpwFolder):
                        shutil.rmtree(existingEpwFolder)
                        
                        
                    lines = ",".join(lines)
                epwmod.write(lines)
    modEpwFile = _newEpwName_