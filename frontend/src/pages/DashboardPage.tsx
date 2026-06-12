import { useEffect, useState } from "react";
import { analyticsApi } from "../lib/analyticsApi";
import type { DashboardStats } from "../lib/analyticsApi";

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const data = await analyticsApi.getDashboardStats();
        setStats(data);
      } catch (err) {
        console.error("Dashboard stats fetch error:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchStats();
  }, []);

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="text-slate-500 font-medium">Veriler Yükleniyor...</div>
      </div>
    );
  }

  const processed = stats?.total_rows_processed || 0;
  const success = stats?.total_rows_success || 0;
  const failed = stats?.total_rows_failed || 0;
  const successRate = processed > 0 ? Math.round((success / processed) * 100) : 0;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-slate-900">Gösterge Paneli</h1>
        <span className="bg-indigo-100 text-indigo-700 text-xs font-semibold px-3 py-1 rounded-full uppercase tracking-wider">
          Genel Durum
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Projects Card */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5 flex flex-col">
          <span className="text-slate-500 text-sm font-medium mb-1">Toplam Proje</span>
          <span className="text-3xl font-bold text-slate-800">{stats?.total_projects || 0}</span>
          <div className="mt-4 text-xs text-indigo-600 bg-indigo-50 rounded-lg px-2 py-1 self-start">
            Aktif Çalışma Alanları
          </div>
        </div>

        {/* Total Jobs Card */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5 flex flex-col">
          <span className="text-slate-500 text-sm font-medium mb-1">Toplam Dönüşüm İşi</span>
          <span className="text-3xl font-bold text-slate-800">{stats?.total_jobs || 0}</span>
          <div className="mt-4 text-xs text-blue-600 bg-blue-50 rounded-lg px-2 py-1 self-start">
            Çalıştırılan FHIR Motorları
          </div>
        </div>

        {/* Total Processed Rows Card */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5 flex flex-col">
          <span className="text-slate-500 text-sm font-medium mb-1">İşlenen Kayıt Sayısı</span>
          <span className="text-3xl font-bold text-slate-800">{processed.toLocaleString()}</span>
          <div className="mt-4 text-xs text-green-600 bg-green-50 rounded-lg px-2 py-1 self-start">
            FHIR Formatına Giren Veriler
          </div>
        </div>

        {/* Success Rate Card */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5 flex flex-col">
          <span className="text-slate-500 text-sm font-medium mb-1">Genel Başarı Oranı</span>
          <div className="flex items-end gap-2">
            <span className="text-3xl font-bold text-slate-800">%{successRate}</span>
          </div>
          <div className="w-full bg-slate-100 rounded-full h-1.5 mt-4">
            <div
              className={`h-1.5 rounded-full ${successRate > 90 ? 'bg-green-500' : successRate > 50 ? 'bg-yellow-500' : 'bg-red-500'}`}
              style={{ width: `${successRate}%` }}
            ></div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-8">
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          <h3 className="text-lg font-semibold text-slate-800 mb-4">Detaylı Dönüşüm İstatistikleri</h3>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-slate-600 font-medium">Başarılı FHIR Kaynakları</span>
              <span className="text-green-600 font-bold bg-green-50 px-3 py-1 rounded-full text-sm">
                {success.toLocaleString()}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-600 font-medium">Validasyon Hataları (Eksik Veri vb.)</span>
              <span className="text-red-600 font-bold bg-red-50 px-3 py-1 rounded-full text-sm">
                {failed.toLocaleString()}
              </span>
            </div>
            <div className="pt-4 border-t border-slate-100">
              <p className="text-sm text-slate-500">
                FHIR dönüştürücü motoru, hatalı olan satırları (schema validation errors) es geçerek başarılı satırları çıktı dosyasına yazar. Hatalı kayıtları projelerin detay sayfasından kontrol edebilirsiniz.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
