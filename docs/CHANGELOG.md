# Changelog

## v0.4.1 — 27/10/2026
- Impressão do orçamento / ordem de serviço refeita (`web/js/impressao.js`): documento próprio em A4 com logo da empresa, marca d'água do símbolo aOfficina, blocos de cliente/veículo, relato e diagnóstico, tabelas de mão de obra e peças, totais, pagamentos, garantia (90 dias / CDC), condições e assinaturas. Sem botões nem ícones de IA no papel.
- Site v3: menu realinhado; módulos "Placa pela câmera" e "Diagnóstico com IA".

## v0.4.0 — 27/10/2026
- Fechamento com pagamento: tela "Receber e entregar" no pedido concluído — Dinheiro (troco), PIX (QR Code BR Code demonstrativo + copia e cola), Débito, Crédito (1 a 6x com valor da parcela), Boleto (exige CPF/CNPJ e endereço; fica em aberto com vencimento). Pagamento dividido; "Fechar pedido e entregar" só com o total coberto.
- Tabela PAGAMENTO (v004) — base do WebFinanceiro. ENTREGUE agora só pelo fechamento com pagamento.
- requirements: qrcode + Pillow.

## v0.3.4 — 27/10/2026
- Leitor de placa pela câmera (tablet): botão "Placa" no painel, na lista de pedidos e na tela do pedido. OCR local (Tesseract) no servidor; candidatas com correção de confusões (O/0, I/1, B/8…); placa sempre confirmável à mão.
- Painel do veículo pela placa: pedidos em andamento (abre direto se for um só), histórico de atendimentos na oficina (data, km, serviços, peças, valor) e botão "Novo orçamento".
- API: POST /veiculos/ler-placa, GET /veiculos/{id}/historico.
- Instalação: `sudo apt install -y tesseract-ocr` + `pip install -r requirements-ia.txt`.

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
