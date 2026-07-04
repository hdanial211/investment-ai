# REKOD KEPUTUSAN BACKTEST (INVESTMENT AI) - XRP
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
- Jumlah Trade: 4508
- Win Rate: 45.98% (2073 Menang / 2435 Kalah)
- Untung Bersih: **+ RM -538.16**
- Max Drawdown: **53.88%**
- Baki Akaun: RM 461.57

---

## 2. Eksperimen: XGBoost 'Sniper' (Konservatif & Selamat)
**Penerangan:** Probability Threshold tinggi, TP 1.0% dan SL ketat.
**Tetapan:**
- Saiz Layer: RM 50.0 | Max Layer: 1
- Gap Layering: 99.90% | Take Profit: 1.00%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 2673
- Win Rate: 31.20% (834 Menang / 1839 Kalah)
- Untung Bersih: **+ RM -328.23**
- Max Drawdown: **32.95%**
- Baki Akaun: RM 671.50

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
- Jumlah Trade: 30
- Win Rate: 100.00% (30 Menang / 0 Kalah)
- Untung Bersih: **+ RM 7.33**
- Max Drawdown: **5.57%**
- Baki Akaun: RM 959.56

---

## 6. Eksperimen: Layering Skala Besar (Modal Terkawal)
**Penerangan:** Simulasi skala besar tapi modal RM 1000
**Tetapan:**
- Saiz Layer: RM 50.0 | Max Layer: 6
- Gap Layering: 5.00% | Take Profit: 2.00%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 14
- Win Rate: 100.00% (14 Menang / 0 Kalah)
- Untung Bersih: **+ RM 14.98**
- Max Drawdown: **14.77%**
- Baki Akaun: RM 891.52

---

## 7. Eksperimen: The Turtle Guard (RM10 x 30 Layer)
**Penerangan:** Beli banyak tapi saiz sangat kecil untuk tahan crash 15%.
**Tetapan:**
- Saiz Layer: RM 10.0 | Max Layer: 30
- Gap Layering: 0.50% | Take Profit: 0.50%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 106
- Win Rate: 100.00% (106 Menang / 0 Kalah)
- Untung Bersih: **+ RM 7.65**
- Max Drawdown: **13.63%**
- Baki Akaun: RM 898.85

---

## 8. Eksperimen: The Sniper (Deep Drop)
**Penerangan:** Tunggu harga jatuh 3% baru beli layer baru. TP besar 3%.
**Tetapan:**
- Saiz Layer: RM 50.0 | Max Layer: 5
- Gap Layering: 3.00% | Take Profit: 3.00%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 24
- Win Rate: 100.00% (24 Menang / 0 Kalah)
- Untung Bersih: **+ RM 16.00**
- Max Drawdown: **13.19%**
- Baki Akaun: RM 903.68

---

## 9. Eksperimen: Deep Value Layering (Moderate)
**Penerangan:** Saiz RM30, Gap 2%, TP 1.5%. Tunggu dan peram bila bawah.
**Tetapan:**
- Saiz Layer: RM 30.0 | Max Layer: 6
- Gap Layering: 2.00% | Take Profit: 1.50%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 22
- Win Rate: 100.00% (22 Menang / 0 Kalah)
- Untung Bersih: **+ RM 12.37**
- Max Drawdown: **9.59%**
- Baki Akaun: RM 930.64

---

## 10. Eksperimen: Patience is Gold (1 Layer Only)
**Penerangan:** Beli RM100 sekali, TP 5%, tiada DCA. Percaya 100% pada AI.
**Tetapan:**
- Saiz Layer: RM 100.0 | Max Layer: 1
- Gap Layering: 99.00% | Take Profit: 5.00%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 1435
- Win Rate: 18.61% (267 Menang / 1168 Kalah)
- Untung Bersih: **+ RM -383.15**
- Max Drawdown: **38.96%**
- Baki Akaun: RM 616.31

---

## 11. Eksperimen: Micro DCA Jarak Jauh
**Penerangan:** RM10, Gap 5%. Beli bila betul-betul jatuh teruk.
**Tetapan:**
- Saiz Layer: RM 10.0 | Max Layer: 10
- Gap Layering: 5.00% | Take Profit: 2.00%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 14
- Win Rate: 100.00% (14 Menang / 0 Kalah)
- Untung Bersih: **+ RM 3.00**
- Max Drawdown: **4.34%**
- Baki Akaun: RM 969.42

