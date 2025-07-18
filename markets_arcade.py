# markets_arcade.py
import arcade
import random
from string import ascii_uppercase

def random_name(n=6):
    return "".join(random.choices(ascii_uppercase, k=n))

# ───────────────────────────────────────────────────────────────
# Screen
SCREEN_WIDTH  = 800
SCREEN_HEIGHT = 600
SCREEN_TITLE  = "Market Simulator (Arcade + In-game GUI)"

# Defaults & bounds
DEFAULT_NUM_BUYERS  = 50
DEFAULT_NUM_SELLERS = 50
DEFAULT_ROUNDS      = 200
DEFAULT_PRICE       = 1.0
MIN_NUM             = 1
MIN_ROUNDS          = 1
MIN_PRICE           = 0.1
PRICE_STEP          = 0.1

# Total sim time (seconds)
TOTAL_SIM_TIME      = 10.0
DOT_RADIUS          = 6
TICKER_LINES        = 5  # how many recent trades to show

# ───────────────────────────────────────────────────────────────
class Actor:
    def __init__(self, name: str, cash: float, apples: int, w_cash: float, w_apple: float):
        self.name    = name
        self.cash    = cash
        self.apples  = apples
        self.w_cash  = w_cash
        self.w_apple = w_apple

    def utility(self):
        return self.w_cash * self.cash + self.w_apple * self.apples

def attempt_trade(buyer: Actor, seller: Actor, price: float) -> bool:
    if buyer.cash < price or seller.apples < 1:
        return False
    ub, us = buyer.utility(), seller.utility()
    ub2 = buyer.w_cash*(buyer.cash - price) + buyer.w_apple*(buyer.apples + 1)
    us2 = seller.w_cash*(seller.cash + price) + seller.w_apple*(seller.apples - 1)
    if ub2 > ub and us2 > us:
        buyer.cash   -= price
        buyer.apples += 1
        seller.cash  += price
        seller.apples-= 1
        return True
    return False

class ActorDot(arcade.SpriteCircle):
    def __init__(self, actor: Actor, color):
        super().__init__(DOT_RADIUS, color)
        self.actor = actor

