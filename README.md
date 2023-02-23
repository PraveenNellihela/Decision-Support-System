# Decision Support System for the SMART2 Rail Project

## General Overview

The aim of SMART2 is the development, implementation and evaluation of a holistic system for the detection of existing
or approaching obstacles (Obstacle Detection and Track Intrusion Detection - OD&TID), identified by sensors located on 
the train, on the track or on drones and connected to a central decision support system (DSS)

Using images captured from these sensors and a machine learning based algorithm (DisNet), the following are calculated 
or identified:  
- the **objectclass** of the existing or approaching obstacles
- the **distance** to existing or approaching obstacles
- and **bounding box coordinates** that depict where these obstacles are located within the image

## The Goal of the DSS

The goal of **this DSS** is to produce a final list of detected obstacles with their **objectclass** and estimated **GPS 
coordinates** by utilizing the above-mentioned data from all onboard sensors and the UAV, at a given time, which could 
then be used to assess the threat of the detected obstacles colliding with the ongoing train.

## Steps taken to achieve the DSS goal

1. Identify the **GPS coordinates** of the existing or approaching obstacles at a given moment in time using 
available data from onboard algorithms:
      - the **objectclass** of the detection of existing or approaching obstacles
      - the **distance** to existing or approaching obstacles
      - and **bounding box coordinates** of the detection

    and the train's GPS coordinate data:
      - the **GPS coordinates** of the train at the given moment in time
      - the **GPS coordinates** of the train at a slight prior moment in time

2. Merge potential duplicate obstacle detections coming from multiple sensors and create a final set of results that 
depict existing or approaching obstacles.

   Since a single existing or approaching obstacle could be detected by several of the available sensors, the DSS should 
   identify such detections and merge them to produce one detection result. 

To achieve step 1, the _**geographic_estimations**_ module was created, which contains various methods to perform the 
necessary geographical data calculations, such as the distance between two GPS coordinates and the compas bearing 
between two GPS coordinates. Refer to the module's [README.md](decision_support_system/geographic_estimations/README.md) 
file for more information.   

Step 2 is achieved by running the _**run_dss.py**_ script and passing in the **.json** files containing obstacle detection data 
from the onboard sensors and the UAV as well as the **current_train_gps** and **previous_train_gps** variables.

The **current_train_gps** and **previous_train_gps** variables contain in tuple form, the GPS coordinates of the train
when the data was written to the .json files and the GPS coordinates of the train at a slight moment before this capture. 

The **_run_dss.py_** script causes the **_decision_support.py_** to be executed, which:
- reads the .json files containing obstacle detection data from the sensors 
- estimate the GPS coordinates of the obstacle detections
- merges potential duplicate detections of the same object captured by multiple sensors and the UAV using a 
weighted approach
- provides the final list of the objectclass and the estimated GPS coordinates of the obstacle detections.

Refer to the [Input Data Used by the DSS](#input-data-used-by-the-dss) section to see some example data used by the 
DSS.

## Setup Work Environment for the First Time 

To set up the work environment and test or run the code in this repo, do the following:
1. Clone this branch.
2. Open a terminal and navigate to the base folder of your project (git clone location e.g: \praveen\dev\decision_support_system)
4. Create a new virtual environment using Python 3.8 (only necessary the first time).

       $ virtualenv venv --python="/usr/bin/python3.8"
      Use the command```which python3.8``` to find the path if necessary.
5. Activate the environment (necessary each time you use a fresh terminal, or add to bash to avoid this)

        $ . ./venv/bin/activate

   (or on Windows run .\venv\Scripts\activate)

6. Install dependencies

       $ pip install -r requirements.txt

7.  Run the decision support system using the run_dss.py script. You need to provide the paths to the RGB1, RGB4, Monochrome, Thermal, SWIR and UAV json files and also the train's current position and previous position. You can increase verbosity by setting ```verbose``` to True and visualize the estimations of a map setting ```show_map``` to True. If you are in the project root:

        python3 decision_support_system/run_dss.py "{path/to/On-board_rgb1.json}" "{path/to/On-board_rgb4.json" "path/to/On-board_mono.json" "path/to/On-board_thermal.json" "path/to/On-board_swir.json" "path/to/UAV.json" "{train_current_GPS}" "{train_previous_GPS}"
    for example:

        python3 decision_support_system/run_dss.py "/home/praveen/devel/decision_support_system/data/set_2/On-board_rgb1.json" "/home/praveen/devel/decision_support_system/data/set_2/On-board_rgb4.json" "/home/praveen/devel/decision_support_system/data/set_2/On-board_mono.json" "/home/praveen/devel/decision_support_system/data/set_2/On-board_thermal.json" "/home/praveen/devel/decision_support_system/data/set_2/On-board_swir.json" "/home/praveen/devel/decision_support_system/data/set_2/UAV.json" "53.0861622, 8.7816742" "53.086040, 8.781514" --verbose="True" --show_map="True"

The synthetic data created can be found in the ```/data/set_2``` directory within this repo. For this data, 
- the train's current position is ```53.0861622, 8.7816742```
- and the previous position is ```53.086040, 8.781514```

## Input Data Used by the DSS

There are 5 onboard sensors on the train:
- 2 RGB cameras (RGB1 and RGB4)
- A monochrome camera
- A thermal camera
- A SWIR camera

These obstacle detection data from these onborad sensors are available as .json files. A sample of such a file from 
RGB1 is shown below.

      {
        "sensorId": "onboard",
        "guid": "a48ec180-262a-40ba-a935-bee2eb5dcada",
        "creationTime": "2022-05-17T07:58:08.937816Z",
        "camera": "RGB1",
        "imagesize": {
          "image_height": 1944,
          "image_width": 2592
        },
        "objects": [
          {
            "objectclass": "car",
            "x_min": "1097.9376",
            "y_min": "1009.6097",
            "x_max": "1525.0789",
            "y_max": "1165.1981",
            "height": "155.58844",
            "width": "427.14124",
            "confidence": "0.45",
            "distance": "16.1"
          }
        ]
      }

Essentially, the onboard sensors provide data about the detected obstacle's **bounding box coordinates** 
(x_min, y_min, x_max, y_max) and the **distance** to the detection from the train's current GPS position (calculated 
by DisNet).

The algorithm inside the UAV directly calculates the estimated **GPS coordinates** of the detected obstacles. Thus, the 
data from the UAV is similar to the data from the onboard sensors, except instead of the **distance** to detection, the
UAV data contains the estimated **GPS coordinates**. See below for a sample.

      {
        "sensorId": "uav",
        "guid": "0bac889f-cffd-46eb-bd15-5960fcf1093c",
        "creationTime": "2022-05-27T15:09:12.936729Z",
        "camera": "UAV",
        "GPS_drone": {
          "latitude": "43.131493",
          "longitude": "21.904913"
        },
        "imagesize": {
          "image_height": 1530,
          "image_width": 2720
        },
        "objects": [
          {
            "objectclass": "person",
            "x_min": "1944.4734",
            "y_min": "228.97227",
            "x_max": "1968.3579",
            "y_max": "283.2375",
            "height": "54.265213",
            "width": "23.884521",
            "confidence": "0.533",
            "GPS_object": {
              "latitude": "43.13075828703845",
              "longitude": "21.903643229491628"
            }
          }
        ]
      }