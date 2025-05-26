"""
Advanced Dashboard Builder with Power BI-like Features
Provides interactive dashboard creation, advanced visualizations, and business intelligence
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json
import io
import base64


class ChartType(Enum):
    """Available chart types"""
    BAR = "bar"
    LINE = "line"
    PIE = "pie"
    SCATTER = "scatter"
    HISTOGRAM = "histogram"
    BOX = "box"
    HEATMAP = "heatmap"
    WATERFALL = "waterfall"
    FUNNEL = "funnel"
    GAUGE = "gauge"
    TREEMAP = "treemap"
    SUNBURST = "sunburst"
    SANKEY = "sankey"
    CANDLESTICK = "candlestick"
    RADAR = "radar"


@dataclass
class ChartConfig:
    """Chart configuration"""
    chart_type: ChartType
    title: str
    x_column: Optional[str] = None
    y_column: Optional[str] = None
    color_column: Optional[str] = None
    size_column: Optional[str] = None
    facet_column: Optional[str] = None
    aggregation: Optional[str] = None
    filters: Dict[str, Any] = None
    styling: Dict[str, Any] = None


@dataclass
class DashboardLayout:
    """Dashboard layout configuration"""
    title: str
    description: str
    layout_type: str  # "grid", "tabs", "sidebar"
    charts: List[ChartConfig]
    filters: List[Dict[str, Any]]
    refresh_interval: Optional[int] = None


class AdvancedChartBuilder:
    """Build advanced charts with business intelligence features"""
    
    @staticmethod
    def create_waterfall_chart(df: pd.DataFrame, x_col: str, y_col: str, title: str = "Waterfall Chart") -> go.Figure:
        """Create waterfall chart for financial analysis"""
        fig = go.Figure(go.Waterfall(
            name="Waterfall",
            orientation="v",
            measure=["relative"] * (len(df) - 1) + ["total"],
            x=df[x_col].tolist(),
            textposition="outside",
            text=[f"{val:,.0f}" for val in df[y_col]],
            y=df[y_col].tolist(),
            connector={"line": {"color": "rgb(63, 63, 63)"}},
        ))
        
        fig.update_layout(
            title=title,
            showlegend=True,
            height=500
        )
        
        return fig
    
    @staticmethod
    def create_funnel_chart(df: pd.DataFrame, x_col: str, y_col: str, title: str = "Funnel Chart") -> go.Figure:
        """Create funnel chart for conversion analysis"""
        fig = go.Figure(go.Funnel(
            y=df[x_col],
            x=df[y_col],
            textinfo="value+percent initial",
            textposition="inside",
            opacity=0.65,
            marker={"color": ["deepskyblue", "lightsalmon", "tan", "teal", "silver"],
                   "line": {"width": [4, 2, 2, 3, 1, 1], "color": ["wheat", "wheat", "blue", "wheat", "wheat"]}},
            connector={"line": {"color": "royalblue", "dash": "dot", "width": 3}}
        ))
        
        fig.update_layout(title=title, height=500)
        return fig
    
    @staticmethod
    def create_gauge_chart(value: float, title: str = "Gauge Chart", max_value: float = 100) -> go.Figure:
        """Create gauge chart for KPI display"""
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=value,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': title},
            delta={'reference': max_value * 0.8},
            gauge={
                'axis': {'range': [None, max_value]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, max_value * 0.5], 'color': "lightgray"},
                    {'range': [max_value * 0.5, max_value * 0.8], 'color': "gray"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': max_value * 0.9
                }
            }
        ))
        
        fig.update_layout(height=400)
        return fig
    
    @staticmethod
    def create_treemap_chart(df: pd.DataFrame, values_col: str, labels_col: str, 
                           parent_col: Optional[str] = None, title: str = "Treemap Chart") -> go.Figure:
        """Create treemap for hierarchical data"""
        if parent_col:
            fig = go.Figure(go.Treemap(
                labels=df[labels_col],
                values=df[values_col],
                parents=df[parent_col],
                textinfo="label+value+percent parent",
                textfont_size=12,
                marker_colorscale='Blues'
            ))
        else:
            fig = go.Figure(go.Treemap(
                labels=df[labels_col],
                values=df[values_col],
                textinfo="label+value+percent root",
                textfont_size=12,
                marker_colorscale='Blues'
            ))
        
        fig.update_layout(title=title, height=500)
        return fig
    
    @staticmethod
    def create_sunburst_chart(df: pd.DataFrame, values_col: str, labels_col: str, 
                            parent_col: str, title: str = "Sunburst Chart") -> go.Figure:
        """Create sunburst chart for hierarchical data"""
        fig = go.Figure(go.Sunburst(
            labels=df[labels_col],
            values=df[values_col],
            parents=df[parent_col],
            branchvalues="total",
        ))
        
        fig.update_layout(title=title, height=500)
        return fig
    
    @staticmethod
    def create_heatmap_correlation(df: pd.DataFrame, title: str = "Correlation Heatmap") -> go.Figure:
        """Create correlation heatmap"""
        numeric_df = df.select_dtypes(include=[np.number])
        correlation_matrix = numeric_df.corr()
        
        fig = go.Figure(data=go.Heatmap(
            z=correlation_matrix.values,
            x=correlation_matrix.columns,
            y=correlation_matrix.columns,
            colorscale='RdBu',
            zmid=0,
            text=correlation_matrix.round(2).values,
            texttemplate="%{text}",
            textfont={"size": 10},
            hoverongaps=False
        ))
        
        fig.update_layout(
            title=title,
            height=500,
            xaxis_title="Variables",
            yaxis_title="Variables"
        )
        
        return fig
    
    @staticmethod
    def create_candlestick_chart(df: pd.DataFrame, date_col: str, open_col: str, 
                               high_col: str, low_col: str, close_col: str, 
                               title: str = "Candlestick Chart") -> go.Figure:
        """Create candlestick chart for financial data"""
        fig = go.Figure(data=go.Candlestick(
            x=df[date_col],
            open=df[open_col],
            high=df[high_col],
            low=df[low_col],
            close=df[close_col]
        ))
        
        fig.update_layout(
            title=title,
            yaxis_title="Price",
            xaxis_title="Date",
            height=500
        )
        
        return fig
    
    @staticmethod
    def create_radar_chart(df: pd.DataFrame, categories_col: str, values_col: str, 
                         group_col: Optional[str] = None, title: str = "Radar Chart") -> go.Figure:
        """Create radar chart for multi-dimensional analysis"""
        fig = go.Figure()
        
        if group_col:
            for group in df[group_col].unique():
                group_data = df[df[group_col] == group]
                fig.add_trace(go.Scatterpolar(
                    r=group_data[values_col],
                    theta=group_data[categories_col],
                    fill='toself',
                    name=str(group)
                ))
        else:
            fig.add_trace(go.Scatterpolar(
                r=df[values_col],
                theta=df[categories_col],
                fill='toself',
                name='Values'
            ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, df[values_col].max()]
                )),
            showlegend=True,
            title=title,
            height=500
        )
        
        return fig


class DashboardBuilder:
    """Main dashboard builder class"""
    
    def __init__(self):
        self.chart_builder = AdvancedChartBuilder()
        self.current_dashboard = None
    
    def create_dashboard_interface(self):
        """Create the dashboard builder interface"""
        st.header("🎯 Advanced Dashboard Builder")
        
        # Dashboard configuration
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("Dashboard Settings")
            dashboard_title = st.text_input("Dashboard Title", "Business Intelligence Dashboard")
            dashboard_desc = st.text_area("Description", "Advanced analytics dashboard")
            layout_type = st.selectbox("Layout Type", ["Grid", "Tabs", "Sidebar"])
            
            st.subheader("Data Source")
            if 'query_results' in st.session_state and st.session_state.query_results is not None:
                df = st.session_state.query_results
                st.success(f"Data loaded: {len(df)} rows, {len(df.columns)} columns")
                
                # Show data preview
                with st.expander("Data Preview"):
                    st.dataframe(df.head())
                
                # Chart builder
                self._create_chart_builder(df)
                
            else:
                st.info("Execute a query first to load data for dashboard creation")
        
        with col2:
            st.subheader("Dashboard Preview")
            if 'dashboard_charts' in st.session_state:
                self._render_dashboard_preview()
            else:
                st.info("Add charts to see dashboard preview")
    
    def _create_chart_builder(self, df: pd.DataFrame):
        """Create chart builder interface"""
        st.subheader("Chart Builder")
        
        # Chart configuration
        chart_type = st.selectbox(
            "Chart Type",
            options=[ct.value for ct in ChartType],
            format_func=lambda x: x.replace('_', ' ').title()
        )
        
        chart_title = st.text_input("Chart Title", f"Chart {len(st.session_state.get('dashboard_charts', [])) + 1}")
        
        # Column selection based on chart type
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        date_cols = df.select_dtypes(include=['datetime64']).columns.tolist()
        all_cols = df.columns.tolist()
        
        # Dynamic column selection based on chart type
        x_col, y_col, color_col, size_col = self._get_column_selectors(
            chart_type, numeric_cols, categorical_cols, date_cols, all_cols
        )
        
        # Advanced options
        with st.expander("Advanced Options"):
            aggregation = st.selectbox("Aggregation", ["None", "Sum", "Mean", "Count", "Max", "Min"])
            show_trend = st.checkbox("Show Trend Line")
            custom_colors = st.checkbox("Custom Color Scheme")
            
            if custom_colors:
                color_scheme = st.selectbox("Color Scheme", 
                    ["Blues", "Reds", "Greens", "Viridis", "Plasma", "Inferno"])
        
        # Add chart button
        if st.button("Add Chart to Dashboard"):
            self._add_chart_to_dashboard(
                chart_type, chart_title, df, x_col, y_col, color_col, size_col, aggregation
            )
    
    def _get_column_selectors(self, chart_type: str, numeric_cols: List[str], 
                            categorical_cols: List[str], date_cols: List[str], 
                            all_cols: List[str]) -> Tuple[str, str, str, str]:
        """Get appropriate column selectors based on chart type"""
        
        if chart_type in ['bar', 'line', 'scatter']:
            x_col = st.selectbox("X-axis", all_cols)
            y_col = st.selectbox("Y-axis", numeric_cols)
            color_col = st.selectbox("Color by", [None] + categorical_cols)
            size_col = st.selectbox("Size by", [None] + numeric_cols) if chart_type == 'scatter' else None
            
        elif chart_type == 'pie':
            x_col = st.selectbox("Labels", categorical_cols)
            y_col = st.selectbox("Values", numeric_cols)
            color_col = None
            size_col = None
            
        elif chart_type == 'histogram':
            x_col = st.selectbox("Column", numeric_cols)
            y_col = None
            color_col = st.selectbox("Color by", [None] + categorical_cols)
            size_col = None
            
        elif chart_type == 'heatmap':
            x_col = st.selectbox("X-axis", all_cols)
            y_col = st.selectbox("Y-axis", all_cols)
            color_col = st.selectbox("Values", numeric_cols)
            size_col = None
            
        elif chart_type == 'gauge':
            x_col = None
            y_col = st.selectbox("Value", numeric_cols)
            color_col = None
            size_col = None
            
        else:
            x_col = st.selectbox("X-axis", all_cols)
            y_col = st.selectbox("Y-axis", numeric_cols)
            color_col = st.selectbox("Color by", [None] + categorical_cols)
            size_col = None
        
        return x_col, y_col, color_col, size_col
    
    def _add_chart_to_dashboard(self, chart_type: str, title: str, df: pd.DataFrame,
                              x_col: str, y_col: str, color_col: str, size_col: str, aggregation: str):
        """Add chart to dashboard"""
        if 'dashboard_charts' not in st.session_state:
            st.session_state.dashboard_charts = []
        
        # Create the chart
        chart = self._create_chart(chart_type, title, df, x_col, y_col, color_col, size_col, aggregation)
        
        if chart:
            chart_config = {
                'type': chart_type,
                'title': title,
                'chart': chart,
                'config': {
                    'x_col': x_col,
                    'y_col': y_col,
                    'color_col': color_col,
                    'size_col': size_col,
                    'aggregation': aggregation
                }
            }
            
            st.session_state.dashboard_charts.append(chart_config)
            st.success(f"Added {title} to dashboard!")
    
    def _create_chart(self, chart_type: str, title: str, df: pd.DataFrame,
                     x_col: str, y_col: str, color_col: str, size_col: str, aggregation: str):
        """Create chart based on configuration"""
        
        try:
            # Apply aggregation if specified
            if aggregation != "None" and x_col and y_col:
                if aggregation == "Sum":
                    df = df.groupby(x_col)[y_col].sum().reset_index()
                elif aggregation == "Mean":
                    df = df.groupby(x_col)[y_col].mean().reset_index()
                elif aggregation == "Count":
                    df = df.groupby(x_col)[y_col].count().reset_index()
                elif aggregation == "Max":
                    df = df.groupby(x_col)[y_col].max().reset_index()
                elif aggregation == "Min":
                    df = df.groupby(x_col)[y_col].min().reset_index()
            
            # Create chart based on type
            if chart_type == 'bar':
                return px.bar(df, x=x_col, y=y_col, color=color_col, title=title)
            elif chart_type == 'line':
                return px.line(df, x=x_col, y=y_col, color=color_col, title=title)
            elif chart_type == 'scatter':
                return px.scatter(df, x=x_col, y=y_col, color=color_col, size=size_col, title=title)
            elif chart_type == 'pie':
                return px.pie(df, names=x_col, values=y_col, title=title)
            elif chart_type == 'histogram':
                return px.histogram(df, x=x_col, color=color_col, title=title)
            elif chart_type == 'box':
                return px.box(df, x=x_col, y=y_col, color=color_col, title=title)
            elif chart_type == 'heatmap':
                return self.chart_builder.create_heatmap_correlation(df, title)
            elif chart_type == 'gauge':
                value = df[y_col].iloc[0] if len(df) > 0 else 0
                return self.chart_builder.create_gauge_chart(value, title)
            elif chart_type == 'treemap':
                return self.chart_builder.create_treemap_chart(df, y_col, x_col, title=title)
            elif chart_type == 'waterfall':
                return self.chart_builder.create_waterfall_chart(df, x_col, y_col, title)
            elif chart_type == 'funnel':
                return self.chart_builder.create_funnel_chart(df, x_col, y_col, title)
            else:
                return px.bar(df, x=x_col, y=y_col, title=title)
                
        except Exception as e:
            st.error(f"Error creating chart: {str(e)}")
            return None
    
    def _render_dashboard_preview(self):
        """Render dashboard preview"""
        charts = st.session_state.get('dashboard_charts', [])
        
        if not charts:
            st.info("No charts added yet")
            return
        
        # Dashboard controls
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button("Clear Dashboard"):
                st.session_state.dashboard_charts = []
                st.experimental_rerun()
        
        with col2:
            if st.button("Export Dashboard"):
                self._export_dashboard()
        
        with col3:
            layout_cols = st.selectbox("Columns", [1, 2, 3], index=1)
        
        # Render charts in grid layout
        for i in range(0, len(charts), layout_cols):
            cols = st.columns(layout_cols)
            for j in range(layout_cols):
                if i + j < len(charts):
                    with cols[j]:
                        chart_config = charts[i + j]
                        st.plotly_chart(chart_config['chart'], use_container_width=True)
                        
                        # Chart controls
                        if st.button(f"Remove", key=f"remove_{i+j}"):
                            st.session_state.dashboard_charts.pop(i + j)
                            st.experimental_rerun()
    
    def _export_dashboard(self):
        """Export dashboard configuration"""
        charts = st.session_state.get('dashboard_charts', [])
        
        if not charts:
            st.warning("No charts to export")
            return
        
        # Create export data
        export_data = {
            'dashboard_title': 'Business Intelligence Dashboard',
            'charts': []
        }
        
        for chart in charts:
            export_data['charts'].append({
                'type': chart['type'],
                'title': chart['title'],
                'config': chart['config']
            })
        
        # Convert to JSON
        json_str = json.dumps(export_data, indent=2)
        
        # Create download link
        b64 = base64.b64encode(json_str.encode()).decode()
        href = f'<a href="data:application/json;base64,{b64}" download="dashboard_config.json">Download Dashboard Configuration</a>'
        st.markdown(href, unsafe_allow_html=True)
        
        st.success("Dashboard configuration ready for download!")


# Factory function
def create_dashboard_builder() -> DashboardBuilder:
    """Create dashboard builder instance"""
    return DashboardBuilder()
