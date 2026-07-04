import { useState, useEffect } from 'react'
import { useParams, useSearchParams, Link, useNavigate } from 'react-router-dom'
import { api, downloadFile } from '../api/client'
import { useAuth } from '../hooks/useAuth'
import { Play, Download, ChevronDown, ChevronUp, Trash2, FileDown } from 'lucide-react'
import ProcessingModal, { type ProcessingStep } from '../components/ProcessingModal'

interface MCQ {
  question: string
  options: string[]
  correct_answer: string
  explanation: string
  bloom_level: string
  difficulty?: string
}

interface Lecture {
  id: string
  filename: string
  status: string
  file_type?: string
  error?: string
  transcript?: string
  mcqs?: MCQ[]
}

function getFileTypeFromLecture(lecture: Lecture | null): 'video' | 'audio' | 'document' | 'image' {
  if (!lecture?.file_type) return 'document'
  const t = lecture.file_type.toLowerCase()
  if (t === 'video') return 'video'
  if (t === 'audio') return 'audio'
  if (t === 'image') return 'image'
  return 'document'
}

const BLOOM_COLORS: Record<string, string> = {
  Remember: 'bg-indigo-100 text-indigo-800',
  Understand: 'bg-purple-100 text-purple-800',
  Apply: 'bg-pink-100 text-pink-800',
  Analyze: 'bg-teal-100 text-teal-800',
}

const DIFFICULTY_COLORS: Record<string, string> = {
  Easy: 'bg-emerald-100 text-emerald-800',
  Medium: 'bg-amber-100 text-amber-800',
  Hard: 'bg-rose-100 text-rose-800',
}

