# REKOD KEPUTUSAN BACKTEST (INVESTMENT AI) - BTC
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
- Jumlah Trade: 2831
- Win Rate: 45.74% (1295 Menang / 1536 Kalah)
- Untung Bersih: **+ RM -337.60**
- Max Drawdown: **33.80%**
- Baki Akaun: RM 662.40

---

## 2. Eksperimen: XGBoost 'Sniper' (Konservatif & Selamat)
**Penerangan:** Probability Threshold tinggi, TP 1.0% dan SL ketat.
**Tetapan:**
- Saiz Layer: RM 50.0 | Max Layer: 1
- Gap Layering: 99.90% | Take Profit: 1.00%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 2056
- Win Rate: 29.96% (616 Menang / 1440 Kalah)
- Untung Bersih: **+ RM -262.71**
- Max Drawdown: **26.41%**
- Baki Akaun: RM 737.23

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
- Jumlah Trade: 21
- Win Rate: 100.00% (21 Menang / 0 Kalah)
- Untung Bersih: **+ RM 7.11**
- Max Drawdown: **3.82%**
- Baki Akaun: RM 976.73

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
- Untung Bersih: **+ RM 7.18**
- Max Drawdown: **9.07%**
- Baki Akaun: RM 942.22

---

## 7. Eksperimen: The Turtle Guard (RM10 x 30 Layer)
**Penerangan:** Beli banyak tapi saiz sangat kecil untuk tahan crash 15%.
**Tetapan:**
- Saiz Layer: RM 10.0 | Max Layer: 30
- Gap Layering: 0.50% | Take Profit: 0.50%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 60
- Win Rate: 100.00% (60 Menang / 0 Kalah)
- Untung Bersih: **+ RM 4.51**
- Max Drawdown: **9.83%**
- Baki Akaun: RM 930.99

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
- Untung Bersih: **+ RM 10.18**
- Max Drawdown: **8.71%**
- Baki Akaun: RM 942.90

---

## 9. Eksperimen: Deep Value Layering (Moderate)
**Penerangan:** Saiz RM30, Gap 2%, TP 1.5%. Tunggu dan peram bila bawah.
**Tetapan:**
- Saiz Layer: RM 30.0 | Max Layer: 6
- Gap Layering: 2.00% | Take Profit: 1.50%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 11
- Win Rate: 100.00% (11 Menang / 0 Kalah)
- Untung Bersih: **+ RM 6.74**
- Max Drawdown: **6.46%**
- Baki Akaun: RM 956.27

---

## 10. Eksperimen: Patience is Gold (1 Layer Only)
**Penerangan:** Beli RM100 sekali, TP 5%, tiada DCA. Percaya 100% pada AI.
**Tetapan:**
- Saiz Layer: RM 100.0 | Max Layer: 1
- Gap Layering: 99.00% | Take Profit: 5.00%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 978
- Win Rate: 18.51% (181 Menang / 797 Kalah)
- Untung Bersih: **+ RM -270.81**
- Max Drawdown: **27.69%**
- Baki Akaun: RM 730.24

---

## 11. Eksperimen: Micro DCA Jarak Jauh
**Penerangan:** RM10, Gap 5%. Beli bila betul-betul jatuh teruk.
**Tetapan:**
- Saiz Layer: RM 10.0 | Max Layer: 10
- Gap Layering: 5.00% | Take Profit: 2.00%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 11
- Win Rate: 100.00% (11 Menang / 0 Kalah)
- Untung Bersih: **+ RM 3.75**
- Max Drawdown: **2.08%**
- Baki Akaun: RM 1000.34

---

## 12. Eksperimen: High Frequency Scalping (0.2% TP)
**Penerangan:** TP sangat ketat (0.2%) untuk trade beribu kali setahun.
**Tetapan:**
- Saiz Layer: RM 20.0 | Max Layer: 10
- Gap Layering: 0.50% | Take Profit: 0.20%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 145
- Win Rate: 37.24% (54 Menang / 91 Kalah)
- Untung Bersih: **+ RM 1.09**
- Max Drawdown: **7.53%**
- Baki Akaun: RM 941.43

