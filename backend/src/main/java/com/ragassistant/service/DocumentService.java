package com.ragassistant.service;

import com.ragassistant.dto.DocumentResponse;
import com.ragassistant.entity.DocumentEntity;
import com.ragassistant.entity.DocumentStatus;
import com.ragassistant.entity.User;
import com.ragassistant.exception.ResourceNotFoundException;
import com.ragassistant.repository.DocumentRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.stream.Collectors;

@Slf4j
@Service
@RequiredArgsConstructor
public class DocumentService {

    private static final List<String> ALLOWED_EXTENSIONS = List.of(".pdf", ".docx", ".txt");

    private final DocumentRepository documentRepository;
    private final AiServiceClient aiServiceClient;

    public DocumentResponse upload(User owner, MultipartFile file) {
        String filename = file.getOriginalFilename();

        if (filename == null || ALLOWED_EXTENSIONS.stream().noneMatch(ext -> filename.toLowerCase().endsWith(ext))) {
            throw new IllegalArgumentException("Only PDF, DOCX, and TXT files are supported");
        }

        DocumentEntity document = DocumentEntity.builder()
                .filename(filename)
                .owner(owner)
                .status(DocumentStatus.PROCESSING)
                .build();
        document = documentRepository.save(document);

        try {
            byte[] bytes = file.getBytes();
            // FIX: pass the owner's id so the AI service tags every
            // chunk with owner_id and stores the file under a
            // per-owner folder - this is what makes retrieval and
            // storage actually isolated per user.
            Map<String, Object> result = aiServiceClient.uploadDocument(bytes, filename, owner.getId().toString());

            Object chunks = result.get("chunks");
            document.setChunkCount(chunks != null ? Integer.parseInt(chunks.toString()) : 0);
            document.setStatus(DocumentStatus.READY);
        } catch (IOException | RuntimeException e) {
            String errorMessage = e.getMessage();
            if (e instanceof org.springframework.web.reactive.function.client.WebClientResponseException wcre) {
                errorMessage = wcre.getResponseBodyAsString();
            }
            if (errorMessage == null || errorMessage.isBlank()) {
                errorMessage = "Failed due to " + e.getClass().getSimpleName();
            }
            log.error("Document ingestion failed for '{}': {}", filename, errorMessage, e);
            document.setStatus(DocumentStatus.FAILED);
            document.setErrorMessage(errorMessage);
        }

        document = documentRepository.save(document);
        return toResponse(document);
    }

    public List<DocumentResponse> listDocuments(User owner) {
        return documentRepository.findByOwner(owner).stream()
                .map(this::toResponse)
                .collect(Collectors.toList());
    }

    public void delete(User owner, UUID documentId) {
        DocumentEntity document = documentRepository.findByIdAndOwner(documentId, owner)
                .orElseThrow(() -> new ResourceNotFoundException("Document not found"));

        // FIX: owner id now passed through, so this can only ever
        // delete this owner's own chunks - even if another user
        // happens to have a document with the identical filename.
        aiServiceClient.deleteDocument(document.getFilename(), owner.getId().toString());
        documentRepository.delete(document);
    }

    private DocumentResponse toResponse(DocumentEntity document) {
        return new DocumentResponse(
                document.getId(),
                document.getFilename(),
                document.getStatus(),
                document.getChunkCount(),
                document.getErrorMessage(),
                document.getUploadedAt()
        );
    }
}
