# 🚀 CareerPath AI — Setup FĂRĂ Docker (Native)

> Pornire proiect direct pe mașina ta, fără containere.

---

## 📋 Prerequisites (OBLIGATORIU)

### Windows PowerShell (ți-l ai deja)
```powershell
pwsh --version   # Minimum v5.1
```

### 1. Node.js + npm (pentru Frontend și API Gateway - NestJS)
**Download:** https://nodejs.org (LTS 18+)

Verificare:
```powershell
node --version
npm --version
```

### 2. Python 3.11+ (pentru toți agenții AI și serviciile FastAPI)
**Download:** https://www.python.org/downloads/

Verificare:
```powershell
python --version
pip --version
```

### 3. PostgreSQL 15+ (Database)
**Download:** https://www.postgresql.org/download/windows/

**Setup:**
- Default port: 5432
- Default user: postgres
- Setează password sigur (reține-l!)

Verificare:
```powershell
psql --version
psql -U postgres -c "SELECT version();"
```

### 4. Redis 7+ (Cache + Session Storage)
**Download:** https://github.com/microsoftarchive/redis/releases (Windows native)
SAU instalează din WSL2

Verificare:
```powershell
redis-cli --version
redis-cli ping   # Trebuie sa returneze PONG
```

### 5. Git (version control)
```powershell
git --version
```

---

## 🔧 SETUP PARTE 1: Baza de Infrastructură

### 1.1 Pornire PostgreSQL
```powershell
# Verifica dacă serviciul e instalat
Get-Service postgresql*

# Porneste serviciul
Start-Service postgresql-x64-15   # Sau versiunea ta

# Verifica conexiunea
psql -U postgres -c "SELECT 1"
```

**Crează baza de date:**
```powershell
psql -U postgres -c "CREATE DATABASE careerpath;"
psql -U postgres -c "CREATE USER cp_user WITH PASSWORD 'careerpath_dev123';"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE careerpath TO cp_user;"
```

Verificare:
```powershell
psql -U cp_user -d careerpath -c "SELECT 1;"
```

### 1.2 Pornire Redis
```powershell
# Deschide un terminal nou și porneste Redis server
redis-server

# In alt terminal, verifica conexiunea
redis-cli ping   # Trebuie PONG
```

---

## 📂 SETUP PARTE 2: Configurare Proiect

### 2.1 Clone și navighează
```powershell
cd C:\Rares\Carrer_Path\careerpath-ai
```

### 2.2 Crează fișier .env
```powershell
cp .env.example .env
```

**Editează `C:\Rares\Carrer_Path\careerpath-ai\.env`**
```dotenv
# ═══════════════════════════════════════════════════════════
# REQUIRED — TREBUIE COMPLETATE
# ═══════════════════════════════════════════════════════════

ANTHROPIC_API_KEY=sk-ant-...        # De la https://console.anthropic.com
OPENAI_API_KEY=sk-...               # De la https://platform.openai.com
GOOGLE_API_KEY=...                  # De la https://ai.google.dev
JUDGE0_API_KEY=...                  # (opțional — doar pentru technical-interview)
YOUTUBE_API_KEY=...                 # (opțional — doar pentru learning-path)

# ═══════════════════════════════════════════════════════════
# Database
# ═══════════════════════════════════════════════════════════

POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=cp_user
POSTGRES_PASSWORD=careerpath_dev123
POSTGRES_DB=careerpath

# ═══════════════════════════════════════════════════════════
# Cache
# ═══════════════════════════════════════════════════════════

REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=          # (gol — nu e protejat local)

# ═══════════════════════════════════════════════════════════
# Kafka/Redpanda — SKIP PENTRU NOW (Sau instalează Redpanda)
# ═══════════════════════════════════════════════════════════

KAFKA_BROKERS=localhost:9092
KAFKA_SECURITY_PROTOCOL=PLAINTEXT

# ═══════════════════════════════════════════════════════════
# JWT
# ═══════════════════════════════════════════════════════════

JWT_SECRET=super_secret_key_change_in_prod_12345
JWT_EXPIRY=24h
```

