import { HomePageClient } from "../components/home-page-client";

type HomePageProps = {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

export default async function HomePage({ searchParams }: HomePageProps) {
  const resolvedSearchParams = searchParams ? await searchParams : {};
  const hasActiveParams = Object.values(resolvedSearchParams).some((value) => {
    if (typeof value === "string") {
      return value.trim() !== "";
    }
    if (Array.isArray(value)) {
      return value.some((item) => item.trim() !== "");
    }
    return false;
  });

  return <HomePageClient initialSearchParams={resolvedSearchParams} landingOnly={!hasActiveParams} />;
}
