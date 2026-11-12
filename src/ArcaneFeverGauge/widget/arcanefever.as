// Zenderal - Arcane Fever Gauge: Interface/exported/widgets/zenderal/arcanefever.swf, frame 1.
//
// A SkyUI HUD widget (our own code; no SkyUI code is copied). SkyUI's widget loader loads this movie
// into _root.WidgetContainer.<id> and talks to the clip named "widget" through the functions below
// (setClientInfo ... fadeTo, the same names SkyUI's WidgetBase answers). The Papyrus side is
// ZFG_ArcaneFeverWidget (extends SKI_WidgetBase); it only sends the fever value (setFever) and the
// layout numbers (setLayout).
//
// Built by src/ArcaneFeverGauge/tools/01-build-widget.py (skeleton SWF + FFDec's AS2 compiler).
// Never edit the .swf: edit this file and rebuild.
//
// Look: a dark disc in the Vel'dun bar body's colours, a thin ring in the bar frame's colour
// (#7D7767, read from Vel'dun's frame shape 758) with diamond tips at the four points, a purple arc
// that fills clockwise from the top with the fever (0-100), and a flame-and-blade symbol in the middle
// that turns purple as the fever rises. The arc flashes when the fever goes up and pulses from 80 on.
//
// Two hosts, one movie (W.host):
// - "truehud": Papyrus loads a copy into TrueHUD's movie (menu "TrueHUD"), as a sibling of TrueHUD's
//   player widget in _root.TrueHUD.TrueHUD_MainVisibilityWidgets. The list's visible bars ARE that
//   player widget (bPlayerWidgetForceHideVanillaBars hides the HUD's own). Every 20 frames this copy
//   unites the Frame and Outline bounds of the player widget's Health, Magicka and Stamina bars and sits
//   right of that block, vertically centred, its radius a share of the block's height. It shows and
//   fades with the player widget, and sets W.active so Papyrus knows to keep the HUD copy hidden.
// - "hud": SkyUI's widget loader puts a copy in the HUD menu. It does the same with Vel'dun's own bar
//   frames (shape 758 inside HUDMovieBaseInstance.Health.HealthMeter_mc / .Magica.MagickaMeter_mc),
//   which only show when TrueHUD's player widget is off. Papyrus suppresses it while the TrueHUD copy
//   is active. Without those clips it falls back to the Papyrus X/Y (1280x720 units, as SkyUI does).
// Both measure in their own movie's coordinates, so they follow any layout and aspect ratio.
// (Standalone, e.g. tools/02-preview.html in Ruffle, the movie centres itself and cycles the fever.)

var W = this.createEmptyMovieClip("widget", 1);
W.host = _root.HUDMovieBaseInstance != undefined ? "hud" : (_root.TrueHUD != undefined ? "truehud" : "preview");

// ---- constants ------------------------------------------------------------------------------------
W.R0 = 50;                   // drawing radius; the clip is scaled to the computed radius
W.C_BODY = 0x1D1A17;         // Vel'dun bar body (29,26,23 at 60%)
W.C_BODY2 = 0x231F20;        // Vel'dun bar body, lighter stop (35,31,32)
W.C_FRAME = 0x7D7767;        // Vel'dun bar frame (125,119,103)
W.C_GLYPH = 0xCFC3A6;        // symbol at 0 fever
W.C_HOT = 0xB8A2FF;          // symbol at 100 fever
W.C_TRACK = 0x241D38;        // empty arc channel
W.C_ARC = 0x7A5CE0;          // fever arc
W.C_GLOW = 0x8F72F0;         // soft glow under the arc
W.C_EDGE = 0xC2B0FF;         // leading edge of the arc
W.C_FLASH = 0xEFE9FF;        // flash when the fever rises
W.R_ARC1 = 38.2;             // arc channel, inner radius
W.R_ARC2 = 45.4;             // arc channel, outer radius
W.PULSE_FROM = 80;           // fever from which the arc pulses

// Corners of Vel'dun's bar frame (shape 758) in the meter clips' own coordinates:
// HealthMeter_mc places it at (-123.6, 0) scale 0.6726/0.6718, MagickaMeter_mc at (0.4, 1.7) scale 1;
// the shape's bounds are x -28.3..395.9, y -55.6..-26.2.
W.HEALTH_TOP_RIGHT = {x: 142.69, y: -37.35};
W.MANA_BOTTOM_RIGHT = {x: 396.3, y: -24.5};

