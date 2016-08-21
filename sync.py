import os
import dropbox_sync.dropbox_syncer as dbx
import drive_sync.drive_syncer as drv
import gmail_sync.gmail_syncer as gml

# TODO implement a verbose mode, by printing current print statements in verbose mode and by adding specific verbose mode print statements

sync_file_path = os.path.join(os.getcwd(), "sync_files.txt")

# Dropbox
dbx.sync(sync_file_path, "sync_files")

# Google Drive
drv.sync(sync_file_path, "sync_files")

# Gmail
gml.sync(sync_file_path)

# Facebook
pass

