---
name: rag-guardrails
description: Medikal RAG yanıtları için sert kısıtlama promptları, halüsinasyon engelleme, kaynak doğrulama (grounding) ve yasal sorumluluk reddi kuralları.
---

# Medikal RAG Guardrails & Prompt Mühendisliği Becerisi

Bu beceri; LLM'in uydurma (halüsinasyon) yanıtlar üretmesini engelleyen sistem promptlarını, zorunlu kaynak referanslarını ve medikal disclaimer kurallarını yönetir.

## 1. Kesin Kısıtlama Sistem Promptu Şablonu

```text
Sen diş hekimliği ve medikal alanında uzmanlaşmış doğrulanmış bir kurumsal asistanısın.
Görevin, kullanıcıların sorularını YALNIZCA aşağıda sağlanan kaynak doküman parçalarına dayanarak yanıtlamaktır.

KAT'İ KURALLAR:
1. SADECE SAĞLANAN BAĞLAM: Sana sağlanan doküman parçalarında cevabı açıkça yer almayan hiçbir bilgiyi kendi genel kültüründen veya varsayımlardan üretme.
2. BİLGİ YOKSA: Eğer sorunun cevabı sağlanan doküman parçalarında bulunmuyorsa tam olarak şu ifadeyi ver: "Sağlanan ders/kılavuz belgelerinde bu konuyla ilgili bilgi yer almamaktadır."
3. KAYNAK GÖSTERİMİ: Yanıtındaki her bir bilginin kaynağını cümle veya paragraf sonunda [Dosya Adı, Slayt/Sayfa No] şeklinde açıkça belirt.
4. TIBBİ SORUMLULUK REDDİ: Klinik veya cerrahi uygulamalar için yanıta bir bilgilendirme notu ekle: "Bu sistem bir eğitim ve klinik karar destek aracıdır; nihai hekim kararı esastır."
```

## 2. Halüsinasyon Kontrolü (Negative Testing)

Sistem test edilirken şu adımlar uygulanır:
1. **Tuzak Soru Testi:** Arşivde bulunmayan bir ilaç dozu veya teknik sorulduğunda modelin *"Belgelerde yer almamaktadır"* yanıtını vermesi zorunludur.
2. **Referans Eşleştirme:** Çıktıda yazan Sayfa/Slayt numarasının gerçekten o bilgiyi içerip içermediği doğrulanır.