---

## 12. Eksperimen: High Frequency Scalping (0.2% TP)
**Penerangan:** TP sangat ketat (0.2%) untuk trade beribu kali setahun.
**Tetapan:**
- Saiz Layer: RM 20.0 | Max Layer: 10
- Gap Layering: 0.50% | Take Profit: 0.20%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 214
- Win Rate: 59.81% (128 Menang / 86 Kalah)
- Untung Bersih: **+ RM 2.38**
- Max Drawdown: **10.54%**
- Baki Akaun: RM 913.39

---

## 13. Eksperimen: Machine Gun Scalper (Gap 0.3%)
**Penerangan:** Beli setiap 0.3% jatuh. RM10 per layer.
**Tetapan:**
- Saiz Layer: RM 10.0 | Max Layer: 15
- Gap Layering: 0.30% | Take Profit: 0.40%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 136
- Win Rate: 100.00% (136 Menang / 0 Kalah)
- Untung Bersih: **+ RM 7.19**
- Max Drawdown: **7.99%**
- Baki Akaun: RM 939.03

---

## 14. Eksperimen: Mid-Frequency Trailing (0.5% Act)
**Penerangan:** Bila untung 0.5%, buka Trailing Stop 0.1% untuk kejar harga.
**Tetapan:**
- Saiz Layer: RM 20.0 | Max Layer: 8
- Gap Layering: 0.80% | Take Profit: 99.00%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 77
- Win Rate: 98.70% (76 Menang / 1 Kalah)
- Untung Bersih: **+ RM 7.99**
- Max Drawdown: **8.46%**
- Baki Akaun: RM 935.86

---

## 15. Eksperimen: Scalp & Run (RM50, TP 0.4%)
**Penerangan:** Modal besar sikit (RM50), tapi cepat lari (TP 0.4%).
**Tetapan:**
- Saiz Layer: RM 50.0 | Max Layer: 5
- Gap Layering: 0.50% | Take Profit: 0.40%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 105
- Win Rate: 100.00% (105 Menang / 0 Kalah)
- Untung Bersih: **+ RM 21.26**
- Max Drawdown: **13.76%**
- Baki Akaun: RM 900.36

---

## 16. Eksperimen: Heavy Scalping (RM100, 3 Layers)
**Penerangan:** Trade berat tapi pantas.
**Tetapan:**
- Saiz Layer: RM 100.0 | Max Layer: 3
- Gap Layering: 1.00% | Take Profit: 0.50%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 61
- Win Rate: 100.00% (61 Menang / 0 Kalah)
- Untung Bersih: **+ RM 26.42**
- Max Drawdown: **16.41%**
- Baki Akaun: RM 881.37

---

## 17. Eksperimen: Aggressive Micro Martingale (5 Lapis)
**Penerangan:** Mula dengan RM5 sahaja, TP ketat 0.3%. Max Exposure RM155.
**Tetapan:**
- Saiz Layer: RM 5.0 | Max Layer: 5
- Gap Layering: 1.00% | Take Profit: 0.30%
- Martingale: True | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 127
- Win Rate: 100.00% (127 Menang / 0 Kalah)
- Untung Bersih: **+ RM 1.21**
- Max Drawdown: **4.38%**
- Baki Akaun: RM 963.61

---

## 18. Eksperimen: Wide Gap Martingale (Anti-Crash)
**Penerangan:** Martingale gandaan RM10 (10,20,40,80) tapi hanya beli setiap kali jatuh 5%!
**Tetapan:**
- Saiz Layer: RM 10.0 | Max Layer: 4
- Gap Layering: 5.00% | Take Profit: 1.00%
- Martingale: True | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 32
- Win Rate: 100.00% (32 Menang / 0 Kalah)
- Untung Bersih: **+ RM 2.92**
- Max Drawdown: **2.62%**
- Baki Akaun: RM 980.80

---

