import math
import sys
import json
import os.path
import pandas as pd
from datetime import datetime
import time
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from collections import ChainMap
import pwinput 

# Main Function: checks login and gives user options for the programn, as well as an exit.
def main():
    user = login()
    while True:
        print("What would you like to do?:\n"
              "1) Use Carb Calculator.\n"
              "2) Update Ratio/Target BG/Correction Factor.\n"
              "3) Export Current Data as CSV.\n"
              "4) Exit.")
        option = input("Please input an option number: ")
        try:
            userInput = int(option)
            if isinstance(userInput, int):
                if userInput == 1:
                    bolusCalc(user)
                    continue
                if userInput == 2:
                    infoAquire(user)
                    continue
                if userInput == 3:
                    newExportCSV(user)
                    continue
                if userInput == 4:
                    return    
        except:
            print("Please choose a number. \n")
            continue
        if option is None:
            print("Please select an option. \n")
            continue
        if int(option) > 4 or int(option) <= 0:
            print("Please choose a valid oprion. \n")
            continue
                
# Login Function: Does login function, creates new login if needed and sets a flag for accounts that have already been created. Times out users who get their information wrong too many times.
def login():
    timeoutCounter = 0
    while True:
        existingUser = input("Are you an existing user? (Y/N):  ")
        if existingUser in ("Y", "Yes", "yes", "YES", "y", "yES"):
            print("Great! ")
            break
        if existingUser in ("N", "No", "no", "NO", "n", "nO"):
            print("Welcome! Please create a login. \n")
            flag = createLogin()
            if flag == 1:
                continue
            else:
                break
        else:
            print("Please enter a valid response. \n")
            continue
    while True:      
        print("What are your login credentials? \n")  
        User = input("Please enter your username:  \n")
        Pass = pwinput.pwinput("Please enter your password:  \n")

        if timeoutCounter >= 2:
            print("You have failed too many attempts. (3) \n")
            time.sleep(3)
            sys.exit(1)
        else:
            userCheck = findUI("Username", User)

            if userCheck["Username"] == User:
                if userCheck["Password"] == Pass:
                    user = userCheck["Username"]
                    FirstName = userCheck["First Name"]
                    print("Welcome " +FirstName+". \n")
                    break
                else:
                    print("The Password was incorrect. \n")
                    timeoutCounter = timeoutCounter + 1
                    continue
            else:
                print("There is no account with that username. \n")
                timeoutCounter = timeoutCounter + 1
                continue
    return user

# Create Login Function: creates the dictionary for the users login information. Will also check and return a flag if an account is created already.
def createLogin():

    firstName = input("What is your first name?:  \n")
    lastName = input("What is your last name?:  \n")
    username = input("What would you like your username to be?:  \n")
    password = pwinput.pwinput("What would you like your password to be?:  \n")

    newLogin = {"First Name" : firstName, "Last Name" : lastName, "Username" : username, "Password" : password}
    defaultData = {"Username" : username, "Target BG" : "default", "Correction Factor" : 0, "Carb Ratio" : 0}
    checkUser = checkDB("Username", username)
    if checkUser is True:
        print("There is already an account made with that name. Please try again or use different credentials. \n")
        return 1
    else:
        insertUdB(newLogin)
        insertUDdB(defaultData)
        print("Account successfully created! \n")

