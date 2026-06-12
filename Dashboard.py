import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objs as go
import plotly.express as px
from datetime import datetime, timedelta
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
import os
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures, StandardScaler
from sklearn.pipeline import make_pipeline
import pytz
import warnings
warnings.filterwarnings('ignore')

# Configuration de la page
st.set_page_config(
    page_title="🚀 SpaceX & NewSpace Tracker - Scores Boursiers",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuration des fuseaux horaires
USER_TIMEZONE = pytz.timezone('Europe/Paris')
US_TIMEZONE = pytz.timezone('America/New_York')
UTC_TIMEZONE = pytz.UTC

# Style CSS personnalisé - CORRIGÉ (texte sombre sur fond clair)
st.markdown("""
<style>
    /* Style général */
    .stApp {
        background-color: #f5f5f5;
    }
    
    .main-header {
        font-size: 2.5rem;
        color: #1a1a2e;
        text-align: center;
        margin-bottom: 2rem;
        font-family: 'Montserrat', sans-serif;
        background: linear-gradient(135deg, #1a1a2e 0%, #005288 50%, #1a1a2e 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        padding: 20px;
    }
    
    /* Cartes de score avec texte sombre */
    .score-card {
        background: linear-gradient(135deg, #e8f4f8 0%, #d1e7f0 100%);
        padding: 1rem;
        border-radius: 1rem;
        text-align: center;
        color: #1a1a2e;
        margin: 0.5rem 0;
        border: 1px solid #005288;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    .score-card * {
        color: #1a1a2e !important;
    }
    
    .score-excellent { 
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
        border-left: 5px solid #28a745;
    }
    .score-good { 
        background: linear-gradient(135deg, #d1ecf1 0%, #bee5eb 100%);
        border-left: 5px solid #17a2b8;
    }
    .score-average { 
        background: linear-gradient(135deg, #fff3cd 0%, #ffeeba 100%);
        border-left: 5px solid #ffc107;
    }
    .score-poor { 
        background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
        border-left: 5px solid #dc3545;
    }
    
    /* Cartes métriques */
    .metric-card {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border: 1px solid #dee2e6;
        margin: 5px 0;
    }
    
    .metric-card b {
        color: #005288;
    }
    
    .metric-card span {
        color: #1a1a2e;
    }
    
    /* Badges */
    .spacex-badge {
        background-color: #005288;
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 1rem;
        font-weight: bold;
        display: inline-block;
    }
    
    /* Timezone badge */
    .timezone-badge {
        background-color: #e3f2fd;
        border-left: 4px solid #005288;
        padding: 0.5rem 1rem;
        margin: 1rem 0;
        font-size: 0.9rem;
        color: #1a1a2e;
        border-radius: 0.5rem;
    }
    
    /* Alertes */
    .stAlert {
        background-color: #f8f9fa;
        color: #1a1a2e;
    }
    
    /* Dataframe */
    .stDataFrame {
        background-color: white;
    }
    
    /* Boutons */
    .stButton>button {
        width: 100%;
        background-color: #005288;
        color: white;
        border: none;
        border-radius: 0.5rem;
        padding: 0.5rem;
        font-weight: bold;
    }
    
    .stButton>button:hover {
        background-color: #003d66;
        color: white;
    }
    
    /* Sidebar */
    .css-1d391kg, .css-12oz5g7 {
        background-color: #1a1a2e;
    }
    
    /* Texte dans les expanders */
    .streamlit-expanderHeader {
        color: #005288 !important;
        font-weight: bold;
    }
    
    /* Métriques Streamlit */
    .stMetric {
        background-color: white;
        padding: 10px;
        border-radius: 0.5rem;
        border: 1px solid #dee2e6;
    }
    
    .stMetric label {
        color: #005288 !important;
    }
    
    .stMetric div {
        color: #1a1a2e !important;
    }
    
    /* Messages info/success/warning/error */
    .stInfo, .stSuccess, .stWarning, .stError {
        background-color: #f8f9fa;
        border-radius: 0.5rem;
    }
    
    /* Tableaux personnalisés dans les cartes */
    .score-card table, .score-card td, .score-card th {
        color: #1a1a2e !important;
        background: transparent !important;
    }
    
    /* Selectbox et inputs */
    .stSelectbox label, .stSlider label, .stCheckbox label {
        color: #1a1a2e !important;
    }
    
    /* Footer */
    .footer-text {
        text-align: center;
        color: #6c757d;
        font-size: 0.8rem;
        padding: 20px;
    }
</style>
""", unsafe_allow_html=True)

# Initialisation des variables de session
if 'price_alerts' not in st.session_state:
    st.session_state.price_alerts = []

if 'portfolio' not in st.session_state:
    st.session_state.portfolio = {}

if 'watchlist' not in st.session_state:
    st.session_state.watchlist = [
        'RKLB', 'ASTS', 'RDW', 'PL', 'SPCE', 'MNTS', 'BKSY', 'SATL', 'ASTR', 'LLAP',
        'GSAT', 'IRDM', 'MAXR', 'TSLA', 'LMT', 'NOC', 'BA', 'RTX', 'GD', 'LHX',
        'HON', 'GE', 'TDY', 'HEI', 'SATS'
    ]

# Base de données des entreprises spatiales
SPACE_COMPANIES = {
    'RKLB': {'name': 'Rocket Lab USA', 'sector': 'Lanceurs', 'focus': 'Neutron rocket, Electron', 'musk_related': False, 'revenue_growth': 0.65},
    'ASTS': {'name': 'AST SpaceMobile', 'sector': 'Satellites', 'focus': 'Réseau 5G spatial', 'musk_related': False, 'revenue_growth': 0},
    'RDW': {'name': 'Redwire', 'sector': 'Infrastructure', 'focus': 'Manufacturing spatial', 'musk_related': False, 'revenue_growth': 0.45},
    'PL': {'name': 'Planet Labs', 'sector': 'Imagerie', 'focus': 'Earth observation', 'musk_related': False, 'revenue_growth': 0.15},
    'SPCE': {'name': 'Virgin Galactic', 'sector': 'Tourisme', 'focus': 'Vols suborbitaux', 'musk_related': False, 'revenue_growth': -0.20},
    'MNTS': {'name': 'Momentus', 'sector': 'Logistique', 'focus': 'Transfert orbital', 'musk_related': False, 'revenue_growth': 0},
    'BKSY': {'name': 'BlackSky', 'sector': 'Imagerie', 'focus': 'Surveillance', 'musk_related': False, 'revenue_growth': 0.30},
    'SATL': {'name': 'Satellogic', 'sector': 'Imagerie', 'focus': 'Hyper-spectrale', 'musk_related': False, 'revenue_growth': 0.25},
    'ASTR': {'name': 'Astra Space', 'sector': 'Lanceurs', 'focus': 'Rocket 4', 'musk_related': False, 'revenue_growth': -0.50},
    'LLAP': {'name': 'Terran Orbital', 'sector': 'Satellites', 'focus': 'SmallSats', 'musk_related': False, 'revenue_growth': 0.80},
    'GSAT': {'name': 'Globalstar', 'sector': 'Communications', 'focus': 'IoT satellite', 'musk_related': True, 'revenue_growth': 0.10},
    'IRDM': {'name': 'Iridium', 'sector': 'Communications', 'focus': 'Satellite voice/data', 'musk_related': False, 'revenue_growth': 0.08},
    'MAXR': {'name': 'Maxar Technologies', 'sector': 'Imagerie', 'focus': 'Satellite imaging', 'musk_related': False, 'revenue_growth': 0.05},
    'TSLA': {'name': 'Tesla Inc.', 'sector': 'Électromobilité', 'focus': 'EV, batteries', 'musk_related': True, 'revenue_growth': 0.20},
    'LMT': {'name': 'Lockheed Martin', 'sector': 'Défense', 'focus': 'Aérospatial défense', 'musk_related': False, 'revenue_growth': 0.05},
    'BA': {'name': 'Boeing', 'sector': 'Aérospatial', 'focus': 'Starliner, SLS', 'musk_related': False, 'revenue_growth': 0.10},
}

# ============================================================================
# FONCTIONS DE CHARGEMENT DES DONNÉES
# ============================================================================

@st.cache_data(ttl=300, show_spinner=False)
def load_stock_data_cached(symbol, period, interval):
    """Charge uniquement les données sérialisables (DataFrame et dict)"""
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period, interval=interval)
        info = ticker.info
        
        if not hist.empty:
            if hist.index.tz is None:
                hist.index = hist.index.tz_localize('UTC').tz_convert(USER_TIMEZONE)
            else:
                hist.index = hist.index.tz_convert(USER_TIMEZONE)
            hist = hist.reset_index()
        
        safe_info = {
            'marketCap': info.get('marketCap', 0),
            'trailingPE': info.get('trailingPE', 0),
            'forwardPE': info.get('forwardPE', 0),
            'profitMargins': info.get('profitMargins', 0),
            'debtToEquity': info.get('debtToEquity', 0),
            'operatingCashflow': info.get('operatingCashflow', 0),
            'returnOnEquity': info.get('returnOnEquity', 0),
            'dividendYield': info.get('dividendYield', 0),
            'beta': info.get('beta', 1),
            'targetMeanPrice': info.get('targetMeanPrice', 0),
            'recommendationKey': info.get('recommendationKey', ''),
            'numberOfAnalystOpinions': info.get('numberOfAnalystOpinions', 0),
            'currentPrice': info.get('currentPrice', 0),
            'sector': info.get('sector', ''),
            'longName': info.get('longName', ''),
        }
        
        return hist, safe_info
    except Exception as e:
        return pd.DataFrame(), {}

