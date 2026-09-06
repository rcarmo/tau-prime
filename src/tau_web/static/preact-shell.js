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
function d(n2, l3) {
  for (var u6 in l3) n2[u6] = l3[u6];
  return n2;
}
function w(n2) {
  n2 && n2.parentNode && n2.parentNode.removeChild(n2);
}
function _(l3, u6, t3) {
  var i4, o3, r3, f4 = {};
  for (r3 in u6) "key" == r3 ? i4 = u6[r3] : "ref" == r3 ? o3 = u6[r3] : f4[r3] = u6[r3];
  if (arguments.length > 2 && (f4.children = arguments.length > 3 ? n.call(arguments, 2) : t3), "function" == typeof l3 && null != l3.defaultProps) for (r3 in l3.defaultProps) void 0 === f4[r3] && (f4[r3] = l3.defaultProps[r3]);
  return g(l3, f4, i4, o3, null);
}
function g(n2, t3, i4, o3, r3) {
  var f4 = { type: n2, props: t3, key: i4, ref: o3, __k: null, __: null, __b: 0, __e: null, __d: void 0, __c: null, constructor: void 0, __v: null == r3 ? ++u : r3, __i: -1, __u: 0 };
  return null == r3 && null != l.vnode && l.vnode(f4), f4;
}
function b(n2) {
  return n2.children;
}
function k(n2, l3) {
  this.props = n2, this.context = l3;
}
function x(n2, l3) {
  if (null == l3) return n2.__ ? x(n2.__, n2.__i + 1) : null;
  for (var u6; l3 < n2.__k.length; l3++) if (null != (u6 = n2.__k[l3]) && null != u6.__e) return u6.__e;
  return "function" == typeof n2.type ? x(n2) : null;
}
function C(n2) {
  var l3, u6;
  if (null != (n2 = n2.__) && null != n2.__c) {
    for (n2.__e = n2.__c.base = null, l3 = 0; l3 < n2.__k.length; l3++) if (null != (u6 = n2.__k[l3]) && null != u6.__e) {
      n2.__e = n2.__c.base = u6.__e;
      break;
    }
    return C(n2);
  }
}
function S(n2) {
  (!n2.__d && (n2.__d = true) && i.push(n2) && !M.__r++ || o !== l.debounceRendering) && ((o = l.debounceRendering) || r)(M);
}
function M() {
  var n2, u6, t3, o3, r3, e3, c3, s3;
  for (i.sort(f); n2 = i.shift(); ) n2.__d && (u6 = i.length, o3 = void 0, e3 = (r3 = (t3 = n2).__v).__e, c3 = [], s3 = [], t3.__P && ((o3 = d({}, r3)).__v = r3.__v + 1, l.vnode && l.vnode(o3), O(t3.__P, o3, r3, t3.__n, t3.__P.namespaceURI, 32 & r3.__u ? [e3] : null, c3, null == e3 ? x(r3) : e3, !!(32 & r3.__u), s3), o3.__v = r3.__v, o3.__.__k[o3.__i] = o3, j(c3, o3, s3), o3.__e != e3 && C(o3)), i.length > u6 && i.sort(f));
  M.__r = 0;
}
function P(n2, l3, u6, t3, i4, o3, r3, f4, e3, c3, s3) {
  var a3, p3, y4, d3, w4, _4 = t3 && t3.__k || v, g3 = l3.length;
  for (u6.__d = e3, $(u6, l3, _4), e3 = u6.__d, a3 = 0; a3 < g3; a3++) null != (y4 = u6.__k[a3]) && (p3 = -1 === y4.__i ? h : _4[y4.__i] || h, y4.__i = a3, O(n2, y4, p3, i4, o3, r3, f4, e3, c3, s3), d3 = y4.__e, y4.ref && p3.ref != y4.ref && (p3.ref && N(p3.ref, null, y4), s3.push(y4.ref, y4.__c || d3, y4)), null == w4 && null != d3 && (w4 = d3), 65536 & y4.__u || p3.__k === y4.__k ? e3 = I(y4, e3, n2) : "function" == typeof y4.type && void 0 !== y4.__d ? e3 = y4.__d : d3 && (e3 = d3.nextSibling), y4.__d = void 0, y4.__u &= -196609);
  u6.__d = e3, u6.__e = w4;
}
function $(n2, l3, u6) {
  var t3, i4, o3, r3, f4, e3 = l3.length, c3 = u6.length, s3 = c3, a3 = 0;
  for (n2.__k = [], t3 = 0; t3 < e3; t3++) null != (i4 = l3[t3]) && "boolean" != typeof i4 && "function" != typeof i4 ? (r3 = t3 + a3, (i4 = n2.__k[t3] = "string" == typeof i4 || "number" == typeof i4 || "bigint" == typeof i4 || i4.constructor == String ? g(null, i4, null, null, null) : y(i4) ? g(b, { children: i4 }, null, null, null) : void 0 === i4.constructor && i4.__b > 0 ? g(i4.type, i4.props, i4.key, i4.ref ? i4.ref : null, i4.__v) : i4).__ = n2, i4.__b = n2.__b + 1, o3 = null, -1 !== (f4 = i4.__i = L(i4, u6, r3, s3)) && (s3--, (o3 = u6[f4]) && (o3.__u |= 131072)), null == o3 || null === o3.__v ? (-1 == f4 && a3--, "function" != typeof i4.type && (i4.__u |= 65536)) : f4 !== r3 && (f4 == r3 - 1 ? a3-- : f4 == r3 + 1 ? a3++ : (f4 > r3 ? a3-- : a3++, i4.__u |= 65536))) : i4 = n2.__k[t3] = null;
  if (s3) for (t3 = 0; t3 < c3; t3++) null != (o3 = u6[t3]) && 0 == (131072 & o3.__u) && (o3.__e == n2.__d && (n2.__d = x(o3)), V(o3, o3));
}
function I(n2, l3, u6) {
  var t3, i4;
  if ("function" == typeof n2.type) {
    for (t3 = n2.__k, i4 = 0; t3 && i4 < t3.length; i4++) t3[i4] && (t3[i4].__ = n2, l3 = I(t3[i4], l3, u6));
    return l3;
  }
  n2.__e != l3 && (l3 && n2.type && !u6.contains(l3) && (l3 = x(n2)), u6.insertBefore(n2.__e, l3 || null), l3 = n2.__e);
  do {
    l3 = l3 && l3.nextSibling;
  } while (null != l3 && 8 === l3.nodeType);
  return l3;
}
function L(n2, l3, u6, t3) {
  var i4 = n2.key, o3 = n2.type, r3 = u6 - 1, f4 = u6 + 1, e3 = l3[u6];
  if (null === e3 || e3 && i4 == e3.key && o3 === e3.type && 0 == (131072 & e3.__u)) return u6;
  if (t3 > (null != e3 && 0 == (131072 & e3.__u) ? 1 : 0)) for (; r3 >= 0 || f4 < l3.length; ) {
    if (r3 >= 0) {
      if ((e3 = l3[r3]) && 0 == (131072 & e3.__u) && i4 == e3.key && o3 === e3.type) return r3;
      r3--;
    }
    if (f4 < l3.length) {
      if ((e3 = l3[f4]) && 0 == (131072 & e3.__u) && i4 == e3.key && o3 === e3.type) return f4;
      f4++;
    }
  }
  return -1;
}
function T(n2, l3, u6) {
  "-" === l3[0] ? n2.setProperty(l3, null == u6 ? "" : u6) : n2[l3] = null == u6 ? "" : "number" != typeof u6 || p.test(l3) ? u6 : u6 + "px";
}
function A(n2, l3, u6, t3, i4) {
  var o3;
  n: if ("style" === l3) if ("string" == typeof u6) n2.style.cssText = u6;
  else {
    if ("string" == typeof t3 && (n2.style.cssText = t3 = ""), t3) for (l3 in t3) u6 && l3 in u6 || T(n2.style, l3, "");
    if (u6) for (l3 in u6) t3 && u6[l3] === t3[l3] || T(n2.style, l3, u6[l3]);
  }
  else if ("o" === l3[0] && "n" === l3[1]) o3 = l3 !== (l3 = l3.replace(/(PointerCapture)$|Capture$/i, "$1")), l3 = l3.toLowerCase() in n2 || "onFocusOut" === l3 || "onFocusIn" === l3 ? l3.toLowerCase().slice(2) : l3.slice(2), n2.l || (n2.l = {}), n2.l[l3 + o3] = u6, u6 ? t3 ? u6.u = t3.u : (u6.u = e, n2.addEventListener(l3, o3 ? s : c, o3)) : n2.removeEventListener(l3, o3 ? s : c, o3);
  else {
    if ("http://www.w3.org/2000/svg" == i4) l3 = l3.replace(/xlink(H|:h)/, "h").replace(/sName$/, "s");
    else if ("width" != l3 && "height" != l3 && "href" != l3 && "list" != l3 && "form" != l3 && "tabIndex" != l3 && "download" != l3 && "rowSpan" != l3 && "colSpan" != l3 && "role" != l3 && "popover" != l3 && l3 in n2) try {
      n2[l3] = null == u6 ? "" : u6;
      break n;
    } catch (n3) {
    }
    "function" == typeof u6 || (null == u6 || false === u6 && "-" !== l3[4] ? n2.removeAttribute(l3) : n2.setAttribute(l3, "popover" == l3 && 1 == u6 ? "" : u6));
  }
}
function F(n2) {
  return function(u6) {
    if (this.l) {
      var t3 = this.l[u6.type + n2];
      if (null == u6.t) u6.t = e++;
      else if (u6.t < t3.u) return;
      return t3(l.event ? l.event(u6) : u6);
    }
  };
}
function O(n2, u6, t3, i4, o3, r3, f4, e3, c3, s3) {
  var a3, h3, v4, p3, w4, _4, g3, m3, x3, C4, S2, M3, $3, I3, H2, L3, T4 = u6.type;
  if (void 0 !== u6.constructor) return null;
  128 & t3.__u && (c3 = !!(32 & t3.__u), r3 = [e3 = u6.__e = t3.__e]), (a3 = l.__b) && a3(u6);
  n: if ("function" == typeof T4) try {
    if (m3 = u6.props, x3 = "prototype" in T4 && T4.prototype.render, C4 = (a3 = T4.contextType) && i4[a3.__c], S2 = a3 ? C4 ? C4.props.value : a3.__ : i4, t3.__c ? g3 = (h3 = u6.__c = t3.__c).__ = h3.__E : (x3 ? u6.__c = h3 = new T4(m3, S2) : (u6.__c = h3 = new k(m3, S2), h3.constructor = T4, h3.render = q), C4 && C4.sub(h3), h3.props = m3, h3.state || (h3.state = {}), h3.context = S2, h3.__n = i4, v4 = h3.__d = true, h3.__h = [], h3._sb = []), x3 && null == h3.__s && (h3.__s = h3.state), x3 && null != T4.getDerivedStateFromProps && (h3.__s == h3.state && (h3.__s = d({}, h3.__s)), d(h3.__s, T4.getDerivedStateFromProps(m3, h3.__s))), p3 = h3.props, w4 = h3.state, h3.__v = u6, v4) x3 && null == T4.getDerivedStateFromProps && null != h3.componentWillMount && h3.componentWillMount(), x3 && null != h3.componentDidMount && h3.__h.push(h3.componentDidMount);
    else {
      if (x3 && null == T4.getDerivedStateFromProps && m3 !== p3 && null != h3.componentWillReceiveProps && h3.componentWillReceiveProps(m3, S2), !h3.__e && (null != h3.shouldComponentUpdate && false === h3.shouldComponentUpdate(m3, h3.__s, S2) || u6.__v === t3.__v)) {
        for (u6.__v !== t3.__v && (h3.props = m3, h3.state = h3.__s, h3.__d = false), u6.__e = t3.__e, u6.__k = t3.__k, u6.__k.some(function(n3) {
          n3 && (n3.__ = u6);
        }), M3 = 0; M3 < h3._sb.length; M3++) h3.__h.push(h3._sb[M3]);
        h3._sb = [], h3.__h.length && f4.push(h3);
        break n;
      }
      null != h3.componentWillUpdate && h3.componentWillUpdate(m3, h3.__s, S2), x3 && null != h3.componentDidUpdate && h3.__h.push(function() {
        h3.componentDidUpdate(p3, w4, _4);
      });
    }
    if (h3.context = S2, h3.props = m3, h3.__P = n2, h3.__e = false, $3 = l.__r, I3 = 0, x3) {
      for (h3.state = h3.__s, h3.__d = false, $3 && $3(u6), a3 = h3.render(h3.props, h3.state, h3.context), H2 = 0; H2 < h3._sb.length; H2++) h3.__h.push(h3._sb[H2]);
      h3._sb = [];
    } else do {
      h3.__d = false, $3 && $3(u6), a3 = h3.render(h3.props, h3.state, h3.context), h3.state = h3.__s;
    } while (h3.__d && ++I3 < 25);
    h3.state = h3.__s, null != h3.getChildContext && (i4 = d(d({}, i4), h3.getChildContext())), x3 && !v4 && null != h3.getSnapshotBeforeUpdate && (_4 = h3.getSnapshotBeforeUpdate(p3, w4)), P(n2, y(L3 = null != a3 && a3.type === b && null == a3.key ? a3.props.children : a3) ? L3 : [L3], u6, t3, i4, o3, r3, f4, e3, c3, s3), h3.base = u6.__e, u6.__u &= -161, h3.__h.length && f4.push(h3), g3 && (h3.__E = h3.__ = null);
  } catch (n3) {
    if (u6.__v = null, c3 || null != r3) {
      for (u6.__u |= c3 ? 160 : 128; e3 && 8 === e3.nodeType && e3.nextSibling; ) e3 = e3.nextSibling;
      r3[r3.indexOf(e3)] = null, u6.__e = e3;
    } else u6.__e = t3.__e, u6.__k = t3.__k;
    l.__e(n3, u6, t3);
  }
  else null == r3 && u6.__v === t3.__v ? (u6.__k = t3.__k, u6.__e = t3.__e) : u6.__e = z(t3.__e, u6, t3, i4, o3, r3, f4, c3, s3);
  (a3 = l.diffed) && a3(u6);
}
function j(n2, u6, t3) {
  u6.__d = void 0;
  for (var i4 = 0; i4 < t3.length; i4++) N(t3[i4], t3[++i4], t3[++i4]);
  l.__c && l.__c(u6, n2), n2.some(function(u7) {
    try {
      n2 = u7.__h, u7.__h = [], n2.some(function(n3) {
        n3.call(u7);
      });
    } catch (n3) {
      l.__e(n3, u7.__v);
    }
  });
}
function z(u6, t3, i4, o3, r3, f4, e3, c3, s3) {
  var a3, v4, p3, d3, _4, g3, m3, b3 = i4.props, k4 = t3.props, C4 = t3.type;
  if ("svg" === C4 ? r3 = "http://www.w3.org/2000/svg" : "math" === C4 ? r3 = "http://www.w3.org/1998/Math/MathML" : r3 || (r3 = "http://www.w3.org/1999/xhtml"), null != f4) {
    for (a3 = 0; a3 < f4.length; a3++) if ((_4 = f4[a3]) && "setAttribute" in _4 == !!C4 && (C4 ? _4.localName === C4 : 3 === _4.nodeType)) {
      u6 = _4, f4[a3] = null;
      break;
    }
  }
  if (null == u6) {
    if (null === C4) return document.createTextNode(k4);
    u6 = document.createElementNS(r3, C4, k4.is && k4), c3 && (l.__m && l.__m(t3, f4), c3 = false), f4 = null;
  }
  if (null === C4) b3 === k4 || c3 && u6.data === k4 || (u6.data = k4);
  else {
    if (f4 = f4 && n.call(u6.childNodes), b3 = i4.props || h, !c3 && null != f4) for (b3 = {}, a3 = 0; a3 < u6.attributes.length; a3++) b3[(_4 = u6.attributes[a3]).name] = _4.value;
    for (a3 in b3) if (_4 = b3[a3], "children" == a3) ;
    else if ("dangerouslySetInnerHTML" == a3) p3 = _4;
    else if (!(a3 in k4)) {
      if ("value" == a3 && "defaultValue" in k4 || "checked" == a3 && "defaultChecked" in k4) continue;
      A(u6, a3, null, _4, r3);
    }
    for (a3 in k4) _4 = k4[a3], "children" == a3 ? d3 = _4 : "dangerouslySetInnerHTML" == a3 ? v4 = _4 : "value" == a3 ? g3 = _4 : "checked" == a3 ? m3 = _4 : c3 && "function" != typeof _4 || b3[a3] === _4 || A(u6, a3, _4, b3[a3], r3);
    if (v4) c3 || p3 && (v4.__html === p3.__html || v4.__html === u6.innerHTML) || (u6.innerHTML = v4.__html), t3.__k = [];
    else if (p3 && (u6.innerHTML = ""), P(u6, y(d3) ? d3 : [d3], t3, i4, o3, "foreignObject" === C4 ? "http://www.w3.org/1999/xhtml" : r3, f4, e3, f4 ? f4[0] : i4.__k && x(i4, 0), c3, s3), null != f4) for (a3 = f4.length; a3--; ) w(f4[a3]);
    c3 || (a3 = "value", "progress" === C4 && null == g3 ? u6.removeAttribute("value") : void 0 !== g3 && (g3 !== u6[a3] || "progress" === C4 && !g3 || "option" === C4 && g3 !== b3[a3]) && A(u6, a3, g3, b3[a3], r3), a3 = "checked", void 0 !== m3 && m3 !== u6[a3] && A(u6, a3, m3, b3[a3], r3));
  }
  return u6;
}
function N(n2, u6, t3) {
  try {
    if ("function" == typeof n2) {
      var i4 = "function" == typeof n2.__u;
      i4 && n2.__u(), i4 && null == u6 || (n2.__u = n2(u6));
    } else n2.current = u6;
  } catch (n3) {
    l.__e(n3, t3);
  }
}
function V(n2, u6, t3) {
  var i4, o3;
  if (l.unmount && l.unmount(n2), (i4 = n2.ref) && (i4.current && i4.current !== n2.__e || N(i4, null, u6)), null != (i4 = n2.__c)) {
    if (i4.componentWillUnmount) try {
      i4.componentWillUnmount();
    } catch (n3) {
      l.__e(n3, u6);
    }
    i4.base = i4.__P = null;
  }
  if (i4 = n2.__k) for (o3 = 0; o3 < i4.length; o3++) i4[o3] && V(i4[o3], u6, t3 || "function" != typeof n2.type);
  t3 || w(n2.__e), n2.__c = n2.__ = n2.__e = n2.__d = void 0;
}
function q(n2, l3, u6) {
  return this.constructor(n2, u6);
}
function B(u6, t3, i4) {
  var o3, r3, f4, e3;
  l.__ && l.__(u6, t3), r3 = (o3 = "function" == typeof i4) ? null : i4 && i4.__k || t3.__k, f4 = [], e3 = [], O(t3, u6 = (!o3 && i4 || t3).__k = _(b, null, [u6]), r3 || h, h, t3.namespaceURI, !o3 && i4 ? [i4] : r3 ? null : t3.firstChild ? n.call(t3.childNodes) : null, f4, !o3 && i4 ? i4 : r3 ? r3.__e : t3.firstChild, o3, e3), j(f4, u6, e3);
}
n = v.slice, l = { __e: function(n2, l3, u6, t3) {
  for (var i4, o3, r3; l3 = l3.__; ) if ((i4 = l3.__c) && !i4.__) try {
    if ((o3 = i4.constructor) && null != o3.getDerivedStateFromError && (i4.setState(o3.getDerivedStateFromError(n2)), r3 = i4.__d), null != i4.componentDidCatch && (i4.componentDidCatch(n2, t3 || {}), r3 = i4.__d), r3) return i4.__E = i4;
  } catch (l4) {
    n2 = l4;
  }
  throw n2;
} }, u = 0, t = function(n2) {
  return null != n2 && null == n2.constructor;
}, k.prototype.setState = function(n2, l3) {
  var u6;
  u6 = null != this.__s && this.__s !== this.state ? this.__s : this.__s = d({}, this.state), "function" == typeof n2 && (n2 = n2(d({}, u6), this.props)), n2 && d(u6, n2), null != n2 && this.__v && (l3 && this._sb.push(l3), S(this));
}, k.prototype.forceUpdate = function(n2) {
  this.__v && (this.__e = true, n2 && this.__h.push(n2), S(this));
}, k.prototype.render = b, i = [], r = "function" == typeof Promise ? Promise.prototype.then.bind(Promise.resolve()) : setTimeout, f = function(n2, l3) {
  return n2.__v.__b - l3.__v.__b;
}, M.__r = 0, e = 0, c = F(false), s = F(true), a = 0;

