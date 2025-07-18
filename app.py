# app.py
import streamlit as st
import tempfile, subprocess, os, shutil
from pathlib import Path

st.title("🛒 Market Simulator + Manim Animation")

# Sidebar controls
st.sidebar.header("Market Parameters")
num_buyers     = st.sidebar.number_input("Number of Buyers",   min_value=1,   max_value=200, value=20)
num_sellers    = st.sidebar.number_input("Number of Sellers",  min_value=1,   max_value=200, value=20)
rounds         = st.sidebar.number_input("Simulation Rounds",  min_value=1,   max_value=100, value=10)
price          = st.sidebar.number_input("Price per Apple",    min_value=0.1, max_value=10.0, step=0.1, value=1.0)
w_cash_buyer   = st.sidebar.slider("Buyer Cash Weight",   0.1, 5.0, value=1.0)
w_apple_buyer  = st.sidebar.slider("Buyer Apple Weight",  0.1, 5.0, value=2.0)
w_cash_seller  = st.sidebar.slider("Seller Cash Weight",  0.1, 5.0, value=2.0)
w_apple_seller = st.sidebar.slider("Seller Apple Weight", 0.1, 5.0, value=1.0)

if st.sidebar.button("🎥 Generate Animation"):
    tmp = tempfile.mkdtemp()
    script_path = Path(tmp) / "market_manim.py"

    # Write the Manim script
    script_path.write_text(f'''
from manim import *
import random
import numpy as np

class Actor:
    def __init__(self, name, cash=0, apples=0, weight_cash=1.0, weight_apples=1.0):
        self.name   = name
        self.cash   = cash
        self.apples = apples
        self.w_cash = weight_cash
        self.w_apple= weight_apples
    def utility(self):
        return self.w_cash * self.cash + self.w_apple * self.apples

def attempt_trade(buyer, seller, price):
    if buyer.cash < price or seller.apples < 1:
        return False
    u_b_before = buyer.utility()
    u_s_before = seller.utility()
    u_b_after  = buyer.w_cash * (buyer.cash - price) + buyer.w_apple * (buyer.apples + 1)
    u_s_after  = seller.w_cash * (seller.cash + price) + seller.w_apple * (seller.apples - 1)
    if u_b_after > u_b_before and u_s_after > u_s_before:
        buyer.cash   -= price
        buyer.apples += 1
        seller.cash   += price
        seller.apples -= 1
        return True
    return False

class MarketAnimation(Scene):
    def construct(self):
        buyers = [
            Actor(f"Buyer{{i}}", cash={price}, apples=0,
                  weight_cash={w_cash_buyer}, weight_apples={w_apple_buyer})
            for i in range({num_buyers})
        ]
        sellers = [
            Actor(f"Seller{{j}}", cash=0, apples=10,
                  weight_cash={w_cash_seller}, weight_apples={w_apple_seller})
            for j in range({num_sellers})
        ]
        trades = 0
        for _ in range({rounds}):
            b = random.choice(buyers)
            s = random.choice(sellers)
            b_pos = np.array([random.uniform(-6,6), random.uniform(-3,3),0])
            s_pos = np.array([random.uniform(-6,6), random.uniform(-3,3),0])
            b_dot = Dot(b_pos, color=BLUE); s_dot = Dot(s_pos, color=RED)
            self.add(b_dot, s_dot)
            self.play(
                b_dot.animate.move_to((b_pos+s_pos)/2),
                s_dot.animate.move_to((b_pos+s_pos)/2),
                run_time=1,
            )
            if attempt_trade(b, s, {price}):
                trades += 1
                lbl = Text(f"Trade {{trades}}").to_edge(UP)
                self.play(Write(lbl), run_time=0.5)
                self.remove(lbl)
            else:
                lbl = Text("No trade", color=GREY).to_edge(UP)
                self.play(FadeIn(lbl), run_time=0.5)
                self.remove(lbl)
        summary = Text(f"Total Trades: {{trades}}", font_size=32).to_edge(DOWN)
        self.play(Write(summary))
        self.wait(2)
''')

    # Run Manim and capture output
    cmd = ["manim", "-ql", str(script_path), "MarketAnimation"]
    proc = subprocess.run(cmd, cwd=tmp, capture_output=True, text=True)

    if proc.returncode != 0:
        st.error("⚠️ Manim failed:")
        st.text("⟵ stdout ⟵")
        st.code(proc.stdout)
        st.text("⟵ stderr ⟵")
        st.code(proc.stderr)
        shutil.rmtree(tmp, ignore_errors=True)
        st.stop()

    # Locate and show the video
    video_file = None
    for root, _, files in os.walk(tmp):
        for fn in files:
            if fn.endswith(".mp4"):
                video_file = os.path.join(root, fn)
                break
        if video_file:
            break

    if video_file:
        st.video(video_file)
    else:
        st.error("❌ Could not find the rendered video.")

    # Clean up
    shutil.rmtree(tmp, ignore_errors=True)
