// src/lib/mocks/dashboard.ts
export const mockDashboardData = {
  stats: {
    cvScore: 82,
    learningProgress: 65,
    interviewsCompleted: 4,
    currentFlow: "Frontend Developer",
  },
  topJobs: [
    { id: 1, title: "React Developer", company: "TechFlow", location: "Remote", source: "LinkedIn" as const, match: 95, coverLetter: "Sunt impresionat de stack-ul vostru..." },
    { id: 2, title: "Frontend Engineer", company: "WebUI", location: "București", source: "eJobs" as const, match: 88, coverLetter: "Experiența mea cu Next.js se potrivește..." },
    { id: 3, title: "Junior UI Developer", company: "CreativeApp", location: "Hybrid", source: "Indeed" as const, match: 72, coverLetter: "Vreau să îmi încep cariera în echipa..." },
  ],
  modules: [
    { id: 1, title: "Bazele React & Hooks", week: 1, status: "completed" as const, resources: 12 },
    { id: 2, title: "State Management", week: 2, status: "active" as const, resources: 8 },
    { id: 3, title: "Next.js App Router", week: 3, status: "locked" as const, resources: 15 },
  ],
  recentInterviews: [
    { date: "2026-04-20", hrScore: 85, techScore: 78 },
  ]
};