#!/usr/bin/env python3

# The MIT License (MIT)
# Copyright © 2023 Sam Zaydel

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the “Software”), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, # OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import argparse
import json
import sys

from typing import Any, AnyStr, Dict, Generator, List


def filter(elements: List[Dict]) -> Generator[Dict[AnyStr, Any], None, None]:
    """
    Filters a list of dictionaries based on existence of a substring in the HRI.

    Args:
        elements (List[Dict]): Elements from the raw health dump.

    Yields:
        Generator[Dict[AnyStr, Any], None, None]: Elements whose HRI matches a particular substring.
    """
    for elem in (d for d in elements if d.get("HRI", "").endswith("/temperature")):
        yield elem


def line_from_dict(element: Dict[AnyStr, Any]) -> str | None:
    """
    Given a single drive element as a dictionary transform this input into a
    single CSV-formatted line with the following columns in this order order:

    (1) ISO8601 date with nanosecond precision in UTC timezone
    (2) Appliance serial number
    (3) Component type - always Drive
    (4) Drive serial number
    (5) Status - Normal if all is well, could be others
    (6) Severity -
    (7) Units - should be Celsius
    (8) Temperature value

    Args:
        element (Dict[AnyStr, Any]): A drive element from raw health dump.

    Returns:
        str | None: CSV-formatted string or None if certain conditions are not met.
    """
    # The date may not be uniform for all drives. We do not collect data from
    # all drives at the same time, thus it is possible to have observations
    # which are some number of seconds apart. If this is unacceptable for any
    # reason, just change this function a bit and pass a timestamp string as an
    # argument to this function.
    date: str = element.get("Date")  # When this data was collected; GMT
    hri: str = element.get("HRI")
    value: int = element.get("Value")  # temperature
    component_name: str = element.get("ComponentName")  # make + serial
    component_type: str = element.get("ComponentType")  # Always Drive
    severity: str = element.get("Severity")
    status: str = element.get("Status")  # Normal if everything appears to be OK
    units: str = element.get("Units")
    # Some of these checks are invariants. If these conditions are not
    # satisfied we won't be able to form a line.
    if not all(
        [hri, component_name, component_type, date, severity, status, units, value]
    ):
        return None

    # Break-up the HRI into tokens some of which we use later.
    hri_tokens: List[AnyStr] = hri[1:].split("/")
    if len(hri_tokens) < 5:
        return None

    comp_name_tokens: List[AnyStr] = component_name.split()
    wwn: str = hri_tokens[2]
    if wwn.startswith("naa."):  # Drop the `naa.` prefix here
        wwn = wwn[4:]
    drive_serial: str = (
        "unknown" if not len(comp_name_tokens) > 1 else comp_name_tokens[1]
    )
    system_serial = hri_tokens[1]
    return f"{date},{system_serial},{component_type},{drive_serial},{status},{severity},{units},{value}"


def elements_to_lines(
    elements: List[Dict], filter_func=filter, line_func=line_from_dict
) -> Generator[str | None, None, None]:
    """
    Filters a list of elements from raw health data dropping all but the drive
    elements and transforms the reduced list from dicts to CSV-formatted strings.

    Args:
        elements (List[Dict]): List of elements deserialized from raw health data.
        filter_func (function(List[Dict[AnyStr,Any]]) -> List[Dict[AnyStr,Any]], optional): Filter selecting only relevant elements. Defaults to filter.
        line_func (function(Dict[AnyStr, Any]) -> str | None, optional): Transformer function converts dicts into CSV strings. Defaults to line_from_dict.

    Yields:
        str | None: CSV-formatted line or None if something went wrong with transformation.
    """
    for elem in filter_func(elements):
        yield line_func(elem)


def setup_parser() -> argparse.ArgumentParser:
    """
    Sets up an argument parser for this program.

    Returns:
        argparse.ArgumentParser: Configured argument parser.
    """
    parser = argparse.ArgumentParser(
        description="Extracts drive temperature values from health data returned by the RackTop storage system"
    )
    parser.add_argument(
        "--filename",
        help="Path to file containing raw JSON data gathered from the BrickStor appliance",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable output of transformed data to stdout",
    )

    return parser


if __name__ == "__main__":
    parser = setup_parser()
    parsed_args = parser.parse_args(sys.argv[1:])
    debug = parsed_args.debug
    if not parsed_args.filename:
        print("Please specify filename containing raw JSON data", file=sys.stderr)
        sys.exit(1)
    filename = parsed_args.filename
    elements = None

    try:
        with open(filename, "rb") as input:
            try:
                elements = json.load(input)
            except json.JSONDecodeError as err:
                print(f"Failed decoding JSON from input {err}", file=sys.stderr)
                sys.exit(1)
    except IOError as err:
        print(f"Unable to open the input file {err}", file=sys.stderr)
        sys.exit(1)

    # When debug is set, we just print this out. The `else` clause is not
    # implemented, but this is where we would do something with this data.
    if debug:
        for line in elements_to_lines(elements):
            if line:
                print(line)
    else:
        pass
