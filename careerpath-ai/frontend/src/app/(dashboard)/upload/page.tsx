"use client";

import React, { useState, useRef, useCallback, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  UploadCloud,
  FileText,
  CheckCircle2,
  Loader2,
  AlertCircle,
  X,
  ArrowRight,
  Zap,
  Briefcase,
  BookOpen
} from "lucide-react";
import { cn } from "@/lib/utils";
import { uploadCV } from "@/lib/api-client";
import { useAuthStore } from "@/store/auth.store";
import { CVScoreGauge } from "@/components/ui/cv-score-gauge";

// --- TYPES ---
type UploadStep = "idle" | "uploading" | "analyzing" | "routing" | "completed";
type ErrorType = "file_too_large" | "unsupported_format" | "api_error" | null;

interface SSEEvent {
  type: string;
  data: any;
}

export default function CVUploadPage() {
  const [step, setStep] = useState<UploadStep>("idle");
  const [error, setError] = useState<ErrorType>(null);
  const [score, setScore] = useState<number | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const eventSourceRef = useRef<EventSource | null>(null);
  const router = useRouter();
  const { user } = useAuthStore();

  // --- VALIDATION ---
  const validateFile = (file: File): ErrorType => {
    console.log('File validation:', {
      name: file.name,
      size: file.size,
      type: file.type,
      sizeInMB: (file.size / (1024 * 1024)).toFixed(2) + 'MB'
    });

    if (file.size > 10 * 1024 * 1024) { // 10MB
      return "file_too_large";
    }
    if (!['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'].includes(file.type)) {
      console.log('Unsupported file type:', file.type);
      return "unsupported_format";
    }
    return null;
  };

  // --- SSE HANDLER ---
  const setupSSE = useCallback((userId: string) => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    const eventSource = new EventSource(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'}/notifications/sse/${userId}`);
    eventSourceRef.current = eventSource;

    eventSource.onmessage = (event) => {
      try {
        const sseEvent: SSEEvent = JSON.parse(event.data);
        if (sseEvent.type === 'cv_analyzed') {
          setScore(sseEvent.data.score);
          setStep("completed");
          eventSource.close();
          eventSourceRef.current = null;
        }
      } catch (err) {
        console.error('Error parsing SSE event:', err);
      }
    };

    eventSource.onerror = (err) => {
      console.error('SSE error:', err);
      setError("api_error");
      setStep("idle");
    };
  }, []);

  // --- UPLOAD HANDLER ---
  const handleFileUpload = async (file: File) => {
    const validationError = validateFile(file);
    if (validationError) {
      setError(validationError);
      return;
    }

    setError(null);
    setSelectedFile(file);
    setStep("uploading");

    try {
      const response = await uploadCV(file);
      setJobId(response.job_id);
      setStep("analyzing");

      // Setup SSE after getting job_id
      if (user?.id) {
        setupSSE(user.id);
      }
    } catch (err) {
      console.error('Upload error:', err);
      setError("api_error");
      setStep("idle");
    }
  };

  // --- DRAG AND DROP HANDLERS ---
  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);

    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      handleFileUpload(files[0]);
    }
  }, []);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFileUpload(files[0]);
    }
  };

  // --- CLEANUP ---
  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);

  // --- ERROR MESSAGES ---
  const getErrorMessage = (errorType: ErrorType): string => {
    switch (errorType) {
      case "file_too_large":
        return "File size must be less than 10MB";
      case "unsupported_format":
        return "Only PDF and DOCX files are supported";
      case "api_error":
        return "Upload failed. Please try again.";
      default:
        return "";
    }
  };

  // --- PROGRESS STEPS ---
  const progressSteps = [
    { key: "uploading", label: "Uploading", icon: UploadCloud },
    { key: "analyzing", label: "Analyzing", icon: Zap },
    { key: "routing", label: "Routing", icon: ArrowRight },
  ];

  const getStepStatus = (stepKey: string) => {
    const stepOrder = ["uploading", "analyzing", "routing", "completed"];
    const currentIndex = stepOrder.indexOf(step);
    const stepIndex = stepOrder.indexOf(stepKey);

    if (stepIndex < currentIndex) return "completed";
    if (stepIndex === currentIndex) return "active";
    return "pending";
  };

  return (
    <div className="w-full space-y-10 animate-in fade-in duration-700 pb-20">

      {/* HEADER */}
      <div className="flex justify-between items-end border-b border-white/5 pb-8">
        <div>
          <h1 className="text-4xl font-black uppercase tracking-tighter text-white">
            {step === "completed" ? "Analysis Complete" : "CV Intelligence"}
          </h1>
          <p className="text-[10px] font-black text-slate-500 uppercase tracking-[0.4em] mt-2">
            {step === "completed" ? "Your career path is ready" : "Upload your CV for AI analysis"}
          </p>
        </div>
        {step === "completed" && (
          <div className="flex gap-3">
            <button
              onClick={() => router.push('/jobs')}
              className="flex items-center gap-2 px-4 py-2 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-500 text-[10px] font-black uppercase tracking-widest hover:bg-indigo-500 hover:text-white transition-all"
            >
              <Briefcase size={14} /> Find Jobs
            </button>
            <button
              onClick={() => router.push('/learning/path')}
              className="flex items-center gap-2 px-4 py-2 rounded-xl bg-blue-500/10 border border-blue-500/20 text-blue-500 text-[10px] font-black uppercase tracking-widest hover:bg-blue-500 hover:text-white transition-all"
            >
              <BookOpen size={14} /> Learning Path
            </button>
          </div>
        )}
      </div>

      {/* PROGRESS INDICATOR */}
      {step !== "idle" && step !== "completed" && (
        <div className="flex items-center justify-center gap-8">
          {progressSteps.map((progressStep, index) => {
            const status = getStepStatus(progressStep.key);
            const Icon = progressStep.icon;

            return (
              <React.Fragment key={progressStep.key}>
                <div className="flex flex-col items-center gap-2">
                  <div className={cn(
                    "w-12 h-12 rounded-full flex items-center justify-center transition-all duration-300",
                    status === "completed" && "bg-green-500/20 border-2 border-green-500",
                    status === "active" && "bg-indigo-500/20 border-2 border-indigo-500 animate-pulse",
                    status === "pending" && "bg-white/5 border-2 border-white/10"
                  )}>
                    {status === "completed" ? (
                      <CheckCircle2 size={20} className="text-green-500" />
                    ) : status === "active" ? (
                      <Loader2 size={20} className="text-indigo-500 animate-spin" />
                    ) : (
                      <Icon size={20} className="text-white/40" />
                    )}
                  </div>
                  <span className={cn(
                    "text-[10px] font-black uppercase tracking-widest",
                    status === "active" && "text-indigo-400",
                    status === "completed" && "text-green-400",
                    status === "pending" && "text-slate-500"
                  )}>
                    {progressStep.label}
                  </span>
                </div>
                {index < progressSteps.length - 1 && (
                  <div className={cn(
                    "w-16 h-0.5 transition-all duration-300",
                    getStepStatus(progressSteps[index + 1].key) === "completed" ? "bg-green-500" : "bg-white/10"
                  )} />
                )}
              </React.Fragment>
            );
          })}
        </div>
      )}

      {/* MAIN CONTENT */}
      <div className="grid grid-cols-1 gap-8">

        {/* IDLE STATE - UPLOAD ZONE */}
        {step === "idle" && (
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={cn(
              "group h-80 border-2 border-dashed rounded-[48px] flex flex-col items-center justify-center gap-6 cursor-pointer transition-all duration-500",
              isDragOver
                ? "border-indigo-500 bg-indigo-500/5 scale-105"
                : "border-white/5 bg-white/[0.01] hover:bg-white/[0.02] hover:border-indigo-500/30"
            )}
          >
            <div className="w-20 h-20 rounded-3xl bg-indigo-500/5 flex items-center justify-center text-indigo-500/40 group-hover:scale-110 transition-all border border-white/5 shadow-2xl">
              <UploadCloud size={40} strokeWidth={1} />
            </div>
            <div className="text-center">
              <p className="text-lg font-bold text-white uppercase tracking-tight">
                {isDragOver ? "Drop your CV here" : "Drop your CV or click to browse"}
              </p>
              <p className="text-[9px] font-black text-slate-500 uppercase tracking-widest mt-1">
                PDF, DOCX • Max 10MB
              </p>
            </div>
            <input
              type="file"
              ref={fileInputRef}
              className="hidden"
              accept=".pdf,.docx"
              onChange={handleFileSelect}
            />
          </div>
        )}

        {/* PROCESSING STATES */}
        {(step === "uploading" || step === "analyzing" || step === "routing") && (
          <div className="h-80 bg-white/[0.02] border border-white/5 rounded-[48px] flex flex-col items-center justify-center gap-6 backdrop-blur-3xl">
            <Loader2 className="w-12 h-12 text-indigo-500 animate-spin" strokeWidth={1} />
            <div className="text-center">
              <p className="text-sm font-bold text-white uppercase tracking-widest animate-pulse">
                {step === "uploading" && "Uploading your CV..."}
                {step === "analyzing" && "AI is analyzing your profile..."}
                {step === "routing" && "Routing to best opportunities..."}
              </p>
              {selectedFile && (
                <p className="text-[10px] text-slate-500 uppercase tracking-widest mt-2">
                  {selectedFile.name}
                </p>
              )}
            </div>
          </div>
        )}

        {/* COMPLETED STATE */}
        {step === "completed" && score !== null && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">

            {/* SCORE GAUGE */}
            <div className="bg-white/[0.02] border border-white/5 p-8 rounded-[40px] flex flex-col items-center justify-center gap-6">
              <CVScoreGauge score={score} size={200} />
              <div className="text-center">
                <h3 className="text-xl font-bold text-white uppercase tracking-tight">
                  {score >= 70 ? "Finding your best jobs..." : "Building your learning path..."}
                </h3>
                <p className="text-[10px] text-slate-500 uppercase tracking-widest mt-2">
                  {score >= 70
                    ? "Your profile matches top opportunities"
                    : "Let's enhance your skills for better matches"
                  }
                </p>
              </div>
            </div>

            {/* NEXT STEPS */}
            <div className="bg-white/[0.02] border border-white/5 p-8 rounded-[40px] space-y-6">
              <div className="flex items-center gap-3">
                <Zap size={18} className="text-indigo-400" />
                <h3 className="font-bold text-white uppercase tracking-tighter text-xl">
                  What's Next?
                </h3>
              </div>

              <div className="space-y-4">
                {score >= 70 ? (
                  <>
                    <div className="flex items-center gap-4 p-4 bg-green-500/10 border border-green-500/20 rounded-xl">
                      <CheckCircle2 size={20} className="text-green-500" />
                      <div>
                        <p className="text-sm font-bold text-white">Job Matching Ready</p>
                        <p className="text-[10px] text-slate-400">Browse personalized job recommendations</p>
                      </div>
                    </div>
                    <button
                      onClick={() => router.push('/jobs')}
                      className="w-full py-3 bg-indigo-500 text-white rounded-xl font-black text-[10px] uppercase tracking-widest hover:bg-indigo-600 transition-all"
                    >
                      Explore Jobs
                    </button>
                  </>
                ) : (
                  <>
                    <div className="flex items-center gap-4 p-4 bg-blue-500/10 border border-blue-500/20 rounded-xl">
                      <BookOpen size={20} className="text-blue-500" />
                      <div>
                        <p className="text-sm font-bold text-white">Learning Path Created</p>
                        <p className="text-[10px] text-slate-400">Follow your personalized development plan</p>
                      </div>
                    </div>
                    <button
                      onClick={() => router.push('/learning/path')}
                      className="w-full py-3 bg-blue-500 text-white rounded-xl font-black text-[10px] uppercase tracking-widest hover:bg-blue-600 transition-all"
                    >
                      Start Learning
                    </button>
                  </>
                )}
              </div>
            </div>
          </div>
        )}

        {/* ERROR STATE */}
        {error && (
          <div className="bg-red-500/10 border border-red-500/20 p-6 rounded-[40px] flex items-center gap-4">
            <AlertCircle size={24} className="text-red-500 flex-shrink-0" />
            <div className="flex-1">
              <p className="text-sm font-bold text-red-400 uppercase tracking-widest">
                Upload Failed
              </p>
              <p className="text-[10px] text-red-300 mt-1">
                {getErrorMessage(error)}
              </p>
            </div>
            <button
              onClick={() => {
                setError(null);
                setStep("idle");
                setSelectedFile(null);
              }}
              className="p-2 text-red-500 hover:text-red-400 transition-colors"
            >
              <X size={16} />
            </button>
          </div>
        )}
      </div>
    </div>
  );
}