from pathlib import PurePath
from textual.app import App, ComposeResult
from textual.containers import ScrollableContainer
from textual.driver import Driver
from textual.widgets import Input, Static, Footer, TextArea
from textual import events

from ai_teacher import *

class LogApp(App):
    """A simple log display with input that actually scrolls."""
    
    CSS_PATH = "chat.tcss"
    BINDINGS = [
        ("ctrl+s", "submit", "Submit Content"),
        ("ctrl+c", "quit", "Quit")
    ]

    def __init__(self, driver_class: type[Driver] | None = None, css_path: str | PurePath | List[str | PurePath] | None = None, watch_css: bool = False, ansi_color: bool = False):
        super().__init__(driver_class, css_path, watch_css, ansi_color)
        day = 1
        self.sday = f"day{day:02}"
        self.content_manager = ContentManager(sday=self.sday)
        self.step = 0
    
    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield ScrollableContainer(
            Static(id="log-display"),
            id="log-container"
        )
        # yield Input(placeholder="Type something and press Enter...", id="user-input")
        yield TextArea(id="text-area", language="markdown")  # 多行输入部件
        yield Footer()
    
    def on_mount(self) -> None:
        """Initialize the app."""
        self.log_container = self.query_one("#log-container", ScrollableContainer)
        self.text_area = self.query_one("#text-area", TextArea)
        self.log_display = self.query_one("#log-display", Static)
        self.text_area.focus()
    
    def on_unmount(self) -> None:
        self.content_manager.save()

    def action_submit(self) -> None:
        input_text = self.text_area.text
        if input_text.strip():
            current_content = self.log_display.renderable
            new_content = f"{current_content}\nUser >\n{input_text}" if current_content else f"User >\n{input_text}"
            self.log_display.update(new_content)
            self.text_area.text = ""

            try:
                resp = self.content_manager.chat(input_text)
                self.log_display.update(f"{self.log_display.renderable}\nAI >\n{resp}\n")
            except Exception as e:
                self.content_manager.save()
                raise RuntimeError(e)

            # Scroll to bottom
            self.log_container.scroll_end()


if __name__ == "__main__":
    app = LogApp()
    app.run()