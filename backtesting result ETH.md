# REKOD KEPUTUSAN BACKTEST (INVESTMENT AI) - ETH
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
- Jumlah Trade: 8060
- Win Rate: 46.24% (3727 Menang / 4333 Kalah)
- Untung Bersih: **+ RM -949.94**
- Max Drawdown: **95.00%**
- Baki Akaun: RM 50.06

---

## 2. Eksperimen: XGBoost 'Sniper' (Konservatif & Selamat)
**Penerangan:** Probability Threshold tinggi, TP 1.0% dan SL ketat.
**Tetapan:**
- Saiz Layer: RM 50.0 | Max Layer: 1
- Gap Layering: 99.90% | Take Profit: 1.00%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 6949
- Win Rate: 30.51% (2120 Menang / 4829 Kalah)
- Untung Bersih: **+ RM -894.77**
- Max Drawdown: **89.79%**
- Baki Akaun: RM 105.09

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
- Jumlah Trade: 104
- Win Rate: 100.00% (104 Menang / 0 Kalah)
- Untung Bersih: **+ RM 36.08**
- Max Drawdown: **6.63%**
- Baki Akaun: RM 973.63

---

## 6. Eksperimen: Layering Skala Besar (Modal Terkawal)
**Penerangan:** Simulasi skala besar tapi modal RM 1000
**Tetapan:**
- Saiz Layer: RM 50.0 | Max Layer: 6
- Gap Layering: 5.00% | Take Profit: 2.00%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 53
- Win Rate: 100.00% (53 Menang / 0 Kalah)
- Untung Bersih: **+ RM 72.01**
- Max Drawdown: **16.58%**
- Baki Akaun: RM 918.76

---

## 7. Eksperimen: The Turtle Guard (RM10 x 30 Layer)
**Penerangan:** Beli banyak tapi saiz sangat kecil untuk tahan crash 15%.
**Tetapan:**
- Saiz Layer: RM 10.0 | Max Layer: 30
- Gap Layering: 0.50% | Take Profit: 0.50%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 453
- Win Rate: 100.00% (453 Menang / 0 Kalah)
- Untung Bersih: **+ RM 43.25**
- Max Drawdown: **18.73%**
- Baki Akaun: RM 868.57

---

## 8. Eksperimen: The Sniper (Deep Drop)
**Penerangan:** Tunggu harga jatuh 3% baru beli layer baru. TP besar 3%.
**Tetapan:**
- Saiz Layer: RM 50.0 | Max Layer: 5
- Gap Layering: 3.00% | Take Profit: 3.00%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 72
- Win Rate: 100.00% (72 Menang / 0 Kalah)
- Untung Bersih: **+ RM 73.01**
- Max Drawdown: **15.37%**
- Baki Akaun: RM 925.41

---

## 9. Eksperimen: Deep Value Layering (Moderate)
**Penerangan:** Saiz RM30, Gap 2%, TP 1.5%. Tunggu dan peram bila bawah.
**Tetapan:**
- Saiz Layer: RM 30.0 | Max Layer: 6
- Gap Layering: 2.00% | Take Profit: 1.50%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 77
- Win Rate: 100.00% (77 Menang / 0 Kalah)
- Untung Bersih: **+ RM 57.15**
- Max Drawdown: **11.29%**
- Baki Akaun: RM 950.21

---

## 10. Eksperimen: Patience is Gold (1 Layer Only)
**Penerangan:** Beli RM100 sekali, TP 5%, tiada DCA. Percaya 100% pada AI.
**Tetapan:**
- Saiz Layer: RM 100.0 | Max Layer: 1
- Gap Layering: 99.00% | Take Profit: 5.00%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 3398
- Win Rate: 19.39% (659 Menang / 2739 Kalah)
- Untung Bersih: **+ RM -900.21**
- Max Drawdown: **90.05%**
- Baki Akaun: RM 99.79

---

## 11. Eksperimen: Micro DCA Jarak Jauh
**Penerangan:** RM10, Gap 5%. Beli bila betul-betul jatuh teruk.
**Tetapan:**
- Saiz Layer: RM 10.0 | Max Layer: 10
- Gap Layering: 5.00% | Take Profit: 2.00%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 53
- Win Rate: 100.00% (53 Menang / 0 Kalah)
- Untung Bersih: **+ RM 14.40**
- Max Drawdown: **5.48%**
- Baki Akaun: RM 969.37

