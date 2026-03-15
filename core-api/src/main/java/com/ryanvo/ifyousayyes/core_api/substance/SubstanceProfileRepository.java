package com.ryanvo.ifyousayyes.core_api.substance;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;

@Repository
public interface SubstanceProfileRepository extends JpaRepository<SubstanceProfile, Long> {

	Page<SubstanceProfile> findAllByNameContainingIgnoreCase(String name, Pageable pageable);

	Optional<SubstanceProfile> findByName(String name);

	/** Case-insensitive: use when syncing to avoid duplicate rows for "Cocaine" vs "cocaine". */
	Optional<SubstanceProfile> findByNameIgnoreCase(String name);
}
