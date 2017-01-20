# visual-diff
A tool for generating a visual comparison of two Python source code files.

TODO: put some images here!

## Prerequisites
You'll need Python3 with PIL, and if you want to use the GUI you'll need the TK
bindings for PIL. If you're running on Ubuntu, try this:

```
sudo apt-get install python3-pil.imagetk
```

If you're running a different OS, good luck (and if you get it to work, please
either file an issue telling us to update the documentation with what you did,
or update it yourself and send us a pull request!).

You can clone this repository in the usual way:

```
git clone https://github.com/keyme/visual-diff.git
```

## Options
The short version: run `visual_diff.py --help` for info.

The main program is `visual_diff.py`. You can either specify 1 or 2 different
filenames containing Python code as arguments to it. With 2 files, it compares
one to the other; with only 1 file it compares the file to itself.

Each file is treated as a sequence of Python tokens. A token is the smallest
semantic piece of a program; tokens include keywords like "if" and "for",
parentheses, variable names, indentation changes, etc. We then generate an
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
Don't run this on very large files! It can take up all your RAM trying to write
the image to disk or display it to the screen and freeze your whole system. As
a quick estimate, if you have a 1000 line file with 10 tokens per line, the
resulting image will be 100 megapixels, which can be uncomfortably large.

There are plans to make the GUI not have these problems. but for the moment,
it's still an issue. Similarly, it would be neat if we could save large images
without falling over (or at least give some sort of a warning and refuse to
continue on unless the user explicitly said it was okay), but that isn't built
yet, either.

## Uses
Finding code that has been copied and pasted or is otherwise similar enough to
consider refactoring. This is the main use case of this code. These show up
as diagonal lines in the image. TODO: give example images and discuss in more
detail

#### Other Uses
- Finding students who are cheating on their homework by copying and pasting
  code from each other. There are better tools for this task, but `visual_diff`
  is better than nothing.
- Cheating on homework by making sure that the code you have copied and pasted
  has been modified enough that it no longer looks copied and pasted.

## Motivation
This code was predominantly written by Alan Davidson (alan@key.me). He got the
idea from a talk he saw at DEFCON 2006, in which [Dan
Kaminsky](https://dankaminsky.com/) showed a very similar tool he had built to
compare binaries built from the same source code using different compilers.
Here are [slides he made](http://www.slideshare.net/dakami/dmk-shmoo2007) for a
very similar talk at SchmooCon 2007 (start around slide 45).
