package com.ryanvo.ifyousayyes.core_api.comment;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface SubstanceCommentRepository extends JpaRepository<SubstanceComment, Long> {

	List<SubstanceComment> findBySubstanceIdAndStatusOrderByCreatedAtDesc(Long substanceId, CommentStatus status);

	Page<SubstanceComment> findByStatus(CommentStatus status, Pageable pageable);
}
