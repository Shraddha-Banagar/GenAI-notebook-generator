import { ChevronRight } from "lucide-react";

export default function SectionHeading({ index, title, description, icon: Icon }) {
  return (
    <div className="mb-4 flex items-start justify-between gap-4">
      <div>
        <div className="section-kicker">
          <span className="flex h-5 w-5 items-center justify-center rounded-md border border-ember-300/20 bg-ember-300/10 text-[10px] text-ember-300">
            {index}
          </span>
          <span>{title}</span>
        </div>
        {description ? <p className="section-copy max-w-xl">{description}</p> : null}
      </div>
      {Icon ? (
        <div className="hidden h-9 w-9 shrink-0 items-center justify-center rounded-xl border border-zinc-200 bg-zinc-100 text-zinc-500 sm:flex dark:border-white/10 dark:bg-white/[0.03]">
          <Icon className="h-4 w-4" />
        </div>
      ) : (
        <ChevronRight className="mt-1 h-4 w-4 shrink-0 text-zinc-400 dark:text-zinc-700" />
      )}
    </div>
  );
}
