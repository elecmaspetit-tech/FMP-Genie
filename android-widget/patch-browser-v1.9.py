from pathlib import Path
r=Path('build-fmp-widget')
p=r/'app/src/main/java/com/fmp/widget/VisibleTransfersParser.java'
s=p.read_text()
start=s.index('    public static boolean hasBrowserAdvisorOverlay(')
end=s.index('    public static List<Transfer> parse(',start)
replacement=r'''    private static String advisorNormalize(String text) {
        // Firefox OCR may read "RISQUÉ /" separately from "PETIT GAIN".
        return norm(text).replaceAll("[^\\p{L}\\p{N}]+"," ").replaceAll("\\s+"," ").trim();
    }
    public static boolean hasBrowserAdvisorOverlay(List<Word> words) {
        if(words==null)return false;
        for(Word w:words) {
            if(w==null)continue;
            String t=advisorNormalize(w.text);
            if(t.equals("pertinent")||t.equals("non pertinent")
                ||t.equals("risque")||t.equals("risque petit")
                ||t.equals("risque petit gain")||t.equals("petit gain")
                ||t.contains("squad advisor"))return true;
        }
        return false;
    }
    /** Never treat a Squad Advisor badge as a player, even with OCR slash noise. */
    private static boolean isAdvisorLabel(String text) {
        String t=advisorNormalize(text);
        return t.equals("non")||t.equals("pertinent")||t.equals("non pertinent")
            ||t.equals("risque")||t.equals("risque petit")
            ||t.equals("risque petit gain")||t.equals("petit")||t.equals("gain")
            ||t.equals("petit gain")||t.equals("squad")||t.equals("advisor")
            ||t.equals("squad advisor")||t.equals("fmp squad advisor");
    }
    public static boolean isBrowserGhostPlayer(String name) {
        String t=advisorNormalize(name);
        return t.equals("non pertinent")||t.equals("risque petit gain")
            ||t.equals("risque petit")||t.equals("petit gain")
            ||t.equals("squad advisor")||t.equals("fmp squad advisor");
    }
'''
s=s[:start]+replacement+s[end:]
old='''                if(!age&&offer.isEmpty()&&times.isEmpty())continue;
                times.sort(Comparator.comparingInt(Word::cy));'''
new='''                // Browser-only partial-row recovery. A floating Squad Advisor
                // panel can mask the other cells while a two-line name stays
                // visible. Never fabricate a bid or a deadline.
                boolean browserPartialName=false;
                if(browserAdvisor && row.tokens.size()==2 && count==2) {
                    Word first=row.tokens.get(0), last=row.tokens.get(1);
                    int dy=last.cy()-first.cy();
                    int maxDx=(int)(width*.115);
                    browserPartialName=dy>=17 && dy<=82
                        && Math.abs(first.left-last.left)<=maxDx
                        && first.left>=nameLeft && last.left<nameRight;
                }
                if(!age&&offer.isEmpty()&&times.isEmpty()&&!browserPartialName)continue;
                times.sort(Comparator.comparingInt(Word::cy));'''
assert old in s,'Parser evidence marker missing'
p.write_text(s.replace(old,new,1))
p=r/'app/build.gradle'
s=p.read_text()
assert "versionCode 9" in s and "versionName '1.8.0'" in s
p.write_text(s.replace('versionCode 9','versionCode 10').replace("versionName '1.8.0'","versionName '1.9.0'"))
p=r/'tests/ParserTest.java'
s=p.read_text()
insert=r'''    private static void firefoxCoveredSecondFavorite() {
        // Regression: Firefox Squad Advisor can cover age/offer/timer for Hichem.
        List<VisibleTransfersParser.Word> w=new ArrayList<>();
        add(w,"Votre liste de favoris",10,900);
        add(w,"Nom",114,947);add(w,"Age",210,947);
        add(w,"Offre",550,947);add(w,"Fin",642,947);
        add(w,"Axel",87,1018);add(w,"Focquet",86,1060);
        add(w,"34",210,1020);add(w,"2,491,547",553,1065);
        add(w,"09h",643,1020);add(w,"08m",640,1065);
        add(w,"NON",86,1100);add(w,"PERTINENT",86,1130);
        add(w,"Hichem",86,1191);add(w,"Becker",85,1239);
        add(w,"RISQUÉ /",86,1280);add(w,"PETIT",86,1315);add(w,"GAIN",86,1345);
        add(w,"FMP",412,1240);add(w,"Squad",469,1240);add(w,"Advisor",547,1240);
        List<VisibleTransfersParser.Transfer> result=VisibleTransfersParser.parse(w,709);
        eq(true,VisibleTransfersParser.hasBrowserAdvisorOverlay(w));
        eq(2,result.size());
        eq("2,491,547",find(result,"Axel Focquet").offer);
        eq("",find(result,"Hichem Becker").offer);
        eq("",find(result,"Hichem Becker").deadline);
        for(VisibleTransfersParser.Transfer t:result)
            if(VisibleTransfersParser.isBrowserGhostPlayer(t.name))
                throw new AssertionError("False browser player: "+t);
        // Native FMP remains strict when the browser overlay is absent.
        List<VisibleTransfersParser.Word> nativeWords=new ArrayList<>();
        add(nativeWords,"Votre liste de favoris",10,900);
        add(nativeWords,"Nom",114,947);add(nativeWords,"Age",210,947);
        add(nativeWords,"Offre",550,947);add(nativeWords,"Fin",642,947);
        add(nativeWords,"Hichem",86,1191);add(nativeWords,"Becker",85,1239);
        eq(false,VisibleTransfersParser.hasBrowserAdvisorOverlay(nativeWords));
        eq(0,VisibleTransfersParser.parse(nativeWords,709).size());
    }
    private static void browserBadgePunctuationAndFalseRows() {
        List<VisibleTransfersParser.Word> w=new ArrayList<>();
        add(w,"Votre liste de favoris",10,900);
        add(w,"Nom",114,947);add(w,"Age",210,947);
        add(w,"Offre",550,947);add(w,"Fin",642,947);
        add(w,"Hichem",86,1191);add(w,"Becker",85,1239);
        add(w,"RISQUÉ /",86,1280);add(w,"PETIT GAIN",86,1315);
        eq(true,VisibleTransfersParser.hasBrowserAdvisorOverlay(w));
        List<VisibleTransfersParser.Transfer> result=VisibleTransfersParser.parse(w,709);
        eq(1,result.size());
        eq("Hichem Becker",result.get(0).name);
    }
'''
needle='    public static void main(String[] args){'
assert needle in s
s=s.replace(needle,insert+needle,1)
old='nativeFmpUntouched();'
assert old in s
s=s.replace(old,'nativeFmpUntouched(); firefoxCoveredSecondFavorite(); browserBadgePunctuationAndFalseRows();',1)
p.write_text(s)
(r/'README_FR.md').write_text('FMP Mes Transferts V1.9: Firefox OCR correction for a player whose bid is concealed by Squad Advisor. Native FMP remains unchanged; no made-up amounts or timers, no new permissions.\n')
print('FMP browser-only V1.9 patch applied')