W.MODES = ["All", "Favor", "MovementDisabled", "Swimming", "WarHorseMode", "HorseMode", "InventoryMode", "BookMode", "DialogueMode", "StealthMode", "SleepWaitMode", "BarterMode", "TweenMode", "WorldMapMode", "JournalMode", "CartMode", "VATSPlayback"];

// ---- state ----------------------------------------------------------------------------------------
W.fever = 0;                 // target value, 0-100
W.shown = -1;                // drawn value (eases toward fever); -1 = nothing received yet
W.flashA = 0;
W.userAlpha = 100;
W.layout = {radiusK: 0.64, gapK: 0.15, dx: 0, dy: 0};   // Papyrus sends its own (ZFG_ArcaneFeverWidget)
W.posX = 1040;               // fallback position (1280x720 units), from Papyrus X/Y
W.posY = 660;
W.hudMetrics = undefined;
W.tick = 0;
W.lastT = undefined;
W.placed = "";
W.active = false;            // found the bars it follows (Papyrus reads this on the TrueHUD copy)
W.suppressed = false;        // Papyrus hides the HUD copy while the TrueHUD copy is active
W.zfgReady = true;           // Papyrus checks this to know the movie has loaded
// Display options (MCM, through ZFG_ArcaneFeverWidget.ApplySettings -> setDisplay):
W.autoFade = false;          // fade out FADE_DELAY seconds after the fever last changed
W.fadeDelay = 5;
W.userHidden = false;        // the show/hide hotkey
W.FADE_IN_S = 0.2;
W.FADE_OUT_S = 1.0;
W.fadeA = 100;              // 0-100, multiplied into the alpha by follow()
W.showUntil = 0;            // getTimer() until which an auto-fading gauge stays up

// ---- drawing helpers ------------------------------------------------------------------------------
// Filled annular sector between radii r1 < r2, from angle a0 to a1 (radians, 0 = right, clockwise on
// screen because y points down). A full turn gives a ring; one contour, so no fill-rule questions.
W.band = function(mc, r1, r2, a0, a1, col, al)
{
   var n = Math.max(2, Math.ceil(Math.abs(a1 - a0) / 0.05));
   var i;
   var a;
   mc.beginFill(col, al);
   mc.moveTo(r2 * Math.cos(a0), r2 * Math.sin(a0));
   for (i = 1; i <= n; i++)
   {
      a = a0 + (a1 - a0) * i / n;
      mc.lineTo(r2 * Math.cos(a), r2 * Math.sin(a));
   }
   for (i = n; i >= 0; i--)
   {
      a = a0 + (a1 - a0) * i / n;
      mc.lineTo(r1 * Math.cos(a), r1 * Math.sin(a));
   }
   mc.endFill();
};

W.disc = function(mc, r, col, al)
{
   var i;
   var a;
   mc.beginFill(col, al);
   mc.moveTo(r, 0);
   for (i = 1; i <= 96; i++)
   {
      a = i * 2 * Math.PI / 96;
      mc.lineTo(r * Math.cos(a), r * Math.sin(a));
   }
   mc.endFill();
};

// Diamond centred at radius rc on angle a: hl along the radius, hw across it.
W.diamond = function(mc, a, rc, hl, hw, col, al)
{
   var c = Math.cos(a);
   var s = Math.sin(a);
   mc.beginFill(col, al);
   mc.moveTo((rc + hl) * c, (rc + hl) * s);
   mc.lineTo(rc * c - hw * s, rc * s + hw * c);
   mc.lineTo((rc - hl) * c, (rc - hl) * s);
   mc.lineTo(rc * c + hw * s, rc * s - hw * c);
   mc.lineTo((rc + hl) * c, (rc + hl) * s);
   mc.endFill();
};

