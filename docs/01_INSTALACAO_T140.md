# Instalação da instância no T140 (v1)

Etiquetas: `[ Windows PowerShell ]` = seu PC · `[ SERVIDOR ]` = T140 (deploy@201.62.125.150).
Um bloco por vez. Todos os passos gravam em disco (nada só em memória).

## 1. MySQL 8 + utilitários
```bash
# [ SERVIDOR ]
sudo apt update && sudo apt install -y mysql-server python3-venv unzip
sudo systemctl enable --now mysql
sudo mysql -e "SELECT VERSION();"
ss -ltn | grep 3306          # deve mostrar 127.0.0.1:3306 (não exposto)
ss -ltn | grep 8300 || echo "porta 8300 livre"
```

## 2. Pasta do projeto e arquivos
```bash
# [ SERVIDOR ]
mkdir -p /home/deploy/aofficina/logs /home/deploy/aofficina/backups
```
```powershell
# [ Windows PowerShell ]
cd C:\Users\ferna\Downloads
scp aofficina_v1.zip deploy@201.62.125.150:aofficina/
```
```bash
# [ SERVIDOR ]
cd /home/deploy/aofficina && unzip -o aofficina_v1.zip && ls
```

## 3. `.env` + banco e usuário MySQL (senhas geradas, nunca digitadas)
```bash
# [ SERVIDOR ]
cd /home/deploy/aofficina/api
cp -n .env.exemplo .env
SENHA_DB=$(openssl rand -hex 16); SECRET=$(openssl rand -hex 32)
sed -i "s|^DB_PASSWORD=.*|DB_PASSWORD=$SENHA_DB|; s|^SECRET_KEY=.*|SECRET_KEY=$SECRET|; s|^INSTANCIA=.*|INSTANCIA=demo|" .env
chmod 600 .env
sudo mysql -e "CREATE DATABASE IF NOT EXISTS aofficina CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci; CREATE USER IF NOT EXISTS 'aofficina'@'localhost' IDENTIFIED BY '$SENHA_DB'; CREATE USER IF NOT EXISTS 'aofficina'@'127.0.0.1' IDENTIFIED BY '$SENHA_DB'; ALTER USER 'aofficina'@'localhost' IDENTIFIED BY '$SENHA_DB'; ALTER USER 'aofficina'@'127.0.0.1' IDENTIFIED BY '$SENHA_DB'; GRANT ALL ON aofficina.* TO 'aofficina'@'localhost'; GRANT ALL ON aofficina.* TO 'aofficina'@'127.0.0.1'; FLUSH PRIVILEGES;"
grep -c "DB_PASSWORD=$SENHA_DB" .env     # deve dar 1
```

## 4. venv e dependências
```bash
# [ SERVIDOR ]
cd /home/deploy/aofficina/api
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt
.venv/bin/python -c "import main"        # deve mostrar "Rotas registradas: 58"
```

## 5. Migrations e primeira empresa/admin
```bash
# [ SERVIDOR ]
cd /home/deploy/aofficina/api
.venv/bin/python ../db/rodar_migration.py
.venv/bin/python ../db/rodar_migration.py --commit
```
```bash
# [ SERVIDOR ]  (pede a senha do admin — bloco sozinho)
cd /home/deploy/aofficina/api
.venv/bin/python ../scripts/criar_instancia.py --commit
```

## 6. Serviço systemd
```bash
# [ SERVIDOR ]
sudo cp /home/deploy/aofficina/deploy/aofficina-api.service /etc/systemd/system/aofficina-api.service
sudo systemctl daemon-reload
sudo systemctl enable --now aofficina-api
sleep 2; curl -s http://127.0.0.1:8300/health; echo
sudo journalctl -u aofficina-api -n 20 --no-pager
```

## 7. DNS (registro.br) — antes do Nginx/certbot
No painel do registro.br, zona `aofficina.com.br`, criar registros **A** apontando para `201.62.125.150`:
`@`, `www`, `app`, `api`. Conferir propagação:
```bash
# [ SERVIDOR ]
for h in aofficina.com.br www.aofficina.com.br app.aofficina.com.br api.aofficina.com.br; do echo -n "$h -> "; dig +short $h; done
```

