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
from preppy.misc import read_json, backup_session


"""
Expecting session file name as the first command 
line argument after the script name of this file
"""

fname = sys.argv[1]

d = read_json(fname)

backup_session("backups", fname)

# TODO: Finish this remediation script.