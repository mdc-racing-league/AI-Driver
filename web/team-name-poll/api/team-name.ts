import { readFile } from "node:fs/promises";
import type { Context } from "hono";

const DATA_PATH = "/home/workspace/ibmRacingLeague/poll-data.json";

type Name = { id: string; text: string; addedAt: string };
type Vote = { id: string; ranking: string[]; submittedAt: string };
type Data = { names: Name[]; votes: Vote[] };

async function loadData(): Promise<Data> {
  try {
    const raw = await readFile(DATA_PATH, "utf-8");
    return JSON.parse(raw);
  } catch {
    return { names: [], votes: [] };
  }
}

export default async (c: Context) => {
  const data = await loadData();
  const scores: Record<string, { score: number; voteCount: number }> = {};
  for (const n of data.names) scores[n.id] = { score: 0, voteCount: 0 };
  for (const v of data.votes) {
    const len = v.ranking.length;
    for (let i = 0; i < len; i++) {
      const id = v.ranking[i];
      if (!scores[id]) continue;
      scores[id].score += len - i;
      scores[id].voteCount += 1;
    }
  }
  const results = data.names
    .map((n) => ({
      id: n.id,
      text: n.text,
      score: scores[n.id].score,
      voteCount: scores[n.id].voteCount,
    }))
    .sort((a, b) => b.score - a.score);
  return c.json({ names: data.names, results, totalVotes: data.votes.length });
};
