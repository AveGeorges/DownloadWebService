import type { DownloadedFile } from "../api/client";
import { formatNsk } from "../utils/time";

type Props = {
  items: DownloadedFile[];
  selected: Set<string>;
  onToggle: (id: string) => void;
  onTogglePage: (checked: boolean) => void;
  loading: boolean;
};

export function FilesTable({ items, selected, onToggle, onTogglePage, loading }: Props) {
  const pageIds = items.map((item) => item.id);
  const allPageSelected = pageIds.length > 0 && pageIds.every((id) => selected.has(id));

  return (
    <div className="table-wrap">
      <table className="files-table">
        <thead>
          <tr>
            <th>
              <input
                type="checkbox"
                checked={allPageSelected}
                onChange={(event) => onTogglePage(event.target.checked)}
                aria-label="Выбрать все на странице"
                disabled={loading || items.length === 0}
              />
            </th>
            <th>Имя файла</th>
            <th>Время скачивания (НСК)</th>
          </tr>
        </thead>
        <tbody>
          {items.length === 0 ? (
            <tr>
              <td colSpan={3} className="muted">
                {loading ? "Загрузка…" : "Файлов пока нет. Нажмите «Скачать данные»."}
              </td>
            </tr>
          ) : (
            items.map((item) => (
              <tr key={item.id}>
                <td>
                  <input
                    type="checkbox"
                    checked={selected.has(item.id)}
                    onChange={() => onToggle(item.id)}
                    aria-label={`Выбрать ${item.filename}`}
                  />
                </td>
                <td>{item.filename}</td>
                <td>{formatNsk(item.downloaded_at)}</td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
