package com.ryanvo.ifyousayyes.core_api.substance;

import jakarta.validation.constraints.NotBlank;

/**
 * DTO for syncing dosage (PsychonautWiki) and adverse events (OpenFDA) into a substance profile.
 * If no profile exists, one is created with default halfLife/bioavailability (0).
 */
public record SubstanceSyncDto(
		@NotBlank String name,
		String dosageJson,
		String topAdverseEventsJson
) {}
