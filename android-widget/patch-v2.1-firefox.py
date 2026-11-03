from pathlib import Path
p=Path('firefox/FMP_Direct_Bridge_V2_0.user.js')
s=p.read_text()
s=s.replace('// @version      2.0.0','// @version      2.1.0')
s=s.replace('const BADGES = /\\bNON\\s+PERTINENT\\b|\\bRISQU[EÉ]\\s*\\/?\\s*PETIT\\s+GAIN\\b|\\bFMP\\s+Squad\\s+Advisor\\b/gi;',
'''// The badges may be glued directly to a name by textContent (FocquetNON).
  const BADGES = /\\s*NON\\s*PERTINENT\\b|\\s*RISQU[EÉ]\\s*\\/?\\s*PETIT\\s+GAIN\\b|\\s*FMP\\s+Squad\\s+Advisor\\b/gi;''')
old='''    copy.querySelectorAll('script,style,button,input,select,textarea,[class*="squad-advisor" i], [id*="squad-advisor" i], [data-fmp-advisor]').forEach(n => n.remove());
    return plain(copy.textContent || '');'''
new='''    copy.querySelectorAll('script,style,button,input,select,textarea,[class*="squad-advisor" i], [id*="squad-advisor" i], [data-fmp-advisor]').forEach(n => n.remove());
    // Remove only badge-specific elements, never the enclosing player cell.
    for (const el of Array.from(copy.querySelectorAll('*')).reverse()) {
      const t = normalize(el.textContent || '');
      if (/^(?:non pertinent|non|pertinent|risque\\s*\\/?\\s*petit gain|risque|petit gain|fmp squad advisor)$/.test(t)) el.remove();
    }
    return plain(copy.textContent || '');'''
assert old in s
s=s.replace(old,new)
old='''    let t = plain(raw).replace(/[\\u{1F1E6}-\\u{1F1FF}]/gu, '').replace(/\\b(?:NON|PERTINENT|RISQU[EÉ]|PETIT|GAIN)\\b/gi, ' ').trim();
    t = t.replace(/\\s+/g, ' ').replace(/^[^\\p{L}]+/u, '');'''
new='''    let t = plain(raw).replace(/[\\u{1F1E6}-\\u{1F1FF}]/gu, '').trim();
    // Partial badges must never become parts of footballers' surnames.
    t = t.replace(/([a-zà-ÿ])NON$/u, '$1')
      .replace(/([a-zà-ÿ])RISQU[EÉ]$/u, '$1')
      .replace(/\\b(?:NON|PERTINENT|RISQU[EÉ]|PETIT|GAIN)\\b/gi, ' ');
    t = t.replace(/\\s+/g, ' ').replace(/^[^\\p{L}]+/u, '').trim();'''
assert old in s
s=s.replace(old,new)
old='''    const end = deadline(values[indices.end] || '');
    if (!amount && !end) return null;
    return { section, name, offer: amount, deadline: end };'''
new='''    const end = deadline(values[indices.end] || '');
    // In Firefox, Squad Advisor may cover the bid and expiry of an otherwise
    // valid player row. An age column confirms this is a player, not a badge.
    const age = String(values[indices.age] || '').trim();
    const corroborated = /^(?:1[6-9]|[2-4][0-9])(?:\\d{2})?$/.test(age);
    if (!amount && !end && !corroborated) return null;
    return { section, name, offer: amount, deadline: end };'''
assert old in s
s=s.replace(old,new)
old='''      name: col(labels, [/^nom$/, /^name$/], 1),
      offer: col(labels, [/^offre$/, /^bid$/, /^offer$/], 6),'''
new='''      name: col(labels, [/^nom$/, /^name$/], 1),
      age: col(labels, [/^age$/, /^âge$/], 2),
      offer: col(labels, [/^offre$/, /^bid$/, /^offer$/], 6),'''
assert old in s
s=s.replace(old,new)
# New user script path but leave old for traceability
p2=Path('firefox/FMP_Direct_Bridge_V2_1.user.js')
p2.write_text(s)
q=Path('tests/test_userscript.js')
t=q.read_text().replace("firefox/FMP_Direct_Bridge_V2_0.user.js","firefox/FMP_Direct_Bridge_V2_1.user.js")
t=t.replace("FMP_Direct_Bridge_V2_0.user.js'","FMP_Direct_Bridge_V2_1.user.js'")
t=t.replace("assert.strictEqual(f.playerName('NON PERTINENT'),'');", """assert.strictEqual(f.playerName('NON PERTINENT'),'');
assert.strictEqual(f.playerName('Axel FocquetNON'),'Axel Focquet');
assert.strictEqual(f.playerName('Axel FocquetNON PERTINENT'),'Axel Focquet');
assert.strictEqual(f.playerName('Hichem Becker RISQUÉ / PETIT GAIN'),'Hichem Becker');
assert.strictEqual(f.playerName('Hichem BeckerRISQUÉ'),'Hichem Becker');""")
t=t.replace("const result=f.parseRowCells(columns,0,{name:1,offer:6,end:7});", "const result=f.parseRowCells(columns,0,{name:1,age:2,offer:6,end:7});")
t=t.replace("{name:1,offer:6,end:7}),null);", "{name:1,age:2,offer:6,end:7}),null);")
t=t.replace("assert(Object.keys(commands).length>=3);", """const second=f.parseRowCells(['i','Hichem Becker','37','DG','4.5','23.050','',''],0,{name:1,age:2,offer:6,end:7});
assert.strictEqual(second.name,'Hichem Becker');
assert.strictEqual(second.offer,'');
assert.strictEqual(second.deadline,'');
assert.strictEqual(f.parseRowCells(['i','FMP Squad Advisor','','','','','',''],0,{name:1,age:2,offer:6,end:7}),null);
assert(Object.keys(commands).length>=3);""")
q.write_text(t)
print('V2.1 DOM badge filters and partial bid recovery applied')