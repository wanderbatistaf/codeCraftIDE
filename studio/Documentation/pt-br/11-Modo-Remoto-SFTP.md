# 10 - Modo Remoto (SFTP)

## O que é o modo remoto
Permite editar arquivos direto de um servidor remoto via SFTP.
O IDE passa a operar em modo Remote.

## Ativação
- Na conexão de banco, habilite `use_remote_files`
- Configure `remote_workspace_path` se necessário
- O indicador no topo muda para Remote

## Abrir arquivos remotos
- File > Open File(s) from Server
- File > Browse Server Folder

## Regras importantes
- Se houver arquivos com alteração pendente, o IDE bloqueia a troca de modo
- Arquivos abertos por caminho absoluto são marcados como externos
- Ao salvar, o IDE usa endpoints SFTP

Exemplo:
1) Ative o modo remoto
2) Browse Server Folder
3) Abra um arquivo remoto e edite
4) Save para gravar no servidor

Limitações conhecidas:
- A performance depende da rede e do servidor
- Alguns paths podem exigir permissão no servidor