---

## 12. Eksperimen: High Frequency Scalping (0.2% TP)
**Penerangan:** TP sangat ketat (0.2%) untuk trade beribu kali setahun.
**Tetapan:**
- Saiz Layer: RM 20.0 | Max Layer: 10
- Gap Layering: 0.50% | Take Profit: 0.20%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 707
- Win Rate: 52.33% (370 Menang / 337 Kalah)
- Untung Bersih: **+ RM 10.53**
- Max Drawdown: **13.56%**
- Baki Akaun: RM 886.15

---

## 13. Eksperimen: Machine Gun Scalper (Gap 0.3%)
**Penerangan:** Beli setiap 0.3% jatuh. RM10 per layer.
**Tetapan:**
- Saiz Layer: RM 10.0 | Max Layer: 15
- Gap Layering: 0.30% | Take Profit: 0.40%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 421
- Win Rate: 100.00% (421 Menang / 0 Kalah)
- Untung Bersih: **+ RM 30.50**
- Max Drawdown: **9.96%**
- Baki Akaun: RM 937.31

---

## 14. Eksperimen: Mid-Frequency Trailing (0.5% Act)
**Penerangan:** Bila untung 0.5%, buka Trailing Stop 0.1% untuk kejar harga.
**Tetapan:**
- Saiz Layer: RM 20.0 | Max Layer: 8
- Gap Layering: 0.80% | Take Profit: 99.00%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 308
- Win Rate: 96.43% (297 Menang / 11 Kalah)
- Untung Bersih: **+ RM 43.52**
- Max Drawdown: **10.31%**
- Baki Akaun: RM 946.53

---

## 15. Eksperimen: Scalp & Run (RM50, TP 0.4%)
**Penerangan:** Modal besar sikit (RM50), tapi cepat lari (TP 0.4%).
**Tetapan:**
- Saiz Layer: RM 50.0 | Max Layer: 5
- Gap Layering: 0.50% | Take Profit: 0.40%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 240
- Win Rate: 100.00% (240 Menang / 0 Kalah)
- Untung Bersih: **+ RM 61.74**
- Max Drawdown: **16.26%**
- Baki Akaun: RM 904.57

---

## 16. Eksperimen: Heavy Scalping (RM100, 3 Layers)
**Penerangan:** Trade berat tapi pantas.
**Tetapan:**
- Saiz Layer: RM 100.0 | Max Layer: 3
- Gap Layering: 1.00% | Take Profit: 0.50%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 169
- Win Rate: 100.00% (169 Menang / 0 Kalah)
- Untung Bersih: **+ RM 91.06**
- Max Drawdown: **19.03%**
- Baki Akaun: RM 901.85

---

## 17. Eksperimen: Aggressive Micro Martingale (5 Lapis)
**Penerangan:** Mula dengan RM5 sahaja, TP ketat 0.3%. Max Exposure RM155.
**Tetapan:**
- Saiz Layer: RM 5.0 | Max Layer: 5
- Gap Layering: 1.00% | Take Profit: 0.30%
- Martingale: True | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 345
- Win Rate: 100.00% (345 Menang / 0 Kalah)
- Untung Bersih: **+ RM 4.11**
- Max Drawdown: **1.71%**
- Baki Akaun: RM 988.49

---

## 18. Eksperimen: Wide Gap Martingale (Anti-Crash)
**Penerangan:** Martingale gandaan RM10 (10,20,40,80) tapi hanya beli setiap kali jatuh 5%!
**Tetapan:**
- Saiz Layer: RM 10.0 | Max Layer: 4
- Gap Layering: 5.00% | Take Profit: 1.00%
- Martingale: True | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 99
- Win Rate: 100.00% (99 Menang / 0 Kalah)
- Untung Bersih: **+ RM 10.67**
- Max Drawdown: **2.60%**
- Baki Akaun: RM 987.14

---

