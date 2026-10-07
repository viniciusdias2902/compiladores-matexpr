"""Exceções do tradutor. Toda mensagem informa a linha do erro."""


class CompilerError(Exception):
    kind = "Erro"

    def __init__(self, message: str, line: int):
        super().__init__(message)
        self.message = message
        self.line = line

    def __str__(self) -> str:
        return f"{self.kind} na linha {self.line}: {self.message}"


class LexicalError(CompilerError):
    kind = "Erro léxico"


class SyntaxError_(CompilerError):
    """Erro sintático (o sufixo evita conflito com o SyntaxError do Python)."""

    kind = "Erro sintático"


class SemanticWarning(CompilerError):
    """Aviso semântico: não impede a tradução."""

    kind = "Aviso"
