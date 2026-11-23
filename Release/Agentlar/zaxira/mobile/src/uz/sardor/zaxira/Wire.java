package uz.sardor.zaxira;

import java.io.*;
import java.net.URI;
import java.security.MessageDigest;
import java.util.Locale;
import javax.net.ssl.HttpsURLConnection;
import org.json.JSONObject;

final class Wire {
    static final int LIMIT=10*1024*1024;

    static String address(String text) throws Exception {
        URI uri=new URI(text.trim());
        if (!"https".equalsIgnoreCase(uri.getScheme()) || uri.getHost()==null ||
            uri.getRawUserInfo()!=null || uri.getRawFragment()!=null || uri.getRawQuery()!=null ||
            !("".equals(uri.getPath()) || "/".equals(uri.getPath())))
            throw new IOException("9-oynadagi to‘liq HTTPS manzilini kiriting");
        return uri.toASCIIString().replaceAll("/+$","");
    }

    static byte[] read(InputStream stream, int maximum) throws IOException {
        if(stream==null) throw new IOException("Faylni ochib bo‘lmadi");
        try(InputStream in=stream; ByteArrayOutputStream bytes=new ByteArrayOutputStream()) {
            byte[] buffer=new byte[8192]; int count;
            while((count=in.read(buffer))!=-1) {
                if(bytes.size()+count>maximum) throw new IOException("Fayl hajmi limitdan katta");
                bytes.write(buffer,0,count);
            }
            return bytes.toByteArray();
        }
    }

    static String digest(byte[] value) throws Exception {
        StringBuilder hex=new StringBuilder();
        for(byte b: MessageDigest.getInstance("SHA-256").digest(value)) hex.append(String.format(Locale.ROOT,"%02x",b&255));
        return hex.toString();
    }

    static JSONObject post(String root,String path,String token,String fileName,byte[] data) throws Exception {
        HttpsURLConnection c=(HttpsURLConnection)new URI(address(root)+path).toURL().openConnection();
        try {
            c.setInstanceFollowRedirects(false);
            c.setConnectTimeout(12000); c.setReadTimeout(75000);
            c.setRequestMethod("POST"); c.setDoOutput(true); c.setFixedLengthStreamingMode(data.length);
            if(fileName!=null) {
                c.setRequestProperty("Authorization","Bearer "+token);
                c.setRequestProperty("X-Name",android.util.Base64.encodeToString(fileName.getBytes("UTF-8"),android.util.Base64.NO_WRAP));
                c.setRequestProperty("X-SHA256",digest(data));
                c.setRequestProperty("Content-Type","application/octet-stream");
            } else c.setRequestProperty("Content-Type","application/json");
            try(OutputStream stream=c.getOutputStream()){ stream.write(data); }
            int status=c.getResponseCode();
            if(status==403) throw new IOException("Biriktirish kodi yoki ulanish eskirgan. Ulanish bo‘lsa uzing, Telegramda /zpair yuboring.");
            if(status!=200 && status!=201) throw new IOException("Server javobi "+status+". Manzil, fayl hajmi va ombordagi joyni tekshiring.");
            return new JSONObject(new String(read(c.getInputStream(),8192),"UTF-8"));
        } finally { c.disconnect(); }
    }
}
