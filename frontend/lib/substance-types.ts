/**
 * Matches Spring Boot SubstanceProfile and paginated response.
 * API: GET /api/substances?page=0&size=20
 */
export interface SubstanceProfile {
  id: number;
  name: string;
  halfLife: number;
  bioavailability: number;
  standardDosage: string | null;
  /** PsychonautWiki dosage profile JSON (ROAs, dose, duration). */
  dosageJson?: string | null;
  /** OpenFDA top adverse events JSON array. */
  topAdverseEventsJson?: string | null;
  /** Classification/category (e.g. stimulant, depressant). For future APIs. */
  classification?: string | null;
  /** Drug category for interaction resolution: Stimulant, Opioids, Benzo, Psychedelics, Dissociative, Alcohol, etc. */
  category?: string | null;
  /** Similar TripSit drug name for interaction fallback (less popular drugs). */
  interactionReference?: string | null;
  /** Possible effects. For future APIs. */
  effects?: string | null;
  /** Addiction potential 0–10. When &gt; 7, risk warning is shown before dosage data. */
  addictionPotential?: number | null;
}

export interface PagedSubstances {
  content: SubstanceProfile[];
  totalElements: number;
  totalPages: number;
  size: number;
  number: number;
  first: boolean;
  last: boolean;
}
