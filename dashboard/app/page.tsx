// app/page.tsx — runs list page
"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import Navbar from "@/components/Navbar";
import StatusBadge from "@/components/StatusBadge";
import { getRuns, TestRun } from "@/lib/api";

function PassRateBar({ rate }: { rate: number }) {
  return (
    <div style={{
      width: "80px",
      height: "4px",
      background: "var(--border)",
      borderRadius: "2px",
      overflow: "hidden",
    }}>
      <div style={{
        width: `${rate * 100}%`,
        height: "100%",
        background: rate >= 0.8 ? "var(--green)" : rate >= 0.5 ? "var(--yellow)" : "var(--red)",
        borderRadius: "2px",
        transition: "width 0.5s ease",
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
      gap: "16px",
      color: "var(--text-3)",
    }}>
      <div style={{ fontSize: "32px", letterSpacing: "-0.02em", color: "var(--text-2)" }}>
        no runs yet
      </div>
      <div style={{ fontSize: "12px", color: "var(--text-3)", maxWidth: "320px", textAlign: "center" }}>
        submit your first agent test to see results here
      </div>
      <Link href="/new" style={{
        marginTop: "8px",
        color: "var(--green)",
        textDecoration: "none",
        fontSize: "12px",
        border: "1px solid var(--green)33",
        padding: "8px 20px",
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
      setError("Cannot connect to AgentEval API — make sure the backend is running on port 8000");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRuns();
    // Poll every 3 seconds if any run is still running
    const interval = setInterval(() => {
      const hasRunning = runs.some(r => r.status === "running");
      if (hasRunning) fetchRuns();
    }, 3000);
    return () => clearInterval(interval);
  }, [runs.length]);

  const totalRuns = runs.length;
  const avgPassRate = runs.length
    ? runs.reduce((sum, r) => sum + r.pass_rate, 0) / runs.length
    : 0;
  const runningCount = runs.filter(r => r.status === "running").length;

  return (
    <div style={{ minHeight: "100vh", background: "var(--bg)" }}>
      <Navbar />

      <div style={{ padding: "32px 24px", maxWidth: "960px", margin: "0 auto" }}>

        {/* Header */}
        <div style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-end",
          marginBottom: "32px",
        }}>
          <div>
            <div style={{ color: "var(--text-3)", fontSize: "11px", letterSpacing: "0.1em", marginBottom: "6px" }}>
              TEST RUNS
            </div>
            <div style={{ fontSize: "22px", fontWeight: 600, letterSpacing: "-0.02em" }}>
              all runs
            </div>
          </div>
          {runningCount > 0 && (
            <div style={{ color: "var(--blue)", fontSize: "11px", letterSpacing: "0.05em" }}>
              {runningCount} running...
            </div>
          )}
        </div>

        {/* Stats row */}
        {totalRuns > 0 && (
          <div style={{
            display: "grid",
            gridTemplateColumns: "repeat(3, 1fr)",
            gap: "1px",
            background: "var(--border)",
            border: "1px solid var(--border)",
            borderRadius: "4px",
            marginBottom: "24px",
            overflow: "hidden",
          }}>
            {[
              { label: "total runs", value: totalRuns },
              { label: "avg pass rate", value: `${(avgPassRate * 100).toFixed(0)}%` },
              { label: "running", value: runningCount },
            ].map(({ label, value }) => (
              <div key={label} style={{
                background: "var(--bg-2)",
                padding: "16px 20px",
              }}>
                <div style={{ color: "var(--text-3)", fontSize: "10px", letterSpacing: "0.1em", marginBottom: "6px" }}>
                  {label.toUpperCase()}
                </div>
                <div style={{ fontSize: "20px", fontWeight: 600, color: "var(--text)" }}>
                  {value}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Content */}
        {loading ? (
          <div style={{ color: "var(--text-3)", padding: "40px 0", textAlign: "center" }}>
            loading...
          </div>
        ) : error ? (
          <div style={{
            border: "1px solid var(--red)33",
            background: "var(--red)11",
            color: "var(--red)",
            padding: "16px 20px",
            borderRadius: "4px",
            fontSize: "12px",
          }}>
            {error}
          </div>
        ) : runs.length === 0 ? (
          <EmptyState />
        ) : (
          <div style={{
            border: "1px solid var(--border)",
            borderRadius: "4px",
            overflow: "hidden",
          }}>
            {/* Table header */}
            <div style={{
              display: "grid",
              gridTemplateColumns: "1fr 120px 100px 100px 90px 80px",
              padding: "10px 20px",
              background: "var(--bg-2)",
              borderBottom: "1px solid var(--border)",
              color: "var(--text-3)",
              fontSize: "10px",
              letterSpacing: "0.1em",
            }}>
              <span>NAME</span>
              <span>STATUS</span>
              <span>PASS RATE</span>
              <span>SCENARIOS</span>
              <span>STARTED</span>
              <span></span>
            </div>

            {/* Rows */}
            {runs.map((run, i) => (
              <Link
                key={run.run_id}
                href={`/runs/${run.run_id}`}
                style={{
                  display: "grid",
                  gridTemplateColumns: "1fr 120px 100px 100px 90px 80px",
                  padding: "14px 20px",
                  borderBottom: i < runs.length - 1 ? "1px solid var(--border)" : "none",
                  textDecoration: "none",
                  color: "inherit",
                  background: "var(--bg)",
                  alignItems: "center",
                  transition: "background 0.15s",
                }}
                onMouseEnter={e => (e.currentTarget.style.background = "var(--bg-2)")}
                onMouseLeave={e => (e.currentTarget.style.background = "var(--bg)")}
              >
                <div>
                  <div style={{ fontWeight: 500, marginBottom: "2px" }}>{run.test.name}</div>
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
                <div style={{ color: "var(--text-2)" }}>
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