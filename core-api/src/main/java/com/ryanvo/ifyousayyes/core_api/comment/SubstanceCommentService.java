package com.ryanvo.ifyousayyes.core_api.comment;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
public class SubstanceCommentService {

	private final SubstanceCommentRepository repository;

	public SubstanceCommentService(SubstanceCommentRepository repository) {
		this.repository = repository;
	}

	@Transactional(readOnly = true)
	public List<SubstanceComment> findApprovedBySubstanceId(Long substanceId) {
		return repository.findBySubstanceIdAndStatusOrderByCreatedAtDesc(substanceId, CommentStatus.APPROVED);
	}

	@Transactional
	public SubstanceComment create(Long substanceId, String body) {
		SubstanceComment c = new SubstanceComment();
		c.setSubstanceId(substanceId);
		c.setBody(body == null ? "" : body.trim());
		c.setStatus(CommentStatus.PENDING);
		return repository.save(c);
	}

	@Transactional(readOnly = true)
	public Page<SubstanceComment> findPending(Pageable pageable) {
		return repository.findByStatus(CommentStatus.PENDING, pageable);
	}

	@Transactional(readOnly = true)
	public java.util.Optional<SubstanceComment> findById(Long id) {
		return repository.findById(id);
	}

	@Transactional
	public SubstanceComment approve(Long id) {
		return repository.findById(id)
			.map(c -> {
				c.setStatus(CommentStatus.APPROVED);
				return repository.save(c);
			})
			.orElseThrow(() -> new IllegalArgumentException("Comment not found: " + id));
	}

	@Transactional
	public SubstanceComment reject(Long id) {
		return repository.findById(id)
			.map(c -> {
				c.setStatus(CommentStatus.REJECTED);
				return repository.save(c);
			})
			.orElseThrow(() -> new IllegalArgumentException("Comment not found: " + id));
	}
}
