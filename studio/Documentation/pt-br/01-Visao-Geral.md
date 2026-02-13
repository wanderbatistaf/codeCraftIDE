# 00 - Visão Geral

O Studio (CodeCraft IDE) é um IDE web para Informix 4GL com:
- Editor Monaco com suporte a 4GL, PER, Python, SQL, FM2 e CSS
- Execução de 4GL no backend
- Conversão 4GL <-> Python
- Compilação com 4make
- Explorador de arquivos local e remoto (SFTP)
- Banco de dados integrado (schema, queries, terminal)
- Preview de formulários (.per) e editor Lycia (.fm2)

Requisitos básicos:
- Backend em http://localhost:8000
- Studio em http://localhost:9002

Exemplo rápido (fluxo típico):
1) Abrir um .4gl
2) Editar
3) Run para executar
4) Ver saída no Console

Limitações conhecidas:
- Funcionalidades dependem do backend estar ativo
- Algumas funções exigem drivers de banco instalados no backend

