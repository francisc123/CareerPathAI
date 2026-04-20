// Shared Kafka event type contracts — used by all Node.js services

export interface UserRegisteredEvent {
  userId: string;
  email: string;
  timestamp: string;
}

export interface CvUploadedEvent {
  userId: string;
  jobId: string;
  minioPath: string;
  fileName: string;
  timestamp: string;
}

export interface CvAnalyzedEvent {
  userId: string;
  jobId: string;
  score: number;          // 0-100
  skills: string[];
  gaps: string[];
  targetRole: string;
  seniorityLevel: string;
  timestamp: string;
}

export interface GapsIdentifiedEvent {
  userId: string;
  gaps: string[];
  currentLevel: string;
  targetRole: string;
  timestamp: string;
}

export interface JobsScrapedEvent {
  userId: string;
  scrapeRunId: string;
  jobCount: number;
  timestamp: string;
}

export interface JobsMatchedEvent {
  userId: string;
  topJobIds: string[];
  timestamp: string;
}

export interface LearningPathCreatedEvent {
  userId: string;
  pathId: string;
  totalWeeks: number;
  timestamp: string;
}

export interface LearningCompletedEvent {
  userId: string;
  pathId: string;
  timestamp: string;
}

export interface InterviewCompletedEvent {
  userId: string;
  sessionId: string;
  type: "hr" | "technical";
  score: number;
  timestamp: string;
}
