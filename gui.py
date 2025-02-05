import darkdetect
from math import ceil
import numpy
import numpy.typing
import tkinter as tk
import tkinter.font as tkfont
from typing import Optional

from tokenizer import FileInfo
from zoom_map import ZoomMap


class _Context(tk.Text):
    """
    A display of surrounding code, with the relevant tokens highlighted. We will
    have one of these for the token(s) represented by the column of the mouse
    cursor, and another for its row.
    """
    TAB_WIDTH: int = 4  # Width of a tab, in characters
    CONTEXT_COUNT: int = 3  # Lines to display before/after the current one
    # We hope we don't encounter files with more than 99,999 lines, but if we
    # do, alignment will be off.
    LINE_NUMBER_WIDTH: int = 5  # Maximum number of digits in the line number
    PRELUDE_WIDTH: int = LINE_NUMBER_WIDTH + 2  # Line number, colon, space

    def __init__(
        self,
        tk_parent: tk.Widget,
        data: FileInfo,
        text_width: int,
        zoom_map: ZoomMap,
    ) -> None:
        height = 2 * self.CONTEXT_COUNT + 1
        # NOTE: Lines longer than text_width get truncated, and any tokens off
        # the end don't get shown/highlighted.
        width = self.PRELUDE_WIDTH + text_width
        super().__init__(tk_parent, width=width, height=height,
                         state=tk.DISABLED, font="TkFixedFont", borderwidth=2,
                         relief="ridge")
        self.pack()

        # Set the tab width. Tcl/tk uses a list of tab stop distances, where
        # each '\t' character will advance the text to the next tab stop. The
        # units on these widths are not characters, but something more
        # fine-grained (pixels? points?). The first tab should go TAB_WIDTH
        # characters past the end of the prelude (the line number), and the
        # next one should go TAB_WIDTH additional characters past that.
        # Subsequent tab stops are inferred to be the same distance apart as
        # the last two tab stops specified, so these two are sufficient for
        # everything else.
        font = tkfont.Font(font=self["font"])
        prelude_width = font.measure(" " * self.PRELUDE_WIDTH)
        tab_width     = font.measure(" " * self.TAB_WIDTH)
        self.config(tabs=f"{prelude_width +     tab_width} "
                         f"{prelude_width + 2 * tab_width}")

        self._text_width = text_width
        self._lines = data.lines
        self._boundaries = data.boundaries
        self._zoom_map = zoom_map
        self._highlight_color = "grey" if darkdetect.isDark() else "yellow"

    def _snip_line(self, i: int) -> str:
        """
        Returns the part of line i that will fit in the display.
        """
        line_start = self._lines[i][:self._text_width]

        # If we have tabs in the line, they will register as a single character
        # but take up multiple characters of width.
        tab_count = line_start.count("\t")
        characters_on_line = self._text_width - tab_count * (self.TAB_WIDTH - 1)
        line_start = line_start[:characters_on_line]

        updated_tab_count = line_start.count("\t")
        if tab_count != updated_tab_count:
            # We removed a tab while shortening the line to fit all the tabs.
            # Hopefully this is rare enough that it's not worth figuring out a
            # solution that always works.
            print("PROBLEM: tabs at the end of the line!")
        return line_start

    def display(self, pixel: int) -> None:
        # The zoom level is equivalent to the number of tokens described by the
        # current pixel in the map.
        zoom_level = self._zoom_map.zoom_level
        first_token_index = int(pixel * zoom_level)
        last_token_index = min(first_token_index + ceil(zoom_level),
                               len(self._boundaries)) - 1

        if not (0 <= first_token_index < len(self._boundaries)):
            # TODO: Restrict panning so that we can't go outside the image.
            return  # We're out of range of the image. Skip it.
        line_number = self._boundaries[first_token_index][0][0]

        # Recall that line_number comes from the token module, which starts
        # counting at 1 instead of 0.
        start = line_number - self.CONTEXT_COUNT - 1
        end   = line_number + self.CONTEXT_COUNT
        lines = ["{:>{}}: {}".format(i + 1, self.LINE_NUMBER_WIDTH,
                                     self._snip_line(i))
                 if 0 <= i < len(self._lines) else ""
                 for i in range(start, end)]
        text = "\n".join(lines)

        # Update the displayed code
        self.configure(state=tk.NORMAL)
        self.delete("1.0", tk.END)
        self.insert(tk.INSERT, text)

        # Highlight the tokens of interest...
        ar, ac = self._boundaries[first_token_index][0]
        br, bc = self._boundaries[last_token_index][1]
        self.tag_add("token",
                     "{}.{}".format(self.CONTEXT_COUNT + 1,
                                    ac + self.PRELUDE_WIDTH),
                     "{}.{}".format(self.CONTEXT_COUNT + 1 + br - ar,
                                    bc + self.PRELUDE_WIDTH))
        self.tag_config("token", background=self._highlight_color)

        # ...but don't highlight the line numbers on multi-line tokens.
        for i in range(self.CONTEXT_COUNT):
            line = i + self.CONTEXT_COUNT + 2
            self.tag_remove("token",
                            "{}.{}".format(line, 0),
                            "{}.{}".format(line, self.PRELUDE_WIDTH))

        # Remember to disable editing again when we're done, so users can't
        # modify the code we're displaying!
        self.configure(state=tk.DISABLED)


class _Gui(tk.Frame):
    def __init__(
        self,
        matrix: numpy.typing.NDArray[numpy.uint8],
        hues: Optional[numpy.typing.NDArray[numpy.uint8]],
        data_a: FileInfo,
        data_b: FileInfo,
        map_width: int,
        text_width: int,
        root: tk.Tk,
    ) -> None:
        super().__init__(root)
        self.pack(fill=tk.BOTH, expand=True)
        self._map = ZoomMap(self, matrix, hues, map_width)

        self._contexts = [_Context(self, data, text_width, self._map)
                          for data in (data_a, data_b)]
        for event in ("<Motion>", "<Enter>"):
            self._map.bind(event, self._on_motion)

    def _on_motion(self, event: tk.Event) -> None:
        # We're using (row, col) format, so the first one changes with Y.
        self._contexts[0].display(self._map.canvasy(event.y))
        self._contexts[1].display(self._map.canvasx(event.x))


def launch(
    matrix: numpy.typing.NDArray[numpy.uint8],
    hues: Optional[numpy.typing.NDArray[numpy.uint8]],
    data_a: FileInfo,
    data_b: FileInfo,
    map_width: int,
    text_width: int,
) -> None:
    """
    Creates a new window for the GUI and runs the main program.
    """
    root = tk.Tk()

    def _quit(event: tk.Event) -> None:
        root.destroy()
    for char in "wWqQ":
        root.bind("<Control-{}>".format(char), _quit)

    # We construct a _Gui object, but don't bother holding on to a reference to
    # it because we're never going to touch it again. It doesn't get garbage
    # collected because `root` holds a reference to it.
    _Gui(matrix, hues, data_a, data_b, map_width, text_width, root)
    while True:
        try:
            root.mainloop()
            break
        except UnicodeDecodeError:
            # Macs running Python 3.6 and older have a bug in TK where they
            # interpret scroll wheel events as though they should be UTF-8 even
            # though they're not. You can try upgrading TK, but Python 3.7 and
            # later has its own built-in version of TK which doesn't have the
            # bug.
            print("Macs with old versions of TK installed don't scroll "
                  "properly. Try upgrading Python to version 3.7 or later.")
