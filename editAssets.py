import os
import UnityPy
from collections import Counter
import zipfile
import json
import re
import PIL as PIL
from UnityPy.enums import ClassIDType
from UnityPy.helpers.TypeTreeHelper import TypeTreeNode
from UnityPy.enums.TextureFormat import TextureFormat

STRUCTS_PATH = ""
TYPES = [
    # Images
    # "Sprite",
    "Texture2D",
    # Text (filish)
    # "TextAsset",
    "MonoBehaviour",
    # Font
    # "Font",
    # Audio
    # "AudioClip",
]

STRUCTS = {}
MB_JSON = {}
T2D_JSON = {}
SPECIAL_OVR = {}
tlDebug = False
dataFolder = ""
# Credit to K0lb3 for the code I based this off of, as well as the unityPy library in general:
# https://github.com/K0lb3/Romancing-SaGa-Re-univerSe-asset-downloader/blob/24388c660c3ed40665d840b6cf46bbbd48d63b8e/lib/asset.py
def main():
    rootDirectory = os.getcwd()
    while not (os.path.isfile((os.path.join(rootDirectory, "GameAssembly.dll")))):
        if os.path.dirname(rootDirectory) == rootDirectory:
            input("GameAssembly.dll could not be found in any above directory!")
            return 1
        else:
            rootDirectory = os.path.dirname(rootDirectory)
            # Move up the directory tree, one directory at a time
    TL_path = os.path.join(rootDirectory, "TranslationPatch")
    if not (os.path.isdir(TL_path)):
        input("TranslationPatch folder not found!")
        return 1
    global dataFolder
    for dirName in os.listdir(rootDirectory):
        if os.path.isdir(os.path.join(rootDirectory, dirName)):
            if "_Data" in dirName:
                dataFolder = os.path.join(rootDirectory, dirName)
                break  # We've got our _Data directory
    # print(src)
    if not (os.path.isdir(dataFolder)):
        input("Data folder not found!")
        return
    if os.path.isfile(os.path.join(TL_path, "tlDebug.txt")):
        print("Would you like the subtitle IDs to be printed alongside the text?")
        answerTemp = input("y/n\n")
        while answerTemp.lower() != "y" and answerTemp.lower() != "n":
            print("Not a valid answer. \n")
            answerTemp = input("y/n\n")
        global tlDebug

        if answerTemp.lower() == "y":
            tlDebug = True
        else:
            tlDebug = False
    subFolders = [f.path for f in os.scandir(TL_path) if (f.is_dir() and f.path[f.path.rfind("\\") + 1::] != "exeData"
                                                          and f.path[f.path.rfind("\\") + 1::] != "specialOverrides")]
    i = 1
    for sf in subFolders:
        print(str(i) + ") " + sf[sf.rfind("\\") + 1::])
        i = i + 1
    if os.path.isfile(os.path.join(dataFolder, "sharedassets0.assets_JP")):
        print(str(i) + ") Restore original language")

    fileList = []  # These are the files that require editing.
    i = 0
    while os.path.isfile(os.path.join(dataFolder, "level" + str(i))):
        fileList.append("level" + str(i))
        i = i + 1
    i = 0
    while os.path.isfile(os.path.join(dataFolder, "sharedassets" + str(i) + ".assets")):
        fileList.append("sharedassets" + str(i) + ".assets")
        i = i + 1
    # if os.path.isfile(os.path.join(dataFolder, "globalgamemanagers.assets")):
    #    fileList.append("globalgamemanagers.assets")
    if os.path.isfile(os.path.join(dataFolder, "resources.assets")):
        fileList.append("resources.assets")

    TL_num = -1
    while not (0 <= TL_num - 1 <= len(subFolders)):
        try:
            TL_num = int(input("Please select which translation you would like to use.\n"))
        except:
            print("Not a valid number.")

    global SPECIAL_OVR
    global T2D_JSON

    if os.path.isdir(os.path.join(TL_path, "specialOverrides")):
        debugFileList = [f.path for f in os.scandir(os.path.join(TL_path, "specialOverrides")) if
                         (f.is_file() and (f.name.endswith(".json")))]
        for f in debugFileList:
            SPECIAL_OVR[f[f.rfind("#") + 1:f.rfind("."):]] = f

    TL_num = TL_num - 1
    if TL_num == len(subFolders):
        # User wants to restore japanese language. Do that and exit.
        for resFile in fileList:
            curFile = os.path.join(dataFolder, resFile)
            if os.path.isfile(curFile + "_JP"):  # Only do this is there's a corresponding JP version.
                if os.path.isfile(curFile): os.remove(curFile)
                os.rename(curFile + "_JP", curFile)
        return
    TL_path = subFolders[TL_num]

    if os.path.isdir(os.path.join(TL_path, "textureOverrides")):
        textureOverrides = [f.path for f in os.scandir(os.path.join(TL_path, "textureOverrides")) if
                            (f.is_file() and (f.name.endswith(".png")))]
        for f in textureOverrides:
            T2D_JSON[f[f.rfind("#") + 1:f.rfind("."):]] = f

    global STRUCTS_PATH
    STRUCTS_PATH = os.path.join(TL_path[:TL_path.rfind("\\"):], "exeData", "typetrees.json")

    if not (os.path.isfile(STRUCTS_PATH)):
        input("Error, file is not alongside typetrees.json, did you change the working directory?")
        return 1
    for resFile in fileList:
        curFile = os.path.join(dataFolder, resFile)
        if not os.path.isfile(curFile + "_JP"):  # If JP file doesn't exist, move the original one.
            if os.path.isfile(curFile):
                os.rename(curFile, curFile + "_JP")
            else:
                input("Error, resource file " + curFile + " not found.")
                return
        edit_asset(curFile + "_JP", TL_path)

    input("All done! Press Enter to exit.\n")


