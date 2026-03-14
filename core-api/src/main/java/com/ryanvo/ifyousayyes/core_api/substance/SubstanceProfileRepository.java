package com.ryanvo.ifyousayyes.core_api.substance;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface SubstanceProfileRepository extends JpaRepository<SubstanceProfile, Long> {

	Page<SubstanceProfile> findAllByOrderByNameAsc(Pageable pageable);
}
