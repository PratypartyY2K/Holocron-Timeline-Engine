"use client";

import { useEffect, useState, type DependencyList } from "react";

type AsyncDataState<T> = {
  data: T | null;
  error: string | null;
  isLoading: boolean;
};

export function useAsyncData<T>(
  load: () => Promise<T>,
  dependencies: DependencyList,
): AsyncDataState<T> {
  const [state, setState] = useState<AsyncDataState<T>>({
    data: null,
    error: null,
    isLoading: true,
  });

  useEffect(() => {
    let isActive = true;

    setState({
      data: null,
      error: null,
      isLoading: true,
    });

    void load()
      .then((data) => {
        if (!isActive) {
          return;
        }
        setState({
          data,
          error: null,
          isLoading: false,
        });
      })
      .catch((error: unknown) => {
        if (!isActive) {
          return;
        }
        setState({
          data: null,
          error: error instanceof Error ? error.message : "Unexpected request failure.",
          isLoading: false,
        });
      });

    return () => {
      isActive = false;
    };
    // This hook intentionally accepts a caller-provided dependency list.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, dependencies);

  return state;
}
