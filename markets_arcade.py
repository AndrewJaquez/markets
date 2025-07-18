# market_arcade.py
import arcade
import random
import numpy as np

# ───────────────────────────────────────────────────────────────
# Config
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN_TITLE = "Multi-Actor Market Simulation"

NUM_BUYERS    = 50
NUM_SELLERS   = 50
ROUNDS        = 200
PRICE         = 1.0

# Utility weights
W_CASH_BUYER  = 1.0
W_APPLE_BUYER = 2.0
W_CASH_SELLER = 2.0
W_APPLE_SELLER= 1.0

# How fast dots interpolate toward midpoint each frame
MOVE_SPEED = 0.08

# ───────────────────────────────────────────────────────────────
class Actor:
    def __init__(self, cash, apples, w_cash, w_apple):
        self.cash    = cash
        self.apples  = apples
        self.w_cash  = w_cash
        self.w_apple = w_apple

    def utility(self):
        return self.w_cash * self.cash + self.w_apple * self.apples

def attempt_trade(buyer: Actor, seller: Actor, price: float) -> bool:
    if buyer.cash < price or seller.apples < 1:
        return False
    ub_before = buyer.utility()
    us_before = seller.utility()
    ub_after  = buyer.w_cash * (buyer.cash - price) + buyer.w_apple * (buyer.apples + 1)
    us_after  = seller.w_cash * (seller.cash + price) + seller.w_apple * (seller.apples - 1)
    if ub_after > ub_before and us_after > us_before:
        buyer.cash   -= price
        buyer.apples += 1
        seller.cash   += price
        seller.apples -= 1
        return True
    return False

# A little wrapper so each sprite “knows” its actor
class ActorSprite(arcade.SpriteCircle):
    def __init__(self, actor: Actor, radius: int, color, **kwargs):
        super().__init__(radius, color, **kwargs)
        self.actor = actor

# ───────────────────────────────────────────────────────────────
class MarketSim(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
        arcade.set_background_color(arcade.color.DARK_SLATE_GRAY)

        # Create actors + sprites
        self.buyers  = []
        self.sellers = []
        self.buyer_sprites  = arcade.SpriteList()
        self.seller_sprites = arcade.SpriteList()

        for _ in range(NUM_BUYERS):
            a = Actor(cash=PRICE, apples=0,
                      w_cash=W_CASH_BUYER, w_apple=W_APPLE_BUYER)
            spr = ActorSprite(a, radius=6, color=arcade.color.BLUE)
            spr.center_x = random.uniform(0, SCREEN_WIDTH)
            spr.center_y = random.uniform(0, SCREEN_HEIGHT)
            self.buyers.append(a); self.buyer_sprites.append(spr)

        for _ in range(NUM_SELLERS):
            a = Actor(cash=0, apples=10,
                      w_cash=W_CASH_SELLER, w_apple=W_APPLE_SELLER)
            spr = ActorSprite(a, radius=6, color=arcade.color.RED)
            spr.center_x = random.uniform(0, SCREEN_WIDTH)
            spr.center_y = random.uniform(0, SCREEN_HEIGHT)
            self.sellers.append(a); self.seller_sprites.append(spr)

        # Simulation state
        self.trades_done = 0
        self.round       = 0
        self.current_pair = None   # (buyer_sprite, seller_sprite)
        self.midpoint     = None

    def on_draw(self):
        arcade.start_render()
        self.buyer_sprites.draw()
        self.seller_sprites.draw()

        # HUD
        arcade.draw_text(
            f"Trade # {self.trades_done}   Round {self.round}/{ROUNDS}",
            10, 10, arcade.color.WHITE, 14
        )

    def on_update(self, dt):
        if self.round >= ROUNDS:
            return  # done

        # If no trade in flight, pick new pair
        if self.current_pair is None:
            b = random.choice(self.buyer_sprites)
            s = random.choice(self.seller_sprites)
            self.current_pair = (b, s)
            bx, by = b.center_x, b.center_y
            sx, sy = s.center_x, s.center_y
            self.midpoint = ((bx+sx)/2, (by+sy)/2)
        else:
            b, s = self.current_pair
            mx, my = self.midpoint

            # move each  fraction toward midpoint
            for spr in (b, s):
                spr.center_x += (mx - spr.center_x) * MOVE_SPEED
                spr.center_y += (my - spr.center_y) * MOVE_SPEED

            # if both nearly there, do the trade
            if (abs(b.center_x - mx) < 2 and abs(b.center_y - my) < 2
            and  abs(s.center_x - mx) < 2 and abs(s.center_y - my) < 2):
                # execute logic
                if attempt_trade(b.actor, s.actor, PRICE):
                    self.trades_done += 1

                # scatter them again
                for spr in (b, s):
                    spr.center_x = random.uniform(0, SCREEN_WIDTH)
                    spr.center_y = random.uniform(0, SCREEN_HEIGHT)

                # next round
                self.round += 1
                self.current_pair = None

if __name__ == "__main__":
    MarketSim()
    arcade.run()
