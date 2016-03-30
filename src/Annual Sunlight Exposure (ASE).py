

"""
Perform ASE calculations, Calculate ASE and generate relevant time series data.

_
    Args:
        _studyFolder: Location of the Honeybee folder where the files for Daysim based Annual daylighting calculations exist.
        _epwFile_: File path for epw file.If not specified the code will guess the path from the study folder.
        _materialsFile_: File path for the radiance materials file. This file should contain all the material definitions for the space being considered. If not specified the code will guess the path from the study folder.
        _geometryFile_: File path for the radiance geometry file.If not specified the code will guess the path from the study folder.
        _ptsFile_: File path for the grid-points file.If not specified the code will guess the path from the study folder.
        _illumThreshold_: Illuminance threshold for ASE calculations. Default is 1000 lux as per IES LM 83-12
        _hoursThreshold_: Number of hours per grid point to be considered for ASE calculations. Default is 250 hours lux as per IES LM 83-12
        _rcontribSettings_: Custom settings for running rcontrib. Should be in the format: -ad x -dc y -n z where x,y and z are ambient divisions,accuracy of direct calculations and number of processors respectively. Example: -ad 10000 -dc 1 -n 4
        _run: Set this to True to start the calculations.
    Returns:
        annual_ASE_analysis_file: The time-series illuminance file generated by the calculations. This file is compatible with the existing daysim, honeybee file formats.
        ASE: ASE value calculated as per _hoursThreshold_ and _illumThreshold_ values.
        hourlySummary: A list of 8760 numbers. Each number is the fraction of the total grid points that are equal to or above _illumThreshold_ at the hour cooresponding to that number. Can be visualized using the Ladybug 3-d chart.
        gridSummary: A list of numbers that represents the fraction of total hours(3650) for which a grid point is equal to or above _illumThreshold_. Can be visualized using Ladybug ReColor Mesh.
        sunPathGeometry: Radiance definition for the files generated for the sunpath calculations. Can be used for visualizing the sunpath in a radiance rendering.
"""



from __future__ import print_function
import os
import sys
import subprocess as sp

ghenv.Component.Name = "Annual Sunlight Exposure (ASE)"
ghenv.Component.NickName = "ASE"
ghenv.Component.Message = "Ver Alpha\n14_Dec_2015"
ghenv.Component.Category = "PSUAE"
ghenv.Component.SubCategory = "Daylighting"



#Storing cwd for resetting it later.
currfolder = os.getcwd()


#If no values are provided for a file set them as per the start or end variable. If values are provided, then accept those.
def setvalue(variable,filename,start=None,end=None):
    if variable:
        assert os.path.exists(variable),"The file %s does not exist"%variable
    else:
        assert os.path.exists(filename),"The file %s does not exist"%filename
        if start:
            if filename.startswith(start):
                return os.path.abspath(filename)
        elif end:
            if filename.endswith(end):
                return os.path.abspath(filename)
        return os.path.abspath(filename)
    

#illumThreshold and hoursThreshold as per LM 83-12 are 1000 and 250. They can be changed to a custom level.
if _illumThreshold_ is None:
    _illumThreshold_ = 1000 

if _hoursThreshold_ is None:
    _hoursThreshold_ = 250 


