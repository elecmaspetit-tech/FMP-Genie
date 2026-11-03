from pathlib import Path
import xml.etree.ElementTree as ET

root=Path('build-fmp-widget')
src=root/'app/src/main'
main=src/'java/com/fmp/widget/MainActivity.java'
widget=src/'java/com/fmp/widget/FavoritesWidget.java'
manifest=src/'AndroidManifest.xml'

def replace(path, before, after):
    text=path.read_text()
    assert before in text, "Missing marker in "+str(path)+": "+before[:70]
    path.write_text(text.replace(before,after))

replace(manifest, '        <receiver android:name=".FavoritesWidget"',
    '        <receiver android:name=".PinResultReceiver" android:exported="false" />\n        <receiver android:name=".FavoritesWidget"')

(src/'java/com/fmp/widget/PinResultReceiver.java').write_text("""package com.fmp.widget;

import android.appwidget.AppWidgetManager;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.util.Log;

/** Launcher callback, only fired on a successful widget placement. */
public final class PinResultReceiver extends BroadcastReceiver {
    @Override public void onReceive(Context context, Intent intent) {
        if (!"com.fmp.widget.PIN_SUCCESS".equals(intent.getAction())) return;
        int id = intent.getIntExtra(AppWidgetManager.EXTRA_APPWIDGET_ID, AppWidgetManager.INVALID_APPWIDGET_ID);
        if (id == AppWidgetManager.INVALID_APPWIDGET_ID) {
            Log.w("FMPWidget", "Pin callback without widget ID");
            return;
        }
        context.getSharedPreferences("fmp_widget_status", Context.MODE_PRIVATE)
            .edit().putLong("last_added", System.currentTimeMillis()).apply();
        FavoritesWidget.updateAll(context);
    }
}
""")

# Actual preview bitmap, not a blank gray placeholder. Rendered with Pillow on CI.
from PIL import Image,ImageDraw,ImageFont
im=Image.new('RGBA',(640,320),(0,0,0,0))
d=ImageDraw.Draw(im)
d.rounded_rectangle((5,5,635,315),radius=34,fill='#10340c',outline='#689b36',width=4)
font_dir='/usr/share/fonts/truetype/dejavu/'
bold=ImageFont.truetype(font_dir+'DejaVuSans-Bold.ttf',30)
regular=ImageFont.truetype(font_dir+'DejaVuSans.ttf',23)
small=ImageFont.truetype(font_dir+'DejaVuSans.ttf',19)
d.text((32,24),'FMP   •   FAVORIS',font=bold,fill='#f4f9eb')
d.text((32,76),'Transferts de vos joueurs favoris',font=regular,fill='#b5d29c')
d.line((30,115,608,115),fill='#365a29',width=3)
d.text((36,145),'Axel Focquet',font=regular,fill='#f8f8ef')
d.text((430,145),'2 491 547',font=regular,fill='#e3f1a2')
d.line((32,185,605,185),fill='#365a29',width=2)
d.text((36,202),'Hichem Becker',font=regular,fill='#f8f8ef')
d.text((430,202),'2 830 533',font=regular,fill='#e3f1a2')
d.text((36,276),'Ouvrir FMP',font=small,fill='#96d375')
d.text((405,276),'Tout voir / gérer',font=small,fill='#c8d7b8')
preview=src/'res/drawable-nodpi/fmp_widget_preview.png'
preview.parent.mkdir(parents=True,exist_ok=True)
im.save(preview,optimize=True)

provider=src/'res/xml/fmp_widget_info.xml'
replace(provider,'    android:initialLayout="@layout/fmp_widget"',
    '    android:initialLayout="@layout/fmp_widget"\n    android:previewImage="@drawable/fmp_widget_preview"')
replace(provider,'android:minWidth="250dp" android:minHeight="110dp"',
    'android:minWidth="220dp" android:minHeight="100dp"')
replace(provider,'android:minResizeWidth="180dp" android:minResizeHeight="110dp"',
    'android:minResizeWidth="180dp" android:minResizeHeight="100dp"')

replace(main,'import android.appwidget.AppWidgetManager;',
    'import android.appwidget.AppWidgetManager;\nimport android.app.PendingIntent;')

old="""        Button pin=button("+ Ajouter le widget à l'écran d'accueil",()->{
            AppWidgetManager widgets=AppWidgetManager.getInstance(this);
            if(widgets.isRequestPinAppWidgetSupported()) {
                boolean started=widgets.requestPinAppWidget(new ComponentName(this,FavoritesWidget.class),null,null);
                if(!started)Toast.makeText(this,"Ouvrez le menu Widgets du téléphone",Toast.LENGTH_LONG).show();
            } else Toast.makeText(this,"Appui long sur l'accueil → Widgets → FMP Mes transferts",Toast.LENGTH_LONG).show();
        });
        page.addView(pin,new LinearLayout.LayoutParams(-1,dp(48)));"""
