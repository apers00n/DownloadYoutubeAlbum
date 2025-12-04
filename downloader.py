import yt_dlp
from ytmusicapi import YTMusic
import requests
import os
import questionary
import re
from mutagen.mp3 import MP3
from mutagen.id3._frames import APIC
import sys
from getGenres import get_album_genres
from mutagen.easyid3 import EasyID3

DEFAULT_PATH = "~/Downloads"

if "genre" not in EasyID3.valid_keys:
    EasyID3.RegisterTextKey("genre", "TCON")


def safe_filename(name: str) -> str:
    name = re.sub(r'[\\/:"*?<>|]+', "_", name)
    return name.strip().strip(".")


def download_image(url, file_path):
    try:
        response = requests.get(url)
        response.raise_for_status()
        with open(file_path, "wb") as file:
            file.write(response.content)
    except requests.RequestException as e:
        print(f"Failed to download image: {e}")


def set_album_art(audio_file_path, image_file_path):
    audio = MP3(audio_file_path)

    if audio.tags is None:
        audio.add_tags()
        assert audio.tags is not None

    audio.tags.delall("APIC")

    with open(image_file_path, "rb") as img_file:
        audio.tags.add(
            APIC(
                encoding=3,
                mime="image/jpeg",
                type=3,
                desc="Cover",
                data=img_file.read(),
            )
        )

    audio.save()


def update_metadata(
    file_path,
    title,
    album,
    track_number,
    total_tracks,
    artist,
    cover_image_path,
    genre="",
    year="",
):
    audio = MP3(file_path, ID3=EasyID3)

    audio["title"] = title
    audio["tracknumber"] = f"{track_number}/{total_tracks}"
    audio["artist"] = artist
    audio["album"] = album
    audio["genre"] = genre
    audio["date"] = year

    audio.save()
    set_album_art(file_path, cover_image_path)


def download_song(video_id, output_path, index, title):
    title = safe_filename(title)
    url = f"https://music.youtube.com/watch?v={video_id}"
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": os.path.join(output_path, f"{index:02d} - {title}.%(ext)s"),
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
        "quiet": True,
        "progress": True,
        "ignoreerrors": True,
        "no_warnings": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


def main():
    yt = YTMusic()

    album_query = questionary.text("Album name: ").ask()
    if not album_query:
        sys.exit(0)

    results = yt.search(album_query, filter="albums")

    if not results:
        print("No albums found on YouTube Music.")
        return

    album = results[0]
    album_id = album["browseId"]
    album_data = yt.get_album(album_id)

    ALBUM = album_data["title"]
    ARTIST = album_data["artists"][0]["name"]
    COVER_URL = album_data["thumbnails"][-1]["url"]
    YEAR = album_data["year"]
    GENRES = get_album_genres(ARTIST, ALBUM)

    output_dir = os.path.join(os.path.expanduser(DEFAULT_PATH), ALBUM)
    os.makedirs(output_dir, exist_ok=False)

    cover_path = os.path.join(output_dir, "cover.jpg")
    download_image(COVER_URL, cover_path)

    for i, track in enumerate(album_data["tracks"], start=1):
        title = track["title"]
        video_id = track["videoId"]

        if track["videoType"] == "MUSIC_VIDEO_TYPE_OMV":
            newId = get_video_id(ALBUM, title)
            if newId is not None:
                video_id = newId

        if not video_id:
            print(f"Skipping {title} (no video ID)")
            continue

        print(f" {i:02d}/{len(album_data['tracks'])}: {title}")
        download_song(video_id, output_dir, i, title)

        file_path = os.path.join(output_dir, f"{i:02d} - {title}.mp3")
        if os.path.exists(file_path):
            update_metadata(
                file_path,
                title,
                ALBUM,
                i,
                len(album_data["tracks"]),
                ARTIST,
                cover_path,
                GENRES,
                YEAR,
            )


def get_video_id(album_title, song_title):
    yt = YTMusic()
    songs_list = yt.search(song_title, filter="songs")
    for song in songs_list:
        if (
            song.get("title", "").lower() == song_title.lower()
            and song.get("album", {}).get("name", "").lower() == album_title.lower()
        ):
            return song.get("videoId")
    return None


def getAlbums(album_query: str):
    yt = YTMusic()
    results = yt.search(album_query, filter="albums")

    if not results:
        return {}

    return results


if __name__ == "__main__":
    main()
