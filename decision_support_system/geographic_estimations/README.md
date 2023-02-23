# Geographic Estimations

This package contains a set of functions that are used to calculate various values related to GPS coordinates. The main functions are:

- `calculate_distance(coordinate_1, coordinate_2)`: This function calculates the distance between two GPS coordinates using the `geopy` library.
- `calculate_coordinates_from_image_data(detection, im_size, train_cur, train_prev)`: Given a set of image data (`detection`), the size of the image and the current and previous GPS coordinates of a train, this function calculates the GPS coordinates of an object detected in the image.
- `calculate_compass_bearing(start_point, end_point)`: This function calculates the bearing between two GPS coordinates in the direction from start point towards end point.
- `calculate_destination_coordinates(starting_point, distance, angle)`: Given the GPS coordinates of a starting point, a distance and an angle, this function calculates the GPS coordinates of the destination point.
- `calculate_bbox_center(bbox)`: Given the bounding box coordinates of an object, this function returns the center coordinates of the bounding box.
- `get_angle_to_detected_obj(x, y)`: Given the `x` and `y` coordinates of a detected object in an image, this function returns the angle of the object relative to the center of the image.

## Usage

To use these functions in your project, you can simply import the package and call the desired function. For example:
    from gps_calculations import calculate_distance
    
    coordinate_1 = (51.509865, -0.118092)
    coordinate_2 = (52.205338, 0.119543)
    
    distance = calculate_distance(coordinate_1, coordinate_2)
    print(distance)

Note: The library `geopy` is required to be installed to run the above code.

The package is compatible with Python 3.x

## Additional Notes

- It is important to note that the input coordinates should be in decimal degrees format.
- The distance returned by `calculate_distance` is in meters.
- The `calculate_coordinates_from_image_data` function assumes that the image data is in the format of a dictionary with keys `x_min`, `x_max`, `y_min`, `y_max` and `distance` and the `im_size` is in the format of a dictionary with keys `image_width` and `image_height`.
- The `calculate_compass_bearing` function returns the bearing in degrees.
- The `calculate_destination_coordinates` function assumes that the distance input is in kilometers and the angle input is in degrees.
- The `calculate_bbox_center` function assumes that the input `bbox` is in the format of a tuple `(left, bottom, right, top)`.
- The `get_angle_to_detected_obj` function assumes that `x` and `y` are the coordinates of the object relative to the center of the image.
