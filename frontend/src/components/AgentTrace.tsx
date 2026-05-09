import type { AgentStep } from "../types";

interface AgentTraceProps {
	steps: AgentStep[];
}

const toolStyle = (tool: string) => {
	switch (tool) {
		case "document_search":
			return { label: "🔍", color: "bg-blue-500" };
		case "web_search":
			return { label: "🌐", color: "bg-green-500" };
		case "sql_query":
			return { label: "💾", color: "bg-amber-500" };
		case "python_executor":
			return { label: "🐍", color: "bg-purple-500" };
		default:
			return { label: "⚙️", color: "bg-black" };
	}
};

const AgentTrace = ({ steps }: AgentTraceProps) => {
	return (
		<section className="rounded-3xl bg-white/90 p-6 shadow-xl">
			<h2 className="font-display text-xl">Agent trace</h2>
			<p className="text-sm text-black/60">Reasoning steps appear as tools execute.</p>
			<div className="mt-4 space-y-3">
				{steps.map((step, index) => {
					const style = toolStyle(step.tool);
					return (
						<details key={`${step.tool}-${index}`} className="rounded-2xl border border-black/10 p-4">
							<summary className="flex cursor-pointer items-center gap-3 text-sm font-semibold">
								<span className={`flex h-8 w-8 items-center justify-center rounded-full ${style.color} text-white`}>
									{style.label}
								</span>
								<span>{step.tool}</span>
							</summary>
							<div className="mt-3 text-xs text-black/70">
								<p className="font-semibold">Input</p>
								<pre className="mt-2 whitespace-pre-wrap rounded-xl bg-black/5 p-3">{step.input}</pre>
								<p className="mt-3 font-semibold">Output</p>
								<pre className="mt-2 whitespace-pre-wrap rounded-xl bg-black/5 p-3">{step.output}</pre>
							</div>
						</details>
					);
				})}
				{steps.length === 0 && <p className="text-sm text-black/50">No steps yet.</p>}
			</div>
		</section>
	);
};

export default AgentTrace;
