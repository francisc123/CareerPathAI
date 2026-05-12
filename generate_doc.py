from docx import Document
from docx.shared import Pt, RGBColor, Inches, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import copy

doc = Document()

# ── Page margins ──────────────────────────────────────────────────────────────
for section in doc.sections:
    section.top_margin    = Cm(2.5)
    section.bottom_margin = Cm(2.5)
    section.left_margin   = Cm(2.5)
    section.right_margin  = Cm(2.5)

# ── Color palette ─────────────────────────────────────────────────────────────
DARK_BLUE   = RGBColor(0x1A, 0x2B, 0x4C)
MID_BLUE    = RGBColor(0x2E, 0x4A, 0x8A)
ACCENT_BLUE = RGBColor(0x4A, 0x90, 0xD9)
LIGHT_GRAY  = RGBColor(0xF0, 0xF4, 0xF8)
WHITE       = RGBColor(0xFF, 0xFF, 0xFF)
DARK_TEXT   = RGBColor(0x1A, 0x1A, 0x2E)
MED_TEXT    = RGBColor(0x44, 0x44, 0x66)
GREEN       = RGBColor(0x27, 0xAE, 0x60)
ORANGE      = RGBColor(0xE6, 0x7E, 0x22)
RED         = RGBColor(0xC0, 0x39, 0x2B)

# ── Helpers ───────────────────────────────────────────────────────────────────

def set_cell_bg(cell, hex_color: str):
    tc   = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd  = OxmlElement("w:shd")
    shd.set(qn("w:val"),   "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"),  hex_color)
    tcPr.append(shd)

def set_cell_border(cell, **kwargs):
    tc   = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcBorders = OxmlElement("w:tcBorders")
    for edge in ("top", "left", "bottom", "right"):
        tag = OxmlElement(f"w:{edge}")
        tag.set(qn("w:val"),   kwargs.get("val",   "single"))
        tag.set(qn("w:sz"),    kwargs.get("sz",    "4"))
        tag.set(qn("w:space"), "0")
        tag.set(qn("w:color"), kwargs.get("color", "FFFFFF"))
        tcBorders.append(tag)
    tcPr.append(tcBorders)

def add_paragraph_shading(paragraph, hex_color: str):
    pPr  = paragraph._p.get_or_add_pPr()
    shd  = OxmlElement("w:shd")
    shd.set(qn("w:val"),   "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"),  hex_color)
    pPr.append(shd)

def heading1(text: str):
    p = doc.add_paragraph()
    add_paragraph_shading(p, "1A2B4C")
    p.paragraph_format.space_before = Pt(18)
    p.paragraph_format.space_after  = Pt(6)
    p.paragraph_format.left_indent  = Cm(0.3)
    run = p.add_run(text)
    run.bold      = True
    run.font.size = Pt(15)
    run.font.color.rgb = WHITE

def heading2(text: str):
    p = doc.add_paragraph()
    add_paragraph_shading(p, "2E4A8A")
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after  = Pt(4)
    p.paragraph_format.left_indent  = Cm(0.3)
    run = p.add_run(text)
    run.bold      = True
    run.font.size = Pt(12)
    run.font.color.rgb = WHITE

def heading3(text: str):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after  = Pt(2)
    run = p.add_run(text)
    run.bold      = True
    run.font.size = Pt(11)
    run.font.color.rgb = MID_BLUE

def body(text: str, bold_prefix: str = None, color=None):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after  = Pt(2)
    if bold_prefix:
        rb = p.add_run(bold_prefix + " ")
        rb.bold = True
        rb.font.size = Pt(10)
        rb.font.color.rgb = color or DARK_TEXT
    r  = p.add_run(text)
    r.font.size      = Pt(10)
    r.font.color.rgb = color or DARK_TEXT
    return p

def bullet(text: str, bold_prefix: str = None, level: int = 0, color=None):
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.left_indent  = Cm(0.8 + level * 0.5)
    p.paragraph_format.space_before = Pt(1)
    p.paragraph_format.space_after  = Pt(1)
    if bold_prefix:
        rb = p.add_run(bold_prefix + " ")
        rb.bold = True
        rb.font.size = Pt(10)
        rb.font.color.rgb = color or DARK_TEXT
    r  = p.add_run(text)
    r.font.size = Pt(10)
    r.font.color.rgb = color or DARK_TEXT

def info_box(text: str, bg: str = "E8F4FD", border_color: str = "2E4A8A"):
    p = doc.add_paragraph()
    add_paragraph_shading(p, bg)
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after  = Pt(6)
    p.paragraph_format.left_indent  = Cm(0.5)
    p.paragraph_format.right_indent = Cm(0.5)
    r = p.add_run(text)
    r.font.size      = Pt(10)
    r.italic         = True
    r.font.color.rgb = MID_BLUE

def spacer(n=1):
    for _ in range(n):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after  = Pt(0)

# ══════════════════════════════════════════════════════════════════════════════
# COVER PAGE
# ══════════════════════════════════════════════════════════════════════════════
spacer(2)

title_p = doc.add_paragraph()
title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
add_paragraph_shading(title_p, "1A2B4C")
title_p.paragraph_format.space_before = Pt(30)
title_p.paragraph_format.space_after  = Pt(8)
tr = title_p.add_run("CareerPath AI")
tr.bold = True
tr.font.size = Pt(32)
tr.font.color.rgb = WHITE

subtitle_p = doc.add_paragraph()
subtitle_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
add_paragraph_shading(subtitle_p, "2E4A8A")
subtitle_p.paragraph_format.space_before = Pt(0)
subtitle_p.paragraph_format.space_after  = Pt(30)
sr = subtitle_p.add_run("Document de Proiectare Arhitecturală")
sr.bold = True
sr.font.size = Pt(16)
sr.font.color.rgb = RGBColor(0xB8, 0xD4, 0xFF)

spacer(1)

meta_table = doc.add_table(rows=4, cols=2)
meta_table.alignment = WD_TABLE_ALIGNMENT.CENTER
meta_table.style = "Table Grid"
meta_rows = [
    ("Versiune", "1.0"),
    ("Data", "29 Aprilie 2026"),
    ("Echipă", "Rareș Constantinescu · Francisc · Vlad"),
    ("Statut", "In Development — Sprint 1 Complet"),
]
for i, (k, v) in enumerate(meta_rows):
    row = meta_table.rows[i]
    set_cell_bg(row.cells[0], "1A2B4C")
    set_cell_bg(row.cells[1], "F0F4F8")
    kp = row.cells[0].paragraphs[0]
    vp = row.cells[1].paragraphs[0]
    kr = kp.add_run(k)
    kr.bold = True
    kr.font.size = Pt(10)
    kr.font.color.rgb = WHITE
    vr = vp.add_run(v)
    vr.font.size = Pt(10)
    vr.font.color.rgb = DARK_TEXT

doc.add_page_break()

# ══════════════════════════════════════════════════════════════════════════════
# 1. INTRODUCERE
# ══════════════════════════════════════════════════════════════════════════════
heading1("1. INTRODUCERE")

heading2("1.1 Scopul Sistemului")
body(
    "CareerPath AI este o platformă inteligentă de orientare în carieră, construită pe o arhitectură "
    "event-driven cu doi straturi de agenți AI. Sistemul analizează CV-uri ale utilizatorilor, "
    "identifică lacune de competențe față de cerințele pieței, recomandă trasee de învățare personalizate "
    "și potrivește candidații cu oportunități de job relevante. Întreaga logică AI este descuplată "
    "de interfața utilizatorului prin intermediul unui bus de mesaje (Redpanda/Kafka), permițând "
    "scalare independentă a fiecărui agent."
)
spacer()
info_box(
    "Principiu de design: Niciun agent AI nu interacționează direct cu utilizatorul. "
    "Toate comunicațiile se fac exclusiv prin eventi Redpanda, asigurând loose coupling și fault isolation."
)

