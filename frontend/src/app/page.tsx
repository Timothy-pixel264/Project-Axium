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
  video_path?: string | null; // Path to scraping video recording
  scraping_errors?: any[] | null; // Errors from scraping process
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

type ScrapedProfiles = {
  player1: LinkedInProfile;
  player2: LinkedInProfile;
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
  const [scrapedProfiles, setScrapedProfiles] = useState<ScrapedProfiles | null>(null);
  const [showPreview, setShowPreview] = useState(false);
  const [activeProfileTab, setActiveProfileTab] = useState<1 | 2 | null>(null);
  const [scrapedWebUrl, setScrapedWebUrl] = useState<string>("");
  const [webScrapingResult, setWebScrapingResult] = useState<any>(null);
  const [webScrapingError, setWebScrapingError] = useState<string | null>(null);

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
    setScrapedProfiles(null);
    setShowPreview(false);
    setActiveProfileTab(null);
    setScrapedWebUrl("");
    setWebScrapingResult(null);
    setWebScrapingError(null);
  };

  const fetchProfilePreviews = async () => {
    setLoading(true);
    setError(null);
    try {
      const payload = {
        player1_profile: {
          name: player1.name,
          bio: player1.bio || undefined,
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
      if (!res.ok) {
        const errorText = await res.text();
        let errorMessage = "Failed to fetch profiles";
        try {
          const errorJson = JSON.parse(errorText);
          errorMessage = errorJson.detail || errorText;
        } catch {
          errorMessage = errorText;
        }
        setError(errorMessage);
        setLoading(false);
        return;
      }
      const data = await res.json();

      // Store the scraped profiles and show preview
      setScrapedProfiles({
        player1: data.game_state.player1.profile,
        player2: data.game_state.player2.profile,
      });
      setGame(data.game_state);
      setShowPreview(true);
    } catch (e: any) {
      setError(e?.message || "Failed to fetch profiles");
    } finally {
      setLoading(false);
    }
  };

  const startGame = () => {
    setShowPreview(false);
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

      // Fetch updated game state to show damage and advance turn
      const stateRes = await fetch(`${API_BASE}/api/game/${game.game_id}`);
      if (!stateRes.ok) throw new Error(await stateRes.text());
      const state = await stateRes.json();
      setGame(state);
      setRoastDraft(null);
    } catch (e: any) {
      setError(e?.message || "Failed to generate roast");
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

  const renderWebScraperPanel = () => {
    const isValidUrl = (url: string) => {
      const urlPattern = /^https?:\/\/.+\..+/;
      return urlPattern.test(url);
    };

    const handleScrape = async () => {
      if (!scrapedWebUrl) {
        setWebScrapingError("Please enter a URL");
        return;
      }
      if (!isValidUrl(scrapedWebUrl)) {
        setWebScrapingError("Invalid URL format. Please enter a valid URL starting with http:// or https://");
        return;
      }

      setWebScrapingError(null);
      setWebScrapingResult(null);
      setLoading(true);

      try {
        const res = await fetch(`${API_BASE}/api/scrape`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ url: scrapedWebUrl }),
        });

        if (!res.ok) {
          const errorText = await res.text();
          let errorMessage = "Failed to scrape webpage";
          try {
            const errorJson = JSON.parse(errorText);
            errorMessage = errorJson.detail || errorText;
          } catch {
            errorMessage = errorText;
          }
          setWebScrapingError(errorMessage);
          setLoading(false);
          return;
        }

        const data = await res.json();
        setWebScrapingResult(data);
      } catch (e: any) {
        setWebScrapingError(e?.message || "Failed to scrape webpage");
      } finally {
        setLoading(false);
      }
    };

    return (
      <div className="fixed right-0 top-0 h-screen w-full max-w-md overflow-y-auto border-l border-zinc-200 bg-white p-6 shadow-lg dark:border-zinc-800 dark:bg-zinc-950">
        <div className="mb-6 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">
            LinkedIn Profile Scraper
          </h2>
          <button
            onClick={() => {
              setScrapedWebUrl("");
              setWebScrapingResult(null);
              setWebScrapingError(null);
            }}
            className="text-zinc-600 hover:text-zinc-800 dark:text-zinc-400 dark:hover:text-zinc-200"
          >
            <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
              <path d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z" />
            </svg>
          </button>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">
              Enter LinkedIn Profile URL
            </label>
            <input
              type="text"
              value={scrapedWebUrl}
              onChange={(e) => {
                setScrapedWebUrl(e.target.value);
                setWebScrapingError(null);
              }}
              placeholder="https://www.linkedin.com/in/username"
              className="w-full rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm text-zinc-900 shadow-inner focus:border-zinc-400 focus:outline-none dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-50"
            />
            {webScrapingError && (
              <p className="mt-2 text-sm text-red-600 dark:text-red-400">{webScrapingError}</p>
            )}
          </div>

          <button
            onClick={handleScrape}
            disabled={loading || !scrapedWebUrl}
            className="w-full rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow hover:bg-indigo-500 disabled:opacity-60 disabled:cursor-not-allowed"
          >
            {loading ? "Scraping..." : "Scrape Page"}
          </button>

          {webScrapingResult && (
            <div className="space-y-4 border-t border-zinc-200 pt-4 dark:border-zinc-800">
              {webScrapingResult.video_path && (
                <div>
                  <h3 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100 mb-2">
                    Scraping Recording
                  </h3>
                  <div className="rounded-lg overflow-hidden bg-black">
                    <video
                      controls
                      className="w-full"
                      style={{ maxHeight: "200px" }}
                    >
                      <source src={webScrapingResult.video_path} type="video/webm" />
                      Your browser does not support the video tag.
                    </video>
                  </div>
                </div>
              )}

              {webScrapingResult.title && (
                <div>
                  <h3 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">Headline</h3>
                  <p className="mt-1 text-xs text-zinc-600 dark:text-zinc-400">{webScrapingResult.title}</p>
                </div>
              )}

              {webScrapingResult.content?.bio && Array.isArray(webScrapingResult.content.bio) && webScrapingResult.content.bio.length > 0 && (
                <div>
                  <h3 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">Bio</h3>
                  <p className="mt-1 text-xs text-zinc-600 dark:text-zinc-400">
                    {webScrapingResult.content.bio[0]?.substring(0, 150)}...
                  </p>
                </div>
              )}

              {webScrapingResult.content?.experience && Array.isArray(webScrapingResult.content.experience) && webScrapingResult.content.experience.length > 0 && (
                <div>
                  <h3 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">
                    Experience ({webScrapingResult.content.experience.length})
                  </h3>
                  <ul className="mt-2 space-y-1">
                    {webScrapingResult.content.experience.slice(0, 3).map((exp: string, idx: number) => (
                      <li key={idx} className="text-xs text-zinc-600 dark:text-zinc-400">
                        • {exp.substring(0, 80)}
                      </li>
                    ))}
                    {webScrapingResult.content.experience.length > 3 && (
                      <li className="text-xs text-zinc-500">... and {webScrapingResult.content.experience.length - 3} more</li>
                    )}
                  </ul>
                </div>
              )}

              {webScrapingResult.content?.education && Array.isArray(webScrapingResult.content.education) && webScrapingResult.content.education.length > 0 && (
                <div>
                  <h3 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">
                    Education ({webScrapingResult.content.education.length})
                  </h3>
                  <ul className="mt-2 space-y-1">
                    {webScrapingResult.content.education.slice(0, 3).map((edu: string, idx: number) => (
                      <li key={idx} className="text-xs text-zinc-600 dark:text-zinc-400">
                        • {edu.substring(0, 80)}
                      </li>
                    ))}
                    {webScrapingResult.content.education.length > 3 && (
                      <li className="text-xs text-zinc-500">... and {webScrapingResult.content.education.length - 3} more</li>
                    )}
                  </ul>
                </div>
              )}

              {webScrapingResult.content?.skills && Array.isArray(webScrapingResult.content.skills) && webScrapingResult.content.skills.length > 0 && (
                <div>
                  <h3 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">
                    Skills ({webScrapingResult.content.skills.length})
                  </h3>
                  <ul className="mt-2 space-y-1">
                    {webScrapingResult.content.skills.slice(0, 5).map((skill: string, idx: number) => (
                      <li key={idx} className="text-xs text-zinc-600 dark:text-zinc-400">
                        • {skill.substring(0, 50)}
                      </li>
                    ))}
                    {webScrapingResult.content.skills.length > 5 && (
                      <li className="text-xs text-zinc-500">... and {webScrapingResult.content.skills.length - 5} more</li>
                    )}
                  </ul>
                </div>
              )}

              {webScrapingResult.content?.headings && Array.isArray(webScrapingResult.content.headings) && webScrapingResult.content.headings.length > 0 && (
                <div>
                  <h3 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">
                    Headings ({webScrapingResult.content.headings.length})
                  </h3>
                  <ul className="mt-2 space-y-1">
                    {webScrapingResult.content.headings.slice(0, 5).map((heading: string, idx: number) => (
                      <li key={idx} className="text-xs text-zinc-600 dark:text-zinc-400">
                        • {heading.substring(0, 80)}
                      </li>
                    ))}
                    {webScrapingResult.content.headings.length > 5 && (
                      <li className="text-xs text-zinc-500">... and {webScrapingResult.content.headings.length - 5} more</li>
                    )}
                  </ul>
                </div>
              )}

              {webScrapingResult.content?.paragraphs && Array.isArray(webScrapingResult.content.paragraphs) && webScrapingResult.content.paragraphs.length > 0 && (
                <div>
                  <h3 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">
                    Paragraphs ({webScrapingResult.content.paragraphs.length})
                  </h3>
                  <p className="mt-1 text-xs text-zinc-600 dark:text-zinc-400">
                    {webScrapingResult.content.paragraphs[0].substring(0, 150)}...
                  </p>
                </div>
              )}

              {webScrapingResult.content?.links && Array.isArray(webScrapingResult.content.links) && webScrapingResult.content.links.length > 0 && (
                <div>
                  <h3 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">
                    Links ({webScrapingResult.content.links.length})
                  </h3>
                  <ul className="mt-2 space-y-1">
                    {webScrapingResult.content.links.slice(0, 3).map((link: any, idx: number) => (
                      <li key={idx} className="text-xs">
                        <a
                          href={link.href}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-indigo-600 hover:text-indigo-500 dark:text-indigo-400 dark:hover:text-indigo-300 truncate"
                        >
                          {link.text}
                        </a>
                      </li>
                    ))}
                    {webScrapingResult.content.links.length > 3 && (
                      <li className="text-xs text-zinc-500">... and {webScrapingResult.content.links.length - 3} more</li>
                    )}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    );
  };

  const renderProfileCardContent = (profile: LinkedInProfile, playerName: string) => (
    <div className="space-y-4">
      {/* Video or placeholder */}
      <div>
        <h4 className="text-xs font-semibold uppercase tracking-wide text-zinc-500 mb-2">Scraping Recording</h4>
        {profile.video_path ? (
          <div className="rounded-lg overflow-hidden bg-black">
            <video
              controls
              className="w-full"
              style={{ maxHeight: "300px" }}
            >
              <source src={profile.video_path} type="video/webm" />
              Your browser does not support the video tag.
            </video>
          </div>
        ) : (
          <div className="rounded-lg bg-black h-48 flex items-center justify-center">
            <div className="text-center">
              <svg className="w-12 h-12 text-zinc-600 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <p className="text-xs text-zinc-500">Video unavailable</p>
            </div>
          </div>
        )}
      </div>

      {profile.headline && (
        <div>
          <h4 className="text-xs font-semibold uppercase tracking-wide text-zinc-500">Headline</h4>
          <p className="mt-1 text-sm text-zinc-900 dark:text-zinc-50">{profile.headline}</p>
        </div>
      )}

      {profile.bio && !profile.bio.startsWith("http") && (
        <div>
          <h4 className="text-xs font-semibold uppercase tracking-wide text-zinc-500">Bio</h4>
          <p className="mt-1 text-sm text-zinc-900 dark:text-zinc-50">{profile.bio}</p>
        </div>
      )}

      {profile.experience && profile.experience.length > 0 && (
        <div>
          <h4 className="text-xs font-semibold uppercase tracking-wide text-zinc-500">
            Experience ({profile.experience.length} {profile.experience.length === 1 ? 'entry' : 'entries'})
          </h4>
          <ul className="mt-2 space-y-2">
            {profile.experience.map((exp, idx) => (
              <li key={idx} className="text-sm text-zinc-700 dark:text-zinc-300">
                <span className="text-indigo-600 dark:text-indigo-400">•</span> {exp}
              </li>
            ))}
          </ul>
        </div>
      )}

      {profile.education && profile.education.length > 0 && (
        <div>
          <h4 className="text-xs font-semibold uppercase tracking-wide text-zinc-500">
            Education ({profile.education.length} {profile.education.length === 1 ? 'entry' : 'entries'})
          </h4>
          <ul className="mt-2 space-y-2">
            {profile.education.map((edu, idx) => (
              <li key={idx} className="text-sm text-zinc-700 dark:text-zinc-300">
                <span className="text-purple-600 dark:text-purple-400">•</span> {edu}
              </li>
            ))}
          </ul>
        </div>
      )}

      {profile.skills && profile.skills.length > 0 && (
        <div>
          <h4 className="text-xs font-semibold uppercase tracking-wide text-zinc-500">
            Skills ({profile.skills.length})
          </h4>
          <div className="mt-2 flex flex-wrap gap-2">
            {profile.skills.map((skill, idx) => (
              <span
                key={idx}
                className="rounded-full bg-indigo-100 px-3 py-1 text-xs font-medium text-indigo-800 dark:bg-indigo-900/30 dark:text-indigo-200"
              >
                {skill}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );

  const renderSetup = () => (
    <div className="space-y-6">
      <header className="space-y-2">
        <p className="text-sm text-zinc-500 dark:text-zinc-400">
          Enter player names and optional LinkedIn or Wikipedia URLs to begin.
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
                  <label className="text-xs text-zinc-500">LinkedIn or Wikipedia URL (optional)</label>
                  <input
                    value={player.bio ?? ""}
                    onChange={(e) => setPlayer({ ...player, bio: e.target.value })}
                    className="w-full rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm text-zinc-900 shadow-inner focus:border-zinc-400 focus:outline-none dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-50"
                    placeholder="https://www.linkedin.com/in/username or https://en.wikipedia.org/wiki/Topic"
                  />
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 dark:border-red-900/50 dark:bg-red-950/30">
          <div className="flex items-start gap-3">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-600 dark:text-red-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.28 7.22a.75.75 0 00-1.06 1.06L8.94 10l-1.72 1.72a.75.75 0 101.06 1.06L10 11.06l1.72 1.72a.75.75 0 101.06-1.06L11.06 10l1.72-1.72a.75.75 0 00-1.06-1.06L10 8.94 8.28 7.22z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="flex-1">
              <h3 className="text-sm font-semibold text-red-800 dark:text-red-200">Error</h3>
              <p className="mt-1 text-sm text-red-700 dark:text-red-300">{error}</p>
            </div>
            <button
              onClick={() => setError(null)}
              className="flex-shrink-0 text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-200"
            >
              <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                <path d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z" />
              </svg>
            </button>
          </div>
        </div>
      )}

      <button
        onClick={fetchProfilePreviews}
        disabled={loading || !player1.name || !player2.name}
        className="w-full rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {loading ? "Loading Profiles..." : "Preview Profiles & Start"}
      </button>
    </div>
  );

  const renderProfilePreview = () => {
    if (!scrapedProfiles || !game) return null;

    const renderProfileCard = (profile: LinkedInProfile, playerName: string, playerNum: number) => (
      <div className="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm dark:border-zinc-800 dark:bg-zinc-950">
        <div className="flex items-center gap-3 border-b border-zinc-200 pb-4 dark:border-zinc-800">
          <div className="flex h-14 w-14 items-center justify-center rounded-full bg-gradient-to-br from-indigo-500 to-purple-500 text-xl font-bold text-white">
            {playerName?.[0]?.toUpperCase() ?? "?"}
          </div>
          <div>
            <h3 className="text-lg font-semibold text-zinc-900 dark:text-zinc-50">{playerName}</h3>
            <p className="text-xs text-zinc-500">Player {playerNum}</p>
          </div>
        </div>

        <div className="mt-4 space-y-4">
          {profile.headline && (
            <div>
              <h4 className="text-xs font-semibold uppercase tracking-wide text-zinc-500">Headline</h4>
              <p className="mt-1 text-sm text-zinc-900 dark:text-zinc-50">{profile.headline}</p>
            </div>
          )}

          {profile.bio && !profile.bio.startsWith("http") && (
            <div>
              <h4 className="text-xs font-semibold uppercase tracking-wide text-zinc-500">Bio</h4>
              <p className="mt-1 text-sm text-zinc-900 dark:text-zinc-50">{profile.bio}</p>
            </div>
          )}

          {profile.experience && profile.experience.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold uppercase tracking-wide text-zinc-500">
                Experience ({profile.experience.length} {profile.experience.length === 1 ? 'entry' : 'entries'})
              </h4>
              <ul className="mt-2 space-y-2">
                {profile.experience.slice(0, 3).map((exp, idx) => (
                  <li key={idx} className="text-sm text-zinc-700 dark:text-zinc-300">
                    <span className="text-indigo-600 dark:text-indigo-400">•</span> {exp}
                  </li>
                ))}
                {profile.experience.length > 3 && (
                  <li className="text-xs italic text-zinc-500">
                    ... and {profile.experience.length - 3} more
                  </li>
                )}
              </ul>
            </div>
          )}

          {profile.education && profile.education.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold uppercase tracking-wide text-zinc-500">
                Education ({profile.education.length} {profile.education.length === 1 ? 'entry' : 'entries'})
              </h4>
              <ul className="mt-2 space-y-2">
                {profile.education.slice(0, 2).map((edu, idx) => (
                  <li key={idx} className="text-sm text-zinc-700 dark:text-zinc-300">
                    <span className="text-purple-600 dark:text-purple-400">•</span> {edu}
                  </li>
                ))}
                {profile.education.length > 2 && (
                  <li className="text-xs italic text-zinc-500">
                    ... and {profile.education.length - 2} more
                  </li>
                )}
              </ul>
            </div>
          )}

          {profile.skills && profile.skills.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold uppercase tracking-wide text-zinc-500">
                Skills ({profile.skills.length})
              </h4>
              <div className="mt-2 flex flex-wrap gap-2">
                {profile.skills.slice(0, 6).map((skill, idx) => (
                  <span
                    key={idx}
                    className="rounded-full bg-indigo-100 px-3 py-1 text-xs font-medium text-indigo-800 dark:bg-indigo-900/30 dark:text-indigo-200"
                  >
                    {skill}
                  </span>
                ))}
                {profile.skills.length > 6 && (
                  <span className="rounded-full bg-zinc-100 px-3 py-1 text-xs font-medium text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400">
                    +{profile.skills.length - 6} more
                  </span>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    );

    return (
      <div className="space-y-6">
        <header className="space-y-2">
          <p className="text-xs uppercase tracking-wide text-indigo-600">Profile Preview</p>
          <h2 className="text-xl font-semibold text-zinc-900 dark:text-zinc-50">
            Review Scraped LinkedIn Data
          </h2>
          <p className="text-sm text-zinc-500 dark:text-zinc-400">
            Here's what we found from the LinkedIn profiles. Ready to battle?
          </p>
        </header>

        <div className="grid gap-4 md:grid-cols-2">
          {renderProfileCard(scrapedProfiles.player1, game.player1.name, 1)}
          {renderProfileCard(scrapedProfiles.player2, game.player2.name, 2)}
        </div>

        <div className="flex flex-col gap-3 sm:flex-row">
          <button
            onClick={startGame}
            className="flex-1 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow hover:bg-indigo-500"
          >
            Start Battle
          </button>
          <button
            onClick={reset}
            className="rounded-lg border border-zinc-300 bg-white px-4 py-2 text-sm font-semibold text-zinc-700 shadow-sm hover:bg-zinc-50 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-300 dark:hover:bg-zinc-800"
          >
            Start Over
          </button>
        </div>
      </div>
    );
  };

  const renderBattle = () => {
    if (!game || !scrapedProfiles) return null;
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

        {/* Tab Navigation for Profile Data */}
        <div className="flex gap-2 border-b border-zinc-200 dark:border-zinc-800">
          {([1, 2] as const).map((playerNum) => {
            const player = playerNum === 1 ? game.player1 : game.player2;
            return (
              <button
                key={playerNum}
                onClick={() => setActiveProfileTab(activeProfileTab === playerNum ? null : (playerNum as 1 | 2))}
                className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                  activeProfileTab === playerNum
                    ? "border-indigo-600 text-indigo-600 dark:text-indigo-400"
                    : "border-transparent text-zinc-600 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-200"
                }`}
              >
                {player.name}'s Profile
              </button>
            );
          })}
        </div>

        {/* Profile Data Panel */}
        {activeProfileTab && (
          <div className="rounded-lg border border-zinc-200 bg-zinc-50 p-4 dark:border-zinc-800 dark:bg-zinc-900/50">
            <div className="max-h-96 overflow-y-auto">
              {renderProfileCardContent(
                activeProfileTab === 1 ? scrapedProfiles.player1 : scrapedProfiles.player2,
                activeProfileTab === 1 ? game.player1.name : game.player2.name
              )}
            </div>
          </div>
        )}

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
              className="flex-1 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow hover:bg-indigo-500 disabled:opacity-60"
            >
              {loading ? "Generating & Judging..." : "Roast & Judge"}
            </button>
          </div>
          {game.last_roast && (
            <div className="mt-4 rounded-lg border border-indigo-100 bg-indigo-50 p-3 text-sm text-indigo-900 dark:border-indigo-900/50 dark:bg-indigo-950/30 dark:text-indigo-50">
              <p className="text-xs font-semibold uppercase text-indigo-600">
                Last Roast {game.last_damage ? `(Damage: ${game.last_damage})` : ""}
              </p>
              <p className="mt-2 leading-relaxed">{game.last_roast}</p>
            </div>
          )}
          {error && (
            <div className="mt-4 rounded-lg border border-red-200 bg-red-50 p-3 dark:border-red-900/50 dark:bg-red-950/30">
              <div className="flex items-start gap-3">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-red-600 dark:text-red-400" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.28 7.22a.75.75 0 00-1.06 1.06L8.94 10l-1.72 1.72a.75.75 0 101.06 1.06L10 11.06l1.72 1.72a.75.75 0 101.06-1.06L11.06 10l1.72-1.72a.75.75 0 00-1.06-1.06L10 8.94 8.28 7.22z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="flex-1">
                  <h3 className="text-sm font-semibold text-red-800 dark:text-red-200">Error</h3>
                  <p className="mt-1 text-sm text-red-700 dark:text-red-300">{error}</p>
                </div>
                <button
                  onClick={() => setError(null)}
                  className="flex-shrink-0 text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-200"
                >
                  <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                    <path d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z" />
                  </svg>
                </button>
              </div>
            </div>
          )}
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
          {status === "setup" && !showPreview && renderSetup()}
          {status === "setup" && showPreview && renderProfilePreview()}
          {status === "in_progress" && renderBattle()}
          {status === "finished" && renderEnd()}
        </main>
      </div>
    </div>
  );
}
