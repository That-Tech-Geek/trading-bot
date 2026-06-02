#!/usr/bin/env python3
"""Streamlit dashboard for the Binance Futures Testnet trading bot."""

import os
import logging
import streamlit as st
from dotenv import load_dotenv

from bot.client import BinanceFuturesClient
from bot.orders import place_order
from bot.logging_config import setup_logging

# ──────────────────────────────────────────────────────────────────────────── #
# Page config
# ──────────────────────────────────────────────────────────────────────────── #
st.set_page_config(
    page_title="Futures Trading Bot",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────────────────────────────────── #
# Custom CSS
# ──────────────────────────────────────────────────────────────────────────── #
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

    /* ── Global ─────────────────────────────────────────────── */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .stApp {
        background: linear-gradient(145deg, #0a0a0f 0%, #0d1117 40%, #0f0f1a 100%);
    }

    /* ── Sidebar ────────────────────────────────────────────── */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0d1117 0%, #161b22 100%);
        border-right: 1px solid rgba(48, 54, 61, 0.6);
    }

    section[data-testid="stSidebar"] .stMarkdown h1,
    section[data-testid="stSidebar"] .stMarkdown h2,
    section[data-testid="stSidebar"] .stMarkdown h3 {
        color: #f0f6fc;
    }

    /* ── Cards ──────────────────────────────────────────────── */
    .metric-card {
        background: linear-gradient(135deg, rgba(22, 27, 34, 0.9) 0%, rgba(13, 17, 23, 0.95) 100%);
        border: 1px solid rgba(48, 54, 61, 0.6);
        border-radius: 16px;
        padding: 24px;
        backdrop-filter: blur(10px);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .metric-card:hover {
        border-color: rgba(136, 98, 255, 0.4);
        box-shadow: 0 0 20px rgba(136, 98, 255, 0.08);
        transform: translateY(-2px);
    }

    .metric-label {
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 1.2px;
        text-transform: uppercase;
        color: #8b949e;
        margin-bottom: 6px;
    }
    .metric-value {
        font-size: 28px;
        font-weight: 800;
        background: linear-gradient(135deg, #f0f6fc 0%, #c9d1d9 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        line-height: 1.2;
    }
    .metric-value.success {
        background: linear-gradient(135deg, #3fb950 0%, #56d364 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .metric-value.warning {
        background: linear-gradient(135deg, #d29922 0%, #e3b341 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .metric-value.danger {
        background: linear-gradient(135deg, #f85149 0%, #ff7b72 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    /* ── Hero header ────────────────────────────────────────── */
    .hero {
        text-align: center;
        padding: 20px 0 30px;
    }
    .hero h1 {
        font-size: 42px;
        font-weight: 900;
        background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 30%, #818cf8 60%, #a78bfa 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -0.5px;
        margin-bottom: 4px;
    }
    .hero p {
        font-size: 15px;
        color: #8b949e;
        font-weight: 400;
    }

    /* ── Status badges ──────────────────────────────────────── */
    .badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        letter-spacing: 0.5px;
    }
    .badge-success {
        background: rgba(63, 185, 80, 0.15);
        color: #3fb950;
        border: 1px solid rgba(63, 185, 80, 0.3);
    }
    .badge-pending {
        background: rgba(210, 153, 34, 0.15);
        color: #d29922;
        border: 1px solid rgba(210, 153, 34, 0.3);
    }
    .badge-error {
        background: rgba(248, 81, 73, 0.15);
        color: #f85149;
        border: 1px solid rgba(248, 81, 73, 0.3);
    }

    /* ── Order panel ────────────────────────────────────────── */
    .order-panel {
        background: linear-gradient(135deg, rgba(22, 27, 34, 0.95) 0%, rgba(13, 17, 23, 0.98) 100%);
        border: 1px solid rgba(48, 54, 61, 0.6);
        border-radius: 20px;
        padding: 32px;
        backdrop-filter: blur(12px);
    }

    .order-panel h3 {
        font-size: 18px;
        font-weight: 700;
        color: #f0f6fc;
        margin-bottom: 20px;
        padding-bottom: 12px;
        border-bottom: 1px solid rgba(48, 54, 61, 0.6);
    }

    /* ── Response panel ─────────────────────────────────────── */
    .response-panel {
        background: linear-gradient(135deg, rgba(22, 27, 34, 0.9) 0%, rgba(13, 17, 23, 0.95) 100%);
        border: 1px solid rgba(48, 54, 61, 0.6);
        border-radius: 16px;
        padding: 24px;
        margin-top: 16px;
    }

    /* ── History table ──────────────────────────────────────── */
    .history-row {
        background: rgba(22, 27, 34, 0.6);
        border: 1px solid rgba(48, 54, 61, 0.4);
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 8px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        transition: all 0.2s ease;
    }
    .history-row:hover {
        border-color: rgba(136, 98, 255, 0.3);
        background: rgba(22, 27, 34, 0.8);
    }

    /* ── Button overrides ───────────────────────────────────── */
    .stButton > button {
        background: linear-gradient(135deg, #7c3aed 0%, #6366f1 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 12px 32px;
        font-weight: 700;
        font-size: 15px;
        letter-spacing: 0.3px;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        width: 100%;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #6d28d9 0%, #4f46e5 100%);
        box-shadow: 0 8px 25px rgba(99, 102, 241, 0.35);
        transform: translateY(-1px);
    }
    .stButton > button:active {
        transform: translateY(0px);
    }

    /* ── Input styling ──────────────────────────────────────── */
    .stSelectbox > div > div,
    .stNumberInput > div > div > input,
    .stTextInput > div > div > input {
        background-color: rgba(22, 27, 34, 0.8) !important;
        border: 1px solid rgba(48, 54, 61, 0.8) !important;
        border-radius: 10px !important;
        color: #f0f6fc !important;
    }

    .stSelectbox > div > div:focus-within,
    .stNumberInput > div > div:focus-within,
    .stTextInput > div > div:focus-within {
        border-color: rgba(99, 102, 241, 0.6) !important;
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.15) !important;
    }

    /* ── Divider ────────────────────────────────────────────── */
    .divider {
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(48, 54, 61, 0.6), transparent);
        margin: 24px 0;
    }

    /* ── Scrollbar ──────────────────────────────────────────── */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb {
        background: rgba(48, 54, 61, 0.6);
        border-radius: 3px;
    }

    /* ── Hide streamlit branding ────────────────────────────── */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────── #
# Session state
# ──────────────────────────────────────────────────────────────────────────── #
if "order_history" not in st.session_state:
    st.session_state.order_history = []
if "connected" not in st.session_state:
    st.session_state.connected = False
if "client" not in st.session_state:
    st.session_state.client = None


# ──────────────────────────────────────────────────────────────────────────── #
# Helpers
# ──────────────────────────────────────────────────────────────────────────── #
def get_status_badge(status: str) -> str:
    status = (status or "UNKNOWN").upper()
    if status == "FILLED":
        return f'<span class="badge badge-success">{status}</span>'
    elif status in ("NEW", "PARTIALLY_FILLED"):
        return f'<span class="badge badge-pending">{status}</span>'
    else:
        return f'<span class="badge badge-error">{status}</span>'


def try_connect(api_key: str, api_secret: str) -> bool:
    """Test connectivity to the Binance Futures Testnet."""
    try:
        client = BinanceFuturesClient(api_key, api_secret)
        client._request("GET", "/fapi/v1/ping")
        return True
    except Exception:
        return False


# ──────────────────────────────────────────────────────────────────────────── #
# Sidebar – credentials & connection
# ──────────────────────────────────────────────────────────────────────────── #
with st.sidebar:
    st.markdown("### ⚡ Connection")
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # Auto-load from .env if available
    load_dotenv()
    default_key = os.getenv("BINANCE_TESTNET_API_KEY", "")
    default_secret = os.getenv("BINANCE_TESTNET_SECRET_KEY", "")

    api_key = st.text_input(
        "API Key",
        value=default_key,
        type="password",
        placeholder="Enter your testnet API key",
    )
    api_secret = st.text_input(
        "Secret Key",
        value=default_secret,
        type="password",
        placeholder="Enter your testnet secret key",
    )

    if st.button("🔌 Connect", use_container_width=True):
        if not api_key or not api_secret:
            st.error("Both API Key and Secret Key are required.")
        else:
            with st.spinner("Connecting to Binance Futures Testnet..."):
                if try_connect(api_key, api_secret):
                    st.session_state.client = BinanceFuturesClient(api_key, api_secret)
                    st.session_state.connected = True
                    st.success("Connected ✓")
                else:
                    st.session_state.connected = False
                    st.error("Connection failed. Check your credentials.")

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # Connection status
    if st.session_state.connected:
        st.markdown(
            '🟢 <span style="color: #3fb950; font-weight: 600;">CONNECTED</span> '
            '<span style="color: #8b949e; font-size: 12px;">Testnet</span>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '🔴 <span style="color: #f85149; font-weight: 600;">DISCONNECTED</span>',
            unsafe_allow_html=True,
        )

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # Stats
    total = len(st.session_state.order_history)
    filled = sum(1 for o in st.session_state.order_history if o.get("status") == "FILLED")
    failed = sum(1 for o in st.session_state.order_history if o.get("error"))

    st.markdown("### 📊 Session Stats")
    st.metric("Total Orders", total)
    st.metric("Filled", filled)
    st.metric("Failed", failed)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown(
        '<p style="color: #484f58; font-size: 11px; text-align: center;">'
        'Binance Futures Testnet &middot; USDT-M</p>',
        unsafe_allow_html=True,
    )


# ──────────────────────────────────────────────────────────────────────────── #
# Hero
# ──────────────────────────────────────────────────────────────────────────── #
st.markdown("""
<div class="hero">
    <h1>Futures Trading Bot</h1>
    <p>Place MARKET & LIMIT orders on Binance Futures Testnet</p>
</div>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────── #
# Main layout – Order form + Response
# ──────────────────────────────────────────────────────────────────────────── #
col_form, col_spacer, col_response = st.columns([5, 0.5, 5])

with col_form:
    st.markdown('<div class="order-panel">', unsafe_allow_html=True)
    st.markdown("### 📝 New Order")

    # Symbol
    symbol = st.text_input(
        "Symbol",
        value="BTCUSDT",
        placeholder="e.g. BTCUSDT, ETHUSDT",
    ).upper()

    # Side + Type in two columns
    c1, c2 = st.columns(2)
    with c1:
        side = st.selectbox("Side", ["BUY", "SELL"])
    with c2:
        order_type = st.selectbox("Type", ["MARKET", "LIMIT"])

    # Quantity
    quantity = st.number_input(
        "Quantity",
        min_value=0.0,
        value=0.001,
        step=0.001,
        format="%.6f",
    )

    # Price (only for LIMIT)
    price = None
    if order_type == "LIMIT":
        price = st.number_input(
            "Price (USDT)",
            min_value=0.0,
            value=50000.0,
            step=100.0,
            format="%.2f",
        )

    st.markdown("")  # spacer

    # ── Order summary ──
    st.markdown(
        f"""
        <div style="background: rgba(99, 102, 241, 0.08); border: 1px solid rgba(99, 102, 241, 0.2);
             border-radius: 12px; padding: 16px; margin-bottom: 16px;">
            <div style="font-size: 11px; color: #8b949e; text-transform: uppercase;
                 letter-spacing: 1px; font-weight: 600; margin-bottom: 8px;">Order Preview</div>
            <div style="color: #f0f6fc; font-size: 15px;">
                <span style="color: {'#3fb950' if side == 'BUY' else '#f85149'}; font-weight: 700;">{side}</span>
                &nbsp;{quantity} {symbol}
                &nbsp;<span style="color: #8b949e;">via</span>&nbsp;
                <span style="font-weight: 600;">{order_type}</span>
                {f' @ <span style="color: #d2a8ff; font-weight: 600;">${price:,.2f}</span>' if price else ''}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Execute button ──
    execute = st.button(
        f"⚡ Place {side} Order",
        use_container_width=True,
        disabled=not st.session_state.connected,
    )
    if not st.session_state.connected:
        st.caption("⚠️ Connect to the testnet first via the sidebar.")

    st.markdown("</div>", unsafe_allow_html=True)

with col_response:
    st.markdown('<div class="order-panel">', unsafe_allow_html=True)
    st.markdown("### 📡 Response")

    if execute and st.session_state.connected:
        # Initialize logging once
        os.makedirs("logs", exist_ok=True)
        setup_logging("logs/trading_bot.log")

        with st.spinner("Placing order..."):
            try:
                response = place_order(
                    st.session_state.client,
                    symbol, side, order_type, quantity, price,
                )

                status = response.get("status", "UNKNOWN")

                # Success metrics
                m1, m2 = st.columns(2)
                with m1:
                    st.markdown(
                        f'<div class="metric-card">'
                        f'<div class="metric-label">Order ID</div>'
                        f'<div class="metric-value">{response.get("orderId", "—")}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                with m2:
                    cls = "success" if status == "FILLED" else "warning"
                    st.markdown(
                        f'<div class="metric-card">'
                        f'<div class="metric-label">Status</div>'
                        f'<div class="metric-value {cls}">{status}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

                st.markdown("")

                m3, m4 = st.columns(2)
                with m3:
                    st.markdown(
                        f'<div class="metric-card">'
                        f'<div class="metric-label">Executed Qty</div>'
                        f'<div class="metric-value">{response.get("executedQty", "—")}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                with m4:
                    avg = response.get("avgPrice", "0")
                    st.markdown(
                        f'<div class="metric-card">'
                        f'<div class="metric-label">Avg Price</div>'
                        f'<div class="metric-value">${float(avg):,.2f}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

                st.markdown("")
                st.success("✅ Order placed successfully!")

                # Save to history
                st.session_state.order_history.insert(0, {
                    "orderId": response.get("orderId"),
                    "symbol": symbol,
                    "side": side,
                    "type": order_type,
                    "quantity": quantity,
                    "price": price,
                    "status": status,
                    "executedQty": response.get("executedQty"),
                    "avgPrice": response.get("avgPrice"),
                })

                # Show raw response in expander
                with st.expander("🔍 Raw API Response", expanded=False):
                    st.json(response)

            except ValueError as e:
                st.error(f"❌ Validation Error: {e}")
                st.session_state.order_history.insert(0, {
                    "symbol": symbol, "side": side, "type": order_type,
                    "quantity": quantity, "status": "VALIDATION_ERROR",
                    "error": str(e),
                })
            except Exception as e:
                st.error(f"❌ Order Failed: {e}")
                st.session_state.order_history.insert(0, {
                    "symbol": symbol, "side": side, "type": order_type,
                    "quantity": quantity, "status": "ERROR",
                    "error": str(e),
                })
    else:
        # Empty state
        st.markdown(
            """
            <div style="text-align: center; padding: 60px 20px; color: #484f58;">
                <div style="font-size: 48px; margin-bottom: 12px;">📡</div>
                <div style="font-size: 15px; font-weight: 500;">Waiting for order</div>
                <div style="font-size: 13px; margin-top: 4px;">
                    Configure and submit an order from the left panel
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────── #
# Order history
# ──────────────────────────────────────────────────────────────────────────── #
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

if st.session_state.order_history:
    st.markdown("### 📜 Order History")
    st.markdown("")

    for i, order in enumerate(st.session_state.order_history[:20]):
        error = order.get("error")
        badge = get_status_badge(order.get("status", "UNKNOWN"))

        side_color = "#3fb950" if order.get("side") == "BUY" else "#f85149"

        detail_parts = []
        if order.get("executedQty"):
            detail_parts.append(f"Qty: {order['executedQty']}")
        if order.get("avgPrice") and order["avgPrice"] != "0":
            detail_parts.append(f"Avg: ${float(order['avgPrice']):,.2f}")
        if error:
            detail_parts.append(f"Error: {error}")
        detail_str = " &middot; ".join(detail_parts)

        st.markdown(
            f"""
            <div class="history-row">
                <div style="display: flex; align-items: center; gap: 16px;">
                    <div style="font-size: 14px; font-weight: 700; color: {side_color};">
                        {order.get("side", "?")}
                    </div>
                    <div>
                        <div style="color: #f0f6fc; font-weight: 600; font-size: 14px;">
                            {order.get("quantity", "?")} {order.get("symbol", "?")}
                            <span style="color: #8b949e; font-weight: 400; font-size: 12px;">
                                {order.get("type", "")}
                                {f" @ ${order['price']:,.2f}" if order.get("price") else ""}
                            </span>
                        </div>
                        <div style="color: #8b949e; font-size: 12px; margin-top: 2px;">
                            {f"ID: {order['orderId']}" if order.get("orderId") else ""}
                            {f" &middot; {detail_str}" if detail_str else ""}
                        </div>
                    </div>
                </div>
                <div>{badge}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
else:
    st.markdown(
        """
        <div style="text-align: center; padding: 40px; color: #484f58;">
            <div style="font-size: 13px;">No orders placed yet this session.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