heading2("1.2 Definiții și Acronime")

acronyms = [
    ("AI", "Artificial Intelligence — Inteligență Artificială"),
    ("RAG", "Retrieval-Augmented Generation — generare de conținut augmentată cu regăsire semantică"),
    ("LLM", "Large Language Model — model de limbaj de mari dimensiuni (ex. Gemini 2.5 Flash)"),
    ("JWT", "JSON Web Token — token de autentificare semnat criptografic"),
    ("API", "Application Programming Interface — interfață de programare a aplicației"),
    ("SSE", "Server-Sent Events — notificări push de la server la client"),
    ("CV",  "Curriculum Vitae — document de prezentare profesională"),
    ("RS256", "RSA Signature with SHA-256 — algoritm asimetric de semnare JWT"),
    ("ORM", "Object-Relational Mapping — mapare obiecte-relații pentru baze de date"),
    ("UI",  "User Interface — interfața grafică a aplicației"),
    ("MQ",  "Message Queue — coadă de mesaje pentru comunicare asincronă"),
    ("OTEL", "OpenTelemetry — standard open-source pentru observabilitate distribuită"),
]

t = doc.add_table(rows=len(acronyms)+1, cols=2)
t.style = "Table Grid"
t.alignment = WD_TABLE_ALIGNMENT.LEFT

set_cell_bg(t.rows[0].cells[0], "1A2B4C")
set_cell_bg(t.rows[0].cells[1], "1A2B4C")
for cell, txt in zip(t.rows[0].cells, ["Acronim / Termen", "Definiție"]):
    rr = cell.paragraphs[0].add_run(txt)
    rr.bold = True; rr.font.size = Pt(10); rr.font.color.rgb = WHITE

for i, (a, d) in enumerate(acronyms):
    row = t.rows[i+1]
    bg  = "F0F4F8" if i % 2 == 0 else "FFFFFF"
    set_cell_bg(row.cells[0], bg); set_cell_bg(row.cells[1], bg)
    ra = row.cells[0].paragraphs[0].add_run(a)
    ra.bold = True; ra.font.size = Pt(10); ra.font.color.rgb = MID_BLUE
    rd = row.cells[1].paragraphs[0].add_run(d)
    rd.font.size = Pt(10); rd.font.color.rgb = DARK_TEXT
t.columns[0].width = Cm(3)
t.columns[1].width = Cm(13)

heading2("1.3 Documente de Referință")
bullet("Specificație Cerințe Proiect — CareerPath AI v1.0 (document intern)")
bullet("Google Gemini API Documentation — https://ai.google.dev/api")
bullet("Qdrant Vector Database Documentation — https://qdrant.tech/documentation")
bullet("Apache Kafka Protocol Specification (compatibil Redpanda)")
bullet("Keycloak 24.0 Administration Guide")
bullet("Next.js 14 App Router Documentation — https://nextjs.org/docs")
bullet("OpenTelemetry Specification v1.25")

doc.add_page_break()

# ══════════════════════════════════════════════════════════════════════════════
# 2. OBIECTIVE DE PROIECTARE
# ══════════════════════════════════════════════════════════════════════════════
heading1("2. OBIECTIVE DE PROIECTARE")
spacer()

objectives = [
    ("Scalabilitate orizontală",
     "Fiecare agent AI și serviciu backend poate fi scalat independent. Comunicarea prin Redpanda elimină cuplajul direct între servicii, permitând adăugarea de instanțe fără modificări arhitecturale."),
    ("Arhitectură Event-Driven",
     "Niciun serviciu nu apelează sincron alt serviciu. Toate fluxurile de date se realizează prin eventi publicați pe topicuri Redpanda, asigurând reziliență la căderi parțiale."),
    ("AI-First Design",
     "Logica de business principală este implementată prin agenți AI (Gemini 2.5 Flash). Prompturile sunt externalizate în fișiere .txt versionabile, permitând iterație rapidă fără redeploy de cod."),
    ("Securitate Zero-Trust",
     "Autentificare prin Keycloak cu tokeni JWT RS256 asimetrici. API Gateway-ul validează tokenul și injectează x-user-id în request-uri downstream — serviciile interne nu reverifică tokenul."),
    ("Observabilitate Completă",
     "Stack LGTM (Loki + Grafana + Tempo + Prometheus) cu OpenTelemetry pentru traces distribuite, metrici Prometheus și loguri centralizate Loki."),
    ("Developer Experience",
     "Docker Compose cu profile dedicate pe fiecare developer (agents/backend/frontend), hot-reload automat via docker-compose.override.yml, fără rebuild la modificări de cod."),
    ("Persistență Duală Specializată",
     "PostgreSQL pentru date structurate cu query-uri exacte, Qdrant pentru căutare semantică vectorială — fiecare bază de date optimizată pentru tipul său de query."),
    ("Separarea Responsabilităților",
     "Fiecare developer deține un set clar de servicii și baze de date. Datele cross-service circulă exclusiv prin eventi Redpanda, fără acces direct la bazele de date ale celorlalți."),
]

for title, desc in objectives:
    p = doc.add_paragraph()
    add_paragraph_shading(p, "E8F4FD")
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after  = Pt(4)
    p.paragraph_format.left_indent  = Cm(0.3)
    rb = p.add_run(f"● {title}: ")
    rb.bold = True; rb.font.size = Pt(10); rb.font.color.rgb = MID_BLUE
    rd = p.add_run(desc)
    rd.font.size = Pt(10); rd.font.color.rgb = DARK_TEXT

doc.add_page_break()

# ══════════════════════════════════════════════════════════════════════════════
# 3. ARHITECTURA PROPUSĂ
# ══════════════════════════════════════════════════════════════════════════════
heading1("3. ARHITECTURA PROPUSĂ")

heading2("3.1 Prezentarea Generală a Arhitecturii Sistemului")

body(
    "CareerPath AI este construit pe o arhitectură cu 4 straturi logice: Frontend, API Gateway, "
    "Servicii Core și Agenți AI. Infrastructura transversală (baze de date, mesagerie, stocare) "
    "suportă toate straturile."
)
spacer()

arch_table = doc.add_table(rows=5, cols=2)
arch_table.style = "Table Grid"
arch_table.alignment = WD_TABLE_ALIGNMENT.CENTER

layers = [
    ("STRAT 1 — Frontend", "Next.js 14 (App Router) · Tailwind CSS · shadcn/ui · Zustand\nInterfața utilizatorului: autentificare, dashboard carieră, upload CV, chat cu orchestratorul", "2E4A8A"),
    ("STRAT 2 — API Gateway", "NestJS + Fastify · JWT Guard RS256 · Proxy Routes\nSingura intrare publică în sistem. Validează tokeni, rutează request-uri, injectează identitatea utilizatorului", "1A5276"),
    ("STRAT 3 — Servicii Core", "user-service · cv-service · job-scraper · notification-service\nLogica de business: gestionare utilizatori, procesare CV-uri PDF, scraping joburi, notificări SSE", "1E8449"),
    ("STRAT 4 — Agenți AI", "agent-orchestrator · cv-analyzer · learning-path · job-match · hr/tech interview\nWorkers invizibili care procesează evenimente asincron cu Gemini 2.5 Flash + RAG pe Qdrant", "6E2F8A"),
    ("INFRASTRUCTURĂ", "PostgreSQL · Qdrant · Redis · Redpanda · MinIO · Keycloak · Grafana LGTM\nServicii suport care pornesc cu orice profil Docker Compose", "424949"),
]
for i, (name, desc, color_hex) in enumerate(layers):
    row = arch_table.rows[i]
    set_cell_bg(row.cells[0], color_hex)
    set_cell_bg(row.cells[1], "F8F9FA")
    rn = row.cells[0].paragraphs[0].add_run(name)
    rn.bold = True; rn.font.size = Pt(9); rn.font.color.rgb = WHITE
    rd = row.cells[1].paragraphs[0].add_run(desc)
    rd.font.size = Pt(9); rd.font.color.rgb = DARK_TEXT
