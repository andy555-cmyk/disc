#!/usr/bin/env python3
"""행동유형 진단 — 유형별 정적 페이지 41개 + 유형 목록 + sitemap.xml + robots.txt 생성.

자료 출처는 index.html 안의 `const TYPES={...}` 하나뿐이다(두 벌 정본 금지).
실행:  python3 tools/build_types.py          (저장소 루트 어디서 돌려도 된다)
결과:  t/<코드>/index.html × 41, t/index.html, sitemap.xml, robots.txt
멱등:  같은 입력이면 바이트 단위로 같은 출력. 날짜·시각을 넣지 않는다.

코드 체계 = index.html의 유형 키에서 '/'만 뺀 것.  D/I/S → t/DIS/ , BAL → t/BAL/
공유 주소 = t/<코드>/?t=<결과코드>   예) t/DI/?t=DI-6622  (index.html의 shareURL()과 맞춘다)
"""
import json
import os
import re
import sys
from html import escape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "index.html")

# ── 설정 ─────────────────────────────────────────────────────────
BASE = "https://andy555-cmyk.github.io/disc/"   # 자체 도메인 연결 뒤 이 한 줄만 바꾼다
NOINDEX = True                                    # index.html과 같은 정책. 도메인 연결 뒤 False
OG_IMAGE = BASE + "og.png"                        # 유형별 이미지는 2단계. 지금은 공통 OG 재사용
SITE = "HayDay"

F = ["D", "I", "S", "C"]
FNAME = {"D": "주도", "I": "사교", "S": "안정", "C": "신중"}
FLONG = {"D": "주도 Dominance", "I": "사교 Influence", "S": "안정 Steadiness", "C": "신중 Conscientiousness"}
FCOL = {"D": "#9F2F2D", "I": "#956400", "S": "#346538", "C": "#1F6C9F"}
FBG = {"D": "#FDEBEC", "I": "#FBF3DB", "S": "#EDF3EC", "C": "#E1F3FE"}
FDESC = {
    "D": "문제와 속도. 결정을 빨리 내리고 결과로 판단합니다. 높을수록 주도하고 부딪히는 쪽, 낮을수록 신중하고 합의를 기다리는 쪽입니다.",
    "I": "사람과 표현. 관계로 일을 풉니다. 높을수록 말하고 설득하고 분위기를 만드는 쪽, 낮을수록 조용하고 사실 위주로 가는 쪽입니다.",
    "S": "속도와 지속. 흔들리지 않는 것을 중시합니다. 높을수록 꾸준하고 협조적인 쪽, 낮을수록 변화를 반기고 급하게 움직이는 쪽입니다.",
    "C": "기준과 정확도. 근거가 있어야 움직입니다. 높을수록 확인하고 따지는 쪽, 낮을수록 큰 그림 위주로 빠르게 가는 쪽입니다.",
}
GROUP = {"D": "주도 계열", "I": "사교 계열", "S": "안정 계열", "C": "신중 계열", "BAL": "균형"}

FAVICON = ("data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAzMiAzMiI+"
           "PHJlY3Qgd2lkdGg9IjMyIiBoZWlnaHQ9IjMyIiByeD0iNyIgZmlsbD0iI0Y3RjZGMyIvPjxyZWN0IHg9IjYiICB5PSI5IiAgd2lkdGg9IjQi"
           "IGhlaWdodD0iMTYiIHJ4PSIxIiBmaWxsPSIjOUYyRjJEIi8+PHJlY3QgeD0iMTIiIHk9IjEzIiB3aWR0aD0iNCIgaGVpZ2h0PSIxMiIgcng9"
           "IjEiIGZpbGw9IiM5NTY0MDAiLz48cmVjdCB4PSIxOCIgeT0iNyIgIHdpZHRoPSI0IiBoZWlnaHQ9IjE4IiByeD0iMSIgZmlsbD0iIzM0NjUz"
           "OCIvPjxyZWN0IHg9IjI0IiB5PSIxMiIgd2lkdGg9IjQiIGhlaWdodD0iMTMiIHJ4PSIxIiBmaWxsPSIjMUY2QzlGIi8+PC9zdmc+")

