from lyricsgenius import Genius
from dotenv import load_dotenv
import os
import re

load_dotenv()

TOKEN = os.getenv("GENUIS_ACCESS_TOKEN") or ""
genius = Genius(TOKEN)
genius.verbose = False
# genius.excluded_terms = ["(Traducción al Español)"]


def getLyrics(songTitle: str, artist: str):
    cleaned_title = re.sub(
        r"\s*\(feat\..*?\)", "", songTitle, flags=re.IGNORECASE
    ).strip()
    song = genius.search_song(cleaned_title, artist)

    if song:
        features = [
            str(artist["name"])
            for artist in (song.featured_artists or [])
            if isinstance(artist, dict) and "name" in artist
        ]

        # data = {"features": features, "lyrics": song.lyrics}
        artist = ", ".join([song.primary_artist["name"]] + features)
        data2 = {"artist": artist, "lyrics": song.lyrics}
        return data2

    return {"artist": artist, "lyrics": ""}
