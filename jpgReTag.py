import glob
import os
import sys
import argparse
import exiftool
import tkinter
from tkinter.filedialog import askdirectory
from tkinter import ttk, messagebox, simpledialog
from PIL import Image, ImageTk
from colorama import init, Fore, Back, Style
from csv import DictReader, DictWriter
#requires: pyexiftool, pillow, defusedxml, colorama

VERSION = "v1.15.0.0"
SUPPORTED_FILES = [".jpg", ".jpeg", ".png"]
MAX_TAGS = 15
colorPerm  = "blue"
colorIndiv = "#f38b3c"

#Expect file to have lines with: project,tag1,tag2...
def readProjectFile():
    projects = { "None": [] }
    f = open("projectlist.txt", "r")
    data = f.readlines()
    f.close()
    for line in data:
        line = line.strip()
        d = line.split(",")
        proj = d[0].strip()
        projects[proj] = []
        for i in range(1,len(d)):
            projects[proj].append(d[i].strip())
    #print(Projects)
    return projects

#Expect file to have one tag per line
def readTagList():
    tags = []
    with open("taglist.txt") as file:
        for line in file:
            tag = line.strip()
            if tag:
                tags.append(tag)
    return tags


def getImageFiles(dir):
    files = []
    for ext in SUPPORTED_FILES:
        files.extend(glob.glob(dir + "/*" + ext))
    return files

class projPrompt:
    def __init__(self, root):
        self.root = root
        self.projects = readProjectFile()
        self.selectedProject = ""
        self.projectTags = []

        #Create window
        root.geometry( "300x200" )
        root.title("Template Project Select")

        self.label = tkinter.Label(root, text="Select a Project")
        self.label.pack(anchor=tkinter.W,padx=10)

        # Create Dropdown menu
        options = list(self.projects.keys())
        self.drop = ttk.Combobox(root,values=options)
        self.drop.set(options[0])
        self.drop.pack(anchor=tkinter.W,padx=10)

        # Create button, it will change label text
        self.button = tkinter.Button( root, text = "Click Here to Select", command = self.selectProj )
        self.button.pack(anchor=tkinter.W,padx=10)

    def getProject(self):
        return self.selectedProject

    def getTags(self):
        return self.projectTags

    def selectProj(self):
        selected = self.drop.get()
        #print("selected: " + selected)
        if selected != "None":
            self.selectedProject = selected
            self.projectTags.append(selected)
            self.projectTags.extend(self.projects[selected])
        self.root.destroy()



