package com.careerpath.userservice;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.web.SecurityFilterChain;

@Configuration
@EnableWebSecurity
public class SecurityConfig {

    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http
                .csrf(csrf -> csrf.disable()) // Dezactivăm CSRF
                .authorizeHttpRequests(auth -> auth
                        .requestMatchers("/api/users/progress").permitAll()
                        .requestMatchers("/api/users/register").permitAll()          // <-- ADĂUGATĂ ACUM
                        .requestMatchers("/api/users/verify-credentials").permitAll() // <-- ADĂUGATĂ ACUM
                        .requestMatchers("/api/**").authenticated()          // Restul rutei rămâne securizat
                        .anyRequest().permitAll()
                )
                .oauth2ResourceServer(oauth2 -> oauth2.jwt(jwt -> {}));
        return http.build();
    }
}