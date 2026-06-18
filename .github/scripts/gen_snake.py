import random, math

W, H = 800, 200
SZ = 16
COLS = W // SZ
ROWS = H // SZ
SNAKE_INIT = 10
STAR_COUNT = 8
TOTAL_EATS = 30
STEP_DUR = 0.12

GREEN = ['#4CAF50','#3d9e42','#2e7d32','#1b5e20','#144d19']
STAR_COLORS = ['#FFD700','#8B5CF6','#58A6FF','#F97316','#ff6eb4','#00e5ff']

random.seed(42)

# ── simulation ───────────────────────────────────────────────────────────────
def find_dir(head, direction, snake_set, star_positions):
    dx, dy = direction
    best, best_dist = None, 1e9
    for d in [(1,0),(-1,0),(0,1),(0,-1)]:
        if d[0]==-dx and d[1]==-dy: continue
        nx=(head[0]+d[0])%COLS; ny=(head[1]+d[1])%ROWS
        if (nx,ny) in snake_set: continue
        md = min((abs(nx-s[0])+abs(ny-s[1]) for s in star_positions), default=0)
        if md < best_dist: best_dist=md; best=d
    return best or direction

def spawn_star(snake_set, existing_pos):
    for _ in range(300):
        p=(random.randint(0,COLS-1), random.randint(0,ROWS-1))
        if p not in snake_set and p not in existing_pos:
            return p, random.choice(STAR_COLORS)
    return None, None