class projTemplate:
    def __init__(self, root, dir, projectTags, existingTagInfo):
        self.root = root
        self.Projects = readProjectFile()
        self.ImgFiles = getImageFiles(dir)
        self.ImgIndex = 0
        self.PermTags = projectTags.copy()
        self.ExtraTags = readTagList()
        self.dropbox = [ None ] * 3
        self.dropBtn = [ None ] * 3
        self.TagLabels = []

        if existingTagInfo == None:
            self.TagsToUpdate = {}
            for i in range(0, len(self.ImgFiles)):
                id = "T{}".format(i+1)
                filename = os.path.basename(self.ImgFiles[i])
                self.TagsToUpdate[id] = {"FilePath":filename, "Tags":projectTags.copy()}
        else:
            self.TagsToUpdate = existingTagInfo
            print("{}".format(self.TagsToUpdate))

        # Create object
        root.geometry( "650x580" )
        root.title("Template Creation Project: {}".format(projectTags[0]))

        # Create label, project dropdown and button
        #options = list(self.Projects.keys())
        #self.dropbox[0],self.dropBtn[0] = self.createDropdown("Select Project for all files in folder", colorPerm, options, "Select Project", 10, 0, self.projectSelect)
        dirname = "Folder: " + os.path.basename(dir)
        label = tkinter.Label(root, text=dirname, fg=colorPerm)
        label.place(x=10, y=50)

        # Create label, Global dropdown and button
        self.dropbox[1],self.dropBtn[1] = self.createDropdown("Tags to add to all files in folder", colorPerm, self.ExtraTags, "Add Tags", 220, 0, self.addTagGlob)

        # Create Individual Add Dropdown menu and button
        self.dropbox[2],self.dropBtn[2] = self.createDropdown("Tag to Add to this Image", colorIndiv, self.ExtraTags, "Add Tag", 400, 0, self.addTagIndiv)

        # Create Button for single add
        button = tkinter.Button(root, text="Custom Tag", fg=colorIndiv, command=self.newTag)
        button.place(x=550,y=18)

        # Add label and image itself
        self.labelFilename = tkinter.Label(root, text="")
        self.labelFilename.place(x=10, y=75)
        self.labelImg = tkinter.Label()
        self.labelImg.place(x=10, y=100)

        label = tkinter.Label(root, text = "Image Tags, click to remove")
        label.place(x=420, y=95)

        # Create Tag Labels
        for i in range(0, MAX_TAGS):
            label = tkinter.Label(root, text = "")
            label.place(x=420, y=115+(20*i))
            self.TagLabels.append(label)

        # Add buttons to cycle images
        button = tkinter.Button( root, text = "<-Previous Image" , command=lambda: self.updateImage(-1) )
        button.place(x=10, y=510)
        button = tkinter.Button( root, text = "Next Image->" , command=lambda: self.updateImage(1) )
        button.place(x=150, y=510)

        # Add finish button
        button = tkinter.Button( root, text = "Finished Template Tagging", command= self.finishClick )
        button.place(x=420, y=470, width=150, height=50)

        self.updateImage(0)


    def finishClick(self):
        self.root.destroy();

    #Sets PermTags into all TagsToUpdate appends back any existing ones.
    def refreshPermTags(self):
        for id in self.TagsToUpdate:
            indivTags = []
            for tag in self.TagsToUpdate[id]['Tags']:
                if tag not in self.PermTags:
                    indivTags.append(tag)
            self.TagsToUpdate[id]['Tags'] = self.PermTags.copy()
            self.TagsToUpdate[id]['Tags'].extend(indivTags)

    #Updates the dropbox
    def refreshIndivTags(self):
        self.dropbox[2]['values'] = self.ExtraTags
        self.dropbox[2].set(self.ExtraTags[0])



    def getImage(self):
        image0 = Image.open(self.ImgFiles[self.ImgIndex])
        width = image0.width
        height = image0.height
        if width > height:
            div = width / 400
        else:
            div = height / 400
        width = round(width/div)
        height = round(height/div)
        #print("size is: {}x{} => {}x{}".format(image0.width, image0.height, width, height))
        image1 = image0.resize((width, height))
        return ImageTk.PhotoImage(image1)

    # Left or Right clicked
    def updateImage(self, inc):
        self.ImgIndex += inc
        if self.ImgIndex < 0:
            self.ImgIndex = len(self.ImgFiles)-1
        elif self.ImgIndex >= len(self.ImgFiles):
            self.ImgIndex = 0;
        img = self.getImage()
        self.labelImg.configure(image=img)
        self.labelImg.image = img
        id = "T{}".format(self.ImgIndex + 1)
        self.labelFilename['text'] = "{} of {}: {}".format(self.ImgIndex+1, len(self.TagsToUpdate), self.TagsToUpdate[id]['FilePath'])
        self.showCurrentTags()


    def addTagGlob(self):
        selected = self.dropbox[1].get()
        if selected not in self.PermTags:
            if len(self.PermTags) >= MAX_TAGS:
                print("At maximum {} tags already".format(MAX_TAGS))
                return
            self.PermTags.append(selected)
            print("Adding Global Tag {}".format(selected))
            self.refreshPermTags()
            self.refreshIndivTags()
            self.showCurrentTags()


    def addTagIndiv(self):
        selected = self.dropbox[2].get()
        id = "T{}".format(self.ImgIndex + 1)
        tags = self.TagsToUpdate[id]['Tags']
        if selected not in tags:
            if len(tags) >= MAX_TAGS:
                print("At maximum {} tags already".format(MAX_TAGS))
                return
            tags.append(selected)
            print("id:{} Adding Indiv Tag {}".format(id, selected))
            self.showCurrentTags()


    def newTag(self):
        selected = simpledialog.askstring(title="Custom Tag", prompt="Create a new custom Tag")
        if selected:
            self.ExtraTags.append(selected)
            id = "T{}".format(self.ImgIndex + 1)
            tags = self.TagsToUpdate[id]['Tags']
            if selected not in tags:
                if len(tags) >= MAX_TAGS:
                    print("At maximum {} tags already".format(MAX_TAGS))
                    return
                tags.append(selected)
                self.showCurrentTags()
                self.refreshIndivTags()

    def showCurrentTags(self):
        id = "T{}".format(self.ImgIndex+1)
        tags = self.TagsToUpdate[id]['Tags']
        for i in range(0, MAX_TAGS):
            if i < len(tags):
                self.TagLabels[i]['text'] = tags[i]
                if tags[i] in self.PermTags:
                    self.TagLabels[i]['fg'] = colorPerm
                else:
                    self.TagLabels[i]['fg'] = colorIndiv
                self.TagLabels[i].bind("<Button-1>", lambda event, index=i : self.removeTagIndiv(index))
            else:
                self.TagLabels[i]['text'] = ""
                self.TagLabels[i]['fg'] = colorIndiv


    def removeTagIndiv(self, index):
        selected = self.TagLabels[index]['text']
        if selected:
            ret = False
            start = self.ImgIndex
            end = start + 1
            if selected in self.PermTags:
                ret = messagebox.askyesnocancel(title="All Tags", message="Remove {} from all Images?".format(selected))
                if ret == None:
                    return
                if ret == True:
                    start = 0
                    end = len(self.TagsToUpdate)
            else:
                ret = messagebox.askokcancel(title="Remove Tag", message="Remove {} from this Image?".format(selected))
                if ret == False:
                    return
            #print("remove {} s={} e={}".format(selected, start,end))
            for i in range(start,end):
                id = "T{}".format(i+1)
                if selected in self.TagsToUpdate[id]['Tags']:
                    self.TagsToUpdate[id]['Tags'].remove(selected)
            self.showCurrentTags()

    #Creates a label, dropbox, and button at specific location
    def createDropdown(self, labelText, color, cbData, btnText, xPos, yPos, handler):
        label = tkinter.Label(self.root, text=labelText)
        label['fg'] = color
        label.place(x=xPos,y=yPos)
        dropbox = ttk.Combobox(self.root,values=cbData)
        if len(cbData):
            dropbox.set(cbData[0])
        dropbox.place(x=xPos,y=yPos+20)
        button = tkinter.Button(self.root, text=btnText, fg=color, command=handler)
        button.place(x=xPos,y=yPos+45)
        return dropbox, button

    def getTagsToUpdate(self):
        return self.TagsToUpdate

    def templateDone(self):
        self.root.destroy()




