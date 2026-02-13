# 12 - Sessão e Persistência

O Studio salva estado no sessionStorage por aba do navegador:
- Abas abertas
- Pastas expandidas
- Altura do painel inferior
- Conexão ativa

Cada aba do navegador tem sessão isolada.

Exemplo:
1) Abra 2 abas do browser
2) Cada aba salva seu estado de arquivos

Limitações conhecidas:
- O estado não é sincronizado entre navegadores
- Limpar o sessionStorage perde o estado