## 19. Eksperimen: Fast Recovery Martingale (RM10, 4 Lapis)
**Penerangan:** Gap kecil 0.8% tapi ganda cepat untuk pulih.
**Tetapan:**
- Saiz Layer: RM 10.0 | Max Layer: 4
- Gap Layering: 0.80% | Take Profit: 0.50%
- Martingale: True | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 186
- Win Rate: 100.00% (186 Menang / 0 Kalah)
- Untung Bersih: **+ RM 11.26**
- Max Drawdown: **2.73%**
- Baki Akaun: RM 986.18

---

## 20. Eksperimen: High Risk Martingale (RM20, 5 Lapis)
**Penerangan:** Max exposure RM620. Untung besar tapi risiko tinggi.
**Tetapan:**
- Saiz Layer: RM 20.0 | Max Layer: 5
- Gap Layering: 1.00% | Take Profit: 1.00%
- Martingale: True | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 104
- Win Rate: 100.00% (104 Menang / 0 Kalah)
- Untung Bersih: **+ RM 36.08**
- Max Drawdown: **6.63%**
- Baki Akaun: RM 973.63

---

## 21. Eksperimen: Micro Frequency Martingale (RM2, 8 Lapis)
**Penerangan:** Mula dengan RM2. Gap 0.5%. Mampu cecah gandaan 128x (RM256).
**Tetapan:**
- Saiz Layer: RM 2.0 | Max Layer: 8
- Gap Layering: 0.50% | Take Profit: 0.40%
- Martingale: True | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 332
- Win Rate: 100.00% (332 Menang / 0 Kalah)
- Untung Bersih: **+ RM 3.69**
- Max Drawdown: **1.10%**
- Baki Akaun: RM 993.70

---

## 22. Eksperimen: Dynamic TP Martingale (RM5, Gap 1%)
**Penerangan:** TP membesar apabila Martingale masuk layer dalam. Gap 1%.
**Tetapan:**
- Saiz Layer: RM 5.0 | Max Layer: 5
- Gap Layering: 1.00% | Take Profit: 0.20%
- Martingale: True | Dynamic TP: True
**Keputusan:**
- Jumlah Trade: 444
- Win Rate: 99.55% (442 Menang / 2 Kalah)
- Untung Bersih: **+ RM 3.27**
- Max Drawdown: **1.71%**
- Baki Akaun: RM 987.66

---

## 23. Eksperimen: Dynamic TP Martingale (RM10, Gap 0.5%)
**Penerangan:** Layer rapat (0.5%) untuk agresif mengumpul pada kejatuhan kecil.
**Tetapan:**
- Saiz Layer: RM 10.0 | Max Layer: 4
- Gap Layering: 0.50% | Take Profit: 0.20%
- Martingale: True | Dynamic TP: True
**Keputusan:**
- Jumlah Trade: 357
- Win Rate: 99.44% (355 Menang / 2 Kalah)
- Untung Bersih: **+ RM 5.76**
- Max Drawdown: **2.75%**
- Baki Akaun: RM 980.55

---

## 24. Eksperimen: Dynamic TP Extreme Drop (Gap 3%)
**Penerangan:** Martingale yang selamat pada junaman 3% sahaja.
**Tetapan:**
- Saiz Layer: RM 10.0 | Max Layer: 4
- Gap Layering: 3.00% | Take Profit: 0.25%
- Martingale: True | Dynamic TP: True
**Keputusan:**
- Jumlah Trade: 359
- Win Rate: 99.72% (358 Menang / 1 Kalah)
- Untung Bersih: **+ RM 4.67**
- Max Drawdown: **2.66%**
- Baki Akaun: RM 980.63

---

## 25. Eksperimen: Dynamic TP Trailing Hybrid
**Penerangan:** Sistem Dynamic TP, tetapi ada Trailing Stop dilekatkan bila untung.
**Tetapan:**
- Saiz Layer: RM 10.0 | Max Layer: 4
- Gap Layering: 1.00% | Take Profit: 99.00%
- Martingale: True | Dynamic TP: True
**Keputusan:**
- Jumlah Trade: 394
- Win Rate: 99.49% (392 Menang / 2 Kalah)
- Untung Bersih: **+ RM 5.47**
- Max Drawdown: **2.74%**
- Baki Akaun: RM 980.39

---

