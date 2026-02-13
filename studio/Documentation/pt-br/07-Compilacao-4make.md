# 06 - Compilação com 4make

## O que é a compilação
A compilação usa o compilador 4make (Informix/4GL) no backend.
Isso gera binários conforme o ambiente suporta.

## Como compilar
Menu Run > Compile with 4make

Regras:
- Apenas arquivos .4gl podem ser compilados
- O backend precisa ter o 4make instalado

Exemplo:
1) Abra um .4gl
2) Run > Compile with 4make
3) Veja o toast de sucesso/erro

Observações:
- Compilação é diferente de interpretação
- Compilar não substitui o Run

Limitações conhecidas:
- Se o 4make não estiver instalado, a compilação falha

