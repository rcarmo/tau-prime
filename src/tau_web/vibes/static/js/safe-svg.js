const ELEMENTS = new Set(['svg','g','defs','title','desc','path','rect','circle','ellipse','line','polyline','polygon','text','tspan','linearGradient','radialGradient','stop','clipPath','mask','pattern','marker','use']);
const ATTRIBUTES = new Set(['xmlns','viewBox','width','height','x','y','x1','y1','x2','y2','cx','cy','r','rx','ry','d','points','fill','fill-opacity','stroke','stroke-width','stroke-linecap','stroke-linejoin','stroke-dasharray','stroke-dashoffset','stroke-opacity','opacity','transform','preserveAspectRatio','role','aria-label','aria-labelledby','id','class','offset','stop-color','stop-opacity','gradientUnits','gradientTransform','patternUnits','patternContentUnits','patternTransform','markerWidth','markerHeight','markerUnits','orient','refX','refY','clip-path','mask','text-anchor','dominant-baseline','font-family','font-size','font-weight']);
const LOCAL_REFERENCE = /^#[A-Za-z_][\w:.-]*$/;

export function sanitizeModelSvg(source, runtime = globalThis) {
    if (typeof source !== 'string' || !source.trim() || source.length > 256_000) return null;
    const Parser = runtime.DOMParser;
    const Serializer = runtime.XMLSerializer;
    if (typeof Parser !== 'function' || typeof Serializer !== 'function') return null;
    const document = new Parser().parseFromString(source, 'image/svg+xml');
    if (document.querySelector('parsererror') || document.documentElement?.localName !== 'svg') return null;
    for (const element of [...document.querySelectorAll('*')]) {
        if (!ELEMENTS.has(element.localName)) { element.remove(); continue; }
        for (const attribute of [...element.attributes]) {
            const name = attribute.name;
            const value = attribute.value.trim();
            if (!ATTRIBUTES.has(name) || /^on/i.test(name) || /(?:javascript|data|https?|file):/i.test(value)) {
                element.removeAttribute(name); continue;
            }
            if ((name === 'href' || name === 'xlink:href') && !LOCAL_REFERENCE.test(value)) element.removeAttribute(name);
            if (/url\(/i.test(value) && !/^url\(#[A-Za-z_][\w:.-]*\)$/.test(value)) element.removeAttribute(name);
        }
    }
    const root = document.documentElement;
    root.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
    if (!root.hasAttribute('role')) root.setAttribute('role', 'img');
    return new Serializer().serializeToString(root);
}

export function svgDataUrl(svg) {
    return `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`;
}
