// node_modules/preact/dist/preact.module.js
var n;
var l;
var u;
var t;
var i;
var o;
var r;
var f;
var e;
var c;
var s;
var a;
var h = {};
var v = [];
var p = /acit|ex(?:s|g|n|p|$)|rph|grid|ows|mnc|ntw|ine[ch]|zoo|^ord|itera/i;
var y = Array.isArray;
function d(n2, l2) {
  for (var u3 in l2) n2[u3] = l2[u3];
  return n2;
}
function w(n2) {
  n2 && n2.parentNode && n2.parentNode.removeChild(n2);
}
function _(l2, u3, t2) {
  var i3, o2, r2, f3 = {};
  for (r2 in u3) "key" == r2 ? i3 = u3[r2] : "ref" == r2 ? o2 = u3[r2] : f3[r2] = u3[r2];
  if (arguments.length > 2 && (f3.children = arguments.length > 3 ? n.call(arguments, 2) : t2), "function" == typeof l2 && null != l2.defaultProps) for (r2 in l2.defaultProps) void 0 === f3[r2] && (f3[r2] = l2.defaultProps[r2]);
  return g(l2, f3, i3, o2, null);
}
function g(n2, t2, i3, o2, r2) {
  var f3 = { type: n2, props: t2, key: i3, ref: o2, __k: null, __: null, __b: 0, __e: null, __d: void 0, __c: null, constructor: void 0, __v: null == r2 ? ++u : r2, __i: -1, __u: 0 };
  return null == r2 && null != l.vnode && l.vnode(f3), f3;
}
function b(n2) {
  return n2.children;
}
function k(n2, l2) {
  this.props = n2, this.context = l2;
}
function x(n2, l2) {
  if (null == l2) return n2.__ ? x(n2.__, n2.__i + 1) : null;
  for (var u3; l2 < n2.__k.length; l2++) if (null != (u3 = n2.__k[l2]) && null != u3.__e) return u3.__e;
  return "function" == typeof n2.type ? x(n2) : null;
}
function C(n2) {
  var l2, u3;
  if (null != (n2 = n2.__) && null != n2.__c) {
    for (n2.__e = n2.__c.base = null, l2 = 0; l2 < n2.__k.length; l2++) if (null != (u3 = n2.__k[l2]) && null != u3.__e) {
      n2.__e = n2.__c.base = u3.__e;
      break;
    }
    return C(n2);
  }
}
function S(n2) {
  (!n2.__d && (n2.__d = true) && i.push(n2) && !M.__r++ || o !== l.debounceRendering) && ((o = l.debounceRendering) || r)(M);
}
function M() {
  var n2, u3, t2, o2, r2, e2, c2, s2;
  for (i.sort(f); n2 = i.shift(); ) n2.__d && (u3 = i.length, o2 = void 0, e2 = (r2 = (t2 = n2).__v).__e, c2 = [], s2 = [], t2.__P && ((o2 = d({}, r2)).__v = r2.__v + 1, l.vnode && l.vnode(o2), O(t2.__P, o2, r2, t2.__n, t2.__P.namespaceURI, 32 & r2.__u ? [e2] : null, c2, null == e2 ? x(r2) : e2, !!(32 & r2.__u), s2), o2.__v = r2.__v, o2.__.__k[o2.__i] = o2, j(c2, o2, s2), o2.__e != e2 && C(o2)), i.length > u3 && i.sort(f));
  M.__r = 0;
}
function P(n2, l2, u3, t2, i3, o2, r2, f3, e2, c2, s2) {
  var a2, p2, y2, d2, w2, _2 = t2 && t2.__k || v, g2 = l2.length;
  for (u3.__d = e2, $(u3, l2, _2), e2 = u3.__d, a2 = 0; a2 < g2; a2++) null != (y2 = u3.__k[a2]) && (p2 = -1 === y2.__i ? h : _2[y2.__i] || h, y2.__i = a2, O(n2, y2, p2, i3, o2, r2, f3, e2, c2, s2), d2 = y2.__e, y2.ref && p2.ref != y2.ref && (p2.ref && N(p2.ref, null, y2), s2.push(y2.ref, y2.__c || d2, y2)), null == w2 && null != d2 && (w2 = d2), 65536 & y2.__u || p2.__k === y2.__k ? e2 = I(y2, e2, n2) : "function" == typeof y2.type && void 0 !== y2.__d ? e2 = y2.__d : d2 && (e2 = d2.nextSibling), y2.__d = void 0, y2.__u &= -196609);
  u3.__d = e2, u3.__e = w2;
}
function $(n2, l2, u3) {
  var t2, i3, o2, r2, f3, e2 = l2.length, c2 = u3.length, s2 = c2, a2 = 0;
  for (n2.__k = [], t2 = 0; t2 < e2; t2++) null != (i3 = l2[t2]) && "boolean" != typeof i3 && "function" != typeof i3 ? (r2 = t2 + a2, (i3 = n2.__k[t2] = "string" == typeof i3 || "number" == typeof i3 || "bigint" == typeof i3 || i3.constructor == String ? g(null, i3, null, null, null) : y(i3) ? g(b, { children: i3 }, null, null, null) : void 0 === i3.constructor && i3.__b > 0 ? g(i3.type, i3.props, i3.key, i3.ref ? i3.ref : null, i3.__v) : i3).__ = n2, i3.__b = n2.__b + 1, o2 = null, -1 !== (f3 = i3.__i = L(i3, u3, r2, s2)) && (s2--, (o2 = u3[f3]) && (o2.__u |= 131072)), null == o2 || null === o2.__v ? (-1 == f3 && a2--, "function" != typeof i3.type && (i3.__u |= 65536)) : f3 !== r2 && (f3 == r2 - 1 ? a2-- : f3 == r2 + 1 ? a2++ : (f3 > r2 ? a2-- : a2++, i3.__u |= 65536))) : i3 = n2.__k[t2] = null;
  if (s2) for (t2 = 0; t2 < c2; t2++) null != (o2 = u3[t2]) && 0 == (131072 & o2.__u) && (o2.__e == n2.__d && (n2.__d = x(o2)), V(o2, o2));
}
function I(n2, l2, u3) {
  var t2, i3;
  if ("function" == typeof n2.type) {
    for (t2 = n2.__k, i3 = 0; t2 && i3 < t2.length; i3++) t2[i3] && (t2[i3].__ = n2, l2 = I(t2[i3], l2, u3));
    return l2;
  }
  n2.__e != l2 && (l2 && n2.type && !u3.contains(l2) && (l2 = x(n2)), u3.insertBefore(n2.__e, l2 || null), l2 = n2.__e);
  do {
    l2 = l2 && l2.nextSibling;
  } while (null != l2 && 8 === l2.nodeType);
  return l2;
}
function L(n2, l2, u3, t2) {
  var i3 = n2.key, o2 = n2.type, r2 = u3 - 1, f3 = u3 + 1, e2 = l2[u3];
  if (null === e2 || e2 && i3 == e2.key && o2 === e2.type && 0 == (131072 & e2.__u)) return u3;
  if (t2 > (null != e2 && 0 == (131072 & e2.__u) ? 1 : 0)) for (; r2 >= 0 || f3 < l2.length; ) {
    if (r2 >= 0) {
      if ((e2 = l2[r2]) && 0 == (131072 & e2.__u) && i3 == e2.key && o2 === e2.type) return r2;
      r2--;
    }
    if (f3 < l2.length) {
      if ((e2 = l2[f3]) && 0 == (131072 & e2.__u) && i3 == e2.key && o2 === e2.type) return f3;
      f3++;
    }
  }
  return -1;
}
function T(n2, l2, u3) {
  "-" === l2[0] ? n2.setProperty(l2, null == u3 ? "" : u3) : n2[l2] = null == u3 ? "" : "number" != typeof u3 || p.test(l2) ? u3 : u3 + "px";
}
function A(n2, l2, u3, t2, i3) {
  var o2;
  n: if ("style" === l2) if ("string" == typeof u3) n2.style.cssText = u3;
  else {
    if ("string" == typeof t2 && (n2.style.cssText = t2 = ""), t2) for (l2 in t2) u3 && l2 in u3 || T(n2.style, l2, "");
    if (u3) for (l2 in u3) t2 && u3[l2] === t2[l2] || T(n2.style, l2, u3[l2]);
  }
  else if ("o" === l2[0] && "n" === l2[1]) o2 = l2 !== (l2 = l2.replace(/(PointerCapture)$|Capture$/i, "$1")), l2 = l2.toLowerCase() in n2 || "onFocusOut" === l2 || "onFocusIn" === l2 ? l2.toLowerCase().slice(2) : l2.slice(2), n2.l || (n2.l = {}), n2.l[l2 + o2] = u3, u3 ? t2 ? u3.u = t2.u : (u3.u = e, n2.addEventListener(l2, o2 ? s : c, o2)) : n2.removeEventListener(l2, o2 ? s : c, o2);
  else {
    if ("http://www.w3.org/2000/svg" == i3) l2 = l2.replace(/xlink(H|:h)/, "h").replace(/sName$/, "s");
    else if ("width" != l2 && "height" != l2 && "href" != l2 && "list" != l2 && "form" != l2 && "tabIndex" != l2 && "download" != l2 && "rowSpan" != l2 && "colSpan" != l2 && "role" != l2 && "popover" != l2 && l2 in n2) try {
      n2[l2] = null == u3 ? "" : u3;
      break n;
    } catch (n3) {
    }
    "function" == typeof u3 || (null == u3 || false === u3 && "-" !== l2[4] ? n2.removeAttribute(l2) : n2.setAttribute(l2, "popover" == l2 && 1 == u3 ? "" : u3));
  }
}
function F(n2) {
  return function(u3) {
    if (this.l) {
      var t2 = this.l[u3.type + n2];
      if (null == u3.t) u3.t = e++;
      else if (u3.t < t2.u) return;
      return t2(l.event ? l.event(u3) : u3);
    }
  };
}
function O(n2, u3, t2, i3, o2, r2, f3, e2, c2, s2) {
  var a2, h2, v2, p2, w2, _2, g2, m, x2, C2, S2, M2, $2, I2, H, L2, T2 = u3.type;
  if (void 0 !== u3.constructor) return null;
  128 & t2.__u && (c2 = !!(32 & t2.__u), r2 = [e2 = u3.__e = t2.__e]), (a2 = l.__b) && a2(u3);
  n: if ("function" == typeof T2) try {
    if (m = u3.props, x2 = "prototype" in T2 && T2.prototype.render, C2 = (a2 = T2.contextType) && i3[a2.__c], S2 = a2 ? C2 ? C2.props.value : a2.__ : i3, t2.__c ? g2 = (h2 = u3.__c = t2.__c).__ = h2.__E : (x2 ? u3.__c = h2 = new T2(m, S2) : (u3.__c = h2 = new k(m, S2), h2.constructor = T2, h2.render = q), C2 && C2.sub(h2), h2.props = m, h2.state || (h2.state = {}), h2.context = S2, h2.__n = i3, v2 = h2.__d = true, h2.__h = [], h2._sb = []), x2 && null == h2.__s && (h2.__s = h2.state), x2 && null != T2.getDerivedStateFromProps && (h2.__s == h2.state && (h2.__s = d({}, h2.__s)), d(h2.__s, T2.getDerivedStateFromProps(m, h2.__s))), p2 = h2.props, w2 = h2.state, h2.__v = u3, v2) x2 && null == T2.getDerivedStateFromProps && null != h2.componentWillMount && h2.componentWillMount(), x2 && null != h2.componentDidMount && h2.__h.push(h2.componentDidMount);
    else {
      if (x2 && null == T2.getDerivedStateFromProps && m !== p2 && null != h2.componentWillReceiveProps && h2.componentWillReceiveProps(m, S2), !h2.__e && (null != h2.shouldComponentUpdate && false === h2.shouldComponentUpdate(m, h2.__s, S2) || u3.__v === t2.__v)) {
        for (u3.__v !== t2.__v && (h2.props = m, h2.state = h2.__s, h2.__d = false), u3.__e = t2.__e, u3.__k = t2.__k, u3.__k.some(function(n3) {
          n3 && (n3.__ = u3);
        }), M2 = 0; M2 < h2._sb.length; M2++) h2.__h.push(h2._sb[M2]);
        h2._sb = [], h2.__h.length && f3.push(h2);
        break n;
      }
      null != h2.componentWillUpdate && h2.componentWillUpdate(m, h2.__s, S2), x2 && null != h2.componentDidUpdate && h2.__h.push(function() {
        h2.componentDidUpdate(p2, w2, _2);
      });
    }
    if (h2.context = S2, h2.props = m, h2.__P = n2, h2.__e = false, $2 = l.__r, I2 = 0, x2) {
      for (h2.state = h2.__s, h2.__d = false, $2 && $2(u3), a2 = h2.render(h2.props, h2.state, h2.context), H = 0; H < h2._sb.length; H++) h2.__h.push(h2._sb[H]);
      h2._sb = [];
    } else do {
      h2.__d = false, $2 && $2(u3), a2 = h2.render(h2.props, h2.state, h2.context), h2.state = h2.__s;
    } while (h2.__d && ++I2 < 25);
    h2.state = h2.__s, null != h2.getChildContext && (i3 = d(d({}, i3), h2.getChildContext())), x2 && !v2 && null != h2.getSnapshotBeforeUpdate && (_2 = h2.getSnapshotBeforeUpdate(p2, w2)), P(n2, y(L2 = null != a2 && a2.type === b && null == a2.key ? a2.props.children : a2) ? L2 : [L2], u3, t2, i3, o2, r2, f3, e2, c2, s2), h2.base = u3.__e, u3.__u &= -161, h2.__h.length && f3.push(h2), g2 && (h2.__E = h2.__ = null);
  } catch (n3) {
    if (u3.__v = null, c2 || null != r2) {
      for (u3.__u |= c2 ? 160 : 128; e2 && 8 === e2.nodeType && e2.nextSibling; ) e2 = e2.nextSibling;
      r2[r2.indexOf(e2)] = null, u3.__e = e2;
    } else u3.__e = t2.__e, u3.__k = t2.__k;
    l.__e(n3, u3, t2);
  }
  else null == r2 && u3.__v === t2.__v ? (u3.__k = t2.__k, u3.__e = t2.__e) : u3.__e = z(t2.__e, u3, t2, i3, o2, r2, f3, c2, s2);
  (a2 = l.diffed) && a2(u3);
}
function j(n2, u3, t2) {
  u3.__d = void 0;
  for (var i3 = 0; i3 < t2.length; i3++) N(t2[i3], t2[++i3], t2[++i3]);
  l.__c && l.__c(u3, n2), n2.some(function(u4) {
    try {
      n2 = u4.__h, u4.__h = [], n2.some(function(n3) {
        n3.call(u4);
      });
    } catch (n3) {
      l.__e(n3, u4.__v);
    }
  });
}
function z(u3, t2, i3, o2, r2, f3, e2, c2, s2) {
  var a2, v2, p2, d2, _2, g2, m, b2 = i3.props, k2 = t2.props, C2 = t2.type;
  if ("svg" === C2 ? r2 = "http://www.w3.org/2000/svg" : "math" === C2 ? r2 = "http://www.w3.org/1998/Math/MathML" : r2 || (r2 = "http://www.w3.org/1999/xhtml"), null != f3) {
    for (a2 = 0; a2 < f3.length; a2++) if ((_2 = f3[a2]) && "setAttribute" in _2 == !!C2 && (C2 ? _2.localName === C2 : 3 === _2.nodeType)) {
      u3 = _2, f3[a2] = null;
      break;
    }
  }
  if (null == u3) {
    if (null === C2) return document.createTextNode(k2);
    u3 = document.createElementNS(r2, C2, k2.is && k2), c2 && (l.__m && l.__m(t2, f3), c2 = false), f3 = null;
  }
  if (null === C2) b2 === k2 || c2 && u3.data === k2 || (u3.data = k2);
  else {
    if (f3 = f3 && n.call(u3.childNodes), b2 = i3.props || h, !c2 && null != f3) for (b2 = {}, a2 = 0; a2 < u3.attributes.length; a2++) b2[(_2 = u3.attributes[a2]).name] = _2.value;
    for (a2 in b2) if (_2 = b2[a2], "children" == a2) ;
    else if ("dangerouslySetInnerHTML" == a2) p2 = _2;
    else if (!(a2 in k2)) {
      if ("value" == a2 && "defaultValue" in k2 || "checked" == a2 && "defaultChecked" in k2) continue;
      A(u3, a2, null, _2, r2);
    }
    for (a2 in k2) _2 = k2[a2], "children" == a2 ? d2 = _2 : "dangerouslySetInnerHTML" == a2 ? v2 = _2 : "value" == a2 ? g2 = _2 : "checked" == a2 ? m = _2 : c2 && "function" != typeof _2 || b2[a2] === _2 || A(u3, a2, _2, b2[a2], r2);
    if (v2) c2 || p2 && (v2.__html === p2.__html || v2.__html === u3.innerHTML) || (u3.innerHTML = v2.__html), t2.__k = [];
    else if (p2 && (u3.innerHTML = ""), P(u3, y(d2) ? d2 : [d2], t2, i3, o2, "foreignObject" === C2 ? "http://www.w3.org/1999/xhtml" : r2, f3, e2, f3 ? f3[0] : i3.__k && x(i3, 0), c2, s2), null != f3) for (a2 = f3.length; a2--; ) w(f3[a2]);
    c2 || (a2 = "value", "progress" === C2 && null == g2 ? u3.removeAttribute("value") : void 0 !== g2 && (g2 !== u3[a2] || "progress" === C2 && !g2 || "option" === C2 && g2 !== b2[a2]) && A(u3, a2, g2, b2[a2], r2), a2 = "checked", void 0 !== m && m !== u3[a2] && A(u3, a2, m, b2[a2], r2));
  }
  return u3;
}
function N(n2, u3, t2) {
  try {
    if ("function" == typeof n2) {
      var i3 = "function" == typeof n2.__u;
      i3 && n2.__u(), i3 && null == u3 || (n2.__u = n2(u3));
    } else n2.current = u3;
  } catch (n3) {
    l.__e(n3, t2);
  }
}
function V(n2, u3, t2) {
  var i3, o2;
  if (l.unmount && l.unmount(n2), (i3 = n2.ref) && (i3.current && i3.current !== n2.__e || N(i3, null, u3)), null != (i3 = n2.__c)) {
    if (i3.componentWillUnmount) try {
      i3.componentWillUnmount();
    } catch (n3) {
      l.__e(n3, u3);
    }
    i3.base = i3.__P = null;
  }
  if (i3 = n2.__k) for (o2 = 0; o2 < i3.length; o2++) i3[o2] && V(i3[o2], u3, t2 || "function" != typeof n2.type);
  t2 || w(n2.__e), n2.__c = n2.__ = n2.__e = n2.__d = void 0;
}
function q(n2, l2, u3) {
  return this.constructor(n2, u3);
}
function B(u3, t2, i3) {
  var o2, r2, f3, e2;
  l.__ && l.__(u3, t2), r2 = (o2 = "function" == typeof i3) ? null : i3 && i3.__k || t2.__k, f3 = [], e2 = [], O(t2, u3 = (!o2 && i3 || t2).__k = _(b, null, [u3]), r2 || h, h, t2.namespaceURI, !o2 && i3 ? [i3] : r2 ? null : t2.firstChild ? n.call(t2.childNodes) : null, f3, !o2 && i3 ? i3 : r2 ? r2.__e : t2.firstChild, o2, e2), j(f3, u3, e2);
}
n = v.slice, l = { __e: function(n2, l2, u3, t2) {
  for (var i3, o2, r2; l2 = l2.__; ) if ((i3 = l2.__c) && !i3.__) try {
    if ((o2 = i3.constructor) && null != o2.getDerivedStateFromError && (i3.setState(o2.getDerivedStateFromError(n2)), r2 = i3.__d), null != i3.componentDidCatch && (i3.componentDidCatch(n2, t2 || {}), r2 = i3.__d), r2) return i3.__E = i3;
  } catch (l3) {
    n2 = l3;
  }
  throw n2;
} }, u = 0, t = function(n2) {
  return null != n2 && null == n2.constructor;
}, k.prototype.setState = function(n2, l2) {
  var u3;
  u3 = null != this.__s && this.__s !== this.state ? this.__s : this.__s = d({}, this.state), "function" == typeof n2 && (n2 = n2(d({}, u3), this.props)), n2 && d(u3, n2), null != n2 && this.__v && (l2 && this._sb.push(l2), S(this));
}, k.prototype.forceUpdate = function(n2) {
  this.__v && (this.__e = true, n2 && this.__h.push(n2), S(this));
}, k.prototype.render = b, i = [], r = "function" == typeof Promise ? Promise.prototype.then.bind(Promise.resolve()) : setTimeout, f = function(n2, l2) {
  return n2.__v.__b - l2.__v.__b;
}, M.__r = 0, e = 0, c = F(false), s = F(true), a = 0;

