#!/usr/bin/env python3
"""Carga de DEMONSTRAÇÃO: ~150 peças e ~45 serviços de mão de obra típicos de oficina.

Preços são faixas de mercado aproximadas (out/2026) e os part numbers são ILUSTRATIVOS — servem para mostrar o
sistema, não para comprar peça. Rodar na pasta api/:
    python3 ../scripts/seed_demo.py            # dry-run: mostra o que faria
    python3 ../scripts/seed_demo.py --commit   # grava (idempotente: pula códigos já existentes)
    python3 ../scripts/seed_demo.py --commit --remover   # remove só o que este script criou (prefixo DEMO-)
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "api"))
import db  # noqa: E402

R = lambda v: int(round(v * 100))  # reais -> centavos

# ---------------------------------------------------------------- modelos de referência (aplicação)
CARROS = [
    ("Gol G5/G6 1.0/1.6 2009-2016", "VW"), ("Onix 1.0/1.4 2013-2019", "GM"), ("HB20 1.0/1.6 2013-2019", "Hyundai"),
    ("Corolla 1.8/2.0 2015-2019", "Toyota"), ("Civic 2.0 2017-2021", "Honda"), ("Hilux 2.8 Diesel 2016-2023", "Toyota"),
    ("Compass 2.0 Flex/Diesel 2017-2021", "Jeep"), ("Argo/Cronos 1.3/1.8 2018-2023", "Fiat"), ("Kicks 1.6 2017-2022", "Nissan"),
    ("Renegade 1.8 2016-2021", "Jeep"), ("Polo/Virtus 1.0 TSI 2018-2023", "VW"), ("Creta 1.6/2.0 2017-2021", "Hyundai"),
]

PECAS = []  # (codigo, nome, fabricante, part_number, aplicacao, unidade, custo, venda, validade)

def add(cod, nome, fab, pn, apl, un, custo, venda, val=0):
    PECAS.append((f"DEMO-{cod}", nome, fab, pn, apl, un, R(custo), R(venda), val))

# filtros (4 por modelo)
for i, (apl, _) in enumerate(CARROS, 1):
    add(f"FO{i:02d}", f"Filtro de óleo {apl.split()[0]}", "Mann-Filter", f"W 712/{70+i}", apl, "UN", 18 + i, 42 + i * 1.5)
    add(f"FA{i:02d}", f"Filtro de ar do motor {apl.split()[0]}", "Fram", f"CA{10000+i*37}", apl, "UN", 28 + i, 69 + i * 2)
    add(f"FC{i:02d}", f"Filtro de combustível {apl.split()[0]}", "Bosch", f"0 986 450 {100+i}", apl, "UN", 24 + i, 59 + i * 2)
    add(f"FB{i:02d}", f"Filtro de cabine (ar-condicionado) {apl.split()[0]}", "Wega", f"AKX-{1500+i*3}", apl, "UN", 22 + i, 55 + i * 1.5)
# freios
for i, (apl, _) in enumerate(CARROS, 1):
    add(f"PD{i:02d}", f"Pastilha de freio dianteira {apl.split()[0]}", "Cobreq", f"N-{1200+i*7}", apl, "JG", 70 + i * 6, 165 + i * 12)
    add(f"DD{i:02d}", f"Disco de freio dianteiro ventilado {apl.split()[0]}", "Fremax", f"BD{5000+i*11}", apl, "PAR", 160 + i * 12, 360 + i * 25)
for i, (apl, _) in enumerate(CARROS[:6], 1):
    add(f"PT{i:02d}", f"Pastilha de freio traseira {apl.split()[0]}", "Fras-le", f"PD/{900+i*5}", apl, "JG", 60 + i * 5, 145 + i * 10)
# suspensão
for i, (apl, _) in enumerate(CARROS, 1):
    add(f"AD{i:02d}", f"Amortecedor dianteiro {apl.split()[0]}", "Cofap", f"GP{32000+i*13}", apl, "UN", 180 + i * 15, 390 + i * 30)
    add(f"AT{i:02d}", f"Amortecedor traseiro {apl.split()[0]}", "Monroe", f"G{7000+i*9}", apl, "UN", 150 + i * 12, 330 + i * 25)
for i, (apl, _) in enumerate(CARROS[:8], 1):
    add(f"KB{i:02d}", f"Kit batente e coifa amortecedor dianteiro {apl.split()[0]}", "Axios", f"011.{3000+i}", apl, "KIT", 45 + i * 3, 110 + i * 6)
    add(f"BI{i:02d}", f"Bieleta da barra estabilizadora {apl.split()[0]}", "Nakata", f"N 99{100+i}", apl, "UN", 28 + i * 2, 75 + i * 4)
    add(f"PV{i:02d}", f"Pivô de suspensão {apl.split()[0]}", "Viemar", f"50{300+i}", apl, "UN", 55 + i * 3, 130 + i * 6)
# motor / ignição
for i, (apl, _) in enumerate(CARROS[:10], 1):
    add(f"VL{i:02d}", f"Jogo de velas de ignição {apl.split()[0]}", "NGK", f"BKR6E-{i}", apl, "JG", 60 + i * 4, 140 + i * 8)
    add(f"CD{i:02d}", f"Correia dentada {apl.split()[0]}", "Gates", f"5{500+i*3}XS", apl, "UN", 70 + i * 5, 160 + i * 10)
    add(f"TE{i:02d}", f"Tensor da correia dentada {apl.split()[0]}", "SKF", f"VKM 1{1000+i*7}", apl, "UN", 120 + i * 8, 260 + i * 15)
for i, (apl, _) in enumerate(CARROS[:6], 1):
    add(f"BA{i:02d}", f"Bobina de ignição {apl.split()[0]}", "Bosch", f"F 000 ZS0 {200+i}", apl, "UN", 140 + i * 10, 310 + i * 20)
    add(f"BG{i:02d}", f"Bomba d'água {apl.split()[0]}", "Urba", f"UB0{700+i}", apl, "UN", 130 + i * 9, 290 + i * 18)
# óleos e fluidos (com validade)
add("OL01", "Óleo motor 5W30 sintético API SP", "Mobil", "Super 3000 5W30", "Motores flex modernos", "L", 34, 59.9, 1)
add("OL02", "Óleo motor 5W40 sintético", "Castrol", "Magnatec 5W40", "Motores flex/gasolina", "L", 36, 64.9, 1)
add("OL03", "Óleo motor 0W20 sintético", "Motul", "8100 Eco-lite 0W20", "Toyota/Honda modernos", "L", 48, 84.9, 1)
add("OL04", "Óleo motor 15W40 Diesel CI-4", "Petronas", "Urania 15W40", "Hilux/Diesel leves", "L", 22, 39.9, 1)
add("OL05", "Óleo de câmbio ATF Dexron VI", "Mobil", "ATF D/M", "Câmbios automáticos", "L", 42, 79.9, 1)
add("OL06", "Óleo de câmbio manual 75W80 GL-4", "Castrol", "Syntrans 75W80", "Câmbios manuais", "L", 45, 84.9, 1)
add("FL01", "Fluido de freio DOT 4", "Bosch", "DOT4 500ml", "Todos", "UN", 14, 29.9, 1)
add("FL02", "Aditivo radiador concentrado rosa (OAT)", "Paraflu", "Paraflu Concentrado 1L", "Todos", "L", 19, 39.9, 1)
add("FL03", "Água desmineralizada", "Radnaq", "5L", "Todos", "UN", 9, 19.9, 1)
add("FL04", "Fluido de direção hidráulica", "Tutela", "GI/A", "Direção hidráulica", "L", 24, 49.9, 1)
add("FL05", "Limpa para-brisa concentrado", "Würth", "500ml", "Todos", "UN", 8, 19.9, 1)
add("FL06", "Graxa multiuso lítio", "Bardahl", "500g", "Todos", "UN", 18, 34.9, 1)
# elétrica
for i, (apl, _) in enumerate(CARROS[:8], 1):
    add(f"BT{i:02d}", f"Bateria {['60','60','60','60','60','75','70','60'][i-1]}Ah {apl.split()[0]}", "Moura", f"M{['60','60','60','60','60','75','70','60'][i-1]}GD", apl, "UN", 380 + i * 15, 690 + i * 25, 1)
add("LP01", "Lâmpada H4 12V 60/55W", "Philips", "12342", "Farol principal", "UN", 12, 29.9)
add("LP02", "Lâmpada H7 12V 55W", "Osram", "64210", "Farol principal", "UN", 16, 39.9)
add("LP03", "Lâmpada H11 12V 55W", "Philips", "12362", "Farol de neblina/baixo", "UN", 22, 49.9)
add("LP04", "Lâmpada 1 polo 21W (seta/ré)", "Osram", "7506", "Sinalização", "UN", 3, 9.9)
add("LP05", "Lâmpada 2 polos 21/5W (lanterna/freio)", "Osram", "7528", "Sinalização", "UN", 4, 11.9)
add("PP01", "Palheta limpador 22''", "Bosch", "Aerotwin 22", "Para-brisa", "UN", 32, 69.9)
add("PP02", "Palheta limpador 18''", "Bosch", "Aerotwin 18", "Para-brisa", "UN", 28, 59.9)
add("PP03", "Palheta limpador traseira 12''", "Dyna", "DY12", "Vidro traseiro", "UN", 18, 39.9)
add("FS01", "Fusível lâmina 10A (cartela 10)", "Tridon", "MINI10", "Todos", "UN", 6, 14.9)
add("FS02", "Relé auxiliar 12V 40A", "DNI", "0101", "Todos", "UN", 14, 34.9)
# diversos
add("EX01", "Catalisador universal", "Fiesta", "FT-001", "Universal", "UN", 420, 890)
add("EX02", "Flexível do escapamento", "Mastra", "MF-50", "Universal", "UN", 45, 99)
add("CV01", "Cabo de vela jogo", "NGK", "SC-V06", "Motores 1.0/1.6 flex", "JG", 65, 139)
add("JT01", "Junta do cabeçote", "Taranto", "JT-200", "Motores 1.0/1.6 flex", "UN", 85, 189)
add("RT01", "Rolamento de roda dianteiro", "SKF", "VKBA 3660", "Hatches e sedãs compactos", "UN", 110, 239)
add("HM01", "Homocinética lado roda", "Axios", "012.1100", "Hatches e sedãs compactos", "UN", 160, 349)
add("CX01", "Coxim do motor", "Sampel", "SP-3300", "Hatches e sedãs compactos", "UN", 95, 209)
add("TM01", "Válvula termostática", "MTE-Thomson", "VT-260", "Motores flex", "UN", 48, 109)
add("SM01", "Sensor de oxigênio (sonda lambda)", "Bosch", "0 258 006 537", "Motores flex", "UN", 180, 389)
add("MF01", "Mangueira do radiador superior", "Gates", "MG-4411", "Hatches e sedãs compactos", "UN", 38, 89)

# ---------------------------------------------------------------- serviços de mão de obra
SERVICOS = [  # (codigo, nome, categoria, valor_hora, tempo_min, valor_fixo ou None)
    ("DEMO-REV01", "Revisão básica (óleo + filtros + checklist 30 itens)", "Revisão", 150, 60, None),
    ("DEMO-REV02", "Revisão completa (fluidos, freios, suspensão, checklist 60 itens)", "Revisão", 150, 150, None),
    ("DEMO-OLE01", "Troca de óleo e filtro de óleo", "Revisão", 150, 30, None),
    ("DEMO-FIL01", "Troca de filtro de ar / combustível / cabine (cada)", "Revisão", 150, 15, None),
    ("DEMO-FRE01", "Troca de pastilhas dianteiras", "Freios", 150, 60, None),
    ("DEMO-FRE02", "Troca de pastilhas traseiras", "Freios", 150, 60, None),
    ("DEMO-FRE03", "Troca de discos e pastilhas dianteiras", "Freios", 150, 90, None),
    ("DEMO-FRE04", "Sangria e troca do fluido de freio", "Freios", 150, 45, None),
    ("DEMO-FRE05", "Regulagem de freio de estacionamento", "Freios", 150, 30, None),
    ("DEMO-SUS01", "Troca de amortecedores dianteiros (par)", "Suspensão", 150, 120, None),
    ("DEMO-SUS02", "Troca de amortecedores traseiros (par)", "Suspensão", 150, 90, None),
    ("DEMO-SUS03", "Troca de bieletas (par)", "Suspensão", 150, 40, None),
    ("DEMO-SUS04", "Troca de pivôs (par)", "Suspensão", 150, 90, None),
    ("DEMO-SUS05", "Troca de buchas da bandeja (par)", "Suspensão", 150, 120, None),
    ("DEMO-ALI01", "Alinhamento 3D", "Suspensão", 120, 40, 120),
    ("DEMO-ALI02", "Balanceamento (4 rodas)", "Suspensão", 120, 30, 80),
    ("DEMO-ALI03", "Alinhamento + balanceamento (4 rodas)", "Suspensão", 120, 60, 180),
    ("DEMO-ALI04", "Cambagem / cáster (por eixo)", "Suspensão", 150, 45, None),
    ("DEMO-MOT01", "Troca de correia dentada + tensor", "Motor", 160, 180, None),
    ("DEMO-MOT02", "Troca de correia dentada + tensor + bomba d'água", "Motor", 160, 240, None),
    ("DEMO-MOT03", "Troca de velas", "Motor", 150, 30, None),
    ("DEMO-MOT04", "Troca de velas e cabos/bobinas", "Motor", 150, 60, None),
    ("DEMO-MOT05", "Troca de bomba d'água", "Motor", 160, 150, None),
    ("DEMO-MOT06", "Troca de válvula termostática", "Motor", 150, 60, None),
    ("DEMO-MOT07", "Limpeza de bicos injetores (ultrassom, 4 bicos)", "Injeção", 150, 120, 350),
    ("DEMO-MOT08", "Limpeza do corpo de borboleta", "Injeção", 150, 45, None),
    ("DEMO-MOT09", "Troca de junta do cabeçote (motor 1.0/1.6)", "Motor", 160, 600, None),
    ("DEMO-MOT10", "Troca de coxim do motor (unidade)", "Motor", 150, 60, None),
    ("DEMO-ARR01", "Troca do fluido de arrefecimento com limpeza", "Arrefecimento", 150, 60, None),
    ("DEMO-ARR02", "Troca de mangueira do radiador", "Arrefecimento", 150, 45, None),
    ("DEMO-ARR03", "Troca do radiador", "Arrefecimento", 150, 150, None),
    ("DEMO-ELE01", "Diagnóstico eletrônico com scanner", "Elétrica", 180, 60, 180),
    ("DEMO-ELE02", "Troca de bateria com teste do sistema de carga", "Elétrica", 150, 20, None),
    ("DEMO-ELE03", "Troca de lâmpada (unidade)", "Elétrica", 150, 10, None),
    ("DEMO-ELE04", "Troca de alternador", "Elétrica", 160, 120, None),
    ("DEMO-ELE05", "Troca de motor de partida", "Elétrica", 160, 120, None),
    ("DEMO-ELE06", "Troca de sonda lambda", "Injeção", 150, 45, None),
    ("DEMO-ARC01", "Higienização do ar-condicionado", "Ar-condicionado", 150, 45, 150),
    ("DEMO-ARC02", "Recarga de gás R134a com teste de vazamento", "Ar-condicionado", 150, 60, 280),
    ("DEMO-ARC03", "Troca do compressor do ar-condicionado", "Ar-condicionado", 160, 180, None),
    ("DEMO-TRA01", "Troca de óleo do câmbio manual", "Transmissão", 150, 45, None),
    ("DEMO-TRA02", "Troca de óleo do câmbio automático (com filtro)", "Transmissão", 160, 120, None),
    ("DEMO-TRA03", "Troca de homocinética", "Transmissão", 160, 90, None),
    ("DEMO-TRA04", "Troca de kit de embreagem (motor 1.0/1.6)", "Transmissão", 160, 300, None),
    ("DEMO-ESC01", "Troca de flexível do escapamento", "Escapamento", 150, 45, None),
    ("DEMO-ESC02", "Troca de catalisador", "Escapamento", 150, 90, None),
    ("DEMO-GER01", "Hora técnica (diagnóstico / serviço avulso)", "Geral", 150, 60, None),
    ("DEMO-GER02", "Lavagem técnica do motor", "Geral", 120, 45, 120),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--commit", action="store_true")
    ap.add_argument("--remover", action="store_true", help="remove peças/serviços DEMO- (só com --commit)")
    args = ap.parse_args()
    with db.abrir() as con:
        emp = db.um(con, "SELECT ID FROM EMPRESA ORDER BY ID LIMIT 1")
        if not emp:
            print("Sem EMPRESA — rode criar_instancia.py antes."); return
        eid = emp["ID"]
        if args.remover:
            np_ = db.um(con, "SELECT COUNT(*) N FROM PECA WHERE EMPRESA_ID=%s AND CODIGO LIKE 'DEMO-%%'", [eid])["N"]
            ns = db.um(con, "SELECT COUNT(*) N FROM SERVICO WHERE EMPRESA_ID=%s AND CODIGO LIKE 'DEMO-%%'", [eid])["N"]
            print(f"{'REMOVENDO' if args.commit else 'DRY-RUN remover'} {np_} peças e {ns} serviços DEMO-")
            if args.commit:
                db.executar(con, "DELETE FROM PECA WHERE EMPRESA_ID=%s AND CODIGO LIKE 'DEMO-%%' AND ID NOT IN (SELECT DISTINCT PECA_ID FROM PEDIDO_PECA WHERE PECA_ID IS NOT NULL)", [eid])
                db.executar(con, "DELETE FROM SERVICO WHERE EMPRESA_ID=%s AND CODIGO LIKE 'DEMO-%%' AND ID NOT IN (SELECT DISTINCT SERVICO_ID FROM PEDIDO_SERVICO WHERE SERVICO_ID IS NOT NULL)", [eid])
                print("ok (itens já usados em pedidos foram mantidos)")
            return
        ja_p = {r["CODIGO"] for r in db.todos(con, "SELECT CODIGO FROM PECA WHERE EMPRESA_ID=%s", [eid])}
        ja_s = {r["CODIGO"] for r in db.todos(con, "SELECT CODIGO FROM SERVICO WHERE EMPRESA_ID=%s", [eid])}
        novas_p = [p for p in PECAS if p[0] not in ja_p]; novos_s = [s for s in SERVICOS if s[0] not in ja_s]
        print(f"Empresa {eid}: {len(PECAS)} peças no script ({len(novas_p)} novas), {len(SERVICOS)} serviços ({len(novos_s)} novos)")
        for p in novas_p[:5]:
            print("  ex.:", p[0], p[1], "-", p[2], f"R$ {p[7]/100:.2f}")
        if not args.commit:
            print("Dry-run. Para gravar: --commit"); return
        for cod, nome, fab, pn, apl, un, custo, venda, val in novas_p:
            db.executar(con, """INSERT INTO PECA (EMPRESA_ID, CODIGO, CODIGO_FABRICANTE, NOME, FABRICANTE, APLICACAO, UNIDADE,
                                PRECO_CUSTO_CENT, PRECO_VENDA_CENT, ESTOQUE_MIN, TEM_VALIDADE, ATIVO)
                                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,1)""",
                        [eid, cod, pn, nome, fab, apl, un, custo, venda, 2, val])
        for cod, nome, cat, vh, tempo, fixo in novos_s:
            db.executar(con, """INSERT INTO SERVICO (EMPRESA_ID, CODIGO, NOME, CATEGORIA, VALOR_HORA_CENT, TEMPO_PREVISTO_MIN, VALOR_FIXO_CENT, ATIVO)
                                VALUES (%s,%s,%s,%s,%s,%s,%s,1)""",
                        [eid, cod, nome, cat, R(vh), tempo, R(fixo) if fixo is not None else None])
        print(f"OK: {len(novas_p)} peças e {len(novos_s)} serviços gravados.")


if __name__ == "__main__":
    main()
