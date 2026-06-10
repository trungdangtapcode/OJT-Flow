import pageGuides from "../../data/page-guides.json";
import {
  GuideGrid,
  GuideItem,
  GuidePanel,
  ManualLink,
} from "../ui/guide-panel";

type PageGuide = {
  id: string;
  path: string;
  title: string;
  summary: string;
  items: Array<{ title: string; text: string }>;
  nextAction: string;
};

const guides = pageGuides as PageGuide[];

export function PageGuide({ pathname }: { pathname: string }) {
  const guide = pageGuideForPath(pathname);
  if (!guide) return null;

  return (
    <GuidePanel className="mb-4" title={guide.title}>
      <div className="grid gap-3">
        <p className="text-sm leading-6 text-muted-foreground">{guide.summary}</p>
        <GuideGrid columns="lg:grid-cols-3">
          {guide.items.map((item) => (
            <GuideItem key={item.title} title={item.title}>
              {item.text}
            </GuideItem>
          ))}
        </GuideGrid>
        <div className="flex flex-wrap items-center justify-between gap-3 rounded-md border border-border bg-card px-3 py-2 text-sm">
          <span className="font-semibold text-muted-foreground">{guide.nextAction}</span>
          <ManualLink>Open manual</ManualLink>
        </div>
      </div>
    </GuidePanel>
  );
}

function pageGuideForPath(pathname: string): PageGuide | null {
  const exact = guides.find((guide) => pathname === guide.path);
  if (exact) return exact;
  return (
    guides
      .filter((guide) => guide.path !== "/" && pathname.startsWith(`${guide.path}/`))
      .sort((a, b) => b.path.length - a.path.length)[0] ?? null
  );
}
