package com.careerpath.userservice.model;

import jakarta.persistence.*;
import lombok.Data;
import java.time.LocalDateTime;

@Entity
@Table(name = "user_progress")
@Data
public class UserProgress {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "user_id")
    private String userId;

    private String resourceId;
    private Integer completionPercentage;
    private LocalDateTime lastAccessed;

    private Integer modulesCompleted = 0;
    private Integer modulesTotal = 10;

    @PrePersist
    @PreUpdate
    protected void onCreate() {
        lastAccessed = LocalDateTime.now();
    }
}