def performDirPrompt():
    root = tkinter.Tk()
    root.withdraw()
    root.update()
    dir = askdirectory(initialdir=os.path.dirname(__file__), title='Select Folder') # shows dialog box and return the path
    root.destroy()

    return dir

def performProjectPrompt():
    root = tkinter.Tk()
    #root.withdraw()
    #root.update()
    app = projPrompt(root);
    root.mainloop()
    return app.getProject(), app.getTags()

#Compare two lists return common elements
def common_member(a, b):
    result = [i for i in a if i in b]
    return result

# Returns True (exit) or False continue with program
def performTemplatePrompt(dir, isTemplateCsv):
    root = tkinter.Tk()
    root.withdraw()
    root.update()
    templateFile = os.path.basename(dir) + ".csv"

    project = ""
    projectTags = []
    res = False
    if isTemplateCsv:
        print("Found a template file {}".format(templateFile))
        res = messagebox.askyesnocancel('Template prompt', 'Template {} found do you want to modify it? (selecting no will Tag the Images)'.format(templateFile))
        root.destroy()
        if res == None:  #Cancel
            return True  #Done exit
        if res == False:
            return False #continue with program

        csvFiles = [ dir + '/' + templateFile ]
        tagsToUpdate = parseCsvFiles(csvFiles)
        #Determine the project and projectTags by reading
        commonTags = []
        first = True
        for id in tagsToUpdate:
            if first:
                commonTags = tagsToUpdate[id]['Tags'].copy()
                first = False
            else:
                commonTags = common_member(commonTags, tagsToUpdate[id]['Tags'])
        if len(commonTags) == 0:
            input('Template has no common tags and is probably corrupt, press ENTER to close')
            return True
        project = commonTags[0]
        projectTags = commonTags

        root = tkinter.Tk()
        app = projTemplate(root, dir, projectTags, tagsToUpdate)
        root.mainloop()

    else:
        res = messagebox.askyesno('Template prompt', 'Create a Template .csv file ?')
        root.destroy()
        if res == False:
            return False  # continue with program

        project, projectTags = performProjectPrompt()
        if project == "":
            input('No Project selected, press ENTER to close')
            return True
        print("projectTags={}".format(projectTags))

        root = tkinter.Tk()
        app = projTemplate(root, dir, projectTags, None)
        root.mainloop()

    #Save the data entered to the csv
    createTemplateCsv(dir, templateFile, app.getTagsToUpdate())
    if performExecOnTemplate(dir) == False:
        input('Template Created, press ENTER to close')
        return True  #Done exit

    return False

