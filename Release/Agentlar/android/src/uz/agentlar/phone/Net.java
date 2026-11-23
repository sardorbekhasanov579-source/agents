package uz.agentlar.phone;
import java.net.*;import java.io.*;import javax.net.ssl.HttpsURLConnection;import org.json.*;
final class Net {
 static String normalize(String raw) throws Exception {
  URI u=new URI(raw.trim());
  if(!"https".equals(u.getScheme())||u.getHost()==null||u.getUserInfo()!=null||u.getQuery()!=null||u.getFragment()!=null||(!u.getPath().isEmpty()&&!u.getPath().equals("/")))throw new Exception("Faqat HTTPS asosiy manzil kerak");
  return raw.trim().replaceAll("/+$", "");
 }
 static JSONObject post(String root,String route,String token,JSONObject data)throws Exception {
  HttpsURLConnection c=(HttpsURLConnection)new URL(normalize(root)+route).openConnection();
  c.setInstanceFollowRedirects(false);c.setConnectTimeout(15000);c.setReadTimeout(20000);c.setRequestMethod("POST");c.setDoOutput(true);c.setRequestProperty("Content-Type","application/json");
  if(!token.isEmpty())c.setRequestProperty("Authorization","Bearer "+token);
  byte[] out=data.toString().getBytes("UTF-8");c.setFixedLengthStreamingMode(out.length);
  try{
   try(OutputStream s=c.getOutputStream()){s.write(out);}
   int status=c.getResponseCode();if(status!=200)throw new Exception("Server javobi "+status+". /phonepair bilan qayta ulash kerak bo‘lishi mumkin.");
   ByteArrayOutputStream bytes=new ByteArrayOutputStream();try(InputStream s=c.getInputStream()){byte[] b=new byte[8192];int n;while((n=s.read(b))!=-1){if(bytes.size()+n>6*1024*1024)throw new Exception("Javob hajmi limiti");bytes.write(b,0,n);}}
   return new JSONObject(bytes.toString("UTF-8"));
  }finally{c.disconnect();}
 }
}
