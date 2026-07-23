package com.ragassistant.repository;

import com.ragassistant.entity.DocumentEntity;
import com.ragassistant.entity.User;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

public interface DocumentRepository extends JpaRepository<DocumentEntity, UUID> {

    List<DocumentEntity> findByOwner(User owner);

    Optional<DocumentEntity> findByIdAndOwner(UUID id, User owner);
}
