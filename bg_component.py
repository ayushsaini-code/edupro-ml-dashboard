"""EduPro animated background (decorative only).

Draws a slow neural-network field - drifting cyan/blue particles joined by
faint lines, with mouse/idle parallax - on a single fixed <canvas> that sits
BEHIND the Streamlit app.

How it is embedded
------------------
Streamlit has no "page background" API, so a zero-height components iframe
loads a tiny loader script. The loader injects the animation script into the
parent page (the component iframe is same-origin), where it creates one
<canvas id="edupro-bg-canvas"> with pointer-events:none and z-index:-2.

* Idempotent: Streamlit reruns re-execute this call; the script detects the
  running instance and does nothing, so there is never more than one canvas.
* Safe fallback: if the parent page cannot be reached, the loader exits
  silently. The CSS layers in theme.py (grid, moving glows, overlay) still
  provide the background, and the dashboard is unaffected.
* Performance: capped at ~30 fps, <=120 particles, device-pixel-ratio capped at
  1.5, paused while the tab is hidden, and a single still frame is drawn when
  the user prefers reduced motion.
* Independent of data: it reads nothing from the app and touches no model,
  metric or calculation.
"""

import json

import streamlit.components.v1 as components

_VERSION = "3"

# Runs in the PARENT page's context.
_ANIMATION_JS = r"""
(function () {
  var V = "__VERSION__";
  if (window.__eduproBg) {
    if (window.__eduproBg.v === V) { return; }
    window.__eduproBg.stop();
  }
  var doc = document;
  var stale = doc.getElementById("edupro-bg-canvas");
  if (stale) { stale.remove(); }

  var canvas = doc.createElement("canvas");
  canvas.id = "edupro-bg-canvas";
  canvas.setAttribute("aria-hidden", "true");
  canvas.style.cssText =
    "position:fixed;top:0;left:0;width:100vw;height:100vh;" +
    "z-index:-2;pointer-events:none;display:block;";
  doc.body.appendChild(canvas);
  var ctx = canvas.getContext("2d");
  if (!ctx) { canvas.remove(); return; }

  var mq = window.matchMedia("(prefers-reduced-motion: reduce)");
  var dpr = Math.min(window.devicePixelRatio || 1, 1.5);
  var FRAME_MS = 1000 / 30;
  var COLORS = [[34, 211, 238], [59, 130, 246], [139, 92, 246]];
  var w = 0, h = 0, parts = [];
  var raf = 0, running = false, last = 0;
  var tx = 0, ty = 0, mx = 0, my = 0;
  var resizeTimer = 0;

  function build() {
    var n = Math.min(120, Math.max(34, Math.round((w * h) / 14500)));
    parts = [];
    for (var i = 0; i < n; i++) {
      var z = 0.25 + Math.random() * 0.75;
      var roll = Math.random();
      parts.push({
        x: Math.random() * w,
        y: Math.random() * h,
        vx: (Math.random() - 0.5) * 0.2 * (0.4 + z),
        vy: (Math.random() - 0.5) * 0.2 * (0.4 + z),
        z: z,
        r: 0.8 + z * 1.7,
        c: roll < 0.62 ? 0 : (roll < 0.92 ? 1 : 2)
      });
    }
  }

  function size() {
    w = window.innerWidth;
    h = window.innerHeight;
    canvas.width = Math.round(w * dpr);
    canvas.height = Math.round(h * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    build();
  }

  function step(dt) {
    var k = dt / 33;
    for (var i = 0; i < parts.length; i++) {
      var p = parts[i];
      p.x += p.vx * k;
      p.y += p.vy * k;
      if (p.x < -40) { p.x = w + 40; } else if (p.x > w + 40) { p.x = -40; }
      if (p.y < -40) { p.y = h + 40; } else if (p.y > h + 40) { p.y = -40; }
    }
    mx += (tx - mx) * 0.04;
    my += (ty - my) * 0.04;
  }

  function draw(ts) {
    ctx.clearRect(0, 0, w, h);
    var idleX = Math.sin(ts / 9000) * 0.35;
    var idleY = Math.cos(ts / 11000) * 0.35;
    var px = (mx + idleX) * 26;
    var py = (my + idleY) * 26;
    var maxD = Math.min(175, Math.max(115, w / 9));
    var maxD2 = maxD * maxD;
    var n = parts.length;
    var xs = new Array(n), ys = new Array(n);

    for (var i = 0; i < n; i++) {
      xs[i] = parts[i].x + px * parts[i].z;
      ys[i] = parts[i].y + py * parts[i].z;
    }

    ctx.lineWidth = 1;
    for (var a = 0; a < n; a++) {
      for (var b = a + 1; b < n; b++) {
        var dx = xs[a] - xs[b], dy = ys[a] - ys[b];
        var d2 = dx * dx + dy * dy;
        if (d2 < maxD2) {
          var t = 1 - Math.sqrt(d2) / maxD;
          var depth = Math.min(parts[a].z, parts[b].z);
          ctx.strokeStyle =
            "rgba(70,160,255," + (t * 0.34 * (0.45 + depth)).toFixed(3) + ")";
          ctx.beginPath();
          ctx.moveTo(xs[a], ys[a]);
          ctx.lineTo(xs[b], ys[b]);
          ctx.stroke();
        }
      }
    }

    for (var j = 0; j < n; j++) {
      var q = parts[j], col = COLORS[q.c];
      var rgb = col[0] + "," + col[1] + "," + col[2];
      ctx.fillStyle = "rgba(" + rgb + ",0.10)";
      ctx.beginPath();
      ctx.arc(xs[j], ys[j], q.r * 3.4, 0, 6.2832);
      ctx.fill();
      ctx.fillStyle = "rgba(" + rgb + "," + (0.5 + q.z * 0.45).toFixed(2) + ")";
      ctx.beginPath();
      ctx.arc(xs[j], ys[j], q.r, 0, 6.2832);
      ctx.fill();
    }
  }

  function loop(ts) {
    raf = window.requestAnimationFrame(loop);
    if (ts - last < FRAME_MS) { return; }
    var dt = Math.min(64, ts - last);
    last = ts;
    step(dt);
    draw(ts);
  }

  function start() {
    if (running || mq.matches || doc.hidden) { return; }
    running = true;
    last = performance.now();
    raf = window.requestAnimationFrame(loop);
  }

  function pause() {
    running = false;
    window.cancelAnimationFrame(raf);
  }

  function still() { draw(0); }

  function onVisibility() {
    if (doc.hidden) { pause(); } else { start(); }
  }

  function onMotionPref() {
    if (mq.matches) { pause(); still(); } else { start(); }
  }

  function onMove(e) {
    tx = e.clientX / w - 0.5;
    ty = e.clientY / h - 0.5;
  }

  function onResize() {
    window.clearTimeout(resizeTimer);
    resizeTimer = window.setTimeout(function () {
      size();
      if (!running) { still(); }
    }, 150);
  }

  function stop() {
    pause();
    window.clearTimeout(resizeTimer);
    window.removeEventListener("resize", onResize);
    window.removeEventListener("mousemove", onMove);
    doc.removeEventListener("visibilitychange", onVisibility);
    if (mq.removeEventListener) { mq.removeEventListener("change", onMotionPref); }
    if (canvas.parentNode) { canvas.parentNode.removeChild(canvas); }
    delete window.__eduproBg;
  }

  window.addEventListener("resize", onResize);
  window.addEventListener("mousemove", onMove, { passive: true });
  doc.addEventListener("visibilitychange", onVisibility);
  if (mq.addEventListener) { mq.addEventListener("change", onMotionPref); }

  size();
  window.__eduproBg = { v: V, stop: stop };
  if (mq.matches) { still(); } else { start(); }
})();
""".replace("__VERSION__", _VERSION)


