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
    "Sprite",
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
DEBUG_DICT = {}
tlDebug = False
src = ""


# Credit to K0lb3 for the code I based this off of, as well as the unityPy library in general:
# https://github.com/K0lb3/Romancing-SaGa-Re-univerSe-asset-downloader/blob/24388c660c3ed40665d840b6cf46bbbd48d63b8e/lib/asset.py


def main():
    holoErrorDirectory = os.getcwd()
    while not (os.path.isfile((os.path.join(holoErrorDirectory, "hololiveERROR.exe")))):
        if os.path.dirname(holoErrorDirectory) == holoErrorDirectory:
            input("hololiveERROR.exe not found!")
            return 1
        else:
            holoErrorDirectory = os.path.dirname(holoErrorDirectory)
            # Move up the directory tree, one directory at a time

    TL_path = os.path.join(holoErrorDirectory, "TranslationPatch")
    if not (os.path.isdir(TL_path)):
        input("TranslationPatch folder not found!")
        return 1
    global src
    src = os.path.join(holoErrorDirectory, "hololiveERROR_Data")
    # print(src)
    if not (os.path.isdir(src)):
        input("hololiveERROR_Data folder not found!")
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
                                                          and f.path[f.path.rfind("\\") + 1::] != "debugOverrides")]
    i = 1
    for sf in subFolders:
        print(str(i) + ") " + sf[sf.rfind("\\") + 1::])
        i = i + 1

    fileList = ["level0", "sharedassets0.assets"]  # These are the two files that require editing.
    if os.path.isfile(os.path.join(src, fileList[0] + "_JP")):
        print(str(i) + ") Restore original language")

    TL_num = -1
    while not (0 <= TL_num - 1 <= len(subFolders)):
        try:
            TL_num = int(input("Please select which translation you would like to use.\n"))
        except:
            print("Not a valid number.")

    global DEBUG_DICT
    global T2D_JSON

    if os.path.isdir(os.path.join(TL_path, "debugOverrides")):
        print("debugOverrides found, patching files manually")
        debugFileList = [f.path for f in os.scandir(os.path.join(TL_path, "debugOverrides")) if
                         (f.is_file() and (f.name.endswith(".json")))]
        for f in debugFileList:
            DEBUG_DICT[f[f.rfind("#") + 1:f.rfind("."):]] = f

    TL_num = TL_num - 1
    if TL_num == len(subFolders):
        # User wants to restore japanese language. Do that and exit.
        for resFile in fileList:
            curFile = os.path.join(src, resFile)
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
        curFile = os.path.join(src, resFile)
        if not os.path.isfile(curFile + "_JP"):  # If JP file doesn't exist, move the original one.
            if os.path.isfile(curFile):
                os.rename(curFile, curFile + "_JP")
            else:
                input("Error, resource file " + curFile + " not found.")
                return

        edit_asset(curFile + "_JP", TL_path)

    input("All done! Press Enter to exit.\n")

    # Okay, so, some of you are going to ask "why the fuck do we have to run a separate file."
    # The answer is that unityPy, as far as I can tell, doesn't support closing the file handle without killing
    # the entire process, and I'm not going to redistributed a modified version of the library because that
    # would be hell.


def edit_asset(inp, TL_path):
    env = UnityPy.load(inp)
    env.files["globalgamemanagers.assets"] = env.load_file(os.path.join(src, "globalgamemanagers.assets"))
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