# 방문 집계 — Cloudflare Web Analytics (쿠키 없음). 대표가 토큰을 발급하면 index.html·privacy.html과 같이 주석을 풀고 토큰을 넣는다.
ANALYTICS = """<!-- 방문 집계 · Cloudflare Web Analytics (쿠키·개인식별자 없음). 토큰 발급 뒤 아래 주석을 풀고 CF_TOKEN_HERE를 바꾼다.
<script defer type="module" src="https://static.cloudflareinsights.com/beacon.min.js" data-cf-beacon='{"token": "CF_TOKEN_HERE"}'></script>
-->"""

CSS = """
:root{--canvas:#F7F6F3;--paper:#FFFFFF;--ink:#111111;--ink2:#2F3437;--sub:#787774;--line:#EAEAEA;--line2:#DEDCD7;
--D:#9F2F2D;--I:#956400;--S:#346538;--C:#1F6C9F;--Dbg:#FDEBEC;--Ibg:#FBF3DB;--Sbg:#EDF3EC;--Cbg:#E1F3FE}
*{box-sizing:border-box;margin:0;padding:0;-webkit-tap-highlight-color:transparent;word-break:keep-all}
html{scroll-behavior:smooth}
body{background:var(--canvas);color:var(--ink);padding:0 20px 90px;font-family:Pretendard,-apple-system,BlinkMacSystemFont,system-ui,sans-serif;-webkit-font-smoothing:antialiased;font-feature-settings:"tnum"}
.wrap{max-width:700px;margin:0 auto}
.mono{font-variant-numeric:tabular-nums;font-family:"SFMono-Regular",ui-monospace,Menlo,monospace}
.eyebrow{font-size:11px;letter-spacing:.2em;color:var(--sub);font-weight:700;display:block;text-align:center}
h1{font-size:46px;line-height:1.08;letter-spacing:-.045em;font-weight:800;margin:16px 0 0}
h2{font-size:23px;line-height:1.25;letter-spacing:-.03em;font-weight:700}
h3{font-size:15px;letter-spacing:-.02em;font-weight:700}
p{line-height:1.68;color:var(--ink2)}
b{font-weight:700;color:var(--ink)}
a{color:inherit}
.top{display:flex;justify-content:space-between;align-items:center;padding:18px 0 0;font-size:12.5px;color:var(--sub)}
.top a{text-decoration:none;font-weight:700}
.top a:hover{color:var(--ink)}
.rband{position:relative;margin:26px 0 22px;border-radius:12px;overflow:hidden;aspect-ratio:1600/686;border:1px solid var(--line);background:#EFEDE8}
.rband img{width:100%;height:100%;object-fit:cover;display:block}
.rbandtag{position:absolute;left:16px;bottom:14px;background:rgba(255,255,255,.92);border:1px solid var(--line);border-radius:999px;padding:6px 12px;font-size:12px;font-weight:800;letter-spacing:-.01em}
.rhead{text-align:center}
.badge{display:inline-flex;align-items:center;gap:9px;background:var(--paper);border:1px solid var(--line);border-radius:999px;padding:7px 14px;font-size:12.5px;font-weight:700;color:var(--ink2)}
.dots{display:flex;gap:3px}.dots i{width:7px;height:7px;border-radius:50%}
.rline{font-size:18px;line-height:1.55;color:var(--ink2);margin:14px auto 0;max-width:30em;font-weight:600}
.rbody p{font-size:15.5px;margin-top:16px}
.sect{margin-top:52px}.sect>.eyebrow{margin-bottom:15px}
.card{background:var(--paper);border:1px solid var(--line);border-radius:12px;padding:26px 24px;margin-top:14px}
.two{display:grid;grid-template-columns:1fr 1fr;gap:14px}
@media(max-width:640px){.two{grid-template-columns:1fr}}
.pts{list-style:none}.pts li{position:relative;padding:9px 0 9px 18px;font-size:14.5px;line-height:1.6;color:var(--ink2);border-bottom:1px solid var(--line)}
.pts li:last-child{border-bottom:0}.pts li::before{content:"";position:absolute;left:0;top:17px;width:7px;height:7px;border-radius:50%;background:var(--ink)}
dl{display:block}.kv{display:flex;gap:14px;padding:15px 0;border-bottom:1px solid var(--line);align-items:flex-start}
.kv:last-child{border-bottom:0}.kv dt{flex:0 0 92px;font-size:12.5px;font-weight:700;color:var(--sub);padding-top:2px}
.kv dd{font-size:14.5px;line-height:1.62;color:var(--ink2)}
.fx{display:grid;grid-template-columns:1fr 1fr;gap:10px}
@media(max-width:640px){.fx{grid-template-columns:1fr}}
.fxi{border:1px solid var(--line);border-radius:10px;padding:15px 16px;background:var(--paper)}
.fxi .h{font-weight:800;font-size:14px;letter-spacing:-.02em;display:flex;align-items:center;gap:7px}
.fxi .h i{width:9px;height:9px;border-radius:2px}
.fxi .d{font-size:13px;color:var(--sub);line-height:1.6;margin-top:6px}
.btn{font-family:inherit;font-size:14.5px;font-weight:700;letter-spacing:-.02em;border-radius:10px;padding:14px 20px;cursor:pointer;border:1px solid var(--ink);background:var(--ink);color:#fff;transition:.15s;text-decoration:none;display:inline-block}
.btn:hover{opacity:.86}.btn.sec{background:#fff;color:var(--ink);border-color:var(--line2)}.btn.sec:hover{border-color:var(--ink);opacity:1}
.btnrow{margin-top:46px;display:flex;flex-wrap:wrap;gap:9px;justify-content:center}
.cta{margin-top:52px;text-align:center;background:var(--paper);border:1px solid var(--line);border-radius:12px;padding:30px 24px}
.cta h2{font-size:22px}.cta p{margin:10px auto 0;max-width:32em;font-size:14.5px}
.cta .btn{margin-top:18px}
.mine{display:none;margin-top:22px;text-align:center}
.mine.on{display:block}
.mine .btn{margin-top:0}
.mine p{font-size:13px;color:var(--sub);margin-top:8px}
.adslot{margin-top:46px;min-height:100px;display:flex;align-items:center;justify-content:center}
body[data-ads="off"] .adslot{display:none}
.tl{list-style:none;display:grid;grid-template-columns:1fr 1fr;gap:6px 14px}
@media(max-width:640px){.tl{grid-template-columns:1fr}}
.tl li{border-bottom:1px solid var(--line)}
.tl a{display:flex;justify-content:space-between;align-items:center;gap:10px;padding:10px 2px;text-decoration:none;font-size:14px}
.tl a:hover{background:#FCFBF9}
.tl .c{font-size:11.5px;color:var(--sub);font-weight:700;letter-spacing:.04em}
.tl .cur{background:var(--paper)}
.tl .cur a{font-weight:800}
.disc{margin-top:14px;font-size:12px;color:var(--sub);line-height:1.8}
.foot{margin-top:70px;padding-top:18px;border-top:1px solid var(--line);font-size:12px;color:var(--sub);display:flex;gap:14px;flex-wrap:wrap;justify-content:center}
.foot a{color:var(--sub);text-decoration:none}.foot a:hover{color:var(--ink)}
@media(max-width:480px){h1{font-size:36px}.rline{font-size:16.5px}}
"""


