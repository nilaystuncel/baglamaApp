import { useEffect, useRef, useState } from 'react'
import WaveSurfer from 'wavesurfer.js'
import { parseApiError, toWavBlob } from './audioUtils'

const API = ''

function App() {
  const [references, setReferences] = useState([])
  const [selectedRef, setSelectedRef] = useState('')
  const [refNotes, setRefNotes] = useState([])
  const [showNotes, setShowNotes] = useState(false)
  const [audioBlob, setAudioBlob] = useState(null)
  const [audioUrl, setAudioUrl] = useState(null)
  const [recording, setRecording] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)
  const [history, setHistory] = useState([])

  const mediaRecorderRef = useRef(null)
  const chunksRef = useRef([])
  const waveformRef = useRef(null)
  const wavesurferRef = useRef(null)

  useEffect(() => {
    fetch(`${API}/api/references`)
      .then((r) => r.json())
      .then((data) => {
        setReferences(data)
        if (data.length) setSelectedRef(data[0].id)
      })
      .catch(() => setError('Backend bağlantısı kurulamadı. Sunucu çalışıyor mu?'))

    loadHistory()
  }, [])

  useEffect(() => {
    if (!audioUrl || !waveformRef.current) return

    if (wavesurferRef.current) {
      wavesurferRef.current.destroy()
    }

    wavesurferRef.current = WaveSurfer.create({
      container: waveformRef.current,
      waveColor: '#2f3b4a',
      progressColor: '#8ecae6',
      cursorColor: '#1d9bf0',
      height: 80,
      barWidth: 2,
      barGap: 1,
    })

    wavesurferRef.current.load(audioUrl)

    return () => {
      if (wavesurferRef.current) {
        wavesurferRef.current.destroy()
        wavesurferRef.current = null
      }
    }
  }, [audioUrl])

  const loadHistory = () => {
    fetch(`${API}/api/history`)
      .then((r) => r.json())
      .then(setHistory)
      .catch(() => {})
  }

  const handleRefChange = (id) => {
    setSelectedRef(id)
    setRefNotes([])
    setShowNotes(false)
  }

  const loadRefNotes = () => {
    if (!selectedRef) return
    fetch(`${API}/api/references/${selectedRef}/notes`)
      .then((r) => r.json())
      .then((data) => {
        setRefNotes(data.notes)
        setShowNotes(true)
      })
  }

  const handleFileChange = (e) => {
    const file = e.target.files[0]
    if (!file) return
    setAudioBlob(file)
    setAudioUrl(URL.createObjectURL(file))
    setResult(null)
    setError('')
  }

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const recorder = new MediaRecorder(stream)
      chunksRef.current = []

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data)
      }

      recorder.onstop = async () => {
        const webmBlob = new Blob(chunksRef.current, { type: 'audio/webm' })
        try {
          const wavBlob = await toWavBlob(webmBlob)
          wavBlob.name = 'recording.wav'
          setAudioBlob(wavBlob)
          setAudioUrl(URL.createObjectURL(wavBlob))
        } catch {
          setError('Kayıt WAV formatına dönüştürülemedi. Tekrar deneyin.')
        }
        stream.getTracks().forEach((t) => t.stop())
      }

      mediaRecorderRef.current = recorder
      recorder.start()
      setRecording(true)
      setResult(null)
      setError('')
    } catch {
      setError('Mikrofon erişimi reddedildi veya bulunamadı.')
    }
  }

  const stopRecording = () => {
    if (mediaRecorderRef.current?.state === 'recording') {
      mediaRecorderRef.current.stop()
    }
    setRecording(false)
  }

  const [debugNotes, setDebugNotes] = useState(null)

  const handleDebug = async () => {
    if (!audioBlob) return
    setLoading(true)
    try {
      const wavBlob = await toWavBlob(audioBlob)
      const form = new FormData()
      form.append('file', wavBlob, 'recording.wav')
      const res = await fetch(`${API}/api/debug-pitch`, { method: 'POST', body: form })
      const data = await res.json()
      setDebugNotes(data)
    } catch (err) {
      setError('Debug hatası: ' + err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleAnalyze = async () => {
    if (!audioBlob || !selectedRef) return

    setLoading(true)
    setError('')

    try {
      const wavBlob = await toWavBlob(audioBlob)
      const form = new FormData()
      form.append('file', wavBlob, 'recording.wav')
      form.append('reference_id', selectedRef)

      const res = await fetch(`${API}/api/upload-audio`, { method: 'POST', body: form })
      const data = await res.json()
      if (!res.ok) throw new Error(parseApiError(data))
      setResult(data)
      loadHistory()
    } catch (err) {
      setError(err.message || 'Analiz başarısız.')
    } finally {
      setLoading(false)
    }
  }

  const metrics = result?.analysis?.metrics
  const errors = result?.analysis?.errors || []

  return (
    <div>
      <h1>Bağlama Performans Analizi</h1>
      <p className="subtitle">Çalışınızı yükleyin veya kaydedin, sistem analiz etsin.</p>

      {error && <div className="status error">{error}</div>}

      <div className="card">
        <h2>1. Türkü Seç</h2>
        <label>Referans türkü</label>
        <select value={selectedRef} onChange={(e) => handleRefChange(e.target.value)}>
          {references.map((r) => (
            <option key={r.id} value={r.id}>
              {r.title} — {r.artist} ({r.expected_bpm} BPM)
            </option>
          ))}
        </select>
        <button className="btn-primary" onClick={loadRefNotes} style={{ marginTop: '0.5rem' }}>
          🎵 Notaları Göster
        </button>

        {showNotes && refNotes.length > 0 && (
          <div style={{ marginTop: '1rem' }}>
            <label>Nota Dizisi:</label>
            {(() => {
              const hasLines = refNotes.some(n => n.line)
              if (hasLines) {
                const lines = [...new Set(refNotes.map(n => n.line))].sort()
                return lines.map(line => (
                  <div key={line} style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem', marginTop: '0.5rem', marginBottom: '0.3rem' }}>
                    {refNotes.filter(n => n.line === line).map((n, i) => (
                      <span key={i} style={{
                        background: '#fff3e6',
                        border: '1px solid #e76f00',
                        borderRadius: '6px',
                        padding: '0.3rem 0.6rem',
                        fontSize: '0.85rem',
                        color: '#e76f00',
                        fontWeight: '600'
                      }}>
                        {n.solfege || n.note}
                      </span>
                    ))}
                  </div>
                ))
              }
              return (
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem', marginTop: '0.5rem' }}>
                  {refNotes.map((n, i) => (
                    <span key={i} style={{
                      background: '#fff3e6',
                      border: '1px solid #e76f00',
                      borderRadius: '6px',
                      padding: '0.3rem 0.6rem',
                      fontSize: '0.85rem',
                      color: '#e76f00',
                      fontWeight: '600'
                    }}>
                      {n.solfege || n.note}
                    </span>
                  ))}
                </div>
              )
            })()}
          </div>
        )}
      </div>

      <div className="card">
        <h2>2. Ses Kaydı</h2>
        <div className="btn-row">
          <button
            className="btn-primary"
            onClick={startRecording}
            disabled={recording}
          >
            🎙️ Canlı Kayıt
          </button>
          <button
            className="btn-danger"
            onClick={stopRecording}
            disabled={!recording}
          >
            ⏹ Durdur
          </button>
        </div>

        {recording && (
          <div className="recording-indicator">
            <span className="dot" /> Kayıt devam ediyor...
          </div>
        )}

        <label style={{ marginTop: '1rem' }}>veya dosya yükle (.wav önerilir)</label>
        <input type="file" accept="audio/*" onChange={handleFileChange} />

        {audioUrl && (
          <div className="waveform">
            <div ref={waveformRef} />
          </div>
        )}

        <div className="btn-row" style={{ marginTop: '1rem' }}>
          <button
            className="btn-primary"
            onClick={handleAnalyze}
            disabled={!audioBlob || loading}
          >
            {loading ? 'Analiz ediliyor...' : '▶ Analiz Et'}
          </button>
          <button
            className="btn-primary"
            onClick={handleDebug}
            disabled={!audioBlob || loading}
            style={{ background: '#555' }}
          >
            🔍 Notaları Gör
          </button>
        </div>
      </div>

      {debugNotes && (
        <div className="card">
          <h2>🔍 Algılanan Notalar ({debugNotes.note_count} nota)</h2>
          <p style={{ wordBreak: 'break-all', fontSize: '0.85rem' }}>
            {debugNotes.detected_notes.join(' → ')}
          </p>
          <p style={{ fontSize: '0.8rem', color: '#888', marginTop: '0.5rem' }}>
            Örnek frekanslar: {debugNotes.sample_frequencies_hz.join(', ')} Hz
          </p>
        </div>
      )}

      {result && (
        <>
          <div className="card">
            <h2>3. Sonuçlar — {result.reference_title}</h2>
            <div className="metrics">
              <div className="metric">
                <div className="value">{metrics.performance_score}</div>
                <div className="label">Performans Skoru</div>
              </div>
              <div className="metric">
                <div className="value">%{metrics.tempo_accuracy}</div>
                <div className="label">Tempo Doğruluğu</div>
              </div>
              <div className="metric">
                <div className="value">%{metrics.note_accuracy}</div>
                <div className="label">Nota Uyumu</div>
              </div>
              <div className="metric">
                <div className="value">%{metrics.stability}</div>
                <div className="label">Ses Stabilitesi</div>
              </div>
              <div className="metric">
                <div className="value">{metrics.detected_bpm}</div>
                <div className="label">Algılanan BPM</div>
              </div>
              <div className="metric">
                <div className="value">{metrics.expected_bpm}</div>
                <div className="label">Hedef BPM</div>
              </div>
            </div>

            {errors.length > 0 && (
              <>
                <h2 style={{ fontSize: '1rem', marginBottom: '0.5rem' }}>Hatalar</h2>
                <ul className="errors-list">
                  {errors.map((e, i) => (
                    <li key={i}>
                      {e.index + 1}. nota — beklenen: <strong>{e.expected_note}</strong>,
                      çalınan: <strong>{e.played_note}</strong>
                      {e.deviation_cents < 900 && ` (${e.deviation_cents} cent sapma)`}
                    </li>
                  ))}
                </ul>
              </>
            )}
          </div>

          <div className="card">
            <h2>Geri Bildirim</h2>
            <p className="feedback">{result.analysis.feedback}</p>
          </div>
        </>
      )}

      {history.length > 0 && (
        <div className="card">
          <h2>Geçmiş Performanslar</h2>
          <table className="history-table">
            <thead>
              <tr>
                <th>Türkü</th>
                <th>Skor</th>
                <th>Tempo</th>
                <th>Nota</th>
                <th>Stabilite</th>
                <th>Tarih</th>
              </tr>
            </thead>
            <tbody>
              {history.map((h) => (
                <tr key={h.id}>
                  <td>{h.reference_title}</td>
                  <td>{h.performance_score}</td>
                  <td>%{h.tempo_accuracy}</td>
                  <td>%{h.note_accuracy}</td>
                  <td>%{h.stability}</td>
                  <td>{new Date(h.created_at).toLocaleString('tr-TR')}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

export default App