def overwrite_obj(obj, TL_path: str, append_name: bool = False) -> list:
    if obj.type.name not in TYPES:
        return []
    if not STRUCTS:
        with open(STRUCTS_PATH, "rt", encoding="utf8") as f:
            STRUCTS.update(json.load(f))

    if not MB_JSON:
        with open(os.path.join(TL_path, "subtitles.json"), "rt", encoding="utf8") as f:
            MB_JSON.update(json.load(f))

    data = obj.read()

    if obj.type == ClassIDType.TextAsset:
        print("TextAsset found!")
        input(data.script)

    # streamlineable types
    export = None
    if obj.type == ClassIDType.MonoBehaviour:

        # if TLDebug is set, modify all available monobehaviours

        if not str(obj.path_id) in MB_JSON:
            if not str(obj.path_id) in DEBUG_DICT:
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
        else:  # I'm leaving this here even if for this game it shouldn't be necessary.
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

                if str(obj.path_id) in DEBUG_DICT:
                    # COMPLETELY DEBUG FEATURE, SHOULD NOT BE USED.
                    # Replace the entire thing.
                    with open(DEBUG_DICT[str(obj.path_id)], "rt", encoding="utf8") as f:
                        export = f.read()
                        export = json.loads(export)
                        obj.save_typetree(export, nodes)
                        break

                export = json.dumps(obj.read_typetree(nodes), indent=4, ensure_ascii=False)

                # Check if this is textEffect, if so, disable it and break.
                if obj.path_id == 226546:
                    export = export.replace("\"m_Enabled\": 1,", "\"m_Enabled\": 0,")
                    export = json.loads(export)
                    obj.save_typetree(export, nodes)
                    break

                i = export.rfind("m_Text\": ") + len("m_Text\": ")
                if export.rfind("m_Text\": ") == -1:
                    break
                beforeText = export[0:i + 1]
                JPtext = export[i + 1:export.index("\n", i) - 1]
                afterText = export[export.index("\n", i) - 1:len(export)]

                # Check if this is the startup red text. If so, modify the line height.
                if obj.path_id == 232224:
                    beforeText = beforeText.replace("\"m_LineSpacing\": 1.0", "\"m_LineSpacing\": 1.1")

                if MB_JSON[str(obj.path_id)] == "":
                    if tlDebug:
                        export = beforeText + "#" + str(obj.path_id) + " " + JPtext + afterText
                        # Text is missing TL, just add the ID. More of an edge case than anything.
                else:
                    decoded = str(MB_JSON[str(obj.path_id)].replace("\n", "\\n").replace("\r", "\\r")) \
                        .replace("\"", "\\\"")
                    decoded = re.sub(r'(?<!\\)\\(?!["\\/bfnrt]|u[0-9a-fA-F]{4})', r'', decoded)
                    if tlDebug:
                        # Stupid encoding jank, I know it's ugly
                        export = beforeText + "#" + str(obj.path_id) + " " + decoded + afterText
                        # Add TL and ID.
                    else:
                        export = beforeText + decoded + afterText
                        # Just add the TL.
                # new_data = json.load(open("edited.json", "rt", encoding="utf8"))
                export = json.loads(export)
                obj.save_typetree(export, nodes)
                break

    elif obj.type == ClassIDType.Texture2D:
        from PIL import Image
        if str(obj.path_id) in T2D_JSON:  # Check if ID is in JSON.
            print("Patching Texture2D with ID : " + str(obj.path_id))
            img_data = Image.open(os.path.join(TL_path, "textureOverrides", T2D_JSON[str(obj.path_id)]))
            data.set_image(img_data, mipmap_count=data.m_MipCount)
            data.save()

    elif obj.type == ClassIDType.Sprite:
        if "idou" == data.name:
            return [obj.path_id]

            # This was a test to see if I could increase the size of the "MOVE" text.
            # It did not work.

            from PIL import Image
            print(str(obj.path_id))
            print(data.name)
#            data.image = Image.open(os.path.join(TL_path, "textureOverrides", "idou #492.png"))
            print(data.m_Rect.size)
            data.m_RD.textureRect.bottom = 46
            data.m_RD.textureRect.height = 46
            data.m_RD.textureRect.size = (94, 46)
            data.m_RD.textureRect.width = 94
            data.m_RD.uvTransform.X = 100
            data.m_RD.uvTransform.Z = 100
            data.m_RD.uvTransform.W = 11.5
            data.m_RD.uvTransform.Y = 23.5
            print("")
            data.save()


    return [obj.path_id]


class Fake:
    def __init__(self, **kwargs) -> None:
        self.__dict__.update(**kwargs)


if __name__ == "__main__":
    main()
