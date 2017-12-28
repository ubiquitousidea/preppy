import shutil
from preppy.misc import get_latest_file


latest_backup_path = get_latest_file("backups")

shutil.copyfile(latest_backup_path, "./preppy_session.json")
