package com.ryanvo.ifyousayyes.core_api.comment;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record CommentDto(
		@NotBlank @Size(min = 1, max = 4000) String body
) {}
