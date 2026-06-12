interface ProgressBarProps {
  value: number; // 0-100
  variant?: "primary" | "success" | "danger";
  size?: "sm" | "md";
  showLabel?: boolean;
  animated?: boolean;
}

const variantStyles = {
  primary: "bg-indigo-500",
  success: "bg-emerald-500",
  danger: "bg-red-500",
};

const sizeStyles = {
  sm: "h-1.5",
  md: "h-2.5",
};

export default function ProgressBar({
  value,
  variant = "primary",
  size = "md",
  showLabel = false,
  animated = true,
}: ProgressBarProps) {
  const clamped = Math.min(100, Math.max(0, value));

  return (
    <div className="w-full" id="progress-bar">
      {showLabel && (
        <div className="flex justify-between items-center mb-1">
          <span className="text-xs font-medium text-slate-600">İlerleme</span>
          <span className="text-xs font-semibold text-slate-700">{Math.round(clamped)}%</span>
        </div>
      )}
      <div className={`w-full bg-slate-200 rounded-full overflow-hidden ${sizeStyles[size]}`}>
        <div
          className={`
            ${sizeStyles[size]} rounded-full
            ${variantStyles[variant]}
            ${animated ? "transition-all duration-500 ease-out" : ""}
          `}
          style={{ width: `${clamped}%` }}
          role="progressbar"
          aria-valuenow={clamped}
          aria-valuemin={0}
          aria-valuemax={100}
        />
      </div>
    </div>
  );
}