def load_types(src):
    s = open(src, encoding="utf-8").read()
    i = s.index("const TYPES=") + len("const TYPES=")
    d, j, ins, esc = 0, i, False, False
    while True:
        c = s[j]
        if ins:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                ins = False
        else:
            if c == '"':
                ins = True
            elif c == "{":
                d += 1
            elif c == "}":
                d -= 1
                if d == 0:
                    break
        j += 1
    return json.loads(s[i:j + 1])


def slug(key):
    return key.replace("/", "")


def lead(key):
    return "BAL" if key == "BAL" else key.split("/")[0]


def e(s):
    return escape(s, quote=True)


def first_sentence(s):
    m = re.match(r"(.+?[.!?])(\s|$)", s)
    return (m.group(1) if m else s).strip()


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def head(title, desc, url, og_title, og_desc, extra=""):
    robots = '<meta name="robots" content="noindex,nofollow">\n' if NOINDEX else ""
    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{e(title)}</title>
{robots}<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="article">
<meta property="og:title" content="{e(og_title)}">
<meta property="og:description" content="{e(og_desc)}">
<meta property="og:image" content="{OG_IMAGE}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:url" content="{url}">
<meta property="og:site_name" content="{SITE}">
<meta property="og:locale" content="ko_KR">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="{FAVICON}">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css">
<style>{CSS}</style>{extra}
</head>"""


def footer(rel):
    return f"""<footer class="foot">
  <span>© {SITE}</span>
  <a href="{rel}">검사하기</a>
  <a href="{rel}t/">유형 41개</a>
  <a href="{rel}privacy.html">개인정보처리방침</a>
