# Lecturify AI – Smart Lecture to MCQ Generator with Bloom's Taxonomy Alignment

A full-stack AI platform that converts lecture content (audio, video, PDF, DOCX, images, or text) into structured MCQs categorized by Bloom's Taxonomy (Remember, Understand, Apply), with dashboards, analytics, and export.

## Architecture (Three-Tier Modular)

1. **Presentation Layer** – React + Vite + Tailwind (frontend)
2. **Application Layer** – Flask REST API, workflow engine
3. **Data & AI Layer** – Whisper (STT), OCR, NLP, MCQ generation, Bloom classifier

All data is stored **locally** – no AWS or cloud storage.

---

## Prerequisites

- **Python 3.9+**
- **Node.js 18+** and npm
- **MongoDB** (local – default `mongodb://localhost:27017/`)
- **Tesseract OCR** (for image OCR – [install Tesseract](https://github.com/tesseract-ocr/tesseract))
- **FFmpeg** – bundled via `imageio-ffmpeg` (install: `pip install imageio-ffmpeg`). Or install [FFmpeg](https://ffmpeg.org/download.html) system-wide.

---

## Quick Start (VS Code)

### 1. Open Project

```bash
# Open the lecturify_ai folder in VS Code
code lecturify_ai
```

### 2. Backend Setup

```bash
# Create virtual environment (recommended)
python -m venv venv
.\venv\Scripts\activate   # Windows
# source venv/bin/activate   # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Download spaCy model (for NLP)
python -m spacy download en_core_web_sm

# Download NLTK data
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"
```

### 3. Datasets (Optional – for training)

Place datasets in `lecturify_ai/datasets/` (or use existing ones in `Project/datasets/datasets/`). Supported formats:

- **MCQ training**: CSV (SciQ format), JSON (SQuAD), RACE
- **Bloom training**: JSON with `question` and `bloom_level` fields

The system auto-detects datasets at startup. If none exist, it runs in **inference-only** mode.

### 4. Train Models (Optional)

```bash
# From lecturify_ai root
python backend/train_models.py
```

Trained models are saved to `backend/models/`.

### 5. Start Backend (Video/Audio Support)

**Windows (recommended):** Use `start_backend.bat` – it activates venv, installs video deps, and starts the server:

```bash
.\start_backend.bat
```

**Or manually:** Activate venv, install deps, then run:

```bash
.\venv\Scripts\activate
pip install imageio-ffmpeg openai-whisper moviepy av
python run_backend.py
```

If video upload fails, check `http://localhost:5000/api/diagnostic/video` for dependency status.

### 6. Start MongoDB

Ensure MongoDB is running locally:

```bash
# Windows (if installed as service)
net start MongoDB

# Or start mongod manually
mongod
```

Backend runs at **http://localhost:5000**.

### 7. Frontend Setup & Run

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at **http://localhost:5173**.

### 8. First Use

1. Open **http://localhost:5173**
2. Click **Register** and create an account (e.g. Instructor role)
3. **Upload** a lecture file (PDF, DOCX, TXT, or audio/video)
4. Open the lecture and click **Process & Generate MCQs**
5. Review, approve/reject MCQs
6. Export to PDF, JSON, or CSV

---

## Project Structure

```
lecturify_ai/
├── frontend/               # React (Vite) + Tailwind
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── api/
│   │   └── hooks/
│   └── package.json
├── backend/
│   ├── app.py              # Flask app
│   ├── config.py           # Config & paths
│   ├── train_models.py     # Training pipeline
│   ├── routes/             # API routes
│   │   ├── auth_routes.py
│   │   ├── lecture_routes.py
│   │   ├── mcq_routes.py
│   │   ├── export_routes.py
│   │   └── analytics_routes.py
│   ├── services/
│   │   ├── dataset_loader.py
│   │   ├── stt_module.py
│   │   ├── ocr_module.py
│   │   ├── document_parser.py
│   │   ├── nlp_processing.py
│   │   ├── bloom_classifier.py
│   │   ├── mcq_generator.py
│   │   └── logging_service.py
│   └── models/             # Trained models
├── storage/
│   ├── uploaded_files/     # Uploaded lectures
│   └── processed_outputs/  # Exported MCQs
├── datasets/               # Training data
├── run_backend.py
├── requirements.txt
└── README.md
```

---

## API Overview

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/register` | POST | Register user |
| `/api/auth/login` | POST | Login, get JWT |
| `/api/lecture/upload` | POST | Upload lecture file |
| `/api/lecture/process/<id>` | POST | Process lecture, generate MCQs |
| `/api/lecture/lectures` | GET | List lectures |
| `/api/lecture/lectures/<id>` | GET | Get lecture + MCQs |
| `/api/export/json/<id>` | GET | Export MCQs as JSON (requires auth) |
| `/api/export/csv/<id>` | GET | Export MCQs as CSV (requires auth) |
| `/api/export/pdf/<id>` | GET | Export MCQs as PDF (requires auth) |
| `/api/analytics/overview` | GET | Dashboard analytics |
| `/api/analytics/logs` | GET | Audit logs |

---

## MongoDB Collections

- **users** – email, password (bcrypt), role, name
- **lectures** – filename, stored_path, file_type, status, transcript, concepts, mcqs
- **logs** – event_type, user_id, lecture_id, timestamp, details

---

## Configuration

Edit `backend/config.py`:

- `DATASET_PATH` – path to datasets folder
- `MONGODB_URI` – MongoDB connection
- `WHISPER_MODEL` – `tiny` / `base` / `small` / `medium` / `large`
- `WHISPER_LANGUAGE` – `None` for auto-detect (multilingual)

---

## Example Generated MCQ

```json
{
  "question": "Fill in the blank: The stored food in a seed is called ______.",
  "options": ["endosperm", "larval", "membrane", "pollin"],
  "correct_answer": "endosperm",
  "explanation": "The stored food in a seed is called endosperm. It nourishes the embryo...",
  "bloom_level": "Remember"
}
```

---

## MongoDB Setup (localhost:27017)

Lecturify AI expects MongoDB at **mongodb://localhost:27017/**.

1. **Start MongoDB** before the backend:
   - Windows (service): `net start MongoDB`
   - Or run `mongod` manually from your MongoDB install folder

2. **No manual DB setup needed** – the app creates the `lecturify_ai` database and collections on first use.

3. See **[MONGODB_SETUP.md](MONGODB_SETUP.md)** for more details.

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| MongoDB connection error | Ensure MongoDB is running on port 27017 |
| Whisper not found | `pip install openai-whisper` |
| pytesseract error | Install Tesseract OCR and add to PATH |
| FFmpeg not found | Install FFmpeg for video processing |
| spaCy model missing | `python -m spacy download en_core_web_sm` |
| CORS errors | Frontend proxy in `vite.config.ts` points to backend at 5000 |

---

## Bonus Features

- Multilingual Whisper transcription (auto-detect)
- Adaptive difficulty (Bloom-based classification)
- Admin analytics dashboard
- Personalized quiz recommendations (Bloom distribution in dashboard)

---

## License

MIT