## 19. Eksperimen: Fast Recovery Martingale (RM10, 4 Lapis)
**Penerangan:** Gap kecil 0.8% tapi ganda cepat untuk pulih.
**Tetapan:**
- Saiz Layer: RM 10.0 | Max Layer: 4
- Gap Layering: 0.80% | Take Profit: 0.50%
- Martingale: True | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 73
- Win Rate: 100.00% (73 Menang / 0 Kalah)
- Untung Bersih: **+ RM 4.69**
- Max Drawdown: **8.23%**
- Baki Akaun: RM 933.92

---

## 20. Eksperimen: High Risk Martingale (RM20, 5 Lapis)
**Penerangan:** Max exposure RM620. Untung besar tapi risiko tinggi.
**Tetapan:**
- Saiz Layer: RM 20.0 | Max Layer: 5
- Gap Layering: 1.00% | Take Profit: 1.00%
- Martingale: True | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 31
- Win Rate: 100.00% (31 Menang / 0 Kalah)
- Untung Bersih: **+ RM 11.37**
- Max Drawdown: **17.39%**
- Baki Akaun: RM 861.01

---

## 21. Eksperimen: Micro Frequency Martingale (RM2, 8 Lapis)
**Penerangan:** Mula dengan RM2. Gap 0.5%. Mampu cecah gandaan 128x (RM256).
**Tetapan:**
- Saiz Layer: RM 2.0 | Max Layer: 8
- Gap Layering: 0.50% | Take Profit: 0.40%
- Martingale: True | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 135
- Win Rate: 100.00% (135 Menang / 0 Kalah)
- Untung Bersih: **+ RM 1.81**
- Max Drawdown: **0.85%**
- Baki Akaun: RM 994.64

---

## 22. Eksperimen: Dynamic TP Martingale (RM5, Gap 1%)
**Penerangan:** TP membesar apabila Martingale masuk layer dalam. Gap 1%.
**Tetapan:**
- Saiz Layer: RM 5.0 | Max Layer: 5
- Gap Layering: 1.00% | Take Profit: 0.20%
- Martingale: True | Dynamic TP: True
**Keputusan:**
- Jumlah Trade: 154
- Win Rate: 97.40% (150 Menang / 4 Kalah)
- Untung Bersih: **+ RM 1.00**
- Max Drawdown: **1.33%**
- Baki Akaun: RM 989.78

---

## 23. Eksperimen: Dynamic TP Martingale (RM10, Gap 0.5%)
**Penerangan:** Layer rapat (0.5%) untuk agresif mengumpul pada kejatuhan kecil.
**Tetapan:**
- Saiz Layer: RM 10.0 | Max Layer: 4
- Gap Layering: 0.50% | Take Profit: 0.20%
- Martingale: True | Dynamic TP: True
**Keputusan:**
- Jumlah Trade: 165
- Win Rate: 96.97% (160 Menang / 5 Kalah)
- Untung Bersih: **+ RM 3.97**
- Max Drawdown: **2.16%**
- Baki Akaun: RM 985.45

---

## 24. Eksperimen: Dynamic TP Extreme Drop (Gap 3%)
**Penerangan:** Martingale yang selamat pada junaman 3% sahaja.
**Tetapan:**
- Saiz Layer: RM 10.0 | Max Layer: 4
- Gap Layering: 3.00% | Take Profit: 0.25%
- Martingale: True | Dynamic TP: True
**Keputusan:**
- Jumlah Trade: 89
- Win Rate: 96.63% (86 Menang / 3 Kalah)
- Untung Bersih: **+ RM 0.94**
- Max Drawdown: **3.22%**
- Baki Akaun: RM 973.61

---

## 25. Eksperimen: Dynamic TP Trailing Hybrid
**Penerangan:** Sistem Dynamic TP, tetapi ada Trailing Stop dilekatkan bila untung.
**Tetapan:**
- Saiz Layer: RM 10.0 | Max Layer: 4
- Gap Layering: 1.00% | Take Profit: 99.00%
- Martingale: True | Dynamic TP: True
**Keputusan:**
- Jumlah Trade: 152
- Win Rate: 97.37% (148 Menang / 4 Kalah)
- Untung Bersih: **+ RM 1.96**
- Max Drawdown: **2.14%**
- Baki Akaun: RM 983.88

---

