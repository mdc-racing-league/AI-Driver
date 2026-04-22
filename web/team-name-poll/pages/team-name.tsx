import { useState, useEffect } from "react";
import { ArrowUp, ArrowDown, Plus, Check, Trophy, Share2 } from "lucide-react";

const STORAGE_KEY = "ibm-racing-team-name-vote-id";

type Name = { id: string; text: string; addedAt: string };
type Result = { id: string; text: string; score: number; voteCount: number };
type PollData = { names: Name[]; results: Result[]; totalVotes: number };

export default function TeamNamePoll() {
  const [data, setData] = useState<PollData | null>(null);
  const [ranking, setRanking] = useState<string[]>([]);
  const [newName, setNewName] = useState("");
  const [voteId, setVoteId] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [savedAt, setSavedAt] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    const stored = typeof window !== "undefined" ? localStorage.getItem(STORAGE_KEY) : null;
    if (stored) setVoteId(stored);
    loadData();
  }, []);

  async function loadData() {
    try {
      const res = await fetch("/api/team-name", { headers: { Accept: "application/json" } });
      const json: PollData = await res.json();
      setData(json);
      setRanking((prev) => {
        if (prev.length === 0) return json.names.map((n) => n.id);
        const existing = prev.filter((id) => json.names.some((n) => n.id === id));
        const added = json.names.filter((n) => !existing.includes(n.id)).map((n) => n.id);
        return [...existing, ...added];
      });
    } catch (e) {
      setError("Could not load poll data");
    }
  }

  function move(idx: number, dir: -1 | 1) {
    const target = idx + dir;
    if (target < 0 || target >= ranking.length) return;
    const next = [...ranking];
    [next[idx], next[target]] = [next[target], next[idx]];
    setRanking(next);
    setSavedAt(null);
  }

  async function addName(e: React.FormEvent) {
    e.preventDefault();
    const trimmed = newName.trim();
    if (!trimmed) return;
    setError(null);
    const res = await fetch("/api/team-name/add", {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify({ text: trimmed }),
    });
    if (!res.ok) {
      const j = await res.json().catch(() => ({}));
      setError(j.error || "Failed to add suggestion");
      return;
    }
    setNewName("");
    await loadData();
  }

  async function submit() {
    setSubmitting(true);
    setError(null);
    try {
      const res = await fetch("/api/team-name/vote", {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify({ voteId, ranking }),
      });
      const json = await res.json();
      if (!res.ok) {
        setError(json.error || "Failed to submit vote");
        return;
      }
      if (json.voteId) {
        localStorage.setItem(STORAGE_KEY, json.voteId);
        setVoteId(json.voteId);
      }
      setSavedAt(Date.now());
      await loadData();
    } finally {
      setSubmitting(false);
    }
  }

  async function shareLink() {
    const url = typeof window !== "undefined" ? window.location.href : "";
    try {
      await navigator.clipboard.writeText(url);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      setError("Could not copy link");
    }
  }

  if (!data) {
    return (
      <div className="min-h-screen bg-zinc-950 text-zinc-400 p-8 flex items-center justify-center">
        Loading…
      </div>
    );
  }

  const nameById = Object.fromEntries(data.names.map((n) => [n.id, n.text]));
  const maxScore = Math.max(1, ...data.results.map((r) => r.score));

  return (
    <div
      className="min-h-screen text-zinc-100 p-5 md:p-10 relative"
      style={{
        backgroundColor: "#09090b",
        backgroundImage:
          "linear-gradient(to bottom, rgba(9,9,11,0.85) 0%, rgba(9,9,11,0.92) 50%, rgba(9,9,11,0.98) 100%), url('/images/racing-bg.png')",
        backgroundSize: "cover",
        backgroundPosition: "center",
        backgroundAttachment: "fixed",
      }}
    >
      <div className="max-w-2xl mx-auto space-y-8 relative">
        <header>
          <div className="flex items-center justify-between gap-2 mb-4">
            <div className="flex items-center gap-3">
              <div className="flex flex-col items-center justify-center w-12 h-12 rounded-lg border-2 border-amber-400 bg-zinc-900/70 shadow-lg shadow-amber-500/10">
                <span className="text-amber-400 font-black text-sm leading-none tracking-tight">MDC</span>
                <span className="text-zinc-500 text-[7px] leading-none mt-0.5 tracking-widest">RACING</span>
              </div>
              <div className="flex items-center gap-2 text-amber-400 text-xs font-mono tracking-widest">
                <Trophy className="w-4 h-4" />
                <span>IBM RACING LEAGUE</span>
              </div>
            </div>
            <button
              onClick={shareLink}
              className="flex items-center gap-1.5 text-xs text-zinc-400 hover:text-zinc-100 border border-zinc-800 bg-zinc-900/70 rounded-md px-2.5 py-1.5 backdrop-blur"
            >
              <Share2 className="w-3.5 h-3.5" />
              {copied ? "Copied!" : "Share"}
            </button>
          </div>
          <h1 className="text-3xl md:text-4xl font-bold tracking-tight drop-shadow-lg">
            Vote on our team name
          </h1>
          <p className="text-zinc-300 mt-2 leading-relaxed">
            Rank the names from favorite (top) to least favorite (bottom), and add your own
            suggestions. The poll is anonymous — feel free to share with friends &amp; family.
            You can come back and change your ranking any time.
          </p>
        </header>

        <section className="bg-zinc-900/80 backdrop-blur border border-zinc-800 rounded-xl p-4 md:p-6 shadow-xl">
          <h2 className="font-semibold mb-4 text-lg">Your ranking</h2>
          <ul className="space-y-2">
            {ranking.map((id, idx) => (
              <li
                key={id}
                className="flex items-center gap-3 bg-zinc-800/60 border border-zinc-700/70 rounded-lg p-3"
              >
                <span className="text-zinc-500 font-mono w-6 text-right text-sm">
                  {idx + 1}.
                </span>
                <span className="flex-1 text-sm md:text-base">
                  {nameById[id] || "(removed)"}
                </span>
                <div className="flex flex-col gap-1">
                  <button
                    onClick={() => move(idx, -1)}
                    disabled={idx === 0}
                    aria-label="Move up"
                    className="p-1 rounded hover:bg-zinc-700 disabled:opacity-20"
                  >
                    <ArrowUp className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => move(idx, 1)}
                    disabled={idx === ranking.length - 1}
                    aria-label="Move down"
                    className="p-1 rounded hover:bg-zinc-700 disabled:opacity-20"
                  >
                    <ArrowDown className="w-4 h-4" />
                  </button>
                </div>
              </li>
            ))}
          </ul>

          <form onSubmit={addName} className="mt-4 flex gap-2">
            <input
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              placeholder="Suggest a new name…"
              maxLength={80}
              className="flex-1 bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-sm outline-none focus:border-amber-500"
            />
            <button
              type="submit"
              className="flex items-center gap-1 bg-zinc-700 hover:bg-zinc-600 text-sm font-medium rounded-lg px-3 py-2"
            >
              <Plus className="w-4 h-4" /> Add
            </button>
          </form>

          <div className="mt-5 flex items-center gap-3 flex-wrap">
            <button
              onClick={submit}
              disabled={submitting}
              className="flex items-center gap-2 bg-amber-500 hover:bg-amber-400 text-zinc-900 font-semibold rounded-lg px-4 py-2 disabled:opacity-50"
            >
              <Check className="w-4 h-4" />
              {voteId ? "Update my ranking" : "Submit my ranking"}
            </button>
            {savedAt && <span className="text-emerald-400 text-sm">Saved ✓</span>}
            {error && <span className="text-red-400 text-sm">{error}</span>}
          </div>
        </section>

        <section className="bg-zinc-900/60 backdrop-blur border border-zinc-800 rounded-xl p-4 md:p-6">
          <div className="flex items-baseline justify-between mb-3">
            <h2 className="font-semibold text-lg">Live results</h2>
            <span className="text-zinc-500 text-sm">
              {data.totalVotes} {data.totalVotes === 1 ? "vote" : "votes"}
            </span>
          </div>
          {data.totalVotes === 0 ? (
            <p className="text-zinc-500 text-sm italic">
              No votes yet — be the first to submit a ranking.
            </p>
          ) : (
            <ul className="space-y-2">
              {data.results.map((r, i) => (
                <li
                  key={r.id}
                  className="bg-zinc-900/60 border border-zinc-800 rounded-lg p-3"
                >
                  <div className="flex items-baseline justify-between text-sm gap-3">
                    <span className="truncate">
                      <span className="text-zinc-500 mr-2">#{i + 1}</span>
                      {r.text}
                    </span>
                    <span className="text-zinc-500 font-mono text-xs shrink-0">
                      {r.score} pts · {r.voteCount} {r.voteCount === 1 ? "vote" : "votes"}
                    </span>
                  </div>
                  <div className="mt-2 bg-zinc-800 rounded-full h-2 overflow-hidden">
                    <div
                      className="bg-amber-500 h-full transition-all"
                      style={{ width: `${(r.score / maxScore) * 100}%` }}
                    />
                  </div>
                </li>
              ))}
            </ul>
          )}
          <p className="text-xs text-zinc-500 mt-3 leading-relaxed">
            Scoring: for each vote, #1 gets the most points (N where N = list size), #2 gets
            N−1, and so on. Higher score = more preferred.
          </p>
        </section>

        <footer className="text-center text-xs text-zinc-600 pt-4">
          Anonymous poll · Your ranking is remembered on this device so you can update it later
        </footer>
      </div>
    </div>
  );
}
