# app.py
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Input, Static, ListView, ListItem
from textual.containers import Vertical
from textual.reactive import reactive
from art import text2art
from downloader import download_album  # your downloader module
from ytmusicapi import YTMusic
import asyncio


class AlbumTUI(App):
    CSS_PATH = "app.css"
    album_query = reactive("")
    albums = reactive([])
    selected_album = reactive(None)

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static(text2art("What Album?", font="tarty1-large"), id="title")
            self.input_widget = Input(
                placeholder="Type album name here...", id="album_input"
            )
            yield self.input_widget
            self.status_widget = Static("", id="status")
            yield self.status_widget
            self.list_view = ListView(id="album_list")
            yield self.list_view
            yield Footer()

    # Phase 1: handle search input
    def on_input_submitted(self, event: Input.Submitted) -> None:
        query = event.value.strip()
        if not query:
            return
        self.album_query = query
        self.status_widget.update("Searching YouTube Music...")
        self.set_focus(None)
        asyncio.create_task(self.search_albums(query))

    async def search_albums(self, query: str):
        yt = YTMusic()
        results = yt.search(query, filter="albums")
        if not results:
            self.status_widget.update("❌ No albums found")
            return

        self.albums = results
        self.list_view.clear()
        for album in results:
            title = album.get("title")
            artist = ", ".join(a["name"] for a in album.get("artists", []))
            self.list_view.append(ListItem(Static(f"{title} — {artist}")))
        self.status_widget.update("Select an album and press Enter")
        self.set_focus(self.list_view)

    # Phase 2: handle selection
    def on_list_view_selected(self, event: ListView.Selected) -> None:
        index = event.index
        if index < 0 or index >= len(self.albums):
            return
        self.selected_album = self.albums[index]
        self.status_widget.update(
            f"Downloading album '{self.selected_album['title']}' ..."
        )
        self.list_view.clear()
        self.set_focus(None)
        asyncio.create_task(self.download_selected_album())

    # Phase 3: download with progress updates
    async def download_selected_album(self):
        album_title = self.selected_album["title"]
        album_id = self.selected_album["browseId"]
        yt = YTMusic()
        album_data = yt.get_album(album_id)
        tracks = album_data["tracks"]
        total_tracks = len(tracks)

        output_dir = f"./Downloads/{album_title}"
        import os

        os.makedirs(output_dir, exist_ok=True)

        # download album track by track
        for i, track in enumerate(tracks, start=1):
            title = track["title"]
            video_id = track.get("videoId")
            if not video_id:
                continue
            self.status_widget.update(f"Downloading {i}/{total_tracks}: {title}")
            # call your downloader's function per track
            download_album_track = download_album  # reuse your existing function
            # using the track individually
            # optional: adjust your downloader to accept single track
            await asyncio.to_thread(download_album_track, title)
        self.status_widget.update(f"✅ Finished downloading '{album_title}'")


if __name__ == "__main__":
    AlbumTUI().run()
