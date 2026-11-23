package uz.agentlar.phone;
import android.app.*;import android.os.*;import android.content.*;import android.net.Uri;import android.database.Cursor;import android.provider.DocumentsContract;import android.util.Base64;
import org.json.*;import java.io.*;import java.util.*;import java.security.MessageDigest;
public class PhoneService extends Service {
 volatile boolean running=false;Thread worker;android.content.SharedPreferences prefs;String root,token;int visited;Map<String,Doc> docs=new LinkedHashMap<>();
 static final int LIMIT=4*1024*1024;static class Doc{Uri uri;String name;Doc(Uri u,String n){uri=u;name=n;}}
 public IBinder onBind(Intent i){return null;}
 public void onCreate(){super.onCreate();prefs=getSharedPreferences("phone",0);NotificationManager nm=(NotificationManager)getSystemService(NOTIFICATION_SERVICE);nm.createNotificationChannel(new NotificationChannel("phone","Agentlar ulanishi",NotificationManager.IMPORTANCE_LOW));}
 public int onStartCommand(Intent i,int flags,int id){
  if(i!=null&&"STOP".equals(i.getAction())){stopSelf();return START_NOT_STICKY;}
  Intent stop=new Intent(this,PhoneService.class).setAction("STOP");PendingIntent pi=PendingIntent.getService(this,1,stop,PendingIntent.FLAG_UPDATE_CURRENT|PendingIntent.FLAG_IMMUTABLE);
  PendingIntent open=PendingIntent.getActivity(this,2,new Intent(this,MainActivity.class),PendingIntent.FLAG_UPDATE_CURRENT|PendingIntent.FLAG_IMMUTABLE);
  startForeground(1,new Notification.Builder(this,"phone").setContentTitle("Agentlar: ulanish yoqilgan").setContentText("Tanlangan papka uchun masofaviy fayl amallari").setSmallIcon(android.R.drawable.stat_notify_sync).setContentIntent(open).addAction(android.R.drawable.ic_menu_close_clear_cancel,"To‘xtatish",pi).setOngoing(true).build());
  if(!running){running=true;root=prefs.getString("url","");token=prefs.getString("token","");worker=new Thread(()->loop(),"agentlar-phone");worker.start();}
  return START_NOT_STICKY;
 }
 void state(String text){if(running)prefs.edit().putString("status",text).apply();}
 void active()throws Exception{if(!running||Thread.currentThread().isInterrupted())throw new Exception("To‘xtatildi");}
 void loop(){
  while(running){try{
   active();JSONObject info=new JSONObject();BatteryManager bm=(BatteryManager)getSystemService(BATTERY_SERVICE);info.put("battery",bm.getIntProperty(BatteryManager.BATTERY_PROPERTY_CAPACITY));info.put("device",Build.MODEL);info.put("folder",prefs.contains("tree")?"tanlangan":"yo‘q");info.put("receive",prefs.getBoolean("receive",false)?"yoqilgan":"o‘chiq");
   JSONObject reply=Net.post(root,"/poll",token,info);active();state("Ulangan • oxirgi aloqa: "+new java.text.SimpleDateFormat("HH:mm:ss",Locale.US).format(new Date()));
   JSONObject command=reply.optJSONObject("command");
   if(command!=null){String id=command.getString("id");JSONObject result;
    if(!id.matches("[a-f0-9]{24}"))throw new Exception("Buyruq ID xato");
    File cache=new File(getFilesDir(),"last-result.json");JSONObject cached=null;
    if(cache.exists()){try{cached=new JSONObject(new String(read(new FileInputStream(cache),6*1024*1024),"UTF-8"));}catch(Exception ignore){}}
    String scope=hash(token);
    if(cached!=null&&id.equals(cached.optString("id"))&&scope.equals(cached.optString("scope")))result=cached.getJSONObject("result");
    else{
     try{active();if(command.getDouble("expires")<System.currentTimeMillis()/1000.0)throw new Exception("Amal muddati o‘tgan");result=perform(command);}catch(Exception e){result=new JSONObject().put("text","Xato: "+(e.getMessage()==null?"fayl amali bajarilmadi":e.getMessage()));}
     JSONObject save=new JSONObject().put("id",id).put("scope",scope).put("result",result);File tmp=new File(getFilesDir(),"last-result.tmp");try(FileOutputStream out=new FileOutputStream(tmp)){out.write(save.toString().getBytes("UTF-8"));out.getFD().sync();}if(!tmp.renameTo(cache))throw new Exception("Natija saqlanmadi");
    }
    active();Net.post(root,"/result",token,new JSONObject().put("id",id).put("result",result));
   }
  }catch(Exception e){state("Aloqa/fayl xatosi: "+e.getMessage());}
   try{Thread.sleep(10000);}catch(InterruptedException e){break;}
  }
 }
 JSONObject perform(JSONObject cmd)throws Exception{
  String action=cmd.getString("action");Uri tree=Uri.parse(prefs.getString("tree",""));
  if(action.equals("search")||action.equals("get")){
   docs.clear();visited=0;walk(tree,DocumentsContract.getTreeDocumentId(tree),"",0,new HashSet<String>());active();
   if(action.equals("search")){
    String query=cmd.optString("query").toLowerCase(Locale.ROOT);StringBuilder text=new StringBuilder();int matches=0;
    for(Map.Entry<String,Doc> e:docs.entrySet())if(e.getValue().name.toLowerCase(Locale.ROOT).contains(query)){text.append(e.getKey()).append("  ").append(e.getValue().name).append('\n');if(++matches>=40)break;}
    if(matches==0)text.append("Topilmadi. ");text.append("\nKo‘rilgan yozuvlar: ").append(visited).append(" (limit 500; chuqurlik 10). Olish: /phoneget ID");return new JSONObject().put("text",text.toString());
   }
   Doc d=docs.get(cmd.getString("file_id"));if(d==null)throw new Exception("Fayl topilmadi; /phonefind bilan qayta qidiring");
   byte[] data=read(getContentResolver().openInputStream(d.uri),LIMIT);active();String name=d.name.substring(d.name.lastIndexOf('/')+1);return new JSONObject().put("text",name+" olindi").put("name",name).put("data",Base64.encodeToString(data,Base64.NO_WRAP));
  }
  if(action.equals("put")){
   if(!prefs.getBoolean("receive",false))throw new Exception("Ilovada fayl qabul qilishni yoqing");
   String name=cmd.getString("name").replaceAll("[^\\p{L}\\p{N}._ -]","_");if(name.length()>100)name=name.substring(0,100);if(name.isEmpty()||name.startsWith("."))name="fayl_"+name;
   byte[] data=Base64.decode(cmd.getString("data"),Base64.DEFAULT);if(data.length>LIMIT)throw new Exception("4 MiB limit");active();
   // Durable journal BEFORE creating a file. Crash retries never repeat a possibly committed write.
   String marker=hash(token)+":"+cmd.getString("id");if(marker.equals(prefs.getString("last_put","")))throw new Exception("Oldingi yozish boshlangan; nusxani papkadan tekshiring. Qayta yozilmadi.");
   if(!prefs.edit().putString("last_put",marker).commit())throw new Exception("Amal jurnali saqlanmadi");
   Uri parent=DocumentsContract.buildDocumentUriUsingTree(tree,DocumentsContract.getTreeDocumentId(tree));
   Uri dest=DocumentsContract.createDocument(getContentResolver(),parent,"application/octet-stream","Agentlar_"+cmd.getString("id").substring(0,8)+"_"+name);
   if(dest==null)throw new Exception("Fayl yaratilmadi");
   try(OutputStream out=getContentResolver().openOutputStream(dest,"w")){active();if(out==null)throw new Exception("Fayl ochilmadi");out.write(data);}
   catch(Exception e){try{DocumentsContract.deleteDocument(getContentResolver(),dest);}catch(Exception ignored){}throw e;}
   return new JSONObject().put("text","Yangi nusxa telefon papkasiga saqlandi: "+name);
  }
  throw new Exception("Noma’lum amal");
 }
 void walk(Uri tree,String parent,String prefix,int depth,Set<String> seen)throws Exception{
  active();if(depth>10||visited>=500||!seen.add(parent))return;
  Uri children=DocumentsContract.buildChildDocumentsUriUsingTree(tree,parent);
  try(Cursor c=getContentResolver().query(children,new String[]{DocumentsContract.Document.COLUMN_DOCUMENT_ID,DocumentsContract.Document.COLUMN_DISPLAY_NAME,DocumentsContract.Document.COLUMN_MIME_TYPE},null,null,null)){
   if(c==null)return;while(c.moveToNext()&&visited<500){active();visited++;String id=c.getString(0),name=c.getString(1),mime=c.getString(2);if(name==null)continue;
    if(DocumentsContract.Document.MIME_TYPE_DIR.equals(mime))walk(tree,id,prefix+name+"/",depth+1,seen);
    else docs.put(hash(id).substring(0,16),new Doc(DocumentsContract.buildDocumentUriUsingTree(tree,id),prefix+name));
   }
  }
 }
 byte[] read(InputStream s,int limit)throws Exception{
  if(s==null)throw new Exception("Fayl ochilmadi");try(InputStream in=s;ByteArrayOutputStream out=new ByteArrayOutputStream()){byte[] b=new byte[8192];int n;while((n=in.read(b))!=-1){active();if(out.size()+n>limit)throw new Exception("Fayl hajmi limiti");out.write(b,0,n);}return out.toByteArray();}
 }
 static String hash(String v)throws Exception{byte[] d=MessageDigest.getInstance("SHA-256").digest(v.getBytes("UTF-8"));StringBuilder s=new StringBuilder();for(byte b:d)s.append(String.format(Locale.ROOT,"%02x",b&255));return s.toString();}
 public void onDestroy(){running=false;if(worker!=null)worker.interrupt();prefs.edit().putString("status","To‘xtatilgan").apply();stopForeground(true);super.onDestroy();}
}
