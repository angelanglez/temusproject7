"""
Research Assistant Script

This script provides a complete research pipeline using LLMs and search tools.
It creates structured research reports by planning an outline, gathering evidence,
and producing a well-cited final document.
"""

import argparse
import time

import tiktoken
from dotenv import load_dotenv
from langchain.prompts import ChatPromptTemplate
from langchain_community.retrievers import TavilySearchAPIRetriever
from langchain_groq import ChatGroq

load_dotenv()


# ---------- Configuration & Prompts ----------
class Config:
    """
    Configuration parameters for the research pipeline.
    """

    # Model settings
    GROQ_MODEL = "llama3-70b-8192"
    TOKEN_BUDGET = 12_000  # tokens-per-minute for free tier and note the underscores

    # Token allocations
    PLANNER_TOK = 512  # outline size
    WRITER_TOK = 1_024  # each section draft and note the underscores

    # Prompts
    PLANNER_PROMPT = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a meticulous research planner. "
                "Create a bullet-point outline (≤6 bullets) for a report on: {query}. "
                "Return plain bullets, no prose.",
            ),
        ]
    )

    WRITER_PROMPT = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a senior analyst. Write a concise, well-cited answer.\n"
                "Use the <sources></sources> tag to enclose any sources.",
            ),
            ("user", "{draft_instructions}"),
        ]
    )


# ---------- Token Management ----------
class TokenCounter:
    """
    Utility for counting tokens in text.
    """

    def __init__(self):
        """
        Initialize the token counter with the appropriate encoding.
        """
        self.enc = tiktoken.encoding_for_model("gpt-4o")  # Groq uses o200k_base

    def count(self, text: str) -> int:
        """
        Count the number of tokens in a text string.

        Args:
            text: The text to count tokens for

        Returns:
            Number of tokens
        """
        return len(self.enc.encode(text))


class Budget:
    """
    Token rate limiter to stay within API rate limits.
    """

    def __init__(self, tpm: int):
        """
        Initialize the budget with tokens-per-minute limit.

        Args:
            tpm: Tokens per minute limit
        """
        self.tpm = tpm
        self.window_start = time.time()
        self.used = 0

    def consume(self, n_tokens: int):
        """
        Track token usage and throttle if necessary to stay within budget.

        Args:
            n_tokens: Number of tokens to consume
        """
        now = time.time()
        # reset every 60 s
        if now - self.window_start >= 60:
            self.window_start, self.used = now, 0
        # throttle if over budget
        if self.used + n_tokens > self.tpm:
            sleep = 60 - (now - self.window_start)
            time.sleep(max(0, sleep))
            self.window_start, self.used = time.time(), 0
        self.used += n_tokens


# ---------- Research Pipeline Components ----------
class ResearchPipeline:
    """
    End-to-end research pipeline.
    """

    def __init__(self):
        """
        Initialize the research pipeline with necessary components.
        """
        self.config = Config()
        self.counter = TokenCounter() 
        self.limiter = Budget(self.config.TOKEN_BUDGET)
        self.llm = ChatGroq(
            model=self.config.GROQ_MODEL,
            temperature=0.2,
            max_tokens=self.config.WRITER_TOK,
        )
        self.search_tool = TavilySearchAPIRetriever(k=3)

    def plan(self, query: str) -> list[str]:
        """
        Create a structured outline for the research topic.

        Args:
            query: The research question

        Returns:
            List of outline points
        """
        messages = self.config.PLANNER_PROMPT.format_messages(query=query)
        tokens = (
            sum(self.counter.count(str(m.content)) for m in messages) #tokenizing the input
            + self.config.PLANNER_TOK
        )
        self.limiter.consume(tokens)

        # Get response and ensure we're working with a string
        response = self.llm.invoke(messages)
        outline_text = str(response.content) if response.content is not None else ""

        return [
            line.lstrip("-• ").strip()
            for line in outline_text.splitlines()
            if line.strip()
        ]

    def research(self, bullet: str) -> str:
        """
        Gather evidence for a specific outline point.

        Args:
            bullet: The outline point to research

        Returns:
            Combined search results as text
        """
        hits = self.search_tool.invoke(bullet)
        
        combined = "\n".join(f"{h.metadata['title']} – {h.page_content}" for h in hits)
        return combined

    def write(self, query: str, outline: list[str], sources: dict[str, str]) -> str:
        """
        Draft the final research document using the outline and sources.

        Args:
            query: The original research question
            outline: List of outline points
            sources: Dictionary mapping outline points to their research data

        Returns:
            Completed research document
        """
        draft_instructions = f"Question: {query}\n\n"
        for n, bullet in enumerate(outline, 1):
            draft_instructions += f"Section {n}: {bullet}\n{sources[bullet]}\n\n"
        messages = self.config.WRITER_PROMPT.format_messages(
            draft_instructions=draft_instructions
        )
        tokens_needed = (
            sum(self.counter.count(str(m.content)) for m in messages)
            + self.config.WRITER_TOK
        )
        self.limiter.consume(tokens_needed)

        # Get response and ensure we're working with a string
        response = self.llm.invoke(messages)
        result = str(response.content) if response.content is not None else ""

        # Extract sources from the research results
        source_links = []
        for bullet, content in sources.items():
            # Extract URLs from the content
            lines = content.split('\n')
            for line in lines:
                if 'http' in line:
                    # Extract the URL from the line
                    url_start = line.find('http')
                    if url_start != -1:
                        url_end = line.find(' ', url_start)
                        if url_end == -1:
                            url_end = len(line)
                        url = line[url_start:url_end].strip()
                        if url not in source_links:
                            source_links.append(url)

        # Add sources to the output if they exist
        if source_links:
            result += "\n\n<sources>\n" + "\n".join(source_links) + "\n</sources>"

        return result

    def deep_research(self, query: str) -> str:
        """
        Execute the complete research pipeline.

        Args:
            query: The research question to answer

        Returns:
            Complete research report
        """
        outline = self.plan(query)
        evidence = {b: self.research(b) for b in outline}
        return self.write(query, outline, evidence)


def main():
    """
    Run the research pipeline with command-line arguments.
    """
    parser = argparse.ArgumentParser(description="AI-powered research assistant")
    parser.add_argument(
        "query", nargs="?", default=None, help="Research question to investigate"
    )
    args = parser.parse_args()

    # If no query provided, prompt the user
    query = args.query
    if not query:
        query = input("Enter your research question: ")

    if not query.strip():
        print("Error: Research question cannot be empty")
        return

    # Run the pipeline
    researcher = ResearchPipeline()
    print(f"\nResearching: {query}\n")
    print("Working...\n")
    result = researcher.deep_research(query)
    print("\n" + "=" * 50 + " RESEARCH REPORT " + "=" * 50 + "\n")
    print(result)
    print("\n" + "=" * 120)


if __name__ == "__main__":
    main()
    