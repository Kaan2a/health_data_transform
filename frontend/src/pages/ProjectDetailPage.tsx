import { useCallback, useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api } from "../lib/api";
import type {
  CsvPreviewResponse,
  DataSourceCreate,
  DataSourceResponse,
  ProjectResponse,
  UploadResponse,
} from "../types/api";
import Badge from "../components/ui/Badge";
import Button from "../components/ui/Button";
import Dialog from "../components/ui/Dialog";
import Input from "../components/ui/Input";
import Tabs from "../components/ui/Tabs";
import DataSourceCard from "../components/DataSourceCard";
import FileUpload from "../components/FileUpload";
import CsvPreview from "../components/CsvPreview";
import MappingTable from "../components/MappingTable";
import FhirPreview from "../components/FhirPreview";
import { JobPanel } from "../components/Jobs/JobPanel";

type TabId = "sources" | "mapping" | "transform";

const TABS = [
  {
    id: "sources" as TabId,
    label: "Veri Kaynakları",
    icon: (
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M20.25 6.375c0 2.278-3.694 4.125-8.25 4.125S3.75 8.653 3.75 6.375m16.5 0c0-2.278-3.694-4.125-8.25-4.125S3.75 4.097 3.75 6.375m16.5 0v11.25c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125V6.375m16.5 0v3.75m-16.5-3.75v3.75m16.5 0v3.75C20.25 16.153 16.556 18 12 18s-8.25-1.847-8.25-4.125v-3.75m16.5 0c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125" />
      </svg>
    ),
  },
  {
    id: "mapping" as TabId,
    label: "Eşleştirme",
    disabled: false,
    icon: (
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M7.5 21L3 16.5m0 0L7.5 12M3 16.5h13.5m0-13.5L21 7.5m0 0L16.5 12M21 7.5H7.5" />
      </svg>
    ),
  },
  {
    id: "transform" as TabId,
    label: "Dönüşüm",
    disabled: false,
    icon: (
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182" />
      </svg>
    ),
  },
];

