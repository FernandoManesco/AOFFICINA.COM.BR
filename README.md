# aOfficina — gestão para oficinas mecânicas

Software web de gestão para oficinas e redes de oficinas mecânicas, com foco em atendimento de alto padrão.
Produto da **IA Process Automation** (Fernando Manesco, Rio Claro/SP). Modelo comercial: **licença definitiva por
oficina** (venda, não aluguel), hospedado inicialmente em servidor da IA Process e migrável para o servidor do cliente.

- Site: https://aofficina.com.br · App: https://app.aofficina.com.br · API: https://api.aofficina.com.br
- Repositório: `FernandoManesco/AOFFICINA.COM.BR` · Início: 27/10/2026 · Versão atual: **0.4.0**

## Stack

| Camada | Tecnologia |
|---|---|
| Backend | Python 3.8 · FastAPI · Uvicorn (porta 8300) · systemd `aofficina-api` |
| Banco | MySQL 8 (utf8mb4), PyMySQL, dinheiro em centavos (BIGINT), migrations idempotentes em `db/migrations/` |
| Frontend | HTML + JS puro, Bootstrap 5.3 servido localmente (`web/vendor/`, sem CDN), PWA-friendly para tablet |
| Auth | JWT, bcrypt, níveis 0–4, rate limit no login, `SECURITY_LOG` |
| IA | DeepSeek (texto), MyScript iink (escrita à mão), faster-whisper (ditado no servidor, opcional), Tesseract (OCR de placa) |
| Deploy | Nginx + certbot, uma instância (banco próprio) por oficina cliente |

Estrutura de pastas e convenções: [`docs/00_LEIA_PRIMEIRO.md`](docs/00_LEIA_PRIMEIRO.md). Instalação passo a passo:
[`docs/01_INSTALACAO_T140.md`](docs/01_INSTALACAO_T140.md). Histórico: [`docs/CHANGELOG.md`](docs/CHANGELOG.md).

## O que já está pronto (v0.1 → v0.4)

### Cadastros
- **Empresa** (1 por instância) e **oficinas** (N, com horário e dias de funcionamento).
- **Funcionários** (mecânicos, atendentes…) e **equipamentos** agendáveis (boxes, elevadores, scanner), com cor na agenda.
- **Clientes** com **vários veículos**; busca por nome, CPF/CNPJ, telefone ou **placa**; remoção = inativação (histórico preservado).
- **Veículos** com placa única por empresa (antiga e Mercosul), km, chassi, Renavam; vínculo opcional com o catálogo.
- **Catálogo de marcas/modelos/anos** (2006 em diante) importado da FIPE via `scripts/importar_fipe.py` (retomável, cron); veículo fora do catálogo sempre permitido.
- **Peças** (código, part number, código de barras, fabricante, aplicação, custo/venda, validade, mínimo) e **mão de obra** (valor/hora + tempo previsto, valor fixo opcional). Busca por palavras ("pastilha onix").
- Carga de demonstração: `scripts/seed_demo.py` (208 peças, 48 serviços, prefixo `DEMO-`, `--remover` limpa).

### Operação
- **Agenda por oficina**: uma coluna por mecânico e por equipamento; conflito de recurso bloqueado no servidor; linha da hora atual; status (agendado, confirmado, chegou, em atendimento, concluído, faltou, cancelado); guincho com destaque; abre orçamento direto do agendamento.
- **Orçamento → Pedido**: nasce orçamento (nº próprio); itens de serviço e de peça **autorizados item a item**; aprovação registra quem autorizou e gera **nº de pedido**; mecânico registra a **execução** de cada serviço (relato); só conclui com tudo o que foi autorizado executado; totais recalculados no servidor; desconto; impressão.
- **Leitor de placa pela câmera** (tablet): OCR local, candidatas corrigíveis, painel do veículo com pedidos em andamento, **histórico de atendimentos** (data, km, serviços, peças, valor) e botão de novo orçamento.
- **Fechamento com pagamento**: dinheiro (troco), PIX (QR Code BR Code demonstrativo + copia e cola), débito, crédito (1 a 6x), boleto (exige CPF/CNPJ e endereço; fica em aberto com vencimento); pagamento dividido; entrega só com o total coberto. Tabela `PAGAMENTO` pronta para o financeiro.
- **Painel** com agenda do dia, orçamentos abertos, pedidos em execução e prontos para entrega.

