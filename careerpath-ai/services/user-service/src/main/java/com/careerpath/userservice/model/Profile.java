package com.careerpath.userservice.model;

import jakarta.persistence.*;
import lombok.Data;

@Entity
@Table(name = "profiles")
@Data
public class Profile {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String firstName;
    private String lastName;
    private String bio;
    private String avatarUrl;

    private String name;
    private String title;
    private String location;
    private String linkedinUrl;
    private String targetRole;
    private String seniorityLevel;

    // Populated from the orchestrator's shadow profile via profile.extracted.
    // Stored as comma-separated values to avoid an extra join table.
    @Column(length = 2048)
    private String skillsCsv;

    private Integer experienceYears;

    // "in_tech" | "student" | "career_switch" — kept as String so new orchestrator
    // values don't force a schema change.
    private String currentSituation;
}