// src/app-shell.html
var app_shell_default = '<header class="topbar" aria-label="Tau status bar">\n        <div class="topbar-group topbar-branding">\n          <button\n            id="mobile-nav-toggle"\n            class="icon-button mobile-only"\n            type="button"\n            aria-controls="session-nav"\n            aria-expanded="false"\n            aria-label="Open sessions drawer"\n          >\n            Sessions\n          </button>\n          <div class="brand-block">\n            <h1>Tau</h1>\n            <p id="status-stream" class="muted">Connecting\u2026</p>\n          </div>\n        </div>\n        <dl class="status-grid" aria-label="Current Tau status">\n          <div>\n            <dt>Session</dt>\n            <dd id="status-session">No session selected</dd>\n          </div>\n          <div>\n            <dt>Model</dt>\n            <dd id="status-model">Unset</dd>\n          </div>\n          <div>\n            <dt>Context</dt>\n            <dd id="status-context">No context loaded</dd>\n          </div>\n        </dl>\n        <div class="topbar-group topbar-dashboard-control">\n          <button\n            id="dashboard-toggle"\n            class="dashboard-toggle"\n            type="button"\n            aria-controls="session-dashboard"\n            aria-expanded="false"\n            title="Toggle dashboard (`)"\n          >\n            Dashboard <span id="dashboard-count" class="dashboard-count">0</span>\n          </button>\n        </div>\n        <div class="topbar-group topbar-actions">\n          <section\n            id="system-meters"\n            class="system-meters"\n            aria-label="System meters"\n            data-enabled="true"\n            data-collapsed="true"\n          >\n            <div class="meters-toolbar">\n              <output id="meters-summary" class="meters-summary" aria-live="polite">\n                Meters loading\u2026\n              </output>\n              <button\n                id="meters-collapse-button"\n                class="meter-control"\n                type="button"\n                aria-controls="meters-details"\n                aria-expanded="false"\n              >\n                Expand\n              </button>\n              <button\n                id="meters-visibility-button"\n                class="meter-control"\n                type="button"\n                aria-pressed="true"\n              >\n                Hide\n              </button>\n            </div>\n            <div id="meters-details" class="meters-details">\n              <figure class="meter-tile">\n                <figcaption>CPU <output id="meter-cpu-value">--</output></figcaption>\n                <svg id="meter-cpu-sparkline" role="img" aria-label="CPU history"></svg>\n              </figure>\n              <figure class="meter-tile">\n                <figcaption>RAM <output id="meter-ram-value">--</output></figcaption>\n                <svg id="meter-ram-sparkline" role="img" aria-label="RAM history"></svg>\n              </figure>\n              <figure class="meter-tile">\n                <figcaption>RSS <output id="meter-rss-value">--</output></figcaption>\n                <svg id="meter-rss-sparkline" role="img" aria-label="Tau RSS history"></svg>\n              </figure>\n              <figure class="meter-tile">\n                <figcaption>Swap <output id="meter-swap-value">--</output></figcaption>\n                <svg id="meter-swap-sparkline" role="img" aria-label="Swap history"></svg>\n              </figure>\n            </div>\n          </section>\n          <button\n            id="mobile-panel-toggle"\n            class="icon-button mobile-only"\n            type="button"\n            aria-controls="side-panel"\n            aria-expanded="false"\n            aria-label="Open workspace and settings drawer"\n          >\n            Panels\n          </button>\n        </div>\n      </header>\n\n      <section\n        id="session-dashboard"\n        class="session-dashboard"\n        aria-labelledby="dashboard-title"\n        data-open="false"\n        hidden\n      >\n        <div class="dashboard-shell">\n          <header class="dashboard-header">\n            <div>\n              <h2 id="dashboard-title">Session dashboard</h2>\n              <p class="muted small-text">\n                Live Tau sessions, queue state, context estimates, and current activity.\n              </p>\n            </div>\n            <button id="dashboard-close" class="icon-button" type="button">Close</button>\n          </header>\n          <div\n            id="dashboard-grid"\n            class="dashboard-grid"\n            role="list"\n            aria-live="polite"\n            aria-busy="false"\n          ></div>\n          <footer class="dashboard-footer">\n            <p id="dashboard-age" class="muted small-text">Not refreshed yet.</p>\n            <div class="dashboard-pagination" role="group" aria-label="Dashboard pages">\n              <button id="dashboard-previous" type="button">Previous</button>\n              <output id="dashboard-page">Page 1 of 1</output>\n              <button id="dashboard-next" type="button">Next</button>\n              <button id="dashboard-manage" type="button">All sessions</button>\n            </div>\n          </footer>\n        </div>\n      </section>\n\n      <div class="shell-layout">\n        <aside id="session-nav" class="panel panel-nav" aria-label="Session navigation">\n          <div class="panel-header sticky-header">\n            <div>\n              <h2>Sessions</h2>\n              <p class="muted">Persisted chats, archive, and restore.</p>\n            </div>\n            <button\n              id="close-nav-drawer"\n              class="icon-button mobile-only"\n              type="button"\n              aria-label="Close sessions drawer"\n            >\n              Close\n            </button>\n          </div>\n\n          <div class="button-row button-row-wrap" role="group" aria-label="Session actions">\n            <button id="new-session-button" type="button">New</button>\n            <button id="archive-session-button" type="button">Archive</button>\n            <button id="restore-session-button" type="button">Restore</button>\n          </div>\n\n          <div class="button-row" role="group" aria-label="Session list filter">\n            <button id="show-active-sessions" type="button" aria-pressed="true">Active</button>\n            <button id="show-archived-sessions" type="button" aria-pressed="false">\n              Archived\n            </button>\n          </div>\n\n          <p id="session-count" class="muted small-text">0 sessions</p>\n          <ul id="session-list" class="session-list" aria-label="Available sessions"></ul>\n        </aside>\n\n        <main id="timeline-main" class="panel panel-main" tabindex="-1">\n          <div class="panel-header sticky-header">\n            <div>\n              <h2>Timeline</h2>\n              <p id="timeline-meta" class="muted">Load a session to inspect persisted messages.</p>\n            </div>\n          </div>\n\n          <section class="branch-strip" aria-labelledby="branch-strip-title">\n            <div class="branch-strip-header">\n              <h3 id="branch-strip-title">Branches</h3>\n              <p class="muted small-text">Select the active leaf for restored playback.</p>\n            </div>\n            <div id="branch-list" class="branch-list"></div>\n          </section>\n\n          <section id="session-overview" class="session-overview" aria-label="Live session overview">\n            <div class="extension-slot" data-extension-slot="dashboard"></div>\n            <article class="overview-card" aria-labelledby="context-summary-title">\n              <div class="overview-card-header">\n                <div>\n                  <h3 id="context-summary-title">Context</h3>\n                  <p class="muted small-text">Session entry, message, and compaction summary.</p>\n                </div>\n              </div>\n              <dl id="context-summary" class="stats-list"></dl>\n            </article>\n\n            <article class="overview-card" aria-labelledby="usage-summary-title">\n              <div class="overview-card-header">\n                <div>\n                  <h3 id="usage-summary-title">Usage</h3>\n                  <p class="muted small-text">Durable token and cost records for this session.</p>\n                </div>\n              </div>\n              <dl id="usage-totals" class="stats-list"></dl>\n              <ol id="usage-records" class="compact-list" aria-live="polite"></ol>\n            </article>\n\n            <article class="overview-card" aria-labelledby="active-run-title">\n              <div class="overview-card-header">\n                <div>\n                  <h3 id="active-run-title">Active run</h3>\n                  <p id="active-run-note" class="muted small-text">\n                    Pending and running work for the selected session.\n                  </p>\n                </div>\n              </div>\n              <div id="active-run-card" aria-live="polite"></div>\n            </article>\n\n            <article class="overview-card" aria-labelledby="queue-panel-title">\n              <div class="overview-card-header">\n                <div>\n                  <h3 id="queue-panel-title">Queue</h3>\n                  <p class="muted small-text">Follow-up and steer messages waiting for dispatch.</p>\n                </div>\n              </div>\n              <form id="queue-form" class="stack-form">\n                <label for="queue-input">Queue follow-up</label>\n                <textarea\n                  id="queue-input"\n                  name="content"\n                  rows="3"\n                  placeholder="Add a follow-up message for this session."\n                ></textarea>\n                <div class="button-row button-row-wrap" role="group" aria-label="Queue actions">\n                  <button id="queue-submit-button" type="submit">Enqueue follow-up</button>\n                  <button id="dispatch-follow-up-button" type="button">Dispatch follow-up</button>\n                  <button id="dispatch-steer-button" type="button">Dispatch steer</button>\n                </div>\n                <p id="queue-help" class="muted small-text">\n                  Enter submits. Shift+Enter inserts a newline.\n                </p>\n              </form>\n              <ul id="queue-list" class="queue-list" aria-live="polite"></ul>\n            </article>\n          </section>\n\n          <div class="extension-slot" data-extension-slot="timeline_before"></div>\n          <ol id="timeline-list" class="timeline-list" aria-live="polite"></ol>\n          <div class="extension-slot" data-extension-slot="timeline_after"></div>\n        </main>\n\n        <aside id="side-panel" class="panel panel-side" aria-label="Workspace search and settings">\n          <div class="panel-header sticky-header">\n            <div>\n              <h2>Workspace</h2>\n              <p class="muted">Files, search, and Tau settings.</p>\n            </div>\n            <button\n              id="close-panel-drawer"\n              class="icon-button mobile-only"\n              type="button"\n              aria-label="Close workspace drawer"\n            >\n              Close\n            </button>\n          </div>\n\n          <div class="tabs" role="tablist" aria-label="Sidebar sections">\n            <button\n              id="tab-workspace"\n              class="tab-button"\n              type="button"\n              role="tab"\n              aria-controls="panel-workspace"\n              aria-selected="true"\n            >\n              Workspace\n            </button>\n            <button\n              id="tab-search"\n              class="tab-button"\n              type="button"\n              role="tab"\n              aria-controls="panel-search"\n              aria-selected="false"\n            >\n              Search\n            </button>\n            <button\n              id="tab-plan"\n              class="tab-button"\n              type="button"\n              role="tab"\n              aria-controls="panel-plan"\n              aria-selected="false"\n            >\n              Plan\n            </button>\n            <button\n              id="tab-settings"\n              class="tab-button"\n              type="button"\n              role="tab"\n              aria-controls="panel-settings"\n              aria-selected="false"\n            >\n              Settings\n            </button>\n          </div>\n\n          <section\n            id="panel-workspace"\n            class="tab-panel"\n            role="tabpanel"\n            aria-labelledby="tab-workspace"\n          >\n            <div class="toolbar-row">\n              <button id="workspace-up-button" type="button">Up</button>\n              <button id="workspace-reload-button" type="button">Reload</button>\n            </div>\n            <p id="workspace-path" class="muted small-text">.</p>\n            <div class="workspace-split">\n              <nav class="workspace-browser" aria-label="Workspace tree">\n                <ul id="workspace-list" class="workspace-list"></ul>\n              </nav>\n              <section class="workspace-editor-panel" aria-labelledby="workspace-editor-title">\n                <div class="workspace-editor-header">\n                  <h3 id="workspace-editor-title">Editor</h3>\n                  <p id="workspace-editor-path" class="muted small-text">No file selected</p>\n                </div>\n                <label class="sr-only" for="workspace-editor">Workspace file editor</label>\n                <textarea\n                  id="workspace-editor"\n                  spellcheck="false"\n                  aria-describedby="workspace-editor-note"\n                ></textarea>\n                <p id="workspace-editor-note" class="muted small-text">\n                  Local edits are not yet persisted through the web shell.\n                </p>\n                <section id="workspace-annotations" class="workspace-annotations" hidden>\n                  <h4>Annotations</h4>\n                  <ul id="workspace-annotation-list" class="workspace-annotation-list"></ul>\n                </section>\n                <section\n                  id="workspace-renderer"\n                  class="workspace-renderer"\n                  aria-label="Extension file preview"\n                  hidden\n                ></section>\n              </section>\n            </div>\n          </section>\n\n          <section\n            id="panel-search"\n            class="tab-panel"\n            role="tabpanel"\n            aria-labelledby="tab-search"\n            hidden\n          >\n            <form id="search-form" class="stack-form">\n              <label for="search-input">Search persisted content</label>\n              <div class="toolbar-row">\n                <input\n                  id="search-input"\n                  name="query"\n                  type="search"\n                  autocomplete="off"\n                  placeholder="Search messages and indexed content"\n                />\n                <button id="search-submit-button" type="submit">Search</button>\n              </div>\n              <p class="muted small-text">Shortcut: Ctrl/Cmd+K</p>\n            </form>\n            <ol\n              id="search-results"\n              class="search-results"\n              tabindex="0"\n              aria-label="Search results"\n              aria-live="polite"\n            ></ol>\n          </section>\n\n          <section\n            id="panel-plan"\n            class="tab-panel plan-panel"\n            role="tabpanel"\n            aria-labelledby="tab-plan"\n            hidden\n          >\n            <form id="plan-form" class="stack-form">\n              <div class="plan-editor-header">\n                <label for="plan-editor">Session plan</label>\n                <span id="plan-revision" class="muted small-text">Revision 0</span>\n              </div>\n              <textarea\n                id="plan-editor"\n                class="plan-editor"\n                spellcheck="true"\n                placeholder="- [ ] Add a concrete next step"\n                aria-describedby="plan-status"\n              ></textarea>\n              <p id="plan-status" class="muted small-text" aria-live="polite">\n                Select a session to edit its shared plan.\n              </p>\n              <div id="plan-conflict" class="plan-conflict" role="alert" hidden>\n                The plan changed elsewhere while you had local edits. Reload the server version or\n                save again after reviewing it.\n              </div>\n              <div class="button-row button-row-wrap">\n                <button id="plan-save-button" type="submit">Save plan</button>\n                <button id="plan-reload-button" type="button">Reload server plan</button>\n              </div>\n            </form>\n          </section>\n\n          <section\n            id="panel-settings"\n            class="tab-panel"\n            role="tabpanel"\n            aria-labelledby="tab-settings"\n            hidden\n          >\n            <form id="auth-form" class="stack-form">\n              <label for="auth-token">Bearer token</label>\n              <input id="auth-token" type="password" autocomplete="off" />\n              <div class="button-row button-row-wrap">\n                <button id="save-auth-button" type="submit">Save token</button>\n                <button id="clear-auth-button" type="button">Clear token</button>\n              </div>\n            </form>\n\n            <form id="model-form" class="stack-form">\n              <label for="provider-input">Provider</label>\n              <input id="provider-input" list="provider-options" autocomplete="off" />\n              <datalist id="provider-options"></datalist>\n\n              <label for="model-input">Model</label>\n              <input id="model-input" list="model-options" autocomplete="off" />\n              <datalist id="model-options"></datalist>\n\n              <div class="button-row button-row-wrap">\n                <button id="apply-model-button" type="submit">Apply to session</button>\n                <button id="refresh-button" type="button">Refresh shell</button>\n              </div>\n            </form>\n\n            <form id="thinking-form" class="stack-form">\n              <label for="thinking-level-select">Thinking level</label>\n              <div class="toolbar-row toolbar-row-wrap">\n                <select id="thinking-level-select" name="thinking_level"></select>\n                <button id="apply-thinking-button" type="submit">Apply thinking</button>\n              </div>\n              <p id="thinking-help" class="muted small-text">\n                Updates session thinking with optimistic concurrency checks.\n              </p>\n            </form>\n\n            <section aria-labelledby="settings-summary-title">\n              <h3 id="settings-summary-title">Runtime summary</h3>\n              <dl id="settings-summary" class="settings-summary"></dl>\n            </section>\n\n            <p id="streaming-note" class="muted small-text">\n              Live streaming, queue controls, and persisted timeline playback are rendered with safe\n              DOM updates only.\n            </p>\n            <div class="extension-slot" data-extension-slot="sidebar"></div>\n          </section>\n        </aside>\n      </div>\n\n      <footer class="composer-shell">\n        <div class="extension-slot" data-extension-slot="compose_above"></div>\n        <form id="compose-form" class="compose-form">\n          <section class="compose-toolbar" aria-label="Prompt controls">\n            <div class="compose-select-grid">\n              <div class="compose-control">\n                <label for="compose-provider-select">Provider</label>\n                <select id="compose-provider-select" name="provider_name"></select>\n              </div>\n              <div class="compose-control">\n                <label for="compose-model-select">Model</label>\n                <select id="compose-model-select" name="model"></select>\n              </div>\n              <div class="compose-control">\n                <label for="compose-thinking-select">Thinking</label>\n                <select id="compose-thinking-select" name="compose_thinking_level"></select>\n              </div>\n              <div class="compose-control">\n                <label for="compose-delivery-mode">Delivery</label>\n                <select id="compose-delivery-mode" name="delivery_mode">\n                  <option value="run">Run immediately</option>\n                  <option value="follow_up">Queue follow-up</option>\n                  <option value="steer">Queue steer</option>\n                </select>\n              </div>\n            </div>\n            <p id="compose-context-readout" class="muted small-text">\n              No session selected. Sending will create one.\n            </p>\n            <div class="compose-attachment-bar">\n              <button id="compose-attachment-button" type="button">Attach files</button>\n              <button id="compose-clear-attachments" type="button">Clear staged</button>\n              <input\n                id="compose-file-input"\n                class="sr-only"\n                type="file"\n                multiple\n                aria-label="Attach files"\n              />\n            </div>\n            <ul\n              id="compose-attachment-list"\n              class="compose-attachment-list"\n              aria-live="polite"\n              aria-label="Staged attachments"\n            ></ul>\n          </section>\n\n          <label for="compose-input">Send a prompt to Tau</label>\n          <div class="compose-editor-group">\n            <div class="compose-row">\n              <textarea\n                id="compose-input"\n                name="prompt"\n                rows="3"\n                autocomplete="off"\n                role="combobox"\n                aria-autocomplete="list"\n                aria-controls="compose-completion-listbox"\n                aria-describedby="compose-help compose-completion-status"\n                aria-expanded="false"\n                aria-haspopup="listbox"\n                placeholder="Select or create a session, then send a prompt."\n              ></textarea>\n              <button id="compose-submit" type="submit">Run</button>\n            </div>\n            <div id="compose-completion-popup" class="compose-completion-popup" hidden>\n              <p\n                id="compose-completion-status"\n                class="muted small-text"\n                aria-live="polite"\n              ></p>\n              <ul\n                id="compose-completion-listbox"\n                class="compose-completion-listbox"\n                role="listbox"\n                aria-label="Composer completions"\n              ></ul>\n            </div>\n          </div>\n\n          <div class="compose-status-row">\n            <p id="compose-help" class="muted small-text">Enter sends. Shift+Enter inserts a newline.</p>\n            <p id="app-status" class="small-text" aria-live="polite">Loading Tau shell\u2026</p>\n          </div>\n        </form>\n        <div class="extension-slot" data-extension-slot="compose_below"></div>\n      </footer>\n';

