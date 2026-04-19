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
  const text = String(body?.text ?? "").trim();
  if (!text) return c.json({ error: "text is required" }, 400);
  if (text.length > 80) return c.json({ error: "too long (max 80 chars)" }, 400);
  const data = await loadData();
  if (data.names.some((n) => n.text.toLowerCase() === text.toLowerCase())) {
    return c.json({ error: "that name already exists" }, 409);
  }
  if (data.names.length >= 50) {
    return c.json({ error: "too many names (50 max)" }, 400);
  }
  const entry: Name = { id: randomUUID(), text, addedAt: new Date().toISOString() };
  data.names.push(entry);
  await saveData(data);
  return c.json(entry);
};
