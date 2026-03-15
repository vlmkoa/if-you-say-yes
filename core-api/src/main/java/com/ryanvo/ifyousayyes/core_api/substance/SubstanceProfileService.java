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
	public Page<SubstanceProfile> findAll(Pageable pageable) {
		return repository.findAllByOrderByNameAsc(pageable);
	}

	/**
	 * Upsert dosage and/or adverse events for a substance by name.
	 * If the profile does not exist, creates one with default halfLife and bioavailability (0).
	 */
	@Transactional
	public SubstanceProfile syncDosageAndAdverseEvents(SubstanceSyncDto dto) {
		Optional<SubstanceProfile> existing = repository.findByName(dto.name());
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
		} else {
			profile = new SubstanceProfile();
			profile.setName(dto.name());
			profile.setHalfLife(dto.halfLife() != null ? dto.halfLife() : BigDecimal.ZERO);
			profile.setBioavailability(dto.bioavailability() != null ? dto.bioavailability() : BigDecimal.ZERO);
			profile.setDosageJson(dto.dosageJson());
			profile.setTopAdverseEventsJson(dto.topAdverseEventsJson());
		}
		return repository.save(profile);
	}
}