## 26. Eksperimen: The Ultimate 6-Layer Dynamic Martingale
**Penerangan:** Mula dengan RM3. Max exposure RM189. Dynamic TP diaktifkan.
**Tetapan:**
- Saiz Layer: RM 3.0 | Max Layer: 6
- Gap Layering: 0.80% | Take Profit: 0.20%
- Martingale: True | Dynamic TP: True
**Keputusan:**
- Jumlah Trade: 513
- Win Rate: 99.61% (511 Menang / 2 Kalah)
- Untung Bersih: **+ RM 2.50**
- Max Drawdown: **1.24%**
- Baki Akaun: RM 991.23

---

## 27. Eksperimen: The Trailing Master (Gap 1%, Act 1%)
**Penerangan:** Tiada Hard TP. Trailing hidup bila untung 1%.
**Tetapan:**
- Saiz Layer: RM 15.0 | Max Layer: 10
- Gap Layering: 1.00% | Take Profit: 99.00%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 140
- Win Rate: 100.00% (140 Menang / 0 Kalah)
- Untung Bersih: **+ RM 43.92**
- Max Drawdown: **9.56%**
- Baki Akaun: RM 954.31

---

## 28. Eksperimen: Ultra Tight Trailing (Act 0.3%, Gap 0.1%)
**Penerangan:** Trailing hidup sangat awal (0.3%) untuk kunci untung segera.
**Tetapan:**
- Saiz Layer: RM 20.0 | Max Layer: 10
- Gap Layering: 0.80% | Take Profit: 99.00%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 540
- Win Rate: 61.48% (332 Menang / 208 Kalah)
- Untung Bersih: **+ RM 26.67**
- Max Drawdown: **13.02%**
- Baki Akaun: RM 906.23

---

## 29. Eksperimen: Wide Trailing (Act 2%, Gap 0.5%)
**Penerangan:** Beri ruang untuk trend membesar sebelum jual.
**Tetapan:**
- Saiz Layer: RM 10.0 | Max Layer: 15
- Gap Layering: 1.00% | Take Profit: 99.00%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 68
- Win Rate: 100.00% (68 Menang / 0 Kalah)
- Untung Bersih: **+ RM 44.41**
- Max Drawdown: **9.40%**
- Baki Akaun: RM 956.53

---

## 30. Eksperimen: Trailing Stop + Martingale (RM10, 4L)
**Penerangan:** Pulih dengan Martingale dan kejar profit dengan Trailing.
**Tetapan:**
- Saiz Layer: RM 10.0 | Max Layer: 4
- Gap Layering: 1.00% | Take Profit: 99.00%
- Martingale: True | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 217
- Win Rate: 92.17% (200 Menang / 17 Kalah)
- Untung Bersih: **+ RM 11.86**
- Max Drawdown: **2.73%**
- Baki Akaun: RM 986.78

---

## 31. Eksperimen: Deep Trailing Rescue
**Penerangan:** Layer di -3%, Trailing di 0.5%. Pertahanan kental.
**Tetapan:**
- Saiz Layer: RM 30.0 | Max Layer: 5
- Gap Layering: 3.00% | Take Profit: 99.00%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 235
- Win Rate: 92.34% (217 Menang / 18 Kalah)
- Untung Bersih: **+ RM 30.33**
- Max Drawdown: **9.64%**
- Baki Akaun: RM 941.17

---

## 32. Eksperimen: Golden Mean (RM15, 10L, 0.8% Gap, 0.6% TP)
**Penerangan:** Kesimbangan antara profit sederhana dan pertahanan.
**Tetapan:**
- Saiz Layer: RM 15.0 | Max Layer: 10
- Gap Layering: 0.80% | Take Profit: 0.60%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 232
- Win Rate: 100.00% (232 Menang / 0 Kalah)
- Untung Bersih: **+ RM 31.77**
- Max Drawdown: **9.97%**
- Baki Akaun: RM 938.93

---

## 33. Eksperimen: The Whale Imitator (RM250, 2L, 5% Gap)
**Penerangan:** Membeli saiz gergasi pada kejatuhan drastik.
**Tetapan:**
- Saiz Layer: RM 250.0 | Max Layer: 2
- Gap Layering: 5.00% | Take Profit: 2.00%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 36
- Win Rate: 100.00% (36 Menang / 0 Kalah)
- Untung Bersih: **+ RM 190.12**
- Max Drawdown: **28.89%**
- Baki Akaun: RM 878.26

