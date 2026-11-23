package uz.agentlar.phone;
import android.app.*;import android.os.*;import android.content.*;import android.net.Uri;import android.widget.*;import android.graphics.Color;
import org.json.JSONObject;
public class MainActivity extends Activity {
 final PairGate pairGate=new PairGate();
 EditText url,code;TextView status,folder;Switch receive;android.content.SharedPreferences prefs;Handler handler=new Handler();
 Runnable refresh=new Runnable(){public void run(){status.setText(prefs.getString("status","Ulanmagan"));handler.postDelayed(this,2000);}};
 public void onCreate(Bundle b){super.onCreate(b);prefs=getSharedPreferences("phone",0);
  ScrollView scroll=new ScrollView(this);LinearLayout box=new LinearLayout(this);box.setOrientation(1);box.setPadding(30,40,30,30);scroll.addView(box);setContentView(scroll);
  TextView title=new TextView(this);title.setText("Agentlar • Telefon");title.setTextSize(27);title.setTextColor(Color.rgb(24,62,115));box.addView(title);
  TextView intro=new TextView(this);intro.setText("Shaxsiy telefoningizni Telegram agentingizga ulang. Faqat tanlangan papkadagi fayllar. Ekran, boshqa ilovalar va parollar boshqarilmaydi. Ulanish yoqilganda doimiy bildirishnoma ko‘rinadi.");box.addView(intro);
  url=new EditText(this);url.setSingleLine(true);url.setHint("https://....trycloudflare.com");url.setText(prefs.getString("url",""));box.addView(url);
  code=new EditText(this);code.setSingleLine(true);code.setHint("Telegram /phonepair kodi");box.addView(code);
  folder=new TextView(this);folder.setText(prefs.contains("tree")?"Papka tanlangan":"Papka hali tanlanmagan");box.addView(folder);
  Button choose=new Button(this);choose.setText("1. Papka tanlash");box.addView(choose);choose.setOnClickListener(v->{stopConnection();Intent i=new Intent(Intent.ACTION_OPEN_DOCUMENT_TREE);i.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION|Intent.FLAG_GRANT_WRITE_URI_PERMISSION|Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION);startActivityForResult(i,100);});
  receive=new Switch(this);receive.setText("Kompyuterdan yangi fayl nusxalarini qabul qilish");receive.setChecked(prefs.getBoolean("receive",false));box.addView(receive);receive.setOnCheckedChangeListener((v,on)->prefs.edit().putBoolean("receive",on).apply());
  Button pair=new Button(this);pair.setText("2. Kod bilan biriktirish va ulash");box.addView(pair);pair.setOnClickListener(v->pair());
  Button start=new Button(this);start.setText("Ulanishni qayta boshlash");box.addView(start);start.setOnClickListener(v->startConnection());
  Button stop=new Button(this);stop.setText("Ulanishni to‘xtatish");box.addView(stop);stop.setOnClickListener(v->stopConnection());
  status=new TextView(this);status.setPadding(0,24,0,24);box.addView(status);
  TextView help=new TextView(this);help.setText("Kompyuterda bot va 7_TELEFON_INTERNET.bat ochiq tursin. Telegram: /phone, /phonefind, /phoneget. Telefonni qayta yoqsangiz ulanishni ilovadan qayta boshlang. Android batareya cheklovi aloqani to‘xtatishi mumkin. Manzil o‘zgarsa qayta biriktiring. Fayllar TLS orqali kompyuteringizga, so‘ng Telegram chattingizga boradi.");box.addView(help);
 }
 void pair(){
  if(!prefs.contains("tree")){toast("Avval papka tanlang");return;}
  final String root=url.getText().toString(),key=code.getText().toString().trim();
  if(key.isEmpty()){toast("Telegramdan /phonepair kodini oling");return;}
  stopConnection();final long generation=pairGate.begin();status.setText("Biriktirilmoqda...");
  new Thread(()->{try{String clean=Net.normalize(root);JSONObject r=Net.post(clean,"/pair","",new JSONObject().put("code",key));final String pairedToken=r.getString("token");runOnUiThread(()->{if(!pairGate.current(generation))return;prefs.edit().putString("url",clean).putString("token",pairedToken).commit();code.setText("");startConnection();});}catch(Exception e){runOnUiThread(()->toast(e.getMessage()));}}).start();
 }
 void startConnection(){if(!prefs.contains("token")||!prefs.contains("tree")){toast("Avval papka tanlang va kod bilan biriktiring");return;}startForegroundService(new Intent(this,PhoneService.class));}
 void stopConnection(){pairGate.cancel();stopService(new Intent(this,PhoneService.class));prefs.edit().putString("status","To‘xtatilgan").apply();}
 void toast(String s){Toast.makeText(this,s,Toast.LENGTH_LONG).show();}
 protected void onActivityResult(int request,int result,Intent data){super.onActivityResult(request,result,data);if(request==100&&result==RESULT_OK&&data!=null){try{
  Uri u=data.getData();int flags=data.getFlags()&(Intent.FLAG_GRANT_READ_URI_PERMISSION|Intent.FLAG_GRANT_WRITE_URI_PERMISSION);getContentResolver().takePersistableUriPermission(u,flags);
  for(UriPermission old:getContentResolver().getPersistedUriPermissions())if(!old.getUri().equals(u))getContentResolver().releasePersistableUriPermission(old.getUri(),(old.isReadPermission()?1:0)|(old.isWritePermission()?2:0));
  prefs.edit().putString("tree",u.toString()).apply();folder.setText("Papka tanlandi");
 }catch(Exception e){toast("Papka ruxsati olinmadi");}}}
 protected void onDestroy(){pairGate.cancel();super.onDestroy();}
 protected void onResume(){super.onResume();handler.post(refresh);}protected void onPause(){handler.removeCallbacks(refresh);super.onPause();}
}
