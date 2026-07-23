package com.ragassistant.dto;

import com.ragassistant.entity.DocumentStatus;

import java.time.Instant;
import java.util.UUID;

public record DocumentResponse(
        UUID id,
        String filename,
        DocumentStatus status,
        Integer chunkCount,
        Instant uploadedAt
) {}
