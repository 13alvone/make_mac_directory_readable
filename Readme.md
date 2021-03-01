# Make Mac Directory Readable
This quick tool parses through a given Mac Filesystem Directory, creating human-readable copies of each file found in a directory. Specifically, this was made to parse through and convert SQLite3, Plist, XML, and generic Binary data that is stored within a target directory.

## Usage
`python3 make_mac_directory_readable.py -d <target_directory>`

## Output
Human-Readable Files are output to the following location:

```/tmp/<date><directory>/files...```
