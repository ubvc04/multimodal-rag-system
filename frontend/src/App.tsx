import { useEffect } from "react";
import { Navigate, Route, Routes } from "react-router-dom";

import { ErrorBoundary } from "./components/ErrorBoundary";
import { useAuth } from "./hooks/useAuth";
import DashboardPage from "./pages/DashboardPage";
import LoginPage from "./pages/LoginPage";
import QueryPage from "./pages/QueryPage";

const App = () => {
	const { user, loadProfile } = useAuth();

	useEffect(() => {
		loadProfile();
	}, [loadProfile]);

	return (
		<div className="min-h-screen bg-[radial-gradient(circle_at_top,_#f4f1ea,_#e6dfd3_45%,_#d6d0c6_100%)]">
			<div className="mx-auto max-w-6xl px-4 py-8">
				<header className="mb-8 flex items-center justify-between">
					<div>
						<p className="text-xs uppercase tracking-[0.25em] text-black/40">Multimodal RAG</p>
						<h1 className="font-display text-3xl">Atlas of Answers</h1>
					</div>
					<div className="rounded-full bg-white/80 px-4 py-2 text-xs font-semibold shadow-md">
						{user ? `Signed in as ${user.email}` : "Guest"}
					</div>
				</header>
				<ErrorBoundary>
					<Routes>
						<Route path="/login" element={<LoginPage />} />
						<Route path="/" element={user ? <DashboardPage /> : <Navigate to="/login" replace />} />
						<Route path="/query" element={user ? <QueryPage /> : <Navigate to="/login" replace />} />
					</Routes>
				</ErrorBoundary>
			</div>
		</div>
	);
};

export default App;
