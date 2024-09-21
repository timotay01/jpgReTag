jpgReTag tool:
Examines a dominion exported csv file(s) (either comma or semicolon separated) for the following columns:
'Item Id', 'Description' 'Usage', (others EXCEPT 'FilePath' will be taken as tags)
Updates all matching jpg,jpeg,png files (based on the item id) existing in the filename in format: SomeFile-1234.jpg (id=1234)

When to install the tool on a new pc the following 3 files and 1 folder should be downloaded:
runscript.bat
projectlist.txt
taglist.txt
jpgReTag.dist\*

Simply run runscript.bat and when prompted select the directory to retag all files in that directory.
If the directory contains a dominion exported .csv it will be used to determine which files from the id should be updated.
If no .csv exists in the folder then tool will prompt if wishing to create a template .csv
If a template .csv (with optional modifications) exists, then the FilePath rather than Item Id column identifies which files to update.
note: the template .csv will create the following columns:
'FilePath', 'Tag1', 'Tag2'....
The template .csv may then be further editted to add columns: 'Description' 'Usage' or additional tag columns.
If BOTH columns 'Description' and 'Usage' columns exist, then in the image file will get: "Some new Description Usage: FY2024"  

The script relies on an underlying tool exiftool.exe for modifying image file metadata: https://exiftool.org/

Dealing with errors (script crashes some issue resulting in uncompleted job):
Either use the runscript.bat OR:
-launch command prompt
-cd into the directory where script.exe resides
-run it: script.exe -v
-additional arguments may be added run with -h for more info
Running from cmd prompt will allow to see any errors without closing the cmdprompt window.


General notes/info for running the exiftool separately
To set tags:
exiftool.exe "-XMP-dc:Subject+=Timtest" "-XMP-lr:HierarchicalSubject+=Timtest" <file>

To append to existing title: '; Usage:Timtet'
exiftool.exe "-XMP-dc:Title<${XMP-dc:Title}; Usage:Timtest" <file>

Some files have microsoft tags that prevent updating (they're corrupted) so simply to wipe them first.
error was: Warning = [minor] Fixed incorrect URI for xmlns:MicrosoftPhoto_1_
exiftool.exe -overwrite_original -XMP-microsoft:all= -m

Fix issues related to IPTCDigest
error was: Warning: IPTCDigest is not current. XMP may be out of sync
exiftool -if "$IPTCDigest" -IPTCDigest= "FY2007-DaveThormoset&Nelson-2647.jpg"

Fix issues with jpg that are actually png:
exiftool.exe -ext jpg "-filename<%f.$fileTypeExtension" timtest

Change title & description
exiftool.exe -overwrite_original "-XMP-dc:Title<${XMP-dc:Title}; Usage:Timtest" "-XMP-dc:Description<${XMP-dc:Description}; Usage:Timtest"

Set tags
exiftool.exe -overwrite_original "-XMP-dc:Subject+=Timtest" "-XMP-lr:HierarchicalSubject+=Timtest"

Read both title & tags for all png files in a dir:
exiftool.exe -XMP-dc:all test-pngs\*.png

In general the following is the mappings:
(jpg) XMP:Title & XMP:Description => (windows) Title & Subject => (filecamp) Description
(jpg) XMP:Subject => (windows) Tags => (Filecamp) Tags
(jpg) XMP:Rights => (windows) CopyWrite => (Filecamp) CopyWrite

How to create new exe with pyinstaller:
pyinstaller --onefile --name=script jpgReTag.py

How to create new exe with nuitka (pyinstaller exe seem to get flagged as virus):
pip install nuitka
create all files into jpgReTag.dist\ 
python -m nuitka --product-name=script --product-version=1.15 --file-description=jpgReTagTool --enable-plugin=tk-inter --standalone -o script jpgReTag.py
xcopy /e /k /h /i exiftool jpgReTag.dist\exiftool

Change History:
v1.15
Fix actual image retagging (had testcode to skip in v1.14), move exiftool to subfolder to make things less confusing
v1.14
Merge dropdown menuing into template creation.
After template options via gui selected write the template csv, and prompt if image retagging should be executed
If template csv found prompt if wishing to re-edit it
If template csv used for retagging, rename to template-tagged.csv (its been used)
v1.13
Template.csv always to have Tag1 - Tag20 columns
v1.12
Add dropdown selection of projects read in from projectlist.txt for adding to the template.csv
v1.11
Add color for warnings & errors when running
Force copyright updates on files having: 'Warning: [minor] Bad SubIFD0 SubDirectory start' from exiftool
Cmdline with no --path specified will prompt for folder to run on
Only prompt for template csv creation if no csv files found in folder
v1.10
Fix not adding Usage: even if its blank from csv
Add updating copyright tags
v1.09
Fixed some general issues with Usage/Subject not updating from v1.08
Added renaming of non-png files that actually are .png
Fixed updating files that only had title and no description
v1.08
Add a warning if csv specifies things to update and a corresponding file wasnt found
After selecting the folder, if no .csv present then prompt to create a template csv file.
If using the template csv file for updating- 
Column: FilePath => the files to tag
Column: Usage => Adds Usage/Description to .jpgs
Comumn: Tags1 = > Tags (for more than one separate them with / or |)
Additional columms maybe added but ensure the headings are unique (ie Tags2, Tags3...)
v1.07
Added support for .png files
v1.06
Added support for .jpeg files
v1.05
Added popup to prompt for a directory