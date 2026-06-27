import pygame, sys, random, json, os, math

# ── Constants ──────────────────────────────────────────────────────────────────
SCREEN_W, SCREEN_H = 700, 700
GRID_SIZE = 20
GRID_W    = (SCREEN_W - 140) // GRID_SIZE
GRID_H    = (SCREEN_H - 80)  // GRID_SIZE
PLAY_X    = 70
PLAY_Y    = 40

SCORES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "high_scores.json")
SPEEDS      = {"Slow": 200, "Normal": 130, "Fast": 70, "Blazing": 35}
SPEED_ORDER = ["Slow", "Normal", "Fast", "Blazing"]

# Palette
C_BG       = (10,  12,  25)
C_PANEL    = (18,  20,  40)
C_BORDER   = (40, 180, 100)
C_GRID     = (20,  24,  45)
C_TEXT     = (220, 255, 220)
C_ACCENT   = (60,  220, 120)
C_ACCENT2  = (255, 200,  50)
C_RED      = (255,  70,  70)
C_DIM      = (100, 120, 100)
C_FOOD_OUT = (255, 100,  80)
C_FOOD_IN  = (255, 220,  60)
C_SNAKE_H  = (50,  220,  80)
C_SNAKE_B  = (30,  160,  60)
C_SNAKE_T  = (20,  100,  40)
C_GOLD     = (255, 200,  30)
C_SILVER   = (190, 190, 210)
C_BRONZE   = (200, 130,  60)
C_ORANGE   = (255, 140,  20)

pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("Snake Game")
clock = pygame.time.Clock()

# ── Fonts ──────────────────────────────────────────────────────────────────────
def load_font(size, bold=False):
    for name in ["Segoe UI", "Arial", "DejaVu Sans", None]:
        try:
            return pygame.font.SysFont(name, size, bold=bold)
        except Exception:
            pass
    return pygame.font.Font(None, size)

F_TITLE = load_font(62, bold=True)
F_BIG   = load_font(36, bold=True)
F_MED   = load_font(26)
F_SMALL = load_font(20)
F_TINY  = load_font(16)

# ── Sounds ─────────────────────────────────────────────────────────────────────
def make_beep(freq=440, dur_ms=60, vol=0.4):
    sr = 22050
    n  = int(sr * dur_ms / 1000)
    buf = bytes([int(128 + 127 * math.sin(2 * math.pi * freq * i / sr)) for i in range(n)])
    snd = pygame.mixer.Sound(buffer=bytearray(buf))
    snd.set_volume(vol)
    return snd

SND_EAT   = make_beep(660,  60, 0.5)
SND_DIE   = make_beep(220, 300, 0.6)
SND_CLICK = make_beep(880,  30, 0.3)

