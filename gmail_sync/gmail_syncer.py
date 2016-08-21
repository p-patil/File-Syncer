import httplib2, base64, time, os, shutil, mimetypes, sys
from email.mime import base, text, image, audio, multipart
from apiclient import discovery
from oauth2client import client, file, tools

CREDENTIALS_FILE = "./credentials.txt"
CLIENT_SECRETS_FILE = "/home/piyush/Documents/Files/projects/File-Syncer/gmail_sync/client_secrets.json"

def sync(sync_file_path):
    # Initialize the authenticated service
    credentials = get_credentials(CREDENTIALS_FILE)
    authorized_http = credentials.authorize(httplib2.Http())
    gmail_service = discovery.build("gmail", "v1", http = authorized_http)

    # Create directory for temporarily storing attachments for comparison
    temp_dir_name = os.path.join(os.getcwd(), "downloaded_files_temp")
    if os.path.exists(temp_dir_name):
        print("Error: directory \"%s\" exists" % temp_dir_name)
        sys.exit()
    os.makedirs(temp_dir_name)

    try:
        for file_path in files_to_sync(sync_file_path):
            file_name = file_path.split("/")[-1]
            to_addr = from_addr = "piyush.patil210@gmail.com"
            subject = "%s Backup - %s | %s" % (file_name, str(time.strftime("%H:%M:%S")), time.strftime("%d/%m/%Y"))
            body = "<%s> identifier" % file_name

            try:
                local_path, email = download_corresponding_attachment(gmail_service, body, file_name, temp_dir_name)
                if local_path is not None: # Email with corresponding attachment exists
                    if not file_compare(local_path, file_path):
                        delete_email(gmail_service, email["id"])
                        send_email(gmail_service, to_addr, from_addr, subject, body, file_path, file_name)
                        mark_unread(gmail_service, body)
                else:
                    # Not found
                    send_email(gmail_service, to_addr, from_addr, subject, body, file_path, file_name)
                    mark_unread(gmail_service, subject)
            except Exception as e:
                print("Gmail: Got exception \"%s\" when processing file \"%s\"" % (str(e), file_name))
    finally:
        shutil.rmtree(temp_dir_name)

def download_corresponding_attachment(service, query, file_name, storage_path):
    email = most_recent_email(service, query, file_name)

    if email is None:
        return (None, None)

    for part in email["payload"]["parts"]:
        if part["filename"] == file_name: # Found corresponding attachment
            if part["body"]["size"] == 0: # Empty attachment
                file_data = ""
            else:
                if "data" in part["body"]:
                    attachment = part["body"]["data"]
                elif "attachmentId" in part["body"]:
                    http_request = service.users().messages().attachments().get(userId = "me", messageId = email["id"], id = part["body"]["attachmentId"])
                    attachment_dict = http_request.execute()
                    attachment = attachment_dict["data"]

                try:
                    file_data = base64.urlsafe_b64decode(attachment.encode("UTF-8")).decode("UTF-8")
                except UnicodeDecodeError as e:
                    print("Error occurred during decoding; ignoring invalid bytes and proceeding:\n\t\"%s\"" % str(e))
                    file_data = base64.urlsafe_b64decode(attachment.encode("UTF-8")).decode("UTF-8", errors = "ignore")

            download_path = os.path.join(storage_path, file_name)
            with open(download_path, "w") as f:
                f.write(file_data)

            return (download_path, email)

    return (None, None)

def delete_email(service, email_id):
    service.users().messages().trash(userId = "me", id = email_id).execute()
    
def send_email(service, to_addr, from_addr, subject, message_body, attachment_file_path, attachment_file_name):
    # Build message
    message = multipart.MIMEMultipart()
    message["to"] = to_addr
    message["from"] = from_addr
    message["subject"] = subject
    message.attach(text.MIMEText(message_body))

    # Build attachment
    attachment = text.MIMEText("")
    content_type, encoding = mimetypes.guess_type(attachment_file_path)
    if content_type is None or encoding is not None:
        content_type = "application/octet-stream"
    main_type, sub_type = content_type.split("/", 1)

    if main_type == "text":
        with open(attachment_file_path) as afp:
            attachment = text.MIMEText(afp.read(), _subtype = sub_type)
    elif main_type == "image":
        with open(attachment_file_path) as afp:
            attachment = image.MIMEImage(afp.read(), _subtype = sub_type)
    elif main_type == "audio":
        with open(attachment_file_path) as afp:
            attachment = audio.MIMEAudio(afp.read(), _subtype = sub_type)
    else:
        with open(attachment_file_path) as afp:
            attachment = base.MIMEBase(main_type, sub_type)
            attachment.set_payload(afp.read())

    # Attach
    attachment.add_header("Content-Disposition", "attachment", filename = attachment_file_name)
    message.attach(attachment)

    # Send
    body = {"raw": base64.urlsafe_b64encode(message.as_bytes()).decode()}
    service.users().messages().send(userId = "me", body = body).execute()

def mark_unread(service, query):
    email = most_recent_email(service, query) 
    if email is not None:
        body = {"removeLabelIds": ["UNREAD"]}
        service.users().messages().modify(userId = "me", id = email["id"], body = body).execute()
    else:
        print("No matches for \"%s\"" % query)

def most_recent_email(service, query, file_name = None):
    messages_resource = service.users().messages()
    search_result = messages_resource.list(userId = "me", q = query).execute()

    if "messages" not in search_result:
        return None

    best_email, best_date = None, -float("inf")
    for message in search_result["messages"]:
        email = messages_resource.get(userId = "me", id = message["id"], format = "full").execute()

        for part in email["payload"]["parts"]:
            if int(email["internalDate"]) > best_date and (file_name is None or part["filename"] == file_name):
                best_email, best_date = email, int(email["internalDate"])

    return best_email

def get_credentials(credentials_file):
    storage = file.Storage(credentials_file) # Cache for authentication token
    scope = "https://www.googleapis.com/auth/gmail.modify" # Access to all read/write operations except permanent deletion
    flags = tools.argparser.parse_args(args = [])

    # Get credentials, from cache or by running OAuth flow
    credentials = storage.get()
    if credentials is None or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRETS_FILE, scope = scope)
        flow.user_agent = "Personal-File-Syncer"
        if flags:
            credentials = tools.run_flow(flow, storage, flags) 
        else:
            credentials = tools.run_flow(flow, storage)

    return credentials


def files_to_sync(sync_file):
    return [line.strip() for line in open(sync_file, "r")]

def remove_extension(name):
    if "." in name:
        k = name.rfind(".")
        name = name[: k]
    return name

def file_compare(path1, path2):
    buffer_size = 1024
    buffer1, buffer2 = " ", " "
    with open(path1, "rb") as file1, open(path2, "rb") as file2:
        while len(buffer1) > 0 and len(buffer2) > 0:
            buffer1 = file1.read(buffer_size).decode("UTF-8").replace("\r", "")
            buffer2 = file2.read(buffer_size).decode("UTF-8").replace("\r", "")

            if len(buffer1) == len(buffer2):
                if buffer1 != buffer2:
                    return False
                else:
                    continue
            elif len(buffer2) < len(buffer1):
                buffer1, buffer2 = buffer2, buffer1
                file1, file2 = file2, file1

            if buffer2[: len(buffer1)] != buffer1:
                return False

            i = len(buffer1)
            while i < len(buffer2):
                c = file1.read(1).decode("UTF-8")
                if c == "\r":
                    continue
                elif c != buffer2[i]:
                    return False
                i += 1

    return len(buffer1) == 0 and len(buffer2) == 0

