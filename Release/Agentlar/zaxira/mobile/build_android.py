"""Reproducible local native APK build; JDK and Android SDK required."""
import argparse,os,shutil,subprocess,tempfile,zipfile
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--sdk',default=os.environ.get('ANDROID_HOME',str(Path.home()/'AppData/Local/Android/Sdk')));p.add_argument('--key');p.add_argument('--ecj');a=p.parse_args()
base=Path(__file__).resolve().parent;sdk=Path(a.sdk);bt=sdk/'build-tools'/'34.0.0';android=sdk/'platforms'/'android-30'/'android.jar';suffix='.exe' if os.name=='nt' else ''
if not android.exists() or not bt.exists():raise SystemExit('SDK Manager orqali Android SDK Platform 30 va Build-Tools 34.0.0 ni o‘rnating.')
key=Path(a.key) if a.key else base/'private-signing.jks'
def run(args):subprocess.run([str(x) for x in args],check=True)
with tempfile.TemporaryDirectory() as tmp:
 tmp=Path(tmp);classes=tmp/'classes';classes.mkdir();dex=tmp/'dex';dex.mkdir()
 sources=sorted((base/'src').rglob('*.java'))
 compiler=['java','-jar',a.ecj,'-8','-proc:none'] if a.ecj else ['javac','-source','8','-target','8']
 run([*compiler,'-classpath',android,'-d',classes,*sources])
 jar=tmp/'classes.jar'
 with zipfile.ZipFile(jar,'w') as z:
  for f in classes.rglob('*.class'):z.write(f,f.relative_to(classes))
 run(['java','-cp',bt/'lib'/'d8.jar','com.android.tools.r8.D8','--lib',android,'--min-api','26','--output',dex,jar])
 unsigned=tmp/'unsigned.apk';aligned=tmp/'aligned.apk'
 run([bt/('aapt'+suffix),'package','-f','-M',base/'AndroidManifest.xml','-I',android,'-F',unsigned])
 with zipfile.ZipFile(unsigned,'a') as z:z.write(dex/'classes.dex','classes.dex')
 run([bt/('zipalign'+suffix),'-f','4',unsigned,aligned])
 if not key.exists():run(['keytool','-genkeypair','-keystore',key,'-storepass','android','-keypass','android','-alias','androiddebugkey','-dname','CN=Zaxira Development,O=Personal,C=UZ','-keyalg','RSA','-keysize','2048','-validity','10000'])
 out=base.parent.parent/'Shaxsiy_Zaxira_0_1.apk'
 run(['java','-jar',bt/'lib'/'apksigner.jar','sign','--ks',key,'--ks-pass','pass:android','--key-pass','pass:android','--out',out,aligned])
 run(['java','-jar',bt/'lib'/'apksigner.jar','verify','--verbose',out]);print('APK:',out)
