# Changelog

## v0.3.3 — 27/10/2026
- scripts/seed_demo.py: carga de demonstração (208 peças, 48 serviços, prefixo DEMO-; --remover limpa).
- Busca de peças e serviços por palavras ("pastilha onix").

## v0.3.2 — 27/10/2026
- Correção: editar um cadastro sem alterar nada dava "não encontrado" (MySQL contava 0 linhas alteradas); conexão agora usa FOUND_ROWS.

## v0.3.1 — 27/10/2026
- Correção: VEICULO.CODIGO_FIPE era VARCHAR(10) e recebia "modelo/ano" (v003 alarga para 24).
- API: erro não tratado agora responde JSON com CORS (antes o navegador mostrava só "Failed to fetch"); DataError/IntegrityError viram 400/409 legíveis.

## site v1 — 27/10/2026
- Site de vendas aofficina.com.br: herói com logo, seção por módulo (recepção, agenda, orçamento→OS, mão de obra/hora, NFS-e/reforma), IA, financeiro, licença (sem preço), FAQ, formulário → WhatsApp, privacidade (LGPD).
- Fotos: slots `site/img/carro-1.jpg` (herói) e `carro-2.jpg` (faixa); sem arquivo local, tenta foto livre do Unsplash; sem internet, fundo marinho.
- A fazer: robô de atendimento inicial no WhatsApp.

## v0.3 — 27/10/2026
- Assistente de IA portado do WebTriagem: botões ✍️🎤✨ em queixa, diagnóstico, observações, serviço executado (pedido), descrição do serviço (mão de obra) e aplicação (peças).
- Pesquisa por IA no pedido: "Pesquisar problema" (sintoma + veículo + km) e código de peça (lupa ao lado do lançamento de peça).
- Rotas /ia/status, /ia/escrita/config, /ia/transcrever, /ia/corrigir, /ia/pesquisar; contexto_oficina.md.
- Importador FIPE imprime progresso a cada 25 modelos.

## v0.2 — 27/10/2026
- Telas: agenda por oficina (dia, colunas por mecânico e equipamento, conflito bloqueado), peças, mão de obra, oficinas/recursos, empresa, lista de orçamentos/pedidos, tela do pedido (itens, autorização por item, aprovação → pedido, execução pelo mecânico, status, impressão).
- API: TIME das oficinas devolvido como HH:MM; edição de item de serviço preserva valor fechado ao mudar só o 'autorizado'.
- Importador FIPE: retry com espera crescente em queda de conexão; cron com `-u` e `--max-req 950` (token).
- Bootstrap/ícones servidos localmente (web/vendor) — sem CDN.
- Site: botão WhatsApp.

## v0.1 — 27/10/2026
- Base: API FastAPI + MySQL, migrations v001/v002, auth JWT/bcrypt, login/painel/clientes, systemd, Nginx, scripts.
