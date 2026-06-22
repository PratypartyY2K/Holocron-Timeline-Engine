import { HomePageClient } from "../../components/home-page-client";

type EventsPageProps = {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

export default async function EventsPage({ searchParams }: EventsPageProps) {
  const resolvedSearchParams = searchParams ? await searchParams : {};
  return <HomePageClient initialSearchParams={resolvedSearchParams} eventsOnly />;
}
