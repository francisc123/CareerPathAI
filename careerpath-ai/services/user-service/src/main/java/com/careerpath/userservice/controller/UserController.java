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
import org.springframework.http.ResponseEntity;
import java.util.Map;
import java.util.HashMap;

@RestController
@RequestMapping("/api/users")
public class UserController {

    @Autowired
    private UserService userService;
    @Autowired
    private UserProgressRepository progressRepository;
    @Autowired
    private UserRepository userRepository;
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
    public org.springframework.http.ResponseEntity<?> updateProgress(
            @AuthenticationPrincipal Jwt jwt,
            @RequestHeader(value = "X-User-Id", required = false) String headerUserId) {

        System.out.println("[DEBUG-TEST] Cerere HTTP PUT /progress receptionata rapid.");

        final String userId = (jwt != null) ? jwt.getSubject() : headerUserId;
        if (userId == null || userId.trim().isEmpty()) {
            return org.springframework.http.ResponseEntity.badRequest().body("Missing user identifier");
        }

        // DECUPLARE TOTALĂ: Mutăm absolut toată logica greoaie (DB + Kafka) în fundal
        java.util.concurrent.CompletableFuture.runAsync(() -> {
            try {
                System.out.println("[DEBUG-ASYNC] Începe procesarea asincronă pentru user: " + userId);

                // 1. Asigurare Foreign Key în fundal
                if (!userService.getUserById(userId).isPresent()) {
                    User mockUser = new User();
                    mockUser.setId(userId);
                    mockUser.setEmail("test-" + userId + "@careerpath.ai");
                    mockUser.setUsername("test_" + userId.substring(0, 5));
                    userService.saveUser(mockUser);
                }

                // 2. Căutare sau inițializare progres
                UserProgress progress = progressRepository.findByUserId(userId)
                        .orElseGet(() -> {
                            UserProgress newProgress = new UserProgress();
                            newProgress.setUserId(userId);
                            newProgress.setModulesCompleted(0);
                            newProgress.setModulesTotal(1);
                            return newProgress;
                        });

                // 3. Incrementare și salvare în PostgreSQL (Aici dura 44 de secunde)
                progress.setModulesCompleted(progress.getModulesCompleted() + 1);
                progressRepository.save(progress);
                System.out.println("[DEBUG-ASYNC] Salvare cu succes în PostgreSQL finalizată.");

                // 4. Livrare eveniment Kafka în fundal
                if (progress.getModulesCompleted().equals(progress.getModulesTotal())) {
                    kafkaTemplate.send("learning.completed", userId, "Success")
                            .whenComplete((result, ex) -> {
                                if (ex != null) {
                                    System.err.println("[DEBUG-ASYNC-WARN] Trimitere Kafka eșuată: " + ex.getMessage());
                                } else {
                                    System.out.println("[DEBUG-ASYNC-SUCCESS] Eveniment trimis cu succes! Offset: " + result.getRecordMetadata().offset());
                                }
                            });
                }

            } catch (Exception e) {
                System.err.println("[DEBUG-ASYNC-ERROR] Crash în firul de execuție de fundal: " + e.getMessage());
            }
        });

        // Întoarcem instant un obiect JSON curat către API Gateway.
        // Conexiunea HTTP se închide cu succes în 2ms, eliminând riscul de timeout.
        java.util.Map<String, Object> response = new java.util.HashMap<>();
        response.put("status", "success");
        response.put("message", "Progress update accepted and processing asynchronously");

        return org.springframework.http.ResponseEntity.ok(response);
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

    @PostMapping("/register")
    public org.springframework.http.ResponseEntity<?> registerLocalUser(@RequestBody java.util.Map<String, String> payload) {
        // Extragem valorile din JSON-ul trimis de Gateway
        String id = payload.get("id");
        String email = payload.get("email");
        String username = payload.get("username");

        if (id == null || email == null) {
            java.util.Map<String, String> errorResponse = new java.util.HashMap<>();
            errorResponse.put("message", "Id-ul și Email-ul sunt obligatorii");
            return org.springframework.http.ResponseEntity.badRequest().body(errorResponse);
        }

        // Salvăm utilizatorul în PostgreSQL folosind repository-ul injectat
        com.careerpath.userservice.model.User user = userRepository.findById(id)
                .orElseGet(() -> {
                    com.careerpath.userservice.model.User newUser = new com.careerpath.userservice.model.User();
                    newUser.setId(id);
                    newUser.setEmail(email);
                    newUser.setUsername(username);
                    return userRepository.save(newUser);
                });

        return org.springframework.http.ResponseEntity.status(201).body(user);
    }

    @PostMapping("/verify-credentials")
    public org.springframework.http.ResponseEntity<?> verifyCredentials(@RequestBody java.util.Map<String, String> payload) {
        String email = payload.get("email");
        String password = payload.get("password");

        if (email == null || password == null) {
            java.util.Map<String, String> errorResponse = new java.util.HashMap<>();
            errorResponse.put("message", "Email-ul și parola sunt obligatorii");
            return org.springframework.http.ResponseEntity.badRequest().body(errorResponse);
        }

        java.util.Optional<com.careerpath.userservice.model.User> userOpt = userRepository.findByEmail(email);

        if (userOpt.isPresent()) {
            // Utilizatorul există (TODO: adaugă logica de hashing BCrypt pentru parolă pe viitor)
            return org.springframework.http.ResponseEntity.ok(userOpt.get());
        } else {
            java.util.Map<String, String> errorResponse = new java.util.HashMap<>();
            errorResponse.put("message", "Credențiale invalide sau utilizator inexistent");
            return org.springframework.http.ResponseEntity.status(401).body(errorResponse);
        }
    }
}
