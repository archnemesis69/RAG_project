package com.ragassistant.config;

import io.netty.channel.ChannelOption;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.client.reactive.ReactorClientHttpConnector;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.netty.http.client.HttpClient;

import java.time.Duration;

@Configuration
public class WebClientConfig {

    @Value("${app.ai-service.base-url}")
    private String aiServiceBaseUrl;

    // FIX: the previous WebClient had no timeouts at all. If Ollama is
    // slow, wedged, or the AI service just never responds, the
    // .block() calls in AiServiceClient would hang indefinitely,
    // tying up a Spring thread per stuck request until the pool is
    // exhausted. A response that takes this long is a failure, not a
    // slow success - fail fast and let GlobalExceptionHandler turn it
    // into a proper error response instead.
    @Bean
    public WebClient aiServiceWebClient(WebClient.Builder builder) {
        HttpClient httpClient = HttpClient.create()
                .option(ChannelOption.CONNECT_TIMEOUT_MILLIS, 5_000)
                .responseTimeout(Duration.ofSeconds(600));

        return builder
                .baseUrl(aiServiceBaseUrl)
                .clientConnector(new ReactorClientHttpConnector(httpClient))
                .build();
    }
}
