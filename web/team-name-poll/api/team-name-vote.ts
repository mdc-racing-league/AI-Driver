import { readFile, writeFile, mkdir } from "node:fs/promises";
import { dirname } from "node:path";
import { randomUUID } from "node:crypto";
import type { Context } from "hono";

const DATA_PATH = "/home/workspace/ibmRacingLeague/poll-data.json";

type Name = { id: string; text: string; addedAt: string };
type Vote = { id: string; ranking: string[]; submittedAt: string };
type Data = { names: Name[]; votes: Vote[] };

async function loadData(): Promise<Data> {
  try {
    return JSON.parse(await readFile(DATA_PATH, "utf-8"));
  } catch {
    return { names: [], votes: [] };
  }
}

async function saveData(data: Data) {
  await mkdir(dirname(DATA_PATH), { recursive: true });
  await writeFile(DATA_PATH, JSON.stringify(data, null, 2));
}

export default async (c: Context) => {
  const body = await c.req.json().catch(() => ({}));
  const { voteId, ranking } = body as { voteId?: string; ranking?: string[] };
  if (!Array.isArray(ranking) || ranking.length === 0) {
    return c.json({ error: "ranking must be a non-empty array" }, 400);
  }
  const data = await loadData();
  const validIds = new Set(data.names.map((n) => n.id));
  const filtered = ranking.filter((id) => typeof id === "string" && validIds.has(id));
  const deduped = Array.from(new Set(filtered));
  if (deduped.length === 0) {
    return c.json({ error: "ranking contains no valid names" }, 400);
  }
  const now = new Date().toISOString();
  let id = voteId;
  const existingIdx = id ? data.votes.findIndex((v) => v.id === id) : -1;
  if (id && existingIdx !== -1) {
    data.votes[existingIdx] = { id, ranking: deduped, submittedAt: now };
  } else {
    id = randomUUID();
    data.votes.push({ id, ranking: deduped, submittedAt: now });
  }
  await saveData(data);
  return c.json({ voteId: id, totalVotes: data.votes.length });
};
