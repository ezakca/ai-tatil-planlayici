import streamlit as st

import streamlit as st
import google.generativeai as genai

import json
import os

def harita_linki_olustur(mekan_adi, sehir):
    # Boşlukları URL formatına uygun olması için '+' işaretine çeviriyoruz
    arama_metni = f"{mekan_adi} {sehir}".replace(" ", "+")
    link = f"https://www.google.com/maps/search/?api=1&query={arama_metni}"
    return link


def arkaplan_degistir(sehir):
    # Şehir adındaki boşlukları web formatına (%20) çeviriyoruz ki bağlantı bozulmasın
    arama_kelimesi = sehir.replace(" ", "%20")

    # Ücretsiz ve API şifresi istemeyen bir servisten o şehrin harika bir görselini çekiyoruz
    # Yapay zekayı "gerçekçi 4K fotoğraf" üretmeye zorlayan yeni ve güçlü komutumuz
    url = f"https://image.pollinations.ai/prompt/Hyper%20realistic%204k%20travel%20photography%20of%20{arama_kelimesi}%20city%20skyline%20and%20landmarks,%20daylight,%20cinematic?width=1920&height=1080&nologo=true"

    # CSS hileleri ile Streamlit'in standart tasarımını manipüle ediyoruz
    arkaplan_kodu = f"""
    <style>
    .stApp {{
        background-image: url("{url}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}
    /* Fotoğraf çok parlak veya karışık olursa yazıları okumak zorlaşır. */
    /* Bu yüzden resmin üstüne şık, karanlık bir filtre (film şeridi) çekiyoruz. */
    .stApp::before {{
        content: "";
        position: absolute;
        top: 0; left: 0; width: 100%; height: 100%;
        background-color: rgba(0, 0, 0, 0.75);
    }}
    </style>
    """
    # Streamlit'e "Bu HTML/CSS koduna güven ve sayfaya uygula" diyoruz
    st.markdown(arkaplan_kodu, unsafe_allow_html=True)



# --- API AYARLARI ---
api_key = st.secrets["API_KEY"]

# Gemini'ye anahtarımızı tanıtıyoruz
genai.configure(api_key=api_key)

# Kullanacağımız yapay zeka modelini seçiyoruz
model = genai.GenerativeModel('models/gemini-2.5-flash')

# --- AŞAMA 1'DEN KALAN ARAYÜZ KODLARI ---

# Sayfa Başlığı
st.title("✈️ Yapay Zeka Destekli Rota Oluşturucu")
st.write("Hayalindeki tatili planlamak için aşağıdaki bilgileri doldur!")

# Kullanıcıdan Alınacak Girdiler
secilen_sehir = st.text_input("Gidilecek Şehir (Örn: Paris, Roma):")
gun_sayisi = st.slider("Kaç Gün Kalacaksın?", min_value=1, max_value=15, value=3)
mevsim=st.selectbox("Seyahat Dönemi:", ["Yaz", "Sonbahar", "Kış","İlkbahar"])
butce_secimi = st.selectbox("Bütçe Seviyesi:", ["Düşük", "Orta", "Yüksek", "Lüks"])
ilgi_alanlari = st.multiselect("İlgi Alanları:", ["Tarih", "Sanat", "Gece Hayatı", "Doğa", "Gastronomi"])
para_birimi = st.selectbox("Para Birimi:", ["TL", "Euro", "Dolar","yerel para birimi"])


