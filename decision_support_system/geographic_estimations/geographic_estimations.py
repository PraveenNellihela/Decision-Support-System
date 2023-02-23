import geopy.distance
import math
from math import asin, cos, sin, atan2

categories = ["bicycle", "bus", "car", "dog", "fallen_tree", "horse",
              "motorbike", "person", "rock", "rock_cluster", "truck"]


def calculate_distance(coordinate_1, coordinate_2):
    return geopy.distance.distance(coordinate_1, coordinate_2).m


def calculate_coordinates_from_image_data(detection, im_size, train_cur, train_prev):
    """
    Calculate coordinates from image data.

    This function takes in a detection dictionary, image size, and train's current and previous coordinates. It
    calculates the x and y coordinates of the detection in the image, and then calculates the angle to the object using
    the x and y coordinates. It then calculates the destination coordinates using the current train coordinates,
    distance to the object, and angle to the object.

    Args:
    detection (dict): A dictionary containing object detection information from an image.
    im_size (dict): A dictionary containing the width and height of the image.
    train_cur (tuple): A tuple containing the current coordinates of the train.
    train_prev (tuple): A tuple containing the previous coordinates of the train.

    Returns:
    tuple: A tuple containing the calculated destination coordinates.
    """
    x = ((int(detection["x_min"]) + int(detection["x_max"])) / 2) - (im_size["image_width"] / 2)
    y = im_size["image_height"] - int(detection["y_max"])
    # im_width_center = im_size["image_width"] / 2
    angle = get_angle_to_detected_obj(x, y) + calculate_compass_bearing(train_prev, train_cur)
    return calculate_destination_coordinates(train_cur, float(detection["distance"]), angle)


def calculate_compass_bearing(start_point, end_point):
    """
    Calculates the bearing between start point and endpoint in the direction -> from start point towards end point.
    The formulae used is the following:
        θ = atan2(sin(Δ longitude).cos(latitude 2), cos(latitude 1).sin(latitude 2)
            − sin(latitude 1).cos(latitude2).cos(Δ longitude))
    :Parameters:
      - start_point: gps coordinates (in decimal degrees) for the initial point
      - end_point: gps coordinates (in decimal degrees) for the final point
    :Returns:
      The bearing between the two coordinates in degrees
    :Returns Type:
      float
    """
    start_latitude = math.radians(start_point[0])
    end_latitude = math.radians(end_point[0])

    delta_longitude = math.radians(end_point[1] - start_point[1])

    x = math.sin(delta_longitude) * math.cos(end_latitude)
    y = math.cos(start_latitude) * math.sin(end_latitude) - (math.sin(start_latitude) * math.cos(end_latitude)
                                                             * math.cos(delta_longitude))
    # normalize to get compass bearings between 0°-360°
    normalized_bearing = (math.degrees(math.atan2(x, y)) + 360) % 360

    return normalized_bearing


def calculate_destination_coordinates(starting_point, distance, angle):
    """
    Given gps coordinates of starting point, distance to destination point and heading,
    calculates the gps coordinates of the destination

    :Parameters:
    starting_point : gps coordinates of starting point in degrees
    distance : distance to destination from starting point in km
    angle : direction of heading from starting point towards destination given in degrees

    :Returns:
      The coordinates of destination
    :Returns Type:
        tuple
    """
    earth_radius = 6372795.477598
    start_lat = math.radians(starting_point[0])
    start_long = math.radians(starting_point[1])
    angle = math.radians(angle)
    delta = distance / earth_radius

    des_lat = asin((sin(start_lat) * cos(delta)) + (cos(start_lat) * sin(delta) * cos(angle)))
    des_long = start_long + atan2(sin(angle) * sin(delta) * cos(start_lat), cos(delta) - sin(start_lat) * sin(des_lat))

    return math.degrees(des_lat), math.degrees(des_long)


def calculate_bbox_center(bbox):
    left, bottom, right, top = bbox
    return (left + right) / 2, bottom


def get_angle_to_detected_obj(x, y):
    alpha = math.atan(x / y)
    return math.degrees(alpha)


def prepare_annotations(data):
    annotations = []
    image_data = data['images']
    for annotation in data['annotations']:
        for image in image_data:
            if annotation['image_id'] == image['id']:
                image_height = image['height']
                image_width = image['width']
        ann = {'id': annotation['id'],
               'bbox': annotation['bbox'],
               'image_id': annotation['image_id'],
               'category_id': annotation['category_id'],
               'image_height': image_height,
               'image_width': image_width}
        annotations.append(ann)
    return annotations


# json data modification functions


def append_detection_angles(annotations, train_bearing):
    for annotation in annotations:
        bbox_center = calculate_bbox_center(annotation['bbox'])
        image_center_along_bbox_center = annotation["image_width"] / 2, bbox_center[1]
        image_bottom_center = annotation["image_width"] / 2, annotation["image_height"]

        # calculate angle to detected object
        y = image_bottom_center[1] - image_center_along_bbox_center[1]
        x = bbox_center[0] - image_center_along_bbox_center[0]
        # detection.update({'angle': get_angle_to_detected_obj(x,y)})
        # annotation['angle_as_seen_from_train'] = get_angle_to_detected_obj(x, y)
        annotation['detection_bearing'] = get_angle_to_detected_obj(x, y) + train_bearing
    return annotations


def append_detection_coordinates(annotations, detections, final_train_coordinates):
    for annotation, detection in zip(annotations, detections):
        detection_coordinates = calculate_destination_coordinates(final_train_coordinates, detection["distance"],
                                                                  annotation["detection_bearing"])
        annotation['coordinates'] = detection_coordinates
    return annotations


def format_annotations(annotations):
    keys_to_remove = ("bbox", "image_id", "image_height", "image_width", "detection_bearing", "category_id")
    for annotation in annotations:
        category_id = annotation["category_id"] - 1
        annotation['object_class'] = categories[category_id]
        for key in keys_to_remove:
            annotation.pop(key)
    return annotations

