"use client";

import React, { useState, useRef, useEffect } from "react";
import Link from "next/link";
import {
  Zap,
  User,
  Plus,
  MapPin,
  Target,
  Sparkles,
  Save,
  ChevronDown,
  Briefcase,
  X,
  CheckCircle2,
  Award,
  GraduationCap,
  Building2,
  ArrowRight,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { ChatPanel } from "@/components/chat-panel";
import { useAuthStore } from "@/store/auth.store";
import { getLearningPath, getJobMatches, regenerateLearningPath, LearningPath } from "@/lib/api-client";

// --- MOCK DATA ---
const POPULAR_CITIES = [
  "București, RO", "Cluj-Napoca, RO", "Timișoara, RO", "Iași, RO", 
  "London, UK", "New York, US", "Berlin, DE", "Amsterdam, NL"
];

const POPULAR_ROLES = [
  "Frontend Developer", "Backend Developer", "Fullstack Engineer", 
  "DevOps Engineer", "UI/UX Designer", "Product Manager", 
  "Data Scientist", "QA Automation"
];

interface ProfileData {
  fullName: string;
  role: string;
  location: string;
  workPreference: string;
  seniority: string;
  discovery: {
    passion: string[];
    industry: string[];
    environment: string[];
  };
}

// Cheia sub care vom salva datele in browser
const STORAGE_KEY = "careerpath_user_profile";

interface CvSnapshot {
  score: number | null;
  seniority: string | null;
  targetRole?: string;
  strengths: string[];
  gaps: string[];
  analyzedAt?: number;
}

interface CareerSnapshot {
  cv: CvSnapshot | null;
  path: LearningPath | null;
  completedCount: number;
  totalModules: number;
  nextModuleId: string | null;
  jobsCount: number;
}

function loadCvSnapshot(): CvSnapshot | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem("careerpath_cv_analysis");
    if (!raw) return null;
    return JSON.parse(raw) as CvSnapshot;
  } catch {
    return null;
  }
}

