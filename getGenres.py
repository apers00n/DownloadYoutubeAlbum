import requests
from dotenv import load_dotenv
import os

load_dotenv()

USERNAME = os.getenv("GETGENRE_USERNAME") or ""
PASSWORD = os.getenv("GETGENRE_PASSWORD") or ""


def get_token(username: str, password: str) -> str:
    url = "https://api.getgenre.com/token"
    data = {
        "grant_type": "password",
        "username": username,
        "password": password,
        "remember_me": "true",
        "refresh_token": "",
    }
    headers = {
        "accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    response = requests.post(url, data=data, headers=headers)
    response.raise_for_status()
    return response.json()["access_token"]


def get_album_genres(artist_name: str, album_name: str) -> str:
    token = get_token(USERNAME, PASSWORD)
    url = "https://api.getgenre.com/search"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"artist_name": artist_name,
              "album_name": album_name, "timeout": 30}
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    data = response.json()

    genres = data.get("top_genres") or []
    return (", ".join(genres)).title()


if __name__ == "__main__":
    artist = "Ariana Grande"
    album = "Dangerous Woman"

    genres_str = get_album_genres(artist, album)

    print("Genres:", genres_str)
