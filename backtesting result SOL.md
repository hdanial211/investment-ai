# REKOD KEPUTUSAN BACKTEST (INVESTMENT AI) - SOL
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
- Jumlah Trade: 4669
- Win Rate: 47.06% (2197 Menang / 2472 Kalah)
- Untung Bersih: **+ RM -540.37**
- Max Drawdown: **54.08%**
- Baki Akaun: RM 459.63

---

## 2. Eksperimen: XGBoost 'Sniper' (Konservatif & Selamat)
**Penerangan:** Probability Threshold tinggi, TP 1.0% dan SL ketat.
**Tetapan:**
- Saiz Layer: RM 50.0 | Max Layer: 1
- Gap Layering: 99.90% | Take Profit: 1.00%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 3565
- Win Rate: 30.86% (1100 Menang / 2465 Kalah)
- Untung Bersih: **+ RM -452.73**
- Max Drawdown: **45.47%**
- Baki Akaun: RM 547.27

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
- Jumlah Trade: 42
- Win Rate: 100.00% (42 Menang / 0 Kalah)
- Untung Bersih: **+ RM 17.61**
- Max Drawdown: **5.68%**
- Baki Akaun: RM 970.02

---

## 6. Eksperimen: Layering Skala Besar (Modal Terkawal)
**Penerangan:** Simulasi skala besar tapi modal RM 1000
**Tetapan:**
- Saiz Layer: RM 50.0 | Max Layer: 6
- Gap Layering: 5.00% | Take Profit: 2.00%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 12
- Win Rate: 100.00% (12 Menang / 0 Kalah)
- Untung Bersih: **+ RM 14.33**
- Max Drawdown: **15.62%**
- Baki Akaun: RM 890.14

---

## 7. Eksperimen: The Turtle Guard (RM10 x 30 Layer)
**Penerangan:** Beli banyak tapi saiz sangat kecil untuk tahan crash 15%.
**Tetapan:**
- Saiz Layer: RM 10.0 | Max Layer: 30
- Gap Layering: 0.50% | Take Profit: 0.50%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 110
- Win Rate: 100.00% (110 Menang / 0 Kalah)
- Untung Bersih: **+ RM 10.67**
- Max Drawdown: **15.74%**
- Baki Akaun: RM 885.12

---

## 8. Eksperimen: The Sniper (Deep Drop)
**Penerangan:** Tunggu harga jatuh 3% baru beli layer baru. TP besar 3%.
**Tetapan:**
- Saiz Layer: RM 50.0 | Max Layer: 5
- Gap Layering: 3.00% | Take Profit: 3.00%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 21
- Win Rate: 100.00% (21 Menang / 0 Kalah)
- Untung Bersih: **+ RM 19.82**
- Max Drawdown: **13.74%**
- Baki Akaun: RM 906.71

---

## 9. Eksperimen: Deep Value Layering (Moderate)
**Penerangan:** Saiz RM30, Gap 2%, TP 1.5%. Tunggu dan peram bila bawah.
**Tetapan:**
- Saiz Layer: RM 30.0 | Max Layer: 6
- Gap Layering: 2.00% | Take Profit: 1.50%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 23
- Win Rate: 100.00% (23 Menang / 0 Kalah)
- Untung Bersih: **+ RM 18.75**
- Max Drawdown: **9.92%**
- Baki Akaun: RM 936.56

---

## 10. Eksperimen: Patience is Gold (1 Layer Only)
**Penerangan:** Beli RM100 sekali, TP 5%, tiada DCA. Percaya 100% pada AI.
**Tetapan:**
- Saiz Layer: RM 100.0 | Max Layer: 1
- Gap Layering: 99.00% | Take Profit: 5.00%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 1826
- Win Rate: 19.33% (353 Menang / 1473 Kalah)
- Untung Bersih: **+ RM -474.36**
- Max Drawdown: **48.80%**
- Baki Akaun: RM 525.37

---

## 11. Eksperimen: Micro DCA Jarak Jauh
**Penerangan:** RM10, Gap 5%. Beli bila betul-betul jatuh teruk.
**Tetapan:**
- Saiz Layer: RM 10.0 | Max Layer: 10
- Gap Layering: 5.00% | Take Profit: 2.00%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 12
- Win Rate: 100.00% (12 Menang / 0 Kalah)
- Untung Bersih: **+ RM 2.87**
- Max Drawdown: **4.63%**
- Baki Akaun: RM 969.35

