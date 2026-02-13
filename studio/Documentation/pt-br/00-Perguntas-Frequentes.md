# 00 - Perguntas Frequentes

## Visão Geral

Q: Posso usar o Studio sem banco de dados?
A: Sim. O IDE funciona sem conexão ativa, mas recursos de DB ficam inativos.

Q: Preciso instalar algo no browser?
A: Não. O IDE roda no navegador e usa o backend via HTTP.

## Interface

Q: Onde vejo a saída do Run?
A: No Console, no Bottom Panel.

Q: Posso esconder o Bottom Panel?
A: Não há modo de esconder, apenas redimensionar a altura.

## Arquivos e Projetos

Q: Posso versionar .ccp no Git?
A: Pode, mas normalmente é melhor versionar os arquivos fonte diretamente.

Q: O .ccp guarda configurações de banco?
A: Não. Ele guarda arquivos e estado do IDE, não credenciais.

## Search e Command Palette

Q: A busca percorre arquivos binários?
A: Não. A busca foi pensada para texto.

Q: Posso buscar apenas dentro da pasta atual?
A: Atualmente não. A busca percorre todo o workspace.

## Editor e Linguagens

Q: Posso executar .py no IDE?
A: Não. Apenas .4gl pode ser executado pelo interpretador.

Q: O editor suporta autocomplete?
A: O Monaco oferece recursos básicos, mas não há autocomplete semântico dedicado.

## Interpretação 4GL

Q: Por que o Run está desabilitado?
A: O arquivo ativo não é .4gl ou não há aba ativa.

Q: O Run salva o arquivo automaticamente?
A: Não. Salve manualmente se quiser persistir as mudanças.

## Compilação 4make

Q: Onde fica o binário gerado?
A: No ambiente do backend, conforme o 4make configurar.

Q: Posso compilar projetos inteiros?
A: O IDE compila o arquivo ativo; compilação de diretório é via backend/CLI.

## Conversão 4GL-Python

Q: O arquivo original é alterado?
A: Não. O IDE cria um novo arquivo ao lado do original.

Q: Posso escolher onde salvar?
A: No IDE atual, o arquivo é criado no mesmo diretório.

## Diagnósticos e Quick Fixes

Q: Por que não vejo diagnósticos em .py?
A: O suporte a diagnósticos é focado em .4gl e .per.

Q: Quick fixes alteram o arquivo automaticamente?
A: Sim, quando aplicados.

## Banco de Dados

Q: Posso salvar várias conexões?
A: Sim, o IDE gerencia várias configurações.

Q: O SQL Query suporta transações?
A: Depende do backend e do driver configurado.

## Modo Remoto SFTP

Q: Posso usar modo remoto sem configurar banco?
A: O modo remoto está ligado à configuração de conexão no menu Database.

Q: Posso abrir arquivos fora do workspace remoto?
A: Sim, por caminho absoluto, mas eles ficam marcados como externos.

## Formulários PER e Lycia

Q: O preview atualiza em tempo real?
A: Sim, com pequeno debounce após editar.

Q: Posso exportar o HTML do Lycia?
A: Sim, pelo dialog HTML no editor Lycia.

## Sessão e Persistência

Q: Minhas abas somem ao reiniciar o browser?
A: Sim, sessionStorage é por sessão.

Q: Posso persistir permanentemente?
A: Atualmente não, só por sessão.

## Atalhos

Q: Existe atalho para Run?
A: O botão Run existe, mas atalho dedicado não foi configurado.

Q: Posso customizar atalhos?
A: Atualmente não.

## Solução de Problemas

Q: O IDE abre mas não lista arquivos.
A: Verifique se o backend está online e se o /api/files/tree responde.

Q: A busca não retorna resultados.
A: Verifique se está em Search Content e se o backend respondeu.
