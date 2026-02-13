# 02 - Arquivos e Projetos

Abrir arquivos e pastas:
- File > Open File(s) / Open Folder
- Duplo clique no arquivo no Explorer
- Command Palette (Ctrl+P / Cmd+P)

Criar arquivos e pastas:
- File > New File / New Folder
- Botões no Explorer
- Context menu (botão direito) em pasta

Renomear e deletar:
- Context menu no Explorer
- Ao deletar, abas abertas relacionadas são fechadas

Download de arquivo:
- Context menu em arquivo > Download

Tabs e estado:
- Abas abertas ficam salvas por aba do navegador (sessionStorage)
- Indicador de arquivo alterado (dot)
- Fechar aba com alteração pede confirmação

## Projetos (.ccp)

### O que é um .ccp
Um arquivo `.ccp` (CodeCraft Project) é o pacote de um projeto do IDE. Ele guarda:
- Todos os arquivos do projeto (4GL, PER, SQL, etc.)
- O estado do IDE no momento do salvamento:
  - Abas abertas
  - Aba ativa
  - Pastas expandidas

Na prática, ele funciona como um "snapshot" do projeto + seu estado de trabalho.

### New Project
- Cria um novo projeto no workspace
- Estrutura inicial:
  - `nome.4gl` (arquivo principal)
  - `global.4gl` (definições globais)
  - `nome.per` (formulário de exemplo)
- O Explorer passa a mostrar a pasta do projeto como raiz

### Open Project
- Importa um `.ccp`
- Recria os arquivos no workspace
- Reabre as abas salvas no projeto

### Save Project
- Gera um `.ccp` para download
- Inclui arquivos atuais + estado do IDE

Exemplo: criar e salvar projeto
1) File > New Project
2) Informe nome e descrição
3) Edite os arquivos
4) File > Save Project (gera um .ccp)

Exemplo: abrir projeto
1) File > Open Project
2) Selecione um .ccp
3) O IDE recria os arquivos e reabre as abas

Limitações conhecidas:
- Ao abrir um .ccp, o workspace atual é sobrescrito pelos arquivos do projeto
- Save Project sempre gera download (não salva no servidor)

