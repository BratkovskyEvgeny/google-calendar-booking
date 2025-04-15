import json

from google_auth_oauthlib.flow import InstalledAppFlow
from google_auth_oauthlib.flow import InstalledAppFlow

# Настройки OAuth 2.0
SCOPES = ["https://www.googleapis.com/auth/calendar"]

# Создаем flow из credentials.json
flow = InstalledAppFlow.from_client_secrets_file(
    "credentials.json",  # Убедитесь, что файл credentials.json находится в той же папке
    scopes=SCOPES,
)

# Запускаем локальный сервер для получения токена
creds = flow.run_local_server(port=0)

# Выводим полученные токены
print("\nВаши учетные данные:")
print("===================")
print(f"Refresh Token: {creds.refresh_token}")
print(f"Token URI: {creds.token_uri}")
print(f"Client ID: {creds.client_id}")
print(f"Client Secret: {creds.client_secret}")

# Сохраняем токены в файл
tokens = {
    "refresh_token": creds.refresh_token,
    "token_uri": creds.token_uri,
    "client_id": creds.client_id,
    "client_secret": creds.client_secret,
    "scopes": creds.scopes,
}

# Сохраняем в файл
with open("tokens.json", "w") as f:
    json.dump(tokens, f, indent=2)

print("\nТокены сохранены в файл tokens.json")
print("\nДобавьте этот refresh_token в секреты Streamlit:")
print("===================")
print("google_refresh_token =", f'"{creds.refresh_token}"')
