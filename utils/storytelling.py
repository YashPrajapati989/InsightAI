import pandas as pd
from typing import Dict, Any, List

class BusinessStoryGenerator:
    """
    Transforms raw dataset analysis and dashboard recommendations into 
    professional, business-friendly narratives suitable for executives.
    """

    def __init__(self, df: pd.DataFrame, profile_report: Dict[str, Any], dashboard_recommendations: Dict[str, Any], original_score: int = None):
        self.df = df
        self.report = profile_report
        self.dash_rec = dashboard_recommendations
        self.original_score = original_score
        
    def generate_summary(self) -> str:
        """Automatically generate a concise executive summary."""
        rows = self.report.get("rows", 0)
        cols = self.report.get("columns", 0)
        current_score = self.report.get("quality_score", 0)
        
        summary = f"This dataset contains {rows:,} records across {cols} columns. "
        
        if self.original_score is not None and self.original_score < current_score:
            summary += f"After cleaning, the data quality improved from {self.original_score}/100 to {current_score}/100. "
        else:
            summary += f"The dataset currently has a data quality score of {current_score}/100. "
            
        themes = self.dash_rec.get("themes", [])
        domain = themes[0].get("domain", "General Analytics") if themes else "General Analytics"
        
        summary += f"Based on our analysis, the dataset is well-suited for {domain.lower()} use cases and provides a strong foundation for data-driven decision making."
        
        return summary

    def generate_kpi_story(self) -> List[Dict[str, str]]:
        """Generate an explanation for every recommended KPI."""
        stories = []
        kpis = self.dash_rec.get("kpis", [])
        
        for kpi in kpis:
            name = kpi.get("name", "")
            reason = kpi.get("reason", "")
            
            # Formulate a more executive-friendly interpretation
            interpretation = f"This KPI measures '{name}' and serves as a critical indicator of performance. {reason}"
            
            stories.append({
                "kpi_name": name,
                "interpretation": interpretation
            })
            
        return stories

    def generate_chart_story(self) -> List[Dict[str, str]]:
        """Generate storytelling text for every recommended visualization."""
        stories = []
        charts = self.dash_rec.get("charts", [])
        
        for chart in charts:
            name = chart.get("chart_name", "Chart")
            x_axis = chart.get("x_axis", "X-Axis")
            y_axis = chart.get("y_axis", "Y-Axis")
            reason = chart.get("reason", "")
            
            purpose = f"Analyzing {y_axis} by {x_axis}"
            description = f"This visualization helps identify underlying patterns and variations when viewing {y_axis} across {x_axis}. {reason}"
            
            stories.append({
                "chart_name": name,
                "business_purpose": purpose,
                "story_description": description
            })
            
        return stories

    def generate_insights(self) -> List[str]:
        """Generate at least 10 intelligent business-oriented insights, deeply analyzing data values."""
        insights = []
        df = self.df
        
        date_cols = [c for c in df.columns if pd.api.types.is_datetime64_any_dtype(df[c])]
        num_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c]) and df[c].nunique() > 2]
        cat_cols = [c for c in df.columns if not pd.api.types.is_numeric_dtype(df[c]) and not pd.api.types.is_datetime64_any_dtype(df[c])]
        
        # Determine primary metrics (e.g., Sales, Revenue, Profit, or just the first numeric column)
        primary_num = None
        for col in num_cols:
            if any(k in str(col).lower() for k in ['sales', 'revenue', 'profit', 'amount', 'total']):
                primary_num = col
                break
        if not primary_num and num_cols:
            primary_num = num_cols[0]

        # 1. Which section is performing well and why
        if primary_num and cat_cols:
            # Let's find a categorical column with reasonable cardinality (e.g., < 20)
            target_cat = None
            for col in cat_cols:
                if 2 <= df[col].nunique() <= 20:
                    target_cat = col
                    break
            
            if target_cat:
                agg_df = df.groupby(target_cat)[primary_num].sum().reset_index()
                if not agg_df.empty:
                    agg_df = agg_df.sort_values(by=primary_num, ascending=False)
                    best_cat = agg_df.iloc[0][target_cat]
                    best_val = agg_df.iloc[0][primary_num]
                    worst_cat = agg_df.iloc[-1][target_cat]
                    worst_val = agg_df.iloc[-1][primary_num]
                    
                    total_val = agg_df[primary_num].sum()
                    if total_val > 0:
                        pct = (best_val / total_val) * 100
                        insights.append(f"The '{best_cat}' segment in '{target_cat}' is performing exceptionally well, generating the highest {primary_num} ({best_val:,.2f}). This segment alone accounts for {pct:.1f}% of the total.")
                        insights.append(f"Conversely, the '{worst_cat}' segment underperformed with a total {primary_num} of {worst_val:,.2f}. Reviewing the strategy and resource allocation for this section is recommended.")
                    else:
                        insights.append(f"The '{best_cat}' segment in '{target_cat}' recorded the highest {primary_num} ({best_val:,.2f}), highlighting a strong concentration of activity.")

        # 2. Why did sales go higher or lower (Time Trend)
        if primary_num and date_cols:
            date_col = date_cols[0]
            try:
                # Group by year-month
                temp_df = df.copy()
                temp_df['year_month'] = temp_df[date_col].dt.to_period('M')
                time_agg = temp_df.groupby('year_month')[primary_num].sum().reset_index()
                time_agg = time_agg.sort_values('year_month')
                
                if len(time_agg) >= 2:
                    best_month = time_agg.loc[time_agg[primary_num].idxmax()]
                    worst_month = time_agg.loc[time_agg[primary_num].idxmin()]
                    
                    insights.append(f"Performance peaked in {best_month['year_month'].strftime('%B %Y')} with a total {primary_num} of {best_month[primary_num]:,.2f}. This surge could be attributed to seasonal demand or successful campaigns during that period.")
                    insights.append(f"The lowest point occurred in {worst_month['year_month'].strftime('%B %Y')} ({worst_month[primary_num]:,.2f}). Investigating external factors or operational bottlenecks during this time is critical.")
                    
                    # Trend direction (compare first half to second half)
                    half = len(time_agg) // 2
                    first_half_sum = time_agg.iloc[:half][primary_num].sum()
                    second_half_sum = time_agg.iloc[half:][primary_num].sum()
                    if second_half_sum > first_half_sum:
                        insights.append(f"Overall, {primary_num} exhibits an upward trend in the latter half of the recorded period, indicating growth and positive momentum.")
                    elif second_half_sum < first_half_sum:
                        insights.append(f"Overall, {primary_num} shows a downward trend in the latter half of the recorded period, suggesting the need for strategic intervention.")
            except Exception:
                pass # Fallback safely if date parsing fails

        # 3. Add existing generic structural insights to reach the 10-insight goal
        if date_cols and num_cols:
            insights.append(f"Monitoring temporal trends in '{num_cols[0]}' over '{date_cols[0]}' will enable more accurate forecasting and capacity planning.")
            
        geo_keywords = ['city', 'region', 'country', 'state', 'location']
        geo_col = next((c for c in df.columns if any(k in str(c).lower() for k in geo_keywords)), None)
        
        if geo_col and primary_num:
            try:
                geo_agg = df.groupby(geo_col)[primary_num].sum().reset_index().sort_values(by=primary_num, ascending=False)
                if not geo_agg.empty:
                    top_geo = geo_agg.iloc[0][geo_col]
                    insights.append(f"Geographically, '{top_geo}' is the top-performing market. Expanding similar strategies to other regions could unlock further growth.")
            except Exception:
                pass

        if len(num_cols) >= 2:
            insights.append(f"Investigating the correlation between '{num_cols[0]}' and '{num_cols[1]}' could uncover hidden operational efficiencies.")
            
        generic_recs = [
            "Customer or entity segmentation can vastly improve targeted marketing and personalization strategies.",
            "Profitability and cost analysis derived from these metrics can support dynamic pricing decisions.",
            "Monitoring outlier behaviors will help in early anomaly detection and fraud prevention.",
            "Automated alerting on these key indicators will reduce reaction time to critical business shifts.",
            "Deeper cohort analysis will improve long-term retention and lifetime value estimations.",
            "Consolidating these data points establishes a unified single source of truth for stakeholder alignment."
        ]
        
        for rec in generic_recs:
            if len(insights) >= 10:
                break
            if rec not in insights:
                insights.append(rec)
            
        return insights[:10]

    def generate_findings(self) -> List[str]:
        """Generate bullet-point findings based on dataset capabilities."""
        findings = []
        df = self.df
        
        date_cols = sum(pd.api.types.is_datetime64_any_dtype(df[c]) for c in df.columns)
        num_cols = sum(pd.api.types.is_numeric_dtype(df[c]) for c in df.columns)
        
        if num_cols > 1:
            findings.append("✓ Dataset contains multiple numerical metrics supporting robust aggregation.")
        elif num_cols == 1:
            findings.append("✓ Dataset contains a primary numerical metric for performance tracking.")
            
        if date_cols > 0:
            findings.append("✓ Date/Time fields are present, fully supporting longitudinal and trend analysis.")
            
        cat_cols = [c for c in df.columns if not pd.api.types.is_numeric_dtype(df[c]) and not pd.api.types.is_datetime64_any_dtype(df[c])]
        
        geo_keywords = ['city', 'region', 'country', 'state', 'zip']
        has_geo = any(any(k in str(c).lower() for k in geo_keywords) for c in df.columns)
        if has_geo:
            findings.append("✓ Regional information is available, enabling geographical comparison.")
            
        cust_keywords = ['customer', 'client', 'user']
        has_cust = any(any(k in str(c).lower() for k in cust_keywords) for c in df.columns)
        if has_cust:
            findings.append("✓ Customer/User level data is present, allowing for detailed segmentation analysis.")
            
        prod_keywords = ['product', 'item', 'category', 'sku']
        has_prod = any(any(k in str(c).lower() for k in prod_keywords) for c in df.columns)
        if has_prod:
            findings.append("✓ Product/Category attributes enable portfolio performance comparison.")
            
        if len(findings) < 5:
            findings.append("✓ Data structure is tabular and well-suited for relational modeling.")
            findings.append("✓ Grain of the data permits drill-down from macro summaries to row-level details.")
            
        return findings

    def generate_recommendations(self) -> List[Dict[str, str]]:
        """Generate business-level risks and actionable recommendations based on data quality issues."""
        recommendations = []
        issues = self.report.get("issues", [])
        
        # Translate technical issues into business risks and recommendations
        for issue in issues:
            if "Missing values detected in" in issue:
                col_name = issue.split("in ")[-1]
                recommendations.append({
                    "risk": f"Large number of missing values in {col_name}.",
                    "recommendation": f"Implement mandatory data collection protocols for {col_name} to improve completeness and downstream analysis accuracy."
                })
            elif "Duplicate records found" in issue:
                recommendations.append({
                    "risk": "High duplicate count distorts true metric volumes.",
                    "recommendation": "Implement strict validation rules and unique constraints during data entry or pipeline ingestion."
                })
            elif "High cardinality column" in issue:
                col_name = issue.split(": ")[-1]
                recommendations.append({
                    "risk": f"Free-text or highly fragmented entries in {col_name} prevent effective categorization.",
                    "recommendation": f"Standardize {col_name} inputs using predefined dropdown menus or controlled vocabularies."
                })
                
        # If no explicit issues, provide general best practices to hit at least 5 recommendations
        general_recs = [
            {
                "risk": "Data staleness could lead to outdated decisions.",
                "recommendation": "Automate data refreshes on a daily or hourly cadence to ensure real-time dashboard accuracy."
            },
            {
                "risk": "Lack of historical context prevents year-over-year comparisons.",
                "recommendation": "Begin archiving snapshot data to build a longitudinal warehouse for trend benchmarking."
            },
            {
                "risk": "Unauthorized access to sensitive columns.",
                "recommendation": "Implement Role-Based Access Control (RBAC) at the BI layer to restrict data visibility."
            },
            {
                "risk": "Siloed dataset limits cross-functional insights.",
                "recommendation": "Integrate this dataset with CRM or ERP systems to enrich the analytical dimensions."
            },
            {
                "risk": "Unmonitored metric drift.",
                "recommendation": "Set up automated anomaly detection alerts for the primary KPIs to catch deviations early."
            }
        ]
        
        for rec in general_recs:
            if len(recommendations) >= 5:
                break
            recommendations.append(rec)
            
        return recommendations

    def generate_report(self) -> Dict[str, Any]:
        """Orchestrate all methods and return the full JSON structure."""
        return {
            "summary": self.generate_summary(),
            "kpi_stories": self.generate_kpi_story(),
            "chart_stories": self.generate_chart_story(),
            "insights": self.generate_insights(),
            "findings": self.generate_findings(),
            "recommendations": self.generate_recommendations(),
        }
