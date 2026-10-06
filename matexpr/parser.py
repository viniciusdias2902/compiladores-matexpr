"""Analisador sintático preditivo (descendente recursivo) com esquema de
tradução dirigido por sintaxe: traduz expressões infixas para pós-fixadas.

Gramática original (enunciado):
    program -> Matexpr block
    block   -> { decls stmts }
    decls   -> decls decl | ε
    decl    -> type id ;
    stmts   -> stmts stmt
    stmt    -> block
    expr    -> expr + term | expr - term | term
    term    -> term * fact | term / fact | fact
    fact    -> ( expr ) | num | id

Gramática transformada (sem recursão à esquerda, LL(1)), com ações semânticas
entre chaves duplas {{ }}:
    program -> Matexpr block EOF
    block   -> { decls stmts }
    decls   -> decl decls | ε                    FIRST(decl) = { type }
    decl    -> type id ;
    stmts   -> stmt stmts | ε                    FOLLOW(stmts) = { '}' }
    stmt    -> block | expr ;                    {{ emitir tradução }}
    expr    -> term restExpr
    restExpr-> + term {{print('+')}} restExpr
             | - term {{print('-')}} restExpr
             | ε
    term    -> fact restTerm
    restTerm-> * fact {{print('*')}} restTerm
             | / fact {{print('/')}} restTerm
             | ε
    fact    -> ( expr )
             | num {{print(num.lexema)}}
             | id  {{print(id.lexema)}}

Observações sobre a gramática do enunciado:
  * stmts -> stmts stmt não tem caso base; foi adicionado ε.
  * stmt -> block nunca alcança expr; foi adicionada a alternativa expr ;
  * As recursões restExpr e restTerm são implementadas como laços (while),
    equivalente à eliminação da recursão de cauda.
"""

from .errors import SyntaxError_
from .lexer import Lexer
from .tokens import DESCRIPTIONS, Token, TokenType

FIRST_EXPR = (TokenType.LPAREN, TokenType.NUM, TokenType.ID)


class Parser:
    def __init__(self, source: str):
        self.lexer = Lexer(source)
        self.lookahead: Token = self.lexer.next_token()
        self._current: list[str] = []      # tradução da expressão em andamento
        self.translations: list[str] = []  # uma tradução por comando expr ;

    # ---------- utilitários ----------

    def _error(self, expected: str) -> SyntaxError_:
        tok = self.lookahead
        found = DESCRIPTIONS[TokenType.EOF] if tok.type is TokenType.EOF else f"'{tok.lexeme}'"
        return SyntaxError_(f"esperado {expected}, encontrado {found}", tok.line)

    def _match(self, expected: TokenType) -> Token:
        if self.lookahead.type is not expected:
            raise self._error(DESCRIPTIONS[expected])
        tok = self.lookahead
        self.lookahead = self.lexer.next_token()
        return tok

    def _emit(self, symbol: str) -> None:
        self._current.append(symbol)

    # ---------- não-terminais ----------

    def parse(self) -> list[str]:
        """program -> Matexpr block EOF"""
        self._match(TokenType.MATEXPR)
        self._block()
        self._match(TokenType.EOF)
        return self.translations

    def _block(self) -> None:
        """block -> { decls stmts }"""
        self._match(TokenType.LBRACE)
        self._decls()
        self._stmts()
        self._match(TokenType.RBRACE)

    def _decls(self) -> None:
        """decls -> decl decls | ε"""
        while self.lookahead.type is TokenType.TYPE:
            self._decl()

    def _decl(self) -> None:
        """decl -> type id ;"""
        self._match(TokenType.TYPE)
        self._match(TokenType.ID)
        self._match(TokenType.SEMI)

    def _stmts(self) -> None:
        """stmts -> stmt stmts | ε   (ε quando lookahead = '}')"""
        while self.lookahead.type is not TokenType.RBRACE:
            self._stmt()

    def _stmt(self) -> None:
        """stmt -> block | expr ;"""
        if self.lookahead.type is TokenType.LBRACE:
            self._block()
        elif self.lookahead.type in FIRST_EXPR:
            self._current = []
            self._expr()
            self._match(TokenType.SEMI)
            self.translations.append(" ".join(self._current))
        elif self.lookahead.type is TokenType.TYPE:
            raise SyntaxError_(
                f"declaração '{self.lookahead.lexeme}' após comandos "
                "(declarações devem vir no início do bloco)",
                self.lookahead.line,
            )
        else:
            raise self._error("comando (bloco ou expressão) ou '}'")

    def _expr(self) -> None:
        """expr -> term restExpr"""
        self._term()
        while self.lookahead.type in (TokenType.PLUS, TokenType.MINUS):
            op = self._match(self.lookahead.type)
            self._term()
            self._emit(op.lexeme)

    def _term(self) -> None:
        """term -> fact restTerm"""
        self._fact()
        while self.lookahead.type in (TokenType.TIMES, TokenType.DIVIDE):
            op = self._match(self.lookahead.type)
            self._fact()
            self._emit(op.lexeme)

    def _fact(self) -> None:
        """fact -> ( expr ) | num | id"""
        t = self.lookahead.type
        if t is TokenType.LPAREN:
            self._match(TokenType.LPAREN)
            self._expr()
            self._match(TokenType.RPAREN)
        elif t in (TokenType.NUM, TokenType.ID):
            self._emit(self._match(t).lexeme)
        else:
            raise self._error("'(', número ou identificador")


def translate(source: str) -> list[str]:
    """Traduz um programa Matexpr e devolve as expressões em notação pós-fixada."""
    return Parser(source).parse()