export default function LectureDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { user } = useAuth()
  const isTeacherOrAdmin = user?.role === 'Instructor' || user?.role === 'Admin'
  const [searchParams] = useSearchParams()
  const shouldProcess = searchParams.get('process') === '1'

  const [lecture, setLecture] = useState<Lecture | null>(null)
  const [deleting, setDeleting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [processing, setProcessing] = useState(false)
  const [processingError, setProcessingError] = useState<string | null>(null)
  const [numQuestions, setNumQuestions] = useState(12)
  const [selectedAnswers, setSelectedAnswers] = useState<Record<number, string>>({})
  const [answersRevealed, setAnswersRevealed] = useState(false)
  const [currentLevel, setCurrentLevel] = useState<'All' | 'Easy' | 'Medium' | 'Hard'>('Easy')

  useEffect(() => {
    if (!id) return
    setError(null)
    api<Lecture>(`/lecture/lectures/${id}`)
      .then((l) => { setLecture(l); setError(null) })
      .catch((e) => { setLecture(null); setError(e instanceof Error ? e.message : "Failed to load lecture") })
  }, [id])

  useEffect(() => {
    if (!id || !shouldProcess || !lecture || lecture.status === 'processed') return
    setProcessing(true)
    setError(null)
    setProcessingError(null)
    api<{ status: string; mcq_count?: number }>(`/lecture/process/${id}`, {
      method: 'POST',
      body: JSON.stringify({ num_questions: numQuestions }),
    })
      .then((res) => api<Lecture>(`/lecture/lectures/${id}`))
      .then((l) => { setLecture(l); setError(null); setProcessingError(null) })
      .catch((e) => {
        const msg = e instanceof Error ? e.message : "Processing failed"
        setError(msg)
        setProcessingError(msg)
      })
      .finally(() => setProcessing(false))
  }, [id, shouldProcess, lecture?.status, numQuestions])

  const levelOrder: ('All' | 'Easy' | 'Medium' | 'Hard')[] = ['Easy', 'Medium', 'Hard', 'All']
  const currentLevelIdx = levelOrder.indexOf(currentLevel)
  const nextLevel = currentLevelIdx < levelOrder.length - 1 ? levelOrder[currentLevelIdx + 1] : null

  const filteredMcqs = lecture?.mcqs?.filter((m) => currentLevel === 'All' || m.difficulty === currentLevel) ?? []

  const handleDelete = async () => {
    if (!id) return
    if (!confirm('Delete this lecture? This cannot be undone.')) return
    setDeleting(true)
    try {
      await api(`/lecture/lectures/${id}`, { method: 'DELETE' })
      navigate('/lectures')
    } catch {
      alert('Failed to delete lecture')
    } finally {
      setDeleting(false)
    }
  }

  if (!lecture && !error) return <div className="text-center py-16 animate-pulse text-slate-500">Loading lecture...</div>
  if (error && !lecture) return (
    <div className="card text-center py-16">
      <p className="text-red-600 mb-4">{error}</p>
      <Link to="/lectures" className="text-primary-600 hover:underline">← Back to Lectures</Link>
    </div>
  )

  return (
    <div className="space-y-8 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <Link to="/lectures" className="text-primary-600 hover:underline text-sm mb-2 block">← Back to Lectures</Link>
          <h1 className="text-3xl font-bold text-slate-900">{lecture.filename}</h1>
          <p className="text-slate-600 mt-1">Status: {lecture.status}</p>
        </div>
        {isTeacherOrAdmin && (
          <button
            onClick={handleDelete}
            disabled={deleting}
            className="p-2 rounded-lg text-slate-400 hover:text-red-600 hover:bg-red-50 transition-colors"
            title="Delete lecture"
          >
            <Trash2 className="w-5 h-5" />
          </button>
        )}
        {isTeacherOrAdmin && (lecture.status === 'uploaded' || lecture.status === 'failed') && (
          <div className="flex items-center gap-4">
            <select
              value={numQuestions}
              onChange={(e) => setNumQuestions(Number(e.target.value))}
              className="border rounded-lg px-3 py-2"
            >
              {[9, 12, 15, 18].map((n) => (
                <option key={n} value={n}>{n} MCQs ({n / 3} per level)</option>
              ))}
            </select>
            <Link
              to={`/lectures/${id}?process=1`}
              className="btn-primary flex items-center gap-2"
            >
              <Play className="w-5 h-5" />
              {processing ? 'Processing...' : lecture.status === 'failed' ? 'Retry Processing' : 'Process & Generate MCQs'}
            </Link>
          </div>
        )}
      </div>

      {lecture.status === 'failed' && lecture.error && (
        <div className="card border-red-200 bg-red-50">
          <h2 className="font-semibold mb-2 text-red-800">Processing Error</h2>
          <p className="text-red-700 text-sm">{lecture.error}</p>
          <p className="text-red-600 text-xs mt-2">Fix: In <code className="bg-red-100 px-1 rounded">lecturify_ai</code> folder run <code className="bg-red-100 px-1 rounded">start_backend.bat</code> (or activate venv first). Check <code className="bg-red-100 px-1 rounded">/api/diagnostic/video</code> for details.</p>
        </div>
      )}

      {lecture.mcqs && lecture.mcqs.length > 0 && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-bold">Generated MCQs ({lecture.mcqs.length})</h2>
            {isTeacherOrAdmin && (
            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => downloadFile(`/export/json/${id}`, `lecturify_${id}.json`)}
                className="btn-secondary flex items-center gap-2"
              >
                <Download className="w-4 h-4" />
                JSON
              </button>
              <button
                onClick={() => downloadFile(`/export/csv/${id}`, `lecturify_${id}.csv`)}
                className="btn-secondary flex items-center gap-2"
              >
                <Download className="w-4 h-4" />
                CSV
              </button>
              <button
                onClick={() => downloadFile(`/export/pdf/${id}`, `lecturify_${id}.pdf`)}
                className="btn-secondary flex items-center gap-2"
              >
                <Download className="w-4 h-4" />
                PDF
              </button>
              <button
                onClick={() => downloadFile(`/export/lms/${id}`, `lecturify_${id}_moodle.xml`)}
                className="btn-secondary flex items-center gap-2"
                title="Moodle XML (LMS-ready)"
              >
                <FileDown className="w-4 h-4" />
                LMS
              </button>
            </div>
            )}
          </div>

          {/* Level tabs and Next Level */}
          <div className="flex flex-wrap items-center gap-2 mb-4">
            {(['Easy', 'Medium', 'Hard', 'All'] as const).map((level) => (
              <button
                key={level}
                onClick={() => { setCurrentLevel(level); setAnswersRevealed(false); setSelectedAnswers({}) }}
                className={`px-4 py-2 rounded-xl font-medium transition-colors ${
                  currentLevel === level
                    ? level === 'Easy'
                      ? 'bg-emerald-100 text-emerald-800'
                      : level === 'Medium'
                        ? 'bg-amber-100 text-amber-800'
                        : level === 'Hard'
                          ? 'bg-rose-100 text-rose-800'
                          : 'bg-slate-200 text-slate-800'
                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                }`}
              >
                {level}
                {level !== 'All' && (
                  <span className="ml-1 text-xs opacity-75">
                    ({lecture.mcqs.filter((m) => m.difficulty === level).length})
                  </span>
                )}
              </button>
            ))}
            {answersRevealed && nextLevel && (
              <button
                onClick={() => { setCurrentLevel(nextLevel); setAnswersRevealed(false); setSelectedAnswers({}) }}
                className="btn-primary flex items-center gap-2 ml-auto"
              >
                Next: {nextLevel} →
              </button>
            )}
          </div>

          {/* Quiz mode: answer first, then reveal */}
          <div className="flex items-center justify-between mb-4">
            <p className="text-sm text-slate-600">
              {!answersRevealed
                ? `Select your answers for ${currentLevel} MCQs, then click "Show Answers".`
                : `Score: ${filteredMcqs.filter((mcq) => selectedAnswers[lecture.mcqs!.indexOf(mcq)] === mcq.correct_answer).length} / ${filteredMcqs.length} correct`}
            </p>
            {!answersRevealed ? (
              <button
                onClick={() => setAnswersRevealed(true)}
                className="btn-primary flex items-center gap-2"
              >
                <ChevronDown className="w-5 h-5" />
                Show Answers
              </button>
            ) : (
              <button
                onClick={() => { setAnswersRevealed(false); setSelectedAnswers({}) }}
                className="btn-secondary flex items-center gap-2"
              >
                <ChevronUp className="w-5 h-5" />
                Retry Quiz
              </button>
            )}
          </div>

          {filteredMcqs.length === 0 ? (
            <div className="card text-center py-8 text-slate-600">
              No {currentLevel} MCQs in this batch. Try another level or &quot;All&quot;.
            </div>
          ) : (
          <div className="space-y-6">
            {filteredMcqs.map((mcq, localIdx) => {
              const idx = lecture.mcqs!.indexOf(mcq)
              const userAnswer = selectedAnswers[idx]
              const isCorrect = userAnswer === mcq.correct_answer
              const showResult = answersRevealed

              return (
                <div
                  key={idx}
                  className={`card ${
                    showResult ? (isCorrect ? 'border-l-4 border-green-500' : 'border-l-4 border-red-500') : ''
                  }`}
                >
                          <div className="mb-3">
                    <p className="font-medium mb-2">Q{localIdx + 1}. {mcq.question}</p>
                    <div className="flex gap-2 flex-wrap">
                      <span className={`inline-block px-2 py-1 rounded text-xs ${BLOOM_COLORS[mcq.bloom_level] || 'bg-slate-100'}`}>
                        {mcq.bloom_level}
                      </span>
                      {mcq.difficulty && (
                        <span className={`inline-block px-2 py-1 rounded text-xs ${DIFFICULTY_COLORS[mcq.difficulty] || 'bg-slate-100'}`}>
                          {mcq.difficulty}
                        </span>
                      )}
                    </div>
                  </div>
                  <ul className="space-y-2 mb-3">
                    {mcq.options?.map((opt, i) => {
                      const letter = String.fromCharCode(65 + i)
                      const isSelected = userAnswer === opt
                      const isCorrectOpt = opt === mcq.correct_answer
                      const showAsCorrect = showResult && isCorrectOpt
                      const showAsWrong = showResult && isSelected && !isCorrect

                      return (
                        <li key={i}>
                          <label
                            className={`flex items-center gap-2 p-2 rounded-lg cursor-pointer transition-colors ${
                              !showResult
                                ? 'hover:bg-slate-50'
                                : showAsCorrect
                                  ? 'bg-green-50 text-green-800'
                                  : showAsWrong
                                    ? 'bg-red-50 text-red-800'
                                    : ''
                            }`}
                          >
                            <input
                              type="radio"
                              name={`mcq-${idx}-${localIdx}`}
                              checked={isSelected}
                              onChange={() => !showResult && setSelectedAnswers((s) => ({ ...s, [idx]: opt }))}
                              disabled={showResult}
                              className="w-4 h-4"
                            />
                            <span>
                              {letter}. {opt}
                              {showAsCorrect && <span className="text-green-600 ml-2 font-medium">✓ Correct</span>}
                              {showAsWrong && !showAsCorrect && <span className="text-red-600 ml-2 font-medium">✗ Your answer</span>}
                            </span>
                          </label>
                        </li>
                      )
                    })}
                  </ul>
                  {showResult && mcq.explanation && (
                    <p className="text-sm text-slate-500 border-t pt-2 mt-2">
                      <strong>Explanation:</strong> {mcq.explanation}
                    </p>
                  )}
                </div>
              )
            })}
          </div>
          )}
        </div>
      )}

      {(lecture.status === 'uploaded' || lecture.status === 'failed') && !lecture.mcqs?.length && !processing && (
        <div className="card text-center py-12">
          <p className="text-slate-600 mb-4">
            {lecture.status === 'failed'
              ? 'Processing failed. Fix the issue above and retry.'
              : 'Click &quot;Process & Generate MCQs&quot; to extract text and generate questions.'}
          </p>
          <Link to={`/lectures/${id}?process=1`} className="btn-primary inline-flex items-center gap-2">
            <Play className="w-5 h-5" />
            {lecture.status === 'failed' ? 'Retry Processing' : 'Process Now'}
          </Link>
        </div>
      )}

      <ProcessingModal
        isOpen={processing || !!processingError}
        step={processingError ? 'error' : (lecture && (getFileTypeFromLecture(lecture) === 'document' || getFileTypeFromLecture(lecture) === 'image') ? 'extract' : 'transcribe')}
        filename={lecture?.filename}
        fileType={lecture ? getFileTypeFromLecture(lecture) : undefined}
        error={processingError ?? undefined}
        onClose={processingError ? () => setProcessingError(null) : undefined}
      />
    </div>
  )
}