def performExecOnTemplate(dir):
    root = tkinter.Tk()
    root.withdraw()
    root.update()

    res = messagebox.askyesno('Template execute', 'Do you want to tag the images in {} now?'.format(dir))
    return res


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


def createTemplateCsv(dir, templateFile, tagsToUpdate):
    #create a csv with only headings FilePath,Tag1,Tag2,Tag3...
    with open(dir + "/" + templateFile, 'w', newline='') as csvFile:
        header = ["FilePath"]
        tagCols = MAX_TAGS  # always create maximum number of tag columns
        for t in range(0, tagCols):
            header.append("Tag" + str(t+1))

        writer = DictWriter(csvFile, fieldnames=header)
        writer.writeheader()
        for id in tagsToUpdate:
            rowdata = {"FilePath" : tagsToUpdate[id]["FilePath"]}
            for t in range(0, len(tagsToUpdate[id]["Tags"])):
                rowdata["Tag" + str(t+1)] = tagsToUpdate[id]["Tags"][t]
            writer.writerow(rowdata)

    print("Created: " + templateFile)
    return templateFile


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


def testFileIsPng(file):
    ret = False
    with open(file, "rb") as f:
        data = f.read(4)
        if data == b'\x89PNG':
            ret = True
    return ret

def updateImgFile(et, file, description, tags, verbose):
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
    doTemplate = False
    if args.path:
        dir = args.path
    else:
        dir = performDirPrompt()

    jpgFiles = getImageFiles(dir)
    csvFiles = glob.glob(dir + "/*.csv")
    numCsvFiles = len(csvFiles)
    isTemplateCsv = False
    if numCsvFiles == 1:
        templateFile = os.path.basename(dir) + ".csv"
        csvFile = os.path.basename(csvFiles[0])
        if csvFile == templateFile:
            isTemplateCsv = True

    if numCsvFiles == 0 or isTemplateCsv:
        if performTemplatePrompt(dir, isTemplateCsv):
            return  #Template created but nothing more to do

    #Check if any jpg file are actually PNG- if so rename them so they can properly be tagged
    for i in range(0, len(jpgFiles)):
        file = jpgFiles[i]
        fsplit = os.path.splitext(file)
        ext = fsplit[1]
        if ext != ".png":
            if testFileIsPng(file):
                newName = fsplit[0] + ".png"
                print(Style.BRIGHT + Fore.YELLOW + "Detected {} is PNG renaming to {}".format(os.path.basename(file), os.path.basename(newName)))
                os.rename(file, newName)
                jpgFiles[i] = newName

    tagsToUpdate = {}

    if args.id:  #Single id specified to be updated.
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

    toolDir = os.getcwd() + '/jpgReTag.dist/exiftool/exiftool.exe'
    with exiftool.ExifToolHelper(auto_start=True, check_execute=False, check_tag_names=True, executable=toolDir) as et:
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
            updateImgFile(et, file, description, tagsToAdd, args.verbose)
            del jpgFiles[foundIndex]

    if isTemplateCsv:
        templateRename = csvFiles[0].replace(".csv", "-tagged.csv")
        try:
            os.rename(csvFiles[0], templateRename)
            print("Template was renamed successfully to " + os.path.basename(templateRename))
        except:
            print(Style.BRIGHT + Fore.YELLOW + "Template rename failed")

    if len(jpgFiles):
        print(Style.BRIGHT + Fore.YELLOW + "The following {} files where not modified:\n{}".format(len(jpgFiles),"\n".join(jpgFiles)))

    # prevent the console window from closing automatically.
    if isWinClick:
        input('Press ENTER to close')


if __name__ == '__main__':
    main()