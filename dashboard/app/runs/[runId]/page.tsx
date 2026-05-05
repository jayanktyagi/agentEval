// app/runs/[runId]/page.tsx — run detail + trace viewer
"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import Navbar from "@/components/Navbar";
import StatusBadge from "@/components/StatusBadge";
import { getRun, TestRun, ScenarioResult, ToolCall } from "@/lib/api";

function TraceStep({ call }: { call: ToolCall }) {
  const [open, setOpen] = useState(false);

  return (
    <div style={{
      borderLeft: "1px solid var(--border)",
      marginLeft: "12px",
    }}>
      <div
        onClick={() => setOpen(!open)}
        style={{
          display: "flex",
          alignItems: "center",
          gap: "10px",
          padding: "8px 16px",
          cursor: "pointer",
          borderBottom: "1px solid var(--border)",
        }}
      >
        <span style={{
          width: "20px",
          height: "20px",
          borderRadius: "50%",
          border: "1px solid var(--border-2)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: "9px",
          color: "var(--text-3)",
          flexShrink: 0,
          marginLeft: "-10px",
          background: "var(--bg)",
        }}>
          {call.step}
        </span>
        <span style={{ color: "var(--green)", fontWeight: 600 }}>{call.tool_name}</span>
        <span style={{
          color: call.status === "success" ? "var(--text-3)" : "var(--red)",
          fontSize: "11px",
          marginLeft: "auto",
        }}>
          {call.duration_ms}ms
        </span>
        <span style={{ color: "var(--text-3)", fontSize: "11px" }}>{open ? "▲" : "▼"}</span>
      </div>

      {open && (
        <div style={{ padding: "12px 16px 12px 26px", background: "var(--bg-2)" }}>
          <div style={{ marginBottom: "10px" }}>
            <div style={{ color: "var(--text-3)", fontSize: "10px", letterSpacing: "0.08em", marginBottom: "4px" }}>
              PARAMETERS
            </div>
            <pre style={{
              color: "var(--text-2)",
              fontSize: "11px",
              whiteSpace: "pre-wrap",
              wordBreak: "break-all",
            }}>
              {JSON.stringify(call.parameters, null, 2)}
            </pre>
          </div>
          {call.response !== null && (
            <div>
              <div style={{ color: "var(--text-3)", fontSize: "10px", letterSpacing: "0.08em", marginBottom: "4px" }}>
                RESPONSE
              </div>
              <pre style={{
                color: "var(--text-2)",
                fontSize: "11px",
                whiteSpace: "pre-wrap",
                wordBreak: "break-all",
              }}>
                {JSON.stringify(call.response, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function ScenarioCard({ result }: { result: ScenarioResult }) {
  const [open, setOpen] = useState(false);

  return (
    <div style={{
      border: "1px solid var(--border)",
      borderRadius: "4px",
      overflow: "hidden",
      marginBottom: "8px",
    }}>
      {/* Header */}
      <div
        onClick={() => setOpen(!open)}
        style={{
          display: "flex",
          alignItems: "center",
          gap: "12px",
          padding: "12px 16px",
          cursor: "pointer",
          background: result.status === "passed" ? "var(--bg-2)" : "#1a0a0a",
        }}
      >
        <StatusBadge status={result.status} />
        <StatusBadge status={result.scenario.scenario_type} />
        <span style={{ fontWeight: 500, flex: 1 }}>{result.scenario.title}</span>
        <span style={{ color: "var(--text-3)", fontSize: "11px" }}>
          {result.trace.total_steps} steps
        </span>
        <span style={{ color: "var(--text-3)", fontSize: "11px" }}>
          {(result.tool_accuracy * 100).toFixed(0)}% accuracy
        </span>
        <span style={{ color: "var(--text-3)", fontSize: "11px" }}>{open ? "▲" : "▼"}</span>
      </div>

      {/* Failure detail */}
      {result.status === "failed" && result.failure_detail && (
        <div style={{
          padding: "8px 16px",
          background: "#1a0a0a",
          borderTop: "1px solid var(--red)22",
          color: "var(--red)",
          fontSize: "11px",
        }}>
          {result.failure_reason && (
            <span style={{ marginRight: "12px", opacity: 0.7 }}>[{result.failure_reason}]</span>
          )}
          {result.failure_detail}
        </div>
      )}

      {/* Trace viewer */}
      {open && (
        <div style={{ borderTop: "1px solid var(--border)", padding: "16px" }}>
          <div style={{ color: "var(--text-3)", fontSize: "10px", letterSpacing: "0.08em", marginBottom: "12px" }}>
            EXECUTION TRACE
          </div>
          <div style={{ color: "var(--text-3)", fontSize: "11px", marginBottom: "12px" }}>
            task: <span style={{ color: "var(--text-2)" }}>{result.trace.task}</span>
          </div>

          {result.trace.tool_calls.length === 0 ? (
            <div style={{ color: "var(--text-3)", fontSize: "11px" }}>no tool calls recorded</div>
          ) : (
            result.trace.tool_calls.map((call) => (
              <TraceStep key={call.step} call={call} />
            ))
          )}

          {result.trace.loop_detected && (
            <div style={{
              marginTop: "12px",
              padding: "8px 12px",
              background: "var(--yellow)11",
              border: "1px solid var(--yellow)33",
              color: "var(--yellow)",
              fontSize: "11px",
              borderRadius: "2px",
            }}>
              loop detected at step {result.trace.loop_at_step}
            </div>
          )}

          {result.trace.final_output && (
            <div style={{ marginTop: "12px" }}>
              <div style={{ color: "var(--text-3)", fontSize: "10px", letterSpacing: "0.08em", marginBottom: "6px" }}>
                FINAL OUTPUT
              </div>
              <div style={{ color: "var(--text-2)", fontSize: "11px" }}>
                {result.trace.final_output}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function RunPage() {
  const params = useParams();
  const runId = params.runId as string;

  const [run, setRun] = useState<TestRun | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchRun = async () => {
    try {
      const data = await getRun(runId);
      setRun(data);
      setError(null);
    } catch {
      setError("Failed to load run");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRun();
    const interval = setInterval(() => {
      if (run?.status === "running") fetchRun();
    }, 2000);
    return () => clearInterval(interval);
  }, [run?.status]);

  return (
    <div style={{ minHeight: "100vh", background: "var(--bg)" }}>
      <Navbar />
      <div style={{ padding: "32px 24px", maxWidth: "960px", margin: "0 auto" }}>

        {loading ? (
          <div style={{ color: "var(--text-3)", padding: "40px 0" }}>loading...</div>
        ) : error ? (
          <div style={{ color: "var(--red)" }}>{error}</div>
        ) : !run ? null : (
          <>
            {/* Breadcrumb */}
            <div style={{ color: "var(--text-3)", fontSize: "11px", marginBottom: "24px" }}>
              <Link href="/" style={{ color: "var(--text-3)", textDecoration: "none" }}>runs</Link>
              <span style={{ margin: "0 8px" }}>→</span>
              <span style={{ color: "var(--text-2)" }}>{run.test.name}</span>
            </div>

            {/* Run header */}
            <div style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "flex-start",
              marginBottom: "24px",
            }}>
              <div>
                <div style={{ fontSize: "20px", fontWeight: 600, letterSpacing: "-0.02em", marginBottom: "6px" }}>
                  {run.test.name}
                </div>
                <div style={{ color: "var(--text-3)", fontSize: "11px" }}>
                  {run.test.agent_endpoint}
                </div>
              </div>
              <StatusBadge status={run.status} size="md" />
            </div>

            {/* Stats */}
            <div style={{
              display: "grid",
              gridTemplateColumns: "repeat(4, 1fr)",
              gap: "1px",
              background: "var(--border)",
              border: "1px solid var(--border)",
              borderRadius: "4px",
              marginBottom: "24px",
              overflow: "hidden",
            }}>
              {[
                { label: "pass rate", value: `${(run.pass_rate * 100).toFixed(0)}%`, color: run.pass_rate >= 0.8 ? "var(--green)" : run.pass_rate >= 0.5 ? "var(--yellow)" : "var(--red)" },
                { label: "passed", value: String(run.passed), color: "var(--green)" },
                { label: "failed", value: String(run.failed), color: run.failed > 0 ? "var(--red)" : "var(--text-3)" },
                { label: "total", value: String(run.total_scenarios), color: "var(--text)" },
              ].map(({ label, value, color }) => (
                <div key={label} style={{ background: "var(--bg-2)", padding: "16px 20px" }}>
                  <div style={{ color: "var(--text-3)", fontSize: "10px", letterSpacing: "0.1em", marginBottom: "6px" }}>
                    {label.toUpperCase()}
                  </div>
                  <div style={{ fontSize: "22px", fontWeight: 600, color }}>
                    {value}
                  </div>
                </div>
              ))}
            </div>

            {/* Agent info */}
            <div style={{
              border: "1px solid var(--border)",
              borderRadius: "4px",
              padding: "16px 20px",
              marginBottom: "24px",
              background: "var(--bg-2)",
            }}>
              <div style={{ color: "var(--text-3)", fontSize: "10px", letterSpacing: "0.1em", marginBottom: "10px" }}>
                AGENT CONFIG
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
                <div>
                  <div style={{ color: "var(--text-3)", fontSize: "10px", marginBottom: "3px" }}>task</div>
                  <div style={{ color: "var(--text-2)", fontSize: "12px" }}>{run.test.task_description}</div>
                </div>
                <div>
                  <div style={{ color: "var(--text-3)", fontSize: "10px", marginBottom: "3px" }}>expected tools</div>
                  <div style={{ color: "var(--text-2)", fontSize: "12px" }}>
                    {run.test.expected_tools.join(", ")}
                  </div>
                </div>
              </div>
            </div>

            {/* Scenarios */}
            <div>
              <div style={{ color: "var(--text-3)", fontSize: "10px", letterSpacing: "0.1em", marginBottom: "12px" }}>
                SCENARIOS ({run.results.length})
              </div>
              {run.status === "running" && run.results.length === 0 && (
                <div style={{ color: "var(--blue)", fontSize: "12px", padding: "20px 0" }}>
                  generating scenarios and running tests...
                </div>
              )}
              {run.results.map((result) => (
                <ScenarioCard key={result.result_id} result={result} />
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
}