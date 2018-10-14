from gmail_syncer import *
import sys

if __name__ == "__main__":
    # Create a service object through which to communicate with Gmail.
    credentials = get_credentials(CREDENTIALS_FILE)
    authorized_http = credentials.authorize(httplib2.Http())
    gmail_service = discovery.build("gmail", "v1", http = authorized_http)

    # Search for email.
    query = "from:amit.satoor@sap.com OR to:amit.satoor@sap.com"
    messages_resource = gmail_service.users().messages()
    search_result = messages_resource.list(userId="me", q=query).execute()

    if "messages" not in search_result: # Search failed
        print("No emails matching query \"{0}\" found".format(query))
        sys.exit(1)

    for message in search_result["messages"]:
        email = messages_resource.get(userId="me", id=message["id"], format="full").execute()

