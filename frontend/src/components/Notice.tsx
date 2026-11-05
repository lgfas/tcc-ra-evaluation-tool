export default function Notice({ message, error = false }: {message: string; error?: boolean}) {
  return <p className={error ? 'notice error' : 'notice'} role={error ? 'alert' : 'status'}>{message}</p>;
}
