/* Build script — Radar de Tendências Tecnológicas — deck de apresentação
 * Paleta "radar/sinal": navy quase-preto + verde-fósforo (tela de radar).
 * Roda com: node build-deck.js  (requer NODE_PATH apontando p/ node_modules globais)
 */
const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const fa = require("react-icons/fa");

// ---------------------------------------------------------------------------
// Design tokens
// ---------------------------------------------------------------------------
const COLOR = {
  bg: "0B1220",
  card: "141C2E",
  card2: "1B2438",
  border: "26314A",
  accent: "00D9A3",
  accentDim: "0A5C48",
  accentSoft: "12332C",
  text: "E8EEEC",
  muted: "8CA0A8",
  warn: "F5A623",
  danger: "F2545B",
  white: "FFFFFF",
};

const FONT_HEAD = "Consolas";
const FONT_BODY = "Calibri";

const PAGE_W = 13.333;
const PAGE_H = 7.5;
const MARGIN_X = 0.7;
const CONTENT_W = PAGE_W - MARGIN_X * 2;

function blend(hexA, hexB, ratio) {
  const a = [0, 2, 4].map((i) => parseInt(hexA.slice(i, i + 2), 16));
  const b = [0, 2, 4].map((i) => parseInt(hexB.slice(i, i + 2), 16));
  const c = a.map((v, i) => Math.round(v + (b[i] - v) * ratio));
  return c.map((v) => v.toString(16).padStart(2, "0")).join("").toUpperCase();
}

const makeShadow = (opacity = 0.35) => ({
  type: "outer", color: "000000", blur: 10, offset: 3, angle: 135, opacity,
});

// ---------------------------------------------------------------------------
// Icon rendering (react-icons -> PNG base64), cached
// ---------------------------------------------------------------------------
const iconCache = new Map();
async function icon(name, color = COLOR.accent, size = 256) {
  const key = `${name}_${color}_${size}`;
  if (iconCache.has(key)) return iconCache.get(key);
  const Comp = fa[name];
  if (!Comp) throw new Error(`Unknown icon: ${name}`);
  const svg = ReactDOMServer.renderToStaticMarkup(
    React.createElement(Comp, { color: `#${color}`, size: String(size) })
  );
  const png = await sharp(Buffer.from(svg)).png().toBuffer();
  const data = "image/png;base64," + png.toString("base64");
  iconCache.set(key, data);
  return data;
}

// ---------------------------------------------------------------------------
// Shared slide helpers
// ---------------------------------------------------------------------------
function baseSlide(pres) {
  const slide = pres.addSlide();
  slide.background = { color: COLOR.bg };
  return slide;
}

/** Decorative radar rings bleeding from a corner. corner: 'tr'|'br'|'tl' */
function radarMotif(slide, corner = "tr", scale = 1) {
  const size = 3.2 * scale;
  let cx, cy;
  if (corner === "tr") { cx = PAGE_W - 0.6; cy = 0.2; }
  else if (corner === "br") { cx = PAGE_W - 0.6; cy = PAGE_H - 0.6; }
  else { cx = 0.6; cy = PAGE_H - 0.6; }

  const rings = [
    { r: size, mix: 0.88 },
    { r: size * 0.68, mix: 0.78 },
    { r: size * 0.38, mix: 0.6 },
  ];
  for (const ring of rings) {
    const col = blend(COLOR.accent, COLOR.bg, ring.mix);
    slide.addShape("ellipse", {
      x: cx - ring.r, y: cy - ring.r, w: ring.r * 2, h: ring.r * 2,
      fill: { type: "none" }, line: { color: col, width: 1.25 },
    });
  }
}

function kicker(slide, text) {
  slide.addText(text.toUpperCase(), {
    x: MARGIN_X, y: 0.5, w: CONTENT_W, h: 0.35,
    fontFace: FONT_HEAD, fontSize: 12, bold: true, color: COLOR.accent,
    charSpacing: 3, margin: 0,
  });
}

function title(slide, text, opts = {}) {
  slide.addText(text, {
    x: MARGIN_X, y: 0.85, w: opts.w || CONTENT_W, h: opts.h || 0.9,
    fontFace: FONT_HEAD, fontSize: opts.fontSize || 30, bold: true,
    color: COLOR.text, margin: 0, valign: "top",
  });
}

function footer(slide, pageNum) {
  slide.addText("RADAR DE TENDÊNCIAS TECNOLÓGICAS  ·  SENAI FUTURO — IA", {
    x: MARGIN_X, y: PAGE_H - 0.42, w: 8, h: 0.3,
    fontFace: FONT_BODY, fontSize: 9, color: COLOR.muted, charSpacing: 1, margin: 0,
  });
  slide.addText(String(pageNum).padStart(2, "0"), {
    x: PAGE_W - MARGIN_X - 0.6, y: PAGE_H - 0.42, w: 0.6, h: 0.3,
    fontFace: FONT_HEAD, fontSize: 9, color: COLOR.muted, align: "right", margin: 0,
  });
}

/** Icon-in-circle badge */
function iconBadge(slide, iconData, { x, y, d = 0.55, bg = COLOR.accentSoft, iconScale = 0.56 }) {
  slide.addShape("ellipse", { x, y, w: d, h: d, fill: { color: bg }, line: { type: "none" } });
  const iw = d * iconScale;
  slide.addImage({ data: iconData, x: x + (d - iw) / 2, y: y + (d - iw) / 2, w: iw, h: iw });
}

/** A row: icon badge + bold heading + description text */
function iconRow(slide, iconData, headingText, bodyText, { x, y, w, badgeColor = COLOR.accentSoft }) {
  iconBadge(slide, iconData, { x, y, d: 0.5, bg: badgeColor });
  slide.addText(headingText, {
    x: x + 0.68, y: y - 0.03, w: w - 0.68, h: 0.32,
    fontFace: FONT_BODY, fontSize: 15, bold: true, color: COLOR.text, margin: 0,
  });
  slide.addText(bodyText, {
    x: x + 0.68, y: y + 0.27, w: w - 0.68, h: 0.6,
    fontFace: FONT_BODY, fontSize: 12, color: COLOR.muted, margin: 0, valign: "top",
  });
}

/** Card panel with border, used as content container */
function panel(slide, { x, y, w, h, fill = COLOR.card, line = COLOR.border }) {
  slide.addShape(pptxgenPres.shapes.RECTANGLE, {
    x, y, w, h, fill: { color: fill }, line: { color: line, width: 1 },
    shadow: makeShadow(0.25),
  });
}

let pptxgenPres; // set in main() so `panel()` can reach pres.shapes

