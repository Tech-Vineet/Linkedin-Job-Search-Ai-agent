from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow

GMAIL_SEND_SCOPE = "https://www.googleapis.com/auth/gmail.send"


def main():
    credentials_path = Path("gmail_client_secret.json")

    if not credentials_path.exists():
        raise SystemExit(
            "Place your Google OAuth client JSON at gmail_client_secret.json, then run again."
        )

    flow = InstalledAppFlow.from_client_secrets_file(
        str(credentials_path),
        scopes=[GMAIL_SEND_SCOPE],
    )
    credentials = flow.run_local_server(
        port=0,
        access_type="offline",
        prompt="consent",
    )

    print("GMAIL_CLIENT_ID=" + credentials.client_id)
    print("GMAIL_CLIENT_SECRET=" + credentials.client_secret)
    print("GMAIL_REFRESH_TOKEN=" + credentials.refresh_token)


if __name__ == "__main__":
    main()