# ============================================================================
# FONCTIONS DE CALCUL DES SCORES
# ============================================================================

def calculate_financial_score_from_info(info):
    score = 50
    market_cap = info.get('marketCap', 0)
    if market_cap > 1e12:
        score += 15
    elif market_cap > 1e11:
        score += 10
    elif market_cap > 1e10:
        score += 5
    elif market_cap > 1e9:
        score += 2
    
    pe_ratio = info.get('trailingPE', 0)
    if pe_ratio and pe_ratio > 0:
        if pe_ratio < 15:
            score += 10
        elif pe_ratio < 25:
            score += 5
        elif pe_ratio > 50:
            score -= 5
    else:
        score -= 5
    
    profit_margins = info.get('profitMargins', 0)
    if profit_margins:
        if profit_margins > 0.2:
            score += 10
        elif profit_margins > 0.1:
            score += 5
        elif profit_margins < 0:
            score -= 5
    
    debt_to_equity = info.get('debtToEquity', 0)
    if debt_to_equity:
        if debt_to_equity < 50:
            score += 10
        elif debt_to_equity < 100:
            score += 5
        elif debt_to_equity > 200:
            score -= 10
    
    return min(max(score, 0), 100)

def calculate_technical_score_from_hist(hist_df):
    if hist_df is None or hist_df.empty or len(hist_df) < 50:
        return 50
    
    score = 50
    close = hist_df['Close']
    
    if len(close) > 20:
        ma_20 = close.rolling(window=20).mean()
        if close.iloc[-1] > ma_20.iloc[-1]:
            score += 10
        else:
            score -= 5
    
    if len(close) > 50:
        ma_50 = close.rolling(window=50).mean()
        ma_20 = close.rolling(window=20).mean()
        if len(ma_20) > 0 and len(ma_50) > 0:
            if ma_20.iloc[-1] > ma_50.iloc[-1]:
                score += 10
            else:
                score -= 5
    
    if len(close) > 14:
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        if len(rsi) > 0 and not pd.isna(rsi.iloc[-1]):
            current_rsi = rsi.iloc[-1]
            if 30 <= current_rsi <= 70:
                score += 5
            elif current_rsi < 30:
                score += 15
            elif current_rsi > 70:
                score -= 10
    
    return min(max(score, 0), 100)

