# aOfficina — leia primeiro

Sistema de gestão para redes de oficinas mecânicas. Produto da **IA Process Automation** (Fernando Manesco).
Modelo: **venda de licença** (não aluguel). Uma **instância por cliente** (banco MySQL próprio), hospedada
primeiro no T140, migrável para o servidor do cliente.

## Stack (igual ao ecossistema homecare, trocando o banco)
- Backend: FastAPI + Uvicorn (porta **8300**), venv próprio em `api/.venv`, serviço systemd `aofficina-api`.
- Banco: **MySQL 8** (utf8mb4), driver PyMySQL. Dinheiro em **centavos (BIGINT)**. SQL sempre parametrizado (`%s`).
- Frontend: HTML estático + `js/api.js` + `js/auth.js` + `js/layout.js`, Bootstrap 5.3 **servido localmente** (`web/vendor/`,
  sem CDN — o sistema roda sem internet no servidor do cliente).
- Deploy: Nginx (`deploy/nginx-aofficina.conf`), certbot. Domínios: `aofficina.com.br` (site), `app.` (app), `api.` (API).

## Pastas
```
/home/deploy/aofficina/
├── api/            main.py, config.py, db.py, utils/auth.py, routers/*.py, .env (NUNCA no git)
├── db/migrations/  vNNN_*.sql  +  rodar_migration.py (dry-run padrão, --commit aplica)
├── scripts/        criar_instancia.py, importar_fipe.py, backup_mysql.sh
├── deploy/         aofficina-api.service, nginx-aofficina.conf
├── web/            app (index.html = login, pages/, js/, css/, img/, vendor/)
├── site/           site de venda (aofficina.com.br)
└── docs/
```

## Regras herdadas (não negociáveis)
1. Toda rota nasce autenticada (middleware JWT em `main.py`); pública só em `config.ROTAS_PUBLICAS` com `# PUBLICA: motivo`.
2. Autorização por nível no backend (`requer_nivel(n)`); frontend não protege nada.
3. Senha só bcrypt. Segredo ausente no `.env` = serviço não sobe. Nada de segredo em código/git/chat.
4. Login com rate limit (10/min) e `SECURITY_LOG`.
5. Migrations idempotentes; dry-run antes de `--commit`; backup antes de migrar produção.
6. Routers não fazem commit/rollback (o `get_db_dep` faz). Exceção única documentada: log de falha de login.

## Níveis de usuário (USUARIO.NIVEL)
| Nível | Papel | Pode |
|---|---|---|
| 0 | Dono / admin | tudo, inclusive empresa e usuários |
| 1 | Gerente | cadastros, serviços, oficinas/recursos, pedidos, financeiro |
| 2 | Atendente / recepção | clientes, veículos, peças, agenda, abrir/aprovar pedidos |
| 3 | Mecânico | agenda, pedidos (itens e execução), consultas |
| 4 | Financeiro | contas, caixa (Fase 4) |

## Modelo de dados (v001 + v002)
- `EMPRESA` (1 por instância) → `OFICINA` (N) → `EQUIPAMENTO` (boxes/elevadores) e `FUNCIONARIO` (mecânicos etc.).
- `USUARIO` (login) opcionalmente ligado a `FUNCIONARIO` e restrito a uma `OFICINA`.
- `CLIENTE` → `VEICULO` (N por cliente; placa única por empresa) → opcional `CAT_MODELO` (catálogo FIPE: `CAT_MARCA`/`CAT_MODELO`/`CAT_ANO`, anos ≥ 2006).
- `AGENDA` por oficina, com `FUNCIONARIO_ID` e/ou `EQUIPAMENTO_ID`; conflito de recurso é bloqueado no backend.
- `PECA` (cadastro; estoque por lote na v003) e `SERVICO` (mão de obra: valor/hora + tempo previsto; opcional valor fixo).
- `PEDIDO`: nasce `ORCAMENTO` (NUMERO_ORCAMENTO); `POST /pedidos/{id}/aprovar` vira `PEDIDO` (NUMERO_PEDIDO).
  Itens: `PEDIDO_SERVICO` (com `EXECUTADO`/`DESCRICAO_EXECUTADO` do mecânico) e `PEDIDO_PECA`. Totais recalculados no servidor.
  Só conclui quando todos os serviços autorizados estão executados.

## Roadmap
| Fase | Conteúdo | Estado |
|---|---|---|
| 0 | Infra no T140 (MySQL, venv, systemd, Nginx, DNS, certbot) | **v1 — instalar** |
| 1 | Auth, empresa/oficinas/recursos, clientes+veículos, catálogo FIPE, agenda (API) | **v1 — pronto (API); telas: login, painel, clientes** |
| 2 | Telas: agenda, peças, mão de obra, orçamento/pedido; diagnóstico por áudio/escrita (modelo WebTriagem); assistente DeepSeek (problemas, códigos de peça, correção de textos) | próxima |
| 3 | Estoque por lote (FIFO, validade, perda, mínimo), baixa no fechamento do pedido | |
| 4 | Financeiro: contas a receber/pagar, pagamentos (PIX/cartão/dinheiro), boletos (clonar do homecare) | |
| 5 | NFS-e (padrão nacional; GISS só Rio Claro), recibo/OS em PDF | |
| 6 | Site de venda completo, instalador para servidor do cliente, atualizador | |

## FIPE
Não há API oficial. Usamos `fipe.parallelum.com.br/api/v2` (projeto deividfortuna/fipe): 500 req/dia sem token,
1.000 com token grátis (`FIPE_TOKEN`). `scripts/importar_fipe.py` é retomável e só grava catálogo (sem preço).
Veículo fora do catálogo é sempre permitido (marca/modelo digitados).