new="""        AppWidgetManager widgetManager=AppWidgetManager.getInstance(this);
        int countWidgets=widgetManager.getAppWidgetIds(new ComponentName(this,FavoritesWidget.class)).length;
        TextView widgetStatus=text(countWidgets>0?"Widgets installés sur l’accueil : "+countWidgets:
            "Aucun widget encore placé sur l’accueil",12,0xFFC2D7B9,false);
        widgetStatus.setPadding(0,0,0,dp(6));page.addView(widgetStatus);
        Button pin=button("+ Ajouter le widget à l'écran d'accueil",this::requestWidgetPin);
        page.addView(pin,new LinearLayout.LayoutParams(-1,dp(48)));
        Button manual=button("Si l’ajout échoue : comment faire ?",this::showWidgetHelp);
        page.addView(manual,new LinearLayout.LayoutParams(-1,dp(44)));"""
replace(main,old,new)

methods="""    private void requestWidgetPin() {
        try {
            AppWidgetManager widgets=AppWidgetManager.getInstance(this);
            if(!widgets.isRequestPinAppWidgetSupported()){showWidgetHelp();return;}
            Intent callback=new Intent(this,PinResultReceiver.class).setAction("com.fmp.widget.PIN_SUCCESS");
            PendingIntent success=PendingIntent.getBroadcast(this,2001,callback,
                PendingIntent.FLAG_MUTABLE|PendingIntent.FLAG_UPDATE_CURRENT);
            boolean accepted=widgets.requestPinAppWidget(
                new ComponentName(this,FavoritesWidget.class),null,success);
            if(!accepted)showWidgetHelp();
        }catch(RuntimeException ex){
            android.util.Log.e("FMPWidget","Widget pin request failed",ex);
            showWidgetHelp();
        }
    }
    private void showWidgetHelp() {
        new AlertDialog.Builder(this)
            .setTitle("Ajouter le widget sur Samsung")
            .setMessage("1. Revenez à l’écran d’accueil.\\n"
                +"2. Maintenez un doigt sur une zone vide.\\n"
                +"3. Choisissez Widgets.\\n"
                +"4. Cherchez FMP Mes transferts.\\n"
                +"5. Sélectionnez le widget 4 × 2, puis Ajouter.\\n\\n"
                +"Libérez une zone 4 × 2 ou essayez une autre page d’accueil. "
                +"Si l’ajout échoue encore, faites une capture de l’erreur.")
            .setPositiveButton("Compris",null).show();
    }
"""
replace(main,"    private void openFmp() {",methods+"    private void openFmp() {")

replace(widget,'''    @Override public void onUpdate(Context context,AppWidgetManager m,int[] ids) {
        for (int id:ids) render(context,m,id);
    }''','''    @Override public void onUpdate(Context context,AppWidgetManager m,int[] ids) {
        for (int id:ids) render(context,m,id);
    }
    @Override public void onAppWidgetOptionsChanged(Context context,AppWidgetManager m,int id,android.os.Bundle options) {
        render(context,m,id);
    }''')

replace(root/'app/build.gradle','versionCode 2','versionCode 3')
replace(root/'app/build.gradle',"versionName '1.1.0'","versionName '1.2.0'")
checks=root/'tests/check_project.py'
if checks.exists():
    with checks.open('a') as f:
        f.write("\nassert 'android:previewImage' in (root/'app/src/main/res/xml/fmp_widget_info.xml').read_text()\n")
        f.write("assert (root/'app/src/main/res/drawable-nodpi/fmp_widget_preview.png').exists()\n")
        f.write("assert (root/'app/src/main/java/com/fmp/widget/PinResultReceiver.java').exists()\n")
root.joinpath('README_FR.md').write_text(
    "FMP Mes Transferts V1.2 - widget Android 4x2 avec apercu Samsung, "
    "callback apres ajout et instructions d'ajout manuel. "
    "Aucune synchronisation FMP ni enchere reelle. Aucune permission sensible.\n")
for file in [manifest]+list((src/'res').rglob('*.xml')):
    ET.parse(file)
assert 'BIND_ACCESSIBILITY_SERVICE' not in manifest.read_text()
assert 'android.permission.INTERNET' not in manifest.read_text()
print('Safe FMP widget V1.2 patch applied')
