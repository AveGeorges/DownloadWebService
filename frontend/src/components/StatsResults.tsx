import type { CalculationResult } from "../api/client";

type Props = {
  result: CalculationResult | null;
  error: string | null;
};

const DIGITS = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"];

export function StatsResults({ result, error }: Props) {
  if (!result && !error) {
    return null;
  }

  return (
    <section className="panel">
      <h2>Результаты расчётов</h2>
      {error ? <p className="err">{error}</p> : null}
      {result ? (
        <>
          <h3>Общая статистика</h3>
          <div className="stats-grid">
            {DIGITS.map((digit) => (
              <div key={digit} className="stat-cell">
                <span className="stat-digit">{digit}</span>
                <span className="stat-value">{result.total[digit] ?? 0}</span>
              </div>
            ))}
          </div>

          <h3>По файлам</h3>
          <div className="table-wrap">
            <table className="files-table">
              <thead>
                <tr>
                  <th>Файл</th>
                  {DIGITS.map((digit) => (
                    <th key={digit}>{digit}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {result.per_file.map((row) => (
                  <tr key={row.file_id}>
                    <td>{row.filename}</td>
                    {DIGITS.map((digit) => (
                      <td key={digit}>{row.counts[digit] ?? 0}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {result.errors.length > 0 ? (
            <ul className="err-list">
              {result.errors.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          ) : null}
        </>
      ) : null}
    </section>
  );
}