</footer>"""


def type_list(T, current=None, rel="./"):
    """계열별 묶음 목록. current는 현재 페이지 키(굵게)."""
    out = []
    for g in ["D", "I", "S", "C", "BAL"]:
        keys = [k for k in T if lead(k) == g]
        items = []
        for k in keys:
            cls = ' class="cur"' if k == current else ""
            href = f"{rel}{slug(k)}/"
            code = "균형" if k == "BAL" else k
            items.append(f'<li{cls}><a href="{href}"><span>{e(T[k]["t"])}</span><span class="c mono">{e(code)}</span></a></li>')
        col = FCOL.get(g, "#111")
        out.append(f'<h3 style="margin-top:22px;color:{col}">{GROUP[g]} <span style="color:var(--sub);font-weight:600">· {len(keys)}</span></h3>\n<ul class="tl">\n' + "\n".join(items) + "\n</ul>")
    return "\n".join(out)


def type_page(T, key, idx):
    t = T[key]
    sl = slug(key)
    url = f"{BASE}t/{sl}/"
    ld = lead(key)
    flat = key == "BAL"
    factors = F if flat else key.split("/")
    code_label = "네 방향 균형" if flat else "  ·  ".join(f"{f} {FNAME[f]}" for f in factors)
    dots = "".join(f'<i style="background:{FCOL[f]}"></i>' for f in factors)
    tag = "네 방향 균형" if flat else "주 성향  " + FLONG[ld]
    tagcol = "#111" if flat else FCOL[ld]
    band = "f_ALL.jpg" if flat else f"f_{ld}.jpg"
    title = f"{t['t']} — 행동유형 진단 ({'균형' if flat else key})"
    desc = f"{t['l']} {first_sentence(t['b1'])}"
    og_title = f"{t['t']} · 행동유형 진단"
    og_desc = t["l"] + " 3분 14문항, 회원가입 없이 결과 전부 공개."

    if t["f"][0]:
        fit_key = t["f"][0]
        fit_txt = re.sub(r"^[^—]*—\s*", "", t["f"][1])
        fit = f'<a href="../{slug(fit_key)}/"><b>{e(T[fit_key]["t"])}</b></a> — {e(fit_txt)}'
    else:
        fit = e(t["f"][1])

    strong = "".join(f"<li>{e(x)}</li>" for x in t["s"])
    weak = "".join(f"<li>{e(x)}</li>" for x in t["w"])
    fx = "".join(
        f'<div class="fxi"><div class="h"><i style="background:{FCOL[f]}"></i>{FLONG[f]}</div><div class="d">{e(FDESC[f])}</div></div>'
        for f in F)

    js = f"""
