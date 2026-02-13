# 03 - Search e Command Palette

## File Search Modal
A busca do Studio permite encontrar texto no conteúdo dos arquivos ou encontrar arquivos pelo nome.
Abra pelo ícone de lupa no Explorer.

Modos:
- Search Content: busca texto dentro dos arquivos
- Search File Names: busca pelo nome do arquivo

Opções:
- Case Sensitive: diferencia maiúsculas/minúsculas
- Use Regex: usa expressão regular (apenas Search Content)

Como a busca funciona:
- Local mode: o frontend chama `POST /api/files/search`
- Remote mode: o frontend chama `POST /api/sftp/search`
- O backend retorna os arquivos e as linhas onde houve match
- O IDE agrupa resultados por arquivo e por linha
- Clique em um resultado para abrir o arquivo e ir direto para a linha

Exemplo (Search Content):
1) Abra a busca
2) Digite `DISPLAY` e pressione Enter
3) Clique em um resultado
4) O arquivo abre na linha do match

Exemplo (Search File Names):
1) Selecione Search File Names
2) Digite `global`
3) Clique no arquivo encontrado

Dicas:
- Use regex para encontrar padrões como `LET\s+\w+\s*=`
- Case Sensitive é útil para localizar nomes exatos de variáveis

## Command Palette
Atalho: Ctrl+P / Cmd+P

O Command Palette serve para:
- Abrir arquivos rapidamente
- Executar comandos comuns (ex.: Save All)
- Acessar arquivos recentes

Exemplo:
1) Pressione Ctrl+P
2) Digite parte do nome do arquivo
3) Pressione Enter para abrir

Limitações conhecidas:
- O Command Palette não executa todos os comandos do menu (apenas os listados)

