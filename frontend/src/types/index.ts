export interface User {
	id: string;
	email: string;
	full_name: string;
	is_active: boolean;
	created_at: string;
}

export interface TokenResponse {
	access_token: string;
	token_type: string;
	expires_in: number;
	refresh_token?: string;
}

export interface Document {
	id: string;
	filename: string;
	original_filename: string;
	file_type: string;
	file_size_bytes: number;
	status: "pending" | "processing" | "indexed" | "failed";
	pinecone_namespace: string;
	chunk_count: number;
	error_message?: string | null;
	created_at: string;
	updated_at: string;
}

export interface DocumentListResponse {
	items: Document[];
	total: number;
	skip: number;
	limit: number;
}

export interface SourceMetadata {
	doc_id: string;
	source: string;
	page?: number | null;
	file_type?: string;
	chunk_index: number;
}

export interface SourceChunk {
	text: string;
	score: number;
	metadata: SourceMetadata;
}

export interface QueryResponse {
	answer: string;
	sources: SourceChunk[];
	latency_ms: number;
}

export interface AgentStep {
	tool: string;
	input: string;
	output: string;
}

export interface AgentResponse {
	output: string;
	steps: AgentStep[];
	total_steps: number;
	session_id: string;
}

export interface StreamEvent<T> {
	type: string;
	data: T;
}
