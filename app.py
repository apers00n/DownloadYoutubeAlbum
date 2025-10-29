from textual.app import App, ComposeResult
from textual.widgets import Footer, Input, Button, LoadingIndicator, Static
from textual.containers import Container, Vertical, VerticalScroll
from textual.reactive import reactive
from art import text2art
from downloader import getAlbums
from downloadScreen import DownloadScreen


class AlbumTUI(App):
    CSS_PATH = "app.css"
    album_name = reactive("")

    def compose(self) -> ComposeResult:
        headerText = str(text2art("What     Album?", font="tarty1-large"))

        with Vertical(id="main-container") as self.main_container:
            yield Static(headerText, id="title")
            with Container(id="text-container") as self.outer_container:
                with Container(id="inner-text-container") as self.inner_container:
                    self.album_input = Input(
                        placeholder="Type album name here...", id="album_input"
                    )
                    yield self.album_input

            yield Footer()

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

        self.scroll_container = VerticalScroll(id="scroll-container")
        await self.outer_container.mount(self.scroll_container)

        for album in results:
            btn = Button(album["title"], classes="append")
            btn.album_data = album
            await self.scroll_container.mount(btn)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        button = event.button
        if hasattr(button, "album_data"):
            await self.push_screen(DownloadScreen(button.album_data))
        elif button.id == "back-btn":
            await self.pop_screen()


if __name__ == "__main__":
    AlbumTUI().run()