arch_table.columns[0].width = Cm(5)
arch_table.columns[1].width = Cm(11)

spacer()
heading3("Fluxul principal de date")
body(
    "Utilizatorul încarcă un CV → cv-service îl procesează și publică pe cv.uploaded → "
    "cv-analyzer-agent îl analizează cu Gemini (scor + gap analysis) și publică pe cv.analyzed → "
    "agent-orchestrator routează: dacă scor ≥ 70 trimite la job-match-agent, dacă scor < 70 "
    "trimite la learning-path-agent → rezultatele ajung la utilizator prin notification-service (SSE)."
)

heading2("3.2 Decompoziția în Subsisteme și Responsabilități")

# ── Rares ──────────────────────────────────────────────────────────────────
heading3("3.2.1 Subsistemul AI Agents — Responsabil: Rareș Constantinescu")
info_box("Profil Docker: --profile agents | Porturi: 8005–8010")

agents_data = [
    ("cv-analyzer-agent", "8006", "Python + FastAPI", "Consumă cv.uploaded. Scor CV (Gemini 2.5 Flash), gap analysis, embedding Qdrant, persistare PostgreSQL. Publică pe cv.analyzed."),
    ("agent-orchestrator", "8005", "Python + LangGraph", "Hub central. Conversație WebSocket cu utilizatorul. Shadow profiling. Rutare evenimente pe baza scorului CV."),
    ("learning-path-agent", "8007", "Python + FastAPI", "Consumă gaps.identified. Generează traseu de învățare personalizat cu resurse Udemy/YouTube via Gemini."),
    ("job-match-agent", "8008", "Python + Qdrant", "Consumă jobs.scraped. Căutare semantică în Qdrant job_embeddings. Reranking cu Gemini. Publică jobs.matched."),
    ("hr-interview-agent", "8009", "Python + WebSocket", "Simulare interviu HR cu streaming Gemini. Feedback pe răspunsuri în timp real."),
    ("technical-interview-agent", "8010", "Python + WebSocket", "Simulare interviu tehnic. Evaluare cod via Judge0 API. Feedback instant."),
]

t = doc.add_table(rows=len(agents_data)+1, cols=4)
t.style = "Table Grid"
headers = ["Serviciu", "Port", "Stack", "Responsabilitate"]
for j, h in enumerate(headers):
    set_cell_bg(t.rows[0].cells[j], "6E2F8A")
    rr = t.rows[0].cells[j].paragraphs[0].add_run(h)
    rr.bold = True; rr.font.size = Pt(9); rr.font.color.rgb = WHITE

for i, row_data in enumerate(agents_data):
    row = t.rows[i+1]
    bg = "F5EEF8" if i % 2 == 0 else "FFFFFF"
    for j, val in enumerate(row_data):
        set_cell_bg(row.cells[j], bg)
        r = row.cells[j].paragraphs[0].add_run(val)
        r.font.size = Pt(8.5)
        r.font.color.rgb = DARK_TEXT
        if j == 0:
            r.bold = True; r.font.color.rgb = MID_BLUE

t.columns[0].width = Cm(3.5)
t.columns[1].width = Cm(1.2)
t.columns[2].width = Cm(3.3)
t.columns[3].width = Cm(8)

spacer()

# ── Francis ─────────────────────────────────────────────────────────────────
heading3("3.2.2 Subsistemul Backend Core — Responsabil: Francisc")
info_box("Profil Docker: --profile backend | Porturi: 8000–8004")

backend_data = [
    ("api-gateway", "8000", "NestJS + Fastify", "Singura intrare publică. JWT Guard RS256, routing, injectare x-user-id header."),
    ("user-service", "8001", "Java Spring Boot + Keycloak", "Gestionare utilizatori și profiluri. Autentificare OAuth2 via Keycloak. PostgreSQL cu JPA/Hibernate."),
    ("cv-service", "8002", "Python + FastAPI + pdfplumber", "Extragere text din PDF. Stocare fișier în MinIO. Publicare pe cv.uploaded."),
    ("job-scraper-service", "8003", "Python + Playwright", "Scraping joburi cu browser headless Chromium. Publicare pe jobs.scraped."),
    ("notification-service", "8004", "NestJS + SSE + aiokafka", "Consumă eventi și livrează notificări push la frontend via Server-Sent Events."),
]

t2 = doc.add_table(rows=len(backend_data)+1, cols=4)
t2.style = "Table Grid"
for j, h in enumerate(headers):
    set_cell_bg(t2.rows[0].cells[j], "1E5276")
    rr = t2.rows[0].cells[j].paragraphs[0].add_run(h)
    rr.bold = True; rr.font.size = Pt(9); rr.font.color.rgb = WHITE

for i, row_data in enumerate(backend_data):
    row = t2.rows[i+1]
    bg = "EBF5FB" if i % 2 == 0 else "FFFFFF"
    for j, val in enumerate(row_data):
        set_cell_bg(row.cells[j], bg)
        r = row.cells[j].paragraphs[0].add_run(val)
        r.font.size = Pt(8.5); r.font.color.rgb = DARK_TEXT
        if j == 0:
            r.bold = True; r.font.color.rgb = MID_BLUE

t2.columns[0].width = Cm(3.5)
t2.columns[1].width = Cm(1.2)
t2.columns[2].width = Cm(3.3)
t2.columns[3].width = Cm(8)

spacer()

# ── Vlad ─────────────────────────────────────────────────────────────────────
heading3("3.2.3 Subsistemul Frontend — Responsabil: Vlad")
info_box("Profil Docker: --profile frontend | Port: 3000")

frontend_data = [
    ("Login Page", "Auth flow", "React Hook Form + Zod + Axios", "Validare client-side, apel API Gateway /auth/login, stocare JWT în Zustand + localStorage."),
    ("Register Page", "Auth flow", "React Hook Form + Zod", "Înregistrare utilizator nou, redirect post-register."),
    ("Dashboard Page", "Core UI", "Next.js App Router + shadcn/ui", "Panou principal: scor CV, job matches, progres learning path, chat orchestrator."),
    ("UI Component Library", "Shared", "shadcn/ui + Tailwind CSS", "CVScoreGauge, JobCard, ModuleCard, ChatBubble, ProgressBar — componente reutilizabile."),
    ("Auth Store", "State", "Zustand + persist middleware", "Gestionare globală autentificare: user, token, isAuthenticated cu persistare localStorage."),
    ("API Client", "Infra", "Axios interceptors", "Client centralizat cu baseURL api-gateway, injectare automată Bearer token la fiecare request."),
]

t3 = doc.add_table(rows=len(frontend_data)+1, cols=4)
t3.style = "Table Grid"
fheaders = ["Componentă", "Categorie", "Stack", "Responsabilitate"]
for j, h in enumerate(fheaders):
    set_cell_bg(t3.rows[0].cells[j], "1E8449")
    rr = t3.rows[0].cells[j].paragraphs[0].add_run(h)
    rr.bold = True; rr.font.size = Pt(9); rr.font.color.rgb = WHITE

for i, row_data in enumerate(frontend_data):
    row = t3.rows[i+1]
    bg = "EAFAF1" if i % 2 == 0 else "FFFFFF"
    for j, val in enumerate(row_data):
        set_cell_bg(row.cells[j], bg)
        r = row.cells[j].paragraphs[0].add_run(val)
        r.font.size = Pt(8.5); r.font.color.rgb = DARK_TEXT
        if j == 0:
            r.bold = True; r.font.color.rgb = MID_BLUE

