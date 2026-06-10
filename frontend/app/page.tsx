import { HomePageClient } from "../components/home-page-client";

type HomePageProps = {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

export default async function HomePage({ searchParams }: HomePageProps) {
  const resolvedSearchParams = searchParams ? await searchParams : {};
  return <HomePageClient initialSearchParams={resolvedSearchParams} />;
}
