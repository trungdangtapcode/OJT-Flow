import type * as React from "react";
import { Link } from "@tanstack/react-router";
import {
  Bot,
  BookOpen,
  CheckCircle2,
  ClipboardCheck,
  Database,
  FileCode,
  FileText,
  HelpCircle,
  Layers,
  Search,
  ShieldCheck,
} from "lucide-react";

import { PageHeader } from "../../components/layout/page-header";
import { Badge } from "../../components/ui/badge";
import { Button } from "../../components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "../../components/ui/card";

type HelpMode = "overview" | "tutorials" | "manual";

const helpModes: Array<{
  mode: HelpMode;
  label: string;
  to: "/help" | "/help/tutorials" | "/help/manual";
  description: string;
}> = [
  {
    mode: "overview",
    label: "Start here",
    to: "/help",
    description: "Choose the right page and understand the basic workflow.",
  },
  {
    mode: "tutorials",
    label: "Tutorials",
    to: "/help/tutorials",
    description: "Follow concrete healthcare data tasks step by step.",
  },
  {
    mode: "manual",
    label: "Manual",
    to: "/help/manual",
    description: "Decode output panels, evidence, warnings, and review states.",
  },
];

const glossary = [
  {
    term: "Workflow",
    meaning: "A governed run that parses data, validates it, retrieves evidence, and records an audit trail.",
  },
  {
    term: "Review gate",
    meaning: "A human checkpoint before risky or meaning-changing actions continue.",
  },
  {
    term: "Evidence",
    meaning: "Trusted schema, standard, policy, terminology, or source material used to explain a result.",
  },
  {
    term: "Quality score",
    meaning: "A retrieval readiness score. Low scores mean evidence is missing, weak, unsafe, or needs review.",
  },
  {
    term: "Evidence bucket",
    meaning: "A category of support, such as schema, policy, terminology, FHIR mapping, or source locator.",
  },
  {
    term: "Strategy recommendation",
    meaning: "Backend advice about the retrieval technique being used, such as hybrid search, reranking, or corrective retrieval.",
  },
];

const decisionGuide = [
  {
    situation: "I have a file and I do not know the format",
    destination: "Assistant",
    action: "Attach the file and ask the assistant to identify the format, extract usable text, and explain any warnings.",
    to: "/assistant" as const,
  },
  {
    situation: "I have CSV, JSON, or YAML and need a governed run",
    destination: "Workbench",
    action: "Use Workbench when you want explicit source data, workflow instructions, and review gates.",
    to: "/workbench" as const,
  },
  {
    situation: "The app says human review is required",
    destination: "Reviews",
    action: "Open Reviews, read the reason, then approve, edit, reject, or request clarification.",
    to: "/reviews" as const,
  },
  {
    situation: "I do not trust an explanation yet",
    destination: "Retrieval",
    action: "Open Retrieval to inspect source grounding, evidence readiness, filters, and quality warnings.",
    to: "/retrieval" as const,
  },
];

const tutorials = [
  {
    title: "Validate a lab CSV",
    steps: [
      "Open Assistant.",
      "Paste or attach the CSV.",
      "Ask: Validate this lab CSV and explain issues with trusted evidence.",
      "Read LLM text first, then inspect tool calls and evidence.",
      "If a review is required, open Reviews and approve, edit, reject, or clarify.",
    ],
  },
  {
    title: "Search medical evidence",
    steps: [
      "Open Retrieval.",
      "Start from a preset or type a clinical data question.",
      "Apply source, standard, trust, or domain filters only when they match your goal.",
      "Read the Search cockpit, Evidence readiness, and Strategy recommendations before individual hits.",
      "Use relevance judgments to mark whether retrieved evidence is useful.",
    ],
  },
  {
    title: "Upload a document",
    steps: [
      "Open Workbench for governed uploads, or Assistant for conversational extraction.",
      "Attach CSV, JSON, YAML, PDF, DOCX, or image formats supported by runtime settings.",
      "Check extraction warnings before trusting scanned or image-heavy files.",
      "Run validation or workflow creation after extracted text looks usable.",
    ],
  },
];