# --- SİHİRLİ FONKSİYON: YAPAY ZEKAYA İSTEK GÖNDERME ---
def rotayi_olustur(sehir, gun, butce, ilgi_alani):
    # Gemini'ye vereceğimiz komutu (prompt) hazırlıyoruz
    prompt = f"""
            Kullanıcı {secilen_sehir} şehrine gidiyor, bütçesi {butce_secimi},{mevsim} mevsiminde seyahat edecek, {gun_sayisi} gün kalacak ve {ilgi_alanlari} ile ilgileniyor, {para_birimi} para birimini kullanıyor.
            Ona saatlik bir plan çıkar.
            ÖNEMLİ KURAL: Gider kalemlerindeki fiyatları uydurma. Tamamen gerçekçi, güncel ortalama piyasa koşullarına ve {butce_secimi} bütçe seviyesine uygun mantıklı fiyatlar ver. Para birimi olarak {para_birimi} kullan.
            Çıktıyı SADECE aşağıdaki JSON formatında ver. Başka hiçbir açıklama yazma:
            {{
              "rota": [
                {{
                  "plan": "Günün kısa özeti...",
                  "gezilecek_mekanlar": ["Mekan 1 Adı", "Mekan 2 Adı", "Restoran Adı"],
                  "gider_kalemleri": [
                    {{"kalem": "Kahve", "maliyet": "5 Euro"}}
                  ],
                  "gunluk_toplam": "50 Euro"
                }}
              ]
            }}
            """

    # API'ye isteği gönderiyoruz ve yanıtı alıyoruz
    response = model.generate_content(
        prompt,
        generation_config={"response_mime_type": "application/json"}
    )
    try:
        # Artık replace ile temizlemeye gerek yok, gelen veri garanti saf JSON!
        rota_verisi = json.loads(response.text)

        # Python ile günleri kendimiz saydırıyoruz (Garantili yöntemimiz)
        toplam_gun = len(rota_verisi["rota"])
        gun_isimleri = [f"{i + 1}. Gün" for i in range(toplam_gun)]

        # Sekmeleri bu garantili listeye göre oluşturuyoruz
        sekmeler = st.tabs(gun_isimleri)

        # Her bir sekmenin içini dolduruyoruz
        for i, sekme in enumerate(sekmeler):
            with sekme:
                gun_verisi = rota_verisi["rota"][i]

                # 1. Günün kısa özet planını yazdır
                st.write(gun_verisi.get("plan", "Plan bulunamadı."))

                # 2. Yapay zekanın önerdiği mekanları harita linkleriyle alt alta listele
                st.markdown("#### 📍 Gezilecek Mekanlar")
                mekanlar = gun_verisi.get("gezilecek_mekanlar", [])

                for mekan in mekanlar:
                    # Her bir mekan için o mekana özel Google Maps linki üretiyoruz
                    link = harita_linki_olustur(mekan, secilen_sehir)
                    st.markdown(f"- **{mekan}** ➔ [Haritada Gör]({link})")

                st.divider()  # Araya şık bir çizgi çekiyoruz

                # 3. Gider kalemleri (Aşağıdaki eski kodların aynı şekilde kalabilir)
                # Gider kalemlerini alt alta listele
                # 3. Gider kalemlerini alt alta listele
                st.markdown("#### 💸 Gider Kalemleri")

                for gider in gun_verisi.get("gider_kalemleri", []):
                    # Giderin adını çekiyoruz
                    kalem = gider.get("kalem", "Belirtilmemiş")

                    # Fiyatı çekerken hem "maliyet" hem de eski ihtimale karşı "tutar" kelimesini arıyoruz (Defensive Programming)
                    fiyat = gider.get("maliyet", gider.get("tutar", "-"))

                    st.write(f"- **{kalem}**: {fiyat}")

                # Günlük toplamı yeşil ve dikkat çekici bir kutuda göster
                st.success(f"💰 Günlük Toplam Maliyet: {gun_verisi.get('gunluk_toplam', 'Belirtilmedi')}")

                # --- SEKMELER DÖNGÜSÜ BİTTİKTEN SONRA EKLENECEK KISIM ---

        st.divider()  # Araya şık bir çizgi çekelim
        st.markdown("### 📥 Rotanızı Kaydedin")

        # 1. Bütün veriyi tek bir şık metin (string) dosyasında birleştiriyoruz
        indirme_metni = f"🌍 {secilen_sehir} Tatil Rotası 🌍\n"
        indirme_metni += f"Bütçe: {butce_secimi} | Süre: {gun_sayisi} Gün\n"
        indirme_metni += "=" * 40 + "\n\n"

        for i, gun_verisi in enumerate(rota_verisi["rota"]):
            indirme_metni += f"📍 {i + 1}. GÜN\n"
            indirme_metni += f"Plan: {gun_verisi.get('plan', 'Plan bulunamadı.')}\n\n"

            indirme_metni += "Gezilecek Mekanlar:\n"
            for mekan in gun_verisi.get("gezilecek_mekanlar", []):
                indirme_metni += f"- {mekan}\n"

            indirme_metni += "\n💸 Gider Kalemleri:\n"
            for gider in gun_verisi.get("gider_kalemleri", []):
                kalem = gider.get("kalem", "Belirtilmemiş")
                fiyat = gider.get("maliyet", gider.get("tutar", "-"))
                indirme_metni += f"- {kalem}: {fiyat}\n"

            indirme_metni += f"\n💰 Günlük Toplam: {gun_verisi.get('gunluk_toplam', 'Belirtilmedi')}\n"
            indirme_metni += "-" * 40 + "\n\n"

        # 2. Streamlit'in sihirli "İndirme Butonu"nu ekliyoruz
        st.download_button(
            label="📄 Rota Planını İndir",
            data=indirme_metni,
            file_name=f"{secilen_sehir}_Tatil_Rotasi.txt",
            mime="text/plain"
        )

    except Exception as e:
        # Eğer yepyeni bir hata olursa, sebebini ekranda görelim ki çözebilelim
        st.error(f"Görselleştirme sırasında ufak bir pürüz çıktı. Hata detayı: {e}")
        st.write("İşte ham rotan:")
        st.write(response.text)

# --- BUTON VE SONUÇ EKRANI ---
if st.button("Rotamı Çıkar"):
    arkaplan_degistir(secilen_sehir)
    with st.spinner("Yapay zeka rotanızı hazırlıyor, lütfen bekleyin..."):
        # Yukarıdaki fonksiyonu çağırıp sonuçları alıyoruz
        sonuc = rotayi_olustur(secilen_sehir, gun_sayisi, butce_secimi, ilgi_alanlari)

        # Sonucu ekrana yazdırıyoruz
        st.success("İşte Rotanız!")
        st.write(sonuc)