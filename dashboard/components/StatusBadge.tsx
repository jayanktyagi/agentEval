// components/StatusBadge.tsx

interface StatusBadgeProps {
  status: string;
  size?: "sm" | "md";
}

const config: Record<string, { label: string; color: string; bg: string; border: string }> = {
  passed:       { label: "PASS",    color: "#22c55e", bg: "#22c55e12", border: "#22c55e30" },
  failed:       { label: "FAIL",    color: "#ef4444", bg: "#ef444412", border: "#ef444430" },
  error:        { label: "ERROR",   color: "#ef4444", bg: "#ef444412", border: "#ef444430" },
  running:      { label: "RUNNING", color: "#ffffff", bg: "#ffffff08", border: "#ffffff20" },
  happy_path:   { label: "HAPPY",   color: "#a0a0a0", bg: "transparent", border: "#2a2a2a" },
  failure_case: { label: "FAILURE", color: "#a0a0a0", bg: "transparent", border: "#2a2a2a" },
  edge_case:    { label: "EDGE",    color: "#a0a0a0", bg: "transparent", border: "#2a2a2a" },
};

export default function StatusBadge({ status, size = "sm" }: StatusBadgeProps) {
  const c = config[status] || { label: status.toUpperCase(), color: "#505050", bg: "transparent", border: "#1f1f1f" };
  const pad = size === "md" ? "3px 10px" : "2px 7px";
  const fs = size === "md" ? "11px" : "10px";

  return (
    <span style={{
      display: "inline-block",
      padding: pad,
      fontSize: fs,
      fontWeight: 600,
      letterSpacing: "0.08em",
      color: c.color,
      border: `1px solid ${c.border}`,
      background: c.bg,
      borderRadius: "2px",
      fontFamily: "inherit",
    }}>
      {c.label}
    </span>
  );
}