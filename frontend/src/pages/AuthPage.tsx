import { useState, type FormEvent } from 'react';
import { api, type User } from '../services/api';
import Notice from '../components/Notice';
export default function AuthPage({ onLogin }: {onLogin: (user: User) => void}) {
  const [register, setRegister] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const values = new FormData(form);
    setBusy(true); setError(''); setMessage('');
    try {
      const body = { email: values.get('email'), password: values.get('password'),
        ...(register ? { name: values.get('name') } : {}) };
      const user = await api<User>(register ? '/auth/register/' : '/auth/login/', 'POST', body);
      form.reset();
      if (register) { setRegister(false); setMessage('Conta criada. Entre com seu e-mail e senha.'); }
      else onLogin(user);
    } catch (err) { setError(err instanceof Error ? err.message : 'Ocorreu um erro.'); }
    finally { setBusy(false); }
  }
  return <section className="card"><h1>{register ? 'Criar conta' : 'Entrar'}</h1>
    <p>{register ? 'Cadastre-se para acessar a ferramenta.' : 'Acesse sua conta para continuar.'}</p>
    {message && <Notice message={message} />}{error && <Notice message={error} error />}
    <form onSubmit={submit}>
      {register && <label>Nome<input name="name" autoComplete="name" required maxLength={150} /></label>}
      <label>E-mail<input name="email" type="email" autoComplete="email" required maxLength={254} /></label>
      <label>Senha<input name="password" type="password" autoComplete={register ? 'new-password' : 'current-password'} required minLength={register ? 8 : undefined} maxLength={128} /></label>
      {register && <small>Use ao menos 8 caracteres. Evite senhas comuns, apenas números ou semelhantes aos seus dados.</small>}
      <button disabled={busy}>{busy ? 'Aguarde…' : register ? 'Criar conta' : 'Entrar'}</button>
    </form>
    <button className="secondary" disabled={busy} onClick={() => {setRegister(!register); setError(''); setMessage('');}}>
      {register ? 'Voltar para login' : 'Criar uma conta'}</button>
  </section>;
}
