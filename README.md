# brickstor-health-data
This repository contains examples of health-related data made available by the BrickStor and transformations of this data enabling it to be used for monitoring by customers.

While examples may be written in Python because it is a good language for providing easy-to-read examples, it does not mean that it cannot be done in some other language. I do not expect that these examples can be used verbatim, but it should be fairly easy to go from an example to a useful utility.

## Requirements
- Python >= 3.10 (not tested with earlier version)
- Linux, MacOS, Windows (some unix-y things may not work on Windows)

## Assumptions
It is assumed that the data made available by the BrickStor is in some way periodically collected from the system, or the system periodically copies the data to one of its shared out filesystems enabling collection of this data from the share by external agents/probes. Much of the environmental and system health data is made available from one place, the health service. It is possible to get a "raw" dump of this data from the service periodically with the following command: `healthadm -j ls e --all`. This will generate a potentially very large JSON array filled with objects, each of which is known as an _element_. There are many types of elements, but fundamentally there are standards which all data follows. Some elements may have no useful value and exist only to provide a status. Some elements will have a useful value, such as a temperature, normally expressed in degrees C. Elements also have a notion _Status_ and _Severity_. These indicate whether or not the element is healthy and if not healthy then the level of unhealthy.

We tossed example output from `healthadm` into the data directory to make it easy to play with the scripts without ever touching the BrickStor.

> ### NOTE
> Most data analysis, conversation, manipulation, etc. should be done on some external system responsible for gathering and exporting metric data. The BrickStor is an appliance and limited in terms of tools and resources.

## Example programs
### drive_temps_to_csv.py
For the purposes of health monitoring, keeping an eye on temperatures is frequently considered to be foundational. There are a lot of temperature sensors inside of our system, in particular storage enclosures filled with drives. Each drive has a temperature sensor and this information is already collected and accessible from the BrickStor.

This script pulls out _Drive_ temperature elements out of the "raw" JSON data and converts them into line-oriented CSVf-formatted data. I find that people are more familiar with working on line-oriented data than serialized objects. Once transformed to to CSV the data could be fairly easily inserted into some data and pushed to a monitoring system.

**CSV format in this example is as follows:**
1. ISO8601 date with nanosecond precision in UTC timezone
2. Appliance serial number
3. Component type (Drive)
4. Drive serial number
5. Status
6. Severity
7. Units 
8. Temperature value

Reasonable header line for this data could be:
```
timestamp,system_serial,component_type,drive_serial,status,severity,units,value
```
#### Example output
Run the script with supplied input and the `--debug` flag to see resulting CSV lines.
```
$ python3 ./drive_temps_to_csv.py --filename data/healthadm.json --debug
2023-04-19T15:42:00.802186761Z,ZZ0001C8,Drive,HLK031P10000822150Z3,Normal,Normal,Celsius,26
2023-04-19T15:41:58.496598265Z,ZZ0001C8,Drive,ZA2678XP0000C833C96W,Normal,Normal,Celsius,23
--- snip ---
```