import type { DownloadJob } from "../api/client";
import { formatNsk } from "../utils/time";

type Props = {
  job: DownloadJob | null;
  error: string | null;
};

export function DownloadProgress({ job, error }: Props) {
  if (!job && !error) {
    return null;
  }

  const names = job?.names_received ?? 0;
  const downloaded = job?.downloaded_count ?? 0;
  const inFlight = names > downloaded;

  return (
    <section className="panel progress-panel" aria-live="polite">
      <h2>Скачивание</h2>
      {job ? (
        <>
          <p>
            Старт (НСК): <strong>{formatNsk(job.started_at)}</strong>
          </p>
          <p>
            Получено <strong>{names}</strong> названий файлов,{" "}
            {inFlight ? "скачиваю" : "скачано"}{" "}
            <strong>
              {downloaded} из {names || "—"}
            </strong>
          </p>
          <p className="muted">
            Статус: {job.status}
            {job.error ? ` — ${job.error}` : ""}
          </p>
        </>
      ) : null}
      {error ? <p className="err">{error}</p> : null}
    </section>
  );
}