---

## 13. Eksperimen: Machine Gun Scalper (Gap 0.3%)
**Penerangan:** Beli setiap 0.3% jatuh. RM10 per layer.
**Tetapan:**
- Saiz Layer: RM 10.0 | Max Layer: 15
- Gap Layering: 0.30% | Take Profit: 0.40%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 82
- Win Rate: 100.00% (82 Menang / 0 Kalah)
- Untung Bersih: **+ RM 5.28**
- Max Drawdown: **5.59%**
- Baki Akaun: RM 960.89

---

## 14. Eksperimen: Mid-Frequency Trailing (0.5% Act)
**Penerangan:** Bila untung 0.5%, buka Trailing Stop 0.1% untuk kejar harga.
**Tetapan:**
- Saiz Layer: RM 20.0 | Max Layer: 8
- Gap Layering: 0.80% | Take Profit: 99.00%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 51
- Win Rate: 100.00% (51 Menang / 0 Kalah)
- Untung Bersih: **+ RM 6.47**
- Max Drawdown: **6.02%**
- Baki Akaun: RM 958.50

---

## 15. Eksperimen: Scalp & Run (RM50, TP 0.4%)
**Penerangan:** Modal besar sikit (RM50), tapi cepat lari (TP 0.4%).
**Tetapan:**
- Saiz Layer: RM 50.0 | Max Layer: 5
- Gap Layering: 0.50% | Take Profit: 0.40%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 48
- Win Rate: 100.00% (48 Menang / 0 Kalah)
- Untung Bersih: **+ RM 10.26**
- Max Drawdown: **9.56%**
- Baki Akaun: RM 933.26

---

## 16. Eksperimen: Heavy Scalping (RM100, 3 Layers)
**Penerangan:** Trade berat tapi pantas.
**Tetapan:**
- Saiz Layer: RM 100.0 | Max Layer: 3
- Gap Layering: 1.00% | Take Profit: 0.50%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 35
- Win Rate: 100.00% (35 Menang / 0 Kalah)
- Untung Bersih: **+ RM 17.87**
- Max Drawdown: **11.56%**
- Baki Akaun: RM 924.09

---

## 17. Eksperimen: Aggressive Micro Martingale (5 Lapis)
**Penerangan:** Mula dengan RM5 sahaja, TP ketat 0.3%. Max Exposure RM155.
**Tetapan:**
- Saiz Layer: RM 5.0 | Max Layer: 5
- Gap Layering: 1.00% | Take Profit: 0.30%
- Martingale: True | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 83
- Win Rate: 100.00% (83 Menang / 0 Kalah)
- Untung Bersih: **+ RM 0.65**
- Max Drawdown: **0.95%**
- Baki Akaun: RM 993.15

---

## 18. Eksperimen: Wide Gap Martingale (Anti-Crash)
**Penerangan:** Martingale gandaan RM10 (10,20,40,80) tapi hanya beli setiap kali jatuh 5%!
**Tetapan:**
- Saiz Layer: RM 10.0 | Max Layer: 4
- Gap Layering: 5.00% | Take Profit: 1.00%
- Martingale: True | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 14
- Win Rate: 100.00% (14 Menang / 0 Kalah)
- Untung Bersih: **+ RM 1.34**
- Max Drawdown: **1.37%**
- Baki Akaun: RM 991.02

---

## 19. Eksperimen: Fast Recovery Martingale (RM10, 4 Lapis)
**Penerangan:** Gap kecil 0.8% tapi ganda cepat untuk pulih.
**Tetapan:**
- Saiz Layer: RM 10.0 | Max Layer: 4
- Gap Layering: 0.80% | Take Profit: 0.50%
- Martingale: True | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 44
- Win Rate: 100.00% (44 Menang / 0 Kalah)
- Untung Bersih: **+ RM 2.52**
- Max Drawdown: **1.55%**
- Baki Akaun: RM 990.07

