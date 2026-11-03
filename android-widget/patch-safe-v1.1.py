from pathlib import Path
import re
p = Path('build-fmp-widget')
src = p / 'app/src/main'
manifest = src / 'AndroidManifest.xml'
s = manifest.read_text()
s, n = re.subn(r'\s*<service android:name="\.FmpReaderService"[\s\S]*?</service>', '', s)
assert n == 1, 'Old accessibility service not found'
manifest.write_text(s)
(src / 'java/com/fmp/widget/FmpReaderService.java').unlink()
(src / 'res/xml/fmp_accessibility.xml').unlink()

def change(file, old, new):
    s = file.read_text()
    assert old in s, f'Expected text not found in {file}: {old[:80]}'
    file.write_text(s.replace(old,new))
main = src / 'java/com/fmp/widget/MainActivity.java'
change(main, 'import android.provider.Settings;\n', '')
change(main, 'Widget Android indépendant • offres de FMP lues avec votre autorisation', 'Widget Android indépendant • suivi manuel des transferts')
change(main, '''        long ts=TransferStore.lastCapture(this);
        TextView status=text(ts==0 ? "Lecture FMP : pas encore effectuée" :
            "Dernière lecture : "+DateFormat.getDateTimeInstance(DateFormat.SHORT,DateFormat.SHORT).format(new Date(ts)),12,0xFFBDD6AF,false);''', '''        TextView status=text("Données locales • suivi manuel",12,0xFFBDD6AF,false);''')
change(main, '''        LinearLayout actions=horizontal();page.addView(actions);
        Button open=button("Ouvrir FMP",this::openFmp);
        Button perms=button("Activer lecture FMP",()->startActivity(new Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS)));
        actions.addView(open,new LinearLayout.LayoutParams(0,dp(52),1));
        actions.addView(perms,new LinearLayout.LayoutParams(0,dp(52),1.3f));''', '''        Button open=button("Ouvrir FMP",this::openFmp);
        page.addView(open,new LinearLayout.LayoutParams(-1,dp(52)));''')
change(main, 'Pour actualiser : autorisez le service « Lecture volontaire des transferts FMP », puis ouvrez dans FMP la page « Offres concernant Votre Équipe ». Faites défiler jusqu\'à vos favoris. La lecture ne fonctionne que si FMP expose ses textes à Android.', 'Ajoutez vos favoris et leurs montants avec « + Ajouter ». Les données sont saisies manuellement et ne se synchronisent pas avec le jeu. Les enchères sont à confirmer dans FMP.')
change(main, 'Aucun joueur reconnu dans cette catégorie.\\nActivez la lecture, ouvrez la page des transferts dans FMP ou ajoutez un favori manuellement.', 'Aucun joueur enregistré.\\nAppuyez sur « + Ajouter » pour commencer votre suivi manuel.')
change(main, '''        Button diagnostic=button("Diagnostic de lecture FMP",this::showDiagnostic);
        LinearLayout.LayoutParams dp=new LinearLayout.LayoutParams(-1,dp(50));dp.topMargin=dp(20);page.addView(diagnostic,dp);
''', '')
s=main.read_text(); a=s.index('    private void showDiagnostic(){'); b=s.index('    private void openFmp() {',a);main.write_text(s[:a]+s[b:])
change(main, "Confidentialité : stockage local uniquement. Aucun identifiant FMP n'est demandé. Aucune enchère n'est envoyée depuis ce widget. Les montants proposés ici sont des brouillons à confirmer dans FMP.", "Confidentialité : aucune permission d'accessibilité ni connexion réseau. Suivi manuel local. Aucune enchère n'est envoyée depuis ce widget.")
widget=src/'java/com/fmp/widget/FavoritesWidget.java'
change(widget, '''        long last=TransferStore.lastCapture(ctx);
        String stamp=last==0?"non synchronisé":DateFormat.getDateTimeInstance(DateFormat.SHORT,DateFormat.SHORT).format(new Date(last));
        rv.setTextViewText(R.id.status,rows.size()+" joueurs • "+(page+1)+"/"+pages+" • Lecture "+stamp);''','''        rv.setTextViewText(R.id.status,rows.size()+" joueurs • "+(page+1)+"/"+pages+" • suivi manuel");''')
gradle=p/'app/build.gradle'
change(gradle, 'versionCode 1','versionCode 2')
change(gradle, "versionName '1.0.0'", "versionName '1.1.0'")
check=p/'tests/check_project.py'
if check.exists():
    change(check, "assert 'BIND_ACCESSIBILITY_SERVICE' in manifest", "assert 'BIND_ACCESSIBILITY_SERVICE' not in manifest")
    change(check, "'FmpReaderService',", '')
    change(check, '''assert '<service' in manifest and 'canRetrieveWindowContent="true"' in (root/'app/src/main/res/xml/fmp_accessibility.xml').read_text()''', "assert '<service' not in manifest and 'android.permission.' not in manifest")
assert 'accessibility' not in manifest.read_text().lower()
print('FMP safe V1.1 patched')
