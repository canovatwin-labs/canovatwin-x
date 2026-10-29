import { useEffect, useState, type DependencyList } from 'react';

export function useLoad<T>(load: () => Promise<T>, dependencies: DependencyList) {
  const [state, setState] = useState<{ data?: T; error?: unknown; loading: boolean }>({
    loading: true,
  });
  useEffect(() => {
    let current = true;
    setState({ loading: true });
    load().then(
      (data) => {
        if (current) setState({ data, loading: false });
      },
      (error) => {
        if (current) setState({ error, loading: false });
      },
    );
    return () => {
      current = false;
    };
  }, dependencies);
  return state;
}

export function useRoute() {
  const [route, setRoute] = useState(window.location.hash.slice(1) || '/incidents');
  useEffect(() => {
    const update = () => setRoute(window.location.hash.slice(1) || '/incidents');
    window.addEventListener('hashchange', update);
    return () => window.removeEventListener('hashchange', update);
  }, []);
  return route;
}
