import zipfile
from preppy.misc import date_string


fname_in = "preppy_session.json"
fname_out = "preppy_session_{}.zip".format(date_string())

with zipfile.ZipFile(
        fname_out, "w",
        zipfile.ZIP_DEFLATED) as zf:
    zf.write(fname_in)
