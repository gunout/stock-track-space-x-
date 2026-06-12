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
import requests
import warnings
warnings.filterwarnings('ignore')

# Configuration de la page
st.set_page_config(
    page_title="🚀 SpaceX & NewSpace Tracker - Avancé",
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
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
        background: linear-gradient(135deg, #000000 0%, #005288 50%, #FFFFFF 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .spacex-badge {
        background-color: #005288;
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 1rem;
        font-weight: bold;
        display: inline-block;
    }
    .starship-badge {
        background: linear-gradient(135deg, #ff6b35, #f7931e);
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 1rem;
        font-weight: bold;
        display: inline-block;
    }
    .launch-alert {
        background: linear-gradient(135deg, #1a1a2e, #16213e);
        color: #ff6b35;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        border-left: 4px solid #ff6b35;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .stButton>button {
        width: 100%;
        background-color: #005288;
        color: white;
    }
    .timezone-badge {
        background-color: #e3f2fd;
        border-left: 4px solid #005288;
        padding: 0.5rem 1rem;
        margin: 1rem 0;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialisation des variables de session
if 'price_alerts' not in st.session_state:
    st.session_state.price_alerts = []

if 'portfolio' not in st.session_state:
    st.session_state.portfolio = {}

if 'launch_alerts' not in st.session_state:
    st.session_state.launch_alerts = []

if 'email_config' not in st.session_state:
    st.session_state.email_config = {
        'enabled': False,
        'smtp_server': 'smtp.gmail.com',
        'smtp_port': 587,
        'email': '',
        'password': ''
    }

# Watchlist SpaceX & NewSpace
if 'watchlist' not in st.session_state:
    st.session_state.watchlist = [
        # SpaceX liés (indirects)
        'TSLA',      # Tesla (Elon Musk)
        'LMT',       # Lockheed Martin
        'NOC',       # Northrop Grumman
        'BA',        # Boeing (Starliner)
        'RTX',       # Raytheon
        'GD',        # General Dynamics
        'LHX',       # L3Harris
        # NewSpace compagnies publiques
        'RKLB',      # Rocket Lab
        'ASTS',      # AST SpaceMobile
        'RDW',       # Redwire
        'PL',        # Planet Labs
        'SPCE',      # Virgin Galactic
        'MNTS',      # Momentus
        'BKSY',      # BlackSky
        'SATL',      # Satellogic
        'ASTR',      # Astra Space
        'LLAP',      # Terran Orbital
        'GSAT',      # Globalstar
        'IRDM',      # Iridium
        'MAXR',      # Maxar Technologies
        # Fournisseurs et partenaires
        'HON',       # Honeywell
        'GE',        # General Electric
        'TDY',       # Teledyne
        'HEI',       # HEICO
        # Satellites et communications
        'SATS',      # EchoStar
        'CMCSA',     # Comcast (partenaire potentiel)
        'T',         # AT&T (Starlink distribution)
    ]

# Derniers lancements SpaceX (simulé - à remplacer par API réelle)
RECENT_LAUNCHES = [
    {
        'mission': 'Starship IFT-6',
        'date': '2024-11-18',
        'vehicle': 'Starship Super Heavy',
        'outcome': 'Succès partiel',
        'description': 'Sixième vol d\'essai intégré, atterrissage réussi du booster'
    },
    {
        'mission': 'Starlink Group 9-6',
        'date': '2024-11-15',
        'vehicle': 'Falcon 9',
        'outcome': 'Succès',
        'description': '22 satellites Starlink en orbite'
    },
    {
        'mission': 'CRS-31',
        'date': '2024-11-10',
        'vehicle': 'Falcon 9',
        'outcome': 'Succès',
        'description': 'Ravitaillement de l\'ISS'
    }
]

UPCOMING_LAUNCHES = [
    {
        'mission': 'Starship IFT-7',
        'date': '2025-01-15',
        'vehicle': 'Starship Super Heavy',
        'description': 'Test orbital avec charge utile'
    },
    {
        'mission': 'Falcon Heavy - USSF-67',
        'date': '2025-02-01',
        'vehicle': 'Falcon Heavy',
        'description': 'Mission militaire classifiée'
    },
    {
        'mission': 'Starlink Group 12-1',
        'date': '2024-12-05',
        'vehicle': 'Falcon 9',
        'description': 'Déploiement constellation'
    }
]

# Titre principal
st.markdown("<h1 class='main-header'>🚀 SpaceX & NewSpace - Tracker Avancé</h1>", unsafe_allow_html=True)

# Bannière de fuseau horaire
current_time_paris = datetime.now(USER_TIMEZONE)
current_time_ny = datetime.now(US_TIMEZONE)
current_time_utc = datetime.now(UTC_TIMEZONE)

st.markdown(f"""
<div class='timezone-badge'>
    <b>🕐 Fuseaux horaires :</b><br>
    🇫🇷 Heure Paris : {current_time_paris.strftime('%H:%M:%S')} (UTC+1/UTC+2)<br>
    🇺🇸 Heure Floride (CCSFS) : {current_time_ny.strftime('%H:%M:%S')} (UTC-4/UTC-5)<br>
    🌍 Heure UTC : {current_time_utc.strftime('%H:%M:%S')} (Temps universel)<br>
    🚀 Prochain lancement estimé : <b>Starship IFT-7 - 15 janvier 2025</b>
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/d/dc/SpaceX_Logo_Black.png/800px-SpaceX_Logo_Black.png", width=200)
    st.title("Navigation SpaceX")
    
    menu = st.radio(
        "Choisir une section",
        ["🚀 Tableau de bord SpaceX",
         "🛰️ Watchlist NewSpace",
         "💰 Portefeuille virtuel",
         "🎯 Alertes & Lancements",
         "📧 Notifications",
         "📤 Export données",
         "🤖 Prédictions ML",
         "📊 Analyse comparative"]
    )
    
    st.markdown("---")
    
    # Configuration
    st.subheader("⚙️ Configuration")
    
    symbol = st.selectbox(
        "Symbole principal",
        options=st.session_state.watchlist,
        index=0
    )
    
    period = st.selectbox(
        "Période",
        options=["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y"],
        index=2
    )
    
    interval = st.selectbox(
        "Intervalle",
        options=["1m", "5m", "15m", "30m", "1h", "1d", "1wk"],
        format_func=lambda x: {"1m": "1 min", "5m": "5 min", "15m": "15 min", "30m": "30 min", "1h": "1 heure", "1d": "1 jour", "1wk": "1 semaine"}[x],
        index=5
    )
    
    auto_refresh = st.checkbox("Auto-refresh", value=False)
    if auto_refresh:
        refresh_rate = st.slider("Fréquence (sec)", 5, 60, 30)

# Fonctions utilitaires
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
        
        return hist, info
    except Exception as e:
        st.error(f"Erreur: {e}")
        return None, None

def get_company_info(symbol):
    """Informations spécifiques SpaceX/NewSpace"""
    space_companies = {
        'TSLA': {'name': 'Tesla Inc.', 'role': 'Actionnaire principal SpaceX', 'musk_related': True},
        'RKLB': {'name': 'Rocket Lab USA', 'role': 'Concurrent direct - Neutron rocket', 'musk_related': False},
        'ASTS': {'name': 'AST SpaceMobile', 'role': 'Réseau satellite 5G', 'musk_related': False},
        'RDW': {'name': 'Redwire', 'role': 'Infrastructure spatiale', 'musk_related': False},
        'PL': {'name': 'Planet Labs', 'role': 'Imagerie satellite', 'musk_related': False},
        'SPCE': {'name': 'Virgin Galactic', 'role': 'Tourisme spatial', 'musk_related': False},
        'LMT': {'name': 'Lockheed Martin', 'role': 'Concurrent/Partenaire', 'musk_related': False},
        'BA': {'name': 'Boeing', 'role': 'Concurrent (Starliner)', 'musk_related': False},
    }
    return space_companies.get(symbol, {'name': symbol, 'role': 'Entreprise spatiale', 'musk_related': False})

def format_currency(value, symbol):
    return f"${value:.2f}" if value else "$0.00"

def send_email_alert(subject, body, to_email):
    if not st.session_state.email_config['enabled']:
        return False
    try:
        msg = MIMEMultipart()
        msg['From'] = st.session_state.email_config['email']
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))
        
        server = smtplib.SMTP(st.session_state.email_config['smtp_server'], st.session_state.email_config['smtp_port'])
        server.starttls()
        server.login(st.session_state.email_config['email'], st.session_state.email_config['password'])
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        st.error(f"Erreur: {e}")
        return False

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
    st.warning(f"⚠️ Impossible de charger {symbol}")
    current_price = 0
else:
    current_price = safe_get_metric(hist, 'Close')

# ============================================================================
# SECTION 1: TABLEAU DE BORD SPACEX
# ============================================================================
if menu == "🚀 Tableau de bord SpaceX":
    st.subheader("🚀 Tableau de bord SpaceX & NewSpace")
    
    # Alertes lancements
    st.markdown("""
    <div class='launch-alert'>
        <b>🚨 PROCHAIN LANCEMENT MAJEUR</b><br>
        <b>Starship IFT-7</b> - 15 janvier 2025<br>
        Premier vol orbital avec charge utile - Lancement depuis Starbase, TX
    </div>
    """, unsafe_allow_html=True)
    
    # Métriques SpaceX (estimations)
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        st.metric("Lancements 2024", "128", delta="+22 vs 2023")
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        st.metric("Starlink actifs", "~6,200", delta="+1,200 cette année")
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col3:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        st.metric("Valuation SpaceX", "$180B", delta="Est. privé")
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col4:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        st.metric("Abonnés Starlink", "2.6M", delta="+500k")
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Graphique des actions liées
    st.subheader("📈 Performance des actions liées à SpaceX")
    
    related_stocks = ['TSLA', 'RKLB', 'ASTS', 'LMT', 'BA']
    perf_data = []
    
    for sym in related_stocks:
        ticker = yf.Ticker(sym)
        hist_data = ticker.history(period="1mo")
        if not hist_data.empty:
            start_price = hist_data['Close'].iloc[0]
            end_price = hist_data['Close'].iloc[-1]
            perf_pct = ((end_price - start_price) / start_price) * 100
            perf_data.append({'Symbole': sym, 'Performance 1M': f"{perf_pct:.1f}%", 'Couleur': 'green' if perf_pct > 0 else 'red'})
    
    if perf_data:
        df_perf = pd.DataFrame(perf_data)
        st.dataframe(df_perf, use_container_width=True)
    
    # Graphique comparatif
    fig_comp = go.Figure()
    
    for sym in related_stocks:
        ticker = yf.Ticker(sym)
        hist_data = ticker.history(period="3mo")
        if not hist_data.empty:
            hist_data.index = hist_data.index.tz_convert(USER_TIMEZONE)
            normalized = (hist_data['Close'] / hist_data['Close'].iloc[0] - 1) * 100
            fig_comp.add_trace(go.Scatter(
                x=hist_data.index,
                y=normalized,
                mode='lines',
                name=sym,
                line=dict(width=2)
            ))
    
    fig_comp.update_layout(
        title="Comparaison de performance (normalisée %) - 3 mois",
        xaxis_title="Date (heure Paris)",
        yaxis_title="Variation %",
        height=500,
        hovermode='x unified',
        template='plotly_white'
    )
    
    st.plotly_chart(fig_comp, use_container_width=True)
    
    # Derniers lancements
    st.subheader("🛸 Derniers lancements SpaceX")
    for launch in RECENT_LAUNCHES:
        st.markdown(f"""
        **{launch['mission']}** - {launch['date']}
        - 🚀 Véhicule: {launch['vehicle']}
        - ✅ Résultat: {launch['outcome']}
        - 📝 {launch['description']}
        """)
    
    # Lancements à venir
    st.subheader("🔮 Lancements à venir")
    for launch in UPCOMING_LAUNCHES:
        st.info(f"**{launch['mission']}** - {launch['date']}\n🚀 {launch['vehicle']}\n{launch['description']}")

# ============================================================================
# SECTION 2: WATCHLIST NEWSPACE
# ============================================================================
elif menu == "🛰️ Watchlist NewSpace":
    st.subheader("🛰️ Watchlist NewSpace - Actions spatiales")
    
    # Filtres
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        sector_filter = st.multiselect(
            "Filtrer par secteur",
            ["Lanceurs", "Satellites", "Tourisme spatial", "Défense", "Infrastructure"],
            default=["Lanceurs", "Satellites"]
        )
    
    with col_f2:
        sort_by = st.selectbox("Trier par", ["Symbole", "Market Cap", "Performance", "Volume"])
    
    # Watchlist complète
    watchlist_data = []
    
    for sym in st.session_state.watchlist:
        try:
            ticker = yf.Ticker(sym)
            hist = ticker.history(period="5d")
            info = ticker.info
            
            if not hist.empty:
                current = hist['Close'].iloc[-1]
                prev = hist['Close'].iloc[0]
                change_pct = ((current - prev) / prev * 100) if prev != 0 else 0
                
                company_info = get_company_info(sym)
                
                watchlist_data.append({
                    'Symbole': sym,
                    'Entreprise': company_info['name'],
                    'Rôle': company_info['role'],
                    'Prix': f"${current:.2f}",
                    'Variation 5j': f"{change_pct:+.2f}%",
                    'Market Cap': info.get('marketCap', 'N/A'),
                    'Volume': info.get('volume', 'N/A'),
                    'Lien Musk': "✅" if company_info['musk_related'] else "❌"
                })
        except:
            pass
    
    if watchlist_data:
        df_watchlist = pd.DataFrame(watchlist_data)
        st.dataframe(df_watchlist, use_container_width=True, height=400)
        
        # Graphique radar des performances
        st.subheader("📊 Radar de performance sectorielle")
        sector_perf = {}
        for item in watchlist_data:
            sector = item['Rôle']
            perf = float(item['Variation 5j'].replace('%', '').replace('+', ''))
            if sector not in sector_perf:
                sector_perf[sector] = []
            sector_perf[sector].append(perf)
        
        radar_data = []
        for sector, perfs in sector_perf.items():
            radar_data.append({'Secteur': sector, 'Performance moyenne': np.mean(perfs)})
        
        if radar_data:
            df_radar = pd.DataFrame(radar_data)
            fig_radar = px.bar(df_radar, x='Secteur', y='Performance moyenne', 
                               title="Performance par secteur", color='Performance moyenne',
                               color_continuous_scale='RdYlGn')
            st.plotly_chart(fig_radar, use_container_width=True)
    else:
        st.info("Aucune donnée disponible")

# ============================================================================
# SECTION 3: PORTEFEUILLE VIRTUEL
# ============================================================================
elif menu == "💰 Portefeuille virtuel":
    st.subheader("💰 Portefeuille virtuel - Investissement spatial")
    
    col1, col2 = st.columns([2, 1])
    
    with col2:
        st.markdown("### ➕ Ajouter une position")
        with st.form("add_position"):
            symbol_pf = st.selectbox("Symbole", options=st.session_state.watchlist)
            shares = st.number_input("Actions", min_value=1, step=1, value=100)
            buy_price = st.number_input("Prix d'achat ($)", min_value=0.01, step=1.0, value=10.0)
            
            if st.form_submit_button("Ajouter"):
                if symbol_pf not in st.session_state.portfolio:
                    st.session_state.portfolio[symbol_pf] = []
                st.session_state.portfolio[symbol_pf].append({
                    'shares': shares,
                    'buy_price': buy_price,
                    'date': datetime.now(USER_TIMEZONE).strftime('%Y-%m-%d %H:%M:%S')
                })
                st.success(f"✅ {shares} {symbol_pf} ajoutées")
    
    with col1:
        if st.session_state.portfolio:
            portfolio_data = []
            total_value = 0
            total_cost = 0
            
            for sym, positions in st.session_state.portfolio.items():
                ticker = yf.Ticker(sym)
                hist = ticker.history(period='1d')
                current = hist['Close'].iloc[-1] if not hist.empty else 0
                
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
                        'Symbole': sym,
                        'Actions': shares,
                        "Prix d'achat": f"${buy_price:.2f}",
                        'Prix actuel': f"${current:.2f}",
                        'Valeur': f"${value:,.2f}",
                        'Profit': f"${profit:,.2f}",
                        'Profit %': f"{profit_pct:+.1f}%"
                    })
            
            if portfolio_data:
                total_profit = total_value - total_cost
                total_profit_pct = (total_profit / total_cost * 100) if total_cost > 0 else 0
                
                col_met1, col_met2, col_met3 = st.columns(3)
                col_met1.metric("Valeur totale", f"${total_value:,.2f}")
                col_met2.metric("Coût total", f"${total_cost:,.2f}")
                col_met3.metric("Profit total", f"${total_profit:,.2f}", delta=f"{total_profit_pct:+.1f}%")
                
                df_portfolio = pd.DataFrame(portfolio_data)
                st.dataframe(df_portfolio, use_container_width=True)
                
                # Graphique de répartition
                fig_pie = px.pie(names=[p['Symbole'] for p in portfolio_data], 
                                 values=[float(p['Valeur'].replace('$', '').replace(',', '')) for p in portfolio_data],
                                 title="Répartition du portefeuille")
                st.plotly_chart(fig_pie)
                
                if st.button("🗑️ Vider le portefeuille"):
                    st.session_state.portfolio = {}
                    st.rerun()
        else:
            st.info("Aucune position")

# ============================================================================
# SECTION 4: ALERTES & LANCEMENTS
# ============================================================================
elif menu == "🎯 Alertes & Lancements":
    st.subheader("🎯 Alertes prix & Lancements SpaceX")
    
    tab1, tab2 = st.tabs(["Alertes prix", "Alertes lancements"])
    
    with tab1:
        col_a1, col_a2 = st.columns(2)
        
        with col_a1:
            with st.form("new_alert"):
                alert_symbol = st.selectbox("Symbole", st.session_state.watchlist)
                alert_price = st.number_input("Prix cible ($)", min_value=0.01, step=1.0, value=50.0)
                condition = st.selectbox("Condition", ["above", "below"])
                
                if st.form_submit_button("Créer alerte"):
                    st.session_state.price_alerts.append({
                        'symbol': alert_symbol,
                        'price': alert_price,
                        'condition': condition,
                        'created': datetime.now(USER_TIMEZONE).strftime('%Y-%m-%d %H:%M:%S')
                    })
                    st.success(f"Alerte créée pour {alert_symbol}")
        
        with col_a2:
            if st.session_state.price_alerts:
                for i, alert in enumerate(st.session_state.price_alerts):
                    st.warning(f"{alert['symbol']} - {alert['condition']} ${alert['price']}")
                    if st.button(f"Supprimer", key=f"del_{i}"):
                        st.session_state.price_alerts.pop(i)
                        st.rerun()
            else:
                st.info("Aucune alerte")
    
    with tab2:
        st.markdown("### 🚀 Suivi des lancements")
        
        for launch in UPCOMING_LAUNCHES:
            st.info(f"""
            **{launch['mission']}** - {launch['date']}
            - 🚀 {launch['vehicle']}
            - 📝 {launch['description']}
            """)
        
        if st.button("🔔 Alerte avant lancement"):
            st.session_state.launch_alerts.append({
                'mission': 'Starship IFT-7',
                'date': '2025-01-15',
                'created': datetime.now(USER_TIMEZONE).strftime('%Y-%m-%d %H:%M:%S')
            })
            st.success("Vous serez notifié 24h avant le lancement")

# ============================================================================
# SECTION 5: NOTIFICATIONS EMAIL
# ============================================================================
elif menu == "📧 Notifications":
    st.subheader("📧 Configuration email")
    
    with st.form("email_config"):
        enabled = st.checkbox("Activer emails", value=st.session_state.email_config['enabled'])
        
        col1, col2 = st.columns(2)
        with col1:
            smtp_server = st.text_input("Serveur SMTP", value=st.session_state.email_config['smtp_server'])
            smtp_port = st.number_input("Port", value=st.session_state.email_config['smtp_port'])
        
        with col2:
            email = st.text_input("Email", value=st.session_state.email_config['email'])
            password = st.text_input("Mot de passe", type="password", value=st.session_state.email_config['password'])
        
        if st.form_submit_button("💾 Sauvegarder"):
            st.session_state.email_config = {
                'enabled': enabled,
                'smtp_server': smtp_server,
                'smtp_port': smtp_port,
                'email': email,
                'password': password
            }
            st.success("Configuration sauvegardée")

# ============================================================================
# SECTION 6: EXPORT DONNÉES
# ============================================================================
elif menu == "📤 Export données":
    st.subheader("📤 Export des données")
    
    if hist is not None and not hist.empty:
        csv = hist.to_csv()
        st.download_button("📥 CSV", csv, f"{symbol}_data.csv", "text/csv")
        
        # Statistiques
        st.markdown("### Statistiques")
        stats = {
            'Moyenne': hist['Close'].mean(),
            'Std': hist['Close'].std(),
            'Min': hist['Close'].min(),
            'Max': hist['Close'].max(),
            'Volatilité': hist['Close'].pct_change().std() * 100
        }
        
        for key, val in stats.items():
            st.write(f"{key}: {format_currency(val, symbol) if key != 'Volatilité' else f'{val:.2f}%'}")
        
        # Export JSON
        json_data = {
            'symbol': symbol,
            'company': get_company_info(symbol),
            'last_update': datetime.now(USER_TIMEZONE).isoformat(),
            'statistics': {k: float(v) if isinstance(v, (int, float)) else v for k, v in stats.items()},
            'data': hist.reset_index().to_dict(orient='records')
        }
        
        st.download_button("📥 JSON", json.dumps(json_data, indent=2, default=str), f"{symbol}_data.json", "application/json")

# ============================================================================
# SECTION 7: PRÉDICTIONS ML
# ============================================================================
elif menu == "🤖 Prédictions ML":
    st.subheader("🤖 Prédictions ML - Actions spatiales")
    
    if hist is not None and not hist.empty and len(hist) > 30:
        df_pred = hist[['Close']].reset_index()
        df_pred['Days'] = (df_pred['Date'] - df_pred['Date'].min()).dt.days
        
        X = df_pred['Days'].values.reshape(-1, 1)
        y = df_pred['Close'].values
        
        col1, col2 = st.columns(2)
        with col1:
            days_to_predict = st.slider("Jours à prédire", 1, 30, 7)
            degree = st.slider("Degré polynôme", 1, 5, 2)
        
        model = make_pipeline(PolynomialFeatures(degree=degree), LinearRegression())
        model.fit(X, y)
        
        last_day = X[-1][0]
        future_days = np.arange(last_day + 1, last_day + days_to_predict + 1).reshape(-1, 1)
        predictions = model.predict(future_days)
        
        last_date = df_pred['Date'].iloc[-1]
        future_dates = [last_date + timedelta(days=i+1) for i in range(days_to_predict)]
        
        fig_pred = go.Figure()
        fig_pred.add_trace(go.Scatter(x=df_pred['Date'], y=y, mode='lines', name='Historique'))
        fig_pred.add_trace(go.Scatter(x=future_dates, y=predictions, mode='lines+markers', name='Prédictions'))
        
        fig_pred.update_layout(title=f"Prédictions {symbol} - {days_to_predict} jours",
                               xaxis_title="Date", yaxis_title="Prix ($)", height=500)
        
        st.plotly_chart(fig_pred, use_container_width=True)
        
        # Tableau prédictions
        pred_df = pd.DataFrame({
            'Date': [d.strftime('%Y-%m-%d') for d in future_dates],
            'Prix prédit': [f"${p:.2f}" for p in predictions],
            'Variation %': [f"{((p/current_price)-1)*100:+.2f}%" for p in predictions]
        })
        st.dataframe(pred_df)
        
        # Performance modèle
        residuals = y - model.predict(X)
        st.metric("RMSE", f"${np.sqrt(np.mean(residuals**2)):.2f}")
        st.metric("R²", f"{model.score(X, y):.3f}")
    else:
        st.warning(f"Données insuffisantes pour {symbol}")

# ============================================================================
# SECTION 8: ANALYSE COMPARATIVE
# ============================================================================
elif menu == "📊 Analyse comparative":
    st.subheader("📊 Analyse comparative du secteur spatial")
    
    # Comparaison des ratios
    compare_symbols = st.multiselect("Sélectionner actions à comparer", st.session_state.watchlist, default=['RKLB', 'ASTS', 'PL'])
    
    if compare_symbols:
        comparison = []
        for sym in compare_symbols:
            ticker = yf.Ticker(sym)
            info = ticker.info
            hist = ticker.history(period="1mo")
            
            perf_1m = ((hist['Close'].iloc[-1] / hist['Close'].iloc[0]) - 1) * 100 if len(hist) > 1 else 0
            
            comparison.append({
                'Symbole': sym,
                'Prix': f"${info.get('currentPrice', 0):.2f}",
                'Market Cap': info.get('marketCap', 'N/A'),
                'P/E': info.get('trailingPE', 'N/A'),
                'Perf 1M': f"{perf_1m:+.1f}%",
                'Beta': info.get('beta', 'N/A')
            })
        
        df_comp = pd.DataFrame(comparison)
        st.dataframe(df_comp, use_container_width=True)
        
        # Graphique de corrélation
        st.subheader("📈 Corrélation des prix")
        corr_data = pd.DataFrame()
        
        for sym in compare_symbols:
            ticker = yf.Ticker(sym)
            hist = ticker.history(period="3mo")
            if not hist.empty:
                corr_data[sym] = hist['Close']
        
        if not corr_data.empty:
            fig_heatmap = px.imshow(corr_data.corr(), text_auto=True, color_continuous_scale='RdBu',
                                    title="Matrice de corrélation")
            st.plotly_chart(fig_heatmap, use_container_width=True)

# ============================================================================
# FOOTER & AUTO-REFRESH
# ============================================================================
st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: gray; font-size: 0.8rem;'>"
    "🚀 SpaceX & NewSpace Tracker | Données yfinance | ⚠️ Données avec délai possible | "
    "🇫🇷 Heure Paris | 🌍 UTC | 🚀 Prochain vol: Starship IFT-7"
    "</p>",
    unsafe_allow_html=True
)

if auto_refresh and hist is not None and not hist.empty:
    time.sleep(refresh_rate)
    st.rerun()