def calculate_momentum_score_from_hist(hist_df):
    if hist_df is None or hist_df.empty or len(hist_df) < 30:
        return 50
    
    score = 50
    close = hist_df['Close']
    
    if len(close) > 26:
        exp1 = close.ewm(span=12, adjust=False).mean()
        exp2 = close.ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=9, adjust=False).mean()
        
        if len(macd) > 0 and len(signal) > 0:
            if macd.iloc[-1] > signal.iloc[-1]:
                score += 10
            else:
                score -= 5
    
    return min(max(score, 0), 100)

def calculate_space_sector_score_from_info(info, symbol):
    score = 50
    company_data = SPACE_COMPANIES.get(symbol, {})
    
    if company_data.get('musk_related', False):
        score += 15
    
    sector = company_data.get('sector', '')
    if sector in ['Lanceurs', 'Satellites']:
        score += 10
    elif sector == 'Imagerie':
        score += 5
    
    has_gov_contracts = info.get('sector', '') in ['Aerospace', 'Defense']
    if has_gov_contracts:
        score += 10
    
    revenue_growth = company_data.get('revenue_growth', 0)
    if revenue_growth > 0.5:
        score += 10
    elif revenue_growth < -0.2:
        score -= 10
    
    return min(max(score, 0), 100)

def calculate_esg_score_from_info(info):
    score = 50
    sector = info.get('sector', '')
    if sector == 'Clean Energy':
        score += 15
    elif sector in ['Aerospace', 'Industrial']:
        score -= 5
    
    if info.get('dividendYield', 0) > 0:
        score += 5
    
    return min(max(score, 0), 100)

def calculate_volatility_risk_score_from_hist(hist_df):
    if hist_df is None or hist_df.empty or len(hist_df) < 20:
        return 50
    
    score = 70
    close = hist_df['Close']
    
    volatility = close.pct_change().std() * np.sqrt(252)
    
    if volatility > 0.8:
        score -= 30
    elif volatility > 0.6:
        score -= 20
    elif volatility > 0.4:
        score -= 10
    elif volatility < 0.2:
        score += 10
    
    return min(max(score, 0), 100)

