import { PlanetDetailPageClient } from "../../../components/entity-pages-client";

type PlanetDetailPageProps = {
  params: Promise<{
    slug: string;
  }>;
};

export default async function PlanetDetailPage({ params }: PlanetDetailPageProps) {
  const { slug } = await params;
  return <PlanetDetailPageClient slug={slug} />;
}