// ---------------------------------------------------------------------------
// Main build
// ---------------------------------------------------------------------------
async function main() {
  const pres = new pptxgen();
  pptxgenPres = pres;
  pres.layout = "LAYOUT_WIDE";
  pres.author = "Carlos Araújo Jr.";
  pres.title = "Radar de Tendências Tecnológicas";

  // Pre-render icons
  const ic = {};
  const iconSpecs = [
    ["satellite", "FaSatelliteDish", COLOR.accent],
    ["satelliteDark", "FaSatelliteDish", COLOR.bg],
    ["search", "FaSearch", COLOR.accent],
    ["robot", "FaRobot", COLOR.accent],
    ["database", "FaDatabase", COLOR.accent],
    ["shield", "FaShieldAlt", COLOR.accent],
    ["flask", "FaFlask", COLOR.accent],
    ["chartline", "FaChartLine", COLOR.accent],
    ["newspaper", "FaNewspaper", COLOR.accent],
    ["building", "FaBuilding", COLOR.accent],
    ["certificate", "FaCertificate", COLOR.accent],
    ["check", "FaCheckCircle", COLOR.accent],
    ["warn", "FaExclamationTriangle", COLOR.warn],
    ["coins", "FaCoins", COLOR.accent],
    ["road", "FaRoad", COLOR.accent],
    ["github", "FaGithub", COLOR.text],
    ["cloud", "FaCloud", COLOR.accent],
    ["projectDiagram", "FaProjectDiagram", COLOR.accent],
    ["lightbulb", "FaLightbulb", COLOR.accent],
    ["lock", "FaLock", COLOR.accent],
    ["globe", "FaGlobe", COLOR.accent],
    ["clock", "FaClock", COLOR.accent],
    ["layerGroup", "FaLayerGroup", COLOR.accent],
    ["brain", "FaBrain", COLOR.accent],
    ["bug", "FaBug", COLOR.danger],
    ["wrench", "FaWrench", COLOR.accent],
    ["play", "FaPlay", COLOR.accent],
    ["book", "FaBook", COLOR.accent],
    ["clipboardList", "FaClipboardList", COLOR.accent],
  ];
  for (const [key, comp, col] of iconSpecs) {
    ic[key] = await icon(comp, col, 256);
  }

  // =========================================================================
  // SLIDE 1 — Capa
  // =========================================================================
  {
    const s = baseSlide(pres);
    radarMotif(s, "tr", 1.3);
    radarMotif(s, "bl", 0.5);

    iconBadge(s, ic.satellite, { x: MARGIN_X, y: 1.5, d: 1.0, bg: COLOR.accentSoft, iconScale: 0.55 });

    s.addText("SENAI FUTURO — DESAFIO IA", {
      x: MARGIN_X, y: 2.75, w: 10, h: 0.4,
      fontFace: FONT_HEAD, fontSize: 14, bold: true, color: COLOR.accent, charSpacing: 4, margin: 0,
    });
    s.addText("Radar de Tendências Tecnológicas", {
      x: MARGIN_X, y: 3.15, w: 11.5, h: 1.3,
      fontFace: FONT_HEAD, fontSize: 42, bold: true, color: COLOR.text, margin: 0,
    });
    s.addText("Um painel executivo que só afirma o que consegue provar.", {
      x: MARGIN_X, y: 4.35, w: 10, h: 0.5,
      fontFace: FONT_BODY, fontSize: 17, italic: true, color: COLOR.muted, margin: 0,
    });

    s.addShape("line", {
      x: MARGIN_X, y: 6.5, w: 3.2, h: 0, line: { color: COLOR.border, width: 1 },
    });
    s.addText("Carlos Araújo Jr.  ·  Apresentação técnica", {
      x: MARGIN_X, y: 6.65, w: 6, h: 0.4,
      fontFace: FONT_BODY, fontSize: 12, color: COLOR.muted, margin: 0,
    });
  }

  // =========================================================================
  // SLIDE 2 — O problema
  // =========================================================================
  {
    const s = baseSlide(pres);
    radarMotif(s, "br", 0.55);
    kicker(s, "O problema");
    title(s, "Tendências tecnológicas, decisões atrasadas");

    // Left: pull-quote style problem statement (single run — let PowerPoint wrap naturally)
    const quoteH = 2.05, quoteY = 2.05, attribY = quoteY + quoteH + 0.05, attribH = 0.35;
    s.addShape(pptxgenPres.shapes.RECTANGLE, {
      x: MARGIN_X, y: quoteY, w: 0.06, h: (attribY + attribH) - quoteY,
      fill: { color: COLOR.accent }, line: { type: "none" },
    });
    s.addText(
      "“A diretoria de uma empresa industrial deseja acompanhar tendências emergentes que possam impactar seus negócios nos próximos anos.”",
      {
        x: MARGIN_X + 0.35, y: quoteY, w: 5.3, h: quoteH,
        fontFace: FONT_HEAD, fontSize: 19, color: COLOR.text, margin: 0, valign: "top", lineSpacingMultiple: 1.3,
      }
    );
    s.addText("— recorte literal do desafio", {
      x: MARGIN_X + 0.35, y: attribY, w: 5.3, h: attribH,
      fontFace: FONT_BODY, fontSize: 12, italic: true, color: COLOR.muted, margin: 0,
    });

    // Right: 3 pain points
    const painX = 7.1;
    const painW = PAGE_W - MARGIN_X - painX;
    iconRow(s, ic.search, "Pesquisa manual e dispersa", "Cada tendência exige garimpar dezenas de fontes na mão, sem padrão.", { x: painX, y: 2.15, w: painW });
    iconRow(s, ic.warn, "Sem rastreabilidade", "Um resumo de IA genérico não dá pra citar com segurança em reunião de diretoria.", { x: painX, y: 3.35, w: painW });
    iconRow(s, ic.clock, "Semanas para consolidar", "O trabalho hoje depende de tempo humano — decisão estratégica sempre chega atrasada.", { x: painX, y: 4.55, w: painW });

    footer(s, 2);
  }

  // =========================================================================
  // SLIDE 3 — A proposta
  // =========================================================================
  {
    const s = baseSlide(pres);
    radarMotif(s, "tr", 1.0);
    kicker(s, "A proposta");
    title(s, "De tema livre a painel executivo, em minutos");

    // 3-node flow: Tema -> Radar -> Painel
    const nodeY = 2.6, nodeW = 3.1, nodeH = 1.8, gap = 0.55;
    const totalW = nodeW * 3 + gap * 2;
    const startX = (PAGE_W - totalW) / 2;
    const nodes = [
      { label: "Tema livre", sub: '"Edge AI"', ic: ic.search },
      { label: "Radar", sub: "coleta + síntese", ic: ic.satellite },
      { label: "Painel executivo", sub: "10 seções + evidências", ic: ic.layerGroup },
    ];
    nodes.forEach((n, i) => {
      const x = startX + i * (nodeW + gap);
      s.addShape(pptxgenPres.shapes.RECTANGLE, {
        x, y: nodeY, w: nodeW, h: nodeH,
        fill: { color: i === 1 ? COLOR.accentSoft : COLOR.card },
        line: { color: i === 1 ? COLOR.accent : COLOR.border, width: i === 1 ? 1.5 : 1 },
        shadow: makeShadow(0.3),
      });
      iconBadge(s, n.ic, { x: x + nodeW / 2 - 0.3, y: nodeY + 0.28, d: 0.6, bg: COLOR.card2 });
      s.addText(n.label, {
        x: x + 0.15, y: nodeY + 1.0, w: nodeW - 0.3, h: 0.4,
        fontFace: FONT_HEAD, fontSize: 16, bold: true, color: COLOR.text, align: "center", margin: 0,
      });
      s.addText(n.sub, {
        x: x + 0.15, y: nodeY + 1.38, w: nodeW - 0.3, h: 0.3,
        fontFace: FONT_BODY, fontSize: 11, color: COLOR.muted, align: "center", margin: 0,
      });
      if (i < 2) {
        s.addShape(pptxgenPres.shapes.RIGHT_ARROW, {
          x: x + nodeW + 0.06, y: nodeY + nodeH / 2 - 0.15, w: gap - 0.12, h: 0.3,
          fill: { color: COLOR.accent }, line: { type: "none" },
        });
      }
    });

    s.addText(
      [
        { text: "Cada afirmação é rastreável a uma evidência real ", options: { color: COLOR.text } },
        { text: "— ou é marcada como inferência.", options: { color: COLOR.accent, bold: true } },
      ],
      { x: MARGIN_X, y: 5.1, w: CONTENT_W, h: 0.5, fontFace: FONT_BODY, fontSize: 17, align: "center", margin: 0 }
    );

    footer(s, 3);
  }

  // =========================================================================
  // SLIDE 4 — Fluxo em 3 etapas (do enunciado)
  // =========================================================================
  {
    const s = baseSlide(pres);
    kicker(s, "Como funciona — conforme o desafio");
    title(s, "3 etapas, do enunciado à entrega");

    const stages = [
      { n: "1", h: "Definição do tema", d: "Usuário informa uma tendência ou tecnologia em texto livre.", ic: ic.search },
      { n: "2", h: "Coleta de evidências", d: "Fontes públicas e confiáveis: científicas, mercado, notícia, corporativa, patente.", ic: ic.satellite },
      { n: "3", h: "Consolidação", d: "Painel de 10 seções com grau de suporte calculado em código.", ic: ic.layerGroup },
    ];
    const cardW = 3.55, cardH = 2.5, gap = 0.4;
    const totalW = cardW * 3 + gap * 2;
    const startX = (PAGE_W - totalW) / 2;
    const y = 3.1;
    const numberColor = blend(COLOR.accent, COLOR.card, 0.15);

    stages.forEach((st, i) => {
      const x = startX + i * (cardW + gap);
      s.addShape(pptxgenPres.shapes.RECTANGLE, {
        x, y, w: cardW, h: cardH, fill: { color: COLOR.card }, line: { color: COLOR.border, width: 1 },
        shadow: makeShadow(0.3),
      });
      s.addText(st.n, {
        x: x + 0.25, y: y + 0.18, w: 0.8, h: 0.65,
        fontFace: FONT_HEAD, fontSize: 30, bold: true, color: numberColor, margin: 0,
      });
      iconBadge(s, st.ic, { x: x + cardW - 0.85, y: y + 0.22, d: 0.55, bg: COLOR.accentSoft });
      s.addText(st.h, {
        x: x + 0.25, y: y + 0.92, w: cardW - 0.5, h: 0.45,
        fontFace: FONT_HEAD, fontSize: 17, bold: true, color: COLOR.text, margin: 0,
      });
      s.addText(st.d, {
        x: x + 0.25, y: y + 1.4, w: cardW - 0.5, h: cardH - 1.4 - 0.15,
        fontFace: FONT_BODY, fontSize: 12.5, color: COLOR.muted, margin: 0, valign: "middle",
      });
      if (i < 2) {
        s.addShape(pptxgenPres.shapes.RIGHT_ARROW, {
          x: x + cardW + 0.04, y: y + cardH / 2 - 0.13, w: gap - 0.08, h: 0.26,
          fill: { color: COLOR.accent }, line: { type: "none" },
        });
      }
    });

    footer(s, 4);
  }

  // =========================================================================
  // SLIDE 5 — Arquitetura da solução
  // =========================================================================
  {
    const s = baseSlide(pres);
    kicker(s, "Arquitetura");
    title(s, "Do Streamlit ao Cosmos DB — visão completa");

    s.addText("App Service + Cosmos DB + Foundry na região Brazil South — colocalizados, zero latência cross-region.", {
      x: MARGIN_X, y: 1.5, w: CONTENT_W, h: 0.35,
      fontFace: FONT_BODY, fontSize: 12, italic: true, color: COLOR.muted, margin: 0,
    });

    // Single vertical spine — no diagonals, every arrow strictly vertical.
    const spineW = 6.7, spineX = (PAGE_W - spineW) / 2;
    const boxH = 0.55, splitBoxH = 0.65, arrowH = 0.22;

    function spineBox(y, h, label, opts = {}) {
      s.addShape(pptxgenPres.shapes.RECTANGLE, {
        x: spineX, y, w: spineW, h, fill: { color: opts.fill || COLOR.card },
        line: { color: opts.line || COLOR.border, width: opts.lw || 1 },
        shadow: makeShadow(0.25),
      });
      if (opts.split) {
        s.addShape("line", {
          x: spineX + spineW / 2, y: y + 0.1, w: 0, h: h - 0.2,
          line: { color: opts.line || COLOR.border, width: 1 },
        });
        s.addText(opts.split[0], {
          x: spineX + 0.15, y, w: spineW / 2 - 0.3, h,
          fontFace: FONT_BODY, fontSize: 11.5, bold: true, color: opts.color || COLOR.text,
          align: "center", valign: "middle", margin: 0,
        });
        s.addText(opts.split[1], {
          x: spineX + spineW / 2 + 0.15, y, w: spineW / 2 - 0.3, h,
          fontFace: FONT_BODY, fontSize: 11.5, bold: true, color: opts.color || COLOR.text,
          align: "center", valign: "middle", margin: 0,
        });
      } else {
        s.addText(label, {
          x: spineX + 0.15, y, w: spineW - 0.3, h,
          fontFace: FONT_BODY, fontSize: opts.fs || 13, bold: opts.bold !== false, color: opts.color || COLOR.text,
          align: "center", valign: "middle", margin: 0,
        });
      }
    }
    function downArrow(yTop, label) {
      s.addShape(pptxgenPres.shapes.RIGHT_ARROW, {
        x: spineX + spineW / 2 - 0.14, y: yTop, w: 0.28, h: arrowH,
        fill: { color: COLOR.accent }, line: { type: "none" }, rotate: 90,
      });
      if (label) {
        s.addText(label, {
          x: spineX + spineW / 2 + 0.25, y: yTop - 0.03, w: 2.6, h: arrowH + 0.06,
          fontFace: FONT_BODY, fontSize: 9.5, italic: true, color: COLOR.muted, valign: "middle", margin: 0,
        });
      }
    }

    let y = 1.98;
    spineBox(y, boxH, "Streamlit UI — Azure App Service", { fill: COLOR.accentSoft, line: COLOR.accent });
    const uiTop = y;
    y += boxH + 0.1;
    downArrow(y); y += arrowH + 0.1;

    spineBox(y, boxH, "Orquestrador (Python)");
    y += boxH + 0.1;
    downArrow(y, "coleta concorrente"); y += arrowH + 0.1;

    spineBox(y, splitBoxH, null, { split: ["arXiv + OpenAlex\n(coleta acadêmica)", "Agente Coletor — Foundry\nWeb Search · 4 perspectivas"] });
    y += splitBoxH + 0.1;
    downArrow(y, "dedup + numerado"); y += arrowH + 0.1;

    spineBox(y, splitBoxH, null, { split: ["Agente Sintetizador\n— Foundry", "Grau de suporte\n(código determinístico)"], fill: COLOR.accentSoft, line: COLOR.accent });
    y += splitBoxH + 0.1;
    downArrow(y); y += arrowH + 0.1;

    spineBox(y, boxH, "Cosmos DB — documento único por relatório", { fill: COLOR.card2 });
    const dbBottom = y + boxH;

    // Histórico: short side note near the top box instead of a long return line
    const noteX = spineX + spineW + 0.35, noteW = PAGE_W - MARGIN_X - noteX;
    s.addShape("line", {
      x: spineX + spineW, y: uiTop + boxH / 2, w: noteX - (spineX + spineW), h: 0,
      line: { color: COLOR.muted, width: 1, dashType: "dash" },
    });
    s.addShape(pptxgenPres.shapes.RECTANGLE, {
      x: noteX, y: uiTop - 0.15, w: noteW, h: 0.95,
      fill: { color: COLOR.card2 }, line: { color: COLOR.border, width: 1 },
    });
    s.addText("Histórico: reabre relatórios direto do Cosmos, sem nova coleta.", {
      x: noteX + 0.18, y: uiTop - 0.15, w: noteW - 0.36, h: 0.95,
      fontFace: FONT_BODY, fontSize: 11, italic: true, color: COLOR.muted, valign: "middle", margin: 0,
    });

    footer(s, 5);
  }

  // =========================================================================
  // SLIDE 6 — Arquitetura da solução (diagrama completo)
  // =========================================================================
  {
    const s = baseSlide(pres);
    kicker(s, "Arquitetura");
    title(s, "O diagrama completo, de ponta a ponta");

    s.addText("Guardrail de escopo, coleta em paralelo, síntese e persistência — cada bloco mapeado para um serviço Azure real.", {
      x: MARGIN_X, y: 1.5, w: CONTENT_W, h: 0.35,
      fontFace: FONT_BODY, fontSize: 12, italic: true, color: COLOR.muted, margin: 0,
    });

    const highlights = [
      { ic: ic.cloud, h: "Colocalizado em Brazil South", d: "App Service + Cosmos DB + Foundry na mesma região — zero latência cross-region." },
      { ic: ic.shield, h: "Guardrail antes do pipeline", d: "O Foundry classifica o tema antes de qualquer chamada cara (fail-open em caso de erro)." },
      { ic: ic.projectDiagram, h: "Camadas isoladas e testáveis", d: "Coleta, síntese e persistência são módulos independentes, cada um com sua própria suíte de testes." },
    ];
    const leftX = MARGIN_X, leftW = 3.5;
    let hy = 2.3;
    highlights.forEach((it) => {
      iconRow(s, it.ic, it.h, it.d, { x: leftX, y: hy, w: leftW });
      hy += 1.45;
    });

    // Framed diagram image (white card, matches the light background of the exported PNG)
    const imgH = 4.6, imgW = imgH * (2625 / 1905);
    const zoneX = leftX + leftW + 0.4, zoneW = PAGE_W - MARGIN_X - zoneX;
    const imgX = zoneX + (zoneW - imgW) / 2, imgY = 2.15;
    const pad = 0.12;
    s.addShape(pptxgenPres.shapes.RECTANGLE, {
      x: imgX - pad, y: imgY - pad, w: imgW + pad * 2, h: imgH + pad * 2,
      fill: { color: "FFFFFF" }, line: { color: COLOR.border, width: 1 },
      shadow: makeShadow(0.35),
    });
    s.addImage({
      path: require("path").join(__dirname, "criterios", "01-arquitetura.drawio.png"),
      x: imgX, y: imgY, w: imgW, h: imgH,
    });

    footer(s, 6);
  }

  // =========================================================================
  // SLIDE 7 — Diferencial: evidência rastreável por design
  // =========================================================================
  {
    const s = baseSlide(pres);
    radarMotif(s, "tr", 0.8);
    kicker(s, "O diferencial");
    title(s, "Quem gradua a confiança é código, não o modelo");

    const levels = [
      { label: "ALTO", rule: "≥4 evidências\nE ≥2 tipos de fonte", col: COLOR.accent },
      { label: "MÉDIO", rule: "2–3 evidências,\nou ≥4 com 1 tipo", col: blend(COLOR.accent, COLOR.warn, 0.5) },
      { label: "BAIXO", rule: "apenas\n1 evidência", col: COLOR.warn },
      { label: "INFERÊNCIA", rule: "0 evidências —\nmarcado explicitamente", col: COLOR.muted },
    ];
    const chipW = 2.7, chipH = 2.0, gap = 0.28;
    const totalW = chipW * 4 + gap * 3;
    const startX = (PAGE_W - totalW) / 2;
    const y = 2.15;

    levels.forEach((lv, i) => {
      const x = startX + i * (chipW + gap);
      s.addShape(pptxgenPres.shapes.RECTANGLE, {
        x, y, w: chipW, h: chipH, fill: { color: COLOR.card }, line: { color: lv.col, width: 1.5 },
        shadow: makeShadow(0.25),
      });
      s.addShape(pptxgenPres.shapes.RECTANGLE, {
        x, y, w: chipW, h: 0.12, fill: { color: lv.col }, line: { type: "none" },
      });
      s.addText(lv.label, {
        x: x + 0.15, y: y + 0.35, w: chipW - 0.3, h: 0.45,
        fontFace: FONT_HEAD, fontSize: 18, bold: true, color: lv.col, margin: 0,
      });
      s.addText(lv.rule, {
        x: x + 0.15, y: y + 0.95, w: chipW - 0.3, h: 0.9,
        fontFace: FONT_BODY, fontSize: 12.5, color: COLOR.muted, margin: 0, valign: "top",
      });
    });

    s.addShape(pptxgenPres.shapes.RECTANGLE, {
      x: MARGIN_X, y: 4.75, w: CONTENT_W, h: 1.15, fill: { color: COLOR.card2 }, line: { color: COLOR.border, width: 1 },
    });
    iconBadge(s, ic.shield, { x: MARGIN_X + 0.3, y: 4.75 + 0.28, d: 0.6, bg: COLOR.accentSoft });
    s.addText(
      [
        { text: "O Sintetizador só pode ", options: {} },
        { text: "citar", options: { bold: true, color: COLOR.text } },
        { text: " evidências. Um módulo separado, puro e testado ", options: {} },
        { text: "(7 testes unitários)", options: { color: COLOR.accent } },
        { text: ", calcula o grau — e rebaixa para inferência qualquer citação de id inexistente.", options: {} },
      ],
      {
        x: MARGIN_X + 1.1, y: 4.75 + 0.15, w: CONTENT_W - 1.4, h: 0.85,
        fontFace: FONT_BODY, fontSize: 13.5, color: COLOR.muted, margin: 0, valign: "middle",
      }
    );

    footer(s, 7);
  }

  // =========================================================================
  // SLIDE 8 — Coleta multi-perspectiva + fontes
  // =========================================================================
  {
    const s = baseSlide(pres);
    kicker(s, "Coleta de evidências");
    title(s, "4 perguntas concorrentes, 5 tipos de fonte");

    // Left: 4 perspectives converging into a single corpus below
    const perspectives = ["Técnica", "Econômica", "Industrial", "Regulatória"];
    const px = MARGIN_X, pw = 5.3;
    s.addText("Perspectivas (estilo STORM) — rodam em paralelo:", {
      x: px, y: 2.0, w: pw, h: 0.35, fontFace: FONT_BODY, fontSize: 13, bold: true, color: COLOR.text, margin: 0,
    });
    let rowY = 2.45;
    perspectives.forEach((p) => {
      s.addShape(pptxgenPres.shapes.RECTANGLE, {
        x: px, y: rowY, w: pw, h: 0.48, fill: { color: COLOR.card }, line: { color: COLOR.border, width: 1 },
      });
      s.addText(p, {
        x: px + 0.25, y: rowY, w: pw - 0.5, h: 0.48,
        fontFace: FONT_BODY, fontSize: 13, color: COLOR.text, valign: "middle", margin: 0,
      });
      rowY += 0.55;
    });
    s.addShape(pptxgenPres.shapes.RIGHT_ARROW, {
      x: px + pw / 2 - 0.14, y: rowY + 0.04, w: 0.28, h: 0.24,
      fill: { color: COLOR.accent }, line: { type: "none" }, rotate: 90,
    });
    rowY += 0.38;
    s.addShape(pptxgenPres.shapes.RECTANGLE, {
      x: px, y: rowY, w: pw, h: 0.55, fill: { color: COLOR.accentSoft }, line: { color: COLOR.accent, width: 1 },
    });
    s.addText("Corpus de evidências deduplicado", {
      x: px, y: rowY, w: pw, h: 0.55,
      fontFace: FONT_BODY, fontSize: 12.5, bold: true, color: COLOR.accent, align: "center", valign: "middle", margin: 0,
    });
    rowY += 0.65;
    s.addText("Medido no spike: ~30s/pergunta — concorrência é obrigatória p/ caber em 5 min (SC-001).", {
      x: px, y: rowY, w: pw, h: 0.4,
      fontFace: FONT_BODY, fontSize: 10.5, italic: true, color: COLOR.muted, margin: 0,
    });

    // Right: 5 source types
    const sx = 6.9, sw = PAGE_W - MARGIN_X - sx;
    const sources = [
      { ic: ic.flask, label: "Científica", sub: "arXiv, OpenAlex" },
      { ic: ic.chartline, label: "Mercado", sub: "consultorias" },
      { ic: ic.newspaper, label: "Notícia", sub: "imprensa especializada" },
      { ic: ic.building, label: "Corporativa", sub: "empresas" },
      { ic: ic.certificate, label: "Patente", sub: "sinais via busca" },
    ];
    s.addText("Tipos de fonte cobertos:", {
      x: sx, y: 2.0, w: sw, h: 0.35, fontFace: FONT_BODY, fontSize: 13, bold: true, color: COLOR.text, margin: 0,
    });
    sources.forEach((src, i) => {
      const y = 2.5 + i * 0.68;
      iconRow(s, src.ic, src.label, src.sub, { x: sx, y, w: sw });
    });

    s.addShape("line", {
      x: MARGIN_X, y: 6.28, w: CONTENT_W, h: 0, line: { color: COLOR.border, width: 1 },
    });
    s.addText(
      [
        { text: "Técnica de Shao et al., STORM — NAACL 2024, ", options: { color: COLOR.muted } },
        { text: "Stanford OVAL", options: { color: COLOR.accent, bold: true } },
        { text: " (Open Virtual Assistant Lab). Adaptada, não importada — sem o framework `knowledge-storm`.", options: { color: COLOR.muted } },
      ],
      {
        x: MARGIN_X, y: 6.4, w: CONTENT_W, h: 0.4,
        fontFace: FONT_BODY, fontSize: 10.5, italic: true, align: "center", margin: 0,
      }
    );

    footer(s, 8);
  }

  // =========================================================================
  // SLIDE 9 — Demo
  // =========================================================================
  {
    const s = baseSlide(pres);
    kicker(s, "Demonstração");
    title(s, "O sistema em funcionamento");

    const frameX = MARGIN_X, frameY = 1.95, frameW = CONTENT_W, frameH = 3.9;
    s.addShape(pptxgenPres.shapes.RECTANGLE, {
      x: frameX, y: frameY, w: frameW, h: frameH,
      fill: { color: COLOR.card }, line: { color: COLOR.accent, width: 1.5, dashType: "dash" },
    });
    iconBadge(s, ic.play, { x: frameX + frameW / 2 - 0.4, y: frameY + frameH / 2 - 0.75, d: 0.8, bg: COLOR.accentSoft, iconScale: 0.5 });
    s.addText("[ inserir GIF de navegação pelo sistema aqui ]", {
      x: frameX, y: frameY + frameH / 2 + 0.15, w: frameW, h: 0.4,
      fontFace: FONT_BODY, fontSize: 13, italic: true, color: COLOR.muted, align: "center", margin: 0,
    });

    const steps = ["1. Gerar painel novo", "2. Reabrir do histórico", "3. Explorar evidências"];
    const stepW = (CONTENT_W - 0.6) / 3;
    steps.forEach((st, i) => {
      s.addText(st, {
        x: MARGIN_X + i * (stepW + 0.3), y: 6.1, w: stepW, h: 0.4,
        fontFace: FONT_BODY, fontSize: 13, bold: true, color: COLOR.accent, align: "center", margin: 0,
      });
    });

    footer(s, 9);
  }

  // =========================================================================
  // SLIDE 10 — Resultados reais
  // =========================================================================
  {
    const s = baseSlide(pres);
    kicker(s, "Resultados reais — smoke test em produção");
    title(s, "Os 2 temas do desafio, de ponta a ponta");

    const results = [
      { theme: "Edge AI", time: "123s", ev: "53", types: "4", sections: "10/10" },
      { theme: "Robôs Humanoides p/ Indústria", time: "36,8s", ev: "44", types: "3", sections: "10/10" },
    ];
    const cardW = (CONTENT_W - 0.5) / 2, cardH = 4.1;
    results.forEach((r, i) => {
      const x = MARGIN_X + i * (cardW + 0.5);
      const y = 2.05;
      s.addShape(pptxgenPres.shapes.RECTANGLE, {
        x, y, w: cardW, h: cardH, fill: { color: COLOR.card }, line: { color: COLOR.border, width: 1 },
        shadow: makeShadow(0.3),
      });
      s.addText(r.theme, {
        x: x + 0.3, y: y + 0.25, w: cardW - 0.6, h: 0.5,
        fontFace: FONT_HEAD, fontSize: 18, bold: true, color: COLOR.text, margin: 0,
      });

      const stats = [
        { v: r.time, l: "duração total" },
        { v: r.ev, l: "evidências coletadas" },
        { v: r.types, l: "tipos de fonte" },
        { v: r.sections, l: "seções geradas" },
      ];
      const statW = (cardW - 0.6) / 2;
      stats.forEach((st, j) => {
        const sx = x + 0.3 + (j % 2) * statW;
        const sy = y + 0.95 + Math.floor(j / 2) * 1.15;
        s.addText(st.v, {
          x: sx, y: sy, w: statW - 0.2, h: 0.6,
          fontFace: FONT_HEAD, fontSize: 30, bold: true, color: COLOR.accent, margin: 0,
        });
        s.addText(st.l, {
          x: sx, y: sy + 0.58, w: statW - 0.2, h: 0.35,
          fontFace: FONT_BODY, fontSize: 10.5, color: COLOR.muted, margin: 0,
        });
      });

      s.addShape("line", { x: x + 0.3, y: y + 3.35, w: cardW - 0.6, h: 0, line: { color: COLOR.border, width: 1 } });
      iconBadge(s, ic.check, { x: x + 0.3, y: y + 3.5, d: 0.4, bg: COLOR.accentSoft, iconScale: 0.6 });
      s.addText("SC-001 (≤5min)", { x: x + 0.8, y: y + 3.5, w: (cardW - 1.1) / 2, h: 0.4, fontFace: FONT_BODY, fontSize: 11.5, color: COLOR.text, valign: "middle", margin: 0 });
      iconBadge(s, ic.check, { x: x + 0.3 + (cardW - 1.1) / 2 + 0.5, y: y + 3.5, d: 0.4, bg: COLOR.accentSoft, iconScale: 0.6 });
      s.addText("SC-005 (≥3 tipos)", { x: x + 0.8 + (cardW - 1.1) / 2 + 0.5, y: y + 3.5, w: (cardW - 1.1) / 2, h: 0.4, fontFace: FONT_BODY, fontSize: 11.5, color: COLOR.text, valign: "middle", margin: 0 });
    });

    footer(s, 10);
  }

  // =========================================================================
  // SLIDE 11 — Resiliência testada em produção
  // =========================================================================
  {
    const s = baseSlide(pres);
    kicker(s, "Maturidade de engenharia");
    title(s, "3 de 6 bugs reais — corrigidos antes da banca");

    const bugs = [
      { h: "Registro malformado derrubava a coleta", d: "Um campo nulo do OpenAlex escapava sem tratamento e abortava a análise inteira." },
      { h: "arXiv migrou para HTTPS", d: "Redirect não seguido pelo cliente HTTP — coleta acadêmica degradava 100% das vezes." },
      { h: "Erro de API não tratado na síntese", d: "Um rate limit real do modelo escapava do orquestrador e travava o processo." },
    ];
    const cardW = (CONTENT_W - 0.8) / 3, cardH = 2.65, gap = 0.4;
    const y = 2.95;
    bugs.forEach((b, i) => {
      const x = MARGIN_X + i * (cardW + gap);
      s.addShape(pptxgenPres.shapes.RECTANGLE, {
        x, y, w: cardW, h: cardH, fill: { color: COLOR.card }, line: { color: COLOR.border, width: 1 },
        shadow: makeShadow(0.25),
      });
      iconBadge(s, ic.bug, { x: x + 0.25, y: y + 0.22, d: 0.5, bg: COLOR.card2 });
      s.addText(b.h, {
        x: x + 0.25, y: y + 0.88, w: cardW - 0.5, h: 0.6,
        fontFace: FONT_BODY, fontSize: 13, bold: true, color: COLOR.text, margin: 0, valign: "top",
      });
      s.addText(b.d, {
        x: x + 0.25, y: y + 1.48, w: cardW - 0.5, h: 0.85,
        fontFace: FONT_BODY, fontSize: 11, color: COLOR.muted, margin: 0, valign: "top",
      });
      s.addText("→ corrigido + teste de regressão", {
        x: x + 0.25, y: y + cardH - 0.38, w: cardW - 0.5, h: 0.3,
        fontFace: FONT_BODY, fontSize: 10, bold: true, color: COLOR.accent, margin: 0,
      });
    });

    s.addText(
      "Outros 3 vieram da revisão de código automatizada — lista completa em docs/critical-review.md. Nenhum apareceu em testes mockados, só contra APIs reais.",
      {
        x: MARGIN_X, y: y + cardH + 0.3, w: CONTENT_W, h: 0.5,
        fontFace: FONT_BODY, fontSize: 12.5, italic: true, color: COLOR.muted, align: "center", margin: 0,
      }
    );

    footer(s, 11);
  }

  // =========================================================================
  // SLIDE 12 — Documentação e gestão do conhecimento
  // =========================================================================
  {
    const s = baseSlide(pres);
    kicker(s, "Qualidade de implementação");
    title(s, "Documentação como maturidade de gestão do conhecimento");

    const docs = [
      { ic: ic.book, h: "README.md", d: "visão geral, arquitetura em 1 parágrafo e quickstart" },
      { ic: ic.projectDiagram, h: "docs/architecture.md", d: "decisões técnicas e justificativas, com diagrama" },
      { ic: ic.warn, h: "docs/critical-review.md", d: "autoavaliação crítica contínua, achados reais datados" },
      { ic: ic.wrench, h: "infra/provision.md + RUNBOOK", d: "provisionamento, deploy e operação passo a passo" },
      { ic: ic.clipboardList, h: "Spec-Kit (constitution → spec → plan → tasks)", d: "especificação formal e rastreável, não improvisada" },
      { ic: ic.certificate, h: "Guia de arguição + critérios de avaliação", d: "material de defesa mapeado aos critérios da banca" },
      { ic: ic.layerGroup, h: "Project Book (novo)", d: "referência única do projeto para quem herdar ou avaliar" },
    ];
    const leftX = MARGIN_X, leftW = 7.0;
    let dy = 2.0;
    const rowH = 0.565;
    docs.forEach((it) => {
      iconBadge(s, it.ic, { x: leftX, y: dy, d: 0.4, bg: COLOR.accentSoft, iconScale: 0.52 });
      s.addText(
        [
          { text: it.h + "  ", options: { bold: true, color: COLOR.text } },
          { text: "— " + it.d, options: { color: COLOR.muted } },
        ],
        {
          x: leftX + 0.52, y: dy - 0.06, w: leftW - 0.52, h: rowH,
          fontFace: FONT_BODY, fontSize: 11.5, valign: "middle", margin: 0,
        }
      );
      dy += rowH;
    });

    // Right: knowledge-graph callout — the innovation
    const rx = leftX + leftW + 0.35, rw = PAGE_W - MARGIN_X - rx;
    panel(s, { x: rx, y: 2.0, w: rw, h: dy - 2.0 - 0.05, fill: COLOR.card2 });
    iconBadge(s, ic.brain, { x: rx + 0.3, y: 2.28, d: 0.6, bg: COLOR.accentSoft });
    s.addText("Grafo de conhecimento", {
      x: rx + 1.05, y: 2.3, w: rw - 1.3, h: 0.4,
      fontFace: FONT_BODY, fontSize: 14, bold: true, color: COLOR.text, margin: 0,
    });
    s.addText("Inovação — não um markdown a mais", {
      x: rx + 1.05, y: 2.62, w: rw - 1.3, h: 0.3,
      fontFace: FONT_BODY, fontSize: 10.5, italic: true, color: COLOR.accent, margin: 0,
    });
    s.addText("194 nós · 334 arestas · 9 camadas · 15 passos guiados", {
      x: rx + 0.3, y: 3.15, w: rw - 0.6, h: 0.5,
      fontFace: FONT_HEAD, fontSize: 12.5, bold: true, color: COLOR.accent, margin: 0,
    });
    s.addText(
      "Extraído automaticamente do código-fonte real via IA — documentação viva que nunca fica desatualizada, navegável por um tour guiado interativo. Pouco comum neste tipo de projeto.",
      {
        x: rx + 0.3, y: 3.65, w: rw - 0.6, h: dy - 3.65 - 0.15,
        fontFace: FONT_BODY, fontSize: 11, color: COLOR.muted, margin: 0, valign: "top",
      }
    );

    // Bottom strip: standards/practices followed
    const stripY = dy + 0.15;
    s.addShape(pptxgenPres.shapes.RECTANGLE, {
      x: MARGIN_X, y: stripY, w: CONTENT_W, h: 0.85,
      fill: { color: COLOR.card2 }, line: { color: COLOR.border, width: 1 },
    });
    iconBadge(s, ic.check, { x: MARGIN_X + 0.3, y: stripY + 0.15, d: 0.55, bg: COLOR.accentSoft });
    s.addText(
      [
        { text: "Práticas seguidas: ", options: { bold: true, color: COLOR.text } },
        {
          text: "Spec-Driven Development (Spec-Kit) · decisões registradas com justificativa (estilo ADR) · "
            + "revisão crítica contínua com achados reais datados · versionamento semântico via git.",
          options: { color: COLOR.muted },
        },
      ],
      {
        x: MARGIN_X + 1.05, y: stripY + 0.06, w: CONTENT_W - 1.35, h: 0.73,
        fontFace: FONT_BODY, fontSize: 11.5, margin: 0, valign: "middle",
      }
    );

    footer(s, 12);
  }

  // =========================================================================
  // SLIDE 13 — Avaliação crítica: custos
  // =========================================================================
  {
    const s = baseSlide(pres);
    kicker(s, "Avaliação crítica — custos");
    title(s, "O que custa operar isso de verdade");

    const bigStats = [
      { v: "~US$14-15", l: "fixo por mês\n(App Service + Cosmos)" },
      { v: "~US$0,20-0,50", l: "por análise\n(tokens + busca)" },
    ];
    const statW = 3.75;
    bigStats.forEach((st, i) => {
      const x = MARGIN_X + 0.3 + i * (statW + 0.45);
      iconBadge(s, ic.coins, { x, y: 2.2, d: 0.6, bg: COLOR.accentSoft });
      s.addText(st.v, {
        x, y: 2.95, w: statW, h: 0.65,
        fontFace: FONT_HEAD, fontSize: 27, bold: true, color: COLOR.accent, margin: 0,
      });
      s.addText(st.l, {
        x, y: 3.65, w: statW, h: 0.6,
        fontFace: FONT_BODY, fontSize: 13, color: COLOR.muted, margin: 0, valign: "top",
      });
    });

    // breakdown table
    const tblX = 9.55, tblW = PAGE_W - MARGIN_X - tblX;
    s.addShape(pptxgenPres.shapes.RECTANGLE, {
      x: tblX, y: 2.05, w: tblW, h: 2.7, fill: { color: COLOR.card2 }, line: { color: COLOR.border, width: 1 },
    });
    s.addText(
      [
        { text: "App Service B1", options: { bold: true, color: COLOR.text, breakLine: true } },
        { text: "Cosmos DB serverless", options: { bold: true, color: COLOR.text, breakLine: true } },
        { text: "Foundry / Web Search", options: { bold: true, color: COLOR.text, breakLine: true } },
        { text: "por token e por chamada", options: { color: COLOR.muted } },
      ],
      { x: tblX + 0.25, y: 2.25, w: tblW - 0.5, h: 2.3, fontFace: FONT_BODY, fontSize: 12, margin: 0, valign: "top", lineSpacingMultiple: 1.4 }
    );

    s.addText("Número exato pendente de confirmação via Azure Cost Management — estimativa declarada, não inventada.", {
      x: MARGIN_X, y: 5.1, w: CONTENT_W, h: 0.5,
      fontFace: FONT_BODY, fontSize: 12.5, italic: true, color: COLOR.muted, margin: 0,
    });

    footer(s, 13);
  }

  // =========================================================================
  // SLIDE 14 — Vieses e limitações
  // =========================================================================
  {
    const s = baseSlide(pres);
    kicker(s, "Avaliação crítica — vieses e limitações");
    title(s, "O que sabemos que não resolvemos");

    const leftItems = [
      { h: "Viés de fonte", d: "Consultorias pagas só entram pelo material público que elas divulgam." },
      { h: "Viés de idioma", d: "Corpus predominantemente em inglês; painel sempre em português." },
    ];
    const rightItems = [
      { h: "Viés de modelo", d: "Mitigado: só afirma com citação; grau nunca é autoavaliado pelo LLM." },
      { h: "Patentes sem API dedicada", d: "Cobertas só por sinais via busca — EPO OPS avaliada e adiada por prazo." },
    ];
    const colW = (CONTENT_W - 0.6) / 2;
    leftItems.forEach((it, i) => {
      iconRow(s, ic.warn, it.h, it.d, { x: MARGIN_X, y: 2.2 + i * 1.5, w: colW });
    });
    rightItems.forEach((it, i) => {
      iconRow(s, ic.warn, it.h, it.d, { x: MARGIN_X + colW + 0.6, y: 2.2 + i * 1.5, w: colW });
    });

    s.addShape(pptxgenPres.shapes.RECTANGLE, {
      x: MARGIN_X, y: 5.55, w: CONTENT_W, h: 1.05,
      fill: { color: COLOR.card2 }, line: { color: COLOR.border, width: 1 },
    });
    iconBadge(s, ic.shield, { x: MARGIN_X + 0.3, y: 5.55 + 0.23, d: 0.55, bg: COLOR.accentSoft });
    s.addText(
      "Nenhum viés aqui é “resolvido” — são mitigados por desenho (citação obrigatória, graduação em código) e documentados honestamente para a arguição.",
      {
        x: MARGIN_X + 1.05, y: 5.55 + 0.12, w: CONTENT_W - 1.35, h: 0.82,
        fontFace: FONT_BODY, fontSize: 13, color: COLOR.muted, margin: 0, valign: "middle",
      }
    );

    footer(s, 14);
  }

  // =========================================================================
  // SLIDE 15 — Evoluções futuras
  // =========================================================================
  {
    const s = baseSlide(pres);
    kicker(s, "Próximos passos");
    title(s, "Evoluções priorizadas");

    const items = [
      { ic: ic.brain, h: "Co-STORM", d: "Melhora coleta e síntese — agentes colaborativos" },
      { ic: ic.certificate, h: "Patentes dedicadas", d: "API EPO OPS — cobertura mundial" },
      { ic: ic.lock, h: "Multiusuário", d: "Easy Auth / Entra ID" },
      { ic: ic.clock, h: "Monitoramento contínuo", d: "Azure Functions com timer" },
      { ic: ic.chartline, h: "Observabilidade de custo", d: "Application Insights por consulta" },
    ];
    const gap = 0.3;
    const cardW = (CONTENT_W - gap * 4) / 5, cardH = 2.3, y = 3.3;
    items.forEach((it, i) => {
      const x = MARGIN_X + i * (cardW + gap);
      s.addShape(pptxgenPres.shapes.RECTANGLE, {
        x, y, w: cardW, h: cardH, fill: { color: COLOR.card }, line: { color: COLOR.border, width: 1 },
        shadow: makeShadow(0.25),
      });
      iconBadge(s, it.ic, { x: x + cardW / 2 - 0.25, y: y + 0.25, d: 0.5, bg: COLOR.accentSoft });
      s.addText(it.h, {
        x: x + 0.1, y: y + 0.98, w: cardW - 0.2, h: 0.5,
        fontFace: FONT_BODY, fontSize: 12, bold: true, color: COLOR.text, align: "center", margin: 0, valign: "top",
      });
      s.addText(it.d, {
        x: x + 0.1, y: y + 1.5, w: cardW - 0.2, h: cardH - 1.5 - 0.1,
        fontFace: FONT_BODY, fontSize: 9.5, color: COLOR.muted, align: "center", margin: 0, valign: "middle",
      });
    });

    footer(s, 15);
  }

  // =========================================================================
  // SLIDE 16 — Fechamento
  // =========================================================================
  {
    const s = baseSlide(pres);
    radarMotif(s, "tr", 1.3);
    radarMotif(s, "bl", 0.9);

    iconBadge(s, ic.satellite, { x: PAGE_W / 2 - 0.5, y: 2.1, d: 1.0, bg: COLOR.accentSoft, iconScale: 0.55 });
    s.addText("Obrigado.", {
      x: 0, y: 3.35, w: PAGE_W, h: 0.9,
      fontFace: FONT_HEAD, fontSize: 38, bold: true, color: COLOR.text, align: "center", margin: 0,
    });
    s.addText("Perguntas, críticas e sugestões são bem-vindas.", {
      x: 0, y: 4.2, w: PAGE_W, h: 0.5,
      fontFace: FONT_BODY, fontSize: 16, italic: true, color: COLOR.muted, align: "center", margin: 0,
    });
    iconBadge(s, ic.github, { x: PAGE_W / 2 - 2.35, y: 5.15, d: 0.4, bg: COLOR.card2, iconScale: 0.6 });
    s.addText("github.com/Carlosaaajr/radar-tendencias-tecnologicas", {
      x: PAGE_W / 2 - 1.85, y: 5.15, w: 4.2, h: 0.4,
      fontFace: FONT_BODY, fontSize: 13, color: COLOR.muted, valign: "middle", margin: 0,
    });
  }

  const outPath = require("path").join(__dirname, "radar-tendencias-apresentacao.pptx");
  await pres.writeFile({ fileName: outPath });
  console.log("Deck gerado em:", outPath);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
