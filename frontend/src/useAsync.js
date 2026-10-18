import { useCallback, useEffect, useState } from 'react';

export function useAsync(fn, deps) {
  const [state, setState] = useState({ data: null, error: null, loading: true });

  // eslint-disable-next-line react-hooks/exhaustive-deps
  const run = useCallback(fn, deps);

  const load = useCallback(() => {
    let active = true;
    setState((s) => ({ ...s, loading: true, error: null }));
    run()
      .then((data) => active && setState({ data, error: null, loading: false }))
      .catch((error) => active && setState({ data: null, error, loading: false }));
    return () => {
      active = false;
    };
  }, [run]);

  useEffect(() => load(), [load]);

  return { ...state, reload: load, setData: (data) => setState((s) => ({ ...s, data })) };
}
