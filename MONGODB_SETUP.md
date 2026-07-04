# MongoDB Setup for Lecturify AI

## Your Setup (localhost:27017)

You have MongoDB connected to **localhost:27017**. That is correct for Lecturify AI.

### What Lecturify AI Uses

- **URI:** `mongodb://localhost:27017/`
- **Database:** `lecturify_ai`
- **Collections:**
  - `users` – login credentials
  - `lectures` – uploaded files, transcripts, MCQs
  - `logs` – audit logs

### What You Need to Do

1. **Ensure MongoDB is running** before starting the backend:
   - Windows: `net start MongoDB` (if installed as service)
   - Or start `mongod` manually from your MongoDB install folder

2. **No database creation needed** – Lecturify AI creates the database and collections on first use.

3. **Default user** – The app auto-creates `instructor@lecturify.com` / `Test@123` if no users exist (when login is enabled).

### Verify Connection

```bash
# From project root
python -c "from pymongo import MongoClient; c=MongoClient('mongodb://localhost:27017/'); print('OK' if c.admin.command('ping') else 'Fail')"
```

If you see `OK`, MongoDB is reachable.
