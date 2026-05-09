import axios, { AxiosError, AxiosInstance, AxiosRequestConfig } from "axios";

import { authStore } from "./auth";
import type {
	AgentResponse,
	Document,
	DocumentListResponse,
	QueryResponse,
	TokenResponse,
	User,
} from "../types";

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL as string;

const client: AxiosInstance = axios.create({
	baseURL: apiBaseUrl,
	withCredentials: true,
});

client.interceptors.request.use((config) => {
	const token = authStore.getAccessToken();
	if (token) {
		config.headers.Authorization = `Bearer ${token}`;
	}
	return config;
});

let isRefreshing = false;
let pendingQueue: Array<(token: string | null) => void> = [];

const flushQueue = (token: string | null) => {
	pendingQueue.forEach((callback) => callback(token));
	pendingQueue = [];
};

client.interceptors.response.use(
	(response) => response,
	async (error: AxiosError) => {
		const original = error.config as AxiosRequestConfig & { _retry?: boolean };
		if (error.response?.status === 401 && !original._retry) {
			original._retry = true;

			if (isRefreshing) {
				return new Promise((resolve, reject) => {
					pendingQueue.push((token) => {
						if (!token) {
							reject(error);
							return;
						}
						original.headers = { ...original.headers, Authorization: `Bearer ${token}` };
						resolve(client(original));
					});
				});
			}

			isRefreshing = true;
			try {
				const refresh = await client.post<TokenResponse>("/api/v1/auth/refresh");
				authStore.setAccessToken(refresh.data.access_token);
				flushQueue(refresh.data.access_token);
				original.headers = { ...original.headers, Authorization: `Bearer ${refresh.data.access_token}` };
				return client(original);
			} catch (refreshError) {
				authStore.clear();
				flushQueue(null);
				window.location.href = "/login";
				return Promise.reject(refreshError);
			} finally {
				isRefreshing = false;
			}
		}
		return Promise.reject(error);
	},
);

export const api = {
	async register(email: string, password: string, fullName: string): Promise<TokenResponse> {
		const response = await client.post<TokenResponse>("/api/v1/auth/register", {
			email,
			password,
			full_name: fullName,
		});
		return response.data;
	},
	async login(email: string, password: string): Promise<TokenResponse> {
		const params = new URLSearchParams();
		params.append("username", email);
		params.append("password", password);
		const response = await client.post<TokenResponse>("/api/v1/auth/login", params, {
			headers: { "Content-Type": "application/x-www-form-urlencoded" },
		});
		return response.data;
	},
	async logout(): Promise<void> {
		await client.post("/api/v1/auth/logout");
		authStore.clear();
	},
	async getMe(): Promise<User> {
		const response = await client.get<User>("/api/v1/auth/me");
		return response.data;
	},
	async listDocuments(params: { skip?: number; limit?: number; status?: string; fileType?: string }): Promise<DocumentListResponse> {
		const response = await client.get<DocumentListResponse>("/api/v1/documents", {
			params: {
				skip: params.skip ?? 0,
				limit: params.limit ?? 20,
				status_filter: params.status,
				file_type: params.fileType,
			},
		});
		return response.data;
	},
	async uploadDocuments(
		files: File[],
		onUploadProgress?: (percent: number) => void,
	): Promise<Document[]> {
		const form = new FormData();
		files.forEach((file) => form.append("files", file));
		const response = await client.post<Document[]>("/api/v1/documents/upload", form, {
			headers: { "Content-Type": "multipart/form-data" },
			onUploadProgress: (event) => {
				if (!onUploadProgress || !event.total) {
					return;
				}
				const percent = Math.round((event.loaded / event.total) * 100);
				onUploadProgress(percent);
			},
		});
		return response.data;
	},
	async deleteDocument(docId: string): Promise<void> {
		await client.delete(`/api/v1/documents/${docId}`);
	},
	async query(question: string, docIds: string[] | null): Promise<QueryResponse> {
		const response = await client.post<QueryResponse>("/api/v1/query", {
			question,
			doc_ids: docIds,
			stream: false,
		});
		return response.data;
	},
	async runAgent(query: string, sessionId?: string): Promise<AgentResponse> {
		const response = await client.post<AgentResponse>("/api/v1/agent/run", {
			query,
			session_id: sessionId ?? null,
		});
		return response.data;
	},
};

export default client;
