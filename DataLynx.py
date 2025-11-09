import datetime

# Creates a new database file.
def createDB(path: str, name: str):
    line = "\n"
    output = "@META" + line
    output = output + LynxDB.lynxVersion + line
    output = output + name + line
    output = output + "@MAIN" + line
    output = output + "@PLAYLISTS" + line
    output = output + "@FINAL"

    with open(path, "w") as file:
        file.write(output)

# Holds a URL and associated metadata
class Entry:
    def __init__(self, rawEntry: str):
        sections = rawEntry.split("^")
        self.idNum = int(sections[0])
        self.url = sections[1]
        self.name = sections[2]
        self.authors = sections[3].split("+")
        self.tags = sections[4].split("+")

    def reconstruct(self):
        sections = []
        sections.append(str(self.idNum))
        sections.append(self.url)
        sections.append(self.name)
        auth = ""
        for a in self.authors:
            if auth == "":
                auth = a
            else:
                auth = auth + "+" + a
        sections.append(auth)
        tagCompile = ""
        for t in self.tags:
            if tagCompile == "":
                tagCompile = t
            else:
                tagCompile = tagCompile + "+" + t
        sections.append(tagCompile)
        return "^".join(sections)

# A collection of ID's that link to Entry objects
class Playlist:
    def __init__(self, rawPlaylist: str):
        parts = rawPlaylist.split("^")
        self.name = parts[0]
        rawSection = parts[1]
        if not rawSection == "":
            strNums = rawSection.split("+")
        else:
            strNums = []
        self.entryIDs = []
        if not strNums == []:
            for stringNum in strNums:
                self.entryIDs.append(int(stringNum))

    def removeID(self, targetID: int):
        self.entryIDs.remove(targetID)

    def addID(self, targetID: int):
        self.entryIDs.append(targetID)

    def reconstruct(self):
        eCompile = ""
        for e in self.entryIDs:
            if eCompile == "":
                eCompile = str(e)
            else:
                eCompile = eCompile + "+" + str(e)
        return self.name + "^" + eCompile

