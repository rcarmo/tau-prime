import { useCallback, useEffect, useState } from "preact/hooks";

export type ResourceState<T> = {
  data: T | null;
  error: Error | null;
  loading: boolean;
  refresh: () => Promise<void>;
};

export function useResource<T>(load: () => Promise<T>, dependencies: readonly unknown[] = []): ResourceState<T> {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [loading, setLoading] = useState(true);
  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setData(await load());
    } catch (reason) {
      setError(reason instanceof Error ? reason : new Error(String(reason)));
    } finally {
      setLoading(false);
    }
  }, dependencies);
  useEffect(() => { void refresh(); }, [refresh]);
  return { data, error, loading, refresh };
}
