// app/new/page.tsx — submit a new test run
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Navbar from "@/components/Navbar";
import { submitRun } from "@/lib/api";

export default function NewRunPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [form, setForm] = useState({
    name: "",
    agent_endpoint: "",
    task_description: "",
    expected_tools: "",
    max_steps: "10",
  });

  const handleSubmit = async () => {
    if (!form.name || !form.agent_endpoint || !form.task_description || !form.expected_tools) {
      setError("all fields are required");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const run = await submitRun({
        name: form.name,
        agent_endpoint: form.agent_endpoint,
        task_description: form.task_description,
        expected_tools: form.expected_tools.split(",").map(t => t.trim()).filter(Boolean),
        max_steps: parseInt(form.max_steps) || 10,
      });
      router.push(`/runs/${run.run_id}`);
    } catch {
      setError("failed to submit run — is the backend running?");
      setLoading(false);
    }
  };

  const inputStyle = {
    width: "100%",
    background: "var(--bg-2)",
    border: "1px solid var(--border)",
    borderRadius: "2px",
    padding: "10px 14px",
    color: "var(--text)",
    fontFamily: "inherit",
    fontSize: "13px",
    outline: "none",
  };

  const labelStyle = {
    display: "block",
    color: "var(--text-3)",
    fontSize: "10px",
    letterSpacing: "0.1em",
    marginBottom: "6px",
  };

  return (
    <div style={{ minHeight: "100vh", background: "var(--bg)" }}>
      <Navbar />
      <div style={{ padding: "32px 24px", maxWidth: "600px", margin: "0 auto" }}>

        <div style={{ marginBottom: "32px" }}>
          <div style={{ color: "var(--text-3)", fontSize: "11px", letterSpacing: "0.1em", marginBottom: "6px" }}>
            NEW RUN
          </div>
          <div style={{ fontSize: "22px", fontWeight: 600, letterSpacing: "-0.02em" }}>
            submit agent test
          </div>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
          <div>
            <label style={labelStyle}>RUN NAME</label>
            <input
              style={inputStyle}
              placeholder="My Flight Booking Agent"
              value={form.name}
              onChange={e => setForm({ ...form, name: e.target.value })}
            />
          </div>

          <div>
            <label style={labelStyle}>AGENT ENDPOINT</label>
            <input
              style={inputStyle}
              placeholder="http://localhost:9000/run"
              value={form.agent_endpoint}
              onChange={e => setForm({ ...form, agent_endpoint: e.target.value })}
            />
          </div>

          <div>
            <label style={labelStyle}>TASK DESCRIPTION</label>
            <textarea
              style={{ ...inputStyle, resize: "vertical", minHeight: "80px" }}
              placeholder="Book a flight from Karachi to Dubai for next Friday"
              value={form.task_description}
              onChange={e => setForm({ ...form, task_description: e.target.value })}
            />
          </div>

          <div>
            <label style={labelStyle}>EXPECTED TOOLS (comma separated)</label>
            <input
              style={inputStyle}
              placeholder="search_flights, check_availability, book_ticket"
              value={form.expected_tools}
              onChange={e => setForm({ ...form, expected_tools: e.target.value })}
            />
          </div>

          <div>
            <label style={labelStyle}>MAX STEPS</label>
            <input
              style={{ ...inputStyle, width: "120px" }}
              type="number"
              min="1"
              max="100"
              value={form.max_steps}
              onChange={e => setForm({ ...form, max_steps: e.target.value })}
            />
          </div>

          {error && (
            <div style={{
              color: "var(--red)",
              fontSize: "12px",
              padding: "10px 14px",
              border: "1px solid var(--red)33",
              background: "var(--red)11",
              borderRadius: "2px",
            }}>
              {error}
            </div>
          )}

          <div style={{ display: "flex", gap: "12px", paddingTop: "8px" }}>
            <button
              onClick={handleSubmit}
              disabled={loading}
              style={{
                background: loading ? "var(--border)" : "var(--green)",
                color: loading ? "var(--text-3)" : "var(--bg)",
                border: "none",
                borderRadius: "2px",
                padding: "10px 24px",
                fontFamily: "inherit",
                fontSize: "12px",
                fontWeight: 600,
                letterSpacing: "0.05em",
                cursor: loading ? "not-allowed" : "pointer",
              }}
            >
              {loading ? "submitting..." : "submit run"}
            </button>

            <button
              onClick={() => router.back()}
              style={{
                background: "transparent",
                color: "var(--text-3)",
                border: "1px solid var(--border)",
                borderRadius: "2px",
                padding: "10px 24px",
                fontFamily: "inherit",
                fontSize: "12px",
                cursor: "pointer",
              }}
            >
              cancel
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}