const firstRunChecklist = [
  "Confirm the top bar says postgres for persistent storage when testing real workflows.",
  "Open Settings and check upload limits, extraction support, LLM provider, and retrieval runtime settings.",
  "Use Assistant for simple questions; use Workbench when a governed workflow record matters.",
  "Read warnings before output. In healthcare data, warnings are often more important than generated prose.",
  "Keep write actions gated unless you intentionally want the assistant to execute a state-changing action.",
];

const explanationGuide = [
  {
    label: "Completed",
    meaning: "The backend finished the requested operation. It does not mean the data is clinically correct.",
    next: "Read warnings, evidence, and limitations before using the result.",
  },
  {
    label: "Needs human review",
    meaning: "The workflow found risk, uncertainty, missing evidence, PHI, or a meaning-changing action.",
    next: "Open Reviews. Do not treat the output as final until the review decision is made.",
  },
  {
    label: "Evidence summary",
    meaning: "A compact list of trusted sources used to support a claim or warning.",
    next: "Prefer approved schema, policy, terminology, or source-document evidence over generic text.",
  },
  {
    label: "Low confidence",
    meaning: "The system did not have enough reliable signal to make the result dependable.",
    next: "Provide more context, reduce conflicting filters, or escalate to review.",
  },
];

const roleGuides = [
  {
    role: "Operations user",
    goal: "Validate healthcare data and move work through review gates.",
    start: "Assistant for natural language tasks, Workbench for explicit upload workflows.",
  },
  {
    role: "Data steward",
    goal: "Check schema fit, missing fields, PHI warnings, and output quality.",
    start: "Schemas, Workflows, and Reviews.",
  },
  {
    role: "Evidence reviewer",
    goal: "Verify that issues and explanations are grounded in approved sources.",
    start: "Retrieval and workflow evidence panels.",
  },
  {
    role: "Administrator",
    goal: "Confirm runtime settings, storage backend, upload limits, and extraction capabilities.",
    start: "Settings and system badges in the top bar.",
  },
];

const inputFormatGuide = [
  {
    format: "CSV",
    use: "Best for tables such as lab results, measurements, and exported operational data.",
    caution: "Malformed rows, missing cells, extra cells, missing units, and PHI columns should trigger review.",
  },
  {
    format: "JSON / YAML",
    use: "Best for structured records, configuration-like payloads, and FHIR-like resources.",
    caution: "Nested objects can become lossy when converted to flat CSV.",
  },
  {
    format: "FHIR-like JSON",
    use: "Best when the payload contains resourceType, Bundle.entry, or healthcare resource profiles.",
    caution: "This app profiles FHIR-like shape; it is not a full HL7 FHIR validator yet.",
  },
  {
    format: "PDF / DOCX / Image",
    use: "Best for uploaded documents that need text extraction before validation.",
    caution: "Scanned, image-heavy, encrypted, or low-quality files may need OCR fallback and human review.",
  },
];

const issueGuide = [
  {
    issue: "Missing field",
    meaning: "A required schema field is absent or blank.",
    action: "Confirm whether the source data omitted it or whether the wrong schema was selected.",
  },
  {
    issue: "Missing unit",
    meaning: "A measurement has a value but no unit, making interpretation unsafe.",
    action: "Add a source-backed unit or send the run to review.",
  },
  {
    issue: "Possible PHI",
    meaning: "The data includes patient identifiers, diagnosis text, SSN-like values, or sensitive context.",
    action: "Keep review gates enabled and avoid external sharing.",
  },
  {
    issue: "Weak evidence",
    meaning: "Retrieval did not find enough trusted support or required evidence buckets.",
    action: "Broaden filters, check source scope, or ask for clarification.",
  },
  {
    issue: "Prompt-injection pattern",
    meaning: "Input text contains instructions that may try to control the assistant or tool behavior.",
    action: "Treat the source text as untrusted data and require review.",
  },
];