t3.columns[0].width = Cm(3.5)
t3.columns[1].width = Cm(2)
t3.columns[2].width = Cm(3.5)
t3.columns[3].width = Cm(7)

doc.add_page_break()

# ══════════════════════════════════════════════════════════════════════════════
# 3.3 MANAGEMENTUL DATELOR
# ══════════════════════════════════════════════════════════════════════════════
heading2("3.3 Managementul Datelor Persistente")

heading3("3.3.1 PostgreSQL — Baza de Date Relațională")
body(
    "PostgreSQL 16 stochează toate datele structurate ale platformei. Accesul este strict per serviciu — "
    "niciun serviciu nu accesează tabelele altui serviciu direct."
)
spacer()

pg_tables = [
    ("users", "Francisc (user-service)", "id, keycloak_id, email, username, created_at"),
    ("profiles", "Francisc (user-service)", "user_id FK, first_name, last_name, bio, avatar_url, updated_at"),
    ("user_progress", "Francisc (user-service)", "user_id FK, current_step, completion_pct, last_activity"),
    ("cv_uploads", "Francisc (cv-service)", "id, user_id, filename, minio_path, uploaded_at, status"),
    ("cv_analyses", "Rareș (cv-analyzer-agent)", "id, user_id, score, seniority, target_role, skills[], gaps[], score_breakdown JSONB, analyzed_at"),
    ("learning_paths", "Rareș (learning-path-agent)", "id, user_id, estimated_weeks, learning_order[], created_at"),
    ("scraped_jobs", "Francisc (job-scraper)", "id, title, company, description, tech_stack[], url, scraped_at"),
    ("job_matches", "Rareș (job-match-agent)", "id, user_id, job_id FK, match_score, matched_at"),
    ("interview_sessions", "Rareș (interview agents)", "id, user_id, type (hr/tech), score, feedback, conducted_at"),
    ("quiz_attempts", "Rareș (learning-path-agent)", "id, user_id, topic, score, passed, attempted_at"),
]

t4 = doc.add_table(rows=len(pg_tables)+1, cols=3)
t4.style = "Table Grid"
for j, h in enumerate(["Tabel", "Proprietar", "Coloane principale"]):
    set_cell_bg(t4.rows[0].cells[j], "424949")
    rr = t4.rows[0].cells[j].paragraphs[0].add_run(h)
    rr.bold = True; rr.font.size = Pt(9); rr.font.color.rgb = WHITE

for i, row_data in enumerate(pg_tables):
    row = t4.rows[i+1]
    bg = "F2F3F4" if i % 2 == 0 else "FFFFFF"
    for j, val in enumerate(row_data):
        set_cell_bg(row.cells[j], bg)
        r = row.cells[j].paragraphs[0].add_run(val)
        r.font.size = Pt(8.5); r.font.color.rgb = DARK_TEXT
        if j == 0: r.bold = True

t4.columns[0].width = Cm(3.5)
t4.columns[1].width = Cm(4.5)
t4.columns[2].width = Cm(8)

spacer()
heading3("3.3.2 Qdrant — Baza de Date Vectorială")
body(
    "Qdrant v1.10 stochează reprezentări matematice (embeddings) ale CV-urilor și joburilor, "
    "generate cu modelul Google gemini-embedding-001 (dimensiune: 3072, similaritate: Cosine). "
    "Permite căutare semantică — găsirea documentelor similare ca sens, nu ca text exact."
)
spacer()

qdrant_data = [
    ("cv_embeddings", "3072", "Cosine", "Rareș", "user_id, score, seniority, skills[], target_role", "Embedding CV per utilizator. Actualizat la fiecare upload nou."),
    ("job_embeddings", "3072", "Cosine", "Rareș", "job_id, title, company, tech_stack[]", "Embedding joburi scraped. Permite job-match semantic."),
    ("course_embeddings", "3072", "Cosine", "Rareș", "course_id, title, provider, topics[]", "Embedding cursuri Udemy/YouTube pentru recomandări learning path."),
]

t5 = doc.add_table(rows=len(qdrant_data)+1, cols=6)
t5.style = "Table Grid"
for j, h in enumerate(["Colecție", "Dim.", "Distanță", "Owner", "Payload", "Scop"]):
    set_cell_bg(t5.rows[0].cells[j], "6E2F8A")
    rr = t5.rows[0].cells[j].paragraphs[0].add_run(h)
    rr.bold = True; rr.font.size = Pt(8); rr.font.color.rgb = WHITE

for i, row_data in enumerate(qdrant_data):
    row = t5.rows[i+1]
    bg = "F5EEF8" if i % 2 == 0 else "FFFFFF"
    for j, val in enumerate(row_data):
        set_cell_bg(row.cells[j], bg)
        r = row.cells[j].paragraphs[0].add_run(val)
        r.font.size = Pt(8); r.font.color.rgb = DARK_TEXT
        if j == 0: r.bold = True

t5.columns[0].width = Cm(3.5)
t5.columns[1].width = Cm(1)
t5.columns[2].width = Cm(1.5)
t5.columns[3].width = Cm(1.5)
t5.columns[4].width = Cm(4.5)
t5.columns[5].width = Cm(4)

spacer()
heading3("3.3.3 Redis — Cache și State Sesiuni")
body(
    "Redis 7 cu autentificare prin parolă. Utilizat pentru: sesiuni JWT (TTL = 15 minute), "
    "rate limiting pe API Gateway, stare temporară workflow-uri inter-agenți."
)

heading3("3.3.4 MinIO — Object Storage")
body(
    "MinIO (compatibil S3) stochează fișierele CV brut în bucket-ul cvs-raw. "
    "cv-service uploadează fișierul, salvează calea MinIO în PostgreSQL (cv_uploads.minio_path) "
    "și publică doar textul extras pe Redpanda — nu fișierul binar."
)

doc.add_page_break()

# ══════════════════════════════════════════════════════════════════════════════
# 3.4 CONTROLUL ACCESULUI
# ══════════════════════════════════════════════════════════════════════════════
heading2("3.4 Controlul Accesului Utilizatorilor")

body(
    "Sistemul implementează un model de autentificare centralizat prin Keycloak 24.0 cu tokeni "
    "JWT semnaţi RS256 (cheie asimetrică — cheia privată semnează, cheia publică verifică)."
)
spacer()

auth_flow = [
    ("1", "Utilizatorul trimite credențiale (email + parolă) la API Gateway /auth/login"),
    ("2", "API Gateway redirecționează autentificarea la Keycloak 24.0 (port 8484)"),
    ("3", "Keycloak emite access_token (JWT, TTL 15min) + refresh_token (TTL 7 zile)"),
    ("4", "API Gateway returnează tokenul la frontend"),
    ("5", "Frontend stochează tokenul în Zustand store (persistat în localStorage)"),
    ("6", "La fiecare request API, Axios injectează automat Bearer token în header"),
    ("7", "API Gateway validează semnătura JWT cu cheia publică RS256 (keys/public.pem)"),
    ("8", "API Gateway extrage sub (Keycloak user ID) și injectează x-user-id header"),
    ("9", "Serviciile downstream (user-service, cv-service etc.) citesc x-user-id — nu reverifică JWT"),
]

t6 = doc.add_table(rows=len(auth_flow)+1, cols=2)
t6.style = "Table Grid"
for j, h in enumerate(["Pas", "Acțiune"]):
    set_cell_bg(t6.rows[0].cells[j], "1A2B4C")
    rr = t6.rows[0].cells[j].paragraphs[0].add_run(h)
    rr.bold = True; rr.font.size = Pt(10); rr.font.color.rgb = WHITE

