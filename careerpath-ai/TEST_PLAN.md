# Test Plan — CareerPath AI Demo Run

Use this as a checklist while the session recorder is running. For each step,
note in the bottom of this file what actually happened so we can debug after.

## 0. Pre-flight (~2 min)

```powershell
# Terminal A — start the stack:
cd C:\Rares\Carrer_Path\careerpath-ai
make up
make redpanda-topics   # once, only on first start
```

```powershell
# Terminal B — start the session recorder:
cd C:\Rares\Carrer_Path\careerpath-ai
.\scripts\record-session.ps1
```

Wait until `make up` says `✅ Stack is up`. Then open these tabs in the browser
**before** you start clicking (so SSE / WebSocket connections show in DevTools):

- `http://localhost:3000` — frontend
- `http://localhost:8080` — Redpanda Console (to watch topics flow)
- `http://localhost:8025` — MailHog (to see emails the platform sends)
- `http://localhost:8000/health` — should return `{"status":"ok"}`

Open browser DevTools (F12) on the frontend tab → **Network** tab → tick
"Preserve log". This way, even page navigations keep the request history.

## 1. Register + login (~1 min)

1. Click "Register" or go to `/register`.
2. Enter a real email + password (note them down — you'll need them again).
3. Submit. Expect: redirect to `/dashboard` or `/login`.
4. If redirected to login, log in with the same credentials.

**Watch for:**
- 4xx/5xx in Network tab
- Recorder log: `Select-String session-*.log -Pattern 'register|verify-credentials'`

**Expected new behavior:** Dashboard header shows **"Welcome back, {your first
name}!"** instead of "Your Professional Profile".

---

## 2. Dashboard + AI Assistant chat (~2 min)

1. On `/dashboard`, **don't** click any of the 3 suggestion buttons yet — confirm
   they remain visible until you do.
2. Look at the AI assistant chat pane on the right.

**Expected new behavior:**
- First message from AI is **in English** ("Welcome! I'm here to help you shape
  your career path. To start, I'd like to know — are you already working in
  tech, a student, or thinking about a career switch?").
- The 3 buttons ("Find the Right Job for Me", etc.) stay visible.

3. Type a Romanian reply: "Sunt student la informatică, vreau să fac frontend".
4. Verify the AI's next reply switches to **Romanian** and asks a follow-up.
5. After ~2 user turns, check the **Redpanda Console** (`localhost:8080`) for a
   message on topic `profile.extracted`.

**Watch the recorder log:**
```powershell
Select-String session-*.log -Pattern 'profile.extracted|profile updated'
```

---

## 3. CV Upload (~3 min)

1. Click "Upload your CV" CTA (after enough chat turns it appears) or navigate
   to `/upload`.
2. Drag a PDF or click to pick one. Use a real-ish CV — the analyzer needs text.
3. Wait through "Uploading" → "Analyzing" → "Routing".

**Expected new behavior:**
- A score gauge appears.
- **Three new cards below the score:**
  - **Core Strengths** (2-4 bullet points)
  - **Industry Gaps** (2-4 bullet points)
  - **Career Roadmap** (exactly 3 numbered platform-native steps)

**Watch the recorder log:**
```powershell
Select-String session-*.log -Pattern 'cv.analyzed|career_roadmap|gap_analysis'
```

If only the score shows up and the 3 cards are empty, the SSE event isn't
carrying the new fields. Check the Network tab → find the EventSource request
to `/notifications/sse/{userId}` → look at the actual message payload.

---

## 4. HR Behavioral Interview (~5 min)

1. Navigate to `/hr`.
2. If you see "Interview Locked", click "[Dev Unlock]" at the bottom (it's a
   tiny gray button).
3. Wait for the AI Recruiter greeting.

**Expected new behavior:**
- AI message appears **all at once** — no character-by-character animation,
  no progress bar in the header (no "Turn X/15" anymore).
- Only an "End Interview" button.

4. Type 2-3 STAR-style answers (Situation / Task / Action / Result format).
   Example: "When I worked on my graduation project, I had to..."
5. Click **End Interview** before reaching the natural turn limit.

**Expected at end:**
- A big **PASS** or **FAIL** badge (not a numeric score 1-10).
- Evaluator Summary + Key Strengths + Areas for Growth sections.

**Watch the recorder log:**
```powershell
Select-String session-*.log -Pattern 'interview.hr.completed|verdict'
```

In Redpanda Console, the message on `interview.hr.completed` should now have a
`verdict` field with `"PASS"` or `"FAIL"`.

---

## 5. Technical Interview (~5 min)

1. Navigate to `/technical`.
2. Click "[Dev Unlock]" if locked.
3. Wait for the first problem to appear in the left "Problem Info" tab.
4. Write a deliberately wrong solution (e.g., return `[]` for Two Sum) and
   click **Run Code**.
5. Verify: test results show FAIL, but **you stay on the same problem** — no
   auto-advance to a new one. This is the spec's "manual transition" rule.
6. Now write a correct solution. Click Run Code.
7. Expected: a new problem appears in the Problem Info tab automatically (only
   advances on `passed=true`).
8. Solve the second problem. Expected: interview ends + a completed view shows.

**Expected completed view:**
- Big **PASS** or **FAIL** badge (left card)
- Problems Solved counter (e.g., 2/2) + Readiness Level (junior/mid/senior)
- Evaluator Summary
- Strengths + Weaknesses + Optimization Insights sections

**Watch the recorder log:**
```powershell
Select-String session-*.log -Pattern 'interview.tech.completed|readiness_level'
```

---

## 6. Learning Path — Empty state (~1 min)

1. Open a **private/incognito** window → log in as a NEW user (fresh
   `localStorage`).
2. Navigate to `/learning/path` **before** filling profile or chatting.

**Expected new behavior:**
- Instead of "React Architecture & Performance" hardcoded modules, you see:
  > "To receive personalized courses and quizzes, please talk with the AI
  > assistant or complete your profile manually."

With two CTAs: "Talk to AI" + "Fill profile manually".

---

## 7. Jobs label (~10 sec)

1. Navigate to `/jobs`.

**Expected:** Header reads **"Recommended For You"** (not "Job Matches").

---

# After the test — what to send back

Stop the recorder (Ctrl+C in Terminal B). Then:

1. Run the suggested greps the recorder printed at exit.
2. Take a screenshot of any UI that **doesn't match the expected behavior**
   above.
3. Open the latest `logs/session-*.log` and copy:
   - The last ~20 lines
   - Any line containing `ERROR`, `Exception`, or `Traceback`

Paste those back into the chat. That's enough for me to triage.

---

# Test session notes (fill in as you go)

| Step | OK? | What I saw |
|------|-----|------------|
| 0. Pre-flight |   |  |
| 1. Register/login |   |  |
| 2. Dashboard greeting |   |  |
| 2. Language mirroring |   |  |
| 2. `profile.extracted` on Redpanda |   |  |
| 3. CV roadmap 3 cards |   |  |
| 4. HR instant render |   |  |
| 4. HR PASS/FAIL verdict |   |  |
| 5. Tech manual transition |   |  |
| 5. Tech readiness level shown |   |  |
| 6. Learning empty state |   |  |
| 7. Jobs label |   |  |
