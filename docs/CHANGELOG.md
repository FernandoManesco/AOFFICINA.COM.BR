# Changelog

## v0.2 — 27/10/2026
- Telas: agenda por oficina (dia, colunas por mecânico e equipamento, conflito bloqueado), peças, mão de obra, oficinas/recursos, empresa, lista de orçamentos/pedidos, tela do pedido (itens, autorização por item, aprovação → pedido, execução pelo mecânico, status, impressão).
- API: TIME das oficinas devolvido como HH:MM; edição de item de serviço preserva valor fechado ao mudar só o 'autorizado'.
- Importador FIPE: retry com espera crescente em queda de conexão; cron com `-u` e `--max-req 950` (token).
- Bootstrap/ícones servidos localmente (web/vendor) — sem CDN.
- Site: botão WhatsApp.

## v0.1 — 27/10/2026
- Base: API FastAPI + MySQL, migrations v001/v002, auth JWT/bcrypt, login/painel/clientes, systemd, Nginx, scripts.