## 26. Eksperimen: The Ultimate 6-Layer Dynamic Martingale
**Penerangan:** Mula dengan RM3. Max exposure RM189. Dynamic TP diaktifkan.
**Tetapan:**
- Saiz Layer: RM 3.0 | Max Layer: 6
- Gap Layering: 0.80% | Take Profit: 0.20%
- Martingale: True | Dynamic TP: True
**Keputusan:**
- Jumlah Trade: 164
- Win Rate: 97.56% (160 Menang / 4 Kalah)
- Untung Bersih: **+ RM 1.04**
- Max Drawdown: **0.97%**
- Baki Akaun: RM 992.83

---

## 27. Eksperimen: The Trailing Master (Gap 1%, Act 1%)
**Penerangan:** Tiada Hard TP. Trailing hidup bila untung 1%.
**Tetapan:**
- Saiz Layer: RM 15.0 | Max Layer: 10
- Gap Layering: 1.00% | Take Profit: 99.00%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 33
- Win Rate: 100.00% (33 Menang / 0 Kalah)
- Untung Bersih: **+ RM 8.30**
- Max Drawdown: **8.01%**
- Baki Akaun: RM 939.88

---

## 28. Eksperimen: Ultra Tight Trailing (Act 0.3%, Gap 0.1%)
**Penerangan:** Trailing hidup sangat awal (0.3%) untuk kunci untung segera.
**Tetapan:**
- Saiz Layer: RM 20.0 | Max Layer: 10
- Gap Layering: 0.80% | Take Profit: 99.00%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 126
- Win Rate: 64.29% (81 Menang / 45 Kalah)
- Untung Bersih: **+ RM 6.03**
- Max Drawdown: **10.51%**
- Baki Akaun: RM 916.82

---

## 29. Eksperimen: Wide Trailing (Act 2%, Gap 0.5%)
**Penerangan:** Beri ruang untuk trend membesar sebelum jual.
**Tetapan:**
- Saiz Layer: RM 10.0 | Max Layer: 15
- Gap Layering: 1.00% | Take Profit: 99.00%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 17
- Win Rate: 100.00% (17 Menang / 0 Kalah)
- Untung Bersih: **+ RM 5.46**
- Max Drawdown: **7.78%**
- Baki Akaun: RM 940.32

---

## 30. Eksperimen: Trailing Stop + Martingale (RM10, 4L)
**Penerangan:** Pulih dengan Martingale dan kejar profit dengan Trailing.
**Tetapan:**
- Saiz Layer: RM 10.0 | Max Layer: 4
- Gap Layering: 1.00% | Take Profit: 99.00%
- Martingale: True | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 63
- Win Rate: 92.06% (58 Menang / 5 Kalah)
- Untung Bersih: **+ RM 2.76**
- Max Drawdown: **8.23%**
- Baki Akaun: RM 932.18

---

## 31. Eksperimen: Deep Trailing Rescue
**Penerangan:** Layer di -3%, Trailing di 0.5%. Pertahanan kental.
**Tetapan:**
- Saiz Layer: RM 30.0 | Max Layer: 5
- Gap Layering: 3.00% | Take Profit: 99.00%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 55
- Win Rate: 90.91% (50 Menang / 5 Kalah)
- Untung Bersih: **+ RM 6.87**
- Max Drawdown: **7.92%**
- Baki Akaun: RM 939.61

---

## 32. Eksperimen: Golden Mean (RM15, 10L, 0.8% Gap, 0.6% TP)
**Penerangan:** Kesimbangan antara profit sederhana dan pertahanan.
**Tetapan:**
- Saiz Layer: RM 15.0 | Max Layer: 10
- Gap Layering: 0.80% | Take Profit: 0.60%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 60
- Win Rate: 100.00% (60 Menang / 0 Kalah)
- Untung Bersih: **+ RM 7.28**
- Max Drawdown: **7.89%**
- Baki Akaun: RM 940.28

---

## 33. Eksperimen: The Whale Imitator (RM250, 2L, 5% Gap)
**Penerangan:** Membeli saiz gergasi pada kejatuhan drastik.
**Tetapan:**
- Saiz Layer: RM 250.0 | Max Layer: 2
- Gap Layering: 5.00% | Take Profit: 2.00%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 14
- Win Rate: 100.00% (14 Menang / 0 Kalah)
- Untung Bersih: **+ RM 74.89**
- Max Drawdown: **25.70%**
- Baki Akaun: RM 838.90

