import type { ReactNode } from "react";

interface Column<T> {
  key: string;
  header: string | ReactNode;
  render?: (item: T, index: number) => ReactNode;
  className?: string;
}

interface TableProps<T> {
  columns: Column<T>[];
  data: T[];
  keyExtractor?: (item: T, index: number) => string;
  emptyMessage?: string;
  maxHeight?: string;
}

export default function Table<T extends Record<string, unknown>>({
  columns,
  data,
  keyExtractor,
  emptyMessage = "Veri bulunamadı.",
  maxHeight = "400px",
}: TableProps<T>) {
  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center py-12 text-sm text-slate-400">
        {emptyMessage}
      </div>
    );
  }

  return (
    <div
      className="overflow-auto rounded-lg border border-slate-200 shadow-sm"
      style={{ maxHeight }}
      id="data-table-container"
    >
      <table className="min-w-full divide-y divide-slate-200">
        <thead className="bg-slate-50 sticky top-0 z-10">
          <tr>
            {columns.map((col) => (
              <th
                key={col.key}
                scope="col"
                className={`
                  px-4 py-3 text-left text-xs font-semibold
                  text-slate-600 uppercase tracking-wider
                  whitespace-nowrap border-b border-slate-200
                  bg-slate-50
                  ${col.className ?? ""}
                `}
              >
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-slate-100">
          {data.map((item, rowIdx) => (
            <tr
              key={keyExtractor ? keyExtractor(item, rowIdx) : rowIdx}
              className="hover:bg-indigo-50/30 transition-colors duration-100"
            >
              {columns.map((col) => (
                <td
                  key={col.key}
                  className={`
                    px-4 py-2.5 text-sm text-slate-700
                    whitespace-nowrap
                    ${col.className ?? ""}
                  `}
                >
                  {col.render
                    ? col.render(item, rowIdx)
                    : String(item[col.key] ?? "")}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
