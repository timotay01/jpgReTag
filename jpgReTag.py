import glob
import os
import sys
import argparse
import exiftool
import tkinter
from tkinter.filedialog import askdirectory
from tkinter import messagebox as mb
from tkinter import ttk
from colorama import init, Fore, Back, Style
from csv import DictReader, DictWriter
#requires: pyexiftool, pillow, defusedxml, colorama

VERSION = "v1.13.0.0"
SUPPORTED_FILES = [".jpg", ".jpeg", ".png"]



def readProjectFile():
    projects = {
        "None": [],
    }
    f = open("projectlist.txt", "r")
    data = f.readlines()
    f.close()

    for line in data:
        d = [x.strip() for x in line.split(',')]
        proj = d[0]
        if len(d) <= 1:
            projects[proj] = []
        else:
            projects[proj] = d[1:]
    #print(projects)
    return projects



class projPrompt:
    def __init__(self, master, projects):
        self.master = master
        self.projects = projects
        self.templateTags = []

        #Create window
        self.master.geometry( "300x200" )
        self.master.title("Template Project Select")

        self.label = tkinter.Label(master, text="Select a Project")
        self.label.pack(anchor=tkinter.W,padx=10)

        # Create Dropdown menu
        options = list(projects.keys())
        self.drop = ttk.Combobox(master,values=options)
        self.drop.set(options[0])
        self.drop.pack(anchor=tkinter.W,padx=10)

        # Create button, it will change label text
        self.button = tkinter.Button( master, text = "Click Here to Select", command = self.selectProj )
        self.button.pack(anchor=tkinter.W,padx=10)

        # Create Label
        self.label = tkinter.Label( master , text = " " )
        self.label.pack(anchor=tkinter.W,padx=10)

    def getTags(self):
        return self.templateTags

    def selectProj(self):
        selected = self.drop.get()
        print("show selected: " + selected)
        if selected != "None":
            self.templateTags.append(selected)
            self.templateTags.extend(self.projects[selected])
        self.master.destroy()

def performTemplatePrompt():
    root = tkinter.Tk()
    root.withdraw()
    root.update()
    dir = askdirectory(initialdir=os.path.dirname(__file__), title='Select Folder') # shows dialog box and return the path
    templateFile = os.path.basename(dir) + ".csv"
    csvFiles = glob.glob(dir + "/*.csv")
    res = "no"
    if os.path.isfile(dir + "/" + templateFile):
        print("Found a template file {}".format(templateFile))
    elif len(csvFiles) == 0:
        res = mb.askquestion('Template prompt', 'Create a Template .csv file ?')
    root.destroy()

    if res == "yes":
        projects = readProjectFile()

        root = tkinter.Tk()
        app = projPrompt(root, projects)
        root.mainloop()
        tags = app.getTags()
        print("Tags to add: {}".format(tags))

        createTemplate(dir, templateFile, tags)
        return ""

    return dir



#If column has /, \, or | then take only the rightmost data of this:
def cleanData(value):
    for ch in ["/", "\\", "|"]:
        i = value.rfind(ch)
        if i != -1:
            value = value[i+1:]
    return value

def addToDict(dict, id, key, val):
    if id not in dict:
        dict[id] = {}
    dict[id][key] = val

#Return a dictionary with key's by id.
#Each entry should be: <id>:{FilePath:somejpg, Usage:title, Tags:[tags...]
def parseCsvFiles(csvFiles):
    tagsToUpdate = {}
    #Parse all the csv files and build a dictionary
    for file in csvFiles:
        print("Reading {}".format(file))

        with open(file, encoding="utf-8-sig") as f:
            #Determine if the csv is semicolon or comma separated- supporting both types based on the first line
            first_line = f.readline()
            semis  = first_line.count(";")
            commas = first_line.count(",")
            delim = ","
            if semis > commas:
                delim = ";"

            f.seek(0,0)  #rewind
            #Read in the csv to reqList dictionary
            reqList = DictReader(f, delimiter=delim)
            row = 0
            #cycle through all 'rows' that have been read in
            for req in reqList:
                row += 1
                if 'Item Id' in req:
                    id = req['Item Id']
                elif 'FilePath' in req:
                    #No id in the csv (created from template), invent an id
                    id = "T" + str(row)
                else:
                    print(Style.BRIGHT + Fore.YELLOW + "Unexpected no Item Id or FilePath columns in csv")
                    break
                if 'Usage' not in req:
                    req['Usage'] = ""
                
                #print("{}".format(req))
                #cycle through all the columns
                for col in req:
                    #Get the value for this column
                    value = req[col]
                    #    print("[{}] = {}".format(id,value))

                    #Determine which columns are of interest:
                    if col == 'Item Id':
                        continue #Id => Ignore
                    elif col == 'FilePath':
                        addToDict(tagsToUpdate, id, "FilePath", os.path.basename(value))
                        continue  #FilePath and Id => Ignore
                    elif col == 'Description':
                        addToDict(tagsToUpdate, id, 'Description', value)
                    elif col == 'Usage':
                        #Usage from exported csv, Description from Template csv
                        #csv Usage or Description column => Usage
                        if not value:
                            value = ""
                        #split it, clean it, and create a single new Usage key
                        values = value.split(",")
                        newValue = ""
                        for v in values:
                            newValue += cleanData(v) + ','
                        newValue = newValue[:-1]  # strip last comma
                        addToDict(tagsToUpdate, id, 'Usage', newValue)
                    else:
                        #csv People (or any other) columns => Tags
                        if not value:
                            continue
                        if id not in tagsToUpdate:
                           tagsToUpdate[id] = {}
                        if 'Tags' not in tagsToUpdate[id]:
                            tagsToUpdate[id]['Tags'] = []
                        #split it, clean it and store each one as a new tag key
                        values = value.split(",")
                        for v in values:
                            tagsToUpdate[id]['Tags'].append(cleanData(v))
    return tagsToUpdate

