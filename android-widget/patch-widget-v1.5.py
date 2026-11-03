from pathlib import Path

out=Path('build-fmp-widget')
assert (out/'app/src/main/AndroidManifest.xml').exists(), 'V1.4 source not extracted'

def replace(path,old,new):
    content=path.read_text()
    assert old in content, f'Missing expected V1.4 marker in {path}: {old[:90]}'
    path.write_text(content.replace(old,new))

p=out/'app/src/main/java/com/fmp/widget/VisibleTransfersParser.java'
replace(p,'int nameX=(int)(width*.16),ageX=(int)(width*.29),offerX=(int)(width*.75),endX=(int)(width*.90);','int nameX=(int)(width*.16),ageX=(int)(width*.29),iqX=(int)(width*.60),offerX=(int)(width*.75),endX=(int)(width*.90);')
replace(p,'if(n.equals("offre")||n.equals("bid")){offerX=w.left;bodyY=Math.max(bodyY,w.bottom+2);}', 'if(n.equals("iq"))iqX=w.left;\n                if(n.equals("offre")||n.equals("bid")){offerX=w.left;bodyY=Math.max(bodyY,w.bottom+2);}')
replace(p,'int nameLeft=clamp(nameX-(int)(width*.045),0,width);','int nameLeft=clamp(nameX-(int)(width*.075),0,width);')
replace(p,'int nameRight=Math.max(nameLeft+24,clamp(ageX-(int)(width*.008),0,width));','int nameRight=Math.max(nameLeft+24,clamp(ageX+(int)(width*.005),0,width));')
replace(p,'int lineGap=clamp((int)(medianHeight*1.9),28,55);','int lineGap=clamp((int)(medianHeight*2.9),42,72);')
replace(p,'w.cy()-current.firstY>clamp(medianHeight*3,45,85)','w.cy()-current.firstY>clamp(medianHeight*3,50,83)')
replace(p,'int bottom=i+1<rows.size()?(row.lastY+rows.get(i+1).firstY)/2:row.lastY+clamp(medianHeight*3,50,88);','int bottom=i+1<rows.size()?(row.lastY+rows.get(i+1).firstY)/2:row.lastY+clamp(medianHeight*3,55,100);')
replace(p,'if(w.left>=offerX-(int)(width*.035)&&w.left<endX+(int)(width*.014)){','int priceLeft=Math.max(iqX+(int)(width*.064),offerX-(int)(width*.095));\n                    if(w.left>=priceLeft&&w.left<endX-(int)(width*.015)){')
replace(p,'if(w.left>=endX-(int)(width*.020)&&DURATION.matcher(norm(w.text)).matches())times.add(w);','if(w.left>=endX-(int)(width*.056)&&DURATION.matcher(norm(w.text).replaceAll("\\s+", "")).matches())times.add(w);')
replace(p,'int score=Math.abs(w.cy()-(row.firstY+medianHeight));','int score=Math.abs(w.cy()-row.lastY);')

p=out/'app/src/main/java/com/fmp/widget/TransferStore.java'
replace(p,'rows.set(i,new Entry(r.section,r.name,r.offer,r.deadline,old.draft,now,"FMP écran"));',
'''String offer=r.offer.isEmpty()?old.offer:r.offer;
                    String deadline=r.deadline.isEmpty()?old.deadline:r.deadline;
                    rows.set(i,new Entry(r.section,r.name,offer,deadline,old.draft,now,"FMP écran"));''')

p=out/'app/src/main/java/com/fmp/widget/FmpProjectionService.java'
replace(p,'import android.graphics.Bitmap;', '''import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.ColorMatrix;
import android.graphics.ColorMatrixColorFilter;''')
replace(p,'''            recognizer.process(InputImage.fromBitmap(screenshot,0))
                .addOnSuccessListener(text->handleRecognized(text,capturedWidth))
                .addOnFailureListener(err->android.util.Log.w("FMPProjection","Local OCR failed",err))
                .addOnCompleteListener(done->{screenshot.recycle();busy.set(false);});''',
'''            recognizer.process(InputImage.fromBitmap(screenshot,0))
                .addOnSuccessListener(text->handleRecognized(text,capturedWidth))
                .addOnFailureListener(err->android.util.Log.w("FMPProjection","Primary OCR failed",err))
                .addOnCompleteListener(done->{
                    // Second local OCR pass recovers low-contrast text on green cells.
                    Bitmap enhanced=null;
                    try {
                        enhanced=enhanceForFmp(screenshot);
                        Bitmap second=enhanced;
                        recognizer.process(InputImage.fromBitmap(second,0))
                            .addOnSuccessListener(text->handleRecognized(text,capturedWidth))
                            .addOnFailureListener(err->android.util.Log.w("FMPProjection","Contrast OCR failed",err))
                            .addOnCompleteListener(done2->{second.recycle();screenshot.recycle();busy.set(false);});
                    }catch(Exception ex){
                        if(enhanced!=null)enhanced.recycle();
                        screenshot.recycle();busy.set(false);
                    }
                });''')
