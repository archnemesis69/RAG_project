package com.ragassistant.controller;

import com.ragassistant.dto.QueryRequest;
import com.ragassistant.dto.QueryResponse;
import com.ragassistant.entity.User;
import com.ragassistant.service.AiServiceClient;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/chat")
@RequiredArgsConstructor
public class ChatController {

    private final AiServiceClient aiServiceClient;

    @PostMapping("/query")
    public ResponseEntity<QueryResponse> query(
            @AuthenticationPrincipal User user,
            @Valid @RequestBody QueryRequest request
    ) {
        int topK = request.topK() != null ? request.topK() : 5;

        // FIX: `user` was being injected but never actually used -
        // every question was answered against the entire shared
        // index. Now the query is scoped to this user's own documents.
        return ResponseEntity.ok(aiServiceClient.query(request.question(), topK, user.getId().toString()));
    }
}
