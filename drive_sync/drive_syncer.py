import sys, os, shutil, filecmp

try:
    from pydrive.drive import GoogleDrive
    from pydrive.auth import GoogleAuth
except ImportError:
    print("Module PyDrive is not installed - install with \"pip3 install pydrive\"")
    sys.exit()

CREDENTIALS_FILE = "/home/piyush/Documents/Files/projects/File-Syncer/drive_sync/credentials.txt"

def sync(sync_file_path, drive_sync_folder_name):
    """ Given a file containing paths to files to sync and a sync folder in Drive to sync into, syncs the files.
    
    @param sync_file_path: str
    @param dbx_sync_folder_path: str
    """
    drive = GoogleDrive(authenticate(CREDENTIALS_FILE))

    # Locate sync folder by ID
    sync_file_id = None
    while sync_file_id is None:
        root = drive.ListFile({"q": "'root' in parents and trashed=false"}).GetList()
        for file in root:
            if file["title"] == drive_sync_folder_name:
                sync_file_id = file["id"]
                break

        if sync_file_id is None: 
            # Create folder if not found
            sync_folder = drive.CreateFile({"title": drive_sync_folder_name, "mimeType": "application/vnd.google-apps.folder"})
            sync_folder.Upload()
            drive_files = {}
        else:
            drive_files = {f["title"]: f for f in drive.ListFile({"q": "'%s' in parents and trashed=false" % sync_file_id}).GetList()}

    temp_dir_name = os.path.join(os.getcwd(), "downloaded_files_temp")
    if os.path.exists(temp_dir_name):
        print("Error: directory \"%s\" exists" % temp_dir_name)
        sys.exit()
    os.makedirs(temp_dir_name)

    try:
        for file_path in files_to_sync(sync_file_path):
            file_name = file_path.split("/")[-1]

            try:
                if file_name in drive_files:
                    local_path = os.path.join(temp_dir_name, file_name)
                    drive_files[file_name].GetContentFile(local_path)

                    if not filecmp.cmp(local_path, file_path):
                        drive_files[file_name].Delete()

                        new_file = drive.CreateFile({"title": file_name, "parents": [{"kind": "drive#fileLink", "id": sync_file_id}]})
                        new_file.SetContentFile(file_path)
                        new_file.Upload()
                else:
                    new_file = drive.CreateFile({"title": file_name, "parents": [{"kind": "drive#fileLink", "id": sync_file_id}]})
                    new_file.SetContentFile(file_path)
                    new_file.Upload()
            except Exception as e:
                print("Drive: Got exception \"%s\" when processing file \"%s\"" % (str(e), file_name))
    finally:
        shutil.rmtree(temp_dir_name)
        
def authenticate(credentials_file):
    gauth = GoogleAuth()
    gauth.LoadCredentialsFile(credentials_file)

    if gauth.credentials is None: # Failed to load from cached credentials
        gauth.LocalWebserverAuth() # Creates local webserver and auto handles authentication
    elif gauth.access_token_expired:
        gauth.Refresh()
    else:
        gauth.Authorize()

    gauth.SaveCredentialsFile(credentials_file)

    return gauth

def files_to_sync(sync_file):
    """ Given a text file containing paths to files to sync, loads the appropriate files.

    @param sync_file: str
    
    @return list(str)
    """
    return [line.strip() for line in open(sync_file, "r")]


