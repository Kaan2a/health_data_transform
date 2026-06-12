import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { api } from "../lib/api";
import Button from "../components/ui/Button";

interface SubmissionEntry {
  id: string;
  source_row_number: number | null;
  resource_type: string;
  resource_identifier: string | null;
  status: string;
  http_status: number | null;
  location: string | null;
  operation_outcome: any;
  error_message: string | null;
}

interface SubmissionDetail {
  id: string;
  project_id: string;
  fhir_server_url: string;
  bundle_type: string;
  bundle_count: number;
  resource_count: number;
  success_count: number;
  failure_count: number;
  status: string;
  progress: number;
  error_message: string | null;
  started_at: string | null;
  completed_at: string | null;
}

export default function SubmissionDetailPage() {
  const { projectId, submissionId } = useParams<{
    projectId: string;
    submissionId: string;
  }>();
  const [submission, setSubmission] = useState<SubmissionDetail | null>(null);
  const [entries, setEntries] = useState<SubmissionEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [retrying, setRetrying] = useState(false);

  const load = async () => {
    if (!submissionId) return;
    try {
      const [subResp, entriesResp] = await Promise.all([
        api.get(`/submissions/${submissionId}`),
        api.get(`/submissions/${submissionId}/entries`),
      ]);
      setSubmission((subResp.data as any).data || subResp.data);
      setEntries((entriesResp.data as any).data || entriesResp.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [submissionId]);

  const handleRetry = async () => {
    if (!submissionId) return;
    setRetrying(true);
    try {
      await api.post(`/submissions/${submissionId}/retry`);
      // Reload after a delay
      setTimeout(load, 2000);
    } catch (err) {
      console.error(err);
    } finally {
      setRetrying(false);
    }
  };

  const handleDownloadErrorReport = async () => {
    if (!submissionId) return;
    try {
      const resp = await api.get(`/submissions/${submissionId}/error-report`);
      const data = (resp.data as any).data || resp.data;
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `error_report_${submissionId}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error(err);
    }
  };

  if (loading) {
    return <div className="py-12 text-center text-slate-500">Yükleniyor...</div>;
  }

  if (!submission) {
    return <div className="py-12 text-center text-red-500">Gönderim bulunamadı.</div>;
  }

  const successRate = submission.resource_count > 0
    ? Math.round((submission.success_count / submission.resource_count) * 100)
    : 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-slate-900">Gönderim Detayı</h2>
          <p className="text-sm text-slate-500 font-mono">{submission.id}</p>
        </div>
        <div className="flex gap-2">
          {submission.failure_count > 0 && (
            <Button variant="secondary" onClick={handleDownloadErrorReport}>
              Hata Raporu İndir
            </Button>
          )}
          {(submission.status === "failed" || submission.status === "completed_with_errors") && (
            <Button onClick={handleRetry} isLoading={retrying}>
              Yeniden Gönder
            </Button>
          )}
          <Link to={`/projects/${projectId}/submissions`}>
            <Button variant="secondary">← Geri</Button>
          </Link>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-xl border border-slate-200 p-4">
          <p className="text-sm text-slate-500">Toplam Kaynak</p>
          <p className="text-2xl font-bold text-slate-900">{submission.resource_count}</p>
        </div>
        <div className="bg-white rounded-xl border border-emerald-200 p-4">
          <p className="text-sm text-emerald-600">Başarılı</p>
          <p className="text-2xl font-bold text-emerald-700">{submission.success_count}</p>
        </div>
        <div className="bg-white rounded-xl border border-red-200 p-4">
          <p className="text-sm text-red-600">Hatalı</p>
          <p className="text-2xl font-bold text-red-700">{submission.failure_count}</p>
        </div>
        <div className="bg-white rounded-xl border border-slate-200 p-4">
          <p className="text-sm text-slate-500">Başarı Oranı</p>
          <p className="text-2xl font-bold text-indigo-700">%{successRate}</p>
        </div>
      </div>

      {/* Progress bar */}
      {submission.status === "sending" && (
        <div className="bg-white rounded-xl border border-slate-200 p-4">
          <p className="text-sm text-slate-600 mb-2">Gönderim İlerleme</p>
          <div className="w-full bg-slate-200 rounded-full h-3">
            <div
              className="bg-indigo-600 h-3 rounded-full transition-all duration-300"
              style={{ width: `${submission.progress}%` }}
            />
          </div>
          <p className="text-xs text-slate-500 mt-1 text-right">%{submission.progress}</p>
        </div>
      )}

      {/* Submission Info */}
      <div className="bg-white rounded-xl border border-slate-200 p-4 space-y-2">
        <h3 className="font-medium text-slate-900">Gönderim Bilgileri</h3>
        <div className="grid grid-cols-2 gap-2 text-sm">
          <div className="text-slate-500">Hedef FHIR Sunucusu</div>
          <div className="text-slate-900 font-mono text-xs">{submission.fhir_server_url}</div>
          <div className="text-slate-500">Bundle Türü</div>
          <div className="text-slate-900 capitalize">{submission.bundle_type}</div>
          <div className="text-slate-500">Bundle Sayısı</div>
          <div className="text-slate-900">{submission.bundle_count}</div>
          <div className="text-slate-500">Durum</div>
          <div className="text-slate-900 capitalize">{submission.status.replace(/_/g, " ")}</div>
          {submission.started_at && (
            <>
              <div className="text-slate-500">Başlangıç</div>
              <div className="text-slate-900">{new Date(submission.started_at).toLocaleString("tr-TR")}</div>
            </>
          )}
          {submission.completed_at && (
            <>
              <div className="text-slate-500">Tamamlanma</div>
              <div className="text-slate-900">{new Date(submission.completed_at).toLocaleString("tr-TR")}</div>
            </>
          )}
        </div>
      </div>

      {/* Entries table */}
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
        <h3 className="font-medium text-slate-900 px-4 py-3 border-b border-slate-200">
          Kaynak Sonuçları ({entries.length})
        </h3>
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-50 border-b border-slate-200 text-slate-600">
            <tr>
              <th className="px-4 py-2 font-medium">Satır</th>
              <th className="px-4 py-2 font-medium">Kaynak Tipi</th>
              <th className="px-4 py-2 font-medium">Durum</th>
              <th className="px-4 py-2 font-medium">HTTP</th>
              <th className="px-4 py-2 font-medium">Hata</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {entries.slice(0, 100).map((e) => (
              <tr key={e.id} className="hover:bg-slate-50/50">
                <td className="px-4 py-2 text-slate-500">{e.source_row_number ?? "-"}</td>
                <td className="px-4 py-2 font-medium">{e.resource_type}</td>
                <td className="px-4 py-2">
                  <span
                    className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                      e.status === "success"
                        ? "bg-emerald-100 text-emerald-700"
                        : "bg-red-100 text-red-700"
                    }`}
                  >
                    {e.status}
                  </span>
                </td>
                <td className="px-4 py-2 text-slate-500">{e.http_status ?? "-"}</td>
                <td className="px-4 py-2 text-red-600 text-xs truncate max-w-[250px]">
                  {e.error_message || "-"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {entries.length > 100 && (
          <div className="px-4 py-3 text-center text-sm text-slate-500 border-t border-slate-200">
            İlk 100 kayıt gösteriliyor. Tam rapor için hata raporu indirin.
          </div>
        )}
      </div>
    </div>
  );
}
