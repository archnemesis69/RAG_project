package com.ragassistant.dto;

import jakarta.validation.constraints.NotBlank;

public record QueryRequest(
        @NotBlank String question,
        Integer topK
) {}