export default function DashboardPage() {
  const [profile, setProfile] = useState<ProfileData>({
    fullName: "",
    role: "",
    location: "",
    workPreference: "",
    seniority: "",
    discovery: {
      passion: [],
      industry: [],
      environment: []
    }
  });

  const [isSaving, setIsSaving] = useState(false);
  const [isSaved, setIsSaved] = useState(false);
  const [isLoaded, setIsLoaded] = useState(false);
  const [isRegenerating, setIsRegenerating] = useState(false);
  const [regenerateError, setRegenerateError] = useState<string | null>(null);
  const [pathRefreshKey, setPathRefreshKey] = useState(0);
  const [snapshot, setSnapshot] = useState<CareerSnapshot>({
    cv: null,
    path: null,
    completedCount: 0,
    totalModules: 0,
    nextModuleId: null,
    jobsCount: 0,
  });
  const authUser = useAuthStore((s) => s.user);

  const firstName = (authUser?.name || profile.fullName || "").trim().split(" ")[0];
  const greeting = firstName ? `Welcome back, ${firstName}!` : "Welcome to your profile";

  useEffect(() => {
    const savedProfile = localStorage.getItem(STORAGE_KEY);
    let parsed: ProfileData | null = null;
    if (savedProfile) {
      try {
        parsed = JSON.parse(savedProfile);
      } catch (error) {
        console.error("Failed to parse profile data", error);
      }
    }

    // Pre-fill from CV analysis any fields the user hasn't filled yet.
    // Mapează: target_role → role, seniority CV → seniority.
    const cv = loadCvSnapshot();
    const merged: ProfileData = parsed ?? {
      fullName: "",
      role: "",
      location: "",
      workPreference: "",
      seniority: "",
      discovery: { passion: [], industry: [], environment: [] },
    };
    if (cv) {
      if (!merged.role && cv.targetRole) merged.role = cv.targetRole;
      if (!merged.seniority && cv.seniority) {
        merged.seniority = cv.seniority.charAt(0).toUpperCase() + cv.seniority.slice(1).toLowerCase();
      }
    }
    if (authUser?.name && !merged.fullName) merged.fullName = authUser.name;

    setProfile(merged);
    setIsLoaded(true);
  }, [authUser?.name]);

  // Persistă automat orice schimbare după hidratare — fără apăsare manuală.
  useEffect(() => {
    if (!isLoaded) return;
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(profile));
    } catch {}
  }, [profile, isLoaded]);

  useEffect(() => {
    if (!authUser?.id) return;
    const cv = loadCvSnapshot();
    let cancelled = false;

    async function fetchCareer() {
      let path: LearningPath | null = null;
      let totalModules = 0;
      let completedCount = 0;
      let nextModuleId: string | null = null;
      let jobsCount = 0;

      try {
        path = await getLearningPath(authUser!.id);
        const completed: string[] = JSON.parse(localStorage.getItem("completed_modules") || "[]");
        for (const week of path.weekly_plan || []) {
          week.modules.forEach((_, mi) => {
            const id = `w${week.week}-m${mi}`;
            totalModules += 1;
            if (completed.includes(id)) {
              completedCount += 1;
            } else if (!nextModuleId) {
              nextModuleId = id;
            }
          });
        }
      } catch {
        // 404 = no path yet; leave defaults
      }

      try {
        const jobs = await getJobMatches(authUser!.id);
        jobsCount = jobs?.count ?? 0;
      } catch {
        // 404 = no jobs yet
      }

      if (cancelled) return;
      setSnapshot({ cv, path, totalModules, completedCount, nextModuleId, jobsCount });
    }

    fetchCareer();
    return () => {
      cancelled = true;
    };
  }, [authUser?.id, pathRefreshKey]);

  const handleRegeneratePath = async () => {
    if (!authUser?.id) return;
    const newRole = profile.role.trim();
    if (!newRole) {
      setRegenerateError("Selectează un Target Role mai întâi.");
      return;
    }
    setIsRegenerating(true);
    setRegenerateError(null);
    try {
      const cv = loadCvSnapshot();
      await regenerateLearningPath(authUser.id, newRole, cv?.gaps);
      // Update the cached CV snapshot so the snapshot card stops showing the
      // old role (it falls back to cv.targetRole before path.target_role).
      if (cv) {
        try {
          localStorage.setItem(
            "careerpath_cv_analysis",
            JSON.stringify({ ...cv, targetRole: newRole }),
          );
        } catch {}
      }
      setPathRefreshKey((k) => k + 1);
    } catch (err: any) {
      const msg =
        err?.response?.data?.detail ||
        err?.message ||
        "Nu am putut regenera materia.";
      setRegenerateError(typeof msg === "string" ? msg : "Eroare necunoscută.");
    } finally {
      setIsRegenerating(false);
    }
  };

  const handleSave = () => {
    setIsSaving(true);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(profile));

    setTimeout(() => {
      setIsSaving(false);
      setIsSaved(true);
      setTimeout(() => setIsSaved(false), 2000);
    }, 800); 
  };

  if (!isLoaded) return null; 

  return (
    <div className="w-full max-w-[1440px] mx-auto space-y-10 animate-in fade-in duration-700 pb-24">
      
      {/* --- CHENAR DESIGN TITLU UNIFICAT --- */}
      <div className="flex justify-between items-center bg-[#0b0f1a]/60 border border-white/5 p-5 rounded-[24px] shadow-lg backdrop-blur-xl">
        <div className="space-y-1">
          <div className="flex items-center gap-2 text-indigo-400 mb-1">
             <Sparkles size={16} className="fill-current" />
             <span className="text-[10px] font-black uppercase tracking-[0.3em]">Identity Hub</span>
          </div>
          <h1 className="text-2xl font-black tracking-tight text-white uppercase leading-none">{greeting}</h1>
        </div>
      </div>

      {/* --- CAREER SNAPSHOT --- live data from CV analysis + learning path + jobs */}
      <CareerSnapshotStrip snapshot={snapshot} />

      {/* --- MAIN GRID (7 / 5) --- */}
      <div className="grid grid-cols-1 xl:grid-cols-12 gap-8 items-start">
        
        {/* === LEFT COLUMN: PROFILE EDITOR (7 Cols) === */}
        <div className="xl:col-span-7 flex flex-col bg-[#0b0f1a]/80 border border-white/[0.06] rounded-[40px] backdrop-blur-2xl shadow-[0_0_80px_rgba(0,0,0,0.4)] overflow-visible">
          
          <div className="p-8 sm:p-10 space-y-10">
            {/* Secțiunea 1: Basic Info */}
            <div>
              <div className="flex items-center gap-4 mb-8">
                <div className="w-12 h-12 rounded-[16px] bg-indigo-500/10 flex items-center justify-center text-indigo-400 border border-indigo-500/20 shadow-inner">
                  <User size={20} />
                </div>
                <div>
                  <h2 className="text-xl font-black uppercase tracking-tight text-white leading-none">Professional Identity</h2>
                  <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mt-1.5">Manual Configuration</p>
                </div>
              </div>

              {/* Grid Formular Perfect Aliniat */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 relative z-20">
                <EditableField label="Full Name" value={profile.fullName} onChange={(v) => setProfile({...profile, fullName: v})} placeholder="John Doe" />
                
                <div className="flex flex-col gap-2">
                  <SmartSearchDropdown
                    label="Target Role"
                    icon={<Briefcase size={16} className="text-slate-500" />}
                    placeholder="e.g. Frontend Developer"
                    options={POPULAR_ROLES}
                    value={profile.role}
                    onChange={(v) => setProfile({...profile, role: v})}
                  />
                  {(() => {
                    const currentPathRole = (snapshot.path?.target_role || "").trim();
                    const chosen = profile.role.trim();
                    const roleChanged =
                      chosen.length > 0 && chosen.toLowerCase() !== currentPathRole.toLowerCase();
                    return (
                      <>
                        <button
                          type="button"
                          onClick={handleRegeneratePath}
                          disabled={isRegenerating || !roleChanged}
                          className={cn(
                            "self-start text-[10px] font-black uppercase tracking-widest px-3 py-1.5 rounded-lg transition-colors border",
                            isRegenerating
                              ? "border-indigo-500/30 text-indigo-300 cursor-wait"
                              : roleChanged
                              ? "border-indigo-500/40 text-indigo-300 hover:bg-indigo-500/10"
                              : "border-white/5 text-slate-600 cursor-not-allowed",
                          )}
                        >
                          {isRegenerating
                            ? "Regenerating curriculum..."
                            : roleChanged
                            ? "Apply & regenerate curriculum"
                            : currentPathRole
                            ? `Curriculum aligned with "${currentPathRole}"`
                            : "Pick a role to generate"}
                        </button>
                        {regenerateError && (
                          <p className="text-[10px] text-red-400 font-medium">{regenerateError}</p>
                        )}
                      </>
                    );
                  })()}
                </div>
                
                <SmartSearchDropdown 
                  label="Location"
                  icon={<MapPin size={16} className="text-slate-500" />}
                  placeholder="Global hotspots..."
                  options={POPULAR_CITIES}
                  value={profile.location} 
                  onChange={(v) => setProfile({...profile, location: v})} 
                />

                <div className="grid grid-cols-2 gap-4 relative z-10">
                  <StyledSelect 
                    label="Seniority" 
                    options={["Junior", "Mid-Level", "Senior", "Lead"]} 
                    value={profile.seniority}
                    onChange={(v) => setProfile({...profile, seniority: v})}
                  />
                  <StyledSelect 
                    label="Preference" 
                    options={["Remote", "Flexible", "On-site"]} 
                    value={profile.workPreference}
                    onChange={(v) => setProfile({...profile, workPreference: v})}
                  />
                </div>
              </div>
            </div>

            {/* Linia despărțitoare fină */}
            <div className="h-px w-full bg-gradient-to-r from-transparent via-white/10 to-transparent" />

            {/* Secțiunea 2: Discovery */}
            <div className="relative z-0">
              <div className="flex items-center gap-4 mb-8">
                <div className="w-12 h-12 rounded-[16px] bg-emerald-500/10 flex items-center justify-center text-emerald-400 border border-emerald-500/20 shadow-inner">
                  <Target size={20} />
                </div>
                <div>
                  <h3 className="text-xl font-black uppercase tracking-tight text-white leading-none">Career Discovery</h3>
                  <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mt-1.5">Context for AI Matching</p>
                </div>
              </div>
              
              <div className="space-y-8">
                <DiscoveryTagInput 
                  question="What kind of projects truly spark your interest?" 
                  values={profile.discovery.passion} 
                  onChange={(v) => setProfile({...profile, discovery: {...profile.discovery, passion: v}})} 
                  suggestions={["SaaS Platforms", "AI Integrations", "E-commerce UIs", "Hardware-Software"]}
                />
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                  <DiscoveryTagInput 
                    question="Preferred Industry?" 
                    values={profile.discovery.industry} 
                    onChange={(v) => setProfile({...profile, discovery: {...profile.discovery, industry: v}})} 
                    suggestions={["Fintech", "Healthtech", "Gaming"]}
                  />
                  <DiscoveryTagInput 
                    question="Ideal Team Culture?" 
                    values={profile.discovery.environment} 
                    onChange={(v) => setProfile({...profile, discovery: {...profile.discovery, environment: v}})} 
                    suggestions={["Startup", "Corporate Agile", "Remote"]}
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Footer */}
          <div className="px-8 py-5 bg-[#0b0f1a] border-t border-white/[0.06] rounded-b-[40px] flex flex-col sm:flex-row justify-between items-center gap-4 shrink-0">
            <div className="flex items-center gap-2">
              <div className="w-1.5 h-1.5 rounded-full bg-indigo-500 animate-pulse shadow-[0_0_8px_#6366f1]" />
              <span className="text-[9px] font-black text-slate-500 uppercase tracking-[0.2em]">Data structured for AI Engine</span>
            </div>
            <button 
              onClick={handleSave}
              disabled={isSaving || isSaved}
              className={cn(
                "px-8 py-3.5 rounded-[16px] font-black text-[11px] uppercase tracking-[0.15em] transition-all flex items-center gap-2.5 shadow-xl outline-none",
                isSaved 
                  ? "bg-emerald-500 text-white shadow-emerald-500/25" 
                  : isSaving
                    ? "bg-white/10 text-white cursor-wait"
                    : "bg-white text-black hover:bg-indigo-500 hover:text-white hover:shadow-indigo-500/25 active:scale-[0.98]"
              )}
            >
              {isSaved ? (
                <><CheckCircle2 size={16} /> Profile Synced</>
              ) : isSaving ? (
                <><Zap size={16} className="animate-bounce" /> Syncing...</>
              ) : (
                <><Save size={16} /> Save Changes</>
              )}
            </button>
          </div>
        </div>

        {/* === RIGHT COLUMN: AI COPILOT CHAT (5 Cols) === */}
        {/* CORECTAT ACUM: Integrat design-ul 100% identic de pe Home Page */}
        <div className="xl:col-span-5 h-[500px] flex flex-col bg-[#0b0f1a]/60 border border-white/10 backdrop-blur-3xl rounded-[40px] overflow-hidden shadow-2xl border-t border-l border-white/20 relative">
          
          <div className="px-6 py-4 border-b border-white/5 flex items-center justify-between bg-white/[0.01] shrink-0">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-indigo-500/10 flex items-center justify-center text-indigo-400 border border-indigo-500/20 shadow-inner">
                <Sparkles size={14} />
              </div>
              <span className="text-xs font-black tracking-widest uppercase text-slate-200">AI Assistant</span>
            </div>
            <div className="flex items-center gap-1.5">
               <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 shadow-[0_0_5px_#10b981]" />
               <span className="text-[9px] font-black text-slate-500 uppercase tracking-widest">LIVE</span>
            </div>
          </div>

          <div className="flex-1 overflow-hidden min-h-0">
             <ChatPanel />
          </div>
        </div>

      </div>
    </div>
  );
}

