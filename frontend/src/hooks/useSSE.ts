import { useEffect, useRef, useState } from "react";
import { createParser, type ParsedEvent, type ReconnectInterval } from "eventsource-parser";

import type { AgentStep, SourceChunk } from "../types";

interface UseSSEOptions {
	url: string;
	token: string;
	enabled: boolean;
}

export const useSSE = ({ url, token, enabled }: UseSSEOptions) => {
	const [tokens, setTokens] = useState<string[]>([]);
	const [sources, setSources] = useState<SourceChunk[]>([]);
	const [steps, setSteps] = useState<AgentStep[]>([]);
	const [isStreaming, setIsStreaming] = useState(false);
	const [error, setError] = useState<string | null>(null);
	const controllerRef = useRef<AbortController | null>(null);
	const lastToolInputRef = useRef<Record<string, string>>({});

	const reset = () => {
		setTokens([]);
		setSources([]);
		setSteps([]);
		setError(null);
	};

	useEffect(() => {
		if (!enabled || !token || !url) {
			return;
		}

		const controller = new AbortController();
		controllerRef.current = controller;
		setIsStreaming(true);
		setError(null);

		const parser = createParser((event: ParsedEvent | ReconnectInterval) => {
			if (event.type !== "event") {
				return;
			}
			try {
				const payload = JSON.parse(event.data) as { type: string; data: unknown };
				if (payload.type === "token") {
					setTokens((prev) => [...prev, String(payload.data)]);
				} else if (payload.type === "sources") {
					setSources(payload.data as SourceChunk[]);
				} else if (payload.type === "tool_start") {
					const data = payload.data as { tool: string; input: string };
					lastToolInputRef.current[data.tool] = String(data.input ?? "");
				} else if (payload.type === "tool_end") {
					const data = payload.data as { tool: string; output: string; input?: string };
					const toolInput = data.input ?? lastToolInputRef.current[data.tool] ?? "";
					  setSteps((prev) => [...prev, { tool: data.tool, input: String(toolInput), output: String(data.output) }]);
				} else if (payload.type === "done") {
					setIsStreaming(false);
				} else if (payload.type === "error") {
					setError(String(payload.data));
					setIsStreaming(false);
				}
			} catch (err) {
				setError("Failed to parse stream");
			}
		});

		const stream = async () => {
			try {
				const response = await fetch(`${url}${url.includes("?") ? "&" : "?"}token=${token}`, {
					signal: controller.signal,
					headers: { Accept: "text/event-stream" },
				});
				if (!response.body) {
					throw new Error("Streaming unsupported");
				}
				const reader = response.body.getReader();
				const decoder = new TextDecoder();
				while (true) {
					const { value, done } = await reader.read();
					if (done) {
						break;
					}
					parser.feed(decoder.decode(value, { stream: true }));
				}
				setIsStreaming(false);
			} catch (err) {
				if (!controller.signal.aborted) {
					setError("Stream failed");
					setIsStreaming(false);
				}
			}
		};

		stream();

		return () => {
			controller.abort();
			setIsStreaming(false);
		};
	}, [enabled, token, url]);

	return {
		tokens,
		sources,
		steps,
		isStreaming,
		error,
		reset,
	};
};
