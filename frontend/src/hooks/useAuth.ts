import { create } from "zustand";

import { api } from "../lib/api";
import { authStore } from "../lib/auth";
import type { TokenResponse, User } from "../types";

interface AuthState {
	user: User | null;
	loading: boolean;
	error: string | null;
	login: (email: string, password: string) => Promise<void>;
	register: (email: string, password: string, fullName: string) => Promise<void>;
	logout: () => Promise<void>;
	loadProfile: () => Promise<void>;
}

export const useAuth = create<AuthState>((set) => ({
	user: null,
	loading: false,
	error: null,
	async login(email: string, password: string) {
		set({ loading: true, error: null });
		try {
			const token: TokenResponse = await api.login(email, password);
			authStore.setAccessToken(token.access_token);
			const profile = await api.getMe();
			set({ user: profile, loading: false });
		} catch (err) {
			set({ loading: false, error: "Login failed" });
			throw err;
		}
	},
	async register(email: string, password: string, fullName: string) {
		set({ loading: true, error: null });
		try {
			const token = await api.register(email, password, fullName);
			authStore.setAccessToken(token.access_token);
			const profile = await api.getMe();
			set({ user: profile, loading: false });
		} catch (err) {
			set({ loading: false, error: "Registration failed" });
			throw err;
		}
	},
	async logout() {
		set({ loading: true });
		await api.logout();
		set({ user: null, loading: false });
	},
	async loadProfile() {
		set({ loading: true, error: null });
		try {
			const profile = await api.getMe();
			set({ user: profile, loading: false });
		} catch {
			set({ user: null, loading: false });
		}
	},
}));
