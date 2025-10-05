import pygame
import time
import json
import os
import random

pygame.init()

# ----------------------------------------
# Constants and Globals
# ----------------------------------------

WIDTH, HEIGHT = 900, 600
GRID_SIZE = 30

FONT_SMALL = pygame.font.Font(None, 20)
FONT = pygame.font.Font(None, 24)
BIG_FONT = pygame.font.Font(None, 32)

COLOR_GRASS = (10, 255, 10)
COLOR_FARMED_DIRT = (88, 57, 39)
COLOR_WATERED_DIRT = (60, 70, 69)
COLOR_WITHERED = (50, 20, 20)
COLOR_PLANT_STAGE = [(80, 180, 90), (40, 220, 40), (240, 220, 50)]
COLOR_MONEY_FACTORY = (0, 255, 255)
COLOR_ENERGY_FACTORY = (255, 165, 0)
COLOR_FERTILIZER_FACTORY = (128, 0, 128)

MODE_CURSOR = "Cursor"
MODE_DEFAULT = "Default"
MODE_WATERING = "Watering"

DAY_LENGTH_SEC = 180  # Each in-game day is 5 real seconds


class CurrencyManager:
    currencies = {"Money": 100, "Energy": 50}

    @classmethod
    def add_currency(cls, currency, amount):
        cls.currencies[currency] = cls.currencies.get(currency, 0) + amount

    @classmethod
    def deduct_currency(cls, currency, amount):
        if cls.currencies.get(currency, 0) >= amount:
            cls.currencies[currency] -= amount
            return True
        return False

    @classmethod
    def get_currency(cls, currency):
        return cls.currencies.get(currency, 0)


class Inventory:
    def __init__(self):
        self.seeds = {}  # seed_tag -> count
        self.buildings = {}  # building_tag -> count

    def add_seed(self, seed_tag, amount=1):
        self.seeds[seed_tag] = self.seeds.get(seed_tag, 0) + amount

    def add_building(self, building_tag, amount=1):
        self.buildings[building_tag] = self.buildings.get(building_tag, 0) + amount

    def use_seed(self, seed_tag):
        if self.seeds.get(seed_tag, 0) > 0:
            self.seeds[seed_tag] -= 1
            if self.seeds[seed_tag] == 0:
                del self.seeds[seed_tag]
            return True
        return False

    def use_building(self, building_tag):
        if self.buildings.get(building_tag, 0) > 0:
            self.buildings[building_tag] -= 1
            if self.buildings[building_tag] == 0:
                del self.buildings[building_tag]
            return True
        return False


class GrassTile:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, GRID_SIZE, GRID_SIZE)
        self.farm = False
        self.humidity = 100
        self.planted_seed = None
        self.growth_stage = 0
        self.growth_time = 0
        self.withered = False
        self.building = None
        self.ready_to_harvest = False

    def update(self, dt, environment):
        if self.farm and not self.building:
            dry_rate = 5 * dt
            self.humidity = max(0, self.humidity - dry_rate)
            if self.humidity == 0 and self.planted_seed and not self.withered:
                self.withered = True

        old_stage = self.growth_stage
        if self.planted_seed and not self.withered and self.humidity > 20:
            self.growth_time += dt
            if self.growth_time > 30:
                self.growth_stage = 2
            elif self.growth_time > 15:
                self.growth_stage = 1

        if old_stage < 2 and self.growth_stage == 2:
            self.ready_to_harvest = True

    def draw(self, surface):
        if self.building:
            color = {
                "MoneyFactory": COLOR_MONEY_FACTORY,
                "EnergyFactory": COLOR_ENERGY_FACTORY,
                "FertilizerFactory": COLOR_FERTILIZER_FACTORY
            }.get(self.building, (255, 255, 255))
        elif self.farm:
            if self.withered:
                color = COLOR_WITHERED
            elif self.planted_seed:
                base = COLOR_PLANT_STAGE[self.growth_stage]
                brightness_factor = max(0.4, self.humidity / 100)
                color = tuple(min(255, int(c * brightness_factor)) for c in base)
            elif self.humidity < 30:
                color = COLOR_WATERED_DIRT
            else:
                color = COLOR_FARMED_DIRT
        else:
            color = COLOR_GRASS

        pygame.draw.rect(surface, color, self.rect)
        pygame.draw.rect(surface, (50, 50, 50), self.rect, 1)


