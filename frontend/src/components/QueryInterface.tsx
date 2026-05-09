import { useMemo, useState } from "react";

import { authStore } from "../lib/auth";
import { useDocuments } from "../hooks/useDocuments";
import { useSSE } from "../hooks/useSSE";
import StreamingResponse from "./StreamingResponse";
import AgentTrace from "./AgentTrace";

const QueryInterface = () => {
	const { documents } = useDocuments();
	const [mode, setMode] = useState<"rag" | "agent">("rag");
	const [question, setQuestion] = useState("");
	const [requestUrl, setRequestUrl] = useState("");
	const [enabled, setEnabled] = useState(false);
	const [selectedDocIds, setSelectedDocIds] = useState<string[]>([]);

	const token = authStore.getAccessToken() ?? "";
	const stream = useSSE({ url: requestUrl, token, enabled });

	const toggleDoc = (docId: string) => {
		setSelectedDocIds((prev) => (prev.includes(docId) ? prev.filter((id) => id !== docId) : [...prev, docId]));
	};

	const submit = () => {
		if (!question.trim()) return;
		stream.reset();
		const base = import.meta.env.VITE_API_BASE_URL as string;
		if (mode === "rag") {
			const docParam = selectedDocIds.length ? `&doc_ids=${selectedDocIds.join(",")}` : "";
			setRequestUrl(`${base}/api/v1/query/stream?question=${encodeURIComponent(question)}${docParam}`);
		} else {
			setRequestUrl(`${base}/api/v1/agent/stream?query=${encodeURIComponent(question)}`);
		}
		setEnabled(true);
	};

	const selectedCount = selectedDocIds.length;

	return (
		<div className="grid gap-6 lg:grid-cols-[280px_1fr]">
			<aside className="rounded-3xl bg-white/90 p-6 shadow-xl">
				<h2 className="font-display text-lg">Documents</h2>
				<p className="text-xs text-black/50">Select which sources to query.</p>
				<div className="mt-4 space-y-2">
					{documents.map((doc) => (
						<label key={doc.id} className="flex items-center gap-3 rounded-xl border border-black/10 px-3 py-2">
							<input
								type="checkbox"
								checked={selectedDocIds.includes(doc.id)}
								onChange={() => toggleDoc(doc.id)}
							/>
							<span className="text-xs">{doc.original_filename}</span>
						</label>
					))}
					{documents.length === 0 && <p className="text-sm text-black/50">No documents available.</p>}
				</div>
			</aside>

			<section className="space-y-6">
				<div className="rounded-3xl bg-white/90 p-6 shadow-xl">
					<div className="flex flex-wrap items-center justify-between gap-4">
						<div>
							<h2 className="font-display text-xl">Ask the archive</h2>
							<p className="text-sm text-black/60">
								{mode === "rag" ? "Semantic Search" : "Agentic Reasoning"}
							</p>
						</div>
						<button
							onClick={() => setMode(mode === "rag" ? "agent" : "rag")}
							className="rounded-full border border-black/10 px-4 py-2 text-xs"
						>
							{mode === "rag" ? "Switch to Agent" : "Switch to RAG"}
						</button>
					</div>
					<textarea
						value={question}
						onChange={(event) => setQuestion(event.target.value)}
						onKeyDown={(event) => {
							if (event.key === "Enter" && event.ctrlKey) {
								submit();
							}
						}}
						className="mt-4 min-h-[120px] w-full rounded-2xl border border-black/10 p-4 text-sm"
						placeholder="Ask about patterns, figures, or anomalies..."
					/>
					<div className="mt-4 flex items-center justify-between text-xs text-black/50">
						<span>{selectedCount} documents selected</span>
						<button className="rounded-full bg-ink px-4 py-2 text-white" onClick={submit}>
							Run query
						</button>
					</div>
				</div>

				{mode === "rag" ? (
					<StreamingResponse tokens={stream.tokens} sources={stream.sources} isStreaming={stream.isStreaming} />
				) : (
					<AgentTrace steps={stream.steps} />
				)}
			</section>
		</div>
	);
};

export default QueryInterface;
