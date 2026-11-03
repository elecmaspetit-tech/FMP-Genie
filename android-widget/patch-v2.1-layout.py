from pathlib import Path

p = Path('app/src/main/java/com/fmp/widget/MainActivity.java')
s = p.read_text()
s = s.replace('    private int section=0;\n', '    private int section=0;\n    private boolean settingsOpen=false;\n')
needle='''        section=Math.max(0,Math.min(3,intent.getIntExtra(EXTRA_SECTION,section)));
        drawScreen();'''
assert needle in s
s=s.replace(needle,'''        section=Math.max(0,Math.min(3,intent.getIntExtra(EXTRA_SECTION,section)));
        settingsOpen=false;
        drawScreen();''')
anchor='    private int dp(int n)'
assert anchor in s
s=s.replace(anchor,'''    @Override public void onBackPressed() {
        if(settingsOpen){settingsOpen=false;drawScreen();}
        else super.onBackPressed();
    }
    private void showSettings(){settingsOpen=true;drawScreen();}
    private void showHome(){settingsOpen=false;drawScreen();}
    private void sectionHeading(LinearLayout page,String heading){
        TextView label=text(heading,16,LIGHT,true);
        label.setPadding(0,dp(19),0,dp(7));page.addView(label);
    }
    private void sectionNote(LinearLayout page,String note){
        TextView label=text(note,12,0xFFB9CFB2,false);
        label.setPadding(dp(2),dp(2),dp(2),dp(11));page.addView(label);
    }
    private void settingsAction(LinearLayout page,String name,Runnable action){
        Button button=button(name,action);
        LinearLayout.LayoutParams layout=new LinearLayout.LayoutParams(-1,dp(47));
        layout.bottomMargin=dp(5);page.addView(button,layout);
    }
'''+anchor)
a=s.index('    private void drawScreen() {')
b=s.index('    private void addEntry(',a)
replacement='''    private void drawScreen() {
        timeLines.clear();
        root=vertical();root.setBackgroundColor(DARK);
        setContentView(root);
        ScrollView scroll=new ScrollView(this);
        scroll.setFillViewport(true);
        root.addView(scroll,new LinearLayout.LayoutParams(-1,-1));
        LinearLayout page=vertical();page.setPadding(dp(15),dp(15),dp(15),dp(22));
        scroll.addView(page);
        LinearLayout toolbar=horizontal();page.addView(toolbar);
        TextView title=text(settingsOpen?"FMP  ·  PARAMÈTRES":"FMP  ·  TRANSFERTS",22,LIGHT,true);
        toolbar.addView(title,new LinearLayout.LayoutParams(0,-2,1));
        Button navigate=button(settingsOpen?"← Retour":"⚙",settingsOpen?this::showHome:this::showSettings);
        navigate.setContentDescription(settingsOpen?"Retour aux transferts":"Ouvrir les paramètres");
        navigate.setTextSize(settingsOpen?13:23);
        navigate.setTextColor(LIGHT);
        navigate.setBackgroundTintList(ColorStateList.valueOf(0xFF31552B));
        toolbar.addView(navigate,new LinearLayout.LayoutParams(dp(settingsOpen?85:52),dp(46)));
        if(settingsOpen)drawSettings(page);else drawTransfers(page);
    }
    private void drawTransfers(LinearLayout page) {
        long last=TransferStore.lastCapture(this);
        String lastText=last==0?"Aucune lecture enregistrée":
            "MAJ "+DateFormat.getDateTimeInstance(DateFormat.SHORT,DateFormat.SHORT).format(new Date(last));
        TextView status=text(lastText,11,0xFFBDD6AF,false);
        status.setPadding(dp(2),dp(2),0,dp(12));page.addView(status);
        LinearLayout bar=horizontal();page.addView(bar);
        for(int i=0;i<4;i++){
            final int n=i;
            Button tab=button(new String[]{"Favoris","Reçues","Mes offres","Attente"}[i],()->{section=n;drawScreen();});
            tab.setPadding(dp(2),0,dp(2),0);
            tab.setTextColor(i==section?DARK:LIGHT);
            tab.setBackgroundTintList(ColorStateList.valueOf(i==section?GREEN:0xFF31552B));
            LinearLayout.LayoutParams params=new LinearLayout.LayoutParams(0,dp(46),1);
            params.setMargins(dp(2),0,dp(2),0);bar.addView(tab,params);
        }
        LinearLayout listTitle=horizontal();
        LinearLayout.LayoutParams tp=new LinearLayout.LayoutParams(-1,-2);
        tp.topMargin=dp(17);tp.bottomMargin=dp(6);page.addView(listTitle,tp);
        TextView label=text(VisibleTransfersParser.SECTIONS[section],19,LIGHT,true);
        listTitle.addView(label,new LinearLayout.LayoutParams(0,-2,1));
        Button add=button("+",()->showEdit(null));
        add.setContentDescription("Ajouter un joueur manuellement");
        add.setTextSize(20);
        add.setBackgroundTintList(ColorStateList.valueOf(0xFF31552B));
        add.setTextColor(LIGHT);
        listTitle.addView(add,new LinearLayout.LayoutParams(dp(52),dp(43)));
        entries=vertical();page.addView(entries);
        List<TransferStore.Entry> all=TransferStore.all(this);
        int count=0;
        for(TransferStore.Entry entry:all)if(entry.section==section){addEntry(entry);count++;}
        if(count==0){
            LinearLayout emptyBox=vertical();
            emptyBox.setBackgroundColor(0xFF17420E);
            emptyBox.setPadding(dp(15),dp(24),dp(15),dp(24));
            TextView empty=text("Aucun transfert dans cette catégorie",15,LIGHT,true);
            emptyBox.addView(empty);
            TextView hint=text("Ouvre FMP dans Firefox ou l'application et active la liaison depuis ⚙ Paramètres.",12,0xFFBFD3B6,false);
            hint.setPadding(0,dp(7),0,0);emptyBox.addView(hint);
            entries.addView(emptyBox);
        }
        TextView source=text("Source et compte à rebours indiqués sur chaque fiche · échéances estimées",11,0xFFA5BE9D,false);
        source.setPadding(dp(3),dp(13),0,0);page.addView(source);
    }
    private void drawSettings(LinearLayout page) {
        sectionNote(page,"Configuration du widget et des sources de transferts. Les relevés restent visibles dans l'accueil.");
        sectionHeading(page,"Widget Samsung");
        AppWidgetManager widgetManager=AppWidgetManager.getInstance(this);
        int count=widgetManager.getAppWidgetIds(new ComponentName(this,FavoritesWidget.class)).length;
        sectionNote(page,count>0?"Widgets actifs sur l'accueil : "+count:
            "Aucun widget placé sur l'écran d'accueil");
        settingsAction(page,"Ajouter le widget à l'accueil",this::requestWidgetPin);
        settingsAction(page,"Aide à l'installation Samsung",this::showWidgetHelp);
        sectionHeading(page,"Lecture de l'application FMP (OCR)");
        sectionNote(page,"Partage d'écran volontaire. Le moteur OCR officiel déjà validé est conservé.");
        settingsAction(page,"Démarrer la lecture FMP",this::startCaptureSession);
        settingsAction(page,"Arrêter le partage d'écran",this::stopCaptureSession);
        sectionHeading(page,"Firefox · Liaison HTML locale");
        sectionNote(page,FmpLocalBridgeService.isActive()?"Pont local actif · 127.0.0.1":"Pont local arrêté");
        settingsAction(page,"Activer le pont Firefox",this::startFirefoxBridge);
        settingsAction(page,"Copier la clé privée de liaison",this::copyFirefoxBridgeKey);
        settingsAction(page,"Arrêter le pont Firefox",this::stopFirefoxBridge);
        sectionNote(page,"Installer le script FMP Direct Bridge dans Violentmonkey, puis coller la clé depuis son menu. Aucune connexion bancaire ni identifiant FMP demandé.");
        sectionHeading(page,"Diagnostic et entretien");
        settingsAction(page,"Voir le diagnostic OCR local",this::showOcrDiagnostic);
        settingsAction(page,"Effacer les anciens relevés importés",this::confirmClearCaptured);
        sectionHeading(page,"Accès et confidentialité");
        settingsAction(page,"Ouvrir l'application FMP",this::openFmp);
        sectionNote(page,"Firefox : analyse HTML et transfert local protégé par clé. FMP officiel : OCR avec autorisation. Aucune enchère envoyée par notre application.");
    }
'''
s=s[:a]+replacement+s[b:]
p.write_text(s)
print('UI V2.1: home and settings separated')