import { FactionDetailPageClient } from "../../../components/entity-pages-client";

type FactionDetailPageProps = {
  params: Promise<{
    slug: string;
  }>;
};

export default async function FactionDetailPage({ params }: FactionDetailPageProps) {
  const { slug } = await params;
  return <FactionDetailPageClient slug={slug} />;
}
