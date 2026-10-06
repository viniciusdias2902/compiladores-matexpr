import unittest

from matexpr.errors import CompilerError, LexicalError, SyntaxError_
from matexpr.parser import translate


def prog(body: str) -> str:
    return "Matexpr {\n" + body + "\n}"


def tr(expr: str) -> str:
    """Traduz uma única expressão dentro de um programa mínimo."""
    result = translate(prog(expr + ";"))
    assert len(result) == 1
    return result[0]


class TestTraducao(unittest.TestCase):
    def test_operando_simples(self):
        self.assertEqual(tr("a"), "a")
        self.assertEqual(tr("42"), "42")
        self.assertEqual(tr("3.14"), "3.14")

    def test_soma(self):
        self.assertEqual(tr("a + b"), "a b +")

    def test_precedencia(self):
        self.assertEqual(tr("a + b * c"), "a b c * +")
        self.assertEqual(tr("a * b + c"), "a b * c +")
        self.assertEqual(tr("a - b / c"), "a b c / -")

    def test_associatividade_a_esquerda(self):
        self.assertEqual(tr("a - b - c"), "a b - c -")
        self.assertEqual(tr("a / b / c"), "a b / c /")
        self.assertEqual(tr("a - b + c"), "a b - c +")

    def test_parenteses(self):
        self.assertEqual(tr("(a + b) * c"), "a b + c *")
        self.assertEqual(tr("a - (b - c)"), "a b c - -")
        self.assertEqual(tr("((a))"), "a")

    def test_expressao_complexa(self):
        self.assertEqual(tr("9 - 5 + 2"), "9 5 - 2 +")
        self.assertEqual(tr("(a + 2.5) * (b - c) / 4"), "a 2.5 + b c - * 4 /")

    def test_varias_expressoes(self):
        src = prog("int a; float b;\n a + b;\n a * b;\n")
        self.assertEqual(translate(src), ["a b +", "a b *"])

    def test_blocos_aninhados(self):
        src = prog("int a;\n a + 1;\n { float b; b * 2; { a - b; } }\n 3;")
        self.assertEqual(translate(src), ["a 1 +", "b 2 *", "a b -", "3"])

    def test_programa_sem_comandos(self):
        self.assertEqual(translate("Matexpr { }"), [])
        self.assertEqual(translate("Matexpr { int a; float b; }"), [])

    def test_bloco_vazio_aninhado(self):
        self.assertEqual(translate("Matexpr { { } { } }"), [])

    def test_comentarios_no_programa(self):
        src = "/* cabeçalho */\nMatexpr { // início\n a /* meio */ + b; }"
        self.assertEqual(translate(src), ["a b +"])


class TestErrosSintaticos(unittest.TestCase):
    def assertErro(self, src, linha, trecho=""):
        with self.assertRaises(SyntaxError_) as ctx:
            translate(src)
        self.assertEqual(ctx.exception.line, linha, str(ctx.exception))
        self.assertIn(trecho, str(ctx.exception))
        self.assertIn(f"linha {linha}", str(ctx.exception))

    def test_falta_matexpr(self):
        self.assertErro("{ a; }", 1, "esperado 'Matexpr'")

    def test_falta_chave_abertura(self):
        self.assertErro("Matexpr a;", 1, "esperado '{'")

    def test_falta_chave_fechamento(self):
        self.assertErro("Matexpr {\n int a;\n a + 1;\n", 4, "fim do arquivo")

    def test_falta_ponto_e_virgula_expr(self):
        self.assertErro("Matexpr {\n a + b\n}", 3, "esperado ';'")

    def test_falta_ponto_e_virgula_decl(self):
        self.assertErro("Matexpr {\n int a\n float b;\n}", 3, "esperado ';'")

    def test_decl_sem_identificador(self):
        self.assertErro("Matexpr {\n int ;\n}", 2, "esperado identificador")

    def test_decl_com_palavra_reservada(self):
        self.assertErro("Matexpr { int float; }", 1, "esperado identificador")

    def test_decl_apos_comando(self):
        self.assertErro("Matexpr {\n a;\n int b;\n}", 3, "declaração 'int' após comandos")

    def test_operador_sem_operando(self):
        self.assertErro("Matexpr {\n a + ;\n}", 2, "esperado '(', número ou identificador")

    def test_operadores_seguidos(self):
        self.assertErro("Matexpr { a * / b; }", 1, "encontrado '/'")

    def test_parentese_nao_fechado(self):
        self.assertErro("Matexpr {\n (a + b;\n}", 2, "esperado ')'")

    def test_parentese_sobrando(self):
        self.assertErro("Matexpr { a + b); }", 1, "esperado ';'")

    def test_operandos_sem_operador(self):
        self.assertErro("Matexpr { a b; }", 1, "esperado ';'")

    def test_tokens_apos_programa(self):
        self.assertErro("Matexpr { }\n a;", 2, "esperado fim do arquivo")

    def test_menos_unario_nao_suportado(self):
        self.assertErro("Matexpr { -a; }", 1, "encontrado '-'")

    def test_arquivo_vazio(self):
        self.assertErro("", 1, "fim do arquivo")


class TestErrosLexicosNoParser(unittest.TestCase):
    def test_erro_lexico_propagado_com_linha(self):
        with self.assertRaises(LexicalError) as ctx:
            translate("Matexpr {\n int a;\n a $ b;\n}")
        self.assertEqual(ctx.exception.line, 3)

    def test_hierarquia_de_erros(self):
        with self.assertRaises(CompilerError):
            translate("Matexpr { x1; }")


if __name__ == "__main__":
    unittest.main()
