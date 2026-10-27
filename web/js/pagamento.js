// aOfficina — tela de pagamento no fechamento do pedido. Uso: abrirPagamento(pedidoId, aoFechar)
(function () {
  const HTML = `
  <div class="modal fade" id="pgModal" tabindex="-1" data-bs-backdrop="static"><div class="modal-dialog modal-lg modal-dialog-scrollable"><div class="modal-content">
    <div class="modal-header py-2"><h6 class="modal-title mb-0"><i class="bi bi-cash-coin me-2"></i>Receber e entregar — <span id="pgTitulo"></span></h6><button type="button" class="btn-close" data-bs-dismiss="modal"></button></div>
    <div class="modal-body">
      <div class="row g-2 text-center mb-3">
        <div class="col-4"><div class="card card-ao"><div class="card-body py-2"><div class="small text-muted">Total</div><b id="pgTotal" class="fs-5"></b></div></div></div>
        <div class="col-4"><div class="card card-ao"><div class="card-body py-2"><div class="small text-muted">Recebido / em aberto</div><b id="pgPago" class="fs-6"></b></div></div></div>
        <div class="col-4"><div class="card card-ao kpi"><div class="card-body py-2"><div class="small text-muted">Falta</div><b id="pgResta" class="fs-5 text-danger"></b></div></div></div>
      </div>
      <div id="pgForm">
        <div class="btn-group w-100 flex-wrap mb-3" role="group" id="pgFormas">
          <input type="radio" class="btn-check" name="pgForma" id="pgF_DINHEIRO" value="DINHEIRO" checked><label class="btn btn-outline-secondary" for="pgF_DINHEIRO"><i class="bi bi-cash d-block fs-4"></i>Dinheiro</label>
          <input type="radio" class="btn-check" name="pgForma" id="pgF_PIX" value="PIX"><label class="btn btn-outline-secondary" for="pgF_PIX"><i class="bi bi-qr-code d-block fs-4"></i>PIX</label>
          <input type="radio" class="btn-check" name="pgForma" id="pgF_DEBITO" value="DEBITO"><label class="btn btn-outline-secondary" for="pgF_DEBITO"><i class="bi bi-credit-card-2-front d-block fs-4"></i>Débito</label>
          <input type="radio" class="btn-check" name="pgForma" id="pgF_CREDITO" value="CREDITO"><label class="btn btn-outline-secondary" for="pgF_CREDITO"><i class="bi bi-credit-card d-block fs-4"></i>Crédito</label>
          <input type="radio" class="btn-check" name="pgForma" id="pgF_BOLETO" value="BOLETO"><label class="btn btn-outline-secondary" for="pgF_BOLETO"><i class="bi bi-upc-scan d-block fs-4"></i>Boleto</label>
        </div>
        <div class="row g-2 align-items-end">
          <div class="col-md-4"><label class="form-label small mb-0">Valor (R$)</label><input type="number" step="0.01" min="0.01" class="form-control form-control-lg" id="pgValor"></div>
          <div class="col-md-4" id="pgBoxParcelas" style="display:none"><label class="form-label small mb-0">Parcelas</label><select class="form-select form-select-lg" id="pgParcelas"></select></div>
          <div class="col-md-4" id="pgBoxVenc" style="display:none"><label class="form-label small mb-0">Vencimento do boleto</label><input type="date" class="form-control form-control-lg" id="pgVenc"></div>
          <div class="col-md-4" id="pgBoxTroco" style="display:none"><label class="form-label small mb-0">Troco</label><div class="form-control form-control-lg bg-light" id="pgTroco">R$ 0,00</div></div>
          <div class="col-md-4 ms-auto"><button class="btn btn-success btn-lg w-100" id="pgPagar" type="button"><i class="bi bi-check2-circle me-1"></i>Pago</button></div>
        </div>
        <div id="pgPix" class="mt-3 text-center" style="display:none">
          <div class="d-inline-block border rounded p-2 bg-white"><img id="pgQr" alt="QR Code PIX" style="width:220px;height:220px"></div>
          <div class="small text-muted mt-1">QR Code de demonstração — não é uma cobrança real</div>
          <div class="input-group input-group-sm mt-2" style="max-width:520px;margin:auto"><input class="form-control font-monospace" id="pgPixTxt" readonly><button class="btn btn-outline-secondary" type="button" id="pgPixCopiar"><i class="bi bi-clipboard"></i> copiar</button></div>
        </div>
        <div id="pgAviso" class="small text-muted mt-2"></div>
      </div>
      <h6 class="mt-4 mb-2 text-secondary">Lançamentos</h6>
      <div class="table-responsive"><table class="table table-ao table-sm mb-0"><thead><tr><th>Forma</th><th class="text-end">Valor</th><th>Detalhe</th><th class="text-center">Pago</th><th></th></tr></thead><tbody id="pgLista"></tbody></table></div>
    </div>
    <div class="modal-footer justify-content-between">
      <span class="small text-muted" id="pgRodape"></span>
      <div><button type="button" class="btn btn-outline-secondary" data-bs-dismiss="modal">Fechar</button> <button type="button" class="btn btn-cobre" id="pgFechar" disabled><i class="bi bi-car-front me-1"></i>Fechar pedido e entregar</button></div>
    </div>
  </div></div></div>`;
  const $ = (id) => document.getElementById(id);
  let pronto = false, pedidoId = null, R = null, aoFechar = null, qrUrl = null;
  const FORMA_ROT = { DINHEIRO: 'Dinheiro', PIX: 'PIX', DEBITO: 'Cartão de débito', CREDITO: 'Cartão de crédito', BOLETO: 'Boleto' };

  function preparar() {
    if (pronto) return; pronto = true;
    const d = document.createElement('div'); d.innerHTML = HTML; document.body.appendChild(d);
    document.querySelectorAll('input[name=pgForma]').forEach(r => r.onchange = formaMudou);
    $('pgValor').oninput = recalc; $('pgParcelas').onchange = recalc;
    $('pgPagar').onclick = pagar; $('pgFechar').onclick = fechar;
    $('pgPixCopiar').onclick = () => navigator.clipboard && navigator.clipboard.writeText($('pgPixTxt').value).then(() => mostrarAlerta('Código PIX copiado'));
  }
  function forma() { return document.querySelector('input[name=pgForma]:checked').value; }
  function formaMudou() {
    const f = forma();
    $('pgBoxParcelas').style.display = f === 'CREDITO' ? '' : 'none'; $('pgBoxVenc').style.display = f === 'BOLETO' ? '' : 'none';
    $('pgBoxTroco').style.display = f === 'DINHEIRO' ? '' : 'none'; $('pgPix').style.display = f === 'PIX' ? '' : 'none';
    $('pgPagar').innerHTML = f === 'BOLETO' ? '<i class="bi bi-file-earmark-text me-1"></i>Emitir boleto (em aberto)' : '<i class="bi bi-check2-circle me-1"></i>Pago';
    if (f === 'BOLETO') { const d = new Date(); d.setDate(d.getDate() + 7); $('pgVenc').value = d.toISOString().slice(0, 10); }
    if (f !== 'DINHEIRO' && R && reaisParaCent($('pgValor').value) > R.restante_cent) $('pgValor').value = centParaReais(R.restante_cent);
    let aviso = '';
    if (f === 'BOLETO' && R) { if (!R.cliente.cpf_cnpj) aviso = '⚠ O cliente não tem CPF/CNPJ cadastrado — o boleto exige. Complete o cadastro antes.'; else if (!R.cliente.endereco_ok) aviso = '⚠ O cliente não tem endereço completo — o boleto exige logradouro, cidade e CEP.'; }
    $('pgAviso').textContent = aviso; recalc();
  }
  async function recalc() {
    const f = forma(), v = reaisParaCent($('pgValor').value);
    if (f === 'CREDITO') { const sel = $('pgParcelas'); const atual = parseInt(sel.value) || 1; sel.innerHTML = ''; for (let n = 1; n <= 6; n++) { const o = document.createElement('option'); o.value = n; o.textContent = n + 'x de ' + formatarMoeda(Math.round(v / n)) + (n === 1 ? ' (à vista)' : ''); sel.appendChild(o); } sel.value = atual; }
    if (f === 'DINHEIRO' && R) $('pgTroco').textContent = formatarMoeda(Math.max(v - R.restante_cent, 0));
    if (f === 'PIX' && v > 0) await carregarQr(v);
  }
  let qrTimer = null;
  function carregarQr(v) {
    clearTimeout(qrTimer);
    return new Promise(res => { qrTimer = setTimeout(async () => {
      try {
        const resp = await fetch(API.pixQrUrl(pedidoId, v), { headers: { Authorization: 'Bearer ' + localStorage.getItem('token') } });
        if (!resp.ok) throw new Error((await resp.json()).detail || 'QR indisponível');
        if (qrUrl) URL.revokeObjectURL(qrUrl); qrUrl = URL.createObjectURL(await resp.blob()); $('pgQr').src = qrUrl; $('pgPixTxt').value = resp.headers.get('X-Pix-Payload') || '';
      } catch (e) { mostrarAlerta('PIX: ' + e.message, 'warning'); } res();
    }, 400); });
  }
  function render() {
    $('pgTotal').textContent = formatarMoeda(R.total_cent); $('pgPago').textContent = formatarMoeda(R.pago_cent) + (R.aberto_cent ? ' / ' + formatarMoeda(R.aberto_cent) : ''); $('pgResta').textContent = formatarMoeda(R.restante_cent);
    $('pgResta').className = 'fs-5 ' + (R.restante_cent ? 'text-danger' : 'text-success');
    $('pgValor').value = centParaReais(R.restante_cent); $('pgForm').style.display = R.restante_cent ? '' : 'none';
    $('pgLista').innerHTML = R.pagamentos.length ? R.pagamentos.map(g => `<tr>
      <td>${esc(FORMA_ROT[g.FORMA])}${g.FORMA === 'CREDITO' && g.PARCELAS > 1 ? ' ' + g.PARCELAS + 'x' : ''}</td><td class="text-end fw-bold">${formatarMoeda(g.VALOR_CENT)}</td>
      <td class="small text-muted">${g.FORMA === 'BOLETO' ? 'venc. ' + esc(formatarData(g.VENCIMENTO)) + ' · nº ' + esc(g.NOSSO_NUMERO || '') : g.FORMA === 'PIX' ? 'txid ' + esc(g.TXID || '') : ''}${g.OBS ? ' · ' + esc(g.OBS) : ''}${g.PAGO_EM ? ' · ' + esc(formatarDataHora(g.PAGO_EM)) : ''}</td>
      <td class="text-center"><input type="checkbox" class="form-check-input" ${g.PAGO ? 'checked' : ''} onchange="window.__pgPago(${g.ID}, this.checked)"></td>
      <td class="text-end">${['ENTREGUE', 'FATURADO'].includes(R.status) ? '' : `<button class="btn btn-sm btn-outline-danger" onclick="window.__pgDel(${g.ID})"><i class="bi bi-trash"></i></button>`}</td></tr>`).join('')
      : '<tr><td colspan="5" class="text-muted text-center py-2">Nenhum pagamento lançado</td></tr>';
    const podeFechar = R.coberto && R.status === 'CONCLUIDO';
    $('pgFechar').disabled = !podeFechar;
    $('pgRodape').textContent = R.status === 'ENTREGUE' ? 'Pedido já entregue.' : R.coberto ? 'Total coberto — pode entregar o veículo.' : R.status !== 'CONCLUIDO' ? 'Conclua o pedido para liberar a entrega.' : 'Lance os pagamentos até cobrir o total.';
    formaMudou();
  }
  async function carregar() { R = await API.getPagamentos(pedidoId); render(); }
  async function pagar() {
    const f = forma(); const v = reaisParaCent($('pgValor').value); if (v <= 0) return mostrarAlerta('Informe o valor', 'warning');
    if (f === 'BOLETO' && $('pgAviso').textContent) return mostrarAlerta($('pgAviso').textContent, 'warning');
    const b = $('pgPagar'); b.disabled = true;
    try {
      const r = await API.lancarPagamento(pedidoId, { forma: f, valor_cent: v, parcelas: f === 'CREDITO' ? parseInt($('pgParcelas').value) : 1, pago: f !== 'BOLETO', vencimento: f === 'BOLETO' ? $('pgVenc').value : null });
      mostrarAlerta(f === 'BOLETO' ? 'Boleto lançado em aberto' : 'Pagamento registrado' + (r.troco_cent ? ' — troco ' + formatarMoeda(r.troco_cent) : ''));
      await carregar();
    } catch (e) { mostrarAlerta(e.message, 'danger'); } finally { b.disabled = false; }
  }
  window.__pgPago = async (id, pago) => { try { await API.pagoPagamento(pedidoId, id, pago); await carregar(); } catch (e) { mostrarAlerta(e.message, 'danger'); carregar(); } };
  window.__pgDel = async (id) => { if (!confirmar('Excluir este lançamento?')) return; try { await API.delPagamento(pedidoId, id); await carregar(); } catch (e) { mostrarAlerta(e.message, 'danger'); } };
  async function fechar() {
    if (!confirmar('Confirmar entrega do veículo ao cliente e fechar o pedido?')) return;
    try { await API.fecharPedido(pedidoId); mostrarAlerta('Pedido entregue e fechado'); bootstrap.Modal.getInstance($('pgModal')).hide(); if (aoFechar) aoFechar(); }
    catch (e) { mostrarAlerta(e.message, 'danger'); }
  }
  window.abrirPagamento = async function (id, titulo, callback) {
    preparar(); pedidoId = id; aoFechar = callback || null; $('pgTitulo').textContent = titulo || '';
    bootstrap.Modal.getOrCreateInstance($('pgModal')).show();
    try { await carregar(); } catch (e) { mostrarAlerta(e.message, 'danger'); }
  };
})();
