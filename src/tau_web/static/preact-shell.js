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
  for (var u4 in l3) n2[u4] = l3[u4];
  return n2;
}
function w(n2) {
  n2 && n2.parentNode && n2.parentNode.removeChild(n2);
}
function _(l3, u4, t3) {
  var i4, o3, r3, f4 = {};
  for (r3 in u4) "key" == r3 ? i4 = u4[r3] : "ref" == r3 ? o3 = u4[r3] : f4[r3] = u4[r3];
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
  for (var u4; l3 < n2.__k.length; l3++) if (null != (u4 = n2.__k[l3]) && null != u4.__e) return u4.__e;
  return "function" == typeof n2.type ? x(n2) : null;
}
function C(n2) {
  var l3, u4;
  if (null != (n2 = n2.__) && null != n2.__c) {
    for (n2.__e = n2.__c.base = null, l3 = 0; l3 < n2.__k.length; l3++) if (null != (u4 = n2.__k[l3]) && null != u4.__e) {
      n2.__e = n2.__c.base = u4.__e;
      break;
    }
    return C(n2);
  }
}
function S(n2) {
  (!n2.__d && (n2.__d = true) && i.push(n2) && !M.__r++ || o !== l.debounceRendering) && ((o = l.debounceRendering) || r)(M);
}
function M() {
  var n2, u4, t3, o3, r3, e3, c3, s3;
  for (i.sort(f); n2 = i.shift(); ) n2.__d && (u4 = i.length, o3 = void 0, e3 = (r3 = (t3 = n2).__v).__e, c3 = [], s3 = [], t3.__P && ((o3 = d({}, r3)).__v = r3.__v + 1, l.vnode && l.vnode(o3), O(t3.__P, o3, r3, t3.__n, t3.__P.namespaceURI, 32 & r3.__u ? [e3] : null, c3, null == e3 ? x(r3) : e3, !!(32 & r3.__u), s3), o3.__v = r3.__v, o3.__.__k[o3.__i] = o3, j(c3, o3, s3), o3.__e != e3 && C(o3)), i.length > u4 && i.sort(f));
  M.__r = 0;
}
function P(n2, l3, u4, t3, i4, o3, r3, f4, e3, c3, s3) {
  var a3, p3, y3, d3, w3, _2 = t3 && t3.__k || v, g2 = l3.length;
  for (u4.__d = e3, $(u4, l3, _2), e3 = u4.__d, a3 = 0; a3 < g2; a3++) null != (y3 = u4.__k[a3]) && (p3 = -1 === y3.__i ? h : _2[y3.__i] || h, y3.__i = a3, O(n2, y3, p3, i4, o3, r3, f4, e3, c3, s3), d3 = y3.__e, y3.ref && p3.ref != y3.ref && (p3.ref && N(p3.ref, null, y3), s3.push(y3.ref, y3.__c || d3, y3)), null == w3 && null != d3 && (w3 = d3), 65536 & y3.__u || p3.__k === y3.__k ? e3 = I(y3, e3, n2) : "function" == typeof y3.type && void 0 !== y3.__d ? e3 = y3.__d : d3 && (e3 = d3.nextSibling), y3.__d = void 0, y3.__u &= -196609);
  u4.__d = e3, u4.__e = w3;
}
function $(n2, l3, u4) {
  var t3, i4, o3, r3, f4, e3 = l3.length, c3 = u4.length, s3 = c3, a3 = 0;
  for (n2.__k = [], t3 = 0; t3 < e3; t3++) null != (i4 = l3[t3]) && "boolean" != typeof i4 && "function" != typeof i4 ? (r3 = t3 + a3, (i4 = n2.__k[t3] = "string" == typeof i4 || "number" == typeof i4 || "bigint" == typeof i4 || i4.constructor == String ? g(null, i4, null, null, null) : y(i4) ? g(b, { children: i4 }, null, null, null) : void 0 === i4.constructor && i4.__b > 0 ? g(i4.type, i4.props, i4.key, i4.ref ? i4.ref : null, i4.__v) : i4).__ = n2, i4.__b = n2.__b + 1, o3 = null, -1 !== (f4 = i4.__i = L(i4, u4, r3, s3)) && (s3--, (o3 = u4[f4]) && (o3.__u |= 131072)), null == o3 || null === o3.__v ? (-1 == f4 && a3--, "function" != typeof i4.type && (i4.__u |= 65536)) : f4 !== r3 && (f4 == r3 - 1 ? a3-- : f4 == r3 + 1 ? a3++ : (f4 > r3 ? a3-- : a3++, i4.__u |= 65536))) : i4 = n2.__k[t3] = null;
  if (s3) for (t3 = 0; t3 < c3; t3++) null != (o3 = u4[t3]) && 0 == (131072 & o3.__u) && (o3.__e == n2.__d && (n2.__d = x(o3)), V(o3, o3));
}
function I(n2, l3, u4) {
  var t3, i4;
  if ("function" == typeof n2.type) {
    for (t3 = n2.__k, i4 = 0; t3 && i4 < t3.length; i4++) t3[i4] && (t3[i4].__ = n2, l3 = I(t3[i4], l3, u4));
    return l3;
  }
  n2.__e != l3 && (l3 && n2.type && !u4.contains(l3) && (l3 = x(n2)), u4.insertBefore(n2.__e, l3 || null), l3 = n2.__e);
  do {
    l3 = l3 && l3.nextSibling;
  } while (null != l3 && 8 === l3.nodeType);
  return l3;
}
function L(n2, l3, u4, t3) {
  var i4 = n2.key, o3 = n2.type, r3 = u4 - 1, f4 = u4 + 1, e3 = l3[u4];
  if (null === e3 || e3 && i4 == e3.key && o3 === e3.type && 0 == (131072 & e3.__u)) return u4;
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
function T(n2, l3, u4) {
  "-" === l3[0] ? n2.setProperty(l3, null == u4 ? "" : u4) : n2[l3] = null == u4 ? "" : "number" != typeof u4 || p.test(l3) ? u4 : u4 + "px";
}
function A(n2, l3, u4, t3, i4) {
  var o3;
  n: if ("style" === l3) if ("string" == typeof u4) n2.style.cssText = u4;
  else {
    if ("string" == typeof t3 && (n2.style.cssText = t3 = ""), t3) for (l3 in t3) u4 && l3 in u4 || T(n2.style, l3, "");
    if (u4) for (l3 in u4) t3 && u4[l3] === t3[l3] || T(n2.style, l3, u4[l3]);
  }
  else if ("o" === l3[0] && "n" === l3[1]) o3 = l3 !== (l3 = l3.replace(/(PointerCapture)$|Capture$/i, "$1")), l3 = l3.toLowerCase() in n2 || "onFocusOut" === l3 || "onFocusIn" === l3 ? l3.toLowerCase().slice(2) : l3.slice(2), n2.l || (n2.l = {}), n2.l[l3 + o3] = u4, u4 ? t3 ? u4.u = t3.u : (u4.u = e, n2.addEventListener(l3, o3 ? s : c, o3)) : n2.removeEventListener(l3, o3 ? s : c, o3);
  else {
    if ("http://www.w3.org/2000/svg" == i4) l3 = l3.replace(/xlink(H|:h)/, "h").replace(/sName$/, "s");
    else if ("width" != l3 && "height" != l3 && "href" != l3 && "list" != l3 && "form" != l3 && "tabIndex" != l3 && "download" != l3 && "rowSpan" != l3 && "colSpan" != l3 && "role" != l3 && "popover" != l3 && l3 in n2) try {
      n2[l3] = null == u4 ? "" : u4;
      break n;
    } catch (n3) {
    }
    "function" == typeof u4 || (null == u4 || false === u4 && "-" !== l3[4] ? n2.removeAttribute(l3) : n2.setAttribute(l3, "popover" == l3 && 1 == u4 ? "" : u4));
  }
}
function F(n2) {
  return function(u4) {
    if (this.l) {
      var t3 = this.l[u4.type + n2];
      if (null == u4.t) u4.t = e++;
      else if (u4.t < t3.u) return;
      return t3(l.event ? l.event(u4) : u4);
    }
  };
}
function O(n2, u4, t3, i4, o3, r3, f4, e3, c3, s3) {
  var a3, h3, v3, p3, w3, _2, g2, m2, x2, C3, S2, M2, $2, I2, H, L2, T3 = u4.type;
  if (void 0 !== u4.constructor) return null;
  128 & t3.__u && (c3 = !!(32 & t3.__u), r3 = [e3 = u4.__e = t3.__e]), (a3 = l.__b) && a3(u4);
  n: if ("function" == typeof T3) try {
    if (m2 = u4.props, x2 = "prototype" in T3 && T3.prototype.render, C3 = (a3 = T3.contextType) && i4[a3.__c], S2 = a3 ? C3 ? C3.props.value : a3.__ : i4, t3.__c ? g2 = (h3 = u4.__c = t3.__c).__ = h3.__E : (x2 ? u4.__c = h3 = new T3(m2, S2) : (u4.__c = h3 = new k(m2, S2), h3.constructor = T3, h3.render = q), C3 && C3.sub(h3), h3.props = m2, h3.state || (h3.state = {}), h3.context = S2, h3.__n = i4, v3 = h3.__d = true, h3.__h = [], h3._sb = []), x2 && null == h3.__s && (h3.__s = h3.state), x2 && null != T3.getDerivedStateFromProps && (h3.__s == h3.state && (h3.__s = d({}, h3.__s)), d(h3.__s, T3.getDerivedStateFromProps(m2, h3.__s))), p3 = h3.props, w3 = h3.state, h3.__v = u4, v3) x2 && null == T3.getDerivedStateFromProps && null != h3.componentWillMount && h3.componentWillMount(), x2 && null != h3.componentDidMount && h3.__h.push(h3.componentDidMount);
    else {
      if (x2 && null == T3.getDerivedStateFromProps && m2 !== p3 && null != h3.componentWillReceiveProps && h3.componentWillReceiveProps(m2, S2), !h3.__e && (null != h3.shouldComponentUpdate && false === h3.shouldComponentUpdate(m2, h3.__s, S2) || u4.__v === t3.__v)) {
        for (u4.__v !== t3.__v && (h3.props = m2, h3.state = h3.__s, h3.__d = false), u4.__e = t3.__e, u4.__k = t3.__k, u4.__k.some(function(n3) {
          n3 && (n3.__ = u4);
        }), M2 = 0; M2 < h3._sb.length; M2++) h3.__h.push(h3._sb[M2]);
        h3._sb = [], h3.__h.length && f4.push(h3);
        break n;
      }
      null != h3.componentWillUpdate && h3.componentWillUpdate(m2, h3.__s, S2), x2 && null != h3.componentDidUpdate && h3.__h.push(function() {
        h3.componentDidUpdate(p3, w3, _2);
      });
    }
    if (h3.context = S2, h3.props = m2, h3.__P = n2, h3.__e = false, $2 = l.__r, I2 = 0, x2) {
      for (h3.state = h3.__s, h3.__d = false, $2 && $2(u4), a3 = h3.render(h3.props, h3.state, h3.context), H = 0; H < h3._sb.length; H++) h3.__h.push(h3._sb[H]);
      h3._sb = [];
    } else do {
      h3.__d = false, $2 && $2(u4), a3 = h3.render(h3.props, h3.state, h3.context), h3.state = h3.__s;
    } while (h3.__d && ++I2 < 25);
    h3.state = h3.__s, null != h3.getChildContext && (i4 = d(d({}, i4), h3.getChildContext())), x2 && !v3 && null != h3.getSnapshotBeforeUpdate && (_2 = h3.getSnapshotBeforeUpdate(p3, w3)), P(n2, y(L2 = null != a3 && a3.type === b && null == a3.key ? a3.props.children : a3) ? L2 : [L2], u4, t3, i4, o3, r3, f4, e3, c3, s3), h3.base = u4.__e, u4.__u &= -161, h3.__h.length && f4.push(h3), g2 && (h3.__E = h3.__ = null);
  } catch (n3) {
    if (u4.__v = null, c3 || null != r3) {
      for (u4.__u |= c3 ? 160 : 128; e3 && 8 === e3.nodeType && e3.nextSibling; ) e3 = e3.nextSibling;
      r3[r3.indexOf(e3)] = null, u4.__e = e3;
    } else u4.__e = t3.__e, u4.__k = t3.__k;
    l.__e(n3, u4, t3);
  }
  else null == r3 && u4.__v === t3.__v ? (u4.__k = t3.__k, u4.__e = t3.__e) : u4.__e = z(t3.__e, u4, t3, i4, o3, r3, f4, c3, s3);
  (a3 = l.diffed) && a3(u4);
}
function j(n2, u4, t3) {
  u4.__d = void 0;
  for (var i4 = 0; i4 < t3.length; i4++) N(t3[i4], t3[++i4], t3[++i4]);
  l.__c && l.__c(u4, n2), n2.some(function(u5) {
    try {
      n2 = u5.__h, u5.__h = [], n2.some(function(n3) {
        n3.call(u5);
      });
    } catch (n3) {
      l.__e(n3, u5.__v);
    }
  });
}
function z(u4, t3, i4, o3, r3, f4, e3, c3, s3) {
  var a3, v3, p3, d3, _2, g2, m2, b2 = i4.props, k3 = t3.props, C3 = t3.type;
  if ("svg" === C3 ? r3 = "http://www.w3.org/2000/svg" : "math" === C3 ? r3 = "http://www.w3.org/1998/Math/MathML" : r3 || (r3 = "http://www.w3.org/1999/xhtml"), null != f4) {
    for (a3 = 0; a3 < f4.length; a3++) if ((_2 = f4[a3]) && "setAttribute" in _2 == !!C3 && (C3 ? _2.localName === C3 : 3 === _2.nodeType)) {
      u4 = _2, f4[a3] = null;
      break;
    }
  }
  if (null == u4) {
    if (null === C3) return document.createTextNode(k3);
    u4 = document.createElementNS(r3, C3, k3.is && k3), c3 && (l.__m && l.__m(t3, f4), c3 = false), f4 = null;
  }
  if (null === C3) b2 === k3 || c3 && u4.data === k3 || (u4.data = k3);
  else {
    if (f4 = f4 && n.call(u4.childNodes), b2 = i4.props || h, !c3 && null != f4) for (b2 = {}, a3 = 0; a3 < u4.attributes.length; a3++) b2[(_2 = u4.attributes[a3]).name] = _2.value;
    for (a3 in b2) if (_2 = b2[a3], "children" == a3) ;
    else if ("dangerouslySetInnerHTML" == a3) p3 = _2;
    else if (!(a3 in k3)) {
      if ("value" == a3 && "defaultValue" in k3 || "checked" == a3 && "defaultChecked" in k3) continue;
      A(u4, a3, null, _2, r3);
    }
    for (a3 in k3) _2 = k3[a3], "children" == a3 ? d3 = _2 : "dangerouslySetInnerHTML" == a3 ? v3 = _2 : "value" == a3 ? g2 = _2 : "checked" == a3 ? m2 = _2 : c3 && "function" != typeof _2 || b2[a3] === _2 || A(u4, a3, _2, b2[a3], r3);
    if (v3) c3 || p3 && (v3.__html === p3.__html || v3.__html === u4.innerHTML) || (u4.innerHTML = v3.__html), t3.__k = [];
    else if (p3 && (u4.innerHTML = ""), P(u4, y(d3) ? d3 : [d3], t3, i4, o3, "foreignObject" === C3 ? "http://www.w3.org/1999/xhtml" : r3, f4, e3, f4 ? f4[0] : i4.__k && x(i4, 0), c3, s3), null != f4) for (a3 = f4.length; a3--; ) w(f4[a3]);
    c3 || (a3 = "value", "progress" === C3 && null == g2 ? u4.removeAttribute("value") : void 0 !== g2 && (g2 !== u4[a3] || "progress" === C3 && !g2 || "option" === C3 && g2 !== b2[a3]) && A(u4, a3, g2, b2[a3], r3), a3 = "checked", void 0 !== m2 && m2 !== u4[a3] && A(u4, a3, m2, b2[a3], r3));
  }
  return u4;
}
function N(n2, u4, t3) {
  try {
    if ("function" == typeof n2) {
      var i4 = "function" == typeof n2.__u;
      i4 && n2.__u(), i4 && null == u4 || (n2.__u = n2(u4));
    } else n2.current = u4;
  } catch (n3) {
    l.__e(n3, t3);
  }
}
function V(n2, u4, t3) {
  var i4, o3;
  if (l.unmount && l.unmount(n2), (i4 = n2.ref) && (i4.current && i4.current !== n2.__e || N(i4, null, u4)), null != (i4 = n2.__c)) {
    if (i4.componentWillUnmount) try {
      i4.componentWillUnmount();
    } catch (n3) {
      l.__e(n3, u4);
    }
    i4.base = i4.__P = null;
  }
  if (i4 = n2.__k) for (o3 = 0; o3 < i4.length; o3++) i4[o3] && V(i4[o3], u4, t3 || "function" != typeof n2.type);
  t3 || w(n2.__e), n2.__c = n2.__ = n2.__e = n2.__d = void 0;
}
function q(n2, l3, u4) {
  return this.constructor(n2, u4);
}
function B(u4, t3, i4) {
  var o3, r3, f4, e3;
  l.__ && l.__(u4, t3), r3 = (o3 = "function" == typeof i4) ? null : i4 && i4.__k || t3.__k, f4 = [], e3 = [], O(t3, u4 = (!o3 && i4 || t3).__k = _(b, null, [u4]), r3 || h, h, t3.namespaceURI, !o3 && i4 ? [i4] : r3 ? null : t3.firstChild ? n.call(t3.childNodes) : null, f4, !o3 && i4 ? i4 : r3 ? r3.__e : t3.firstChild, o3, e3), j(f4, u4, e3);
}
n = v.slice, l = { __e: function(n2, l3, u4, t3) {
  for (var i4, o3, r3; l3 = l3.__; ) if ((i4 = l3.__c) && !i4.__) try {
    if ((o3 = i4.constructor) && null != o3.getDerivedStateFromError && (i4.setState(o3.getDerivedStateFromError(n2)), r3 = i4.__d), null != i4.componentDidCatch && (i4.componentDidCatch(n2, t3 || {}), r3 = i4.__d), r3) return i4.__E = i4;
  } catch (l4) {
    n2 = l4;
  }
  throw n2;
} }, u = 0, t = function(n2) {
  return null != n2 && null == n2.constructor;
}, k.prototype.setState = function(n2, l3) {
  var u4;
  u4 = null != this.__s && this.__s !== this.state ? this.__s : this.__s = d({}, this.state), "function" == typeof n2 && (n2 = n2(d({}, u4), this.props)), n2 && d(u4, n2), null != n2 && this.__v && (l3 && this._sb.push(l3), S(this));
}, k.prototype.forceUpdate = function(n2) {
  this.__v && (this.__e = true, n2 && this.__h.push(n2), S(this));
}, k.prototype.render = b, i = [], r = "function" == typeof Promise ? Promise.prototype.then.bind(Promise.resolve()) : setTimeout, f = function(n2, l3) {
  return n2.__v.__b - l3.__v.__b;
}, M.__r = 0, e = 0, c = F(false), s = F(true), a = 0;

// node_modules/preact/jsx-runtime/dist/jsxRuntime.module.js
var f2 = 0;
var i2 = Array.isArray;
function u2(e3, t3, n2, o3, i4, u4) {
  t3 || (t3 = {});
  var a3, c3, l3 = t3;
  "ref" in t3 && (a3 = t3.ref, delete t3.ref);
  var p3 = { type: e3, props: l3, key: n2, ref: a3, __k: null, __: null, __b: 0, __e: null, __d: void 0, __c: null, constructor: void 0, __v: --f2, __i: -1, __u: 0, __source: i4, __self: u4 };
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
  return /* @__PURE__ */ u2("nav", { className: "activity-bar", "aria-label": "Activity bar", children: PANELS.map((panel) => {
    const active = panel.id === activePanel;
    return /* @__PURE__ */ u2(
      "button",
      {
        type: "button",
        className: `activity-bar__button ${active ? "is-active" : ""} ${panel.alignBottom ? "is-bottom" : ""}`,
        title: panel.label,
        "aria-label": panel.label,
        "aria-pressed": active,
        onClick: () => panel.id === "dashboard" ? onDashboard() : onPanelChange(panel.id),
        children: /* @__PURE__ */ u2("i", { className: `codicon ${panel.icon} activity-bar__icon`, "aria-hidden": "true" })
      },
      panel.id
    );
  }) });
}

// src/components/StatusBar.tsx
var Meter = ({ id: id2, label, icon }) => /* @__PURE__ */ u2("span", { className: "sys-stats__metric", title: `${label} usage`, children: [
  /* @__PURE__ */ u2("i", { className: `sys-stats__icon codicon ${icon}`, "aria-hidden": "true" }),
  /* @__PURE__ */ u2("span", { className: "sys-stats__label", children: label }),
  /* @__PURE__ */ u2("output", { id: `meter-${id2}-value`, className: "sys-stats__value", children: "--" }),
  /* @__PURE__ */ u2("svg", { id: `meter-${id2}-sparkline`, className: "sys-stats__sparkline", role: "img", "aria-label": `${label === "RSS" ? "Tau RSS" : label} history` })
] });
function StatusBar({ dashboardOpen, metersEnabled, metersCollapsed, onOpenSessions, onToggleDashboard, onToggleMetersEnabled, onToggleMetersCollapsed }) {
  return /* @__PURE__ */ u2("footer", { className: "app-layout__status-bar", role: "banner", "aria-label": "Tau status bar", children: [
    /* @__PURE__ */ u2("span", { className: "status-bar__conn", children: [
      /* @__PURE__ */ u2("span", { className: "status-bar__conn-dot status-bar__conn-dot--disconnected", "aria-hidden": "true" }),
      /* @__PURE__ */ u2("span", { id: "status-stream", className: "status-bar__conn-text", children: "Connecting\u2026" })
    ] }),
    /* @__PURE__ */ u2("span", { className: "session-pill-wrap", children: /* @__PURE__ */ u2("button", { className: "session-pill", type: "button", title: "Open sessions", onClick: onOpenSessions, children: [
      /* @__PURE__ */ u2("span", { className: "session-pill__dot session-pill__dot--current", "aria-hidden": "true" }),
      /* @__PURE__ */ u2("span", { id: "status-session", className: "session-pill__label", children: "No session selected" })
    ] }) }),
    /* @__PURE__ */ u2("span", { className: "model-badge-wrapper", children: [
      /* @__PURE__ */ u2("span", { id: "status-model", className: "model-badge model-badge--empty", children: "Unset" }),
      /* @__PURE__ */ u2("span", { id: "status-context", className: "usage-badge", children: "No context loaded" })
    ] }),
    /* @__PURE__ */ u2("span", { className: "status-bar__right", children: [
      /* @__PURE__ */ u2("span", { id: "system-meters", className: "sys-stats-bar", "data-enabled": String(metersEnabled), "data-collapsed": String(metersCollapsed), children: [
        /* @__PURE__ */ u2("span", { className: "sys-stats-bar__inline", children: /* @__PURE__ */ u2("span", { id: "meters-details", className: "sys-stats", children: [
          /* @__PURE__ */ u2(Meter, { id: "cpu", label: "CPU", icon: "codicon-pulse" }),
          /* @__PURE__ */ u2(Meter, { id: "ram", label: "RAM", icon: "codicon-circuit-board" }),
          /* @__PURE__ */ u2(Meter, { id: "rss", label: "RSS", icon: "codicon-package" }),
          /* @__PURE__ */ u2(Meter, { id: "swap", label: "SWP", icon: "codicon-arrow-swap" })
        ] }) }),
        /* @__PURE__ */ u2("output", { id: "meters-summary", className: "sys-stats-bar__compact", "aria-live": "polite", children: "Meters loading\u2026" }),
        /* @__PURE__ */ u2("button", { id: "meters-collapse-button", className: "status-bar__terminal-btn", type: "button", "aria-controls": "meters-details", "aria-expanded": !metersCollapsed, title: metersCollapsed ? "Expand system meters" : "Compact system meters", onClick: onToggleMetersCollapsed, children: /* @__PURE__ */ u2("i", { className: `codicon ${metersCollapsed ? "codicon-chevron-up" : "codicon-chevron-down"}`, "aria-hidden": "true" }) }),
        /* @__PURE__ */ u2("button", { id: "meters-visibility-button", className: "status-bar__terminal-btn", type: "button", "aria-pressed": metersEnabled, title: metersEnabled ? "Hide system meters" : "Show system meters", onClick: onToggleMetersEnabled, children: /* @__PURE__ */ u2("i", { className: `codicon ${metersEnabled ? "codicon-eye" : "codicon-eye-closed"}`, "aria-hidden": "true" }) })
      ] }),
      /* @__PURE__ */ u2("button", { id: "dashboard-toggle", className: "status-bar__terminal-btn", type: "button", "aria-controls": "session-dashboard", "aria-expanded": dashboardOpen, title: "Toggle dashboard (`)", onClick: onToggleDashboard, children: [
        /* @__PURE__ */ u2("i", { className: "codicon codicon-dashboard", "aria-hidden": "true" }),
        /* @__PURE__ */ u2("span", { id: "dashboard-count", children: "0" })
      ] })
    ] })
  ] });
}

// src/components/Composer.tsx
function Composer() {
  return /* @__PURE__ */ u2(b, { children: [
    /* @__PURE__ */ u2("div", { className: "extension-slot", "data-extension-slot": "compose_above" }),
    /* @__PURE__ */ u2("form", { id: "compose-form", className: "chat__compose", children: [
      /* @__PURE__ */ u2("div", { className: "chat__compose-container", children: [
        /* @__PURE__ */ u2("div", { className: "chat__toolbar", "aria-label": "Prompt controls", children: [
          /* @__PURE__ */ u2("button", { id: "compose-attachment-button", className: "chat__toolbar-btn", type: "button", "aria-label": "Attach file", title: "Attach file", children: /* @__PURE__ */ u2("i", { className: "codicon codicon-attach", "aria-hidden": "true" }) }),
          /* @__PURE__ */ u2("input", { id: "compose-file-input", type: "file", multiple: true, hidden: true, "aria-label": "Attach files" }),
          /* @__PURE__ */ u2("label", { className: "thinking-badge-wrapper", title: "Message delivery", children: [
            /* @__PURE__ */ u2("span", { className: "sr-only", children: "Delivery" }),
            /* @__PURE__ */ u2("select", { id: "compose-delivery-mode", className: "thinking-badge", name: "delivery_mode", "aria-label": "Message delivery", children: [
              /* @__PURE__ */ u2("option", { value: "run", children: "Run" }),
              /* @__PURE__ */ u2("option", { value: "follow_up", children: "Follow-up" }),
              /* @__PURE__ */ u2("option", { value: "steer", children: "Steer" })
            ] })
          ] }),
          /* @__PURE__ */ u2("span", { id: "compose-context-readout", className: "usage-badge", children: "No session selected. Sending will create one." })
        ] }),
        /* @__PURE__ */ u2("div", { className: "sr-only", "aria-hidden": "true", children: [
          /* @__PURE__ */ u2("select", { id: "compose-provider-select", name: "provider_name", tabIndex: -1, "aria-label": "Provider adapter" }),
          /* @__PURE__ */ u2("select", { id: "compose-model-select", name: "model", tabIndex: -1, "aria-label": "Model adapter" }),
          /* @__PURE__ */ u2("select", { id: "compose-thinking-select", name: "compose_thinking_level", tabIndex: -1, "aria-label": "Thinking adapter" })
        ] }),
        /* @__PURE__ */ u2("div", { id: "compose-attachment-list", className: "chat__attachments", role: "region", "aria-live": "polite", "aria-label": "Staged attachments" }),
        /* @__PURE__ */ u2("button", { id: "compose-clear-attachments", className: "chat__attachment-clear", type: "button", "aria-label": "Clear all attachments", hidden: true, children: "Clear all" }),
        /* @__PURE__ */ u2("label", { className: "sr-only", htmlFor: "compose-input", children: "Send a prompt to Tau" }),
        /* @__PURE__ */ u2(
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
            "aria-expanded": "false",
            "aria-haspopup": "listbox",
            placeholder: "Type a message..."
          }
        ),
        /* @__PURE__ */ u2("div", { id: "compose-completion-popup", className: "command-palette compose-completion-popup", hidden: true, children: [
          /* @__PURE__ */ u2("p", { id: "compose-completion-status", className: "command-palette__step-hint", "aria-live": "polite" }),
          /* @__PURE__ */ u2("ul", { id: "compose-completion-listbox", className: "command-palette__results", role: "listbox", "aria-label": "Composer completions" })
        ] })
      ] }),
      /* @__PURE__ */ u2("button", { id: "compose-submit", className: "chat__send-btn", type: "submit", "aria-label": "Run", title: "Send (Enter)", children: /* @__PURE__ */ u2("svg", { viewBox: "0 0 24 24", width: "22", height: "22", fill: "currentColor", "aria-hidden": "true", children: /* @__PURE__ */ u2("path", { d: "M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" }) }) })
    ] }),
    /* @__PURE__ */ u2("div", { className: "sr-only", children: [
      /* @__PURE__ */ u2("p", { id: "compose-help", children: "Enter sends. Shift+Enter inserts a newline." }),
      /* @__PURE__ */ u2("p", { id: "app-status", "aria-live": "polite", children: "Loading Tau shell\u2026" })
    ] }),
    /* @__PURE__ */ u2("div", { className: "extension-slot", "data-extension-slot": "compose_below" })
  ] });
}

