"""Agno Stock Analysis Agent powered by Groq and openai/gpt-oss-120b.

Implements the single-agent architecture specified in PRD Section 7,
with registered tools for deterministic financial calculations, Yahoo Finance,
DuckDuckGo news, and real-time execution transparency tracking (Feature 7).
"""

from datetime import datetime
from typing import Any
import json

from config.settings import settings
from agents.instructions import STOCK_AGENT_SYSTEM_PROMPT, STOCK_AGENT_ANALYSIS_INSTRUCTION
from tools.analysis_tools import (
    calculate_historical_returns,
    calculate_sma,
    calculate_rsi,
    calculate_volatility,
    calculate_affordability,
    calculate_basket_affordability,
)

# Agno Imports
try:
    from agno.agent import Agent
    from agno.models.groq import Groq
    _HAS_AGNO = True
except ImportError:
    _HAS_AGNO = False


class StockPilotAgent:
    """Wrapper around the Agno Agent with tool telemetry and Groq GPT-OSS 120B model."""

    def __init__(self):
        self.model_id = settings.GROQ_MODEL  # strictly 'openai/gpt-oss-120b' from .env
        self.api_key = settings.GROQ_API_KEY
        self.execution_logs: list[dict[str, Any]] = []
        self._init_agent()

    def _init_agent(self) -> None:
        """Initialize the Agno Agent with Groq openai/gpt-oss-120b and tools."""
        if not _HAS_AGNO:
            self.agent = None
            return

        try:
            model = Groq(
                id=self.model_id,
                api_key=self.api_key,
            )

            # Register deterministic mathematical tools
            tools = [
                calculate_historical_returns,
                calculate_sma,
                calculate_rsi,
                calculate_volatility,
                calculate_affordability,
                calculate_basket_affordability,
            ]

            self.agent = Agent(
                model=model,
                tools=tools,
                system_message=STOCK_AGENT_SYSTEM_PROMPT,
                markdown=True,
            )
        except Exception as e:
            print(f"[StockPilotAgent] Initialization warning: {e}")
            self.agent = None

    def log_tool_activity(
        self,
        tool_name: str,
        task_description: str,
        status: str,
        summary: str,
        details: Any = None,
        error: str | None = None,
    ) -> None:
        """Record verified tool execution activity for UI transparency."""
        entry = {
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "tool_name": tool_name,
            "task": task_description,
            "status": status,
            "summary": summary,
            "details": details or {},
            "error": error,
        }
        self.execution_logs.append(entry)

    def run_synthesis(
        self,
        budget: float,
        duration: str,
        risk_tolerance: str,
        stock_preference: str,
        investment_type: str,
        market: str,
        candidate_data: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Synthesize analysis and qualitative rationale using GPT-OSS 120B."""
        # Build prompt summary of verified candidate data
        summary_lines = []
        for c in candidate_data:
            summary_lines.append(
                f"- Symbol: {c.get('symbol')} ({c.get('short_name', '')})\n"
                f"  Sector: {c.get('sector')}, Market Cap Category: {c.get('market_cap_category', 'Large-cap')}\n"
                f"  Current Price: ₹{c.get('current_price', 0):,.2f} (As of {c.get('latest_data_date')})\n"
                f"  Screening Score: {c.get('screening_score')}/100\n"
                f"  Historical Return: {c.get('return_pct')}%\n"
                f"  RSI (14-period): {c.get('rsi')} ({c.get('rsi_zone', 'Neutral')})\n"
                f"  Trend: {c.get('trend')}\n"
                f"  Annualized Volatility: {c.get('annualized_volatility_pct')}%\n"
                f"  Affordable Whole Shares: {c.get('affordable_shares', 0)} (Total Cost: ₹{c.get('total_cost', 0):,.2f})\n"
                f"  Key Reasons: {'; '.join(c.get('key_reasons', []))}\n"
                f"  Identified Cautions: {'; '.join(c.get('key_cautions', []))}\n"
            )

        summary_text = "\n".join(summary_lines)

        prompt = STOCK_AGENT_ANALYSIS_INSTRUCTION.format(
            budget=budget,
            duration=duration,
            risk_tolerance=risk_tolerance,
            stock_preference=stock_preference,
            investment_type=investment_type,
            market=market,
            candidate_data_summary=summary_text,
        )

        agent_response_text = ""
        if self.agent and self.api_key:
            try:
                start_time = datetime.now()
                resp = self.agent.run(prompt)
                duration_sec = (datetime.now() - start_time).total_seconds()

                if hasattr(resp, "content") and resp.content:
                    agent_response_text = resp.content
                else:
                    agent_response_text = str(resp)

                # Capture any tools executed during the run
                if hasattr(resp, "tools") and resp.tools:
                    for t in resp.tools:
                        tool_name = getattr(t, "tool_name", "agent_tool")
                        tool_args = getattr(t, "tool_args", {})
                        has_err = getattr(t, "tool_call_error", False)
                        self.log_tool_activity(
                            tool_name=tool_name,
                            task_description=f"Agent invoked {tool_name}",
                            status="failed" if has_err else "success",
                            summary=f"Executed with args: {tool_args}",
                            details=tool_args,
                        )

                self.log_tool_activity(
                    tool_name="openai/gpt-oss-120b",
                    task_description="AI Agent Rationale Synthesis via Groq",
                    status="success",
                    summary=f"Generated investment synthesis ({duration_sec:.2f}s) across {len(candidate_data)} candidates",
                )
            except Exception as e:
                self.log_tool_activity(
                    tool_name="openai/gpt-oss-120b",
                    task_description="AI Agent Synthesis",
                    status="failed",
                    summary="Synthesis call failed, falling back to structured deterministic summary.",
                    error=str(e),
                )
                agent_response_text = self._fallback_synthesis(candidate_data, budget)
        else:
            agent_response_text = self._fallback_synthesis(candidate_data, budget)

        return {
            "synthesis_markdown": agent_response_text,
            "tool_logs": self.execution_logs,
        }

    def _fallback_synthesis(self, candidates: list[dict[str, Any]], budget: float) -> str:
        """Deterministic fallback explanation if LLM API is unavailable."""
        lines = [
            "### Investment Analysis Overview (Deterministic Grounded Summary)",
            f"Based on your specified budget of **₹{budget:,.2f}**, the analysis evaluated candidate stocks against historical return, moving average trends, RSI momentum, and annualized volatility.\n",
        ]
        for c in candidates:
            lines.append(
                f"#### {c.get('short_name', c.get('symbol'))} ({c.get('symbol')})\n"
                f"- **Screening Score:** {c.get('screening_score')}/100\n"
                f"- **Current Price:** ₹{c.get('current_price', 0):,.2f} | **Affordable Shares:** {c.get('affordable_shares', 0)}\n"
                f"- **Strengths:** {', '.join(c.get('key_reasons', ['Solid fundamentals']))}\n"
                f"- **Key Cautions:** {', '.join(c.get('key_cautions', ['Market volatility risk']))}\n"
            )
        return "\n".join(lines)