replace(p,'    private static boolean isOfferHeading(String text){',
'''    private static Bitmap enhanceForFmp(Bitmap original) {
        Bitmap target=Bitmap.createBitmap(original.getWidth(),original.getHeight(),Bitmap.Config.ARGB_8888);
        Canvas canvas=new Canvas(target);
        Paint paint=new Paint(Paint.FILTER_BITMAP_FLAG);
        ColorMatrix colors=new ColorMatrix();
        colors.setSaturation(0f);
        ColorMatrix contrast=new ColorMatrix(new float[]{
            1.65f,0,0,0,-72, 0,1.65f,0,0,-72,
            0,0,1.65f,0,-72, 0,0,0,1,0
        });
        colors.postConcat(contrast);
        paint.setColorFilter(new ColorMatrixColorFilter(colors));
        canvas.drawBitmap(original,0,0,paint);
        return target;
    }
    private static boolean isOfferHeading(String text){''')
replace(p,'''        if(!offerPage)return;
        List<VisibleTransfersParser.Transfer> transfers=VisibleTransfersParser.parse(words,displayWidth);''',
'''        if(!offerPage)return;
        StringBuilder diagnostic=new StringBuilder("FMP OCR elements (positions, last read):\\n");
        for(VisibleTransfersParser.Word w:words) {
            if(diagnostic.length()>6800)break;
            diagnostic.append(w.left).append(',').append(w.top).append(": ").append(w.text).append('\\n');
        }
        TransferStore.storeDiagnostic(getApplicationContext(),diagnostic.toString());
        List<VisibleTransfersParser.Transfer> transfers=VisibleTransfersParser.parse(words,displayWidth);''')

p=out/'app/src/main/java/com/fmp/widget/MainActivity.java'
replace(p,'        Button open=button("Ouvrir FMP",this::openFmp);',
'''        Button diag=button("Voir les mots reconnus (diagnostic local)",this::showOcrDiagnostic);
        page.addView(diag,new LinearLayout.LayoutParams(-1,dp(44)));
        Button open=button("Ouvrir FMP",this::openFmp);''')
replace(p,'    private void confirmClearCaptured() {',
'''    private void showOcrDiagnostic() {
        String data=TransferStore.diagnostic(this);
        new AlertDialog.Builder(this).setTitle("Diagnostic OCR FMP")
            .setMessage("Reconnaissance locale des mots visibles. Aucune capture n'est conservée.\\n\\n"+data)
            .setPositiveButton("Fermer",null)
            .setNeutralButton("Partager le texte",(d,w)->{
                Intent send=new Intent(Intent.ACTION_SEND);
                send.setType("text/plain");
                send.putExtra(Intent.EXTRA_TEXT,data);
                startActivity(Intent.createChooser(send,"Partager les mots OCR FMP"));
            }).show();
    }
    private void confirmClearCaptured() {''')
replace(p,'Les montants et délais OCR restent à confirmer dans FMP.',
'Les montants et délais OCR restent à confirmer dans FMP. Le bouton diagnostic permet de partager uniquement les mots détectés pour corriger les erreurs.')

p=out/'app/build.gradle'
replace(p,'versionCode 5','versionCode 6')
replace(p,"versionName '1.4.0'","versionName '1.5.0'")

p=out/'tests/ParserTest.java'
fixture='''    private static void novemberFavoriteScreenshot() {
        List<VisibleTransfersParser.Word> w=new ArrayList<>();
        add(w,"Votre liste de favoris",9,828);
        add(w,"Nom",101,865);add(w,"Age",172,865);
        add(w,"IQ",429,865);add(w,"Offre",534,865);add(w,"Fin",616,865);
        add(w,"Axel",83,946);add(w,"Focquet",83,992);
        add(w,"34",176,948);add(w,"7.339",431,947);
        add(w,"2,491,547",495,995);add(w,"11h",615,942);add(w,"31m",609,991);
        add(w,"Hichem",83,1065);add(w,"Becker",83,1110);
        add(w,"37",176,1069);add(w,"23.050",429,1068);
        add(w,"2,830,533",495,1112);add(w,"1j",620,1063);add(w,"10h",620,1110);
        List<VisibleTransfersParser.Transfer> rows=VisibleTransfersParser.parse(w,709);
        eq(2,rows.size());
        eq("2,491,547",find(rows,"Axel Focquet").offer);
        eq("11h 31m",find(rows,"Axel Focquet").deadline);
        eq("2,830,533",find(rows,"Hichem Becker").offer);
        eq("1j 10h",find(rows,"Hichem Becker").deadline);
    }
'''
replace(p,'    public static void main(String[] args){',fixture+'    public static void main(String[] args){')
replace(p,'legacySanity(); screenshotRegression(); missingAgesAndUnrelatedScreen();','legacySanity(); screenshotRegression(); missingAgesAndUnrelatedScreen(); novemberFavoriteScreenshot();')

(out/'README_FR.md').write_text(
'FMP Mes Transferts V1.5 - double-pass local OCR to recover low-contrast surnames/bids; '
'price column aligned with IQ/Offre; less destructive merging; optional diagnostic '
'text only, no saved screenshots. No INTERNET permission, no automatic purchases. '
'Bids/deadlines must be confirmed in FMP.'
)
print('FMP V1.5 patch applied')
