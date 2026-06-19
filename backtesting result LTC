# REKOD KEPUTUSAN BACKTEST (INVESTMENT AI) - LTC
Modal Permulaan Rujukan: RM 1,000
Yuran Hata Exchange: 0.25% Taker / 0.00% Maker (Total: 0.25% per round trip)

--- 

# --- UJIAN BATCH 40 TETAPAN (MEGA BACKTEST) ---

---

## 1. Eksperimen: XGBoost Asas (Model Kekerapan Tinggi)
**Penerangan:** Beli jika AI arah Beli, Jual jika AI arah Jual. Tiada tapisan keyakinan.
**Tetapan:**
- Saiz Layer: RM 50.0 | Max Layer: 1
- Gap Layering: 99.90% | Take Profit: 0.50%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 3816
- Win Rate: 47.54% (1814 Menang / 2002 Kalah)
- Untung Bersih: **+ RM -437.48**
- Max Drawdown: **43.84%**
- Baki Akaun: RM 562.31

---

## 2. Eksperimen: XGBoost 'Sniper' (Konservatif & Selamat)
**Penerangan:** Probability Threshold tinggi, TP 1.0% dan SL ketat.
**Tetapan:**
- Saiz Layer: RM 50.0 | Max Layer: 1
- Gap Layering: 99.90% | Take Profit: 1.00%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 2237
- Win Rate: 31.74% (710 Menang / 1527 Kalah)
- Untung Bersih: **+ RM -275.19**
- Max Drawdown: **27.62%**
- Baki Akaun: RM 724.63

---

## 3. Eksperimen: Reinforcement Learning PPO (Agresif Scalping)
**Penerangan:** PPO Model, Auto TP 1.0%, Auto SL 0.5%.
**Tetapan:**
- Saiz Layer: RM 50.0 | Max Layer: 1
- Gap Layering: 99.90% | Take Profit: 1.00%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 0
- Win Rate: 0.00% (0 Menang / 0 Kalah)
- Untung Bersih: **+ RM 0.00**
- Max Drawdown: **0.00%**
- Baki Akaun: RM 1000.00

---

## 4. Eksperimen: Reinforcement Learning PPO (Fokus Expectancy & Perlindungan Yuran)
**Penerangan:** Hukuman Keras untuk elak kerugian.
**Tetapan:**
- Saiz Layer: RM 50.0 | Max Layer: 1
- Gap Layering: 99.90% | Take Profit: 2.00%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 0
- Win Rate: 0.00% (0 Menang / 0 Kalah)
- Untung Bersih: **+ RM 0.00**
- Max Drawdown: **0.00%**
- Baki Akaun: RM 1000.00

---

## 5. Eksperimen: Strategi Layering / Dollar Cost Averaging (DCA)
**Penerangan:** DCA Asas
**Tetapan:**
- Saiz Layer: RM 20.0 | Max Layer: 5
- Gap Layering: 1.00% | Take Profit: 1.00%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 22
- Win Rate: 100.00% (22 Menang / 0 Kalah)
- Untung Bersih: **+ RM 8.15**
- Max Drawdown: **5.04%**
- Baki Akaun: RM 963.54

---

## 6. Eksperimen: Layering Skala Besar (Modal Terkawal)
**Penerangan:** Simulasi skala besar tapi modal RM 1000
**Tetapan:**
- Saiz Layer: RM 50.0 | Max Layer: 6
- Gap Layering: 5.00% | Take Profit: 2.00%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 7
- Win Rate: 100.00% (7 Menang / 0 Kalah)
- Untung Bersih: **+ RM 7.42**
- Max Drawdown: **13.39%**
- Baki Akaun: RM 894.54

---

## 7. Eksperimen: The Turtle Guard (RM10 x 30 Layer)
**Penerangan:** Beli banyak tapi saiz sangat kecil untuk tahan crash 15%.
**Tetapan:**
- Saiz Layer: RM 10.0 | Max Layer: 30
- Gap Layering: 0.50% | Take Profit: 0.50%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 84
- Win Rate: 100.00% (84 Menang / 0 Kalah)
- Untung Bersih: **+ RM 6.05**
- Max Drawdown: **12.61%**
- Baki Akaun: RM 899.48

---

## 8. Eksperimen: The Sniper (Deep Drop)
**Penerangan:** Tunggu harga jatuh 3% baru beli layer baru. TP besar 3%.
**Tetapan:**
- Saiz Layer: RM 50.0 | Max Layer: 5
- Gap Layering: 3.00% | Take Profit: 3.00%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 13
- Win Rate: 100.00% (13 Menang / 0 Kalah)
- Untung Bersih: **+ RM 11.55**
- Max Drawdown: **11.33%**
- Baki Akaun: RM 914.47

