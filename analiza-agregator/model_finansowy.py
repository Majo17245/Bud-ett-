# Uproszczony model finansowy agregatora ofert pracy - wszystkie wartości to SZACUNKI (PLN).
# Uruchomienie: python3 model_finansowy.py
# Zmieniaj założenia w słownikach `models` i `scen`, aby przeliczyć scenariusze z raportu.md.
# MAU = unikalni użytkownicy miesięcznie. ARPU = przychód na MAU na miesiąc.
levels = [10_000, 100_000, 500_000]

# Przychód na MAU / miesiąc dla każdego modelu (pesymistyczny / bazowy / optymistyczny).
# Wzory, np. CPC: kliknięcia wychodzące na MAU * udział płatnych kliknięć * stawka za kliknięcie.
models = {
 "CPC afiliacyjny (feedy partnerów)": dict(pess=2*0.30*0.15, base=3*0.40*0.30, opt=4*0.50*0.50),
 "CPA (płatność za aplikację)":       dict(pess=2*0.05*0.05*10, base=3*0.05*0.10*15, opt=4*0.06*0.20*20),
 "Płatne ogłoszenia pracodawców":     dict(pess=0.5/1000*99, base=1/1000*149, opt=2/1000*199),
 "Promowanie ofert (boost)":          dict(pess=0.5/1000*0.15*49, base=1/1000*0.25*79, opt=2/1000*0.35*99),
 "Premium dla kandydatów":            dict(pess=0.001*9.99, base=0.003*19, opt=0.008*24),
 "Alerty sponsorowane (e-mail/push)": dict(pess=0.20*4/1000*15, base=0.30*8/1000*25, opt=0.40*12/1000*40),
 "Reklamy display":                   dict(pess=5/1000*3, base=8/1000*6, opt=12/1000*10),
 "Narzędzia dla pracodawców (SaaS)":  dict(pess=0.25/1000*99, base=0.5/1000*199, opt=1/1000*299),
}
print("== Przychód / MAU / mies. i przychód miesięczny przy poziomach MAU (pess / base / opt) ==")
for name, v in models.items():
    row = [f"{name}: ARPU {v['pess']:.3f}/{v['base']:.3f}/{v['opt']:.3f}"]
    for L in levels:
        row.append(f"{L:>7}: {v['pess']*L:>9,.0f} / {v['base']*L:>9,.0f} / {v['opt']*L:>9,.0f}")
    print(" | ".join(row))

# Uczelnie (stałe kwoty, nie skalują się liniowo)
uni = {10_000:(0,500,1000), 100_000:(1500,4167,8333), 500_000:(6250,18750,37500)}
print("Uczelnie/biura karier:", uni)
# Raporty płacowe
rep = {10_000:(0,0,0), 100_000:(0,1667,3333), 500_000:(1667,8333,16667)}
print("Raporty:", rep)

# Miks realistyczny (bez sumowania wzajemnie wykluczających się: display i premium pominięte)
mix_keys = ["CPC afiliacyjny (feedy partnerów)","Płatne ogłoszenia pracodawców","Promowanie ofert (boost)","Alerty sponsorowane (e-mail/push)","Narzędzia dla pracodawców (SaaS)"]
for i,sc in enumerate(["pess","base","opt"]):
    arpu = sum(models[k][sc] for k in mix_keys)
    print(f"Miks {sc}: ARPU={arpu:.3f}", [ (L, round(arpu*L + uni[L][i])) for L in levels])

print()
print("== Model 3-letni ==")
scen = {
 "pesymistyczny": dict(mau=[1500,6000,12000], arpu=[0.15,0.25,0.35],
    costs=dict(infra=[4000,8000,12000], dane=[0,0,0], marketing=[6000,12000,15000], seo=[0,4000,6000],
               prawnik=[5000,2000,2000], ksiegowosc=[0,6000,7200], narzedzia=[3000,4000,5000], ludzie=[0,0,0])),
 "bazowy": dict(mau=[5000,25000,60000], arpu=[0.30,0.50,0.75],
    costs=dict(infra=[5000,12000,24000], dane=[0,3000,6000], marketing=[10000,40000,90000], seo=[3000,18000,30000],
               prawnik=[8000,4000,6000], ksiegowosc=[2000,9600,10800], narzedzia=[4000,6000,9000], ludzie=[0,48000,156000])),
 "optymistyczny": dict(mau=[15000,100000,300000], arpu=[0.50,0.90,1.20],
    costs=dict(infra=[8000,30000,90000], dane=[0,12000,30000], marketing=[25000,150000,450000], seo=[6000,48000,96000],
               prawnik=[10000,12000,20000], ksiegowosc=[3000,12000,18000], narzedzia=[6000,12000,24000], ludzie=[0,180000,900000])),
}
for name, s in scen.items():
    start = 0
    cum = 0
    print(f"--- {name} ---")
    for y in range(3):
        end = s['mau'][y]
        avg = (start+end)/2
        rev = avg*12*s['arpu'][y]
        cost = sum(v[y] for v in s['costs'].values())
        prof = rev-cost
        cum += prof
        be_mau = (cost/12)/s['arpu'][y]
        print(f"Rok {y+1}: MAU koniec {end:,}, śr. {avg:,.0f}, ARPU {s['arpu'][y]}, przychód {rev:,.0f}, koszty {cost:,.0f}, wynik {prof:,.0f}, skumul. {cum:,.0f}, MAU do BEP {be_mau:,.0f}")
        start = end
    for k,v in s['costs'].items():
        print(f"   {k}: {v}")

# Break-even month for base: linear monthly growth
import math
for name, s in scen.items():
    start=0; m=0; found=None
    for y in range(3):
        end=s['mau'][y]; cost_m=sum(v[y] for v in s['costs'].values())/12
        for i in range(12):
            m+=1
            mau = start + (end-start)*(i+0.5)/12
            if found is None and mau*s['arpu'][y] >= cost_m:
                found=m
        start=end
    print(name, "miesiąc osiągnięcia miesięcznego BEP:", found)

# LLM cost
for n in [10_000, 50_000]:
    for model,(pin,pout) in {"Haiku 4.5":(1,5),"Sonnet 5.5":(2,10)}.items():
        cost = n*(1200*pin + 250*pout)/1e6
        print(f"LLM {model} {n} ofert: ${cost:.1f} standard, ${cost/2:.1f} batch")

# TAM
top10 = [3641112,3078000,2776032,2007504,1925208,1026756,893430,712800,592434,366120]
print("Suma top10 Gemius:", sum(top10))
students=1_322_800
print("studenci pracujący 80%:", students*0.8, " aktywnie szukający/mies 35%:", students*0.8*0.35)
print("EU 18.8M*0.78:", 18.8e6*0.78, " *0.35:", 18.8e6*0.78*0.35)
# CAC
fx=3.7
cpc_meta=0.70*fx
print("Meta CPC PLN:", cpc_meta, " CAC przy 25% retencji:", cpc_meta/0.25, " Google Ads CPC PLN:", 2.04*fx, " CAC 25%:", 2.04*fx/0.25)
print("LTV base: ARPU 0.5 * 5 mies =", 0.5*5)
