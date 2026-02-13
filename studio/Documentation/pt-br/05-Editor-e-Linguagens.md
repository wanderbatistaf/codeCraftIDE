# 04 - Editor e Linguagens

## 4GL (.4gl)
- Diagnósticos e quick fixes
- Execução pelo botão Run
- Conversão para Python

Exemplo:
```4gl
MAIN
    DEFINE name CHAR(20)
    LET name = "World"
    DISPLAY "Hello", name
END MAIN
```

## PER (.per)
- Diagnósticos
- Preview do formulário ao lado do editor
- Validação de campos e atributos

Exemplo mínimo:
```per
DATABASE mydb

SCREEN
{
    [name      ]
}
END

ATTRIBUTES
    name = formonly.name;
END
```

## FM2 (.fm2)
- Abre o editor Lycia
- Preview visual com grid e zoom
- Pode carregar CSS externo

## Python (.py)
- Edição normal
- Conversão para 4GL

## SQL (.sql), DEF (.def), CSS (.css)
- Edição normal
- CSS pode ser usado no preview do Lycia

Comportamentos importantes:
- O editor marca arquivos modificados
- Ctrl+S salva o arquivo ativo
- Save All salva todas as abas modificadas

Limitações conhecidas:
- Diagnósticos completos só estão ativos para .4gl e .per

