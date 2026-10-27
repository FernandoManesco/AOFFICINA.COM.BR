// aOfficina — utilitários de UI compartilhados pelas telas (campos de dinheiro, cabeçalho de página, busca com atraso)
function reaisParaCent(v) { const n = parseFloat(String(v ?? '').replace(',', '.')); return isNaN(n) ? 0 : Math.round(n * 100); }
function centParaReais(c) { return (Number(c || 0) / 100).toFixed(2); }
function debounce(fn, ms = 300) { let t; return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); }; }
function badgeStatus(s) {
  const cor = { ABERTO: 'secondary', ENVIADO: 'info', APROVADO: 'primary', RECUSADO: 'dark', EM_EXECUCAO: 'warning', AGUARDANDO_PECA: 'warning',
    CONCLUIDO: 'success', ENTREGUE: 'success', FATURADO: 'success', CANCELADO: 'danger',
    AGENDADO: 'secondary', CONFIRMADO: 'info', CHEGOU: 'primary', FALTOU: 'dark' }[s] || 'secondary';
  return `<span class="badge text-bg-${cor}">${esc(String(s || '').replace('_', ' '))}</span>`;
}
function hojeISO() { const d = new Date(); return new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 10); }
function isoLocal(d) { return new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 16); }
function minutosParaTexto(m) { m = Number(m || 0); const h = Math.floor(m / 60), r = m % 60; return h ? (r ? `${h}h${String(r).padStart(2, '0')}` : `${h}h`) : `${r}min`; }
function confirmar(msg) { return window.confirm(msg); }
