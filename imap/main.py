# -*- coding: utf-8 -*-
#!/usr/bin/env python

# Copyright 2021 daohu527 <daohu527@gmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import argparse
import sys

import imap.global_var as global_var

from imap.lib.draw import add_editor, show_map
from imap.lib.convertor import Opendrive2Apollo


def convert_map_format(input_path, output_path):
    opendrive2apollo = Opendrive2Apollo(input_path, output_path)
    opendrive2apollo.set_parameters(only_driving=True)
    opendrive2apollo.convert()
    opendrive2apollo.save_map()


def show_open_drive_map(map_file):
    opendrive2apollo = Opendrive2Apollo(map_file)
    opendrive2apollo.set_parameters(only_driving=True)
    opendrive2apollo.convert()


def main(args=sys.argv):
    parser = argparse.ArgumentParser(
        description="Imap is a tool to display hdmap info on a map.",
        prog="main.py")

    parser.add_argument(
        "-m", "--map", action="store", type=str, required=False,
        help="Specify the map file in txt or binary format")
    parser.add_argument(
        "-l", "--lane", action="store", type=str, required=False,
        help="Find lane by lane id")

    parser.add_argument(
        "-f", "--format", action="store", type=str, required=False,
        nargs='?', const="0", help="Convert format")
    parser.add_argument(
        "-i", "--input", action="store", type=str, required=False,
        help="map input path")
    parser.add_argument(
        "-o", "--output", action="store", type=str, required=False,
        help="map output path")
    parser.add_argument(
        "-s", "--sampling", action="store", type=float, required=False,
        default=1.0, help="sampling length")
    parser.add_argument(
        "-d", "--debug", action="store", type=bool, required=False,
        nargs='?', const=True, default=False, help="debug mode")

    args = parser.parse_args(args[1:])

    # 1. Init global var
    global_var._init()
    global_var.set_element_vaule("sampling_length", args.sampling)
    global_var.set_element_vaule("debug_mode", args.debug)

    # 2. show map
    if args.map is not None:
        suffix = args.map.split(".")[1]
        if suffix == "bin" or suffix == "txt":
            add_editor()
            show_map(args.map, args.lane)
        elif suffix == "xodr":
            show_open_drive_map(args.map)
        else:
            pass

    # 3. convert opendrive map to apllo
    if args.format is not None:
        convert_map_format(args.input, args.output)
