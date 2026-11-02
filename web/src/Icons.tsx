export function NavIcon({ name }: { name: string }) {
  const paths: Record<string, string> = {
    operations: 'M3 3h7v7H3zM14 3h7v7h-7zM3 14h7v7H3zM14 14h7v7h-7z',
    assets: 'M4 3h16v18H4zM8 7h8M8 11h8M8 15h3M15 18h1',
    incidents: 'M12 3 3 7v5c0 5 9 9 9 9s9-4 9-9V7zM12 8v5M12 16h.01',
    new: 'M12 3v18M3 12h18',
    agents: 'M8 3h8v4H8zM3 17h6v4H3zM15 17h6v4h-6zM12 7v5M6 17v-5h12v5',
    stream: 'M2 12h4l3-8 6 16 3-8h4',
    compare: 'M3 5h8M3 10h5M3 15h8M3 20h5M16 3v18M20 6h2M20 12h2M20 18h2',
  };
  return (
    <svg
      aria-hidden="true"
      width="20"
      height="20"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d={paths[name] ?? paths.operations} />
    </svg>
  );
}