<script>
/* 공유 링크(?t=결과코드)로 들어온 사람에게 전체 결과로 가는 길을 연다 */
(function(){{
  try{{
    var q=new URLSearchParams(location.search).get("t");
    if(!q) return;
    var m=q.toUpperCase().replace(/[^A-Z0-9]/g,"").match(/^(BAL|[DISC]{{1,3}})([1-7]{{4}})$/);
    if(!m || m[1]!=="{sl}") return;
    var box=document.getElementById("mine"), a=document.getElementById("minelink");
    a.href="../../?t="+m[1]+"-"+m[2];
    box.classList.add("on");
  }}catch(e){{}}
}})();
function copyLink(btn){{
  var u="{url}";
  var done=function(){{ btn.textContent="복사됨"; setTimeout(function(){{btn.textContent="이 유형 링크 복사";}},1600); }};
  if(navigator.clipboard&&navigator.clipboard.writeText){{ navigator.clipboard.writeText(u).then(done).catch(function(){{prompt("주소를 복사하세요",u);}}); }}
  else prompt("주소를 복사하세요",u);
}}
</script>"""

    body = f"""
<body data-ads="off">
<div class="wrap">
<nav class="top"><a href="../../">← 행동유형 진단</a><a href="../">유형 41개</a></nav>

<figure class="rband"><img src="../../{band}" alt="{e(tag)}" width="1600" height="686" loading="eager"><span class="rbandtag" style="color:{tagcol}">{e(tag)}</span></figure>

<article>
<div class="rhead">
  <span class="eyebrow">행동유형 진단 · 41유형 중 {idx}번째</span>
  <span class="badge" style="margin-top:14px"><span class="dots">{dots}</span><span>{e(code_label)}</span></span>
  <h1>{e(t['t'])}</h1>
  <p class="rline">{e(t['l'])}</p>
</div>
<div class="rbody"><p>{e(t['b1'])}</p><p>{e(t['b2'])}</p></div>

<div class="mine" id="mine">
  <a class="btn" id="minelink" href="../../">내 결과 전체 보기 →</a>
  <p>공유받은 결과입니다. 강도 그래프와 상세 분석은 전체 결과에서 봅니다.</p>
</div>

<div class="sect two">
  <div><span class="eyebrow">이럴 때 강하다</span><div class="card"><ul class="pts">{strong}</ul></div></div>
  <div><span class="eyebrow">이럴 때 걸린다</span><div class="card"><ul class="pts">{weak}</ul></div></div>
</div>

<!-- 광고 자리 ② 유형 페이지 본문 중간 · 애드센스 승인 뒤 body[data-ads]를 "on"으로 바꾸고 <ins class="adsbygoogle"> 삽입 -->
<div class="adslot" id="ad-type-mid" aria-hidden="true"></div>

<div class="sect">
  <span class="eyebrow">압박 · 성장 · 자리</span>
  <div class="card" style="padding:6px 24px">
    <dl>
      <div class="kv"><dt>압박받을 때</dt><dd>{e(t['st'])}</dd></div>
      <div class="kv"><dt>성장 포인트</dt><dd>{e(t['g'])}</dd></div>
      <div class="kv"><dt>잘 맞는 자리</dt><dd>{e(t['j'])}</dd></div>
      <div class="kv"><dt>궁합 유형</dt><dd>{fit}</dd></div>
    </dl>
  </div>
</div>

<div class="sect">
  <span class="eyebrow">네 가지 방향</span>
  <div class="fx">{fx}</div>
</div>

