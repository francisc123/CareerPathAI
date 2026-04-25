package com.careerpath.userservice.controller;

import com.careerpath.userservice.model.Profile;
import com.careerpath.userservice.model.User;
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
}
