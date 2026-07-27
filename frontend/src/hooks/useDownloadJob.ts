import { useCallback, useEffect, useRef, useState } from "react";

import { getDownloadJob, startDownloadJob, type DownloadJob } from "../api/client";
import { isJobActive } from "../utils/time";

const STORAGE_KEY = "dws.activeJobId";

export function useDownloadJob(onCompleted?: () => void) {
  const [job, setJob] = useState<DownloadJob | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [starting, setStarting] = useState(false);
  const onCompletedRef = useRef(onCompleted);
  onCompletedRef.current = onCompleted;

  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (!saved) {
      return;
    }
    void getDownloadJob(saved)
      .then((loaded) => {
        setJob(loaded);
        if (!isJobActive(loaded.status)) {
          localStorage.removeItem(STORAGE_KEY);
        }
      })
      .catch(() => {
        localStorage.removeItem(STORAGE_KEY);
      });
  }, []);

  useEffect(() => {
    if (!job || !isJobActive(job.status)) {
      return;
    }

    const timer = window.setInterval(() => {
      void getDownloadJob(job.id)
        .then((next) => {
          setJob(next);
          setError(null);
          if (!isJobActive(next.status)) {
            localStorage.removeItem(STORAGE_KEY);
            if (next.status === "completed") {
              onCompletedRef.current?.();
            }
          }
        })
        .catch((err: unknown) => {
          setError(err instanceof Error ? err.message : "Ошибка опроса статуса");
        });
    }, 1500);

    return () => window.clearInterval(timer);
  }, [job]);

  const start = useCallback(async () => {
    setStarting(true);
    setError(null);
    try {
      const created = await startDownloadJob();
      localStorage.setItem(STORAGE_KEY, created.id);
      setJob(created);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось стартовать скачивание");
    } finally {
      setStarting(false);
    }
  }, []);

  const active = job ? isJobActive(job.status) : false;

  return { job, error, starting, active, start };
}
