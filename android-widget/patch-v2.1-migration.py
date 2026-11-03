from pathlib import Path
p=Path('app/build.gradle')
s=p.read_text()
assert 'versionCode 11' in s and "versionName '2.0.0'" in s
p.write_text(s.replace('versionCode 11','versionCode 12').replace("versionName '2.0.0'","versionName '2.1.0'"))
p=Path('app/src/main/java/com/fmp/widget/TransferStore.java')
s=p.read_text()
needle='''    public static synchronized void mergeDirect(Context ctx,List<VisibleTransfersParser.Transfer> captured) {
        if(captured==null||captured.isEmpty())return;
        List<Entry> rows=all(ctx);
        long now=System.currentTimeMillis();
        for(VisibleTransfersParser.Transfer r:captured) {
            boolean replaced=false;'''
replacement='''    public static synchronized void mergeDirect(Context ctx,List<VisibleTransfersParser.Transfer> captured) {
        if(captured==null||captured.isEmpty())return;
        List<Entry> rows=all(ctx);
        long now=System.currentTimeMillis();
        for(VisibleTransfersParser.Transfer r:captured) {
            // V2.0 could import "Axel FocquetNON" from an Advisor badge.
            // Remove only corrupted Firefox imports when a clean row is re-read.
            // Native OCR and manually entered players are never touched.
            rows.removeIf(old -> old.section==r.section
                && "FMP Firefox (HTML)".equals(old.source)
                && (old.name.equalsIgnoreCase(r.name+"NON")
                    || old.name.equalsIgnoreCase(r.name+"PERTINENT")
                    || old.name.equalsIgnoreCase(r.name+"NON PERTINENT")));
            boolean replaced=false;'''
assert needle in s
p.write_text(s.replace(needle,replacement))
Path('README_FR.md').write_text('''FMP Mes Transferts V2.1 – interface simplifiee et correction Firefox DOM.\n\nAccueil : 4 onglets, cartes joueurs, chronometres et statut court.\nParametres : widget Samsung, lecture OCR FMP, liaison Firefox, nettoyage, diagnostic et acces jeu.\nFirefox : nettoyage des badges Squad Advisor, prise en compte des lignes dont le montant est masque mais dont le nom et l age sont connus.\nAnciennes fiches Firefox collee a NON purgees uniquement a la lecture de la bonne fiche.\nOCR APK FMP et chronometres conserves. Aucune enchere automatique.\n''')
print('V2.1 build version + prior contaminated Firefox row cleanup applied')