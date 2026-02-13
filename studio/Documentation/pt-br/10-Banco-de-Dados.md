# 09 - Banco de Dados

## Configurar conexões
Menu Database > Configure Connections

Campos principais:
- host, port, database, username, password
- driver: wbjdbc ou wborm
- server e db_type opcionais

Ao salvar, a conexão aparece na lista e pode ser ativada.

## Database Explorer
Mostra tabelas e colunas do banco ativo.
- Expandir tabela mostra colunas
- Busca por tabela ou coluna
- Context menu em tabela:
  - Copy Table Name
  - Generate SELECT *
- View Sample Data abre um dialog com dados

## SQL Query Panel
- Múltiplas abas de query
- Ctrl+Enter executa a query
- Resultados em tabela
- Export CSV (Copy/Download)

## Terminal SSH
- Abre um terminal remoto usando SSH
- Usa credenciais SSH da conexão
- Se não informado, usa host/usuário do banco

Exemplo de fluxo:
1) Configure uma conexão
2) Ative a conexão
3) Explore tabelas
4) Rode um SELECT no SQL Query

Limitações conhecidas:
- O Terminal depende de SSH aberto no servidor
- A visualização de dados pode ser limitada a 100 linhas por query (padrão)