---

## 9. Eksperimen: Deep Value Layering (Moderate)
**Penerangan:** Saiz RM30, Gap 2%, TP 1.5%. Tunggu dan peram bila bawah.
**Tetapan:**
- Saiz Layer: RM 30.0 | Max Layer: 6
- Gap Layering: 2.00% | Take Profit: 1.50%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 12
- Win Rate: 100.00% (12 Menang / 0 Kalah)
- Untung Bersih: **+ RM 9.52**
- Max Drawdown: **8.21%**
- Baki Akaun: RM 938.18

---

## 10. Eksperimen: Patience is Gold (1 Layer Only)
**Penerangan:** Beli RM100 sekali, TP 5%, tiada DCA. Percaya 100% pada AI.
**Tetapan:**
- Saiz Layer: RM 100.0 | Max Layer: 1
- Gap Layering: 99.00% | Take Profit: 5.00%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 1146
- Win Rate: 20.16% (231 Menang / 915 Kalah)
- Untung Bersih: **+ RM -303.15**
- Max Drawdown: **31.00%**
- Baki Akaun: RM 696.44

---

## 11. Eksperimen: Micro DCA Jarak Jauh
**Penerangan:** RM10, Gap 5%. Beli bila betul-betul jatuh teruk.
**Tetapan:**
- Saiz Layer: RM 10.0 | Max Layer: 10
- Gap Layering: 5.00% | Take Profit: 2.00%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 7
- Win Rate: 100.00% (7 Menang / 0 Kalah)
- Untung Bersih: **+ RM 1.48**
- Max Drawdown: **3.67%**
- Baki Akaun: RM 972.75

---

## 12. Eksperimen: High Frequency Scalping (0.2% TP)
**Penerangan:** TP sangat ketat (0.2%) untuk trade beribu kali setahun.
**Tetapan:**
- Saiz Layer: RM 20.0 | Max Layer: 10
- Gap Layering: 0.50% | Take Profit: 0.20%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 251
- Win Rate: 49.00% (123 Menang / 128 Kalah)
- Untung Bersih: **+ RM 1.99**
- Max Drawdown: **9.56%**
- Baki Akaun: RM 918.44

---

## 13. Eksperimen: Machine Gun Scalper (Gap 0.3%)
**Penerangan:** Beli setiap 0.3% jatuh. RM10 per layer.
**Tetapan:**
- Saiz Layer: RM 10.0 | Max Layer: 15
- Gap Layering: 0.30% | Take Profit: 0.40%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 121
- Win Rate: 100.00% (121 Menang / 0 Kalah)
- Untung Bersih: **+ RM 6.70**
- Max Drawdown: **7.10%**
- Baki Akaun: RM 944.42

---

## 14. Eksperimen: Mid-Frequency Trailing (0.5% Act)
**Penerangan:** Bila untung 0.5%, buka Trailing Stop 0.1% untuk kejar harga.
**Tetapan:**
- Saiz Layer: RM 20.0 | Max Layer: 8
- Gap Layering: 0.80% | Take Profit: 99.00%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 76
- Win Rate: 96.05% (73 Menang / 3 Kalah)
- Untung Bersih: **+ RM 8.86**
- Max Drawdown: **7.56%**
- Baki Akaun: RM 942.48

---

## 15. Eksperimen: Scalp & Run (RM50, TP 0.4%)
**Penerangan:** Modal besar sikit (RM50), tapi cepat lari (TP 0.4%).
**Tetapan:**
- Saiz Layer: RM 50.0 | Max Layer: 5
- Gap Layering: 0.50% | Take Profit: 0.40%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 83
- Win Rate: 100.00% (83 Menang / 0 Kalah)
- Untung Bersih: **+ RM 15.87**
- Max Drawdown: **12.01%**
- Baki Akaun: RM 908.98

---

## 16. Eksperimen: Heavy Scalping (RM100, 3 Layers)
**Penerangan:** Trade berat tapi pantas.
**Tetapan:**
- Saiz Layer: RM 100.0 | Max Layer: 3
- Gap Layering: 1.00% | Take Profit: 0.50%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 49
- Win Rate: 100.00% (49 Menang / 0 Kalah)
- Untung Bersih: **+ RM 20.64**
- Max Drawdown: **14.91%**
- Baki Akaun: RM 886.32

---

