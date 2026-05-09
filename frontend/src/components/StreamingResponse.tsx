import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import type { SourceChunk } from "../types";

interface StreamingResponseProps {
	tokens: string[];
	sources: SourceChunk[];
	isStreaming: boolean;
	latencyMs?: number;
}

const scoreBadge = (score: number) => {
	if (score >= 0.9) return "bg-moss text-white";
	if (score >= 0.7) return "bg-amber-400 text-black";
	return "bg-ember text-white";
};

const StreamingResponse = ({ tokens, sources, isStreaming, latencyMs }: StreamingResponseProps) => {
	const answer = tokens.join("");
	const tokenCount = tokens.length;

	return (
		<section className="rounded-3xl bg-white/90 p-6 shadow-xl">
			<div className="prose max-w-none prose-headings:font-display">
				<ReactMarkdown remarkPlugins={[remarkGfm]}>
					{answer || "Waiting for response..."}
				</ReactMarkdown>
			</div>
			{isStreaming && <span className="inline-block h-4 w-2 animate-pulseCursor bg-ink align-middle" />}

			<div className="mt-6 flex flex-wrap gap-4 text-xs text-black/60">
				<span>Tokens: {tokenCount}</span>
				{latencyMs !== undefined && <span>Latency: {latencyMs.toFixed(0)} ms</span>}
			</div>

			{sources.length > 0 && (
				<div className="mt-6 space-y-3">
					<h3 className="text-xs uppercase tracking-wide text-black/40">Sources</h3>
					{sources.map((source, index) => (
						<details key={`${source.metadata.doc_id}-${index}`} className="rounded-2xl border border-black/10 p-4">
							<summary className="flex cursor-pointer items-center justify-between text-sm font-semibold">
								<span>{source.metadata.source || "Unknown"}</span>
								<span className={`rounded-full px-2 py-1 text-xs ${scoreBadge(source.score)}`}>
									{source.score.toFixed(2)}
								</span>
							</summary>
							<div className="mt-3 text-xs text-black/70">
								<p>Page: {source.metadata.page ?? "N/A"}</p>
								<p className="mt-2 whitespace-pre-wrap">{source.text}</p>
							</div>
						</details>
					))}
				</div>
			)}
		</section>
	);
};

export default StreamingResponse;
