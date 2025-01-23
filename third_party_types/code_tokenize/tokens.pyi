from typing import Any


class Token:
    type: str
    text: str

class ASTToken(Token):
    ast_node: Any  # Not sure what this really is.
    new_line_before: bool
