import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import os

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")

def api_get(path: str):
    resp = requests.get(API_BASE + path)
    resp.raise_for_status()
    return resp.json()

def api_post(path: str):
    resp = requests.post(API_BASE + path)
    resp.raise_for_status()
    return resp.json()

def render_admiral_deck():
    st.title("⚓ Admiral — Trading Engine")
    st.write("Trading engine status placeholder.")
    # Future: show telemetry and portfolio

def render_perimeter_scout_deck():
    st.title("🛡️ Perimeter Scout — Aegis Security Core")

    col1, col2 = st.columns(2)
    with col1:
        mode = st.radio("Intel Mode", ["Sample", "Deep"], horizontal=True)
    with col2:
        if st.button("Refresh Intel"):
            st.rerun()

    endpoint = "/security/intel?mode=sample" if mode == "Sample" else "/security/intel"
    try:
        sec = api_get(endpoint)
        posture = sec.get("posture", {})
        st.subheader("Global Posture")
        c1, c2, c3 = st.columns(3)
        c1.metric("Posture", posture.get("posture", "UNKNOWN"))
        c2.metric("Trajectory", posture.get("trajectory", "UNKNOWN"))
        c3.metric("Tags", ", ".join(posture.get("tags", [])) or "None")

        with st.expander("Detectors"):
            st.json(sec.get("detectors", {}))

        with st.expander("Hound (Runtime Health)"):
            st.json(sec.get("hound", {}))

        with st.expander("Perimeter Scout (Edge Health)"):
            st.json(sec.get("perimeter", {}))

        with st.expander("Warnings"):
            st.json(sec.get("warnings", []))

    except Exception as e:
        st.error(f"Aegis intel unavailable: {e}")

    st.markdown("---")
    st.subheader("📜 Posture Timeline (Minimal Log)")
    try:
        timeline = api_get("/security/timeline/minimal")
        if not timeline:
            st.info("No posture events recorded yet.")
        else:
            df = pd.DataFrame(timeline)
            df["ts"] = pd.to_datetime(df["ts"])
            st.dataframe(df, use_container_width=True)

            posture_map = {"SAFE": 0, "WATCH": 1, "DANGER": 2, "CRITICAL": 3}
            df["level"] = df["posture"].map(posture_map).fillna(0)
            fig = px.line(df, x="ts", y="level", title="Posture over time")
            st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Timeline error: {e}")

def render_tia_deck():
    st.title("🧠 TIA — Tactical Intelligence Agent")
    st.write("Future: display TIA summaries here.")
    # When TIA is wired, call its API or registry-based methods

def render_mapping_inventory_deck():
    st.title("🗺️ Mapping & Inventory — Pioneer Trader Fleet")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Refresh Fleet Status"):
            st.rerun()

    st.subheader("Fleet Inventory")
    try:
        fleet = api_get("/inventory/fleet")
        if fleet.get("status") in ("UNREACHABLE", "TIMEOUT", "ERROR"):
            st.warning(f"Pioneer Trader unavailable: {fleet.get('error')}")
        else:
            vortex = fleet.get("vortex", {})
            tia = fleet.get("tia", {})
            admiral = fleet.get("admiral", {})

            c1, c2, c3 = st.columns(3)
            c1.metric("Active Slots", vortex.get("active_slots", "—"))
            c2.metric("Total Equity", f"${vortex.get('total_equity', 0):.2f}")
            c3.metric("Total Profit", f"${vortex.get('total_profit', 0):.2f}")

            with st.expander("T.I.A. Status"):
                st.json(tia)
            with st.expander("Admiral Status"):
                st.json(admiral)
            with st.expander("Authorization"):
                st.json(fleet.get("authorization", {}))
    except Exception as e:
        st.error(f"Fleet inventory error: {e}")

    st.markdown("---")
    st.subheader("🧠 T.I.A. Risk Summary")
    try:
        summary = api_get("/inventory/tia/summary")
        if summary.get("status") in ("UNREACHABLE", "TIMEOUT", "ERROR"):
            st.warning(f"T.I.A. unavailable: {summary.get('error')}")
        else:
            st.json(summary)
    except Exception as e:
        st.error(f"T.I.A. summary error: {e}")

    st.markdown("---")
    st.subheader("🔌 Pioneer Trader Connection")
    try:
        health = api_get("/inventory/health")
        if health.get("status") in ("UNREACHABLE", "TIMEOUT", "ERROR"):
            st.error(f"⚠️ Pioneer Trader not connected: {health.get('error')}")
        else:
            st.success("✅ Connected to Pioneer Trader")
            st.json(health)
    except Exception as e:
        st.error(f"Health check error: {e}")

def render_future_modules_deck():
    st.title("🧩 Module Health & Future Agents")

    try:
        info = api_get("/modules/health")
        st.subheader("Registered Modules & Capabilities")
        st.json(info)
    except Exception as e:
        st.error(f"Module health unavailable: {e}")

    st.markdown("---")
    st.subheader("📡 Cross-Module Events")
    try:
        events = api_get("/modules/events")
        if not events:
            st.info("No module events recorded yet.")
        else:
            df = pd.DataFrame(events)
            df["ts"] = pd.to_datetime(df["ts"])
            st.dataframe(df, use_container_width=True)

            fig = px.scatter(
                df,
                x="ts",
                y="module",
                color="module",
                title="Module Activity Timeline",
                hover_data=["event", "tags"],
            )
            st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Event timeline unavailable: {e}")

    st.markdown("---")
    st.subheader("Policy & Admin")
    if st.button("Reload Policies"):
        try:
            api_post("/admin/reload")
            st.success("Policy engine reloaded.")
        except Exception as e:
            st.error(f"Reload failed: {e}")

def main():
    st.sidebar.title("Pioneer Ecosystem")
    module = st.sidebar.radio(
        "Active Module",
        ["Admiral (Trading)", "Perimeter Scout (Security)", "TIA (Intel)", "Mapping & Inventory", "Future Modules"],
    )

    if module == "Admiral (Trading)":
        render_admiral_deck()
    elif module == "Perimeter Scout (Security)":
        render_perimeter_scout_deck()
    elif module == "TIA (Intel)":
        render_tia_deck()
    elif module == "Mapping & Inventory":
        render_mapping_inventory_deck()
    else:
        render_future_modules_deck()

if __name__ == "__main__":
    main()