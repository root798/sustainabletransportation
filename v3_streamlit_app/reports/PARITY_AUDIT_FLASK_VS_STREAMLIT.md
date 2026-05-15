# PARITY_AUDIT_FLASK_VS_STREAMLIT

## Feature parity table
| feature | original_flask | new_streamlit | status |
| --- | --- | --- | --- |
| Live slider behavior | Yes via JS realtime toggle | Yes via session-state realtime/manual modes | restored |
| Region switching | Yes | Yes | matched |
| Policy switching | No explicit policy selector in Flask UI | Yes, with explicit availability messaging | expanded |
| Linear/log scale | Yes | Yes | matched |
| Chart families | Energy, emissions, counts | Energy, emissions, counts, subsystem detail | expanded |
| Uncertainty display | Limited summary plus optional bands | Dedicated page plus default-only overlays when files exist | clarified |
| Subsystem display | Partial | Explicit optional subsystem breakdown | expanded |
| Reset behavior | Reset params button | Reset region defaults and reset app defaults | expanded |
| State comparison behavior | Manual multi-state chart selection | Dedicated CA/OH/U.S. compare with diagnostics | improved |

## Numerical parity check
Original Flask default charts are backed by `results/<region>_results.csv`. The new Streamlit explorer uses the same `TransportModel` runtime path under identical default configs.
| region | year | metric | flask_pipeline | new_streamlit_pipeline | absolute_difference | relative_difference | expected | difference_source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| California | 2025 | ATS total annual energy | 546074384.0392593 | 546074384.0392593 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| California | 2025 | ATS total annual emissions | 566081054.4739238 | 566081054.4739238 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| California | 2025 | ECAV energy | 9138639.341758292 | 9138639.341758292 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| California | 2025 | ICECAV energy | 318800517.3556375 | 318800517.3556375 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| California | 2025 | STI energy | 218135227.3418636 | 218135227.34186357 | 2.9802322387695312e-08 | 1.366231523026257e-16 | yes | Same TransportModel path; differences are float-noise only. |
| California | 2025 | EV share | 0.0438506547114914 | 0.04385065471149145 | 4.85722573273506e-17 | 1.1076746207536523e-15 | yes | Same TransportModel path; differences are float-noise only. |
| California | 2025 | clean grid fraction | 0.6888000000000001 | 0.6888000000000001 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| California | 2025 | total CAV count | 29917.617801011245 | 29917.617801011245 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| California | 2025 | total STI count | 3729.4117647058815 | 3729.4117647058824 | 9.094947017729282e-13 | 2.4387081908737826e-16 | yes | Same TransportModel path; differences are float-noise only. |
| California | 2045 | ATS total annual energy | 4339924711.963615 | 4339924711.963615 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| California | 2045 | ATS total annual emissions | 4809338016.697065 | 4809338016.697065 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| California | 2045 | ECAV energy | 368927738.72885305 | 368927738.72885305 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| California | 2045 | ICECAV energy | 2888358194.6531835 | 2888358194.6531835 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| California | 2045 | STI energy | 1082638778.5815785 | 1082638778.5815785 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| California | 2045 | EV share | 0.169688197206905 | 0.16968819720690503 | 2.7755575615628914e-17 | 1.635680976785077e-16 | yes | Same TransportModel path; differences are float-noise only. |
| California | 2045 | clean grid fraction | 1.0 | 1.0 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| California | 2045 | total CAV count | 6619861.662291816 | 6619861.6622918155 | 9.313225746154785e-10 | 1.406861082793461e-16 | yes | Same TransportModel path; differences are float-noise only. |
| California | 2045 | total STI count | 77433.52647467476 | 77433.52647467476 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| California | 2075 | ATS total annual energy | 4240467068.314381 | 4240467068.314381 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| California | 2075 | ATS total annual emissions | 127214012.0494314 | 127214012.04943141 | 1.4901161193847656e-08 | 1.1713459039447266e-16 | yes | Same TransportModel path; differences are float-noise only. |
| California | 2075 | ECAV energy | 2969586446.7501926 | 2969586446.7501926 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| California | 2075 | ICECAV energy | 0.0 | 0.0 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| California | 2075 | STI energy | 1270880621.5641882 | 1270880621.5641882 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| California | 2075 | EV share | 1.0 | 1.0 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| California | 2075 | clean grid fraction | 1.0 | 1.0 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| California | 2075 | total CAV count | 39537290.752555095 | 39537290.752555095 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| California | 2075 | total STI count | 186847.05094165757 | 186847.05094165754 | 2.9103830456733704e-11 | 1.5576285689315637e-16 | yes | Same TransportModel path; differences are float-noise only. |
| California | 2036 | ATS total annual energy | 6828259339.227728 | 6828259339.227728 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| California | 2036 | ATS total annual emissions | 9107405239.298222 | 9107405239.298222 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| California | 2036 | ECAV energy | 349249383.4259276 | 349249383.4259276 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| California | 2036 | ICECAV energy | 5495405838.963822 | 5495405838.963822 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| California | 2036 | STI energy | 983604116.8379778 | 983604116.8379778 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| California | 2036 | EV share | 0.0922991361791088 | 0.0922991361791088 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| California | 2036 | clean grid fraction | 1.0 | 1.0 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| California | 2036 | total CAV count | 2202009.6337753567 | 2202009.6337753567 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| California | 2036 | total STI count | 44312.293870931455 | 44312.293870931455 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| California | 2092 | ATS total annual energy | 4715054809.7682295 | 4715054809.7682295 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| California | 2092 | ATS total annual emissions | 141451682.17994145 | 141451682.17994145 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| California | 2092 | ECAV energy | 3438565912.795601 | 3438565912.795601 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| California | 2092 | ICECAV energy | 23.38697195842789 | 23.38697195842789 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| California | 2092 | STI energy | 1276488873.5856562 | 1276488873.5856562 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| California | 2092 | EV share | 1.0 | 1.0 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| California | 2092 | clean grid fraction | 1.0 | 1.0 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| California | 2092 | total CAV count | 42875560.18225794 | 42875560.18225794 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| California | 2092 | total STI count | 190199.97530020468 | 190199.97530020468 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| Ohio | 2025 | ATS total annual energy | 134795414.91362038 | 134795414.91362038 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| Ohio | 2025 | ATS total annual emissions | 134314121.75432444 | 134314121.75432444 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| Ohio | 2025 | ECAV energy | 294919.51791625423 | 294919.51791625423 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| Ohio | 2025 | ICECAV energy | 65529990.105863765 | 65529990.105863765 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| Ohio | 2025 | STI energy | 68970505.28984036 | 68970505.28984036 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| Ohio | 2025 | EV share | 0.0071505055368319 | 0.00715050553683197 | 7.025630077706069e-17 | 9.82536135594525e-15 | yes | Same TransportModel path; differences are float-noise only. |
| Ohio | 2025 | clean grid fraction | 0.25935 | 0.25935 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| Ohio | 2025 | total CAV count | 8252.484114672587 | 8252.484114672587 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| Ohio | 2025 | total STI count | 1676.470588235294 | 1676.4705882352941 | 2.2737367544323206e-13 | 1.35626402895963e-16 | yes | Same TransportModel path; differences are float-noise only. |
| Ohio | 2045 | ATS total annual energy | 1254071409.7151854 | 1254071409.7151854 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| Ohio | 2045 | ATS total annual emissions | 1534071579.7433212 | 1534071579.7433212 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| Ohio | 2045 | ECAV energy | 15844951.480681654 | 15844951.480681654 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| Ohio | 2045 | ICECAV energy | 890871931.1862527 | 890871931.1862527 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| Ohio | 2045 | STI energy | 347354527.04825103 | 347354527.04825103 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| Ohio | 2045 | EV share | 0.0276702001748001 | 0.0276702001748001 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| Ohio | 2045 | clean grid fraction | 0.688132759829206 | 0.688132759829206 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| Ohio | 2045 | total CAV count | 1836645.58291848 | 1836645.58291848 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| Ohio | 2045 | total STI count | 34808.44644366294 | 34808.44644366294 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| Ohio | 2075 | ATS total annual energy | 1955550934.371794 | 1955550934.371794 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| Ohio | 2075 | ATS total annual emissions | 2196299809.005154 | 2196299809.005154 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| Ohio | 2075 | ECAV energy | 220061741.50623888 | 220061741.50623888 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| Ohio | 2075 | ICECAV energy | 1319526716.6506176 | 1319526716.6506176 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| Ohio | 2075 | STI energy | 415962476.2149375 | 415962476.2149375 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| Ohio | 2075 | EV share | 0.2106326208120902 | 0.2106326208120902 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| Ohio | 2075 | clean grid fraction | 1.0 | 1.0 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| Ohio | 2075 | total CAV count | 10969908.073992666 | 10969908.073992666 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| Ohio | 2075 | total STI count | 83992.75949270093 | 83992.75949270093 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| Ohio | 2076 | ATS total annual energy | 1981229529.2307768 | 1981229529.2307768 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| Ohio | 2076 | ATS total annual emissions | 2203578728.2817698 | 2203578728.2817698 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| Ohio | 2076 | ECAV energy | 240678594.10223627 | 240678594.10223627 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| Ohio | 2076 | ICECAV energy | 1323544347.1634855 | 1323544347.1634855 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| Ohio | 2076 | STI energy | 417006587.9650551 | 417006587.9650551 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| Ohio | 2076 | EV share | 0.2253769042689365 | 0.2253769042689365 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| Ohio | 2076 | clean grid fraction | 1.0 | 1.0 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| Ohio | 2076 | total CAV count | 11408684.862712832 | 11408684.862712832 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| Ohio | 2076 | total STI count | 84759.66497410978 | 84759.66497410978 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| Ohio | 2092 | ATS total annual energy | 1871241954.8262167 | 1871241954.8262167 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| Ohio | 2092 | ATS total annual emissions | 1105904235.8859997 | 1105904235.8859997 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| Ohio | 2092 | ECAV energy | 805223172.6070877 | 805223172.6070877 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| Ohio | 2092 | ICECAV energy | 648004306.9390205 | 648004306.9390205 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| Ohio | 2092 | STI energy | 418014475.28010833 | 418014475.28010833 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| Ohio | 2092 | EV share | 0.6653495265466511 | 0.6653495265466511 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| Ohio | 2092 | clean grid fraction | 1.0 | 1.0 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| Ohio | 2092 | total CAV count | 11896290.61369347 | 11896290.61369347 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| Ohio | 2092 | total STI count | 85499.9888967797 | 85499.9888967797 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| U.S. Average (synthetic CA/OH midpoint) | 2025 | ATS total annual energy | 124001967.70448914 | 124001967.70448914 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| U.S. Average (synthetic CA/OH midpoint) | 2025 | ATS total annual emissions | 189366832.5237029 | 189366832.52370292 | 2.9802322387695312e-08 | 1.5737878693178744e-16 | yes | Same TransportModel path; differences are float-noise only. |
| U.S. Average (synthetic CA/OH midpoint) | 2025 | ECAV energy | 2629234.354798126 | 2629234.354798126 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| U.S. Average (synthetic CA/OH midpoint) | 2025 | ICECAV energy | 112903304.4366502 | 112903304.43665019 | 1.4901161193847656e-08 | 1.3198162151408655e-16 | yes | Same TransportModel path; differences are float-noise only. |
| U.S. Average (synthetic CA/OH midpoint) | 2025 | STI energy | 8469428.913040843 | 8469428.913040843 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| U.S. Average (synthetic CA/OH midpoint) | 2025 | EV share | 0.0358794864233472 | 0.03587948642334729 | 9.020562075079397e-17 | 2.5141279807198167e-15 | yes | Same TransportModel path; differences are float-noise only. |
| U.S. Average (synthetic CA/OH midpoint) | 2025 | clean grid fraction | 0.474075 | 0.474075 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| U.S. Average (synthetic CA/OH midpoint) | 2025 | total CAV count | 10912.670984121209 | 10912.670984121207 | 1.8189894035458565e-12 | 1.6668599339177628e-16 | yes | Same TransportModel path; differences are float-noise only. |
| U.S. Average (synthetic CA/OH midpoint) | 2025 | total STI count | 162.17647058823528 | 162.17647058823528 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| U.S. Average (synthetic CA/OH midpoint) | 2045 | ATS total annual energy | 7463968787.351455 | 7463968787.351455 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| U.S. Average (synthetic CA/OH midpoint) | 2045 | ATS total annual emissions | 11083442085.784275 | 11083442085.784277 | 1.9073486328125e-06 | 1.720899173785446e-16 | yes | Same TransportModel path; differences are float-noise only. |
| U.S. Average (synthetic CA/OH midpoint) | 2045 | ECAV energy | 675483352.8550243 | 675483352.8550243 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| U.S. Average (synthetic CA/OH midpoint) | 2045 | ICECAV energy | 6703409272.940576 | 6703409272.940576 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| U.S. Average (synthetic CA/OH midpoint) | 2045 | STI energy | 85076161.55585532 | 85076161.55585532 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| U.S. Average (synthetic CA/OH midpoint) | 2045 | EV share | 0.1388422911344109 | 0.13884229113441096 | 5.551115123125783e-17 | 3.9981442813788207e-16 | yes | Same TransportModel path; differences are float-noise only. |
| U.S. Average (synthetic CA/OH midpoint) | 2045 | clean grid fraction | 1.0 | 1.0 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| U.S. Average (synthetic CA/OH midpoint) | 2045 | total CAV count | 2347866.159467353 | 2347866.1594673526 | 4.656612873077393e-10 | 1.9833382981821296e-16 | yes | Same TransportModel path; differences are float-noise only. |
| U.S. Average (synthetic CA/OH midpoint) | 2045 | total STI count | 3403.777472983801 | 3403.777472983801 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| U.S. Average (synthetic CA/OH midpoint) | 2075 | ATS total annual energy | 13971237864.065111 | 13971237864.065113 | 1.9073486328125e-06 | 1.3651965927216218e-16 | yes | Same TransportModel path; differences are float-noise only. |
| U.S. Average (synthetic CA/OH midpoint) | 2075 | ATS total annual emissions | 419137135.9219534 | 419137135.9219534 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| U.S. Average (synthetic CA/OH midpoint) | 2075 | ECAV energy | 13815174582.446648 | 13815174582.446648 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| U.S. Average (synthetic CA/OH midpoint) | 2075 | ICECAV energy | 0.0 | 0.0 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| U.S. Average (synthetic CA/OH midpoint) | 2075 | STI energy | 156063281.61846572 | 156063281.61846572 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| U.S. Average (synthetic CA/OH midpoint) | 2075 | EV share | 1.0 | 1.0 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| U.S. Average (synthetic CA/OH midpoint) | 2075 | clean grid fraction | 1.0 | 1.0 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| U.S. Average (synthetic CA/OH midpoint) | 2075 | total CAV count | 14596766.778840462 | 14596766.778840462 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| U.S. Average (synthetic CA/OH midpoint) | 2075 | total STI count | 8266.091624185226 | 8266.091624185226 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| U.S. Average (synthetic CA/OH midpoint) | 2059 | ATS total annual energy | 11905926724.217382 | 11905926724.217382 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| U.S. Average (synthetic CA/OH midpoint) | 2059 | ATS total annual emissions | 14517375924.705383 | 14517375924.705385 | 1.9073486328125e-06 | 1.313838425556379e-16 | yes | Same TransportModel path; differences are float-noise only. |
| U.S. Average (synthetic CA/OH midpoint) | 2059 | ECAV energy | 3046495387.4595814 | 3046495387.4595814 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| U.S. Average (synthetic CA/OH midpoint) | 2059 | ICECAV energy | 8740863038.875843 | 8740863038.875843 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| U.S. Average (synthetic CA/OH midpoint) | 2059 | STI energy | 118568297.88195673 | 118568297.88195673 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| U.S. Average (synthetic CA/OH midpoint) | 2059 | EV share | 0.3580095891822627 | 0.3580095891822627 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| U.S. Average (synthetic CA/OH midpoint) | 2059 | clean grid fraction | 1.0 | 1.0 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| U.S. Average (synthetic CA/OH midpoint) | 2059 | total CAV count | 6633254.55840041 | 6633254.55840041 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| U.S. Average (synthetic CA/OH midpoint) | 2059 | total STI count | 5672.870732866101 | 5672.870732866101 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| U.S. Average (synthetic CA/OH midpoint) | 2092 | ATS total annual energy | 16697287929.673824 | 16697287929.673824 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| U.S. Average (synthetic CA/OH midpoint) | 2092 | ATS total annual emissions | 500918637.89021474 | 500918637.89021474 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| U.S. Average (synthetic CA/OH midpoint) | 2092 | ECAV energy | 16541153772.78992 | 16541153772.78992 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| U.S. Average (synthetic CA/OH midpoint) | 2092 | ICECAV energy | 0.0 | 0.0 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| U.S. Average (synthetic CA/OH midpoint) | 2092 | STI energy | 156134156.88390437 | 156134156.88390437 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| U.S. Average (synthetic CA/OH midpoint) | 2092 | EV share | 1.0 | 1.0 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| U.S. Average (synthetic CA/OH midpoint) | 2092 | clean grid fraction | 1.0 | 1.0 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| U.S. Average (synthetic CA/OH midpoint) | 2092 | total CAV count | 25160147.79409263 | 25160147.79409263 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |
| U.S. Average (synthetic CA/OH midpoint) | 2092 | total STI count | 8271.0 | 8271.0 | 0.0 | 0.0 | yes | Same TransportModel path; differences are float-noise only. |