// src/components/Dashboard.tsx
function Dashboard({ open, onClose }) {
  return /* @__PURE__ */ u2(
    "div",
    {
      id: "session-dashboard",
      className: "modal-dialog__backdrop",
      "data-open": String(open),
      hidden: !open,
      onMouseDown: (event) => {
        if (event.target === event.currentTarget) onClose();
      },
      children: /* @__PURE__ */ u2(
        "section",
        {
          className: "modal-dialog session-dashboard__dialog",
          role: "dialog",
          "aria-modal": "true",
          "aria-labelledby": "dashboard-title",
          onMouseDown: (event) => event.stopPropagation(),
          children: [
            /* @__PURE__ */ u2("header", { className: "session-dashboard__header", children: [
              /* @__PURE__ */ u2("div", { children: [
                /* @__PURE__ */ u2("h2", { id: "dashboard-title", className: "modal-dialog__title", children: "Session dashboard" }),
                /* @__PURE__ */ u2("p", { className: "modal-dialog__description", children: "Live Tau sessions, queue state, context estimates, and current activity." })
              ] }),
              /* @__PURE__ */ u2("button", { id: "dashboard-close", className: "modal-dialog__btn", type: "button", onClick: onClose, children: "Close" })
            ] }),
            /* @__PURE__ */ u2("div", { id: "dashboard-grid", className: "session-dashboard__grid", role: "list", "aria-live": "polite", "aria-busy": "false" }),
            /* @__PURE__ */ u2("footer", { className: "session-dashboard__footer", children: [
              /* @__PURE__ */ u2("p", { id: "dashboard-age", className: "modal-dialog__description", children: "Not refreshed yet." }),
              /* @__PURE__ */ u2("div", { className: "modal-dialog__actions", role: "group", "aria-label": "Dashboard pages", children: [
                /* @__PURE__ */ u2("button", { id: "dashboard-previous", className: "modal-dialog__btn", type: "button", children: "Previous" }),
                /* @__PURE__ */ u2("output", { id: "dashboard-page", children: "Page 1 of 1" }),
                /* @__PURE__ */ u2("button", { id: "dashboard-next", className: "modal-dialog__btn", type: "button", children: "Next" }),
                /* @__PURE__ */ u2("button", { id: "dashboard-manage", className: "modal-dialog__btn modal-dialog__btn--primary", type: "button", children: "All sessions" })
              ] })
            ] })
          ]
        }
      )
    }
  );
}

