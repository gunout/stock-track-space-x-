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
from sklearn.metrics import mean_squared_error
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

# Style CSS personnalisé
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #005288;
        text-align: center;
        margin-bottom: 2rem;
        font-family: 'Montserrat', sans-serif;
        background: linear-gradient(135deg, #000000 0%, #005288 50%, #FFFFFF 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .score-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 1rem;
        text-align: center;
        color: white;
        margin: 0.5rem 0;
    }
    .score-excellent { background: linear-gradient(135deg, #00b09b, #96c93d); }
    .score-good { background: linear-gradient(135deg, #2193b0, #6dd5ed); }
    .score-average { background: linear-gradient(135deg, #f2994a, #f2c94c); }
    .score-poor { background: linear-gradient(135deg, #eb3349, #f45c43); }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .spacex-badge {
        background-color: #005288;
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 1rem;
        font-weight: bold;
        display: inline-block;
    }
    .stButton>button {
        width: 100%;
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

if 'historical_scores' not in st.session_state:
    st.session_state.historical_scores = {}

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
# FONCTIONS DE CALCUL DES SCORES
# ============================================================================

def calculate_financial_score(info, ticker_obj):
    """Score financier basé sur les fondamentaux"""
    score = 50  # Base
    max_score = 100
    
    # Market Cap (pondéré)
    market_cap = info.get('marketCap', 0)
    if market_cap > 1e12:  # > $1 trillion
        score += 15
    elif market_cap > 1e11:  # > $100 billion
        score += 10
    elif market_cap > 1e10:  # > $10 billion
        score += 5
    elif market_cap > 1e9:  # > $1 billion
        score += 2
    
    # P/E Ratio (plus bas = meilleur, mais attention aux valeurs négatives)
    pe_ratio = info.get('trailingPE', 0)
    if pe_ratio and pe_ratio > 0:
        if pe_ratio < 15:
            score += 10
        elif pe_ratio < 25:
            score += 5
        elif pe_ratio > 50:
            score -= 5
    else:
        score -= 5  # Pénalité pour P/E négatif ou nul
    
    # Croissance du revenu
    revenue_growth = SPACE_COMPANIES.get(ticker_obj.ticker, {}).get('revenue_growth', 0)
    if revenue_growth > 0.5:
        score += 15
    elif revenue_growth > 0.2:
        score += 10
    elif revenue_growth > 0:
        score += 5
    elif revenue_growth < -0.2:
        score -= 10
    elif revenue_growth < 0:
        score -= 5
    
    # Marge bénéficiaire
    profit_margins = info.get('profitMargins', 0)
    if profit_margins:
        if profit_margins > 0.2:
            score += 10
        elif profit_margins > 0.1:
            score += 5
        elif profit_margins < 0:
            score -= 5
    
    # Dette / Equity
    debt_to_equity = info.get('debtToEquity', 0)
    if debt_to_equity:
        if debt_to_equity < 50:
            score += 10
        elif debt_to_equity < 100:
            score += 5
        elif debt_to_equity > 200:
            score -= 10
    
    # Cash flow
    operating_cash = info.get('operatingCashflow', 0)
    if operating_cash and operating_cash > 0:
        score += 10
    else:
        score -= 5
    
    # Return on Equity (ROE)
    roe = info.get('returnOnEquity', 0)
    if roe:
        if roe > 0.15:
            score += 10
        elif roe > 0.05:
            score += 5
        elif roe < 0:
            score -= 5
    
    return min(max(score, 0), max_score)

def calculate_technical_score(hist):
    """Score technique basé sur les indicateurs chartistes"""
    if hist is None or hist.empty or len(hist) < 50:
        return 50
    
    score = 50
    
    # Tendance (Moving Averages)
    close = hist['Close']
    ma_20 = close.rolling(window=20).mean()
    ma_50 = close.rolling(window=50).mean()
    
    if len(close) > 20 and not ma_20.isna().iloc[-1]:
        if close.iloc[-1] > ma_20.iloc[-1]:
            score += 10
        else:
            score -= 5
    
    if len(close) > 50 and not ma_50.isna().iloc[-1]:
        if ma_20.iloc[-1] > ma_50.iloc[-1]:
            score += 10
        else:
            score -= 5
    
    # RSI (Relative Strength Index)
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    if not rsi.isna().iloc[-1]:
        current_rsi = rsi.iloc[-1]
        if 30 <= current_rsi <= 70:  # Zone neutre
            score += 5
        elif current_rsi < 30:  # Survente - potentiel rebond
            score += 15
        elif current_rsi > 70:  # Surachat - risque correction
            score -= 10
    
    # Volume
    volume = hist['Volume']
    avg_volume = volume.rolling(window=20).mean()
    if len(volume) > 20:
        if volume.iloc[-1] > avg_volume.iloc[-1] * 1.5:
            score += 10  # Volume élevé = intérêt
        elif volume.iloc[-1] < avg_volume.iloc[-1] * 0.5:
            score -= 5
    
    # Volatilité (moins = mieux pour score technique)
    volatility = close.pct_change().std() * np.sqrt(252)
    if volatility < 0.3:
        score += 5
    elif volatility > 0.6:
        score -= 5
    
    # Performance récente
    perf_5d = ((close.iloc[-1] / close.iloc[-6]) - 1) * 100 if len(close) > 5 else 0
    perf_20d = ((close.iloc[-1] / close.iloc[-21]) - 1) * 100 if len(close) > 20 else 0
    
    if perf_5d > 5:
        score += 10
    elif perf_5d > 0:
        score += 5
    elif perf_5d < -5:
        score -= 10
    
    if perf_20d > 10:
        score += 10
    elif perf_20d > 0:
        score += 5
    elif perf_20d < -10:
        score -= 10
    
    return min(max(score, 0), 100)

def calculate_momentum_score(hist):
    """Score momentum basé sur les indicateurs de tendance"""
    if hist is None or hist.empty or len(hist) < 30:
        return 50
    
    score = 50
    close = hist['Close']
    
    # MACD
    exp1 = close.ewm(span=12, adjust=False).mean()
    exp2 = close.ewm(span=26, adjust=False).mean()
    macd = exp1 - exp2
    signal = macd.ewm(span=9, adjust=False).mean()
    
    if not macd.isna().iloc[-1] and not signal.isna().iloc[-1]:
        if macd.iloc[-1] > signal.iloc[-1]:
            score += 10
        else:
            score -= 5
    
    # Bollinger Bands
    sma = close.rolling(window=20).mean()
    std = close.rolling(window=20).std()
    upper_bb = sma + (std * 2)
    lower_bb = sma - (std * 2)
    
    if not upper_bb.isna().iloc[-1]:
        if close.iloc[-1] <= lower_bb.iloc[-1]:
            score += 10  # Rebond potentiel
        elif close.iloc[-1] >= upper_bb.iloc[-1]:
            score -= 5  # Surachat
    
    # ADX (Tendance force)
    high = hist['High']
    low = hist['Low']
    
    plus_dm = high.diff()
    minus_dm = low.diff()
    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm > 0] = 0
    
    tr = pd.concat([high - low, (high - close.shift()).abs(), (low - close.shift()).abs()], axis=1).max(axis=1)
    atr = tr.rolling(window=14).mean()
    
    plus_di = 100 * (plus_dm.rolling(window=14).mean() / atr)
    minus_di = 100 * (minus_dm.abs().rolling(window=14).mean() / atr)
    dx = (abs(plus_di - minus_di) / (plus_di + minus_di)) * 100
    adx = dx.rolling(window=14).mean()
    
    if not adx.isna().iloc[-1]:
        if adx.iloc[-1] > 25:
            score += 10
        elif adx.iloc[-1] < 20:
            score -= 5
    
    return min(max(score, 0), 100)

def calculate_space_sector_score(info, symbol):
    """Score spécifique au secteur spatial"""
    score = 50
    
    company_data = SPACE_COMPANIES.get(symbol, {})
    
    # Lien avec SpaceX/Musk (facteur de spéculation)
    if company_data.get('musk_related', False):
        score += 15
    
    # Secteur porteur
    sector = company_data.get('sector', '')
    if sector in ['Lanceurs', 'Satellites']:
        score += 10
    elif sector == 'Imagerie':
        score += 5
    
    # Contrats gouvernementaux (simulé)
    has_gov_contracts = info.get('sector', '') in ['Aerospace', 'Defense']
    if has_gov_contracts:
        score += 10
    
    # Partenariats stratégiques
    if 'Rocket Lab' in company_data.get('name', ''):
        score += 5  # Partenariat NASA
    if 'Lockheed' in company_data.get('name', ''):
        score += 5
    
    # Innovation et brevets (proxy market cap)
    market_cap = info.get('marketCap', 0)
    if market_cap > 1e10:
        score += 5
    
    # Cash burn rate pour startups spatiales
    revenue_growth = company_data.get('revenue_growth', 0)
    if revenue_growth > 0.5:
        score += 10
    elif revenue_growth < -0.2:
        score -= 10
    
    return min(max(score, 0), 100)

def calculate_esg_score(info):
    """Score ESG (Environnemental, Social, Gouvernance)"""
    score = 50
    
    # Environnement
    sector = info.get('sector', '')
    if sector == 'Clean Energy' or 'Solar' in str(info.get('longName', '')):
        score += 15
    elif sector in ['Aerospace', 'Industrial']:
        score -= 5
    
    # Gouvernance
    has_dividend = info.get('dividendYield', 0) > 0
    if has_dividend:
        score += 5
    
    # Social - diversité (proxy: entreprise tech = mieux noté)
    if 'Technology' in sector:
        score += 5
    
    # Controverses (proxy: bet léger)
    beta = info.get('beta', 1)
    if beta < 0.5:
        score += 5
    elif beta > 1.5:
        score -= 5
    
    return min(max(score, 0), 100)

def calculate_volatility_risk_score(hist):
    """Score de risque basé sur la volatilité"""
    if hist is None or hist.empty or len(hist) < 20:
        return 50
    
    score = 70  # Base élevée = risque faible
    
    close = hist['Close']
    volatility = close.pct_change().std() * np.sqrt(252)
    
    if volatility > 0.8:
        score -= 30
    elif volatility > 0.6:
        score -= 20
    elif volatility > 0.4:
        score -= 10
    elif volatility < 0.2:
        score += 10
    
    # Maximum drawdown
    rolling_max = close.expanding().max()
    drawdown = (close - rolling_max) / rolling_max
    max_drawdown = drawdown.min()
    
    if max_drawdown < -0.5:
        score -= 20
    elif max_drawdown < -0.3:
        score -= 10
    elif max_drawdown > -0.1:
        score += 10
    
    return min(max(score, 0), 100)

def calculate_liquidity_score(hist, info):
    """Score de liquidité"""
    score = 50
    
    if hist is None or hist.empty:
        return 50
    
    # Volume quotidien moyen
    avg_volume = hist['Volume'].tail(20).mean()
    market_cap = info.get('marketCap', 0)
    
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
    
    # Spread (estimé par market cap)
    if market_cap > 1e10:
        score += 10
    elif market_cap < 1e8:
        score -= 10
    
    return min(max(score, 0), 100)

def calculate_growth_potential_score(info, symbol):
    """Score de potentiel de croissance"""
    score = 50
    
    company_data = SPACE_COMPANIES.get(symbol, {})
    
    # Croissance du revenu
    revenue_growth = company_data.get('revenue_growth', 0)
    if revenue_growth > 0.5:
        score += 20
    elif revenue_growth > 0.2:
        score += 15
    elif revenue_growth > 0:
        score += 10
    elif revenue_growth < 0:
        score -= 10
    
    # Market cap (plus petit = plus de potentiel)
    market_cap = info.get('marketCap', 0)
    if market_cap < 500_000_000:  # Small cap
        score += 15
    elif market_cap < 2_000_000_000:
        score += 10
    elif market_cap > 100_000_000_000:  # Mega cap
        score -= 10
    
    # Secteur innovant
    sector = company_data.get('sector', '')
    if sector in ['Lanceurs', 'Satellites']:
        score += 10
    
    # P/E ratio pour growth stocks (accepté plus élevé)
    pe_ratio = info.get('forwardPE', 0)
    if pe_ratio and pe_ratio > 0:
        if pe_ratio > 50:
            score += 10  # Attentes de croissance élevées
    
    return min(max(score, 0), 100)

def calculate_analyst_consensus_score(info):
    """Score basé sur le consensus des analystes"""
    score = 50
    
    # Target price
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
    
    # Recommendation
    recommendation = info.get('recommendationKey', '')
    rec_map = {'strong_buy': 20, 'buy': 15, 'hold': 0, 'sell': -10, 'strong_sell': -20}
    score += rec_map.get(recommendation, 0)
    
    # Number of analysts
    num_analysts = info.get('numberOfAnalystOpinions', 0)
    if num_analysts > 20:
        score += 5
    elif num_analysts < 5:
        score -= 5
    
    return min(max(score, 0), 100)

def calculate_composite_score(scores, weights=None):
    """Calcule le score composite avec pondérations"""
    if weights is None:
        weights = {
            'financial': 0.20,
            'technical': 0.15,
            'momentum': 0.10,
            'space_sector': 0.15,
            'esg': 0.05,
            'risk': 0.10,
            'liquidity': 0.05,
            'growth': 0.15,
            'analyst': 0.05
        }
    
    composite = 0
    for key, weight in weights.items():
        composite += scores.get(key, 50) * weight
    
    return composite

def get_score_grade(score):
    """Convertit un score en grade et description"""
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

# ============================================================================
# FONCTIONS UTILITAIRES
# ============================================================================

@st.cache_data(ttl=300)
def load_stock_data(symbol, period, interval):
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period, interval=interval)
        info = ticker.info
        
        if not hist.empty:
            if hist.index.tz is None:
                hist.index = hist.index.tz_localize('UTC').tz_convert(USER_TIMEZONE)
            else:
                hist.index = hist.index.tz_convert(USER_TIMEZONE)
        
        return hist, info, ticker
    except Exception as e:
        return None, None, None

def format_currency(value):
    return f"${value:,.2f}" if value else "$0.00"

def format_percentage(value):
    return f"{value:+.1f}%" if value else "0%"

# ============================================================================
# INTERFACE PRINCIPALE
# ============================================================================

st.markdown("<h1 class='main-header'>🚀 SpaceX & NewSpace Tracker - Scores Boursiers Avancés</h1>", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/d/dc/SpaceX_Logo_Black.png/800px-SpaceX_Logo_Black.png", width=200)
    st.title("Navigation")
    
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
    
    # Période d'analyse
    period = st.selectbox("Période technique", ["1mo", "3mo", "6mo", "1y"], index=1)
    interval = "1d"
    
    auto_refresh = st.checkbox("Auto-refresh", value=False)
    if auto_refresh:
        refresh_rate = st.slider("Fréquence (sec)", 10, 60, 30)

# ============================================================================
# SECTION 1: CLASSEMENT DES SCORES
# ============================================================================

if menu == "🏆 Classement des scores":
    st.subheader("🏆 Classement général des actions spatiales")
    
    # Chargement des scores pour toutes les actions
    all_scores = []
    progress_bar = st.progress(0)
    
    for i, symbol in enumerate(st.session_state.watchlist):
        hist, info, ticker = load_stock_data(symbol, period, interval)
        
        if hist is not None and not hist.empty:
            # Calcul de tous les scores
            scores = {
                'financial': calculate_financial_score(info, ticker),
                'technical': calculate_technical_score(hist),
                'momentum': calculate_momentum_score(hist),
                'space_sector': calculate_space_sector_score(info, symbol),
                'esg': calculate_esg_score(info),
                'risk': calculate_volatility_risk_score(hist),
                'liquidity': calculate_liquidity_score(hist, info),
                'growth': calculate_growth_potential_score(info, symbol),
                'analyst': calculate_analyst_consensus_score(info)
            }
            
            composite = calculate_composite_score(scores)
            grade, icon, css_class, recommendation = get_score_grade(composite)
            current_price = hist['Close'].iloc[-1]
            perf_5d = ((hist['Close'].iloc[-1] / hist['Close'].iloc[-6]) - 1) * 100 if len(hist) > 5 else 0
            
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
                'Recommandation': recommendation,
                'Financial': scores['financial'],
                'Technical': scores['technical'],
                'Space': scores['space_sector'],
                'Growth': scores['growth']
            })
        
        progress_bar.progress((i + 1) / len(st.session_state.watchlist))
    
    progress_bar.empty()
    
    # Classement par score
    df_scores = pd.DataFrame(all_scores)
    df_scores = df_scores.sort_values('Score', ascending=False)
    
    # Affichage du classement
    st.markdown("### 🔥 Top 10 des meilleurs scores")
    
    top10 = df_scores.head(10)
    
    for idx, row in top10.iterrows():
        score_class = "score-excellent" if row['Score'] >= 70 else "score-good" if row['Score'] >= 55 else "score-average"
        st.markdown(f"""
        <div class='score-card {score_class}' style='margin-bottom: 10px;'>
            <table style='width: 100%; color: white;'>
                <tr>
                    <td style='width: 10%; font-size: 24px;'>{row['Icone']}</td>
                    <td style='width: 25%;'><b>{row['Symbole']}</b><br><small>{row['Entreprise']}</small></td>
                    <td style='width: 15%;'>{row['Prix']}<br><small>{row['Perf 5j']}</small></td>
                    <td style='width: 15%;'><b>Secteur:</b><br>{row['Secteur']}</td>
                    <td style='width: 15%; text-align: center;'><b style='font-size: 28px;'>{row['Score']}</b><br>{row['Grade']}</td>
                    <td style='width: 20%;'><b>Recommandation:</b><br>{row['Recommandation']}</td>
                </tr>
            </table>
        </div>
        """, unsafe_allow_html=True)
    
    # Tableau complet
    st.markdown("### 📋 Classement complet")
    st.dataframe(df_scores, use_container_width=True, height=400)
    
    # Distribution des scores
    st.markdown("### 📊 Distribution des scores")
    
    fig_dist = px.histogram(df_scores, x='Score', nbins=20, 
                            title="Distribution des scores composites",
                            color_discrete_sequence=['#005288'])
    fig_dist.add_vline(x=70, line_dash="dash", line_color="green", annotation_text="Excellent")
    fig_dist.add_vline(x=55, line_dash="dash", line_color="orange", annotation_text="Bon")
    fig_dist.add_vline(x=40, line_dash="dash", line_color="red", annotation_text="Moyen")
    fig_dist.update_layout(height=400)
    st.plotly_chart(fig_dist, use_container_width=True)
    
    # Radar chart des scores moyens par secteur
    st.markdown("### 🎯 Performance par secteur")
    sector_perf = df_scores.groupby('Secteur')['Score'].mean().reset_index()
    
    fig_radar = px.bar(sector_perf, x='Secteur', y='Score', 
                       title="Score moyen par secteur",
                       color='Score', color_continuous_scale='Viridis')
    st.plotly_chart(fig_radar, use_container_width=True)

# ============================================================================
# SECTION 2: SCOREBOARD DÉTAILLÉ
# ============================================================================

elif menu == "📊 Scoreboard détaillé":
    st.subheader("📊 Scoreboard détaillé par action")
    
    # Sélection de l'action
    selected_symbol = st.selectbox("Sélectionner une action", st.session_state.watchlist)
    
    if selected_symbol:
        hist, info, ticker = load_stock_data(selected_symbol, period, interval)
        
        if hist is not None and not hist.empty:
            # Calcul de tous les scores
            scores = {
                'financial': calculate_financial_score(info, ticker),
                'technical': calculate_technical_score(hist),
                'momentum': calculate_momentum_score(hist),
                'space_sector': calculate_space_sector_score(info, selected_symbol),
                'esg': calculate_esg_score(info),
                'risk': calculate_volatility_risk_score(hist),
                'liquidity': calculate_liquidity_score(hist, info),
                'growth': calculate_growth_potential_score(info, selected_symbol),
                'analyst': calculate_analyst_consensus_score(info)
            }
            
            composite = calculate_composite_score(scores)
            grade, icon, css_class, recommendation = get_score_grade(composite)
            
            # En-tête avec score global
            st.markdown(f"""
            <div class='score-card {css_class}' style='text-align: center; padding: 2rem;'>
                <h2 style='margin: 0;'>{icon} {selected_symbol} - {SPACE_COMPANIES.get(selected_symbol, {}).get('name', selected_symbol)}</h2>
                <div style='font-size: 48px; font-weight: bold; margin: 20px 0;'>{composite:.1f}</div>
                <div style='font-size: 20px;'>{grade} - {recommendation}</div>
                <div style='margin-top: 10px;'>Prix: {format_currency(hist['Close'].iloc[-1])}</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Affichage des scores détaillés
            st.markdown("### 📈 Détail des scores par catégorie")
            
            col1, col2, col3 = st.columns(3)
            
            categories = [
                ('💰 Financier', scores['financial'], 'Santé financière, P/E, croissance'),
                ('📊 Technique', scores['technical'], 'Moyennes mobiles, RSI, volume'),
                ('⚡ Momentum', scores['momentum'], 'MACD, Bollinger, ADX'),
                ('🛰️ Spatial', scores['space_sector'], 'Secteur spatial, contrats, innovation'),
                ('🌿 ESG', scores['esg'], 'Environnement, social, gouvernance'),
                ('⚠️ Risque', scores['risk'], 'Volatilité, drawdown maximum'),
                ('💧 Liquidité', scores['liquidity'], 'Volume, spread, accessibilité'),
                ('🚀 Croissance', scores['growth'], 'Potentiel, revenue growth, small cap'),
                ('🎯 Analystes', scores['analyst'], 'Consensus, price target, recommandations')
            ]
            
            for i, (name, score, desc) in enumerate(categories):
                with [col1, col2, col3][i % 3]:
                    score_class = "score-excellent" if score >= 70 else "score-good" if score >= 55 else "score-average"
                    st.markdown(f"""
                    <div class='metric-card' style='margin: 5px 0;'>
                        <b>{name}</b><br>
                        <span style='font-size: 32px; font-weight: bold;'>{score}</span>
                        <br><small>{desc}</small>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Graphique radar
            st.markdown("### 🎯 Profil de score (Radar)")
            
            categories_radar = ['financial', 'technical', 'momentum', 'space_sector', 'esg', 'risk', 'liquidity', 'growth', 'analyst']
            labels_radar = ['Financier', 'Technique', 'Momentum', 'Spatial', 'ESG', 'Risque', 'Liquidité', 'Croissance', 'Analystes']
            values_radar = [scores[cat] for cat in categories_radar]
            
            fig_radar = go.Figure()
            fig_radar.add_trace(go.Scatterpolar(
                r=values_radar + [values_radar[0]],
                theta=labels_radar + [labels_radar[0]],
                fill='toself',
                name=selected_symbol,
                line_color='#005288'
            ))
            fig_radar.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                showlegend=True,
                height=500,
                title=f"Profil de score - {selected_symbol}"
            )
            st.plotly_chart(fig_radar, use_container_width=True)
            
            # Historique des scores (simulé)
            st.markdown("### 📅 Évolution du score (simulée)")
            dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
            historical_composite = [composite - np.random.randint(-10, 15) for _ in range(30)]
            
            fig_history = go.Figure()
            fig_history.add_trace(go.Scatter(
                x=dates,
                y=historical_composite,
                mode='lines+markers',
                name='Score composite',
                line=dict(color='#005288', width=2),
                marker=dict(size=6)
            ))
            fig_history.add_hline(y=70, line_dash="dash", line_color="green", annotation_text="Excellent")
            fig_history.add_hline(y=55, line_dash="dash", line_color="orange", annotation_text="Bon")
            fig_history.add_hline(y=40, line_dash="dash", line_color="red", annotation_text="Moyen")
            fig_history.update_layout(title="Tendance du score (30 derniers jours)", height=400)
            st.plotly_chart(fig_history, use_container_width=True)
            
            # Recommandation détaillée
            st.markdown("### 💡 Recommandation d'investissement")
            
            if composite >= 70:
                st.success(f"""
                **{icon} RECOMMANDATION : ACHAT FORT**
                
                {selected_symbol} affiche un score excellent de {composite:.1f}/100.
                
                **Points forts:**
                - Score financier solide ({scores['financial']}/100)
                - Bon momentum technique ({scores['momentum']}/100)
                - Positionnement stratégique dans le spatial ({scores['space_sector']}/100)
                
                **Risques à surveiller:**
                - Score de risque: {scores['risk']}/100
                - Volatilité potentielle du secteur
                """)
            elif composite >= 55:
                st.info(f"""
                **{icon} RECOMMANDATION : ACCUMULATION**
                
                {selected_symbol} présente un score bon de {composite:.1f}/100.
                
                **Points positifs:**
                - Potentiel de croissance intéressant ({scores['growth']}/100)
                - Bonne liquidité ({scores['liquidity']}/100)
                
                **Points d'attention:**
                - Amélioration technique nécessaire ({scores['technical']}/100)
                - Suivre l'évolution du consensus analystes
                """)
            elif composite >= 40:
                st.warning(f"""
                **{icon} RECOMMANDATION : NEUTRE / SURVEILLER**
                
                {selected_symbol} affiche un score moyen de {composite:.1f}/100.
                
                **Points faibles:**
                - Score financier à renforcer ({scores['financial']}/100)
                - ESG perfectible ({scores['esg']}/100)
                
                **Catalyseurs potentiels:**
                - Nouvelles de l'entreprise
                - Contrats gouvernementaux
                """)
            else:
                st.error(f"""
                **{icon} RECOMMANDATION : ÉVITER / VENDRE**
                
                {selected_symbol} présente un score faible de {composite:.1f}/100.
                
                **Risques majeurs:**
                - Score technique faible ({scores['technical']}/100)
                - Croissance incertaine ({scores['growth']}/100)
                - Forte volatilité ({scores['risk']}/100)
                
                **Alternatives à considérer:**
                - RKLB, ASTS, ou PL pour le secteur spatial
                """)
            
            # Métriques clés
            with st.expander("📊 Métriques financières détaillées"):
                col_m1, col_m2 = st.columns(2)
                with col_m1:
                    st.write(f"**Market Cap:** {format_currency(info.get('marketCap', 0))}")
                    st.write(f"**P/E Ratio:** {info.get('trailingPE', 'N/A')}")
                    st.write(f"**Forward P/E:** {info.get('forwardPE', 'N/A')}")
                    st.write(f"**PEG Ratio:** {info.get('pegRatio', 'N/A')}")
                with col_m2:
                    st.write(f"**Beta:** {info.get('beta', 'N/A')}")
                    st.write(f"**Dividende:** {info.get('dividendYield', 0)*100:.2f}%")
                    st.write(f"**Target Price:** {format_currency(info.get('targetMeanPrice', 0))}")
                    st.write(f"**Recommandation:** {info.get('recommendationKey', 'N/A').upper()}")

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
    
    with col1:
        if st.session_state.portfolio:
            portfolio_scores = []
            total_value = 0
            weighted_score = 0
            
            for sym, positions in st.session_state.portfolio.items():
                hist, info, ticker = load_stock_data(sym, period, interval)
                
                if hist is not None and not hist.empty:
                    current_price = hist['Close'].iloc[-1]
                    
                    # Calcul du score
                    scores = {
                        'financial': calculate_financial_score(info, ticker),
                        'technical': calculate_technical_score(hist),
                        'momentum': calculate_momentum_score(hist),
                        'space_sector': calculate_space_sector_score(info, sym),
                        'esg': calculate_esg_score(info),
                        'risk': calculate_volatility_risk_score(hist),
                        'liquidity': calculate_liquidity_score(hist, info),
                        'growth': calculate_growth_potential_score(info, sym),
                        'analyst': calculate_analyst_consensus_score(info)
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
                
                # Métriques du portefeuille
                st.markdown(f"""
                <div class='score-card {"score-excellent" if portfolio_score >= 70 else "score-good" if portfolio_score >= 55 else "score-average"}'>
                    <h3>📊 Score global du portefeuille</h3>
                    <div style='font-size: 48px;'>{portfolio_score:.1f}/100</div>
                    <div>{get_score_grade(portfolio_score)[0]} - {get_score_grade(portfolio_score)[3]}</div>
                    <div>Valeur totale: {format_currency(total_value)}</div>
                </div>
                """, unsafe_allow_html=True)
                
                # Tableau des positions avec scores
                df_portfolio = pd.DataFrame(portfolio_scores)
                st.dataframe(df_portfolio, use_container_width=True)
                
                # Distribution des scores
                fig_dist = px.histogram(df_portfolio, x='Score', title="Distribution des scores dans le portefeuille")
                st.plotly_chart(fig_dist)
                
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
    
    compare_symbols = st.multiselect("Sélectionner actions à comparer", st.session_state.watchlist, default=['RKLB', 'ASTS', 'PL', 'SPCE'])
    
    if len(compare_symbols) >= 2:
        comparison_data = []
        
        for sym in compare_symbols:
            hist, info, ticker = load_stock_data(sym, period, interval)
            
            if hist is not None and not hist.empty:
                scores = {
                    'financial': calculate_financial_score(info, ticker),
                    'technical': calculate_technical_score(hist),
                    'momentum': calculate_momentum_score(hist),
                    'space_sector': calculate_space_sector_score(info, sym),
                    'esg': calculate_esg_score(info),
                    'risk': calculate_volatility_risk_score(hist),
                    'liquidity': calculate_liquidity_score(hist, info),
                    'growth': calculate_growth_potential_score(info, sym),
                    'analyst': calculate_analyst_consensus_score(info)
                }
                
                comparison_data.append({
                    'Symbole': sym,
                    **scores,
                    'Composite': calculate_composite_score(scores)
                })
        
        if comparison_data:
            df_compare = pd.DataFrame(comparison_data)
            
            # Graphique comparatif
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
            
            # Tableau comparatif
            st.dataframe(df_compare.sort_values('Composite', ascending=False), use_container_width=True)

# ============================================================================
# SECTION 5: ALERTES SCORING
# ============================================================================

elif menu == "🎯 Alertes scoring":
    st.subheader("🎯 Alertes basées sur les scores")
    
    st.markdown("""
    ### Configuration des alertes de scoring
    
    Recevez une notification quand une action atteint un certain score.
    """)
    
    target_score = st.slider("Seuil d'alerte", 0, 100, 70)
    
    if st.button("🔍 Scanner les actions maintenant"):
        st.info("Scan en cours...")
        
        alerts_found = []
        
        for sym in st.session_state.watchlist[:10]:  # Limité pour performance
            hist, info, ticker = load_stock_data(sym, "1mo", "1d")
            
            if hist is not None and not hist.empty:
                scores = {
                    'financial': calculate_financial_score(info, ticker),
                    'technical': calculate_technical_score(hist),
                    'momentum': calculate_momentum_score(hist),
                    'space_sector': calculate_space_sector_score(info, sym),
                    'esg': calculate_esg_score(info),
                    'risk': calculate_volatility_risk_score(hist),
                    'liquidity': calculate_liquidity_score(hist, info),
                    'growth': calculate_growth_potential_score(info, sym),
                    'analyst': calculate_analyst_consensus_score(info)
                }
                composite = calculate_composite_score(scores)
                
                if composite >= target_score:
                    alerts_found.append({
                        'Symbole': sym,
                        'Score': round(composite, 1),
                        'Grade': get_score_grade(composite)[0]
                    })
        
        if alerts_found:
            st.success(f"🎯 {len(alerts_found)} actions ont dépassé le seuil de {target_score}")
            df_alerts = pd.DataFrame(alerts_found)
            st.dataframe(df_alerts)
        else:
            st.warning(f"Aucune action n'a atteint le score de {target_score}")

# ============================================================================
# SECTION 6: EXPORT SCORES
# ============================================================================

elif menu == "📤 Export scores":
    st.subheader("📤 Export des scores")
    
    # Génération du rapport complet
    if st.button("📊 Générer rapport complet des scores"):
        all_scores_export = []
        
        with st.spinner("Génération du rapport..."):
            for sym in st.session_state.watchlist:
                hist, info, ticker = load_stock_data(sym, "1mo", "1d")
                
                if hist is not None and not hist.empty:
                    scores = {
                        'financial': calculate_financial_score(info, ticker),
                        'technical': calculate_technical_score(hist),
                        'momentum': calculate_momentum_score(hist),
                        'space_sector': calculate_space_sector_score(info, sym),
                        'esg': calculate_esg_score(info),
                        'risk': calculate_volatility_risk_score(hist),
                        'liquidity': calculate_liquidity_score(hist, info),
                        'growth': calculate_growth_potential_score(info, sym),
                        'analyst': calculate_analyst_consensus_score(info)
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
            
            # CSV
            csv = df_export.to_csv(index=False)
            st.download_button("📥 Télécharger CSV", csv, f"scores_spatiaux_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv")
            
            # JSON
            json_data = df_export.to_dict(orient='records')
            st.download_button("📥 Télécharger JSON", json.dumps(json_data, indent=2), f"scores_spatiaux_{datetime.now().strftime('%Y%m%d')}.json", "application/json")
            
            # Aperçu
            st.markdown("### Aperçu du rapport")
            st.dataframe(df_export, use_container_width=True)

# Footer
st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: gray; font-size: 0.8rem;'>"
    "🚀 SpaceX & NewSpace Tracker - Scores Boursiers Avancés | "
    "Scores basés sur fondamentaux, technique, momentum, secteur spatial, ESG, risque, liquidité, croissance et analystes"
    "</p>",
    unsafe_allow_html=True
)

# Auto-refresh
if auto_refresh and menu != "🏆 Classement des scores":
    time.sleep(refresh_rate)
    st.rerun()
