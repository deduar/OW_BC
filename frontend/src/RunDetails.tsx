import React, { useState, useEffect, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import api from './api';

interface Match {
  id: string;
  bank_transaction_id: string;
  admin_entry_id: string;
  score: number;
  explanation: any;
  is_confirmed: boolean;
  bank_transaction: any;
  admin_entry: any;
}

const RunDetails: React.FC = () => {
  const { runId } = useParams<{ runId: string }>();
  const [matches, setMatches] = useState<Match[]>([]);
  const [suggestions, setSuggestions] = useState<Match[]>([]);
  const [unmatchedBank, setUnmatchedBank] = useState<any[]>([]);
  const [unmatchedAdmin, setUnmatchedAdmin] = useState<any[]>([]);
  const [activeTab, setActiveTab] = useState<'matched' | 'suggested' | 'unmatched'>('suggested');
  const [isRefreshing, setIsRefreshing] = useState(false);

  const fetchResults = useCallback(async () => {
    setIsRefreshing(true);
    try {
      const [matchesRes, suggestionsRes, unmatchedRes] = await Promise.all([
        api.get(`/reconciliation/runs/${runId}/matches`),
        api.get(`/reconciliation/runs/${runId}/suggestions`),
        api.get(`/reconciliation/runs/${runId}/unmatched`)
      ]);
      setMatches(matchesRes.data);
      setSuggestions(suggestionsRes.data);
      setUnmatchedBank(unmatchedRes.data.bank_transactions);
      setUnmatchedAdmin(unmatchedRes.data.admin_entries);
    } catch (err) {
      console.error('Failed to fetch run results', err);
    } finally {
      setIsRefreshing(false);
    }
  }, [runId]);

  useEffect(() => {
    fetchResults();
  }, [fetchResults]);

  const handleConfirm = async (matchId: string) => {
    try {
      await api.post(`/reconciliation/matches/${matchId}/confirm`);
      fetchResults();
    } catch (err) {
      alert('Failed to confirm match');
    }
  };

  const handleReject = async (matchId: string) => {
    try {
      await api.post(`/reconciliation/matches/${matchId}/reject`);
      fetchResults();
    } catch (err) {
      alert('Failed to reject match');
    }
  };

  const handleExport = async () => {
    try {
      const response = await api.get(`/reconciliation/runs/${runId}/export/csv`, {
        responseType: 'blob',
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `reconciliation_${runId}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      alert('Failed to export CSV');
    }
  };

  return (
    <div style={{ padding: '20px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <Link to="/" style={{ color: '#007bff' }}>&larr; Back to Workspace</Link>
        <h2>Run Details: {runId?.slice(0, 8)}</h2>
        <div style={{ display: 'flex', gap: '10px' }}>
          <button onClick={handleExport} style={{ padding: '5px 10px', backgroundColor: '#6c757d', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
            Export CSV
          </button>
          <button onClick={fetchResults} disabled={isRefreshing} style={{ padding: '5px 10px' }}>
            {isRefreshing ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>
      </div>

      <div style={{ display: 'flex', borderBottom: '2px solid #eee', marginBottom: '20px' }}>
        <button onClick={() => setActiveTab('matched')} style={tabStyle(activeTab === 'matched')}>Matched ({matches.length})</button>
        <button onClick={() => setActiveTab('suggested')} style={tabStyle(activeTab === 'suggested')}>Suggested ({suggestions.length})</button>
        <button onClick={() => setActiveTab('unmatched')} style={tabStyle(activeTab === 'unmatched')}>Unmatched ({unmatchedBank.length + unmatchedAdmin.length})</button>
      </div>

      {activeTab === 'matched' && (
        <MatchTable matches={matches} />
      )}

      {activeTab === 'suggested' && (
        <SuggestionTable suggestions={suggestions} onConfirm={handleConfirm} onReject={handleReject} />
      )}

      {activeTab === 'unmatched' && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
          <div>
            <h4>Bank Transactions</h4>
            <TransactionList transactions={unmatchedBank} />
          </div>
          <div>
            <h4>Admin Entries</h4>
            <TransactionList transactions={unmatchedAdmin} />
          </div>
        </div>
      )}
    </div>
  );
};

const tabStyle = (isActive: boolean) => ({
  padding: '10px 20px',
  border: 'none',
  backgroundColor: 'transparent',
  borderBottom: isActive ? '3px solid #007bff' : '3px solid transparent',
  color: isActive ? '#007bff' : '#666',
  cursor: 'pointer',
  fontWeight: isActive ? 'bold' : 'normal'
});

const MatchTable: React.FC<{ matches: Match[] }> = ({ matches }) => (
  <table style={{ width: '100%', borderCollapse: 'collapse' }}>
    <thead>
      <tr style={{ textAlign: 'left', borderBottom: '1px solid #eee' }}>
        <th style={{ padding: '10px' }}>Bank Transaction</th>
        <th style={{ padding: '10px' }}>Admin Entry</th>
        <th style={{ padding: '10px' }}>Amount</th>
        <th style={{ padding: '10px' }}>Score</th>
      </tr>
    </thead>
    <tbody>
      {matches.map(m => (
        <tr key={m.id} style={{ borderBottom: '1px solid #eee' }}>
          <td style={{ padding: '10px' }}>
            <div style={{ fontSize: '0.9em' }}>{m.bank_transaction.raw_description}</div>
            <div style={{ fontSize: '0.8em', color: '#888' }}>{m.bank_transaction.date}</div>
          </td>
          <td style={{ padding: '10px' }}>
            <div style={{ fontSize: '0.9em' }}>{m.admin_entry.description || 'N/A'}</div>
            <div style={{ fontSize: '0.8em', color: '#888' }}>Ref: {m.admin_entry.reference} | {m.admin_entry.date}</div>
          </td>
          <td style={{ padding: '10px' }}>{m.bank_transaction.amount.toFixed(2)}</td>
          <td style={{ padding: '10px' }}>{m.score}</td>
        </tr>
      ))}
    </tbody>
  </table>
);

const SuggestionTable: React.FC<{ suggestions: Match[], onConfirm: (id: string) => void, onReject: (id: string) => void }> = ({ suggestions, onConfirm, onReject }) => (
  <div style={{ display: 'grid', gap: '15px' }}>
    {suggestions.map(s => (
      <div key={s.id} style={{ border: '1px solid #eee', padding: '15px', borderRadius: '8px', display: 'grid', gridTemplateColumns: '1fr auto 1fr auto', alignItems: 'center', gap: '20px' }}>
        <div>
          <div style={{ fontWeight: 'bold' }}>{s.bank_transaction.raw_description}</div>
          <div style={{ fontSize: '0.85em', color: '#666' }}>{s.bank_transaction.date} | Amount: {s.bank_transaction.amount.toFixed(2)}</div>
        </div>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '1.2em', fontWeight: 'bold', color: '#28a745' }}>{s.score}</div>
          <div style={{ fontSize: '0.7em', color: '#888' }}>score</div>
        </div>
        <div>
          <div style={{ fontWeight: 'bold' }}>{s.admin_entry.description || 'Admin Entry'}</div>
          <div style={{ fontSize: '0.85em', color: '#666' }}>Ref: {s.admin_entry.reference} | Date: {s.admin_entry.date} | Amount: {s.admin_entry.amount.toFixed(2)}</div>
        </div>
        <div style={{ display: 'flex', gap: '10px' }}>
          <button onClick={() => onConfirm(s.id)} style={{ padding: '5px 10px', backgroundColor: '#d4edda', color: '#155724', border: '1px solid #c3e6cb', borderRadius: '4px', cursor: 'pointer' }}>Confirm</button>
          <button onClick={() => onReject(s.id)} style={{ padding: '5px 10px', backgroundColor: '#f8d7da', color: '#721c24', border: '1px solid #f5c6cb', borderRadius: '4px', cursor: 'pointer' }}>Reject</button>
        </div>
      </div>
    ))}
  </div>
);

const TransactionList: React.FC<{ transactions: any[] }> = ({ transactions }) => (
  <div style={{ display: 'grid', gap: '10px', maxHeight: '500px', overflowY: 'auto' }}>
    {transactions.map(t => (
      <div key={t.id} style={{ padding: '10px', border: '1px solid #eee', borderRadius: '4px', fontSize: '0.85em' }}>
        <div style={{ fontWeight: 'bold' }}>{t.raw_description || t.description || 'N/A'}</div>
        <div>{t.date} | Amount: {t.amount.toFixed(2)}</div>
        {t.reference && <div>Ref: {t.reference}</div>}
      </div>
    ))}
  </div>
);

export default RunDetails;
