import { useCallback, useEffect, useState } from "react";

import { listFiles, type DownloadedFile } from "../api/client";

const PAGE_SIZE = 10;

export function useFiles(reloadToken = 0) {
  const [items, setItems] = useState<DownloadedFile[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async (pageIndex: number) => {
    setLoading(true);
    setError(null);
    try {
      const data = await listFiles(PAGE_SIZE, pageIndex * PAGE_SIZE);
      setItems(data.items);
      setTotal(data.total);
      setPage(pageIndex);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка загрузки файлов");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load(page);
  }, [load, page, reloadToken]);

  const pageCount = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return {
    items,
    total,
    page,
    pageCount,
    pageSize: PAGE_SIZE,
    loading,
    error,
    setPage,
    reload: () => void load(page),
  };
}