def edit_asset(inp, TL_path):
    env = UnityPy.load(inp)
    env.files["globalgamemanagers.assets"] = env.load_file(os.path.join(dataFolder, "globalgamemanagers.assets"))
    print("Modifying file " + inp)
    # make sure that Texture2Ds are at the end
    objs = sorted(
        (obj for obj in env.objects if obj.type.name in TYPES),
        key=lambda x: 1 if x.type == ClassIDType.Texture2D else 0,
    )
    # check how the path should be handled
    if len(objs) == 1 or (
            len(objs) == 2 and objs[0].type == ClassIDType.Sprite and objs[1].type == ClassIDType.Texture2D
    ):
        overwrite_obj(objs[0], os.path.dirname(TL_path), True)
    else:
        used = []
        for obj in objs:
            if obj.path_id not in used:
                used.extend(overwrite_obj(obj, TL_path, True))

    # Save patched file to directory.
    with open(inp[0:inp.rfind("_")], "wb") as f:
        f.write(env.file.save())


def csvToJsonData(TSVfileLocation):
    data = {}
    with open(TSVfileLocation, encoding="utf8") as f:
        lines = f.readlines()
        last = lines[-1]
        lineIndex = 0
        for line in lines:
            lineIndex = lineIndex + 1
            if lineIndex == 1:
                try:
                    # Check if the first cell is an integer.
                    int(line[0:line.index("\t"):])
                except ValueError:
                    # It's not, assume these are the headers.
                    continue
            try:
                currentID = line[0:line.index("\t"):]
                tlText = line[line.rfind("\t") + 1:len(line):].rstrip()
            except:
                print("Error! Subtitles files is not formatted correctly, please check line " + str(lineIndex))
                input("Press enter to exit.")
                raise Exception("Incorrect formatting")
            data[currentID] = tlText
    return data