---

## 12. Eksperimen: High Frequency Scalping (0.2% TP)
**Penerangan:** TP sangat ketat (0.2%) untuk trade beribu kali setahun.
**Tetapan:**
- Saiz Layer: RM 20.0 | Max Layer: 10
- Gap Layering: 0.50% | Take Profit: 0.20%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 345
- Win Rate: 53.04% (183 Menang / 162 Kalah)
- Untung Bersih: **+ RM 4.99**
- Max Drawdown: **11.46%**
- Baki Akaun: RM 910.34

---

## 13. Eksperimen: Machine Gun Scalper (Gap 0.3%)
**Penerangan:** Beli setiap 0.3% jatuh. RM10 per layer.
**Tetapan:**
- Saiz Layer: RM 10.0 | Max Layer: 15
- Gap Layering: 0.30% | Take Profit: 0.40%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 179
- Win Rate: 100.00% (179 Menang / 0 Kalah)
- Untung Bersih: **+ RM 13.96**
- Max Drawdown: **8.51%**
- Baki Akaun: RM 942.98

---

## 14. Eksperimen: Mid-Frequency Trailing (0.5% Act)
**Penerangan:** Bila untung 0.5%, buka Trailing Stop 0.1% untuk kejar harga.
**Tetapan:**
- Saiz Layer: RM 20.0 | Max Layer: 8
- Gap Layering: 0.80% | Take Profit: 99.00%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 108
- Win Rate: 97.22% (105 Menang / 3 Kalah)
- Untung Bersih: **+ RM 14.96**
- Max Drawdown: **8.99%**
- Baki Akaun: RM 940.30

---

## 15. Eksperimen: Scalp & Run (RM50, TP 0.4%)
**Penerangan:** Modal besar sikit (RM50), tapi cepat lari (TP 0.4%).
**Tetapan:**
- Saiz Layer: RM 50.0 | Max Layer: 5
- Gap Layering: 0.50% | Take Profit: 0.40%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 111
- Win Rate: 100.00% (111 Menang / 0 Kalah)
- Untung Bersih: **+ RM 30.00**
- Max Drawdown: **14.26%**
- Baki Akaun: RM 907.81

---

## 16. Eksperimen: Heavy Scalping (RM100, 3 Layers)
**Penerangan:** Trade berat tapi pantas.
**Tetapan:**
- Saiz Layer: RM 100.0 | Max Layer: 3
- Gap Layering: 1.00% | Take Profit: 0.50%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 64
- Win Rate: 100.00% (64 Menang / 0 Kalah)
- Untung Bersih: **+ RM 36.38**
- Max Drawdown: **17.08%**
- Baki Akaun: RM 889.20

---

## 17. Eksperimen: Aggressive Micro Martingale (5 Lapis)
**Penerangan:** Mula dengan RM5 sahaja, TP ketat 0.3%. Max Exposure RM155.
**Tetapan:**
- Saiz Layer: RM 5.0 | Max Layer: 5
- Gap Layering: 1.00% | Take Profit: 0.30%
- Martingale: True | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 186
- Win Rate: 100.00% (186 Menang / 0 Kalah)
- Untung Bersih: **+ RM 2.19**
- Max Drawdown: **1.44%**
- Baki Akaun: RM 990.29

---

## 18. Eksperimen: Wide Gap Martingale (Anti-Crash)
**Penerangan:** Martingale gandaan RM10 (10,20,40,80) tapi hanya beli setiap kali jatuh 5%!
**Tetapan:**
- Saiz Layer: RM 10.0 | Max Layer: 4
- Gap Layering: 5.00% | Take Profit: 1.00%
- Martingale: True | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 31
- Win Rate: 100.00% (31 Menang / 0 Kalah)
- Untung Bersih: **+ RM 3.27**
- Max Drawdown: **2.24%**
- Baki Akaun: RM 985.20

---