// src/theme/theme.ts
var DARK_THEME = {
  bg: "#1e1e2e",
  bgSidebar: "#181825",
  bgTerminal: "#11111b",
  bgStatus: "#181825",
  border: "#313244",
  text: "#cdd6f4",
  textMuted: "#9399b2",
  accent: "#89b4fa",
  success: "#a6e3a1",
  error: "#f38ba8",
  handleHover: "#89b4fa",
  handle: "#313244",
  inputBg: "#11111b",
  inputBorder: "#45475a"
};
var LIGHT_THEME = {
  bg: "#f3f3f3",
  bgSidebar: "#e8e8e8",
  bgTerminal: "#1e1e2e",
  bgStatus: "#dcdcdc",
  border: "#c8c8c8",
  text: "#1a1a1a",
  textMuted: "#4a4a4a",
  accent: "#0078d4",
  success: "#16a34a",
  error: "#d32f2f",
  handleHover: "#0078d4",
  handle: "#c8c8c8",
  inputBg: "#ffffff",
  inputBorder: "#c8c8c8"
};
function getSystemTheme() {
  if (typeof window === "undefined" || typeof window.matchMedia !== "function") {
    return "dark";
  }
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

// src/theme/applyTheme.ts
function installSystemTheme() {
  const apply2 = () => {
    const mode = getSystemTheme();
    const theme = mode === "dark" ? DARK_THEME : LIGHT_THEME;
    const root = document.documentElement;
    root.classList.remove("light", "dark");
    root.classList.add(mode);
    const variables = {
      "--bg": theme.bg,
      "--bg-sidebar": theme.bgSidebar,
      "--bg-terminal": theme.bgTerminal,
      "--bg-status": theme.bgStatus,
      "--border": theme.border,
      "--text": theme.text,
      "--text-muted": theme.textMuted,
      "--accent": theme.accent,
      "--success": theme.success,
      "--error": theme.error,
      "--handle-hover": theme.handleHover,
      "--handle": theme.handle,
      "--input-bg": theme.inputBg,
      "--input-border": theme.inputBorder
    };
    for (const [key, value] of Object.entries(variables)) root.style.setProperty(key, value);
  };
  apply2();
  const media = window.matchMedia("(prefers-color-scheme: dark)");
  media.addEventListener("change", apply2);
  return () => media.removeEventListener("change", apply2);
}

// node_modules/preact/hooks/dist/hooks.module.js
var t2;
var r2;
var u2;
var i2;
var o2 = 0;
var f2 = [];
var c2 = l;
var e2 = c2.__b;
var a2 = c2.__r;
var v2 = c2.diffed;
var l2 = c2.__c;
var m = c2.unmount;
var s2 = c2.__;
function d2(n2, t3) {
  c2.__h && c2.__h(r2, n2, o2 || t3), o2 = 0;
  var u6 = r2.__H || (r2.__H = { __: [], __h: [] });
  return n2 >= u6.__.length && u6.__.push({}), u6.__[n2];
}
function h2(n2) {
  return o2 = 1, p2(D, n2);
}
function p2(n2, u6, i4) {
  var o3 = d2(t2++, 2);
  if (o3.t = n2, !o3.__c && (o3.__ = [i4 ? i4(u6) : D(void 0, u6), function(n3) {
    var t3 = o3.__N ? o3.__N[0] : o3.__[0], r3 = o3.t(t3, n3);
    t3 !== r3 && (o3.__N = [r3, o3.__[1]], o3.__c.setState({}));
  }], o3.__c = r2, !r2.u)) {
    var f4 = function(n3, t3, r3) {
      if (!o3.__c.__H) return true;
      var u7 = o3.__c.__H.__.filter(function(n4) {
        return !!n4.__c;
      });
      if (u7.every(function(n4) {
        return !n4.__N;
      })) return !c3 || c3.call(this, n3, t3, r3);
      var i5 = false;
      return u7.forEach(function(n4) {
        if (n4.__N) {
          var t4 = n4.__[0];
          n4.__ = n4.__N, n4.__N = void 0, t4 !== n4.__[0] && (i5 = true);
        }
      }), !(!i5 && o3.__c.props === n3) && (!c3 || c3.call(this, n3, t3, r3));
    };
    r2.u = true;
    var c3 = r2.shouldComponentUpdate, e3 = r2.componentWillUpdate;
    r2.componentWillUpdate = function(n3, t3, r3) {
      if (this.__e) {
        var u7 = c3;
        c3 = void 0, f4(n3, t3, r3), c3 = u7;
      }
      e3 && e3.call(this, n3, t3, r3);
    }, r2.shouldComponentUpdate = f4;
  }
  return o3.__N || o3.__;
}
function y2(n2, u6) {
  var i4 = d2(t2++, 3);
  !c2.__s && C2(i4.__H, u6) && (i4.__ = n2, i4.i = u6, r2.__H.__h.push(i4));
}
function _2(n2, u6) {
  var i4 = d2(t2++, 4);
  !c2.__s && C2(i4.__H, u6) && (i4.__ = n2, i4.i = u6, r2.__h.push(i4));
}
function A2(n2) {
  return o2 = 5, T2(function() {
    return { current: n2 };
  }, []);
}
function T2(n2, r3) {
  var u6 = d2(t2++, 7);
  return C2(u6.__H, r3) && (u6.__ = n2(), u6.__H = r3, u6.__h = n2), u6.__;
}
function q2(n2, t3) {
  return o2 = 8, T2(function() {
    return n2;
  }, t3);
}
function j2() {
  for (var n2; n2 = f2.shift(); ) if (n2.__P && n2.__H) try {
    n2.__H.__h.forEach(z2), n2.__H.__h.forEach(B2), n2.__H.__h = [];
  } catch (t3) {
    n2.__H.__h = [], c2.__e(t3, n2.__v);
  }
}
c2.__b = function(n2) {
  r2 = null, e2 && e2(n2);
}, c2.__ = function(n2, t3) {
  n2 && t3.__k && t3.__k.__m && (n2.__m = t3.__k.__m), s2 && s2(n2, t3);
}, c2.__r = function(n2) {
  a2 && a2(n2), t2 = 0;
  var i4 = (r2 = n2.__c).__H;
  i4 && (u2 === r2 ? (i4.__h = [], r2.__h = [], i4.__.forEach(function(n3) {
    n3.__N && (n3.__ = n3.__N), n3.i = n3.__N = void 0;
  })) : (i4.__h.forEach(z2), i4.__h.forEach(B2), i4.__h = [], t2 = 0)), u2 = r2;
}, c2.diffed = function(n2) {
  v2 && v2(n2);
  var t3 = n2.__c;
  t3 && t3.__H && (t3.__H.__h.length && (1 !== f2.push(t3) && i2 === c2.requestAnimationFrame || ((i2 = c2.requestAnimationFrame) || w2)(j2)), t3.__H.__.forEach(function(n3) {
    n3.i && (n3.__H = n3.i), n3.i = void 0;
  })), u2 = r2 = null;
}, c2.__c = function(n2, t3) {
  t3.some(function(n3) {
    try {
      n3.__h.forEach(z2), n3.__h = n3.__h.filter(function(n4) {
        return !n4.__ || B2(n4);
      });
    } catch (r3) {
      t3.some(function(n4) {
        n4.__h && (n4.__h = []);
      }), t3 = [], c2.__e(r3, n3.__v);
    }
  }), l2 && l2(n2, t3);
}, c2.unmount = function(n2) {
  m && m(n2);
  var t3, r3 = n2.__c;
  r3 && r3.__H && (r3.__H.__.forEach(function(n3) {
    try {
      z2(n3);
    } catch (n4) {
      t3 = n4;
    }
  }), r3.__H = void 0, t3 && c2.__e(t3, r3.__v));
};
var k2 = "function" == typeof requestAnimationFrame;
function w2(n2) {
  var t3, r3 = function() {
    clearTimeout(u6), k2 && cancelAnimationFrame(t3), setTimeout(n2);
  }, u6 = setTimeout(r3, 100);
  k2 && (t3 = requestAnimationFrame(r3));
}
function z2(n2) {
  var t3 = r2, u6 = n2.__c;
  "function" == typeof u6 && (n2.__c = void 0, u6()), r2 = t3;
}
function B2(n2) {
  var t3 = r2;
  n2.__c = n2.__(), r2 = t3;
}
function C2(n2, t3) {
  return !n2 || n2.length !== t3.length || t3.some(function(t4, r3) {
    return t4 !== n2[r3];
  });
}
function D(n2, t3) {
  return "function" == typeof t3 ? t3(n2) : t3;
}

// node_modules/preact/jsx-runtime/dist/jsxRuntime.module.js
var f3 = 0;
var i3 = Array.isArray;
function u3(e3, t3, n2, o3, i4, u6) {
  t3 || (t3 = {});
  var a3, c3, l3 = t3;
  "ref" in t3 && (a3 = t3.ref, delete t3.ref);
  var p3 = { type: e3, props: l3, key: n2, ref: a3, __k: null, __: null, __b: 0, __e: null, __d: void 0, __c: null, constructor: void 0, __v: --f3, __i: -1, __u: 0, __source: i4, __self: u6 };
  if ("function" == typeof e3 && (a3 = e3.defaultProps)) for (c3 in a3) void 0 === l3[c3] && (l3[c3] = a3[c3]);
  return l.vnode && l.vnode(p3), p3;
}

// src/components/ActivityBar.tsx
var PANELS = [
  { id: "sessions", label: "Sessions", icon: "codicon-comment-discussion" },
  { id: "workspace", label: "Workspace", icon: "codicon-files" },
  { id: "search", label: "Search", icon: "codicon-search" },
  { id: "plan", label: "Plan", icon: "codicon-checklist" },
  { id: "dashboard", label: "Dashboard", icon: "codicon-dashboard" },
  { id: "settings", label: "Settings", icon: "codicon-settings-gear", alignBottom: true }
];
function ActivityBar({ activePanel, onPanelChange, onDashboard }) {
  return /* @__PURE__ */ u3("nav", { className: "activity-bar", "aria-label": "Activity bar", children: PANELS.map((panel) => {
    const active = panel.id === activePanel;
    return /* @__PURE__ */ u3(
      "button",
      {
        type: "button",
        className: `activity-bar__button ${active ? "is-active" : ""} ${panel.alignBottom ? "is-bottom" : ""}`,
        title: panel.label,
        "aria-label": panel.label,
        "aria-pressed": active,
        onClick: () => panel.id === "dashboard" ? onDashboard() : onPanelChange(panel.id),
        children: /* @__PURE__ */ u3("i", { className: `codicon ${panel.icon} icon--size-24 activity-bar__icon`, "aria-hidden": "true" })
      },
      panel.id
    );
  }) });
}

// src/components/TabBar.tsx
function TabBar() {
  return /* @__PURE__ */ u3("div", { className: "tab-bar", role: "tablist", "aria-label": "Central pane tabs", children: /* @__PURE__ */ u3(
    "button",
    {
      role: "tab",
      type: "button",
      "aria-selected": true,
      className: "tab-bar__tab tab-bar__tab--active",
      children: /* @__PURE__ */ u3("span", { className: "tab-bar__tab__label", children: "Chat" })
    }
  ) });
}

// src/components/SystemStats.tsx
var formatPercent = (value) => Number.isFinite(value) ? `${Math.round(value)}%` : "--";
var formatBytes = (value) => {
  if (!Number.isFinite(value)) return "--";
  const units = ["B", "KB", "MB", "GB", "TB"];
  let amount = value;
  let unit = 0;
  while (amount >= 1024 && unit < units.length - 1) {
    amount /= 1024;
    unit += 1;
  }
  return `${amount.toFixed(unit > 1 && amount < 10 ? 1 : 0)} ${units[unit]}`;
};
var severity = (value) => value != null && value > 85 ? "error" : value != null && value >= 60 ? "warning" : "normal";
var points = (series, maximum) => {
  const values = (series ?? []).filter(Number.isFinite);
  if (values.length < 2) return "";
  const max = maximum ?? Math.max(...values, 1);
  return values.map((value, index) => `${index / (values.length - 1) * 48},${12 - Math.min(1, Math.max(0, value / max)) * 12}`).join(" ");
};
function Metric({ id: id2, label, icon, value, series, maximum }) {
  const numeric = series?.at(-1);
  const level = id2 === "swap" && numeric && numeric > 0 ? "warning" : severity(numeric);
  return /* @__PURE__ */ u3("span", { className: "sys-stats__metric", title: `${label} usage`, children: [
    /* @__PURE__ */ u3("i", { className: `sys-stats__icon codicon ${icon}`, "aria-hidden": "true" }),
    /* @__PURE__ */ u3("span", { className: "sys-stats__label", children: label }),
    /* @__PURE__ */ u3("output", { id: `meter-${id2}-value`, className: `sys-stats__value${level === "normal" ? "" : ` sys-stats__value--${level}`}`, children: value }),
    /* @__PURE__ */ u3("svg", { id: `meter-${id2}-sparkline`, className: "sys-stats__sparkline", viewBox: "0 0 48 12", role: "img", "aria-label": `${label === "RSS" ? "Tau RSS" : label} history`, children: points(series, maximum) && /* @__PURE__ */ u3("polyline", { className: "meter-sparkline", points: points(series, maximum) }) })
  ] });
}
function SystemStats({ enabled, collapsed, onToggleEnabled, onToggleCollapsed }) {
  const [state, setState] = h2({ enabled, collapsed, meters: null });
  _2(() => {
    const update = (event) => setState(event.detail);
    window.addEventListener("tau:meters-render", update);
    return () => window.removeEventListener("tau:meters-render", update);
  }, []);
  const meters = state.meters;
  const cpu = formatPercent(meters?.cpu_percent), ram = formatPercent(meters?.ram_percent);
  const rss = formatBytes(meters?.process_rss_bytes), swap = formatPercent(meters?.swap_percent);
  const summary = !state.enabled ? "Meters hidden" : !meters ? "Meters unavailable" : `CPU ${cpu} \xB7 RAM ${ram} \xB7 RSS ${rss} \xB7 Swap ${swap}`;
  return /* @__PURE__ */ u3("span", { id: "system-meters", className: "sys-stats-bar", "data-enabled": String(state.enabled), "data-collapsed": String(state.collapsed), children: [
    /* @__PURE__ */ u3("span", { className: "sys-stats-bar__inline", children: /* @__PURE__ */ u3("span", { id: "meters-details", className: "sys-stats", children: [
      /* @__PURE__ */ u3(Metric, { id: "cpu", label: "CPU", icon: "codicon-pulse", value: cpu, series: meters?.cpu_series, maximum: 100 }),
      /* @__PURE__ */ u3(Metric, { id: "ram", label: "RAM", icon: "codicon-circuit-board", value: ram, series: meters?.ram_series, maximum: 100 }),
      /* @__PURE__ */ u3(Metric, { id: "rss", label: "RSS", icon: "codicon-package", value: rss, series: meters?.process_rss_series_bytes, maximum: null }),
      /* @__PURE__ */ u3(Metric, { id: "swap", label: "SWP", icon: "codicon-arrow-swap", value: swap, series: meters?.swap_series, maximum: 100 })
    ] }) }),
    /* @__PURE__ */ u3("output", { id: "meters-summary", className: "sys-stats-bar__compact", "aria-live": "polite", children: summary }),
    /* @__PURE__ */ u3("button", { id: "meters-collapse-button", className: "status-bar__terminal-btn", type: "button", "aria-controls": "meters-details", "aria-expanded": !state.collapsed, title: state.collapsed ? "Expand system meters" : "Compact system meters", onClick: onToggleCollapsed, children: /* @__PURE__ */ u3("i", { className: `codicon ${state.collapsed ? "codicon-chevron-up" : "codicon-chevron-down"}`, "aria-hidden": "true" }) }),
    /* @__PURE__ */ u3("button", { id: "meters-visibility-button", className: "status-bar__terminal-btn", type: "button", "aria-pressed": state.enabled, title: state.enabled ? "Hide system meters" : "Show system meters", onClick: onToggleEnabled, children: /* @__PURE__ */ u3("i", { className: `codicon ${state.enabled ? "codicon-eye" : "codicon-eye-closed"}`, "aria-hidden": "true" }) })
  ] });
}

// src/components/StatusBar.tsx
function StatusBar({ dashboardOpen, metersEnabled, metersCollapsed, onOpenSessions, onToggleDashboard, onToggleMetersEnabled, onToggleMetersCollapsed }) {
  const [model, setModel] = h2("");
  y2(() => {
    const receive = (event) => setModel(event.detail.model);
    window.addEventListener("tau:status-model", receive);
    return () => window.removeEventListener("tau:status-model", receive);
  }, []);
  return /* @__PURE__ */ u3("footer", { className: "app-layout__status-bar", role: "banner", "aria-label": "Tau status bar", children: [
    /* @__PURE__ */ u3("span", { className: "status-bar__conn", children: [
      /* @__PURE__ */ u3("span", { className: "status-bar__conn-dot status-bar__conn-dot--disconnected", "aria-hidden": "true" }),
      /* @__PURE__ */ u3("span", { id: "status-stream", className: "status-bar__conn-text", children: "Connecting\u2026" })
    ] }),
    /* @__PURE__ */ u3("span", { className: "session-pill-wrap", children: /* @__PURE__ */ u3("button", { className: "session-pill", type: "button", title: "Open sessions", onClick: onOpenSessions, children: [
      /* @__PURE__ */ u3("span", { className: "session-pill__dot session-pill__dot--current", "aria-hidden": "true" }),
      /* @__PURE__ */ u3("span", { id: "status-session", className: "session-pill__label", children: "No session selected" })
    ] }) }),
    /* @__PURE__ */ u3("span", { className: "model-badge-wrapper", children: [
      /* @__PURE__ */ u3("span", { id: "status-model", className: `model-badge${model ? "" : " model-badge--empty"}`, children: model ? /* @__PURE__ */ u3("span", { className: "model-badge__name-wrapper", children: [
        /* @__PURE__ */ u3("span", { className: "model-badge__provider", children: model.includes("/") ? model.slice(0, model.lastIndexOf("/") + 1) : "" }),
        /* @__PURE__ */ u3("span", { className: "model-badge__name", children: model.split("/").pop() })
      ] }) : /* @__PURE__ */ u3("span", { className: "model-badge__empty", children: "Unset" }) }),
      /* @__PURE__ */ u3("span", { id: "status-context", className: "usage-badge", children: "No context loaded" })
    ] }),
    /* @__PURE__ */ u3("span", { className: "status-bar__right", children: [
      /* @__PURE__ */ u3(SystemStats, { enabled: metersEnabled, collapsed: metersCollapsed, onToggleEnabled: onToggleMetersEnabled, onToggleCollapsed: onToggleMetersCollapsed }),
      /* @__PURE__ */ u3("button", { id: "dashboard-toggle", className: "status-bar__terminal-btn", type: "button", "aria-controls": "session-dashboard", "aria-expanded": dashboardOpen, title: "Toggle dashboard (`)", onClick: onToggleDashboard, children: [
        /* @__PURE__ */ u3("i", { className: "codicon codicon-dashboard", "aria-hidden": "true" }),
        /* @__PURE__ */ u3("span", { id: "dashboard-count", children: "0" })
      ] })
    ] })
  ] });
}

// src/components/Composer.tsx
function Composer() {
  const [completion, setCompletion] = h2({ open: false, index: 0, items: [] });
  const [attachments, setAttachments] = h2({ items: [], busy: false });
  const [adapterOptions, setAdapterOptions] = h2({ providers: [], models: [], thinking: [] });
  _2(() => {
    const update = (event) => setCompletion(event.detail);
    const updateAttachments = (event) => setAttachments(event.detail);
    const updateModels = (event) => setAdapterOptions((current) => ({ ...current, ...event.detail }));
    const updateThinking = (event) => setAdapterOptions((current) => ({ ...current, thinking: event.detail.items }));
    window.addEventListener("tau:completion-render", update);
    window.addEventListener("tau:attachments-render", updateAttachments);
    window.addEventListener("tau:model-options-render", updateModels);
    window.addEventListener("tau:thinking-options-render", updateThinking);
    return () => {
      window.removeEventListener("tau:completion-render", update);
      window.removeEventListener("tau:attachments-render", updateAttachments);
      window.removeEventListener("tau:model-options-render", updateModels);
      window.removeEventListener("tau:thinking-options-render", updateThinking);
    };
  }, []);
  const activeDescendant = completion.open ? `compose-completion-option-${completion.index}` : void 0;
  const choose = (index) => window.dispatchEvent(new CustomEvent("tau:completion-select", { detail: { index } }));
  return /* @__PURE__ */ u3(b, { children: [
    /* @__PURE__ */ u3("div", { className: "extension-slot", "data-extension-slot": "compose_above" }),
    /* @__PURE__ */ u3("form", { id: "compose-form", className: "chat__compose", children: [
      /* @__PURE__ */ u3("div", { className: "chat__compose-container", children: [
        /* @__PURE__ */ u3("div", { className: "chat__toolbar", "aria-label": "Prompt controls", children: [
          /* @__PURE__ */ u3("button", { id: "compose-attachment-button", className: "chat__toolbar-btn", type: "button", "aria-label": "Attach file", title: "Attach file", children: /* @__PURE__ */ u3("i", { className: "codicon codicon-attach", "aria-hidden": "true" }) }),
          /* @__PURE__ */ u3("input", { id: "compose-file-input", type: "file", multiple: true, hidden: true, "aria-label": "Attach files" }),
          /* @__PURE__ */ u3("label", { className: "thinking-badge-wrapper", title: "Message delivery", children: [
            /* @__PURE__ */ u3("span", { className: "sr-only", children: "Delivery" }),
            /* @__PURE__ */ u3("select", { id: "compose-delivery-mode", className: "settings-panel__select", name: "delivery_mode", "aria-label": "Message delivery", children: [
              /* @__PURE__ */ u3("option", { value: "run", children: "Run" }),
              /* @__PURE__ */ u3("option", { value: "follow_up", children: "Follow-up" }),
              /* @__PURE__ */ u3("option", { value: "steer", children: "Steer" })
            ] })
          ] }),
          /* @__PURE__ */ u3("span", { id: "compose-context-readout", className: "usage-badge", children: "No session selected. Sending will create one." })
        ] }),
        /* @__PURE__ */ u3("div", { className: "sr-only", "aria-hidden": "true", children: [
          /* @__PURE__ */ u3("select", { id: "compose-provider-select", name: "provider_name", tabIndex: -1, "aria-label": "Provider adapter", children: adapterOptions.providers.map((item) => /* @__PURE__ */ u3("option", { value: item.value, children: item.label }, item.value)) }),
          /* @__PURE__ */ u3("select", { id: "compose-model-select", name: "model", tabIndex: -1, "aria-label": "Model adapter", children: adapterOptions.models.map((item) => /* @__PURE__ */ u3("option", { value: item.value, children: item.label }, item.value)) }),
          /* @__PURE__ */ u3("select", { id: "compose-thinking-select", name: "compose_thinking_level", tabIndex: -1, "aria-label": "Thinking adapter", children: adapterOptions.thinking.map((item) => /* @__PURE__ */ u3("option", { value: item.value, children: item.label }, item.value)) })
        ] }),
        /* @__PURE__ */ u3("div", { id: "compose-attachment-list", className: "chat__attachments", role: "region", "aria-live": "polite", "aria-label": "Staged attachments", children: attachments.items.map((attachment) => /* @__PURE__ */ u3("span", { className: "chat__attachment-pill", children: [
          /* @__PURE__ */ u3("span", { className: "chat__attachment-name", children: attachment.label }),
          /* @__PURE__ */ u3("button", { className: "chat__attachment-remove", type: "button", "aria-label": `Remove attachment ${attachment.filename}`, disabled: attachments.busy, onClick: () => window.dispatchEvent(new CustomEvent("tau:attachment-remove", { detail: { mediaId: attachment.mediaId } })), children: "\u2715" })
        ] }, attachment.mediaId)) }),
        /* @__PURE__ */ u3("button", { id: "compose-clear-attachments", className: "chat__attachment-clear", type: "button", "aria-label": "Clear all attachments", hidden: !attachments.items.length, disabled: !attachments.items.length || attachments.busy, onClick: () => window.dispatchEvent(new CustomEvent("tau:attachments-clear")), children: "Clear all" }),
        /* @__PURE__ */ u3("label", { className: "sr-only", htmlFor: "compose-input", children: "Send a prompt to Tau" }),
        /* @__PURE__ */ u3(
          "textarea",
          {
            id: "compose-input",
            className: "chat__input",
            name: "prompt",
            rows: 3,
            autoComplete: "off",
            role: "combobox",
            "aria-autocomplete": "list",
            "aria-controls": "compose-completion-listbox",
            "aria-describedby": "compose-help compose-completion-status",
            "aria-expanded": completion.open,
            "aria-activedescendant": activeDescendant,
            "aria-haspopup": "listbox",
            placeholder: "Type a message..."
          }
        ),
        /* @__PURE__ */ u3("div", { id: "compose-completion-popup", className: "command-palette compose-completion-popup", hidden: !completion.open, children: [
          /* @__PURE__ */ u3("p", { id: "compose-completion-status", className: "command-palette__step-hint", "aria-live": "polite", children: completion.open ? `${completion.items.length} completion${completion.items.length === 1 ? "" : "s"} available.` : "" }),
          /* @__PURE__ */ u3("ul", { id: "compose-completion-listbox", className: "command-palette__results", role: "listbox", "aria-label": "Composer completions", children: completion.items.map((item, index) => /* @__PURE__ */ u3(
            "li",
            {
              id: `compose-completion-option-${index}`,
              className: `command-palette__row${index === completion.index ? " is-active" : ""}`,
              role: "option",
              "aria-selected": index === completion.index,
              "data-active": String(index === completion.index),
              onMouseDown: (event) => event.preventDefault(),
              onClick: () => choose(index),
              children: [
                /* @__PURE__ */ u3("strong", { className: "command-palette__label", children: item.label }),
                /* @__PURE__ */ u3("p", { className: "command-palette__description", children: item.detail })
              ]
            }
          )) })
        ] })
      ] }),
      /* @__PURE__ */ u3("button", { id: "compose-submit", className: "chat__send-btn", type: "submit", "aria-label": "Run", title: "Send (Enter)", children: /* @__PURE__ */ u3("svg", { viewBox: "0 0 24 24", width: "22", height: "22", fill: "currentColor", "aria-hidden": "true", children: /* @__PURE__ */ u3("path", { d: "M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" }) }) })
    ] }),
    /* @__PURE__ */ u3("div", { className: "sr-only", children: [
      /* @__PURE__ */ u3("p", { id: "compose-help", children: "Enter sends. Shift+Enter inserts a newline." }),
      /* @__PURE__ */ u3("p", { id: "app-status", "aria-live": "polite", children: "Loading Tau shell\u2026" })
    ] }),
    /* @__PURE__ */ u3("div", { className: "extension-slot", "data-extension-slot": "compose_below" })
  ] });
}

// src/components/Dashboard.tsx
var EMPTY_DASHBOARD = {
  sessions: [],
  page: 1,
  totalPages: 1,
  generatedAt: null,
  loading: false,
  selectedSessionId: null
};
var stringOrEmpty = (value) => typeof value === "string" ? value : "";
var numberOrZero = (value) => typeof value === "number" && Number.isFinite(value) ? value : 0;
function shortId(value) {
  const text2 = stringOrEmpty(value);
  return text2 ? text2.slice(0, 8) : "unknown";
}
function sentenceCase(value) {
  const text2 = stringOrEmpty(value).replace(/_/g, " ").trim();
  return text2 ? `${text2.charAt(0).toUpperCase()}${text2.slice(1)}` : "Unknown";
}
function sessionLabel(session) {
  const title = stringOrEmpty(session.title).trim();
  if (title) return title;
  const agentName = stringOrEmpty(session.agent_name).trim();
  if (agentName) return agentName;
  return shortId(session.session_id);
}
function buildSessionUrl(sessionId) {
  const url = new URL(window.location.href);
  if (sessionId) url.searchParams.set("session_id", sessionId);
  else url.searchParams.delete("session_id");
  return `${url.pathname}${url.search}${url.hash}`;
}
function dashboardPreviewKindLabel(value) {
  switch (value) {
    case "draft":
      return "Draft";
    case "thinking":
      return "Thinking";
    case "tool":
      return "Tool";
    case "summary":
      return "Summary";
    default:
      return "Preview";
  }
}
function dashboardActivityLabel(session) {
  return sentenceCase(stringOrEmpty(session.activity_state) || "idle");
}
function formatDashboardContextPercent(session) {
  const value = typeof session.context_percent === "number" && Number.isFinite(session.context_percent) ? session.context_percent : 0;
  return Math.max(0, Math.min(100, Math.round(value)));
}
function formatDashboardContext(session) {
  const used = numberOrZero(session.context_used_tokens).toLocaleString();
  const windowTokens = numberOrZero(session.context_window_tokens).toLocaleString();
  return `${used} / ${windowTokens} \xB7 ${formatDashboardContextPercent(session)}%`;
}
function relativeTimeText(value, now) {
  const date = new Date(value ?? "");
  if (Number.isNaN(date.valueOf())) return "just now";
  const elapsedSeconds = Math.max(0, Math.round((now - date.valueOf()) / 1e3));
  if (elapsedSeconds < 5) return "just now";
  if (elapsedSeconds < 60) return `${elapsedSeconds}s ago`;
  const elapsedMinutes = Math.round(elapsedSeconds / 60);
  if (elapsedMinutes < 60) return `${elapsedMinutes}m ago`;
  const elapsedHours = Math.round(elapsedMinutes / 60);
  if (elapsedHours < 24) return `${elapsedHours}h ago`;
  return `${Math.round(elapsedHours / 24)}d ago`;
}
function Dashboard({ open, onClose }) {
  const [view, setView] = h2(EMPTY_DASHBOARD);
  const [now, setNow] = h2(() => Date.now());
  _2(() => {
    const update = (event) => {
      const detail = event.detail;
      if (!detail) return;
      setView({
        sessions: Array.isArray(detail.sessions) ? detail.sessions : [],
        page: Number.isInteger(detail.page) && detail.page > 0 ? detail.page : 1,
        totalPages: Number.isInteger(detail.totalPages) && detail.totalPages > 0 ? detail.totalPages : 1,
        generatedAt: stringOrEmpty(detail.generatedAt) || null,
        loading: Boolean(detail.loading),
        selectedSessionId: stringOrEmpty(detail.selectedSessionId) || null
      });
    };
    window.addEventListener("tau:dashboard-render", update);
    return () => window.removeEventListener("tau:dashboard-render", update);
  }, []);
  y2(() => {
    if (!open) return;
    setNow(Date.now());
    const timer = window.setInterval(() => setNow(Date.now()), 1e3);
    return () => window.clearInterval(timer);
  }, [open, view.generatedAt, view.sessions]);
  const dashboardAge = !view.generatedAt ? view.loading ? "Refreshing dashboard\u2026" : "Not refreshed yet." : view.loading ? `Refreshing\u2026 last updated ${relativeTimeText(view.generatedAt, now)}.` : `Updated ${relativeTimeText(view.generatedAt, now)}.`;
  const selectSession = (sessionId) => {
    window.dispatchEvent(new CustomEvent("tau:session-select", { detail: { sessionId } }));
  };
  return /* @__PURE__ */ u3(
    "div",
    {
      id: "session-dashboard",
      className: "modal-dialog__backdrop",
      "data-open": String(open),
      hidden: !open,
      onMouseDown: (event) => {
        if (event.target === event.currentTarget) onClose();
      },
      children: /* @__PURE__ */ u3(
        "section",
        {
          className: "modal-dialog session-dashboard__dialog",
          role: "dialog",
          "aria-modal": "true",
          "aria-labelledby": "dashboard-title",
          onMouseDown: (event) => event.stopPropagation(),
          children: [
            /* @__PURE__ */ u3("header", { className: "session-dashboard__header", children: [
              /* @__PURE__ */ u3("div", { children: [
                /* @__PURE__ */ u3("h2", { id: "dashboard-title", className: "modal-dialog__title", children: "Session dashboard" }),
                /* @__PURE__ */ u3("p", { className: "modal-dialog__description", children: "Live Tau sessions, queue state, context estimates, and current activity." })
              ] }),
              /* @__PURE__ */ u3("button", { id: "dashboard-close", className: "modal-dialog__btn", type: "button", onClick: onClose, children: "Close" })
            ] }),
            /* @__PURE__ */ u3("div", { id: "dashboard-grid", className: "session-dashboard__grid", role: "list", "aria-live": "polite", "aria-busy": view.loading, children: [
              !view.sessions.length && /* @__PURE__ */ u3("p", { className: "dashboard-empty", children: view.loading ? "Loading dashboard sessions\u2026" : "No active sessions." }),
              view.sessions.map((session) => {
                const sessionId = stringOrEmpty(session.session_id);
                const selected = sessionId !== "" && sessionId === view.selectedSessionId;
                return /* @__PURE__ */ u3("article", { className: "dashboard-tile", "data-selected": String(selected), role: "listitem", children: /* @__PURE__ */ u3(
                  "a",
                  {
                    href: buildSessionUrl(sessionId),
                    className: "dashboard-tile-button",
                    "aria-current": selected ? "page" : "false",
                    title: "Open this session. Ctrl-click or Cmd-click opens it in a new tab.",
                    onClick: (event) => {
                      if (!sessionId || event.metaKey || event.ctrlKey) return;
                      event.preventDefault();
                      selectSession(sessionId);
                    },
                    children: [
                      /* @__PURE__ */ u3("div", { className: "dashboard-tile-header", children: [
                        /* @__PURE__ */ u3("p", { className: "dashboard-agent", children: sessionLabel(session) }),
                        /* @__PURE__ */ u3("span", { className: "dashboard-state", "data-state": stringOrEmpty(session.activity_state) || "idle", "data-error": String(Boolean(session.has_error)), children: dashboardActivityLabel(session) })
                      ] }),
                      /* @__PURE__ */ u3("p", { className: "dashboard-identity", children: [session.agent_name ? `@${session.agent_name}` : null, shortId(session.session_id)].filter(Boolean).join(" \xB7 ") }),
                      /* @__PURE__ */ u3("p", { className: "dashboard-workspace", children: stringOrEmpty(session.workspace) || "Workspace unavailable" }),
                      /* @__PURE__ */ u3("p", { className: "dashboard-model", children: stringOrEmpty(session.model) || "Model unavailable" }),
                      /* @__PURE__ */ u3("p", { className: "dashboard-preview-kind", children: dashboardPreviewKindLabel(session.preview_kind) }),
                      /* @__PURE__ */ u3("p", { className: "dashboard-preview", children: stringOrEmpty(session.preview) || "No assistant summary yet." }),
                      /* @__PURE__ */ u3("div", { className: "dashboard-indicators", children: [
                        /* @__PURE__ */ u3("span", { children: `Queue ${numberOrZero(session.queue_count)}` }),
                        /* @__PURE__ */ u3("div", { className: "dashboard-context", children: [
                          /* @__PURE__ */ u3("span", { children: `Context ${formatDashboardContext(session)}` }),
                          /* @__PURE__ */ u3("span", { className: "dashboard-context-track", children: /* @__PURE__ */ u3("span", { className: "dashboard-context-fill", style: { width: `${formatDashboardContextPercent(session)}%` } }) })
                        ] }),
                        session.has_error && /* @__PURE__ */ u3("span", { className: "dashboard-error", children: "Error" }),
                        /* @__PURE__ */ u3("p", { className: "dashboard-tile-age", children: session.last_activity ? `Activity ${relativeTimeText(session.last_activity, now)}` : "Activity unknown" })
                      ] })
                    ]
                  }
                ) }, sessionId || `${sessionLabel(session)}-${stringOrEmpty(session.last_activity)}`);
              })
            ] }),
            /* @__PURE__ */ u3("footer", { className: "session-dashboard__footer", children: [
              /* @__PURE__ */ u3("p", { id: "dashboard-age", className: "modal-dialog__description", children: dashboardAge }),
              /* @__PURE__ */ u3("div", { className: "modal-dialog__actions", role: "group", "aria-label": "Dashboard pages", children: [
                /* @__PURE__ */ u3("button", { id: "dashboard-previous", className: "modal-dialog__btn", type: "button", disabled: view.loading || view.page <= 1, onClick: () => window.dispatchEvent(new CustomEvent("tau:dashboard-page", { detail: { delta: -1 } })), children: "Previous" }),
                /* @__PURE__ */ u3("output", { id: "dashboard-page", children: [
                  "Page ",
                  view.page,
                  " of ",
                  view.totalPages
                ] }),
                /* @__PURE__ */ u3("button", { id: "dashboard-next", className: "modal-dialog__btn", type: "button", disabled: view.loading || view.page >= view.totalPages, onClick: () => window.dispatchEvent(new CustomEvent("tau:dashboard-page", { detail: { delta: 1 } })), children: "Next" }),
                /* @__PURE__ */ u3("button", { id: "dashboard-manage", className: "modal-dialog__btn modal-dialog__btn--primary", type: "button", onClick: () => window.dispatchEvent(new CustomEvent("tau:dashboard-manage")), children: "All sessions" })
              ] })
            ] })
          ]
        }
      )
    }
  );
}

// src/components/PlanPanel.tsx
var INITIAL = {
  draft: "",
  revision: 0,
  dirty: false,
  disabled: true,
  reloadDisabled: true,
  conflict: false,
  status: "Select a session to edit its shared plan."
};
function PlanPanel({ hidden }) {
  const [view, setView] = h2(INITIAL);
  _2(() => {
    const update = (event) => {
      const detail = event.detail;
      if (detail) setView(detail);
    };
    window.addEventListener("tau:plan-render", update);
    return () => window.removeEventListener("tau:plan-render", update);
  }, []);
  return /* @__PURE__ */ u3("section", { id: "panel-plan", className: "tasks-panel", "aria-labelledby": "tab-plan", hidden, children: [
    /* @__PURE__ */ u3("div", { className: "tasks-panel__tabs", role: "tablist", "aria-label": "Plan views", children: /* @__PURE__ */ u3("button", { className: "tasks-panel__tab tasks-panel__tab--active", type: "button", role: "tab", "aria-selected": "true", children: "Plan" }) }),
    /* @__PURE__ */ u3("div", { className: "tasks-panel__tasks", children: /* @__PURE__ */ u3("form", { id: "plan-form", className: "tasks-panel__card", children: [
      /* @__PURE__ */ u3("div", { className: "tasks-panel__card-header", children: [
        /* @__PURE__ */ u3("span", { className: "tasks-panel__card-id", children: "Session plan" }),
        /* @__PURE__ */ u3("span", { id: "plan-revision", className: "tasks-panel__badge tasks-panel__badge--kind", children: [
          "Revision ",
          view.revision
        ] })
      ] }),
      /* @__PURE__ */ u3("label", { className: "tasks-panel__card-label", htmlFor: "plan-editor", children: "Shared checklist" }),
      /* @__PURE__ */ u3("textarea", { id: "plan-editor", className: "plan-editor tasks-panel__card-mono", spellcheck: true, placeholder: "- [ ] Add a concrete next step", "aria-describedby": "plan-status", value: view.draft, disabled: view.disabled }),
      /* @__PURE__ */ u3("p", { id: "plan-status", className: "tasks-panel__card-muted", "aria-live": "polite", children: view.status }),
      /* @__PURE__ */ u3("div", { id: "plan-conflict", className: "tasks-panel__sessions-error tasks-panel__sessions-error--inline", role: "alert", hidden: !view.conflict, children: "The plan changed elsewhere. Reload the server version or save again after reviewing it." }),
      /* @__PURE__ */ u3("div", { className: "tasks-panel__card-actions", children: [
        /* @__PURE__ */ u3("button", { id: "plan-save-button", type: "submit", disabled: view.disabled || !view.dirty, children: "Save plan" }),
        /* @__PURE__ */ u3("button", { id: "plan-reload-button", type: "button", disabled: view.reloadDisabled, children: "Reload" })
      ] })
    ] }) })
  ] });
}

// src/components/SessionList.tsx
function SessionList({ filter, onSelectFilter }) {
  const [items, setItems] = h2([]);
  _2(() => {
    const update = (event) => setItems(event.detail.items);
    window.addEventListener("tau:sessions-render", update);
    return () => window.removeEventListener("tau:sessions-render", update);
  }, []);
  const select = (sessionId) => window.dispatchEvent(new CustomEvent("tau:session-select", { detail: { sessionId } }));
  return /* @__PURE__ */ u3(b, { children: [
    /* @__PURE__ */ u3("div", { className: "sessions-panel__filters", role: "group", "aria-label": "Session list filter", children: [
      /* @__PURE__ */ u3("button", { id: "show-active-sessions", className: "settings-panel__provider-btn", type: "button", "aria-pressed": filter === "active", onClick: () => onSelectFilter("active"), children: "Active" }),
      /* @__PURE__ */ u3("button", { id: "show-archived-sessions", className: "settings-panel__provider-btn", type: "button", "aria-pressed": filter === "archived", onClick: () => onSelectFilter("archived"), children: "Archived" }),
      /* @__PURE__ */ u3("span", { id: "session-count", className: "sessions-panel__count", children: [
        items.length,
        " session",
        items.length === 1 ? "" : "s"
      ] })
    ] }),
    /* @__PURE__ */ u3("ul", { id: "session-list", className: "sessions-panel__list", "aria-label": "Available sessions", children: [
      !items.length && /* @__PURE__ */ u3("li", { className: "sessions-panel__item sessions-panel__placeholder", children: "No sessions available." }),
      items.map((session) => /* @__PURE__ */ u3("li", { className: "sessions-panel__item", children: /* @__PURE__ */ u3("button", { type: "button", className: "sessions-panel__session settings-panel__provider-btn", "data-active": String(session.active), onClick: () => select(session.sessionId), children: /* @__PURE__ */ u3("div", { className: "sessions-panel__session-body", children: [
        /* @__PURE__ */ u3("strong", { className: "sessions-panel__session-title", children: session.title }),
        /* @__PURE__ */ u3("span", { className: "sessions-panel__session-meta", children: session.meta })
      ] }) }) }, session.sessionId))
    ] })
  ] });
}

// src/components/SearchResults.tsx
function SearchResults() {
  const [items, setItems] = h2([]);
  _2(() => {
    const update = (event) => setItems(event.detail.items);
    window.addEventListener("tau:search-render", update);
    return () => window.removeEventListener("tau:search-render", update);
  }, []);
  return /* @__PURE__ */ u3("ol", { id: "search-results", className: "search-panel__results", tabIndex: 0, "aria-label": "Search results", "aria-live": "polite", children: [
    !items.length && /* @__PURE__ */ u3("li", { children: "Search results will appear here." }),
    items.map((result, index) => /* @__PURE__ */ u3("li", { className: "search-panel__item", children: /* @__PURE__ */ u3("article", { children: [
      /* @__PURE__ */ u3("div", { className: "search-panel__item-header", children: [
        /* @__PURE__ */ u3("strong", { className: "search-panel__item-type", children: [
          result.entityType,
          " \xB7 ",
          result.entityId
        ] }),
        /* @__PURE__ */ u3("span", { className: "search-panel__item-time", children: result.meta })
      ] }),
      /* @__PURE__ */ u3("span", { className: "search-panel__item-text", children: result.text }),
      result.sessionId && /* @__PURE__ */ u3("button", { type: "button", onClick: () => window.dispatchEvent(new CustomEvent("tau:search-open-session", { detail: { sessionId: result.sessionId } })), children: "Open session" })
    ] }) }, `${result.entityType}-${result.entityId}-${index}`))
  ] });
}

// src/components/WorkspacePanel.tsx
var empty = { path: ".", filePath: null, content: "", entries: [], annotations: [] };
function WorkspacePanel({ hidden }) {
  const [view, setView] = h2(empty);
  _2(() => {
    const update = (event) => setView(event.detail);
    window.addEventListener("tau:workspace-render", update);
    return () => window.removeEventListener("tau:workspace-render", update);
  }, []);
  const describedBy = view.annotations.length ? "workspace-editor-note workspace-annotations" : "workspace-editor-note";
  return /* @__PURE__ */ u3("section", { id: "panel-workspace", className: "workspace", "aria-labelledby": "tab-workspace", hidden, children: [
    /* @__PURE__ */ u3("div", { className: "workspace__pane-top", children: [
      /* @__PURE__ */ u3("div", { className: "workspace__section-header workspace__section-header--padded", children: [
        /* @__PURE__ */ u3("span", { children: "Files" }),
        /* @__PURE__ */ u3("div", { className: "workspace__files-toolbar", children: [
          /* @__PURE__ */ u3("button", { id: "workspace-up-button", className: "workspace__files-toolbar-icon codicon codicon-arrow-up", type: "button", title: "Parent directory", "aria-label": "Parent directory" }),
          /* @__PURE__ */ u3("button", { id: "workspace-reload-button", className: "workspace__files-toolbar-icon codicon codicon-refresh", type: "button", title: "Refresh", "aria-label": "Refresh workspace" })
        ] })
      ] }),
      /* @__PURE__ */ u3("p", { id: "workspace-path", className: "workspace__current-path", children: view.path }),
      /* @__PURE__ */ u3("div", { id: "workspace-list", className: "file-tree", role: "tree", "aria-label": "Workspace tree", children: [
        !view.entries.length && /* @__PURE__ */ u3("div", { children: "No workspace entries available." }),
        view.entries.map((entry) => /* @__PURE__ */ u3("div", { children: /* @__PURE__ */ u3("button", { type: "button", className: "file-tree__item", role: "treeitem", disabled: entry.kind !== "directory" && entry.kind !== "file", onClick: () => window.dispatchEvent(new CustomEvent("tau:workspace-open", { detail: { entry } })), children: [
          /* @__PURE__ */ u3("span", { className: `file-tree__icon codicon codicon-${entry.kind === "directory" ? "folder" : "file"}`, "aria-hidden": "true" }),
          /* @__PURE__ */ u3("span", { className: "file-tree__name", children: entry.name }),
          /* @__PURE__ */ u3("span", { className: "file-tree__meta", children: entry.kind })
        ] }) }, `${entry.kind}:${entry.path ?? entry.name}`))
      ] })
    ] }),
    /* @__PURE__ */ u3("div", { className: "workspace__drag-handle", role: "separator", "aria-orientation": "horizontal" }),
    /* @__PURE__ */ u3("div", { className: "workspace__pane-bottom", children: [
      /* @__PURE__ */ u3("div", { className: "workspace__preview-header", children: "Preview" }),
      /* @__PURE__ */ u3("section", { className: "workspace__preview-info", "aria-labelledby": "workspace-editor-title", children: [
        /* @__PURE__ */ u3("div", { id: "workspace-editor-title", className: "workspace__preview-name", children: "Selected file" }),
        /* @__PURE__ */ u3("div", { id: "workspace-editor-path", className: "workspace__preview-path", children: view.filePath ?? "No file selected" }),
        /* @__PURE__ */ u3("label", { className: "sr-only", htmlFor: "workspace-editor", children: "Workspace file editor" }),
        /* @__PURE__ */ u3("textarea", { id: "workspace-editor", className: "workspace__preview-content", spellcheck: false, "aria-describedby": describedBy, value: view.content, readOnly: true }),
        /* @__PURE__ */ u3("p", { id: "workspace-editor-note", className: "workspace__preview-meta", children: "Local edits are not yet persisted through the web shell." }),
        /* @__PURE__ */ u3("section", { id: "workspace-annotations", className: "workspace-annotations", hidden: !view.annotations.length, children: [
          /* @__PURE__ */ u3("h4", { children: "Annotations" }),
          /* @__PURE__ */ u3("ul", { id: "workspace-annotation-list", className: "workspace-annotation-list", children: view.annotations.map((annotation, index) => /* @__PURE__ */ u3("li", { className: "workspace-annotation", "data-severity": annotation.severity, children: [
            "Line ",
            annotation.line,
            annotation.endLine ? `\u2013${annotation.endLine}` : "",
            annotation.source ? ` \xB7 ${annotation.source}` : "",
            ": ",
            annotation.message
          ] }, `${annotation.line}:${index}`)) })
        ] }),
        /* @__PURE__ */ u3("section", { id: "workspace-renderer", className: "workspace-renderer", "aria-label": "Extension file preview", hidden: true })
      ] })
    ] })
  ] });
}

// src/components/Sidebar.tsx
function Sidebar({ title, children, id: id2, label, actions }) {
  return /* @__PURE__ */ u3("aside", { id: id2, className: "sidebar", "aria-label": label, children: [
    /* @__PURE__ */ u3("header", { className: "sidebar__header", children: [
      /* @__PURE__ */ u3("span", { className: "sidebar__title", children: title.toUpperCase() }),
      actions
    ] }),
    /* @__PURE__ */ u3("div", { className: "sidebar__content", children })
  ] });
}

// src/components/SidePanel.tsx
var TITLES = {
  sessions: "Sessions",
  workspace: "Workspace",
  search: "Search",
  plan: "Plan",
  settings: "Settings"
};
var LegacyTabAnchor = ({ name, selected, onSelect }) => /* @__PURE__ */ u3("button", { id: `tab-${name}`, type: "button", "aria-controls": `panel-${name}`, "aria-selected": selected, onClick: () => onSelect(name), children: TITLES[name] });
function SidePanel({ activeTab, onSelectTab, onClose, sessionFilter, onSelectSessionFilter }) {
  return /* @__PURE__ */ u3(Sidebar, { id: "side-panel", title: TITLES[activeTab], label: `${TITLES[activeTab]} sidebar`, actions: /* @__PURE__ */ u3(b, { children: [
    /* @__PURE__ */ u3("button", { id: "close-nav-drawer", className: "sidebar__close mobile-only", type: "button", "aria-label": "Close sessions drawer", hidden: activeTab !== "sessions", onClick: onClose, children: "\u2715" }),
    /* @__PURE__ */ u3("button", { id: "close-panel-drawer", className: "sidebar__close mobile-only", type: "button", "aria-label": "Close workspace drawer", hidden: activeTab === "sessions", onClick: onClose, children: "\u2715" })
  ] }), children: [
    /* @__PURE__ */ u3("div", { hidden: true, children: [
      /* @__PURE__ */ u3(LegacyTabAnchor, { name: "workspace", selected: activeTab === "workspace", onSelect: onSelectTab }),
      /* @__PURE__ */ u3(LegacyTabAnchor, { name: "search", selected: activeTab === "search", onSelect: onSelectTab }),
      /* @__PURE__ */ u3(LegacyTabAnchor, { name: "plan", selected: activeTab === "plan", onSelect: onSelectTab }),
      /* @__PURE__ */ u3(LegacyTabAnchor, { name: "settings", selected: activeTab === "settings", onSelect: onSelectTab })
    ] }),
    /* @__PURE__ */ u3("section", { id: "panel-sessions", className: "sessions-panel", "aria-label": "Session navigation", hidden: activeTab !== "sessions", children: [
      /* @__PURE__ */ u3("div", { className: "sessions-panel__toolbar", role: "group", "aria-label": "Session actions", children: [
        /* @__PURE__ */ u3("button", { id: "new-session-button", className: "sessions-panel__new settings-panel__provider-btn", type: "button", children: [
          /* @__PURE__ */ u3("i", { className: "codicon codicon-add", "aria-hidden": "true" }),
          " New"
        ] }),
        /* @__PURE__ */ u3("button", { id: "archive-session-button", className: "sessions-panel__action settings-panel__provider-btn", type: "button", children: "Archive" }),
        /* @__PURE__ */ u3("button", { id: "restore-session-button", className: "sessions-panel__action settings-panel__provider-btn", type: "button", children: "Restore" })
      ] }),
      /* @__PURE__ */ u3(SessionList, { filter: sessionFilter, onSelectFilter: onSelectSessionFilter })
    ] }),
    /* @__PURE__ */ u3(WorkspacePanel, { hidden: activeTab !== "workspace" }),
    /* @__PURE__ */ u3("section", { id: "panel-search", className: "search-panel", "aria-labelledby": "tab-search", hidden: activeTab !== "search", children: [
      /* @__PURE__ */ u3("form", { id: "search-form", children: [
        /* @__PURE__ */ u3("label", { className: "sr-only", htmlFor: "search-input", children: "Search persisted content" }),
        /* @__PURE__ */ u3("div", { className: "search-panel__input-wrapper", children: [
          /* @__PURE__ */ u3("span", { className: "search-panel__icon", "aria-hidden": "true", children: "\u2315" }),
          /* @__PURE__ */ u3("input", { id: "search-input", className: "search-panel__input", name: "query", type: "search", autoComplete: "off", spellcheck: false, placeholder: "Search messages\u2026" }),
          /* @__PURE__ */ u3("button", { id: "search-submit-button", className: "search-panel__submit", type: "submit", children: "Search" })
        ] })
      ] }),
      /* @__PURE__ */ u3(SearchResults, {})
    ] }),
    /* @__PURE__ */ u3(PlanPanel, { hidden: activeTab !== "plan" })
  ] });
}

// src/components/ModelControls.tsx
var thinking = [
  { value: "", label: "Default" },
  { value: "off", label: "Off \u2014 no reasoning" },
  { value: "minimal", label: "Minimal \u2014 very brief reasoning" },
  { value: "low", label: "Low \u2014 light reasoning" },
  { value: "medium", label: "Medium \u2014 moderate reasoning" },
  { value: "high", label: "High \u2014 deep reasoning" },
  { value: "xhigh", label: "XHigh \u2014 maximum reasoning" }
];
function ModelControls() {
  const [options, setOptions] = h2({ providers: [], models: [] });
  _2(() => {
    const update = (event) => setOptions(event.detail);
    window.addEventListener("tau:model-options-render", update);
    return () => window.removeEventListener("tau:model-options-render", update);
  }, []);
  return /* @__PURE__ */ u3(b, { children: [
    /* @__PURE__ */ u3("form", { id: "model-form", children: [
      /* @__PURE__ */ u3("div", { className: "settings-panel__field", children: [
        /* @__PURE__ */ u3("label", { className: "settings-panel__label", htmlFor: "provider-input", children: "Provider" }),
        /* @__PURE__ */ u3("input", { id: "provider-input", className: "settings-panel__input", list: "provider-options", autoComplete: "off" }),
        /* @__PURE__ */ u3("datalist", { id: "provider-options", children: options.providers.map((item) => /* @__PURE__ */ u3("option", { value: item.value, children: item.label }, item.value)) })
      ] }),
      /* @__PURE__ */ u3("div", { className: "settings-panel__field", children: [
        /* @__PURE__ */ u3("label", { className: "settings-panel__label", htmlFor: "model-input", children: "Model" }),
        /* @__PURE__ */ u3("input", { id: "model-input", className: "settings-panel__input", list: "model-options", autoComplete: "off" }),
        /* @__PURE__ */ u3("datalist", { id: "model-options", children: options.models.map((item) => /* @__PURE__ */ u3("option", { value: item.value, children: item.label }, item.value)) })
      ] }),
      /* @__PURE__ */ u3("div", { className: "settings-panel__field", children: [
        /* @__PURE__ */ u3("span", { className: "settings-panel__label" }),
        /* @__PURE__ */ u3("button", { id: "apply-model-button", className: "settings-panel__provider-btn", type: "submit", children: "Apply to session" }),
        /* @__PURE__ */ u3("button", { id: "refresh-button", className: "settings-panel__provider-btn", type: "button", children: "Refresh" })
      ] })
    ] }),
    /* @__PURE__ */ u3("form", { id: "thinking-form", children: [
      /* @__PURE__ */ u3("div", { className: "settings-panel__field", children: [
        /* @__PURE__ */ u3("label", { className: "settings-panel__label", htmlFor: "thinking-level-select", children: "Thinking level" }),
        /* @__PURE__ */ u3("select", { id: "thinking-level-select", className: "settings-panel__select", name: "thinking_level", children: thinking.map((item) => /* @__PURE__ */ u3("option", { value: item.value, children: item.label }, item.value)) }),
        /* @__PURE__ */ u3("button", { id: "apply-thinking-button", className: "settings-panel__provider-btn", type: "submit", children: "Apply" })
      ] }),
      /* @__PURE__ */ u3("p", { id: "thinking-help", className: "settings-panel__description", children: "Updates session thinking with optimistic concurrency checks." })
    ] })
  ] });
}

// src/components/SettingsSummary.tsx
function SettingsSummary() {
  const [items, setItems] = h2(null);
  _2(() => {
    const update = (event) => setItems(event.detail.items);
    window.addEventListener("tau:settings-render", update);
    return () => window.removeEventListener("tau:settings-render", update);
  }, []);
  return /* @__PURE__ */ u3("dl", { id: "settings-summary", className: "settings-summary", children: items === null ? /* @__PURE__ */ u3("div", { children: /* @__PURE__ */ u3("dd", { className: "muted-text", children: "Runtime settings unavailable." }) }) : items.map((item) => /* @__PURE__ */ u3("div", { children: [
    /* @__PURE__ */ u3("dt", { children: item.label }),
    /* @__PURE__ */ u3("dd", { children: item.value })
  ] }, item.label)) });
}

// src/components/SettingsPanel.tsx
function SettingsPanel({ hidden }) {
  return /* @__PURE__ */ u3("section", { id: "panel-settings", className: "settings-panel", "aria-labelledby": "tab-settings", hidden, children: [
    /* @__PURE__ */ u3("nav", { className: "settings-panel__nav", "aria-label": "Settings categories", children: [
      /* @__PURE__ */ u3("a", { className: "settings-panel__nav-item settings-panel__nav-item--active", href: "#tau-settings-auth", children: [
        /* @__PURE__ */ u3("i", { className: "codicon codicon-shield", "aria-hidden": "true" }),
        "Authentication"
      ] }),
      /* @__PURE__ */ u3("a", { className: "settings-panel__nav-item", href: "#tau-settings-model", children: [
        /* @__PURE__ */ u3("i", { className: "codicon codicon-symbol-parameter", "aria-hidden": "true" }),
        "Model"
      ] }),
      /* @__PURE__ */ u3("a", { className: "settings-panel__nav-item", href: "#tau-settings-runtime", children: [
        /* @__PURE__ */ u3("i", { className: "codicon codicon-server", "aria-hidden": "true" }),
        "Runtime"
      ] })
    ] }),
    /* @__PURE__ */ u3("div", { className: "settings-panel__content", children: [
      /* @__PURE__ */ u3("section", { id: "tau-settings-auth", className: "settings-panel__section", children: [
        /* @__PURE__ */ u3("h2", { className: "settings-panel__section-title", children: "Authentication" }),
        /* @__PURE__ */ u3("button", { className: "settings-panel__provider-btn settings-provider-setup", type: "button", onClick: () => {
          window.dispatchEvent(new CustomEvent("tau:switch-tab", { detail: { tab: "workspace" } }));
          document.querySelector(".provider-setup-trigger")?.click();
        }, children: "Provider setup" }),
        /* @__PURE__ */ u3("form", { id: "auth-form", children: [
          /* @__PURE__ */ u3("div", { className: "settings-panel__field", children: [
            /* @__PURE__ */ u3("label", { className: "settings-panel__label", htmlFor: "auth-token", children: "Bearer token" }),
            /* @__PURE__ */ u3("input", { id: "auth-token", className: "settings-panel__input", type: "password", autoComplete: "off" })
          ] }),
          /* @__PURE__ */ u3("div", { className: "settings-panel__field", children: [
            /* @__PURE__ */ u3("span", { className: "settings-panel__label" }),
            /* @__PURE__ */ u3("button", { id: "save-auth-button", className: "settings-panel__provider-btn", type: "submit", children: "Save token" }),
            /* @__PURE__ */ u3("button", { id: "clear-auth-button", className: "settings-panel__provider-btn settings-panel__provider-btn--logout", type: "button", children: "Clear token" })
          ] })
        ] })
      ] }),
      /* @__PURE__ */ u3("section", { id: "tau-settings-model", className: "settings-panel__section", children: [
        /* @__PURE__ */ u3("h2", { className: "settings-panel__section-title", children: "Model" }),
        /* @__PURE__ */ u3(ModelControls, {})
      ] }),
      /* @__PURE__ */ u3("section", { id: "tau-settings-runtime", className: "settings-panel__section", "aria-labelledby": "settings-summary-title", children: [
        /* @__PURE__ */ u3("h2", { id: "settings-summary-title", className: "settings-panel__section-title", children: "Runtime" }),
        /* @__PURE__ */ u3(SettingsSummary, {}),
        /* @__PURE__ */ u3("p", { id: "streaming-note", className: "settings-panel__description", children: "Live streaming, queue controls, and persisted timeline playback use safe DOM updates." }),
        /* @__PURE__ */ u3("div", { className: "extension-slot", "data-extension-slot": "sidebar" })
      ] })
    ] })
  ] });
}

// src/components/CopyButton.tsx
function CopyButton({ text: text2 }) {
  const [copied, setCopied] = h2(false);
  const timer = A2();
  y2(() => () => clearTimeout(timer.current), []);
  return /* @__PURE__ */ u3(
    "button",
    {
      type: "button",
      className: `tool-call__copy${copied ? " tool-call__copy--copied" : ""}`,
      title: copied ? "Copied!" : "Copy",
      "aria-label": copied ? "Copied!" : "Copy",
      onClick: async (event) => {
        event.stopPropagation();
        try {
          await navigator.clipboard.writeText(text2);
          setCopied(true);
          clearTimeout(timer.current);
          timer.current = setTimeout(() => setCopied(false), 2e3);
        } catch {
          setCopied(false);
        }
      },
      children: copied ? "\u2713" : /* @__PURE__ */ u3("i", { className: "codicon codicon-copy", "aria-hidden": "true" })
    }
  );
}

// node_modules/marked/lib/marked.esm.js
function z3() {
  return { async: false, breaks: false, extensions: null, gfm: true, hooks: null, pedantic: false, renderer: null, silent: false, tokenizer: null, walkTokens: null };
}
var T3 = z3();
function G(u6) {
  T3 = u6;
}
var _3 = { exec: () => null };
function k3(u6, e3 = "") {
  let t3 = typeof u6 == "string" ? u6 : u6.source, n2 = { replace: (r3, i4) => {
    let s3 = typeof i4 == "string" ? i4 : i4.source;
    return s3 = s3.replace(m2.caret, "$1"), t3 = t3.replace(r3, s3), n2;
  }, getRegex: () => new RegExp(t3, e3) };
  return n2;
}
var Re = (() => {
  try {
    return !!new RegExp("(?<=1)(?<!1)");
  } catch {
    return false;
  }
})();
var m2 = { codeRemoveIndent: /^(?: {1,4}| {0,3}\t)/gm, outputLinkReplace: /\\([\[\]])/g, indentCodeCompensation: /^(\s+)(?:```)/, beginningSpace: /^\s+/, endingHash: /#$/, startingSpaceChar: /^ /, endingSpaceChar: / $/, nonSpaceChar: /[^ ]/, newLineCharGlobal: /\n/g, tabCharGlobal: /\t/g, multipleSpaceGlobal: /\s+/g, blankLine: /^[ \t]*$/, doubleBlankLine: /\n[ \t]*\n[ \t]*$/, blockquoteStart: /^ {0,3}>/, blockquoteSetextReplace: /\n {0,3}((?:=+|-+) *)(?=\n|$)/g, blockquoteSetextReplace2: /^ {0,3}>[ \t]?/gm, listReplaceNesting: /^ {1,4}(?=( {4})*[^ ])/g, listIsTask: /^\[[ xX]\] +\S/, listReplaceTask: /^\[[ xX]\] +/, listTaskCheckbox: /\[[ xX]\]/, anyLine: /\n.*\n/, hrefBrackets: /^<(.*)>$/, tableDelimiter: /[:|]/, tableAlignChars: /^\||\| *$/g, tableRowBlankLine: /\n[ \t]*$/, tableAlignRight: /^ *-+: *$/, tableAlignCenter: /^ *:-+: *$/, tableAlignLeft: /^ *:-+ *$/, startATag: /^<a /i, endATag: /^<\/a>/i, startPreScriptTag: /^<(pre|code|kbd|script)(\s|>)/i, endPreScriptTag: /^<\/(pre|code|kbd|script)(\s|>)/i, startAngleBracket: /^</, endAngleBracket: />$/, pedanticHrefTitle: /^([^'"]*[^\s])\s+(['"])(.*)\2/, unicodeAlphaNumeric: /[\p{L}\p{N}]/u, escapeTest: /[&<>"']/, escapeReplace: /[&<>"']/g, escapeTestNoEncode: /[<>"']|&(?!(#\d{1,7}|#[Xx][a-fA-F0-9]{1,6}|\w+);)/, escapeReplaceNoEncode: /[<>"']|&(?!(#\d{1,7}|#[Xx][a-fA-F0-9]{1,6}|\w+);)/g, caret: /(^|[^\[])\^/g, percentDecode: /%25/g, findPipe: /\|/g, splitPipe: / \|/, slashPipe: /\\\|/g, carriageReturn: /\r\n|\r/g, spaceLine: /^ +$/gm, notSpaceStart: /^\S*/, endingNewline: /\n$/, listItemRegex: (u6) => new RegExp(`^( {0,3}${u6})((?:[	 ][^\\n]*)?(?:\\n|$))`), nextBulletRegex: (u6) => new RegExp(`^ {0,${Math.min(3, u6 - 1)}}(?:[*+-]|\\d{1,9}[.)])((?:[ 	][^\\n]*)?(?:\\n|$))`), hrRegex: (u6) => new RegExp(`^ {0,${Math.min(3, u6 - 1)}}((?:- *){3,}|(?:_ *){3,}|(?:\\* *){3,})(?:\\n+|$)`), fencesBeginRegex: (u6) => new RegExp(`^ {0,${Math.min(3, u6 - 1)}}(?:\`\`\`|~~~)`), headingBeginRegex: (u6) => new RegExp(`^ {0,${Math.min(3, u6 - 1)}}#`), htmlBeginRegex: (u6) => new RegExp(`^ {0,${Math.min(3, u6 - 1)}}<(?:[a-z].*>|!--)`, "i"), blockquoteBeginRegex: (u6) => new RegExp(`^ {0,${Math.min(3, u6 - 1)}}>`) };
var Te = /^(?:[ \t]*(?:\n|$))+/;
var Oe = /^((?: {4}| {0,3}\t)[^\n]+(?:\n(?:[ \t]*(?:\n|$))*)?)+/;
var we = /^ {0,3}(`{3,}(?=[^`\n]*(?:\n|$))|~{3,})([^\n]*)(?:\n|$)(?:|([\s\S]*?)(?:\n|$))(?: {0,3}\1[~`]* *(?=\n|$)|$)/;
var C3 = /^ {0,3}((?:-[\t ]*){3,}|(?:_[ \t]*){3,}|(?:\*[ \t]*){3,})(?:\n+|$)/;
var ye = /^ {0,3}(#{1,6})(?=\s|$)(.*)(?:\n+|$)/;
var Q = / {0,3}(?:[*+-]|\d{1,9}[.)])/;
var ie = /^(?!bull |blockCode|fences|blockquote|heading|html|table)((?:.|\n(?!\s*?\n|bull |blockCode|fences|blockquote|heading|html|table))+?)\n {0,3}(=+|-+) *(?:\n+|$)/;
var oe = k3(ie).replace(/bull/g, Q).replace(/blockCode/g, /(?: {4}| {0,3}\t)/).replace(/fences/g, / {0,3}(?:`{3,}|~{3,})/).replace(/blockquote/g, / {0,3}>/).replace(/heading/g, / {0,3}#{1,6}/).replace(/html/g, / {0,3}<[^\n>]+>\n/).replace(/\|table/g, "").getRegex();
var Pe = k3(ie).replace(/bull/g, Q).replace(/blockCode/g, /(?: {4}| {0,3}\t)/).replace(/fences/g, / {0,3}(?:`{3,}|~{3,})/).replace(/blockquote/g, / {0,3}>/).replace(/heading/g, / {0,3}#{1,6}/).replace(/html/g, / {0,3}<[^\n>]+>\n/).replace(/table/g, / {0,3}\|?(?:[:\- ]*\|)+[\:\- ]*\n/).getRegex();
var j3 = /^([^\n]+(?:\n(?!hr|heading|lheading|blockquote|fences|list|html|table| +\n)[^\n]+)*)/;
var Se = /^[^\n]+/;
var F2 = /(?!\s*\])(?:\\[\s\S]|[^\[\]\\])+/;
var $e = k3(/^ {0,3}\[(label)\]: *(?:\n[ \t]*)?([^<\s][^\s]*|<.*?>)(?:(?: +(?:\n[ \t]*)?| *\n[ \t]*)(title))? *(?:\n+|$)/).replace("label", F2).replace("title", /(?:"(?:\\"?|[^"\\])*"|'[^'\n]*(?:\n[^'\n]+)*\n?'|\([^()]*\))/).getRegex();
var Le = k3(/^(bull)([ \t][^\n]+?)?(?:\n|$)/).replace(/bull/g, Q).getRegex();
var v3 = "address|article|aside|base|basefont|blockquote|body|caption|center|col|colgroup|dd|details|dialog|dir|div|dl|dt|fieldset|figcaption|figure|footer|form|frame|frameset|h[1-6]|head|header|hr|html|iframe|legend|li|link|main|menu|menuitem|meta|nav|noframes|ol|optgroup|option|p|param|search|section|summary|table|tbody|td|tfoot|th|thead|title|tr|track|ul";
var U = /<!--(?:-?>|[\s\S]*?(?:-->|$))/;
var _e = k3("^ {0,3}(?:<(script|pre|style|textarea)[\\s>][\\s\\S]*?(?:</\\1>[^\\n]*\\n+|$)|comment[^\\n]*(\\n+|$)|<\\?[\\s\\S]*?(?:\\?>\\n*|$)|<![A-Z][\\s\\S]*?(?:>\\n*|$)|<!\\[CDATA\\[[\\s\\S]*?(?:\\]\\]>\\n*|$)|</?(tag)(?: +|\\n|/?>)[\\s\\S]*?(?:(?:\\n[ 	]*)+\\n|$)|<(?!script|pre|style|textarea)([a-z][\\w-]*)(?:attribute)*? */?>(?=[ \\t]*(?:\\n|$))[\\s\\S]*?(?:(?:\\n[ 	]*)+\\n|$)|</(?!script|pre|style|textarea)[a-z][\\w-]*\\s*>(?=[ \\t]*(?:\\n|$))[\\s\\S]*?(?:(?:\\n[ 	]*)+\\n|$))", "i").replace("comment", U).replace("tag", v3).replace("attribute", / +[a-zA-Z:_][\w.:-]*(?: *= *"[^"\n]*"| *= *'[^'\n]*'| *= *[^\s"'=<>`]+)?/).getRegex();
var ae = k3(j3).replace("hr", C3).replace("heading", " {0,3}#{1,6}(?:\\s|$)").replace("|lheading", "").replace("|table", "").replace("blockquote", " {0,3}>").replace("fences", " {0,3}(?:`{3,}(?=[^`\\n]*\\n)|~{3,})[^\\n]*\\n").replace("list", " {0,3}(?:[*+-]|1[.)])[ \\t]").replace("html", "</?(?:tag)(?: +|\\n|/?>)|<(?:script|pre|style|textarea|!--)").replace("tag", v3).getRegex();
var Me = k3(/^( {0,3}> ?(paragraph|[^\n]*)(?:\n|$))+/).replace("paragraph", ae).getRegex();
var K = { blockquote: Me, code: Oe, def: $e, fences: we, heading: ye, hr: C3, html: _e, lheading: oe, list: Le, newline: Te, paragraph: ae, table: _3, text: Se };
var re = k3("^ *([^\\n ].*)\\n {0,3}((?:\\| *)?:?-+:? *(?:\\| *:?-+:? *)*(?:\\| *)?)(?:\\n((?:(?! *\\n|hr|heading|blockquote|code|fences|list|html).*(?:\\n|$))*)\\n*|$)").replace("hr", C3).replace("heading", " {0,3}#{1,6}(?:\\s|$)").replace("blockquote", " {0,3}>").replace("code", "(?: {4}| {0,3}	)[^\\n]").replace("fences", " {0,3}(?:`{3,}(?=[^`\\n]*\\n)|~{3,})[^\\n]*\\n").replace("list", " {0,3}(?:[*+-]|1[.)])[ \\t]").replace("html", "</?(?:tag)(?: +|\\n|/?>)|<(?:script|pre|style|textarea|!--)").replace("tag", v3).getRegex();
var ze = { ...K, lheading: Pe, table: re, paragraph: k3(j3).replace("hr", C3).replace("heading", " {0,3}#{1,6}(?:\\s|$)").replace("|lheading", "").replace("table", re).replace("blockquote", " {0,3}>").replace("fences", " {0,3}(?:`{3,}(?=[^`\\n]*\\n)|~{3,})[^\\n]*\\n").replace("list", " {0,3}(?:[*+-]|1[.)])[ \\t]").replace("html", "</?(?:tag)(?: +|\\n|/?>)|<(?:script|pre|style|textarea|!--)").replace("tag", v3).getRegex() };
var Ee = { ...K, html: k3(`^ *(?:comment *(?:\\n|\\s*$)|<(tag)[\\s\\S]+?</\\1> *(?:\\n{2,}|\\s*$)|<tag(?:"[^"]*"|'[^']*'|\\s[^'"/>\\s]*)*?/?> *(?:\\n{2,}|\\s*$))`).replace("comment", U).replace(/tag/g, "(?!(?:a|em|strong|small|s|cite|q|dfn|abbr|data|time|code|var|samp|kbd|sub|sup|i|b|u|mark|ruby|rt|rp|bdi|bdo|span|br|wbr|ins|del|img)\\b)\\w+(?!:|[^\\w\\s@]*@)\\b").getRegex(), def: /^ *\[([^\]]+)\]: *<?([^\s>]+)>?(?: +(["(][^\n]+[")]))? *(?:\n+|$)/, heading: /^(#{1,6})(.*)(?:\n+|$)/, fences: _3, lheading: /^(.+?)\n {0,3}(=+|-+) *(?:\n+|$)/, paragraph: k3(j3).replace("hr", C3).replace("heading", ` *#{1,6} *[^
]`).replace("lheading", oe).replace("|table", "").replace("blockquote", " {0,3}>").replace("|fences", "").replace("|list", "").replace("|html", "").replace("|tag", "").getRegex() };
var Ie = /^\\([!"#$%&'()*+,\-./:;<=>?@\[\]\\^_`{|}~])/;
var Ae = /^(`+)([^`]|[^`][\s\S]*?[^`])\1(?!`)/;
var le = /^( {2,}|\\)\n(?!\s*$)/;
var Ce = /^(`+|[^`])(?:(?= {2,}\n)|[\s\S]*?(?:(?=[\\<!\[`*_]|\b_|$)|[^ ](?= {2,}\n)))/;
var E = /[\p{P}\p{S}]/u;
var H = /[\s\p{P}\p{S}]/u;
var W = /[^\s\p{P}\p{S}]/u;
var Be = k3(/^((?![*_])punctSpace)/, "u").replace(/punctSpace/g, H).getRegex();
var ue = /(?!~)[\p{P}\p{S}]/u;
var De = /(?!~)[\s\p{P}\p{S}]/u;
var qe = /(?:[^\s\p{P}\p{S}]|~)/u;
var ve = k3(/link|precode-code|html/, "g").replace("link", /\[(?:[^\[\]`]|(?<a>`+)[^`]+\k<a>(?!`))*?\]\((?:\\[\s\S]|[^\\\(\)]|\((?:\\[\s\S]|[^\\\(\)])*\))*\)/).replace("precode-", Re ? "(?<!`)()" : "(^^|[^`])").replace("code", /(?<b>`+)[^`]+\k<b>(?!`)/).replace("html", /<(?! )[^<>]*?>/).getRegex();
var pe = /^(?:\*+(?:((?!\*)punct)|([^\s*]))?)|^_+(?:((?!_)punct)|([^\s_]))?/;
var He = k3(pe, "u").replace(/punct/g, E).getRegex();
var Ze = k3(pe, "u").replace(/punct/g, ue).getRegex();
var ce = "^[^_*]*?__[^_*]*?\\*[^_*]*?(?=__)|[^*]+(?=[^*])|(?!\\*)punct(\\*+)(?=[\\s]|$)|notPunctSpace(\\*+)(?!\\*)(?=punctSpace|$)|(?!\\*)punctSpace(\\*+)(?=notPunctSpace)|[\\s](\\*+)(?!\\*)(?=punct)|(?!\\*)punct(\\*+)(?!\\*)(?=punct)|notPunctSpace(\\*+)(?=notPunctSpace)";
var Ge = k3(ce, "gu").replace(/notPunctSpace/g, W).replace(/punctSpace/g, H).replace(/punct/g, E).getRegex();
var Ne = k3(ce, "gu").replace(/notPunctSpace/g, qe).replace(/punctSpace/g, De).replace(/punct/g, ue).getRegex();
var Qe = k3("^[^_*]*?\\*\\*[^_*]*?_[^_*]*?(?=\\*\\*)|[^_]+(?=[^_])|(?!_)punct(_+)(?=[\\s]|$)|notPunctSpace(_+)(?!_)(?=punctSpace|$)|(?!_)punctSpace(_+)(?=notPunctSpace)|[\\s](_+)(?!_)(?=punct)|(?!_)punct(_+)(?!_)(?=punct)", "gu").replace(/notPunctSpace/g, W).replace(/punctSpace/g, H).replace(/punct/g, E).getRegex();
var je = k3(/^~~?(?:((?!~)punct)|[^\s~])/, "u").replace(/punct/g, E).getRegex();
var Fe = "^[^~]+(?=[^~])|(?!~)punct(~~?)(?=[\\s]|$)|notPunctSpace(~~?)(?!~)(?=punctSpace|$)|(?!~)punctSpace(~~?)(?=notPunctSpace)|[\\s](~~?)(?!~)(?=punct)|(?!~)punct(~~?)(?!~)(?=punct)|notPunctSpace(~~?)(?=notPunctSpace)";
var Ue = k3(Fe, "gu").replace(/notPunctSpace/g, W).replace(/punctSpace/g, H).replace(/punct/g, E).getRegex();
var Ke = k3(/\\(punct)/, "gu").replace(/punct/g, E).getRegex();
var We = k3(/^<(scheme:[^\s\x00-\x1f<>]*|email)>/).replace("scheme", /[a-zA-Z][a-zA-Z0-9+.-]{1,31}/).replace("email", /[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+(@)[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)+(?![-_])/).getRegex();
var Xe = k3(U).replace("(?:-->|$)", "-->").getRegex();
var Je = k3("^comment|^</[a-zA-Z][\\w:-]*\\s*>|^<[a-zA-Z][\\w-]*(?:attribute)*?\\s*/?>|^<\\?[\\s\\S]*?\\?>|^<![a-zA-Z]+\\s[\\s\\S]*?>|^<!\\[CDATA\\[[\\s\\S]*?\\]\\]>").replace("comment", Xe).replace("attribute", /\s+[a-zA-Z:_][\w.:-]*(?:\s*=\s*"[^"]*"|\s*=\s*'[^']*'|\s*=\s*[^\s"'=<>`]+)?/).getRegex();
var q3 = /(?:\[(?:\\[\s\S]|[^\[\]\\])*\]|\\[\s\S]|`+(?!`)[^`]*?`+(?!`)|``+(?=\])|[^\[\]\\`])*?/;
var Ve = k3(/^!?\[(label)\]\(\s*(href)(?:(?:[ \t]+(?:\n[ \t]*)?|\n[ \t]*)(title))?\s*\)/).replace("label", q3).replace("href", /<(?:\\.|[^\n<>\\])+>|[^ \t\n\x00-\x1f]*/).replace("title", /"(?:\\"?|[^"\\])*"|'(?:\\'?|[^'\\])*'|\((?:\\\)?|[^)\\])*\)/).getRegex();
var he = k3(/^!?\[(label)\]\[(ref)\]/).replace("label", q3).replace("ref", F2).getRegex();
var ke = k3(/^!?\[(ref)\](?:\[\])?/).replace("ref", F2).getRegex();
var Ye = k3("reflink|nolink(?!\\()", "g").replace("reflink", he).replace("nolink", ke).getRegex();
var se = /[hH][tT][tT][pP][sS]?|[fF][tT][pP]/;
var X = { _backpedal: _3, anyPunctuation: Ke, autolink: We, blockSkip: ve, br: le, code: Ae, del: _3, delLDelim: _3, delRDelim: _3, emStrongLDelim: He, emStrongRDelimAst: Ge, emStrongRDelimUnd: Qe, escape: Ie, link: Ve, nolink: ke, punctuation: Be, reflink: he, reflinkSearch: Ye, tag: Je, text: Ce, url: _3 };
var et = { ...X, link: k3(/^!?\[(label)\]\((.*?)\)/).replace("label", q3).getRegex(), reflink: k3(/^!?\[(label)\]\s*\[([^\]]*)\]/).replace("label", q3).getRegex() };
var N2 = { ...X, emStrongRDelimAst: Ne, emStrongLDelim: Ze, delLDelim: je, delRDelim: Ue, url: k3(/^((?:protocol):\/\/|www\.)(?:[a-zA-Z0-9\-]+\.?)+[^\s<]*|^email/).replace("protocol", se).replace("email", /[A-Za-z0-9._+-]+(@)[a-zA-Z0-9-_]+(?:\.[a-zA-Z0-9-_]*[a-zA-Z0-9])+(?![-_])/).getRegex(), _backpedal: /(?:[^?!.,:;*_'"~()&]+|\([^)]*\)|&(?![a-zA-Z0-9]+;$)|[?!.,:;*_'"~)]+(?!$))+/, del: /^(~~?)(?=[^\s~])((?:\\[\s\S]|[^\\])*?(?:\\[\s\S]|[^\s~\\]))\1(?=[^~]|$)/, text: k3(/^([`~]+|[^`~])(?:(?= {2,}\n)|(?=[a-zA-Z0-9.!#$%&'*+\/=?_`{\|}~-]+@)|[\s\S]*?(?:(?=[\\<!\[`*~_]|\b_|protocol:\/\/|www\.|$)|[^ ](?= {2,}\n)|[^a-zA-Z0-9.!#$%&'*+\/=?_`{\|}~-](?=[a-zA-Z0-9.!#$%&'*+\/=?_`{\|}~-]+@)))/).replace("protocol", se).getRegex() };
var tt = { ...N2, br: k3(le).replace("{2,}", "*").getRegex(), text: k3(N2.text).replace("\\b_", "\\b_| {2,}\\n").replace(/\{2,\}/g, "*").getRegex() };
var B3 = { normal: K, gfm: ze, pedantic: Ee };
var I2 = { normal: X, gfm: N2, breaks: tt, pedantic: et };
var nt = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" };
var de = (u6) => nt[u6];
function O2(u6, e3) {
  if (e3) {
    if (m2.escapeTest.test(u6)) return u6.replace(m2.escapeReplace, de);
  } else if (m2.escapeTestNoEncode.test(u6)) return u6.replace(m2.escapeReplaceNoEncode, de);
  return u6;
}
function J(u6) {
  try {
    u6 = encodeURI(u6).replace(m2.percentDecode, "%");
  } catch {
    return null;
  }
  return u6;
}
function V2(u6, e3) {
  let t3 = u6.replace(m2.findPipe, (i4, s3, a3) => {
    let o3 = false, l3 = s3;
    for (; --l3 >= 0 && a3[l3] === "\\"; ) o3 = !o3;
    return o3 ? "|" : " |";
  }), n2 = t3.split(m2.splitPipe), r3 = 0;
  if (n2[0].trim() || n2.shift(), n2.length > 0 && !n2.at(-1)?.trim() && n2.pop(), e3) if (n2.length > e3) n2.splice(e3);
  else for (; n2.length < e3; ) n2.push("");
  for (; r3 < n2.length; r3++) n2[r3] = n2[r3].trim().replace(m2.slashPipe, "|");
  return n2;
}
function $2(u6, e3, t3) {
  let n2 = u6.length;
  if (n2 === 0) return "";
  let r3 = 0;
  for (; r3 < n2; ) {
    let i4 = u6.charAt(n2 - r3 - 1);
    if (i4 === e3 && !t3) r3++;
    else if (i4 !== e3 && t3) r3++;
    else break;
  }
  return u6.slice(0, n2 - r3);
}
function Y(u6) {
  let e3 = u6.split(`
`), t3 = e3.length - 1;
  for (; t3 >= 0 && !e3[t3].trim(); ) t3--;
  return e3.length - t3 <= 2 ? u6 : e3.slice(0, t3 + 1).join(`
`);
}
function ge(u6, e3) {
  if (u6.indexOf(e3[1]) === -1) return -1;
  let t3 = 0;
  for (let n2 = 0; n2 < u6.length; n2++) if (u6[n2] === "\\") n2++;
  else if (u6[n2] === e3[0]) t3++;
  else if (u6[n2] === e3[1] && (t3--, t3 < 0)) return n2;
  return t3 > 0 ? -2 : -1;
}
function fe(u6, e3 = 0) {
  let t3 = e3, n2 = "";
  for (let r3 of u6) if (r3 === "	") {
    let i4 = 4 - t3 % 4;
    n2 += " ".repeat(i4), t3 += i4;
  } else n2 += r3, t3++;
  return n2;
}
function me(u6, e3, t3, n2, r3) {
  let i4 = e3.href, s3 = e3.title || null, a3 = u6[1].replace(r3.other.outputLinkReplace, "$1");
  n2.state.inLink = true;
  let o3 = { type: u6[0].charAt(0) === "!" ? "image" : "link", raw: t3, href: i4, title: s3, text: a3, tokens: n2.inlineTokens(a3) };
  return n2.state.inLink = false, o3;
}
function rt(u6, e3, t3) {
  let n2 = u6.match(t3.other.indentCodeCompensation);
  if (n2 === null) return e3;
  let r3 = n2[1];
  return e3.split(`
`).map((i4) => {
    let s3 = i4.match(t3.other.beginningSpace);
    if (s3 === null) return i4;
    let [a3] = s3;
    return a3.length >= r3.length ? i4.slice(r3.length) : i4;
  }).join(`
`);
}
var w3 = class {
  options;
  rules;
  lexer;
  constructor(e3) {
    this.options = e3 || T3;
  }
  space(e3) {
    let t3 = this.rules.block.newline.exec(e3);
    if (t3 && t3[0].length > 0) return { type: "space", raw: t3[0] };
  }
  code(e3) {
    let t3 = this.rules.block.code.exec(e3);
    if (t3) {
      let n2 = this.options.pedantic ? t3[0] : Y(t3[0]), r3 = n2.replace(this.rules.other.codeRemoveIndent, "");
      return { type: "code", raw: n2, codeBlockStyle: "indented", text: r3 };
    }
  }
  fences(e3) {
    let t3 = this.rules.block.fences.exec(e3);
    if (t3) {
      let n2 = t3[0], r3 = rt(n2, t3[3] || "", this.rules);
      return { type: "code", raw: n2, lang: t3[2] ? t3[2].trim().replace(this.rules.inline.anyPunctuation, "$1") : t3[2], text: r3 };
    }
  }
  heading(e3) {
    let t3 = this.rules.block.heading.exec(e3);
    if (t3) {
      let n2 = t3[2].trim();
      if (this.rules.other.endingHash.test(n2)) {
        let r3 = $2(n2, "#");
        (this.options.pedantic || !r3 || this.rules.other.endingSpaceChar.test(r3)) && (n2 = r3.trim());
      }
      return { type: "heading", raw: $2(t3[0], `
`), depth: t3[1].length, text: n2, tokens: this.lexer.inline(n2) };
    }
  }
  hr(e3) {
    let t3 = this.rules.block.hr.exec(e3);
    if (t3) return { type: "hr", raw: $2(t3[0], `
`) };
  }
  blockquote(e3) {
    let t3 = this.rules.block.blockquote.exec(e3);
    if (t3) {
      let n2 = $2(t3[0], `
`).split(`
`), r3 = "", i4 = "", s3 = [];
      for (; n2.length > 0; ) {
        let a3 = false, o3 = [], l3;
        for (l3 = 0; l3 < n2.length; l3++) if (this.rules.other.blockquoteStart.test(n2[l3])) o3.push(n2[l3]), a3 = true;
        else if (!a3) o3.push(n2[l3]);
        else break;
        n2 = n2.slice(l3);
        let p3 = o3.join(`
`), c3 = p3.replace(this.rules.other.blockquoteSetextReplace, `
    $1`).replace(this.rules.other.blockquoteSetextReplace2, "");
        r3 = r3 ? `${r3}
${p3}` : p3, i4 = i4 ? `${i4}
${c3}` : c3;
        let d3 = this.lexer.state.top;
        if (this.lexer.state.top = true, this.lexer.blockTokens(c3, s3, true), this.lexer.state.top = d3, n2.length === 0) break;
        let h3 = s3.at(-1);
        if (h3?.type === "code") break;
        if (h3?.type === "blockquote") {
          let R = h3, f4 = R.raw + `
` + n2.join(`
`), S2 = this.blockquote(f4);
          s3[s3.length - 1] = S2, r3 = r3.substring(0, r3.length - R.raw.length) + S2.raw, i4 = i4.substring(0, i4.length - R.text.length) + S2.text;
          break;
        } else if (h3?.type === "list") {
          let R = h3, f4 = R.raw + `
` + n2.join(`
`), S2 = this.list(f4);
          s3[s3.length - 1] = S2, r3 = r3.substring(0, r3.length - h3.raw.length) + S2.raw, i4 = i4.substring(0, i4.length - R.raw.length) + S2.raw, n2 = f4.substring(s3.at(-1).raw.length).split(`
`);
          continue;
        }
      }
      return { type: "blockquote", raw: r3, tokens: s3, text: i4 };
    }
  }
  list(e3) {
    let t3 = this.rules.block.list.exec(e3);
    if (t3) {
      let n2 = t3[1].trim(), r3 = n2.length > 1, i4 = { type: "list", raw: "", ordered: r3, start: r3 ? +n2.slice(0, -1) : "", loose: false, items: [] };
      n2 = r3 ? `\\d{1,9}\\${n2.slice(-1)}` : `\\${n2}`, this.options.pedantic && (n2 = r3 ? n2 : "[*+-]");
      let s3 = this.rules.other.listItemRegex(n2), a3 = false;
      for (; e3; ) {
        let l3 = false, p3 = "", c3 = "";
        if (!(t3 = s3.exec(e3)) || this.rules.block.hr.test(e3)) break;
        p3 = t3[0], e3 = e3.substring(p3.length);
        let d3 = fe(t3[2].split(`
`, 1)[0], t3[1].length), h3 = e3.split(`
`, 1)[0], R = !d3.trim(), f4 = 0;
        if (this.options.pedantic ? (f4 = 2, c3 = d3.trimStart()) : R ? f4 = t3[1].length + 1 : (f4 = d3.search(this.rules.other.nonSpaceChar), f4 = f4 > 4 ? 1 : f4, c3 = d3.slice(f4), f4 += t3[1].length), R && this.rules.other.blankLine.test(h3) && (p3 += h3 + `
`, e3 = e3.substring(h3.length + 1), l3 = true), !l3) {
          let S2 = this.rules.other.nextBulletRegex(f4), ee = this.rules.other.hrRegex(f4), te = this.rules.other.fencesBeginRegex(f4), ne = this.rules.other.headingBeginRegex(f4), xe = this.rules.other.htmlBeginRegex(f4), be = this.rules.other.blockquoteBeginRegex(f4);
          for (; e3; ) {
            let Z = e3.split(`
`, 1)[0], A3;
            if (h3 = Z, this.options.pedantic ? (h3 = h3.replace(this.rules.other.listReplaceNesting, "  "), A3 = h3) : A3 = h3.replace(this.rules.other.tabCharGlobal, "    "), te.test(h3) || ne.test(h3) || xe.test(h3) || be.test(h3) || S2.test(h3) || ee.test(h3)) break;
            if (A3.search(this.rules.other.nonSpaceChar) >= f4 || !h3.trim()) c3 += `
` + A3.slice(f4);
            else {
              if (R || d3.replace(this.rules.other.tabCharGlobal, "    ").search(this.rules.other.nonSpaceChar) >= 4 || te.test(d3) || ne.test(d3) || ee.test(d3)) break;
              c3 += `
` + h3;
            }
            R = !h3.trim(), p3 += Z + `
`, e3 = e3.substring(Z.length + 1), d3 = A3.slice(f4);
          }
        }
        i4.loose || (a3 ? i4.loose = true : this.rules.other.doubleBlankLine.test(p3) && (a3 = true)), i4.items.push({ type: "list_item", raw: p3, task: !!this.options.gfm && this.rules.other.listIsTask.test(c3), loose: false, text: c3, tokens: [] }), i4.raw += p3;
      }
      let o3 = i4.items.at(-1);
      if (o3) o3.raw = o3.raw.trimEnd(), o3.text = o3.text.trimEnd();
      else return;
      i4.raw = i4.raw.trimEnd();
      for (let l3 of i4.items) {
        if (this.lexer.state.top = false, l3.tokens = this.lexer.blockTokens(l3.text, []), l3.task) {
          if (l3.text = l3.text.replace(this.rules.other.listReplaceTask, ""), l3.tokens[0]?.type === "text" || l3.tokens[0]?.type === "paragraph") {
            l3.tokens[0].raw = l3.tokens[0].raw.replace(this.rules.other.listReplaceTask, ""), l3.tokens[0].text = l3.tokens[0].text.replace(this.rules.other.listReplaceTask, "");
            for (let c3 = this.lexer.inlineQueue.length - 1; c3 >= 0; c3--) if (this.rules.other.listIsTask.test(this.lexer.inlineQueue[c3].src)) {
              this.lexer.inlineQueue[c3].src = this.lexer.inlineQueue[c3].src.replace(this.rules.other.listReplaceTask, "");
              break;
            }
          }
          let p3 = this.rules.other.listTaskCheckbox.exec(l3.raw);
          if (p3) {
            let c3 = { type: "checkbox", raw: p3[0] + " ", checked: p3[0] !== "[ ]" };
            l3.checked = c3.checked, i4.loose ? l3.tokens[0] && ["paragraph", "text"].includes(l3.tokens[0].type) && "tokens" in l3.tokens[0] && l3.tokens[0].tokens ? (l3.tokens[0].raw = c3.raw + l3.tokens[0].raw, l3.tokens[0].text = c3.raw + l3.tokens[0].text, l3.tokens[0].tokens.unshift(c3)) : l3.tokens.unshift({ type: "paragraph", raw: c3.raw, text: c3.raw, tokens: [c3] }) : l3.tokens.unshift(c3);
          }
        }
        if (!i4.loose) {
          let p3 = l3.tokens.filter((d3) => d3.type === "space"), c3 = p3.length > 0 && p3.some((d3) => this.rules.other.anyLine.test(d3.raw));
          i4.loose = c3;
        }
      }
      if (i4.loose) for (let l3 of i4.items) {
        l3.loose = true;
        for (let p3 of l3.tokens) p3.type === "text" && (p3.type = "paragraph");
      }
      return i4;
    }
  }
  html(e3) {
    let t3 = this.rules.block.html.exec(e3);
    if (t3) {
      let n2 = Y(t3[0]);
      return { type: "html", block: true, raw: n2, pre: t3[1] === "pre" || t3[1] === "script" || t3[1] === "style", text: n2 };
    }
  }
  def(e3) {
    let t3 = this.rules.block.def.exec(e3);
    if (t3) {
      let n2 = t3[1].toLowerCase().replace(this.rules.other.multipleSpaceGlobal, " "), r3 = t3[2] ? t3[2].replace(this.rules.other.hrefBrackets, "$1").replace(this.rules.inline.anyPunctuation, "$1") : "", i4 = t3[3] ? t3[3].substring(1, t3[3].length - 1).replace(this.rules.inline.anyPunctuation, "$1") : t3[3];
      return { type: "def", tag: n2, raw: $2(t3[0], `
`), href: r3, title: i4 };
    }
  }
  table(e3) {
    let t3 = this.rules.block.table.exec(e3);
    if (!t3 || !this.rules.other.tableDelimiter.test(t3[2])) return;
    let n2 = V2(t3[1]), r3 = t3[2].replace(this.rules.other.tableAlignChars, "").split("|"), i4 = t3[3]?.trim() ? t3[3].replace(this.rules.other.tableRowBlankLine, "").split(`
`) : [], s3 = { type: "table", raw: $2(t3[0], `
`), header: [], align: [], rows: [] };
    if (n2.length === r3.length) {
      for (let a3 of r3) this.rules.other.tableAlignRight.test(a3) ? s3.align.push("right") : this.rules.other.tableAlignCenter.test(a3) ? s3.align.push("center") : this.rules.other.tableAlignLeft.test(a3) ? s3.align.push("left") : s3.align.push(null);
      for (let a3 = 0; a3 < n2.length; a3++) s3.header.push({ text: n2[a3], tokens: this.lexer.inline(n2[a3]), header: true, align: s3.align[a3] });
      for (let a3 of i4) s3.rows.push(V2(a3, s3.header.length).map((o3, l3) => ({ text: o3, tokens: this.lexer.inline(o3), header: false, align: s3.align[l3] })));
      return s3;
    }
  }
  lheading(e3) {
    let t3 = this.rules.block.lheading.exec(e3);
    if (t3) {
      let n2 = t3[1].trim();
      return { type: "heading", raw: $2(t3[0], `
`), depth: t3[2].charAt(0) === "=" ? 1 : 2, text: n2, tokens: this.lexer.inline(n2) };
    }
  }
  paragraph(e3) {
    let t3 = this.rules.block.paragraph.exec(e3);
    if (t3) {
      let n2 = t3[1].charAt(t3[1].length - 1) === `
` ? t3[1].slice(0, -1) : t3[1];
      return { type: "paragraph", raw: t3[0], text: n2, tokens: this.lexer.inline(n2) };
    }
  }
  text(e3) {
    let t3 = this.rules.block.text.exec(e3);
    if (t3) return { type: "text", raw: t3[0], text: t3[0], tokens: this.lexer.inline(t3[0]) };
  }
  escape(e3) {
    let t3 = this.rules.inline.escape.exec(e3);
    if (t3) return { type: "escape", raw: t3[0], text: t3[1] };
  }
  tag(e3) {
    let t3 = this.rules.inline.tag.exec(e3);
    if (t3) return !this.lexer.state.inLink && this.rules.other.startATag.test(t3[0]) ? this.lexer.state.inLink = true : this.lexer.state.inLink && this.rules.other.endATag.test(t3[0]) && (this.lexer.state.inLink = false), !this.lexer.state.inRawBlock && this.rules.other.startPreScriptTag.test(t3[0]) ? this.lexer.state.inRawBlock = true : this.lexer.state.inRawBlock && this.rules.other.endPreScriptTag.test(t3[0]) && (this.lexer.state.inRawBlock = false), { type: "html", raw: t3[0], inLink: this.lexer.state.inLink, inRawBlock: this.lexer.state.inRawBlock, block: false, text: t3[0] };
  }
  link(e3) {
    let t3 = this.rules.inline.link.exec(e3);
    if (t3) {
      let n2 = t3[2].trim();
      if (!this.options.pedantic && this.rules.other.startAngleBracket.test(n2)) {
        if (!this.rules.other.endAngleBracket.test(n2)) return;
        let s3 = $2(n2.slice(0, -1), "\\");
        if ((n2.length - s3.length) % 2 === 0) return;
      } else {
        let s3 = ge(t3[2], "()");
        if (s3 === -2) return;
        if (s3 > -1) {
          let o3 = (t3[0].indexOf("!") === 0 ? 5 : 4) + t3[1].length + s3;
          t3[2] = t3[2].substring(0, s3), t3[0] = t3[0].substring(0, o3).trim(), t3[3] = "";
        }
      }
      let r3 = t3[2], i4 = "";
      if (this.options.pedantic) {
        let s3 = this.rules.other.pedanticHrefTitle.exec(r3);
        s3 && (r3 = s3[1], i4 = s3[3]);
      } else i4 = t3[3] ? t3[3].slice(1, -1) : "";
      return r3 = r3.trim(), this.rules.other.startAngleBracket.test(r3) && (this.options.pedantic && !this.rules.other.endAngleBracket.test(n2) ? r3 = r3.slice(1) : r3 = r3.slice(1, -1)), me(t3, { href: r3 && r3.replace(this.rules.inline.anyPunctuation, "$1"), title: i4 && i4.replace(this.rules.inline.anyPunctuation, "$1") }, t3[0], this.lexer, this.rules);
    }
  }
  reflink(e3, t3) {
    let n2;
    if ((n2 = this.rules.inline.reflink.exec(e3)) || (n2 = this.rules.inline.nolink.exec(e3))) {
      let r3 = (n2[2] || n2[1]).replace(this.rules.other.multipleSpaceGlobal, " "), i4 = t3[r3.toLowerCase()];
      if (!i4) {
        let s3 = n2[0].charAt(0);
        return { type: "text", raw: s3, text: s3 };
      }
      return me(n2, i4, n2[0], this.lexer, this.rules);
    }
  }
  emStrong(e3, t3, n2 = "") {
    let r3 = this.rules.inline.emStrongLDelim.exec(e3);
    if (!r3 || !r3[1] && !r3[2] && !r3[3] && !r3[4] || r3[4] && n2.match(this.rules.other.unicodeAlphaNumeric)) return;
    if (!(r3[1] || r3[3] || "") || !n2 || this.rules.inline.punctuation.exec(n2)) {
      let s3 = [...r3[0]].length - 1, a3, o3, l3 = s3, p3 = 0, c3 = r3[0][0] === "*" ? this.rules.inline.emStrongRDelimAst : this.rules.inline.emStrongRDelimUnd;
      for (c3.lastIndex = 0, t3 = t3.slice(-1 * e3.length + s3); (r3 = c3.exec(t3)) !== null; ) {
        if (a3 = r3[1] || r3[2] || r3[3] || r3[4] || r3[5] || r3[6], !a3) continue;
        if (o3 = [...a3].length, r3[3] || r3[4]) {
          l3 += o3;
          continue;
        } else if ((r3[5] || r3[6]) && s3 % 3 && !((s3 + o3) % 3)) {
          p3 += o3;
          continue;
        }
        if (l3 -= o3, l3 > 0) continue;
        o3 = Math.min(o3, o3 + l3 + p3);
        let d3 = [...r3[0]][0].length, h3 = e3.slice(0, s3 + r3.index + d3 + o3);
        if (Math.min(s3, o3) % 2) {
          let f4 = h3.slice(1, -1);
          return { type: "em", raw: h3, text: f4, tokens: this.lexer.inlineTokens(f4) };
        }
        let R = h3.slice(2, -2);
        return { type: "strong", raw: h3, text: R, tokens: this.lexer.inlineTokens(R) };
      }
    }
  }
  codespan(e3) {
    let t3 = this.rules.inline.code.exec(e3);
    if (t3) {
      let n2 = t3[2].replace(this.rules.other.newLineCharGlobal, " "), r3 = this.rules.other.nonSpaceChar.test(n2), i4 = this.rules.other.startingSpaceChar.test(n2) && this.rules.other.endingSpaceChar.test(n2);
      return r3 && i4 && (n2 = n2.substring(1, n2.length - 1)), { type: "codespan", raw: t3[0], text: n2 };
    }
  }
  br(e3) {
    let t3 = this.rules.inline.br.exec(e3);
    if (t3) return { type: "br", raw: t3[0] };
  }
  del(e3, t3, n2 = "") {
    let r3 = this.rules.inline.delLDelim.exec(e3);
    if (!r3) return;
    if (!(r3[1] || "") || !n2 || this.rules.inline.punctuation.exec(n2)) {
      let s3 = [...r3[0]].length - 1, a3, o3, l3 = s3, p3 = this.rules.inline.delRDelim;
      for (p3.lastIndex = 0, t3 = t3.slice(-1 * e3.length + s3); (r3 = p3.exec(t3)) !== null; ) {
        if (a3 = r3[1] || r3[2] || r3[3] || r3[4] || r3[5] || r3[6], !a3 || (o3 = [...a3].length, o3 !== s3)) continue;
        if (r3[3] || r3[4]) {
          l3 += o3;
          continue;
        }
        if (l3 -= o3, l3 > 0) continue;
        o3 = Math.min(o3, o3 + l3);
        let c3 = [...r3[0]][0].length, d3 = e3.slice(0, s3 + r3.index + c3 + o3), h3 = d3.slice(s3, -s3);
        return { type: "del", raw: d3, text: h3, tokens: this.lexer.inlineTokens(h3) };
      }
    }
  }
  autolink(e3) {
    let t3 = this.rules.inline.autolink.exec(e3);
    if (t3) {
      let n2, r3;
      return t3[2] === "@" ? (n2 = t3[1], r3 = "mailto:" + n2) : (n2 = t3[1], r3 = n2), { type: "link", raw: t3[0], text: n2, href: r3, tokens: [{ type: "text", raw: n2, text: n2 }] };
    }
  }
  url(e3) {
    let t3;
    if (t3 = this.rules.inline.url.exec(e3)) {
      let n2, r3;
      if (t3[2] === "@") n2 = t3[0], r3 = "mailto:" + n2;
      else {
        let i4;
        do
          i4 = t3[0], t3[0] = this.rules.inline._backpedal.exec(t3[0])?.[0] ?? "";
        while (i4 !== t3[0]);
        n2 = t3[0], t3[1] === "www." ? r3 = "http://" + t3[0] : r3 = t3[0];
      }
      return { type: "link", raw: t3[0], text: n2, href: r3, tokens: [{ type: "text", raw: n2, text: n2 }] };
    }
  }
  inlineText(e3) {
    let t3 = this.rules.inline.text.exec(e3);
    if (t3) {
      let n2 = this.lexer.state.inRawBlock;
      return { type: "text", raw: t3[0], text: t3[0], escaped: n2 };
    }
  }
};
var x2 = class u4 {
  tokens;
  options;
  state;
  inlineQueue;
  tokenizer;
  constructor(e3) {
    this.tokens = [], this.tokens.links = /* @__PURE__ */ Object.create(null), this.options = e3 || T3, this.options.tokenizer = this.options.tokenizer || new w3(), this.tokenizer = this.options.tokenizer, this.tokenizer.options = this.options, this.tokenizer.lexer = this, this.inlineQueue = [], this.state = { inLink: false, inRawBlock: false, top: true };
    let t3 = { other: m2, block: B3.normal, inline: I2.normal };
    this.options.pedantic ? (t3.block = B3.pedantic, t3.inline = I2.pedantic) : this.options.gfm && (t3.block = B3.gfm, this.options.breaks ? t3.inline = I2.breaks : t3.inline = I2.gfm), this.tokenizer.rules = t3;
  }
  static get rules() {
    return { block: B3, inline: I2 };
  }
  static lex(e3, t3) {
    return new u4(t3).lex(e3);
  }
  static lexInline(e3, t3) {
    return new u4(t3).inlineTokens(e3);
  }
  lex(e3) {
    e3 = e3.replace(m2.carriageReturn, `
`), this.blockTokens(e3, this.tokens);
    for (let t3 = 0; t3 < this.inlineQueue.length; t3++) {
      let n2 = this.inlineQueue[t3];
      this.inlineTokens(n2.src, n2.tokens);
    }
    return this.inlineQueue = [], this.tokens;
  }
  blockTokens(e3, t3 = [], n2 = false) {
    for (this.tokenizer.lexer = this, this.options.pedantic && (e3 = e3.replace(m2.tabCharGlobal, "    ").replace(m2.spaceLine, "")); e3; ) {
      let r3;
      if (this.options.extensions?.block?.some((s3) => (r3 = s3.call({ lexer: this }, e3, t3)) ? (e3 = e3.substring(r3.raw.length), t3.push(r3), true) : false)) continue;
      if (r3 = this.tokenizer.space(e3)) {
        e3 = e3.substring(r3.raw.length);
        let s3 = t3.at(-1);
        r3.raw.length === 1 && s3 !== void 0 ? s3.raw += `
` : t3.push(r3);
        continue;
      }
      if (r3 = this.tokenizer.code(e3)) {
        e3 = e3.substring(r3.raw.length);
        let s3 = t3.at(-1);
        s3?.type === "paragraph" || s3?.type === "text" ? (s3.raw += (s3.raw.endsWith(`
`) ? "" : `
`) + r3.raw, s3.text += `
` + r3.text, this.inlineQueue.at(-1).src = s3.text) : t3.push(r3);
        continue;
      }
      if (r3 = this.tokenizer.fences(e3)) {
        e3 = e3.substring(r3.raw.length), t3.push(r3);
        continue;
      }
      if (r3 = this.tokenizer.heading(e3)) {
        e3 = e3.substring(r3.raw.length), t3.push(r3);
        continue;
      }
      if (r3 = this.tokenizer.hr(e3)) {
        e3 = e3.substring(r3.raw.length), t3.push(r3);
        continue;
      }
      if (r3 = this.tokenizer.blockquote(e3)) {
        e3 = e3.substring(r3.raw.length), t3.push(r3);
        continue;
      }
      if (r3 = this.tokenizer.list(e3)) {
        e3 = e3.substring(r3.raw.length), t3.push(r3);
        continue;
      }
      if (r3 = this.tokenizer.html(e3)) {
        e3 = e3.substring(r3.raw.length), t3.push(r3);
        continue;
      }
      if (r3 = this.tokenizer.def(e3)) {
        e3 = e3.substring(r3.raw.length);
        let s3 = t3.at(-1);
        s3?.type === "paragraph" || s3?.type === "text" ? (s3.raw += (s3.raw.endsWith(`
`) ? "" : `
`) + r3.raw, s3.text += `
` + r3.raw, this.inlineQueue.at(-1).src = s3.text) : this.tokens.links[r3.tag] || (this.tokens.links[r3.tag] = { href: r3.href, title: r3.title }, t3.push(r3));
        continue;
      }
      if (r3 = this.tokenizer.table(e3)) {
        e3 = e3.substring(r3.raw.length), t3.push(r3);
        continue;
      }
      if (r3 = this.tokenizer.lheading(e3)) {
        e3 = e3.substring(r3.raw.length), t3.push(r3);
        continue;
      }
      let i4 = e3;
      if (this.options.extensions?.startBlock) {
        let s3 = 1 / 0, a3 = e3.slice(1), o3;
        this.options.extensions.startBlock.forEach((l3) => {
          o3 = l3.call({ lexer: this }, a3), typeof o3 == "number" && o3 >= 0 && (s3 = Math.min(s3, o3));
        }), s3 < 1 / 0 && s3 >= 0 && (i4 = e3.substring(0, s3 + 1));
      }
      if (this.state.top && (r3 = this.tokenizer.paragraph(i4))) {
        let s3 = t3.at(-1);
        n2 && s3?.type === "paragraph" ? (s3.raw += (s3.raw.endsWith(`
`) ? "" : `
`) + r3.raw, s3.text += `
` + r3.text, this.inlineQueue.pop(), this.inlineQueue.at(-1).src = s3.text) : t3.push(r3), n2 = i4.length !== e3.length, e3 = e3.substring(r3.raw.length);
        continue;
      }
      if (r3 = this.tokenizer.text(e3)) {
        e3 = e3.substring(r3.raw.length);
        let s3 = t3.at(-1);
        s3?.type === "text" ? (s3.raw += (s3.raw.endsWith(`
`) ? "" : `
`) + r3.raw, s3.text += `
` + r3.text, this.inlineQueue.pop(), this.inlineQueue.at(-1).src = s3.text) : t3.push(r3);
        continue;
      }
      if (e3) {
        let s3 = "Infinite loop on byte: " + e3.charCodeAt(0);
        if (this.options.silent) {
          console.error(s3);
          break;
        } else throw new Error(s3);
      }
    }
    return this.state.top = true, t3;
  }
  inline(e3, t3 = []) {
    return this.inlineQueue.push({ src: e3, tokens: t3 }), t3;
  }
  inlineTokens(e3, t3 = []) {
    this.tokenizer.lexer = this;
    let n2 = e3, r3 = null;
    if (this.tokens.links) {
      let o3 = Object.keys(this.tokens.links);
      if (o3.length > 0) for (; (r3 = this.tokenizer.rules.inline.reflinkSearch.exec(n2)) !== null; ) o3.includes(r3[0].slice(r3[0].lastIndexOf("[") + 1, -1)) && (n2 = n2.slice(0, r3.index) + "[" + "a".repeat(r3[0].length - 2) + "]" + n2.slice(this.tokenizer.rules.inline.reflinkSearch.lastIndex));
    }
    for (; (r3 = this.tokenizer.rules.inline.anyPunctuation.exec(n2)) !== null; ) n2 = n2.slice(0, r3.index) + "++" + n2.slice(this.tokenizer.rules.inline.anyPunctuation.lastIndex);
    let i4;
    for (; (r3 = this.tokenizer.rules.inline.blockSkip.exec(n2)) !== null; ) i4 = r3[2] ? r3[2].length : 0, n2 = n2.slice(0, r3.index + i4) + "[" + "a".repeat(r3[0].length - i4 - 2) + "]" + n2.slice(this.tokenizer.rules.inline.blockSkip.lastIndex);
    n2 = this.options.hooks?.emStrongMask?.call({ lexer: this }, n2) ?? n2;
    let s3 = false, a3 = "";
    for (; e3; ) {
      s3 || (a3 = ""), s3 = false;
      let o3;
      if (this.options.extensions?.inline?.some((p3) => (o3 = p3.call({ lexer: this }, e3, t3)) ? (e3 = e3.substring(o3.raw.length), t3.push(o3), true) : false)) continue;
      if (o3 = this.tokenizer.escape(e3)) {
        e3 = e3.substring(o3.raw.length), t3.push(o3);
        continue;
      }
      if (o3 = this.tokenizer.tag(e3)) {
        e3 = e3.substring(o3.raw.length), t3.push(o3);
        continue;
      }
      if (o3 = this.tokenizer.link(e3)) {
        e3 = e3.substring(o3.raw.length), t3.push(o3);
        continue;
      }
      if (o3 = this.tokenizer.reflink(e3, this.tokens.links)) {
        e3 = e3.substring(o3.raw.length);
        let p3 = t3.at(-1);
        o3.type === "text" && p3?.type === "text" ? (p3.raw += o3.raw, p3.text += o3.text) : t3.push(o3);
        continue;
      }
      if (o3 = this.tokenizer.emStrong(e3, n2, a3)) {
        e3 = e3.substring(o3.raw.length), t3.push(o3);
        continue;
      }
      if (o3 = this.tokenizer.codespan(e3)) {
        e3 = e3.substring(o3.raw.length), t3.push(o3);
        continue;
      }
      if (o3 = this.tokenizer.br(e3)) {
        e3 = e3.substring(o3.raw.length), t3.push(o3);
        continue;
      }
      if (o3 = this.tokenizer.del(e3, n2, a3)) {
        e3 = e3.substring(o3.raw.length), t3.push(o3);
        continue;
      }
      if (o3 = this.tokenizer.autolink(e3)) {
        e3 = e3.substring(o3.raw.length), t3.push(o3);
        continue;
      }
      if (!this.state.inLink && (o3 = this.tokenizer.url(e3))) {
        e3 = e3.substring(o3.raw.length), t3.push(o3);
        continue;
      }
      let l3 = e3;
      if (this.options.extensions?.startInline) {
        let p3 = 1 / 0, c3 = e3.slice(1), d3;
        this.options.extensions.startInline.forEach((h3) => {
          d3 = h3.call({ lexer: this }, c3), typeof d3 == "number" && d3 >= 0 && (p3 = Math.min(p3, d3));
        }), p3 < 1 / 0 && p3 >= 0 && (l3 = e3.substring(0, p3 + 1));
      }
      if (o3 = this.tokenizer.inlineText(l3)) {
        e3 = e3.substring(o3.raw.length), o3.raw.slice(-1) !== "_" && (a3 = o3.raw.slice(-1)), s3 = true;
        let p3 = t3.at(-1);
        p3?.type === "text" ? (p3.raw += o3.raw, p3.text += o3.text) : t3.push(o3);
        continue;
      }
      if (e3) {
        let p3 = "Infinite loop on byte: " + e3.charCodeAt(0);
        if (this.options.silent) {
          console.error(p3);
          break;
        } else throw new Error(p3);
      }
    }
    return t3;
  }
};
var y3 = class {
  options;
  parser;
  constructor(e3) {
    this.options = e3 || T3;
  }
  space(e3) {
    return "";
  }
  code({ text: e3, lang: t3, escaped: n2 }) {
    let r3 = (t3 || "").match(m2.notSpaceStart)?.[0], i4 = e3.replace(m2.endingNewline, "") + `
`;
    return r3 ? '<pre><code class="language-' + O2(r3) + '">' + (n2 ? i4 : O2(i4, true)) + `</code></pre>
` : "<pre><code>" + (n2 ? i4 : O2(i4, true)) + `</code></pre>
`;
  }
  blockquote({ tokens: e3 }) {
    return `<blockquote>
${this.parser.parse(e3)}</blockquote>
`;
  }
  html({ text: e3 }) {
    return e3;
  }
  def(e3) {
    return "";
  }
  heading({ tokens: e3, depth: t3 }) {
    return `<h${t3}>${this.parser.parseInline(e3)}</h${t3}>
`;
  }
  hr(e3) {
    return `<hr>
`;
  }
  list(e3) {
    let t3 = e3.ordered, n2 = e3.start, r3 = "";
    for (let a3 = 0; a3 < e3.items.length; a3++) {
      let o3 = e3.items[a3];
      r3 += this.listitem(o3);
    }
    let i4 = t3 ? "ol" : "ul", s3 = t3 && n2 !== 1 ? ' start="' + n2 + '"' : "";
    return "<" + i4 + s3 + `>
` + r3 + "</" + i4 + `>
`;
  }
  listitem(e3) {
    return `<li>${this.parser.parse(e3.tokens)}</li>
`;
  }
  checkbox({ checked: e3 }) {
    return "<input " + (e3 ? 'checked="" ' : "") + 'disabled="" type="checkbox"> ';
  }
  paragraph({ tokens: e3 }) {
    return `<p>${this.parser.parseInline(e3)}</p>
`;
  }
  table(e3) {
    let t3 = "", n2 = "";
    for (let i4 = 0; i4 < e3.header.length; i4++) n2 += this.tablecell(e3.header[i4]);
    t3 += this.tablerow({ text: n2 });
    let r3 = "";
    for (let i4 = 0; i4 < e3.rows.length; i4++) {
      let s3 = e3.rows[i4];
      n2 = "";
      for (let a3 = 0; a3 < s3.length; a3++) n2 += this.tablecell(s3[a3]);
      r3 += this.tablerow({ text: n2 });
    }
    return r3 && (r3 = `<tbody>${r3}</tbody>`), `<table>
<thead>
` + t3 + `</thead>
` + r3 + `</table>
`;
  }
  tablerow({ text: e3 }) {
    return `<tr>
${e3}</tr>
`;
  }
  tablecell(e3) {
    let t3 = this.parser.parseInline(e3.tokens), n2 = e3.header ? "th" : "td";
    return (e3.align ? `<${n2} align="${e3.align}">` : `<${n2}>`) + t3 + `</${n2}>
`;
  }
  strong({ tokens: e3 }) {
    return `<strong>${this.parser.parseInline(e3)}</strong>`;
  }
  em({ tokens: e3 }) {
    return `<em>${this.parser.parseInline(e3)}</em>`;
  }
  codespan({ text: e3 }) {
    return `<code>${O2(e3, true)}</code>`;
  }
  br(e3) {
    return "<br>";
  }
  del({ tokens: e3 }) {
    return `<del>${this.parser.parseInline(e3)}</del>`;
  }
  link({ href: e3, title: t3, tokens: n2 }) {
    let r3 = this.parser.parseInline(n2), i4 = J(e3);
    if (i4 === null) return r3;
    e3 = i4;
    let s3 = '<a href="' + e3 + '"';
    return t3 && (s3 += ' title="' + O2(t3) + '"'), s3 += ">" + r3 + "</a>", s3;
  }
  image({ href: e3, title: t3, text: n2, tokens: r3 }) {
    r3 && (n2 = this.parser.parseInline(r3, this.parser.textRenderer));
    let i4 = J(e3);
    if (i4 === null) return O2(n2);
    e3 = i4;
    let s3 = `<img src="${e3}" alt="${O2(n2)}"`;
    return t3 && (s3 += ` title="${O2(t3)}"`), s3 += ">", s3;
  }
  text(e3) {
    return "tokens" in e3 && e3.tokens ? this.parser.parseInline(e3.tokens) : "escaped" in e3 && e3.escaped ? e3.text : O2(e3.text);
  }
};
var L2 = class {
  strong({ text: e3 }) {
    return e3;
  }
  em({ text: e3 }) {
    return e3;
  }
  codespan({ text: e3 }) {
    return e3;
  }
  del({ text: e3 }) {
    return e3;
  }
  html({ text: e3 }) {
    return e3;
  }
  text({ text: e3 }) {
    return e3;
  }
  link({ text: e3 }) {
    return "" + e3;
  }
  image({ text: e3 }) {
    return "" + e3;
  }
  br() {
    return "";
  }
  checkbox({ raw: e3 }) {
    return e3;
  }
};
var b2 = class u5 {
  options;
  renderer;
  textRenderer;
  constructor(e3) {
    this.options = e3 || T3, this.options.renderer = this.options.renderer || new y3(), this.renderer = this.options.renderer, this.renderer.options = this.options, this.renderer.parser = this, this.textRenderer = new L2();
  }
  static parse(e3, t3) {
    return new u5(t3).parse(e3);
  }
  static parseInline(e3, t3) {
    return new u5(t3).parseInline(e3);
  }
  parse(e3) {
    this.renderer.parser = this;
    let t3 = "";
    for (let n2 = 0; n2 < e3.length; n2++) {
      let r3 = e3[n2];
      if (this.options.extensions?.renderers?.[r3.type]) {
        let s3 = r3, a3 = this.options.extensions.renderers[s3.type].call({ parser: this }, s3);
        if (a3 !== false || !["space", "hr", "heading", "code", "table", "blockquote", "list", "html", "def", "paragraph", "text"].includes(s3.type)) {
          t3 += a3 || "";
          continue;
        }
      }
      let i4 = r3;
      switch (i4.type) {
        case "space": {
          t3 += this.renderer.space(i4);
          break;
        }
        case "hr": {
          t3 += this.renderer.hr(i4);
          break;
        }
        case "heading": {
          t3 += this.renderer.heading(i4);
          break;
        }
        case "code": {
          t3 += this.renderer.code(i4);
          break;
        }
        case "table": {
          t3 += this.renderer.table(i4);
          break;
        }
        case "blockquote": {
          t3 += this.renderer.blockquote(i4);
          break;
        }
        case "list": {
          t3 += this.renderer.list(i4);
          break;
        }
        case "checkbox": {
          t3 += this.renderer.checkbox(i4);
          break;
        }
        case "html": {
          t3 += this.renderer.html(i4);
          break;
        }
        case "def": {
          t3 += this.renderer.def(i4);
          break;
        }
        case "paragraph": {
          t3 += this.renderer.paragraph(i4);
          break;
        }
        case "text": {
          t3 += this.renderer.text(i4);
          break;
        }
        default: {
          let s3 = 'Token with "' + i4.type + '" type was not found.';
          if (this.options.silent) return console.error(s3), "";
          throw new Error(s3);
        }
      }
    }
    return t3;
  }
  parseInline(e3, t3 = this.renderer) {
    this.renderer.parser = this;
    let n2 = "";
    for (let r3 = 0; r3 < e3.length; r3++) {
      let i4 = e3[r3];
      if (this.options.extensions?.renderers?.[i4.type]) {
        let a3 = this.options.extensions.renderers[i4.type].call({ parser: this }, i4);
        if (a3 !== false || !["escape", "html", "link", "image", "strong", "em", "codespan", "br", "del", "text"].includes(i4.type)) {
          n2 += a3 || "";
          continue;
        }
      }
      let s3 = i4;
      switch (s3.type) {
        case "escape": {
          n2 += t3.text(s3);
          break;
        }
        case "html": {
          n2 += t3.html(s3);
          break;
        }
        case "link": {
          n2 += t3.link(s3);
          break;
        }
        case "image": {
          n2 += t3.image(s3);
          break;
        }
        case "checkbox": {
          n2 += t3.checkbox(s3);
          break;
        }
        case "strong": {
          n2 += t3.strong(s3);
          break;
        }
        case "em": {
          n2 += t3.em(s3);
          break;
        }
        case "codespan": {
          n2 += t3.codespan(s3);
          break;
        }
        case "br": {
          n2 += t3.br(s3);
          break;
        }
        case "del": {
          n2 += t3.del(s3);
          break;
        }
        case "text": {
          n2 += t3.text(s3);
          break;
        }
        default: {
          let a3 = 'Token with "' + s3.type + '" type was not found.';
          if (this.options.silent) return console.error(a3), "";
          throw new Error(a3);
        }
      }
    }
    return n2;
  }
};
var P2 = class {
  options;
  block;
  constructor(e3) {
    this.options = e3 || T3;
  }
  static passThroughHooks = /* @__PURE__ */ new Set(["preprocess", "postprocess", "processAllTokens", "emStrongMask"]);
  static passThroughHooksRespectAsync = /* @__PURE__ */ new Set(["preprocess", "postprocess", "processAllTokens"]);
  preprocess(e3) {
    return e3;
  }
  postprocess(e3) {
    return e3;
  }
  processAllTokens(e3) {
    return e3;
  }
  emStrongMask(e3) {
    return e3;
  }
  provideLexer(e3 = this.block) {
    return e3 ? x2.lex : x2.lexInline;
  }
  provideParser(e3 = this.block) {
    return e3 ? b2.parse : b2.parseInline;
  }
};
var D2 = class {
  defaults = z3();
  options = this.setOptions;
  parse = this.parseMarkdown(true);
  parseInline = this.parseMarkdown(false);
  Parser = b2;
  Renderer = y3;
  TextRenderer = L2;
  Lexer = x2;
  Tokenizer = w3;
  Hooks = P2;
  constructor(...e3) {
    this.use(...e3);
  }
  walkTokens(e3, t3) {
    let n2 = [];
    for (let r3 of e3) switch (n2 = n2.concat(t3.call(this, r3)), r3.type) {
      case "table": {
        let i4 = r3;
        for (let s3 of i4.header) n2 = n2.concat(this.walkTokens(s3.tokens, t3));
        for (let s3 of i4.rows) for (let a3 of s3) n2 = n2.concat(this.walkTokens(a3.tokens, t3));
        break;
      }
      case "list": {
        let i4 = r3;
        n2 = n2.concat(this.walkTokens(i4.items, t3));
        break;
      }
      default: {
        let i4 = r3;
        this.defaults.extensions?.childTokens?.[i4.type] ? this.defaults.extensions.childTokens[i4.type].forEach((s3) => {
          let a3 = i4[s3].flat(1 / 0);
          n2 = n2.concat(this.walkTokens(a3, t3));
        }) : i4.tokens && (n2 = n2.concat(this.walkTokens(i4.tokens, t3)));
      }
    }
    return n2;
  }
  use(...e3) {
    let t3 = this.defaults.extensions || { renderers: {}, childTokens: {} };
    return e3.forEach((n2) => {
      let r3 = { ...n2 };
      if (r3.async = this.defaults.async || r3.async || false, n2.extensions && (n2.extensions.forEach((i4) => {
        if (!i4.name) throw new Error("extension name required");
        if ("renderer" in i4) {
          let s3 = t3.renderers[i4.name];
          s3 ? t3.renderers[i4.name] = function(...a3) {
            let o3 = i4.renderer.apply(this, a3);
            return o3 === false && (o3 = s3.apply(this, a3)), o3;
          } : t3.renderers[i4.name] = i4.renderer;
        }
        if ("tokenizer" in i4) {
          if (!i4.level || i4.level !== "block" && i4.level !== "inline") throw new Error("extension level must be 'block' or 'inline'");
          let s3 = t3[i4.level];
          s3 ? s3.unshift(i4.tokenizer) : t3[i4.level] = [i4.tokenizer], i4.start && (i4.level === "block" ? t3.startBlock ? t3.startBlock.push(i4.start) : t3.startBlock = [i4.start] : i4.level === "inline" && (t3.startInline ? t3.startInline.push(i4.start) : t3.startInline = [i4.start]));
        }
        "childTokens" in i4 && i4.childTokens && (t3.childTokens[i4.name] = i4.childTokens);
      }), r3.extensions = t3), n2.renderer) {
        let i4 = this.defaults.renderer || new y3(this.defaults);
        for (let s3 in n2.renderer) {
          if (!(s3 in i4)) throw new Error(`renderer '${s3}' does not exist`);
          if (["options", "parser"].includes(s3)) continue;
          let a3 = s3, o3 = n2.renderer[a3], l3 = i4[a3];
          i4[a3] = (...p3) => {
            let c3 = o3.apply(i4, p3);
            return c3 === false && (c3 = l3.apply(i4, p3)), c3 || "";
          };
        }
        r3.renderer = i4;
      }
      if (n2.tokenizer) {
        let i4 = this.defaults.tokenizer || new w3(this.defaults);
        for (let s3 in n2.tokenizer) {
          if (!(s3 in i4)) throw new Error(`tokenizer '${s3}' does not exist`);
          if (["options", "rules", "lexer"].includes(s3)) continue;
          let a3 = s3, o3 = n2.tokenizer[a3], l3 = i4[a3];
          i4[a3] = (...p3) => {
            let c3 = o3.apply(i4, p3);
            return c3 === false && (c3 = l3.apply(i4, p3)), c3;
          };
        }
        r3.tokenizer = i4;
      }
      if (n2.hooks) {
        let i4 = this.defaults.hooks || new P2();
        for (let s3 in n2.hooks) {
          if (!(s3 in i4)) throw new Error(`hook '${s3}' does not exist`);
          if (["options", "block"].includes(s3)) continue;
          let a3 = s3, o3 = n2.hooks[a3], l3 = i4[a3];
          P2.passThroughHooks.has(s3) ? i4[a3] = (p3) => {
            if (this.defaults.async && P2.passThroughHooksRespectAsync.has(s3)) return (async () => {
              let d3 = await o3.call(i4, p3);
              return l3.call(i4, d3);
            })();
            let c3 = o3.call(i4, p3);
            return l3.call(i4, c3);
          } : i4[a3] = (...p3) => {
            if (this.defaults.async) return (async () => {
              let d3 = await o3.apply(i4, p3);
              return d3 === false && (d3 = await l3.apply(i4, p3)), d3;
            })();
            let c3 = o3.apply(i4, p3);
            return c3 === false && (c3 = l3.apply(i4, p3)), c3;
          };
        }
        r3.hooks = i4;
      }
      if (n2.walkTokens) {
        let i4 = this.defaults.walkTokens, s3 = n2.walkTokens;
        r3.walkTokens = function(a3) {
          let o3 = [];
          return o3.push(s3.call(this, a3)), i4 && (o3 = o3.concat(i4.call(this, a3))), o3;
        };
      }
      this.defaults = { ...this.defaults, ...r3 };
    }), this;
  }
  setOptions(e3) {
    return this.defaults = { ...this.defaults, ...e3 }, this;
  }
  lexer(e3, t3) {
    return x2.lex(e3, t3 ?? this.defaults);
  }
  parser(e3, t3) {
    return b2.parse(e3, t3 ?? this.defaults);
  }
  parseMarkdown(e3) {
    return (n2, r3) => {
      let i4 = { ...r3 }, s3 = { ...this.defaults, ...i4 }, a3 = this.onError(!!s3.silent, !!s3.async);
      if (this.defaults.async === true && i4.async === false) return a3(new Error("marked(): The async option was set to true by an extension. Remove async: false from the parse options object to return a Promise."));
      if (typeof n2 > "u" || n2 === null) return a3(new Error("marked(): input parameter is undefined or null"));
      if (typeof n2 != "string") return a3(new Error("marked(): input parameter is of type " + Object.prototype.toString.call(n2) + ", string expected"));
      if (s3.hooks && (s3.hooks.options = s3, s3.hooks.block = e3), s3.async) return (async () => {
        let o3 = s3.hooks ? await s3.hooks.preprocess(n2) : n2, p3 = await (s3.hooks ? await s3.hooks.provideLexer(e3) : e3 ? x2.lex : x2.lexInline)(o3, s3), c3 = s3.hooks ? await s3.hooks.processAllTokens(p3) : p3;
        s3.walkTokens && await Promise.all(this.walkTokens(c3, s3.walkTokens));
        let h3 = await (s3.hooks ? await s3.hooks.provideParser(e3) : e3 ? b2.parse : b2.parseInline)(c3, s3);
        return s3.hooks ? await s3.hooks.postprocess(h3) : h3;
      })().catch(a3);
      try {
        s3.hooks && (n2 = s3.hooks.preprocess(n2));
        let l3 = (s3.hooks ? s3.hooks.provideLexer(e3) : e3 ? x2.lex : x2.lexInline)(n2, s3);
        s3.hooks && (l3 = s3.hooks.processAllTokens(l3)), s3.walkTokens && this.walkTokens(l3, s3.walkTokens);
        let c3 = (s3.hooks ? s3.hooks.provideParser(e3) : e3 ? b2.parse : b2.parseInline)(l3, s3);
        return s3.hooks && (c3 = s3.hooks.postprocess(c3)), c3;
      } catch (o3) {
        return a3(o3);
      }
    };
  }
  onError(e3, t3) {
    return (n2) => {
      if (n2.message += `
Please report this to https://github.com/markedjs/marked.`, e3) {
        let r3 = "<p>An error occurred:</p><pre>" + O2(n2.message + "", true) + "</pre>";
        return t3 ? Promise.resolve(r3) : r3;
      }
      if (t3) return Promise.reject(n2);
      throw n2;
    };
  }
};
var M2 = new D2();
function g2(u6, e3) {
  return M2.parse(u6, e3);
}
g2.options = g2.setOptions = function(u6) {
  return M2.setOptions(u6), g2.defaults = M2.defaults, G(g2.defaults), g2;
};
g2.getDefaults = z3;
g2.defaults = T3;
g2.use = function(...u6) {
  return M2.use(...u6), g2.defaults = M2.defaults, G(g2.defaults), g2;
};
g2.walkTokens = function(u6, e3) {
  return M2.walkTokens(u6, e3);
};
g2.parseInline = M2.parseInline;
g2.Parser = b2;
g2.parser = b2.parse;
g2.Renderer = y3;
g2.TextRenderer = L2;
g2.Lexer = x2;
g2.lexer = x2.lex;
g2.Tokenizer = w3;
g2.Hooks = P2;
g2.parse = g2;
var jt = g2.options;
var Ft = g2.setOptions;
var Ut = g2.use;
var Kt = g2.walkTokens;
var Wt = g2.parseInline;
var Jt = b2.parse;
var Vt = x2.lex;

// node_modules/dompurify/dist/purify.es.mjs
function _arrayLikeToArray(r3, a3) {
  (null == a3 || a3 > r3.length) && (a3 = r3.length);
  for (var e3 = 0, n2 = Array(a3); e3 < a3; e3++) n2[e3] = r3[e3];
  return n2;
}
function _arrayWithHoles(r3) {
  if (Array.isArray(r3)) return r3;
}
function _iterableToArrayLimit(r3, l3) {
  var t3 = null == r3 ? null : "undefined" != typeof Symbol && r3[Symbol.iterator] || r3["@@iterator"];
  if (null != t3) {
    var e3, n2, i4, u6, a3 = [], f4 = true, o3 = false;
    try {
      if (i4 = (t3 = t3.call(r3)).next, 0 === l3) ;
      else for (; !(f4 = (e3 = i4.call(t3)).done) && (a3.push(e3.value), a3.length !== l3); f4 = true) ;
    } catch (r4) {
      o3 = true, n2 = r4;
    } finally {
      try {
        if (!f4 && null != t3.return && (u6 = t3.return(), Object(u6) !== u6)) return;
      } finally {
        if (o3) throw n2;
      }
    }
    return a3;
  }
}
function _nonIterableRest() {
  throw new TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
}
function _slicedToArray(r3, e3) {
  return _arrayWithHoles(r3) || _iterableToArrayLimit(r3, e3) || _unsupportedIterableToArray(r3, e3) || _nonIterableRest();
}
function _unsupportedIterableToArray(r3, a3) {
  if (r3) {
    if ("string" == typeof r3) return _arrayLikeToArray(r3, a3);
    var t3 = {}.toString.call(r3).slice(8, -1);
    return "Object" === t3 && r3.constructor && (t3 = r3.constructor.name), "Map" === t3 || "Set" === t3 ? Array.from(r3) : "Arguments" === t3 || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(t3) ? _arrayLikeToArray(r3, a3) : void 0;
  }
}
var entries = Object.entries;
var setPrototypeOf = Object.setPrototypeOf;
var isFrozen = Object.isFrozen;
var getPrototypeOf = Object.getPrototypeOf;
var getOwnPropertyDescriptor = Object.getOwnPropertyDescriptor;
var freeze = Object.freeze;
var seal = Object.seal;
var create = Object.create;
var _ref = typeof Reflect !== "undefined" && Reflect;
var apply = _ref.apply;
var construct = _ref.construct;
if (!freeze) {
  freeze = function freeze2(x3) {
    return x3;
  };
}
if (!seal) {
  seal = function seal2(x3) {
    return x3;
  };
}
if (!apply) {
  apply = function apply2(func, thisArg) {
    for (var _len = arguments.length, args = new Array(_len > 2 ? _len - 2 : 0), _key = 2; _key < _len; _key++) {
      args[_key - 2] = arguments[_key];
    }
    return func.apply(thisArg, args);
  };
}
if (!construct) {
  construct = function construct2(Func) {
    for (var _len2 = arguments.length, args = new Array(_len2 > 1 ? _len2 - 1 : 0), _key2 = 1; _key2 < _len2; _key2++) {
      args[_key2 - 1] = arguments[_key2];
    }
    return new Func(...args);
  };
}
var arrayForEach = unapply(Array.prototype.forEach);
var arrayLastIndexOf = unapply(Array.prototype.lastIndexOf);
var arrayPop = unapply(Array.prototype.pop);
var arrayPush = unapply(Array.prototype.push);
var arraySplice = unapply(Array.prototype.splice);
var arrayIsArray = Array.isArray;
var stringToLowerCase = unapply(String.prototype.toLowerCase);
var stringToString = unapply(String.prototype.toString);
var stringMatch = unapply(String.prototype.match);
var stringReplace = unapply(String.prototype.replace);
var stringIndexOf = unapply(String.prototype.indexOf);
var stringTrim = unapply(String.prototype.trim);
var numberToString = unapply(Number.prototype.toString);
var booleanToString = unapply(Boolean.prototype.toString);
var bigintToString = typeof BigInt === "undefined" ? null : unapply(BigInt.prototype.toString);
var symbolToString = typeof Symbol === "undefined" ? null : unapply(Symbol.prototype.toString);
var objectHasOwnProperty = unapply(Object.prototype.hasOwnProperty);
var objectToString = unapply(Object.prototype.toString);
var regExpTest = unapply(RegExp.prototype.test);
var typeErrorCreate = unconstruct(TypeError);
function unapply(func) {
  return function(thisArg) {
    if (thisArg instanceof RegExp) {
      thisArg.lastIndex = 0;
    }
    for (var _len3 = arguments.length, args = new Array(_len3 > 1 ? _len3 - 1 : 0), _key3 = 1; _key3 < _len3; _key3++) {
      args[_key3 - 1] = arguments[_key3];
    }
    return apply(func, thisArg, args);
  };
}
function unconstruct(Func) {
  return function() {
    for (var _len4 = arguments.length, args = new Array(_len4), _key4 = 0; _key4 < _len4; _key4++) {
      args[_key4] = arguments[_key4];
    }
    return construct(Func, args);
  };
}
function addToSet(set, array) {
  let transformCaseFunc = arguments.length > 2 && arguments[2] !== void 0 ? arguments[2] : stringToLowerCase;
  if (setPrototypeOf) {
    setPrototypeOf(set, null);
  }
  if (!arrayIsArray(array)) {
    return set;
  }
  let l3 = array.length;
  while (l3--) {
    let element = array[l3];
    if (typeof element === "string") {
      const lcElement = transformCaseFunc(element);
      if (lcElement !== element) {
        if (!isFrozen(array)) {
          array[l3] = lcElement;
        }
        element = lcElement;
      }
    }
    set[element] = true;
  }
  return set;
}
function cleanArray(array) {
  for (let index = 0; index < array.length; index++) {
    const isPropertyExist = objectHasOwnProperty(array, index);
    if (!isPropertyExist) {
      array[index] = null;
    }
  }
  return array;
}
function clone(object) {
  const newObject = create(null);
  for (const _ref2 of entries(object)) {
    var _ref3 = _slicedToArray(_ref2, 2);
    const property = _ref3[0];
    const value = _ref3[1];
    const isPropertyExist = objectHasOwnProperty(object, property);
    if (isPropertyExist) {
      if (arrayIsArray(value)) {
        newObject[property] = cleanArray(value);
      } else if (value && typeof value === "object" && value.constructor === Object) {
        newObject[property] = clone(value);
      } else {
        newObject[property] = value;
      }
    }
  }
  return newObject;
}
function stringifyValue(value) {
  switch (typeof value) {
    case "string": {
      return value;
    }
    case "number": {
      return numberToString(value);
    }
    case "boolean": {
      return booleanToString(value);
    }
    case "bigint": {
      return bigintToString ? bigintToString(value) : "0";
    }
    case "symbol": {
      return symbolToString ? symbolToString(value) : "Symbol()";
    }
    case "undefined": {
      return objectToString(value);
    }
    case "function":
    case "object": {
      if (value === null) {
        return objectToString(value);
      }
      const valueAsRecord = value;
      const valueToString = lookupGetter(valueAsRecord, "toString");
      if (typeof valueToString === "function") {
        const stringified = valueToString(valueAsRecord);
        return typeof stringified === "string" ? stringified : objectToString(stringified);
      }
      return objectToString(value);
    }
    default: {
      return objectToString(value);
    }
  }
}
function lookupGetter(object, prop) {
  while (object !== null) {
    const desc = getOwnPropertyDescriptor(object, prop);
    if (desc) {
      if (desc.get) {
        return unapply(desc.get);
      }
      if (typeof desc.value === "function") {
        return unapply(desc.value);
      }
    }
    object = getPrototypeOf(object);
  }
  function fallbackValue() {
    return null;
  }
  return fallbackValue;
}
function isRegex(value) {
  try {
    regExpTest(value, "");
    return true;
  } catch (_unused) {
    return false;
  }
}
var html$1 = freeze(["a", "abbr", "acronym", "address", "area", "article", "aside", "audio", "b", "bdi", "bdo", "big", "blink", "blockquote", "body", "br", "button", "canvas", "caption", "center", "cite", "code", "col", "colgroup", "content", "data", "datalist", "dd", "decorator", "del", "details", "dfn", "dialog", "dir", "div", "dl", "dt", "element", "em", "fieldset", "figcaption", "figure", "font", "footer", "form", "h1", "h2", "h3", "h4", "h5", "h6", "head", "header", "hgroup", "hr", "html", "i", "img", "input", "ins", "kbd", "label", "legend", "li", "main", "map", "mark", "marquee", "menu", "menuitem", "meter", "nav", "nobr", "ol", "optgroup", "option", "output", "p", "picture", "pre", "progress", "q", "rp", "rt", "ruby", "s", "samp", "search", "section", "select", "shadow", "slot", "small", "source", "spacer", "span", "strike", "strong", "style", "sub", "summary", "sup", "table", "tbody", "td", "template", "textarea", "tfoot", "th", "thead", "time", "tr", "track", "tt", "u", "ul", "var", "video", "wbr"]);
var svg$1 = freeze(["svg", "a", "altglyph", "altglyphdef", "altglyphitem", "animatecolor", "animatemotion", "animatetransform", "circle", "clippath", "defs", "desc", "ellipse", "enterkeyhint", "exportparts", "filter", "font", "g", "glyph", "glyphref", "hkern", "image", "inputmode", "line", "lineargradient", "marker", "mask", "metadata", "mpath", "part", "path", "pattern", "polygon", "polyline", "radialgradient", "rect", "stop", "style", "switch", "symbol", "text", "textpath", "title", "tref", "tspan", "view", "vkern"]);
var svgFilters = freeze(["feBlend", "feColorMatrix", "feComponentTransfer", "feComposite", "feConvolveMatrix", "feDiffuseLighting", "feDisplacementMap", "feDistantLight", "feDropShadow", "feFlood", "feFuncA", "feFuncB", "feFuncG", "feFuncR", "feGaussianBlur", "feImage", "feMerge", "feMergeNode", "feMorphology", "feOffset", "fePointLight", "feSpecularLighting", "feSpotLight", "feTile", "feTurbulence"]);
var svgDisallowed = freeze(["animate", "color-profile", "cursor", "discard", "font-face", "font-face-format", "font-face-name", "font-face-src", "font-face-uri", "foreignobject", "hatch", "hatchpath", "mesh", "meshgradient", "meshpatch", "meshrow", "missing-glyph", "script", "set", "solidcolor", "unknown", "use"]);
var mathMl$1 = freeze(["math", "menclose", "merror", "mfenced", "mfrac", "mglyph", "mi", "mlabeledtr", "mmultiscripts", "mn", "mo", "mover", "mpadded", "mphantom", "mroot", "mrow", "ms", "mspace", "msqrt", "mstyle", "msub", "msup", "msubsup", "mtable", "mtd", "mtext", "mtr", "munder", "munderover", "mprescripts"]);
var mathMlDisallowed = freeze(["maction", "maligngroup", "malignmark", "mlongdiv", "mscarries", "mscarry", "msgroup", "mstack", "msline", "msrow", "semantics", "annotation", "annotation-xml", "mprescripts", "none"]);
var text = freeze(["#text"]);
var html = freeze(["accept", "action", "align", "alt", "autocapitalize", "autocomplete", "autopictureinpicture", "autoplay", "background", "bgcolor", "border", "capture", "cellpadding", "cellspacing", "checked", "cite", "class", "clear", "color", "cols", "colspan", "command", "commandfor", "controls", "controlslist", "coords", "crossorigin", "datetime", "decoding", "default", "dir", "disabled", "disablepictureinpicture", "disableremoteplayback", "download", "draggable", "enctype", "enterkeyhint", "exportparts", "face", "for", "headers", "height", "hidden", "high", "href", "hreflang", "id", "inert", "inputmode", "integrity", "ismap", "kind", "label", "lang", "list", "loading", "loop", "low", "max", "maxlength", "media", "method", "min", "minlength", "multiple", "muted", "name", "nonce", "noshade", "novalidate", "nowrap", "open", "optimum", "part", "pattern", "placeholder", "playsinline", "popover", "popovertarget", "popovertargetaction", "poster", "preload", "pubdate", "radiogroup", "readonly", "rel", "required", "rev", "reversed", "role", "rows", "rowspan", "spellcheck", "scope", "selected", "shape", "size", "sizes", "slot", "span", "srclang", "start", "src", "srcset", "step", "style", "summary", "tabindex", "title", "translate", "type", "usemap", "valign", "value", "width", "wrap", "xmlns"]);
var svg = freeze(["accent-height", "accumulate", "additive", "alignment-baseline", "amplitude", "ascent", "attributename", "attributetype", "azimuth", "basefrequency", "baseline-shift", "begin", "bias", "by", "class", "clip", "clippathunits", "clip-path", "clip-rule", "color", "color-interpolation", "color-interpolation-filters", "color-profile", "color-rendering", "cx", "cy", "d", "dx", "dy", "diffuseconstant", "direction", "display", "divisor", "dominant-baseline", "dur", "edgemode", "elevation", "end", "exponent", "fill", "fill-opacity", "fill-rule", "filter", "filterunits", "flood-color", "flood-opacity", "font-family", "font-size", "font-size-adjust", "font-stretch", "font-style", "font-variant", "font-weight", "fx", "fy", "g1", "g2", "glyph-name", "glyphref", "gradientunits", "gradienttransform", "height", "href", "id", "image-rendering", "in", "in2", "intercept", "k", "k1", "k2", "k3", "k4", "kerning", "keypoints", "keysplines", "keytimes", "lang", "lengthadjust", "letter-spacing", "kernelmatrix", "kernelunitlength", "lighting-color", "local", "marker-end", "marker-mid", "marker-start", "markerheight", "markerunits", "markerwidth", "maskcontentunits", "maskunits", "max", "mask", "mask-type", "media", "method", "mode", "min", "name", "numoctaves", "offset", "operator", "opacity", "order", "orient", "orientation", "origin", "overflow", "paint-order", "path", "pathlength", "patterncontentunits", "patterntransform", "patternunits", "pointer-events", "points", "preservealpha", "preserveaspectratio", "primitiveunits", "r", "rx", "ry", "radius", "refx", "refy", "repeatcount", "repeatdur", "restart", "result", "rotate", "scale", "seed", "shape-rendering", "slope", "specularconstant", "specularexponent", "spreadmethod", "startoffset", "stddeviation", "stitchtiles", "stop-color", "stop-opacity", "stroke-dasharray", "stroke-dashoffset", "stroke-linecap", "stroke-linejoin", "stroke-miterlimit", "stroke-opacity", "stroke", "stroke-width", "style", "surfacescale", "systemlanguage", "tabindex", "tablevalues", "targetx", "targety", "transform", "transform-origin", "text-anchor", "text-decoration", "text-orientation", "text-rendering", "textlength", "type", "u1", "u2", "unicode", "values", "vector-effect", "viewbox", "visibility", "version", "vert-adv-y", "vert-origin-x", "vert-origin-y", "width", "word-spacing", "wrap", "writing-mode", "xchannelselector", "ychannelselector", "x", "x1", "x2", "xmlns", "y", "y1", "y2", "z", "zoomandpan"]);
var mathMl = freeze(["accent", "accentunder", "align", "bevelled", "close", "columnalign", "columnlines", "columnspacing", "columnspan", "denomalign", "depth", "dir", "display", "displaystyle", "encoding", "fence", "frame", "height", "href", "id", "largeop", "length", "linethickness", "lquote", "lspace", "mathbackground", "mathcolor", "mathsize", "mathvariant", "maxsize", "minsize", "movablelimits", "notation", "numalign", "open", "rowalign", "rowlines", "rowspacing", "rowspan", "rspace", "rquote", "scriptlevel", "scriptminsize", "scriptsizemultiplier", "selection", "separator", "separators", "stretchy", "subscriptshift", "supscriptshift", "symmetric", "voffset", "width", "xmlns"]);
var xml = freeze(["xlink:href", "xml:id", "xlink:title", "xml:space", "xmlns:xlink"]);
var MUSTACHE_EXPR = seal(/{{[\w\W]*|^[\w\W]*}}/g);
var ERB_EXPR = seal(/<%[\w\W]*|^[\w\W]*%>/g);
var TMPLIT_EXPR = seal(/\${[\w\W]*/g);
var DATA_ATTR = seal(/^data-[\-\w.\u00B7-\uFFFF]+$/);
var ARIA_ATTR = seal(/^aria-[\-\w]+$/);
var IS_ALLOWED_URI = seal(
  /^(?:(?:(?:f|ht)tps?|mailto|tel|callto|sms|cid|xmpp|matrix):|[^a-z]|[a-z+.\-]+(?:[^a-z+.\-:]|$))/i
  // eslint-disable-line no-useless-escape
);
var IS_SCRIPT_OR_DATA = seal(/^(?:\w+script|data):/i);
var ATTR_WHITESPACE = seal(
  /[\u0000-\u0020\u00A0\u1680\u180E\u2000-\u2029\u205F\u3000]/g
  // eslint-disable-line no-control-regex
);
var DOCTYPE_NAME = seal(/^html$/i);
var CUSTOM_ELEMENT = seal(/^[a-z][.\w]*(-[.\w]+)+$/i);
var ELEMENT_MARKUP_PROBE = seal(/<[/\w!]/g);
var COMMENT_MARKUP_PROBE = seal(/<[/\w]/g);
var FALLBACK_TAG_CLOSE = seal(/<\/no(script|embed|frames)/i);
var SELF_CLOSING_TAG = seal(/\/>/i);
var NODE_TYPE = {
  element: 1,
  attribute: 2,
  text: 3,
  cdataSection: 4,
  entityReference: 5,
  // Deprecated
  entityNode: 6,
  // Deprecated
  processingInstruction: 7,
  comment: 8,
  document: 9,
  documentType: 10,
  documentFragment: 11,
  notation: 12
  // Deprecated
};
var LITERAL_TEXT_ELEMENT_NAMES = ["style", "script", "xmp", "iframe", "noembed", "noframes", "plaintext", "noscript"];
var LITERAL_TEXT_ELEMENTS = freeze(addToSet({}, LITERAL_TEXT_ELEMENT_NAMES));
var LITERAL_TEXT_CLOSE = function() {
  const map = {};
  arrayForEach(LITERAL_TEXT_ELEMENT_NAMES, (name) => {
    map[name] = seal(new RegExp("</" + name + "(?=[\\t\\n\\f\\r />])", "i"));
  });
  return freeze(map);
}();
var getGlobal = function getGlobal2() {
  return typeof window === "undefined" ? null : window;
};
var _createTrustedTypesPolicy = function _createTrustedTypesPolicy2(trustedTypes, purifyHostElement) {
  if (typeof trustedTypes !== "object" || typeof trustedTypes.createPolicy !== "function") {
    return null;
  }
  let suffix = null;
  const ATTR_NAME = "data-tt-policy-suffix";
  if (purifyHostElement && purifyHostElement.hasAttribute(ATTR_NAME)) {
    suffix = purifyHostElement.getAttribute(ATTR_NAME);
  }
  const policyName = "dompurify" + (suffix ? "#" + suffix : "");
  try {
    return trustedTypes.createPolicy(policyName, {
      createHTML(html2) {
        return html2;
      },
      createScriptURL(scriptUrl) {
        return scriptUrl;
      }
    });
  } catch (_4) {
    console.warn("TrustedTypes policy " + policyName + " could not be created.");
    return null;
  }
};
var _createHooksMap = function _createHooksMap2() {
  return {
    afterSanitizeAttributes: [],
    afterSanitizeElements: [],
    afterSanitizeShadowDOM: [],
    beforeSanitizeAttributes: [],
    beforeSanitizeElements: [],
    beforeSanitizeShadowDOM: [],
    uponSanitizeAttribute: [],
    uponSanitizeElement: [],
    uponSanitizeShadowNode: []
  };
};
var _resolveSetOption = function _resolveSetOption2(cfg, key, fallback, options) {
  return objectHasOwnProperty(cfg, key) && arrayIsArray(cfg[key]) ? addToSet(options.base ? clone(options.base) : {}, cfg[key], options.transform) : fallback;
};
var _resolveObjectOption = function _resolveObjectOption2(cfg, key, makeFallback) {
  const value = objectHasOwnProperty(cfg, key) ? cfg[key] : void 0;
  return value && typeof value === "object" ? clone(value) : makeFallback();
};
function createDOMPurify() {
  let window2 = arguments.length > 0 && arguments[0] !== void 0 ? arguments[0] : getGlobal();
  const DOMPurify = (root) => createDOMPurify(root);
  DOMPurify.version = "3.4.14";
  DOMPurify.removed = [];
  if (!window2 || !window2.document || window2.document.nodeType !== NODE_TYPE.document || !window2.Element) {
    DOMPurify.isSupported = false;
    return DOMPurify;
  }
  let document2 = window2.document;
  const originalDocument = document2;
  const currentScript = originalDocument.currentScript;
  window2.DocumentFragment;
  const HTMLTemplateElement = window2.HTMLTemplateElement, Node = window2.Node, Element = window2.Element, NodeFilter = window2.NodeFilter, _window$NamedNodeMap = window2.NamedNodeMap;
  _window$NamedNodeMap === void 0 ? window2.NamedNodeMap || window2.MozNamedAttrMap : _window$NamedNodeMap;
  window2.HTMLFormElement;
  const DOMParser = window2.DOMParser, trustedTypes = window2.trustedTypes;
  const ElementPrototype = Element.prototype;
  const cloneNode = lookupGetter(ElementPrototype, "cloneNode");
  const remove = lookupGetter(ElementPrototype, "remove");
  const getNextSibling = lookupGetter(ElementPrototype, "nextSibling");
  const getChildNodes = lookupGetter(ElementPrototype, "childNodes");
  const getParentNode = lookupGetter(ElementPrototype, "parentNode");
  const getShadowRoot = lookupGetter(ElementPrototype, "shadowRoot");
  const getAttributes = lookupGetter(ElementPrototype, "attributes");
  const getNodeType = Node && Node.prototype ? lookupGetter(Node.prototype, "nodeType") : null;
  const getNodeName = Node && Node.prototype ? lookupGetter(Node.prototype, "nodeName") : null;
  const getOwnerDocument = Node && Node.prototype ? lookupGetter(Node.prototype, "ownerDocument") : null;
  const _readNodeType = function _readNodeType2(node) {
    return getNodeType ? getNodeType(node) : node.nodeType;
  };
  const _readNodeName = function _readNodeName2(node) {
    return getNodeName ? getNodeName(node) : node.nodeName;
  };
  if (typeof HTMLTemplateElement === "function") {
    const template = document2.createElement("template");
    if (template.content && template.content.ownerDocument) {
      document2 = template.content.ownerDocument;
    }
  }
  let trustedTypesPolicy;
  let emptyHTML = "";
  let defaultTrustedTypesPolicy;
  let defaultTrustedTypesPolicyResolved = false;
  let IN_TRUSTED_TYPES_POLICY = 0;
  const _assertNotInTrustedTypesPolicy = function _assertNotInTrustedTypesPolicy2() {
    if (IN_TRUSTED_TYPES_POLICY > 0) {
      throw typeErrorCreate('A configured TRUSTED_TYPES_POLICY callback (createHTML or createScriptURL) must not call DOMPurify.sanitize, as that causes infinite recursion. Do not pass a policy whose callbacks wrap DOMPurify as TRUSTED_TYPES_POLICY; see the "DOMPurify and Trusted Types" section of the README.');
    }
  };
  const _createTrustedHTML = function _createTrustedHTML2(html2) {
    _assertNotInTrustedTypesPolicy();
    IN_TRUSTED_TYPES_POLICY++;
    try {
      return trustedTypesPolicy.createHTML(html2);
    } finally {
      IN_TRUSTED_TYPES_POLICY--;
    }
  };
  const _createTrustedScriptURL = function _createTrustedScriptURL2(scriptUrl) {
    _assertNotInTrustedTypesPolicy();
    IN_TRUSTED_TYPES_POLICY++;
    try {
      return trustedTypesPolicy.createScriptURL(scriptUrl);
    } finally {
      IN_TRUSTED_TYPES_POLICY--;
    }
  };
  const _getDefaultTrustedTypesPolicy = function _getDefaultTrustedTypesPolicy2() {
    if (!defaultTrustedTypesPolicyResolved) {
      defaultTrustedTypesPolicy = _createTrustedTypesPolicy(trustedTypes, currentScript);
      defaultTrustedTypesPolicyResolved = true;
    }
    return defaultTrustedTypesPolicy;
  };
  const _document = document2, implementation = _document.implementation, createNodeIterator = _document.createNodeIterator, createDocumentFragment = _document.createDocumentFragment, getElementsByTagName = _document.getElementsByTagName;
  const importNode = originalDocument.importNode;
  let hooks = _createHooksMap();
  DOMPurify.isSupported = typeof entries === "function" && typeof getParentNode === "function" && implementation && implementation.createHTMLDocument !== void 0;
  const MUSTACHE_EXPR$1 = MUSTACHE_EXPR, ERB_EXPR$1 = ERB_EXPR, TMPLIT_EXPR$1 = TMPLIT_EXPR, DATA_ATTR$1 = DATA_ATTR, ARIA_ATTR$1 = ARIA_ATTR, IS_SCRIPT_OR_DATA$1 = IS_SCRIPT_OR_DATA, ATTR_WHITESPACE$1 = ATTR_WHITESPACE, CUSTOM_ELEMENT$1 = CUSTOM_ELEMENT;
  let IS_ALLOWED_URI$1 = IS_ALLOWED_URI;
  let ALLOWED_TAGS = null;
  const DEFAULT_ALLOWED_TAGS = addToSet({}, [...html$1, ...svg$1, ...svgFilters, ...mathMl$1, ...text]);
  let ALLOWED_ATTR = null;
  const DEFAULT_ALLOWED_ATTR = addToSet({}, [...html, ...svg, ...mathMl, ...xml]);
  let CUSTOM_ELEMENT_HANDLING = Object.seal(create(null, {
    tagNameCheck: {
      writable: true,
      configurable: false,
      enumerable: true,
      value: null
    },
    attributeNameCheck: {
      writable: true,
      configurable: false,
      enumerable: true,
      value: null
    },
    allowCustomizedBuiltInElements: {
      writable: true,
      configurable: false,
      enumerable: true,
      value: false
    }
  }));
  let FORBID_TAGS = null;
  let FORBID_ATTR = null;
  const EXTRA_ELEMENT_HANDLING = Object.seal(create(null, {
    tagCheck: {
      writable: true,
      configurable: false,
      enumerable: true,
      value: null
    },
    attributeCheck: {
      writable: true,
      configurable: false,
      enumerable: true,
      value: null
    }
  }));
  let ALLOW_ARIA_ATTR = true;
  let ALLOW_DATA_ATTR = true;
  let ALLOW_UNKNOWN_PROTOCOLS = false;
  let ALLOW_SELF_CLOSE_IN_ATTR = true;
  let SAFE_FOR_TEMPLATES = false;
  let SAFE_FOR_XML = true;
  let WHOLE_DOCUMENT = false;
  let SET_CONFIG = false;
  let SET_CONFIG_ALLOWED_TAGS = null;
  let SET_CONFIG_ALLOWED_ATTR = null;
  let FORCE_BODY = false;
  let RETURN_DOM = false;
  let RETURN_DOM_FRAGMENT = false;
  let RETURN_TRUSTED_TYPE = false;
  let SANITIZE_DOM = true;
  let SANITIZE_NAMED_PROPS = false;
  const SANITIZE_NAMED_PROPS_PREFIX = "user-content-";
  let KEEP_CONTENT = true;
  let IN_PLACE = false;
  let USE_PROFILES = {};
  let FORBID_CONTENTS = null;
  const DEFAULT_FORBID_CONTENTS = addToSet({}, [
    "annotation-xml",
    "audio",
    "colgroup",
    "desc",
    "foreignobject",
    "head",
    "iframe",
    "math",
    "mi",
    "mn",
    "mo",
    "ms",
    "mtext",
    "noembed",
    "noframes",
    "noscript",
    "plaintext",
    "script",
    // <selectedcontent> mirrors the selected <option>'s subtree, cloned by
    // the UA (customizable <select>) — including any on* handlers — and the
    // engine re-mirrors synchronously whenever a removal changes which
    // option/selectedcontent is current, even inside DOMPurify's inert
    // DOMParser document. Hoisting its children on removal re-inserts a fresh
    // mirror target ahead of the walk, which the engine refills, looping
    // forever (DoS) and amplifying output. Dropping its content on removal
    // (rather than hoisting) breaks that cascade; the content is a duplicate
    // of the option, which is sanitized on its own. See campaign-3 F1/F6.
    "selectedcontent",
    "style",
    "svg",
    "template",
    "thead",
    "title",
    "video",
    "xmp"
  ]);
  let DATA_URI_TAGS = null;
  const DEFAULT_DATA_URI_TAGS = addToSet({}, ["audio", "video", "img", "source", "image", "track"]);
  let URI_SAFE_ATTRIBUTES = null;
  const DEFAULT_URI_SAFE_ATTRIBUTES = addToSet({}, ["alt", "class", "for", "id", "label", "name", "pattern", "placeholder", "role", "summary", "title", "value", "style", "xmlns"]);
  const MATHML_NAMESPACE = "http://www.w3.org/1998/Math/MathML";
  const SVG_NAMESPACE = "http://www.w3.org/2000/svg";
  const HTML_NAMESPACE = "http://www.w3.org/1999/xhtml";
  let NAMESPACE = HTML_NAMESPACE;
  let IS_EMPTY_INPUT = false;
  let ALLOWED_NAMESPACES = null;
  const DEFAULT_ALLOWED_NAMESPACES = addToSet({}, [MATHML_NAMESPACE, SVG_NAMESPACE, HTML_NAMESPACE], stringToString);
  const DEFAULT_MATHML_TEXT_INTEGRATION_POINTS = freeze(["mi", "mo", "mn", "ms", "mtext"]);
  let MATHML_TEXT_INTEGRATION_POINTS = addToSet({}, DEFAULT_MATHML_TEXT_INTEGRATION_POINTS);
  const DEFAULT_HTML_INTEGRATION_POINTS = freeze(["annotation-xml"]);
  let HTML_INTEGRATION_POINTS = addToSet({}, DEFAULT_HTML_INTEGRATION_POINTS);
  const COMMON_SVG_AND_HTML_ELEMENTS = addToSet({}, ["title", "style", "font", "a", "script"]);
  let PARSER_MEDIA_TYPE = null;
  const SUPPORTED_PARSER_MEDIA_TYPES = ["application/xhtml+xml", "text/html"];
  const DEFAULT_PARSER_MEDIA_TYPE = "text/html";
  let transformCaseFunc = null;
  let CONFIG = null;
  const formElement = document2.createElement("form");
  const isRegexOrFunction = function isRegexOrFunction2(testValue) {
    return testValue instanceof RegExp || testValue instanceof Function;
  };
  const _parseConfig = function _parseConfig2() {
    let cfg = arguments.length > 0 && arguments[0] !== void 0 ? arguments[0] : {};
    if (CONFIG && CONFIG === cfg) {
      return;
    }
    if (!cfg || typeof cfg !== "object") {
      cfg = {};
    }
    cfg = clone(cfg);
    PARSER_MEDIA_TYPE = // eslint-disable-next-line unicorn/prefer-includes
    SUPPORTED_PARSER_MEDIA_TYPES.indexOf(cfg.PARSER_MEDIA_TYPE) === -1 ? DEFAULT_PARSER_MEDIA_TYPE : cfg.PARSER_MEDIA_TYPE;
    transformCaseFunc = PARSER_MEDIA_TYPE === "application/xhtml+xml" ? stringToString : stringToLowerCase;
    ALLOWED_TAGS = _resolveSetOption(cfg, "ALLOWED_TAGS", DEFAULT_ALLOWED_TAGS, {
      transform: transformCaseFunc
    });
    ALLOWED_ATTR = _resolveSetOption(cfg, "ALLOWED_ATTR", DEFAULT_ALLOWED_ATTR, {
      transform: transformCaseFunc
    });
    ALLOWED_NAMESPACES = _resolveSetOption(cfg, "ALLOWED_NAMESPACES", DEFAULT_ALLOWED_NAMESPACES, {
      transform: stringToString
    });
    URI_SAFE_ATTRIBUTES = _resolveSetOption(cfg, "ADD_URI_SAFE_ATTR", DEFAULT_URI_SAFE_ATTRIBUTES, {
      transform: transformCaseFunc,
      base: DEFAULT_URI_SAFE_ATTRIBUTES
    });
    DATA_URI_TAGS = _resolveSetOption(cfg, "ADD_DATA_URI_TAGS", DEFAULT_DATA_URI_TAGS, {
      transform: transformCaseFunc,
      base: DEFAULT_DATA_URI_TAGS
    });
    FORBID_CONTENTS = _resolveSetOption(cfg, "FORBID_CONTENTS", DEFAULT_FORBID_CONTENTS, {
      transform: transformCaseFunc
    });
    FORBID_TAGS = _resolveSetOption(cfg, "FORBID_TAGS", clone({}), {
      transform: transformCaseFunc
    });
    FORBID_ATTR = _resolveSetOption(cfg, "FORBID_ATTR", clone({}), {
      transform: transformCaseFunc
    });
    USE_PROFILES = objectHasOwnProperty(cfg, "USE_PROFILES") ? cfg.USE_PROFILES && typeof cfg.USE_PROFILES === "object" ? clone(cfg.USE_PROFILES) : cfg.USE_PROFILES : false;
    ALLOW_ARIA_ATTR = cfg.ALLOW_ARIA_ATTR !== false;
    ALLOW_DATA_ATTR = cfg.ALLOW_DATA_ATTR !== false;
    ALLOW_UNKNOWN_PROTOCOLS = cfg.ALLOW_UNKNOWN_PROTOCOLS || false;
    ALLOW_SELF_CLOSE_IN_ATTR = cfg.ALLOW_SELF_CLOSE_IN_ATTR !== false;
    SAFE_FOR_TEMPLATES = cfg.SAFE_FOR_TEMPLATES || false;
    SAFE_FOR_XML = cfg.SAFE_FOR_XML !== false;
    WHOLE_DOCUMENT = cfg.WHOLE_DOCUMENT || false;
    RETURN_DOM = cfg.RETURN_DOM || false;
    RETURN_DOM_FRAGMENT = cfg.RETURN_DOM_FRAGMENT || false;
    RETURN_TRUSTED_TYPE = cfg.RETURN_TRUSTED_TYPE || false;
    FORCE_BODY = cfg.FORCE_BODY || false;
    SANITIZE_DOM = cfg.SANITIZE_DOM !== false;
    SANITIZE_NAMED_PROPS = cfg.SANITIZE_NAMED_PROPS || false;
    KEEP_CONTENT = cfg.KEEP_CONTENT !== false;
    IN_PLACE = cfg.IN_PLACE || false;
    IS_ALLOWED_URI$1 = isRegex(cfg.ALLOWED_URI_REGEXP) ? cfg.ALLOWED_URI_REGEXP : IS_ALLOWED_URI;
    NAMESPACE = typeof cfg.NAMESPACE === "string" ? cfg.NAMESPACE : HTML_NAMESPACE;
    MATHML_TEXT_INTEGRATION_POINTS = _resolveObjectOption(
      cfg,
      "MATHML_TEXT_INTEGRATION_POINTS",
      () => addToSet({}, DEFAULT_MATHML_TEXT_INTEGRATION_POINTS)
      // Default built-in map
    );
    HTML_INTEGRATION_POINTS = _resolveObjectOption(
      cfg,
      "HTML_INTEGRATION_POINTS",
      () => addToSet({}, DEFAULT_HTML_INTEGRATION_POINTS)
      // Default built-in map
    );
    const customElementHandling = _resolveObjectOption(cfg, "CUSTOM_ELEMENT_HANDLING", () => create(null));
    CUSTOM_ELEMENT_HANDLING = create(null);
    if (objectHasOwnProperty(customElementHandling, "tagNameCheck") && isRegexOrFunction(customElementHandling.tagNameCheck)) {
      CUSTOM_ELEMENT_HANDLING.tagNameCheck = customElementHandling.tagNameCheck;
    }
    if (objectHasOwnProperty(customElementHandling, "attributeNameCheck") && isRegexOrFunction(customElementHandling.attributeNameCheck)) {
      CUSTOM_ELEMENT_HANDLING.attributeNameCheck = customElementHandling.attributeNameCheck;
    }
    if (objectHasOwnProperty(customElementHandling, "allowCustomizedBuiltInElements") && typeof customElementHandling.allowCustomizedBuiltInElements === "boolean") {
      CUSTOM_ELEMENT_HANDLING.allowCustomizedBuiltInElements = customElementHandling.allowCustomizedBuiltInElements;
    }
    seal(CUSTOM_ELEMENT_HANDLING);
    if (SAFE_FOR_TEMPLATES) {
      ALLOW_DATA_ATTR = false;
    }
    if (RETURN_DOM_FRAGMENT) {
      RETURN_DOM = true;
    }
    if (USE_PROFILES) {
      ALLOWED_TAGS = addToSet({}, text);
      ALLOWED_ATTR = create(null);
      if (USE_PROFILES.html === true) {
        addToSet(ALLOWED_TAGS, html$1);
        addToSet(ALLOWED_ATTR, html);
      }
      if (USE_PROFILES.svg === true) {
        addToSet(ALLOWED_TAGS, svg$1);
        addToSet(ALLOWED_ATTR, svg);
        addToSet(ALLOWED_ATTR, xml);
      }
      if (USE_PROFILES.svgFilters === true) {
        addToSet(ALLOWED_TAGS, svgFilters);
        addToSet(ALLOWED_ATTR, svg);
        addToSet(ALLOWED_ATTR, xml);
      }
      if (USE_PROFILES.mathMl === true) {
        addToSet(ALLOWED_TAGS, mathMl$1);
        addToSet(ALLOWED_ATTR, mathMl);
        addToSet(ALLOWED_ATTR, xml);
      }
    }
    EXTRA_ELEMENT_HANDLING.tagCheck = null;
    EXTRA_ELEMENT_HANDLING.attributeCheck = null;
    if (objectHasOwnProperty(cfg, "ADD_TAGS")) {
      if (typeof cfg.ADD_TAGS === "function") {
        EXTRA_ELEMENT_HANDLING.tagCheck = cfg.ADD_TAGS;
      } else if (arrayIsArray(cfg.ADD_TAGS)) {
        if (ALLOWED_TAGS === DEFAULT_ALLOWED_TAGS) {
          ALLOWED_TAGS = clone(ALLOWED_TAGS);
        }
        addToSet(ALLOWED_TAGS, cfg.ADD_TAGS, transformCaseFunc);
      }
    }
    if (objectHasOwnProperty(cfg, "ADD_ATTR")) {
      if (typeof cfg.ADD_ATTR === "function") {
        EXTRA_ELEMENT_HANDLING.attributeCheck = cfg.ADD_ATTR;
      } else if (arrayIsArray(cfg.ADD_ATTR)) {
        if (ALLOWED_ATTR === DEFAULT_ALLOWED_ATTR) {
          ALLOWED_ATTR = clone(ALLOWED_ATTR);
        }
        addToSet(ALLOWED_ATTR, cfg.ADD_ATTR, transformCaseFunc);
      }
    }
    if (objectHasOwnProperty(cfg, "ADD_FORBID_CONTENTS") && arrayIsArray(cfg.ADD_FORBID_CONTENTS)) {
      if (FORBID_CONTENTS === DEFAULT_FORBID_CONTENTS) {
        FORBID_CONTENTS = clone(FORBID_CONTENTS);
      }
      addToSet(FORBID_CONTENTS, cfg.ADD_FORBID_CONTENTS, transformCaseFunc);
    }
    if (KEEP_CONTENT) {
      ALLOWED_TAGS["#text"] = true;
    }
    if (WHOLE_DOCUMENT) {
      addToSet(ALLOWED_TAGS, ["html", "head", "body"]);
    }
    if (ALLOWED_TAGS.table) {
      addToSet(ALLOWED_TAGS, ["tbody"]);
      delete FORBID_TAGS.tbody;
    }
    if (cfg.TRUSTED_TYPES_POLICY) {
      if (typeof cfg.TRUSTED_TYPES_POLICY.createHTML !== "function") {
        throw typeErrorCreate('TRUSTED_TYPES_POLICY configuration option must provide a "createHTML" hook.');
      }
      if (typeof cfg.TRUSTED_TYPES_POLICY.createScriptURL !== "function") {
        throw typeErrorCreate('TRUSTED_TYPES_POLICY configuration option must provide a "createScriptURL" hook.');
      }
      const previousTrustedTypesPolicy = trustedTypesPolicy;
      trustedTypesPolicy = cfg.TRUSTED_TYPES_POLICY;
      try {
        emptyHTML = _createTrustedHTML("");
      } catch (error) {
        trustedTypesPolicy = previousTrustedTypesPolicy;
        throw error;
      }
    } else if (cfg.TRUSTED_TYPES_POLICY === null) {
      trustedTypesPolicy = void 0;
      emptyHTML = "";
    } else {
      if (trustedTypesPolicy === void 0) {
        trustedTypesPolicy = _getDefaultTrustedTypesPolicy();
      }
      if (trustedTypesPolicy && typeof emptyHTML === "string") {
        emptyHTML = _createTrustedHTML("");
      }
    }
    if (freeze) {
      freeze(cfg);
    }
    CONFIG = cfg;
  };
  const ALL_SVG_TAGS = addToSet({}, [...svg$1, ...svgFilters, ...svgDisallowed]);
  const ALL_MATHML_TAGS = addToSet({}, [...mathMl$1, ...mathMlDisallowed]);
  const _checkSvgNamespace = function _checkSvgNamespace2(tagName, parent, parentTagName) {
    if (parent.namespaceURI === HTML_NAMESPACE) {
      return tagName === "svg";
    }
    if (parent.namespaceURI === MATHML_NAMESPACE) {
      return tagName === "svg" && (parentTagName === "annotation-xml" || MATHML_TEXT_INTEGRATION_POINTS[parentTagName]);
    }
    return Boolean(ALL_SVG_TAGS[tagName]);
  };
  const _checkMathMlNamespace = function _checkMathMlNamespace2(tagName, parent, parentTagName) {
    if (parent.namespaceURI === HTML_NAMESPACE) {
      return tagName === "math";
    }
    if (parent.namespaceURI === SVG_NAMESPACE) {
      return tagName === "math" && HTML_INTEGRATION_POINTS[parentTagName];
    }
    return Boolean(ALL_MATHML_TAGS[tagName]);
  };
  const _checkHtmlNamespace = function _checkHtmlNamespace2(tagName, parent, parentTagName) {
    if (parent.namespaceURI === SVG_NAMESPACE && !HTML_INTEGRATION_POINTS[parentTagName]) {
      return false;
    }
    if (parent.namespaceURI === MATHML_NAMESPACE && !MATHML_TEXT_INTEGRATION_POINTS[parentTagName]) {
      return false;
    }
    return !ALL_MATHML_TAGS[tagName] && (COMMON_SVG_AND_HTML_ELEMENTS[tagName] || !ALL_SVG_TAGS[tagName]);
  };
  const _checkValidNamespace = function _checkValidNamespace2(element) {
    let parent = getParentNode(element);
    if (!parent || !parent.tagName) {
      parent = {
        namespaceURI: NAMESPACE,
        tagName: "template"
      };
    }
    const tagName = stringToLowerCase(element.tagName);
    const parentTagName = stringToLowerCase(parent.tagName);
    if (!ALLOWED_NAMESPACES[element.namespaceURI]) {
      return false;
    }
    if (element.namespaceURI === SVG_NAMESPACE) {
      return _checkSvgNamespace(tagName, parent, parentTagName);
    }
    if (element.namespaceURI === MATHML_NAMESPACE) {
      return _checkMathMlNamespace(tagName, parent, parentTagName);
    }
    if (element.namespaceURI === HTML_NAMESPACE) {
      return _checkHtmlNamespace(tagName, parent, parentTagName);
    }
    if (PARSER_MEDIA_TYPE === "application/xhtml+xml" && ALLOWED_NAMESPACES[element.namespaceURI]) {
      return true;
    }
    return false;
  };
  const _forceRemove = function _forceRemove2(node) {
    arrayPush(DOMPurify.removed, {
      element: node
    });
    try {
      getParentNode(node).removeChild(node);
    } catch (_4) {
      remove(node);
      if (!getParentNode(node)) {
        throw typeErrorCreate("a node selected for removal could not be detached from its tree and cannot be safely returned; refusing to sanitize in place");
      }
    }
  };
  const _stripAttributeNode = function _stripAttributeNode2(element, attribute, name) {
    try {
      element.removeAttributeNode(attribute);
    } catch (_4) {
      try {
        element.removeAttribute(name);
      } catch (_5) {
      }
    }
  };
  const _neutralizeRoot = function _neutralizeRoot2(root) {
    _neutralizeSubtree(root);
    const childNodes = getChildNodes(root);
    if (childNodes) {
      const snapshot = [];
      arrayForEach(childNodes, (child) => {
        arrayPush(snapshot, child);
      });
      arrayForEach(snapshot, (child) => {
        try {
          remove(child);
        } catch (_4) {
        }
      });
    }
    const attributes = getAttributes(root);
    if (attributes) {
      for (let i4 = attributes.length - 1; i4 >= 0; --i4) {
        const attribute = attributes[i4];
        const name = attribute && attribute.name;
        if (typeof name === "string") {
          _stripAttributeNode(root, attribute, name);
        }
      }
    }
  };
  const _removeAttribute = function _removeAttribute2(name, element, attr) {
    if (!attr) {
      try {
        attr = element.getAttributeNode(name);
      } catch (_4) {
        attr = null;
      }
    }
    arrayPush(DOMPurify.removed, {
      attribute: attr || null,
      from: element
    });
    try {
      if (attr) {
        element.removeAttributeNode(attr);
      } else {
        element.removeAttribute(name);
      }
    } catch (_4) {
      try {
        element.removeAttribute(name);
      } catch (_5) {
      }
    }
    if (name === "is") {
      if (RETURN_DOM || RETURN_DOM_FRAGMENT) {
        try {
          _forceRemove(element);
        } catch (_4) {
        }
      } else {
        try {
          element.setAttribute(name, "");
        } catch (_4) {
        }
      }
    }
  };
  const _stripDisallowedAttributes = function _stripDisallowedAttributes2(element) {
    const attributes = getAttributes(element);
    if (!attributes) {
      return;
    }
    for (let i4 = attributes.length - 1; i4 >= 0; --i4) {
      const attribute = attributes[i4];
      const name = attribute && attribute.name;
      if (typeof name !== "string" || ALLOWED_ATTR[transformCaseFunc(name)]) {
        continue;
      }
      _stripAttributeNode(element, attribute, name);
    }
  };
  const _neutralizeSubtree = function _neutralizeSubtree2(root) {
    const stack = [root];
    while (stack.length > 0) {
      const node = stack.pop();
      const nodeType = _readNodeType(node);
      if (nodeType === NODE_TYPE.element) {
        _stripDisallowedAttributes(node);
      }
      const childNodes = getChildNodes(node);
      if (childNodes) {
        for (let i4 = childNodes.length - 1; i4 >= 0; --i4) {
          stack.push(childNodes[i4]);
        }
      }
    }
  };
  const _isPatchLinkageAttribute = function _isPatchLinkageAttribute2(lcName, lcTag) {
    if (!SAFE_FOR_XML) {
      return false;
    }
    if (lcName === "patchsrc") {
      return true;
    }
    return lcName === "for" && lcTag !== "label" && lcTag !== "output";
  };
  const _neutralizePatchLinkage = function _neutralizePatchLinkage2(root) {
    if (!SAFE_FOR_XML) {
      return;
    }
    const stack = [root];
    while (stack.length > 0) {
      const node = stack.pop();
      const nodeType = _readNodeType(node);
      if (nodeType === NODE_TYPE.processingInstruction || nodeType === NODE_TYPE.comment && regExpTest(COMMENT_MARKUP_PROBE, node.data)) {
        try {
          remove(node);
        } catch (_4) {
        }
        continue;
      }
      if (nodeType === NODE_TYPE.element) {
        const element = node;
        const lcTag = transformCaseFunc(_readNodeName(node));
        try {
          if (element.hasAttribute && element.hasAttribute("patchsrc")) {
            element.removeAttribute("patchsrc");
          }
          if (element.hasAttribute && element.hasAttribute("for") && _isPatchLinkageAttribute("for", lcTag)) {
            element.removeAttribute("for");
          }
        } catch (_4) {
        }
      }
      const childNodes = getChildNodes(node);
      if (childNodes) {
        for (let i4 = childNodes.length - 1; i4 >= 0; --i4) {
          stack.push(childNodes[i4]);
        }
      }
    }
  };
  const _initDocument = function _initDocument2(dirty) {
    let doc = null;
    let leadingWhitespace = null;
    if (FORCE_BODY) {
      dirty = "<remove></remove>" + dirty;
    } else {
      const matches = stringMatch(dirty, /^[\r\n\t ]+/);
      leadingWhitespace = matches && matches[0];
    }
    if (PARSER_MEDIA_TYPE === "application/xhtml+xml" && NAMESPACE === HTML_NAMESPACE) {
      dirty = '<html xmlns="http://www.w3.org/1999/xhtml"><head></head><body>' + dirty + "</body></html>";
    }
    const dirtyPayload = trustedTypesPolicy ? _createTrustedHTML(dirty) : dirty;
    if (NAMESPACE === HTML_NAMESPACE) {
      try {
        doc = new DOMParser().parseFromString(dirtyPayload, PARSER_MEDIA_TYPE);
      } catch (_4) {
      }
    }
    if (!doc || !doc.documentElement) {
      doc = implementation.createDocument(NAMESPACE, "template", null);
      try {
        doc.documentElement.innerHTML = IS_EMPTY_INPUT ? emptyHTML : dirtyPayload;
      } catch (_4) {
      }
    }
    const body = doc.body || doc.documentElement;
    if (dirty && leadingWhitespace) {
      body.insertBefore(document2.createTextNode(leadingWhitespace), body.childNodes[0] || null);
    }
    if (NAMESPACE === HTML_NAMESPACE) {
      return getElementsByTagName.call(doc, WHOLE_DOCUMENT ? "html" : "body")[0];
    }
    return WHOLE_DOCUMENT ? doc.documentElement : body;
  };
  const _createNodeIterator = function _createNodeIterator2(root) {
    const doc = getOwnerDocument ? getOwnerDocument(root) : root.ownerDocument;
    return createNodeIterator.call(
      doc || root,
      root,
      // eslint-disable-next-line no-bitwise
      NodeFilter.SHOW_ELEMENT | NodeFilter.SHOW_COMMENT | NodeFilter.SHOW_TEXT | NodeFilter.SHOW_PROCESSING_INSTRUCTION | NodeFilter.SHOW_CDATA_SECTION,
      null
    );
  };
  const _stripTemplateExpressions = function _stripTemplateExpressions2(value) {
    value = stringReplace(value, MUSTACHE_EXPR$1, " ");
    value = stringReplace(value, ERB_EXPR$1, " ");
    value = stringReplace(value, TMPLIT_EXPR$1, " ");
    return value;
  };
  const _scrubTemplateExpressions2 = function _scrubTemplateExpressions(node) {
    var _node$querySelectorAl;
    node.normalize();
    const doc = getOwnerDocument ? getOwnerDocument(node) : node.ownerDocument;
    const walker = createNodeIterator.call(
      doc || node,
      node,
      // eslint-disable-next-line no-bitwise
      NodeFilter.SHOW_TEXT | NodeFilter.SHOW_COMMENT | NodeFilter.SHOW_CDATA_SECTION | NodeFilter.SHOW_PROCESSING_INSTRUCTION,
      null
    );
    let currentNode = walker.nextNode();
    while (currentNode) {
      currentNode.data = _stripTemplateExpressions(currentNode.data);
      currentNode = walker.nextNode();
    }
    const templates = (_node$querySelectorAl = node.querySelectorAll) === null || _node$querySelectorAl === void 0 ? void 0 : _node$querySelectorAl.call(node, "template");
    if (templates) {
      arrayForEach(templates, (tmpl) => {
        if (_isDocumentFragment(tmpl.content)) {
          _scrubTemplateExpressions2(tmpl.content);
        }
      });
    }
  };
  const _isClobbered = function _isClobbered2(element) {
    const realTagName = getNodeName ? getNodeName(element) : null;
    if (typeof realTagName !== "string") {
      return false;
    }
    if (transformCaseFunc(realTagName) !== "form") {
      return false;
    }
    return typeof element.nodeName !== "string" || typeof element.textContent !== "string" || typeof element.removeChild !== "function" || // Realm-safe NamedNodeMap detection: equality against the cached
    // prototype getter. Clobbered .attributes (e.g. <input name="attributes">)
    // makes the direct read diverge from the cached read; a clean form
    // (same-realm OR foreign-realm) has both reads pointing at the same
    // canonical NamedNodeMap.
    element.attributes !== getAttributes(element) || typeof element.removeAttribute !== "function" || typeof element.setAttribute !== "function" || typeof element.namespaceURI !== "string" || typeof element.insertBefore !== "function" || typeof element.hasChildNodes !== "function" || // NodeType clobbering probe. Cached Node.prototype.nodeType getter
    // returns the integer 1 for any Element regardless of realm; direct
    // read on a clobbered form (e.g. <input name="nodeType">) returns
    // the named child element. Cheap addition — nodeType is read from
    // an internal slot, no serialization cost — and removes a residual
    // clobbering surface used by several mXSS / PI / comment branches
    // in _sanitizeElements that compare currentNode.nodeType directly.
    element.nodeType !== getNodeType(element) || // HTMLFormElement has [LegacyOverrideBuiltIns]: a descendant named
    // "childNodes" shadows the prototype getter. Direct reads of
    // form.childNodes from a clobbered form return the named child
    // instead of the real NodeList, so any walk that reads it directly
    // skips the form's real children. Compare the direct read to the
    // cached Node.prototype getter — when the form's named-property
    // getter intercepts the read, the two values differ and we flag
    // the form. This catches every clobbering child type (input,
    // select, etc.) regardless of whether the named child happens to
    // carry a numeric .length, which a typeof-based probe would miss
    // (e.g. HTMLSelectElement.length is a defined unsigned-long).
    element.childNodes !== getChildNodes(element);
  };
  const _isDocumentFragment = function _isDocumentFragment2(value) {
    if (!getNodeType || typeof value !== "object" || value === null) {
      return false;
    }
    try {
      return getNodeType(value) === NODE_TYPE.documentFragment;
    } catch (_4) {
      return false;
    }
  };
  const _isNode = function _isNode2(value) {
    if (!getNodeType || typeof value !== "object" || value === null) {
      return false;
    }
    try {
      return typeof getNodeType(value) === "number";
    } catch (_4) {
      return false;
    }
  };
  function _executeHooks(hooks2, currentNode, data) {
    if (hooks2.length === 0) {
      return;
    }
    arrayForEach(hooks2, (hook) => {
      hook.call(DOMPurify, currentNode, data, CONFIG);
    });
  }
  const _isUnsafeNode = function _isUnsafeNode2(currentNode, tagName) {
    if (SAFE_FOR_XML && currentNode.hasChildNodes() && !_isNode(currentNode.firstElementChild) && regExpTest(ELEMENT_MARKUP_PROBE, currentNode.textContent) && regExpTest(ELEMENT_MARKUP_PROBE, currentNode.innerHTML)) {
      return true;
    }
    if (SAFE_FOR_XML && currentNode.namespaceURI === HTML_NAMESPACE && LITERAL_TEXT_ELEMENTS[tagName] && (_isNode(currentNode.firstElementChild) || typeof currentNode.textContent === "string" && regExpTest(LITERAL_TEXT_CLOSE[tagName], currentNode.textContent))) {
      return true;
    }
    if (currentNode.nodeType === NODE_TYPE.processingInstruction) {
      return true;
    }
    if (SAFE_FOR_XML && currentNode.nodeType === NODE_TYPE.comment && regExpTest(COMMENT_MARKUP_PROBE, currentNode.data)) {
      return true;
    }
    return false;
  };
  const _matchesNameCheck = function _matchesNameCheck2(check, name) {
    if (check instanceof RegExp) {
      return regExpTest(check, name);
    }
    if (check instanceof Function) {
      for (var _len = arguments.length, args = new Array(_len > 2 ? _len - 2 : 0), _key = 2; _key < _len; _key++) {
        args[_key - 2] = arguments[_key];
      }
      return Boolean(check(name, ...args));
    }
    return false;
  };
  const _sanitizeDisallowedNode = function _sanitizeDisallowedNode2(currentNode, tagName, root) {
    if (!FORBID_TAGS[tagName] && _isBasicCustomElement(tagName) && _matchesNameCheck(CUSTOM_ELEMENT_HANDLING.tagNameCheck, tagName)) {
      return false;
    }
    if (KEEP_CONTENT && !FORBID_CONTENTS[tagName]) {
      const parentNode = getParentNode(currentNode);
      const childNodes = getChildNodes(currentNode);
      if (childNodes && parentNode) {
        const childCount = childNodes.length;
        for (let i4 = childCount - 1; i4 >= 0; --i4) {
          const hoisted = currentNode === root ? cloneNode(childNodes[i4], true) : childNodes[i4];
          parentNode.insertBefore(hoisted, getNextSibling(currentNode));
        }
      }
    }
    _forceRemove(currentNode);
    return true;
  };
  const _forkSharedAllowlist = function _forkSharedAllowlist2(hookList, set, defaultSet, setConfigSet) {
    if (hookList.length === 0) {
      return set;
    }
    return set === defaultSet || set === setConfigSet ? clone(set) : set;
  };
  const _handleHookDetachedNode = function _handleHookDetachedNode2(currentNode, root) {
    if (currentNode === root || getParentNode(currentNode) !== null) {
      return false;
    }
    if (IN_PLACE) {
      _neutralizeSubtree(currentNode);
    }
    return true;
  };
  const _sanitizeElements = function _sanitizeElements2(currentNode, root) {
    _executeHooks(hooks.beforeSanitizeElements, currentNode, null);
    if (_handleHookDetachedNode(currentNode, root)) {
      return true;
    }
    if (_isClobbered(currentNode)) {
      _forceRemove(currentNode);
      return true;
    }
    const tagName = transformCaseFunc(_readNodeName(currentNode));
    ALLOWED_TAGS = _forkSharedAllowlist(hooks.uponSanitizeElement, ALLOWED_TAGS, DEFAULT_ALLOWED_TAGS, SET_CONFIG_ALLOWED_TAGS);
    _executeHooks(hooks.uponSanitizeElement, currentNode, {
      tagName,
      allowedTags: ALLOWED_TAGS
    });
    if (_handleHookDetachedNode(currentNode, root)) {
      return true;
    }
    if (_isUnsafeNode(currentNode, tagName)) {
      _forceRemove(currentNode);
      return true;
    }
    if (FORBID_TAGS[tagName] || !(EXTRA_ELEMENT_HANDLING.tagCheck instanceof Function && EXTRA_ELEMENT_HANDLING.tagCheck(tagName)) && !ALLOWED_TAGS[tagName]) {
      const removed = _sanitizeDisallowedNode(currentNode, tagName, root);
      if (removed === false) {
        _executeHooks(hooks.afterSanitizeElements, currentNode, null);
      }
      return removed;
    }
    const nt2 = _readNodeType(currentNode);
    if (nt2 === NODE_TYPE.element && !_checkValidNamespace(currentNode)) {
      _forceRemove(currentNode);
      return true;
    }
    if ((tagName === "noscript" || tagName === "noembed" || tagName === "noframes") && regExpTest(FALLBACK_TAG_CLOSE, currentNode.innerHTML)) {
      _forceRemove(currentNode);
      return true;
    }
    if (SAFE_FOR_TEMPLATES && currentNode.nodeType === NODE_TYPE.text) {
      const content = _stripTemplateExpressions(currentNode.textContent);
      if (currentNode.textContent !== content) {
        arrayPush(DOMPurify.removed, {
          element: currentNode.cloneNode()
        });
        currentNode.textContent = content;
      }
    }
    _executeHooks(hooks.afterSanitizeElements, currentNode, null);
    return false;
  };
  const _isValidAttribute = function _isValidAttribute2(lcTag, lcName, value) {
    if (FORBID_ATTR[lcName]) {
      return false;
    }
    if (_isPatchLinkageAttribute(lcName, lcTag)) {
      return false;
    }
    if (SANITIZE_DOM && (lcName === "id" || lcName === "name") && (value in document2 || value in formElement)) {
      return false;
    }
    const nameIsPermitted = ALLOWED_ATTR[lcName] || EXTRA_ELEMENT_HANDLING.attributeCheck instanceof Function && EXTRA_ELEMENT_HANDLING.attributeCheck(lcName, lcTag);
    if (ALLOW_DATA_ATTR && regExpTest(DATA_ATTR$1, lcName)) {
      return true;
    }
    if (ALLOW_ARIA_ATTR && regExpTest(ARIA_ATTR$1, lcName)) {
      return true;
    }
    if (!nameIsPermitted) {
      return (
        // Condition a) covers a basically valid custom element tag name whose
        // tag passes the configured tagNameCheck and whose attribute name
        // passes the configured attributeNameCheck ...
        _isBasicCustomElement(lcTag) && _matchesNameCheck(CUSTOM_ELEMENT_HANDLING.tagNameCheck, lcTag) && _matchesNameCheck(CUSTOM_ELEMENT_HANDLING.attributeNameCheck, lcName, lcTag) || // Condition b) covers an `is` attribute whose value passes the
        // configured tagNameCheck while customized built-in elements are
        // allowed.
        lcName === "is" && CUSTOM_ELEMENT_HANDLING.allowCustomizedBuiltInElements && _matchesNameCheck(CUSTOM_ELEMENT_HANDLING.tagNameCheck, value)
      );
    }
    if (URI_SAFE_ATTRIBUTES[lcName]) {
      return true;
    }
    if (regExpTest(IS_ALLOWED_URI$1, stringReplace(value, ATTR_WHITESPACE$1, ""))) {
      return true;
    }
    if ((lcName === "src" || lcName === "xlink:href" || lcName === "href") && lcTag !== "script" && stringIndexOf(value, "data:") === 0 && DATA_URI_TAGS[lcTag]) {
      return true;
    }
    if (ALLOW_UNKNOWN_PROTOCOLS && !regExpTest(IS_SCRIPT_OR_DATA$1, stringReplace(value, ATTR_WHITESPACE$1, ""))) {
      return true;
    }
    return !value;
  };
  const RESERVED_CUSTOM_ELEMENT_NAMES = addToSet({}, ["annotation-xml", "color-profile", "font-face", "font-face-format", "font-face-name", "font-face-src", "font-face-uri", "missing-glyph"]);
  const _isBasicCustomElement = function _isBasicCustomElement2(tagName) {
    return !RESERVED_CUSTOM_ELEMENT_NAMES[stringToLowerCase(tagName)] && regExpTest(CUSTOM_ELEMENT$1, tagName);
  };
  const _applyTrustedTypesToAttribute = function _applyTrustedTypesToAttribute2(lcTag, lcName, namespaceURI, value) {
    if (trustedTypesPolicy && typeof trustedTypes === "object" && typeof trustedTypes.getAttributeType === "function" && !namespaceURI) {
      switch (trustedTypes.getAttributeType(lcTag, lcName)) {
        case "TrustedHTML": {
          return _createTrustedHTML(value);
        }
        case "TrustedScriptURL": {
          return _createTrustedScriptURL(value);
        }
      }
    }
    return value;
  };
  const _setAttributeValue = function _setAttributeValue2(currentNode, name, namespaceURI, value) {
    try {
      if (namespaceURI) {
        currentNode.setAttributeNS(namespaceURI, name, value);
      } else {
        currentNode.setAttribute(name, value);
      }
      if (_isClobbered(currentNode)) {
        _forceRemove(currentNode);
      } else {
        arrayPop(DOMPurify.removed);
      }
    } catch (_4) {
      _removeAttribute(name, currentNode);
    }
  };
  const _sanitizeAttributes = function _sanitizeAttributes2(currentNode) {
    _executeHooks(hooks.beforeSanitizeAttributes, currentNode, null);
    const attributes = currentNode.attributes;
    if (!attributes || _isClobbered(currentNode)) {
      return;
    }
    ALLOWED_ATTR = _forkSharedAllowlist(hooks.uponSanitizeAttribute, ALLOWED_ATTR, DEFAULT_ALLOWED_ATTR, SET_CONFIG_ALLOWED_ATTR);
    const hookEvent = {
      attrName: "",
      attrValue: "",
      keepAttr: true,
      allowedAttributes: ALLOWED_ATTR,
      forceKeepAttr: void 0
    };
    let l3 = attributes.length;
    const lcTag = transformCaseFunc(currentNode.nodeName);
    while (l3--) {
      const attr = attributes[l3];
      const name = attr.name, namespaceURI = attr.namespaceURI, attrValue = attr.value;
      const lcName = transformCaseFunc(name);
      const initValue = attrValue;
      let value = name === "value" ? initValue : stringTrim(initValue);
      hookEvent.attrName = lcName;
      hookEvent.attrValue = value;
      hookEvent.keepAttr = true;
      hookEvent.forceKeepAttr = void 0;
      _executeHooks(hooks.uponSanitizeAttribute, currentNode, hookEvent);
      value = hookEvent.attrValue;
      if (SANITIZE_NAMED_PROPS && (lcName === "id" || lcName === "name") && stringIndexOf(value, SANITIZE_NAMED_PROPS_PREFIX) !== 0) {
        _removeAttribute(name, currentNode, attr);
        value = SANITIZE_NAMED_PROPS_PREFIX + value;
      }
      if (SAFE_FOR_XML && regExpTest(/((--!?|])>)|<\/(style|script|title|xmp|textarea|noscript|iframe|noembed|noframes)/i, value)) {
        _removeAttribute(name, currentNode, attr);
        continue;
      }
      if (lcName === "attributename" && stringMatch(value, "href")) {
        _removeAttribute(name, currentNode, attr);
        continue;
      }
      if (hookEvent.forceKeepAttr) {
        continue;
      }
      if (!hookEvent.keepAttr) {
        _removeAttribute(name, currentNode, attr);
        continue;
      }
      if (!ALLOW_SELF_CLOSE_IN_ATTR && regExpTest(SELF_CLOSING_TAG, value)) {
        _removeAttribute(name, currentNode, attr);
        continue;
      }
      if (SAFE_FOR_TEMPLATES) {
        value = _stripTemplateExpressions(value);
      }
      if (!_isValidAttribute(lcTag, lcName, value)) {
        _removeAttribute(name, currentNode, attr);
        continue;
      }
      value = _applyTrustedTypesToAttribute(lcTag, lcName, namespaceURI, value);
      if (value !== initValue) {
        _setAttributeValue(currentNode, name, namespaceURI, value);
      }
    }
    _executeHooks(hooks.afterSanitizeAttributes, currentNode, null);
  };
  const _sanitizeShadowDOM2 = function _sanitizeShadowDOM(fragment) {
    let shadowNode = null;
    const shadowIterator = _createNodeIterator(fragment);
    _executeHooks(hooks.beforeSanitizeShadowDOM, fragment, null);
    while (shadowNode = shadowIterator.nextNode()) {
      _executeHooks(hooks.uponSanitizeShadowNode, shadowNode, null);
      _sanitizeElements(shadowNode, fragment);
      _sanitizeAttributes(shadowNode);
      if (_isDocumentFragment(shadowNode.content)) {
        _sanitizeShadowDOM2(shadowNode.content);
      }
      if (_readNodeType(shadowNode) === NODE_TYPE.element) {
        const innerSr = getShadowRoot(shadowNode);
        if (_isDocumentFragment(innerSr)) {
          _sanitizeAttachedShadowRoots(innerSr);
          _sanitizeShadowDOM2(innerSr);
        }
      }
    }
    _executeHooks(hooks.afterSanitizeShadowDOM, fragment, null);
  };
  const _sanitizeAttachedShadowRoots = function _sanitizeAttachedShadowRoots2(root) {
    const stack = [{
      node: root,
      shadow: null
    }];
    while (stack.length > 0) {
      const item = stack.pop();
      if (item.shadow) {
        _sanitizeShadowDOM2(item.shadow);
        continue;
      }
      const node = item.node;
      const nodeType = _readNodeType(node);
      const isElement = nodeType === NODE_TYPE.element;
      const childNodes = getChildNodes(node);
      if (childNodes) {
        for (let i4 = childNodes.length - 1; i4 >= 0; --i4) {
          stack.push({
            node: childNodes[i4],
            shadow: null
          });
        }
      }
      if (isElement) {
        const rootName = getNodeName ? getNodeName(node) : null;
        if (typeof rootName === "string" && transformCaseFunc(rootName) === "template") {
          const content = node.content;
          if (_isDocumentFragment(content)) {
            stack.push({
              node: content,
              shadow: null
            });
          }
        }
      }
      if (isElement) {
        const sr = getShadowRoot(node);
        if (_isDocumentFragment(sr)) {
          stack.push({
            node: null,
            shadow: sr
          }, {
            node: sr,
            shadow: null
          });
        }
      }
    }
  };
  DOMPurify.sanitize = function(dirty) {
    let cfg = arguments.length > 1 && arguments[1] !== void 0 ? arguments[1] : {};
    let body = null;
    let importedNode = null;
    let currentNode = null;
    let returnNode = null;
    IS_EMPTY_INPUT = !dirty;
    if (IS_EMPTY_INPUT) {
      dirty = "<!-->";
    }
    if (typeof dirty !== "string" && !_isNode(dirty)) {
      dirty = stringifyValue(dirty);
      if (typeof dirty !== "string") {
        throw typeErrorCreate("dirty is not a string, aborting");
      }
    }
    if (!DOMPurify.isSupported) {
      return dirty;
    }
    if (SET_CONFIG) {
      ALLOWED_TAGS = SET_CONFIG_ALLOWED_TAGS;
      ALLOWED_ATTR = SET_CONFIG_ALLOWED_ATTR;
    } else {
      _parseConfig(cfg);
    }
    if (hooks.uponSanitizeElement.length > 0 || hooks.uponSanitizeAttribute.length > 0) {
      ALLOWED_TAGS = clone(ALLOWED_TAGS);
    }
    if (hooks.uponSanitizeAttribute.length > 0) {
      ALLOWED_ATTR = clone(ALLOWED_ATTR);
    }
    DOMPurify.removed = [];
    const inPlace = IN_PLACE && typeof dirty !== "string" && _isNode(dirty);
    if (inPlace) {
      _neutralizePatchLinkage(dirty);
      const nn = _readNodeName(dirty);
      if (typeof nn === "string") {
        const tagName = transformCaseFunc(nn);
        if (!ALLOWED_TAGS[tagName] || FORBID_TAGS[tagName]) {
          _neutralizeRoot(dirty);
          throw typeErrorCreate("root node is forbidden and cannot be sanitized in-place");
        }
      }
      if (_isClobbered(dirty)) {
        _neutralizeRoot(dirty);
        throw typeErrorCreate("root node is clobbered and cannot be sanitized in-place");
      }
      try {
        _sanitizeAttachedShadowRoots(dirty);
      } catch (error) {
        _neutralizeRoot(dirty);
        throw error;
      }
    } else if (_isNode(dirty)) {
      body = _initDocument("<!---->");
      importedNode = body.ownerDocument.importNode(dirty, true);
      if (importedNode.nodeType === NODE_TYPE.element && importedNode.nodeName === "BODY") {
        body = importedNode;
      } else if (importedNode.nodeName === "HTML") {
        body = importedNode;
      } else {
        body.appendChild(importedNode);
      }
      _sanitizeAttachedShadowRoots(importedNode);
    } else {
      if (!RETURN_DOM && !SAFE_FOR_TEMPLATES && !WHOLE_DOCUMENT && // eslint-disable-next-line unicorn/prefer-includes
      dirty.indexOf("<") === -1) {
        return trustedTypesPolicy && RETURN_TRUSTED_TYPE ? _createTrustedHTML(dirty) : dirty;
      }
      body = _initDocument(dirty);
      if (!body) {
        return RETURN_DOM ? null : RETURN_TRUSTED_TYPE ? emptyHTML : "";
      }
    }
    if (body && FORCE_BODY) {
      _forceRemove(body.firstChild);
    }
    const walkRoot = inPlace ? dirty : body;
    try {
      const nodeIterator = _createNodeIterator(walkRoot);
      while (currentNode = nodeIterator.nextNode()) {
        _sanitizeElements(currentNode, walkRoot);
        _sanitizeAttributes(currentNode);
        if (_isDocumentFragment(currentNode.content)) {
          _sanitizeShadowDOM2(currentNode.content);
        }
      }
    } catch (error) {
      if (inPlace) {
        _neutralizeRoot(dirty);
        arrayForEach(DOMPurify.removed, (entry) => {
          if (entry.element) {
            _neutralizeSubtree(entry.element);
          }
        });
      }
      throw error;
    }
    if (inPlace) {
      arrayForEach(DOMPurify.removed, (entry) => {
        if (entry.element) {
          _neutralizeSubtree(entry.element);
        }
      });
      if (SAFE_FOR_TEMPLATES) {
        _scrubTemplateExpressions2(dirty);
      }
      return dirty;
    }
    if (RETURN_DOM) {
      if (SAFE_FOR_TEMPLATES) {
        _scrubTemplateExpressions2(body);
      }
      if (RETURN_DOM_FRAGMENT) {
        returnNode = createDocumentFragment.call(body.ownerDocument);
        while (body.firstChild) {
          returnNode.appendChild(body.firstChild);
        }
      } else {
        returnNode = body;
      }
      if (ALLOWED_ATTR.shadowroot || ALLOWED_ATTR.shadowrootmode) {
        returnNode = importNode.call(originalDocument, returnNode, true);
      }
      return returnNode;
    }
    let serializedHTML = WHOLE_DOCUMENT ? body.outerHTML : body.innerHTML;
    if (WHOLE_DOCUMENT && ALLOWED_TAGS["!doctype"] && body.ownerDocument && body.ownerDocument.doctype && body.ownerDocument.doctype.name && regExpTest(DOCTYPE_NAME, body.ownerDocument.doctype.name)) {
      serializedHTML = "<!DOCTYPE " + body.ownerDocument.doctype.name + ">\n" + serializedHTML;
    }
    if (SAFE_FOR_TEMPLATES) {
      serializedHTML = _stripTemplateExpressions(serializedHTML);
    }
    return trustedTypesPolicy && RETURN_TRUSTED_TYPE ? _createTrustedHTML(serializedHTML) : serializedHTML;
  };
  DOMPurify.setConfig = function() {
    let cfg = arguments.length > 0 && arguments[0] !== void 0 ? arguments[0] : {};
    _parseConfig(cfg);
    SET_CONFIG = true;
    SET_CONFIG_ALLOWED_TAGS = ALLOWED_TAGS;
    SET_CONFIG_ALLOWED_ATTR = ALLOWED_ATTR;
  };
  DOMPurify.clearConfig = function() {
    CONFIG = null;
    SET_CONFIG = false;
    SET_CONFIG_ALLOWED_TAGS = null;
    SET_CONFIG_ALLOWED_ATTR = null;
    trustedTypesPolicy = defaultTrustedTypesPolicy;
    emptyHTML = "";
  };
  DOMPurify.isValidAttribute = function(tag, attr, value) {
    if (!CONFIG) {
      _parseConfig({});
    }
    const lcTag = transformCaseFunc(tag);
    const lcName = transformCaseFunc(attr);
    return _isValidAttribute(lcTag, lcName, value);
  };
  DOMPurify.addHook = function(entryPoint, hookFunction) {
    if (typeof hookFunction !== "function") {
      return;
    }
    if (!objectHasOwnProperty(hooks, entryPoint)) {
      return;
    }
    arrayPush(hooks[entryPoint], hookFunction);
  };
  DOMPurify.removeHook = function(entryPoint, hookFunction) {
    if (!objectHasOwnProperty(hooks, entryPoint)) {
      return void 0;
    }
    if (hookFunction !== void 0) {
      const index = arrayLastIndexOf(hooks[entryPoint], hookFunction);
      return index === -1 ? void 0 : arraySplice(hooks[entryPoint], index, 1)[0];
    }
    return arrayPop(hooks[entryPoint]);
  };
  DOMPurify.removeHooks = function(entryPoint) {
    if (!objectHasOwnProperty(hooks, entryPoint)) {
      return;
    }
    hooks[entryPoint] = [];
  };
  DOMPurify.removeAllHooks = function() {
    hooks = _createHooksMap();
  };
  return DOMPurify;
}
var purify = createDOMPurify();

// src/components/MarkdownContent.tsx
var labels = { js: "JavaScript", javascript: "JavaScript", ts: "TypeScript", typescript: "TypeScript", py: "Python", python: "Python", sh: "Shell", bash: "Bash", json: "JSON", go: "Go", css: "CSS", html: "HTML" };
function MarkdownContent({ content }) {
  const html2 = T2(() => {
    const clean = purify.sanitize(g2.parse(content, { async: false }), {
      USE_PROFILES: { html: true },
      FORBID_TAGS: ["style", "form", "input", "button", "iframe"],
      FORBID_ATTR: ["style"]
    });
    const template = document.createElement("template");
    template.innerHTML = clean;
    for (const code of Array.from(template.content.querySelectorAll("pre > code"))) {
      const pre = code.parentElement;
      const language = Array.from(code.classList).find((c3) => c3.startsWith("language-"))?.slice(9) ?? "";
      code.className = `hljs${language ? ` language-${language}` : ""}`;
      const block = document.createElement("div");
      block.className = "code-block";
      const header = document.createElement("div");
      header.className = "code-block__header";
      const label = document.createElement("span");
      label.className = "code-block__lang";
      label.textContent = labels[language.toLowerCase()] || language || "Text";
      const button = document.createElement("button");
      button.className = "code-block__copy";
      button.setAttribute("aria-label", "Copy code");
      const bytes = new TextEncoder().encode(code.textContent ?? "");
      button.dataset.code = btoa(Array.from(bytes, (byte) => String.fromCharCode(byte)).join(""));
      const icon = document.createElement("i");
      icon.className = "codicon codicon-copy";
      button.append(icon);
      header.append(label, button);
      pre.replaceWith(block);
      block.append(header, pre);
    }
    return template.innerHTML;
  }, [content]);
  return /* @__PURE__ */ u3("div", { className: "message-list__content", onClick: async (event) => {
    const button = event.target.closest("button.code-block__copy");
    if (!button || !event.currentTarget.contains(button)) return;
    try {
      const bytes = Uint8Array.from(atob(button.dataset.code ?? ""), (c3) => c3.charCodeAt(0));
      await navigator.clipboard.writeText(new TextDecoder().decode(bytes));
    } catch {
    }
  }, dangerouslySetInnerHTML: { __html: html2 } });
}

// src/components/Timeline.tsx
function valueText(value) {
  if (typeof value === "string") return value;
  if (value == null) return "";
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
}
function ToolCallBlock({ call, result }) {
  const [open, setOpen] = h2(false);
  const [expanded, setExpanded] = h2(false);
  const name = call.name || result?.toolName || "tool";
  const input = valueText(call.arguments);
  const output = result?.content ?? "";
  const lines = output.split("\n");
  const hiddenLines = !expanded && lines.length > 20 ? lines.length - 20 : 0;
  const displayedOutput = hiddenLines ? lines.slice(-20).join("\n") : output;
  return /* @__PURE__ */ u3("div", { className: "message-list__tool-call", children: [
    /* @__PURE__ */ u3("button", { className: "message-list__tool-call-header", type: "button", onClick: () => setOpen((value) => !value), "aria-expanded": open, children: [
      /* @__PURE__ */ u3("span", { className: "message-list__tool-call-icon", children: open ? "\u25BE" : "\u25B8" }),
      /* @__PURE__ */ u3("span", { className: "message-list__tool-call-name", children: name }),
      result && /* @__PURE__ */ u3("span", { className: "message-list__tool-call-badge", children: result.toolOk === false ? "failed" : "done" })
    ] }),
    open && /* @__PURE__ */ u3("div", { className: "message-list__tool-call-body", children: [
      input && /* @__PURE__ */ u3("div", { className: "tool-call__pre-wrapper", children: [
        /* @__PURE__ */ u3(CopyButton, { text: input }),
        /* @__PURE__ */ u3("pre", { className: "message-list__tool-call-code", children: input })
      ] }),
      output && /* @__PURE__ */ u3(b, { children: [
        /* @__PURE__ */ u3("div", { className: "message-list__tool-call-result-label", children: "Result" }),
        /* @__PURE__ */ u3("div", { className: "tool-call__pre-wrapper", children: [
          hiddenLines > 0 && /* @__PURE__ */ u3("button", { type: "button", className: "tool-call__hidden-lines", title: "Show full output", onClick: () => setExpanded(true), children: [
            hiddenLines,
            " lines hidden \u2014 click to expand"
          ] }),
          expanded && /* @__PURE__ */ u3("button", { type: "button", className: "tool-call__hidden-lines tool-call__hidden-lines--collapse", onClick: () => setExpanded(false), children: "collapse" }),
          /* @__PURE__ */ u3(CopyButton, { text: output }),
          /* @__PURE__ */ u3("pre", { className: "message-list__tool-call-code", children: displayedOutput })
        ] })
      ] })
    ] })
  ] });
}
function AttachmentChip({ attachment }) {
  const [previewUrl, setPreviewUrl] = h2(null);
  const contentUrl = `/api/media/${encodeURIComponent(attachment.mediaId)}/content`;
  const thumbnailUrl = `/api/media/${encodeURIComponent(attachment.mediaId)}/thumbnail`;
  const token = localStorage.getItem("tau.web.authToken");
  y2(() => {
    if (!token || !attachment.mediaType.startsWith("image/")) return;
    let objectUrl = null;
    const controller = new AbortController();
    void fetch(thumbnailUrl, { headers: { Authorization: `Bearer ${token}` }, credentials: "same-origin", signal: controller.signal }).then((response) => response.ok ? response.blob() : Promise.reject(new Error("Preview unavailable"))).then((blob) => {
      objectUrl = URL.createObjectURL(blob);
      setPreviewUrl(objectUrl);
    }).catch(() => void 0);
    return () => {
      controller.abort();
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [attachment.mediaType, thumbnailUrl, token]);
  const download = async (event) => {
    if (!token) return;
    event.preventDefault();
    const response = await fetch(contentUrl, { headers: { Authorization: `Bearer ${token}` }, credentials: "same-origin" });
    if (!response.ok) return;
    const objectUrl = URL.createObjectURL(await response.blob());
    const link = document.createElement("a");
    link.href = objectUrl;
    link.download = attachment.filename;
    link.click();
    URL.revokeObjectURL(objectUrl);
  };
  return /* @__PURE__ */ u3("a", { className: "attachment-chip", href: contentUrl, target: "_blank", rel: "noopener", title: attachment.filename, onClick: (event) => void download(event), children: [
    attachment.mediaType.startsWith("image/") ? /* @__PURE__ */ u3("img", { className: "attachment-chip__preview", src: previewUrl ?? thumbnailUrl, alt: "", loading: "lazy" }) : /* @__PURE__ */ u3("span", { className: "attachment-chip__icon", "aria-hidden": "true", children: "\u{1F4C4}" }),
    /* @__PURE__ */ u3("span", { className: "attachment-chip__name", children: attachment.filename }),
    /* @__PURE__ */ u3("i", { className: "codicon codicon-desktop-download attachment-chip__action", "aria-hidden": "true" })
  ] });
}
function MessageItem({ item, resultByCall }) {
  const isUser = item.role === "user";
  const isTool = item.role === "tool";
  if (isTool) return null;
  return /* @__PURE__ */ u3("div", { className: `message-list__item message-list__item--${isUser ? "user" : "agent"}`, "data-message-id": item.id, children: [
    /* @__PURE__ */ u3("div", { className: `message-list__avatar-circle message-list__avatar-circle--${isUser ? "user" : "agent"}`, "aria-hidden": "true", children: isUser ? "Y" : "\u03C4" }),
    /* @__PURE__ */ u3("div", { className: item.live ? "message-list__body message-list__body--draft" : "message-list__body", children: [
      /* @__PURE__ */ u3("div", { className: "message-list__header", children: [
        /* @__PURE__ */ u3("span", { className: `message-list__name message-list__name--${isUser ? "user" : "agent"}`, children: isUser ? "You" : "Tau" }),
        /* @__PURE__ */ u3("span", { className: "message-list__time", children: item.live ? "live" : item.meta })
      ] }),
      item.toolCalls && item.toolCalls.length > 0 && /* @__PURE__ */ u3("div", { className: "message-list__tool-calls", children: item.toolCalls.map((call, index) => /* @__PURE__ */ u3(ToolCallBlock, { call, result: call.id ? resultByCall.get(call.id) : void 0 }, call.id ?? index)) }),
      item.content && (isUser ? /* @__PURE__ */ u3("div", { className: "message-list__content", children: item.content }) : /* @__PURE__ */ u3(MarkdownContent, { content: item.content })),
      item.attachments && item.attachments.length > 0 && /* @__PURE__ */ u3("div", { className: "message-list__attachments", children: item.attachments.map((attachment) => /* @__PURE__ */ u3(AttachmentChip, { attachment }, attachment.mediaId)) })
    ] })
  ] });
}
function Timeline() {
  const [timeline, setTimeline] = h2({ selected: false, items: [] });
  _2(() => {
    const update = (event) => {
      const detail = event.detail;
      if (detail && Array.isArray(detail.items)) setTimeline(detail);
    };
    window.addEventListener("tau:timeline-render", update);
    return () => window.removeEventListener("tau:timeline-render", update);
  }, []);
  const resultByCall = /* @__PURE__ */ new Map();
  for (const item of timeline.items) if (item.role === "tool" && item.toolCallId) resultByCall.set(item.toolCallId, item);
  const visibleItems = timeline.items.filter((item) => item.role !== "tool");
  const empty2 = !timeline.selected ? "Select or create a session to load the timeline." : "No persisted messages yet.";
  return /* @__PURE__ */ u3(b, { children: [
    /* @__PURE__ */ u3("div", { className: "extension-slot", "data-extension-slot": "timeline_before" }),
    /* @__PURE__ */ u3("div", { id: "timeline-main", className: "message-list", tabIndex: -1, children: [
      /* @__PURE__ */ u3("div", { id: "timeline-meta", className: "message-list__empty", "aria-live": "polite", children: "Load a session to inspect persisted messages." }),
      /* @__PURE__ */ u3("div", { id: "timeline-list", "aria-live": "polite", tabIndex: 0, children: visibleItems.length === 0 ? /* @__PURE__ */ u3("div", { className: "message-list__empty", children: /* @__PURE__ */ u3("p", { children: empty2 }) }) : visibleItems.map((item, index) => /* @__PURE__ */ u3(MessageItem, { item, resultByCall }, item.id ?? index)) })
    ] }),
    /* @__PURE__ */ u3("div", { className: "extension-slot", "data-extension-slot": "timeline_after" })
  ] });
}
function SessionRuntime() {
  const [branches, setBranches] = h2([]);
  _2(() => {
    const update = (event) => setBranches(event.detail.items);
    window.addEventListener("tau:branches-render", update);
    return () => window.removeEventListener("tau:branches-render", update);
  }, []);
  return /* @__PURE__ */ u3("div", { className: "agent-status-panel", "aria-label": "Session runtime", children: [
    /* @__PURE__ */ u3("div", { className: "agent-status-panel__status", "aria-live": "polite", children: [
      /* @__PURE__ */ u3("span", { id: "agent-status-indicator", className: "agent-status-panel__status-dot", "aria-hidden": "true" }),
      /* @__PURE__ */ u3("span", { id: "agent-status-text", className: "agent-status-panel__status-text", children: "No session selected" })
    ] }),
    /* @__PURE__ */ u3("section", { className: "agent-status-panel__section", children: [
      /* @__PURE__ */ u3("div", { className: "agent-status-panel__title", children: "Session branch" }),
      /* @__PURE__ */ u3("div", { id: "branch-list", className: "agent-status-panel__tools", children: [
        branches.map((branch) => /* @__PURE__ */ u3("button", { type: "button", className: "branch-button", "data-active": String(branch.active), onClick: () => window.dispatchEvent(new CustomEvent("tau:branch-select", { detail: { leafId: branch.leafId } })), children: branch.label })),
        !branches.length && /* @__PURE__ */ u3("span", { className: "muted-text", children: "No persisted branches yet." })
      ] })
    ] })
  ] });
}

// src/api/client.ts
var ApiError = class extends Error {
  constructor(message, status, code = "request_failed", details) {
    super(message);
    this.status = status;
    this.code = code;
    this.details = details;
    this.name = "ApiError";
  }
};
var SAFE_METHODS = /* @__PURE__ */ new Set(["GET", "HEAD", "OPTIONS", "TRACE"]);
var ApiClient = class {
  constructor(options = {}) {
    this.options = options;
    this.fetchImpl = options.fetch ?? globalThis.fetch.bind(globalThis);
  }
  fetchImpl;
  async request(path, init = {}) {
    const method = (init.method ?? "GET").toUpperCase();
    const headers = new Headers(init.headers);
    headers.set("Accept", "application/json");
    if (!SAFE_METHODS.has(method)) headers.set("X-Tau-CSRF", "1");
    const token = this.options.authToken?.();
    if (token) headers.set("Authorization", `Bearer ${token}`);
    let body = init.body;
    if (init.json !== void 0) {
      headers.set("Content-Type", "application/json");
      body = JSON.stringify(init.json);
    }
    const response = await this.fetchImpl(path, {
      ...init,
      body,
      credentials: "same-origin",
      headers,
      method
    });
    if (response.status === 204) return null;
    const isJson = response.headers.get("content-type")?.includes("application/json") ?? false;
    const payload = isJson ? await response.json() : await response.text();
    if (!response.ok) {
      const error = typeof payload === "object" && payload !== null ? payload.error : void 0;
      throw new ApiError(
        error?.message ?? `${response.status} ${response.statusText}`.trim(),
        response.status,
        error?.code,
        error?.details
      );
    }
    return payload;
  }
};

// src/api/tau.ts
var id = encodeURIComponent;
var TauApi = class {
  constructor(client = new ApiClient()) {
    this.client = client;
  }
  settings() {
    return this.client.request("/api/settings");
  }
  onboarding() {
    return this.client.request("/api/onboarding");
  }
  configureOnboarding(input) {
    return this.client.request("/api/onboarding", { method: "PUT", json: input });
  }
  models() {
    return this.client.request("/api/models");
  }
  commands() {
    return this.client.request("/api/commands");
  }
  sessions() {
    return this.client.request("/api/sessions");
  }
  session(sessionId) {
    return this.client.request(`/api/sessions/${id(sessionId)}`);
  }
  createSession(input) {
    return this.client.request("/api/sessions", { method: "POST", json: input });
  }
  updateSession(sessionId, input) {
    return this.client.request(`/api/sessions/${id(sessionId)}`, { method: "PATCH", json: input });
  }
  archiveSession(sessionId) {
    return this.client.request(`/api/sessions/${id(sessionId)}`, { method: "DELETE" });
  }
  timeline(sessionId) {
    return this.client.request(`/api/sessions/${id(sessionId)}/timeline`);
  }
  entries(sessionId) {
    return this.client.request(`/api/sessions/${id(sessionId)}/entries`);
  }
  messages(sessionId) {
    return this.client.request(`/api/sessions/${id(sessionId)}/messages`);
  }
  branches(sessionId) {
    return this.client.request(`/api/sessions/${id(sessionId)}/branches`);
  }
  selectBranch(sessionId, input) {
    return this.client.request(`/api/sessions/${id(sessionId)}/branches/select`, { method: "POST", json: input });
  }
  context(sessionId) {
    return this.client.request(`/api/sessions/${id(sessionId)}/context`);
  }
  usage(sessionId) {
    return this.client.request(`/api/sessions/${id(sessionId)}/usage`);
  }
  async runs(sessionId) {
    const response = await this.client.request(`/api/sessions/${id(sessionId)}/runs`);
    return response.runs;
  }
  submitRun(sessionId, input) {
    return this.client.request(`/api/sessions/${id(sessionId)}/runs`, { method: "POST", json: input });
  }
  runAction(runId, action) {
    return this.client.request(`/api/runs/${id(runId)}/${action}`, { method: "POST" });
  }
  async queue(sessionId, kind) {
    const query = kind ? `?kind=${id(kind)}` : "";
    const response = await this.client.request(`/api/sessions/${id(sessionId)}/queue${query}`);
    return response.queue;
  }
  enqueue(sessionId, content, kind) {
    return this.client.request(`/api/sessions/${id(sessionId)}/queue`, { method: "POST", json: { content, kind } });
  }
  queueRunMessage(runId, content, kind) {
    return this.client.request(`/api/runs/${id(runId)}/messages`, { method: "POST", json: { content, kind } });
  }
  dispatchNext(runId, kind) {
    return this.client.request(`/api/runs/${id(runId)}/queue/${id(kind)}/dispatch`, { method: "POST" });
  }
  plan(sessionId) {
    return this.client.request(`/api/sessions/${id(sessionId)}/plan`);
  }
  savePlan(sessionId, plan) {
    return this.client.request(`/api/sessions/${id(sessionId)}/plan`, { method: "PUT", json: plan });
  }
  approvals(sessionId) {
    return this.client.request(`/api/sessions/${id(sessionId)}/approvals`);
  }
  resolveApproval(approvalId, resolution) {
    return this.client.request(`/api/approvals/${id(approvalId)}`, { method: "POST", json: { resolution } });
  }
  media() {
    return this.client.request("/api/media");
  }
  uploadMedia(body) {
    return this.client.request("/api/media", { method: "POST", body });
  }
  deleteMedia(mediaId) {
    return this.client.request(`/api/media/${id(mediaId)}`, { method: "DELETE" });
  }
  files(path = "") {
    return this.client.request(`/api/files?path=${encodeURIComponent(path)}`);
  }
  search(query) {
    return this.client.request(`/api/search?q=${encodeURIComponent(query)}`);
  }
  dashboard() {
    return this.client.request("/dashboard");
  }
  meters() {
    return this.client.request("/meters");
  }
  frontendModules() {
    return this.client.request("/api/extensions/frontend-modules");
  }
  widget(extensionId, widgetId) {
    return this.client.request(`/api/extensions/widgets/${id(extensionId)}/${id(widgetId)}`);
  }
  widgetAction(extensionId, widgetId, action, input) {
    return this.client.request(`/api/extensions/widgets/${id(extensionId)}/${id(widgetId)}/actions/${id(action)}`, { method: "POST", json: input });
  }
  eventUrl(sessionId) {
    return `/api/events?session_id=${id(sessionId)}`;
  }
};

// src/components/Onboarding.tsx
var api = new TauApi();
function Onboarding({ onOpenChange }) {
  const [state, setState] = h2(null);
  const [open, setOpen] = h2(false);
  const [provider, setProvider] = h2("");
  const [model, setModel] = h2("");
  const [credential, setCredential] = h2("");
  const [error, setError] = h2("");
  const [saving, setSaving] = h2(false);
  y2(() => {
    api.onboarding().then((next) => {
      setState(next);
      setProvider(next.default_provider);
      setModel(next.default_model);
      setOpen(!next.configured);
    }).catch((reason) => setError(String(reason)));
  }, []);
  y2(() => {
    onOpenChange(open);
  }, [open, onOpenChange]);
  const selected = T2(
    () => state?.providers.find((item) => item.name === provider),
    [state, provider]
  );
  function chooseProvider(name) {
    const next = state?.providers.find((item) => item.name === name);
    setProvider(name);
    setModel(next?.default_model ?? "");
    setCredential("");
    setError("");
  }
  async function submit(event) {
    event.preventDefault();
    setSaving(true);
    setError("");
    try {
      const next = await api.configureOnboarding({
        provider,
        model,
        ...credential.trim() ? { credential } : {}
      });
      setState(next);
      setCredential("");
      setOpen(false);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : String(reason));
    } finally {
      setSaving(false);
    }
  }
  if (!state && !error) return null;
  return /* @__PURE__ */ u3(b, { children: [
    /* @__PURE__ */ u3("button", { className: "provider-setup-trigger", type: "button", onClick: () => setOpen(true), children: "Provider setup" }),
    open && state ? /* @__PURE__ */ u3("div", { className: "provider-wizard", children: /* @__PURE__ */ u3("section", { className: "provider-wizard__content", "aria-labelledby": "onboarding-title", children: [
      /* @__PURE__ */ u3("h2", { id: "onboarding-title", className: "provider-wizard__title", children: "Connect a model provider" }),
      /* @__PURE__ */ u3("p", { className: "provider-wizard__subtitle", children: "Choose a provider and model. Credentials are stored locally and never returned by this API." }),
      /* @__PURE__ */ u3("form", { className: "provider-wizard__apikey-form", onSubmit: submit, children: [
        /* @__PURE__ */ u3("label", { className: "settings-panel__field", children: [
          /* @__PURE__ */ u3("span", { className: "settings-panel__label", children: "Provider" }),
          /* @__PURE__ */ u3("select", { className: "settings-panel__select", value: provider, onChange: (event) => chooseProvider(event.currentTarget.value), children: state.providers.map((item) => /* @__PURE__ */ u3("option", { value: item.name, children: item.name })) })
        ] }),
        /* @__PURE__ */ u3("label", { className: "settings-panel__field", children: [
          /* @__PURE__ */ u3("span", { className: "settings-panel__label", children: "Model" }),
          /* @__PURE__ */ u3("select", { className: "settings-panel__select", value: model, onChange: (event) => setModel(event.currentTarget.value), children: (selected?.models ?? []).map((item) => /* @__PURE__ */ u3("option", { value: item, children: item })) })
        ] }),
        selected?.credential_name ? /* @__PURE__ */ u3("label", { className: "settings-panel__field", children: [
          /* @__PURE__ */ u3("span", { className: "settings-panel__label", children: "API key" }),
          /* @__PURE__ */ u3("input", { className: "provider-wizard__input", type: "password", value: credential, autocomplete: "off", onInput: (event) => setCredential(event.currentTarget.value), placeholder: selected.configured ? "Stored credential (leave blank to keep)" : "Required" })
        ] }) : null,
        error ? /* @__PURE__ */ u3("p", { className: "provider-wizard__error", role: "alert", children: error }) : null,
        /* @__PURE__ */ u3("div", { className: "provider-wizard__apikey-actions", children: [
          /* @__PURE__ */ u3("button", { className: "provider-wizard__btn provider-wizard__btn--secondary", type: "button", onClick: () => setOpen(false), children: "Cancel" }),
          /* @__PURE__ */ u3("button", { className: "provider-wizard__btn provider-wizard__btn--primary", type: "submit", disabled: saving || !provider || !model || Boolean(selected?.credential_name && !selected.configured && !credential.trim()), children: saving ? "Saving\u2026" : "Save and continue" })
        ] })
      ] })
    ] }) }) : null
  ] });
}

// src/components/QueueStack.tsx
var api2 = new TauApi();
var ACTIVE_RUN_STATUSES = /* @__PURE__ */ new Set(["pending", "running"]);
function queueText(content) {
  if (typeof content === "string") return content;
  try {
    return JSON.stringify(content);
  } catch {
    return String(content);
  }
}
function findActiveRun(runs) {
  return runs.find((run) => ACTIVE_RUN_STATUSES.has(run.status)) ?? null;
}
function QueueStack() {
  const [state, setState] = h2({ sessionId: null, items: [], activeRun: null });
  const [busyKind, setBusyKind] = h2(null);
  const [error, setError] = h2("");
  const refresh = q2(async (sessionId) => {
    if (!sessionId) {
      setState({ sessionId: null, items: [], activeRun: null });
      return;
    }
    try {
      const [items2, runs] = await Promise.all([api2.queue(sessionId), api2.runs(sessionId)]);
      setState({ sessionId, items: items2, activeRun: findActiveRun(runs) });
      setError("");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to load queued messages.");
    }
  }, []);
  _2(() => {
    window.dispatchEvent(new CustomEvent("tau:active-run", { detail: { run: state.activeRun } }));
  }, [state.activeRun]);
  _2(() => {
    const selected = (event) => {
      const sessionId = event.detail?.sessionId ?? null;
      setState({ sessionId, items: [], activeRun: null });
      void refresh(sessionId);
    };
    const changed = () => void refresh(state.sessionId);
    window.addEventListener("tau:session-selected", selected);
    window.addEventListener("tau:queue-changed", changed);
    return () => {
      window.removeEventListener("tau:session-selected", selected);
      window.removeEventListener("tau:queue-changed", changed);
    };
  }, [refresh, state.sessionId]);
  const items = T2(
    () => [...state.items].sort((left, right) => left.queue_kind.localeCompare(right.queue_kind) || left.position - right.position),
    [state.items]
  );
  const dispatch = q2(async (kind) => {
    if (!state.activeRun) return;
    setBusyKind(kind);
    try {
      await api2.dispatchNext(state.activeRun.run_id, kind);
      await refresh(state.sessionId);
      window.dispatchEvent(new CustomEvent("tau:queue-dispatched", { detail: { kind } }));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to dispatch queued message.");
    } finally {
      setBusyKind(null);
    }
  }, [refresh, state.activeRun, state.sessionId]);
  const copyToComposer = q2((item) => {
    const input = document.getElementById("compose-input");
    if (!input) return;
    input.value = queueText(item.content);
    input.dispatchEvent(new Event("input", { bubbles: true }));
    input.focus();
  }, []);
  if (items.length === 0 && !error) return null;
  const firstByKind = /* @__PURE__ */ new Map();
  for (const item of items) {
    if (!firstByKind.has(item.queue_kind)) firstByKind.set(item.queue_kind, item.queue_id);
  }
  return /* @__PURE__ */ u3("div", { className: "queue-stack", "aria-label": "Queued messages", children: [
    error && /* @__PURE__ */ u3("div", { className: "queue-stack__error", role: "status", children: error }),
    items.map((item) => {
      const text2 = queueText(item.content);
      const isHead = firstByKind.get(item.queue_kind) === item.queue_id;
      return /* @__PURE__ */ u3("div", { className: "queue-stack__item", children: [
        /* @__PURE__ */ u3("div", { className: "queue-stack__content", title: text2, children: [
          /* @__PURE__ */ u3("span", { className: "queue-stack__kind", children: item.queue_kind === "follow_up" ? "Follow-up" : "Steer" }),
          text2.length > 80 ? `${text2.slice(0, 80)}\u2026` : text2
        ] }),
        /* @__PURE__ */ u3("div", { className: "queue-stack__actions", children: [
          /* @__PURE__ */ u3("button", { type: "button", className: "queue-stack__btn queue-stack__btn--edit", onClick: () => copyToComposer(item), title: "Copy to compose", "aria-label": "Copy queued message to compose", children: /* @__PURE__ */ u3("i", { className: "codicon codicon-edit", "aria-hidden": "true" }) }),
          isHead && /* @__PURE__ */ u3("button", { type: "button", className: "queue-stack__btn queue-stack__btn--steer", disabled: !state.activeRun || busyKind === item.queue_kind, onClick: () => void dispatch(item.queue_kind), title: state.activeRun ? `Dispatch next ${item.queue_kind === "follow_up" ? "follow-up" : "steer"}` : "A pending or running run is required", children: "\u21B5 Dispatch" })
        ] })
      ] }, item.queue_id);
    })
  ] });
}

// src/components/ApprovalDialog.tsx
function ApprovalDialog() {
  const [approval, setApproval] = h2(null);
  const [busy, setBusy] = h2(false);
  const denyRef = A2(null);
  _2(() => {
    const update = (event) => {
      setBusy(false);
      setApproval(event.detail?.approval ?? null);
    };
    window.addEventListener("tau:approval-render", update);
    return () => window.removeEventListener("tau:approval-render", update);
  }, []);
  y2(() => {
    if (!approval) return;
    denyRef.current?.focus();
    const escape = (event) => {
      if (event.key !== "Escape") return;
      event.preventDefault();
      respond("deny");
    };
    window.addEventListener("keydown", escape, true);
    return () => window.removeEventListener("keydown", escape, true);
  }, [approval]);
  const respond = (decision) => {
    if (!approval || busy) return;
    setBusy(true);
    window.dispatchEvent(new CustomEvent("tau:approval-response", { detail: { approvalId: approval.approval_id, decision } }));
  };
  if (!approval) return null;
  return /* @__PURE__ */ u3("div", { className: "modal-dialog__backdrop approval-backdrop", "data-approval-id": approval.approval_id, role: "presentation", children: /* @__PURE__ */ u3("section", { className: "modal-dialog approval-prompt", role: "alertdialog", "aria-modal": "true", "aria-labelledby": "approval-title", "aria-describedby": "approval-description", onMouseDown: (event) => event.stopPropagation(), children: [
    /* @__PURE__ */ u3("h2", { id: "approval-title", className: "modal-dialog__title", children: [
      "Allow ",
      approval.tool_name || "tool",
      "?"
    ] }),
    /* @__PURE__ */ u3("p", { id: "approval-description", className: "modal-dialog__description", children: approval.description || "The agent requested permission to run this tool." }),
    /* @__PURE__ */ u3("pre", { className: "modal-dialog__description approval-arguments", children: JSON.stringify(approval.arguments ?? {}, null, 2) }),
    /* @__PURE__ */ u3("div", { className: "modal-dialog__actions approval-actions", children: [
      /* @__PURE__ */ u3("button", { ref: denyRef, type: "button", className: "modal-dialog__btn modal-dialog__btn--destructive", disabled: busy, onClick: () => respond("deny"), children: "Deny" }),
      /* @__PURE__ */ u3("button", { type: "button", className: "modal-dialog__btn modal-dialog__btn--primary", disabled: busy, onClick: () => respond("allow"), children: "Allow once" })
    ] })
  ] }) });
}

// src/hooks/useDashboardVisibility.ts
function useDashboardVisibility() {
  const [open, setOpen] = h2(false);
  y2(() => {
    window.dispatchEvent(new CustomEvent("tau:dashboard-visibility", { detail: { open } }));
  }, [open]);
  y2(() => {
    const requested = (event) => {
      setOpen(Boolean(event.detail?.open));
    };
    window.addEventListener("tau:set-dashboard", requested);
    return () => window.removeEventListener("tau:set-dashboard", requested);
  }, []);
  return { dashboardOpen: open, setDashboardOpen: setOpen };
}

// src/hooks/useDrawers.ts
function useDrawers() {
  const [drawer, setDrawer] = h2(null);
  const close = () => setDrawer(null);
  const open = (next) => setDrawer(next);
  const toggle = (next) => {
    setDrawer((current) => current === next ? null : next);
  };
  y2(() => {
    document.body.dataset.navOpen = String(drawer === "nav");
    document.body.dataset.panelOpen = String(drawer === "panel");
  }, [drawer]);
  y2(() => {
    const closeRequested = () => close();
    const openRequested = (event) => {
      const next = event.detail?.drawer;
      if (next === "nav" || next === "panel") open(next);
    };
    const resize = () => {
      if (window.innerWidth > 960) close();
    };
    const keydown = (event) => {
      if (event.key === "Escape") close();
    };
    window.addEventListener("tau:close-drawers", closeRequested);
    window.addEventListener("tau:open-drawer", openRequested);
    window.addEventListener("resize", resize);
    window.addEventListener("keydown", keydown);
    return () => {
      window.removeEventListener("tau:close-drawers", closeRequested);
      window.removeEventListener("tau:open-drawer", openRequested);
      window.removeEventListener("resize", resize);
      window.removeEventListener("keydown", keydown);
    };
  }, []);
  return { drawer, close, open, toggle };
}

// src/hooks/useMeterControls.ts
var readBoolean = (key, fallback) => {
  const value = window.localStorage.getItem(key);
  return value === null ? fallback : value === "true";
};
function useMeterControls() {
  const [enabled, setEnabled] = h2(() => readBoolean("tau.web.metersEnabled", true));
  const [collapsed, setCollapsed] = h2(() => readBoolean("tau.web.metersCollapsed", true));
  y2(() => {
    window.localStorage.setItem("tau.web.metersEnabled", String(enabled));
    window.localStorage.setItem("tau.web.metersCollapsed", String(collapsed));
    window.dispatchEvent(new CustomEvent("tau:meter-controls", { detail: { enabled, collapsed } }));
  }, [enabled, collapsed]);
  return {
    metersEnabled: enabled,
    metersCollapsed: collapsed,
    toggleMetersEnabled: () => setEnabled((current) => !current),
    toggleMetersCollapsed: () => setCollapsed((current) => !current)
  };
}

// src/hooks/useSessionFilter.ts
function useSessionFilter() {
  const [filter, setFilter] = h2(
    () => window.localStorage.getItem("tau.web.sessionFilter") === "archived" ? "archived" : "active"
  );
  const selectFilter = (next) => {
    setFilter(next);
    window.localStorage.setItem("tau.web.sessionFilter", next);
    window.dispatchEvent(new CustomEvent("tau:session-filter", { detail: { filter: next } }));
  };
  return { sessionFilter: filter, selectSessionFilter: selectFilter };
}

// src/hooks/useSidebarTabs.ts
var TABS = /* @__PURE__ */ new Set(["sessions", "workspace", "search", "plan", "settings"]);
function useSidebarTabs() {
  const [activeTab, setActiveTab] = h2("workspace");
  y2(() => {
    const requested = (event) => {
      const tab = event.detail?.tab;
      if (TABS.has(tab)) setActiveTab(tab);
    };
    window.addEventListener("tau:switch-tab", requested);
    return () => window.removeEventListener("tau:switch-tab", requested);
  }, []);
  const selectTab = (tab) => {
    setActiveTab(tab);
    window.dispatchEvent(new CustomEvent("tau:tab-selected", { detail: { tab } }));
  };
  return { activeTab, selectTab };
}

// src/index.tsx
function TauShell() {
  const { drawer, close, toggle } = useDrawers();
  const { activeTab, selectTab } = useSidebarTabs();
  const [onboardingOpen, setOnboardingOpen] = h2(false);
  const { dashboardOpen, setDashboardOpen } = useDashboardVisibility();
  const { metersEnabled, metersCollapsed, toggleMetersEnabled, toggleMetersCollapsed } = useMeterControls();
  const { sessionFilter, selectSessionFilter } = useSessionFilter();
  const settingsOpen = activeTab === "settings";
  const sidebarOpen = drawer !== null && !settingsOpen;
  const selectPanel = (panel) => {
    if (panel === "settings") {
      selectTab(settingsOpen ? "workspace" : "settings");
      close();
      return;
    }
    const target = panel === "sessions" ? "nav" : "panel";
    if (panel === activeTab && drawer === target) close();
    else {
      selectTab(panel);
      if (drawer !== target) toggle(target);
    }
  };
  return /* @__PURE__ */ u3(b, { children: [
    /* @__PURE__ */ u3("a", { className: "skip-link", href: "#timeline-main", children: "Skip to timeline" }),
    /* @__PURE__ */ u3("div", { className: "app-layout", children: [
      /* @__PURE__ */ u3(ActivityBar, { activePanel: activeTab, onPanelChange: selectPanel, onDashboard: () => setDashboardOpen(true) }),
      /* @__PURE__ */ u3("main", { className: "app-layout__main", children: [
        /* @__PURE__ */ u3("div", { className: "app-layout__content-area", children: [
          /* @__PURE__ */ u3("div", { className: "app-layout__sidebar-wrapper", hidden: settingsOpen, style: { width: sidebarOpen ? "300px" : "0" }, children: /* @__PURE__ */ u3(SidePanel, { activeTab, onSelectTab: selectTab, onClose: close, sessionFilter, onSelectSessionFilter: selectSessionFilter }) }),
          /* @__PURE__ */ u3("button", { id: "drawer-backdrop", className: "app-layout__sidebar-backdrop", type: "button", "aria-label": "Close sidebar", hidden: !sidebarOpen, onClick: close }),
          sidebarOpen && /* @__PURE__ */ u3("div", { className: "app-layout__resize-handle", role: "separator", "aria-orientation": "vertical", "aria-label": "Resize sidebar" }),
          /* @__PURE__ */ u3("div", { className: "app-layout__panel", children: [
            /* @__PURE__ */ u3(SettingsPanel, { hidden: !settingsOpen }),
            !settingsOpen && /* @__PURE__ */ u3(TabBar, {}),
            /* @__PURE__ */ u3("div", { className: "app-layout__tab-viewport", hidden: settingsOpen, children: /* @__PURE__ */ u3("div", { className: "app-layout__tab-content", children: [
              /* @__PURE__ */ u3(Onboarding, { onOpenChange: setOnboardingOpen }),
              /* @__PURE__ */ u3("section", { className: "chat", "aria-label": "Tau chat", hidden: onboardingOpen, children: [
                /* @__PURE__ */ u3("div", { className: "chat__messages", children: /* @__PURE__ */ u3(Timeline, {}) }),
                /* @__PURE__ */ u3(SessionRuntime, {}),
                /* @__PURE__ */ u3(QueueStack, {}),
                /* @__PURE__ */ u3(Dashboard, { open: dashboardOpen, onClose: () => setDashboardOpen(false) }),
                /* @__PURE__ */ u3(Composer, {})
              ] })
            ] }) })
          ] })
        ] }),
        /* @__PURE__ */ u3(StatusBar, { dashboardOpen, metersEnabled, metersCollapsed, onOpenSessions: () => selectPanel("sessions"), onToggleDashboard: () => setDashboardOpen((current) => !current), onToggleMetersEnabled: toggleMetersEnabled, onToggleMetersCollapsed: toggleMetersCollapsed }),
        /* @__PURE__ */ u3("div", { className: "mobile-toolbar", children: [
          /* @__PURE__ */ u3("button", { id: "mobile-nav-toggle", className: "mobile-toolbar__terminal-btn", type: "button", "aria-label": "Open sessions", "aria-expanded": drawer === "nav", onClick: () => selectPanel("sessions"), children: "Sessions" }),
          /* @__PURE__ */ u3("span", { className: "mobile-toolbar__model-slot", children: "Tau" }),
          /* @__PURE__ */ u3("button", { id: "mobile-panel-toggle", className: "mobile-toolbar__terminal-btn", type: "button", "aria-label": "Open workspace", "aria-expanded": drawer === "panel", onClick: () => selectPanel("workspace"), children: "Workspace" })
        ] })
      ] })
    ] }),
    /* @__PURE__ */ u3(ApprovalDialog, {}),
    /* @__PURE__ */ u3("aside", { id: "session-nav", hidden: true }),
    /* @__PURE__ */ u3("noscript", { children: /* @__PURE__ */ u3("p", { className: "noscript-banner", children: "Tau Web requires JavaScript." }) })
  ] });
}
var mount = document.getElementById("app");
if (!mount) throw new Error("Missing #app root element");
installSystemTheme();
B(/* @__PURE__ */ u3(TauShell, {}), mount);