def calculate_liquidity_score_from_hist(hist_df, info):
    if hist_df is None or hist_df.empty:
        return 50
    
    score = 50
    avg_volume = hist_df['Volume'].tail(20).mean()
    
    if avg_volume > 10_000_000:
        score += 20
    elif avg_volume > 5_000_000:
        score += 15
    elif avg_volume > 1_000_000:
        score += 10
    elif avg_volume > 500_000:
        score += 5
    elif avg_volume < 100_000:
        score -= 15
    
    return min(max(score, 0), 100)

def calculate_growth_potential_score_from_info(info, symbol):
    score = 50
    company_data = SPACE_COMPANIES.get(symbol, {})
    
    revenue_growth = company_data.get('revenue_growth', 0)
    if revenue_growth > 0.5:
        score += 20
    elif revenue_growth > 0.2:
        score += 15
    elif revenue_growth > 0:
        score += 10
    elif revenue_growth < 0:
        score -= 10
    
    market_cap = info.get('marketCap', 0)
    if market_cap < 500_000_000:
        score += 15
    elif market_cap < 2_000_000_000:
        score += 10
    elif market_cap > 100_000_000_000:
        score -= 10
    
    return min(max(score, 0), 100)

def calculate_analyst_consensus_score_from_info(info):
    score = 50
    
    target_mean = info.get('targetMeanPrice', 0)
    current_price = info.get('currentPrice', 0)
    
    if target_mean > 0 and current_price > 0:
        upside = (target_mean / current_price - 1) * 100
        if upside > 20:
            score += 15
        elif upside > 10:
            score += 10
        elif upside > 0:
            score += 5
        elif upside < -10:
            score -= 10
    
    recommendation = info.get('recommendationKey', '')
    rec_map = {'strong_buy': 20, 'buy': 15, 'hold': 0, 'sell': -10, 'strong_sell': -20}
    score += rec_map.get(recommendation, 0)
    
    return min(max(score, 0), 100)

def calculate_composite_score(scores, weights=None):
    if weights is None:
        weights = {
            'financial': 0.20, 'technical': 0.15, 'momentum': 0.10,
            'space_sector': 0.15, 'esg': 0.05, 'risk': 0.10,
            'liquidity': 0.05, 'growth': 0.15, 'analyst': 0.05
        }
    
    composite = 0
    for key, weight in weights.items():
        composite += scores.get(key, 50) * weight
    
    return composite

def get_score_grade(score):
    if score >= 85:
        return "EXCELLENT", "🌟", "score-excellent", "Forte opportunité d'achat"
    elif score >= 70:
        return "TRÈS BON", "📈", "score-good", "Potentiel de croissance élevé"
    elif score >= 55:
        return "BON", "✅", "score-average", "Performance solide"
    elif score >= 40:
        return "MOYEN", "⚠️", "score-poor", "À surveiller"
    else:
        return "FAIBLE", "🔻", "score-poor", "Risque élevé, éviter"

def format_currency(value):
    return f"${value:,.2f}" if value else "$0.00"

def format_percentage(value):
    return f"{value:+.1f}%" if value else "0%"

# ============================================================================
# INTERFACE PRINCIPALE
# ============================================================================

st.markdown("<h1 class='main-header'>🚀 SpaceX & NewSpace Tracker - Scores Boursiers Avancés</h1>", unsafe_allow_html=True)

# Bannière de fuseau horaire
current_time_paris = datetime.now(USER_TIMEZONE)
current_time_ny = datetime.now(US_TIMEZONE)