// The symbol: a flame loop over two curled arms and a tapering blade (fever burns, then cuts).
W.drawGlyph = function(g, col)
{
   g.clear();
   g.lineStyle(2.6, col, 100);
   g.moveTo(0, -27);
   g.curveTo(7.5, -20, 6.5, -13.5);
   g.curveTo(5.5, -6.5, 0, -6);
   g.curveTo(-5.5, -6.5, -6.5, -13.5);
   g.curveTo(-7.5, -20, 0, -27);
   g.lineStyle(2.3, col, 100);
   g.moveTo(-2, -3.5);
   g.curveTo(-10, -5, -13, -0.5);
   g.curveTo(-15, 4, -10.5, 4.5);
   g.moveTo(2, -3.5);
   g.curveTo(10, -5, 13, -0.5);
   g.curveTo(15, 4, 10.5, 4.5);
   g.lineStyle();
   g.beginFill(col, 100);
   g.moveTo(0, -7);
   g.lineTo(2.8, -1.5);
   g.lineTo(0, 27);
   g.lineTo(-2.8, -1.5);
   g.lineTo(0, -7);
   g.endFill();
   g.beginFill(col, 100);
   g.moveTo(0, 6.5);
   g.lineTo(4.2, 9.5);
   g.lineTo(0, 12.5);
   g.lineTo(-4.2, 9.5);
   g.lineTo(0, 6.5);
   g.endFill();
};

W.build = function()
{
   var TWO_PI = 2 * Math.PI;
   var i;
   var a;
   this.bg = this.createEmptyMovieClip("bg", 1);
   this.disc(this.bg, 49.4, this.C_BODY, 60);
   this.disc(this.bg, 36.6, this.C_BODY2, 35);
   this.track = this.createEmptyMovieClip("track", 2);
   this.band(this.track, this.R_ARC1, this.R_ARC2, 0, TWO_PI, this.C_TRACK, 45);
   this.arc = this.createEmptyMovieClip("arc", 3);
   this.flash = this.createEmptyMovieClip("flash", 4);
   this.flash._alpha = 0;
   this.ring = this.createEmptyMovieClip("ring", 5);
   this.band(this.ring, 47.2, 49.6, 0, TWO_PI, this.C_FRAME, 100);
   this.band(this.ring, 35.6, 36.6, 0, TWO_PI, this.C_FRAME, 70);
   for (i = 0; i < 4; i++)
   {
      a = i * Math.PI / 2;
      this.diamond(this.ring, a, 48.4, 5.6, 3.6, this.C_FRAME, 100);
      this.diamond(this.ring, a, 48.4, 2.6, 1.6, this.C_BODY, 100);
   }
   this.glyph = this.createEmptyMovieClip("glyph", 6);
   this.drawGlyph(this.glyph, this.C_GLYPH);
   this.glyph._xscale = this.glyph._yscale = 88;
   this.hot = this.createEmptyMovieClip("hot", 7);
   this.drawGlyph(this.hot, this.C_HOT);
   this.hot._xscale = this.hot._yscale = 88;
   this.hot._alpha = 0;
};

W.drawArc = function()
{
   var p = Math.max(0, Math.min(100, this.shown)) / 100;
   var a0 = -Math.PI / 2;
   var a1 = a0 + p * 2 * Math.PI;
   this.arc.clear();
   this.flash.clear();
   if (p <= 0.002)
   {
      return;
   }
   this.band(this.arc, this.R_ARC1 - 1.2, this.R_ARC2 + 1.2, a0, a1, this.C_GLOW, 25);
   this.band(this.arc, this.R_ARC1, this.R_ARC2, a0, a1, this.C_ARC, 100);
   this.band(this.arc, this.R_ARC1, this.R_ARC2, Math.max(a0, a1 - 0.08), a1, this.C_EDGE, 100);
   this.band(this.flash, this.R_ARC1, this.R_ARC2, a0, a1, this.C_FLASH, 100);
};

// ---- placement ------------------------------------------------------------------------------------
W.unite = function(box, b)
{
   if (b == undefined || isNaN(b.xMin) || isNaN(b.yMin) || b.xMax < b.xMin)
   {
      return box;
   }
   if (box == undefined)
   {
      return {xMin: b.xMin, xMax: b.xMax, yMin: b.yMin, yMax: b.yMax};
   }
   box.xMin = Math.min(box.xMin, b.xMin);
   box.xMax = Math.max(box.xMax, b.xMax);
   box.yMin = Math.min(box.yMin, b.yMin);
   box.yMax = Math.max(box.yMax, b.yMax);
   return box;
};

