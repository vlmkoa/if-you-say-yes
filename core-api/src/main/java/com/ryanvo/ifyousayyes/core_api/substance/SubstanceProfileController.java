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
	 * Paginated list of substance profiles.
	 * Default: page=0, size=20, sort=name,asc.
	 */
	@GetMapping(produces = MediaType.APPLICATION_JSON_VALUE)
	public Page<SubstanceProfile> getSubstances(
			@RequestParam(defaultValue = "0") int page,
			@RequestParam(defaultValue = "20") int size,
			@RequestParam(defaultValue = "name") String sortBy,
			@RequestParam(defaultValue = "asc") String sortDir) {

		Sort.Direction direction = "desc".equalsIgnoreCase(sortDir) ? Sort.Direction.DESC : Sort.Direction.ASC;
		Pageable pageable = PageRequest.of(page, size, Sort.by(direction, sortBy));
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
}