// src/components/SidePanel.tsx
var TITLES = {
  sessions: "Sessions",
  workspace: "Workspace",
  search: "Search",
  plan: "Plan",
  settings: "Settings"
};
var LegacyTabAnchor = ({ name, selected, onSelect }) => /* @__PURE__ */ u2("button", { id: `tab-${name}`, type: "button", "aria-controls": `panel-${name}`, "aria-selected": selected, onClick: () => onSelect(name), children: TITLES[name] });
function SidePanel({ activeTab, onSelectTab, onClose, sessionFilter, onSelectSessionFilter }) {
  return /* @__PURE__ */ u2("aside", { id: "side-panel", className: "sidebar", "aria-label": `${TITLES[activeTab]} sidebar`, children: [
    /* @__PURE__ */ u2("header", { className: "sidebar__header", children: [
      /* @__PURE__ */ u2("span", { className: "sidebar__title", children: TITLES[activeTab].toUpperCase() }),
      /* @__PURE__ */ u2("button", { id: "close-nav-drawer", className: "sidebar__close mobile-only", type: "button", "aria-label": "Close sessions drawer", hidden: activeTab !== "sessions", onClick: onClose, children: "\u2715" }),
      /* @__PURE__ */ u2("button", { id: "close-panel-drawer", className: "sidebar__close mobile-only", type: "button", "aria-label": "Close workspace drawer", hidden: activeTab === "sessions", onClick: onClose, children: "\u2715" })
    ] }),
    /* @__PURE__ */ u2("div", { className: "sidebar__content", children: [
      /* @__PURE__ */ u2("div", { hidden: true, children: [
        /* @__PURE__ */ u2(LegacyTabAnchor, { name: "workspace", selected: activeTab === "workspace", onSelect: onSelectTab }),
        /* @__PURE__ */ u2(LegacyTabAnchor, { name: "search", selected: activeTab === "search", onSelect: onSelectTab }),
        /* @__PURE__ */ u2(LegacyTabAnchor, { name: "plan", selected: activeTab === "plan", onSelect: onSelectTab }),
        /* @__PURE__ */ u2(LegacyTabAnchor, { name: "settings", selected: activeTab === "settings", onSelect: onSelectTab })
      ] }),
      /* @__PURE__ */ u2("section", { id: "panel-sessions", className: "sessions-panel", "aria-label": "Session navigation", hidden: activeTab !== "sessions", children: [
        /* @__PURE__ */ u2("div", { className: "sessions-panel__toolbar", role: "group", "aria-label": "Session actions", children: [
          /* @__PURE__ */ u2("button", { id: "new-session-button", className: "sessions-panel__new", type: "button", children: [
            /* @__PURE__ */ u2("i", { className: "codicon codicon-add", "aria-hidden": "true" }),
            " New"
          ] }),
          /* @__PURE__ */ u2("button", { id: "archive-session-button", className: "sessions-panel__action", type: "button", children: "Archive" }),
          /* @__PURE__ */ u2("button", { id: "restore-session-button", className: "sessions-panel__action", type: "button", children: "Restore" })
        ] }),
        /* @__PURE__ */ u2("div", { className: "sessions-panel__filters", role: "group", "aria-label": "Session list filter", children: [
          /* @__PURE__ */ u2("button", { id: "show-active-sessions", type: "button", "aria-pressed": sessionFilter === "active", onClick: () => onSelectSessionFilter("active"), children: "Active" }),
          /* @__PURE__ */ u2("button", { id: "show-archived-sessions", type: "button", "aria-pressed": sessionFilter === "archived", onClick: () => onSelectSessionFilter("archived"), children: "Archived" }),
          /* @__PURE__ */ u2("span", { id: "session-count", className: "sessions-panel__count", children: "0 sessions" })
        ] }),
        /* @__PURE__ */ u2("ul", { id: "session-list", className: "sessions-panel__list", "aria-label": "Available sessions" })
      ] }),
      /* @__PURE__ */ u2("section", { id: "panel-workspace", className: "workspace", "aria-labelledby": "tab-workspace", hidden: activeTab !== "workspace", children: [
        /* @__PURE__ */ u2("div", { className: "workspace__pane-top", children: [
          /* @__PURE__ */ u2("div", { className: "workspace__section-header workspace__section-header--padded", children: [
            /* @__PURE__ */ u2("span", { children: "Files" }),
            /* @__PURE__ */ u2("div", { className: "workspace__files-toolbar", children: [
              /* @__PURE__ */ u2("button", { id: "workspace-up-button", className: "workspace__files-toolbar-icon codicon codicon-arrow-up", type: "button", title: "Parent directory", "aria-label": "Parent directory" }),
              /* @__PURE__ */ u2("button", { id: "workspace-reload-button", className: "workspace__files-toolbar-icon codicon codicon-refresh", type: "button", title: "Refresh", "aria-label": "Refresh workspace" })
            ] })
          ] }),
          /* @__PURE__ */ u2("p", { id: "workspace-path", className: "workspace__current-path", children: "." }),
          /* @__PURE__ */ u2("div", { id: "workspace-list", className: "file-tree", role: "tree", "aria-label": "Workspace tree" })
        ] }),
        /* @__PURE__ */ u2("div", { className: "workspace__drag-handle", role: "separator", "aria-orientation": "horizontal" }),
        /* @__PURE__ */ u2("div", { className: "workspace__pane-bottom", children: [
          /* @__PURE__ */ u2("div", { className: "workspace__preview-header", children: "Preview" }),
          /* @__PURE__ */ u2("section", { className: "workspace__preview-info", "aria-labelledby": "workspace-editor-title", children: [
            /* @__PURE__ */ u2("div", { id: "workspace-editor-title", className: "workspace__preview-name", children: "Selected file" }),
            /* @__PURE__ */ u2("div", { id: "workspace-editor-path", className: "workspace__preview-path", children: "No file selected" }),
            /* @__PURE__ */ u2("label", { className: "sr-only", htmlFor: "workspace-editor", children: "Workspace file editor" }),
            /* @__PURE__ */ u2("textarea", { id: "workspace-editor", className: "workspace__preview-content", spellcheck: false, "aria-describedby": "workspace-editor-note" }),
            /* @__PURE__ */ u2("p", { id: "workspace-editor-note", className: "workspace__preview-meta", children: "Local edits are not yet persisted through the web shell." }),
            /* @__PURE__ */ u2("section", { id: "workspace-annotations", className: "workspace-annotations", hidden: true, children: [
              /* @__PURE__ */ u2("h4", { children: "Annotations" }),
              /* @__PURE__ */ u2("ul", { id: "workspace-annotation-list", className: "workspace-annotation-list" })
            ] }),
            /* @__PURE__ */ u2("section", { id: "workspace-renderer", className: "workspace-renderer", "aria-label": "Extension file preview", hidden: true })
          ] })
        ] })
      ] }),
      /* @__PURE__ */ u2("section", { id: "panel-search", className: "search-panel", "aria-labelledby": "tab-search", hidden: activeTab !== "search", children: [
        /* @__PURE__ */ u2("form", { id: "search-form", children: [
          /* @__PURE__ */ u2("label", { className: "sr-only", htmlFor: "search-input", children: "Search persisted content" }),
          /* @__PURE__ */ u2("div", { className: "search-panel__input-wrapper", children: [
            /* @__PURE__ */ u2("span", { className: "search-panel__icon", "aria-hidden": "true", children: "\u2315" }),
            /* @__PURE__ */ u2("input", { id: "search-input", className: "search-panel__input", name: "query", type: "search", autoComplete: "off", spellcheck: false, placeholder: "Search messages\u2026" }),
            /* @__PURE__ */ u2("button", { id: "search-submit-button", className: "search-panel__submit", type: "submit", children: "Search" })
          ] })
        ] }),
        /* @__PURE__ */ u2("ol", { id: "search-results", className: "search-panel__results", tabIndex: 0, "aria-label": "Search results", "aria-live": "polite" })
      ] }),
      /* @__PURE__ */ u2("section", { id: "panel-plan", className: "tasks-panel", "aria-labelledby": "tab-plan", hidden: activeTab !== "plan", children: [
        /* @__PURE__ */ u2("div", { className: "tasks-panel__tabs", role: "tablist", "aria-label": "Plan views", children: /* @__PURE__ */ u2("button", { className: "tasks-panel__tab tasks-panel__tab--active", type: "button", role: "tab", "aria-selected": "true", children: "Plan" }) }),
        /* @__PURE__ */ u2("div", { className: "tasks-panel__tasks", children: /* @__PURE__ */ u2("form", { id: "plan-form", className: "tasks-panel__card", children: [
          /* @__PURE__ */ u2("div", { className: "tasks-panel__card-header", children: [
            /* @__PURE__ */ u2("span", { className: "tasks-panel__card-id", children: "Session plan" }),
            /* @__PURE__ */ u2("span", { id: "plan-revision", className: "tasks-panel__badge tasks-panel__badge--kind", children: "Revision 0" })
          ] }),
          /* @__PURE__ */ u2("label", { className: "tasks-panel__card-label", htmlFor: "plan-editor", children: "Shared checklist" }),
          /* @__PURE__ */ u2("textarea", { id: "plan-editor", className: "plan-editor tasks-panel__card-mono", spellcheck: true, placeholder: "- [ ] Add a concrete next step", "aria-describedby": "plan-status" }),
          /* @__PURE__ */ u2("p", { id: "plan-status", className: "tasks-panel__card-muted", "aria-live": "polite", children: "Select a session to edit its shared plan." }),
          /* @__PURE__ */ u2("div", { id: "plan-conflict", className: "tasks-panel__sessions-error tasks-panel__sessions-error--inline", role: "alert", hidden: true, children: "The plan changed elsewhere. Reload the server version or save again after reviewing it." }),
          /* @__PURE__ */ u2("div", { className: "tasks-panel__card-actions", children: [
            /* @__PURE__ */ u2("button", { id: "plan-save-button", type: "submit", children: "Save plan" }),
            /* @__PURE__ */ u2("button", { id: "plan-reload-button", type: "button", children: "Reload" })
          ] })
        ] }) })
      ] }),
      /* @__PURE__ */ u2("section", { id: "panel-settings", className: "settings-panel", "aria-labelledby": "tab-settings", hidden: activeTab !== "settings", children: [
        /* @__PURE__ */ u2("nav", { className: "settings-panel__nav", "aria-label": "Settings categories", children: [
          /* @__PURE__ */ u2("a", { className: "settings-panel__nav-item settings-panel__nav-item--active", href: "#tau-settings-auth", children: [
            /* @__PURE__ */ u2("i", { className: "codicon codicon-shield", "aria-hidden": "true" }),
            "Authentication"
          ] }),
          /* @__PURE__ */ u2("a", { className: "settings-panel__nav-item", href: "#tau-settings-model", children: [
            /* @__PURE__ */ u2("i", { className: "codicon codicon-symbol-parameter", "aria-hidden": "true" }),
            "Model"
          ] }),
          /* @__PURE__ */ u2("a", { className: "settings-panel__nav-item", href: "#tau-settings-runtime", children: [
            /* @__PURE__ */ u2("i", { className: "codicon codicon-server", "aria-hidden": "true" }),
            "Runtime"
          ] })
        ] }),
        /* @__PURE__ */ u2("div", { className: "settings-panel__content", children: [
          /* @__PURE__ */ u2("section", { id: "tau-settings-auth", className: "settings-panel__section", children: [
            /* @__PURE__ */ u2("h2", { className: "settings-panel__section-title", children: "Authentication" }),
            /* @__PURE__ */ u2("button", { className: "settings-panel__provider-btn settings-provider-setup", type: "button", onClick: () => document.querySelector(".provider-setup-trigger")?.click(), children: "Provider setup" }),
            /* @__PURE__ */ u2("form", { id: "auth-form", children: [
              /* @__PURE__ */ u2("div", { className: "settings-panel__field", children: [
                /* @__PURE__ */ u2("label", { className: "settings-panel__label", htmlFor: "auth-token", children: "Bearer token" }),
                /* @__PURE__ */ u2("input", { id: "auth-token", className: "settings-panel__input", type: "password", autoComplete: "off" })
              ] }),
              /* @__PURE__ */ u2("div", { className: "settings-panel__field", children: [
                /* @__PURE__ */ u2("span", { className: "settings-panel__label" }),
                /* @__PURE__ */ u2("button", { id: "save-auth-button", className: "settings-panel__provider-btn", type: "submit", children: "Save token" }),
                /* @__PURE__ */ u2("button", { id: "clear-auth-button", className: "settings-panel__provider-btn settings-panel__provider-btn--logout", type: "button", children: "Clear token" })
              ] })
            ] })
          ] }),
          /* @__PURE__ */ u2("section", { id: "tau-settings-model", className: "settings-panel__section", children: [
            /* @__PURE__ */ u2("h2", { className: "settings-panel__section-title", children: "Model" }),
            /* @__PURE__ */ u2("form", { id: "model-form", children: [
              /* @__PURE__ */ u2("div", { className: "settings-panel__field", children: [
                /* @__PURE__ */ u2("label", { className: "settings-panel__label", htmlFor: "provider-input", children: "Provider" }),
                /* @__PURE__ */ u2("input", { id: "provider-input", className: "settings-panel__input", list: "provider-options", autoComplete: "off" }),
                /* @__PURE__ */ u2("datalist", { id: "provider-options" })
              ] }),
              /* @__PURE__ */ u2("div", { className: "settings-panel__field", children: [
                /* @__PURE__ */ u2("label", { className: "settings-panel__label", htmlFor: "model-input", children: "Model" }),
                /* @__PURE__ */ u2("input", { id: "model-input", className: "settings-panel__input", list: "model-options", autoComplete: "off" }),
                /* @__PURE__ */ u2("datalist", { id: "model-options" })
              ] }),
              /* @__PURE__ */ u2("div", { className: "settings-panel__field", children: [
                /* @__PURE__ */ u2("span", { className: "settings-panel__label" }),
                /* @__PURE__ */ u2("button", { id: "apply-model-button", className: "settings-panel__provider-btn", type: "submit", children: "Apply to session" }),
                /* @__PURE__ */ u2("button", { id: "refresh-button", className: "settings-panel__provider-btn", type: "button", children: "Refresh" })
              ] })
            ] }),
            /* @__PURE__ */ u2("form", { id: "thinking-form", children: [
              /* @__PURE__ */ u2("div", { className: "settings-panel__field", children: [
                /* @__PURE__ */ u2("label", { className: "settings-panel__label", htmlFor: "thinking-level-select", children: "Thinking level" }),
                /* @__PURE__ */ u2("select", { id: "thinking-level-select", className: "settings-panel__select", name: "thinking_level" }),
                /* @__PURE__ */ u2("button", { id: "apply-thinking-button", className: "settings-panel__provider-btn", type: "submit", children: "Apply" })
              ] }),
              /* @__PURE__ */ u2("p", { id: "thinking-help", className: "settings-panel__description", children: "Updates session thinking with optimistic concurrency checks." })
            ] })
          ] }),
          /* @__PURE__ */ u2("section", { id: "tau-settings-runtime", className: "settings-panel__section", "aria-labelledby": "settings-summary-title", children: [
            /* @__PURE__ */ u2("h2", { id: "settings-summary-title", className: "settings-panel__section-title", children: "Runtime" }),
            /* @__PURE__ */ u2("dl", { id: "settings-summary", className: "settings-summary" }),
            /* @__PURE__ */ u2("p", { id: "streaming-note", className: "settings-panel__description", children: "Live streaming, queue controls, and persisted timeline playback use safe DOM updates." }),
            /* @__PURE__ */ u2("div", { className: "extension-slot", "data-extension-slot": "sidebar" })
          ] })
        ] })
      ] })
    ] })
  ] });
}

