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
}
