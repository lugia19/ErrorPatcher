# Translation injector for Hololive ERROR

## How do I install the patch?
Grab the Translation.zip file for the latest version from the [releases page](https://github.com/lugia19/ErrorPatcher/releases), and unzip it in the same folder as HololiveERROR.exe.
You now should have a folder called TranslationPatch. 

If you're on windows, simply run patchGame.bat, select the language you want and you're done. 


### What if I'm not on Windows?
Download editAssets.py, put it in the TranslationPatch folder, install the required libraries (UnityPy and Pillow) and run it.

UnityPy might give you some trouble as it requires pythonnet 3, which can't currently install normally via pip.
Just run `pip install git+https://github.com/pythonnet/pythonnet.git` (Requires git to be installed).


## How do I make a translation for another language?

The short version is:
- Download the ResourcesForTranslators.zip file from the releases page (it has its own README with more details)
- Create a folder inside of TranslationPatch with the language name, with a textureOverrides subfolder
- Edit the subtitles.csv to include your own translation
- Run the csvToJSON script on it to create a subtitles.json file, and put it in the newly created folder.
- Use the provided PSD files to edit the various textures, and put the resulting PNGs in the textureOverrides folder
- Done! Feel free to send it to me and I'll include it in the download.

## Special Thanks
Special thanks to Tungsten for making the texture edits and darktossgen for the English translation, as well as being putting up with all my rants.

This program leverages the [UnityPy](https://pypi.org/project/UnityPy/) library to modify the game assets. Special thanks to its developer for helping me figure out how to use it properly.
If you'd like to know more about how the patch itself works, as well as how to make something similar for other games, I made [this video]().
