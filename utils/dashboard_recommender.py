import pandas as pd
from typing import Dict, Any, List

class DashboardRecommender:
    """
    Analyzes dataset columns and structure to automatically recommend
    KPIs, charts, dashboard layouts, business questions, and AI insights.
    """

    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.columns_info: Dict[str, str] = {}
        self.date_cols: List[str] = []
        self.numeric_cols: List[str] = []
        self.categorical_cols: List[str] = []
        self.boolean_cols: List[str] = []
        self.id_cols: List[str] = []
        
        self.analyze_columns()

    def analyze_columns(self) -> Dict[str, str]:
        """
        Classify columns as Date/Time, Boolean, Identifier, Numerical, or Categorical.
        """
        for col in self.df.columns:
            series = self.df[col]
            col_name_lower = str(col).lower()
            
            # 1. Date/Time Detection
            if pd.api.types.is_datetime64_any_dtype(series):
                self.columns_info[col] = "Date/Time"
                self.date_cols.append(col)
                continue
            
            if 'date' in col_name_lower or 'time' in col_name_lower or 'year' in col_name_lower or 'month' in col_name_lower:
                # Check if parseable as datetime
                try:
                    parsed = pd.to_datetime(series.dropna().head(10), errors='coerce')
                    if not parsed.isna().all():
                        self.columns_info[col] = "Date/Time"
                        self.date_cols.append(col)
                        continue
                except Exception:
                    pass

            # 2. Boolean Detection
            if pd.api.types.is_bool_dtype(series):
                self.columns_info[col] = "Boolean"
                self.boolean_cols.append(col)
                continue
                
            unique_vals = series.dropna().unique()
            if len(unique_vals) <= 2:
                # Check if it looks like boolean flags
                set_vals = set(str(v).lower() for v in unique_vals)
                if set_vals.issubset({'true', 'false', '0', '1', 'yes', 'no', 'y', 'n'}):
                    self.columns_info[col] = "Boolean"
                    self.boolean_cols.append(col)
                    continue

            # 3. Identifier Detection
            is_id_name = any(x in col_name_lower for x in ['id', 'key', 'code', 'num', 'pk'])
            if is_id_name and not pd.api.types.is_float_dtype(series):
                # Ensure it's not a general float measure like SalesNum
                unique_ratio = series.nunique() / len(series) if len(series) > 0 else 0
                if unique_ratio > 0.5 or 'id' in col_name_lower:
                    self.columns_info[col] = "Identifier"
                    self.id_cols.append(col)
                    continue

            # 4. Numerical Detection
            if pd.api.types.is_numeric_dtype(series):
                self.columns_info[col] = "Numerical"
                self.numeric_cols.append(col)
                continue

            # 5. Categorical Fallback
            self.columns_info[col] = "Categorical"
            self.categorical_cols.append(col)
            
        return self.columns_info

    def recommend_kpis(self) -> List[Dict[str, Any]]:
        """
        Recommend KPI Cards based on numeric columns and identifiers.
        """
        kpis = []
        df = self.df
        
        # We can aggregate numerical fields
        for col in self.numeric_cols:
            col_name_lower = str(col).lower()
            series = df[col].dropna()
            if series.empty:
                continue
                
            # Sales / Revenue
            if any(x in col_name_lower for x in ['sales', 'revenue', 'amount', 'spend', 'price']):
                total_val = series.sum()
                kpis.append({
                    "name": f"Total {col}",
                    "value": f"${total_val:,.2f}" if total_val > 100 else f"{total_val:,.0f}",
                    "reason": f"Tracks overall financial volume generated under '{col}'."
                })
                
                avg_val = series.mean()
                kpis.append({
                    "name": f"Average {col}",
                    "value": f"${avg_val:,.2f}" if avg_val > 10 else f"{avg_val:,.2f}",
                    "reason": f"Shows the average transaction or unit value for '{col}'."
                })
                
            # Profit / Margins
            elif any(x in col_name_lower for x in ['profit', 'margin', 'gain', 'income']):
                total_profit = series.sum()
                kpis.append({
                    "name": f"Total {col}",
                    "value": f"${total_profit:,.2f}" if total_profit > 100 else f"{total_profit:,.0f}",
                    "reason": f"Summarizes net returns and profitability across '{col}'."
                })

            # Quality/Ratings
            elif any(x in col_name_lower for x in ['rating', 'score', 'satisfaction']):
                avg_score = series.mean()
                kpis.append({
                    "name": f"Average {col}",
                    "value": f"{avg_score:.2f}",
                    "reason": f"Measures the mean quality score or feedback metrics for '{col}'."
                })
                
        # Unique counts for IDs
        for col in self.id_cols:
            col_name_lower = str(col).lower()
            unique_cnt = df[col].nunique()
            
            if 'customer' in col_name_lower or 'user' in col_name_lower or 'client' in col_name_lower:
                kpis.append({
                    "name": f"Total Customers",
                    "value": f"{unique_cnt:,}",
                    "reason": f"Measures unique client reach based on identifier '{col}'."
                })
            elif 'order' in col_name_lower or 'invoice' in col_name_lower or 'trans' in col_name_lower:
                kpis.append({
                    "name": f"Total Orders",
                    "value": f"{unique_cnt:,}",
                    "reason": f"Calculates overall volume of transactions processed."
                })
            else:
                kpis.append({
                    "name": f"Unique {col} Count",
                    "value": f"{unique_cnt:,}",
                    "reason": f"Counts distinct active entries for '{col}'."
                })
                
        # Default fallback KPIs if nothing specific is found
        if not kpis:
            kpis.append({
                "name": "Total Records",
                "value": f"{len(df):,}",
                "reason": "Indicates the overall count of rows loaded into the dataset."
            })
            kpis.append({
                "name": "Total Columns",
                "value": f"{len(df.columns)}",
                "reason": "Represents the structural width of the dataset."
            })

        return kpis[:4] # Limit to top 4 KPIs for screen space

    def recommend_charts(self) -> List[Dict[str, Any]]:
        """
        Generate chart suggestions based on column types.
        """
        charts = []
        
        # 1. Date + Numeric -> Line Chart
        if self.date_cols and self.numeric_cols:
            date_col = self.date_cols[0]
            for num_col in self.numeric_cols:
                if any(x in str(num_col).lower() for x in ['sales', 'revenue', 'profit', 'spend', 'amount']):
                    charts.append({
                        "chart_name": "Line Chart",
                        "x_axis": date_col,
                        "y_axis": num_col,
                        "reason": f"Perfect for visualising temporal trends in '{num_col}' over '{date_col}'."
                    })
                    break

        # 2. Categorical + Numeric -> Bar Chart
        if self.categorical_cols and self.numeric_cols:
            cat_col = self.categorical_cols[0]
            for num_col in self.numeric_cols:
                if any(x in str(num_col).lower() for x in ['sales', 'revenue', 'profit', 'amount']):
                    charts.append({
                        "chart_name": "Bar Chart",
                        "x_axis": cat_col,
                        "y_axis": num_col,
                        "reason": f"Ideal for comparing summary aggregates of '{num_col}' across different '{cat_col}' divisions."
                    })
                    break

        # 3. Categorical (Low Cardinality) -> Pie Chart
        for col in self.categorical_cols:
            unique_cnt = self.df[col].nunique()
            if 2 <= unique_cnt <= 6:
                charts.append({
                    "chart_name": "Pie Chart",
                    "x_axis": col,
                    "y_axis": "Record Count",
                    "reason": f"Shows the proportional distribution of '{col}' since it has only {unique_cnt} unique values."
                })
                break

        # 4. Two Numeric columns -> Scatter Plot
        if len(self.numeric_cols) >= 2:
            num1, num2 = self.numeric_cols[0], self.numeric_cols[1]
            charts.append({
                "chart_name": "Scatter Plot",
                "x_axis": num1,
                "y_axis": num2,
                "reason": f"Examines the correlation and distribution pattern between '{num1}' and '{num2}'."
            })

        # 5. Geographic Column -> Map
        geo_keywords = ['city', 'region', 'country', 'state', 'postal', 'zip', 'lat', 'lon']
        geo_col = None
        for col in self.df.columns:
            if any(x in str(col).lower() for x in geo_keywords):
                geo_col = col
                break
        if geo_col and self.numeric_cols:
            num_col = self.numeric_cols[0]
            charts.append({
                "chart_name": "Geographic Map",
                "x_axis": geo_col,
                "y_axis": num_col,
                "reason": f"Visualizes regional variance and clusters of '{num_col}' on an interactive map using '{geo_col}'."
            })

        # 6. Multiple Categorical + Numeric -> Stacked Bar Chart
        if len(self.categorical_cols) >= 2 and self.numeric_cols:
            cat1, cat2 = self.categorical_cols[0], self.categorical_cols[1]
            num_col = self.numeric_cols[0]
            charts.append({
                "chart_name": "Stacked Bar Chart",
                "x_axis": cat1,
                "y_axis": f"{num_col} by {cat2}",
                "reason": f"Breaks down '{num_col}' values across '{cat1}' categories segmented by secondary sub-categories in '{cat2}'."
            })

        # 7. Distribution -> Histogram
        if self.numeric_cols:
            num_col = self.numeric_cols[0]
            charts.append({
                "chart_name": "Histogram",
                "x_axis": num_col,
                "y_axis": "Frequency",
                "reason": f"Displays the underlying data distribution and frequency dispersion of '{num_col}'."
            })

        # 8. Correlation -> Correlation Heatmap
        if len(self.numeric_cols) >= 3:
            charts.append({
                "chart_name": "Heatmap",
                "x_axis": "Numerical Columns Matrix",
                "y_axis": "Correlation Score",
                "reason": "Illustrates statistical relationship strengths between all numerical fields in a single view."
            })

        # Fallback if no charts generated
        if not charts:
            charts.append({
                "chart_name": "Bar Chart",
                "x_axis": self.df.columns[0],
                "y_axis": "Record Count",
                "reason": "Fallback chart showing categorical frequency of the first column."
            })

        return charts[:6] # Limit to top 6 charts

    def recommend_layout(self, kpis: List[Dict[str, Any]], charts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Arrange recommended elements into a logical dashboard wireframe layout.
        """
        layout = {
            "top": [kpi["name"] for kpi in kpis],
            "middle_left": "N/A",
            "middle_right": "N/A",
            "bottom_left": "N/A",
            "bottom_right": "N/A"
        }
        
        # Populate middle and bottom chart placeholders
        if len(charts) >= 1:
            c = charts[0]
            layout["middle_left"] = f"{c['chart_name']} ({c['x_axis']} vs {c['y_axis']})"
            
        if len(charts) >= 2:
            c = charts[1]
            layout["middle_right"] = f"{c['chart_name']} ({c['x_axis']} vs {c['y_axis']})"
            
        if len(charts) >= 3:
            c = charts[2]
            layout["bottom_left"] = f"{c['chart_name']} ({c['x_axis']} vs {c['y_axis']})"
            
        if len(charts) >= 4:
            c = charts[3]
            layout["bottom_right"] = f"{c['chart_name']} ({c['x_axis']} vs {c['y_axis']})"
        elif len(self.categorical_cols) > 0:
            layout["bottom_right"] = f"Leaderboard / Top 10 by {self.categorical_cols[0]}"
            
        return layout

    def generate_questions(self) -> List[str]:
        """
        Generate at least 5 relevant business questions the user can solve using the dataset.
        """
        questions = []
        
        # Find some key columns
        date_col = self.date_cols[0] if self.date_cols else None
        num_col = self.numeric_cols[0] if self.numeric_cols else None
        cat_col = self.categorical_cols[0] if self.categorical_cols else None
        
        # Geo column
        geo_keywords = ['city', 'region', 'country', 'state']
        geo_col = next((col for col in self.df.columns if any(x in str(col).lower() for x in geo_keywords)), None)
        
        # Question 1: Geo performance
        if geo_col and num_col:
            questions.append(f"Which {geo_col} performs best based on total/average {num_col}?")
        elif cat_col and num_col:
            questions.append(f"Which {cat_col} generates the highest average {num_col}?")
        else:
            questions.append("Which category segment drives the highest business activity?")
            
        # Question 2: Categories comparison
        if len(self.categorical_cols) >= 2 and num_col:
            questions.append(f"How does {num_col} vary when comparing {self.categorical_cols[0]} and {self.categorical_cols[1]}?")
        elif cat_col and num_col:
            questions.append(f"What is the average {num_col} contribution per '{cat_col}'?")
        else:
            questions.append("What is the average metrics output across core dimensions?")
            
        # Question 3: Time trends
        if date_col and num_col:
            questions.append(f"Which month or quarter has the lowest/highest values for {num_col}?")
        else:
            questions.append("Are there visible cyclical trends or seasonal spikes in the dataset transactions?")

        # Question 4: Outliers & distribution
        if num_col:
            questions.append(f"Are there any outliers or anomalies in the values for '{num_col}'?")
        else:
            questions.append("What is the typical size or frequency distribution of records in the dataset?")

        # Question 5: Correlations
        if len(self.numeric_cols) >= 2:
            questions.append(f"Is there a statistical correlation between '{self.numeric_cols[0]}' and '{self.numeric_cols[1]}'?")
        else:
            questions.append("What indicators show the highest growth potential based on transaction volume?")
            
        return questions

    def generate_insights(self) -> List[str]:
        """
        Generate structural and semantic metadata insights about the dataset.
        """
        insights = []
        
        # Date column insight
        if self.date_cols:
            insights.append(
                f"The dataset contains a date/time column '{self.date_cols[0]}', "
                "which is ideal for rendering line charts and tracking monthly/yearly business performance trends."
            )
            
        # Categorical insight
        if self.categorical_cols:
            insights.append(
                f"The categorical column '{self.categorical_cols[0]}' contains distinct divisions. "
                "We recommend comparing aggregates using a horizontal bar or stacked column chart."
            )
            
        # Geographical insight
        geo_keywords = ['city', 'region', 'country', 'state']
        geo_col = next((col for col in self.df.columns if any(x in str(col).lower() for x in geo_keywords)), None)
        if geo_col:
            insights.append(
                f"Region-related indicator detected in '{geo_col}'. "
                "This allows you to construct geo-maps or cluster charts to spot geographic pockets of activity."
            )
            
        # Numeric correlation insight
        if len(self.numeric_cols) >= 2:
            insights.append(
                f"Multiple numeric columns are present (e.g. '{self.numeric_cols[0]}' and '{self.numeric_cols[1]}'). "
                "This allows you to build scatter charts to investigate dependencies and correlations."
            )
            
        # Boolean insight
        if self.boolean_cols:
            insights.append(
                f"Boolean field '{self.boolean_cols[0]}' is present. "
                "This can be used to filter or slice the entire dashboard report cleanly."
            )
            
        # Fallback if short of insights
        if len(insights) < 3:
            insights.append("Simple tabular data detected. Ideal for structured grid layouts and list sorting dashboards.")
            
        return insights

    def recommend_theme(self) -> Dict[str, Any]:
        """
        Recommend a complete dashboard design system — colors, typography,
        shadows, borders, chart styling, gridlines, and more.
        Theme is chosen based on dataset domain keywords detected in column names.
        """
        col_names_combined = " ".join(str(c).lower() for c in self.df.columns)

        # --- Detect Domain ---
        is_financial  = any(x in col_names_combined for x in ['sales','revenue','profit','income','expense','budget','cost','amount','price'])
        is_healthcare  = any(x in col_names_combined for x in ['patient','diagnosis','health','hospital','medical','treatment','dose'])
        is_hr          = any(x in col_names_combined for x in ['employee','department','salary','hr','performance','attendance','leave'])
        is_retail      = any(x in col_names_combined for x in ['product','category','order','customer','purchase','store','inventory','sku'])
        is_marketing   = any(x in col_names_combined for x in ['campaign','clicks','impressions','ctr','conversion','lead','funnel','ad'])
        is_logistics   = any(x in col_names_combined for x in ['shipment','delivery','warehouse','freight','carrier','route','dispatch'])

        # ===================================================================
        # FINANCIAL / SALES THEME  — dark professional navy
        # ===================================================================
        if is_financial or is_retail:
            theme = {
                "theme_name": "Executive Finance",
                "domain": "Financial / Retail Analytics",

                # Canvas
                "canvas": {
                    "background_color": "#0f172a",
                    "page_background": "#1e293b",
                    "grid_gap": "24px",
                    "border_radius_page": "0px",
                    "padding": "32px",
                },

                # Typography
                "typography": {
                    "font_family": "'Inter', 'Segoe UI', sans-serif",
                    "dashboard_title_font_size": "28px",
                    "dashboard_title_font_weight": "700",
                    "dashboard_title_color": "#f1f5f9",
                    "dashboard_title_letter_spacing": "0.04em",
                    "section_header_font_size": "14px",
                    "section_header_color": "#94a3b8",
                    "section_header_font_weight": "600",
                    "section_header_text_transform": "uppercase",
                    "section_header_letter_spacing": "0.08em",
                    "body_font_size": "13px",
                    "body_color": "#cbd5e1",
                    "kpi_value_font_size": "36px",
                    "kpi_value_font_weight": "800",
                    "kpi_value_color": "#ffffff",
                    "kpi_label_font_size": "12px",
                    "kpi_label_color": "#94a3b8",
                    "axis_label_font_size": "11px",
                    "axis_label_color": "#64748b",
                    "data_label_font_size": "11px",
                    "data_label_color": "#e2e8f0",
                    "legend_font_size": "12px",
                    "legend_color": "#94a3b8",
                    "tooltip_font_size": "12px",
                    "tooltip_color": "#f1f5f9",
                },

                # KPI Cards
                "kpi_card": {
                    "background": "linear-gradient(145deg, #1e3a5f 0%, #1e293b 100%)",
                    "border": "1px solid rgba(99, 179, 237, 0.15)",
                    "border_radius": "16px",
                    "padding": "24px 28px",
                    "box_shadow": "0 4px 24px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.05)",
                    "accent_bar_color": "#3b82f6",
                    "accent_bar_width": "4px",
                    "hover_shadow": "0 8px 32px rgba(59,130,246,0.25)",
                    "hover_border": "1px solid rgba(59,130,246,0.4)",
                    "icon_background": "rgba(59,130,246,0.12)",
                    "icon_color": "#60a5fa",
                },

                # Chart Panel
                "chart_panel": {
                    "background": "#1e293b",
                    "border": "1px solid rgba(148,163,184,0.08)",
                    "border_radius": "16px",
                    "padding": "24px",
                    "box_shadow": "0 2px 16px rgba(0,0,0,0.35)",
                    "header_border_bottom": "1px solid rgba(148,163,184,0.1)",
                    "header_padding_bottom": "14px",
                    "header_margin_bottom": "20px",
                },

                # Chart Colors (ordered for sequential use)
                "chart_colors": {
                    "primary_palette": ["#3b82f6","#06b6d4","#8b5cf6","#10b981","#f59e0b","#ef4444","#ec4899","#14b8a6"],
                    "positive_color": "#10b981",
                    "negative_color": "#ef4444",
                    "neutral_color": "#94a3b8",
                    "line_chart_color": "#3b82f6",
                    "line_chart_fill": "rgba(59,130,246,0.08)",
                    "line_chart_stroke_width": "2.5px",
                    "bar_chart_color": "#3b82f6",
                    "bar_chart_hover_color": "#60a5fa",
                    "bar_chart_border_radius": "6px 6px 0 0",
                    "pie_chart_colors": ["#3b82f6","#06b6d4","#8b5cf6","#10b981","#f59e0b","#ef4444"],
                    "scatter_dot_color": "#8b5cf6",
                    "scatter_dot_radius": "5px",
                    "heatmap_low": "#1e293b",
                    "heatmap_high": "#3b82f6",
                },

                # Axes & Gridlines
                "axes_and_gridlines": {
                    "gridline_color": "rgba(148,163,184,0.08)",
                    "gridline_style": "dashed",
                    "gridline_width": "1px",
                    "show_x_gridlines": False,
                    "show_y_gridlines": True,
                    "axis_line_color": "rgba(148,163,184,0.15)",
                    "axis_tick_color": "#475569",
                    "zero_line_color": "rgba(148,163,184,0.3)",
                    "zero_line_width": "1px",
                },

                # Data Labels
                "data_labels": {
                    "show_on_bars": True,
                    "show_on_lines": False,
                    "show_on_pie": True,
                    "position": "outside",
                    "font_size": "11px",
                    "font_weight": "600",
                    "color": "#e2e8f0",
                    "background": "transparent",
                    "border_radius": "4px",
                    "padding": "2px 4px",
                },

                # Tooltip
                "tooltip": {
                    "background": "#0f172a",
                    "border": "1px solid rgba(99,179,237,0.2)",
                    "border_radius": "10px",
                    "padding": "12px 16px",
                    "box_shadow": "0 8px 24px rgba(0,0,0,0.6)",
                    "font_size": "12px",
                    "text_color": "#f1f5f9",
                    "header_color": "#94a3b8",
                    "value_color": "#60a5fa",
                },

                # Legend
                "legend": {
                    "position": "bottom",
                    "font_size": "12px",
                    "color": "#94a3b8",
                    "marker_shape": "circle",
                    "marker_size": "8px",
                    "gap_between_items": "16px",
                },

                # Filters / Slicers
                "slicer": {
                    "background": "#1e293b",
                    "border": "1px solid rgba(148,163,184,0.15)",
                    "border_radius": "10px",
                    "active_background": "#3b82f6",
                    "active_color": "#ffffff",
                    "font_size": "13px",
                    "color": "#94a3b8",
                    "padding": "8px 14px",
                },

                # Dashboard Title
                "dashboard_title": {
                    "text": "Executive Performance Dashboard",
                    "font_size": "28px",
                    "font_weight": "700",
                    "color": "#f1f5f9",
                    "subtitle_text": "Real-time KPI monitoring and trend analysis",
                    "subtitle_color": "#94a3b8",
                    "subtitle_font_size": "14px",
                    "border_bottom": "1px solid rgba(148,163,184,0.1)",
                    "padding_bottom": "24px",
                    "margin_bottom": "32px",
                    "logo_alignment": "right",
                },

                # Table Styling
                "table": {
                    "header_background": "#1e3a5f",
                    "header_color": "#93c5fd",
                    "header_font_weight": "700",
                    "row_background": "#1e293b",
                    "alternate_row_background": "#162032",
                    "border": "1px solid rgba(148,163,184,0.08)",
                    "row_hover_background": "rgba(59,130,246,0.08)",
                    "cell_padding": "10px 14px",
                    "font_size": "13px",
                    "color": "#cbd5e1",
                    "border_radius": "10px",
                },
            }

        # ===================================================================
        # HEALTHCARE THEME  — clean teal & white
        # ===================================================================
        elif is_healthcare:
            theme = {
                "theme_name": "Clinical Clarity",
                "domain": "Healthcare Analytics",
                "canvas": {"background_color": "#f0fdf9","page_background": "#ffffff","grid_gap": "20px","border_radius_page": "0px","padding": "28px"},
                "typography": {"font_family": "'DM Sans', 'Inter', sans-serif","dashboard_title_font_size": "26px","dashboard_title_color": "#134e4a","kpi_value_font_size": "34px","kpi_value_color": "#0f766e","kpi_label_color": "#64748b","body_color": "#374151","axis_label_color": "#6b7280","data_label_color": "#1f2937"},
                "kpi_card": {"background": "#ffffff","border": "1px solid #ccfbf1","border_radius": "14px","padding": "22px 26px","box_shadow": "0 2px 16px rgba(20,184,166,0.1)","accent_bar_color": "#14b8a6","icon_color": "#0d9488"},
                "chart_panel": {"background": "#ffffff","border": "1px solid #e2e8f0","border_radius": "14px","padding": "22px","box_shadow": "0 2px 12px rgba(0,0,0,0.06)"},
                "chart_colors": {"primary_palette": ["#0d9488","#06b6d4","#3b82f6","#8b5cf6","#f59e0b","#ef4444"],"line_chart_color": "#14b8a6","bar_chart_color": "#0d9488","pie_chart_colors": ["#14b8a6","#06b6d4","#3b82f6","#8b5cf6","#f59e0b","#ef4444"],"positive_color": "#10b981","negative_color": "#ef4444"},
                "axes_and_gridlines": {"gridline_color": "rgba(0,0,0,0.05)","gridline_style": "solid","show_y_gridlines": True,"show_x_gridlines": False,"axis_line_color": "#e2e8f0","axis_tick_color": "#9ca3af"},
                "data_labels": {"show_on_bars": True,"show_on_pie": True,"font_size": "11px","color": "#374151","position": "outside"},
                "tooltip": {"background": "#ffffff","border": "1px solid #ccfbf1","border_radius": "10px","padding": "12px 16px","box_shadow": "0 4px 20px rgba(0,0,0,0.12)","text_color": "#111827"},
                "legend": {"position": "bottom","font_size": "12px","color": "#6b7280","marker_shape": "circle"},
                "slicer": {"background": "#f0fdf9","border": "1px solid #99f6e4","border_radius": "8px","active_background": "#14b8a6","active_color": "#ffffff","font_size": "13px"},
                "dashboard_title": {"text": "Clinical Operations Dashboard","font_size": "26px","font_weight": "700","color": "#134e4a","subtitle_text": "Patient outcomes, resource utilization, and performance metrics","subtitle_color": "#64748b"},
                "table": {"header_background": "#f0fdf9","header_color": "#0f766e","row_background": "#ffffff","alternate_row_background": "#f8fffe","border": "1px solid #ccfbf1","row_hover_background": "rgba(20,184,166,0.05)","font_size": "13px","color": "#374151","border_radius": "10px"},
            }

        # ===================================================================
        # HR THEME  — warm violet & amber
        # ===================================================================
        elif is_hr:
            theme = {
                "theme_name": "People Analytics",
                "domain": "HR & Workforce Analytics",
                "canvas": {"background_color": "#faf5ff","page_background": "#ffffff","grid_gap": "20px","border_radius_page": "0px","padding": "28px"},
                "typography": {"font_family": "'Outfit', 'Inter', sans-serif","dashboard_title_font_size": "26px","dashboard_title_color": "#581c87","kpi_value_font_size": "34px","kpi_value_color": "#7c3aed","kpi_label_color": "#6b7280","body_color": "#374151","axis_label_color": "#6b7280","data_label_color": "#1f2937"},
                "kpi_card": {"background": "#ffffff","border": "1px solid #ede9fe","border_radius": "14px","padding": "22px 26px","box_shadow": "0 2px 16px rgba(124,58,237,0.1)","accent_bar_color": "#8b5cf6","icon_color": "#7c3aed"},
                "chart_panel": {"background": "#ffffff","border": "1px solid #ede9fe","border_radius": "14px","padding": "22px","box_shadow": "0 2px 12px rgba(0,0,0,0.06)"},
                "chart_colors": {"primary_palette": ["#8b5cf6","#a78bfa","#f59e0b","#ec4899","#06b6d4","#10b981"],"line_chart_color": "#8b5cf6","bar_chart_color": "#8b5cf6","pie_chart_colors": ["#8b5cf6","#a78bfa","#f59e0b","#ec4899","#06b6d4","#10b981"],"positive_color": "#10b981","negative_color": "#ef4444"},
                "axes_and_gridlines": {"gridline_color": "rgba(0,0,0,0.05)","gridline_style": "solid","show_y_gridlines": True,"show_x_gridlines": False,"axis_line_color": "#ede9fe","axis_tick_color": "#9ca3af"},
                "data_labels": {"show_on_bars": True,"show_on_pie": True,"font_size": "11px","color": "#374151","position": "outside"},
                "tooltip": {"background": "#ffffff","border": "1px solid #ede9fe","border_radius": "10px","padding": "12px 16px","box_shadow": "0 4px 20px rgba(0,0,0,0.12)","text_color": "#111827"},
                "legend": {"position": "bottom","font_size": "12px","color": "#6b7280","marker_shape": "circle"},
                "slicer": {"background": "#faf5ff","border": "1px solid #ede9fe","border_radius": "8px","active_background": "#8b5cf6","active_color": "#ffffff","font_size": "13px"},
                "dashboard_title": {"text": "People Analytics Dashboard","font_size": "26px","font_weight": "700","color": "#581c87","subtitle_text": "Workforce performance, headcount, and engagement metrics","subtitle_color": "#6b7280"},
                "table": {"header_background": "#faf5ff","header_color": "#7c3aed","row_background": "#ffffff","alternate_row_background": "#fdfcff","border": "1px solid #ede9fe","row_hover_background": "rgba(139,92,246,0.05)","font_size": "13px","color": "#374151","border_radius": "10px"},
            }

        # ===================================================================
        # MARKETING THEME  — bold orange & yellow
        # ===================================================================
        elif is_marketing:
            theme = {
                "theme_name": "Growth Marketing",
                "domain": "Marketing & Campaign Analytics",
                "canvas": {"background_color": "#0c0a09","page_background": "#1c1917","grid_gap": "22px","border_radius_page": "0px","padding": "30px"},
                "typography": {"font_family": "'Sora', 'Inter', sans-serif","dashboard_title_font_size": "28px","dashboard_title_color": "#fef3c7","kpi_value_font_size": "36px","kpi_value_color": "#fbbf24","kpi_label_color": "#a8a29e","body_color": "#d6d3d1","axis_label_color": "#78716c","data_label_color": "#fef3c7"},
                "kpi_card": {"background": "linear-gradient(145deg, #292524 0%, #1c1917 100%)","border": "1px solid rgba(251,191,36,0.2)","border_radius": "16px","padding": "24px 28px","box_shadow": "0 4px 24px rgba(0,0,0,0.5)","accent_bar_color": "#f59e0b","icon_color": "#fbbf24"},
                "chart_panel": {"background": "#1c1917","border": "1px solid rgba(251,191,36,0.08)","border_radius": "16px","padding": "24px","box_shadow": "0 2px 16px rgba(0,0,0,0.4)"},
                "chart_colors": {"primary_palette": ["#f59e0b","#ef4444","#ec4899","#8b5cf6","#06b6d4","#10b981"],"line_chart_color": "#f59e0b","line_chart_fill": "rgba(245,158,11,0.08)","bar_chart_color": "#f59e0b","pie_chart_colors": ["#f59e0b","#ef4444","#ec4899","#8b5cf6","#06b6d4","#10b981"],"positive_color": "#10b981","negative_color": "#ef4444"},
                "axes_and_gridlines": {"gridline_color": "rgba(255,255,255,0.05)","gridline_style": "dashed","show_y_gridlines": True,"show_x_gridlines": False,"axis_line_color": "rgba(255,255,255,0.08)","axis_tick_color": "#78716c"},
                "data_labels": {"show_on_bars": True,"show_on_pie": True,"font_size": "11px","color": "#fef3c7","position": "outside"},
                "tooltip": {"background": "#0c0a09","border": "1px solid rgba(251,191,36,0.3)","border_radius": "10px","padding": "12px 16px","box_shadow": "0 8px 24px rgba(0,0,0,0.6)","text_color": "#fef3c7"},
                "legend": {"position": "bottom","font_size": "12px","color": "#a8a29e","marker_shape": "square"},
                "slicer": {"background": "#292524","border": "1px solid rgba(251,191,36,0.15)","border_radius": "8px","active_background": "#f59e0b","active_color": "#0c0a09","font_size": "13px"},
                "dashboard_title": {"text": "Campaign Performance Dashboard","font_size": "28px","font_weight": "700","color": "#fef3c7","subtitle_text": "Track reach, conversions, and ROI across all campaigns","subtitle_color": "#a8a29e"},
                "table": {"header_background": "#292524","header_color": "#fbbf24","row_background": "#1c1917","alternate_row_background": "#231f1c","border": "1px solid rgba(251,191,36,0.08)","row_hover_background": "rgba(245,158,11,0.06)","font_size": "13px","color": "#d6d3d1","border_radius": "10px"},
            }

        # ===================================================================
        # LOGISTICS THEME  — slate blue & emerald
        # ===================================================================
        elif is_logistics:
            theme = {
                "theme_name": "Operations Hub",
                "domain": "Logistics & Supply Chain Analytics",
                "canvas": {"background_color": "#f8fafc","page_background": "#ffffff","grid_gap": "20px","border_radius_page": "0px","padding": "28px"},
                "typography": {"font_family": "'IBM Plex Sans', 'Inter', sans-serif","dashboard_title_font_size": "26px","dashboard_title_color": "#0f172a","kpi_value_font_size": "34px","kpi_value_color": "#059669","kpi_label_color": "#64748b","body_color": "#334155","axis_label_color": "#6b7280","data_label_color": "#1f2937"},
                "kpi_card": {"background": "#ffffff","border": "1px solid #d1fae5","border_radius": "14px","padding": "22px 26px","box_shadow": "0 2px 16px rgba(5,150,105,0.08)","accent_bar_color": "#10b981","icon_color": "#059669"},
                "chart_panel": {"background": "#ffffff","border": "1px solid #e2e8f0","border_radius": "14px","padding": "22px","box_shadow": "0 2px 12px rgba(0,0,0,0.05)"},
                "chart_colors": {"primary_palette": ["#059669","#0284c7","#7c3aed","#ea580c","#d97706","#dc2626"],"line_chart_color": "#10b981","bar_chart_color": "#059669","pie_chart_colors": ["#10b981","#0284c7","#7c3aed","#ea580c","#d97706","#dc2626"],"positive_color": "#10b981","negative_color": "#ef4444"},
                "axes_and_gridlines": {"gridline_color": "rgba(0,0,0,0.04)","gridline_style": "solid","show_y_gridlines": True,"show_x_gridlines": False,"axis_line_color": "#e2e8f0","axis_tick_color": "#9ca3af"},
                "data_labels": {"show_on_bars": True,"show_on_pie": True,"font_size": "11px","color": "#334155","position": "outside"},
                "tooltip": {"background": "#ffffff","border": "1px solid #d1fae5","border_radius": "10px","padding": "12px 16px","box_shadow": "0 4px 20px rgba(0,0,0,0.1)","text_color": "#111827"},
                "legend": {"position": "bottom","font_size": "12px","color": "#6b7280","marker_shape": "circle"},
                "slicer": {"background": "#f0fdf4","border": "1px solid #bbf7d0","border_radius": "8px","active_background": "#10b981","active_color": "#ffffff","font_size": "13px"},
                "dashboard_title": {"text": "Supply Chain Operations Dashboard","font_size": "26px","font_weight": "700","color": "#0f172a","subtitle_text": "Shipment tracking, fulfillment rates, and delivery performance","subtitle_color": "#64748b"},
                "table": {"header_background": "#f0fdf4","header_color": "#065f46","row_background": "#ffffff","alternate_row_background": "#f8fffe","border": "1px solid #d1fae5","row_hover_background": "rgba(16,185,129,0.04)","font_size": "13px","color": "#334155","border_radius": "10px"},
            }

        # ===================================================================
        # DEFAULT GENERAL THEME  — clean indigo & slate
        # ===================================================================
        else:
            theme = {
                "theme_name": "Insight Blue",
                "domain": "General Analytics",
                "canvas": {"background_color": "#f1f5f9","page_background": "#ffffff","grid_gap": "20px","border_radius_page": "0px","padding": "28px"},
                "typography": {"font_family": "'Inter', 'Segoe UI', sans-serif","dashboard_title_font_size": "26px","dashboard_title_color": "#1e293b","kpi_value_font_size": "34px","kpi_value_color": "#2563eb","kpi_label_color": "#64748b","body_color": "#334155","axis_label_color": "#6b7280","data_label_color": "#1f2937"},
                "kpi_card": {"background": "#ffffff","border": "1px solid #e0e7ff","border_radius": "14px","padding": "22px 26px","box_shadow": "0 2px 16px rgba(37,99,235,0.08)","accent_bar_color": "#2563eb","icon_color": "#2563eb"},
                "chart_panel": {"background": "#ffffff","border": "1px solid #e2e8f0","border_radius": "14px","padding": "22px","box_shadow": "0 2px 12px rgba(0,0,0,0.06)"},
                "chart_colors": {"primary_palette": ["#2563eb","#7c3aed","#0d9488","#ea580c","#d97706","#dc2626"],"line_chart_color": "#2563eb","bar_chart_color": "#2563eb","pie_chart_colors": ["#2563eb","#7c3aed","#0d9488","#ea580c","#d97706","#dc2626"],"positive_color": "#10b981","negative_color": "#ef4444"},
                "axes_and_gridlines": {"gridline_color": "rgba(0,0,0,0.05)","gridline_style": "solid","show_y_gridlines": True,"show_x_gridlines": False,"axis_line_color": "#e2e8f0","axis_tick_color": "#9ca3af"},
                "data_labels": {"show_on_bars": True,"show_on_pie": True,"font_size": "11px","color": "#334155","position": "outside"},
                "tooltip": {"background": "#ffffff","border": "1px solid #e0e7ff","border_radius": "10px","padding": "12px 16px","box_shadow": "0 4px 20px rgba(0,0,0,0.1)","text_color": "#111827"},
                "legend": {"position": "bottom","font_size": "12px","color": "#6b7280","marker_shape": "circle"},
                "slicer": {"background": "#f1f5f9","border": "1px solid #e0e7ff","border_radius": "8px","active_background": "#2563eb","active_color": "#ffffff","font_size": "13px"},
                "dashboard_title": {"text": "Insight Analytics Dashboard","font_size": "26px","font_weight": "700","color": "#1e293b","subtitle_text": "Explore trends, patterns, and data-driven insights","subtitle_color": "#64748b"},
                "table": {"header_background": "#eff6ff","header_color": "#1e40af","row_background": "#ffffff","alternate_row_background": "#f8fafc","border": "1px solid #e0e7ff","row_hover_background": "rgba(37,99,235,0.04)","font_size": "13px","color": "#334155","border_radius": "10px"},
            }

        return theme

    def recommend(self) -> Dict[str, Any]:
        """
        Execute the full recommendations pipeline and return a consolidated output
        that includes KPIs, charts, layout, questions, insights, and a complete design theme.
        """
        kpis    = self.recommend_kpis()
        charts  = self.recommend_charts()
        layout  = self.recommend_layout(kpis, charts)
        questions = self.generate_questions()
        insights  = self.generate_insights()
        theme     = self.recommend_theme()

        return {
            "kpis":      kpis,
            "charts":    charts,
            "layout":    layout,
            "questions": questions,
            "insights":  insights,
            "theme":     theme,
        }
