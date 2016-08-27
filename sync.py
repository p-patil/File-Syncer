import os
import dropbox_sync.dropbox_syncer as dbx
import drive_sync.drive_syncer as drv
import gmail_sync.gmail_syncer as gml

# TODO implement a verbose mode, by printing current print statements in verbose mode and by adding specific verbose mode print statements

sync_file_path = os.path.join(os.getcwd(), "sync_files.txt")

# Dropbox
try:
    dbx.sync(sync_file_path, "sync_files")
except Exception as e:
    print("Exception occurred in sync.py while syncing dropbox: \"{0}\"".format(str(e)))

# Google Drive
try:
    drv.sync(sync_file_path, "sync_files")
except Exception as e:
    print("Exception occurred in sync.py while syncing drive: \"{0}\"".format(str(e)))

# Gmail
try:
    gml.sync(sync_file_path)
except Exception as e:
    print("Exception occurred in sync.py while syncing gmail: \"{0}\"".format(str(e)))

# Facebook
pass

