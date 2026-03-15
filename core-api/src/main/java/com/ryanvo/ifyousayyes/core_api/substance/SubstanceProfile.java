package com.ryanvo.ifyousayyes.core_api.substance;

import jakarta.persistence.*;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

import java.math.BigDecimal;

@Entity
@Table(name = "substance_profile")
public class SubstanceProfile {

	@Id
	@GeneratedValue(strategy = GenerationType.IDENTITY)
	private Long id;

	@NotBlank
	@Column(nullable = false, unique = true)
	private String name;

	/** Half-life in hours (e.g. 2.5). */
	@NotNull
	@Column(name = "half_life_hours", nullable = false, precision = 10, scale = 2)
	private BigDecimal halfLife;

	/** Bioavailability as percentage 0–100 (e.g. 85). */
	@NotNull
	@Column(nullable = false, precision = 5, scale = 2)
	private BigDecimal bioavailability;

	/** Standard dosage description (e.g. "250 mg twice daily"). */
	@Column(name = "standard_dosage", length = 512)
	private String standardDosage;

	/** JSON from PsychonautWiki (ROAs with dose/duration). */
	@Column(name = "dosage_json", columnDefinition = "TEXT")
	private String dosageJson;

	/** JSON array of top adverse events from OpenFDA (e.g. [{"term":"NAUSEA","count":123}]). */
	@Column(name = "top_adverse_events_json", columnDefinition = "TEXT")
	private String topAdverseEventsJson;

	/** Addiction potential 0–10 scale (e.g. 7). Used to trigger risk warning in UX. */
	@Column(name = "addiction_potential", precision = 3, scale = 1)
	private BigDecimal addictionPotential;

	/** Drug category for interaction resolution: Stimulant, Opioids, Benzo, Psychedelics, Dissociative, Alcohol, Cannabinoid, Depressant, SSRI, MAOI, Other. */
	@Column(name = "category", length = 32)
	private String category;

	/** Name of a similar TripSit drug for interaction fallback (e.g. "mdma" for a novel stimulant). Null if none or if drug is well‑covered in TripSit. */
	@Column(name = "interaction_reference", length = 128)
	private String interactionReference;

	public Long getId() {
		return id;
	}

	public void setId(Long id) {
		this.id = id;
	}

	public String getName() {
		return name;
	}

	public void setName(String name) {
		this.name = name;
	}

	public BigDecimal getHalfLife() {
		return halfLife;
	}

	public void setHalfLife(BigDecimal halfLife) {
		this.halfLife = halfLife;
	}

	public BigDecimal getBioavailability() {
		return bioavailability;
	}

	public void setBioavailability(BigDecimal bioavailability) {
		this.bioavailability = bioavailability;
	}

	public String getStandardDosage() {
		return standardDosage;
	}

	public void setStandardDosage(String standardDosage) {
		this.standardDosage = standardDosage;
	}

	public String getDosageJson() {
		return dosageJson;
	}

	public void setDosageJson(String dosageJson) {
		this.dosageJson = dosageJson;
	}

	public String getTopAdverseEventsJson() {
		return topAdverseEventsJson;
	}

	public void setTopAdverseEventsJson(String topAdverseEventsJson) {
		this.topAdverseEventsJson = topAdverseEventsJson;
	}

	public BigDecimal getAddictionPotential() {
		return addictionPotential;
	}

	public void setAddictionPotential(BigDecimal addictionPotential) {
		this.addictionPotential = addictionPotential;
	}

	public String getCategory() {
		return category;
	}

	public void setCategory(String category) {
		this.category = category;
	}

	public String getInteractionReference() {
		return interactionReference;
	}

	public void setInteractionReference(String interactionReference) {
		this.interactionReference = interactionReference;
	}
}
