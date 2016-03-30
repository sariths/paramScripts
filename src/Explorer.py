
"""
Locate a file/directory in windows explorer.
If a file-path is provided then the directory containing the file is opened.
If a folder-path is provided then the folder containing that folder is opened.
-
Args:
    _destination: File path or Directory path
"""
ghenv.Component.Name = "Explorer"
ghenv.Component.NickName = 'explorer'
ghenv.Component.Message = 'Ver 0.0.1\n29_Mar_2016'
ghenv.Component.Category = "PSUAE"

try: ghenv.Component.AdditionalHelpFromDocStrings = "3"
except: pass
import Grasshopper.Kernel as gh
import os
import subprocess
def main(location):
    if location:
        try:
            location = location.replace('"',"") #Just in case the user enters a hardcoded path.
            location = location.strip() #Remove all the whitespaces.
            assert os.path.exists(location) #Check if the path exists at all or else throw an assertion error.
            foldername = os.path.dirname(location)
            subprocess.Popen('explorer.exe '+foldername)
        except AssertionError:
            raise Exception("The specified path %s does not exist.\nPlease check for white-spaces or other characters in your path name."%location)
        except:
            raise Exception("The input: %s is not a valid path.\nA valid path would be something like D:\Honeybee\Results."%location)
    else:
        raise Exception("The input is empty")

main(_destination)