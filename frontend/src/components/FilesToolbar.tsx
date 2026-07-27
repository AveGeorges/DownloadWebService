type Props = {
  selectedCount: number;
  total: number;
  page: number;
  pageCount: number;
  calculating: boolean;
  onSelectAll: () => void;
  onClear: () => void;
  onPrev: () => void;
  onNext: () => void;
  onCalculate: () => void;
};

export function FilesToolbar({
  selectedCount,
  total,
  page,
  pageCount,
  calculating,
  onSelectAll,
  onClear,
  onPrev,
  onNext,
  onCalculate,
}: Props) {
  return (
    <div className="toolbar">
      <div className="toolbar-group">
        <button type="button" className="ghost-btn" onClick={onSelectAll}>
          Выбрать все
        </button>
        <button type="button" className="ghost-btn" onClick={onClear} disabled={selectedCount === 0}>
          Снять выбор
        </button>
        <span className="muted">
          Выбрано: {selectedCount}
          {total ? ` / ${total}` : ""}
        </span>
      </div>
      <div className="toolbar-group">
        <button type="button" className="ghost-btn" onClick={onPrev} disabled={page <= 0}>
          Назад
        </button>
        <span className="muted">
          {page + 1} / {pageCount}
        </span>
        <button
          type="button"
          className="ghost-btn"
          onClick={onNext}
          disabled={page + 1 >= pageCount}
        >
          Вперёд
        </button>
        <button
          type="button"
          className="primary-btn"
          onClick={onCalculate}
          disabled={selectedCount === 0 || calculating}
        >
          {calculating ? "Считаем…" : "Произвести расчёты"}
        </button>
      </div>
    </div>
  );
}
