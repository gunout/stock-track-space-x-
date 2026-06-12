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
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import make_pipeline
import pytz
import warnings
warnings.filterwarnings('ignore')

# Configuration de la page
st.set_page_config(
    page_title="🚀 SpaceX & NewSpace Tracker - Actions Spatiales",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuration du fuseau horaire
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
    .spacex-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        padding: 1rem;
        border-radius: 1rem;
        color: white;
        margin: 1rem 0;
        border-left: 4px solid #005288;
    }
    .stock-price {
        font-size: 2rem;
        font-weight: bold;
        color: #005288;
        text-align: center;
    }
    .stock-change-positive {
        color: #00cc96;
        font-size: 1.2rem;
        font-weight: bold;
    }
    .stock-change-negative {
        color: #ef553b;
        font-size: 1.2rem;
        font-weight: bold;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .alert-box {
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .alert-success {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    .alert-warning {
        background-color: #fff3cd;
        border: 1px solid #ffeeba;
        color: #856404;
    }
    .timezone-badge {
        background-color: #e3f2fd;
        border-left: 4px solid #005288;
        padding: 0.5rem 1rem;
        margin: 1rem 0;
        font-size: 0.9rem;
    }
    .stButton>button {
        width: 100%;
    }
    .error-message {
        color: #ef553b;
        background-color: #ffe6e6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #ef553b;
        margin: 1rem 0;
    }
    .score-excellent {
        background: linear-gradient(135deg, #00b09b, #96c93d);
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 1rem;
        font-weight: bold;
    }
    .score-good {
        background: linear-gradient(135deg, #2193b0, #6dd5ed);
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 1rem;
        font-weight: bold;
    }
    .score-average {
        background: linear-gradient(135deg, #f2994a, #f2c94c);
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 1rem;
        font-weight: bold;
    }
    .score-poor {
        background: linear-gradient(135deg, #eb3349, #f45c43);
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 1rem;
        font-weight: bold;
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
        # NewSpace / Spatial
        'RKLB',   # Rocket Lab
        'ASTS',   # AST SpaceMobile
        'RDW',    # Redwire
        'PL',     # Planet Labs
        'SPCE',   # Virgin Galactic
        'MNTS',   # Momentus
        'BKSY',   # BlackSky
        'SATL',   # Satellogic
        'ASTR',   # Astra Space
        'LLAP',   # Terran Orbital
        'GSAT',   # Globalstar
        'IRDM',   # Iridium
        'MAXR',   # Maxar Technologies
        # Liés à l'espace / défense
        'LMT',    # Lockheed Martin
        'NOC',    # Northrop Grumman
        'BA',     # Boeing
        'RTX',    # Raytheon
        'GD',     # General Dynamics
        'LHX',    # L3Harris
        'HON',    # Honeywell
        'GE',     # General Electric
        'TDY',    # Teledyne
        'HEI',    # HEICO
        # Elon Musk lié
        'TSLA'    # Tesla
    ]

if 'notifications' not in st.session_state:
    st.session_state.notifications = []

if 'email_config' not in st.session_state:
    st.session_state.email_config = {
        'enabled': False,
        'smtp_server': 'smtp.gmail.com',
        'smtp_port': 587,
        'email': '',
        'password': ''
    }

# Mapping des entreprises spatiales
SPACE_COMPANIES = {
    'RKLB': {'name': 'Rocket Lab USA', 'sector': 'Lanceurs', 'description': 'Rocket Lab - Neutron, Electron'},
    'ASTS': {'name': 'AST SpaceMobile', 'sector': 'Satellites', 'description': 'Réseau 5G spatial'},
    'RDW': {'name': 'Redwire', 'sector': 'Infrastructure', 'description': 'Manufacturing spatial'},
    'PL': {'name': 'Planet Labs', 'sector': 'Imagerie', 'description': 'Earth observation satellites'},
    'SPCE': {'name': 'Virgin Galactic', 'sector': 'Tourisme', 'description': 'Vols suborbitaux'},
    'MNTS': {'name': 'Momentus', 'sector': 'Logistique', 'description': 'Transfert orbital'},
    'BKSY': {'name': 'BlackSky', 'sector': 'Imagerie', 'description': 'Surveillance satellite'},
    'SATL': {'name': 'Satellogic', 'sector': 'Imagerie', 'description': 'Hyper-spectrale'},
    'ASTR': {'name': 'Astra Space', 'sector': 'Lanceurs', 'description': 'Rocket 4'},
    'LLAP': {'name': 'Terran Orbital', 'sector': 'Satellites', 'description': 'SmallSats'},
    'GSAT': {'name': 'Globalstar', 'sector': 'Communications', 'description': 'IoT satellite'},
    'IRDM': {'name': 'Iridium', 'sector': 'Communications', 'description': 'Satellite voice/data'},
    'MAXR': {'name': 'Maxar Technologies', 'sector': 'Imagerie', 'description': 'Satellite imaging'},
    'TSLA': {'name': 'Tesla Inc.', 'sector': 'Électromobilité', 'description': 'EV, batteries, SpaceX lien'},
    'LMT': {'name': 'Lockheed Martin', 'sector': 'Défense', 'description': 'Aérospatial défense'},
    'BA': {'name': 'Boeing', 'sector': 'Aérospatial', 'description': 'Starliner, SLS'},
}

# Titre principal
st.markdown("<h1 class='main-header'>🚀 SpaceX & NewSpace Tracker - Actions Spatiales</h1>", unsafe_allow_html=True)

# Bannière de fuseau horaire
current_time_paris = datetime.now(USER_TIMEZONE)
current_time_ny = datetime.now(US_TIMEZONE)

st.markdown(f"""
<div class='timezone-badge'>
    <b>🕐 Fuseaux horaires :</b><br>
    🇫🇷 Heure Paris : {current_time_paris.strftime('%H:%M:%S')} (UTC+2)<br>
    🇺🇸 Heure NY (Bourses US) : {current_time_ny.strftime('%H:%M:%S')} (UTC-4/UTC-5)<br>
    🚀 Prochain lancement majeur: Starship IFT-7 - Janvier 2025
</div>
""", unsafe_allow_html=True)

# Sidebar pour la navigation
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/d/dc/SpaceX_Logo_Black.png/800px-SpaceX_Logo_Black.png", width=200)
    st.title("Navigation")
    
    menu = st.radio(
        "Choisir une section",
        ["📈 Tableau de bord", 
         "🏆 Scores boursiers",
         "💰 Portefeuille virtuel", 
         "🔔 Alertes de prix",
         "📧 Notifications email",
         "📤 Export des données",
         "🤖 Prédictions ML",
         "📊 Comparatif NewSpace"]
    )
    
    st.markdown("---")
    
    st.subheader("⚙️ Configuration")
    st.caption(f"🕐 Fuseau : UTC+2 (Heure Paris)")
    
    # Sélection du symbole principal
    symbol = st.selectbox(
        "Symbole principal",
        options=st.session_state.watchlist,
        index=0
    )
    
    period = st.selectbox(
        "Période",
        options=["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y"],
        index=2
    )
    
    interval_map = {
        "1m": "1 minute", "5m": "5 minutes", "15m": "15 minutes",
        "30m": "30 minutes", "1h": "1 heure", "1d": "1 jour",
        "1wk": "1 semaine"
    }
    interval = st.selectbox(
        "Intervalle",
        options=list(interval_map.keys()),
        format_func=lambda x: interval_map[x],
        index=5
    )
    
    auto_refresh = st.checkbox("Actualisation automatique", value=False)
    if auto_refresh:
        refresh_rate = st.slider("Fréquence (secondes)", 5, 60, 30)

# ============================================================================
# FONCTIONS DE SCORING
# ============================================================================

def calculate_financial_score(info):
    """Score financier (0-100)"""
    score = 50
    
    market_cap = info.get('marketCap', 0)
    if market_cap > 1e11:
        score += 15
    elif market_cap > 1e10:
        score += 10
    elif market_cap > 1e9:
        score += 5
    
    pe_ratio = info.get('trailingPE', 0)
    if pe_ratio and pe_ratio > 0:
        if pe_ratio < 20:
            score += 10
        elif pe_ratio < 30:
            score += 5
        elif pe_ratio > 50:
            score -= 5
    else:
        score -= 10
    
    profit_margins = info.get('profitMargins', 0)
    if profit_margins:
        if profit_margins > 0.15:
            score += 10
        elif profit_margins > 0:
            score += 5
        else:
            score -= 5
    
    return min(max(score, 0), 100)

def calculate_technical_score(hist):
    """Score technique (0-100)"""
    if hist is None or hist.empty or len(hist) < 20:
        return 50
    
    score = 50
    close = hist['Close']
    
    # Tendance MA20
    if len(close) > 20:
        ma20 = close.rolling(20).mean()
        if close.iloc[-1] > ma20.iloc[-1]:
            score += 10
        else:
            score -= 5
    
    # Performance récente
    if len(close) > 5:
        perf_5d = (close.iloc[-1] / close.iloc[-6] - 1) * 100
        if perf_5d > 5:
            score += 10
        elif perf_5d > 0:
            score += 5
        elif perf_5d < -5:
            score -= 10
    
    # Volume
    avg_volume = hist['Volume'].tail(20).mean()
    if hist['Volume'].iloc[-1] > avg_volume * 1.5:
        score += 5
    
    return min(max(score, 0), 100)

def calculate_space_sector_score(symbol):
    """Score spécifique au secteur spatial"""
    company = SPACE_COMPANIES.get(symbol, {})
    
    score = 50
    
    # Secteur porteur
    if company.get('sector') in ['Lanceurs', 'Satellites']:
        score += 15
    elif company.get('sector') == 'Imagerie':
        score += 10
    
    # Lien SpaceX / Musk
    if symbol == 'TSLA':
        score += 20
    elif symbol in ['RKLB', 'ASTS']:
        score += 10
    
    return min(score, 100)

def calculate_growth_score(info, symbol):
    """Score de croissance"""
    score = 50
    
    company = SPACE_COMPANIES.get(symbol, {})
    
    # Revenue growth (simulé basé sur le secteur)
    if company.get('sector') in ['Lanceurs', 'Satellites']:
        score += 15
    
    # Small cap = plus de potentiel
    market_cap = info.get('marketCap', 0)
    if market_cap < 5e8:
        score += 15
    elif market_cap < 2e9:
        score += 10
    elif market_cap > 1e11:
        score -= 10
    
    return min(score, 100)

def calculate_risk_score(hist):
    """Score de risque (inversé - plus haut = moins risqué)"""
    if hist is None or hist.empty or len(hist) < 20:
        return 50
    
    score = 70  # Base haute = moins risqué
    close = hist['Close']
    
    # Volatilité
    volatility = close.pct_change().std() * np.sqrt(252)
    if volatility > 0.6:
        score -= 25
    elif volatility > 0.4:
        score -= 15
    elif volatility > 0.3:
        score -= 5
    elif volatility < 0.2:
        score += 10
    
    # Drawdown maximum
    rolling_max = close.expanding().max()
    drawdown = (close - rolling_max) / rolling_max
    max_drawdown = drawdown.min()
    
    if max_drawdown < -0.5:
        score -= 20
    elif max_drawdown < -0.3:
        score -= 10
    
    return min(max(score, 0), 100)

def calculate_composite_score(scores):
    """Score composite pondéré"""
    weights = {
        'financial': 0.25,
        'technical': 0.20,
        'space_sector': 0.20,
        'growth': 0.20,
        'risk': 0.15
    }
    
    composite = 0
    for key, weight in weights.items():
        composite += scores.get(key, 50) * weight
    
    return composite

def get_score_grade(score):
    if score >= 75:
        return "EXCELLENT", "score-excellent", "🌟"
    elif score >= 60:
        return "TRÈS BON", "score-good", "📈"
    elif score >= 45:
        return "BON", "score-average", "✅"
    else:
        return "FAIBLE", "score-poor", "⚠️"

# ============================================================================
# FONCTIONS UTILITAIRES
# ============================================================================

@st.cache_data(ttl=300)
def load_stock_data(symbol, period, interval):
    """Charge les données boursières"""
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period, interval=interval)
        info = ticker.info
        
        if not hist.empty:
            if hist.index.tz is None:
                hist.index = hist.index.tz_localize('UTC').tz_convert(USER_TIMEZONE)
            else:
                hist.index = hist.index.tz_convert(USER_TIMEZONE)
        
        return hist, info
    except Exception as e:
        return None, None

def send_email_alert(subject, body, to_email):
    if not st.session_state.email_config['enabled']:
        return False
    
    try:
        msg = MIMEMultipart()
        msg['From'] = st.session_state.email_config['email']
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))
        
        server = smtplib.SMTP(
            st.session_state.email_config['smtp_server'], 
            st.session_state.email_config['smtp_port']
        )
        server.starttls()
        server.login(
            st.session_state.email_config['email'],
            st.session_state.email_config['password']
        )
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        st.error(f"Erreur d'envoi: {e}")
        return False

def check_price_alerts(current_price, symbol):
    triggered = []
    for alert in st.session_state.price_alerts:
        if alert['symbol'] == symbol:
            if alert['condition'] == 'above' and current_price >= alert['price']:
                triggered.append(alert)
            elif alert['condition'] == 'below' and current_price <= alert['price']:
                triggered.append(alert)
    return triggered

def format_currency(value):
    return f"${value:.2f}" if value else "$0.00"

def safe_get_metric(hist, metric, index=-1):
    try:
        if hist is not None and not hist.empty and len(hist) > abs(index):
            return hist[metric].iloc[index]
        return 0
    except:
        return 0

# Chargement des données
hist, info = load_stock_data(symbol, period, interval)

if hist is None or hist.empty:
    st.markdown(f"""
    <div class='error-message'>
        ⚠️ Impossible de charger les données pour {symbol}.<br>
        Vérifiez que le symbole est correct.
    </div>
    """, unsafe_allow_html=True)
    current_price = 0
else:
    current_price = safe_get_metric(hist, 'Close')
    
    triggered_alerts = check_price_alerts(current_price, symbol)
    for alert in triggered_alerts:
        st.balloons()
        st.success(f"🎯 Alerte déclenchée pour {symbol} à {format_currency(current_price)}")
        
        if st.session_state.email_config['enabled']:
            subject = f"🚨 Alerte prix - {symbol}"
            body = f"""
            <h2>Alerte de prix déclenchée</h2>
            <p><b>Symbole:</b> {symbol}</p>
            <p><b>Prix actuel:</b> {format_currency(current_price)}</p>
            <p><b>Date:</b> {datetime.now(USER_TIMEZONE).strftime('%Y-%m-%d %H:%M:%S')} (Paris)</p>
            """
            send_email_alert(subject, body, st.session_state.email_config['email'])

# ============================================================================
# SECTION 1: TABLEAU DE BORD
# ============================================================================
if menu == "📈 Tableau de bord":
    st.subheader("📊 Tableau de bord SpaceX & NewSpace")
    
    # Info SpaceX
    st.markdown("""
    <div class='spacex-card'>
        <b>🚀 SpaceX (privé - non coté)</b><br>
        Valuation estimée: $180B | Starlink: ~6,200 satellites | Lancements 2024: 128<br>
        Actions liées: TSLA (Elon Musk), RKLB (concurrent), ASTS (Starlink concurrent)
    </div>
    """, unsafe_allow_html=True)
    
    if hist is not None and not hist.empty:
        company = SPACE_COMPANIES.get(symbol, {})
        company_name = company.get('name', symbol)
        sector = company.get('sector', 'Spatial')
        
        st.subheader(f"📊 {symbol} - {company_name} ({sector})")
        
        col1, col2, col3, col4 = st.columns(4)
        
        previous_close = safe_get_metric(hist, 'Close', -2) if len(hist) > 1 else current_price
        change = current_price - previous_close
        change_pct = (change / previous_close * 100) if previous_close != 0 else 0
        
        with col1:
            st.metric(
                label="Prix actuel",
                value=format_currency(current_price),
                delta=f"{change:.2f} ({change_pct:.2f}%)"
            )
        
        with col2:
            day_high = safe_get_metric(hist, 'High')
            st.metric("Plus haut", format_currency(day_high))
        
        with col3:
            day_low = safe_get_metric(hist, 'Low')
            st.metric("Plus bas", format_currency(day_low))
        
        with col4:
            volume = safe_get_metric(hist, 'Volume')
            volume_formatted = f"{volume/1e6:.1f}M" if volume > 1e6 else f"{volume/1e3:.1f}K"
            st.metric("Volume", volume_formatted)
        
        # Graphique
        st.subheader("📉 Évolution du prix")
        
        fig = go.Figure()
        
        if interval in ["1m", "5m", "15m", "30m", "1h"]:
            fig.add_trace(go.Candlestick(
                x=hist.index,
                open=hist['Open'],
                high=hist['High'],
                low=hist['Low'],
                close=hist['Close'],
                name='Prix',
                increasing_line_color='#00cc96',
                decreasing_line_color='#ef553b'
            ))
        else:
            fig.add_trace(go.Scatter(
                x=hist.index,
                y=hist['Close'],
                mode='lines',
                name='Prix',
                line=dict(color='#005288', width=2)
            ))
        
        if len(hist) >= 20:
            ma20 = hist['Close'].rolling(20).mean()
            fig.add_trace(go.Scatter(
                x=hist.index, y=ma20, mode='lines',
                name='MA20', line=dict(color='orange', width=1, dash='dash')
            ))
        
        if len(hist) >= 50:
            ma50 = hist['Close'].rolling(50).mean()
            fig.add_trace(go.Scatter(
                x=hist.index, y=ma50, mode='lines',
                name='MA50', line=dict(color='purple', width=1, dash='dash')
            ))
        
        fig.add_trace(go.Bar(
            x=hist.index, y=hist['Volume'],
            name='Volume', yaxis='y2',
            marker=dict(color='lightgray', opacity=0.3)
        ))
        
        fig.update_layout(
            title=f"{symbol} - {period} (heures Paris UTC+2)",
            yaxis_title="Prix ($)",
            yaxis2=dict(title="Volume", overlaying='y', side='right', showgrid=False),
            xaxis_title="Date",
            height=600,
            hovermode='x unified',
            template='plotly_white'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Informations entreprise
        with st.expander("ℹ️ Informations sur l'entreprise"):
            if info:
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Nom :** {info.get('longName', company_name)}")
                    st.write(f"**Secteur :** {info.get('sector', sector)}")
                    st.write(f"**Industrie :** {info.get('industry', 'Aérospatial/Défense')}")
                    st.write(f"**Description :** {company.get('description', info.get('longBusinessSummary', 'N/A')[:300])}")
                
                with col2:
                    market_cap = info.get('marketCap', 0)
                    if market_cap > 0:
                        st.write(f"**Capitalisation :** ${market_cap/1e9:.2f}B")
                    st.write(f"**P/E :** {info.get('trailingPE', 'N/A')}")
                    st.write(f"**Beta :** {info.get('beta', 'N/A')}")
                    st.write(f"**Dividende :** {info.get('dividendYield', 0)*100:.2f}%" if info.get('dividendYield') else "**Dividende :** N/A")
            else:
                st.write("Informations non disponibles")
    else:
        st.warning(f"Aucune donnée disponible pour {symbol}")

# ============================================================================
# SECTION 2: SCORES BOURSIERS
# ============================================================================
elif menu == "🏆 Scores boursiers":
    st.subheader("🏆 Scores boursiers - Actions Spatiales")
    
    st.info("""
    Les scores sont calculés sur 5 critères:
    - 💰 Financier (P/E, Market Cap, marges)
    - 📊 Technique (tendance, performance, volume)
    - 🚀 Secteur spatial (positionnement, innovation)
    - 📈 Croissance (potentiel, small cap)
    - ⚠️ Risque (volatilité, drawdown)
    """)
    
    all_scores = []
    progress_bar = st.progress(0)
    
    for i, sym in enumerate(st.session_state.watchlist):
        hist_s, info_s = load_stock_data(sym, "1mo", "1d")
        
        if hist_s is not None and not hist_s.empty:
            scores = {
                'financial': calculate_financial_score(info_s),
                'technical': calculate_technical_score(hist_s),
                'space_sector': calculate_space_sector_score(sym),
                'growth': calculate_growth_score(info_s, sym),
                'risk': calculate_risk_score(hist_s)
            }
            
            composite = calculate_composite_score(scores)
            grade, grade_class, icon = get_score_grade(composite)
            
            company = SPACE_COMPANIES.get(sym, {})
            current = hist_s['Close'].iloc[-1]
            perf_5d = ((hist_s['Close'].iloc[-1] / hist_s['Close'].iloc[-6]) - 1) * 100 if len(hist_s) > 5 else 0
            
            all_scores.append({
                'Symbole': sym,
                'Entreprise': company.get('name', sym),
                'Secteur': company.get('sector', 'N/A'),
                'Prix': format_currency(current),
                'Perf 5j': f"{perf_5d:+.1f}%",
                'Score': round(composite, 1),
                'Grade': grade,
                'Classe': grade_class,
                'Icone': icon
            })
        
        progress_bar.progress((i + 1) / len(st.session_state.watchlist))
    
    progress_bar.empty()
    
    if all_scores:
        df_scores = pd.DataFrame(all_scores)
        df_scores = df_scores.sort_values('Score', ascending=False)
        
        st.markdown("### 🔥 Classement des scores")
        
        for _, row in df_scores.iterrows():
            st.markdown(f"""
            <div style='margin-bottom: 10px; padding: 15px; background-color: #f8f9fa; border-radius: 10px; border-left: 5px solid #005288;'>
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <div>
                        <span style='font-size: 24px;'>{row['Icone']}</span>
                        <span style='font-size: 18px; font-weight: bold; margin-left: 10px;'>{row['Symbole']}</span>
                        <span style='font-size: 14px; color: #666; margin-left: 10px;'>{row['Entreprise']}</span>
                        <br><small>{row['Secteur']}</small>
                    </div>
                    <div>
                        <span style='font-size: 18px;'>{row['Prix']}</span>
                        <span style='font-size: 14px; margin-left: 10px;'>{row['Perf 5j']}</span>
                    </div>
                    <div>
                        <span class='{row['Classe']}' style='font-size: 28px; padding: 5px 15px;'>{row['Score']}</span>
                        <br><small>{row['Grade']}</small>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("### 📊 Détail des scores")
        st.dataframe(df_scores, use_container_width=True)
        
        # Graphique radar des scores moyens par secteur
        sector_avg = df_scores.groupby('Secteur')['Score'].mean().reset_index()
        fig = px.bar(sector_avg, x='Secteur', y='Score', 
                     title="Score moyen par secteur",
                     color='Score', color_continuous_scale='Viridis')
        st.plotly_chart(fig, use_container_width=True)
        
        # Distribution
        fig_hist = px.histogram(df_scores, x='Score', nbins=20,
                                title="Distribution des scores",
                                color_discrete_sequence=['#005288'])
        fig_hist.add_vline(x=75, line_dash="dash", line_color="green", annotation_text="Excellent")
        fig_hist.add_vline(x=60, line_dash="dash", line_color="orange", annotation_text="Très bon")
        fig_hist.add_vline(x=45, line_dash="dash", line_color="red", annotation_text="Bon")
        st.plotly_chart(fig_hist, use_container_width=True)

# ============================================================================
# SECTION 3: PORTEFEUILLE VIRTUEL
# ============================================================================
elif menu == "💰 Portefeuille virtuel":
    st.subheader("💰 Portefeuille virtuel - Actions Spatiales")
    
    col1, col2 = st.columns([2, 1])
    
    with col2:
        st.markdown("### ➕ Ajouter une position")
        with st.form("add_position"):
            symbol_pf = st.selectbox("Symbole", st.session_state.watchlist)
            shares = st.number_input("Nombre d'actions", min_value=1, step=1, value=100)
            buy_price = st.number_input("Prix d'achat ($)", min_value=0.01, step=1.0, value=10.0)
            
            if st.form_submit_button("Ajouter au portefeuille"):
                if symbol_pf not in st.session_state.portfolio:
                    st.session_state.portfolio[symbol_pf] = []
                
                st.session_state.portfolio[symbol_pf].append({
                    'shares': shares,
                    'buy_price': buy_price,
                    'date': datetime.now(USER_TIMEZONE).strftime('%Y-%m-%d %H:%M:%S')
                })
                st.success(f"✅ {shares} actions {symbol_pf} ajoutées")
    
    with col1:
        st.markdown("### 📊 Performance du portefeuille")
        
        if st.session_state.portfolio:
            portfolio_data = []
            total_value = 0
            total_cost = 0
            
            for symbol_pf, positions in st.session_state.portfolio.items():
                try:
                    ticker = yf.Ticker(symbol_pf)
                    hist = ticker.history(period='1d')
                    if not hist.empty:
                        current = hist['Close'].iloc[-1]
                    else:
                        current = 0
                    
                    for pos in positions:
                        shares = pos['shares']
                        buy_price = pos['buy_price']
                        cost = shares * buy_price
                        value = shares * current
                        profit = value - cost
                        profit_pct = (profit / cost * 100) if cost > 0 else 0
                        
                        total_cost += cost
                        total_value += value
                        
                        portfolio_data.append({
                            'Symbole': symbol_pf,
                            'Actions': shares,
                            "Prix d'achat": f"${buy_price:.2f}",
                            'Prix actuel': f"${current:.2f}",
                            'Valeur': f"${value:,.2f}",
                            'Profit': f"${profit:,.2f}",
                            'Profit %': f"{profit_pct:.1f}%"
                        })
                except Exception as e:
                    st.warning(f"Impossible de charger {symbol_pf}")
            
            if portfolio_data:
                total_profit = total_value - total_cost
                total_profit_pct = (total_profit / total_cost * 100) if total_cost > 0 else 0
                
                col_1, col_2, col_3 = st.columns(3)
                col_1.metric("Valeur totale", f"${total_value:,.2f}")
                col_2.metric("Coût total", f"${total_cost:,.2f}")
                col_3.metric("Profit total", f"${total_profit:,.2f}", delta=f"{total_profit_pct:.1f}%")
                
                df_portfolio = pd.DataFrame(portfolio_data)
                st.dataframe(df_portfolio, use_container_width=True)
                
                fig_pie = px.pie(
                    names=[p['Symbole'] for p in portfolio_data],
                    values=[float(p['Valeur'].replace('$', '').replace(',', '')) for p in portfolio_data],
                    title="Répartition du portefeuille"
                )
                st.plotly_chart(fig_pie)
                
                if st.button("🗑️ Vider le portefeuille"):
                    st.session_state.portfolio = {}
                    st.rerun()
            else:
                st.info("Aucune donnée de performance disponible")
        else:
            st.info("Aucune position. Ajoutez des actions spatiales pour commencer !")

# ============================================================================
# SECTION 4: ALERTES DE PRIX
# ============================================================================
elif menu == "🔔 Alertes de prix":
    st.subheader("🔔 Gestion des alertes de prix")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### ➕ Créer une nouvelle alerte")
        with st.form("new_alert"):
            alert_symbol = st.selectbox("Symbole", st.session_state.watchlist, index=0)
            
            default_price = float(current_price * 1.05) if current_price > 0 else 50.0
            alert_price = st.number_input("Prix cible ($)", min_value=0.01, step=1.0, value=default_price)
            
            col_cond, col_type = st.columns(2)
            with col_cond:
                condition = st.selectbox("Condition", ["above", "below"])
            with col_type:
                alert_type = st.selectbox("Type", ["Permanent", "Une fois"])
            
            one_time = alert_type == "Une fois"
            
            if st.form_submit_button("Créer l'alerte"):
                st.session_state.price_alerts.append({
                    'symbol': alert_symbol,
                    'price': alert_price,
                    'condition': condition,
                    'one_time': one_time,
                    'created': datetime.now(USER_TIMEZONE).strftime('%Y-%m-%d %H:%M:%S')
                })
                st.success(f"✅ Alerte créée pour {alert_symbol} à ${alert_price:.2f}")
    
    with col2:
        st.markdown("### 📋 Alertes actives")
        if st.session_state.price_alerts:
            for i, alert in enumerate(st.session_state.price_alerts):
                st.markdown(f"""
                <div class='alert-box alert-warning'>
                    <b>{alert['symbol']}</b> - {alert['condition']} ${alert['price']:.2f}<br>
                    <small>Créée: {alert['created']} | {('Usage unique' if alert['one_time'] else 'Permanent')}</small>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"Supprimer", key=f"del_alert_{i}"):
                    st.session_state.price_alerts.pop(i)
                    st.rerun()
        else:
            st.info("Aucune alerte active")

# ============================================================================
# SECTION 5: NOTIFICATIONS EMAIL
# ============================================================================
elif menu == "📧 Notifications email":
    st.subheader("📧 Configuration des notifications email")
    
    with st.form("email_config"):
        enabled = st.checkbox("Activer les notifications email", value=st.session_state.email_config['enabled'])
        
        col1, col2 = st.columns(2)
        with col1:
            smtp_server = st.text_input("Serveur SMTP", value=st.session_state.email_config['smtp_server'])
            smtp_port = st.number_input("Port SMTP", value=st.session_state.email_config['smtp_port'])
        
        with col2:
            email = st.text_input("Adresse email", value=st.session_state.email_config['email'])
            password = st.text_input("Mot de passe", type="password", value=st.session_state.email_config['password'])
        
        test_email = st.text_input("Email de test (optionnel)")
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.form_submit_button("💾 Sauvegarder"):
                st.session_state.email_config = {
                    'enabled': enabled,
                    'smtp_server': smtp_server,
                    'smtp_port': smtp_port,
                    'email': email,
                    'password': password
                }
                st.success("Configuration sauvegardée !")
        
        with col_btn2:
            if st.form_submit_button("📨 Tester"):
                if test_email:
                    if send_email_alert(
                        "Test SpaceX Tracker",
                        f"<h2>✅ Test réussi !</h2><p>Votre configuration email fonctionne correctement.</p><p>Heure: {datetime.now(USER_TIMEZONE).strftime('%Y-%m-%d %H:%M:%S')} (Paris)</p>",
                        test_email
                    ):
                        st.success("Email de test envoyé !")
                    else:
                        st.error("Échec de l'envoi")

# ============================================================================
# SECTION 6: EXPORT DES DONNÉES
# ============================================================================
elif menu == "📤 Export des données":
    st.subheader("📤 Export des données")
    
    if hist is not None and not hist.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📊 Données historiques")
            display_hist = hist.copy()
            display_hist.index = display_hist.index.strftime('%Y-%m-%d %H:%M:%S (Paris)')
            st.dataframe(display_hist.tail(20))
            
            csv = hist.to_csv()
            st.download_button(
                label="📥 Télécharger en CSV",
                data=csv,
                file_name=f"{symbol}_data_{datetime.now(USER_TIMEZONE).strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        
        with col2:
            st.markdown("### 📈 Statistiques")
            stats = {
                'Moyenne': hist['Close'].mean(),
                'Écart-type': hist['Close'].std(),
                'Min': hist['Close'].min(),
                'Max': hist['Close'].max(),
                'Variation': f"{(hist['Close'].iloc[-1] / hist['Close'].iloc[0] - 1) * 100:.2f}%" if len(hist) > 1 else "N/A"
            }
            
            for key, value in stats.items():
                if isinstance(value, float):
                    st.write(f"{key}: ${value:.2f}")
                else:
                    st.write(f"{key}: {value}")
            
            json_data = {
                'symbol': symbol,
                'company': SPACE_COMPANIES.get(symbol, {}).get('name', symbol),
                'last_update': datetime.now(USER_TIMEZONE).isoformat(),
                'timezone': 'Europe/Paris',
                'current_price': float(current_price) if current_price else 0,
                'statistics': {k: (float(v) if isinstance(v, (int, float)) else v) for k, v in stats.items()},
                'data': hist.reset_index().to_dict(orient='records')
            }
            
            st.download_button(
                label="📥 Télécharger en JSON",
                data=json.dumps(json_data, indent=2, default=str),
                file_name=f"{symbol}_data_{datetime.now(USER_TIMEZONE).strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    else:
        st.warning(f"Aucune donnée à exporter pour {symbol}")

# ============================================================================
# SECTION 7: PRÉDICTIONS ML
# ============================================================================
elif menu == "🤖 Prédictions ML":
    st.subheader("🤖 Prédictions Machine Learning - Actions Spatiales")
    
    if hist is not None and not hist.empty and len(hist) > 30:
        st.markdown("### Modèle de prédiction (Régression polynomiale)")
        
        st.info("""
        ⚠️ Facteurs influençant le secteur spatial:
        - Lancements et succès/échecs
        - Contrats gouvernementaux (NASA, DoD, ESA)
        - Concurrence (SpaceX, Blue Origin)
        - Régulations et licences
        - Technologie et innovation
        """)
        
        df_pred = hist[['Close']].reset_index()
        df_pred['Days'] = (df_pred['Date'] - df_pred['Date'].min()).dt.days
        
        X = df_pred['Days'].values.reshape(-1, 1)
        y = df_pred['Close'].values
        
        col1, col2 = st.columns(2)
        
        with col1:
            days_to_predict = st.slider("Jours à prédire", 1, 30, 7)
            degree = st.slider("Degré du polynôme", 1, 5, 2)
        
        with col2:
            show_confidence = st.checkbox("Afficher l'intervalle de confiance", value=True)
        
        model = make_pipeline(PolynomialFeatures(degree=degree), LinearRegression())
        model.fit(X, y)
        
        last_day = X[-1][0]
        future_days = np.arange(last_day + 1, last_day + days_to_predict + 1).reshape(-1, 1)
        predictions = model.predict(future_days)
        
        last_date = df_pred['Date'].iloc[-1]
        future_dates = [last_date + timedelta(days=i+1) for i in range(days_to_predict)]
        
        fig_pred = go.Figure()
        
        fig_pred.add_trace(go.Scatter(
            x=df_pred['Date'], y=y, mode='lines',
            name='Historique', line=dict(color='blue')
        ))
        
        fig_pred.add_trace(go.Scatter(
            x=future_dates, y=predictions, mode='lines+markers',
            name='Prédictions', line=dict(color='red', dash='dash'), marker=dict(size=8)
        ))
        
        if show_confidence:
            residuals = y - model.predict(X)
            std_residuals = np.std(residuals)
            upper_bound = predictions + 2 * std_residuals
            lower_bound = predictions - 2 * std_residuals
            
            fig_pred.add_trace(go.Scatter(
                x=future_dates + future_dates[::-1],
                y=np.concatenate([upper_bound, lower_bound[::-1]]),
                fill='toself', fillcolor='rgba(255,0,0,0.2)',
                line=dict(color='rgba(255,0,0,0)'),
                name='Intervalle confiance 95%'
            ))
        
        fig_pred.update_layout(
            title=f"Prédictions pour {symbol} - {days_to_predict} jours",
            xaxis_title="Date (Paris UTC+2)",
            yaxis_title="Prix ($)",
            height=500,
            template='plotly_white'
        )
        
        st.plotly_chart(fig_pred, use_container_width=True)
        
        pred_df = pd.DataFrame({
            'Date': [d.strftime('%Y-%m-%d') for d in future_dates],
            'Prix prédit': [format_currency(p) for p in predictions],
            'Variation %': [f"{(p/current_price - 1)*100:+.2f}%" for p in predictions]
        })
        st.dataframe(pred_df, use_container_width=True)
        
        # Performance du modèle
        residuals = y - model.predict(X)
        rmse = np.sqrt(np.mean(residuals**2))
        mae = np.mean(np.abs(residuals))
        
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("RMSE", format_currency(rmse))
        col_m2.metric("MAE", format_currency(mae))
        col_m3.metric("R²", f"{model.score(X, y):.3f}")
        
        # Tendance
        last_pred = predictions[-1]
        trend = "HAUSSIÈRE 📈" if last_pred > current_price else "BAISSIÈRE 📉"
        st.info(f"**Tendance prévue:** {trend}")
        
    else:
        st.warning(f"Pas assez de données pour {symbol} (minimum 30 points)")

# ============================================================================
# SECTION 8: COMPARATIF NEWSPACE
# ============================================================================
elif menu == "📊 Comparatif NewSpace":
    st.subheader("📊 Comparatif des actions NewSpace")
    
    compare_symbols = st.multiselect(
        "Sélectionner les actions à comparer",
        st.session_state.watchlist,
        default=['RKLB', 'ASTS', 'PL', 'SPCE', 'TSLA']
    )
    
    if len(compare_symbols) >= 2:
        performance_data = []
        
        for sym in compare_symbols:
            hist_s, _ = load_stock_data(sym, "3mo", "1d")
            
            if hist_s is not None and not hist_s.empty:
                normalized = (hist_s['Close'] / hist_s['Close'].iloc[0] - 1) * 100
                performance_data.append({
                    'Symbole': sym,
                    'Date': hist_s.index,
                    'Performance %': normalized
                })
        
        if performance_data:
            fig_comp = go.Figure()
            
            for data in performance_data:
                fig_comp.add_trace(go.Scatter(
                    x=data['Date'], y=data['Performance %'],
                    mode='lines', name=data['Symbole'], line=dict(width=2)
                ))
            
            fig_comp.update_layout(
                title="Comparaison de performance (3 mois) - Normalisée à 100%",
                xaxis_title="Date (Paris UTC+2)",
                yaxis_title="Performance %",
                height=500,
                hovermode='x unified',
                template='plotly_white'
            )
            
            st.plotly_chart(fig_comp, use_container_width=True)
    
    # Corrélation
    if len(compare_symbols) >= 2:
        st.subheader("📊 Matrice de corrélation")
        
        corr_data = pd.DataFrame()
        for sym in compare_symbols:
            hist_s, _ = load_stock_data(sym, "1mo", "1d")
            if hist_s is not None and not hist_s.empty:
                corr_data[sym] = hist_s['Close']
        
        if not corr_data.empty:
            fig_corr = px.imshow(
                corr_data.corr(), text_auto=True,
                color_continuous_scale='RdBu',
                title="Corrélation des prix"
            )
            st.plotly_chart(fig_corr, use_container_width=True)

# ============================================================================
# WATCHLIST
# ============================================================================
st.markdown("---")
col_w1, col_w2 = st.columns([3, 1])

with col_w1:
    st.subheader("📋 Watchlist NewSpace")
    
    # Catégories
    launchers = [s for s in st.session_state.watchlist if SPACE_COMPANIES.get(s, {}).get('sector') == 'Lanceurs']
    satellites = [s for s in st.session_state.watchlist if SPACE_COMPANIES.get(s, {}).get('sector') == 'Satellites']
    imaging = [s for s in st.session_state.watchlist if SPACE_COMPANIES.get(s, {}).get('sector') == 'Imagerie']
    defense = [s for s in st.session_state.watchlist if SPACE_COMPANIES.get(s, {}).get('sector') == 'Défense']
    
    tabs = st.tabs(["🚀 Lanceurs", "🛰️ Satellites", "📸 Imagerie", "🛡️ Défense"])
    
    with tabs[0]:
        if launchers:
            cols = st.columns(min(len(launchers), 4))
            for i, sym in enumerate(launchers):
                with cols[i % 4]:
                    try:
                        ticker = yf.Ticker(sym)
                        hist = ticker.history(period='1d')
                        if not hist.empty:
                            price = hist['Close'].iloc[-1]
                            st.metric(sym, f"${price:.2f}")
                        else:
                            st.metric(sym, "N/A")
                    except:
                        st.metric(sym, "N/A")
        else:
            st.info("Aucune action lanceurs")
    
    with tabs[1]:
        if satellites:
            cols = st.columns(min(len(satellites), 4))
            for i, sym in enumerate(satellites):
                with cols[i % 4]:
                    try:
                        ticker = yf.Ticker(sym)
                        hist = ticker.history(period='1d')
                        if not hist.empty:
                            price = hist['Close'].iloc[-1]
                            st.metric(sym, f"${price:.2f}")
                        else:
                            st.metric(sym, "N/A")
                    except:
                        st.metric(sym, "N/A")
        else:
            st.info("Aucune action satellites")
    
    with tabs[2]:
        if imaging:
            cols = st.columns(min(len(imaging), 4))
            for i, sym in enumerate(imaging):
                with cols[i % 4]:
                    try:
                        ticker = yf.Ticker(sym)
                        hist = ticker.history(period='1d')
                        if not hist.empty:
                            price = hist['Close'].iloc[-1]
                            st.metric(sym, f"${price:.2f}")
                        else:
                            st.metric(sym, "N/A")
                    except:
                        st.metric(sym, "N/A")
        else:
            st.info("Aucune action imagerie")
    
    with tabs[3]:
        if defense:
            cols = st.columns(min(len(defense), 4))
            for i, sym in enumerate(defense):
                with cols[i % 4]:
                    try:
                        ticker = yf.Ticker(sym)
                        hist = ticker.history(period='1d')
                        if not hist.empty:
                            price = hist['Close'].iloc[-1]
                            st.metric(sym, f"${price:.2f}")
                        else:
                            st.metric(sym, "N/A")
                    except:
                        st.metric(sym, "N/A")
        else:
            st.info("Aucune action défense")

with col_w2:
    paris_time = datetime.now(USER_TIMEZONE)
    ny_time = datetime.now(US_TIMEZONE)
    
    st.caption(f"🇫🇷 Paris: {paris_time.strftime('%H:%M:%S')}")
    st.caption(f"🇺🇸 NY: {ny_time.strftime('%H:%M:%S')}")
    
    if auto_refresh and hist is not None and not hist.empty:
        time.sleep(refresh_rate)
        st.rerun()

# Footer
st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: gray; font-size: 0.8rem;'>"
    "🚀 SpaceX & NewSpace Tracker - Données yfinance | Scores basés sur: Financier, Technique, Spatial, Croissance, Risque | "
    "⚠️ Données avec délai possible | 🕐 Heure Paris UTC+2"
    "</p>",
    unsafe_allow_html=True
)