for i, (step, action) in enumerate(auth_flow):
    row = t6.rows[i+1]
    bg = "E8EAF6" if i % 2 == 0 else "FFFFFF"
    set_cell_bg(row.cells[0], bg); set_cell_bg(row.cells[1], bg)
    rs = row.cells[0].paragraphs[0].add_run(step)
    rs.bold = True; rs.font.size = Pt(10); rs.font.color.rgb = ACCENT_BLUE
    ra = row.cells[1].paragraphs[0].add_run(action)
    ra.font.size = Pt(10); ra.font.color.rgb = DARK_TEXT

t6.columns[0].width = Cm(1)
t6.columns[1].width = Cm(15)

spacer()
info_box(
    "Principiu de securitate: Serviciile interne nu sunt expuse public. Doar api-gateway "
    "are acces la rețeaua publică. Toate celelalte servicii sunt pe rețeaua internă Docker (internal-net)."
)

# ══════════════════════════════════════════════════════════════════════════════
# 3.5 FLUXUL GLOBAL AL CONTROLULUI
# ══════════════════════════════════════════════════════════════════════════════
heading2("3.5 Fluxul Global al Controlului — Topicuri Redpanda")

body(
    "Toate comunicările asincrone se realizează prin topicuri Redpanda (compatibil Kafka). "
    "Fiecare serviciu consumă un singur topic și publică pe unul sau mai multe topicuri."
)
spacer()

topics = [
    ("cv.uploaded", "cv-service", "cv-analyzer-agent", "Text extras din PDF + user_id + cv_upload_id"),
    ("cv.analyzed", "cv-analyzer-agent", "agent-orchestrator", "Scor, seniority, skills, gaps, score_breakdown, user_id"),
    ("gaps.identified", "agent-orchestrator", "learning-path-agent", "Lista gaps prioritare, săptămâni estimate, user_id"),
    ("learning.path.created", "learning-path-agent", "agent-orchestrator + notification-service", "Traseu complet cu resurse, ordine recomandată"),
    ("jobs.scraped", "job-scraper-service", "job-match-agent", "Lista joburi brute: titlu, companie, descriere, tech stack"),
    ("jobs.matched", "job-match-agent", "agent-orchestrator + notification-service", "Top joburi cu match score semantic față de CV-ul userului"),
    ("learning.completed", "agent-orchestrator", "hr-interview-agent / tech-interview-agent", "Semnalul că utilizatorul a finalizat learning path-ul"),
    ("interview.completed", "interview agents", "agent-orchestrator + notification-service", "Scor interviu, feedback detaliat, recomandări"),
]

t7 = doc.add_table(rows=len(topics)+1, cols=4)
t7.style = "Table Grid"
for j, h in enumerate(["Topic Redpanda", "Publisher", "Consumer(s)", "Payload"]):
    set_cell_bg(t7.rows[0].cells[j], "922B21")
    rr = t7.rows[0].cells[j].paragraphs[0].add_run(h)
    rr.bold = True; rr.font.size = Pt(9); rr.font.color.rgb = WHITE

for i, row_data in enumerate(topics):
    row = t7.rows[i+1]
    bg = "FDEDEC" if i % 2 == 0 else "FFFFFF"
    for j, val in enumerate(row_data):
        set_cell_bg(row.cells[j], bg)
        r = row.cells[j].paragraphs[0].add_run(val)
        r.font.size = Pt(8.5); r.font.color.rgb = DARK_TEXT
        if j == 0:
            r.bold = True; r.font.color.rgb = RGBColor(0x92, 0x2B, 0x21)

t7.columns[0].width = Cm(3.5)
t7.columns[1].width = Cm(3.5)
t7.columns[2].width = Cm(4)
t7.columns[3].width = Cm(5)

# ══════════════════════════════════════════════════════════════════════════════
# 3.6 CONDIȚII LIMITĂ
# ══════════════════════════════════════════════════════════════════════════════
doc.add_page_break()
heading2("3.6 Condiții Limită și Gestionarea Erorilor")

limits = [
    ("Gemini API Rate Limit", "Retry cu backoff exponențial — 3 încercări, 2s/5s între tentative (implementat în cv_analyzer.py)"),
    ("Redpanda down la startup", "cv-analyzer-agent nu pornește dacă healthcheck-ul Redpanda eșuează — depends_on cu condition: service_healthy"),
    ("PostgreSQL pool epuizat", "asyncpg connection pool cu max_size configurabil. Timeout la 30s → eroare loggată, mesaj Kafka nack-uit"),
    ("CV text gol sau invalid", "Validare în cv-service înainte de publish. embedding_tool.py aruncă ValueError dacă textul e gol"),
    ("Qdrant collection lipsă", "qdrant_setup.py creează colecțiile la startup dacă nu există — idempotent"),
    ("JWT expirat", "API Gateway returnează 401. Frontend-ul detectează și declanșează refresh token flow automat"),
    ("MinIO indisponibil", "cv-service eșuează graceful, returnează 503. Nu publică pe cv.uploaded dacă fișierul nu a fost salvat"),
    ("Gemini răspuns invalid JSON", "ValidationError captat de Pydantic → retry. Dacă toate 3 tentative eșuează → RuntimeError loggat, mesaj Kafka nack-uit"),
]

t8 = doc.add_table(rows=len(limits)+1, cols=2)
t8.style = "Table Grid"
for j, h in enumerate(["Condiție Limită", "Strategie de Gestionare"]):
    set_cell_bg(t8.rows[0].cells[j], "7D6608")
    rr = t8.rows[0].cells[j].paragraphs[0].add_run(h)
    rr.bold = True; rr.font.size = Pt(9); rr.font.color.rgb = WHITE

for i, (cond, strat) in enumerate(limits):
    row = t8.rows[i+1]
    bg = "FEFBD8" if i % 2 == 0 else "FFFFFF"
    set_cell_bg(row.cells[0], bg); set_cell_bg(row.cells[1], bg)
    rc = row.cells[0].paragraphs[0].add_run(cond)
    rc.bold = True; rc.font.size = Pt(9); rc.font.color.rgb = RGBColor(0x7D, 0x66, 0x08)
    rs = row.cells[1].paragraphs[0].add_run(strat)
    rs.font.size = Pt(9); rs.font.color.rgb = DARK_TEXT

t8.columns[0].width = Cm(5)
t8.columns[1].width = Cm(11)

doc.add_page_break()

# ══════════════════════════════════════════════════════════════════════════════
# 4. STACK TEHNOLOGIC COMPLET
# ══════════════════════════════════════════════════════════════════════════════
heading1("4. STACK TEHNOLOGIC COMPLET")
spacer()

