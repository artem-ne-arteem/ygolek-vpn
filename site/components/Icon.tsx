// Набор линейных иконок 24×24 (stroke), чтобы не тянуть отдельную библиотеку
const PATHS = {
  cart: "M3 4h2l2.4 10.2a1.5 1.5 0 0 0 1.5 1.1h7.7a1.5 1.5 0 0 0 1.4-1l2-6.3H6.2M9.5 20a1 1 0 1 0 0-.01M17 20a1 1 0 1 0 0-.01",
  user: "M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8Zm-7 8a7 7 0 0 1 14 0",
  key: "M15 7a4 4 0 1 1-3.9 4.9L4 19v-3h2v-2h2l1.6-1.6A4 4 0 0 1 15 7Zm1 3h.01",
  book: "M5 4h9a3 3 0 0 1 3 3v13H8a3 3 0 0 1-3-3V4Zm0 13a3 3 0 0 1 3-3h9",
  chat: "M4 5h16v11H9l-5 4V5Zm4 5h.01M12 10h.01M16 10h.01",
  doc: "M7 3h7l5 5v13H7V3Zm7 0v5h5M10 13h6M10 17h6",
  shield: "M12 3 5 6v6c0 4.4 3 7.6 7 9 4-1.4 7-4.6 7-9V6l-7-3Zm-3 9 2 2 4-4",
  devices: "M4 5h12v9H4V5Zm-1 12h14M18 9h3v10h-3V9Z",
  infinity: "M7.5 15.5a3.5 3.5 0 1 1 0-7c3.5 0 5.5 7 9 7a3.5 3.5 0 1 0 0-7c-3.5 0-5.5 7-9 7Z",
  bolt: "M13 3 5 14h6l-1 7 8-11h-6l1-7Z",
  home: "M4 11 12 4l8 7v9h-5v-6H9v6H4v-9Z",
  star: "m12 4 2.5 5 5.5.8-4 3.9.9 5.5L12 16.6l-4.9 2.6.9-5.5-4-3.9 5.5-.8L12 4Z",
  arrow: "M5 12h14m-5-5 5 5-5 5",
  copy: "M9 9h10v10H9V9Zm-4 6V5h10",
  check: "m5 12 4 4 10-10",
  logout: "M15 4h4v16h-4M10 8l-4 4 4 4M6 12h10",
  send: "M21 4 3 11l7 2 2 7 9-16Zm-11 9 5-5",
  alert: "M12 4 3 20h18L12 4Zm0 6v4m0 3h.01",
  menu: "M4 7h16M4 12h16M4 17h16",
} as const;

export type IconName = keyof typeof PATHS;

export function Icon({ name, className = "h-5 w-5" }: { name: IconName; className?: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.7}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
    >
      <path d={PATHS[name]} />
    </svg>
  );
}
