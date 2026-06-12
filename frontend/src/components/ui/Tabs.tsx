import type { ReactNode } from "react";

interface Tab {
  id: string;
  label: string;
  icon?: ReactNode;
  disabled?: boolean;
}

interface TabsProps {
  tabs: Tab[];
  activeTab: string;
  onChange: (tabId: string) => void;
}

export default function Tabs({ tabs, activeTab, onChange }: TabsProps) {
  return (
    <div className="border-b border-slate-200" id="tabs-container">
      <nav className="-mb-px flex gap-1" aria-label="Tabs">
        {tabs.map((tab) => {
          const isActive = tab.id === activeTab;
          const isDisabled = tab.disabled;

          return (
            <button
              key={tab.id}
              id={`tab-${tab.id}`}
              onClick={() => !isDisabled && onChange(tab.id)}
              disabled={isDisabled}
              className={`
                group relative inline-flex items-center gap-2 px-4 py-3
                text-sm font-medium transition-all duration-200 ease-out
                border-b-2 cursor-pointer
                ${isActive
                  ? "border-indigo-500 text-indigo-600"
                  : isDisabled
                    ? "border-transparent text-slate-300 cursor-not-allowed"
                    : "border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300"
                }
              `}
            >
              {tab.icon && (
                <span className={`
                  transition-colors duration-200
                  ${isActive ? "text-indigo-500" : isDisabled ? "text-slate-300" : "text-slate-400 group-hover:text-slate-500"}
                `}>
                  {tab.icon}
                </span>
              )}
              {tab.label}
              {isActive && (
                <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-indigo-500 rounded-t-full" />
              )}
            </button>
          );
        })}
      </nav>
    </div>
  );
}
