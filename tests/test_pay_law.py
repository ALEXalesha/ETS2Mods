"""Job pay law (report of 10.10.2026: "are we really getting x10 pay?").

Big Money 1.0-1.1 set revenue_per_km_base 15 -> 150. The freight market then
showed the same pay as without the mod (about 3 900 RUB/km = 41.5 EUR/km). The
numbers below are field data: delivered jobs from the delivery log of a 1.61
save and the cargo definitions (def/cargo/*.sui) of the game.

They show how 1.61 pays a job:
    pay ~= fixed + distance * units * unit_reward_per_km * revenue_coef * bonuses
where revenue_coef is revenue_coef_per_km (freight market) or
driver_revenue_coef_per_km (quick jobs, hired drivers), and the bonuses come
from the level and the skills. revenue_per_km_base (15) is not a factor: if it
were, a full tanker of 30 units x 1.2 EUR/km would earn about 15 * 36 = 540
EUR/km, not the 30-35 EUR/km the log shows.

So x10 pay has to scale the revenue coefficients and fixed_revenue. These
checks need neither the game nor a save.
"""

import json
import os
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick jobs (driver_revenue_coef_per_km 0.67), from the delivery log:
# cargo, units, unit_reward_per_km (def/cargo/<cargo>.sui), distance km, planned pay EUR
QUICK_JOBS = [
    ("kerosene", 30, 1.200, 1832, 59936),
    ("petrol", 30, 1.150, 2433, 74117),
    ("diesel", 30, 1.200, 1377, 42053),
    ("sulfuric_t", 13, 2.690, 2107, 72255),
    ("fuel_oil", 27, 1.210, 2268, 68248),
    ("ammonia", 37, 1.050, 1103, 39606),
    ("lead", 80, 0.295, 1924, 45174),
    ("watertank", 2, 10.860, 2194, 35920),
    ("watermelons", 33, 0.603, 1929, 31208),
]

# Freight market offers from the screenshot of 10.10 (Russian UI, currency RUB),
# matched to the save's job offers: cargo, units, unit_reward_per_km, shortest
# distance km, shown total RUB, shown RUB/km.
FREIGHT_SCREENSHOT = [
    ("ethane", 40, 0.720, 1242, 4875689, 3899.19),
    ("boric_acid", 33, 0.765, 1784, 7123014, 3974.28),
]
RUB_RATIO = 93.991          # def/economy_data.sii, currency_code[] "RUB"

VANILLA = {                  # def/economy_data.sii of 1.61
    "revenue_per_km_base": 15.0,
    "fixed_revenue": 600.0,
    "revenue_coef_per_km": 0.9,
    "cargo_market_revenue_coef_per_km": 1.0,
    "driver_revenue_coef_per_km": 0.67,
    "driver_cargo_market_revenue_coef_per_km": 0.70,
}
PAY_COEFS = ("revenue_coef_per_km", "cargo_market_revenue_coef_per_km",
             "driver_revenue_coef_per_km", "driver_cargo_market_revenue_coef_per_km")


def money_patches():
    with open(os.path.join(ROOT, "mods", "money", "mod.json"), encoding="utf-8") as fh:
        spec = json.load(fh)
    return {p["key"]: p for p in spec["patches"]["def/economy_data.sii"]}


class FieldDataTest(unittest.TestCase):
    def test_pay_follows_cargo_reward_not_revenue_per_km_base(self):
        for cargo, units, reward, km, pay in QUICK_JOBS:
            per_unit = pay / (km * units * reward)
            # 0.67 x bonuses (level, skills) lands between 0.6 and 1.1
            self.assertGreater(per_unit, 0.6, cargo)
            # with revenue_per_km_base (15) as a factor it would be 9 or more
            self.assertLess(per_unit, 1.1, cargo)

    def test_screenshot_is_vanilla_pay(self):
        """The screenshot shows vanilla-level pay: about 41-43 EUR/km, about 1.1-1.9 per cargo unit."""
        for cargo, units, reward, km, total_rub, per_km_rub in FREIGHT_SCREENSHOT:
            eur = total_rub / RUB_RATIO
            self.assertAlmostEqual(per_km_rub / RUB_RATIO, 42, delta=1.5, msg=cargo)
            per_unit = eur / (km * units * reward)
            self.assertGreater(per_unit, 1.0, cargo)
            self.assertLess(per_unit, 2.0, cargo)       # x10 pay would be above 10


class BigMoneyLawTest(unittest.TestCase):
    def test_scales_the_pay_coefficients_x10(self):
        p = money_patches()
        for key in PAY_COEFS:
            self.assertIn(key, p, key)
            self.assertAlmostEqual(float(p[key]["value"]), VANILLA[key] * 10, places=6, msg=key)
        self.assertAlmostEqual(float(p["fixed_revenue"]["value"]), VANILLA["fixed_revenue"] * 10)

    def test_does_not_touch_revenue_per_km_base(self):
        # not a pay factor in 1.61 (see above); leave it vanilla
        self.assertNotIn("revenue_per_km_base", money_patches())

    def test_expected_pay_for_the_screenshot_jobs(self):
        """With the mod the same offers would show about 10x: 39 000-40 000 RUB/km instead of 3 900-4 000."""
        p = money_patches()
        k = float(p["revenue_coef_per_km"]["value"]) / VANILLA["revenue_coef_per_km"]
        f = float(p["fixed_revenue"]["value"]) - VANILLA["fixed_revenue"]
        for cargo, units, reward, km, total_rub, per_km_rub in FREIGHT_SCREENSHOT:
            eur = total_rub / RUB_RATIO
            new_eur = (eur - VANILLA["fixed_revenue"]) * k + VANILLA["fixed_revenue"] + f
            self.assertGreater(new_eur / eur, 9.5, cargo)
            self.assertLess(new_eur / eur, 10.5, cargo)


if __name__ == "__main__":
    unittest.main()
