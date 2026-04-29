package com.careerpath.userservice.repository;

import com.careerpath.userservice.model.UserProgress;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.Optional;

public interface UserProgressRepository extends JpaRepository<UserProgress, Long> {

    // Această metodă îi spune lui Spring:
    // "Caută în tabelul user_progress rândul unde coloana user_id este egală cu parametrul meu"
    Optional<UserProgress> findByUserId(String userId);
}