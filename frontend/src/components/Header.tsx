type HeaderProps = {
  downloading: boolean;
  starting: boolean;
  onDownload: () => void;
};

export function Header({ downloading, starting, onDownload }: HeaderProps) {
  const disabled = downloading || starting;

  return (
    <header className="header">
      <div>
        <p className="brand">Download Web Service</p>
        <p className="tagline">Каталог файлов и статистика по цифрам</p>
      </div>
      <button
        type="button"
        className="download-btn"
        disabled={disabled}
        onClick={onDownload}
      >
        {starting ? "Запуск…" : downloading ? "Скачивание…" : "Скачать данные"}
      </button>
    </header>
  );
}