## 8. Nginx + HTTPS
```bash
# [ SERVIDOR ]
sudo cp /home/deploy/aofficina/deploy/nginx-aofficina.conf /etc/nginx/sites-available/aofficina
sudo ln -sf /etc/nginx/sites-available/aofficina /etc/nginx/sites-enabled/aofficina
sudo nginx -t && sudo systemctl reload nginx
curl -s -H "Host: api.aofficina.com.br" http://127.0.0.1/health; echo
```
```bash
# [ SERVIDOR ]  (interativo — bloco sozinho; só depois do DNS propagado)
sudo certbot --nginx -d aofficina.com.br -d www.aofficina.com.br -d app.aofficina.com.br -d api.aofficina.com.br
```
Teste: `https://app.aofficina.com.br` → login com o admin criado no passo 5.

## 9. Catálogo FIPE (carros, anos ≥ 2006) — retomável, 450 req por execução
```bash
# [ SERVIDOR ]
cd /home/deploy/aofficina/api
.venv/bin/python ../scripts/importar_fipe.py --tipo carros
.venv/bin/python ../scripts/importar_fipe.py --tipo carros --commit
```
Agendar diário até concluir (e o backup):
```bash
# [ SERVIDOR ]
chmod +x /home/deploy/aofficina/scripts/backup_mysql.sh
(crontab -l 2>/dev/null; echo "20 4 * * * cd /home/deploy/aofficina/api && .venv/bin/python -u ../scripts/importar_fipe.py --tipo carros --commit --max-req 950 >> /home/deploy/aofficina/logs/fipe.log 2>&1"; echo "15 3 * * * /home/deploy/aofficina/scripts/backup_mysql.sh >> /home/deploy/aofficina/logs/backup.log 2>&1") | crontab -
crontab -l
```

## 10. Git (repositório FernandoManesco/AOFFICINA.COM.BR — criar vazio e privado no GitHub antes)
```bash
# [ SERVIDOR ]
cd /home/deploy/aofficina
git init -b main
git add -A
git commit -m "aOfficina v0.1: API, banco MySQL, frontend base, deploy"
git remote add origin git@github.com:FernandoManesco/AOFFICINA.COM.BR.git
git push -u origin main
```

## 11. Assistente de IA (v3) — chaves
As chaves do DeepSeek e do MyScript já existem no `.env` do nfe-servico; copie os valores (sem passar pelo chat):
```bash
# [ SERVIDOR ]
cd /home/deploy/aofficina/api
for k in DEEPSEEK_API_KEY MYSCRIPT_APP_KEY MYSCRIPT_HMAC_KEY; do v=$(grep "^$k=" /home/deploy/var/www/sistema-gestao/nfe-servico/.env | cut -d= -f2-); [ -n "$v" ] && sed -i "s|^$k=.*|$k=$v|" .env && echo "$k ok" || echo "$k nao encontrado no nfe-servico"; done
sudo systemctl restart aofficina-api
```
Ditado no servidor (opcional; só para navegadores sem reconhecimento de voz próprio — o modelo whisper já baixado pelo WebTriagem é reaproveitado):
```bash
# [ SERVIDOR ]
cd /home/deploy/aofficina/api && .venv/bin/pip install -r requirements-ia.txt && sudo systemctl restart aofficina-api
```
Conferir: `curl -s -H "Authorization: Bearer TOKEN" http://127.0.0.1:8300/ia/status` (ou abrir um pedido e clicar em ✨).

## 12. Leitor de placa pela câmera (v3.4)
```bash
# [ SERVIDOR ]
sudo apt install -y tesseract-ocr
cd /home/deploy/aofficina/api && .venv/bin/pip install pytesseract Pillow && .venv/bin/python -c "import pytesseract; print(pytesseract.get_tesseract_version())"
sudo systemctl restart aofficina-api
```
No tablet, a câmera só abre em HTTPS (já é o caso em app.aofficina.com.br) e após permitir no navegador.

## Operação
| Ação | Comando `[ SERVIDOR ]` |
|---|---|
| Reiniciar API | `sudo systemctl restart aofficina-api` |
| Logs | `sudo journalctl -u aofficina-api -n 50 --no-pager` |
| Validar antes de reiniciar | `cd /home/deploy/aofficina/api && .venv/bin/python -c "import main"` |
| Consulta rápida | `cd /home/deploy/aofficina/api && set -a && . ./.env && set +a && mysql -h 127.0.0.1 -u $DB_USER -p"$DB_PASSWORD" $DB_NAME -e "SELECT COUNT(*) FROM CLIENTE"` |
| Backup manual | `/home/deploy/aofficina/scripts/backup_mysql.sh` |