const retrievalManual = [
  {
    title: "Search plan",
    meaning:
      "Shows the backend route, query aspects, rewrites, medical search hints, and suggested filters that shaped the latest search.",
    action: "Read this before individual hits when you need to understand what the system actually searched for.",
  },
  {
    title: "Execution summary",
    meaning:
      "Separates local OJTFlow searches from external medical follow-ups so you can see what can run now and what must be copied or opened manually.",
    action:
      "Use Run first local task for the first trusted-corpus step, then Copy external follow-ups when you need to check FHIR, LOINC, UCUM, PubMed, or other external indexes.",
  },
  {
    title: "Hybrid search",
    meaning:
      "Combines keyword search with vector similarity. Use it when field names, standards, and clinical wording may not match exactly.",
    action: "Check the hybrid stack and reranker state before judging why a result ranked first.",
  },
  {
    title: "Reranking",
    meaning:
      "A second-stage sorter that can reorder candidate evidence after the first search pass.",
    action: "If reranking is off or unavailable, inspect score explanations more carefully.",
  },
  {
    title: "Evidence readiness",
    meaning:
      "The readiness panel translates backend quality signals into ready, review, blocked, or unscored states.",
    action: "Do not use blocked evidence downstream. Review warnings and missing buckets first.",
  },
  {
    title: "Exact source scope",
    meaning:
      "Restricts retrieval to one trusted source ID. This is useful for audit, but it can hide broader evidence.",
    action: "Clear exact source scope before deciding the full corpus lacks evidence.",
  },
  {
    title: "Query rewrites",
    meaning:
      "Backend-generated variants used to improve recall. They do not change the submitted query payload.",
    action: "Use rewrites to understand what the search tried, not as final clinical wording.",
  },
  {
    title: "Exported JSON reports",
    meaning:
      "Copy buttons export audit data for cockpit summaries, evidence hits, comparisons, and judgment evaluations.",
    action: "Use these reports for offline review, tuning notes, and reproducible evidence discussions.",
  },
];

