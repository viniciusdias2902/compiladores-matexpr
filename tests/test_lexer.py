import unittest

from matexpr.errors import LexicalError
from matexpr.lexer import Lexer
from matexpr.tokens import TokenType as T


def types(src):
    return [t.type for t in Lexer(src).tokenize()]


def lexemes(src):
    return [t.lexeme for t in Lexer(src).tokenize()][:-1]


class TestTokens(unittest.TestCase):
    def test_palavras_reservadas(self):
        self.assertEqual(types("Matexpr int float"), [T.MATEXPR, T.TYPE, T.TYPE, T.EOF])

    def test_palavra_reservada_diferencia_maiusculas(self):
        self.assertEqual(types("matexpr Int"), [T.ID, T.ID, T.EOF])

    def test_identificadores(self):
        self.assertEqual(types("a abc XyZ"), [T.ID, T.ID, T.ID, T.EOF])

    def test_inteiros_e_floats(self):
        self.assertEqual(lexemes("0 42 3.14 10.0"), ["0", "42", "3.14", "10.0"])
        self.assertEqual(types("42 3.14"), [T.NUM, T.NUM, T.EOF])

    def test_simbolos(self):
        self.assertEqual(
            types("+-*/(){};"),
            [T.PLUS, T.MINUS, T.TIMES, T.DIVIDE, T.LPAREN, T.RPAREN,
             T.LBRACE, T.RBRACE, T.SEMI, T.EOF],
        )

    def test_sem_espacos(self):
        self.assertEqual(lexemes("a+3.5*(b)"), ["a", "+", "3.5", "*", "(", "b", ")"])

    def test_entrada_vazia(self):
        self.assertEqual(types(""), [T.EOF])


class TestIgnorados(unittest.TestCase):
    def test_espacos_tabs_quebras(self):
        self.assertEqual(lexemes(" \t a \n\r\n b\t"), ["a", "b"])

    def test_comentario_bloco(self):
        self.assertEqual(lexemes("a /* comentário + * */ b"), ["a", "b"])

    def test_comentario_bloco_multilinha(self):
        self.assertEqual(lexemes("a /* linha1\nlinha2 */ b"), ["a", "b"])

    def test_comentario_linha(self):
        self.assertEqual(lexemes("a // ignora isto ;\nb"), ["a", "b"])

    def test_divisao_nao_e_comentario(self):
        self.assertEqual(types("a / b"), [T.ID, T.DIVIDE, T.ID, T.EOF])

    def test_comentario_com_asteriscos(self):
        self.assertEqual(lexemes("/*** x **/ a"), ["a"])


class TestLinhas(unittest.TestCase):
    def test_numero_da_linha(self):
        toks = Lexer("a\nb\n\nc").tokenize()
        self.assertEqual([t.line for t in toks[:3]], [1, 2, 4])

    def test_linha_apos_comentario_multilinha(self):
        toks = Lexer("/* 1\n2\n3 */ a").tokenize()
        self.assertEqual(toks[0].line, 3)


class TestErrosLexicos(unittest.TestCase):
    def assertErro(self, src, linha, trecho):
        lexer = Lexer(src)
        lexer.tokenize()
        self.assertEqual(len(lexer.errors), 1, lexer.errors)
        err = lexer.errors[0]
        self.assertIsInstance(err, LexicalError)
        self.assertEqual(err.line, linha)
        self.assertIn(trecho, str(err))

    def test_caractere_invalido(self):
        self.assertErro("a\nb # c", 2, "caractere inválido '#'")

    def test_identificador_com_digito(self):
        self.assertErro("var1", 1, "identificador inválido 'var1'")

    def test_identificador_com_underscore(self):
        self.assertErro("\nminha_var", 2, "identificador inválido 'minha_var'")

    def test_numero_terminando_em_ponto(self):
        self.assertErro("3.", 1, "número mal formado")

    def test_numero_com_letra(self):
        self.assertErro("12abc", 1, "número mal formado '12abc'")

    def test_numero_com_dois_pontos(self):
        self.assertErro("1.2.3", 1, "número mal formado '1.2.3'")

    def test_comentario_nao_fechado_informa_linha_de_inicio(self):
        self.assertErro("a\n/* nunca fecha\n\n", 2, "comentário não fechado")


class TestRecuperacaoLexica(unittest.TestCase):
    def test_caractere_invalido_e_descartado(self):
        lexer = Lexer("a # b")
        self.assertEqual([t.lexeme for t in lexer.tokenize()][:-1], ["a", "b"])
        self.assertEqual(len(lexer.errors), 1)

    def test_identificador_invalido_vira_id(self):
        lexer = Lexer("var1 + b")
        toks = lexer.tokenize()
        self.assertEqual((toks[0].type, toks[0].lexeme), (T.ID, "var1"))
        self.assertEqual(toks[1].type, T.PLUS)

    def test_numero_mal_formado_vira_num(self):
        toks = Lexer("3. + 12abc").tokenize()
        self.assertEqual([t.type for t in toks], [T.NUM, T.PLUS, T.NUM, T.EOF])

    def test_varios_erros_com_linhas(self):
        lexer = Lexer("a $\nb1\n@ c\n/* aberto")
        lexer.tokenize()
        self.assertEqual([e.line for e in lexer.errors], [1, 2, 3, 4])

    def test_entrada_valida_sem_erros(self):
        lexer = Lexer("Matexpr { int a; a + 1.5; }")
        lexer.tokenize()
        self.assertEqual(lexer.errors, [])


if __name__ == "__main__":
    unittest.main()
