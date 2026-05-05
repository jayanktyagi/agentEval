// components/StatusBadge.tsx

interface StatusBadgeProps {
  status: string;
  size?: "sm" | "md";
}

const config: Record<string, { label: string; color: string }> = {
  passed:       { label: "PASS",    color: "#22c55e" },
  failed:       { label: "FAIL",    color: "#ef4444" },
  error:        { label: "ERROR",   color: "#eab308" },
  running:      { label: "RUNNING", color: "#3b82f6" },
  happy_path:   { label: "HAPPY",   color: "#22c55e" },
  failure_case: { label: "FAILURE", color: "#ef4444" },
  edge_case:    { label: "EDGE",    color: "#eab308" },
};

export default function StatusBadge({ status, size = "sm" }: StatusBadgeProps) {
  const c = config[status] || { label: status.toUpperCase(), color: "#888888" };
  const pad = size === "md" ? "4px 10px" : "2px 7px";
  const fs = size === "md" ? "11px" : "10px";

  return (
    <span style={{
      display: "inline-block",
      padding: pad,
      fontSize: fs,
      fontWeight: 600,
      letterSpacing: "0.08em",
      color: c.color,
      border: `1px solid ${c.color}33`,
      background: `${c.color}11`,
      borderRadius: "2px",
      fontFamily: "inherit",
    }}>
      {c.label}
    </span>
  );
}