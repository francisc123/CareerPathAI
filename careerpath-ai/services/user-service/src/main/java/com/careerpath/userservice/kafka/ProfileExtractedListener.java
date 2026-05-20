package com.careerpath.userservice.kafka;

import com.careerpath.userservice.model.Profile;
import com.careerpath.userservice.model.User;
import com.careerpath.userservice.repository.UserRepository;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

import java.util.Optional;

@Component
public class ProfileExtractedListener {

    private static final Logger log = LoggerFactory.getLogger(ProfileExtractedListener.class);
    private static final ObjectMapper MAPPER = new ObjectMapper();

    @Autowired
    private UserRepository userRepository;

    @KafkaListener(topics = "profile.extracted", groupId = "user-service-profile-extracted")
    @Transactional
    public void onProfileExtracted(String payload) {
        try {
            JsonNode node = MAPPER.readTree(payload);
            String userId = textOrNull(node, "user_id");
            if (userId == null || userId.isBlank()) {
                log.warn("profile.extracted missing user_id — skipping payload");
                return;
            }

            Optional<User> userOpt = userRepository.findById(userId);
            if (userOpt.isEmpty()) {
                // Don't fabricate users from chat events; the orchestrator already
                // skips anon_* ids, but real ids may still arrive before registration.
                log.info("profile.extracted: no user row for id={} yet, skipping", userId);
                return;
            }

            User user = userOpt.get();
            Profile profile = user.getProfile() == null ? new Profile() : user.getProfile();

            applyIfPresent(node, "target_role", profile::setTargetRole);
            applyIfPresent(node, "seniority", profile::setSeniorityLevel);
            applyIfPresent(node, "location", profile::setLocation);
            applyIfPresent(node, "current_situation", profile::setCurrentSituation);

            JsonNode skills = node.get("skills");
            if (skills != null && skills.isArray() && skills.size() > 0) {
                StringBuilder csv = new StringBuilder();
                for (JsonNode s : skills) {
                    if (s == null || s.isNull()) continue;
                    String value = s.asText().trim();
                    if (value.isEmpty()) continue;
                    if (csv.length() > 0) csv.append(",");
                    csv.append(value);
                }
                if (csv.length() > 0) {
                    profile.setSkillsCsv(csv.toString());
                }
            }

            JsonNode exp = node.get("experience_years");
            if (exp != null && exp.isNumber()) {
                profile.setExperienceYears(exp.asInt());
            }

            user.setProfile(profile);
            userRepository.save(user);
            log.info("profile.extracted applied for user {}", userId);
        } catch (Exception e) {
            // Eat the exception so the consumer keeps polling — bad payloads
            // shouldn't poison the partition.
            log.error("profile.extracted failed to process payload: {}", e.getMessage(), e);
        }
    }

    private static String textOrNull(JsonNode node, String field) {
        JsonNode v = node.get(field);
        return (v == null || v.isNull()) ? null : v.asText();
    }

    private static void applyIfPresent(JsonNode node, String field, java.util.function.Consumer<String> setter) {
        String value = textOrNull(node, field);
        if (value != null && !value.isBlank()) {
            setter.accept(value);
        }
    }
}
