const ELEMENTS = new Set(['svg','g','defs','title','desc','path','rect','circle','ellipse','line','polyline','polygon','text','tspan','linearGradient','radialGradient','stop','clipPath','mask','pattern','marker','use']);
const ATTRIBUTES = new Set(['xmlns','viewBox','width','height','x','y','x1','y1','x2','y2','cx','cy','r','rx','ry','d','points','fill','fill-opacity','stroke','stroke-width','stroke-linecap','stroke-linejoin','stroke-dasharray','stroke-dashoffset','stroke-opacity','opacity','transform','preserveAspectRatio','role','aria-label','aria-labelledby','id','offset','stop-color','stop-opacity','gradientUnits','gradientTransform','patternUnits','patternContentUnits','patternTransform','markerWidth','markerHeight','markerUnits','orient','refX','refY','clip-path','mask','text-anchor','dominant-baseline','font-family','font-size','font-weight']);
const LOCAL_REFERENCE = /^#[A-Za-z_][\w:.-]*$/;
const MAX_BYTES = 256_000, MAX_NODES = 2_000, MAX_DEPTH = 32;

export function sanitizeModelSvg(source, runtime = globalThis) {
    if (typeof source !== 'string' || !source.trim() || new TextEncoder().encode(source).length > MAX_BYTES) return null;
    const Parser = runtime.DOMParser, Serializer = runtime.XMLSerializer;
    if (typeof Parser !== 'function' || typeof Serializer !== 'function') return null;
    const document = new Parser().parseFromString(source, 'image/svg+xml');
    const root = document.documentElement;
    if (document.querySelector('parsererror') || root?.localName !== 'svg') return null;
    const nodes = [root, ...root.querySelectorAll('*')];
    if (nodes.length > MAX_NODES) return null;
    for (const element of nodes) {
        let depth = 0;
        for (let parent = element.parentElement; parent; parent = parent.parentElement) depth++;
        if (depth > MAX_DEPTH) return null;
        if (!ELEMENTS.has(element.localName)) { element.remove(); continue; }
        for (const attribute of [...element.attributes]) {
            const name = attribute.name, value = attribute.value.trim();
            if (!ATTRIBUTES.has(name) || /^on/i.test(name) || /(?:javascript|data|https?|file):/i.test(value) || /(?:expression|@import|url\()/i.test(value) || ((name === 'href' || name === 'xlink:href') && !LOCAL_REFERENCE.test(value))) element.removeAttribute(name);
        }
    }
    root.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
    root.setAttribute('role', 'img');
    if (!root.getAttribute('aria-label')?.trim()) root.setAttribute('aria-label', root.querySelector('title')?.textContent?.trim() || 'Model-generated SVG preview');
    return new Serializer().serializeToString(root);
}

export function svgDataUrl(svg) {
    return `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`;
}
