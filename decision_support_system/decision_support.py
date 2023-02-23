import geographic_estimations.geographic_estimations as geographic_estimations
import folium
import json
import itertools
from collections import defaultdict
from math import ceil

icon_colors = {
    'RGB1': "beige",
    'RGB4': "green",
    'Monochrome': "blue",
    'Thermal': "red",
    'SWIR': "purple",
    'UAV': "lightgray"
}


def read_json(file_path):
    with open(file_path) as f:
        return json.load(f)


class DetectionMerger(object):
    def __init__(self, rgb1, rgb4, mono, therm, swir, uav, train_current, train_prev, verbose, show_map, output_file):
        """
        Initializes the DetectionMerger class and sets initial values for class variables.

        Parameters:
            - rgb1 (str): Path to the JSON file containing RGB1 sensor data.
            - rgb4 (str): Path to the JSON file containing RGB4 sensor data.
            - mono (str): Path to the JSON file containing Monochrome sensor data.
            - therm (str): Path to the JSON file containing Thermal sensor data.
            - swir (str): Path to the JSON file containing SWIR sensor data.
            - uav (str): Path to the JSON file containing UAV sensor data.
        """
        self._read_data_from_files(rgb1, rgb4, mono, therm, swir, uav)
        self._initialize_variables(train_current, train_prev, verbose, show_map, output_file)
        self._initialize_zones()
        self._initialize_weights()
        self._initialize_map()

    def _read_data_from_files(self, rgb1, rgb4, mono, therm, swir, uav):
        """Reads in the data from the given JSON files and assigns it to class variables."""
        self.rgb1 = read_json(rgb1)
        self.rgb4 = read_json(rgb4)
        self.monochrome = read_json(mono)
        self.thermal = read_json(therm)
        self.swir = read_json(swir)
        self.uav_data = read_json(uav)
        self.sensor_data = [self.rgb1, self.rgb4, self.monochrome, self.thermal, self.swir]

    def _initialize_variables(self, train_current, train_prev, verbose, show_map, output_file):
        """Initializes other class variables with default values."""
        self.output_file = output_file
        self.distance_threshold = 20
        self.angle_threshold = 20
        self.train_current = tuple(map(float, train_current.split(',')))  # the current position of the train
        self.train_prev = tuple(
            map(float, train_prev.split(',')))  # (53.086040, 8.781514)  # previous position of the train

        self.uav_detections = []
        self.all_detections = []
        self.final_results = []

        self.test_estimations = []
        self.visualize_estimated_coordinates = []  # list to hold all estimated coordinates to be visualized on map
        self.verbose = verbose
        self.show_map = show_map

    def _initialize_weights(self):
        self.weights = {"RGB1": [100, 100, 100, 80, 60, 40, 20],
                        "RGB4": [80, 100, 100, 100, 80, 60, 40],
                        "Monochrome": [60, 80, 100, 100, 100, 80, 60],
                        "Thermal": [40, 60, 80, 100, 100, 100, 80],
                        "SWIR": [10, 20, 40, 60, 80, 100, 100],
                        "UAV": [100, 100, 100, 100, 100, 100, 100]
                        }

    def _initialize_zones(self):
        """Initializes the zones and merged_zones dictionaries."""
        self.zones = {i: [] for i in range(1, 8)}
        self.merged_zones = {i: [] for i in range(1, 8)}
        self.zone_mapping = {
            (0, 50): 1,
            (50, 100): 2,
            (100, 150): 3,
            (150, 200): 4,
            (200, 250): 5,
            (250, 400): 6,
            (400, float("inf")): 7,
        }

    def _initialize_map(self):
        """Initializes the map to visualize final results."""
        self.map = folium.Map(location=[53.086, 8.782], zoom_start=12)

    def run(self):
        # estimate the GPS coordinates of detected obstacles
        self.estimate_detection_coordinates()
        # make calculations and change uav detection data to match train's onboard sensor data
        self.prepare_uav_detections()
        # group all detections into zones based on expert ranges
        self.group_detections_into_zones()
        # run the merging algorithm to merge similar detections
        self.run_onboard_merging_algorithm()
        # write the final detection list into a json file.
        with open(self.output_file, 'w') as f:
            json.dump(self.final_results, f)
        if self.verbose:
            print("Merging algorithm complete. Final list of detections:")
            for det in self.final_results:
                print(" ", det)
        # visualize estimated positions and original positions on a map
        if self.show_map:
            self.draw_on_map()

    def group_detections_into_zones(self):
        """
        Group detections into zones

        This function groups the detections in all_detections list into specific zones based on the distance of the
        detection. It iterates through each detection and retrieves the distance of the detection. For each range of
        distance in the self.zone_mapping dictionary, it checks if the detection distance falls within that range and
        if so, it appends the detection to the corresponding zone in the self.zones dictionary.

        Args:
        None

        Returns:
        None
        """
        for detection in self.all_detections:
            distance = float(detection["distance"])
            for (low, high), zone in self.zone_mapping.items():
                if low <= distance < high:
                    self.zones[zone].append(detection)
                    break

    def run_onboard_merging_algorithm(self):
        """
        Run onboard merging algorithm.

        This function runs the onboard merging algorithm to merge similar detections in each zone. It iterates through
        each zone in self.zones and calls the find_similar_detections method on each zone, passing the zone and zone_id
        as arguments. The find_similar_detections method is used to identify and merge similar detections in the zone.
        It then iterates through each detection in the zone, and append the detection to the final detection list. The
        final detection list is a dictionary containing the object class and estimated coordinates of the detection.
        The final detections of each zone is added to the self.merged_zones dictionary
        It then flattens the self.final_results and returns it

        Args:
        None

        Returns:
        List : List of merged detections.
        """
        for zone_id, zone_detections in self.zones.items():
            # print information about detections in the zone if self.verbose is set to true.
            if self.verbose:
                print(f"All detections in zone {zone_id}:")
                for det in zone_detections:
                    print(f" {det['camera']} {det['objectclass']}, estimated GPS coordinate: "
                          f"{det['estimated_coordinates']}, distance: {det['distance']}m, relative bearing: "
                          f"{det['relative_bearing']}")
                print(f"Finding similar detections for zone {zone_id}...")
            # for each zone, find similar detections and merge if duplicates are present:
            self.find_similar_detections(zone_detections, zone_id)
            # add detections that are not potential duplicates into the final detections:
            for det in zone_detections:
                final_detection = {det["objectclass"]: det["estimated_coordinates"]}
                self.merged_zones[zone_id].append(final_detection)
            # add final zone data to the self.final_results list
            for det in self.merged_zones[zone_id]:
                self.final_results.append(det)

            if self.verbose:
                print(f"All detections in zone {zone_id} after merge: ", self.merged_zones[zone_id])
                print(f"Zone {zone_id} merged successfully.\n")

    def find_similar_detections(self, zone_detections, zone_id):
        """
        Find similar detections

        This function finds similar detections within a zone. It takes in a zone and a zone_id as arguments.
        It uses the itertools library to iterate through all possible combinations of detections in the zone, and
        compares detections from different sensors. It then checks if the detections have the same object class, and
        if so, it calculates the distance and angle between the detections. If the distance and angle between the
        detections fall within the defined distance and angle thresholds, the detections are considered similar and
        added to the similar_detections dictionary. If similar detections are found, it calls the
        merge_similar_detections method and passing the similar_detections and zone_id as arguments.

        Args:
        zone_detections (list): A list of detections in a specific zone
        zone_id (str): The id of the zone

        Returns:
        None
        """
        similar_detections = {}
        for a, b in itertools.combinations(zone_detections, 2):
            # compare detections from different sensors
            if not a['camera'] == b["camera"]:
                # identify detections with the same class
                if a["objectclass"] == b["objectclass"]:
                    # find the distance and angle between the detections of same class
                    gap = geographic_estimations.calculate_distance(a["estimated_coordinates"],
                                                                    b["estimated_coordinates"])
                    angle_dif = abs(a["relative_bearing"] - b["relative_bearing"])
                    if gap < self.distance_threshold:
                        # detection_groups = {}
                        if angle_dif < self.angle_threshold:
                            # if not detection_groups:
                            #     detection_groups["group_1"]: []
                            objectclass = a["objectclass"]
                            if objectclass not in similar_detections.keys():
                                similar_detections[objectclass] = []
                            if a not in similar_detections[objectclass]:
                                similar_detections[objectclass].append(a)
                                zone_detections.remove(a)
                            if b not in similar_detections[objectclass]:
                                similar_detections[objectclass].append(b)
                                zone_detections.remove(b)

        if similar_detections:
            # print information about similar detections if self.verbose is set to true
            if self.verbose:
                print(f"Found similar detections in zone {zone_id}. List of similar detections:")
                for objectclass, dets in similar_detections.items():
                    print(" objectclass: ", objectclass)
                    for det in dets:
                        print(f"  {det['camera']} {det['objectclass']}, estimated GPS coordinate: "
                              f"{det['estimated_coordinates']}, distance: {det['distance']}m, relative bearing: "
                              f"{det['relative_bearing']}")
                print("Attempting to merge...")
            # merge similar detections with weights
            self.merge_similar_detections(similar_detections, zone_id)
        else:
            if self.verbose:
                print(f"no similar detections to be merged found for zone {zone_id}")

    def merge_similar_detections(self, similar_detections, zone_id):
        """
        Merge similar detections

        This function takes in similar_detections and zone_id as arguments. It groups the detections based on the angle
        range using the group_similar_detections_by_angle method. For each group of detections, it iterates through each
        detection and accumulates the latitude and longitude using a weighted average. The weight is determined by the
        camera source of the detection, and the zone it was detected in.
        It then creates a final detection dictionary containing the object class and the final estimated coordinates,
        and adds it to the self.merged_zones dictionary.

        Args:
        similar_detections (dict): A dictionary containing similar detections.
        zone_id (str): The id of the zone in which the detections were found.

        Returns:
        None
        """
        grouped_dict = self.group_similar_detections_by_angle(similar_detections)
        if self.verbose:
            print(f"Grouped similar detections by angle: ")
            for angle_range, dets in grouped_dict.items():
                print("angle range: ", angle_range)
                for det in dets:
                    print(" ", det["camera"], det["objectclass"], det["distance"], "m", det["estimated_coordinates"],
                          "relative bearing:",
                          det["relative_bearing"])
        for angle_range, detections in grouped_dict.items():
            accumulated_weight = 0
            latitude = 0
            longitude = 0
            objectclass = None
            if self.verbose:
                print(f"Merging group of similar detections in Zone {zone_id} in the angle range:", angle_range)
            for det in detections:
                objectclass = det["objectclass"]
                weight = self.weights[det["camera"]][zone_id - 1]
                latitude = latitude + det["estimated_coordinates"][0] * weight
                longitude = longitude + det["estimated_coordinates"][1] * weight
                accumulated_weight += weight
                if self.verbose:
                    print("    -> merged", det["camera"], det["objectclass"], det["estimated_coordinates"],
                          f"with accumulated weight:{accumulated_weight}")
            final_estimation = (latitude / accumulated_weight, longitude / accumulated_weight)
            final_detection = {objectclass: final_estimation}
            self.merged_zones[zone_id].append(final_detection)
            if self.verbose:
                print(f"Similar group of {objectclass}s merged successfully. Final merged result: {final_detection}")
        if self.verbose:
            print(f"Found and merged all similar detections for zone {zone_id}.")

    def group_similar_detections_by_angle(self, similar_detections_dict):
        """
        Group similar detections by angle

        This function takes in similar_detections_dict as an argument, which is a dictionary containing similar
        detections. It groups the detections based on the angle range using a defaultdict(list) and a for loop.
        It finds the minimum and maximum angles among the detections, and calculates the number of ranges needed based
        on the angle threshold. It then iterates over the list of detections, and groups them into the dictionary based
        on the angle range they fall into.

        Args:
        similar_detections_dict (dict): A dictionary containing similar detections.

        Returns:
        grouped_dict (dict): A dictionary containing the detections grouped by angle range.
        """
        grouped_dict = defaultdict(list)
        for objectclass, detections in similar_detections_dict.items():
            # Find the minimum and maximum angles
            min_bearing = min(d['relative_bearing'] for d in detections)
            max_bearing = max(d['relative_bearing'] for d in detections)
            # Define the range size
            range_size = self.angle_threshold
            # Calculate the number of ranges
            num_ranges = ceil((max_bearing - min_bearing) / range_size)
            # Create a dictionary with default values as lists

            # Iterate over the list of dictionaries and group them based on the angle range
            for d in detections:
                for i in range(num_ranges):
                    range_start = min_bearing + i * range_size
                    range_end = range_start + range_size
                    if range_start <= d['relative_bearing'] < range_end:
                        grouped_dict[(range_start, range_end)].append(d)
        return grouped_dict

    def estimate_detection_coordinates(self):
        """
        Estimate GPS coordinates for detections from all sensors and append to self.all_detections list.

        This function uses the sensor's detected objects and their data to calculate estimated GPS coordinates and
        bearing if entering the region of interest (ROI). The function calls calculate_coordinates_from_image_data which
        takes in the detection, image size, and train's current and previous coordinates, to calculate the coordinates
        of the object. The calculated coordinates and bearing are then added to the detection dictionary and appended to
        the self.all_detections list.
        Args:
        None
        Returns:
        None
        """
        for sensor in self.sensor_data:
            camera = sensor["camera"]
            for detection in sensor["objects"]:
                if detection["entering_ROI"]:
                    coordinates = geographic_estimations.calculate_coordinates_from_image_data(detection,
                                                                                               sensor["imagesize"],
                                                                                               self.train_current,
                                                                                               self.train_prev)
                    self.test_estimations.append({detection['objectclass']: coordinates})
                    bearing = geographic_estimations.calculate_compass_bearing(self.train_current, coordinates)
                    detection["estimated_coordinates"] = coordinates
                    detection["relative_bearing"] = bearing if bearing < 180 else bearing - 360
                    detection["camera"] = camera
                    self.all_detections.append(detection)

    def prepare_uav_detections(self):
        """
        Prepare UAV detections

        This function prepares UAV detections by iterating through the objects in uav_data. It checks if the detection
        is entering the region of interest, and if so, it calculates the coordinates and relative bearing of the object
        using GPS data. It also calculates the distance between the object and the train's current coordinates. The
        detection dictionary is then modified to include these calculated values and the camera source is set to "UAV".
        The detection is then appended to the uav_detections and all_detections lists and the uav_data is appended to
        the sensor_data list.
        Args:
        None
        Returns:
        None
        """
        for detection in self.uav_data["objects"]:
            if detection["entering_ROI"]:
                coordinates = (float(detection["GPS_object"]["latitude"]), float(detection["GPS_object"]["longitude"]))
                bearing = geographic_estimations.calculate_compass_bearing(self.train_current, coordinates)
                detection["relative_bearing"] = bearing if bearing < 180 else bearing - 360
                detection["distance"] = geographic_estimations.calculate_distance(self.train_current, coordinates)
                detection["estimated_coordinates"] = coordinates
                detection["camera"] = "UAV"
                detection.pop("GPS_object")
                self.uav_detections.append(detection)
                self.all_detections.append(detection)
        self.sensor_data.append(self.uav_data)

    def plot_results(self, label, coordinates, color):
        """
        Plot the detection results on a map using the Folium library.

        :param label: the object class of the detection.
        :type label: str
        :param coordinates: the coordinates of the detection.
        :type coordinates: tuple
        :param color: the color of the marker on the map.
        :type color: str
        """
        folium.Marker(location=coordinates, icon=folium.Icon(color=color, icon=label, prefix='fa')).add_to(self.map)

    def draw_on_map(self):
        # draw estimated positions of all detections on the map
        for det in self.all_detections:
            self.plot_results(det["objectclass"], det['estimated_coordinates'], icon_colors[det['camera']])
        # draw current and previous positions of the train on the map
        self.plot_results('train', self.train_current, 'darkgreen')
        self.plot_results('train', self.train_prev, 'lightgreen')
        # draw the final merged results on the map with a gear icon in light blue
        for res in self.final_results:
            for k, v in res.items():
                self.plot_results('gear', v, 'black')
        # show the map in the browser
        self.map.show_in_browser()
