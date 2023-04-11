# Robot Plotter

This repository contains the code used for the Arboreal Intuitions 2022-23 project.

## Requirements

First things first, you will need any version of the Arduino 1.8 IDE. You can download that [here](https://www.arduino.cc/en/software/OldSoftwareReleases). Once downloaded, you should have an Arduino `libraries` folder (found in `C:\Users\{username}\Documents\Arduino` on Windows).

You will then need to download Python 3.8, which may be found [here](https://www.python.org/downloads/release/python-380/).

## Installation

### Arduino

Copy the `grbl-mod\grbl-mod` folder (just the inner `grbl-mod` one) into your Arduino "libraries" folder.

In your Arduino IDE, open the example code found in `File > Examples > Examples from custom libraries, grbl-mod > grblUpload`. Select your board (Arduino Uno) and COM port (Arduino Uno) from `Tools`. **Take note of the COM port number - it will be used later.**

Click the `Upload` button, and wait for the program to finish compiling/uploading to the board.

### Python

Install the python packages found in the `requirements.txt` file. To do this open a console window in administrator mode (right-click on "Command Prompt", select "Run as Administrator") and navigate to the project's directory. For example:

```powershell
C:\Windows\system32> cd "C:\Users\blah\Downloads\robot-plotter"
C:\Users\blah\Downloads\robot-plotter> pip install --upgrade pip --user
...
Successfully installed pip-23.0.1 

C:\Users\blah\Downloads\robot-plotter> pip install -r .\requirements.txt --user
...
Successfully installed requirement-1.0.0
```

Now you are ready to run Python plotter code!

## Sending G-Code commands

Initialization of the CNC shield is performed using the `GRBL Config` file. This file sets up the servo and stepper motors for the plotter and paper feeder.

TODO: configuration for paper feeder, and modifications to grbl library for motion sensor input/reset.
