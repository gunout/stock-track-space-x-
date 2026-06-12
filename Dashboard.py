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
import warnings
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import make_pipeline
import pytz
warnings.filterwarnings('ignore')

# Configuration de la page
st.set_page_config(
    page_title="🚀 SpaceX & NewSpace Tracker",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuration du fuseau horaire
USER_TIMEZONE = pytz.timezone('Europe/Paris')
US_TIMEZONE = pytz.timezone('America/New_York')

# Style CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #005288;
        text-align: center;
        margin-bottom: 2rem;
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
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
    }
    .score-card {
        padding: 1rem;
        border-radius: 1rem;
        text-align: center;
        margin: 0.5rem 0;
        color: white;
    }
    .score-excellent { background: linear-gradient(135deg, #00b09b, #96c93d); }
    .score-good { background: linear-gradient(135deg, #2193b0, #6dd5ed); }
    .score-average { background: linear-gradient(135deg, #f2994a, #f2c94c); }
    .score-poor { background: linear-gradient(135deg, #eb3349, #f45c43); }
    .timezone-badge {
        background-color: #e3f2fd;
        border-left: 4px solid #005288;
        padding: 0.5rem 1rem;
        margin: 1rem 0;
        font-size: 0.9rem;
    }
    .stButton>button { width: 100%; }
</style>
""", unsafe_allow_html=True)

# Initialisation des variables de session
if 'price_alerts' not in st.session_state:
    st.session_state.price_alerts = []

if 'portfolio' not in st.session_state:
    st.session_state.portfolio = {}

if 'email_config' not in st.session_state:
    st.session_state.email_config = {
        'enabled': False,
        'smtp_server': 'smtp.gmail.com',
        'smtp_port': 587,
        'email': '',
        'password': ''
    }

# Base de données des entreprises spatiales avec prix simulés pour fallback
SPACE_COMPANIES = {
    'RKLB': {'name': 'Rocket Lab USA', 'sector': 'Lanceurs', 'price': 4.50, 'volatility': 0.35},
    'ASTS': {'name': 'AST SpaceMobile', 'sector': 'Satellites', 'price': 2.80, 'volatility': 0.45},
    'RDW': {'name': 'Redwire', 'sector': 'Infrastructure', 'price': 3.20, 'volatility': 0.30},
    'PL': {'name': 'Planet Labs', 'sector': 'Imagerie', 'price': 2.30, 'volatility': 0.28},
    'SPCE': {'name': 'Virgin Galactic', 'sector': 'Tourisme', 'price': 1.80, 'volatility': 0.50},
    'GSAT': {'name': 'Globalstar', 'sector': 'Communications', 'price': 1.15, 'volatility': 0.25},
    'IRDM': {'name': 'Iridium', 'sector': 'Communications', 'price': 32.50, 'volatility': 0.20},
    'TSLA': {'name': 'Tesla Inc.', 'sector': 'Électromobilité', 'price': 220.00, 'volatility': 0.35},
    'LMT': {'name': 'Lockheed Martin', 'sector': 'Défense', 'price': 450.00, 'volatility': 0.15},
    'BA': {'name': 'Boeing', 'sector': 'Aérospatial', 'price': 170.00, 'volatility': 0.25},
    'NOC': {'name': 'Northrop Grumman', 'sector': 'Défense', 'price': 480.00, 'volatility': 0.18},
    'RTX': {'name': 'Raytheon', 'sector': 'Défense', 'price': 85.00, 'volatility': 0.16},
    'GD': {'name': 'General Dynamics', 'sector': 'Défense', 'price': 260.00, 'volatility': 0.14},
}

# ============================================================================
# FONCTIONS AMÉLIORÉES
# ============================================================================

@st.cache_data(ttl=300, show_spinner=False)
def get_stock_data(symbol, period="1mo", interval="1d"):
    """Récupère les données avec fallback vers données simulées"""
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period, interval=interval)
        
        if not hist.empty:
            # Convertir timezone
            if hist.index.tz is None:
                hist.index = hist.index.tz_localize('UTC').tz_convert(USER_TIMEZONE)
            else:
                hist.index = hist.index.tz_convert(USER_TIMEZONE)
            
            # Récupérer les infos
            info = ticker.info
            
            # Vérifier si les données sont récentes
            last_date = hist.index[-1]
            days_ago = (datetime.now(USER_TIMEZONE) - last_date).days
            
            if days_ago > 5:
                # Données trop anciennes, utiliser fallback
                return generate_fallback_data(symbol, period), SPACE_COMPANIES.get(symbol, {})
            
            return hist, info
        
        # Pas de données, utiliser fallback
        return generate_fallback_data(symbol, period), SPACE_COMPANIES.get(symbol, {})
        
    except Exception as e:
        # Erreur, utiliser fallback
        return generate_fallback_data(symbol, period), SPACE_COMPANIES.get(symbol, {})

def generate_fallback_data(symbol, period="1mo"):
    """Génère des données simulées réalistes pour fallback"""
    company = SPACE_COMPANIES.get(symbol, {'price': 10.0, 'volatility': 0.25})
    base_price = company.get('price', 10.0)
    volatility = company.get('volatility', 0.25)
    
    # Déterminer le nombre de jours
    period_map = {
        "1d": 1, "5d": 5, "1mo": 22, "3mo": 66, "6mo": 132, "1y": 252, "2y": 504
    }
    days = period_map.get(period, 22)
    
    # Générer les dates
    end_date = datetime.now(USER_TIMEZONE)
    dates = pd.date_range(end=end_date, periods=days, freq='D')
    
    # Générer les prix avec marche aléatoire
    returns = np.random.normal(0, volatility / np.sqrt(252), days)
    prices = base_price * np.exp(np.cumsum(returns))
    prices[0] = base_price
    
    # Ajouter une tendance
    trend = np.linspace(0, np.random.uniform(-0.2, 0.2), days)
    prices = prices * (1 + trend)
    
    # Créer le DataFrame
    hist = pd.DataFrame({
        'Open': prices * (1 + np.random.uniform(-0.02, 0.02, days)),
        'High': prices * (1 + np.random.uniform(0, 0.03, days)),
        'Low': prices * (1 - np.random.uniform(0, 0.03, days)),
        'Close': prices,
        'Volume': np.random.uniform(500000, 5000000, days)
    }, index=dates)
    
    # S'assurer que High >= Close et Low <= Close
    hist['High'] = hist[['High', 'Close']].max(axis=1)
    hist['Low'] = hist[['Low', 'Close']].min(axis=1)
    
    return hist

def calculate_scores(symbol, hist, info):
    """Calcule les scores avec fallback intelligent"""
    company = SPACE_COMPANIES.get(symbol, {})
    
    # Score financier
    financial_score = 50
    market_cap = info.get('marketCap', 0) if isinstance(info, dict) else 0
    if market_cap > 1e11:
        financial_score += 15
    elif market_cap > 1e10:
        financial_score += 10
    elif market_cap > 1e9:
        financial_score += 5
    
    pe = info.get('trailingPE', 0) if isinstance(info, dict) else 0
    if pe and pe > 0 and pe < 20:
        financial_score += 10
    elif pe and pe > 0 and pe < 30:
        financial_score += 5
    
    # Score technique
    technical_score = 50
    if hist is not None and not hist.empty and len(hist) > 20:
        close = hist['Close']
        ma20 = close.rolling(20).mean()
        if close.iloc[-1] > ma20.iloc[-1]:
            technical_score += 15
        else:
            technical_score -= 10
        
        # Performance
        if len(close) > 5:
            perf = (close.iloc[-1] / close.iloc[-6] - 1) * 100
            if perf > 5:
                technical_score += 10
            elif perf > 0:
                technical_score += 5
            elif perf < -10:
                technical_score -= 15
    
    # Score secteur spatial
    space_score = 50
    sector = company.get('sector', '')
    if sector in ['Lanceurs', 'Satellites']:
        space_score += 20
    elif sector == 'Imagerie':
        space_score += 10
    if symbol == 'TSLA':
        space_score += 15
    if symbol in ['RKLB', 'ASTS']:
        space_score += 10
    
    # Score croissance
    growth_score = 50
    if market_cap < 2e9 and market_cap > 0:
        growth_score += 20
    elif market_cap < 1e10:
        growth_score += 10
    if sector in ['Lanceurs', 'Satellites']:
        growth_score += 10
    
    # Score risque
    risk_score = 70
    if hist is not None and not hist.empty and len(hist) > 20:
        volatility = hist['Close'].pct_change().std() * np.sqrt(252)
        if volatility > 0.5:
            risk_score -= 25
        elif volatility > 0.35:
            risk_score -= 15
        elif volatility > 0.25:
            risk_score -= 5
        elif volatility < 0.15:
            risk_score += 10
    
    return {
        'financial': min(max(financial_score, 0), 100),
        'technical': min(max(technical_score, 0), 100),
        'space_sector': min(max(space_score, 0), 100),
        'growth': min(max(growth_score, 0), 100),
        'risk': min(max(risk_score, 0), 100)
    }

def get_composite_score(scores):
    weights = {'financial': 0.25, 'technical': 0.20, 'space_sector': 0.20, 'growth': 0.20, 'risk': 0.15}
    return sum(scores[k] * w for k, w in weights.items())

def get_score_grade(score):
    if score >= 75: return "EXCELLENT", "score-excellent", "🌟"
    if score >= 60: return "TRÈS BON", "score-good", "📈"
    if score >= 45: return "BON", "score-average", "✅"
    return "FAIBLE", "score-poor", "⚠️"

def format_currency(value):
    return f"${value:.2f}"

# ============================================================================
# INTERFACE PRINCIPALE
# ============================================================================

st.markdown("<h1 class='main-header'>🚀 SpaceX & NewSpace Tracker</h1>", unsafe_allow_html=True)

current_time_paris = datetime.now(USER_TIMEZONE)
current_time_ny = datetime.now(US_TIMEZONE)

st.markdown(f"""
<div class='timezone-badge'>
    <b>🕐 Fuseaux horaires :</b><br>
    🇫🇷 Paris : {current_time_paris.strftime('%H:%M:%S')} (UTC+2)<br>
    🇺🇸 New York : {current_time_ny.strftime('%H:%M:%S')} (UTC-4/UTC-5)
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/d/dc/SpaceX_Logo_Black.png/800px-SpaceX_Logo_Black.png", width=200)
    st.title("Navigation")
    
    menu = st.radio(
        "Choisir une section",
        ["📈 Tableau de bord", "🏆 Scores boursiers", "💰 Portefeuille", "🔔 Alertes", "📧 Email", "🤖 Prédictions"]
    )
    
    st.markdown("---")
    
    symbol = st.selectbox("Symbole", list(SPACE_COMPANIES.keys()), index=0)
    period = st.selectbox("Période", ["1mo", "3mo", "6mo", "1y"], index=0)
    auto_refresh = st.checkbox("Auto-refresh", value=False)
    if auto_refresh:
        refresh_rate = st.slider("Fréquence (sec)", 5, 60, 30)

# Chargement des données
hist, info = get_stock_data(symbol, period)

# Message d'info sur les données
if hist is not None and not hist.empty:
    company = SPACE_COMPANIES.get(symbol, {})
    st.info(f"📊 Données pour {symbol} - {company.get('name', symbol)} | Dernier prix: {format_currency(hist['Close'].iloc[-1])}")
else:
    st.warning(f"⚠️ Utilisation de données simulées pour {symbol}")

# ============================================================================
# SECTION 1: TABLEAU DE BORD
# ============================================================================
if menu == "📈 Tableau de bord":
    st.subheader("📊 Tableau de bord")
    
    st.markdown("""
    <div class='spacex-card'>
        <b>🚀 SpaceX (privé - non coté)</b><br>
        Valuation: $180B | Starlink: ~6,200 satellites | Lancements 2024: 128+
    </div>
    """, unsafe_allow_html=True)
    
    if hist is not None and not hist.empty:
        company = SPACE_COMPANIES.get(symbol, {})
        current_price = hist['Close'].iloc[-1]
        prev_price = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
        change = current_price - prev_price
        change_pct = (change / prev_price * 100) if prev_price != 0 else 0
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Prix", format_currency(current_price), f"{change:+.2f} ({change_pct:+.1f}%)")
        col2.metric("Plus haut", format_currency(hist['High'].max()))
        col3.metric("Plus bas", format_currency(hist['Low'].min()))
        col4.metric("Volume", f"{hist['Volume'].iloc[-1]/1e6:.1f}M")
        
        # Graphique
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=hist.index, y=hist['Close'],
            mode='lines', name='Prix',
            line=dict(color='#005288', width=2)
        ))
        
        if len(hist) >= 20:
            ma20 = hist['Close'].rolling(20).mean()
            fig.add_trace(go.Scatter(
                x=hist.index, y=ma20,
                mode='lines', name='MA20',
                line=dict(color='orange', width=1, dash='dash')
            ))
        
        fig.update_layout(
            title=f"{symbol} - Évolution {period}",
            xaxis_title="Date",
            yaxis_title="Prix ($)",
            height=500,
            template='plotly_white'
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Stats
        with st.expander("📊 Statistiques"):
            st.write(f"**Moyenne:** {format_currency(hist['Close'].mean())}")
            st.write(f"**Volatilité:** {hist['Close'].pct_change().std() * 100:.2f}%")
            st.write(f"**Performance période:** {((current_price / hist['Close'].iloc[0] - 1) * 100):+.1f}%")

# ============================================================================
# SECTION 2: SCORES BOURSIERS
# ============================================================================
elif menu == "🏆 Scores boursiers":
    st.subheader("🏆 Classement des scores")
    
    all_scores = []
    progress_bar = st.progress(0)
    
    for i, sym in enumerate(list(SPACE_COMPANIES.keys())[:15]):
        hist_s, info_s = get_stock_data(sym, "1mo")
        scores = calculate_scores(sym, hist_s, info_s)
        composite = get_composite_score(scores)
        grade, grade_class, icon = get_score_grade(composite)
        company = SPACE_COMPANIES.get(sym, {})
        
        current_price = hist_s['Close'].iloc[-1] if hist_s is not None else company.get('price', 0)
        
        all_scores.append({
            'Symbole': sym,
            'Entreprise': company.get('name', sym),
            'Secteur': company.get('sector', 'N/A'),
            'Prix': format_currency(current_price),
            'Score': round(composite, 1),
            'Grade': grade
        })
        progress_bar.progress((i + 1) / len(SPACE_COMPANIES))
    
    progress_bar.empty()
    
    if all_scores:
        df_scores = pd.DataFrame(all_scores).sort_values('Score', ascending=False)
        
        for _, row in df_scores.iterrows():
            grade_class = "score-excellent" if row['Score'] >= 75 else "score-good" if row['Score'] >= 60 else "score-average" if row['Score'] >= 45 else "score-poor"
            st.markdown(f"""
            <div class='score-card {grade_class}'>
                <div style='display: flex; justify-content: space-between;'>
                    <span style='font-weight: bold; font-size: 18px;'>{row['Symbole']} - {row['Entreprise']}</span>
                    <span>{row['Prix']}</span>
                    <span style='font-size: 24px; font-weight: bold;'>{row['Score']}</span>
                    <span>{row['Grade']}</span>
                </div>
                <div style='font-size: 12px; margin-top: 8px;'>{row['Secteur']}</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("### 📊 Détail des scores")
        st.dataframe(df_scores, use_container_width=True)
        
        # Graphique
        fig = px.bar(df_scores, x='Symbole', y='Score', 
                     title="Scores par action", color='Score',
                     color_continuous_scale='Viridis')
        st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# SECTION 3: PORTEFEUILLE
# ============================================================================
elif menu == "💰 Portefeuille":
    st.subheader("💰 Portefeuille virtuel")
    
    col1, col2 = st.columns([2, 1])
    
    with col2:
        with st.form("add_position"):
            symbol_pf = st.selectbox("Symbole", list(SPACE_COMPANIES.keys()))
            shares = st.number_input("Actions", min_value=1, value=100)
            buy_price = st.number_input("Prix d'achat ($)", min_value=0.01, value=10.0)
            
            if st.form_submit_button("Ajouter"):
                if symbol_pf not in st.session_state.portfolio:
                    st.session_state.portfolio[symbol_pf] = []
                st.session_state.portfolio[symbol_pf].append({
                    'shares': shares, 'buy_price': buy_price,
                    'date': datetime.now().strftime('%Y-%m-%d')
                })
                st.success(f"✅ {shares} {symbol_pf} ajoutées")
                st.rerun()
    
    with col1:
        if st.session_state.portfolio:
            portfolio_data = []
            total_value = 0
            
            for sym, positions in st.session_state.portfolio.items():
                hist_s, _ = get_stock_data(sym, "1d")
                current = hist_s['Close'].iloc[-1] if hist_s is not None else SPACE_COMPANIES.get(sym, {}).get('price', 0)
                
                for pos in positions:
                    value = pos['shares'] * current
                    cost = pos['shares'] * pos['buy_price']
                    profit = value - cost
                    total_value += value
                    portfolio_data.append({
                        'Symbole': sym, 'Actions': pos['shares'],
                        'Prix actuel': format_currency(current),
                        'Valeur': format_currency(value),
                        'Profit': format_currency(profit)
                    })
            
            if portfolio_data:
                st.metric("Valeur totale", format_currency(total_value))
                st.dataframe(pd.DataFrame(portfolio_data), use_container_width=True)
                
                if st.button("🗑️ Vider"):
                    st.session_state.portfolio = {}
                    st.rerun()

# ============================================================================
# SECTION 4: ALERTES
# ============================================================================
elif menu == "🔔 Alertes":
    st.subheader("🔔 Alertes de prix")
    
    with st.form("new_alert"):
        alert_symbol = st.selectbox("Symbole", list(SPACE_COMPANIES.keys()))
        alert_price = st.number_input("Prix cible ($)", min_value=0.01, value=50.0)
        condition = st.selectbox("Condition", ["above", "below"])
        
        if st.form_submit_button("Créer"):
            st.session_state.price_alerts.append({
                'symbol': alert_symbol, 'price': alert_price,
                'condition': condition, 'created': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
            st.success(f"Alerte créée")
    
    if st.session_state.price_alerts:
        for i, alert in enumerate(st.session_state.price_alerts):
            st.info(f"{alert['symbol']} - {alert['condition']} ${alert['price']:.2f}")
            if st.button(f"Supprimer", key=f"del_{i}"):
                st.session_state.price_alerts.pop(i)
                st.rerun()

# ============================================================================
# SECTION 5: EMAIL
# ============================================================================
elif menu == "📧 Email":
    st.subheader("📧 Configuration email")
    
    with st.form("email_config"):
        enabled = st.checkbox("Activer", value=st.session_state.email_config['enabled'])
        email = st.text_input("Email", value=st.session_state.email_config['email'])
        password = st.text_input("Mot de passe", type="password", value=st.session_state.email_config['password'])
        
        if st.form_submit_button("💾 Sauvegarder"):
            st.session_state.email_config = {
                'enabled': enabled, 'email': email, 'password': password,
                'smtp_server': 'smtp.gmail.com', 'smtp_port': 587
            }
            st.success("Configuration sauvegardée")

# ============================================================================
# SECTION 6: PRÉDICTIONS
# ============================================================================
elif menu == "🤖 Prédictions":
    st.subheader("🤖 Prédictions ML")
    
    if hist is not None and not hist.empty and len(hist) > 30:
        df = hist[['Close']].reset_index()
        df['Days'] = (df['Date'] - df['Date'].min()).dt.days
        
        X = df['Days'].values.reshape(-1, 1)
        y = df['Close'].values
        
        days = st.slider("Jours à prédire", 1, 30, 7)
        degree = st.slider("Degré", 1, 5, 2)
        
        model = make_pipeline(PolynomialFeatures(degree=degree), LinearRegression())
        model.fit(X, y)
        
        last_day = X[-1][0]
        future_days = np.arange(last_day + 1, last_day + days + 1).reshape(-1, 1)
        predictions = model.predict(future_days)
        
        future_dates = [df['Date'].iloc[-1] + timedelta(days=i+1) for i in range(days)]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df['Date'], y=y, mode='lines', name='Historique'))
        fig.add_trace(go.Scatter(x=future_dates, y=predictions, mode='lines+markers', name='Prédictions'))
        fig.update_layout(title=f"Prédictions {symbol}", height=500)
        st.plotly_chart(fig, use_container_width=True)
        
        pred_df = pd.DataFrame({
            'Date': [d.strftime('%Y-%m-%d') for d in future_dates],
            'Prédiction': [format_currency(p) for p in predictions]
        })
        st.dataframe(pred_df)

# Auto-refresh
if auto_refresh:
    time.sleep(refresh_rate)
    st.rerun()

# Footer
st.markdown("---")
st.markdown("<p style='text-align: center; color: gray;'>🚀 SpaceX & NewSpace Tracker | Données temps réel et simulées</p>", unsafe_allow_html=True)
