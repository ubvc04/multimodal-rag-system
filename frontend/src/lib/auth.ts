const ACCESS_TOKEN_KEY = "rag_access_token";

export const authStore = {
	getAccessToken(): string | null {
		return localStorage.getItem(ACCESS_TOKEN_KEY);
	},
	setAccessToken(token: string): void {
		localStorage.setItem(ACCESS_TOKEN_KEY, token);
	},
	clear(): void {
		localStorage.removeItem(ACCESS_TOKEN_KEY);
	},
};
