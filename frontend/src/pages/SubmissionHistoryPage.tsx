import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { api } from "../lib/api";
import Button from "../components/ui/Button";

interface Submission {
  id: string;
  project_id: string;
  job_id: string | null;
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
  created_at: string;
}

export default function SubmissionHistoryPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!projectId) return;
    const load = async () => {
      try {
        const resp = await api.get(`/projects/${projectId}/submissions`);
        setSubmissions((resp.data as any).data || resp.data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [projectId]);

  const statusBadge = (status: string) => {
    const colors: Record<string, string> = {
      completed: "bg-emerald-100 text-emerald-700",
      completed_with_errors: "bg-amber-100 text-amber-700",
      failed: "bg-red-100 text-red-700",
      sending: "bg-blue-100 text-blue-700",
      queued: "bg-slate-100 text-slate-600",
      processing: "bg-blue-100 text-blue-700",
    };
    return (
      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${colors[status] || "bg-slate-100 text-slate-600"}`}>
        {status.replace(/_/g, " ")}
      </span>
    );
  };

  if (loading) {
    return <div className="py-12 text-center text-slate-500">Yükleniyor...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-slate-900">Gönderim Geçmişi</h2>
          <p className="text-sm text-slate-500">FHIR sunucusuna yapılan tüm gönderimler</p>
        </div>
        <Link to={`/projects/${projectId}`}>
          <Button variant="secondary">← Projeye Dön</Button>
        </Link>
      </div>

      {submissions.length === 0 ? (
        <div className="bg-white rounded-xl border border-slate-200 p-12 text-center text-slate-500">
          Henüz gönderim yapılmamış.
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-600">
              <tr>
                <th className="px-4 py-3 font-medium">Tarih</th>
                <th className="px-4 py-3 font-medium">Bundle Türü</th>
                <th className="px-4 py-3 font-medium">Hedef</th>
                <th className="px-4 py-3 font-medium">Toplam</th>
                <th className="px-4 py-3 font-medium">Başarılı</th>
                <th className="px-4 py-3 font-medium">Hatalı</th>
                <th className="px-4 py-3 font-medium">Durum</th>
                <th className="px-4 py-3 font-medium">İşlem</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {submissions.map((s) => (
                <tr key={s.id} className="hover:bg-slate-50/50">
                  <td className="px-4 py-3 text-slate-700">
                    {new Date(s.created_at).toLocaleDateString("tr-TR")}
                  </td>
                  <td className="px-4 py-3">
                    <span className="px-2 py-0.5 rounded text-xs bg-indigo-50 text-indigo-700 font-medium">
                      {s.bundle_type}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-slate-500 truncate max-w-[200px]">
                    {s.fhir_server_url}
                  </td>
                  <td className="px-4 py-3 font-medium">{s.resource_count}</td>
                  <td className="px-4 py-3 text-emerald-600 font-medium">{s.success_count}</td>
                  <td className="px-4 py-3 text-red-600 font-medium">{s.failure_count}</td>
                  <td className="px-4 py-3">{statusBadge(s.status)}</td>
                  <td className="px-4 py-3">
                    <Link to={`/projects/${projectId}/submissions/${s.id}`}>
                      <Button variant="secondary" className="text-xs px-2 py-1">Detay</Button>
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
