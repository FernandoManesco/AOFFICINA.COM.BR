// aOfficina — leitor de placa pela câmera (tablet) + painel do veículo (pedidos abertos / histórico / novo orçamento).
// Uso: botão com onclick="abrirLeitorPlaca()". Sem câmera (ou no PC) funciona só com a digitação da placa.
(function () {
  const HTML = `
  <div class="modal fade" id="plModal" tabindex="-1" data-bs-backdrop="static"><div class="modal-dialog modal-lg modal-fullscreen-md-down"><div class="modal-content">
    <div class="modal-header py-2"><h6 class="modal-title mb-0"><i class="bi bi-camera me-2"></i>Localizar veículo pela placa</h6><button type="button" class="btn-close" data-bs-dismiss="modal"></button></div>
    <div class="modal-body">
      <div id="plCam" class="position-relative rounded overflow-hidden bg-dark" style="aspect-ratio:4/3;max-height:52vh">
        <video id="plVideo" autoplay playsinline muted style="width:100%;height:100%;object-fit:cover"></video>
        <div id="plGuia" style="position:absolute;left:12%;right:12%;top:38%;height:24%;border:3px solid #3FD2C7;border-radius:10px;box-shadow:0 0 0 2000px rgba(0,0,0,.45)"></div>
        <div class="position-absolute bottom-0 start-0 end-0 text-center text-white small py-1" style="background:rgba(0,0,0,.45)">Enquadre a placa dentro da moldura e toque em Ler</div>
      </div>
      <div class="d-flex gap-2 mt-2 flex-wrap">
        <button class="btn btn-cobre flex-fill" id="plLer" type="button"><i class="bi bi-camera me-1"></i>Ler placa</button>
        <button class="btn btn-outline-secondary" id="plTrocar" type="button" title="Trocar câmera"><i class="bi bi-arrow-repeat"></i></button>
      </div>
      <div class="input-group mt-3"><span class="input-group-text">Placa</span><input class="form-control text-uppercase placa" id="plTexto" maxlength="8" placeholder="ou digite: ABC1D23" autocomplete="off" style="font-size:1.3rem;letter-spacing:.15em"><button class="btn btn-cobre" id="plBuscar" type="button"><i class="bi bi-search"></i></button></div>
      <div id="plCands" class="d-flex gap-2 mt-2 flex-wrap"></div>
      <div id="plResultado" class="mt-3"></div>
    </div>
  </div></div></div>`;
  const $ = (id) => document.getElementById(id);
  let stream = null, frontal = false, pronto = false, cb = null;

  function preparar() {
    if (pronto) return; pronto = true;
    const d = document.createElement('div'); d.innerHTML = HTML; document.body.appendChild(d);
    $('plModal').addEventListener('shown.bs.modal', ligarCamera);
    $('plModal').addEventListener('hidden.bs.modal', desligarCamera);
    $('plLer').onclick = ler; $('plTrocar').onclick = () => { frontal = !frontal; ligarCamera(); };
    $('plBuscar').onclick = () => buscar($('plTexto').value);
    $('plTexto').addEventListener('keydown', (ev) => { if (ev.key === 'Enter') buscar($('plTexto').value); });
  }
  async function ligarCamera() {
    desligarCamera();
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) { $('plCam').style.display = 'none'; $('plLer').disabled = true; return; }
    try {
      stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: frontal ? 'user' : { ideal: 'environment' }, width: { ideal: 1920 }, height: { ideal: 1440 } }, audio: false });
      $('plVideo').srcObject = stream; $('plCam').style.display = ''; $('plLer').disabled = false;
    } catch (e) { $('plCam').style.display = 'none'; $('plLer').disabled = true; mostrarAlerta('Câmera indisponível (' + (e.name === 'NotAllowedError' ? 'permita a câmera no cadeado do endereço' : e.message) + ') — digite a placa', 'warning'); setTimeout(() => $('plTexto').focus(), 300); }
  }
  function desligarCamera() { if (stream) { stream.getTracks().forEach(t => t.stop()); stream = null; } }
  async function ler() {
    const v = $('plVideo'); if (!v.videoWidth) return mostrarAlerta('Câmera ainda carregando', 'warning');
    // recorta a região da moldura (12%..88% largura, 38%..62% altura) em relação ao vídeo exibido com object-fit:cover
    const cw = $('plCam').clientWidth, ch = $('plCam').clientHeight, vw = v.videoWidth, vh = v.videoHeight;
    const esc_ = Math.max(cw / vw, ch / vh), dw = vw * esc_, dh = vh * esc_, ox = (dw - cw) / 2, oy = (dh - ch) / 2;
    const sx = (0.12 * cw + ox) / esc_, sy = (0.38 * ch + oy) / esc_, sw = (0.76 * cw) / esc_, sh = (0.24 * ch) / esc_;
    const c = document.createElement('canvas'); c.width = Math.round(sw * 2); c.height = Math.round(sh * 2);
    c.getContext('2d').drawImage(v, sx, sy, sw, sh, 0, 0, c.width, c.height);
    const blob = await new Promise(r => c.toBlob(r, 'image/jpeg', 0.92));
    $('plLer').disabled = true; $('plLer').innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Lendo…'; $('plCands').innerHTML = '';
    try {
      const fd = new FormData(); fd.append('imagem', blob, 'placa.jpg');
      const r = await API.lerPlaca(fd);
      if (!r.candidatas.length) { mostrarAlerta('Não consegui ler — aproxime, evite reflexo e tente de novo, ou digite a placa', 'warning'); return; }
      const melhor = r.candidatas.find(x => x.cadastrada) || r.candidatas[0];
      $('plTexto').value = melhor.placa;
      $('plCands').innerHTML = r.candidatas.map(x => `<button type="button" class="btn btn-sm ${x.cadastrada ? 'btn-outline-success' : 'btn-outline-secondary'}" data-p="${esc(x.placa)}"><span class="placa">${esc(formatarPlaca(x.placa))}</span>${x.cadastrada ? ' ✓ ' + esc(x.MODELO) : ''}</button>`).join('');
      $('plCands').querySelectorAll('button').forEach(b => b.onclick = () => { $('plTexto').value = b.dataset.p; buscar(b.dataset.p); });
      buscar(melhor.placa);
    } catch (e) { mostrarAlerta(e.message, 'danger'); }
    finally { $('plLer').disabled = false; $('plLer').innerHTML = '<i class="bi bi-camera me-1"></i>Ler placa'; }
  }
  async function buscar(placa) {
    placa = (placa || '').replace(/[^A-Za-z0-9]/g, '').toUpperCase(); const out = $('plResultado');
    if (placa.length < 7) { out.innerHTML = ''; return; }
    out.innerHTML = '<div class="text-muted small"><span class="spinner-border spinner-border-sm me-1"></span>Procurando…</div>';
    let v;
    try { v = await API.getVeiculoPorPlaca(placa); }
    catch (e) { out.innerHTML = `<div class="alert alert-warning mb-2">Placa <b>${esc(formatarPlaca(placa))}</b> não cadastrada.</div><a class="btn btn-cobre" href="/pages/clientes.html"><i class="bi bi-person-plus me-1"></i>Cadastrar cliente e veículo</a>`; return; }
    const h = await API.historicoVeiculo(v.ID);
    const ve = h.veiculo;
    let html = `<div class="card card-ao mb-2"><div class="card-body py-2"><div class="d-flex justify-content-between flex-wrap gap-2 align-items-center">
      <div><span class="placa">${esc(formatarPlaca(ve.PLACA))}</span> <b>${esc(ve.MARCA)} ${esc(ve.MODELO)}</b> <span class="text-muted">${esc(ve.ANO_FAB || '')}${ve.ANO_MODELO ? '/' + ve.ANO_MODELO : ''} ${esc(ve.COR || '')}</span><div class="small">${esc(ve.CLIENTE_NOME)} · ${esc(formatarFone(ve.CLIENTE_WHATSAPP || ve.CLIENTE_TELEFONE))}${ve.KM_ATUAL ? ' · ' + Number(ve.KM_ATUAL).toLocaleString('pt-BR') + ' km' : ''}</div></div>
      <a class="btn btn-sm btn-cobre" href="/pages/pedidos.html?novo=1&cliente=${ve.CLIENTE_ID}&veiculo=${ve.ID}"><i class="bi bi-clipboard2-plus me-1"></i>Novo orçamento</a></div></div></div>`;
    if (h.abertos.length) {
      html += `<div class="small text-uppercase text-muted mb-1">Em andamento</div>` + h.abertos.map(p => `<a class="d-block card card-ao mb-2 text-decoration-none" href="/pages/pedido.html?id=${p.ID}"><div class="card-body py-2 d-flex justify-content-between align-items-center gap-2">
        <div><b>${p.TIPO === 'PEDIDO' ? 'Pedido ' + p.NUMERO_PEDIDO : 'Orçamento ' + p.NUMERO_ORCAMENTO}</b> ${badgeStatus(p.STATUS)}<div class="small text-muted">${esc(formatarDataHora(p.ABERTO_EM))}${p.FUNCIONARIO_NOME ? ' · ' + esc(p.FUNCIONARIO_NOME) : ''}</div><div class="small">${esc(p.SERVICOS || p.QUEIXA || '')}</div></div>
        <div class="text-end"><b>${formatarMoeda(p.TOTAL_CENT)}</b><div class="small text-cobre"><i class="bi bi-arrow-right-circle"></i> abrir</div></div></div></a>`).join('');
      if (h.abertos.length === 1 && cb === null) { setTimeout(() => location.href = '/pages/pedido.html?id=' + h.abertos[0].ID, 900); }
    } else {
      html += `<div class="alert alert-light border mb-2 py-2 small"><i class="bi bi-info-circle me-1"></i>Nenhum pedido em andamento para este veículo.</div>`;
    }
    if (h.historico.length) {
      html += `<div class="small text-uppercase text-muted mb-1 mt-2">Histórico na oficina (${h.historico.length})</div><div class="table-responsive"><table class="table table-ao table-sm mb-0"><thead><tr><th>Data</th><th>Nº</th><th>Km</th><th>Serviços / peças</th><th>Status</th><th class="text-end">Total</th></tr></thead><tbody>` +
        h.historico.map(p => `<tr onclick="location.href='/pages/pedido.html?id=${p.ID}'"><td class="small">${esc(formatarData(p.ABERTO_EM))}</td><td class="mono small text-nowrap">${p.NUMERO_PEDIDO ? 'P ' + p.NUMERO_PEDIDO : 'O ' + p.NUMERO_ORCAMENTO}</td><td class="small">${p.KM_ENTRADA ? Number(p.KM_ENTRADA).toLocaleString('pt-BR') : ''}</td>
          <td class="small">${esc(p.SERVICOS || '')}${p.PECAS ? '<div class="text-muted">' + esc(p.PECAS) + '</div>' : ''}</td><td>${badgeStatus(p.STATUS)}</td><td class="text-end small">${formatarMoeda(p.TOTAL_CENT)}</td></tr>`).join('') + '</tbody></table></div>';
    } else if (!h.abertos.length) {
      html += `<div class="small text-muted">Primeira visita deste veículo.</div>`;
    }
    out.innerHTML = html;
  }
  window.abrirLeitorPlaca = function (callback) {
    preparar(); cb = callback || null; $('plTexto').value = ''; $('plCands').innerHTML = ''; $('plResultado').innerHTML = '';
    bootstrap.Modal.getOrCreateInstance($('plModal')).show();
  };
})();