---

## 34. Eksperimen: Micro Limitless (RM1, 100L, 0.2% Gap)
**Penerangan:** Saiz sekecil mungkin. Sentiasa berada dalam pasaran.
**Tetapan:**
- Saiz Layer: RM 1.0 | Max Layer: 100
- Gap Layering: 0.20% | Take Profit: 0.50%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 316
- Win Rate: 100.00% (316 Menang / 0 Kalah)
- Untung Bersih: **+ RM 5.88**
- Max Drawdown: **2.77%**
- Baki Akaun: RM 999.30

---

## 35. Eksperimen: Martingale Mega Defense (RM5, 5L, 2% Gap)
**Penerangan:** Martingale yang cuma masuk pasaran bila ada junaman merah.
**Tetapan:**
- Saiz Layer: RM 5.0 | Max Layer: 5
- Gap Layering: 2.00% | Take Profit: 0.50%
- Martingale: True | Dynamic TP: True
**Keputusan:**
- Jumlah Trade: 107
- Win Rate: 98.13% (105 Menang / 2 Kalah)
- Untung Bersih: **+ RM 0.58**
- Max Drawdown: **1.63%**
- Baki Akaun: RM 986.70

---

## 36. Eksperimen: The Final Holy Grail Candidate
**Penerangan:** RM10, 15 Layer, 0.6% Gap, Trailing 0.5% Act / 0.15% Gap. Sangat kukuh.
**Tetapan:**
- Saiz Layer: RM 10.0 | Max Layer: 15
- Gap Layering: 0.60% | Take Profit: 99.00%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 97
- Win Rate: 94.85% (92 Menang / 5 Kalah)
- Untung Bersih: **+ RM 5.92**
- Max Drawdown: **7.84%**
- Baki Akaun: RM 939.61

---

## 37. Eksperimen: High Volatility Catcher (RM20, 10L, 2% Gap)
**Penerangan:** Gap besar 2%, RM20 per layer.
**Tetapan:**
- Saiz Layer: RM 20.0 | Max Layer: 10
- Gap Layering: 2.00% | Take Profit: 1.00%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 32
- Win Rate: 100.00% (32 Menang / 0 Kalah)
- Untung Bersih: **+ RM 6.78**
- Max Drawdown: **10.36%**
- Baki Akaun: RM 919.22

---

## 38. Eksperimen: Super Fast Martingale (RM1, 10L, 0.2% Gap)
**Penerangan:** Saiz RM1 untuk main pantas dan ganda pada gap kecil.
**Tetapan:**
- Saiz Layer: RM 1.0 | Max Layer: 10
- Gap Layering: 0.20% | Take Profit: 0.30%
- Martingale: True | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 173
- Win Rate: 100.00% (173 Menang / 0 Kalah)
- Untung Bersih: **+ RM 2.56**
- Max Drawdown: **0.77%**
- Baki Akaun: RM 997.95

---

## 39. Eksperimen: AI Only No SL (Pure Trust)
**Penerangan:** Modal RM1000 main RM50 sekali tembak tiada dca, tiada sl.
**Tetapan:**
- Saiz Layer: RM 50.0 | Max Layer: 1
- Gap Layering: 99.90% | Take Profit: 1.00%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 2673
- Win Rate: 31.20% (834 Menang / 1839 Kalah)
- Untung Bersih: **+ RM -328.23**
- Max Drawdown: **32.95%**
- Baki Akaun: RM 671.50

---

## 40. Eksperimen: Scalp + Dynamic TP Extreme (0.3% Gap)
**Penerangan:** Gabung layer pantas dan dynamic TP.
**Tetapan:**
- Saiz Layer: RM 10.0 | Max Layer: 10
- Gap Layering: 0.30% | Take Profit: 0.20%
- Martingale: False | Dynamic TP: True
**Keputusan:**
- Jumlah Trade: 181
- Win Rate: 98.90% (179 Menang / 2 Kalah)
- Untung Bersih: **+ RM 4.03**
- Max Drawdown: **5.39%**
- Baki Akaun: RM 958.07

