// ==UserScript==
// @name         FMP Direct Bridge — Transferts vers widget Android
// @namespace    fmp.widget.direct-bridge
// @version      2.2.1
// @description  Pont local FMP vers Android, selection du club dans une liste tactile, sans OCR navigateur. Indépendant de FMP Squad Advisor.
// @match        https://footballmanagerproject.com/*
// @match        https://www.footballmanagerproject.com/*
// @grant        GM_xmlhttpRequest
// @grant        GM_getValue
// @grant        GM_setValue
// @grant        GM_registerMenuCommand
// @connect      127.0.0.1
// @run-at       document-idle
// ==/UserScript==

(function () {
  'use strict';
  const ENDPOINT = 'http://127.0.0.1:28471/v2/transfers';
  const LAST_STATUS = 'fmp-bridge-last-status';
  const TOKEN_NAME = 'fmp-bridge-private-key';
  const CLUB_NAME = 'fmp-bridge-selected-club-v22';
  const CLUB_PAUSED = 'fmp-bridge-paused-nt-v221';
  const MANAGED_CLUBS = ['Circle SC','Kazakh Very Nice United','Chicken Run SC'];
  const NATIONAL_TEAM = /\(NT\)\s*$/i;
  const validClub = raw => {
    const clean = String(raw || '').replace(/\s+/g,' ').trim();
    if (!clean || clean.length > 80 || NATIONAL_TEAM.test(clean) ||
        /^new zealand\s*\(nt\)$/i.test(clean) ||
        !/^[\p{L}\p{N} .'’()\-&]+$/u.test(clean)) return '';
    return MANAGED_CLUBS.find(name => name.toLowerCase() === clean.toLowerCase()) || clean;
  };
  function detectedClub(root = document) {
    // Only positive, single-active-team markers. A list of teams in FMPbar
    // does NOT identify the current team and must never be guessed.
    const selectors = [
      '[data-current-club]','[data-active-club]','[data-selected-club]',
      '.fmpbar-current-team','.fmpbar-active-team','#fmpbar .current-team',
      '#fmpbar [aria-selected="true"]','#fmpbar [aria-current="page"]',
      '#fmpbar .team.active','#fmpbar .team.selected',
      '.fmpbar select[name*="team"] option:checked',
      '.fmpbar select[name*="club"] option:checked'
    ];
    for (const selector of selectors) {
      let nodes=[];
      try { nodes=Array.from(root.querySelectorAll(selector)); } catch (_) { continue; }
      for(const element of nodes) {
        const possible=[element.getAttribute?.('data-current-club'),
          element.getAttribute?.('data-active-club'),
          element.getAttribute?.('data-selected-club'),element.textContent];
        for(const raw of possible) {
          const club=validClub(raw);
          if (club && MANAGED_CLUBS.some(c=>c.toLowerCase()===club.toLowerCase()))
            return club;
        }
      }
    }
    return '';
  }
  function currentClub() {
    if (GM_getValue(CLUB_PAUSED, false)) return '';
    const automatic=detectedClub();
    return automatic || validClub(GM_getValue(CLUB_NAME,'') || '');
  }
  const SECTION_RULES = [
    [/^(?:votre liste de favoris|your favou?rites list)$/i, 0],
    [/^(?:offres pour vos joueurs|offers for your players)$/i, 1],
    [/^(?:vos offres|your offers)$/i, 2],
    [/^(?:offres en attente|pending offers)$/i, 3],
  ];
  // The badges may be glued directly to a name by textContent (FocquetNON).
  const BADGES = /\s*NON\s*PERTINENT\b|\s*RISQU[EÉ]\s*\/?\s*PETIT\s+GAIN\b|\s*FMP\s+Squad\s+Advisor\b/gi;
  const normalize = text => String(text || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '')
    .replace(/\s+/g, ' ').trim().toLowerCase();
  const plain = text => String(text || '').replace(BADGES, ' ').replace(/\s+/g, ' ').trim();
  const key = text => normalize(text).replace(/[^a-z0-9]+/g, ' ').trim();
  const isTransferPage = () => normalize(document.body?.textContent || '').includes('offres concernant votre equipe') ||
    normalize(document.body?.textContent || '').includes('offers concerning your team');

  function sectionOf(value) {
    const t = normalize(value);
    for (const [pattern, section] of SECTION_RULES) if (pattern.test(t)) return section;
    return -1;
  }
  function headings() {
    const all = document.querySelectorAll('h1,h2,h3,h4,h5,h6,div,span,strong,b,legend');
    const found = [];
    for (const node of all) {
      if (node.closest('table,[role="table"]')) continue;
      const label = plain(node.textContent);
      if (label.length > 65) continue;
      const section = sectionOf(label);
      if (section < 0) continue;
      if (found.some(v => v.node.contains(node))) continue;
      found.push({ node, section });
    }
    return found;
  }
  function getCells(tr) {
    const direct = Array.from(tr.children || []).filter(c => /^(td|th)$/i.test(c.tagName));
    return direct.length ? direct : Array.from(tr.querySelectorAll('[role="cell"],[role="columnheader"]'));
  }
  function cleanCell(node) {
    if (!node) return '';
    // Work on a detached copy: never modify the FMP page or Squad Advisor.
    const copy = node.cloneNode(true);
    copy.querySelectorAll('script,style,button,input,select,textarea,[class*="squad-advisor" i], [id*="squad-advisor" i], [data-fmp-advisor]').forEach(n => n.remove());
    // Remove only badge-specific elements, never the enclosing player cell.
    for (const el of Array.from(copy.querySelectorAll('*')).reverse()) {
      const t = normalize(el.textContent || '');
      if (/^(?:non pertinent|non|pertinent|risque\s*\/?\s*petit gain|risque|petit gain|fmp squad advisor)$/.test(t)) el.remove();
    }
    return plain(copy.textContent || '');
  }
  function col(headers, patterns, fallback) {
    for (let i = 0; i < headers.length; i++)
      if (patterns.some(p => p.test(normalize(headers[i])))) return i;
    return fallback;
  }
  function money(raw) {
    const t = String(raw || '').replace(/\u00a0/g, ' ');
    const candidates = t.match(/\d{1,3}(?:[., ]\d{3})+|\b\d{4,12}\b/g) || [];
    const price = candidates.map(v => v.trim()).filter(v => v.replace(/\D/g, '').length >= 4).pop();
    if (!price) return '';
    const digits = price.replace(/\D/g, '');
    return digits.length <= 12 ? Number(digits).toLocaleString('en-US') : '';
  }
  function deadline(raw) {
    const t = normalize(raw);
    if (/\b(vendu|sold|expire|termine)\b/.test(t)) return 'Vendu';
    const pieces = [...t.matchAll(/(\d{1,3})\s*(min|[jdhms])/g)];
    return pieces.length ? pieces.map(v => v[1] + v[2]).join(' ') : '';
  }
  function playerName(raw) {
    let t = plain(raw).replace(/[\u{1F1E6}-\u{1F1FF}]/gu, '').trim();
    // Partial badges must never become parts of footballers' surnames.
    t = t.replace(/([a-zà-ÿ])NON$/u, '$1')
      .replace(/([a-zà-ÿ])RISQU[EÉ]$/u, '$1')
      .replace(/\b(?:NON|PERTINENT|RISQU[EÉ]|PETIT|GAIN)\b/gi, ' ');
    t = t.replace(/\s+/g, ' ').replace(/^[^\p{L}]+/u, '').trim();
    if (!/^[\p{L}][\p{L} .’'\-]{2,75}$/u.test(t)) return '';
    const words = t.split(' ').filter(Boolean);
    if (words.length < 2 || words.length > 5) return '';
    if (/\b(?:Football|Manager|Copyright|Manual|Advisor|Service|Evaluation|Infos?)\b/i.test(t)) return '';
    return t;
  }
  function parseRowCells(values, section, indices) {
    const name = playerName(values[indices.name] || '');
    if (!name) return null;
    const amount = money(values[indices.offer] || '');
    const end = deadline(values[indices.end] || '');
    // In Firefox, Squad Advisor may cover the bid and expiry of an otherwise
    // valid player row. An age column confirms this is a player, not a badge.
    const age = String(values[indices.age] || '').trim();
    const corroborated = /^(?:1[6-9]|[2-4][0-9])(?:\d{2})?$/.test(age);
    if (!amount && !end && !corroborated) return null;
    return { section, name, offer: amount, deadline: end };
  }
  function parseTable(table, section) {
    const rows = Array.from(table.querySelectorAll('tr,[role="row"]')).filter(x => x.closest('table,[role="table"]') === table);
    if (!rows.length) return [];
    let header = null;
    for (const r of rows) {
      const labels = getCells(r).map(cleanCell);
      if (labels.some(x => /^nom$|^name$/i.test(x)) && labels.some(x => /^offre$|^offer$|^bid$/i.test(x))) { header = r; break; }
    }
    if (!header) return []; // No blind parsing of unrelated tables.
    const labels = getCells(header).map(cleanCell);
    const indices = {
      name: col(labels, [/^nom$/, /^name$/], 1),
      age: col(labels, [/^age$/, /^âge$/], 2),
      offer: col(labels, [/^offre$/, /^bid$/, /^offer$/], 6),
      end: col(labels, [/^fin$/, /^end$/, /^expires?$/], 7),
    };
    if (indices.name === indices.offer || indices.offer === indices.end) return [];
    const found = [];
    for (const row of rows) {
      if (row === header) continue;
      const cells = getCells(row);
      if (cells.length <= Math.max(indices.name, indices.offer)) continue;
      const data = cells.map(cleanCell);
      const item = parseRowCells(data, section, indices);
      if (item) found.push(item);
    }
    return found;
  }
  function readTables() {
    if (!isTransferPage()) return [];
    const titleNodes = headings();
    const results = new Map();
    const allTables = Array.from(document.querySelectorAll('table,[role="table"]'));
    for (const table of allTables) {
      let section = -1;
      for (const h of titleNodes) {
        if (h.node === table) continue;
        if (h.node.compareDocumentPosition(table) & Node.DOCUMENT_POSITION_FOLLOWING) section = h.section;
      }
      if (section < 0) continue;
      for (const item of parseTable(table, section)) results.set(`${item.section}:${key(item.name)}`, item);
    }
    return [...results.values()];
  }

  let busy = false, pending = false, lastSent = '', lastAttempt = 0;
  let clubDialogOpen = false;
  function httpPush(rows, club, reason) {
    const token = String(GM_getValue(TOKEN_NAME, '') || '').trim();
    if (!/^[a-f0-9]{64}$/.test(token)) {
      GM_setValue(LAST_STATUS, 'Non associé : configurer la clé dans le menu Violentmonkey.');
      return;
    }
    const body = JSON.stringify({ v: 2, source: 'fmp-dom', observedAt: Date.now(), club, transfers: rows });
    busy = true;
    GM_xmlhttpRequest({
      method: 'POST', url: ENDPOINT, data: body,
      headers: { 'Content-Type': 'application/json', 'X-FMP-Bridge-Token': token },
      timeout: 5000,
      onload(response) {
        busy = false;
        if (response.status === 200) {
          lastSent = JSON.stringify({club,rows});
          GM_setValue(LAST_STATUS, `OK : ${rows.length} transfert(s) • ${club} • ${new Date().toLocaleTimeString('fr-FR')}.`);
        } else {
          GM_setValue(LAST_STATUS, `Erreur locale ${response.status} : vérifier le pont Android et la clé.`);
        }
        if (pending) { pending = false; schedule(); }
      },
      onerror() { busy = false; GM_setValue(LAST_STATUS, 'Connexion impossible : démarrer le pont dans l’application Android.'); },
      ontimeout() { busy = false; GM_setValue(LAST_STATUS, 'Connexion locale expirée.'); },
    });
  }
  function sync(force = false) {
    if (clubDialogOpen) return;
    if (busy) { pending = true; return; }
    if (!force && Date.now() - lastAttempt < 4000) return;
    lastAttempt = Date.now();
    const club = currentClub();
    if(!club) {
      GM_setValue(LAST_STATUS, GM_getValue(CLUB_PAUSED, false)
        ? 'Équipe nationale (NT) : synchronisation suspendue.'
        : 'Club non identifié : menu Violentmonkey → FMP : choisir le club actif. Aucune offre envoyée.');
      return;
    }
    if(NATIONAL_TEAM.test(club)) {
      GM_setValue(LAST_STATUS,'Équipe nationale (NT) exclue : aucun transfert envoyé.');
      return;
    }
    const rows = readTables();
    if (!rows.length) {
      if (force) GM_setValue(LAST_STATUS, 'Aucune ligne lisible : vérifier la page des offres et les tableaux HTML.');
      return;
    }
    if (!force && JSON.stringify({club,rows}) === lastSent) return;
    httpPush(rows,club,force ? 'manual' : 'auto');
  }
  let timer;
  function schedule() { clearTimeout(timer); timer = setTimeout(() => sync(), 1200); }
  GM_registerMenuCommand('FMP : configurer la clé du pont Android', () => {
    const entered = prompt('Copie la clé depuis FMP Mes transferts → Copier la clé Firefox.\nColle-la ici (64 caractères).', '');
    if (entered === null) return;
    const value = entered.trim().toLowerCase();
    if (!/^[a-f0-9]{64}$/.test(value)) { alert('Clé invalide : elle doit contenir 64 caractères hexadécimaux.'); return; }
    GM_setValue(TOKEN_NAME, value); lastSent = ''; GM_setValue(LAST_STATUS, 'Clé enregistrée uniquement dans Violentmonkey.');
    sync(true);
  });
  // A native Android-friendly <select> replaces the old prompt() text entry.
  // The dialog is added to the page only when the user chooses the menu item.
  function chooseClubFromList() {
    if (!document.body) {
      alert('La page FMP doit être ouverte pour sélectionner un club.');
      return;
    }
    document.getElementById('fmp-bridge-club-dialog-v221')?.remove();
    clubDialogOpen = true;

    const overlay = document.createElement('div');
    overlay.id = 'fmp-bridge-club-dialog-v221';
    overlay.setAttribute('role', 'dialog');
    overlay.setAttribute('aria-modal', 'true');
    overlay.setAttribute('aria-label', 'Choisir le club actif FMP');
    overlay.style.cssText = 'position:fixed!important;inset:0!important;z-index:2147483647!important;'+
      'display:flex!important;align-items:center!important;justify-content:center!important;'+
      'background:rgba(0,0,0,.72)!important;padding:16px!important;box-sizing:border-box!important;';

    const card = document.createElement('div');
    card.style.cssText = 'width:min(100%,410px)!important;max-height:85vh!important;overflow-y:auto!important;'+
      'box-sizing:border-box!important;background:#123510!important;color:#fff!important;'+
      'border:2px solid #7bb64b!important;border-radius:16px!important;'+
      'padding:20px!important;font:16px/1.4 system-ui,sans-serif!important;'+
      'box-shadow:0 16px 36px rgba(0,0,0,.5)!important;';

    const heading = document.createElement('div');
    heading.textContent = 'Choisir le club actif';
    heading.style.cssText = 'font-size:21px!important;font-weight:700!important;margin-bottom:12px!important;';

    const description = document.createElement('p');
    description.textContent = 'Sélectionne le club que tu consultes actuellement dans FMP :';
    description.style.cssText = 'margin:0 0 12px!important;color:#d9e9d0!important;';

    const select = document.createElement('select');
    select.setAttribute('aria-label', 'Liste des clubs FMP');
    select.style.cssText = 'width:100%!important;min-height:52px!important;font-size:17px!important;'+
      'box-sizing:border-box!important;background:#fff!important;color:#132a11!important;'+
      'border:2px solid #75ad51!important;border-radius:8px!important;'+
      'padding:8px!important;';

    const option = (value, label) => {
      const o = document.createElement('option');
      o.value = value;
      o.textContent = label;
      select.appendChild(o);
    };
    option('', '— Sélectionner un club —');
    for (const club of MANAGED_CLUBS) option(club, club);
    option('__NT__', 'New Zealand (NT) — ne pas synchroniser');

    // Never make a guess: only an explicit user selection can be submitted.
    select.value = '';

    const note = document.createElement('p');
    note.textContent = 'Nouvelle équipe ? Choisis-la de nouveau dans ce menu. Les équipes (NT) sont exclues.';
    note.style.cssText = 'font-size:13px!important;color:#bfcebd!important;margin:10px 0 14px!important;';

    const buttons = document.createElement('div');
    buttons.style.cssText = 'display:flex!important;gap:10px!important;';
    const cancel = document.createElement('button');
    cancel.type = 'button';
    cancel.textContent = 'Annuler';
    cancel.style.cssText = 'flex:1!important;min-height:46px!important;font:inherit!important;'+
      'background:#30492e!important;color:white!important;border:0!important;'+
      'border-radius:8px!important;';
    const confirm = document.createElement('button');
    confirm.type = 'button';
    confirm.textContent = 'Valider';
    confirm.disabled = true;
    confirm.style.cssText = 'flex:1!important;min-height:46px!important;font:inherit!important;'+
      'background:#8ac557!important;color:#0b2508!important;border:0!important;'+
      'border-radius:8px!important;font-weight:700!important;';
    select.addEventListener('change', () => { confirm.disabled = !select.value; });

    const close = () => {
      overlay.remove();
      clubDialogOpen = false;
    };
    cancel.addEventListener('click', close);
    overlay.addEventListener('click', event => {
      if (event.target === overlay) close();
    });
    overlay.addEventListener('keydown', event => {
      if (event.key === 'Escape') { event.preventDefault(); close(); }
    });
    confirm.addEventListener('click', () => {
      const chosen = select.value;
      if (!chosen) return;
      close();
      lastSent = '';
      lastAttempt = 0;
      if (chosen === '__NT__') {
        GM_setValue(CLUB_NAME, '');
        GM_setValue(CLUB_PAUSED, true);
        GM_setValue(LAST_STATUS, 'New Zealand (NT) : aucune offre synchronisée.');
        alert('New Zealand (NT) exclue. Choisis un autre club pour reprendre.');
        return;
      }
      const club = validClub(chosen);
      if (!MANAGED_CLUBS.includes(club)) return;
      GM_setValue(CLUB_PAUSED, false);
      GM_setValue(CLUB_NAME, club);
      GM_setValue(LAST_STATUS, 'Club actif : '+club+' (choisi dans la liste).');
      sync(true);
    });

    buttons.append(cancel, confirm);
    card.append(heading, description, select, note, buttons);
    overlay.appendChild(card);
    document.body.appendChild(overlay);
    select.focus();
  }
  GM_registerMenuCommand('FMP : choisir le club actif (liste)', chooseClubFromList);
  GM_registerMenuCommand('FMP : envoyer les offres maintenant', () => sync(true));
  GM_registerMenuCommand('FMP : état de la dernière synchronisation', () => alert(GM_getValue(LAST_STATUS, 'Aucune synchronisation.')));
  GM_registerMenuCommand('FMP : club sélectionné', () => {
    alert('Club détecté ou sélectionné : '+(GM_getValue(CLUB_PAUSED, false) ? 'New Zealand (NT) — ignorée' : currentClub() || 'aucun')+'\n'
      +'Change le club dans ce menu si FMP ne peut pas le détecter automatiquement.');
  });
  GM_registerMenuCommand('FMP : dissocier ce navigateur', () => {
    GM_setValue(TOKEN_NAME, ''); GM_setValue(CLUB_NAME, ''); GM_setValue(CLUB_PAUSED, false); lastSent = ''; GM_setValue(LAST_STATUS, 'Navigateur dissocié.');
  });
  if (document.body) {
    const observer = new MutationObserver(schedule);
    observer.observe(document.body, { subtree: true, childList: true, characterData: true });
  }
  setInterval(() => sync(), 13000);
  schedule();

  // Safe pure-function test hooks; never sent to or attached to FMP page objects.
  if (typeof module !== 'undefined' && module.exports) module.exports = { parseRowCells, money, deadline, playerName, validClub, detectedClub };
})();