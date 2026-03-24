import React, { useState, useEffect, useCallback } from 'react';
import api from './api';

interface ReconciliationRun {
  id: string;
  bank_upload_ids: string[];
  admin_upload_id: string;
  status: string;
  created_at: string;
}

const Workspace: React.FC = () => {
  const [runs, setRuns] = useState<ReconciliationRun[]>([]);
  const [bankUploads, setBankUploads] = useState<any[]>([]);
  const [adminUploads, setAdminUploads] = useState<any[]>([]);
  const [selectedBankIds, setSelectedBankIds] = useState<string[]>([]);
  const [selectedAdminId, setSelectedAdminId] = useState<string>('');
  const [isStarting, setIsStarting] = useState(false);
  
  const [bankFiles, setBankFiles] = useState<FileList | null>(null);
  const [adminFile, setAdminFile] = useState<File | null>(null);
  const [isUploadingBank, setIsUploadingBank] = useState(false);
  const [isUploadingAdmin, setIsUploadingAdmin] = useState(false);
  const [uploadError, setUploadError] = useState('');

  const fetchData = useCallback(async () => {
    try {
      const [runsRes, uploadsRes] = await Promise.all([
        api.get('/reconciliation/runs'),
        api.get('/uploads')
      ]);
      setRuns(runsRes.data);
      setBankUploads(uploadsRes.data.filter((u: any) => u.type === 'bank' && u.status === 'succeeded'));
      setAdminUploads(uploadsRes.data.filter((u: any) => u.type === 'admin' && u.status === 'succeeded'));
    } catch (err) {
      console.error('Failed to fetch workspace data', err);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleUploadBank = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!bankFiles || bankFiles.length === 0) return;
    setIsUploadingBank(true);
    setUploadError('');
    
    for (const file of Array.from(bankFiles)) {
      const formData = new FormData();
      formData.append('file', file);
      try {
        await api.post('/uploads/bank', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        });
      } catch (err: any) {
        setUploadError(`${file.name}: ${err.response?.data?.detail || 'Upload failed'}`);
      }
    }
    
    setBankFiles(null);
    fetchData();
    setIsUploadingBank(false);
  };

  const handleUploadAdmin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!adminFile) return;
    setIsUploadingAdmin(true);
    setUploadError('');
    const formData = new FormData();
    formData.append('file', adminFile);
    try {
      await api.post('/uploads/admin', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setAdminFile(null);
      fetchData();
    } catch (err: any) {
      setUploadError(err.response?.data?.detail || 'Upload failed');
    } finally {
      setIsUploadingAdmin(false);
    }
  };

  const handleStartRun = async () => {
    if (selectedBankIds.length === 0 || !selectedAdminId) return;
    setIsStarting(true);
    try {
      await api.post('/reconciliation/runs', {
        bank_upload_ids: selectedBankIds,
        admin_upload_id: selectedAdminId
      });
      fetchData();
      setSelectedBankIds([]);
      setSelectedAdminId('');
    } catch (err) {
      alert('Failed to start reconciliation run');
    } finally {
      setIsStarting(false);
    }
  };

  return (
    <div style={{ padding: '20px' }}>
      <h2>Reconciliation Workspace</h2>
      
      <div style={{ marginBottom: '30px', border: '1px solid #eee', padding: '20px', borderRadius: '8px' }}>
        <h3>New Reconciliation Run</h3>
        {uploadError && <p style={{ color: 'red' }}>{uploadError}</p>}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '15px' }}>
          <div>
            <label style={{ display: 'block', fontWeight: 'bold' }}>Bank Statements</label>
            <form onSubmit={handleUploadBank} style={{ marginBottom: '10px' }}>
              <div style={{ display: 'flex', gap: '10px', marginBottom: '5px' }}>
                <input
                  type="file"
                  multiple
                  onChange={(e) => setBankFiles(e.target.files)}
                  accept=".csv,.xls,.xlsx,.pdf"
                  style={{ flex: 1 }}
                />
                <button
                  type="submit"
                  disabled={isUploadingBank || !bankFiles || bankFiles.length === 0}
                  style={{ padding: '5px 15px', backgroundColor: '#007bff', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
                >
                  {isUploadingBank ? '...' : 'Upload'}
                </button>
              </div>
            </form>
            <select
              multiple
              value={selectedBankIds}
              onChange={(e) => setSelectedBankIds(Array.from(e.target.selectedOptions, option => option.value))}
              style={{ width: '100%', height: '80px', padding: '5px' }}
            >
              {bankUploads.map(u => (
                <option key={u.id} value={u.id}>{u.filename}</option>
              ))}
            </select>
            <small style={{ color: '#666' }}>Select uploaded files for matching</small>
          </div>
          <div>
            <label style={{ display: 'block', fontWeight: 'bold' }}>Admin Report</label>
            <form onSubmit={handleUploadAdmin} style={{ marginBottom: '10px' }}>
              <div style={{ display: 'flex', gap: '10px', marginBottom: '5px' }}>
                <input
                  type="file"
                  onChange={(e) => setAdminFile(e.target.files?.[0] || null)}
                  accept=".csv,.xls,.xlsx"
                  style={{ flex: 1 }}
                />
                <button
                  type="submit"
                  disabled={isUploadingAdmin || !adminFile}
                  style={{ padding: '5px 15px', backgroundColor: '#007bff', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
                >
                  {isUploadingAdmin ? '...' : 'Upload'}
                </button>
              </div>
            </form>
            <select
              value={selectedAdminId}
              onChange={(e) => setSelectedAdminId(e.target.value)}
              style={{ width: '100%', height: '35px', padding: '5px' }}
            >
              <option value="">Select an admin report</option>
              {adminUploads.map(u => (
                <option key={u.id} value={u.id}>{u.filename}</option>
              ))}
            </select>
          </div>
        </div>
        <button
          onClick={handleStartRun}
          disabled={isStarting || selectedBankIds.length === 0 || !selectedAdminId}
          style={{ padding: '10px 20px', backgroundColor: '#28a745', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
        >
          {isStarting ? 'Starting...' : 'Start Matching'}
        </button>
      </div>

      <h3>Recent Runs</h3>
      <div style={{ display: 'grid', gap: '15px' }}>
        {runs.map(run => (
          <div key={run.id} style={{ border: '1px solid #eee', padding: '15px', borderRadius: '8px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <strong>Run ID: {run.id.slice(0, 8)}</strong>
              <div style={{ fontSize: '0.9em', color: '#666' }}>Created: {new Date(run.created_at).toLocaleString()}</div>
            </div>
            <button
              onClick={() => window.location.href = `/workspace/${run.id}`}
              style={{ padding: '8px 15px', border: '1px solid #007bff', color: '#007bff', backgroundColor: 'transparent', borderRadius: '4px', cursor: 'pointer' }}
            >
              View Matches
            </button>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Workspace;
