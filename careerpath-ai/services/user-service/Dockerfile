# User Service — Java 21 + Spring Boot + Maven

FROM maven:3.9-eclipse-temurin-21-alpine AS builder
WORKDIR /app
COPY pom.xml .
RUN mvn dependency:go-offline -B
COPY src ./src
RUN mvn clean package -DskipTests -B

FROM eclipse-temurin:21-jre-alpine AS production
WORKDIR /app
RUN addgroup --system --gid 1001 appgroup \
 && adduser  --system --uid 1001 appuser --ingroup appgroup
COPY --from=builder --chown=appuser:appgroup /app/target/*.jar app.jar
USER appuser
EXPOSE 8001
CMD ["java", "-jar", "app.jar"]
