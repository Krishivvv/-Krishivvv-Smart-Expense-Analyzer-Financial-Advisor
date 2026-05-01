import { useState, useRef } from 'react'
import api from '../api/client.js'
import { UploadCloud, FileSpreadsheet, Download, CheckCircle2, Loader2, AlertTriangle } from 'lucide-react'
import CategoryBadge from '../components/CategoryBadge.jsx'

export default function Upload() {
  const [file, setFile] = useState(null)
  const [dragOver, setDragOver] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const inputRef = useRef(null)

  const onDrop = (e) => {
    e.preventDefault()
    setDragOver(false)
    const f = e.dataTransfer.files?.[0]
    if (f) setFile(f)
  }

  const upload = async () => {
    if (!file) return
    setUploading(true)
    setError(null)
    setResult(null)
    try {
      const fd = new FormData()
      fd.append('file', file)
      const r = await api.post('/upload/csv', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
      setResult(r.data)
    } catch (e) {
      setError(e?.response?.data?.detail || e.message || 'Upload failed')
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="space-y-6 animate-fade-in max-w-3xl">
      <div>
        <h1 className="text-2xl font-bold">Bulk Upload</h1>
        <p className="text-gray-400 text-sm">Upload a CSV of expenses — they'll be auto-categorised and scanned for anomalies.</p>
      </div>

      <div className="flex items-center justify-between flex-wrap gap-3">
        <a href="/api/upload/template" className="btn-secondary inline-flex items-center gap-2" download>
          <Download className="w-4 h-4" /> Download CSV template
        </a>
        <div className="text-xs text-gray-500">
          Required columns: <code className="bg-gray-800 px-1 rounded">description, amount</code>; optional: <code className="bg-gray-800 px-1 rounded">category, date, payment_method</code>
        </div>
      </div>

      <div
        className={`card border-2 border-dashed transition-colors cursor-pointer ${dragOver ? 'border-brand-500 bg-brand-900/10' : 'border-gray-700'}`}
        onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
        onDragLeave={() => setDragOver(false)}
        onDrop={onDrop}
        onClick={() => inputRef.current?.click()}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".csv"
          className="hidden"
          onChange={(e) => setFile(e.target.files?.[0] || null)}
        />
        <div className="flex flex-col items-center gap-3 py-10">
          <UploadCloud className="w-12 h-12 text-brand-400" />
          {file ? (
            <div className="text-center">
              <div className="font-medium flex items-center gap-2 justify-center">
                <FileSpreadsheet className="w-4 h-4" /> {file.name}
              </div>
              <div className="text-xs text-gray-500">{(file.size / 1024).toFixed(1)} KB</div>
            </div>
          ) : (
            <div className="text-center">
              <div className="font-medium">Drop CSV here or click to browse</div>
              <div className="text-xs text-gray-500">.csv files only</div>
            </div>
          )}
        </div>
      </div>

      <div className="flex justify-end">
        <button
          onClick={upload}
          disabled={!file || uploading}
          className="btn-primary inline-flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {uploading && <Loader2 className="w-4 h-4 animate-spin" />}
          {uploading ? 'Processing...' : 'Upload & Analyze'}
        </button>
      </div>

      {error && (
        <div className="card border-rose-700/50 bg-rose-950/30 flex items-center gap-2">
          <AlertTriangle className="w-5 h-5 text-rose-400" />
          <span className="text-rose-300 text-sm">{error}</span>
        </div>
      )}

      {result && (
        <div className="card border-emerald-700/50 bg-emerald-950/20 animate-slide-up">
          <div className="flex items-center gap-3 mb-3">
            <CheckCircle2 className="w-6 h-6 text-emerald-400" />
            <div className="text-lg font-semibold">Upload complete</div>
          </div>
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div>
              <div className="text-xs text-gray-400">Expenses added</div>
              <div className="text-3xl font-bold text-emerald-300">{result.inserted}</div>
            </div>
            <div>
              <div className="text-xs text-gray-400">Anomalies found</div>
              <div className="text-3xl font-bold text-rose-300">{result.anomalies_found}</div>
            </div>
          </div>
          <div>
            <div className="text-xs text-gray-400 mb-2">Categories detected</div>
            <div className="flex flex-wrap gap-2">
              {Object.entries(result.categories_detected || {}).map(([cat, n]) => (
                <div key={cat} className="flex items-center gap-2 bg-gray-800/60 px-2 py-1 rounded-lg">
                  <CategoryBadge category={cat} />
                  <span className="text-xs text-gray-300">{n}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