## 19. Eksperimen: Fast Recovery Martingale (RM10, 4 Lapis)
**Penerangan:** Gap kecil 0.8% tapi ganda cepat untuk pulih.
**Tetapan:**
- Saiz Layer: RM 10.0 | Max Layer: 4
- Gap Layering: 0.80% | Take Profit: 0.50%
- Martingale: True | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 83
- Win Rate: 100.00% (83 Menang / 0 Kalah)
- Untung Bersih: **+ RM 5.90**
- Max Drawdown: **2.34%**
- Baki Akaun: RM 986.32

---

## 20. Eksperimen: High Risk Martingale (RM20, 5 Lapis)
**Penerangan:** Max exposure RM620. Untung besar tapi risiko tinggi.
**Tetapan:**
- Saiz Layer: RM 20.0 | Max Layer: 5
- Gap Layering: 1.00% | Take Profit: 1.00%
- Martingale: True | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 42
- Win Rate: 100.00% (42 Menang / 0 Kalah)
- Untung Bersih: **+ RM 18.93**
- Max Drawdown: **5.67%**
- Baki Akaun: RM 971.34

---

## 21. Eksperimen: Micro Frequency Martingale (RM2, 8 Lapis)
**Penerangan:** Mula dengan RM2. Gap 0.5%. Mampu cecah gandaan 128x (RM256).
**Tetapan:**
- Saiz Layer: RM 2.0 | Max Layer: 8
- Gap Layering: 0.50% | Take Profit: 0.40%
- Martingale: True | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 158
- Win Rate: 100.00% (158 Menang / 0 Kalah)
- Untung Bersih: **+ RM 1.98**
- Max Drawdown: **0.92%**
- Baki Akaun: RM 994.34

---

## 22. Eksperimen: Dynamic TP Martingale (RM5, Gap 1%)
**Penerangan:** TP membesar apabila Martingale masuk layer dalam. Gap 1%.
**Tetapan:**
- Saiz Layer: RM 5.0 | Max Layer: 5
- Gap Layering: 1.00% | Take Profit: 0.20%
- Martingale: True | Dynamic TP: True
**Keputusan:**
- Jumlah Trade: 207
- Win Rate: 96.14% (199 Menang / 8 Kalah)
- Untung Bersih: **+ RM 1.71**
- Max Drawdown: **1.44%**
- Baki Akaun: RM 989.80

---

## 23. Eksperimen: Dynamic TP Martingale (RM10, Gap 0.5%)
**Penerangan:** Layer rapat (0.5%) untuk agresif mengumpul pada kejatuhan kecil.
**Tetapan:**
- Saiz Layer: RM 10.0 | Max Layer: 4
- Gap Layering: 0.50% | Take Profit: 0.20%
- Martingale: True | Dynamic TP: True
**Keputusan:**
- Jumlah Trade: 151
- Win Rate: 94.70% (143 Menang / 8 Kalah)
- Untung Bersih: **+ RM 3.62**
- Max Drawdown: **2.35%**
- Baki Akaun: RM 984.01

---

## 24. Eksperimen: Dynamic TP Extreme Drop (Gap 3%)
**Penerangan:** Martingale yang selamat pada junaman 3% sahaja.
**Tetapan:**
- Saiz Layer: RM 10.0 | Max Layer: 4
- Gap Layering: 3.00% | Take Profit: 0.25%
- Martingale: True | Dynamic TP: True
**Keputusan:**
- Jumlah Trade: 123
- Win Rate: 99.19% (122 Menang / 1 Kalah)
- Untung Bersih: **+ RM 1.78**
- Max Drawdown: **2.28%**
- Baki Akaun: RM 983.00

---

## 25. Eksperimen: Dynamic TP Trailing Hybrid
**Penerangan:** Sistem Dynamic TP, tetapi ada Trailing Stop dilekatkan bila untung.
**Tetapan:**
- Saiz Layer: RM 10.0 | Max Layer: 4
- Gap Layering: 1.00% | Take Profit: 99.00%
- Martingale: True | Dynamic TP: True
**Keputusan:**
- Jumlah Trade: 187
- Win Rate: 95.72% (179 Menang / 8 Kalah)
- Untung Bersih: **+ RM 2.97**
- Max Drawdown: **2.34%**
- Baki Akaun: RM 983.42

---

