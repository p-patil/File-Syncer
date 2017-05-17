import sys, os, shutil, filecmp, time
from pydrive.drive import GoogleDrive
from pydrive.auth import GoogleAuth

CREDENTIALS_FILE = "/home/piyush/projects/File-Syncer/drive_sync/credentials.txt"
ERROR_LOG = "/home/piyush/projects/File-Syncer/drive_sync/log.txt"

with open(ERROR_LOG, "a") as f:
    f.write("Executed at %s on %s\n" % (str(time.strftime("%H:%M:%S")), time.strftime("%d/%m/%Y")))

def sync(sync_file_path, drive_sync_folder_name, verbose = False):
    """ Given a file containing paths to files to sync and a sync folder in Drive to sync into, syncs the files.
    
    @param sync_file_path: str
    @param dbx_sync_folder_path: str
    """
    if verbose: print("Reading credentials from file \"%s\"" % CREDENTIALS_FILE)

    drive = GoogleDrive(authenticate(CREDENTIALS_FILE))

    if verbose: print("Reading drive files")

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
        with open("ERROR_LOG", "a") as f:
            f.write("Error: directory \"%s\" exists\n" % temp_dir_name)
        sys.exit()
    os.makedirs(temp_dir_name)

    print("Syncing files")

    try:
        for file_path in files_to_sync(sync_file_path):
            file_name = file_path.split("/")[-1]

            try:
                if file_name in drive_files:
                    local_path = os.path.join(temp_dir_name, file_name)
                    drive_files[file_name].GetContentFile(local_path)

                    if not filecmp.cmp(local_path, file_path):
                        if verbose: print("Uploading file \"%s\"" % file_name)

                        drive_files[file_name].Delete()

                        new_file = drive.CreateFile({"title": file_name, "parents": [{"kind": "drive#fileLink", "id": sync_file_id}]})
                        new_file.SetContentFile(file_path)
                        new_file.Upload()
                    elif verbose: print("Skipping file \"%s\"" % file_name)
                else:
                    if verbose: print("Uploading file \"%s\"" % file_name)

                    new_file = drive.CreateFile({"title": file_name, "parents": [{"kind": "drive#fileLink", "id": sync_file_id}]})
                    new_file.SetContentFile(file_path)
                    new_file.Upload()
            except Exception as e:
                with open("ERROR_LOG", "a") as f:
                    f.write("Drive: Got exception \"%s\" when processing file \"%s\"\n" % (str(e), file_name))
    finally:
        if verbose: print("Cleaning up")

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