---

## 20. Eksperimen: High Risk Martingale (RM20, 5 Lapis)
**Penerangan:** Max exposure RM620. Untung besar tapi risiko tinggi.
**Tetapan:**
- Saiz Layer: RM 20.0 | Max Layer: 5
- Gap Layering: 1.00% | Take Profit: 1.00%
- Martingale: True | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 21
- Win Rate: 100.00% (21 Menang / 0 Kalah)
- Untung Bersih: **+ RM 7.11**
- Max Drawdown: **3.82%**
- Baki Akaun: RM 976.73

---

## 21. Eksperimen: Micro Frequency Martingale (RM2, 8 Lapis)
**Penerangan:** Mula dengan RM2. Gap 0.5%. Mampu cecah gandaan 128x (RM256).
**Tetapan:**
- Saiz Layer: RM 2.0 | Max Layer: 8
- Gap Layering: 0.50% | Take Profit: 0.40%
- Martingale: True | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 72
- Win Rate: 100.00% (72 Menang / 0 Kalah)
- Untung Bersih: **+ RM 0.71**
- Max Drawdown: **0.61%**
- Baki Akaun: RM 995.88

---

## 22. Eksperimen: Dynamic TP Martingale (RM5, Gap 1%)
**Penerangan:** TP membesar apabila Martingale masuk layer dalam. Gap 1%.
**Tetapan:**
- Saiz Layer: RM 5.0 | Max Layer: 5
- Gap Layering: 1.00% | Take Profit: 0.20%
- Martingale: True | Dynamic TP: True
**Keputusan:**
- Jumlah Trade: 95
- Win Rate: 100.00% (95 Menang / 0 Kalah)
- Untung Bersih: **+ RM 0.43**
- Max Drawdown: **0.95%**
- Baki Akaun: RM 992.93

---

## 23. Eksperimen: Dynamic TP Martingale (RM10, Gap 0.5%)
**Penerangan:** Layer rapat (0.5%) untuk agresif mengumpul pada kejatuhan kecil.
**Tetapan:**
- Saiz Layer: RM 10.0 | Max Layer: 4
- Gap Layering: 0.50% | Take Profit: 0.20%
- Martingale: True | Dynamic TP: True
**Keputusan:**
- Jumlah Trade: 68
- Win Rate: 100.00% (68 Menang / 0 Kalah)
- Untung Bersih: **+ RM 0.84**
- Max Drawdown: **1.57%**
- Baki Akaun: RM 988.24

---

## 24. Eksperimen: Dynamic TP Extreme Drop (Gap 3%)
**Penerangan:** Martingale yang selamat pada junaman 3% sahaja.
**Tetapan:**
- Saiz Layer: RM 10.0 | Max Layer: 4
- Gap Layering: 3.00% | Take Profit: 0.25%
- Martingale: True | Dynamic TP: True
**Keputusan:**
- Jumlah Trade: 59
- Win Rate: 100.00% (59 Menang / 0 Kalah)
- Untung Bersih: **+ RM 0.47**
- Max Drawdown: **1.46%**
- Baki Akaun: RM 989.06

---

## 25. Eksperimen: Dynamic TP Trailing Hybrid
**Penerangan:** Sistem Dynamic TP, tetapi ada Trailing Stop dilekatkan bila untung.
**Tetapan:**
- Saiz Layer: RM 10.0 | Max Layer: 4
- Gap Layering: 1.00% | Take Profit: 99.00%
- Martingale: True | Dynamic TP: True
**Keputusan:**
- Jumlah Trade: 84
- Win Rate: 100.00% (84 Menang / 0 Kalah)
- Untung Bersih: **+ RM 0.78**
- Max Drawdown: **1.53%**
- Baki Akaun: RM 988.61