## 26. Eksperimen: The Ultimate 6-Layer Dynamic Martingale
**Penerangan:** Mula dengan RM3. Max exposure RM189. Dynamic TP diaktifkan.
**Tetapan:**
- Saiz Layer: RM 3.0 | Max Layer: 6
- Gap Layering: 0.80% | Take Profit: 0.20%
- Martingale: True | Dynamic TP: True
**Keputusan:**
- Jumlah Trade: 232
- Win Rate: 97.84% (227 Menang / 5 Kalah)
- Untung Bersih: **+ RM 1.15**
- Max Drawdown: **1.04%**
- Baki Akaun: RM 992.58

---

## 27. Eksperimen: The Trailing Master (Gap 1%, Act 1%)
**Penerangan:** Tiada Hard TP. Trailing hidup bila untung 1%.
**Tetapan:**
- Saiz Layer: RM 15.0 | Max Layer: 10
- Gap Layering: 1.00% | Take Profit: 99.00%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 50
- Win Rate: 100.00% (50 Menang / 0 Kalah)
- Untung Bersih: **+ RM 13.05**
- Max Drawdown: **8.46%**
- Baki Akaun: RM 943.12

---

## 28. Eksperimen: Ultra Tight Trailing (Act 0.3%, Gap 0.1%)
**Penerangan:** Trailing hidup sangat awal (0.3%) untuk kunci untung segera.
**Tetapan:**
- Saiz Layer: RM 20.0 | Max Layer: 10
- Gap Layering: 0.80% | Take Profit: 99.00%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 201
- Win Rate: 63.18% (127 Menang / 74 Kalah)
- Untung Bersih: **+ RM 9.03**
- Max Drawdown: **11.24%**
- Baki Akaun: RM 916.31

---

## 29. Eksperimen: Wide Trailing (Act 2%, Gap 0.5%)
**Penerangan:** Beri ruang untuk trend membesar sebelum jual.
**Tetapan:**
- Saiz Layer: RM 10.0 | Max Layer: 15
- Gap Layering: 1.00% | Take Profit: 99.00%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 19
- Win Rate: 100.00% (19 Menang / 0 Kalah)
- Untung Bersih: **+ RM 9.49**
- Max Drawdown: **8.16%**
- Baki Akaun: RM 943.56

---

## 30. Eksperimen: Trailing Stop + Martingale (RM10, 4L)
**Penerangan:** Pulih dengan Martingale dan kejar profit dengan Trailing.
**Tetapan:**
- Saiz Layer: RM 10.0 | Max Layer: 4
- Gap Layering: 1.00% | Take Profit: 99.00%
- Martingale: True | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 79
- Win Rate: 93.67% (74 Menang / 5 Kalah)
- Untung Bersih: **+ RM 4.99**
- Max Drawdown: **2.34%**
- Baki Akaun: RM 985.50

---

## 31. Eksperimen: Deep Trailing Rescue
**Penerangan:** Layer di -3%, Trailing di 0.5%. Pertahanan kental.
**Tetapan:**
- Saiz Layer: RM 30.0 | Max Layer: 5
- Gap Layering: 3.00% | Take Profit: 99.00%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 66
- Win Rate: 90.91% (60 Menang / 6 Kalah)
- Untung Bersih: **+ RM 8.27**
- Max Drawdown: **8.38%**
- Baki Akaun: RM 939.53

---

## 32. Eksperimen: Golden Mean (RM15, 10L, 0.8% Gap, 0.6% TP)
**Penerangan:** Kesimbangan antara profit sederhana dan pertahanan.
**Tetapan:**
- Saiz Layer: RM 15.0 | Max Layer: 10
- Gap Layering: 0.80% | Take Profit: 0.60%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 86
- Win Rate: 100.00% (86 Menang / 0 Kalah)
- Untung Bersih: **+ RM 12.49**
- Max Drawdown: **8.40%**
- Baki Akaun: RM 942.94

---

## 33. Eksperimen: The Whale Imitator (RM250, 2L, 5% Gap)
**Penerangan:** Membeli saiz gergasi pada kejatuhan drastik.
**Tetapan:**
- Saiz Layer: RM 250.0 | Max Layer: 2
- Gap Layering: 5.00% | Take Profit: 2.00%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 12
- Win Rate: 100.00% (12 Menang / 0 Kalah)
- Untung Bersih: **+ RM 71.67**
- Max Drawdown: **27.13%**
- Baki Akaun: RM 833.46

