"use client";

import { CVScoreGauge } from "../../components/ui/cv-score-gauge";
import { JobCard } from "../../components/ui/job-card";
import { ChatBubble } from "../../components/ui/chat-bubble";
import { ModuleCard } from "../../components/ui/module-card";
import { ProgressBar } from "../../components/ui/progress-bar";

export default function PreviewPage() {
  return (
    <div className="min-h-screen bg-black p-10 space-y-12">
      <header className="border-b border-gray-800 pb-5">
        <h1 className="text-3xl font-bold text-white">Component Library Sandbox</h1>
        <p className="text-gray-400">Verificare vizuală pentru task-ul CP-013</p>
      </header>

      {/* CV & Progress Section */}
      <section className="grid grid-cols-1 md:grid-cols-2 gap-10">
        <div className="space-y-4">
          <h2 className="text-xl text-primary font-semibold">Gauges & Progress</h2>
          <div className="flex gap-10 items-center">
            <CVScoreGauge score={85} />
            <CVScoreGauge score={55} />
            <CVScoreGauge score={25} />
          </div>
          <div className="w-full max-w-md pt-5">
            <ProgressBar progress={65} label="Gradul de pregătire" />
          </div>
        </div>

        <div className="space-y-4">
          <h2 className="text-xl text-primary font-semibold">Chat System</h2>
          <div className="bg-gray-900/50 p-6 rounded-xl border border-gray-800">
            <ChatBubble role="ai" content="Salut! Sunt AI-ul tău. Cum te pot ajuta astăzi?" />
            <ChatBubble role="user" content="Vreau să îmi verifici CV-ul pentru un job de Frontend." />
            <ChatBubble role="ai" content="..." isTyping={true} />
          </div>
        </div>
      </section>

      {/* Jobs Section */}
      <section className="space-y-4">
        <h2 className="text-xl text-primary font-semibold">Job Recommendations</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <JobCard 
            title="Frontend Developer" 
            company="Tech Corp" 
            location="București (Remote)" 
            source="LinkedIn" 
            match={92} 
            coverLetter="Stimate manager, sunt pasionat de React și..." 
          />
          <JobCard 
            title="React Engineer" 
            company="Soft Solutions" 
            location="Cluj-Napoca" 
            source="eJobs" 
            match={78} 
            coverLetter="Bună ziua, vă scriu referitor la poziția..." 
          />
        </div>
      </section>

      {/* Modules Section */}
      <section className="space-y-4 pb-20">
        <h2 className="text-xl text-primary font-semibold">Learning Modules</h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <ModuleCard title="Bazele React" week={1} status="completed" resources={12} />
          <ModuleCard title="State Management" week={2} status="active" resources={8} />
          <ModuleCard title="Next.js App Router" week={3} status="locked" resources={15} />
          <ModuleCard title="Deploy & DevOps" week={4} status="locked" resources={5} />
        </div>
      </section>
    </div>
  );
}