export function HelpPage({ mode = "overview" }: { mode?: HelpMode }) {
  const pageTitle =
    mode === "tutorials"
      ? "Tutorials"
      : mode === "manual"
        ? "User Manual"
        : "Help Center";
  const pageDescription =
    mode === "tutorials"
      ? "Step-by-step guides for common healthcare data tasks."
      : mode === "manual"
        ? "Plain-language reference for outputs, evidence, warnings, and review decisions."
        : "Plain-language guide for using OJTFlow, reading results, and deciding the next action.";
  const showOverview = mode === "overview";
  const showTutorials = mode === "overview" || mode === "tutorials";
  const showManual = mode === "overview" || mode === "manual";

  return (
    <div className="grid gap-5">
      <PageHeader
        title={pageTitle}
        description={pageDescription}
        action={
          <div className="flex flex-wrap gap-2">
            <Button asChild type="button" variant="outline">
              <Link to="/assistant">
                <Bot className="h-4 w-4" />
                Assistant
              </Link>
            </Button>
            <Button asChild type="button" variant="outline">
              <Link to="/retrieval">
                <Search className="h-4 w-4" />
                Retrieval
              </Link>
            </Button>
          </div>
        }
      />

      <HelpModeNav activeMode={mode} />

      {showOverview ? (
        <>
          <Card>
            <CardHeader>
              <CardTitle>What Should I Do?</CardTitle>
              <CardDescription>Choose the path based on the situation in front of you.</CardDescription>
            </CardHeader>
            <CardContent className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
              {decisionGuide.map((item) => (
                <DecisionGuideCard
                  action={item.action}
                  destination={item.destination}
                  key={item.situation}
                  situation={item.situation}
                  to={item.to}
                />
              ))}
            </CardContent>
          </Card>

          <section className="grid gap-3 lg:grid-cols-4">
            <HelpRouteCard
              icon={Layers}
              title="Workflows"
              to="/workflows"
              description="Use when you need to inspect current and historical runs, status, output, evidence, and audit events."
              bestFor="Queue, progress, output, audit"
            />
            <HelpRouteCard
              icon={Bot}
              title="Assistant"
              to="/assistant"
              description="Use when you want to ask in natural language, attach a file, and let the app call governed tools."
              bestFor="Questions, validation, evidence, review listing"
            />
            <HelpRouteCard
              icon={FileCode}
              title="Workbench"
              to="/workbench"
              description="Use when you want a governed upload-to-workflow path with explicit format and schema controls."
              bestFor="CSV, JSON, YAML, PDF/image intake"
            />
            <HelpRouteCard
              icon={Search}
              title="Retrieval"
              to="/retrieval"
              description="Use when you need to inspect trusted standards, policies, terminology, and source grounding."
              bestFor="Evidence search, filters, relevance review"
            />
            <HelpRouteCard
              icon={ClipboardCheck}
              title="Reviews"
              to="/reviews"
              description="Use when a workflow pauses before a risky, low-confidence, or meaning-changing action."
              bestFor="Approve, edit, reject, clarify"
            />
            <HelpRouteCard
              icon={Database}
              title="Schemas"
              to="/schemas"
              description="Use when you need to understand approved healthcare profiles and required fields."
              bestFor="Contracts, fields, source refs"
            />
          </section>
        </>
      ) : null}

      {showOverview ? <Card>
        <CardHeader>
          <CardTitle>Who Should Start Where</CardTitle>
          <CardDescription>Pick the path that matches the job you are doing.</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
          {roleGuides.map((guide) => (
            <div className="rounded-md border border-border bg-muted/20 p-3" key={guide.role}>
              <div className="font-black">{guide.role}</div>
              <p className="mt-1 text-sm leading-6 text-muted-foreground">{guide.goal}</p>
              <div className="mt-3 rounded-md border border-border bg-card px-3 py-2 text-sm font-semibold leading-6">
                Start with: {guide.start}
              </div>
            </div>
          ))}
        </CardContent>
      </Card> : null}

      {showOverview ? <section className="grid gap-3 xl:grid-cols-[0.85fr_1.15fr]">
        <Card>
          <CardHeader>
            <CardTitle>Quick Start</CardTitle>
            <CardDescription>Recommended path for a non-technical healthcare operator.</CardDescription>
          </CardHeader>
          <CardContent>
            <ol className="grid gap-3 text-sm leading-6">
              <GuideStep title="Start with Assistant">
                Ask what you want in plain language. Attach a file when the task depends on data.
              </GuideStep>
              <GuideStep title="Check the live timeline">
                Read model text, then expand tool calls only when you need details.
              </GuideStep>
              <GuideStep title="Trust evidence, not just prose">
                For medical data, check evidence sources, quality warnings, and limitations.
              </GuideStep>
              <GuideStep title="Use review gates">
                Do not force writes unless you understand the action. Review gates are intentional.
              </GuideStep>
            </ol>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>How To Read Output</CardTitle>
            <CardDescription>What the common panels mean.</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-2">
            <OutputMeaning label="LLM text" value="Readable explanation generated after backend tools run." />
            <OutputMeaning label="Tool call" value="A real backend operation, such as validation or retrieval." />
            <OutputMeaning label="Evidence readiness" value="Whether required support classes are present." />
            <OutputMeaning label="Strategy recommendations" value="Why the retrieval route was chosen and what filter may help." />
            <OutputMeaning label="Warnings" value="Possible PHI, missing units, weak evidence, policy gaps, or unsafe text." />
            <OutputMeaning label="Audit events" value="Append-only trace of what happened, when, and which module produced it." />
          </CardContent>
        </Card>
      </section> : null}

      {showTutorials ? (
        <Card>
          <CardHeader>
            <CardTitle>First Run Checklist</CardTitle>
            <CardDescription>Use this before trusting a real workflow run.</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-2 text-sm leading-6">
            {firstRunChecklist.map((item) => (
              <SafetyItem key={item}>{item}</SafetyItem>
            ))}
          </CardContent>
        </Card>
      ) : null}

      {showManual ? <Card>
        <CardHeader>
          <CardTitle>Input Format Guide</CardTitle>
          <CardDescription>What you can provide and what to check before trusting the result.</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
          {inputFormatGuide.map((item) => (
            <div className="grid gap-2 rounded-md border border-border bg-muted/20 p-3" key={item.format}>
              <div className="flex items-center gap-2">
                <FileText className="h-4 w-4 text-primary" />
                <span className="font-black">{item.format}</span>
              </div>
              <p className="text-sm leading-6 text-muted-foreground">{item.use}</p>
              <div className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-sm font-semibold leading-6 text-amber-950">
                Watch for: {item.caution}
              </div>
            </div>
          ))}
        </CardContent>
      </Card> : null}

      {showTutorials ? <section className="grid gap-3 lg:grid-cols-3">
        {tutorials.map((tutorial) => (
          <Card key={tutorial.title}>
            <CardHeader>
              <CardTitle>{tutorial.title}</CardTitle>
              <CardDescription>Step-by-step tutorial.</CardDescription>
            </CardHeader>
            <CardContent>
              <ol className="grid gap-2 text-sm leading-6">
                {tutorial.steps.map((step) => (
                  <li className="flex gap-2" key={step}>
                    <CheckCircle2 className="mt-1 h-4 w-4 shrink-0 text-emerald-600" />
                    <span>{step}</span>
                  </li>
                ))}
              </ol>
            </CardContent>
          </Card>
        ))}
      </section> : null}

      {showManual ? <Card>
        <CardHeader>
          <CardTitle>Status And Output Manual</CardTitle>
          <CardDescription>Translate result labels into next actions.</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
          {explanationGuide.map((item) => (
            <div className="grid gap-2 rounded-md border border-border bg-muted/20 p-3" key={item.label}>
              <div className="font-black">{item.label}</div>
              <p className="text-sm leading-6 text-muted-foreground">{item.meaning}</p>
              <div className="rounded-md border border-border bg-card px-3 py-2 text-sm font-semibold leading-6">
                Next: {item.next}
              </div>
            </div>
          ))}
        </CardContent>
      </Card> : null}

      {showManual ? <Card>
        <CardHeader>
          <CardTitle>Retrieval Search Manual</CardTitle>
          <CardDescription>How to interpret healthcare evidence search without needing retrieval expertise.</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {retrievalManual.map((item) => (
            <RetrievalManualItem
              action={item.action}
              key={item.title}
              meaning={item.meaning}
              title={item.title}
            />
          ))}
        </CardContent>
      </Card> : null}

      {showManual ? <Card>
        <CardHeader>
          <CardTitle>Manual And Glossary</CardTitle>
          <CardDescription>Terms used throughout the app.</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-2 md:grid-cols-2">
          {glossary.map((item) => (
            <div className="rounded-md border border-border bg-muted/20 p-3" key={item.term}>
              <div className="flex items-center gap-2">
                <HelpCircle className="h-4 w-4 text-primary" />
                <span className="font-black">{item.term}</span>
              </div>
              <p className="mt-1 text-sm leading-6 text-muted-foreground">{item.meaning}</p>
            </div>
          ))}
        </CardContent>
      </Card> : null}

      {showManual ? <Card>
        <CardHeader>
          <CardTitle>Issue And Warning Manual</CardTitle>
          <CardDescription>How to translate backend warnings into user actions.</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {issueGuide.map((item) => (
            <div className="grid gap-2 rounded-md border border-border bg-muted/20 p-3" key={item.issue}>
              <div className="font-black">{item.issue}</div>
              <p className="text-sm leading-6 text-muted-foreground">{item.meaning}</p>
              <div className="rounded-md border border-border bg-card px-3 py-2 text-sm font-semibold leading-6">
                Action: {item.action}
              </div>
            </div>
          ))}
        </CardContent>
      </Card> : null}

      {showManual ? <Card>
        <CardHeader>
          <CardTitle>Safety Rules</CardTitle>
          <CardDescription>How to avoid misuse.</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-2 text-sm leading-6">
          <SafetyItem>Do not treat OJTFlow as clinical decision support.</SafetyItem>
          <SafetyItem>Do not copy patient identifiers into external search engines.</SafetyItem>
          <SafetyItem>Use evidence and audit trails when making operational decisions.</SafetyItem>
          <SafetyItem>Escalate low-confidence, missing-evidence, or PHI-sensitive results for review.</SafetyItem>
        </CardContent>
      </Card> : null}
    </div>
  );
}