// --- CAREER SNAPSHOT STRIP --- real data from CV analysis + learning + jobs

function CareerSnapshotStrip({ snapshot }: { snapshot: CareerSnapshot }) {
  const { cv, path, completedCount, totalModules, nextModuleId, jobsCount } = snapshot;
  const hasAnything = cv || path || totalModules > 0;

  if (!hasAnything) {
    return (
      <div className="bg-[#0b0f1a]/40 border border-dashed border-white/10 rounded-[24px] p-6 flex items-center justify-between">
        <div className="space-y-1">
          <p className="text-[10px] font-black text-slate-500 uppercase tracking-[0.3em]">Career snapshot</p>
          <p className="text-sm font-medium text-slate-400">Upload your CV to populate this section.</p>
        </div>
        <Link
          href="/upload"
          className="px-5 py-2.5 bg-white text-black rounded-[12px] font-black text-[10px] uppercase tracking-[0.2em] hover:bg-indigo-500 hover:text-white transition-all flex items-center gap-2"
        >
          Upload CV <ArrowRight size={12} />
        </Link>
      </div>
    );
  }

  const score = cv?.score ?? null;
  const scoreColor = score === null
    ? "text-slate-500"
    : score >= 75
      ? "text-emerald-400"
      : score >= 55
        ? "text-amber-400"
        : "text-red-400";

  const targetRole = cv?.targetRole || path?.target_role || "—";
  const learningProgress = totalModules > 0 ? Math.round((completedCount / totalModules) * 100) : 0;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
      <SnapshotCard icon={<Award size={16} />} accent="indigo" label="CV Score">
        <p className={cn("text-3xl font-black leading-none", scoreColor)}>
          {score ?? "—"}<span className="text-xl text-slate-500">/100</span>
        </p>
        <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mt-1.5">
          {cv?.seniority ? `${cv.seniority} • ${cv.gaps.length} gaps` : "Awaiting analysis"}
        </p>
      </SnapshotCard>

      <SnapshotCard icon={<Briefcase size={16} />} accent="emerald" label="Target Role">
        <p className="text-base font-black text-white leading-tight truncate" title={targetRole}>
          {targetRole}
        </p>
        <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mt-1.5">
          {path?.estimated_weeks ? `${path.estimated_weeks} week plan` : "From CV analysis"}
        </p>
      </SnapshotCard>

      <SnapshotCard icon={<GraduationCap size={16} />} accent="violet" label="Learning Progress">
        <p className="text-3xl font-black leading-none text-white">
          {completedCount}<span className="text-xl text-slate-500">/{totalModules || "—"}</span>
        </p>
        <div className="w-full h-1 bg-white/5 rounded-full overflow-hidden mt-2">
          <div className="h-full bg-violet-500 transition-all duration-700" style={{ width: `${learningProgress}%` }} />
        </div>
      </SnapshotCard>

      <SnapshotCard icon={<Building2 size={16} />} accent="amber" label="Jobs Matched">
        <p className="text-3xl font-black leading-none text-white">
          {jobsCount}
        </p>
        <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mt-1.5">
          {jobsCount > 0 ? "Tap Jobs in sidebar" : "Awaiting score ≥ 70"}
        </p>
      </SnapshotCard>

      {nextModuleId && (
        <div className="col-span-full bg-gradient-to-r from-indigo-500/10 via-violet-500/10 to-transparent border border-indigo-500/20 rounded-[20px] p-5 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3 min-w-0">
            <div className="w-10 h-10 rounded-[14px] bg-indigo-500/15 border border-indigo-500/30 text-indigo-400 flex items-center justify-center shrink-0">
              <Zap size={16} className="fill-current" />
            </div>
            <div className="min-w-0">
              <p className="text-[10px] font-black text-indigo-300 uppercase tracking-[0.3em] mb-0.5">Next up</p>
              <p className="text-sm font-bold text-white truncate">Continue your learning path</p>
            </div>
          </div>
          <Link
            href="/learning/path"
            className="shrink-0 px-5 py-2.5 bg-white text-black rounded-[12px] font-black text-[10px] uppercase tracking-[0.2em] hover:bg-indigo-500 hover:text-white transition-all flex items-center gap-2"
          >
            Continue <ArrowRight size={12} />
          </Link>
        </div>
      )}
    </div>
  );
}