def createTemplate(dir, templateFile, tags):
    files = []
    outData = []
    for ext in SUPPORTED_FILES:
        files.extend(glob.glob(dir + "/*" + ext))

    with open(dir + "/" + templateFile, 'w', newline='') as csvFile:
        header = ["FilePath"]
        tagCols = max(len(tags), 20)  # always create 20 columns minimum
        for t in range(0, tagCols):
            header.append("Tag" + str(t+1))

        writer = DictWriter(csvFile, fieldnames=header)
        writer.writeheader()
        for i in range(0, len(files)):
            files[i] = os.path.basename(files[i])
            rowdata = {"FilePath" : files[i]}
            for t in range(0, len(tags)):
                rowdata["Tag" + str(t+1)] = tags[t]
            writer.writerow(rowdata)

    print("Created: " + templateFile)
    return templateFile


def testFileIsPng(file):
    ret = False
    with open(file, "rb") as f:
        data = f.read(4)
        if data == b'\x89PNG':
            ret = True
    return ret

def updateJpgFile(et, file, description, tags, verbose):
    status = ""
    #Time to update it see:
    #https://stackoverflow.com/questions/77998586/how-to-correctly-get-and-update-title-comments-and-tags-in-jpeg-metadata-using


    #clean microsoft tags, and IPTCDigest
    ret = et.execute('-overwrite_original', '-XMP-microsoft:all=', '-m', file)
    ret = et.execute('-overwrite_original', '-if' '$IPTCDigest', '-IPTCDigest=', file)
    currentTags = et.get_tags(file,['XMP-dc:Title','XMP-dc:Subject','XMP-dc:Description'])  #note returns keys as XMP:Title and XMP:Subject (if they exist)
    if verbose:
        print(currentTags)

    if 1:  # always attempt to Description which includes "Usage:" even if nothing specified by input
        title = description
        if 'XMP:Title' not in currentTags[0] or currentTags[0]['XMP:Title'] == None:
            titleTag = r'-XMP-dc:Title=' + title
            descriptionTag = r'-XMP-dc:Description=' + title
        elif title in currentTags[0]['XMP:Title']:
            if verbose:
                print("title '{}' exists- skipping".format(title))
            titleTag = None
        else:
            titleTag = r'-XMP-dc:Title<${XMP-dc:Title}; ' + title
            if 'XMP:Description' not in currentTags[0]:
                descriptionTag = r'-XMP-dc:Description<${XMP-dc:Title}; ' + title
            else:
                descriptionTag = r'-XMP-dc:Description<${XMP-dc:Description}; ' + title
        if titleTag:
            if verbose:
                print("adding title: " + title)
            ret = et.execute('-overwrite_original', titleTag, descriptionTag, file)
            if ret.startswith("1"):
                status += " title"
            else:
                print(Style.BRIGHT + Fore.RED + "ERROR title " + ret.rstrip())

    if tags:
        tagStatus =""
        for tag in tags:
            if 'XMP:Subject' in currentTags[0] and tag in currentTags[0]['XMP:Subject']:
                if verbose:
                    print("tag: {} exists- skipping".format(tag))
                continue
            subject = r'-XMP-dc:Subject+=' + tag
            h_subject = r'-XMP-lr:HierarchicalSubject+=' + tag
            if verbose:
                print("adding tag: {}".format(tag))
            ret = et.execute('-overwrite_original', subject, h_subject, file)
            if ret.startswith("1"):
                tagStatus = " tag"
            else:
                print(Style.BRIGHT + Fore.RED + "ERROR subject " + ret.rstrip())
                break
        status += tagStatus
    if 1: #always modify the copywrite
        copyright = 'Global Partnerlink Society (o/a OneBook)'
        if verbose:
            print("adding copyright: {}".format(copyright))
        xmp_rights = '-XMP-dc:Rights=' + copyright
        exif_cw = '-Exif:Copyright=' + copyright
        ret = et.execute('-overwrite_original', '-m', xmp_rights, exif_cw, file)
        if ret.startswith("1"):
            status += " copyright"
        else:
            print(Style.BRIGHT + Fore.RED + "ERROR copyright " + ret.rstrip())
    if status:
        print("upated: " + status)
    return 0


