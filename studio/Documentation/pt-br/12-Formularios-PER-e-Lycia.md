# 11 - Formulários (PER e Lycia)

## PER Preview
Quando você abre um .per:
- O editor fica à esquerda
- O preview aparece à direita
- O backend valida o formulário

Exemplo:
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

Se houver erros, eles aparecem no preview.

## Lycia (FM2)
Para .fm2, o Lycia Editor oferece:
- Preview visual
- Grid e zoom
- Fullscreen
- Painel de propriedades
- CSS externo
- Snapshot HTML

Exemplo de uso:
1) Abra um .fm2
2) Ative o grid
3) Ajuste zoom
4) Carregue um CSS

Limitações conhecidas:
- O preview depende do parser e pode falhar em arquivos incompletos