snake = [(COLS//2-i, ROWS//2) for i in range(SNAKE_INIT)]
direction = (1,0)
stars = {}
for _ in range(STAR_COUNT):
    p, c = spawn_star(set(snake), set(stars))
    if p: stars[p] = c

frames = []
eat_events = []
step = 0

while len(eat_events) < TOTAL_EATS:
    snake_set = set(snake)
    direction = find_dir(snake[0], direction, snake_set, list(stars.keys()))
    nx=(snake[0][0]+direction[0])%COLS; ny=(snake[0][1]+direction[1])%ROWS
    snake.insert(0,(nx,ny))

    eat_pos = eat_color = None
    if (nx,ny) in stars:
        eat_color = stars.pop((nx,ny))
        eat_pos = (nx,ny)
        eat_events.append((step, eat_pos, eat_color))
        p, c = spawn_star(set(snake), set(stars))
        if p: stars[p] = c
    else:
        snake.pop()

    frames.append((list(snake), dict(stars), eat_pos, eat_color))
    step += 1

TOTAL_STEPS = len(frames)
TOTAL_TIME = round(TOTAL_STEPS * STEP_DUR, 2)

def kt(i):
    if TOTAL_STEPS <= 1: return "0%"
    return f"{round(i/(TOTAL_STEPS-1)*100,4)}%"

# ── star lifetime tracking ───────────────────────────────────────────────────
star_spans = []
tracked = {}
for fi, (_, stars_f, _, _) in enumerate(frames):
    for pos in set(stars_f) - set(tracked):
        tracked[pos] = (fi, stars_f[pos])
    for pos in set(tracked) - set(stars_f):
        a, c = tracked.pop(pos)
        star_spans.append((pos, c, a, fi))
for pos, (a, c) in tracked.items():
    star_spans.append((pos, c, a, TOTAL_STEPS))

# ── SVG ──────────────────────────────────────────────────────────────────────
out = []
out.append(f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">')
out.append(f'<rect width="{W}" height="{H}" fill="#0d1117" rx="8"/>')
# grid
out.append(f'<defs><pattern id="gr" width="{SZ}" height="{SZ}" patternUnits="userSpaceOnUse">'
           f'<path d="M{SZ} 0L0 0 0 {SZ}" fill="none" stroke="#ffffff" stroke-width="0.3"/>'
           f'</pattern></defs>')
out.append(f'<rect width="{W}" height="{H}" fill="url(#gr)" opacity="0.06" rx="8"/>')

KT = ";".join(kt(i) for i in range(TOTAL_STEPS))

# ── snake: each segment uses x/y animate, visibility via display ─────────────
MAX_SEG = SNAKE_INIT + TOTAL_EATS
for seg_idx in range(MAX_SEG):
    color = GREEN[min(seg_idx, len(GREEN)-1)]
    xs, ys, vis = [], [], []
    last_x, last_y = 0, 0
    for fi, (snake_f, _, _, _) in enumerate(frames):
        if seg_idx < len(snake_f):
            sx, sy = snake_f[seg_idx]
            last_x, last_y = sx*SZ+1, sy*SZ+1
            xs.append(last_x); ys.append(last_y); vis.append("inline")
        else:
            xs.append(last_x); ys.append(last_y); vis.append("none")

    out.append(
        f'<rect width="{SZ-2}" height="{SZ-2}" fill="{color}" rx="2" x="{xs[0]}" y="{ys[0]}">'
        f'<animate attributeName="x" values="{";".join(map(str,xs))}" keyTimes="{KT}" dur="{TOTAL_TIME}s" repeatCount="indefinite" calcMode="discrete"/>'
        f'<animate attributeName="y" values="{";".join(map(str,ys))}" keyTimes="{KT}" dur="{TOTAL_TIME}s" repeatCount="indefinite" calcMode="discrete"/>'
        f'<animate attributeName="display" values="{";".join(vis)}" keyTimes="{KT}" dur="{TOTAL_TIME}s" repeatCount="indefinite" calcMode="discrete"/>'
        f'</rect>'
    )

# ── stars: 每颗星用独立 rect + text，visibility 用 display，闪烁用独立 opacity ──
for pos, color, a, d in star_spans:
    x, y = pos[0]*SZ+2, pos[1]*SZ+2
    # display keyframes: only show during [a, d)
    disp = ["inline" if a <= fi < d else "none" for fi in range(TOTAL_STEPS)]
    KD = ";".join(disp)
    twinkle_dur = round(1.1 + random.random()*0.9, 2)
    # rect
    out.append(
        f'<rect x="{x}" y="{y}" width="{SZ-5}" height="{SZ-5}" fill="{color}" rx="2" display="none">'
        f'<animate attributeName="display" values="{KD}" keyTimes="{KT}" dur="{TOTAL_TIME}s" repeatCount="indefinite" calcMode="discrete"/>'
        f'<animate attributeName="opacity" values="1;0.3;1" dur="{twinkle_dur}s" repeatCount="indefinite"/>'
        f'</rect>'
    )
    # star glyph
    out.append(
        f'<text x="{x-1}" y="{y+SZ-5}" font-size="12" font-family="monospace" fill="{color}" display="none">'
        f'<animate attributeName="display" values="{KD}" keyTimes="{KT}" dur="{TOTAL_TIME}s" repeatCount="indefinite" calcMode="discrete"/>'
        f'<animate attributeName="opacity" values="0.9;0.2;0.9" dur="{twinkle_dur}s" repeatCount="indefinite"/>'
        f'★</text>'
    )

# ── eat bursts ────────────────────────────────────────────────────────────────
for eat_step, eat_pos, eat_color in eat_events:
    ex, ey = eat_pos[0]*SZ+SZ//2, eat_pos[1]*SZ+SZ//2
    ts = round(eat_step * STEP_DUR, 3)
    dur = 0.4
    for i in range(8):
        angle = i * math.pi / 4
        ex2 = round(ex + math.cos(angle)*24, 1)
        ey2 = round(ey + math.sin(angle)*24, 1)
        out.append(
            f'<circle r="2.5" fill="{eat_color}" cx="{ex}" cy="{ey}" opacity="0">'
            f'<animate attributeName="cx" values="{ex};{ex2}" begin="{ts}s" dur="{dur}s" fill="remove" calcMode="linear"/>'
            f'<animate attributeName="cy" values="{ey};{ey2}" begin="{ts}s" dur="{dur}s" fill="remove" calcMode="linear"/>'
            f'<animate attributeName="opacity" values="0;1;1;0" keyTimes="0;0.05;0.5;1" begin="{ts}s" dur="{dur}s" fill="remove"/>'
            f'</circle>'
        )

# ── HUD ──────────────────────────────────────────────────────────────────────
out.append(f'<text x="8" y="{H-6}" font-size="10" font-family="monospace" fill="#4CAF50" opacity="0.55">♥♥♥  PIXEL SNAKE</text>')
out.append(f'<text x="{W-78}" y="{H-6}" font-size="10" font-family="monospace" fill="#4CAF50" opacity="0.55">XyLuoDYS</text>')
out.append('</svg>')

svg = "\n".join(out)
with open('dist/pixel-snake.svg','w') as f:
    f.write(svg)
print(f"Done! steps={TOTAL_STEPS} time={TOTAL_TIME}s size={len(svg)//1024}KB")
