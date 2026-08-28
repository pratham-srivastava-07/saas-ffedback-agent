"use client";

import { PageHeader } from "@/components/app/shell";
import { ErrorState, SkeletonRows } from "@/components/app/states";
import { FeatureAreas } from "@/components/app/feature-areas";
import { api } from "@/lib/api";
import { useApi } from "@/lib/use-api";

export default function AreasPage() {
  const { data, error, loading, reload } = useApi(() => api.featureAreas(30), []);

  return (
    <>
      <PageHeader
        title="Product areas"
        description="Which parts of the product your feedback is about, and who would own each one."
      />

      <div className="px-5 py-6 sm:px-8">
        {loading && <SkeletonRows rows={5} />}
        {error && !loading && <ErrorState message={error} onRetry={reload} />}
        {data && !loading && <FeatureAreas data={data} />}
      </div>
    </>
  );
}
