package com.ryanvo.ifyousayyes.core_api.comment;

import jakarta.persistence.*;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

import java.time.Instant;

@Entity
@Table(name = "substance_comment", indexes = {
	@Index(name = "idx_substance_comment_substance_status", columnList = "substance_id, status"),
	@Index(name = "idx_substance_comment_status", columnList = "status")
})
public class SubstanceComment {

	@Id
	@GeneratedValue(strategy = GenerationType.IDENTITY)
	private Long id;

	@NotNull
	@Column(name = "substance_id", nullable = false)
	private Long substanceId;

	@NotBlank
	@Size(max = 4000)
	@Column(nullable = false, columnDefinition = "TEXT")
	private String body;

	@Enumerated(EnumType.STRING)
	@Column(nullable = false, length = 20)
	private CommentStatus status = CommentStatus.PENDING;

	@Column(name = "created_at", nullable = false, updatable = false)
	private Instant createdAt = Instant.now();

	@PrePersist
	void onCreate() {
		if (createdAt == null) createdAt = Instant.now();
	}

	public Long getId() { return id; }
	public void setId(Long id) { this.id = id; }
	public Long getSubstanceId() { return substanceId; }
	public void setSubstanceId(Long substanceId) { this.substanceId = substanceId; }
	public String getBody() { return body; }
	public void setBody(String body) { this.body = body; }
	public CommentStatus getStatus() { return status; }
	public void setStatus(CommentStatus status) { this.status = status; }
	public Instant getCreatedAt() { return createdAt; }
	public void setCreatedAt(Instant createdAt) { this.createdAt = createdAt; }
}
