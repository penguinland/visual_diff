from functools import partial
import numpy
import PIL.Image
import PIL.ImageTk
import tkinter as tk
from typing import Optional

from image_pyramid import ImagePyramid

class ZoomMap(tk.Canvas):
    def __init__(
        self,
        tk_parent: tk.Widget,
        matrix: numpy.ndarray,
        hues: Optional[numpy.ndarray],
        sidelength: int,
    ) -> None:
        super().__init__(tk_parent, height=sidelength, width=sidelength,
                         bg="green", xscrollincrement=1, yscrollincrement=1)
        # We keep a handle to the actual image being displayed, because TK
        # doesn't do that itself and then it gets garbage collected while it's
        # still supposed to be on the screen. We also keep track of the TK
        # image object, so we can delete it later when we create a new, updated
        # one to take its place.
        self._cached_image: Optional[PIL.ImageTk.PhotoImage] = None
        # TK canvas images are referred to by their ID numbers.
        self._tk_image: Optional[int] = None  # 

        self._pyramid = ImagePyramid(matrix, hues, sidelength)

        self._set_image()
        self.pack()
        for button_name, function in (("<Button-1>", self._on_click),
                                      ("<B1-Motion>", self._on_drag),
                                      ("<ButtonRelease-1>", self._on_unclick),
                                      # Linux scrolling
                                      ("<Button-4>", partial(self._zoom, -1)),
                                      ("<Button-5>", partial(self._zoom,  1)),
                                      # Mac scrolling
                                      ("<MouseWheel>", self._zoom_mac),
                                      ):
            # On this next line, mypy isn't smart enough to figure out that
            # every function will be Callable: some are methods and some are
            # functools.partial objects.
            self.bind(button_name, function)  # type: ignore

    def _set_image(self) -> None:
        """
        Delete the old image, if it exists, then display the new one.

        The image to use is at the current zoom level, 3 times taller and wider
        than the displayed window.
        """
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

        submatrix, min_x, min_y = self._pyramid.get_submatrix(top_left_x,
                                                              top_left_y)
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

    def _zoom_mac(self, event: tk.Event) -> None:
        self._zoom(-event.delta, event)

    def _zoom(self, amount: int, event: tk.Event) -> None:
        if not self._pyramid.zoom(amount):
            return

        # Otherwise, we changed zoom levels, so adjust everything accordingly.
        # We need to move the map so the pixels that started under the mouse are
        # still under it afterwards.
        location_shift = (2 ** -amount) - 1
        self.xview_scroll(int(self.canvasx(event.x) * location_shift), "units")
        self.yview_scroll(int(self.canvasy(event.y) * location_shift), "units")

        self._set_image()

    def _on_click(self, event: tk.Event) -> None:
        self._click_coords = [event.x, event.y]

    def _on_drag(self, event: tk.Event) -> None:
        dx = self._click_coords[0] - event.x
        dy = self._click_coords[1] - event.y
        self.xview_scroll(dx, "units")
        self.yview_scroll(dy, "units")
        self._on_click(event)

    def _on_unclick(self, event: tk.Event) -> None:
        self._set_image()

    @staticmethod
    def _to_image(matrix: numpy.ndarray) -> PIL.ImageTk.PhotoImage:
        image = PIL.Image.fromarray(matrix, mode="HSV")
        return PIL.ImageTk.PhotoImage(image)

    @property
    def zoom_level(self) -> int:  # Used in gui.py
        return 2 ** self._pyramid.get_zoom_level()
