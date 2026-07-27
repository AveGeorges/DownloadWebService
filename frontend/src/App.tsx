import { useEffect, useState } from "react";

type HealthPayload = {
  status: string;
  version: string;
  app: string;
};

export function App() {
  const [health, setHealth] = useState<HealthPayload | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadHealth() {
      try {
        const response = await fetch("/health");
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }
        const payload = (await response.json()) as HealthPayload;
        if (!cancelled) {
          setHealth(payload);
          setError(null);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Unknown error");
        }
      }
    }

    void loadHealth();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <main className="page">
      <header className="header">
        <p className="brand">Download Web Service</p>
        <button type="button" className="download-btn" disabled>
          Скачать данные
        </button>
      </header>

      <section className="panel">
        <h1>Каркас проекта (этап 0)</h1>
        <p>
          Backend, worker, Postgres, Redis, RabbitMQ и Nginx подняты через Docker Compose. Бизнес-логика
          скачивания появится на следующих этапах.
        </p>
        {health ? (
          <p className="ok">
            API: {health.app} v{health.version} — {health.status}
          </p>
        ) : null}
        {error ? <p className="err">Не удалось проверить /health: {error}</p> : null}
      </section>
    </main>
  );
}
