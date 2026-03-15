package com.ryanvo.ifyousayyes.core_api.moderation;

import com.ryanvo.ifyousayyes.core_api.comment.CommentStatus;
import com.ryanvo.ifyousayyes.core_api.comment.SubstanceComment;
import com.ryanvo.ifyousayyes.core_api.comment.SubstanceCommentService;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/moderation/comments")
public class ModerationController {

	private final SubstanceCommentService commentService;

	@Value("${moderation.api-key:}")
	private String moderationApiKey;

	public ModerationController(SubstanceCommentService commentService) {
		this.commentService = commentService;
	}

	private boolean isAuthorized(String key) {
		return key != null && !key.isBlank() && key.equals(moderationApiKey);
	}

	/**
	 * List pending comments. Requires header: X-Moderation-Key: <MODERATION_API_KEY>
	 */
	@GetMapping(produces = MediaType.APPLICATION_JSON_VALUE)
	public ResponseEntity<Page<SubstanceComment>> listPending(
			@RequestHeader(value = "X-Moderation-Key", required = false) String key,
			@RequestParam(defaultValue = "0") int page,
			@RequestParam(defaultValue = "20") int size) {
		if (!isAuthorized(key)) {
			return ResponseEntity.status(401).build();
		}
		return ResponseEntity.ok(commentService.findPending(PageRequest.of(page, size)));
	}

	/**
	 * Approve a comment. Requires header: X-Moderation-Key: <MODERATION_API_KEY>
	 */
	@PatchMapping(value = "/{id}/approve", produces = MediaType.APPLICATION_JSON_VALUE)
	public ResponseEntity<SubstanceComment> approve(
			@RequestHeader(value = "X-Moderation-Key", required = false) String key,
			@PathVariable Long id) {
		if (!isAuthorized(key)) {
			return ResponseEntity.status(401).build();
		}
		try {
			return ResponseEntity.ok(commentService.approve(id));
		} catch (IllegalArgumentException e) {
			return ResponseEntity.notFound().build();
		}
	}

	/**
	 * Reject a comment. Requires header: X-Moderation-Key: <MODERATION_API_KEY>
	 */
	@PatchMapping(value = "/{id}/reject", produces = MediaType.APPLICATION_JSON_VALUE)
	public ResponseEntity<SubstanceComment> reject(
			@RequestHeader(value = "X-Moderation-Key", required = false) String key,
			@PathVariable Long id) {
		if (!isAuthorized(key)) {
			return ResponseEntity.status(401).build();
		}
		try {
			return ResponseEntity.ok(commentService.reject(id));
		} catch (IllegalArgumentException e) {
			return ResponseEntity.notFound().build();
		}
	}
}