# Aquire Info Function: This will aquire the first time info from the user that usually does not change on a frequent basis. It directly updates this information to the users data (dictionary) with a function updateDict().
def infoAquire(user):
    while True:
        correctionFactor = input("Please enter your pre-determined correction factor (number of mg/dL that 1 unit corrects):  \n")
        try:
            userData = int(correctionFactor)
            if isinstance(userData, int):
                print("Correction factor is " +str(userData)+ "mg/dL. \n")
                CFDict = {"Correction Factor" : correctionFactor}
                updateDB(user, CFDict)
                break
        except ValueError:
            print("Please enter a valid number. \n")
            continue
    while True:
        carbRatio = input("Please enter your pre-determined carb ratio (grams of carbs per 1 unit administered):  \n")
        try:
            userData = int(carbRatio)
            if isinstance(userData, int):
                print("Carb ratio is " +str(userData)+ ".")
                CRDict = {"Carb Ratio" : carbRatio}
                updateDB(user, CRDict)
                break
        except ValueError:
            print("Please enter a valid number. \n")
            continue
    while True:
        targetBG = input("Please enter your target blood glucose level (in mg/dL): \n")
        try:
            userData = int(targetBG)
            if isinstance(userData, int):
                print("Target BG is " +str(userData)+ ".")
                TBGDict = {"Target BG" : targetBG}
                updateDB(user, TBGDict)
                break
        except ValueError:
            print("Please enter a valid number. \n")
            continue

# Main Calculation Function: This function will do the main calculation of the program, take the imputs from the user for that meal and store them in the data file, as well as the current date and time. The log counter is what allows the dictionary addition to be dynamic and add new values instead of update old ones.
def bolusCalc(user):
    while True:
        TBG = findUD(user, "Target BG")
        CF = findUD(user, "Correction Factor")
        CR = findUD(user, "Carb Ratio")
        if TBG["Target BG"] == "default":
            infoAquire(user)
            continue
        else:
            while True:
                numberCarbs = input("Enter the number of carbs you are going to eat (in grams):  \n")
                try:
                    userData = int(numberCarbs)
                    if isinstance(userData, int):
                        print("You have entered "+str(userData)+ " grams of carbs. \n")
                        break
                except ValueError:
                    print("Please enter a valid number. \n")
                    continue
            while True:
                currentBG = input("Enter your current blood glucose level (in mg/dL): \n")
                try:
                    userData = int(currentBG)
                    if isinstance(userData, int):
                        print("You current BG is "+str(userData)+ "mg/dL. \n")
                        break
                except ValueError:
                    print("Please enter a valid number. \n")
                    continue   

            CF, CR, TBG, NC, CBG = int(CF["Correction Factor"]), int(CR["Carb Ratio"]), int(TBG["Target BG"]), int(numberCarbs), int(currentBG)

            unitsTake = ((CBG-TBG)/CF) + (NC/CR)

            time = datetime.now()
            currentTime = time.strftime("%m/%d/%Y at %H:%M:%S")
            adminInstance = {"Carb Intake on "+currentTime : numberCarbs, "Current BG on "+currentTime : currentBG, "Bolus Units on "+currentTime : unitsTake}
            updateDB(user, adminInstance)

            print("Administer "+str(math.ceil(unitsTake))+" units of bolus insulin. \n")
            break

def newExportCSV(user):
    path = "./"+user+"_Data.csv"
    if os.path.isfile(path):
        os.remove(user+"_Data.csv")
    myclient = pyMongoConnect()
    mydb = myclient["T1D_Database"]
    mycol = mydb["User_Data"]
    found = mycol.find({"Username": user},{"_id": 0})
    foundList = list(found)
    foundDict = dict(ChainMap(*foundList))
    with open(user+"_Data.json", "w") as f:
        json.dump(foundDict, f, indent=2)
    df = pd.read_json(user+"_Data.json", typ='series')
    df.to_csv(user+"_Data.csv")
    os.remove(user+"_Data.json")
    print(user+"_Data.csv file created successfully. \n")

def insertUdB(addedInfo):
    myclient = pyMongoConnect()
    mydb = myclient["T1D_Database"]
    mycol = mydb["Users"]
    mycol.insert_one(addedInfo)

def insertUDdB(addedInfo):
    myclient = pyMongoConnect()
    mydb = myclient["T1D_Database"]
    mycol = mydb["User_Data"]
    mycol.insert_one(addedInfo)

def updateDB(name, updateInfo):
    myclient = pyMongoConnect()
    mydb = myclient["T1D_Database"]
    mycol = mydb["User_Data"]
    mycol.update_one({"Username": name}, {"$set": updateInfo})