// node_modules/preact/jsx-runtime/dist/jsxRuntime.module.js
var f2 = 0;
var i2 = Array.isArray;
function u2(e2, t2, n2, o2, i3, u3) {
  t2 || (t2 = {});
  var a2, c2, l2 = t2;
  "ref" in t2 && (a2 = t2.ref, delete t2.ref);
  var p2 = { type: e2, props: l2, key: n2, ref: a2, __k: null, __: null, __b: 0, __e: null, __d: void 0, __c: null, constructor: void 0, __v: --f2, __i: -1, __u: 0, __source: i3, __self: u3 };
  if ("function" == typeof e2 && (a2 = e2.defaultProps)) for (c2 in a2) void 0 === l2[c2] && (l2[c2] = a2[c2]);
  return l.vnode && l.vnode(p2), p2;
}

// src/index.tsx
function TauShell() {
  return /* @__PURE__ */ u2(b, { children: [
    /* @__PURE__ */ u2("a", { className: "skip-link", href: "#timeline-main", children: "Skip to timeline" }),
    /* @__PURE__ */ u2("div", { className: "app-shell", dangerouslySetInnerHTML: { __html: app_shell_default } }),
    /* @__PURE__ */ u2(
      "button",
      {
        id: "drawer-backdrop",
        className: "drawer-backdrop",
        type: "button",
        hidden: true,
        "aria-label": "Close open drawers"
      }
    ),
    /* @__PURE__ */ u2("noscript", { children: /* @__PURE__ */ u2("p", { className: "noscript-banner", children: "Tau Web Shell requires JavaScript to load persisted sessions." }) })
  ] });
}
var mount = document.getElementById("app");
if (!mount) throw new Error("Missing #app root element");
B(/* @__PURE__ */ u2(TauShell, {}), mount);
