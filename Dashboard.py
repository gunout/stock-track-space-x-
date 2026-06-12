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
    .success-message {
        background-color: #d4edda;
        color: #155724;
        padding: 0.75rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
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

# Base de données des entreprises spatiales
SPACE_COMPANIES = {
    'RKLB': {'name': 'Rocket Lab USA', 'sector': 'Lanceurs', 'price': 4.50, 'volatility': 0.35, 'market_cap': 2.1e9},
    'ASTS': {'name': 'AST SpaceMobile', 'sector': 'Satellites', 'price': 2.80, 'volatility': 0.45, 'market_cap': 0.8e9},
    'RDW': {'name': 'Redwire', 'sector': 'Infrastructure', 'price': 3.20, 'volatility': 0.30, 'market_cap': 0.3e9},
    'PL': {'name': 'Planet Labs', 'sector': 'Imagerie', 'price': 2.30, 'volatility': 0.28, 'market_cap': 0.6e9},
    'SPCE': {'name': 'Virgin Galactic', 'sector': 'Tourisme', 'price': 1.80, 'volatility': 0.50, 'market_cap': 0.5e9},
    'GSAT': {'name': 'Globalstar', 'sector': 'Communications', 'price': 1.15, 'volatility': 0.25, 'market_cap': 2.2e9},
    'IRDM': {'name': 'Iridium', 'sector': 'Communications', 'price': 32.50, 'volatility': 0.20, 'market_cap': 4.5e9},
    'TSLA': {'name': 'Tesla Inc.', 'sector': 'Électromobilité', 'price': 220.00, 'volatility': 0.35, 'market_cap': 700e9},
    'LMT': {'name': 'Lockheed Martin', 'sector': 'Défense', 'price': 450.00, 'volatility': 0.15, 'market_cap': 110e9},
    'BA': {'name': 'Boeing', 'sector': 'Aérospatial', 'price': 170.00, 'volatility': 0.25, 'market_cap': 100e9},
    'NOC': {'name': 'Northrop Grumman', 'sector': 'Défense', 'price': 480.00, 'volatility': 0.18, 'market_cap': 70e9},
    'RTX': {'name': 'Raytheon', 'sector': 'Défense', 'price': 85.00, 'volatility': 0.16, 'market_cap': 120e9},
    'GD': {'name': 'General Dynamics', 'sector': 'Défense', 'price': 260.00, 'volatility': 0.14, 'market_cap': 70e9},
}

# ============================================================================
# FONCTIONS
# ============================================================================

@st.cache_data(ttl=300, show_spinner=False)
def get_stock_data(symbol, period="1mo", interval="1d"):
    """Récupère les données avec fallback"""
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period, interval=interval)
        
        if not hist.empty:
            # Convertir timezone
            if hist.index.tz is None:
                hist.index = hist.index.tz_localize('UTC').tz_convert(USER_TIMEZONE)
            else:
                hist.index = hist.index.tz_convert(USER_TIMEZONE)
            
            info = ticker.info
            return hist, info
        
        return generate_fallback_data(symbol, period), SPACE_COMPANIES.get(symbol, {})
        
    except Exception as e:
        return generate_fallback_data(symbol, period), SPACE_COMPANIES.get(symbol, {})

def generate_fallback_data(symbol, period="1mo"):
    """Génère des données simulées"""
    company = SPACE_COMPANIES.get(symbol, {'price': 10.0, 'volatility': 0.25})
    base_price = company.get('price', 10.0)
    volatility = company.get('volatility', 0.25)
    
    period_days = {"1d": 1, "5d": 5, "1mo": 22, "3mo": 66, "6mo": 132, "1y": 252}
    days = period_days.get(period, 22)
    
    end_date = datetime.now(USER_TIMEZONE)
    dates = pd.date_range(end=end_date, periods=days, freq='D')
    
    # Génération des prix
    returns = np.random.normal(0, volatility / np.sqrt(252), days)
    prices = base_price * np.exp(np.cumsum(returns))
    prices[0] = base_price
    
    hist = pd.DataFrame({
        'Open': prices * (1 + np.random.uniform(-0.02, 0.02, days)),
        'High': prices * (1 + np.random.uniform(0, 0.03, days)),
        'Low': prices * (1 - np.random.uniform(0, 0.03, days)),
        'Close': prices,
        'Volume': np.random.uniform(500000, 5000000, days)
    }, index=dates)
    
    # Corriger les extrêmes
    hist['High'] = hist[['High', 'Close']].max(axis=1)
    hist['Low'] = hist[['Low', 'Close']].min(axis=1)
    
    return hist

