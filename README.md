# FaReT
**Fa**ce **Re**search **T**oolkit: A free and open-source toolkit of three-dimensional models and software to study face perception.

![](example.gif)

Please use the following reference when you use FaReT in your research:

**Hays, J., Wong, C., & Soto, F. A. (2019). FaReT: A free and open-source toolkit of three-dimensional models and software to study face perception.**

## Table of contents
* [Installation](#installation)
* ["Morphing" in 3d shape space](#morphing-in-3d-shape-space)
   * [Interpolation (i.e., morphing)](#interpolation-ie-morphing) 
   * [Extrapolation (i.e., caricaturing)](#extrapolation-ie-caricaturing)
* [Creating average models](#creating-average-models)
* [Standardizing models](#standardizing-models)
* [Creating dynamic animations from render sequences](#creating-dynamic-animations-from-render-sequences)
* [Communicating with Psychopy to render faces online](#communicating-with-psychopy-to-render-faces-online)

# Installation
## Instal pre-requisites
* You can download and install MakeHuman (stable version) from the following website: <http://www.makehumancommunity.org/content/downloads.html>. This is all you need to use FaReT and generate single face images.
* We have also developed a GIMP plugin that generates dynamic GIF files from a sequence of images rendered from MakeHuman. To use this plugin, download and install GIMP from the following website: <https://www.gimp.org/>

## Download FaReT
* Click on the green button labeled `Clone or Download` above, and then choose `Download ZIP`
* Once the ZIP file is downloaded, open it with your unzipping software.

## MakeHuman plugins
* Locate your makehuman installation directory.
    * **On Windows**, find the MakeHuman shortcut located where you unzipped MakeHuman. Right-click on the shortcut and choose `Open File Location`. This will open the installation folder.
    * **On MacOS X**, open Finder and go to the folder where MakeHuman has been installed. This is usually the `Applications` folder. Right-click (or control+click) the MakeHuman shortcut and choose `Show Package Contents`.
    * **On Debian-like** systems, when using a package management, the folder is found at `/usr/share/makehuman`. 
* Inside the MakeHuman directory, you will find a sub-folder called `PlugIns` or `plugins`.
* From the downloaded FaReT folder, copy the entire sub-folders `4_average_model`, `4_interpolate_render`, `4_socket_psychopy`, and `4_standardizer`.
* Paste the subfolders and their contents into MakeHuman's plugins folder.
* If you already had MakeHuman open ***before*** you installed the plugin, close it and ***re-open*** it so that the plugin will load.
* When loaded correctly, each plugin will produce a new menu as described below.

## GIMP Plugin
* If GIMP is already opened, close it.
* From the downloaded FaReT folder, copy the `make_gif_plugin.py` file and paste it into the **.gimp-2.8/plug-ins** folder.
    * Refer to this page <https://en.wikibooks.org/wiki/GIMP/Installing_Plugins> for specific plugin installation instructions depending on your operating system. 

# "Morphing" in 3d shape space
## Interpolation (i.e., "morphing")
* Because it is an altered version of the Render Task View, it has the same options and more (which were mostly added in the right pane).
* ![](https://mfr.osf.io/export?url=https://osf.io/3jav4/?action=download%26mode=render%26direct%26public_file=False&initialWidth=684&childId=mfrIframe&parentTitle=OSF+%7C+IRscreen.jpeg&parentUrl=https://osf.io/3jav4/&format=2400x2400.jpeg)

* On the left, specify the folder in which you want the program to output the PNG files for each frame of the morph.
  * The images that go into that directory have a naming convention such that the first frame is MH_0000.png, the second is MH_0001.png, etc.
  
### **Total Frames**
* The integer value represents the number of pictures that will be outputted to the output directory.
* Having higher values leads to more precision in the morphs, but also larger GIF file sizes and longer rendering times.
* To test your interpolation settings quickly, start with a small number of total frames. 

### **Interpolation Frames**
* Each row represents a key frame: a starting/ending point of a transformation.
* The **Add Frame** button will save the contents of the Interpolation Settings (below) to a new key frame in the Interpolation Frames list.
* The **Remove Frame** button will delete the selected key frame from the list.
* The **Save As** button will allow you to store your settings into a JavaScript Object Notation (JSON) file so that you do not have to redo them repeatedly.
* The **Load** button loads your previously saved settings from any given json file.

### **Interpolation Settings**
* Once you add a frame, select it to edit the interpolation settings. 
* The **Current Frame** represents the time at which the settings listed below should be reached.
  * By specifying an integer, you can set a specific frame (like frame 61).
  * By specifying a float between 0.0 and 1.0, you can specify the proportion of the total frames (i.e., 0.5 is halfway through the animation).
  * ***Important***: there should always be one key frame that is at frame 0 (start of the morph) and one key frame that is at at 1.0 (end of the morph).
    * ![](https://mfr.osf.io/export?url=https://osf.io/rz93e/?action=download%26mode=render%26direct%26public_file=False&initialWidth=684&childId=mfrIframe&parentTitle=OSF+%7C+Frames.jpeg&parentUrl=https://osf.io/rz93e/&format=2400x2400.jpeg)
    * Unless there is only one frame, in which case, you can have just key frame 0.
* For ***any of the following settings***, you do not need to specify them after the first frame (unless you want them to change).
    * The **Orbit Camera Y** setting can be set to an angle (in degrees).
      * The value causes left-right motion to occur (positive values rotate to the head's right -- your left).
    * The **Orbit Camera X** setting can also be set to an angle (in degrees).
      * The value causes up-down motion to occur (positive values rotate to the top of the head).
    * The **Model File** input box takes the path of a mhm file that you want to have by the current key frame.
    * The **Expression File** input box can either:
      * take an expression mhpose file or..
      * take the word **None**, which means that it should use a neutral expression.
        * The word none is necessary, if no expression will be used. 
* The Update Frame button will change the parameters of a ***selected*** frame.
  * Do *not* select a new frame after making changes you want to save because that will load that frame, overriding your changes.  
  * If you forgot to select the frame first (or the GUI code deselected it after a previous Update), then you can use the **Add Frame** button instead and then remove the frame you wanted to replace/update.

## Extrapolation (i.e., "caricaturing")

# Creating average models
* The **Average Model** menu is under the **Utilities** menu.
* The **Input Directory** specifies the location of the \*.mhm model files you want to average.
  * Keep in mind: the input directory only grabs \*.mhm files from that directory and one layer of subdirectories.
    * i.e., when selecting **identity_models**, it can reach **identity_models/male/\*.mhm**,
    * but not:  **identity_models/male/happy/\*.mhm**
* The **Start** button will generate the average model from the files in the input directory (this may take some time).
  * **Important**: When it finishes, be sure to use MakeHuman's normal save feature to save the average mhm file!
* The remaining functions are only important if you want to generate faces within the average space (which don't always look great).
    * You can avoid re-creating the average if you **Save the Average JSON** files to the input folder you selected earlier.
      * This creates four json files that keep track of the values for the mean, standard deviation, minimums, and maximums for each parameter.
      * You can Load the Average JSONs from the same folder to reload the average model and the parameters for the average space.
    * **Generate Randomly from Average** uses the average parameters, the standard deviations, and the upper and lower limits to generate a new face.
        * Values are sampled from a normal distribution using the mean and standard deviation, but they cannot exceed the minimum or maximum values.
        * If there is only one possible value, it is selected.

# Standardizing models

# Creating dynamic animations from render sequences
## Using GIMP plugin to create GIF files
### **GUI**
If you only need to produce one GIF file, this is the easiest way to do it.
* The **Make-GIF** button will appear at the bottom of the Filters Menu (underneath the Python-Fu and Script-Fu buttons).
* In the **first text-box**, provide the path to the folder containing the PNG image frames that you produced with MakeHuman.
* In the **second text-box**, provide the output path and the output file format -- the GUI can only produce one GIF at a time, so any filename ending with ".gif" is fine.
* The **Frames per second box** is the delay between switching frames in milliseconds.  The default is for 30 frames per second (33.3333 ms).

### **Python-Fu**
If you want to produce several GIF files, then this is the best way to do so.
* Use the Python-Fu console in GIMP (modify the input paths under the **# call the function** comment):
```python
def mass_make_gifs(super_path, out_file_path_format, fps=33.33333):
    # super_path contains multiple folders that each have PNG files
    # out_file_path_format has the _existing_ output directory 
    #  AND the file format:
    # out_file_path_format = "C:/Users/Jason/out_directory/MH_{0:04d}.gif"
    paths = [os.path.join(super_path, folder) for folder in os.listdir(super_path)]
    pdb.python_fu_make_gif(paths, out_file_path_format, fps)
    
# call the function
mass_make_gifs("C:/path-to-png-folders/", "C:/path-to-png-folders/MH_{0:04d}.gif", 33.33333)
```

# Communicating with Psychopy to render faces online
The Socket Render plugin is made for telling MakeHuman what to do from PsychoPy or any Python project.

## PsychoPy Installation
Copy these files next to your PsychoPy experiment file (or into the site-packages library that PsychoPy uses):
* communicator.py
  * MakeHuman also needs communicator.py, so do not use Cut to move it out of 4_socket_render: Copy it.
* py_client.py

## Setting up MakeHuman
* In MakeHuman, navigate to the Rendering tab at the top of the window.
* Select the "Socket Render" subtab.
* When you are ready to open a connection to PsychoPy, push the button labeled "Socket Render", which starts a local server that is waiting for the py_client to connect.  
  * MakeHuman will appear to "stall" while it is waiting for input from the Python client: you cannot interact directly with MakeHuman's GUI while it is taking instructions from the Python client.
* Make sure that you start the server before running the PsychoPy experiment.

## Setting up PsychoPy
Within PsychoPy, you need to import the PythonMHC communication class.
```python
from py_client import PythonMHC
makehuman = PythonMHC()
```
If you want to avoid having to restart MakeHuman every time you exit a PsychoPy run, add this to the beginning of the experiment script as well:
```python
import atexit
# when the session ends, close the link, but keep the server alive, waiting for the next PsychoPy run.
# at the end of a run, makehuman.close() will send the string, 'exit', 
#  to tell MakeHuman's server to wait for another connection from PsychoPy.
atexit.register(makehuman.close)
```

Now you have a connection with MakeHuman from PsychoPy!
The most important function in py_client.py is execute_MH():
* It takes the name of a function as a string,
* Whether you want MakeHuman to return the output of the function,
* Whether you want PsychoPy to wait for that return message to come back before moving on,
* And, the arguments you want to pass to MakeHuman.

This is an example of how you could load a model.
```python
filename = "C:/Example/Model.mhm" # the absolute path
makehuman.execute_MH("gui3d.app.loadHumanMHM", False, False, filename)
```
However, for your convenience, some functions -- like load_model() -- are set up ahead of time:
```python
# makehuman.*function* functions almost all wrap around execute_MH()
makehuman.load_model(filename)
# make the camera look at the face
makehuman.setFaceCamera()
# retrieve the shape parameter dictionary
params = makehuman.get_model_params()
# set and update the model's shape parameters
makehuman.set_model_params(params)

emotion_file = "C:/Example/Emotion.mhpose"
# load the expression parameters for neutral and some emotion (as specified by an mhpose file).
neutral, emotion = makehuman.load_expression(emotion_file)
# set an emotional expression at a specific percentage
makehuman.set_expression(neutral, emotion, 50.0) # 0.0 would be purely neutral, 100 would be "fully" expressing the emotion.

# you can specify how you want MakeHuman to render each stimulus.
render_settings = dict()
render_settings['AA'] = True#/False #anti-aliasing -- smoothing by rendering at a larger scale and then downscaling
render_settings['dimensions'] = (256, 256) # how big is the image
render_settings['lightmapSSS'] = False # do you want cool, slow to render lighting effects?

save_location = "C:/Example/Image_Folder/"
image_number = 0
# Ask MakeHuman to render and save whatever to the save location, 
#  and wait until MakeHuman finishes before moving on.
image_path = makehuman.get_render(save_location, render_settings, image_number)
# you only need to increment the image number want to reserve
# the previously rendered image for the next time
# (or if you are going to render multiple images in one trial).
#image_number+=1

# $image_path can be given to ImageStim components as long as the Image is set every repeat.
```

If you want to kill the server without terminating MakeHuman's process, you can send the string 'shutdown' to resume MakeHuman's normal processing.  
```python
# unlike when MakeHuman receives the 'exit' string (which only indicates that 
#  the PsychoPy/Python client has left),
# shutting down the MakeHuman server means you will have to click the "Socket Render"
# button again before you want to start the next PsychoPy Run.
makehuman.send('shutdown')
```





