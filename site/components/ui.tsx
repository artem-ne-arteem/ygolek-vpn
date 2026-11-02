import Link from "next/link";
import { Icon, type IconName } from "./Icon";

export function Logo({ compact = false }: { compact?: boolean }) {
  return (
    <Link href="/" className="flex items-center gap-2.5 font-semibold tracking-tight">
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src="/logo.jpg" alt="" className="h-8 w-8 rounded-lg bg-white object-cover" />
      {!compact && <span className="whitespace-nowrap text-[17px]">Ygolek VPN</span>}
    </Link>
  );
}

/** Карточка-действие: иконка в квадрате, стрелка, заголовок и подпись. */
export function ActionCard({
  icon,
  title,
  text,
  href,
  onClick,
}: {
  icon: IconName;
  title: string;
  text: string;
  href?: string;
  onClick?: () => void;
}) {
  const inner = (
    <>
      <div className="flex items-start justify-between">
        <span className="icon-box transition-colors group-hover:bg-accent/20">
          <Icon name={icon} />
        </span>
        <Icon
          name="arrow"
          className="h-5 w-5 text-muted transition-transform duration-200 group-hover:translate-x-1 group-hover:text-white"
        />
      </div>
      <h3 className="mt-5 font-semibold">{title}</h3>
      <p className="mt-1 text-sm leading-snug text-muted">{text}</p>
    </>
  );
  const className = "card group block h-full p-5 text-left transition-colors hover:border-accent/40";

  if (onClick) {
    return (
      <button onClick={onClick} className={`${className} w-full`}>
        {inner}
      </button>
    );
  }
  const external = href?.startsWith("http");
  return external ? (
    <a href={href} target="_blank" rel="noreferrer" className={className}>
      {inner}
    </a>
  ) : (
    <Link href={href ?? "/"} className={className}>
      {inner}
    </Link>
  );
}

/** Маленькая карточка с крупным значением — как счётчики в дашборде. */
export function StatCard({ value, label, icon }: { value: string; label: string; icon: IconName }) {
  return (
    <div className="card flex items-start justify-between p-5">
      <div>
        <p className="text-2xl font-bold leading-none tracking-tight">{value}</p>
        <p className="mt-2 text-sm text-muted">{label}</p>
      </div>
      <Icon name={icon} className="h-5 w-5 text-accent" />
    </div>
  );
}

/** Таблица «ключ — значение» с тонкими разделителями. */
export function InfoTable({ rows }: { rows: { label: string; value: React.ReactNode }[] }) {
  return (
    <div className="overflow-hidden rounded-xl border border-line">
      {rows.map((row) => (
        <div
          key={row.label}
          className="flex items-center justify-between gap-4 border-b border-line bg-panel2/40 px-4 py-3 text-sm last:border-b-0"
        >
          <span className="text-muted">{row.label}</span>
          <span className="text-right font-medium">{row.value}</span>
        </div>
      ))}
    </div>
  );
}

export function Chip({ children }: { children: React.ReactNode }) {
  return (
    <span className="rounded-md border border-line bg-panel2 px-2 py-0.5 font-mono text-xs text-white/90">
      {children}
    </span>
  );
}

/** Карточка «Полезное»: список ссылок со стрелками. */
export function LinksCard({ links }: { links: { label: string; href: string }[] }) {
  return (
    <div className="card h-full p-6">
      <p className="label-dot">Ссылки</p>
      <h2 className="mt-1 text-lg font-semibold">Полезное</h2>
      <ul className="mt-4">
        {links.map((link) => {
          const external = link.href.startsWith("http");
          const className =
            "group flex items-center justify-between border-b border-line py-3 text-sm font-medium transition-colors last:border-b-0 hover:text-accent2";
          const arrow = (
            <Icon name="arrow" className="h-4 w-4 text-muted transition-transform group-hover:translate-x-1" />
          );
          return (
            <li key={link.label}>
              {external ? (
                <a href={link.href} target="_blank" rel="noreferrer" className={className}>
                  {link.label}
                  {arrow}
                </a>
              ) : (
                <Link href={link.href} className={className}>
                  {link.label}
                  {arrow}
                </Link>
              )}
            </li>
          );
        })}
      </ul>
    </div>
  );
}