# Main object. Takes a database filepath as input, with a boolean for verbose mode. Verbose mode prints all actions DataLynx takes to the terminal.
class LynxDB:

    # This variable contains the file version that will be written to new saves.
    lynxVersion = "1.0.0"

    def __init__(self, filepath: str, verbose: bool):
        self.verbose = verbose

        if self.verbose:
            stamp = datetime.datetime.now()
            print("DataLynx - Verbose Mode")
            print("DataLynx file load starting at: " + str(stamp))

        self.filepath = filepath
        self.fileVersion = "0.0.0"
        self.name = "Blank"
        self.readMode = "START"
        self.readPosition = 0

        self.entries = []
        self.playlists = []

        with open(self.filepath, "r", encoding="utf-8") as file:
            raw = file.read()
            lines = raw.splitlines()
            # Release raw
            raw = ""
            for line in lines:
                # Divider lines
                if line[0] == "@":
                    cmd = line[1:]
                    self.readMode = cmd
                    self.readPosition = 0
                else:
                    match self.readMode:
                        case "META":
                            if self.readPosition == 0:
                                self.fileVersion = line
                            elif self.readPosition == 1:
                                self.name = line
                        case "MAIN":
                            self.entries.append(Entry(line))
                        case "PLAYLISTS":
                            self.playlists.append(Playlist(line))
                    self.readPosition = self.readPosition + 1
            
            if self.verbose:
                stamp = datetime.datetime.now()
                print("DataLynx file load completed at: " + str(stamp))
                print("DataLynx LynxDB object is now initialized. " + str(len(self.entries)) + " Entries Loaded.")
    
    # Takes in an ID that is associated with an Entry object. Will raise an exception if ID cannot be found.
    def searchByID(self, target: int):
        for e in self.entries:
            thisID = e.idNum
            if thisID == target:
                if self.verbose:
                    print("DataLynx: Accessing ID " + str(target))
                return e
        raise Exception("ID does not exist in database.")
    
    # Returns a list of Entry objects that are associated with the given author. List may be returned empty.
    def searchByAuthor(self, target: str):
        output = []
        for e in self.entries:
            if target in e.authors:
                output.append(e)
        if self.verbose:
            print("DataLynx: " + str(len(output)) + " Results Found for Author - " + target)
        return output
    
    # Returns a list of Entry objects that are associated with the given tag. List may be returned empty.
    def searchByTag(self, target: str):
        output = []
        for e in self.entries:
            if target in e.tags:
                output.append(e)
        if self.verbose:
            print("DataLynx: " + str(len(output)) + " Results Found for Tag - " + target)
        return output
    
    # Takes a Playlist object and returns the Entry objects associated with the IDs contained in the Playlist.
    def viewPlaylist(self, pl: Playlist):
        output = []
        for i in pl.entryIDs:
            output.append(self.searchByID(i))
        if self.verbose:
            print("DataLynx: " + str(len(output)) + " Entries in Playlist - " + pl.name)
        return output

    # Returns a list of Playlist objects that reference the given ID. May be returned empty. Used to ensure safe deletes.
    def checkReferencesToID(self, targetID: int):
        output = []
        for p in self.playlists:
            if targetID in p.entryIDs:
                output.append(p)
        if self.verbose:
            print("DataLynx: ID "+ str(targetID) + " is referenced by " + str(len(output)) + " playlists")
        return output

    # Deletes the Entry associated with the given ID.
    def deleteByID(self, targetID: int):
        targetEntry = self.searchByID(targetID)
        refs = self.checkReferencesToID(targetID)
        for r in refs:
            r.removeID(targetID)
        self.entries.remove(targetEntry)
        if self.verbose:
            print("DataLynx: Entry ID " + str(targetID) + " Has Been Deleted.")

    # Checks if ID is in use. Returns a boolean.
    def idActive(self, targetID):
        for e in self.entries:
            thisID = e.idNum
            if thisID == targetID:
                return True
        return False

    # Creates a new Entry object in the database. Will raise exception if given ID is already in use.
    def createEntry(self, newID: int, newURL: str, newName: str, newAuthors: list[str], newTags: list[str]):
        if self.idActive(newID):
            raise Exception("DataLynx: ID is already in use.")
        convertID = str(newID)
        convertAuthors = "BLANK"
        for author in newAuthors:
            if convertAuthors == "BLANK":
                convertAuthors = author
            else:
                convertAuthors = convertAuthors + "+" + author
        convertTags = "BLANK"
        for tag in newTags:
            if convertTags == "BLANK":
                convertTags = tag
            else:
                convertTags = convertTags + "+" + tag
        entryCode = convertID + "^" + newURL + "^" + newName + "^" + convertAuthors + "^" + convertTags
        new = Entry(entryCode)
        self.entries.append(new)
        if self.verbose:
            print("DataLynx: Created Entry - " + entryCode)

    # Creates a Playlist object and adds it to the database. Object will not hold any IDs until manually added.
    def createPlaylist(self, name: str):
        pCode = name + "^"
        new = Playlist(pCode)
        self.playlists.append(new)
        if self.verbose:
            print("DataLynx: Created Playlist - " + name)

    # Edits the data of an Entry object. The Entry is found by an ID, and all other parameters will overwrite the Entry's object variables.
    def editEntryByID(self, targetID: int, newURL: str, newName: str, newAuthors: list[str], newTags: list[str]):
        target = self.searchByID(targetID)
        target.url = newURL
        target.name = newName
        target.authors = newAuthors
        target.tags = newTags
        if self.verbose:
            print("DataLynx: Entry ID " + str(targetID) + " Has Been Altered.")

    # Returns a list of unique authors in the DB.
    def compileAuthors(self):
        output = []
        for e in self.entries:
            theseAuthors = e.authors
            for a in theseAuthors:
                if not a in output:
                    output.append(a)
        if self.verbose:
            print("DataLynx: " + str(len(output)) + " Unique Authors Found.")
        return output
    
    # Returns a list of unique tags in the DB.
    def compileTags(self):
        output = []
        for e in self.entries:
            theseTags = e.tags
            for t in theseTags:
                if not t in output:
                    output.append(t)
        if self.verbose:
            print("DataLynx: " + str(len(output)) + " Unique Tags Found.")
        return output
    
    # Saves a db file to the given filepath.
    def saveAs(self, path: str):
        line = "\n"

        if self.verbose:
            stamp = datetime.datetime.now()
            print("DataLynx: Compiling Entries. Starting at " + str(stamp))

        output = "@META" + line
        output = output + LynxDB.lynxVersion + line
        output = output + self.name + line
        output = output + "@MAIN" + line
        for e in self.entries:
            output = output + e.reconstruct() + line
        output = output + "@PLAYLISTS" + line
        for p in self.playlists:
            output = output + p.reconstruct() + line
        output = output + "@FINAL"

        if self.verbose:
            stamp = datetime.datetime.now()
            print("DataLynx: Ready to Save. Compilation Finished at " + str(stamp))

        with open(path, "w") as file:
            file.write(output)

        if self.verbose:
            print("DataLynx: Saved to " + path)

    # Saves a db file to the filepath used when initializing the LynxDB object.
    def quickSave(self):
        self.saveAs(self.filepath)

    # Deletes a Playlist from the DB.
    def deletePlaylist(self, target: Playlist):
        self.playlists.remove(target)

    # Returns an ID integer that is not in use.
    def findFreeID(self):
        maxID = 0
        for e in self.entries:
            thisID = e.idNum
            if thisID > maxID:
                maxID = thisID

        if self.verbose:
            print("DataLynx: Found Unused ID " + str(maxID + 1))

        return (maxID + 1)
    
    # If only the Entry ID is known, and a change is needed, this function will find and overwrite the Entry object with a new ID.
    # References are updated to maintain Playlist functionality.
    def reassignID(self, old: int, new: int):
        if self.idActive(new):
            raise Exception("DataLynx: ID is already in use.")
        e = self.searchByID(old)
        refs = self.checkReferencesToID(old)
        for pl in refs:
            i = pl.entryIDs.index(old)
            pl.entryIDs[i] = new
        e.idNum = new
        if self.verbose:
            print("DataLynx: Entry ID " + str(old) + " has been reassigned to ID " + str(new))

    # A version of reassignID() that takes an Entry object as input, saving a call to searchByID(). Does not have idActive() protection.
    def directReassignID(self, e: Entry, newID: int):
        oldID = e.idNum
        refs = self.checkReferencesToID(oldID)
        for pl in refs:
            i = pl.entryIDs.index(oldID)
            pl.entryIDs[i] = newID
        e.idNum = newID
        if self.verbose:
            print("DataLynx: Entry ID " + str(oldID) + " has been reassigned to ID " + str(newID))

    # Overwrites all IDs to be ascending order.
    def normalizeDatabaseAscending(self):
        # IDs are assigned in ascending order starting from the result of findFreeID().
        # This allows the IDs to be in ascending order without any conflicts with preexisitng IDs.
        if self.verbose:
            print("DataLynx: Normalizing IDs. Stage 1 - Ascending Order in High Range...")
        currentID = self.findFreeID()
        for e in self.entries:
            self.directReassignID(e, currentID)
            currentID = currentID + 1
        # The IDs are assigned starting at 1. This range of IDs should've been freed up by the previous loop.
        if self.verbose:
            print("DataLynx: Normalizing IDs. Stage 2 - Reassigning Starting at ID 1...")
        currentID = 1
        for e in self.entries:
            self.directReassignID(e, currentID)
            currentID = currentID + 1
        if self.verbose:
            print("DataLynx: Completed Database Normalization - Ascending Order.")