import zipfile


fname_in = "preppy_session.json"
fname_out = "preppy_session.zip"

with zipfile.ZipFile(
        fname_out, "w",
        zipfile.ZIP_DEFLATED) as zf:
    zf.write(fname_in)
