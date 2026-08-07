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
  var a3, p3, y2, d3, w3, _2 = t3 && t3.__k || v, g2 = l3.length;
  for (u4.__d = e3, $(u4, l3, _2), e3 = u4.__d, a3 = 0; a3 < g2; a3++) null != (y2 = u4.__k[a3]) && (p3 = -1 === y2.__i ? h : _2[y2.__i] || h, y2.__i = a3, O(n2, y2, p3, i4, o3, r3, f4, e3, c3, s3), d3 = y2.__e, y2.ref && p3.ref != y2.ref && (p3.ref && N(p3.ref, null, y2), s3.push(y2.ref, y2.__c || d3, y2)), null == w3 && null != d3 && (w3 = d3), 65536 & y2.__u || p3.__k === y2.__k ? e3 = I(y2, e3, n2) : "function" == typeof y2.type && void 0 !== y2.__d ? e3 = y2.__d : d3 && (e3 = d3.nextSibling), y2.__d = void 0, y2.__u &= -196609);
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
  var a3, h3, v3, p3, w3, _2, g2, m2, x2, C2, S2, M2, $2, I2, H, L2, T2 = u4.type;
  if (void 0 !== u4.constructor) return null;
  128 & t3.__u && (c3 = !!(32 & t3.__u), r3 = [e3 = u4.__e = t3.__e]), (a3 = l.__b) && a3(u4);
  n: if ("function" == typeof T2) try {
    if (m2 = u4.props, x2 = "prototype" in T2 && T2.prototype.render, C2 = (a3 = T2.contextType) && i4[a3.__c], S2 = a3 ? C2 ? C2.props.value : a3.__ : i4, t3.__c ? g2 = (h3 = u4.__c = t3.__c).__ = h3.__E : (x2 ? u4.__c = h3 = new T2(m2, S2) : (u4.__c = h3 = new k(m2, S2), h3.constructor = T2, h3.render = q), C2 && C2.sub(h3), h3.props = m2, h3.state || (h3.state = {}), h3.context = S2, h3.__n = i4, v3 = h3.__d = true, h3.__h = [], h3._sb = []), x2 && null == h3.__s && (h3.__s = h3.state), x2 && null != T2.getDerivedStateFromProps && (h3.__s == h3.state && (h3.__s = d({}, h3.__s)), d(h3.__s, T2.getDerivedStateFromProps(m2, h3.__s))), p3 = h3.props, w3 = h3.state, h3.__v = u4, v3) x2 && null == T2.getDerivedStateFromProps && null != h3.componentWillMount && h3.componentWillMount(), x2 && null != h3.componentDidMount && h3.__h.push(h3.componentDidMount);
    else {
      if (x2 && null == T2.getDerivedStateFromProps && m2 !== p3 && null != h3.componentWillReceiveProps && h3.componentWillReceiveProps(m2, S2), !h3.__e && (null != h3.shouldComponentUpdate && false === h3.shouldComponentUpdate(m2, h3.__s, S2) || u4.__v === t3.__v)) {
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
  var a3, v3, p3, d3, _2, g2, m2, b2 = i4.props, k3 = t3.props, C2 = t3.type;
  if ("svg" === C2 ? r3 = "http://www.w3.org/2000/svg" : "math" === C2 ? r3 = "http://www.w3.org/1998/Math/MathML" : r3 || (r3 = "http://www.w3.org/1999/xhtml"), null != f4) {
    for (a3 = 0; a3 < f4.length; a3++) if ((_2 = f4[a3]) && "setAttribute" in _2 == !!C2 && (C2 ? _2.localName === C2 : 3 === _2.nodeType)) {
      u4 = _2, f4[a3] = null;
      break;
    }
  }
  if (null == u4) {
    if (null === C2) return document.createTextNode(k3);
    u4 = document.createElementNS(r3, C2, k3.is && k3), c3 && (l.__m && l.__m(t3, f4), c3 = false), f4 = null;
  }
  if (null === C2) b2 === k3 || c3 && u4.data === k3 || (u4.data = k3);
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
    else if (p3 && (u4.innerHTML = ""), P(u4, y(d3) ? d3 : [d3], t3, i4, o3, "foreignObject" === C2 ? "http://www.w3.org/1999/xhtml" : r3, f4, e3, f4 ? f4[0] : i4.__k && x(i4, 0), c3, s3), null != f4) for (a3 = f4.length; a3--; ) w(f4[a3]);
    c3 || (a3 = "value", "progress" === C2 && null == g2 ? u4.removeAttribute("value") : void 0 !== g2 && (g2 !== u4[a3] || "progress" === C2 && !g2 || "option" === C2 && g2 !== b2[a3]) && A(u4, a3, g2, b2[a3], r3), a3 = "checked", void 0 !== m2 && m2 !== u4[a3] && A(u4, a3, m2, b2[a3], r3));
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

// src/app-shell.html
var app_shell_default = '      <div class="shell-layout">\n        <aside id="session-nav" class="panel panel-nav" aria-label="Session navigation">\n          <div class="panel-header sticky-header">\n            <div>\n              <h2>Sessions</h2>\n              <p class="muted">Persisted chats, archive, and restore.</p>\n            </div>\n            <button\n              id="close-nav-drawer"\n              class="icon-button mobile-only"\n              type="button"\n              aria-label="Close sessions drawer"\n            >\n              Close\n            </button>\n          </div>\n\n          <div class="button-row button-row-wrap" role="group" aria-label="Session actions">\n            <button id="new-session-button" type="button">New</button>\n            <button id="archive-session-button" type="button">Archive</button>\n            <button id="restore-session-button" type="button">Restore</button>\n          </div>\n\n          <div class="button-row" role="group" aria-label="Session list filter">\n            <button id="show-active-sessions" type="button" aria-pressed="true">Active</button>\n            <button id="show-archived-sessions" type="button" aria-pressed="false">\n              Archived\n            </button>\n          </div>\n\n          <p id="session-count" class="muted small-text">0 sessions</p>\n          <ul id="session-list" class="session-list" aria-label="Available sessions"></ul>\n        </aside>\n\n        <main id="timeline-main" class="panel panel-main" tabindex="-1">\n          <div class="panel-header sticky-header">\n            <div>\n              <h2>Timeline</h2>\n              <p id="timeline-meta" class="muted">Load a session to inspect persisted messages.</p>\n            </div>\n          </div>\n\n          <section class="branch-strip" aria-labelledby="branch-strip-title">\n            <div class="branch-strip-header">\n              <h3 id="branch-strip-title">Branches</h3>\n              <p class="muted small-text">Select the active leaf for restored playback.</p>\n            </div>\n            <div id="branch-list" class="branch-list"></div>\n          </section>\n\n          <section id="session-overview" class="session-overview" aria-label="Live session overview">\n            <div class="extension-slot" data-extension-slot="dashboard"></div>\n            <article class="overview-card" aria-labelledby="context-summary-title">\n              <div class="overview-card-header">\n                <div>\n                  <h3 id="context-summary-title">Context</h3>\n                  <p class="muted small-text">Session entry, message, and compaction summary.</p>\n                </div>\n              </div>\n              <dl id="context-summary" class="stats-list"></dl>\n            </article>\n\n            <article class="overview-card" aria-labelledby="usage-summary-title">\n              <div class="overview-card-header">\n                <div>\n                  <h3 id="usage-summary-title">Usage</h3>\n                  <p class="muted small-text">Durable token and cost records for this session.</p>\n                </div>\n              </div>\n              <dl id="usage-totals" class="stats-list"></dl>\n              <ol id="usage-records" class="compact-list" aria-live="polite"></ol>\n            </article>\n\n            <article class="overview-card" aria-labelledby="active-run-title">\n              <div class="overview-card-header">\n                <div>\n                  <h3 id="active-run-title">Active run</h3>\n                  <p id="active-run-note" class="muted small-text">\n                    Pending and running work for the selected session.\n                  </p>\n                </div>\n              </div>\n              <div id="active-run-card" aria-live="polite"></div>\n            </article>\n\n            <article class="overview-card" aria-labelledby="queue-panel-title">\n              <div class="overview-card-header">\n                <div>\n                  <h3 id="queue-panel-title">Queue</h3>\n                  <p class="muted small-text">Follow-up and steer messages waiting for dispatch.</p>\n                </div>\n              </div>\n              <form id="queue-form" class="stack-form">\n                <label for="queue-input">Queue follow-up</label>\n                <textarea\n                  id="queue-input"\n                  name="content"\n                  rows="3"\n                  placeholder="Add a follow-up message for this session."\n                ></textarea>\n                <div class="button-row button-row-wrap" role="group" aria-label="Queue actions">\n                  <button id="queue-submit-button" type="submit">Enqueue follow-up</button>\n                  <button id="dispatch-follow-up-button" type="button">Dispatch follow-up</button>\n                  <button id="dispatch-steer-button" type="button">Dispatch steer</button>\n                </div>\n                <p id="queue-help" class="muted small-text">\n                  Enter submits. Shift+Enter inserts a newline.\n                </p>\n              </form>\n              <ul id="queue-list" class="queue-list" aria-live="polite"></ul>\n            </article>\n          </section>\n\n          <div class="extension-slot" data-extension-slot="timeline_before"></div>\n          <ol id="timeline-list" class="timeline-list" aria-live="polite" tabindex="0"></ol>\n          <div class="extension-slot" data-extension-slot="timeline_after"></div>\n        </main>\n\n        <aside id="side-panel" class="panel panel-side" aria-label="Workspace search and settings">\n          <div class="panel-header sticky-header">\n            <div>\n              <h2>Workspace</h2>\n              <p class="muted">Files, search, and Tau settings.</p>\n            </div>\n            <button\n              id="close-panel-drawer"\n              class="icon-button mobile-only"\n              type="button"\n              aria-label="Close workspace drawer"\n            >\n              Close\n            </button>\n          </div>\n\n          <div class="tabs" role="tablist" aria-label="Sidebar sections">\n            <button\n              id="tab-workspace"\n              class="tab-button"\n              type="button"\n              role="tab"\n              aria-controls="panel-workspace"\n              aria-selected="true"\n            >\n              Workspace\n            </button>\n            <button\n              id="tab-search"\n              class="tab-button"\n              type="button"\n              role="tab"\n              aria-controls="panel-search"\n              aria-selected="false"\n            >\n              Search\n            </button>\n            <button\n              id="tab-plan"\n              class="tab-button"\n              type="button"\n              role="tab"\n              aria-controls="panel-plan"\n              aria-selected="false"\n            >\n              Plan\n            </button>\n            <button\n              id="tab-settings"\n              class="tab-button"\n              type="button"\n              role="tab"\n              aria-controls="panel-settings"\n              aria-selected="false"\n            >\n              Settings\n            </button>\n          </div>\n\n          <section\n            id="panel-workspace"\n            class="tab-panel"\n            role="tabpanel"\n            aria-labelledby="tab-workspace"\n          >\n            <div class="toolbar-row">\n              <button id="workspace-up-button" type="button">Up</button>\n              <button id="workspace-reload-button" type="button">Reload</button>\n            </div>\n            <p id="workspace-path" class="muted small-text">.</p>\n            <div class="workspace-split">\n              <nav class="workspace-browser" aria-label="Workspace tree">\n                <ul id="workspace-list" class="workspace-list"></ul>\n              </nav>\n              <section class="workspace-editor-panel" aria-labelledby="workspace-editor-title">\n                <div class="workspace-editor-header">\n                  <h3 id="workspace-editor-title">Editor</h3>\n                  <p id="workspace-editor-path" class="muted small-text">No file selected</p>\n                </div>\n                <label class="sr-only" for="workspace-editor">Workspace file editor</label>\n                <textarea\n                  id="workspace-editor"\n                  spellcheck="false"\n                  aria-describedby="workspace-editor-note"\n                ></textarea>\n                <p id="workspace-editor-note" class="muted small-text">\n                  Local edits are not yet persisted through the web shell.\n                </p>\n                <section id="workspace-annotations" class="workspace-annotations" hidden>\n                  <h4>Annotations</h4>\n                  <ul id="workspace-annotation-list" class="workspace-annotation-list"></ul>\n                </section>\n                <section\n                  id="workspace-renderer"\n                  class="workspace-renderer"\n                  aria-label="Extension file preview"\n                  hidden\n                ></section>\n              </section>\n            </div>\n          </section>\n\n          <section\n            id="panel-search"\n            class="tab-panel"\n            role="tabpanel"\n            aria-labelledby="tab-search"\n            hidden\n          >\n            <form id="search-form" class="stack-form">\n              <label for="search-input">Search persisted content</label>\n              <div class="toolbar-row">\n                <input\n                  id="search-input"\n                  name="query"\n                  type="search"\n                  autocomplete="off"\n                  placeholder="Search messages and indexed content"\n                />\n                <button id="search-submit-button" type="submit">Search</button>\n              </div>\n              <p class="muted small-text">Shortcut: Ctrl/Cmd+K</p>\n            </form>\n            <ol\n              id="search-results"\n              class="search-results"\n              tabindex="0"\n              aria-label="Search results"\n              aria-live="polite"\n            ></ol>\n          </section>\n\n          <section\n            id="panel-plan"\n            class="tab-panel plan-panel"\n            role="tabpanel"\n            aria-labelledby="tab-plan"\n            hidden\n          >\n            <form id="plan-form" class="stack-form">\n              <div class="plan-editor-header">\n                <label for="plan-editor">Session plan</label>\n                <span id="plan-revision" class="muted small-text">Revision 0</span>\n              </div>\n              <textarea\n                id="plan-editor"\n                class="plan-editor"\n                spellcheck="true"\n                placeholder="- [ ] Add a concrete next step"\n                aria-describedby="plan-status"\n              ></textarea>\n              <p id="plan-status" class="muted small-text" aria-live="polite">\n                Select a session to edit its shared plan.\n              </p>\n              <div id="plan-conflict" class="plan-conflict" role="alert" hidden>\n                The plan changed elsewhere while you had local edits. Reload the server version or\n                save again after reviewing it.\n              </div>\n              <div class="button-row button-row-wrap">\n                <button id="plan-save-button" type="submit">Save plan</button>\n                <button id="plan-reload-button" type="button">Reload server plan</button>\n              </div>\n            </form>\n          </section>\n\n          <section\n            id="panel-settings"\n            class="tab-panel"\n            role="tabpanel"\n            aria-labelledby="tab-settings"\n            hidden\n          >\n            <form id="auth-form" class="stack-form">\n              <label for="auth-token">Bearer token</label>\n              <input id="auth-token" type="password" autocomplete="off" />\n              <div class="button-row button-row-wrap">\n                <button id="save-auth-button" type="submit">Save token</button>\n                <button id="clear-auth-button" type="button">Clear token</button>\n              </div>\n            </form>\n\n            <form id="model-form" class="stack-form">\n              <label for="provider-input">Provider</label>\n              <input id="provider-input" list="provider-options" autocomplete="off" />\n              <datalist id="provider-options"></datalist>\n\n              <label for="model-input">Model</label>\n              <input id="model-input" list="model-options" autocomplete="off" />\n              <datalist id="model-options"></datalist>\n\n              <div class="button-row button-row-wrap">\n                <button id="apply-model-button" type="submit">Apply to session</button>\n                <button id="refresh-button" type="button">Refresh shell</button>\n              </div>\n            </form>\n\n            <form id="thinking-form" class="stack-form">\n              <label for="thinking-level-select">Thinking level</label>\n              <div class="toolbar-row toolbar-row-wrap">\n                <select id="thinking-level-select" name="thinking_level"></select>\n                <button id="apply-thinking-button" type="submit">Apply thinking</button>\n              </div>\n              <p id="thinking-help" class="muted small-text">\n                Updates session thinking with optimistic concurrency checks.\n              </p>\n            </form>\n\n            <section aria-labelledby="settings-summary-title">\n              <h3 id="settings-summary-title">Runtime summary</h3>\n              <dl id="settings-summary" class="settings-summary"></dl>\n            </section>\n\n            <p id="streaming-note" class="muted small-text">\n              Live streaming, queue controls, and persisted timeline playback are rendered with safe\n              DOM updates only.\n            </p>\n            <div class="extension-slot" data-extension-slot="sidebar"></div>\n          </section>\n        </aside>\n      </div>\n';

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
function D(n2, t3) {
  return "function" == typeof t3 ? t3(n2) : t3;
}

// node_modules/preact/jsx-runtime/dist/jsxRuntime.module.js
var f3 = 0;
var i3 = Array.isArray;
function u3(e3, t3, n2, o3, i4, u4) {
  t3 || (t3 = {});
  var a3, c3, l3 = t3;
  "ref" in t3 && (a3 = t3.ref, delete t3.ref);
  var p3 = { type: e3, props: l3, key: n2, ref: a3, __k: null, __: null, __b: 0, __e: null, __d: void 0, __c: null, constructor: void 0, __v: --f3, __i: -1, __u: 0, __source: i4, __self: u4 };
  if ("function" == typeof e3 && (a3 = e3.defaultProps)) for (c3 in a3) void 0 === l3[c3] && (l3[c3] = a3[c3]);
  return l.vnode && l.vnode(p3), p3;
}

// src/components/ActivityBar.tsx
var PANELS = [
  { id: "workspace", label: "Workspace", target: "tab-workspace", glyph: "\u25B1" },
  { id: "search", label: "Search", target: "tab-search", glyph: "\u2315" },
  { id: "plan", label: "Plan", target: "tab-plan", glyph: "\u2637" },
  { id: "dashboard", label: "Dashboard", target: "dashboard-toggle", glyph: "\u2301" },
  { id: "settings", label: "Settings", target: "tab-settings", glyph: "\u2699", bottom: true }
];
function ActivityBar() {
  const [activePanel, setActivePanel] = h2("workspace");
  const activate = (panel) => {
    document.getElementById(panel.target)?.click();
    setActivePanel(panel.id);
  };
  return /* @__PURE__ */ u3("nav", { className: "activity-bar", "aria-label": "Activity bar", children: PANELS.map((panel) => /* @__PURE__ */ u3(
    "button",
    {
      type: "button",
      className: `activity-bar__button ${activePanel === panel.id ? "is-active" : ""} ${panel.bottom ? "is-bottom" : ""}`,
      title: panel.label,
      "aria-label": panel.label,
      "aria-pressed": activePanel === panel.id,
      onClick: () => activate(panel),
      children: /* @__PURE__ */ u3("span", { className: "activity-bar__icon", "aria-hidden": "true", children: panel.glyph })
    },
    panel.id
  )) });
}

// src/components/StatusBar.tsx
var Meter = ({ id, label }) => /* @__PURE__ */ u3("figure", { className: "meter-tile", children: [
  /* @__PURE__ */ u3("figcaption", { children: [
    label,
    " ",
    /* @__PURE__ */ u3("output", { id: `meter-${id}-value`, children: "--" })
  ] }),
  /* @__PURE__ */ u3("svg", { id: `meter-${id}-sparkline`, role: "img", "aria-label": `${label === "RSS" ? "Tau RSS" : label} history` })
] });
function StatusBar() {
  return /* @__PURE__ */ u3("header", { className: "topbar", "aria-label": "Tau status bar", children: [
    /* @__PURE__ */ u3("div", { className: "topbar-group topbar-branding", children: [
      /* @__PURE__ */ u3("button", { id: "mobile-nav-toggle", className: "icon-button mobile-only", type: "button", "aria-controls": "session-nav", "aria-expanded": "false", "aria-label": "Open sessions drawer", children: "Sessions" }),
      /* @__PURE__ */ u3("div", { className: "brand-block", children: [
        /* @__PURE__ */ u3("h1", { children: "Tau" }),
        /* @__PURE__ */ u3("p", { id: "status-stream", className: "muted", children: "Connecting\u2026" })
      ] })
    ] }),
    /* @__PURE__ */ u3("dl", { className: "status-grid", "aria-label": "Current Tau status", children: [
      /* @__PURE__ */ u3("div", { children: [
        /* @__PURE__ */ u3("dt", { children: "Session" }),
        /* @__PURE__ */ u3("dd", { id: "status-session", children: "No session selected" })
      ] }),
      /* @__PURE__ */ u3("div", { children: [
        /* @__PURE__ */ u3("dt", { children: "Model" }),
        /* @__PURE__ */ u3("dd", { id: "status-model", children: "Unset" })
      ] }),
      /* @__PURE__ */ u3("div", { children: [
        /* @__PURE__ */ u3("dt", { children: "Context" }),
        /* @__PURE__ */ u3("dd", { id: "status-context", children: "No context loaded" })
      ] })
    ] }),
    /* @__PURE__ */ u3("div", { className: "topbar-group topbar-dashboard-control", children: /* @__PURE__ */ u3("button", { id: "dashboard-toggle", className: "dashboard-toggle", type: "button", "aria-controls": "session-dashboard", "aria-expanded": "false", title: "Toggle dashboard (`)", children: [
      "Dashboard ",
      /* @__PURE__ */ u3("span", { id: "dashboard-count", className: "dashboard-count", children: "0" })
    ] }) }),
    /* @__PURE__ */ u3("div", { className: "topbar-group topbar-actions", children: [
      /* @__PURE__ */ u3("section", { id: "system-meters", className: "system-meters", "aria-label": "System meters", "data-enabled": "true", "data-collapsed": "true", children: [
        /* @__PURE__ */ u3("div", { className: "meters-toolbar", children: [
          /* @__PURE__ */ u3("output", { id: "meters-summary", className: "meters-summary", "aria-live": "polite", children: "Meters loading\u2026" }),
          /* @__PURE__ */ u3("button", { id: "meters-collapse-button", className: "meter-control", type: "button", "aria-controls": "meters-details", "aria-expanded": "false", children: "Expand" }),
          /* @__PURE__ */ u3("button", { id: "meters-visibility-button", className: "meter-control", type: "button", "aria-pressed": "true", children: "Hide" })
        ] }),
        /* @__PURE__ */ u3("div", { id: "meters-details", className: "meters-details", children: [
          /* @__PURE__ */ u3(Meter, { id: "cpu", label: "CPU" }),
          /* @__PURE__ */ u3(Meter, { id: "ram", label: "RAM" }),
          /* @__PURE__ */ u3(Meter, { id: "rss", label: "RSS" }),
          /* @__PURE__ */ u3(Meter, { id: "swap", label: "Swap" })
        ] })
      ] }),
      /* @__PURE__ */ u3("button", { id: "mobile-panel-toggle", className: "icon-button mobile-only", type: "button", "aria-controls": "side-panel", "aria-expanded": "false", "aria-label": "Open workspace and settings drawer", children: "Panels" })
    ] })
  ] });
}

// src/components/Composer.tsx
var SelectControl = ({ id, name, label, children }) => /* @__PURE__ */ u3("div", { className: "compose-control", children: [
  /* @__PURE__ */ u3("label", { htmlFor: id, children: label }),
  /* @__PURE__ */ u3("select", { id, name, children })
] });
function Composer() {
  return /* @__PURE__ */ u3("footer", { className: "composer-shell", children: [
    /* @__PURE__ */ u3("div", { className: "extension-slot", "data-extension-slot": "compose_above" }),
    /* @__PURE__ */ u3("form", { id: "compose-form", className: "compose-form", children: [
      /* @__PURE__ */ u3("section", { className: "compose-toolbar", "aria-label": "Prompt controls", children: [
        /* @__PURE__ */ u3("div", { className: "compose-select-grid", children: [
          /* @__PURE__ */ u3(SelectControl, { id: "compose-provider-select", name: "provider_name", label: "Provider" }),
          /* @__PURE__ */ u3(SelectControl, { id: "compose-model-select", name: "model", label: "Model" }),
          /* @__PURE__ */ u3(SelectControl, { id: "compose-thinking-select", name: "compose_thinking_level", label: "Thinking" }),
          /* @__PURE__ */ u3(SelectControl, { id: "compose-delivery-mode", name: "delivery_mode", label: "Delivery", children: [
            /* @__PURE__ */ u3("option", { value: "run", children: "Run immediately" }),
            /* @__PURE__ */ u3("option", { value: "follow_up", children: "Queue follow-up" }),
            /* @__PURE__ */ u3("option", { value: "steer", children: "Queue steer" })
          ] })
        ] }),
        /* @__PURE__ */ u3("p", { id: "compose-context-readout", className: "muted small-text", children: "No session selected. Sending will create one." }),
        /* @__PURE__ */ u3("div", { className: "compose-attachment-bar", children: [
          /* @__PURE__ */ u3("button", { id: "compose-attachment-button", type: "button", children: "Attach files" }),
          /* @__PURE__ */ u3("button", { id: "compose-clear-attachments", type: "button", children: "Clear staged" }),
          /* @__PURE__ */ u3("input", { id: "compose-file-input", className: "sr-only", type: "file", multiple: true, "aria-label": "Attach files" })
        ] }),
        /* @__PURE__ */ u3("ul", { id: "compose-attachment-list", className: "compose-attachment-list", "aria-live": "polite", "aria-label": "Staged attachments" })
      ] }),
      /* @__PURE__ */ u3("label", { htmlFor: "compose-input", children: "Send a prompt to Tau" }),
      /* @__PURE__ */ u3("div", { className: "compose-editor-group", children: [
        /* @__PURE__ */ u3("div", { className: "compose-row", children: [
          /* @__PURE__ */ u3("textarea", { id: "compose-input", name: "prompt", rows: 3, autoComplete: "off", role: "combobox", "aria-autocomplete": "list", "aria-controls": "compose-completion-listbox", "aria-describedby": "compose-help compose-completion-status", "aria-expanded": "false", "aria-haspopup": "listbox", placeholder: "Select or create a session, then send a prompt." }),
          /* @__PURE__ */ u3("button", { id: "compose-submit", type: "submit", children: "Run" })
        ] }),
        /* @__PURE__ */ u3("div", { id: "compose-completion-popup", className: "compose-completion-popup", hidden: true, children: [
          /* @__PURE__ */ u3("p", { id: "compose-completion-status", className: "muted small-text", "aria-live": "polite" }),
          /* @__PURE__ */ u3("ul", { id: "compose-completion-listbox", className: "compose-completion-listbox", role: "listbox", "aria-label": "Composer completions" })
        ] })
      ] }),
      /* @__PURE__ */ u3("div", { className: "compose-status-row", children: [
        /* @__PURE__ */ u3("p", { id: "compose-help", className: "muted small-text", children: "Enter sends. Shift+Enter inserts a newline." }),
        /* @__PURE__ */ u3("p", { id: "app-status", className: "small-text", "aria-live": "polite", children: "Loading Tau shell\u2026" })
      ] })
    ] }),
    /* @__PURE__ */ u3("div", { className: "extension-slot", "data-extension-slot": "compose_below" })
  ] });
}

// src/components/Dashboard.tsx
function Dashboard() {
  return /* @__PURE__ */ u3("section", { id: "session-dashboard", className: "session-dashboard", "aria-labelledby": "dashboard-title", "data-open": "false", hidden: true, children: /* @__PURE__ */ u3("div", { className: "dashboard-shell", children: [
    /* @__PURE__ */ u3("header", { className: "dashboard-header", children: [
      /* @__PURE__ */ u3("div", { children: [
        /* @__PURE__ */ u3("h2", { id: "dashboard-title", children: "Session dashboard" }),
        /* @__PURE__ */ u3("p", { className: "muted small-text", children: "Live Tau sessions, queue state, context estimates, and current activity." })
      ] }),
      /* @__PURE__ */ u3("button", { id: "dashboard-close", className: "icon-button", type: "button", children: "Close" })
    ] }),
    /* @__PURE__ */ u3("div", { id: "dashboard-grid", className: "dashboard-grid", role: "list", "aria-live": "polite", "aria-busy": "false" }),
    /* @__PURE__ */ u3("footer", { className: "dashboard-footer", children: [
      /* @__PURE__ */ u3("p", { id: "dashboard-age", className: "muted small-text", children: "Not refreshed yet." }),
      /* @__PURE__ */ u3("div", { className: "dashboard-pagination", role: "group", "aria-label": "Dashboard pages", children: [
        /* @__PURE__ */ u3("button", { id: "dashboard-previous", type: "button", children: "Previous" }),
        /* @__PURE__ */ u3("output", { id: "dashboard-page", children: "Page 1 of 1" }),
        /* @__PURE__ */ u3("button", { id: "dashboard-next", type: "button", children: "Next" }),
        /* @__PURE__ */ u3("button", { id: "dashboard-manage", type: "button", children: "All sessions" })
      ] })
    ] })
  ] }) });
}

// src/index.tsx
function TauShell() {
  return /* @__PURE__ */ u3(b, { children: [
    /* @__PURE__ */ u3("a", { className: "skip-link", href: "#timeline-main", children: "Skip to timeline" }),
    /* @__PURE__ */ u3("div", { className: "app-layout", children: [
      /* @__PURE__ */ u3(ActivityBar, {}),
      /* @__PURE__ */ u3("div", { className: "app-layout__main", children: /* @__PURE__ */ u3("div", { className: "app-layout__content-area", children: /* @__PURE__ */ u3("div", { className: "app-layout__panel", children: /* @__PURE__ */ u3("div", { className: "app-shell", children: [
        /* @__PURE__ */ u3(StatusBar, {}),
        /* @__PURE__ */ u3(Dashboard, {}),
        /* @__PURE__ */ u3("div", { className: "legacy-shell-regions", dangerouslySetInnerHTML: { __html: app_shell_default } }),
        /* @__PURE__ */ u3(Composer, {})
      ] }) }) }) })
    ] }),
    /* @__PURE__ */ u3(
      "button",
      {
        id: "drawer-backdrop",
        className: "drawer-backdrop",
        type: "button",
        hidden: true,
        "aria-label": "Close open drawers"
      }
    ),
    /* @__PURE__ */ u3("noscript", { children: /* @__PURE__ */ u3("p", { className: "noscript-banner", children: "Tau Web Shell requires JavaScript to load persisted sessions." }) })
  ] });
}
var mount = document.getElementById("app");
if (!mount) throw new Error("Missing #app root element");
B(/* @__PURE__ */ u3(TauShell, {}), mount);
