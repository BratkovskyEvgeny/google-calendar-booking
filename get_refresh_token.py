from google_auth_oauthlib.flow import InstalledAppFlow

# Если у вас есть файл credentials.json, используйте его
SCOPES = ["https://www.googleapis.com/auth/calendar"]

flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
creds = flow.run_local_server(port=0)

print("Access Token:", creds.token)
print("Refresh Token:", creds.refresh_token)
print("Token URI:", creds.token_uri)
print("Client ID:", creds.client_id)
print("Client Secret:", creds.client_secret)
print("Scopes:", creds.scopes)
