#!/usr/bin/python3

import functools
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

    def __init__(self, tk_parent, data, axis, zoom_map):
        height = 2 * self.CONTEXT_COUNT + 1
        width = self.PRELUDE_WIDTH + self.TEXT_WIDTH
        super().__init__(tk_parent, width=width, height=height,
                         state=tk.DISABLED, font="TkFixedFont")
        self.pack()
        # TODO: Use a NamedTuple?
        self._tokens, self._lines, self._boundaries = data
        self._axis = axis
        self._zoom_map = zoom_map

    def display(self, event):
        # TODO: Check this whole thing for off-by-one errors.
        # The zoom level is equivalent to the number of tokens described by the
        # current pixel in the map.
        zoom_level = self._zoom_map.zoom_level
        begin_token_index = getattr(event, self._axis) * zoom_level
        end_token_index = min(begin_token_index + zoom_level,
                              len(self._boundaries)) - 1
        if not (0 <= begin_token_index < len(self._boundaries)):
            # TODO: Should this ever happen? It does happen on the rightmost
            # and bottommost edges of the image.
            print("Out of range; skipping!")
            return
        line_number = self._boundaries[begin_token_index][0][0]

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

        # Highlight the tokens of interest.
        (ar, ac) = self._boundaries[begin_token_index][0]
        (br, bc) = self._boundaries[end_token_index][1]
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
        self._zoom_map = ZoomMap(matrix)
        self._map = tk.Label(self, image=self._zoom_map.image)
        self._map.pack()

        # We're using (row, col) format, so the first one changes with Y.
        self._contexts = [_Context(self, data, axis, self._zoom_map)
                          for data, axis in ((data_a, "y"), (data_b, "x"))]
        [self._map.bind(*args) for args in
                [("<Button-4>",  functools.partial(self._zoom, -1)),
                 ("<Button-5>",  functools.partial(self._zoom,  1)),
                 ("<Button-1>",  self._on_click),
                 ("<B1-Motion>", self._on_drag),
                 ("<Motion>",    self._on_motion),
                 ("<Enter>",     self._on_motion)]]

    def _on_motion(self, event):
        [context.display(event) for context in self._contexts]

    def _zoom(self, amount, event):
        # TODO: when click-and-drag is implemented and the whole map is not
        # onscreen, make the zooming centered around the curser.
        self._zoom_map.zoom(amount)
        self._map.configure(image=self._zoom_map.image)

    def _on_click(self, event):
        self._click_coords = [event.x, event.y]

    def _on_drag(self, event):
        # TODO: fill this in.
        dx = self._click_coords[0] - event.x
        dy = self._click_coords[1] - event.y
        print("Dragging ({}, {})".format(dx, dy))
        self._on_click(event)


def launch(matrix, data_a, data_b):
    root = tk.Tk()

    def _quit(event):
        root.destroy()
    [root.bind("<Control-{}>".format(char), _quit) for char in "wWqQ"]

    gui = _Gui(matrix, data_a, data_b, root)
    root.mainloop()
