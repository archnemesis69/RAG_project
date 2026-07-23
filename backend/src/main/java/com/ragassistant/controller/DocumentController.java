package com.ragassistant.controller;

import com.ragassistant.dto.DocumentResponse;
import com.ragassistant.entity.User;
import com.ragassistant.service.DocumentService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.util.List;
import java.util.UUID;

@RestController
@RequestMapping("/api/documents")
@RequiredArgsConstructor
public class DocumentController {

    private final DocumentService documentService;

    @PostMapping(consumes = "multipart/form-data")
    public ResponseEntity<DocumentResponse> upload(
            @AuthenticationPrincipal User user,
            @RequestParam("file") MultipartFile file
    ) {
        return ResponseEntity.ok(documentService.upload(user, file));
    }

    @GetMapping
    public ResponseEntity<List<DocumentResponse>> list(@AuthenticationPrincipal User user) {
        return ResponseEntity.ok(documentService.listDocuments(user));
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> delete(@AuthenticationPrincipal User user, @PathVariable UUID id) {
        documentService.delete(user, id);
        return ResponseEntity.noContent().build();
    }
}