---

## 26. Eksperimen: The Ultimate 6-Layer Dynamic Martingale
**Penerangan:** Mula dengan RM3. Max exposure RM189. Dynamic TP diaktifkan.
**Tetapan:**
- Saiz Layer: RM 3.0 | Max Layer: 6
- Gap Layering: 0.80% | Take Profit: 0.20%
- Martingale: True | Dynamic TP: True
**Keputusan:**
- Jumlah Trade: 105
- Win Rate: 100.00% (105 Menang / 0 Kalah)
- Untung Bersih: **+ RM 0.36**
- Max Drawdown: **0.68%**
- Baki Akaun: RM 994.97

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
- Untung Bersih: **+ RM 5.93**
- Max Drawdown: **5.38%**
- Baki Akaun: RM 963.96

---

## 28. Eksperimen: Ultra Tight Trailing (Act 0.3%, Gap 0.1%)
**Penerangan:** Trailing hidup sangat awal (0.3%) untuk kunci untung segera.
**Tetapan:**
- Saiz Layer: RM 20.0 | Max Layer: 10
- Gap Layering: 0.80% | Take Profit: 99.00%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 92
- Win Rate: 57.61% (53 Menang / 39 Kalah)
- Untung Bersih: **+ RM 3.56**
- Max Drawdown: **7.32%**
- Baki Akaun: RM 946.02

---

## 29. Eksperimen: Wide Trailing (Act 2%, Gap 0.5%)
**Penerangan:** Beri ruang untuk trend membesar sebelum jual.
**Tetapan:**
- Saiz Layer: RM 10.0 | Max Layer: 15
- Gap Layering: 1.00% | Take Profit: 99.00%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 10
- Win Rate: 100.00% (10 Menang / 0 Kalah)
- Untung Bersih: **+ RM 4.87**
- Max Drawdown: **5.09%**
- Baki Akaun: RM 966.33

---

## 30. Eksperimen: Trailing Stop + Martingale (RM10, 4L)
**Penerangan:** Pulih dengan Martingale dan kejar profit dengan Trailing.
**Tetapan:**
- Saiz Layer: RM 10.0 | Max Layer: 4
- Gap Layering: 1.00% | Take Profit: 99.00%
- Martingale: True | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 50
- Win Rate: 100.00% (50 Menang / 0 Kalah)
- Untung Bersih: **+ RM 2.50**
- Max Drawdown: **1.55%**
- Baki Akaun: RM 990.12

---

## 31. Eksperimen: Deep Trailing Rescue
**Penerangan:** Layer di -3%, Trailing di 0.5%. Pertahanan kental.
**Tetapan:**
- Saiz Layer: RM 30.0 | Max Layer: 5
- Gap Layering: 3.00% | Take Profit: 99.00%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 35
- Win Rate: 100.00% (35 Menang / 0 Kalah)
- Untung Bersih: **+ RM 3.55**
- Max Drawdown: **5.28%**
- Baki Akaun: RM 962.85

---

## 32. Eksperimen: Golden Mean (RM15, 10L, 0.8% Gap, 0.6% TP)
**Penerangan:** Kesimbangan antara profit sederhana dan pertahanan.
**Tetapan:**
- Saiz Layer: RM 15.0 | Max Layer: 10
- Gap Layering: 0.80% | Take Profit: 0.60%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 44
- Win Rate: 100.00% (44 Menang / 0 Kalah)
- Untung Bersih: **+ RM 5.49**
- Max Drawdown: **5.56%**
- Baki Akaun: RM 961.52

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
- Untung Bersih: **+ RM 35.91**
- Max Drawdown: **18.26%**
- Baki Akaun: RM 886.70

---

