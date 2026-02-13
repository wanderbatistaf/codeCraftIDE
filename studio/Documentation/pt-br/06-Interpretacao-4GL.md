# 05 - Interpretação 4GL

## O que acontece quando você clica em Run
O Studio envia o conteúdo do arquivo ativo (.4gl) para o backend, usando `POST /api/execute`.
No backend:
1) O código é parseado (lexer + parser)
2) Um AST é gerado
3) O interpretador executa o AST
4) O backend devolve output, tempo e erros

O resultado aparece no Console do Bottom Panel.

## Banco de dados na execução
- Se houver uma conexão ativa no menu Database, ela é enviada junto
- O interpretador usa essa conexão para executar SQL embutido

## Tipos de erro
- LexerError / ParserError: erro de sintaxe
- RuntimeError: erro durante a execução
- Erros de banco: falha de conexão ou SQL

## Exemplo completo
Arquivo `hello.4gl`:
```4gl
MAIN
    DEFINE name CHAR(20)
    LET name = "World"
    DISPLAY "Hello", name
END MAIN
```

Passos:
1) Abra `hello.4gl`
2) Clique Run
3) Veja o Console com a saída

Console esperado:
```
Hello World
```

Limitações conhecidas:
- Apenas arquivos .4gl podem ser executados
- A execução depende do backend estar online