function SnapshotCard({
  icon,
  label,
  accent,
  children,
}: {
  icon: React.ReactNode;
  label: string;
  accent: "indigo" | "emerald" | "violet" | "amber";
  children: React.ReactNode;
}) {
  const tone = {
    indigo: "bg-indigo-500/10 border-indigo-500/20 text-indigo-400",
    emerald: "bg-emerald-500/10 border-emerald-500/20 text-emerald-400",
    violet: "bg-violet-500/10 border-violet-500/20 text-violet-400",
    amber: "bg-amber-500/10 border-amber-500/20 text-amber-400",
  }[accent];

  return (
    <div className="bg-[#0b0f1a]/80 border border-white/5 rounded-[24px] p-5 backdrop-blur-xl">
      <div className="flex items-center gap-3 mb-4">
        <div className={cn("w-9 h-9 rounded-[12px] flex items-center justify-center border", tone)}>
          {icon}
        </div>
        <p className="text-[10px] font-black text-slate-500 uppercase tracking-[0.3em]">{label}</p>
      </div>
      {children}
    </div>
  );
}

// --- STANDARD UI COMPONENTS (Anti-OCD Pass) ---

function EditableField({ label, value, onChange, placeholder }: { label: string, value: string, onChange: (v: string) => void, placeholder?: string }) {
  return (
    <div className="flex flex-col gap-2 group">
      <label className="text-[10px] font-bold text-slate-400 uppercase tracking-widest ml-1">{label}</label>
      <input 
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full bg-white/[0.03] border border-white/[0.08] hover:border-white/[0.15] focus:bg-white/[0.05] focus:border-indigo-500/50 rounded-[16px] px-5 py-3.5 text-sm font-medium text-white outline-none transition-all placeholder:text-slate-600"
      />
    </div>
  );
}

