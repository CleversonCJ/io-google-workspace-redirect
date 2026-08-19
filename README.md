# IO Google Workspace Redirect

ExApp para Nextcloud 33+ que abre arquivos ponteiro do Google Workspace sem
armazenar credenciais. O backend lê o arquivo pelo WebDAV no contexto do usuário
que executou a ação, valida o JSON e monta uma URL restrita a `docs.google.com`.

Formatos aceitos:

- `.gdoc` → `https://docs.google.com/document/d/<doc_id>/edit`
- `.gsheet` → `https://docs.google.com/spreadsheets/d/<doc_id>/edit`
- `.gslides` → `https://docs.google.com/presentation/d/<doc_id>/edit`
- `resource_key`, quando presente, vira `?resourcekey=<valor>`

## Segurança

- Não usa Google API, OAuth, senha de usuário nem credencial administrativa.
- Aceita somente os três sufixos previstos.
- Limita o arquivo ponteiro a 64 KiB.
- Valida `doc_id` e `resource_key` por lista de caracteres permitidos.
- A página de transição aceita apenas HTTPS no host exato `docs.google.com`.
- Não registra o conteúdo dos arquivos nos logs.

## Integração com Nextcloud 33

A ExApp usa File Actions Menu v2 e registra **Abrir no Google Workspace**. Como
o AppAPI 33 filtra ações por MIME, mas não por extensão, a ação é disponibilizada
para os MIME types normalmente usados por esses pequenos arquivos JSON; o backend
faz a validação definitiva da extensão.

O AppAPI 33 não expõe a propriedade `default` da biblioteca Files v4 para ExApps.
Por isso, o clique direto no nome do arquivo não pode ser substituído por uma
ExApp sem modificar o próprio AppAPI/Nextcloud. Esta implementação não aplica
patches ao NX11. Ao usar o menu, a página de transição tenta abrir uma nova aba;
se o navegador bloquear pop-ups, ela mostra um botão explícito.

## Desenvolvimento

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-dev.txt
pytest -q
node --check ex_app/js/redirect.js
```

## Instalação manual

Depois de publicar a imagem definida em `appinfo/info.xml`, registre a ExApp com:

```bash
occ app_api:app:register io-google-workspace-redirect \
  --info-xml https://raw.githubusercontent.com/CleversonCJ/io-google-workspace-redirect/main/appinfo/info.xml \
  --wait-finish
occ app_api:app:enable io-google-workspace-redirect
```

O comando deve ser executado no Nextcloud, não no host Docker remoto.

