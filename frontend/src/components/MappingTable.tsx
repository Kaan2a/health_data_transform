import { useEffect, useState } from "react";
import { mappingsApi } from "../lib/mappingsApi";
import type {
  FhirSchemaField,
  MappingRuleCreate,
} from "../types/mapping";
import Button from "./ui/Button";

interface MappingTableProps {
  projectId: string;
  sourceId: string;
  columns: { name: string; inferred_type: string }[];
}

export default function MappingTable({ projectId, sourceId, columns }: MappingTableProps) {
  const [schema, setSchema] = useState<FhirSchemaField[]>([]);
  const [mappingState, setMappingState] = useState<Record<string, { target: string; valueMapStr: string; maskingType: any }>>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      try {
        const [schemaResp, rulesResp] = await Promise.all([
          mappingsApi.getFhirSchema(projectId),
          mappingsApi.listMappingRules(projectId, sourceId),
        ]);
        setSchema(schemaResp.data);

        // Initialize state with existing rules
        const initialState: Record<string, { target: string; valueMapStr: string; maskingType: any }> = {};
        rulesResp.data.forEach((rule: any) => {
          initialState[rule.sourceField || rule.source_field] = {
            target: rule.targetFhirField || rule.target_fhir_field,
            valueMapStr: (rule.valueMap || rule.value_map) ? JSON.stringify(rule.valueMap || rule.value_map) : "",
            maskingType: (rule.maskingType || rule.masking_type) || "NONE",
          };
        });
        setMappingState(initialState);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, [projectId, sourceId]);

  const handleAutoSuggest = async () => {
    try {
      const resp = await mappingsApi.autoSuggestMappings(projectId, sourceId, {
        columns: columns.map((c) => c.name),
      });
      const newState = { ...mappingState };
      const suggestions = (resp.data as any).suggestions || [];
      suggestions.forEach((s: any) => {
        newState[s.source_field] = {
          target: s.target_fhir_field,
          valueMapStr: "",
          maskingType: "NONE",
        };
      });
      setMappingState(newState);
    } catch (err) {
      console.error(err);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const rulesToSave: MappingRuleCreate[] = Object.entries(mappingState)
        .filter(([_, mapping]) => mapping.target !== "") // Only save mapped fields
        .map(([source_field, mapping]) => {
          let value_map = null;
          if (mapping.valueMapStr && mapping.valueMapStr.trim() !== "") {
            try {
              value_map = JSON.parse(mapping.valueMapStr);
            } catch (e) {
              console.warn("Invalid JSON in value map for", source_field);
            }
          }
          return {
            source_field,
            target_fhir_field: mapping.target,
            transformation_type: "direct",
            value_map,
            masking_type: mapping.maskingType || "NONE",
          };
        });

      await mappingsApi.batchUpdateMappings(projectId, sourceId, { rules: rulesToSave });
      // Reload is handled by parent or user, no need to update rules state
    } catch (err) {
      console.error(err);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <div className="py-8 text-center text-slate-500">Yükleniyor...</div>;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-medium text-slate-900">Eşleştirme Kuralları</h3>
          <p className="text-sm text-slate-500">
            CSV kolonlarınızı FHIR hedeflerine eşleştirin.
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="secondary" onClick={handleAutoSuggest}>
            Otomatik Eşleştir
          </Button>
          <Button onClick={handleSave} isLoading={saving}>
            Kaydet
          </Button>
        </div>
      </div>

      <div className="bg-white border border-slate-200 rounded-xl overflow-hidden">
        <table className="w-full text-left text-sm whitespace-nowrap">
          <thead className="bg-slate-50 border-b border-slate-200 text-slate-600">
            <tr>
              <th className="px-4 py-3 font-medium">Kaynak Kolon (CSV)</th>
              <th className="px-4 py-3 font-medium">Veri Tipi</th>
              <th className="px-4 py-3 font-medium">Hedef Alan (FHIR)</th>
              <th className="px-4 py-3 font-medium">Sözlük (JSON)</th>
              <th className="px-4 py-3 font-medium">Maskeleme</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {columns.map((col) => (
              <tr key={col.name} className="hover:bg-slate-50/50">
                <td className="px-4 py-3 font-medium text-slate-700">
                  {col.name}
                </td>
                <td className="px-4 py-3 text-slate-500">
                  <span className="px-2 py-0.5 rounded text-xs bg-slate-100 border border-slate-200">
                    {col.inferred_type}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <select
                    className="w-full max-w-xs px-3 py-1.5 bg-white border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    value={mappingState[col.name]?.target || ""}
                    onChange={(e) =>
                      setMappingState({ 
                        ...mappingState, 
                        [col.name]: { ...(mappingState[col.name] || { valueMapStr: "", maskingType: "NONE" }), target: e.target.value } 
                      })
                    }
                  >
                    <option value="">-- Eşleştirilmedi --</option>
                    {schema.map((field) => (
                      <option key={field.path} value={field.path}>
                        {field.path} ({field.type})
                      </option>
                    ))}
                  </select>
                </td>
                <td className="px-4 py-3">
                  <input
                    type="text"
                    placeholder='{"K":"female", "E":"male"}'
                    className="w-full px-3 py-1.5 bg-white border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 font-mono text-xs"
                    value={mappingState[col.name]?.valueMapStr || ""}
                    onChange={(e) =>
                      setMappingState({
                        ...mappingState,
                        [col.name]: {
                           ...(mappingState[col.name] || { target: "", maskingType: "NONE" }),
                           valueMapStr: e.target.value
                        }
                      })
                    }
                  />
                </td>
                <td className="px-4 py-3">
                  <select
                    className="w-full max-w-[120px] px-3 py-1.5 bg-white border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    value={mappingState[col.name]?.maskingType || "NONE"}
                    onChange={(e) =>
                      setMappingState({
                        ...mappingState,
                        [col.name]: {
                           ...(mappingState[col.name] || { target: "", valueMapStr: "" }),
                           maskingType: e.target.value as any
                        }
                      })
                    }
                  >
                    <option value="NONE">Yok</option>
                    <option value="HASH">Hash</option>
                    <option value="PARTIAL">Kısmi</option>
                    <option value="REDACT">Gizle</option>
                  </select>
                </td>
              </tr>
            ))}
            {columns.length === 0 && (
              <tr>
                <td colSpan={4} className="px-4 py-8 text-center text-slate-500">
                  Kolon bilgisi bulunamadı. Lütfen önce veri yükleyin.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