// TrueHUD's player widget: the box of the bars as you SEE them. Each standalone bar's Frame is Vel'dun's
// LargeBarFrame (TrueHUD_Assets0.swf): a scale-9 sprite whose shape spans x -69..69 around a -50..50 centre,
// sized to the bar + 38 (TrueHUD_Bar.fFrameWidthOffset = 138 - 100), so a fixed 19-unit cap sits past each bar
// end. Only x -59.5..59.5 of that shape is drawn (alpha > 8 at 4x; y is full), so the arrow tip is FRAME_PAD
// units inside the frame's bounds. The cap is scale-9, so the pad stays FRAME_PAD in the bar's own space
// whatever the bar's width. Bars without a Frame (another skin) count by their whole bounds.
W.FRAME_PAD = 9.5;
W.measureTrueHUD = function()
{
   var pw = _root.TrueHUD.playerWidget;
   if (pw == undefined)
   {
      return undefined;
   }
   var holder = this._parent;
   var names = ["Health", "Magicka", "Stamina"];
   var box = undefined;
   var i;
   var k;
   for (i = 0; i < names.length; i++)
   {
      var bar = pw[names[i]];
      if (bar == undefined)
      {
         continue;
      }
      if (bar.Frame != undefined)
      {
         var fb = bar.Frame.getBounds(bar);
         var pts = [{x: fb.xMin + this.FRAME_PAD, y: fb.yMin}, {x: fb.xMax - this.FRAME_PAD, y: fb.yMin},
                    {x: fb.xMin + this.FRAME_PAD, y: fb.yMax}, {x: fb.xMax - this.FRAME_PAD, y: fb.yMax}];
         for (k = 0; k < pts.length; k++)
         {
            bar.localToGlobal(pts[k]);
            holder.globalToLocal(pts[k]);
            box = this.unite(box, {xMin: pts[k].x, xMax: pts[k].x, yMin: pts[k].y, yMax: pts[k].y});
         }
      }
      else
      {
         box = this.unite(box, bar.getBounds(holder));
      }
   }
   return box;
};

// Vel'dun's own bars in the HUD menu: two corners of the frame shape, in the meter clips' coordinates.
W.measureHUD = function()
{
   var hud = _root.HUDMovieBaseInstance;
   var hm = hud.Health.HealthMeter_mc;
   var mm = hud.Magica.MagickaMeter_mc;
   if (hm == undefined || mm == undefined)
   {
      return undefined;
   }
   var holder = this._parent;
   var a = {x: this.HEALTH_TOP_RIGHT.x, y: this.HEALTH_TOP_RIGHT.y};
   var b = {x: this.MANA_BOTTOM_RIGHT.x, y: this.MANA_BOTTOM_RIGHT.y};
   hm.localToGlobal(a);
   mm.localToGlobal(b);
   holder.globalToLocal(a);
   holder.globalToLocal(b);
   return {xMin: Math.min(a.x, b.x), xMax: Math.max(a.x, b.x), yMin: a.y, yMax: b.y};
};

W.place = function()
{
   var box = this.host == "truehud" ? this.measureTrueHUD() : this.measureHUD();
   var r;
   var cx;
   var cy;
   var how = this.host;
   if (box != undefined && box.yMax - box.yMin > 2)
   {
      var h = box.yMax - box.yMin;
      r = h * this.layout.radiusK;
      cx = box.xMax + h * this.layout.gapK + r + h * this.layout.dx;
      cy = (box.yMin + box.yMax) / 2 + h * this.layout.dy;
      this.active = true;
   }
   else if (this.host == "hud")
   {
      // SkyUI's own mapping of 1280x720 positions onto the HUD's safe area.
      var m = this.hudMetrics;
      r = 30;
      cx = this.posX;
      cy = this.posY;
      if (m != undefined)
      {
         cx = - m.hMin + (m.hMax + m.hMin) * this.posX / 1280;
         cy = - m.vMin + (m.vMax + m.vMin) * this.posY / 720;
      }
      how = "hud fallback, no Vel'dun bars";
      this.active = true;
   }
   else
   {
      // TrueHUD without its player widget: nothing to sit next to; the HUD copy takes over.
      this.active = false;
      how = "truehud, no player widget";
   }
   if (r != undefined)
   {
      this._x = cx;
      this._y = cy;
      this._xscale = this._yscale = 100 * r / this.R0;
   }
   var s = how + (r == undefined ? "" : " at " + Math.round(cx) + "," + Math.round(cy) + " r" + Math.round(r * 10) / 10)
      + (box == undefined ? "" : " (bars right " + Math.round(box.xMax) + ", top " + Math.round(box.yMin) + ", bottom " + Math.round(box.yMax) + ")");
   if (s != this.placed)
   {
      this.placed = s;
      if (_global.skse != undefined)
      {
         skse.Log("Zenderal Arcane Fever Gauge: " + s);
      }
   }
};

