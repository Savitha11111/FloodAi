"""
Modern UI Components for FloodScope AI
Clean, professional styling inspired by leading tech companies
"""

import streamlit as st

def apply_modern_styling():
    """Apply modern, clean styling to the application"""
    
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display: none;}
    div[data-testid="stToolbar"] {visibility: hidden;}
    div[data-testid="stDecoration"] {visibility: hidden;}
    
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 16px;
        margin-bottom: 2rem;
        color: white;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
    }
    
    .main-title {
        font-size: 2.8rem;
        font-weight: 700;
        margin: 0;
        letter-spacing: -0.02em;
    }
    
    .main-subtitle {
        font-size: 1.2rem;
        opacity: 0.9;
        margin: 0.5rem 0 0 0;
        font-weight: 400;
    }
    
    .clean-card {
        background: white;
        border-radius: 16px;
        padding: 2rem;
        margin: 1rem 0;
        box-shadow: 0 4px 24px rgba(0,0,0,0.06);
        border: 1px solid #f0f0f0;
        transition: all 0.3s ease;
    }
    
    .clean-card:hover {
        box-shadow: 0 8px 40px rgba(0,0,0,0.1);
        transform: translateY(-4px);
    }
    
    .metric-card {
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
        border: 1px solid #e2e8f0;
    }
    
    .status-high { 
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
        color: white; padding: 0.5rem 1rem; border-radius: 8px; font-weight: 600;
    }
    .status-moderate { 
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
        color: white; padding: 0.5rem 1rem; border-radius: 8px; font-weight: 600;
    }
    .status-low { 
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white; padding: 0.5rem 1rem; border-radius: 8px; font-weight: 600;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.75rem 2rem;
        border-radius: 12px;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 16px rgba(102, 126, 234, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 24px rgba(102, 126, 234, 0.4);
    }
    
    .quick-action {
        background: white;
        border: 2px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.2rem;
        text-align: center;
        transition: all 0.3s ease;
        cursor: pointer;
    }
    
    .quick-action:hover {
        border-color: #667eea;
        background: #f8fafc;
        transform: translateY(-2px);
    }
    
    .section-title {
        font-size: 1.5rem;
        font-weight: 600;
        color: #1e293b;
        margin: 2rem 0 1rem 0;
    }
    
    .info-box {
        background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
        border: 1px solid #0ea5e9;
        border-radius: 12px;
        padding: 1.5rem;
        color: #0c4a6e;
        margin: 1rem 0;
    }
    
    .warning-box {
        background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
        border: 1px solid #f59e0b;
        border-radius: 12px;
        padding: 1.5rem;
        color: #92400e;
        margin: 1rem 0;
    }
    
    .success-box {
        background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
        border: 1px solid #10b981;
        border-radius: 12px;
        padding: 1.5rem;
        color: #065f46;
        margin: 1rem 0;
    }
    
    .nav-tabs {
        display: flex;
        background: white;
        border-radius: 12px;
        padding: 0.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 12px rgba(0,0,0,0.08);
    }
    
    .nav-tab {
        flex: 1;
        text-align: center;
        padding: 0.75rem;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.3s ease;
        font-weight: 500;
    }
    
    .nav-tab.active {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

def create_header():
    """Create modern header"""
    st.markdown("""
    <div class="main-header">
        <h1 class="main-title">FloodScope AI</h1>
        <p class="main-subtitle">Advanced flood detection and monitoring system</p>
    </div>
    """, unsafe_allow_html=True)

def create_clean_metrics(col1, col2, col3, col4):
    """Create clean metric display"""
    with col1:
        st.markdown("""
        <div class="metric-card">
            <div style="font-size: 2rem; font-weight: 700; color: #1e293b;">127</div>
            <div style="font-size: 0.9rem; color: #64748b; margin-top: 0.5rem;">Locations Monitored</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
            <div style="font-size: 2rem; font-weight: 700; color: #1e293b;">99.2%</div>
            <div style="font-size: 0.9rem; color: #64748b; margin-top: 0.5rem;">Detection Accuracy</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card">
            <div style="font-size: 2rem; font-weight: 700; color: #1e293b;">24/7</div>
            <div style="font-size: 0.9rem; color: #64748b; margin-top: 0.5rem;">Real-time Monitoring</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="metric-card">
            <div style="font-size: 2rem; font-weight: 700; color: #1e293b;">< 5min</div>
            <div style="font-size: 0.9rem; color: #64748b; margin-top: 0.5rem;">Analysis Time</div>
        </div>
        """, unsafe_allow_html=True)

def create_status_indicator(status, level):
    """Create status indicator"""
    return f'<span class="status-{level}">{status}</span>'

def create_info_box(message, type="info"):
    """Create styled info box"""
    box_class = f"{type}-box"
    return f'<div class="{box_class}">{message}</div>'