---

## 34. Eksperimen: Micro Limitless (RM1, 100L, 0.2% Gap)
**Penerangan:** Saiz sekecil mungkin. Sentiasa berada dalam pasaran.
**Tetapan:**
- Saiz Layer: RM 1.0 | Max Layer: 100
- Gap Layering: 0.20% | Take Profit: 0.50%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 134
- Win Rate: 100.00% (134 Menang / 0 Kalah)
- Untung Bersih: **+ RM 2.12**
- Max Drawdown: **4.57%**
- Baki Akaun: RM 969.25

---

## 35. Eksperimen: Martingale Mega Defense (RM5, 5L, 2% Gap)
**Penerangan:** Martingale yang cuma masuk pasaran bila ada junaman merah.
**Tetapan:**
- Saiz Layer: RM 5.0 | Max Layer: 5
- Gap Layering: 2.00% | Take Profit: 0.50%
- Martingale: True | Dynamic TP: True
**Keputusan:**
- Jumlah Trade: 143
- Win Rate: 97.90% (140 Menang / 3 Kalah)
- Untung Bersih: **+ RM 1.08**
- Max Drawdown: **1.42%**
- Baki Akaun: RM 989.49

---

## 36. Eksperimen: The Final Holy Grail Candidate
**Penerangan:** RM10, 15 Layer, 0.6% Gap, Trailing 0.5% Act / 0.15% Gap. Sangat kukuh.
**Tetapan:**
- Saiz Layer: RM 10.0 | Max Layer: 15
- Gap Layering: 0.60% | Take Profit: 99.00%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 111
- Win Rate: 94.59% (105 Menang / 6 Kalah)
- Untung Bersih: **+ RM 8.43**
- Max Drawdown: **8.33%**
- Baki Akaun: RM 940.37

---

## 37. Eksperimen: High Volatility Catcher (RM20, 10L, 2% Gap)
**Penerangan:** Gap besar 2%, RM20 per layer.
**Tetapan:**
- Saiz Layer: RM 20.0 | Max Layer: 10
- Gap Layering: 2.00% | Take Profit: 1.00%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 41
- Win Rate: 100.00% (41 Menang / 0 Kalah)
- Untung Bersih: **+ RM 11.02**
- Max Drawdown: **10.89%**
- Baki Akaun: RM 922.43

---

## 38. Eksperimen: Super Fast Martingale (RM1, 10L, 0.2% Gap)
**Penerangan:** Saiz RM1 untuk main pantas dan ganda pada gap kecil.
**Tetapan:**
- Saiz Layer: RM 1.0 | Max Layer: 10
- Gap Layering: 0.20% | Take Profit: 0.30%
- Martingale: True | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 204
- Win Rate: 100.00% (204 Menang / 0 Kalah)
- Untung Bersih: **+ RM 1.37**
- Max Drawdown: **0.59%**
- Baki Akaun: RM 996.48

---

## 39. Eksperimen: AI Only No SL (Pure Trust)
**Penerangan:** Modal RM1000 main RM50 sekali tembak tiada dca, tiada sl.
**Tetapan:**
- Saiz Layer: RM 50.0 | Max Layer: 1
- Gap Layering: 99.90% | Take Profit: 1.00%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 2872
- Win Rate: 32.63% (937 Menang / 1935 Kalah)
- Untung Bersih: **+ RM -332.11**
- Max Drawdown: **33.33%**
- Baki Akaun: RM 667.89

---

## 40. Eksperimen: Scalp + Dynamic TP Extreme (0.3% Gap)
**Penerangan:** Gabung layer pantas dan dynamic TP.
**Tetapan:**
- Saiz Layer: RM 10.0 | Max Layer: 10
- Gap Layering: 0.30% | Take Profit: 0.20%
- Martingale: False | Dynamic TP: True
**Keputusan:**
- Jumlah Trade: 282
- Win Rate: 97.16% (274 Menang / 8 Kalah)
- Untung Bersih: **+ RM 6.40**
- Max Drawdown: **5.77%**
- Baki Akaun: RM 958.45

