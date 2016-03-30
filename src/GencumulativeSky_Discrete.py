"""
    Create a skyfile using gencumulative sky.
    
    Args:
        _epwFile: Weather file
        _analysisPeriod_: Use the Ladybug analysis period app
        _hourList_: This should be a list of integers or floating point numbers between 1 and 8760
        _customName_: Specify a custom name for the cal file. If not specified, the script will add a timestamp to filename
        _run: Boolean toggle
        skyFilePath_cal: Pathname of the sky.cal file.
"""
from __future__ import print_function

import scriptcontext as sc
import os,glob
import subprocess as sp
import Grasshopper.Kernel as gh
import time


ghenv.Component.Name = "GencumulativeSky_Discrete"
ghenv.Component.NickName = "GenCSkyDiscr"
ghenv.Component.Message = "VER 0.0.1\n29_Mar_2016"
ghenv.Component.Category = "PSUAE"
ghenv.Component.SubCategory = "Daylighting"


workdir =  sc.sticky["Honeybee_DefaultFolder"]
psudir = os.path.join(workdir+'psuae')
gencskypath = os.path.join(workdir,"gencumulativesky.exe")

if not os.path.exists(psudir):
    os.makedirs(workdir+'\psuae')

_hourList_ = sorted(set(_hourList_)) #remove this later....for testing purposes only
_hourList_ = map(int,_hourList_) #Keep this one !

hourcount = 0

if _customName_:
    stamp = _customName_
else:
    stamp = time.strftime("%d_%b_%H_%M_%S")
newepw = os.path.join(psudir,"{}.epw".format(stamp)) #change this later.


locName=altitude=longitude =timezone =  None

if _analysisPeriod_:
    stmonth,stday,sthr = _analysisPeriod_[0]
    endmonth,endday,endhr = _analysisPeriod_[1]
else:
    stmonth,stday,sthr,endmonth,endday,endhr=1,1,1,12,31,24

if _run:
    if os.path.exists(gencskypath):
         if _epwFile:
            try:
                with open(_epwFile) as epw,open(newepw,'w') as epwmod:
                    for ids,lines in enumerate(epw):
                        try:
                           year = float(lines.split(',')[0]) #throw exception in case of text string.
                           hourcount = hourcount + 1
                           if _hourList_ and hourcount in _hourList_:
                               epwmod.write(lines)
                           elif _hourList_ :
                               linesplit = lines.split(',')
                               linesplit[14],linesplit[15]="0","0"
                               lines = ",".join(linesplit)
                               epwmod.write(lines)
                           else:
                               epwmod.write(lines)    
                           
                        except:
                            if not ids:
                                locinfo = lines.split(',')
                                locName,latitude,longitude,timezone = locinfo[1].split()[0],float(locinfo[6]),float(locinfo[7]),float(locinfo[8])
                                timezone = timezone*-15.0
                                longitude = -longitude
                            epwmod.write(lines)
                        
            except:
                throw("The epw file appears to be corrupted")
            
            
            
    else:
        throw("GenCumulativeSky.exe was not found in the Honeybee folder")
        
    
    
    
    
    
    
    
    
    calfilepath = os.path.join(psudir,"{}_{}.cal".format(stamp,locName))
    
    cmskydef="{} +s1 -a {} -o {} -m {} -p -E -time {} {} -date {} {} {} {} {} > {}".format(gencskypath,latitude,longitude,timezone,sthr,endhr,stmonth,stday,endmonth,endday,newepw,calfilepath)
    
    #run cumulative sky
    sp.call(cmskydef,shell=True)
    
    time.sleep(3) #buffer time for writing.
    skyFilePath_cal = calfilepath
    

    
    
    skystring = """void brightfunc skyfunc
2 skybright {}
0
0
skyfunc glow sky_glow
0
0
4 1 1 1 0
sky_glow source sky
0
0
4 0 0 1 180""".format(calfilepath)
    
    with open(os.path.splitext(calfilepath)[0]+'.sky','w') as skyfile:
        print(skystring,file=skyfile)
    
    skyFilePath = os.path.splitext(calfilepath)[0]+'.sky'
    
    
    def throw(msg):
        e = msg
        et = gh.GH_RuntimeMessageLevel.Error
        ghenv.Component.AddRuntimeMessage(et,e)