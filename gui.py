#!/usr/bin/python3

from functools import partial
from math import ceil
import tkinter as tk

from zoom_map import ZoomMap


class _Context(tk.Text):
    CONTEXT_COUNT = 3  # Lines to display before/after the current one
    # TODO: What about files with over 99,999 lines?
    LINE_NUMBER_WIDTH = 5  # Number of characters to allocate for line numbers
    PRELUDE_WIDTH = LINE_NUMBER_WIDTH + 2  # Line number, colon, space
    # TODO: What about files with very long lines? They currently wrap around to
    # the next line and push later context out of the widget. Should we truncate
    # them instead? and if so, should we change which part gets cut based on the
    # location of the token within the line?
    TEXT_WIDTH = 80

    def __init__(self, tk_parent, data, zoom_map):
        height = 2 * self.CONTEXT_COUNT + 1
        width = self.PRELUDE_WIDTH + self.TEXT_WIDTH
        super().__init__(tk_parent, width=width, height=height,
                         state=tk.DISABLED, font="TkFixedFont")
        self.pack()
        # TODO: Use a NamedTuple?
        self._tokens, self._lines, self._boundaries = data
        self._zoom_map = zoom_map

    def display(self, pixel):
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
                                     self._lines[i])
                 if 0 <= i < len(self._lines) else ""
                 for i in range(start, end)]
        text = "\n".join(lines)

        # Update the displayed code
        self.configure(state=tk.NORMAL)
        self.delete("1.0", tk.END)
        self.insert(tk.INSERT, text)

        # Highlight the tokens of interest...
        (ar, ac) = self._boundaries[first_token_index][0]
        (br, bc) = self._boundaries[last_token_index][1]
        self.tag_add("token",
                     "{}.{}".format(self.CONTEXT_COUNT + 1,
                                    ac + self.PRELUDE_WIDTH),
                     "{}.{}".format(self.CONTEXT_COUNT + 1 + br - ar,
                                    bc + self.PRELUDE_WIDTH))
        self.tag_config("token", background="yellow")

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
    def __init__(self, matrix, data_a, data_b, root):
        super().__init__(root)
        self.pack(fill=tk.BOTH, expand="true")
        self._map = ZoomMap(self, matrix)

        self._contexts = [_Context(self, data, self._map)
                          for data in (data_a, data_b)]
        [self._map.bind(event, self._on_motion)
                for event in ["<Motion>", "<Enter>"]]

    def _on_motion(self, event):
        # We're using (row, col) format, so the first one changes with Y.
        self._contexts[0].display(self._map.canvasy(event.y))
        self._contexts[1].display(self._map.canvasx(event.x))


def launch(matrix, data_a, data_b):
    root = tk.Tk()

    def _quit(event):
        root.destroy()
    [root.bind("<Control-{}>".format(char), _quit) for char in "wWqQ"]

    gui = _Gui(matrix, data_a, data_b, root)
    root.mainloop()
