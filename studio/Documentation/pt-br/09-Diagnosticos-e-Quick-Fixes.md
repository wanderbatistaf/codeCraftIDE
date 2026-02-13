# 08 - Diagnósticos e Quick Fixes

## O que são diagnósticos
Diagnósticos são análises estáticas do código que detectam erros, avisos e melhorias.
O backend processa isso via `POST /api/diagnostics`.

## Quick Fixes
Quando o diagnóstico oferece sugestões, o editor mostra quick fixes.
Essas sugestões são retornadas por `POST /api/code-actions`.

Exemplo:
1) Crie uma variável não definida
2) O editor marca a linha com erro
3) Abra o quick fix e aplique

Exemplo de problema:
```4gl
MAIN
    DISPLAY x
END MAIN
```

Resultado:
- Diagnóstico: variável x não definida
- Quick fix: sugerir DEFINE x

Limitações conhecidas:
- Diagnósticos não substituem o compilador (são análise estática)

