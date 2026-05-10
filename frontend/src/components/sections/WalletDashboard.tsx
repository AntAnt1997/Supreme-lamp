import { useEffect, useState } from "react";

// ── Types ──────────────────────────────────────────────────────────────────────

type Chain = "ethereum" | "polygon" | "arbitrum" | "base" | "optimism" | "bsc";

type TrackedWallet = {
  id: number;
  address: string;
  label: string | null;
  chain: Chain;
  polymarket_volume: number | null;
  polymarket_win_rate: number | null;
  polymarket_pnl: number | null;
  last_synced_at: string | null;
  is_active: boolean;
  created_at: string | null;
};

type WalletToken = {
  id: number;
  wallet_id: number;
  token_symbol: string;
  token_name: string | null;
  token_address: string | null;
  balance: number;
  balance_usd: number | null;
  price_usd: number | null;
};

type WalletTransaction = {
  id: number;
  wallet_id: number;
  tx_hash: string;
  tx_type: string | null;
  from_address: string | null;
  to_address: string | null;
  asset: string | null;
  value: number | null;
  value_usd: number | null;
  status: string | null;
  timestamp: string | null;
};

type PortfolioSummary = {
  total_wallets: number;
  total_value_usd: number;
  chain_allocation: Record<string, number>;
  wallets: TrackedWallet[];
};

// ── API helpers ────────────────────────────────────────────────────────────────

const API = "/api";

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || res.statusText);
  }
  return res.json() as Promise<T>;
}

// ── Helpers ────────────────────────────────────────────────────────────────────

function fmt(n: number | null | undefined, decimals = 2): string {
  if (n == null) return "—";
  return n.toLocaleString("en-US", { maximumFractionDigits: decimals });
}

function fmtUsd(n: number | null | undefined): string {
  if (n == null) return "—";
  return "$" + fmt(n);
}

function shortAddr(addr: string): string {
  return addr.slice(0, 6) + "..." + addr.slice(-4);
}

const CHAIN_LABELS: Record<string, string> = {
  ethereum: "Ethereum",
  polygon: "Polygon",
  arbitrum: "Arbitrum",
  base: "Base",
  optimism: "Optimism",
  bsc: "BNB Chain",
};

const CHAIN_COLORS: Record<string, string> = {
  ethereum: "bg-blue-500/20 text-blue-300 border-blue-500/30",
  polygon: "bg-purple-500/20 text-purple-300 border-purple-500/30",
  arbitrum: "bg-sky-500/20 text-sky-300 border-sky-500/30",
  base: "bg-indigo-500/20 text-indigo-300 border-indigo-500/30",
  optimism: "bg-red-500/20 text-red-300 border-red-500/30",
  bsc: "bg-yellow-500/20 text-yellow-300 border-yellow-500/30",
};

// ── Sub-components ─────────────────────────────────────────────────────────────

function ChainBadge({ chain }: { chain: string }) {
  return (
    <span className={`text-xs px-2 py-0.5 rounded-full border ${CHAIN_COLORS[chain] ?? "bg-gray-700 text-gray-300 border-gray-600"}`}>
      {CHAIN_LABELS[chain] ?? chain}
    </span>
  );
}

function SyncStatus({ lastSynced }: { lastSynced: string | null }) {
  if (!lastSynced) return <span className="text-gray-500 text-xs">Never synced</span>;
  const d = new Date(lastSynced);
  const mins = Math.round((Date.now() - d.getTime()) / 60000);
  return (
    <span className="text-gray-400 text-xs">
      {mins < 60 ? `${mins}m ago` : `${Math.round(mins / 60)}h ago`}
    </span>
  );
}

// ── Add Wallet Modal ───────────────────────────────────────────────────────────

