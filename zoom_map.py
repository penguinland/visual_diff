#!/usr/bin/python3

from functools import partial
import numpy
import PIL.Image
import PIL.ImageTk
import tkinter as tk


class ZoomMap(tk.Canvas):
    _ZOOMED_IN_LEVELS = 3  # Number of times you can zoom in beyond 100%
    _MIN_MAP_SIZE = 250  # Pixel length at which to stop zooming out
    _HEIGHT=500
    _WIDTH=500

    def __init__(self, tk_parent, matrix):
        super().__init__(tk_parent, height=self._HEIGHT, width=self._WIDTH,
                         bg="green", xscrollincrement=1, yscrollincrement=1)
        self._matrix = matrix
        self._pyramid = []
        # We keep a handle to the actual image being displayed, because TK
        # doesn't do that itself and then it gets garbage collected while it's
        # still supposed to be on the screen. We also keep track of the TK
        # image object, so we can delete it later when we create a new, updated
        # one to take its place.
        self._cached_image = None
        self._tk_image = None

        def add_level(level):
            self._pyramid.append(level)

        # Start by zooming into the matrix so that each pixel of the original
        # takes up multiple pixels on the screen.
        zoomed_in_matrix = matrix
        for _ in range(self._ZOOMED_IN_LEVELS):
            next_level = numpy.zeros([2 * x for x in zoomed_in_matrix.shape])
            for r in [0, 1]:
                for c in [0, 1]:
                    next_level[r::2, c::2] = zoomed_in_matrix
            add_level(next_level)
            zoomed_in_matrix = next_level
        self._pyramid.reverse()  # The most zoomed-in part comes at the base
        add_level(matrix)

        # Now, zoom out and make the matrix smaller and smaller
        while max(matrix.shape) > 2 * self._MIN_MAP_SIZE:
            # Combine 2x2 squares of pixels to make the next level.
            nr, nc = [(value // 2) * 2 for value in matrix.shape]
            quads = [matrix[row:nr:2, col:nc:2]
                     for row in [0, 1] for col in [0, 1]]
            # TODO: Is there a standard way of resizing a binary image that
            # keeps lines crisp while removing salt-and-pepper noise?

            # We want the following outcomes when combining a 2x2 square into a
            # single pixel:
            #   - If none of the 4 pixels is set, we should not be set.
            #   - If 1 of the 4 pixels is set, we're set a quarter of the time.
            #   - If 2 of the 4 pixels are set, we're set half the time.
            #   - It's impossible to have 3 of the 4 pixels set.
            #   - If all 4 pixels are set, this one should be set, too.
            # To discuss the times when half the pixels are set:
            #   - If the two that are set are on the main diagonal, we should be
            #     set. It's good to make diagonals easy to see.
            #   - If the two that are set are off the main diagonal, we should
            #     not be set.
            #   - If the two that are set are adjacent to each other, we should
            #     be set half the time.
            # To discuss times when 1 pixel is set:
            #   - If the 1 pixel is off the diagonal, it might be part of a
            #     large diagonal line shifted 1 pixel off of our diagonal. Half
            #     of these should be set.
            #   - If the 1 pixel is on the diagonal, we should not be set (so
            #     that we're set a quarter of the time overall).
            # To satisfy all these conditions, we should be set either if both
            # pixels on the diagonal are set or if 1 pixel off the diagonal is
            # set.
            matrix = ((quads[0] & quads[3]) |
                      (quads[1] & numpy.logical_not(quads[2])))
            add_level(matrix)

        # self._zoom_level is the index into self._pyramid to get the current
        # image.
        self._zoom_level = self._ZOOMED_IN_LEVELS  # Start at 100%

        self._set_image()
        self.pack()
        [self.bind(*args) for args in
                [("<Button-4>", partial(self._map_zoom, -1)),
                 ("<Button-5>", partial(self._map_zoom,  1)),
                 ("<Button-1>", self._on_click),
                 ("<B1-Motion>", self._on_drag),
                 ("<ButtonRelease-1>", self._on_unclick)]]

    def _set_image(self):
        if self._tk_image is not None:
            # Clean up the old image.
            self.delete(self._tk_image)
            self._cached_image = None
            self._tk_image = None

        # We'll make an image that covers as much of the 3-screen-by-3-screen
        # area centered on the actual screen center as we have data to cover.
        # Start by figuring out where the top-left corner of the screen is in
        # canvas coordinates.
        top_left_x = int(self.canvasx(0))
        top_left_y = int(self.canvasy(0))

        current_data = self._pyramid[self._zoom_level]
        nr, nc = current_data.shape

        min_x = max(0,  top_left_x -     self._WIDTH)
        min_y = max(0,  top_left_y -     self._HEIGHT)
        max_x = min(nc, top_left_x + 2 * self._WIDTH)
        max_y = min(nr, top_left_y + 2 * self._HEIGHT)

        submatrix = current_data[min_y:max_y, min_x:max_x]
        if len(submatrix) == 0:
            # We're so far away from the actual data that none of it will fit
            # on or even near the screen. Rather than attempting and failing to
            # display this data, just don't show it in the first place.
            # TODO: Should we snap to the nearest edge or something? It would
            # be nice if we couldn't explore outside the data.
            return

        # Hold on to the image because tkinter doesn't, and we don't want it to
        # get garbage collected at the end of this function!
        self._cached_image = self._to_image(submatrix)
        self._tk_image = self.create_image(min_x, min_y, anchor=tk.NW,
                                           image=self._cached_image)

    def _map_zoom(self, amount, event):
        if not self.zoom(amount):
            return

        # Otherwise, we changed zoom levels, so adjust everything accordingly.
        # We need to move the map so the pixels that started under the mouse are
        # still under it afterwards.
        location_shift = (2 ** -amount) - 1
        self.xview_scroll(int(self.canvasx(event.x) * location_shift), "units")
        self.yview_scroll(int(self.canvasy(event.y) * location_shift), "units")

        self._set_image()

    def _on_click(self, event):
        self._click_coords = [event.x, event.y]

    def _on_drag(self, event):
        dx = self._click_coords[0] - event.x
        dy = self._click_coords[1] - event.y
        self.xview_scroll(dx, "units")
        self.yview_scroll(dy, "units")
        self._on_click(event)

    def _on_unclick(self, event):
        self._set_image()

    @staticmethod
    def _to_image(matrix):
        image = PIL.Image.fromarray(matrix * 255)
        return PIL.ImageTk.PhotoImage(image)

    @property
    def zoom_level(self):
        return 2 ** (self._zoom_level - self._ZOOMED_IN_LEVELS)

    def zoom(self, amount):
        """
        Returns whether we successfully changed zoom levels.
        """
        orig_zoom_level = self._zoom_level
        # Note that tkinter doesn't spawn extra threads, so this doesn't have
        # race conditions.
        self._zoom_level += amount
        self._zoom_level = min(self._zoom_level, len(self._pyramid) - 1)
        self._zoom_level = max(self._zoom_level, 0)
        return (self._zoom_level != orig_zoom_level)