// src/components/Timeline.tsx
function Timeline() {
  return /* @__PURE__ */ u2(b, { children: [
    /* @__PURE__ */ u2("div", { className: "extension-slot", "data-extension-slot": "timeline_before" }),
    /* @__PURE__ */ u2("div", { id: "timeline-main", className: "message-list", tabIndex: -1, children: [
      /* @__PURE__ */ u2("div", { id: "timeline-meta", className: "message-list__status-banner", "aria-live": "polite", children: "Load a session to inspect persisted messages." }),
      /* @__PURE__ */ u2("ol", { id: "timeline-list", className: "timeline-list message-list__items", "aria-live": "polite", tabIndex: 0 })
    ] }),
    /* @__PURE__ */ u2("div", { className: "extension-slot", "data-extension-slot": "timeline_after" })
  ] });
}
function SessionRuntime() {
  return /* @__PURE__ */ u2("div", { className: "agent-status-panel", "aria-label": "Session runtime", children: [
    /* @__PURE__ */ u2("div", { className: "agent-status-panel__status", "aria-live": "polite", children: [
      /* @__PURE__ */ u2("span", { id: "agent-status-indicator", className: "agent-status-panel__status-dot", "aria-hidden": "true" }),
      /* @__PURE__ */ u2("span", { id: "agent-status-text", className: "agent-status-panel__status-text", children: "No session selected" })
    ] }),
    /* @__PURE__ */ u2("section", { className: "agent-status-panel__section", children: [
      /* @__PURE__ */ u2("div", { className: "agent-status-panel__title", children: "Session branch" }),
      /* @__PURE__ */ u2("div", { id: "branch-list", className: "agent-status-panel__tools" })
    ] })
  ] });
}

