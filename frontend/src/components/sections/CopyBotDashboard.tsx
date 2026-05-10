import { useEffect, useRef, useState } from "react";

// ── Types ─────────────────────────────────────────────────────────────────────

type BotStatus = {
  status: string;
  mode: string;
  strategies: { copy: boolean; signal: boolean; ai: boolean };
};

type CopyConfig = {
  trade_ratio: number;
  min_trade_usdt: number;
  max_trade_usdt: number;
  auto_approve: boolean;
};

type CopyLeader = {
  id: number;
  external_id: string;
  label: string;
  allocation_pct: number;
  is_active: boolean;
  total_pnl: number;
  num_trades: number;
  last_polled: string | null;
};

type PendingTrade = {
  id: string;
  leader_id: string;
  label: string;
  symbol: string;
  side: string;
  amount: number;
  price: number;
  value: number;
  detected_at: string;
};

type CopyTrade = {
  id: number;
  symbol: string;
  side: string;
  amount: number;
  price: number | null;
  cost: number | null;
  pnl: number | null;
  status: string;
  leader_id: string | null;
  created_at: string | null;
  closed_at: string | null;
};

type CopyStats = {
  period_days: number;
  num_trades: number;
  closed_trades: number;
  wins: number;
  win_rate_pct: number;
  total_pnl: number;
  total_volume_usdt: number;
};

type Position = {
  id: number;
  symbol: string;
  side: string;
  entry_price: number;
  current_price: number | null;
  amount: number;
  unrealized_pnl: number;
  unrealized_pnl_pct: number;
  strategy: string;
};

// ── API helpers ───────────────────────────────────────────────────────────────

const API = "/api";

async function apiFetch<T>(path: string, opts?: RequestInit): Promise<T> {
  const res = await fetch(`${API}${path}`, opts);
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json() as Promise<T>;
}

// ── Utility ───────────────────────────────────────────────────────────────────

function pnlColor(val: number) {
  if (val > 0) return "text-emerald-400";
  if (val < 0) return "text-red-400";
  return "text-gray-400";
}

