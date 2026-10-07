# Tradutor Matexpr — infixa → pós-fixada

Trabalho I de Compiladores (2026.2). Tradutor que lê um programa `Matexpr` de um
arquivo, valida sua estrutura e exibe na tela cada expressão aritmética traduzida
da notação infixa para a pós-fixada.

Implementado em Python 3.10+, sem dependências externas.

## Como executar

```bash
python3 main.py exemplos/valido.txt
# ou
python3 -m matexpr exemplos/valido.txt

# exibindo também os tokens reconhecidos pelo analisador léxico
python3 main.py --tokens exemplos/valido.txt
```

Entrada (`exemplos/valido.txt`):

```c
Matexpr {
    int a;
    float b;
    a + b * c;
    (a + b) * c;
}
```

Saída:

```
a b c * +
a b + c *
```

Códigos de saída: `0` sucesso, `1` erro léxico/sintático, `2` erro ao abrir o arquivo.

## Testes

```bash
python3 -m unittest discover -s tests -t . -v
```

## Arquitetura

```
matexpr/
├── tokens.py   # TokenType, Token, palavras reservadas e símbolos
├── errors.py   # LexicalError e SyntaxError_ (sempre com número da linha)
├── lexer.py    # Analisador léxico
├── parser.py   # Analisador sintático preditivo + esquema de tradução
├── cli.py      # Leitura do arquivo e exibição do resultado
└── __main__.py # permite `python -m matexpr`
tests/          # testes unitários (unittest)
exemplos/       # arquivos de entrada válidos e com erros
```

Fluxo: `arquivo → Lexer → tokens → Parser (ações semânticas) → expressões pós-fixadas`.
O parser pede um token por vez ao léxico (`next_token`), como no capítulo 2 do
livro do Aho et al.

### Analisador léxico

- Ignora espaços, tabulações, quebras de linha e comentários no estilo C
  (`/* ... */`, inclusive em várias linhas, e `// ...`).
- `num`: inteiros (`42`) e ponto flutuante (`3.14`).
- `id`: somente letras do alfabeto (`a-z`, `A-Z`).
- `type`: `int`, `float`. `Matexpr`: palavra reservada (diferencia maiúsculas).
- Erros léxicos: caractere inválido, identificador com dígito/`_` (`var1`),
  número mal formado (`3.`, `12abc`, `1.2.3`), comentário não fechado.

### Gramática

Gramática do enunciado:

```
program → Matexpr block
block   → { decls stmts }
decls   → decls decl | ε
decl    → type id ;
stmts   → stmts stmt
stmt    → block
expr    → expr + term | expr - term | term
term    → term * fact | term / fact | fact
fact    → ( expr ) | num | id
```

Ajustes necessários:

1. `stmts → stmts stmt` não tem caso base, por isso foi adicionado `ε`.
2. `stmt → block` nunca chega a `expr`, por isso foi adicionada a alternativa `stmt → expr ;`.
3. Um analisador preditivo não aceita recursão à esquerda, então ela foi eliminada
   (`A → Aα | β` vira `A → βA'`, `A' → αA' | ε`).

Gramática transformada (LL(1)), com as ações semânticas entre `{ }`:

```
program  → Matexpr block EOF
block    → { decls stmts }
decls    → decl decls | ε
decl     → type id ;
stmts    → stmt stmts | ε
stmt     → block | expr ;
expr     → term restExpr
restExpr → + term {print('+')} restExpr
         | - term {print('-')} restExpr
         | ε
term     → fact restTerm
restTerm → * fact {print('*')} restTerm
         | / fact {print('/')} restTerm
         | ε
fact     → ( expr ) | num {print(num)} | id {print(id)}
```

As produções `restExpr` e `restTerm` (recursão de cauda) foram implementadas como
laços `while`. O resultado é equivalente e preserva a associatividade à esquerda
(`a - b - c` → `a b - c -`).

Conjuntos usados nas decisões do parser:

| Não-terminal | Decisão |
|---|---|
| `decls` | continua enquanto o lookahead for `type` |
| `stmts` | continua até o lookahead ser `}` (FOLLOW) |
| `stmt`  | `{` → `block`; `(`, `num`, `id` → `expr ;` |
| `fact`  | `(` → `( expr )`; `num`; `id` |

### Mensagens de erro

O tradutor para no primeiro erro e informa o tipo e a linha:

```
Erro léxico na linha 3: caractere inválido '#'
Erro sintático na linha 4: esperado ';', encontrado '}'
Erro sintático na linha 4: esperado comando (bloco ou expressão) ou '}', encontrado fim do arquivo
```