// Show and fade with the bars it follows.
W.follow = function()
{
   var v = this.active && !this.suppressed;
   var al = 100;
   var hb;
   var mb;
   if (this.host == "truehud")
   {
      var pw = _root.TrueHUD.playerWidget;
      if (pw == undefined || pw._visible == false)
      {
         v = false;
      }
      else
      {
         al = pw._alpha;
         var top = 0;
         var names = ["Health", "Magicka", "Stamina"];
         var i;
         for (i = 0; i < names.length; i++)
         {
            if (pw[names[i]] != undefined && pw[names[i]]._visible != false)
            {
               top = Math.max(top, pw[names[i]]._alpha);
            }
         }
         al = al * top / 100;
      }
   }
   else
   {
      var hud = _root.HUDMovieBaseInstance;
      if (hud != undefined)
      {
         if (hud._visible == false)
         {
            v = false;
         }
         if (hud._alpha != undefined)
         {
            al = hud._alpha;
         }
         hb = hud.Health;
         mb = hud.Magica;
         if (hb != undefined && mb != undefined)
         {
            if (hb._visible == false && mb._visible == false)
            {
               v = false;
            }
            if (hb.HealthMeter_mc != undefined && mb.MagickaMeter_mc != undefined)
            {
               al = al * Math.max(hb._alpha * hb.HealthMeter_mc._alpha, mb._alpha * mb.MagickaMeter_mc._alpha) / 10000;
            }
         }
      }
   }
   if (this.userHidden || this.fadeA <= 0)
   {
      v = false;
   }
   this._visible = v;
   this._alpha = al * this.userAlpha / 100 * this.fadeA / 100;
};

W.onEnterFrame = function()
{
   var t = getTimer();
   var dt = this.lastT == undefined ? 0.016 : Math.min(0.1, (t - this.lastT) / 1000);
   this.lastT = t;
   if (this.tick % 20 == 0)
   {
      this.place();
   }
   this.tick++;
   if (!this.autoFade || t < this.showUntil)
   {
      this.fadeA = Math.min(100, this.fadeA + dt * 100 / this.FADE_IN_S);
   }
   else
   {
      this.fadeA = Math.max(0, this.fadeA - dt * 100 / this.FADE_OUT_S);
   }
   this.follow();
   if (this.shown < 0)
   {
      return;
   }
   var d = this.fever - this.shown;
   if (Math.abs(d) > 0.05)
   {
      this.shown += d * Math.min(1, dt * 8);
      this.drawArc();
   }
   else if (this.shown != this.fever)
   {
      this.shown = this.fever;
      this.drawArc();
   }
   if (this.flashA > 0)
   {
      this.flashA = Math.max(0, this.flashA - dt * 120);
      this.flash._alpha = this.flashA;
   }
   if (this.fever >= this.PULSE_FROM)
   {
      this.arc._alpha = 82 + 18 * Math.sin(t / 1000 * Math.PI * 1.6);
   }
   else
   {
      this.arc._alpha = 100;
   }
};

// ---- our interface (Papyrus: ZFG_ArcaneFeverWidget) -----------------------------------------------
W.setFever = function(v)
{
   v = Number(v);
   if (isNaN(v))
   {
      return;
   }
   v = Math.max(0, Math.min(100, v));
   if (this.shown < 0)
   {
      this.shown = v;
      this.peek();
   }
   else
   {
      if (v > this.fever + 0.05)
      {
         this.flashA = 55;
      }
      if (Math.abs(v - this.fever) > 0.05)
      {
         this.peek();
      }
   }
   this.fever = v;
   this.hot._alpha = v * 0.55;
   this.drawArc();
};