def main():
    # Initializes Colorama
    init(autoreset=True)
    print(Style.BRIGHT + Fore.GREEN + "jpgReTag tool " + VERSION)

    isWinClick = False
    # If the program was started via the GUI (i.e. by double-clicking the executable),
    if (os.name == 'nt' and not 'PROMPT' in os.environ):
      isWinClick = True
      print("windows run")

    parser = argparse.ArgumentParser(description='A tool to retag/retitle a batch of jpg or png from an input csv')
    parser.add_argument('--path=', dest='path', required=False,                     help='specify an alternate directory, default is current directory')
    parser.add_argument('--id=',   dest='id',   required=False,                     help='specify a single id to update format is: id,usage,tag,tag...')
    parser.add_argument('-v', dest='verbose', action='store_true', required=False,  help='verbose logging')
    args = parser.parse_args()

    jpgFiles = []
    csvFiles = []
    dir = "."
    if args.path:
        dir = args.path
    else:
        dir = performTemplatePrompt()
        if dir == "":
           input('Press ENTER to close')
           return
    csvFiles = glob.glob(dir + "/*.csv")
    
    jpgFiles = []
    for ext in SUPPORTED_FILES:
        jpgFiles.extend(glob.glob(dir + "/*" + ext))

    for i in range(0, len(jpgFiles)):
        file = jpgFiles[i]
        fsplit = os.path.splitext(file)
        ext = fsplit[1]
        if ext != ".png":
            if testFileIsPng(file):
                newName = fsplit[0] + ".png"
                print("Detected {} is PNG renaming to {}".format(os.path.basename(file), os.path.basename(newName)))
                os.rename(file, newName)
                jpgFiles[i] = newName

    tagsToUpdate = {}

    if args.id:
        csvFiles = []
        data = args.id.split(",")
        if len(data) < 3:
            print("--id= requires at least: id,usage,tag no updates will be performed")
        else:
            id = data[0]
            tagsToUpdate[id] = {"Usage":data[1], "Tags":[]}
            for i in range(2, len(data)):
                tagsToUpdate[id]['Tags'].append(data[i])
    else:
        tagsToUpdate = parseCsvFiles(csvFiles)


    #Show all the parsed csv data to be added
    #print(tagsToUpdate)

    print("Requesting {} files to update".format(len(tagsToUpdate)))
    print("Examining {} files".format(len(jpgFiles)))

    with exiftool.ExifToolHelper() as et:
        et.check_execute = False
        for id in tagsToUpdate:
            print("{} : {}".format(id, tagsToUpdate[id]))
            filePath = ""
            if id.startswith('T'):
                filePath = tagsToUpdate[id]['FilePath']
                fileToMatch = filePath
            else:
                fileToMatch = "-" + id + "."
            foundIndex = -1
            for i in range(0, len(jpgFiles)):
                file = jpgFiles[i]
                if fileToMatch in file:
                    foundIndex = i
                    break
            if foundIndex == -1:
                print(Style.BRIGHT + Fore.YELLOW + "WARNING no file for entry {} id={}".format(filePath, id))
                continue

            file = jpgFiles[foundIndex]
            description = ""
            tagsToAdd = []
            if 'Description' in tagsToUpdate:
                description += tagsToUpdate[id]['Description']
            if 'Usage' in tagsToUpdate[id]:
                description += "Usage:" + tagsToUpdate[id]['Usage']
            if 'Tags' in tagsToUpdate[id]:
                tagsToAdd = tagsToUpdate[id]['Tags']
            updateJpgFile(et, file, description, tagsToAdd, args.verbose)
            del jpgFiles[foundIndex]

    if len(jpgFiles):
        print(Style.BRIGHT + Fore.YELLOW + "The following {} files where not modified:\n{}".format(len(jpgFiles),"\n".join(jpgFiles)))

    # prevent the console window from closing automatically.
    if isWinClick:
        input('Press ENTER to close')


if __name__ == '__main__':
    main()