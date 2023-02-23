#!/usr/bin/python3

import os
import argparse
import decision_support


def main():
    parser = argparse.ArgumentParser(description='Create a list of obstacle detections and their estimated coordinates')
    parser.add_argument('rgb1_path', help='Path to json file containing rgb1 sensor data')
    parser.add_argument('rgb4_path', help='Path to json file containing rgb4 sensor data')
    parser.add_argument('monochrome_path', help='Path to json file containing monochrome sensor data')
    parser.add_argument('thermal_path', help='Path to json file containing thermal sensor data')
    parser.add_argument('swir_path', help='Path to json file containing swir sensor data')
    parser.add_argument('uav_path', help='Path to json file containing uav sensor data')

    parser.add_argument('train_current', help='Current GPS coordinate latitude of the train as a tuple '
                                              'e.g: "53.0861622, 8.7816742"', type=str)
    parser.add_argument('train_prev', help='Previous GPS coordinates of the train as a tuple'
                                           'e.g "53.086040, 8.781514"', type=str)

    parser.add_argument('--verbose', help='increase output verbosity', default=False)
    parser.add_argument('--show_map', help='plot the estimations and final results on a map', default=False)

    parser.add_argument('--output_file', help='Output file; Default is ${cwd}/dss_results.json', type=str,
                        default=os.path.join(os.path.curdir, "dss_results.json"))
    args = parser.parse_args()

    dss = decision_support.DetectionMerger(args.rgb1_path, args.rgb4_path, args.monochrome_path, args.thermal_path,
                                           args.swir_path, args.uav_path, args.train_current, args.train_prev,
                                           args.verbose, args.show_map, args.output_file)
    dss.run()


if __name__ == '__main__':
    main()
