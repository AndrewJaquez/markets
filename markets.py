from manim import *
import random
import numpy as np

# Simple Actor and trading logic
class Actor:
    def __init__(self, name, cash=0, apples=0, weight_cash=1.0, weight_apples=1.0):
        self.name = name
        self.cash = cash
        self.apples = apples
        self.w_cash = weight_cash
        self.w_apple = weight_apples

    def utility(self):
        return self.w_cash * self.cash + self.w_apple * self.apples

    def __repr__(self):
        return f"{self.name}(cash=${self.cash}, apples={self.apples}, u={self.utility():.1f})"


def attempt_trade(buyer: Actor, seller: Actor, price: float) -> bool:
    """Attempt to trade 1 apple for price; execute if both utilities improve."""
    if buyer.cash < price or seller.apples < 1:
        return False

    u_b_before = buyer.utility()
    u_s_before = seller.utility()
    u_b_after = buyer.w_cash * (buyer.cash - price) + buyer.w_apple * (buyer.apples + 1)
    u_s_after = seller.w_cash * (seller.cash + price) + seller.w_apple * (seller.apples - 1)

    if u_b_after > u_b_before and u_s_after > u_s_before:
        # execute
        buyer.cash -= price
        buyer.apples += 1
        seller.cash += price
        seller.apples -= 1
        return True
    return False


class MarketAnimation(Scene):
    def construct(self):
        # Initialize two actors
        buyer = Actor("Buyer", cash=1, apples=0, weight_cash=1.0, weight_apples=2.0)
        seller = Actor("Seller", cash=0, apples=5, weight_cash=2.0, weight_apples=1.0)
        price = 1

        # Random starting points on screen
        buyer_pos = np.array([random.uniform(-6, 6), random.uniform(-3, 3), 0])
        seller_pos = np.array([random.uniform(-6, 6), random.uniform(-3, 3), 0])

        # Create dots and labels
        buyer_dot = Dot(buyer_pos, color=BLUE)
        seller_dot = Dot(seller_pos, color=RED)
        buyer_label = Text("Buyer").next_to(buyer_dot, DOWN)
        seller_label = Text("Seller").next_to(seller_dot, DOWN)

        # Add to scene
        self.add(buyer_dot, buyer_label, seller_dot, seller_label)
        self.wait(1)

        # Compute midpoint
        midpoint = (buyer_pos + seller_pos) / 2

        # Animate both moving to midpoint
        self.play(
            buyer_dot.animate.move_to(midpoint),
            seller_dot.animate.move_to(midpoint),
            run_time=2
        )
        self.wait(0.5)

        # Attempt the trade and log
        if attempt_trade(buyer, seller, price):
            print(f"Transaction: {buyer.name} buys 1 apple from {seller.name} for ${price}")
            # Display a text on screen
            txn_text = Text(f"{buyer.name} → {seller.name}: 1 apple @ ${price}")
            txn_text.to_edge(UP)
            self.play(Write(txn_text))
            self.wait(2)
        else:
            print("No mutually beneficial trade possible.")
            fail_text = Text("Trade failed", color=GRAY).to_edge(UP)
            self.play(FadeIn(fail_text))
            self.wait(2)