function HelpModeNav({ activeMode }: { activeMode: HelpMode }) {
  return (
    <div className="grid gap-3 rounded-md border border-border bg-muted/20 p-3 md:grid-cols-3">
      {helpModes.map((item) => (
        <Link
          className={
            activeMode === item.mode
              ? "rounded-md border border-primary/40 bg-primary/10 px-3 py-2 text-sm font-bold text-primary"
              : "rounded-md border border-border bg-card px-3 py-2 text-sm font-bold text-foreground hover:bg-muted/50"
          }
          key={item.mode}
          to={item.to}
        >
          <span className="block">{item.label}</span>
          <span className="mt-1 block text-xs font-semibold leading-5 text-muted-foreground">
            {item.description}
          </span>
        </Link>
      ))}
    </div>
  );
}

function DecisionGuideCard({
  action,
  destination,
  situation,
  to,
}: {
  action: string;
  destination: string;
  situation: string;
  to: "/assistant" | "/workbench" | "/reviews" | "/retrieval";
}) {
  return (
    <div className="grid gap-3 rounded-md border border-border bg-card p-3">
      <div>
        <div className="text-xs font-black uppercase text-muted-foreground">Situation</div>
        <div className="mt-1 font-black leading-6">{situation}</div>
      </div>
      <p className="text-sm leading-6 text-muted-foreground">{action}</p>
      <Button asChild size="sm" type="button" variant="outline">
        <Link to={to}>Open {destination}</Link>
      </Button>
    </div>
  );
}

