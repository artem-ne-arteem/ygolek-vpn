import Link from "next/link";
import { Plan, botDeepLink } from "@/lib/plans";

export function PlanCard({ plan }: { plan: Plan }) {
  return (
    <div
      className={`group flex flex-col gap-4 rounded-2xl border p-6 transition-all duration-300 hover:-translate-y-1 ${
        plan.highlighted
          ? "border-accent bg-accent/5 hover:shadow-[0_0_50px_rgba(255,107,53,0.25)]"
          : "border-white/10 bg-panel hover:border-accent/40"
      }`}
    >
      {plan.highlighted && (
        <span className="w-fit rounded-full bg-accent px-3 py-1 text-xs font-semibold text-ink">
          Популярный
        </span>
      )}
      <div>
        <h3 className="text-xl font-semibold">{plan.title}</h3>
        <p className="mt-1 text-sm text-white/60">{plan.trafficLabel}</p>
      </div>
      <p className="text-2xl font-bold text-accent">{plan.priceLabel}</p>
      <div className="mt-auto flex flex-col gap-2">
        <Link
          href="/account"
          className="shine rounded-full bg-white px-4 py-2 text-center font-medium text-ink transition-transform hover:bg-white/90 group-hover:scale-[1.02]"
        >
          Оформить на сайте
        </Link>
        <a
          href={botDeepLink(plan.id)}
          target="_blank"
          rel="noreferrer"
          className="text-center text-xs text-white/40 hover:text-white/70"
        >
          или в боте
        </a>
      </div>
    </div>
  );
}