st.markdown(f"""
<div class='timezone-badge'>
    <b>🕐 Fuseaux horaires :</b><br>
    🇫🇷 Heure Paris : {current_time_paris.strftime('%H:%M:%S')}<br>
    🇺🇸 Heure Floride : {current_time_ny.strftime('%H:%M:%S')}
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("## 🚀 Navigation")
    
    menu = st.radio(
        "Choisir une section",
        ["🏆 Classement des scores",
         "📊 Scoreboard détaillé",
         "💼 Portefeuille & Scores",
         "📈 Analyse comparative",
         "🎯 Alertes scoring",
         "📤 Export scores"]
    )
    
    st.markdown("---")
    period = st.selectbox("Période technique", ["1mo", "3mo", "6mo", "1y"], index=1)
    interval = "1d"

# ============================================================================
# SECTION 1: CLASSEMENT DES SCORES
# ============================================================================

if menu == "🏆 Classement des scores":
    st.subheader("🏆 Classement général des actions spatiales")
    
    all_scores = []
    progress_bar = st.progress(0)
    
    for i, symbol in enumerate(st.session_state.watchlist):
        hist_df, info = load_stock_data_cached(symbol, period, interval)
        
        if not hist_df.empty:
            scores = {
                'financial': calculate_financial_score_from_info(info),
                'technical': calculate_technical_score_from_hist(hist_df),
                'momentum': calculate_momentum_score_from_hist(hist_df),
                'space_sector': calculate_space_sector_score_from_info(info, symbol),
                'esg': calculate_esg_score_from_info(info),
                'risk': calculate_volatility_risk_score_from_hist(hist_df),
                'liquidity': calculate_liquidity_score_from_hist(hist_df, info),
                'growth': calculate_growth_potential_score_from_info(info, symbol),
                'analyst': calculate_analyst_consensus_score_from_info(info)
            }
            
            composite = calculate_composite_score(scores)
            grade, icon, css_class, recommendation = get_score_grade(composite)
            current_price = hist_df['Close'].iloc[-1]
            perf_5d = ((hist_df['Close'].iloc[-1] / hist_df['Close'].iloc[-6]) - 1) * 100 if len(hist_df) > 5 else 0
            
            company_data = SPACE_COMPANIES.get(symbol, {})
            
            all_scores.append({
                'Symbole': symbol,
                'Entreprise': company_data.get('name', symbol),
                'Secteur': company_data.get('sector', 'N/A'),
                'Prix': format_currency(current_price),
                'Perf 5j': format_percentage(perf_5d),
                'Score': round(composite, 1),
                'Grade': grade,
                'Icone': icon,
                'Recommandation': recommendation
            })
        
        progress_bar.progress((i + 1) / len(st.session_state.watchlist))
    
    progress_bar.empty()
    
    if all_scores:
        df_scores = pd.DataFrame(all_scores)
        df_scores = df_scores.sort_values('Score', ascending=False)
        
        st.markdown("### 🔥 Top 5 des meilleurs scores")
        
        top5 = df_scores.head(5)
        
        for idx, row in top5.iterrows():
            st.markdown(f"""
            <div class='score-card {row["Grade"].lower().replace(" ", "-") if "EXCELLENT" in row["Grade"] else "score-good" if "TRÈS BON" in row["Grade"] else "score-average"}'>
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <div>
                        <span style='font-size: 24px;'>{row['Icone']}</span>
                        <span style='font-size: 20px; font-weight: bold; margin-left: 10px;'>{row['Symbole']}</span>
                        <span style='font-size: 14px; color: #666; margin-left: 10px;'>{row['Entreprise']}</span>
                    </div>
                    <div>
                        <span style='font-size: 20px;'>{row['Prix']}</span>
                        <span style='font-size: 14px; margin-left: 10px;'>{row['Perf 5j']}</span>
                    </div>
                    <div style='text-align: center;'>
                        <span style='font-size: 32px; font-weight: bold;'>{row['Score']}</span>
                        <br><span style='font-size: 14px;'>{row['Grade']}</span>
                    </div>
                    <div>
                        <span style='font-size: 14px;'>{row['Recommandation']}</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("### 📋 Classement complet")
        st.dataframe(df_scores, use_container_width=True, height=400)
        
        fig_dist = px.histogram(df_scores, x='Score', nbins=20, 
                                title="Distribution des scores composites",
                                color_discrete_sequence=['#005288'])
        fig_dist.add_vline(x=70, line_dash="dash", line_color="green", annotation_text="Excellent")
        fig_dist.add_vline(x=55, line_dash="dash", line_color="orange", annotation_text="Bon")
        fig_dist.update_layout(height=400)
        st.plotly_chart(fig_dist, use_container_width=True)
    else:
        st.warning("Aucune donnée disponible")

# ============================================================================
# SECTION 2: SCOREBOARD DÉTAILLÉ
# ============================================================================

elif menu == "📊 Scoreboard détaillé":
    st.subheader("📊 Scoreboard détaillé par action")
    
    selected_symbol = st.selectbox("Sélectionner une action", st.session_state.watchlist)
    
    if selected_symbol:
        hist_df, info = load_stock_data_cached(selected_symbol, period, interval)
        
        if not hist_df.empty:
            scores = {
                'financial': calculate_financial_score_from_info(info),
                'technical': calculate_technical_score_from_hist(hist_df),
                'momentum': calculate_momentum_score_from_hist(hist_df),
                'space_sector': calculate_space_sector_score_from_info(info, selected_symbol),
                'esg': calculate_esg_score_from_info(info),
                'risk': calculate_volatility_risk_score_from_hist(hist_df),
                'liquidity': calculate_liquidity_score_from_hist(hist_df, info),
                'growth': calculate_growth_potential_score_from_info(info, selected_symbol),
                'analyst': calculate_analyst_consensus_score_from_info(info)
            }
            
            composite = calculate_composite_score(scores)
            grade, icon, css_class, recommendation = get_score_grade(composite)
            current_price = hist_df['Close'].iloc[-1]
            
            st.markdown(f"""
            <div class='score-card {css_class}' style='text-align: center; padding: 2rem;'>
                <h2 style='margin: 0; color: #1a1a2e;'>{icon} {selected_symbol} - {SPACE_COMPANIES.get(selected_symbol, {}).get('name', selected_symbol)}</h2>
                <div style='font-size: 48px; font-weight: bold; margin: 20px 0; color: #1a1a2e;'>{composite:.1f}</div>
                <div style='font-size: 20px; color: #1a1a2e;'>{grade} - {recommendation}</div>
                <div style='margin-top: 10px; color: #1a1a2e;'>Prix: {format_currency(current_price)}</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("### 📈 Détail des scores par catégorie")
            
            col1, col2, col3 = st.columns(3)
            
            categories = [
                ('💰 Financier', scores['financial'], 'Santé financière, P/E'),
                ('📊 Technique', scores['technical'], 'Moyennes mobiles, RSI'),
                ('⚡ Momentum', scores['momentum'], 'MACD, Bollinger'),
                ('🛰️ Spatial', scores['space_sector'], 'Secteur spatial'),
                ('🌿 ESG', scores['esg'], 'Environnement, social'),
                ('⚠️ Risque', scores['risk'], 'Volatilité'),
                ('💧 Liquidité', scores['liquidity'], 'Volume'),
                ('🚀 Croissance', scores['growth'], 'Potentiel'),
                ('🎯 Analystes', scores['analyst'], 'Consensus')
            ]
            
            for i, (name, score, desc) in enumerate(categories):
                with [col1, col2, col3][i % 3]:
                    st.markdown(f"""
                    <div class='metric-card'>
                        <b>{name}</b><br>
                        <span style='font-size: 28px; font-weight: bold;'>{score}</span>
                        <br><small>{desc}</small>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Graphique radar
            categories_radar = ['financial', 'technical', 'momentum', 'space_sector', 'esg', 'risk', 'liquidity', 'growth', 'analyst']
            labels_radar = ['Financier', 'Technique', 'Momentum', 'Spatial', 'ESG', 'Risque', 'Liquidité', 'Croissance', 'Analystes']
            values_radar = [scores[cat] for cat in categories_radar]
            
            fig_radar = go.Figure()
            fig_radar.add_trace(go.Scatterpolar(
                r=values_radar + [values_radar[0]],
                theta=labels_radar + [labels_radar[0]],
                fill='toself',
                name=selected_symbol,
                line_color='#005288',
                fillcolor='rgba(0,82,136,0.3)'
            ))
            fig_radar.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                showlegend=True,
                height=500,
                title=f"Profil de score - {selected_symbol}",
                font=dict(color='#1a1a2e')
            )
            st.plotly_chart(fig_radar, use_container_width=True)
            
            # Recommandation
            if composite >= 70:
                st.success(f"**{icon} RECOMMANDATION : ACHAT FORT** - Score: {composite:.1f}/100")
            elif composite >= 55:
                st.info(f"**{icon} RECOMMANDATION : ACCUMULATION** - Score: {composite:.1f}/100")
            elif composite >= 40:
                st.warning(f"**{icon} RECOMMANDATION : NEUTRE** - Score: {composite:.1f}/100")
            else:
                st.error(f"**{icon} RECOMMANDATION : ÉVITER** - Score: {composite:.1f}/100")
        else:
            st.warning(f"Aucune donnée disponible pour {selected_symbol}")

# ============================================================================
# SECTION 3: PORTEFEUILLE & SCORES
# ============================================================================

elif menu == "💼 Portefeuille & Scores":
    st.subheader("💼 Analyse scoring de votre portefeuille")
    
    col1, col2 = st.columns([2, 1])
    
    with col2:
        st.markdown("### ➕ Ajouter une position")
        with st.form("add_to_portfolio"):
            symbol_pf = st.selectbox("Symbole", st.session_state.watchlist)
            shares = st.number_input("Actions", min_value=1, value=100)
            buy_price = st.number_input("Prix d'achat ($)", min_value=0.01, value=10.0)
            
            if st.form_submit_button("Ajouter"):
                if symbol_pf not in st.session_state.portfolio:
                    st.session_state.portfolio[symbol_pf] = []
                st.session_state.portfolio[symbol_pf].append({
                    'shares': shares,
                    'buy_price': buy_price,
                    'date': datetime.now().strftime('%Y-%m-%d')
                })
                st.success(f"✅ Ajouté")
                st.rerun()
    
    with col1:
        if st.session_state.portfolio:
            portfolio_scores = []
            total_value = 0
            weighted_score = 0
            
            for sym, positions in st.session_state.portfolio.items():
                hist_df, info = load_stock_data_cached(sym, period, interval)
                
                if not hist_df.empty:
                    current_price = hist_df['Close'].iloc[-1]
                    
                    scores = {
                        'financial': calculate_financial_score_from_info(info),
                        'technical': calculate_technical_score_from_hist(hist_df),
                        'momentum': calculate_momentum_score_from_hist(hist_df),
                        'space_sector': calculate_space_sector_score_from_info(info, sym),
                        'esg': calculate_esg_score_from_info(info),
                        'risk': calculate_volatility_risk_score_from_hist(hist_df),
                        'liquidity': calculate_liquidity_score_from_hist(hist_df, info),
                        'growth': calculate_growth_potential_score_from_info(info, sym),
                        'analyst': calculate_analyst_consensus_score_from_info(info)
                    }
                    composite = calculate_composite_score(scores)
                    
                    for pos in positions:
                        position_value = pos['shares'] * current_price
                        cost = pos['shares'] * pos['buy_price']
                        profit = position_value - cost
                        profit_pct = (profit / cost * 100) if cost > 0 else 0
                        
                        total_value += position_value
                        weighted_score += composite * position_value
                        
                        portfolio_scores.append({
                            'Symbole': sym,
                            'Actions': pos['shares'],
                            'Prix actuel': format_currency(current_price),
                            'Valeur': format_currency(position_value),
                            'Profit': format_currency(profit),
                            'Profit %': format_percentage(profit_pct),
                            'Score': round(composite, 1),
                            'Grade': get_score_grade(composite)[0]
                        })
            
            if total_value > 0:
                portfolio_score = weighted_score / total_value
                
                score_class = "score-excellent" if portfolio_score >= 70 else "score-good" if portfolio_score >= 55 else "score-average"
                st.markdown(f"""
                <div class='score-card {score_class}' style='text-align: center;'>
                    <h3 style='color: #1a1a2e;'>📊 Score global du portefeuille</h3>
                    <div style='font-size: 48px; font-weight: bold; color: #1a1a2e;'>{portfolio_score:.1f}/100</div>
                    <div style='color: #1a1a2e;'>{get_score_grade(portfolio_score)[0]}</div>
                    <div style='color: #1a1a2e;'>Valeur totale: {format_currency(total_value)}</div>
                </div>
                """, unsafe_allow_html=True)
                
                df_portfolio = pd.DataFrame(portfolio_scores)
                st.dataframe(df_portfolio, use_container_width=True)
                
                if st.button("🗑️ Vider le portefeuille"):
                    st.session_state.portfolio = {}
                    st.rerun()
        else:
            st.info("Aucune position. Ajoutez des actions pour analyser votre portefeuille.")

# ============================================================================
# SECTION 4: ANALYSE COMPARATIVE
# ============================================================================

elif menu == "📈 Analyse comparative":
    st.subheader("📈 Comparaison des scores entre actions")
    
    compare_symbols = st.multiselect("Sélectionner actions à comparer", st.session_state.watchlist, default=['RKLB', 'ASTS', 'PL'])
    
    if len(compare_symbols) >= 2:
        comparison_data = []
        
        for sym in compare_symbols:
            hist_df, info = load_stock_data_cached(sym, period, interval)
            
            if not hist_df.empty:
                scores = {
                    'financial': calculate_financial_score_from_info(info),
                    'technical': calculate_technical_score_from_hist(hist_df),
                    'momentum': calculate_momentum_score_from_hist(hist_df),
                    'space_sector': calculate_space_sector_score_from_info(info, sym),
                    'esg': calculate_esg_score_from_info(info),
                    'risk': calculate_volatility_risk_score_from_hist(hist_df),
                    'liquidity': calculate_liquidity_score_from_hist(hist_df, info),
                    'growth': calculate_growth_potential_score_from_info(info, sym),
                    'analyst': calculate_analyst_consensus_score_from_info(info)
                }
                
                comparison_data.append({
                    'Symbole': sym,
                    **scores,
                    'Composite': calculate_composite_score(scores)
                })
        
        if comparison_data:
            df_compare = pd.DataFrame(comparison_data)
            
            fig_compare = go.Figure()
            
            for sym in compare_symbols:
                sym_data = df_compare[df_compare['Symbole'] == sym].iloc[0]
                categories = ['financial', 'technical', 'momentum', 'space_sector', 'esg', 'risk', 'liquidity', 'growth', 'analyst']
                labels = ['Financier', 'Technique', 'Momentum', 'Spatial', 'ESG', 'Risque', 'Liquidité', 'Croissance', 'Analystes']
                values = [sym_data[cat] for cat in categories]
                
                fig_compare.add_trace(go.Scatterpolar(
                    r=values + [values[0]],
                    theta=labels + [labels[0]],
                    fill='toself',
                    name=sym
                ))
            
            fig_compare.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                showlegend=True,
                height=600,
                title="Comparaison radar des scores"
            )
            st.plotly_chart(fig_compare, use_container_width=True)
            
            st.dataframe(df_compare.sort_values('Composite', ascending=False), use_container_width=True)

