import { useState, useEffect, type FormEvent } from "react";
import { api, ApiRequestError } from "../lib/api";
import type { ProjectResponse, FhirResourceType } from "../types/api";
import Button from "../components/ui/Button";
import Input from "../components/ui/Input";
import Dialog from "../components/ui/Dialog";
import ProjectCard from "../components/ProjectCard";

export default function ProjectsPage() {
  const [projects, setProjects] = useState<ProjectResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // New project form state
  const [newName, setNewName] = useState("");
  const [newType, setNewType] = useState<FhirResourceType>("Patient");
  const [newDescription, setNewDescription] = useState("");

  const fetchProjects = async () => {
    setIsLoading(true);
    try {
      const response = await api.get<ProjectResponse[]>("/api/v1/projects");
      setProjects(response.data);
    } catch (err) {
      setError(
        err instanceof ApiRequestError
          ? err.message
          : "Projeler yüklenemedi."
      );
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchProjects();
  }, []);

  const handleCreateProject = async (e: FormEvent) => {
    e.preventDefault();
    setIsCreating(true);
    try {
      await api.post("/api/v1/projects", {
        name: newName,
        resource_type: newType,
        description: newDescription || undefined,
      });
      setIsDialogOpen(false);
      setNewName("");
      setNewDescription("");
      setNewType("Patient");
      await fetchProjects();
    } catch (err) {
      setError(
        err instanceof ApiRequestError
          ? err.message
          : "Proje oluşturulamadı."
      );
    } finally {
      setIsCreating(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Projeler</h1>
          <p className="mt-1 text-sm text-slate-500">
            FHIR dönüşüm projelerinizi yönetin
          </p>
        </div>
        <Button onClick={() => setIsDialogOpen(true)}>
          <svg className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
            <path d="M10.75 4.75a.75.75 0 00-1.5 0v4.5h-4.5a.75.75 0 000 1.5h4.5v4.5a.75.75 0 001.5 0v-4.5h4.5a.75.75 0 000-1.5h-4.5v-4.5z" />
          </svg>
          Yeni Proje
        </Button>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700 flex items-center gap-2">
          <svg className="h-5 w-5 text-red-400 shrink-0" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.28 7.22a.75.75 0 00-1.06 1.06L8.94 10l-1.72 1.72a.75.75 0 101.06 1.06L10 11.06l1.72 1.72a.75.75 0 101.06-1.06L11.06 10l1.72-1.72a.75.75 0 00-1.06-1.06L10 8.94 8.28 7.22z" clipRule="evenodd" />
          </svg>
          {error}
          <button onClick={() => setError(null)} className="ml-auto text-red-500 hover:text-red-700">
            ✕
          </button>
        </div>
      )}

      {/* Content */}
      {isLoading ? (
        <div className="flex items-center justify-center py-20">
          <div className="animate-spin h-8 w-8 rounded-full border-4 border-indigo-500 border-t-transparent" />
        </div>
      ) : projects.length === 0 ? (
        <div className="text-center py-20">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-slate-100 mb-4">
            <svg className="w-8 h-8 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 12.75V12A2.25 2.25 0 014.5 9.75h15A2.25 2.25 0 0121.75 12v.75m-8.69-6.44l-2.12-2.12a1.5 1.5 0 00-1.061-.44H4.5A2.25 2.25 0 002.25 6v12a2.25 2.25 0 002.25 2.25h15A2.25 2.25 0 0021.75 18V9a2.25 2.25 0 00-2.25-2.25h-5.379a1.5 1.5 0 01-1.06-.44z" />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-slate-900">
            Henüz proje yok
          </h3>
          <p className="mt-1 text-sm text-slate-500">
            İlk FHIR dönüşüm projenizi oluşturarak başlayın.
          </p>
          <Button className="mt-4" onClick={() => setIsDialogOpen(true)}>
            İlk Projenizi Oluşturun
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {projects.map((project) => (
            <ProjectCard key={project.id} project={project} />
          ))}
        </div>
      )}

      {/* New Project Dialog */}
      <Dialog
        isOpen={isDialogOpen}
        onClose={() => setIsDialogOpen(false)}
        title="Yeni Proje Oluştur"
      >
        <form onSubmit={handleCreateProject} className="space-y-5">
          <Input
            label="Proje Adı"
            placeholder="Hasta dönüşümü"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            required
            autoFocus
          />

          <div className="space-y-1.5">
            <label className="block text-sm font-medium text-slate-700">
              Hedef Kaynak Tipi
            </label>
            <div className="grid grid-cols-2 gap-3">
              {(["Patient", "Observation"] as const).map((type) => (
                <button
                  key={type}
                  type="button"
                  onClick={() => setNewType(type)}
                  className={`
                    px-4 py-3 rounded-lg border-2 text-sm font-medium
                    transition-all duration-150
                    ${
                      newType === type
                        ? type === "Patient"
                          ? "border-violet-500 bg-violet-50 text-violet-700"
                          : "border-teal-500 bg-teal-50 text-teal-700"
                        : "border-slate-200 text-slate-600 hover:border-slate-300"
                    }
                  `}
                >
                  <div className="text-center">
                    <span className="text-lg">
                      {type === "Patient" ? "👤" : "🔬"}
                    </span>
                    <div className="mt-1">{type}</div>
                  </div>
                </button>
              ))}
            </div>
          </div>

          <Input
            label="Açıklama (opsiyonel)"
            placeholder="Projenin kısa açıklaması"
            value={newDescription}
            onChange={(e) => setNewDescription(e.target.value)}
          />

          <div className="flex justify-end gap-3 pt-2">
            <Button
              type="button"
              variant="secondary"
              onClick={() => setIsDialogOpen(false)}
            >
              İptal
            </Button>
            <Button type="submit" isLoading={isCreating}>
              Oluştur
            </Button>
          </div>
        </form>
      </Dialog>
    </div>
  );
}
