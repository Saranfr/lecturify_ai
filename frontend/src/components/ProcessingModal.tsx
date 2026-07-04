import { Loader2, CheckCircle, XCircle, FileVideo, FileAudio, FileText, Image } from 'lucide-react'

export type ProcessingStep = 'upload' | 'transcribe' | 'extract' | 'mcq' | 'done' | 'error'

interface QuestionPlan {
  easy: number
  medium: number
  hard: number
}

interface ProcessingModalProps {
  isOpen: boolean
  onClose?: () => void
  step: ProcessingStep
  filename?: string
  fileType?: 'video' | 'audio' | 'document' | 'image'
  error?: string
  mcqCount?: number
  /** User-selected total from slider (10–30) */
  requestedTotal?: number
  /** Target split for this run (matches backend) */
  questionPlan?: QuestionPlan
  /** Actual counts returned from API after generation */
  resultByDifficulty?: QuestionPlan
}

function getStepLabel(step: ProcessingStep, fileType?: 'video' | 'audio' | 'document' | 'image'): string {
  switch (step) {
    case 'upload':
      return 'Uploading file...'
    case 'transcribe':
      return fileType === 'video' ? 'Transcribing video...' : 'Transcribing audio...'
    case 'extract':
      if (fileType === 'image') return 'Extracting text with OCR...'
      return 'Extracting text from document...'
    case 'mcq':
      return 'Generating MCQs...'
    case 'done':
      return 'Processing complete!'
    case 'error':
      return 'Processing failed'
    default:
      return 'Processing...'
  }
}

function getStepDescription(step: ProcessingStep, fileType?: 'video' | 'audio' | 'document' | 'image'): string {
  switch (step) {
    case 'upload':
      return 'Please wait while your file uploads.'
    case 'transcribe':
      return 'Extracting speech from your media. This may take a minute for longer files.'
    case 'extract':
      if (fileType === 'image') return 'Running OCR to read text from the image.'
      return 'Reading PDF, DOCX, PPTX, or TXT content.'
    case 'mcq':
      return 'Analyzing your file and generating Bloom-aligned MCQs. This may take a minute.'
    default:
      return ''
  }
}

function getFileIcon(fileType?: 'video' | 'audio' | 'document' | 'image') {
  switch (fileType) {
    case 'video':
      return FileVideo
    case 'audio':
      return FileAudio
    case 'image':
      return Image
    case 'document':
    default:
      return FileText
  }
}

function DifficultyBreakdown({
  title,
  total,
  plan,
}: {
  title: string
  total: number
  plan: QuestionPlan
}) {
  return (
    <div className="w-full mt-4 rounded-xl border border-slate-200 bg-slate-50/80 p-4 text-left">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500 mb-2">{title}</p>
      <p className="text-sm text-slate-700 mb-3">
        <span className="font-semibold text-slate-900">{total}</span> total
      </p>
      <div className="grid grid-cols-3 gap-2 text-center text-sm">
        <div className="rounded-lg bg-emerald-50 border border-emerald-100 py-2">
          <div className="text-xs text-emerald-700 font-medium">Easy</div>
          <div className="text-lg font-bold text-emerald-800 tabular-nums">{plan.easy}</div>
        </div>
        <div className="rounded-lg bg-amber-50 border border-amber-100 py-2">
          <div className="text-xs text-amber-800 font-medium">Medium</div>
          <div className="text-lg font-bold text-amber-900 tabular-nums">{plan.medium}</div>
        </div>
        <div className="rounded-lg bg-rose-50 border border-rose-100 py-2">
          <div className="text-xs text-rose-800 font-medium">Hard</div>
          <div className="text-lg font-bold text-rose-900 tabular-nums">{plan.hard}</div>
        </div>
      </div>
    </div>
  )
}