def calculate_scores(symbol, hist, info):
    """Calcule les scores"""
    company = SPACE_COMPANIES.get(symbol, {})
    
    # Score financier
    financial_score = 50
    market_cap = info.get('marketCap', company.get('market_cap', 0)) if isinstance(info, dict) else company.get('market_cap', 0)
    
    if market_cap > 1e11:
        financial_score += 15
    elif market_cap > 1e10:
        financial_score += 10
    elif market_cap > 1e9:
        financial_score += 5
    
    # Score technique
    technical_score = 50
    if hist is not None and not hist.empty and len(hist) > 20:
        close = hist['Close']
        ma20 = close.rolling(20).mean()
        if len(ma20) > 0 and close.iloc[-1] > ma20.iloc[-1]:
            technical_score += 15
        else:
            technical_score -= 10
        
        if len(close) > 5:
            perf = (close.iloc[-1] / close.iloc[-6] - 1) * 100
            if perf > 5:
                technical_score += 10
            elif perf > 0:
                technical_score += 5
            elif perf < -10:
                technical_score -= 15
    
    # Score secteur
    space_score = 50
    sector = company.get('sector', '')
    if sector in ['Lanceurs', 'Satellites']:
        space_score += 20
    elif sector == 'Imagerie':
        space_score += 10
    if symbol == 'TSLA':
        space_score += 15
    
    # Score croissance
    growth_score = 50
    if market_cap < 2e9 and market_cap > 0:
        growth_score += 20
    elif market_cap < 1e10:
        growth_score += 10
    
    # Score risque
    risk_score = 70
    if hist is not None and not hist.empty and len(hist) > 10:
        volatility = hist['Close'].pct_change().std() * np.sqrt(252)
        if not np.isnan(volatility):
            if volatility > 0.5:
                risk_score -= 25
            elif volatility > 0.35:
                risk_score -= 15
            elif volatility > 0.25:
                risk_score -= 5
            elif volatility < 0.15:
                risk_score += 10
    
    return {
        'financial': max(0, min(financial_score, 100)),
        'technical': max(0, min(technical_score, 100)),
        'space_sector': max(0, min(space_score, 100)),
        'growth': max(0, min(growth_score, 100)),
        'risk': max(0, min(risk_score, 100))
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
        server.login(st.session_state.email_config['email'], st.session_state.email_config['password'])
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        return False

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

if hist is not None and not hist.empty:
    company = SPACE_COMPANIES.get(symbol, {})
    current_price = hist['Close'].iloc[-1]
    st.success(f"✅ Données chargées pour {symbol} - {company.get('name', symbol)} | Prix: {format_currency(current_price)}")

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
    
    symbols = list(SPACE_COMPANIES.keys())
    for i, sym in enumerate(symbols):
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
        progress_bar.progress((i + 1) / len(symbols))
    
    progress_bar.empty()
    
    if all_scores:
        df_scores = pd.DataFrame(all_scores).sort_values('Score', ascending=False)
        
        for _, row in df_scores.iterrows():
            grade_class = "score-excellent" if row['Score'] >= 75 else "score-good" if row['Score'] >= 60 else "score-average" if row['Score'] >= 45 else "score-poor"
            st.markdown(f"""
            <div class='score-card {grade_class}'>
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <div style='flex: 2'>
                        <span style='font-weight: bold; font-size: 18px;'>{row['Symbole']}</span>
                        <br><span style='font-size: 12px;'>{row['Entreprise']}</span>
                    </div>
                    <div style='flex: 1'>{row['Prix']}</div>
                    <div style='flex: 0.5; text-align: center;'>
                        <span style='font-size: 28px; font-weight: bold;'>{row['Score']}</span>
                        <br><span style='font-size: 12px;'>{row['Grade']}</span>
                    </div>
                    <div style='flex: 1'>{row['Secteur']}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("### 📊 Détail des scores")
        st.dataframe(df_scores, use_container_width=True, height=400)
        
        # Graphique
        fig = px.bar(df_scores, x='Symbole', y='Score', 
                     title="Scores par action", color='Score',
                     color_continuous_scale='Viridis', height=500)
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
            shares = st.number_input("Actions", min_value=1, value=100, step=10)
            buy_price = st.number_input("Prix d'achat ($)", min_value=0.01, value=10.0, step=1.0)
            
            if st.form_submit_button("➕ Ajouter"):
                if symbol_pf not in st.session_state.portfolio:
                    st.session_state.portfolio[symbol_pf] = []
                st.session_state.portfolio[symbol_pf].append({
                    'shares': shares, 
                    'buy_price': buy_price,
                    'date': datetime.now().strftime('%Y-%m-%d')
                })
                st.markdown(f"<div class='success-message'>✅ {shares} actions {symbol_pf} ajoutées</div>", unsafe_allow_html=True)
                time.sleep(1)
                st.rerun()
    
    with col1:
        if st.session_state.portfolio:
            portfolio_data = []
            total_value = 0
            total_cost = 0
            
            for sym, positions in st.session_state.portfolio.items():
                hist_s, _ = get_stock_data(sym, "1d")
                current = hist_s['Close'].iloc[-1] if hist_s is not None else SPACE_COMPANIES.get(sym, {}).get('price', 0)
                
                for pos in positions:
                    value = pos['shares'] * current
                    cost = pos['shares'] * pos['buy_price']
                    profit = value - cost
                    profit_pct = (profit / cost * 100) if cost > 0 else 0
                    
                    total_value += value
                    total_cost += cost
                    
                    portfolio_data.append({
                        'Symbole': sym,
                        'Actions': pos['shares'],
                        'Prix achat': format_currency(pos['buy_price']),
                        'Prix actuel': format_currency(current),
                        'Valeur': format_currency(value),
                        'Profit': format_currency(profit),
                        'Profit %': f"{profit_pct:+.1f}%"
                    })
            
            if portfolio_data:
                total_profit = total_value - total_cost
                total_profit_pct = (total_profit / total_cost * 100) if total_cost > 0 else 0
                
                col_a, col_b, col_c = st.columns(3)
                col_a.metric("Valeur totale", format_currency(total_value))
                col_b.metric("Coût total", format_currency(total_cost))
                col_c.metric("Profit total", format_currency(total_profit), delta=f"{total_profit_pct:+.1f}%")
                
                df_portfolio = pd.DataFrame(portfolio_data)
                st.dataframe(df_portfolio, use_container_width=True)
                
                if st.button("🗑️ Vider le portefeuille", use_container_width=True):
                    st.session_state.portfolio = {}
                    st.rerun()
        else:
            st.info("💡 Aucune position. Ajoutez des actions pour commencer !")

# ============================================================================
# SECTION 4: ALERTES
# ============================================================================
elif menu == "🔔 Alertes":
    st.subheader("🔔 Alertes de prix")
    
    col1, col2 = st.columns(2)
    
    with col1:
        with st.form("new_alert"):
            alert_symbol = st.selectbox("Symbole", list(SPACE_COMPANIES.keys()))
            alert_price = st.number_input("Prix cible ($)", min_value=0.01, value=50.0, step=5.0)
            condition = st.selectbox("Condition", ["above (au-dessus)", "below (en-dessous)"])
            condition = condition.split()[0]
            
            if st.form_submit_button("🔔 Créer l'alerte"):
                st.session_state.price_alerts.append({
                    'symbol': alert_symbol,
                    'price': alert_price,
                    'condition': condition,
                    'created': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
                st.success(f"✅ Alerte créée pour {alert_symbol} à ${alert_price:.2f}")
    
    with col2:
        st.markdown("### 📋 Alertes actives")
        if st.session_state.price_alerts:
            for i, alert in enumerate(st.session_state.price_alerts):
                st.info(f"🔔 {alert['symbol']} - {alert['condition']} ${alert['price']:.2f}")
                if st.button(f"Supprimer", key=f"del_{i}"):
                    st.session_state.price_alerts.pop(i)
                    st.rerun()
        else:
            st.info("Aucune alerte active")

# ============================================================================
# SECTION 5: EMAIL
# ============================================================================
elif menu == "📧 Email":
    st.subheader("📧 Configuration email")
    
    with st.form("email_config"):
        enabled = st.checkbox("Activer les notifications", value=st.session_state.email_config['enabled'])
        email = st.text_input("Adresse email", value=st.session_state.email_config['email'])
        password = st.text_input("Mot de passe", type="password", value=st.session_state.email_config['password'])
        test_email = st.text_input("Email de test (optionnel)")
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.form_submit_button("💾 Sauvegarder"):
                st.session_state.email_config = {
                    'enabled': enabled,
                    'email': email,
                    'password': password,
                    'smtp_server': 'smtp.gmail.com',
                    'smtp_port': 587
                }
                st.success("Configuration sauvegardée !")
        
        with col_btn2:
            if st.form_submit_button("📨 Tester"):
                if test_email:
                    if send_email_alert(
                        "Test SpaceX Tracker",
                        "<h2>✅ Test réussi !</h2><p>Votre configuration email fonctionne.</p>",
                        test_email
                    ):
                        st.success("Email de test envoyé !")
                    else:
                        st.error("Échec de l'envoi")

# ============================================================================
# SECTION 6: PRÉDICTIONS (CORRIGÉE)
# ============================================================================
elif menu == "🤖 Prédictions":
    st.subheader("🤖 Prédictions ML")
    
    if hist is not None and not hist.empty and len(hist) > 30:
        # CRITIQUE: Créer un DataFrame avec une colonne 'Date' explicite
        hist_reset = hist.reset_index()
        
        # Vérifier le nom de la colonne date
        date_col = hist_reset.columns[0]  # La première colonne est la date
        hist_reset['Days'] = (hist_reset[date_col] - hist_reset[date_col].min()).dt.days
        
        X = hist_reset['Days'].values.reshape(-1, 1)
        y = hist_reset['Close'].values
        
        col1, col2 = st.columns(2)
        with col1:
            days_to_predict = st.slider("Jours à prédire", 1, 30, 7)
            degree = st.slider("Degré du polynôme", 1, 4, 2)
        
        with col2:
            show_confidence = st.checkbox("Afficher intervalle de confiance", value=True)
        
        # Modèle
        model = make_pipeline(PolynomialFeatures(degree=degree), LinearRegression())
        model.fit(X, y)
        
        # Prédictions
        last_day = X[-1][0]
        future_days = np.arange(last_day + 1, last_day + days_to_predict + 1).reshape(-1, 1)
        predictions = model.predict(future_days)
        
        # Dates futures
        last_date = hist_reset[date_col].iloc[-1]
        future_dates = [last_date + timedelta(days=i+1) for i in range(days_to_predict)]
        
        # Graphique
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=hist_reset[date_col], y=y,
            mode='lines', name='Historique',
            line=dict(color='blue', width=2)
        ))
        fig.add_trace(go.Scatter(
            x=future_dates, y=predictions,
            mode='lines+markers', name='Prédictions',
            line=dict(color='red', width=2, dash='dash'),
            marker=dict(size=8, color='red')
        ))
        
        if show_confidence:
            residuals = y - model.predict(X)
            std_residuals = np.std(residuals)
            upper_bound = predictions + 2 * std_residuals
            lower_bound = predictions - 2 * std_residuals
            
            fig.add_trace(go.Scatter(
                x=future_dates + future_dates[::-1],
                y=np.concatenate([upper_bound, lower_bound[::-1]]),
                fill='toself',
                fillcolor='rgba(255,0,0,0.2)',
                line=dict(color='rgba(255,0,0,0)'),
                name='Intervalle confiance 95%'
            ))
        
        fig.update_layout(
            title=f"Prédictions pour {symbol} - {days_to_predict} jours",
            xaxis_title="Date",
            yaxis_title="Prix ($)",
            height=500,
            hovermode='x unified',
            template='plotly_white'
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Tableau des prédictions
        pred_df = pd.DataFrame({
            'Date': [d.strftime('%Y-%m-%d') for d in future_dates],
            'Prix prédit': [format_currency(p) for p in predictions],
            'Variation': [f"{(p/hist['Close'].iloc[-1] - 1)*100:+.1f}%" for p in predictions]
        })
        st.dataframe(pred_df, use_container_width=True)
        
        # Métriques
        residuals = y - model.predict(X)
        rmse = np.sqrt(np.mean(residuals**2))
        st.metric("RMSE", format_currency(rmse))
        
        # Tendance
        last_pred = predictions[-1]
        current = hist['Close'].iloc[-1]
        if last_pred > current * 1.05:
            st.success(f"📈 Tendance: HAUSSIÈRE FORTE - {((last_pred/current - 1)*100):+.1f}%")
        elif last_pred > current:
            st.info(f"📈 Tendance: LÉGÈREMENT HAUSSIÈRE - {((last_pred/current - 1)*100):+.1f}%")
        elif last_pred < current * 0.95:
            st.error(f"📉 Tendance: BAISSIÈRE FORTE - {((last_pred/current - 1)*100):+.1f}%")
        elif last_pred < current:
            st.warning(f"📉 Tendance: LÉGÈREMENT BAISSIÈRE - {((last_pred/current - 1)*100):+.1f}%")
        else:
            st.info("➡️ Tendance: NEUTRE")
    else:
        st.warning(f"⚠️ Pas assez de données pour {symbol} (minimum 30 jours requis)")

# Auto-refresh
if auto_refresh:
    time.sleep(refresh_rate)
    st.rerun()

# Footer
st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: gray; font-size: 0.8rem;'>"
    "🚀 SpaceX & NewSpace Tracker | Données: yfinance + simulation | Heure Paris UTC+2"
    "</p>",
    unsafe_allow_html=True
)