<div class="cta">
  <h2>나는 어떤 유형일까</h2>
  <p>3분 14문항. 회원가입도 결제도 없고, 답변은 브라우저 안에서만 계산돼 서버로 가지 않습니다. 결과는 전부 공개됩니다.</p>
  <a class="btn" href="../../">나도 검사하기</a>
  <button class="btn sec" style="margin-top:18px;margin-left:6px" onclick="copyLink(this)">이 유형 링크 복사</button>
</div>
</article>

<div class="sect">
  <span class="eyebrow">다른 유형 보기</span>
  {type_list(T, current=key, rel="../")}
</div>

<div class="sect">
  <div class="card">
    <p class="disc">이 해설은 DISC 4요인 모델(W. M. Marston, 1928)의 구조를 참고해 문항·채점 기준·유형 해설을 전부 자체 제작한 것입니다. 어떤 상용 검사 도구의 문항이나 리포트도 사용하지 않았고, 어느 기업·기관의 공인 검사도 아닙니다. 강도 구간은 규준 표본 확보 전의 잠정값입니다.<br>
    <b>채용·승진·평가 등 개인에게 불이익이 갈 수 있는 결정의 근거로 사용하지 마세요.</b> 서로 다른 일하는 방식을 이야기하기 시작하는 도구로 쓰십시오.</p>
  </div>
</div>

{footer("../../")}
</div>
{js}
{ANALYTICS}
</body>
</html>
"""
    return head(title, desc, url, og_title, og_desc) + body


def list_page(T):
    url = f"{BASE}t/"
    body = f"""
<body data-ads="off">
<div class="wrap">
<nav class="top"><a href="../">← 행동유형 진단</a><span>유형 41개</span></nav>
<div class="rhead" style="margin-top:34px">
  <span class="eyebrow">행동유형 진단</span>
  <h1>41개 행동유형</h1>
  <p class="rline">단일 4 · 2조합 12 · 3조합 24 · 균형 1. 주도·사교·안정·신중 네 방향 가운데 뚜렷하게 쓰는 것의 조합으로 나뉩니다.</p>
</div>
<div class="sect">
  {type_list(T, rel="./")}
</div>
<div class="cta">
  <h2>나는 어떤 유형일까</h2>
  <p>3분 14문항. 회원가입도 결제도 없고, 결과는 전부 공개됩니다.</p>
  <a class="btn" href="../">나도 검사하기</a>
</div>
{footer("../")}
</div>
{ANALYTICS}
</body>
</html>
"""
    return head("41개 행동유형 목록 — 행동유형 진단", "주도·사교·안정·신중 네 방향의 조합으로 나뉘는 41개 행동유형 해설 목록.",
                url, "41개 행동유형 목록 · 행동유형 진단", "주도·사교·안정·신중 네 방향의 조합으로 나뉘는 41개 유형. 3분 14문항, 결과 전부 공개.") + body


def sitemap(T):
    urls = [BASE, BASE + "privacy.html", BASE + "t/"] + [f"{BASE}t/{slug(k)}/" for k in T]
    body = "\n".join(f"  <url><loc>{u}</loc></url>" for u in urls)
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{body}\n</urlset>\n'


def robots():
    return f"User-agent: *\nAllow: /\n\nSitemap: {BASE}sitemap.xml\n"


def main():
    T = load_types(SRC)
    assert len(T) == 41, f"유형 수가 41이 아닙니다: {len(T)}"
    n = 0
    for i, k in enumerate(T, 1):
        write(os.path.join(ROOT, "t", slug(k), "index.html"), type_page(T, k, i))
        n += 1
    write(os.path.join(ROOT, "t", "index.html"), list_page(T))
    write(os.path.join(ROOT, "sitemap.xml"), sitemap(T))
    write(os.path.join(ROOT, "robots.txt"), robots())
    print(f"유형 페이지 {n}개 + t/index.html + sitemap.xml({n + 3} url) + robots.txt  →  {ROOT}")


if __name__ == "__main__":
    sys.exit(main())
