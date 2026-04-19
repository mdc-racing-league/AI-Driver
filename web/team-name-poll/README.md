# Team Name Poll

Anonymous ranked-choice poll used by the team to pick a name for the IBM Racing League squad.

- **Live URL:** https://mickeypress.zo.space/team-name
- **Hosting:** [Zo Space](https://mickeypress.zo.computer) (managed React pages + Hono API routes)
- **Storage:** JSON file at `ibmRacingLeague/poll-data.json` (in this repo, read/written at request time)

## How it works

- Voters drag-rank the names using ↑/↓ buttons (top = favorite)
- Anyone can suggest a new name (max 80 chars, no duplicates)
- Each submission is an ordered list; scoring uses **Borda count** (position i of N earns N−i points)
- Returning voters update their existing ballot via a `voteId` saved in `localStorage`
- Results (total points + vote count per name) are recomputed live by the GET endpoint

## File layout

```
web/team-name-poll/
├── pages/
│   └── team-name.tsx           # React page served at /team-name (public)
├── api/
│   ├── team-name.ts            # GET /api/team-name     — names + scored results
│   ├── team-name-vote.ts       # POST /api/team-name/vote — submit/update a ranking
│   └── team-name-add.ts        # POST /api/team-name/add  — add a new name
└── assets/
    └── racing-bg.png           # Background image (served at /images/racing-bg.png)
```

The sibling `poll-data.json` (one level up) holds the live names + votes.

## Redeploying the routes to Zo Space

These files are the source of truth for the deployed routes. Zo Space routes live in a managed
store (not on disk), so to redeploy them after editing here, ask Zo:

> "Re-sync the team-name poll routes from `ibmRacingLeague/web/team-name-poll/` to zo.space."

Zo will map each file to the matching route using `update_space_route`:

| File                              | Route path              | Type |
|-----------------------------------|-------------------------|------|
| `pages/team-name.tsx`             | `/team-name`            | page |
| `api/team-name.ts`                | `/api/team-name`        | api  |
| `api/team-name-vote.ts`           | `/api/team-name/vote`   | api  |
| `api/team-name-add.ts`            | `/api/team-name/add`    | api  |
| `assets/racing-bg.png`            | `/images/racing-bg.png` | asset |

## Notes

- The API routes are publicly accessible (no auth) by design — friends & family can vote.
- There is no identity check, so a motivated person could stuff the ballot by clearing cookies.
  For a small team poll this is accepted; add IP-based or bearer-token rate limiting if needed.
- No deadline is enforced; the poll is open until we decide to freeze it.
