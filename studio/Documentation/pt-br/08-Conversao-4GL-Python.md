# 07 - Conversão 4GL <-> Python

## 4GL -> Python
Menu Run > Convert to Python

O que acontece:
1) O Studio envia o código .4gl para `POST /api/conversion/convert`
2) O backend gera Python equivalente
3) O IDE cria um `.py` no mesmo diretório
4) O novo arquivo é aberto automaticamente

Exemplo:
4GL:
```4gl
MAIN
    DEFINE x INTEGER
    LET x = 10
    DISPLAY x
END MAIN
```

Python gerado (exemplo):
```python
def main() -> None:
    x: int = 0
    x = 10
    print(x)
```

## Python -> 4GL
Menu Run > Convert to 4GL

O que acontece:
1) O Studio envia o código .py para `POST /api/conversion/reverse`
2) O backend gera 4GL
3) O IDE cria um `.4gl` no mesmo diretório
4) O arquivo gerado é aberto

## Warnings
- A conversão pode gerar warnings se algum recurso não for mapeado
- O IDE mostra warnings no console/notify quando fornecidos

## Dicas
- Converta arquivos pequenos primeiro para validar o resultado
- Compare o output da execução 4GL vs Python quando possível

Limitações conhecidas:
- Nem todo recurso 4GL tem mapeamento 1:1 para Python
- Conversão reversa (Python -> 4GL) é limitada ao subset suportado

