import yt_dlp
from ytmusicapi import YTMusic
import requests
import os
import questionary
import re
from mutagen.mp3 import MP3
from mutagen.id3._frames import TIT2, TALB, TPE1, TRCK, TCON, APIC
import sys


def safe_filename(name: str) -> str:
    """
    Replace filesystem-unsafe characters in filenames.
    """
    # Replace slashes and other invalid characters
    name = re.sub(r'[\\/:"*?<>|]+', "_", name)
    # Strip leading/trailing spaces and dots
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
):
    set_album_art(file_path, cover_image_path)
    audio = MP3(file_path)

    # ensure tags exist
    if audio.tags is None:
        audio.add_tags()

    unwanted_phrases = [
        r"\s\(Official Video\)",
        r"\s\(Official Audio\)",
        r"\s\[Official Audio\]",
        r"\s\(Audio\)",
        rf"^{re.escape(artist)}\s-\s",
    ]
    for phrase in unwanted_phrases:
        title = re.sub(phrase, "", title)

    # update tags
    audio.tags.add(TIT2(encoding=3, text=title))
    audio.tags.add(TALB(encoding=3, text=album))
    audio.tags.add(TPE1(encoding=3, text=artist))
    audio.tags.add(TRCK(encoding=3, text=f"{track_number}/{total_tracks}"))
    audio.tags.add(TCON(encoding=3, text=genre))
    audio.save()

    # set cover art last


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

    output_dir = os.path.join(os.path.expanduser("~/Downloads"), ALBUM)
    os.makedirs(output_dir, exist_ok=False)

    cover_path = os.path.join(output_dir, "cover.jpg")
    download_image(COVER_URL, cover_path)

    # Download each song
    for i, track in enumerate(album_data["tracks"], start=1):
        title = track["title"]
        video_id = track.get("videoId")
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
            )


def getAlbums(album_query: str):
    yt = YTMusic()
    results = yt.search(album_query, filter="albums")

    if not results:
        return {}

    return results


def download_album(album_data, genre: str = ""):
    ALBUM = album_data["title"]
    ARTIST = album_data["artists"][0]["name"]
    COVER_URL = album_data["thumbnails"][-1]["url"]

    output_dir = os.path.join(os.path.expanduser("~/Downloads"), ALBUM)
    os.makedirs(output_dir, exist_ok=True)

    cover_path = os.path.join(output_dir, "cover.jpg")
    download_image(COVER_URL, cover_path)

    total_tracks = len(album_data["tracks"])
    for i, track in enumerate(album_data["tracks"], start=1):
        title = track["title"]
        video_id = track.get("videoId")
        if not video_id:
            continue

        download_song(video_id, output_dir, i, title)
        file_path = os.path.join(output_dir, f"{i:02d} - {safe_filename(title)}.mp3")
        if os.path.exists(file_path):
            update_metadata(
                file_path,
                title,
                ALBUM,
                i,
                total_tracks,
                ARTIST,
                cover_path,
                genre,
            )

    return ALBUM, ARTIST, total_tracks


if __name__ == "__main__":
    main()