export default function ProjectDetailPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();

  const [project, setProject] = useState<ProjectResponse | null>(null);
  const [sources, setSources] = useState<DataSourceResponse[]>([]);
  const [activeTab, setActiveTab] = useState<string>("sources");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Dialog states
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showUploadDialog, setShowUploadDialog] = useState(false);
  const [showPreviewDialog, setShowPreviewDialog] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  // Form states
  const [newSourceName, setNewSourceName] = useState("");
  const [newSourceType, setNewSourceType] = useState<"csv" | "api">("csv");
  const [creating, setCreating] = useState(false);

  // Upload states
  const [activeSourceId, setActiveSourceId] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  // Preview states
  const [previewData, setPreviewData] = useState<CsvPreviewResponse | null>(null);
  const [isPreviewing, setIsPreviewing] = useState(false);

  // Mapping states
  const [mappingSourceId, setMappingSourceId] = useState<string>("");

  // Delete
  const [deleteSourceId, setDeleteSourceId] = useState<string | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  // ── Data loading ──

  const loadProject = useCallback(async () => {
    if (!projectId) return;
    try {
      const resp = await api.get<ProjectResponse>(`/api/v1/projects/${projectId}`);
      setProject(resp.data);
    } catch {
      setError("Proje yüklenirken hata oluştu.");
    }
  }, [projectId]);

  const loadSources = useCallback(async () => {
    if (!projectId) return;
    try {
      const resp = await api.get<DataSourceResponse[]>(`/api/v1/projects/${projectId}/sources`);
      setSources(resp.data);
    } catch {
      // silent fail, sources might not exist yet
    }
  }, [projectId]);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      await Promise.all([loadProject(), loadSources()]);
      setLoading(false);
    };
    load();
  }, [loadProject, loadSources]);

  // ── Create source ──

  const handleCreateSource = async () => {
    if (!projectId || !newSourceName.trim()) return;
    setCreating(true);
    try {
      const body: DataSourceCreate = {
        name: newSourceName.trim(),
        type: newSourceType,
      };
      await api.post(`/api/v1/projects/${projectId}/sources`, body);
      await loadSources();
      setShowCreateDialog(false);
      setNewSourceName("");
      setNewSourceType("csv");
    } catch {
      setError("Veri kaynağı oluşturulamadı.");
    } finally {
      setCreating(false);
    }
  };

  // ── Upload ──

  const handleUploadClick = (sourceId: string) => {
    setActiveSourceId(sourceId);
    setShowUploadDialog(true);
  };

  const handleUpload = async (file: File) => {
    if (!projectId || !activeSourceId) return;
    setIsUploading(true);
    setUploadProgress(10);

    try {
      const formData = new FormData();
      formData.append("file", file);

      setUploadProgress(30);
      await api.upload<UploadResponse>(
        `/api/v1/projects/${projectId}/sources/${activeSourceId}/upload`,
        formData
      );
      setUploadProgress(100);

      await loadSources();

      setTimeout(() => {
        setShowUploadDialog(false);
        setIsUploading(false);
        setUploadProgress(0);
      }, 500);
    } catch {
      setError("Dosya yüklenirken hata oluştu.");
      setIsUploading(false);
      setUploadProgress(0);
    }
  };

  // ── Preview ──

  const handlePreviewClick = async (sourceId: string) => {
    if (!projectId) return;
    setActiveSourceId(sourceId);
    setIsPreviewing(true);
    setShowPreviewDialog(true);

    try {
      const resp = await api.post<CsvPreviewResponse>(
        `/api/v1/projects/${projectId}/sources/${sourceId}/preview`
      );
      setPreviewData(resp.data);
      await loadSources();
    } catch {
      setError("Ön izleme oluşturulurken hata oluştu.");
    } finally {
      setIsPreviewing(false);
    }
  };

  // For sources that already have preview_data, show it directly
  const handleSelectSource = (source: DataSourceResponse) => {
    if (source.status === "previewed" || source.status === "ready") {
      if (source.columns && source.preview_data) {
        setPreviewData({
          columns: source.columns as CsvPreviewResponse["columns"],
          preview_rows: source.preview_data as Record<string, string>[],
          total_rows: source.row_count ?? 0,
          encoding: "utf-8",
          delimiter: ",",
        });
        setShowPreviewDialog(true);
      }
    }
  };

  // ── Delete ──

  const handleDeleteClick = (sourceId: string) => {
    setDeleteSourceId(sourceId);
    setShowDeleteConfirm(true);
  };

  const handleDeleteConfirm = async () => {
    if (!projectId || !deleteSourceId) return;
    setIsDeleting(true);
    try {
      await api.delete(`/api/v1/projects/${projectId}/sources/${deleteSourceId}`);
      await loadSources();
      setShowDeleteConfirm(false);
      setDeleteSourceId(null);
    } catch {
      setError("Silme işlemi başarısız oldu.");
    } finally {
      setIsDeleting(false);
    }
  };

  // ── Render ──

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="w-8 h-8 border-2 border-indigo-200 border-t-indigo-600 rounded-full animate-spin" />
      </div>
    );
  }

  if (!project) {
    return (
      <div className="text-center py-20">
        <p className="text-slate-500">Proje bulunamadı.</p>
        <Button variant="ghost" onClick={() => navigate("/")} className="mt-4">
          Projelere Dön
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6" id="project-detail-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate("/")}
            className="p-2 -ml-2 rounded-lg hover:bg-slate-100 transition-colors duration-150 cursor-pointer"
            id="back-button"
          >
            <svg className="w-5 h-5 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" />
            </svg>
          </button>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-xl font-bold text-slate-900">{project.name}</h1>
              <Badge variant={project.resource_type === "Patient" ? "patient" : "observation"}>
                {project.resource_type}
              </Badge>
            </div>
            {project.description && (
              <p className="text-sm text-slate-500 mt-0.5">{project.description}</p>
            )}
          </div>
        </div>
      </div>

      {/* Error banner */}
      {error && (
        <div className="flex items-center gap-2 px-4 py-3 rounded-lg bg-red-50 border border-red-200">
          <svg className="w-4 h-4 text-red-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
          </svg>
          <p className="text-sm text-red-600 flex-1">{error}</p>
          <button onClick={() => setError(null)} className="text-red-400 hover:text-red-600 cursor-pointer">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      )}

      {/* Tabs */}
      <Tabs tabs={TABS} activeTab={activeTab} onChange={setActiveTab} />

      {/* Tab content */}
      {activeTab === "sources" && (
        <div className="space-y-4">
          {/* Action bar */}
          <div className="flex items-center justify-between">
            <p className="text-sm text-slate-500">
              {sources.length === 0
                ? "Henüz veri kaynağı eklenmemiş."
                : `${sources.length} veri kaynağı`}
            </p>
            <Button onClick={() => setShowCreateDialog(true)} id="add-source-button">
              <svg className="w-4 h-4 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
              </svg>
              Veri Kaynağı Ekle
            </Button>
          </div>

          {/* Sources list */}
          {sources.length === 0 ? (
            <div className="text-center py-16">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-indigo-50 mb-4">
                <svg className="w-8 h-8 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M20.25 6.375c0 2.278-3.694 4.125-8.25 4.125S3.75 8.653 3.75 6.375m16.5 0c0-2.278-3.694-4.125-8.25-4.125S3.75 4.097 3.75 6.375m16.5 0v11.25c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125V6.375" />
                </svg>
              </div>
              <h3 className="text-sm font-semibold text-slate-700">Veri Kaynağı Yok</h3>
              <p className="text-sm text-slate-400 mt-1 max-w-sm mx-auto">
                CSV dosyası yükleyin veya bir API kaynağı ekleyerek başlayın.
              </p>
              <Button
                variant="secondary"
                onClick={() => setShowCreateDialog(true)}
                className="mt-4"
              >
                İlk Kaynağı Ekle
              </Button>
            </div>
          ) : (
            <div className="grid gap-3">
              {sources.map((source) => (
                <DataSourceCard
                  key={source.id}
                  source={source}
                  onUpload={() => handleUploadClick(source.id)}
                  onPreview={() => handlePreviewClick(source.id)}
                  onDelete={() => handleDeleteClick(source.id)}
                  onSelect={() => handleSelectSource(source)}
                />
              ))}
            </div>
          )}
        </div>
      )}

      {activeTab === "mapping" && (
        <div className="space-y-8">
          {sources.length === 0 ? (
            <div className="text-center py-16 text-slate-500">
              Eşleştirme yapmak için önce bir veri kaynağı ekleyin.
            </div>
          ) : (
            <>
              <div className="flex items-center gap-4 bg-slate-50 p-4 rounded-xl border border-slate-200">
                <label className="text-sm font-medium text-slate-700 whitespace-nowrap">
                  Veri Kaynağı Seçin:
                </label>
                <select
                  className="flex-1 max-w-sm px-3 py-2 bg-white border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  value={mappingSourceId}
                  onChange={(e) => setMappingSourceId(e.target.value)}
                >
                  <option value="">-- Kaynak Seçin --</option>
                  {sources.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name} ({s.type})
                    </option>
                  ))}
                </select>
              </div>

              {mappingSourceId && projectId ? (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                  <div className="lg:col-span-1 border-r border-slate-200 pr-0 lg:pr-8">
                    <MappingTable
                      projectId={projectId}
                      sourceId={mappingSourceId}
                      columns={(sources.find((s) => s.id === mappingSourceId)?.columns as any) || []}
                    />
                  </div>
                  <div className="lg:col-span-1">
                    <FhirPreview projectId={projectId} sourceId={mappingSourceId} />
                  </div>
                </div>
              ) : (
                <div className="text-center py-12 text-slate-500">
                  Lütfen yukarıdan bir veri kaynağı seçin.
                </div>
              )}
            </>
          )}
        </div>
      )}

      {activeTab === "transform" && (
        <div className="space-y-8">
          {sources.length === 0 ? (
            <div className="text-center py-16 text-slate-500">
              Dönüşüm yapmak için önce bir veri kaynağı ekleyin ve eşleştirin.
            </div>
          ) : (
            <>
              <div className="flex items-center gap-4 bg-slate-50 p-4 rounded-xl border border-slate-200">
                <label className="text-sm font-medium text-slate-700 whitespace-nowrap">
                  Dönüştürülecek Kaynak:
                </label>
                <select
                  className="flex-1 max-w-sm px-3 py-2 bg-white border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  value={mappingSourceId}
                  onChange={(e) => setMappingSourceId(e.target.value)}
                >
                  <option value="">-- Kaynak Seçin --</option>
                  {sources.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name} ({s.type})
                    </option>
                  ))}
                </select>
              </div>

              {mappingSourceId && projectId ? (
                <JobPanel projectId={projectId} sourceId={mappingSourceId} />
              ) : (
                <div className="text-center py-12 text-slate-500">
                  Lütfen yukarıdan bir veri kaynağı seçin.
                </div>
              )}
            </>
          )}
        </div>
      )}

      {/* Create Source Dialog */}
      <Dialog
        isOpen={showCreateDialog}
        onClose={() => setShowCreateDialog(false)}
        title="Yeni Veri Kaynağı"
      >
        <div className="space-y-4">
          <Input
            label="Kaynak Adı"
            value={newSourceName}
            onChange={(e) => setNewSourceName(e.target.value)}
            placeholder="örn. Hasta Verileri CSV"
            id="source-name-input"
          />

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
              Kaynak Türü
            </label>
            <div className="grid grid-cols-2 gap-2">
              <button
                onClick={() => setNewSourceType("csv")}
                className={`
                  p-3 rounded-lg border-2 text-left transition-all duration-150 cursor-pointer
                  ${newSourceType === "csv"
                    ? "border-indigo-500 bg-indigo-50"
                    : "border-slate-200 hover:border-slate-300"
                  }
                `}
                id="type-csv-button"
              >
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-lg bg-emerald-100 flex items-center justify-center">
                    <svg className="w-4 h-4 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                    </svg>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-slate-700">CSV Dosya</p>
                    <p className="text-xs text-slate-400">CSV/TSV yükleme</p>
                  </div>
                </div>
              </button>
              <button
                onClick={() => setNewSourceType("api")}
                className={`
                  p-3 rounded-lg border-2 text-left transition-all duration-150 cursor-pointer
                  ${newSourceType === "api"
                    ? "border-indigo-500 bg-indigo-50"
                    : "border-slate-200 hover:border-slate-300"
                  }
                `}
                id="type-api-button"
              >
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-lg bg-purple-100 flex items-center justify-center">
                    <svg className="w-4 h-4 text-purple-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M12 21a9.004 9.004 0 008.716-6.747M12 21a9.004 9.004 0 01-8.716-6.747M12 21c2.485 0 4.5-4.03 4.5-9S14.485 3 12 3m0 18c-2.485 0-4.5-4.03-4.5-9S9.515 3 12 3m0 0a8.997 8.997 0 017.843 4.582M12 3a8.997 8.997 0 00-7.843 4.582" />
                    </svg>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-slate-700">REST API</p>
                    <p className="text-xs text-slate-400">HTTP endpoint</p>
                  </div>
                </div>
              </button>
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <Button variant="ghost" onClick={() => setShowCreateDialog(false)}>
              İptal
            </Button>
            <Button
              onClick={handleCreateSource}
              disabled={!newSourceName.trim() || creating}
              isLoading={creating}
              id="create-source-button"
            >
              Oluştur
            </Button>
          </div>
        </div>
      </Dialog>

      {/* Upload Dialog */}
      <Dialog
        isOpen={showUploadDialog}
        onClose={() => !isUploading && setShowUploadDialog(false)}
        title="CSV Dosya Yükleme"
      >
        <FileUpload
          onFileSelect={() => {}}
          onUpload={handleUpload}
          isUploading={isUploading}
          uploadProgress={uploadProgress}
        />
      </Dialog>

      {/* Preview Dialog */}
      <Dialog
        isOpen={showPreviewDialog}
        onClose={() => {
          setShowPreviewDialog(false);
          setPreviewData(null);
        }}
        title="CSV Ön İzleme"
        size="lg"
      >
        <div className="min-w-[600px] max-w-[90vw]">
          {isPreviewing ? (
            <div className="flex items-center justify-center py-12">
              <div className="text-center">
                <div className="w-8 h-8 border-2 border-indigo-200 border-t-indigo-600 rounded-full animate-spin mx-auto mb-3" />
                <p className="text-sm text-slate-500">Sütunlar analiz ediliyor...</p>
              </div>
            </div>
          ) : previewData ? (
            <CsvPreview
              columns={previewData.columns}
              previewRows={previewData.preview_rows}
              totalRows={previewData.total_rows}
              encoding={previewData.encoding}
              delimiter={previewData.delimiter}
            />
          ) : (
            <p className="text-sm text-slate-500 text-center py-8">Ön izleme verisi bulunamadı.</p>
          )}
        </div>
      </Dialog>

      {/* Delete Confirmation */}
      <Dialog
        isOpen={showDeleteConfirm}
        onClose={() => setShowDeleteConfirm(false)}
        title="Veri Kaynağını Sil"
      >
        <div className="space-y-4">
          <p className="text-sm text-slate-600">
            Bu veri kaynağını ve ilişkili dosyaları silmek istediğinizden emin misiniz? Bu işlem geri alınamaz.
          </p>
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={() => setShowDeleteConfirm(false)}>
              İptal
            </Button>
            <Button
              variant="danger"
              onClick={handleDeleteConfirm}
              isLoading={isDeleting}
              id="confirm-delete-button"
            >
              Sil
            </Button>
          </div>
        </div>
      </Dialog>
    </div>
  );
}
