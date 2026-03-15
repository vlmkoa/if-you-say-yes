package com.ryanvo.ifyousayyes.core_api.substance;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

import jakarta.validation.Valid;

@RestController
@RequestMapping("/api/substances")
public class SubstanceProfileController {

	private final SubstanceProfileService service;

	public SubstanceProfileController(SubstanceProfileService service) {
		this.service = service;
	}

	/**
	 * Get a single substance profile by id.
	 */
	@GetMapping(value = "/{id}", produces = MediaType.APPLICATION_JSON_VALUE)
	public ResponseEntity<SubstanceProfile> getSubstanceById(@PathVariable Long id) {
		return service.findById(id)
			.map(ResponseEntity::ok)
			.orElse(ResponseEntity.notFound().build());
	}

	/**
	 * Update category and/or interactionReference by id (avoids drug name in URL; use for scripts to avoid 403 from filters).
	 */
	@org.springframework.web.bind.annotation.PatchMapping(value = "/{id}", consumes = MediaType.APPLICATION_JSON_VALUE, produces = MediaType.APPLICATION_JSON_VALUE)
	public ResponseEntity<SubstanceProfile> patchById(
			@PathVariable Long id,
			@RequestBody java.util.Map<String, String> body) {
		String cat = body != null ? body.get("category") : null;
		String ref = body != null ? body.get("interactionReference") : null;
		return service.patchById(id, cat, ref)
			.map(ResponseEntity::ok)
			.orElse(ResponseEntity.notFound().build());
	}

	private static final List<String> ALLOWED_SORT_FIELDS = List.of("name", "halfLife", "bioavailability", "id");

	/**
	 * Paginated list of substance profiles. Optional search by name (q). Sort by name, halfLife, bioavailability, or id.
	 * Default: page=0, size=20, sort=name,asc.
	 */
	@GetMapping(produces = MediaType.APPLICATION_JSON_VALUE)
	public Page<SubstanceProfile> getSubstances(
			@RequestParam(defaultValue = "0") int page,
			@RequestParam(defaultValue = "20") int size,
			@RequestParam(defaultValue = "name") String sortBy,
			@RequestParam(defaultValue = "asc") String sortDir,
			@RequestParam(required = false) String q) {

		String safeSort = ALLOWED_SORT_FIELDS.contains(sortBy) ? sortBy : "name";
		Sort.Direction direction = "desc".equalsIgnoreCase(sortDir) ? Sort.Direction.DESC : Sort.Direction.ASC;
		Pageable pageable = PageRequest.of(page, size, Sort.by(direction, safeSort));
		if (q != null && !q.isBlank()) {
			return service.searchByName(q, pageable);
		}
		return service.findAll(pageable);
	}

	/**
	 * Sync dosage (PsychonautWiki) and/or adverse events (OpenFDA) for a substance.
	 * Creates a new profile with default halfLife/bioavailability if one does not exist.
	 */
	@PostMapping(value = "/sync", consumes = MediaType.APPLICATION_JSON_VALUE, produces = MediaType.APPLICATION_JSON_VALUE)
	public ResponseEntity<SubstanceProfile> syncSubstance(@Valid @RequestBody SubstanceSyncDto dto) {
		return ResponseEntity.ok(service.syncDosageAndAdverseEvents(dto));
	}

	/**
	 * Update only interactionReference for a substance (by name). Used by scripts to set
	 * a similar TripSit drug for interaction fallback.
	 */
	@GetMapping(value = "/by-name", produces = MediaType.APPLICATION_JSON_VALUE)
	public ResponseEntity<SubstanceProfile> getSubstanceByName(@RequestParam String name) {
		return service.findByNameIgnoreCase(name != null ? name.trim() : "")
			.map(ResponseEntity::ok)
			.orElse(ResponseEntity.notFound().build());
	}

	@org.springframework.web.bind.annotation.PatchMapping(value = "/by-name", consumes = MediaType.APPLICATION_JSON_VALUE, produces = MediaType.APPLICATION_JSON_VALUE)
	public ResponseEntity<SubstanceProfile> patchByName(
			@RequestParam String name,
			@RequestBody java.util.Map<String, String> body) {
		String cat = body != null ? body.get("category") : null;
		String ref = body != null ? body.get("interactionReference") : null;
		return service.patchByName(name, cat, ref)
			.map(ResponseEntity::ok)
			.orElse(ResponseEntity.notFound().build());
	}
}
