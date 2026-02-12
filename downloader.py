import yt_dlp
from ytmusicapi import YTMusic
import requests
import os
import questionary
import re
from mutagen.mp3 import MP3
from mutagen.id3._frames import APIC
import sys
from discs import get_disc_info
from getGenres import get_album_genres
from mutagen.easyid3 import EasyID3
from send2trash import send2trash
from mutagen.mp4 import MP4, MP4Cover
from datetime import datetime
from lyrics import getLyrics
from questionary import Choice

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


def update_metadata(
    file_path,
    title,
    album,
    track_number,
    total_tracks,
    disc,
    total_discs,
    album_artist,
    artists,
    cover_image_path,
    genre="",
    year="",
    explicit=0,
    lyrics="",
    video_id="",
):
    audio = MP4(file_path)

    audio["\xa9nam"] = title
    audio["\xa9alb"] = album
    audio["aART"] = album_artist
    audio["\xa9ART"] = artists
    audio["trkn"] = [(track_number, total_tracks)]
    audio["disk"] = [(disc, total_discs)]
    audio["\xa9gen"] = genre
    audio["\xa9day"] = year
    audio["rtng"] = [explicit]
    audio["\xa9lyr"] = lyrics
    audio["----:com.apple.iTunes:DOWNLOADED_DATE"] = [
        datetime.now().isoformat().encode("utf-8")
    ]
    if video_id != "":
        audio["----:com.apple.iTunes:YT_URL"] = [video_id.encode("utf-8")]

    if cover_image_path:
        with open(cover_image_path, "rb") as img:
            audio["covr"] = [MP4Cover(img.read(), imageformat=MP4Cover.FORMAT_PNG)]

    audio.save()


def download_song(video_id, output_path, index, title):
    # title = safe_filename(title)
    url = f"https://youtube.com/watch?v={video_id}"
    ydl_opts = {
        "format": (
            "bestaudio[ext=m4a][protocol=https]/bestaudio[ext=webm]/bestaudio/best"
        ),
        "noplaylist": True,
        "force_ipv4": True,
        # "cookiesfrombrowser": ("vivaldi", "Default"),
        "outtmpl": os.path.join(output_path, f"{index:02d} - {title}.%(ext)s"),
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "m4a",
                "preferredquality": "256",
            }
        ],
        "quiet": True,
        "progress": True,
        "ignoreerrors": True,
        "no_warnings": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:  # type: ignore[reportArgumentType]
        ydl.download([url])


def get_best_album_version_playlist_id(album_browse_id: str):
    """
    Finds the album version with the most tracks.
    If tied, prefers the explicit version.
    Returns the album browseId (playlist ID).
    """
    yt = YTMusic()

    # Default album
    default_album_id = album_browse_id  # results[0]["browseId"]
    default_album = yt.get_album(default_album_id)

    albums_to_compare = [default_album]

    # 2) Collect other versions
    for version in default_album.get("other_versions", []):
        try:
            albums_to_compare.append(yt.get_album(version["browseId"]))
        except Exception:
            pass  # skip broken versions safely

    # 3) Choose best version
    def score(album):
        track_count = len(album.get("tracks", []))
        is_explicit = album.get("isExplicit", False)
        return (track_count, is_explicit)

    best_album = max(albums_to_compare, key=score)

    return best_album


def main():
    yt = YTMusic()

    album_query = questionary.text("Album name: ").ask()
    if not album_query:
        sys.exit(0)

    results = yt.search(album_query, filter="albums")

    if not results:
        print("No albums found on YouTube Music.")
        return

    album_browse_id = questionary.select(
        "Which version:",
        choices=[
            Choice(title=album["title"], value=album["browseId"])
            for album in results[:4]
        ],
    ).ask()

    # first_album = results[0]
    album_data = get_best_album_version_playlist_id(album_browse_id)

    ALBUM = album_data["title"]
    ARTIST = album_data["artists"][0]["name"]
    COVER_URL = album_data["thumbnails"][-1]["url"]
    YEAR = album_data["year"]
    GENRES = get_album_genres(ARTIST, ALBUM)

    output_dir = os.path.join(os.path.expanduser(DEFAULT_PATH), ALBUM)
    os.makedirs(output_dir, exist_ok=False)

    cover_path = os.path.join(output_dir, "cover.jpg")
    download_image(COVER_URL, cover_path)

    disc_track_counts = get_disc_info(ARTIST, ALBUM, len(album_data["tracks"]))

    current_disc = 1
    track_within_disc = 1  # per-disc numbering
    cumulative_track = 1  # overall numbering

    for i, track in enumerate(album_data["tracks"], start=1):
        if cumulative_track > sum(disc_track_counts[:current_disc]):
            current_disc += 1
            track_within_disc = 1

        title = track["title"]
        original_title = re.sub(
            r"\s*\(feat\..*?\)", "", title, flags=re.IGNORECASE
        ).strip()
        title = safe_filename(title)
        video_id = track["videoId"]
        explicit = 1 if track["isExplicit"] else 0

        if track["videoType"] == "MUSIC_VIDEO_TYPE_OMV":
            newId = get_video_id(ALBUM, title)
            if newId is not None:
                video_id = newId

        if not video_id:
            print(f"Skipping {title} (no video ID)")
            cumulative_track += 1
            continue

        genius_data = getLyrics(original_title, ARTIST)

        print(
            f"Disc {current_disc} Track {track_within_disc}/{
                disc_track_counts[current_disc - 1]
            } "
            f"({cumulative_track}/{len(album_data['tracks'])}): {title} - {video_id}"
        )
        # print(f" {i:02d}/{len(album_data['tracks'])}: {title} - {video_id}")
        download_song(video_id, output_dir, i, title)

        file_path = os.path.join(output_dir, f"{i:02d} - {title}.m4a")
        if os.path.exists(file_path):
            update_metadata(
                file_path=file_path,
                title=original_title,
                album=ALBUM,
                track_number=track_within_disc,
                total_tracks=len(album_data["tracks"]),
                disc=current_disc,
                total_discs=len(disc_track_counts),
                album_artist=ARTIST,
                artists=genius_data["artist"],
                cover_image_path=cover_path,
                genre=GENRES,
                year=YEAR,
                explicit=explicit,
                lyrics=genius_data["lyrics"],
                video_id=video_id,
            )
        cumulative_track += 1
        track_within_disc += 1
    send2trash(cover_path)


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
