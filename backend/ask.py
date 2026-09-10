"""Interactive Terminal Q&A Interface for IP-SAKTI (RAG 1 + RAG 2)."""
import sys
import io
import asyncio
from pathlib import Path

# Safe encoding for Windows console
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from app.main import lifespan, app
from app.orchestrator.service import orchestrator_service
from app.data.models import MultiRAGQueryRequest


async def main():
    async with lifespan(app):
        print("\n" + "=" * 70)
        print("  * IP-SAKTI Multi-RAG Interactive Testing Console *")
        print("  (RAG 1: Ayurveda Domain + RAG 2: Legal & Regulatory Evidence)")
        print("=" * 70)
        print("Type any question to test (or type 'exit' or 'quit' to stop):\n")

        while True:
            try:
                sys.stdout.write("\n> Enter your question: ")
                sys.stdout.flush()
                line = sys.stdin.readline()
                if not line:
                    break
                query = line.strip()
                if not query or query.lower() in ("exit", "quit", "q"):
                    print("\nExiting IP-SAKTI console. Goodbye!")
                    break

                print("\n[Thinking & Retrieving across RAG 1 and RAG 2...]")
                req = MultiRAGQueryRequest(query=query)
                resp = await orchestrator_service.execute_query(req)

                print("\n" + "-" * 70)
                print(f"Route Decision : {resp.route_decision.target_rags}")
                print(f"Intent Type     : {resp.route_decision.intent}")
                print(f"Router Rationale: {resp.route_decision.explanation}")
                print("-" * 70)

                print("\nSYNTHESIZED RESPONSE:\n")
                print(resp.synthesized_answer)

                print("\n" + "-" * 70)
                print(f"AUTHORITATIVE CITATIONS & EVIDENCE ({len(resp.citations)} found):")
                print("-" * 70)
                for idx, c in enumerate(resp.citations, 1):
                    badge = f"[{c.rag_source}]"
                    print(f"\n[{idx}] {badge} {c.title}")
                    print(f"    Authority Tier : {c.authority_tier}")
                    if c.source_url:
                        print(f"    Source URL     : {c.source_url}")
                    if c.text:
                        clean_snip = " ".join(c.text[:220].split())
                        print(f"    Excerpt        : \"{clean_snip}...\"")

                print("\n" + "=" * 70)

            except (KeyboardInterrupt, EOFError):
                print("\nExiting...")
                break
            except Exception as e:
                print(f"\n[Error processing query]: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