## 17. Eksperimen: Aggressive Micro Martingale (5 Lapis)
**Penerangan:** Mula dengan RM5 sahaja, TP ketat 0.3%. Max Exposure RM155.
**Tetapan:**
- Saiz Layer: RM 5.0 | Max Layer: 5
- Gap Layering: 1.00% | Take Profit: 0.30%
- Martingale: True | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 159
- Win Rate: 100.00% (159 Menang / 0 Kalah)
- Untung Bersih: **+ RM 1.37**
- Max Drawdown: **1.20%**
- Baki Akaun: RM 990.87

---

## 18. Eksperimen: Wide Gap Martingale (Anti-Crash)
**Penerangan:** Martingale gandaan RM10 (10,20,40,80) tapi hanya beli setiap kali jatuh 5%!
**Tetapan:**
- Saiz Layer: RM 10.0 | Max Layer: 4
- Gap Layering: 5.00% | Take Profit: 1.00%
- Martingale: True | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 19
- Win Rate: 100.00% (19 Menang / 0 Kalah)
- Untung Bersih: **+ RM 2.06**
- Max Drawdown: **1.80%**
- Baki Akaun: RM 986.64

---

## 19. Eksperimen: Fast Recovery Martingale (RM10, 4 Lapis)
**Penerangan:** Gap kecil 0.8% tapi ganda cepat untuk pulih.
**Tetapan:**
- Saiz Layer: RM 10.0 | Max Layer: 4
- Gap Layering: 0.80% | Take Profit: 0.50%
- Martingale: True | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 75
- Win Rate: 100.00% (75 Menang / 0 Kalah)
- Untung Bersih: **+ RM 5.73**
- Max Drawdown: **1.94%**
- Baki Akaun: RM 988.67

---

## 20. Eksperimen: High Risk Martingale (RM20, 5 Lapis)
**Penerangan:** Max exposure RM620. Untung besar tapi risiko tinggi.
**Tetapan:**
- Saiz Layer: RM 20.0 | Max Layer: 5
- Gap Layering: 1.00% | Take Profit: 1.00%
- Martingale: True | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 23
- Win Rate: 100.00% (23 Menang / 0 Kalah)
- Untung Bersih: **+ RM 11.68**
- Max Drawdown: **6.97%**
- Baki Akaun: RM 949.98

---

## 21. Eksperimen: Micro Frequency Martingale (RM2, 8 Lapis)
**Penerangan:** Mula dengan RM2. Gap 0.5%. Mampu cecah gandaan 128x (RM256).
**Tetapan:**
- Saiz Layer: RM 2.0 | Max Layer: 8
- Gap Layering: 0.50% | Take Profit: 0.40%
- Martingale: True | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 118
- Win Rate: 100.00% (118 Menang / 0 Kalah)
- Untung Bersih: **+ RM 1.61**
- Max Drawdown: **0.77%**
- Baki Akaun: RM 994.86

---

## 22. Eksperimen: Dynamic TP Martingale (RM5, Gap 1%)
**Penerangan:** TP membesar apabila Martingale masuk layer dalam. Gap 1%.
**Tetapan:**
- Saiz Layer: RM 5.0 | Max Layer: 5
- Gap Layering: 1.00% | Take Profit: 0.20%
- Martingale: True | Dynamic TP: True
**Keputusan:**
- Jumlah Trade: 185
- Win Rate: 92.43% (171 Menang / 14 Kalah)
- Untung Bersih: **+ RM 1.05**
- Max Drawdown: **1.20%**
- Baki Akaun: RM 990.55

---

## 23. Eksperimen: Dynamic TP Martingale (RM10, Gap 0.5%)
**Penerangan:** Layer rapat (0.5%) untuk agresif mengumpul pada kejatuhan kecil.
**Tetapan:**
- Saiz Layer: RM 10.0 | Max Layer: 4
- Gap Layering: 0.50% | Take Profit: 0.20%
- Martingale: True | Dynamic TP: True
**Keputusan:**
- Jumlah Trade: 95
- Win Rate: 97.89% (93 Menang / 2 Kalah)
- Untung Bersih: **+ RM 1.81**
- Max Drawdown: **4.05%**
- Baki Akaun: RM 965.96

---

## 24. Eksperimen: Dynamic TP Extreme Drop (Gap 3%)
**Penerangan:** Martingale yang selamat pada junaman 3% sahaja.
**Tetapan:**
- Saiz Layer: RM 10.0 | Max Layer: 4
- Gap Layering: 3.00% | Take Profit: 0.25%
- Martingale: True | Dynamic TP: True
**Keputusan:**
- Jumlah Trade: 113
- Win Rate: 95.58% (108 Menang / 5 Kalah)
- Untung Bersih: **+ RM 0.97**
- Max Drawdown: **1.86%**
- Baki Akaun: RM 984.89

