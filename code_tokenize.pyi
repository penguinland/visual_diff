# The code_tokenize module doesn't contain type annotations, so here are the
# ones we use.

from typing import Any


# We actually return a list[code_tokenize.tokens.ASTToken], but that would be
# annoying to add annotations for.
def tokenize(file_contents: str, language: str) -> list[Any]: ...
