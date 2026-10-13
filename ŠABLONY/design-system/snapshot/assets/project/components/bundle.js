/* @ds-bundle: {"format":4,"namespace":"RedButtonDesignSystem_3b681f","components":[{"name":"ICON_NAMES","sourcePath":"components/brand/Icon.jsx"},{"name":"Icon","sourcePath":"components/brand/Icon.jsx"},{"name":"Logo","sourcePath":"components/brand/Logo.jsx"},{"name":"MarkerNote","sourcePath":"components/brand/MarkerNote.jsx"},{"name":"NetPattern","sourcePath":"components/brand/NetPattern.jsx"},{"name":"Badge","sourcePath":"components/display/Badge.jsx"},{"name":"Card","sourcePath":"components/display/Card.jsx"},{"name":"Tabs","sourcePath":"components/display/Tabs.jsx"},{"name":"Tag","sourcePath":"components/display/Tag.jsx"},{"name":"Dialog","sourcePath":"components/feedback/Dialog.jsx"},{"name":"Toast","sourcePath":"components/feedback/Toast.jsx"},{"name":"Tooltip","sourcePath":"components/feedback/Tooltip.jsx"},{"name":"Button","sourcePath":"components/forms/Button.jsx"},{"name":"Checkbox","sourcePath":"components/forms/Checkbox.jsx"},{"name":"IconButton","sourcePath":"components/forms/IconButton.jsx"},{"name":"Input","sourcePath":"components/forms/Input.jsx"},{"name":"Radio","sourcePath":"components/forms/Radio.jsx"},{"name":"Select","sourcePath":"components/forms/Select.jsx"},{"name":"Switch","sourcePath":"components/forms/Switch.jsx"},{"name":"PhotoPost","sourcePath":"ui_kits/social/PhotoPost.jsx"},{"name":"SocialPost","sourcePath":"ui_kits/social/SocialPost.jsx"}],"sourceHashes":{"components/brand/Icon.jsx":"ce29a85b985a","components/brand/Logo.jsx":"8b108013c6ca","components/brand/MarkerNote.jsx":"ab3b580b216e","components/brand/NetPattern.jsx":"55906fcc5c54","components/display/Badge.jsx":"7cce47f455b6","components/display/Card.jsx":"7ba48fe54726","components/display/Tabs.jsx":"e32dcce178fe","components/display/Tag.jsx":"d3148f84d615","components/feedback/Dialog.jsx":"87764975e9c8","components/feedback/Toast.jsx":"eac4f1a74428","components/feedback/Tooltip.jsx":"074ff5184ce1","components/forms/Button.jsx":"63079bd8d2dc","components/forms/Checkbox.jsx":"0bfbb0e9a052","components/forms/IconButton.jsx":"3193d29e1018","components/forms/Input.jsx":"6f702e28204a","components/forms/Radio.jsx":"036d8ed313ca","components/forms/Select.jsx":"7999c9fe2fe4","components/forms/Switch.jsx":"40c19b7fe200","ui_kits/social/PhotoPost.jsx":"34246a2b6b60","ui_kits/social/SocialPost.jsx":"dd8395c20891"},"inlinedExternals":[],"unexposedExports":[]} */