### 2.3 Generează JWT keys
```powershell
# Dacă ai OpenSSL instalat (vine cu Git for Windows)
openssl genrsa -out keys/private.pem 2048
openssl rsa -in keys/private.pem -pubout -out keys/public.pem

# Verificare
dir keys/
```

---

## 🎯 SETUP PARTEA 3: Instalare Dependencies

### 3.1 API Gateway (NestJS)
```powershell
cd C:\Rares\Carrer_Path\careerpath-ai\api-gateway
npm install
npm run build
```

### 3.2 Frontend (Next.js)
```powershell
cd C:\Rares\Carrer_Path\careerpath-ai\frontend
npm install
npm run build
```

### 3.3 Agenți AI (Python)

#### CV Analyzer Agent
```powershell
cd C:\Rares\Carrer_Path\careerpath-ai\services\cv-analyzer-agent
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

#### HR Interview Agent
```powershell
cd C:\Rares\Carrer_Path\careerpath-ai\services\hr-interview-agent
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

#### Agent Orchestrator
```powershell
cd C:\Rares\Carrer_Path\careerpath-ai\services\agent-orchestrator
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

---

## 🚀 PORNIRE SERVICII (Terminal separat pentru fiecare!)

### Terminal 1: PostgreSQL ✅
```powershell
# Serviciu Windows - ar trebui deja activ
Get-Service postgresql*
Start-Service postgresql-x64-15   # Daca nu e active
```

### Terminal 2: Redis ✅
```powershell
redis-server
```

### Terminal 3: API Gateway (NestJS)
```powershell
cd C:\Rares\Carrer_Path\careerpath-ai\api-gateway
npm run start:dev
```

**Aștepți output:**
```
[Nest] 12345  - 05/18/2026, 10:15:32 AM   LOG [NestFactory] Starting Nest application...
[Nest] 12345  - 05/18/2026, 10:15:33 AM   LOG [InstanceLoader] TypeOrmModule dependencies initialized +1234ms
[Nest] 12345  - 05/18/2026, 10:15:34 AM   LOG [NestApplication] Nest application successfully started +789ms
```

Verificare: http://localhost:8000/health → `{"status":"ok"}`

### Terminal 4: Frontend (Next.js)
```powershell
cd C:\Rares\Carrer_Path\careerpath-ai\frontend
npm run dev
```

Verificare: http://localhost:3000 → Ar trebui să vezi interfața

### Terminal 5: CV Analyzer Agent (FastAPI)
```powershell
cd C:\Rares\Carrer_Path\careerpath-ai\services\cv-analyzer-agent
.\.venv\Scripts\Activate.ps1
uvicorn src.main:app --port 8002 --reload
```

Verificare: http://localhost:8002/docs → Documentație Swagger

### Terminal 6: HR Interview Agent (FastAPI)
```powershell
cd C:\Rares\Carrer_Path\careerpath-ai\services\hr-interview-agent
.\.venv\Scripts\Activate.ps1
uvicorn src.main:app --port 8003 --reload
```

Verificare: http://localhost:8003/docs

### Terminal 7: Agent Orchestrator (FastAPI)
```powershell
cd C:\Rares\Carrer_Path\careerpath-ai\services\agent-orchestrator
.\.venv\Scripts\Activate.ps1
python -m uvicorn src.main:app --port 8005 --reload
```

---

## 📊 Verificare Toate Serviciile

| Serviciu | URL | Status |
|---|---|---|
| Frontend | http://localhost:3000 | ✅ |
| API Gateway | http://localhost:8000/health | ✅ |
| CV Analyzer | http://localhost:8002/docs | ✅ |
| HR Interview | http://localhost:8003/docs | ✅ |
| Orchestrator | http://localhost:8005/docs | ✅ |
| PostgreSQL | localhost:5432 | ✅ |
| Redis | localhost:6379 | ✅ |

---

## ⚠️ Probleme Frecvente

### Eroare: "Port 5432 in use"
```powershell
# Găsește procesul pe portul 5432
netstat -ano | findstr :5432

