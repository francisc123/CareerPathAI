package com.careerpath.userservice.dto;

import com.careerpath.userservice.model.Profile;
import com.careerpath.userservice.model.UserProgress;
import lombok.Data;
import java.util.List;

@Data
public class DashboardDTO {

    private Profile profile;
    private UserProgress progress;

    private Object latestCvUpload;
    private List<Object> topJobMatches;
    private List<Object> lastInterviewSessions;
}
