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
    <GuidePanel className="mb-3" title={guide.title}>
      <div className="grid gap-2 text-sm">
        <GuideGrid columns="lg:grid-cols-3">
          {guide.items.map((item) => (
            <GuideItem key={item.title} title={item.title}>
              {item.text}
            </GuideItem>
          ))}
        </GuideGrid>
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
