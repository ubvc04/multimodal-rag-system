import { Link } from "react-router-dom";

import DocumentUpload from "../components/DocumentUpload";
import DocumentList from "../components/DocumentList";
import { useAuth } from "../hooks/useAuth";

const DashboardPage = () => {
	const { logout } = useAuth();

	return (
		<div className="space-y-6">
			<div className="flex flex-wrap items-center justify-between gap-4 rounded-3xl bg-white/90 p-6 shadow-xl">
				<div>
					<h2 className="font-display text-2xl">Research cockpit</h2>
					<p className="text-sm text-black/60">Upload files and jump into question mode.</p>
				</div>
				<div className="flex items-center gap-3">
					<Link to="/query" className="rounded-full bg-ink px-4 py-2 text-xs font-semibold text-white">
						Go to query
					</Link>
					<button onClick={() => logout()} className="rounded-full border border-black/10 px-4 py-2 text-xs">
						Sign out
					</button>
				</div>
			</div>
			<div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
				<DocumentUpload />
				<DocumentList />
			</div>
		</div>
	);
};

export default DashboardPage;
