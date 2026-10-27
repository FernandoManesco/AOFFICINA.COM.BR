// aOfficina — assistente de IA nos campos de texto (portado do WebTriagem v086).
// Uso: iaAtivar([{ id: 'diagnostico', campo: 'diagnostico', rotulo: 'Diagnóstico' }, ...])
//   ✍️ escrever com a caneta (MyScript iink; precisa das chaves no servidor)
//   🎤 ditar — Chrome/Edge/Safari: reconhecimento do próprio navegador; outros: grava e transcreve no servidor (whisper)
//   ✨ corrigir e formatar o texto com a IA (DeepSeek), mostrando antes/depois para o usuário aceitar
// iaPesquisar(tipo, texto, veiculo, km) abre a janela de pesquisa (problema | peca).
(function () {
  const CSS = `
  .ia-btns{display:inline-flex;gap:.15rem;margin-left:.4rem;vertical-align:middle}
  .ia-btns button{border:1px solid #d7d9de;background:#fff;border-radius:.4rem;padding:0 .35rem;font-size:.9rem;line-height:1.5;cursor:pointer}
  .ia-btns button:hover{background:#faf4ee;border-color:#B87333}
  .ia-btns button.on{background:#dc3545;color:#fff;border-color:#dc3545}
  .ia-flash{animation:iaflash 1.6s ease-out}
  @keyframes iaflash{0%{box-shadow:0 0 0 3px rgba(184,115,51,.55)}100%{box-shadow:none}}
  #iinkPad{height:58vh;min-height:300px;border:2px dashed #c9a27e;border-radius:12px;background:repeating-linear-gradient(#fff 0 44px,#f6efe8 44px 45px);touch-action:none;position:relative}
  #iinkPad .ms-editor{height:100%}
  .ia-prev{min-height:2.4rem;border:1px solid #e3e5e8;border-radius:.5rem;padding:.4rem .6rem;background:#fafafa;white-space:pre-wrap}
  .ia-resp{white-space:pre-wrap;font-size:.92rem;line-height:1.45}
  .ia-resp h1,.ia-resp h2,.ia-resp h3{font-size:1rem;margin:.6rem 0 .2rem}`;
  const HTML = `
  <div class="modal fade" id="iaModalEscrita" tabindex="-1" data-bs-backdrop="static"><div class="modal-dialog modal-xl modal-fullscreen-md-down"><div class="modal-content">
    <div class="modal-header py-2"><h6 class="modal-title mb-0">✍️ Escrever — <span id="iaEscCampo"></span></h6>
      <div class="ms-auto d-flex gap-2"><button class="btn btn-sm btn-outline-secondary" id="iaEscDesfazer" type="button">↶ Desfazer</button><button class="btn btn-sm btn-outline-secondary" id="iaEscLimpar" type="button">Limpar</button><button type="button" class="btn-close ms-2" data-bs-dismiss="modal"></button></div></div>
    <div class="modal-body py-2"><div id="iinkPad"></div>
      <div class="d-flex justify-content-between mt-2 small text-muted"><span id="iaEscStatus">carregando quadro…</span><span>escreva em letra cursiva ou de forma; o texto aparece abaixo</span></div>
      <div class="ia-prev mt-2" id="iaEscTexto"></div></div>
    <div class="modal-footer py-2"><button class="btn btn-outline-secondary" data-bs-dismiss="modal" type="button">Cancelar</button><button class="btn btn-cobre" id="iaEscInserir" type="button" disabled>Inserir no campo</button></div>
  </div></div></div>
  <div class="modal fade" id="iaModalCorrigir" tabindex="-1"><div class="modal-dialog modal-lg"><div class="modal-content">
    <div class="modal-header py-2"><h6 class="modal-title mb-0">✨ Correção sugerida — <span id="iaCorCampo"></span></h6><button type="button" class="btn-close" data-bs-dismiss="modal"></button></div>
    <div class="modal-body"><div class="row g-2"><div class="col-md-6"><label class="form-label small">Original</label><textarea class="form-control" rows="8" id="iaCorAntes" readonly></textarea></div>
      <div class="col-md-6"><label class="form-label small">Sugestão da IA (editável)</label><textarea class="form-control" rows="8" id="iaCorDepois"></textarea></div></div></div>
    <div class="modal-footer py-2"><button class="btn btn-outline-secondary" data-bs-dismiss="modal" type="button">Manter original</button><button class="btn btn-cobre" id="iaCorAceitar" type="button">Usar a sugestão</button></div>
  </div></div></div>
  <div class="modal fade" id="iaModalPesq" tabindex="-1"><div class="modal-dialog modal-lg modal-dialog-scrollable"><div class="modal-content">
    <div class="modal-header py-2"><h6 class="modal-title mb-0" id="iaPesqTitulo">🔎 Pesquisa</h6><button type="button" class="btn-close" data-bs-dismiss="modal"></button></div>
    <div class="modal-body"><div class="small text-muted mb-2" id="iaPesqVeic"></div><div class="input-group mb-2"><input class="form-control" id="iaPesqTexto" placeholder="descreva o sintoma ou a peça"><button class="btn btn-cobre" id="iaPesqBtn" type="button"><i class="bi bi-search"></i> Pesquisar</button></div>
      <div class="ia-resp" id="iaPesqResp"></div></div>
    <div class="modal-footer py-2"><span class="small text-muted me-auto">Resposta gerada por IA: confirme códigos e procedimentos com o fornecedor/manual.</span><button class="btn btn-outline-secondary" id="iaPesqCopiar" type="button"><i class="bi bi-clipboard"></i> Copiar</button></div>
  </div></div></div>`;

  const $ = (id) => document.getElementById(id);
  const ROT = {};
  let pronto = false;
  function preparar() {
    if (pronto) return; pronto = true;
    const st = document.createElement('style'); st.textContent = CSS; document.head.appendChild(st);
    const div = document.createElement('div'); div.innerHTML = HTML; document.body.appendChild(div);
    $('iaCorAceitar').onclick = () => { if (!corAlvo) return; const el = $(corAlvo); el.value = $('iaCorDepois').value; el.dispatchEvent(new Event('input')); flash(el); bootstrap.Modal.getInstance($('iaModalCorrigir')).hide(); mostrarAlerta('Texto atualizado'); };
    $('iaEscInserir').onclick = () => { if (!escAlvo || !escTextoAtual) return; acrescentar(escAlvo, escTextoAtual); bootstrap.Modal.getInstance($('iaModalEscrita')).hide(); mostrarAlerta('Texto inserido — se quiser, clique em ✨ para corrigir'); };
    $('iaModalEscrita').addEventListener('shown.bs.modal', criarPad);
    $('iaModalEscrita').addEventListener('hidden.bs.modal', () => { try { if (pad && pad.destroy) pad.destroy(); } catch (e) {} pad = null; });
    $('iaEscLimpar').onclick = () => { escTextoAtual = ''; $('iaEscTexto').textContent = ''; $('iaEscInserir').disabled = true; if (pad && pad.clear) { try { pad.clear(); return; } catch (e) {} } criarPad(); };
    $('iaEscDesfazer').onclick = () => { if (pad && pad.undo) { try { pad.undo(); agendarExport(); } catch (e) {} } };
    $('iaPesqBtn').onclick = executarPesquisa; $('iaPesqTexto').addEventListener('keydown', (ev) => { if (ev.key === 'Enter') executarPesquisa(); });
    $('iaPesqCopiar').onclick = () => { navigator.clipboard && navigator.clipboard.writeText($('iaPesqResp').innerText).then(() => mostrarAlerta('Copiado')); };
    document.addEventListener('click', (e) => {
      const b = e.target.closest('button[data-ia-esc],button[data-ia-mic],button[data-ia-cor]'); if (!b) return; e.preventDefault();
      if (b.dataset.iaEsc) abrirEscrita(b.dataset.iaEsc); else if (b.dataset.iaMic) ditar(b.dataset.iaMic, b); else corrigir(b.dataset.iaCor);
    });
  }
  function flash(el) { el.classList.remove('ia-flash'); void el.offsetWidth; el.classList.add('ia-flash'); }
  function acrescentar(id, texto) { const el = $(id); if (!el || !texto) return; const sep = el.tagName === 'TEXTAREA' ? '\n' : ' '; el.value = (el.value.trim() ? el.value.replace(/\s+$/, '') + sep : '') + texto.trim(); el.dispatchEvent(new Event('input')); flash(el); }

  // ---------- ativação ----------
  window.iaAtivar = function (campos) {
    preparar();
    campos.forEach(c => {
      const el = $(c.id); if (!el || el.dataset.iaOk) return; el.dataset.iaOk = '1'; el.dataset.iaCampo = c.campo || c.id; ROT[c.id] = c.rotulo || c.id;
      const lab = el.closest('.col-12, .col-md-6, .mb-2, .mb-3, div')?.querySelector('label') || el.previousElementSibling;
      const slot = document.createElement('span'); slot.className = 'ia-btns';
      slot.innerHTML = `<button type="button" data-ia-esc="${c.id}" title="Escrever com a caneta">✍️</button><button type="button" data-ia-mic="${c.id}" title="Ditar (microfone)">🎤</button><button type="button" data-ia-cor="${c.id}" title="Corrigir e formatar com IA">✨</button>`;
      if (lab && lab.tagName === 'LABEL') lab.appendChild(slot); else el.parentNode.insertBefore(slot, el);
    });
  };

  // ---------- ditado ----------
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  let recAtual = null;
  const NAV_VOZ = (() => {
    if (!SR) return false; if (navigator.brave) return false;
    const marcas = (navigator.userAgentData && navigator.userAgentData.brands || []).map(b => b.brand);
    if (marcas.length) return marcas.some(b => /Google Chrome|Microsoft Edge/i.test(b));
    const ua = navigator.userAgent; if (/OPR\/|Vivaldi|SamsungBrowser|YaBrowser/.test(ua)) return false;
    return /Edg\/|Chrome\/|Safari\//.test(ua);
  })();
  function ditar(id, btn) { return NAV_VOZ ? ditarVoz(id, btn) : ditarServidor(id, btn); }
  function ditarVoz(id, btn) {
    if (recAtual) { recAtual.__parar = true; try { recAtual.stop(); } catch (e) {} return; }
    const el = $(id); const base = el.value; const sep = el.tagName === 'TEXTAREA' ? '\n' : ' ';
    const norm = t => (t || '').toLowerCase().replace(/[^\p{L}\p{N} ]/gu, '').replace(/\s+/g, ' ').trim();
    const ERRO = { 'not-allowed': 'o navegador bloqueou o microfone — permita no cadeado ao lado do endereço', 'service-not-allowed': 'o navegador bloqueou o serviço de voz', 'audio-capture': 'nenhum microfone encontrado', 'network': 'o reconhecimento de voz precisa de internet', 'language-not-supported': 'pt-BR não suportado' };
    let finais = [], interim = '', vazias = 0, inicio = 0;
    const render = () => { const corpo = finais.concat(interim ? [interim] : []).join(' '); el.value = corpo ? (base.trim() ? base.replace(/\s+$/, '') + sep : '') + corpo : base; el.dispatchEvent(new Event('input')); };
    const addFinal = t => { t = (t || '').trim(); if (!t) return; if (finais.length && norm(finais[finais.length - 1]) === norm(t)) return; finais.push(t); vazias = 0; };
    const desligar = aviso => { btn.classList.remove('on'); btn.textContent = '🎤'; recAtual = null; interim = ''; render(); if (aviso) mostrarAlerta(aviso, 'warning'); else if (finais.length) { flash(el); mostrarAlerta('Ditado inserido — revise e, se quiser, clique em ✨'); } };
    const criar = () => {
      const r = new SR(); r.lang = 'pt-BR'; r.interimResults = true; r.continuous = false; r.maxAlternatives = 1;
      r.onstart = () => { inicio = Date.now(); };
      r.onresult = ev => { interim = ''; for (let i = ev.resultIndex; i < ev.results.length; i++) { const t = ev.results[i][0].transcript; if (ev.results[i].isFinal) addFinal(t); else interim += t; } render(); };
      r.onerror = ev => { if (ev.error === 'no-speech' || ev.error === 'aborted') return; r.__erro = 'Microfone: ' + (ERRO[ev.error] || ev.error); r.__parar = true; };
      r.onend = () => {
        if (recAtual !== r) return; if (r.__parar) { desligar(r.__erro); return; }
        if (Date.now() - inicio < 1500 && !interim) vazias++;
        if (vazias >= 4) { desligar('Microfone: o navegador encerra a escuta na hora. Verifique a permissão do microfone para este site.'); return; }
        interim = ''; render();
        try { const n = criar(); recAtual = n; n.start(); } catch (e) { desligar('Microfone: não foi possível continuar a escuta.'); }
      };
      return r;
    };
    const r = criar();
    try { r.start(); } catch (e) { mostrarAlerta('Não foi possível iniciar o microfone', 'warning'); return; }
    recAtual = r; btn.classList.add('on'); btn.textContent = '⏹'; mostrarAlerta('Gravando… fale e clique em ⏹ para parar', 'info');
  }
  function ditarServidor(id, btn) {
    if (recAtual) { recAtual.__parar = true; try { recAtual.stop(); } catch (e) {} return; }
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia || !window.MediaRecorder) { mostrarAlerta('Este navegador não permite gravar áudio', 'warning'); return; }
    const el = $(id);
    const tipo = ['audio/webm;codecs=opus', 'audio/webm', 'audio/ogg;codecs=opus', 'audio/mp4', ''].find(t => !t || (MediaRecorder.isTypeSupported && MediaRecorder.isTypeSupported(t)));
    const ERRO = { NotAllowedError: 'permita o microfone no cadeado ao lado do endereço', NotFoundError: 'nenhum microfone encontrado', NotReadableError: 'o microfone está em uso por outro programa', SecurityError: 'o site precisa estar em https' };
    navigator.mediaDevices.getUserMedia({ audio: true }).then(stream => {
      const r = tipo ? new MediaRecorder(stream, { mimeType: tipo }) : new MediaRecorder(stream);
      const partes = []; let inicio = Date.now(); let timer = null;
      const desligar = () => { btn.classList.remove('on'); btn.textContent = '🎤'; recAtual = null; clearInterval(timer); stream.getTracks().forEach(t => t.stop()); };
      r.ondataavailable = ev => { if (ev.data && ev.data.size) partes.push(ev.data); };
      r.onerror = () => { mostrarAlerta('Microfone: falha na gravação', 'danger'); desligar(); };
      r.onstop = async () => {
        const seg = (Date.now() - inicio) / 1000; desligar();
        if (seg < 0.7 || !partes.length) { mostrarAlerta('Gravação muito curta', 'warning'); return; }
        const blob = new Blob(partes, { type: r.mimeType || tipo || 'audio/webm' });
        const ext = /ogg/.test(blob.type) ? 'ogg' : /mp4/.test(blob.type) ? 'm4a' : 'webm';
        btn.disabled = true; btn.textContent = '…'; mostrarAlerta('Transcrevendo ' + Math.round(seg) + 's de áudio…', 'info');
        try {
          const fd = new FormData(); fd.append('audio', blob, 'ditado.' + ext); fd.append('campo', el.dataset.iaCampo || id);
          const resp = await API.iaTranscrever(fd);
          if (resp && resp.texto) { acrescentar(id, resp.texto); mostrarAlerta('Ditado inserido (' + resp.segundos + 's) — revise e, se quiser, clique em ✨'); }
          else mostrarAlerta('Não entendi nada no áudio — fale mais perto do microfone', 'warning');
        } catch (e) { mostrarAlerta('Transcrição: ' + e.message, 'danger'); }
        finally { btn.disabled = false; btn.textContent = '🎤'; }
      };
      r.start(1000); recAtual = r; btn.classList.add('on'); btn.textContent = '⏹'; inicio = Date.now();
      mostrarAlerta('Gravando… fale e clique em ⏹ para parar', 'info');
      timer = setInterval(() => { const t = Math.round((Date.now() - inicio) / 1000); btn.textContent = '⏹ ' + t + 's'; if (t >= 600) { try { r.stop(); } catch (e) {} } }, 1000);
    }).catch(e => mostrarAlerta('Microfone: ' + (ERRO[e && e.name] || (e && e.message) || 'não disponível'), 'warning'));
  }

  // ---------- corrigir ----------
  let corAlvo = null;
  async function corrigir(id) {
    const el = $(id); if (!el.value.trim()) { mostrarAlerta('Campo vazio — escreva, dite ou digite algo antes', 'warning'); return; }
    const btn = document.querySelector(`button[data-ia-cor="${id}"]`); if (btn) { btn.disabled = true; btn.textContent = '…'; }
    try {
      const r = await API.iaCorrigir(el.dataset.iaCampo || id, el.value);
      corAlvo = id; $('iaCorCampo').textContent = ROT[id] || id; $('iaCorAntes').value = el.value; $('iaCorDepois').value = r.texto || '';
      new bootstrap.Modal($('iaModalCorrigir')).show();
    } catch (e) { mostrarAlerta('IA: ' + e.message, 'danger'); }
    finally { if (btn) { btn.disabled = false; btn.textContent = '✨'; } }
  }

  // ---------- escrita à mão (MyScript iink) ----------
  let escAlvo = null, escCfg = null, pad = null, escTimer = null, escTextoAtual = '', iinkCarregando = null;
  function escStatus(t) { $('iaEscStatus').textContent = t; }
  function lerTexto(d) { d = d || {}; return d['text/plain'] || (d.exports && d.exports['text/plain']) || (d.rawResult && d.rawResult.exports && d.rawResult.exports['text/plain']) || ''; }
  function agendarExport() { clearTimeout(escTimer); escTimer = setTimeout(() => { if (!pad) return; try { (pad.export || pad.export_).call(pad, ['text/plain']); } catch (e) { try { (pad.export || pad.export_).call(pad); } catch (e2) {} } }, 1200); }
  function carregarIink() {
    if (window.iink) return Promise.resolve();
    if (!iinkCarregando) iinkCarregando = new Promise((ok, erro) => { const s = document.createElement('script'); s.src = 'https://unpkg.com/iink-ts/dist/iink.min.js'; s.onload = ok; s.onerror = () => erro(new Error('biblioteca de escrita não carregou (precisa de internet)')); document.head.appendChild(s); });
    return iinkCarregando;
  }
  async function criarPad() {
    const padEl = $('iinkPad');
    try { await carregarIink(); } catch (e) { escStatus(e.message + ' — use o teclado de escrita à mão do tablet'); return; }
    if (!escCfg) { try { escCfg = await API.iaEscritaConfig(); } catch (e) { escStatus(e.message); return; } }
    if (!padEl.dataset.ev) { padEl.dataset.ev = '1';
      padEl.addEventListener('exported', ev => { const t = lerTexto(ev.detail); if (t && t.trim()) { escTextoAtual = t.trim(); $('iaEscTexto').textContent = escTextoAtual; $('iaEscInserir').disabled = false; escStatus('texto reconhecido — continue ou clique em Inserir'); } });
      padEl.addEventListener('changed', () => { escStatus('reconhecendo…'); agendarExport(); });
      padEl.addEventListener('pointerup', agendarExport);
      padEl.addEventListener('error', ev => escStatus('erro: ' + ((ev.detail && ev.detail.message) || 'conexão com o MyScript'))); }
    const opts = { configuration: { server: { scheme: 'https', host: 'cloud.myscript.com', applicationKey: escCfg.applicationKey, hmacKey: escCfg.hmacKey },
      recognition: { type: 'TEXT', lang: escCfg.lang || 'pt_BR', text: { mimeTypes: ['text/plain'], guides: { enable: false } } } } };
    try { if (pad && pad.destroy) pad.destroy(); } catch (e) {}
    padEl.innerHTML = '';
    try {
      if (iink.Canvas && iink.Canvas.load) pad = iink.Canvas.load(padEl, 'INK_V2', opts);
      else if (iink.Editor && iink.Editor.load) pad = await iink.Editor.load(padEl, 'INKV2', opts);
      else { pad = new iink.Editor(padEl, opts); if (pad.initialize) await pad.initialize(); }
      escStatus('pronto — escreva no quadro');
    } catch (e) { escStatus('não foi possível iniciar o quadro: ' + (e && e.message || e)); }
  }
  function abrirEscrita(id) { escAlvo = id; escTextoAtual = ''; $('iaEscTexto').textContent = ''; $('iaEscInserir').disabled = true; $('iaEscCampo').textContent = ROT[id] || id; bootstrap.Modal.getOrCreateInstance($('iaModalEscrita')).show(); }

  // ---------- pesquisa ----------
  let pesqCtx = null;
  window.iaPesquisar = function (tipo, texto, veiculo, km) {
    preparar(); pesqCtx = { tipo, veiculo: veiculo || {}, km: km || null };
    $('iaPesqTitulo').textContent = tipo === 'peca' ? '🔎 Pesquisar código de peça' : '🔎 Pesquisar problema';
    $('iaPesqVeic').textContent = 'Veículo: ' + ([veiculo.marca, veiculo.modelo, veiculo.ano, veiculo.combustivel].filter(Boolean).join(' ') || 'não informado') + (km ? ' · ' + Number(km).toLocaleString('pt-BR') + ' km' : '');
    $('iaPesqTexto').value = texto || ''; $('iaPesqResp').innerHTML = '';
    bootstrap.Modal.getOrCreateInstance($('iaModalPesq')).show();
    if (texto && texto.trim().length >= 3) executarPesquisa(); else setTimeout(() => $('iaPesqTexto').focus(), 300);
  };
  async function executarPesquisa() {
    const t = $('iaPesqTexto').value.trim(); if (t.length < 3) return;
    const b = $('iaPesqBtn'); b.disabled = true; $('iaPesqResp').innerHTML = '<div class="text-muted"><span class="spinner-border spinner-border-sm me-2"></span>Pesquisando…</div>';
    try { const r = await API.iaPesquisar({ tipo: pesqCtx.tipo, texto: t, veiculo: pesqCtx.veiculo, km: pesqCtx.km }); $('iaPesqResp').innerHTML = mdSimples(r.resposta); }
    catch (e) { $('iaPesqResp').innerHTML = '<div class="text-danger"></div>'; $('iaPesqResp').firstChild.textContent = 'IA: ' + e.message; }
    finally { b.disabled = false; }
  }
  function mdSimples(md) { // markdown mínimo e seguro: títulos, negrito, listas, parágrafos
    const e = esc(md || '');
    return e.split('\n').map(l => {
      if (/^#{1,3}\s/.test(l)) return '<h3>' + l.replace(/^#{1,3}\s/, '') + '</h3>';
      if (/^\s*[-*]\s/.test(l)) return '<div>• ' + l.replace(/^\s*[-*]\s/, '') + '</div>';
      if (/^\s*\d+[.)]\s/.test(l)) return '<div>' + l + '</div>';
      return l.trim() ? '<div>' + l + '</div>' : '<div style="height:.4rem"></div>';
    }).join('').replace(/\*\*(.+?)\*\*/g, '<b>$1</b>').replace(/`(.+?)`/g, '<code>$1</code>');
  }
})();
