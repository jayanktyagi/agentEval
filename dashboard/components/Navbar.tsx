// components/Navbar.tsx
import Link from "next/link";

export default function Navbar() {
  return (
    <nav style={{
      borderBottom: "1px solid var(--border)",
      padding: "0 24px",
      height: "44px",
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      background: "var(--bg)",
      position: "sticky",
      top: 0,
      zIndex: 100,
    }}>
      <Link href="/" style={{
        textDecoration: "none",
        display: "flex",
        alignItems: "center",
        gap: "12px",
      }}>
        <span style={{
          color: "var(--text)",
          fontSize: "13px",
          fontWeight: 700,
          letterSpacing: "0.05em",
        }}>
          AGENTEVAL
        </span>
        <span style={{
          fontSize: "10px",
          color: "var(--text-3)",
          letterSpacing: "0.1em",
        }}>
          v0.1.0
        </span>
      </Link>

      <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
        <Link href="/" style={{
          color: "var(--text-3)",
          textDecoration: "none",
          fontSize: "11px",
          letterSpacing: "0.05em",
        }}>
          runs
        </Link>
        <Link href="/new" style={{
          color: "var(--bg)",
          background: "var(--text)",
          textDecoration: "none",
          fontSize: "11px",
          fontWeight: 600,
          letterSpacing: "0.05em",
          padding: "4px 12px",
          borderRadius: "2px",
        }}>
          + new run
        </Link>
      </div>
    </nav>
  );
}