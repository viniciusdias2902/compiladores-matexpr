import unittest

from matexpr.errors import CompilerError, LexicalError, SyntaxError_
from matexpr.parser import translate


def prog(body: str) -> str:
    return "Matexpr {\n" + body + "\n}"


def ok(src: str) -> list[str]:
    """Traduz um programa que deve ser válido e devolve as traduções."""
    result = translate(src)
    assert result.ok, [str(e) for e in result.errors]
    return result.translations


def tr(expr: str) -> str:
    """Traduz uma única expressão dentro de um programa mínimo."""
    result = ok(prog(expr + ";"))
    assert len(result) == 1
    return result[0]


def errors(src: str) -> list:
    result = translate(src)
    assert not result.ok, "era esperado ao menos um erro"
    assert result.translations == []
    return result.errors


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
        self.assertEqual(ok(src), ["a b +", "a b *"])

    def test_blocos_aninhados(self):
        src = prog("int a;\n a + 1;\n { float b; b * 2; { a - b; } }\n 3;")
        self.assertEqual(ok(src), ["a 1 +", "b 2 *", "a b -", "3"])

    def test_programa_sem_comandos(self):
        self.assertEqual(ok("Matexpr { }"), [])
        self.assertEqual(ok("Matexpr { int a; float b; }"), [])

    def test_bloco_vazio_aninhado(self):
        self.assertEqual(ok("Matexpr { { } { } }"), [])

    def test_comentarios_no_programa(self):
        src = "/* cabeçalho */\nMatexpr { // início\n a /* meio */ + b; }"
        self.assertEqual(ok(src), ["a b +"])


class TestErrosSintaticos(unittest.TestCase):
    def assertErro(self, src, linha, trecho=""):
        err = errors(src)[0]
        self.assertIsInstance(err, SyntaxError_)
        self.assertEqual(err.line, linha, str(err))
        self.assertIn(trecho, str(err))
        self.assertIn(f"linha {linha}", str(err))

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


class TestRecuperacaoDeErros(unittest.TestCase):
    def linhas(self, src):
        return [e.line for e in errors(src)]

    def test_relata_varios_erros(self):
        src = "Matexpr {\n a + ;\n b * (a;\n a + b;\n c c;\n}"
        self.assertEqual(self.linhas(src), [2, 3, 5])

    def test_continua_apos_erro_em_declaracao(self):
        src = "Matexpr {\n int ;\n float b;\n int 3;\n b + ;\n}"
        self.assertEqual(self.linhas(src), [2, 4, 5])

    def test_declaracao_apos_comando_e_analisada(self):
        src = "Matexpr {\n a;\n int b\n c;\n d + ;\n}"
        msgs = [str(e) for e in errors(src)]
        self.assertEqual(len(msgs), 3, msgs)
        self.assertIn("declaração 'int' após comandos", msgs[0])

    def test_bloco_aninhado_dentro_de_expressao_com_erro(self):
        src = "Matexpr {\n a + { b; }\n c - ;\n}"
        self.assertEqual(self.linhas(src), [2, 3])

    def test_sem_erros_em_cascata_por_chave_faltando(self):
        self.assertEqual(len(errors("Matexpr {\n { a;\n")), 1)

    def test_sem_matexpr_continua_no_bloco(self):
        msgs = [str(e) for e in errors("foo { a + ; }")]
        self.assertEqual(len(msgs), 2, msgs)
        self.assertIn("esperado 'Matexpr'", msgs[0])

    def test_erro_sintatico_na_linha_de_erro_lexico_e_suprimido(self):
        msgs = [str(e) for e in errors("Matexpr {\n a $ b;\n c + ;\n}")]
        self.assertEqual(len(msgs), 2, msgs)
        self.assertIn("Erro léxico na linha 2", msgs[0])
        self.assertIn("Erro sintático na linha 3", msgs[1])

    def test_erros_ordenados_por_linha(self):
        src = "Matexpr {\n a + ;\n b1;\n c # ;\n}"
        self.assertEqual(self.linhas(src), sorted(self.linhas(src)))

    def test_nenhuma_traducao_quando_ha_erros(self):
        result = translate("Matexpr { a + b; c + ; }")
        self.assertFalse(result.ok)
        self.assertEqual(result.translations, [])


class TestErrosLexicosNoParser(unittest.TestCase):
    def test_erro_lexico_propagado_com_linha(self):
        err = errors("Matexpr {\n int a;\n a $ b;\n}")[0]
        self.assertIsInstance(err, LexicalError)
        self.assertEqual(err.line, 3)

    def test_hierarquia_de_erros(self):
        self.assertIsInstance(errors("Matexpr { x1; }")[0], CompilerError)


if __name__ == "__main__":
    unittest.main()