// node_modules/preact/hooks/dist/hooks.module.js
var t2;
var r2;
var u3;
var i3;
var o2 = 0;
var f3 = [];
var c2 = l;
var e2 = c2.__b;
var a2 = c2.__r;
var v2 = c2.diffed;
var l2 = c2.__c;
var m = c2.unmount;
var s2 = c2.__;
function d2(n2, t3) {
  c2.__h && c2.__h(r2, n2, o2 || t3), o2 = 0;
  var u4 = r2.__H || (r2.__H = { __: [], __h: [] });
  return n2 >= u4.__.length && u4.__.push({}), u4.__[n2];
}
function h2(n2) {
  return o2 = 1, p2(D, n2);
}
function p2(n2, u4, i4) {
  var o3 = d2(t2++, 2);
  if (o3.t = n2, !o3.__c && (o3.__ = [i4 ? i4(u4) : D(void 0, u4), function(n3) {
    var t3 = o3.__N ? o3.__N[0] : o3.__[0], r3 = o3.t(t3, n3);
    t3 !== r3 && (o3.__N = [r3, o3.__[1]], o3.__c.setState({}));
  }], o3.__c = r2, !r2.u)) {
    var f4 = function(n3, t3, r3) {
      if (!o3.__c.__H) return true;
      var u5 = o3.__c.__H.__.filter(function(n4) {
        return !!n4.__c;
      });
      if (u5.every(function(n4) {
        return !n4.__N;
      })) return !c3 || c3.call(this, n3, t3, r3);
      var i5 = false;
      return u5.forEach(function(n4) {
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
        var u5 = c3;
        c3 = void 0, f4(n3, t3, r3), c3 = u5;
      }
      e3 && e3.call(this, n3, t3, r3);
    }, r2.shouldComponentUpdate = f4;
  }
  return o3.__N || o3.__;
}
function y2(n2, u4) {
  var i4 = d2(t2++, 3);
  !c2.__s && C2(i4.__H, u4) && (i4.__ = n2, i4.i = u4, r2.__H.__h.push(i4));
}
function T2(n2, r3) {
  var u4 = d2(t2++, 7);
  return C2(u4.__H, r3) && (u4.__ = n2(), u4.__H = r3, u4.__h = n2), u4.__;
}
function j2() {
  for (var n2; n2 = f3.shift(); ) if (n2.__P && n2.__H) try {
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
  i4 && (u3 === r2 ? (i4.__h = [], r2.__h = [], i4.__.forEach(function(n3) {
    n3.__N && (n3.__ = n3.__N), n3.i = n3.__N = void 0;
  })) : (i4.__h.forEach(z2), i4.__h.forEach(B2), i4.__h = [], t2 = 0)), u3 = r2;
}, c2.diffed = function(n2) {
  v2 && v2(n2);
  var t3 = n2.__c;
  t3 && t3.__H && (t3.__H.__h.length && (1 !== f3.push(t3) && i3 === c2.requestAnimationFrame || ((i3 = c2.requestAnimationFrame) || w2)(j2)), t3.__H.__.forEach(function(n3) {
    n3.i && (n3.__H = n3.i), n3.i = void 0;
  })), u3 = r2 = null;
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
    clearTimeout(u4), k2 && cancelAnimationFrame(t3), setTimeout(n2);
  }, u4 = setTimeout(r3, 100);
  k2 && (t3 = requestAnimationFrame(r3));
}
function z2(n2) {
  var t3 = r2, u4 = n2.__c;
  "function" == typeof u4 && (n2.__c = void 0, u4()), r2 = t3;
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
  runs(sessionId) {
    return this.client.request(`/api/sessions/${id(sessionId)}/runs`);
  }
  submitRun(sessionId, input) {
    return this.client.request(`/api/sessions/${id(sessionId)}/runs`, { method: "POST", json: input });
  }
  runAction(runId, action) {
    return this.client.request(`/api/runs/${id(runId)}/${action}`, { method: "POST" });
  }
  queue(sessionId) {
    return this.client.request(`/api/sessions/${id(sessionId)}/queue`);
  }
  enqueue(sessionId, content, kind) {
    return this.client.request(`/api/sessions/${id(sessionId)}/queue`, { method: "POST", json: { content, kind } });
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
function Onboarding() {
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
  return /* @__PURE__ */ u2(b, { children: [
    /* @__PURE__ */ u2("button", { className: "provider-setup-trigger", type: "button", onClick: () => setOpen(true), children: "Provider setup" }),
    open && state ? /* @__PURE__ */ u2("div", { className: "modal-dialog__backdrop", role: "presentation", children: /* @__PURE__ */ u2("section", { className: "modal-dialog", role: "dialog", "aria-modal": "true", "aria-labelledby": "onboarding-title", children: [
      /* @__PURE__ */ u2("h2", { id: "onboarding-title", className: "modal-dialog__title", children: "Connect a model provider" }),
      /* @__PURE__ */ u2("p", { className: "modal-dialog__description", children: "Choose a provider and model. Credentials are stored locally and never returned by this API." }),
      /* @__PURE__ */ u2("form", { className: "modal-dialog__form", onSubmit: submit, children: [
        /* @__PURE__ */ u2("label", { className: "settings-panel__field", children: [
          /* @__PURE__ */ u2("span", { className: "settings-panel__label", children: "Provider" }),
          /* @__PURE__ */ u2("select", { className: "settings-panel__select", value: provider, onChange: (event) => chooseProvider(event.currentTarget.value), children: state.providers.map((item) => /* @__PURE__ */ u2("option", { value: item.name, children: item.name })) })
        ] }),
        /* @__PURE__ */ u2("label", { className: "settings-panel__field", children: [
          /* @__PURE__ */ u2("span", { className: "settings-panel__label", children: "Model" }),
          /* @__PURE__ */ u2("select", { className: "settings-panel__select", value: model, onChange: (event) => setModel(event.currentTarget.value), children: (selected?.models ?? []).map((item) => /* @__PURE__ */ u2("option", { value: item, children: item })) })
        ] }),
        selected?.credential_name ? /* @__PURE__ */ u2("label", { className: "settings-panel__field", children: [
          /* @__PURE__ */ u2("span", { className: "settings-panel__label", children: "API key" }),
          /* @__PURE__ */ u2("input", { className: "modal-dialog__input", type: "password", value: credential, autocomplete: "off", onInput: (event) => setCredential(event.currentTarget.value), placeholder: selected.configured ? "Stored credential (leave blank to keep)" : "Required" })
        ] }) : null,
        error ? /* @__PURE__ */ u2("p", { className: "modal-dialog__description onboarding-error", role: "alert", children: error }) : null,
        /* @__PURE__ */ u2("div", { className: "modal-dialog__actions", children: [
          /* @__PURE__ */ u2("button", { className: "modal-dialog__btn", type: "button", onClick: () => setOpen(false), children: "Cancel" }),
          /* @__PURE__ */ u2("button", { className: "modal-dialog__btn modal-dialog__btn--primary", type: "submit", disabled: saving || !provider || !model || Boolean(selected?.credential_name && !selected.configured && !credential.trim()), children: saving ? "Saving\u2026" : "Save and continue" })
        ] })
      ] })
    ] }) }) : null
  ] });
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
  const { dashboardOpen, setDashboardOpen } = useDashboardVisibility();
  const { metersEnabled, metersCollapsed, toggleMetersEnabled, toggleMetersCollapsed } = useMeterControls();
  const { sessionFilter, selectSessionFilter } = useSessionFilter();
  const sidebarOpen = drawer !== null;
  const selectPanel = (panel) => {
    const target = panel === "sessions" ? "nav" : "panel";
    if (panel === activeTab && drawer === target) close();
    else {
      selectTab(panel);
      if (drawer !== target) toggle(target);
    }
  };
  return /* @__PURE__ */ u2(b, { children: [
    /* @__PURE__ */ u2("a", { className: "skip-link", href: "#timeline-main", children: "Skip to timeline" }),
    /* @__PURE__ */ u2("div", { className: "app-layout", children: [
      /* @__PURE__ */ u2(ActivityBar, { activePanel: activeTab, onPanelChange: selectPanel, onDashboard: () => setDashboardOpen(true) }),
      /* @__PURE__ */ u2("main", { className: "app-layout__main", children: [
        /* @__PURE__ */ u2("div", { className: "app-layout__content-area", children: [
          /* @__PURE__ */ u2("div", { className: "app-layout__sidebar-wrapper", style: { width: sidebarOpen ? "300px" : "0" }, children: /* @__PURE__ */ u2(SidePanel, { activeTab, onSelectTab: selectTab, onClose: close, sessionFilter, onSelectSessionFilter: selectSessionFilter }) }),
          /* @__PURE__ */ u2("button", { id: "drawer-backdrop", className: "app-layout__sidebar-backdrop", type: "button", "aria-label": "Close sidebar", hidden: !sidebarOpen, onClick: close }),
          sidebarOpen && /* @__PURE__ */ u2("div", { className: "app-layout__resize-handle", role: "separator", "aria-orientation": "vertical", "aria-label": "Resize sidebar" }),
          /* @__PURE__ */ u2("div", { className: "app-layout__panel", children: [
            /* @__PURE__ */ u2("div", { className: "tab-bar", role: "tablist", "aria-label": "Open views", children: [
              /* @__PURE__ */ u2("button", { className: "tab-bar__tab tab-bar__tab--active", type: "button", role: "tab", "aria-selected": "true", children: "Chat" }),
              /* @__PURE__ */ u2("span", { className: "tab-bar__clock", "aria-hidden": "true" })
            ] }),
            /* @__PURE__ */ u2("div", { className: "app-layout__tab-viewport", children: /* @__PURE__ */ u2("div", { className: "app-layout__tab-content", children: /* @__PURE__ */ u2("section", { className: "chat", "aria-label": "Tau chat", children: [
              /* @__PURE__ */ u2("div", { className: "chat__messages", children: /* @__PURE__ */ u2(Timeline, {}) }),
              /* @__PURE__ */ u2(SessionRuntime, {}),
              /* @__PURE__ */ u2(Dashboard, { open: dashboardOpen, onClose: () => setDashboardOpen(false) }),
              /* @__PURE__ */ u2(Composer, {})
            ] }) }) })
          ] })
        ] }),
        /* @__PURE__ */ u2(StatusBar, { dashboardOpen, metersEnabled, metersCollapsed, onOpenSessions: () => selectPanel("sessions"), onToggleDashboard: () => setDashboardOpen((current) => !current), onToggleMetersEnabled: toggleMetersEnabled, onToggleMetersCollapsed: toggleMetersCollapsed }),
        /* @__PURE__ */ u2("div", { className: "mobile-toolbar", children: [
          /* @__PURE__ */ u2("button", { id: "mobile-nav-toggle", className: "mobile-toolbar__terminal-btn", type: "button", "aria-label": "Open sessions", "aria-expanded": drawer === "nav", onClick: () => selectPanel("sessions"), children: "Sessions" }),
          /* @__PURE__ */ u2("span", { className: "mobile-toolbar__model-slot", children: "Tau" }),
          /* @__PURE__ */ u2("button", { id: "mobile-panel-toggle", className: "mobile-toolbar__terminal-btn", type: "button", "aria-label": "Open workspace", "aria-expanded": drawer === "panel", onClick: () => selectPanel("workspace"), children: "Workspace" })
        ] })
      ] })
    ] }),
    /* @__PURE__ */ u2(Onboarding, {}),
    /* @__PURE__ */ u2("aside", { id: "session-nav", hidden: true }),
    /* @__PURE__ */ u2("noscript", { children: /* @__PURE__ */ u2("p", { className: "noscript-banner", children: "Tau Web requires JavaScript." }) })
  ] });
}
var mount = document.getElementById("app");
if (!mount) throw new Error("Missing #app root element");
B(/* @__PURE__ */ u2(TauShell, {}), mount);
