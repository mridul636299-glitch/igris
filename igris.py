import math
import random
import time
import tkinter as tk


WIDTH = 960
HEIGHT = 600
FPS_MS = 16


def clamp(value, low, high):
    return max(low, min(high, value))


def distance(a, b, c, d):
    return math.hypot(a - c, b - d)


class IgrisGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Igris")
        self.canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg="#11131a", highlightthickness=0)
        self.canvas.pack()

        self.keys = set()
        self.last_time = time.perf_counter()
        self.running = True
        self.paused = False

        self.root.bind("<KeyPress>", self.key_down)
        self.root.bind("<KeyRelease>", self.key_up)
        self.canvas.focus_set()

        self.reset()
        self.loop()

    def reset(self):
        self.player = {
            "x": WIDTH / 2,
            "y": HEIGHT / 2,
            "r": 18,
            "speed": 245,
            "hp": 120,
            "max_hp": 120,
            "attack_cd": 0,
            "dash_cd": 0,
            "summon_cd": 0,
            "dash_time": 0,
            "invuln": 0,
            "facing_x": 1,
            "facing_y": 0,
        }
        self.wave = 0
        self.score = 0
        self.kills = 0
        self.enemies = []
        self.projectiles = []
        self.slashes = []
        self.shadows = []
        self.particles = []
        self.wave_delay = 0
        self.message = "IGRIS - Press Space to strike"
        self.message_time = 3.0
        self.game_over = False
        self.victory = False
        self.spawn_next_wave()

    def key_down(self, event):
        key = event.keysym.lower()
        self.keys.add(key)
        if key == "r" and (self.game_over or self.victory):
            self.reset()
        elif key == "p":
            self.paused = not self.paused
        elif key == "space":
            self.try_attack()
        elif key in ("shift_l", "shift_r"):
            self.try_dash()
        elif key == "e":
            self.try_summon()

    def key_up(self, event):
        self.keys.discard(event.keysym.lower())

    def spawn_next_wave(self):
        self.wave += 1
        self.message_time = 2.5

        if self.wave == 6:
            self.message = "The Crownless Monarch descends"
            self.spawn_enemy("monarch", WIDTH / 2, 80)
            return

        self.message = f"Wave {self.wave}: Hold the throne room"
        count = 4 + self.wave * 2
        for _ in range(count):
            kind_roll = random.random()
            if self.wave >= 4 and kind_roll < 0.22:
                kind = "knight"
            elif self.wave >= 2 and kind_roll < 0.45:
                kind = "archer"
            else:
                kind = "pawn"
            x, y = self.edge_spawn()
            self.spawn_enemy(kind, x, y)

    def edge_spawn(self):
        edge = random.choice(("top", "bottom", "left", "right"))
        if edge == "top":
            return random.randint(20, WIDTH - 20), -30
        if edge == "bottom":
            return random.randint(20, WIDTH - 20), HEIGHT + 30
        if edge == "left":
            return -30, random.randint(20, HEIGHT - 20)
        return WIDTH + 30, random.randint(20, HEIGHT - 20)

    def spawn_enemy(self, kind, x, y):
        stats = {
            "pawn": {"hp": 28, "speed": 95, "r": 14, "damage": 10, "score": 50},
            "archer": {"hp": 24, "speed": 70, "r": 13, "damage": 8, "score": 65},
            "knight": {"hp": 62, "speed": 58, "r": 18, "damage": 16, "score": 110},
            "monarch": {"hp": 520, "speed": 48, "r": 34, "damage": 22, "score": 1000},
        }[kind]
        enemy = {
            "kind": kind,
            "x": x,
            "y": y,
            "hp": stats["hp"],
            "max_hp": stats["hp"],
            "speed": stats["speed"],
            "r": stats["r"],
            "damage": stats["damage"],
            "score": stats["score"],
            "touch_cd": 0,
            "shoot_cd": random.uniform(0.5, 2.0),
            "charge_cd": random.uniform(2.5, 4.0),
            "flash": 0,
        }
        self.enemies.append(enemy)

    def try_attack(self):
        if self.game_over or self.victory or self.paused:
            return
        if self.player["attack_cd"] > 0:
            return
        self.player["attack_cd"] = 0.36
        slash = {
            "x": self.player["x"],
            "y": self.player["y"],
            "dx": self.player["facing_x"],
            "dy": self.player["facing_y"],
            "life": 0.14,
            "max_life": 0.14,
            "radius": 78,
            "hit": set(),
        }
        self.slashes.append(slash)
        self.add_particles(self.player["x"] + slash["dx"] * 40, self.player["y"] + slash["dy"] * 40, "#f2c96d", 7)

    def try_dash(self):
        if self.game_over or self.victory or self.paused:
            return
        if self.player["dash_cd"] > 0:
            return
        self.player["dash_cd"] = 2.25
        self.player["dash_time"] = 0.18
        self.player["invuln"] = 0.35
        self.add_particles(self.player["x"], self.player["y"], "#6a88ff", 18)

    def try_summon(self):
        if self.game_over or self.victory or self.paused:
            return
        if self.player["summon_cd"] > 0 or not self.enemies:
            return
        self.player["summon_cd"] = 5.5
        targets = sorted(
            self.enemies,
            key=lambda enemy: distance(self.player["x"], self.player["y"], enemy["x"], enemy["y"]),
        )[:4]
        for index, target in enumerate(targets):
            angle = math.atan2(target["y"] - self.player["y"], target["x"] - self.player["x"])
            self.shadows.append(
                {
                    "x": self.player["x"] - math.cos(angle) * 26 + (index - 1.5) * 10,
                    "y": self.player["y"] - math.sin(angle) * 26,
                    "dx": math.cos(angle),
                    "dy": math.sin(angle),
                    "life": 1.0,
                    "damage": 34,
                    "hit": set(),
                }
            )
        self.message = "Royal Call"
        self.message_time = 0.8

    def loop(self):
        now = time.perf_counter()
        dt = min(now - self.last_time, 0.05)
        self.last_time = now

        if self.running and not self.paused:
            self.update(dt)
        self.draw()
        self.root.after(FPS_MS, self.loop)

    def update(self, dt):
        if self.game_over or self.victory:
            return

        player = self.player
        for key in ("attack_cd", "dash_cd", "summon_cd", "dash_time", "invuln"):
            player[key] = max(0, player[key] - dt)
        self.message_time = max(0, self.message_time - dt)

        self.update_player(dt)
        self.update_slashes(dt)
        self.update_shadows(dt)
        self.update_enemies(dt)
        self.update_projectiles(dt)
        self.update_particles(dt)

        self.enemies = [enemy for enemy in self.enemies if enemy["hp"] > 0]
        if self.wave_delay > 0:
            self.wave_delay = max(0, self.wave_delay - dt)
            if self.wave_delay == 0 and not self.enemies and not self.victory:
                self.spawn_next_wave()

        if not self.enemies and not self.victory:
            if self.wave_delay == 0:
                self.wave_delay = 0.6
                self.message = "Wave cleared"
                self.message_time = 0.6

        if player["hp"] <= 0:
            self.game_over = True
            self.message = "Igris falls. Press R to rise again."
            self.message_time = 999

    def update_player(self, dt):
        player = self.player
        dx = 0
        dy = 0
        if "a" in self.keys or "left" in self.keys:
            dx -= 1
        if "d" in self.keys or "right" in self.keys:
            dx += 1
        if "w" in self.keys or "up" in self.keys:
            dy -= 1
        if "s" in self.keys or "down" in self.keys:
            dy += 1

        if dx or dy:
            length = math.hypot(dx, dy)
            dx /= length
            dy /= length
            player["facing_x"] = dx
            player["facing_y"] = dy

        speed = player["speed"] * (2.95 if player["dash_time"] > 0 else 1)
        player["x"] = clamp(player["x"] + dx * speed * dt, player["r"], WIDTH - player["r"])
        player["y"] = clamp(player["y"] + dy * speed * dt, player["r"], HEIGHT - player["r"])

    def update_slashes(self, dt):
        for slash in self.slashes:
            slash["life"] -= dt
            for index, enemy in enumerate(self.enemies):
                if enemy["hp"] <= 0 or index in slash["hit"]:
                    continue
                ex = enemy["x"] - slash["x"]
                ey = enemy["y"] - slash["y"]
                dist = math.hypot(ex, ey)
                if dist > slash["radius"] + enemy["r"] or dist == 0:
                    continue
                dot = (ex / dist) * slash["dx"] + (ey / dist) * slash["dy"]
                if dot > 0.28:
                    damage = 36 if enemy["kind"] != "monarch" else 24
                    enemy["hp"] -= damage
                    enemy["flash"] = 0.12
                    slash["hit"].add(index)
                    self.score += 4
                    self.add_particles(enemy["x"], enemy["y"], "#ef476f", 8)
                    if enemy["hp"] <= 0:
                        self.defeat_enemy(enemy)
        self.slashes = [slash for slash in self.slashes if slash["life"] > 0]

    def update_shadows(self, dt):
        for shadow in self.shadows:
            shadow["life"] -= dt
            shadow["x"] += shadow["dx"] * 460 * dt
            shadow["y"] += shadow["dy"] * 460 * dt
            for index, enemy in enumerate(self.enemies):
                if enemy["hp"] <= 0 or index in shadow["hit"]:
                    continue
                if distance(shadow["x"], shadow["y"], enemy["x"], enemy["y"]) < enemy["r"] + 15:
                    enemy["hp"] -= shadow["damage"]
                    enemy["flash"] = 0.15
                    shadow["hit"].add(index)
                    self.add_particles(enemy["x"], enemy["y"], "#8ea0ff", 10)
                    if enemy["hp"] <= 0:
                        self.defeat_enemy(enemy)
        self.shadows = [
            shadow
            for shadow in self.shadows
            if shadow["life"] > 0 and -50 < shadow["x"] < WIDTH + 50 and -50 < shadow["y"] < HEIGHT + 50
        ]

    def update_enemies(self, dt):
        player = self.player
        for enemy in self.enemies:
            if enemy["hp"] <= 0:
                continue
            enemy["touch_cd"] = max(0, enemy["touch_cd"] - dt)
            enemy["shoot_cd"] = max(0, enemy["shoot_cd"] - dt)
            enemy["charge_cd"] = max(0, enemy["charge_cd"] - dt)
            enemy["flash"] = max(0, enemy["flash"] - dt)

            dx = player["x"] - enemy["x"]
            dy = player["y"] - enemy["y"]
            dist = max(1, math.hypot(dx, dy))
            nx = dx / dist
            ny = dy / dist

            preferred = 190 if enemy["kind"] == "archer" else 0
            if enemy["kind"] == "monarch":
                preferred = 150 if enemy["shoot_cd"] < 0.9 else 0

            if dist > preferred + 12:
                enemy["x"] += nx * enemy["speed"] * dt
                enemy["y"] += ny * enemy["speed"] * dt
            elif dist < preferred - 18:
                enemy["x"] -= nx * enemy["speed"] * 0.65 * dt
                enemy["y"] -= ny * enemy["speed"] * 0.65 * dt

            if enemy["kind"] in ("archer", "monarch") and enemy["shoot_cd"] <= 0:
                self.enemy_shoot(enemy, nx, ny)
                enemy["shoot_cd"] = 1.55 if enemy["kind"] == "archer" else 0.78

            if enemy["kind"] == "monarch" and enemy["charge_cd"] <= 0:
                enemy["x"] += nx * 76
                enemy["y"] += ny * 76
                enemy["charge_cd"] = 3.3
                self.add_particles(enemy["x"], enemy["y"], "#b80f3a", 20)

            if dist < enemy["r"] + player["r"] and enemy["touch_cd"] <= 0:
                self.hurt_player(enemy["damage"])
                enemy["touch_cd"] = 0.75
                shove = 20
                enemy["x"] -= nx * shove
                enemy["y"] -= ny * shove

    def enemy_shoot(self, enemy, nx, ny):
        spread = [-0.18, 0, 0.18] if enemy["kind"] == "monarch" else [0]
        for angle_offset in spread:
            angle = math.atan2(ny, nx) + angle_offset
            self.projectiles.append(
                {
                    "x": enemy["x"],
                    "y": enemy["y"],
                    "dx": math.cos(angle),
                    "dy": math.sin(angle),
                    "speed": 235 if enemy["kind"] == "archer" else 285,
                    "r": 5 if enemy["kind"] == "archer" else 7,
                    "damage": 10 if enemy["kind"] == "archer" else 14,
                    "life": 3.5,
                    "color": "#d9b44a" if enemy["kind"] == "archer" else "#d52d5e",
                }
            )

    def update_projectiles(self, dt):
        player = self.player
        for shot in self.projectiles:
            shot["life"] -= dt
            shot["x"] += shot["dx"] * shot["speed"] * dt
            shot["y"] += shot["dy"] * shot["speed"] * dt
            if distance(shot["x"], shot["y"], player["x"], player["y"]) < shot["r"] + player["r"]:
                shot["life"] = 0
                self.hurt_player(shot["damage"])
                self.add_particles(player["x"], player["y"], shot["color"], 7)
        self.projectiles = [
            shot
            for shot in self.projectiles
            if shot["life"] > 0 and -30 < shot["x"] < WIDTH + 30 and -30 < shot["y"] < HEIGHT + 30
        ]

    def update_particles(self, dt):
        for particle in self.particles:
            particle["life"] -= dt
            particle["x"] += particle["dx"] * dt
            particle["y"] += particle["dy"] * dt
            particle["dy"] += 45 * dt
        self.particles = [particle for particle in self.particles if particle["life"] > 0]

    def hurt_player(self, amount):
        if self.player["invuln"] > 0:
            return
        self.player["hp"] -= amount
        self.player["invuln"] = 0.28
        self.add_particles(self.player["x"], self.player["y"], "#ffffff", 8)

    def defeat_enemy(self, enemy):
        if enemy.get("dead"):
            return
        enemy["dead"] = True
        self.score += enemy.get("score", 0)
        self.kills += 1
        self.add_particles(enemy["x"], enemy["y"], "#f2c96d", 16)
        if enemy["kind"] == "monarch":
            self.victory = True
            self.message = "The throne is claimed. Press R to play again."
            self.message_time = 999

    def add_particles(self, x, y, color, count):
        for _ in range(count):
            angle = random.uniform(0, math.tau)
            speed = random.uniform(60, 190)
            self.particles.append(
                {
                    "x": x,
                    "y": y,
                    "dx": math.cos(angle) * speed,
                    "dy": math.sin(angle) * speed,
                    "life": random.uniform(0.25, 0.65),
                    "color": color,
                    "size": random.uniform(2, 5),
                }
            )

    def draw(self):
        canvas = self.canvas
        canvas.delete("all")
        self.draw_background(canvas)
        self.draw_projectiles(canvas)
        self.draw_shadows(canvas)
        self.draw_enemies(canvas)
        self.draw_slashes(canvas)
        self.draw_player(canvas)
        self.draw_particles(canvas)
        self.draw_hud(canvas)

        if self.paused:
            canvas.create_rectangle(0, 0, WIDTH, HEIGHT, fill="#000000", stipple="gray50", outline="")
            canvas.create_text(WIDTH / 2, HEIGHT / 2, text="PAUSED", fill="#f2c96d", font=("Consolas", 34, "bold"))

    def draw_background(self, canvas):
        canvas.create_rectangle(0, 0, WIDTH, HEIGHT, fill="#11131a", outline="")
        for x in range(0, WIDTH, 64):
            canvas.create_line(x, 0, x, HEIGHT, fill="#191c26")
        for y in range(0, HEIGHT, 64):
            canvas.create_line(0, y, WIDTH, y, fill="#191c26")
        canvas.create_oval(WIDTH / 2 - 138, HEIGHT / 2 - 138, WIDTH / 2 + 138, HEIGHT / 2 + 138, outline="#262b3a", width=3)
        canvas.create_oval(WIDTH / 2 - 42, HEIGHT / 2 - 42, WIDTH / 2 + 42, HEIGHT / 2 + 42, outline="#372432", width=2)

    def draw_player(self, canvas):
        p = self.player
        x = p["x"]
        y = p["y"]
        flash = p["invuln"] > 0 and int(time.perf_counter() * 18) % 2 == 0
        body = "#7f102c" if not flash else "#ffffff"
        trim = "#f2c96d"
        canvas.create_oval(x - p["r"], y - p["r"], x + p["r"], y + p["r"], fill=body, outline=trim, width=2)
        canvas.create_polygon(
            x - 10,
            y - 13,
            x + 10,
            y - 13,
            x + 5,
            y - 27,
            x,
            y - 18,
            x - 5,
            y - 27,
            fill=trim,
            outline="#2a1c0a",
        )
        sx = x + p["facing_x"] * 26
        sy = y + p["facing_y"] * 26
        canvas.create_line(x, y, sx, sy, fill="#e8edf2", width=4)
        canvas.create_oval(sx - 4, sy - 4, sx + 4, sy + 4, fill="#f2c96d", outline="")

    def draw_enemies(self, canvas):
        for enemy in self.enemies:
            if enemy["hp"] <= 0:
                continue
            x = enemy["x"]
            y = enemy["y"]
            r = enemy["r"]
            colors = {
                "pawn": ("#3d4b66", "#8ea0ff"),
                "archer": ("#315f4c", "#86efac"),
                "knight": ("#5b3340", "#f39a9a"),
                "monarch": ("#231826", "#d52d5e"),
            }
            fill, outline = colors[enemy["kind"]]
            if enemy["flash"] > 0:
                fill = "#ffffff"
            if enemy["kind"] == "monarch":
                canvas.create_oval(x - r - 10, y - r - 10, x + r + 10, y + r + 10, outline="#6d1938", width=4)
                canvas.create_polygon(x - 24, y - 24, x - 8, y - 50, x, y - 30, x + 8, y - 50, x + 24, y - 24, fill="#d52d5e", outline="")
            canvas.create_oval(x - r, y - r, x + r, y + r, fill=fill, outline=outline, width=2)
            if enemy["kind"] == "archer":
                canvas.create_line(x - 11, y - 10, x + 11, y + 10, fill="#d9b44a", width=3)
            if enemy["kind"] == "knight":
                canvas.create_rectangle(x - 5, y - 22, x + 5, y + 4, fill="#b9c0d4", outline="")
            self.draw_enemy_hp(canvas, enemy)

    def draw_enemy_hp(self, canvas, enemy):
        if enemy["hp"] >= enemy["max_hp"]:
            return
        x = enemy["x"]
        y = enemy["y"] - enemy["r"] - 12
        width = 44 if enemy["kind"] != "monarch" else 92
        pct = clamp(enemy["hp"] / enemy["max_hp"], 0, 1)
        canvas.create_rectangle(x - width / 2, y, x + width / 2, y + 5, fill="#2a2d38", outline="")
        canvas.create_rectangle(x - width / 2, y, x - width / 2 + width * pct, y + 5, fill="#ef476f", outline="")

    def draw_slashes(self, canvas):
        for slash in self.slashes:
            progress = 1 - slash["life"] / slash["max_life"]
            x = slash["x"] + slash["dx"] * 34
            y = slash["y"] + slash["dy"] * 34
            radius = slash["radius"] * (0.75 + progress * 0.25)
            angle = math.degrees(math.atan2(-slash["dy"], slash["dx"]))
            start = angle - 48
            canvas.create_arc(
                x - radius,
                y - radius,
                x + radius,
                y + radius,
                start=start,
                extent=96,
                style=tk.ARC,
                outline="#f2c96d",
                width=8,
            )

    def draw_projectiles(self, canvas):
        for shot in self.projectiles:
            x = shot["x"]
            y = shot["y"]
            r = shot["r"]
            canvas.create_oval(x - r, y - r, x + r, y + r, fill=shot["color"], outline="")

    def draw_shadows(self, canvas):
        for shadow in self.shadows:
            x = shadow["x"]
            y = shadow["y"]
            canvas.create_line(x - shadow["dx"] * 18, y - shadow["dy"] * 18, x + shadow["dx"] * 18, y + shadow["dy"] * 18, fill="#8ea0ff", width=6)
            canvas.create_oval(x - 7, y - 7, x + 7, y + 7, fill="#141a35", outline="#8ea0ff")

    def draw_particles(self, canvas):
        for particle in self.particles:
            x = particle["x"]
            y = particle["y"]
            s = particle["size"]
            canvas.create_oval(x - s, y - s, x + s, y + s, fill=particle["color"], outline="")

    def draw_hud(self, canvas):
        p = self.player
        canvas.create_rectangle(18, 18, 298, 96, fill="#161922", outline="#2e3446", width=2)
        canvas.create_text(32, 31, anchor="w", text="IGRIS", fill="#f2c96d", font=("Consolas", 18, "bold"))
        canvas.create_text(32, 58, anchor="w", text=f"Wave {min(self.wave, 6)}   Score {self.score}   Kills {self.kills}", fill="#dce2ef", font=("Consolas", 11))
        self.draw_bar(canvas, 32, 74, 238, 12, p["hp"] / p["max_hp"], "#ef476f")

        x = WIDTH - 276
        canvas.create_rectangle(x, 18, WIDTH - 18, 96, fill="#161922", outline="#2e3446", width=2)
        canvas.create_text(x + 14, 34, anchor="w", text="Space Strike", fill="#dce2ef", font=("Consolas", 11))
        canvas.create_text(x + 14, 56, anchor="w", text=f"Shift Dash {self.cooldown_text(p['dash_cd'])}", fill="#8ea0ff", font=("Consolas", 11))
        canvas.create_text(x + 14, 78, anchor="w", text=f"E Royal Call {self.cooldown_text(p['summon_cd'])}", fill="#f2c96d", font=("Consolas", 11))

        if self.message_time > 0:
            canvas.create_text(WIDTH / 2, 36, text=self.message, fill="#f2c96d", font=("Consolas", 18, "bold"))

        if self.game_over or self.victory:
            canvas.create_rectangle(0, 0, WIDTH, HEIGHT, fill="#000000", stipple="gray50", outline="")
            title = "VICTORY" if self.victory else "DEFEAT"
            color = "#f2c96d" if self.victory else "#ef476f"
            canvas.create_text(WIDTH / 2, HEIGHT / 2 - 36, text=title, fill=color, font=("Consolas", 42, "bold"))
            canvas.create_text(WIDTH / 2, HEIGHT / 2 + 12, text=self.message, fill="#ffffff", font=("Consolas", 16))
            canvas.create_text(WIDTH / 2, HEIGHT / 2 + 46, text=f"Final score: {self.score}", fill="#dce2ef", font=("Consolas", 14))

    def draw_bar(self, canvas, x, y, w, h, pct, color):
        pct = clamp(pct, 0, 1)
        canvas.create_rectangle(x, y, x + w, y + h, fill="#2a2d38", outline="")
        canvas.create_rectangle(x, y, x + w * pct, y + h, fill=color, outline="")
        canvas.create_rectangle(x, y, x + w, y + h, outline="#60687c")

    def cooldown_text(self, value):
        return "ready" if value <= 0 else f"{value:.1f}s"


def main():
    root = tk.Tk()
    root.resizable(False, False)
    IgrisGame(root)
    root.mainloop()


if __name__ == "__main__":
    main()
