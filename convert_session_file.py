#! /usr/bin/env python
"""
Convert a session file from Format II to format III

Usage:
$ convert_session_file.py preppy_session.json

~~~~~~~~~~~~~~~~~~~
Format II:

"metadata":
    id_str:
        param_name:
            user_id:
                value
    ...
"tweets":
    id_str:
        Status.AsDict()
    ...

~~~~~~~~~~~~~~~~~~~
Format III:

id_str:
    "status":
        Status.AsDict()
    "metadata":
        MetaData.as_dict
...

Essentially switching the place of the id_str key
and the "metadata"/"status" keys

"""

import sys
from os.path import splitext as split_ext
from preppy.misc import read_json, backup_session, write_json


"""
Expecting session file name as the first command 
line argument after the script name of this file
"""

try:
    fname = sys.argv[1]
except:
    fname = "preppy_session.json"
backup_session("backups", fname)
d = read_json(fname)
metadata = d['metadata']
tweets = d['tweets']

output = {}

k1 = metadata.keys()
k2 = metadata.keys()
keys = set(k1).union(k2)
for id_str in list(keys):
    output[id_str] = dict(
        status=tweets.get(id_str),
        metadata=metadata.get(id_str)
    )

if False:
    basename, ext = split_ext(fname)
    outFileName = basename + "_test" + ext
else:
    outFileName = fname

write_json(output, outFileName)