# Omoară procesul (schimba PID-ul)
taskkill /PID 12345 /F

# SAU schimbă portul în .env
POSTGRES_PORT=5433
```

### Eroare: "Cannot connect to Redis"
```powershell
# Verifică dacă Redis e pornit
redis-cli ping   # Trebuie PONG

# Daca nu:
redis-server     # Porneste Redis
```

### Eroare: "ANTHROPIC_API_KEY not found"
```powershell
# Verifica .env
cat .env | grep ANTHROPIC

# Daca nu e acolo, adaugă-l
"ANTHROPIC_API_KEY=sk-ant-..." >> .env
```

### Eroare: "Module not found" (Python)
```powershell
# Verifica ca virtual environment e activat
.\.venv\Scripts\Activate.ps1

# Reinstalează dependencies
pip install -r requirements.txt --force-reinstall
```

### Eroare: "npm: command not found"
```powershell
# Reinitializeaza PATH
$env:PATH = "C:\Program Files\nodejs;$env:PATH"

# Verifica
npm --version
```

---

## 🔄 Workflow Development Zilnic

### Morning Start
```powershell
# Terminal 1: PostgreSQL (ar trebui deja activ)
Get-Service postgresql* | Start-Service

# Terminal 2: Redis
redis-server

# Terminal 3: API Gateway
cd api-gateway; npm run start:dev

# Terminal 4: Frontend
cd frontend; npm run dev

# Terminal 5+: Agenți (pe măsură ce ai nevoie)
cd services/cv-analyzer-agent; .\.venv\Scripts\Activate.ps1; uvicorn src.main:app --reload
```

### Stop All
```powershell
# În fiecare terminal, apasă Ctrl+C

# PostgreSQL (opțional)
Stop-Service postgresql-x64-15
```

---

## 🧪 Testing Fără Kafka (Workaround)

Deoarece Redpanda nu e ușor pe Windows, poti testa fiecare agent **direct**:

### Test CV Analyzer
```powershell
cd services/cv-analyzer-agent
.\.venv\Scripts\Activate.ps1
python -c "
from src.main import analyze_cv
result = analyze_cv('''
I am a Python developer with 3 years experience.
Skills: Python, FastAPI, PostgreSQL, Redis.
''')
print(result)
"
```

### Test HR Interview
```powershell
# Deschide browser și navighează la
http://localhost:8003/docs

# Click pe /interview/hr POST endpoint și testează manual
```

---

## 📈 Next Steps

1. ✅ **Toate serviciile pornite** → Mergi la http://localhost:3000
2. 🔧 **Implementează Agent Orchestrator** → Pune logica care leagă agentii
3. 📡 **Instalează Redpanda** (opțional) → Pentru async events
4. 🚀 **Deploy pe Kubernetes** → Cand e gata local

---

## 💡 Pro Tips

### Rapid Restart API Gateway
```powershell
cd api-gateway
npm run build && npm run start:prod
```

### Rebuild Frontend Quick
```powershell
cd frontend
npm run build
npm run dev
```

### Clear Redis Cache
```powershell
redis-cli FLUSHALL
```

### View PostgreSQL Logs
```powershell
# Windows Event Viewer
eventvwr   # Cauta "PostgreSQL"

# SAU din psql direct
psql -U postgres -d careerpath -c "SELECT * FROM pg_stat_statements LIMIT 10;"
```

### Monitor Python Agent Logs
```powershell
# Adaugă la fiecare script Python (deja e)
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

**🎉 Ready to go! Deschide http://localhost:3000**

Orice probleme → Check Terminal 5/6/7 (Agents) pentru error messages.

