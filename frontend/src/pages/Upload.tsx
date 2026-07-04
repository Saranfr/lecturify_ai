import { useState, useCallback, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, apiFormData } from '../api/client'
import { Upload as UploadIcon, FileUp, Sparkles } from 'lucide-react'
import ProcessingModal, { type ProcessingStep } from '../components/ProcessingModal'

const ACCEPT = '.mp3,.wav,.m4a,.mp4,.avi,.mkv,.mpeg,.mpg,.pdf,.docx,.ppt,.pptx,.txt,.png,.jpg,.jpeg,.bmp,.tiff'

function getFileType(filename: string): 'video' | 'audio' | 'document' | 'image' {
  const ext = filename.split('.').pop()?.toLowerCase() || ''
  if (['mp4', 'avi', 'mkv', 'mov', 'webm', 'mpeg', 'mpg'].includes(ext)) return 'video'
  if (['mp3', 'wav', 'm4a', 'ogg', 'flac'].includes(ext)) return 'audio'
  if (['png', 'jpg', 'jpeg', 'bmp', 'tiff'].includes(ext)) return 'image'
  return 'document'
}

/** Match backend _split_mcq_counts: remainder to Easy, then Medium */
function splitMcqCounts(total: number): { easy: number; medium: number; hard: number } {
  const t = Math.min(30, Math.max(10, Math.round(total)))
  const base = Math.floor(t / 3)
  const rem = t % 3
  const easy = base + (rem >= 1 ? 1 : 0)
  const medium = base + (rem >= 2 ? 1 : 0)
  const hard = t - easy - medium
  return { easy, medium, hard }
}

export default function Upload() {
  const [file, setFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState('')
  const [modalStep, setModalStep] = useState<ProcessingStep | null>(null)
  const [modalError, setModalError] = useState<string | null>(null)
  const [mcqCount, setMcqCount] = useState<number | undefined>()
  const [resultByDifficulty, setResultByDifficulty] = useState<{
    easy: number
    medium: number
    hard: number
  } | null>(null)
  const [numQuestions, setNumQuestions] = useState(18)
  const [lectureId, setLectureId] = useState<string | null>(null)
  const [dragActive, setDragActive] = useState(false)
  const navigate = useNavigate()
  const questionPlan = useMemo(() => splitMcqCounts(numQuestions), [numQuestions])

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setDragActive(false)
    const f = e.dataTransfer.files[0]
    if (f) setFile(f)
  }, [])

  const onDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setDragActive(true)
  }, [])

  const onDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setDragActive(false)
  }, [])

  const handleUploadAndProcess = async () => {
    if (!file) return
    setError('')
    setModalError(null)
    setLectureId(null)
    setResultByDifficulty(null)
    setUploading(true)

    const fileType = getFileType(file.name)

    let uploadSucceeded = false
    try {
      setModalStep('upload')
      const formData = new FormData()
      formData.append('file', file)
      const res = await apiFormData('/lecture/upload', formData) as { lecture_id: string }
      const id = res.lecture_id
      setLectureId(id)
      uploadSucceeded = true

      setModalStep('mcq')
      const processRes = await api<{
        status: string
        mcq_count?: number
        error?: string
        mcq_by_difficulty?: { easy: number; medium: number; hard: number }
      }>(`/lecture/process/${id}`, {
        method: 'POST',
        body: JSON.stringify({ num_questions: numQuestions }),
      })

      if (processRes.status === 'processed') {
        setModalStep('done')
        setMcqCount(processRes.mcq_count ?? 0)
        if (processRes.mcq_by_difficulty) {
          setResultByDifficulty(processRes.mcq_by_difficulty)
        }
      } else {
        setModalStep('error')
        setModalError(processRes.error || 'Processing failed')
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Upload or processing failed. Check that MongoDB is running and all dependencies are installed.'
      if (!uploadSucceeded) {
        setError(msg)
        setModalStep(null)
      } else {
        setModalStep('error')
        setModalError(msg)
      }
    } finally {
      setUploading(false)
    }
  }

  const handleModalClose = () => {
    if (modalStep === 'done' && lectureId) {
      navigate(`/lectures/${lectureId}`)
    }
    setModalStep(null)
    setModalError(null)
  }

  return (
    <div className="space-y-8 animate-fade-in">
      <div>
        <h1 className="text-3xl font-bold text-slate-900 tracking-tight">Upload Lecture</h1>
        <p className="text-slate-500 mt-1">Transform lectures into Bloom&apos;s Taxonomy-aligned MCQs</p>
      </div>

      <div
        onDrop={onDrop}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        className={`card border-2 border-dashed transition-all duration-200 cursor-pointer ${
          dragActive ? 'border-primary-400 bg-primary-50/30' : 'border-slate-200 hover:border-primary-300 hover:bg-slate-50/50'
        }`}
      >
        <input
          type="file"
          accept={ACCEPT}
          onChange={(e) => setFile(e.target.files?.[0] || null)}
          className="hidden"
          id="file-upload"
        />
        <label htmlFor="file-upload" className="flex flex-col items-center justify-center py-16 cursor-pointer">
          <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-primary-100 to-primary-50 flex items-center justify-center mb-5">
            <UploadIcon className="w-10 h-10 text-primary-600" />
          </div>
          <p className="text-lg font-semibold text-slate-700 mb-2">
            {file ? (
              <span className="flex items-center gap-2">
                <FileUp className="w-5 h-5 text-primary-500" />
                {file.name}
              </span>
            ) : (
              'Drag and drop or click to select'
            )}
          </p>
          <p className="text-sm text-slate-500">
            MP3, WAV, MP4, PDF, DOCX, PPTX, TXT, PNG, JPG
          </p>
        </label>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-50 border border-red-100 text-red-700 text-sm">
          {error}
        </div>
      )}

      <div className="card p-6 space-y-4">
        <div className="flex items-center justify-between gap-4 flex-wrap">
          <div>
            <p className="font-semibold text-slate-800">Number of MCQs</p>
            <p className="text-sm text-slate-500 mt-0.5">
              Total {numQuestions} — Easy {questionPlan.easy}, Medium {questionPlan.medium}, Hard{' '}
              {questionPlan.hard}
            </p>
          </div>
          <span className="text-2xl font-bold text-primary-600 tabular-nums">{numQuestions}</span>
        </div>
        <input
          type="range"
          min={10}
          max={30}
          step={1}
          value={numQuestions}
          onChange={(e) => setNumQuestions(Number(e.target.value))}
          className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-primary-600"
          aria-label="Number of questions"
        />
        <div className="flex justify-between text-xs text-slate-400">
          <span>10</span>
          <span>30</span>
        </div>
      </div>

      <div className="flex gap-3">
        <button
          onClick={handleUploadAndProcess}
          disabled={!file || uploading}
          className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed inline-flex items-center gap-2"
        >
          <Sparkles className="w-5 h-5" />
          {uploading ? 'Processing...' : 'Upload & Process'}
        </button>
      </div>

      <ProcessingModal
        isOpen={modalStep !== null}
        step={modalStep ?? 'upload'}
        filename={file?.name}
        fileType={file ? getFileType(file.name) : undefined}
        error={modalError ?? undefined}
        mcqCount={mcqCount}
        requestedTotal={numQuestions}
        questionPlan={questionPlan}
        resultByDifficulty={resultByDifficulty ?? undefined}
        onClose={(modalStep === 'done' || modalStep === 'error') ? handleModalClose : undefined}
      />
    </div>
  )
}
