"""Agent service for tool-augmented reasoning."""

from __future__ import annotations

import ast
from collections.abc import AsyncGenerator
from dataclasses import dataclass

import asyncpg
from langchain import hub
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.chains.summarize import load_summarize_chain
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_experimental.tools import PythonREPLTool

from app.config import settings
from app.services.rag_pipeline import RAGPipeline
from app.services.streaming import sse_event


@dataclass(frozen=True)
class AgentStepResult:
	"""Agent tool step result."""

	tool: str
	input: str
	output: str


@dataclass(frozen=True)
class AgentRunResult:
	"""Agent execution result."""

	output: str
	steps: list[AgentStepResult]
	total_steps: int
	session_id: str


class AgentService:
	"""Agentic reasoning with tools."""

	def __init__(self, rag_pipeline: RAGPipeline) -> None:
		self.rag_pipeline = rag_pipeline
		self.llm = ChatOpenAI(model=settings.OPENAI_CHAT_MODEL, temperature=0, streaming=True)
		self.tools = self._build_tools()
		self.agent = self._build_agent()

	def _build_tools(self) -> list:
		@tool("document_search")
		async def document_search(question: str) -> str:
			"""Search the document knowledge base for information."""
			result = await self.rag_pipeline.query(question)
			sources = result.sources
			citation_lines = [
				f"- {source.metadata.get('source')}, Page {source.metadata.get('page')}" for source in sources
			]
			citations = "\n".join(citation_lines) if citation_lines else "- No sources"
			return f"Answer:\n{result.answer}\n\nSources:\n{citations}"

		@tool("web_search")
		async def web_search(query: str) -> str:
			"""Search the internet for current information."""
			search = DuckDuckGoSearchRun()
			return search.run(query)

		@tool("sql_query")
		async def sql_query(query: str) -> str:
			"""Execute a read-only SQL SELECT query."""
			if not query.strip().lower().startswith("select"):
				return "Only SELECT statements are allowed."

			dsn = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
			conn = await asyncpg.connect(dsn)
			try:
				rows = await conn.fetch(query)
			finally:
				await conn.close()

			if not rows:
				return "No rows returned."

			columns = rows[0].keys()
			header = "| " + " | ".join(columns) + " |"
			divider = "| " + " | ".join(["---" for _ in columns]) + " |"
			body = []
			for row in rows[:100]:
				body.append("| " + " | ".join([str(row[col]) for col in columns]) + " |")
			return "\n".join([header, divider, *body])

		@tool("python_executor")
		async def python_executor(code: str) -> str:
			"""Execute Python code for analysis in a restricted environment."""
			_validate_python_code(code)
			repl = PythonREPLTool()
			output = repl.run(code)
			return str(output)

		@tool("document_summarizer")
		async def document_summarizer(doc_ids: str) -> str:
			"""Summarize documents by doc_id list.

			Args:
				doc_ids: Comma-separated document IDs.
			"""
			ids = [doc_id.strip() for doc_id in doc_ids.split(",") if doc_id.strip()]
			if not ids:
				return "No document IDs provided."

			query = f"Summarize the following documents: {', '.join(ids)}"
			results = await self.rag_pipeline.query(query, doc_ids=ids)
			docs = [Document(page_content=results.answer, metadata={"doc_id": ",".join(ids)})]
			prompt = PromptTemplate(
				template=(
					"Write a structured summary with key points, entities, and conclusions.\n\n{context}"
				),
				input_variables=["context"],
			)
			chain = load_summarize_chain(self.llm, chain_type="map_reduce", combine_prompt=prompt)
			summary = await chain.arun(docs)
			return summary

		return [document_search, web_search, sql_query, python_executor, document_summarizer]

	def _build_agent(self) -> AgentExecutor:
		prompt = hub.pull("hwchase17/openai-functions-agent")
		agent = create_openai_functions_agent(llm=self.llm, tools=self.tools, prompt=prompt)
		return AgentExecutor(
			agent=agent,
			tools=self.tools,
			max_iterations=settings.AGENT_MAX_ITERATIONS,
			handle_parsing_errors=True,
			return_intermediate_steps=True,
			verbose=True,
		)

	async def run(self, query: str, session_id: str) -> AgentRunResult:
		"""Execute the agent and return its output and steps."""
		result = await self.agent.ainvoke({"input": query})
		steps: list[AgentStepResult] = []
		for item in result.get("intermediate_steps", []):
			tool, output = item
			steps.append(AgentStepResult(tool=tool.tool, input=str(tool.tool_input), output=str(output)))
		return AgentRunResult(
			output=str(result.get("output", "")),
			steps=steps,
			total_steps=len(steps),
			session_id=session_id,
		)

	async def stream_run(self, query: str, session_id: str) -> AsyncGenerator[str, None]:
		"""Stream agent execution as SSE events."""
		try:
			async for event in self.agent.astream_events({"input": query}, version="v1"):
				event_type = event.get("event")
				if event_type == "on_chain_start":
					yield sse_event({"type": "agent_start", "data": query})
				elif event_type == "on_tool_start":
					tool_name = event.get("name", "")
					tool_input = event.get("data", {}).get("input", "")
					yield sse_event({"type": "tool_start", "data": {"tool": tool_name, "input": str(tool_input)}})
				elif event_type == "on_tool_end":
					tool_name = event.get("name", "")
					output = event.get("data", {}).get("output", "")
					yield sse_event({"type": "tool_end", "data": {"tool": tool_name, "output": str(output)}})
				elif event_type == "on_chat_model_stream":
					token = event.get("data", {}).get("chunk", "")
					token_text = getattr(token, "content", "") if token else ""
					if token_text:
						yield sse_event({"type": "token", "data": token_text})
				elif event_type == "on_chain_end":
					output = event.get("data", {}).get("output", {})
					if isinstance(output, dict) and "output" in output:
						yield sse_event({"type": "done", "data": output.get("output", "")})
			yield sse_event({"type": "done", "data": ""})
		except Exception as exc:
			yield sse_event({"type": "error", "data": str(exc)})


def _validate_python_code(code: str) -> None:
	tree = ast.parse(code)
	for node in ast.walk(tree):
		if isinstance(node, (ast.Import, ast.ImportFrom)):
			for alias in node.names:
				if alias.name.split(".")[0] in {"os", "sys", "subprocess", "socket", "shutil"}:
					raise ValueError("Unsafe import detected")
