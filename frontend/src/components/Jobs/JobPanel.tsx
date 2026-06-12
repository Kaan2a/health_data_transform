import { useEffect, useState } from "react";
import { jobsApi } from "../../lib/jobsApi";
import type { JobResponse, JobIssue } from "../../lib/jobsApi";
import Button from "../ui/Button";
import ProgressBar from "../ui/ProgressBar";
import Badge from "../ui/Badge";

interface JobPanelProps {
  projectId: string;
  sourceId: string;
}

export function JobPanel({ projectId, sourceId }: JobPanelProps) {
  const [job, setJob] = useState<JobResponse | null>(null);
  const [issues, setIssues] = useState<JobIssue[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [exportModalOpen, setExportModalOpen] = useState(false);
  const [exportUrl, setExportUrl] = useState("");
  const [exportToken, setExportToken] = useState("");
  const [exportBundleType, setExportBundleType] = useState("transaction");
  const [exporting, setExporting] = useState(false);

  const loadJob = async () => {
    try {
      const data = await jobsApi.getJobs(projectId);
      const sourceJob = data.find(j => j.data_source_id === sourceId);
      if (sourceJob) {
        setJob(sourceJob);
        if (sourceJob.status === "completed" || sourceJob.status === "failed") {
          loadIssues(sourceJob.id);
        }
      }
    } catch (err: any) {
      console.error(err);
    }
  };

  const loadIssues = async (jobId: string) => {
    try {
      const data = await jobsApi.getJobIssues(projectId, jobId);
      setIssues(data);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    loadJob();
    const interval = setInterval(() => {
      if (job && (job.status === "pending" || job.status === "running")) {
        loadJob();
      }
    }, 2000); // Poll every 2 seconds
    return () => clearInterval(interval);
  }, [projectId, sourceId, job?.status]);

  const handleStart = async () => {
    try {
      setLoading(true);
      setError(null);
      const newJob = await jobsApi.startJob(projectId, sourceId);
      setJob(newJob);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Dönüşüm başlatılamadı.");
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async () => {
    if (!job) return;
    try {
      setExporting(true);
      await jobsApi.exportJob(projectId, job.id, {
        target_url: exportUrl,
        auth_token: exportToken,
        bundle_type: exportBundleType
      });
      setExportModalOpen(false);
      alert("Gönderim işlemi arka planda başarıyla başlatıldı.");
    } catch (err: any) {
      alert("Gönderim başlatılamadı: " + (err.response?.data?.detail || err.message));
    } finally {
      setExporting(false);
    }
  };

  const progress = job && job.total_rows > 0 ? Math.round((job.processed_rows / job.total_rows) * 100) : 0;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-medium text-gray-900">Veri Dönüşümü</h3>
          <p className="text-sm text-gray-500">
            Eşleştirme kurallarını uygulayarak veriyi FHIR formatına dönüştürün.
          </p>
        </div>
        <Button 
          onClick={handleStart} 
          disabled={loading || job?.status === "pending" || job?.status === "running"}
        >
          {loading ? "Başlatılıyor..." : "Dönüşümü Başlat"}
        </Button>
      </div>

      {error && (
        <div className="bg-red-50 text-red-700 p-3 rounded-md text-sm border border-red-200">
          {error}
        </div>
      )}

      {job && (
        <div className="bg-white border rounded-lg shadow-sm overflow-hidden">
          <div className="p-5 border-b space-y-4">
            <div className="flex justify-between items-center">
              <span className="font-medium text-gray-700">Durum:</span>
              <Badge variant={
                job.status === "completed" ? "success" :
                job.status === "failed" ? "danger" :
                "warning"
              }>
                {job.status.toUpperCase()}
              </Badge>
            </div>

            {(job.status === "running" || job.status === "pending") && (
              <div className="space-y-1 mt-4">
                <div className="flex justify-between text-sm font-medium text-slate-600 mb-1">
                  <span>İşleniyor: {job.processed_rows} / {job.total_rows}</span>
                  <span>{progress}%</span>
                </div>
                <ProgressBar value={progress} />
              </div>
            )}

            {job.status === "completed" && (
              <div className="flex flex-col space-y-5 mt-4">
                <div className="grid grid-cols-3 gap-4 text-center">
                  <div className="bg-gray-50 border border-gray-100 p-4 rounded-lg">
                    <div className="text-sm font-medium text-gray-500 uppercase tracking-wider mb-1">Toplam Satır</div>
                    <div className="text-2xl font-bold text-gray-900">{job.total_rows}</div>
                  </div>
                  <div className="bg-green-50 border border-green-100 p-4 rounded-lg">
                    <div className="text-sm font-medium text-green-600 uppercase tracking-wider mb-1">Başarılı</div>
                    <div className="text-2xl font-bold text-green-700">{job.successful_rows}</div>
                  </div>
                  <div className="bg-red-50 border border-red-100 p-4 rounded-lg">
                    <div className="text-sm font-medium text-red-600 uppercase tracking-wider mb-1">Hatalı</div>
                    <div className="text-2xl font-bold text-red-700">{job.failed_rows}</div>
                  </div>
                </div>
                
                <div className="flex gap-4">
                  <a 
                    href={jobsApi.getDownloadUrl(projectId, job.id)} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="flex-1 inline-flex justify-center items-center px-4 py-3 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-colors"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                    </svg>
                    FHIR NDJSON İndir
                  </a>
                  <button 
                    onClick={() => setExportModalOpen(true)}
                    className="flex-1 inline-flex justify-center items-center px-4 py-3 border border-transparent text-sm font-medium rounded-md shadow-sm text-indigo-700 bg-indigo-100 hover:bg-indigo-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-colors"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 5l7 7-7 7M5 5l7 7-7 7" />
                    </svg>
                    FHIR Sunucusuna Gönder
                  </button>
                </div>
              </div>
            )}
            
            {job.error_message && (
              <div className="bg-red-50 text-red-700 p-4 rounded-md text-sm mt-4 border border-red-200">
                <strong>Kritik Hata:</strong> {job.error_message}
              </div>
            )}
          </div>

          {issues.length > 0 && (
            <div className="bg-gray-50 p-5">
              <h4 className="text-md font-medium text-gray-900 mb-3 flex items-center">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2 text-red-500" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
                Hatalı Satırlar ({issues.length})
              </h4>
              <div className="overflow-x-auto bg-white rounded shadow-sm border border-gray-200 max-h-64 overflow-y-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50 sticky top-0">
                    <tr>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Satır</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Hata Türü</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Hata Detayı</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {issues.slice(0, 100).map((issue) => (
                      <tr key={issue.id} className="hover:bg-red-50/50">
                        <td className="px-4 py-2 text-sm text-gray-600 font-medium">{issue.row_index}</td>
                        <td className="px-4 py-2 text-sm text-gray-500">
                           <Badge variant="danger">{issue.issue_type}</Badge>
                        </td>
                        <td className="px-4 py-2 text-sm text-red-600">{issue.message}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {issues.length > 100 && (
                <p className="text-xs text-gray-500 mt-3 text-center italic">Sadece ilk 100 hata gösteriliyor.</p>
              )}
            </div>
          )}
        </div>
      )}

      {exportModalOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-xl shadow-xl max-w-md w-full space-y-4">
            <h3 className="text-lg font-medium text-slate-900">FHIR Sunucusuna Gönder</h3>
            <p className="text-sm text-slate-500">Oluşturulan verileri uzak sunucuya aktarın.</p>
            
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Hedef URL</label>
                <input 
                  type="text" 
                  placeholder="https://hapi.fhir.org/baseR4" 
                  className="w-full px-3 py-2 border rounded-md focus:ring-indigo-500 focus:border-indigo-500 text-sm"
                  value={exportUrl}
                  onChange={e => setExportUrl(e.target.value)}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Auth Token (Opsiyonel)</label>
                <input 
                  type="text" 
                  placeholder="Bearer token..." 
                  className="w-full px-3 py-2 border rounded-md focus:ring-indigo-500 focus:border-indigo-500 text-sm"
                  value={exportToken}
                  onChange={e => setExportToken(e.target.value)}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Bundle Tipi</label>
                <select 
                  className="w-full px-3 py-2 border rounded-md focus:ring-indigo-500 focus:border-indigo-500 text-sm"
                  value={exportBundleType}
                  onChange={e => setExportBundleType(e.target.value)}
                >
                  <option value="transaction">Transaction (Önerilen)</option>
                  <option value="batch">Batch</option>
                </select>
              </div>
            </div>

            <div className="flex justify-end gap-3 pt-4">
              <Button variant="secondary" onClick={() => setExportModalOpen(false)}>İptal</Button>
              <Button onClick={handleExport} isLoading={exporting} disabled={!exportUrl}>
                Gönderimi Başlat
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
