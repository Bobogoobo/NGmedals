"""NGmedals.py: stats for Newgrounds medals - http://www.newgrounds.com/
Author: Bobogoobo ( http://bobogoobo.newgrounds.com/ ) copyright March 2013 to present"""

VersionDate = "November 21, 2022" #using a global variable isn't the end of the world, right? I'd forget about it otherwise :P Remember to update in news post.
TopUserName = "HerbieG"
DebugMode = False #remember to turn this off

from operator import itemgetter
from urllib.request import urlopen, Request
import os, sys, time

##########
# Classes
##########

class GameData():
    __slots__ = ("ernMed", "totMed", "ernPts", "totPts", "unMeds", "unPnts")

    def __init__(self, ernMed, totMed, ernPts, totPts):
        args = [ernMed, totMed, ernPts, totPts]
        for i in range(len(args)):
            if not isinstance(args[i], int):
                args[i] = int(args[i].replace(",",""))
        self.ernMed = args[0]
        self.totMed = args[1]
        self.ernPts = args[2]
        self.totPts = args[3]
        self.unMeds = args[1] - args[0]
        self.unPnts = args[3] - args[2]

    def __str__(self):
        medals = str(self.ernMed).rjust(3) + "/" + str(self.totMed).rjust(3) + " medals"
        unmedals = " (" + str(self.unMeds).rjust(3) + ")"
        points = str(self.ernPts).rjust(4) + "/" + str(self.totPts).rjust(4) + " points"
        unpoints = " (" + str(self.unPnts).rjust(4) + ")"
        return medals.rjust(14) + unmedals.ljust(6) + " " + points.rjust(16) + unpoints.ljust(7)

class MedalData():
    #should have a docstring :P. Values passed are None if data unavailable, else strings
    __slots__ = ("name", "value", "earned", "secret")

    def __init__(self, name, value, earned):
        if value == "?????": value = None
        self.secret = True if value == None else False
        self.name, self.value, self.earned = name, value, earned

    def __str__(self, pad=0):
        out = "    " + self.name.rjust(pad) + ": "
        if not self.secret:
            out += (self.value + " pts").rjust(7)
            if self.earned:
                out += " (earned)"
        else:
            out += "  secret"
        return out

############
# Utilities
############

def timestamp(string="", fmt=""):
    Time = time.gmtime()
    Time = [str(x).zfill(2) for x in Time]
    if fmt == "YMD":
        Time = Time[0] + Time[1] + Time[2]
    else:
        Time = string + Time[0] + "-" + Time[1] + "-" + Time[2] + "T" + Time[3] + ":" + Time[4] + ":" + Time[5] + "Z"
    return Time

def rnd(a, b, mult=100, place=2):
    return str(round(a / b * mult, place))

def url(URL):
    req = Request(url=URL, headers={"User-Agent":"NGmedals"}) #Python's user agent is blocked
    page = ""
    time.sleep(1) #NG request rate limit
    #The replace is for a FNAF game breaking something despite being unicode
    try:
        page = urlopen(req).read().decode("utf-8").replace("´", "'")
    except Exception as e:
        print(page)
        print(page.getcode() + " - " + URL)
        sys.exit(e)
    if page == "An internal server error has occurred, and the staff has been alerted. The site could be under heavy load at the moment, so you may want to try again in a few minutes.":
        sys.exit("Newgrounds is down at the moment. Please try again in a few minutes.")
    elif page == "<html><body>\nYou're making too many requests - ease up!\n</body></html>":
        sys.exit("Too many requests. Wait a while and try again.")
    return page

def printline(string):
    if len(sys.argv) < 2:
        print(string)
    elif sys.argv[1] == "incmd":
        print(string + "\r", end="")

def cacheFile(opn=False, mde="r"):
    filename = os.getcwd() + "\\cache-" + timestamp(fmt="YMD") + ".txt"
    if opn:
        return open(filename, mode=mde, encoding="utf-8")
    else:
        return filename