# ───────────────────────────────────────────────────────────────
class MarketSim(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
        arcade.set_background_color(arcade.color.DARK_SLATE_GRAY)

        # GUI parameters
        self.param_names   = ["Buyers", "Sellers", "Rounds", "Price"]
        self.market_params = {
            "Buyers": DEFAULT_NUM_BUYERS,
            "Sellers": DEFAULT_NUM_SELLERS,
            "Rounds": DEFAULT_ROUNDS,
            "Price": DEFAULT_PRICE
        }
        self.selected     = 0
        self.simulating   = False

    def setup_sim(self):
        """Initialize sprites, state, and ticker."""
        self.trades_done    = 0
        self.round          = 0
        self.trade_timer    = 0.0
        self.dt_per_round   = TOTAL_SIM_TIME / self.market_params["Rounds"]
        self.current_pair   = None
        self.trade_messages = []  # ticker buffer

        # Create buyers
        self.buyers  = arcade.SpriteList()
        for _ in range(self.market_params["Buyers"]):
            name = random_name()
            actor = Actor(name, self.market_params["Price"], 0, 1.0, 2.0)
            dot   = ActorDot(actor, arcade.color.BLUE)
            dot.center_x = random.uniform(0, SCREEN_WIDTH)
            dot.center_y = random.uniform(0, SCREEN_HEIGHT)
            self.buyers.append(dot)

        # Create sellers
        self.sellers = arcade.SpriteList()
        for _ in range(self.market_params["Sellers"]):
            name = random_name()
            actor = Actor(name, 0, 10, 2.0, 1.0)
            dot   = ActorDot(actor, arcade.color.RED)
            dot.center_x = random.uniform(0, SCREEN_WIDTH)
            dot.center_y = random.uniform(0, SCREEN_HEIGHT)
            self.sellers.append(dot)

        self.simulating = True

    def on_draw(self):
        self.clear()
        if not self.simulating:
            # Parameter menu
            for i, key in enumerate(self.param_names):
                val = self.market_params[key]
                txt = f"{key}: ${val:.1f}" if key=="Price" else f"{key}: {val}"
                color = arcade.color.WHITE if i==self.selected else arcade.color.GRAY
                arcade.draw_text(
                    txt, 20, SCREEN_HEIGHT-40 - i*30, color, 18
                )
            arcade.draw_text(
                "↑/↓ select  ←/→ change  Enter/Space to run",
                20, 20, arcade.color.WHITE, 14
            )
        else:
            # Draw actors
            self.buyers.draw()
            self.sellers.draw()

            # HUD
            arcade.draw_text(
                f"Trades: {self.trades_done}   Round {self.round}/{self.market_params['Rounds']}",
                10, SCREEN_HEIGHT-30, arcade.color.WHITE, 14
            )

            # Ticker of recent trade messages
            for idx, msg in enumerate(self.trade_messages[-TICKER_LINES:]):
                arcade.draw_text(
                    msg,
                    10, SCREEN_HEIGHT - 60 - idx*20,
                    arcade.color.LIGHT_GRAY, 12
                )

    def on_update(self, dt):
        if not self.simulating:
            return

        # End condition
        if self.round >= self.market_params["Rounds"]:
            self.simulating = False
            return

        self.trade_timer += dt

        # Start a new trade if none in progress
        if self.current_pair is None:
            b = random.choice(self.buyers)
            s = random.choice(self.sellers)
            self.current_pair = (b, s)
            self.start_bpos = (b.center_x, b.center_y)
            self.start_spos = (s.center_x, s.center_y)
            self.midpoint   = (
                (b.center_x + s.center_x)/2,
                (b.center_y + s.center_y)/2
            )
            self.trade_timer = 0.0

        # Interpolate toward midpoint
        frac = min(1.0, self.trade_timer / self.dt_per_round)
        bx0, by0 = self.start_bpos
        sx0, sy0 = self.start_spos
        mx, my   = self.midpoint
        b_dot, s_dot = self.current_pair

        b_dot.center_x = bx0 + frac*(mx - bx0)
        b_dot.center_y = by0 + frac*(my - by0)
        s_dot.center_x = sx0 + frac*(mx - sx0)
        s_dot.center_y = sy0 + frac*(my - sy0)

        # Once movement complete, execute trade, scatter, and log
        if frac >= 1.0:
            buyer, seller = b_dot.actor, s_dot.actor
            if attempt_trade(buyer, seller, self.market_params["Price"]):
                self.trades_done += 1
                msg = f"{buyer.name}→{seller.name}"
                self.trade_messages.append(msg)
            # scatter both
            for spr in (b_dot, s_dot):
                spr.center_x = random.uniform(0, SCREEN_WIDTH)
                spr.center_y = random.uniform(0, SCREEN_HEIGHT)
            self.round += 1
            self.current_pair = None

    def on_key_press(self, symbol, modifiers):
        if self.simulating:
            return

        name = self.param_names[self.selected]
        if symbol == arcade.key.UP:
            self.selected = (self.selected - 1) % len(self.param_names)
        elif symbol == arcade.key.DOWN:
            self.selected = (self.selected + 1) % len(self.param_names)
        elif symbol == arcade.key.LEFT:
            if name in ("Buyers", "Sellers"):
                self.market_params[name] = max(MIN_NUM, self.market_params[name]-1)
            elif name == "Rounds":
                self.market_params[name] = max(MIN_ROUNDS, self.market_params[name]-1)
            else:
                self.market_params[name] = max(
                    MIN_PRICE,
                    round(self.market_params[name] - PRICE_STEP, 1)
                )
        elif symbol == arcade.key.RIGHT:
            if name in ("Buyers", "Sellers"):
                self.market_params[name] += 1
            elif name == "Rounds":
                self.market_params[name] += 1
            else:
                self.market_params[name] = round(
                    self.market_params[name] + PRICE_STEP,
                    1
                )
        elif symbol in (arcade.key.ENTER, arcade.key.SPACE):
            self.setup_sim()

if __name__ == "__main__":
    window = MarketSim()
    arcade.run()
