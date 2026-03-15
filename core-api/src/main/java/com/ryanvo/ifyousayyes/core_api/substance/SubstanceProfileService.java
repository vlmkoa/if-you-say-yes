package com.ryanvo.ifyousayyes.core_api.substance;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.util.Optional;

@Service
public class SubstanceProfileService {

	private final SubstanceProfileRepository repository;

	public SubstanceProfileService(SubstanceProfileRepository repository) {
		this.repository = repository;
	}

	@Transactional(readOnly = true)
	public Optional<SubstanceProfile> findById(Long id) {
		return repository.findById(id);
	}

	@Transactional(readOnly = true)
	public Optional<SubstanceProfile> findByNameIgnoreCase(String name) {
		return repository.findByNameIgnoreCase(name);
	}

	/** Update only interactionReference for a substance by name (for LLM backfill). */
	@Transactional
	public Optional<SubstanceProfile> updateInteractionReference(String name, String interactionReference) {
		return repository.findByNameIgnoreCase(name != null ? name.trim() : null)
			.map(profile -> {
				profile.setInteractionReference(interactionReference);
				return repository.save(profile);
			});
	}

	/** Update category and/or interactionReference for a substance by name. Null values are not written. */
	@Transactional
	public Optional<SubstanceProfile> patchByName(String name, String category, String interactionReference) {
		return repository.findByNameIgnoreCase(name != null ? name.trim() : null)
			.map(profile -> {
				if (category != null) {
					profile.setCategory(category);
				}
				if (interactionReference != null) {
					profile.setInteractionReference(interactionReference);
				}
				return repository.save(profile);
			});
	}

	/** Update category and/or interactionReference by id (no name in URL; avoids 403 from URL filters). */
	@Transactional
	public Optional<SubstanceProfile> patchById(Long id, String category, String interactionReference) {
		return repository.findById(id)
			.map(profile -> {
				if (category != null) {
					profile.setCategory(category);
				}
				if (interactionReference != null) {
					profile.setInteractionReference(interactionReference);
				}
				return repository.save(profile);
			});
	}

	@Transactional(readOnly = true)
	public Page<SubstanceProfile> findAll(Pageable pageable) {
		return repository.findAll(pageable);
	}

	@Transactional(readOnly = true)
	public Page<SubstanceProfile> searchByName(String name, Pageable pageable) {
		if (name == null || name.isBlank()) {
			return repository.findAll(pageable);
		}
		return repository.findAllByNameContainingIgnoreCase(name.trim(), pageable);
	}

	/**
	 * Upsert dosage and/or adverse events for a substance by name.
	 * If the profile does not exist, creates one with default halfLife and bioavailability (0).
	 */
	@Transactional
	public SubstanceProfile syncDosageAndAdverseEvents(SubstanceSyncDto dto) {
		Optional<SubstanceProfile> existing = repository.findByNameIgnoreCase(dto.name());
		SubstanceProfile profile;
		if (existing.isPresent()) {
			profile = existing.get();
			if (dto.dosageJson() != null) {
				profile.setDosageJson(dto.dosageJson());
			}
			if (dto.topAdverseEventsJson() != null) {
				profile.setTopAdverseEventsJson(dto.topAdverseEventsJson());
			}
			if (dto.halfLife() != null) {
				profile.setHalfLife(dto.halfLife());
			}
			if (dto.bioavailability() != null) {
				profile.setBioavailability(dto.bioavailability());
			}
			if (dto.addictionPotential() != null) {
				profile.setAddictionPotential(dto.addictionPotential());
			}
			if (dto.category() != null) {
				profile.setCategory(dto.category());
			}
			if (dto.interactionReference() != null) {
				profile.setInteractionReference(dto.interactionReference());
			}
		} else {
			profile = new SubstanceProfile();
			profile.setName(dto.name());
			profile.setHalfLife(dto.halfLife() != null ? dto.halfLife() : BigDecimal.ZERO);
			profile.setBioavailability(dto.bioavailability() != null ? dto.bioavailability() : BigDecimal.ZERO);
			profile.setDosageJson(dto.dosageJson());
			profile.setTopAdverseEventsJson(dto.topAdverseEventsJson());
			if (dto.addictionPotential() != null) {
				profile.setAddictionPotential(dto.addictionPotential());
			}
			if (dto.category() != null) {
				profile.setCategory(dto.category());
			}
			if (dto.interactionReference() != null) {
				profile.setInteractionReference(dto.interactionReference());
			}
		}
		return repository.save(profile);
	}
}
