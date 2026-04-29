CREATE TABLE IF NOT EXISTS cv_analysis_results (                                                                                                                            user_id     TEXT PRIMARY KEY,
      score       INT NOT NULL,
      seniority   TEXT NOT NULL,
      target_role TEXT NOT NULL,
      analyzed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
  );