// autoFade / hidden as 0 or 1 (Papyrus sends floats), delay in seconds. Restarts the fade timer.
W.setDisplay = function(autoFade, delay, hidden)
{
   this.autoFade = autoFade == true || autoFade == "true" || Number(autoFade) == 1;
   if (!isNaN(Number(delay)) && Number(delay) > 0)
   {
      this.fadeDelay = Number(delay);
   }
   this.userHidden = hidden == true || hidden == "true" || Number(hidden) == 1;
   this.peek();
   this.follow();
};

// Show an auto-fading gauge again for fadeDelay seconds (fever change, hotkey).
W.peek = function()
{
   this.showUntil = getTimer() + this.fadeDelay * 1000;
};

W.setSuppressed = function(b)
{
   this.suppressed = b == true || b == "true" || Number(b) == 1;
   this.follow();
};

W.setLayout = function(radiusK, gapK, dx, dy)
{
   if (!isNaN(Number(radiusK)) && Number(radiusK) > 0)
   {
      this.layout.radiusK = Number(radiusK);
   }
   if (!isNaN(Number(gapK)))
   {
      this.layout.gapK = Number(gapK);
   }
   if (!isNaN(Number(dx)))
   {
      this.layout.dx = Number(dx);
   }
   if (!isNaN(Number(dy)))
   {
      this.layout.dy = Number(dy);
   }
   this.place();
};

// ---- SkyUI widget interface (called by SKI_WidgetBase and the widget loader) ----------------------
W.setRootPath = function(a_path)
{
};

W.setHudMetrics = function(a_hudMetrics)
{
   this.hudMetrics = a_hudMetrics;
};

W.setClientInfo = function(a_clientString)
{
};

W.setModes = function()
{
   var holder = this._parent;
   var hud = _root.HUDMovieBaseInstance;
   var i;
   var k;
   var n = 0;
   for (i = 0; i < this.MODES.length; i++)
   {
      delete holder[this.MODES[i]];
   }
   for (i = 0; i < arguments.length; i++)
   {
      for (k = 0; k < this.MODES.length; k++)
      {
         if (String(arguments[i]).toLowerCase() == this.MODES[k].toLowerCase())
         {
            holder[this.MODES[k]] = true;
            n++;
         }
      }
   }
   if (n == 0 && _global.skse != undefined)
   {
      skse.SendModEvent("SKIWF_widgetError", "NoValidModes", Number(holder._name));
   }
   if (hud != undefined)
   {
      var cur = hud.HUDModes[hud.HUDModes.length - 1];
      holder._visible = holder[cur] == true;
      var found = false;
      for (i = 0; i < hud.HudElements.length; i++)
      {
         if (hud.HudElements[i] == holder)
         {
            found = true;
         }
      }
      if (!found)
      {
         hud.HudElements.push(holder);
      }
   }
};

W.setHAnchor = function(a_hAnchor)
{
};

W.setVAnchor = function(a_vAnchor)
{
};

W.setPositionX = function(a_x)
{
   this.posX = Number(a_x);
   this.place();
};

W.setPositionY = function(a_y)
{
   this.posY = Number(a_y);
   this.place();
};

W.setAlpha = function(a_alpha)
{
   this.userAlpha = Number(a_alpha);
   this.follow();
};

W.tweenTo = function(a_x, a_y, a_duration)
{
   this.posX = Number(a_x);
   this.posY = Number(a_y);
   this.place();
};

W.fadeTo = function(a_alpha, a_duration)
{
   this.setAlpha(a_alpha);
};

W.getWidth = function()
{
   return this._width;
};

W.getHeight = function()
{
   return this._height;
};

W.build();

if (W.host == "hud")
{
   // In the HUD: hidden until SkyUI sends the modes, as SkyUI's own widgets are.
   this._visible = false;
}
else if (W.host == "truehud")
{
   // In TrueHUD: TrueHUD's visibility container hides it with the player widget; no SkyUI calls.
   W.place();
   W.follow();
}
else
{
   // Standalone (tools/02-preview.html in Ruffle): centred, larger, cycling through the fever.
   W.place = function()
   {
      this._x = Stage.width / 2;
      this._y = Stage.height / 2;
      this._xscale = this._yscale = 160;
   };
   W.follow = function()
   {
   };
   W.demo = 0;
   W.setFever(0);
   setInterval(function()
   {
      W.demo = W.demo >= 100 ? 0 : W.demo + 12.5;
      W.setFever(W.demo);
   }, 2000);
}
