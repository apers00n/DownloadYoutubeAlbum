from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Input, Placeholder, Static, Select
from textual.containers import Container, Vertical
from textual.reactive import reactive
from art import text2art
from downloader import download_album
from textual.screen import Screen


class StatusScreen(Screen):
    def __init__(self, message: str):
        super().__init__()
        self.message = message

    def compose(self):
        yield Static(self.message)


LINES = """I must not fear.
Fear is the mind-killer.
Fear is the little-death that brings total obliteration.
I will face my fear.
I will permit it to pass over me and through me.""".splitlines()


class AlbumTUI(App):
    CSS_PATH = "app.css"
    album_name = reactive("")

    def compose(self) -> ComposeResult:
        with Vertical(id="main-container"):
            yield Static(text2art("What     Album?", font="tarty1-large"), id="title")

            with Container(id="text-container"):
                with Container(id="inner-text-container"):
                    # yield Select(
                    #     ((line, line) for line in LINES),
                    # )
                    yield Input(placeholder="Type album name here...", id="album_input")

            yield Footer()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        album_name = event.value.strip()
        if not album_name:
            return

        self.album_name = album_name
        self.push_screen(StatusScreen(f"Downloading '{album_name}'..."))

        try:
            album, artist, total_tracks = download_album(album_name)
            self.push_screen(
                StatusScreen(
                    f"✅ Finished downloading '{album}' by {artist}, {
                        total_tracks
                    } tracks!"
                )
            )
        except Exception as e:
            self.push_screen(StatusScreen(f"❌ Error: {str(e)}"))


if __name__ == "__main__":
    AlbumTUI().run()