def renameCache():
    #This could probably use some builtin stuff but even doing this myself was less of a headache (kinda fun actually)
    #Also, I set Feb to 28 days, leap year code would be obtrusive http://en.wikipedia.org/wiki/Leap_year#Algorithm
    cache = ""
    newCache = "cache-" + timestamp(fmt="YMD") + ".txt"
    monthDays = {"01":"31", "02":"28", "03":"31", "04":"30", "05":"31", "06":"30", "07":"31", "08":"31", "09":"30", "10":"31", "11":"30", "12":"31"}
    for path in os.listdir():
        if path[:6] == "cache-":
            cache = path
            break
    year, month, day = newCache[6:10], newCache[10:12], newCache[12:14]
    for i in range(7):
        day = str(int(day) - 1).zfill(2)
        if day == "00":
            if month != "01":
                month = str(int(month) - 1).zfill(2)
                day = monthDays[month]
            else:
                year = str(int(year) - 1)
                month, day = "12", "31"
        string = "cache-" + year + month + day + ".txt"
        if cache == string:
            os.rename(os.getcwd() + "\\" + cache, os.getcwd() + "\\" + newCache)
            break

def checkProgress(milestones, donePages, i):
    #first element of milestones is percentage completion
    if donePages + i + 1 in milestones:
        milestones[0] = str(int(milestones[0]) + 10)
    printline(
        "Progress: |" + "-" * (int(milestones[0]) // 10) +
        " " * (10 - (int(milestones[0]) // 10)) +
        "| ( " + str(donePages + i).rjust(len(str(milestones[-1]))) +
        " / " + str(milestones[-1]) + " )"
    )
    return milestones

def calcTotalRequests(username):
    pages, miles, userMedalCount = 0, ["-10"], 0
    checkPages = [username]
    if not os.path.isfile(cacheFile()):
        checkPages.append(TopUserName)
    for pagename in checkPages:
        page = url("http://" + pagename + ".newgrounds.com/stats/medals")

        if pagename == username:
            umcstart = page.find("Total Medals Earned: <strong>")
            umcstart += len("Total Medals Earned: <strong>")
            userMedalCount = int(page[umcstart : page.find("</strong>", umcstart)].replace(",", ""))

        pgnumix = page.rfind("/stats/medals?page=")
        pages += int(page[page.find("<span>", pgnumix)+6 : page.find("</span>", pgnumix)])
    page = url("http://www.newgrounds.com/gameswithmedals/")
    pgnumix = page.rfind("/gameswithmedals/")
    pages += int(page[page.find("<span>", pgnumix)+6 : page.find("</span>", pgnumix)])
    
    for i in range(11):
        miles.append(int(pages * (i / 10)))
    return miles, userMedalCount

##################
# Retrieving data
##################

def getUserMedals(username, milestones, donePages, IDs, IDDict, medalData, isuser=True):
    gamesList, topUserMedals, gamePages = {}, {}, [{}, 0]
    LCletters = "abcdefghijklmnopqrstuvwxyz"
    statsreplace = [
        ("\t", ""), ("\n", ""), (" ", ""), #spaces are removed due to inconsistencies
        ("MedalsEarned:<strong>", ""), ("</strong>/", "|"), ("<em>(<strong>", "|"), ("points)</em>", "")
    ]
    page = url("http://" + username + ".newgrounds.com/stats/medals")
    pgnumix = page.rfind("/stats/medals?page=")
    maxpage = int(page[page.find("<span>", pgnumix)+6 : page.find("</span>", pgnumix)])
    gamePages[1] = maxpage #this'll need adjusting if pages over 1000 have commas...but we're a while away from that

    for i in range(5 if DebugMode else maxpage):
        checkProgress(milestones, donePages, i)
        page = url("http://" + username + ".newgrounds.com/stats/medals?page=" + str(i + 1))
        start, search = 0, '<a name="for_'
        while start <= page.rfind(search):
            data = []
            start = page.find("</a>", page.find(search, start))
            headstart = page.find("<a", page.find("<h2", start))
            headstart = page.find(">", headstart) + 1
            headend = page.find("</a>", headstart)
            game = page[headstart:headend].strip()
            if game not in medalData:
                medalData[game] = []
            topUserMedals[game] = []
            firstletter = game.lower()[0]
            if firstletter not in gamePages[0] and firstletter in LCletters:
                gamePages[0][firstletter] = i + 1

            idstart = page.find("/portal/view/", start) + 13
            idend = page.find('"', idstart)
            ID = page[idstart:idend]
            try:
                int(ID) #remember ID is still a string
            except:
                ID = "0" #NG Easter Eggs has no "Play!" button
                idend = headend
            IDs.add(ID)
            IDDict[game] = ID
            
            pstart = page.find("<p>", headend) + 3
            pend = page.find("</p>", pstart)
            stats = page[pstart:pend].strip()
            for x in statsreplace:
                stats = stats.replace(x[0], x[1])
            stats = stats.split("|")
            if "<head>" in stats[0]:
                #Fix for another strange bug
                data = GameData(0, 0, 0, 0)
                pend = page.find("</html>", pstart)
            elif isuser:
                data = GameData(stats[0], stats[1], stats[2], stats[3])
            else:
                data = GameData(0, stats[1], 0, stats[3])

            gamesList[game] = data

            mdstart = pend
            mdsearch = '<div class="medal-icon '
            while True:
                mdstart = page.find(mdsearch, mdstart)
                mdstatus = page[mdstart + len(mdsearch) : page.find('"', mdstart)]
                if mdstatus == "unlocked":
                    mdunlocked = True
                elif mdstatus == "locked" or mdstatus == "secret":
                    mdunlocked = False
                else:
                    mdunlocked = None
                mdstart = page.find("<h4>", mdstart) + 4
                mdend = page.find("</h4>", mdstart)
                if mdstart > page.find(search, pend) or mdstart < page.find(mdsearch):
                    mdend = pend
                    break #I might need to fix the logic so I don't use a while True...it's annoying
                mdinfo = page[mdstart:mdend].split(" <span>")
                mdata = [mdinfo[0], mdinfo[1].replace(" Points</span>", ""), mdunlocked]
                    
                if isuser:
                    medalData[game].append(MedalData(mdata[0], mdata[1], mdata[2]))
                else:
                    medalData[game].append(MedalData(mdata[0], mdata[1], None))
                    topUserMedals[game].append([mdata[0], mdata[1]])

            start = mdend

    donePages += maxpage
    return gamesList, donePages, IDs, IDDict, medalData, gamePages, topUserMedals

def getMissedGames(allList, milestones, donePages, IDs, IDDict, medalData):
    gamesList, secrets = {}, {}
    page = url("http://www.newgrounds.com/gameswithmedals/")
    pgnumix = page.rfind("/gameswithmedals/")
    maxpage = int(page[page.find("<span>", pgnumix)+6 : page.find("</span>", pgnumix)])

    for i in range(5 if DebugMode else maxpage):
        checkProgress(milestones, donePages, i)
        sort = "title" if DebugMode else "date"
        page = url("http://www.newgrounds.com/gameswithmedals/sort/" + sort + "/page/" + str(i + 1))
        start, search = 0, "<div><div><div>"
        while start <= page.rfind(search):
            bgn = page.find(search, start) + len(search)
            end = page.find("by <strong>", bgn)
            info = page[bgn:end].strip()
            start = end
            name = info[info.find(">")+1 : info.rfind("<")].strip()
            ID = info[info.find("/view/")+6 : info.find(">")-1]
            IDDict[name] = ID
            if ID not in IDs and name not in allList: #some IDs are messed up
                IDs.add(ID)
                medals, points, secretMedals, medalData = getGameMedals(ID, name, medalData)
                if medals != 0: #some games in the collection have no medals
                    gamesList[name] = GameData(0, medals, 0, points)
                    if secretMedals != 0:
                        secrets[name] = secretMedals
    donePages += maxpage
    return gamesList, donePages, IDs, IDDict, secrets, medalData

def getGameMedals(ID, game, medalData):
    page = url("http://www.newgrounds.com/portal/view/" + ID)
    start, search = 0, '<div class="medal-icon '
    medals = page.count(search)
    if medals != 0:
        medalData[game] = []
    points, secretMedals = 0, 0
    for i in range(medals):
        bgn = page.find("<h4>", page.find(search, start)) + 4
        end = page.find(" <span>", bgn)
        name = page[bgn:end].strip()
        bgn = end + 7
        end = page.find("</span>", bgn)
        value = page[bgn:end].strip()
        value = value[:value.find(" ")]
        start = end
        if value == "?????":
            secretMedals += 1
            medalData[game].append(MedalData(name, None, None))
        else:
            try:
                points += int(value)
            except ValueError:
                value = "0"
            medalData[game].append(MedalData(name, value, None))
    return medals, points, secretMedals, medalData

#################
# Analyzing data
#################

def combineLists(userList, allList, nameLength=25):# 25 is maximum length of submission title without an exception
    for game in allList.keys():
        if len(game) > nameLength:
            nameLength = len(game)
        if game in userList:
            allList[game] = userList[game]
            userList.pop(game)
            
    for game in userList.keys():
        if len(game) > nameLength:
            nameLength = len(game)
        allList[game] = userList[game]
        
    return allList, nameLength

def sortList(allList, sortType, rev=False):
    sortedList = []
    types = {"1":"unPnts", "2":"unMeds", "3":"name", "4":"ernPts",
             "5":"ernMed", "6":"totPts", "7":"totMed"}
    if sortType in types:
        sortType = types[sortType]
    else:
        sortType = types["1"]
    
    if sortType == "name":
        sortedList = sorted(allList.keys())
    else:
        sortedList = sortHelper(allList, sortType) #it's really astounding how quickly this runs even with my lazy sorting.

    if rev: sortedList.reverse()
    return sortedList

def sortHelper(allList, check):#could combine these three back into one function, meh
    sortedList = []
    valuelist = {}
    for game in sorted(allList.keys()):
        thing = getattr(allList[game], check)
        if thing in valuelist:
            newCheck = {"unPnts":"totPts", "unMeds":"totMed", "ernPts":"totPts",
                        "ernMed":"totMed", "totPts":"ernPts", "totMed":"ernMed"}
            valuelist[thing] = keepSorted(allList, valuelist[thing], game, newCheck[check])
        else:
            valuelist[thing] = [game]
    for value in sorted(valuelist.keys(), reverse=True):
        for game in valuelist[value]:
            sortedList.append(game)

    return sortedList

def keepSorted(allList, lst, new, check):
    sortedList = []
    if check == "name":
        lst.append(new)
        sortedList = sorted(lst)
    else:
        for i in range(len(lst)):
            if getattr(allList[new], check) > getattr(allList[lst[i]], check):
                #be careful with any sorting that isn't descending by default
                lst.insert(i, new)
                break
        else:
            lst.append(new)
        sortedList = lst

    return sortedList

def makeOutput(sortedList, allList, username, nameLength, secretMedals, userMedalCount):
    rowLength = nameLength + 45 #sum of padding and other characters
    ownedMedals, totalMedals, earnedPoint, totalPoints = 0, 0, 0, 0
    unplayedGames, undoneGames, doneGames, totalGames = 0, 0, 0, len(allList)
    listout, stats = "", ""
    output = "~Medal game stats and list for " + username + " as of " + timestamp() + "~\n\n"
    if len(output) - 2 < rowLength:
        output = output.replace("\n", "").center(rowLength) + "\n\n"
    for game in sortedList:
        data = allList[game]
        listout += game.rjust(nameLength) + " " + str(data) + "\n"
        ownedMedals += data.ernMed
        totalMedals += data.totMed
        earnedPoint += data.ernPts
        totalPoints += data.totPts
        if data.ernPts == 0:
            unplayedGames += 1
        elif data.unPnts != 0:
            undoneGames += 1
        else:
            doneGames += 1

    if userMedalCount != ownedMedals:
        output += "--NOTE: some data is inaccurate due to NG glitches.--".center(rowLength) + "\n\n"
    overall = GameData(ownedMedals, totalMedals, earnedPoint, totalPoints)
    stats += "Medals: " + str(ownedMedals) + "/" + str(totalMedals) + \
             " (" + rnd(ownedMedals, totalMedals) + "%)"
    stats += ". Points: " + str(earnedPoint) + "/" + str(totalPoints) + " (" + rnd(earnedPoint, totalPoints) + "%)."
    stats += "\nGames: " + str(unplayedGames) + " unplayed, " + str(undoneGames) + " incomplete, " + \
             str(doneGames) + "/" + str(totalGames) + " completed (" + rnd(doneGames, totalGames) + "%)."
    stats += "\nMy stats: " + rnd(earnedPoint, ownedMedals, 1) + " pts/med, " + \
             rnd(ownedMedals, totalGames, 1) + " med/game, " + rnd(earnedPoint, totalGames, 1) + " pts/game."
    stats += "\nOverall stats: " + rnd(totalPoints, totalMedals, 1) + " pts/med, " + \
             rnd(totalMedals, totalGames, 1) + " med/game, " + rnd(totalPoints, totalGames, 1) + " pts/game."
    for x in stats.split("\n"):
        output += x.center(rowLength) + "\n"
        
    output += "\n" + listout
    
    if len(secretMedals) > 0:
        output += "\nThe following games have unknown secret medals, which cannot be included in point totals. Total: " + \
                   str(sum(secretMedals.values())) + ".\n"
        for game in sorted(secretMedals.keys()):
            output += "*" + game + ": " + str(secretMedals[game]) + "\n"
            
    return output

def medalStats(medalData, username, gamePages, IDDict, fullList=False):
    output = "~Individual medal statistics for " + username + " as of " + timestamp() + "~\n\n"
    output += "NOTE: value and date statistics do not include unknown secret medals, which don't show them.\n\n"
    counts = {"0":[0, 0], "5":[0, 0], "10":[0, 0], "25":[0, 0], "50":[0, 0], "100":[0, 0], "secret":[0, 0]} #earned, total
    names, dates = {}, {}
    
    for game in medalData.keys():
        for medal in medalData[game]:
            #could probably make this stuff more efficient with more variables
            if medal.name in names:
                names[medal.name] += 1
            else:
                names[medal.name] = 1

            if medal.secret:
                counts["secret"][1] += 1
                if medal.earned:
                    counts["secret"][0] += 1 #will always be 0, no way to tell if they earned it
            else:
                try:
                    counts[medal.value][1] += 1
                    if medal.earned:
                        counts[medal.value][0] += 1
                except:
                    errorstr = str(medal) + " [" + game + "]"
                    if "errors" in counts:
                        counts["errors"].append(errorstr)
                    else:
                        counts["errors"] = [errorstr]

            #if medal.date in dates:
            #    dates[medal.date] += 1
            #else:
            #    dates[medal.date] = 1

    output += "Earned medals by value:\n" #need to fix the if stuff in here...
    for mtype in ["5", "10", "25", "50", "100", "0", "secret"]:
        if mtype != "secret":
            if mtype == "0" and counts["0"][1] == 0:
                pass
            else:
                output += mtype + "-point medals: "
        elif counts["secret"][1] != 0:
            output += "Unearned secret medals: "
        if counts[mtype][1] == 0:
            if mtype == "0" or mtype == "secret":
                pass
            else:
                output += "0/0 (0.00%)"  
        else:
            if mtype == "secret":
                output += str(counts["secret"][1]) + "\n"
            else:
                output += str(counts[mtype][0]) + "/" + str(counts[mtype][1]) + " (" + \
                            rnd(counts[mtype][0], counts[mtype][1]) + "%)\n"
    if "errors" in counts:
        output += "Medals with an erroneous point value:\n"
        for x in counts["errors"]:
            output += x + "\n"

    #output += "\nDates earning the most medals:\n"
    #output += medalDateNameStuff(dates, 20)

    output += "\nIndex of medals pages:\n"
    i = 0
    for letter in sorted(gamePages[0].keys()):
        output += " " + letter.upper() + ": " + str(gamePages[0][letter]).zfill(len(str(gamePages[1]))) + " "
        i += 1
        if i % 4 == 0:
            output += "\n"
        else:
            output += "|"
    output += "\n"

    output += "\nMost common medal names:\n"
    output += medalDateNameStuff(names, 10)

    if fullList:
        output += "\n\n" + "-"*33 + "\n Detailed list of medals by game \n" + "-"*33 + "\n"
        for game in sorted(medalData.keys()):
            output += "\n" + game + " | http://www.newgrounds.com/portal/view/" + IDDict[game] + "\n"
            
            length = 0
            for x in medalData[game]:
                if len(x.name) > length:
                    length = len(x.name)

            for medal in medalData[game]:
                output += medal.__str__(length) + "\n"
    
    return output

def medalDateNameStuff(lst, limit):
    #only for use with format of medal date and name lists in medalStats function
    newlst, output = [], ""
    for item in lst:
        if item == None or lst[item] == 1: continue
        newlst.append([item, lst[item]])
    newlst = sorted(newlst, key=itemgetter(1, 0), reverse=True)
    i, j = 0, 0
    while i < limit and j < len(newlst) - 1:
        output += "  " + str(i + 1) + ": " + newlst[j][0] + " (" + str(newlst[j][1]) + ")\n"
        j += 1
        if newlst[j][1] != newlst[j-1][1]:
            i = int(j) #not sure about reference stuff if I set it directly
    return output

############################
# Finalizing and file stuff
############################

def loadSettings(): #the configparser module may be helpful if this gets large
    settings = {}
    bools = {"1": True, "on": True, "false": False, "0": False, "off": False, "yes": True, "no": False, "true": True}
    try:
        file = open(os.getcwd() + "\\settings.ini")
        for line in file:
            line = line.strip()
            if line == "" or line[0] == ";": continue
            data = [x.strip() for x in line.split("=")]
            if data[0] == "sort":
                pass
            elif data[1].lower() in bools:
                data[1] = bools[data[1]]
            #add more conversions here
            settings[data[0]] = data[1]
        print("Settings loaded. Edit settings.ini to change your values.")
    except Exception as error:
        print("Error loading settings (set to defaults):", error)
        settings = {"deleteold":False, "username":"", "sort":"", "listfull":""} #hopefully I remember to update this :P
    return settings

def delOldFiles():
    for path in os.listdir():
        if path[:7] == "medals-" or path[:11] == "medalStats-":
            os.remove(path)

def saveFile(prefix, output):
    filename = os.getcwd() + "\\" + prefix + "-" + timestamp(fmt="YMD") + "-1.txt"
    i = 1
    while os.path.isfile(filename):
        i += 1
        filename = filename[:filename.rfind("-")] + "-" + str(i) + ".txt"
    saved = False
    while not saved:
        try:
            try:
                open(filename, mode="w").write(output)
            except:
                open(filename, mode="w", encoding="utf-8").write(output)
                #previously the fallback was iso-8859-1, but that's no longer sufficient
            saved = True
            print("Saved " + filename)
        except Exception as error:
            filename = input("Error saving file. Enter a full path to try again, or press Enter to skip: ")
            if filename == "":
                saved = True
                print("Please report the following error:", type(error).__name__ + ":", error)

def saveCache(lst, medalData, IDDict):
    for path in os.listdir():
        if path[:6] == "cache-":
            os.remove(path) #delete old cache files
    output = ""
    output += "//\tThis is an automatically saved list of the medals/points/ID and medal detail data for each game.\n"
    output += "//\tIt is generated from the medal stats of " + TopUserName + ", who is #1 in medal points, for efficiency.\n"
    output += "//\tIt will be deleted automatically the next time you run the program if it is more than a week old.\n"
    output += "//\t\n"
    filename = cacheFile()
    for game in lst.keys():
        output += game + "\t" + str(lst[game].totMed) + "\t" + str(lst[game].totPts) + \
                  "\t" + IDDict[game] + "\t" + str(medalData[game]) + "\n"
        #adding ID was really annoying. Maybe find a better way to do it or something
    cacheFile(True, "w").write(output)

def getCache(MD, IDs, IDDict):
    gamesList = {}
    for line in cacheFile(True):
        if line[0:3] == "//\t":
            continue
        line = line.strip().split("\t")
        if line == [""]: continue
        game, medals, points, ID, medalData = line[0], line[1], line[2], line[3], eval(line[4])
        gamesList[game] = GameData(0, medals, 0, points)
        IDs.add(ID)
        if game not in IDDict:
            IDDict[game] = ID
        if game not in MD:
            MD[game] = []
            for medal in medalData:
                MD[game].append(MedalData(medal[0], medal[1], None))
    return gamesList, MD, IDs, IDDict

def checkVersion():
    newspost = url("http://bobogoobo.newgrounds.com/news/post/832879")
    startidx = newspost.find("(last update: ") + len("(last update: ")
    endidx = newspost.find(")", startidx)
    uploadDate = newspost[startidx:endidx]
    if uploadDate != VersionDate:
        print("New program version is available. Shortcut in program folder goes to news post.")

#######
# Main
#######

def main():
    printline("Initializing...")
    renameCache()
    settings = loadSettings()
    username = settings["username"]
    while username == "":
        username = input("Enter username: ")
        printline("Loading...")
        testuser = url("http://" + username + ".newgrounds.com/")
        if testuser.find('<p>ERROR &mdash; No user "' + username + '" exists in our system.</p>') != -1:
            print("That user does not exist. Please try again.")
            username = ""
    sortType, rev = settings["sort"], False
    if sortType == "":
        sortType = input("Enter the number corresponding to the sorting you desire.\n"+
                         "To reverse the sorting order, add an 'r' after the numeral.\n"+
                         "  1: The number of points you are missing in the game (descending).\n"+
                         "  2: The number of medals you are missing in the game (descending).\n"+
                         "  3: The name of the game (ascending).\n"+
                         "  4: The number of points you have in the game (descending).\n"+
                         "  5: The number of medals you have in the game (descending).\n"+
                         "  6: The total number of points in the game (descending).\n"+
                         "  7: The total number of medals in the game (descending).\n"+
                         "Or press Enter for the default, 1: ")
    if sortType == "":
        sortType = "1"
    if len(sortType) > 1:
        sortType = sortType[0]
        rev = True
    fullList = settings["listfull"]
    if fullList == "":
        fullList = input("Do you want a detailed list of medals per game? (y/n, press Enter for n) ")
    if fullList.lower() == "y":
        fullList = True
    else:
        fullList = False
        
    print("\n" + timestamp("Began: "))
    printline("Calculating...")
    miles, userMedalCount = calcTotalRequests(username)
    donePages, IDs, IDDict, medalData = 0, set(), {}, {}
    miles = checkProgress(miles, donePages, -1)
    userList, donePages, IDs, IDDict, medalData, gamePages, dummyVar = getUserMedals(username, miles, donePages, IDs, IDDict, medalData)
    if not os.path.isfile(cacheFile()):
        topUserList, donePages, IDs, IDDict, medalData, dummyVar, topUserMedals = getUserMedals(TopUserName, miles, donePages, IDs, IDDict, medalData, False)
        saveCache(topUserList, topUserMedals, IDDict)
    else:
        topUserList, medalData, IDs, IDDict = getCache(medalData, IDs, IDDict)    
    finalList, nameLength = combineLists(userList, topUserList)
    missedList, donePages, IDs, IDDict, secretMedals, medalData = getMissedGames(finalList, miles, donePages, IDs, IDDict, medalData)
    finalList, nameLength = combineLists(missedList, finalList, nameLength)
    sortedList = sortList(finalList, sortType, rev)
    output = makeOutput(sortedList, finalList, username, nameLength, secretMedals, userMedalCount)
    if settings["deleteold"]:
        delOldFiles()
    saveFile("medals", output)
    saveFile("medalStats", medalStats(medalData, username, gamePages, IDDict, fullList))
    print(timestamp("Ended: ") + "\n")
    checkVersion()

if __name__ == "__main__":
    main()
