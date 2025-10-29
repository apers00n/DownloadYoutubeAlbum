import asyncio
import os
from textual.screen import Screen
from textual.widgets import Static, Button
from textual.containers import Vertical
from pyfiglet import Figlet
from downloader import download_image, download_song, update_metadata, safe_filename
from ytmusicapi import YTMusic
from getGenres import get_album_genres

yt = YTMusic()

straight = Figlet(font="chunky", width=175)
small = Figlet(font="doom", width=175)


class DownloadScreen(Screen):
    """A screen that shows info about an album."""

    def __init__(self, album_data: dict):
        super().__init__()
        self.album_data = album_data

    def compose(self):
        with Vertical() as self.main:
            yield Static(
                small.renderText(self.album_data["title"]),
                id="song-title",
                classes="pink-text",
            )
            yield Static(
                straight.renderText(
                    f"{self.album_data['artists'][0]['name']}"),
                classes="pink-text",
            )
            yield Button("Download", id="download-btn")
            yield Button("Back", id="back-btn")

    async def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "download-btn":
            asyncio.create_task(self.download())

    async def download(self):
        album_data = yt.get_album(self.album_data["browseId"])
        ALBUM = album_data["title"]
        ARTIST = album_data["artists"][0]["name"]
        COVER_URL = album_data["thumbnails"][-1]["url"]
        GENRES = get_album_genres(ARTIST, ALBUM)
        YEAR = album_data["year"]

        output_dir = os.path.join(os.path.expanduser("~/Downloads"), ALBUM)
        os.makedirs(output_dir, exist_ok=True)

        cover_path = os.path.join(output_dir, "cover.jpg")
        await asyncio.to_thread(download_image, COVER_URL, cover_path)

        track_widgets = []
        for i, track in enumerate(album_data["tracks"], start=1):
            title = track["title"]
            btn = Static(f"{i}. {title}", classes="song song-default")
            track_widgets.append(btn)
            await self.main.mount(btn)

        for i, track in enumerate(album_data["tracks"], start=1):
            title = track["title"]
            video_id = track.get("videoId")
            if not video_id:
                continue

            btn = track_widgets[i - 1]

            self.refresh()
            await asyncio.sleep(0)

            await asyncio.to_thread(download_song, video_id, output_dir, i, title)

            file_path = os.path.join(
                output_dir, f"{i:02d} - {safe_filename(title)}.mp3"
            )
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

            btn.update(f"{i}. {title}")
            btn.remove_class("song-downloading")
            btn.add_class("song-downloaded")

            await asyncio.sleep(0.05)
