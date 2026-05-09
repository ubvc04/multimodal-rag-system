import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { useAuth } from "../hooks/useAuth";

const AuthForms = () => {
	const [mode, setMode] = useState<"login" | "register">("login");
	const [email, setEmail] = useState("");
	const [password, setPassword] = useState("");
	const [fullName, setFullName] = useState("");
	const [error, setError] = useState<string | null>(null);
	const { login, register, loading } = useAuth();
	const navigate = useNavigate();

	const submit = async (event: React.FormEvent) => {
		event.preventDefault();
		setError(null);
		try {
			if (mode === "login") {
				await login(email, password);
			} else {
				await register(email, password, fullName);
			}
			navigate("/");
		} catch {
			setError("Authentication failed. Please try again.");
		}
	};

	return (
		<div className="w-full max-w-md rounded-3xl bg-white/90 p-8 shadow-2xl">
			<h2 className="font-display text-2xl">{mode === "login" ? "Welcome back" : "Create your account"}</h2>
			<p className="mt-2 text-sm text-black/60">
				{mode === "login" ? "Continue where your research left off." : "Start curating your knowledge base."}
			</p>
			<form className="mt-6 space-y-4" onSubmit={submit}>
				{mode === "register" && (
					<div>
						<label className="text-xs uppercase tracking-wide text-black/50">Full name</label>
						<input
							value={fullName}
							onChange={(event) => setFullName(event.target.value)}
							className="mt-2 w-full rounded-xl border border-black/10 px-4 py-3 text-sm"
							placeholder="Avery Rivera"
							required
						/>
					</div>
				)}
				<div>
					<label className="text-xs uppercase tracking-wide text-black/50">Email</label>
					<input
						type="email"
						value={email}
						onChange={(event) => setEmail(event.target.value)}
						className="mt-2 w-full rounded-xl border border-black/10 px-4 py-3 text-sm"
						placeholder="you@studio.com"
						required
					/>
				</div>
				<div>
					<label className="text-xs uppercase tracking-wide text-black/50">Password</label>
					<input
						type="password"
						value={password}
						onChange={(event) => setPassword(event.target.value)}
						className="mt-2 w-full rounded-xl border border-black/10 px-4 py-3 text-sm"
						placeholder="Minimum 8 characters"
						minLength={8}
						required
					/>
				</div>
				{error && <p className="text-sm text-ember">{error}</p>}
				<button
					type="submit"
					disabled={loading}
					className="w-full rounded-xl bg-ink px-4 py-3 text-sm font-semibold text-white transition hover:opacity-90"
				>
					{loading ? "Working..." : mode === "login" ? "Sign in" : "Create account"}
				</button>
			</form>
			<button
				className="mt-4 w-full text-sm text-black/60"
				onClick={() => setMode(mode === "login" ? "register" : "login")}
			>
				{mode === "login" ? "Need an account? Create one." : "Already have an account? Sign in."}
			</button>
		</div>
	);
};

export default AuthForms;