function StyledSelect({ label, options, value, onChange }: { label: string, options: string[], value: string, onChange: (v: string) => void }) {
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) setIsOpen(false);
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <div className="flex flex-col gap-2 relative" ref={containerRef}>
      <label className="text-[10px] font-bold text-slate-400 uppercase tracking-widest ml-1">{label}</label>
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className="w-full bg-white/[0.03] border border-white/[0.08] hover:border-white/[0.15] rounded-[16px] px-5 py-3.5 text-sm font-medium text-white flex justify-between items-center transition-all outline-none"
      >
        <span className="truncate">{value || "Select..."}</span>
        <ChevronDown size={16} className={cn("text-slate-500 transition-transform duration-300", isOpen && "rotate-180")} />
      </button>
      
      {isOpen && (
        <div className="absolute top-[calc(100%+8px)] left-0 right-0 bg-[#0b0f1a] border border-white/10 rounded-[20px] shadow-[0_10px_40px_rgba(0,0,0,0.5)] z-[100] p-1.5 animate-in fade-in slide-in-from-top-2">
          {options.map((opt) => (
            <button 
              key={opt}
              onClick={() => { onChange(opt); setIsOpen(false); }}
              className="w-full px-4 py-2.5 text-left text-xs font-medium text-slate-300 hover:bg-white/5 hover:text-white rounded-[12px] transition-colors"
            >
              {opt}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

function SmartSearchDropdown({ label, value, onChange, options, placeholder, icon }: { label: string, value: string, onChange: (v: string) => void, options: string[], placeholder: string, icon: React.ReactNode }) {
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState(value);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) setIsOpen(false);
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const filtered = query === "" 
    ? options.slice(0, 4) 
    : options.filter(o => o.toLowerCase().includes(query.toLowerCase()));

  return (
    <div className="flex flex-col gap-2 relative" ref={containerRef}>
      <label className="text-[10px] font-bold text-slate-400 uppercase tracking-widest ml-1">{label}</label>
      <div className="relative group">
        <div className="absolute left-5 top-1/2 -translate-y-1/2 pointer-events-none transition-colors group-focus-within:text-indigo-400">
          {icon}
        </div>
        <input
          placeholder={placeholder}
          value={query}
          onFocus={() => setIsOpen(true)}
          onChange={(e) => {
            const next = e.target.value;
            setQuery(next);
            onChange(next); // commit live so custom values aren't lost
            setIsOpen(true);
          }}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              e.preventDefault();
              onChange(query);
              setIsOpen(false);
            }
          }}
          className="w-full bg-white/[0.03] border border-white/[0.08] hover:border-white/[0.15] focus:bg-white/[0.05] focus:border-indigo-500/50 rounded-[16px] pl-12 pr-5 py-3.5 text-sm font-medium text-white outline-none transition-all placeholder:text-slate-600"
        />
      </div>

      {isOpen && (
        <div className="absolute top-[calc(100%+8px)] left-0 right-0 bg-[#0b0f1a] border border-white/10 rounded-[20px] shadow-[0_10px_40px_rgba(0,0,0,0.5)] z-[100] p-1.5 max-h-64 overflow-y-auto custom-scrollbar animate-in fade-in slide-in-from-top-2">
          <div className="px-3 py-2 text-[9px] font-black text-slate-600 uppercase tracking-widest mb-1">
            {query === "" ? "Suggestions" : "Results"}
          </div>
          {filtered.length > 0 ? filtered.map((item) => (
            <button
              key={item}
              onClick={() => { onChange(item); setQuery(item); setIsOpen(false); }}
              className="w-full px-3 py-2.5 text-left text-xs font-medium text-slate-300 hover:bg-white/5 hover:text-white rounded-[12px] transition-colors flex items-center justify-between group/item"
            >
              {item}
              <Plus size={12} className="opacity-0 group-hover/item:opacity-100 text-indigo-400 transition-opacity" />
            </button>
          )) : (
            <div className="px-3 py-2.5 text-xs font-medium text-slate-500 italic">Press enter or click outside to use "{query}".</div>
          )}
        </div>
      )}
    </div>
  );
}

function DiscoveryTagInput({ question, values, onChange, suggestions }: { question: string, values: string[], onChange: (v: string[]) => void, suggestions: string[] }) {
  const [inputValue, setInputValue] = useState("");

  const handleAdd = (val: string) => {
    const trimmed = val.trim();
    if (trimmed && !values.includes(trimmed)) onChange([...values, trimmed]);
    setInputValue("");
  };

  const handleRemove = (valToRemove: string) => {
    onChange(values.filter(v => v !== valToRemove));
  };

  return (
    <div className="flex flex-col gap-2">
      <label className="text-[11px] font-bold text-slate-400 ml-1 leading-relaxed">{question}</label>
      
      <div 
        className="flex flex-wrap items-center gap-2 p-2 bg-white/[0.03] border border-white/[0.08] rounded-[16px] transition-all hover:border-white/[0.15] focus-within:bg-white/[0.05] focus-within:border-indigo-500/50 min-h-[56px] cursor-text"
        onClick={() => document.getElementById(`tag-${question}`)?.focus()}
      >
        {values.map((val) => (
          <span key={val} className="flex items-center gap-1.5 px-3 py-1.5 bg-indigo-500/15 border border-indigo-500/30 text-indigo-200 rounded-[10px] text-[11px] font-bold tracking-wide animate-in zoom-in duration-200">
            {val}
            <button 
              onClick={(e) => { e.stopPropagation(); handleRemove(val); }} 
              className="hover:bg-indigo-500/40 hover:text-white rounded-full p-0.5 transition-colors"
            >
              <X size={12} />
            </button>
          </span>
        ))}

        <input
          id={`tag-${question}`}
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') { e.preventDefault(); handleAdd(inputValue); }
            if (e.key === 'Backspace' && inputValue === "" && values.length > 0) handleRemove(values[values.length - 1]);
          }}
          onBlur={() => handleAdd(inputValue)}
          placeholder={values.length === 0 ? "Type and press enter..." : ""}
          className="flex-1 bg-transparent border-none outline-none text-sm font-medium text-white min-w-[140px] px-2 placeholder:text-slate-600"
        />
      </div>

      {suggestions && (
        <div className="flex flex-wrap gap-1.5 mt-1 ml-1">
          {suggestions.map((suggestion, i) => {
            const isSelected = values.includes(suggestion);
            return (
              <button
                key={i}
                onMouseDown={(e) => { e.preventDefault(); handleAdd(suggestion); }}
                disabled={isSelected}
                className={cn(
                  "px-2.5 py-1.5 rounded-[8px] text-[9px] font-black uppercase tracking-widest transition-colors border",
                  isSelected 
                    ? "bg-transparent border-transparent text-slate-700 cursor-not-allowed line-through" 
                    : "bg-white/[0.03] border-white/5 text-slate-500 hover:bg-indigo-500/20 hover:text-indigo-300 hover:border-indigo-500/30"
                )}
              >
                + {suggestion}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}