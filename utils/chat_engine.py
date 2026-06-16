import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # non-interactive backend for web apps
import matplotlib.pyplot as plt
import io
import base64
import re
from typing import Dict, Any, Tuple, List, Optional


class ChatEngine:
    """
    NLP-based Data Assistant that parses user queries, executes Pandas operations,
    and returns text, tables, and charts.

    Supports:
      - Basic aggregations (sum, avg, count, max, min)
      - Group-by analysis with charts
      - Top-N queries with tables
      - Diagnostic / "Why" questions (trend analysis, segment breakdown)
      - Data quality queries (missing, duplicates, score)

    Designed to be modular so the NLP parser can be swapped with an LLM later.
    """

    # Keywords that signal an analytical / diagnostic question
    DIAGNOSTIC_KEYWORDS = [
        'why', 'reason', 'cause', 'explain', 'insight',
        'decline', 'decrease', 'drop', 'fall', 'down',
        'increase', 'rise', 'growth', 'grew', 'up',
        'trending', 'trend', 'perform', 'performing',
        'underperform', 'outperform',
        'compare', 'comparison', 'versus', 'vs',
        'best', 'worst', 'improve', 'weak', 'strong',
    ]

    def __init__(self, df: pd.DataFrame):
        self.df = df

        # Identify columns by type
        self.num_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
        self.cat_cols = [
            c for c in df.columns
            if not pd.api.types.is_numeric_dtype(df[c])
            and not pd.api.types.is_datetime64_any_dtype(df[c])
        ]
        self.date_cols = [c for c in df.columns if pd.api.types.is_datetime64_any_dtype(df[c])]

    # ------------------------------------------------------------------
    # Column finders
    # ------------------------------------------------------------------

    def _find_numeric_column(self, query: str) -> Optional[str]:
        """Find the best matching numeric column from the query."""
        query_lower = query.lower()
        for c in self.num_cols:
            if c.lower() in query_lower:
                return c
        if self.num_cols and any(
            w in query_lower
            for w in [
                'revenue', 'sales', 'profit', 'amount', 'total',
                'average', 'avg', 'sum', 'highest', 'lowest',
                'income', 'cost', 'price', 'value', 'quantity',
            ]
        ):
            return self.num_cols[0]
        return None

    def _find_group_column(self, query: str) -> Optional[str]:
        """Find the best matching categorical column for grouping."""
        query_lower = query.lower()
        for c in self.cat_cols:
            if c.lower() in query_lower:
                return c
        if self.cat_cols and any(
            w in query_lower
            for w in ['by ', 'wise', 'per ', 'each ', 'across ', 'section', 'segment']
        ):
            return self.cat_cols[0]
        if self.date_cols and any(
            w in query_lower
            for w in ['month', 'year', 'day', 'trend', 'date',
                       'monthly', 'daily', 'yearly', 'quarter']
        ):
            return self.date_cols[0]
        return None

    # ------------------------------------------------------------------
    # Intent parser
    # ------------------------------------------------------------------

    def parse_question(self, query: str, context: list = None) -> Dict[str, Any]:
        """Rule-based NLP parser with memory and diagnostic detection."""
        query_lower = query.lower()
        intent = {
            "type": "unknown",
            "operation": None,
            "target_col": None,
            "group_col": None,
            "limit": None,
            "sort": None,
            "requires_chart": False,
            "chart_type": None,
        }

        # Memory: carry forward context from the previous turn
        if context and len(context) > 0:
            last_intent = context[-1].get("parsed_intent", {})
            if any(w in query_lower for w in ["what about", "and the", "how about"]):
                intent["group_col"] = last_intent.get("group_col")

        # 0. Check for diagnostic / analytical question FIRST
        if any(w in query_lower for w in self.DIAGNOSTIC_KEYWORDS):
            intent["type"] = "diagnostic"
            intent["target_col"] = self._find_numeric_column(query_lower)
            intent["group_col"] = self._find_group_column(query_lower)
            # Auto-fill
            if not intent["target_col"] and self.num_cols:
                intent["target_col"] = self.num_cols[0]
            return intent

        # 1. Identify Target Column (Numeric)
        intent["target_col"] = self._find_numeric_column(query_lower)

        # 2. Identify Group Column (Categorical/Date)
        if not intent["group_col"]:
            intent["group_col"] = self._find_group_column(query_lower)

        # 3. Operations
        if any(w in query_lower for w in ['total', 'sum']):
            intent["operation"] = 'sum'
        elif any(w in query_lower for w in ['average', 'avg', 'mean']):
            intent["operation"] = 'mean'
        elif any(w in query_lower for w in ['count', 'how many']):
            intent["operation"] = 'count'
        elif any(w in query_lower for w in ['highest', 'max', 'maximum', 'peak']):
            intent["operation"] = 'max'
            intent["sort"] = 'desc'
        elif any(w in query_lower for w in ['lowest', 'min', 'minimum', 'bottom']):
            intent["operation"] = 'min'
            intent["sort"] = 'asc'

        # 4. Top N
        top_match = re.search(r'top\s+(\d+)', query_lower)
        if top_match:
            intent["limit"] = int(top_match.group(1))
            intent["sort"] = 'desc'
            if not intent["operation"]:
                intent["operation"] = 'sum'

        # --- Smart Auto-Fill ---
        if intent["limit"] and not intent["group_col"] and self.cat_cols:
            intent["group_col"] = self.cat_cols[0]
        if intent["group_col"] and not intent["target_col"] and self.num_cols:
            intent["target_col"] = self.num_cols[0]
        if intent["operation"] and not intent["target_col"] and self.num_cols:
            intent["target_col"] = self.num_cols[0]

        # 5. Chart Rules
        if intent["group_col"]:
            intent["requires_chart"] = True
            if self.date_cols and intent["group_col"] in self.date_cols:
                intent["chart_type"] = 'line'
            elif any(w in query_lower for w in ['contribution', 'share', 'percent', 'pie']):
                intent["chart_type"] = 'pie'
            else:
                intent["chart_type"] = 'bar'

        # 6. Classify
        if intent["group_col"] and intent["limit"]:
            intent["type"] = "top_n"
        elif intent["group_col"]:
            intent["type"] = "group_by"
        elif intent["operation"] and intent["target_col"]:
            intent["type"] = "aggregation"
        elif "duplicate" in query_lower:
            intent["type"] = "duplicates"
        elif "missing" in query_lower or "null" in query_lower:
            intent["type"] = "missing_values"
        elif "quality" in query_lower or "score" in query_lower:
            intent["type"] = "quality_score"

        return intent

    # ------------------------------------------------------------------
    # Query execution
    # ------------------------------------------------------------------

    def execute_query(self, intent: Dict[str, Any]) -> Tuple[Any, pd.DataFrame]:
        """Execute the parsed intent against the DataFrame."""
        q_type = intent["type"]
        df = self.df

        if q_type == "unknown":
            return None, None

        try:
            if q_type == "aggregation":
                col = intent["target_col"]
                op = intent["operation"]
                ops = {'sum': df[col].sum, 'mean': df[col].mean,
                       'max': df[col].max, 'min': df[col].min,
                       'count': df[col].count}
                val = ops.get(op, df[col].sum)()
                return val, None

            elif q_type in ["group_by", "top_n"]:
                target = intent["target_col"]
                group = intent["group_col"]
                op = intent["operation"] or 'sum'

                temp_df = df.copy()
                if self.date_cols and group in self.date_cols:
                    temp_df[group] = temp_df[group].dt.to_period('M').astype(str)

                if target:
                    if op == 'count':
                        agg_df = temp_df.groupby(group).size().reset_index(name='Count')
                        intent["target_col"] = 'Count'
                    else:
                        agg_df = temp_df.groupby(group)[target].agg(op).reset_index()
                else:
                    agg_df = temp_df.groupby(group).size().reset_index(name='Count')
                    intent["target_col"] = 'Count'
                    target = 'Count'

                if intent["sort"] == 'desc':
                    agg_df = agg_df.sort_values(by=target, ascending=False)
                elif intent["sort"] == 'asc':
                    agg_df = agg_df.sort_values(by=target, ascending=True)
                elif self.date_cols and group in self.date_cols:
                    agg_df = agg_df.sort_values(by=group, ascending=True)

                if intent["limit"]:
                    agg_df = agg_df.head(intent["limit"])
                    intent["requires_chart"] = False

                return None, agg_df

            elif q_type == "duplicates":
                count = df.duplicated().sum()
                dups_df = df[df.duplicated(keep=False)].head(10)
                return count, dups_df

            elif q_type == "missing_values":
                missing = df.isnull().sum()
                missing = missing[missing > 0].reset_index()
                missing.columns = ['Column', 'Missing Count']
                return missing['Missing Count'].sum(), missing

            elif q_type == "quality_score":
                total_cells = np.prod(df.shape)
                missing_cells = df.isnull().sum().sum()
                score = 100 * (1 - (missing_cells / total_cells)) if total_cells > 0 else 0
                return round(score, 2), None

        except Exception as e:
            print(f"Query execution error: {e}")
            return None, None

        return None, None

    # ------------------------------------------------------------------
    # Diagnostic / Analytical engine
    # ------------------------------------------------------------------

    def _run_diagnostic(self, query: str, intent: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform multi-dimensional analysis to answer 'why' and
        'insight' questions.  Returns a full response dict.

        Strategy:
        1. Time-trend analysis  (if date columns exist)
        2. Segment breakdown    (across every categorical column)
        3. Correlation hints    (which categories are top/bottom)
        4. Compose a narrative
        """
        df = self.df
        target = intent.get("target_col") or (self.num_cols[0] if self.num_cols else None)
        if target is None:
            return self._unknown_response()

        sections: List[str] = []
        chart_b64 = None
        table_html = None

        # ---- Overall stats ----
        total = float(df[target].sum())
        avg = float(df[target].mean())
        sections.append(
            f"<b>Overall {target}:</b> Total = {total:,.2f} | "
            f"Average = {avg:,.2f} | Records = {len(df):,}"
        )

        # ---- 1. Time-Trend Analysis ----
        if self.date_cols:
            date_col = self.date_cols[0]
            try:
                temp = df.copy()
                temp['_period'] = temp[date_col].dt.to_period('M').astype(str)
                monthly = temp.groupby('_period')[target].sum().reset_index()
                monthly = monthly.sort_values('_period')

                if len(monthly) >= 2:
                    monthly['_change'] = monthly[target].pct_change() * 100
                    best_month = monthly.loc[monthly[target].idxmax()]
                    worst_month = monthly.loc[monthly[target].idxmin()]

                    last = monthly.iloc[-1]
                    prev = monthly.iloc[-2]
                    change_pct = float(last['_change']) if pd.notna(last['_change']) else 0

                    direction = "increased" if change_pct > 0 else "decreased"
                    sections.append(
                        f"<b>📅 Time Trend:</b> From <b>{prev['_period']}</b> to "
                        f"<b>{last['_period']}</b>, {target} {direction} by "
                        f"<b>{abs(change_pct):.1f}%</b>."
                    )
                    sections.append(
                        f"&nbsp;&nbsp;• Best month: <b>{best_month['_period']}</b> "
                        f"({float(best_month[target]):,.2f})"
                    )
                    sections.append(
                        f"&nbsp;&nbsp;• Worst month: <b>{worst_month['_period']}</b> "
                        f"({float(worst_month[target]):,.2f})"
                    )

                    # Generate trend chart
                    chart_b64 = self._make_line_chart(
                        monthly['_period'].astype(str).tolist(),
                        monthly[target].tolist(),
                        f"{target} Monthly Trend",
                        target,
                    )
            except Exception:
                pass  # gracefully skip if date processing fails

        # ---- 2. Segment Breakdown (every categorical column) ----
        for cat in self.cat_cols:
            try:
                seg = df.groupby(cat)[target].agg(['sum', 'mean', 'count']).reset_index()
                seg.columns = [cat, 'Total', 'Average', 'Count']
                seg = seg.sort_values('Total', ascending=False)

                top_seg = seg.iloc[0]
                bottom_seg = seg.iloc[-1]

                total_sum = seg['Total'].sum()
                top_share = (float(top_seg['Total']) / total_sum * 100) if total_sum > 0 else 0

                sections.append(
                    f"<b>📊 By {cat}:</b> "
                    f"<b>{top_seg[cat]}</b> leads with {float(top_seg['Total']):,.2f} "
                    f"({top_share:.1f}% share, avg {float(top_seg['Average']):,.2f}). "
                    f"<b>{bottom_seg[cat]}</b> is the weakest at "
                    f"{float(bottom_seg['Total']):,.2f}."
                )

                # If more than 2 segments, mention the gap
                if len(seg) >= 2:
                    gap = float(top_seg['Total']) - float(bottom_seg['Total'])
                    sections.append(
                        f"&nbsp;&nbsp;• Gap between best and worst {cat}: "
                        f"<b>{gap:,.2f}</b>"
                    )

                # If no time chart was generated, make a bar chart for the first category
                if chart_b64 is None:
                    chart_b64 = self._make_bar_chart(
                        seg[cat].astype(str).head(10).tolist(),
                        seg['Total'].head(10).tolist(),
                        f"{target} by {cat}",
                        target,
                    )
            except Exception:
                pass

        # ---- 3. Additional numeric correlations ----
        if len(self.num_cols) >= 2:
            try:
                corr_pairs = []
                for nc in self.num_cols:
                    if nc != target:
                        corr = df[target].corr(df[nc])
                        if pd.notna(corr):
                            corr_pairs.append((nc, float(corr)))
                corr_pairs.sort(key=lambda x: abs(x[1]), reverse=True)
                if corr_pairs:
                    top_corr = corr_pairs[0]
                    strength = "strong" if abs(top_corr[1]) > 0.6 else "moderate" if abs(top_corr[1]) > 0.3 else "weak"
                    direction = "positive" if top_corr[1] > 0 else "negative"
                    sections.append(
                        f"<b>🔗 Correlation:</b> <b>{target}</b> has a {strength} "
                        f"{direction} correlation ({top_corr[1]:.2f}) with "
                        f"<b>{top_corr[0]}</b>."
                    )
            except Exception:
                pass

        # ---- Build the full narrative ----
        if len(sections) <= 1:
            # We only have the overall stats — not enough data to diagnose
            narrative = (
                f"Based on the available data, the total {target} is "
                f"{total:,.2f} across {len(df):,} records. "
                "To provide deeper insights, the dataset would need "
                "categorical or date columns for comparison."
            )
        else:
            narrative = "<br><br>".join(sections)

        explanation = "Multi-dimensional analysis &rarr; Time Trends &rarr; Segment Breakdown &rarr; Correlations"

        return {
            "answer": narrative,
            "chart": chart_b64,
            "table": table_html,
            "explanation": explanation,
            "query_type": "diagnostic",
            "parsed_intent": self._safe_intent(intent),
            "confidence": 0.85,
        }

    # ------------------------------------------------------------------
    # Chart helpers
    # ------------------------------------------------------------------

    def _make_line_chart(self, labels: list, values: list, title: str, ylabel: str) -> Optional[str]:
        """Generate a line chart and return Base64 string."""
        try:
            plt.figure(figsize=(9, 5))
            plt.style.use('ggplot')
            plt.plot(labels, values, marker='o', color='#10b981',
                     linewidth=2.5, markersize=8)
            plt.xticks(rotation=45, ha='right')
            plt.ylabel(ylabel)
            plt.title(title, pad=15, fontweight='bold', color='#1e293b')
            plt.grid(True, linestyle='--', alpha=0.7)
            plt.tight_layout()
            return self._fig_to_base64()
        except Exception:
            plt.close()
            return None

    def _make_bar_chart(self, labels: list, values: list, title: str, ylabel: str) -> Optional[str]:
        """Generate a bar chart and return Base64 string."""
        try:
            plt.figure(figsize=(9, 5))
            plt.style.use('ggplot')
            plt.bar(labels, values, color='#3b82f6', edgecolor='white', linewidth=1)
            plt.xticks(rotation=45, ha='right')
            plt.ylabel(ylabel)
            plt.title(title, pad=15, fontweight='bold', color='#1e293b')
            plt.tight_layout()
            return self._fig_to_base64()
        except Exception:
            plt.close()
            return None

    def _fig_to_base64(self) -> str:
        """Convert current matplotlib figure to Base64 PNG."""
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=120, transparent=True)
        buf.seek(0)
        plt.close()
        return f"data:image/png;base64,{base64.b64encode(buf.read()).decode('utf-8')}"

    # ------------------------------------------------------------------
    # Legacy chart (for group_by queries)
    # ------------------------------------------------------------------

    def generate_chart(self, agg_df: pd.DataFrame, intent: Dict[str, Any]) -> Optional[str]:
        """Generate Matplotlib chart and return Base64 string."""
        if agg_df is None or agg_df.empty or not intent["requires_chart"]:
            return None

        group_col = intent["group_col"]
        target_col = intent["target_col"] or 'Count'
        chart_type = intent["chart_type"]

        try:
            plt.figure(figsize=(9, 5))
            plt.style.use('ggplot')

            if chart_type == 'bar':
                plot_df = agg_df.head(15)
                plt.bar(plot_df[group_col].astype(str), plot_df[target_col],
                        color='#3b82f6', edgecolor='white', linewidth=1)
                plt.xticks(rotation=45, ha='right')
                plt.ylabel(target_col)
                plt.title(f"{target_col} by {group_col}", pad=15,
                          fontweight='bold', color='#1e293b')

            elif chart_type == 'line':
                plot_df = agg_df.sort_values(by=group_col)
                plt.plot(plot_df[group_col].astype(str), plot_df[target_col],
                         marker='o', color='#10b981', linewidth=2.5, markersize=8)
                plt.xticks(rotation=45, ha='right')
                plt.ylabel(target_col)
                plt.title(f"{target_col} over {group_col}", pad=15,
                          fontweight='bold', color='#1e293b')
                plt.grid(True, linestyle='--', alpha=0.7)

            elif chart_type == 'pie':
                plot_df = agg_df.head(6)
                colors = ['#3b82f6', '#10b981', '#f59e0b',
                          '#ef4444', '#8b5cf6', '#64748b']
                plt.pie(plot_df[target_col],
                        labels=plot_df[group_col].astype(str),
                        autopct='%1.1f%%', colors=colors, startangle=140,
                        wedgeprops={'edgecolor': 'white', 'linewidth': 2})
                plt.title(f"{target_col} Distribution by {group_col}",
                          pad=15, fontweight='bold', color='#1e293b')

            plt.tight_layout()
            return self._fig_to_base64()
        except Exception as e:
            print(f"Chart generation error: {e}")
            plt.close()
            return None

    # ------------------------------------------------------------------
    # Table / Explanation helpers
    # ------------------------------------------------------------------

    def generate_table(self, df: pd.DataFrame) -> Optional[str]:
        """Generate HTML table from DataFrame."""
        if df is None or df.empty:
            return None
        html = df.to_html(classes='data-table', index=False, float_format='%.2f')
        return (
            f"<div class='table-responsive' style='max-height: 400px; "
            f"overflow-y: auto;'>{html}</div>"
        )

    def generate_explanation(self, intent: Dict[str, Any]) -> str:
        """Generate step-by-step trace."""
        steps = []
        if intent.get("group_col"):
            steps.append(f"Group By: <b>{intent['group_col']}</b>")
        if intent.get("operation") and intent.get("target_col"):
            steps.append(f"{intent['operation'].capitalize()}: <b>{intent['target_col']}</b>")
        elif intent.get("target_col"):
            steps.append(f"Metric: <b>{intent['target_col']}</b>")
        if intent.get("sort"):
            dir_str = "Descending" if intent["sort"] == 'desc' else "Ascending"
            steps.append(f"Sort: <b>{dir_str}</b>")
        if intent.get("limit"):
            steps.append(f"Return Top: <b>{intent['limit']}</b>")
        if not steps:
            return "Analyzed dataset metrics directly."
        return " &rarr; ".join(steps)

    # ------------------------------------------------------------------
    # Utility helpers
    # ------------------------------------------------------------------

    def _safe_intent(self, intent: Dict) -> Dict:
        """Convert numpy types in intent dict to JSON-safe Python types."""
        safe = {}
        for k, v in intent.items():
            if isinstance(v, (np.integer,)):
                safe[k] = int(v)
            elif isinstance(v, (np.floating,)):
                safe[k] = float(v)
            elif isinstance(v, np.bool_):
                safe[k] = bool(v)
            else:
                safe[k] = v
        return safe

    def _unknown_response(self) -> Dict[str, Any]:
        """Standard 'not supported' response."""
        return {
            "answer": (
                "This functionality is currently unavailable. "
                "Try asking about totals, averages, trends, rankings, "
                "comparisons, or ask 'why' questions for insights."
            ),
            "chart": None,
            "table": None,
            "explanation": "Could not parse query.",
            "query_type": "unknown",
            "parsed_intent": {},
            "confidence": 0.0,
        }

    # ------------------------------------------------------------------
    # Main orchestrator
    # ------------------------------------------------------------------

    def generate_answer(self, query: str, context: list = None) -> Dict[str, Any]:
        """Main orchestration method."""
        intent = self.parse_question(query, context)

        # Route diagnostic queries to the analytical engine
        if intent["type"] == "diagnostic":
            return self._run_diagnostic(query, intent)

        val, agg_df = self.execute_query(intent)

        answer_text = ""
        chart_b64 = None
        table_html = None
        confidence = 0.0

        if intent["type"] == "unknown":
            return self._unknown_response()

        elif intent["type"] == "aggregation":
            col = intent["target_col"]
            op = intent["operation"]
            if val is not None:
                val = float(val)
                if op == 'count':
                    answer_text = f"The {op} of {col} is {val:,.0f}."
                else:
                    prefix = "₹" if any(
                        w in query.lower()
                        for w in ['revenue', 'sales', 'profit']
                    ) else ""
                    answer_text = (
                        f"The {op} of {col} is {prefix}{val:,.2f}."
                    )
            else:
                answer_text = f"Could not compute {op} on {col}."
            confidence = 0.95

        elif intent["type"] in ["group_by", "top_n"]:
            group = intent["group_col"]
            target = intent["target_col"] or "Count"
            if agg_df is not None and not agg_df.empty:
                top_name = str(agg_df.iloc[0][group])
                top_val = float(agg_df.iloc[0][target])

                prefix = "₹" if any(
                    w in query.lower()
                    for w in ['revenue', 'sales', 'profit']
                ) else ""

                if intent["type"] == "top_n":
                    answer_text = (
                        f"Here are the top {intent['limit']} {group}s "
                        f"based on {target}. '{top_name}' leads with "
                        f"{prefix}{top_val:,.2f}."
                    )
                    table_html = self.generate_table(agg_df)
                else:
                    answer_text = (
                        f"Analyzing {target} across {group}. "
                        f"'{top_name}' generated the highest amount "
                        f"({prefix}{top_val:,.2f})."
                    )
                    chart_b64 = self.generate_chart(agg_df, intent)
            else:
                answer_text = f"Could not group {target} by {group}."
            confidence = 0.90

        elif intent["type"] == "duplicates":
            if val == 0:
                answer_text = "There are no duplicate rows in the dataset."
            else:
                answer_text = f"Found {val} duplicate rows. Here is a sample:"
                table_html = self.generate_table(agg_df)
            confidence = 0.99

        elif intent["type"] == "missing_values":
            if val == 0:
                answer_text = "There are no missing values in the dataset."
            else:
                answer_text = (
                    f"Found {val} total missing values across the dataset."
                )
                table_html = self.generate_table(agg_df)
            confidence = 0.99

        elif intent["type"] == "quality_score":
            answer_text = f"The current Data Quality Score is {val}/100."
            confidence = 0.99

        return {
            "answer": answer_text,
            "chart": chart_b64,
            "table": table_html,
            "explanation": self.generate_explanation(intent),
            "query_type": intent["type"],
            "parsed_intent": self._safe_intent(intent),
            "confidence": float(confidence),
        }
