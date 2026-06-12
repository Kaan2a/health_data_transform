import { useEffect, useState } from "react";
import { mappingsApi } from "../lib/mappingsApi";
import Button from "./ui/Button";

interface FhirPreviewProps {
  projectId: string;
  sourceId: string;
}

export default function FhirPreview({ projectId, sourceId }: FhirPreviewProps) {
  const [previewJson, setPreviewJson] = useState<any[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadPreview = async () => {
    setLoading(true);
    setError(null);
    try {
      const resp = await mappingsApi.previewMappings(projectId, sourceId);
      setPreviewJson(resp.data);
    } catch (err: any) {
      setError(err.message || "Ön izleme oluşturulamadı.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPreview();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId, sourceId]);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-medium text-slate-900">FHIR Ön İzleme</h3>
          <p className="text-sm text-slate-500">
            Eşleştirme kuralları uygulandıktan sonraki JSON çıktısı.
          </p>
        </div>
        <Button variant="secondary" onClick={loadPreview} isLoading={loading}>
          <svg className="w-4 h-4 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182" />
          </svg>
          Yenile
        </Button>
      </div>

      {error && (
        <div className="p-3 text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg">
          {error}
        </div>
      )}

      <div className="bg-[#1e1e1e] rounded-xl overflow-hidden shadow-inner relative">
        {loading && (
          <div className="absolute inset-0 bg-[#1e1e1e]/50 flex items-center justify-center z-10 backdrop-blur-sm">
            <div className="w-8 h-8 border-2 border-indigo-200 border-t-indigo-600 rounded-full animate-spin" />
          </div>
        )}
        <pre className="p-4 text-sm font-mono text-emerald-400 overflow-x-auto max-h-[500px] overflow-y-auto">
          {previewJson
            ? JSON.stringify(previewJson, null, 2)
            : "// Yükleniyor veya veri yok..."}
        </pre>
      </div>
    </div>
  );
}