# ── Score helpers ──────────────────────────────────────────────────────────────
def load_scores():
    if os.path.exists(SCORES_FILE):
        try:
            with open(SCORES_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return []

def save_scores(scores):
    with open(SCORES_FILE, "w") as f:
        json.dump(scores, f)

def add_score(new_score, scores):
    scores.append(new_score)
    scores.sort(reverse=True)
    return scores[:5]

# ── Draw helpers ───────────────────────────────────────────────────────────────
def draw_rounded_rect(surf, color, rect, radius=12, alpha=255):
    r = pygame.Rect(rect)
    if alpha < 255:
        s = pygame.Surface((r.w, r.h), pygame.SRCALPHA)
        pygame.draw.rect(s, (*color[:3], alpha), s.get_rect(), border_radius=radius)
        surf.blit(s, r.topleft)
    else:
        pygame.draw.rect(surf, color, r, border_radius=radius)

def draw_text_centered(surf, text, font, color, cx, cy, shadow=False):
    if shadow:
        sh = font.render(text, True, (0, 0, 0))
        surf.blit(sh, sh.get_rect(center=(cx+2, cy+2)))
    img = font.render(text, True, color)
    surf.blit(img, img.get_rect(center=(cx, cy)))

def draw_text_left(surf, text, font, color, x, cy):
    img = font.render(text, True, color)
    surf.blit(img, (x, cy - img.get_height()//2))
    return img.get_width()

# ── Icon drawing (all pygame shapes, no emoji font) ───────────────────────────
def icon_trophy(surf, cx, cy, sz=22, color=C_GOLD):
    s = sz
    # cup body
    body = [(-s//2,0),(s//2,0),(s//2-2,s//2),(s//4,s//2+2),(s//4,s*3//4),(-s//4,s*3//4),(-s//4,s//2+2),(-s//2+2,s//2)]
    pts  = [(cx+x, cy-s//2+y) for x,y in body]
    pygame.draw.polygon(surf, color, pts)
    pygame.draw.polygon(surf, (255,255,200), pts, 1)
    # handles
    pygame.draw.arc(surf, color, (cx-s//2-4, cy-s//2, 8, s//2), math.pi*0.2, math.pi*0.8, 3)
    pygame.draw.arc(surf, color, (cx+s//2-4, cy-s//2, 8, s//2), math.pi*0.2, math.pi*0.8, 3)
    # base
    pygame.draw.rect(surf, color, (cx-s//3, cy+s//4*3-2, s*2//3, 4), border_radius=2)
    pygame.draw.rect(surf, color, (cx-s//2+2, cy+s//4*3+2, s-4, 4), border_radius=2)

def icon_medal(surf, cx, cy, sz=18, rank=1):
    colors = {1: C_GOLD, 2: C_SILVER, 3: C_BRONZE}
    col    = colors.get(rank, C_DIM)
    # ribbon
    pygame.draw.line(surf, col, (cx-sz//3, cy-sz), (cx, cy-sz//4), 3)
    pygame.draw.line(surf, col, (cx+sz//3, cy-sz), (cx, cy-sz//4), 3)
    # circle
    pygame.draw.circle(surf, col,           (cx, cy), sz//2+1)
    pygame.draw.circle(surf, (255,255,255), (cx, cy), sz//2-2, 1)
    # rank number
    n = load_font(sz-4, bold=True).render(str(rank), True, (30,20,10))
    surf.blit(n, n.get_rect(center=(cx, cy)))

def icon_play(surf, cx, cy, sz=18, color=C_ACCENT):
    pts = [(cx-sz//3, cy-sz//2),(cx-sz//3, cy+sz//2),(cx+sz//2, cy)]
    pygame.draw.polygon(surf, color, pts)

def icon_sound(surf, cx, cy, sz=18, muted=False, color=C_ACCENT):
    # speaker box
    pts = [(cx-sz//2,cy-sz//4),(cx-sz//6,cy-sz//4),(cx+sz//6,cy-sz//2),
           (cx+sz//6,cy+sz//2),(cx-sz//6,cy+sz//4),(cx-sz//2,cy+sz//4)]
    pygame.draw.polygon(surf, color, pts)
    if not muted:
        pygame.draw.arc(surf, color, (cx+sz//6, cy-sz//3, sz//2, sz*2//3),
                        -math.pi*0.4, math.pi*0.4, 2)
        pygame.draw.arc(surf, color, (cx+sz//6-3, cy-sz//2, sz*2//3, sz),
                        -math.pi*0.4, math.pi*0.4, 2)
    else:
        x1,y1 = cx+sz//4, cy-sz//3
        x2,y2 = cx+sz*3//4, cy+sz//3
        pygame.draw.line(surf, C_RED, (x1,y1),(x2,y2), 3)
        pygame.draw.line(surf, C_RED, (x2,y1),(x1,y2), 3)

def icon_lightning(surf, cx, cy, sz=18, color=C_ACCENT2):
    pts = [(cx+sz//4,cy-sz//2),(cx-sz//6,cy),(cx+sz//4,cy),(cx-sz//4,cy+sz//2),(cx+sz//6,cy),(cx-sz//4,cy)]
    pygame.draw.polygon(surf, color, pts)

def icon_home(surf, cx, cy, sz=18, color=C_TEXT):
    # roof
    roof = [(cx-sz//2,cy),(cx,cy-sz//2),(cx+sz//2,cy)]
    pygame.draw.polygon(surf, color, roof)
    # walls
    pygame.draw.rect(surf, color, (cx-sz//3, cy, sz*2//3, sz//2))
    # door
    pygame.draw.rect(surf, C_BG, (cx-sz//7, cy+sz//6, sz*2//7, sz//2))

def icon_back(surf, cx, cy, sz=18, color=C_TEXT):
    # left arrow
    pts = [(cx+sz//2,cy-sz//2),(cx-sz//4,cy),(cx+sz//2,cy+sz//2)]
    pygame.draw.polygon(surf, color, pts)
    pygame.draw.rect(surf, color, (cx-sz//4, cy-sz//8, sz//2, sz//4), border_radius=2)

def icon_star(surf, cx, cy, sz=14, color=C_ACCENT2):
    pts = []
    for i in range(10):
        angle = math.pi/2 + i * math.pi/5
        r     = sz if i%2==0 else sz//2
        pts.append((cx + r*math.cos(angle), cy - r*math.sin(angle)))
    pygame.draw.polygon(surf, color, pts)

def icon_check(surf, cx, cy, sz=14, color=C_ACCENT):
    x1,y1 = cx-sz//2, cy
    x2,y2 = cx-sz//6, cy+sz//3
    x3,y3 = cx+sz//2, cy-sz//3
    pygame.draw.line(surf, color, (x1,y1),(x2,y2), 3)
    pygame.draw.line(surf, color, (x2,y2),(x3,y3), 3)

def icon_party(surf, cx, cy, sz=18, color=C_ACCENT2):
    # confetti dots
    colors = [C_ACCENT2, C_ACCENT, C_RED, (180,100,255), C_ORANGE]
    random.seed(42)
    for i in range(12):
        angle = i * math.pi * 2 / 12
        r     = random.randint(sz//3, sz*2//3)
        x     = int(cx + r * math.cos(angle))
        y     = int(cy + r * math.sin(angle))
        pygame.draw.circle(surf, colors[i%len(colors)], (x,y), 3)
    pygame.draw.circle(surf, C_GOLD, (cx, cy), sz//4)

def icon_turtle(surf, cx, cy, sz=18):
    pygame.draw.ellipse(surf, (50,160,60), (cx-sz//2,cy-sz//3,sz,sz*2//3))
    pygame.draw.circle(surf, (30,120,40), (cx+sz//2,cy), sz//4)
    for dx,dy in [(-sz//3,sz//3),(-sz//6,sz//2),(sz//6,sz//2),(sz//3,sz//3)]:
        pygame.draw.circle(surf, (40,140,50), (cx+dx,cy+dy), sz//6)

def icon_snake_head(surf, cx, cy, sz=18):
    pygame.draw.ellipse(surf, C_SNAKE_H, (cx-sz//2,cy-sz//3,sz,sz*2//3))
    pygame.draw.circle(surf, (255,255,255), (cx+sz//4,cy-sz//8), 4)
    pygame.draw.circle(surf, (10,10,10),   (cx+sz//4,cy-sz//8), 2)

def icon_cheetah(surf, cx, cy, sz=18):
    pygame.draw.ellipse(surf, C_ORANGE, (cx-sz//2,cy-sz//4,sz,sz//2))
    pygame.draw.circle(surf, C_ORANGE,  (cx+sz//2,cy), sz//4)
    for i,col in enumerate([(80,50,10),(80,50,10),(80,50,10)]):
        pygame.draw.circle(surf, col, (cx-sz//3+i*sz//4, cy-sz//5), 3)

def icon_fire(surf, cx, cy, sz=18):
    # orange flame
    pts_o = [(cx,cy-sz),(cx+sz//3,cy-sz//3),(cx+sz//2,cy),(cx,cy+sz//4),(cx-sz//2,cy),(cx-sz//3,cy-sz//3)]
    pygame.draw.polygon(surf, C_ORANGE, pts_o)
    # yellow core
    pts_y = [(cx,cy-sz//2),(cx+sz//5,cy-sz//6),(cx+sz//3,cy),(cx,cy+sz//5),(cx-sz//3,cy),(cx-sz//5,cy-sz//6)]
    pygame.draw.polygon(surf, C_ACCENT2, pts_y)

# Map speed labels to icon drawing functions
SPEED_ICONS = {
    "Slow":    icon_turtle,
    "Normal":  icon_snake_head,
    "Fast":    icon_cheetah,
    "Blazing": icon_fire,
}

# ── Button with optional icon ──────────────────────────────────────────────────
def draw_button(surf, text, font, rect, color_bg, color_text,
                hover=False, radius=10, icon_fn=None, icon_sz=18):
    r  = pygame.Rect(rect)
    bg = tuple(min(255, c+30) for c in color_bg) if hover else color_bg
    draw_rounded_rect(surf, bg, r, radius)
    pygame.draw.rect(surf, C_ACCENT if hover else C_BORDER, r, 2, border_radius=radius)

    t_surf = font.render(text, True, color_text)
    if icon_fn:
        gap     = 8
        total_w = icon_sz + gap + t_surf.get_width()
        ix      = r.centerx - total_w//2 + icon_sz//2
        tx      = r.centerx - total_w//2 + icon_sz + gap
        icon_fn(surf, ix, r.centery, icon_sz)
        surf.blit(t_surf, (tx, r.centery - t_surf.get_height()//2))
    else:
        surf.blit(t_surf, t_surf.get_rect(center=r.center))
    return r

# ── Snake / Food surfaces ──────────────────────────────────────────────────────
def make_segment_surface(size, hue_rgb, is_head=False, is_tail=False):
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    r = pygame.Rect(0, 0, size, size)
    pygame.draw.rect(s, hue_rgb, r, border_radius=6 if is_head or is_tail else 4)
    lighter = tuple(min(255, c+60) for c in hue_rgb)
    pygame.draw.rect(s, lighter, pygame.Rect(3, 3, size-6, size//2-2), border_radius=4)
    sc = tuple(max(0, c-40) for c in hue_rgb)
    for i in range(1, 3):
        y = size * i // 3
        pygame.draw.line(s, sc, (4, y), (size-4, y), 1)
    if is_head:
        ey = size // 3
        for ex in [size//3, 2*size//3]:
            pygame.draw.circle(s, (255,255,255), (ex,ey), 3)
            pygame.draw.circle(s, (10,10,10),    (ex,ey), 1)
    return s

SEG_HEAD = make_segment_surface(GRID_SIZE-2, C_SNAKE_H, is_head=True)
SEG_BODY = make_segment_surface(GRID_SIZE-2, C_SNAKE_B)
SEG_TAIL = make_segment_surface(GRID_SIZE-2, C_SNAKE_T, is_tail=True)

def make_food_surface(size):
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    cx, cy, r = size//2, size//2, size//2-2
    pygame.draw.circle(s, C_FOOD_OUT, (cx,cy), r)
    pygame.draw.circle(s, C_FOOD_IN,  (cx,cy), r-4)
    pygame.draw.circle(s, (255,255,255), (cx-r//3,cy-r//3), r//4)
    return s

FOOD_IMG = make_food_surface(GRID_SIZE)

# ── Game ───────────────────────────────────────────────────────────────────────
class SnakeGame:
    def __init__(self):
        self.high_scores = load_scores()
        self.muted       = False
        self.speed_label = "Normal"
        self.state       = "start"
        self.score       = 0
        self.snake       = []
        self.direction   = (1, 0)
        self.next_dir    = (1, 0)
        self.food        = (0, 0)
        self.move_timer  = 0
        self.anim_tick   = 0
        self.new_high    = False

    def start_game(self):
        cx, cy = GRID_W//2, GRID_H//2
        self.snake     = [(cx,cy),(cx-1,cy),(cx-2,cy)]
        self.direction = (1, 0)
        self.next_dir  = (1, 0)
        self.score     = 0
        self.new_high  = False
        self.spawn_food()
        self.state      = "playing"
        self.move_timer = 0

    def spawn_food(self):
        while True:
            pos = (random.randint(0,GRID_W-1), random.randint(0,GRID_H-1))
            if pos not in self.snake:
                self.food = pos; break

    def get_speed(self): return SPEEDS[self.speed_label]

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if self.state == "playing":
                if   event.key in (pygame.K_UP,    pygame.K_w) and self.direction != (0, 1):  self.next_dir = (0,-1)
                elif event.key in (pygame.K_DOWN,  pygame.K_s) and self.direction != (0,-1):  self.next_dir = (0, 1)
                elif event.key in (pygame.K_LEFT,  pygame.K_a) and self.direction != (1, 0):  self.next_dir = (-1,0)
                elif event.key in (pygame.K_RIGHT, pygame.K_d) and self.direction != (-1,0):  self.next_dir = (1, 0)
                elif event.key in (pygame.K_ESCAPE, pygame.K_p): self.state = "paused"
            elif self.state == "paused":
                if event.key in (pygame.K_ESCAPE, pygame.K_p): self.state = "playing"

    def update(self, dt):
        self.anim_tick += dt
        if self.state != "playing": return
        self.move_timer += dt
        if self.move_timer >= self.get_speed():
            self.move_timer = 0; self.move()

    def move(self):
        self.direction = self.next_dir
        hx, hy = self.snake[0]
        dx, dy = self.direction
        nh = (hx+dx, hy+dy)
        if not (0 <= nh[0] < GRID_W and 0 <= nh[1] < GRID_H): self.die(); return
        if nh in self.snake: self.die(); return
        self.snake.insert(0, nh)
        if nh == self.food:
            self.score += 10
            if not self.muted: SND_EAT.play()
            self.spawn_food()
        else:
            self.snake.pop()

    def die(self):
        if not self.muted: SND_DIE.play()
        best = self.high_scores[0] if self.high_scores else -1
        if self.score > best and self.score > 0: self.new_high = True
        self.high_scores = add_score(self.score, self.high_scores)
        save_scores(self.high_scores)
        self.state = "gameover"

    # ── Draw dispatcher ──────────────────────────────────────────────────────
    def draw(self):
        screen.fill(C_BG)
        if   self.state == "start":    self.draw_start()
        elif self.state == "scores":   self.draw_scores()
        elif self.state == "audio":    self.draw_audio()
        elif self.state == "speed":    self.draw_speed()
        elif self.state in ("playing","paused","gameover"):
            self.draw_game()
            if   self.state == "paused":   self.draw_pause_overlay()
            elif self.state == "gameover": self.draw_gameover_overlay()
        pygame.display.flip()

    # ── Start screen ─────────────────────────────────────────────────────────
    def draw_start(self):
        t = self.anim_tick / 1000
        for i in range(20):
            x = int(SCREEN_W*(0.1+0.8*((i*137+t*20)%100)/100))
            y = int(SCREEN_H*(0.1+0.8*((i*79 +t*15)%100)/100))
            r = int(3+3*math.sin(t+i))
            a = int(80+60*math.sin(t*0.7+i))
            circ = pygame.Surface((r*2,r*2), pygame.SRCALPHA)
            pygame.draw.circle(circ, (*C_ACCENT,a), (r,r), r)
            screen.blit(circ, (x-r,y-r))

        self._draw_logo_snake(SCREEN_W//2-54, 88)

        pulse = int(255*(0.8+0.2*math.sin(t*2)))
        draw_text_centered(screen, "SNAKE", F_TITLE, (C_ACCENT[0],pulse,C_ACCENT[2]), SCREEN_W//2, 200, shadow=True)
        draw_text_centered(screen, "GAME",  F_TITLE, (pulse,C_ACCENT2[1],50),         SCREEN_W//2, 262, shadow=True)
        draw_text_centered(screen, "Arrow Keys / WASD to move",F_SMALL,C_DIM,SCREEN_W//2,322)
        draw_text_centered(screen, "P or ESC to Pause",        F_SMALL,C_DIM,SCREEN_W//2,347)

        mx,my = pygame.mouse.get_pos()
        btn_play   = pygame.Rect(SCREEN_W//2-130, 392, 260, 56)
        btn_scores = pygame.Rect(SCREEN_W//2-130, 462, 260, 56)
        draw_button(screen, "START GAME",  F_BIG, btn_play,
                    (20,90,50), C_TEXT, btn_play.collidepoint(mx,my),
                    icon_fn=lambda s,cx,cy,sz: icon_play(s,cx,cy,sz,C_TEXT), icon_sz=20)
        draw_button(screen, "HIGH SCORES", F_MED, btn_scores,
                    (40,40,90), C_TEXT, btn_scores.collidepoint(mx,my),
                    icon_fn=lambda s,cx,cy,sz: icon_trophy(s,cx,cy,sz,C_GOLD), icon_sz=20)

        draw_text_centered(screen, f"Speed: {self.speed_label}   |   Sound: {'OFF' if self.muted else 'ON'}",
                           F_TINY, C_DIM, SCREEN_W//2, 542)

    def _draw_logo_snake(self, ox, oy):
        segs = [(0,0),(1,0),(2,0),(2,1),(2,2),(1,2),(0,2),(0,1)]
        sz   = 20
        for i,(gx,gy) in enumerate(segs):
            col = C_SNAKE_H if i==0 else (C_SNAKE_B if i<len(segs)-1 else C_SNAKE_T)
            r   = pygame.Rect(ox+gx*sz, oy+gy*sz, sz-2, sz-2)
            pygame.draw.rect(screen, col, r, border_radius=4)
            if i==0:
                pygame.draw.circle(screen,(255,255,255),(r.left+5,r.top+5),3)
                pygame.draw.circle(screen,(0,0,0),      (r.left+5,r.top+5),1)

    # ── Game screen ──────────────────────────────────────────────────────────
    def draw_game(self):
        draw_rounded_rect(screen, C_PANEL, (0,0,PLAY_X,SCREEN_H), 0)
        draw_rounded_rect(screen, C_PANEL, (PLAY_X+GRID_W*GRID_SIZE,0,PLAY_X,SCREEN_H), 0)
        draw_rounded_rect(screen, C_PANEL, (0,0,SCREEN_W,PLAY_Y), 0)

        draw_text_centered(screen,"SCORE",F_TINY,C_DIM,35,150)
        draw_text_centered(screen,str(self.score),F_BIG,C_ACCENT,35,175)
        hs = self.high_scores[0] if self.high_scores else 0
        draw_text_centered(screen,"BEST",F_TINY,C_DIM,35,215)
        draw_text_centered(screen,str(hs),F_MED,C_ACCENT2,35,238)
        draw_text_centered(screen,self.speed_label,F_TINY,C_DIM,35,280)
        icon_sound(screen, 35, 312, sz=16, muted=self.muted, color=C_ACCENT)

        draw_text_centered(screen,"SNAKE",F_MED,C_ACCENT,SCREEN_W//2,20)

        play_rect = pygame.Rect(PLAY_X,PLAY_Y,GRID_W*GRID_SIZE,GRID_H*GRID_SIZE)
        pygame.draw.rect(screen,(14,16,30),play_rect)
        for x in range(GRID_W+1):
            px=PLAY_X+x*GRID_SIZE
            pygame.draw.line(screen,C_GRID,(px,PLAY_Y),(px,PLAY_Y+GRID_H*GRID_SIZE))
        for y in range(GRID_H+1):
            py=PLAY_Y+y*GRID_SIZE
            pygame.draw.line(screen,C_GRID,(PLAY_X,py),(PLAY_X+GRID_W*GRID_SIZE,py))
        pygame.draw.rect(screen,C_BORDER,play_rect,3,border_radius=4)

        t  = self.anim_tick/1000
        fx,fy = self.food
        px = PLAY_X+fx*GRID_SIZE; py2 = PLAY_Y+fy*GRID_SIZE
        r  = int(GRID_SIZE//2-1+2*math.sin(t*4))
        ps = pygame.Surface((r*2,r*2),pygame.SRCALPHA)
        pygame.draw.circle(ps,(*C_FOOD_OUT,80),(r,r),r)
        screen.blit(ps,(px+GRID_SIZE//2-r,py2+GRID_SIZE//2-r))
        screen.blit(FOOD_IMG,(px,py2))

        for i,(sx,sy) in enumerate(self.snake):
            px2=PLAY_X+sx*GRID_SIZE+1; py3=PLAY_Y+sy*GRID_SIZE+1
            img=SEG_HEAD if i==0 else (SEG_TAIL if i==len(self.snake)-1 else SEG_BODY)
            screen.blit(img,(px2,py3))

    # ── Pause overlay ─────────────────────────────────────────────────────────
    def draw_pause_overlay(self):
        ov = pygame.Surface((SCREEN_W,SCREEN_H),pygame.SRCALPHA)
        ov.fill((5,5,15,200)); screen.blit(ov,(0,0))

        panel = pygame.Rect(SCREEN_W//2-185,148,370,388)
        draw_rounded_rect(screen,C_PANEL,panel,18)
        pygame.draw.rect(screen,C_ACCENT,panel,2,border_radius=18)
        draw_text_centered(screen,"PAUSED",F_BIG,C_ACCENT2,SCREEN_W//2,195,shadow=True)

        mx,my = pygame.mouse.get_pos()
        btns = [
            (lambda s,cx,cy,sz: icon_play(s,cx,cy,sz,C_TEXT),    "Resume",          "resume", pygame.Rect(SCREEN_W//2-120,230,240,50)),
            (lambda s,cx,cy,sz: icon_sound(s,cx,cy,sz,False,C_TEXT),"Audio Settings","audio",  pygame.Rect(SCREEN_W//2-120,294,240,50)),
            (lambda s,cx,cy,sz: icon_lightning(s,cx,cy,sz,C_ACCENT2),"Speed Settings","speed", pygame.Rect(SCREEN_W//2-120,358,240,50)),
            (lambda s,cx,cy,sz: icon_home(s,cx,cy,sz,C_TEXT),    "Main Menu",       "menu",   pygame.Rect(SCREEN_W//2-120,422,240,50)),
        ]
        rects=[]
        for icon_fn,label,action,rect in btns:
            draw_button(screen,label,F_SMALL,rect,(25,30,55),C_TEXT,
                        rect.collidepoint(mx,my),icon_fn=icon_fn,icon_sz=18)
            rects.append((rect,action))
        return rects

    # ── Game Over overlay ─────────────────────────────────────────────────────
    def draw_gameover_overlay(self):
        ov=pygame.Surface((SCREEN_W,SCREEN_H),pygame.SRCALPHA)
        ov.fill((5,5,15,210)); screen.blit(ov,(0,0))

        panel=pygame.Rect(SCREEN_W//2-195,138,390,440)
        draw_rounded_rect(screen,C_PANEL,panel,18)
        pygame.draw.rect(screen,C_RED,panel,2,border_radius=18)

        draw_text_centered(screen,"GAME OVER",F_BIG,C_RED,SCREEN_W//2,185,shadow=True)
        draw_text_centered(screen,f"Score: {self.score}",F_MED,C_ACCENT,SCREEN_W//2,232)

        if self.new_high and self.score>0:
            icon_star(screen, SCREEN_W//2-105, 270, sz=12, color=C_ACCENT2)
            draw_text_centered(screen,"NEW HIGH SCORE!",F_MED,C_ACCENT2,SCREEN_W//2,270)
            icon_star(screen, SCREEN_W//2+105, 270, sz=12, color=C_ACCENT2)

        hs=self.high_scores[0] if self.high_scores else 0
        draw_text_centered(screen,f"Best: {hs}",F_SMALL,C_DIM,SCREEN_W//2,304)
        draw_text_centered(screen,"Top 5",F_SMALL,C_DIM,SCREEN_W//2,328)

        for i,s in enumerate(self.high_scores[:5]):
            y   = 352+i*22
            col = [C_GOLD,C_SILVER,C_BRONZE,C_TEXT,C_TEXT][i]
            if i<3:
                icon_medal(screen,SCREEN_W//2-68,y,sz=14,rank=i+1)
                draw_text_centered(screen,f"{s} pts",F_TINY,col,SCREEN_W//2+20,y)
            else:
                draw_text_centered(screen,f"{'4th' if i==3 else '5th'}  {s} pts",F_TINY,col,SCREEN_W//2,y)

        mx,my=pygame.mouse.get_pos()
        btn_play=pygame.Rect(SCREEN_W//2-115,468,230,50)
        btn_menu=pygame.Rect(SCREEN_W//2-115,526,230,44)
        draw_button(screen,"Play Again",F_MED,btn_play,(20,90,50),C_TEXT,
                    btn_play.collidepoint(mx,my),
                    icon_fn=lambda s,cx,cy,sz:icon_play(s,cx,cy,sz,C_TEXT),icon_sz=18)
        draw_button(screen,"Main Menu",F_SMALL,btn_menu,(35,35,70),C_TEXT,
                    btn_menu.collidepoint(mx,my),
                    icon_fn=lambda s,cx,cy,sz:icon_home(s,cx,cy,sz,C_TEXT),icon_sz=18)
        return btn_play,btn_menu

    # ── High Scores screen ────────────────────────────────────────────────────
    def draw_scores(self):
        icon_trophy(screen,SCREEN_W//2-118,88,sz=32,color=C_GOLD)
        draw_text_centered(screen,"HIGH SCORES",F_TITLE,C_ACCENT2,SCREEN_W//2+28,88,shadow=True)

        panel=pygame.Rect(SCREEN_W//2-210,138,420,380)
        draw_rounded_rect(screen,C_PANEL,panel,16)
        pygame.draw.rect(screen,C_ACCENT2,panel,2,border_radius=16)

        if self.high_scores:
            for i,s in enumerate(self.high_scores[:5]):
                y   = 190+i*62
                col = [C_GOLD,C_SILVER,C_BRONZE,C_TEXT,C_TEXT][i]
                if i<3:
                    icon_medal(screen,SCREEN_W//2-90,y,sz=22,rank=i+1)
                    draw_text_centered(screen,f"{s}  pts",F_BIG,col,SCREEN_W//2+20,y)
                else:
                    draw_text_centered(screen,f"{'4th' if i==3 else '5th'}   {s}  pts",F_BIG,col,SCREEN_W//2,y)
        else:
            draw_text_centered(screen,"No scores yet!",F_MED,C_DIM,SCREEN_W//2,330)

        mx,my=pygame.mouse.get_pos()
        btn=pygame.Rect(SCREEN_W//2-115,546,230,50)
        draw_button(screen,"Back",F_MED,btn,(35,35,70),C_TEXT,
                    btn.collidepoint(mx,my),
                    icon_fn=lambda s,cx,cy,sz:icon_back(s,cx,cy,sz,C_TEXT),icon_sz=18)
        return btn

    # ── Audio settings ────────────────────────────────────────────────────────
    def draw_audio(self):
        panel=pygame.Rect(SCREEN_W//2-210,178,420,320)
        draw_rounded_rect(screen,C_PANEL,panel,18)
        pygame.draw.rect(screen,C_ACCENT,panel,2,border_radius=18)

        icon_sound(screen,SCREEN_W//2-108,224,sz=26,muted=self.muted,color=C_ACCENT)
        draw_text_centered(screen,"Audio Settings",F_BIG,C_ACCENT,SCREEN_W//2+22,224,shadow=True)

        mx,my=pygame.mouse.get_pos()
        state_lbl = "Sound  ON" if not self.muted else "Sound  OFF"
        state_col = C_ACCENT   if not self.muted else C_RED
        bg_col    = (25,50,25) if not self.muted else (50,20,20)

        btn_toggle=pygame.Rect(SCREEN_W//2-120,278,240,58)
        draw_button(screen,state_lbl,F_MED,btn_toggle,bg_col,state_col,
                    btn_toggle.collidepoint(mx,my),
                    icon_fn=lambda s,cx,cy,sz,m=self.muted:icon_sound(s,cx,cy,sz,m,state_col),
                    icon_sz=20)
        draw_text_centered(screen,"Toggle game sound effects",F_TINY,C_DIM,SCREEN_W//2,354)

        btn_back=pygame.Rect(SCREEN_W//2-115,394,230,50)
        draw_button(screen,"Back",F_MED,btn_back,(35,35,70),C_TEXT,
                    btn_back.collidepoint(mx,my),
                    icon_fn=lambda s,cx,cy,sz:icon_back(s,cx,cy,sz,C_TEXT),icon_sz=18)
        return btn_toggle,btn_back

    # ── Speed settings ────────────────────────────────────────────────────────
    def draw_speed(self):
        panel=pygame.Rect(SCREEN_W//2-225,148,450,390)
        draw_rounded_rect(screen,C_PANEL,panel,18)
        pygame.draw.rect(screen,C_ACCENT,panel,2,border_radius=18)

        icon_lightning(screen,SCREEN_W//2-108,196,sz=28,color=C_ACCENT)
        draw_text_centered(screen,"Speed Settings",F_BIG,C_ACCENT,SCREEN_W//2+20,196,shadow=True)

        descs={"Slow":"Great for beginners","Normal":"Classic feel",
               "Fast":"Challenge mode","Blazing":"Expert only!"}
        mx,my=pygame.mouse.get_pos()
        btns=[]
        for i,label in enumerate(SPEED_ORDER):
            y        = 243+i*66
            rect     = pygame.Rect(SCREEN_W//2-155,y,310,52)
            selected = label==self.speed_label
            bg       = (20,80,40) if selected else (25,30,55)
            col      = C_ACCENT2 if selected else C_TEXT
            prefix   = "  OK  " if selected else "        "
            icon_fn  = SPEED_ICONS[label]
            draw_button(screen,prefix+label,F_MED,rect,bg,col,
                        rect.collidepoint(mx,my) and not selected,
                        icon_fn=icon_fn,icon_sz=18)
            if selected:
                draw_text_centered(screen,descs[label],F_TINY,C_DIM,SCREEN_W//2,y+55)
            btns.append((rect,label))

        btn_back=pygame.Rect(SCREEN_W//2-115,500,230,50)
        draw_button(screen,"Back",F_MED,btn_back,(35,35,70),C_TEXT,
                    btn_back.collidepoint(mx,my),
                    icon_fn=lambda s,cx,cy,sz:icon_back(s,cx,cy,sz,C_TEXT),icon_sz=18)
        return btns,btn_back

# ── Main loop ──────────────────────────────────────────────────────────────────
def main():
    game = SnakeGame()
    while True:
        dt = clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save_scores(game.high_scores); pygame.quit(); sys.exit()
            game.handle_input(event)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = pygame.mouse.get_pos()
                if game.state == "start":
                    if pygame.Rect(SCREEN_W//2-130,392,260,56).collidepoint(pos):
                        if not game.muted: SND_CLICK.play(); game.start_game()
                    elif pygame.Rect(SCREEN_W//2-130,462,260,56).collidepoint(pos):
                        if not game.muted: SND_CLICK.play(); game.state="scores"
                elif game.state == "scores":
                    if pygame.Rect(SCREEN_W//2-115,546,230,50).collidepoint(pos):
                        if not game.muted: SND_CLICK.play(); game.state="start"
                elif game.state == "paused":
                    mapping={"resume":(SCREEN_W//2-120,230,240,50),"audio":(SCREEN_W//2-120,294,240,50),
                             "speed": (SCREEN_W//2-120,358,240,50),"menu": (SCREEN_W//2-120,422,240,50)}
                    for action,(x,y,w,h) in mapping.items():
                        if pygame.Rect(x,y,w,h).collidepoint(pos):
                            if not game.muted: SND_CLICK.play()
                            if   action=="resume": game.state="playing"
                            elif action=="audio":  game.state="audio"
                            elif action=="speed":  game.state="speed"
                            elif action=="menu":   game.state="start"
                elif game.state == "gameover":
                    if pygame.Rect(SCREEN_W//2-115,468,230,50).collidepoint(pos):
                        if not game.muted: SND_CLICK.play(); game.start_game()
                    elif pygame.Rect(SCREEN_W//2-115,526,230,44).collidepoint(pos):
                        if not game.muted: SND_CLICK.play(); game.state="start"
                elif game.state == "audio":
                    if pygame.Rect(SCREEN_W//2-120,278,240,58).collidepoint(pos):
                        game.muted=not game.muted
                        if not game.muted: SND_CLICK.play()
                    elif pygame.Rect(SCREEN_W//2-115,394,230,50).collidepoint(pos):
                        if not game.muted: SND_CLICK.play(); game.state="paused"
                elif game.state == "speed":
                    if pygame.Rect(SCREEN_W//2-115,500,230,50).collidepoint(pos):
                        if not game.muted: SND_CLICK.play(); game.state="paused"
                    for i,label in enumerate(SPEED_ORDER):
                        if pygame.Rect(SCREEN_W//2-155,243+i*66,310,52).collidepoint(pos):
                            game.speed_label=label
                            if not game.muted: SND_CLICK.play()
        game.update(dt)
        game.draw()

if __name__ == "__main__":
    main()
