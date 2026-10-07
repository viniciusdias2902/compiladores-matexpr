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

from dataclasses import dataclass, field

from .errors import CompilerError, SyntaxError_
from .lexer import Lexer
from .tokens import DESCRIPTIONS, Token, TokenType

FIRST_EXPR = (TokenType.LPAREN, TokenType.NUM, TokenType.ID)


@dataclass
class TranslationResult:
    translations: list[str] = field(default_factory=list)  # uma por comando expr ;
    errors: list[CompilerError] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


class Parser:
    def __init__(self, source: str):
        self.lexer = Lexer(source)
        self.lookahead: Token | None = None
        self._current: list[str] = []      # tradução da expressão em andamento
        self.translations: list[str] = []  # uma tradução por comando expr ;
        self.errors: list[SyntaxError_] = []
        self._last_error_token: Token | None = None
        self._previous: Token | None = None  # último token consumido

    # ---------- utilitários ----------

    def _advance(self) -> Token:
        tok = self._previous = self.lookahead
        self.lookahead = self.lexer.next_token()
        return tok

    def _error(self, expected: str, line: int | None = None) -> SyntaxError_:
        tok = self.lookahead
        found = DESCRIPTIONS[TokenType.EOF] if tok.type is TokenType.EOF else f"'{tok.lexeme}'"
        return SyntaxError_(f"esperado {expected}, encontrado {found}", line or tok.line)

    def _match(self, expected: TokenType) -> Token:
        if self.lookahead.type is not expected:
            if expected is TokenType.SEMI and self._previous is not None:
                raise self._missing_semicolon()
            raise self._error(DESCRIPTIONS[expected])
        return self._advance()

    def _missing_semicolon(self) -> SyntaxError_:
        """O ';' falta logo após o token anterior; por isso o erro é relatado
        na linha dele, e não na linha do próximo token (que pode estar abaixo)."""
        return self._error(f"';' após '{self._previous.lexeme}'", self._previous.line)

    def _expect(self, expected: TokenType) -> None:
        """Como _match, mas registra o erro e segue como se o token estivesse
        presente (recuperação em nível de frase). Usado para '{' e '}'."""
        if self.lookahead.type is expected:
            self._advance()
        else:
            self._report(self._error(DESCRIPTIONS[expected]))

    def _report(self, err: SyntaxError_) -> None:
        """Registra um erro sintático, evitando erros em cascata."""
        # Sem consumir nenhum token desde o último erro: é consequência dele.
        if self.lookahead is self._last_error_token:
            return
        self._last_error_token = self.lookahead
        # A linha já tem erro léxico: o erro sintático provavelmente é efeito dele.
        if any(e.line == err.line for e in self.lexer.errors):
            return
        self.errors.append(err)

    def _synchronize(self, *stop: TokenType) -> None:
        """Modo pânico: descarta tokens até um ponto seguro (';', '{', '}',
        fim do arquivo ou um dos tokens em `stop`). O ';' é consumido."""
        sync = (TokenType.SEMI, TokenType.LBRACE, TokenType.RBRACE, TokenType.EOF, *stop)
        while self.lookahead.type not in sync:
            self._advance()
        if self.lookahead.type is TokenType.SEMI:
            self._advance()

    def _emit(self, symbol: str) -> None:
        self._current.append(symbol)

    # ---------- não-terminais ----------

    def parse(self) -> TranslationResult:
        """program -> Matexpr block EOF"""
        self.lookahead = self.lexer.next_token()
        if self.lookahead.type is TokenType.MATEXPR:
            self._advance()
        else:
            self._report(self._error(DESCRIPTIONS[TokenType.MATEXPR]))
            while self.lookahead.type not in (TokenType.LBRACE, TokenType.EOF):
                self._advance()
        self._block()
        if self.lookahead.type is not TokenType.EOF:
            self._report(self._error(DESCRIPTIONS[TokenType.EOF]))

        errors = sorted(self.lexer.errors + self.errors, key=lambda e: e.line)
        if errors:
            return TranslationResult(errors=errors)
        return TranslationResult(translations=self.translations)

    def _block(self) -> None:
        """block -> { decls stmts }"""
        self._expect(TokenType.LBRACE)
        self._decls()
        self._stmts()
        self._expect(TokenType.RBRACE)

    def _decls(self) -> None:
        """decls -> decl decls | ε"""
        while self.lookahead.type is TokenType.TYPE:
            self._decl()

    def _decl(self) -> None:
        """decl -> type id ;"""
        try:
            self._match(TokenType.TYPE)
            self._match(TokenType.ID)
            self._match(TokenType.SEMI)
        except SyntaxError_ as e:
            self._report(e)
            self._synchronize(TokenType.TYPE)

    def _stmts(self) -> None:
        """stmts -> stmt stmts | ε   (ε quando lookahead = '}')"""
        while self.lookahead.type not in (TokenType.RBRACE, TokenType.EOF):
            self._stmt()

    def _stmt(self) -> None:
        """stmt -> block | expr ;"""
        if self.lookahead.type is TokenType.LBRACE:
            self._block()
            return
        if self.lookahead.type is TokenType.TYPE:
            self._report(SyntaxError_(
                f"declaração '{self.lookahead.lexeme}' após comandos "
                "(declarações devem vir no início do bloco)",
                self.lookahead.line,
            ))
            self._decl()  # analisa a declaração mesmo assim
            return
        try:
            if self.lookahead.type not in FIRST_EXPR:
                raise self._error("comando (bloco ou expressão) ou '}'")
            self._current = []
            self._expr()
            self._match(TokenType.SEMI)
            self.translations.append(" ".join(self._current))
        except SyntaxError_ as e:
            self._report(e)
            self._synchronize()

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


def translate(source: str) -> TranslationResult:
    """Traduz um programa Matexpr. O resultado traz as expressões em notação
    pós-fixada ou a lista de erros encontrados."""
    return Parser(source).parse()