export default function ProcessingModal({
  isOpen,
  onClose,
  step,
  filename,
  fileType,
  error,
  mcqCount,
  requestedTotal,
  questionPlan,
  resultByDifficulty,
}: ProcessingModalProps) {
  if (!isOpen) return null

  const Icon = getFileIcon(fileType)
  const canDismiss = step === 'done' || step === 'error'
  const processingSteps = ['upload', 'transcribe', 'extract', 'mcq'] as const
  const currentOrder = processingSteps.indexOf(step as typeof processingSteps[number])
  const showProgress = processingSteps.includes(step as typeof processingSteps[number])

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div
        className={`absolute inset-0 bg-slate-900/50 backdrop-blur-sm transition-opacity ${
          canDismiss ? 'cursor-pointer' : 'cursor-not-allowed'
        }`}
        onClick={canDismiss ? onClose : undefined}
        aria-hidden="true"
      />
      <div
        className="relative bg-white rounded-2xl shadow-xl p-8 max-w-md w-full mx-4 border border-slate-200/80 animate-slide-up"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex flex-col items-center text-center">
          <div className="mb-4 p-3 bg-primary-50 rounded-full">
            <Icon className="w-10 h-10 text-primary-600" />
          </div>
          {filename && (
            <p className="text-sm text-slate-500 mb-2 truncate w-full">{filename}</p>
          )}
          {step === 'error' ? (
            <>
              <div className="p-3 bg-red-50 rounded-full mb-4">
                <XCircle className="w-12 h-12 text-red-500" />
              </div>
              <h3 className="text-lg font-semibold text-slate-900 mb-2">Processing failed</h3>
              <p className="text-sm text-slate-600 mb-6">{error || 'An unexpected error occurred'}</p>
            </>
          ) : step === 'done' ? (
            <>
              <div className="p-3 bg-emerald-50 rounded-full mb-4">
                <CheckCircle className="w-12 h-12 text-emerald-500" />
              </div>
              <h3 className="text-lg font-semibold text-slate-900 mb-2">Processing complete!</h3>
              {mcqCount != null && (
                <p className="text-sm text-slate-600">
                  Generated {mcqCount} MCQ{mcqCount !== 1 ? 's' : ''}
                </p>
              )}
              {resultByDifficulty != null && (
                <DifficultyBreakdown
                  title="Questions by difficulty level"
                  total={
                    mcqCount ??
                    resultByDifficulty.easy +
                      resultByDifficulty.medium +
                      resultByDifficulty.hard
                  }
                  plan={resultByDifficulty}
                />
              )}
            </>
          ) : (
            <>
              <div className="p-3 bg-primary-50 rounded-full mb-4">
                <Loader2 className="w-12 h-12 text-primary-600 animate-spin" />
              </div>
              <h3 className="text-lg font-semibold text-slate-900 mb-2">
                {getStepLabel(step, fileType)}
              </h3>
              <p className="text-sm text-slate-500">
                {getStepDescription(step, fileType)}
              </p>
              {questionPlan && requestedTotal != null && step === 'mcq' && (
                <DifficultyBreakdown
                  title="Target for this run"
                  total={requestedTotal}
                  plan={questionPlan}
                />
              )}
            </>
          )}
          {(step === 'done' || step === 'error') && onClose && (
            <button
              onClick={onClose}
              className={`mt-6 px-6 py-2.5 rounded-xl font-medium transition-all ${
                step === 'error'
                  ? 'btn-secondary'
                  : 'btn-primary'
              }`}
            >
              {step === 'error' ? 'Close' : 'View Lecture'}
            </button>
          )}
        </div>
        {showProgress && (
          <div className="mt-6 flex justify-center gap-2">
            {processingSteps.map((s, i) => {
              const isActive = currentOrder >= i
              return (
                <div
                  key={s}
                  className={`h-1.5 rounded-full transition-colors ${
                    isActive ? 'bg-primary-600 w-6' : 'bg-slate-200 w-2'
                  }`}
                />
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
