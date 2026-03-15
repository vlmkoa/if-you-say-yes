import { SubstanceProfilePage } from "./SubstanceProfilePage";

type PageProps = {
  params: { id: string };
};

export default function DashboardSubstancePage({ params }: PageProps) {
  return <SubstanceProfilePage id={params.id} />;
}