def findUI(parameter, find):
    myclient = pyMongoConnect()
    mydb = myclient["T1D_Database"]
    mycol = mydb["Users"]
    found = mycol.find({parameter: find})
    for info in found:
        return info
    
def findUD(name, find):
    myclient = pyMongoConnect()
    mydb = myclient["T1D_Database"]
    mycol = mydb["User_Data"]
    found = mycol.find({"Username": name},{"_id": 0, find: 1})
    for info in found:
        return info

def checkDB(parameter, input):
    myclient = pyMongoConnect()
    mydb = myclient["T1D_Database"]
    mycol = mydb["Users"]
    checkList = mycol.find({parameter: input},{})
    for info in checkList:
        if info is None:
            return False
        else:
            return True
        
def pyMongoConnect():
    uri = "mongodb+srv://jfeinbe3:kpmznlNjPIJQfN34@testcluster.o1l0vf1.mongodb.net/?retryWrites=true&w=majority&appName=TestCluster"
# Create a new client and connect to the server
    client = MongoClient(uri, server_api=ServerApi('1'))
# Send a ping to confirm a successful connection
    try:
        client.admin.command('ping')
        print("\n")
    except Exception as e:
        print(e)
    
    return client

main()




##Commented out code:

"""
    path = "./data.json"
    if os.path.isfile(path):
        f = open("data.json", "r+")
        dataRead = f.read()
        newData = json.loads(dataRead)
        newData.update(newLogin)
        ##f.seek(0)
        json.dump(newData, f, indent=2)
    else:
        f = open("data.json", "x")
        json.dump(newLogin, f, indent=2)
        
        f.write("Logins")
        newData = json.load(f)
        newData["Logins"].append(newLogin)
        f.seek(0)

    def addInfo(name, addedInfo):
        with open(name+"Data.json", "r") as f:
            oldDict = json.load(f)
            #dictionary to list
            newList = list(oldDict.items())
            newList.append(addedInfo)
            #convert back to dictionary
            it = iter(newList)
            newDict = dict(zip(it, it))
        with open(name+"Data.json", "w") as f:
            json.dump(newDict, f, indent=2)

    with open(name+"Data.json") as f:
        jsonData = json.load(f)
    with open(name+"Data.csv", "w") as newCSV:
        csvWriter = csv.writer(newCSV)
        count = 0
        for data in jsonData:
            if count == 0:
                header = data.keys()
                csvWriter.writerow(header)
                count += 1
            csvWriter.writerow(data.values())
        newCSV.close()

    def oldMain(): 
        lastName = login()
        while True:
            with open(lastName+"Data.json", "r") as f:
                readData = json.load(f)
                if "Target BG" in readData:
                    bolusCalc(readData["Correction Factor"], readData["Carb Ratio"], readData["Target BG"], lastName)
                    newLC = int(readData["LC"]) + 1
                    newLCdict = {"LC" : newLC}
                    updateDict(lastName, newLCdict)
                    break
                else:
                    infoAquire(lastName)
                    continue
        csvExport = input("Would you like to export the code as a .CSV file? (Y/N): ")
        if csvExport == "Y":
            exportCSV(lastName)

# Update Data Function: This is the function created to update the data (dictionary) of the user.
def updateDict(name, addedInfo):
    with open(name+"Data.json", "r") as f:
        oldData = json.load(f)
        oldData.update(addedInfo)
    with open(name+"Data.json", "w") as f:
        json.dump(oldData, f, indent=2)

# Read Current Data Function: This function allows the reading of current data values in the users data file by loading it to a dictionary.
def readCurrent(name):
    with open(name+"Data.json", "r") as f:
        readData = json.load(f)
    return readData

# Export to CSV File Function: This function will export the user's data to a CSV file using pandas, and automatically removes any old files with the same name to overwite and update.
def exportCSV(name):
    checkFile = checkDB(name)
    if checkFile is True:
        os.remove(name+"Data.csv")
    df = pd.read_json(name+"Data.json", typ='series')
    df.to_csv(name+"Data.csv")
    print(name+"Data.csv file created successfully. \n")


"""