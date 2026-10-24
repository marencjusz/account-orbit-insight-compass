import { signalLabel, signalTone } from "@/lib/format";

const tones = {
  risk: "bg-risk-soft text-risk",
  warn: "bg-warn-soft text-warn",
  good: "bg-good-soft text-good",
  neutral: "bg-muted text-muted-foreground",
};

export function SignalBadge({ signal }: { signal?: string | null }) {
  return (
    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${tones[signalTone(signal)]}`}>
      {signalLabel(signal)}
    </span>
  );
}
