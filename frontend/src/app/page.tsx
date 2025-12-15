/* eslint-disable @next/next/no-img-element */
"use client";

import { useMemo, useState } from "react";

type LinkedInProfile = {
  name: string;
  headline?: string | null;
  bio?: string | null; // using bio to hold LinkedIn URL if provided
  experience?: string[] | null;
  skills?: string[] | null;
  education?: string[] | null;
};

type Player = {
  name: string;
  health: number;
  profile: LinkedInProfile;
};

type GameState = {
  game_id: string;
  player1: Player;
  player2: Player;
  current_turn: 1 | 2;
  status: "setup" | "in_progress" | "finished";
  last_roast?: string | null;
  last_damage?: number | null;
  winner?: 1 | 2 | null;
  round_number: number;
};

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE?.replace(/\/$/, "") || "http://localhost:8000";

const initialProfile = { name: "", headline: "", bio: "" };

export default function Home() {
  const [player1, setPlayer1] = useState(initialProfile);
  const [player2, setPlayer2] = useState(initialProfile);
  const [game, setGame] = useState<GameState | null>(null);
  const [roastDraft, setRoastDraft] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const status = game?.status ?? "setup";

  const currentPlayer = useMemo(() => {
    if (!game) return null;
    return game.current_turn === 1 ? game.player1 : game.player2;
  }, [game]);

  const opponentPlayer = useMemo(() => {
    if (!game) return null;
    return game.current_turn === 1 ? game.player2 : game.player1;
  }, [game]);

  const reset = () => {
    setGame(null);
    setRoastDraft(null);
    setError(null);
  };

  const startGame = async () => {
    setLoading(true);
    setError(null);
    try {
      const payload = {
        player1_profile: {
          name: player1.name,
          bio: player1.bio || undefined, // storing LinkedIn URL in bio until backend adds dedicated field
        },
        player2_profile: {
          name: player2.name,
          bio: player2.bio || undefined,
        },
      };

      const res = await fetch(`${API_BASE}/api/game/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      setGame(data.game_state);
    } catch (e: any) {
      setError(e?.message || "Failed to start game");
    } finally {
      setLoading(false);
    }
  };

  const generateRoast = async () => {
    if (!game) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/game/${game.game_id}/roast`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          game_id: game.game_id,
          player_number: game.current_turn,
        }),
      });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      setRoastDraft(data.roast);
    } catch (e: any) {
      setError(e?.message || "Failed to generate roast");
    } finally {
      setLoading(false);
    }
  };

  const reviewRoast = async () => {
    if (!game || !roastDraft) return;
    setLoading(true);
    setError(null);
    try {
      const targetPlayer = game.current_turn === 1 ? 2 : 1;
      const res = await fetch(`${API_BASE}/api/game/${game.game_id}/review`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          game_id: game.game_id,
          roast: roastDraft,
          target_player_number: targetPlayer,
        }),
      });
      if (!res.ok) throw new Error(await res.text());
      await res.json();

      const stateRes = await fetch(`${API_BASE}/api/game/${game.game_id}`);
      if (!stateRes.ok) throw new Error(await stateRes.text());
      const state = await stateRes.json();
      setGame(state);
      setRoastDraft(null);
    } catch (e: any) {
      setError(e?.message || "Failed to review roast");
    } finally {
      setLoading(false);
    }
  };

  const renderHealthBar = (player: Player, color: string) => {
    const width = Math.max(0, Math.min(100, player.health));
    return (
      <div className="w-full rounded-md bg-zinc-200 dark:bg-zinc-800">
        <div
          className="h-3 rounded-md transition-all"
          style={{ width: `${width}%`, backgroundColor: color }}
        />
      </div>
    );
  };

  const renderSetup = () => (
    <div className="space-y-6">
      <header className="space-y-2">
        <p className="text-sm text-zinc-500 dark:text-zinc-400">
          Enter player names and optional LinkedIn URLs to begin.
        </p>
      </header>

      <div className="grid gap-4 md:grid-cols-2">
        {[player1, player2].map((player, idx) => {
          const setPlayer = idx === 0 ? setPlayer1 : setPlayer2;
          return (
            <div
              key={idx}
              className="rounded-xl border border-zinc-200 bg-white p-4 shadow-sm dark:border-zinc-800 dark:bg-zinc-950"
            >
              <h3 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">
                Player {idx + 1}
              </h3>
              <div className="mt-3 space-y-3">
                <div className="space-y-1">
                  <label className="text-xs text-zinc-500">Name *</label>
                  <input
                    value={player.name}
                    onChange={(e) => setPlayer({ ...player, name: e.target.value })}
                    className="w-full rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm text-zinc-900 shadow-inner focus:border-zinc-400 focus:outline-none dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-50"
                    placeholder="Alex Recruiter"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-xs text-zinc-500">LinkedIn URL (optional)</label>
                  <input
                    value={player.bio ?? ""}
                    onChange={(e) => setPlayer({ ...player, bio: e.target.value })}
                    className="w-full rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm text-zinc-900 shadow-inner focus:border-zinc-400 focus:outline-none dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-50"
                    placeholder="https://www.linkedin.com/in/username"
                  />
                </div>
              </div>
            </div>
          );
        })}
      </div>

      <button
        onClick={startGame}
        disabled={loading || !player1.name || !player2.name}
        className="w-full rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {loading ? "Starting..." : "Start Battle"}
      </button>
      {error && <p className="text-sm text-red-600">{error}</p>}
    </div>
  );

  const renderBattle = () => {
    if (!game) return null;
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs uppercase tracking-wide text-indigo-600">
              Round {game.round_number}
            </p>
            <h2 className="text-xl font-semibold text-zinc-900 dark:text-zinc-50">
              Streetfighter Mode
            </h2>
          </div>
          <button onClick={reset} className="text-sm text-zinc-500 underline hover:text-zinc-700">
            Restart
          </button>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          {[game.player1, game.player2].map((p, idx) => (
            <div
              key={idx}
              className={`rounded-xl border p-4 shadow-sm ${
                game.current_turn === idx + 1
                  ? "border-indigo-300 ring-2 ring-indigo-100 dark:ring-indigo-900/40"
                  : "border-zinc-200 dark:border-zinc-800"
              }`}
            >
              <div className="flex items-center gap-3">
                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-gradient-to-br from-indigo-500 to-purple-500 text-lg font-bold text-white">
                  {p.name?.[0]?.toUpperCase() ?? "?"}
                </div>
                <div>
                  <p className="text-sm font-semibold text-zinc-900 dark:text-zinc-50">
                    {p.name || `Player ${idx + 1}`}
                  </p>
                  <p className="text-xs text-zinc-500">HP: {p.health}</p>
                </div>
              </div>
              <div className="mt-3">{renderHealthBar(p, idx === 0 ? "#22c55e" : "#ef4444")}</div>
              {p.profile.bio && (
                <p className="mt-2 truncate text-xs text-zinc-500">{p.profile.bio}</p>
              )}
            </div>
          ))}
        </div>

        <div className="rounded-xl border border-zinc-200 bg-white p-4 shadow-sm dark:border-zinc-800 dark:bg-zinc-950">
          <p className="text-sm text-zinc-500">
            Current Turn:{" "}
            <span className="font-semibold text-zinc-900 dark:text-zinc-50">
              Player {game.current_turn} ({currentPlayer?.name || "Unknown"})
            </span>
          </p>
          <div className="mt-3 flex flex-col gap-2 sm:flex-row">
            <button
              onClick={generateRoast}
              disabled={loading}
              className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow hover:bg-indigo-500 disabled:opacity-60"
            >
              {loading ? "Working..." : "Generate Roast"}
            </button>
            <button
              onClick={reviewRoast}
              disabled={loading || !roastDraft}
              className="rounded-lg bg-amber-500 px-4 py-2 text-sm font-semibold text-white shadow hover:bg-amber-400 disabled:opacity-60"
            >
              {loading ? "Scoring..." : "Review & Deal Damage"}
            </button>
          </div>
          {roastDraft && (
            <div className="mt-4 rounded-lg border border-zinc-200 bg-zinc-50 p-3 text-sm text-zinc-800 dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-100">
              <p className="text-xs font-semibold uppercase text-zinc-500">
                Draft Roast (Player {game.current_turn} → Player{" "}
                {game.current_turn === 1 ? 2 : 1})
              </p>
              <p className="mt-2 leading-relaxed">{roastDraft}</p>
            </div>
          )}
          {game.last_roast && (
            <div className="mt-4 rounded-lg border border-indigo-100 bg-indigo-50 p-3 text-sm text-indigo-900 dark:border-indigo-900/50 dark:bg-indigo-950/30 dark:text-indigo-50">
              <p className="text-xs font-semibold uppercase text-indigo-600">
                Last Applied Roast {game.last_damage ? `(Damage: ${game.last_damage})` : ""}
              </p>
              <p className="mt-2 leading-relaxed">{game.last_roast}</p>
            </div>
          )}
          {error && <p className="mt-3 text-sm text-red-600">{error}</p>}
        </div>
      </div>
    );
  };

  const renderEnd = () => {
    if (!game) return null;
    const winner = game.winner === 1 ? game.player1 : game.player2;
    const loser = game.winner === 1 ? game.player2 : game.player1;
    return (
      <div className="space-y-6">
        <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-6 text-center shadow-sm dark:border-emerald-900/40 dark:bg-emerald-950/30">
          <p className="text-xs uppercase tracking-wide text-emerald-600">Winner</p>
          <h2 className="mt-2 text-2xl font-semibold text-emerald-900 dark:text-emerald-50">
            {winner?.name || "Player"} takes the crown!
          </h2>
          <p className="mt-2 text-sm text-emerald-800 dark:text-emerald-100">
            Final HP: {winner?.health ?? "—"}
          </p>
          {game.last_roast && (
            <p className="mt-3 text-sm text-emerald-900 dark:text-emerald-50">
              Finishing Roast: {game.last_roast}
            </p>
          )}
        </div>
        <div className="grid gap-4 md:grid-cols-2">
          {[winner, loser].map((p, idx) => (
            <div
              key={idx}
              className="rounded-xl border border-zinc-200 bg-white p-4 shadow-sm dark:border-zinc-800 dark:bg-zinc-950"
            >
              <p className="text-xs uppercase text-zinc-500">
                {idx === 0 ? "Champion" : "Defeated"}
              </p>
              <h3 className="text-lg font-semibold text-zinc-900 dark:text-zinc-50">{p?.name}</h3>
              <p className="text-xs text-zinc-500">Final HP: {p?.health}</p>
            </div>
          ))}
        </div>
        <button
          onClick={reset}
          className="w-full rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow hover:bg-indigo-500"
        >
          Play Again
        </button>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-zinc-50 to-white px-4 py-10 font-sans text-zinc-900 dark:from-black dark:to-zinc-950 dark:text-zinc-50">
      <div className="mx-auto max-w-5xl space-y-8">
        <header className="space-y-2 text-center">
          <p className="text-xs uppercase tracking-[0.2em] text-indigo-600">LinkedIn Roast Battle</p>
          <h1 className="text-3xl font-bold leading-tight sm:text-4xl">
            Roast, Review, and Battle to Zero HP
          </h1>
          <p className="text-sm text-zinc-500">
            Setup screen → Streetfighter battle view → Winner screen, aligned with the project plan.
          </p>
        </header>

        <main className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-xl dark:border-zinc-800 dark:bg-zinc-950">
          {status === "setup" && renderSetup()}
          {status === "in_progress" && renderBattle()}
          {status === "finished" && renderEnd()}
        </main>
      </div>
    </div>
  );
}