### Inteligência artificial (portada do WebTriagem)
- Botões ✍️ (escrever à mão), 🎤 (ditar — navegador no Chrome/Edge/Safari; whisper no servidor nos demais) e ✨ (corrigir/formatar com aceite) em queixa, diagnóstico, observações, serviço executado, descrição de serviço e aplicação de peça.
- **Pesquisa de problema** (sintoma + veículo + km → causas prováveis, como verificar, peças) e **pesquisa de código de peça** (nome técnico, variantes, fabricantes, referências para confirmar).
- Regras do assistente em `api/contexto_oficina.md`, editável sem reiniciar.

### Site de vendas (aofficina.com.br)
- Página premium (marinho/verde-água): herói com logo, seção por módulo com a dor que resolve, telas reais, IA, financeiro/tributário (em integração), licença sem preço ("sob consulta"), FAQ, formulário que abre o WhatsApp, política de privacidade (LGPD). Links "Entrar no sistema".

## Projetado (roadmap)

| Prioridade | Item | Observações |
|---|---|---|
| 1 | **Usuários** — tela para cadastrar login/senha/nível da equipe (ligado ao funcionário) | hoje só o admin, criado por script |
| 1 | **Orçamento/OS em PDF** com logo da empresa e **envio pelo WhatsApp** (Evolution API) | impressão já existe pelo navegador |
| 2 | **Estoque por lote** (entrada de compra, FIFO, validade/perda, mínimo com alerta) e **baixa automática** das peças na conclusão do pedido | tabela `PECA` já tem `TEM_VALIDADE` e `ESTOQUE_MIN` |
| 2 | **Fila de atendimento** (ordem de chegada, prioridade de guincho, próximo veículo quando um box libera) | base do enunciado da Fatec |
| 3 | **WebFinanceiro**: contas a receber (a partir de `PAGAMENTO`), contas a pagar, boletos registrados com baixa, PIX com integração bancária, conciliação, caixa diário, fluxo −12/+12 | clonar do homecare |
| 3 | **WebTributário**: NFS-e padrão nacional e NF-e de peças a partir do pedido; campos da reforma (IBS/CBS); certificado A1 em cofre; relatórios para a contabilidade | GISS só serve para Rio Claro |
| 4 | **Robô de atendimento inicial** no WhatsApp do site (qualificação de leads) | |
| 4 | **Relatórios**: produtividade por mecânico, ocupação de elevadores, ticket médio, margem por pedido, retornos | |
| 4 | **Diagnóstico por árvore de componentes** (sistema → subconjunto → peça, estado OK/defeito) | enunciado da Fatec |
| 5 | **Instalador para servidor do cliente** (migração de instância), atualizador, backup remoto | |
| 5 | Importação de cadastros de outros sistemas (planilhas), multi-idioma do assistente, app do cliente (acompanhar o carro) | |
| — | Ditado via whisper no servidor para navegadores sem voz nativa (Brave) | opcional; instalação travou em `tokenizers` no Python 3.8 |
| — | Fotos próprias de carros no site (`site/img/carro-1.jpg`, `carro-2.jpg`) | hoje hotlink Unsplash com fallback |

## Convenções de desenvolvimento

- Toda rota nasce autenticada; autorização por nível no backend; SQL parametrizado; segredos só no `.env`.
- Migrations `vNNN_*.sql` idempotentes, aplicadas com `db/rodar_migration.py` (dry-run → `--commit`).
- Scripts com dry-run por padrão e `--commit` para valer.
- Entregas em `.zip` sem pasta raiz (`unzip -o` em `/home/deploy/aofficina`), `import main` antes de reiniciar, um commit por versão em uma linha.

## Licença

Software proprietário — © IA Process Automation. Todos os direitos reservados.
