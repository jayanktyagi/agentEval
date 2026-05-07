"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import Navbar from "@/components/Navbar";
import StatusBadge from "@/components/StatusBadge";
import { getRuns, TestRun } from "@/lib/api";

function PassRateBar({ rate }: { rate: number }) {
  return (
    <div style={{
      width: "60px",
      height: "2px",
      background: "var(--border-2)",
      borderRadius: "1px",
      overflow: "hidden",
    }}>
      <div style={{
        width: `${rate * 100}%`,
        height: "100%",
        background: rate >= 0.8 ? "var(--pass)" : rate >= 0.5 ? "#ffffff" : "var(--fail)",
      }} />
    </div>
  );
}

function EmptyState() {
  return (
    <div style={{
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      justifyContent: "center",
      padding: "80px 24px",
      gap: "12px",
    }}>
      <div style={{ color: "var(--text-2)", fontSize: "14px" }}>no runs yet</div>
      <div style={{ color: "var(--text-3)", fontSize: "12px" }}>
        submit your first agent test to see results here
      </div>
      <Link href="/new" style={{
        marginTop: "8px",
        color: "var(--text)",
        textDecoration: "none",
        fontSize: "11px",
        border: "1px solid var(--border-2)",
        padding: "6px 16px",
        borderRadius: "2px",
      }}>
        + create first run
      </Link>
    </div>
  );
}

export default function HomePage() {
  const [runs, setRuns] = useState<TestRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchRuns = async () => {
    try {
      const data = await getRuns();
      setRuns(data);
      setError(null);
    } catch {
      setError("cannot connect to backend — make sure it is running on port 8000");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRuns();
    const interval = setInterval(() => {
      if (runs.some(r => r.status === "running")) fetchRuns();
    }, 3000);
    return () => clearInterval(interval);
  }, [runs.length]);

  const avgPassRate = runs.length
    ? runs.reduce((sum, r) => sum + r.pass_rate, 0) / runs.length
    : 0;

  return (
    <div style={{ minHeight: "100vh", background: "var(--bg)" }}>
      <Navbar />

      <div style={{ padding: "32px 24px", maxWidth: "900px", margin: "0 auto" }}>

        {/* Header */}
        <div style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "32px",
          paddingBottom: "16px",
          borderBottom: "1px solid var(--border)",
        }}>
          <div style={{ color: "var(--text-3)", fontSize: "11px", letterSpacing: "0.1em" }}>
            TEST RUNS
          </div>
          {runs.length > 0 && (
            <div style={{ display: "flex", gap: "24px" }}>
              {[
                { label: "total", value: String(runs.length) },
                { label: "avg pass rate", value: `${(avgPassRate * 100).toFixed(0)}%` },
                { label: "running", value: String(runs.filter(r => r.status === "running").length) },
              ].map(({ label, value }) => (
                <div key={label} style={{ textAlign: "right" }}>
                  <div style={{ color: "var(--text-3)", fontSize: "10px", letterSpacing: "0.08em" }}>
                    {label.toUpperCase()}
                  </div>
                  <div style={{ color: "var(--text)", fontSize: "14px", fontWeight: 600 }}>
                    {value}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {loading ? (
          <div style={{ color: "var(--text-3)", padding: "40px 0", textAlign: "center", fontSize: "12px" }}>
            loading...
          </div>
        ) : error ? (
          <div style={{
            border: "1px solid var(--fail)",
            color: "var(--fail)",
            padding: "12px 16px",
            borderRadius: "2px",
            fontSize: "12px",
            background: "#ef444408",
          }}>
            {error}
          </div>
        ) : runs.length === 0 ? (
          <EmptyState />
        ) : (
          <div>
            {/* Table header */}
            <div style={{
              display: "grid",
              gridTemplateColumns: "1fr 90px 110px 80px 100px 60px",
              padding: "8px 16px",
              color: "var(--text-3)",
              fontSize: "10px",
              letterSpacing: "0.1em",
              borderBottom: "1px solid var(--border)",
            }}>
              <span>NAME</span>
              <span>STATUS</span>
              <span>PASS RATE</span>
              <span>RESULTS</span>
              <span>STARTED</span>
              <span></span>
            </div>

            {runs.map((run, i) => (
              <Link
                key={run.run_id}
                href={`/runs/${run.run_id}`}
                style={{
                  display: "grid",
                  gridTemplateColumns: "1fr 90px 110px 80px 100px 60px",
                  padding: "14px 16px",
                  borderBottom: i < runs.length - 1 ? "1px solid var(--border)" : "none",
                  textDecoration: "none",
                  color: "inherit",
                  alignItems: "center",
                  transition: "background 0.1s",
                  cursor: "pointer",
                }}
                onMouseEnter={e => (e.currentTarget.style.background = "var(--bg-2)")}
                onMouseLeave={e => (e.currentTarget.style.background = "transparent")}
              >
                <div>
                  <div style={{ fontWeight: 500, marginBottom: "2px", color: "var(--text)" }}>
                    {run.test.name}
                  </div>
                  <div style={{ color: "var(--text-3)", fontSize: "11px" }}>
                    {run.test.agent_endpoint}
                  </div>
                </div>
                <div><StatusBadge status={run.status} /></div>
                <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  <PassRateBar rate={run.pass_rate} />
                  <span style={{ color: "var(--text-2)", fontSize: "11px" }}>
                    {(run.pass_rate * 100).toFixed(0)}%
                  </span>
                </div>
                <div style={{ color: "var(--text-2)", fontSize: "12px" }}>
                  {run.passed}/{run.total_scenarios}
                </div>
                <div style={{ color: "var(--text-3)", fontSize: "11px" }}>
                  {new Date(run.started_at).toLocaleDateString()}
                </div>
                <div style={{ color: "var(--text-3)", fontSize: "11px", textAlign: "right" }}>
                  view →
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}