if _run:
    if _studyFolder:
        if os.path.isdir(_studyFolder):
            os.chdir(_studyFolder)
            #Create ase folder if it does not already exist. Will overwrite existing files.
            if not os.path.exists('ase'):
                os.mkdir('ase')
        
        #iterate through the files in the study folder and set values. If user has specified values, set that.
        for files in os.listdir(_studyFolder):
            if files.endswith("epw"):
                _epwFile_ = setvalue(_epwFile_,files,end='epw')
            
            if files.startswith('Daysim_material'):
                _materialsFile_ = setvalue(_materialsFile_,files,start='Daysim_material')
            
            if files.startswith('Daysim') and files.endswith('.rad') and 'material' not in files:
                _geometryFile_ = setvalue(_geometryFile_,files)
            
            if files.endswith('.pts'):
                _ptsFile_ = setvalue(_ptsFile_,files,end='.pts')
        
            
    #Check that all the required files exist.
    for files,varnames in ((_epwFile_,'_epwFile_'),(_materialsFile_,'_materialsFile_'),
    (_geometryFile_,'_geometryFile_'),(_ptsFile_,'_ptsFile_')):
        assert os.path.exists(files),"The value for {} is {}. It should be a file".format(varnames,files)
        print("{}:\t {}".format(varnames,files))
    
    os.chdir('ase')
    
    #Create analemma geometry and sky matrix.
    os.system('dxanalemma -f {} -m sunmat.rad -g sungeo.rad -s suns.smx'.format(_epwFile_))
    
    #get the list of suns for rcontrib.Create a separate rad file containing the sun material and sun files.
    with open('sunlist.txt','w') as sunfile,open('sunpaths.rad','w') as sunpaths:
        with open('sunmat.rad') as sunmat:
            for lines in sunmat:
                print(lines.split()[2],file=sunfile)
                print(lines.strip(),file = sunpaths)
        with open('sungeo.rad') as sungeo:
            for lines in sungeo:
                print(lines.strip(),file = sunpaths)

    #This can be used in the future to see where the analemma patterns are.
    sunPathGeometry = os.path.abspath('sunpaths.rad')
    
    
    #create and run batch file.
    with open('ase.bat','w') as asebatfile:
        
        print('oconv {} {} sunmat.rad sungeo.rad > ase.oct'.format(_materialsFile_,_geometryFile_),file=asebatfile)
        
        #if rcontrib settings have been provided by the user, use those or else accept default values of ad = 10000, dc =1 and n =4
        if _rcontribSettings_:
            print('rcontrib -ab 0 {} -I -M {}  ase.oct< {} > ase.rct'.format(_rcontribSettings_,os.path.abspath('sunlist.txt'),_ptsFile_),file=asebatfile)
        else:
            ad,dc,n = 10000,1,4
            print('rcontrib -ab 0 -ad {} -I -M {} -dc {} -n {} ase.oct< {} > ase.rct'.format(ad,os.path.abspath('sunlist.txt'),dc,n,_ptsFile_),file=asebatfile)
        
        print('dctimestep -h -n 8760 ase.rct suns.smx > dct.mtx',file=asebatfile)
        
        print('rcollate -h -oc 1 < dct.mtx > rcol.mtx',file=asebatfile) 
            #rcalc
        print("rcalc -e $1=179*(.265*$1+.670*$2+.065*$3) rcol.mtx > rcalc.mtx",file=asebatfile)
        
        #rcollate
        print('rcollate -ir 7884000 -or 900 -h -fa1 -oc 8760 -ic 1 < rcalc.mtx > asetemp.ill',file=asebatfile)
        
        #rcollate, final.
        print('rcollate -h -fa1 -t < asetemp.ill>ase.ill',file=asebatfile)
    
    #run batch file.
    sp.call('ase.bat')

    hourlySummary = []
    gridSummary = []
    asearray = []
    with open('ase.ill') as asefile:
        for lines in asefile:
            lines = lines.strip().split()
            lines = [round(float(illvalue)) for illvalue in lines]
            ptsAboveThreshold = len([pt for pt in lines if pt >= _illumThreshold_])
            hourlySummary.append(ptsAboveThreshold/len(lines))
            
            if not gridSummary:
                gridSummary = [0]*len(lines)
            
            for idx,luxlevel in enumerate(lines):
                if luxlevel >= _illumThreshold_:
                    gridSummary[idx] += 1
            
            lines = " ".join(map(str,lines))
            asearray.append(lines)
    
    ASE = len([gridpt for gridpt in gridSummary if gridpt>=_hoursThreshold_])/len(gridSummary)
    
    idx = 0
    with open(_epwFile_) as epwfile,open('ase.ill','w') as asefile:
        for lines in epwfile:
            
            try:
                lines = lines.strip().split(',')
                year = float(lines[0])
                timestamp = " ".join(map(str,lines[1:4]))
                asedata = timestamp + ' ' + asearray[idx]
                print(asedata,file=asefile)
                idx +=1
            except ValueError:
                pass
    annual_ASE_analysis_file = os.path.abspath('ase.ill')            
    os.chdir(currfolder)