def overwrite_obj(obj, TL_path: str, append_name: bool = False) -> list:
    global MB_JSON
    if obj.type.name not in TYPES:
        return []
    if not STRUCTS:
        with open(STRUCTS_PATH, "rt", encoding="utf8") as f:
            STRUCTS.update(json.load(f))

    if not MB_JSON:
        JSONdata = csvToJsonData(os.path.join(TL_path, "subtitles.tsv"))
        if os.path.isfile(os.path.join(TL_path, "subtitles.tsv")):
            MB_JSON = csvToJsonData(os.path.join(TL_path, "subtitles.tsv"))
        if os.path.isfile(os.path.join(TL_path, "subtitles.csv")):
            MB_JSON = csvToJsonData(os.path.join(TL_path, "subtitles.csv"))
        if not MB_JSON:
            print("Error! Could not find subtitles tsv/csv file.")
            input("Press enter to exit.")
            raise Exception("Subtitles not found")

    data = obj.read()

    if obj.type == ClassIDType.TextAsset:
        print("TextAsset found!")
        input(data.script)

    # streamlineable types
    export = None
    if obj.type == ClassIDType.MonoBehaviour:

        # if TLDebug is set, modify all available monobehaviours
        if not str(obj.path_id) in MB_JSON:
            if not str(obj.path_id) in SPECIAL_OVR:
                return [obj.path_id]
        # Only edit if the path id is in the dict
        # The data structure of MonoBehaviours is custom
        # and is stored as nodes
        if obj.serialized_type.nodes:
            # This piece of code is never going to run, but I might as well leave it in. Better safe than sorry.
            export = json.dumps(
                obj.read_typetree(), indent=4, ensure_ascii=False
            )

            i = export.rfind("m_Text\": ") + len("m_Text\": ")
            JPtext = export[i + 1:export.index("\n", i) - 1]
            export = export.replace(JPtext, MB_JSON[str(obj.path_id)])

            export = json.loads(export)
            obj.save_typetree(export)
        else:
            for i in [1]:
                # abuse that a finished loop calls else
                # while a broken one doesn't
                script = data.m_Script
                if not script:
                    print("Script not found!")
                    continue
                script = script.read()
                try:
                    nodes = [TypeTreeNode(x) for x in STRUCTS[script.m_AssemblyName][script.m_ClassName]]
                except KeyError as e:
                    print("Key not found for: ")
                    print(e)
                    continue
                # adjust the name
                name = (
                    f"{script.m_ClassName}-{data.name}"
                    if data.name
                    else script.m_ClassName
                )

                print("Patching MonoBehaviour with ID : " + str(obj.path_id))
                try:
                    currJSON = obj.read_typetree(nodes)
                except Exception as e:
                    print(e, obj.path_id, script.m_AssemblyName, script.m_ClassName)
                    return [obj.path_id]

                # currJSON = obj.read_typetree(nodes)
                if str(obj.path_id) in SPECIAL_OVR:
                    print("Found a special override, apply it.")
                    # Replace the entire JSON with the modified version.
                    # This way we can still apply translations as normal.
                    # Was a debug-only feature, now I use it for special cases so I don't have to hardcode them in.
                    with open(SPECIAL_OVR[str(obj.path_id)], "rt", encoding="utf8") as f:
                        currJSON = json.loads(f.read())

                textItem = ""
                if "m_text" in currJSON:
                    textItem = "m_text"
                elif "m_Text" in currJSON:
                    textItem = "m_Text"
                if textItem != "":
                    newText = ""
                    if tlDebug:
                        newText = "#" + str(obj.path_id) + " "
                    if MB_JSON[str(obj.path_id)] == "":
                        newText = newText + currJSON[textItem]
                    else:
                        newText = newText + MB_JSON[str(obj.path_id)]
                    # This reverse escapes special characters.
                    currJSON[textItem] = newText.encode('raw_unicode_escape').decode('unicode_escape')

                obj.save_typetree(currJSON, nodes)
                break
    elif obj.type == ClassIDType.Texture2D:
        from PIL import Image
        if str(obj.path_id) in T2D_JSON:  # Check if ID is in JSON.
            print("Patching Texture2D with ID : " + str(obj.path_id))
            img_data = Image.open(os.path.join(TL_path, "textureOverrides", T2D_JSON[str(obj.path_id)]))
            data.set_image(img_data, mipmap_count=data.m_MipCount)
            data.save()

    # elif obj.type == ClassIDType.Sprite:
    #    if "idou" == data.name:
    #       return [obj.path_id]
    return [obj.path_id]


class Fake:
    def __init__(self, **kwargs) -> None:
        self.__dict__.update(**kwargs)


if __name__ == "__main__":
    main()
