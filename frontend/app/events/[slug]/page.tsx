import { EventDetailPageClient } from "../../../components/event-detail-page-client";

type EventDetailPageProps = {
  params: Promise<{
    slug: string;
  }>;
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

function parseDepth(value: string | string[] | undefined): number {
  if (typeof value !== "string" || value.trim() === "") {
    return 2;
  }
  const parsed = Number.parseInt(value, 10);
  if (Number.isNaN(parsed) || parsed < 1) {
    return 2;
  }
  return parsed;
}

export default async function EventDetailPage({ params, searchParams }: EventDetailPageProps) {
  const { slug } = await params;
  const resolvedSearchParams = searchParams ? await searchParams : {};
  const depth = parseDepth(resolvedSearchParams.depth);
  return <EventDetailPageClient slug={slug} depth={depth} />;
}