# ============================================================================
# SECTION 5: ALERTES SCORING
# ============================================================================

elif menu == "🎯 Alertes scoring":
    st.subheader("🎯 Alertes basées sur les scores")
    
    target_score = st.slider("Seuil d'alerte", 0, 100, 70)
    
    if st.button("🔍 Scanner les actions maintenant"):
        with st.spinner("Scan en cours..."):
            alerts_found = []
            
            for sym in st.session_state.watchlist[:15]:
                hist_df, info = load_stock_data_cached(sym, "1mo", "1d")
                
                if not hist_df.empty:
                    scores = {
                        'financial': calculate_financial_score_from_info(info),
                        'technical': calculate_technical_score_from_hist(hist_df),
                        'momentum': calculate_momentum_score_from_hist(hist_df),
                        'space_sector': calculate_space_sector_score_from_info(info, sym),
                        'esg': calculate_esg_score_from_info(info),
                        'risk': calculate_volatility_risk_score_from_hist(hist_df),
                        'liquidity': calculate_liquidity_score_from_hist(hist_df, info),
                        'growth': calculate_growth_potential_score_from_info(info, sym),
                        'analyst': calculate_analyst_consensus_score_from_info(info)
                    }
                    composite = calculate_composite_score(scores)
                    
                    if composite >= target_score:
                        alerts_found.append({'Symbole': sym, 'Score': round(composite, 1)})
            
            if alerts_found:
                st.success(f"🎯 {len(alerts_found)} actions ont dépassé le seuil de {target_score}")
                st.dataframe(pd.DataFrame(alerts_found))
            else:
                st.warning(f"Aucune action n'a atteint le score de {target_score}")