# Runs inside the zero-height component iframe.
_LOADER_JS = """
(function () {
  try {
    var host = window.frameElement;
    var parentWin = window.parent;
    var pdoc = parentWin.document;
    if (host) {
      var box = host.closest('[data-testid="stElementContainer"]') ||
                host.closest('.element-container') || host.parentElement;
      if (box) {
        box.style.cssText =
          'position:absolute;width:0;height:0;overflow:hidden;margin:0;padding:0;';
      }
    }
    if (parentWin.__eduproBg && parentWin.__eduproBg.v === "%s") { return; }
    var tag = pdoc.getElementById('edupro-bg-script');
    if (tag) { tag.remove(); }
    var s = pdoc.createElement('script');
    s.id = 'edupro-bg-script';
    s.textContent = %s;
    pdoc.head.appendChild(s);
  } catch (err) {
    /* Parent not reachable: the CSS background layers remain. */
  }
})();
""" % (_VERSION, json.dumps(_ANIMATION_JS).replace("</", "<\\/"))


def render_background() -> None:
    """Mount the animated background. Safe to call on every rerun."""
    markup = "<script>" + _LOADER_JS + "</script>"
    try:
        components.html(markup, height=0)
    except Exception:
        # Purely decorative: never let the background break the dashboard.
        pass
