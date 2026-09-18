# Spotify Learning Integration

Integração opcional para usar músicas, podcasts e playlists como material de prática de inglês.

## Objetivo da demo

- Nova sugere conteúdo por nível e objetivo.
- O usuário autoriza o acesso somente quando quiser.
- Nenhum token, playlist ou dado da conta é salvo no Git.
- O modo local continua funcionando sem Spotify.

## Fluxo planejado

1. Usuário escolhe “Conectar Spotify”.
2. A aplicação abre o fluxo oficial de autorização.
3. O token fica somente no armazenamento local protegido.
4. Nova consulta playlists, faixas ou podcasts autorizados.
5. A aula registra apenas o vocabulário aprovado pelo usuário.

## Próxima implementação

Criar o adaptador OAuth e um modo mock para demonstração no GitHub sem exigir conta real.

Nunca coloque `client_secret`, tokens ou arquivos `.env` neste repositório.
