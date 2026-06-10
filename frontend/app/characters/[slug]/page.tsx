import { CharacterDetailPageClient } from "../../../components/entity-pages-client";

type CharacterDetailPageProps = {
  params: Promise<{
    slug: string;
  }>;
};

export default async function CharacterDetailPage({ params }: CharacterDetailPageProps) {
  const { slug } = await params;
  return <CharacterDetailPageClient slug={slug} />;
}