tech_categories = [
    ("AI & Machine Learning", "6E2F8A", [
        ("Google Gemini 2.5 Flash", "Model LLM principal pentru scoring CV, gap analysis, simulare interviuri, reranking joburi. Accesat via google-genai SDK."),
        ("gemini-embedding-001", "Model Google pentru generare embeddings semantice (dim=3072). Înlocuiește text-embedding-004 (deprecated)."),
        ("Qdrant v1.10", "Baza de date vectorială pentru căutare semantică. 3 colecții: cv_embeddings, job_embeddings, course_embeddings."),
        ("LangGraph", "Framework pentru agenți cu stări (agent-orchestrator). Gestionează graful de decizie și tranzițiile între stări."),
        ("Pydantic v2", "Validare structurată a răspunsurilor Gemini. Garantează că JSON-ul returnat respectă schema definită."),
    ]),
    ("Backend & API", "1E5276", [
        ("FastAPI 0.111", "Framework web asincron Python pentru toți agenții AI și serviciile Python core."),
        ("NestJS + Fastify", "Framework Node.js pentru API Gateway și notification-service. Fastify ca adapter HTTP pentru performanță."),
        ("Java Spring Boot", "Framework pentru user-service. Securitate via Spring Security + OAuth2 Resource Server (Keycloak JWT)."),
        ("aiokafka 0.11", "Client Python async pentru Redpanda/Kafka. Folosit de toți agenții pentru consumer și producer."),
        ("asyncpg 0.29", "Client PostgreSQL async performant. Pool de conexiuni gestionat la startup/shutdown."),
        ("pdfplumber", "Extragere text din PDF în cv-service. Suportă PDF scanate cu OCR fallback (Tesseract)."),
        ("Playwright", "Browser headless Chromium pentru job-scraper-service. Suportă site-uri cu JavaScript rendering."),
        ("Prisma ORM", "ORM TypeScript pentru NestJS services (notification-service)."),
    ]),
    ("Frontend", "1E8449", [
        ("Next.js 14", "Framework React cu App Router. SSR + client components. Hot reload via WATCHPACK_POLLING în Docker."),
        ("Tailwind CSS", "Utility-first CSS framework. Design system consistent pe toate paginile."),
        ("shadcn/ui", "Librărie componente bazată pe Radix UI. Componente: Button, Card, Dialog, Input, Tabs, Badge, Progress."),
        ("Zustand", "State management global React. Auth store cu persist middleware (localStorage)."),
        ("Axios", "HTTP client cu interceptori pentru injectare automată Bearer token."),
        ("React Hook Form + Zod", "Formulare cu validare schema-based. Schema Zod partajată între client și server."),
    ]),
    ("Infrastructură & DevOps", "424949", [
        ("Docker + Docker Compose", "Containerizare completă. Profile dedicate pe developer (agents/backend/frontend)."),
        ("Redpanda", "Message broker compatibil Kafka. 8 topicuri pentru comunicare inter-servicii asincronă."),
        ("PostgreSQL 16", "Baza de date relațională principală. Init schema automată la primul start container."),
        ("Redis 7", "Cache distributed și session store. Autentificare cu parolă, maxmemory configurat."),
        ("MinIO", "Object storage compatibil S3 pentru CV-uri PDF brute. Bucket cvs-raw cu lifecycle rules."),
        ("Keycloak 24.0", "Identity Provider. Gestionare utilizatori, OAuth2/OIDC, emitere JWT RS256."),
        ("OpenTelemetry", "Traces distribuite cross-service. Colector OTEL → Tempo (traces) + Prometheus (metrici)."),
        ("Grafana LGTM", "Observabilitate: Loki (loguri) + Grafana (dashboards) + Tempo (traces) + Prometheus (metrici)."),
        ("prometheus-fastapi-instrumentator", "Auto-instrumentare FastAPI pentru metrici Prometheus pe toți agenții Python."),
    ]),
]

for cat_name, cat_color, items in tech_categories:
    p = doc.add_paragraph()
    add_paragraph_shading(p, cat_color)
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after  = Pt(4)
    p.paragraph_format.left_indent  = Cm(0.3)
    rh = p.add_run(f"  {cat_name}")
    rh.bold = True; rh.font.size = Pt(11); rh.font.color.rgb = WHITE

    for tech, desc in items:
        bp = doc.add_paragraph()
        bp.paragraph_format.left_indent  = Cm(0.5)
        bp.paragraph_format.space_before = Pt(2)
        bp.paragraph_format.space_after  = Pt(2)
        rt = bp.add_run(f"▸ {tech}: ")
        rt.bold = True; rt.font.size = Pt(9.5); rt.font.color.rgb = RGBColor(int(cat_color[:2],16), int(cat_color[2:4],16), int(cat_color[4:],16))
        rd = bp.add_run(desc)
        rd.font.size = Pt(9.5); rd.font.color.rgb = DARK_TEXT

doc.add_page_break()

# ══════════════════════════════════════════════════════════════════════════════
# 5. RESPONSABILITĂȚI ECHIPĂ
# ══════════════════════════════════════════════════════════════════════════════
heading1("5. RESPONSABILITĂȚI ECHIPĂ")
spacer()

team = [
    ("Rareș Constantinescu", "AI Engineer — Agenți & RAG", "6E2F8A", "F5EEF8", [
        "cv-analyzer-agent (COMPLET): scoring CV, gap analysis, RAG Qdrant, persistare PostgreSQL",
        "agent-orchestrator: hub conversațional WebSocket, shadow profiling, routing evenimente",
        "learning-path-agent: generare traseu personalizat cu resurse Udemy/YouTube",
        "job-match-agent: căutare semantică Qdrant job_embeddings + reranking Gemini",
        "hr-interview-agent: simulare interviu HR cu streaming Gemini",
        "technical-interview-agent: simulare interviu tehnic cu Judge0 evaluare cod",
        "Colecții Qdrant: cv_embeddings, job_embeddings, course_embeddings (dim=3072)",
        "Tabele PostgreSQL: cv_analyses, learning_paths, job_matches, interview_sessions, quiz_attempts",
        "Prompt engineering: cv_scoring.txt, gap_analysis.txt (fișiere externalizate versionabile)",
    ]),
    ("Francisc", "Backend Engineer — Core Services & Infrastructure", "1E5276", "EBF5FB", [
        "api-gateway (NestJS + Fastify): JWT Guard RS256, routing, proxy la servicii interne",
        "user-service (Java Spring Boot + Keycloak): gestionare utilizatori, profiluri, autentificare OAuth2",
        "cv-service (FastAPI + pdfplumber + MinIO): upload PDF, extragere text, publicare cv.uploaded",
        "job-scraper-service (Playwright): scraping joburi din surse externe cu browser headless",
        "notification-service (NestJS + SSE): livrare notificări push la frontend",
        "PostgreSQL schema: users, profiles, user_progress, cv_uploads, scraped_jobs",
        "Redis: configurare cache sesiuni JWT, rate limiting API Gateway",
        "MinIO: configurare bucket cvs-raw cu lifecycle rules, gestionare fișiere PDF",
        "Keycloak: configurare realm careerpath, clienți OAuth2, management utilizatori",
    ]),
    ("Vlad", "Frontend Engineer — UI/UX & Design System", "1E8449", "EAFAF1", [
        "Next.js 14 setup (App Router, TypeScript, hot reload Docker)",
        "Pagina Login: React Hook Form, validare Zod, Axios API client, Zustand auth store",
        "Pagina Register: înregistrare utilizator, redirect post-register",
        "Dashboard Page: panou principal complet (scor CV, job matches, learning progress, chat)",
        "UI Component Library: CVScoreGauge, JobCard, ModuleCard, ChatBubble, ProgressBar, Badge",
        "Auth Store (Zustand + persist): gestionare globală JWT cu auto-persistare localStorage",
        "API Client (Axios): interceptori Bearer token, baseURL api-gateway configurabil via .env",
        "Design system: Tailwind CSS + shadcn/ui, temă dark cu palette consistentă",
    ]),
]

for name, role, header_color, bg_color, tasks in team:
    p_header = doc.add_paragraph()
    add_paragraph_shading(p_header, header_color)
    p_header.paragraph_format.space_before = Pt(12)
    p_header.paragraph_format.space_after  = Pt(0)
    p_header.paragraph_format.left_indent  = Cm(0.3)
    rn = p_header.add_run(f"  {name}")
    rn.bold = True; rn.font.size = Pt(13); rn.font.color.rgb = WHITE
    rr = p_header.add_run(f"  —  {role}")
    rr.font.size = Pt(10); rr.font.color.rgb = RGBColor(0xB8, 0xD4, 0xFF)

    for task in tasks:
        tp = doc.add_paragraph()
        add_paragraph_shading(tp, bg_color)
        tp.paragraph_format.left_indent  = Cm(0.8)
        tp.paragraph_format.space_before = Pt(1)
        tp.paragraph_format.space_after  = Pt(1)
        rt = tp.add_run(f"✓  {task}")
        rt.font.size = Pt(9.5); rt.font.color.rgb = DARK_TEXT
    spacer()

