import { Link } from "react-router-dom";

import QueryInterface from "../components/QueryInterface";

const QueryPage = () => {
	return (
		<div className="space-y-6">
			<div className="flex items-center justify-between rounded-3xl bg-white/90 p-6 shadow-xl">
				<div>
					<h2 className="font-display text-2xl">Question theatre</h2>
					<p className="text-sm text-black/60">Stream responses with citations and tool traces.</p>
				</div>
				<Link to="/" className="rounded-full border border-black/10 px-4 py-2 text-xs">
					Back to dashboard
				</Link>
			</div>
			<QueryInterface />
		</div>
	);
};

export default QueryPage;
