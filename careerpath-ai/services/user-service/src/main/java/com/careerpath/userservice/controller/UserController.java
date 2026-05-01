package com.careerpath.userservice.controller;

import com.careerpath.userservice.model.Profile;
import com.careerpath.userservice.model.User;
import com.careerpath.userservice.model.UserProgress;
import com.careerpath.userservice.repository.UserProgressRepository;
import com.careerpath.userservice.repository.UserRepository;
import com.careerpath.userservice.service.UserService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/users")
public class UserController {

    @Autowired
    private UserService userService;
    @Autowired
    private UserProgressRepository progressRepository;
    @Autowired
    private org.springframework.kafka.core.KafkaTemplate<String, String> kafkaTemplate;

    @GetMapping("/me")
    public User getCurrentUser(@AuthenticationPrincipal Jwt jwt) {
        String keycloakId = jwt.getSubject();
        String email = jwt.getClaimAsString("email");

        return userService.getUserById(keycloakId)
                .orElseGet(() -> {
                    User newUser = new User();
                    newUser.setId(keycloakId);
                    newUser.setEmail(email);
                    newUser.setUsername(jwt.getClaimAsString("preferred_username"));
                    return userService.saveUser(newUser);
                });
    }

    @PostMapping("/me/profile")
    public User updateProfile(@AuthenticationPrincipal Jwt jwt, @RequestBody Profile profileData) {
        String keycloakId = jwt.getSubject();

        // Căutăm user-ul sau îl creăm dacă nu există
        User user = userService.getUserById(keycloakId).orElseGet(() -> {
            User newUser = new User();
            newUser.setId(keycloakId);
            newUser.setEmail(jwt.getClaimAsString("email"));
            newUser.setUsername(jwt.getClaimAsString("preferred_username"));
            return newUser;
        });

        // Dacă user-ul nu are încă un profil, îi creăm unul
        if (user.getProfile() == null) {
            user.setProfile(new Profile());
        }

        // Actualizăm câmpurile profilului cu datele primite din Postman
        user.getProfile().setFirstName(profileData.getFirstName());
        user.getProfile().setLastName(profileData.getLastName());
        user.getProfile().setBio(profileData.getBio());
        user.getProfile().setAvatarUrl(profileData.getAvatarUrl());

        return userService.saveUser(user);
    }

    @PutMapping("/progress")
    public UserProgress updateProgress(@AuthenticationPrincipal Jwt jwt) {
        String userId = jwt.getSubject();
        UserProgress progress  = progressRepository.findByUserId(userId)
                .orElseThrow(() -> new RuntimeException("Progress not found"));

        progress.setModulesCompleted(progress.getModulesCompleted() + 1);

        if(progress.getModulesCompleted().equals(progress.getModulesTotal())) {
            kafkaTemplate.send("learning.completed", userId, "Success");
        }
        return progressRepository.save(progress);
    }

    @GetMapping("/profile")
    public Profile getFullProfile(@AuthenticationPrincipal Jwt jwt) {
        return userService.getUserById(jwt.getSubject())
                .map(User::getProfile)
                .orElseThrow(() -> new RuntimeException("Profile not found"));
    }

    @PutMapping("/profile")
    public Profile updateFullProfile(@AuthenticationPrincipal Jwt jwt, @RequestBody Profile updates) {
        User user = userService.getUserById(jwt.getSubject())
                .orElseThrow(() -> new RuntimeException("User not found"));

        Profile p = user.getProfile();

        p.setName(updates.getName());
        p.setTitle(updates.getTitle());
        p.setLocation(updates.getLocation());
        p.setLinkedinUrl(updates.getLinkedinUrl());
        p.setTargetRole(updates.getTargetRole());
        p.setSeniorityLevel(updates.getSeniorityLevel());
        p.setBio(updates.getBio());

        user.setProfile(p);

        return userService.saveUser(user).getProfile();
    }

    @GetMapping("/dashboard")
    public com.careerpath.userservice.dto.DashboardDTO getDashboard(@AuthenticationPrincipal Jwt jwt) {
        String userId = jwt.getSubject();
        User user = userService.getUserById(userId).orElseThrow(() -> new RuntimeException("User not found"));

        com.careerpath.userservice.dto.DashboardDTO dashboard = new com.careerpath.userservice.dto.DashboardDTO();
        dashboard.setProgress(progressRepository.findByUserId(userId).orElse(null));

        dashboard.setLatestCvUpload(null);
        dashboard.setTopJobMatches(new java.util.ArrayList<>());

        return dashboard;
    }
}