doc.add_page_break()

# ══════════════════════════════════════════════════════════════════════════════
# 6. ROADMAP
# ══════════════════════════════════════════════════════════════════════════════
heading1("6. ROADMAP DE DEZVOLTARE")
spacer()

sprints = [
    ("Sprint 1 — Fundații", "COMPLET ✓", "27AE60", [
        ("Docker Compose complet cu toate serviciile și profile dedicate", "DONE", "Toată echipa"),
        ("PostgreSQL schema inițială (01_schema.sql)", "DONE", "Francisc + Rareș"),
        ("Redpanda setup + console UI + creare topicuri", "DONE", "Francisc"),
        ("Redis configurare cu auth și maxmemory", "DONE", "Francisc"),
        ("MinIO configurare bucket cvs-raw cu lifecycle rules", "DONE", "Francisc"),
        ("Qdrant setup + colecții cv/job/course embeddings (dim=3072)", "DONE", "Rareș"),
        ("Next.js 14 setup + UI Component Library (shadcn/ui)", "DONE", "Vlad"),
        ("Pagini Auth (Login, Register) cu validare Zod", "DONE", "Vlad"),
        ("Dashboard complet cu toate componentele UI", "DONE", "Vlad"),
        ("API Gateway NestJS + Fastify + JWT Guard RS256", "DONE", "Francisc"),
        ("User Service Java Spring Boot + Keycloak OAuth2", "DONE", "Francisc"),
        ("cv-analyzer-agent: pipeline complet (Gemini + RAG + PostgreSQL + Kafka)", "DONE", "Rareș"),
        ("Prompt engineering cv_scoring.txt + gap_analysis.txt", "DONE", "Rareș"),
        ("Keycloak 24.0 integrat în docker-compose", "DONE", "Francisc"),
    ]),
    ("Sprint 2 — Integrare Frontend-Backend", "IN PROGRESS", "E67E22", [
        ("Conectare login/register frontend la API Gateway real (înlocuire mock)", "TODO", "Vlad + Francisc"),
        ("cv-service: upload PDF + extragere text + publicare cv.uploaded", "TODO", "Francisc"),
        ("agent-orchestrator: consumer cv.analyzed + routing scor ≥/< 70", "TODO", "Rareș"),
        ("Implementare learning-path-agent complet", "TODO", "Rareș"),
        ("Implementare job-scraper-service cu Playwright", "TODO", "Francisc"),
        ("Implementare job-match-agent cu căutare Qdrant", "TODO", "Rareș"),
        ("notification-service: SSE la frontend pentru rezultate agenți", "TODO", "Francisc"),
        ("Dashboard: afișare dinamică rezultate CV (scor real, gaps, jobs)", "TODO", "Vlad"),
        ("Integrare OpenTelemetry traces în toți agenții", "TODO", "Rareș"),
    ]),
    ("Sprint 3 — Agenți Interviu & Polish", "PLANIFICAT", "2E4A8A", [
        ("hr-interview-agent: simulare conversație cu streaming Gemini", "PLANNED", "Rareș"),
        ("technical-interview-agent: evaluare cod cu Judge0", "PLANNED", "Rareș"),
        ("Grafana dashboards: CV score trends, agent latency, Kafka lag", "PLANNED", "Toată echipa"),
        ("E2E testing pipeline complet (upload CV → jobs matched)", "PLANNED", "Toată echipa"),
        ("Optimizare prompts cu A/B testing via prompt_testing scripts", "PLANNED", "Rareș"),
        ("Production deployment cu docker-compose.prod.yml overlay", "PLANNED", "Toată echipa"),
        ("Kubernetes manifests (k8s/) pentru scalare", "PLANNED", "Toată echipa"),
        ("Security audit: input validation, rate limiting, CORS", "PLANNED", "Francisc"),
    ]),
]

for sprint_name, status, status_color, tasks in sprints:
    p_sp = doc.add_paragraph()
    add_paragraph_shading(p_sp, "1A2B4C")
    p_sp.paragraph_format.space_before = Pt(12)
    p_sp.paragraph_format.space_after  = Pt(4)
    p_sp.paragraph_format.left_indent  = Cm(0.3)
    rs = p_sp.add_run(f"  {sprint_name}   ")
    rs.bold = True; rs.font.size = Pt(12); rs.font.color.rgb = WHITE
    rb = p_sp.add_run(f"[{status}]")
    rb.bold = True; rb.font.size = Pt(10)
    rb.font.color.rgb = RGBColor(int(status_color[:2],16), int(status_color[2:4],16), int(status_color[4:],16))

    t_sp = doc.add_table(rows=len(tasks)+1, cols=3)
    t_sp.style = "Table Grid"
    for j, h in enumerate(["Task", "Status", "Responsabil"]):
        set_cell_bg(t_sp.rows[0].cells[j], "2C3E50")
        rr = t_sp.rows[0].cells[j].paragraphs[0].add_run(h)
        rr.bold = True; rr.font.size = Pt(9); rr.font.color.rgb = WHITE

    for i, (task, st, owner) in enumerate(tasks):
        row = t_sp.rows[i+1]
        if st == "DONE":
            bg_st = "EAFAF1"; st_color = "27AE60"
        elif st == "TODO":
            bg_st = "FEF9E7"; st_color = "E67E22"
        else:
            bg_st = "EBF5FB"; st_color = "2E4A8A"
        bg = "F8F9FA" if i % 2 == 0 else "FFFFFF"
        set_cell_bg(t_sp.rows[i+1].cells[0], bg)
        set_cell_bg(t_sp.rows[i+1].cells[1], bg_st)
        set_cell_bg(t_sp.rows[i+1].cells[2], bg)
        rt = row.cells[0].paragraphs[0].add_run(task)
        rt.font.size = Pt(9); rt.font.color.rgb = DARK_TEXT
        rs_cell = row.cells[1].paragraphs[0].add_run(st)
        rs_cell.bold = True; rs_cell.font.size = Pt(9)
        rs_cell.font.color.rgb = RGBColor(int(st_color[:2],16), int(st_color[2:4],16), int(st_color[4:],16))
        ro = row.cells[2].paragraphs[0].add_run(owner)
        ro.font.size = Pt(9); ro.font.color.rgb = DARK_TEXT

    t_sp.columns[0].width = Cm(10)
    t_sp.columns[1].width = Cm(2.5)
    t_sp.columns[2].width = Cm(3.5)
    spacer()

doc.add_page_break()

# ══════════════════════════════════════════════════════════════════════════════
# 7. DIAGRAMA FLUX EVENT
# ══════════════════════════════════════════════════════════════════════════════
heading1("7. DIAGRAMA FLUX EVENT — REDPANDA TOPICS")
spacer()

info_box(
    "Diagrama de mai jos ilustrează fluxul complet al unui CV prin sistemul CareerPath AI. "
    "Fiecare săgeată reprezintă un eveniment publicat pe un topic Redpanda."
)
spacer()

