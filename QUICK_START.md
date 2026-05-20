# ⚡ Quick Start — Native Setup (No Docker)

## 🎯 TL;DR — Copy-Paste 5 Minute Setup

### Windows (PowerShell)
```powershell
cd C:\Rares\Carrer_Path\careerpath-ai

# FIRST TIME ONLY
powershell -NoProfile -ExecutionPolicy Bypass -File setup-native.ps1 -Action install

# EVERY DAY
powershell -NoProfile -ExecutionPolicy Bypass -File setup-native.ps1 -Action start

# CHECK STATUS
powershell -NoProfile -ExecutionPolicy Bypass -File setup-native.ps1 -Action status

# STOP
powershell -NoProfile -ExecutionPolicy Bypass -File setup-native.ps1 -Action stop
```

### Linux / WSL2 (Bash)
```bash
cd /path/to/careerpath-ai

# FIRST TIME ONLY
chmod +x setup-native.sh
./setup-native.sh install

# EVERY DAY
./setup-native.sh start

# CHECK STATUS
./setup-native.sh status

# STOP
./setup-native.sh stop
```

---

## 📋 PRE-FLIGHT CHECKLIST

Before running setup, verify you have these installed:

### Windows
- [ ] Node.js 18+ → `node --version`
- [ ] Python 3.11+ → `python --version`
- [ ] PostgreSQL 15+ → `psql --version`
- [ ] Redis → `redis-cli --version`
- [ ] Git → `git --version`

### Linux/WSL2
```bash
node --version && python3 --version && psql --version && redis-cli --version && git --version
```

**Install missing?** See `SETUP_FARA_DOCKER.md` for download links.

---

## 🚀 What The Script Does

### `install` Action (First time)
✅ Checks all prerequisites  
✅ Downloads & builds 13 Node packages  
✅ Creates Python virtual environments  
✅ Installs all Python dependencies  

**Time:** ~5-10 min (first time) | ~30s (subsequent)

### `start` Action (Every day)
✅ Starts PostgreSQL  
✅ Starts Redis  
✅ Opens API Gateway in new terminal (npm)  
✅ Opens Frontend in new terminal (npm)  
✅ Opens 3 AI Agents in new terminals (Python)  

**Time:** ~10 seconds

### `status` Action
✅ Checks all 7 services  
✅ Shows which are UP / DOWN  

### `stop` Action
✅ Gracefully stops all services  

---

## 📊 Services Running After `start`

| Service | PID | Port | Terminal | Status |
|---------|-----|------|----------|--------|
| API Gateway | npm | 8000 | New | Running |
| Frontend | npm | 3000 | New | Running |
| CV Analyzer | python | 8002 | New | Running |
| HR Interview | python | 8003 | New | Running |
| Orchestrator | python | 8005 | New | Running |
| PostgreSQL | service | 5432 | System | Running |
| Redis | redis-server | 6379 | System | Running |

---

## 🌐 Access Points (After Start)

Open in browser:

```
Frontend            → http://localhost:3000
API Gateway Health  → http://localhost:8000/health
CV Analyzer API     → http://localhost:8002/docs
HR Interview API    → http://localhost:8003/docs
Orchestrator API    → http://localhost:8005/docs
```

---

## ⚠️ Troubleshooting

### Error: "Module not found" (Python)
```powershell
# Verify virtual env is active
.\.venv\Scripts\Activate.ps1

# Reinstall
pip install -r requirements.txt --force-reinstall
```

### Error: "Port 8000 in use"
```powershell
# Find process on port 8000
netstat -ano | findstr :8000

# Kill it
taskkill /PID 12345 /F
```

### Error: "Cannot connect to PostgreSQL"
```powershell
# Start service
Start-Service postgresql-x64-15

# Verify
psql -U postgres -c "SELECT 1;"
```

### Error: "Redis connection refused"
```powershell
# Start Redis
redis-server

# In another terminal, verify
redis-cli ping   # Must return PONG
```

### API Gateway won't start
```powershell
cd api-gateway
npm run build
npm run start:prod
```

### Frontend won't load
```powershell
cd frontend
rm -r .next node_modules
npm install
npm run dev
```

---

## 🔄 Daily Workflow

### Morning
```bash
# Windows PowerShell
powershell -File setup-native.ps1 -Action start

# Linux/WSL2
./setup-native.sh start

# Open http://localhost:3000 in browser
```

### During Development
Each terminal auto-reloads on code changes:
- `npm run start:dev` watches for .ts changes
- `npm run dev` watches for .js/.jsx changes
- `uvicorn --reload` watches for .py changes

### Evening
```bash
# Windows PowerShell
powershell -File setup-native.ps1 -Action stop

# Linux/WSL2
./setup-native.sh stop
```

---

## 🧪 Manual Testing (No Kafka)

Since Kafka/Redpanda requires extra setup, test agents directly:

### Test CV Analyzer
```bash
curl -X POST http://localhost:8002/analyze \
  -H "Content-Type: application/json" \
  -d '{"cv_text": "I am a Python developer with 5 years experience"}'
```

### Test HR Interview
```bash
# Use browser WebSocket at http://localhost:8003/docs
# Or use wscat: npm install -g wscat
wscat -c ws://localhost:8003/interview/hr/session-123
```

---

## 📈 Next Steps

1. ✅ Run `setup-native.ps1 install` (first time only)
2. ✅ Fill `.env` with API keys (ANTHROPIC_API_KEY, etc.)
3. ✅ Run `setup-native.ps1 start`
4. ✅ Open http://localhost:3000
5. 🚀 Build features!

---

## 💾 Script Files

- **`setup-native.ps1`** — Windows PowerShell automation
- **`setup-native.sh`** — Linux/WSL2 Bash automation
- **`SETUP_FARA_DOCKER.md`** — Detailed manual setup guide

---

## 📞 Need Help?

1. Check terminal output (each service has its own terminal)
2. Run `setup-native.ps1 -Action status` to see what's down
3. Refer to `SETUP_FARA_DOCKER.md` for manual steps
4. Check service logs in corresponding terminal

---

**🎉 Happy coding! 🚀**

