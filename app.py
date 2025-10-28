from textual.app import App, ComposeResult
from textual.widgets import (
    Footer,
    Input,
    Static,
    LoadingIndicator,
)
from textual.containers import Container, Vertical, VerticalScroll
from textual.reactive import reactive
from art import text2art
from downloader import download_album, getAlbums
from textual.screen import Screen
import asyncio


class StatusScreen(Screen):
    def __init__(self, message: str):
        super().__init__()
        self.message = message

    def compose(self):
        yield Static(self.message)


class AlbumTUI(App):
    CSS_PATH = "app.css"
    album_name = reactive("")

    def compose(self) -> ComposeResult:
        with Vertical(id="main-container") as self.main_container:
            yield Static(text2art("What     Album?", font="tarty1-large"), id="title")
            with Container(id="text-container") as self.outer_container:
                with Container(id="inner-text-container") as self.inner_container:
                    self.album_input = Input(
                        placeholder="Type album name here...", id="album_input"
                    )
                    yield self.album_input

            yield Footer()

    async def show_loading(self):
        # Create the loading indicator
        self.loading = LoadingIndicator()
        await self.main_container.mount(self.loading)

        # Wait a few seconds to simulate work
        await asyncio.sleep(3)

        # Unmount it when done
        await self.loading.remove()  # <-- unmount

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        album_name = event.value.strip()
        if not album_name:
            return

        self.loading = LoadingIndicator()
        await self.main_container.mount(self.loading)

        results = getAlbums(album_name)
        await self.loading.remove()

        if hasattr(self, "scroll_container"):
            await self.scroll_container.remove()
        self.scroll_container = VerticalScroll(id="scroll-container", classes="right")
        await self.outer_container.mount(self.scroll_container)

        for album in results:
            self.scroll_container.mount(Static(album["title"], classes="append"))


if __name__ == "__main__":
    AlbumTUI().run()