function fmt(n: number | null | undefined, decimals = 2) {
  if (n == null) return "—";
  return n.toLocaleString("en-US", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

// ── Main component ────────────────────────────────────────────────────────────

export default function CopyBotDashboard() {
  const [botStatus, setBotStatus] = useState<BotStatus | null>(null);
  const [configDraft, setConfigDraft] = useState<CopyConfig | null>(null);
  const [leaders, setLeaders] = useState<CopyLeader[]>([]);
  const [pending, setPending] = useState<PendingTrade[]>([]);
  const [history, setHistory] = useState<CopyTrade[]>([]);
  const [stats, setStats] = useState<CopyStats | null>(null);
  const [positions, setPositions] = useState<Position[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const configInitialized = useRef(false);

  // Poll every 5 seconds — fetch logic lives inside the effect to avoid
  // triggering the react-hooks/set-state-in-effect lint rule.
  useEffect(() => {
    const fetchAll = async () => {
      try {
        const [status, cfg, ldrs, pend, hist, sts, pos] = await Promise.all([
          apiFetch<BotStatus>("/bot/status"),
          apiFetch<CopyConfig>("/copy-trading/config"),
          apiFetch<CopyLeader[]>("/leaders"),
          apiFetch<PendingTrade[]>("/copy-trading/pending"),
          apiFetch<CopyTrade[]>("/copy-trading/history?limit=20"),
          apiFetch<CopyStats>("/copy-trading/stats"),
          apiFetch<Position[]>("/portfolio/positions"),
        ]);
        setBotStatus(status);
        // Only initialize configDraft on first load; subsequent polls don't
        // overwrite edits the user may be in the middle of making.
        if (!configInitialized.current) {
          setConfigDraft(cfg);
          configInitialized.current = true;
        }
        setLeaders(ldrs);
        setPending(pend);
        setHistory(hist);
        setStats(sts);
        setPositions(pos.filter((p) => p.strategy === "copy"));
        setError(null);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to load data");
      }
    };

    void fetchAll();
    const id = setInterval(() => {
      void fetchAll();
    }, 5000);
    return () => clearInterval(id);
  }, []); // intentionally empty — fetchAll is fully self-contained

  const refresh = () => {
    // Trigger a one-shot re-poll by resetting and re-mounting would be complex;
    // instead we just let the 5-second interval handle it naturally.
  };

  const toggleBot = async () => {
    if (!botStatus) return;
    const action = botStatus.strategies.copy ? "stop" : "start";
    await apiFetch(`/strategies/copy/${action}`, { method: "POST" });
  };

  const saveConfig = async () => {
    if (!configDraft) return;
    setSaving(true);
    try {
      await apiFetch("/copy-trading/config", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(configDraft),
      });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Save failed");
    } finally {
      setSaving(false);
    }
  };

  const approvePending = async (id: string) => {
    await apiFetch(`/copy-trading/pending/${id}/approve`, { method: "POST" });
    setPending((prev) => prev.filter((t) => t.id !== id));
  };

  const rejectPending = async (id: string) => {
    await apiFetch(`/copy-trading/pending/${id}/reject`, { method: "POST" });
    setPending((prev) => prev.filter((t) => t.id !== id));
  };

  const closePosition = async (posId: number) => {
    await apiFetch(`/positions/${posId}/close`, { method: "POST" });
    setPositions((prev) => prev.filter((p) => p.id !== posId));
  };

  // Suppress lint warning — refresh is intentionally a no-op placeholder
  void refresh;

  const isActive = botStatus?.strategies.copy ?? false;

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <main className="mx-auto flex w-full max-w-5xl flex-col gap-6 px-4 py-10">
        {/* Header */}
        <header className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">Copy Trading Bot</h1>
            <p className="mt-1 text-sm text-gray-400">
              Mirroring trader{" "}
              <span className="font-mono text-emerald-400">
                cdc_74935e5e6b816909e70be3b4cd01
              </span>
            </p>
          </div>
          <button
            type="button"
            onClick={() => void toggleBot()}
            className={`rounded-md px-5 py-2 text-sm font-semibold transition-colors ${
              isActive
                ? "bg-red-600 hover:bg-red-500"
                : "bg-emerald-600 hover:bg-emerald-500"
            }`}
          >
            {isActive ? "⏸ Stop Bot" : "▶ Start Bot"}
          </button>
        </header>

        {error && (
          <div className="rounded-md border border-red-700 bg-red-950 px-4 py-3 text-sm text-red-300">
            {error}
          </div>
        )}

        {/* Status + Stats row */}
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          <StatCard
            label="Bot Status"
            value={isActive ? "ACTIVE" : "STOPPED"}
            valueClass={isActive ? "text-emerald-400" : "text-red-400"}
          />
          <StatCard
            label="Win Rate (7d)"
            value={stats ? `${stats.win_rate_pct}%` : "—"}
          />
          <StatCard
            label="Total PnL (7d)"
            value={stats ? `$${fmt(stats.total_pnl)}` : "—"}
            valueClass={stats ? pnlColor(stats.total_pnl) : undefined}
          />
          <StatCard
            label="Volume (7d)"
            value={stats ? `$${fmt(stats.total_volume_usdt, 0)}` : "—"}
          />
        </div>

        {/* Config panel */}
        {configDraft && (
          <section className="rounded-md border border-gray-800 bg-gray-900 p-5">
            <h2 className="mb-4 text-lg font-semibold">Configuration</h2>
            <div className="grid gap-5 sm:grid-cols-2">
              <div>
                <label className="mb-1 block text-sm text-gray-400">
                  Copy Ratio:{" "}
                  <span className="font-semibold text-white">
                    {Math.round(configDraft.trade_ratio * 100)}%
                  </span>
                </label>
                <input
                  type="range"
                  min={5}
                  max={100}
                  step={5}
                  value={Math.round(configDraft.trade_ratio * 100)}
                  onChange={(e) =>
                    setConfigDraft((prev) =>
                      prev
                        ? { ...prev, trade_ratio: Number(e.target.value) / 100 }
                        : prev,
                    )
                  }
                  className="w-full accent-emerald-500"
                />
                <div className="mt-1 flex justify-between text-xs text-gray-500">
                  <span>5%</span>
                  <span>100%</span>
                </div>
              </div>

              <div className="flex flex-col gap-3">
                <label className="flex items-center justify-between text-sm">
                  <span className="text-gray-400">Min Trade ($)</span>
                  <input
                    type="number"
                    min={0}
                    value={configDraft.min_trade_usdt}
                    onChange={(e) =>
                      setConfigDraft((prev) =>
                        prev
                          ? { ...prev, min_trade_usdt: Number(e.target.value) }
                          : prev,
                      )
                    }
                    className="w-28 rounded border border-gray-700 bg-gray-800 px-2 py-1 text-right text-sm"
                  />
                </label>
                <label className="flex items-center justify-between text-sm">
                  <span className="text-gray-400">Max Trade ($)</span>
                  <input
                    type="number"
                    min={0}
                    value={configDraft.max_trade_usdt}
                    onChange={(e) =>
                      setConfigDraft((prev) =>
                        prev
                          ? { ...prev, max_trade_usdt: Number(e.target.value) }
                          : prev,
                      )
                    }
                    className="w-28 rounded border border-gray-700 bg-gray-800 px-2 py-1 text-right text-sm"
                  />
                </label>
                <label className="flex items-center justify-between text-sm">
                  <span className="text-gray-400">Auto-Approve</span>
                  <button
                    type="button"
                    onClick={() =>
                      setConfigDraft((prev) =>
                        prev
                          ? { ...prev, auto_approve: !prev.auto_approve }
                          : prev,
                      )
                    }
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                      configDraft.auto_approve
                        ? "bg-emerald-600"
                        : "bg-gray-700"
                    }`}
                  >
                    <span
                      className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                        configDraft.auto_approve
                          ? "translate-x-6"
                          : "translate-x-1"
                      }`}
                    />
                  </button>
                </label>
              </div>
            </div>

            <button
              type="button"
              onClick={() => void saveConfig()}
              disabled={saving}
              className="mt-4 rounded-md bg-emerald-600 px-4 py-2 text-sm font-semibold hover:bg-emerald-500 disabled:opacity-50"
            >
              {saving ? "Saving…" : "Save Config"}
            </button>
          </section>
        )}

        {/* Pending approvals */}
        {pending.length > 0 && (
          <section className="rounded-md border border-yellow-700 bg-yellow-950/30 p-5">
            <h2 className="mb-3 text-lg font-semibold text-yellow-300">
              ⏳ Pending Approval ({pending.length})
            </h2>
            <ul className="space-y-2">
              {pending.map((t) => (
                <li
                  key={t.id}
                  className="flex items-center justify-between rounded border border-yellow-800 bg-gray-900 px-4 py-3"
                >
                  <div className="text-sm">
                    <span
                      className={
                        t.side === "buy"
                          ? "font-semibold text-emerald-400"
                          : "font-semibold text-red-400"
                      }
                    >
                      {t.side.toUpperCase()}
                    </span>{" "}
                    <span className="font-mono">{t.symbol}</span>
                    <span className="ml-2 text-gray-400">
                      {fmt(t.amount, 6)} @ ${fmt(t.price)} ≈ $
                      {fmt(t.value, 0)}
                    </span>
                    <span className="ml-2 text-xs text-gray-500">
                      {t.label}
                    </span>
                  </div>
                  <div className="flex gap-2">
                    <button
                      type="button"
                      onClick={() => void approvePending(t.id)}
                      className="rounded bg-emerald-700 px-3 py-1 text-xs font-semibold hover:bg-emerald-600"
                    >
                      Approve
                    </button>
                    <button
                      type="button"
                      onClick={() => void rejectPending(t.id)}
                      className="rounded bg-red-800 px-3 py-1 text-xs font-semibold hover:bg-red-700"
                    >
                      Reject
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          </section>
        )}

        {/* Open positions */}
        <section className="rounded-md border border-gray-800 bg-gray-900 p-5">
          <h2 className="mb-3 text-lg font-semibold">
            Open Positions ({positions.length})
          </h2>
          {positions.length === 0 ? (
            <p className="text-sm text-gray-500">No open copy positions.</p>
          ) : (
            <ul className="space-y-2">
              {positions.map((p) => (
                <li
                  key={p.id}
                  className="flex items-center justify-between rounded border border-gray-700 bg-gray-800 px-4 py-3"
                >
                  <div className="text-sm">
                    <span className="font-semibold">{p.symbol}</span>
                    <span className="ml-2 text-gray-400">
                      {p.side.toUpperCase()} {fmt(p.amount, 4)} @ $
                      {fmt(p.entry_price)}
                    </span>
                    <span className={`ml-3 font-semibold ${pnlColor(p.unrealized_pnl)}`}>
                      {p.unrealized_pnl >= 0 ? "+" : ""}${fmt(p.unrealized_pnl)}{" "}
                      ({p.unrealized_pnl_pct >= 0 ? "+" : ""}
                      {fmt(p.unrealized_pnl_pct)}%)
                    </span>
                  </div>
                  <button
                    type="button"
                    onClick={() => void closePosition(p.id)}
                    className="rounded border border-gray-600 px-3 py-1 text-xs hover:bg-gray-700"
                  >
                    Close
                  </button>
                </li>
              ))}
            </ul>
          )}
        </section>

        {/* Leaders */}
        <section className="rounded-md border border-gray-800 bg-gray-900 p-5">
          <h2 className="mb-3 text-lg font-semibold">
            Tracked Leaders ({leaders.length})
          </h2>
          {leaders.length === 0 ? (
            <p className="text-sm text-gray-500">No leaders configured.</p>
          ) : (
            <ul className="space-y-2">
              {leaders.map((l) => (
                <li
                  key={l.id}
                  className="flex items-center justify-between rounded border border-gray-700 bg-gray-800 px-4 py-3"
                >
                  <div className="text-sm">
                    <span
                      className={`mr-2 text-xs font-semibold ${l.is_active ? "text-emerald-400" : "text-gray-500"}`}
                    >
                      {l.is_active ? "● ACTIVE" : "○ OFF"}
                    </span>
                    <span className="font-mono text-gray-300">
                      {l.label || l.external_id}
                    </span>
                    <span className="ml-3 text-gray-500">
                      Alloc: {Math.round(l.allocation_pct * 100)}% · Trades:{" "}
                      {l.num_trades}
                    </span>
                  </div>
                  <span className={`text-sm font-semibold ${pnlColor(l.total_pnl)}`}>
                    {l.total_pnl >= 0 ? "+" : ""}${fmt(l.total_pnl)}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </section>

        {/* Trade history */}
        <section className="rounded-md border border-gray-800 bg-gray-900 p-5">
          <h2 className="mb-3 text-lg font-semibold">Recent Copy Trades</h2>
          {history.length === 0 ? (
            <p className="text-sm text-gray-500">No copy trades yet.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-700 text-left text-xs text-gray-500">
                    <th className="pb-2 pr-4">Symbol</th>
                    <th className="pb-2 pr-4">Side</th>
                    <th className="pb-2 pr-4">Amount</th>
                    <th className="pb-2 pr-4">Cost</th>
                    <th className="pb-2 pr-4">PnL</th>
                    <th className="pb-2 pr-4">Status</th>
                    <th className="pb-2">Date</th>
                  </tr>
                </thead>
                <tbody>
                  {history.map((t) => (
                    <tr
                      key={t.id}
                      className="border-b border-gray-800 last:border-0"
                    >
                      <td className="py-2 pr-4 font-mono">{t.symbol}</td>
                      <td
                        className={`py-2 pr-4 font-semibold ${
                          t.side === "buy"
                            ? "text-emerald-400"
                            : "text-red-400"
                        }`}
                      >
                        {t.side.toUpperCase()}
                      </td>
                      <td className="py-2 pr-4 text-gray-300">
                        {fmt(t.amount, 4)}
                      </td>
                      <td className="py-2 pr-4 text-gray-300">
                        {t.cost != null ? `$${fmt(t.cost, 0)}` : "—"}
                      </td>
                      <td
                        className={`py-2 pr-4 font-semibold ${t.pnl != null ? pnlColor(t.pnl) : "text-gray-500"}`}
                      >
                        {t.pnl != null
                          ? `${t.pnl >= 0 ? "+" : ""}$${fmt(t.pnl)}`
                          : "—"}
                      </td>
                      <td className="py-2 pr-4">
                        <span
                          className={`rounded px-1.5 py-0.5 text-xs ${
                            t.status === "filled"
                              ? "bg-emerald-900 text-emerald-300"
                              : t.status === "failed"
                                ? "bg-red-900 text-red-300"
                                : "bg-gray-700 text-gray-300"
                          }`}
                        >
                          {t.status}
                        </span>
                      </td>
                      <td className="py-2 text-xs text-gray-500">
                        {t.created_at
                          ? new Date(t.created_at).toLocaleDateString()
                          : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}

// ── Helper sub-components ─────────────────────────────────────────────────────

function StatCard({
  label,
  value,
  valueClass,
}: {
  label: string;
  value: string;
  valueClass?: string;
}) {
  return (
    <div className="rounded-md border border-gray-800 bg-gray-900 p-4">
      <p className="text-xs text-gray-500">{label}</p>
      <p className={`mt-1 text-xl font-bold ${valueClass ?? "text-white"}`}>
        {value}
      </p>
    </div>
  );
}