(() => {

const __ds_ns = (window.RedButtonDesignSystem_3b681f = window.RedButtonDesignSystem_3b681f || {});

const __ds_scope = {};

(__ds_ns.__errors = __ds_ns.__errors || []);

// components/brand/Icon.jsx
try { (() => {
const ICON_NAMES = {
  "oval-scribble": 1,
  "arrow-up-left": 2,
  "underline": 3,
  "oval-highlight": 4,
  "arrow-bent-down": 5,
  "arrow-squiggle": 6,
  "arrow-s-curve": 7,
  "double-underline": 8,
  "arrow-down-right": 9,
  "arrow-curve-left": 10,
  "circle-scribble": 11,
  "asterisk": 12,
  "map-pin": 13,
  "phone": 14,
  "mail": 15,
  "arrow-right": 16,
  "arrow-down": 17,
  "check": 18,
  "cross": 19,
  "shield": 20,
  "crown": 21,
  "search": 22,
  "compass": 23,
  "presentation": 24,
  "people-group": 25,
  "idea-bulb": 26,
  "growth-chart": 27,
  "puzzle": 28,
  "gear": 29,
  "arrows-scatter": 30,
  "instagram": 31,
  "facebook": 32,
  "youtube": 33,
  "linkedin": 34,
  "code": 35,
  "road": 36,
  "arrow-up-right": 37,
  "people-pair": 38,
  "checklist": 39,
  "pen": 40,
  "shapes-transform": 41,
  "ellipse": 42
};
function Icon({
  name = "idea-bulb",
  size = 32,
  white = false,
  assetsBase = "assets",
  style,
  alt
}) {
  const num = typeof name === "number" ? name : ICON_NAMES[name] || 26;
  const n = String(num).padStart(2, "0");
  return /*#__PURE__*/React.createElement("img", {
    src: assetsBase + "/icons/icon-" + n + ".svg",
    alt: alt || (typeof name === "string" ? name : "icon " + n),
    style: {
      width: size,
      height: size,
      objectFit: "contain",
      display: "inline-block",
      filter: white ? "brightness(0) invert(1)" : "none",
      ...style
    }
  });
}
Object.assign(__ds_scope, { ICON_NAMES, Icon });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/brand/Icon.jsx", error: String((e && e.message) || e) }); }

// components/brand/Logo.jsx
try { (() => {
const FILES = {
  "horizontal-light": "logo-light-logo.svg",
  "horizontal-dark": "logo-dark-logo.svg",
  "vertical-light": "logo-light-alternativni.svg",
  "vertical-dark": "logo-dark-alternativni.svg",
  "symbol": "logo-universal-symbol.svg"
};
function Logo({
  variant = "horizontal-light",
  height = 32,
  assetsBase = "assets",
  style
}) {
  const file = FILES[variant] || FILES["horizontal-light"];
  return /*#__PURE__*/React.createElement("img", {
    src: assetsBase + "/logos/" + file,
    alt: "Red Button",
    style: {
      height: Math.max(height, 20),
      width: "auto",
      display: "inline-block",
      ...style
    }
  });
}
Object.assign(__ds_scope, { Logo });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/brand/Logo.jsx", error: String((e && e.message) || e) }); }

// components/brand/MarkerNote.jsx
try { (() => {
function MarkerNote({
  children,
  size = 24,
  color = "wine",
  as = "div",
  style
}) {
  const colors = {
    wine: "var(--rb-wine)",
    white: "#ffffff",
    red: "var(--rb-red-button)",
    anthracite: "var(--rb-anthracite)"
  };
  const Tag = as;
  return /*#__PURE__*/React.createElement(Tag, {
    style: {
      fontFamily: "var(--font-accent)",
      fontWeight: 400,
      fontSize: size,
      lineHeight: 1.3,
      color: colors[color] || colors.wine,
      ...style
    }
  }, children);
}
Object.assign(__ds_scope, { MarkerNote });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/brand/MarkerNote.jsx", error: String((e && e.message) || e) }); }

// components/brand/NetPattern.jsx
try { (() => {
function NetPattern({
  corner = "bottom-left",
  width = "45%",
  color = "grey",
  variant = 1,
  opacity = 0.6,
  assetsBase = "assets",
  style
}) {
  const file = variant === 2 ? "sit-1.svg" : "zakladni-sit.svg";
  const filters = {
    grey: "grayscale(1) brightness(1.6)",
    wine: "brightness(0) saturate(100%) invert(14%) sepia(76%) saturate(4048%) hue-rotate(334deg) brightness(92%)",
    red: "brightness(0) saturate(100%) invert(22%) sepia(93%) saturate(6995%) hue-rotate(342deg) brightness(101%) contrast(105%)",
    white: "brightness(0) invert(1)",
    anthracite: "grayscale(1) brightness(0.55)"
  };
  const pos = {
    "bottom-left": {
      left: "-6%",
      bottom: "-10%"
    },
    "bottom-right": {
      right: "-6%",
      bottom: "-10%",
      transform: "scaleX(-1)"
    },
    "top-left": {
      left: "-6%",
      top: "-10%",
      transform: "scaleY(-1)"
    },
    "top-right": {
      right: "-6%",
      top: "-10%",
      transform: "scale(-1)"
    }
  };
  return /*#__PURE__*/React.createElement("img", {
    src: assetsBase + "/patterns/" + file,
    alt: "",
    "aria-hidden": "true",
    style: {
      position: "absolute",
      width,
      opacity,
      pointerEvents: "none",
      filter: filters[color] || "none",
      ...(pos[corner] || pos["bottom-left"]),
      ...style
    }
  });
}
Object.assign(__ds_scope, { NetPattern });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/brand/NetPattern.jsx", error: String((e && e.message) || e) }); }

// components/display/Badge.jsx
try { (() => {
function Badge({
  children,
  tone = "wine",
  torn = true,
  size = "md",
  style
}) {
  const tones = {
    wine: {
      background: "var(--rb-wine)",
      color: "#fff"
    },
    red: {
      background: "var(--button-primary)",
      color: "#fff"
    },
    anthracite: {
      background: "var(--rb-anthracite)",
      color: "#fff"
    },
    outline: {
      background: "transparent",
      color: "var(--rb-wine)",
      boxShadow: "inset 0 0 0 2px var(--rb-wine)"
    }
  };
  const sizes = {
    sm: {
      fontSize: 12,
      padding: "4px 10px"
    },
    md: {
      fontSize: 14,
      padding: "6px 14px"
    },
    lg: {
      fontSize: 18,
      padding: "10px 20px"
    }
  };
  const tornClip = "polygon(0% 8%, 3% 0%, 97% 2%, 100% 12%, 99% 88%, 100% 96%, 96% 100%, 4% 98%, 0% 92%)";
  return /*#__PURE__*/React.createElement("span", {
    style: {
      display: "inline-block",
      fontFamily: "var(--font-sans)",
      fontWeight: 700,
      lineHeight: 1.3,
      borderRadius: torn ? 0 : 4,
      clipPath: torn ? tornClip : "none",
      ...(sizes[size] || sizes.md),
      ...(tones[tone] || tones.wine),
      ...style
    }
  }, children);
}
Object.assign(__ds_scope, { Badge });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/display/Badge.jsx", error: String((e && e.message) || e) }); }

// components/display/Card.jsx
try { (() => {
function Card({
  surface = "white",
  padding = 24,
  bordered = true,
  children,
  style
}) {
  const surfaces = {
    white: {
      background: "var(--surface-card)",
      color: "var(--text-body)",
      border: bordered ? "1px solid var(--border-subtle)" : "none"
    },
    "off-white": {
      background: "var(--surface-page)",
      color: "var(--text-body)",
      border: bordered ? "1px solid var(--border-subtle)" : "none"
    },
    wine: {
      background: "var(--surface-brand)",
      color: "#fff",
      border: "none"
    },
    anthracite: {
      background: "var(--surface-dark)",
      color: "#fff",
      border: "none"
    }
  };
  return /*#__PURE__*/React.createElement("div", {
    style: {
      borderRadius: "var(--radius-card, 6px)",
      padding,
      position: "relative",
      overflow: "hidden",
      ...(surfaces[surface] || surfaces.white),
      ...style
    }
  }, children);
}
Object.assign(__ds_scope, { Card });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/display/Card.jsx", error: String((e && e.message) || e) }); }

// components/display/Tabs.jsx
try { (() => {
function Tabs({
  tabs = [],
  active,
  defaultActive = 0,
  onChange,
  style
}) {
  const isControlled = active !== undefined;
  const [inner, setInner] = React.useState(defaultActive);
  const cur = isControlled ? active : inner;
  const [hover, setHover] = React.useState(-1);
  return /*#__PURE__*/React.createElement("div", {
    role: "tablist",
    style: {
      display: "flex",
      gap: 4,
      borderBottom: "2px solid var(--border-subtle)",
      fontFamily: "var(--font-sans)",
      ...style
    }
  }, tabs.map((t, i) => /*#__PURE__*/React.createElement("button", {
    key: i,
    role: "tab",
    "aria-selected": cur === i,
    onClick: () => {
      if (!isControlled) setInner(i);
      onChange && onChange(i);
    },
    onMouseEnter: () => setHover(i),
    onMouseLeave: () => setHover(-1),
    style: {
      background: "none",
      border: "none",
      cursor: "pointer",
      padding: "10px 16px",
      marginBottom: -2,
      fontFamily: "var(--font-sans)",
      fontSize: 16,
      fontWeight: cur === i ? 800 : 500,
      color: cur === i ? "var(--rb-wine)" : hover === i ? "var(--rb-wine)" : "var(--text-body)",
      borderBottom: "3px solid " + (cur === i ? "var(--rb-wine)" : "transparent"),
      transition: "color 150ms ease-out, border-color 150ms ease-out"
    }
  }, t)));
}
Object.assign(__ds_scope, { Tabs });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/display/Tabs.jsx", error: String((e && e.message) || e) }); }

// components/display/Tag.jsx
try { (() => {
function Tag({
  children,
  marker = true,
  color = "wine",
  style
}) {
  if (marker) {
    const colors = {
      wine: "var(--rb-wine)",
      red: "var(--rb-red-button)",
      white: "#fff"
    };
    return /*#__PURE__*/React.createElement("span", {
      style: {
        fontFamily: "var(--font-accent)",
        fontSize: 18,
        color: colors[color] || colors.wine,
        ...style
      }
    }, children);
  }
  return /*#__PURE__*/React.createElement("span", {
    style: {
      display: "inline-block",
      fontFamily: "var(--font-sans)",
      fontWeight: 700,
      fontSize: 12,
      letterSpacing: "0.08em",
      textTransform: "uppercase",
      color: "var(--rb-wine)",
      border: "1.5px solid var(--rb-wine)",
      borderRadius: 999,
      padding: "4px 12px",
      ...style
    }
  }, children);
}
Object.assign(__ds_scope, { Tag });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/display/Tag.jsx", error: String((e && e.message) || e) }); }

// components/feedback/Toast.jsx
try { (() => {
function Toast({
  message,
  tone = "success",
  visible = true,
  onClose,
  assetsBase,
  style
}) {
  if (!visible) return null;
  const tones = {
    success: {
      icon: "check",
      bg: "var(--rb-wine)"
    },
    error: {
      icon: "cross",
      bg: "var(--rb-anthracite)"
    },
    info: {
      icon: "idea-bulb",
      bg: "var(--rb-anthracite)"
    }
  };
  const t = tones[tone] || tones.success;
  return /*#__PURE__*/React.createElement("div", {
    role: "status",
    style: {
      display: "inline-flex",
      alignItems: "center",
      gap: 12,
      background: t.bg,
      color: "#fff",
      borderRadius: "var(--radius-card, 6px)",
      boxShadow: "var(--shadow-float)",
      padding: "12px 16px",
      fontFamily: "var(--font-sans)",
      fontSize: 15,
      fontWeight: 500,
      ...style
    }
  }, /*#__PURE__*/React.createElement(__ds_scope.Icon, {
    name: t.icon,
    size: 22,
    white: true,
    assetsBase: assetsBase
  }), /*#__PURE__*/React.createElement("span", null, message), onClose && /*#__PURE__*/React.createElement("button", {
    onClick: onClose,
    "aria-label": "Zav\u0159\xEDt",
    style: {
      background: "none",
      border: "none",
      color: "#fff",
      cursor: "pointer",
      fontSize: 18,
      lineHeight: 1,
      padding: "0 0 0 6px",
      opacity: 0.8
    }
  }, "\xD7"));
}
Object.assign(__ds_scope, { Toast });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/feedback/Toast.jsx", error: String((e && e.message) || e) }); }

// components/feedback/Tooltip.jsx
try { (() => {
function Tooltip({
  label,
  marker = false,
  children,
  style
}) {
  const [show, setShow] = React.useState(false);
  return /*#__PURE__*/React.createElement("span", {
    style: {
      position: "relative",
      display: "inline-block",
      ...style
    },
    onMouseEnter: () => setShow(true),
    onMouseLeave: () => setShow(false),
    onFocus: () => setShow(true),
    onBlur: () => setShow(false)
  }, children, show && /*#__PURE__*/React.createElement("span", {
    role: "tooltip",
    style: {
      position: "absolute",
      bottom: "calc(100% + 8px)",
      left: "50%",
      transform: "translateX(-50%)",
      background: "var(--rb-anthracite)",
      color: "#fff",
      whiteSpace: "nowrap",
      zIndex: 100,
      fontFamily: marker ? "var(--font-accent)" : "var(--font-sans)",
      fontSize: marker ? 16 : 13,
      fontWeight: marker ? 400 : 500,
      padding: "6px 10px",
      borderRadius: 4,
      boxShadow: "var(--shadow-float)"
    }
  }, label));
}
Object.assign(__ds_scope, { Tooltip });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/feedback/Tooltip.jsx", error: String((e && e.message) || e) }); }

// components/forms/Button.jsx
try { (() => {
const SIZES = {
  sm: {
    pad: "8px 20px",
    font: 14
  },
  md: {
    pad: "12px 28px",
    font: 16
  },
  lg: {
    pad: "16px 36px",
    font: 18
  }
};

/* Hand-drawn brush frames (uploads: "Komponent RGB 1–8").
   short = 504×148 (compact labels), long = 905×149 (wide labels). */
/* Hand-drawn brush frames (uploads: "Komponent RGB 1–8").
   short = 504×148 (compact labels), long = ≈900×149 (wide labels).
   Red exists filled (solid CTA, white label) and outline; wine/grey are outlines. */
const FRAMES = {
  redFilled: {
    short: "frame-short-red.svg",
    long: "frame-long-red-2.svg"
  },
  red: {
    short: "frame-short-red-2.svg",
    long: "frame-long-red.svg"
  },
  wine: {
    short: "frame-short-wine.svg",
    long: "frame-long-wine.svg"
  },
  grey: {
    short: "frame-short-grey.svg",
    long: "frame-long-grey.svg"
  }
};
function Button({
  variant = "primary",
  size = "md",
  disabled = false,
  brush = true,
  long,
  children,
  onClick,
  assetsBase = "assets",
  style
}) {
  const [state, setState] = React.useState("idle");
  const s = SIZES[size] || SIZES.md;
  const ref = React.useRef(null);
  const [wide, setWide] = React.useState(false);
  React.useLayoutEffect(() => {
    if (long === undefined && ref.current) setWide(ref.current.offsetWidth / ref.current.offsetHeight > 4.2);
  }, [children, size, long]);
  const useLong = long === undefined ? wide : long;
  const base = {
    fontFamily: "var(--font-sans)",
    fontWeight: 800,
    fontSize: s.font,
    padding: s.pad,
    cursor: disabled ? "not-allowed" : "pointer",
    border: "none",
    background: "transparent",
    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    lineHeight: 1.2,
    position: "relative",
    transition: "color 150ms ease-out, transform 100ms ease-out, opacity 150ms ease-out",
    transform: state === "press" ? "scale(0.98)" : "none",
    opacity: disabled ? 0.45 : 1
  };

  // Brush-framed variants: the hand-drawn frame SVG stretched behind the label.
  // primary = FILLED red frame with white label; secondary/grey = outline frame with frame-color label.
  const frameColor = {
    primary: "redFilled",
    secondary: "wine",
    ghost: null,
    grey: "grey"
  }[variant];
  if (brush && frameColor) {
    const set = FRAMES[frameColor];
    const file = useLong ? set.long : set.short;
    const filled = frameColor === "redFilled";
    const outlineColor = {
      red: "var(--button-primary)",
      wine: "var(--rb-wine)",
      grey: "var(--rb-spanish-grey)"
    }[frameColor];
    const labelColor = filled ? "#ffffff" : state === "hover" && !disabled ? "var(--rb-wine)" : outlineColor;
    return /*#__PURE__*/React.createElement("button", {
      ref: ref,
      style: {
        ...base,
        color: labelColor,
        ...style
      },
      disabled: disabled,
      onClick: onClick,
      onMouseEnter: () => setState("hover"),
      onMouseLeave: () => setState("idle"),
      onMouseDown: () => setState("press"),
      onMouseUp: () => setState("hover")
    }, /*#__PURE__*/React.createElement("img", {
      src: assetsBase + "/frames/" + file,
      alt: "",
      "aria-hidden": "true",
      style: {
        position: "absolute",
        inset: 0,
        width: "100%",
        height: "100%",
        pointerEvents: "none",
        filter: state === "hover" && !disabled ? "brightness(0.72)" : "none",
        transition: "filter 150ms ease-out"
      }
    }), /*#__PURE__*/React.createElement("span", {
      style: {
        position: "relative"
      }
    }, children));
  }

  // Filled / ghost variants (brush={false}) — solid fallback for dark or photo backgrounds.
  const variants = {
    primary: {
      background: state === "hover" && !disabled ? "var(--rb-wine)" : "var(--button-primary)",
      color: "#fff",
      borderRadius: "var(--radius-button, 6px)"
    },
    secondary: {
      background: state === "hover" && !disabled ? "var(--rb-wine)" : "transparent",
      color: state === "hover" && !disabled ? "#fff" : "var(--rb-wine)",
      boxShadow: "inset 0 0 0 2px var(--rb-wine)",
      borderRadius: "var(--radius-button, 6px)"
    },
    dark: {
      background: state === "hover" && !disabled ? "#2e2e2e" : "var(--rb-anthracite)",
      color: "#fff",
      borderRadius: "var(--radius-button, 6px)"
    },
    ghost: {
      background: "transparent",
      color: state === "hover" && !disabled ? "var(--rb-wine)" : "var(--link)",
      padding: "4px 2px",
      borderRadius: 0,
      boxShadow: state === "hover" && !disabled ? "inset 0 -2px 0 var(--rb-wine)" : "inset 0 -2px 0 transparent"
    }
  };
  return /*#__PURE__*/React.createElement("button", {
    ref: ref,
    style: {
      ...base,
      ...(variants[variant] || variants.primary),
      ...style
    },
    disabled: disabled,
    onClick: onClick,
    onMouseEnter: () => setState("hover"),
    onMouseLeave: () => setState("idle"),
    onMouseDown: () => setState("press"),
    onMouseUp: () => setState("hover")
  }, children);
}
Object.assign(__ds_scope, { Button });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/Button.jsx", error: String((e && e.message) || e) }); }

// components/feedback/Dialog.jsx
try { (() => {
function Dialog({
  open = false,
  title,
  children,
  confirmLabel = "Jdu do toho!",
  cancelLabel = "Zavřít",
  onConfirm,
  onClose,
  width = 480,
  assetsBase = "assets"
}) {
  if (!open) return null;
  return /*#__PURE__*/React.createElement("div", {
    onClick: onClose,
    style: {
      position: "fixed",
      inset: 0,
      background: "rgba(68,68,68,0.55)",
      zIndex: 1000,
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      padding: 24
    }
  }, /*#__PURE__*/React.createElement("div", {
    role: "dialog",
    "aria-modal": "true",
    onClick: e => e.stopPropagation(),
    style: {
      background: "#fff",
      borderRadius: "var(--radius-card, 6px)",
      boxShadow: "var(--shadow-float)",
      width,
      maxWidth: "100%",
      padding: 32,
      fontFamily: "var(--font-sans)",
      color: "var(--text-body)"
    }
  }, title && /*#__PURE__*/React.createElement("h2", {
    style: {
      margin: "0 0 12px",
      fontWeight: 900,
      fontSize: 28,
      textTransform: "uppercase",
      color: "var(--text-heading)",
      lineHeight: 1.15
    }
  }, title), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 16,
      lineHeight: 1.6
    }
  }, children), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      gap: 12,
      marginTop: 24,
      justifyContent: "flex-end"
    }
  }, cancelLabel && /*#__PURE__*/React.createElement(__ds_scope.Button, {
    variant: "secondary",
    assetsBase: assetsBase,
    onClick: onClose
  }, cancelLabel), confirmLabel && /*#__PURE__*/React.createElement(__ds_scope.Button, {
    assetsBase: assetsBase,
    onClick: onConfirm
  }, confirmLabel))));
}
Object.assign(__ds_scope, { Dialog });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/feedback/Dialog.jsx", error: String((e && e.message) || e) }); }

// components/forms/Checkbox.jsx
try { (() => {
function Checkbox({
  label,
  checked,
  defaultChecked = false,
  onChange,
  disabled = false,
  style
}) {
  const isControlled = checked !== undefined;
  const [inner, setInner] = React.useState(defaultChecked);
  const on = isControlled ? checked : inner;
  const toggle = () => {
    if (disabled) return;
    if (!isControlled) setInner(!on);
    onChange && onChange(!on);
  };
  return /*#__PURE__*/React.createElement("label", {
    style: {
      display: "inline-flex",
      alignItems: "center",
      gap: 10,
      fontFamily: "var(--font-sans)",
      fontSize: 16,
      cursor: disabled ? "not-allowed" : "pointer",
      opacity: disabled ? 0.5 : 1,
      ...style
    }
  }, /*#__PURE__*/React.createElement("input", {
    type: "checkbox",
    checked: on,
    onChange: toggle,
    disabled: disabled,
    style: {
      position: "absolute",
      opacity: 0,
      width: 0,
      height: 0
    }
  }), /*#__PURE__*/React.createElement("span", {
    "aria-hidden": "true",
    style: {
      width: 22,
      height: 22,
      borderRadius: 4,
      flexShrink: 0,
      display: "inline-flex",
      alignItems: "center",
      justifyContent: "center",
      border: "2px solid " + (on ? "var(--rb-wine)" : "var(--rb-spanish-grey)"),
      background: on ? "var(--rb-wine)" : "#fff",
      transition: "all 150ms ease-out"
    }
  }, on && /*#__PURE__*/React.createElement("svg", {
    viewBox: "0 0 12 10",
    style: {
      width: 12,
      height: 10
    }
  }, /*#__PURE__*/React.createElement("path", {
    d: "M1 5.5 L4.2 8.5 L11 1",
    fill: "none",
    stroke: "#fff",
    strokeWidth: "2.4",
    strokeLinecap: "round",
    strokeLinejoin: "round"
  }))), /*#__PURE__*/React.createElement("span", null, label));
}
Object.assign(__ds_scope, { Checkbox });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/Checkbox.jsx", error: String((e && e.message) || e) }); }

// components/forms/IconButton.jsx
try { (() => {
function IconButton({
  icon = "arrow-right",
  label,
  size = 44,
  variant = "primary",
  disabled = false,
  onClick,
  assetsBase,
  style
}) {
  const [hover, setHover] = React.useState(false);
  const variants = {
    primary: {
      background: hover && !disabled ? "var(--rb-wine)" : "var(--button-primary)"
    },
    secondary: {
      background: "transparent",
      boxShadow: "inset 0 0 0 2px var(--rb-wine)"
    },
    dark: {
      background: hover && !disabled ? "#2e2e2e" : "var(--rb-anthracite)"
    }
  };
  const white = variant === "primary" || variant === "dark" || variant === "secondary" && false;
  return /*#__PURE__*/React.createElement("button", {
    "aria-label": label || icon,
    title: label || icon,
    disabled: disabled,
    onClick: onClick,
    onMouseEnter: () => setHover(true),
    onMouseLeave: () => setHover(false),
    style: {
      width: size,
      height: size,
      minWidth: 44,
      minHeight: 44,
      borderRadius: "var(--radius-button, 6px)",
      border: "none",
      display: "inline-flex",
      alignItems: "center",
      justifyContent: "center",
      cursor: disabled ? "not-allowed" : "pointer",
      opacity: disabled ? 0.45 : 1,
      transition: "background 150ms ease-out",
      ...(variants[variant] || variants.primary),
      ...style
    }
  }, /*#__PURE__*/React.createElement(__ds_scope.Icon, {
    name: icon,
    size: size * 0.55,
    white: white,
    assetsBase: assetsBase
  }));
}
Object.assign(__ds_scope, { IconButton });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/IconButton.jsx", error: String((e && e.message) || e) }); }

// components/forms/Input.jsx
try { (() => {
function Input({
  label,
  placeholder,
  type = "text",
  value,
  onChange,
  disabled = false,
  error,
  style
}) {
  const [focus, setFocus] = React.useState(false);
  const id = React.useId();
  return /*#__PURE__*/React.createElement("label", {
    htmlFor: id,
    style: {
      display: "flex",
      flexDirection: "column",
      gap: 6,
      fontFamily: "var(--font-sans)",
      ...style
    }
  }, label && /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 14,
      fontWeight: 700,
      color: "var(--text-heading)"
    }
  }, label), /*#__PURE__*/React.createElement("input", {
    id: id,
    type: type,
    placeholder: placeholder,
    value: value,
    onChange: onChange,
    disabled: disabled,
    onFocus: () => setFocus(true),
    onBlur: () => setFocus(false),
    style: {
      fontFamily: "var(--font-sans)",
      fontSize: 16,
      padding: "12px 14px",
      borderRadius: "var(--radius-card, 6px)",
      border: "2px solid " + (error ? "var(--rb-red-button)" : focus ? "var(--rb-wine)" : "var(--border-subtle)"),
      outline: "none",
      background: disabled ? "var(--surface-page)" : "#fff",
      color: "var(--text-body)",
      opacity: disabled ? 0.6 : 1,
      transition: "border-color 150ms ease-out"
    }
  }), error && /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 13,
      color: "var(--rb-red-button)",
      fontWeight: 500
    }
  }, error));
}
Object.assign(__ds_scope, { Input });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/Input.jsx", error: String((e && e.message) || e) }); }

// components/forms/Radio.jsx
try { (() => {
function Radio({
  label,
  name,
  checked = false,
  onChange,
  disabled = false,
  style
}) {
  return /*#__PURE__*/React.createElement("label", {
    style: {
      display: "inline-flex",
      alignItems: "center",
      gap: 10,
      fontFamily: "var(--font-sans)",
      fontSize: 16,
      cursor: disabled ? "not-allowed" : "pointer",
      opacity: disabled ? 0.5 : 1,
      ...style
    }
  }, /*#__PURE__*/React.createElement("input", {
    type: "radio",
    name: name,
    checked: checked,
    onChange: e => onChange && onChange(e),
    disabled: disabled,
    style: {
      position: "absolute",
      opacity: 0,
      width: 0,
      height: 0
    }
  }), /*#__PURE__*/React.createElement("span", {
    "aria-hidden": "true",
    style: {
      width: 22,
      height: 22,
      borderRadius: "50%",
      flexShrink: 0,
      display: "inline-flex",
      alignItems: "center",
      justifyContent: "center",
      border: "2px solid " + (checked ? "var(--rb-wine)" : "var(--rb-spanish-grey)"),
      background: "#fff",
      transition: "all 150ms ease-out"
    }
  }, checked && /*#__PURE__*/React.createElement("span", {
    style: {
      width: 10,
      height: 10,
      borderRadius: "50%",
      background: "var(--rb-wine)"
    }
  })), /*#__PURE__*/React.createElement("span", null, label));
}
Object.assign(__ds_scope, { Radio });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/Radio.jsx", error: String((e && e.message) || e) }); }

// components/forms/Select.jsx
try { (() => {
function Select({
  label,
  options = [],
  value,
  onChange,
  disabled = false,
  style
}) {
  const [focus, setFocus] = React.useState(false);
  const id = React.useId();
  return /*#__PURE__*/React.createElement("label", {
    htmlFor: id,
    style: {
      display: "flex",
      flexDirection: "column",
      gap: 6,
      fontFamily: "var(--font-sans)",
      ...style
    }
  }, label && /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 14,
      fontWeight: 700,
      color: "var(--text-heading)"
    }
  }, label), /*#__PURE__*/React.createElement("div", {
    style: {
      position: "relative"
    }
  }, /*#__PURE__*/React.createElement("select", {
    id: id,
    value: value,
    onChange: onChange,
    disabled: disabled,
    onFocus: () => setFocus(true),
    onBlur: () => setFocus(false),
    style: {
      appearance: "none",
      WebkitAppearance: "none",
      width: "100%",
      fontFamily: "var(--font-sans)",
      fontSize: 16,
      padding: "12px 40px 12px 14px",
      borderRadius: "var(--radius-card, 6px)",
      border: "2px solid " + (focus ? "var(--rb-wine)" : "var(--border-subtle)"),
      outline: "none",
      background: "#fff",
      color: "var(--text-body)",
      cursor: disabled ? "not-allowed" : "pointer",
      opacity: disabled ? 0.6 : 1
    }
  }, options.map(o => {
    const v = typeof o === "string" ? {
      value: o,
      label: o
    } : o;
    return /*#__PURE__*/React.createElement("option", {
      key: v.value,
      value: v.value
    }, v.label);
  })), /*#__PURE__*/React.createElement("span", {
    style: {
      position: "absolute",
      right: 14,
      top: "50%",
      transform: "translateY(-50%) rotate(45deg)",
      width: 8,
      height: 8,
      borderRight: "2px solid var(--rb-wine)",
      borderBottom: "2px solid var(--rb-wine)",
      pointerEvents: "none",
      marginTop: -2
    }
  })));
}
Object.assign(__ds_scope, { Select });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/Select.jsx", error: String((e && e.message) || e) }); }

// components/forms/Switch.jsx
try { (() => {
function Switch({
  label,
  checked,
  defaultChecked = false,
  onChange,
  disabled = false,
  style
}) {
  const isControlled = checked !== undefined;
  const [inner, setInner] = React.useState(defaultChecked);
  const on = isControlled ? checked : inner;
  const toggle = () => {
    if (disabled) return;
    if (!isControlled) setInner(!on);
    onChange && onChange(!on);
  };
  return /*#__PURE__*/React.createElement("label", {
    style: {
      display: "inline-flex",
      alignItems: "center",
      gap: 10,
      fontFamily: "var(--font-sans)",
      fontSize: 16,
      cursor: disabled ? "not-allowed" : "pointer",
      opacity: disabled ? 0.5 : 1,
      ...style
    }
  }, /*#__PURE__*/React.createElement("input", {
    type: "checkbox",
    role: "switch",
    checked: on,
    onChange: toggle,
    disabled: disabled,
    style: {
      position: "absolute",
      opacity: 0,
      width: 0,
      height: 0
    }
  }), /*#__PURE__*/React.createElement("span", {
    "aria-hidden": "true",
    style: {
      width: 44,
      height: 24,
      borderRadius: 999,
      background: on ? "var(--rb-wine)" : "var(--rb-grey)",
      position: "relative",
      transition: "background 150ms ease-out",
      flexShrink: 0
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      position: "absolute",
      top: 3,
      left: on ? 23 : 3,
      width: 18,
      height: 18,
      borderRadius: "50%",
      background: "#fff",
      transition: "left 150ms ease-out"
    }
  })), /*#__PURE__*/React.createElement("span", null, label));
}
Object.assign(__ds_scope, { Switch });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/Switch.jsx", error: String((e && e.message) || e) }); }

// ui_kits/social/PhotoPost.jsx
try { (() => {
function PhotoPost({
  hashtag = "#Leadership",
  photo,
  headline = "NEJSTE V TOM SAMI",
  quote = "\u201EMáme skvělé odborníky. Ale nejsou připraveni vést lidi.\u201C",
  body = "Tuhle větu slyšíme ve firmách čím dál častěji — silní experti excelují ve své oblasti, ale v roli lídra tápou. Chybí jim nejen potřebné dovednosti, ale především mindset a sebevědomí.",
  url = "www.redbuttonedu.cz",
  width = 540,
  assetsBase = "assets",
  style
}) {
  const s = width / 540;
  return /*#__PURE__*/React.createElement("div", {
    style: {
      width,
      height: width * 1.25,
      background: "var(--rb-off-white)",
      position: "relative",
      overflow: "hidden",
      fontFamily: "var(--font-sans)",
      color: "var(--rb-anthracite)",
      display: "flex",
      flexDirection: "column",
      ...style
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      padding: 18 * s + "px " + 24 * s + "px"
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: "var(--font-accent)",
      fontSize: 18 * s,
      color: "var(--rb-wine)"
    }
  }, hashtag), /*#__PURE__*/React.createElement("span", {
    style: {
      flex: 1,
      height: 2 * s,
      background: "var(--rb-wine)",
      margin: "0 " + 14 * s + "px",
      borderRadius: 2
    }
  }), /*#__PURE__*/React.createElement(__ds_scope.Logo, {
    variant: "horizontal-light",
    height: 22 * s,
    assetsBase: assetsBase
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      minHeight: 0,
      background: "var(--rb-grey)",
      overflow: "hidden"
    }
  }, photo && /*#__PURE__*/React.createElement("img", {
    src: photo,
    alt: "",
    style: {
      width: "100%",
      height: "100%",
      objectFit: "cover",
      filter: "grayscale(1)"
    }
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: 0 * s + "px " + 24 * s + "px " + 20 * s + "px",
      position: "relative"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "inline-block",
      background: "var(--rb-wine)",
      color: "#fff",
      fontWeight: 900,
      textTransform: "uppercase",
      fontSize: 26 * s,
      padding: 8 * s + "px " + 16 * s + "px",
      marginTop: -(22 * s),
      position: "relative",
      clipPath: "polygon(0% 10%, 2% 0%, 98% 3%, 100% 14%, 99% 86%, 100% 95%, 97% 100%, 3% 97%, 0% 90%)"
    }
  }, headline), /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: "var(--font-accent)",
      fontSize: 19 * s,
      color: "var(--rb-wine)",
      marginTop: 12 * s,
      lineHeight: 1.3
    }
  }, quote), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 13.5 * s,
      lineHeight: 1.5,
      marginTop: 10 * s,
      color: "var(--rb-anthracite)"
    }
  }, body), /*#__PURE__*/React.createElement(__ds_scope.Icon, {
    name: "idea-bulb",
    size: 40 * s,
    assetsBase: assetsBase,
    style: {
      position: "absolute",
      right: 24 * s,
      bottom: 48 * s
    }
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      marginTop: 14 * s,
      marginLeft: -(24 * s),
      marginRight: -(24 * s),
      background: "var(--rb-wine)",
      color: "#fff",
      fontWeight: 700,
      fontSize: 13 * s,
      padding: 7 * s + "px " + 24 * s + "px",
      clipPath: "polygon(0% 0%, 100% 15%, 100% 100%, 0% 100%)"
    }
  }, url)));
}
Object.assign(__ds_scope, { PhotoPost });
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/social/PhotoPost.jsx", error: String((e && e.message) || e) }); }

// ui_kits/social/SocialPost.jsx
try { (() => {
const RED_FILTER = "brightness(0) saturate(100%) invert(22%) sepia(93%) saturate(6995%) hue-rotate(342deg) brightness(101%) contrast(105%)";

/* Crops the 500×500 icon canvas to a horizontal band (for underline/arrow artwork). */
function IconBand({
  name,
  width,
  height,
  white = false,
  red = false,
  flip = false,
  assetsBase,
  style
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      width,
      height,
      overflow: "hidden",
      position: "relative",
      ...style
    }
  }, /*#__PURE__*/React.createElement(__ds_scope.Icon, {
    name: name,
    size: 0,
    white: white,
    assetsBase: assetsBase,
    style: {
      position: "absolute",
      left: 0,
      top: "50%",
      transform: "translateY(-50%)" + (flip ? " scaleX(-1)" : ""),
      width,
      height: "auto",
      ...(red ? {
        filter: RED_FILTER
      } : {})
    }
  }));
}
function SocialPost({
  variant = "light",
  title = "READY",
  title2 = "TO",
  titleAccent = "LEAD",
  subtitle = "Rozvojový program pro Albert",
  bullets = ["Šitý na míru, aby měnil mindset, ne jen dovednosti.", "Protože přechod z experta na lídra je cesta, ne okamžik."],
  width = 540,
  assetsBase = "assets",
  style
}) {
  const v = {
    light: {
      bg: "var(--rb-off-white)",
      head: "var(--rb-anthracite)",
      accent: "var(--rb-wine)",
      text: "var(--rb-anthracite)",
      marker: "var(--rb-wine)",
      net: "wine",
      netOp: 0.3,
      logo: "horizontal-light",
      arrowWhite: false,
      bulbWhite: false
    },
    wine: {
      bg: "var(--rb-wine)",
      head: "#ffffff",
      accent: "#ffffff",
      text: "#ffffff",
      marker: "#ffffff",
      net: "white",
      netOp: 0.45,
      logo: "horizontal-dark",
      arrowWhite: true,
      bulbWhite: true
    },
    anthracite: {
      bg: "var(--rb-anthracite)",
      head: "#ffffff",
      accent: "#ffffff",
      text: "#ffffff",
      marker: "#ffffff",
      net: "white",
      netOp: 0.4,
      logo: "horizontal-dark",
      arrowWhite: true,
      bulbWhite: false,
      bulbRed: true
    }
  }[variant] || {};
  const s = width / 540; // scale factor against 540px design
  return /*#__PURE__*/React.createElement("div", {
    style: {
      width,
      height: width * 1.25,
      background: v.bg,
      position: "relative",
      overflow: "hidden",
      fontFamily: "var(--font-sans)",
      color: v.text,
      ...style
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      position: "absolute",
      top: 24 * s,
      right: 24 * s
    }
  }, /*#__PURE__*/React.createElement(__ds_scope.Logo, {
    variant: v.logo,
    height: 26 * s,
    assetsBase: assetsBase
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: 110 * s + "px " + 40 * s + "px 0"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "flex-start",
      gap: 20 * s
    }
  }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      fontWeight: 900,
      fontSize: 46 * s,
      lineHeight: 1.06,
      textTransform: "uppercase",
      color: v.head
    }
  }, title, /*#__PURE__*/React.createElement("br", null), title2, " ", /*#__PURE__*/React.createElement("span", {
    style: {
      color: v.accent
    }
  }, titleAccent))), /*#__PURE__*/React.createElement(__ds_scope.Icon, {
    name: "idea-bulb",
    size: 66 * s,
    white: v.bulbWhite,
    assetsBase: assetsBase,
    style: {
      marginTop: 2 * s,
      ...(v.bulbRed ? {
        filter: RED_FILTER
      } : {})
    }
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: "var(--font-accent)",
      fontSize: 26 * s,
      lineHeight: 1.3,
      color: v.marker,
      marginTop: 20 * s,
      maxWidth: 340 * s
    }
  }, subtitle), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      flexDirection: "column",
      gap: 14 * s,
      marginTop: 22 * s,
      maxWidth: 400 * s
    }
  }, bullets.map((b, i) => /*#__PURE__*/React.createElement("div", {
    key: i,
    style: {
      display: "flex",
      gap: 12 * s,
      alignItems: "flex-start"
    }
  }, /*#__PURE__*/React.createElement(IconBand, {
    name: "arrow-curve-left",
    width: 30 * s,
    height: 16 * s,
    flip: true,
    white: v.arrowWhite,
    assetsBase: assetsBase,
    style: {
      marginTop: 4 * s,
      flexShrink: 0
    }
  }), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 17 * s,
      lineHeight: 1.45,
      fontWeight: 500
    }
  }, b)))), /*#__PURE__*/React.createElement(IconBand, {
    name: "arrow-curve-left",
    width: 160 * s,
    height: 44 * s,
    flip: true,
    white: v.arrowWhite,
    assetsBase: assetsBase,
    style: {
      position: "absolute",
      right: 90 * s,
      bottom: 160 * s
    }
  })), /*#__PURE__*/React.createElement(__ds_scope.NetPattern, {
    corner: "bottom-left",
    color: v.net,
    width: "115%",
    opacity: v.netOp,
    assetsBase: assetsBase,
    style: {
      maxWidth: "none"
    }
  }));
}
Object.assign(__ds_scope, { SocialPost });
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/social/SocialPost.jsx", error: String((e && e.message) || e) }); }

__ds_ns.ICON_NAMES = __ds_scope.ICON_NAMES;

__ds_ns.Icon = __ds_scope.Icon;

__ds_ns.Logo = __ds_scope.Logo;

__ds_ns.MarkerNote = __ds_scope.MarkerNote;

__ds_ns.NetPattern = __ds_scope.NetPattern;

__ds_ns.Badge = __ds_scope.Badge;

__ds_ns.Card = __ds_scope.Card;

__ds_ns.Tabs = __ds_scope.Tabs;

__ds_ns.Tag = __ds_scope.Tag;

__ds_ns.Dialog = __ds_scope.Dialog;

__ds_ns.Toast = __ds_scope.Toast;

__ds_ns.Tooltip = __ds_scope.Tooltip;

__ds_ns.Button = __ds_scope.Button;

__ds_ns.Checkbox = __ds_scope.Checkbox;

__ds_ns.IconButton = __ds_scope.IconButton;

__ds_ns.Input = __ds_scope.Input;

__ds_ns.Radio = __ds_scope.Radio;

__ds_ns.Select = __ds_scope.Select;

__ds_ns.Switch = __ds_scope.Switch;

__ds_ns.PhotoPost = __ds_scope.PhotoPost;

__ds_ns.SocialPost = __ds_scope.SocialPost;

})();
