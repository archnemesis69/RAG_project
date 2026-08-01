package com.ragassistant.service;

import com.ragassistant.dto.QueryResponse;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.http.MediaType;
import org.springframework.http.client.MultipartBodyBuilder;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.BodyInserters;
import org.springframework.web.reactive.function.client.WebClient;

import java.util.Map;

/**
 * Everything the Spring Boot backend needs from the FastAPI AI service:
 * uploading a file for ingestion, deleting a document from the index,
 * and asking a question. Every call takes an ownerId, which the AI
 * service uses to tag/filter Chroma chunks by owner_id metadata - this
 * is the piece that makes "voir ses documents" and "poser une
 * question" actually scoped to the current user instead of the whole
 * shared index.
 */
@Component
public class AiServiceClient {

    private final WebClient webClient;

    public AiServiceClient(WebClient aiServiceWebClient) {
        this.webClient = aiServiceWebClient;
    }

    /** POST /documents on the AI service - ingests the file under ownerId, returns {filename, status, chunks}. */
    public Map<String, Object> uploadDocument(byte[] fileBytes, String filename, String ownerId) {
        MultipartBodyBuilder builder = new MultipartBodyBuilder();
        builder.part("file", new ByteArrayResource(fileBytes) {
            @Override
            public String getFilename() {
                return filename;
            }
        }).contentType(MediaType.APPLICATION_OCTET_STREAM);
        builder.part("owner_id", ownerId);

        return webClient.post()
                .uri("/documents")
                .contentType(MediaType.MULTIPART_FORM_DATA)
                .body(BodyInserters.fromMultipartData(builder.build()))
                .retrieve()
                .bodyToMono(Map.class)
                .block();
    }

    /** DELETE /documents/{filename}?owner_id=... on the AI service - never touches another owner's copy. */
    public void deleteDocument(String filename, String ownerId) {
        webClient.delete()
                .uri(uriBuilder -> uriBuilder
                        .path("/documents/{filename}")
                        .queryParam("owner_id", ownerId)
                        .build(filename))
                .retrieve()
                .toBodilessEntity()
                .block();
    }

    /** POST /query on the AI service, scoped to ownerId's own documents. */
    public QueryResponse query(String question, int topK, String ownerId) {
        Map<String, Object> payload = Map.of(
                "question", question,
                "top_k", topK,
                "owner_id", ownerId
        );

        // #region agent log
        try (java.io.FileWriter fw = new java.io.FileWriter("/app/.cursor/debug-a5752a.log", true)) {
            fw.write("{\"sessionId\":\"a5752a\",\"hypothesisId\":\"E\",\"location\":\"AiServiceClient.java:query\",\"message\":\"backend query start\",\"data\":{\"ownerId\":\"" + ownerId + "\",\"topK\":" + topK + ",\"questionLen\":" + question.length() + "},\"timestamp\":" + System.currentTimeMillis() + ",\"runId\":\"pre-fix\"}\n");
        } catch (Exception ignored) {}
        // #endregion

        try {
            QueryResponse response = webClient.post()
                    .uri("/query")
                    .contentType(MediaType.APPLICATION_JSON)
                    .bodyValue(payload)
                    .retrieve()
                    .bodyToMono(QueryResponse.class)
                    .block();
            // #region agent log
            try (java.io.FileWriter fw = new java.io.FileWriter("/app/.cursor/debug-a5752a.log", true)) {
                fw.write("{\"sessionId\":\"a5752a\",\"hypothesisId\":\"E\",\"location\":\"AiServiceClient.java:query\",\"message\":\"backend query success\",\"data\":{\"answerLen\":" + (response.answer() != null ? response.answer().length() : 0) + "},\"timestamp\":" + System.currentTimeMillis() + ",\"runId\":\"pre-fix\"}\n");
            } catch (Exception ignored) {}
            // #endregion
            return response;
        } catch (Exception e) {
            // #region agent log
            try (java.io.FileWriter fw = new java.io.FileWriter("/app/.cursor/debug-a5752a.log", true)) {
                fw.write("{\"sessionId\":\"a5752a\",\"hypothesisId\":\"E\",\"location\":\"AiServiceClient.java:query\",\"message\":\"backend query failed\",\"data\":{\"errorType\":\"" + e.getClass().getSimpleName() + "\",\"error\":\"" + e.getMessage().replace("\"", "'") + "\"},\"timestamp\":" + System.currentTimeMillis() + ",\"runId\":\"pre-fix\"}\n");
            } catch (Exception ignored) {}
            // #endregion
            throw e;
        }
    }
}
