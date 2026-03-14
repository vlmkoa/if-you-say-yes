package com.ryanvo.ifyousayyes.core_api.substance;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class SubstanceProfileService {

	private final SubstanceProfileRepository repository;

	public SubstanceProfileService(SubstanceProfileRepository repository) {
		this.repository = repository;
	}

	@Transactional(readOnly = true)
	public Page<SubstanceProfile> findAll(Pageable pageable) {
		return repository.findAllByOrderByNameAsc(pageable);
	}
}