class Button:
    def __init__(self, rect, text, callback):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.callback = callback
        self.font = FONT

    def update(self, mouse_pos, mouse_pressed):
        self.is_hover = self.rect.collidepoint(mouse_pos)
        if self.is_hover and mouse_pressed[0]:
            self.callback()

    def draw(self, surface):
        base_color = (70, 70, 70)
        hover_color = (100, 150, 100)
        color = hover_color if getattr(self, "is_hover", False) else base_color
        pygame.draw.rect(surface, color, self.rect, border_radius=5)
        txt_surf = self.font.render(self.text, True, (255, 255, 255))
        txt_rect = txt_surf.get_rect(center=self.rect.center)
        surface.blit(txt_surf, txt_rect)


class ScrollableList:
    def __init__(self, rect, font=None, bg_color=(40, 40, 50), fg_color=(255, 255, 255)):
        self.rect = pygame.Rect(rect)
        self.font = font or FONT_SMALL
        self.bg_color = bg_color
        self.fg_color = fg_color
        self.items = []
        self.scroll_offset = 0
        self.max_visible_items = max((self.rect.height - 10) // 30, 1)
        self.last_click_time = 0
        self.click_delay = 300  # milliseconds

    def add_item(self, label, callback):
        self.items.append((label, callback))

    def clear(self):
        self.items.clear()
        self.scroll_offset = 0

    def draw(self, surface):
        pygame.draw.rect(surface, self.bg_color, self.rect, border_radius=5)
        y = self.rect.y + 5
        visible = self.items[
            self.scroll_offset : self.scroll_offset + self.max_visible_items
        ]
        mouse_pos = pygame.mouse.get_pos()
        for label, _ in visible:
            item_rect = pygame.Rect(self.rect.x + 5, y, self.rect.width - 10, 25)
            if item_rect.collidepoint(mouse_pos):
                pygame.draw.rect(surface, (70, 110, 70), item_rect)
            txt = self.font.render(label, True, self.fg_color)
            surface.blit(txt, (item_rect.x + 5, item_rect.y + 3))
            y += 30

    def update(self, mouse_pos, mouse_pressed):
        if mouse_pressed[0]:
            now = pygame.time.get_ticks()
            if now - self.last_click_time < self.click_delay:
                return  # debounce
            y = self.rect.y + 5
            for idx in range(
                self.scroll_offset,
                min(len(self.items), self.scroll_offset + self.max_visible_items),
            ):
                label, callback = self.items[idx]
                item_rect = pygame.Rect(self.rect.x + 5, y, self.rect.width - 10, 25)
                if item_rect.collidepoint(mouse_pos):
                    callback()
                    self.last_click_time = now
                    break
                y += 30


class Game:
    def __init__(self):
        self.win = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Farming Game")
        self.clock = pygame.time.Clock()
        self.running = True

        self.tiles = [GrassTile(x, y) for y in range(0, HEIGHT, GRID_SIZE) for x in range(0, WIDTH, GRID_SIZE)]

        self.inventory = Inventory()

        self.seeds_shop = {"wheat": 5}
        self.buildings_shop = {
            "MoneyFactory": 70,
            "EnergyFactory": 50,
            "FertilizerFactory": 40,
        }

        self.placing_item_type = None
        self.placing_item_tag = None

        self.mode = MODE_CURSOR

        self.start_time = time.time()
        self.last_day_num = 0

        self.environment = {
            "temperature": 20,
            "humidity": 50,
            "soil_moisture": 100,
        }

        try:
            # Load hammer cursor image
            hammer_img = pygame.image.load("Game/Assets/hammer.png").convert_alpha()
            hammer_img = pygame.transform.smoothscale(hammer_img, (40, 40))
            hammer_img.set_colorkey((255, 255, 255))
            self.cursor_img_building = hammer_img

            # Load seeding cursor image
            seeding_img = pygame.image.load("Game/Assets/seeding.png").convert_alpha()
            seeding_img = pygame.transform.smoothscale(seeding_img, (50, 50))
            seeding_img.set_colorkey((255, 255, 255))
            self.cursor_img_seeding = seeding_img

        except Exception as e:
            print(f"Failed to load cursor images: {e}")
            self.cursor_img_building = None
            self.cursor_img_seeding = None

        self.buttons = []
        self.buttons.append(Button((10, 10, 100, 40), "Inventory", self.toggle_inventory))
        self.buttons.append(Button((120, 10, 100, 40), "Shop", self.toggle_shop))
        self.buttons.append(Button((230, 10, 100, 40), "Info", self.toggle_info))

        self.buttons.append(Button((WIDTH - 460, 10, 130, 40), "Cursor", self.set_mode_cursor))
        self.buttons.append(Button((WIDTH - 310, 10, 130, 40), "Default", self.set_mode_default))
        self.buttons.append(Button((WIDTH - 160, 10, 130, 40), "Watering", self.set_mode_watering))

        self.show_inventory = False
        self.show_shop = False
        self.show_info = False

        inv_panel_w, inv_panel_h = 700, 400
        inv_x, inv_y = 100, 100

        self.inventory_list_seeds = ScrollableList((inv_x + 20, inv_y + 70, (inv_panel_w // 2) - 40, inv_panel_h - 100), FONT_SMALL)
        self.inventory_list_buildings = ScrollableList((inv_x + (inv_panel_w // 2) + 20, inv_y + 70, (inv_panel_w // 2) - 40, inv_panel_h - 100), FONT_SMALL)
        self.shop_list_seeds = ScrollableList((inv_x + 20, inv_y + 70, (inv_panel_w // 2) - 40, inv_panel_h - 100), FONT_SMALL)
        self.shop_list_buildings = ScrollableList((inv_x + (inv_panel_w // 2) + 20, inv_y + 70, (inv_panel_w // 2) - 40, inv_panel_h - 100), FONT_SMALL)

    def post_notification(self, text):
        self.notification = text
        self.notification_time = time.time()

    def set_mode_cursor(self):
        self.mode = MODE_CURSOR
        self.post_notification("Switched to Cursor mode")
        self.clear_placement()

    def set_mode_default(self):
        self.mode = MODE_DEFAULT
        self.post_notification("Switched to Default mode (Plow)")
        self.clear_placement()

    def set_mode_watering(self):
        self.mode = MODE_WATERING
        self.post_notification("Switched to Watering mode")
        self.clear_placement()

    def toggle_inventory(self):
        self.show_inventory = not self.show_inventory
        if self.show_inventory:
            self.show_shop = False
            self.show_info = False
            self.clear_placement()
            self.update_inventory_lists()
        self.post_notification("Inventory toggled")

    def toggle_shop(self):
        self.show_shop = not self.show_shop
        if self.show_shop:
            self.show_inventory = False
            self.show_info = False
            self.clear_placement()
            self.update_shop_lists()
        self.post_notification("Shop toggled")

    def toggle_info(self):
        self.show_info = not self.show_info
        if self.show_info:
            self.show_inventory = False
            self.show_shop = False
            self.clear_placement()
        self.post_notification("Info toggled")

    def clear_placement(self):
        self.placing_item_type = None
        self.placing_item_tag = None

    def update_inventory_lists(self):
        self.inventory_list_seeds.clear()
        self.inventory_list_buildings.clear()
        for seed, count in sorted(self.inventory.seeds.items()):
            def on_select(s=seed):
                self.placing_item_type = "seed"
                self.placing_item_tag = s
                self.show_inventory = False
                self.post_notification(f"Selected seed '{s}' for planting")
            self.inventory_list_seeds.add_item(f"{seed} (x{count})", on_select)
        for bld, count in sorted(self.inventory.buildings.items()):
            def on_select(b=bld):
                self.placing_item_type = "building"
                self.placing_item_tag = b
                self.show_inventory = False
                self.post_notification(f"Selected building '{b}' for placement")
            self.inventory_list_buildings.add_item(f"{bld} (x{count})", on_select)

    def update_shop_lists(self):
        self.shop_list_seeds.clear()
        self.shop_list_buildings.clear()
        for seed, price in self.seeds_shop.items():
            def on_buy(s=seed, p=price):
                if CurrencyManager.deduct_currency("Money", p):
                    self.inventory.add_seed(s, 1)
                    self.post_notification(f"Bought seed {s} for ${p}")
                else:
                    self.post_notification("Not enough money!")
            self.shop_list_seeds.add_item(f"{seed} - ${price}", on_buy)
        for bld, price in self.buildings_shop.items():
            def on_buy(b=bld, p=price):
                if CurrencyManager.deduct_currency("Money", p):
                    self.inventory.add_building(b, 1)
                    self.post_notification(f"Bought building {b} for ${p}")
                else:
                    self.post_notification("Not enough money!")
            self.shop_list_buildings.add_item(f"{bld} - ${price}", on_buy)

    def load_environment_from_json(self, filename="environment_data.json"):
        if not os.path.exists(filename):
            self.post_notification(f"Environment file '{filename}' not found!")
            return

        try:
            with open(filename, "r") as f:
                data_list = json.load(f)
        except Exception as e:
            self.post_notification(f"Failed to load environment JSON: {e}")
            return

        elapsed_seconds = time.time() - self.start_time
        elapsed_days = int(elapsed_seconds // DAY_LENGTH_SEC)  # integer number of days passed
        day_of_year = (elapsed_days % 365) + 1  # 1-based day of year

        doy_entry = next((entry for entry in data_list if entry.get("DOY") == day_of_year), None)

        if doy_entry is None:
            self.post_notification(f"No environment data found for day {day_of_year}")
            return

        self.environment["temperature"] = float(doy_entry.get("T2M", self.environment.get("temperature", 20)))

        gwet = doy_entry.get("GWETTOP", 0.5)
        if isinstance(gwet, str):
            try:
                gwet = float(gwet)
            except:
                gwet = 0.5
        self.environment["soil_moisture"] = max(0, min(100, gwet * 100))

        self.environment["humidity"] = 50  # default or computed elsewhere

        self.post_notification(f"Environment updated for day {day_of_year}")
    def save_game(self):
        data = {
            "tiles": [{
                "pos": (tile.rect.x, tile.rect.y),
                "farm": tile.farm,
                "humidity": tile.humidity,
                "planted_seed": tile.planted_seed,
                "growth_stage": tile.growth_stage,
                "growth_time": tile.growth_time,
                "withered": tile.withered,
                "building": tile.building
            } for tile in self.tiles],
            "inventory_seeds": self.inventory.seeds,
            "inventory_buildings": self.inventory.buildings,
            "currencies": CurrencyManager.currencies,
            "start_time": self.start_time,
            "environment": self.environment
        }
        with open("savegame.json", "w") as f:
            json.dump(data, f, indent=4)
        self.post_notification("Game saved!")

    def load_game(self):
        if not os.path.exists("savegame.json"):
            self.post_notification("Save file not found!")
            return
        with open("savegame.json", "r") as f:
            data = json.load(f)
        pos_to_tile = {(t.rect.x, t.rect.y): t for t in self.tiles}
        for tdata in data.get("tiles", []):
            tile = pos_to_tile.get(tuple(tdata["pos"]))
            if tile:
                tile.farm = tdata.get("farm", False)
                tile.humidity = tdata.get("humidity", 100)
                tile.planted_seed = tdata.get("planted_seed", None)
                tile.growth_stage = tdata.get("growth_stage", 0)
                tile.growth_time = tdata.get("growth_time", 0)
                tile.withered = tdata.get("withered", False)
                tile.building = tdata.get("building", None)
        self.inventory.seeds = data.get("inventory_seeds", {})
        self.inventory.buildings = data.get("inventory_buildings", {})
        CurrencyManager.currencies = data.get("currencies", {"Money":100, "Energy":50})
        self.start_time = data.get("start_time", time.time())
        self.environment = data.get("environment", self.environment)
        self.post_notification("Game loaded!")

    # -------------------
    # Daily update
    # -------------------

    def daily_update(self, day_num):
        self.post_notification(f"Day {day_num} has started!")
        self.load_environment_from_json()

    # -------------------
    # Main loop methods
    # -------------------

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_s:
                    self.save_game()
                elif event.key == pygame.K_l:
                    self.load_game()

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = event.pos

                # Check if any top button is clicked and call its callback
                for btn in self.buttons:
                    if btn.rect.collidepoint(pos):
                        btn.callback()
                        break
                else:
                    # If no buttons clicked, handle panel item clicks or game tile clicks

                    # Inventory panel clicks to select seeds or buildings
                    if self.show_inventory:
                        inv_x_start = 100
                        inv_x_end = 350
                        seeds_start_y = 160

                        if inv_x_start <= pos[0] <= inv_x_end:
                            idx = (pos[1] - seeds_start_y) // 30
                            seeds_list = list(self.inventory.seeds.items())
                            if 0 <= idx < len(seeds_list):
                                seed, _ = seeds_list[idx]
                                self.placing_item_type = "seed"
                                self.placing_item_tag = seed
                                self.show_inventory = False
                                self.post_notification(f"Selected seed '{seed}' for planting")
                                pygame.time.wait(200)
                                continue

                        bld_x_start = 370
                        bld_x_end = 700
                        buildings_start_y = 160

                        if bld_x_start <= pos[0] <= bld_x_end:
                            idx = (pos[1] - buildings_start_y) // 30
                            buildings_list = list(self.inventory.buildings.items())
                            if 0 <= idx < len(buildings_list):
                                bld, _ = buildings_list[idx]
                                self.placing_item_type = "building"
                                self.placing_item_tag = bld
                                self.show_inventory = False
                                self.post_notification(f"Selected building '{bld}' for placement")
                                pygame.time.wait(200)
                                continue

                    # Shop panel clicks to buy seeds or buildings
                    elif self.show_shop:
                        shop_x_start = 100
                        shop_x_end = 350
                        seeds_shop_start_y = 160

                        if shop_x_start <= pos[0] <= shop_x_end:
                            idx = (pos[1] - seeds_shop_start_y) // 30
                            seeds_list = list(self.seeds_shop.items())
                            if 0 <= idx < len(seeds_list):
                                seed, price = seeds_list[idx]
                                if CurrencyManager.deduct_currency("Money", price):
                                    self.inventory.add_seed(seed, 1)
                                    self.post_notification(f"Bought seed {seed} for ${price}")
                                else:
                                    self.post_notification("Not enough money!")
                                pygame.time.wait(200)
                                continue

                        bld_x_start = 370
                        bld_x_end = 700
                        buildings_shop_start_y = 160

                        if bld_x_start <= pos[0] <= bld_x_end:
                            idx = (pos[1] - buildings_shop_start_y) // 30
                            buildings_list = list(self.buildings_shop.items())
                            if 0 <= idx < len(buildings_list):
                                bld, price = buildings_list[idx]
                                if CurrencyManager.deduct_currency("Money", price):
                                    self.inventory.add_building(bld, 1)
                                    self.post_notification(f"Bought building {bld} for ${price}")
                                else:
                                    self.post_notification("Not enough money!")
                                pygame.time.wait(200)
                                continue

                    # If no panel open, process game tile clicks
                    if not (self.show_inventory or self.show_shop or self.show_info):
                        self.handle_click(pos)

    def handle_click(self, pos):
        # Check button clicks first
        for btn in self.buttons:
            if btn.rect.collidepoint(pos):
                btn.callback()
                return

        clicked_tile = None
        for tile in self.tiles:
            if tile.rect.collidepoint(pos):
                clicked_tile = tile
                break

        if clicked_tile is None:
            return

        # Mode behavior
        if self.mode == MODE_DEFAULT:
            if not clicked_tile.farm:
                clicked_tile.farm = True
                clicked_tile.update_color = lambda: None  # placeholder, visual updated in draw()
                self.post_notification("Plowed soil!")

        elif self.mode == MODE_WATERING:
            if clicked_tile.farm:
                clicked_tile.humidity = min(100, clicked_tile.humidity + 20)
                self.post_notification("Watered soil!")
            else:
                self.post_notification("Can't water non-farmed soil!")

        elif self.mode == MODE_CURSOR:
            # No farming or watering actions on click
            pass

        # If placing an item (from inventory selection)
        if self.placing_item_type and self.placing_item_tag:
            if self.placing_item_type == "seed":
                if not clicked_tile.farm:
                    self.post_notification("Soil must be farmed to plant!")
                    return
                if clicked_tile.humidity < 20:
                    self.post_notification("Soil moisture too low to plant!")
                    return
                if clicked_tile.planted_seed:
                    self.post_notification("Soil already has a plant!")
                    return
                if not self.inventory.use_seed(self.placing_item_tag):
                    self.post_notification("No seeds left!")
                    return

                clicked_tile.planted_seed = self.placing_item_tag
                clicked_tile.growth_stage = 0
                clicked_tile.growth_time = 0
                clicked_tile.withered = False
                self.post_notification(f"Planted seed: {self.placing_item_tag}")
                # Clear placing mode
                self.placing_item_type = None
                self.placing_item_tag = None

            elif self.placing_item_type == "building":
                if clicked_tile.farm:
                    self.post_notification("Can't build on farmed soil!")
                    return
                if clicked_tile.building:
                    self.post_notification("Building already exists!")
                    return
                if not self.inventory.use_building(self.placing_item_tag):
                    self.post_notification("No buildings left!")
                    return

                clicked_tile.building = self.placing_item_tag
                clicked_tile.planted_seed = None  # If any plant present, remove it because building on top
                clicked_tile.growth_stage = 0
                clicked_tile.growth_time = 0
                clicked_tile.withered = False
                self.post_notification(f"Placed building: {self.placing_item_tag}")
                self.placing_item_type = None
                self.placing_item_tag = None

    def update(self, dt):
        current_time = time.time()
        elapsed = current_time - self.start_time
        day_num = int(elapsed // DAY_LENGTH_SEC) + 1

        if day_num != self.last_day_num:
            self.last_day_num = day_num
            self.daily_update(day_num)

        # Update all tiles
        for tile in self.tiles:
            tile.update(dt, self.environment)

            if tile.ready_to_harvest:
                # Harvest the crop
                harvest_values = {
                    "wheat": 10,
                    # add other seeds and their sell values here
                }
                seed_tag = tile.planted_seed
                money_earned = harvest_values.get(seed_tag, 5)

                CurrencyManager.add_currency("Money", money_earned)

                # Reset tile to grass block (not farmed)
                tile.planted_seed = None
                tile.growth_stage = 0
                tile.growth_time = 0
                tile.withered = False
                tile.farm = False  # Turns back to grass block

                tile.ready_to_harvest = False

                if hasattr(tile, "update_color"):
                    tile.update_color()

                self.post_notification(f"Auto-harvested {seed_tag} for ${money_earned}!")

        # Buildings produce:
        for tile in self.tiles:
            
            if tile.building == "MoneyFactory":
                tile.building_timer = getattr(tile, "building_timer", 0) + dt
                if tile.building_timer >= 5:
                    tile.building_timer = 0
                    CurrencyManager.add_currency("Money", 5)
                    self.post_notification("Money Factory produced $5!")
            elif tile.building == "EnergyFactory":
                tile.building_timer = getattr(tile, "building_timer", 0) + dt
                if tile.building_timer >= 8:
                    tile.building_timer = 0
                    CurrencyManager.add_currency("Energy", 10)
                    self.post_notification("Energy Factory produced 10 Energy!")
            elif tile.building == "FertilizerFactory":
                tile.building_timer = getattr(tile, "building_timer", 0) + dt
                if tile.building_timer >= 6:
                    tile.building_timer = 0
                    # Fertilize nearby farmed soil: +10 humidity
                    self.fertilize_nearby(tile)
                    self.post_notification("Fertilizer increased soil humidity nearby!")

    def fertilize_nearby(self, tile, radius=1):
        tx, ty = tile.rect.x, tile.rect.y
        for other in self.tiles:
            ox, oy = other.rect.x, other.rect.y
            if abs(tx - ox) <= GRID_SIZE * radius and abs(ty - oy) <= GRID_SIZE * radius:
                if other.farm:
                    other.humidity = min(100, other.humidity + 10)

    def draw(self):
        self.win.fill((0, 0, 0))

        # Draw tiles
        for tile in self.tiles:
            tile.draw(self.win)

        # Highlight hovered tile
        mx, my = pygame.mouse.get_pos()
        for tile in self.tiles:
            if tile.rect.collidepoint((mx, my)):
                color = (255, 255, 255)
                if self.placing_item_type:
                    if self.placing_item_type == "seed":
                        if tile.farm and not tile.planted_seed and tile.humidity >= 20:
                            color = (0, 255, 0)  # green border if valid
                        else:
                            color = (255, 0, 0)  # red invalid
                    elif self.placing_item_type == "building":
                        if not tile.farm and not tile.building:
                            color = (255, 165, 0) # orange valid
                        else:
                            color = (255, 0, 0)
                pygame.draw.rect(self.win, color, tile.rect, 3)
                break

        # Draw buttons
        for btn in self.buttons:
            btn.draw(self.win)

        # Draw HUD info
        # Mode display
        mode_text = FONT.render(f"Mode: {self.mode}", True, (255, 255, 255))
        self.win.blit(mode_text, (WIDTH - 150, 60))

        # Day info
        day_text = FONT.render(f"Day: {self.last_day_num}", True, (255, 255, 255))
        self.win.blit(day_text, (WIDTH // 2 - 50, 10))

        # Currency info
        money_text = FONT.render(f"Money: ${CurrencyManager.get_currency('Money')}", True, (255, 255, 0))
        energy_text = FONT.render(f"Energy: {CurrencyManager.get_currency('Energy')}", True, (0, 255, 255))
        self.win.blit(money_text, (WIDTH // 2 - 150, 35))
        self.win.blit(energy_text, (WIDTH // 2 + 50, 35))

        # Notification
        if time.time() - self.notification_time < 3:
            notif_text = FONT.render(self.notification, True, (255, 255, 100))
            self.win.blit(notif_text, (WIDTH // 2 - notif_text.get_width() // 2, HEIGHT - 30))

        # Inventory Panel
        if self.show_inventory:
            self.draw_inventory_panel()

        # Shop Panel
        if self.show_shop:
            self.draw_shop_panel()

        # Info Panel
        if self.show_info:
            self.draw_info_panel()
        if self.placing_item_type == "building" and self.cursor_img_building:
            pygame.mouse.set_visible(False)
            mx, my = pygame.mouse.get_pos()
            rect = self.cursor_img_building.get_rect(center=(mx, my))
            self.win.blit(self.cursor_img_building, rect)
        elif self.placing_item_type == "seed" and self.cursor_img_seeding:
            pygame.mouse.set_visible(False)
            mx, my = pygame.mouse.get_pos()
            rect = self.cursor_img_seeding.get_rect(center=(mx, my))
            self.win.blit(self.cursor_img_seeding, rect)
        else:
            # Show default system cursor if not placing
            pygame.mouse.set_visible(True)


        pygame.display.flip()

    def draw_inventory_panel(self):
        panel_rect = pygame.Rect(100, 100, 700, 400)
        pygame.draw.rect(self.win, (30, 30, 30), panel_rect)
        pygame.draw.rect(self.win, (100, 100, 100), panel_rect, 3)

        # Seeds Inventory - left side
        seed_text = BIG_FONT.render("Seeds Inventory", True, (200, 200, 255))
        self.win.blit(seed_text, (panel_rect.x + 20, panel_rect.y + 10))

        y = panel_rect.y + 60
        for seed, count in self.inventory.seeds.items():
            text = FONT.render(f"{seed} (x{count})", True, (255, 255, 255))
            self.win.blit(text, (panel_rect.x + 30, y))
            y += 30

        # Buildings Inventory - right side
        building_text = BIG_FONT.render("Buildings Inventory", True, (200, 200, 255))
        self.win.blit(building_text, (panel_rect.x + 360, panel_rect.y + 10))

        y = panel_rect.y + 60
        for bld, count in self.inventory.buildings.items():
            text = FONT.render(f"{bld} (x{count})", True, (255, 255, 255))
            self.win.blit(text, (panel_rect.x + 370, y))
            y += 30

    def draw_shop_panel(self):
        panel_rect = pygame.Rect(100, 100, 700, 400)
        pygame.draw.rect(self.win, (30, 30, 30), panel_rect)
        pygame.draw.rect(self.win, (100, 100, 100), panel_rect, 3)

        seed_text = BIG_FONT.render("Seeds Shop", True, (200, 200, 255))
        self.win.blit(seed_text, (panel_rect.x + 20, panel_rect.y + 10))

        y = panel_rect.y + 60
        for seed, price in self.seeds_shop.items():
            text = FONT.render(f"{seed} - ${price}", True, (255, 255, 255))
            self.win.blit(text, (panel_rect.x + 30, y))
            y += 30

        building_text = BIG_FONT.render("Buildings Shop", True, (200, 200, 255))
        self.win.blit(building_text, (panel_rect.x + 360, panel_rect.y + 10))

        y = panel_rect.y + 60
        for bld, price in self.buildings_shop.items():
            text = FONT.render(f"{bld} - ${price}", True, (255, 255, 255))
            self.win.blit(text, (panel_rect.x + 370, y))
            y += 30

    def draw_info_panel(self):
        panel_rect = pygame.Rect(WIDTH - 200, 80, 180, 120)
        pygame.draw.rect(self.win, (30, 30, 60), panel_rect)
        pygame.draw.rect(self.win, (100, 100, 150), panel_rect, 2)

        info_items = [
            f"Temperature: {self.environment['temperature']:.1f} °C",
            f"Humidity: {self.environment['humidity']:.1f} %",
            f"Soil Moisture: {self.environment['soil_moisture']:.1f} %",
            f"Current Day: {self.last_day_num}",
        ]

        y = panel_rect.y + 10
        for item in info_items:
            text = FONT.render(item, True, (255, 255, 255))
            self.win.blit(text, (panel_rect.x + 10, y))
            y += 25

    def run(self):
        while self.running:
            dt = self.clock.tick(60) / 1000.0
            self.handle_events()
            self.update(dt)
            self.draw()

        pygame.quit()


# ----------------------------------------
# Run Game
# ----------------------------------------
if __name__ == "__main__":
    game = Game()
    game.run()