import React, { useState, useEffect, useCallback } from 'react';
import api from './api';

interface Upload {
  id: string;
  filename: string;
  type: 'bank' | 'admin';
  status: 'pending' | 'processing' | 'succeeded' | 'failed';
  error_message?: string;
  created_at: string;
}

const Uploads: React.FC = () => {
  const [uploads, setUploads] = useState<Upload[]>([]);
  const [file, setFile] = useState<File | null>(null);
  const [uploadType, setUploadType] = useState<'bank' | 'admin'>('bank');
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState('');

  const fetchUploads = useCallback(async () => {
    try {
      const { data } = await api.get('/uploads');
      setUploads(data);
    } catch (err) {
      console.error('Failed to fetch uploads', err);
    }
  }, []);

  useEffect(() => {
    fetchUploads();
    const interval = setInterval(fetchUploads, 5000);
    return () => clearInterval(interval);
  }, [fetchUploads]);

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;

    setIsUploading(true);
    setError('');
    const formData = new FormData();
    formData.append('file', file);

    try {
      const endpoint = uploadType === 'bank' ? '/uploads/bank' : '/uploads/admin';
      await api.post(endpoint, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setFile(null);
      fetchUploads();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Upload failed');
    } finally {
      setIsUploading(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this file? This will also remove associated transactions.')) {
      return;
    }
    try {
      await api.delete(`/uploads/${id}`);
      fetchUploads();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Delete failed');
    }
  };

  return (
    <div style={{ padding: '20px' }}>
      <h2>File Uploads</h2>
      <form onSubmit={handleUpload} style={{ marginBottom: '30px', border: '1px solid #eee', padding: '20px', borderRadius: '8px' }}>
        <div style={{ marginBottom: '15px' }}>
          <label style={{ marginRight: '15px' }}>
            <input type="radio" checked={uploadType === 'bank'} onChange={() => setUploadType('bank')} /> Bank Statement
          </label>
          <label>
            <input type="radio" checked={uploadType === 'admin'} onChange={() => setUploadType('admin')} /> Admin Report
          </label>
        </div>
        <div style={{ marginBottom: '15px' }}>
          <input type="file" onChange={(e) => setFile(e.target.files?.[0] || null)} required />
        </div>
        {error && <p style={{ color: 'red' }}>{error}</p>}
        <button type="submit" disabled={isUploading || !file} style={{ padding: '8px 15px', backgroundColor: '#007bff', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
          {isUploading ? 'Uploading...' : 'Upload File'}
        </button>
      </form>

      <h3>Upload History</h3>
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr style={{ textAlign: 'left', borderBottom: '2px solid #eee' }}>
            <th style={{ padding: '10px' }}>Filename</th>
            <th style={{ padding: '10px' }}>Type</th>
            <th style={{ padding: '10px' }}>Status</th>
            <th style={{ padding: '10px' }}>Date</th>
            <th style={{ padding: '10px' }}>Actions</th>
          </tr>
        </thead>
        <tbody>
          {uploads.map((u) => (
            <tr key={u.id} style={{ borderBottom: '1px solid #eee' }}>
              <td style={{ padding: '10px' }}>{u.filename}</td>
              <td style={{ padding: '10px' }}>{u.type}</td>
              <td style={{ padding: '10px' }}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                  <span style={{
                    padding: '2px 8px',
                    borderRadius: '12px',
                    fontSize: '0.85em',
                    display: 'inline-block',
                    backgroundColor: u.status === 'succeeded' ? '#d4edda' : u.status === 'failed' ? '#f8d7da' : '#fff3cd',
                    color: u.status === 'succeeded' ? '#155724' : u.status === 'failed' ? '#721c24' : '#856404'
                  }}>
                    {u.status}
                  </span>
                  {u.error_message && (
                    <span style={{ fontSize: '0.75em', color: '#dc3545' }} title={u.error_message}>
                      {u.error_message.slice(0, 50)}...
                    </span>
                  )}
                </div>
              </td>
              <td style={{ padding: '10px' }}>{new Date(u.created_at).toLocaleString()}</td>
              <td style={{ padding: '10px' }}>
                <button
                  onClick={() => handleDelete(u.id)}
                  style={{
                    padding: '4px 12px',
                    backgroundColor: '#dc3545',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    fontSize: '0.85em'
                  }}
                >
                  Delete
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default Uploads;