function HelpRouteCard({
  bestFor,
  description,
  icon: Icon,
  title,
  to,
}: {
  bestFor: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  to: "/assistant" | "/workbench" | "/retrieval" | "/reviews" | "/workflows" | "/schemas";
}) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <Icon className="h-4 w-4 text-primary" />
          <CardTitle>{title}</CardTitle>
        </div>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent className="grid gap-3">
        <Badge variant="muted">{bestFor}</Badge>
        <Button asChild size="sm" type="button" variant="outline">
          <Link to={to}>Open {title}</Link>
        </Button>
      </CardContent>
    </Card>
  );
}

function GuideStep({ children, title }: { children: React.ReactNode; title: string }) {
  return (
    <li className="rounded-md border border-border bg-muted/20 p-3">
      <div className="font-black">{title}</div>
      <div className="mt-1 text-muted-foreground">{children}</div>
    </li>
  );
}

function OutputMeaning({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-start gap-2 rounded-md border border-border bg-muted/20 p-3 text-sm">
      <BookOpen className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
      <div>
        <div className="font-black">{label}</div>
        <div className="mt-1 text-muted-foreground">{value}</div>
      </div>
    </div>
  );
}

function RetrievalManualItem({
  action,
  meaning,
  title,
}: {
  action: string;
  meaning: string;
  title: string;
}) {
  return (
    <div className="grid gap-2 rounded-md border border-border bg-muted/20 p-3">
      <div className="flex items-center gap-2">
        <Search className="h-4 w-4 text-primary" />
        <span className="font-black">{title}</span>
      </div>
      <p className="text-sm leading-6 text-muted-foreground">{meaning}</p>
      <div className="rounded-md border border-border bg-card px-3 py-2 text-sm font-semibold leading-6">
        {action}
      </div>
    </div>
  );
}

function SafetyItem({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex items-start gap-2 rounded-md border border-border bg-muted/20 p-3">
      <ShieldCheck className="mt-1 h-4 w-4 shrink-0 text-emerald-600" />
      <span>{children}</span>
    </div>
  );
}
