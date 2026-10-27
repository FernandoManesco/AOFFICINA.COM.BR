// aOfficina — camada de API. Mesmo padrão do WebHomeCare: API_URL + apiCall + objeto API.
const API_URL = (location.hostname === 'localhost' || location.hostname === '127.0.0.1')
  ? 'http://127.0.0.1:8300'
  : 'https://api.' + location.hostname.replace(/^app\./, '');

async function apiCall(caminho, opcoes = {}) {
  const token = localStorage.getItem('token');
  const cab = { 'Content-Type': 'application/json', ...(opcoes.headers || {}) };
  if (token) cab['Authorization'] = 'Bearer ' + token;
  const resp = await fetch(API_URL + caminho, { ...opcoes, headers: cab });
  if (resp.status === 401 && !caminho.startsWith('/auth/login')) {
    localStorage.removeItem('token');
    location.href = '/index.html?expirou=1';
    throw new Error('Sessão expirada');
  }
  let dados = null;
  try { dados = await resp.json(); } catch (_) { dados = null; }
  if (!resp.ok) {
    const msg = (dados && (dados.detail || dados.error)) || ('Erro ' + resp.status);
    throw new Error(typeof msg === 'string' ? msg : JSON.stringify(msg));
  }
  return dados;
}

const _qs = (o) => {
  const p = Object.entries(o || {}).filter(([, v]) => v !== undefined && v !== null && v !== '');
  return p.length ? '?' + new URLSearchParams(p).toString() : '';
};
const _post = (c, b) => apiCall(c, { method: 'POST', body: JSON.stringify(b || {}) });
const _put = (c, b) => apiCall(c, { method: 'PUT', body: JSON.stringify(b || {}) });
const _patch = (c, b) => apiCall(c, { method: 'PATCH', body: b ? JSON.stringify(b) : undefined });
const _del = (c) => apiCall(c, { method: 'DELETE' });

const API = {
  // auth
  login: (login, senha) => _post('/auth/login', { login, senha }),
  me: () => apiCall('/auth/me'),
  trocarSenha: (senha_atual, senha_nova) => _post('/auth/trocar-senha', { senha_atual, senha_nova }),
  // empresa / oficinas / recursos
  getEmpresa: () => apiCall('/empresa'),
  putEmpresa: (d) => _put('/empresa', d),
  getOficinas: () => apiCall('/empresa/oficinas'),
  criarOficina: (d) => _post('/empresa/oficinas', d),
  editarOficina: (id, d) => _put('/empresa/oficinas/' + id, d),
  getFuncionarios: (f) => apiCall('/empresa/funcionarios' + _qs(f)),
  criarFuncionario: (d) => _post('/empresa/funcionarios', d),
  editarFuncionario: (id, d) => _put('/empresa/funcionarios/' + id, d),
  getEquipamentos: (f) => apiCall('/empresa/equipamentos' + _qs(f)),
  criarEquipamento: (d) => _post('/empresa/equipamentos', d),
  editarEquipamento: (id, d) => _put('/empresa/equipamentos/' + id, d),
  // clientes / veículos
  getClientes: (f) => apiCall('/clientes' + _qs(f)),
  getCliente: (id) => apiCall('/clientes/' + id),
  criarCliente: (d) => _post('/clientes', d),
  editarCliente: (id, d) => _put('/clientes/' + id, d),
  inativarCliente: (id) => _del('/clientes/' + id),
  getVeiculos: (f) => apiCall('/veiculos' + _qs(f)),
  getVeiculoPorPlaca: (placa) => apiCall('/veiculos/placa/' + encodeURIComponent(placa)),
  criarVeiculo: (d) => _post('/veiculos', d),
  editarVeiculo: (id, d) => _put('/veiculos/' + id, d),
  inativarVeiculo: (id) => _del('/veiculos/' + id),
  // catálogo
  getMarcas: (tipo = 1) => apiCall('/catalogo/marcas' + _qs({ tipo })),
  getModelos: (marcaId, q) => apiCall('/catalogo/marcas/' + marcaId + '/modelos' + _qs({ q })),
  getAnos: (modeloId) => apiCall('/catalogo/modelos/' + modeloId + '/anos'),
  buscarCatalogo: (q, tipo = 1) => apiCall('/catalogo/buscar' + _qs({ q, tipo })),
  // agenda
  getAgenda: (f) => apiCall('/agenda' + _qs(f)),
  getDisponibilidade: (oficina_id, dia) => apiCall('/agenda/disponibilidade' + _qs({ oficina_id, dia })),
  criarAgenda: (d) => _post('/agenda', d),
  editarAgenda: (id, d) => _put('/agenda/' + id, d),
  statusAgenda: (id, status) => _patch('/agenda/' + id + '/status' + _qs({ status })),
  // peças / serviços
  getPecas: (f) => apiCall('/pecas' + _qs(f)),
  criarPeca: (d) => _post('/pecas', d),
  editarPeca: (id, d) => _put('/pecas/' + id, d),
  getServicos: (f) => apiCall('/servicos' + _qs(f)),
  criarServico: (d) => _post('/servicos', d),
  editarServico: (id, d) => _put('/servicos/' + id, d),
  // pedidos
  getPedidos: (f) => apiCall('/pedidos' + _qs(f)),
  getPedido: (id) => apiCall('/pedidos/' + id),
  criarPedido: (d) => _post('/pedidos', d),
  editarPedido: (id, d) => _put('/pedidos/' + id, d),
  addServicoPedido: (id, d) => _post('/pedidos/' + id + '/servicos', d),
  editServicoPedido: (id, item, d) => _put('/pedidos/' + id + '/servicos/' + item, d),
  delServicoPedido: (id, item) => _del('/pedidos/' + id + '/servicos/' + item),
  execServicoPedido: (id, item, d) => _patch('/pedidos/' + id + '/servicos/' + item + '/execucao', d),
  addPecaPedido: (id, d) => _post('/pedidos/' + id + '/pecas', d),
  editPecaPedido: (id, item, d) => _put('/pedidos/' + id + '/pecas/' + item, d),
  delPecaPedido: (id, item) => _del('/pedidos/' + id + '/pecas/' + item),
  aprovarPedido: (id, d) => _post('/pedidos/' + id + '/aprovar', d),
  statusPedido: (id, status) => _post('/pedidos/' + id + '/status' + _qs({ status })),
};