# ============================================================================
# SECTION 6: EXPORT SCORES
# ============================================================================

elif menu == "📤 Export scores":
    st.subheader("📤 Export des scores")
    
    if st.button("📊 Générer rapport complet des scores"):
        all_scores_export = []
        
        with st.spinner("Génération du rapport..."):
            for sym in st.session_state.watchlist:
                hist_df, info = load_stock_data_cached(sym, "1mo", "1d")
                
                if not hist_df.empty:
                    scores = {
                        'financial': calculate_financial_score_from_info(info),
                        'technical': calculate_technical_score_from_hist(hist_df),
                        'momentum': calculate_momentum_score_from_hist(hist_df),
                        'space_sector': calculate_space_sector_score_from_info(info, sym),
                        'esg': calculate_esg_score_from_info(info),
                        'risk': calculate_volatility_risk_score_from_hist(hist_df),
                        'liquidity': calculate_liquidity_score_from_hist(hist_df, info),
                        'growth': calculate_growth_potential_score_from_info(info, sym),
                        'analyst': calculate_analyst_consensus_score_from_info(info)
                    }
                    
                    all_scores_export.append({
                        'Symbole': sym,
                        'Entreprise': SPACE_COMPANIES.get(sym, {}).get('name', sym),
                        'Secteur': SPACE_COMPANIES.get(sym, {}).get('sector', 'N/A'),
                        'Score_Financier': scores['financial'],
                        'Score_Technique': scores['technical'],
                        'Score_Momentum': scores['momentum'],
                        'Score_Spatial': scores['space_sector'],
                        'Score_ESG': scores['esg'],
                        'Score_Risque': scores['risk'],
                        'Score_Liquidite': scores['liquidity'],
                        'Score_Croissance': scores['growth'],
                        'Score_Analystes': scores['analyst'],
                        'Score_Composite': calculate_composite_score(scores),
                        'Date_Analyse': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
        
        if all_scores_export:
            df_export = pd.DataFrame(all_scores_export)
            csv = df_export.to_csv(index=False)
            st.download_button("📥 Télécharger CSV", csv, f"scores_spatiaux.csv", "text/csv")
            st.dataframe(df_export, use_container_width=True)

# Footer
st.markdown("---")
st.markdown(
    "<p class='footer-text'>🚀 SpaceX & NewSpace Tracker - Scores Boursiers Avancés | Données yfinance | Scores basés sur fondamentaux, technique, momentum, secteur spatial, ESG, risque, liquidité, croissance et analystes</p>",
    unsafe_allow_html=True
)
