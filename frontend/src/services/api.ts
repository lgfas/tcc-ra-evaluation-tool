export interface User { id: number; name: string; email: string }
export class ApiError extends Error {
  constructor(public status: number, message: string) { super(message); }
}
function describeError(data: unknown): string {
  if (typeof data === 'string') return data;
  if (Array.isArray(data)) return data.map(describeError).join(' ');
  if (data && typeof data === 'object') {
    const labels: Record<string, string> = { name: 'Nome', email: 'E-mail', password: 'Senha', visibility: 'Visibilidade', initial_version: 'Primeira versão', version: 'Versão', description_markdown: 'Descrição', element_type_id: 'Tipo arquitetural', ra_version: 'Versão do elemento', reference_architecture_id: 'Arquitetura' };
    return Object.entries(data).map(([key, value]) =>
      `${labels[key] ? labels[key] + ': ' : ''}${describeError(value)}`).join(' ');
  }
  return 'Não foi possível concluir a solicitação.';
}
export async function api<T>(path: string, method = 'GET', body?: unknown): Promise<T> {
  try {
    const headers: Record<string, string> = { Accept: 'application/json' };
    if (method !== 'GET') {
      // Um token novo considera a rotação realizada pelo Django no login.
      const csrf = await api<{csrfToken: string}>('/auth/csrf/');
      headers['X-CSRFToken'] = csrf.csrfToken;
      headers['Content-Type'] = 'application/json';
    }
    const response = await fetch(`/api${path}`, { method, headers, credentials: 'same-origin',
      body: body === undefined ? undefined : JSON.stringify(body) });
    if (!response.ok) {
      const data: unknown = await response.json().catch(() => null);
      throw new ApiError(response.status, data ? describeError(data) : 'Serviço indisponível. Tente novamente.');
    }
    return response.status === 204 ? undefined as T : await response.json() as T;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    throw new Error('Não foi possível conectar ao servidor. Verifique sua conexão e tente novamente.');
  }
}
