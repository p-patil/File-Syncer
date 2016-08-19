import os
import dropbox_sync.dropbox_syncer as dbx
import drive_sync.drive_syncer as drv

sync_file = os.path.join(os.getcwd(), "sync_files.txt")

# Dropbox
dbx.sync(sync_file, "/sync_files")

# Google Drive
drv.sync(sync_file, "sync_files")

# Gmail
pass

# Facebook
pass

