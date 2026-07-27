import { useCallback, useState } from "react";

import { calculateStats, selectAllFileIds, type CalculationResult } from "./api/client";
import { DownloadProgress } from "./components/DownloadProgress";
import { FilesTable } from "./components/FilesTable";
import { FilesToolbar } from "./components/FilesToolbar";
import { Header } from "./components/Header";
import { StatsResults } from "./components/StatsResults";
import { useDownloadJob } from "./hooks/useDownloadJob";
import { useFiles } from "./hooks/useFiles";

export function App() {
  const [reloadToken, setReloadToken] = useState(0);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [calcResult, setCalcResult] = useState<CalculationResult | null>(null);
  const [calcError, setCalcError] = useState<string | null>(null);
  const [calculating, setCalculating] = useState(false);

  const refreshFiles = useCallback(() => {
    setReloadToken((value) => value + 1);
  }, []);

  const download = useDownloadJob(refreshFiles);
  const files = useFiles(reloadToken);

  const toggleOne = (id: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const togglePage = (checked: boolean) => {
    setSelected((prev) => {
      const next = new Set(prev);
      for (const item of files.items) {
        if (checked) {
          next.add(item.id);
        } else {
          next.delete(item.id);
        }
      }
      return next;
    });
  };

  const selectAll = async () => {
    try {
      const ids = await selectAllFileIds();
      setSelected(new Set(ids));
    } catch (err) {
      setCalcError(err instanceof Error ? err.message : "Не удалось выбрать все файлы");
    }
  };

  const runCalculations = async () => {
    setCalculating(true);
    setCalcError(null);
    try {
      const result = await calculateStats([...selected]);
      setCalcResult(result);
    } catch (err) {
      setCalcResult(null);
      setCalcError(err instanceof Error ? err.message : "Ошибка расчётов");
    } finally {
      setCalculating(false);
    }
  };

  return (
    <main className="page">
      <Header
        downloading={download.active}
        starting={download.starting}
        onDownload={() => void download.start()}
      />

      <DownloadProgress job={download.job} error={download.error} />

      <section className="panel">
        <h1>Скачанные файлы</h1>
        <p className="muted">Сортировка по времени скачивания. Время показано по Новосибирску (НСК).</p>

        <FilesToolbar
          selectedCount={selected.size}
          total={files.total}
          page={files.page}
          pageCount={files.pageCount}
          calculating={calculating}
          onSelectAll={() => void selectAll()}
          onClear={() => setSelected(new Set())}
          onPrev={() => files.setPage(Math.max(0, files.page - 1))}
          onNext={() => files.setPage(Math.min(files.pageCount - 1, files.page + 1))}
          onCalculate={() => void runCalculations()}
        />

        {files.error ? <p className="err">{files.error}</p> : null}

        <FilesTable
          items={files.items}
          selected={selected}
          onToggle={toggleOne}
          onTogglePage={togglePage}
          loading={files.loading}
        />
      </section>

      <StatsResults result={calcResult} error={calcError} />
    </main>
  );
}
