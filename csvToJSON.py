import os

def main():
    workingDir = os.getcwd()
    i = 0
    print("Please select the csv/tsv file (the separator must be a tab character) to turn it into a JSON.")
    i = 0
    csvFiles = [f.path for f in os.scandir(os.getcwd()) if (f.is_file() and (f.name.endswith(".csv")) or f.name.endswith(".tsv"))]
    if len(csvFiles) == 0:
        print("No files in " + os.getcwd())
        return
    for file in csvFiles:
        print(str(i+1) + ") " + file[file.rfind("\\") + 1::])
        i = i+1

    fileNum = -1

    while not (0 <= fileNum - 1 <= len(csvFiles)):
        try:
            fileNum = int(input("Please choose a file by inputting the number.\n"))
        except:
            print("Not a valid number.")

    fileNum = fileNum-1

    fileName = csvFiles[fileNum]

    print("WARNING. THIS WILL OVERRIDE ANY FILE CALLED subtitles.json IN THIS FOLDER. CONTINUE?")
    answerTemp = input("y/n\n")
    while answerTemp.lower() != "y" and answerTemp.lower() != "n":
        print("Not a valid answer. \n")
        answerTemp = input("y/n\n")
    if answerTemp.lower() == "n":
        return

    outputFile = open("subtitles.json", "w", encoding="utf8")
    outputFile.write("{\n")
    with open(fileName, encoding="utf8") as f:
        lines = f.readlines()
        last = lines[-1]
        for line in lines:
            print(line.rstrip())
            try:
                currentID = line[0:line.index("\t"):]
                tlText = line[line.rfind("\t")+1:len(line):].rstrip().replace("\"", "\\\"")
            except:
                print("something went wrong, are you sure the values are separated by tabs?")
                input("Press enter to exit.")
                return
            print(currentID)
            print(tlText)
            outputFile.write("\t\"" + currentID + "\" : \"" + tlText + "\"")
            # if line != last:
            #    outputFile.write(",")
            outputFile.write(",")
            outputFile.write("\n")

    outputFile.write("\t\"" + str(226546) + "\" : \"" + "DO NOT EDIT THIS LINE!" + "\"\n")
    outputFile.write("}")
    outputFile.close()
    input("Done, hit enter to exit.")


if __name__ == "__main__":
    main()