### Detected legacy data/result misalignment
The legacy Streamlit v2 pages loaded notebook quantile medians instead of the deterministic Flask defaults. Those notebook medians are not numerically aligned with the Flask baseline outputs, especially for California and U.S. Average.
| region | year | metric | flask_default | legacy_streamlit_notebook_p50 | absolute_difference | relative_difference | where_difference_comes_from |
| --- | --- | --- | --- | --- | --- | --- | --- |
| California | 2025 | ATS total annual energy | 546074384.0392593 | 121763550.43152805 | 424310833.6077313 | 0.7770202119153533 | results_notebook_quantiles |
| California | 2025 | ATS total annual emissions | 566081054.4739238 | 108208210.64873372 | 457872843.82519007 | 0.8088467900603123 | results_notebook_quantiles |
| California | 2025 | ECAV energy | 9138639.341758292 | 166669.45841883053 | 8971969.883339461 | 0.9817621144476893 | results_notebook_quantiles |
| California | 2025 | ICECAV energy | 318800517.3556375 | 53667535.695286185 | 265132981.6603513 | 0.831657940393436 | results_notebook_quantiles |
| California | 2025 | STI energy | 218135227.3418636 | 69139248.27430847 | 148995979.06755513 | 0.6830440955510924 | results_notebook_quantiles |
| California | 2025 | EV share | 0.0438506547114914 | 0.0049579164170775 | 0.038892738294413906 | 0.8869363194301809 | results_notebook_quantiles |
| California | 2025 | clean grid fraction | 0.6888000000000001 | 0.4163915198398554 | 0.2724084801601447 | 0.39548269477372916 | results_notebook_quantiles |
| California | 2025 | total CAV count | 29917.617801011245 | 7799.880026907889 | 22117.737774103356 | 0.7392880650195268 | results_notebook_quantiles |
| California | 2025 | total STI count | 3729.4117647058815 | 1680.7941176470588 | 2048.6176470588225 | 0.5493138801261828 | results_notebook_quantiles |
| California | 2045 | ATS total annual energy | 4339924711.963615 | 1030483536.4408884 | 3309441175.522727 | 0.7625572781020337 | results_notebook_quantiles |
| California | 2045 | ATS total annual emissions | 4809338016.697065 | 1103612272.200224 | 3705725744.4968414 | 0.77052719763745 | results_notebook_quantiles |
| California | 2045 | ECAV energy | 368927738.72885305 | 8420020.387719726 | 360507718.3411333 | 0.9771770471455167 | results_notebook_quantiles |
| California | 2045 | ICECAV energy | 2888358194.6531835 | 689006259.0068334 | 2199351935.64635 | 0.7614540120812249 | results_notebook_quantiles |
| California | 2045 | STI energy | 1082638778.5815785 | 348882087.55673224 | 733756691.0248463 | 0.677748391745379 | results_notebook_quantiles |
| California | 2045 | EV share | 0.169688197206905 | 0.0196597763838193 | 0.1500284208230857 | 0.8841417570142038 | results_notebook_quantiles |
| California | 2045 | clean grid fraction | 1.0 | 1.0 | 0.0 | 0.0 | results_notebook_quantiles |
| California | 2045 | total CAV count | 6619861.662291816 | 1426849.2981909993 | 5193012.364100818 | 0.784459348098066 | results_notebook_quantiles |
| California | 2045 | total STI count | 77433.52647467476 | 34898.21559501765 | 42535.3108796571 | 0.549313880126183 | results_notebook_quantiles |
| California | 2075 | ATS total annual energy | 4240467068.314381 | 1628580790.1198254 | 2611886278.1945558 | 0.6159430638457478 | results_notebook_quantiles |
| California | 2075 | ATS total annual emissions | 127214012.0494314 | 1782231887.485593 | 1655017875.4361618 | 13.009713700351448 | results_notebook_quantiles |
| California | 2075 | ECAV energy | 2969586446.7501926 | 121252924.9620316 | 2848333521.7881613 | 0.9591684138056576 | results_notebook_quantiles |
| California | 2075 | ICECAV energy | 0.0 | 1081886277.6823444 | 1081886277.6823444 | nan | results_notebook_quantiles |
| California | 2075 | STI energy | 1270880621.5641882 | 417514184.672451 | 853366436.8917372 | 0.6714764726221268 | results_notebook_quantiles |
| California | 2075 | EV share | 1.0 | 0.1446884308542057 | 0.8553115691457943 | 0.8553115691457943 | results_notebook_quantiles |
| California | 2075 | clean grid fraction | 1.0 | 1.0 | 0.0 | 0.0 | results_notebook_quantiles |
| California | 2075 | total CAV count | 39537290.752555095 | 8529231.782652635 | 31008058.96990246 | 0.784273742072187 | results_notebook_quantiles |
| California | 2075 | total STI count | 186847.05094165757 | 84209.37239876106 | 102637.67854289651 | 0.5493138801261831 | results_notebook_quantiles |
| California | 2036 | ATS total annual energy | 6828259339.227728 | 1276346587.4131837 | 5551912751.814545 | 0.8130787768881759 | results_notebook_quantiles |
| California | 2036 | ATS total annual emissions | 9107405239.298222 | 1601492102.8108475 | 7505913136.487374 | 0.8241549529496668 | results_notebook_quantiles |
| California | 2036 | ECAV energy | 349249383.4259276 | 6448717.1080765575 | 342800666.317851 | 0.9815354946519347 | results_notebook_quantiles |

## Unit and terminology audit
| location | old_label | new_label | reason |
| --- | --- | --- | --- |
| results/*.csv column headers | `ATS Total Power (kWh)` | Annual energy demand (kWh/year) | Stored values are annual totals, not instantaneous power. |
| static/js/main.js | Power (TWh) | Annual energy demand (TWh/year) | Original Flask UI axis label used power terminology. |
| templates/index.html | Consumption tab labels mixing power and kWh | Annual energy demand labels | kWh implies energy; dashboard display now uses energy language. |
| Turning-point descriptions | Turning year described without formula | Explicit formula shown | Now marked as derived, not measured. |
| Emissions intensity notes | Intensity label ambiguous | ATS emissions / ATS energy or ATS emissions / CAV count | New diagnostics tables name the denominator explicitly. |