## 34. Eksperimen: Micro Limitless (RM1, 100L, 0.2% Gap)
**Penerangan:** Saiz sekecil mungkin. Sentiasa berada dalam pasaran.
**Tetapan:**
- Saiz Layer: RM 1.0 | Max Layer: 100
- Gap Layering: 0.20% | Take Profit: 0.50%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 80
- Win Rate: 100.00% (80 Menang / 0 Kalah)
- Untung Bersih: **+ RM 1.36**
- Max Drawdown: **2.68%**
- Baki Akaun: RM 995.55

---

## 35. Eksperimen: Martingale Mega Defense (RM5, 5L, 2% Gap)
**Penerangan:** Martingale yang cuma masuk pasaran bila ada junaman merah.
**Tetapan:**
- Saiz Layer: RM 5.0 | Max Layer: 5
- Gap Layering: 2.00% | Take Profit: 0.50%
- Martingale: True | Dynamic TP: True
**Keputusan:**
- Jumlah Trade: 59
- Win Rate: 98.31% (58 Menang / 1 Kalah)
- Untung Bersih: **+ RM 0.24**
- Max Drawdown: **0.91%**
- Baki Akaun: RM 993.17

---

## 36. Eksperimen: The Final Holy Grail Candidate
**Penerangan:** RM10, 15 Layer, 0.6% Gap, Trailing 0.5% Act / 0.15% Gap. Sangat kukuh.
**Tetapan:**
- Saiz Layer: RM 10.0 | Max Layer: 15
- Gap Layering: 0.60% | Take Profit: 99.00%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 55
- Win Rate: 100.00% (55 Menang / 0 Kalah)
- Untung Bersih: **+ RM 4.68**
- Max Drawdown: **5.44%**
- Baki Akaun: RM 962.12

---

## 37. Eksperimen: High Volatility Catcher (RM20, 10L, 2% Gap)
**Penerangan:** Gap besar 2%, RM20 per layer.
**Tetapan:**
- Saiz Layer: RM 20.0 | Max Layer: 10
- Gap Layering: 2.00% | Take Profit: 1.00%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 19
- Win Rate: 100.00% (19 Menang / 0 Kalah)
- Untung Bersih: **+ RM 4.74**
- Max Drawdown: **6.63%**
- Baki Akaun: RM 955.05

---

## 38. Eksperimen: Super Fast Martingale (RM1, 10L, 0.2% Gap)
**Penerangan:** Saiz RM1 untuk main pantas dan ganda pada gap kecil.
**Tetapan:**
- Saiz Layer: RM 1.0 | Max Layer: 10
- Gap Layering: 0.20% | Take Profit: 0.30%
- Martingale: True | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 103
- Win Rate: 100.00% (103 Menang / 0 Kalah)
- Untung Bersih: **+ RM 0.39**
- Max Drawdown: **0.38%**
- Baki Akaun: RM 997.33

---

## 39. Eksperimen: AI Only No SL (Pure Trust)
**Penerangan:** Modal RM1000 main RM50 sekali tembak tiada dca, tiada sl.
**Tetapan:**
- Saiz Layer: RM 50.0 | Max Layer: 1
- Gap Layering: 99.90% | Take Profit: 1.00%
- Martingale: False | Dynamic TP: False
**Keputusan:**
- Jumlah Trade: 1728
- Win Rate: 31.42% (543 Menang / 1185 Kalah)
- Untung Bersih: **+ RM -203.56**
- Max Drawdown: **20.50%**
- Baki Akaun: RM 796.44

---

## 40. Eksperimen: Scalp + Dynamic TP Extreme (0.3% Gap)
**Penerangan:** Gabung layer pantas dan dynamic TP.
**Tetapan:**
- Saiz Layer: RM 10.0 | Max Layer: 10
- Gap Layering: 0.30% | Take Profit: 0.20%
- Martingale: False | Dynamic TP: True
**Keputusan:**
- Jumlah Trade: 122
- Win Rate: 98.36% (120 Menang / 2 Kalah)
- Untung Bersih: **+ RM 2.26**
- Max Drawdown: **3.81%**
- Baki Akaun: RM 971.91