---

## 25. Eksperimen: Dynamic TP Trailing Hybrid
**Penerangan:** Sistem Dynamic TP, tetapi ada Trailing Stop dilekatkan bila untung.
**Tetapan:**
- Saiz Layer: RM 10.0 | Max Layer: 4
- Gap Layering: 1.00% | Take Profit: 99.00%
- Martingale: True | Dynamic TP: True
**Keputusan:**
- Jumlah Trade: 164
- Win Rate: 93.29% (153 Menang / 11 Kalah)
- Untung Bersih: **+ RM 1.86**
- Max Drawdown: **1.93%**
- Baki Akaun: RM 984.93

---

## 26. Eksperimen: The Ultimate 6-Layer Dynamic Martingale
**Penerangan:** Mula dengan RM3. Max exposure RM189. Dynamic TP diaktifkan.
**Tetapan:**
- Saiz Layer: RM 3.0 | Max Layer: 6
- Gap Layering: 0.80% | Take Profit: 0.20%
- Martingale: True | Dynamic TP: True
**Keputusan:**
- Jumlah Trade: 189
- Win Rate: 93.65% (177 Menang / 12 Kalah)
- Untung Bersih: **+ RM 0.67**
- Max Drawdown: **0.87%**
- Baki Akaun: RM 993.08

---

## 27. Eksperimen: The Trailing Master (Gap 1%, Act 1%)
**Penerangan:** Tiada Hard TP. Trailing hidup bila untung 1%.
**Tetapan:**
- Saiz Layer: RM 15.0 | Max Layer: 10
- Gap Layering: 1.00% | Take Profit: 99.00%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 26
- Win Rate: 100.00% (26 Menang / 0 Kalah)
- Untung Bersih: **+ RM 6.84**
- Max Drawdown: **6.97%**
- Baki Akaun: RM 946.75

---

## 28. Eksperimen: Ultra Tight Trailing (Act 0.3%, Gap 0.1%)
**Penerangan:** Trailing hidup sangat awal (0.3%) untuk kunci untung segera.
**Tetapan:**
- Saiz Layer: RM 20.0 | Max Layer: 10
- Gap Layering: 0.80% | Take Profit: 99.00%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 157
- Win Rate: 63.06% (99 Menang / 58 Kalah)
- Untung Bersih: **+ RM 6.34**
- Max Drawdown: **9.33%**
- Baki Akaun: RM 924.89

---

## 29. Eksperimen: Wide Trailing (Act 2%, Gap 0.5%)
**Penerangan:** Beri ruang untuk trend membesar sebelum jual.
**Tetapan:**
- Saiz Layer: RM 10.0 | Max Layer: 15
- Gap Layering: 1.00% | Take Profit: 99.00%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 9
- Win Rate: 100.00% (9 Menang / 0 Kalah)
- Untung Bersih: **+ RM 3.95**
- Max Drawdown: **7.21%**
- Baki Akaun: RM 942.45

---

## 30. Eksperimen: Trailing Stop + Martingale (RM10, 4L)
**Penerangan:** Pulih dengan Martingale dan kejar profit dengan Trailing.
**Tetapan:**
- Saiz Layer: RM 10.0 | Max Layer: 4
- Gap Layering: 1.00% | Take Profit: 99.00%
- Martingale: True | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 85
- Win Rate: 95.29% (81 Menang / 4 Kalah)
- Untung Bersih: **+ RM 4.30**
- Max Drawdown: **1.94%**
- Baki Akaun: RM 987.37

---

## 31. Eksperimen: Deep Trailing Rescue
**Penerangan:** Layer di -3%, Trailing di 0.5%. Pertahanan kental.
**Tetapan:**
- Saiz Layer: RM 30.0 | Max Layer: 5
- Gap Layering: 3.00% | Take Profit: 99.00%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 57
- Win Rate: 91.23% (52 Menang / 5 Kalah)
- Untung Bersih: **+ RM 5.42**
- Max Drawdown: **6.76%**
- Baki Akaun: RM 947.17

---

## 32. Eksperimen: Golden Mean (RM15, 10L, 0.8% Gap, 0.6% TP)
**Penerangan:** Kesimbangan antara profit sederhana dan pertahanan.
**Tetapan:**
- Saiz Layer: RM 15.0 | Max Layer: 10
- Gap Layering: 0.80% | Take Profit: 0.60%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 62
- Win Rate: 100.00% (62 Menang / 0 Kalah)
- Untung Bersih: **+ RM 7.92**
- Max Drawdown: **6.99%**
- Baki Akaun: RM 946.84