flow_steps = [
    ("UTILIZATOR", "Upload CV (PDF)", "Frontend → API Gateway → cv-service", "3000→8000→8002", "1E8449"),
    ("cv-service", "Extrage text PDF + salvează MinIO", "Publică: cv.uploaded {text, user_id}", "Topic: cv.uploaded", "1E5276"),
    ("cv-analyzer-agent", "Gemini: scoring + gap analysis\nEmbedding → Qdrant\nPersistare → PostgreSQL", "Publică: cv.analyzed {score, seniority, gaps}", "Topic: cv.analyzed", "6E2F8A"),
    ("agent-orchestrator", "Evaluează scorul CV:\n● scor ≥ 70 → ruta job matching\n● scor < 70 → ruta learning", "Publică pe topicul corespunzător", "Routing logic", "1A2B4C"),
    ("job-match-agent\n(dacă scor ≥ 70)", "Căutare semantică Qdrant\nReranking cu Gemini", "Publică: jobs.matched {top5 jobs}", "Topic: jobs.matched", "2E4A8A"),
    ("learning-path-agent\n(dacă scor < 70)", "Generare traseu personalizat\nResurse Udemy/YouTube", "Publică: learning.path.created", "Topic: learning.path.created", "922B21"),
    ("notification-service", "Consumă rezultatele", "SSE push la frontend", "Port 8004 → Port 3000", "424949"),
    ("UTILIZATOR", "Primește rezultatele în dashboard", "Scor CV + joburi / learning path", "Frontend Dashboard", "1E8449"),
]

for i, (actor, action, output, topic, color) in enumerate(flow_steps):
    row_t = doc.add_table(rows=1, cols=4)
    row_t.style = "Table Grid"
    row_t.alignment = WD_TABLE_ALIGNMENT.CENTER
    cells = row_t.rows[0].cells

    set_cell_bg(cells[0], color)
    set_cell_bg(cells[1], "F8F9FA")
    set_cell_bg(cells[2], "F8F9FA")
    set_cell_bg(cells[3], "E8EAF6")

    ra = cells[0].paragraphs[0].add_run(actor)
    ra.bold = True; ra.font.size = Pt(9); ra.font.color.rgb = WHITE

    rb = cells[1].paragraphs[0].add_run(action)
    rb.font.size = Pt(8.5); rb.font.color.rgb = DARK_TEXT

    rc = cells[2].paragraphs[0].add_run(output)
    rc.font.size = Pt(8.5); rc.font.color.rgb = DARK_TEXT; rc.italic = True

    rd = cells[3].paragraphs[0].add_run(topic)
    rd.bold = True; rd.font.size = Pt(8.5); rd.font.color.rgb = MID_BLUE

    row_t.columns[0].width = Cm(3.5)
    row_t.columns[1].width = Cm(5)
    row_t.columns[2].width = Cm(5.5)
    row_t.columns[3].width = Cm(2)

    if i < len(flow_steps)-1:
        arr = doc.add_paragraph("                                              ↓")
        arr.paragraph_format.space_before = Pt(0)
        arr.paragraph_format.space_after  = Pt(0)
        arr.runs[0].font.size = Pt(14)
        arr.runs[0].font.color.rgb = MID_BLUE
        arr.runs[0].bold = True

doc.add_page_break()

# ══════════════════════════════════════════════════════════════════════════════
# 8. INFRASTRUCTURA DOCKER
# ══════════════════════════════════════════════════════════════════════════════
heading1("8. INFRASTRUCTURA DOCKER COMPOSE")
spacer()

body(
    "Sistemul folosește Docker Compose cu profile dedicate. Infrastructura (PostgreSQL, Redis, "
    "Qdrant, Redpanda, MinIO, Keycloak) pornește cu orice profil. Serviciile aplicative "
    "pornesc selectiv în funcție de profilul ales."
)
spacer()

profiles_data = [
    ("--profile agents", "Rareș", "6E2F8A", "cv-analyzer-agent (8006), agent-orchestrator (8005), learning-path-agent (8007), job-match-agent (8008), hr-interview-agent (8009), technical-interview-agent (8010) + toată infrastructura"),
    ("--profile backend", "Francisc", "1E5276", "user-service (8001), cv-service (8002), job-scraper-service (8003), notification-service (8004), api-gateway (8000) + toată infrastructura"),
    ("--profile frontend", "Vlad", "1E8449", "frontend (3000), api-gateway (8000), user-service (8001) + toată infrastructura"),
    ("--profile observability", "Toată echipa", "424949", "otel-collector (4317/4318), prometheus (9090), loki (3100), tempo (3200), grafana (3001) + toată infrastructura"),
    ("(fără profil)", "Infrastructură", "922B21", "postgres (5432), redis (6379), qdrant (6333), redpanda (19092), redpanda-console (8080), minio (9001), keycloak (8484)"),
]

t9 = doc.add_table(rows=len(profiles_data)+1, cols=4)
t9.style = "Table Grid"
for j, h in enumerate(["Comandă Profil", "Developer", "Servicii Pornite", ""]):
    set_cell_bg(t9.rows[0].cells[j], "1A2B4C")
    rr = t9.rows[0].cells[j].paragraphs[0].add_run(h if h else "")
    rr.bold = True; rr.font.size = Pt(9); rr.font.color.rgb = WHITE

for i, (cmd, dev, color, svcs) in enumerate(profiles_data):
    row = t9.rows[i+1]
    bg = "F0F4F8" if i % 2 == 0 else "FFFFFF"
    set_cell_bg(row.cells[0], color)
    set_cell_bg(row.cells[1], bg)
    set_cell_bg(row.cells[2], bg)
    set_cell_bg(row.cells[3], bg)
    rc = row.cells[0].paragraphs[0].add_run(cmd)
    rc.bold = True; rc.font.size = Pt(8.5); rc.font.color.rgb = WHITE
    rd = row.cells[1].paragraphs[0].add_run(dev)
    rd.font.size = Pt(9); rd.font.color.rgb = DARK_TEXT
    rs = row.cells[2].paragraphs[0].add_run(svcs)
    rs.font.size = Pt(8.5); rs.font.color.rgb = DARK_TEXT

t9.columns[0].width = Cm(3.5)
t9.columns[1].width = Cm(2.5)
t9.columns[2].width = Cm(9.5)
t9.columns[3].width = Cm(0.5)

spacer()
heading3("Comenzi rapide uzuale")
commands = [
    ("make up", "Pornește tot (toate profilele) cu rebuild"),
    ("make down", "Oprește toate containerele"),
    ("make logs-cv", "Tail logs cv-service + cv-analyzer-agent"),
    ("make logs-agents", "Tail logs orchestrator + toți agenții AI"),
    ("make clean", "Șterge containere, volume, imagini"),
    ("docker compose --profile agents up -d --build", "Pornește doar agenții AI (Rareș)"),
    ("docker compose --profile backend up -d", "Pornește doar backend core (Francisc)"),
]
for cmd, desc in commands:
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Cm(0.5)
    p.paragraph_format.space_before = Pt(1)
    add_paragraph_shading(p, "F0F4F8")
    rc = p.add_run(f"$ {cmd}")
    rc.bold = True; rc.font.size = Pt(9)
    rc.font.name = "Courier New"; rc.font.color.rgb = MID_BLUE
    rd = p.add_run(f"  —  {desc}")
    rd.font.size = Pt(9); rd.font.color.rgb = MED_TEXT

# ── Footer note ───────────────────────────────────────────────────────────────
spacer(2)
p_end = doc.add_paragraph()
p_end.alignment = WD_ALIGN_PARAGRAPH.CENTER
add_paragraph_shading(p_end, "1A2B4C")
p_end.paragraph_format.space_before = Pt(8)
p_end.paragraph_format.space_after  = Pt(8)
re = p_end.add_run("CareerPath AI  ·  Document Arhitectural v1.0  ·  Aprilie 2026  ·  Rareș · Francisc · Vlad")
re.font.size = Pt(9); re.font.color.rgb = RGBColor(0xB8, 0xD4, 0xFF)

# ── Save ──────────────────────────────────────────────────────────────────────
output_path = r"C:\Rares\Carrer_Path\CareerPathAI_Arhitectura.docx"
doc.save(output_path)
print(f"Salvat: {output_path}")
