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
    <div style={{ borderLeft: "1px solid var(--border)", marginLeft: "8px" }}>
      <div
        onClick={() => setOpen(!open)}
        style={{
          display: "flex",
          alignItems: "center",
          gap: "10px",
          padding: "7px 14px",
          cursor: "pointer",
          borderBottom: "1px solid var(--border)",
        }}
      >
        <span style={{
          width: "18px",
          height: "18px",
          borderRadius: "50%",
          border: "1px solid var(--border-2)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: "9px",
          color: "var(--text-3)",
          flexShrink: 0,
          marginLeft: "-9px",
          background: "var(--bg)",
        }}>
          {call.step}
        </span>
        <span style={{ color: "var(--pass)", fontWeight: 600, fontSize: "12px" }}>
          {call.tool_name}
        </span>
        <span style={{
          color: call.status === "success" ? "var(--text-3)" : "var(--fail)",
          fontSize: "11px",
          marginLeft: "auto",
        }}>
          {call.duration_ms}ms
        </span>
        <span style={{ color: "var(--text-3)", fontSize: "10px" }}>{open ? "▲" : "▼"}</span>
      </div>

      {open && (
        <div style={{ padding: "10px 14px 10px 24px", background: "var(--bg-2)" }}>
          <div style={{ marginBottom: "8px" }}>
            <div style={{ color: "var(--text-3)", fontSize: "10px", letterSpacing: "0.08em", marginBottom: "4px" }}>
              PARAMETERS
            </div>
            <pre style={{ color: "var(--text-2)", fontSize: "11px", whiteSpace: "pre-wrap", wordBreak: "break-all" }}>
              {JSON.stringify(call.parameters, null, 2)}
            </pre>
          </div>
          {call.response !== null && (
            <div>
              <div style={{ color: "var(--text-3)", fontSize: "10px", letterSpacing: "0.08em", marginBottom: "4px" }}>
                RESPONSE
              </div>
              <pre style={{ color: "var(--text-2)", fontSize: "11px", whiteSpace: "pre-wrap", wordBreak: "break-all" }}>
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
  const passed = result.status === "passed";

  return (
    <div style={{
      border: `1px solid ${passed ? "var(--border)" : "var(--fail)22"}`,
      borderRadius: "2px",
      overflow: "hidden",
      marginBottom: "6px",
    }}>
      <div
        onClick={() => setOpen(!open)}
        style={{
          display: "flex",
          alignItems: "center",
          gap: "10px",
          padding: "10px 14px",
          cursor: "pointer",
          background: passed ? "var(--bg)" : "#ef444406",
        }}
      >
        <StatusBadge status={result.status} />
        <span style={{
          fontSize: "10px",
          color: "var(--text-3)",
          border: "1px solid var(--border)",
          padding: "1px 6px",
          borderRadius: "2px",
          letterSpacing: "0.06em",
        }}>
          {result.scenario.scenario_type.replace("_", " ").toUpperCase()}
        </span>
        <span style={{ fontWeight: 500, flex: 1, fontSize: "12px" }}>
          {result.scenario.title}
        </span>
        <span style={{ color: "var(--text-3)", fontSize: "11px" }}>
          {result.trace.total_steps} steps
        </span>
        <span style={{ color: "var(--text-3)", fontSize: "11px" }}>
          {(result.tool_accuracy * 100).toFixed(0)}%
        </span>
        <span style={{ color: "var(--text-3)", fontSize: "11px" }}>{open ? "▲" : "▼"}</span>
      </div>

      {result.status === "failed" && result.failure_detail && (
        <div style={{
          padding: "6px 14px",
          background: "#ef444406",
          borderTop: "1px solid var(--fail)22",
          color: "var(--fail)",
          fontSize: "11px",
        }}>
          <span style={{ opacity: 0.6, marginRight: "10px" }}>[{result.failure_reason}]</span>
          {result.failure_detail}
        </div>
      )}

      {open && (
        <div style={{ borderTop: "1px solid var(--border)", padding: "14px" }}>
          <div style={{ color: "var(--text-3)", fontSize: "10px", letterSpacing: "0.08em", marginBottom: "10px" }}>
            EXECUTION TRACE
          </div>
          <div style={{ color: "var(--text-3)", fontSize: "11px", marginBottom: "10px" }}>
            task: <span style={{ color: "var(--text-2)" }}>{result.trace.task}</span>
          </div>

          {result.trace.tool_calls.length === 0 ? (
            <div style={{ color: "var(--text-3)", fontSize: "11px" }}>no tool calls recorded</div>
          ) : (
            result.trace.tool_calls.map(call => (
              <TraceStep key={call.step} call={call} />
            ))
          )}

          {result.trace.loop_detected && (
            <div style={{
              marginTop: "10px",
              padding: "7px 12px",
              border: "1px solid var(--fail)33",
              color: "var(--fail)",
              fontSize: "11px",
              borderRadius: "2px",
            }}>
              loop detected at step {result.trace.loop_at_step}
            </div>
          )}

          {result.trace.final_output && (
            <div style={{ marginTop: "10px" }}>
              <div style={{ color: "var(--text-3)", fontSize: "10px", letterSpacing: "0.08em", marginBottom: "4px" }}>
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
    } catch {
      setError("failed to load run");
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
      <div style={{ padding: "32px 24px", maxWidth: "900px", margin: "0 auto" }}>

        {loading ? (
          <div style={{ color: "var(--text-3)", fontSize: "12px" }}>loading...</div>
        ) : error ? (
          <div style={{ color: "var(--fail)", fontSize: "12px" }}>{error}</div>
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
              paddingBottom: "16px",
              borderBottom: "1px solid var(--border)",
            }}>
              <div>
                <div style={{ fontSize: "18px", fontWeight: 600, marginBottom: "4px" }}>
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
              borderRadius: "2px",
              marginBottom: "24px",
              overflow: "hidden",
            }}>
              {[
                { label: "pass rate", value: `${(run.pass_rate * 100).toFixed(0)}%`, color: run.pass_rate >= 0.8 ? "var(--pass)" : run.pass_rate >= 0.5 ? "var(--text)" : "var(--fail)" },
                { label: "passed", value: String(run.passed), color: "var(--pass)" },
                { label: "failed", value: String(run.failed), color: run.failed > 0 ? "var(--fail)" : "var(--text-3)" },
                { label: "total", value: String(run.total_scenarios), color: "var(--text)" },
              ].map(({ label, value, color }) => (
                <div key={label} style={{ background: "var(--bg-2)", padding: "14px 18px" }}>
                  <div style={{ color: "var(--text-3)", fontSize: "10px", letterSpacing: "0.1em", marginBottom: "4px" }}>
                    {label.toUpperCase()}
                  </div>
                  <div style={{ fontSize: "20px", fontWeight: 600, color }}>
                    {value}
                  </div>
                </div>
              ))}
            </div>

            {/* Agent config */}
            <div style={{
              border: "1px solid var(--border)",
              borderRadius: "2px",
              padding: "14px 18px",
              marginBottom: "24px",
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
              <div style={{
                color: "var(--text-3)",
                fontSize: "10px",
                letterSpacing: "0.1em",
                marginBottom: "12px",
                display: "flex",
                justifyContent: "space-between",
              }}>
                <span>SCENARIOS ({run.results.length})</span>
                {run.status === "running" && (
                  <span style={{ color: "var(--text-2)" }}>running...</span>
                )}
              </div>

              {run.results.length === 0 && run.status === "running" && (
                <div style={{ color: "var(--text-3)", fontSize: "12px", padding: "20px 0" }}>
                  generating scenarios...
                </div>
              )}

              {run.results.map(result => (
                <ScenarioCard key={result.result_id} result={result} />
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
}