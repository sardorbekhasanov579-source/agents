package uz.sardor.zaxira;

import android.app.Activity;
import android.content.*;
import android.database.Cursor;
import android.graphics.Color;
import android.graphics.Typeface;
import android.net.Uri;
import android.os.Bundle;
import android.provider.OpenableColumns;
import android.text.InputType;
import android.view.View;
import android.widget.*;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.*;
import org.json.JSONObject;

public class Home extends Activity {
    private SharedPreferences prefs;
    private EditText endpoint,code;
    private TextView status,receipt;
    private Button connect,upload,forget;
    private LinearLayout page,settings;
    private boolean busy;
    private final ExecutorService io=Executors.newSingleThreadExecutor();
    private static final int PICK=802;
    private static final int INK=Color.rgb(27,48,57),ACCENT=Color.rgb(12,92,81);

    private int dp(int n){ return (int)(getResources().getDisplayMetrics().density*n+0.5f); }
    private TextView label(LinearLayout parent,String content,int sp,boolean bold) {
        TextView label=new TextView(this);
        label.setText(content); label.setTextColor(INK); label.setTextSize(sp);
        if(bold) label.setTypeface(Typeface.DEFAULT,Typeface.BOLD);
        label.setPadding(0,dp(6),0,dp(5)); parent.addView(label); return label;
    }
    private Button button(LinearLayout parent,String text,View.OnClickListener action) {
        Button b=new Button(this); b.setText(text); b.setAllCaps(false);
        b.setOnClickListener(action);parent.addView(b);return b;
    }
    private EditText field(LinearLayout parent,String hint){
        EditText e=new EditText(this);e.setSingleLine(true);e.setHint(hint);e.setTextSize(16);
        parent.addView(e);return e;
    }
    @Override public void onCreate(Bundle state){
        super.onCreate(state);
        prefs=getSharedPreferences("vault",MODE_PRIVATE);
        ScrollView scroll=new ScrollView(this);scroll.setFillViewport(true);
        page=new LinearLayout(this);page.setOrientation(1);page.setPadding(dp(22),dp(24),dp(22),dp(22));
        scroll.addView(page);setContentView(scroll);
        label(page,"Shaxsiy zaxira",30,true);
        status=label(page,"",16,false);status.setAccessibilityLiveRegion(View.ACCESSIBILITY_LIVE_REGION_POLITE);
        settings=new LinearLayout(this);settings.setOrientation(1);page.addView(settings);
        label(settings,"Kompyuterga ulash",20,true);
        label(settings,"9_ZAXIRA_INTERNET oynasidagi manzilni va bot bergan /zpair kodini kiriting.",15,false);
        endpoint=field(settings,"https://…trycloudflare.com");endpoint.setInputType(InputType.TYPE_CLASS_TEXT|InputType.TYPE_TEXT_VARIATION_URI);
        endpoint.setText(prefs.getString("root",""));
        code=field(settings,"Bir martalik kod");code.setInputType(InputType.TYPE_CLASS_TEXT|InputType.TYPE_TEXT_VARIATION_PASSWORD);
        connect=button(settings,"Biriktirish",v->pair());
        label(page,"Hujjatlaringiz",20,true);
        label(page,"Tanlangan faylning nusxasi kompyuteringizda saqlanadi. Bir fayl 10 MiB gacha.",15,false);
        upload=button(page,"Hujjat tanlash va zaxiralash",v->{
            Intent pick=new Intent(Intent.ACTION_OPEN_DOCUMENT).setType("*/*").addCategory(Intent.CATEGORY_OPENABLE);
            try{ startActivityForResult(pick,PICK); }catch(android.content.ActivityNotFoundException e){status.setText("Qurilmada fayl tanlash dasturi topilmadi.");}
        });
        upload.setTextColor(Color.WHITE);upload.setBackgroundTintList(android.content.res.ColorStateList.valueOf(ACCENT));
        receipt=label(page,prefs.getString("receipt","Hali hujjat saqlanmagan."),15,false);
        forget=button(page,"Ulanishni uzish",v->{
            prefs.edit().remove("token").remove("root").remove("receipt").apply();receipt.setText("Ulanish uzildi.");endpoint.setText("");refresh();
        });
        refresh();
    }
    private void refresh(){
        boolean paired=prefs.contains("token");
        settings.setVisibility(paired?View.GONE:View.VISIBLE);
        forget.setVisibility(paired?View.VISIBLE:View.GONE);
        forget.setEnabled(!busy);connect.setEnabled(!busy);upload.setEnabled(paired&&!busy);
        status.setText(busy?"Bajarilmoqda…":paired?"Telefon biriktirilgan.":"Telefonni biriktiring.");
    }
    private interface Action {String run() throws Exception;}
    private void runTask(Action task,boolean isUpload){
        if(busy)return;
        busy=true;refresh();
        io.execute(()->{
            try {
                String message=task.run();
                runOnUiThread(()->{
                    if(isDestroyed())return;
                    busy=false;refresh();
                    if(isUpload)receipt.setText(message);else code.setText("");
                    status.setText(isUpload?"Server saqlanganini tasdiqladi.":"Telefon biriktirildi.");
                });
            }catch(Exception failure){
                runOnUiThread(()->{
                    if(isDestroyed())return;
                    busy=false;refresh();
                    status.setText("Yakunlanmadi. "+(failure.getMessage()!=null?failure.getMessage():"Internetni tekshiring."));
                });
            }
        });
    }
    private void pair(){
        final String root=endpoint.getText().toString(), key=code.getText().toString().trim();
        if(key.isEmpty()){status.setText("Telegram botiga /zpair yuboring va kodni kiriting.");return;}
        runTask(()->{
            String url=Wire.address(root);
            JSONObject reply=Wire.post(url,"/v1/pair",null,null,new JSONObject().put("code",key).toString().getBytes(StandardCharsets.UTF_8));
            String token=reply.getString("token");if(token.length()<32)throw new IOException("Ulanish javobi yaroqsiz");
            if(!prefs.edit().putString("root",url).putString("token",token).commit())throw new IOException("Sozlama saqlanmadi");
            return "";
        },false);
    }
    @Override protected void onActivityResult(int request,int result,Intent data){
        super.onActivityResult(request,result,data);
        if(request!=PICK || result!=RESULT_OK || data==null || data.getData()==null)return;
        final Uri file=data.getData();
        runTask(()->{
            String title="hujjat";
            try(Cursor c=getContentResolver().query(file,new String[]{OpenableColumns.DISPLAY_NAME,OpenableColumns.SIZE},null,null,null)){
                if(c!=null && c.moveToFirst()){
                    if(!c.isNull(0))title=c.getString(0);
                    if(!c.isNull(1) && c.getLong(1)>Wire.LIMIT)throw new IOException("10 MiB dan kichik fayl tanlang.");
                }
            }
            byte[] payload=Wire.read(getContentResolver().openInputStream(file),Wire.LIMIT);
            JSONObject reply=Wire.post(prefs.getString("root",""),"/v1/documents",prefs.getString("token",""),title,payload);
            String id=reply.getString("id");
            if(!id.matches("[a-f0-9]{16}"))throw new IOException("Server tasdig‘i kelmadi");
            String note=title+"\n"+(reply.getBoolean("created")?"Zaxiralandi":"Bu nusxa avval saqlangan")+" • "+payload.length+" bayt\nTelegramda: /zol_"+id;
            prefs.edit().putString("receipt",note).apply();return note;
        },true);
    }
    @Override protected void onDestroy(){io.shutdown();super.onDestroy();}
}