---

## 34. Eksperimen: Micro Limitless (RM1, 100L, 0.2% Gap)
**Penerangan:** Saiz sekecil mungkin. Sentiasa berada dalam pasaran.
**Tetapan:**
- Saiz Layer: RM 1.0 | Max Layer: 100
- Gap Layering: 0.20% | Take Profit: 0.50%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 687
- Win Rate: 100.00% (687 Menang / 0 Kalah)
- Untung Bersih: **+ RM 11.98**
- Max Drawdown: **4.36%**
- Baki Akaun: RM 978.89

---

## 35. Eksperimen: Martingale Mega Defense (RM5, 5L, 2% Gap)
**Penerangan:** Martingale yang cuma masuk pasaran bila ada junaman merah.
**Tetapan:**
- Saiz Layer: RM 5.0 | Max Layer: 5
- Gap Layering: 2.00% | Take Profit: 0.50%
- Martingale: True | Dynamic TP: True
**Keputusan:**
- Jumlah Trade: 454
- Win Rate: 99.78% (453 Menang / 1 Kalah)
- Untung Bersih: **+ RM 3.18**
- Max Drawdown: **1.67%**
- Baki Akaun: RM 988.11

---

## 36. Eksperimen: The Final Holy Grail Candidate
**Penerangan:** RM10, 15 Layer, 0.6% Gap, Trailing 0.5% Act / 0.15% Gap. Sangat kukuh.
**Tetapan:**
- Saiz Layer: RM 10.0 | Max Layer: 15
- Gap Layering: 0.60% | Take Profit: 99.00%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 334
- Win Rate: 95.81% (320 Menang / 14 Kalah)
- Untung Bersih: **+ RM 27.23**
- Max Drawdown: **9.71%**
- Baki Akaun: RM 937.50

---

## 37. Eksperimen: High Volatility Catcher (RM20, 10L, 2% Gap)
**Penerangan:** Gap besar 2%, RM20 per layer.
**Tetapan:**
- Saiz Layer: RM 20.0 | Max Layer: 10
- Gap Layering: 2.00% | Take Profit: 1.00%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 138
- Win Rate: 100.00% (138 Menang / 0 Kalah)
- Untung Bersih: **+ RM 39.59**
- Max Drawdown: **12.48%**
- Baki Akaun: RM 923.84

---

## 38. Eksperimen: Super Fast Martingale (RM1, 10L, 0.2% Gap)
**Penerangan:** Saiz RM1 untuk main pantas dan ganda pada gap kecil.
**Tetapan:**
- Saiz Layer: RM 1.0 | Max Layer: 10
- Gap Layering: 0.20% | Take Profit: 0.30%
- Martingale: True | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 373
- Win Rate: 100.00% (373 Menang / 0 Kalah)
- Untung Bersih: **+ RM 1.55**
- Max Drawdown: **0.69%**
- Baki Akaun: RM 995.27

---

## 39. Eksperimen: AI Only No SL (Pure Trust)
**Penerangan:** Modal RM1000 main RM50 sekali tembak tiada dca, tiada sl.
**Tetapan:**
- Saiz Layer: RM 50.0 | Max Layer: 1
- Gap Layering: 99.90% | Take Profit: 1.00%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 5048
- Win Rate: 32.01% (1616 Menang / 3432 Kalah)
- Untung Bersih: **+ RM -602.58**
- Max Drawdown: **60.47%**
- Baki Akaun: RM 397.28

---

## 40. Eksperimen: Scalp + Dynamic TP Extreme (0.3% Gap)
**Penerangan:** Gabung layer pantas dan dynamic TP.
**Tetapan:**
- Saiz Layer: RM 10.0 | Max Layer: 10
- Gap Layering: 0.30% | Take Profit: 0.20%
- Martingale: False | Dynamic TP: True
**Keputusan:**
- Jumlah Trade: 592
- Win Rate: 99.32% (588 Menang / 4 Kalah)
- Untung Bersih: **+ RM 11.75**
- Max Drawdown: **6.81%**
- Baki Akaun: RM 949.15