---

## 33. Eksperimen: The Whale Imitator (RM250, 2L, 5% Gap)
**Penerangan:** Membeli saiz gergasi pada kejatuhan drastik.
**Tetapan:**
- Saiz Layer: RM 250.0 | Max Layer: 2
- Gap Layering: 5.00% | Take Profit: 2.00%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 7
- Win Rate: 100.00% (7 Menang / 0 Kalah)
- Untung Bersih: **+ RM 37.11**
- Max Drawdown: **24.43%**
- Baki Akaun: RM 815.58

---

## 34. Eksperimen: Micro Limitless (RM1, 100L, 0.2% Gap)
**Penerangan:** Saiz sekecil mungkin. Sentiasa berada dalam pasaran.
**Tetapan:**
- Saiz Layer: RM 1.0 | Max Layer: 100
- Gap Layering: 0.20% | Take Profit: 0.50%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 102
- Win Rate: 100.00% (102 Menang / 0 Kalah)
- Untung Bersih: **+ RM 1.24**
- Max Drawdown: **3.16%**
- Baki Akaun: RM 977.60

---

## 35. Eksperimen: Martingale Mega Defense (RM5, 5L, 2% Gap)
**Penerangan:** Martingale yang cuma masuk pasaran bila ada junaman merah.
**Tetapan:**
- Saiz Layer: RM 5.0 | Max Layer: 5
- Gap Layering: 2.00% | Take Profit: 0.50%
- Martingale: True | Dynamic TP: True
**Keputusan:**
- Jumlah Trade: 119
- Win Rate: 94.96% (113 Menang / 6 Kalah)
- Untung Bersih: **+ RM 0.58**
- Max Drawdown: **1.17%**
- Baki Akaun: RM 990.47

---

## 36. Eksperimen: The Final Holy Grail Candidate
**Penerangan:** RM10, 15 Layer, 0.6% Gap, Trailing 0.5% Act / 0.15% Gap. Sangat kukuh.
**Tetapan:**
- Saiz Layer: RM 10.0 | Max Layer: 15
- Gap Layering: 0.60% | Take Profit: 99.00%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 84
- Win Rate: 96.43% (81 Menang / 3 Kalah)
- Untung Bersih: **+ RM 5.59**
- Max Drawdown: **6.91%**
- Baki Akaun: RM 945.63

---

## 37. Eksperimen: High Volatility Catcher (RM20, 10L, 2% Gap)
**Penerangan:** Gap besar 2%, RM20 per layer.
**Tetapan:**
- Saiz Layer: RM 20.0 | Max Layer: 10
- Gap Layering: 2.00% | Take Profit: 1.00%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 22
- Win Rate: 100.00% (22 Menang / 0 Kalah)
- Untung Bersih: **+ RM 5.67**
- Max Drawdown: **8.52%**
- Baki Akaun: RM 933.56

---

## 38. Eksperimen: Super Fast Martingale (RM1, 10L, 0.2% Gap)
**Penerangan:** Saiz RM1 untuk main pantas dan ganda pada gap kecil.
**Tetapan:**
- Saiz Layer: RM 1.0 | Max Layer: 10
- Gap Layering: 0.20% | Take Profit: 0.30%
- Martingale: True | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 220
- Win Rate: 100.00% (220 Menang / 0 Kalah)
- Untung Bersih: **+ RM 1.50**
- Max Drawdown: **1.82%**
- Baki Akaun: RM 997.24

---

## 39. Eksperimen: AI Only No SL (Pure Trust)
**Penerangan:** Modal RM1000 main RM50 sekali tembak tiada dca, tiada sl.
**Tetapan:**
- Saiz Layer: RM 50.0 | Max Layer: 1
- Gap Layering: 99.90% | Take Profit: 1.00%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 2237
- Win Rate: 31.74% (710 Menang / 1527 Kalah)
- Untung Bersih: **+ RM -275.19**
- Max Drawdown: **27.62%**
- Baki Akaun: RM 724.63

---

## 40. Eksperimen: Scalp + Dynamic TP Extreme (0.3% Gap)
**Penerangan:** Gabung layer pantas dan dynamic TP.
**Tetapan:**
- Saiz Layer: RM 10.0 | Max Layer: 10
- Gap Layering: 0.30% | Take Profit: 0.20%
- Martingale: False | Dynamic TP: True
**Keputusan:**
- Jumlah Trade: 165
- Win Rate: 95.76% (158 Menang / 7 Kalah)
- Untung Bersih: **+ RM 2.73**
- Max Drawdown: **4.82%**
- Baki Akaun: RM 960.45

