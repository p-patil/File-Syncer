import sys, os, shutil, filecmp

try:
    import dropbox
except ImportError:
    print("Error: Dropbox API not installed. Install with \"pip3 install dropbox\".")
    sys.exit()

ACCESS_TOKEN_FILE = "/home/piyush/Documents/Files/projects/File-Syncer/dropbox_sync/access_token.txt"
    
def sync(sync_file_path, dbx_sync_folder_path):
    """ Given a file containing paths to files to sync and a sync folder in Dropbox to sync into, syncs the files.
    
    @param sync_file_path: str
    @param dbx_sync_folder_path: str
    """
    dbx = dropbox.Dropbox(get_access_token())
    dbx_files = {f.name: f.path_display for f in dbx.files_list_folder("/%s/" % dbx_sync_folder_path, recursive = True).entries}

    temp_dir_name = os.path.join(os.getcwd(), "downloaded_files_temp")
    if os.path.exists(temp_dir_name):
        print("Error: directory \"%s\" exists" % temp_dir_name)
        sys.exit()
    os.makedirs(temp_dir_name)

    try:
        for file_path in files_to_sync(sync_file_path):
            f = open(file_path, "rb")
            file_name = file_path.split("/")[-1]

            try:
                if file_name in dbx_files:
                    local_path = os.path.join(temp_dir_name, file_name)
                    dbx.files_download_to_file(local_path, dbx_files[file_name])
                    
                    if not filecmp.cmp(local_path, file_path):
                        dbx.files_delete(dbx_files[file_name])
                        dbx.files_upload(f, dbx_files[file_name])
                else:
                    dbx.files_upload(f, "%s/%s" % (dbx_sync_folder_path, file_name))
            except Exception as e:
                print("Dropbox: Got exception \"%s\" when processing file \"%s\"" % (str(e), file_name))
    finally:
        shutil.rmtree(temp_dir_name)

# Helper functions below

def get_access_token():
    """ Returns the access token to my personal account.

    @return str
    """
    with open(ACCESS_TOKEN_FILE, "r") as f:
        token = f.readline()

    return token.strip()

def files_to_sync(sync_file):
    """ Given a text file containing paths to files to sync, loads the appropriate files.

    @param sync_file: str
    
    @return list(str)
    """
    return [line.strip() for line in open(sync_file, "r")]

