package com.ryanvo.ifyousayyes.core_api.comment;

import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

import jakarta.validation.Valid;

@RestController
@RequestMapping("/api/substances/{substanceId}/comments")
public class SubstanceCommentController {

	private final SubstanceCommentService commentService;
	private final com.ryanvo.ifyousayyes.core_api.substance.SubstanceProfileService substanceService;

	public SubstanceCommentController(SubstanceCommentService commentService,
			com.ryanvo.ifyousayyes.core_api.substance.SubstanceProfileService substanceService) {
		this.commentService = commentService;
		this.substanceService = substanceService;
	}

	/**
	 * List approved comments for a substance (anonymous community thread). No auth required.
	 */
	@GetMapping(produces = MediaType.APPLICATION_JSON_VALUE)
	public ResponseEntity<List<SubstanceComment>> getComments(@PathVariable Long substanceId) {
		if (substanceService.findById(substanceId).isEmpty()) {
			return ResponseEntity.notFound().build();
		}
		return ResponseEntity.ok(commentService.findApprovedBySubstanceId(substanceId));
	}

	/**
	 * Submit a comment (anonymous). No login required. Comment is created as PENDING until a moderator approves.
	 */
	@PostMapping(consumes = MediaType.APPLICATION_JSON_VALUE, produces = MediaType.APPLICATION_JSON_VALUE)
	public ResponseEntity<SubstanceComment> postComment(@PathVariable Long substanceId,
			@Valid @RequestBody CommentDto dto) {
		if (substanceService.findById(substanceId).isEmpty()) {
			return ResponseEntity.notFound().build();
		}
		SubstanceComment created = commentService.create(substanceId, dto.body());
		return ResponseEntity.status(201).body(created);
	}
}
