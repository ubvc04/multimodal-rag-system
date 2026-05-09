import AuthForms from "../components/AuthForms";

const LoginPage = () => {
	return (
		<div className="grid place-items-center">
			<div className="grid gap-6 md:grid-cols-[1.2fr_1fr]">
				<div className="rounded-3xl bg-ink p-10 text-white shadow-2xl">
					<p className="text-xs uppercase tracking-[0.25em] text-white/50">Multimodal RAG</p>
					<h2 className="mt-4 font-display text-3xl">Build a living archive</h2>
					<p className="mt-3 text-sm text-white/70">
						Ingest text, tables, and images. Ask complex questions and watch the agent reason in real time.
					</p>
					<div className="mt-6 space-y-2 text-sm text-white/70">
						<p>• Hybrid vector search with citations</p>
						<p>• Agentic reasoning with tool trace</p>
						<p>• Live streaming answers</p>
					</div>
				</div>
				<AuthForms />
			</div>
		</div>
	);
};

export default LoginPage;
