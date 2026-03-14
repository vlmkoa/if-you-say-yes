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
