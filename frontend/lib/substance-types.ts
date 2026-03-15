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
  /** Possible effects. For future APIs. */
  effects?: string | null;
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