function AddWalletModal({ onClose, onAdded }: { onClose: () => void; onAdded: () => void }) {
  const [address, setAddress] = useState("");
  const [label, setLabel] = useState("");
  const [chain, setChain] = useState<Chain>("ethereum");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await apiFetch("/wallets", {
        method: "POST",
        body: JSON.stringify({ address, label: label || null, chain }),
      });
      onAdded();
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
      <div className="bg-gray-900 border border-gray-700 rounded-xl p-6 w-full max-w-md">
        <h2 className="text-lg font-semibold text-white mb-4">Add Wallet</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm text-gray-400 mb-1">Address *</label>
            <input
              className="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
              placeholder="0x..."
              value={address}
              onChange={(e) => setAddress(e.target.value)}
              required
            />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">Label</label>
            <input
              className="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
              placeholder="e.g. My ETH Wallet"
              value={label}
              onChange={(e) => setLabel(e.target.value)}
            />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">Chain</label>
            <select
              className="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
              value={chain}
              onChange={(e) => setChain(e.target.value as Chain)}
            >
              {Object.entries(CHAIN_LABELS).map(([id, name]) => (
                <option key={id} value={id}>{name}</option>
              ))}
            </select>
          </div>
          {error && <p className="text-red-400 text-sm">{error}</p>}
          <div className="flex gap-2 pt-2">
            <button
              type="submit"
              disabled={loading}
              className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded-lg py-2 text-sm font-medium transition-colors"
            >
              {loading ? "Adding…" : "Add Wallet"}
            </button>
            <button
              type="button"
              onClick={onClose}
              className="flex-1 bg-gray-700 hover:bg-gray-600 text-white rounded-lg py-2 text-sm font-medium transition-colors"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ── Wallet Detail Panel ────────────────────────────────────────────────────────

function WalletDetail({
  wallet,
  onBack,
  onRefresh,
}: {
  wallet: TrackedWallet;
  onBack: () => void;
  onRefresh: () => void;
}) {
  const [tokens, setTokens] = useState<WalletToken[]>([]);
  const [txns, setTxns] = useState<WalletTransaction[]>([]);
  const [syncing, setSyncing] = useState(false);
  const [tab, setTab] = useState<"tokens" | "transactions">("tokens");
  const [syncError, setSyncError] = useState<string | null>(null);

  useEffect(() => {
    apiFetch<WalletToken[]>(`/wallets/${wallet.id}/tokens`).then(setTokens).catch(() => {});
    apiFetch<WalletTransaction[]>(`/wallets/${wallet.id}/transactions`).then(setTxns).catch(() => {});
  }, [wallet.id]);

  async function handleSync() {
    setSyncing(true);
    setSyncError(null);
    try {
      await apiFetch(`/wallets/${wallet.id}/sync`, { method: "POST" });
      const [newTokens, newTxns] = await Promise.all([
        apiFetch<WalletToken[]>(`/wallets/${wallet.id}/tokens`),
        apiFetch<WalletTransaction[]>(`/wallets/${wallet.id}/transactions`),
      ]);
      setTokens(newTokens);
      setTxns(newTxns);
      onRefresh();
    } catch (err) {
      setSyncError(err instanceof Error ? err.message : String(err));
    } finally {
      setSyncing(false);
    }
  }

  const totalUsd = tokens.reduce((sum, t) => sum + (t.balance_usd ?? 0), 0);

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center gap-3">
        <button
          onClick={onBack}
          className="text-gray-400 hover:text-white transition-colors text-sm"
        >
          ← Back
        </button>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <h2 className="text-white font-semibold text-lg truncate">
              {wallet.label ?? shortAddr(wallet.address)}
            </h2>
            <ChainBadge chain={wallet.chain} />
          </div>
          <p className="text-gray-400 text-xs font-mono">{wallet.address}</p>
        </div>
        <button
          onClick={handleSync}
          disabled={syncing}
          className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded-lg px-4 py-2 text-sm font-medium transition-colors"
        >
          {syncing ? "Syncing…" : "Sync Now"}
        </button>
      </div>

      {syncError && (
        <div className="bg-red-900/30 border border-red-500/30 rounded-lg p-3 text-red-300 text-sm">
          {syncError}
        </div>
      )}

      {/* Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {[
          { label: "Total Value", value: fmtUsd(totalUsd) },
          { label: "Tokens", value: String(tokens.length) },
          { label: "Transactions", value: String(txns.length) },
          { label: "Last Synced", value: wallet.last_synced_at ? new Date(wallet.last_synced_at).toLocaleDateString() : "Never" },
        ].map(({ label, value }) => (
          <div key={label} className="bg-gray-800 border border-gray-700 rounded-lg p-3">
            <p className="text-gray-400 text-xs mb-1">{label}</p>
            <p className="text-white font-semibold text-sm">{value}</p>
          </div>
        ))}
      </div>

      {/* Polymarket stats (if available) */}
      {wallet.polymarket_volume != null && (
        <div className="bg-purple-900/20 border border-purple-500/30 rounded-lg p-4">
          <h3 className="text-purple-300 text-sm font-medium mb-3">Polymarket Performance</h3>
          <div className="grid grid-cols-3 gap-4">
            <div>
              <p className="text-gray-400 text-xs">Volume</p>
              <p className="text-white font-semibold">{fmtUsd(wallet.polymarket_volume)}</p>
            </div>
            <div>
              <p className="text-gray-400 text-xs">Win Rate</p>
              <p className="text-green-400 font-semibold">{fmt(wallet.polymarket_win_rate)}%</p>
            </div>
            <div>
              <p className="text-gray-400 text-xs">P&L</p>
              <p className={`font-semibold ${(wallet.polymarket_pnl ?? 0) >= 0 ? "text-green-400" : "text-red-400"}`}>
                {fmtUsd(wallet.polymarket_pnl)}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-2">
        {(["tokens", "transactions"] as const).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2 rounded-lg text-sm font-medium capitalize transition-colors ${
              tab === t ? "bg-blue-600 text-white" : "bg-gray-800 text-gray-400 hover:text-white"
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      {tab === "tokens" && (
        <div className="bg-gray-900 border border-gray-700 rounded-xl overflow-hidden">
          {tokens.length === 0 ? (
            <div className="p-6 text-center text-gray-500 text-sm">
              No tokens found. Click "Sync Now" to fetch holdings.
            </div>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-700">
                  <th className="text-left text-gray-400 px-4 py-3 font-medium">Token</th>
                  <th className="text-right text-gray-400 px-4 py-3 font-medium">Balance</th>
                  <th className="text-right text-gray-400 px-4 py-3 font-medium">Price</th>
                  <th className="text-right text-gray-400 px-4 py-3 font-medium">Value (USD)</th>
                </tr>
              </thead>
              <tbody>
                {tokens.map((tok) => (
                  <tr key={tok.id} className="border-b border-gray-800 hover:bg-gray-800/50 transition-colors">
                    <td className="px-4 py-3">
                      <div className="font-medium text-white">{tok.token_symbol}</div>
                      {tok.token_name && <div className="text-gray-500 text-xs">{tok.token_name}</div>}
                    </td>
                    <td className="px-4 py-3 text-right text-gray-300">{fmt(tok.balance, 6)}</td>
                    <td className="px-4 py-3 text-right text-gray-300">{fmtUsd(tok.price_usd)}</td>
                    <td className="px-4 py-3 text-right font-medium text-white">{fmtUsd(tok.balance_usd)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {tab === "transactions" && (
        <div className="bg-gray-900 border border-gray-700 rounded-xl overflow-hidden">
          {txns.length === 0 ? (
            <div className="p-6 text-center text-gray-500 text-sm">
              No transactions found. Click "Sync Now" to fetch history.
            </div>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-700">
                  <th className="text-left text-gray-400 px-4 py-3 font-medium">Tx Hash</th>
                  <th className="text-left text-gray-400 px-4 py-3 font-medium">Type</th>
                  <th className="text-left text-gray-400 px-4 py-3 font-medium">Asset</th>
                  <th className="text-right text-gray-400 px-4 py-3 font-medium">Value</th>
                  <th className="text-right text-gray-400 px-4 py-3 font-medium">Date</th>
                </tr>
              </thead>
              <tbody>
                {txns.slice(0, 50).map((tx) => (
                  <tr key={tx.id} className="border-b border-gray-800 hover:bg-gray-800/50 transition-colors">
                    <td className="px-4 py-3 font-mono text-blue-400 text-xs">
                      {shortAddr(tx.tx_hash)}
                    </td>
                    <td className="px-4 py-3">
                      <span className={`text-xs px-2 py-0.5 rounded-full ${
                        tx.tx_type === "receive"
                          ? "bg-green-900/40 text-green-400"
                          : tx.tx_type === "send"
                          ? "bg-red-900/40 text-red-400"
                          : "bg-gray-700 text-gray-300"
                      }`}>
                        {tx.tx_type ?? "unknown"}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-300">{tx.asset ?? "—"}</td>
                    <td className="px-4 py-3 text-right text-white">{fmt(tx.value, 6)}</td>
                    <td className="px-4 py-3 text-right text-gray-400 text-xs">
                      {tx.timestamp ? new Date(tx.timestamp).toLocaleDateString() : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  );
}

// ── Main Dashboard ─────────────────────────────────────────────────────────────

export default function WalletDashboard() {
  const [wallets, setWallets] = useState<TrackedWallet[]>([]);
  const [summary, setSummary] = useState<PortfolioSummary | null>(null);
  const [selectedWallet, setSelectedWallet] = useState<TrackedWallet | null>(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    setError(null);
    setLoading(true);
    try {
      const [ws, sum] = await Promise.all([
        apiFetch<TrackedWallet[]>("/wallets"),
        apiFetch<PortfolioSummary>("/wallets/portfolio/summary"),
      ]);
      setWallets(ws);
      setSummary(sum);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    let cancelled = false;
    apiFetch<TrackedWallet[]>("/wallets")
      .then((ws) => { if (!cancelled) setWallets(ws); })
      .catch((err) => { if (!cancelled) setError(err instanceof Error ? err.message : String(err)); });
    apiFetch<PortfolioSummary>("/wallets/portfolio/summary")
      .then((sum) => { if (!cancelled) setSummary(sum); })
      .catch(() => {})
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, []);

  if (selectedWallet) {
    return (
      <div className="min-h-screen bg-gray-950 text-white p-4 md:p-8">
        <WalletDetail
          wallet={selectedWallet}
          onBack={() => setSelectedWallet(null)}
          onRefresh={refresh}
        />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-950 text-white p-4 md:p-8">
      {showAddModal && (
        <AddWalletModal
          onClose={() => setShowAddModal(false)}
          onAdded={refresh}
        />
      )}

      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">Wallet Tracker</h1>
          <p className="text-gray-400 text-sm mt-1">
            Multi-chain portfolio tracking powered by Alchemy &amp; CoinGecko
          </p>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="bg-blue-600 hover:bg-blue-700 text-white rounded-lg px-4 py-2 text-sm font-medium transition-colors"
        >
          + Add Wallet
        </button>
      </div>

      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
          <div className="bg-gray-900 border border-gray-700 rounded-xl p-4">
            <p className="text-gray-400 text-xs mb-1">Total Value</p>
            <p className="text-white text-xl font-bold">{fmtUsd(summary.total_value_usd)}</p>
          </div>
          <div className="bg-gray-900 border border-gray-700 rounded-xl p-4">
            <p className="text-gray-400 text-xs mb-1">Wallets Tracked</p>
            <p className="text-white text-xl font-bold">{summary.total_wallets}</p>
          </div>
          <div className="bg-gray-900 border border-gray-700 rounded-xl p-4">
            <p className="text-gray-400 text-xs mb-1">Chains</p>
            <p className="text-white text-xl font-bold">{Object.keys(summary.chain_allocation).length}</p>
          </div>
          <div className="bg-gray-900 border border-gray-700 rounded-xl p-4">
            <p className="text-gray-400 text-xs mb-1">Top Chain</p>
            <p className="text-white text-xl font-bold">
              {Object.entries(summary.chain_allocation).sort((a, b) => b[1] - a[1])[0]?.[0]
                ? CHAIN_LABELS[Object.entries(summary.chain_allocation).sort((a, b) => b[1] - a[1])[0][0]] ?? "—"
                : "—"}
            </p>
          </div>
        </div>
      )}

      {/* Chain Allocation */}
      {summary && Object.keys(summary.chain_allocation).length > 0 && (
        <div className="bg-gray-900 border border-gray-700 rounded-xl p-4 mb-6">
          <h3 className="text-sm font-medium text-gray-400 mb-3">Chain Allocation</h3>
          <div className="flex flex-wrap gap-3">
            {Object.entries(summary.chain_allocation)
              .sort((a, b) => b[1] - a[1])
              .map(([chain, usd]) => {
                const pct = summary.total_value_usd > 0
                  ? ((usd / summary.total_value_usd) * 100).toFixed(1)
                  : "0.0";
                return (
                  <div key={chain} className="flex items-center gap-2">
                    <ChainBadge chain={chain} />
                    <span className="text-white text-sm font-medium">{pct}%</span>
                    <span className="text-gray-500 text-xs">{fmtUsd(usd)}</span>
                  </div>
                );
              })}
          </div>
        </div>
      )}

      {/* Error / Loading */}
      {error && (
        <div className="bg-red-900/30 border border-red-500/30 rounded-xl p-4 mb-4 text-red-300 text-sm">
          Failed to load wallet data: {error}
        </div>
      )}

      {loading && (
        <div className="text-center py-12 text-gray-500">Loading wallets…</div>
      )}

      {/* Wallet List */}
      {!loading && wallets.length === 0 && (
        <div className="bg-gray-900 border border-gray-700 border-dashed rounded-xl p-12 text-center">
          <p className="text-gray-400 mb-2">No wallets tracked yet.</p>
          <p className="text-gray-500 text-sm mb-4">
            Add your first wallet or import from Polymarket.
          </p>
          <button
            onClick={() => setShowAddModal(true)}
            className="bg-blue-600 hover:bg-blue-700 text-white rounded-lg px-6 py-2 text-sm font-medium transition-colors"
          >
            Add Wallet
          </button>
        </div>
      )}

      {!loading && wallets.length > 0 && (
        <div className="space-y-3">
          {wallets.map((w) => (
            <div
              key={w.id}
              onClick={() => setSelectedWallet(w)}
              className="bg-gray-900 border border-gray-700 rounded-xl p-4 cursor-pointer hover:border-blue-500/50 hover:bg-gray-800/60 transition-all"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <div className="flex items-center gap-2 flex-wrap mb-1">
                    <span className="text-white font-medium">
                      {w.label ?? shortAddr(w.address)}
                    </span>
                    <ChainBadge chain={w.chain} />
                  </div>
                  <p className="text-gray-500 text-xs font-mono truncate">{w.address}</p>
                </div>
                <div className="text-right shrink-0">
                  <SyncStatus lastSynced={w.last_synced_at} />
                  {w.polymarket_win_rate != null && (
                    <p className="text-green-400 text-xs mt-1">
                      {fmt(w.polymarket_win_rate)}% win rate
                    </p>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Polymarket import hint */}
      {wallets.length === 0 && !loading && (
        <div className="mt-6 bg-purple-900/10 border border-purple-500/20 rounded-xl p-4 text-sm text-gray-400">
          <p className="font-medium text-purple-300 mb-1">Import from Polymarket</p>
          <code className="text-xs block bg-gray-900 rounded p-2 font-mono mt-2">
            python scripts/polymarket_import.py --bot-data scripts/example_wallets.json --auto-sync
          </code>
        </div>
      )}
    </div>
  );
}
