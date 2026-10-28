// aOfficina — impressão do orçamento / ordem de serviço.
// Monta um documento próprio (#impressao) a partir dos dados já carregados na tela e chama window.print().
// Uso: imprimirPedido(P, EMP, pagamentos)  — P = pedido com servicos/pecas; EMP = empresa; pagamentos = resumo (opcional)
(function () {
  const CSS = `
  #impressao { display: none; }
  @media print {
    @page { size: A4; margin: 14mm 14mm 18mm 14mm; }
    html, body { background: #fff !important; }
    body { display: block !important; min-height: 0 !important; }
    body > *:not(#impressao) { display: none !important; }
    #impressao { display: block; }
  }
  #impressao { font-family: "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; color: #23272e; font-size: 10.5pt; line-height: 1.38; position: relative; }
  #impressao * { box-sizing: border-box; }
  #impressao .marca-dagua { position: fixed; left: 50%; top: 50%; width: 120mm; transform: translate(-50%, -50%); opacity: .045; z-index: 0; pointer-events: none; }
  #impressao .doc { position: relative; z-index: 1; }
  #impressao .cab { display: flex; justify-content: space-between; align-items: flex-start; padding-bottom: 4mm; border-bottom: 2px solid #B87333; }
  #impressao .cab img { height: 13mm; }
  #impressao .cab .emp { text-align: right; font-size: 9pt; color: #555; }
  #impressao .cab .emp b { display: block; font-size: 11.5pt; color: #23272e; }
  #impressao .tit { display: flex; justify-content: space-between; align-items: flex-end; margin: 6mm 0 4mm; }
  #impressao .tit h1 { margin: 0; font-size: 19pt; font-weight: 700; letter-spacing: .2px; }
  #impressao .tit h1 small { display: block; font-size: 8.5pt; font-weight: 600; color: #B87333; letter-spacing: 1.6px; text-transform: uppercase; }
  #impressao .pill { display: inline-block; padding: 1.2mm 3.5mm; border-radius: 99px; font-size: 8pt; font-weight: 700; letter-spacing: .6px; text-transform: uppercase; border: 1.2px solid #B87333; color: #B87333; }
  #impressao .pill.ok { background: #B87333; color: #fff; }
  #impressao .datas { font-size: 8.5pt; color: #666; text-align: right; }
  #impressao .datas span { display: inline-block; margin-left: 4mm; }
  #impressao .datas b { color: #23272e; font-weight: 600; }
  #impressao .grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 4mm; }
  #impressao .box { border: 1px solid #dfe3e8; border-radius: 2.5mm; padding: 3mm 4mm; break-inside: avoid; background: rgba(255,255,255,.75); }
  #impressao .box .rot { font-size: 7.5pt; font-weight: 700; letter-spacing: 1.2px; text-transform: uppercase; color: #B87333; margin-bottom: 1.2mm; }
  #impressao .box .nome { font-size: 12pt; font-weight: 700; }
  #impressao .box .sub { font-size: 9pt; color: #555; }
  #impressao .placa { display: inline-block; font-family: "Consolas", "Courier New", monospace; font-weight: 700; font-size: 11pt; letter-spacing: 1.5px; border: 1.4px solid #23272e; border-radius: 1.5mm; padding: 0 2mm; margin-right: 2mm; }
  #impressao .txt { margin-top: 4mm; }
  #impressao .txt .box { padding: 2.5mm 4mm; }
  #impressao .txt p { margin: 0; white-space: pre-wrap; }
  #impressao h2 { font-size: 9pt; font-weight: 700; letter-spacing: 1.4px; text-transform: uppercase; color: #23272e; margin: 6mm 0 2mm; padding-bottom: 1.2mm; border-bottom: 1px solid #B87333; display: flex; justify-content: space-between; }
  #impressao h2 span { font-weight: 500; letter-spacing: 0; text-transform: none; color: #777; font-size: 8.5pt; }
  #impressao table { width: 100%; border-collapse: collapse; font-size: 9.5pt; }
  #impressao th { text-align: left; font-size: 7.5pt; letter-spacing: 1px; text-transform: uppercase; color: #777; font-weight: 600; padding: 1.5mm 2mm; border-bottom: 1px solid #dfe3e8; }
  #impressao td { padding: 2mm; border-bottom: 1px solid #eef0f3; vertical-align: top; }
  #impressao tr { break-inside: avoid; }
  #impressao tbody tr:nth-child(even) td { background: rgba(246,247,249,.8); }
  #impressao .r { text-align: right; white-space: nowrap; }
  #impressao .c { text-align: center; }
  #impressao .cod { font-family: "Consolas", "Courier New", monospace; font-size: 8.5pt; color: #888; margin-left: 1.5mm; }
  #impressao .feito { font-size: 9pt; color: #2e7d4f; margin-top: .8mm; }
  #impressao .feito::before { content: "✓ "; font-weight: 700; }
  #impressao .nao td { color: #999; text-decoration: line-through; }
  #impressao .nao td .tag { text-decoration: none; }
  #impressao .tag { display: inline-block; font-size: 7pt; font-weight: 700; letter-spacing: .6px; text-transform: uppercase; color: #a33; border: 1px solid #d9a0a0; border-radius: 1mm; padding: 0 1.2mm; margin-left: 1.5mm; vertical-align: middle; }
  #impressao .tot { display: flex; justify-content: flex-end; margin-top: 4mm; break-inside: avoid; }
  #impressao .tot table { width: 78mm; }
  #impressao .tot td { border: 0; padding: 1mm 2mm; }
  #impressao .tot .total td { border-top: 1.5px solid #23272e; font-size: 13pt; font-weight: 700; padding-top: 2mm; }
  #impressao .tot .total td.r { color: #B87333; }
  #impressao .gar { margin-top: 6mm; display: grid; grid-template-columns: 1fr 1fr; gap: 4mm; break-inside: avoid; }
  #impressao .gar .box { background: #fbf6f1; border-color: #e8d5c4; }
  #impressao .gar p { margin: 0; font-size: 8.8pt; color: #444; }
  #impressao .ass { display: grid; grid-template-columns: 1fr 1fr; gap: 14mm; margin-top: 16mm; break-inside: avoid; }
  #impressao .ass div { border-top: 1px solid #23272e; padding-top: 1.5mm; font-size: 8.5pt; color: #555; text-align: center; }
  #impressao .ass div b { display: block; color: #23272e; font-size: 9.5pt; }
  #impressao .rod { position: fixed; bottom: 0; left: 0; right: 0; display: flex; justify-content: space-between; align-items: center; font-size: 7.5pt; color: #888; border-top: 1px solid #e3e6ea; padding-top: 1.5mm; background: #fff; }
  #impressao .rod img { height: 6mm; vertical-align: middle; margin-right: 2mm; }
  #impressao .rod b { color: #B87333; font-weight: 700; }
  #impressao .fim { height: 10mm; }
  `;
  const FORMA_ROT = { DINHEIRO: 'Dinheiro', PIX: 'PIX', DEBITO: 'Cartão de débito', CREDITO: 'Cartão de crédito', BOLETO: 'Boleto' };
  const STATUS_ROT = { ABERTO: 'Orçamento aberto', ENVIADO: 'Enviado ao cliente', APROVADO: 'Aprovado', RECUSADO: 'Recusado', EM_EXECUCAO: 'Em execução',
    AGUARDANDO_PECA: 'Aguardando peça', CONCLUIDO: 'Concluído', ENTREGUE: 'Entregue', FATURADO: 'Faturado', CANCELADO: 'Cancelado' };
  const dt = (v) => v ? formatarDataHora(v) : '';
  const data = (v) => v ? new Date(v).toLocaleDateString('pt-BR') : '';

  function garantiaTexto(P) {
    // Texto padrão (CDC art. 26, II — 90 dias para serviços e produtos duráveis). Quando houver prazo por item no cadastro, ele prevalece.
    const base = P.ENTREGUE_EM || P.CONCLUIDO_EM;
    const ate = base ? new Date(new Date(base).getTime() + 90 * 86400000) : null;
    const km = P.KM_ENTRADA || P.KM_ATUAL;
    return { prazo: '90 dias' + (ate ? ` · válida até <b>${ate.toLocaleDateString('pt-BR')}</b>` : ' a partir da entrega') + (km ? ` ou <b>${(Number(km) + 5000).toLocaleString('pt-BR')} km</b>, o que ocorrer primeiro` : ''),
      cond: 'Cobre defeitos de execução dos serviços e defeitos de fabricação das peças fornecidas pela oficina, mediante apresentação deste documento. Não cobre desgaste natural, mau uso, intervenção de terceiros, peças fornecidas pelo cliente nem itens não autorizados. Peças substituídas ficam à disposição do cliente por 7 dias.' };
  }

  window.imprimirPedido = function (P, EMP, pg) {
    if (!document.getElementById('cssImpressao')) { const s = document.createElement('style'); s.id = 'cssImpressao'; s.textContent = CSS; document.head.appendChild(s); }
    let el = document.getElementById('impressao'); if (!el) { el = document.createElement('div'); el.id = 'impressao'; document.body.appendChild(el); }
    EMP = EMP || {};
    const ehPed = P.TIPO === 'PEDIDO', fechado = ['ENTREGUE', 'FATURADO'].includes(P.STATUS);
    const titulo = ehPed ? 'Ordem de serviço' : 'Orçamento', numero = ehPed ? P.NUMERO_PEDIDO : P.NUMERO_ORCAMENTO;
    const servs = ehPed ? P.servicos.filter(s => s.AUTORIZADO) : P.servicos, pecas = ehPed ? P.pecas.filter(p => p.AUTORIZADO) : P.pecas;
    const minutos = servs.filter(s => s.AUTORIZADO).reduce((a, s) => a + Math.round(Number(s.HORAS) * 60), 0);
    const g = garantiaTexto(P);
    const emp = [EMP.FANTASIA || EMP.RAZAO_SOCIAL, [EMP.LOGRADOURO, EMP.NUMERO, EMP.BAIRRO].filter(Boolean).join(', '), [EMP.CIDADE, EMP.UF].filter(Boolean).join('/'),
      [EMP.CNPJ && 'CNPJ ' + formatarDoc(EMP.CNPJ), EMP.TELEFONE && formatarFone(EMP.TELEFONE), EMP.EMAIL].filter(Boolean).join(' · ')];
    const datas = [['Aberto', dt(P.ABERTO_EM)], ['Aprovado', P.APROVADO_EM && dt(P.APROVADO_EM) + (P.APROVADO_POR_NOME ? ' por ' + esc(P.APROVADO_POR_NOME) : '')],
      ['Previsão', dt(P.PREVISAO_ENTREGA)], ['Concluído', dt(P.CONCLUIDO_EM)], ['Entregue', dt(P.ENTREGUE_EM)]].filter(x => x[1]);

    el.innerHTML = `
    <img class="marca-dagua" src="/img/simbolo-cobre.png" alt="">
    <div class="doc">
      <div class="cab"><img src="/img/aofficina-cobre.png" alt="aOfficina">
        <div class="emp"><b>${esc(emp[0] || '')}</b>${emp.slice(1).filter(Boolean).map(esc).join('<br>')}</div></div>

      <div class="tit">
        <h1><small>${ehPed ? 'Ordem de serviço' : 'Proposta de orçamento'}</small>Nº ${numero}${ehPed && P.NUMERO_ORCAMENTO ? ` <span style="font-size:10pt;font-weight:500;color:#888">· origem: orçamento ${P.NUMERO_ORCAMENTO}</span>` : ''}</h1>
        <div style="text-align:right"><span class="pill ${fechado ? 'ok' : ''}">${STATUS_ROT[P.STATUS] || P.STATUS}</span>
          <div class="datas" style="margin-top:2mm">${datas.map(x => `<span>${x[0]} <b>${x[1]}</b></span>`).join('')}</div></div>
      </div>

      <div class="grid2">
        <div class="box"><div class="rot">Cliente</div><div class="nome">${esc(P.CLIENTE_NOME)}</div>
          <div class="sub">${[formatarDoc(P.CPF_CNPJ), formatarFone(P.CLIENTE_WHATSAPP || P.CLIENTE_TELEFONE)].filter(Boolean).map(esc).join(' · ')}</div></div>
        <div class="box"><div class="rot">Veículo</div><div class="nome"><span class="placa">${esc(formatarPlaca(P.PLACA))}</span>${esc(P.MARCA + ' ' + P.MODELO)}</div>
          <div class="sub">${[P.ANO_FAB && (P.ANO_FAB + (P.ANO_MODELO ? '/' + P.ANO_MODELO : '')), P.COR, P.COMBUSTIVEL, P.KM_ENTRADA ? 'entrada com ' + Number(P.KM_ENTRADA).toLocaleString('pt-BR') + ' km' : (P.KM_ATUAL && Number(P.KM_ATUAL).toLocaleString('pt-BR') + ' km'), P.GUINCHO && 'chegou de guincho'].filter(Boolean).map(esc).join(' · ')}
          ${P.MECANICO_NOME || P.FUNCIONARIO_NOME ? '<br>Mecânico responsável: <b>' + esc(P.MECANICO_NOME || P.FUNCIONARIO_NOME) + '</b>' : ''}</div></div>
      </div>

      ${(P.QUEIXA || P.DIAGNOSTICO || P.OBSERVACAO) ? `<div class="txt grid2" style="grid-template-columns:${P.QUEIXA && P.DIAGNOSTICO ? '1fr 1fr' : '1fr'}">
        ${P.QUEIXA ? `<div class="box"><div class="rot">Relato do cliente</div><p>${esc(P.QUEIXA)}</p></div>` : ''}
        ${P.DIAGNOSTICO ? `<div class="box"><div class="rot">Diagnóstico</div><p>${esc(P.DIAGNOSTICO)}</p></div>` : ''}
        ${P.OBSERVACAO ? `<div class="box" style="grid-column:1/-1"><div class="rot">Observações</div><p>${esc(P.OBSERVACAO)}</p></div>` : ''}
      </div>` : ''}

      <h2>Mão de obra <span>${servs.length} ${servs.length === 1 ? 'item' : 'itens'}${minutos ? ' · tempo previsto ' + minutosParaTexto(minutos) : ''}</span></h2>
      <table><thead><tr><th style="width:52%">Serviço</th><th>${ehPed ? 'Executado por' : 'Mecânico'}</th><th class="r">Horas</th><th class="r">R$/hora</th><th class="r">Valor</th></tr></thead><tbody>
        ${servs.length ? servs.map(s => `<tr class="${!s.AUTORIZADO ? 'nao' : ''}"><td>${esc(s.DESCRICAO)}${s.SERVICO_CODIGO ? '<span class="cod">' + esc(s.SERVICO_CODIGO) + '</span>' : ''}${!s.AUTORIZADO ? '<span class="tag">não autorizado</span>' : ''}
          ${ehPed && s.DESCRICAO_EXECUTADO ? '<div class="feito">' + esc(s.DESCRICAO_EXECUTADO) + '</div>' : ''}</td>
          <td>${esc(s.FUNCIONARIO_NOME || P.FUNCIONARIO_NOME || '—')}</td><td class="r">${Number(s.HORAS).toFixed(2).replace('.', ',')}</td><td class="r">${formatarMoeda(s.VALOR_HORA_CENT)}</td><td class="r"><b>${formatarMoeda(s.VALOR_CENT)}</b></td></tr>`).join('')
        : '<tr><td colspan="5" style="color:#999;text-align:center">Nenhum serviço</td></tr>'}
      </tbody></table>

      <h2>Peças e materiais <span>${pecas.length} ${pecas.length === 1 ? 'item' : 'itens'}</span></h2>
      <table><thead><tr><th style="width:58%">Descrição</th><th class="r">Qtd</th><th class="r">Unitário</th><th class="r">Valor</th></tr></thead><tbody>
        ${pecas.length ? pecas.map(p => `<tr class="${!p.AUTORIZADO ? 'nao' : ''}"><td>${esc(p.DESCRICAO)}${p.PECA_CODIGO ? '<span class="cod">' + esc(p.PECA_CODIGO) + '</span>' : ''}${!p.AUTORIZADO ? '<span class="tag">não autorizada</span>' : ''}</td>
          <td class="r">${Number(p.QUANTIDADE).toLocaleString('pt-BR')} ${esc(p.UNIDADE || '')}</td><td class="r">${formatarMoeda(p.VALOR_UNIT_CENT)}</td><td class="r"><b>${formatarMoeda(p.VALOR_CENT)}</b></td></tr>`).join('')
        : '<tr><td colspan="4" style="color:#999;text-align:center">Nenhuma peça</td></tr>'}
      </tbody></table>

      <div class="tot"><table>
        <tr><td>Mão de obra</td><td class="r">${formatarMoeda(P.TOTAL_SERVICOS_CENT)}</td></tr>
        <tr><td>Peças e materiais</td><td class="r">${formatarMoeda(P.TOTAL_PECAS_CENT)}</td></tr>
        ${Number(P.DESCONTO_CENT) ? `<tr><td>Desconto</td><td class="r">− ${formatarMoeda(P.DESCONTO_CENT)}</td></tr>` : ''}
        <tr class="total"><td>Total</td><td class="r">${formatarMoeda(P.TOTAL_CENT)}</td></tr>
      </table></div>

      ${pg && pg.pagamentos && pg.pagamentos.length ? `<h2>Pagamento <span>${pg.restante_cent > 0 ? 'restam ' + formatarMoeda(pg.restante_cent) : pg.aberto_cent > 0 ? formatarMoeda(pg.aberto_cent) + ' a vencer' : 'quitado'}</span></h2>
      <table><thead><tr><th>Forma</th><th>Detalhe</th><th>Situação</th><th class="r">Valor</th></tr></thead><tbody>
        ${pg.pagamentos.map(x => `<tr><td>${FORMA_ROT[x.FORMA] || x.FORMA}</td><td>${[x.PARCELAS > 1 && x.PARCELAS + 'x', x.VENCIMENTO && 'venc. ' + data(x.VENCIMENTO), x.RECEBIDO_POR_NOME && 'recebido por ' + esc(x.RECEBIDO_POR_NOME)].filter(Boolean).join(' · ')}</td>
          <td>${x.PAGO ? '<b style="color:#2e7d4f">Pago</b>' + (x.PAGO_EM ? ' em ' + data(x.PAGO_EM) : '') : 'Em aberto'}</td><td class="r"><b>${formatarMoeda(x.VALOR_CENT)}</b></td></tr>`).join('')}
      </tbody></table>` : ''}

      ${ehPed ? `<div class="gar">
        <div class="box"><div class="rot">Garantia</div><p><b>${g.prazo}</b></p><p style="margin-top:1mm">${g.cond}</p></div>
        <div class="box"><div class="rot">Condições</div><p>Serviços e peças executados conforme autorização do cliente, item a item. Valores conferidos no fechamento. A retirada do veículo implica a aceitação dos serviços descritos neste documento. Em caso de dúvida sobre a garantia, apresente este documento na oficina.</p></div>
      </div>` : `<div class="gar">
        <div class="box"><div class="rot">Validade da proposta</div><p>Este orçamento é válido por <b>10 dias</b> a partir de ${data(P.ABERTO_EM)}. Preços de peças sujeitos a confirmação com o fornecedor no momento da aprovação. Itens não autorizados não serão executados.</p></div>
        <div class="box"><div class="rot">Garantia</div><p>Serviços e peças fornecidos pela oficina têm garantia de <b>90 dias</b> a partir da entrega do veículo, conforme o Código de Defesa do Consumidor, nas condições descritas na ordem de serviço.</p></div>
      </div>`}

      <div class="ass"><div><b>${esc(P.CLIENTE_NOME)}</b>${ehPed ? 'Cliente · ciente dos serviços executados' : 'Cliente · de acordo com o orçamento'}</div><div><b>${esc(emp[0] || 'Oficina')}</b>Responsável pela oficina</div></div>
      <div class="fim"></div>
    </div>
    <div class="rod"><span><img src="/img/iaprocess-badge.png" alt="">aOfficina · <b>IA PROCESS AUTOMATION</b></span><span>${titulo} nº ${numero} · emitido em ${new Date().toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' })}</span></div>`;
    window.print();
  };
})();
