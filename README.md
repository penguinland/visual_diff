# visual_diff
A tool for generating a visual comparison of two files of source code.

TODO: put some images here!

## Prerequisites
You'll need [Tcl/Tk bindings](https://docs.python.org/3/library/tkinter.html)
for Python. This might require installing something outside of your virtual
environment: you'll know it's right if you can run `python3 -m tkinter` and
get a little interactive window to pop up.

After that, just `pip install -r requirements.txt`, and you should be good!

On Ubuntu, you might try `sudo apt-get install python3-pil.imagetk` to get
Tcl/Tk set up correctly. I don't remember exactly what I did that finally
worked, but that was one of the things I tried.

If you're running a different OS, good luck (and if you get it to work, please
either file an issue telling us to update the documentation with what you did,
or update it yourself and send us a pull request!).

## Options
The short version: run `visual_diff.py --help` for info.

The main program is `visual_diff.py`. You can either specify 1 or 2 different
filenames containing source code as arguments to it. With 2 files, it compares
one to the other; with only 1 file it compares the file to itself. Both files
should be written in the same language (though I have vague plans to change
that in the future!).

Each file is treated as a sequence of lexical tokens. A token is the smallest
semantic piece of a program; tokens include keywords like "if" and "for",
parentheses, variable names, etc. We then generate an
image, in which the pixel in row i and column j is set if the ith token from
the first file and the jth token from the second file are equal. All strings
are considered equal regardless of their contents; all numbers are considered
equal, too.

If you specify the `--gui` option (and have the TK bindings for PIL installed),
a graphical user interface will open up in which you can explore the image. Use
the scroll wheel to zoom in and out, click-and-drag to pan around, and mouse
around the image to explore the code. Quit with control-Q or control-W. When
the GUI is finished, the intention is to have it be very similar to Google
Maps, OpenStreetMap, or other map exploration interfaces.

If you don't specify `--gui`, the image will be saved to file. By default it
goes in `output.png`, but you can specify a different place to put it with the
`-o` option.

## Warnings
Saving images to a file takes much more memory than displaying them to the
screen, and doing this with large images can freeze your whole system. So, by
default we refuse to save any image that is over 10 megapixels. This can be
overridden with the `--big_file` flag, but use that at your own peril.

## Uses
Finding code that has been copied and pasted or is otherwise similar enough to
consider refactoring. This is the main use case of this code. These show up
as diagonal lines in the image.

TODO: give example images and discuss in more detail

#### Other Uses
- Finding students who are cheating on their homework by copying and pasting
  code from each other. There are better tools for this task, but `visual_diff`
  is better than nothing.
- Cheating on homework by making sure that the code you have copied and pasted
  has been modified enough that it no longer looks copied and pasted.
  :upside_down_face:

## Motivation
This code was predominantly written by Alan Davidson. He got the
idea from a talk he saw at DEFCON 2006, in which [Dan
Kaminsky](https://dankaminsky.com/) showed a very similar tool he had built to
compare binaries made from the same source code using different compilers.
Here are [slides he made](http://www.slideshare.net/dakami/dmk-shmoo2007) for a
very similar talk at SchmooCon 2007 (start around slide 45).
