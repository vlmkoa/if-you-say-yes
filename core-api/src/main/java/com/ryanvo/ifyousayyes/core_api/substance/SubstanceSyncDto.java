package com.ryanvo.ifyousayyes.core_api.substance;

import jakarta.validation.constraints.NotBlank;

import java.math.BigDecimal;

/**
 * DTO for syncing dosage (PsychonautWiki), adverse events (OpenFDA), and optional half-life/bioavailability.
 * If no profile exists, one is created with default halfLife/bioavailability (0) when not provided.
 */
public record SubstanceSyncDto(
		@NotBlank String name,
		String dosageJson,
		String topAdverseEventsJson,
		BigDecimal halfLife,
		BigDecimal bioavailability,
		BigDecimal addictionPotential
) {}
